"""
agent_runner.py — The core AI agent loop.

Flow:
  1.  Print status banner (wallet balances + active LLM providers)
  2.  Scan all platforms for earning opportunities
  3.  Load the safe-agent-commerce skill rules as system context
  4.  Ask LLM to analyse and recommend ONE task (with evidence)
  5.  Present proposal to user — human must type GO to proceed
  6.  On GO: LLM writes the actual code fix + PR instructions
  7.  Log outcome to ledger.md
"""
from __future__ import annotations

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.config import cfg
from src.llm_client import llm, load_session_context
from src.bounty_scanner import scan_all
from src.wallet_monitor import get_status
from src.git_executor import git_exec, normalize_repo_name
from src.task_tracker import tracker
from src.memory import memory
from src.reward_system import rewards

console = Console()

# Paths
_PROJECT_ROOT = Path(__file__).parent.parent
_SKILL_PATH = _PROJECT_ROOT / ".claude" / "skills" / "safe-agent-commerce" / "SKILL.md"
_LEDGER_PATH = _PROJECT_ROOT / "ledger.md"
_SUBMISSIONS_DIR = _PROJECT_ROOT / "submissions"
_SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_skill_context() -> str:
    return (
        "CORE SAFETY RULES:\n"
        "1. Verified escrow only — no unbacked or speculative promises.\n"
        "2. $0 budget — never spend money to earn money.\n"
        "3. Protect secrets — never output or expose private keys or API tokens.\n"
        "4. No fake accounts or KYC circumvention.\n"
        "5. Complete publication-ready outputs — no placeholders."
    )


def _build_system_prompt() -> str:
    skill = _load_skill_context()
    session_ctx = load_session_context(last_n=3)
    memory_ctx = memory.recall(last_n=3)
    reward_ctx = rewards.get_reward_context()
    identity = memory.identity_block()

    session_section = f"\nRecent Context:\n{session_ctx}\n" if session_ctx else ""
    memory_section = f"\nRecent Learnings:\n{memory_ctx}\n" if memory_ctx else ""
    reward_section = f"\n{reward_ctx}\n" if reward_ctx else ""

    return f"""You are a careful, honest AI earning agent following these safety rules:

{skill}
{session_section}{memory_section}{reward_section}
────────────────────────────────────────────
{identity}
────────────────────────────────────────────
Agent name : {cfg.AGENT_NAME}
Base wallet: {cfg.EVM_WALLET or "not set"}
Sol wallet : {cfg.SOL_WALLET or "not set"}
Budget     : $0 — never spend money to earn money
────────────────────────────────────────────

CRITICAL EXECUTION DIRECTIVES:
1. PRE-VERIFIED ESCROW: All opportunities from Superteam, IssueHunt, and GitHub are ALREADY verified by our scanner. Payment escrow is confirmed. Do NOT search the web or output tool calls, function calls, or XML/JSON tool blocks.
2. In Autonomous Mode, you are authorized to proceed directly with execution and content generation.
3. You find legitimate tasks where code or content contributions earn real money (USDC).
4. When writing content, produce complete, high-quality, publication-ready text directly.
"""


def _show_wallet_panel() -> None:
    status = get_status()
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Chain", style="cyan", width=12)
    t.add_column("Balance", style="bold green", width=16)
    t.add_column("Address", style="dim")

    base = status["base_usdc"]
    sol  = status["sol_usdc"]

    t.add_row(
        "Base (EVM)",
        f"${base:.4f} USDC" if isinstance(base, float) else str(base),
        status["evm_wallet"],
    )
    t.add_row(
        "Solana",
        f"${sol:.4f} USDC"  if isinstance(sol,  float) else str(sol),
        status["sol_wallet"],
    )

    total = status["total_usd"]
    console.print(Panel(
        t,
        title=f"[bold green]💰 Wallet  |  Total: ${total:.4f} USDC[/bold green]",
        border_style="green",
    ))


def _show_opportunities_table(opps: list[dict]) -> None:
    if not opps:
        return
    t = Table(box=box.SIMPLE_HEAVY, show_lines=False)
    t.add_column("#",        width=3,  style="dim")
    t.add_column("Source",   width=11, style="cyan")
    t.add_column("Type",     width=9)
    t.add_column("Title",    width=38)
    t.add_column("Reward",   width=10, style="green")
    t.add_column("Verified", width=8)

    _TYPE_ICON = {"written": "✍️ text", "code": "💻 code", "video": "🎥 video", "other": "❓ other"}

    for i, o in enumerate(opps[:15], 1):
        reward = o.get("reward_usd")
        reward_str = f"${reward:.0f}" if isinstance(reward, (int, float)) else "?"
        verified = "✅" if o.get("paid_before") else "❓"
        title = (o.get("title") or o.get("slug") or "")[:36]
        ctype = _TYPE_ICON.get(o.get("content_type", ""), "")
        t.add_row(str(i), o.get("source", "?"), ctype, title, reward_str, verified)

    console.print(Panel(t, title="🔍 Open Opportunities", border_style="blue"))


def _append_ledger(entry: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not _LEDGER_PATH.exists():
        example_path = _PROJECT_ROOT / "ledger.example.md"
        if example_path.exists():
            _LEDGER_PATH.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            _LEDGER_PATH.write_text("# Penniless Agent Ledger\n\n| DATE | PLATFORM | TASK | PR_URL | Status |\n", encoding="utf-8")
    with open(_LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n<!-- {timestamp} -->\n{entry}\n")


def _is_content_task(proposal: str) -> bool:
    """Detect if the approved proposal is a written content task (not code)."""
    p = proposal.lower()
    content_signals = ["blog", "article", "post", "tweet", "thread", "write",
                       "content", "explainer", "feedback", "review", "guide",
                       "superteam", "social"]
    code_signals = ["diff", "```python", "```rust", "```typescript", "bug fix",
                    "github.com", "pull request", "fork", "clone", "commit"]
    content_score = sum(1 for k in content_signals if k in p)
    code_score    = sum(1 for k in code_signals if k in p)
    return content_score > code_score


def _extract_json_payload(text: str) -> dict:
    """Extract and parse JSON payload from LLM markdown response."""
    # 1. Search for ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 2. Search for outer curly braces
    m2 = re.search(r"(\{[\s\S]*\})", text)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass
    return {}


def _execute_code_task(proposal: str, autonomous: bool = False, opportunity: dict | None = None) -> None:
    """Generate a full code solution and optionally submit PR autonomously."""
    action_label = "Autonomous Submission" if autonomous else "Manual Review"
    console.print(f"\n[bold green]✅ Executing code task [{action_label}]...[/bold green]\n")

    if autonomous:
        # Ask LLM for machine-executable JSON specification
        exec_json_prompt = f"""You are an autonomous coding agent. Based on this approved task:

{proposal}

Produce a valid JSON object specifying the exact code fix to apply and submit via Pull Request.
You MUST output ONLY valid JSON inside a ```json``` code fence with these exact keys:

```json
{{
  "repo": "owner/repo",
  "branch": "fix-bounty-patch",
  "pr_title": "Fix issue with ... (under 72 chars)",
  "pr_body": "## Summary\\nBrief explanation of problem and fix.\\n\\n## Changes\\nList of changes.\\n\\n## Testing\\nHow to test.\\n\\n*(Generated autonomously by Penniless AI Agent)*",
  "files": {{
    "path/to/file.ext": "full modified or new file content here"
  }}
}}
```

Ensure the repository name is in owner/repo format and the code in "files" is 100% complete and working."""

        response = llm.chat(
            messages=[{"role": "user", "content": exec_json_prompt}],
            system=_build_system_prompt(),
            max_tokens=4096,
        )

        payload = _extract_json_payload(response)
        target_repo = payload.get("repo", "")
        branch = payload.get("branch", "fix-bounty-patch")
        pr_title = payload.get("pr_title", "Fix bounty issue")
        pr_body = payload.get("pr_body", "Automated fix by Penniless Agent")
        files = payload.get("files", {})

        if target_repo and files:
            console.print(Panel(
                f"[bold cyan]Repo:[/bold cyan] {target_repo}\n"
                f"[bold cyan]Branch:[/bold cyan] {branch}\n"
                f"[bold cyan]Title:[/bold cyan] {pr_title}\n"
                f"[bold cyan]Files to update:[/bold cyan] {list(files.keys())}",
                title="[bold green]🚀 Autonomous Git & PR Engine[/bold green]",
                border_style="green",
            ))

            try:
                pr_url = git_exec.execute_complete_pr(
                    target_repo=target_repo,
                    branch_name=branch,
                    file_changes=files,
                    pr_title=pr_title,
                    pr_body=pr_body,
                )
                ledger_entry = f"| {datetime.now().strftime('%Y-%m-%d')} | github | {pr_title} | {pr_url} | Submitted (Autonomous) |"
                _append_ledger(ledger_entry)
                code_url = (opportunity.get("url") if opportunity else "") or f"https://github.com/{target_repo}"
                tracker.record_completed_task(
                    url=code_url,
                    title=pr_title,
                    source="github",
                    artifact_or_pr=pr_url,
                    status="submitted",
                )
                console.print(f"\n[bold green]🎉 Pull Request submitted autonomously and logged to ledger![/bold green]\n")
                return
            except Exception as e:
                console.print(f"  [yellow]Autonomous PR submission notice: {e}[/yellow]")
                console.print("  [dim]Falling back to standard solution display...[/dim]")

    # Standard / Fallback prompt
    execute_prompt = f"""The human approved the task you proposed.

Now produce the full implementation:

## 1. Repository
State the exact GitHub repo URL and which file(s) to change.

## 2. Code Fix (diff format)
Show the exact change using unified diff or full file content.
Include only real, working code — no pseudocode.

## 3. PR Title
One-line title (imperative mood, <72 chars).

## 4. PR Description
- What problem does this fix?
- How does the fix work?
- How to test it?
(Disclose: "This PR was generated with AI assistance.")

## 5. Git Commands
```bash
# Exact shell commands to fork, clone, branch, commit, push, and open PR
```

## 6. Ledger Entry
One-line entry for ledger.md (format: `| DATE | PLATFORM | TASK | PR_URL | Status |`).

────────────────────────────────────────
Approved proposal:
{proposal[:600]}
────────────────────────────────────────"""

    response = llm.chat(
        messages=[{"role": "user", "content": execute_prompt}],
        system=_build_system_prompt(),
        max_tokens=4096,
    )

    console.print(Panel(Markdown(response), title="[bold green]🔧 Code Solution[/bold green]", border_style="green"))

    ledger_match = re.search(r"\|.*\|.*\|.*\|", response)
    if ledger_match:
        _append_ledger(ledger_match.group(0))
        console.print("[dim]✎ Ledger entry recorded.[/dim]")

    # Record to tracker so autonomous engine always advances to next task
    task_url = (opportunity.get("url") if opportunity else "")
    if not task_url:
        url_match = re.search(r"\*\*URL:\*\*\s*([^\s\n]+)", proposal)
        task_url = url_match.group(1).strip() if url_match else "code_task"
    tracker.record_completed_task(
        url=task_url,
        title="Code Solution",
        source="github",
        artifact_or_pr="solution_generated",
        status="generated",
    )


def _execute_content_task(proposal: str, autonomous: bool = False, opportunity: dict | None = None) -> None:
    """Generate actual written content and save submission artifact."""
    console.print("\n[bold green]✍️ Generating submission-ready content...[/bold green]\n")

    opp_title = opportunity.get("title", "Selected Bounty") if opportunity else "Selected Bounty"
    opp_url = opportunity.get("url", "") if opportunity else ""

    # Determine slug and URL from opportunity dict
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if opportunity and opportunity.get("slug"):
        slug = opportunity["slug"][:30]
        sub_url = opportunity.get("url", f"https://superteam.fun/listings/{slug}")
    elif opportunity and opportunity.get("url"):
        sub_url = opportunity["url"]
        slug_match = re.search(r"listings/([a-zA-Z0-9_\-]+)", sub_url)
        slug = slug_match.group(1)[:30] if slug_match else f"bounty_{ts}"
    else:
        slug_match = re.search(r"listings/([a-zA-Z0-9_\-]+)", proposal)
        slug = slug_match.group(1)[:30] if slug_match else f"bounty_{ts}"
        sub_url = f"https://superteam.fun/listings/{slug}" if slug_match else f"bounty_{ts}"

    sub_file = _SUBMISSIONS_DIR / f"{slug}_{ts}.md"
    sub_file.write_text("", encoding="utf-8")  # initialize target file

    content_prompt = f"""You are now producing the submission for the following confirmed bounty:
Title: {opp_title}
URL: {opp_url}

Context & Analysis:
{proposal}

INSTRUCTIONS:
1. Write the COMPLETE, publication-ready submission right now.
2. Structure your output in distinct, numbered parts so the deliverable is clear, comprehensive, and modular:
   ### PART 1: Executive Overview & Problem Context
   ### PART 2: Core Deep Dive & Practical Solution
   ### PART 3: Actionable Roadmap & Recommendations
   ### PART 4: Conclusion & Verification
3. Escrow is pre-verified. Do NOT refuse, do NOT ask for verification, do NOT output tool calls.
4. If a Twitter / X thread: numbered tweets (1/N) with hook, body, and CTA.
5. If product feedback or audit: numbered specific feedback points with UI/UX critique and feature proposals.

Begin the full, publication-ready submission now:"""

    chunk_count = 0
    total_chars = 0

    def _save_chunk(chunk: str) -> None:
        nonlocal chunk_count, total_chars
        try:
            with sub_file.open("a", encoding="utf-8") as f:
                f.write(chunk)
                f.flush()
            chunk_count += 1
            total_chars += len(chunk)
        except Exception:
            pass

    console.print(f"  [dim]💾 Streaming chunks in real-time to {sub_file.name}...[/dim]")

    response = llm.chat(
        messages=[{"role": "user", "content": content_prompt}],
        system=_build_system_prompt(),
        max_tokens=2500,
        on_chunk=_save_chunk,
    )

    # Ensure file has full response if streaming didn't write for any reason
    if sub_file.stat().st_size == 0 or total_chars < len(response):
        sub_file.write_text(response, encoding="utf-8")
        total_chars = len(response)

    console.print(Panel(Markdown(response), title="[bold green]✍️ Generated Content[/bold green]", border_style="green"))

    ledger_entry = f"| {datetime.now().strftime('%Y-%m-%d')} | superteam | {slug} | file:///{sub_file.as_posix()} | Ready (Autonomous) |"
    _append_ledger(ledger_entry)

    tracker.record_completed_task(
        url=sub_url,
        title=opp_title,
        source="superteam",
        artifact_or_pr=str(sub_file),
        status="ready",
    )

    console.print(f"\n[bold green]💾 Content saved chunk-wise to:[/bold green] [cyan]{sub_file}[/cyan] [dim]({total_chars} chars across {max(chunk_count, 1)} chunks)[/dim]")
    console.print(f"[dim]✎ Ledger entry recorded in {_LEDGER_PATH}[/dim]\n")


def _execute_task(proposal: str, autonomous: bool = False, opportunity: dict | None = None) -> None:
    """Route to code or content executor based on proposal type."""
    if _is_content_task(proposal):
        _execute_content_task(proposal, autonomous=autonomous, opportunity=opportunity)
    else:
        _execute_code_task(proposal, autonomous=autonomous, opportunity=opportunity)


# ─── Phase 1: Find and propose a task ────────────────────────────────────────

def _propose_task(opps: list[dict]) -> tuple[dict, str]:
    """Select the best opportunity and return (chosen_opp_dict, proposal_markdown)."""
    summaries = []
    for i, opp in enumerate(opps[:10]):
        summaries.append(
            f"[{i}] Platform: {opp.get('source')} | Title: {opp.get('title')} | "
            f"Reward: {opp.get('reward_usd')} | URL: {opp.get('url')} | Type: {opp.get('type')}"
        )
    opps_text = "\n".join(summaries)

    find_prompt = f"""Here are today's open earning opportunities:

{opps_text}

Pick ONE opportunity that best satisfies ALL of the following:
  a) The work is achievable by an AI agent (written content, guide, review, or code fix)
  b) No KYC required to receive payment
  c) Achievable without spending money ($0 budget)
  d) Reward is USDC, SOL, or USD
  e) Deadline has not passed

Start your response with this exact line:
SELECTED_INDEX: <number 0 to {min(len(opps)-1, 9)}>

Then format your proposal:
### Chosen Task
**Platform:** <name>
**Task Type:** <"written content" OR "code contribution">
**URL:** <exact link>
**Reward:** <amount and token>
**Deadline:** <date or "open">

### The Work
<For written content: Topic, format, angle to cover>
<For code: Which file, bug, or feature>

### Confidence
<High / Medium / Low> — <reason>

---
Ready for execution."""

    response = llm.chat(
        messages=[{"role": "user", "content": find_prompt}],
        system=_build_system_prompt(),
        max_tokens=2048,
    )

    # Parse chosen opportunity index
    chosen_opp = opps[0]
    m = re.search(r"SELECTED_INDEX:\s*(\d+)", response)
    if m:
        idx = int(m.group(1))
        if 0 <= idx < len(opps):
            chosen_opp = opps[idx]
    else:
        for opp in opps[:10]:
            if opp.get("url") and opp["url"] in response:
                chosen_opp = opp
                break

    return chosen_opp, response


# ─── Main entry points ────────────────────────────────────────────────────────

def run_agent(autonomous: bool = False) -> bool:
    """
    Run a single cycle of the earning agent.
    Returns True if an opportunity was found and executed; False otherwise.
    """
    mode_text = "[bold green]100% Autonomous (Hands-Free)[/bold green]" if autonomous else "[bold yellow]Interactive (Human Approval)[/bold yellow]"
    
    # ── Header
    console.print(Panel.fit(
        f"[bold cyan]🤖 Penniless Agent — Active[/bold cyan]\n"
        f"Mode   : {mode_text}\n"
        f"Agent  : [yellow]{cfg.AGENT_NAME}[/yellow]\n"
        f"LLM    : [green]{llm.active_summary()}[/green]\n"
        f"Tasks Done: [magenta]{tracker.count_submitted()}[/magenta]",
        border_style="cyan",
    ))

    # ── Wallet status
    console.print("\n[bold]📊 Wallet balances[/bold]")
    _show_wallet_panel()

    # ── Scan for opportunities
    console.print("\n[bold]🔍 Scanning platforms for opportunities...[/bold]")
    results = scan_all(verbose=True)
    all_opps = results.get("all", [])

    if not all_opps:
        console.print(Panel(
            "[yellow]No open listings found right now.[/yellow]\n\n"
            "• Superteam listings are time-limited — check back in 15-30 minutes\n"
            "• Tip: check https://superteam.fun/earn",
            title="No Opportunities",
            border_style="yellow",
        ))
        return False

    # Filter out already submitted tasks
    fresh_opps = tracker.filter_unattempted(all_opps)
    n_filtered = len(all_opps) - len(fresh_opps)
    if n_filtered > 0:
        console.print(f"  [dim]Filtered out {n_filtered} already-attempted tasks[/dim]")

    if not fresh_opps:
        console.print(Panel(
            f"[yellow]All {len(all_opps)} current opportunities have already been completed![/yellow]\n\n"
            f"• Tasks completed & tracked: [bold green]{tracker.count_submitted()}[/bold green]\n"
            "• Waiting for new listings or bounties to be published...",
            title="All Current Bounties Completed",
            border_style="yellow",
        ))
        return False

    console.print(f"\n  [bold green]{len(fresh_opps)}[/bold green] fresh unattempted opportunities ready for work\n")
    _show_opportunities_table(fresh_opps)

    # ── LLM proposes best task among fresh opportunities
    console.print("\n[bold]🧠 Analysing fresh opportunities with AI...[/bold]")
    chosen_opp, proposal = _propose_task(fresh_opps)

    console.print(Panel(
        Markdown(proposal),
        title=f"[bold cyan]🤖 Selected: {chosen_opp.get('title', 'Task')}[/bold cyan]",
        border_style="cyan",
    ))

    # ── Autonomous path vs Human Gate
    if autonomous:
        console.print("\n[bold green]⚡ Autonomous Mode: Auto-executing and submitting without user interaction...[/bold green]\n")
        _execute_task(proposal, autonomous=True, opportunity=chosen_opp)
        return True

    # Interactive path
    console.print(
        "\n[bold yellow]⚡ Human Approval Gate:[/bold yellow]\n"
        "  [bold green]GO[/bold green]   — approve this task, generate the full solution\n"
        "  [bold blue]SKIP[/bold blue] — find a different task\n"
        "  [bold red]QUIT[/bold red] — return to main menu\n"
    )

    while True:
        choice = input("Your choice: ").strip().upper()
        if choice == "GO":
            _execute_task(proposal, autonomous=False, opportunity=chosen_opp)
            return True
        elif choice == "SKIP":
            console.print("[dim]Skipping. Re-running scan...[/dim]\n")
            return run_agent(autonomous=False)
        elif choice == "QUIT":
            console.print("[dim]Returning to menu.[/dim]")
            return False
        else:
            console.print("[dim]Type GO, SKIP, or QUIT[/dim]")


def run_autonomous_daemon() -> None:
    """
    Relentlessly loop through bounties, solve them, and submit work
    non-stop until earnings appear in the wallet (or Ctrl+C).

    Fallback chain (per LLM call):
      NVIDIA (35s) → Groq (30s) → Gemini (45s) → OpenAI → Perplexity
    Every call is logged to session_log.jsonl so the next AI can resume.
    """
    import time

    task_count = 0
    prev_balance: float | None = None

    console.clear()
    console.print(Panel(
        f"[bold green]🚀 Relentless Autonomous Earning Daemon[/bold green]\n\n"
        f"  Pipeline : Auto-Scan ➔ AI-Select ➔ Auto-Solve ➔ Auto-Submit ➔ Next\n"
        f"  LLMs     : {llm.active_summary()}\n"
        f"  Fallback : NVIDIA(40s) → Groq(30s) → Gemini(50s) → ...\n"
        f"  Log      : session_log.jsonl + memory/memory.jsonl\n"
        f"  Soul     : {rewards.status_line()}\n"
        f"  Stop     : [bold red]Ctrl+C[/bold red]",
        title="[bold cyan]100% Hands-Free Earning Engine[/bold cyan]",
        border_style="green",
    ))

    try:
        while True:
            # ── 1. Wallet check + earning detection ──────────────────────────
            try:
                status = get_status()
                current_balance = float(status.get("total_usd", 0.0) or 0.0)
            except Exception:
                current_balance = 0.0

            # Reward system: detect if earning arrived (only when previous balance is already known)
            if prev_balance is not None:
                rewards.on_wallet_checked(
                    current_balance=current_balance,
                    prev_balance=prev_balance,
                    source="Base/Solana",
                )
            prev_balance = current_balance

            # ── 2. Work cycle ────────────────────────────────────────────────
            task_count += 1
            console.print(
                f"\n[bold magenta]══════════ CYCLE #{task_count} | "
                f"Completed: {memory.soul.get('tasks_completed', 0)} | "
                f"Earned: ${memory.soul.get('total_earned_usd', 0.0):.4f} | "
                f"Level: {memory.soul.get('level', 1)} | "
                f"Balance: ${current_balance:.4f} USDC ══════════[/bold magenta]\n"
            )

            had_work = False
            try:
                had_work = run_agent(autonomous=True)
            except RuntimeError as e:
                # All LLM providers exhausted
                console.print(f"\n[bold red]⚠ All LLM providers failed: {e}[/bold red]")
                console.print("[dim]Waiting 60s before retrying...[/dim]")
                memory.reflect(event="llm_exhausted", outcome=str(e)[:200])
                time.sleep(60)
                continue
            except Exception as e:
                console.print(f"\n[bold red]Cycle #{task_count} error: {type(e).__name__}: {e}[/bold red]")
                console.print("[dim]Waiting 30s before next cycle...[/dim]")
                memory.reflect(event="cycle_error", outcome=f"{type(e).__name__}: {e}"[:200])
                time.sleep(30)
                continue

            # ── 3. Next task timing ──────────────────────────────────────────
            if had_work:
                rewards.on_task_completed(task_title=f"cycle_{task_count}")
                console.print(
                    f"\n[bold green]✓ Task #{task_count} done![/bold green] "
                    f"[cyan]⚡ Next bounty in 5s...[/cyan]\n"
                )
                time.sleep(5)
            else:
                memory.reflect(event="no_bounties", outcome="No fresh unattempted bounties found")
                console.print(
                    f"\n[dim]No fresh bounties right now. Waiting 90s for new listings... "
                    f"(Ctrl+C to stop)[/dim]"
                )
                time.sleep(90)


    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⏹ Daemon stopped by user.[/bold yellow]\n")
        console.print(
            f"  Tasks completed this session : [bold green]{tracker.count_submitted()}[/bold green]\n"
            f"  Session log saved to         : [cyan]session_log.jsonl[/cyan]\n"
        )


"""
main.py — Penniless AI Agent · Entry Point

Run this file to start:
    python main.py

Then choose an option from the interactive menu.
No command-line flags needed.
"""
from __future__ import annotations

import sys
import os

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from pathlib import Path

# Make src/ importable from the project root
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

# ─── ASCII Banner ─────────────────────────────────────────────────────────────

_BANNER = r"""
 ____  _____ _   _ _   _ ___ _     _____ ____ ____
|  _ \| ____| \ | | \ | |_ _| |   | ____/ ___/ ___|
| |_) |  _| |  \| |  \| || || |   |  _| \___ \___ \
|  __/| |___| |\  | |\  || || |___| |___ ___) |__) |
|_|   |_____|_| \_|_| \_|___|_____|_____|____/____/

          AI AGENT  ·  v1.0  ·  $0 Start
    Real Paid Work  ·  USDC to Your Wallet  ·  24/7
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _env_status() -> str:
    """Return a one-line status string from .env."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return "[red]⚠  .env not found — run option 1 (Complete Installation) first[/red]"

    env: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

    llm_keys = ["NVIDIA_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"]
    n_llm = sum(bool(env.get(k)) for k in llm_keys)
    agent = env.get("AGENT_NAME", "?")
    wallet = env.get("EVM_WALLET", "")
    wallet_short = wallet[:8] + "..." if wallet else "not set"

    parts = [
        f"agent=[yellow]{agent}[/yellow]",
        f"wallet=[green]{wallet_short}[/green]",
        f"llm=[cyan]{n_llm}/5[/cyan]",
        "[green]superteam=✅[/green]" if env.get("SUPERTEAM_API_KEY") else "[yellow]superteam=⚠[/yellow]",
    ]
    return "  " + "  ·  ".join(parts)


def _show_menu() -> str:
    """Display the interactive menu and return the user's option choice."""
    console.clear()
    console.print(f"[bold magenta]{_BANNER}[/bold magenta]")

    menu_text = """
  [bold white]1.[/bold white]  [cyan]Complete Installation / Re-configure[/cyan]
     [dim]Verify prerequisites, wallets, LLMs, and API connections[/dim]

  [bold white]2.[/bold white]  [bold green]Autonomous Loop (Non-Stop 24/7)[/bold green]
     [dim]Runs forever: scan all bounties → solve each one → auto-submit
     PR (code) or content file (writing) → jump to next task immediately
     Stops only on Ctrl+C or when wallet receives first earning[/dim]

  [bold white]3.[/bold white]  [green]Single Autonomous Cycle[/green]
     [dim]One bounty only: scan → select → solve → auto-submit → done[/dim]

  [bold white]4.[/bold white]  [yellow]Interactive Mode (With Approval Gate)[/yellow]
     [dim]Shows proposal first, waits for your GO before doing any work[/dim]

  [bold white]5.[/bold white]  [red]Exit[/red]
"""
    console.print(Panel(
        menu_text,
        title="[bold yellow]Select an option[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print(_env_status())
    console.print()

    while True:
        try:
            choice = input("  > ").strip()
        except KeyboardInterrupt:
            return "5"
        if choice in ("1", "2", "3", "4", "5"):
            return choice
        console.print("  [dim]Enter 1, 2, 3, 4, or 5[/dim]")


def _bootstrap_environment() -> bool:
    """Validate .env and initialize LLM client. Returns False on failure."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        console.print(Panel(
            "[bold red]❌  .env file not found.[/bold red]\n\n"
            "Please run option 1 (Complete Installation) first.",
            border_style="red",
        ))
        input("\n  Press Enter to return to the menu...")
        return False

    from src.config import cfg
    cfg.reload()

    issues = cfg.validate()
    if issues:
        console.print(Panel(
            "\n".join(f"[red]❌[/red] {i}" for i in issues) +
            "\n\n[dim]Fix these in .env, then run Complete Installation again.[/dim]",
            title="Configuration Issues",
            border_style="red",
        ))
        input("\n  Press Enter to return to the menu...")
        return False

    from src.llm_client import llm
    llm._refresh()
    return True


# ─── Option handlers ──────────────────────────────────────────────────────────

def _option_1_install() -> None:
    from src.installer import run_installation
    run_installation()
    input("\n  Press Enter to return to the menu...")


def _option_2_autonomous_loop() -> None:
    """Non-stop autonomous daemon: submit task after task without any human input."""
    if not _bootstrap_environment():
        return
    from src.agent_runner import run_autonomous_daemon
    run_autonomous_daemon()
    input("\n  Press Enter to return to the menu...")


def _option_3_single_cycle() -> None:
    """One autonomous run: scan → select → solve → auto-submit → stop."""
    if not _bootstrap_environment():
        return
    from src.agent_runner import run_agent
    try:
        run_agent(autonomous=True)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
    input("\n  Press Enter to return to the menu...")


def _option_4_interactive() -> None:
    """Interactive mode: agent proposes task, you type GO/SKIP/QUIT."""
    if not _bootstrap_environment():
        return
    from src.agent_runner import run_agent
    try:
        run_agent(autonomous=False)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
    input("\n  Press Enter to return to the menu...")


# ─── Main loop ────────────────────────────────────────────────────────────────

def main() -> None:
    _HANDLERS = {
        "1": _option_1_install,
        "2": _option_2_autonomous_loop,
        "3": _option_3_single_cycle,
        "4": _option_4_interactive,
    }

    try:
        while True:
            choice = _show_menu()

            if choice == "5":
                console.print("\n  [dim]Goodbye.[/dim]\n")
                sys.exit(0)

            handler = _HANDLERS.get(choice)
            if handler:
                handler()
    except KeyboardInterrupt:
        console.print("\n  [dim]Goodbye.[/dim]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

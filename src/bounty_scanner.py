"""
bounty_scanner.py — Scan multiple platforms for real earning opportunities.

Sources:
  1. Superteam   — agent-eligible bounty listings (via authenticated API)
  2. IssueHunt   — pay-per-merged-PR bounties on open-source repos
  3. Algora      — open-source bounties with USDC/USD payouts
  4. GitHub      — issues labelled 'bounty' or 'good-first-issue' on known paying repos
"""
from __future__ import annotations

import requests
from datetime import datetime, timezone
from typing import Any
from rich.console import Console

from src.config import cfg

console = Console()
_TIMEOUT = 12


def _safe_float(v: Any) -> float:
    """Safely convert any numeric, string, or None value to float."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        clean = str(v).replace("$", "").replace(",", "").strip()
        return float(clean)
    except (ValueError, TypeError):
        return 0.0


# ─── Superteam ────────────────────────────────────────────────────────────────

def scan_superteam() -> dict:
    """Fetch open listings from Superteam.

    Tries the agent-only endpoint first; if it returns 0 results (common),
    falls back to the general listings endpoint which always has live bounties.
    """
    if not cfg.SUPERTEAM_API_KEY:
        return {"skipped": "no SUPERTEAM_API_KEY in .env"}

    now = datetime.now(timezone.utc).isoformat()
    headers = {"Authorization": f"Bearer {cfg.SUPERTEAM_API_KEY}"}

    # Keywords that indicate video/design/audio work (not suitable for written-only mode)
    _VIDEO_KEYWORDS = {"video", "record", "film", "reel", "youtube", "tiktok",
                       "design", "merch", "logo", "audio", "podcast", "graphic"}

    def _detect_content_type(title: str, skills: list) -> str:
        """Return 'written', 'video', 'code', or 'other'."""
        t = (title or "").lower()
        s = " ".join(str(x) for x in (skills or [])).lower()
        combined = t + " " + s
        if any(k in combined for k in _VIDEO_KEYWORDS):
            return "video"
        code_kw = {"bug", "fix", "feature", "github", "rust", "python",
                   "typescript", "smart contract", "sdk", "deploy", "api"}
        if any(k in combined for k in code_kw):
            return "code"
        # Default: treat Superteam bounties without code/video signals as written
        return "written"

    def _parse_items(items: list) -> list[dict]:
        return [
            {
                "source": "superteam",
                "title": l.get("title", l.get("slug")),
                "slug": l.get("slug"),
                "type": l.get("type"),
                "content_type": _detect_content_type(l.get("title", ""), l.get("skills", [])),
                "reward_usd": _safe_float(l.get("rewardAmount")),
                "token": l.get("token"),
                "access": l.get("agentAccess", "PUBLIC"),
                "deadline": (l.get("deadline") or "")[:10],
                "url": f"https://superteam.fun/listings/{l.get('slug')}",
                "paid_before": True,
            }
            for l in items
            if (l.get("deadline") or "9999") > now and _safe_float(l.get("rewardAmount")) > 0
        ]

    # 1st: agent-only endpoint
    try:
        r = requests.get(
            "https://superteam.fun/api/agents/listings/live?take=50",
            headers=headers, timeout=_TIMEOUT,
        )
        if r.ok:
            data = r.json()
            items = data if isinstance(data, list) else data.get("result", [])
            if items:
                open_listings = _parse_items(items)
                open_listings.sort(key=lambda x: (x.get("access") != "AGENT_ONLY", -_safe_float(x.get("reward_usd"))))
                return {"total": len(items), "open": open_listings, "source_endpoint": "agent-only"}
    except Exception:
        pass

    # 2nd fallback: general bounty listings (always has results)
    try:
        r = requests.get(
            "https://superteam.fun/api/listings?take=50&type=bounty&status=open",
            headers=headers, timeout=_TIMEOUT,
        )
        if r.ok:
            data = r.json()
            items = data if isinstance(data, list) else data.get("result", [])
            open_listings = _parse_items(items)
            open_listings.sort(key=lambda x: -_safe_float(x.get("reward_usd")))
            return {"total": len(items), "open": open_listings, "source_endpoint": "general"}
        return {"error": f"HTTP {r.status_code}: {r.text[:120]}"}
    except Exception as e:
        return {"error": str(e)}


# ─── IssueHunt ────────────────────────────────────────────────────────────────

def scan_issuehunt(limit: int = 20) -> list[dict]:
    """
    Fetch funded open issues from IssueHunt (pay-per-merged-PR).
    No API key required.
    """
    try:
        r = requests.get(
            f"https://issuehunt.io/api/v1/issues?state=open&sort=funded_at&limit={limit}",
            timeout=_TIMEOUT,
        )
        if not r.ok or "application/json" not in r.headers.get("Content-Type", ""):
            return []

        data = r.json()
        issues: list[dict] = data if isinstance(data, list) else data.get("data", [])

        return [
            {
                "source": "issuehunt",
                "title": i.get("title", ""),
                "repo": i.get("repo_full_name", ""),
                "reward_usd": _safe_float(i.get("funded_amount")),
                "currency": "USD",
                "url": i.get("html_url", ""),
                "labels": [lbl.get("name") for lbl in (i.get("labels") or []) if isinstance(lbl, dict)],
                "paid_before": True,  # IssueHunt escrows funds before listing
            }
            for i in issues
            if _safe_float(i.get("funded_amount")) > 0
        ]
    except Exception:
        return []


# ─── Algora ───────────────────────────────────────────────────────────────────

def scan_algora(limit: int = 20) -> list[dict]:
    """
    Fetch open bounties from Algora (open-source USDC bounties).
    No API key required.
    """
    try:
        r = requests.get(
            "https://console.algora.io/api/bounties?status=open&limit=" + str(limit),
            timeout=_TIMEOUT,
        )
        if not r.ok or "application/json" not in r.headers.get("Content-Type", ""):
            # Try alternative endpoint
            r = requests.get(
                "https://console.algora.io/api/trpc/bounty.list?input=%7B%22status%22%3A%22open%22%7D",
                timeout=_TIMEOUT,
            )
            if not r.ok or "application/json" not in r.headers.get("Content-Type", ""):
                return []

        data = r.json()
        # Handle both direct array and nested response
        if isinstance(data, list):
            bounties = data[:limit]
        else:
            bounties = (
                data.get("result", {}).get("data", {}).get("bounties", [])
                or data.get("data", [])
                or []
            )[:limit]

        res_bounties = []
        for b in bounties:
            issue = b.get("issue") if isinstance(b.get("issue"), dict) else {}
            repo_info = issue.get("repo") if isinstance(issue.get("repo"), dict) else {}
            amt = _safe_float(b.get("total_amount") or b.get("amount"))
            if amt > 0:
                res_bounties.append({
                    "source": "algora",
                    "title": issue.get("title") or b.get("title", ""),
                    "repo": repo_info.get("full_name") or b.get("repo", ""),
                    "reward_usd": amt,
                    "currency": (b.get("currency") or "USD").upper(),
                    "url": issue.get("url") or b.get("url", ""),
                    "paid_before": True,  # Algora holds funds in escrow
                })
        return res_bounties
    except Exception as e:
        console.print(f"  [dim]Algora scan error: {e}[/dim]")
        return []


# ─── GitHub bounty search ─────────────────────────────────────────────────────

def scan_github_bounties(limit: int = 10) -> list[dict]:
    """
    Search GitHub for open issues labelled 'bounty' in known paying repos.
    Uses the public search API (no auth needed, 10 req/min limit).
    """
    try:
        headers = {"Accept": "application/vnd.github+json"}
        if cfg.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {cfg.GITHUB_TOKEN}"

        # Search for open bounty-labelled issues, sorted by recent activity
        r = requests.get(
            "https://api.github.com/search/issues"
            "?q=label:bounty+state:open+is:issue"
            "&sort=updated&order=desc"
            f"&per_page={limit}",
            headers=headers,
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return []

        items = r.json().get("items", [])
        return [
            {
                "source": "github",
                "title": i.get("title", ""),
                "repo": i.get("repository_url", "").split("repos/")[-1],
                "reward_usd": None,  # amount not in GitHub API, check issue body
                "url": i.get("html_url", ""),
                "body_snippet": (i.get("body") or "")[:1000],
                "labels": [l.get("name") for l in (i.get("labels") or [])],
                "paid_before": True,
            }
            for i in items
        ]
    except Exception as e:
        console.print(f"  [dim]GitHub bounty search error: {e}[/dim]")
        return []


# ─── Combined scanner ─────────────────────────────────────────────────────────

def scan_all(verbose: bool = True) -> dict[str, Any]:
    """
    Run all scanners and return a combined result dict.

    Returns:
        {
          "superteam": {...},
          "issuehunt": [...],
          "algora": [...],
          "github": [...],
          "all": [...],     # deduplicated, sorted by reward_usd desc
          "total": int,
        }
    """
    if verbose:
        console.print("  [dim]Scanning Superteam...[/dim]", end="")
    superteam = scan_superteam()
    if verbose:
        count = len(superteam.get("open", [])) if "open" in superteam else 0
        console.print(f" [green]{count} open[/green]")

    if verbose:
        console.print("  [dim]Scanning IssueHunt...[/dim]", end="")
    issuehunt = scan_issuehunt()
    if verbose:
        console.print(f" [green]{len(issuehunt)} open[/green]")

    if verbose:
        console.print("  [dim]Scanning Algora...[/dim]", end="")
    algora = scan_algora()
    if verbose:
        console.print(f" [green]{len(algora)} open[/green]")

    if verbose:
        console.print("  [dim]Scanning GitHub bounty issues...[/dim]", end="")
    github = scan_github_bounties()
    if verbose:
        console.print(f" [green]{len(github)} found[/green]")

    # Merge all opportunities that have a verified positive payout (> $0)
    raw_opps: list[dict] = []
    if isinstance(superteam, dict) and "open" in superteam:
        raw_opps.extend(superteam["open"])
    raw_opps.extend(issuehunt)
    raw_opps.extend(algora)
    # Only include GitHub issues if they have a confirmed positive reward
    raw_opps.extend([g for g in github if _safe_float(g.get("reward_usd")) > 0])

    all_opps: list[dict] = [o for o in raw_opps if _safe_float(o.get("reward_usd")) > 0]

    # Sort: verified payment first, then by reward descending
    all_opps.sort(
        key=lambda x: (
            not x.get("paid_before"),       # verified payers first
            -_safe_float(x.get("reward_usd")),    # highest reward first
        )
    )

    return {
        "superteam": superteam,
        "issuehunt": issuehunt,
        "algora": algora,
        "github": github,
        "all": all_opps,
        "total": len(all_opps),
    }

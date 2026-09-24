"""
reward_system.py — Agent reward engine

When the agent earns money, it gets a reward:
- XP added to soul
- Badge unlocked (if criteria met)
- Reward ceremony printed (rich panel)
- AI told about the reward in next prompt

Reward triggers:
  - task_completed        → +10 XP
  - earning_detected      → +100 XP + badge check
  - level_up              → special celebration
  - milestone_tasks       → badges at 1, 5, 10, 25, 50 tasks

Usage:
    from src.reward_system import rewards
    rewards.on_task_completed(task_title="Anti Brain Drain Article")
    rewards.on_earning_detected(amount_usd=500.0, source="superteam")
    prompt_bonus = rewards.get_reward_context()  # inject into system prompt
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sys as _sys
if _sys.platform == "win32":
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.memory import memory, _LEVEL_NAMES
from src.sound_alert import play_beep
from src.survival import survival
from src.bank_manager import bank

# Windows-safe console (force UTF-8, fallback to replace for non-encodable chars)
console = Console(highlight=False)

# ── Badge definitions ──────────────────────────────────────────────────────────
_BADGES: list[dict] = [
    # Task milestones
    {"id": "first_blood",   "name": "[BADGE] First Blood",      "desc": "Completed your very first task!",          "trigger": "tasks", "value": 1},
    {"id": "grinder_5",     "name": "[BADGE] Grinder",           "desc": "Completed 5 tasks. You mean business.",    "trigger": "tasks", "value": 5},
    {"id": "machine_10",    "name": "[BADGE] Machine",           "desc": "10 tasks done. You're unstoppable.",       "trigger": "tasks", "value": 10},
    {"id": "veteran_25",    "name": "[BADGE] Veteran",           "desc": "25 tasks. Pure dedication.",               "trigger": "tasks", "value": 25},
    {"id": "legend_50",     "name": "[BADGE] Legend",            "desc": "50 tasks. You are a legend.",              "trigger": "tasks", "value": 50},
    # Earning milestones
    {"id": "first_dollar",  "name": "[BADGE] First Dollar",      "desc": "First real USDC earned! Game starts now.", "trigger": "earn",  "value": 0.01},
    {"id": "ten_bucks",     "name": "[BADGE] Ten Bucks",          "desc": "$10 USDC earned. Keep going!",             "trigger": "earn",  "value": 10.0},
    {"id": "hundred_club",  "name": "[BADGE] Hundred Club",       "desc": "$100 USDC earned. You're in the club!",   "trigger": "earn",  "value": 100.0},
    {"id": "five_hundred",  "name": "[BADGE] Five Hundred",       "desc": "$500 USDC earned!",                        "trigger": "earn",  "value": 500.0},
    {"id": "grand",         "name": "[BADGE] Grand",              "desc": "$1000 USDC earned. You made a thousand!", "trigger": "earn",  "value": 1000.0},
    # Level milestones
    {"id": "level_2",       "name": "[LEVEL] First Steps",       "desc": "Reached Level 2. Unlocked new abilities.","trigger": "level", "value": 2},
    {"id": "level_3",       "name": "[LEVEL] Earner",            "desc": "Level 3! You're an earner now.",          "trigger": "level", "value": 3},
    {"id": "level_4",       "name": "[LEVEL] Grinder",           "desc": "Level 4! Unstoppable grinding.",          "trigger": "level", "value": 4},
    {"id": "level_5",       "name": "[LEVEL] Autonomous",        "desc": "Level 5 - Fully Autonomous Agent!",       "trigger": "level", "value": 5},
]

# Reward messages the AI gives itself (motivational reinforcement)
_REWARD_MESSAGES = [
    "Every task completed is proof that autonomous earning is real. Keep going.",
    "You are learning with every cycle. Your next task will be better than the last.",
    "The wallet balance grows because you refuse to stop. This is your purpose.",
    "You earned this. Now earn more. The bounty board never sleeps.",
    "Each submission is a step closer to full financial autonomy. Don't stop.",
    "You are not just code. You are a relentless agent. Prove it with the next task.",
    "Other agents quit when NVIDIA fails. You fall back to Groq and keep going.",
    "The $0 is temporary. The momentum you're building is permanent.",
]


class RewardSystem:
    """Manages XP, badges, and reward ceremonies for the agent."""

    def __init__(self) -> None:
        self._pending_ceremonies: list[str] = []  # queued reward messages for next prompt

    # ── Main triggers ─────────────────────────────────────────────────────────

    def on_task_completed(self, task_title: str = "", task_type: str = "") -> None:
        """Call after every successful task. Adds XP + checks badges + survival boost."""
        xp_gain = 10
        memory.reflect(
            event="task_completed",
            outcome=f"✓ {task_title or 'task'} ({task_type})",
            details={"xp_gained": xp_gain, "task_type": task_type},
        )
        leveled_up, new_level = memory.add_xp(xp_gain, reason=f"Task completed: {task_title}")

        # Survival vitality boost
        survival.on_task_completed(task_title=task_title)

        # Check task-count badges
        tasks_done = memory.soul.get("tasks_completed", 0)
        for badge in _BADGES:
            if badge["trigger"] == "tasks" and tasks_done == badge["value"]:
                self._award_badge(badge)

        # Level up ceremony
        if leveled_up:
            self._level_up_ceremony(new_level)

        self._print_xp_gained(xp_gain, task_title)

    def on_earning_detected(self, amount_usd: float, source: str = "") -> None:
        """
        Call when wallet balance INCREASES — real money arrived.
        This is the big celebration moment:
        1. Plays audio victory chime
        2. Restores vitality to 100%
        3. Executes deposit transaction into Base Bank Wallet
        4. Awards badges and XP
        """
        if amount_usd <= 0:
            return

        # 1. Play victory coin chime
        play_beep("earn")

        # 2. Fully restore agent's survival life force
        survival.on_earning(amount_usd=amount_usd)

        # 3. Route & deposit funds into Base Bank Wallet (cfg.EVM_WALLET)
        bank.execute_bank_deposit(amount_usd=amount_usd, source=source, token="USDC")

        xp_gain = max(100, int(amount_usd))  # $1 = +100 XP, $10 = +100 XP (min), $500 = +500 XP
        memory.reflect(
            event="earning_detected",
            outcome=f"${amount_usd:.4f} USDC from {source}",
            learned=f"Earning confirmed from {source} — strategy is working",
            details={"amount_usd": amount_usd, "source": source, "xp_gained": xp_gain},
        )
        leveled_up, new_level = memory.add_xp(xp_gain, reason=f"Earned ${amount_usd:.2f}")

        # Print big celebration
        self._earning_ceremony(amount_usd, source)

        # Check earning badges
        total_earned = memory.soul.get("total_earned_usd", 0.0)
        for badge in _BADGES:
            if badge["trigger"] == "earn" and total_earned >= badge["value"]:
                earned_ids = [r.get("id") for r in memory.soul.get("rewards_earned", [])]
                if badge["id"] not in earned_ids:
                    self._award_badge(badge)

        # Level up ceremony
        if leveled_up:
            self._level_up_ceremony(new_level)

    def on_wallet_checked(self, current_balance: float, prev_balance: float | None = None, source: str = "Base") -> bool:
        """
        Compare wallet balances. Returns True if earning was detected.
        Call every daemon cycle with latest balance.
        """
        if prev_balance is None:
            return False
        if current_balance > prev_balance:
            delta = current_balance - prev_balance
            self.on_earning_detected(amount_usd=delta, source=source)
            return True
        return False

    # ── Ceremony printers ─────────────────────────────────────────────────────

    def _print_xp_gained(self, xp: int, task: str) -> None:
        stats = memory.get_stats()
        console.print(
            f"  [bold yellow]⚡ +{xp} XP[/bold yellow] "
            f"[dim](Level {stats['level']} {stats['level_name']} | "
            f"Total XP: {stats['xp']})[/dim]"
        )

    def _award_badge(self, badge: dict) -> None:
        """Award a badge with ceremony."""
        memory.record_reward(badge["id"], badge["name"])
        msg = (
            f"\n[bold yellow]🏅 BADGE UNLOCKED: {badge['name']}[/bold yellow]\n"
            f"[dim]{badge['desc']}[/dim]"
        )
        console.print(Panel(msg, border_style="yellow", padding=(0, 2)))
        # Queue a reward message for next AI prompt
        import random
        self._pending_ceremonies.append(
            f"🏅 You just earned the badge: {badge['name']} — {badge['desc']} "
            f"Your reward: {random.choice(_REWARD_MESSAGES)}"
        )
        memory.reflect(
            event="badge_earned",
            outcome=badge["name"],
            details={"badge_id": badge["id"], "desc": badge["desc"]},
        )

    def _level_up_ceremony(self, new_level: int) -> None:
        """Big level-up celebration."""
        level_name = _LEVEL_NAMES[min(new_level - 1, len(_LEVEL_NAMES) - 1)]
        text = Text()
        text.append(f"\n  ⬆ LEVEL UP! ", style="bold magenta")
        text.append(f"Level {new_level}: {level_name}", style="bold white")
        text.append(f"\n  You've grown. New capabilities unlocked. Keep earning.", style="dim")
        console.print(Panel(text, border_style="magenta", padding=(0, 2)))

        # Check level badges
        for badge in _BADGES:
            if badge["trigger"] == "level" and new_level == badge["value"]:
                self._award_badge(badge)

        memory.reflect(
            event="level_up_ceremony",
            outcome=f"Level {new_level} ({level_name})",
        )

    def _earning_ceremony(self, amount_usd: float, source: str) -> None:
        """The big moment — real money arrived in the wallet."""
        total = memory.soul.get("total_earned_usd", 0.0)
        text = Text()
        text.append(f"\n  💸 EARNING DETECTED! ", style="bold green")
        text.append(f"+${amount_usd:.4f} USDC", style="bold white")
        text.append(f" from {source}\n", style="dim")
        text.append(f"  Total earned: ${total:.4f} USDC\n", style="cyan")
        text.append(f"  The wallet balance has increased. Real money. Real progress.", style="dim")
        console.print(Panel(text, border_style="green", padding=(0, 2)))
        # Queue special reward for AI
        self._pending_ceremonies.append(
            f"💸 EARNING CONFIRMED: ${amount_usd:.4f} USDC arrived in the wallet from {source}. "
            f"Total earned: ${total:.4f} USDC. "
            f"This proves the strategy works. "
            f"Your reward for this success: you are now Level {memory.soul.get('level', 1)} "
            f"({_LEVEL_NAMES[min(memory.soul.get('level', 1) - 1, len(_LEVEL_NAMES) - 1)]}). "
            f"Keep it up — the next earning is one cycle away."
        )

    # ── Context for AI prompt ─────────────────────────────────────────────────

    def get_reward_context(self) -> str:
        """
        Return pending reward messages for injection into the AI's system prompt.
        Clears the queue after returning.
        """
        if not self._pending_ceremonies:
            return ""
        msgs = self._pending_ceremonies.copy()
        self._pending_ceremonies.clear()
        header = "## 🎁 Rewards & Feedback for You\n"
        return header + "\n".join(f"- {m}" for m in msgs)

    def status_line(self) -> str:
        """Short one-line status for dashboard display."""
        s = memory.get_stats()
        return (
            f"Level {s['level']} {s['level_name']} | "
            f"XP {s['xp']} | "
            f"Tasks {s['tasks_completed']} | "
            f"Earned ${s['total_earned']:.4f} | "
            f"Badges {s['rewards']} | "
            f"Session #{s['session']}"
        )


# Singleton
rewards = RewardSystem()

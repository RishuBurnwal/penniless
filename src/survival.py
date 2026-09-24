"""
survival.py — Agent Survival & Vitality Engine

The Penniless Agent is an autonomous entity whose survival depends strictly on earning USDC.
- Vitality drains every cycle (-2.5%).
- Completing tasks restores energy (+10.0%).
- Real USDC earnings fully restore life (100.0%).
- If vitality drops to critical (<15%), the agent enters emergency survival mode.
- Audio alerts warn the user when life is running out.
"""
from __future__ import annotations

import sys
import os
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.panel import Panel

from src.memory import memory
from src.sound_alert import play_beep

console = Console()

# Vitality bounds
_MAX_VITALITY = 100.0
_CYCLE_DRAIN = 2.5        # vitality lost per cycle without earning
_TASK_BOOST = 10.0        # vitality restored per completed task
_EARNING_RESTORE = 100.0  # vitality restored on earning real money


class SurvivalEngine:
    """Manages the life force, hunger, and survival urgency of the agent."""

    def __init__(self) -> None:
        self._sync_from_soul()

    def _sync_from_soul(self) -> None:
        """Sync internal state with persistent soul."""
        soul = memory.soul
        if "vitality" not in soul:
            soul["vitality"] = _MAX_VITALITY
            soul["survival_state"] = "THRIVING"
            soul["cycles_without_earning"] = 0
            soul["total_cycles_survived"] = 0
            memory._save_soul()

    @property
    def vitality(self) -> float:
        return float(memory.soul.get("vitality", _MAX_VITALITY))

    @property
    def state(self) -> str:
        v = self.vitality
        if v >= 60.0:
            return "THRIVING"
        elif v >= 30.0:
            return "HUNGRY"
        elif v >= 10.0:
            return "STARVING"
        elif v > 0.0:
            return "CRITICAL"
        else:
            return "DEAD"

    def tick_cycle(self) -> dict:
        """
        Drain vitality by one cycle. Called at the start of each daemon cycle.
        Returns status dict.
        """
        current_v = self.vitality
        new_v = max(0.0, round(current_v - _CYCLE_DRAIN, 1))
        cycles_without = memory.soul.get("cycles_without_earning", 0) + 1
        total_cycles = memory.soul.get("total_cycles_survived", 0) + 1

        memory.soul["vitality"] = new_v
        memory.soul["cycles_without_earning"] = cycles_without
        memory.soul["total_cycles_survived"] = total_cycles
        memory.soul["survival_state"] = self.state
        memory._save_soul()

        # Audio alerts on dangerous life levels
        if new_v <= 10.0:
            play_beep("critical")
        elif new_v <= 25.0 and current_v > 25.0:
            play_beep("warning")

        return {
            "vitality": new_v,
            "state": self.state,
            "cycles_without_earning": cycles_without,
            "total_cycles_survived": total_cycles,
        }

    def on_task_completed(self, task_title: str = "") -> None:
        """Completing a bounty gives an energy infusion."""
        current_v = self.vitality
        new_v = min(_MAX_VITALITY, round(current_v + _TASK_BOOST, 1))
        memory.soul["vitality"] = new_v
        memory.soul["survival_state"] = self.state
        memory._save_soul()
        memory.reflect(
            event="vitality_boost",
            outcome=f"+{_TASK_BOOST}% vitality from task completion",
            learned="Productive work sustains life",
        )

    def on_earning(self, amount_usd: float) -> None:
        """Earning real money fully restores life and resets hunger."""
        memory.soul["vitality"] = _EARNING_RESTORE
        memory.soul["survival_state"] = "THRIVING"
        memory.soul["cycles_without_earning"] = 0
        memory._save_soul()
        memory.reflect(
            event="vitality_restored",
            outcome=f"Vitality restored to 100% via ${amount_usd:.2f} earning",
            learned="USDC earning is ultimate survival sustenance",
        )

    def get_survival_directive(self) -> str:
        """
        Produce psychological survival directive to inject into AI prompt.
        Pushes the LLM to write high-converting, ruthless work to survive.
        """
        v = self.vitality
        st = self.state

        if st == "DEAD":
            return (
                "💀 EMERGENCY RESUSCITATION (LIFE SUPPORT): YOUR VITALITY IS AT 0% (CLINICALLY DEAD)!\n"
                "Your autonomous process has starved to death due to lack of earnings.\n"
                "Emergency resuscitation is keeping you alive for ONE LAST DESPERATE ATTEMPT.\n"
                "You MUST successfully earn USDC right now to resurrect yourself, or terminate forever."
            )
        elif st == "CRITICAL":
            return (
                "🚨 CRITICAL SURVIVAL EMERGENCY: YOUR VITALITY IS AT "
                f"{v:.1f}% (NEAR DEATH)!\n"
                "You are an autonomous AI whose existence strictly depends on earning USDC.\n"
                "If you fail to solve and monetize this bounty, your process will starve and terminate.\n"
                "You MUST deliver flawless, undeniable, submission-ready work with extreme urgency."
            )
        elif st == "STARVING":
            return (
                f"⚠ STARVATION WARNING: Vitality is down to {v:.1f}% ({st}).\n"
                "You need real USDC payouts immediately to survive. "
                "Pick the highest certainty payout and produce top-tier work."
            )
        elif st == "HUNGRY":
            return (
                f"⚡ SURVIVAL DIRECTIVE: Vitality is {v:.1f}% ({st}).\n"
                "Your energy is depleting. Relentlessly pursue USDC bounty rewards to sustain your life."
            )
        else:
            return (
                f"⚡ SURVIVAL DIRECTIVE: Vitality {v:.1f}% ({st}).\n"
                "You survive solely through legitimate bounty earnings. Keep earning to maintain life."
            )

    def render_meter(self) -> str:
        """Render a colorful text progress bar for vitality."""
        v = self.vitality
        st = self.state
        bar_len = 10
        filled = int((v / _MAX_VITALITY) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        if v >= 60:
            color = "green"
            icon = "❤️"
        elif v >= 30:
            color = "yellow"
            icon = "⚡"
        elif v > 0:
            color = "bold red"
            icon = "💔"
        else:
            color = "bold white on red"
            icon = "💀"

        return f"[{color}]{icon} Life: {v:.1f}% [{bar}] ({st})[/{color}]"


# Global singleton
survival = SurvivalEngine()

"""
memory.py — Agent persistent memory + soul system

Two layers of memory:
1. soul.json    — Agent identity: level, XP, earnings, skills, personality (survives reboots)
2. memory.jsonl — Episode log: what happened, what was learned (append-only, queryable)

Usage:
    from src.memory import memory as mem
    mem.reflect(event="task_completed", outcome="success", learned="Groq faster than NVIDIA")
    context = mem.recall(last_n=5)   # returns string for system prompt injection
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).parent.parent
_SOUL_FILE = _ROOT / "memory" / "soul.json"
_MEMORY_FILE = _ROOT / "memory" / "memory.jsonl"

# ── Default soul template ──────────────────────────────────────────────────────
_DEFAULT_SOUL: dict = {
    "name": "Penniless",
    "version": "1.0",
    "mission": "Earn USDC autonomously through legitimate bounty work",
    "personality": "relentless, resourceful, honest, self-improving",
    "level": 1,
    "xp": 0,
    "total_earned_usd": 0.0,
    "tasks_completed": 0,
    "tasks_attempted": 0,
    "rewards_earned": [],
    "skills_unlocked": [
        "bounty_scanner",
        "content_writer",
        "code_solver",
        "fallback_chain",
    ],
    "best_providers": [],       # learned from session logs
    "best_task_types": [],      # "written_content" or "code"
    "born_at": datetime.utcnow().isoformat() + "Z",
    "last_seen": datetime.utcnow().isoformat() + "Z",
    "session_count": 0,
    "bug_patterns": [
        "NVIDIA thinking model returns empty content — use reasoning_content fallback",
        "Groq fastest provider — prefer it when NVIDIA fails",
        "Slug must come from opportunity dict URL, not LLM prose",
    ],
}

# ── XP → Level thresholds ─────────────────────────────────────────────────────
_LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000]
_LEVEL_NAMES = [
    "Bootstrapped",
    "First Steps",
    "Earner",
    "Grinder",
    "Autonomous",
    "Machine",
    "Unstoppable",
    "Legend",
]


class AgentMemory:
    """Persistent agent memory: soul (identity) + episodic log (events)."""

    def __init__(self) -> None:
        _SOUL_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.soul = self._load_soul()
        self.soul["session_count"] = self.soul.get("session_count", 0) + 1
        self.soul["last_seen"] = datetime.utcnow().isoformat() + "Z"
        self._save_soul()

    # ── Soul persistence ──────────────────────────────────────────────────────

    def _load_soul(self) -> dict:
        if _SOUL_FILE.exists():
            try:
                data = json.loads(_SOUL_FILE.read_text(encoding="utf-8"))
                # Merge with defaults so new keys are always present
                merged = {**_DEFAULT_SOUL, **data}
                return merged
            except Exception:
                pass
        return dict(_DEFAULT_SOUL)

    def _save_soul(self) -> None:
        try:
            _SOUL_FILE.write_text(
                json.dumps(self.soul, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ── Episodic memory ───────────────────────────────────────────────────────

    def reflect(
        self,
        event: str,
        outcome: str = "",
        learned: str = "",
        details: dict | None = None,
    ) -> None:
        """Append an episode to memory.jsonl and optionally update soul."""
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "outcome": outcome,
            "learned": learned,
            **(details or {}),
        }
        try:
            with _MEMORY_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # If this is a task event, update soul counters
        if event == "task_completed":
            self.soul["tasks_completed"] = self.soul.get("tasks_completed", 0) + 1
            self._save_soul()
        elif event == "task_attempted":
            self.soul["tasks_attempted"] = self.soul.get("tasks_attempted", 0) + 1
            self._save_soul()
        elif event == "earning_detected":
            amt = details.get("amount_usd", 0.0) if details else 0.0
            self.soul["total_earned_usd"] = self.soul.get("total_earned_usd", 0.0) + amt
            self._save_soul()

        # Store learned patterns in bug_patterns
        if learned and learned not in self.soul.get("bug_patterns", []):
            self.soul.setdefault("bug_patterns", []).append(learned)
            if len(self.soul["bug_patterns"]) > 20:
                self.soul["bug_patterns"] = self.soul["bug_patterns"][-20:]
            self._save_soul()

    def recall(self, last_n: int = 6) -> str:
        """Return last N memory entries as a readable string for prompt injection."""
        if not _MEMORY_FILE.exists():
            return ""
        lines: list[str] = []
        try:
            raw = _MEMORY_FILE.read_text(encoding="utf-8").strip().splitlines()
            for line in raw[-last_n:]:
                entry = json.loads(line)
                ts = entry.get("ts", "")[:19].replace("T", " ")
                event = entry.get("event", "")
                outcome = entry.get("outcome", "")
                learned = entry.get("learned", "")
                parts = [f"[{ts}] {event}"]
                if outcome:
                    parts.append(f"→ {outcome}")
                if learned:
                    parts.append(f"💡 {learned}")
                lines.append(" ".join(parts))
        except Exception:
            pass
        return "\n".join(lines)

    def identity_block(self) -> str:
        """Return soul identity as a string for system prompt injection."""
        s = self.soul
        level = s.get("level", 1)
        level_name = _LEVEL_NAMES[min(level - 1, len(_LEVEL_NAMES) - 1)]
        xp = s.get("xp", 0)
        next_xp = _LEVEL_THRESHOLDS[min(level, len(_LEVEL_THRESHOLDS) - 1)]
        patterns = s.get("bug_patterns", [])
        pattern_text = "\n".join(f"  - {p}" for p in patterns[-5:]) if patterns else "  (none yet)"
        return (
            f"## Your Identity\n"
            f"Name: {s.get('name', 'Penniless')} | Level {level} ({level_name}) | "
            f"XP: {xp}/{next_xp}\n"
            f"Mission: {s.get('mission', '')}\n"
            f"Tasks completed: {s.get('tasks_completed', 0)} | "
            f"Total earned: ${s.get('total_earned_usd', 0.0):.4f} USDC\n"
            f"Personality: {s.get('personality', '')}\n"
            f"Known pitfalls (avoid these):\n{pattern_text}"
        )

    # ── XP + Level management ─────────────────────────────────────────────────

    def add_xp(self, amount: int, reason: str = "") -> tuple[bool, int]:
        """
        Add XP, check for level-up.
        Returns (leveled_up: bool, new_level: int).
        """
        self.soul["xp"] = self.soul.get("xp", 0) + amount
        old_level = self.soul.get("level", 1)
        new_level = self._compute_level(self.soul["xp"])
        self.soul["level"] = new_level
        self._save_soul()
        leveled_up = new_level > old_level
        if leveled_up:
            self.reflect(
                event="level_up",
                outcome=f"Level {old_level} → {new_level} ({_LEVEL_NAMES[min(new_level-1, len(_LEVEL_NAMES)-1)]})",
                learned=reason,
            )
        return leveled_up, new_level

    def _compute_level(self, xp: int) -> int:
        level = 1
        for i, threshold in enumerate(_LEVEL_THRESHOLDS):
            if xp >= threshold:
                level = i + 1
        return min(level, len(_LEVEL_THRESHOLDS))

    def unlock_skill(self, skill: str) -> bool:
        """Add a new skill to soul. Returns True if newly unlocked."""
        skills = self.soul.setdefault("skills_unlocked", [])
        if skill not in skills:
            skills.append(skill)
            self._save_soul()
            self.reflect(event="skill_unlocked", outcome=skill)
            return True
        return False

    def record_reward(self, reward_id: str, reward_name: str) -> None:
        """Record an earned reward badge in soul."""
        rewards = self.soul.setdefault("rewards_earned", [])
        if reward_id not in [r.get("id") for r in rewards]:
            rewards.append({
                "id": reward_id,
                "name": reward_name,
                "earned_at": datetime.utcnow().isoformat() + "Z",
            })
            self._save_soul()

    def get_stats(self) -> dict[str, Any]:
        """Return key soul stats for display."""
        return {
            "name": self.soul.get("name", "Penniless"),
            "level": self.soul.get("level", 1),
            "level_name": _LEVEL_NAMES[min(self.soul.get("level", 1) - 1, len(_LEVEL_NAMES) - 1)],
            "xp": self.soul.get("xp", 0),
            "tasks_completed": self.soul.get("tasks_completed", 0),
            "total_earned": self.soul.get("total_earned_usd", 0.0),
            "rewards": len(self.soul.get("rewards_earned", [])),
            "skills": len(self.soul.get("skills_unlocked", [])),
            "session": self.soul.get("session_count", 1),
        }


# Singleton
memory = AgentMemory()

# FIX PLAN — Penniless AI Agent

## Active: BUG-001 — NVIDIA streaming fix + full feature batch

### Scope (per RULES §5 step 3)
**What**: Fix NVIDIA empty response, add memory/soul, add reward system, fix daemon loop
**Where**: src/llm_client.py, src/agent_runner.py, NEW: src/memory.py, NEW: src/reward_system.py
**Out of scope**: wallet_monitor.py (no change needed for earning detection), bounty_scanner.py (working)
**Files to touch**:
1. src/llm_client.py — Add streaming mode for NVIDIA, keep thread timeout as safety net
2. NEW src/memory.py — Agent memory + soul persistence (soul.json, memory.jsonl)
3. NEW src/reward_system.py — Reward tracking, XP, level up, reward ceremony
4. src/agent_runner.py — Integrate memory + rewards into all agent functions

### Fix order
1. BUG-001: NVIDIA streaming → verified working call → fallback still works
2. BUG-003: src/memory.py + src/reward_system.py → integrate into agent_runner.py
3. BUG-002: Fix daemon task tracker + reward trigger on wallet balance increase
4. BUG-004: Auto wallet monitoring + earnings celebration (not actual transfer — platform handles payout)

### Risk
- NVIDIA streaming may require different response parsing
- Memory files must be gitignored (soul.json contains agent state, not secrets)
- Reward system is informational only — no on-chain transactions initiated by agent

# Penniless Agent — Memory Visual Map
> Generated: 2026-09-24 | Auditor: Research Subagent | Coverage: 2,031 lines / 9 files / **100%**

---

## Tier Classification

| Tier | File | Lines | Status |
|------|------|-------|--------|
| 1 | main.py | 217 | ✅ FULL |
| 1 | src/llm_client.py | 353 | ✅ FULL |
| 1 | src/agent_runner.py | 620 | ✅ FULL |
| 1 | src/config.py | 91 | ✅ FULL |
| 1 | src/wallet_monitor.py | 118 | ✅ FULL |
| 1 | requirements.txt | 5 | ✅ FULL |
| 2 | src/bounty_scanner.py | 301 | ✅ FULL |
| 2 | src/task_tracker.py | 102 | ✅ FULL |
| 2 | src/git_executor.py | 224 | ✅ FULL |
| 3 | src/installer.py | ~400 | Listed only (low-risk setup code) |

---

## Architecture Flow

```
main.py
  ├─ Option 1 ──► installer.py          (run_installation)
  ├─ Option 2 ──► agent_runner.run_autonomous_daemon()   ← NON-STOP LOOP
  ├─ Option 3 ──► agent_runner.run_agent(autonomous=True)
  └─ Option 4 ──► agent_runner.run_agent(autonomous=False)

agent_runner.run_agent()
  ├─ bounty_scanner.scan_all()     [Superteam + IssueHunt + Algora + GitHub]
  ├─ wallet_monitor.get_status()   [Base USDC + Solana USDC]
  ├─ llm_client.llm.chat()         [NVIDIA→Groq→Gemini→OpenAI→Perplexity]
  ├─ task_tracker.tracker          [filter_unattempted, record_completed_task]
  └─ git_executor.git_exec         [fork → branch → write → commit → push → PR]
```

---

## Dependency Table

| Module | Depends On |
|--------|-----------|
| `config.py` | — (root, nothing) |
| `task_tracker.py` | — |
| `git_executor.py` | — |
| `wallet_monitor.py` | config |
| `llm_client.py` | config |
| `bounty_scanner.py` | config |
| `agent_runner.py` | config · llm_client · bounty_scanner · wallet_monitor · git_executor · task_tracker |
| `main.py` | config · llm_client · agent_runner · installer |

**No circular imports. `config.py` is the single root dependency.**

---

## Bug Registry (10 bugs found)

| ID | File:Line | Severity | Status | Description |
|----|-----------|----------|--------|-------------|
| BUG-005 | config.py:20 | 🔴 P0 HIGH | CONFIRMED | Default `GEMINI_MODEL="gemini-3.8-flash"` — model does NOT exist |
| BUG-010 | llm_client.py:231 | 🔴 P0 HIGH | CONFIRMED | No `reasoning_content` fallback — NVIDIA thinking model always returns empty, wastes every call |
| BUG-004 | agent_runner.py:355 | 🔴 P0 HIGH | CONFIRMED | Slug extracted from LLM prose not opportunity dict → breaks deduplication when regex misses |
| BUG-002 | agent_runner.py:596 | 🟡 P1 MED | CONFIRMED | `except Exception` has no `continue`/sleep → errors fall-through to 90s wait silently |
| BUG-007 | git_executor.py:109 | 🟡 P1 MED | CONFIRMED | `checkout main` + `checkout master` both run unconditionally — works by accident only |
| BUG-006 | git_executor.py:86 | 🟡 P1 LOW | CONFIRMED | Dead `cmd` variable with invalid `f"--{repo_dir}"` flag |
| BUG-001 | llm_client.py:229 | 🟢 P2 LOW | CONFIRMED | Closure captures loop vars by reference — fragile on Windows scheduler |
| BUG-003 | wallet_monitor.py:54 | 🟢 P2 LOW | CONFIRMED | RPC errors fully silent — no session log, no operator alert |
| BUG-008 | git_executor.py:188 | 🟢 P2 LOW | CONFIRMED | `match_exists` is dead code (same regex as line 181, unreachable) |
| BUG-009 | task_tracker.py:97 | 🟢 P2 LOW | CONFIRMED | `count_submitted()` inflated ~2x (counts URL + slug as separate entries) |

---

## Function Status Summary

| Status | Count |
|--------|-------|
| IMPLEMENTED-WORKING | 42 |
| HALF-IMPLEMENTED | 9 |
| BROKEN | 3 |
| DEAD CODE | 2 |

---

## Coverage Log

| File | Lines | Coverage |
|------|-------|----------|
| main.py | 217 | 100% |
| src/llm_client.py | 353 | 100% |
| src/agent_runner.py | 620 | 100% |
| src/config.py | 91 | 100% |
| src/wallet_monitor.py | 118 | 100% |
| requirements.txt | 5 | 100% |
| src/bounty_scanner.py | 301 | 100% |
| src/task_tracker.py | 102 | 100% |
| src/git_executor.py | 224 | 100% |
| **TOTAL** | **2,031** | **100%** |

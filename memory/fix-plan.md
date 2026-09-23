# FIX PLAN — Penniless AI Agent

## Active: Batch BUG-011 to BUG-019 (Code & Logic Quality Overhaul)

### Scope (per RULES §5 step 3)
**What**: Fix tracker double counting, prevent false earning triggers on startup, ensure code task deduplication, clean deprecations, align badge names, remove dead code, safeguard scanner null types, fix installer Groq model, and fix daemon exit UX.
**Files to touch**:
1. `src/task_tracker.py` — BUG-011: Separate `seen_slugs` and maintain explicit `_submitted_count` loaded from lines.
2. `src/agent_runner.py` — BUG-012 & BUG-013: Set `prev_balance = None` on startup; pass `opportunity` to `_execute_code_task` and track real task URL.
3. `src/reward_system.py` — BUG-012 & BUG-015: Safeguard `prev_balance is None`; align level badge names with `_LEVEL_NAMES` in `memory.py`.
4. `src/memory.py` — BUG-014: Replace `datetime.utcnow()` with `datetime.now(timezone.utc).isoformat()`.
5. `src/llm_client.py` — BUG-014: Replace `datetime.utcnow()` with `datetime.now(timezone.utc).isoformat()`.
6. `src/git_executor.py` — BUG-016: Remove dead `cmd` definition.
7. `src/bounty_scanner.py` — BUG-017: Protect against `None` values on numeric fields and nested dictionaries.
8. `src/installer.py` — BUG-018: Update Groq test model to `qwen/qwen3.8-27b` and update comments.
9. `main.py` — BUG-019: Add `input("  Press Enter to return to the menu...")` on Option 2 exit.

### Fix Order
1. `src/task_tracker.py`
2. `src/reward_system.py`
3. `src/agent_runner.py`
4. `src/memory.py` & `src/llm_client.py`
5. `src/git_executor.py`
6. `src/bounty_scanner.py`
7. `src/installer.py`
8. `main.py`
9. Run test suites (`test_full_system.py` & tests)
10. Commit & Push to GitHub

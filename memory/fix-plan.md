# FIX PLAN — Penniless AI Agent

## Active: BUG-025 through BUG-028 Comprehensive Integrity & Error Elimination

### Scope (per RULES §5 step 3)
**What**:
1. BUG-025: Fix sort key crash on string/non-numeric `reward_usd` in `src/bounty_scanner.py`.
2. BUG-026: Submissions cleanup and prevention of false completion/reward records on LLM failure in `src/agent_runner.py`.
3. BUG-027: Clean PR URL extraction when PR already exists in `src/git_executor.py`.
4. BUG-028: Bounds check on `resp.choices` in `src/llm_client.py` for Gemini / non-streamed responses.

### Files to touch:
1. `src/bounty_scanner.py` [MODIFY]
2. `src/agent_runner.py` [MODIFY]
3. `src/git_executor.py` [MODIFY]
4. `src/llm_client.py` [MODIFY]
5. `test_full_system.py` [MODIFY]
6. `memory/fix-log.md` [MODIFY]

### Verification:
- Unit check safe float sorting in bounty scanner with string & None rewards.
- Unit check LLM error handling and submissions cleanup.
- Unit check PR URL extraction with "already exists".
- Run full 12-subsystem diagnostic suite live.


# FIX PLAN — Penniless AI Agent

## Active: BUG-029 through BUG-031 Zero-Payout Discard, Test Isolation & Counter Synchronization

### Scope (per RULES §5 step 3)
**What**:
1. BUG-029: Discard all bounties with `reward_usd <= 0`, `None`, or unbacked token in `bounty_scanner.py`, `agent_runner.py`, and `task_tracker.py`. Agent must NEVER touch $0 payout tasks.
2. BUG-030: Clean test pollution: remove 6 `test-diagnostic-slug` from `history.jsonl`, reset `bank_total_usd` to 0.0 in `soul.json`, clean test receipts from `bank_ledger.jsonl`, and make `test_full_system.py` run isolated/rollback tests.
3. BUG-031: Reconcile `tasks_completed` with clean `history.jsonl` count (25 real tasks) so header banner and box display identical true values.

### Files to touch:
1. `src/bounty_scanner.py` [MODIFY]
2. `src/agent_runner.py` [MODIFY]
3. `src/task_tracker.py` [MODIFY]
4. `test_full_system.py` [MODIFY]
5. `history.jsonl` [CLEAN]
6. `memory/soul.json` [CLEAN/RESET]
7. `memory/bank_ledger.jsonl` [CLEAN]
8. `memory/fix-log.md` [MODIFY]

### Verification:
- Run scanner check: verify 0-reward tasks are 100% excluded.
- Verify `history.jsonl` count matches `soul.json` tasks count exactly.
- Verify `Bank Stored` starts at $0.00 USDC matching real wallet balance.
- Run `test_full_system.py` and confirm it leaves `history.jsonl` and `soul.json` untouched!



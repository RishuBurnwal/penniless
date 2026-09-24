# BUGS — Penniless AI Agent
Status flow: NOTED → EVIDENCE-PENDING → CONFIRMED → PLANNED → IN-PROGRESS → FIXED-VERIFIED
Side exits: REJECTED (false positive, keep+reason) · UNCONFIRMED → needs-user.md · BLOCKED (§6)

---

### BUG-001 — NVIDIA deepseek-v4.1-flash returns empty content → agent hangs
- **Status**: FIXED-VERIFIED
- **Priority**: P0 — Critical (blocks option 2 entirely)
- **Category**: LLM API / Timeout
- **Found**: 2026-09-24, run_agent() hangs indefinitely at NVIDIA call
- **Where**: src/llm_client.py — `chat()` method, NVIDIA provider
- **Evidence (E1 Runtime)**: Fixed with `stream=True` and token accumulation + on_chunk callback. Tokens stream cleanly in ~6.9s. Verified in commit `7466161` & `a6cc353`.

---

### BUG-002 — Autonomous daemon does not auto-jump to next task after completion
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High
- **Category**: Logic / Flow
- **Found**: 2026-09-24, option 2 stops after first task
- **Where**: src/agent_runner.py — `run_autonomous_daemon()`
- **Evidence (E1 Runtime)**: Auto-jump implemented with 5s delay on success, tested live in Cycle 1 -> Cycle 2 transition.

---

### BUG-003 — No memory/soul system — agent starts fresh every session
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High
- **Category**: Missing Feature
- **Found**: 2026-09-24
- **Where**: src/memory.py, src/reward_system.py
- **Evidence (E1 Runtime)**: Memory and reward system active, verified with test_full_system.py (100% green).

---

### BUG-004 — No auto wallet transfer after earning
- **Status**: REJECTED (Design Clarification)
- **Priority**: P2
- **Category**: Missing Feature / Wallet
- **Found**: 2026-09-24
- **Note**: Superteam & GitHub bounties pay directly to the user's on-chain wallet. No outbound transfer is needed or safe; agent monitors balance increases via `wallet_monitor.py` and awards rewards automatically.

---

### BUG-011 — Double Counting in TaskTracker.count_submitted()
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Medium
- **Category**: Logic / Flow
- **Found**: 2026-09-24
- **Where**: src/task_tracker.py:78-83, 96-97
- **Evidence (E3 Static)**: In `record_completed_task()`, both `norm` and `slug` are added to `self.seen_urls`. But `_load_cache()` only adds URLs. Calling `count_submitted()` returns `len(self.seen_urls)`, causing completed tasks with slugs to be double-counted during active runtime.
- **Root cause**: Single set `seen_urls` overloaded for URL deduplication, slug deduplication, and count tracking.
- **Fix**: Maintain distinct `seen_slugs` set and explicit `_submitted_count` loaded from valid lines in `history.jsonl`.

---

### BUG-012 — False Earning Detection on Daemon Startup
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High
- **Category**: Logic / Flow
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:603, 628-636; src/reward_system.py:140-148
- **Evidence (E3 Static)**: `prev_balance` initialized to `0.0`. If user wallet already contains USDC (e.g. $50), cycle 1 computes `delta = 50.0 - 0.0 = 50.0`, falsely triggering `on_earning_detected()`, XP gain, and badges for pre-existing funds.
- **Fix**: Initialize `prev_balance = None`. On first balance fetch, set `prev_balance = current_balance` without triggering `on_wallet_checked`. Also guard against `prev_balance is None` in `on_wallet_checked()`.

---

### BUG-013 — GitHub Code Tasks Fail Deduplication in Task Tracker
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High
- **Category**: Logic / Flow
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:260-266, 321-329, 426
- **Evidence (E3 Static)**: `_execute_code_task` does not accept `opportunity` dict and records `target_repo` (e.g. `owner/repo`) as `url` in tracker. But `filter_unattempted()` checks against `o.get('url')` (`https://github.com/owner/repo/issues/123`). Thus, completed GitHub code tasks are never filtered out and get re-proposed.
- **Fix**: Pass `opportunity` dict to `_execute_code_task`, track `opportunity.get('url')`.

---

### BUG-014 — Deprecated datetime.utcnow() in memory.py and llm_client.py
- **Status**: FIXED-VERIFIED
- **Priority**: P3 — Code Health
- **Category**: Deprecation / Warning
- **Where**: src/memory.py:44, 45, 76, 112; src/llm_client.py:57
- **Evidence (E3 Static)**: `datetime.utcnow()` is deprecated in Python 3.12+ (PEP 615).
- **Fix**: Replace with `datetime.now(timezone.utc).isoformat()`.

---

### BUG-015 — Badge Name vs Level Name Mismatch in reward_system.py
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Consistency
- **Category**: Logic / Data
- **Where**: src/reward_system.py:59-61
- **Evidence (E3 Static)**: Level 2 badge named `[LEVEL] Earner` (but Level 2 in `memory.py` is `First Steps`). Level 3 badge named `[LEVEL] Grinder` (Level 3 is `Earner`). Level 4 badge missing.
- **Fix**: Synchronize level badge IDs and names with `_LEVEL_NAMES` in `src/memory.py`.

---

### BUG-016 — Dead and Malformed Code in git_executor.py
- **Status**: FIXED-VERIFIED
- **Priority**: P3 — Code Health
- **Category**: Dead Code
- **Where**: src/git_executor.py:86
- **Evidence (E3 Static)**: `cmd = ["gh", "repo", "fork", repo_slug, "--clone=true", f"--{repo_dir}"]` defined and immediately overwritten on line 87.
- **Fix**: Remove line 86.

---

### BUG-017 — Potential TypeError & AttributeError on Null API Values in bounty_scanner.py
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Robustness
- **Category**: Runtime Safety
- **Where**: src/bounty_scanner.py:130, 137, 178-182, 186
- **Evidence (E3 Static)**: `float(i.get("funded_amount", 0))` raises `TypeError` when API key returns `None` for amount. `b.get("issue", {}).get(...)` raises `AttributeError` when `"issue": null` is in JSON.
- **Fix**: Use `(b.get("issue") or {}).get(...)` and `float(i.get("funded_amount") or 0)`.

---

### BUG-018 — Outdated Model and Comments in installer.py
- **Status**: FIXED-VERIFIED
- **Priority**: P3 — Configuration
- **Category**: Consistency
- **Where**: src/installer.py:88, 319
- **Evidence (E3 Static)**: `_step_test_llm()` tests `"openai/gpt-oss-20b"` on Groq instead of `"qwen/qwen3.8-27b"`.
- **Fix**: Update Groq test model to `"qwen/qwen3.8-27b"` and correct LLM fallback comment.

---

### BUG-019 — Screen Clears Immediately on Daemon Exit Hiding Summary
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — UX
- **Category**: Interactive Flow
- **Where**: main.py:163
- **Evidence (E3 Static)**: When Option 2 exits on Ctrl+C, `_option_2_autonomous_loop()` returns to `main()` loop which immediately calls `console.clear()` in `_show_menu()`. User cannot see final stats.
- **Fix**: Add `input("  Press Enter to return to the menu...")` before returning.

---

### BUG-020 — Tasks Completed in Option 3 & Option 4 Never Award XP, Badges, or Vitality
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High
- **Category**: Logic / Flow
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:418, 266, 679
- **Evidence (E3 Static)**: `rewards.on_task_completed()` was only called in `run_autonomous_daemon()`. When a user runs Option 3 (Single Cycle) or Option 4 (Interactive Gate), completing a task never triggered `on_task_completed()`, so XP remained 0, badges remained locked, and survival vitality was not replenished.
- **Root cause**: Callback placed in daemon wrapper instead of inside task execution functions.
- **Fix**: Move `rewards.on_task_completed(task_title, task_type)` directly into `_execute_content_task()` and `_execute_code_task()` with real bounty title.

---

### BUG-021 — Interactive Approval Gate SKIP Causes Infinite Loop on Same Task
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Medium
- **Category**: Logic / Flow
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:589-591, src/task_tracker.py
- **Evidence (E3 Static)**: Typing `SKIP` in interactive mode simply calls `run_agent(autonomous=False)` recursively without recording the skipped task. The scanner re-scans, finds the same task, and LLM re-proposes the exact same task indefinitely.
- **Fix**: Add `tracker.record_skipped_task(url)` and call it when user chooses `SKIP`.

---

### BUG-022 — Concurrent Audio Chimes Interrupt and Race on Windows Speaker
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Audio / Reliability
- **Category**: Concurrency
- **Found**: 2026-09-24
- **Where**: src/sound_alert.py:25-72
- **Evidence (E3 Static)**: When earning arrives, `on_earning_detected()` calls `play_beep('earn')` and `bank.execute_bank_deposit()` immediately calls `play_beep('transaction')`. Two simultaneous threads call `winsound.Beep()`, causing race conditions and dropped chimes.
- **Fix**: Protect `_play_tones_sync()` with a `threading.Lock()` to ensure sequential, melodious chime playback.

---

### BUG-023 — Survival Engine Missing "DEAD" State and Emergency Resuscitation
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Game Loop
- **Category**: Logic / State
- **Found**: 2026-09-24
- **Where**: src/survival.py:61-70, 134-158
- **Evidence (E3 Static)**: When vitality drops to 0.0%, `state` still returns `"CRITICAL"` and never reaches `"DEAD"`. No distinct life support / resuscitation prompt was given.
- **Fix**: Define `"DEAD"` state when `vitality <= 0.0`, provide emergency life support directive, and render `💀 Life: 0.0% (DEAD)` in meter.

---

### BUG-024 — Unhandled KeyboardInterrupt Traceback in Main Menu
- **Status**: FIXED-VERIFIED
- **Priority**: P3 — UX
- **Category**: CLI / Exception Handling
- **Found**: 2026-09-24
- **Where**: main.py:112, 203-214
- **Evidence (E3 Static)**: Pressing Ctrl+C at `choice = input("  > ")` causes Python to crash with a traceback rather than cleanly exiting.
- **Fix**: Catch `KeyboardInterrupt` in `_show_menu()` / `main()` and exit cleanly.

---

### BUG-025 — Unary minus on string reward crashes sort in bounty scanner
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — High / Crash Prevention
- **Category**: Type Safety / Sorting
- **Found**: 2026-09-24
- **Where**: src/bounty_scanner.py:85, 100, 304
- **Evidence (E3 Static)**: `-(x.get("reward_usd") or 0)` raises `TypeError: bad operand type for unary -: 'str'` if any API returns `rewardAmount` or `reward_usd` as a string (e.g. `"$500"`, `"100"`).
- **Fix**: Centralize a `_safe_float()` helper that strips currency symbols, commas, and safely casts to float before negating.

---

### BUG-026 — Submissions Directory Cleanup and False Task Completion on LLM Failure
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — Integrity / Logic Flow
- **Category**: Flow Control / File Management
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:364-437
- **Evidence (E3 Static)**: `sub_file` is created before LLM call. If LLM call fails, times out, or returns empty/error, `sub_file` remains on disk, the ledger marks it "Ready", tracker marks it completed, and XP/vitality boost is awarded for failed work.
- **Fix**: Check `response` validity. On failure/error, delete `sub_file`, do not log to ledger/tracker, do not grant rewards/vitality, and return `False`.

---

### BUG-027 — GitExecutor PR creation returns multiline raw CLI error when PR already exists
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Data Integrity
- **Category**: String Parsing
- **Found**: 2026-09-24
- **Where**: src/git_executor.py:187-195
- **Evidence (E3 Static)**: When `gh pr create` fails with "already exists", the function returns the entire multiline `output` string instead of extracting the existing PR URL from the message, corrupting ledger formatting.
- **Fix**: Extract and return the clean URL with regex, falling back to a clean status string.

---

### BUG-028 — LLM Client missing index bounds check on `resp.choices` in Gemini/non-streaming fallback
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — Robustness
- **Category**: Exception Handling
- **Found**: 2026-09-24
- **Where**: src/llm_client.py:266
- **Evidence (E3 Static)**: If a provider response has an empty `choices` list (e.g., content safety filtered or empty candidate), `resp.choices[0]` raises an unhandled `IndexError`.
- **Fix**: Check `if not resp.choices` before accessing `resp.choices[0]` and raise a descriptive `ValueError`.

---

### BUG-029 — Zero-Payout, Null, or Non-USDC/SOL/USD Bounties Touched by Agent
- **Status**: FIXED-VERIFIED
- **Priority**: P0 — Critical Earning Rule
- **Category**: Earning Integrity / Filtering
- **Found**: 2026-09-24
- **Where**: src/bounty_scanner.py, src/agent_runner.py, src/task_tracker.py
- **Evidence (E1 Runtime)**: Agent processed Superteam listings with `reward_usd == 0.0` (e.g. `kriptok-league-trading-content-partner`) and GitHub issues with `reward_usd == None` or non-convertible tokens like RTC (RustChain), leading to rejected prompts or wasted agent cycles on $0 tasks.
- **Root cause**: `filter_unattempted()` only checked if a task URL was seen before, not whether it paid money. `scan_github_bounties()` returned issues with `reward_usd: None`, and `scan_superteam()` did not filter out $0 listings.
- **Fix**: Enforce a strict positive payout filter `_safe_float(reward_usd) > 0` and acceptable currencies (`USDC`, `SOL`, `USD`, `USDT`) across `scan_all()`, `filter_unattempted()`, and `_propose_task()`. Discard any $0, null, or unverified token opportunities immediately.

---

### BUG-030 — Diagnostic Test Suite Contaminating Production Soul, History, & Treasury
- **Status**: FIXED-VERIFIED
- **Priority**: P1 — Data Integrity
- **Category**: Testing / State Leakage
- **Found**: 2026-09-24
- **Where**: test_full_system.py, memory/soul.json, history.jsonl, memory/bank_ledger.jsonl
- **Evidence (E1 Runtime)**: Running `test_full_system.py` called `bank.execute_bank_deposit(1.0)` and `tracker.record_completed_task('test-diagnostic-slug', ...)` directly against production files, adding 6 dummy records to `history.jsonl` and creating a false "$4.00 USDC" Bank Stored balance in `soul.json` when actual wallet balance was $0.
- **Fix**: Clean all test records from `history.jsonl`, reset `bank_total_usd` to 0.0 in `soul.json`, clean test deposits from `bank_ledger.jsonl`, and isolate `test_full_system.py` so tests restore state and never pollute production files.

---

### BUG-031 — Discrepancy Between Header "Completed" and Box "Tasks Done"
- **Status**: FIXED-VERIFIED
- **Priority**: P2 — UI Consistency
- **Category**: Accounting / Display
- **Found**: 2026-09-24
- **Where**: src/agent_runner.py:521, 661
- **Evidence (E1 Runtime)**: Top cycle banner showed `Completed: 24` (read from `memory.soul['tasks_completed']`), while the UI panel showed `Tasks Done: 30` (read from `tracker.count_submitted()`, which counted dummy test lines).
- **Fix**: Synchronize `tasks_completed` with clean `tracker.count_submitted()`, and eliminate test pollution.



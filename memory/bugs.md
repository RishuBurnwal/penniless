# BUGS — Penniless AI Agent
Status flow: NOTED → EVIDENCE-PENDING → CONFIRMED → PLANNED → IN-PROGRESS → FIXED-VERIFIED
Side exits: REJECTED (false positive, keep+reason) · UNCONFIRMED → needs-user.md · BLOCKED (§6)

---

### BUG-001 — NVIDIA deepseek-v4.1-flash returns empty content → agent hangs
- **Status**: CONFIRMED → IN-PROGRESS
- **Priority**: P0 — Critical (blocks option 2 entirely)
- **Category**: LLM API / Timeout
- **Found**: 2026-09-24, run_agent() hangs indefinitely at NVIDIA call
- **Where**: src/llm_client.py — `chat()` method, NVIDIA provider
- **Evidence (E1 Runtime)**: Ran `run_agent(autonomous=True)` — process stuck at `-> [NVIDIA] deepseek-ai/deepseek-v4.1-flash` for 90+ seconds with no output
- **Evidence (E3 Static)**: NVIDIA deepseek-v4.1-flash uses internal thinking tokens. The `content` field in response is empty when max_tokens is insufficient for thinking + response. SDK `timeout` parameter only sets connect timeout, not read/response timeout.
- **Root cause**: Two sub-issues:
  1. openai SDK `timeout=N` does not enforce wall-clock read timeout for streaming/thinking models
  2. deepseek-v4.1-flash returns empty `choices[0].message.content` — thinking tokens go to a separate field or require streaming
- **Attempts**:
  1. Set `timeout=35` on openai.OpenAI() → FAILED (only connect timeout)
  2. Added `concurrent.futures.ThreadPoolExecutor` with `future.result(timeout=40)` → PARTIALLY FIXED (fallback to Groq works, but NVIDIA itself still returns empty)
  3. Next: Use streaming mode (`stream=True`) to collect tokens as they arrive
- **Verification needed**: `stream=True` call to NVIDIA with content accumulated from chunks
- **ELI10**: Socho NVIDIA ek slow writer hai jo pehle draft likhta hai (thinking) phir clean copy deta hai — lekin hum sirf clean copy maang rahe the aur usne khaali page de diya. Streaming mode me hum draft bhi padh sakte hain.

---

### BUG-002 — Autonomous daemon does not auto-jump to next task after completion
- **Status**: CONFIRMED → PLANNED
- **Priority**: P1 — High
- **Category**: Logic / Flow
- **Found**: 2026-09-24, option 2 stops after first task or waits 120s unnecessarily
- **Where**: src/agent_runner.py — `run_autonomous_daemon()`
- **Evidence (E3)**: `run_autonomous_daemon` calls `run_agent()` and if it returns False (no work done), waits 90s. But if all tasks are already in tracker, it also returns False even though new work could be found after re-scanning.
- **Root cause**: Task tracker `filter_unattempted()` too aggressive — filters all tasks if they were attempted even if submission failed. Also daemon has no exponential backoff, just flat 90s wait.
- **Verification needed**: Check tracker logic + daemon loop logic after BUG-001 is fixed

---

### BUG-003 — No memory/soul system — agent starts fresh every session
- **Status**: CONFIRMED → PLANNED  
- **Priority**: P1 — High
- **Category**: Missing Feature
- **Found**: 2026-09-24
- **Where**: Entire src/ — no persistence of agent state, no reward system, no self-improvement
- **Evidence (E3)**: No `memory.py`, no `soul.json`, no reward tracking files exist
- **Root cause**: Not implemented yet
- **Planned**: Implement src/memory.py + src/reward_system.py

---

### BUG-004 — No auto wallet transfer after earning
- **Status**: EVIDENCE-PENDING
- **Priority**: P2
- **Category**: Missing Feature / Wallet
- **Found**: 2026-09-24
- **Where**: src/wallet_monitor.py
- **Note**: For Superteam bounties, platform pays directly to registered wallet — no "transfer" step needed for content bounties. For code bounties (PRs accepted), maintainer pays to wallet. "Auto transfer" may mean: auto-detect incoming balance + celebrate/log it. Need to clarify if user means something else.
- **Evidence-Pending**: Need to verify actual payout mechanism for accepted bounties

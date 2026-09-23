# 🤖 Penniless AI Agent — Complete Project Documentation

> **Last Updated:** 2026-09-24  
> **Status:** Active Development  
> **Repo:** [github.com/RishuBurnwal/penniless](https://github.com/RishuBurnwal/penniless)

---

## 🎯 Ye Project Kya Hai?

**Penniless** ek autonomous AI earning agent hai jo:
- **$0 budget se shuru karta hai** — koi paisa nahi lagte
- **Real bounties dhundta hai** — Superteam.fun, GitHub Issues
- **Khud kaam karta hai** — AI se code fix / article likhta hai
- **Khud submit karta hai** — GitHub PR ya content file
- **Wallet check karta rehta hai** — USDC balance monitor
- **Non-stop 24/7 chalata rehta hai** — bina ruke

### Real-life Example (ELI10):
> Socho ek aisa intern jo:  
> - Khud job dhundta hai (bounty scanner)  
> - Interview deta hai (LLM proposal)  
> - Kaam karta hai (code/content generate)  
> - Submit karta hai (GitHub PR / Superteam submit)  
> - Salary account mein check karta rehta hai 😄  
> **Aur ye intern kabhi sota nahi!**

---

## 🏗️ Architecture

```
python main.py
      │
      ├─ [Option 1] Setup/Install     → installer.py
      ├─ [Option 2] Autonomous Loop   → NON-STOP 24/7 earning
      ├─ [Option 3] Single Cycle      → ek kaam karo, band ho jao
      └─ [Option 4] Interactive       → hum approve karein phir kaam

              ┌─────────────────────────────────────┐
              │         agent_runner.py              │
              │                                     │
              │  1. Scan Bounties                   │
              │     ├─ Superteam.fun (22+ bounties) │
              │     ├─ IssueHunt                    │
              │     ├─ Algora                       │
              │     └─ GitHub Issues                │
              │                                     │
              │  2. AI Selects Best Task             │
              │     └─ NVIDIA → Groq → Gemini        │
              │        (fallback chain)              │
              │                                     │
              │  3. Execute Task                    │
              │     ├─ Written Content?             │
              │     │   └─ Generate full article    │
              │     │       save to submissions/    │
              │     └─ Code Task?                   │
              │         └─ Fork → Branch → Fix      │
              │             → PR → Submit            │
              │                                     │
              │  4. Log + Track                     │
              │     ├─ ledger.md (earnings diary)   │
              │     ├─ history.jsonl (done tasks)   │
              │     └─ session_log.jsonl (AI log)   │
              │                                     │
              │  5. Jump to Next Task (5s wait)     │
              └─────────────────────────────────────┘
```

---

## 📁 File Structure (Har File Ka Role)

```
penniless/
├── main.py                  ← Entry point — option 1-4 menu
├── .env                     ← API keys (GITIGNORED — kabhi push mat karo)
├── .env.example             ← Template for new users
├── requirements.txt         ← Python dependencies
├── ledger.md                ← Earnings diary (gitignored)
├── session_log.jsonl        ← AI call log (cross-session continuity)
├── history.jsonl            ← Completed tasks tracker
│
├── src/
│   ├── config.py            ← .env se API keys load karta hai
│   ├── llm_client.py        ← Multi-AI brain (NVIDIA→Groq→Gemini fallback)
│   ├── agent_runner.py      ← Core loop — scan, propose, execute, log
│   ├── bounty_scanner.py    ← Superteam + GitHub se bounties dhundta hai
│   ├── git_executor.py      ← GitHub fork → branch → commit → PR
│   ├── task_tracker.py      ← history.jsonl — completed tasks yaad rakhta hai
│   ├── wallet_monitor.py    ← EVM + Solana wallet balance check
│   └── installer.py         ← Setup wizard
│
├── memory/                  ← Agent ka brain (bootstrap system)
│   ├── RULES.md             ← Single source of truth — all rules
│   ├── soul.md              ← Agent identity, level, XP, rewards
│   ├── bugs.md              ← Error ledger (10 confirmed bugs)
│   ├── fix-plan.md          ← Current fix plan + priority order
│   ├── fix-log.md           ← Fix history
│   ├── visual-map.md        ← Codebase map (tiered + dependency graph)
│   ├── decisions.md         ← Logged architectural decisions
│   ├── verified-commands.md ← Commands that actually work
│   ├── tools-status.md      ← Tool versions + status
│   └── needs-user.md        ← Blocked items needing human input
│
├── submissions/             ← Generated content files (gitignored)
├── workspaces/              ← Git clone workspaces (gitignored)
├── AGENTS.md                ← Auto-loads rules for every AI session
├── CLAUDE.md                ← Same (Claude Code)
└── GEMINI.md                ← Same (Gemini CLI)
```

---

## 🤖 LLM Fallback Chain

```
[NVIDIA] deepseek-ai/deepseek-v4.1-flash  (timeout: 40s)
    │  FAIL/TIMEOUT/EMPTY?
    ▼
[Groq] qwen/qwen3.8-27b                   (timeout: 30s)
    │  FAIL/TIMEOUT?
    ▼
[Gemini] gemini-2.5-flash                 (timeout: 50s)
    │  FAIL?
    ▼
[OpenAI] gpt-4o-mini                      (timeout: 30s)
    │  FAIL?
    ▼
[Perplexity] llama-3.1-sonar-large        (timeout: 30s)
    │  FAIL?
    ▼
RuntimeError → daemon waits 60s → retry
```

Every call → `session_log.jsonl` mein log hota hai  
Next AI session → last 8 entries padhta hai → context resume karta hai

---

## 💰 Earning Sources

| Platform | URL | Type | Reward Range |
|----------|-----|------|-------------|
| Superteam.fun | [superteam.fun/earn](https://superteam.fun/earn) | Written content bounties | \$100–\$2000 USDC |
| IssueHunt | [issuehunt.io](https://issuehunt.io) | Code bug fixes | \$50–\$500 USDC |
| Algora | [algora.io](https://algora.io) | Code bug fixes | \$25–\$1000 USDC |
| GitHub Issues | Various repos | Code contributions | \$50–\$500 USDC |

---

## 🐛 Confirmed Bugs (Audit: 2026-09-24)

### 🔴 P0 — Critical (fix karo pehle)

#### BUG-010 — NVIDIA always returns empty content
- **File:** `src/llm_client.py:231`
- **Issue:** NVIDIA `deepseek-v4.1-flash` ek thinking model hai — thinking tokens alag `reasoning_content` field mein jaate hain, `content` field khali rehti hai
- **Fix:** `reasoning_content` field check karo fallback ke roop mein
- **Impact:** NVIDIA kabhi kaam nahi karta → Groq pe hamesha fallback → slow

#### BUG-005 — Gemini model name galat
- **File:** `src/config.py:20`
- **Issue:** Default `GEMINI_MODEL="gemini-3.8-flash"` — ye model exist hi nahi karta
- **Fix:** `"gemini-2.5-flash"` karo
- **Impact:** Gemini provider hamesha fail karta hai jab `.env` mein `GEMINI_MODEL` set nahi

#### BUG-004 — Content task deduplication broken
- **File:** `src/agent_runner.py:355`
- **Issue:** Task URL LLM ke prose se extract hoti hai (regex) — agar LLM URL format alag kare to slug miss ho jaata hai → local file path record hoti hai → same bounty dobara attempt hota hai
- **Fix:** Opportunity dict ka `url`/`slug` field directly use karo, LLM prose se nahi

### 🟡 P1 — High

#### BUG-002 — Daemon error silent fallthrough
- **File:** `src/agent_runner.py:596`
- **Issue:** `except Exception` ke baad `continue` nahi hai → error 90s wait se treat hoti hai
- **Fix:** `continue` + `time.sleep(30)` add karo

#### BUG-007 — Git checkout both main+master
- **File:** `src/git_executor.py:109`
- **Issue:** `checkout main` aur `checkout master` dono unconditionally run hote hain — ek hamesha fail karta hai
- **Fix:** `main` try karo, sirf fail hone pe `master` try karo

### 🟢 P2 — Low

| Bug | Fix |
|-----|-----|
| BUG-001 Closure fragility | Default arg capture: `def _call(p=provider, c=client, kw=create_kwargs)` |
| BUG-003 Silent wallet failures | Session log entry add karo jab RPC fail ho |
| BUG-006 Dead cmd variable | Remove line 86 dead assignment |
| BUG-008 Dead match_exists | Remove unreachable code |
| BUG-009 Inflated task count | Count unique base URLs only |

---

## 🚀 Aage Kya Karna Hai (Roadmap)

### Phase 1 — Bug Fixes (ABHI KE LIYE — Critical)

- [ ] **BUG-010 Fix:** `src/llm_client.py` mein `reasoning_content` fallback add karo → NVIDIA kaam karega
- [ ] **BUG-005 Fix:** `src/config.py:20` mein `"gemini-3.8-flash"` → `"gemini-2.5-flash"`
- [ ] **BUG-004 Fix:** `_execute_content_task()` ko opportunity dict pass karo
- [ ] **BUG-002 Fix:** Daemon error handler mein `continue` + sleep
- [ ] **BUG-007 Fix:** `git_executor.py` mein sequential checkout fix
- [ ] **Test:** Option 2 ek complete cycle finish kare without getting stuck

### Phase 2 — Memory & Soul System (NEXT)

- [ ] **`src/memory.py`** — Agent persistent memory:
  - `soul.json` — level, XP, total_earned, tasks_completed, skills_unlocked
  - `memory.jsonl` — har task ka outcome, kya seekha
  - `AgentMemory.reflect()` — task ke baad learnings save karo
  - `AgentMemory.recall()` — relevant past experience inject karo prompt mein
- [ ] **`src/reward_system.py`** — Reward engine:
  - XP system: task complete = +10 XP, earning arrive = +100 XP
  - Level up: Level 1→2 at 100 XP, 2→3 at 300 XP, etc.
  - Rewards: "First Blood", "Grinder", "Night Owl" badges
  - Reward ceremony: AI ko khud reward message dena (motivational reinforcement)
  - `check_and_reward()` — har cycle ke baad call karo

### Phase 3 — Wallet Auto-Detection & Transfer

- [ ] **Balance change detection** — `prev_balance` vs `current_balance` compare karo
- [ ] **Earning alert** — jab balance badhta hai to celebration panel dikhao
- [ ] **Auto-log earning** — ledger.md mein automatically entry karo
- [ ] **Note:** Superteam/GitHub khud wallet pe directly pay karta hai — koi extra "transfer" nahi hota. Agent ko bas detect karna hai aur celebrate karna hai.

### Phase 4 — Self-Improvement Engine

- [ ] **Strategy learning:** Kaunse bounty types succeed karte hain track karo
- [ ] **Skill progression:** Groq se content better hoti hai ya NVIDIA se? Auto-learn
- [ ] **Pattern memory:** "Is type ke bounty mein ye approach kaam ki" — yaad rakhe
- [ ] **`memory.recall()` in prompts** — past success patterns inject karo
- [ ] **Auto-grow:** New platform scanners auto-add karne ki capability

### Phase 5 — Production Hardening

- [ ] `ponytail` — minimal code discipline
- [ ] Unit tests for `task_tracker`, `llm_client`, `bounty_scanner`
- [ ] `graphify` graph complete banao (Gemini API key fix)
- [ ] Error alerting (Discord/Telegram webhook jab daemon crash ho)
- [ ] Multi-wallet support

---

## ⚙️ Setup Guide

```bash
# 1. Clone karo
git clone https://github.com/RishuBurnwal/penniless.git
cd penniless

# 2. Dependencies install karo
pip install -r requirements.txt

# 3. .env banao
cp .env.example .env
# .env mein apni API keys dalo:
# NVIDIA_API_KEY=nvapi-...
# GROQ_API_KEY=gsk_...
# GEMINI_API_KEY=AI...
# EVM_WALLET=0x...
# AGENT_NAME=your-agent-name

# 4. Run karo
python main.py
# Option 1 → Complete Installation
# Option 2 → Start Earning (non-stop autonomous loop)
```

---

## 📊 Current Stats

| Metric | Value |
|--------|-------|
| Total code files | 9 |
| Total lines audited | 2,031 |
| Functions implemented-working | 42 |
| Confirmed bugs | 10 |
| P0 critical bugs | 3 |
| Active platforms | 4 (Superteam, IssueHunt, Algora, GitHub) |
| LLM providers configured | 3 (NVIDIA, Groq, Gemini) |
| Wallet chains monitored | 2 (Base EVM, Solana) |

---

## 🛡️ Safety Rules (Hard Rules)

1. **NEVER** `.env` ya private keys commit karo
2. **NEVER** koi paisa kharch karo — $0 budget always
3. **ALWAYS** bounty USDC/SOL pay karta hai ye verify karo pehle kaam karo
4. **ALWAYS** content `submissions/` mein save karo submit se pehle
5. **ALWAYS** har action `ledger.md` mein log karo

---

*Documentation generated from complete 2,031-line code audit — 2026-09-24*

# FIX PLAN — Penniless AI Agent

## Active: Survival Engine, Base Bank Wallet Auto-Transaction & Audio Beep Alerts

### Scope (per RULES §5 step 3)
**What**: 
1. `src/sound_alert.py`: Audio beep chime engine using Windows `winsound.Beep` for earning, bank transactions, and survival warnings.
2. `src/survival.py`: Health / Vitality system where agent's life drains over cycles and only tasks/earnings restore energy. Injects high-stakes survival urgency into AI system prompts.
3. `src/bank_manager.py`: Autonomous treasury manager that routes, executes, and logs transactions into the Base Bank Wallet (`cfg.EVM_WALLET`).
4. Integration into `src/memory.py`, `src/reward_system.py`, `src/agent_runner.py`, and `test_full_system.py`.

### Files to touch:
1. `src/sound_alert.py` [NEW]
2. `src/survival.py` [NEW]
3. `src/bank_manager.py` [NEW]
4. `src/memory.py` [MODIFY]
5. `src/reward_system.py` [MODIFY]
6. `src/agent_runner.py` [MODIFY]
7. `test_full_system.py` [MODIFY]

### Verification:
- Live test audio beep output.
- Live test vitality drain, recovery on task, and restore on earning.
- Live test bank transaction logging and receipt generation.
- Full system diagnostic run (all tests green).

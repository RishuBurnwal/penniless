# VERIFIED COMMANDS — Penniless AI Agent
Only commands actually run and confirmed working.

| Purpose | Verified Command | Real Output (short) | Date | Platform |
|---------|-----------------|---------------------|------|----------|
| Check git status | `git status` | `On branch main, 2 modified` | 2026-09-24 | Windows/PowerShell |
| Install deps | `pip install -r requirements.txt` | All installed | 2026-09-24 | Windows |
| Run agent cycle | `python -c "from src.agent_runner import run_agent; run_agent(autonomous=True)"` | Scans 22 bounties, proposes task | 2026-09-24 | Windows |
| Test LLM chain | `python -c "from src.llm_client import llm; print(llm.chat([{'role':'user','content':'Say OK'}]))"` | `OK` via Groq in ~24s | 2026-09-24 | Windows |
| Check providers | `python -c "from src.llm_client import llm; print(llm.active_summary())"` | `NVIDIA(deepseek-v4.1-flash) → Groq(qwen3.8-27b) → Gemini(gemini-3.8-flash)` | 2026-09-24 | Windows |
| Git push | `git push origin main` | Branch up to date | 2026-09-24 | Windows |
| graphify pip package | `pip show graphifyy` | Name: graphifyy Version: 0.9.4 | 2026-09-24 | Windows |
| graphify CLI | BLOCKED by AppLocker policy | Cannot run graphify.exe | 2026-09-24 | Windows |

# FIX LOG — Penniless AI Agent

| Date | BUG-ID | What Changed | Files | Verification | Status |
|------|--------|--------------|-------|--------------|--------|
| 2026-09-24 | BUG-001 attempt 1 | Added openai timeout=35 | llm_client.py | FAILED — SDK timeout only connects | ATTEMPT-FAILED |
| 2026-09-24 | BUG-001 attempt 2 | Thread-based timeout + fallback to Groq | llm_client.py | PARTIALLY FIXED — fallback works, NVIDIA still empty | IN-PROGRESS |
| 2026-09-24 | Misc | Groq moved before Gemini in provider list | llm_client.py | Groq responds in 24s | FIXED-VERIFIED |
| 2026-09-24 | Misc | session_log.jsonl added | llm_client.py | Log entries verified in file | FIXED-VERIFIED |
| 2026-09-24 | Misc | main.py converted to option-based menu | main.py | Syntax check OK | FIXED-VERIFIED |

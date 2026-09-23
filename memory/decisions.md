# DECISIONS — Penniless AI Agent
Logged assumptions and architectural decisions.

| Date | Decision | Reason | Who |
|------|----------|--------|-----|
| 2026-09-24 | Use Groq before Gemini in fallback chain | Groq is ~2x faster for same quality output; Gemini has daily quota limits | agent |
| 2026-09-24 | Thread-based hard timeout for NVIDIA | SDK timeout= only sets connect timeout; NVIDIA thinking model can stall for 90s+ on read | agent |
| 2026-09-24 | session_log.jsonl for cross-AI context | When one AI session ends and another starts, the new AI reads last 8 log entries to avoid repeating failed approaches | agent |
| 2026-09-24 | Groq model: qwen/qwen3.8-27b | Best coding+reasoning model on Groq at time of selection; free tier available | agent |
| 2026-09-24 | Submissions saved to submissions/ | Content bounties cannot be auto-submitted via API — only code bounties have PR mechanism | agent |
| 2026-09-24 | history.jsonl removed from .gitignore | User wants task history pushed to GitHub for continuity across machines | user |

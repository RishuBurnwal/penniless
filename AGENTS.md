# Penniless AI Agent — Coding Agent Instructions

## Auto-loaded core rules (full detail: memory/RULES.md)
1. NOTE FIRST: any error/inconsistency found → append to memory/bugs.md before doing anything else about it.
2. NO CODE EDIT WITHOUT EVIDENCE: an error becomes actionable only when CONFIRMED per memory/RULES.md §4.
3. SCOPE WITH THE GRAPH: before editing, grep/read to find what's connected; write scope in memory/fix-plan.md.
4. FIX = NECESSARY CODE, NOT MINIMUM CODE: a bug fix contains everything the root cause needs.
5. VERIFY WITH REAL OUTPUT, then independently re-check once before calling it done.
6. 3 failed attempts on a bug → change approach; 2 more fails → skip, log in memory/needs-user.md.
7. Ask first only for: destructive changes, deleting code, product-level ambiguity, new paid deps.
8. Everything else: proceed and log the assumption in memory/decisions.md.

Full detail → memory/RULES.md

## Project: Penniless AI Agent
- **Purpose**: Autonomous AI agent that scans bounties (Superteam, GitHub), solves them (code/content), and submits for USDC earnings to wallet 0x4dB6d4B64af7F6c128D80505E08313C30061b037
- **Root**: C:\Users\rishu\Desktop\penniless
- **LLMs**: NVIDIA deepseek-v4.1-flash → Groq qwen3.8-27b → Gemini (fallback chain)
- **Entry**: main.py → option 2 = autonomous daemon
- **Key bug**: Option 2 hangs at NVIDIA API call (thinking model returns empty content)
- **Session log**: session_log.jsonl (cross-AI context continuity)

## Memory files
- memory/RULES.md — single source of truth
- memory/soul.md — agent identity + state
- memory/bugs.md — error ledger
- memory/fix-plan.md — current fix plan
- memory/fix-log.md — fix history
- memory/decisions.md — logged assumptions
- memory/needs-user.md — blocked items
- memory/verified-commands.md — verified CLI commands
- memory/visual-map.md — codebase map
- memory/tools-status.md — tool status

# TOOLS STATUS — Penniless AI Agent

## graphify
- **CLI version**: graphify 0.9.67 installed via `uv tool install "graphifyy[gemini]" --force`
- **Verified command**: `graphify --version` → `graphify 0.9.67` ✅
- **Skills updated**: `graphify install --platform claude` + `graphify install --platform agents` ✅
- **AST extraction**: ✅ 13 code files parsed
- **Semantic (docs)**: ❌ Gemini API key incompatible with graphify's openai-backend format
- **Graph output**: ❌ graphify crashes (exit -1073741819 = Windows tree-sitter access violation)
- **graphify-out/**: Only `cache/` created — no graph.json / graph.html
- **Workaround**: Manual tiered reading (more reliable for this 13-file codebase)
- **Hooks**: NOT installed (crash risk)
- **Date**: 2026-09-24

## ponytail
- **Present before bootstrap**: NOT CHECKED (Claude Code plugin system)
- **Status**: N/A — running in Antigravity agent, not Claude Code
- **Date**: 2026-09-24

## node
- **Present**: YES
- **Verified command**: `node --version` → `v24.12.0`
- **Date**: 2026-09-24

## uv
- **Present**: YES
- **Verified command**: `uv --version` → `uv 0.11.17`
- **Date**: 2026-09-24

## pipx
- **Status**: BLOCKED — AppLocker policy
- **Date**: 2026-09-24

## Python
- **Present**: YES
- **Version**: 3.x (confirmed by pip working)
- **Date**: 2026-09-24

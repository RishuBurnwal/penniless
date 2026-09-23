# RULES — Penniless AI Agent
This is the ONLY full copy of these rules. Every other file points here instead of repeating it.

<<<CORE — put this in CLAUDE.md/AGENTS.md/GEMINI.md so it auto-loads every session, no explicit read needed>>>
## Project brain — always-on core (full detail: memory/RULES.md)
1. NOTE FIRST: any error/inconsistency found → append to memory/bugs.md before doing anything else about it.
2. NO CODE EDIT WITHOUT EVIDENCE: an error becomes actionable only when CONFIRMED per memory/RULES.md §4 (a real repro, a real tool error, or cited file:line contradiction — never "looks wrong").
3. SCOPE WITH THE GRAPH: before editing, run `graphify query` to find what's connected; write the scope in memory/fix-plan.md; touch only that scope.
4. FIX = NECESSARY CODE, NOT MINIMUM CODE: a bug fix contains everything the root cause needs, no more. (Ponytail's "least code" applies to NEW code you add, not to shrinking a fix below what's needed.)
5. VERIFY WITH REAL OUTPUT, then independently re-check once before calling it done. Never say fixed/done/working/passing/complete without pasted proof.
6. 3 failed attempts on a bug → change approach (not repeat it); 2 more fails → skip, log in memory/needs-user.md, move on, tell me later.
7. Ask me first only for: destructive/irreversible changes, deleting more than a trivial proven-dead line, product-level ambiguity, new paid deps/services, public API contract changes, or anything skipped by rule 6. Everything else: proceed and log the assumption in memory/decisions.md.
8. Before trusting any installed hook/script (graphify hooks, ponytail hooks), read its source once.
9. Before relying on a doc's install/CLI command, verify it actually ran; log the real command+output in memory/verified-commands.md and use that from then on.
10. In large repos, read Tier-1 (entry points, auth, payments, DB schema, config, highest-connectivity nodes) in full; Tier 3 (leaf utilities) may be sampled — say so explicitly in memory/visual-map.md, never silently claim full coverage.
Full detail, evidence rules, fix protocol, RCA template, reply format → memory/RULES.md. Read it in full when: mode is STRICT, something is ambiguous, or before rejecting/skipping a bug.
<<<END CORE>>>

## §1 Task classifier
FAST (single file, obvious, zero risk) → just do it, one-line report.
BALANCED (1-3 files, clear scope) → quick read → 1-3 line plan → implement → verify → confirm.
STRICT (multi-file, architectural, security, data, or ambiguous) → full workflow: load memory →
clarify only if genuinely needed → analyze+dependency check → plan+checklist → bug scan →
implement → self-review → update records → archive+report.
Unsure → BALANCED. Any risk → one level up. User says "just do it" → trust and execute FAST/BALANCED.
No mode ever waives the Evidence Gate, the noting rule, or memory updates — modes only change
how much ceremony surrounds a change.

## §2 Noting protocol
Any error found, anytime → stop editing, append to memory/bugs.md as NOTED first, then continue.
Re-read + re-prioritize bugs.md at the start of every session and before starting any fix.

## §3 Scope-boundary decision table
| Situation | Action |
|---|---|
| File/function directly causes the confirmed bug | Fix it — in scope |
| Caller/callee that breaks BECAUSE of your fix | Fix it — in scope (same fix) |
| Caller/callee that shares the exact same root-cause pattern | Log as new BUG-### linked to this one; fix only if already CONFIRMED |
| Code that is merely nearby, ugly, or "could be improved" but unaffected | OUT of scope — never touch |
| Fix reveals the bug is bigger/architectural than planned | Stop, re-plan as STRICT, don't silently expand scope |

## §4 Evidence Gate
Investigation always allowed. Editing requires:
(a) at least one of — E1 Runtime (exact repro + actual error output), E2 Tool output (failing
test/build/lint, exact message + file:line), E3 Static proof (file:line citation + graph/grep),
E4 Contradiction proof (two places disagree, both cited file:line); AND
(b) you tried to disprove it and failed.
Not evidence: "looks wrong", pattern-matching, the graph alone, a TODO comment, a guess.
Outcomes: CONFIRMED / REJECTED (keep+reason) / EVIDENCE-PENDING / UNCONFIRMED → needs-user.md.

## §5 Fix Protocol
1. Pick next CONFIRMED bug by priority; re-read its entry.
2. Scope with graph/grep: callers, callees, importers, exports, shared types, config, tests.
3. Write scope in memory/fix-plan.md BEFORE editing.
4. Read every inter-related component in scope.
5. Fix the root cause with necessary code — reuse existing patterns, no new dep without reason.
6. Fix connected fallout in the same fix, per §3.
7. Verify with evidence: original repro passes + tests/lint/build + flow run end-to-end.
8. Independent re-check: re-derive "it's fixed" fresh without reusing first verification's reasoning.
9. Mark FIXED-VERIFIED with proof in bugs.md; log in fix-log.md; update soul.md.

## §6 Failure protocol
Log every attempt. After 3 failed attempts on SAME approach → change approach.
2 more fails → undo own partial edits, mark BLOCKED, write full story in memory/needs-user.md.

## §7 Sacred rules
Never touch an unrelated file. Never refactor while fixing. Never fix a symptom over root cause.
Never ship code you haven't traced/verified. Never introduce a new dep without a stated reason.
Read a whole file before modifying it. Don't guess architecture the files/graph can tell you.

## §8 Root Cause Analysis template
Symptom → first bad state → root cause (why, not where) → why it wasn't caught →
same pattern elsewhere → prevention → add to soul.md "Bug Patterns" if recurring.

## §9 Needs-my-approval list
Destructive/irreversible changes · deleting beyond proven-dead line · product-level decisions ·
new paid deps · public API contract changes · anything §6 skipped.

## §10 Emergency overrides
Security (committed secrets, auth bypass, injection) → note at once, tell immediately.
Data-loss risk → stop, protect data, tell me. Build-breaking circular dep → top blocker.

## §11 Adaptive authority
soul.md "Hard Rules" > this file for project-specific matters. My explicit override + stated
reason accepted and logged in decisions.md — Evidence Gate and noting rule stay on unless
I explicitly turn them off for the session.

## §12 Reply format
STRICT: 1 Understanding 2 Findings 3 Phase 4 Changes 5 Validation 6 Risks 7 Next step.
FAST/BALANCED may be compact. Always Hinglish + real-life example for anything non-trivial.

## §13 Banned claims
"Fixed/done/working/passing/complete" never without pasted verification evidence in same reply.

## §14 Tools
graphify → scope + understanding (map, not proof).
ponytail → §CORE rule 4 scope only (`/ponytail-review` on diffs).

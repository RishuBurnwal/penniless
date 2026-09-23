# NEEDS USER — Penniless AI Agent
Items that require human decision before proceeding.

### ITEM-001 — Auto wallet transfer clarification
- **Date**: 2026-09-24
- **Question**: "ye khud hi earning ko wallet me transfer karae" — kya iska matlab hai:
  (A) Agent detect kare ki wallet mein earning aayi → celebrate + log (Superteam/GitHub already pays to registered wallet directly)
  (B) Agent khud on-chain USDC transfer kare private key use karke (DANGEROUS — requires private key in .env)
- **Default assumed**: Option A (detect + celebrate) — safer, no private key needed
- **Status**: Proceeding with Option A, will ask if user wants Option B

### ITEM-002 — graphify CLI blocked
- **Date**: 2026-09-24
- **Issue**: AppLocker policy blocks graphify.exe. Using manual code reading instead.
- **Impact**: No auto-generated graph.html — dependency mapping done manually
- **Status**: Noted, proceeding without graphify CLI

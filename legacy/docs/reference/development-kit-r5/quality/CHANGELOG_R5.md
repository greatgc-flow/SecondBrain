# R5 changes and scope

Date: 2026-10-10 | Baseline: `Development_Kits_VerySimple_LoopAudit_20261010_FINAL.zip` (exact original retained separately before modifications).

**Preserved:** original 100 generic / 188 Brain requirements, 14 generic schemas + 22 Second Brain schemas, 46 cross-scenarios, all legacy ZIP/history bytes, product implementation state NOT_IMPLEMENTED/NOT_RUN.

**Changed:**
- code-count and scenario-count hardcode removed; canonical requirement↔test mapping and duplicate scenario IDs validated.
- `kit catalog --id|--find|--limit|--json`, intended to reduce AI token spend.
- `feedback add --kind task`, `feedback note`, `feedback show`, `feedback verify`, `list --json` introduced.
- local feedback chain now has sequence number + previous digest + canonical JSON digest + O_EXCL single-writer lock and fail-closed state transitions (not remote integrity attestation).
- canonical docs map, feedback state contract, T3/T4 live test runbook, recursive MECE residual risk register, owner decisions revised.
- actual management CLI unit regressions expanded from 6 to 11. R5 is **not** implemented Brain or Generic software.
- maintainer-only `tools/update_manifest.py` performs explicit --apply, never silently rewrites evidence.
- no actual Git push, package publication or cloud/live AI testing.

**Open:** all product TDD and releases; cloud-only/Windows/Node/AI-provider live tests, external hash anchor, independent actor identity, single-writer cloud handover. These are NOT_PASS; release NO_GO.

# R3 Changes — Lifecycle Feedback Loop / Recursive MECE

Date: 2026-10-09. Parent: R2 reviewed Pre-TDD (`history/R2_input.zip`). **No implementation or runnable TDD tests added**.

## Existing files fixed
- `docs/02_ARCHITECTURE.md`: removed contradictory multi-writer canonical publish protocol; aligned with single Writer + capture-only.
- `docs/23_OPERATION_PLAYBOOK.md`: removed accidental form-feed in example Windows file path.
- `docs/adr/0010-canonical-json-hash-chain.md`: explicitly deprecated duplicate; canonical ADR-0010 is `0010-canonical-jcs-event-hash.md`.
- R2 norm docs 01/21/22/24/29/30 include authoritative R3 addenda; original R1/R2 sources preserved.

## New scope
- `docs/32`~`45`: SSOT precedence, feedback state machine, new requirements, TDD→release gates, SLI/SLO, incident/root-cause, secure supply chain, DR/fault drills, candidate attestations, AI eval, ownership/cadence, recursive MECE matrix, audit findings, sources.
- `schemas/governance/v1`: 8 governance record schemas with 8 structural positive/negative fixture pairs.
- New unique requirements `54`; existing 134 retained; total **188**.
- Lifecycle scenario catalog 30 (planned, **not run**).
- History contains R1 and R2 input files; RFC/hash based manifest regenerated for R3.

## Decision and limits
- Normative R3 is design-only, no runtime results.
- Feedback can be CLOSED only with effect verification, not because tests are green.
- Test pass is candidate fingerprint-bound. PeerHub feedback/consensus is optional and does not replace approval.
- Benchmarks/DR/deployment/SBOM/provenance not actually run; actual user settings/encryption/retention/forensic admissibility not certified.

Final cross-check added a dedicated `governance-event.schema.json` so append-only improvement transitions are explicit, not just prose. Governance schemas total **8** and positive/negative fixture pairs total **8**.

- Added `docs/46_POST_TDD_EXECUTION_ROADMAP.md` with milestones M0~M8, concrete deliverables and candidate-bound finish conditions.

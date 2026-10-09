# S1 roadmap — GitHub SSOT

Implementation: `profiles/secondbrain/`. Historical specs: `docs/reference/`.
Release version `0.0.0`; product **NO-GO**.

## Completed local development slices

- **R7:** source-preserving local Capture receipt and READY marker.
- **R8:** local single-writer Vault publication and capture-specific pending Observation.
- **R9:** RFC 8785 canonical local Acquisition/Custody event pair and unanchored chain.
- **R10:** operator-managed off-root checkpoint export/comparison (custody of that
  checkpoint itself is not verified).
- **R11:** [unsealed EvidenceObject creation and full per-Capture lineage](../../profiles/secondbrain/R11_SCOPE.md)
  with immutable local metadata, capture-specific Observation/Acquisition/Custody
  cross-links, retry, integrity and CLI. Verified synthetic PR tests and exact
  limitations are tracked at [R11 gate](../history/R11_GATE.md). No external
  anchor, legal seal, trusted time or cloud durability is inferred.

## Next gate: R12 — independent backup and restore

1. RED: deterministic backup manifest, copying of the verified *entire*
   capture/Vault/Observation/ledger/object closure; reject missing or
   inconsistent source records and placeholders; preserve exact bytes.
2. Restore into a separate root without overwriting a populated or
   untrusted destination. Fail closed on interrupt, partial snapshot,
   conflicting path, symlink and digest mismatch. Prove all R7–R11
   verifiers still agree and exercise repeated idempotent restore.
3. Verify actual independently retained copies and documented restoration
   with operator-observed results. Simulated local copies are not proof of
   independent offsite retention.
4. Add Windows (NTFS, junction/reparse) and OneDrive/Google Drive
   offline/placeholder/conflict matrix on real endpoints after isolated
   synthetic tests. Do not test with personal evidence.

## Deferred gates

External authentic time and checkpoint custody, cross-device/cloud writer
fencing, hostile filesystem TOCTOU hardening, Legal Hold policy, legal export,
AI/privacy and paid-provider tests, installer/wheel/winget review, independent
security assessment and public product release.

For all gates: RED → cause → minimal GREEN → full synthetic regression →
candidate-bound GitHub CI → PR review → merge → fresh main CI. Maintain
Very Simple, SSOT, no duplicate engines, no evidence/secrets/caches/ZIPs in Git.

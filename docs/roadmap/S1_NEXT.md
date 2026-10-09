# S1 roadmap — GitHub SSOT

Current code: `profiles/secondbrain/`. Historical specs: `docs/reference/`. R10 was the first manual off-root checkpoint comparison.

## Next vertical slice (R11)
1. RED tests for EvidenceObject record schema and cross-links to the local Vault payload and R9 acquisition/custody receipt. Duplicate records must not silently overwrite.
2. Minimal source implementation using canonical content address and immutable create-if-absent. Different Captures containing the same bytes share payload but retain independent Acquisition and Observation records.
3. Fail-closed partial write and read-only verify, including hash and record path consistency, duplicate keys, missing metadata, symlink, abort/retry.
4. Run full local tests and candidate-bound GitHub CI; update `profiles/secondbrain/R11_SCOPE.md` and `docs/history/R11_GATE.md` with exact run/SHA.
5. Move on to independently verified backup/restore and Windows reparse-point tests **after** content records and recovery are correct.

## Deferred gates
- Cloud OneDrive/Google Drive test matrix, conflict reconciliation, offline/placeholder behaviors, snapshot integrity, independent backup and restore.
- Trusted external timestamp/signature/anchor (manual checkpoint comparison is **not** proof of independent external custody).
- Legal Hold rules, production security review, installer/wheel validation, real provider/paid AI tests and production release.
- GitHub private source control is the source of truth; no nested ZIP release artifacts or personal evidence should be added.

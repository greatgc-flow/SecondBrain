# R12 local snapshot/restore quality gate — 2026-10-10 KST

**Partial gate: synthetic local implementation only.**
Operational independent-backup acceptance **NOT MET**; formal product
release **NO-GO** (version 0.0.0).

## Traceable RED → GREEN and candidates

- PR: https://github.com/greatgc-flow/SecondBrain/pull/9
- First RED commit `180c86d767a849e3e1478d0a5617449e9b682851`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991572408
  FAILED (missing backup module; intended RED).
- First code candidate `f7fedd5dbc763526493bcfa68c0afc275b6d5241`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991644558
  125 passed, 1 failed because CLI not yet wired.
- CLI added at `fd60338490492f0ae256ec9626b94103678d18e4`;
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991661994
  125 passed, 1 failed: missing completion marker was categorized as
  `SNAPSHOT_TAMPERED` instead of `INCOMPLETE_SNAPSHOT`.
- Additional RED `fc42321ff41817e4b34250ee5adf67303db5b065`;
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991748530
  126 passed, 4 failed: marker classification, unnoticed unlisted empty
  source/snapshot directory, and marker-write failure.
- Corrections `1a69c4d0a879b597c03a6a2095a4c18b60408a68`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991767413
  **SUCCESS — 130 passed**, Python 3.12 and actual pinned
  `rfc8785==0.1.4`: prior R7–R11 106 plus R12 24 synthetic tests.
- **Final PR #9 tip** `8b5c43593b0001e29e3d7fde828ea7067e6f06df`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37991953845
  **SUCCESS — 130 passed in 9.95s**, Python 3.12, real `rfc8785==0.1.4`.
- **PR #9 squash-merged** to `main` commit
  `9863a6974249701bf7c48ab4c731758a91a7eed3`:
  https://github.com/greatgc-flow/SecondBrain/commit/9863a6974249701bf7c48ab4c731758a91a7eed3
- **Exact post-merge main CI**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37992051401
  **SUCCESS — 130 passed in 9.61s**, Python 3.12 with installed
  `rfc8785==0.1.4`; run SHA exactly equals `9863a6974249701bf7c48ab4c731758a91a7eed3`.
- **R12 synthetic source-development gate PASS**. **R12 independent
  offsite/physical operational backup gate NOT TESTED / NO-GO**, and
  product release remains NO-GO. The final documentation-only closure
  does not revise the verified code tree.

## Implementation contract

- [backup.py](../../profiles/secondbrain/brain_core/backup.py):
  detect complete R7–R11 closure; copy exact files under a new off-root
  path, RFC8785 canonical manifest and last completion marker;
  independently verify snapshot bytes and full local cross-links;
  no-overwrite isolated restore and exact idempotent retry.
- [brain.py](../../profiles/secondbrain/brain.py): CLI create, verify,
  restore, machine-readable statuses and stable nonzero failure.
- [RED and GREEN tests](../../profiles/secondbrain/tests/test_backup_r12_tdd.py),
  [scope](../../profiles/secondbrain/R12_SCOPE.md),
  [quickstart](../../profiles/secondbrain/R12_BACKUP_QUICKSTART.md).
- Verified categories: normal, zero bytes, duplicate payload, malformed
  marker/manifest, extra/missing file, unexpected empty directories,
  orphan/uncommitted Capture, source corruption, unsafe symlink,
  writer busy, interrupted copy/restore/marker, destination collision,
  relocation, CLI and no network. **Synthetic only.**

## Known risk and NO-GO rationale

No independent physical/offsite custody proof, actual independent
restore drill, trusted anchor/authenticated manifest, reparse/junction
or hostile directory race proof, real cloud placeholder/conflict/multiple
writers, tested power-loss durability, RPO/RTO, wheel install/packaging
or formal legal evidence export. Restore duplicates writer authority:
the original and recovered roots must **never both become live writers**
without separate operator-controlled leadership transition. A locally
rewritten history plus correspondingly rewritten manifest may pass
verification. Protect sensitive snapshot files (including original
Capture source paths) outside GitHub. R13 operational evidence is
required before any production backup/restore or release claim.

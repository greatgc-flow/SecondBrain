# R11 quality gate — local EvidenceObject lineage (2026-10-10 KST)

**Development gate only; formal release NO-GO.** Private repository,
version `0.0.0`. This report distinguishes a verified commit-bound test
result from future PR/main results; consult the linked GitHub run for the
current latest verdict.

## Test and CI evidence

- PR: https://github.com/greatgc-flow/SecondBrain/pull/7
- Initial RED commit: `3ac761098b53499b7aa5c36b07c688cb98ec4af6`
  (new tests import missing R11 object module); reproducing failed CI:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37989698922
- First GREEN candidate `92f4c015f0c53b997a8cdebfcaa58e215d478a1a`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37989832573
  **101 passed** (84 existing + 17 new).
- Additional RED regression: object metadata timestamp rewrite was not
  bound to per-capture link. A matching metadata hash is now added to every
  capture-specific link, while preserving one shared object per byte digest.
  Newly added interrupt test exposed an `INCOMPLETE_COMMIT` vs
  `INCOMPLETE_OBJECT_LINK` classification inconsistency.
- Corrected implementation commit `14f58793a7e22e622633d93c7b29afcb0c2b5fc5`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37990121790
  **SUCCESS: 106 passed in 4.40s**, including all 84 prior tests and
  22 R11 synthetic tests, on GitHub Python 3.12 with real
  `rfc8785==0.1.4`. The precise count refers to this commit.
- Final PR tip CI and post-merge `main` CI require a fresh verification;
  do **not** infer them from the successful intermediate implementation CI.

## Implementation

- [object.py](../../profiles/secondbrain/brain_core/object.py): local
  shared object record with `recorded_at`, an unsealed scope and real
  content digest; per-capture canonical immutable lineage linking the R7
  Capture, R8 pending Observation and receipt, R9 Acquisition/Custody pair
  and commit receipt, and exact object record bytes.
- [schema](../../profiles/secondbrain/schemas/v2/evidence-object.schema.json):
  accepts old legacy `sealed_at` metadata or new
  `recorded_at + record_scope`, not both. Legacy naming is not proof of
  legal sealing. New creation never writes `sealed_at`.
- [tests](../../profiles/secondbrain/tests/test_object_create_r11_tdd.py)
  use synthetic payloads only; retry/idempotency, byte deduplication,
  tampered link/record/payload/observation/capture/custody, unsafe symlinks,
  JSON duplicate keys, missing dependencies, Unicode and spaces in root,
  zero bytes, fsync/publish injection, CLI statuses/codes.
- [scope](../../profiles/secondbrain/R11_SCOPE.md) and
  [quickstart](../../profiles/secondbrain/R11_OBJECT_QUICKSTART.md).
  `brain object verify` remains byte-only; `verify-link` is a read-only
  local cross-reference check.

## Failure → cause → remedy → verification

1. Missing R11 create command → no local EvidenceObject writer existed
   → implement minimal object + per-Capture link using existing R7-R9
   verification/immutable write helpers → initial 101 GREEN.
2. Object metadata clock-only mutation undetected → link had event hashes
   but no digest of full object metadata → bind `object_record_sha256`
   into link → synthetic regression.
3. Pre-object-write failure classified as generic incomplete commit →
   reader reported old narrow error → return R11 incomplete-link code →
   test and 106 GREEN.

## Remaining risks / NO-GO rationale

This is **local consistency**, not independently proven truth of acquisition,
third-party custody, WORM, legal admissibility or a trusted timestamp.
Consistent full-local-history rewriting, malicious concurrent directory
replacements/TOCTOU, actual OS power-loss durability, Windows reparse,
cloud concurrent writers/placeholders/conflicts, verified independent
off-site backup and restore, portable wheel/installer and paid-AI egress
remain unverified or unimplemented. The success of Ubuntu synthetic
tests is not evidence that these operational requirements work.

**Next slice: R12 independently verified backup/restore** followed by
real Windows/cloud filesystem fault matrix. No PyPI or winget release.

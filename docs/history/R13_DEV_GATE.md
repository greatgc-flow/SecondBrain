# R13-A development gate — recovered-root quarantine and Windows CI

**Date:** 2026-10-10 KST. **Status:** implementation candidate;
this document must be supplemented with final PR-tip and merged-main CI
results before declaring the source gate complete. Full R13 operational
acceptance remains **NO-GO** (issue #11); product release **NO-GO**.

## Problem → RED → GREEN

- R12's byte-exact recovery duplicated original writer authority/epoch.
  It did NOT separately block new writes from the restored root.
- PR #12: https://github.com/greatgc-flow/SecondBrain/pull/12
- RED commit `587093851fb4bd92de0072102218cba5d8027254`;
  intentionally failing CI:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37992671464
- Initial Ubuntu GREEN commit `ea7146a79c159931e40cc38c5792a9228a84c1cf`;
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37992827162,
  **139 passed** (R7–R12 130 + R13 quarantine 9).
- First Windows matrix candidate:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37992940260
  **Windows: 137 passed, 2 failed** while Ubuntu 139 passed.
  Root cause: pre-existing test code relied on Windows default CP1252
  `Path.read_text()` to read a UTF-8 Korean capture receipt.
  Fixed **test decoding only**, `encoding='utf-8'`, no production
  codec override or OS locale hardcoding.
- Windows NTFS junction regression tests added (real `mklink /J`),
  accompanied by explicit `is_junction()` rejection in R7 capture
  source/parent checks, R8 writer root, R11 object file verifier and
  R12 snapshot source/destination walk.
- Candidate `4998c09dc3d319d3c3e26b701508454ea7be7b73`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37993107386
  **SUCCESS:** Ubuntu `139 passed, 2 skipped` (the actual Windows-only
  tests), Windows `141 passed`, Python 3.12 with real
  `rfc8785==0.1.4`. Both Windows NTFS junction tests executed and passed,
  not skipped. Prior CP1252 failures are resolved without modifying
  application data serialization.
- Final PR-tip SHA/Ubuntu+Windows CI and post-merge `main` SHA/CI:
  verify at time of merge and append by a documentation-only closure PR.
  Do not infer later results from early passing runs.

## R13-A software scope

1. A new R12 restore creates TWO local canonical records under
   `90_System/writer/`: `recovery-hold.json` and
   `recovery-sentinel.json`, **before** copying writer authority.
   The records reference the exact R12 snapshot manifest SHA-256.
2. Presence of **either** marker blocks `capture file`,
   `writer init|publish`, `custody commit`, `object create` and
   `backup create` with `RECOVERY_HOLD`.
3. Read-only R7–R12 verifiers and `brain recovery status` remain
   functional. Repeat restore compares ALL original data bytes AND
   both canonical markers to the original manifest; changed/missing
   marker → `DESTINATION_CONFLICT`. Never overwrite partial data.
4. The restored root has **additional local operational markers**.
   Its original R7–R11 files are byte-exact, but the full root,
   including new markers, is deliberately not byte-identical to
   the R12 snapshot. R12 snapshot payload and manifest are untouched.
5. No automatic `activate` operation exists. Local advisory
   quarantine is NOT a trusted, distributed, cross-cloud writer fence.

## Known limitations — do not close issue #11

Full-root writer can delete **both** markers. This cannot be secured by
local writable files alone; real distributed fencing and tested handover
require externally managed authority. Previously restored R12 copies
do not retroactively gain quarantine. Windows GitHub-hosted runners
test only synthetic paths/junctions; not OneDrive/Google Drive
placeholder, offline or conflict behavior, cloud concurrency, network
shares, actual sudden power loss, hostile path races/TOCTOU, operator-
controlled independent backup custody, encryption/access governance,
or a loss-of-primary restore drill with measured RPO/RTO. Production
security and legal acceptance also remain outside this development gate.

## SSOT

- Code: `profiles/secondbrain/brain_core/{recovery,backup,capture,writer,custody,verify}.py`
- CLI: `profiles/secondbrain/brain.py`
- Tests: `profiles/secondbrain/tests/test_recovery_hold_r13_tdd.py`
  and `test_capture_tdd.py`
- Guide: `profiles/secondbrain/R13_RECOVERY_SCOPE.md`
- Operational R13 gate: https://github.com/greatgc-flow/SecondBrain/issues/11

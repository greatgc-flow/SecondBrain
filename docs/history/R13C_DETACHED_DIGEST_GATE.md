# R13-C synthetic source gate — detached operator-supplied fingerprint

**Date:** 2026-10-10 KST. **Baseline main:**
`b500284579d00d52fda3baec94fc7d5a9c2537d7`.
Version `0.0.0`; full R13 operational gate and product release remain **NO-GO**.

## Purpose / before-and-after

Old R12 `backup verify|restore` internally checks SHA-256, path
inventory, completion marker, Capture/Vault/Observation/Custody and
EvidenceObject linkage. It **does not** distinguish two perfectly valid
but different internally coherent snapshots after a full replacement.

R13-C optional `expected_manifest_sha256` uses the **existing R12
manifest body SHA**: reject wrong `--expect-manifest-sha256` before
creating a new destination, and reject bad type/length/non-lowercase
hex. A valid, independently supplied pin identifies which manifest the
operator previously accepted. It does NOT prove who supplied or
independently retained the pin; the caller must authenticate it.

## Test traceability

- PR #16 https://github.com/greatgc-flow/SecondBrain/pull/16
- RED commit `28c53b42a5753e96220e4a113cf62d377bc9bda1`.
  Prior implementation lacked both API argument and CLI flag:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37996704658
- Implementation: `profiles/secondbrain/brain_core/backup.py`,
  `profiles/secondbrain/brain.py`, plus R13-B cross-runner
  `ci_cross_runner_drill.py` exercising pins from a **co-traveling**
  synthetic proof (not an external authenticated source).
- Tests:
  `profiles/secondbrain/tests/test_detached_manifest_pin_r13c_tdd.py`.
  Matching pin, mismatch before restore creation, two distinct
  valid snapshots, bad input types, CLI JSON codes, backward
  compatibility and preexisting restored target refusal.
- Final PR-tip and post-merge exact SHA + Ubuntu/Windows 6-job CI
  results must be added after observation, **never assumed**.

## Security and operational limitations

A `proof.json` or digest copied with the snapshot is **not**
independent custody. This gate demonstrates an optional comparison
interface only; no signatures, trusted time, hardware TPM, WORM,
legal authenticity, genuine offsite operator-held backup,
Google Drive/OneDrive sync fault or secure distributed writer
handover has been validated. R13 operational
[issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11)
remains OPEN, and formal release **NO-GO**.

Guide: [R13-C quickstart](../../profiles/secondbrain/R13C_DETACHED_DIGEST_QUICKSTART.md).

# R13-G source development gate — operator-invoked synthetic witness preflight

**Current scope:** local, disposable R13-B synthetic fixture only. This is
not an operational independently administered backup, physical-loss DR
rehearsal or approval to release SecondBrain (version 0.0.0; NO-GO).

## Narrow problem solved

Previous `ci_cross_runner_drill.py consume` reads the canonical manifest
fingerprint and checkpoint from files packaged alongside the snapshot.
This confirms interoperability but **not independently retained
witnesses**. A real operator also needs a repeatable script that refuses
to create a new restore root until a manually supplied, off-snapshot
manifest pin, exact capture roster and checkpoint match the downloaded
bytes.

`profiles/secondbrain/synthetic_offline_drill.py` requires all of:

- `--snapshot <RETRIEVED_SYNTHETIC_SNAPSHOT>` (R12 sealed snapshot tree)
- `--to-root <NEW_NONEXISTENT_ROOT>` (never overwrites an existing path)
- `--expect-manifest-sha256 <64_LOWERCASE_HEX_FROM_SEPARATE_CHANNEL>`
- `--checkpoint <OPERATOR_RETRIEVED_R10_CHECKPOINT>`
- `--expect-capture ci-device/CAP-...` **repeated for every capture**.

Example using **synthetic test IDs only**:

```text
python synthetic_offline_drill.py --snapshot <retrieved-snapshot> --to-root <fresh-root> --expect-manifest-sha256 <externally-held-digest> --checkpoint <detached-checkpoint> --expect-capture ci-device/<actual-CAP-ID-A> --expect-capture ci-device/<actual-CAP-ID-B> --expect-capture ci-device/<actual-CAP-ID-C>
```

The operator must get actual IDs and pin **before the primary becomes
unavailable** and must preserve their independent custody separately;
merely typing a value **is not proof of independence**.

## Fail-closed behavior

1. Validate Capture roster argument format, uniqueness, no pre-existing
   target and external checkpoint path (reject checkpoint inside snapshot).
2. Verify R12 canonical manifest and **operator-supplied expected digest**
   before creating any recovery root.
3. Require the **exact** Capture ID roster, `ci-device` IDs and
   `collector=ci-synthetic` for every linked R7 receipt. This utility
   deliberately refuses ordinary user/evidence captures.
4. Compare supplied R10 checkpoint against the complete source-absent
   snapshot **data** root before restoring anything.
5. Restore to fresh root, preserving R13 dual recovery-hold markers,
   validate complete event chain, exact checkpoint, every Capture,
   Observation/Writer publication, Acquisition/Custody commit and linked
   EvidenceObject.
6. Output JSON with explicit
   `SYNTHETIC_LOCAL_RESTORE_VERIFIED_OPERATOR_CUSTODY_UNVERIFIED`,
   `read_only_advisory`, `restore_execution_seconds` and
   `actual_rpo_rto=NOT_MEASURED_OPERATOR_REQUIRED`.
   A failure returns exit code **3**, with `error_code`; no silent
   success or cleanup of a partial restore.

## TDD & software-only acceptance

- Implementation PR: https://github.com/greatgc-flow/SecondBrain/pull/24
- RED: `tests/test_operator_synthetic_drill_r13g_tdd.py` includes
  successful source-absent synthetic restore, stale but valid snapshot
  and detached digest mismatch, malformed pin, missing/altered checkpoint,
  incorrect/duplicate/malformed Capture roster, refusal to overwrite,
  CLI error JSON and quarantined root.
- **RED first-tests commit** `8242bb014d4ff566077cb8adb6cb62bab867d49b`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38012661565
  Expected **one collection/import error per OS** (operator helper not
  yet implemented). Both CI fixture producer jobs were skipped.
- **Initial failing implementation** `a3bc6d4748e5ce81d41276787a9bae5e3075893c`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38012688716
  Windows **10 failed/219 passed**; Ubuntu **10 failed/217 passed,
  2 Windows-only skipped**. Invalidly doubled regex end-of-string escape
  rejected legitimate `ci-device/CAP-...` IDs; corrected in
  `93a18eb30a1adf90a107d62846da14f9371b8b3c`.
- **First GREEN code candidate**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38012726740
  **SUCCESS ALL SIX JOBS**: Windows **229 passed in 146.24s**;
  Ubuntu **227 passed, 2 Windows-only skipped in 39.14s**;
  both cross-OS synthetic producer/consumer artifact restores passed.
- **Final PR #24 tip**:
  `a1b624403294db6f0990b75e86c7926d98ad566d`
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38012906061
  **SUCCESS ALL SIX JOBS**: Windows **229 passed in 182.94s**,
  Ubuntu **227 passed, 2 Windows-only skipped in 35.81s**;
  both cross-OS transfer/restore jobs succeeded. Actual Python 3.12
  `rfc8785==0.1.4` pinned in both test jobs.
- **PR #24 squash merged to main**:
  SHA `4b912ee3bf0cb052c5dc51474246a1c34b7bb45b`,
  https://github.com/greatgc-flow/SecondBrain/commit/4b912ee3bf0cb052c5dc51474246a1c34b7bb45b
- **Exact source-implementation merged-main CI**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38013233035
  **SUCCESS ALL SIX JOBS**: Windows **229 passed in 113.51s**,
  Ubuntu **227 passed, 2 Windows-only skipped in 37.21s**,
  independent synthetic Windows→Ubuntu and Ubuntu→Windows restores
  both passed; pinned real RFC8785 installed on both test OSes.
  Run head equals `4b912ee3bf0cb052c5dc51474246a1c34b7bb45b`.
- **R13-G synthetic operator-input preflight development gate PASS**.
  Neither separate CI jobs nor manually passed witness inputs establish
  real independently governed custody. Operational #11 and formal
  release stay **NO-GO**. This gate closure changes documentation only.

## Mandatory separate real-world gate

The field operator must conduct all 17
[NOT_RUN checklist](../runbooks/R13_OPERATOR_EVIDENCE_RECORD_TEMPLATE.md)
items from the [runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md).
Independently controlled media/account and witness, actual primary loss,
measured full RPO/RTO, real Windows/OneDrive/GDrive offline/conflicts,
distributed Writer fencing, durability and independent review remain
**NO-GO** until witnessed and documented. Never commit private evidence,
secrets or actual backed-up data.

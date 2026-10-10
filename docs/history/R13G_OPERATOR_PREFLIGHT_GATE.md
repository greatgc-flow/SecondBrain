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
- Exact failing run/green PR tip/merged-main six-job Windows and Ubuntu CI
  results must be recorded **only after observed**.
- **Development PASS** only if all six synthetic regression, producer and
  opposite-OS consumer jobs finish SUCCESS, with the pinned actual RFC8785.
  Neither separate CI jobs nor manually passed witness inputs establish
  real independently governed custody.

## Mandatory separate real-world gate

The field operator must conduct all 17
[NOT_RUN checklist](../runbooks/R13_OPERATOR_EVIDENCE_RECORD_TEMPLATE.md)
items from the [runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md).
Independently controlled media/account and witness, actual primary loss,
measured full RPO/RTO, real Windows/OneDrive/GDrive offline/conflicts,
distributed Writer fencing, durability and independent review remain
**NO-GO** until witnessed and documented. Never commit private evidence,
secrets or actual backed-up data.

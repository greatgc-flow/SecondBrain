# R13 slice A — restored-root quarantine (development-only)

**R12 baseline:** `b4150d078b7879a5befe2f11c28cd372884b5e47` (130 CI tests).
**New acceptance is strictly local software protection, NOT real multi-PC fencing.**
No production release; version stays `0.0.0`.

## Problem / reason

R12 restore copied `90_System/writer/authority.json` exactly. A recovered
copy could therefore use the same writer ID/epoch as the original while both
roots were accessible. Matching content hashes do not establish exclusive
leadership and R8's filesystem lock is **not** global or cross-device.

## Minimal behavior

1. A fresh restore installs two canonical RFC 8785 **local advisory** records
   in `90_System/writer/` **before copying any writer authority**:
   `recovery-hold.json` (RECOVERED_READ_ONLY) and
   `recovery-sentinel.json`. Both reference the R12 snapshot manifest SHA-256.
2. Read-only `capture verify`, `writer verify`, `custody verify|chain`,
   `object verify|verify-link`, `backup verify` and
   `recovery status` remain available. A restore retry checks every original
   file, full chain and BOTH exact marker bytes before reporting
   `RESTORE_ALREADY_VALID_LOCAL`; an absent/changed marker is a conflict.
3. Creating captures, initializing/publishing a writer, committing custody,
   creating EvidenceObjects and snapshotting a recovery-held root fail with
   `RECOVERY_HOLD` (exit 3 in JSON CLI).
4. **There is deliberately no `activate` / `unlock` command.** Writer
   takeover requires a future externally enforceable lease/fencing and
   an independently observed shutdown/handover of the former active writer.
   `recovery status` of an ordinary source returns
   `LOCAL_WRITER_POLICY_ONLY`, meaning **absence of hold**, NOT verified
   exclusive operation.
5. Backup manifest and snapshot bytes are unchanged. The two recovery
   markers live **only in the restored root** and are excluded from the
   source-data manifest comparison after their own bytes are verified.
   No claim is made that the restored tree is byte-for-byte identical
   including newly added operational markers. All ORIGINAL R7–R11
   files remain byte-exact.
6. Interrupted recovery leaves visible/quarantined partial state.
   No blind cleanup or overwrite. Adding the sentinel detects accidental
   deletion of a single marker.

## Boundaries / limitations

Anyone with write access to the entire root can remove **both** local
markers; neither is a cryptographic external authorization. Root directory
replacement race, Windows reparse/junction, actual power loss, network/cloud
sync multi-writer fencing, malicious filesystem admins, independent
restoration from physically/offsite retained copies and RPO/RTO remain
unverified. The markers are a *safety catch*, not a lockout or security
boundary. Existing R12 restore roots made before R13 do not automatically
gain the markers; do not claim migration or fail-safe retroactivity.

## Test and traceability

- [RED/GREEN tests](tests/test_recovery_hold_r13_tdd.py)
- [recovery.py](brain_core/recovery.py),
  [writer.py](brain_core/writer.py),
  [backup.py](brain_core/backup.py),
  [capture.py](brain_core/capture.py), [custody.py](brain_core/custody.py)
- [R13 quality gate](../../docs/history/R13_DEV_GATE.md)
- [R13 full operational criteria](https://github.com/greatgc-flow/SecondBrain/issues/11)
- Next: genuine Windows/NTFS and OneDrive/Google Drive matrix, independently
  controlled snapshot retrieval and operator-observed RTO/RPO, THEN
  distributed writer authority. Product release: **NO-GO**.

# R13-K development gate — snapshot control-leaf drift

**Version 0.0.0; production release and R13 independent operational acceptance remain NO-GO.**
Parent gate: [issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11).
All fixtures are synthetic. No personal evidence, secrets, real cloud storage, or durable independent snapshot was used.

## Failure mode

During `brain backup verify` or `brain backup restore`, a mutable filesystem can
replace `<snapshot>/manifest.json` or `<snapshot>/.complete` with a **different
ordinary file containing identical bytes** between the path check and the read.
Content hash and canonical JSON comparisons alone do not detect that the file
identity changed. Prior code could report success; on restore it could create a
recovery root following a changed control-file name.

## Minimal fix

In `brain_core/backup.py::_validate_manifest`, bind the pre-read leaf metadata
identity (device, inode, size, mtime, ctime, link count) and check it again after
the manifest/canonical read and after the marker/tree scan. Reject any difference
as `SNAPSHOT_TAMPERED` before a restore destination is created.

No second hashing engine, cloud SDK, snapshot format migration or silent repair.
R12 snapshots and valid sibling snapshot→verify→restore calls are unchanged.

## Reproducible TDD

- Base main: `710340b75db66cccef8039b4b6ae7823c9f0f361` (R13-J).
- RED test commit: `e077edb423019017e19bf3405aa3326a9f42eb08`.
- [RED CI run #38042012605](https://github.com/greatgc-flow/SecondBrain/actions/runs/38042012605):
  Ubuntu reproduced **4 failure cases** (verify/restore × manifest/marker), with
  **251 passed and 2 skipped**. Same-byte ordinary-file replacement had not been rejected.
- Initial code fix: `9717215c278cf886e9037949cb4cd394deef353d`.
- [PR #30](https://github.com/greatgc-flow/SecondBrain/pull/30).
- GREEN CI, merge and post-merge main CI are recorded only after observed completion.

## Limits

This is **best-effort local leaf drift detection**. It cannot guarantee
against hostile concurrent parent-directory alias/ABA swaps, malicious
filesystem code fabricating stable metadata, or a process that repeatedly
replaces a file and restores its identity. It is not a secure descriptor-relative
openat/openat2 design, distributed writer fencing or an independent trusted
custody/witness proof. Windows NTFS, actual sync-cloud hydration, ransomware,
power failure, independent RTO/RPO and multi-writer handover remain separate
operator test gates. Do not infer operational PASS from synthetic CI.

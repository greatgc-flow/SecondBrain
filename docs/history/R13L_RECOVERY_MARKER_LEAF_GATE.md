# R13-L development gate — recovery quarantine marker leaf identity

**Version 0.0.0. Full product release and R13 operational acceptance remain NO-GO.**
Parent: [operational issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11).

## Exact synthetic failure

R13-A introduced two local read-only quarantine control files in the restored
root: `90_System/writer/recovery-hold.json` and
`90_System/writer/recovery-sentinel.json`. R13-I checks their presence without
using `Path.exists()`. But the R13-K snapshot-control leaf guard did not
cover these **recovered-root** files. During `recovery status` or a repeated
`backup restore`, replacing either ordinary marker with a *different inode
containing identical canonical bytes* while its JSON is read could silently
pass. This violates local identity continuity, even though the content hash
does not change.

## Narrow remedy

`brain_core/recovery.py::validate_recovery_hold` records each marker's
pre-read regular-file identity (device, inode, size, mtime_ns, ctime_ns,
unique-link count), then rejects any identity drift after the canonical
read and structural validation. Unsafe/missing/special leaves remain
fail closed. There is no new hashing engine, restore mutation, marker
schema migration, network access, or special Windows-only branch.

Expected outcomes:
- `recovery status` fails `RECOVERY_HOLD_INVALID` when a marker is replaced.
- Existing-root `backup restore` refuses with `DESTINATION_CONFLICT`.
- Normal restored roots remain `RECOVERED_READ_ONLY`, and byte-exact
  idempotent restore retries still report `RESTORE_ALREADY_VALID_LOCAL`.
- Recovery quarantine remains **local advisory**, not remote writer exclusion.

## RED → GREEN reproducibility

- R13-K `main` baseline: `8df9056bcba0929131f544629cf29e9bc27b5832`.
- [PR #31](https://github.com/greatgc-flow/SecondBrain/pull/31).
- RED test commit `3c64e55fd45be6f39043483f14006bb64f1fbeda`.
- [RED run #38046599176](https://github.com/greatgc-flow/SecondBrain/actions/runs/38046599176):
  Ubuntu observed **4 failures / 256 passes / 2 skips**; all four swaps were
  incorrectly accepted before fixing the implementation. Windows job and
  full final CI outcomes must be read from the exact linked run.
- Initial narrow implementation commit:
  `b71da47f4b31a72341b46e2b6c4202981d3929e2`.
- Final full-matrix PR CI and post-merge main CI: **pending verification**.
  Do not promote to GREEN until the six jobs actually complete.

## Known boundaries

Local leaf stat comparison does not defeat an adversary with mutable parent
directories, forged/ABA metadata, cloud-provider runtime races, or control of
both markers. It does not establish independently retained custody, offline
OneDrive/Google Drive behavior, real power-loss durability, operator-tested
RPO/RTO, or cross-device writer fencing. Only synthetic data is permitted
in CI/GitHub; operational acceptance boxes in issue #11 remain unchecked.

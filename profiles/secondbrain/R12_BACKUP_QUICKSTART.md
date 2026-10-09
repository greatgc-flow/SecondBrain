# R12 local snapshot and verified restore (synthetic source only)

This is a **local byte-and-reference consistency demonstration**, not proof of
independent storage, secure source provenance, trusted timestamps, WORM,
durable power-loss safety, or legal admissibility. No ZIP, cloud SDK or AI.

## Precondition

Finish the [R11 synthetic flow](R11_OBJECT_QUICKSTART.md) for **every**
Capture under the root. R12 rejects even one READY-only, unlinked,
partial or inconsistent R7–R11 capture, and rejects unknown files,
symlinks, partial publication and unlisted directories. Do not use R12
to silently discard work in progress. All test roots must be disposable
synthetic data and on a filesystem supporting the existing writer lock.

## CLI

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'

# Use a completed, SYNTHETIC R11 root; backup destination must NOT exist.
python brain.py backup create --root '/path/to/한글 Second Brain' --to '/outside-root/snapshot-001' --json

# Read-only check using just the snapshot files.
python brain.py backup verify '/outside-root/snapshot-001' --json

# Target must not exist; if already present, only exact fully-verified
# repetition succeeds. A partial/conflicting target is NEVER overwritten.
python brain.py backup restore '/outside-root/snapshot-001' --to-root '/another/빈 복구 루트' --json
```

The snapshot directory contains `data/` (exact relative root files),
`manifest.json` (RFC 8785 canonical JSON with ordered path/hash/size
entries and custody-tip summary) and `.complete` (last-published
manifest-digest marker). No absolute root path goes in the manifest.
**The R7 captured receipt itself may still contain private source paths
and original names. Treat backups as sensitive.**

`LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED` means the supplied
local copy currently matches the manifest and complete R7–R11 linkage.
`LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED` means restored bytes,
entries and references match that copy. Neither proves the copy was kept
independently or was authenticated by a trusted party.

Errors return code 3 and machine-readable `error_code`: e.g.
`SNAPSHOT_NOT_CLOSED`, `SOURCE_INVALID`, `SOURCE_BUSY`,
`SNAPSHOT_TAMPERED`, `INCOMPLETE_SNAPSHOT`,
`DESTINATION_CONFLICT`, `INCOMPLETE_RESTORE`, `UNSAFE_PATH`,
`UNSAFE_DESTINATION`. Missing CLI arguments use argparse code 2.

**Fail-closed operational rule:** Do not delete or repair a partial
destination automatically. Quarantine/inspect it manually and use a
new backup/restore path. A retry at an existing restored path returns
`RESTORE_ALREADY_VALID_LOCAL` only after verifying all files and links.

**Restore safety:** The recovered writer authority preserves the original
writer ID and epoch. Never run the original and restored roots as active
concurrent writers, especially when cloud sync is involved. An operator
must explicitly designate a single active root and preserve the other as
an offline historical copy. This implementation does not implement
multi-device fencing or disaster-recovery leadership transfer.

## Gate exclusions

This is one-machine synthetic snapshot/recovery only. Actual independent
offsite retention, physically separate storage, ransomware isolation,
RPO/RTO and real power loss, actual Windows NTFS/reparse and cloud
placeholder/conflict behavior are **not tested**. Do not call R12 a
completed operational backup system until separately measured and
documented. Product remains 0.0.0, release **NO-GO**.

[Implementation](brain_core/backup.py) ·
[Tests](tests/test_backup_r12_tdd.py) ·
[Quality gate](../../docs/history/R12_GATE.md).

# R12 scope: complete R7–R11 local snapshot and exact restore

**Development-only feature**. Product version 0.0.0 / release NO-GO.
This is *synthetic, offline, local* file-and-reference consistency. It
does NOT prove an independent backup exists, has been retained, or
survives ransomware, source loss, hardware fault or cloud deletion.

## Data and API

- SSOT: [backup.py](brain_core/backup.py), reuse
  [Capture](brain_core/capture.py), [Writer](brain_core/writer.py),
  [Custody](brain_core/custody.py) and [R11 lineage](brain_core/object.py)
  verifiers, **not** duplicate reconstruction engines.
- CLI: `brain backup create --root ROOT --to NEW_DIR`;
  `brain backup verify SNAPSHOT_DIR`;
  `brain backup restore SNAPSHOT_DIR --to-root NEW_ROOT`.
- Snapshot directory format: `data/` stores exact bytes for every
  supported, linked root file. `manifest.json` holds relative POSIX
  paths, SHA-256, sizes, capture/object counts, local custody-tip hash;
  RFC 8785 canonical bytes, with a body-level SHA-256.
  `.complete` is the digest marker written **last**.
- Allowed root contents: R7 `00_Inbox/Drop` payload/receipt/ready;
  R8 pending ingest and Observation; R9 custody events/commit receipts;
  R11 unique EvidenceObjects, links, Vault payload; local writer
  authority. Unknown files, stage debris, unsupported empty
  directories, unlinked captures and symlinks fail closed. This is
  deliberately NOT a general purpose backup for extra folders in a
  user's future SecondBrain.
- Source backup uses the existing **local** writer lock, not a
  distributed lock. The lock file is excluded from the copy. Restore
  preserves writer metadata but MUST NOT activate concurrent roots.
- Backup target must be new and outside the source root hierarchy
  (neither parent nor child). The snapshot directory is reserved
  without overwriting existing files. Partial failure leaves
  inspectable incomplete directory without a valid completion marker.
- Snapshot `verify` checks the completed marker, canonical manifest,
  exact directory/file inventory and every hash; it re-runs the full
  R7–R11 local closure on the copied root.
- Restore refuses unsafe links and all conflicting pre-existing
  destinations, never replaces existing contents, verifies all bytes
  and references after copy, and accepts retry only if the already
  restored destination matches the full manifest and closure.

## Truthful state and risks

`LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED` and
`LOCAL_RESTORE_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED` prove local
comparisons to a **self-described** manifest, not independent
attestation. Consistent malicious rewriting of BOTH source data and
manifest may pass. Captured source receipts include personal paths;
backups may contain highly sensitive originals and must never be
committed to GitHub.

Synthetic CI exercises two captures/same bytes, zero bytes, full
relative path closure, missing linkage, source/event mutation,
manifest/copy/marker changes, missing/extra/unlisted paths and
directories, symlink rejection, writer busy, copy/fsync/marker
interruption, existing target refusal, validated repeat restore,
Korean/spaces, CLI JSON/exit codes and no network. It does NOT
establish actual physical power-off durability, independent cloud/offsite
retention, RPO/RTO, restore on Windows/NTFS reparse, OneDrive/Google Drive
offline conflicts, network filesystem locks, hostile filesystem races,
multi-PC fencing or legal authenticity.

## Follow-up / gate

- [R12 quality gate](../../docs/history/R12_GATE.md) tracks RED/GREEN,
  exact CI/commit and fixes; [quickstart](R12_BACKUP_QUICKSTART.md).
- Operational acceptance REQUIRES a real separately controlled
  storage account/media, operator-observed independent copy retrieval,
  documented loss-of-primary simulation, **successful R7–R12** restore
  on representative OS/FS, measured RPO/RTO, deletion/overwrite and
  cloud conflict fault matrix and privacy review. None are established
  by the GitHub CI.
- Next: R13 independent backup/drill and Windows/cloud filesystem
  matrix; only then assess trusted external checkpoint/authentication
  and product release. **Release NO-GO remains.**

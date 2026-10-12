# SecondBrain v0.1 design

SecondBrain preserves personal files on one local computer without changing their sources.  
The owner captures, finds, opens and verifies originals with recorded acquisition context.  
One user-managed backup folder supports a verified restore into an empty local root.

This is a proposed contract, not implemented functionality. The owner's `sb_plan_v21.md` controls scope.

## Root and source of truth

Default: `D:\SecondBrain`, local NTFS outside sync folders; configurable with global `--root`.
Reject known synced active roots with an explanatory warning; detection is best effort, not a guarantee.
Ubuntu CI uses a local filesystem test root.

```text
D:\SecondBrain\
  objects/ab/<64-character-sha256>  original bytes; prefix = first two hash characters
  receipts/v1/<id>.json            immutable receipt per acquisition
  config.json                     settings with exactly one backup_root
  cache/index.db                  derived, rebuildable SQLite FTS5 index
  cache/open/<id>/<original_name>  disposable working copies
```

Plain objects, receipts and configuration are the source of truth; the database is not.
Configure `config.json` with `{"backup_root":"D:\\GoogleDrive\\SecondBrainBackup"}` before backup.
First use creates the layout; no initialization, configuration or reindex command is added.

## Receipt: six fields, versioned

`receipts/v1/` identifies format version 1 without a seventh field; `tool_version` identifies the tool release.

```json
{
  "id": "cap-20261012-001",
  "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  "original_name": "contract.txt",
  "source_path": "C:\\Inbox\\contract.txt",
  "collected_at": "2026-10-12T09:00:00+09:00",
  "tool_version": "0.1.0"
}
```

IDs identify acquisitions, not hashes; identical bytes share one object but each acquisition gets a new receipt.
Record original name, source path, observed local collection time with timezone and tool version at first capture.
This is local context, not verified creation time, authorship or complete custody history.

## End-to-end scenarios

Commands/output are illustrative v0.1 interfaces; IDs, hashes and dates are sample values.
Start with local `C:\Inbox\contract.txt` and the backup configuration above.

```text
> sb capture "C:\Inbox\contract.txt"
captured id=cap-20261012-001 name=contract.txt object=new
> sb capture "C:\Inbox"
captured=2 reused_objects=1 failed=0
> sb find "contract"
cap-20261012-001  contract.txt  contract.txt [filename match]
> sb open cap-20261012-001
verified cap-20261012-001; opened D:\SecondBrain\cache\open\cap-20261012-001\contract.txt
> sb verify
OK receipts=3 objects=2 missing=0 corrupt=0 orphan=0
> sb backup
OK root=D:\GoogleDrive\SecondBrainBackup added_objects=2 added_receipts=3 manifest=20261012T001000Z-001.json
> sb restore "D:\GoogleDrive\SecondBrainBackup" --to "D:\Recovered"
OK restored_receipts=3 restored_objects=2; verify missing=0 corrupt=0 orphan=0; index rebuilt
> sb --root "D:\Recovered" open cap-20261012-001
verified cap-20261012-001; opened D:\Recovered\cache\open\cap-20261012-001\contract.txt
```

Capture a file or recursively capture each regular file in a folder without touching the source.
Unreadable/locked files produce per-file errors and nonzero exit; completed captures remain valid.
Open checks the hash before copying and launching a working copy; edits never change the object.
Verify checks receipt format, referenced hashes and object names; reports missing, corrupt and orphan files.

## Search

SQLite FTS5 searches names, receipt context and extracted UTF-8 `.txt`/`.md` and text-based PDF text (`pypdf`).
Start with `unicode61` tokenization; automatically rebuild missing/stale indexes from plain files.
Return acquisition ID, name and snippet; report extraction failures while retaining filename/context search.
No OCR, embeddings, semantic matching or Korean morphological analyzer in v0.1.
Korean spacing and particles affect matches; partial words and two-character substrings are not guaranteed hits.
Document a Korean benchmark: names, spaced/unspaced phrases, particles, two-character queries, expected/actual hits and extraction failures.
Report measured limits rather than universal Korean support; scanned PDFs have no extracted text.

## Backup and restore

One user-managed backup root mirrors objects and versioned receipts, with configuration and dated manifests.
Append-only: never delete, prune or overwrite differing bytes; content addressing makes originals incremental by nature.
Hash-check source and destination on every new write, including receipts/configuration; validate reused destination files.
Store configuration per manifest so settings changes preserve old backups; manifests list paths and hashes.
Publish the dated manifest last after its entire set verifies; exclude caches and working copies.
If `notes/` exists, mirror dated versions referenced by the manifest; no note editor/integration is provided.
Works inside Google Drive/OneDrive synced folders; the owner's sync client handles upload/download.
A reported link count of zero there is a warning, not failure; unavailable bytes or failed hashes still fail.
Files are plain and NOT encrypted: the cloud provider and anyone with folder access can read them.
No backup engine, restic/Kopia integration, rclone, cloud API, credentials or application network access.
Local backup success means verified local writes, not confirmed cloud upload or provider durability.
Restore selects the latest complete manifest, requires an empty destination and validates/copies all listed files atomically.
Run full verification and rebuild the index before success; use `--root` to access the restored root.
Incomplete manifests are not restore points; a failed restore remains explicitly incomplete, never reported as success.

## CLI: six commands

```text
sb --help
Usage: sb [--root PATH] COMMAND [--json]
  capture <file-or-folder>          Preserve bytes and acquisition receipt
  find <text>                      Search names, context and supported text
  open <id>                        Verify and open a working copy
  verify                           Check all receipts and objects
  backup                           Mirror to configured backup_root
  restore <backup-root> --to <dir>  Restore into an empty local directory
Options: --root PATH (default D:\SecondBrain), --json, --help
Exit: 0 success; nonzero on errors or verification problems
```

Every command supports `--json`: one structured stdout result with status, results and errors; diagnostics use stderr.
`sb find "contract" --json` yields `{"status":"ok","results":[{"id":"cap-20261012-001","name":"contract.txt","snippet":"contract.txt [filename match]"}]}`.

## Failure behaviour

A single-writer lock prevents concurrent publication; backup holds it to keep the manifest consistent.
Write temporary files on the destination filesystem, flush and atomically publish; publish object before receipt.
Interruptions preserve completed acquisitions; rerun handles unpublished files/unfinished objects without inventing receipts.
Retries of an interrupted acquisition with a published receipt do not duplicate it; a fresh capture records a new acquisition.
Atomic publication does not promise protection from every hardware/power-loss failure; verify exposes inconsistencies.
Hash mismatch, missing bytes, malformed receipts, occupied restore destination or lock conflict gives a clear error and nonzero exit.

## Non-claims and acceptance

Integrity and recorded context only: no authenticity, admissibility, independent timestamp or custody certification claim.
No litigation-readiness claim or proof against a rewritten archive.
Capture 100 mixed files: Korean names, spaces, long paths, duplicates, empty and locked files; errors must be explicit.
Interrupt each publication stage and safely rerun; check receipt-per-acquisition semantics and single-writer exclusion.
Check expected search hits against the Korean benchmark; rebuild the index without losing source records.
Tampering must block open/fail verify; missing, corrupt and orphan files must be reported.
Backup/restore into an empty directory must verify all hashes; test a Drive-synced backup folder and link-count-zero warnings.
Windows and Ubuntu CI must pass offline; the application performs no network operations.

## Later

- MCP: read-only access restricted to items the owner marks AI-visible.
- Web capture: SingleFile-based acquisition.
- Import: email and messenger exports.
- Inbox: acquisition from other devices.
- OCR: scanned text and transcription.
- Evidence tier: custody, TSA, packaging and lawyer-reviewed exhibits.
- Encryption: optional protection for backup files.

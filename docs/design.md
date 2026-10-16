# SecondBrain v0.1 design

SecondBrain preserves personal files on one local computer without changing their sources.
The owner captures, finds, opens and verifies originals with recorded acquisition context.
One user-managed backup folder supports a verified restore into an absent local root.

## Status and scope

- The current phase and gate are recorded in [status.md](status.md) (at this writing `DESIGN_REVIEW`; this document does not fix the phase). This is a target contract for v0.1, not implemented functionality; no implementation is asserted. Readiness is recorded separately in status.md, and the owner's explicit go is needed before TDD starts.
- Installed version today is `0.0.1`. The v0.1 target requires `secondbrain.__version__` and the build metadata to agree; that is a future packaging gate and needs no code edit now. `0.1.0` in examples is illustrative.
- Scope is unchanged: local `capture`, `find`, `open`, `verify`, `backup`, `restore`. Global options are `--json` and `--root`; `--print-path` (open), `--backup-root` (backup) and `--to` (restore) are the only command options. No other flags.
- The former external plan (`sb_plan_v21.md`) is absent; its hash is UNKNOWN (provenance gap in [collaboration.md](collaboration.md)). The accepted authority is this document plus [decisions.md](decisions.md) and the owner's current broad permission to improve earlier decisions.
- Where an older sentence contradicts a decision in [decisions.md](decisions.md) (0009-0013), the decision wins and the sentence is not normative.
- Integrity and recorded context only: no authenticity, admissibility, independent timestamp, custody or legal-weight claim.

## Root and on-disk authority

Default root on Windows: `D:\SecondBrain`, unsynced local NTFS outside sync folders. On Ubuntu an explicit `--root` is required and must be an unsynced local filesystem that supports the required OS locks and atomic no-replace operations; otherwise the command exits 2 with `unsupported_platform`. Known synced roots are rejected with an explanatory warning (best effort, not a guarantee).

| Path under root | Class | Content | Recovery |
|---|---|---|---|
| `objects/ab/<sha256>` | authority, immutable | original bytes; `ab` = first two lowercase hex chars | verify; restore from backup |
| `receipts/v1/<id>.json` | authority, immutable | six-field receipt; filename = id | verify; restore |
| `config.json` | authority, mutable | `{"backup_root": null \| "path"}` | rewrite by `backup`; restore from manifest config |
| `writer.lock` | coordination | persistent lock file, never unlinked | n/a |
| `cache/index.db` | derived | SQLite FTS5 index | rebuilt automatically |
| `cache/open/<id>/<n>/<name>` | derived, disposable | working copies, never deleted by the tool | user may delete |
| `tmp/` stage files | transient | staged bytes owned by the running command | see Failure states |

Plain objects, receipts and configuration are the source of truth; the database is not.

## Receipt: six fields

```json
{
  "id": "cap-20261012t000000z-ba7816bf",
  "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  "original_name": "contract.txt",
  "source_path": "C:\\Inbox\\contract.txt",
  "collected_at": "2026-10-12T09:00:00+09:00",
  "tool_version": "0.1.0"
}
```

- `receipts/v1/` names format version 1; `tool_version` names the release. There is no seventh field.
- `id` is `cap-<yyyymmdd>t<hhmmss>z-<first 8 hex of sha256>`, UTC, all lowercase. A same-second, same-prefix collision gets suffix `-2`, `-3`, ... chosen by retrying the no-replace publish of `<id>.json`. There is no persistent counter and no directory scan.
- The receipt filename is `<id>.json`, lowercase, and equals `id`. SHA-256 hex is lowercase everywhere.
- `collected_at` is zoned ISO 8601 from the local clock. All six fields are observed local context at first capture, not verified creation time, authorship or custody.
- `original_name` is acquisition data and preserved exactly as the source reported it. Search queries and the working-copy name are NFC-normalized and made safe (see Path safety); the original name is never rewritten.
- IDs identify acquisitions: identical bytes share one object, each acquisition gets its own receipt. Retrying after an unknown outcome may create a new acquisition; exactly-once capture is not claimed.

## Lock model

- **Writer lock:** `<root>/writer.lock`, created on first use, never unlinked. A nonblocking OS-released lock (`msvcrt.locking` / `fcntl.flock`); released by the OS if the process dies. No PID, age or timestamp based stale breaking.
- **Coherent reads:** `find`, `open` and `verify` take the same lock, nonblocking, while they read authority files and refresh the index, so no stale silent result is returned during a write. `open` releases it before launching the viewer.
- **Backup:** acquire the destination lock `<backup_root>/backup.lock` first, then the source writer lock, and hold both until completion. Fixed order prevents deadlock.
- **Restore:** locks only the sibling staging directory it exclusively created.
- A lock that cannot be taken immediately fails with exit 2; there is no waiting and no retry loop beyond Windows sharing-violation backoff.
- `sb --help` and usage errors never create or modify anything. Restore accesses only its backup input, the destination parent and its owned staging; it never initializes the global active root. Every other data command initializes its active root (layout and `config.json`) under that root's writer lock. Nothing is written to any source.

## Publication of immutable files

Objects, receipts, config snapshots and manifests share one procedure:

1. Write the complete bytes to a staging file on the target volume, flush, fsync, close.
2. Atomically publish to the final name with **no-replace** semantics (hard link or rename that fails if the target exists). Never open the final name directly with `O_EXCL` (a crash would leave a visible partial file).
3. Publish the object **before** the receipt.
4. If the final name already exists: for objects, verify its hash and reuse it; for receipts, take the next suffix.
5. Remove only staging files that this command created and still owns. Cleanup requires retained ownership and identity evidence (recorded at creation) that the current path still names the file this command created; a matching name or a held lock is insufficient. Old temp files are never swept by name, location or lock. A failed stage is retained and reported.

Orphans (objects without a receipt, left by an interrupted capture) are preserved and reported: `verify` exits 1, `backup` rejects them. Atomic publish does not promise protection from every power-loss failure; `verify` exposes inconsistencies.

## Path safety

- Reject overlapping `source`, `root`, `backup_root` and `restore --to` paths (one contained in or equal to another).
- Reject actual redirects: symlinks, junctions, mount-point or other redirecting reparse tags, linked directories during traversal, and special files (devices, sockets, FIFOs). Hydrated NTFS cloud-tag regular files (for example OneDrive/Drive placeholders already hydrated) are accepted with ordinary opened-file semantics for **both** capture sources and backup inputs; offline or unavailable bytes exit 2. This is not a blanket rejection of all reparse points. The active root itself must still be an unsynced local root: unsynced local NTFS on Windows, or an unsynced local filesystem with the required locks and atomic no-replace support on Ubuntu (otherwise exit 2 `unsupported_platform`).
- Working-copy and restore names are derived NFC, and rejected or replaced if unsafe: path separators, control characters, Windows reserved device names (`CON`, `NUL`, `COM1`, ...), alternate data stream `:`, trailing dot or space. A derived name falling back to `file` plus the id is allowed; the receipt keeps `original_name`.
- Source coherence: read through one opened regular-file handle; compare its identity, size and mtime before and after reading, hash the bytes actually staged, and confirm the pathname still names that same file before publication. Any change fails that file with `source_changed`. This detects ordinary mutation only; no snapshot or hostile-TOCTOU claim.

## CLI: six commands

```text
Usage: sb [--root PATH] [--json] COMMAND [ARGS]
  capture <file-or-folder>          Preserve bytes and acquisition receipt
  find <text>                      Search names, context and supported text
  open <id> [--print-path]         Verify and open, or only print the verified path
  verify                           Check all receipts and objects
  backup [--backup-root PATH]      Set/store root and mirror to backup_root
  restore <backup-root> --to <dir>  Restore into an absent local directory
```

| Command | Input | Output (default) | `--json` `results[]` item |
|---|---|---|---|
| `capture` | file or folder | `captured id=<id> name=<n> object=new\|reused`; summary for folders | `{id, sha256, original_name, object, warnings[]}` |
| `find` | one text argument | `<id>  <name>  <snippet>` lines | `{id, name, snippet, warnings[]}` |
| `open` | id | verified working-copy path message; `--print-path` prints the path only | `{id, path, warnings[]}` |
| `verify` | none | `OK receipts=N objects=N missing=N corrupt=N orphan=N invalid=N` | one singleton summary `{receipts, objects, missing, corrupt, orphan, invalid, warnings}` |
| `backup` | optional root | `OK added_objects=N added_receipts=N manifest=<name>` | `{manifest, added_objects, added_receipts, warnings}` |
| `restore` | backup root, `--to` | `OK restored_receipts=N restored_objects=N` | `{restored_receipts, restored_objects, warnings}` |

### Envelope, warnings and exit codes

- `--json` prints exactly one object: `{"status":"ok"|"error","results":[],"errors":[]}`; `ok` requires zero errors, `error` at least one. No exception text reaches stdout.
- The authoritative shapes are [schemas/cli-output.v1.schema.json](schemas/cli-output.v1.schema.json) (per-command result `$defs` and per-command envelopes, error-code enum, warning-code enum), [schemas/manifest.v1.schema.json](schemas/manifest.v1.schema.json), [schemas/receipt.v1.schema.json](schemas/receipt.v1.schema.json) and [schemas/config.v1.schema.json](schemas/config.v1.schema.json). This document does not duplicate the code lists. Schemas are structural only; the semantic checks are listed in their `$comment` fields.
- Result cardinality: `open`, `verify`, `backup` and `restore` return at most one result and exactly one when `status` is `ok`; on `error` they return 0 or 1. A completed `verify` inspection yields exactly one summary even with problems; a lock or pre-inspection failure yields none. `capture` and `find` return zero or more.
- All six result types carry `warnings[]`. Human-readable diagnostics go to stderr; under `--json`, warnings are structured per-result `warnings[]` and nothing else reaches stdout. A successful result keeps `status:"ok"` and `errors:[]`.
- Exit precedence **2 > 1 > 0**. `1`: missing, corrupt, orphan or schema problems. `2`: usage, lock, IO, source-change, unsafe-path, config-persist or unsupported-platform errors. Successful results are retained alongside errors, including a completed backup result whose final config save failed (`status:"error"`, code `config_persist_failed`).
- Folder capture is recursive, sorted by path, and partial: successful files are published, failures go to `errors[]`, and any failed item forces exit 2 even if other items had integrity (exit 1) problems. An empty folder exits 0 with zero results.

## Capture

Stat the source, read and hash while staging, re-stat; publish the object (or verify and reuse an existing one), then the receipt. Source files are never modified. Unreadable or locked files give a per-file error; completed captures stay valid.

## Open

Verify the object hash, then copy into a fresh unique directory `cache/open/<id>/<n>/` (n = 1, 2, ...), then hash the copy and compare before launching. Edits happen on the copy and never reach the object; earlier copies are never overwritten or deleted. `--print-path` prints the path only (with `--json`, a structured result). An OS launch failure exits 2.

## Search

- SQLite FTS5, `unicode61`, over names, receipt context and extracted UTF-8 `.txt`/`.md` and text-based PDF text (`pypdf`). No OCR, embeddings or Korean morphological analysis.
- The query is NFC-normalized and split into literal tokens; embedded FTS quotes are escaped, each token quoted, joined with AND. Raw FTS operators (`OR`, `NEAR`, `*`, `"`, `:`) are never interpreted. A query with no searchable tokens returns zero results.
- Results are deterministically sorted (rank, then id). The default limit is a bounded 100 with an explicit `search_truncated` warning (stderr for humans, the last result's `warnings[]` in JSON); no extra flag.
- Index freshness uses a fingerprint over a deterministic sequence of receipt paths and receipt **byte** digests, assuming immutable objects. A missing, stale or corrupt index is rebuilt into a separate database and published safely under the authority lock; a rebuild or publication failure exits 2. `verify` and `open` remain the integrity checks; the index never proves integrity.
- Text and PDF extraction run in a bounded subprocess. Initial assumptions, not benchmark proof: 32 MiB input, 4 MiB extracted text, 10 s, 256 MiB memory. If these limits cannot be enforced on the platform, extraction is skipped with an `extraction_skipped` warning and name/context search is retained. Capture itself is unrestricted. An extraction error is a warning; names and context stay searchable. The numbers may be revisited through the benchmark, not through a runtime framework.
- Korean spacing, particles and two-character queries are not guaranteed hits; the benchmark reports measured limits.

## Backup tree and schema

```text
<backup_root>/
  objects/ab/<sha256>
  receipts/v1/<id>.json
  configs/<sha256>.json
  manifests/<yyyymmdd>t<hhmmss>z[-N].json
```

Manifest JSON: `{"schema_version":1,"created_utc":"...","tool_version":"...","entries":[{"kind":"object|receipt|config","path":"...","sha256":"...","size":N}]}`. Rules:

- Exactly one `config` entry; the object entries are exactly the objects referenced by the receipt entries (set equality), and every receipt entry's `path` equals `receipts/v1/<id>.json`.
- Strict JSON: duplicate keys, a BOM, `NaN`/`Infinity` and unknown fields are invalid. Path semantics: no absolute paths, no `..`, no case aliases (two paths equal under case folding).
- Append-only: never delete, prune or overwrite differing bytes.
- Manifest names: lowercase `t` and `z`, a valid UTC calendar timestamp that **must equal** the UTC date-time portion of `created_utc` (seconds precision), and an optional canonical integer suffix `-N` with N ≥ 2 (no `-1`, no leading zeros). An unsuffixed name sorts as 1. Publication retries suffixes numerically on collision.
- That name-versus-`created_utc` match is a **semantic** check on the external file name; JSON Schema cannot express it and the manifest schema gives no assurance about it.
- Unexpected entries in `manifests/` (including a malformed or mismatched manifest name) are integrity errors (exit 1), never silently ignored. Only explicitly defined coordination files (`backup.lock`, outside `manifests/`) and this command's own retained staging files are excluded from that rule.

### Backup sequence

1. Validate the explicit candidate destination without mutation.
2. Acquire the destination lock, then the source lock. Under those locks read the configuration and derive the effective config snapshot. If the destination came from configuration, revalidate that it still matches; otherwise exit 2. Reject orphans.
3. Copy or reuse each object, receipt and the config snapshot; verify every copy by hash, reuse included.
4. Publish the manifest **last**, no-replace, atomic.
5. Persist the local `config.json` (the backup root) and only then release both locks.

If the final config save fails, exit 2, return the completed backup result alongside a `config_persist_failed` error, and state explicitly that a complete **local** backup exists. A locally valid backup does NOT confirm cloud sync or provider durability.

The newest manifest is chosen by parsed timestamp then numeric suffix (`-10` > `-2`), never lexicographic. If the newest manifest is corrupt, exit 1 with no fallback to an older one; there is no `--manifest` flag. Documented recovery: build an isolated mirror containing the byte-exact selected manifest plus all its payloads; the original backup stays untouched.

Cloud-synced backup folders are allowed: hydrated regular files are accepted, a reported link count of zero is a warning, directory redirects are rejected, unavailable bytes exit 2. Files are plain, NOT encrypted. No backup engine, credentials or application network access. Provider drills are NOT_VERIFIED.

## Restore

`--to` must be **absent** (an existing empty directory is no longer accepted). Steps:

1. Select and fully validate the manifest (schema, hashes of all files, set equality).
2. Create a sibling staging directory, exclusively owned by this command and retained on failure.
3. Copy payloads and receipts; restore the sole `configs/<sha256>.json` entry as staging `config.json`, preserving its exact bytes. Verify, rebuild the index, run full verification in staging.
4. Activate with an atomic **no-replace** rename: Linux `renameat2(RENAME_NOREPLACE)` or a tested equivalent; Windows a rename that refuses an existing target. No check-then-replace. If neither is available, exit 2.

Successful activation is the commit point. A crash right after it may leave a complete destination without a reported success; a rerun then refuses that existing destination and never removes or replaces it automatically. A failed restore is never reported as success. Use `--root` to open the restored root.

## Failure states

| State | Detected by | Result |
|---|---|---|
| Missing/corrupt object, malformed receipt | `verify`, `open` | exit 1 |
| Orphan object | `verify` (preserved), `backup` (rejected) | exit 1 |
| Lock held, IO error, unsupported rename | any | exit 2 |
| Unknown outcome after a crash | rerun `verify` | may yield a second acquisition on retry |
| Failed stage left behind | reported, never swept | exit 2 or warning |
| Interrupted backup | no manifest published | rerun completes |
| Non-absent restore target | `restore` | exit 2 |

## Acceptance (to be run after implementation; none claimed now)

- 100 synthetic mixed files: Korean names, spaces, long paths, duplicates, empty and locked files; explicit errors.
- Interrupt each publication stage; rerun safely; check receipt-per-acquisition and lock exclusion (concurrent capture and backup).
- Korean benchmark: names, spaced and unspaced phrases, particles, two-character queries, expected versus actual hits, extraction failures.
- Tampering blocks `open` and fails `verify`; missing, corrupt, orphan reported.
- Backup then restore to an absent path verifies all hashes; a Drive-synced backup folder and link-count-zero warning; mid-way abort leaves no partial manifest; restore refuses an existing target.
- Platforms: Windows and Ubuntu CI offline; the application does no network operation.

## Later

MCP (read-only, owner-marked items), web capture, email and messenger import, other-device inbox, OCR, evidence tier (custody, TSA), optional backup encryption.

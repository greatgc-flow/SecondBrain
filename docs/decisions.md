# Restart decisions

Status: accepted for the proposed v0.1; implementation is not asserted. Phase: DESIGN_REVIEW.
Scope authority: the owner decision of 2026-10-12. The former record `sb_plan_v21.md` is absent and its hash UNKNOWN (see [collaboration.md](collaboration.md)); the owner's current broad permission to improve earlier decisions is accepted.
Binding contract text is [design.md](design.md) and [schemas/](schemas/). Where an older sentence conflicts with a later decision (0009-0017), the later decision wins; superseded wording has been removed from this file. Requirements and evidence are in [requirements.md](requirements.md).

## 0001 — Restart and legacy freeze

Decision: restart with the simple v0.1 contract in [design.md](design.md). The earlier R7-R13 line is frozen reference material (`legacy-r13-final`). Reuse old test cases only. This phase is documentation only: no code, file moves or commits.

## 0002 — Local NTFS root outside sync folders

Decision: the active Windows root lives on unsynced local NTFS outside cloud sync folders; known synced roots are refused with a warning that discloses detection limits. Only the backup root may be cloud-synced. On Ubuntu an explicit `--root` is required on an unsynced local filesystem with the required OS locking and atomic no-replace support; otherwise the command fails with exit 2 `unsupported_platform`.

## 0003 — One user-managed backup folder

Decision: one append-only mirror folder; no backup engine, rclone, cloud API or encryption. restic and Kopia were considered and rejected. Files are plain and NOT encrypted. Never delete backup files. Details are in 0010, 0012 and 0009.

## 0004 — FTS5 lexical search first

Decision: SQLite FTS5 `unicode61` over names, receipt context, UTF-8 text/Markdown and text-based PDF (`pypdf`); queries and names NFC-normalized. Query handling, limits, fingerprinting and extraction bounds are in 0013. Korean benchmark results and limits are recorded; OCR and morphological analysis are out of scope.

## 0005 — Plain files are the source of truth

Decision: objects, receipts and configuration are authoritative; `cache/index.db` and open copies are derived. A missing, stale or corrupt index is rebuilt from plain files (failure exits 2). Publication is governed by 0010.

## 0006 — Record acquisition context at first capture

Decision: six-field receipt (id, sha256, original_name, source_path, zoned collected_at, tool_version) in `receipts/v1/`, schema [receipt.v1](schemas/receipt.v1.schema.json). Dedupe bytes, never acquisition events. These are limited local context, not authorship or custody. ID format is 0011.

## 0007 — CLI name and default root

Decision: executable `sb`; default root `D:\SecondBrain`; global `--root PATH` and `--json`; exactly capture, find, open, verify, backup, restore. Exit and envelope rules are 0014.

## 0008 — Deferred integration and legal specifics

Decision: defer MCP, the evidence tier, TSA selection and Korean legal specifics. No authenticity or admissibility claim. `sb_law.md` is non-authoritative discussion.

## 0009 — Restore target must be absent; staged and committed

Decision: `restore --to` must not exist (the "empty directory" allowance is withdrawn: Windows cannot rename onto an existing directory, remove-then-rename races, and a half-restored root could look valid).
Restore accesses only its backup input, the destination parent and its owned staging; it never initializes the global active root. It validates the manifest, schema, hashes and receipt/object set equality, restores the sole `configs/<sha256>.json` entry as staging `config.json` with exact bytes, rebuilds the index, verifies in staging, then activates by atomic no-replace rename (Linux `renameat2(RENAME_NOREPLACE)` or tested equivalent; Windows refusing rename; no check-then-replace; unsupported exits 2). The exclusively owned staging directory is retained on failure.
Successful activation is the commit point: a crash afterward may leave a complete destination without a reported success; a rerun refuses it and the tool never removes or replaces it automatically.

## 0010 — Immutable publication, locks and cleanup

Decision: stage complete bytes, flush, then atomic no-replace publish to the final name; raw `O_EXCL` into the final name is withdrawn (a crash leaves a visible partial file). Objects precede receipts; an existing object is hash-verified and reused; orphans are preserved and reported (`verify` exit 1, `backup` rejects).
Cleanup removes only staging files this command created, and only with retained ownership and identity evidence that the current path still names the created file; a matching name, a lock or "own open handle" alone is insufficient. Old temp files are never swept; failed stages are retained and reported.
Locks: persistent, never unlinked `writer.lock` with a nonblocking OS-released lock; no PID or age stale breaking (reversed: PID reuse and clock guesses can break a live writer). Reads (`find`, `open`, `verify`) take the lock for a coherent view. Every other data command initializes its active root under that lock. An unknown outcome after a crash may yield a new acquisition on retry; exactly-once is not claimed.

## 0011 — Lowercase acquisition IDs

Decision: `cap-<yyyymmdd>t<hhmmss>z-<hash8>`, UTC, lowercase; same-second collisions add `-2`, `-3` (canonical integers ≥ 2) by retrying the no-replace receipt publish; no persistent counter or scan. Receipt filename equals the id. Reason: NTFS is case-insensitive, so mixed-case IDs could alias.

## 0012 — Backup tree, manifest, transaction and recovery

Decision: tree `objects/ab/<sha256>`, `receipts/v1/<id>.json`, `configs/<sha256>.json`, `manifests/<yyyymmdd>t<hhmmss>z[-N].json`; schema [manifest.v1](schemas/manifest.v1.schema.json) with exactly one config entry, object set equal to receipt references, strict JSON and path semantics.
Manifest names: valid UTC timestamp equal to the UTC portion of `created_utc`, optional canonical suffix N ≥ 2 (unsuffixed sorts as 1); publication retries suffixes numerically. Unexpected entries in `manifests/`, including malformed or mismatched names, are integrity errors (exit 1); only defined coordination files and the command's own retained staging are excluded.
Transaction: validate the explicit candidate destination without mutation; acquire the destination lock then the source lock; read the configuration and derive the effective snapshot under those locks, revalidating a configured destination (mismatch exits 2); verify every copy including reuse; publish the manifest last; persist the local config; then release both locks. A final config save failure exits 2, retains the completed backup result with a `config_persist_failed` error, and states that a complete local backup exists. A valid local backup does NOT confirm cloud sync.
The newest manifest is chosen by parsed timestamp then numeric suffix; a corrupt newest manifest exits 1 with no fallback. There is no `--manifest` flag; recovery builds an isolated mirror of the byte-exact selected manifest and its payloads, leaving the original untouched.

## 0013 — Path safety, source coherence, cloud files and search

Decision: reject overlapping source/root/backup/restore paths and special files. Reject actual redirects: symlinks, junctions, mount-point or other redirecting reparse tags and linked directories. Hydrated NTFS cloud-tag regular files are accepted with ordinary opened-file semantics for **both** capture sources and backup inputs; offline or unavailable bytes exit 2. This is not a blanket reparse rejection. The active root must still be unsynced: local NTFS on Windows, or an unsynced local filesystem with the required locking and atomic no-replace support on Ubuntu (else exit 2 `unsupported_platform`). Unsafe working names (separators, control characters, Windows device names, ADS, trailing dot or space) are rejected or replaced; the receipt keeps `original_name` exactly.
Source coherence: read through one opened regular-file handle, compare its identity, size and mtime before and after, hash the staged bytes, and confirm the pathname still names that file before publication. This detects ordinary mutation only; no snapshot or hostile-TOCTOU claim. `nlink == 0` warns; unavailable bytes exit 2; real provider drills are NOT_VERIFIED.
Search: NFC literal tokens with escaped quotes, joined by AND, no raw FTS operators; a query without searchable tokens returns zero results; deterministic order; default limit 100 with a `search_truncated` warning (no new flag). The index fingerprint covers a deterministic sequence of receipt paths and byte digests, assuming immutable objects; rebuild goes to a separate database and is published safely under the lock, with failure exiting 2. Extraction limits (32 MiB input, 4 MiB text, 10 s, 256 MiB) are initial assumptions, not benchmark proof; if they cannot be enforced, extraction is skipped with a warning and name/context search stays. Capture is unrestricted.
`open` always writes a fresh unique working copy, hash-verifying the object before and the copy after copying (reversed: overwriting would destroy user edits).

## 0014 — Envelope, warnings and exit codes

Decision: `--json` emits `{"status":"ok"|"error","results":[],"errors":[]}`; `ok` requires zero errors. Shapes, error codes and warning codes are defined in [cli-output.v1](schemas/cli-output.v1.schema.json) (per-command result `$defs` authoritative; this file does not duplicate the lists). Every result type, including backup and restore, carries `warnings[]`; `verify` yields one singleton summary `{receipts, objects, missing, corrupt, orphan, invalid, warnings}`. Human diagnostics use stderr; under `--json`, warnings are structured per result and stdout holds only the JSON object.
Exit precedence 2 > 1 > 0: missing, corrupt, orphan and schema problems exit 1; usage, lock, IO, source-change, unsafe-path, config-persist and unsupported-platform errors exit 2. Folder capture is recursive, sorted and partial; any failed item forces exit 2 over individual exit 1; an empty folder exits 0.

## 0015 — Versioning and first-run behaviour

Decision: installed version is `0.0.1`; the v0.1 target requires `secondbrain.__version__` and build metadata to agree (future packaging gate, no code edit now). `sb --help` initializes nothing. Default Windows root `D:\SecondBrain` on unsynced local NTFS; Ubuntu needs an explicit `--root` on an unsynced local filesystem with the required OS locking and atomic no-replace support, else exit 2 `unsupported_platform`. First-run initialization follows 0009 and 0010.

## 0016 — Lifecycle applicability and evidence discipline

Decision: apply the VerySimpleGuide (pin `32c5e1f1258418d0324908f338c646e9602b6716`, Standard 1.7.0) proportionately: per-control applicability, 12 stage decisions and 10 concern decisions are recorded in [requirements.md](requirements.md), not 120 cells. A design artifact may be ready while real operational verification (real cloud, OS and Python 3.11-3.13 acceptance) stays NOT_VERIFIED; those remain release gates and are never pre-marked PASS. Planned test names are not passed tests.

## 0017 — Build / buy / reuse / do nothing

Decision: build a small local CLI. Do nothing leaves originals without acquisition context; buy or reuse (a backup engine, restic/Kopia, a document manager, a framework) adds dependencies, credentials or a daemon the owner rejected for v0.1. Plain files plus a rebuildable index are the minimum that meets the recovery and inspection need. Retire/export is plain-file copy of the root or backup; the tool never deletes automatically.

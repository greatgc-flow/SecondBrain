# SecondBrain Status

**Release v0.1.1 (2026-10-17)** fixes `Path.is_file(follow_symlinks=)` (Python 3.13+ only) in backup, found by the first full CI matrix; adds docs/USAGE.md. **Release v0.1.0 (2026-10-17).** M1 shipped as a GitHub release (wheel + sdist); not published to PyPI. Open backlog: see "Deferred" below.

**Checkpoint 2026-10-13 (M1 done).** All five steps of milestone M1 (S1 through S5) have been implemented, hardened, and verified with an end-to-end acceptance suite.

## Milestone M1 Done Criteria Checklist

All items below pass automated test suites on both Windows and Linux:

### S1: `sb capture`
- [x] Content-addressed SHA-256 object storage under canonical 2-character hex prefixes (`objects/ab/<sha256>`).
- [x] Immutable versioned receipts with 6 standard fields (`receipts/v1/<id>.json`).
- [x] Byte deduplication: identical payloads share one object while each acquisition receives a unique receipt.
- [x] Atomic publish: write to staged temporary file on target volume, flush, fsync, and atomic rename.
- [x] Interruption recovery: partial writes and process crashes leave no corrupt objects; re-runs converge without duplicate objects.
- [x] Windows file-sharing retry: retry loop with backoff before failing closed on sharing violations.

### S2: `sb verify` & `sb open`
- [x] Point-in-time cryptographic integrity check recalculating SHA-256 digests for referenced objects and validating receipt structure, schema, and ID-to-hash consistency (receipts are not cryptographically hashed in the live store; valid in-schema edits to unhashed fields such as source_path or collected_at are undetected).
- [x] Accurate categorization and reporting of missing, corrupt, and orphan files.
- [x] Standardized exit code contract: `0` = OK, `1` = integrity failure, `2` = usage/IO error.
- [x] Tamper detection: object payload alterations, corrupt receipt JSON, schema violations, and receipt ID/hash mismatches are caught immediately (valid metadata edits within receipt schema remain undetected).
- [x] Disposable read-only working copies staged in `cache/open/<id>/<name>` with hash check prior to opening.
- [x] Headless `--print-path` flag to output verified file paths without spawning interactive viewers.

### S3: `sb find`
- [x] Derived, rebuildable SQLite FTS5 index located at `<root>/cache/index.db`.
- [x] Text extraction for `.txt`, `.md`, text PDFs via `pypdf`, `.eml`, and `.html`.
- [x] Safety boundaries: text input cap (32 MiB), PDF cap (64 MiB, 1000 pages, 30s worker timeout), output text cap (2 MiB).
- [x] Korean language support: Unicode NFC normalization, SQLite trigram tokenization, and automatic `< 3` character SQL `LIKE` fallback.
- [x] Link and reparse point rejection: index and cache operations strictly prohibit following symlinks or junctions.
- [x] Atomic re-indexing via `sb find --reindex`.

### S4: `sb backup` & `sb restore`
- [x] Append-only mirror to a single user-managed backup directory.
- [x] Cloud-synced backup root support: path-keyword detection emits informational warnings (intended use per ADR 0003).
- [x] Virtual file system tolerance: `st_nlink == 0` (e.g. Google Drive FS) generates warnings without aborting.
- [x] Hardlink alias rejection (`st_nlink > 1` on backup payload files fails closed).
- [x] Atomic roster snapshot captured under source `WriterLock`.
- [x] Dated MANIFEST v1 published LAST atomically; an interrupted backup never leaves an incomplete manifest.
- [x] Safe restore into an empty target directory with full manifest and payload verification and automatic index rebuild.
- [x] Restoration tolerance for unreferenced (orphan) objects in source backups.

### S5: Acceptance Suite (`tests/test_acceptance_m1.py`)
- [x] Suite is marker-free and completes well under the 90-second threshold (~28 seconds).
- [x] Drives the real CLI via subprocess (`python -m secondbrain ... --json`).
- [x] Comprehensive test dataset: ~100 mixed files covering Korean names, spaces, long paths (>200 chars), byte duplicates, empty files, Windows locked/open-for-write files, and unreadable files.
- [x] Full lifecycle tested: `capture` -> `verify` -> `find` (Korean + English) -> `open` -> `backup` -> wipe data root -> `restore` -> `verify` -> `find` again, asserting identical hashes and receipt counts.
- [x] Process interruption and recovery: simulated terminations at multiple stages (`mid_write`, `after_staging`, `after_object` for capture; `mid_objects`, `mid_receipts`, `before_manifest` for backup) and real subprocess termination mid-write; re-runs converge with zero corruption, no duplicate objects, and no data loss.
- [x] Cloud-synced backup folder and simulated `st_nlink == 0` warnings verified.

---

## Owner Decisions on Record
- Executable name `sb`, default root `D:\SecondBrain` (configurable with `--root`).
- Append-only mirror to one user-managed folder; no backup engine, cloud APIs, or encryption in v0.1.
- AI access deferred; future access will be restricted to items marked AI-visible by the owner.
- Legal specifics (timestamp authority, legal exhibit formats) to be reviewed with legal counsel prior to any evidence tier.

## Deferred (Not in v0.1)
- Read-only MCP server.
- Web capture (SingleFile).
- Email / messenger import.
- Cross-device inbox.
- OCR / speech transcription.
- Legal evidence tier and sealing.

## Handoff 2026-10-17 (v0.1.0 released)

- Released v0.1.0 on GitHub (wheel + sdist); not on PyPI. Verified only on Windows / Python 3.14.8 (183 tests, `python scripts/verify.py`). Linux and Python 3.11-3.13 are NOT_VERIFIED because the private-repo Actions allowance is exhausted (see `ci-policy.md`); run the `full_matrix=true` dispatch once the allowance resets and record the run URL.
- Repo cleaned: only `main` remains (local and remote). Legacy R7-R13 history is kept at tag `legacy-r13-final` and `archive/20261016/dev/r13l-snapshot-consistency-20261010`.
- Backlog: Linux/Py3.11-3.13 matrix run; M2 scope (see Deferred above) needs an owner decision; no PyPI publication authorized.

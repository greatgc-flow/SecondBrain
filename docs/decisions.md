# Restart decisions

Status: accepted for the proposed v0.1; implementation is not asserted.
Scope authority: owner decision, 2026-10-12, recorded in `sb_plan_v21.md`.
Earlier designs/votes inform the record; v2.1 supersedes their broader scope.

## 0001 — Restart and legacy freeze

Decision: restart with the very simple v0.1 contract in [design.md](design.md).
The earlier R7–R13 line is frozen reference material identified by `legacy-r13-final`.
Reuse old test cases only; the old implementation does not define restart behaviour.
M0a changes documentation only: no code, file moves or commit.
Any later relocation of the old tree is outside this step.

## 0002 — Local NTFS root outside sync folders

Decision: the active Windows root lives on local NTFS outside cloud sync folders.
Refuse known synced roots with an explanatory warning; disclose detection limits.
Reason: publication and the derived SQLite index need a stable local working root.
Only the backup root may be cloud-synced; Ubuntu CI uses a local test filesystem.

## 0003 — One user-managed backup folder

Decision: v0.1 uses one append-only mirror folder managed by the owner.
No backup engine, rclone, cloud API or encryption is included.
restic and Kopia were considered and rejected for v0.1: the owner wants one folder to manage.
Originals are content-addressed, so a mirror is incremental by nature.
Verify hashes on write and publish a dated manifest last; never delete backup files.
The owner's Drive/OneDrive client handles sync; backups are readable plain files.

## 0004 — FTS5 lexical search first

Decision: SQLite FTS5 searches names, receipt context and supported extracted text.
Start with `unicode61`, UTF-8 text/Markdown and text-based PDF extraction using `pypdf`.
Record Korean benchmark results and spacing, particle and short-query limits.
Reason: lexical retrieval tests first value without vectors or a daemon.
Extraction failures remain visible; OCR and morphological analysis are outside v0.1.

## 0005 — Plain files are the source of truth

Decision: objects, versioned receipts and configuration are authoritative plain files.
`cache/index.db` and open working copies are derived and disposable.
Missing/stale indexes rebuild automatically; restore verifies files before success.
Reason: recovery and inspection must not depend on a surviving database.

## 0006 — Record acquisition context at first capture

Decision: record ID, SHA-256, original name, source path, zoned collection time and tool version.
Version the six-field receipt through the `receipts/v1/` namespace.
Deduplicate original bytes, never distinct acquisition events.
Reason: a later evidence tier cannot recreate acquisition context that was never recorded.
These observations are limited local context, not verified authorship or full custody history.

## 0007 — CLI name and default root

Decision: the executable is `sb`; the default root is `D:\SecondBrain`.
Allow global `--root PATH` while retaining local-root restrictions.
Expose exactly capture, find, open, verify, backup and restore, all with `--json`.
Reason: owner choice and a one-screen interface keep v0.1 understandable.

## 0008 — Deferred integration and legal specifics

Decision: defer MCP, the evidence tier, TSA selection and Korean legal specifics.
The owner controls future AI visibility/evidence scope; owner plus lawyer resolve legal requirements.
No legal-weight default or authenticity/admissibility claim is made.
`sb_law.md` is preliminary, non-authoritative discussion, not a legal specification.
Reason: the owner explicitly chose simple capture/search/recovery first.
Other deferred items appear only as one-line entries in [design.md](design.md).

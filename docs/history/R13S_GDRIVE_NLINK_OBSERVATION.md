# R13-S — Google Drive zero-link observation and policy A (NOT acceptance)

## Purpose

Record the 2026-10-11 synthetic-only observation and pin the decision after
cx + ag consultation: **KEEP** the R13-D `st_nlink != 1` guard unchanged.
Google Drive for desktop paths are an **unsupported DIRECT source** for
verification/restore; operators stage a snapshot copy to a local disk first.
This partial observation closes no operational acceptance row. Row 14 stays
`NOT_RUN`; R13 operational gate remains **NO-GO**.

## Environment

| Field | Observed |
|---|---|
| Date | 2026-10-11 |
| Host | Windows 11, Python 3.14 |
| Provider / path | Google Drive for desktop, G: (`내 드라이브`) |
| Scope | Synthetic-only folder; same PC, same account |
| Independent custody / real remote sync | UNVERIFIED |

## Commands

CLI forms below illustrate the reported operations using sanitized placeholder
paths and the independently noted manifest-body digest; literal original
commands, paths and digest were not supplied. DIRECT verification and pinned
restore:

```powershell
python profiles/secondbrain/brain.py backup verify <G-snapshot> --json
python profiles/secondbrain/brain.py backup restore <G-snapshot> --to-root <new-local-root> --expect-manifest-sha256 <DIGEST> --json
```

After copying the snapshot from G: to a local disk, preserving its files:

```powershell
python profiles/secondbrain/brain.py backup verify <staged-local-snapshot> --expect-manifest-sha256 <DIGEST> --json
python profiles/secondbrain/brain.py backup restore <staged-local-snapshot> --to-root <new-local-root> --expect-manifest-sha256 <DIGEST> --json
python profiles/secondbrain/brain.py recovery status --root <new-local-root> --json
```

Metadata probes inspected `stat()` / `lstat()`, `st_nlink`, Windows attributes
and `resolve()`, including G:\ root, and polled attribute stability. The
conflict probe wrote the same new name twice back-to-back from two local paths.

## Observations

| Case | Result |
|---|---|
| Link counts | `st_nlink == 0` for every observed file and directory, including G:\ root |
| Windows attributes | Directories `0x10`, files `0x80`; no reparse/offline/recall/sparse flags |
| Path metadata | `resolve()` stable; `lstat()` works |
| DIRECT G: verify / pinned restore | `UNSAFE_PATH`, exit 3 |
| DIRECT G: after rename / delete / one-byte change | `UNSAFE_PATH`, exit 3; path guard fires first, so these are NOT corruption-specific detections |
| Attribute stability polling | Attributes stable within approximately 31 s; metadata only, remote sync lag NOT verified |
| Same-name conflict probe | One file, no duplicate name |
| G: snapshot copied to local disk | Copy 0.68 s |
| Staged local verify / pinned restore | Both PASS; restore program time 0.72 s (NOT disaster RTO) |
| Restored recovery state | `RECOVERED_READ_ONLY`, `writer_active` false |
| Manual Explorer “Online only” offline step | NOT_RUN; needs an operator in Explorer |
| Independent custody / real remote sync | UNVERIFIED; same PC, same account |

## What this does and does NOT prove

The observed Google Drive metadata is incompatible with the current single-link
requirement, even without visible unsafe Windows attributes. Staging the copy
to local disk allowed verification and pinned restore of this synthetic
snapshot, with the restored writer held read-only.

This does **not** prove independent custody, real remote synchronization,
remote durability, offline/placeholder behavior, multi-client conflict handling,
or disaster RPO/RTO. The two-path same-name probe is not a simultaneous-client
drill. The direct negative scenarios demonstrate path rejection before
corruption checks. Attribute stability is not a remote-sync completion signal.
Row 14 therefore stays `NOT_RUN` / **NO-GO**.

## Decision and rationale

**Policy A, cx + ag consulted:** keep `st_nlink != 1` unchanged. The guard
stops a snapshot file sharing storage with a mutable outside name; matching
hashes alone cannot exclude that alias. A reported link count of zero gives
no evidence of a single link, so accepting zero would weaken the guard.

Google Drive for desktop is unsupported as a DIRECT snapshot source.
Operators must stage a copy to local disk, then verify and restore using the
independently retained expected manifest digest. Options C/D were rejected
as additional complexity without replacing the guard's protection. No runtime
guard change is warranted; the zero-link regression is expected GREEN against
the current code.

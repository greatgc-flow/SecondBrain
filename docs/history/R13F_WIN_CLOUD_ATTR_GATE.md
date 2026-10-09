# R13-F developer gate — Windows offline/reparse/recall metadata fail-closed

**Source-only prototype, no production claims.** Version `0.0.0`,
formal product release **NO-GO**; R13 independent operational issue
[#11](https://github.com/greatgc-flow/SecondBrain/issues/11) stays OPEN.

## Scope and mechanism

Windows files-on-demand and other cloud-sync/storage virtualized entries
can appear as ordinary directory entries yet fetching their data may
trigger unwanted hydration or network access. Pure byte-digest,
symlink, junction and hardlink checks do not identify all cases.

Add one shared metadata predicate
`brain_core.verify._unsafe_windows_attributes` for four Win32 flags
on the `st_file_attributes` returned by Python's `Path.lstat` or
`os.fstat`:

| Windows flag | Value | Why refused |
|---|---:|---|
| `FILE_ATTRIBUTE_REPARSE_POINT` | `0x00000400` | may be a reparse/cloud link |
| `FILE_ATTRIBUTE_OFFLINE` | `0x00001000` | data not immediately available |
| `FILE_ATTRIBUTE_RECALL_ON_OPEN` | `0x00040000` | opening may fetch remote representation |
| `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` | `0x00400000` | read may retrieve remote bytes |

Checks apply before opening Capture source path components or opened
file descriptor; before inspecting saved Capture/Object file leaves;
during source/snapshot/restored inventory and backup root/ancestor
validation; before hashing a snapshot data leaf or accepting a restore
hold marker. Ordinary local files remain readable and content-address
dedup remains unaffected. **Never auto-hydrate or change attributes.**

These bits are documented in:
- [Microsoft WinNT.h file attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
- [Microsoft MS-FSCC file attributes](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/ca28ec38-f155-4768-81d6-4bfeb8586fc9)
- [Python stat module Windows st_file_attributes](https://docs.python.org/3.12/library/stat.html)

**Important:** `RECALL_ON_OPEN` is a directory enumeration attribute
and may not be exposed by Python's stat calls. An **absent bit does not
certify that cloud data is hydrated**. This slice cannot assert no
network requests under hostile races or unsupported provider APIs.

## RED → GREEN traceability

- [Implementation PR #22](https://github.com/greatgc-flow/SecondBrain/pull/22).
- RED test file: `profiles/secondbrain/tests/test_cloud_attributes_r13f_tdd.py`.
  Inject *genuine bit values* into synthetic stat objects on BOTH
  Ubuntu and Windows CI; no external accounts, credential access,
  live placeholders or production evidence are used.
- Test oracles: all four bits on Capture source, backup manifest,
  snapshot root, snapshot data directory, recovered hold marker
  and open file-descriptor attributes. Additional direct digest tests
  inject all four flags into a leaf's `lstat` and fail the test if
  `os.open` is called, proving known metadata flags are rejected **before
  file open**; local files still work.
- Implementation: `brain_core/verify.py` provides shared predicate;
  `capture.py`, `backup.py`, `writer.py`, `recovery.py`
  use it at their existing boundaries.
- Record failing baseline, exact green PR head, post-merge main SHAs
  and 6-job cross-runner CI **only after observed success**.

## Unresolved operational acceptance

Real Windows NTFS offline/reparse test media and genuine
OneDrive/Google Drive files-on-demand (online/offline, sync conflict,
placeholder rehydration, multiple clients and deletion/reappearance)
**are not tested by attribute-injection CI**. The separately governed
offsite copy, loss of primary, independent checkpoint and RPO/RTO,
reviewer, power loss, and distributed writer fencing are also
unverified. Follow the
[operator drill](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md) and
[R13 issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11).

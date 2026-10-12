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
- **RED baseline**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38004392695
  SHA `3b46ccd637a8b1e06313d4792de142d0ca750168`.
  Expected FAIL: **Windows 24 failed/187 passed**; Ubuntu
  **24 failed/185 passed, 2 Windows-only skipped**. Baseline incorrectly
  read/opened flagged file and accepted metadata with intact byte hashes.
- **Additional RED pre-open test**, commit
  `4cd473d2a734d90be0e26157e6344b79f64c973c`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38004901405
  Expected FAIL: **Windows 4 failed/211 passed**; Ubuntu
  **4 failed/209 passed, 2 Windows-only skipped**. Direct leaf
  digest was still calling `os.open` before checking cloud attribute
  metadata. Implementation fixed by inspecting `Path.lstat` first.
- **Final PR #22 tip**,
  `542b3689b24562f8cee5cd160667f37f2c6f51da`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38004939328
  **SUCCESS all 6 jobs**: Windows **215 passed in 145.66s**;
  Ubuntu **213 passed/2 Windows-only skipped in 32.45s**;
  both independent GitHub jobs consumed and restored the opposite-OS
  synthetic snapshot. Python 3.12 and actual pinned `rfc8785==0.1.4`.
- **PR #22 implementation squash merged to main**:
  SHA `05651eb4bcd94e60fb4d4c36b08578ff0fd5d372`,
  https://github.com/greatgc-flow/SecondBrain/commit/05651eb4bcd94e60fb4d4c36b08578ff0fd5d372
- **Exact post-implementation-merge main CI**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38005318554
  **SUCCESS all 6 jobs**, Windows **215 passed in 216.10s**;
  Ubuntu **213 passed, 2 Windows-only skipped in 30.91s**;
  both opposite-OS transfer/restore consumers passed. The run head
  SHA equals `05651eb4bcd94e60fb4d4c36b08578ff0fd5d372`.
- **R13-F synthetic Win32 attribute-software gate PASS** for detectable
  bits in test doubles on Windows and Linux. This is NOT validation
  of real OneDrive/Google Drive placeholders or avoiding cloud hydration
  under every provider, parent-dir swap, or race.
  The R13 operational issue #11 remains **OPEN/NO-GO** and formal
  product release 0.0.0 remains **NO-GO**. This record closure is
  documentation only and does not modify the tested implementation.

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

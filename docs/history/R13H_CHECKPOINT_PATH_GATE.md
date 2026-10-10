# R13-H TDD developer gate — detached R10 checkpoint path safety

**Private source-only prototype.** R13 operational issue [#11](https://github.com/greatgc-flow/SecondBrain/issues/11) stays **OPEN / NO-GO** and formal release `0.0.0` stays **NO-GO**.

## Narrow gap and correction

R10's `verify_checkpoint(root, supplied_external_file)` previously checked symlinks and root containment, then read externally supplied canonical JSON. It did **not** reject (1) hardlinks outside the inspected filesystem tree, (2) Windows OFFLINE / REPARSE_POINT / RECALL_ON_OPEN / RECALL_ON_DATA_ACCESS metadata, (3) Windows directory junction ancestors, or (4) replacement of the same pathname with a separate, byte-identical inode after parsing. R13-G synthetic recovery depends on this witness input.

Minimal reuse of existing primitives in `profiles/secondbrain/brain_core/checkpoint.py`:

- New metadata-only `_external_leaf_identity` visits witness leaf **and ancestors via `lstat` before `Path.resolve` or `read_bytes`**, rejects links, junctions, visible unsafe Windows file attributes and leaf `st_nlink != 1`.
- Retain lexical and canonical containment refusal for paths inside source root, and normal RFC8785 JSON body/ledger prefix/digest checks.
- Compare witness leaf `st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns, st_nlink` **before and after** canonical parsing/byte read; changed name/inode fails with `UNSAFE_CHECKPOINT_PATH` even if contents match exactly.
- The `synthetic_offline_drill.run_drill` R13-G caller converts invalid witness failure to `CHECKPOINT_INVALID` before ever creating a fresh destination. No new writer, storage/backup engine, or cloud SDK.

## Tests, evidence and trace

- [PR #26](https://github.com/greatgc-flow/SecondBrain/pull/26)
- RED test file `profiles/secondbrain/tests/test_checkpoint_path_safety_r13h_tdd.py`: real hardlink alias, simulated junction ancestor on each platform, injected authentic Win32 attribute bits on witness leaf and parent (8 parameterized cases), byte-identical `os.replace` swap after parse and clean valid R13-G restore. Each invalid witness case must fail without reading flagged JSON or creating target.
- Intentional RED SHA `6bfdd2c3f5a09a0ad45c29dcc420a9369d08e65f`, first run [Actions #38018587897](https://github.com/greatgc-flow/SecondBrain/actions/runs/38018587897).
- Initial implementation SHA `71e58395886c327955c50b99816029b33561caae` and subsequent exact Windows/Ubuntu six-job tests: document observed outcomes after CI finishes, not before.

## Important limits and operator acceptance

File attributes may be unavailable on some Windows/provider APIs, and inspecting metadata is **not proof** that a cloud placeholder cannot hydrate in every situation. Before/after sampling is not atomic path-handle security and does not defeat hostile parent-directory ABA swaps. A supplied external file, even valid and safely opened, **is not proof of independent retention, provenance or trusted time**.

Real offsite/account/media custody, separate witness control, observed source-loss recovery, Windows/OneDrive/Google Drive offline and conflict tests, external distributed writer fencing, measured RPO/RTO and independent reviewer are **NOT RUN / NO-GO** under the [17-item operator evidence record](../runbooks/R13_OPERATOR_EVIDENCE_RECORD_TEMPLATE.md). No private evidence, credentials, real backups or ZIP committed.

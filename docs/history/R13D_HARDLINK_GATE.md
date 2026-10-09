# R13-D development gate — fail-closed filesystem hardlinks

**Scope:** disposable synthetic files on Linux and Windows NTFS.
**Release:** 0.0.0, formal product release **NO-GO**. Full operator-observed
R13 issue #11 remains OPEN/NO-GO.

## Issue

R12/13-C already reject symlinks and Windows directory junctions, but a
same-volume filesystem **hardlink** to a regular file can reference an inode
also accessible **outside** the source/snapshot/restored root. Its hash,
length and contents match perfectly: SHA-256 byte-consistency tests alone
cannot detect the alias, and an outside writer could subsequently change
both names. Hardlinks do not require symlink support.

## Minimal fix / no new engines

- Keep the existing R7–R13-C closure and file inventory. In the canonical
  `brain_core/backup.py:_walk_files`, reject any regular file with
  `st_nlink != 1` before accepting a source, snapshot or restored tree.
  This applies to immutable R7–R11 data, R12 `manifest.json` and
  `.complete`, and R13 `recovery-hold.json` /
  `recovery-sentinel.json`.
- Existing `brain_core/verify.py:_safe_regular_file` and `_digest_fd`
  also refuse a hardlink, including read-only inspection of R13 hold
  markers. A hardlinked marker must never be reported as a safe hold.
- Backup `_copy_file` repeats a source file link-count check before and
  after copying and checks destination parent link/junction ancestry.
  This is a **best-effort static and before/after guard**; it is not an
  atomic capability-safe directory handle or an openat2/Windows reparse
  security primitive.
- Stable duplicate **content** (distinct files and one content-addressed
  R11 object) remains supported: two files with equal SHA-256 but each
  `st_nlink == 1` are NOT an alias.

## Acceptance / traceability

- PR #18: https://github.com/greatgc-flow/SecondBrain/pull/18
- RED tests commit `4b104f98ced9fdc61d273df65b250ac838db7493`.
  Run (verify exact outcome from Actions):
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37999820093
- Implementation: `profiles/secondbrain/brain_core/backup.py` and
  `brain_core/verify.py`.
- Tests: `profiles/secondbrain/tests/test_hardlink_faults_r13d_tdd.py`.
  Real `os.link` attempts with unchanged hashes on source Capture,
  Writer metadata, snapshot payload/manifest/completion marker,
  restored root payload, R13 hold/sentinel, CLI error codes and
  successful valid R11 content dedup.
- Candidate, final PR head and final merged-main 6-job Ubuntu↔Windows
  evidence: append **only after observed real GitHub Actions results**.

## Limitations / NO-GO

Link-count checks do not stop a privileged attacker from swapping a
directory between inspection and opening or changing file contents
without changing link count. They also cannot prove that an arbitrary
filesystem reports reliable hardlink counts. No real cloud placeholder,
actual OneDrive/Drive sync collision, cross-machine writer fencing,
external independent custody, hardware power loss, or operator-observed
RPO/RTO test is included. Real-world site gates stay **NO-GO**.

SSOT: [Roadmap](../roadmap/S1_NEXT.md) ·
[Operational drill](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md) ·
[R13 issue](https://github.com/greatgc-flow/SecondBrain/issues/11).

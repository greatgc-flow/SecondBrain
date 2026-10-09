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
  `recovery-sentinel.json` (after temporary Writer staging aliases are dropped).
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
- RED result:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37999820093
  Ubuntu **9 failed, 169 passed, 2 Windows-only skipped**. The
  aliases had matching hashes yet passed original R12 verification.
- Initial cross-cutting verifier change on
  https://github.com/greatgc-flow/SecondBrain/actions/runs/37999869275
  also caused an important **legitimate regression**:
  R8 Writer intentionally publishes via a *temporary staging hardlink*,
  then historically verified before removing that temporary name. The
  new verifier correctly rejected `st_nlink == 2` but thus blocked
  valid ordinary Writer publication (over 130 failures, both OS).
  **Not a spurious test:** actual Writer publication sequence needed
  a minimal fix before enabling the new rule.
- Writer code now unlinks only its own staging name after atomic
  create-if-absent publication, fsyncs the directory and THEN verifies
  the published file. It retains `finally` cleanup and never permits
  permanent two-name aliases. A new explicit test asserts the link
  count is exactly 1 at final Vault and metadata verification.
- Implementation: `profiles/secondbrain/brain_core/backup.py`,
  `brain_core/verify.py`, and the minimal
  `brain_core/writer.py` staging cleanup reorder.
- Tests: `profiles/secondbrain/tests/test_hardlink_faults_r13d_tdd.py`.
  Real `os.link` attempts with unchanged hashes on source Capture,
  Writer metadata, snapshot payload/manifest/completion marker,
  restored root payload, R13 hold/sentinel, CLI error codes and
  successful valid R11 content dedup.
- **Final PR #18 tip**:
  `9dbba5864c36f9866c84d5442eb574fe7b1c045c`.
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38000217312
  **SUCCESS all 6 jobs**: Windows **181 passed in 81.03s**;
  Ubuntu **179 passed, 2 Windows-only skipped in 22.74s**;
  both synthetic producer and opposite-OS consumer jobs succeeded.
  Actual pinned `rfc8785==0.1.4` on Python 3.12.
- **Implementation PR #18 squash merged to main**:
  `081aec31e0a55ef479cd3590df247036965f6144`.
  https://github.com/greatgc-flow/SecondBrain/commit/081aec31e0a55ef479cd3590df247036965f6144
- **Exact implementation post-merge main CI**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38000547175
  **SUCCESS all 6 jobs**, Windows **181 passed in 59.80s**;
  Ubuntu **179 passed, 2 Windows-only skipped in 26.54s**.
  Both cross-OS transfer and recovery consumers passed. Run head SHA
  exactly matches `081aec31e0a55ef479cd3590df247036965f6144`.
  Both unit jobs installed pinned real RFC8785.
- **R13-D synthetic static filesystem hardlink development gate PASS**.
  This verifies real hardlinks on GitHub-hosted Linux and Windows runners,
  not adversarial atomic race prevention or a production offsite DR drill.
  R13 operational issue #11 remains OPEN/NO-GO and product 0.0.0
  remains **NO-GO**. This documentation-only closure changes no code.

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

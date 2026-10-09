# R13-E developer gate — same-bytes source pathname replacement

**Private source-only prototype.** Synthetic CI evidence only. R13
operational acceptance issue #11 OPEN/NO-GO. Product 0.0.0 and formal
release NO-GO. No external custody, authenticated identity, cloud access
or legal acquisition claims.

## Specific fault

R12–R13-D requires a full R7–R11 closure, SHA256 file consistency and
unique regular file link count. Its `_copy_source` checks an **opened
file descriptor**, including size/hash/stability. A separate actor can
replace the file's **pathname** (directory entry) after the FD was
read/closed with a DIFFERENT ordinary, single-linked, byte-identical
file. Pre/post only `st_nlink == 1` checks do not detect the identity
drift. R12 snapshot `create` may then publish `.complete` despite
an in-flight source-path replacement; `verify` can miss a
byte-identical path substitution between hash calls.

## Minimal correction, reuse existing integrity engine

- `brain_core/backup.py:_regular_leaf_identity`: regular file and
  `st_nlink == 1` enforcement, plus immutable tuple of
  `st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns, st_nlink`.
- `_copy_file`: require exact pre/post **path leaf identity**, in
  addition to the already existing byte/hash/stable-FD source checks.
  A replacement fails with `SOURCE_CHANGED` during `create`,
  preserving an incomplete snapshot without a completion marker, or
  fails with `INCOMPLETE_RESTORE` during a quarantined restore.
- `_compare_data`: require pre/post path identity around `_digest_fd`;
  a mid-verify replacement is `SNAPSHOT_TAMPERED`.
- No new metadata format, trust authority, backup engine, cloud SDK
  or real evidence. Byte-identical dedup still works; R13-D hardlink
  checks remain active.

## Test-driven matrix

- Implementation: [PR #20](https://github.com/greatgc-flow/SecondBrain/pull/20).
- RED test commit `4be6c64e7c19c00db7b254bb952f530b5ba41045`:
  `profiles/secondbrain/tests/test_leaf_drift_r13e_tdd.py`.
- Cases: source changes to different same-content inode after copy
  during **backup create** (no `.complete`), during **restore**
  (retains hold), after a **verify digest**, during **restore preflight**
  (no target directory), plus normal success regression.
- **RED run**, commit `4be6c64e7c19c00db7b254bb952f530b5ba41045`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38002243214
  FAILED as expected: **Windows 4 failed, 182 passed**; Ubuntu **4 failed,
  180 passed, 2 Windows-only skipped**. Four intentional replacement
  oracles exposed same-byte leaf substitution acceptance.
- First **GREEN code candidate**, commit
  `43b35941f04cc3e22cec3885f7ad1bedf61fc0b1`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38002279579
  SUCCESS in all six jobs, Windows **186 passed**; Ubuntu **184 passed,
  2 Windows-only skipped**; both opposite-OS producer/consumer transfer
  and read-only restore workflows passed.
- **Final PR #20 tip**, commit
  `be25b44414a3f45a4298712d8291050886135c51`:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38002397570
  **SUCCESS ALL SIX JOBS**, Windows **186 passed in 107.08s**; Ubuntu
  **184 passed, 2 Windows-only skipped in 25.32s**; both cross-OS
  producer/consumer restore jobs succeeded with real pinned
  `rfc8785==0.1.4` on Python 3.12.
- **PR #20 squash merged to main**,
  `e51f2acb480d2fa184ebdb9caf045d355171d3fa`:
  https://github.com/greatgc-flow/SecondBrain/commit/e51f2acb480d2fa184ebdb9caf045d355171d3fa
- **Exact post-merge main CI**:
  https://github.com/greatgc-flow/SecondBrain/actions/runs/38002995890
  **SUCCESS ALL SIX JOBS**, Windows **186 passed in 101.18s**;
  Ubuntu **184 passed, 2 Windows-only skipped in 29.55s**, both
  independent-job opposite-OS synthetic restores succeeded.
  Exact run head SHA matches the above implementation main commit.
- **R13-E synthetic source-development gate PASS**. The gate validates
  sampled leaf pathname identity checks on Windows and Ubuntu,
  **NOT** a hostile concurrent parent-directory security proof.
  R13 full operational issue #11 OPEN/NO-GO; formal product release
  remains NO-GO with version 0.0.0. This closure change is docs only.

## Residual risk (NO-GO)

This is a **best-effort leaf-name before/after check**, NOT a guarantee
that a privileged attacker cannot atomically swap a parent directory,
retarget a path twice between samples (ABA), mutate a file without
observable stat change, or bypass filesystem identity semantics on
unusual storage/cloud placeholders. `st_ino` and ctime reliability
varies across filesystems. No cross-PC writer fencing, real offline
OneDrive/Google Drive state, independently governed WORM retention,
operator-observed physical loss/recovery, encryption audit or
measured RPO/RTO is certified.

Real operator drill:
[runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md) /
[issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11).

# R13-I development gate — fail-closed restored-root quarantine presence

**Product status: 0.0.0 / release NO-GO. Operational R13 issue #11 stays OPEN.**

## Narrow finding and minimal fix

R13-A placed two locally removable recovery-hold and sentinel files before restoring writer authority. The writer guard used `Path.exists() or Path.is_symlink()` to ask whether either local marker exists. False negatives from provider/ACL behavior, and a reparse/unsafe directory with missing leaves, could be mistaken for *no hold*. That is unsafe because R7–R11 mutation entrypoints use the same guard.

R13-I changes only `profiles/secondbrain/brain_core/recovery.py`: a shared metadata-only `lstat` state check of `root/90_System/writer` ancestors plus both marker leaves returns `present`, `missing` or `unsafe`. Both `present` **and** `unsafe` block local writers; `validate_recovery_hold` reports `UNSAFE_PATH` rather than converting unclear metadata into authorization. Only a genuinely missing file under ordinary safe ancestors means absence. No cloud API, privilege escalation, fallback-by-reading, silent repair, or new second locking protocol was introduced.

## RED → GREEN trace (synthetic GitHub CI, not operational proof)

- Base main was `183595ee6a4643e34a8b8a354a69a30a6c28373e`.
- **RED test commit:** `6f06626e2a52a5bdc9bd9dabafb2c3c74ae2b3a3`; first [Ubuntu run #38032501609](https://github.com/greatgc-flow/SecondBrain/actions/runs/38032501609) gave **3 failed, 241 passed, 2 skipped**. One failure was a *test fixture assertion bug*: a pre-existing CI capture directory was incorrectly assumed absent; corrected before code change.
- **Corrected RED test commit:** `d071c59570270fe7b299e350775188317bb63f37`; [run #38032560086](https://github.com/greatgc-flow/SecondBrain/actions/runs/38032560086) Ubuntu **2 failed, 242 passed, 2 skipped**. The two remaining failures specifically demonstrated the false-negative marker and Win32-reparse-parent paths.
- **Minimal fix:** `69792d0f6aad9445ff1668c10f039302d7ff3a37`; [candidate run #38032589802](https://github.com/greatgc-flow/SecondBrain/actions/runs/38032589802) Ubuntu **244 passed, 2 skipped**. Inspect Windows and subsequent final PR/main CI live before asserting two-OS completion.
- Source tests: `profiles/secondbrain/tests/test_recovery_marker_presence_r13i_tdd.py`. Cases: simulated `exists()/is_symlink()` false negative; denied `lstat` (write stays blocked); known Win32 reparse ancestor with missing markers; normal fresh writer initialization; one missing marker still blocked.
- Source-only Python 3.12 with pinned real `rfc8785==0.1.4`; CI `.github/workflows/test.yml` runs Ubuntu and Windows full synthetic suite and Ubuntu↔Windows artifact transport. No personal/production evidence or cloud credentials are used.

## Explicit non-claims and next gate

- Both local markers can be deleted by a root owner; local read-only quarantine is **not** a distributed writer lease, independently verified active writer epoch, signed record or offsite witness.
- Static `lstat`/path checks do not close malicious concurrent path-swap/ABA or a true NTFS OneDrive/Google Drive hydration race. Synthetic Win32 flag injection cannot prove real provider behavior.
- This gate cannot show independent custodian control, trusted timestamps, source-outage recovery RPO/RTO, actual media retention, physical power-loss durability, Windows ACL provider behavior, or real multi-device fencing.
- Before formal release, complete the operator-observed [independent restore runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md), including external custody and reviewer acceptance, then record the issue #11 evidence. Do not mark #11 complete on CI alone.

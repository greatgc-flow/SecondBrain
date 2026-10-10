# SecondBrain — R13-R handoff: waived simulations done, real drill pending (2026-10-10)

> Supplements [R13-L handoff](2026-10-10_R13L_TO_R13_OPERATIONS.md); re-read live `main`, issue #11 and CI first. Never roll back.

- Baseline: `main` includes PRs #34–#41 (docs + R13-N/O checkpoint export fix). Latest verified main CI: run 38060911625 (6/6).
- Code change since R13-L: `checkpoint export` always emits exact RFC 8785 bytes (no trailing newline/CRLF); `--out PATH` creates a new file outside the root (`xb`). Local suite 268 passed (py3.14, Windows).
- Evidence docs: [R13-M](../history/R13M_LOCAL_NTFS_OBSERVATION.md), [R13-N/P](../history/R13N_SAME_HOST_REHEARSAL.md), [R13-Q/R owner waiver](../history/R13Q_OWNER_WAIVER.md).
- Status: owner waived independence for same-host/`subst` drills (`WAIVED-SIM` ≠ PASS). Rows 11, 15–17 `NOT_RUN`; 13–14 `SKIPPED_BY_OWNER`. Issue #11 OPEN; release `0.0.0` **NO-GO**.
- Next (needs real resources): external USB disk → row 12 cross-volume, 03/04; second device/account → 01/03/05/11; reviewer → 17; later OneDrive/Google Drive test accounts → 13/14. A real run supersedes `WAIVED-SIM`.
- Ops notes: on Windows use cmd/bash (not PowerShell `>`) or `--out` for checkpoints; `docs/history/` is gitignored, add new files with `git add -f`; keep background shells light (a low-memory event killed two watchers).

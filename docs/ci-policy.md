# CI usage policy (private repository)

**Effective:** 2026-10-15. Private GitHub Actions included allowance is shared with other private repositories. In Oct 2026 the personal Free allowance was exhausted (account report confirmed $12.00 of discounted Private runner usage across SecondBrain, LK and Lovely; net charge $0). A new workflow cannot allocate a runner until included time resets or separately approved paid overage is available. No budget/payment change is part of this PR.

## Event-to-test contract

| Event | Trigger / cost | Tests |
|---|---|---|
| A PR into `main` modifying `src/**`, `tests/**`, `pyproject.toml`, or `.github/workflows/**` | **Automatic** one `ubuntu-latest` job with Python 3.12 | Install editable `.[dev]` and run `python -m pytest tests -q` |
| Docs-only PR | No CI run | Manual review, document/link inspection. **No green CI claim**. Branch protection check requirements must be reconsidered before requiring this path-filtered check. |
| Push to any branch including `main` | No CI run | PR validation is performed once, not duplicated on merge |
| Manual `workflow_dispatch` (default `full_matrix=false`) | One Linux Py3.12 Job | Same current test suite |
| Manual `workflow_dispatch` with `full_matrix=true` | **4 jobs**, Linux and Windows × Py3.12/3.13, at most 2 simultaneous jobs | Same current test suite on each platform; explicit pre-release/Windows-compatibility gate |

## Quality and cost guardrails

- Current M0/v0.1 tests are the **actual `tests/` directory**; frozen R7–R13 reference under `legacy/` is not an automatic regression contract. M1 and later features must add tests before asserting acceptance.
- Developers run `python -m pytest tests -q` locally on each code change; run Windows tests locally when behavior depends on NTFS, path casing, locks, junctions, file attributes, or atomic replace. Linux CI cannot prove Windows behavior.
- For milestone, branch reconciliation, filesystem safety, backup/restore or production-facing release, execute `full_matrix=true` on the specific candidate SHA and save the run URL/result. Avoid authorizing release with a skipped/manual-unrun matrix.
- At GitHub **Actions → CI → Run workflow**, choose `main` (or the intended candidate ref) and select full matrix explicitly. A completed green job verifies only tested paths and versions; local/cloud recovery and legal evidence authenticity remain unproven.
- No `push` trigger, no cron, no upload artifact with personal evidence, no background network/backups; `GITHUB_TOKEN` read-only and checkout credentials not retained. Failures must never be concealed by `continue-on-error`.
- **Important:** branch protection currently reports `protected=false`; if this changes, a path-filtered required check can remain pending on docs-only PRs. Review protection config before requiring this workflow as a merge gate, or move to an always-running no-runner path-aware decision gate.
- The 2026-10 monthly Private included quota is exhausted. Do not repeatedly manually run an unassignable job, raise paid budget, add payment methods or make repository Public without explicit informed owner approval. Check included balance next month, then make one manual smoke + one full matrix for a significant milestone.
- Historical 4-job CI on all push/PR events is superseded by this operational policy only; the older successful/failing execution logs are preserved in GitHub.

**Status vocabulary:** `POLICY_APPLIED` ≠ `RUNNER_ASSIGNED` ≠ `TESTS_PASSED`. None of the latter two is asserted for this update.

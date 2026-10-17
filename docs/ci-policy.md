# CI usage policy (private repository)

**Effective:** 2026-10-15. Private GitHub Actions included allowance is shared with other private repositories. In Oct 2026 the personal Free allowance was exhausted (account report confirmed $12.00 of discounted Private runner usage across SecondBrain, LK and Lovely; net charge $0). A new workflow cannot allocate a runner until included time resets or separately approved paid overage is available. No budget/payment change is part of this PR.

## Event-to-test contract

| Event | Trigger / cost | Tests |
|---|---|---|
| A PR into `main` modifying `src/**`, `tests/**`, `scripts/**`, `pyproject.toml`, or `.github/workflows/**` | **Automatic** one `ubuntu-latest` job with Python 3.12 | Install editable `.[dev]` and run `python scripts/verify.py` |
| Docs-only PR or push | No CI run | Manual review, document/link inspection. **No green CI claim**. Branch protection check requirements must be reconsidered before requiring this path-filtered check. |
| Push to `main` modifying `src/**`, `tests/**`, `scripts/**`, `pyproject.toml`, or `.github/workflows/**` | **Automatic** one Linux Python 3.12 job | Protect direct pushes and merged code. A PR merge may run smoke twice; trade-off accepted. Other branches and docs-only pushes do not run CI. |
| Manual `workflow_dispatch` (default `full_matrix=false`) | One Linux Py3.12 Job | Same current tests through the same local verifier |
| Manual `workflow_dispatch` with `full_matrix=true` | **6 jobs**, Linux and Windows × Py3.11/3.12/3.13, at most 2 simultaneous jobs | Cover Python 3.11 minimum declared in `pyproject.toml`; same local verifier on each OS/version. Use only at milestone/pre-release gates. |

## Quality and cost guardrails

- Current M0/v0.1 tests are the **actual `tests/` directory**; frozen R7–R13 reference under `legacy/` is not an automatic regression contract. M1 and later features must add tests before asserting acceptance.
- Developers run **`python scripts/verify.py`** locally on each code change; run Windows tests locally when behavior depends on NTFS, path casing, locks, junctions, file attributes, or atomic replace. Linux CI cannot prove Windows behavior.
- For milestone, branch reconciliation, filesystem safety, backup/restore or production-facing release, execute `full_matrix=true` on the specific candidate SHA and save the run URL/result. Avoid authorizing release with a skipped/manual-unrun matrix.
- At GitHub **Actions → CI → Run workflow**, choose `main` (or the intended candidate ref) and select full matrix explicitly. A completed green job verifies only tested paths and versions; local/cloud recovery and legal evidence authenticity remain unproven.
- Only path-filtered `push(main)` and `pull_request(main)` plus explicit manual dispatch; no cron, no upload artifact with personal evidence, no background network/backups; `GITHUB_TOKEN` read-only and checkout credentials not retained. Failures must never be concealed by `continue-on-error`.
- **Important:** branch protection currently reports `protected=false`; if this changes, a path-filtered required check can remain pending on docs-only PRs. Review protection config before requiring this workflow as a merge gate, or move to an always-running no-runner path-aware decision gate.
- The 2026-10 monthly Private included quota is exhausted. Do not repeatedly manually run an unassignable job, raise paid budget, add payment methods or make repository Public without explicit informed owner approval. Check included balance next month, then make one manual smoke + one full matrix for a significant milestone.
- Historical 4-job CI on all push/PR events is superseded by this operational policy only; the older successful/failing execution logs are preserved in GitHub.

- The verifier records the Git HEAD, working-tree state, executing OS/Python version and PASS/FAIL for actual tests; all other operating systems/versions are NOT_VERIFIED. Tests passing on Windows do not imply Linux was tested, and vice versa. Tests run using the active Python interpreter, requiring prior `python -m pip install -e ".[dev]"`. No automatic dependency/network installation happens inside the local verifier.
- PR #47 (M1 capture) previously had unstable checks; it must not be treated as tested/merge-ready until a **new** real-runner successful check on that candidate is observed. A skipped/blocked job is not PASS.

**Status vocabulary:** `POLICY_APPLIED` ≠ `RUNNER_ASSIGNED` ≠ `TESTS_PASSED`. None of the latter two is asserted for this update.

## R57 — declared Python minimum compatibility coverage

`pyproject.toml` declares `requires-python = ">=3.11"`. Earlier full manual CI covered only Python 3.12 and 3.13, leaving the minimum version untested. The `full_matrix=true` manual gate now explicitly tests **Linux + Windows × Python 3.11/3.12/3.13 (six jobs)**, with at most two concurrent jobs. This spends more time only when the owner explicitly dispatches the full matrix; default main-push/PR smoke remains a single Linux/Python 3.12 job. Python versions outside that declared tested matrix remain NOT_VERIFIED. No claim that the October 2026 Private runners actually ran or passed.

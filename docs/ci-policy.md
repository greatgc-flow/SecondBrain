# CI usage policy (private repository)

This file states **policy**. Dated facts (runs, billing messages, results) live in [status.md](status.md), not here. Nothing here claims a CI run or pass.

## Event-to-test contract

| Event | Cost | Tests |
|---|---|---|
| PR into `main` changing `src/**`, `tests/**`, `scripts/**`, `pyproject.toml` or `.github/workflows/**` | Automatic: one `ubuntu-latest` job, Python 3.12 | Install editable `.[dev]`, run `python scripts/verify.py` |
| Push to `main` changing the same paths | Automatic: one Linux Python 3.12 job | Same smoke; a PR merge may run it twice (accepted) |
| Docs-only PR or push | No CI run | Manual review and link inspection. **No green-CI claim** from a docs check |
| Manual `workflow_dispatch`, `full_matrix=false` (default) | One Linux Python 3.12 job | Same local verifier |
| Manual `workflow_dispatch`, `full_matrix=true` | 6 jobs: Windows and Ubuntu × Python 3.11/3.12/3.13, at most 2 at once | Same verifier on each cell |

The full matrix is required before filesystem-sensitive acceptance (NTFS, path casing, locks, junctions, atomic replace, backup/restore) and before release. It is run only by an explicit dispatch on the candidate SHA, with the run URL and result saved. A skipped, blocked or never-started job is not a pass; a matrix that was not run is never claimed.

## Guardrails

- Tests are the actual `tests/` directory; frozen R7-R13 material under `legacy/` is not an automatic regression contract.
- `scripts/verify.py` is the same test gate locally and in CI, so there is no duplicate CI logic. It records HEAD, working-tree state, OS, Python and PASS/FAIL. Local runs (for example Python 3.14) are not declared-matrix assurance; versions and systems outside the matrix are NOT_VERIFIED. Windows-sensitive behaviour must be run on Windows; Linux CI cannot prove it.
- Workflow triggers are limited to path-filtered `push`/`pull_request` on `main` plus manual dispatch: no cron, no personal-evidence artifacts, no background network or backups, read-only `GITHUB_TOKEN`, no persisted checkout credentials, no `continue-on-error` hiding failures.
- If branch protection ever requires this check, a path-filtered check stays pending on docs-only PRs; review the protection config first or use an always-running path-aware gate.
- `pyproject.toml` declares `requires-python = ">=3.11"`, so the minimum version is covered by the full matrix.
- No spend or budget change, payment method or visibility change without explicit informed owner approval. Do not repeatedly dispatch a job that cannot get a runner. No Actions dispatch in the design phase.
- Policy may become more flexible only with measured risk and cost plus candidate evidence. Coverage is never removed just to obtain a green result.

## Vocabulary

`POLICY_APPLIED` ≠ `RUNNER_ASSIGNED` ≠ `TESTS_PASSED`. The latter two need a recorded run on the exact candidate. Current runner and billing facts: [status.md](status.md).

# Contributing to SecondBrain

## Development Setup

Create and activate a Python virtual environment (requires Python >= 3.11):

```bash
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\Activate.ps1

pip install -e .[dev]
```

## Running Tests

Run test suite locally before opening a pull request:

```bash
python -m pytest tests -q
```

## Development Principles

1. **Docs First**: Update documentation and design specifications before code changes.
2. **Decision Records Required**: No new features or architecture changes are accepted without an accompanying decision record in `docs/decisions.md`.

## CI workflow (Private GitHub repository)

The [CI policy](docs/ci-policy.md) runs one Linux smoke job automatically for code/test/tooling PRs into `main`. There is no push-triggered CI and no docs-only CI. For releases and Windows filesystem-sensitive changes, explicitly run **Actions → CI → Run workflow → full_matrix=true** on the candidate branch/commit. GitHub Free included Private minutes may be exhausted; a job not started is not a test pass.

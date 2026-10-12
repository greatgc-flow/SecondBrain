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
pytest -q -n auto
```

## Development Principles

1. **Docs First**: Update documentation and design specifications before code changes.
2. **Decision Records Required**: No new features or architecture changes are accepted without an accompanying decision record in `docs/decisions.md`.

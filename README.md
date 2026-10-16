# SecondBrain

SecondBrain is a restarted project for preserving personal files on one local computer without changing their sources.
The target v0.1 is a small offline CLI, `sb`, with six commands: `capture`, `find`, `open`, `verify`, `backup`, `restore`.

## Current state

- **Documentation and design only.** The target v0.1 contract is written but not implemented; no implementation or release is claimed. The current gate and readiness are recorded only in [docs/status.md](docs/status.md).
- `main` contains six stub commands that exit 2 as not implemented, installed version `0.0.1`, and 15 smoke tests. Those tests check the stubs; they are not feature completion.
- Product implementation (TDD) starts only after the design is frozen and the owner gives an explicit go.
- An S1-S5 prototype of the six commands already exists in open pull requests. It is a source for comparison and reuse: each piece is traced to a requirement before review, and nothing is merged blindly.

## Where to read

| Document | Purpose |
|---|---|
| [docs/README.md](docs/README.md) | Documentation map and authority |
| [docs/design.md](docs/design.md) | v0.1 target contract |
| [docs/decisions.md](docs/decisions.md) | ADRs |
| [docs/requirements.md](docs/requirements.md) | Requirements, planned tests, evidence status |
| [docs/schemas/](docs/schemas/) | JSON Schemas for receipt, config, manifest and CLI output |
| [docs/status.md](docs/status.md) | Current gate and evidence (canonical) |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Resume record |
| [docs/collaboration.md](docs/collaboration.md), [AGENTS.md](AGENTS.md) | Peer workflow and rules |
| [docs/ci-policy.md](docs/ci-policy.md) | Cost-aware CI policy |
| [docs/git-inventory.md](docs/git-inventory.md) | Git policy and inventory |

## Quick start (Windows, development)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python scripts/verify.py
```

This runs the 15 stub smoke tests. They show the scaffold works, not that any `sb` feature exists.

## History

The earlier R7-R13 line is frozen reference material: see [legacy/README.md](legacy/README.md) and the tag `legacy-r13-final`. Its implementation claims and instructions do not apply to the restarted v0.1.

## Guidance

[VerySimpleGuide](../VerySimpleGuide) is used as scoped guidance, pinned at `32c5e1f1258418d0324908f338c646e9602b6716` (Standard 1.7.0). It is not a mandatory framework, and no full validator run is claimed.

Integrity and recorded context only: no authenticity, admissibility, custody or legal-weight claim.

# SecondBrain — R7 (Development)

Evidence-first Second Brain project. The current implementation includes a read-only Evidence Object verifier and a local Capture-only pipeline. This is **not** a legally certified evidence preservation system, and Vault commit, custody chain, cloud restore, and release gates are not implemented.

This repository is currently **public**. Personal evidence, archive ZIPs, secrets and private local files are intentionally excluded.

## Scope
- Python 3.11+ source-first development
- Source-preserving Capture-only operations and explicit integrity validation
- TDD tests using synthetic fixtures; no real personal evidence
- Open issues: complete S1 (Vault publishing, custody, recovery), security review, supported-platform/live testing

## Development status
R7; partial TDD slice only. **Not a production release.**

See `src/` and `tests/` for the initial implementation and tests.

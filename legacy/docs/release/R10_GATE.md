# SecondBrain R10: development gate and publication inventory

## Implemented and executed

- R7 local Capture-only landing + receipt; R8 single-writer local Vault publication; R9 local RFC 8785 Acquisition/Custody chain; R10 manual checkpoint JSON export + prefix verification.
- R10 tests cover clean match, later unanchored suffix, full history rollback, consistent full-chain rewrite, malformed checksum, symlinks, copy inside root, empty chain, duplicate JSON keys and CLI usage.
- Offline execution uses a restricted `rfc8785` *shim*, which is **not** a standards implementation. RFC 8785 conformance and all tests MUST run on GitHub CI with the pinned external package before merging to main.

## Out of scope / NO-GO

- This is NOT a certification, legal admissibility conclusion, trusted third-party timestamp, WORM, cryptographic signature, proven external retention, verified independent backup, completed EvidenceObject, multi-machine cloud-safe lock, supported wheel distribution or real-device validation.
- Do not publish actual personal evidence, secrets, the original ZIP handoffs or local scratch databases to Git. Git keeps reviewed executable source and derived design/traceability documentation; original handoff archives remain under operator-controlled local retention until reviewed separately.

## Developer commands

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'
python -m pytest -q tests/
python brain.py checkpoint export --help
python brain.py checkpoint verify --help
```

Gate: **no formal release**; PR review and candidate-bound CI required. This document must be revised when tests/implementation change.

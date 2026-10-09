# Evidence-First SecondBrain

**R10 development snapshot — private repository, not a production evidence system.**

## Implemented vertical slices

- **R7 Capture:** `brain capture file|verify` copies local source bytes into an Inbox without deleting the source.
- **R8 Writer:** `brain writer init|publish|verify` checks local single-writer policy and publishes an **uncommitted** content-addressed Vault payload.
- **R9 Local custody ledger:** `brain custody commit|verify|chain` stores two RFC8785-canonicalized hash-linked events (Acquisition and Custody) per capture and a local receipt. Retry is idempotent and partial writes fail closed.
- **R10 manual external checkpoint:** `brain checkpoint export|verify` produces an RFC 8785 snapshot and checks a *supplied* off-root copy against the chain, distinguishing rolled-back or fully rewritten history from a later unanchored suffix. Independent retention remains an operator responsibility.\n- **Read-only object verifier:** `brain object verify` validates already-created object metadata and bytes. R9 still does **not** generate a sealed EvidenceObject record.

**New-chat continuation:** [R10 → R11 handoff](docs/handoff/2026-10-10_R10_TO_R11_HANDOFF.md) · [R11 start prompt](docs/handoff/START_NEW_CHAT_R11.md). These are dated handoff notes, not a substitute for current code/CI.

## Quick start (synthetic samples only)

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'
python -m pytest -q
python brain.py --help
python brain.py custody --help
```

See [R10 checkpoint quickstart](profiles/secondbrain/R10_CHECKPOINT_QUICKSTART.md), [current docs index](docs/README.md), [design-reference inventory](docs/reference/SOURCE_INVENTORY.json) and [R9 custody example](profiles/secondbrain/TDD_R9_CUSTODY_QUICKSTART.md), [R9 scope/limits](profiles/secondbrain/R9_SCOPE.md), and [R8 Writer example](profiles/secondbrain/TDD_R8_WRITER_QUICKSTART.md).

## Critical distinctions

`READY` → `VAULT_VERIFIED_UNCOMMITTED` → `LOCAL_CHAIN_COMMITTED_UNANCHORED` reflects **local data processing**, not a judicial determination or trusted forensic custody. Without an independently preserved trustworthy checkpoint outside the writable filesystem, the entire ledger can be substituted or rolled back undetected. R10 compares to a supplied external-file copy, **but cannot authenticate that file's independent custody or timestamp**. Neither filesystem locks nor cloud-sync files provide cross-device writer fencing. Original acquisition authenticity, WORM, trusted time, full EvidenceObject sealing, backups, Legal Hold and real Windows/OneDrive/Drive recovery remain **unverified/unimplemented**.

Only synthetic tests and reviewed source are committed. Do not upload real personal evidence, passwords or historical archive ZIPs. R9 CI passed 74 tests. R10 CI passed **84 tests** using the actual pinned `rfc8785==0.1.4` (PR #3 and `main`). The local offline shim is **not** a conformant implementation or CI evidence. Historical design and generic-kit source files are tracked in `docs/reference/` as **read-only archival materials**, deduplicated against their source ZIPs. See [R10 gate](docs/history/R10_GATE.md).

**Product release: NO-GO.** Version remains `0.0.0`; no PyPI/winget release is authorized.

# Evidence-First SecondBrain

**R9 development snapshot — private repository, not a production evidence system.**

## Implemented vertical slices

- **R7 Capture:** `brain capture file|verify` copies local source bytes into an Inbox without deleting the source.
- **R8 Writer:** `brain writer init|publish|verify` checks local single-writer policy and publishes an **uncommitted** content-addressed Vault payload.
- **R9 Local custody ledger:** `brain custody commit|verify|chain` stores two RFC8785-canonicalized hash-linked events (Acquisition and Custody) per capture and a local receipt. Retry is idempotent and partial writes fail closed.
- **Read-only object verifier:** `brain object verify` validates already-created object metadata and bytes. R9 still does **not** generate a sealed EvidenceObject record.

## Quick start (synthetic samples only)

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'
python -m pytest -q
python brain.py --help
python brain.py custody --help
```

See [R9 custody example](profiles/secondbrain/TDD_R9_CUSTODY_QUICKSTART.md), [R9 scope/limits](profiles/secondbrain/R9_SCOPE.md), and [R8 Writer example](profiles/secondbrain/TDD_R8_WRITER_QUICKSTART.md).

## Critical distinctions

`READY` → `VAULT_VERIFIED_UNCOMMITTED` → `LOCAL_CHAIN_COMMITTED_UNANCHORED` reflects **local data processing**, not a judicial determination or trusted forensic custody. Without an authenticated checkpoint outside the writable filesystem, the entire ledger can be substituted or rolled back undetected. Neither filesystem locks nor cloud-sync files provide cross-device writer fencing. Original acquisition authenticity, WORM, trusted time, full EvidenceObject sealing, backups, Legal Hold and real Windows/OneDrive/Drive recovery remain **unverified/unimplemented**.

Only synthetic tests and reviewed source are committed. Do not upload real personal evidence, passwords or historical archive ZIPs. The initial local offline suite passed **73 tests** with a restricted non-RFC shim and omitted one Unicode ordering test; the branch CI ran all **74 tests using actual `rfc8785==0.1.4` and passed**. Subsequent `main` CI remains a separate release gate.

**Product release: NO-GO.** Version remains `0.0.0`; no PyPI/winget release is authorized.
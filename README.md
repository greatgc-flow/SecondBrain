# Evidence-First SecondBrain

**R13-C development snapshot — private repository, not a production evidence system.**

## Implemented vertical slices

- **R7 Capture:** `brain capture file|verify` copies local source bytes into an Inbox without deleting the source.
- **R8 Writer:** `brain writer init|publish|verify` checks local single-writer policy and publishes an **uncommitted** content-addressed Vault payload.
- **R9 Local custody ledger:** `brain custody commit|verify|chain` stores two RFC8785-canonicalized hash-linked events (Acquisition and Custody) per capture and a local receipt. Retry is idempotent and partial writes fail closed.
- **R10 manual external checkpoint:** `brain checkpoint export|verify` produces an RFC 8785 snapshot and checks a *supplied* off-root copy against the chain, distinguishing rolled-back or fully rewritten history from a later unanchored suffix. Independent retention remains an operator responsibility.
- **R11 local EvidenceObject record:** `brain object create|verify-link` writes and validates a content-addressed **unsealed** object metadata record plus an immutable **per-Capture** Observation/Acquisition/Custody linkage. Identical bytes share one object, but not their capture events. `brain object verify` remains a narrow, read-only byte and metadata check. **Nothing is legally sealed, externally certified or independently timestamped.**
- **R12 synthetic local backup/restore:** `brain backup create|verify|restore` snapshots only complete R7–R11 local roots, uses an exact canonical manifest and last completion marker, and verifies all bytes/links on an isolated restore. **Independent offsite custody, Windows/cloud recovery and actual power-loss durability are not verified.**
- **R13-A local recovery quarantine:** a restored root receives two canonical advisory hold/sentinel files **before** copying writer authority. Writes fail with `RECOVERY_HOLD`; read-only verifiers continue. `brain recovery status` reports local hold state. **Neither marker is secure distributed fencing, and Windows CI is not a cloud recovery drill.**
- **R13-C operator-supplied backup pin:** optional `backup verify|restore --expect-manifest-sha256` compares a separately obtained manifest fingerprint before creating a restore root. A co-traveling or unauthenticated digest is not external proof.
- **R13-B synthetic cross-runner recovery:** independent CI jobs transfer synthetic snapshots using short-lived GitHub artifact storage and validate Ubuntu→Windows and Windows→Ubuntu restore with the original root unavailable to the consumer. This verifies portability only, **not** offsite custody, production recovery or RPO/RTO.

**Continue development from current GitHub `main`:** check the latest commit/PR/Actions first, then [current docs index](docs/README.md), [R13 development gate](docs/history/R13_DEV_GATE.md), [current roadmap](docs/roadmap/S1_NEXT.md) and [open R13 operational gate](https://github.com/greatgc-flow/SecondBrain/issues/11). Older R10→R11 handoffs are archived history and must **not** roll back the active code/tests.

## Quick start (synthetic samples only)

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'
python -m pytest -q
python brain.py --help
python brain.py custody --help
```

See [R13-C expected fingerprint guide](profiles/secondbrain/R13C_DETACHED_DIGEST_QUICKSTART.md), [R13-C development gate](docs/history/R13C_DETACHED_DIGEST_GATE.md), [R13-B CI transfer development gate](docs/history/R13B_CROSS_RUNNER_GATE.md), [R13 local quarantine scope](profiles/secondbrain/R13_RECOVERY_SCOPE.md), [R12 backup/restore quickstart](profiles/secondbrain/R12_BACKUP_QUICKSTART.md), [R12 scope](profiles/secondbrain/R12_SCOPE.md), [R11 object quickstart](profiles/secondbrain/R11_OBJECT_QUICKSTART.md), [R11 scope](profiles/secondbrain/R11_SCOPE.md), [R10 checkpoint quickstart](profiles/secondbrain/R10_CHECKPOINT_QUICKSTART.md), [current docs index](docs/README.md), [design-reference inventory](docs/reference/SOURCE_INVENTORY.json) and [R9 custody example](profiles/secondbrain/TDD_R9_CUSTODY_QUICKSTART.md), [R9 scope/limits](profiles/secondbrain/R9_SCOPE.md), and [R8 Writer example](profiles/secondbrain/TDD_R8_WRITER_QUICKSTART.md).

## Critical distinctions

`READY` → `VAULT_VERIFIED_UNCOMMITTED` → `LOCAL_CHAIN_COMMITTED_UNANCHORED` reflects **local data processing**, not a judicial determination or trusted forensic custody. Without an independently preserved trustworthy checkpoint outside the writable filesystem, the entire ledger can be substituted or rolled back undetected. R10 compares to a supplied external-file copy, **but cannot authenticate that file's independent custody or timestamp**. R11's `recorded_at` means only the local process clock and explicitly declares `LOCAL_UNSEALED_UNANCHORED`; historical `sealed_at` documents are read as legacy metadata labels, not legal evidence seals. Neither filesystem locks nor cloud-sync files provide cross-device writer fencing. Original acquisition authenticity, WORM, trusted time, certified EvidenceObject sealing, independently retained backups, Legal Hold and real OneDrive/Drive recovery remain **unverified/unimplemented**.

Only synthetic tests and reviewed source are committed. Do not upload real personal evidence, passwords or historical archive ZIPs. R9 CI passed 74 tests. R10 CI passed **84 tests** using the actual pinned `rfc8785==0.1.4` (PR #3 and `main`). R11 CI evidence is in [R11 gate](docs/history/R11_GATE.md); R12 synthetic CI and unverified operational acceptance are documented in [R12 gate](docs/history/R12_GATE.md); R13-A source CI and operational exclusions appear in [R13 development gate](docs/history/R13_DEV_GATE.md). The local offline shim is **not** a conformant implementation or CI evidence. Historical design and generic-kit source files are tracked in `docs/reference/` as **read-only archival materials**, deduplicated against their source ZIPs. See [R10 gate](docs/history/R10_GATE.md).

**Product release: NO-GO.** Version remains `0.0.0`; no PyPI/winget release is authorized.

# Evidence-First SecondBrain

Private development repository; **R8 S1 local Writer pre-commit**, not a production evidence system.

## Implemented

- `brain capture file/verify`: source-preserving local Capture; receipts and last `.ready` marker
- `brain writer init/publish/verify`: explicit local Writer policy, hash-based Vault reuse, distinct pending observation per capture, read-only verification of pre-commit receipt
- `brain object verify`: read-only validation of an already independently created v2 canonical object record (R8 does **not** create this record)
- 57 local, synthetic TDD tests with negative/fault cases; GitHub Actions executes all three suites

**`READY` and `VAULT_VERIFIED_UNCOMMITTED` are NOT `SEALED`, `COMMITTED` or evidence authenticity guarantees.** No Custody JCS hash chain, AcquisitionEvent, distributed Writer gate, cloud validation, Legal Hold, restore or production release exists yet.

## Start

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1'
python -m pytest -q tests/test_writer_tdd.py tests/test_capture_tdd.py tests/test_object_verify_tdd.py
python brain.py --help
```

See [R8 quickstart](profiles/secondbrain/TDD_R8_WRITER_QUICKSTART.md), [scope/gates](profiles/secondbrain/R8_SCOPE.md) and [R7 history](profiles/secondbrain/R7_SCOPE.md).

## Safety and publication

Only synthetic tests and reviewed source belong in Git. **Never commit personal evidence, credentials, original archives, cloud sync folders or test caches.** The local writer epoch is a policy generation ID, not a secret or cross-cloud lock. On failure, retain and inspect partial assets; never automatically delete the only original. The `.active` lock may require manual operator recovery after a crash.

Product release remains **NO-GO** pending complete TDD, verified RFC8785 custody streams, recovery, backup/restore, live Windows and sync tests and security review. Version stays `0.0.0`; do not publish to pip/winget yet.

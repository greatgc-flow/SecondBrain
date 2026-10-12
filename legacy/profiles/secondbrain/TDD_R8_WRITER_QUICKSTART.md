# R8 S1 writer pre-commit TDD — first-run guide

The new feature is a **local, single-writer, UNCOMMITTED** Vault publication prototype, not a legal custody chain or final canonical commit. It does not call any cloud or AI APIs.

## 90-second path (synthetic file only)

From `profiles/secondbrain`:

```bash
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1'
python -m pytest -q tests/test_writer_tdd.py tests/test_capture_tdd.py tests/test_object_verify_tdd.py
mkdir -p ./demo-brain
printf 'synthetic fixture' > ./fixture.txt
python brain.py capture file ./fixture.txt --root ./demo-brain --device-id pc-1 --collector tester --json
# Copy capture_id from that JSON into CAP_ID below.
python brain.py writer init --root ./demo-brain --writer-id central --json
# Copy writer_epoch and CAP_ID into the next command.
python brain.py writer publish CAP_ID --root ./demo-brain --device-id pc-1 --writer-id central --writer-epoch WRITER_EPOCH --json
python brain.py writer verify CAP_ID --root ./demo-brain --device-id pc-1 --json
```

On PowerShell, create the directory with `New-Item -ItemType Directory -Force .\demo-brain` and the fixture with `[IO.File]::WriteAllBytes((Join-Path (Get-Location) 'fixture.txt'), [byte[]](1,2,3))`.

Do **not** paste a real personal evidence file into a cloud-synced demo root. The captured receipt includes the source path.

## What is and is not published

- Canonical-like content address under `10_Evidence/Vault/objects/sha256/AA/BB/FULLHASH/payload` is copied and verified without overwriting a different existing payload.
- A distinct pending observation per `(device_id,capture_id)` is stored under `10_Evidence/Records/pending/observations`.
- A last local pre-commit receipt under `10_Evidence/Records/pending/ingest` is allowed **only** after the byte verification and observation publish; read-only `writer verify` reconstructs all expected references.
- No `10_Evidence/Records/objects/*.json` canonical record, no Acquisition/Custody journal, no `SEALED`, no `COMMITTED`, no ERL grade claim, no legal authenticity certification. `brain object verify` intentionally rejects these pre-commit candidates.

## Writer guard and recovery

`writer init` is a one-time **policy registration** and emits a random epoch. It is not a password, encryption key or distributed fencing token. `writer publish` requires matching Writer ID **and** epoch. It uses a local `.active` exclusive marker; if a process crashes while holding that marker, it remains and blocks publication pending manual inspection. Do not delete it automatically or promote another Writer until the journal, staged files and cloud provider sync state have been reviewed.

If a partial write occurs **before** the receipt, `writer verify` returns `INCOMPLETE_PUBLISH`; retry with the same key validates existing bytes and resumes safely. If a Vault object or existing observation conflicts, the Writer fails closed and does not overwrite it. A duplicate canonical Writer on two cloud-synced machines is **not supported**; synced filesystem operations are not a distributed lock or transaction.

Hardlink create-if-absent is required for metadata and payload publication on the local filesystem. If the filesystem, Windows toolchain or cloud sync root does not support it, the Writer fails rather than simulate global atomicity. This feature must pass physical Windows/OneDrive/Drive compatibility and adversarial reparse-point tests before production use. Root relocation and Korean/space-containing paths were exercised on the current Linux test system only.

## Next RED slice

Independent RFC 8785 JCS serializer/vector verification; append-only Acquisition and Custody streams with authorized writer events; proof of chain and external anchors; atomic logical commit receipt; crash replay reconciliation; Legal Hold and backup restore. None is implied by `VAULT_VERIFIED_UNCOMMITTED`.

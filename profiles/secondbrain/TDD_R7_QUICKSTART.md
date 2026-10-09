# R7 — Capture-only feature quickstart

## Run local synthetic tests

Install the explicit date-time validator: without it, JSON Schema FormatChecker may silently skip invalid RFC3339 dates.

```bash
python -m pip install 'pytest>=8,<10' 'jsonschema>=4,<5' 'rfc3339-validator>=0.1,<1'
python -m pytest -q tests/test_capture_tdd.py tests/test_object_verify_tdd.py
python brain.py capture file --help
python brain.py capture verify --help
```

## Capture one local file (examples use temporary local scratch directories)

```bash
mkdir -p ./scratch-brain
printf 'test bytes' > ./sample.txt
python brain.py capture file ./sample.txt --root ./scratch-brain --device-id pc-1 --collector local-user --json
# Read capture_id from the JSON result, then:
python brain.py capture verify 'CAP-<printed-uuidv7>' --root ./scratch-brain --device-id pc-1 --json
```

Windows PowerShell: `New-Item -ItemType Directory -Force .\scratch-brain`; `Set-Content .\sample.txt 'test bytes'`; same `python brain.py ...` commands.

`capture file` **does not write to `10_Evidence`**; it writes to `00_Inbox/Drop/<device>/<capture>/`. `.ready` means local bytes/receipt were present and verified when published; no cloud upload certainty, forensic acquisition guarantee, custody log or sealed commit. Never copy private files into a cloud-synced root without checking storage ACLs/encryption and the inclusion of original source path in receipt. Do not move/drop/delete the original until approved external retention policy.

Known limits: capture root must exist; aliases/symlinks rejected; parent path concurrently swapped remains an OS-level race and must be tested on real Windows with reparse points. UUIDv7 is generated using standard library cryptographic randomness because Python 3.13 has no `uuid.uuid7`. No external network calls are made.

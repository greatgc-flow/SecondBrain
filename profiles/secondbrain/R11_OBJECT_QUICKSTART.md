# R11 local EvidenceObject quickstart (synthetic test only)

This sequence works on a local filesystem with Python 3.12. It does **not**
prove legal authenticity, actual acquisition truth, trusted external
timestamp, cloud sync or durable backup. Use only **invented sample bytes**.

```bash
cd profiles/secondbrain
python -m pip install 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4' 'pytest>=8,<10'
mkdir -p '/tmp/내 Second Brain'
printf 'synthetic-only\n' > /tmp/synthetic-demo.txt
python brain.py capture file /tmp/synthetic-demo.txt --root '/tmp/내 Second Brain' --device-id pc1 --collector demo --json
```

From the JSON output, copy the `capture_id`. Do not hardcode a historical
capture ID. Initialize exactly one local writer (before publication):

```bash
python brain.py writer init --root '/tmp/내 Second Brain' --writer-id local-writer --json
```

Copy `writer_epoch` from the returned JSON and use it below, together with
your `capture_id`:

```bash
python brain.py writer publish <CAPTURE_ID> --root '/tmp/내 Second Brain' --device-id pc1 --writer-id local-writer --writer-epoch <WRITER_EPOCH> --json
python brain.py custody commit <CAPTURE_ID> --root '/tmp/내 Second Brain' --device-id pc1 --writer-id local-writer --writer-epoch <WRITER_EPOCH> --json
python brain.py object create <CAPTURE_ID> --root '/tmp/내 Second Brain' --device-id pc1 --writer-id local-writer --writer-epoch <WRITER_EPOCH> --json
python brain.py object verify-link <CAPTURE_ID> --root '/tmp/내 Second Brain' --device-id pc1 --json
python brain.py object verify <OBJECT_ID_FROM_CREATE> --root '/tmp/내 Second Brain' --json
```

`object create` yields
`LOCAL_OBJECT_LINK_VERIFIED_UNANCHORED`, a **local consistency status**.
The per-capture link commits the already-verified Observation and
Acquisition/Custody hashes to one shared EvidenceObject metadata digest.
`object verify` is intentionally narrower: it checks object metadata and
the Vault payload, not all capture-level links.

Success exits 0, missing root/epoch exits 2, an integrity/authorization/
record failure exits 3 (JSON `error_code`). Existing objects/links are
never silently replaced; retry the same command after resolving a transient
failure rather than deleting evidence paths. If a different record is
already at the same path, investigate the conflict; do not bypass it.

`recorded_at` is the software's **untrusted local clock time**, not
`sealed_at`, court certification or a trusted independent witness.
R10 manual checkpoints may be exported out-of-root for independent
operator retention (see [R10 guide](R10_CHECKPOINT_QUICKSTART.md)), but
the tool cannot verify that retention or timestamp. Do not store private
evidence or secrets in GitHub.

Code: [brain_core/object.py](brain_core/object.py) ·
[scope](R11_SCOPE.md) ·
[tests](tests/test_object_create_r11_tdd.py) ·
[roadmap](../../docs/roadmap/S1_NEXT.md).

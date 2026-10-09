# Evidence-First SecondBrain

Private development repository for an evidence-first Second Brain. Current milestone: **R7, two narrow TDD product slices**.

## What's implemented

- Local copy-only Capture landing: `brain capture file` / `brain capture verify`
- Read-only Evidence Object verification: `brain object verify`
- Two JSON Schema v2 contracts and 40 synthetic pytest test cases
- GitHub Actions to run tests against the pushed source

**Important:** A READY capture is **not** a legally sealed evidence object. Writer, Custody, Legal Hold, cloud sync/restore, provenance certification and full system validation remain unimplemented or unverified.

## Start

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4,<5' 'rfc3339-validator>=0.1,<1'
python -m pytest -q tests/test_capture_tdd.py tests/test_object_verify_tdd.py
python brain.py --help
```

For practical examples, see [R7 Quickstart](profiles/secondbrain/TDD_R7_QUICKSTART.md). For scope and release limitations, see [R7 Scope](profiles/secondbrain/R7_SCOPE.md).

## Roadmap

Next is S1 single-writer canonical commit: verify authority → stage source → publish Vault → Observation/Acquisition/Custody → recovery/commit receipt, with independently verified RFC 8785 canonicalization. A tested local capture does not authorize promotion to SEALED/COMMITTED.

## Publishing policy

No private evidence source files, copied personal data, secrets, generated archives or test caches should be committed. Existing archived R1–R7 ZIPs remain outside Git; publication of archival material requires separate review.

Repository initialized after the owner's privacy change; prior README and ignore commits were preserved. This Git tree contains the **R7 runtime core, schemas, test suite, quickstart and scope docs**. The full historical design corpus and archived R1–R7 ZIP bundles remain in the original local handoff ZIP, not in Git. Editable/wheel distribution packaging and install-from-wheel testing are not yet completed. This is a **development snapshot, not a formal release**.

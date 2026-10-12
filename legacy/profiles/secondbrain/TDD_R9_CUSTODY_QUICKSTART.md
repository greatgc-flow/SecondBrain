# R9 — Local RFC 8785 custody ledger (development only)

The R9 ledger requires `rfc8785==0.1.4` (Trail of Bits, Apache-2.0), rather than a homemade canonicalization algorithm. Each Capture written through R8 must be **READY and VAULT_VERIFIED_UNCOMMITTED** before a custody append is permitted.

## Install and verify

```bash
cd profiles/secondbrain
python -m pip install 'pytest>=8,<10' 'jsonschema>=4.23,<5' 'rfc3339-validator>=0.1,<1' 'rfc8785==0.1.4'
python -m pytest -q
python brain.py custody --help
```

## Normal flow

```bash
# Configure an empty local brain root once (the operator must ensure sole writer)
python brain.py writer init --root ./brain-root --writer-id pc-primary --json
# Save returned writer_epoch. Capture existing source and publish using R7/R8 CLI.
python brain.py capture file ./sample.txt --root ./brain-root --device-id pc-primary --collector tester --json
python brain.py writer publish CAP-... --device-id pc-primary --writer-id pc-primary --writer-epoch UUID --root ./brain-root --json
# Only now record two locally hash-linked acquisition/custody events:
python brain.py custody commit CAP-... --device-id pc-primary --writer-id pc-primary --writer-epoch UUID --root ./brain-root --json
python brain.py custody verify CAP-... --device-id pc-primary --root ./brain-root --json
python brain.py custody chain --root ./brain-root --json
```

The `CAP-...` and `UUID` arguments are placeholders from the earlier commands. Never replace real source data with a testing sample.

## Recovery, risk and failure modes

- A partial `ACQUISITION` event blocks *other* captures; the same capture and writer epoch can retry safely. A complete event pair with a missing receipt is also recoverable by retry.
- Replaced, missing or malformed event files fail closed. A damaged R8 vault or capture also blocks verification.
- Do not manually delete `.active` lock, partial files, or event files: preserve them for investigation and do not rerun before operator review.
- The RFC 8785 library **must** be installed; there is no runtime fallback. GitHub CI exercises its actual implementation and Unicode UTF-16 ordering.
- `LOCAL_CHAIN_COMMITTED_UNANCHORED` is an **internal local ledger record only**. It is NOT an independently timestamped, externally anchored, irreversible, cloud-replicated, legally authenticated or sealed evidence commit.
- Whole-chain substitution or rollback is not independently detectable without an authenticated checkpoint outside the writable tree. Local filesystem locks do not provide multi-machine safety on OneDrive/Google Drive.
- There is no production-ready deletion/legal-hold policy, boot-time recovery supervisor, independent snapshot verifier, object record publication or Windows reparse-race hardening.
- This milestone is a **synthetic TDD slice**, not a formal `pip`, winget, or end-user release.

RFC: https://www.rfc-editor.org/rfc/rfc8785.html
Library: https://github.com/trailofbits/rfc8785.py

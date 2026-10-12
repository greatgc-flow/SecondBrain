# R10 — external checkpoint verification (development-only)

Local custody chain verification alone **cannot** detect consistent rewriting of the full local history. The R10 checkpoint is an exportable canonical RFC 8785 JSON statement of a **specific prefix** (`event_count`, `tip_hash`). It is **not a trusted timestamp, signature, WORM guarantee or independent attestation**.

After completing local custody commits:

```bash
cd profiles/secondbrain
python brain.py checkpoint export --root /path/to/brain --json > /path/outside/brain/checkpoint-001.json
python brain.py checkpoint verify /path/outside/brain/checkpoint-001.json --root /path/to/brain --json
```

**Critical operator responsibility:** retain the checkpoint outside the brain in a separately access-controlled location (preferably independent provider/offline media), monitor/check its integrity and document its acquisition time. Just choosing a different subfolder or path does NOT prove independence. A compromised local ledger and its same-administrator checkpoint can still be rewritten together. Do not upload or expose sensitive identifiers without policy approval.

Valid results:

- `CHECKPOINT_EXACT_MATCH_EXTERNAL_CUSTODY_UNVERIFIED`: the ledger agrees through the checkpoint tip, **but its independent custody has not been verified**.
- `CHECKPOINT_PREFIX_MATCH_UNANCHORED_SUFFIX`: historical prefix agrees, but there are later **unanchored** events; refresh external checkpoint.

Failures include `CHECKPOINT_AHEAD_OR_ROLLBACK`, `CHECKPOINT_CHAIN_MISMATCH`, `CHECKPOINT_MISMATCH`, `CHECKPOINT_INSIDE_ROOT`, `CHECKPOINT_MALFORMED` and `UNSAFE_CHECKPOINT_PATH`. CLI uses exit code 3 for validation failure. Reject symlinked checkpoint files; filesystem-race/Windows reparse adversarial tests are still required. Do not treat this as legal seal.

## Next TDD slices

- Create a schema-compliant EvidenceObject record, link it to Observation/Acquisition and validate bytes/metadata cross references before advancing state.
- Require validated off-root checkpoint for **policy** where configured; report unverified external retention rather than falsely claiming an anchor.
- Test independent backup/restore, cloud sync conflict detection, malicious concurrent parent-path swapping and Windows reparse points.

## Scope and known limits

R7 Capture-only → R8 uncommitted Vault Writer → R9 local JCS chain → R10 checkpoint export/verification. This remains *developer preview, no production release*.

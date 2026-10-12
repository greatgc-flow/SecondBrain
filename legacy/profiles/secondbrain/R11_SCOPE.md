# R11 — local EvidenceObject metadata + capture-specific lineage

**Development-only local consistency**, not certified collection, legal sealing, WORM,
verified backup, trustworthy timestamp, outside-party authentication or release.

## Contract and SSOT

- Implemented by [brain_core/object.py](brain_core/object.py) using existing R7
  [capture.py](brain_core/capture.py), R8 [writer.py](brain_core/writer.py),
  R9 [custody.py](brain_core/custody.py), and read-only v2
  [verify.py](brain_core/verify.py). Do not create an independent second
  interpretation of capture, publication, chain or byte integrity.
- One **shared byte-level** object record at
  `10_Evidence/Records/objects/obj-sha256-<SHA256>.json`. Its Vault
  payload is immutable content-addressed bytes. Recorded media type is
  `application/octet-stream` (not reliable content sniffing); provenance
  fidelity is `unknown` unless separately established.
- One **distinct capture-level** link at
  `10_Evidence/Records/objects/links/<device>/<CAP>.json`. It names the
  object metadata digest, Observation ID/hash, R8 publication receipt digest,
  Acquisition event sequence/hash, Custody event sequence/hash, R9 commit
  receipt digest and writer ID/epoch. A repeated capture of identical bytes
  must keep its own link/events/Observation, never insert a mutable list of
  captures into the shared object.
- Objects and links use RFC 8785 canonical JSON, immutable same-volume
  staging + create-if-absent link, verification on retry and directory fsync.
  The capture link is written LAST. If publication fails, absence of the
  link means the operation is **not complete**, even if a shared object record
  was already created. No repair overwrites an existing different record.
- `brain object verify <object_id>` checks the local byte record and Vault
  bytes only. `brain object verify-link <capture_id> --device-id ...`
  rechecks the underlying Capture, Vault, Observation, entire local R9 chain,
  Acquisition/Custody pair and receipt, plus the R11 object+link contents.
  These are **read-only**; neither is independent certification.

## Timestamp and legacy `sealed_at` decision

**New R11 records DO NOT write `sealed_at`.** They use
`recorded_at` (process-clock metadata publication instant, **not trusted
or independently timestamped**) plus the mandatory
`record_scope=LOCAL_UNSEALED_UNANCHORED`. Updated
[JSON schema](schemas/v2/evidence-object.schema.json) accepts exactly either
the new recorded-at/local-scope form or the older sealed-at-only v2 form.
Existing tests and older manually supplied v2 records remain readable by
`brain object verify` without granting any legal seal interpretation;
the historical `sealed_at` spelling itself never proves seal status.
R11 `create` refuses to claim/update a legacy or inconsistent existing record.
It also does not backfill an unverified source filename or asserted timestamp.

## Fail-closed and limitations

| Condition | Behavior |
| --- | --- |
| No local custody commit | `CUSTODY_INVALID`; no R11 completion |
| Unverified R7/R8 or changed bytes | `PUBLICATION_INVALID` / `INTEGRITY_MISMATCH` |
| Wrong writer ID/epoch | `WRITER_NOT_AUTHORIZED` |
| Corrupt existing object/link | `OBJECT_RECORD_CONFLICT` / `LINK_TAMPERED` |
| Link absent, partial object published | `INCOMPLETE_OBJECT_LINK`; retry |
| Unsafe path/symlink | `UNSAFE_PATH` |
| System call interrupted | `INCOMPLETE_OBJECT`; examine, then retry |
| Invalid device/capture syntax | `INVALID_ARGUMENT` |

The local root may be moved, including Korean/spaces, because object and
lineage records contain no absolute root path. The original R7 capture
receipt may still record its original source path: treat it as private.

Synthetic GitHub CI tests cover idempotency, two captures/one content,
actual digests, missing/tampered dependencies, duplicate keys, link and
parent symlinks, fsync/publish fault injection, empty bytes, relocation,
CLI/exit codes and original-byte preservation. No live OneDrive/Google Drive
placeholder, Windows reparse, hostile concurrent path swap, true power
loss/durable sync, remote multi-writer fencing, independent snapshot/restore,
legal evidence export, real evidence, or paid provider was tested. An
adversary controlling the entire local root can rewrite the chain and
links coherently; R10 can compare only against an operator-supplied external
checkpoint whose own custody remains **unverified**.

## Feedback loop and next gate

Failure observed → isolate underlying vs new R11 record → create a
regression oracle → minimal correction → exact candidate-bound PR CI
→ post-merge main CI → document residual operational risk.
R12 priority: independently verified backup/restore and Windows/cloud
filesystem matrix, then trusted external custody and multi-device fencing.
Formal product release remains **NO-GO** (version 0.0.0).

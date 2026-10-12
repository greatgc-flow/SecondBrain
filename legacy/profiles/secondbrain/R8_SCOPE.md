# R8 S1 writer publish: scope and gate

R8 extends R7 with an explicit *local* Writer policy/epoch check, fail-closed local lock, content-addressed Vault payload publication, distinct pending observation per capture, last-file **pre-commit** receipt, read-only verifier and crash/retry regression tests.

Success status: `VAULT_VERIFIED_UNCOMMITTED` only. No canonical object record or custody/commit event is issued. `writer init` and the epoch field are not security credentials. No cloud-wide CAS, WORM, RFC8785 hash chain or cross-host writer fencing is claimed.

R8 tests: 57 synthetic pytest cases (R7: 40; R8: 17). Files are generated in local temporary directories; no API, provider, secrets or personal evidence needed. Verified Linux paths with Hangul/spaces and fault-injection; live Windows/Node reparse-point, multi-host sync, hardlink support and paid AI remain **NOT RUN**.

Logical transaction is **not** complete. `VAULT_VERIFIED_UNCOMMITTED` is never a legal evidentiary or release approval. Product/production release: **NO-GO**.

Remaining order: trusted RFC8785 serializer & independent vectors → Acquisition/Custody event stream and chain verification → sealed object records and logical receipt → recovery/split-brain/hold/restore → candidate-bound deployment and live verification.

# R9 Scope and gate

**Implemented:** Append-only, per-sequence local RFC8785-hashed acquisition/custody events (two events per capture); local unanchored commit receipt; strict read-only chain and receipt verification; single-writer policy; crash/retry handling. R7 Capture and R8 Vault publication remain unchanged.

**Not implemented:** external timestamp/witness, trusted chain-head anchoring, hash-chain anti-rollback, full EvidenceObject record publication and `SEALED` state, legal hold, cross-host fencing, restore under cloud conflict, production-grade Windows filesystem adversarial validation, offline dependency availability.

**Test results:** The local environment could not download `rfc8785`. Offline regression used a **NON-RFC test shim** for the restricted ASCII-key ledger data. A UTF-16 canonicalization vector is intentionally excluded from that local run; it MUST pass in GitHub CI with the actual library before merge. Treat CI as the canonical dependency/contract gate and check its commit SHA.

**Verdict:** source-development milestone GO if full CI succeeds; legal-evidence production release NO-GO.

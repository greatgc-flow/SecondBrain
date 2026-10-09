# S1 roadmap — current GitHub main SSOT

Code: `profiles/secondbrain/`. Historical plans: `docs/reference/`.
Version 0.0.0 and **formal product release NO-GO** remain unchanged.

## Implemented development slices

- **R7:** synthetic source-preserving Capture landing.
- **R8:** synthetic local Writer/Vault publication and Observation.
- **R9:** RFC 8785 canonical, locally unanchored Acquisition/Custody chain.
- **R10:** operator-supplied external checkpoint prefix comparison, not
  trusted offsite custody or timestamp.
- **R11:** one local unsealed EvidenceObject per payload digest, distinct
  Capture linkage; see [R11 gate](../history/R11_GATE.md).
- **R12 LOCAL ONLY:** strict, synthetic whole-R7–R11 closure snapshot,
  canonical file inventory and local restore to a non-overwriting destination;
  see [R12 gate](../history/R12_GATE.md). Development CI success does
  **not** mean operational independent backup acceptance.

- **R13-A LOCAL SAFETY:** synthetic R12 restored-root quarantine blocks
  mutating commands via two locally removable manifest-bound markers;
  development code/test results in [R13 gate](../history/R13_DEV_GATE.md).
  This is **not** external writer fencing or independent recovery proof.

## Next operational gate: remaining R13 — independent storage/recovery drill and platform matrix

1. **Independent custody:** operator chooses a separately administered
   physical medium or account, retains and authenticates a snapshot
   independently of the source root. Record who/when/how with no
   fabricated proof of trusted timestamp. Do not ingest production
   evidence as a test fixture.
2. **Loss of primary:** disconnect/disable original synthetic storage;
   fetch independent snapshot to a fresh machine/root; run
   `backup verify`, `backup restore`, and all R7–R12 verifiers.
   Record observed source loss/recovery, RPO/RTO, digest equality,
   recovery-only status and controlled writer handover.
3. **Real filesystem tests:** CI-level Windows NTFS junction/reparse
   guard coverage (R13-A) is distinct from full platform operational
   acceptance; still test permissions,
   missing hydration, OneDrive and Google Drive offline files,
   conflicts, restore and multi-device race matrix. Fail closed,
   never silently repair sync conflicts or assert a distributed lock.
4. **Hardening:** hostile concurrent directory-swap/TOCTOU review,
   durable fsync/power-loss study, backup privacy/encryption/access
   controls and multi-PC writer fencing. Use mature platform
   facilities rather than bespoke cloud SDKs.
5. **Acceptance:** reproducible fault logs → cause analysis →
   failing regression → minimal fix → exact PR CI → operator-observed
   drill → independent review → recorded go/no-go.

## Other deferred product gates

Trusted external signatures/timestamps, Legal Hold, legal export,
cross-platform installer/wheel, PyPI/winget, AI privacy and paid
provider quotas, production security audit and true acquisition
provenance. Source and docs stay GitHub-only; **never** commit personal
evidence, secrets, caches, archives/ZIPs or live snapshot output.

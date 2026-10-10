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

- **R13-B CI TRANSPORT:** short-lived synthetic artifact between independent
  GitHub jobs, Ubuntu→Windows and Windows→Ubuntu. Checks byte-exact
  R7–R13 recovery and R10 checkpoint without producer root; development
  results in [R13-B gate](../history/R13B_CROSS_RUNNER_GATE.md).
  Separate CI runner is not separately administered durable custody.

- **R13-C OPTIONAL PIN:** require a previously known external SHA-256
  of the R12 canonical manifest body as an optional verify/restore input.
  Refuse mismatching, even internally valid, snapshots before creating
  the recovery root. See [R13-C gate](../history/R13C_DETACHED_DIGEST_GATE.md).
  A digest co-traveling with the backup is not independently authenticated.

- **R13-D HARDLINK GUARD:** reject regular files with `st_nlink != 1`
  in source/snapshot/restored root (including recovery hold), checked in
  read-only verifier and copy path; distinct same-content objects remain
  allowed. See [R13-D gate](../history/R13D_HARDLINK_GATE.md).
  **Not** protection against concurrent hostile filesystem path swaps.

- **R13-E LEAF IDENTITY DRIFT:** reject byte-identical ordinary files substituted at
  the source path between backup copy or digest checks; compare pre/post
  inode and metadata identity. See [R13-E gate](../history/R13E_LEAF_DRIFT_GATE.md).
  This cannot guarantee safety against atomic parent-directory swaps.

- **R13-F WINDOWS CLOUD FLAGS:** refuse file attributes REPARSE_POINT, OFFLINE,
  RECALL_ON_OPEN or RECALL_ON_DATA_ACCESS where surfaced by Windows
  stat/lstat/fstat before accepting or reading Capture, snapshots or
  recovery markers. Tests inject exact bit values on both CI runners;
  genuine cloud placeholders/online-offline states remain unverified.
  See [R13-F gate](../history/R13F_WIN_CLOUD_ATTR_GATE.md).

- **R13-G OPERATOR SYNTHETIC REHEARSAL:** `synthetic_offline_drill.py` accepts an
  externally typed R12 manifest fingerprint, Capture IDs and checkpoint;
  performs read-only preflight before creating a fresh quarantined restore
  root, then checks R7–R11 links and records only elapsed program time.
  CI-synthetic receipts are enforced. See [R13-G gate](../history/R13G_OPERATOR_PREFLIGHT_GATE.md).
  No inference of actual custody independence, observed disaster RTO/RPO
  or external Writer fencing.

- **R13-H DETACHED CHECKPOINT PATH SAFETY:** externally provided R10 witness
  file and all ancestors are checked with lstat before following paths or
  reading JSON: reject known Win32 OFFLINE/REPARSE/RECALL flags, links,
  junctions and nonunique regular-file hardlinks. Repeat identity check
  after canonical JSON reads to reject byte-identical leaf replacements.
  [R13-H gate](../history/R13H_CHECKPOINT_PATH_GATE.md). This does not
  prove independent witness custody or prevent hostile parent ABA races.

- **R13-I RECOVERY MARKER PRESENCE:** local restored-root quarantine
  now uses metadata-only `lstat` for both markers and their directories.
  A denied stat, dangling/unsafe link, known Win32 offline/reparse/recall
  attribute or nonregular marker is treated as HOLD/UNSAFE, never as
  permission to write. This prevents `Path.exists()` false negatives from
  bypassing the local advisory quarantine. See
  [R13-I gate](../history/R13I_MARKER_PRESENCE_GATE.md). Two markers can still
  be deleted by a malicious root owner; this is **not distributed fencing**.

- **R13-J PARENT-TRAVERSAL PATH ISOLATION:** reject caller-supplied `..`
  components in backup source/snapshot and create/restore destination paths
  *before* absolute-path normalization or directory creation. Prevents a
  lexical containment check being bypassed to place a snapshot inside the
  source root, or a restore inside its own snapshot. See
  [R13-J gate](../history/R13J_PATH_BOUNDARY_GATE.md). Static path inspection
  still does not provide atomic security against hostile parent swaps or
  Windows filesystem aliasing; no independent custody claim.

- **R13-K SNAPSHOT CONTROL-LEAF DRIFT:** snapshot `manifest.json` and
  `.complete` must remain the same ordinary file identity throughout
  canonical read and tree scan, even when an attacker substitutes a
  different inode with the *same bytes*. Reject as `SNAPSHOT_TAMPERED`
  before restore-root creation. See
  [R13-K development gate](../history/R13K_SNAPSHOT_CONTROL_LEAF_GATE.md).
  This still does not close hostile parent-directory ABA races, secure
  descriptor-relative opens or independent offsite custody.

## Next operational gate: remaining R13 — independent storage/recovery drill and platform matrix

Runbook: [operator-observed independent restore and Windows/cloud matrix](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md). **Not performed by CI; no operational PASS assertion.**

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

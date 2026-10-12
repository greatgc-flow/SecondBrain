# R13-C — expected manifest digest (operator-supplied, NOT authenticated)

## Problem and precise trust boundary

R12 checks all files against the manifest and internally verifies
`manifest_sha256`. A sophisticated actor who can replace **all**
snapshot files and re-canonicalize the manifest and completion marker
could make a *different, locally coherent* snapshot. Local validation
alone cannot identify which prior backup an operator expected.

R13-C adds only a **detached expected 64-character lowercase SHA-256
fingerprint** to existing R12 `verify` and `restore` operations.
The fingerprint is calculated over the R12 canonical **manifest BODY
excluding `manifest_sha256`**, as already returned on `backup create
--json`. It is **not** a new hashing engine, signature or timestamp.

Use only with disposable synthetic data until separately approved.

## Usage

```bash
cd profiles/secondbrain
# On the SYNTHETIC source machine:
python brain.py backup create --root "<fully-linked-source-root>" --to "<new-outside-root-snapshot>" --json
# IMPORTANT: copy the returned manifest_sha256 to a DIFFERENT,
# separately administered place BEFORE the primary is lost.

# On the restore machine, independently retrieve THAT pinned value.
# Substitute literal 64-digit lowercase SHA-256 value in place of <DIGEST>.
python brain.py backup verify "<retrieved-snapshot>" --expect-manifest-sha256 <DIGEST> --json
python brain.py backup restore "<retrieved-snapshot>" --to-root "<fresh-root>" --expect-manifest-sha256 <DIGEST> --json
```

Both operations are backward compatible: omit
`--expect-manifest-sha256` for previous purely local checks. With a
pin supplied, malformed digests (not exactly 64 lowercase hex
characters) fail with `INVALID_EXPECTED_MANIFEST_SHA256`; an otherwise
valid but different snapshot fails with `MANIFEST_DIGEST_MISMATCH`
(exit code 3). **Restore refuses before creating the target directory**
even when the alternate backup is perfectly internally coherent.
Matching pin does not alter the existing
`LOCAL_*_EXTERNAL_CUSTODY_UNVERIFIED` status.

## Detachment means independent custody, not merely a second file

The pin must originate from an **independently controlled, previously
recorded channel** (e.g. approved offline operator-held log). A
`proof.json` or checksum stored *alongside* the snapshot can be
rewritten at the same time; its equality is not a separate witness.

R13-B CI passes the same-artifact `proof.json` fingerprint into the new
API to exercise it on both operating systems. That is a protocol
regression, **not independently authenticated custody**. Never upload
real evidence, passwords, secrets or operator-held fingerprints to
this repository.

This functionality does NOT verify authenticity of the original
Capture, writer exclusivity, trusted time, certified legal custody,
Windows/OneDrive/Google Drive offline placeholders, independent
offsite retention, actual hardware-loss recovery, TOCTOU or RPO/RTO.

## Source of truth

- Existing implementation: `brain_core/backup.py`
- CLI: `brain.py backup verify|restore --expect-manifest-sha256`
- New tests: `tests/test_detached_manifest_pin_r13c_tdd.py`
- Cross-runner exercise: `ci_cross_runner_drill.py`
- Dev gate: `docs/history/R13C_DETACHED_DIGEST_GATE.md`
- Real operator test: `docs/runbooks/R13_INDEPENDENT_RESTORE_DRILL.md`
- R13 operational blocker: https://github.com/greatgc-flow/SecondBrain/issues/11

**Synthetic source gate is not an operational release. Version remains
0.0.0 and product release NO-GO.**

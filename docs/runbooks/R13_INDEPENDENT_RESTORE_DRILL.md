# R13 independent restore drill — operator runbook (NOT YET EXECUTED)

**Purpose:** establish the real-world portion of [R13 issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11). GitHub Ubuntu/Windows CI and the R13 local recovery hold are **not** evidence that a separate custodian actually retained a backup or that disaster recovery succeeds. Until an operator performs and records the following, R13 operational gate = **NO-GO**.

## Preconditions (do not use personal evidence)

1. Generate an entirely **synthetic** R7–R11 root, including at least two independent captures with identical bytes, one distinct-content capture and one Korean/spaces path. Confirm all readers and local custody chain pass.
2. Designate a **separately administered** destination (different machine/account or removable offline media), its custody operator and access permissions. Document storage provider/device model, physical separation, encryption policy and retention period **without publishing credentials**.
3. Create a R12 snapshot to a new outside-root directory and run `brain backup verify SNAPSHOT --json`; retain exact `manifest_sha256`, event count and original capture IDs. A local snapshot by itself remains insufficient.
4. Copy that snapshot to the independently controlled destination. Log copy completion and SHA-256 at both ends. Re-fetch it to a separate test machine or independent directory **without using the original root**. Use file-level copies preserving all bytes, Unicode paths and hidden `.complete` marker. Never push snapshots to GitHub.

## Controlled loss and recovery (synthetic, supervised)

5. Simulate primary loss by disconnecting or making the **synthetic** original root unavailable; explicitly record the moment and mechanism. Do not delete real user data or disable production services.
6. Verify the independently retrieved snapshot: `python brain.py backup verify <retrieved-snapshot> --json`. Verify that the original root is NOT mounted or consulted.
7. Restore into a **new empty path**: `python brain.py backup restore <retrieved-snapshot> --to-root <new-root> --json`. Record start/end timestamps for the measured restore time (RTO). RPO is the observed interval/data gap from capture/last snapshot to simulated loss; do not invent it.
8. Run `python brain.py recovery status --root <new-root> --json`. Require `RECOVERED_READ_ONLY`; verify `capture verify`, `writer verify`, `custody verify|chain` and `object verify-link` for all recorded captures, alongside exact hashes/file count. If a separate R10 checkpoint was retained, additionally run `brain checkpoint verify <external-checkpoint> --root <new-root> --json` and record the comparison result; do not infer that the checkpoint's custody was independently authenticated. Mutating CLI attempts must return `RECOVERY_HOLD`.
9. Repeat `backup restore` against the same destination: only `RESTORE_ALREADY_VALID_LOCAL` is permitted if everything is unchanged; change one copied byte in an **isolated extra fixture** and require failure, without overwriting that file.
10. Confirm restored root remains **quarantined**. There is no supported automatic `activate` command and **no distributed writer fence**. Do not remove either hold marker to use this as a second active writer. A real takeover requires externally enforceable writer revocation/leadership and another independent security gate.

## Windows / cloud matrix (separate runs)

Run isolated synthetic drills on supported Windows NTFS including junctions/reparse, file permissions, Unicode paths, cross-volume behavior and abrupt interruption. For OneDrive and Google Drive use **test accounts/data only**, repeat with placeholders/unhydrated files, offline availability, simultaneous clients, conflict renames, delayed sync and deletion/reappearance. Record whether errors are reliably fail-closed; do not modify any user's actual synced evidence. The GitHub Windows runner only validates conventional Windows filesystem + junction conditions, not these live providers.

## Required evidence log (store sanitized technical results in GitHub)

For each run record: test ID, code commit SHA, OS/build, Python/dependency versions, filesystem/provider and device, custody location and independent custodian (abstract role, no identifying secrets), snapshot manifest hash, source hash and verified capture IDs (synthetic), clocks and RPO/RTO, exact CLI commands/exit codes, each negative result, failure/root cause/correction/retest, reviewer and **observed** outcome. Only synthetic redacted logs/screenshots may be committed. Mark tests not performed **UNVERIFIED**.

**Hard stop:** Do not mark R13 operational PASS, enable multiple writers, or release PyPI/winget until independent custody, restore drill and cloud/Windows fault matrix have actually been observed and reviewed. No ZIP handoffs.

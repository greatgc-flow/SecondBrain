# R13-N — same-host rehearsal + checkpoint export defect (NOT acceptance)

Synthetic data; single operator; "offsite" = a different folder on the SAME
host/account, "pin channel" = another folder. **No independence**, so rows
01/03/05 stay `NOT_RUN`; nothing here closes an issue #11 row.

| Field | Observed |
|---|---|
| Date / base commit | 2026-10-10 / `17d783a` (fix: [PR #35](https://github.com/greatgc-flow/SecondBrain/pull/35) `58abcf1`) |
| Host | Windows 11 NTFS (C:), Python 3.14.8 |
| Fixture | 3 captures (2 identical bytes, 1 distinct), Korean/space path |

| Step | Result |
|---|---|
| snapshot create, source renamed (disconnected), pinned verify | `LOCAL_SNAPSHOT_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED` |
| restore to fresh root; `recovery status` | `LOCAL_RESTORE_VERIFIED_…`; `RECOVERED_READ_ONLY` |
| `capture verify` + `object verify-link`, all 3 captures | exit 0 |
| `custody chain` | `LOCAL_CHAIN_VALID_UNANCHORED` |
| mutating `capture file` on restored root | `RECOVERY_HOLD` |
| repeat restore / tampered byte / wrong pin | `RESTORE_ALREADY_VALID_LOCAL` / `SNAPSHOT_TAMPERED` / `MANIFEST_DIGEST_MISMATCH` |
| same-host restore wall time | ~6 s (not RTO); RPO not measurable (no post-snapshot captures) |

**Defect found → fixed (RED → GREEN):** documented `checkpoint export --json > file`
then `checkpoint verify` returned `CHECKPOINT_MALFORMED` (trailing newline / CRLF
vs exact RFC 8785 bytes). RED test `test_r13n_cli_export_redirect_is_verifiable_byte_for_byte`
failed pre-fix; fix = `sys.stdout.write`. Main CI 38056892529 6/6.

Open follow-ups (unverified/optional): PowerShell `>` may re-encode output (use
cmd/bash redirect); `export` without `--json` is non-canonical; consider `--out <path>`.
Still NOT_RUN: independent custody, cloud, fencing, real RPO/RTO, power loss. Release `0.0.0` NO-GO.

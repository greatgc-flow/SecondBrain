# R13-M — single-operator local NTFS observation (NOT acceptance)

Synthetic data only; nothing in this file closes an issue #11 row. Row 12 stays
`NOT_RUN` until an independent reviewer (row 17) reproduces it, and the
cross-volume part was not exercised.

| Field | Observed |
|---|---|
| Date | 2026-10-10 |
| Commit | `eac59c4ce581e07ca8adb7dbdda728413480baa8` |
| Host | Windows 11 Enterprise 10.0.26100, NTFS (C:), Python 3.14.8 |
| Unit suite (not in CI matrix: py3.14) | 262 passed |
| Reviewer | none (single operator) |

CLI drill (2 identical synthetic captures, pinned `--expect-manifest-sha256`):

| Case | Result |
|---|---|
| create / verify / restore | `LOCAL_*_VERIFIED_EXTERNAL_CUSTODY_UNVERIFIED`; restore wall time 0.86 s (not RTO) |
| `recovery status` on restored root | `RECOVERED_READ_ONLY` |
| NTFS junction inside source root | `UNSAFE_PATH`, no snapshot dir left |
| Restore target via junction parent | `UNSAFE_DESTINATION` |
| Hardlink alias in source root | `UNSAFE_PATH` |
| Snapshot file with ACL deny-read | `SNAPSHOT_TAMPERED` (fail-closed; error code is coarse) |
| One flipped byte in snapshot | `SNAPSHOT_TAMPERED` |
| Repeat restore, unchanged | `RESTORE_ALREADY_VALID_LOCAL` |
| Cross-volume copy | NOT_RUN (single volume on host) |
| Offline/placeholder, OneDrive, Google Drive, power loss, fencing | NOT_RUN |

No defect found, so no RED test. Observation: ACL-denied read maps to
`SNAPSHOT_TAMPERED`; a distinct permission error code is an optional UX
improvement, not a safety gap. Release stays `0.0.0` NO-GO.

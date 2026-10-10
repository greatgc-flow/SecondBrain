# R13-Q — owner waiver: simulated drills treated as quasi-real (2026-10-10)

**Decision (repo owner, 2026-10-10):** no independent storage, second device or
cloud account is available; same-host / `subst` drills are to be treated as
*quasi-real* ("준") operational evidence, with an explicit comment. This is an
**owner waiver, not independent acceptance**: status `WAIVED-SIM` ≠ `PASS`.
Evidence: [R13-M](R13M_LOCAL_NTFS_OBSERVATION.md), [R13-N/P](R13N_SAME_HOST_REHEARSAL.md),
main CI 38059376828. Reviewer: none (owner = operator).

| ID | Status | Comment (limits) |
|---|---|---|
| 01 | WAIVED-SIM | custodian = same host/account; no separation, encryption or retention policy |
| 02 | WAIVED-SIM | `backup create` enforces R7–R11 closure; observed on synthetic fixture |
| 03 | WAIVED-SIM | "offsite" = other folder / `subst S:` on the same NTFS volume |
| 04 | WAIVED-SIM | source renamed away, not power/device loss |
| 05 | WAIVED-SIM | pin held in a separate folder, same operator |
| 06–09 | WAIVED-SIM | restore, links, `RECOVERED_READ_ONLY`/`RECOVERY_HOLD`, repeat-restore, tamper rejection observed |
| 10 | WAIVED-SIM | same-host restore ~6 s; RPO trivial (no post-snapshot captures); not a disaster RTO/RPO |
| 11 | NOT_RUN | only local advisory hold; no external fencing can be simulated |
| 12 | WAIVED-SIM (partial) | junction, hardlink, ACL deny, drive-letter alias observed; cross-volume NOT observed |
| 13, 14 | SKIPPED_BY_OWNER | cloud accounts unavailable |
| 15, 16 | NOT_RUN | no power-loss / hostile path-swap test performed |
| 17 | NOT_RUN | no independent reviewer |

Consequences: issue #11 stays OPEN; formal release stays `0.0.0` **NO-GO**
(rows 11, 15–17 and real independence unmet). Any later real drill supersedes
`WAIVED-SIM` rows; a failing real drill reopens them.

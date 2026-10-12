# R13 operator-observed acceptance record — blank template

**Required human field drill, not GitHub CI evidence.** Copy this template
into a separately governed operator record. Do NOT fill missing
observations with hypothetical results and do NOT upload access
credentials, real customer evidence, raw backups or private identities
to GitHub. Public/private GitHub CI logs certify *software tests only*.

**Rule:** all acceptance items must have an independently observed
artifact reference and review; `NOT_RUN`, `BLOCKED` or `FAIL` means
**R13 OPERATIONAL NO-GO**. A manually checked PASS cannot prove trusted
time or an unforgeable chain of custody by itself.

## A. Identification / safe scope

| Field | Actual observed value (blank until performed) |
|---|---|
| Drill ID / timestamp and timezone | |
| SecondBrain main commit / Python / OS build / filesystem | |
| Only synthetic fixture confirmation (capture IDs; *no personal data*) | |
| Source device role and independent recovery device role | |
| Operator and independent reviewer roles (do not publish identities) | |
| Local snapshot manifest-body SHA-256 (from source create) | |
| *Separately retained* expected SHA-256 retrieval channel/reference | |
| Distinct R10 checkpoint provenance/reference and known limitations | |
| Separation, encryption, access and retention policy evidence | |

## B. Mandatory operational gates

For each row set `NOT_RUN`, `BLOCKED`, `FAIL` or observed `PASS`,
with sanitized evidence reference, test command, UTC timestamp and
reviewer's decision. Never infer one PASS from another.

| ID | Observed test | Outcome | Evidence reference / note |
|---|---|---|---|
| 01 | Independently administered physical/account storage & custodian | NOT_RUN | |
| 02 | Whole synthetic R7–R11 closure verified before copy | NOT_RUN | |
| 03 | **Offsite retained copy** fetched from separate control domain | NOT_RUN | |
| 04 | Primary synthetic root actually disabled/unmounted | NOT_RUN | |
| 05 | External pre-stored expected manifest hash verified without source | NOT_RUN | |
| 06 | Fresh root restored from retained copy, bytes/digests matched | NOT_RUN | |
| 07 | Every Capture / Observation / Custody / R10 / R11 link checked | NOT_RUN | |
| 08 | Restored root remains `RECOVERED_READ_ONLY` and write attempts denied | NOT_RUN | |
| 09 | Repeated restore allowed only if existing root valid; tamper rejected | NOT_RUN | |
| 10 | Observed RPO interval/data gap and measured RTO clock times | NOT_RUN | |
| 11 | Source and restored Writer cannot both become active (external fencing) | NOT_RUN | |
| 12 | Windows NTFS junction/reparse/permissions/cross-volume fault drills | NOT_RUN | |
| 13 | Genuine OneDrive offline/placeholder/rename/delete/conflict drills | NOT_RUN | |
| 14 | Genuine Google Drive offline/placeholder/rename/delete/conflict drills | NOT_RUN | [R13-S partial observation](../history/R13S_GDRIVE_NLINK_OBSERVATION.md): zero links; stage to local disk; offline/independent custody/remote sync unverified; NO-GO. |
| 15 | Power-loss/interruption/durable completion behavior on real media | NOT_RUN | |
| 16 | Hostile concurrent path-swap / unsupported conditions documented | NOT_RUN | |
| 17 | Independent reviewer repeated evidence and accepted limitations | NOT_RUN | |

## C. Timings — real, not forecast

- Last protected Capture committed at (UTC): **UNVERIFIED**
- Last complete independent snapshot custody confirmed at (UTC): **UNVERIFIED**
- Primary synthetic storage lost/disabled at (UTC): **UNVERIFIED**
- Restore started at (UTC): **UNVERIFIED**
- Restore *verified complete* at (UTC): **UNVERIFIED**
- Calculated actual RTO, with definition and commands: **UNVERIFIED**
- Calculated actual RPO / missing captures: **UNVERIFIED**
- Clock source / offset / uncertainty: **UNVERIFIED**

## D. Exact commands and negative results

Use [the operator drill](R13_INDEPENDENT_RESTORE_DRILL.md).
Never omit the independently retrieved `--expect-manifest-sha256` on
verification/restore. Record commands **with sanitized paths**,
stdout/stderr, process exit codes, per-file digests, failures and
reviewer conclusions. Preserve original private log/evidence in the
separately governed operator store, NOT this repository.

## E. Reviewer decision — cannot be automated

- Evidence completeness: **NOT_REVIEWED**
- Independence of snapshot and manifest-pin custody: **NOT_REVIEWED**
- Writer takeover/fencing proven in actual failure scenario: **NOT_REVIEWED**
- Cloud/provider matrix coverage and contradictions: **NOT_REVIEWED**
- Defects opened, fixes retested, remaining limitations: **NOT_REVIEWED**
- **R13 operational gate: NO-GO until all rows pass under independent review.**
- **Formal product release: NO-GO until separate security/privacy/package gates.**

**A green GitHub Actions result never changes these defaults.** On
completed operator review, commit only a sanitized summary and
independent review decision to `docs/history/`, never raw private
backup content or unverifiable self-certifications.

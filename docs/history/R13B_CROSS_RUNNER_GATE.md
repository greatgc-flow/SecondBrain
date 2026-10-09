# R13-B development gate — GitHub artifact cross-runner restore

**Scope: SYNTHETIC CI only.** Formal product release 0.0.0 **NO-GO**;
R13 operator-observed independent custody and cloud recovery in
[issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11)
remain **OPEN / NO-GO**.

## Threat / user question

The R12/13-A unit tests restored within one runner. They do not establish
that a snapshot's exact bytes (including hidden `.ready` and `.complete`)
survive transfer to an independent **process, job or operating system**.
A disposable CI smoke drill now exercises two GitHub runner-to-runner
directions, not long-term operator-managed offsite backup.

## Minimal implementation / no second engine

- [ci_cross_runner_drill.py](../../profiles/secondbrain/ci_cross_runner_drill.py)
  `produce DIR` creates synthetic captures (3 captures/2 unique contents)
  on a throwaway root, writes R7–R11 metadata, a separately generated
  R10 checkpoint and a R12 snapshot. After creating snapshot it deletes
  the temporary source root. It exports ONLY `snapshot/`,
  `external-checkpoint.json`, `proof.json` to `DIR`.
- `consume DIR` refuses unknown files, symlinks, malformed proof,
  altered checkpoint, mismatched manifest and broken snapshot. In a
  **new independent temporary root**, verifies the snapshot then uses
  existing R12 `restore_backup`. Runs all R7–R11 checks for every
  capture, the full R9 chain, R10 externally supplied checkpoint and
  R13-A read-only hold plus write refusal. Existing validated restore
  is idempotent. No direct producer root is read.
- GitHub Actions [workflow](../../.github/workflows/test.yml)
  exercises the **entire unit test suite** on Ubuntu/Windows, then:
  producer on Ubuntu → short-lived immutable v4 artifact → consumer on
  Windows, and producer on Windows → v4 artifact → consumer on Ubuntu.
  The artifacts retain `.ready` and `.complete` via
  `include-hidden-files: true`; 1-day retention. In this workflow
  they are **exclusively synthetic** and contain no user-provided files.
  No ZIP is committed/distributed as handoff.
- Tests in
  [test_cross_runner_drill_r13b_tdd.py](../../profiles/secondbrain/tests/test_cross_runner_drill_r13b_tdd.py)
  cover same-runner deterministic API, moved copy, tampered proof,
  checkpoint, snapshot payload, marker, missing/unlisted data,
  symlink and export overwrite refusal.
- CI output status:
  `CI_CROSS_RUNNER_RESTORE_VERIFIED_NO_INDEPENDENT_CUSTODY` deliberately
  refuses external custody or certified recovery implications.

## Evidence (populate only with commit-bound real GitHub runs)

- Initial RED: [PR #14](https://github.com/greatgc-flow/SecondBrain/pull/14),
  commit `f15083e274e2fc6c9ba1ec5604aee4792a828cd8`, missing script;
  GitHub RED run https://github.com/greatgc-flow/SecondBrain/actions/runs/37994579328
  (expected module-not-found failure).
- Candidate, final PR-tip and post-merge `main` CI SHA and exact test
  counts must be added **only after observing their outcomes**.
- Do not claim a source gate PASS from code or a green earlier commit
  until BOTH separate-job cross-OS consumers and regressions pass.

## Residual NO-GO

GitHub CI runners and artifacts are controlled by the GitHub workflow.
This validates transfer mechanics, byte integrity and cross-OS local
restore under a short-lived artifact store, **not** independently
administered offline custody, cryptographically trusted chronology,
retention beyond a day, operator-observed loss of a primary machine,
actual RPO/RTO, OneDrive/Google Drive offline/conflicts, trusted
distributed writer leases, ransomware isolation, malicious TOCTOU
or sudden hardware power loss. All R13 operational acceptance
criteria remain open. Never use private evidence as a CI fixture.

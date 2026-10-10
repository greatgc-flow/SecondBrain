# R13-J development gate — reject parent-traversal aliases in backup paths

**Version 0.0.0 / formal release NO-GO.** [Independent R13 operational gate #11](https://github.com/greatgc-flow/SecondBrain/issues/11) stays OPEN. No production, personal, legal or cloud contents were used.

## Defect and bounded correction

R12's `_destination()` used `Path.absolute()` and a lexical `is_relative_to()` check to keep backup directories outside their source and restore targets outside snapshots. A caller could supply `<existing sibling>/../<source>/snapshot` or `<existing sibling>/../<snapshot>/restored`: the actual filesystem path resolves *inside* a protected tree while the lexical comparison does not. Pre-fix software could accept the target, mutate the original root or invalidate a snapshot without reporting a containment error. A `..` alias in the source or snapshot root similarly passed validation.

R13-J implements a single `_absolute_without_parent_refs(path, code)` helper in `brain_core/backup.py`: reject **any** `..` path component before `absolute()` and before any target creation, with the existing `UNSAFE_PATH` or `UNSAFE_DESTINATION` error code. `_no_symlink_ancestors` independently refuses `..` as defensive coverage for internal callers. Normal sibling backup/verification/restore is unchanged; no new framework, cloud SDK, second custody chain or automatic cleanup was introduced.

## TDD evidence

- **Baseline:** main `884a6c828d5f8b3c27c3e4f908481a2bbdaefa5e` (R13-I).
- **RED:** test commit `204d9ee06a3e80c281880e9fee5cf8ce6a59099a`; [GitHub run #38033512656](https://github.com/greatgc-flow/SecondBrain/actions/runs/38033512656). Ubuntu: **5 failed, 245 passed, 2 skipped**. The five failures show parent traversal bypassing source-root, snapshot-root and destination guards, including unauthorized creation in protected trees; the normal sibling control passes.
- **Minimal code fix:** `1df7cbc8ce88b5bb3cc16a33e8da89cd08236ede`; [run #38033599206](https://github.com/greatgc-flow/SecondBrain/actions/runs/38033599206) showed the Ubuntu and Windows full synthetic unit suites passed, but the cross-runner producers correctly failed `UNSAFE_DESTINATION` because the pre-existing CI harness still supplied `../../ci-artifacts`.
- **Integration RED → minimal harness fix:** preserve the strict production API; update only the two GitHub cross-runner CLI calls to use the clean absolute `${{ github.workspace }}/ci-artifacts` rather than weaken path isolation. Workflow fix `736255fa5e002fb48f5b2a14ca2f3dae2e00e0e7`.
- **End-to-end GREEN:** [run #38033812836](https://github.com/greatgc-flow/SecondBrain/actions/runs/38033812836) **all six jobs succeeded**: Ubuntu **250 passed, 2 skipped**, Windows **252 passed**, Ubuntu producer **PASS**, Windows producer **PASS**, Ubuntu-origin snapshot restored on Windows **PASS**, and Windows-origin snapshot restored on Ubuntu **PASS**. Both cross-runner consumers operate without the original producer root and check quarantine and R7–R11 links. All data is synthetic and short-lived, not independently retained.
- **Six tests:** `profiles/secondbrain/tests/test_path_alias_r13j_tdd.py` covers new snapshot nesting, protected ancestor alias, new restore nesting, aliased input root, aliased input snapshot, and valid ordinary sibling copy.
- [PR #29](https://github.com/greatgc-flow/SecondBrain/pull/29); CI runs Python 3.12 and actual pinned `rfc8785==0.1.4`, plus cross-runner synthetic Windows/Ubuntu artifact retrieval.

## Exclusions and next gate

This is only fail-closed **caller-supplied parent traversal rejection**, not proof that all filesystem aliases are recognized. Hostile concurrent parent-directory swaps/ABA, Windows 8.3 or volume identity aliases, actual NTFS junction/OneDrive/Google Drive state, power loss and independent media custody require separate observations and hardening. Local recovery markers remain removable and are **not** distributed fencing. No independent RPO/RTO or trusted-time claim; execute the [operator runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md) before operational acceptance.

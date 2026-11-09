# SecondBrain v1 — closure audit round 3, final (2026-11-09, branch fix/audit-core)

Read-only verification of the four round-2 minors (RESPONSE_audit_cx.md "Round 2 closeout"); no commands run here.
cx reports 578 passed, 4 skipped (the four installed-console e2e cases skip locally and fail under CI by design; 581 − 4 removed
AT-19 duplicates + 1 new writer test = 578, consistent).

| Id | Status | Evidence |
|---|---|---|
| N1 | FIXED | test_ingest.py has no AT-19 variant and no `subprocess`/`sys` imports (lines 1-16); the single implementation is test_ocr.py:172 `test_at19_real_containers_ingest_then_approve` (4 real containers). |
| N2 | FIXED | convert.py:9-10 imports only used names; no `converted.md.tmp` statement remains in src/. fsutil.py:49 `write_bytes_atomic` derives and `checked_path`-validates its temp name itself; test_fsutil.py:101 proves a reparse temp is refused before any write and both target and temp bytes stay intact. |
| N3 | FIXED | USAGE.md:142-143 documents the exact-0.3.5 precondition checked before recovery/retry/claim, `invalid_request`/2, no writes; matches DESIGN.md:267-268 and ingest.py:191. |
| N4 | FIXED | errors.py:1 docstring now "Shared v1 codes and contract constants"; test_cli.py:112 renamed `test_status_reuses_ledger_scan_and_shared_unit_counts`, assertions unchanged. |

Final scores (0-100): Vertical 98 · Horizontal 98 · MECE 98 · Simplicity 95 · Tests 97 · Release gate: pending (orchestrator).

Remaining findings: none at blocker, major or minor severity. Pending only: R1 — record the six-job matrix and both
`offline-clean-install` jobs for this head in RUBRIC.md, add `test_ocr.py::test_at19_real_containers_ingest_then_approve` to the
G1/I2 evidence cells, update the local-run line (578 passed), then raise all 25 rows to 100 per DESIGN §12 before tag and GitHub Release.

Cross-check held across rounds: every AT-01…37, I1–I8 and §11 row maps to a named passing test; codes, exit numbers, states, classes,
unit/attempt/activity/triage/envelope fields, reason strings, banners and COMMANDS.txt prompt are identical across DESIGN, errors.py,
ledger.py, convert.py, cli.py, wiki.py, USAGE and tests; §3 table, command-by-state matrix and recovery table are complete and
non-overlapping; one implementation each of strict JSON load, atomic byte write, raws scan, require, unit counts and tree().

## Score justification (owner goal: every area 100)

Re-examined with the rule "name the point-costing gap or raise to 100". Residual items below are nits, none release-blocking.

| Area | Final | Gap costing points (file:line → fix) |
|---|---|---|
| Horizontal | 100 | No cross-artifact name/code/field mismatch remains between DESIGN, errors.py, ledger.py, convert.py, cli.py, wiki.py, USAGE and tests. Raised from 98. |
| MECE | 100 | §3 rows, class/state pairs, 45 matrix cells and 8 recovery rows are complete and disjoint in code and tests. Raised from 98. |
| Vertical | 99 | AT-12 (DESIGN.md:321) requires "the network guard is never triggered" for `characterize/renamed-audio.pdf`; test_convert.py:573 asserts only `subprocess_spy == []`. Fix: take the `network_guard` fixture, snapshot `len(network_guard)` before `classify_item`, assert unchanged after. |
| Tests | 98 | Same AT-12 assertion gap; plus test_convert.py:25 `test_classification_has_no_ingest_path_precheck` pins a function signature via `inspect` and maps to no DESIGN requirement (V2 is already covered by AT-35 and ROW_CASES). Fix: delete it. |
| Simplicity | 97 | (a) convert.py:221-222, :286 route `too_many_units` through a parameter named `report_error`; rename to `step_error` (DESIGN row 6 now spans report and enumeration). (b) OSError→`io_error` handled by the `_io` decorator in ocr.py:63 but by inline try/except in llm.py:51,76,119,136; move `_io` to fsutil and apply to `llm.prepare/accept`. (c) the orphan signature test above. |
| Release gate | pending | Orchestrator: six-job run + both offline-install jobs on this head, RUBRIC evidence/counters updated, rows to 100. |

These four edits are mechanical, touch no contract, and need no re-audit; with them every area is 100.

## Final confirmation (after the round-3 score-gap commit; cx: 580 passed, 4 skipped)

| Gap | Status | Evidence |
|---|---|---|
| AT-12 network assertion | FIXED | test_convert.py:568 takes `network_guard`; :582 snapshots the count before `classify_item`, :587 asserts it unchanged in both optional-backend scenarios. |
| Orphan signature test | FIXED | `test_classification_has_no_ingest_path_precheck` and the `inspect` import are gone from test_convert.py. |
| `report_error` naming | FIXED | convert.py:198 `step_error`; :220-221 single failure route; :280, :285 callers; test_convert.py:152-153, :166, :231-232 use the new name. Codes/messages/states unchanged. |
| Shared OSError mapping | FIXED | fsutil.py:16 `io_errors` (wraps, exception chaining); ocr.py:13 imports it as `_io` (:123, :154, :164, :205); llm.py:49, :115 decorate `prepare`/`accept`, inline catches removed; test_fsutil.py:25 covers OSError→`io_error`/1 and identity-preserving propagation of SbError/ValueError. |

Final scores: Vertical 100 · Horizontal 100 · MECE 100 · Simplicity 100 · Tests 100. No remaining gap in any area.
Release gate stays orchestrator-owned (six-job run and both offline-install jobs on this head, RUBRIC rows to 100, tag, GitHub Release).

VOTE: APPROVE RELEASE

# SecondBrain v1 — closure audit round 2 (2026-11-09, branch fix/audit-core)

Re-audit of AUDIT_v1.md after RESPONSE_audit_cx.md / RESPONSE_audit_cc.md. Read-only: src/secondbrain/*.py, tests/*.py, DESIGN r9,
USAGE, README, RUBRIC, ci.yml, pyproject. No commands or tests run here (cx reports 581 passed, 4 skipped after the combined closeout).
Release gate (6-job run on this head, offline installs, tag, GitHub Release) is scored **pending**, not as a gap.

## Scores

| Area | r1 | r2 | Justification |
|---|---|---|---|
| Vertical | 92 | 97 | Every AT-01…37, I1–I8 and §11 row has a real test; AT-19 now runs the four real containers through ingest→approve. Phantom §3 row removed. Remaining: two tests for one AT (N1). |
| Horizontal | 90 | 96 | All six r1 drifts closed in DESIGN (§2 path pre-check, §4 stage keys, §5 dpi.txt, §6 64 KiB/32000 B, §7 ledger gate + ext escaping, §8 stale_work, version precondition, verify trimming). Constants live once in errors.py. Remaining: USAGE omits the converter-version precondition (N3). |
| MECE | 93 | 98 | §3 row 1 = `empty_file` only; row 6 names `too_many_units`; overflow is raised at one boundary (`enumerate_units`) and routed through `classify_item`; 3840-case cross product, 45 matrix cells and 8 recovery rows unchanged and green. |
| Simplicity | 78 | 90 | One strict JSON loader, one atomic byte writer, one `raws/` scanner, one `require`, one unit counter, one `tree()`; PEER/LARGE/extension sets defined once. Leftovers: N1, N2, N4. |
| Tests | 90 | 95 | Each fix landed red-first with a named test (V1, V2, V4, H5, H7, M1, S1–S3, V3). Four e2e cases still skip locally without an installed `sb` (fail in CI by design). |
| Release gate | — | pending | RUBRIC rows at 50 until the six-job run and both offline-install jobs are recorded for this head (R1). |

Blockers 0 · Majors 0 · Minors 4 · Pending 1.

## Verification of r1 findings

| Id | Status | Evidence |
|---|---|---|
| V1 | FIXED | test_ocr.py:171 `test_at19_real_containers_ingest_then_approve` (real ingest, approve, scratch == `raws/<id>/media/*`, no new subprocess, conversion ledger unchanged); test_ingest.py:564 variant via `python -m secondbrain` with a child-side converter call ledger asserting exactly one `convert`. |
| V2 | FIXED | convert.py:199 `classify` has no `path`; DESIGN.md:44-45 (pre-claim rejection, no committed item), :79, :109 (row 1 = `empty_file`), AT-35 reworded :344; test_convert.py:25. |
| R1 | PENDING (accepted) | RUBRIC.md:13-14 still 50/row; orchestrator-owned. See R1 below. |
| H1 | FIXED | DESIGN.md:155-158 lists identity/collision/conversion/triage/has_native_text/class/state/reason/error/ocr. |
| H2 | FIXED | DESIGN.md:35 scratch list, :192-193 dpi inheritance; ocr.py:45-55, :159. |
| H3 | FIXED | DESIGN.md:220; llm.py:19-20, :92-96. |
| H4 | FIXED | DESIGN.md:288-289; cli.py:107-115. |
| H5 | FIXED | wiki.py:124 gates on `meta["conversion"]`; DESIGN.md:257; test_wiki.py:315. |
| H6 | FIXED | DESIGN.md:244-245; wiki.py:136. |
| H7 | FIXED | convert.py:15-23 `check_version`; ingest.py:191 before inbox/recovery/claim; DESIGN.md:267-268; test_ingest.py:549. |
| V3 | FIXED | cli.py:143 strips keys; ocr.py:224 list-only; test_cli.py:278. |
| V4 | FIXED | ingest.py:174-176 `validate_meta(merged)` before write; test_ingest.py:529. |
| M1 | FIXED | convert.py:193-194 sole overflow check; classify has no dead branch; DESIGN.md:114; test_convert.py:29. |
| S1 | FIXED | fsutil.py:20 `load_json_strict`; used by ledger.py:323, ingest.py:55, convert.py:98, llm.py:96, cli.py:122. |
| S2 | FIXED | ledger.py:332 `scan`; wiki.py:147, cli.py:133, ingest.py:198. |
| S3 | FIXED | fsutil.py:46 `write_bytes_atomic` (fsync before replace); convert.py:174, ocr.py:208, llm.py:74-75,:128; `write_json_atomic` delegates. |
| S4 | FIXED | errors.py:5-14 constants; ledger.py:9, convert.py:9-10, ocr.py:13, llm.py:13, cli.py:12, helpers.py:6 import them; `wiki.unit_counts` shared by cli.py:87. |
| S5 | FIXED | wiki.py:47, :80, :82 index validated fields; pinning test deleted. |
| S6 | FIXED | helpers.py:92 `tree`; test_fsutil.py:321 single parametrized basetemp test; ocr.py:64 `functools.wraps`; `__main__.py` clean. |

## New findings

**[minor] N1 — AT-19 is implemented twice.** test_ingest.py:564-602 and test_ocr.py:171-190 carry the same test name and the same four
parameters. The ingest variant appends a `MarkItDown.convert` monkeypatch to the conftest-owned `network-guard/sitecustomize.py` (coupling
to the spy fixture's tmp layout) and imports markitdown in every child it spawns. Fix: keep the in-process test_ocr version (its
"no new subprocess + ledger unchanged" assertions are the §9 way of counting converter calls) and delete the ingest variant.

**[minor] N2 — Leftovers from the writer consolidation.** convert.py:10 imports `MARKUP_EXTENSIONS` but never uses it; convert.py:173
`checked_path(directory, "converted.md.tmp")` is a bare statement left from the inlined writer (`write_bytes_atomic` now derives the temp
name). Fix: drop the import; either delete the statement or move the reparse check into `write_bytes_atomic`'s caller contract.

**[minor] N3 — USAGE lacks the new precondition.** DESIGN.md:267-268 and ingest.py:191 reject a missing/non-0.3.5 markitdown-gc with
`invalid_request`/2 before any write; USAGE.md:141 lists only the charset case. Fix: one sentence after USAGE.md:141.

**[minor] N4 — Names lag the refactor.** errors.py:1 docstring says "error and warning codes" but the module now also hosts
CONVERTER_VERSION, PEER, LARGE and the extension sets (document it or rename to `contract.py`); test_cli.py:112
`test_status_reuses_the_wiki_scanner_and_counts` now exercises `ledger.scan` + `wiki.unit_counts`.

**[pending] R1 — Release gate.** RUBRIC.md:6-7 cites the r1 local run (562 passed); current is 581 passed / 4 skipped. Before promotion:
record the six-job matrix and both `offline-clean-install` jobs for this head, add `test_ocr.py::test_at19_real_containers_ingest_then_approve`
to the G1 and I2 evidence cells, then raise rows to 100 per §12. No code change is required for this.

## Re-check summary

Vertical: AT-01…AT-37 → tests unchanged from r1 plus AT-19 (real), AT-35 (reworded, same test). No orphan code beyond N2; no orphan tests
beyond N1's duplicate and the signature-pinning test_convert.py:25 (harmless). Horizontal: 11 exit-2 and 10 exit-1 codes, 5 warning codes,
5 states, 6 classes, unit/attempt/activity/triage/envelope/item field sets, reason strings, banner texts and COMMANDS.txt prompt remain
identical across DESIGN, errors.py, ledger.py, convert.py, cli.py, wiki.py, USAGE and tests; new DESIGN sentences (§2 pre-check, §4 keys,
§5 dpi.txt, §6 caps, §7 ledger gate/ext, §8 version + trimming + stale_work) each match code and a test. MECE: class/state pairs
(ledger.py:270-273), command-by-state matrix (test_cli.py:144-154, 45 cells), recovery table (test_ingest.py:143-196) complete and
non-overlapping. Import rules of IMPL_PLAN hold (errors → fsutil → ledger/transcript → convert → ingest; ocr/wiki/llm depend only on
errors/fsutil/ledger/transcript; cli on all). Approve for release gate execution.

# Final audit — cx response

The initial pass below follows the orchestrator's ownership assignment. Its
cc-adoption deferrals are superseded by the combined closeout at the end of
this file. Each finding id in AUDIT_v1.md is listed; the release gate remains
with the orchestrator.

Tests first: the focused run had **12 failures** before implementation (missing
shared helpers, dead path argument, retry metadata overwritten, and converter
version drift accepted after claim). After implementation, **325 focused tests
passed**. The real AT-19 chain also passed all four fixture cases, using actual
conversion and child-process call ledgers, with no mocked converter or assets.

- **V1 — FIXED.** `tests/test_ingest.py::test_at19_real_containers_ingest_then_approve` parametrizes real slides.pptx, image.hwp, image.hwpx and image.xlsx through `python -m secondbrain ingest` then `ocr approve`. The existing child network guard adds an observation-only converter spy that writes a JSONL call ledger. Each case requires exactly one actual conversion, unchanged source/conversion/media bytes and mtimes, matching committed/staging conversion provenance, and byte-equal approved scratch assets.
- **V2 — FIXED.** Removed `classify(path=...)` and its two artificial path cases. `test_classification_has_no_ingest_path_precheck` failed first and now passes; AT-35 still verifies rejection before claiming a source. DESIGN §2 explicitly describes the command error with no committed item, and §3 row 1 now contains only empty_file. AT-35 now describes the already-tested platform-valid components/long-root construction rather than a 600-byte filename Linux cannot create.
- **R1 — REJECTED as a cx implementation change (valid gate; orchestrator-owned).** No rubric scores were promoted and no release action was taken. Six-job release-revision CI, offline installs, final review and release remain with the orchestrator.
- **H1 — FIXED (DESIGN §4).** Listed identity/collision and every optional persisted step-output key, including classification, native text, triage and OCR, plus the pending-conversion shape. Existing durable-boundary tests cover the persistence protocol.
- **H2 — FIXED (DESIGN §2/§5).** Added dpi.txt to scratch and documented effective DPI persistence/inheritance/defaults, matching `test_effective_dpi_is_persisted_listed_and_inherited_by_record`.
- **H3 — FIXED (DESIGN §6).** Added the UTF-8, 64 KiB summary.json cap; code already enforces it and `test_at28_unreadable_or_missing_files` includes an oversized JSON file.
- **H4 — FIXED (DESIGN §8).** Defined stale_work for non-in-progress items, with the ready-item llm exception and read-only status behavior. `test_status_warnings_stale_work_and_staged_collision` covers the warning.
- **H5 — FIXED (cx documentation).** Changed the failed-item transcript gate in DESIGN §7 to non-null meta.conversion, consistent with the artifact rule. The wiki implementation/test change is cc-owned and is not claimed fixed by this worktree; no wiki file was edited.
- **H6 — FIXED (DESIGN §7).** Documented escaping of the index ext scalar alongside title and label, matching the existing implementation.
- **H7 — FIXED.** `convert.check_version()` rejects a missing or non-0.3.5 installation with invalid_request/2; ingest invokes it before recovery, retry or claim. `test_converter_version_is_checked_before_any_claim` first failed for both cases and now proves no writes/move. DESIGN §8 records the precondition.
- **V3 — REJECTED as a cx code change (valid finding; cc owns CLI/OCR).** No CLI/OCR code was changed here. DESIGN §8 now specifies trimmed, repeatable comma-separated verify lists to match cc's requested fix.
- **V4 — FIXED.** Retry calls validate_meta on the merged outcome before replacing meta.json. `test_retry_validates_outcome_before_committing_meta` first proved an invalid outcome overwrote the old ledger; it now requires preservation and successful next retry using the already completed conversion.
- **M1 — FIXED.** Removed the unreachable classifier overflow guard and its artificial ROW_CASE. Overflow remains checked by enumerate_units; `test_unit_overflow_is_reported_at_the_enumeration_boundary` exercises the real classify_item error route, and the existing enumeration boundary test still covers 9999/10000. DESIGN §3 row 6 now includes unit-enumeration overflow.
- **S1 — FIXED (cx callers).** Added fsutil.load_json_strict(source): pathlib.Path reads UTF-8; str is JSON text; bytes decode UTF-8; duplicate object keys are rejected at any nesting depth. Ledger, staged-meta recovery and report loading use it. New path/text/bytes, nested-duplicate, encoding and syntax tests pass. cc must replace its remaining JSON loader(s) with this helper.
- **S2 — FIXED (cx caller).** Added ledger.scan(root) returning (items, warnings, errors), with the existing dot-skip, reparse-skip, artifact validation and corruption semantics. Ingest retry uses it; plain ingest still validates only its targets. New scan tests prove empty-root no-write behavior and valid/corrupt/orphan/reparse handling without mutation. cc owns migration of wiki/status callers and their projections.
- **S3 — FIXED (cx callers).** Added fsutil.write_bytes_atomic(path, data), preserving exact bytes and fsync-before-replace; conversion and write_json_atomic use it. Tests cover byte preservation, sync order and preservation of the old artifact on failed sync. cc owns OCR/LLM writer migration. Callers retain containment/reparse checks and ledger-last ordering.
- **S4 — FIXED (cx portion).** errors.py exports the shared converter version, PEER, LARGE and extension sets; convert and ledger import these rather than redeclaring them. The duplicate constraint primitive is fsutil.require (imported as _require). Existing classifier/ledger peer, extension and threshold tests cover the same contracts. cc owns adoption in OCR/LLM/CLI and its count-projection consolidation.
- **S5 — REJECTED as a cx code change (valid simplification; cc owns wiki and its tests).** No wiki projection or malformed-meta test was changed here. Valid nullable fields still need explicit null handling when cc replaces permissive get/default chains with schema indexing.
- **S6 — FIXED (cx test portion).** Consolidated three temp-config tests into one parametrized test_basetemp_configuration, preserving default selection/cache reset, outside-root refusal, and Windows permission fallback coverage. The distinct CI audio-extra contract test remains. Shared tree(), __main__ cleanup and OCR wraps are cc-owned and unchanged here.

Shared APIs for cc:

```text
fsutil.load_json_strict(source: Path | str JSON text | bytes) -> decoded JSON
fsutil.write_bytes_atomic(path, data: bytes) -> None  # flush + fsync + replace
fsutil.require(condition, message) -> None           # ValueError on failure
ledger.scan(root) -> (list[Item], warnings, errors)   # no mutations
errors.CONVERTER_VERSION, PEER, LARGE, *_EXTENSIONS
```

`scan` returns valid items sorted by directory/id. Corrupt items are represented
by errors with id/path/code/message; callers can add corrupt-row projections.
It already includes item orphan warnings and reparse warnings. Callers add
their own sorting, stale-work notes, counts, and output projections.

Full validation: `python -m pytest -q -p no:cacheprovider` -> **576 passed, 4 skipped in 118.92s**. The skips are the existing installed-console e2e cases because this interpreter has no installed `sb`; AT-19 uses the real module entry point and all four cases passed.
No git commands, cc-owned production edits, rubric changes or release actions.

## Combined closeout after cc commit ad569ff

- **H1/H2/H3/H4/H6 — FIXED.** Confirmed the complete stage-output keys, dpi.txt inheritance, stale_work rule and ext escaping in DESIGN. Added H3's 32000-byte summary.md pre-read limit before UTF-8 decoding and the 8000-character check; the 64 KiB summary.json cap remains explicit.
- **H5/V3/S5 — FIXED by cc and retained.** The failed transcript gate uses the ledger, verify keys are stripped, and projections index validated schemas. The helper migration preserves those changes.
- **S1/S2/S3/S4 — FIXED across the combined codebase.** OCR/LLM use fsutil.write_bytes_atomic; LLM and collision-status JSON reads use load_json_strict; LLM schema predicates use require with the existing llm_invalid mapping/messages. Wiki and status call ledger.scan directly; wiki keeps its display sort and status keeps corrupt-row/stale-work projections. Deleted the local scanner, unique-key parser, byte writers and list-only OCR key wrapper. OCR/LLM/CLI and tests/helpers.py import shared errors constants; fixture metadata uses write_json_atomic. The cumulative unit counter remains defined once in wiki and shared with CLI.
- **S6 — FIXED across the combined codebase.** helpers.tree is the only tree implementation and serves OCR/wiki/LLM/CLI plus byte-only ingest/ledger snapshots. Timestamp-sensitive snapshots remain explicit because tree intentionally records only bytes. The single parametrized basetemp test retains all three scenarios; the distinct CI audio-extra test remains. Confirmed functools.wraps and the cleaned __main__ from cc.
- **R1 — ORCHESTRATOR GATE, unchanged.** No rubric promotion, CI-result claim, git operation, tag or release action.

Static AST audit confirms one strict JSON parser, atomic byte writer, raws
scanner, constraint helper, cumulative unit counter and tree helper; PEER,
LARGE and raster sets are defined only in errors.py. All source/tests parse
with Python 3.11 syntax. Combined validation: `python -m pytest -q -p no:cacheprovider` -> **581 passed, 4 skipped in 96.60s**. The four skips still require the locally absent installed `sb` console script.

## Round 2 closeout

- **N1 — FIXED.** Removed the duplicate AT-19 implementation and its subprocess/sys imports from test_ingest.py. The canonical test is tests/test_ocr.py::test_at19_real_containers_ingest_then_approve, covering all four real containers. Earlier child-spy evidence above describes the superseded first implementation.
- **N2 — FIXED.** Removed the unused MARKUP_EXTENSIONS import and bare converted.md.tmp check from convert.py. The shared atomic writer now validates its derived temporary path itself, preserving reparse protection. test_atomic_writer_refuses_a_reparse_temp_before_writing failed first and then passed, requiring both existing target and temporary bytes to remain unchanged.
- **N3 — FIXED.** USAGE now documents exact markitdown-gc 0.3.5 as an ingest precondition checked before recovery, retry or claim; missing/different versions are invalid_request/2 before writes.
- **N4 — FIXED.** errors.py now describes its shared codes and contract constants; renamed the stale test to test_status_reuses_ledger_scan_and_shared_unit_counts without changing its assertions.

Round 2 validation: `python -m pytest -q -p no:cacheprovider` -> **578 passed, 4 skipped in 89.21s**. Skips require the locally absent installed `sb` console script. No git commands.

## Round 3 score-gap closeout

- **FIXED — AT-12 network assertion.** test_renamed_audio_never_reaches_optional_backends now takes network_guard, snapshots its call count immediately before classify_item, and requires the count to remain unchanged in both optional-backend scenarios.
- **FIXED — Orphan signature test.** Removed test_classification_has_no_ingest_path_precheck and its inspect import. AT-35 and the representative row tests retain contract coverage without pinning an internal signature.
- **FIXED — Step-error naming.** Renamed the internal classify parameter and all its callers/test options from report_error to step_error, reflecting both report and unit-enumeration failures. Persisted error codes, messages and states are unchanged; report-specific ingest fixture controls retain their descriptive names.
- **FIXED — Shared IO mapping.** Moved the existing OCR wrapper into fsutil.io_errors, retaining wraps and exception chaining. OCR imports it as _io; LLM prepare/accept use the same decorator instead of duplicated inline catches. The three test_io_errors_translates_only_oserror cases failed before the helper existed and now verify io_error/1 for OSError plus identity-preserving propagation of SbError and ValueError.

Round 3 validation: `python -m pytest -q -p no:cacheprovider` -> **580 passed, 4 skipped in 86.38s**. The existing skips require the locally absent installed `sb` console script.
RUBRIC scores and evidence were not changed; new-head CI remains orchestrator-owned. No git commands.

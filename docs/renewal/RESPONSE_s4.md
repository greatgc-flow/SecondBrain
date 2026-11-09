# Slice 4 review response

All seven focused ag regression cases passed on the reviewed implementation,
before any production edit. The three blocker claims are rejected on that evidence.
Fable L1's regression failed first, then passed after limiting the index scan to
`--retry`. The duplicate target is still fully validated on plain ingest.

| Finding | Decision and evidence |
| --- | --- |
| ag blocker 1: staged meta recovery lacks classification keys | **REJECTED.** `test_ag_b1_meta_present_recovery_has_classification_keys` crashes immediately after the real `meta.json` write, verifies that the stage already contains `class`, `state`, `reason`, `error`, and `ocr`, then recovers with byte-identical meta and one conversion/report total. `classify_item.finish` persists these fields before meta is written. Retained stage/meta agreement validation also rejects tampering (`test_staged_meta_must_agree_with_ledger_before_commit`); removing it would weaken that protection. |
| ag blocker 2: pending conversion is reconverted | **REJECTED.** Both cases of `test_ag_b2_pending_conversion_recovery_respects_completed_output` pass: without completed output the backend runs once on recovery; with output present the digest is reconciled, mtime is unchanged, and the backend count stays one. `classify_item` delegates this to the existing ledger-first `convert_document`; recovery need not duplicate that code. |
| ag blocker 3: retained stage loses durable outputs on retry | **REJECTED.** `test_ag_b3_retained_stage_reuses_all_durable_outputs` commits a classification failure after conversion, native-text detection, and valid triage have all been persisted. It verifies all three fields against meta before and after retry, with one conversion/report total. The retained stage already carries these outputs; the fallback hydrates them only when no stage exists. |
| ag minor: null conversion activity crashes charset access | **REJECTED.** `test_ag_invalid_conversion_activity_is_rejected_before_retry` supplies `activity: null` and proves full meta validation reports `corrupt_meta`, leaves bytes unchanged, and never reaches `_retry`. Nested activity/params fields are schema requirements, so silent defaults would conceal corruption. |
| ag minor: missing stage filename raises KeyError; delete corrupt stage | **REJECTED.** `test_ag_missing_stage_filename_is_corrupt_and_preserves_payload` proves `load_stage` reports `corrupt_meta` before `_resume` can index the filename; the staged payload and ledger remain byte-identical. A corrupt ledger does not establish that its payload was never claimed. Both valid unclaimed-stage variants are already deleted by `test_recovery_removes_unclaimed_stage_only`; deleting corrupt stages could discard original bytes. |
| ag minor: normalize alias comparisons to NFC | **REJECTED.** DESIGN §2 defines aliases by a new **exact filename**; NFC is for display/sort. `test_ag_aliases_preserve_distinct_exact_unicode_spellings` requires an NFD spelling equivalent to the original NFC name to be recorded as an alias, then treated as a duplicate on exact repetition with meta bytes unchanged. Folding names would lose the received spelling. |
| Fable L1: avoid unrelated full-ledger scans on plain ingest | **FIXED.** `_scan` now runs only for `--retry`. `test_plain_ingest_does_not_scan_unrelated_committed_items` first failed on the unconditional scan and now proves that an unrelated corrupt item is neither read nor changed while a new file ingests successfully. `test_corrupt_committed_meta_is_reported_preserved_and_blocks_duplicate` covers both plain ingest and retry, preserving validation of an occupied duplicate target. |
| Fable L2: fixture unit count and container media assertions | **FIXED.** `test_real_fixture_ingest_matches_gate_and_retry` now compares unit counts to every probe and checks the media directory and recorded image digests for containers with characterized extracted images. |
| Fable L3: document charset and missing-inbox errors | **FIXED (documentation).** DESIGN §8 now states unknown charset -> `invalid_request`/2 before writes and missing inbox -> `io_error`/1. Existing tests `test_invalid_charset_is_rejected_before_writes` and `test_missing_inbox_is_io_error_without_creating_layout` cover both contracts. |

Validation: `python -m pytest -q -p no:cacheprovider` -> **498 passed in 77.40s**.

Only `ingest.py`, `test_ingest.py`, the §8 clarification in `DESIGN.md`, and this
response were edited. No git commands were run.

# SecondBrain v1 — final MECE / closure audit (2026-11-09, branch slice/9-release)

Scope: BRIEF, DESIGN r9, IMPL_PLAN r2, `src/secondbrain/*.py`, `tests/*.py`, README, docs/USAGE.md, RUBRIC.md, ci.yml, pyproject.
Read-only audit; no code or tests were run here (orchestrator: 562 passed, 4 skipped; slice PRs green on the 6-job matrix).

## Scores

| Area | Score | Justification |
|---|---|---|
| Vertical | 92 | All 37 ATs, I1–I8 and every §11 row have a named passing test (table below). One AT (AT-19) exists only in weakened synthetic form; one §3 row (path_too_long) is reachable only from tests. |
| Horizontal | 90 | Error/warning codes (21+5), exit mapping, states, classes, unit/attempt/activity/triage fields, JSON envelope, item results and reason strings are identical across DESIGN §2/§3/§8, errors.py, ledger.py, convert.py, cli.py, wiki.py, USAGE and tests. Six documentation drifts (H1–H6), none user-visible. |
| MECE | 93 | §3 table exhaustively checked (3840-case cross product), class/state pairs enforced by the validator, 45 matrix cells tested per cell, all 8 recovery rows tested with fault injection. One row (§3 #1 `path_too_long`) is dead inside `classify_item`. |
| Simplicity | 78 | Logic is small and direct, but the same primitive is re-implemented 2–4 times in several places (S1–S6) and some branches defend against states the validator never admits. |
| Tests | 90 | Strong: fault hooks at every durable boundary, real-tool characterization, network guard in-process and in children, console-script e2e. Gaps: AT-19 as written, `--ok` whitespace, `_retry` pre-validation; 4 copies of `tree()`. |

Blockers: 0. Majors: 3 (V1, V2, R1). Minors: 14.

## Findings

**[major] V1 — AT-19 not implemented as specified.** DESIGN.md:318 requires real `mixed/slides.pptx, image.hwp, image.hwpx, image.xlsx` ingested then approved, assets byte-equal, converter spy 1 total. `tests/test_ocr.py:151` builds a synthetic pptx item with `photo.png` as the asset; the real container→approve chain is only covered transitively (`test_ingest.py:528` media digests + synthetic copy). By RUBRIC's own rule (“50 = listed case missing”), G1/I2 cannot reach 100. Fix: add `test_at19_real_containers_ingest_then_approve` that ingests the four fixtures, approves each, compares `work/<id>/uNNNN.<ext>` to `raws/<id>/media/*` bytes, asserts spy count from the child ledgers.

**[major] V2 — §3 row 1 `path_too_long` is a phantom classification row.** DESIGN.md:108 lists it as class null / failed, but AT-35 (DESIGN.md:334) and `ingest.py:166` reject before the claim and never commit an item; `convert.py:217,228-229` keeps a `path=` parameter used only by `test_convert.py:154-155`. Fix: drop `path` from `classify()` and the two ROW_CASES; reword row 1 to `empty_file` only and move `path_too_long` to the ingest pre-check sentence (§2 “Names and bytes”).

**[major] R1 — Release gate is open.** RUBRIC.md:13-14 scores all 25 rows 50 because the release revision has no recorded 6-job run and the offline-install jobs were not executed; slice 9 commit is marked “WIP, unreviewed”. This is accurate reporting, not a defect, but §12 forbids tagging until every row is 100. Fix: run CI on the slice-9 head, record run URL + per-job results in RUBRIC, flip rows after V1/V2 land.

**[minor] H1 — stage.json contract under-documented.** DESIGN.md:154 lists `{relpath, filename, charset, claimed_at, identity?, collision?, conversion?}`; code also persists `triage`, `has_native_text`, `class`, `state`, `reason`, `error`, `ocr` (`convert.py:273,289,297`). `_validate_stage` (ledger.py:347) accepts them by `<=`. Fix: list the step-output keys in §4.

**[minor] H2 — Undocumented scratch file.** `work/<id>/dpi.txt` (ocr.py:175, read at ocr.py:51) is absent from DESIGN.md:35 layout and §5. Fix: add to §2 scratch list or store the effective dpi in COMMANDS.txt only.

**[minor] H3 — summary.json size cap only in code and USAGE.** `MAX_JSON_BYTES = 64 KiB` (llm.py:22, USAGE.md:251) is not in DESIGN.md:213. Fix: add to §6 output contract.

**[minor] H4 — `stale_work` semantics undefined.** DESIGN.md:277 names the warning; the rule (non-in-progress item with a non-`llm` leftover in `work/<id>/`, cli.py:116-124) exists only in code. Fix: one sentence in §8.

**[minor] H5 — Failed-item transcript gate uses file existence, not the ledger.** wiki.py:150 and DESIGN.md:251 (“iff converted.md exists”) contradict the artifact rule (DESIGN.md:51-52): an unreferenced `converted.md` on a failed item yields an empty fenced Transcript section (`view` returns "" since `conversion` is null). Fix: gate on `meta["conversion"] is not None`; adjust `test_transcript_gate_follows_converted_md_file` (test_wiki.py:327).

**[minor] H6 — `ext` column escaping not in DESIGN.** wiki.py:162 escapes `ext` (correct: POSIX allows `|` in names) but DESIGN.md:239 says only title and label are escaped. Fix: add `ext` to the sentence.

**[minor] H7 — exit-2 code can appear in an exit-1 envelope.** `activity()` raises `invalid_request` (ledger.py:100-103) if the installed converter version is not `0.3.5` (convert.py:166); ingest records it per file (ingest.py:237-238) after the inbox move. Unreachable with the `==0.3.5` pin. Fix: raise `conversion_failed` there, or check the version once in `ingest()` before any claim.

**[minor] V3 — `--ok "u0001, u0002"` fails.** cli.py:170 filters on `key.strip()` but passes the unstripped key; ocr.py:63 strips only the string branch. Fix: `key.strip() for ... if key.strip()`; drop the string branch in `ocr._keys`.

**[minor] V4 — `_retry` writes meta before validating it.** ingest.py:202-203 writes `{**meta, **outcome}` and only `_finished` → `load_item` validates. Mutation rule step 1 (DESIGN.md:148) says validate first. Fix: `validate_meta(merged, directory)` before `write_json_atomic`, mirroring `ocr._commit`.

**[minor] M1 — Dead overflow branch.** convert.py:249-250 (`len(units) > 9999`) is unreachable from `classify_item`, since `enumerate_units` raises first (convert.py:211-212) and is routed through `report_error`. Fix: delete the branch and the `unit-overflow` ROW_CASE, or route overflow explicitly instead of via `report_error`.

**[minor] S1 — Four strict JSON loaders.** ledger.py:329-337, ingest.py:75-86, convert.py:83-88, llm.py:92-98 each re-implement duplicate-key-rejecting `json.loads`. Fix: `fsutil.load_json_strict(path|text)`; use everywhere.

**[minor] S2 — Three `raws/` scanners.** ingest.py:25-43, wiki.py:45-65, cli.py:141-164 walk `raws/`, skip dot-names, warn reparse, load items, collect errors. Fix: `ledger.scan(root) -> (items, warnings, errors)`; callers add their own projection (`corrupt_row`, `stale_work`).

**[minor] S3 — Three tmp+replace byte writers.** ocr.py:71-76, llm.py:45-50 (identical), convert.py:187-192 (with fsync). Fix: `fsutil.write_bytes_atomic(path, data)` with fsync; the two peer-output writers then match the ledger's durability.

**[minor] S4 — Repeated constants.** PEER regex in ledger.py:87, ocr.py:21, llm.py:24; raster extension set three times inside ledger.py:191,290,301 (and again in convert.py:18); `_require` in ledger.py:21 and convert.py:23; `LARGE` in cli.py:18 and ocr.py:18; `cli._units` (cli.py:81-85) duplicates `wiki._counts` (wiki.py:74-80). Fix: put extension sets and PEER in errors.py (dependency-free) or a tiny `contract.py`; import.

**[minor] S5 — Defensive branches for validator-rejected states.** wiki.py:105-106 (`error or {}`, `reason or 'unknown'`), wiki.py:70 (`meta.get("llm") or {}`), pinned by test_wiki.py:317-324. Fix: index directly; the validator guarantees shape.

**[minor] S6 — Test-infra duplication.** `tree()` in test_ocr.py:16, test_wiki.py:15, test_llm.py:19, test_cli.py:22; three tests exercise conftest internals (test_fsutil.py:267-313). Fix: move `tree()` to helpers.py; keep at most one conftest sanity test. Also `__main__.py:3` `from __future__ import annotations` is unused; `ocr._io` (ocr.py:79-86) should use `functools.wraps`.

## Vertical closure table (requirement → design → code → test)

| Id | Design | Code | Test evidence (file::test) |
|---|---|---|---|
| B1 | §2, §4, §5 view, §7 | ingest.py `_claim/_resume`, transcript.py `view`, wiki.py `build` | test_ingest::test_at01_two_payload_renames_and_source_identity; test_at02_at03_duplicate_and_alias_in_every_state; test_at08_plain_text_set_never_calls_report; test_wiki::test_at30_build_twice_identical_and_only_expected_files |
| B2 | §1, §12 | pyproject, `__init__`, README#history | test_bootstrap::test_v1_discard_boundary; test_package_version |
| B3 | §7 | wiki.py `index_page/source_page/fence/esc` | test_wiki::test_at30_*; test_at31_index_sort_columns_and_label; test_at31_ties_break_by_id_and_nfc_sort; test_source_page_structure_and_link |
| B4 | §6 | llm.py `prepare/accept` | test_llm::test_at28_accept_valid_records_revision_with_provenance; test_at29_prepare_prompt_fence_contract_and_no_subprocess; test_at27_new_revision_unchanged_and_history |
| B5 | §3, §4, §5, §8 | convert.py `classify_item`, cli.py `run_status`, ocr.py `approve` | test_ingest::test_real_fixture_ingest_matches_gate_and_retry; test_cli::test_at16_status_json_fields_counts_errors_warnings_and_no_writes; test_ocr::test_at24_decline_makes_ready_and_view_is_converted_text; test_at21_only_files_of_approved_units_are_taken |
| B6 | §5 | ocr.py:156-157,169 `LARGE`, `NOTICE` | test_ocr::test_at17_large_item_needs_acknowledgement; test_at17_large_boundary_is_21_units; test_cli::test_approve_prints_notice_and_next_step |
| B7 | §3 | convert.py `adapt_report/run_report/_make_converter` | test_convert::test_real_tool_classification_matches_characterization; test_at06_*; test_at12_shortcuts_never_reach_converter_or_report; test_only_extension_selected_converter_is_registered; test_renamed_audio_never_reaches_optional_backends |
| B8 | §3 | convert.py `classify`, ledger.py:276-279 | test_convert::test_at05_full_domain_is_mece; test_at05_table_rows_and_shortcuts; test_transcript::test_at07_native_text; test_ingest::test_at11_candidates_without_extracted_images_have_no_units |
| B9 | §2 activity, I2, §5 | ledger.py `activity`, convert.py `convert_document`, ocr.py `record` | test_ingest::test_at02_at03_*; test_at14_retry_reuses_completed_conversion_and_assets; test_ocr::test_at20_record_copies_text_with_provenance; test_at22_verify_request_validation |
| B10 | §2 names/bytes | fsutil.py `write_text/write_json_atomic/check_path_length`, ledger.py `_filename` | test_ingest::test_at35_*; test_at36_hidden_and_reparse_are_skipped_without_following; test_fsutil::test_utf8_lf_and_atomic_json; test_ledger::test_windows_reserved_names_rejected_in_stage |
| G1 | §5 approve | ocr.py `approve/_commands/_render` | test_ocr::test_at18_pdf_page_rendered_and_commands; test_commands_ask_grouping_of_three_with_stream_names; test_at17_cap_of_30_then_second_approval_then_full_flow; test_at19_assets_and_rasters_copied_byte_equal (synthetic, see V1); test_convert::test_at18_numeric_pdf_keys_and_container_asset_order |
| G2, G3 | §5 verify/finalize | ocr.py `verify`, ledger.py:209 | test_ocr::test_at22_verify_request_validation; test_verify_accumulates_and_every_unit_needs_verification; test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord; test_at25_fault_after_meta_write_then_verify_cleans; test_at25_fault_after_copy_before_meta_then_record_again |
| G4 | §5, §6, §9 | convert.py `_local_file/_make_converter`; conftest guard/spy | test_fsutil::test_at37_network_and_dns_blocked; test_at37_converter_child_is_guarded; test_at37_real_converter_import_and_http_control; test_audio_extra_check_is_strict_in_ci; test_llm::test_at29_* |
| X1 | §4 mutation rule, protocol, recovery | ingest.py `_resume/_recover`, fsutil `write_json_atomic` | test_ingest::test_at04_collision_is_flagged_and_never_resumed; test_at26_all_durable_boundaries_recover_once; test_at26_payload_cannot_clobber_ledgers; test_staged_meta_must_agree_with_ledger_before_commit; test_ocr::test_at25_*; test_wiki::test_fault_after_wiki_old_rename_recovers; test_llm::test_at27_fault_after_body_copy_leaves_orphan_then_recovers |
| X2 | §6, §7 | wiki.py `fence/esc`, llm.py `_validate`, ocr.py `record` | test_ocr::test_at27_hostile_peer_output_is_stored_as_data_only; test_llm::test_at28_hostile_summary_rendered_inside_fence; test_at28_json_field_validation; test_wiki::test_at31_*; test_at32_view_inside_five_backtick_fence_and_hostile_content; test_at32_model_string_and_summary_stay_fenced |
| X3 | §4 matrix, §8 | cli.py `envelope/main/row`, errors.py | test_cli::test_at15_command_by_state_matrix (45 cells); test_matrix_covers_every_cell; test_at34_parser_failures_are_one_json_object; test_at34_every_command_returns_a_valid_envelope; test_at34_warnings_and_exit_precedence; test_e2e::* |
| I1 | §4 | ingest.py:177 (rename 1), 143 (rename 2) | test_ingest::test_at01_*; test_at26_all_durable_boundaries_recover_once |
| I2 | §3 step 2, §4 | convert.py:159-164,171 | test_convert::test_completed_output_reconciled_after_crash; test_referenced_corruption_and_unledgered_output_are_not_reconverted; test_ingest::test_retry_faults_never_redo_completed_output; test_ag_b2_pending_conversion_recovery_respects_completed_output |
| I3 | §5 view | transcript.py `view` | test_transcript::test_view_only_verified_and_pure; test_view_keeps_recorded_text_line_endings; test_orphan_conversion_is_not_a_transcript |
| I4 | §5 record | ocr.py:200,214-215 | test_ocr::test_at21_only_files_of_approved_units_are_taken; test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord |
| I5 | §5 verify | ocr.py:251-252, ledger.py:209 | test_ocr::test_at22_verify_request_validation; test_ledger::test_nested_contract_rejected[peer] |
| I6 | §5, §7 | transcript.py:16-20, wiki.py:124-125 | test_transcript::test_view_only_verified_and_pure; test_wiki::test_at33_only_verified_text_in_view; test_ocr::test_transcript_view_follows_record_and_verify |
| I7 | §7 | wiki.py `_load/build` | test_wiki::test_at30_build_twice_identical_and_only_expected_files; test_at30_staging_and_hidden_dirs_ignored; test_at30_corrupt_item_reported_and_skipped |
| I8 | §2 deletion rule | fsutil.py `safe_delete/checked_path` | test_fsutil::test_at36_allowed_deletion; test_at36_other_deletion_targets_refused; test_at36_reparse_ancestor_refused_before_delete; test_at36_reparse_descendant_refused_before_any_delete; test_wiki::test_at30_reparse_point_wiki_old_refused; test_ocr::test_reparse_scratch_dir_refused_on_cleanup |

Reverse check: no orphan tests (every test maps to an AT, invariant, §3/§4 row, or test infrastructure); orphan code limited to V2/M1/S5. Horizontal spot checks passed: 11 exit-2 and 10 exit-1 codes (DESIGN.md:275-277 = errors.py:6-26 = USAGE.md:138-139), 5 warning codes, 5 states, 6 classes, 4 unit statuses, 3 unit kinds, 3 dispositions, 4 activity methods, item/envelope/note field sets (cli.py:88-96,210-214 = DESIGN.md:271-274 = test_cli.py:16-18), reason strings (convert.py:226-255 = DESIGN.md:108-119), banner texts (wiki.py:97-119 = DESIGN.md:249-254), COMMANDS.txt prompt (ocr.py:130-133 = USAGE.md:188).

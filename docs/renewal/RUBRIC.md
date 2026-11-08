# SecondBrain v1 release rubric

Release preparation, 2026-11-09. This is evidence for the working release
revision, not a declaration that v1.0.0 has been released.

**R1 — current local result:** Windows, Python 3.15.2,
`python -m pytest -q -p no:cacheprovider` -> **562 passed, 4 skipped in 78.16s**.
Every test cited in the table passed in R1, including all its parametrized
cases. “PASS / R1” is a local result, not a six-job CI result.

DESIGN §12 scores: **0** = no/failing test; **50** = missing/skipped cases;
**100** = all listed tests pass on Ubuntu/Windows × Python 3.11/3.13/3.15,
with no gaps in the MECE/vertical/horizontal review. All 25 rows are **50**:
release-revision CI and final review evidence remain missing. No row is 100.

| Id | Requirement / invariant | Test evidence (file::test) | Current local result | Score |
| --- | --- | --- | --- | --- |
| B1 | inbox -> raws -> wiki | `tests/test_ingest.py::test_at01_two_payload_renames_and_source_identity`; `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files` | PASS / R1 | 50 |
| B2 | Discard v0.1; tag history only | `tests/test_bootstrap.py::test_v1_discard_boundary`; `tests/test_bootstrap.py::test_package_version` | PASS / R1 | 50 |
| B3 | Deterministic wiki pages, index and links | `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files`; `tests/test_wiki.py::test_at31_index_sort_columns_and_label`; `tests/test_wiki.py::test_source_page_structure_and_link` | PASS / R1 | 50 |
| B4 | Explicit LLM tier through operator peers | `tests/test_llm.py::test_at29_prepare_prompt_fence_contract_and_no_subprocess`; `tests/test_llm.py::test_at28_accept_valid_records_revision_with_provenance` | PASS / R1 | 50 |
| B5 | Classify and list counts before approved OCR | `tests/test_ingest.py::test_real_fixture_ingest_matches_gate_and_retry`; `tests/test_cli.py::test_at16_status_json_fields_counts_errors_warnings_and_no_writes`; `tests/test_ocr.py::test_at21_only_files_of_approved_units_are_taken` | PASS / R1 | 50 |
| B6 | Explicit approval for sensitive or large inputs | `tests/test_ocr.py::test_at17_large_item_needs_acknowledgement`; `tests/test_ocr.py::test_at17_large_boundary_is_21_units`; `tests/test_cli.py::test_approve_prints_notice_and_next_step` | PASS / R1 | 50 |
| B7 | markitdown-gc 0.3.5 conversion and triage | `tests/test_convert.py::test_real_tool_classification_matches_characterization`; `tests/test_convert.py::test_at06_every_characterized_real_report`; `tests/test_convert.py::test_at12_shortcuts_never_reach_converter_or_report` | PASS / R1 | 50 |
| B8 | MECE classes, including unsupported and unknown | `tests/test_convert.py::test_at05_full_domain_is_mece`; `tests/test_convert.py::test_at05_table_rows_and_shortcuts`; `tests/test_transcript.py::test_at07_native_text` | PASS / R1 | 50 |
| B9 | Never retranscribe; retain provenance | `tests/test_ingest.py::test_at02_at03_duplicate_and_alias_in_every_state`; `tests/test_ingest.py::test_at14_retry_reuses_completed_conversion_and_assets`; `tests/test_ocr.py::test_at20_record_copies_text_with_provenance` | PASS / R1 | 50 |
| B10 | VerySimpleGuide, Windows, English | `tests/test_ingest.py::test_at35_long_destination_is_rejected_before_claim`; `tests/test_ingest.py::test_at35_nfd_filename_stays_exact`; `tests/test_fsutil.py::test_utf8_lf_and_atomic_json` | PASS / R1 | 50 |
| G1 | OCR prompt, batching, pilot, concurrency, approval cap | `tests/test_ocr.py::test_at18_pdf_page_rendered_and_commands`; `tests/test_ocr.py::test_commands_ask_grouping_of_three_with_stream_names`; `tests/test_ocr.py::test_at17_cap_of_30_then_second_approval_then_full_flow` | PASS / R1 | 50 |
| G2 | Independent verification of every unit; exact digits | `tests/test_ocr.py::test_at22_verify_request_validation`; `tests/test_ocr.py::test_verify_accumulates_and_every_unit_needs_verification`; `tests/test_ocr.py::test_at18_pdf_page_rendered_and_commands` | PASS / R1 | 50 |
| G3 | OCR ledger, no cache, scratch cleanup | `tests/test_ocr.py::test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord`; `tests/test_ocr.py::test_at25_fault_after_meta_write_then_verify_cleans`; `tests/test_ocr.py::test_at25_fault_after_copy_before_meta_then_record_again` | PASS / R1 | 50 |
| G4 | Offline CI; peerhub as an operator workflow | `tests/test_fsutil.py::test_at37_network_and_dns_blocked`; `tests/test_fsutil.py::test_at37_converter_child_is_guarded`; `tests/test_fsutil.py::test_audio_extra_check_is_strict_in_ci`; `tests/test_llm.py::test_at29_prepare_prompt_fence_contract_and_no_subprocess` | PASS / R1 | 50 |
| X1 | Crash safety and corruption handling | `tests/test_ingest.py::test_at26_all_durable_boundaries_recover_once`; `tests/test_ocr.py::test_at25_fault_after_copy_before_meta_then_record_again`; `tests/test_wiki.py::test_fault_after_wiki_old_rename_recovers`; `tests/test_llm.py::test_at27_fault_after_body_copy_leaves_orphan_then_recovers` | PASS / R1 | 50 |
| X2 | Untrusted content handling | `tests/test_ocr.py::test_at27_hostile_peer_output_is_stored_as_data_only`; `tests/test_llm.py::test_at28_hostile_summary_rendered_inside_fence`; `tests/test_wiki.py::test_at32_view_inside_five_backtick_fence_and_hostile_content` | PASS / R1 | 50 |
| X3 | Complete CLI, JSON and exit contract | `tests/test_cli.py::test_at15_command_by_state_matrix`; `tests/test_cli.py::test_at34_parser_failures_are_one_json_object`; `tests/test_cli.py::test_at34_every_command_returns_a_valid_envelope`; `tests/test_cli.py::test_at34_warnings_and_exit_precedence` | PASS / R1 | 50 |
| I1 | Source unchanged after rename 1 | `tests/test_ingest.py::test_at26_all_durable_boundaries_recover_once`; `tests/test_ingest.py::test_at14_retry_reuses_completed_conversion_and_assets` | PASS / R1 | 50 |
| I2 | Completed conversion output produced at most once | `tests/test_convert.py::test_completed_output_reconciled_after_crash`; `tests/test_ingest.py::test_retry_faults_never_redo_completed_output`; `tests/test_ingest.py::test_ag_b2_pending_conversion_recovery_respects_completed_output` | PASS / R1 | 50 |
| I3 | Pure transcript view | `tests/test_transcript.py::test_view_only_verified_and_pure`; `tests/test_transcript.py::test_view_keeps_recorded_text_line_endings` | PASS / R1 | 50 |
| I4 | Approved OCR keys and new digests only | `tests/test_ocr.py::test_at21_only_files_of_approved_units_are_taken`; `tests/test_ocr.py::test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord` | PASS / R1 | 50 |
| I5 | Verifying peer differs from recording peer | `tests/test_ocr.py::test_at22_verify_request_validation` | PASS / R1 | 50 |
| I6 | Unverified OCR excluded from view and wiki | `tests/test_transcript.py::test_view_only_verified_and_pure`; `tests/test_wiki.py::test_at33_only_verified_text_in_view` | PASS / R1 | 50 |
| I7 | Wiki derived only from raws | `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files`; `tests/test_wiki.py::test_at30_staging_and_hidden_dirs_ignored` | PASS / R1 | 50 |
| I8 | Restricted deletion targets | `tests/test_fsutil.py::test_at36_allowed_deletion`; `tests/test_fsutil.py::test_at36_other_deletion_targets_refused`; `tests/test_fsutil.py::test_at36_reparse_ancestor_refused_before_delete`; `tests/test_ingest.py::test_at36_hidden_and_reparse_are_skipped_without_following` | PASS / R1 | 50 |

Remaining gates:

- R1 skipped the installed-console cases
  `tests/test_e2e.py::test_e2e_text_ingest_duplicates_and_wiki`,
  `tests/test_e2e.py::test_e2e_raster_ocr_approve_record_verify`,
  `tests/test_e2e.py::test_e2e_llm_prepare_accept_and_rejection`, and
  `tests/test_e2e.py::test_e2e_status_on_empty_root_and_usage_error`.
  This interpreter has no installed `sb`; the tests require it and fail rather
  than skip in CI. The separate `test_e2e_python_dash_m_entry_point` passed.
- Run the full six-job matrix on the release revision; record its run URL and
  outcomes here. Results from an earlier revision do not certify the version
  bump, discard-boundary test, or new workflow.
- Run both `.github/workflows/ci.yml::jobs.offline-clean-install` jobs.
  They build/download wheels online, create a fresh venv, install
  `secondbrain==1.0.0` with `--no-index`, verify installed package/module
  versions and location (plus markitdown-gc 0.3.5 and absent audio extras), then
  assert installed `sb --json status` exits 0 on a completely empty root.
  Their Python blocks were syntax-checked locally; they were **not executed**
  here because the embedded interpreter lacks `venv`/`ensurepip` and build
  tooling. No clean-install pass is claimed.
- Complete the cross-check and unanimous implementation review. B2's removal
  assertions are automated; history-tag preservation is operator review
  evidence ([README history](../../README.md#history)). B10's simplicity and
  English, B6's owner permission, and G1/G2's pilot/concurrency/faithfulness are
  also review/operator responsibilities. Tests verify notices, caps, prompt
  content, schemas and peer identity; they do not prove that external peers
  followed instructions or enforce their profiles. See
  [USAGE prerequisites](../USAGE.md#operator-and-security-prerequisites).
- After all rows reach 100 and clean installs pass, the orchestrator promotes
  to `main`, runs the full matrix there, tags `v1.0.0`, and creates the GitHub
  Release with this sheet. No PyPI publication.

No git commands, promotion, tag or release were performed during preparation.

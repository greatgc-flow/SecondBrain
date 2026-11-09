# SecondBrain v1 release rubric

Release preparation, 2026-11-09. This records the validated release revision;
v1.0.0 promotion, tag and GitHub Release remain orchestrator actions.

**R1 — release evidence:** head `9a70783163447a61df2ec26c8e6b20c17854d374`
(`9a70783`), [CI run 42541480772](https://github.com/greatgc-flow/SecondBrain/actions/runs/42541480772),
attempt 1: **all eight jobs passed**. The six full-suite logs each report
**582 passed, 0 skipped**, including all four installed-console e2e cases.
Both offline clean installs passed on that revision.

| CI jobs | Python | Result |
| --- | --- | --- |
| Full suite: ubuntu-latest | 3.11 / 3.13 / 3.15 | PASS, 582 passed / 0 skipped in each job |
| Full suite: windows-latest | 3.11 / 3.13 / 3.15 | PASS, 582 passed / 0 skipped in each job |
| Offline clean install: ubuntu-latest / windows-latest | 3.13 | PASS on both OSes |

**Current local result:** Windows, Python 3.15.2,
`python -m pytest -q -p no:cacheprovider` -> **578 passed, 4 skipped in 86.02s**.
The four local skips require the absent installed `sb`; they passed in CI.
Local skips are not represented as CI passes.

DESIGN §12 scores: **0** = no/failing test; **50** = missing/skipped cases;
**100** = all listed tests pass on Ubuntu/Windows × Python 3.11/3.13/3.15,
with no gaps in the MECE/vertical/horizontal review. All 25 rows are **100**:
their cited tests passed in CI R1 and [final audit r3](AUDIT_v1_r3.md) found
no remaining blocker, major or minor finding or traceability gap.
“PASS / CI R1 + audit r3” below refers to that run and cross-check.

| Id | Requirement / invariant | Test evidence (file::test) | Release evidence result | Score |
| --- | --- | --- | --- | --- |
| B1 | inbox -> raws -> wiki | `tests/test_ingest.py::test_at01_two_payload_renames_and_source_identity`; `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files` | PASS / CI R1 + audit r3 | 100 |
| B2 | Discard v0.1; tag history only | `tests/test_bootstrap.py::test_v1_discard_boundary`; `tests/test_bootstrap.py::test_package_version` | PASS / CI R1 + audit r3 | 100 |
| B3 | Deterministic wiki pages, index and links | `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files`; `tests/test_wiki.py::test_at31_index_sort_columns_and_label`; `tests/test_wiki.py::test_source_page_structure_and_link` | PASS / CI R1 + audit r3 | 100 |
| B4 | Explicit LLM tier through operator peers | `tests/test_llm.py::test_at29_prepare_prompt_fence_contract_and_no_subprocess`; `tests/test_llm.py::test_at28_accept_valid_records_revision_with_provenance` | PASS / CI R1 + audit r3 | 100 |
| B5 | Classify and list counts before approved OCR | `tests/test_ingest.py::test_real_fixture_ingest_matches_gate_and_retry`; `tests/test_cli.py::test_at16_status_json_fields_counts_errors_warnings_and_no_writes`; `tests/test_ocr.py::test_at21_only_files_of_approved_units_are_taken` | PASS / CI R1 + audit r3 | 100 |
| B6 | Explicit approval for sensitive or large inputs | `tests/test_ocr.py::test_at17_large_item_needs_acknowledgement`; `tests/test_ocr.py::test_at17_large_boundary_is_21_units`; `tests/test_cli.py::test_approve_prints_notice_and_next_step` | PASS / CI R1 + audit r3 | 100 |
| B7 | markitdown-gc 0.3.5 conversion and triage | `tests/test_convert.py::test_real_tool_classification_matches_characterization`; `tests/test_convert.py::test_at06_every_characterized_real_report`; `tests/test_convert.py::test_at12_shortcuts_never_reach_converter_or_report` | PASS / CI R1 + audit r3 | 100 |
| B8 | MECE classes, including unsupported and unknown | `tests/test_convert.py::test_at05_full_domain_is_mece`; `tests/test_convert.py::test_at05_table_rows_and_shortcuts`; `tests/test_transcript.py::test_at07_native_text` | PASS / CI R1 + audit r3 | 100 |
| B9 | Never retranscribe; retain provenance | `tests/test_ingest.py::test_at02_at03_duplicate_and_alias_in_every_state`; `tests/test_ingest.py::test_at14_retry_reuses_completed_conversion_and_assets`; `tests/test_ocr.py::test_at20_record_copies_text_with_provenance` | PASS / CI R1 + audit r3 | 100 |
| B10 | VerySimpleGuide, Windows, English | `tests/test_ingest.py::test_at35_long_destination_is_rejected_before_claim`; `tests/test_ingest.py::test_at35_nfd_filename_stays_exact`; `tests/test_fsutil.py::test_utf8_lf_and_atomic_json` | PASS / CI R1 + audit r3 | 100 |
| G1 | OCR prompt, batching, pilot, concurrency, approval cap | `tests/test_ocr.py::test_at18_pdf_page_rendered_and_commands`; `tests/test_ocr.py::test_commands_ask_grouping_of_three_with_stream_names`; `tests/test_ocr.py::test_at17_cap_of_30_then_second_approval_then_full_flow`; `tests/test_ocr.py::test_at19_real_containers_ingest_then_approve` | PASS / CI R1 + audit r3 | 100 |
| G2 | Independent verification of every unit; exact digits | `tests/test_ocr.py::test_at22_verify_request_validation`; `tests/test_ocr.py::test_verify_accumulates_and_every_unit_needs_verification`; `tests/test_ocr.py::test_at18_pdf_page_rendered_and_commands` | PASS / CI R1 + audit r3 | 100 |
| G3 | OCR ledger, no cache, scratch cleanup | `tests/test_ocr.py::test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord`; `tests/test_ocr.py::test_at25_fault_after_meta_write_then_verify_cleans`; `tests/test_ocr.py::test_at25_fault_after_copy_before_meta_then_record_again` | PASS / CI R1 + audit r3 | 100 |
| G4 | Offline CI; peerhub as an operator workflow | `tests/test_fsutil.py::test_at37_network_and_dns_blocked`; `tests/test_fsutil.py::test_at37_converter_child_is_guarded`; `tests/test_fsutil.py::test_audio_extra_check_is_strict_in_ci`; `tests/test_llm.py::test_at29_prepare_prompt_fence_contract_and_no_subprocess` | PASS / CI R1 + audit r3 | 100 |
| X1 | Crash safety and corruption handling | `tests/test_ingest.py::test_at26_all_durable_boundaries_recover_once`; `tests/test_ocr.py::test_at25_fault_after_copy_before_meta_then_record_again`; `tests/test_wiki.py::test_fault_after_wiki_old_rename_recovers`; `tests/test_llm.py::test_at27_fault_after_body_copy_leaves_orphan_then_recovers` | PASS / CI R1 + audit r3 | 100 |
| X2 | Untrusted content handling | `tests/test_ocr.py::test_at27_hostile_peer_output_is_stored_as_data_only`; `tests/test_llm.py::test_at28_hostile_summary_rendered_inside_fence`; `tests/test_wiki.py::test_at32_view_inside_five_backtick_fence_and_hostile_content` | PASS / CI R1 + audit r3 | 100 |
| X3 | Complete CLI, JSON and exit contract | `tests/test_cli.py::test_at15_command_by_state_matrix`; `tests/test_cli.py::test_at34_parser_failures_are_one_json_object`; `tests/test_cli.py::test_at34_every_command_returns_a_valid_envelope`; `tests/test_cli.py::test_at34_warnings_and_exit_precedence` | PASS / CI R1 + audit r3 | 100 |
| I1 | Source unchanged after rename 1 | `tests/test_ingest.py::test_at26_all_durable_boundaries_recover_once`; `tests/test_ingest.py::test_at14_retry_reuses_completed_conversion_and_assets` | PASS / CI R1 + audit r3 | 100 |
| I2 | Completed conversion output produced at most once | `tests/test_convert.py::test_completed_output_reconciled_after_crash`; `tests/test_ingest.py::test_retry_faults_never_redo_completed_output`; `tests/test_ingest.py::test_ag_b2_pending_conversion_recovery_respects_completed_output`; `tests/test_ocr.py::test_at19_real_containers_ingest_then_approve` | PASS / CI R1 + audit r3 | 100 |
| I3 | Pure transcript view | `tests/test_transcript.py::test_view_only_verified_and_pure`; `tests/test_transcript.py::test_view_keeps_recorded_text_line_endings` | PASS / CI R1 + audit r3 | 100 |
| I4 | Approved OCR keys and new digests only | `tests/test_ocr.py::test_at21_only_files_of_approved_units_are_taken`; `tests/test_ocr.py::test_at23_mismatch_reopens_unit_and_blocks_stale_rerecord` | PASS / CI R1 + audit r3 | 100 |
| I5 | Verifying peer differs from recording peer | `tests/test_ocr.py::test_at22_verify_request_validation` | PASS / CI R1 + audit r3 | 100 |
| I6 | Unverified OCR excluded from view and wiki | `tests/test_transcript.py::test_view_only_verified_and_pure`; `tests/test_wiki.py::test_at33_only_verified_text_in_view` | PASS / CI R1 + audit r3 | 100 |
| I7 | Wiki derived only from raws | `tests/test_wiki.py::test_at30_build_twice_identical_and_only_expected_files`; `tests/test_wiki.py::test_at30_staging_and_hidden_dirs_ignored` | PASS / CI R1 + audit r3 | 100 |
| I8 | Restricted deletion targets | `tests/test_fsutil.py::test_at36_allowed_deletion`; `tests/test_fsutil.py::test_at36_other_deletion_targets_refused`; `tests/test_fsutil.py::test_at36_reparse_ancestor_refused_before_delete`; `tests/test_ingest.py::test_at36_hidden_and_reparse_are_skipped_without_following` | PASS / CI R1 + audit r3 | 100 |

Gate closeout and remaining release actions:

- R1 is closed for the revision above. All six matrix jobs passed, including
  `tests/test_e2e.py::test_e2e_text_ingest_duplicates_and_wiki`,
  `tests/test_e2e.py::test_e2e_raster_ocr_approve_record_verify`,
  `tests/test_e2e.py::test_e2e_llm_prepare_accept_and_rejection`, and
  `tests/test_e2e.py::test_e2e_status_on_empty_root_and_usage_error`.
  The separate `test_e2e_python_dash_m_entry_point` also passed.
- Both `.github/workflows/ci.yml::jobs.offline-clean-install` jobs passed.
  They built/downloaded wheels online, created fresh venvs, installed
  `secondbrain==1.0.0` with `--no-index`, verified installed package/module
  versions and location (plus markitdown-gc 0.3.5 and absent audio extras),
  then verified installed `sb --json status` exits 0 on an empty root.
- Final audit r3 completed the MECE/vertical/horizontal cross-check and voted
  APPROVE RELEASE. B2's removal assertions are automated; history-tag
  preservation is operator review evidence
  ([README history](../../README.md#history)). B10's simplicity and English,
  B6's owner permission, and G1/G2's pilot/concurrency/faithfulness remain
  review/operator responsibilities. Tests verify notices, caps, prompt
  content, schemas and peer identity; they do not prove that external peers
  followed instructions or enforce their profiles. See
  [USAGE prerequisites](../USAGE.md#operator-and-security-prerequisites).
- With all rows at 100 and clean installs passing, the orchestrator collects
  unanimous final release votes, promotes to `main`, runs the full matrix
  there, tags `v1.0.0`, and creates the GitHub Release with this sheet.
  No PyPI publication. These release actions are not claimed complete here.

Only this rubric and the cx release vote were edited in this evidence update;
no git commands, promotion, tag or release were performed.

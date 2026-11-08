# Slice 5 (OCR) — response to reviews

Files changed: `src/secondbrain/ocr.py`, `tests/test_ocr.py` (32 tests), this file.

## Fable (review_s5_fable.md)
- **M1 FIXED** — `COMMANDS.txt` emits `sb ocr record … --dpi N`. Additionally `approve` persists the effective dpi in
  scratch (`work/<id>/dpi.txt`; the meta schema has no field for it and foundation files are frozen), and `record` (and a
  later `approve` batch) inherit it when `--dpi` is omitted; an explicit `--dpi` wins. Tests: `test_effective_dpi_*`.
- **L1 REJECTED (design-literal)** — §4 guard says "approved units lack scratch"; recorded units keep their images until
  finalize. Re-render for lost images of recorded units is an r10 note for the orchestrator.
- **L2 FIXED** — `test_at22_literal_pending_key_is_rejected`.

## ag.effort
- **blocker (view/source_digest/accepted_text_present) REJECTED** — they live in `transcript.py` per IMPL_PLAN module layout; `ocr.py` must not own them.
- **quoting major FIXED** — each `peerhub` line is `-w "<dir>" --stream S "<prompt>"` with no inner quotes, `$` or backticks; the
  prompt names files relative to the `-w` folder (same shape as the guide's `Open p1.png.`), so it runs in cmd.exe and bash.
  Absolute quoted paths (design §5) moved to separate `Files:` lines. Test: `test_commands_peerhub_lines_have_no_inner_quotes`.
- **dpi major FIXED** — see M1.
- **pending order minor FIXED** — `sorted(units)` before slicing (and for COMMANDS/lacking lists).
- **zero-unit ready item minor REJECTED** — §4 matrix: a `–` cell is `state_not_allowed` (exit 2); `no_units` applies only to states the matrix allows (awaiting-approval/ocr-in-progress). Existing test `test_approve_guards_write_nothing`.

## argon
- **multi-batch major FIXED** — `test_multi_batch_flow_ignores_already_recorded_units` (record 30, leftover `u0001.md`, approve → only `u0031` rendered/asked, record → only `u0031`).
- **transcript.view major FIXED** — `test_transcript_view_follows_record_and_verify` (recorded/mismatch excluded, verified present after finalize, key order).
- **boundary minor FIXED** — `test_at17_large_boundary_is_21_units` (20 ok without ack, 21 rejected).
- **approve fault minor FIXED** — `test_fault_in_approve_before_meta_then_retry_succeeds`.

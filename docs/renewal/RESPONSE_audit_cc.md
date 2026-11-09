# Audit v1 — cc response (owner of ocr.py, wiki.py, llm.py, cli.py, `__main__.py` and their tests)

Suite: 567 passed, 4 skipped (the console-script e2e tests skip locally until `pip install -e .`; they fail under `CI`).

| Id | Disposition |
|---|---|
| V1 | FIXED — `test_ocr.py::test_at19_real_containers_ingest_then_approve` (slides.pptx, image.hwp, image.hwpx, image.xlsx): real ingest, approve, `work/<id>/uNNNN.<ext>` byte-equal to `raws/<id>/media/*`, no new subprocess, `converted.md` and the conversion ledger unchanged. |
| V2 | NOT MINE (convert.py / DESIGN row 1) — other implementer. |
| R1 | NOT MINE (orchestrator: CI run + RUBRIC). |
| H1 | DOC for orchestrator — list `triage, has_native_text, class, state, reason, error, ocr` as stage.json step outputs in §4. |
| H2 | DOC for orchestrator — add `work/<id>/dpi.txt` (effective render dpi; `record` and later `approve` batches inherit it when `--dpi` is omitted) to the §2 scratch list and §5. Kept in scratch because the meta schema has no dpi field and ledger.py is frozen for me. |
| H3 | DOC for orchestrator — §6: `summary.json` <= 64 KiB; `summary.md` is read only if <= 32000 bytes (8000 chars x 4), then checked at 8000 characters. |
| H4 | DOC for orchestrator — §8: `stale_work` = `work/<id>/` of a non-in-progress item holding anything except `llm/` (tolerated only when the item is ready). |
| H5 | FIXED — failed-item Transcript gate is `meta["conversion"] is not None`; `test_transcript_gate_follows_the_ledger_not_the_file_system` (orphan `converted.md` -> no section). |
| H6 | DOC for orchestrator — add `ext` to the §7 escaping sentence (code already escapes it). |
| H7 | NOT MINE (convert.py / ledger.activity). |
| V3 | FIXED — `cli._keys` strips each key; `ocr._keys` no longer has a string branch (callers pass lists); `test_cli.py::test_verify_lists_tolerate_spaces_around_keys`; the one test that passed a bare string now passes a list. |
| V4 | NOT MINE (ingest.py). |
| M1 | NOT MINE (convert.py). |
| S1 | BLOCKED on `fsutil.load_json_strict` (does not exist yet). When it lands, replace the loader in `llm.py` (`_unique` + `json.loads`) with it — a 6-line deletion. |
| S2 | PARTLY FIXED — `cli.run_status` no longer scans `raws/` itself: it reuses `wiki.load_items` (renamed from `_load`), so my modules have one scanner (was two). When `ledger.scan` lands, `wiki.load_items` becomes a one-line wrapper (or is deleted) and `ingest` switches too. |
| S3 | BLOCKED on `fsutil.write_bytes_atomic`; then delete `_write_bytes` in `ocr.py` and `llm.py`. |
| S4 | PARTLY FIXED — `cli.LARGE` removed (uses `ocr.LARGE`); `cli._units` removed (uses `wiki.unit_counts`, one definition of the cumulative counts). The shared `PEER` regex and raster/extension sets need a shared module owned by the other implementer (`llm.py` must not import `ocr.py`). |
| S5 | FIXED — `wiki.py` indexes `meta["error"]`, `meta["reason"]`, `meta["llm"]["summary"]` directly; the test that pinned the defensive branches is deleted. |
| S6 | FIXED for my files — `tree()` moved to `tests/helpers.py` (appended at the end; `test_ocr/wiki/llm/cli` use it); `ocr._io` uses `functools.wraps`; unused `from __future__` removed from `__main__.py`. The conftest-internals tests (`test_fsutil.py`) and the `test_ingest.py` copy of `tree()` are not mine. |

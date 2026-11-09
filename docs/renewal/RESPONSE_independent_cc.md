# RESPONSE to AUDIT_independent — cc (ocr.py, wiki.py, llm.py, cli.py + tests)

Suite: `python -m pytest -q -p no:cacheprovider` → 582 passed, 6 skipped (sb console script absent locally; the 4 original e2e + my 2 new).
The mixed-PDF e2e and the other e2e cases were run locally through `python -m secondbrain` (temporary shim, removed): pass.
`test_e2e_markdown_note_goes_straight_to_ready` FAILS until cx's convert fix lands (plain `.md` without media → ready/text-only).

| Deduction | Verdict |
|---|---|
| G1 −8 plain `.md/.html` ends `awaiting-approval` | NOT MINE (convert.py, cx). e2e test written and red until cx lands it. |
| G2 −5 no tags/links | FIXED: `wiki.tags()` = `class-*`, `ext-*` (`ext-other` for non-ascii), `collected-YYYY-MM`; `wiki/tags/<tag>.md` lists its sources; index has a `## Tags` section; source pages link their tags and the index. |
| G3 −5 transcript inside a text fence | FIXED: `wiki.safe_markdown()` (escape `<`/`>` except a leading blockquote marker, `![`→`&#33;[`, link targets other than http(s)/relative → `#`, inline and reference definitions; nothing fetched). Transcript stays the last section. Summary, banner, JSON subset and all metadata remain fenced/escaped. |
| V1 −5 `--writable` missing in DESIGN | DESIGN wording needed (below). |
| V2 −5 tags dropped from traceability | DESIGN wording needed (below). |
| V3 −5 DPI overwritten at second approve | FIXED: `work/<id>/dpi.json` is `{unit: dpi}`, merged per approve; `record` stamps each unit's own dpi (explicit `--dpi` still wins); `dpi.txt`, "inherit last dpi" and `--dpi` in COMMANDS.txt deleted; omitted `--dpi` = 200. Test: `test_second_approve_with_other_dpi_keeps_earlier_units_provenance`. |
| H1 −4, H2 −4, H3 −4 (RUBRIC, DESIGN layout) | NOT MINE (docs). |
| H4 −2 alias append skips `validate_meta` | NOT MINE (ingest.py). |
| H5 −2 `ocr verify` on ready deletes `llm/` | FIXED: `_clean()` removes everything but `work/<id>/llm/`. Test: `test_verify_on_ready_item_keeps_llm_scratch`. |
| M1 −6 `unknown` mixes two cases | NOT MINE (convert.py/DESIGN, cx). |
| M2 −3 no abandon edge | FIXED: `ocr decline` accepts `ocr-in-progress`; item becomes `ready`/`declined`, verified units stay in the view, scratch removed. Needed one line in ledger.py (`_ocr`: `declined` is exempt from the "disposition ⇔ any unit approved" equivalence) — outside my files, cx please keep it when merging. Tests: `test_decline_abandons_in_progress_item_keeping_verified_units`, CLI matrix cell now `M`. |
| S1 −10 staging ledger / recovery table | NOT MINE. |
| S2 −8 ~55 process files | NOT MINE (docs). |
| S3 −6 hand-written validator | NOT MINE (ledger.py). |
| S4 −6 hard-coded `cx`/`cc`/`*.effort`, copy-paste loop | FIXED (names): `ocr.TRANSCRIBER`, `ocr.VERIFIER`, `ocr.ask_line()` are the only place peer names, `-p <peer>.effort` and `--writable` are built; llm.py uses them. REJECTED (loop): the loop is the product boundary — `sb` never runs a peer (DESIGN §1); removing it needs a peer runner, i.e. more machinery. |
| T1 −8 no contract test vs real peerhub | REJECTED: the suite is offline by design (network guard + subprocess spy) and `peerhub` is not an installable dependency; a test that shells out to it cannot run in CI. The remedy is a live smoke step in the release gate (DESIGN §9 wording, below). The command shape stays covered by the regex test, which now also asserts `--writable` only on write asks. |
| T2 −4 DPI change untested | FIXED (V3 test). |
| T3 −3 e2e rasters only | FIXED: `test_e2e_mixed_pdf_selective_approval_record_verify_wiki` (mixed PDF approved, scan declined, text ready → record → verify → wiki + tags). |
| T4 −3 `.md` → ready e2e | WRITTEN (`test_e2e_markdown_note_goes_straight_to_ready`); red until cx's convert fix. Mixed-corpus wiki is covered by T3. |
| R1–R4 release readiness | NOT MINE. |

## DESIGN wording needed (docs owner)
- §2 layout: add `wiki/tags/<tag>.md`; §7: tag rule above and "the transcript is rendered as Markdown after the safety pass (no raw HTML, no image embeds, only http(s)/relative links; nothing is fetched); summary and metadata stay fenced"; traceability B3: "tags and links".
- §4 matrix: `ocr decline` allowed in `awaiting-approval` and `ocr-in-progress` (abandon; keeps verified units; unit statuses unchanged, scratch removed). §3/ledger: a declined item may hold verified units.
- §5 COMMANDS: write asks carry `--writable`, verify asks do not; `record` takes the dpi each unit was rendered at (`work/<id>/dpi.json`), COMMANDS.txt no longer prints `--dpi`.
- §9 release gate: add a live peer smoke step (one write ask, one read-only ask) before tagging.
- Known residual: a hostile document can now contain its own `## OCR uNNNN (...)` heading in the rendered transcript; the authoritative provenance is the JSON block at the top of each source page.

# RESPONSE to AUDIT_independent — cc (ocr.py, wiki.py, llm.py, cli.py + tests)

Combined candidate reconciliation: cx fixes and cc changes are present together; version remains 1.0.1.
Current required command `python -m pytest -q -p no:cacheprovider`: **601 passed, 6 skipped in 160.76s**, Windows/Python 3.15.2.
The six installed-console e2e cases skip because `sb` is absent locally, including Markdown-to-ready and mixed-corpus selective PDF.
The real local peerhub CLI-help contract passes. New CI/live peer/release success is not claimed.

| Deduction | Verdict |
|---|---|
| G1 −8 plain `.md/.html` ends `awaiting-approval` | FIXED in the combined candidate: cx source inspection makes media-free markup text-only/ready; the e2e regression is retained. |
| G2 −5 no tags/links | FIXED: `wiki.tags()` = `class-*`, `ext-*` (`ext-other` for non-ascii), `collected-YYYY-MM`; `wiki/tags/<tag>.md` lists its sources; index has a `## Tags` section; source pages link their tags and the index. |
| G3 −5 transcript inside a text fence | FIXED: `wiki.safe_markdown()` (escape `<`/`>` except a leading blockquote marker, `![`→`&#33;[`, link targets other than http(s)/relative → `#`, inline and reference definitions; nothing fetched). Transcript stays the last section. Summary, banner, JSON subset and all metadata remain fenced/escaped. |
| V1 −5 `--writable` missing in DESIGN | FIXED: reconciled DESIGN §5 documents shared `ocr.ask_line()` and write-only `--writable`. |
| V2 −5 tags dropped from traceability | FIXED: DESIGN §§2/7/11 include tag pages, the exact tag rule and traceability. |
| V3 −5 DPI overwritten at second approve | FIXED: `work/<id>/dpi.json` is `{unit: dpi}`, merged per approve; `record` stamps each unit's own dpi (explicit `--dpi` still wins); `dpi.txt`, "inherit last dpi" and `--dpi` in COMMANDS.txt deleted; omitted approve `--dpi` = 200; omitted record `--dpi` uses the unit’s stored value (fallback 200). Test: `test_second_approve_with_other_dpi_keeps_earlier_units_provenance`. |
| H1 −4, H2 −4, H3 −4 (RUBRIC, DESIGN layout) | NOT MINE (docs). |
| H4 −2 alias append skips `validate_meta` | NOT MINE (ingest.py). |
| H5 −2 `ocr verify` on ready deletes `llm/` | FIXED: `_clean()` removes everything but `work/<id>/llm/`. Test: `test_verify_on_ready_item_keeps_llm_scratch`. |
| M1 −6 `unknown` mixes two cases | NOT MINE (convert.py/DESIGN, cx). |
| M2 −3 no abandon edge | FIXED: `ocr decline` accepts `ocr-in-progress`; item becomes `ready`/`declined`, verified units stay in the view, scratch removed. Needed one line in ledger.py (`_ocr`: `declined` is exempt from the "disposition ⇔ any unit approved" equivalence) — now retained in the combined cx ledger. Tests: `test_decline_abandons_in_progress_item_keeping_verified_units`, CLI matrix cell now `M`. |
| S1 −10 staging ledger / recovery table | NOT MINE. |
| S2 −8 ~55 process files | NOT MINE (docs). |
| S3 −6 hand-written validator | NOT MINE (ledger.py). |
| S4 −6 hard-coded `cx`/`cc`/`*.effort`, copy-paste loop | FIXED (names): `ocr.TRANSCRIBER`, `ocr.VERIFIER`, `ocr.ask_line()` are the only place peer names, `-p <peer>.effort` and `--writable` are built; llm.py uses them. REJECTED (loop): the loop is the product boundary — `sb` never runs a peer (DESIGN §§5–6); removing it needs a peer runner, i.e. more machinery. |
| T1 −8 no contract test vs real peerhub | FIXED: retain cx’s `test_peerhub_contract.py`; the earlier offline-breaking rejection is withdrawn. It executes only local `peerhub ask --help` under a network/DNS guard, starts no peer and checks every generated OCR/verification/summary flag. `peerhub` is declared in `.[dev]`, which all six CI suites install. Local absence alone may skip; CI absence or help failure fails. Live peer smoke remains a separate DESIGN §12 gate. |
| T2 −4 DPI change untested | FIXED (V3 test). |
| T3 −3 e2e rasters only | FIXED: `test_e2e_mixed_pdf_selective_approval_record_verify_wiki` (mixed PDF approved, scan declined, text ready → record → verify → wiki + tags). |
| T4 −3 `.md` → ready e2e | FIXED in the combined candidate (`test_e2e_markdown_note_goes_straight_to_ready`); cx’s convert fix is present. Mixed-corpus wiki is covered by T3. |
| R1–R4 release readiness | NOT MINE. |

## DESIGN wording reconciled (docs owner)
- §2 layout now includes `wiki/tags/<tag>.md`; §7: tag rule above and "the transcript is rendered as Markdown after the safety pass (no raw HTML, no image embeds, only http(s)/relative links; nothing is fetched); summary and metadata stay fenced"; traceability B3: "tags and links".
- §4 matrix: `ocr decline` allowed in `awaiting-approval` and `ocr-in-progress` (abandon; keeps verified units; unit statuses unchanged, scratch removed). §3/ledger: a declined item may hold verified units.
- §5 COMMANDS: write asks carry `--writable`, verify asks do not; `record` takes the dpi each unit was rendered at (`work/<id>/dpi.json`), COMMANDS.txt no longer prints `--dpi`.
- §12 release gate: live peer smoke (one write ask, one independent read-only ask, plus summary output acceptance) is required before tagging.
- Known residual: a hostile document can now contain its own `## OCR uNNNN (...)` heading in the rendered transcript; the authoritative provenance is the JSON block at the top of each source page.

## Reconciliation decision

Keep the offline CLI-help contract test: invoking local help is compatible with the offline boundary and does not run a peer.
`.github/workflows/ci.yml` full-matrix installs `.[dev]`; `pyproject.toml` includes peerhub in that extra, and the test fails if it is
missing under CI. The manual operator loop remains intentional because sb never runs peers; this rationale is explicit in DESIGN §§5–6.
All wording items above are reflected in DESIGN, including `wiki/tags/<tag>.md`, partial decline, `dpi.json`, `ocr.ask_line()`, safe
Markdown, authoritative JSON provenance and the live-peer release gate. No git commands were used for reconciliation.

# Response to round-1 reviews (DESIGN.md r2, 2026-11-09)

Legend: ACCEPT (change, section of DESIGN r2) | REJECT (reason) | DUP (same as another id). Section numbers refer to r2.

## cx
- cx-1 ACCEPT. `unknown` is a first-class class (coverage partial/none or decision unknown); state `awaiting-approval`; path forward = decline (accept native text) or re-ingest images; native text kept. §3, §4, AT-10/11.
- cx-2 ACCEPT. Report validated before mapping (§3 step 2); rows reordered so top-down order is literally executable; malformed-report cases parametrized. §3, AT-05/06.
- cx-3 ACCEPT. Exact `has_native_text` algorithm; rasters are `ocr-required` by rule (EXIF/alt text are not native text); fixtures for empty table, image-only DOCX, alt text, malformed Markdown. §3, AT-07.
- cx-4 ACCEPT (by deletion). `--pages` removed; approve/decline are whole-item only; finalization requires every unit recorded. §4, §5. DUP ag-1, argon-2.
- cx-5 ACCEPT. Required set defined with n = recorded units and sample capped by remaining; unit keys zero-padded so order is total; repeated verify allowed. §5.
- cx-6 ACCEPT. Conversion output persisted as `converted.md` before triage; `--retry` resumes only missing steps; test asserts zero conversion calls after report-only failure. §4, AT-14.
- cx-7 ACCEPT. Staging dir + single atomic rename as commit point; inbox file deleted only after commit; staging always discarded on restart; `corrupt` only for committed dirs with invalid meta. §4 commit protocol, AT-30/31. DUP argon-9.
- cx-8 ACCEPT. Transcript is assembled by a pure function from `converted.md` + `ocr/*.md` (never appended), idempotent finalize, scratch deleted last; fault tests per boundary. §5, AT-24/25.
- cx-9 ACCEPT. Mismatch keeps the rejected revision as `ocr/uNNN.rN.md` with attribution, deletes the scratch file, and requires a new output with a different digest. §5, AT-23.
- cx-10 ACCEPT. Opaque candidate ids map to unit keys `u001…`; container images are extracted via markitdown's `extract_media` (covers HWP5, safe-member checks inside the tool); `sb` never parses ZIP. §5. DUP ag-3, argon-3.
- cx-11 ACCEPT in part. `status` shows every item with class, pages/images, candidates, coverage; LARGE ack scope defined. REJECT the 30-unit cap: approval is whole-item and explicit; the cap governs what a peer may do per chat approval and is reflected only in the batch plan in COMMANDS.txt. §5, §7.
- cx-12 ACCEPT. Untrusted content fenced with a nonce tag and declared as data; all validation outside the model (unit-key whitelist, size caps, schema, digest); LLM output staged in `work/` and published only by `sb llm accept`. `sb` cannot sandbox peers: stated explicitly as operator responsibility. §6, §8, AT-27/28. DUP ag-2, argon-5.
- cx-13 ACCEPT. Three-rule sanitizer for wiki bodies (no raw HTML, no auto-loading images, no active links), restricted front-matter grammar, escaped link text; raw transcript stays verbatim in raws. §7, AT-33.
- cx-14 ACCEPT. Python API with `enable_plugins=False`, resolved local regular file only, audio/network extensions mapped to `unsupported` before invocation, socket block in CI. §3, §9.
- cx-15 ACCEPT. Per-activity provenance record (tool, version, method, peer, model, UTC date, prompt revision, render settings); peer ids normalized and validated. §2, §5.
- cx-16 ACCEPT. Normative schema table with enums, nullability, allowed class/state pairs, validation outcomes; own front-matter grammar, no YAML dependency. §2.
- cx-17 ACCEPT. Conversion via Python API (typed exceptions); `--ocr-report` via pinned CLI with exact field mapping and stderr handling; `markitdown-gc==0.3.5`. §3.
- cx-18 ACCEPT. One envelope, per-command item `result` enums, error-code enum, exit precedence, JSON on parser errors. §8. DUP ag-7.
- cx-19 ACCEPT. Command-by-state matrix separates reads/no-ops from mutations; AT-14/AT-17 rewritten. §4, AT-15.
- cx-20 ACCEPT. Accepted LLM output lives in `raws/<id>/llm/`; `wiki/` is 100% derived and deleted on rebuild; invalid LLM output is rejected at `llm accept`, never written to wiki. §6, §7.
- cx-21 ACCEPT in part. `llm prepare/accept` require state `ready`; concepts removed from v1. REJECT unit-level citation validation: faithfulness is the operator's judgment at accept time; machine-checkable citations would need a schema we do not have (§10 Q4).
- cx-22 ACCEPT (by deletion). Transcripts are frozen in `ready`, so staleness cannot occur; the stale concept is gone. §6.
- cx-23 ACCEPT. LLM summary is rendered inside the source page (no cross-links); transcript links are rendered inert; one OCR section template; link validation test. §5, §7. DUP ag-9, argon-4.
- cx-24 ACCEPT (by deletion). Derived `wiki-built` removed; build input set = all of `raws/`; sort keys with id tie-breaker. §7.
- cx-25 ACCEPT. Projection table for every class/state; native text kept on declined/unfinished; unverified OCR never rendered. §7, AT-34.
- cx-26 ACCEPT. Traceability now starts from BRIEF/guide ids (B1–B10, G1–G4) to sections and tests. §11.
- cx-27 ACCEPT. Fixture list covers HWP5, HWPX, DOCX, XLSX images, same-page mixed PDF, malformed reports, missing dependency; conversion exceptions mocked separately from report JSON; characterization step before assertions. §9.
- cx-28 ACCEPT. AT-13 uses a real duplicate input with call spies; restart tests assert exact artifact/call counts; single specified result per failure point. §9.
- cx-29 ACCEPT. `filename` (exact) and `filename_nfc` stored separately; aliases are a set; identical repeat is a true no-op (no meta write). §2, AT-02/03.
- cx-30 ACCEPT. Explicit UTF-8 on every file and stdio reconfigure; bounded extension rule; path-length check with actionable error; absolute quoted paths in COMMANDS.txt; root precedence; reserved-name test done at unit level. §2, §8, AT-35.
- cx-31 ACCEPT (by deletion). `ingest` has no PATH args; finite inbox snapshot, reparse points skipped, retry selects by state. §4, §8.
- cx-32 ACCEPT. States reduced to five; `ingested`/`classified`/`wiki-built` gone; by-type/by-month folded into `index.md`; §9 claim corrected. §4, §7.
- cx-33 ACCEPT. New §12 release and closure gate (Python versions = CI matrix, offline clean-install test, v0.1 removal boundary, 100-score rubric, unanimous approvals).

## ag
- ag-1 ACCEPT. DUP cx-4 (deletion of partial approval).
- ag-2 ACCEPT. DUP cx-12 (nonce-tagged fence; validation outside the model).
- ag-3 ACCEPT. DUP cx-10 (unit keys; extraction via markitdown, flattened names, manifest mapping).
- ag-4 ACCEPT. `classified` removed; `unsupported` and `failed` are resting states. §4. DUP cx-32, argon-7.
- ag-5 ACCEPT. `unknown` class with `awaiting-approval` state. DUP cx-1.
- ag-6 REJECT. `_mdgc_guide.txt` states HWP/HWPX converters and triage are included in 0.3.5 ("pdf docx pptx xlsx hwp/hwpx included"; "Triage supports … HWP5 and HWPX"). Fixtures kept; the characterization step (§9) will surface any real gap before assertions are written.
- ag-7 ACCEPT. DUP cx-18 (uniform envelope).
- ag-8 ACCEPT. Single scratch tree `work/<id>/`; root has `inbox/ raws/ wiki/ work/`. §2. DUP argon-8.
- ag-9 ACCEPT. One heading template. DUP cx-23, argon-4.
- ag-10 REJECT. Every approval is already explicit per item with unit counts shown; a `sensitive` flag adds a second gate that the same operator passes in the same command, so it is ceremony without protection (cx-11 concurs). The approve output repeats the guide's "pages leave the machine" notice.

## argon
- argon-1 ACCEPT. Table reordered; executable top-down. DUP cx-2.
- argon-2 ACCEPT. Deletion option taken. DUP cx-4.
- argon-3 ACCEPT. DUP cx-10.
- argon-4 ACCEPT. DUP cx-23; unit keys are zero-padded so lexicographic order equals numeric order.
- argon-5 ACCEPT. DUP cx-12.
- argon-6 ACCEPT. `wiki build` covers all states with a projection table; `llm prepare/accept` guarded by state `ready`. §4, §7.
- argon-7 ACCEPT. Transient states deleted. DUP cx-32.
- argon-8 ACCEPT. Single `work/` tree; `report.json` dropped (triage summary lives in meta). §2.
- argon-9 ACCEPT. DUP cx-7 (staging + atomic rename + unlink last).
- argon-10 ACCEPT. Unit status enum `pending | recorded | verified` in §2; tests for status counts JSON and index dates (UTC) added; `--pages` tests moot after deletion.
- argon-11 ACCEPT (recorded as resolved in §10): Q2 drop `classified` (done), Q3 copy transcript (done, sanitized), Q4 file adapter (kept), Q5 deterministic sample (kept, capped), Q6 16-char id (kept), Q7 committed fixtures (kept), Q9 delete scratch at verify (kept). Q1 superseded by the `unknown` class (cx-1).

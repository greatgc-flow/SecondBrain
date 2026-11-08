# Response to round-2 reviews (DESIGN.md r3, 2026-11-09)

Legend: ACCEPT (change, r3 section) | REJECT (reason) | ACK (reviewer marked resolved; no change). Orchestrator guidance adopted in
full: no sampling, 30-unit approval batches, extraction once at ingest, copy-then-hash staging with resume, security boundary as
explicit non-claims, bidirectional traceability, complete envelope. r3 is shorter than r2 (fewer artifacts: no `transcript.md`,
no front matter, no custom header grammar, no sanitizer rules, no renames).

## cx (round-1 ids)
- cx-1 ACCEPT. Rows 7–8 with partial/none coverage keep `coverage` in meta and the wiki banner permanently, including on `ready` pages; residual uncertainty is accepted explicitly and tested. §3, §7, AT-10.
- cx-2 ACCEPT. Exact report-to-meta adapter with types, defaults, rejections (unique ids, PDF id grammar, page bound) and malformed-field fixtures. §3 step 3, AT-06.
- cx-3 ACK.  cx-4 ACK.  cx-6 ACK.  cx-9 ACK.  cx-10 ACK.
- cx-5 ACCEPT (by deletion). Sampling removed; every unit is verified by a second peer. §5.
- cx-7 ACCEPT. Staging is resumed, not discarded: `original<ext>` and `converted.md` present in staging are reused; only triage/classify rerun; one conversion per item across every pre-commit failure point. §4, AT-26.
- cx-8 ACCEPT. One reconciliation rule for every mutation (artifact first, meta last, orphans ignored, referenced-but-missing = corrupt); no renames (attempt files `uNNNN.aN.md`); approve is idempotent re-render; accept idempotent. §4 "Mutation rule", AT-25/26/27.
- cx-11 ACCEPT. One approval = next <= 30 pending units in key order; larger items need further explicit `approve` calls; `--yes-large` once per item > 20; JSON carries pages/images/coverage. §5, §8, AT-17.
- cx-12 ACCEPT (scoped). New §6 Security boundary: explicit non-claims, operator prerequisite (peer profile: read `raws/`, write only `work/<id>/`, no other paths), and what `sb` validates on import. Tests cover only `sb`'s validation; isolation is review evidence, not a test claim. §6.
- cx-13 ACCEPT (by deletion). Untrusted bodies are rendered inside a fenced block whose fence exceeds the longest backtick run (nothing is active: no images, links, HTML or reference definitions); the three inline rules are gone. §7, AT-32.
- cx-14 ACCEPT (scoped). Audio extras are not installed (renamed audio -> `MissingDependencyException` -> unsupported, tested); plugins disabled; local regular paths only; claim narrowed to "no network required; in-process sockets blocked in CI; the report subprocess is the pinned tool with no network feature invoked". §3, §6, AT-12, AT-37.
- cx-15 ACCEPT. Activity fields typed with nullability per method; effective dpi and charset recorded; tool version null when not observed by `sb` (stated). §2, AT-20, AT-22.
- cx-16 ACCEPT. Compact validator contract: field rules, status-dependent attempt rules, artifact consistency, orphan vs corrupt. §2.
- cx-17 ACK.  cx-20 ACK.  cx-21 ACK (acceptance is a human faithfulness judgment, now stated in §6).  cx-22 ACK.  cx-23 ACK.  cx-24 ACK.  cx-25 ACK.
- cx-18 ACCEPT. Item fields include pages/images/coverage/units; envelope has `warnings`; all mutating commands validate the whole request before writing, so exit 2 always means "nothing written". §8, AT-34.
- cx-19 ACCEPT. Matrix cells name the exact allowed writes (none / alias / scratch / wiki); AT-15 tests those. §4.
- cx-26 ACCEPT. Every AT carries requirement ids; every invariant lists its tests; G2 exact-digit check is in the verify prompt and recorded as `result`. §5, §9, §11.
- cx-27 ACCEPT. `malformed.md` moved to `unknown/`, `alt-text-only.docx` to `ocr/`; `EXPECTED.md` characterization is a gate before implementation (§12 gate 1b), not deferred to coding. §9.
- cx-28 ACCEPT. Fault tests per interruption point for ingest, approve, record, verify, accept, wiki swap, each with one specified outcome and call counts. AT-25–AT-27.
- cx-29 ACK.  cx-30 ACK.  cx-31 ACK.  cx-32 ACK.  cx-33 ACK (N9 applied).

## cx (new, N)
- N1 ACCEPT. Media extracted inside the single conversion call at ingest for container formats; kept in `raws/<id>/media/` only when the class needs OCR; approve never converts. §3, §4 I2, AT-19.
- N2 ACCEPT (narrowed). Mapping to member ids dropped; container units are asset-level (`source` = asset filename); loss of location precision stated in §5 and §10.
- N3 ACCEPT. Copy to staging first, hash the staged copy, commit by rename, unlink inbox only if size+mtime still match the snapshot, else warn `inbox_changed`. §4, AT-26.
- N4 ACCEPT. Whole-request validation for verify (known keys, status recorded, disjoint, canonical peer, independence) before any write. §5, AT-22.
- N5 ACCEPT (by deletion). No sampled-out units; I6 holds literally. §4, §5.
- N6 ACCEPT. OCR class with zero units is reclassified `unknown` (`no_units`) at ingest; approve requires non-empty units for every source type. §3 row 9, AT-11.
- N7 ACCEPT. Deletion rule (owned dirs only, real directories under the resolved root, no reparse points); wiki built in `wiki.tmp/` and swapped with defined recovery. §4, §7, AT-30.
- N8 ACCEPT. `sb ingest --charset NAME` passed to the converter and recorded in `conversion.params`; Korean content fixture. §3, §8, AT-08.
- N9 ACCEPT. CI matrix 3.11/3.12/3.13 x Windows/Ubuntu; UTF-8 without BOM, LF for generated text. §9, §12.
- N10 ACCEPT. `accepted_text_present` defined independently of headers and markers; guard for `llm prepare`. §6, AT-29.
- N11 ACCEPT. Durable `transcript.md` deleted (view computed by one pure function used by wiki and LLM prepare); LLM metadata is JSON (`summary.json`) plus a UTF-8 body; wiki front matter deleted. §2, §6, §7.
- N12 ACCEPT. Keys `u0001…u9999` (item bound 9999 units, else failed `too_many_units`); PDF ids sorted numerically before key assignment. §5, AT-18.

## ag
- ag-B1 ACCEPT. Pipeline is staged with short-circuit: pre-checks -> conversion -> triage -> native text; nothing is evaluated on a missing artifact. §3.
- ag-B2 ACCEPT (by deletion). No verification set; every unit verified. §5.
- ag-M1 ACCEPT. I2 now holds literally: extraction happens in the single ingest conversion call (N1). §4.
- ag-m1 ACCEPT. COMMANDS.txt uses the unit file path `uNNNN<ext>`. §5.
- ag-m2 ACCEPT (by deletion). No sampled-out units. §5.
- ag-m3 ACCEPT. All mutating commands validate first; any invalid unit output -> exit 2, nothing written. §8.

## argon
- argon-1 ACCEPT. Nonce is regenerated until absent from the view; empty content -> `not_eligible` error code. §6, §8.
- argon-2 ACCEPT. Orphan rule: unreferenced files are ignored; `wiki build` uses `meta.llm.summary` only; `llm accept` idempotent. §4, §6.
- argon-3 ACCEPT (by deletion). Fenced rendering removes the backtick-wrapping problem. §7.
- argon-4 ACCEPT. §10 records argon's confirmation; items 2–5 closed; item 1 narrowed per N2 and kept open for cx/ag confirmation.

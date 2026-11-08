### 1. Verification of Round-1 Findings (argon-1..11)
- **argon-1**: RESOLVED — §3 classification table is ordered top-down as an executable decision table, verified exhaustively by AT-05.
- **argon-2**: RESOLVED — Partial `--pages` approval/decline is removed (§8, §10.3); approval/decline is whole-item only.
- **argon-3**: RESOLVED — Candidate IDs are mapped to flat zero-padded unit keys (`u001`…) via `work/<id>/manifest.json` (§9 AT-18, AT-19, AT-21).
- **argon-4**: RESOLVED — Zero-padded unit keys (`uNNN`) make lexicographic order equal numeric order; header template is tested in AT-22.
- **argon-5**: RESOLVED — `<source-<nonce>>` fencing, data-not-instructions rules, external header/SHA/size validation (§6), and Markdown/HTML sanitization (§7) are specified and tested (AT-27, AT-28, AT-29, AT-32).
- **argon-6**: RESOLVED — `wiki build` defines a complete state/class projection table (§7, AT-33) and `llm prepare` is guarded by `state == ready` (§6, AT-29).
- **argon-7**: RESOLVED — Transient states `ingested` and `classified` are deleted; only the 5 persisted states remain (§9 AT-16, §10.6, §11 B10).
- **argon-8**: RESOLVED — Scratch is unified under `work/<id>/` and separate `report.json` is dropped in favor of `meta.json` triage fields (§6, §9, §10.5).
- **argon-9**: RESOLVED — Staging + atomic rename + unlink-last commit protocol is specified and fault-injection tested (AT-25, AT-26).
- **argon-10**: RESOLVED — Unit status enum (`pending | recorded | verified`), JSON `units`/`counts` fields, and UTC index dates are unified in §7, §8, and §9 (AT-16, AT-31).
- **argon-11**: RESOLVED — All r1 open questions are recorded as resolved in §10.6 and reflected across §6–§9.

### 2. New Findings in Revised Text (§6–§12)
1. [SEV minor] §6 vs §8 — Nonce collision or empty transcript in `llm prepare` lacks an explicit error code in the §8 exit-2 enum (`state_not_allowed` covers state/class, but nonce collision in `<source-<nonce>>` is unnamed). — Derive the 16-hex nonce until it does not appear in `transcript.md` (eliminating collision failure), and map empty-transcript rejection to `state_not_allowed`.
2. [SEV minor] §6 & §7 — If a crash occurs during `llm accept` after `tmp+replace` of `raws/<id>/llm/summary.md` but before `meta.json` is updated, an orphan `summary.md` exists on disk. — Specify that `wiki build` includes the summary iff `meta.llm.summary` is present (ignoring unreferenced files), and `llm accept` is idempotent on re-run.
3. [SEV minor] §7 — Sanitizer rules (2) and (3) wrap extracted URLs in single backticks, which can break if the URL itself contains backticks or reference-style link definitions (`[id]: url`). — Escape or strip backticks inside sanitized URLs and neutralize reference-link lines (`^\s*\[[^\]]+\]:`).
4. [SEV minor] §10 — Confirmation of peer questions 1–5: (1) OCRing all extracted container images (`[no text]` for decorative ones), (2) declining/re-feeding `unknown` items without units, (3) whole-item approve/decline, (4) operator-judged LLM faithfulness in v1, and (5) storing triage solely in `meta.json` are all confirmed as the right VerySimpleGuide trade-offs. — Record peer confirmation and close §10.1–10.5.

VOTE: APPROVE

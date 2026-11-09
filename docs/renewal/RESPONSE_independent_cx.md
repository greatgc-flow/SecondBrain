# Independent audit response — cx (2026-11-09)

Scope: convert/ingest/ledger/fsutil/errors/transcript and their tests; sole DESIGN editor; RUBRIC, renewal cleanup, CHANGELOG.
`FIXED` describes the cx-owned change and evidence. `REJECTED(reason)` explicitly leaves work outside cx ownership or declines a
proposed simplification; it does not dismiss the reported defect. This reconciliation covers the combined cx/cc candidate; external
CI, live peer execution and release actions still need their own evidence.

| Audit deduction | Disposition | Change / evidence |
|---|---|---|
| §1 −8: all markup unknown | FIXED | `convert._inspect_markup` inspects original source before conversion can erase media tags. Media-free `.md/.html/.htm` stores complete local triage and becomes text-only/ready without a report subprocess. Real ingest tests cover prose/empty text and inline/reference/shortcut/malformed images, HTML img/svg/object/iframe, case and embedded HTML. |
| §1 −5: missing tags/cross-source links | FIXED | Combined cc implementation generates class/extension/collected-month tag pages and source/index/back links. DESIGN §§2/7/11 now specify the exact rule and `wiki/tags/<tag>.md`; `test_tags_pages_index_links_and_back_links` covers navigation. |
| §1 −5: fenced transcripts | FIXED | Combined cc `wiki.safe_markdown()` preserves headings/lists/tables, neutralizes HTML/images/unsafe destinations and fetches nothing. DESIGN §7 records the pass and authoritative JSON provenance; summaries/banners/metadata stay fenced. |
| §2 −5: writable missing from design | FIXED | DESIGN §5 explicitly requires `--writable` on transcription/summary asks and omits it from verification. `test_peerhub_contract.py` checks flags from both generated workflows against installed CLI help. |
| §2 −5: tags dropped from traceability | FIXED | DESIGN §11 B3 includes tags/cross-source links; separate B3-tags traces BRIEF owner decision 2 to §7 and wiki regressions. |
| §2 −5: DPI overwritten between approvals | FIXED | Combined cc approval merges per-unit `work/<id>/dpi.json`; record defaults to each unit’s own DPI and generated commands omit `--dpi`. Explicit record DPI remains an operator override, matching the reconciled DESIGN §5. Regression: `test_second_approve_with_other_dpi_keeps_earlier_units_provenance`. |
| §3 −4: inconsistent rubric counts | FIXED | Replaced conflicting prior-revision counts with one current-worktree result below; integrated CI counts must come from the exact candidate. |
| §3 −4: stale release text | FIXED | RUBRIC consistently targets v1.0.1 and distinguishes local evidence from pending integrated CI/live smoke/release actions. No stale promotion claim or automatic 100 score remains. |
| §3 −4: retained stage absent from layout | FIXED | DESIGN §2 lists committed `stage.json` as the retained ingest checkpoint, separate from authoritative meta. |
| §3 −2: alias append bypasses validation | FIXED | `ingest._resume` calls `validate_meta` before atomic alias commit. Injected rejection leaves meta unchanged and staged source intact; rerun appends once. |
| §3 −2: ready verify deletes llm scratch | FIXED | Combined cc `_clean()` and DESIGN §§4–5 preserve `work/<id>/llm/`, including verify-on-ready. Regression: `test_verify_on_ready_item_keeps_llm_scratch`. |
| §4 −6: unknown conflates no media/incomplete inspection | FIXED | DESIGN §3 now reserves unknown for incomplete inspection. Decoded media-free source gets complete local evidence; uninspected references/undecodable source remain conservative. Existing exhaustive classification test stays applicable. |
| §4 −3: no abandon edge | FIXED | DESIGN §§4–5 permit decline from ocr-in-progress. Ledger accepts ready/declined with preserved pending/approved/recorded/verified units while still validating every attempt/digest; a regression proves corruption is rejected. Combined cc command and CLI matrix now permit the abandon edge. |
| §5 −10: staging/recovery/digests too complex | REJECTED(removal would weaken crash safety) | Recovery already reuses `_resume`, not a second state machine. Keep the claim ledger, pending conversion intent and artifact digests: without them a restart can lose claimed originals, rerun completed conversion, or accept half-committed bytes. Replaced DESIGN's eight-row recovery table with the shared forward path and restart conditions. Existing durable-boundary/fault tests are retained. |
| §5 −8: historical process docs/dense design | FIXED | Deleted 49 historical review/vote/response files. Kept core docs, audits, tool evidence and independent responses. DESIGN drops historical parity/vote prose, duplicated acceptance scripts and the recovery table; contract additions remain. |
| §5 −6: repeated handwritten full schema | FIXED | Removed the duplicate report/count/candidate validator from convert: adapter and stage/meta reads now share `ledger.validate_triage`. Keep state/attempt/path/digest checks on reads: local files and crash leftovers can change outside the process, so a cache or schema-only parser cannot safely replace validation. No new dependency or validator framework. |
| §5 −6: manual loop/hard-coded peers | REJECTED(removing the operator loop requires a peer runner) | cc centralizes names/profiles/write flags in `ocr.TRANSCRIBER`, `ocr.VERIFIER` and shared `ocr.ask_line()` used by OCR/LLM. DESIGN §§5–6 retain the manual loop: sb never runs peers; owner approval and independent verification remain operator responsibilities. |
| §6 −8: no real peerhub contract test | FIXED | Keep `test_peerhub_contract.py`: it executes only local `peerhub ask --help` under the child network/DNS guard, checks every generated flag and starts no peer. The previous cc offline-breaking rejection is withdrawn in both responses. Verified CI full-matrix installs `.[dev]` and pyproject declares peerhub there; local absence alone may skip, CI absence/help failure fails. |
| §6 −4: repeat-approval DPI untested | FIXED | Combined cc `test_second_approve_with_other_dpi_keeps_earlier_units_provenance` covers multiple approvals with different DPI; DESIGN §5 matches default per-unit lookup and explicit record override. |
| §6 −3: mixed PDF selective OCR e2e missing | FIXED | Combined cc `test_e2e_mixed_pdf_selective_approval_record_verify_wiki` covers approved mixed PDF, declined scan, ready text, record/verify, wiki and tags. Installed-console availability is reported in the current run below. |
| §6 −3: unknown markup/mixed corpus e2e missing | FIXED | cx real markup ingest integration and combined cc `test_e2e_markdown_note_goes_straight_to_ready` cover no-media ready behavior; mixed-corpus wiki is exercised by the selective-PDF e2e. Installed-console availability is reported below. |
| §7 −10: CI pending/unmerged/untagged | REJECTED(release operator scope; user explicitly prohibited git) | No merge/tag/release or CI success is fabricated. RUBRIC leaves exact-candidate CI, live smoke and release actions pending. |
| §7 −5: stale release sheet | FIXED | RUBRIC targets v1.0.1, retains the original 25 requirement/invariant rows, and requires consistent exact-candidate evidence before scores become 100. |
| §7 −5: release gate lacks live peer smoke | FIXED | DESIGN §12 requires generated writable OCR and summary asks, independently verified OCR, accepted outputs, workspace/provenance/DPI checks and recorded live evidence. This is a gate contract change; the live operator run is still pending. |
| §7 −5: no release changelog | FIXED | Added root CHANGELOG.md with separate 1.0.0 and unreleased 1.0.1 entries; combined runtime changes are described together, with release gates still pending. |

## Test-first evidence

- Before implementation, real prose Markdown/HTML/HTM and empty markup failed with unknown instead of text-only; alias-validation
  rejection failed because the write succeeded. Reference/malformed media cases stayed conservative.
- Partial-decline ledger regression failed with `Disposition/unit mismatch`; after the one-condition fix it passes and still rejects
  changed preserved attempt bytes. The shared-validator refactor retains existing malformed-report and corrupt-ledger coverage.
- Focused run: 367 passed (`test_peerhub_contract.py`, `test_convert.py`, `test_ingest.py`, `test_ledger.py`); the later-added partial-decline
  regression also passed independently. Installed peerhub help lists `-p`, `-w`, `--stream`, `--writable`; both workflows pass the contract.
- Current combined-candidate command `python -m pytest -q -p no:cacheprovider`: **601 passed, 6 skipped in 160.76s**,
  Windows/Python 3.15.2. Six installed-console e2e cases skip because `sb` is absent locally; the real peerhub help contract passes.
  This confirms the combined runtime/tests locally without claiming new CI, live peer execution or release evidence.

## Integration notes

The combined candidate keeps unit statuses/attempts on decline, with the cx ledger validating all retained artifacts. No schema bump.
Source inspection uses triage scope `markup_source`, complete coverage and null page counts; no units are invented. cc wiki/tag/DPI/
cleanup and e2e changes are now present. DESIGN records all cc wording items, including per-unit override semantics and JSON provenance.

Decision shared with the cc response: retain the real local CLI-help contract test. It starts no peer, makes no network request and
remains protected by a help-only subprocess guard plus child network/DNS guard. The existing CI full-matrix installation of `.[dev]`
includes peerhub; CI absence fails rather than silently skipping. Retain live peer smoke as a separate release gate and the manual
operator loop as sb’s security boundary. The independent audit stays unchanged. No git commands were run.

## Round 2 — cx closeout

- FIXED — R2 MECE −2 and test-adequacy −3 (cx portion): source media detection now includes embed/video/audio/picture/source,
  src/srcset/poster attributes in tags, and quoted/unquoted, case-insensitive image inputs. Eleven new real-ingest cases cover these
  boundaries plus text inputs and ordinary prose staying ready. Before the fix nine media cases failed; after it all eleven pass.
- FIXED — R2 horizontal −3: USAGE now documents tag pages/navigation, decline from awaiting or ocr-in-progress with retained verified
  text/history, and OCR cleanup preserving LLM scratch. Updated per-unit DPI and safe Markdown descriptions to match current behavior.
- FIXED — R2 horizontal −2: RUBRIC links [LIVE_SMOKE_v1.0.1.md](LIVE_SMOKE_v1.0.1.md) and records the smoke date, source revision,
  Python/peerhub/converter versions and both observed OCR/LLM outcomes. The orchestrator owns the full appended smoke evidence;
  the recorded peerhub 0.24.0 smoke is distinguished from the new 0.24.1 dev pin. This supersedes the earlier pending-smoke wording.
- FIXED — R2 release −2: dev extra pins `peerhub==0.24.1`; the dependency contract test asserts the exact pin. It failed before the pin
  and passed afterward. CI still installs `.[dev]`; the real local CLI-help contract remains offline and never starts a peer.
- Test-first targeted run: 10 failed, 2 passed before implementation; **12 passed** after implementation (media cases + pin check).
- Required command `python -m pytest -q -p no:cacheprovider`: **612 passed, 6 skipped in 148.97s** (Windows/Python 3.15.2).
  The six existing console e2e cases skip because `sb` is absent locally; the real peerhub help contract passes. No git commands used;
  cc-owned runtime/tests and smoke evidence were not edited.

## Round 3 — cx closeout

- FIXED — R3 simplicity −1: `safe_delete(root, target, keep=())` preserves named direct children in place, while keeping the same
  deletion allow-list, whole-tree reparse pre-scan (including retained subtrees), containment checks and read-only error handler.
  With no retained child the target itself is removed as before. `ocr._clean` is now one call with `keep=("llm",)`; park/restore and
  its unused os import are gone. No stranded `work/<id>.llm` path or rename crash window is introduced.
- FIXED — R3 deletion regression coverage: nine test-first cases cover direct kept files/directories, non-kept nested names, repeat/
  missing cleanup, reparse points in removed and kept subtrees, interrupted child removal/retry, Windows read-only versus other
  permission failures, and an OCR cleanup that forbids every rename. All nine failed before implementation; all pass afterward.
  Full filesystem/OCR focused run: **108 passed**.
- FIXED — R3 vertical −1: DESIGN §7 exempts only properly closed top-level column-0 fences and unambiguously paired same-line code
  spans. Indented/container/unclosed fences, unmatched/cross-line spans and ambiguous paragraph pairing receive no exemption;
  everything outside the allowed code is escaped, including table/pipe lines.
- FIXED — R3 LLM provenance contract (cx documentation portion of horizontal −2): DESIGN §§2/6/8 require
  `sb llm accept ID --peer P --model M`, validate/canonicalize the operator peer with `ocr._peer`, use the operator peer/model for
  activity attribution and keep peer self-report in `params.reported` as untrusted provenance. cc owns the runtime/CLI/tests.
- Required command `python -m pytest -q -p no:cacheprovider`: **623 passed, 6 skipped in 125.90s**, Windows/Python 3.15.2.
  Six installed-console cases skip because `sb` is absent locally. RUBRIC now records this exact cx worktree count; cc’s Round 3
  wiki/LLM changes are not merged here yet, so final combined local evidence must be refreshed after that merge. CI counts remain
  orchestrator-owned; no combined/CI result is inferred from this run.
  No git commands used. Outside ocr.py's `_clean` and its now-unused import, no OCR runtime code was changed.

## Round 4 — cx closeout

- FIXED — R4 test adequacy −2 (cx dependency portion): dev extra now pins `markdown-it-py==4.2.0`, so CI's `.[dev]` install
  supplies the real renderer used by the differential tests. The dependency assertion failed before the edit and passes afterward;
  the existing renderer differential test also passes in this local environment. No test files were changed outside cx's assignment.
- FIXED — R4 rendering contract: DESIGN §7 and USAGE now require all `<` and `>` in untrusted text to be escaped everywhere,
  including code (displayed as entities), with no exemptions. Exact code display is deliberately sacrificed to avoid a partial
  CommonMark masker disagreeing with the renderer and restoring raw HTML/images. cc owns the runtime and bypass regressions.
- FIXED — R4 vertical −1 and horizontal −1 (USAGE): summary activity params contain only `prompt_rev`; JSON peer/model fields
  are informational, not validated or retained as attribution. Only required CLI `--peer`/`--model` supplies recorded peer/model;
  CLI peer canonicalization/validation is separate from summary-file checks. Removed the nonexistent reported-provenance field
  and summary-JSON peer-regex promise from DESIGN/USAGE, matching llm.py and the ledger.
- FIXED — R4 horizontal −1 (RUBRIC): cite the latest existing smoke at `22e3e85d3efd44c07d7c52a100e7d14c4e481112`, 02:12Z,
  via [LIVE_SMOKE_v1.0.1.md](LIVE_SMOKE_v1.0.1.md), including verify-on-ready preserving LLM scratch and actual observed versions.
  The orchestrator owns the Round 4 post-merge smoke rerun/new SHA, merged local count and CI counts; these are left explicit
  rather than representing this documentation/dependency run as final merged evidence.
- The initial required full-suite run reported **158 failed, 478 passed, 6 skipped**: the shared interpreter now has markitdown-gc
  0.3.6, violating the project’s unchanged 0.3.5 pin. A representative CLI failure explicitly reports that version mismatch.
  Retrieved the already-cached 0.3.5 wheel without network and extracted it under `work/r4-pinned`; set this workspace-only
  PYTHONPATH for a repeat run, leaving the shared interpreter unchanged.
- Repeat `python -m pytest -q -p no:cacheprovider` with cached markitdown-gc **0.3.5** and local markdown-it-py **4.2.0**:
  **636 passed, 6 skipped in 117.86s**. The six installed-console e2e cases skip because `sb` is absent locally; the real renderer
  differential and peerhub-help tests pass. This is cx verification, not the orchestrator’s final Round 4 merged count or smoke SHA.
  No git commands used; no runtime/test source files were edited. A temporary `.pytest-r4-diagnose` directory remains because
  automatic approval review rejected its cleanup with the stated reason `blocked by policy`.

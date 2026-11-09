# Independent audit response — cx (2026-11-09)

Scope: convert/ingest/ledger/fsutil/errors/transcript and their tests; sole DESIGN editor; RUBRIC, renewal cleanup, CHANGELOG.
`FIXED` describes the cx-owned change and evidence. `REJECTED(reason)` explicitly leaves work outside cx ownership or declines a
proposed simplification; it does not dismiss the reported defect. cc runtime/tests and integrated release evidence are not claimed here.

| Audit deduction | Disposition | Change / evidence |
|---|---|---|
| §1 −8: all markup unknown | FIXED | `convert._inspect_markup` inspects original source before conversion can erase media tags. Media-free `.md/.html/.htm` stores complete local triage and becomes text-only/ready without a report subprocess. Real ingest tests cover prose/empty text and inline/reference/shortcut/malformed images, HTML img/svg/object/iframe, case and embedded HTML. |
| §1 −5: missing tags/cross-source links | REJECTED(runtime belongs to cc) | DESIGN §7 now requires deterministic tags and related-source links; B3 and B3-tags trace them explicitly. cc owns wiki code/tests. |
| §1 −5: fenced transcripts | REJECTED(runtime belongs to cc) | DESIGN §7 now requires safe Markdown headings/lists/tables; summary/metadata fencing remains. cc owns renderer and hostile-content regressions. |
| §2 −5: writable missing from design | FIXED | DESIGN §5 explicitly requires `--writable` on transcription/summary asks and omits it from verification. `test_peerhub_contract.py` checks flags from both generated workflows against installed CLI help. |
| §2 −5: tags dropped from traceability | FIXED | DESIGN §11 B3 includes tags/cross-source links; separate B3-tags traces BRIEF owner decision 2 to §7 and wiki regressions. |
| §2 −5: DPI overwritten between approvals | REJECTED(runtime belongs to cc) | DESIGN §5 binds recorded DPI to each unit's actual render, including repeat approvals and explicit record DPI; the global last-approval value cannot relabel an older render. cc owns scratch format and OCR regressions. |
| §3 −4: inconsistent rubric counts | FIXED | Replaced conflicting prior-revision counts with one current-worktree result below; integrated CI counts must come from the exact candidate. |
| §3 −4: stale release text | FIXED | RUBRIC consistently targets v1.0.1 and distinguishes local evidence from pending integrated CI/live smoke/release actions. No stale promotion claim or automatic 100 score remains. |
| §3 −4: retained stage absent from layout | FIXED | DESIGN §2 lists committed `stage.json` as the retained ingest checkpoint, separate from authoritative meta. |
| §3 −2: alias append bypasses validation | FIXED | `ingest._resume` calls `validate_meta` before atomic alias commit. Injected rejection leaves meta unchanged and staged source intact; rerun appends once. |
| §3 −2: ready verify deletes llm scratch | REJECTED(runtime belongs to cc) | DESIGN §§4–5 now preserve `work/<id>/llm/` during OCR cleanup, including verify-on-ready. cc owns cleanup/runtime regression. |
| §4 −6: unknown conflates no media/incomplete inspection | FIXED | DESIGN §3 now reserves unknown for incomplete inspection. Decoded media-free source gets complete local evidence; uninspected references/undecodable source remain conservative. Existing exhaustive classification test stays applicable. |
| §4 −3: no abandon edge | FIXED | DESIGN §§4–5 permit decline from ocr-in-progress. Ledger accepts ready/declined with preserved pending/approved/recorded/verified units while still validating every attempt/digest; a regression proves corruption is rejected. cc owns command/state-matrix changes. |
| §5 −10: staging/recovery/digests too complex | REJECTED(removal would weaken crash safety) | Recovery already reuses `_resume`, not a second state machine. Keep the claim ledger, pending conversion intent and artifact digests: without them a restart can lose claimed originals, rerun completed conversion, or accept half-committed bytes. Replaced DESIGN's eight-row recovery table with the shared forward path and restart conditions. Existing durable-boundary/fault tests are retained. |
| §5 −8: historical process docs/dense design | FIXED | Deleted 49 historical review/vote/response files. Kept core docs, audits, tool evidence and independent responses. DESIGN drops historical parity/vote prose, duplicated acceptance scripts and the recovery table; contract additions remain. |
| §5 −6: repeated handwritten full schema | FIXED | Removed the duplicate report/count/candidate validator from convert: adapter and stage/meta reads now share `ledger.validate_triage`. Keep state/attempt/path/digest checks on reads: local files and crash leftovers can change outside the process, so a cache or schema-only parser cannot safely replace validation. No new dependency or validator framework. |
| §5 −6: manual loop/hard-coded peers | REJECTED(operator approval/independent-peer boundary; runtime belongs to cc) | Executing peers inside sb or adding orchestration/configuration machinery increases scope and cannot replace owner approval or independent verification. Generated commands remain editable operator examples; existing explicit record/verify peer/model arguments preserve provenance. No automatic peer execution added. |
| §6 −8: no real peerhub contract test | FIXED | Added dev extra `peerhub`; existing CI installs `.[dev]`. New offline test runs exactly `peerhub ask --help`, parses supported flags, and checks every generated OCR/verification/summary command. Only local absence skips; CI absence fails. Help execution failure never skips. Dedicated subprocess guard permits help only, with network/DNS guard in its child. |
| §6 −4: repeat-approval DPI untested | REJECTED(OCR tests belong to cc) | Per-unit contract is explicit in DESIGN §5; cc must test mixed render DPI and explicit record mismatches. |
| §6 −3: mixed PDF selective OCR e2e missing | REJECTED(e2e tests belong to cc) | DESIGN §§9/12 and RUBRIC require the mixed-PDF installed-console flow on the integrated candidate. |
| §6 −3: unknown markup/mixed corpus e2e missing | REJECTED(e2e/wiki tests belong to cc) | cx adds real markup-to-ready ingest integration tests. cc owns the mixed-corpus wiki/installed-console e2e; DESIGN §9 records it. |
| §7 −10: CI pending/unmerged/untagged | REJECTED(release operator scope; user explicitly prohibited git) | No merge/tag/release or CI success is fabricated. RUBRIC leaves exact-candidate CI, live smoke and release actions pending. |
| §7 −5: stale release sheet | FIXED | RUBRIC targets v1.0.1, retains the original 25 requirement/invariant rows, and requires consistent exact-candidate evidence before scores become 100. |
| §7 −5: release gate lacks live peer smoke | FIXED | DESIGN §12 requires generated writable OCR and summary asks, independently verified OCR, accepted outputs, workspace/provenance/DPI checks and recorded live evidence. This is a gate contract change; the live operator run is still pending. |
| §7 −5: no release changelog | FIXED | Added root CHANGELOG.md with separate 1.0.0 and unreleased 1.0.1 entries; cc-owned behavior requires integration before release. |

## Test-first evidence

- Before implementation, real prose Markdown/HTML/HTM and empty markup failed with unknown instead of text-only; alias-validation
  rejection failed because the write succeeded. Reference/malformed media cases stayed conservative.
- Partial-decline ledger regression failed with `Disposition/unit mismatch`; after the one-condition fix it passes and still rejects
  changed preserved attempt bytes. The shared-validator refactor retains existing malformed-report and corrupt-ledger coverage.
- Focused run: 367 passed (`test_peerhub_contract.py`, `test_convert.py`, `test_ingest.py`, `test_ledger.py`); the later-added partial-decline
  regression also passed independently. Installed peerhub help lists `-p`, `-w`, `--stream`, `--writable`; both workflows pass the contract.
- Final required command `python -m pytest -q -p no:cacheprovider`: **597 passed, 4 skipped in 166.08s**, Windows/Python 3.15.2.
  Four existing installed-console e2e cases skipped because `sb` is absent locally; the real peerhub help test passed.
  No cc worktree integration, live peer execution, new CI result or release action is claimed.

## Integration notes

cc should preserve partial OCR statuses/attempts when declining; the cx ledger now accepts them only as ready/declined and continues
all integrity checks. No schema bump is needed. Source inspection adds triage scope `markup_source` with complete coverage and null page
counts; no media enumeration or OCR units are invented. Runtime wiki/tag/DPI/cleanup changes remain in cc's worktree. Keep the
independent audit unchanged as baseline evidence. No git commands were run.

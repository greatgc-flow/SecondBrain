# SecondBrain v1.0.1 candidate — independent audit (2026-11-09)

Auditor: independent (did not design, implement or review v1). Scope: branch `fix/peer-writable` (78a9b4a), BRIEF, DESIGN r9,
src/, tests/, USAGE, RUBRIC. Earlier peer scores were not reused. Local test run: see "Evidence" at the end.

| # | Dimension | Score |
|---|---|---|
| 1 | Goal fulfilment | 82 |
| 2 | Vertical closure | 85 |
| 3 | Horizontal consistency | 84 |
| 4 | MECE | 91 |
| 5 | Simplicity | 70 |
| 6 | Test adequacy | 82 |
| 7 | Release readiness | 75 |

## 1. Goal fulfilment (−18)
- −8 Every `.md/.html` file, including plain prose with no media, ends `unknown/awaiting-approval` (`media_not_inspected`) and needs a
  manual `sb ocr decline ID` per file (convert.py:232; DESIGN.md:120; EXPECTED.md:270 `llm/valid.md`). That breaks "no OCR needed" for the most common note format.
- −5 The owner asked for wiki "tags/links" (BRIEF.md:10). There are no tags and no cross-source links; the only link points to the original file (wiki.py:113-139).
- −5 Transcripts are rendered inside a `text` fence (wiki.py:125). Converted headings and tables never render as Markdown, so the wiki works as an archive rather than a wiki.
- Credit: the peerhub question is answered (operator workflow, not a dependency; DESIGN.md:186), OCR is selective per page/asset, and provenance is complete.

## 2. Vertical closure (−15)
- −5 The `--writable` fix is not reflected in the design: DESIGN §5 COMMANDS contract (DESIGN.md:194-197) still lacks it. RUBRIC scored 100 while this defect shipped.
- −5 The BRIEF "tags" requirement was dropped without a traceability row (DESIGN.md:359 B3 says "links" only).
- −5 DPI provenance: DESIGN.md:191 says the effective dpi is recorded per attempt. A second `approve --dpi 300` overwrites `dpi.txt`
  (ocr.py:148), and `record` then stamps 300 on units that were already rendered at 200 and are still unrecorded (ocr.py:168,192).

## 3. Horizontal consistency (−16)
- −4 RUBRIC.md:9 says 584 passed, but its table (RUBRIC.md:14-15) says 582.
- −4 RUBRIC.md:3,68,81-83 still describe the 1.0.0 promotion as pending. It was not updated for 1.0.1.
- −4 The DESIGN §2 layout (DESIGN.md:28-34) omits the `raws/<id>/stage.json` that is retained after commit (ledger.py:278; USAGE.md:62).
- −2 Alias append writes meta without `validate_meta` (ingest.py:95-96). Every other mutation validates first (ocr.py:57, llm.py:135).
- −2 `ocr verify` on a ready item deletes all of `work/<id>/`, including `llm/` (ocr.py:211). `status` treats that folder as legitimate scratch (cli.py:111).

## 4. MECE (−9)
- −6 `unknown` mixes two cases: "inspection incomplete" and "nothing to inspect" (plain Markdown) (DESIGN.md:122; convert.py:232).
- −3 The lifecycle has no abandon edge: once approved, an item can leave `ocr-in-progress` only when all units are verified, because decline accepts only `awaiting-approval` (ocr.py:156; DESIGN.md:144).
- Credit: the §3 first-match table is exhaustively tested over its domain (test_convert.py `test_at05_full_domain_is_mece`).

## 5. Simplicity, VerySimpleGuide (−30)
- −10 For a single-user local tool: a staging ledger, an 8-row recovery table and a per-artifact digest rule (ingest.py:69-149; DESIGN.md:155-176).
- −8 docs/renewal/ ships about 55 process files (reviews, votes, responses), and DESIGN is 382 dense lines.
- −6 A hand-written full-schema validator (ledger.py:256-330, 387 lines) re-runs on every read.
- −6 Each item needs a manual copy-paste loop (approve → peerhub → record → peerhub → verify) with hard-coded `cx`/`cc`/`*.effort` (ocr.py:108,116; llm.py:73).

## 6. Test adequacy (−18)
- −8 No contract test against the real peerhub CLI; only a regex on the generated string (test_ocr.py:148-151). The v1.0.0 write-ask defect passed all 584 tests and was caught only live.
- −4 Changing DPI between approvals is untested (test_ocr.py:400-415 reuses the same dpi), so the §2 gap above goes undetected.
- −3 The e2e tests cover only rasters (test_e2e.py:79). The owner's headline scenario (mixed PDF → selective page OCR → wiki) has no e2e test.
- −3 No e2e test takes an `unknown` Markdown note to ready, or checks a wiki built from a mixed corpus (test_e2e.py).

## 7. Release readiness (−25)
- −10 The v1.0.1 CI run (42544564284) was still in progress at audit time. The branch is not merged and not tagged.
- −5 The release sheet is stale for 1.0.1 (RUBRIC.md:3-9,68).
- −5 The release gate (DESIGN.md:379-381) has no live peer smoke step, which is how a functional defect passed with every row at 100.
- −5 Release notes amount to one README paragraph (README.md:35-37). There is no changelog for the Release.

## Evidence
Local `python -m pytest -q -p no:cacheprovider` (Windows, branch head): **580 passed, 4 skipped** in 166 s. The 4 skips are e2e cases in test_e2e.py that need the installed `sb` console script, which is absent locally. CI runs them.
I could not run `peerhub ask --help` here (the permission was denied), so the semantics of `--writable` (scope limited to `-w`?) are unverified.

## Round 2 (2026-11-09, branch `fix/indep-core` @ c7660cc)

Same auditor. Inputs: RESPONSE_independent_cx.md, RESPONSE_independent_cc.md, the diff 78a9b4a..c7660cc (src, tests, CI, docs), and
LIVE_SMOKE_v1.0.1.md. I checked the claims against the code. The local suite result (601 passed, 6 skipped) is the authors'; I did not rerun it.
PR #67 CI (run 42546888957) was still pending at re-audit and is not scored, per instructions.

| # | Dimension | R1 | R2 |
|---|---|---|---|
| 1 | Goal fulfilment | 82 | 98 |
| 2 | Vertical closure | 85 | 100 |
| 3 | Horizontal consistency | 84 | 95 |
| 4 | MECE | 91 | 98 |
| 5 | Simplicity | 70 | 97 |
| 6 | Test adequacy | 82 | 97 |
| 7 | Release readiness | 75 | 92 |

### Disposition of round-1 deductions
| R1 deduction | Verdict | Basis |
|---|---|---|
| 1 −8 plain markup unknown | FIXED | convert.py:46-58 `_inspect_markup`; e2e `test_e2e_markdown_note_goes_straight_to_ready`; live smoke note.md is ready |
| 1 −5 no tags/links | FIXED | wiki.py:56-63,166-178,191-193 tag pages, index section and back-links. Metadata-only tags fit the deterministic no-LLM tier (BRIEF.md:10) |
| 1 −5 fenced transcript | FIXED | wiki.py:47-53 `safe_markdown`. I tried scheme, entity, newline, `<…>` and reference-definition bypasses and none got through |
| 2 −5 `--writable` not in DESIGN | FIXED | DESIGN.md:194; `ocr.ask_line` ocr.py:62-64 |
| 2 −5 tags not traced | FIXED | DESIGN.md:250; RUBRIC B3 |
| 2 −5 DPI overwrite | FIXED | ocr.py:159-160,206 per-unit `dpi.json`; `test_second_approve_with_other_dpi_keeps_earlier_units_provenance` |
| 3 −4 / −4 RUBRIC counts and stale text | FIXED | One count; targets 1.0.1 (a new staleness is listed below) |
| 3 −4 stage.json missing from layout | FIXED | DESIGN.md:25; USAGE.md:62 |
| 3 −2 alias skips validation | FIXED | ingest.py:96 |
| 3 −2 verify-on-ready deletes llm/ | FIXED | ocr.py:219-229; test |
| 4 −6 unknown conflated | FIXED | DESIGN.md:93; convert.py:266-268 |
| 4 −3 no abandon edge | FIXED | ocr.py:167-175; ledger.py:212; DESIGN.md:131,206 |
| 5 −10 ledger/recovery/digests | REJECTED, acceptable | The recovery table is gone. The claim ledger and digests serve I1/I2/X1, which are owner invariants |
| 5 −8 process docs | FIXED | docs/renewal has 14 files; historical votes and reviews are deleted |
| 5 −6 validator | FIXED / REJECTED, acceptable | The duplicate convert validator was removed (`validate_triage` is shared). Re-validating on read is justified by external mutation |
| 5 −6 hard-coded peers and manual loop | FIXED (names) / REJECTED, acceptable (loop) | ocr.py:20-21 constants; the loop is the documented security boundary (sb never runs peers) |
| 6 −8 no peerhub contract | FIXED | tests/test_peerhub_contract.py runs the real `ask --help` under a guard and fails in CI if peerhub is absent |
| 6 −4 / −3 / −3 DPI and e2e gaps | FIXED | New DPI regression; mixed-PDF and Markdown e2e (console-only, run in CI) |
| 7 −10 CI/merge/tag | REJECTED, acceptable | CI is still running, and merge and tag are post-gate operator actions (DESIGN §12.4) |
| 7 −5 stale sheet | FIXED, but see the new gap below | |
| 7 −5 no live gate | FIXED | DESIGN.md:346-349. The smoke ran and LIVE_SMOKE_v1.0.1.md exists |
| 7 −5 no changelog | FIXED | CHANGELOG.md |

### Remaining deductions (each with its fix)
- **1 −2** wiki.py:52 also escapes `<` and `![` inside fenced code, indented code and code spans. CommonMark does not decode entities there, so
  converted code reads `a &lt; b` literally. Fix: skip the substitutions inside code spans and blocks, which are already inert.
- **3 −3** USAGE.md is stale against the code and DESIGN. The layout omits `wiki/tags/<tag>.md` (USAGE.md:68-70, :115). Decline is
  described as awaiting-only (USAGE.md:84,112,239-240), but ocr.py:168 also allows it from ocr-in-progress. USAGE.md:123-125 says
  verify-on-ready cleanup removes LLM scratch, which is now false (ocr.py:221). Fix: update those rows.
- **3 −2** RUBRIC.md:17,58,62 still say the live smoke is "pending", although DESIGN.md:349 requires the result to be recorded in RUBRIC.
  Fix: link LIVE_SMOKE_v1.0.1.md and record its date and versions there.
- **4 −2** convert.py:55 counts only `img|svg|object|iframe` as media. A note containing `<embed src=scan.pdf>`, `<video poster>`,
  `<picture><source srcset>` or `<input type=image>` becomes text-only/complete instead of unknown. Fix: add these tags,
  or treat any `src=`/`srcset=`/`poster=` attribute as uninspected media.
- **5 −3** Two deletion policies apply to the same folder. `_clean` (ocr.py:219-229) bypasses `safe_delete`: it has no reparse pre-scan
  and no read-only handling, which is the I8 invariant. Decline (ocr.py:174) uses `safe_delete`. Fix: give `safe_delete` a `keep=("llm",)`
  option and use it in both places.
- **6 −3** Nothing tests the two gaps above: no code-block fidelity case in test_wiki.py, and no `embed`/`video`/`srcset` negative case in test_ingest.py.
  Fix: add both regressions alongside the fixes.
- **7 −4** LIVE_SMOKE_v1.0.1.md:1-10 covers only the OCR half of DESIGN §12.3. It has no writable summary ask or `llm accept`, no candidate
  commit SHA, no sb/peerhub versions, and no observed per-unit DPI or provenance check. Fix: run the generated summary ask and accept it,
  then append SHA, versions, and the dpi/peer/model values from meta.json.
- **7 −2** pyproject.toml:18 declares `"peerhub"` unpinned, and CI resolves it from PyPI, while the Actions are SHA-pinned. If the owner's
  peerhub is not that PyPI distribution, CI either fails to install or runs a foreign package. Fix: pin an exact version or a VCS URL@sha.

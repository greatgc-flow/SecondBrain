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

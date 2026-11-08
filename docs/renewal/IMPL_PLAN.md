# SecondBrain v1 — Implementation plan r2 (TDD slices, 2026-11-09)

Governs implementation of `DESIGN.md` r8 (unanimously approved). Every slice: write the listed ATs red first, implement green, refactor,
then peer review of the diff. Nothing outside a slice's "files" may change in that slice. Exempt from that rule: `docs/renewal/RUBRIC.md`
(orchestrator-owned evidence file, updated after each slice review, never by implementers).

## Module layout (src/secondbrain/)

| Module | Owns | Must not import |
|---|---|---|
| `errors.py` | error/warning code enums (§8), `SbError(code, exit)` | anything |
| `fsutil.py` | root resolution, UTF-8/LF writers, `write_json_atomic`, deletion rule + reparse checks, path-length check, `esc()`, percent-encoding | ledger, commands |
| `ledger.py` | `stage.json`/`meta.json` schemas, validator (§2 table, artifact rule, orphan/corrupt), `activity()` | commands |
| `transcript.py` | `view(item)`, `source_digest`, `has_native_text`, `accepted_text_present` | commands |
| `convert.py` | allow-list, raster branch, MarkItDown wrapper (ledger-first), report runner + adapter, `classify()` table, unit enumeration | ingest, ocr |
| `ingest.py` | protocol (b)–(e), startup recovery table, duplicate/collision, `--retry` | ocr, wiki, llm |
| `ocr.py` | approve (render, COMMANDS.txt), decline, record, verify, finalize | wiki, llm |
| `wiki.py` | build into `wiki.tmp/`, swap, index + source pages, fences | ocr, llm, ingest |
| `llm.py` | prepare (prompt, nonce), accept (validate, revision) | ocr, wiki, ingest |
| `cli.py`, `__main__.py` | argparse, `--json` envelope, exit precedence, command-by-state matrix; `[project.scripts] sb = "secondbrain.cli:main"` | – |

Tests: `tests/conftest.py` (socket block, subprocess spy whose allow-list is `markitdown-gc`, the `sb` console script and `python -m
secondbrain` from slice 2 on (DESIGN §9), audio-extra check, `root` fixture derived from `tmp_path`, **fault hooks**:
`fault_after(step)` monkeypatching `os.replace` / `write_json_atomic` to raise once at a named step), `tests/helpers.py` (build synthetic
committed items/meta in any state), fixtures only under `tests/fixtures/{text,ocr,mixed,unknown,unsupported,characterize,failed,reports,
peer-output,llm}/` + `tests/fixtures/EXPECTED.md`, one `tests/test_<module>.py` per module holding that module's unit, AT and fault tests.
No shared fault-test file exists.

## Slices (strict order unless marked ∥; ∥ pairs touch disjoint files)

| # | Slice | Files | ATs | Depends on | Parallel |
|---|---|---|---|---|---|
| 0 | **Bootstrap / discard v0.1** (§12): delete `src/secondbrain/{backup,capture,lock,open_cmd,publish,receipt,restore,root,search,verify}.py`, v0.1 `cli.py` body, `tests/test_{acceptance_m1,backup_restore,capture,cli_smoke,find,open,verify}.py`, `docs/{design,decisions,USAGE}.md`, `scripts/verify.py`; rewrite `README.md`, `docs/README.md`; `pyproject.toml` (deps `markitdown-gc==0.3.5`, python `>=3.11,<3.16`, dev extras pytest, version `1.0.0.dev0`, `[project.scripts] sb`), `src/secondbrain/__init__.py` (`__version__ = "1.0.0.dev0"`), `.github/workflows/ci.yml` (run `python -m pytest --basetemp=.pytest-tmp` on pushes/PRs to `renew/**` and `main`; smoke job Linux 3.13; manual full matrix 3.11/3.13/3.15 x 2 OS), `.gitignore` (`work/`, `.pytest-tmp/`), `tests/test_bootstrap.py` (placeholder: import package, version string), `docs/renewal/RUBRIC.md` skeleton (one row per §11 id and invariant, all 0) | – (B2 review evidence) | – | – |
| 1 | **Characterization gate (1b)**: commit fixtures per §9 under `tests/fixtures/**`; run real `markitdown-gc` on each; write `EXPECTED.md` (conversion text, report JSON, observed class/state pair, `characterize/*` outcome); move misplaced fixtures. Completion = orchestrator + ag review APPROVE (no code) | `tests/fixtures/**` | feeds AT-05–AT-14 | 0 | – |
| 2 | **Foundation**: `errors.py`, `fsutil.py`, `ledger.py`, `transcript.py`, `conftest.py` (incl. fault hooks), `helpers.py` | `src/secondbrain/{errors,fsutil,ledger,transcript}.py`, `tests/{conftest,helpers}.py`, `tests/test_{fsutil,ledger,transcript}.py` | AT-07, AT-16 (validation part), AT-36 (deletion rule part), AT-37 (socket block) | 1 approved | – |
| 3 | **Classification adapter**: allow-list, raster branch, ledger-first wrapper, report adapter, `classify()` cross product, unit keys | `src/secondbrain/convert.py`, `tests/test_convert.py`, `tests/fixtures/reports/*` (synthetic) | AT-05, AT-06, AT-12 (ext part), AT-18 (key order) | 2 | – |
| 4 | **Ingest protocol** (PRs 4a protocol + recovery table; 4b duplicate/collision/retry/charset) | `src/secondbrain/ingest.py`, `tests/test_ingest.py` | AT-01–AT-04, AT-08–AT-14, AT-26, AT-35, AT-36 (inbox part) | 3 | ∥ 6, 7 |
| 5 | **OCR** (PRs 5a approve/render/COMMANDS.txt/record; 5b decline/verify/finalize/faults) | `src/secondbrain/ocr.py`, `tests/test_ocr.py`, `tests/fixtures/peer-output/*` | AT-17–AT-25, AT-27 (OCR part) | 3 | ∥ 6, 7 |
| 6 | **Wiki**: build/swap/recovery, index, source pages, projections, fences, `esc` use | `src/secondbrain/wiki.py`, `tests/test_wiki.py` | AT-30–AT-33 | 2 | ∥ 4, 5 |
| 7 | **LLM**: prepare prompt/nonce/contract, accept validation, revisions | `src/secondbrain/llm.py`, `tests/test_llm.py`, `tests/fixtures/llm/*` | AT-27 (accept part), AT-28, AT-29 | 6 (AT-27/28 render through `wiki.build`) | ∥ 4, 5 |
| 8 | **CLI envelope + end-to-end**: argparse, `--json` on parser errors, exit precedence, command-by-state matrix, `status` output; e2e tests through the installed `sb` console script (`subprocess` to `sb`, permitted by the slice-2 spy allow-list; converter call counts asserted from the child's `meta.json`/`stage.json` ledgers, not from the parent spy) | `src/secondbrain/{cli,__main__}.py`, `tests/test_cli.py`, `tests/test_e2e.py` | AT-15, AT-16, AT-34; e2e replays of AT-01/02/03 + AT-30 (text ingest, duplicate, wiki), AT-20/22 (raster approve/record/verify with `peer-output` fixtures), AT-29/28 (offline llm prepare/accept with staged outputs) | 4, 5, 6, 7 | – |
| 9 | **CI/release**: full six-job matrix green; offline clean-install job (fresh venv from local wheel cache, `sb --json status` on an empty root exits 0, `importlib.metadata.version("secondbrain") == secondbrain.__version__ == "1.0.0"`); `docs/USAGE.md` with the §6 operator prerequisite; version `1.0.0` in `pyproject.toml` and `__init__.py`; `RUBRIC.md` all 100 | `.github/workflows/ci.yml`, `docs/USAGE.md`, `pyproject.toml`, `src/secondbrain/__init__.py` | §12 gate 3 and release | 8 | – |

Merge order: 0 → 1 (approved) → 2 → 3 → {4 (4a, 4b), 5 (5a, 5b)} in `wt-core` ∥ {6 → 7} in `wt-wiki` → 8 → 9.
Final sequence after slice 9: all rubric rows 100 + unanimous implementation APPROVE → promote `renew/v1-zero-base` to `main` → run the full
matrix on that `main` commit → tag `v1.0.0` → GitHub Release with `RUBRIC.md` attached; no PyPI.

## Roles

- **cx.effort** implements slices 0–5 in worktree `wt-core`. All pytest runs use `pytest --basetemp=.pytest-tmp` inside the worktree (cx's
  sandbox cannot write to the system temp dir); `.pytest-tmp/` is gitignored in slice 0; conftest asserts no test touches
  `tempfile.gettempdir()`. Slice 1 is produced by cx (runs the real tool locally) and approved by orchestrator + ag before slice 2 starts.
- **cc.effort (Sonnet)** implements slices 6, 7 and 8 in worktree `wt-wiki`, starting once slice 2 is merged (needs `helpers.py`,
  `transcript.view`, fault hooks). Tests for 6/7 build items with `helpers.py` only and never call ingest/ocr code; slice 8 starts after 4–7 merge.
- **ag peers**: primary reviewer of every PR diff inline (< 30 KB; hence 4a/4b and 5a/5b).
- **Fable (F pool, argon)**: conformance reviewer per full slice (not per sub-PR): §11 rows touched, invariant tests present, no scope beyond
  the slice, fixture paths canonical.
- **Orchestrator**: runs the full suite on the other OS before each merge, merges in the order above, owns `RUBRIC.md`, performs the final sequence.
- Max two implementers at any time (cx.effort and cc.effort).

## Definition of done per slice

1. Slices 0–1: review-only completion (0: bootstrap suite = placeholder test green on CI smoke; 1: `EXPECTED.md` approved). Slices 2+: all
   listed ATs pass on the implementer's OS with `--basetemp`; no skipped tests without a `# DESIGN §x` reason.
2. From slice 8 on, `sb --json status` (installed console script) on an empty root exits 0; slice 9 additionally verifies installed metadata.
3. Diff reviewed by ag (inline) and Fable (conformance, per slice); orchestrator reruns the suite on the other OS; squash-merge to `renew/v1-zero-base`.
4. Orchestrator updates `RUBRIC.md` rows for the slice's requirements (0/50/100); release requires all rows at 100 (§12).

## Round-2 changes (plan votes: ag APPROVE, argon APPROVE with notes, cx REJECT)

- Strict order 0 → 1 (approved) → 2 → 3; the nominal 2 ∥ 3 is removed (cx-1, argon-2). In `wt-wiki`, 6 precedes 7 (argon-4).
- Shared `tests/test_faults.py` deleted; fault tests live in each owner's `test_<module>.py`; fault hooks frozen in slice-2 `conftest.py` (cx-2, argon-1).
- Canonical fixture paths `tests/fixtures/{reports,peer-output,llm}/`; slices 3/5/7 commit their synthetic fixtures there (cx-3, argon-3).
- `RUBRIC.md` skeleton created in slice 0; orchestrator-owned evidence file exempt from the file rule (cx-4).
- Slice 0 adds: CI workflow replacing `scripts/verify.py` with pytest `--basetemp`, triggers on `renew/**` and `main`, placeholder test, version
  `1.0.0.dev0` in `pyproject.toml` and `__init__.py`, `[project.scripts] sb`; slices 0/1 have review-only completion (cx-5, cx-6, argon-5).
- Slice 9 sets `1.0.0`, verifies installed metadata, and the final sequence (all-100 + unanimous APPROVE → main → validate → tag) is explicit (cx-6).
- Slice 8 adds end-to-end ATs through the installed `sb` console script (text ingest/duplicate/wiki, OCR record/verify, offline LLM) (cx-7).
- Rebalance: cc.effort takes 6, 7, 8; cx.effort takes 0–5; Fable (F pool) reviews conformance per full slice; ag stays primary diff reviewer (cx-8, argon-2).
- Re-vote cx-7: DESIGN §9 spy allow-list now includes the `sb` console script / `python -m secondbrain`; slice-2 conftest ships it from the start; slice 8 e2e asserts converter counts from the child's ledgers.

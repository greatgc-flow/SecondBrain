# SecondBrain v1.0.1 release rubric

Candidate closeout, 2026-11-09. The independent audit remains the baseline; this sheet records current evidence and release gates.
The owner target is 100 in every area. Scores are not promoted until the integrated candidate satisfies DESIGN §12.

## Evidence

- Local command: `python -m pytest -q -p no:cacheprovider`.
- Round 4 merged local count: to be set by the orchestrator after both implementations merge.
  cx's requested local verification is recorded in [the cx response](RESPONSE_independent_cx.md#round-4--cx-closeout);
  it is not substituted for a post-merge result or CI evidence.
- Verified CI workflow installation: `.github/workflows/ci.yml` full-matrix runs `python -m pip install --disable-pip-version-check -q -e ".[dev]"`;
  `pyproject.toml` pins `peerhub==0.24.1` and `markdown-it-py==4.2.0` in dev. `test_peerhub_contract.py` checks local help offline, never starts a peer, and fails if peerhub
  is missing in CI (only local absence skips). Both responses withdraw the prior offline-breaking objection.
- CI: the integrated v1.0.1 candidate must pass all eight jobs (six full suites and two offline clean installs).
  Record one consistent passed/skipped count per suite from that run; prior-revision counts are not release evidence.
- Latest recorded live smoke: **2026-11-09T02:12Z**, code commit **`22e3e85d3efd44c07d7c52a100e7d14c4e481112`**,
  in [LIVE_SMOKE_v1.0.1.md](LIVE_SMOKE_v1.0.1.md). It covers OCR, CLI-attributed summary acceptance and verify-on-ready
  preserving prepared LLM scratch. Observed versions: Python **3.15.2**, peerhub **0.24.0**, markitdown-gc **0.3.5**.
  Round 4 changes wiki rendering, so the orchestrator will rerun the exact-candidate smoke after merge and set its new SHA/evidence.
  The recorded prior smoke is not claimed to exercise Round 4 code or the newer dev pin.
- Merge, main CI, tag `v1.0.1` and GitHub Release: release-operator actions, not established by local tests.

## Requirement evidence

The original **25 rows** are retained: 10 brief requirements, 4 guide requirements, 3 cross-cutting requirements and 8 invariants.
0 = implementation absent/failing; 50 = required evidence missing/skipped; 100 = all relevant local/CI tests and review complete.
All release scores remain **pending the integrated gate**; a previous all-100 sheet does not override the independent findings.

| Id | Requirement / invariant | Test evidence |
|---|---|---|
| B1 | inbox → raws → wiki | `test_ingest.py`, `test_wiki.py`, `test_e2e.py` |
| B2 | v0.1 discarded; history only | `test_bootstrap.py::test_v1_discard_boundary` |
| B3 | Deterministic source pages, index, tag pages and related-source links | `test_wiki.py::test_tags_pages_index_links_and_back_links` |
| B4 | Explicit LLM workflow and accepted provenance | `test_llm.py`, `test_peerhub_contract.py` |
| B5 | Classification/counts before selective approved OCR | `test_ingest.py`, `test_cli.py`, `test_ocr.py`, `test_e2e.py` |
| B6 | Sensitive/large input approval | `test_ocr.py`, `test_cli.py`; operator permission review |
| B7 | markitdown-gc 0.3.5 conversion and triage | `test_convert.py`, `test_ingest.py` |
| B8 | MECE; media-free markup ready; unknown means incomplete inspection | `test_convert.py::test_at05_full_domain_is_mece`, `test_ingest.py::test_markup_without_media_is_ready_but_uninspected_media_stays_unknown` |
| B9 | No retranscription; complete per-unit provenance | `test_ingest.py`, `test_ocr.py::test_second_approve_with_other_dpi_keeps_earlier_units_provenance` |
| B10 | VerySimpleGuide, Windows, English | `test_fsutil.py`, `test_ingest.py`; minimality and English review |
| G1 | Prompt, batching, pilot, concurrency and approval cap | `test_ocr.py`; operator live smoke |
| G2 | Independent verification of every accepted unit | `test_ocr.py`; operator fidelity review |
| G3 | Attempt history, no image cache, cleanup preserving LLM scratch | `test_ocr.py::test_verify_on_ready_item_keeps_llm_scratch`, `test_ledger.py::test_decline_after_partial_ocr_preserves_attempts_and_verification_rules` |
| G4 | Offline operation; peerhub is an operator workflow | `test_fsutil.py`, `test_peerhub_contract.py` |
| X1 | Crash safety and corruption handling | `test_ingest.py`, `test_ledger.py`, `test_ocr.py`, `test_wiki.py`, `test_llm.py` fault tests |
| X2 | Untrusted text, safe Markdown and summary rendering | `test_ocr.py`, `test_wiki.py::test_at32_transcript_is_markdown_but_inert`, `test_llm.py` |
| X3 | CLI, JSON and exit contract | `test_cli.py` |
| I1 | Source unchanged after claim | `test_ingest.py::test_at26_all_durable_boundaries_recover_once` |
| I2 | Completed conversion at most once | `test_convert.py::test_completed_output_reconciled_after_crash`, `test_ingest.py` retry fault tests |
| I3 | Pure transcript projection | `test_transcript.py` |
| I4 | Approved keys and new attempt digests only | `test_ocr.py` |
| I5 | Different recording/verifying peers | `test_ocr.py::test_at22_verify_request_validation` |
| I6 | Unverified OCR excluded from transcript/wiki, including partial decline | `test_transcript.py`, `test_wiki.py`, `test_ledger.py` |
| I7 | Wiki derived only from raws | `test_wiki.py::test_at30_build_twice_identical_and_only_expected_files` |
| I8 | Restricted deletion, preserved direct children and reparse guards | `test_fsutil.py` keep/read-only/interruption regressions, `test_ingest.py`, `test_wiki.py` |

## Closeout

[Independent audit](AUDIT_independent.md) deductions are answered in [cx response](RESPONSE_independent_cx.md) and [cc response](RESPONSE_independent_cc.md).
Retain the independent scores until the integrated candidate is reviewed. Required checks are the complete matrix with no skips,
both offline clean installs and exact-candidate evidence review against the recorded live smoke, then release actions in DESIGN §12.

Reconciled DESIGN now includes the exact tag layout/rule, partial-decline lifecycle, `dpi.json` and shared `ocr.ask_line()` contract,
safe Markdown pass and authoritative JSON provenance. The manual operator loop remains intentional: sb never runs peers.
The recorded live writable/read-only OCR and summary smoke is linked above; offline help does not replace its observed evidence.

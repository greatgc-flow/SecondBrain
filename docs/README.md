# Documentation map

| Document | Purpose |
| --- | --- |
| [Usage](USAGE.md) | Installation, commands, operator prerequisites, OCR/LLM steps, recovery; for people and AI agents. |
| [Design r9](renewal/DESIGN.md) | Approved data contract, security boundary, invariants, and acceptance tests. |
| [Implementation plan](renewal/IMPL_PLAN.md) | Slice ownership and release gates. |
| [Brief](renewal/BRIEF.md) | Owner requirements. |
| [Rubric](renewal/RUBRIC.md) | Test evidence, local results, scores, and remaining release gates. |
| [Characterization](../tests/fixtures/EXPECTED.md) | Real markitdown-gc 0.3.5 observations and design resolutions. |
| [Converter guide](renewal/_mdgc_guide.txt) | Tool contract retained as a design input; SecondBrain's approved rules take precedence. |

The remaining [renewal records](renewal/) preserve design votes, reviews, and
responses. They are historical evidence; current instructions are in USAGE and
DESIGN. The v0.1 status page was removed; history tags are listed in the
[repository README](../README.md).

CI runs Ubuntu/Windows × Python 3.11/3.13/3.15 tests, plus an offline clean-install
job on both OSes with Python 3.13. Jobs run on pushes to `main` and `renew/**`,
pull requests, and manual dispatch. Clean-install jobs build/download wheels
online, then install with `--no-index` in a fresh venv and exercise the installed
`sb` from an empty data directory. No peer or model is invoked by CI.

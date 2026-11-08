# SecondBrain v1

A local workflow: `inbox/` -> `raws/` (originals, conversion, verified OCR,
and provenance) -> `wiki/` (derived pages). OCR requires explicit approval;
LLM summaries are optional and explicit.

This is the Slice 0 bootstrap. The `sb` entry point is reserved; v1 commands
are not implemented yet. The approved [design](docs/renewal/DESIGN.md) and
[implementation plan](docs/renewal/IMPL_PLAN.md) define the work ahead.
See the [documentation map](docs/README.md).

Development requires Python >=3.11,<3.16:

```sh
python -m pip install -e ".[dev]"
python -m pytest --basetemp=.pytest-tmp -q
```

Runtime dependency: `markitdown-gc==0.3.5`, without optional extras.

## History

v0.1 is discarded; its history remains at tag `v0.1.1`. The `legacy/` tree
was deleted and remains reachable at tag `legacy-r13-final`.
`CONTRIBUTING.md` was deleted because it described the v0.1 workflow.

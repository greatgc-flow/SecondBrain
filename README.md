# SecondBrain

A local knowledge pipeline: `inbox/` -> `raws/` (originals, conversion, verified
OCR, provenance) -> `wiki/` (generated Markdown). OCR needs explicit approval;
LLM summaries run only when requested through the operator's peers.

Requires Python >=3.11,<3.16. Install from a repository checkout:

```sh
python -m pip install .
sb --help
```

Create a separate data directory with an `inbox/`, put files there, then run
`sb ingest`, `sb status`, and `sb wiki build` from that directory. Read the
[usage guide](docs/USAGE.md) before approving OCR or invoking peers; it includes
the required access restrictions, every command, and recovery steps.

Runtime dependency: `markitdown-gc==0.3.5`, without optional extras.
[Documentation map](docs/README.md) · [Release evidence](docs/renewal/RUBRIC.md).

For development:

```sh
python -m pip install -e ".[dev]"
python -m pytest -q -p no:cacheprovider
```

## History

v0.1 is discarded; its history remains at tag `v0.1.1`. The deleted `legacy/`
tree remains at tag `legacy-r13-final`. `CONTRIBUTING.md` and `docs/STATUS.md`
were removed because they described the v0.1 workflow.

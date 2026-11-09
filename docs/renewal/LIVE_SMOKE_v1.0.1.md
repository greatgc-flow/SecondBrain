# Live peer smoke (v1.0.1, 2026-11-09T02:12Z)

Code: commit `22e3e85d3efd44c07d7c52a100e7d14c4e481112` run from source; Python 3.15.2; peerhub 0.24.0; markitdown-gc 0.3.5.
Inputs (synthetic fixtures): two-pages.pdf (mixed), plain.txt (text), note.md (plain Markdown with an inline code span `<b>`).

Steps (every peer line copied verbatim from the generated COMMANDS.txt):
1. `sb ingest` -> note.md and plain.txt `ready/text-only`; two-pages.pdf `awaiting-approval/mixed` (1 unit).
2. `sb ocr approve` (only the mixed PDF) -> transcription ask (`--writable`) by cx -> `sb ocr record --peer cx`.
3. Verification ask (read-only) by cc answered `u0001: ok` -> `sb ocr verify --ok u0001` -> finalized.
4. `sb llm prepare` -> summary ask (`--writable`) by cx -> `sb ocr verify` on the READY item returned `cleaned` and kept `work/<id>/llm/` intact -> `sb llm accept --peer cx --model gpt-6.1-sol`.
5. `sb wiki build` -> source pages, tag pages, back-links; the note's inline code span `<b>` is preserved verbatim, no raw HTML elsewhere.

Final status:
```text
05dbc4527cb6fb44 ready text-only -/0 0/0/0/0 complete note.md
4283c5580032cf5a ready mixed 2/1 1/1/1/1 complete two-pages.pdf
59c7bcbced49378e ready text-only -/0 0/0/0/0 - plain.txt

counts: ready=3, awaiting-approval=0, ocr-in-progress=0, unsupported=0, failed=0
```

Provenance: OCR u0001 (source p2) recorded cx/gpt-6.1-sol dpi=200 ocr-v1; verified cc/claude-sonnet-5-5 verify-v1; status=verified. Summary accepted with CLI provenance cx/gpt-6.1-sol (llm-v1).
Result: both halves of the DESIGN §12 live-peer gate passed on this commit.

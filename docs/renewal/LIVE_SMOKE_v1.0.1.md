# Live peer smoke (v1.0.1, 2026-11-09T02:55Z)

Code: commit d7e4ae0 (d7e4ae0bcd93d68fae7b020c05620e7e2eca83ca) run from source; Python 3.15.2; peerhub 0.24.0; markitdown-gc 0.3.6.
Inputs (synthetic): two-pages.pdf (mixed), plain.txt (text), note.md (Markdown with inline code `<b>` and a raw `<img onerror>` tag).

Steps (peer lines copied verbatim from generated COMMANDS.txt):
1. `sb ingest`: plain.txt `ready/text-only`; two-pages.pdf `awaiting-approval/mixed`; note.md `awaiting-approval` (its `<img>` is a media reference, so OCR is offered, not skipped).
2. Approve only the mixed PDF -> cx transcription ask (`--writable`) -> `sb ocr record --peer cx`.
3. cc verification ask (read-only): `u0001: ok` -> `sb ocr verify --ok u0001` -> finalized.
4. `sb llm prepare` -> cx summary ask (`--writable`) -> `sb ocr verify` on the READY item returned `cleaned` and kept `work/<id>/llm/` -> `sb llm accept --peer cx --model gpt-6.1-sol`.
5. `sb wiki build`: no raw `<img`/`<script>` in any source page; the note renders `&lt;b&gt;` and `&lt;img ... onerror ...&gt;` as text (escape-all rule).

Final status:
```text
4283c5580032cf5a ready mixed 2/1 1/1/1/1 complete two-pages.pdf
59c7bcbced49378e ready text-only -/0 0/0/0/0 - plain.txt
b64ac6f323165004 awaiting-approval unknown -/0 0/0/0/0 none note.md

OCR approval needed:
  b64ac6f323165004 note.md units=0

counts: ready=2, awaiting-approval=1, ocr-in-progress=0, unsupported=0, failed=0
```

Provenance: OCR u0001 (source p2) recorded cx/gpt-6.1-sol dpi=200 ocr-v1; verified cc/claude-sonnet-5-5 verify-v1; status=verified. Summary accepted with CLI provenance cx/gpt-6.1-sol (llm-v1).
Result: both halves of the DESIGN §12 live-peer gate passed on this commit.

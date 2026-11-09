# Live peer smoke (v1.0.1 candidate, 2026-11-09T01:41:05Z)

Synthetic fixtures: two-pages.pdf (mixed), plain.txt, note.md. Commands from COMMANDS.txt run verbatim via peerhub.
4283c5580032cf5a ready mixed 2/1 1/1/1/1 complete two-pages.pdf
59c7bcbced49378e ready text-only -/0 0/0/0/0 - plain.txt
781fe4c71c03dea2 ready text-only -/0 0/0/0/0 complete note.md

counts: ready=3, awaiting-approval=0, ocr-in-progress=0, unsupported=0, failed=0

Transcriber: cx/gpt-6.1-sol (--writable); verifier: cc/claude-sonnet-5-5 (read-only): ok.

## Evidence details (appended by orchestrator)

- Code: commit `e96ec022242e3d4fcde72636905935af89f633c2` (branch fix/indep-core) run from source; Python 3.15.2; peerhub 0.24.0; markitdown-gc 0.3.5.
- OCR u0001 (source p2): recorded peer=cx model=gpt-6.1-sol dpi=200 prompt=ocr-v1; verified peer=cc model=claude-sonnet-5-5 prompt=verify-v1; result=ok; status=verified.
- LLM tier: `sb llm prepare` -> generated summary ask run verbatim (--writable) -> `sb llm accept` -> wiki source page shows the Summary section; summary.a1 activity peer=codex model=gpt-6 (self-reported by the peer, recorded as untrusted metadata) prompt=llm-v1.
- Both halves of the DESIGN §12 live-peer step (OCR transcribe/verify, LLM summary/accept) passed.

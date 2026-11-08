# SecondBrain v1 zero-base renewal — brief (owner-approved inputs, 2026-11-09)

## Goal
Rebuild SecondBrain from zero as a personal knowledge pipeline: `inbox/` -> `raws/` (original + transcript) -> `wiki/` (auto-generated).
Analysis/design must reach TDD-ready detail and unanimous peer approval BEFORE any implementation.
Then TDD, recursive MECE + vertical/horizontal closure cross-check, score every item, iterate until all 100, release.

## Owner decisions (binding)
1. v0.1 core (content-addressed objects, receipts, verify, backup/restore) is DISCARDED entirely (concept and code). v0.1.1 stays only as git tag history.
2. Wiki = two tiers: deterministic generation by default (no LLM: per-source pages, indexes, tags/links); optional LLM tier (summaries/concept pages) only on explicit user command, executed through peerhub peers.
3. OCR policy: classify first, show the list (ocr-needed / no-ocr / mixed, page counts), run OCR only on files the user approves. Sensitive or >20 pages/images always need explicit approval.
4. Release: same repo greatgc-flow/SecondBrain, main, GitHub Release v1.0.0; no PyPI.

## Fixed inputs
- Conversion: markitdown-gc 0.3.5 (pip; CLI `markitdown-gc`; Python import name `markitdown`). Run `markitdown-gc --guide all`.
  It never OCRs; `--ocr-report` triage gives decision ocr_recommended | review | no_candidates | unknown and coverage. OCR is done by peers via peerhub (see `--guide ocr` recipe S0-S4).
- Classification classes must be MECE: e.g. text-only (no OCR), ocr-required (scanned/image), mixed (text + image regions), unsupported/unknown.
- Never retranscribe already transcribed content; keep transcript provenance (tool, version, method, peer/model, date).
- Owner rules: VerySimpleGuide (github.com/greatgc-flow/VerySimpleGuide) — minimal, no over-engineering; Windows primary; English code/docs.

## Open design questions for peers (decide by unanimous deliberation)
- Is peerhub a runtime dependency, an optional adapter, or only an operator workflow? Same for any DB/index.
- Folder/data model for inbox/raws/wiki; idempotency key; state ledger; what is source of truth vs derived.
- CLI surface (smallest set of commands), exit codes, JSON output.
- Wiki format (plain Markdown, Obsidian-compatible links?), regeneration rules, LLM-tier boundary.
- Test strategy (fixtures for each class, no network in CI), CI matrix, release checklist.

## Owner addendum (2026-11-09)
The inbox/raws/wiki layout and all user scenarios are suggestions, not constraints: peers may change the folder structure and scenarios if a better design results (justify it).

# Changelog

## 1.0.1 — Unreleased

- Generated OCR transcription and LLM summary peerhub asks include `--writable`; verification asks remain read-only.
- Media-free Markdown/HTML becomes text-only and ready; unknown is reserved for incomplete inspection.
- Alias updates validate metadata before commit. Conversion and ledger reads share triage validation.
- OCR can be declined after partial work while preserving attempts and verified text. Render DPI belongs to each unit;
  later approvals cannot relabel earlier renders. Ready-item cleanup preserves prepared LLM summaries.
- Wiki transcripts render safe Markdown with deterministic tags and related-source navigation.
- Development installs include peerhub; offline tests check generated flags against the real CLI help.
- Remove historical review/vote/response documents; refresh design, release evidence and the live peer smoke gate.

## 1.0.0

- Rebuilt the local pipeline from inbox to immutable originals, conversion/verified OCR and a generated wiki.
- Added selective OCR approval, capped batches, independent verification and append-only provenance.
- Added explicit LLM summary preparation/acceptance, content digests and revision history.
- Added crash recovery, strict ledger/artifact validation, JSON CLI output and offline cross-platform tests.
- Removed the v0.1 core; its history remains in repository tags.

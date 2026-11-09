# Changelog

## 1.0.1 — Unreleased

- OCR and LLM workflows share `ocr.ask_line()` and centralized peer defaults; transcription/summary asks include `--writable`,
  verification asks remain read-only. The operator runs peers; sb prepares commands and validates outputs.
- Media-free Markdown/HTML becomes text-only and ready; unknown is reserved for incomplete inspection.
- Alias updates validate metadata before commit. Conversion and ledger reads share triage validation.
- OCR can be declined after partial work while preserving attempts and verified text. Render DPI belongs to each unit;
  `work/<id>/dpi.json` preserves each render across approvals. Generated record commands omit `--dpi`; explicit record DPI stays
  an operator override. Ready-item cleanup preserves prepared LLM summaries.
- Wiki transcripts render safe Markdown after HTML/image/unsafe-link neutralization; nothing is fetched. Summary/metadata stay
  fenced and JSON records authoritative provenance. Class/extension/collected-month tags link source pages through `wiki/tags/<tag>.md`.
- Keep the real local `peerhub ask --help` contract test: it runs offline and starts no peer. Development installs and CI include
  peerhub; missing CLI fails in CI and only local absence skips. Live write/read-only peer smoke remains a separate release gate.
- Remove historical review/vote/response documents; refresh design, release evidence and the live peer smoke gate.

## 1.0.0

- Rebuilt the local pipeline from inbox to immutable originals, conversion/verified OCR and a generated wiki.
- Added selective OCR approval, capped batches, independent verification and append-only provenance.
- Added explicit LLM summary preparation/acceptance, content digests and revision history.
- Added crash recovery, strict ledger/artifact validation, JSON CLI output and offline cross-platform tests.
- Removed the v0.1 core; its history remains in repository tags.

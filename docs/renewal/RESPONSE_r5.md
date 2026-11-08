# Response to round-5 review (DESIGN.md r6, 2026-11-09)

Legend: ACCEPT (change, r6 section) | ACK (marked resolved; no change). r6 length = r5 (346 lines). argon and ag approved r5; this round
answers cx only.

- cx-1–cx-33, N1–N12, E1, E2, E4, E5, F1 ACK.
- **G1 (blocker) ACCEPT.** The source is never placed beside ledger files: handoff is `os.replace(inbox file -> .staging/tmp-<n>/src/<filename
  unchanged>)`, a dedicated subdirectory that no inbox name can collide with; `stage.json`, `converted.md`, `media/`, `meta.json` live at the
  directory root. After hashing the file moves to `original<ext>` at the root (`ext` from `stage.json.filename`), and `src/` is removed; an
  empty `src/` on restart is simply removed. Adversarial test: inbox files literally named `stage.json`, `meta.json`, `converted.md`,
  `original.pdf`, with byte/hash preservation and an immediate post-handoff restart. §4, AT-26.
- **E3 ACCEPT (cx option 1; no automatic reconversion).** The conversion step is ledger-first: `stage.json` records the pending activity
  (`conversion: {activity, sha256: null}`) before the converter runs; `converted.md` is written tmp+replace; then the digest is recorded. On
  restart a pending entry with a complete `converted.md` is **reconciled** (digest computed and recorded), never regenerated; a pending
  entry without output runs the converter for the first time. I2 is therefore strict again: conversion is invoked at most once per item.
  Argument we accept and state in §4: the brief's never-retranscribe rule primarily protects peer OCR (quota, pages leaving the machine,
  non-determinism), which is why OCR units are never re-requested once recorded (I4); local deterministic conversion is nevertheless held to
  the same once-only standard because the ledger-first protocol makes it free. §3 step 2, §4, AT-26.
- **F2 ACCEPT (by deletion).** The non-existent detected-format accessor is removed. Extension handling becomes an allow-list: only
  `.pdf .docx .pptx .xlsx .hwp .hwpx` (triage-supported), the plain-text set `.txt .md .csv .log .html .htm .json .xml`, and rasters proceed;
  every other extension is `unsupported` (`extension_not_allowed`) before any conversion, so audio/video cannot reach the converter by
  construction. Renamed media behind an allowed extension is documented as "actual outcome recorded at the characterization gate: failed or
  unknown, never transcribed (extra absent), never `unsupported` by guarantee"; `renamed-audio.pdf` becomes a characterization fixture whose
  assertions are only "no network, conversion spy <= 1, state in {failed, unknown}". §3, §6, §9, AT-12.
- **G2 ACCEPT.** AT-08 and AT-26 assert `conversion.activity.params.charset`; staging-to-meta transfer copies the `conversion` object
  unchanged. §9.

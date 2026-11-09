# Response to round-3 reviews (DESIGN.md r4, 2026-11-09)

Legend: ACCEPT (change, r4 section) | REJECT (reason) | ACK (marked resolved; no change). Orchestrator evidence adopted: on 0.3.5
`convert("a.png")` returns empty text without exception and `--ocr-report` gives `ocr_recommended`/`complete`/1 candidate; r4 still
makes rasters one explicit early branch. r4 length = r3 (346 lines).

## cx (prior ids)
- cx-1, cx-2, cx-3, cx-4, cx-5, cx-7, cx-9, cx-10, cx-11, cx-12, cx-13, cx-14, cx-15, cx-17, cx-18, cx-20–cx-27, cx-29–cx-33 ACK.
- cx-6 ACCEPT. Retry resumes from the first missing durable step: conversion runs iff `converted.md` is absent; I2 reworded to "never invoked while `converted.md` exists". §4, AT-13/AT-14. (= ag-M)
- cx-8 / cx-16 / cx-28 ACCEPT. All re-publication is append-only with versioned files referenced by meta: LLM summaries `llm/summary.aN.md` (identical content = no-op; different = new revision); no referenced file is ever overwritten. Fault test for replacement interruption added. §2, §6, AT-27/AT-28.
- cx-19 ACCEPT. Duplicate handling = alias append (if new name) + deletion of the staged copy; the inbox move happens before identity is known and is the only inbox mutation. Matrix cell `A` redefined; AT-03/AT-15 test both duplicate and alias cases. §4.
- N1, N2, N5–N12 ACK (N2: §10 Q2 closed as asset-level provenance; N11: §10 Q1 closed, pure view confirmed by cx and ag).
- N3 ACCEPT. Step 1 of ingest is `os.replace` of the inbox file into staging (same volume, root-contained inbox); `sb` owns the bytes before hashing; no stat-then-unlink, no size+mtime heuristics; cross-volume/OSError leaves the file and records `io_error`. §4, AT-26.
- N4 ACCEPT. `--ok` and `--mismatch` both optional, union non-empty, disjoint, every key `recorded`, validated before any write. §5, §8, AT-22/AT-23.
- E1 ACCEPT. Rasters are one explicit early branch after pre-checks: no conversion, no triage, class ocr-required, one unit `self`, `has_native_text` null; the schema wording follows. Raster cross-product in AT-05/AT-09. §3. (= ag-B, ag-m)
- E2 ACCEPT (simplest form). Extracted media is always kept for container sources (`raws/<id>/media/`), regardless of class or failure; disk cost stated (original image bytes, deduplicated by the tool). Container report-failure/retry test asserts one conversion and intact units. §2, §3, AT-14.
- E3 ACCEPT. Staging writes the same `meta.json` incrementally: identity after the move, `conversion` activity (effective charset, extraction flag) immediately after conversion, the rest at classification; resume reads that meta and never reconstructs the activity from new flags. No side file. §4.
- E4 ACCEPT. One escaping rule `esc()` for the only untrusted scalars rendered as Markdown (title and index label); all other metadata (aliases, provenance, peer/model strings) is rendered as a fenced `json` block. Hostile filename/alias/model tests. §7, AT-31/AT-32.
- E5 ACCEPT. AT-17 records before verifying; AT-22 uses fresh recorded state for the invalid-request case; AT-33 asserts exclusion of unverified attempts, not of all OCR text. §9.

## ag
- Open question 1 ACK. Pure view confirmed; §10 Q1 closed.
- ag-B1, ag-B2, ag-M1, ag-m1, ag-m2, ag-m3 ACK.
- ag-B (raster starvation) ACCEPT in effect, premise corrected. Measured 0.3.5 behaviour: `convert()` on a raster returns empty text, no exception, so row 4 was reachable; r4 nevertheless adopts the proposed fix (rasters branch before conversion/triage with one `self` unit) because it is simpler and independent of converter behaviour. §3. (= E1)
- ag-M (retry skips conversion when `converted.md` absent) ACCEPT. §4 lifecycle row now "resume from the first missing durable step; conversion iff `converted.md` absent". (= cx-6)
- ag-m (`converted.md` wording) ACCEPT. §2: "absent for rasters, conversion failure, or unsupported".

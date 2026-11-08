### Open Question 1: Transcript Materialization vs Pure View
Pure view satisfies the requirement. `raws/<id>/` durably holds all transcript content via `converted.md` and immutable `ocr/uNNNN.aN.md` files. Materializing a redundant `raws/<id>/transcript.md` violates SSOT, reintroduces a crash/sync window across mutations, and duplicates the derived text already materialized in `wiki/sources/<id>.md`.

### (1) Round-2 Findings Status
- **ag-B1**: RESOLVED. Staged execution short-circuits before evaluating native text; missing artifacts are not evaluated.
- **ag-B2**: RESOLVED. Verification treadmill removed by deleting sampling and requiring all units to be verified.
- **ag-M1**: RESOLVED. Media extraction moved into the single ingest conversion call (Step 2); I2 holds strictly.
- **ag-m1**: RESOLVED. `COMMANDS.txt` uses actual unit paths `uNNNN<ext>` instead of hardcoded PNG paths.
- **ag-m2**: RESOLVED. Sampled-out units eliminated by deletion.
- **ag-m3**: RESOLVED. Atomic all-or-nothing validation exits 2 before writing on any invalid unit output.

### (2) New Defects
- [SEV blocker] §3 — Unconditional conversion and table precedence starves raster ingestion — In Step 2, `MarkItDown(enable_plugins=False).convert` raises `UnsupportedFormatException` on raster files (`.png`, `.jpg`, etc.). Because Row 2 (`UnsupportedFormatException` -> `unsupported`) precedes Row 4 (`ext in raster set`), every raster is classified as `unsupported`, making Row 4 dead code. — Fix: Evaluate Row 4 before Step 2; rasters skip Step 2 conversion and Step 3 triage, setting class `ocr-required`, state `awaiting-approval`, and unit `self`.
- [SEV major] §4 — `ingest --retry` skips conversion even when `converted.md` is absent — §4 lifecycle table states `ingest --retry` "reruns steps 3–5 only; conversion reused". If an item previously failed at Step 1 or Step 2, `converted.md` does not exist, causing Steps 3–5 to fail or crash. This contradicts protocol (d) ("skipping conversion when converted.md exists"). — Fix: In §4 lifecycle table, change to "reruns §3, skipping conversion only if converted.md exists (per protocol d)".
- [SEV minor] §2 — Data contract description of `converted.md` ignores rasters — §2 defines `converted.md` as "absent iff conversion failed/unsupported". For rasters, conversion is skipped, yet the item is `ocr-required`. — Fix: Amend description to "absent for rasters or iff conversion failed/unsupported".

VOTE: REJECT (1 blocker)

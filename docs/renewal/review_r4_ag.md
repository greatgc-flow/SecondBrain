### Round-3 Findings Resolution

- **[SEV blocker] §3 (Raster starvation)**: RESOLVED. §3 Step 1 explicitly branches raster extensions directly to Row 2 prior to conversion and triage, assigning class `ocr-required`, state `awaiting-approval`, and one unit.
- **[SEV major] §4 (`ingest --retry` skips conversion)**: RESOLVED. §4 lifecycle table and protocol now resume at the first missing durable step, explicitly executing conversion iff `converted.md` is absent.
- **[SEV minor] §2 (`converted.md` description ignores rasters)**: RESOLVED. §2 data contract description now explicitly states `converted.md` is "absent for rasters, conversion failure, unsupported".

### New Findings (Sections 1–5)

- [SEV minor] §3 — Raster unit definition conflates unit key with source — §3 Step 5 parenthetical notes "(Rasters: one unit `self`, kind `raster`, row 2.)", whereas §2 schema defines unit map keys as `uNNNN` (`units: {uNNNN: unit}`) and §5 references unit artifacts as `uNNNN<ext>` and `ocr/uNNNN.a<n>.md`. `self` is the unit `source` value, while the ledger key is `u0001`. — Fix: In §3 Step 5, clarify: "(Rasters: key `u0001`, source `self`, kind `raster`, row 2.)".

VOTE: APPROVE

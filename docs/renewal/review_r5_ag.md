### 1. Status of Round-4 Findings

- **[SEV blocker] §3 (Raster starvation)**: RESOLVED. §3 Step 1 and Table Row 3 route raster extensions directly to `ocr-required` / `awaiting-approval` with one unit (`u0001`), bypassing conversion and triage.
- **[SEV major] §4 (`ingest --retry` skips conversion)**: RESOLVED. §4 lifecycle table and protocol resume at the first unreferenced durable step; conversion runs iff `converted.md` is absent/unreferenced.
- **[SEV minor] §2 (`converted.md` description ignores rasters)**: RESOLVED. §2 data contract explicitly defines `converted.md` as "absent for rasters, conversion failure, unsupported".
- **[SEV minor] §3 (Raster unit definition conflates unit key with source)**: RESOLVED. §3 Step 5 explicitly assigns key `u0001`, `source: self`, `kind: raster`, conforming to the §2 `units: {uNNNN: unit}` schema and §5 asset copying.

### 2. New Defects (Sections 1–5)

None.

VOTE: APPROVE

### Round-5 Findings Status (Sections 1–5)
- **[SEV blocker] §3 (Raster starvation)**: RESOLVED. §3 Step 1 and Table Row 3 route raster extensions directly to `ocr-required` / `awaiting-approval` with one unit (`u0001`), bypassing conversion and triage.
- **[SEV major] §4 (`ingest --retry` skips conversion)**: RESOLVED. §4 lifecycle table and protocol resume at the first unreferenced durable step; conversion runs iff `converted.md` is absent/unreferenced.
- **[SEV minor] §2 (`converted.md` description ignores rasters)**: RESOLVED. §2 layout contract explicitly defines `converted.md` as "absent for rasters, conversion failure, unsupported".
- **[SEV minor] §3 (Raster unit definition conflates unit key with source)**: RESOLVED. §3 Step 5 explicitly sets key `u0001`, `source: self`, `kind: raster` (Row 3), matching §2 schema and §5 asset copying.

### New Defects
None. Sections 1–5 are internally consistent, MECE, ledger-first, and meet all data and lifecycle constraints.

VOTE: APPROVE

# Response to round-4 reviews (DESIGN.md r5, 2026-11-09)

Legend: ACCEPT (change, r5 section) | ACK (marked resolved; no change). r5 length = r4 (346 lines). Real tool evidence used:
`_sample_ocr_report_png.json` (field names) and cx's AudioConverter probe.

## cx
- cx-1, cx-3–cx-33 (all marked RESOLVED), N1–N12, E1, E2, E4, E5 ACK.
- cx-2 ACCEPT. Adapter now maps the observed 0.3.5 fields only: `decision`, `coverage.{state, pages_total, pages_inspected}`,
  `summary.{scope, image_occurrences, candidates_high, candidates_low}`, `candidates[].{id, kind, page, priority}`, `issues[].code`,
  `schema_version`; PDF id bound uses `coverage.pages_total` when non-null; scope (inspected vs total) is preserved; the adapter is tested
  against the real sample and the characterization reports before implementation. JSON item fields renamed accordingly. §3, §8, AT-06.
- E3 ACCEPT. One rule for every artifact, staged or committed: a file is valid only if the governing ledger (`stage.json` in staging,
  `meta.json` once committed) records its sha256 and activity; resume ignores unreferenced artifacts and redoes that step. The window
  between writing `converted.md` and its ledger entry is therefore a bounded, documented reconversion case on a non-committed item;
  I2 is scoped to validly referenced `converted.md`. No "same step" claim remains. §3, §4, AT-26.
- F1 ACCEPT. The handoff carries its context: `stage.json` (relpath, exact filename, charset, claimed_at) is written first, then the
  inbox file is moved into the same `tmp-<n>/` under its unchanged filename. Startup distinguishes claimed-unhashed `tmp-*` (resume at
  hash) from identified `<id>/` (resume at the first unreferenced step) and `collision-*` (reported only). Full-schema validation applies
  to committed `meta.json` only. Test: crash right after the move with a nested Korean filename and changed restart flags. §4, AT-26.
- F2 ACCEPT. Audio/video never reach the converter by extension (pre-check -> `unsupported`, `network_converter`), and a converter result
  whose detected format is audio/video (accessor fixed at the characterization gate) is also `unsupported`; the `MissingDependencyException`
  promise is deleted; absent extras remain defence in depth only. §3, AT-12.

## ag
- Round-3 items ACK (resolved).
- ag minor (raster unit key) ACCEPT. §3 step 5: rasters get key `u0001`, `source: self`, `kind: raster`.

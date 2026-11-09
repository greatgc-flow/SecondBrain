# Slice 2 review response

Valid behavior changes were covered by tests before implementation. The requested
invocation without `--basetemp` first failed with `UsageError`; the added regression
suite then had **21 failed, 148 passed** before the fixes. Final validation:

```text
python -m pytest -q -p no:cacheprovider
171 passed in 4.36s
```

The default is `<repo>/.pytest-tmp`. A denied Windows temp directory can still
fall back visibly to `<repo>/work/pytest-foundation`; tests cover resetting an
already initialized temp factory for that fallback. This final run used the
default `.pytest-tmp` without needing the fallback. No git commands were run.

| Review / finding | Decision and evidence |
| --- | --- |
| Fable M1: failure reason vs error code | **FIXED.** Removed the equality requirement. A `FileConversionException` reason with `error.code="conversion_failed"` now loads successfully (`test_failed_conversion_reason_differs_from_error_code`). Both fields retain their schema validation. |
| Fable M2: retained staging ledger | **FIXED.** Committed `stage.json` is recognized as a retained ledger, without an orphan warning or deletion. The former orphan test now asserts retention and no warnings. This follows Fable's clarification of the rename-2/I8 interaction. |
| Fable L1: exact artifact bytes | **FIXED.** `write_text` documents that it writes sb-authored UTF-8/LF text; converter output and peer copies must use `write_bytes` for exact bytes. |
| Fable L2: ledger coverage gaps | **FIXED.** Added five parametrized cases for >20 approved units without acknowledgment, non-contiguous unit keys, non-candidate page sources, and summaries on non-ready/unsupported items. |
| Fable L3: audio-extra absence in CI | **FIXED (coverage; policy retained).** Extracted `check_audio_extras` for a direct test proving failure with importable extras under `CI=1` and success when absent. The session fixture still enforces it in CI; GitHub Actions supplies `CI=true` by default. Shared local extras are not uninstalled or hidden. |
| ag source blocker: skipped hidden/reparse warnings | **REJECTED.** DESIGN §4(b) and AT-36 assign `skipped_hidden`/`skipped_reparse` to **inbox enumeration**. For committed items, §2 requires unreferenced artifacts to warn `orphan`. `_orphans` already includes hidden/reparse files and prunes reparse directories before traversal; its directory entry is itself reported, without following it. The new committed hidden/link regression verifies all three orphan warnings and no child traversal. Referenced reparse artifacts remain `corrupt_meta`. |
| ag source major: NFC-fold orphan identities | **REJECTED.** DESIGN §2 preserves exact filenames; NFC is the display/sort field. NTFS and Linux can contain distinct NFC/NFD-equivalent names. Folding references would silently hide an unreferenced file. The new regression creates both spellings, confirms they are distinct files, and requires the extra spelling's orphan warning. No filenames or comparison keys are normalized. |
| ag source major: atomic JSON durability / temp location | **FIXED** flush + `os.fsync` before `os.replace`; tests verify flushed bytes and ordering, and preservation of the old ledger on fsync failure. **REJECTED** relocating the temp outside the ledger directory: DESIGN §2 specifies `*.tmp` + replace and explicitly tolerates/warns crash orphans (§4). A sibling temp stays on the destination volume, is ignored until replace, and remains visible as an orphan after failure. Moving it elsewhere is not needed for atomicity and would introduce scratch-location/cleanup policy into this primitive. |
| ag source major: Windows read-only deletion | **FIXED.** The rmtree error handler retries only `PermissionError` on a file carrying `FILE_ATTRIBUTE_READONLY`, after rechecking containment/reparse safety. It clears the attribute and retries the failed operation. Real read-only cleanup, simulated Windows attributes on both OSes, and non-read-only permission failure are tested. Other permission failures remain `io_error`. |
| ag source minor: Windows-invalid names / streams | **FIXED.** On Windows, filename validation rejects stream colons, reserved characters/control codes, trailing dot/space, and reserved device names. Tests cover these rules on both CI OSes. POSIX volume-valid names remain unchanged, consistent with the exact received-name contract. |
| ag source minor: unused fsutil primitives | **FIXED.** Removed `init_utf8_stdio` (CLI startup responsibility) and `fenced_block` (IMPL_PLAN's wiki ownership). Kept `check_path_length`, `esc`, and `percent_encode`, which IMPL_PLAN explicitly assigns to fsutil, with dedicated boundary/control-character/filename tests. |
| ag source minor: no tests in scope | **REJECTED (void per orchestrator).** Tests were reviewed separately; the three existing module test files already covered the stated areas. This response adds the valid requested regressions. |
| ag tests major: omitted basetemp / cached factory | **FIXED.** Omission defaults to `<repo>/.pytest-tmp`; an explicit outside-worktree path still raises `UsageError`. Changing the selected base resets `_given_basetemp` and cached `_basetemp`. Default selection, explicit refusal and permission fallback with an initialized factory are tested. |
| ag tests minor: unused provenance / summary helper | **REJECTED (premise incorrect).** `make_item` already exercises `ocr-verify` provenance for verified attempts; `test_at16_referenced_artifacts_required` and nested-history tests already call `add_summary`, exercising `summary` provenance. Added a focused round-trip test checking accepted summary provenance, OCR verification provenance and binding to the transcript digest. No used helpers were deleted. |
| ag tests minor: implicit text encoding | **FIXED.** All direct `read_text`/`write_text` calls in the three module test files now specify `encoding="utf-8"`; this also fixes the analogous calls outside the cited fsutil test lines. |
| ag tests minor: cwd-dependent temporary-path assertion | **FIXED.** The assertion uses the repository `WORKTREE`, not `Path.cwd()`. The regression explicitly changes into a nested inbox directory before checking the temporary path. |

Only the foundation modules/tests and this requested response were edited. No
later slice, fixtures, rubric scores, CI workflow, or approved design was changed.

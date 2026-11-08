### 1. Round-1 Finding Verification

- **ag-1**: RESOLVED (partial approval removed; §4/§5 enforce atomic approve/decline across all units).
- **ag-2**: RESOLVED (boundary enforced via nonce-tagged fence and out-of-model validation per cx-12/RESPONSE_r1).
- **ag-3**: RESOLVED (candidate IDs kept opaque; synthetic keys `u001...` used; extraction uses safe tool names).
- **ag-4**: RESOLVED (`classified` state deleted; `unsupported` and `failed` are distinct resting states in §4).
- **ag-5**: RESOLVED (`unknown` class added with `awaiting-approval` state and explicit `decline` resolution).
- **ag-6**: RESOLVED (REJECT holds; `_mdgc_guide.txt` contract confirms HWP/HWPX converter and triage support in 0.3.5).
- **ag-7**: RESOLVED (uniform metadata schema and serialized data envelopes specified in §2).
- **ag-8**: RESOLVED (scratch paths consolidated under single root directory `work/<id>/`).
- **ag-9**: RESOLVED (single unified heading template specified in §5).
- **ag-10**: RESOLVED (REJECT holds; operator approval is explicit per item with unit counts and outbound notice).

---

### 2. New Defects in Sections 1–5

- [SEV blocker] §3 — Unconditional upfront input evaluation crashes on unsupported/unconvertible files — Step (5) evaluates `has_native_text(converted.md)` unconditionally in staging before evaluating the predicate table. For audio/video (Row 1) or conversion failures (Rows 2, 4), `converted.md` does not exist, raising `FileNotFoundError`. CLI triage (Step 3) is also invoked on audio files before Row 1 can reject them. — Fix: Pipeline input evaluation lazily/staged (pre-checks -> conversion -> triage -> native text check) with top-down short-circuiting.
- [SEV blocker] §5 — Dynamic recomputation of R over recorded units causes verification treadmill — §5 defines required verification set R over `n = recorded units`. When units are verified, their status transitions to `verified`, removing them from the recorded set. Recomputing R on subsequent `ocr verify` calls shrinks `n` and shifts the window of "first min(...) other units in key order", forcing previously unselected units into R and preventing multi-call accumulation from finalizing. — Fix: Compute and pin R once over the total approved units `ocr.units` (N), rather than dynamically over units currently in `recorded` state.
- [SEV major] §4 vs §5 — Invariant I2 directly contradicts container media extraction — §4 Invariant I2 asserts "conversion is never invoked for an item that has it", but §5 explicitly invokes `MarkItDown().convert(path, extract_media=...)` during `ocr approve` on containers that already have `converted.md`. Any mock/assertion testing I2 will fail on container approval. — Fix: Amend I2 to specify that `converted.md` is never regenerated/overwritten, while scoped media extraction to `work/<id>/` during approval is permitted.
- [SEV minor] §5 — Hardcoded "PNG paths" in COMMANDS.txt breaks non-PNG rasters and container media — §5 allows units with arbitrary extensions `uNNN<ext>` (e.g. `.jpg`, `.webp`), but specifies `COMMANDS.txt` prompt template with "quoted PNG paths", generating missing file paths for non-PNG images. — Fix: Change specification to "quoted unit image paths (`uNNN<ext>`)".
- [SEV minor] §4 vs §5 — Invariant I6 contradicts sampled-out unit inclusion — §4 Invariant I6 asserts "Unverified OCR text never appears in transcript.md", yet §5 includes unverified units outside R into `transcript.md` labelled `verified: sampled-out`. — Fix: Amend I6 to explicitly permit units with `sampled-out` disposition while barring `pending` or `mismatched` text.
- [SEV minor] §5 — Undefined process exit code for CLI in partial failure — §5 specifies for `ocr record`: "exit 2 for that unit, others proceed". A process has only one exit code; automation cannot tell whether the batch command succeeded. — Fix: Specify that the CLI process exits 2 overall if any unit encountered `stale_output`, after processing remaining valid units.

---

VOTE: REJECT (2 blockers)

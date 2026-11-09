1. [SEV blocker] §4 & §5 — State machine deadlock on partial OCR approval/decline: §5 allows approving/declining page subsets (`--pages`), but §4 only permits `ocr approve`/`decline` from `awaiting-ocr-approval` with no transition from `ocr-approved`. Once a subset is approved, remaining pages can never be approved or declined under Invariant I6 (illegal transition exits 2), permanently deadlocking partial runs.
   Concrete fix: Add explicit self-transitions in §4 table: `ocr-approved` -> `ocr approve [--pages]` -> `ocr-approved` (updates `approved_ids`), and `ocr-approved` -> `ocr decline [--pages]` -> `ocr-approved` (or `ocr-done` if all candidate pages reach a resolved terminal state).

2. [SEV blocker] §6 & §7 — Prompt injection boundary absent in `llm prepare`: Untrusted text from converted PDFs and OCR transcripts is written verbatim into `llm-work/<id>/prompt.txt` alongside instructions without delimiter isolation or escaping. Adversarial document content can hijack the peer model to alter summaries or front-matter schemas.
   Concrete fix: Enclose source text in strict XML boundaries (`<untrusted_source_content>...</untrusted_source_content>`), escape tag occurrences in content, and inject an explicit system constraint instructing the peer LLM to treat all text within the boundary as unprivileged data.

3. [SEV blocker] §2 & §5 — Path traversal and Windows path crash in media extraction: §5 extracts ZIP media IDs (e.g., member paths like `ppt/media/image1.png`) "unchanged" into `ocr-work/<id>/`. ZIP member paths can contain nested subdirectories, illegal Windows characters (`:`, `*`, `?`), or path traversal (`../`), causing unhandled `FileNotFoundError`, `OSError`, or writes outside scratch.
   Concrete fix: Sanitize and flatten extracted member names to safe deterministic slugs (e.g., `media_001.png`) in `ocr-work/<id>/` and maintain the mapping to original member paths in `manifest.json`.

4. [SEV major] §4 & §2 — MECE state violation with overloaded `classified` state: `classified` acts as an ephemeral in-flight transition for normal files, but serves as a terminal state for `unsupported` and an error state for `failed`. As a result, `sb status --json` state counts lump failed and unsupported items together under `classified`.
   Concrete fix: Eliminate `classified` as a resting state. Add explicit resting states `unsupported` and `failed`. Auto-transition directly from `ingested` to `transcribed`, `awaiting-ocr-approval`, `unsupported`, or `failed`.

5. [SEV major] §3 — MECE classification mismatch on `unknown`: BRIEF explicitly requires classes to cover `unsupported/unknown`. DESIGN §3 table (C11, C12) forces `unknown` triage into `text-only` (with a hidden caveat) or `failed`, risking silent misclassification of image-heavy documents where triage failed.
   Concrete fix: Add `unknown` as an explicit first-class category in §3 when triage returns `unknown`, routing to `awaiting-ocr-approval` or an explicit manual triage state rather than silently assuming `text-only`.

6. [SEV major] §8 & AT-06 — Broken TDD fixture `한글이름.hwpx`: `markitdown-gc` 0.3.5 does not natively support Hancom HWP/HWPX; AT-06 will raise `UnsupportedFormatException` and fail the `text-only` assertion during automated testing.
   Concrete fix: Replace `text-only/한글이름.hwpx` with a natively supported fixture (e.g. `text-only/한글이름.docx` or `.txt`), and move HWPX to `unsupported/` unless a custom converter plugin is implemented.

7. [SEV major] §7 & §8 — Incomplete `--json` contract across subcommands: §7 only defines the JSON schema for `ingest`, with minor addenda for `status` and `wiki build`. `ocr approve/record/verify` and `llm prepare` have no defined JSON structure, making them untestable for headless automation.
   Concrete fix: Specify a uniform JSON envelope for all subcommands: `{"command": str, "ok": bool, "exit": int, "item_id": str|null, "data": dict, "errors": list}`.

8. [SEV minor] §2 — Directory sprawl vs VerySimpleGuide: Maintaining top-level `raws/`, `ocr-work/`, and `llm-work/` clutters `<root>` with redundant scratch directories.
   Concrete fix: Merge ephemeral workspaces into a single disposable scratch tree `<root>/work/<id>/{ocr,llm}` (or `raws/<id>/.work/`), preserving a clean 3-folder root layout (`inbox/`, `raws/`, `wiki/`).

9. [SEV minor] §4 vs AT-21 — Provenance heading format discrepancy: §4 specifies appended OCR sections as `## OCR <id> (peer, model, date)`, while AT-21 asserts `## OCR p2 (cc-verified, cx, m, date)`.
   Concrete fix: Standardize the heading format across §4, §5, and AT-21 to `## OCR <pageid> (verified: <peer>, transcribed: <peer>, <model>, <date>)`.

10. [SEV minor] §5 & BRIEF — Dismissal of sensitive content approval gate: BRIEF mandates explicit approval for sensitive content; §5 dismisses this by stating "Sensitive content cannot be detected" without providing an operator mechanism.
    Concrete fix: Allow marking items as sensitive via `sb ingest --sensitive` or an `.inbox-sensitive` marker, recorded as `meta.json.sensitive=true`, requiring `--yes-sensitive` to approve.

VOTE: REJECT (3 blockers)

# SecondBrain v1 renewal: research findings

Research date: 2026-11-09. Internet access was available; primary sources are linked below.
Read first: [BRIEF.md](BRIEF.md) and [_mdgc_guide.txt](_mdgc_guide.txt).
“Verified” means confirmed in published documentation, not experimentally validated here. Proposals are explicitly separated.

## Verified: Markdown wiki patterns

- **Karpathy's LLM wiki** preserves immutable raw sources, maintains a derived Markdown wiki, and uses a steering/schema document to define conventions and ingest/query/lint workflows. `index.md` catalogs pages; append-only `log.md` records activity. Maintenance includes stale claims, contradictions, orphan pages, and missing links. His gist is an architectural idea, not a fixed schema or reliability benchmark. [Original gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- **Obsidian** supports both `[[Note]]` and Markdown links; its documentation recommends Markdown links for interoperability. Link destinations need URL encoding; forward slashes work on Windows. Obsidian block references are application-specific. Flat YAML properties support titles, tags, aliases, dates, and lists; nested properties have limited UI support. [Links](https://obsidian.md/help/links), [properties](https://obsidian.md/help/properties)
- **Zettelkasten** combines individually addressable notes, references, and meaningful connections; structure notes provide topic entry points. Atomicity encourages focused ideas, rather than arbitrary document splitting. This suggests small concept pages and curated hubs when useful. [Introduction](https://zettelkasten.de/introduction/), [atomicity](https://zettelkasten.de/atomicity/guide/)
- **PARA** organizes material by Projects, Areas, Resources, and Archives, emphasizing actionability. It supplies an organizational lens, not a transcript/provenance schema. [Forte Labs](https://fortelabs.com/blog/12-steps-to-build-a-second-brain/)
- **Logseq** supplies journal/page navigation and block references such as `((UUID))`; file-based properties use `key:: value`. Current documentation distinguishes file graphs from DB graphs and offers standard Markdown exports. Compatibility must name the graph/format being targeted; “Logseq-compatible Markdown” is too vague. [Documentation](https://docs.logseq.com/), [block references](https://github.com/logseq/docs/blob/master/pages/Block%20Reference.md), [properties](https://github.com/logseq/docs/blob/master/pages/Properties.md), [DB version](https://github.com/logseq/docs/blob/master/db-version.md)

Synthesis/inference: adopt the raw/derived boundary, a small written schema, explicit links, and an index. PARA can be optional tags/views; neither a four-folder reorganization nor Logseq block IDs are necessary for this pipeline.

## Verified: ingestion, reuse, provenance

- **PDF OCR needs finer evidence than “text exists.”** OCRmyPDF's skip mode skips whole pages with text; redo mode can mask visible text and OCR remaining image text. A mixed page can therefore contain extractable text and still need transcription. These are comparison patterns, not a recommendation to replace the owner's peer OCR workflow. [OCR processing modes](https://ocrmypdf.readthedocs.io/en/latest/advanced.html#ocr-processing-mode)
- **OCR output alone can be incomplete.** OCRmyPDF's sidecar excludes existing native text and pages skipped by selection, size, or timeout. Native extraction and OCR must retain their source locations when assembled; an OCR sidecar is not necessarily the complete transcript. [Cookbook](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html#produce-pdf-and-text-file-containing-ocr-text)
- **Checksums support exact duplicate detection.** Paperless-ngx compares source/archive checksums; its documentation warns that another scan need not be byte-identical. Thus exact reuse and semantic near-duplicate detection are different problems. Python provides SHA-256 without an additional package. [Paperless administration](https://docs.paperless-ngx.com/administration/), [hashlib](https://docs.python.org/3/library/hashlib.html)
- **Provenance has three useful parts:** entities (original/transcript), activities (extraction/OCR/correction), and agents (tool/peer/model). W3C PROV expresses their relationships; a small JSON record can capture these ideas without adopting RDF or a provenance service. [PROV primer](https://www.w3.org/TR/prov-primer/)

## Verified: failure mechanisms

- **Hallucination:** NIST describes confidently false outputs, internal inconsistency, and fabricated citations. A plausible summary or a syntactically valid source link does not establish factual support. [NIST AI 600-1, section 2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
- **Prompt injection:** external documents, hidden text, and attachments can carry instructions; malicious content can persist across sessions. OWASP recommends separating instructions/data, validating tool parameters, and enforcing least privilege outside the model. A “document text is data” prompt alone is insufficient. [OWASP guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- **Windows filenames:** reserved characters/device names, trailing spaces/dots, and usual case-insensitive behavior complicate title-derived paths. Traditional MAX_PATH is 260 characters; longer-path support depends on application/OS configuration. [Naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file), [path limits](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)
- **Korean Unicode:** canonically equivalent composed Hangul and Jamo sequences can differ in code points. NFC performs canonical composition; NFKC additionally folds compatibility distinctions and should not be applied blindly. Windows file APIs treat names as opaque WCHAR sequences and do not supply application-level Unicode normalization. [Unicode UAX #15](https://www.unicode.org/reports/tr15/), [Windows Unicode behavior](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)
- **Minimalism baseline:** VerySimpleGuide calls for shared semantics, small implementations, and evidence-backed claims; it explicitly describes itself as a reference, not a mandatory application framework. [VerySimpleGuide README](https://github.com/greatgc-flow/VerySimpleGuide)

## Local requirements and unverified assumptions

- Binding local inputs: deterministic source pages/indexes/tags/links by default; optional LLM summaries/concepts only on explicit command through peerhub. Karpathy's fully LLM-maintained wiki does not override this boundary.
- The supplied guide says markitdown-gc 0.3.5 never OCRs; its report covers PDF/raster/DOCX/PPTX/XLSX/HWP5/HWPX. `no_candidates` does not prove no OCR need; partial/unknown coverage requires review. Report exit 0 means report produced, not inspection complete. These exact version claims were **not independently web-verified**: public package/repository fetches failed.
- The guide describes HWP5/HWPX image placeholders, flattened merged tables, unsupported encrypted/old HWP, and unsupported legacy DOC/PPT/RTF conversion. Treat these as local tool-contract inputs; no format fixtures were executed here.
- Owner policy: show triage classes and page/image counts before OCR; OCR only approved files. Sensitive material and jobs exceeding 20 pages/images always require explicit approval. The guide adds batching/verification limits; these are policy, not research-derived thresholds.
- No measured transcription costs, Korean recognition accuracy, HWP image coverage, or corpus-size performance claims are established here. Hashes miss re-encoded/rescanned duplicates; durable OCR-unit reuse across changed source bytes remains an open design question.

## Proposed minimal contract (design inference; not implemented)

```text
inbox/                         incoming files
raws/<stable-ascii-id>/         original.<ext>, transcript.md, metadata.json
wiki/sources/<id>.md            deterministic source view
wiki/concepts/<slug>.md         explicit LLM output only
wiki/index.md                  sorted, generated catalog
wiki/log.md                    chronological change log; not processing state
WIKI_SCHEMA.md                 one short conventions/ownership contract
```

- Preserve original bytes; keep the full SHA-256 as metadata, independent of the folder ID. This is a duplicate-work check, without restoring the discarded v0.1 object-store/receipt architecture.
- `metadata.json` is the authoritative per-source processing record: schema version, ID, source SHA-256, original names/URI when available, import time, triage class/coverage/counts, transcript SHA-256, and extraction/OCR provenance.
- Provenance records need tool+version, method, peer+model where applicable, UTC completion time, language/options/prompt revision, source page/media IDs, and verification status. Audio/video units use timestamps; Office/HWP images use member IDs, not invented page numbers. Corrections record their author/time and preserve attribution to the original transcription.
- Persist OCR text and per-unit `pending / ocr_done / verified` state under `raws/` before deleting temporary renders. Keep unverified text visibly marked and out of accepted wiki content. One transcript can contain separate native/OCR sections; retain page/media/time locators.
- Schema defines required fields, generated-file ownership, Markdown links, index ordering, OCR approval semantics, and rebuild rules. Page frontmatter can stay flat: `id`, `title`, `kind`, `source_ids`, `input_digests`, `generator_version`, `tags`; add `model`/`prompt_revision` only for LLM output.
- Use `[Title](../sources/<id>.md)` and `[Transcript](../../raws/<id>/transcript.md#page-3)` with stable generated headings. Build relative links from their containing file; use `/` and percent-encode path components. Keep the vault root above both `raws/` and `wiki/` if Obsidian access to transcripts is wanted.
- Index source pages and optional concepts with explicit tier/status labels. Append log entries only for actual changes; exclude log/schema/concept pages from deterministic overwrites. Processing decisions read metadata, never prose logs.

## Concrete recommendations tied to VerySimpleGuide

These are peer proposals for deliberation; the VSG ties apply its verified small-implementation/evidence principles to this design.

1. **Ship files first:** use the layout above, one metadata sidecar per source, and a sorted Markdown index. Scan sidecars for exact hashes initially; defer DB/vector/graph infrastructure until measured need. **VSG tie: smallest sufficient implementation.**
2. **Write one short schema:** define ownership, required metadata, stable headings, links, and rebuild behavior. Prefer plain Markdown and flat frontmatter; represent PARA as optional tags. **VSG tie: shared semantics without framework overhead.**
3. **Make classification MECE:** first classify incomplete/unsupported inspection as unknown; otherwise distinguish no-ocr, ocr-required, and mixed by native text plus unread image-text evidence. Blank/decorative content can be no-ocr after review. Preserve the original report verdict separately; show counts and reasons before any approved OCR. **VSG tie: explicit, testable decisions.**
4. **Reuse before processing:** compare original-byte SHA-256 and validate existing transcript/provenance before conversion/OCR. Renames reuse the source; model/tool upgrades do not silently invalidate completed transcription. Resume only pending units; missing/corrupt completed artifacts require an explicit recovery decision. **VSG tie: remove repeated work.**
5. **Keep provenance beside text:** persist unit locators, tool/model/version/date, output digest, and verification state before temporary-work cleanup. Use the owner's OCR pilot, batching, and independent-check recipe. **VSG tie: evidence at the point of use.**
6. **Keep LLM work explicit:** deterministic generation reads accepted transcripts and supplied metadata; it performs no semantic summarization/tag invention. Make peerhub an operator workflow initially; optional summaries/concepts require an explicit command and source-level citations. **VSG tie: narrow dependencies and behavior.**
7. **Detect staleness mechanically:** record each page's source transcript digests and generator/prompt revision; compare with current inputs. Rebuild deterministic pages, flag dependent LLM pages stale, and report broken links/orphans. Preserve contradictions and require deliberate semantic refresh; input freshness does not prove real-world currency or truth. **VSG tie: bounded checks with honest claims.**
8. **Constrain document authority:** treat raw text, OCR, frontmatter, and generated prose as untrusted data; never let them redefine schema or permissions. Validate paths/links, restrict peer writes to designated outputs, and prevent automatic URL/tool execution, including remote image loads. **VSG tie: enforce a small boundary outside the model.**
9. **Use stable ASCII storage names:** preserve Korean titles/original names in UTF-8 metadata. NFC-normalize generated display/search keys, detect normalized/case collisions, and open existing files by their actual discovered path. Never normalize source bytes or silently rename originals; keep paths short. **VSG tie: one predictable Windows convention.**
10. **Prove the critical invariants:** offline fixtures should cover text/scanned/mixed/unknown PDFs, Office/HWP embedded images, declined OCR, repeat ingestion, interrupted OCR reuse, stale links, hostile instructions, and NFC/NFD names. Assert unchanged input causes no transcription call; approval gates all OCR; deterministic rebuilds match. **VSG tie: focused evidence before additional machinery.**

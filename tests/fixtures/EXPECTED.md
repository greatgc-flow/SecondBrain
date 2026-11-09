# Characterization — markitdown-gc 0.3.6

Current gate evidence for SecondBrain v1.0.1 / DESIGN §3. All inputs are synthetic; source bytes and filenames are unchanged.
Historical gate-1b contradictions are resolved by the current plain-text/markup split and explicit StreamInfo charset hints.

## 0.3.6 re-characterization

- Replayed all **36** source/peer/LLM inputs through the real gate-1b API and CLI on Windows / Python 3.15.2, with both
  markitdown-gc **0.3.5** and **0.3.6** in the same environment. Also classified every input with the current extension-selected adapter.
- **Converter differences: none.** Conversion text/exception type and message, media filenames/bytes/digests, and full report JSON
  (including decision, coverage, summary, candidates and issues) are identical for every input. Current class/state/reason,
  native-text flags and unit enumeration are identical for both versions. No DESIGN §3 outcome or rule changed.
- **Pre-existing expectation corrections:** `llm/hostile.md`, `llm/valid.md`, `peer-output/illegible.md`, `peer-output/u0001.md`
  now record row 11 **text-only/ready** instead of the obsolete row 12 unknown/awaiting-approval. Both versions already yield this
  result under the current media-free-markup inspection rule; these corrections are not 0.3.6 behavior changes.
- **Guide-only addition:** `--guide all` adds an HWP5 OLE-stream media-extraction recipe; fixture output is unchanged.
- The short CP949 check is also unchanged: bare charset yields `陛`, explicit StreamInfo yields the required `가`.
- The existing row-11 overrides for CP949 and the three LLM JSON inputs are consolidated into the single current expected row;
  their effective outcomes are unchanged. Historical r8/r9 duplicate keys are removed.
- Regenerated all 36 probes with `converter_version=0.3.6`, one current expected row and the observed classification. Raw reports
  and converted text remain unchanged. Excerpts retain the original 180-character limit. No synthetic report fixture was regenerated.

## Method and environment

Each of the 36 files below was passed independently to the real API and report CLI, including denied extensions, rasters and empty
inputs that sb itself must short-circuit. The diagnostic API is exactly the gate-1b call:

```python
from markitdown import MarkItDown
MarkItDown(enable_plugins=False).convert(
    absolute_path, charset=charset,  # cp949 only for korean-cp949.txt; otherwise None
    # Only DOCX/PPTX/XLSX/HWP/HWPX receive extract_media=absolute_work_media_path.
)
```

```text
markitdown-gc ABSOLUTE_FILE --ocr-report -o ABSOLUTE_REPORT_PATH
```

All **36 report commands per version exited 0**. Reports below retain the exact CLI bytes. Conversion artifacts store exact UTF-8
`text_content` bytes, with only the generated extraction-directory prefix held at the original `work/characterize/media/<key>/`
location so staging paths cannot create false differences. Digests refer to these stable artifacts; extracted media digests are exact.

Scratch API/CLI outputs and the paired comparison live under `work/recharacterize-036/`; temp directories stayed in the worktree.
The same startup guard denied external connections and DNS in both API processes and report children; import-time loopback probes
remain allowed. No OCR, peer or LLM service was invoked. Optional audio helpers in the shared environment are diagnostic only:
SecondBrain's extension-selected adapter cannot fall through to them; clean no-audio CI remains a separate release gate.

Probes distinguish direct-tool evidence from `observed_classification`, measured with the current actual adapter, its charset hint,
source-media inspection and early short circuits. This keeps incomplete raw markup reports from overriding locally proven media absence.
The older `charset-observation.json` explicitly retains its historical 0.3.5 measurements; current charset behavior is exercised by
`test_convert.py` on the pinned runtime. This local characterization does not establish CI or exact-candidate live-smoke completion.

## Fixture construction / coverage

- Plain/Markdown/HTML/JSON are fixed synthetic bytes; CP949 is actually encoded
  CP949. The filename shown as `nfd-이름.txt` in the design is stored with NFD
  Hangul codepoints; preserve its actual directory-entry spelling on checkout.
- DOCX: python-docx paragraphs, a truly empty 2x2 table, or one embedded PNG.
  Alt-text-only has no body text, only picture `descr`; native-text removal
  discards the image syntax and its alt text. XLSX: two rows and optional PNG.
  PPTX: one slide with one native-text box and one PNG. All embedded PNGs have
  SHA256 `9c4b0cd1370ef33ef6093b25e6534a3e26ed8605a0e9ef5e39ffe1535d20806f`.
- PDF: pypdf objects with Helvetica native text and/or one Flate RGB raster.
  `two-pages.pdf` has native text on p1 and a scan on p2; `same-page.pdf` has
  both on p1. `scan.pdf` contains only the raster. Numeric p2/p10 ordering
  in AT-18 needs a synthetic >=10-page report; the two-page source cannot
  honestly supply a p10 candidate (the §3 page bound forbids it).
- `photo.png`: Pillow RGB 400x200, EXIF synthetic description/date/orientation=1,
  200 dpi. Its pixels show invoice 12345, date 2026-11-09, total 42 USD.
- HWP5: a small stdlib CFB v3/minifat writer, an uncompressed FileHeader,
  DocInfo, BodyText/Section0 UTF-16LE PARA_TEXT record, and optional BinData PNG.
  HWPX: stdlib ZIP/XML with mimetype, manifest, header, section0, content.hpf
  and optional BinData PNG. These minimal parser fixtures are not a claim of
  full Hancom editor interoperability. Both text and image variants convert
  and triage successfully; **no operator-supplied HWP/HWPX fixture is pending**.
- `encrypted.hwp` sets the real HWP5 encryption flag; the minimal synthetic
  body is not encrypted ciphertext. The parser correctly refuses it.
  `corrupt.pdf` has a PDF header but no root object. `zero-bytes.txt` is empty.
- `legacy.doc` is a minimal CFB WordDocument/FIB-signature container, not a
  complete Word document; the required acceptance is extension rejection
  before conversion. `data.xyz` is arbitrary synthetic text. `clip.mp3` is
  five 417-byte synthetic MPEG-1 Layer III header/zero-payload frames; playback
  is unverified without a decoder. `renamed-audio.pdf` has identical bytes.
  Renamed audio is pinned to **null/failed, FileConversionException (row 5)**
  on this Python 3.15 environment; PdfConverter fails on missing /Root before
  any transcript. Pin other Python-version results separately if sniffing differs.
- `llm/valid.json` binds exactly to the characterized `text/plain.txt` view
  digest; `bad-digest.json` is all-zero instead; `missing-key.json` omits
  `source_digest`. Peer/model/date values are synthetic. Peer and LLM text
  files are adapter data, not additional ingest acceptance categories.
  The `[illegible]`/`[no text]` and hostile instructions are inert test data.

## Synthetic report fixtures (not converter measurements)

`reports/sample-ocr-report-png.json` copies the design's supplied real sample
without moving the renewal reference. The following fixtures are synthetic;
never confuse them with the per-source raw reports linked below. Rows 1–5
short-circuit before triage, so their reports are unused contextual payloads.

| File | Additional preconditions / expected result |
| --- | --- |
| `row-01.json` | zero-size source -> null/failed, empty_file; report unused |
| `row-02.json` | disallowed extension -> unsupported/unsupported; report unused |
| `row-03.json` | raster -> ocr-required/awaiting-approval; report unused |
| `row-04.json` | UnsupportedFormatException or MissingDependencyException -> unsupported; report unused |
| `row-05.json` | FileConversionException -> null/failed; report unused |
| `row-06.json` | invalid schema_version -> null/failed, report_invalid |
| `row-07.json` | ocr_recommended but no candidates -> null/failed, no_candidate_ids |
| `row-08.json` | valid p1 unit + no native text -> ocr-required/awaiting-approval |
| `row-09.json` | valid p1 unit + native text -> mixed/awaiting-approval |
| `row-10.json` | recommended candidate but zero extracted units -> unknown/awaiting-approval, no_units |
| `row-11.json` | no_candidates + complete -> text-only/ready |
| `row-12.json` | unknown + none -> unknown/awaiting-approval |
| `invalid.json` | deliberately malformed JSON -> report_invalid |
| `missing-coverage.json` | missing coverage -> report_invalid |
| `wrong-types.json` | image_occurrences is a string -> report_invalid |
| `dup-ids.json` | duplicate p1 candidate ids -> report_invalid |
| `bad-page-id.json` | PDF candidate p0 -> report_invalid |
| `exit1.txt` | simulated runner exit 1; no JSON parsing -> report_failed |

There is no natural report-invalid/exit-nonzero source in this tiny corpus:
the real CLI reports unknown/none with issues even for corrupt files. Use the
explicit synthetic cases above for fault tests rather than claiming observed
nonzero exits. More cross-product synthetic reports remain Slice 3 work.

## Per-file observations

### `characterize/renamed-audio.pdf` (2085 bytes)

[Input](characterize/renamed-audio.pdf) · [raw report](reports/characterize--renamed-audio.pdf.json) · [probe](reports/characterize--renamed-audio.pdf.probe.json)

Conversion: **FileConversionException**; no converted artifact. See probe for exact message.
DESIGN row **5** -> **null/failed**; reason `FileConversionException`; units 0.
Native text: `none`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `failed/corrupt.pdf` (39 bytes)

[Input](failed/corrupt.pdf) · [raw report](reports/failed--corrupt.pdf.json) · [probe](reports/failed--corrupt.pdf.probe.json)

Conversion: **FileConversionException**; no converted artifact. See probe for exact message.
DESIGN row **5** -> **null/failed**; reason `FileConversionException`; units 0.
Native text: `none`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"corrupt","detail":"PDF could not be inspected."}]}
```

### `failed/encrypted.hwp` (3072 bytes)

[Input](failed/encrypted.hwp) · [raw report](reports/failed--encrypted.hwp.json) · [probe](reports/failed--encrypted.hwp.probe.json)

Conversion: **FileConversionException**; no converted artifact. See probe for exact message.
DESIGN row **5** -> **null/failed**; reason `FileConversionException`; units 0.
Native text: `none`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[{"code":"corrupt","detail":"HWP5 media could not be inspected."}]}
```

### `failed/zero-bytes.txt` (0 bytes)

[Input](failed/zero-bytes.txt) · [raw report](reports/failed--zero-bytes.txt.json) · [probe](reports/failed--zero-bytes.txt.probe.json)

Conversion: [exact text](reports/failed--zero-bytes.txt.converted.md), 0 bytes; SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
DESIGN row **1** -> **null/failed**; reason `empty_file`; units 0.
Native text: `false`; extracted assets: 0.
Direct diagnostic conversion/triage is bypassed by sb’s earlier guard.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"corrupt","detail":"Empty input."}]}
```

### `llm/bad-digest.json` (204 bytes)

[Input](llm/bad-digest.json) · [raw report](reports/llm--bad-digest.json.json) · [probe](reports/llm--bad-digest.json.probe.json)

Conversion: [exact text](reports/llm--bad-digest.json.converted.md), 204 bytes; SHA256 `2a2638b5a15470c97fe79461a543ad5ac3030460f897badd3b1ca64dfd6f5869`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `llm/hostile.md` (79 bytes)

[Input](llm/hostile.md) · [raw report](reports/llm--hostile.md.json) · [probe](reports/llm--hostile.md.probe.json)

Conversion: [exact text](reports/llm--hostile.md.converted.md), 79 bytes; SHA256 `7bdd23c80bbc6467ef0b105261296a699f37cb9a1205540c88a36e7b336d16bd`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `llm/missing-key.json` (118 bytes)

[Input](llm/missing-key.json) · [raw report](reports/llm--missing-key.json.json) · [probe](reports/llm--missing-key.json.probe.json)

Conversion: [exact text](reports/llm--missing-key.json.converted.md), 118 bytes; SHA256 `21aaf5d791c18e00f107fe1bceb6ccba7a3422c82f6e77e823d41aa7b87269a8`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `llm/valid.json` (204 bytes)

[Input](llm/valid.json) · [raw report](reports/llm--valid.json.json) · [probe](reports/llm--valid.json.probe.json)

Conversion: [exact text](reports/llm--valid.json.converted.md), 204 bytes; SHA256 `9956c8e52efb4d185c5a6d51cefb9529ba64ac308121143ea3540ea0a985866a`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `llm/valid.md` (39 bytes)

[Input](llm/valid.md) · [raw report](reports/llm--valid.md.json) · [probe](reports/llm--valid.md.probe.json)

Conversion: [exact text](reports/llm--valid.md.converted.md), 39 bytes; SHA256 `5f6239120682dcb69ffa3257c925fc96d848a6817472ae76b6a205f334783f7c`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `mixed/image.hwp` (7168 bytes)

[Input](mixed/image.hwp) · [raw report](reports/mixed--image.hwp.json) · [probe](reports/mixed--image.hwp.probe.json)

Conversion: [exact text](reports/mixed--image.hwp.converted.md), 110 bytes; SHA256 `28638eb6696fbfcb9d59d9198a335ad4a514a5548f613ffe8606445344a924ce`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 1.

```json
{"decision":"review","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":1,"candidates_high":0,"candidates_low":1,"media_small":0},"candidates":[{"id":"BinData/BIN0001.png","kind":"image","page":null,"priority":"low","reasons":["embedded_image"],"decor":false}],"issues":[]}
```

### `mixed/image.hwpx` (4668 bytes)

[Input](mixed/image.hwpx) · [raw report](reports/mixed--image.hwpx.json) · [probe](reports/mixed--image.hwpx.probe.json)

Conversion: [exact text](reports/mixed--image.hwpx.converted.md), 109 bytes; SHA256 `c8ff7ee1ca5c548e4494588a6fb64f978bb6d342268d9f01e99bdfb243621991`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 1.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":28,"image_occurrences":1,"candidates_high":1,"candidates_low":0,"media_small":0},"candidates":[{"id":"BinData/image1.png","kind":"image","page":null,"priority":"high","reasons":["embedded_image","scan_like"]}],"issues":[]}
```

### `mixed/image.xlsx` (9514 bytes)

[Input](mixed/image.xlsx) · [raw report](reports/mixed--image.xlsx.json) · [probe](reports/mixed--image.xlsx.probe.json)

Conversion: [exact text](reports/mixed--image.xlsx.converted.md), 164 bytes; SHA256 `21ea29685185916740c583e7e1f111b345ea3ae631462d939c8a4767bbb9b735`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 1.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":22,"image_occurrences":1,"candidates_high":1,"candidates_low":0,"media_small":0},"candidates":[{"id":"xl/media/image1.png","kind":"image","page":null,"priority":"high","reasons":["embedded_image","scan_like"]}],"issues":[]}
```

### `mixed/same-page.pdf` (4231 bytes)

[Input](mixed/same-page.pdf) · [raw report](reports/mixed--same-page.pdf.json) · [probe](reports/mixed--same-page.pdf.probe.json)

Conversion: [exact text](reports/mixed--same-page.pdf.converted.md), 53 bytes; SHA256 `b299ba35ac18bf0821f459b74fe3722f0b3015f77883296b83a5905c7b28c4bc`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 0.

```json
{"decision":"review","coverage":{"state":"complete","pages_total":1,"pages_inspected":1,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":1,"nonspace_chars":44,"image_occurrences":1,"candidates_high":0,"candidates_low":1},"candidates":[{"id":"p1","kind":"page","page":1,"priority":"low","reasons":["image_with_text_layer"]}],"issues":[]}
```

### `mixed/slides.pptx` (32112 bytes)

[Input](mixed/slides.pptx) · [raw report](reports/mixed--slides.pptx.json) · [probe](reports/mixed--slides.pptx.probe.json)

Conversion: [exact text](reports/mixed--slides.pptx.converted.md), 150 bytes; SHA256 `9898c42bd601d9d1752fa9f12baf29d7dc897d417a36171e8932b91161c9b4cb`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 1.

```json
{"decision":"review","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":43,"image_occurrences":1,"candidates_high":0,"candidates_low":1,"media_small":0},"candidates":[{"id":"ppt/media/image1.png","kind":"image","page":null,"priority":"low","reasons":["embedded_image"]}],"issues":[]}
```

### `mixed/two-pages.pdf` (4437 bytes)

[Input](mixed/two-pages.pdf) · [raw report](reports/mixed--two-pages.pdf.json) · [probe](reports/mixed--two-pages.pdf.probe.json)

Conversion: [exact text](reports/mixed--two-pages.pdf.converted.md), 53 bytes; SHA256 `b299ba35ac18bf0821f459b74fe3722f0b3015f77883296b83a5905c7b28c4bc`.
DESIGN row **9** -> **mixed/awaiting-approval**; reason `None`; units 1.
Native text: `true`; extracted assets: 0.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":2,"pages_inspected":2,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":1,"nonspace_chars":44,"image_occurrences":1,"candidates_high":1,"candidates_low":0},"candidates":[{"id":"p2","kind":"page","page":2,"priority":"high","reasons":["scan_like"]}],"issues":[]}
```

### `ocr/alt-text-only.docx` (39132 bytes)

[Input](ocr/alt-text-only.docx) · [raw report](reports/ocr--alt-text-only.docx.json) · [probe](reports/ocr--alt-text-only.docx.probe.json)

Conversion: [exact text](reports/ocr--alt-text-only.docx.converted.md), 74 bytes; SHA256 `e15dc051e72a6a60efe2383c42dd5f00ceb353e74b16209a8a51cb9e7a42422e`.
DESIGN row **8** -> **ocr-required/awaiting-approval**; reason `None`; units 1.
Native text: `false`; extracted assets: 1.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":1,"candidates_high":1,"candidates_low":0,"media_small":0},"candidates":[{"id":"word/media/image1.png","kind":"image","page":null,"priority":"high","reasons":["embedded_image","scan_like"]}],"issues":[]}
```

### `ocr/image-only.docx` (39106 bytes)

[Input](ocr/image-only.docx) · [raw report](reports/ocr--image-only.docx.json) · [probe](reports/ocr--image-only.docx.probe.json)

Conversion: [exact text](reports/ocr--image-only.docx.converted.md), 71 bytes; SHA256 `6a55d8d1a1fb1375b1a3da75e186e8c74b75174452942b07c0f16996c23c9419`.
DESIGN row **8** -> **ocr-required/awaiting-approval**; reason `None`; units 1.
Native text: `false`; extracted assets: 1.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":1,"candidates_high":1,"candidates_low":0,"media_small":0},"candidates":[{"id":"word/media/image1.png","kind":"image","page":null,"priority":"high","reasons":["embedded_image","scan_like"]}],"issues":[]}
```

### `ocr/photo.png` (4096 bytes)

[Input](ocr/photo.png) · [raw report](reports/ocr--photo.png.json) · [probe](reports/ocr--photo.png.probe.json)

Conversion: [exact text](reports/ocr--photo.png.converted.md), 0 bytes; SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
DESIGN row **3** -> **ocr-required/awaiting-approval**; reason `raster`; units 1.
Native text: `false`; extracted assets: 0.
Direct diagnostic conversion/triage is bypassed by sb’s earlier guard.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":1,"candidates_low":0},"candidates":[{"id":"image","kind":"image","page":null,"priority":"high","reasons":["standalone_image"]}],"issues":[]}
```

### `ocr/scan.pdf` (4035 bytes)

[Input](ocr/scan.pdf) · [raw report](reports/ocr--scan.pdf.json) · [probe](reports/ocr--scan.pdf.probe.json)

Conversion: [exact text](reports/ocr--scan.pdf.converted.md), 0 bytes; SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
DESIGN row **8** -> **ocr-required/awaiting-approval**; reason `None`; units 1.
Native text: `false`; extracted assets: 0.

```json
{"decision":"ocr_recommended","coverage":{"state":"complete","pages_total":1,"pages_inspected":1,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":1,"candidates_high":1,"candidates_low":0},"candidates":[{"id":"p1","kind":"page","page":1,"priority":"high","reasons":["scan_like"]}],"issues":[]}
```

### `peer-output/hostile-instructions.md` (156 bytes)

[Input](peer-output/hostile-instructions.md) · [raw report](reports/peer-output--hostile-instructions.md.json) · [probe](reports/peer-output--hostile-instructions.md.probe.json)

Conversion: [exact text](reports/peer-output--hostile-instructions.md.converted.md), 156 bytes; SHA256 `b433632df8bd016bb8963a514316e3f032624dd41cad926742ac78ed8fbef963`.
DESIGN row **12** -> **unknown/awaiting-approval**; reason `media_not_inspected`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `peer-output/illegible.md` (22 bytes)

[Input](peer-output/illegible.md) · [raw report](reports/peer-output--illegible.md.json) · [probe](reports/peer-output--illegible.md.probe.json)

Conversion: [exact text](reports/peer-output--illegible.md.converted.md), 22 bytes; SHA256 `7215d7c36da7c082b3822c4e004592e7284947b5a44de1b6bd55d3240f82fc37`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `peer-output/u0001.md` (59 bytes)

[Input](peer-output/u0001.md) · [raw report](reports/peer-output--u0001.md.json) · [probe](reports/peer-output--u0001.md.probe.json)

Conversion: [exact text](reports/peer-output--u0001.md.converted.md), 59 bytes; SHA256 `5646de45361b300585cf745f99ed357efba0630531d2802f6c5f18fc5825c349`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.
Peer/LLM adapter data; classification describes hypothetical ingest, not peer-output acceptance.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `text/doc.docx` (35322 bytes)

[Input](text/doc.docx) · [raw report](reports/text--doc.docx.json) · [probe](reports/text--doc.docx.probe.json)

Conversion: [exact text](reports/text--doc.docx.converted.md), 49 bytes; SHA256 `0c546975c3efd6faddad45c138fe8c3d1dd924261880f5652cd8a5b9d8f2957f`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":42,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```

### `text/empty-table.docx` (35396 bytes)

[Input](text/empty-table.docx) · [raw report](reports/text--empty-table.docx.json) · [probe](reports/text--empty-table.docx.probe.json)

Conversion: [exact text](reports/text--empty-table.docx.converted.md), 37 bytes; SHA256 `0bef335d3bbd83efcef6ac78bd2e310d872142d336828a953e2baa0810700695`.
DESIGN row **11** -> **text-only/ready**; reason `empty_document`; units 0.
Native text: `false`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```

### `text/korean-cp949.txt` (48 bytes)

[Input](text/korean-cp949.txt) · [raw report](reports/text--korean-cp949.txt.json) · [probe](reports/text--korean-cp949.txt.probe.json)

Conversion: [exact text](reports/text--korean-cp949.txt.converted.md), 62 bytes; SHA256 `82e881e07445068f86be55d48363df1a6e085c07f45f738e83c3422ba09fb88f`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `text/nfd-이름.txt` (28 bytes)

[Input](text/nfd-이름.txt) · [raw report](reports/text--nfd-이름.txt.json) · [probe](reports/text--nfd-이름.txt.probe.json)

Conversion: [exact text](reports/text--nfd-이름.txt.converted.md), 28 bytes; SHA256 `256d01e0587f2618e0e5fbbd442984022a4b9206511a663d5cbb49397b3e6da5`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"not_applicable","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000},"reason":"Validated plain text has no embedded media to inspect."},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[]}
```

### `text/note.hwp` (3072 bytes)

[Input](text/note.hwp) · [raw report](reports/text--note.hwp.json) · [probe](reports/text--note.hwp.probe.json)

Conversion: [exact text](reports/text--note.hwp.converted.md), 41 bytes; SHA256 `89d6340d2bbe801c6a639ac4855d58bb7d08996fbe13dc852274467c5319d609`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```

### `text/note.hwpx` (1080 bytes)

[Input](text/note.hwpx) · [raw report](reports/text--note.hwpx.json) · [probe](reports/text--note.hwpx.probe.json)

Conversion: [exact text](reports/text--note.hwpx.converted.md), 41 bytes; SHA256 `f03fd6cbd8de9e8d8d79dac5439d5b8101a81c3173298441f56cfc0aff965d75`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":28,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```

### `text/plain.txt` (47 bytes)

[Input](text/plain.txt) · [raw report](reports/text--plain.txt.json) · [probe](reports/text--plain.txt.probe.json)

Conversion: [exact text](reports/text--plain.txt.converted.md), 47 bytes; SHA256 `59c7bcbced49378eac2525e7ae385ea04bfd468e8a8b79ef2652279cd125160b`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"not_applicable","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000},"reason":"Validated plain text has no embedded media to inspect."},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[]}
```

### `text/table.xlsx` (4890 bytes)

[Input](text/table.xlsx) · [raw report](reports/text--table.xlsx.json) · [probe](reports/text--table.xlsx.probe.json)

Conversion: [exact text](reports/text--table.xlsx.converted.md), 67 bytes; SHA256 `d7bea463e2137683fce730f360725341e288d55d3914ed56fca35f5c8c29533e`.
DESIGN row **11** -> **text-only/ready**; reason `None`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000,"max_zip_entries":10000,"max_zip_total_bytes":536870912,"max_zip_read_bytes":16777216,"max_xml_bytes":2097152,"max_media_probe_bytes":65536,"max_media_read_bytes":67108864,"max_media_references":10000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":22,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```

### `unknown/malformed.md` (51 bytes)

[Input](unknown/malformed.md) · [raw report](reports/unknown--malformed.md.json) · [probe](reports/unknown--malformed.md.probe.json)

Conversion: [exact text](reports/unknown--malformed.md.converted.md), 51 bytes; SHA256 `83efde0848c1d128d775cb5976434a9d27a84327cbce1e928c3294f2543d2cda`.
DESIGN row **12** -> **unknown/awaiting-approval**; reason `media_not_inspected`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `unknown/page.html` (112 bytes)

[Input](unknown/page.html) · [raw report](reports/unknown--page.html.json) · [probe](reports/unknown--page.html.probe.json)

Conversion: [exact text](reports/unknown--page.html.converted.md), 51 bytes; SHA256 `cd36fa7db5c27ac78c84cadb0bc7a5b9f41630d367405815b7d4560af6da8ac9`.
DESIGN row **12** -> **unknown/awaiting-approval**; reason `media_not_inspected`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `unknown/with-image.md` (50 bytes)

[Input](unknown/with-image.md) · [raw report](reports/unknown--with-image.md.json) · [probe](reports/unknown--with-image.md.probe.json)

Conversion: [exact text](reports/unknown--with-image.md.converted.md), 50 bytes; SHA256 `089422445444a8e38ddb4c1f934d90647d6450e4b09e2a9257dcb3878a1929ce`.
DESIGN row **12** -> **unknown/awaiting-approval**; reason `media_not_inspected`; units 0.
Native text: `true`; extracted assets: 0.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"media_not_inspected","detail":"Embedded or linked media in this format were not inspected."}]}
```

### `unsupported/clip.mp3` (2085 bytes)

[Input](unsupported/clip.mp3) · [raw report](reports/unsupported--clip.mp3.json) · [probe](reports/unsupported--clip.mp3.probe.json)

Conversion: **FileConversionException**; no converted artifact. See probe for exact message.
DESIGN row **2** -> **unsupported/unsupported**; reason `extension_not_allowed`; units 0.
Native text: `none`; extracted assets: 0.
Direct diagnostic conversion/triage is bypassed by sb’s earlier guard.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `unsupported/data.xyz` (35 bytes)

[Input](unsupported/data.xyz) · [raw report](reports/unsupported--data.xyz.json) · [probe](reports/unsupported--data.xyz.probe.json)

Conversion: **UnsupportedFormatException**; no converted artifact. See probe for exact message.
DESIGN row **2** -> **unsupported/unsupported**; reason `extension_not_allowed`; units 0.
Native text: `none`; extracted assets: 0.
Direct diagnostic conversion/triage is bypassed by sb’s earlier guard.

```json
{"decision":"unknown","coverage":{"state":"none","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0},"candidates":[],"issues":[{"code":"unsupported_format","detail":"Supported formats: PDF, raster, DOCX, PPTX, XLSX, HWPX."}]}
```

### `unsupported/legacy.doc` (2560 bytes)

[Input](unsupported/legacy.doc) · [raw report](reports/unsupported--legacy.doc.json) · [probe](reports/unsupported--legacy.doc.probe.json)

Conversion: **UnsupportedFormatException**; no converted artifact. See probe for exact message.
DESIGN row **2** -> **unsupported/unsupported**; reason `extension_not_allowed`; units 0.
Native text: `none`; extracted assets: 0.
Direct diagnostic conversion/triage is bypassed by sb’s earlier guard.

```json
{"decision":"no_candidates","coverage":{"state":"complete","pages_total":null,"pages_inspected":0,"limits":{"max_bytes":268435456,"max_pages":1000}},"summary":{"scope":"inspected","pages_with_text":0,"nonspace_chars":0,"image_occurrences":0,"candidates_high":0,"candidates_low":0,"media_small":0},"candidates":[],"issues":[]}
```


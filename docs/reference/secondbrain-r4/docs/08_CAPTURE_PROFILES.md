# 08. Capture Profiles

## 공통 원칙

모든 profile:
- original bytes 보존
- original filename 기록
- size
- MIME/type detection
- SHA-256/SHA-512
- acquisition source
- acquired_at
- collector
- derived extraction은 원본과 분리

---

## PDF / Office documents

Original:
- 원래 파일

Derived:
- text extraction
- page images
- OCR
- normalized PDF (필요 시)
- Markdown

금지:
- OCR 결과를 원본 PDF에 덮어쓰기
- 제출용 병합본을 원본으로 대체

---

## Email

가능하면 Original:
- `.eml` 또는 표준 mailbox export
- attachments 원본

보존 후보:
- Message-ID
- Date
- From/To/Cc
- Received headers
- MIME tree
- attachment filename/hash

Derived:
- rendered PDF
- body Markdown
- header summary

PDF 출력본만 보유한 경우 해당 사실을 Observation에 기록한다.

---

## Photo

Original:
- 기기에서 얻은 원 파일

Extract:
- EXIF JSON
- GPS raw tags
- camera/model
- DateTimeOriginal
- orientation

Derived:
- preview
- annotated copy
- production PDF

EXIF 값과 사람이 검증한 지리 위치는 tier를 분리한다.

---

## Video / Audio

Original:
- source media

Extract:
- ffprobe metadata
- codec/duration
- embedded timestamps

Derived:
- transcript
- normalized audio
- frame captures
- waveform/spectrogram

transcript는 원본이 아니다.

---

## Messenger / SMS

우선순위:
1. native export
2. database/export package
3. conversation export
4. screenshot
5. 수기 전사

가능하면:
- participant identifiers
- export method
- device/app version
- conversation range
- timezone
를 보존.

screenshot만 있다면 그 한계를 metadata에 기록한다.

---

## Web

권장:
- URL
- captured_at
- response/render context
- HTML
- full screenshot
- PDF
- WARC (가능한 경우)

WARC를 사용하지 못해도 URL + timestamp + raw HTML/screenshot을 남긴다.

---

## Cloud file

Cloud 자체가 원출처인지 ingest channel인지 구분한다.

예:
```text
source_type = email
ingest_channel = onedrive-folder
```

provider API를 요구하지 않는다.

---

## Physical document

논리 구조:
```text
physical original
  -> digitization event
  -> scanned file evidence object
```

기록:
- physical original 존재 여부
- 보관 위치
- scan operator
- scan device/settings
- pages/sides
- scan timestamp

scan은 물리적 원본 그 자체라고 표현하지 않는다.

---

## Device / Forensic image

ERL-5 영역.
Second Brain은 forensic imaging tool을 대체하지 않는다.

외부 도구 결과:
- image file
- tool report
- acquisition metadata
- image hash
를 Evidence Object로 보존한다.

## R2 source-fidelity override
먼저 확보한 파일을 Inbox에 넣는 사실 자체를 original creation으로 오인하지 않는다. EML/메신저/웹/사진/종이: 원출처의 정보 획득 가능 범위와 누락을 provenance grade에 표시. `docs/18_DATA_CONTRACTS.md`, `docs/26_EVIDENCE_EXPORT.md` 참고.

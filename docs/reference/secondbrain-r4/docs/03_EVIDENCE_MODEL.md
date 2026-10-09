# 03. Evidence Domain Model

## 1. 핵심 Entity

### EvidenceObject
실제 bytes의 canonical representation.

핵심:
- `object_id`
- `sha256`
- `sha512`
- size
- media type
- vault payload location
- sealed timestamp

### EvidenceRecord
사람이 사건/프로젝트에서 다루는 논리적 증거 단위.

핵심:
- `evidence_id`
- 대표 object
- title
- status
- classification
- ERL

### Observation
동일 Object가 언제/어디에서/어떻게 관찰·입수되었는지.

예:
- 이메일 첨부에서 발견
- USB에서 다시 발견
- Google Drive 폴더에서 별도 발견

동일 bytes라도 Observation은 별개다.

### AcquisitionEvent
수집 행위 자체의 기록.

### CustodyEvent
인수, 봉인, 복제, 검증, export, production 등 보관/처리 이력.

### Derivation
원본에서 파생 artifact가 만들어진 관계.

### LegalHold
삭제/교체가 금지된 matter-level 정책.

---

## 2. Fact provenance tier

```text
OBSERVED
  시스템/사람이 직접 관찰한 것

EXTRACTED
  파일 내부 metadata/header에서 도구가 읽은 값

ASSERTED
  작성자/제공자/외부 source가 주장한 값

INFERRED
  사람이거나 AI가 정황을 바탕으로 추론한 값

VERIFIED
  별도 검증 절차를 통해 확인된 값
```

예:

```yaml
field: capture_location
value: "아산시 탕정면 ..."
tier: VERIFIED
source:
  - exif:GPSLatitude
  - exif:GPSLongitude
verification:
  method: map-coordinate-match
  actor: human:...
```

---

## 3. Temporal fact

변경 가능한 사실은 덮어쓰지 않고 시간축을 가진다.

```yaml
observed_at: 2026-10-03T00:00:00+09:00
valid_from: 2026-10-01
valid_until: null
recorded_at: 2026-10-03T00:01:00+09:00
```

---

## 4. Lineage

```text
Original JPG (EV-001)
   |
   +-- EXIF extraction.json
   |
   +-- preview.jpg
   |
   +-- production/exhibit-03.pdf
   |
   +-- knowledge/location-analysis.md
```

모든 파생물은 다음을 가져야 한다.

- parent evidence/object
- transform type
- tool
- tool version
- parameters digest
- created_at
- output digest
- actor

---

## 5. Evidence Readiness Level

### ERL-0 — Reference only
- 임시 참고
- 원본/출처 보존 미보장

### ERL-1 — Fixity
- 원본 bytes
- SHA-256
- 최소 identity

### ERL-2 — Acquisition
- ERL-1
- source
- acquired_at
- acquisition method
- collector/actor
- original filename

### ERL-3 — Preserved
- ERL-2
- SHA-512
- custody journal
- verified manifest
- secondary verified snapshot 존재
- canonical original/working/production 분리

### ERL-4 — Externally Anchored
- ERL-3
- trusted external timestamp 또는 서명된 external receipt

### ERL-5 — Forensic Acquisition
- 전문 forensic acquisition
- device/image/tool-specific record
- R1 Second Brain 자체 구현 범위 밖
- 외부 forensic 결과를 evidence object로 보존

기본 목표: **ERL-3**
중요 표시된 evidence: **ERL-4 선택 가능**

---

## 6. 삭제 의미

`delete`는 세 가지로 구분한다.

1. `discard_inbox` — 아직 Evidence로 봉인되지 않은 입력
2. `retire_derived` — 재생성 가능한 derived artifact
3. `destroy_evidence` — canonical evidence 제거

`destroy_evidence`는 기본 CLI에서 일반 삭제와 분리하고, Legal Hold 확인, dry-run, 명시적 apply, audit event를 요구한다.

## R2 authoritative changes
Object에는 직접 입력 가능한 ERL을 쓰지 않는다. ERL-3은 backup independent verify를 통과한 뒤 계산되는 view 값이다. Object/Record/Observation의 식별·관계/시간 의미는 `docs/18_DATA_CONTRACTS.md`가 기준이며 `schemas/v2`를 적용한다.

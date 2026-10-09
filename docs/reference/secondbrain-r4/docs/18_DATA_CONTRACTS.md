# 18. Evidence/Meta Data Contracts — R2

## Model boundaries (MECE)
- **Object:** 특정 byte sequence (SHA-256 identity), binary Vault 한 개. 개별 사건 의미·작성 주장 없음.
- **Evidence Record:** 사용자/사건 맥락에서 참조하는 증거 단위. `object_id`를 참조하는 여러 record 가능.
- **Observation:** 파일을 어디서, 언제, 누가 발견/입수했는가. 동일 byte의 다른 취득 경위는 별도 Observation.
- **Acquisition:** 특정 Observation을 실제 수집한 방식/사용 도구/시작·종료/오류 등.
- **Custody Event:** 시스템 내 복제·검증·이전·봉인·제출 등 처리/보관 이력.
- **Claim / Assertion:** 원본에 *무엇이 적혀 있는가*, *누가 주장했는가*, *무엇을 추론했는가*와 *무엇이 검증됐는가*를 명시적으로 분리.
- **Derivation:** byte/텍스트/판단/이미지/제출물 변형, 입력 URI와 도구/설정/출력 digest를 함께 기록.
- **Production:** 제출용 assembly. 원본, 발췌 범위(page/time/page-label), 순서, redaction, 제출 hash, 생성자 기록.
- **Hold:** 파기 금지 범위/책임자/발효일/해제 승인과 이벤트를 가짐.
- **Snapshot:** 완성·검증·복원 가능 기준점. snapshot 존재만으로 ERL-3을 부여하지 않는다.

## Integrity / provenance invariants
- URI: `brain://evidence/<id>` 또는 `brain://object/<digest>`; canonical identity에 물리 드라이브 문자를 저장하지 않음.
- Object raw bytes의 원본 생성자 또는 정확한 원생성일은 **수집만으로 알 수 없음**. 출처 추적 신뢰등급 필드 별도.
- `source_type`(원출처), `ingest_channel`(들어온 매체), `acquisition_method`(복사/내보내기 방식) 별개.
- 서로 다른 시간: `source_claimed_at`, `source_fs_time`, `first_seen_at`, `capture_started_at`, `capture_completed_at`, `recorded_at`, `verified_at`, `valid_from`, `valid_until` (알 수 없음 허용).
- Timestamp 문자열은 RFC3339 offset 명시, UTC instant로 정렬; offset 보존. *스키마의* `format`만 믿지 말고 활성화된 FormatChecker 및 application semantic checks를 필수화.
- original filename, MIME label은 untrusted text; 실행/열람 시 sanitizer, content sniff, AV sandbox 정책 필요.
- `erl`은 증거 객체가 자체 주장하는 절대값이 아니라 **검증 receipt로 계산되는 read model**. `ERL-3`=소스+hash+custody+독립 검증 snapshot까지 통과한 경우. `ERL-4` 외부 receipt 유효성 검증; `ERL-5`에는 전문 acquisition report link 필수.

## Canonical serialization
- `schemas/v2/*`는 **JSON Schema Draft2020-12**. `$id`는 offline URN, 스키마 registry로 로컬 해석.
- hash-chained JSON event는 RFC8785 JCS + UTF-8. object field 허용/null 의미/숫자 처리 규약을 코드에서 고정; 임의 floating-point 금지. 날짜 time strings는 offset 필수.
- 이벤트는 `stream_id`, `sequence`, `previous_event_hash`, `event_hash`, `event_at`, `actor`, `event_type`, `target_uri`, `details` 포함. `sequence=1` 첫 이벤트 prev=null, 후속 `sequence=n` prev는 `n-1`의 검증 hash.
- 이벤트의 **발행 시점과 검증 시점**을 구별; suffix journal 재작성 금지. 조작에 대한 외부 독립 검증은 snapshot anchor로 보강.
- 각 JSON canonical record 변경은 이벤트를 생성하고 새 버전/스냅샷으로 표현; 기록 내용의 silent overwrite 금지.

## Media/source provenance granularity
- Office/PDF: native file; embedded attachments, digital signature flags, page count / annotations, container hash.
- Photo/AV: EXIF/codec/timestamps *extracted* / GPS 판독과 위치 *검증*은 별개.
- Email: raw EML/MBOX/MIME byte와 header + 첨부 파생 관계; 메일 헤더만으로 발신자 신원 보증 불가.
- Chat/Web/SNS: URL/계정/언제 어떤 계정으로 봤는지/capture method/연속성·누락/캡처의 한계; 웹 HTML이 동적 결과를 전부 보존하지 못할 수 있음.
- 종이자료: 물리적 보관위치/스캔 장비/양면/누락페이지 확인; scan != 물리원본.
- 원본이 이미 가공된 screenshot/PDF 뿐인 경우 `source_fidelity`는 스키마 v2의 `native_obtained | exported | rendered | screenshot_only | unknown`만 사용한다. 불확실할 때는 `unknown`; 출처 사실을 모른 채 `native_obtained`로 올려 쓰지 않는다.

## schema v1 → v2 compatibility
- R1 입력 schema (`schemas/v1`)를 변경하지 않음. R2에서는 `schemas/v2`가 신규 canonical data 생성 기준.
- v1 migration: **원본 v1 자체도 보존**, mapper와 mapping report 제시. 누락 필드는 추정하지 않고 null/unknown 또는 사용자 재확인. `backfill` 시 수집시점 재구성 불가한 사실을 fabricated timestamp로 채우지 않는다.
- v2 schema validation과 참조 무결성 cross-check가 모두 PASS해야 sealed read model 승격.

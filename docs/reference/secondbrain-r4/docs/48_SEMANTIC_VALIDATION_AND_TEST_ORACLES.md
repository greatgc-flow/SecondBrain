# 48. 의미적 검증 계약 — 구조적 스키마 PASS와 운영 PASS 분리

**경계**: JSON Schema는 각 문서의 형식; semantic validator는 문서 내부의 필드 간·문서 간·실파일 간·시간에 따른 consistency. 원본 파일은 SHA256 외에도 SHA512/크기, 복사 전후 재읽기, provenance 기록이 맞아야 함. 모든 오라클은 TDD RED의 독립 기대값으로 사용한다.

## 1. 필수 승격 규칙
1. `STRUCTURE_VALID`은 *입력 파싱+JSON Schema 검증*만 의미. `SEMANTIC_VALID`은 cross-field, cryptographic, référential, state/event temporal 검증까지 통과. `FIELD_VERIFIED`은 실제 독립 실패 도메인/운영자 증거까지 있음.
2. `evidence-object`: `object_id == 'obj-sha256-'+sha256`, `vault_relpath`의 두 prefix 디렉터리와 full digest = sha256. 실제 payload를 독립 재해시할 때 SHA256/SHA512/size가 일치해야만 VERIFIED. `sha256` 필드나 UUID가 도메인 사실의 진실을 입증하지는 않음.
3. `capture`: `(device_id,capture_id)` 고유. 같은 키+상이한 hash는 quarantine. 파일 상태가 안정화되어도 복사 중 source 변경이 가능하므로 해시/파일 식별자 복사 전후 일치하고 staging 재해시 필수. 불확실하면 `SOURCE_CHANGED`.
4. `commit`: 모든 참조 개체 ID 존재, schema-valid, payload seal verify, 선행 custody stream valid, writer epoch 현재값, commit receipt verified. receipt 파일 존재만으로 publish 성공 처리 금지.
5. `custody/feedback`: duplicate JSON keys 거부; 유효 Unicode/I-JSON 범위 및 RFC8785 JCS와 digest 비교; `sequence=1` ↔ previous=null, n>1 previous=verified hash n-1; hash 는 `event_hash` 제외한 JCS 객체 SHA256. sequence gap/duplicate/time rollback/unauthorized actor/quarantine 모두 fail closed. 실제 anchor의 독립보관/시각증명은 별도 수동 또는 cryptographic verification.
6. `backup`: `verification_status=PASS`에는 동일한 source/target manifest hashes, 전체 payload 목록+각 byte 검증, file_count/total_bytes/보존경계 일치, 단일 point-in-time source consistency, 타 failure-domain 확인이 모두 필요. `files_checked=0` PASS 금지(명시적 빈 snapshot만 예외; 원본 evidence backup ERL3에 사용 금지). `sync_state=unverified`는 클라우드 독립 copy success로 승격 금지.
7. `hold`: ACTIVE에서 RELEASED는 authorized event/reason/time/scope 확인. 동일 matter의 신규 Evidence, derivative, Production, backups/index/retention policy에 propagation 점검. 삭제 가능 시점은 active hold, data-subject/legal obligation 모두 확인. 누락/상충 시 보류.
8. `production`: 모든 evidence ID, object ID, digest, page/timecode/source labeling, redaction, 원본 표시 및 omission claims에 대한 실제 독립 검증 필요. **BagIt valid**는 RFC8493 complete+checksums 모두 만족한 경우에만; 외형만 BagIt인 디렉터리는 아직 `DRAFT`.
9. `memory`: 원본/source/ACL/tenancy/reliability 상태를 그대로 전파. denied evidence는 ranking/LLM prompt/embedding/cache/telemetry로 유출 금지. `fact-assertion`은 인용과 시간적 효력을 구분; unsupported claim 은 abstain 또는 유보.
10. `release`: 모든 Gate receipt는 동일 candidate fingerprint, 동일 config/deps/test corpus, 부정/복구 경로 실측; `WAIVED`는 required Gate PASS가 아님. 운영 관측 효과가 없는 변경은 feedback `CLOSED` 금지.

## 2. Cross-schema 검증의 책임
- 구조 파서: **스키마 + format checker + duplicate-key rejection**
- 메타/관계 검사: identity, ID refs, unique links, actor/ACL, timeline, matter/hold
- 바이트 검사: 실제 해시, 크기, zip/package validation, symlink/hardlink/ADS/reparse attack
- Event/commit 검사: JCS, event seq, signer/anchor, writer epoch, finalized receipt
- 외부/수동 확인: source acquisition legality, provider UI/cloud upload, timestamp TSA, media authenticity, independent restore

## 3. RFC 8785 구현 지침
`json.dumps(sort_keys=True)`를 *일반적으로* RFC8785 구현이라고 부르지 않는다. property 이름 순서는 UTF-16 code-unit 기준이며 NaN/Infinity, JSON 중복 키, 정밀도/숫자 표현, Unicode 변환을 제약한다. 언어 독립 테스트 벡터를 정하고 Python/JS 연산 결과의 동일성을 검증한다. 샘플 `custody-event.valid.json`의 `event_hash`는 구조 파싱용 placeholder이며 **해시 검증에 통과하는 예제라고 주장하지 않는다**. TDD에서는 `event_hash`까지 실제 계산한 별도 fixture를 만든다.

## 4. 독립 부정 사례
`quality/R4_SEMANTIC_TEST_ORACLES.csv`에 각 반례·예상 거절 사유·연계된 기존 requirement IDs 및 G2~G7 검증단계를 배정했다. 모두 TDD 실행 전 `PLANNED_NOT_RUN`; `quality/R4_SCHEMA_LIMITATION_PROBES.json`의 `schema_accepts`는 **취약 행위가 Schema만으로 차단되지 않음**을 뜻하며 제품 실행 결과가 아니다.

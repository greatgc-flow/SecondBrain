# 01. 요구사항 명세

## 1. 범위

### In Scope
- 일반 파일시스템 기반 Second Brain
- Evidence-ready Inbox
- Evidence Vault / Working / Production 분리
- 원본 hash와 provenance
- Chain of Custody
- Legal Hold
- Knowledge / Context / Memory
- OneDrive/Google Drive 동기화 폴더 사용
- Primary + Secondary Snapshot
- Obsidian 표시
- MCP read/write 경계
- PeerHub AI 검토/합의 연계
- Engram portable runtime 연계
- 재생성 가능한 local search/vector index

### Out of Scope (R1)
- OneDrive/Google Drive API
- OAuth 기반 cloud integration
- 휴대폰/디스크 forensic imaging 자체 구현
- WORM storage 제품 구현
- 전자서명/공인 TSA 사업자 자체 구현
- 법적 증거능력 자동 판정
- Graph DB를 SSOT로 사용
- 클라우드 동기화 엔진 자체 개발

---

## 2. MUST

### Storage / SSOT
- **REQ-STO-001** Second Brain core는 일반 파일시스템 root만 알아야 한다.
- **REQ-STO-002** cloud provider별 API에 의존하지 않아야 한다.
- **REQ-STO-003** 모든 canonical record는 개방형 파일(JSON/JSONL/Markdown/binary/manifest)로 보존한다.
- **REQ-STO-004** SQLite/vector/FTS/cache는 SSOT가 아니며 전부 재생성 가능해야 한다.
- **REQ-STO-005** 동일 live tree를 두 cloud sync engine이 동시에 관리하도록 설계하지 않는다.
- **REQ-STO-006** Primary sync storage와 Secondary snapshot backup을 구분한다.
- **REQ-STO-007** Evidence payload는 verify 시점에 실제 local bytes로 접근 가능해야 한다.

### Evidence
- **REQ-EVD-001** 수집된 원본 바이트는 봉인 후 직접 수정하지 않는다.
- **REQ-EVD-002** 모든 Evidence Object에 안정적 `evidence_id`와 content digest를 부여한다.
- **REQ-EVD-003** SHA-256을 필수 digest로 사용한다.
- **REQ-EVD-004** SHA-512를 추가 digest로 기본 사용한다.
- **REQ-EVD-005** original filename과 canonical object identity를 분리한다.
- **REQ-EVD-006** Object와 Observation을 분리한다.
- **REQ-EVD-007** 같은 bytes가 여러 출처에서 관찰되면 Object는 재사용하고 Observation은 추가한다.
- **REQ-EVD-008** 모든 파생물은 `derived_from` lineage를 가진다.
- **REQ-EVD-009** Working/Production 산출물은 Evidence Vault 원본과 분리한다.
- **REQ-EVD-010** redaction/ocr/markdown/pdf merge/rename/page-numbering은 모두 파생 연산으로 취급한다.
- **REQ-EVD-011** capture 당시 source context와 ingest channel을 분리해 기록한다.
- **REQ-EVD-012** 수집 이후 metadata 수정은 event로 남기고 과거 값을 추적 가능하게 한다.
- **REQ-EVD-013** Evidence 관련 canonical event는 append-only 논리를 따른다.
- **REQ-EVD-014** custody event는 actor/time/action/reason/previous-event 관계를 가져야 한다.
- **REQ-EVD-015** custody journal은 hash chain으로 사후 변경 탐지가 가능해야 한다.
- **REQ-EVD-016** original verification은 manifest와 현재 bytes의 digest를 비교해야 한다.
- **REQ-EVD-017** 중요한 evidence는 Legal Hold 상태로 삭제/교체를 차단할 수 있어야 한다.
- **REQ-EVD-018** Evidence Vault의 원본과 제출용 Production을 1:1 lineage report로 설명할 수 있어야 한다.

### Ingest
- **REQ-ING-001** file watcher 감지 즉시 ingest하지 않고 안정화 단계를 둔다.
- **REQ-ING-002** cloud placeholder/미완료 download/복사 중 파일을 READY로 판정하지 않는다.
- **REQ-ING-003** ingest는 중복 실행되어도 canonical object가 손상되지 않는 idempotent 구조여야 한다.
- **REQ-ING-004** 동일 object write 경쟁 시 temp-write + verify + atomic publish 원칙을 사용한다.
- **REQ-ING-005** 실패 시 원본 Drop 파일을 임의 삭제하지 않는다.
- **REQ-ING-006** 처리 실패는 Quarantine으로 분기하고 실패 이유를 기록한다.

### Knowledge / Memory
- **REQ-KNW-001** Evidence 원본, Knowledge, Context, AI Memory를 논리적으로 분리한다.
- **REQ-KNW-002** AI-generated note는 source evidence와 generator 정보를 기록한다.
- **REQ-KNW-003** OBSERVED / EXTRACTED / ASSERTED / INFERRED / VERIFIED를 구분한다.
- **REQ-KNW-004** 사실이 시간에 따라 바뀌는 경우 `valid_from`, `valid_until`, `observed_at`을 지원한다.
- **REQ-KNW-005** Memory/search index 삭제 후 canonical files에서 rebuild 가능해야 한다.

### AI / PeerHub
- **REQ-AI-001** acquisition/hash/seal/manifest는 deterministic code가 담당해야 한다.
- **REQ-AI-002** AI는 원본 capture의 신뢰 근거가 되어서는 안 된다.
- **REQ-AI-003** PeerHub에는 원본 binary를 저장하지 않고 stable URI/reference만 전달한다.
- **REQ-AI-004** AI가 내린 판단은 Evidence와 분리하여 provenance를 남긴다.
- **REQ-AI-005** destructive write/promote는 policy와 승인 경계를 가져야 한다.

### Security / Operations
- **REQ-OPS-001** secret/token을 canonical metadata에 평문 저장하지 않는다.
- **REQ-OPS-002** primary root는 사용자 설정값이며 하드코딩하지 않는다.
- **REQ-OPS-003** tool path/version 역시 config/catalog로 관리한다.
- **REQ-OPS-004** 정기 full integrity verify를 지원해야 한다.
- **REQ-OPS-005** snapshot backup은 manifest 검증 완료 후 성공으로 기록한다.
- **REQ-OPS-006** restore는 destructive apply 전 dry-run을 제공해야 한다.
- **REQ-OPS-007** 로그에 sensitive content 전문을 기본 기록하지 않는다.

---

## 3. SHOULD

- **REQ-SHD-001** OneDrive 사용 시 Evidence/Meta를 `Always keep on this device`로 유지한다.
- **REQ-SHD-002** Google Drive 사용 시 Primary는 Mirror mode를 권장한다.
- **REQ-SHD-003** Secondary cloud에는 live two-way mirror 대신 dated snapshot을 둔다.
- **REQ-SHD-004** 중요 증거에는 RFC 3161 TSA token을 선택적으로 부착한다.
- **REQ-SHD-005** export package는 BagIt-compatible 구조를 지원한다.
- **REQ-SHD-006** 월 1회 이상 전체 fixity verification을 수행한다.
- **REQ-SHD-007** 오프사이트/오프라인 사본을 추가할 수 있어야 한다.
- **REQ-SHD-008** CLI 출력은 기본적으로 사람 읽기 좋은 형식, `--json`은 machine-readable 형식으로 제공한다.
- **REQ-SHD-009** schema version migration을 명시적으로 관리한다.
- **REQ-SHD-010** Obsidian은 SSOT DB가 아닌 Markdown/metadata frontend로 사용한다.

---

## 4. MAY

- **REQ-MAY-001** WARC 기반 웹 캡처
- **REQ-MAY-002** signed manifest
- **REQ-MAY-003** Graph index
- **REQ-MAY-004** local embedding model
- **REQ-MAY-005** external TSA provider
- **REQ-MAY-006** filesystem ACL/read-only 강화
- **REQ-MAY-007** hardware/offline vault backup

---

## 5. MUST NOT

- **REQ-NOT-001** Vault 원본을 OCR/정리 과정에서 overwrite하지 않는다.
- **REQ-NOT-002** cloud version history만을 backup으로 간주하지 않는다.
- **REQ-NOT-003** cloud-synced SQLite/vector store를 multi-device authoritative DB로 사용하지 않는다.
- **REQ-NOT-004** filesystem creation time만으로 original creation time을 단정하지 않는다.
- **REQ-NOT-005** AI 추론을 EXIF/header 등 직접 관찰 metadata와 같은 factual tier로 합치지 않는다.
- **REQ-NOT-006** Legal Hold 중 canonical evidence를 일반 삭제 경로로 제거하지 않는다.
- **REQ-NOT-007** 동일한 primary folder를 OneDrive와 Google Drive가 동시에 live-sync하도록 기본 설계하지 않는다.

---
## 6. R2 추가 MUST / MUST NOT (2026-10-09)

아래 REQUIREMENT들은 R1을 삭제하지 않고 확장한다. R1과 충돌하면 `docs/31_REQUIREMENT_AMENDMENTS.md`가 우선한다. 모든 요건은 `traceability/requirements_to_tests.csv`에 개별 대응.

### SYNC
- **REQ-SYNC-001** SSOT canonical writes는 한 시점에 지정된 Writer 한 기기에서만 수행한다.
- **REQ-SYNC-002** 그 외 기기는 장치별 불변 capture 폴더에 자료를 추가하고 canonical record를 수정하지 않는다.
- **REQ-SYNC-003** device_id와 capture_id는 idempotency key를 구성한다.
- **REQ-SYNC-004** 동일 capture key의 서로 다른 payload는 충돌로 격리한다.
- **REQ-SYNC-005** Writer 변경은 중단·backup·동기화 확인·승인·epoch 증가 후에만 수행한다.
- **REQ-SYNC-006** Writer가 아닌 기기의 legacy write attempt는 거부·기록한다.
- **REQ-SYNC-007** Cloud 동기화 완료와 로컬 파일 publish 완료를 서로 구별한다.
- **REQ-SYNC-008** split-brain 가능성이 감지되면 전역 mutation을 정지하고 수동 reconciliation한다.
- **REQ-SYNC-009** 동일 파일을 여러 기기에서 관찰했을 때 Observation을 보존하면서 Object만 dedup한다.
- **REQ-SYNC-010** conflicted copy는 자동 최신본 선택/삭제/덮어쓰기하지 않는다.
### TXN
- **REQ-TXN-001** 수집 source의 현재 바이트는 staging copy와 독립 검증을 통해 봉인한다.
- **REQ-TXN-002** seal/commit 전 source가 변하면 SOURCE_CHANGED로 실패한다.
- **REQ-TXN-003** Vault publish와 record publish는 다중 파일 atomic transaction으로 가정하지 않는다.
- **REQ-TXN-004** logical commit receipt 전에는 Evidence를 INDEXABLE/SEALED로 공개하지 않는다.
- **REQ-TXN-005** 크래시 후 partial/orphan을 안전하게 판별하여 이어가거나 fail-closed 한다.
- **REQ-TXN-006** ingest failure 시 유일한 원본 Drop은 절대 자동 삭제하지 않는다.
- **REQ-TXN-007** 중복 시도 retry는 이미 발급된 Observation/Acquisition ID를 재사용한다.
- **REQ-TXN-008** content address가 동일하나 기존 bytes가 다르면 overwrite 없이 경고한다.
- **REQ-TXN-009** snapshot restore는 원래 root를 먼저 보존하고 별도 경로에서 검증한다.
- **REQ-TXN-010** timestamp 및 host clock offset/불확실성은 데이터 생성시각으로 승격하지 않는다.
### SCH
- **REQ-SCH-001** 신규 canonical record는 schemas/v2만을 사용하고 v1 원본 records는 보존한다.
- **REQ-SCH-002** JSON Schema 검증 외 FormatChecker와 도메인간 참조 무결성 검사를 수행한다.
- **REQ-SCH-003** UUIDv7을 기본 ID 규격으로 사용하고 충돌 검사/재발급한다.
- **REQ-SCH-004** Object digest ID와 논리 Evidence ID 및 Observation ID를 혼동하지 않는다.
- **REQ-SCH-005** event hash는 RFC8785 JCS canonical UTF-8 bytes를 대상으로 한다.
- **REQ-SCH-006** event stream은 stream_id·sequence·previous_event_hash의 단조 순서를 가진다.
- **REQ-SCH-007** 기존 이벤트의 수정 또는 fork가 검출되면 fail-closed와 독립 anchor 대조를 수행한다.
- **REQ-SCH-008** ERL은 기본 값으로 주장하지 않고 증빙 receipt로 계산한다.
- **REQ-SCH-009** ERL-3은 secondary snapshot independent verify의 증빙 없이는 부여하지 않는다.
- **REQ-SCH-010** 원출처 정보가 없으면 null/unknown으로 남기며 획득·생성 당시 시각을 추정하지 않는다.
### SEC
- **REQ-SEC-001** AI에 입력되는 웹/메일/PDF 문서는 untrusted content로 취급한다.
- **REQ-SEC-002** 민감 정보의 외부 AI 전송은 목적·자료·대상·기간을 지정한 human approval 없이는 기본 차단한다.
- **REQ-SEC-003** 모든 brain URI read/search는 actor scope/자료 민감도 policy 확인 후 결과를 반환한다.
- **REQ-SEC-004** 아카이브 경로 traversal, junction, symlink, 압축 폭탄 방어를 intake 전에 수행한다.
- **REQ-SEC-005** 파일명·MIME·확장자·메타 문자열에 대해 무조건 신뢰하지 않는 parser boundary를 둔다.
- **REQ-SEC-006** 로그·캐시·AI transcript·index에 의한 민감정보 재노출을 방지한다.
- **REQ-SEC-007** active Legal Hold 범위에는 새 연관 Evidence까지 hold propagation을 수행한다.
- **REQ-SEC-008** 삭제/복원/공유/외부 AI 전송은 권한검사를 우회하는 경로가 없어야 한다.
- **REQ-SEC-009** TSA·외부 서명은 구현/검증이 수행된 경우에만 검증됨 상태로 보고한다.
- **REQ-SEC-010** Hold release와 원본 파기에는 명시적 승인 및 별도 감사 이벤트가 필수다.
### BKP
- **REQ-BKP-001** snapshot은 commit receipt 기준 일관된 canonical 집합만 포함한다.
- **REQ-BKP-002** snapshot complete는 secondary bytes 전체 검증 뒤에만 기록한다.
- **REQ-BKP-003** cloud upload completion을 local backup verification과 구별한다.
- **REQ-BKP-004** restore dry-run은 손실/충돌/보관정책/공간 요구를 가시화한다.
- **REQ-BKP-005** restore는 기존 root를 덮어쓰지 않고 검증된 새 root를 만든다.
- **REQ-BKP-006** 백업 보존 기간/폐기 정책과 Legal Hold 충돌을 평가한다.
- **REQ-BKP-007** 대상 snapshot의 corruption이나 manifest 누락을 fail-closed로 처리한다.
- **REQ-BKP-008** 복원 후 index는 canonical sources에서 재생성되고 관계/검증 상태를 확인한다.
### RET
- **REQ-RET-001** retrieval answer의 모든 사실 주장은 구체 Evidence 위치/시간 범위까지 연결되어야 한다.
- **REQ-RET-002** 출처나 권한이 부족하면 결과를 보류하거나 불확실함을 명시한다.
- **REQ-RET-003** AI 기억은 evidence-기반 derived 자료이며 source 없는 진실값을 승격하지 않는다.
- **REQ-RET-004** 변경되는 fact는 recorded/observed/valid time을 구분해 갱신한다.
- **REQ-RET-005** 파생 검색 인덱스는 삭제 후 동일 canonical data에서 논리적 재생성이 가능하다.
- **REQ-RET-006** 검색 권한 필터를 랭킹 이전에 적용하고 source leakage를 막는다.
### INT
- **REQ-INT-001** Core는 Engram/PeerHub/MCP/Obsidian 없이 사용할 수 있어야 한다.
- **REQ-INT-002** PeerHub의 2026-10-09 Core/Extension 경계를 어기는 기존 v0 Core API에 의존하지 않는다.
- **REQ-INT-003** PeerHub에는 원본 binary보다 제한된 evidence reference만 전달한다.
- **REQ-INT-004** MCP network endpoint는 별도 승인 전 로컬 전송만 허용한다.
- **REQ-INT-005** External integration error는 Evidence SSOT commit을 훼손하지 않는다.
- **REQ-INT-006** CLI의 dry-run/read는 destructive side effects를 가지지 않는다.

### R2 independent snapshot addendum
- **REQ-BKP-009** snapshot은 source tree의 point-in-time 일관성을 quiesce/source-rehash 또는 파일시스템 snapshot proof로 검증해야 한다.
- **REQ-BKP-010** ERL-3용 독립 verified snapshot은 Primary와 상이한 장애영역의 사본임을 증빙해야 한다.

## R3 lifecycle extension (authoritative)
TDD 이후 운영·릴리스·지속개선의 추가 요구사항은 `docs/34_LIFECYCLE_REQUIREMENTS.md` 및 `traceability/requirements_to_tests.csv`에 수록한다. 기존 R1/R2 ID는 불변; 충돌 시 `docs/32_NORMATIVE_INDEX_AND_DECISIONS.md`의 우선순위를 따르며, '설계 완료'와 '실제 테스트 PASS'를 구분한다.

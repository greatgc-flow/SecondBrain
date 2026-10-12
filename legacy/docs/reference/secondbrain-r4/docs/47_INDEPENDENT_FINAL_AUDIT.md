# 47. R4 독립 최종감사 — 설계 완전성·추적성·표준·현실성

기준: 2026-10-09, R3 ZIP(archive) + 실제 R3 파일 219개 + 공식 원문/공개 저장소 확인. **설계 검토이지 제품 검증이 아니다.** R4는 R3의 모든 요구사항 ID 188개와 schemas/v2 14종, governance/v1 8종을 보존한다.

## 평정 규칙
- **P0**: 구현/릴리스 오판, 증거 오염 또는 보안 유출로 이어질 수 있어 TDD 전에 반드시 수락 기준을 확정.
- **P1**: 초기 제품의 의미적 정확성·사용 가능성·통합 운영을 위해 TDD 내에 검증.
- **P2**: 유지보수·표현 정리로 독립 배포를 막지는 않음.
- 해소 상태는 `SPECIFIED`(명세 확정), `STATICALLY_CHECKED`(파일 검사), `IMPLEMENTED`(구현), `FIELD_VERIFIED`(실증)로 분리. 아직 마지막 두 상태는 전부 **NOT RUN**.

| ID | 관찰 증거/원인 | 중요도 | R4 조치 | TDD/실증 미종결 조건 |
|---|---|---|---|---|
| A01 | R3 static audit의 188개 planned test id는 `TC-`+요구사항 ID를 생성한 식별자일 뿐 명세문/실행시험이 아님 | P0 | `48`, `quality/R4_SEMANTIC_TEST_ORACLES.csv`에 입력·반례·예상 결과·소유 게이트 추가 | 모든 MUST 계약의 RED/GREEN/실행 결과가 commit-bound여야 G2 허용 |
| A02 | JSON Schema 구조 검증은 `object_id`/SHA-256/path 같은 서로 다른 필드의 의미적 일치 보증 못함 | P0 | domain semantic validator 필수, 반례 실측 JSON 포함 | 가짜 `valid` 조합 거절 |
| A03 | backup verification은 `PASS`·해시 불일치·`files_checked=0`도 스키마가 허용 | P0 | PASS 승격 규칙 및 음성 fixture | 실바이트 전량 검증/manifest/소스 일관성 없는 PASS 차단 |
| A04 | custody stream에서 `sequence=2`, `previous_event_hash=null`, zero `event_hash`도 schema-valid | P0 | JCS/I-JSON/stream cross-check gate; 예제는 구조 예제임을 명시 | 실제 JCS canonical byte hash 및 독립 anchored head 검증 |
| A05 | Legal Hold `RELEASED`인데 해제자/일시 부재해도 schema-valid | P0 | 상태전이·영향범위·파생/백업/복구계열 정책 oracle | authorized release 이벤트 없으면 release/삭제 불가 |
| A06 | 현재 모든 예제는 schema-valid/invalid 쌍이며 다중 객체 참조 테스트는 없음 | P0 | 교차 객체 referential integrity + negative matrix 설계 | 고아 production, missing evidence, index ghost 검출 |
| A07 | 원본/파생의 시간·출처 사실이 source-provided 주장보다 강하게 승격될 위험 | P1 | Source authenticity/metadata uncertainty 분리 명시 | 빈 문맥 또는 매체 재전송 자료를 original-native 주장 금지 |
| A08 | R2 문구 `partial_or_unknown`, `native_original`이 v2 source_fidelity enum에 없음 | P1 | `18_DATA_CONTRACTS.md` 문구 실제 enum과 정렬 | schemas/v2 보존; enum validation + label UX 확인 |
| A09 | ADR-0010 번호 중복: 하나는 SUPERSEDED여도 `docs/adr/*.md` active listing에 혼재 | P2 | superseded/로 이동, R3 historical ZIP에 원본 보존 | active ADR ID 1:1 |
| A10 | cloud sync/local backup은 독립 백업과 타임스탬프/진정성 및 실제 업로드 증빙을 대신하지 못함 | P0 | backup proof/clock trust/cross-domain drill 강화 | 별도 failure domain에서 물리 복원 통과 전 운영 승인 금지 |
| A11 | 정책상 immutable이 진짜 WORM/법적 증거능력으로 오인될 수 있음 | P1 | `49`의 보증·한계 matrix 포함 | UI, Export, README에서 보증 구분 |
| A12 | 외부 AI/컨버터/뷰어/MCP 등으로 민감 bytes가 전파되거나 진단 로그에 누출 가능 | P0 | local vs provider 경계·egress 모든 간접 경로 oracle | 실제 deny-by-default 테스트와 negative telemetry 검증 |
| A13 | PeerHub/Engram 인터페이스는 버전이 계속 움직이며 API 모양은 릴리스 하나로 입증되지 않음 | P1 | v0.12.4/v3.7.0 기준, release-bound contract probe 유지 | 실제 CLI contract probes 전 `COMPATIBLE` 주장 금지 |
| A14 | 기존 횡적 매트릭스는 영역별 대분류만 있고 실패 반례의 완성도는 검증하지 못함 | P1 | multi-axis semantic acceptance matrix 및 gate owner 연결 | 실험/프로덕션 실증 결과와 feedback verification 등록 |
| A15 | 필수/선택의 수명주기: 하나의 거대한 G0~G7 프로세스를 개인용 CLI에 늘 강제하면 오버엔지니어링 | P1 | core safety fast path와 운영확장 optional path 분리 | 빠른 단일파일 offline ingest→verify 사용성 실측 |
| A16 | snapshot/source_consistency 자료는 실제 원자적 스냅샷 보증이 아님 | P0 | quiesce/manifest 기준·비동기 쓰기·source rehash 부정 테스트 | `COMPLETE`/ERL3에는 일관성 증빙 필요 |

### 종적(Plan→TDD→Release→Operate→Improve→Retire)
- Plan: 단일 책임 소유권·사용자 가치·위험수용·후속 trigger는 문서화, 운영 owner는 미지정(default role).
- TDD: 실행되는 제품/회귀테스트는 **0**. schema structural pass는 semantic pass와 구별해야 함.
- Build: reproducible build, dependency lock, scanner/attestation 및 실제 빌드 없음.
- Integration: PeerHub/Engram/MCP 라이브 compatibility 검증 없음.
- Release: gate G0~G7 계약은 있지만 후보 지문/승인 증거 생성 전.
- Operate: Windows+OneDrive/Google Drive 현장 실증, split brain, 백업 복구 미실행.
- Improve: 사후효과 측정 루프 정의됨; 실사용 관측값·사고 리플레이는 없음.
- Retire: Legal Hold/개인정보 파기/키 파기/복구본까지 범위 재검증 필요.

### 횡적 (정보·권한·오류 전파)
`외부 취득→Drop→Capture→Object→Record→Custody→Knowledge→Memory→Retrieval→Production→Backup→Restore→LegalHold` 경계마다 (a) object identity (b) provenance (c) ACL/egress (d) 시간 (e) fail-closed (f) rollback/repair (g) human approval을 대조한다.

### 품질 / 사용자 관점
간단하고 독립적인 기본 경로를 지킨다. 최소 성공 UX는 `capture → verify → get → export plan`; cloud/multi-AI/Bases/vector index는 optional extension이다. 증거 모델 때문에 개인 메모에도 무조건 포렌식 수집 비용을 강제하지 않는다: high-value evidence profile에서만 강화하지만 **이미 Evidence로 등록된 바이트에 대해서는 원본/관계 무결성을 완화하지 않는다**.

### 객관 결론
**설계 방향 적합, TDD 착수 조건부 GO. 릴리스·증거 제출 신뢰성·운영 준비 NO-GO.** 188개 요구사항에 연결된 test ID 존재는 완성 증명이 아님. `quality/R4_SCHEMA_LIMITATION_PROBES.json`은 현행 JSON Schema에 대해 실제로 발생한 의미적 반례를 기록한다.

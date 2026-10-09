# 32. R3 권위 규칙 및 변경통제

**상태:** R3는 R2 위에 수립한 Pre-TDD 설계 기준선이다. 실제 동작하는 코드, 실행 테스트, 실제 배포가 아님.

## 우선순위 (동일 주제 충돌 시)
1. `docs/32_NORMATIVE_INDEX_AND_DECISIONS.md` + 승격·승인된 R3 ADR / 이 문서의 명시적 변경
2. `schemas/governance/v1` 및 `schemas/v2` (각각 운영/증거 도메인); 구조적으로 못 표현하는 invariant는 domain validator 계약
3. `docs/34_LIFECYCLE_REQUIREMENTS.md`, `docs/33_FEEDBACK_LOOP_STATE_MACHINE.md`, `docs/35_TDD_TO_RELEASE_GATES.md` 및 기타 R3 소유 문서
4. R2 문서의 비충돌 내용. `docs/02_ARCHITECTURE.md`의 concurrent-writer 오해를 본 개정에서 제거함
5. `history/R2_input.zip`과 `history/R1_input.zip`은 역사 자료이며 현행 명세 아님

## 중요 결정
- 증거 canonical byte/metadata는 Second Brain이 소유. PeerHub Core는 Peer/Stream/Record/Offset, 기타 기능은 Extension. PeerHub outage는 evidence commit을 막지 않아야 한다.
- 단일 지정 Writer + 여러 capture-only. 동일 Cloud root에 shared SQLite, 임의 분산 CAS, 자동 writer failover 불허.
- `40_Meta/governance/`는 서명/해시로 검증 가능한 **비민감 운영 사실**만 저장. 원시 개인정보·비밀 로그·토큰·사건 사실을 테스트 evidence로 복제하지 않는다.
- 테스트 로그 / secret bearing traces는 local isolated artifacts. 릴리스 증빙은 sanitized summary + digest + 재현 설명만 durable.
- 개선안은 무엇을 실제로 변경했는지, 어떤 결정/원인에 연결되는지, 후속 효과가 관측됐는지까지 기록해야 CLOSED.
- 법적 증거로 사용 가능성, 외부 타임스탬프 진정성, WORM 성질을 시스템 자체가 보장한다고 주장하지 않는다.
- (중요) 단일 Authoritative ADR ID. 두 파일로 존재한 ADR-0010 중 `0010-canonical-jcs-event-hash.md`만 현행 규범; 다른 것은 SUPERSEDED.

## 판정 정책
- `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`, `WAIVED`를 구분. 필수 게이트의 `WAIVED`는 PASS 대체 불가(릴리스가 아니면 실험용 milestone은 허용).
- 자산/비용/프라이버시 때문에 수동으로만 증빙 가능한 항목은 `MANUAL_VERIFIED`로 구분하고 실제 evidence ref와 운영자 승인을 기록한다.
- 마지막 완전한 테스트 결과가 있어도 candidate digest가 다르면 `STALE`로 재평가.
- release changes, target cloud/provider, underlying schema, major engine/model이 변경되면 해당 의존성 평가를 INVALIDATE.
- 최소 구현은 기능을 줄일 수 있지만 Vault 원본 무결성, fail closed, legal hold, 정책 경계, 복원 가능성은 묵시적으로 생략하지 않는다.

## 패키지 읽기 순서
`00_START_HERE.md` → `docs/32_*` → `docs/33_*` → `docs/34_*` → `docs/35_*` → `docs/40_*` → `docs/43_*` → `docs/44_*` → `START_TDD_NEXT_CHAT.md`.

## R4 independent review addendum
`docs/47~50`와 `quality/R4_*`는 구조 스키마 검증보다 엄격한 의미적 수락 기준 및 미실행 시나리오를 추가한다. 기존 norm 188개는 유지한다. 두 ADR-0010 파일 중 superseded는 `docs/adr/superseded/`로 이동했으며 R3 원형은 history ZIP에서 확인한다.

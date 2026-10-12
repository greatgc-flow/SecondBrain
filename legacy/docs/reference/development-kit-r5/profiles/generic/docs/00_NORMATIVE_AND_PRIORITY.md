# 00. 규범 우선순위 · 상태 해석

## 우선순위
1. 프로젝트 승인된 `project.toml`, 해당 프로젝트 ADR/계약(적용 조건과 재정의 근거 명시) 및 운영·법령상의 외부 의무
2. 이 패키지의 프로파일 판정·필수 요구사항 `quality/requirements.csv`, `docs/01`, `docs/02`
3. 버전 지정된 `schemas/v1`, 해당 프로그램 계약과 요구사항 오라클
4. 본 패키지의 설명 문서·템플릿·예제
5. history/참고자료 및 초안(비규범)

상충 시 임의 해석/자동 승격하지 말고 ADR을 남긴다. **공통 MUST**는 모든 프로젝트에 적용; `STATEFUL`, `NETWORKED`, `AI_ENABLED`, `CLI_PUBLIC`, `CLOUD_SYNC`는 프로젝트에서 해당 기능/위험이 존재할 때 MUST이다. N/A는 (조건 불성립 증거, owner, reviewer, 재평가 트리거) 기록.

## 성숙도
`DRAFT → APPROVED_DESIGN → RED_REPRODUCED → IMPLEMENTED_GREEN → CANDIDATE_VERIFIED → DEPLOYED_OBSERVED → CONTINUOUS_IMPROVEMENT`.
정적 검사 PASS는 설계 문서 검사뿐. `PLANNED`, `NOT_RUN`, `BLOCKED`, `FAIL`, `PASS`, `STALE`를 혼동하지 않는다. 위험한 Gate에 waiver를 PASS로 산입하지 않는다.

## 식별 규칙
`GD-###` 요구사항, `TEST-###` 계획 오라클, `ADR-####` 구조 결정, `INC-###` 사고, `FB-###` 개선, `RC-###` 릴리스 후보. 같은 ID 재할당 금지. 요구사항/상태 데이터는 사람이 승인한 canonical 저장소가 소유한다. GitHub Issue/PeerHub는 연결/투영 채널일 뿐 승격 근거가 아니다.

## v2 추가 (2026-10-10)
`docs/22_2026_METHOD_ADOPTION.md`~`docs/31_RESEARCH_PROVENANCE_AND_CAUTION.md`와 GD-075~100은 기존 v1 계약의 확장 규범이며, 기존 MUST를 면제하지 않는다. 겹치는 내용은 v2에서 **더 구체적인 실행·평가·권한 경계**가 우선하되 충돌은 별도 ADR로 해결한다. AI 평가·장기 harness·다중 trial은 AI_ENABLED가 아니면 N/A로 유지한다. 코드 작성 또는 실제 TDD/인수시험은 아직 없다.

# 23. SDD↔TDD 수렴 프로토콜

**SSOT:** 승인된 `spec.md`(왜/무엇) + 버전 계약(schema/API/CLI) + 요구사항 CSV(ID/수락기준) + ADR(왜 이 구조). task·test·code는 각각 다른 레이어의 구현/증빙이며 spec를 암묵적으로 재정의하지 않는다.

1. **Specify:** 위험·사용자 시나리오·반례·비목표·성공척도·기술 독립적인 WHAT.
2. **Plan:** ports, failure, security, data ownership, migration, 선택 기술·검증 환경.
3. **Tasks:** 작은 수직 슬라이스 및 dependency DAG. 수락기준마다 최소 한 개 negative oracle.
4. **Implement:** TDD RED가 실패하는 원인을 관측 → 최소 GREEN → Refactor. 변형 검사를 추가할 경우 mutant를 살아남게 하지 않는다.
5. **Converge:** 요구사항→작업→테스트→실제 동작/코드 diff→검증영수증 양방향 대조. 미해결 MUST의 `gaps[]` 비어야 PASS 후보가 될 수 있다.
6. **Effect:** 출시 후 사용자 결과/오류 예산/비용/불필요한 변경도 관측 후 업무상 CLOSED.

Spec Kit은 예시적 reference tool이며 정확한 명령은 도구 버전에 종속된다. 브라운필드는 현재 코드 동작과 기존 계약을 먼저 reverse spec로 등록하고 승인된 변경만 반영한다.

**반례**: (a) `spec.md` 변경 후 `tasks.md` 그대로, (b) 구현이 오히려 더 많은 권한 부여, (c) OLD candidate의 test log 재사용, (d) 단순 문서 PR을 구현 성공으로 보고, (e) 필수 requirement N/A 무사유. 각각 G0/G2/G5 차단.

**프로세스 반부패 규칙**: 외부 Spec Kit이 markdown 폴더 형식을 바꾸더라도 `GD-ID`/`TEST-ID`/`candidate_id`는 안정; adapter가 출력물을 정규화한다.

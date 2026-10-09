# SecondBrain R4 — TDD handoff (2026-10-09)

R4를 기준으로 작업한다. 이전 R1/R2/R3로 롤백하지 않는다. `00_START_HERE.md`에서 읽기를 시작하고, `docs/50_FINAL_VERDICT_AND_TDD_ORDER.md`의 S1~S6 순서로 RED fixture부터 작성한다.

- **처음 할 일**: `quality/R4_SEMANTIC_TEST_ORACLES.csv`의 SEM-01/02/03 및 SEM-07~12에 대해 JSON schema PASS여도 domain validation FAIL이 되는 RED 테스트 구현.
- `schemas/v2` 예제 중 custody-event의 all-zero hash는 구조 예제이지 crypto 검증용 정답이 아님. RFC8785 JCS 독립 implementation/vector를 선택하고 actual hash fixture를 별도로 생성.
- Release까지 필요한 TDD/운영 gate는 기존 `docs/35`~`46`.
- 데이터 root는 테스트 전용 임시 위치; 실제 사용자 OneDrive/Google Drive 증거 원본, 실제 AI 공급자 호출, 삭제, 계정 설정 변경은 하지 말 것.
- R4 audit은 제품코드/pytest test run을 증명하지 않는다.

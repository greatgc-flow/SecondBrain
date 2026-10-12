# 34. R3 기능/운영 추가 요구사항 (TDD 직전)

이 요구사항은 R1/R2 기존 **134개**를 보존하면서 추가된 독립 계약이다. 모든 ID의 정확한 수준·planned test·검증 증빙 유형은 `traceability/requirements_to_tests.csv`가 authoritative; 자동 테스트 코드 작성은 아직 하지 않았다.

범주: `LIF`(생명주기/종결), `QAL`(TDD·품질), `FBK`(피드백), `OBS`(관측/SLO), `RLS`(릴리스), `CHG`(변경·마이그레이션), `SUP`(보안/Supply-chain), `DRL`(복구), `EVA`(AI/검색 평가), `GOV`(거버넌스).

각 항목에는 `objective`, `owner`, `evidence`, `negative`, `exit`가 있어야 하며 누락/후보 불일치 경우 PASS 표시 금지. Non-functional 특성은 ISO/IEC 25010:2023의 9개 제품 품질 특성에 맵핑하되 인증 또는 정식 ISO 준수 선언을 의미하지 않는다.

### 해석 원칙
- `MUST` 중 도구로 검증 가능한 것은 자동 테스트. 클라우드 제공자 운영 설정, 독립 외부 보관, 사람 승인처럼 기계적 확정이 불가능한 것은 **수동 증빙 MUST**로 구분.
- `SHOULD`: deferment 승인과 review trigger가 없으면 포함 여부 불명 처리.
- `MAY`: 초기 도입 필수 아님. 0개 구현을 결함이라고 하지 않음.
- 모든 새로운 요구사항은 개발을 요구하는 것은 아니다. `검증·운영 규칙` 자체가 요구사항일 수 있다.

### Pass criteria
Gate는 테스트 count가 아니라 candidate-bound evidence ledger와 안전/품질 수락 조건으로 닫혀야 한다. 체크리스트와 승인서 모두 `not_run / stale / waived / manual_verified` 상태를 별도로 표시.

상세 불변조건: `docs/33`, `35~44` 및 `quality/lifecycle_scenarios.csv`.

Governance-event v1 schema ensures state-transition durable event shape. State snapshots are projections and must be rebuilt or matched to verified event streams.

# 01. 최소 규범 구조와 MECE 기준

| 단일 진실 | 소유 위치 | 누가 읽나 |
|---|---|---|
| 범용 요구사항 100개 | `profiles/generic/quality/requirements.csv` | 모든 개발 프로젝트의 기초 |
| 범용 계획 테스트 100개 | `profiles/generic/quality/test_catalog.csv` | TDD 계획, NOT_RUN |
| Second Brain 요구사항 188개 | `profiles/secondbrain/traceability/requirements_to_tests.csv` | Evidence-First 도메인 |
| 도메인 계약/정책/스키마 | 각 `profiles/...`의 `docs/`, `schemas/` | 해당 제품 구현자 |
| 방법론 적용 덧붙임 | `profiles/secondbrain-methods/` | 도메인 변경이 필요할 때 |
| 교차 기능 인벤토리 | `catalog/FEATURE_INVENTORY.csv` | 조회용 파생 뷰 (SSOT 아님) |
| 범용 운영 표준 | `standards/` | 두 프로젝트 공통, 설계 충돌 시 도메인 안전 규칙 우선 |
| 검수 결과 | `quality/AUDIT_REPORT.json` | 마지막 정적 검수 시점 |
| 진행/학습/오류 기록 | `.kit_state/feedback.jsonl`(로컬 단일 writer) | 작업 중 생성, 백업 정책 별도 |

**분류 규칙:** 각 요소는 Source(원본) / Spec(의도) / Implement(구현) / Test(검증) / Evidence(증빙) / Runtime(운영) / Learning(개선) 중 주 역할 하나만 가진다. 여러 요소를 동시에 대표하면 분리한다. 하나의 ID는 1개 canonical record를 가진다.

**충돌 우선순위:** 법률·보안 외부 의무 → 해당 프로필 승인된 설계/ADR → 범용 설계 계약 → 설명/샘플 → history. 도메인 안전 의무를 범용 편의성으로 우회 금지. 실제 프로젝트 설정이 의무를 임의로 해제할 수 없음.

**Very Simple:** 문서 숫자가 품질은 아니다. 새로운 기능은 현재 사용자 시나리오·실패 오라클·운영 소유자·성공 효과가 하나의 줄로 표현되기 전까지 새 Core 명령으로 승격하지 않는다.

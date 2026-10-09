# 00. Canonical map — One Source, Multiple Uses

## 책임과 우선순위 (각 정보에 SSOT 하나)

| 정보 종류 | 정본 / 변경 위치 | 파생 / 읽기 경로 | 중복 금지 규칙 |
|---|---|---|---|
| 범용 100개 요구 | `profiles/generic/quality/requirements.csv` | `catalog/FEATURE_INVENTORY.csv`, `kit catalog` | derived CSV 수동 수정 금지 |
| 범용 100개 시험 계약 | `profiles/generic/quality/test_catalog.csv` | `kit verify` 참조 검사 | 시험 `NOT_RUN` → `PASS` 허위 변경 금지 |
| Brain 188개 요구/계획 시험 | `profiles/secondbrain/traceability/requirements_to_tests.csv` | 조회용 `catalog` | 도메인 계약/법률 경계 유지 |
| 도메인 스키마 | `profiles/<profile>/schemas/...` | 각 `examples/`, `tools/` | schema 통과만으로 cross-record 의미 통과 주장 금지 |
| 범용 운영 규칙 | `standards/` 해당 주제의 **하나**의 파일 | Quickstart, CLI help | 일반 규칙을 각 프로필에서 재정의 금지 |
| Second Brain 안전·증거 의무 | `profiles/secondbrain/docs/32_NORMATIVE_INDEX_AND_DECISIONS.md` 및 해당 ADR | `profiles/secondbrain-methods/` | 범용 단순화로 약화 금지 |
| 설계 상태/검수 | `quality/AUDIT_REPORT.json` + 실행한 검사 출력 | README 요약 | 실행·시점·범위 구분 |
| 개발 진행/오류/교훈 | `.kit_state/feedback.jsonl` (현재 장치/단일 Writer) | `kit feedback show/verify` | 사용자 승인 근거 없는 종료 금지 |
| 외부 Git 현황 | GitHub 레포의 자체 커밋/릴리스 | `catalog/GIT_HISTORY_REVIEW.csv` | 외부 레포와 이 키트의 Git 이력 혼동 금지 |

### Normative 우선순위

1. 법률·보안·원본보존 요구 및 근거 있는 외부 제약
2. 해당 제품 승인된 ADR·계약·위험 차단 규칙
3. 이 파일과 `standards/` 공통 운영 규칙
4. 구현·테스트 사양과 설계 설명, 예제
5. 보존된 이전 ZIP·과거 문서 (현재 규범 아님)

서로 상충하면 **임의 추측하지 말고 OPEN feedback으로 기록**하고 ADR 또는 정본 1개만 수정한다. 파일/폴더 이름은 식별자가 아니며 루트 절대경로를 사양에 저장하지 않는다.

## One Source Multi Use

- 정본 CSV → 조회 catalog → AI 입력 → TDD 계획 → G0~G7 판정 재사용.
- 정본 JSON Schema → 유효/무효 예제 → 계약/변경 영향 검증 재사용.
- 기록된 incident/lesson → 최소 변경 제안 → 새 실패 오라클 → 회귀테스트 → 릴리스 관측 재사용.
- 재검토가 필요한 시점: 요구/버전/외부 도구/CLI 변경, 실측 결함, 운영 SLO 악화, 새로운 반례 발견.

**이 패키지에 `history/` 아래 중첩 ZIP을 유지하는 이유:** 이전 설계의 유실과 회귀를 검증하기 위함. 현행 사용자는 열지 않아도 된다. 과거 JSON/README의 오래된 버전을 현재 구현 선언으로 간주하지 않는다.

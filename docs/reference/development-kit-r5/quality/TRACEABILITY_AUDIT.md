# Feature → Contract → Planned Test → Implementation → Operation → Feedback 추적

## 실제 생성 결과

- 범용 **100**행 (`GD-*`)과 Second Brain **188**행 (`REQ-*`), 합계 **288**행을 `catalog/FEATURE_INVENTORY.csv`로 생성.
- 모든 행에 `contract`, `test_id`, `test_catalog`, `implementation`, `test_execution`, `applicability`, `release_gate` 필드 포함.
- **모두 PLANNED:** `implementation=NOT_IMPLEMENTED`, `test_execution=NOT_RUN`. 기능을 구현했다고 주장하지 않는다.
- 종/횡/예외/실측 샘플 시나리오 **46**개 `catalog/SCENARIOS.csv`. 이건 일반/도메인 전체 288개 요구사항의 완전한 실행형 테스트가 아님. 도메인 구체화 후 확장해야 함.
- 실측/토큰 비용 발생 계층은 별도 **T3/T4**, 승인 전 기본 미실행. 모델/클라우드 계정/실기기/Git 원격 테스트를 실행하지 않는다.

## 단면 검토 오라클

| 단면 | 발견한 위험 | 현재 방어 | 미해결/실행 이후 |
|---|---|---|---|
| Requirement↔Test | ID는 있으나 실제 함수 없음 | 계획과 실행 상태 분리 | 첫 TDD 이후 추적 업데이트 |
| Spec↔Code | 제품 구현이 없어서 중복 검사 불가 | 표준 공통화 규칙/외부 모듈 결정표 | 실제 구현 PR에서 중복 검토 |
| CLI↔Docs | 수동 예제의 오래된 명령 | kit help는 argparse 한 곳, 제품은 capability check | OS/Node/provider별 실제 help smoke |
| Files↔Paths | 이동 후 하드코딩 | `kit.py`는 `__file__` 기반 상대경로 | Second Brain root의 실기기 rename |
| Event↔History | 로컬 journal 수정 가능 | 도구는 추가 기록, 임의 변경 시 parser reject | 외부 Git/backup anchor 및 동시 Writer 통제 |
| TDD↔Release | schema pass를 실테스트로 오인 | Gate가 source+artifact digest 필요 | CI 구성과 배포 바이트 검사 |
| Release↔Operations | 배포 직후 CLOSED | 관측/검증 증빙 없으면 종료 신청만 | 실제 사용자 측정 필요 |
| Cloud↔Evidence | 동일성≠진정성 | capture chain + restore + export 조건 | 법률 전문가/독립 포렌식 검토 |
| AI↔Security | 외부 도구에 원본 유출 | 기본 deny + negative oracle | 실제 provider opt-in 테스트 |

## 검증 리포트 해석

`python kit.py verify --json`은 **구조·참조·원본 패키지 정적 검사**이며 다음은 제외된다: 법률 증거능력, 문서 의미의 완벽성, 실제 개발 기능 동작, Windows/OneDrive OS 경계, 클라우드 restoration, AI 정확도, 영구 무결성, 설치/릴리스.

원본 ZIP은 `history/` 아래 exact bytes로 있고 `history/SOURCE_FINGERPRINTS.json`에 SHA-256이 기록돼 있다. 변경됐다는 주장에는 원본 바이트 비교를 우선한다.

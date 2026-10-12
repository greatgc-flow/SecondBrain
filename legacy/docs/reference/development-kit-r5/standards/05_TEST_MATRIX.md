# 05. 종·횡·재귀 시험 설계 (실행/비용 상태 구분)

## 종 방향 — 각 사용자 시나리오의 닫힘

`사용자 입력 → 정책·계약 → 정상/예외 처리 → 관찰 가능한 결과 → 복구 → 사용자 안내 → 회귀시험 → 운영효과`. 하나라도 빠지면 CLOSED 불가. `catalog/SCENARIOS.csv`에 샘플 반례, 기대 결과, Gate, 시험환경, 상태를 적는다.

## 횡 방향 — 인접 인터페이스의 간섭

- 설정/CLI ↔ 구현 ↔ 의존성 ↔ OS (유니코드·공백·긴 경로·권한)
- 스토리지 ↔ 클라우드 동기화 ↔ 해시 ↔ 복원 ↔ 접근통제
- AI 입력 ↔ 모델 ↔ 도구 호출 ↔ egress ↔ 평가/감사 로그
- spec ↔ testcase ↔ code ↔ build ↔ release candidate ↔ incident/learning

## 5개 시험 층

| 층 | 종류 | 기본 실행 | 장점/주의 |
|---|---|---|---|
| T0 | 정적 문서/참조/스키마 | 로컬 무료 | 제품 실행 증명 아님 |
| T1 | Unit/Property/Mutation | 로컬 무료 | 디바이스·클라우드 대체 불가 |
| T2 | 계약/통합/고장주입/복원 | 샌드박스·로컬 | 원인별 재현 대상 |
| T3 | 실제 OS/Cloud/App/보안 수동 실증 | 비용·권한 있음 | 별도 승인/데이터 격리 |
| T4 | AI provider 실측, quota, token/latency/eval | 명시적 opt-in | 인증·사용량·요금 발생 가능 |

**T3/T4는 절대 CI 기본으로 자동 실행하지 않는다.** 실행 전에 계정, 데이터 등급, budget cap, 환경, timezone, 횟수, 취소 조건, 결과 보관/삭제, 권한을 확인. 측정값 없으면 `NOT_RUN`/`UNKNOWN`, 과거 값이면 `STALE`. 성공 판정은 release SHA + build digest + test suite revision + environment + verifier + timestamp와 결합한다.

**외부 도구 한계:** Node path escaping, Windows long-path, OneDrive hydration, Drive mirroring, provider quota는 무리한 workaround을 구현하지 않는다. WARN과 간단한 우회방법/지원 범위를 안내; 보안·무결성 위반만 FAIL_CLOSED.

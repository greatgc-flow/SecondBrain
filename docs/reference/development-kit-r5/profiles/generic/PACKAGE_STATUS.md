# 상태: Pre-TDD Design Only (2026-10-10)

- 요구사항: GD-001~GD-100 100개. v1 74개 보존 + 신규 26개.
- 계획된 테스트: TEST-001~TEST-100 = 100개 전부 NOT_RUN. 실행 코드/실제 GREEN 0.
- Schema: v1 8 + v2 6. 구조 계약 예제 검사와 runtime 의미적 검사 구분.
- Cross-boundary failure plans: 기존 16 + 신규 12 = 28개.
- Methods research decisions: 14개.
- ADR: 001~018.
- Release/operation gates: NOT_RUN / NO-GO; G0 프로젝트별 승인 필요.
- 디자인 검증 및 manifest/ZIP 검사 결과는 통합 패키지 `VERIFY_REPORT.json`에서 확인.

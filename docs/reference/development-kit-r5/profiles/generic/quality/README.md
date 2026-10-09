# 품질 매트릭스 사용법

- `requirements.csv`: 템플릿 요구사항 74개, 본문+오라클+부정 사례를 한 줄에 둠.
- `test_catalog.csv`: TEST-ID 74개, 각 test는 **계획된** 양/음 시나리오. `execution_status=NOT_RUN`이 정답.
- `cross_boundary_scenarios.csv`: 단일 컴포넌트만 테스트해서 놓치기 쉬운 경계/복구/보안/릴리스 교차 반례.
- `DESIGN_LINT_RESULT.json`: 실행한 정적 검사 결과. 실제 사용시 새로 계산해야 한다.

생성된 고유 ID 수가 테스트 품질이나 MECE의 자동 증명은 아니다. 도메인과 프로파일이 확정되면 오라클·fixture·제외 근거를 사람과 코드가 보강해야 한다.

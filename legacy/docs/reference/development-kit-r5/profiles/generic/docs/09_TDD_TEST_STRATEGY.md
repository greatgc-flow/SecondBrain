# 09. TDD/Test Harness (Pre-TDD 정의)

## 첫 사이클
`requirement → negative oracle → failing test (RED) → smallest code (GREEN) → refactor → contract/integration → candidate evidence`. 테스트를 확인하지 않고 '합리적으로 동작할 것'이라는 문구로 대체하지 않는다.

## 계층
- **unit**: pure domain invariants, deterministic time/IO injections.
- **property / mutation**: 경계/불변식·randomized faulty inputs·mutation survival.
- **contract**: port/adapters, CLI exit code, error envelopes, versions.
- **integration**: OS filesystem/DB/HTTPS/migration; known dev environment.
- **e2e**: 실제 설치·운영자 워크플로우; live providers 비용 승인 필요.
- **chaos/recovery/security**: 장애 주입, 권한우회, data exfiltration, restore.
- **manual**: 법적/물리적/외부 인증 등 자동 불가 항목. 명시된 증빙과 승인.

## Required test evidence
`test_id, requirement_id, commit, candidate_id, suite_version, env, run_at, actual_status, logs_redacted_uri, digest`. `quality/test_catalog.csv`는 아직 계획표이므로 실제 실행 결과와 혼동 금지.

## Metric caveat
코드 커버리지 100%만으로 성능·보안·UX·복구 보장 불가. 경계 실패가 중요한 곳은 mutation+부정 사례 필수. flaky는 owner·reproduce·expiry 없는 skip 불허.

## v2: Agent 평가와 독립성 (Pre-TDD)
AI_ENABLED인 경우 별도 `docs/25_EVAL_DRIVEN_DEVELOPMENT.md`를 적용하며 eval은 code-based vs model-based vs human으로 구분한다. Golden set 노출·한 번의 성공·같은 agent의 자기 채점만으로 G5 승격 불가. 실제 테스트 오라클은 `quality/v2_semantic_oracles.md`에 정의되지만 아직 NOT_RUN이다.

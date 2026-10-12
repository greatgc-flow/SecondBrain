# R4 change log (2026-10-09)

- 독립 검사에서 R3 static audit PASS가 의미적·실동작 PASS라는 착시 위험 확인.
- `docs/47~50` 최종감사·semantic validation·운영보안·판정/우선순위 추가.
- `quality/R4_SCHEMA_LIMITATION_PROBES.json`: synthetic schema-valid but domain-invalid 반례 8개 실측.
- `quality/R4_SEMANTIC_TEST_ORACLES.csv`: 28개 음성 수락 시나리오; 기존 188개 normative requirements에 매핑, TDD NOT RUN.
- `docs/18_DATA_CONTRACTS.md`: 실제 Evidence v2 source_fidelity enum과 문서 불일치 정정.
- 중복된 ADR-0010의 SUPERSEDED 파일을 `docs/adr/superseded/`로 이동. R3 원본 ZIP은 `history/R3_input.zip`로 전체 보존.
- 기존 제품구현/실행테스트 파일 추가 없음. 원래 schemas/v1, schemas/v2, schemas/governance/v1 모두 바이트 그대로.
- R3 숫자 188개의 개수가 적절함을 확인했고 새 규범 요구사항을 무분별하게 추가하지 않음.
- 최종 경계: **TDD 시작 조건부 GO, 실제 릴리스 NO-GO**.

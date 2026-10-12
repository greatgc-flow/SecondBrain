# v2 — Authoritative R2 Schemas

Draft 2020-12. R1 `schemas/v1`은 그대로 보관. $id = `urn:secondbrain:schema:v2:<name>` — offline local schema registry로 매핑. Network lookup 불필요.

스키마는 개별 JSON field/shape를 판정한다. **서로 다른 record 간 참조 존재**, digest 실제 데이터 일치, JCS event_hash, event sequence linkage, UUIDv7 버전/시각/충돌, `valid_from<=valid_until`, `capture_started<=captured`, valid source/metadata intent, active-hold propagation, `ERL` 산정은 **application semantic validation**이 필요하다.

JSON Schema의 `format: date-time`을 검증하기 위해 실제 validation 엔진에서 `FormatChecker` 또는 동등한 지원을 명시적으로 사용한다. RFC3339 offset 지정은 regex·strict date parser로 모두 검사. NaN/Infinity, duplicate JSON keys, non-UTF8, float canonicalization 문제는 ingestion parser 단계에서 거부.

v2 fixtures are structural examples only. Real source hash/path/backup contents integrity is not established by schema-only fixture validation. See `docs/21_TDD_SCENARIOS.md` and `docs/18_DATA_CONTRACTS.md`.

# Schemas

JSON Schema Draft 2020-12 기준.

R1 Pre-TDD schema:
- `evidence-object.schema.json`
- `evidence-record.schema.json`
- `observation.schema.json`
- `acquisition-event.schema.json`
- `custody-event.schema.json`
- `derivation.schema.json`
- `legal-hold.schema.json`
- `snapshot.schema.json`

주의:
- `$id`의 `example.invalid`는 구현 시작 시 프로젝트의 영구 schema namespace로 교체한다.
- JSON Schema 자체도 TDD contract 대상이다.

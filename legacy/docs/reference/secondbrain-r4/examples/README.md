# Synthetic Structural Fixtures

모두 2026-10-09 설계 검증용 **가상 데이터**이며 증거/인증/실제 custody 검증 결과가 아니다. `valid`=스키마 구조 통과, `invalid`=필수 필드 누락으로 거부. `custody-event.valid.json`의 `event_hash=000...`은 cryptographic semantic validator 관점에서는 **유효하지 않으며**, TDD에서 JCS/chain 검증 테스트가 별도로 반드시 필요하다. Backup verification `PASS` 값도 실제 secondary copy가 검증됐음을 의미하지 않는다. `examples/v2` 데이터를 운영 evidence vault로 ingest하거나 ERL 평가에 이용하지 않는다.

# 합성 예제 (공식 운영 데이터 아님)

각 `.valid.json`은 **JSON Schema 문법 검사용 샘플**이며 의미검증·서명/서버 인증·실행/운영 증빙이 아님. `.invalid.json`은 필수 필드 하나를 제거한 구조적 실패 예제. `status=NOT_RUN`, `release_status=DRAFT`는 의도적.

실제 TDD에서는 추가로 `Gate PASS + evidence_ref=null`, `feedback CLOSED without EFFECT_OBSERVED`, `candidate_id 동일 but artifact hash 다름`, `retry same request_id with different payload`, `unauthorized egress` 등 **형식 통과/의미 실패** 케이스를 만들어야 함.

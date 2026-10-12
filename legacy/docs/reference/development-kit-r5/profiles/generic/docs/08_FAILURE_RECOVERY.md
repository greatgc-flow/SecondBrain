# 08. 실패 모델과 처리 결과

| 유형 | 반환 | 이후 조치 |
|---|---|---|
| 입력/스키마 오류 | DEFINITE_REJECT | 수정 후 재시도 |
| 인가 거부/민감 egress 거부 | DENIED | 승인 없이는 재시도 금지 |
| 일시적 외부 불능/429 | RETRYABLE | 지수 backoff+jitter, budget/circuit |
| 처리 결과 불명/연결 끊김 | UNCERTAIN | idempotency key로 조회/재조정, 무조건 재실행 금지 |
| 검증된 비가역 부작용 | COMMITTED | durable receipt 조회 |
| 데이터 손상/무결성 위반 | STOP_AND_QUARANTINE | writer 동결, root cause, 독립 복구 |

Failure testing: process kill between stage/commit; disk full; permission denied; stale lease; clock skew; corruption; two device collision; secret leak attempt; provider quota exhausted; migration version mismatch. 적용하지 않는 장애는 N/A 이유를 기록한다.

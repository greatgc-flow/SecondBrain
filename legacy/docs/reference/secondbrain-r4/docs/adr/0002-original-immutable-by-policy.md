# ADR-0002 Original immutable-by-policy

Status: Accepted

## Decision
Evidence Vault payload는 봉인 후 직접 수정하지 않는다. 모든 변환은 derived artifact다.

## Note
일반 cloud folder이므로 WORM을 주장하지 않는다. 무결성은 digest, event, backup, optional timestamp로 탐지/복구한다.

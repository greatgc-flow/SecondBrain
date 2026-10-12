# ADR-0010 Canonical JSON for hash chain

Status: Proposed

## Context
Custody event hash가 serializer 차이로 달라지면 안 된다.

## Proposed
RFC 8785 JCS를 채택한다.

## TDD gate
첫 custody hash-chain test 전에 Accepted/Rejected로 결정한다.

> **STATUS: SUPERSEDED / HISTORICAL.** 동일 번호 ADR의 유효본은 `0010-canonical-jcs-event-hash.md`이다. R3 기준 RFC 8785 JCS 이벤트 직렬화 계약만 적용한다. 이 문서는 이력 보존용이며 신규 구현 지침으로 해석하지 않는다.

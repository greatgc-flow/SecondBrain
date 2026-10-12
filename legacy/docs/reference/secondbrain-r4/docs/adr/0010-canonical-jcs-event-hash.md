# ADR-0010 — canonical jcs event hash

Status: Accepted (R2, 2026-10-09).

## Decision
RFC8785 JCS를 canonical serialization으로 고정하고 hash chain을 stream_id+sequence+previous_hash가 검증되도록 설계한다.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

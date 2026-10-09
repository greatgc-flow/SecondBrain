# ADR-0016 — versioned schema migrations

Status: Accepted (R2, 2026-10-09).

## Decision
R1 schemas/v1은 보존, 신규 records는 schemas/v2. 중간 마이그레이션은 verified transformations과 original v1 보존.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

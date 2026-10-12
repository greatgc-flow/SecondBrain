# ADR-0017 — secondary verified backup

Status: Accepted (R2, 2026-10-09).

## Decision
Secondary snapshot은 completed receipt와 hash verification이 있어야 하고 provider cloud 동기화 성공은 별도 확인.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

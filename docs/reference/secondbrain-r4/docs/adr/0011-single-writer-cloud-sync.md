# ADR-0011 — single writer cloud sync

Status: Accepted (R2, 2026-10-09).

## Decision
Cloud sync는 분산 CAS/락을 제공하지 않는다. 단일 지정 Writer만 canonical writes; 다른 PC는 capture-only 장치별 폴더.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

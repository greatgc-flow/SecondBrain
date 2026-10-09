# ADR-0012 — commit receipts and recovery

Status: Accepted (R2, 2026-10-09).

## Decision
여러 파일/record의 commit은 single atomic transaction이 아니다. verified stage + per-record publish 후 마지막 commit receipt가 논리적 완료 기준.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

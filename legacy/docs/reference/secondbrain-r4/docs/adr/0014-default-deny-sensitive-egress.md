# ADR-0014 — default deny sensitive egress

Status: Accepted (R2, 2026-10-09).

## Decision
AI 외부 전송은 explicit scoped approval 없으면 거부, LLM 출력은 Evidence SSOT에 직접 기록 금지.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

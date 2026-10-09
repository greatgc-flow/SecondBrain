# ADR-0019 — internal uri and local index

Status: Accepted (R2, 2026-10-09).

## Decision
Stable brain URI와 physical root/Obsidian/PeerHub index를 분리; PII/hold ACL은 모든 resolver layer에서 검사.

## Rationale / consequences
세부 구조·실패 사례·수락 기준은 `docs/15_R1_AUDIT_FINDINGS.md` 및 관련 도메인 설계 문서의 계약을 따른다. 변경은 새로운 ADR과 마이그레이션 절차를 요구한다.

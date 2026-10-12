# 11. R1 open decisions — R2 disposition

**모든 TDD 블로커 CLOSED.** 2026-10-09: OD-001 UUIDv7 (RFC9562), OD-002 RFC8785-JCS, OD-003 sha256/aa/bb/<digest>/payload, OD-004 directory snapshot + BagIt export, OD-007 *single designated Writer + capture-only other devices*.

OD-005 application-level encryption is **deployment-conditional/out of scope**, never claim cloud/provider encryption is sufficient for all legal data. OD-006 Obsidian default Knowledge/Context editable, evidence view-only (chosen operational UX).

새 오픈 사항은 `docs/29_RESIDUAL_RISKS.md`의 운영환경/보관기간/키관리와 실제 provider 통합 테스트다. R2 작성 중 해결하지 못한 설계 블로커는 없음(그러나 실 구현의 장애 없음 보장 아님).

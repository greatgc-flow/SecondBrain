# 30. Pre-TDD Exit / Implementation Release Gates

## 현 단계: design freeze, not functional release
- [x] 요구사항을 기능/비기능/금지 요구사항으로 구분
- [x] 주요 P0 설계 충돌(Writer/ERL/JCS/transaction/AI egress) 해소
- [x] 신규 v2 JSON Schema/유효·무효 예제 생성
- [x] 최신 Engram/PeerHub 기준 문서 업데이트
- [x] R1 원본 자료 보존/변경로그
- [x] requirement→planned test traceability
- [x] parser/static package verification
- [ ] 실행 단위 테스트 (TDD 이후)
- [ ] 실제 ingest 코드 및 provider state integration tests (TDD 이후)
- [ ] 백업 복구 실제 드릴 (TDD 이후)
- [ ] 실 OS/Cloud 2기기 충돌 실증 (TDD 이후)
- [ ] 외부 감정·법률 제출 적합성 판단 (별도)

## TDD start checklist
1. schema/v2 registry and fixtures에서 실패 테스트.
2. Single Writer vs capture-only / policy deny를 우선 구현.
3. crash-recovery와 no overwrite/hold/secret denial을 기능보다 먼저 검증.
4. 실제 돌리기 전 최신 PeerHub API와 Engram CLI 변경 감지.
5. 모든 새 requirements는 테스트/판정 근거와 함께 traceability 1:1 갱신.

## Release Candidacy (향후)
`pytest` 전체, typecheck, schema tests, property-based tests, fault injection, Windows path/adversarial tests, 2PC 아닌 cloud sync simulation, canonical rebuild, backup-restore round trip, sensitive egress prevention, integration E2E, export PDF page-to-source lineage, independent reviewer sign-off.

### R2 second-pass hard gate
Backup restore뿐 아니라 source tree copy 시점 일관성과 independent failure domain 증빙도 구현 시 필수. `REQ-BKP-009~010` 테스트 PASS 이전에 ERL-3 배지/상태 공개 금지.

## R3 normative implementation gate
이전 `pytest` 통과 체크리스트만으로 릴리스 승인 불가. `docs/35_TDD_TO_RELEASE_GATES.md`(G0~G7), `docs/40_RELEASE_EVIDENCE_AND_DEPENDENCIES.md`(candidate digest 일치), `docs/39_BACKUP_RESTORE_AND_CHAOS.md`(복구 실증), `docs/38_SECURE_CHANGE_AND_SUPPLY_CHAIN.md`(보안 검증)이 동시에 적용된다. **기존 리스트는 최소 체크이지 충분조건이 아니다.**

# 43. R3 종·횡·재귀적 MECE 교차 검수표

## 축 정의: 독립적인 세 축을 이용
- **종적 (시간)**: Plan→Design→RED→GREEN→Integration→Security/DR→Candidate→Deploy→Observe→Improve→Retire.
- **횡적 (도메인)**: Ingest, Evidence Vault, Meta/Custody, Knowledge/Context, Memory/Retrieval, Evidence Export, Writer/Sync, Backup/DR, AI/PeerHub/MCP, Governance/Supply-chain.
- **품질 (ISO 25010 관점)**: 기능적 적합성, 성능 효율성, 호환성, 상호작용 능력, 신뢰성, 보안, 유지보수성, 유연성, 안전성 (용어 표준 분류와 해당 문서 원문 최종 대조 필요).

**MECE의 의미:** 영역 책임은 하나씩 두되 교차통제(privacy/hold/temporal/custody)를 여러 셀에 중복 점검하는 것은 의도적. 중복 제거는 *소유 책임*에서, 누락 방지는 *교차 검증*에서 해결.

| 도메인 | 설계 계약 | 구현 테스트 | 릴리스 게이트 | 운영 관측 | 피드백 종료 |
|---|---|---|---|---|---|
| Ingest | 05,16,17 | T1~T8, LC-SYNC | G2,G3 | intake latency/orphan | recovery negative test |
| Vault & Evidence | 03,18 | hash/seal/lineage | G2,G4 | fixity mismatch | verified repair+follow-up |
| Custody & Meta | 18,ADR10 | event/JCS/anchor | G2,G4,G5 | chain validation | incident/event+external anchor |
| Knowledge/Context | 27 | provenance/change | G2,G3 | drift/contradictions | human correction+eval |
| Retrieval/Memory | 27,41 | citation/ACL/abstain | G3,G4 | golden metrics | dataset version + shadow rerun |
| Export | 26 | bagit/redaction/page map | G4,G5 | production verification | sample recipient replay |
| Writer/Cloud | 04,16 | authority/simulator | G3,G4,G6 | split brain/conflict | root-cause followup |
| Backup/Restore | 20,39 | corrupt/DR/restore | G4,G6 | drill pass/RPO/RTO | verified physical recovery |
| AI & Integrations | 19,25,38 | egress/contract | G3,G4 | quota/leak/stale | version gating |
| Governance/Release | 33~42 | test receipts/approval | G0~G7 | SLO/backlog/release | efficacy proof |

## 잔여 구멍 판정 (의도적인 비포괄)
1. 실제 법원 증거능력·취득 적법성은 기술 모델의 밖; 별도 전문가·사건별 판단.
2. 클라우드 제공자 실제 업로드/버전 기록/계정 보안/오프사이트 독립성은 사용자 운영 설정에 의존.
3. 권한 독립성·서명키 외부 보관·단일 Writer 전원 장애까지 완전 자동 증명 불가.
4. 실데이터로 AI 평가하지 않음; synthetic/golden benchmark와 제한된 승인 자료만.
5. 영구 무결함·MECE 수학적 완전성·100% 재현성은 주장하지 않음.

## Recursive review algorithm
(1) 모든 requirement_ID가 exactly one accountable domain을 갖는지 → (2) 각 domain invariant가 positive+negative test를 갖는지 → (3) 모든 negative에 fail-closed/rollback 경로가 있는지 → (4) 각 gate의 evidence가 candidate-bound인지 → (5) 실제 관측이 알림/피드백으로 전파되는지 → (6) feedback이 test/spec change로 귀착되고 (7) 사용자 영향효과가 확인되어 종결되는지.

**종결 조건:** 미연결 요구사항 0, orphaned scenario 0, P0 risk owner 부재 0, stale gate의 PASS 주장 0, 실제 수행 않은 테스트의 PASS 주장 0. 단 실행 테스트 0건인 Pre-TDD 상태는 별도 미완료로 표시한다.

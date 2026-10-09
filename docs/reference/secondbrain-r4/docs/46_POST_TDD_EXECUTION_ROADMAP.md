# 46. TDD 이후 실행 로드맵 / 완료 정의 / 반복관리

이 문서는 **R3 설계에서 future work를 완료했다고 주장하지 않는다**. TDD 시작 후 순서와 release/운영 성숙도를 단계별로 통제하기 위한 실행 계획이다. 각 단계는 독립적으로 멈출 수 있지만 Evidence 안전조건은 부분 생략하지 않는다.

| Milestone | 개발/검증 범위 | 산출물 | Gate & 종료 조건 |
|---|---|---|---|
| M0 | TDD infra / schema validators / config | 첫 RED→GREEN 기록, fixture test runner | G1/G2 기반 |
| M1 | Capture-only, single Writer, hashing, atomic seal | Evidence intake, commit receipts, fault tests | local evidence integrity PASS |
| M2 | Custody JCS, Provenance, Legal Hold, domain checks | event recorder, anchor verification, hold tests | custody/hold negative PASS |
| M3 | independent snapshot, restore, cloud-like simulator | recovery tool, restore reports, 2-device simulation | G4 on isolated synthetic root |
| M4 | Knowledge/Context/Memory/Index/Search | linked notes, ACL/temporal retrieval, rebuild | query/semantic eval baseline frozen |
| M5 | production/export, CLI, optional MCP/PeerHub/Obsidian | standalone core, adapters & end-to-end sample | G3 + G4 + export proof |
| M6 | supply-chain, build/distribution, canary | locked deps, SBOM, candidate manifest/attestation, release doc | G5 + G6 explicit approval |
| M7 | operations hardening, alarms, physical DR | operating SOP, recurring verify+backup+recovery | G7 observation baseline initiated |
| M8 | closed-loop maturity | defect RCA, added tests, release comparison, effectiveness evidence | repeated G7 cycle; measured results |

## 작업 카드 형식
각 변경은 `change_id`, `why`, `scope`, `invariant`, `user impact`, `requirements`, `risk`, `negative_fixture`, `acceptance_test`, `migration`, `rollback`, `owner`, `candidate_fingerprint`, `gate`, `after_observation`을 포함한다. TDD 실패를 먼저 수집하고 구현을 진행한다.

## Release 최소 정의
- MUST/NOT 모두 validated (자동/수동 증빙 혼합; 미측정 PASS 금지).
- 위험별 gate, P0 stop condition, 독립 restore/로컬 물리 데이터, privacy guardrails.
- Candidate ↔ code ↔ deps ↔ test catalog ↔ build artifact ↔ reviewer ↔ deployment logs hash 일치.
- release notes, legacy schema preservation, rollback/hold compatibility test.
- prod read/write 승인과 사용자 관측은 별도 의사결정.

## 반복 도식
`Incident / Need / Drift → Requirements/ADR → RED → implementation/GREEN → regression/security/DR → candidate+review → canary/deploy → observation → feedback closure or re-open → new requirements/tests`. 단순 pass 횟수는 성공이 아니다.

## Future phase scope control
추가 GraphDB, Always-on background agent, provider API, multi-writer coordinator, full forensic imaging, 자동 법률적 증거능력 판단은 default OUT OF SCOPE. 명확한 요구·측정된 이득·부담/위험 평가·별도 ADR 뒤 추가한다.

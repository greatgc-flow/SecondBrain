# 44. R2 재귀 감사 → R3 보완 / 위험 잔여

| Finding | R2에서 확인 | 심각도 | R3 조치 | 잔여 위험/판정 |
|---|---|---|---|---|
| F-01 | docs/02 두 Writer 동시 publish 암시 vs docs/16 one-writer | P0 design contradiction | docs/02 직접 정정, authority 우선규칙 | 실제 클라우드 충돌 실증 전 NOT VERIFIED |
| F-02 | feedback `Find→Fix→Verify` 개념만; 효과 검증·재발·종결 불명확 | P0 lifecycle | docs/33 state machine, 37 postmortem | KPI pilot 필요 |
| F-03 | release 후보와 test evidence commit/artifact binding 부족 | P0 trace | docs/35,40, release schemas | 서명·CI attestation 미실행 |
| F-04 | 취약점/SBOM/의존성/비밀정보 drift 대응 미연결 | P1 security | docs/38, scenarios | 실제 scanner/tool 정하지 않음 |
| F-05 | restore drill/PIT cloud sync·다중 writer 재난 회복의 주기·판정 부족 | P1 DR | docs/39 & 36 | 물리 드릴 NOT RUN |
| F-06 | retrieval 평가의 golden-set 버전/abstention/poisoning 재검증 부족 | P1 AI quality | docs/41 + corpus governance | 고위험 실제자료는 별도 승인 |
| F-07 | manual vs automated MUST 검증 구분 미흡 | P1 gate | docs/32,35 & test matrix | 운영자 승인 필요 |
| F-08 | 서로 다른 ADR-0010 두 파일 | P2 document governance | canonical 0010-JCS, old superseded | R2 history 보존 |
| F-09 | 운영 플레이북 예시 경로 제어문자(`path` + formfeed) | P2 text | docs/23 정정 | CLI는 설계 전용 |
| F-10 | Docs knowledge/release/ops 간 닫힌 교차표 미흡 | P1 MECE | docs/43, requirements+scenario catalog | 완전 무결성 보증 아님 |

## 하드 잔여 조건
RISK-A: 하나의 사용자가 원본·백업·event chain·signer key 모두 통제 → 외부 anchor/offline 별도 보관 또는 독립 검토 필요. Owner: operator; trigger: ERL-4 주장/분쟁/backup breach; revisit: 분기.
RISK-B: Cloud 2개 사용해도 하나의 동기화 오염·계정탈취·디스크 고장 공유 가능. Owner: operator; trigger: sync conflict/restore fail; revisit: 분기.
RISK-C: 법률 보존의 적법성·보존기간·삭제 요구가 충돌할 수 있음. Owner: data steward + 법률 자문; trigger: 실제 제출·hold release·data subject request; revisit: 사건별.
RISK-D: PeerHub/MCP/Engram/외부 AI spec 업데이트 시 실제 API 및 credential 상태 미확정. Owner: maintainer; trigger: 버전 상향/release; revisit: 매 변경.
RISK-E: 불완전한 원출처(스크린샷·재전송 파일)는 시스템 보존만으로 진정한 원생성 데이터를 만들 수 없음. Owner: data steward; trigger: 법률 제출/증거 확보; revisit: 각 자료.
RISK-F: 지금은 TDD 이전으로 코드/운영 계측/실물 복구를 증명하지 못함. Owner: maintainer; trigger: TDD 착수/G4/G6; revisit: 각 gate.

## 객관 검토 결론
**설계 단계의 지속 개선 루프는 '검증·효과판정'까지 연결되도록 명세됨.** 다만 전체 품질은 실제 failure-injection/restore/integration/운영 후속 관측 없이는 '완전'이라 말할 수 없음. 위험 없는 미래 시스템 또는 법률적 증거능력을 보장하지 않는다.

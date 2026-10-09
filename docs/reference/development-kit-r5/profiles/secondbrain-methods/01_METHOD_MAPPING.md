# 범용 v2에서 Second Brain으로의 상세 매핑

| 채택 방법론 | Second Brain 적용 | 처음 검증할 반례 | 소유 경계 |
|---|---|---|---|
| Spec→Code convergence | evidence ingest/commit→manifest→verify 1개 슬라이스부터 | commit receipt 없이 available 상태 | Brain Core |
| Bounded Agent Harness | PeerHub/CLI는 read-only 조사부터; Original/LegalHold는 수정 못함 | 메모리 요약 지시로 Vault mutation | policy+Brain adapter |
| Eval-Driven | 원본 식별/인용 정확도/거절정확도/시간일치·의견구분 별도 | 출처 없는 사실 확정 | Brain Eval adapter |
| Stochastic multi-trial | AI 요약·분류에만; 해시·봉인은 결정적 단일 시험 | 한번 성공했다고 유효성 주장 | Brain Eval adapter |
| Agent security | Vault·민감문서 외부모델 전송 deny 기본; 승인된 축약 context만 | 악성 PDF prompt가 이메일을 보냄 | auth policy |
| Independent review | evidence export hash/manifest 검증기는 모델과 무관 | AI 검사로 hash mismatch 묵살 | deterministic verifier |
| Progressive delivery | Brain에서는 버전된 Schema/CLI Migration + shadow read | 구버전 Vault 접근 실패 | release owner |
| Golden path | 폴더 Drop→deterministic seal→검증→index. cloud API 없음 | Drive placeholder를 local payload로 오인 | core ingest |
| Candidate provenance | 임시 CLI/engram/peerhub 버전과 후보 SHA 연결 | 일부 도구만 업데이트하고 구버전 테스트 사용 | release owner |
| Continuous improvement | 사용자 검색 실패→golden query→fix→효과 관측 | 법률 원본 자동 등록/전송 | Brain governance |

**금지**: 특수 Evidence 요구사항을 범용 Core 전체의 MUST로 격상하지 않는다. AI 평가를 법적 증거능력으로 주장하지 않는다. 원본의 취득 적법성과 진정성은 AI가 판정하는 항목이 아니다.

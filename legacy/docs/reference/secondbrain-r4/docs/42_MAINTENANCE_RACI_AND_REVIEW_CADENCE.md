# 42. 지속 가능한 운영: RACI-lite / 소유권 / 운영 가이드

## 역할은 사람/도구가 아니라 책임 계약
| Role | Accountable | AI/PeerHub 활용 | 반드시 사람 승인이 필요한가 |
|---|---|---|---|
| product owner | 범위/우선순위/위험수용 | 안건 요약 | 예 |
| maintainer | 이슈 triage/표준/traceability | 초안·교차검토 | 위험변경 예 |
| test owner | failing regression / negative suite | fixture 초안 | 후보 PASS 증거 필요 |
| release reviewer | candidate-bound G5/G6 승인 | 독립 결과 비교 | 예 (고위험) |
| operator | writer, backup, restore, access | 진단 보조 | destructive action 예 |
| data steward | 개인정보/보존/hold/knowledge correction | 추출 보조 | 사건 관련 변경 예 |

한 사람이 여러 역할을 수행할 수 있는 개인 개발 상황을 전제하지만 **동일 개인의 자체승인**이면 risk limitation을 표시. 가능하면 독립 동료/제3자 review, 없을 때 강화된 evidence logs+다중 관점 정적 리뷰로 보완. AI agent 합의가 independent human approval을 대체하지 않음.

## 운영 회고
- 일일: inbox/failed ingest/비정상 hash/hold/write-authority 경고.
- 주간: snapshot/backup/SLI drift/수집 트렌드, 실패 후 재시도 원인 분류.
- 격주: backlog triage + proposed improvements + root-cause/unclosed review.
- 매월: 포맷·버전/권한/법적 자료 보관정책(실제 정책 결정 필요)·full fixity 점검.
- 매분기: restore drill + schema migration dry run + postmortem action efficacy review.
- 반기: Engram·PeerHub·MCP/LLM 프로토콜/표준 업데이트 연구 및 status report.

## 사용자 사용성/비용
- '기능을 하나 추가하면 운영 부담·저장용량·인덱싱비·AI 비용이 얼마나 증가하는지' 비용/복잡도 예산으로 심의.
- `MAY` 기능(GraphRAG, always-on agent, external TSA)은 실제 개선 증거가 없으면 core로 승격 금지.
- 교착된 이슈는 일관된 reason: `waiting_external`, `not_reproducible`, `infeasible`, `awaiting_human`, `deferred_with_trigger` 등으로 관리.
- 운영 문서는 GUI/CLI 두 접근법이 가능한 부분에서 예시 포함; 단, 구현 전 명령 예시는 DESIGN ONLY.

## Core boundary
Second Brain Core가 소유해야 하는 것은 ingest/verifier/policy/record/search 최소 기능. PeerHub integration/Obsidian/Graph/Cloud API/TSA는 extension/optional. 다른 OSS로 교체할 수 있도록 표준 파일 포맷, stable URI, contract tests를 유지한다.

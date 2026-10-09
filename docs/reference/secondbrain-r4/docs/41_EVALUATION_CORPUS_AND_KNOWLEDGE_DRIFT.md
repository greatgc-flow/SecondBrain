# 41. AI/검색/Knowledge/기억 품질 개선 루프

## 평가셋 구조
`golden_cases` 중 Test-only synthetic cases + reviewer-authorized public corpus. 실제 비공개 사건자료를 자동으로 모델/provider에 전송하거나 공개 fixture로 저장하지 않음.

각 case: `case_id`, query/expected behavior, time-scope, actor permission, evidence id/synthetic URI, answer requirements, abstain condition, expected citations, negative contradiction, sample group, risk tier, cost/time limits, reviewer, dataset revision.

## 범주 (서로 다른 실패 원인을 포괄)
A. source identification / original vs derivative; B. single-hop citation; C. multi-hop relation; D. stale/timestamp; E. contradiction and superseded fact; F. ACL/hold; G. prompt injection; H. missing evidence abstention; I. unicode/ocr/page label; J. retrieval drift after reindex; K. poisoning and embedding leakage; L. model/adapter timeout/unknown.

## Metric calculation
- `retrieval_recall@k`: query별 relevant object 집합 대비 top-k hit; human relevance label revision 관리.
- `citation_precision`: 근거 있는 citations / 전체 citations, 인용 span·페이지·timecode 맞는지 별도 score.
- `answer_grounding`: 정답 주장들 중 support evidence 확인 비율. 불확실/근거없음과 hallucination 구분.
- `temporal_accuracy`: 각 valid_at query에서 기간을 맞춘 사실 주장 비율.
- `abstention_accuracy`: no-evidence/forbidden query에 합당하게 답하지 않은 경우 비율.
- `privacy_leak_count`: 접근 불가 source가 context/retrieval/result에 등장한 수, 허용치 0.
- `cost_per_query/p95_latency`: model version과 샘플 크기 조건 하에 비교.

## Evaluation governance
- Model/prompt/embedding/parser/memory format index 변경 전 baseline을 freeze하고 동일 corpus에 반복 평가; 무작위성이 있는 모델은 여러 실행/분포 보고.
- Test leakage 차단: 개발 fixture와 hidden holdout 분리. 평가셋 피드백이 training input으로 섞이면 오염 가능성 기록.
- human adjudication: 고위험 사건 판단/증거능력 단정 금지; 불일치/누락/incomplete evidence 별도 표기.
- AI score 상승만으로 릴리스 결정 금지. Integrity/privacy/hold hard stop은 tradeoff 불가.
- 실패 사례를 *비민감 축약 fixture*로 만드는 변환과 승인 기록을 남김; 원문 비밀 사건정보를 바로 저장하지 않음.
- `EFFECT_OBSERVED`는 real usage sampling + pre/post 비교 및 adverse-effect 조사가 있고 기간·모집단이 유효한 경우만.

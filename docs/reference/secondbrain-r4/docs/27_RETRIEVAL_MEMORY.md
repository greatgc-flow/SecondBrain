# 27. Knowledge / Context / Memory / Retrieval 계약

## R2 domain separation
- Evidence = bytes/custody/source + 관찰 사실, immutable-by-policy.
- Knowledge = 사람이 승인해 정제·연결한 장기적 명제와 방법론.
- Context = PARA Projects/Areas/Resources/Archives, 업무별 현재 묶음(중복 저장보다 stable URI reference).
- Memory = 검색을 돕는 materialized/derived records (verified facts는 Evidence/Knowledge까지 링크, 무근거 memory truth 금지).
- Search indexes = `%LOCALAPPDATA%` 재생성 가능. FTS/semantic/graph index가 섞여도 SSOT가 되지 않는다.

## Retrieval process
Query normalization → ACL/sensitivity/hold filter → structured metadata & temporal filter → BM25/FTS → optional vectors → provenance expansion/explicit links → reranking → evidence pack → human/AI response.

## Response envelope (concept)
```
query_id
actor_scope
as_of
evidence_refs[{uri, sha256, source_type, verified_at, page_index, page_label,
               paragraph_or_time_span, extraction_confidence, view_type}]
claims[{text, epistemic_tier, supported_by_refs, temporal_scope}]
contradictions[]
limitations[]
answer_or_abstention
```
- False-confidence 금지: citation/근거 누락 시 unanswered 또는 uncertainty.
- Time-scope: `valid_at`과 `observed_at`을 분리; 과거 시점 정보가 '현재' 사실로 승격되지 않음.
- Multi-hop linking은 optional graph index. 모든 answer는 raw source/evidence record까지 추적.
- citation은 단순 PDF 파일명에 그치지 않고 실제 인용 위치(page/text span/timecode)를 보유.
- 각 processing 단계의 query/score/log는 민감도 정책으로 logging/redaction 제한.

## Memory update
새 내용이 과거 내용과 다르면 overwrite보다는 valid interval·supersedes link·source status를 기록. 자주 바뀌는 facts의 freshness TTL/revalidation 선택 가능. 원본 불일치 시 *fact correction*과 *original mutation*을 혼동하지 않는다.

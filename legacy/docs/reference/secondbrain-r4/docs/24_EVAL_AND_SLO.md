# 24. 품질 평가 및 선순환 피드백

## 정확성(정량/정성)
- `source_fixity_coverage`: ingested sealed original 중 검증 가능한 SHA-256 비율.
- `acquisition_provenance_completeness`: source/actor/time/method 정보 채움의 비율; null/unknown은 사실대로 표기하고 별도 집계.
- `full_lineage_coverage`: 제출물의 모든 구성 요소가 Vault object로 역추적 가능한 비율.
- `verified_backup_coverage`: ERL3 claim 중 독립 snapshot receipt가 유효한 비율.
- `custody_chain_verification`: event stream별 hash chain/anchor 검사 PASS 비율.
- `orphan_object_count`, `conflict_copy_count`, `nonwriter_mutation_attempt_count`, `quarantined_intake_count`.
- `retrieval_recall@10`, `citation_precision`, `temporal_fact_accuracy`, `abstention_accuracy`, `unauthorized_egress_count`.
- `snapshot_restore_drill_success`, `rebuild_equivalence`.

## 운영적 선순환
Find problem → tag category/source/impact → minimal reproducible scenario → update failing acceptance case → fix impl/config/schema/knowledge → verify unaffected cases → reindex/backup if appropriate → record lessons in **Second Brain governance**, PeerHub feedback는 선택적 투영.

## 권고 게이트
- MUST/NOT: pending 테스트 0건이어야 release candidacy. 미구현은 미완료로 표시.
- critical incident 또는 unauthorized egress 1건이라도 있으면 release hold.
- 최종 ERL 법률 적합성은 점수가 아니라 evidence receipt 충족여부로 판정.
- Baseline/목표 수치 및 허용 지연은 pilot 측정 후 확정: 임의 100% 달성 표시 금지.

**아직 테스트 결과가 없다.** 이 문서의 KPI와 지표는 측정 계획이지 현재 달성 성능이 아니다.

## R3 closure note
이 문서의 `Find→Fix→Verify`는 개념 흐름이다. 실제 완료 정의·성과 후속검증·재개 조건은 `docs/33_FEEDBACK_LOOP_STATE_MACHINE.md`, `docs/36_SLO_OBSERVABILITY_AND_ALERTS.md` 및 `docs/40_RELEASE_EVIDENCE_AND_DEPENDENCIES.md`가 규정한다. 측정되지 않은 KPI를 100%라고 보이지 않는다.

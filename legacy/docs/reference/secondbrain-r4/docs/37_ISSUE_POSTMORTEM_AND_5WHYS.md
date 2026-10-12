# 37. 사고·결함·개선 5 Whys runbook

## 분류
- `INCIDENT`: 실제 보안/무결성/가용성/오동작 영향이 있음.
- `DEFECT`: 기대 계약과 구현이 불일치 (실제 사고 유무 무관).
- `IMPROVEMENT`: 현재 계약은 만족하지만 측정 기반 품질/비용/사용성 개선 여지.
- `RESEARCH_DRIFT`: 표준/외부 제품/API/모델 변동으로 위험 발생.
- `CONTENT_CORRECTION`: Evidence 원본 mutation 없이 사실 주장/Knowledge 수정.

같은 이슈가 여러 축에 영향을 미쳐도 하나의 primary owner+primary class를 두고 related facets를 나열. 단일 인과 사슬이라고 가정하지 않고 5 Whys 외에 fault tree/trigger/전파조건 검사. '사람이 실수했다'를 최종 근본원인으로 남기지 않는다.

## Incident response
1. **Detect**: 시각(UTC+offset), 증상, 운영 환경, 관측근거 digest.
2. **Contain**: writer freeze, egress disable, cloud sync pause if justified; 자동 정리/원본 삭제 금지.
3. **Preserve**: 관련 원본, receipt, 설정, non-sensitive logs, tamper evidence; 개인정보 접근제한.
4. **Scope**: 언제부터/어떤 evidence_id와 data subject까지 영향이 있는지; 불명은 unknown.
5. **Explain**: direct cause, contributing conditions, 5 Whys, evidence for/against hypotheses.
6. **Correct**: change proposal/ADR/권한·데이터 migration impact, 테스트 RED→GREEN.
7. **Verify**: 병렬재현/돌발상황/rollback, release candidate evidence.
8. **Observe**: 사전에 정한 관측 기간/코호트/재발트리거, 운영자 확인.
9. **Close**: 재발 방지 규칙/tests 문서화, action owner·기한·검증 evidence 반영.

## 실패 루프 별 예제
- Sync conflict: 두 장치에서 다른 원본 관측 → writer freeze → conflict two versions both preserved → incident → regression split-brain simulation → canary → observe repeat rate.
- False ERL-3: independent backup 검증 없음 → claim corrected (절대 원본 덮어쓰지 않음) → negative ERL scenario 추가 → restore drill → audit report.
- Prompt injection: PDF 내부 지시가 외부 업로드를 시도 → egress blocked → reduced disclosure → adversarial corpus test → policy prefilter before retrieval.
- False citation: page count but wrong label → original/derived mapping 확인 → deterministic page index contract test → sampled human review of PDF output.

## 변경 종결 체크
`incident_id`, `root_cause_id`, `affected_requirements`, `added_tests`, `candidate_digest`, `release_id`, `before`, `after`, `monitor_until`, `reviewer`, `decision`. 관측되지 않은 개선은 `AWAITING_EFFECT` (CLOSED 아님). 위험수용이라면 acceptor와 재점검 시간 포함.

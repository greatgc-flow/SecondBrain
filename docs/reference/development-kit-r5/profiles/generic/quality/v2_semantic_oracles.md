# 스키마만으로 충분하지 않은 cross-field oracles (모두 PLANNED_NOT_RUN)

| ID | 자료 | 반드시 검증할 의미 불변식 | 실패 예시 |
|---|---|---|---|
| SEM-01 | spec-convergence | satisfied_task_ids ⊆ required_task_ids, PASS ⇒ 모든 required satisfied ∧ unresolved_must=[] | 빠진 작업인데 PASS |
| SEM-02 | agent-execution | spent_units ≤ budget_units; A3/approved action은 별도 유효 approval receipt | 승인 없이 배포 |
| SEM-03 | eval-result | trials = successes + failures; PASS ⇒ configured threshold; grader/env/candidate 같음 | 3 시행에 4 성공 |
| SEM-04 | eval-case | HIGH/CRITICAL은 human or deterministic code audit 필요; MODEL-only 절대 충분치 않음 | AI 자기 승인 |
| SEM-05 | agent-handoff | resume source_sha = HEAD 또는 명시적 reconciliation 후만 재개; verified_commands는 실행 receipt reference | 오래된 SHA 사용 |
| SEM-06 | tool execution | action/args digest = approval receipt scope; timeout uncertain에 blind retry 금지 | 권한 token 교체 실행 |
| SEM-07 | telemetry | restricted payload/secret 원문이 logs/traces/embedding에 없을 것 | prompt 가감없이 trace export |
| SEM-08 | delivery | candidate fingerprint & artifact digest match; stale gates ⇒ NO-GO | 오래된 CI pass 재사용 |
| SEM-09 | research_decision | ADOPT/ADAPT에 owner & review triggers 포함; WATCH/REJECT는 기본 runtime dependency 금지 | 거부된 GraphDB 강제 |
| SEM-10 | feedback | CLOSED ⇒ released + measured effect + regression oracle; never test-only | green으로 종료 |

주의: 이 문서는 **테스트 계획**이며 실제 성공 또는 runtime 검증 결과가 아니다. Python/JSON Schema만으로 cross-record invariants를 모두 강제할 수 없다.

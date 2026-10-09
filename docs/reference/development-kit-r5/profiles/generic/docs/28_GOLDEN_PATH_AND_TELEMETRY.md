# 28. 경량 Golden Path / 계측 계약

**금지할 과설계:** IDE portal, Kubernetes, Backstage, 분산 tracing system을 소규모 CLI의 필수 요소로 만들지 않는다.

### Golden path
`read README → select profile → configure sample → run design_lint → choose first vertical slice → TDD RED/GREEN → local contract+regression → candidate gates`를 one-command 또는 복제 가능한 몇 단계로 만든다. 프로젝트 예제는 실제 본문에 복사 가능한 기본값만 넣으며 비밀/개인정보 내장 금지.

### 관측
Core는 안정적 자체 event ID와 `correlation_id, task_id, candidate_id, outcome, duration, error_code, unit, data_class`를 노출(필요 시). OpenTelemetry exporter는 선택 adapter. GenAI semantic conventions는 불안정한 필드가 포함되므로 버전 지정하여 매핑하고 내부 사건 ID와 분리한다.

### 인간 중심 지표
사용자 작업 완료율/실패/복구와 delivery throughput/instability, agent cost/latency, 인간 검토 시간, 비밀 노출 수를 분리한다. 대시보드 점수 하나로 품질 보장 주장하거나 개인 개발자 성적을 매기지 않는다. 사용자가 얻은 결과가 증가하지 않으면 자동화 효과는 미확인이다.

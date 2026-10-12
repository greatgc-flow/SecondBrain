# 14. 운영·진단·SLO·비용

사람 관점: task success rate, 도움말/입력 실패율, 수행 지연, 만족도. 시스템: latency P50/P95/P99(해당 시), error budget, integrity failures, recovery RTO/RPO(영속 서비스), CPU/IO/quota/cost, secret leaks. 프로세스: DORA change lead time/deployment frequency/failed deployment recovery time/change fail rate/rework rate.

OpenTelemetry 표준 이름은 플랫폼/버전별 안정성 상태를 검토하여 필요한 것만 사용. 사용자 텍스트, 토큰, 비밀, 민감원문은 trace/span/log/feedback에 그대로 저장하지 않는다. `diag`는 ReadOnly 관측과 `refresh`(외부로부터 새 증거 수집)를 분리한다.

Runbook 예: 설치/업데이트/health/backup/restore/rollback/incident/pause/disable. 비영속 CLI라면 24h 모니터링이나 RPO가 필수는 아니다. 모니터는 시스템만 관찰하며 자동 권한 변경·파괴적 복구하지 않는다.

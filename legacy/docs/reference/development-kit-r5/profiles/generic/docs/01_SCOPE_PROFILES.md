# 01. 제품 유형·프로파일

적용 조건은 `config/project.example.toml` 복사본에서 선택한다. CLI 명령이 '내부 개발자만 쓰는 스크립트'이면 공개 CLI 계약(`CLI_PUBLIC`)을 N/A로 둘 수 있지만 명시 기록한다.

| 제품 유형 | 일반적 추가 조건 | 설계 선택 |
|---|---|---|
| CLI | CLI_PUBLIC | 출력 stderr/stdout 구분, exitcode, recursive help |
| 라이브러리 | API compatibility | 언어/ABI/semver, dep contract |
| 서비스/API | NETWORKED, STATEFUL(해당 시) | 인증/인가, retry, idempotency, telemetry, SLO |
| 데스크톱 | STATEFUL(해당 시) | 권한/설치/업데이트/복구/OS 매트릭스 |
| 데이터 파이프라인 | STATEFUL, NETWORKED(해당 시) | 재실행성, lineage, idempotent checkpoint |
| AI 에이전트/확장 | AI_ENABLED | provider egress, tool authorization, cost/timeout, golden eval |
| 파일 동기화형 | CLOUD_SYNC, STATEFUL | 충돌/멀티 writer/백업 구분 |

유형 하나를 선택해도 조건은 여러 개 참일 수 있다. 예: AI 기반 서비스=NETWORKED+STATEFUL+AI_ENABLED. 원본 증거, 의료 등 규제 도메인은 **별도 프로젝트 특수 프로파일**로만 확장한다.

### 최소 MVP
처음부터 Graph DB/자체 plugin framework/다중 agent/server mesh가 필요한 것은 아니다. 사용자 시나리오와 측정 가능한 비즈니스 효용에 의해 증명되기 전까지 연기한다. 구현 없는 설계 파일은 프로젝트별로 정리하여 전달한다.

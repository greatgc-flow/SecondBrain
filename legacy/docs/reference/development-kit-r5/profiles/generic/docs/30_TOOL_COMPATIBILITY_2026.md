# 30. Engram·PeerHub·Spec Kit 실사용 호환성 경계

Engram v3.7.0 릴리스(2026-10-03), PeerHub v0.12.4 릴리스(2026-10-09) 참고. **본 패키지는 두 CLI를 설치·호출하지 않고 사용자가 연결을 선택할 때만 어댑터 호환성 검사**한다.

- Engram: 환경·tool lifecycle 관리. 범용 개발 메모리·Gates SSOT가 아님. `engram help` 및 해당 설치 버전을 먼저 확인.
- PeerHub: Peer/Stream/Record/Offset Core와 확장 계층의 현재 구조. 장기 상태·평가/증거 원본은 범용 패키지가 canonical 관리. `peerhub --help`/`--version` 및 manifest 체크 후 adapter 사용.
- CLI 단축명, 모델 ID/쿼터, native session resume/steer는 시점별 변한다. 구현에서는 discovered capability만 사용하고 지원 불가 시 degrade/stop.
- Spec Kit: 도구 설치는 선택. `spec`, `plan`, `tasks`, `converge` 사고방식만 고정. README에 표시된 `specify` 실제 옵션은 버전별 확인.
- OpenTelemetry GenAI: status=Development인 규칙을 stable이라고 주장하지 말고 telemetry mapping을 versioned adapter로 둔다.

**공통 TDD/평가 Gate**는 제품 소유이며 다른 CLI/Agent의 성공 로그를 그대로 복사하여 성공으로 승격하지 않는다.

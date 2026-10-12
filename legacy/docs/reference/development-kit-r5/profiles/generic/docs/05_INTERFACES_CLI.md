# 05. I/F 계약 표준 (CLI · 라이브러리 · 네트워크 · 이벤트)

## 공통 envelope
입력: `operation`, `request_id`, `contract_version`, `principal`, `payload`. 출력: `status`, `result` 또는 `error`(안정적 code, retryable, user_message, correlation_id). 시간/비밀/실제 경로를 공개 envelope에 무조건 넣지 않는다. JSON 계약은 의미적 도메인 validator를 대체하지 않는다.

## CLI를 공개하는 제품만
`tool [global-options] <group> <action> [args]`. 루트 도움말과 각 하위 help, 예제, 오류 exitcode 일관성. 대화형/상태변경 명령은 `--dry-run`/`--apply` 같은 preview/commit을 명시하며 자동화 출력 `--json`은 stderr 로그와 분리한다. 미지원 명령은 성공 종료 금지.

**Exit code 기본 권고**: `0` success; `2` usage/config; `3` verified operation failure; `4` uncertain/reconciliation needed; `5` denied/security; `130` user interrupt. 기존 ecosystem 호환성이 우선이면 다른 코드를 사용할 수 있으나 계약을 고정한다.

## API/메시지
networked 호출은 deadline, idempotency, retry-after, cancellation, pagination, version negotiation, backward compatibility, correlation을 정의. request-id는 입력 fingerprint와 묶어야 하며 같은 키+다른 payload는 conflict. non-idempotent side effect는 timeout 이후 *결과 불명*으로 반환한다.

## 확장 manifest
`id`, `version`, `entrypoint`, optional dependencies/capabilities. 알 수 없는 필드 기본 거부 또는 버전 정책으로 검사. PeerHub 실제 extension 형식에 직접 결합하려면 해당 릴리스의 schema 확인 후 별도 adapter를 작성; 이 문서는 범용 예시일 뿐 PeerHub manifest 구현 스펙은 아니다.

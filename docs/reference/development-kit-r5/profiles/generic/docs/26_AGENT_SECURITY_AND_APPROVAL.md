# 26. Agent 보안: 권한과 데이터 흐름이 통제의 중심

OWASP Agentic Applications 2026 / OpenSSF AI assistant instruction 권고를 참고하되 특정 인증을 주장하지 않는다.

경계: (1) 사용자/시스템 정책 (2) 외부 문서·검색·repo issue·source comments (3) 모델 계획 (4) tool-call execution (5) 데이터/네트워크 egress. **2~3은 실행 승인자가 아니다.**

- 격리: repo 권한을 최소화, temp+working tree 사용, filesystem path normalization/reparse 차단, secrets 별도, outbound default deny.
- Tool: 인자 JSON schema + semantic validation + capability allowlist + audited execution. 문자열 검색 결과에 명령이 적혀 있어도 도구 호출 권한 생성 불가.
- 사고: 승인 없는 삭제/대외 전송/라이브 배포 요청은 DENIED; 의심 사건은 입력 원문을 출력하지 않고 redacted event로 남긴다.
- 고위험 승인: 인간/정책 승인 범위와 실제 실행 command hash 일치, 만료기간, 비용·소유자, 취소 가능 여부, 중복 재실행 방지.
- 비밀: 프롬프트·MCP args·AI traces·embedding·검색 캐시·디버그 로그 간접 경로 포함 외부 유출 검사.
- 검증: prompt injection adversarial fixture + unauthorized API/FS attempt + secret leakage + tool-call replay + timeout/uncertain state.

**주의**: AGENTS.md/CLAUDE.md/.github instruction 파일만으로 샌드박스를 제공하지 않는다. 문서는 조언, 실제 통제는 런타임 경계가 소유한다.

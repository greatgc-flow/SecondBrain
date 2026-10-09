# 13. 실측 테스트 T3/T4 — 명확한 승인·비용·증거

**현재 미실행 (NOT_RUN)**. 이 문서는 실행 가능한 계획이며, 테스트가 실행됐다는 주장이 아니다. CI/사용자 기기에 비밀키를 자동 배포하지 않는다. 시크릿·민감한 원본은 샌드박스 밖으로 전달하지 않는다.

| Tier | 실제 조건 | 승인/비용 | 성공 증빙 | 실패/중단 조건 |
|---|---|---|---|---|
| T3 OS/path | Windows 10/11 + Linux, 한글/공백/장경로/권한/심볼릭링크 | 로컬 관리자 승인 | 커맨드, exit, 환경/빌드 SHA | 원본 변경·예상치 못한 권한 요구 즉시 중단 |
| T3 Cloud | OneDrive/Google Drive **테스트 계정만**, 완전 로컬 동기화 | 계정/스토리지 비용 확인 | sync→반례→독립 snapshot→full restore 후 해시 비교 | 두 writer나 데이터 손상/결손 발견 시 중단 |
| T3 crash | 강제 중단/동시 입력/백업 손상/LegalHold | 격리 폴더 | 재실행 idempotency, recovery ledger, 미보존 0 | 원본 덮어쓰기/법적보존 우회 금지 |
| T4 Agent | Codex/Claude/AG 실계정 및 PeerHub adapter | **명시적 opt-in**, token/비용 상한, 요청 수 | provider/model/version, session, prompt hash, usage, cost estimate, eval result | 할당량 초과·정보반출·예상비용 초과 즉시 중단 |
| T4 AI eval | 정답/반례/abstention/시간정보/프롬프트 인젝션 | 데이터등급 승인, 익명 synthetic 우선 | baseline vs candidate, 신뢰구간/실패 세트 | 개인정보 입력/근거 없는 증거 확정 금지 |

시험 기록 최소 레코드: `test_id`, `candidate_git_sha`, `build_sha256`, `config_sha256`, `platform`, `provider_version`, `model`, `dataset_revision`, `started/ended`, `requests`, `tokens`, `cost_currency`, `cost_estimate`, `evidence_uri`, `result`, `reviewer`. 미측정치는 `UNKNOWN`, 미실행은 `NOT_RUN`, 오래된 관측은 `STALE`로 구분한다.

**게이트:** T3/T4가 반드시 필요한 시나리오는 해당 환경에서 **해당 릴리스 후보 바이트를** 테스트하기 전에는 NO-GO. 가용성/효과 측정 후 문서/요건/테스트를 갱신하며, 개선 건을 종료하지 않는다.

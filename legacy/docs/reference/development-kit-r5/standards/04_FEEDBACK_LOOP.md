# 04. 실제 CLI와 일치하는 닫힌 피드백 루프 (R5)

**원칙: 성공 선언은 코드 수정보다 늦어야 한다.** 사용자 관찰 → 재현/반례 → 5 Whys → 최소 개선 → RED/GREEN/회귀 → 릴리스 후보 → 실제 관측 → 독립적 확인 → 교훈을 정본 요구/테스트에 환류. 근거가 부족하면 `OPEN`으로 유지한다.

실제 지속 상태는 **세 개만** 존재한다. `OPEN → CLOSE_REQUESTED → CLOSED` (재발 시 `CLOSED → OPEN`). `TRIAGE`, `FIXED`, `OBSERVING`은 **진행 이력의 내용/태그**이지 별도 상태값이 아니다. 과거 문서에서 여섯 단계를 상태값으로 나열한 경우 이 문서가 우선한다.

| EVENT | 사전 조건 | 효과 | 쉽게 쓰는 명령 |
|---|---|---|---|
| CREATED | 고유 ID | OPEN | `feedback add --kind task|bug|error|incident|idea|lesson|question` |
| NOTED | OPEN 또는 CLOSE_REQUESTED | 진행/오류/증거/교훈/결정 추가, 상태 그대로 | `feedback note <ID> --kind progress|error|evidence|lesson|decision --note "..." [--ref ...]` |
| CLOSE_PROPOSED | OPEN/CLOSE_REQUESTED | CLOSE_REQUESTED | `feedback propose-close <ID> --release ... --regression ... --observation ... --lesson ... --evidence ...` |
| CLOSE_APPROVED | CLOSE_REQUESTED + 다른 reviewer 문자열 | CLOSED | `feedback approve-close <ID> --reviewer ... --evidence ...` |
| REOPENED | CLOSED | OPEN | `feedback reopen <ID> --reason ...` |

`feedback show <ID>`: 전체 event history. `feedback verify`: 유효 이벤트 순서/해시 체인/상태 전이 정적 검사. `feedback list --json`: 간단한 AI용 상태 목록. ID/시각/진행 상태/근거 ID를 기록하되 **기밀 원문·API키·개인정보를 note에 넣지 않는다**.

**보안/동시성 한계:** JSONL 파일 추가는 O_EXCL 잠금과 fsync를 쓰는 **로컬 단일 Writer**용이다. 동기화 폴더의 다중 PC 트랜잭션 보장 없음. 오래된 잠금 파일은 실행 중인 작성자가 없고 원본 백업 확인 후 수동 처리. 해시 체인은 국소적인 변조를 발견하지만 작성 권한자가 전체 로그와 해시를 재작성하면 독립 검증 없이 탐지할 수 없다. 리뷰어 ID는 실제 인증 시스템이 아니며, `CLOSED`는 *사람이 제출한 검증 주장*이지 객관적 현장 실측의 암호학적 증명은 아니다.

**보존/복원:** `.kit_state/`는 배포 ZIP 및 정적 Manifest에서 제외된다. 작업 기록을 장기간 유지하려면 주기적으로 별도 버전 백업하고, Git issue/내부 이슈 시스템을 공식 기록으로 선택했다면 관련 URL을 `--ref`에 넣는다. 수집 기록을 클라우드에 놓을 경우 동시 편집 금지와 백업 검증이 필요하다.

**Done 정의:** ① 현상·원인·영향 ② 요구/설계 수정 ③ 실패·회귀 테스트 ④ 후보 산출물 digest ⑤ 실제 운영 관측/롤백 확인 ⑥ 교훈 및 재발 조건 ⑦ 독립 리뷰. 생략되는 경우에는 이유·한계·면책이 아니라 **OPEN** 기록으로 남긴다.

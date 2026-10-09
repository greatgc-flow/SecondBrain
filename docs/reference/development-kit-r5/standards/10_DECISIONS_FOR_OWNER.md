# 10. 사용자 결정이 필요한 것만 — 제안 기본값 포함

| 결정 | 가장 단순한 권장안 | 미결 시 행동 |
|---|---|---|
| DevKit 전용 Git repo/버전/배포 | 우선 ZIP으로 유지; 제품 구현 후 별도 repo 결정 | Git push 없음 |
| Second Brain 저장소 | OneDrive 또는 Google Drive **하나만 Primary**, 나머지는 immutable snapshot backup | 구성만 설계 |
| 작성자/장치 권한 | PC 1대 authoritative Writer; 나머지 읽기 또는 수집/요청만 | 실제 live sync 금지 |
| Evidence timestamp/legal hold | 중요한 법률 자료에만 ERL 강화 및 독립 검증 | 전문가 감정 대체 주장 금지 |
| Agent 개인정보 및 예산 | synthetic 우선, 기본 외부송신 거부, 한도와 승인 후 실측 | T4 NOT_RUN |
| 외부 모듈 | stdlib 유지, 전문 표준은 검증된 모듈 도입(예 `jsonschema`, `ExifTool`, `ffmpeg`) | 초기에 불필요 구현 금지 |
| 패키지 오류 이력 | 단일 로컬 Writer + 주기적 별도 이력 백업; 조직 규모면 Issue tracker SSOT로 전환 | 분산 writer 지원 주장 금지 |
| 실제 제품 release | TDD/실측/후보별 build proof 확보한 다음 PyPI/winget의 대상만 선택 | 정식 릴리스 금지 |

작은 프로젝트에서는 모든 선택지를 구현하지 않는다. **비용/복잡도보다 검증된 사용 시나리오의 필요성이 높을 때만 승격**한다.

# 23. 개인 Windows/OneDrive/Google Drive 운영 플레이북

## 초기 설정 (인터페이스 예시; 구현 전)
1. primary를 OneDrive *또는* Google Drive Mirror 실제 로컬 폴더로 선택. Google Drive Stream/OneDrive online-only를 사용하면 파일 hydrate 완료 확인이 먼저다.
2. Secondary는 다른 provider의 스냅샷 전용 별도 폴더. Secondary 경로는 Primary 하위가 아니며 양방향 sync 겹침/순환 금지.
3. 지정 Writer PC 1대 결정. 다른 PC는 장치 ID별 Capture-Only Drop 사용.
4. 실제 `SECOND_BRAIN_ROOT`, `SECOND_BRAIN_LOCAL_STATE`, `brain_id`, `device_id` 생성/배치. Runtime/SQLite는 Cloud 밖.
5. 중요한 법률 원본을 먼저 가져오기 전에 **백업 restore drill과 실패 알림을 먼저 검증**.
6. Obsidian은 Knowledge/Context만 기본 편집하고 Evidence는 read-only view. 별도 플러그인이 Vault를 자동 reformat하는 경우 비활성.

## 일상
- 자료 수집 → Drop/<device_id>/<capture_id> → Writer source/manifest/hash 안정화 → seal → observation → source receipt/ERL 계산.
- 자료분류 → 증거의 사실적 주장·추론·사실검증 분리 → Knowledge 승격 승인.
- 분기마다 restore drill, hold 목록 및 퇴역·보존정책 재검토. `Cloud sync completed`를 증거 seal과 혼동 금지.

## 장애 매뉴얼
- `hash mismatch`: affected object 격리/로깅, 백업 원본을 덮어쓰지 않고 *독립 사본*으로 복원/조사.
- `duplicate/conflicted copy`: 양쪽 해시·원출처/수정이력 별도 보존. 작성자가 결정.
- `lost Writer PC`: 모든 장치 canonical write 정지 → verified snapshot 확인 → 새 Writer 승인/epoch 증가 → reconcile. 오프라인 옛 Writer 재접속 전 차단.
- `cloud provider 장애`: 로컬 bytes 유지 여부 확인; 새 capture는 로컬 queue, 외부 동기화 성공이라고 기록하지 않음.
- `ransomware`: sync 중지, 별도 보관 snapshot 확보, 새 root로 검증 복원. 동일 위치에서 감염 파일 overwrite 금지.
- `original only screenshot`: source_fidelity 낮음을 유지; 원 데이터가 나중에 들어오면 새 observation/evidence link로 연결하고 예전 원본을 교체하지 않음.

## CLI Design Intent (아직 동작하지 않음)
```
brain doctor --json
brain intake import C:\path\file.pdf --capture-id <id>
brain ingest inbox --writer-epoch <epoch>
brain evidence verify <id> --json
brain evidence lineage <id> --json
brain evidence report <id> --scope acquisition,custody,fixity
brain snapshot create --dry-run
brain restore plan --snapshot <id>
brain export evidence <id> --format bagit --dry-run
brain policy egress check <id> --provider <provider>
brain writer status
brain writer handoff --dry-run
```
`--json` envelope와 exit codes는 `docs/06_INTERFACES.md`의 R2 확장을 참고. Windows PowerShell 버전에 특정 의존성 없는 cli 설계.

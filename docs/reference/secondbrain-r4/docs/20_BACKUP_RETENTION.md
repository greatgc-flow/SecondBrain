# 20. Backup / Snapshot / Restore / Retention / Hold

## 보호 목표
- **Primary**: 단일 Writer가 관리하는 증거/지식 canonical tree. 예: OneDrive 실제 로컬 폴더 또는 Google Drive Mirror.
- **Secondary**: 다른 드라이브의 dated *read-only snapshot*; 업로드된 최신 live copy와 혼동 금지.
- **Tertiary 권고**: 오프라인/분리 계정 보관, 가능하면 불변 스냅샷. 두 provider 계정이 동시에 탈취될 수 있다는 공통고장 고려.

## Snapshot protocol
1. 보존할 canonical 파일 집합을 enumerated snapshot boundary로 고정. running ingest는 commit receipt 기준 선별.
2. `data/` 임시 위치에 복사; SHA256+SHA512 manifest와 `snapshot.json` 생성 (total bytes/file count/refs).
3. Snapshot storage 자체의 바이트들을 source manifest와 비교; 파일 누락·변경 시 `FAILED`.
4. 마지막에 `complete.receipt.json` publish. 실패/중단된 staging은 restore 후보가 아님.
5. Backup success는 '로컬 secondary 경로 검증'까지를 뜻한다. **실제 cloud 업로드 완료**는 provider UI/별도 offline confirmation이 없으면 `sync_state=unverified`.
6. 외부 저장소/백업의 live sync에 의한 소급 삭제 방지: snapshot은 새 timestamp immutable naming, admin 권한/retention 보호가 필요; overwrite 금지.

## Retention
- Evidence original/custody/provenance/hold/data lineage는 기본 indefinite unless explicit lawful policy. 기간을 임의로 법정 기준이라 주장 금지.
- `Legal Hold` 활성 범위는 즉시 파기 금지, matter/context scope에 신규 evidence가 유입되면 **hold propagation** 검사.
- 잊어버릴 권리/개인정보 삭제 의무 등 충돌 시 법률 자문과 조직 정책 검토 필요; 무조건 무기한 보관은 정답 아님.
- 데이터 삭제는 관련 immutable backup·derived indexes·export copies·disclosure 목록까지 영향을 평가. `destroy_evidence` 기본 UI 숨김 + approval + audit.

## Restore
- `restore plan`: 정상 backup 선택, manifest/anchor chain/hold/현재 root 상태 비교, 예상 변경 파일/ID 충돌/공간 추정/되돌릴 경로 출력. 실제 mutation 금지.
- `restore apply`: 명시적 운영자 승인, 이전 root **보존** (overwrite 금지), 새 root에 검증 복원, index rebuild, hold/review reconcile, 운영자 cutover.
- 부분 복원은 원본 bytes만이 아니라 object/observation/acquisition/custody/production linkage를 함께 재구성하고 **누락은 명시적으로 report**.
- 분기/충돌이 있으면 '최신 파일 덮어쓰기' 금지. 새 root에서 수동 reconciliation.

## 운영 SLO (초기 제안, 확정 운영 지표 아님)
- 일일 incremental 또는 변경집합 snapshot, 주간 verify sample, 월간 전량 hash scan, 분기 restore drill.
- 중요 사건자료: ingest 후 첫 independent verified snapshot 완료 전 *ERL-3 미부여*.
- RPO/RTO는 데이터 양·네트워크·인원·디스크에 따라 실측 후 확정; 설계 단계에서는 값을 허위 약속하지 않음.

## 독립 2차 리뷰: Snapshot point-in-time consistency (2026-10-09)

백업 source manifest를 복사 시작 때 만들고, 작성 중인 Knowledge/Context 파일이 나중에 바뀔 수 있다. 그러므로 **source tree가 logical single point-in-time이라고 자동 주장하지 않는다**. 두 가지 허용 경로:

1. **Quiesced snapshot**: Writer의 ingest/Knowledge 자동 쓰기 중지, 사용자 편집 세션 종료 안내. Canonical committed receipts만 범위 지정 → 파일 해시/크기 수집 → secondary 복사 및 독립 재해시 → source 재해시/목록 재조회 → 변동없을 때 `complete.receipt`.
2. **Filesystem-supported point-in-time snapshot**: OS 검증 가능한 snapshot capability 사용 시 snapshot ID, 도구·시각·선택 파일 전체 snapshot provenance 저장. R2 기본 구현에서는 이 방법을 전제하지 않는다.

Source hash/manifest 재검증이 중간에 실패하면 `SNAPSHOT_SOURCE_CHANGED`, backup FAIL, ERL-3 표시 금지. Google Drive/OneDrive 동기화 완료와는 독립적이다. `docs/21_TDD_SCENARIOS.md`의 TC-BKP-03 필수.

증거보존용 '독립 백업'은 동일 물리 디스크의 다른 폴더만으로 충분하다고 주장하지 않는다. 적어도 failure domain이 다른 저장매체 또는 독립적으로 보관되는 cloud/offline snapshot 복사로 확인해야 함. 요구사항 `REQ-BKP-010`.

# 04. Storage / OneDrive / Google Drive 설계

## 1. 원칙

Second Brain은 cloud provider를 알지 않는다.

```toml
[brain]
root = "C:/Users/<user>/OneDrive/SecondBrain"
```

또는

```toml
[brain]
root = "D:/Google Drive/My Drive/SecondBrain"
```

이면 끝이다.

---

## 2. 권장 배치

### Option A
```text
OneDrive/SecondBrain         = Primary SSOT
Google Drive/SecondBrain_Backup = Secondary snapshots
```

### Option B
```text
Google Drive/SecondBrain    = Primary SSOT
OneDrive/SecondBrain_Backup = Secondary snapshots
```

두 선택지는 기능적으로 동등하다.

---

## 3. 금지 구조

```text
        OneDrive sync
            |
      SecondBrain live tree
            |
      Google Drive sync
```

동일 tree를 두 sync engine이 동시에 two-way sync하지 않는다.

---

## 4. Sync ≠ Backup

Primary:
- 일상 파일 동기화
- 여러 장치 접근
- cloud provider version history는 보조 안전망

Secondary:
- 날짜/시점별 snapshot
- snapshot manifest 검증
- primary 삭제/오염이 즉시 전파되지 않음

---

## 5. Local availability

Evidence verify는 실제 bytes가 필요하다.

### OneDrive
Evidence와 Meta는 `Always keep on this device` 권장.

### Google Drive
Primary 사용 시 Mirror mode 권장.

placeholder가 존재하지만 local bytes가 없으면 ingest 상태를 `WAITING_FOR_HYDRATION`으로 둔다.

---

## 6. Snapshot layout

```text
SecondBrain_Backup/
└─ snapshots/
   └─ 2026/
      └─ 10/
         └─ 20261003T010000+0900/
            ├─ snapshot.json
            ├─ manifest-sha256.txt
            ├─ manifest-sha512.txt
            └─ data/
```

`snapshot.json`:
- snapshot_id
- brain_id
- source root fingerprint
- created_at
- tool/version
- file_count
- total_bytes
- manifest digests
- verify status

---

## 7. Cloud conflicts

Cloud sync conflict는 storage transport issue로 분류한다.

원칙:
- canonical bytes identity는 SHA-256
- duplicate filename은 identity가 아님
- conflict copy가 생기면 자동 overwrite 금지
- object digest가 같으면 duplicate candidate
- digest가 다르면 별도 Evidence Observation/Object 후보
- 사람이 의미상 어느 것이 기대본인지 판정할 수 있도록 보존

---

## 8. Local-only state

다음은 cloud sync 대상에서 제외한다.

```text
index.sqlite
fts.sqlite
vector index
graph cache
temp
locks
runtime logs
download staging
```

위치는 기본적으로:
```text
%LOCALAPPDATA%/SecondBrain/<brain_id>/
```

---

## 9. Primary migration

OneDrive → Google Drive로 옮겨도:
- IDs 유지
- `brain://` URI 유지
- JSON records 유지
- index는 새 PC에서 rebuild
- 물리 root path만 변경

물리 경로는 canonical record의 identity가 아니다.

## R2 authoritative multi-device/storage policy
Always designated Writer for records and knowledge auto promotion. Per-device capture-only subfolders for other machines. Local atomic rename does NOT confer cloud cross-machine distributed transaction. Writer handoff requires manual reconciliation and epoch. See `docs/16_WRITE_AUTHORITY_SYNC.md`.

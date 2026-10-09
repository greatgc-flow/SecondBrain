# 05. Inbox / Intake State Machine

## 1. 상태

```text
DETECTED
   |
   v
STABILIZING
   |
   +--> WAITING_FOR_HYDRATION
   |           |
   |           v
   +--------> READY
                |
                v
           FINGERPRINTING
                |
                v
            HASHING
                |
                v
         OBJECT_RESOLUTION
           /          \
     REUSE             CREATE
       \                /
        v              v
         RECORDING_METADATA
                |
                v
             SEALING
                |
                v
          VERIFYING_SEAL
            /       \
          PASS      FAIL
           |          |
           v          v
       PRESERVED   QUARANTINED
           |
           v
         INDEXABLE
```

---

## 2. STABILIZING 판정

READY가 되기 위한 기본 조건:
- N회 연속 size 동일
- mtime 안정
- file open/read 성공
- known temporary extension 아님
- cloud placeholder가 아니라 local bytes 접근 가능
- directory copy의 경우 manifest 대상 enumeration이 안정

구체 시간값은 config로 둔다.

예:
```toml
[inbox.stabilization]
poll_seconds = 5
stable_samples = 3
max_wait_minutes = 60
```

---

## 3. Quarantine 이유 예

- local bytes 접근 불가
- read error
- digest 계산 중 I/O error
- MIME/profile 불일치
- archive bomb 의심
- path traversal entry 포함 archive
- seal verify 실패
- record schema validation 실패
- unsafe symlink
- unsupported special file

Quarantine은 삭제가 아니다.

---

## 4. Object resolution

입력 SHA-256을 계산한 후:

### object already exists
- canonical payload digest 재검증
- payload 같음 → reuse
- Observation 생성

### object does not exist
- local staging에 payload 준비
- payload fsync 가능 범위 수행
- canonical target에 atomic publish
- 경쟁으로 target이 생겼다면 target digest 확인
- 같으면 reuse
- 다르면 critical integrity error

---

## 5. Drop 파일 처리

정책 선택:
- `copy_then_preserve_drop`
- `copy_then_archive_drop`
- `copy_then_delete_drop_after_verified_seal`

R1 기본:
```text
copy_then_archive_drop
```

즉 원본 입력을 먼저 Vault에 복사/검증하고, 성공 후 Inbox/Processed 성격의 이력 위치로 이동할 수 있다. 다만 canonical original은 Vault payload다.

---

## 6. Crash recovery

각 ingest attempt는 local staging record를 가진다.

```text
attempt_id
source_path
state
sha256_if_known
candidate_object_id
last_transition
```

프로세스 재시작 시:
- sealed canonical object가 검증되면 이어서 metadata commit
- ambiguous state면 fail-closed / quarantine
- 원본 Drop을 자동 삭제하지 않음

## R2 canonical commit semantics
R1 단계도는 high-level view일 뿐. `SEALED/INDEXABLE`은 다중 파일 publish 이후 **검증된 commit receipt**가 발행될 때만 전환한다. nonwriter PC는 intake-commit 불가, capture-only. `docs/17_TRANSACTION_AND_RECOVERY.md` 우선.

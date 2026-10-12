# 02. 논리/물리 아키텍처

## 1. 책임 분리

```text
Engram      = portable runtime / tools lifecycle
PeerHub     = multi-AI coordination / review / consensus
SecondBrain = durable evidence + knowledge + context
Obsidian    = human UX
MCP         = AI access boundary
Cloud Sync  = storage replication transport
```

Second Brain은 Engram/PeerHub 없이도 canonical files를 읽고 검증할 수 있어야 한다.

---

## 2. Canonical directory

```text
SecondBrain/
│
├─ 00_Inbox/
│  ├─ Drop/
│  ├─ Pending/
│  ├─ Quarantine/
│  └─ Rejected/
│
├─ 10_Evidence/
│  ├─ Vault/
│  │  └─ objects/
│  │     └─ sha256/
│  ├─ Records/
│  │  ├─ objects/
│  │  ├─ observations/
│  │  ├─ acquisition/
│  │  ├─ custody/
│  │  ├─ derivations/
│  │  └─ integrity/
│  ├─ Manifests/
│  ├─ LegalHold/
│  ├─ Working/
│  └─ Production/
│
├─ 20_Knowledge/
│  ├─ concepts/
│  ├─ entities/
│  ├─ decisions/
│  ├─ patterns/
│  ├─ questions/
│  └─ methods/
│
├─ 30_Context/
│  ├─ Projects/
│  ├─ Areas/
│  ├─ Resources/
│  └─ Archives/
│
├─ 40_Meta/
│  ├─ catalog/
│  ├─ provenance/
│  ├─ relations/
│  ├─ schemas/
│  └─ snapshots/
│
├─ 50_Memory/
│  ├─ semantic/
│  ├─ episodic/
│  ├─ procedural/
│  └─ summaries/
│
└─ 90_System/
   ├─ config/
   ├─ templates/
   ├─ policies/
   └─ evals/
```

`40_Meta/schemas`는 실제 런타임 배포 시 이 패키지의 `schemas/`를 복사 또는 참조한다.

---

## 3. Rebuildable local state

```text
%LOCALAPPDATA%/SecondBrain/<brain_id>/
├─ index/
│  ├─ catalog.sqlite
│  ├─ fts.sqlite
│  ├─ vectors/
│  └─ graph/
├─ cache/
├─ temp/
├─ locks/
├─ staging/
└─ runtime-logs/
```

삭제해도 canonical files에서 전부 재생성 가능해야 한다.

---

## 4. Evidence data flow

```text
External Source
      |
      v
00_Inbox/Drop
      |
      v
DETECTED -> STABILIZING -> READY
      |
      v
Acquire metadata
      |
      v
Hash SHA-256/SHA-512
      |
      v
Create/Reuse Evidence Object
      |
      v
Create Observation + Acquisition event
      |
      v
Seal canonical payload
      |
      v
10_Evidence/Vault
      |
      +------> Working derivations
      |          OCR / MD / EXIF JSON / transcript
      |
      +------> Production
      |          redacted / merged / exhibit copy
      |
      +------> Knowledge
                 human/AI-reviewed note
```

---

## 5. URI model

물리 경로는 외부 interface로 노출하지 않는 것을 기본으로 한다.

```text
brain://evidence/<evidence_id>
brain://object/<object_id>
brain://knowledge/<note_id>
brain://context/<context_id>
brain://production/<production_id>
```

resolver가 `SECOND_BRAIN_ROOT`를 기준으로 실제 파일을 찾는다.

---

## 6. Idempotent ingest

R2/R3 **단일 Writer** 규칙이 적용된다. 각 장치는 독립 Capture-Only 패키지를 만들 수 있지만, Vault/Records에 commit하는 주체는 지정 Writer 한 대뿐이다.

1. 각 Capture-Only PC는 `<device-id>/<capture-id>`에 수집 payload/receipt를 작성한다.
2. 지정 Writer는 stable/hydrated, hash, receipt 검증 후 인수한다.
3. 단일 Writer가 canonical object 경로를 결정하여 존재 시 재검증 후 재사용한다.
4. 신규 객체는 단일 Writer 호스트의 local staging에서 검증 후 publish한다.
5. 같은 bytes라도 capture-id가 다르면 Observation은 각각 남긴다.
6. 다른 Writer/epoch, cloud conflicted copy, 미완료 commit은 fail-closed로 격리한다.

**주의:** 두 호스트의 atomic publish 경쟁을 정상 운영 패턴으로 지원하지 않으며, sync는 distributed transaction/lock이 아니다. `docs/16_WRITE_AUTHORITY_SYNC.md`가 우선한다.
8. 동일 Observation 판정 규칙은 source fingerprint + capture timestamp 정책에 따름

Object uniqueness:
```text
object identity = SHA-256 bytes
```

Evidence identity:
```text
evidence_id = 사람이 다루는 stable record identity
```

R1에서는 Evidence Object 1개가 대표 Evidence record 1개를 갖되, 동일 object의 여러 Observation을 허용한다.

---

## 7. Failure domains

- Cloud sync 실패 → local canonical bytes 유지
- Index 손상 → rebuild
- Vector DB 손상 → rebuild
- PeerHub 장애 → Evidence/Known canonical records 무영향
- Engram 장애 → 일반 Python/CLI 환경에서도 schema/data 읽기 가능
- Obsidian plugin 장애 → Markdown/raw files는 유지
- TSA 장애 → ERL-3까지 정상 동작, ERL-4 승격만 보류

## R2 authoritative addendum
Single designated Writer; capture-only devices; immutable receipt-driven publish; source bytes hashed twice for safety; `ERL-3` as *target* not default truth. 상세: `docs/16_WRITE_AUTHORITY_SYNC.md`, `docs/17_TRANSACTION_AND_RECOVERY.md`, `docs/18_DATA_CONTRACTS.md`.

## R3 Governance canonical addition
`40_Meta/governance/{feedback,releases}/`는 민감내용 없는 변경·후속개선·release 증빙의 canonical metadata 영역이다. 원래 Evidence 원본/custody data와 절대 합치지 않는다. Runtime logs/secret-bearing traces는 `%LOCALAPPDATA%`에 둔다. `docs/32~44` 참고.

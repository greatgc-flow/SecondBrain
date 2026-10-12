# 06. CLI / MCP / PeerHub / Obsidian Interfaces

## 1. CLI surface (계약 초안)

R1 target:

```text
brain init
brain status
brain config validate

brain ingest <path>
brain ingest inbox
brain evidence show <evidence-id>
brain evidence verify <evidence-id>
brain evidence verify --all
brain evidence lineage <evidence-id>

brain derive <evidence-id> --profile <profile>
brain production create <evidence-id> ...
brain production verify <production-id>

brain hold create
brain hold add
brain hold status
brain hold release

brain snapshot create
brain snapshot verify
brain restore plan
brain restore apply

brain index rebuild
brain index status

brain export evidence <evidence-id> --format bagit
```

모든 mutation은 가능한 경우:
```text
--dry-run
--json
```
계약을 가진다.

R1 destructive operation은 dry-run 기본을 권장한다.

---

## 2. MCP surface

### Read
```text
brain.search
brain.get
brain.sources
brain.related
brain.timeline
brain.lineage
brain.context
brain.evidence_status
```

### Propose / Write
```text
brain.capture_proposal
brain.note_proposal
brain.link_proposal
brain.promote_proposal
```

초기 R1에서는 AI가 Vault original을 직접 수정하는 tool을 제공하지 않는다.

---

## 3. Evidence response envelope

AI에게 전달되는 evidence 조회 결과:

```json
{
  "uri": "brain://evidence/EV-...",
  "evidence_id": "EV-...",
  "status": "SEALED",
  "erl": "ERL-3",
  "media_type": "application/pdf",
  "sha256": "...",
  "as_of": "2026-10-03T00:00:00+09:00",
  "source_summary": {},
  "derived_artifacts": [],
  "integrity": {
    "last_verified_at": "...",
    "status": "PASS"
  }
}
```

원본 bytes 자체의 제공은 별도 policy/tool 경계를 둔다.

---

## 4. PeerHub integration

PeerHub DB는 evidence binary storage가 아니다.

권장 payload:

```json
{
  "artifact_type": "brain-evidence-reference",
  "brain_uri": "brain://evidence/EV-...",
  "sha256": "...",
  "purpose": "review",
  "requested_capabilities": ["evidence-review"]
}
```

사용 예:
- Claude: 문서/문맥 검토
- Codex: 구조/metadata consistency review
- AG: 독립 cross-review
- PeerHub: disagreement/consensus/feedback 기록

AI 결과는:
```text
10_Evidence/Vault
```
로 승격하지 않는다.

AI 결과는:
```text
20_Knowledge 또는 40_Meta review records
```
로 저장한다.

---

## 5. Engram integration

Engram은 runtime/tool lifecycle만 담당한다.

필요 환경:
```text
SECOND_BRAIN_ROOT
SECOND_BRAIN_LOCAL_STATE
```

선택적 managed tools:
- Python
- Git
- ExifTool
- ffmpeg/ffprobe
- PDF tools
- WARC capture tooling
- OpenSSL
- PeerHub
- AI CLIs

실제 tool catalog 반영은 Second Brain TDD 이후 별도 변경으로 진행한다.

---

## 6. Obsidian

Obsidian은 Human UX.

권장 화면:
```text
Home
Inbox
Projects
Areas
Knowledge
Evidence Search
Recent
Legal Holds
Integrity
```

Evidence Vault 원본은 read-only UX로 취급한다.

Obsidian property에는 복잡한 provenance 전체를 넣지 않는다.
간단한 stable identifiers와 view fields만 노출한다.

## R2 normative interface patch
`brain writer status/handoff`, `brain doctor`, `brain policy egress check`, `brain evidence report` 추가. `brain ingest` mutation은 designated Writer/epoch 필수. MCP stdio-only/read scope checked, proposal-only writes. PeerHub v0.12.4의 Core는 Peer/Stream/Record/Offset이고 Artifact/Work/Search 등은 Extensions임; 위 R1 나열은 역사적 참고일 뿐. 상세 `docs/25_INTEGRATION_BASELINES.md`.

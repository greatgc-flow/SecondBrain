# 09. TDD Entry Criteria

## 1. 이 패키지의 종료 지점

다음 조건을 만족하면 Pre-TDD 완료로 본다.

- [x] 목적/범위 정의
- [x] MUST/SHOULD/MAY 정의
- [x] SSOT/derived state 분리
- [x] directory model 정의
- [x] cloud sync 원칙 정의
- [x] Evidence domain model 정의
- [x] JSON Schema 초안 정의
- [x] ingest state machine 정의
- [x] CLI/MCP/PeerHub 경계 정의
- [x] Legal Hold 정의
- [x] Capture Profile 정의
- [x] threat model 정의
- [x] requirements traceability 정의
- [x] 첫 테스트 순서 정의
- [ ] 테스트 코드 작성
- [ ] 구현 코드 작성

즉 다음 커밋부터 테스트가 먼저다.

---

## 2. TDD 첫 구현 순서

### T1 — Config and root invariants
1. config parses
2. root path validation
3. local-state path is outside canonical root by default

### T2 — Evidence schemas
1. valid Evidence Object accepted
2. missing required digest rejected
3. invalid timestamp rejected
4. invalid ERL rejected

### T3 — Stable file detector
1. changing size never READY
2. stable size N samples -> READY
3. unreadable file -> wait/quarantine
4. non-local placeholder -> WAITING_FOR_HYDRATION

### T4 — Hashing
1. SHA-256 known vector
2. SHA-512 known vector
3. stream large file
4. read failure fail-closed

### T5 — Content-addressed object resolution
1. new bytes create object
2. same bytes reuse object
3. 서로 다른 장치에서 같은 bytes를 capture하여도 지정 Writer가 순차 처리하면 canonical object는 하나로 재사용
4. existing path different digest -> critical failure

### T6 — Observation
1. same object can have N observations
2. acquisition source and ingest channel stay separate

### T7 — Seal
1. staged payload is verified before publish
2. published payload digest reverified
3. source Drop is not deleted before seal success

### T8 — Custody hash chain
1. first event
2. chained event
3. modified historical event invalidates chain
4. canonical serialization deterministic

### T9 — Legal Hold
1. active hold blocks evidence destroy
2. released hold permits policy-controlled destroy
3. hold operation audited

### T10 — Snapshot
1. manifest includes all expected canonical files
2. snapshot verifies
3. corrupted payload fails
4. partial snapshot never marked complete

### T11 — Index rebuild
1. delete index
2. rebuild from canonical records
3. same canonical data yields equivalent logical index

### T12 — CLI contracts
1. dry-run has no mutation
2. `--json` shape stable
3. nonzero exits classified

### T13 — MCP read boundary
1. read returns stable brain URI
2. no raw path dependency
3. raw original bytes require explicit policy tool

### T14 — PeerHub reference adapter
1. only reference metadata dispatched
2. AI response stored as derived review, not Evidence Vault

---

## 3. Property-based candidates

Hypothesis가 특히 유용한 곳:
- arbitrary filenames / Unicode
- path normalization
- duplicate ingest
- event chain mutation
- concurrent state transitions
- JSON schema round trips
- snapshot manifests
- content-address paths

---

## 4. Fault injection candidates

- process crash after hash before publish
- crash after publish before metadata event
- cloud file disappears mid-read
- disk full
- permission denied
- corrupt existing canonical object
- secondary snapshot unavailable
- TSA timeout
- index DB corrupted
- duplicate device IDs
- clock moves backward

---

## 5. TDD Definition of Done for R1

R1 구현 완료 판정은 별도 release criteria에서 다루되 최소:
- deterministic unit suite
- property tests
- failure injection tests
- cross-device simulation
- local OneDrive-like sync simulation
- Google Drive-like placeholder simulation
- backup/restore round trip
- full evidence lineage export
- no untested destructive mutation
를 요구한다.

## R2 revised sequence / validity
`docs/21_TDD_SCENARIOS.md`와 v2 schemas가 TDD 진입 authoritative 계약. 기존 T1~14는 역사적 순서. **single-writer+privacy-deny+transaction receipt+ERL-by-evidence**를 선행 차단 테스트에 추가한다.

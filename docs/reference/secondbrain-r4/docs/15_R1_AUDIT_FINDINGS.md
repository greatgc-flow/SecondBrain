# 15. R1 독립 감사 발견사항 및 재귀적 MECE 판단

## 평가 방법
입력 85개 ZIP 구성요소를 영역별로 검토했다. 구조 1차 → 각 구조의 실패경로 2차 → 도메인 계약/증빙/운영 3차 → 요구사항·스키마·TDD 교차 추적 4차. **설계의 완전성은 목표이지 수학적 증명은 아니다.** 미구현 시스템 성능·장애 복원력은 미검증.

| ID | 등급 | R1 결함/불확실성 | R2 조치 | 검증 위치 |
|---|---|---|---|---|
| F01 | BLOCKER | 모든 PC ingest 허용하지만 cloud에는 글로벌 CAS·순서 보장 없음 | Single Writer; capture-only + reconciliation | 16 / TC-SYNC-01 |
| F02 | BLOCKER | 동일 SHA bytes dedup ≠ acquisition 재현/중복 event 결정성 | object/ref/observation/attempt 키 분리 | 18 / TC-DATA-02 |
| F03 | BLOCKER | temp rename과 복수 파일 metadata commit 원자성 미정 | commit marker 및 recovery classification | 17 / TC-TXN-01 |
| F04 | HIGH | EvidenceRecord와 Object에 모두 ERL 저장 → drift | ERL은 파생 status view, 증빙이 원본 | 18 / TC-ERL-01 |
| F05 | HIGH | hash-chain JCS가 OPEN, 전역 event ordering 미정 | JCS accepted, stream별 순서 + anchors | 18 / TC-EVT-01 |
| F06 | HIGH | archive/zip/symlink/paths/Windows ADS·junction 처리 부족 | 검증·격리·절대경로 거부 정책 | 19 / TC-SEC-01 |
| F07 | HIGH | AI가 민감 Evidence를 외부 CLI에 전송할 수 있음 | explicit scoped consent/egress log | 19 / TC-AI-01 |
| F08 | HIGH | cloud sync와 backup의 독립성/retention/restore 증빙 부족 | 동일 tree 중복 금지·외부/오프라인 사본·복구 drill | 20 / TC-BKP-01 |
| F09 | HIGH | hold scope가 시점 이후 수집되는 관련 자료를 놓침 | matter/predicate and static IDs + hold expansion | 20 / TC-HOLD-01 |
| F10 | HIGH | PDF/EML/메신저/웹 원본의 취득 당시 한계 명시 미약 | source artifact capability & provenance grades | 26 / TC-CAP-01 |
| F11 | HIGH | 기존 schema format string만으로 timestamp 보장 못함 | Draft2020-12 + FormatChecker + semantic validators contract | 18 / TC-SCH-01 |
| F12 | HIGH | PeerHub v0.10.1 역할이 2026-10-09 현재 구조와 불일치 | v0.12.4 Core/extension 재기술 | 25 / TC-INT-01 |
| F13 | MEDIUM | 검색/인용 정밀 위치 및 거부·불확실성 응답 부족 | retrieval evidence envelope / abstention | 27 / TC-RET-01 |
| F14 | MEDIUM | Korean storage/Dropbox/Obsidian 원본 접근 위험 | folder-first + deny defaults + clean UX | 23 / TC-OPS-01 |
| F15 | MEDIUM | 법률 제출본 출력시 페이지·발췌·마스킹의 역추적 규정 약함 | production manifest & loss-of-context controls | 26 / TC-EXP-01 |
| F16 | MEDIUM | traceability가 ID range로, 개별 수락 기준 부재 | 전체 ID 1:1 CSV + 주요 P0 상세 시나리오 | traceability / 21 |
| F17 | HIGH | snapshot 대상 폴더가 복사 중 변경될 수 있으나 consistency barrier 누락 | quiesce+source rehash / snapshot proof 요구 | 20 / TC-BKP-03 |
| F18 | HIGH | 동일 디스크 secondary를 독립 백업으로 오인 | 서로 다른 장애영역 + snapshot 검증 요구 | 20 / TC-BKP-04 |

## 검토 중 부정한 주장
- OneDrive/Google Drive 동기화만으로 `immutable`, `WORM`, `custody independently attested`, `globally atomic`이라고 주장하지 않는다.
- `SHA-256 matching`은 *현재 파일 바이트가 특정 시점 해시와 같다*는 근거이며 사건 당시 원본 생성시각이나 자료 진위 자체를 입증하지 않는다.
- File size + mtime 몇 회 동일하다고 **다른 프로세스가 이후 수정 불가능**한 것은 아니다. 두 번 hashing/copy 검증 + source-changed 판정이 필요.
- 동일 바이트라도 취득·관찰 사실과 논리적 증거 단위는 다를 수 있다.

## 개정 가이드
동일 주제를 R1 문서와 R2 문서가 다르게 서술할 때: `00_START_HERE` → R2 `ADR-0010~0019` → `docs/31_REQUIREMENT_AMENDMENTS.md` → `schemas/v2` → 나머지 R1을 적용한다.



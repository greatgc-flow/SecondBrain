# R1 → R2 변경 요약 (2026-10-09)

## Blocker 판정 후 해결
- **B-01** 모든 PC가 직접 ingest 가능한 R1 정책을 폐기하고 *single-writer + capture-only peers* 적용 (`ADR-0011`, 16).
- **B-02** cloud-synced directory에서 atomic rename == cross-device atomic transaction 오해를 제거 (`ADR-0012`, 17).
- **B-03** acquisition/hash/seal/backup 사이 장애창과 commit marker가 불명확했던 문제 해결 (17, 21).
- **B-04** `ERL-3`을 수집 완료 직후 부여하던 기본값을 **목표 등급**으로 변경; 등급은 검증 evidence 기준 계산 (18).
- **B-05** 이벤트 JCS canonicalization 미결을 Accepted로 확정; fork를 만드는 다중 Writer는 금지 (ADR-0010, 18).
- **B-06** 민감 원본 외부 AI 전송 통제 및 indirect prompt injection 위협 모델 도입 (19).
- **B-07** backup와 restore 시점/범위/기준점/증빙/retention/hold override 구체화 (20).
- **B-08** 기존 v1 schema의 nullable/hash/event 필수/ERL/format validation 빈틈을 v2 스키마로 보완 (schemas/v2).
- **B-09** PeerHub 2026-10-09 릴리스 Core/Extension 변화 반영 (25, integration).
- **B-10** retrieval의 citation/page-offset/권한/다중시점/모름 응답 계약 보강 (27).
- **B-11** 수집 당시 원출처 맥락과 나중 Inbox 들어온 파일의 차이를 명확히 규정 (18, 23).
- **B-12** R1 요구사항 추적성이 구간/포괄 매핑에 머문 문제를 requirement별 CSV 단위로 재작성 (traceability).

## 비파괴 변경
- 기존 R1 요구사항 ID를 유지하되, 모순되는 부분은 본 R2와 `docs/31_REQUIREMENT_AMENDMENTS.md`가 우선.
- R1 스키마 8종은 `schemas/v1`에 그대로 남겨 migration 검토 가능. 신규 v2 스키마 14종과 fixture 추가.
- 과거 R1 ZIP 원본을 `history/R1_input.zip`으로 묶음.

## 남은 조건부 결정
1. 실제 파일 root/운영 PC(사용자 환경)의 값과 권한 설정은 배포 시 주입.
2. 외부 AI와 TSA·암호화 키·보관기간은 데이터 등급과 운영 정책으로 선택.
3. 실제 파일시스템/O365/GDrive 간 행동 테스트는 TDD/통합 테스트로 검증해야 함. 설계만으로 입증 불가.

## 독립 2차 감사에서 추가 보완
- 백업 데이터의 원본 폴더가 복사 도중 변경되는 **비원자적 snapshots** 문제를 발견하여 source rehash + quiesce gate를 추가했다.
- 같은 디스크의 2개 폴더를 '독립 백업'이라고 주장하지 않도록 failure-domain 정책을 명문화했다.
- MCP `2026-07-28` 사양을 현재 기준선으로 추가했다.

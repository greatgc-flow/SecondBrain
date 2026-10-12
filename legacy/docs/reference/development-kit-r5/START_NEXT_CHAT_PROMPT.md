# Start-next-chat / TDD handoff (R5, 2026-10-10)

첨부된 `Development_Kits_VerySimple_R5_20261010_FINAL.zip`을 전체 해제하고 `00_START_HERE.md`를 먼저 읽어라.

**현재 기준/SSOT:**
- 범용 요구 100개: `profiles/generic/quality/requirements.csv`.
- Second Brain 요구 188개: `profiles/secondbrain/traceability/requirements_to_tests.csv`.
- 파생 전체 검색: `catalog/FEATURE_INVENTORY.csv`, `python kit.py catalog --id/--find/--json`.
- 규범·우선순위: `standards/00_CANONICAL_MAP.md`; 도메인 안전/원본보존 규칙은 우선한다.
- 작업 History/Errors/Lessons: `python kit.py feedback ...` / `standards/04_FEEDBACK_LOOP.md`; `.kit_state`는 새 사용부터 생성, 원본 ZIP에 포함되지 않는다. 진행 후에는 이를 별도 백업해야 한다.

**진행 상태:** R5는 Pre-TDD 설계 패키지. Generic 및 Second Brain **제품 코드 없음, 제품 테스트 없음**. `kit.py`는 패키지 관리 도구일 뿐. 관리 테스트 11개는 두 회차로 개별 실행 PASS, 디자인 lint 3종 PASS, 스키마/참조 ZIP SHA 검사 포함. 클라우드/Windows Node/AI/법적 입증 관련 실증은 NOT_RUN. Git push/태그/배포는 NO-GO.

**다음 작업:** ① `python kit.py verify` → ② 관련 요구/설계와 acceptance/negative 사례만 조회 → ③ 최소 수직기능의 RED 테스트 먼저 → ④ GREEN/review → ⑤ 실제 error·lesson 기록 → ⑥ 후보 검증 → ⑦ T3/T4 실증(권한과 비용 승인 필요) → ⑧ 효과 관측 후 종결. 비필수 복잡화와 과도한 새 도구는 피한다.

**변경/감사:** `quality/CHANGELOG_R5.md`, `quality/MECE_FINDINGS_R5.csv`, `quality/RESEARCH_AND_GIT_R5.md`, `quality/AUDIT_REPORT.json`, `history/Previous_VerySimple_20261010_FINAL.zip`를 비교. 이전 ZIP을 현재 구현 상태로 해석하지 않는다.

**개발자 주의:** 임의로 `PASS`나 릴리스 상태를 승격하지 않는다. PeerHub v0.12.6 native resume은 opt-in이며 model/provider별 실증 전 의존하지 않는다. Engram v3.7.0과 PeerHub은 외부 프로젝트이지 이 ZIP의 저장소가 아니다.

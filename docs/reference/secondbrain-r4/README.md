# Evidence-First Second Brain R4 — Independent Final Audit / Pre-TDD

**현재 상태: 설계 검토만 수행. 구현/운영/TDD/독립 복구 실증 0건.** 이전 R3 설계의 188개 요구사항과 14 Evidence v2 + 8 Governance v1 schema는 그대로 보존했다.

## 시작
1. `00_START_HERE.md` → `CHANGELOG_R4.md`
2. `docs/47_INDEPENDENT_FINAL_AUDIT.md` → `docs/48_SEMANTIC_VALIDATION_AND_TEST_ORACLES.md` → `docs/49_PRACTICAL_OPERATIONS_SECURITY_AND_LEGAL_BOUNDARIES.md`
3. `quality/R4_SCHEMA_LIMITATION_PROBES.json` → `quality/R4_SEMANTIC_TEST_ORACLES.csv`
4. `docs/50_FINAL_VERDICT_AND_TDD_ORDER.md` → `START_TDD_NEXT_CHAT.md`
5. R3 기준선: `docs/32`~`46`, R2 기술계약: `docs/01`~`31`, schemas/v2, schemas/governance/v1.

## 핵심 판정
- 아키텍처 방향: GO.
- TDD 시작: CONDITIONAL GO.
- 실제 Evidence 법적 효력·Production 운영·WORM·클라우드 복구·AI 안전성 인증: NOT VERIFIED / NO-GO.
- JSON Schema에서 서로 모순되는 값도 구조상 받아들일 수 있음: `tools/r4_independent_audit.py`로 재현한 음성 증거를 확인.

## 로컬 감사
`python tools/static_design_audit.py` (R3 legacy structural, 숫자 188 검증)
`python tools/r4_independent_audit.py` (의미적 반례가 실제 JSON Schema를 통과하는 경계를 문서화; 제품을 실행하지 않음)

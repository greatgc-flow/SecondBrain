# 범용 개발 v2 시작 안내

1. `README.md`, `docs/00_NORMATIVE_AND_PRIORITY.md`, `docs/22_2026_METHOD_ADOPTION.md`를 읽는다.
2. GD-001~GD-100 적용 범위를 결정한다. AI_ENABLED가 아니면 AI 전용 요건은 승인된 N/A.
3. `quality/research_decisions_20261010.csv`를 근거로 새 도구를 넣을지 판단한다. 모든 유행을 채택하지 않는다.
4. 계획된 TEST는 실행하지 않았다. `python tools/design_lint.py`는 문서/스키마/manifest의 정적 검사일 뿐.
5. 첫 수직 slice에서 Spec→Task→RED→GREEN→Converge. `docs/16_TDD_KICKOFF.md`.
6. AI가 개발한다면 `docs/24...`/`25...`/`26...`의 자율성 제한과 테스트 오라클을 먼저 승인한다.
7. TDD 이후 G0~G7, 후보 SHA, 수요자 효과와 재발 검증까지 닫는다.

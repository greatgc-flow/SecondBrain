# General Development Governance + Pre-TDD Kit v2 (2026-10-10)

**기존 v1을 기반으로 한 독립 범용 프로젝트 설계 기준본.** 실코드/실제 TDD 없이 새 방법론의 요건/검증 오라클까지 정의한다.

## 첫 경로
1. `00_START_HERE.md` → `docs/00_NORMATIVE_AND_PRIORITY.md` → `docs/01_SCOPE_PROFILES.md`.
2. `docs/22_2026_METHOD_ADOPTION.md`, `quality/research_decisions_20261010.csv`에서 채택 사유와 제외된 유행 확인.
3. 프로젝트별 `config/project.example.toml` 복제, requirements 100개 중 적용 MUST와 승인된 N/A 선택.
4. Spec→Plan→Tasks→RED/GREEN→Converge. `docs/23_SDD_CONVERGENCE_PROTOCOL.md`.
5. AI_ENABLED이면 `docs/24_AI_AGENT_HARNESS.md`, `docs/25_EVAL_DRIVEN_DEVELOPMENT.md`, `docs/26_AGENT_SECURITY_AND_APPROVAL.md` 필수.
6. `python tools/design_lint.py` = **설계 정적 검사**. 실행 TDD가 아니다.
7. TDD 이후 기존 G0~G7 게이트 + v2 수렴/독립평가/효과관측.

## 핵심 내용
- **공통:** SDD↔TDD 수렴, 후보 바인딩, 독립 검증, 작은 수직 슬라이스, 지속 개선 비용 관측.
- **조건부:** AI agent harness, 다중 trial, 보안 승인, 사적 데이터 통제, model/prompt/tool 스냅샷.
- **선택/거부:** 강제 Spec Kit 실행, 기본 GraphDB/마이크로서비스, 제한 없는 AI 자율 실행 및 AI judge 단독 release 승인.

## 숫자와 상태
- 기존 74 + 신규 26 = **100 고유 요구사항**. 100개 계획 TEST 항목, 28개 cross-scenario, 스키마 v1 8 + v2 6 = **14종**.
- 정적 schema example이 통과해도 의미 검증(SEM-01~10)은 **NOT_RUN**.
- 기존 파일을 설계·재검증한 것으로 **제품 구현/실 테스트/표준 준수 인증**을 주장하지 않는다.

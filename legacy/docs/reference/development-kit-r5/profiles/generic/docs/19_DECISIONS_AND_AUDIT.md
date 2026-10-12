# 19. 재귀적 감사: 결과와 남은 한계

## Level 1 — 요구사항
GD ID 중복 여부, test_id/acceptance/negative/gate 누락 확인; 조건부 N/A는 실제 프로젝트에서 추가 승인.

## Level 2 — 구조
Core/extension boundary, authoritative owner, API/schema canonical version, config precedence, 데이터 owner; 독립적으로 불필요한 도메인 요소가 Core에 들어오지 않았는지 점검.

## Level 3 — 실패 경로
잘못된/중복 입력, 권한·secret, I/O 중단, 버전 불일치, 불확실한 외부 부작용, recovery, stale PASS, 품질 루프 false closure.

## Level 4 — 종단 lifecycle
요구→테스트→코드→artifact→운영 관측→새 요구로 다시 이어지는지; 고유 ID/후보 digest/owner로 양방향 검증. 실제 연동 결과가 없으면 `NOT_RUN`.

## 발견된 범용화 위험 및 완화
1. Evidence-only 법률 절차를 일반 개발 MUST로 이식하는 **과설계** → 특별 프로파일 분리.
2. 테스트 ID 목록을 실행 테스트라고 과대평가 → 상태값 NOT_RUN.
3. CI green으로 실환경 보증 → G3/4/6 독립.
4. AI 평가를 실제 승인 권한으로 혼동 → 사람 승인자 분리.
5. 단일 릴리스 날짜를 영구 기준으로 사용 → candidate + review trigger.
6. 모든 앱에 백업·RPO·SLO 강제 → 조건부 적용.

결론: **템플릿 Pre-TDD 시작 가능**, 실제 프로젝트의 자세한 설계·실행·승인은 별도. 품질을 수치로 단정하지 않는다.

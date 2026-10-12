# Very Simple Development Kits — R5 (2026-10-10)

범용 개발·Evidence-First Second Brain의 **설계 / 개발 시작 / 품질 거버넌스** 패키지. **아직 어느 제품도 구현하거나 배포하지 않았다.** `kit.py`는 최소한의 설계 조회·정적 점검·작업 피드백 수집 도구다.

**시작:** [`00_START_HERE.md`](00_START_HERE.md). 모든 기능 목록은 `catalog/FEATURE_INVENTORY.csv`(원본 CSV에서 생성된 파생 뷰), 모든 설계 판단의 우선순위는 [`standards/00_CANONICAL_MAP.md`](standards/00_CANONICAL_MAP.md).

아키텍처: `공통 방법론` → `범용 프로필` / `Second Brain 프로필` → `TDD→검증→릴리스 후보→실측 운영→오류·교훈 환류`. 엔그램은 런타임, PeerHub은 선택적 협업 계층이며 제품별 데이터 SSOT가 아니다.

**비목표:** 여기서 GitHub 저장소의 코드를 수정·푸시하거나 pip/winget 정식 제품을 출시한 척하지 않는다. 클라우드·실모델·보안·복원은 계획만 있고 미실행이며, 비용성 테스트는 명시적 승인과 사용량 상한이 선행되어야 한다.

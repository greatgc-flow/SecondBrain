# 06. 후보별 정식 릴리스 게이트 및 Git 이력

이전 ZIP은 Git 리포지토리 자체가 아님. 따라서 개별 파일/커밋 역사를 소급 입증할 수 없다. 원본 SHA-256과 보관 ZIP은 `history/`에 남겨 **패키지 수준의 회귀·유실 검증**에 쓴다.

Engram v3.7.0 (2026-10-03)과 PeerHub v0.12.6 (2026-10-09), 양 저장소 main 최근 커밋을 조사. `catalog/GIT_HISTORY_REVIEW.csv`와 `catalog/COMPATIBILITY_NOTES.md`에 차이점을 기록. 이 패키지는 해당 제품의 source/PR을 변경하지 않는다.

**정식 릴리스 필수 조건:**
1. 대상 저장소·버전·브랜치·패키지 소유자가 명확함; write 권한과 사용자 승인.
2. 제품 구현 + 실행 unit/integration/negative/restore/OS 테스트 PASS, 필수 취약점 미해결 0.
3. CI가 *실제로 배포할 built wheel/ZIP*을 시험했고 candidate digest 고정. 다른 SHA의 로그 재사용 불허.
4. 비용성 실측/라이브 검증에 별도 계정·예산·격리·허가; T3/T4 미실행이면 보류.
5. CHANGELOG, API/CLI help, known limitations, SBOM/provenance, release rollback plan, 재현 가능한 설치/복원 증거.
6. Git push → tagged release → PyPI(해당 배포물이 실제 Python 패키지인 경우) → winget(Windows 인스톨러 및 매니페스트 요건 충족 시). 의존성이 없는 설계 ZIP을 무리하게 pip/winget에 등록하지 않는다.

**이번 판정:** 두 제품 모두 Pre-TDD; 제품 배포 **NO-GO**. kit.py는 설계 도구이며 릴리스할 standalone 상품으로 승인되지 않음. 원본 Engram/PeerHub는 별도 제품이므로 여기서 태그·push 금지.

## R5 second pass (2026-10-10)

Recent head checked: Engram `0fba1c6abc7f` (v3.7.0), PeerHub `ccdee96c527b` (post-v0.12.6 documentation). PeerHub's native `--resume` feature is opt-in; this package does not implement or emulate it. `quality/RESEARCH_AND_GIT_R5.md` records links, dates and selected commit decisions. The `kit.py` helper is not the Python product. **No push/release** without a named target repository, owner decisions, package candidate and executed product tests.

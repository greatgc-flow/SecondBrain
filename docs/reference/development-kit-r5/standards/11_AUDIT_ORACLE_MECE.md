# 11. 재귀적 MECE 감사 항목 및 실제 적용

다음 검토 관점은 각 구조 계층(root→profile→component→file→schema/field→user scenario→test)에 동일하게 적용한다.

| 축 | 누락 점검 | 중복/모순 점검 | 검증 수단 | 상태 |
|---|---|---|---|---|
| 책임 | 입력·출력·owner·위험 | 두 SSOT·경계 중복 | SOURCE_OF_TRUTH 표 | 설계 확인 |
| 기능 | 요구 ID·계약·도움말 | 기능만 다른 명령 중복 | FEATURE_INVENTORY | 파생 검증 |
| 요구 | 목적·전제·성공 기준 | 상충 MUST·숨은 예외 | 100+188 원본 lint | PASS (정적) |
| 코드 | 공통 함수·configuration | 복제/하드코딩 | 아직 제품 코드 없음 | NOT_RUN |
| 시험 | 정상/예외/경계·복원 | 오라클과 구현 동일 주체 | T0~T4 계획·실제 증거 | 제품 NOT_RUN |
| 문서 | Quickstart→예시→한계 | 오래된 명령/버전 | 1개 입구·참조 점검 | 추가 |
| 기록 | incident→RC→observed→lesson | 원인만 해결 선언 | feedback state machine | toolkit 검증 가능 |
| 릴리스 | 후보 SHA/빌드 SHA/제3자 증빙 | 구버전 PASS 재사용 | G0~G7 | 제품 NO-GO |

점검에는 모든 원본 문장을 사람이 법적·의미적으로 확인하는 행위를 대신하는 자동 인증이 없다. 리스크가 있는 도메인은 담당자가 승인하지 않으면 출시하지 않는다.

# 07. 5Whys + 가감 + 사용자 결정

| 문제(Why1) | 반복 원인(Why3~5) | Very Simple 해결 | 위험/결정 |
|---|---|---|---|
| 문서가 많고 찾기 어려움 | 유사 규정 분산·상위 우선순위 부재 | 1개 시작 문서 + 세 갈래 profile + 생성 catalog | 도메인 문서는 필요한 때만 자세히 읽음 |
| 기능은 있는데 쓰기 어려움 | CLI 최상위에 수십 명령·예시 부족 | `help`, `catalog`, `verify`, `feedback`만 | 제품 CLI는 별도 설계 후 기능 확인 |
| 완료 처리 후 반복 장애 | 수정 자체를 종결로 오인 | RELEASED와 EFFECT_OBSERVED 분리 | 독립 review 승인 필요 |
| AI가 검수했다고 주장 | 모델 출력과 오라클 같은 주체 | 독립/결정적 검사기를 배포 게이트로 | 외부모델 보안 경계 분리 |
| 두 Cloud가 동시에 원본 변경 | 동기화를 DB/backup으로 오해 | 단일 Writer·읽기형 Capture·스냅샷 | 장애 시 FAIL_CLOSED |
| 테스트 종류가 늘어남 | 프로젝트 규모와 무관한 일괄 의무 | T0~T4, 조건부 적용 | 실측은 opt-in·예산 제한 |
| 기존 소스 반복 구현 | 호스트/도메인 조건을 Core에 하드코딩 | 파일 I/O/검증 헬퍼 공통, Tool adapter 밖 | 실제 코드가 생긴 후 중복률 측정 |
| 새 도구 과잉 도입 | 기존 안정 도구 확인 없이 직접 구현 | `argparse`, `unittest`, `jsonschema`, SQLite/FTS, RFC 포맷 활용 | 안정 외부 모듈 채택은 라이선스·유지보수·보안 먼저 확인 |

**검토 후 승인 필요** (여기서는 결정하지 않음): (A) Second Brain Primary OneDrive vs Google Mirror; (B) 단일 writer 운영/교체 권한; (C) LegalHold·증거 TSA 비용 정책; (D) AI 민감정보 외부반출과 T4 예산; (E) 실제 제품 배포 저장소/버전/지원 OS; (F) Python-only vs 추가 Node 도구 허용 범위.

반례: 직접 custom Hash DB/그래프 DB/프롬프트 프레임워크/클라우드 SDK를 코어에 넣기보다 사용 중인 stable module 또는 간단한 설정+문서로 해결 가능한지 먼저 결정. 코드를 만들지 않았다면 중복 구현이 없다고 단언하지 않고 **'현재 제품 소스 없음'**으로 기록.

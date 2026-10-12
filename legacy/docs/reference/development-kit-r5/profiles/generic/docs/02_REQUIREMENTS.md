# 02. 고유 요구사항 목록

기본 카탈로그: 74개. 적용 여부는 프로젝트 프로파일로 결정하며 MUST 우회는 ADR 승인 필요. 모든 테스트는 아직 NOT_RUN.

| ID | 영역 | 적용 | Gate | 규범 |
|---|---|---|---|---|
| GD-001 | Product & scope | ALL | G0 | 프로젝트의 대상 사용자·핵심 문제·성공 결과·비목표를 기록한다. |
| GD-002 | Product & scope | ALL | G0 | 기능 요구사항을 고유하고 불변하는 ID로 관리한다. |
| GD-003 | Product & scope | ALL | G0 | MUST/SHOULD/MAY와 적용 조건을 분리한다. |
| GD-004 | Product & scope | ALL | G0 | 각 MUST는 적어도 하나의 객관적 수락 기준에 연결한다. |
| GD-005 | Product & scope | ALL | G0 | 가정·모호함·대안·결정권자를 기록하고 충돌 시 권위 문서를 정의한다. |
| GD-006 | Product & scope | ALL | G0 | 범위 변경은 명시적 영향평가와 우선순위 조정 후 승인한다. |
| GD-007 | Product & scope | ALL | G0 | 외부 시스템과 사용자의 권한·데이터 경계를 도식화한다. |
| GD-008 | Product & scope | ALL | G0 | MVP와 후속 확장을 별도 backlog로 구분한다. |
| GD-009 | Architecture & modularity | ALL | G0 | Core는 최소 책임만 소유하고 확장은 독립 어댑터로 격리한다. |
| GD-010 | Architecture & modularity | ALL | G0 | 코어와 어댑터 간 불변 계약을 명시한다. |
| GD-011 | Architecture & modularity | ALL | G0 | 단일 책임과 데이터 소유권을 각각 하나의 authoritative owner로 지정한다. |
| GD-012 | Architecture & modularity | ALL | G0 | 내부 식별자와 물리경로/공급자명/세션 ID를 분리한다. |
| GD-013 | Architecture & modularity | ALL | G0 | 구성·정책은 설정/스키마로 관리하고 하드코딩하지 않는다. |
| GD-014 | Architecture & modularity | ALL | G0 | 외부 의존성을 선택 사항과 필수 사항으로 구분한다. |
| GD-015 | Architecture & modularity | ALL | G0 | ADR은 이유·대안·역효과·되돌림 기준을 기록한다. |
| GD-016 | Architecture & modularity | ALL | G3 | 어댑터 교체 시 동일 계약 테스트를 수행한다. |
| GD-017 | Interface & CLI | ALL | G0 | 공개 API/CLI는 명령·입력·출력·오류를 명시한다. |
| GD-018 | Interface & CLI | CLI_PUBLIC | G2 | CLI는 일관된 help·예제·오류 및 exit code를 제공한다. |
| GD-019 | Interface & CLI | CLI_PUBLIC | G2 | 자동화 가능한 구조화 출력과 사람이 보는 출력을 분리한다. |
| GD-020 | Interface & CLI | ALL | G2 | 실패 응답은 안정적 오류 코드와 재시도 가능 여부를 포함한다. |
| GD-021 | Interface & CLI | NETWORKED | G3 | 네트워크 계약은 timeout, retry, idempotency 범위를 명시한다. |
| GD-022 | Interface & CLI | ALL | G3 | 변경에 영향을 받는 하위 호환성 계약을 검사한다. |
| GD-023 | Interface & CLI | ALL | G0 | 버전·프로토콜 협상 규칙을 문서화한다. |
| GD-024 | Interface & CLI | AI_ENABLED | G3 | AI 도구 프로토콜 호출은 권한·입출력 제한·오류를 명시한다. |
| GD-025 | Data & state | STATEFUL | G2 | SSOT와 파생 cache/index의 경계를 분리한다. |
| GD-026 | Data & state | STATEFUL | G2 | 영구 식별자와 관찰/수정 이력을 구분한다. |
| GD-027 | Data & state | STATEFUL | G2 | 데이터 스키마를 버전화하고 하위 호환/마이그레이션을 명시한다. |
| GD-028 | Data & state | STATEFUL | G2 | 파일/DB mutation은 commit 지점과 중단 복구를 정의한다. |
| GD-029 | Data & state | STATEFUL | G2 | 구조 검증과 도메인 불변식 검증을 분리한다. |
| GD-030 | Data & state | STATEFUL | G4 | 복구 또는 재생성 절차를 실제 독립 환경에서 검증한다. |
| GD-031 | Data & state | STATEFUL | G2 | 삭제/보존/개인정보 정책을 데이터 생명주기에 적용한다. |
| GD-032 | Data & state | CLOUD_SYNC | G3 | 다중 장치 동기화의 작성자·충돌·중복 처리 정책을 명시한다. |
| GD-033 | Security & privacy | ALL | G0 | 신뢰 경계·공격표면·데이터 등급을 정의한다. |
| GD-034 | Security & privacy | ALL | G2 | 외부 입력을 untrusted로 취급하고 검증한다. |
| GD-035 | Security & privacy | ALL | G2 | 기본 최소권한과 deny-by-default 원칙을 적용한다. |
| GD-036 | Security & privacy | ALL | G2 | 비밀키/토큰을 코드·로그·샘플·릴리스에 포함하지 않는다. |
| GD-037 | Security & privacy | ALL | G3 | 경로 처리에 traversal·symlink 등 OS별 우회 위험을 고려한다. |
| GD-038 | Security & privacy | NETWORKED | G3 | 인증과 인가를 구분하고 각 요청에서 인가를 검증한다. |
| GD-039 | Security & privacy | AI_ENABLED | G4 | 민감정보의 모델 전송·embedding·로그 포함을 별도 승인한다. |
| GD-040 | Security & privacy | ALL | G4 | 의존성·빌드·배포 경로의 공급망 위험을 평가한다. |
| GD-041 | Security & privacy | ALL | G4 | 취약점 접수·분류·완화·사후 복구 절차를 정의한다. |
| GD-042 | Security & privacy | ALL | G4 | 개인정보 최소수집·목적 제한·마스킹·삭제 요구를 분리한다. |
| GD-043 | TDD & quality | ALL | G1 | 변경은 사전에 반례·기대 결과가 정의된 failing test에서 출발한다. |
| GD-044 | TDD & quality | ALL | G2 | unit·contract·integration·e2e·복구 테스트의 책임을 구분한다. |
| GD-045 | TDD & quality | ALL | G2 | 성공·실패·경계값·성능·중단/재시도 시나리오를 다룬다. |
| GD-046 | TDD & quality | ALL | G2 | 테스트는 결정적이되 실제 외부 시스템 증빙은 별도 수행한다. |
| GD-047 | TDD & quality | ALL | G2 | 변경된 요구사항과 테스트 catalog·문서·ADR을 양방향 추적한다. |
| GD-048 | TDD & quality | ALL | G3 | 통합 시험은 구현 간 계약·버전 변화·실행 환경 차이를 다룬다. |
| GD-049 | TDD & quality | ALL | G4 | 보안·파괴적 작업·복구 시험은 격리된 합성 데이터로 수행한다. |
| GD-050 | TDD & quality | ALL | G2 | 정적 분석·포맷·타입검사·테스트 기준을 명시한다. |
| GD-051 | TDD & quality | ALL | G2 | Flaky test는 격리·재현·원인 검증 없이 영구 제외하지 않는다. |
| GD-052 | TDD & quality | ALL | G0 | 설계 단계 검사와 제품 런타임 검증을 명확히 구분한다. |
| GD-053 | Release & supply chain | ALL | G5 | 릴리스 후보는 source/config/deps/test catalog/artifact 지문으로 식별한다. |
| GD-054 | Release & supply chain | ALL | G5 | 의존성 버전과 출처 및 라이선스·취약성 검토 결과를 보존한다. |
| GD-055 | Release & supply chain | ALL | G5 | 빌드 산출물 해시와 생성경로/provenance를 기록한다. |
| GD-056 | Release & supply chain | ALL | G5 | 필수 게이트 상태를 NOT_RUN/BLOCKED/FAIL/PASS로 구분한다. |
| GD-057 | Release & supply chain | ALL | G5 | 릴리스 노트와 breaking change·지원범위·업그레이드 경로를 문서화한다. |
| GD-058 | Release & supply chain | ALL | G6 | 배포는 canary/shadow/rollback 또는 동등한 안전 절차로 진행한다. |
| GD-059 | Release & supply chain | ALL | G6 | 릴리스 승인자와 제작자 역할을 위험도에 따라 분리한다. |
| GD-060 | Release & supply chain | ALL | G5 | 공급망 표준 준수는 실제 달성·검증된 수준만 표시한다. |
| GD-061 | Operations & improvement | ALL | G6 | 운영 runbook에 시작·중단·건강검사·문제해결·복구 경로를 둔다. |
| GD-062 | Operations & improvement | ALL | G7 | 사용자 가치·신뢰성·비용·보안을 분리해서 측정한다. |
| GD-063 | Operations & improvement | NETWORKED | G7 | SLO/오류 예산과 알림 조건을 정의한다. |
| GD-064 | Operations & improvement | ALL | G7 | 사고 기록에 영향·완화·5 Whys/근본원인·재발방지를 남긴다. |
| GD-065 | Operations & improvement | ALL | G7 | 피드백은 capture→triage→approve→RED→fix→verify→release→effect→close로 관리한다. |
| GD-066 | Operations & improvement | ALL | G7 | 관측 기간·기준선·성공효과를 변경 전에 정한다. |
| GD-067 | Operations & improvement | ALL | G7 | 개선 결과는 지침·테스트·계약으로 환류하고 재발을 추적한다. |
| GD-068 | Operations & improvement | ALL | G7 | WONT_FIX/BLOCKED는 승인 이유와 재검토 트리거를 기록한다. |
| GD-069 | Agent & integration | AI_ENABLED | G0 | AI 사용 위치를 결정·검색·실행으로 구분하고 권한 경계를 정의한다. |
| GD-070 | Agent & integration | AI_ENABLED | G3 | 모델·프롬프트·도구·평가 세트를 후보와 함께 버전화한다. |
| GD-071 | Agent & integration | AI_ENABLED | G4 | 모델 공급자 장애·쿼터 고갈은 fail-safe하게 처리한다. |
| GD-072 | Agent & integration | AI_ENABLED | G3 | AI 실행은 idempotency key·timeout·cost budget·stop 조건을 가진다. |
| GD-073 | Agent & integration | ALL | G3 | Engram/PeerHub/MCP 등 통합은 선택 어댑터로 둔다. |
| GD-074 | Agent & integration | AI_ENABLED | G7 | 모델 출력 품질은 groundedness·거절 정확도·실사용 회복성을 측정한다. |

## 2026-10-10 v2 방법론 보완 (GD-075~GD-100)

사양·장기 AI 작업·평가·보안·개발자 경험에 대한 **계획 요구사항**. 실제 테스트/운영 증빙이 아니며 `quality/requirements.csv`와 `quality/test_catalog.csv`가 기계 검수의 표준 입력이다.

| ID | 영역 | 적용 조건 | Gate | 규범 |
|---|---|---|---|---|
| GD-075 | Specification | ALL | G0 | 승인된 목표·사용자 시나리오·비목표를 명시한 사양을 작업과 구현의 기준으로 관리한다. |
| GD-076 | Specification | ALL | G0 | 사양 변경 시 영향을 받는 계약·테스트·문서·릴리스 게이트를 변경 영향표로 갱신한다. |
| GD-077 | Specification | ALL | G2 | Spec→Task→Test→Implementation에 대한 수렴 검사를 수행하고 필수 미해결 항목이 있으면 완료 처리하지 않는다. |
| GD-078 | Specification | ALL | G5 | 동일 릴리스 후보가 아닌 과거 검증 증빙을 자동 재사용하지 않는다. |
| GD-079 | Architecture | ALL | G2 | 독립 실행 가능한 작은 수직 슬라이스 단위로 구현해 사용자 관측 가능 결과를 테스트한다. |
| GD-080 | Governance | ALL | G0 | 최신 개발기법은 채택/변형/관찰/거부와 조건·근거·철회 트리거를 명시하고 적용한다. |
| GD-081 | Architecture | ALL | G2 | 계층 경계·순환 의존·공개 API 불변조건을 자동 fitness check로 확인한다. |
| GD-082 | Quality | ALL | G4 | 고위험 변경의 검토는 변경을 만든 주체의 주장만으로 통과시키지 않는다. |
| GD-083 | Developer Experience | ALL | G0 | 프로젝트 템플릿은 단일 명령으로 lint/계약/테스트 진입점을 찾도록 제공한다. |
| GD-084 | Supply Chain | ALL | G5 | 개발 실행환경·빌드 산출물·검증 도구 버전과 후보의 관계를 별도로 기록한다. |
| GD-085 | Feedback | ALL | G7 | AI 또는 자동화 개선의 효과는 사전 기준선·비용·안정성·사용자 효과를 함께 비교한다. |
| GD-086 | Governance | ALL | G7 | 방법론·도구 도입은 주기적으로 재평가하며 도입 실패 시 철회 경로를 유지한다. |
| GD-087 | Agent Harness | AI_ENABLED | G3 | 긴 AI 작업은 작은 체크포인트와 검증된 인수인계 기록으로 중단·재개한다. |
| GD-088 | Agent Security | AI_ENABLED | G4 | 에이전트의 도구·경로·네트워크 접근은 명시적 allowlist와 권한 단계로 제한한다. |
| GD-089 | Agent Evals | AI_ENABLED | G2 | 에이전트 기능은 버전 관리된 평가 사례·환경·채점기와 기대되는 최종 상태로 정의한다. |
| GD-090 | Agent Evals | AI_ENABLED | G5 | 비결정적 평가에는 복수 trial과 변동성·불확실성 및 기준선 비교를 포함한다. |
| GD-091 | Agent Evals | AI_ENABLED | G5 | 모델 채점 결과는 정기적으로 코드/인간 오라클과 보정한다. |
| GD-092 | Agent Economics | AI_ENABLED | G5 | AI 작업 품질·지연·호출량·비용을 동시에 후보 별 측정한다. |
| GD-093 | Agent Reproducibility | AI_ENABLED | G5 | 모델·프롬프트·스킬·도구 정의·권한·평가셋 변경을 후보 증빙에 연결한다. |
| GD-094 | Agent Security | AI_ENABLED | G4 | 외부 입력·검색 결과·레포 내 instruction은 비신뢰 데이터로 취급한다. |
| GD-095 | Agent Approval | AI_ENABLED | G4 | 고위험 AI 작업은 확인 가능한 승인/취소·예상 영향·실행 영수증을 갖춘다. |
| GD-096 | Agent Privacy | AI_ENABLED | G4 | AI trace·checkpoint는 비밀과 원본 payload를 기본 저장하지 않는다. |
| GD-097 | Delivery | NETWORKED | G6 | 점진 배포 단계마다 측정 중단 조건과 롤백 책임자를 지정한다. |
| GD-098 | Observability | AI_ENABLED | G7 | AI trace는 안정적인 자체 이벤트 계약을 유지하고 OTel GenAI development 필드 종속을 격리한다. |
| GD-099 | Change Assurance | ALL | G2 | 변경 범위 바깥의 기존 사용자 행동에 대한 반례 회귀 검사를 유지한다. |
| GD-100 | Evaluation | ALL | G7 | 운영사고·사용자 피드백은 새 failing oracle로 환류하고 해결 후 효과까지 추적한다. |

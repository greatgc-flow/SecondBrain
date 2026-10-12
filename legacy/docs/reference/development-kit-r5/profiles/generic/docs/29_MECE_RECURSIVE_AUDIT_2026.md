# 29. 최신 방법론 반영 후 재귀적 MECE 감사

## 종축: 의도→가치 실증
| 단계 | SSOT | 실패 반례 | Gate |
|---|---|---|---|
| 의도 | 승인 spec+requirements | N/A 무근거 | G0 |
| 설계 | ADR+ports/contracts | 금지 의존/계약 불일치 | G0~G2 |
| 테스트 | fail-first 실행 trace | 계획 TEST를 PASS로 오기 | G1~G2 |
| 구현 | 독립 observable behavior | 외관상 GREEN, 부작용 실패 | G2~G3 |
| 검증 | contract/integration/security + eval | 단독 AI judge 자기 승인 | G3~G5 |
| 릴리스 | candidate/attestation | 불일치 digest | G5~G6 |
| 운영 | SLO+human outcome | 성공 예시만 채택 | G7 |
| 개선 | 사례→RED→release→effect | 미실증 효과 CLOSED | G7 반복 |

## 횡축: ownership 명료화
| 책임 | canonical owner | 선택 adapter |
|---|---|---|
| 요구/승인 | 프로젝트 owner | GitHub/PeerHub mirror |
| 제품 데이터 | domain owner | SQLite/cloud |
| 권한 | 정책/실행 인가 engine | AI model/agent |
| 코드 검증 | test harness/independent reviewer | LLM judge |
| 출시증빙 | product candidate gate | CI provider |
| 관측 | 자체 event schema | OTel exporter |
| 교훈 | feedback record + revised oracle | retrospective bot |

## 아직 실제로 입증하지 않은 사항
- 요건 100개·테스트 100개는 **설계 상태**. 실구현 자동화나 시험성공을 주장하지 않는다.
- JSON Schema는 구조 계약만 확인; id↔hash↔경로, score↔trials, approve↔authority 등 semantic cross-field 규칙은 런타임/시험의 책임.
- 모든 플랫폼·cloud·agent/provider 실증은 실제 제품 프로젝트에서 수행해야 한다.
- 확장 도입은 측정된 비용/효익이 없으면 WATCH로 남긴다.

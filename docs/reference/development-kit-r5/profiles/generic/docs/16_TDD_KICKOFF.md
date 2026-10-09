# 16. TDD 착수 전 체크리스트

- [ ] 적용 프로젝트/프로파일, 사용자 가치, 데이터 등급·타깃 환경 명시
- [ ] ALL 및 조건부 MUST와 N/A 사유 승인
- [ ] Core/adapter 경계, 최소 user flow, I/F와 실패 의미 확정
- [ ] 기술 스택과 test runner/환경 독립성 결정
- [ ] `python tools/design_lint.py` 정적 검사 PASS
- [ ] 선정 GD-ID에 TEST-ID, negative fixture, expected error를 구체화
- [ ] 첫 RED: public config/unknown verb/denied action 중 타깃에 맞는 가장 작은 계약
- [ ] GREEN 후 semantic/edge, filesystem/protocol integration, security/DR 차례로 확장
- [ ] CI/Gates는 테스트 구현 후 연결; NOT_RUN을 PASS로 승격 금지

초기 단위 작업: 프로젝트 목적/예제 위주의 작은 수직 Slice 1개를 골라 RED부터 실행한다. 레이어 전체 stub만 만든 후 green이라고 하지 않는다. Step-0에서 코드 쓰지 말고 팀과 목표를 먼저 확정한다. **이 패키지는 Step-0 기준본**.

## v2 첫 RED 이후의 별도 의무
GD-075~100의 프로젝트 applicability를 계산한다. 첫 슬라이스의 `spec.md→tasks→TEST-ID` 상호 링크를 검사하고, AI_ENABLED이면 (a) 툴 허용목록, (b) 평가 oracle, (c) 체크포인트 재개, (d) prompt-injection negative case를 먼저 실패시켜야 한다. 신규 스키마 6종은 형식 계약이고 `quality/v2_semantic_oracles.md`는 실행되지 않은 계획이다.

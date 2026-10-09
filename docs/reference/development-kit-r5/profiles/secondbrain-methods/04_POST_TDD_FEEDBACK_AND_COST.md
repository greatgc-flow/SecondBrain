# TDD 후 지속 운영 · 효과 측정

1. RED→GREEN→Deterministic verifier의 원본 증거 안전성 선행.
2. AI memory/검색은 독립 평가셋과 latency/cost/precision/abstention 기록 후 켬.
3. 후보별 model/prompt/tool versions + OTel mapping revision + benchmark hash.
4. Shadow read/gradual enable: 원본 mutation 금지, active rollout 조건별 분리.
5. 운영 사고/검색실패→synthetic regression→fix→reindex/redeploy→실제 회수 성능 관측.
6. 개선 종료: 출처 정확도·복원성 유지 + 비용 변화 + 재발 여부. `CLOSED`는 테스트만으로 허용 금지.

평가자 독립성: 생성을 담당한 AI의 결과 확인용 설명은 참고에 불과. hash/source alignment 검사기와 필요 시 사용자/법률전문가 판단이 별개로 존재해야 한다.

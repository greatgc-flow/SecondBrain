# Governance v1 schema registry
독립된 `governance/v1` 축이며 `schemas/v2` Evidence 계약을 덮어쓰지 않는다. 검증 가능한 **민감정보 제거한 운영 요약**만 다룬다. JSON Schema Draft 2020-12가 표현 못 하는 의미제약(예: feedback CLOSED 시 improvement-verification EFFECTIVE+reviewer, gate PASS candidate fingerprint 일치, 관측 구간 역전 금지, gate reviewer 역할 독립)은 `docs/33`, `35`, `40`에 지정된 application semantic validator/TDD 시나리오가 enforce한다. `valid` 예제는 structural only; 실제 CI·운영 성적이 아니다.

Structural conditional guards reject CLOSED without nonempty closure evidence or PASS/MANUAL_VERIFIED without reviewer/evidence; **external proof match, valid observation period, reviewer independence and absence of privacy leaks still require semantic and real-world gates**.

Authoritative transition history uses `governance-event` chained canonical events. `feedback-case` state snapshot is a materialized read model, never silently rewritten without a corresponding event. JCS hash format/domain sequencing and offsite anchoring need runtime semantic verification.

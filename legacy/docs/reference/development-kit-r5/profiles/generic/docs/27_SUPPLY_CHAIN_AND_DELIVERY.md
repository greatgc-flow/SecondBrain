# 27. 후보-결합 provenance / Progressive Delivery

기존 G5/G6 규칙을 유지하고 구체화한다.

`source_commit + tree/config/deps_lock + contract_revision + test/eval_catalog_digest + toolchain + target_env` → **Candidate**. 각 빌드 artifact/SBOM/attestation의 digest를 독립 기록하여 candidate와 연결한다. 순환 지문 금지. SLSA 1.2 형식을 참고하지만 달성 레벨은 실제 평가받고 증거 있을 때만 표기한다.

PR 검수: 해당 변경의 untrusted workflow 실행/자격증명 권한 검토. third-party workflow/actions는 버전/출처 핀; 의존성 취약성은 CVE 수 자체가 아닌 reachability와 위험으로 triage.

릴리스: test candidate SHA ≠ shipped SHA일 때 STOP. 적용 대상 service만 canary/flag, CLI/라이브러리는 staged channel/rollback 또는 deterministic installer test. 이상 시 자동 확대 중단·rollback. 운영 gate는 이전 test green과 별개.

최소 프로젝트는 reproducible recipe+sha256+lockfile+CI test evidence를 기본, 위험도가 높은 배포에서 SBOM+서명된 attestation, isolation, human approval을 추가한다.

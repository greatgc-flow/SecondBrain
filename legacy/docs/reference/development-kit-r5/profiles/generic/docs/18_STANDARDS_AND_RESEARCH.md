# 18. 2026-10-09 기준 참고 표준 및 적용 선택

| 근거 | 확인된 상태 | 우리에게 취한 원칙 | 범용 의무 여부 |
|---|---|---|---|
| NIST SSDF SP800-218 v1.1 | 2022 Final; 800-218 Rev1 v1.2는 2025-12 Draft | prepare/protect/produce/respond 및 원인 개선 | 지침; 법적 의무로 보지 않음 |
| SLSA 1.2 | Approved | source/build provenance 와 검증된 artifact claim | 상황별 |
| DORA metrics | 5-metric model | throughput + instability, 계측·인간효과 | 운영 서비스부터 |
| OpenSSF Scorecard | 프로젝트 | 의존성·CI 보안 리스크 점검 | 선택 |
| OpenTelemetry | semantic conventions 계속 발전 | 일관된 trace/metric/log 명칭 | 관측 대상만 |
| SemVer | 버전 명세 | 공개 계약 영향에 맞는 semver | 공개 제품 권장 |
| OWASP ASVS / Top10 | 보안 지침 | 입력·권한·공급망·secret | 노출면 기반 |

공식 링크:
- https://csrc.nist.gov/pubs/sp/800/218/final
- https://csrc.nist.gov/projects/ssdf/publications
- https://slsa.dev/spec/v1.2/
- https://dora.dev/guides/dora-metrics/
- https://openssf.org/projects/scorecard/
- https://opentelemetry.io/docs/specs/semconv/
- https://semver.org/
- https://owasp.org/www-project-application-security-verification-standard/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0
- https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4

이는 출처·설계 참고목록이며, 프로젝트의 특정 규제 적합성 인증이나 자동 검증을 의미하지 않는다. 기준 시점 이후 사양은 도입 시 다시 확인.

## 추가 조사: 2026-10-10
공식 근거와 채택·배제 매트릭스는 `docs/31_RESEARCH_PROVENANCE_AND_CAUTION.md` + `quality/research_decisions_20261010.csv`가 담당한다. GitHub Spec Kit (SDD), OpenAI Harness Engineering, Anthropic 2026 Agent Evals/Long-running harness, OWASP Agentic 2026, OpenSSF secure AI instructions, CNCF golden path, OTel 1.44, DORA 2025를 재검토. OTel의 GenAI conventions 일부는 **Development**이고, SLSA 1.2는 기술 근거이지 자동 인증이 아니다.

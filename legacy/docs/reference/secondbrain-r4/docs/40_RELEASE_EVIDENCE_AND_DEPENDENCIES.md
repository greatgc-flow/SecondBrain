# 40. Candidate-bound test/release evidence와 영향 전파

## Release fingerprint
`release_candidate`는 최소 다음의 안정 식별자를 갖는다: source SHA, code tree digest, requirements revision+digest, schema registry digest, ADR baseline revision, toolchain/dependency lock digest, Python/OS/provider versions, build artifact SHA256, test plan/catalog digest, policy config digest, privacy test-data classification, build method.

`GateResult` 하나는 `candidate_id`, `gate_id`, `test_catalog_digest`, `status`, `observed_at`, `executor`, `environment_digest`, `evidence_uri`, `evidence_sha256`, `reviewer`, `waiver_reason`(해당 시), `expired_at`를 연결. Signed/attested status는 실제 서명/검증된 경우에만 제공.

## Consistency
- Current release must refer to same source+artifact as tests (candidate-bound). `all CI green`은 두 digest가 다르면 무의미.
- 테스트 evidence 파일 경로만 적지 않고 실제 sha256 기록. 해당 파일이 secret-bearing이면 public receipt에는 sanitized derived summary digest만.
- Derivation/Provenance은 SLSA Build Provenance v1의 사고방식을 참조; 포맷 호환이 필요할 때 표준 verifier로 검증. 자체 hash+JSON만으로 supply chain attestation 수준을 주장하지 않음.
- Evidence store 형식 schema/v2 및 governance schema/v1은 서로 다른 버전 축; 한쪽 migration이 다른쪽을 자동 변경하지 않음.

## 영향 규칙 (의존성 그래프)
Source code, requirements, schema, config, policy, dep-lock, runtime model, cloud provider, test catalog, evaluation corpus, build environment 중 어느 것이 변했는지 change fingerprint 비교.
1. `source/code`: G1~G6 후보 관련 게이트를 새로 수행 (사소한 comment-only 변경도 package digest 업데이트/관련 검사 재평가).
2. `schema/serializer`: migration/backward-compat, custody JSON canonical vectors, dump/reindex/rebuild, backup restore, export 다시 검증.
3. `security policy`: egress/ACL/hold/retention, negative tests, manual review 다시 수행.
4. `dependency/parser`: SBOM+vuln+parser sandbox, golden content fixtures, extraction drift 비교.
5. `AI/model/prompt`: corpus eval + privacy test + citations/temporal scoring 다시 수행.
6. `cloud/storage/Writer`: cross-device/sync/DR/authority manual drill, RPO/RTO measurement.
7. `docs-only`: link/trace/audit/spec consistency와 영향받는 operator guide 검토. 실행 gate 재활용은 문서 변경이 binary/behavior에 영향 없다는 근거를 남긴 경우에만.
8. `evaluation harness/tests`: 이전 PASS evidence는 그 테스트셋에만 유효. 새로운 catalog 요구는 candidate release부터 gate 재실행.

## Gate freshness
`PASS` has explicit `valid_for` set of fingerprints. 영향을 받는 fingerprint 변화 시 **STALE**. 실행하지 않은 테스트는 `NOT_RUN`; TIMEOUT/INFRA_ERROR는 FAIL과 구별하되 필수 Gate 승인은 모두 BLOCK.

## Branch / tag / rollback
- Tag/commit/digest for release, `last_known_good` and `previous_root` separately recorded.
- Rollback is not copying code only: migration compatibility + canonical data writer epoch + restoration provenance verified. Upgrade rollback tested before rollout.
- Signed approval applies to one frozen candidate, not to future 'latest' or branch tip.

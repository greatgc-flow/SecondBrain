# 04. 아키텍처, Core vs Extension, 저장소 구조

```text
[Human / API / CLI] → [Application boundary] → [Domain Core / Ports]
                                                  ↓
                                            [Adapter Plug-ins]
                                       (FS, DB, Cloud, AI, PeerHub...)
[Config + Secrets] → validate                    ↑
[Observability] ← stable events (no secrets)      |
[Quality/Governance] -- candidate and gate receipts (independent)
```

Core는 business invariant와 결정적 상태 전이만 소유. 바깥 계층은 프로토콜 구현·실시간 provider 클라이언트. CLI, HTTP, MCP는 adapter다. 한 곳만 변경해도 통합 계약 시험이 있으면 충분한 소형 제품에 방대한 microservice를 강요하지 않는다.

## 권장 코드 저장소
```
repo/
  src/<project>/core/       # use cases + domain rules
  src/<project>/ports/      # transport/storage-neutral contracts
  src/<project>/adapters/   # optional provider implementations
  src/<project>/cli/        # only if CLI_PUBLIC
  tests/unit/ tests/contract/ tests/integration/ tests/e2e/
  docs/adr/ docs/contracts/ docs/runbooks/
  config/ examples/ tools/
  .github/workflows/        # only after tests exist
```

언어별 idiom이 더 좋은 경우 디렉터리명은 바꿔도 됨. 결정되지 않은 물리 폴더 위치를 Core 상수로 못 박지 않는다.

## 상태 저장
영속성 없으면 DB 필수 아님. 있으면 canonical state와 rebuildable projection 분리. distributed writer 요구가 확인되지 않았다면 단일 transaction owner 우선. 캐시를 '복구 가능한 SSOT'라고 부르지 않는다.

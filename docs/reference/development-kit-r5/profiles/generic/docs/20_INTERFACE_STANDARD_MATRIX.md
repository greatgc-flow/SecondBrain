# 20. CLI·계약·확장 표준 간 횡적 정렬

| 표준 | Core | Extension | 문서 | TDD |
|---|---|---|---|---|
| 명령/작업 | use case ports | CLI/REST/MCP adapter | `05_INTERFACES_CLI.md` | malformed args, unauthorized |
| 설정 | validated effective config | product/provider-specific | `06_CONFIG_SECURITY.md` | precedence, secret redaction |
| 데이터 | schema+semantic invariants | SQLite/FS/Cloud | `07_DATA_AND_MIGRATION.md` | corruption, recovery |
| 관측 | stable event contract | OpenTelemetry/UI | `14_METRICS_AND_OPERATIONS.md` | sensitive payload absent |
| AI 협업 | none required | PeerHub adapter | `15_ADAPTERS_AND_INTEGRATIONS.md` | provider off = Core works |
| 릴리스 | candidate receipt | CI/package backend | `10_GATES_RELEASE.md` | stale candidate rejected |
| 개선 | canonical feedback state | GitHub/PeerHub projection | `12_FEEDBACK_LOOP.md` | effect absent => no CLOSED |

비교 핵심: 동일 책임은 두 계층에서 동시에 소유하지 않는다. 다른 I/F에 같은 메시지를 두 번 써야 한다면 한 쪽이 canonical, 다른 쪽은 view/adapter.

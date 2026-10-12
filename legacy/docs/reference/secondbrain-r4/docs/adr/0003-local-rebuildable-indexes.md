# ADR-0003 Local rebuildable indexes

Status: Accepted

## Decision
SQLite FTS, vectors, graph cache는 `%LOCALAPPDATA%` 아래 local-only state로 둔다.

## Rationale
sync engine은 database transaction semantics를 보장하지 않는다.

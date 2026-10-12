# ADR-0001 Filesystem-first SSOT

Status: Accepted

## Decision
Second Brain은 cloud API가 아닌 일반 filesystem root를 canonical storage boundary로 사용한다.

## Consequences
- OneDrive/Google Drive/Dropbox/NAS 교체 가능
- OAuth/API dependency 없음
- provider metadata 자동수집은 core 책임 아님

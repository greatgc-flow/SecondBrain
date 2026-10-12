# ADR-0004 Primary sync + Secondary snapshot

Status: Accepted

## Decision
OneDrive/Google Drive 중 하나를 Primary live sync로 사용하고 다른 쪽은 dated snapshot backup 용도로 사용 가능하다.

동일 live tree에 두 sync engine을 붙이지 않는다.

# 14. Naming / IDs / Filesystem Rules

## 1. Identity != filename

파일명은 표시/편의값이다.
Identity는 stable ID + digest.

## 2. Proposed IDs

```text
BR-...  brain id
EV-...  evidence record
OB-...  evidence object
OV-...  observation
AQ-...  acquisition event
CU-...  custody event
DV-...  derivation
PR-...  production
LH-...  legal hold
SN-...  snapshot
KN-...  knowledge note
```

실제 suffix 알고리즘은 OD-001에서 결정.

## 3. Object path

```text
10_Evidence/Vault/objects/sha256/ab/cd/<full-sha256>/payload
```

관련 record:
```text
10_Evidence/Records/objects/<object_id>.json
```

## 4. Filename preservation

Original filename은 metadata에 Unicode 그대로 보존.
filesystem-invalid char 처리 시 storage alias와 original filename을 분리.

## 5. Case sensitivity

Windows 호환성을 위해 canonical ID/path는 ASCII lower/upper 규칙을 고정해야 한다.
Object hash path는 lowercase hex 권장.

## 6. Unicode

display title/filename은 Unicode 허용.
ID, machine filenames는 ASCII-safe 권장.

## R2 accepted naming rules
Suffix = lowercase canonical UUIDv7 with UUIDv7 version/variant enforcement; EX: `EV-018fa2b3-12cd-7abc-8abc-0123456789ab`. Object identity `obj-sha256-<lowercasehex>`. All paths are root-relative slash form; absolute physical paths only live in local config or optional sanitized acquisition descriptions. `brain://evidence/EV-...` is application URI, not actual network route. See `docs/31_REQUIREMENT_AMENDMENTS.md`.

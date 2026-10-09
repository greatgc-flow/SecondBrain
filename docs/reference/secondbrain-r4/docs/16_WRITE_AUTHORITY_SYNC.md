# 16. OneDrive/Google Drive에서의 쓰기 권한 및 충돌 모델

## 결정 (ADR-0011)
**R2의 최소 안전 구성은 *canonical one-writer*, 많은 capture-only 기기다.** 지정 장치만 `10_Evidence/Vault`, `Records`, `40_Meta`, `20_Knowledge`의 자동 mutation을 commit할 수 있다. 다른 PC는 `00_Inbox/Drop/<device-id>/<capture-id>/`라는 독립 경로에 원본 + sidecar/receipt를 *추가*한다. 타 PC가 저장한 문서의 소유자가 직접 편집한 지식노트는 별도 review/merge 채널에서 반영.

## 왜 이 결정인가
Windows 로컬 rename의 atomicity는 동일한 cloud sync root를 사용하는 서로 다른 호스트 사이에서 **distributed commit**을 뜻하지 않는다. Provider가 conflict copy를 만들 수 있고, 오프라인 중 두 PC의 업데이트 순서도 명확하지 않다. 클라우드 제공자 API가 없는 상태에서 임의 다중 Writer 전역 CAS/락은 제공할 수 없다.

## Capture-only 프로토콜
1. 각 기기는 영속적 무작위 `device_id`를 만들고 절대 두 기기에 복제해 쓰지 않는다.
2. 신규 수집마다 `capture_id`(UUIDv7)를 발급하고 `capture.receipt.json`에 source/actor/time/path/declared hash/size를 채운다.
3. 로컬 staging에서 원본 bytes를 안정화·해시하고 sidecar와 함께 새 디렉터리 생성. *모든 파일이 복사·검증된 뒤* 동일 파일시스템 내 `.ready` marker를 마지막으로 쓴다.
4. 클라우드 경로에는 임시/부분 capture가 노출될 수 있다. Writer는 marker 존재만으로 READY를 선언하지 않고 `manifest`, bytes, source hash, size, 안정화·재독을 확인한다.
5. Writer는 `(device_id,capture_id)`를 ingest idempotency key로 사용. 동일 key+동일 payload는 재실행으로 취급; **동일 key+다른 payload면 conflict/quarantine**.
6. 같은 SHA bytes가 다른 capture_id로 오면 object만 재사용하고 *독립 Observation*을 쓴다.
7. 처리 완료 `result.json`은 Writer가 기기별 capture 디렉터리 하위 새 경로에 남긴다(상호 덮어쓰기 금지).

## 단일 Writer failover
- 운영자 승인, **이전 Writer 종료 및 미완료 작업 정리, Primary 동기화 완료 확인, backup 확보**, 새 Writer 변경 이벤트를 기록한 뒤 다른 기기를 승격.
- 이전 Writer가 복귀해도 자기 권한 epoch가 다르면 canonical mutation 금지.
- **동시에 두 Writer를 강제로 실행해도 안전하다고 주장하지 않는다.** split-brain 감지 시 ingest pause + conflict review + latest verified backup 참조.
- 공유 cloud 폴더를 통한 lease만으로 split-brain을 막을 수 없음. R2에서는 automatic failover 금지.

## 동기화와 삭제 충돌
- Primary root 아래 동기화 실패, placeholder, duplicate(conflicted copy), 파일이 사라짐, 경로 교체는 **미확정 상태**로 분류하고 fail-closed.
- source 원본 삭제 금지; Drop 정리도 verified custody event + retention policy 이후 운영자 확인이 있을 때만.
- Cloud 파일이 호스트에 존재하더라도 정상 업로드 완료를 증명하지 않음. Provider UI/기기 확인과 수동 checklist 별도.
- cloud 폴더를 primary로 선택하면 대량 object 수·경로 길이·OS 대소문자 충돌을 phase별로 실측.

## Multi-device 미래 확장
고급 분산 Writer는 서버형 coordinator/DB/cloud API 또는 CRDT/merge 정책을 도입하는 별도 R3 ADR 전까지 Out of Scope. R2는 '다중 PC 접수'를 지원하지만 '동시에 canonical write'는 지원하지 않는다.

# 07. 데이터 계약·버전·이전

- 자료 종류: source/command/event/read-model/cache/log/artifact의 owner와 생명주기를 분리.
- canonical source는 추적 가능한 ID·작성·변경시점·version을 가지며 검증된 migration 이력 없이는 silent reinterpretation 금지.
- Domain invariant는 JSON Schema만으로 표현 불가(필드 간 해시/총합·권한·시간/관계·실파일 존재). 구조 validator → semantic validator → operational verification 순서 유지.
- crash safety: prepare → stage → validate → atomic publish or transactional commit → verify receipt. 장애 불확실 시 복구가 먼저, 중복 실행 아님.
- Backup=독립 recovery domain과 복원 성공. Sync mirror나 CI artifact는 기본적으로 backup 아님.
- 영속 데이터가 **없다면** 본 문서의 migration/backup을 N/A로, 사유·future trigger와 함께 기록한다.

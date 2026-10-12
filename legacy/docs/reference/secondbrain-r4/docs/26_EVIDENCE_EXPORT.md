# 26. 사건별 Export / 증거묶음 생성 설계

## 기본 원칙
증거 원본 수집 ≠ 조사 분석 ≠ 제출 편집/마스킹. 출력물은 **다른 artifact**이며 원본의 복사인지 전사인지 발췌인지 가공인지 사실대로 표현해야 한다. 사본을 '원본'이라고 라벨링하지 않는다.

## Exhibit production manifest
- `production_id`, `matter_id`, `created_at`, `creator`, `purpose`, `recipient`(선택).
- 항목별 `evidence_id`/`object_sha256`, 원 파일명/문서일자 관련 관측 근거, 제출표제/증 번호, 순서.
- 발췌: PDF `source_page_index`(0-base), `printed_page_label`(별도), page range; 녹취/영상은 start/end timecode.
- redaction: 대상 field, 이유, 적용 기술, 숨은 텍스트 제거 확인 절차, output digest.
- PDF merger/renderer/텍스트 추출 도구 버전과 config digest 및 page total.
- `output_sha256`, 생성 후 재검증, `manifest-sha256.txt`, 원본·파생 lineage graph.
- 수신측 독립 검증 가이드와 root-independent URI mapping을 포함.

## 제출 패키지 레이아웃 (BagIt v1.0 호환 가능)
```
Case_<matter_id>_<production_id>/
  bagit.txt
  bag-info.txt
  manifest-sha256.txt
  tagmanifest-sha256.txt
  metadata/
    production.json
    exhibit-index.csv
    custody-report.jsonl
    lineage-report.json
    validation-report.json
  data/
    originals/    # 외부 제공이 허용된 원본만
    exhibits/     # 편집/마스킹 제출본
    ancillary/    # 별도 표기한 발췌/스크린샷/전사
```
`metadata/`를 Tag Files로 둘 때 BagIt 형식 규칙 충족 여부, `tagmanifest` 등 실제 validator로 테스트해야 한다. 사용자 제공 맥락에 따라 원본 전체가 없는 경우 '미포함'을 표시하고 임의로 '완전'을 선언하지 않는다.

## 문서 종류별 위험
- Screenshot/SNS: 원래 페이지·맥락·아이디·날짜/조회시점·캡처 방법 기재; 허위 원본성 단정 금지.
- EML: 원시 헤더/본문/첨부 보존; 인쇄 PDF는 별도 view.
- 디지털 서명된 PDF: 변환/병합하면 서명 유효성 변할 수 있으므로 원본과 검증 리포트를 함께 보존.
- OCR/전사: AI/사람 오인식 가능, 원본 인용과 구별.
- 사진 EXIF/메타 시간: EXIF 변조가능/기기 시간 부정확 가능성 설명.

## 중요 Disclaimer
이 패키지 설계는 보존과 설명가능성을 위한 것이다. 사건의 증거능력·취득의 적법성·진정성립/전문법칙 충족 여부는 별도 법률 판단 사항이다.

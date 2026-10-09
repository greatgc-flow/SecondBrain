# 11. Secure Software Supply Chain

프로젝트 크기에 맞춰: dependencies lock/review, SBOM(SPDX/CycloneDX 중 채택), 취약점 triage, license review, 코드 리뷰, 최소권한 CI, source/build provenance, artifact digest, reproducibility 목표. 외부 action/publisher 고정 버전 및 서명 검증. SLSA v1.2는 정식 표준이지만, 그 이름만 문서에 붙이고 달성했다고 주장하지 않는다. 승인받은 artifact와 실제 배포 artifact 동일성 확인.

고위험 프로젝트가 아니라면 불필요한 빌드 증빙 인프라부터 개발하지 않는다. 최소 source SHA / lockfile / artifact checksum / peer review로 시작하고, 위협·배포 채널에 따라 서명과 provenance 단계를 올린다.

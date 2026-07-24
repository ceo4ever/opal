# ADD_DONE-1: opdd 클러스터 7페이지 related `.md` 접미사 정비

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-07-10 13:20 ~ 14:08 (KST) |
| 사유 | 053에서 강화된 validate 링크필드 검사가 실 `.opal/brain`에서 opdd 클러스터 7페이지의 `.md` 접미사 related 24건을 신규 `frontmatter_invalid`로 표면화. R-K1 승인분(1페이지)을 초과하는 스코프라 캡틴 에스컬레이션 → "추가작업으로 즉시 정비" 승인 (AGENTIC-LOG #6) |
| 변경 내용 | 7페이지 frontmatter `related` 값의 `.md` 접미사 24항목을 평탄 슬러그로 정규화. 본문 위키링크·다른 frontmatter 필드 불변(surgical). `.md` 제거형 슬러그 7종 전부 실제 페이지 존재를 PM이 사전 확인 |
| 변경 파일 | `.opal/brain/pages/concept/dict-선행-model-ssot.md`, `concept/erd-modeler-deprecation.md`, `concept/opdd-design-artifacts-path-pattern.md`, `entity/op-data-ddl-skill.md`, `entity/op-data-dictionary-skill.md`, `entity/op-data-model-skill.md`, `flow/opdd-pipeline-flow.md` (7파일, 각 related 1줄만 변경 — git numstat 1/1 PM 실측) |
| 검증 결과 | PASS — 강화 validate(프로젝트 소스) `valid: true, violations: 0` PM 직접 재현. frontmatter `.md` grep 0건. lint missing_link는 advisory로 본문 미수정에 따른 기존 이슈 잔존(47건, 신규 유발 아님 — 본문 위키링크는 TASK 명시 제외 범위) |

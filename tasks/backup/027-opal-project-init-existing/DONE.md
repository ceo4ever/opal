# DONE: opal-project-init 기존 프로젝트 지원 (모드 분기)

> 완료일: 2026-03-21 | 모드: Short Task | 작업 유형: 개선

## 완료 요약

opal-project-init 스킬에 "기존 프로젝트" 모드를 추가했다. Step 0에서 신규/기존 모드를 자동 감지하여 분기하며, 기존 모드에서는 코드+LLM 플랫폼 파일을 자동 분석하여 플레이스홀더를 채우고, 인터뷰는 확인/보정만 수행한다. apply.js에 기존 파일 백업 및 CLAUDE.md OPAL 마커 기반 병합 로직을 추가했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/opal-project-init/SKILL.md` | Step 0 모드 분기, Step 0-A 자동 분석(소스+LLM 파일), Step 0-B 확인/보정 인터뷰, 템플릿 필터링, 트리거 4개 추가 |
| 2 | `skills/opal-project-init/scripts/apply.js` | --mode existing, backupFile(), mergeClaudeMd(), mergeAppend(), excludeTemplates 필터링 |
| 3 | `skills/opal-project-init/README.md` | 기존 프로젝트 모드 섹션, 트리거 갱신, FAQ 보강 |
| 4 | `opal/core/references/skills.md` | opal-project-init 트리거/설명 갱신 |

## 핵심 변경 사항

### Before
- 신규 프로젝트 전용 (인터뷰로 모든 정보 수집)
- 기존 파일 무조건 덮어쓰기
- 트리거: "프로젝트 에이전트 만들어줘" 1개

### After
- 신규/기존 듀얼 모드 (자동 감지 + 수동 선택)
- 기존 모드: 코드+LLM 파일 자동 분석 → 확인/보정형 인터뷰
- 기존 파일 백업(.bak) + CLAUDE.md OPAL 마커 병합 + docs 스킵
- 트리거 5개로 확장

## QA 결과

| 단계 | 결과 | 비고 |
|------|------|------|
| QA-PLAN | Pass | 5/5 항목 통과 |
| QA-EXECUTE | Pass | 7/7 항목 통과, Warning 1건(레지스트리 갱신) 추가 반영 |

## 산출물 목록

| 파일 | 설명 |
|------|------|
| tasks/027-opal-project-init-existing/TASK.md | 작업 정의서 |
| tasks/027-opal-project-init-existing/PLAN.md | 통합 PLAN |
| tasks/027-opal-project-init-existing/QA-PLAN.md | PLAN QA |
| tasks/027-opal-project-init-existing/QA-EXECUTE.md | EXECUTE QA |
| tasks/027-opal-project-init-existing/DONE.md | 완료 리포트 |

# DONE: 테스트 도구 레지스트리 설계 및 TEST-SCENARIO 통합

> 완료일: 2026-03-19 | 모드: Short Task | 작업 유형: 신규 개발

## 완료 요약

프로젝트별 테스트 도구를 선언적으로 관리하는 `test-tools.yaml` 레지스트리를 설계하고, TEST-SCENARIO 작성 시점에 도구를 결정하도록 `test-scenario-guide.md`와 `task-flow-test/AGENT.md`를 개선했다. 플랫폼별(mac/windows/linux) install 명령 분기 구조를 적용하여 크로스플랫폼 환경을 지원한다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/templates/test-tools.yaml` | 신규 생성 — 도구 레지스트리 스키마 (version/stack/global/tools 구조) |
| 2 | `opal/core/references/test-tools-schema.yaml` | 신규 생성 — 스키마 필드 명세 레퍼런스 |
| 3 | `skills/task-flow/references/test-scenario-guide.md` | 수정 — 도구 결정 시점을 EXECUTE 후 → TEST-SCENARIO 작성 시점으로 변경 |
| 4 | `agents/claude/task-flow-test/AGENT.md` | 수정 — Step 1을 레지스트리 로드/설치 확인/실행 검증으로 세분화, OS 감지 로직 추가 |

## 핵심 변경 사항

### Before
- 도구 결정: task-flow-test가 EXECUTE 완료 후 즉석 결정
- TEST-SCENARIO `도구` 필드: `_{task-flow-test가 채움}_`
- install 명령: 단일 문자열 (맥 전용 `brew install`)
- 도구 관리: 중앙화 수단 없음

### After
- 도구 결정: task-flow-agent가 TEST-SCENARIO 작성 시 레지스트리 참조하여 결정
- TEST-SCENARIO `도구` 필드: `{task-flow-agent가 결정 / task-flow-test가 검증}`
- install 명령: 플랫폼 맵 (`mac/windows/linux`) + `install_fallback`
- 도구 관리: `.opal/test-tools.yaml` 선언적 레지스트리 (global 필수 + 스택별 선택)

## QA 결과

| 단계 | 결과 |
|------|------|
| QA-PLAN | ⚠️ Needs Revision (Warning 2건 → 수정 반영) |
| QA-EXECUTE | ✅ Pass (7개 항목 중 6 Pass, 1 Info) |

## 산출물 목록

| 파일 | 설명 |
|------|------|
| `tasks/016-test-tools-registry/TASK.md` | 작업 정의서 |
| `tasks/016-test-tools-registry/PLAN.md` | 통합 PLAN + 체크리스트 |
| `tasks/016-test-tools-registry/QA-PLAN.md` | PLAN QA 리뷰 |
| `tasks/016-test-tools-registry/QA-EXECUTE.md` | EXECUTE QA 리뷰 |
| `opal/templates/test-tools.yaml` | 도구 레지스트리 템플릿 |
| `opal/core/references/test-tools-schema.yaml` | 스키마 레퍼런스 |

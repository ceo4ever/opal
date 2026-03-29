# OPAL Agents Registry

OPAL 에이전트가 호출할 수 있는 서브에이전트 목록.
각 에이전트는 독립 컨텍스트에서 실행되며, 호출 시 해당 AGENT.md(또는 SKILL.md)를 Read로 읽어 지시를 전달한다.

## opal-pilot 에이전트

opal-pilot 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe, opal-project-pilot)가 호출하는 서브에이전트.

### opal-task-agent

- **역할**: 범용 워커 — 오케스트레이터가 전달한 단계 스킬(op-task-plan, op-task-execute, op-dev-analysis, op-dev-plan 등)의 SKILL.md를 Read하고 프로세스를 따라 산출물 생성
- **호출 시점**: 각 단계 시작 시 오케스트레이터가 디스패치
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨벤션
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **참고**: opal-project-pilot에서는 op-task-plan(opus), op-task-execute(sonnet)을 사용

### op-task-qa-agent

- **역할**: QA 에이전트 — op-task-qa 스킬을 Read하고 산출물 품질 검증 수행
- **호출 시점**: ANALYSIS, PLAN, WIREFRAME, EXECUTE-UI 완료 후 오케스트레이터가 호출
- **입력**: 검증 대상 산출물 경로, 단계명, TASK.md 경로
- **출력**: QA-{단계}.md 리뷰 문서

### op-dev-test-agent

- **역할**: Test 에이전트 — TEST-SCENARIO.md 기반 동적 검증 (테스트 실행 + 결과 채움 + 판정)
- **호출 시점**: EXECUTE 완료 후 오케스트레이터가 호출
- **입력**: TEST-SCENARIO.md, 변경된 파일 목록, 모드(full-simple/full-complex/short)
- **출력**: TEST-SCENARIO.md (결과 채움 + 판정)

## 탐색 경로

에이전트 파일 탐색 우선순위 (플랫폼 공통):

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

## web-to-markdown 에이전트

### wtm-agent

- **역할**: web-to-markdown 에이전트 — 단일 URL을 받아 Phase 1(WebFetch) → Phase 2(Crawl4AI) 폴백 전략으로 웹 페이지를 마크다운으로 변환
- **호출 시점**: web-to-markdown 스킬에서 URL별로 오케스트레이터가 디스패치
- **입력**: url, save_path, mode (full/clean)
- **출력**: 마크다운 파일 (save_path에 저장)

## 향후 추가 에이전트

새로운 에이전트 등록 시 아래 형식으로 추가:

```markdown
### {agent-name}

- **역할**: {한줄 설명}
- **호출 시점**: {언제 호출되는지}
- **입력**: {필요한 입력}
- **출력**: {생성하는 산출물}
```

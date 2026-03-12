# OPAL Agents Registry

OPAL 에이전트가 호출할 수 있는 서브에이전트 목록.
각 에이전트는 독립 컨텍스트에서 실행되며, 호출 시 해당 AGENT.md(또는 SKILL.md)를 Read로 읽어 지시를 전달한다.

## task-flow 에이전트

task-flow 스킬의 각 단계에서 호출되는 서브에이전트.

### task-flow-qa

- **역할**: 산출물 품질 검증 (5단계 문서 리뷰)
- **호출 시점**: task-flow 각 단계(TASK, RESEARCH, PLAN, TODO, EXECUTE) 완료 후
- **입력**: 검증 대상 산출물 경로
- **출력**: QA-{단계}.md 리뷰 문서

### task-flow-planner

- **역할**: 실행 아키텍처 설계 (복잡 모드 Part C 생성)
- **호출 시점**: TODO 단계에서 복잡 태스크로 판별 시
- **입력**: TASK.md, RESEARCH.md, PLAN.md, TODO.md (Part A+B)
- **출력**: TODO.md Part C (실행 토폴로지)

### task-flow-test

- **역할**: 코드 동적 검증 (테스트 실행)
- **호출 시점**: EXECUTE 단계 완료 후 (복잡 모드)
- **입력**: 구현된 코드, TODO.md 체크리스트
- **출력**: TEST-REPORT.md

## 탐색 경로

에이전트 파일 탐색 우선순위 (플랫폼 공통):

1. `{프로젝트}/.cursor/agents/{agent-name}.md`
2. `{프로젝트}/.cursor/agents/{agent-name}/AGENT.md`
3. `{프로젝트}/.claude/agents/{agent-name}/AGENT.md`
4. `{프로젝트}/.agent/skills/{agent-name}/SKILL.md`
5. `~/.cursor/agents/{agent-name}.md`
6. `~/.cursor/agents/{agent-name}/AGENT.md`
7. `~/.claude/agents/{agent-name}/AGENT.md`
8. `~/.gemini/antigravity/skills/{agent-name}/SKILL.md`

## 향후 추가 에이전트

새로운 에이전트 등록 시 아래 형식으로 추가:

```markdown
### {agent-name}

- **역할**: {한줄 설명}
- **호출 시점**: {언제 호출되는지}
- **입력**: {필요한 입력}
- **출력**: {생성하는 산출물}
```

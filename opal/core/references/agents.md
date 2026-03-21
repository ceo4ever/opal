# OPAL Agents Registry

OPAL 에이전트가 호출할 수 있는 서브에이전트 목록.
각 에이전트는 독립 컨텍스트에서 실행되며, 호출 시 해당 AGENT.md(또는 SKILL.md)를 Read로 읽어 지시를 전달한다.

## dev-task-pilot 에이전트

dev-task-pilot 스킬의 모드별 파이프라인에서 호출되는 서브에이전트.

### 워커 에이전트

#### dtp-dev-agent

- **역할**: Full Task / Short Task 공용 워커 — 오케스트레이터가 전달한 단계(ANALYSIS/PLAN/PLAN-SHORT/TODO/TEST-SCENARIO/EXECUTE/EXECUTE-SHORT)를 독립 컨텍스트에서 실행
- **호출 시점**: Full/Short Task 각 단계 시작 시 오케스트레이터가 디스패치
- **입력**: 단계, 태스크 폴더 경로, 이전 산출물 경로, 가이드 경로, 프로젝트 컨벤션 경로
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)

#### dtp-wireframe-ui-agent

- **역할**: Wireframe UI 워커 — WIREFRAME(wireframe-builder 호출) 및 EXECUTE(ui-designer 호출) 단계 실행
- **호출 시점**: Wireframe UI 파이프라인의 WIREFRAME/EXECUTE 단계 시작 시
- **입력**: wireframe.md 경로(또는 입력물 경로), 출력 모드, 프로젝트 경로
- **출력**: wireframe.md(WIREFRAME 시) / 구현된 UI 파일 + changed_files(EXECUTE 시)

### QA 에이전트

#### dtp-qa-dev-agent

- **역할**: Full/Short Task 산출물 품질 검증 (정적 문서 리뷰)
- **호출 시점**: ANALYSIS, PLAN 완료 후 오케스트레이터가 호출
- **입력**: 검증 대상 산출물 경로, 모드(full/short), 단계(ANALYSIS/PLAN)
- **출력**: QA-{단계}.md 리뷰 문서

#### dtp-qa-wireframe-agent

- **역할**: Wireframe UI 파이프라인 QA (wireframe.md 검증 + 빌드/린트 + wireframe↔코드 대조)
- **호출 시점**: WIREFRAME 완료 후, EXECUTE 완료 후
- **입력**: wireframe.md 경로, 구현 파일 경로 목록, 검증 시점(WIREFRAME/EXECUTE)
- **출력**: QA-WIREFRAME.md(WIREFRAME 시) / QA-EXECUTE-UI.md(EXECUTE 시)

### 보조 에이전트

#### dtp-action-plan-agent

- **역할**: 실행 아키텍처 설계 (복잡 모드 Part C 생성)
- **호출 시점**: Full Task TODO 단계에서 복잡 태스크로 판별 시
- **입력**: TASK.md, ANALYSIS.md, PLAN.md, TODO.md (Part A+B)
- **출력**: TODO.md Part C (실행 토폴로지)

#### dtp-dev-test-agent

- **역할**: 코드 동적 검증 (테스트 실행)
- **호출 시점**: Full/Short Task EXECUTE 단계 완료 후
- **입력**: TEST-SCENARIO.md, 변경된 파일 목록, 모드(full-simple/full-complex/short)
- **출력**: TEST-SCENARIO.md (결과 채움 + 판정)

## 탐색 경로

에이전트 파일 탐색 우선순위 (플랫폼 공통):

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

## web-to-markdown 에이전트

### 워커 에이전트

#### wtm-worker

- **역할**: web-to-markdown 워커 — 단일 URL을 받아 Phase 1(WebFetch) → Phase 2(Crawl4AI) 폴백 전략으로 웹 페이지를 마크다운으로 변환
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

# op-task-execute

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project`가 EXECUTE 단계에서 디스패치합니다.

PLAN.md의 실행 체크리스트를 따라 파일 작성/수정/삭제를 수행하는 범용 실행 스킬입니다.

## 역할

PM이 agents.md 매핑 테이블에 따라 선택한 워커 에이전트(폴백: `opal-task-agent`)의 컨텍스트에서 실행되며, `personas/generalist-executor.md` 페르소나를 사용합니다. 개발 파일럿 전용인 `op-dev-execute`와 달리 FE/BE 전환 페르소나·`execution-plan.json`·ui-designer 연동·SQL Injection 등 보안 가드레일·FE/BE 병렬 실행이 없으며, 단일 모드로 순차 direct 실행만 수행합니다.

`references/execute-guide.md`의 금지 행동·가드레일을 먼저 숙지한 뒤, PLAN.md 섹션 3 실행 체크리스트를 의존성 순서대로 하나씩 실행합니다. 각 Step마다 대상 파일을 확인(존재 시 Read)하고, Write/Edit 또는 Bash로 파일을 작성·수정·삭제한 뒤 완료 기준으로 검증하고 체크박스를 `[x]`로 갱신합니다. `.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`(및 프로젝트 `.opal/code-scan.json` 확장분)에 해당하는 파일은 `~/.opal/references/header-standard.md` 포맷에 따라 `@header`를 작성·갱신합니다. 모든 Step 완료 후 PLAN.md 섹션 4 QA 체크리스트를 자체 검증해 통과 항목을 갱신합니다.

절대 금지 사항은 PLAN.md에 없는 파일 생성/수정, PLAN에서 확정된 설계를 임의로 변경하는 것입니다. 블로커 발생 시 즉시 중단하고 Step 번호·상황·원인·해결 방안을 사용자에게 보고한 뒤 지시를 대기합니다.

## 입력

- `checklist_source`: 오케스트레이터가 지정하는 경로+섹션(PLAN.md 섹션 3 실행 체크리스트)

## 출력

- 파일 변경(생성/수정/삭제)
- 구조화 결과: `{"artifact_path", "summary", "status": "completed | blocked", "blockers": [], "changed_files": []}`

## 호출 시점

오케스트레이터(`opal-pilot-project`)가 EXECUTE 단계를 디스패치할 때, PLAN.md 실행 체크리스트가 확정된 이후 실행됩니다.

## 관련 문서

- `opal/skills/op-task-execute/references/execute-guide.md`
- `opal/skills/op-task-execute/personas/generalist-executor.md`
- `~/.opal/references/header-standard.md`

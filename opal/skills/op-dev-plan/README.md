# op-dev-plan

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`가 PLAN 단계에서 디스패치합니다.

TASK와 ANALYSIS를 실행 가능한 계약·Work items·위험·릴리즈/복구 계획으로 변환하는 단계입니다.

## 역할

TASK의 문제·결과·영향 범위·AC/C와 ANALYSIS의 확인 사실·변경 경계·가정·handoff를 재조사하거나 다른 이름으로 복제하지 않고, 이를 바탕으로 구현 순서와 실행 그룹을 확정합니다. Work items에는 실제 담당 agent, 배타적 파일 소유권, 선행 작업, 실행 그룹을 명시해 병렬/순차 실행 순서를 정합니다.

## 입력

- 필수: `task_folder`, `TASK.md`
- 선택: `ANALYSIS.md`, PM이 주입한 프로젝트 문서와 실행 capability

## 출력

- `PLAN.md` (sdlc-v2: `Approach / Decisions and contracts / Work items / Risks / Release and recovery`)
- 구현으로 내용이 달라지는 문서만 Work item의 변경 대상에 포함 (참조 전용 문서·문서 전문 복제는 제외)
- `TEST-SCENARIO.md`, `execution-plan.json`, QA 문서, 단계·승인 상태는 생성하지 않음

## 호출 시점

`opal-pilot-dev`(개발 오케스트레이터)가 PLAN 단계를 워커에게 디스패치할 때 호출됩니다.

## 완료 검증

산출 후 다음 gate 명령이 통과해야 합니다.

```bash
~/.opal/tools/state-tool/run.sh verify <task-folder> --plan-contract-check
~/.opal/tools/state-tool/run.sh verify <task-folder> --code-scan-citation-check
```

## 관련 문서

- `opal/skills/op-dev-plan/references/plan-guide.md`

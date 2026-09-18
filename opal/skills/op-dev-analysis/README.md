# op-dev-analysis

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`가 ANALYSIS 단계에서 디스패치합니다.

설계 전에 코드·문서 사실을 확인해 PLAN 결정에 필요한 근거를 정리하는 단계입니다.

## 역할

TASK.md의 문제·결과·범위를 다시 도출하지 않고, PLAN을 바꿀 수 있는 질문만 조사합니다. 변경·회귀 경계와 핵심 가정을 확정해 다음 단계가 재조사 없이 쓸 수 있게 만듭니다. TASK와 ANALYSIS 내용이 어긋나면 재도출이 아니라 사실 오류로 보고합니다.

신규(sdlc-v2) 태스크와 legacy 태스크를 다르게 처리합니다. legacy에 이미 ANALYSIS가 있으면 재작성하지 않고 기존 산출물을 그대로 반환합니다.

## 입력

- `task_folder`, `TASK.md`
- PM이 `docs/PROJECT.md` 레지스트리에서 선별해 주입한 프로젝트·기획·설계 문서 (주입되지 않은 문서군은 탐색하지 않음)
- PM이 주입한 실행 capability만 사용

## 출력

- `ANALYSIS.md`
- sdlc-v2 신규 출력은 `Findings / Change boundary / Critical assumptions / Handoff` 네 절만 사용
- 소스코드 원문 복제 없이 `경로:줄번호` 근거만 기록 (`citation-rules.md` 준수)
- 확인하지 못한 실제 연동·권한·데이터 가정은 한계 또는 착수 차단으로 명시

## 호출 시점

`opal-pilot-dev`가 ANALYSIS 단계를 워커에게 디스패치할 때 호출됩니다.

## 관련 문서

- `opal/core/references/harness/citation-rules.md`
- `opal/skills/op-dev-analysis/references/analysis-guide.md` (sdlc-v2)
- `opal/skills/op-dev-analysis/references/analysis-legacy-guide.md` (legacy)

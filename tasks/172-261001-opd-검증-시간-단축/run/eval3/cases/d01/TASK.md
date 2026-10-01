---
template: sdlc-v2
---
# TASK: 워크트리 CLOSE에서 문서·brain·산출물 지식 반영

## Problem

워크트리 태스크는 CLOSE에서 brain 지식을 반영하지 못하고, 반영을 약속한 merge 이후 단계도 절차에 없어서 지식이 누락된다.

- DONE 템플릿은 "워크트리 태스크는 실행 중 brain 파일을 직접 바꾸지 않고, 실제 page 생성·갱신은 merge 후 허브 finalize가 수행한다"고 정한다(`opal/core/references/harness/done-template.md:52`). `brain-tool`의 회고적 학습 쓰기(`add-page`·`update-page`)도 명시 허브 경로만 받고 워크트리 안의 쓰기를 거부한다(`opal/tools/brain-tool/brain_tool.py:304-321`).
- 그래서 CLOSE에서 디스패치한 op-brain-ingest 워커는 아무것도 쓰지 못하고 `skipped`를 반환한다. 태스크 163·164·167 세 건이 모두 그랬다(`tasks/163-*/run/brain-ingest-report.md`, `tasks/164-*/run/brain-ingest-report.md`, 167 `state.json` `close.brain_ingest` 행 메모). 반영할 후보는 워커를 부르기 전에 PM이 DONE.md에 이미 선언했으므로, 워커 호출은 결과에 영향을 주지 못했다. op-brain-ingest 스킬에는 워크트리 분기가 없다(`opal/skills/op-brain-ingest/SKILL.md`).
- opd·opds의 merge 후 안내는 merge, `finalize-attribution`, `status --set done`, `remove` 네 단계뿐이고 brain page를 쓰는 단계가 없다(`opal/skills/opal-pilot-dev/SKILL.md:361-367`). `worktree-tool finalize`는 선언한 후보와 실제 변경을 대조할 뿐이다. 그 결과 태스크 161·162·163·164·167이 선언한 후보 중 허브에 반영된 것은 164의 수동 커밋(`17a94bfd`)뿐이다. 161의 `.opal/brain/pages/entity/test-tool.md`는 2026-09-09 이후 갱신이 없고, 162의 `.opal/brain/pages/flow/test-cycle-early-human-handoff.md`와 167의 `.opal/brain/pages/concept/scenario-economy-advisory-gate.md`는 존재하지 않는다(허브 `main` 2026-10-01 조회).
- 이 제한은 FW의 루트 계약과도 어긋난다. 계약상 작업본(`task_root`)의 쓰기 대상은 브랜치의 `.opal`·`tasks`·소스이고, 허브(`allocator_root`)만 쓰는 대상은 `.opal/MEMORY.json`이다(`opal/core/references/harness/worktree.md:52-53`). 문서 동기화는 이미 워크트리에서 수행되고 있다(162: `docs/PROJECT.md`·`docs/CONVENTIONS.md`, 163: `docs/ARCHITECTURE.md`).

## Proposed outcome

워크트리 태스크의 CLOSE에서 관련 문서·기획서 등 산출물과 brain 지식이 같은 브랜치에 함께 반영된다. 코드와 문서, 지식이 하나의 merge로 허브에 들어가고, merge 후에 지식 반영을 따로 수행하지 않아도 된다. op-brain-ingest 워커는 워크트리에서 실제로 page를 생성하거나 갱신하며, `skipped`로 헛돌지 않는다.

`.opal/MEMORY.json`(채번·작업 이력)은 계속 허브만 소유한다. DONE.md 후보 선언과 finalize의 "선언 밖 brain 변경 차단"도 유지한다. 여러 태스크가 같은 brain 파일을 바꿔도 merge에서 지식이 사라지지 않고, 공유 파일(`index.md`·`log.md`)이 반복 수작업 없이 정합 상태가 된다.

이미 누락된 태스크 161·162·163·167의 선언 후보가 허브 brain에 반영된다.

## Affected users and systems

- 사용자: 워크트리 태스크를 수행하는 캡틴·PM, CLOSE에서 디스패치되는 op-brain-ingest 워커.
- 포함: `brain-tool`의 쓰기 루트 판정과 관련 테스트, `harness/done-template.md`의 회고적 학습 후보 계약, `op-brain-ingest` 스킬, `opal-pilot-dev` CLOSE·merge 후 안내, 같은 전제를 문서화한 다른 워크트리 Pilot·하네스 문서, brain 공유 파일의 merge 설정, install 배포 검증, 누락 후보 반영.
- 제외: `.opal/MEMORY.json`의 허브 단독 소유와 `memory-tool`의 워크트리 쓰기 거부, 허브(비워크트리) 태스크의 brain ingest 동작, brain page 스키마·lint 규칙, 태스크 168(opd2)의 진행 중 산출물.

## Constraints

- C-1: `.opal/MEMORY.json` 쓰기는 계속 허브(`allocator_root`) 명시 인자로만 수행한다. 워크트리에서 MEMORY를 쓰는 경로를 새로 만들지 않는다(`opal/core/references/harness/memory-learning.md` §워크트리에서의 memory 명령 경계).
- C-2: 허브(비워크트리) 태스크의 brain ingest 결과와 `brain-tool` 조회 동작은 바뀌지 않는다.
- C-3: DONE.md `## 회고적 학습 후보` 선언과 `worktree-tool finalize`의 `S ⊆ D` 판정(선언 밖 brain 변경 차단)을 유지한다.
- C-4: 설치본과 상태 편집은 프로젝트 규칙을 따른다(`.opal/AGENT.md` §금지사항). `~/.opal/`은 직접 수정하지 않고, brain·index·log는 `brain-tool`로만 갱신한다.

## Acceptance criteria

- AC-1: 워크트리 태스크 CLOSE에서 op-brain-ingest가 브랜치의 `.opal/brain`에 page를 실제로 생성·갱신한다. 그 변경은 finalize를 거쳐 태스크 브랜치에 커밋되고, merge만으로 허브 brain에 반영된다. merge 후 별도의 page 반영 단계는 요구되지 않는다.
- AC-2: 워크트리 CLOSE 절차가 관련 문서·기획서 등 산출물 갱신과 brain 반영을 같은 브랜치에서 수행하도록 안내한다. DONE 템플릿, op-brain-ingest, opd·opds CLOSE와 merge 후 안내, 그리고 같은 전제를 쓰는 다른 문서에서 "merge 후 허브가 brain page를 반영한다"는 계약이 제거되고 한 가지 절차로 일치한다.
- AC-3: 같은 brain page나 `log.md`를 바꾼 두 태스크 브랜치를 차례로 merge해도 양쪽 지식이 보존되고, `index.md`는 도구로 다시 만들어 전체 page 목록과 일치한다.
- AC-4: 워크트리에서의 `.opal/MEMORY.json` 쓰기는 계속 거부되고, 선언하지 않은 brain 경로를 바꾸면 finalize가 계속 차단한다.
- AC-5: 태스크 161·162·163·167의 DONE.md에 선언된 brain 후보가 허브 brain에 반영되어 있다. 반영하지 않기로 판정한 후보가 있으면 그 사유가 기록된다.

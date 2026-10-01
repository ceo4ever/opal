---
template: sdlc-v2
---
# TASK: opd2 프레임워크 통합 — state-tool 단일 상태와 FW 공통 계약 연결

## Problem

`opal-pilot-dev2`(opd2) 초안은 `main`에 커밋되어 있지만(`e0606fa9`), 단계 상태를 자체 기록(`<task>/.sdlc/events.jsonl`·`.sdlc/state.json`)으로 관리한다(`opal/skills/opal-pilot-dev2/scripts/lifecycle.py:109-160`). 그래서 OPAL FW의 공통 계약과 실행 안전장치에 연결되지 않는다.

- FW 공통 Pilot 계약 테스트에서 opd2 때문에 5건이 실패한다. 원인은 `references/pipeline.json` 없음, `opal-skills-registry.json` 미등재, `state-tool spec-validate` 실패다. 실측 명령은 `~/.opal/.venv/bin/python -m pytest -q opal/tools/state-tool/tests/test_pilot_shared_contract.py`이고, 허브에서 2026-09-30에 실행했다.
- 레지스트리에 없으므로 `//opd2`로 호출할 수 없다(`opal/core/references/opal-skills-registry.json`, `opal/skills/opal-pilot-dev2/SKILL.md:64`).
- 세션 종료를 막는 Stop 판정은 `<task>/state.json`만 읽는다(`opal/tools/ownership-tool/ownership_tool/resolver.py:107-108`). 그래서 opd2 태스크는 agentic 진행 중에도 종료 차단과 재개 안내를 받지 못한다.
- 태스크 lease는 `state-tool`의 첫 상태 전이에서 확보된다(`opal/core/references/harness/worktree.md` §실행 소유권(lease) 계약 §획득). opd2의 상태 도구는 lease를 확보하지 않으므로, 허브 소유 worktree의 체크포인트 커밋이 거부되고(`opal/core/references/harness/guards.md` §커밋 규칙) 다른 세션의 쓰기를 막는 가드도 동작하지 않는다.
- 스킬 문서에는 `pilot.start`·`stage.*`·`worker.dispatch` 이벤트 게이트가 없다(`opal/skills/opal-pilot-dev2/SKILL.md`). 역할 에이전트도 등록된 FW 워커가 아닌 스킬 내부 문서다(`opal/skills/opal-pilot-dev2/agents/`).
- 재개 진입점은 태스크 루트의 `state.json`을 요구하는데 opd2 태스크에는 그 파일이 없어서, 재개가 항상 `resume_state_missing`으로 실패한다(`opal/skills/opal-pilot-dev2/scripts/opd2.py:40-44`).
- `state-tool`은 받아들이는 Pilot 이름과 신규 기본값에 opd2가 없다(`opal/tools/state-tool/state_tool.py:103-110`, `:3344`, `:7664`, `:7725`). 그래서 opd2 태스크를 초기화할 수 없고, 등록하지 않으면 신규 기본값이 semi-agentic·허브가 된다.

## Proposed outcome

사용자가 `//opd2`로 opd2를 호출할 수 있다. 신규 태스크는 agentic·worktree로 시작하고, 재개하면 저장된 mode·workspace를 이어받는다. opd2 태스크의 단계 상태는 다른 Pilot과 마찬가지로 `state-tool`이 태스크 루트 `state.json` 한 곳에서 관리하며, opd2 전용 상태 기록은 더 이상 쓰지 않는다.

opd2 고유의 기계 게이트는 해당 게이트 행을 완료하는 조건으로 그대로 남는다. 대상은 아티팩트 결합 해시, 변경 범위, 실행 증거, 역할 분리, 보호 테스트, 재작업 상한이며, PM이 검사를 건너뛰고 행을 완료할 수 없다. FW 실행 안전장치(lease 확보, Stop 종료 차단·재개 안내, worktree 체크포인트, CLOSE finalize)가 opd2 태스크에도 적용된다. opd2는 단계마다 FW 이벤트 게이트를 거치고, 구현·검증·리뷰를 등록된 FW 워커에게 디스패치한다.

배포 범위는 build로 한정한다. 독립 리뷰를 통과하면 opd와 같은 CLOSE 절차로 마감되고, 배포·관측 경로는 이번에 지원하지 않는다. opd2는 FW 공통 Pilot 계약을 충족하고, 기존 Pilot의 동작은 바뀌지 않는다.

## Affected users and systems

- 사용자: opd2로 개발 태스크를 수행하는 캡틴·PM, 그리고 opd2가 디스패치하는 FW 워커(구현·검증·리뷰).
- 포함: `opal/skills/opal-pilot-dev2/` 전체(SKILL·references·scripts·schemas·templates·tests·agents), `state-tool`의 Pilot 이름 목록·신규 기본값·pipeline 스펙 스키마, `opal-skills-registry.json`, 신규 기본값 원문 문서(`harness/modes.md`·`harness/worktree.md`)와 커맨드 안내(`harness/skill-commands.md`), `docs/PROJECT.md` 컴포넌트 등재, install 배포 검증.
- 제외: RELEASE·OBSERVE(배포·관측) 경로(나중에 일괄 추가 예정), actor 축 지원 Pilot 목록 확장(`harness/actor.md`), 기존 opd·opds 태스크와 pipeline 파일, `state-tool` 단계 이름 목록과 모드 경계 상수.

## Constraints

- C-1: `state-tool` 변경은 opd2 식별자와 신규 기본값 등록으로 한정한다. 단계 이름 목록(`STAGE_ENUM`), 모드 경계(`MODE_BOUNDARY_STAGES`), 사용자 확인 자동 승인 판정, 다른 Pilot의 행 구성·전이 동작은 바꾸지 않는다.
- C-2: 플랫폼 분기는 어댑터 계층에만 둔다(`.opal/AGENT.md` §금지사항 "하드코딩된 플랫폼 분기 추가 금지"). 스킬 소스에 특정 플랫폼 전용 설정 파일을 두지 않는다.
- C-3: 배포 경계와 상태 편집 규칙은 프로젝트 규칙을 따른다(`.opal/AGENT.md` §금지사항). `~/.opal/` 설치본은 직접 수정하지 않고, 파이프라인 행 상태는 `state-tool`로만 바꾼다.
- C-4: 이미 커밋된 opd2 초안(`e0606fa9`)의 산출물 계약(intent·spec·plan의 Markdown+JSON 쌍과 스키마)은 유지한다. 형식을 바꿔야 하면 PLAN에서 결정 사유를 밝힌다.

## Acceptance criteria

- AC-1: `//opd2`와 정식명 `opal-pilot-dev2` 요청이 opd2 스킬로 매칭된다. 무플래그 신규 태스크는 agentic·worktree로 판정되고, 재개는 저장 mode·workspace를 상속하며 다른 workspace 플래그는 거부된다.
- AC-2: opd2 태스크의 단계 상태가 태스크 루트 `state.json`(`state-tool`) 한 곳에만 존재하고, opd2 전용 상태 기록(`.sdlc/` journal·projection)은 생성되지 않는다.
- AC-3: opd2의 기계 게이트(아티팩트 결합 해시 체인, 계획 파일 범위, 실행 증거의 exit·안정성·로그 해시, Builder와 Verifier·Reviewer의 역할 분리, 보호 테스트 불변, 재작업 상한)를 충족하지 않은 상태에서는 해당 게이트 행을 완료할 수 없다. `--force`나 `--auto-pass`로도 우회할 수 없다.
- AC-4: opd2 worktree 태스크에서 첫 상태 전이가 현재 세션의 lease를 확보한다. 진행 중인 태스크는 Stop 판정이 종료를 차단하고 재개 안내를 반환하며, 안정 경계에서 `worktree-tool checkpoint` 커밋이 성공하고, CLOSE에서 `worktree-tool finalize`가 태스크를 인식한다.
- AC-5: opd2는 파일럿 시작과 각 단계 진입에서 FW 이벤트 게이트를 load·verify한다. 구현·검증·리뷰는 등록된 FW 워커에게 `worker.dispatch` 검증을 거쳐 디스패치하며, 같은 워커가 구현과 검증·리뷰를 겸하지 않는다.
- AC-6: build 배포 태스크는 독립 리뷰 통과 뒤 opd와 같은 CLOSE 절차(`close.done_md`부터 `close.final`까지)로 마감되어 `completed_unmerged`가 된다. 배포·관측 요청은 미지원으로 거부되며 배포 완료로 보고되지 않는다.
- AC-7: opd2가 FW 공통 Pilot 계약(레지스트리 등재, pipeline 스펙 검증, 단계 이름 정합, Pilot 간 격리)을 충족하고, 기존 Pilot의 신규 기본값·행 구성·전이 결과가 바뀌지 않는다.
- AC-8: opd2가 FW 문서 체계에 등재된다. 다른 Pilot처럼 스킬 README가 있고, `docs/PROJECT.md` 컴포넌트 표와 신규 기본값·커맨드 안내 문서에서 opd2를 찾을 수 있다.

---
template: sdlc-v2
---
# PLAN: 파일럿 기본 실행 정책과 PM 역할 재정의

> 입력: [TASK.md](TASK.md) (opds — ANALYSIS 없음. PM이 TASK와 프로젝트 문서를 직접 분석)

## Approach

세 축(mode·workspace·actor)의 신규 기본값과 재개 상속을 **하나의 결정론 resolver**로 모은다. 지금은 `state-tool resolve-mode`가 mode만 판정하고, `--wt`·`--pm`·충돌 판정은 Pilot 문서 산문에만 있다(`opal/core/references/harness/modes.md` 라우팅 계약 6은 `mode_flag_conflict`를 약속하지만 이를 집행하는 도구 경로가 없다 — `opal/tools/state-tool/state_tool.py`의 `resolve-mode`는 `--mode` 단일 인자만 받는다).

1. `state-tool resolve-start`를 추가한다. Pilot alias와 사용자가 입력한 원문 플래그를 받아 effective mode·workspace·actor와 `state init` 인자를 반환하고, 충돌은 고유 오류 코드로 거부한다. 기존 `resolve-mode`는 호환용으로 유지하고 신규 기본값 판정만 같은 표를 쓰게 한다.
2. `state init`에 `--workspace worktree|hub`와 새 actor 값을 추가해, resolver가 worktree를 요구한 태스크를 허브 경로로 초기화하는 폴백을 도구가 막는다.
3. `worktree-tool create`에 작업본 안에서 새 작업본을 만드는 중첩을 막는 사전 검사를 추가한다.
4. harness owner 문서(actor·modes·worktree·task-process·guards·서브 하네스·skill-commands)를 새 계약의 SSOT로 고치고, 5개 Pilot 문서와 프로젝트 문서·brain은 SSOT를 참조하도록 맞춘다.
5. 132 전용 이력 테스트가 `actor.md`를 영구 동결하는 문제를 132 귀속 범위로 한정한다.

이 태스크는 착수 시점 설치본의 `--pm` 계약(PM 직접 수행)으로 실행한다(C-8). 따라서 Work items 담당은 `PM`이며, 새 계약은 merge·install 이후 신규 태스크부터 적용된다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| DEC-1. 기본값 표의 SSOT | 신규 태스크 기본값 표는 `harness/modes.md`(mode)·`harness/worktree.md`(workspace)·`harness/actor.md`(actor) 각 절이 소유하고, 기계 사본은 `state_tool.py`의 단일 상수 `NEW_TASK_DEFAULTS`다. 대상: `opd`·`opds`·`oppd`·`oppl`·`oppb` → mode `agentic`, workspace `worktree`. `opd`·`opds`만 actor `coordinator`. 나머지 Pilot은 `semi-agentic`·`hub`·actor 없음. | C-1·C-2. 기본값이 산문 여러 곳에 흩어지면 Pilot마다 다르게 해석된다. 도구 상수 1곳 + 축별 owner 문서 1곳으로 닫는다. |
| DEC-2. resolver 표면 | `state-tool resolve-start <task-path> --skill <alias> [--new-task] [--interactive\|--semi-agentic\|--agentic] [--wt\|--worktree\|--no-wt] [--pm\|--no-pm]`. 응답: `effective_mode`, `mode_source`, `workspace`(`worktree`\|`hub`), `workspace_source`, `actor`(`coordinator`\|`worker`\|`pm`), `actor_source`(`default`\|`explicit`\|`state`\|`legacy_default`), `init_args`(신규만), `warnings`. 신규는 읽기 전용이다. 기존 태스크에 명시 mode 플래그가 있으면 `resolve-mode`와 같은 원자 갱신을 수행한다. | AC-1~AC-4. Pilot이 원문 플래그를 그대로 넘기면 해석이 도구 한 곳에서 일어난다. mode override 영속화는 기존 계약(`modes.md` 라우팅 계약 3)을 재사용한다. |
| DEC-3. 충돌·거부 코드 | 모드 플래그 2개 이상 → `mode_flag_conflict`(기존 코드를 실제로 집행). `--wt`와 `--no-wt` 동시 → `workspace_flag_conflict`. `--pm`과 `--no-pm` 동시 → `actor_flag_conflict`. `--pm`을 opd/opds 밖 alias와 함께 → `actor_unsupported_for_skill`(기존 코드). `oppb`에 `--no-wt` → `workspace_required_for_skill`. 기존 태스크 재개 시 저장값과 다른 workspace·actor 플래그 → `resume_axis_locked`(`axis` 필드 동봉). | AC-4·C-3·C-4. 조용한 무시나 허브 폴백 없이 원인별 코드로 멈춘다. 재개 중 작업본·실행 주체를 바꾸면 이미 만든 산출물과 소유권이 어긋나므로 잠근다. |
| DEC-4. actor 저장값 | 새 PM 조율 actor의 저장값은 `coordinator`다. `--no-pm`으로 해제하면 `worker`를 명시 저장한다. legacy `pm`은 재개 시 "PM 직접 수행"으로만 해석하며, `state init --actor pm`은 `actor_pm_retired`로 거부한다. actor 키 부재는 legacy `worker`다. oppd·oppl·oppb 신규 태스크에는 actor 키를 만들지 않는다. | C-4·AC-2·AC-3. legacy `actor=pm` 태스크(이 태스크 포함)를 새 의미로 재해석하지 않으려면 다른 값을 써야 한다. `coordinator`는 "누가 조율하는가"라는 축 의미를 그대로 드러낸다. |
| DEC-5. 해제 옵션 이름 `--no-pm` | 기본 PM 조율을 해제하는 옵션은 `--no-pm`이다. 결과는 모든 워커 디스패치 단계(ANALYSIS·PLAN·EXECUTE)를 전문 워커가 수행하는 기존 `actor=worker` 의미와 같다. 제안된 `--worker`는 채택하지 않는다. | `--no-pm`은 `--no-wt`와 짝을 이루어 "기본값 해제"임이 이름에 드러난다. 해제 결과가 기존 `actor=worker`와 정확히 같으므로 혼동이 아니라 일치다. `--worker`는 세션 마커 `[WORKER]`, state-tool의 `--as-worker`와 어휘가 겹치고, 특정 워커를 고르는 옵션으로 읽힐 수 있다. |
| DEC-6. PM 조율 계약 (`actor=coordinator`) | PM은 TASK·ANALYSIS(opd)·PLAN·TEST-SCENARIO를 직접 작성하고, Work item 분배·파일 소유권·결과 검토·재작업 지시·마감을 맡는다. EXECUTE 구현·자가 점검·TEST FAIL 수정은 PLAN `담당`의 전문 워커(FE/BE/DB 또는 `opal-task-agent`)가 수행한다. 같은 실행 그룹 병렬은 선행 관계가 없고 변경 파일이 겹치지 않을 때만 허용하고, 그 외에는 순차다. 원문은 `harness/actor.md` 한 곳이다. | AC-5·C-5. 사용자가 원한 역할 분리다. PLAN과 TEST-SCENARIO를 같은 PM이 쓰므로 자기 확인 방지는 독립 evaluator(`op-scenario-gate`)와 `opal-test-agent`가 맡는다는 점을 명시한다. |
| DEC-7. CLOSE 전이 모순 해소 | CLOSE 첫 행은 actor와 무관하게 `harness/modes.md` §CLOSE 전이 계약을 따른다. `actor.md` §독립 검증 경계 표의 "CLOSE 첫 행 `--owner user` 필수" 행은 삭제하고 modes.md 참조로 바꾼다. legacy `actor=pm` 태스크도 같은 판정을 받는다. | AC-5. state-tool은 actor로 CLOSE를 분기하지 않는다(`state_tool.py`에 CLOSE 판정용 actor 참조 없음 — `grep -n 'get("actor")'` 0건). 실제 런타임과 SKILL이 이미 actor 무관 자동 CLOSE이므로, 거짓 문장을 지우는 것이 계약을 약화하는 것이 아니다. merge·push·배포 승인 경계는 그대로다(C-6). |
| DEC-8. worktree 생성 실패 정책 | resolver가 `workspace=worktree`를 반환한 태스크에서 `worktree-tool create`가 `ok:false`면 허브 `tasks/`에 폴더를 만들지 않고 `blocked`로 멈춘다. 보고에는 오류 코드와 두 해결 경로(설정 수정·`worktree-tool init`, 또는 사용자가 `--no-wt`로 다시 시작)를 담는다. 도구 집행: `state init --workspace worktree`는 `--worktree <path>`가 없으면 `worktree_path_required`로 거부하고, `--workspace hub`와 `--skill oppb` 조합은 `workspace_required_for_skill`로 거부한다. `--workspace` 미지정은 기존 동작(호환). | AC-6·C-4. `task-process.md` 스텝 4.5의 `ok:false` 허브 폴백을 제거한다. `--workspace` 미지정 호환은 기존 호출자(다른 Pilot·테스트)를 깨지 않기 위해서다. |
| DEC-9. 작업본 중첩 차단 | `worktree-tool create`는 `--project-root`가 (a) 조상 허브의 `.opal-worktrees/` 아래이거나 (b) Git linked worktree(`git rev-parse --git-dir` ≠ `--git-common-dir`)면 부수 효과 전에 `PROJECT_ROOT_IS_WORKTREE`로 거부한다. | AC-6. 워크트리 세션이 새 태스크를 시작하면 cone 사본의 `.opal/worktree.json`으로 작업본 안에 작업본이 생긴다(`load_config`가 경로의 사본을 그대로 읽음). 허브 경로 추론이 아니라 거부만 하므로 `worktree.md` §cone 확장 계약과 충돌하지 않는다. |
| DEC-10. launcher·lease·재개 점검 결과 | launcher 실패는 비차단을 유지한다. 실패해도 작업본은 이미 있고 허브 세션이 그 작업본을 계속 작업하므로 허브 `tasks/` 코드 수정이 아니다. lease 이관 계약은 바꾸지 않는다. 재개는 `resolve-start`(신규 플래그 없이)가 저장값을 상속한다. | AC-6. 점검 결과 코드 결함이 없어 문서에 사실만 남긴다(불필요한 변경 금지, PRINCIPLES §3). |
| DEC-11. 132 이력 테스트 범위 | `test_pilot_isolation.py`의 `actor.md` 보존 검사는 baseline과 **132가 마지막으로 actor.md를 바꾼 커밋**을 비교한다. HEAD와 비교하지 않는다. | 이 검사의 목적은 "132가 기존 내용을 지우지 않았다"는 귀속이다. HEAD와 비교하면 이후 모든 태스크가 actor.md 계약을 바꿀 수 없다. 커밋 제목에 `oppb`·`(132)`를 쓰지 않아 AttributionTest 오탐을 피한다. |
| DEC-12. 적용 시점 | 새 계약은 이 브랜치의 main merge와 `scripts/install-mac.sh` 재배포 이후 생성되는 신규 태스크부터 적용된다. 이 태스크와 진행 중 태스크는 저장값을 유지한다. DONE.md에 적용 시점을 기록한다. | C-8·C-3. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 세 축 resolver와 init 게이트 | PM | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_start_resolution.py`(신규), `opal/tools/state-tool/tests/test_state_tool_core_cli.py`, `opal/tools/state-tool/tests/test_state_tool_extended_contracts.py`, `opal/tools/state-tool/README.md` | `NEW_TASK_DEFAULTS` 상수, `resolve-start` 서브커맨드(DEC-2·DEC-3), `resolve-mode --skill`(신규 기본값만 표 적용, 미지정은 기존 `semi-agentic`), `init --actor {coordinator,worker}`와 `pm` 거부, `init --workspace {worktree,hub}` 게이트(DEC-8), 신규 오류 코드 6종(`workspace_flag_conflict`·`actor_flag_conflict`·`workspace_required_for_skill`·`resume_axis_locked`·`actor_pm_retired`·`worktree_path_required`) 등재. RED 테스트를 먼저 작성해 실패를 확인한다. 기존 `--actor pm` 테스트와 오류 코드 종수 단언(53→59)을 새 계약으로 갱신한다. `@header` description을 현재 사실로 갱신한다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-6, AC-7, C-1, C-2, C-3, C-4 |
| W-2. 작업본 중첩 차단 | PM | `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`, `opal/tools/worktree-tool/README.md` | `cmd_create` 첫 단계에 `PROJECT_ROOT_IS_WORKTREE` 검사(DEC-9)를 추가한다. 실제 git 저장소로 linked worktree와 `.opal-worktrees/` 하위 경로 두 경우의 거부와 정상 허브 통과를 테스트한다. README 오류 표에 등재한다. | 없음 | P1 | AC-6, AC-7, C-7 |
| W-3. 132 이력 테스트 범위 한정 | PM | `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py` | `test_actor_md_existing_scope_boundary_preserved`의 비교 대상을 HEAD에서 "baseline 이후 132 패턴 커밋 중 actor.md를 바꾼 마지막 커밋"으로 바꾼다(DEC-11). 해당 커밋이 없으면 skip 사유를 명시한다. | 없음 | P1 | AC-7, C-5 |
| W-4. harness owner 계약 | PM | `opal/core/references/harness/actor.md`, `opal/core/references/harness/modes.md`, `opal/core/references/harness/worktree.md`, `opal/core/references/harness/task-process.md`, `opal/core/references/harness/guards.md`, `opal/core/references/opal-harness-agentic.md`, `opal/core/references/opal-harness-semi-agentic.md`, `opal/core/references/harness/skill-commands.md`, `opal/core/references/opal-pm.md`, `opal/core/references/pm/dispatch-process.md` | actor.md: 축 정의를 `coordinator`/`worker`/legacy `pm` 3값으로 재작성, PM 조율 계약(DEC-6), 해제 옵션(DEC-5), 재개 상속·legacy 해석(DEC-4), 독립 검증 표에서 CLOSE 행 제거(DEC-7). modes.md·worktree.md: 신규 기본값 표와 `resolve-start` 라우팅, `--no-wt`, 실패 정책·중첩 차단 참조. task-process.md 스텝 4·4.5·5: resolver 호출, 허브 폴백 제거(DEC-8), `init --workspace` 전달. guards.md §디스패치 의무 원칙: actor별 허용 범위 갱신. 서브 하네스 2종: 기본 모드 설명을 "Pilot별 신규 기본값 표 참조"로 교정. skill-commands.md: 형식·예시에 `--no-wt`·`--no-pm`과 기본값 반영. opal-pm.md §12 진입점 표와 dispatch-process.md preflight 문장: 새 actor 이름으로 교정. | W-1 | P2 | AC-5, AC-6, AC-8, C-3, C-4, C-5, C-6, C-7 |
| W-5. Pilot 문서 | PM | `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/README.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/skills/opal-pilot-project-build/SKILL.md` | opal-pilot-dev: 첫 [MUST]를 `resolve-start`로 교체, actor 분기(STEP 2·3·3.5·4·5 FAIL)를 coordinator/worker/legacy pm 3분기로 정리하되 원문은 actor.md 참조, TEST-SCENARIO 작성자 설명을 actor별로 정리, CLOSE 전이는 modes.md 단일 참조, 명시 모드 표·init 인자 갱신. oppd·oppl: 기본 모드 절과 init 절을 resolver 결과(agentic·worktree, actor 없음)로 갱신. oppb: 기본 모드 절(agentic), P0 worktree 필수와 `--no-wt` 거부, P5 사용자 merge 게이트 유지 명시. | W-4 | P3 | AC-1, AC-2, AC-5, C-1, C-2, C-5, C-6 |
| W-6. 프로젝트 문서와 brain | PM | `README.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/architecture-diagram/opal_framework_architecture.html`, `.opal/brain/pages/concept/actor-axis-orthogonal-to-mode.md`, `.opal/brain/pages/entity/opal-self-pm.md` | 기본 모드·workspace·actor 서술과 `--pm` 의미를 새 계약으로 갱신하고 구형 "PM 직접 구현" 서술을 현행 기본 계약으로 남기지 않는다(AC-8). brain 페이지는 `brain-tool` 규칙에 맞춰 본문을 갱신하고 `brain-tool lint`로 확인한다. | W-5 | P4 | AC-8, C-7 |
| W-7. 설치와 설치본 관측 | PM | 태스크 `run/` 증거(코드 변경 없음, 누락 배포가 확인될 때만 `scripts/install-mac.sh`) | 전체 회귀 후 `scripts/install-mac.sh`로 재배포하고, 설치본 `~/.opal/tools/state-tool/run.sh resolve-start`로 무플래그 신규 opds·oppb·opp 판정과 설치본 문서 문구를 관측해 증거를 남긴다. | W-6 | P5 | AC-7, C-7, C-9 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 호출자가 `init --actor pm`에 의존한다 | 설치본 Pilot 문서·다른 도구·테스트가 `--actor pm`으로 init | merge 전 설치본으로 새 태스크를 만들면 거부된다 | 소스 전체 grep으로 호출자를 찾아 W-1·W-5에서 함께 바꾼다. 설치본은 install 시점에 소스와 함께 교체되므로 문서와 도구가 어긋나는 구간이 없다. S-시나리오로 legacy 재개(`actor=pm` 저장 태스크 advance/mark)가 계속 동작함을 확인한다. |
| H-2. worktree 기본값이 worktree 설정 없는 프로젝트를 막는다 | `.opal/worktree.json`이 없는 실제 프로젝트의 신규 opd/opds/oppd/oppl | 첫 태스크부터 `CONFIG_NOT_FOUND`로 blocked | 차단은 의도된 계약이다(DEC-8). 보고에 `worktree-tool init`과 `--no-wt` 두 경로를 함께 내보내도록 task-process.md에 명시하고, 시나리오로 허브 폴더 미생성을 확인한다. |
| H-3. 132 이력 테스트 변경이 검사 목적을 약화한다 | 132가 actor.md 내용을 지웠는지에 대한 귀속 검사 | 검사가 무력화되면 회귀를 못 잡는다 | 비교 대상 커밋이 실제로 132 패턴 커밋이고 baseline과 다름을 함께 단언한다. SelfCheck 테스트는 그대로 둔다. |

## Release and recovery

- 적용 순서: P1(W-1·W-2·W-3, 파일 비중첩) → P2(W-4) → P3(W-5) → P4(W-6) → 전체 회귀 → P5(W-7 install·설치본 관측). PM 직접 수행이므로 실제 실행은 순차이며, 실행 그룹은 파일 소유권 경계로만 쓴다.
- 검증 범위: 결정론 — state-tool·worktree-tool·oppb-runtime-tool·worktree-launcher 테스트 스위트 전체, `state-tool spec-validate` 전 Pilot, `code-scan validate`, `brain-tool lint`. 실제 연동 — 임시 git 저장소에서 `worktree-tool create` 중첩 거부와 정상 생성, 설치본 `resolve-start` 호출. 사람 전용 검증 없음.
- 실측 경계: 해당 없음(시간·품질 목표 없음).
- 실패 시: install 전이면 worktree 브랜치에서 보정 커밋을 추가한다. install 후 설치본에서 문제가 나면 main의 이전 커밋으로 `scripts/install-mac.sh`를 다시 실행해 복구한다. 이 태스크는 merge·push를 수행하지 않는다(C-6).

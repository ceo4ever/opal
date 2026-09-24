---
module: actor
role: 실행 주체 축과 PM 조율 계약의 단일 SSOT
load: pilot.start
---

<!--
@header {
  "module": "actor-harness",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "모드 축(interactive/semi-agentic/agentic)과 직교하는 실행 주체(actor) 축의 값(coordinator/worker/legacy pm)·신규 기본값·재개 상속·지원 Pilot 범위·PM 조율 계약·독립 검증 경계·GC 호출 지점을 규정하는 단일 SSOT.",
  "exports": ["모드 축과 직교하는 별개 축", "actor 값과 신규 기본값", "지원 Pilot 폐쇄 목록과 미지원 통보", "PM 조율 계약", "legacy pm 재개 계약", "독립 검증 경계와 GC 호출 지점"]
}
-->

# Actor

## 모드 축과 직교하는 별개 축

actor 축은 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**하는 별도의 실행 주체 축이다.

- 모드 축은 "PM이 얼마나 자율적으로 진행하는가"를, actor 축은 "누가 구현을 실제로 수행하는가"를 결정한다.
- 조합 가능: `//opd --interactive`, `//opds --no-pm --semi-agentic --no-wt` 모두 유효하다.
- `mode_flag_conflict` 판정 대상이 **아니다**. 모드 플래그 개수 검사에 `--pm`·`--no-pm`을 세지 않는다. `modes.md`는 대칭 조항(라우팅 계약 10)을 별도로 두되 원문 표현은 그 문서가 소유한다.
- 워크스페이스 축(`--wt`/`--no-wt`, `harness/worktree.md` 소유)과도 직교한다 — mode·actor·workspace 세 축은 서로 독립적으로 조합된다.
- 서브 하네스 로딩 규칙에 영향을 주지 않는다.
- actor 플래그의 해석 owner는 스킬 레지스트리 `triggers`가 아니라 이 문서다. 사용자 대면 커맨드 문법 노출은 `harness/skill-commands.md`가 별도로 소유한다(원문 복제 없음).
- 세 축의 결정론 판정은 `state-tool resolve-start`가 집행한다. Pilot은 사용자가 입력한 원문 플래그를 그대로 넘기고 응답의 `actor`를 사용한다. 인자·오류 코드 구현은 `opal/tools/state-tool/`이 소유한다.

## actor 값과 신규 기본값

| 저장값 | 의미 | 신규 태스크 생성 |
|---|---|---|
| `coordinator` | PM 조율 — 아래 §PM 조율 계약 | opd/opds 기본값. `--pm`으로 명시할 수도 있다 |
| `worker` | 워커 디스패치로 정의된 모든 단계(ANALYSIS·PLAN·EXECUTE)를 전문 워커가 수행 | opd/opds에서 `--no-pm`으로 해제할 때 명시 저장 |
| (키 부재) | legacy `worker`와 같다 | opd/opds 외 Pilot은 키를 만들지 않는다 |
| `pm` | legacy PM 직접 수행 — 아래 §legacy `pm` 재개 계약 | 만들 수 없다(`state-tool init --actor pm`은 `actor_pm_retired`) |

- `--no-pm`은 기본 PM 조율을 해제하는 옵션이며 결과는 기존 `actor=worker`와 같다. 이름은 `--no-wt`와 짝을 이루는 "기본값 해제" 표기다.
- **[MUST] 기존 태스크 재개는 저장 actor를 상속한다.** 신규 기본값으로 바꾸지 않으며, 저장값과 다른 actor 플래그는 `resume_axis_locked`로 거부된다. 키 부재는 `worker`로, `pm`은 legacy 의미로 해석한다.

## 지원 Pilot 폐쇄 목록과 미지원 통보

actor 축을 지원하는 Pilot은 다음 폐쇄 목록 하나뿐이다.

| Pilot | alias |
|---|---|
| `opal-pilot-dev` | `opd`, `opds` |

목록은 이 문서가 소유한다. 지원 범위를 넓히려면 이 표를 갱신하는 별도 태스크가 필요하다(현재 범위 제외: `opwt`·`opsdd`·`oppd`·`oppl` — 제안서·TASK가 확정한 범위 경계 / `oppb` — 고정 Product Flow와 headless worker 구조라 P3 이후 실행이 Supervisor의 `opal-agent` headless attempt 채널이고, 사용자 대면 세션은 OPPB Product Flow와 PM Agent만 소유하므로 actor 축이 성립하지 않는다).

- **[MUST] 목록 밖 Pilot이 `--pm`을 수신하면 조용히 무시하지 않고 미지원임을 1행으로 통보한 뒤 기본 actor(`worker`)로 진행할지 확인한다.** 예: `//opwt --pm ...` 수신 시 "`opwt`는 `--pm`을 지원하지 않습니다. 기본 워커 실행으로 진행할까요?"와 같이 통보하고 답을 받는다.
- 이 게이트는 2중이다.
  - (a) 산문 통보(위 [MUST])는 `pilot.start`에서 이 문서를 로드하는 모든 Pilot이 실행 전 적용한다.
  - (b) 도구가 결정론적으로 거부한다 — `resolve-start --pm`과 `init --actor`가 이 표 밖 Pilot과 함께 오면 `actor_unsupported_for_skill`로 exit 1. 목록 밖 Pilot의 `--no-pm`은 기본값과 같으므로 경고만 남긴다.

## PM 조율 계약

`actor=coordinator`는 선택한 Pilot을 복제하거나 우회하지 않는다. 다음 항목은 actor와 무관하게 그대로 유지된다.

| # | 유지 항목 |
|---|---|
| 1 | 단계 순서와 단계별 skill, task 폴더와 산출물 |
| 2 | `state.json`, event receipt, observability |
| 3 | PLAN·TEST-SCENARIO·RED-first·PM Gate |
| 4 | mode별 사용자 확인과 CLOSE 전이(`harness/modes.md` §CLOSE 전이 계약) |
| 5 | 실제 테스트와 완료 증거 |
| 6 | CLOSE의 brain·memory·개선 루프 |

역할 분담:

| 책임 | `coordinator` | `worker` |
|---|---|---|
| TASK | PM | PM |
| ANALYSIS(opd) | PM이 단계 skill을 직접 Read하고 같은 입력·출력 계약으로 작성 | 전문 워커 |
| PLAN | PM이 직접 작성. Work item `담당`에는 구현할 전문 워커 역할명을 기입 | `opal-plan-agent` |
| TEST-SCENARIO | PM | PM |
| EXECUTE 구현·자가 점검 | PLAN `담당`의 전문 워커(FE/BE/DB 또는 `opal-task-agent`) | 같음 |
| TEST 실행·판정 | `opal-test-agent` | 같음 |
| TEST FAIL 수정 | 해당 Work item을 구현한 전문 워커(fix 모드) | 같음 |
| 분배·파일 소유권·결과 검토·재작업 지시·마감 | PM | PM |

- **[MUST] `coordinator`에서 PM은 구현 코드를 직접 작성하지 않는다.** 구현·자가 점검·FAIL 수정은 전문 워커에게 디스패치하고, 매 디스패치마다 `worker.dispatch`를 load·verify한다.
- **[MUST] 병렬은 같은 실행 그룹 안에서 선행 관계가 없고 변경 파일이 겹치지 않을 때만 허용한다.** 그 외에는 순차로 디스패치한다. 같은 파일은 한 워커가 소유한다(`pm/dispatch-process.md` Step 1).
- PM은 워커 결과를 PM Gate로 검토하고, 부족하면 같은 워커에게 재작업을 지시한다. 재시도 상한은 `harness/guards.md` §자동 루핑 제약을 따른다.
- PLAN과 TEST-SCENARIO를 같은 PM이 쓰므로 자기 확인 방지는 아래 §독립 검증 경계의 evaluator와 테스트 에이전트가 맡는다.
- `worker`는 위 표의 워커 열을 따르며 PLAN 작성자(`opal-plan-agent`)와 TEST-SCENARIO 작성자(PM)가 분리된다.

## legacy `pm` 재개 계약

저장 actor가 `pm`인 기존 태스크는 PM이 해당 단계 skill을 직접 Read하고 같은 입력·출력·검증 계약을 적용해 ANALYSIS·PLAN·EXECUTE를 직접 수행한다. PLAN `Work items`의 `담당`은 `PM`이고, `worker.dispatch`는 아래 독립 검증자를 호출할 때만 load·verify한다. 다른 모든 항목은 위 §PM 조율 계약의 유지 항목과 같다.

legacy `pm` 태스크에서 PM이 구현을 워커에게 넘겨야 하면 사용자에게 알리고 그 시점부터 워커 수행으로 재분류한다. 이미 만든 상태와 산출물은 재사용하되, 이후 `Work items` 담당과 실행 기록은 실제 수행 주체를 사실대로 갱신한다.

## 독립 검증 경계와 GC 호출 지점

어느 actor에서도 PM의 임의 판단에 의한 단계 직접 실행은 금지다(원칙 SSOT는 `harness/guards.md` §디스패치 의무 원칙). 어느 actor에서도 독립 검증 행은 서브에이전트 디스패치를 생략할 수 없다.

다음 행은 서브에이전트 산출 증거 없이 통과 불가하다.

| 행 | 필요 증거 |
|---|---|
| `plan.scenario_gate`(opds)·`test_scenario.scenario_gate`(opd) | `op-scenario-gate` 디스패치 결과 `verdict: pass` |
| `test.run_tests` + `test.pm_gate` | `test-scenario.json` 전 시나리오 PASS + 실제 실행 증거 |

CLOSE 첫 행은 actor와 무관하게 `harness/modes.md` §CLOSE 전이 계약의 effective mode 판정만 따른다. merge·push·배포 승인 경계는 `harness/guards.md` §커밋 규칙이 소유한다.

`worker.dispatch` load·verify는 워커·검증자를 실제로 호출하는 시점마다 새로 발생한다.

### GC 3종 호출 지점

PM이 직접 작업하는 경로(legacy `pm` 태스크와 `opal-self-pm`)는 보안·컨벤션·리포트 검사가 필요할 때 다음 3종을 **같은 입력·결과 계약으로** 직접 호출한다. `coordinator`·`worker` 태스크는 Pilot의 PM Gate 계약이 정한 시점에 같은 3종을 호출한다. 이 문서와 `opal-self-pm/SKILL.md`는 호출 지점·입력 구성 책임만 규정하고, 각 스킬 본체·파라미터·finding 스키마는 변경하지 않는다(호출만).

- `op-gc-security` — 입력: `project_root`·`target_files`·`output_dir`·`timestamp`(선택: `scope`·`element`·`baseline`·`project_documents`). 상세 계약은 `opal/skills/op-gc-security/SKILL.md` §1.
- `op-gc-convention` — 입력·책임은 `opal/skills/op-gc-convention/SKILL.md`가 소유.
- `op-gc-report` — 입력: `project_root`·`output_dir`·`timestamp`·`findings_inputs`·`baseline`. 상세 계약은 `opal/skills/op-gc-report/SKILL.md` §입력과 책임.

파라미터·finding 필드·판정 스키마는 `opal/core/references/harness/gc-finding-schema.md`와 각 스킬 문서가 소유한다. 이 문서는 호출 지점만 규정하고 원문을 복제하지 않는다.

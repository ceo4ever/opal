---
module: actor
role: 실행 주체 축과 PM 직접 수행 계약의 단일 SSOT
load: pilot.start
---

<!--
@header {
  "module": "actor-harness",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "모드 축(interactive/semi-agentic/agentic)과 직교하는 실행 주체(actor) 축 `--pm`의 지원 Pilot 범위·상태 영속화·독립 검증 경계·GC 호출 지점을 규정하는 단일 SSOT.",
  "exports": ["모드 축과 직교하는 별개 축", "--pm 미사용 시 = 현행 동작 100% 유지", "지원 Pilot 폐쇄 목록과 미지원 통보", "--pm 실행 계약", "독립 검증 경계와 GC 호출 지점"]
}
-->

# Actor

## 모드 축과 직교하는 별개 축

`--pm`은 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**하는 별도의 실행 주체(actor) 축이다.

- 모드 축은 "PM이 얼마나 자율적으로 진행하는가"를, actor 축은 "누가 구현을 실제로 수행하는가"를 결정한다.
- 조합 가능: `//opd --pm --interactive`, `//opds --pm --agentic --wt` 모두 유효하다.
- `mode_flag_conflict` 판정 대상이 **아니다**. 모드 플래그 개수 검사에 `--pm`을 세지 않는다. 이 문장은 `harness/modes.md` §라우팅 계약 5(`--wt`)의 `--pm` 버전이며, 이 문서가 자기완결적으로 소유한다. `modes.md`는 대칭 조항(조항 8)을 별도로 두되 원문 표현은 그 문서가 소유한다.
- 워크스페이스 축(`--wt`, `harness/worktree.md` 소유)과도 직교한다 — mode·actor·workspace 세 축은 서로 독립적으로 조합된다.
- 서브 하네스 로딩 규칙에 영향을 주지 않는다.
- `--pm`의 해석 owner는 스킬 레지스트리 `triggers`가 아니라 이 문서다. Pilot alias 다음 토큰으로 `--pm`을 인식하는 규칙 원문은 여기 있으며, 사용자 대면 커맨드 문법 노출은 `harness/skill-commands.md`가 별도로 소유한다(원문 복제 없음).

## `--pm` 미사용 시 = 현행 동작 100% 유지

플래그가 없으면 다음이 전부 현행과 동일하다. 어떤 조건부 분기도 실행되지 않는다.

- `state.json` 스키마: `actor` 키가 **아예 생성되지 않는다**(`state-tool init`에 `--actor`를 전달하지 않는다).
- STATE.md 렌더 결과 · 산출물 경로 · 워커 디스패치 프롬프트(`pm/dispatch-process.md` 절차)는 무변경이다.
- 각 단계(ANALYSIS·PLAN·EXECUTE 등)는 지금처럼 서브에이전트(전문 워커)가 수행하고, PLAN `Work items`의 담당은 전문 워커 역할명 그대로다.
- `worker.dispatch` load·verify는 지금처럼 매 워커 호출 전에 발생한다.

## 지원 Pilot 폐쇄 목록과 미지원 통보

`--pm`을 지원하는 Pilot은 다음 폐쇄 목록 하나뿐이다.

| Pilot | alias |
|---|---|
| `opal-pilot-dev` | `opd`, `opds` |

목록은 이 문서가 소유한다. 지원 범위를 넓히려면 이 표를 갱신하는 별도 태스크가 필요하다(현재 범위 제외: `opwt`·`opsdd`·`oppd`·`oppl` — 제안서·TASK가 확정한 범위 경계 / `oppb` — 고정 Product Flow와 headless worker 구조라 P3 이후 실행이 Supervisor의 `opal-agent` headless attempt 채널이고, 사용자 대면 세션은 OPPB Product Flow와 PM Agent만 소유하므로 actor 축이 성립하지 않는다).

- **[MUST] 목록 밖 Pilot이 `--pm`을 수신하면 조용히 무시하지 않고 미지원임을 1행으로 통보한 뒤 기본 actor(`worker`)로 진행할지 확인한다.** 예: `//opwt --pm ...` 수신 시 "`opwt`는 `--pm`을 지원하지 않습니다. 기본 워커 실행으로 진행할까요?"와 같이 통보하고 답을 받는다.
- 이 게이트는 2중이다.
  - (a) 산문 통보(위 [MUST])는 `pilot.start`에서 이 문서를 로드하는 모든 Pilot이 실행 전 적용한다.
  - (b) state 기록 경로는 `state-tool`이 결정론적으로 거부한다 — `--actor pm`이 이 표 밖 `--skill`과 함께 오면 `actor_unsupported_for_skill`로 exit 1. 인자 정의·에러코드 구현은 `opal/tools/state-tool/`이 소유하며, 이 문서는 그 계약이 존재한다는 사실만 참조하고 스키마를 복제하지 않는다.

## `--pm` 실행 계약

`--pm`은 선택한 Pilot을 복제하거나 우회하지 않는다. 다음 항목은 `--pm` 유무와 무관하게 그대로 유지된다.

| # | 유지 항목 |
|---|---|
| 1 | 단계 순서와 단계별 skill, task 폴더와 산출물 |
| 2 | `state.json`, event receipt, observability |
| 3 | PLAN·TEST-SCENARIO·RED-first·PM Gate |
| 4 | mode별 사용자 확인과 CLOSE 승인 |
| 5 | 실제 테스트와 완료 증거 |
| 6 | CLOSE의 brain·memory·개선 루프 |

달라지는 것은 실행 주체뿐이다.

| 항목 | 기본 Pilot(`actor=worker`) | `--pm` Pilot(`actor=pm`) |
|---|---|---|
| 분석·계획·구현 산출 | 단계별 전문 워커 | PM이 해당 단계 skill을 직접 Read하고 같은 입력·출력·검증 계약을 적용 |
| `worker.dispatch` | 각 워커 호출 전에 필수 | 아래 §독립 검증 경계의 검증 워커를 호출할 때만 load·verify |
| Work item 담당 | 전문 워커 역할명 | `PM` |
| 단계 상태와 Gate | 유지 | 동일하게 유지 |
| 독립 검증 | Pilot 계약에 따름 | 동일하게 유지(§독립 검증 경계) |

### 실행 중 actor 변경 시 재분류

`actor=pm`으로 진행하던 중 PM이 구현을 워커에게 넘겨야 하면, PM은 사용자에게 actor 변경을 알리고 그 시점부터 기본 Pilot 실행(`actor=worker`)으로 재분류한다. 이미 만든 상태와 산출물은 재사용하되, 이후 `Work items` 담당과 실행 기록은 실제 수행 주체를 사실대로 갱신한다. 반대 방향(워커 실행 도중 PM 직접 수행으로 전환)은 사용자가 `--pm`을 새로 명시할 때만 성립하며, 임의 판단으로 전환하지 않는다(§독립 검증 경계 첫 문장).

## 독립 검증 경계와 GC 호출 지점

`actor=pm`은 사용자가 명시한 `--pm`으로만 성립하는 예외이며, 이때 PM이 해당 단계 skill을 직접 읽고 입력·출력·검증 계약을 적용한다. 임의 판단에 의한 직접 실행은 actor 축과 무관하게 여전히 금지다(원칙 SSOT는 `harness/guards.md` §디스패치 의무 원칙). 어느 actor에서도 독립 검증 행은 서브에이전트 디스패치를 생략할 수 없다.

`actor=pm`에서도 다음 3행은 서브에이전트 산출 증거 없이 통과 불가하다.

| 행 | 필요 증거 |
|---|---|
| `plan.scenario_gate` | `op-scenario-gate` 디스패치 결과 `verdict: pass` |
| `test.run_tests` + `test.pm_gate` | `test-scenario.json` 전 시나리오 PASS + 실제 실행 증거 |
| CLOSE 첫 행 | `--auto-pass` 거부, `--owner user` 필수 |

`worker.dispatch` load·verify는 이 독립 검증자를 실제로 호출하는 시점에만 발생한다(위 §`--pm` 실행 계약 표 두 번째 행).

### GC 3종 호출 지점

`actor=pm`(Pilot `--pm`)과 `opal-self-pm` 모두 보안·컨벤션·리포트 검사가 필요할 때 다음 3종을 **같은 입력·결과 계약으로** 직접 호출한다. 이 문서와 `opal-self-pm/SKILL.md`는 호출 지점·입력 구성 책임만 규정하고, 각 스킬 본체·파라미터·finding 스키마는 변경하지 않는다(호출만).

- `op-gc-security` — 입력: `project_root`·`target_files`·`output_dir`·`timestamp`(선택: `scope`·`element`·`baseline`·`project_documents`). 상세 계약은 `opal/skills/op-gc-security/SKILL.md` §1.
- `op-gc-convention` — 입력·책임은 `opal/skills/op-gc-convention/SKILL.md`가 소유.
- `op-gc-report` — 입력: `project_root`·`output_dir`·`timestamp`·`findings_inputs`·`baseline`. 상세 계약은 `opal/skills/op-gc-report/SKILL.md` §입력과 책임.

파라미터·finding 필드·판정 스키마는 `opal/core/references/harness/gc-finding-schema.md`와 각 스킬 문서가 소유한다. 이 문서는 호출 지점만 규정하고 원문을 복제하지 않는다.

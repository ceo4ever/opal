# AGENTIC-LOG — 139 opws 워크스페이스 선언 기반 확장

> 모드: agentic (semi-agentic → agentic 전환, 캡틴 명시 `--agentic`) | actor: pm

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 11회 (Pass: 8 / Fail: 3) |
| 3회 초과 Gate | 0건 |
| 오류 발견 | 6건 (PLAN 표 파손 1 · RED 결함 2 · 계약 미명시 1 · 자체 발견 dry-run 1 · 독립 검증 H-1 미탐 1) |
| 수정 지시 | 4건 (전건 반영) |
| PM 의사결정 | 5건 (`declaration` 필드 분리 · origin 원문 읽기 · 스키마 엄격도 · 좌표 전체 경로화 · `repo`의 org 상대 해석) |
| 개선 사항 | 3건 (README advisory 2 · install 관측 1 — install은 이 태스크 범위 밖 후보) |
| 에스컬레이션 | 0건 |

**가장 값어치 있던 지점**: 독립 검증자가 내 구현과 내 테스트가 함께 놓친 H-1 미탐(subgroup 계층 절단)을 실증했다. 통과 개수(42/42)만 봤다면 그대로 CLOSE로 갔을 결함이다.

## 2026-09-17 14:40 — 진입

- `//opds --pm`으로 시작해 TASK 완료 후 캡틴이 `//opds --pm --agentic`으로 재지시. `resolve-mode --mode agentic` → `persisted: true`, `previous_mode: semi-agentic`.
- actor=pm이므로 단계 스킬을 PM이 직접 Read하고 같은 입력·출력 계약을 적용한다. 독립 검증 행만 서브에이전트를 디스패치한다(`harness/actor.md` §독립 검증 경계).

## GATE — task.user_confirm (자동 승인)

- `advance plan.plan_md` 시점에 도구가 행 2를 자동 승인했다(`auto_approved: [2]`).
- PM 판단 근거: TASK.md가 `verify --clarification-check` 통과(`clarification_check: "pass"`). 필수 5절 충족, C-1~C-7·AC-1~AC-10 고유 ID 보유. 캡틴과의 설계 대화에서 확정된 결정(host 비교 제외·URL 원문 미노출·3진 판정·선언 부재 폴백)이 전부 C/AC로 고정된 것을 직접 확인했다.

## GATE — plan.plan_md

- `verify --plan-contract-check` → pass (W-1~W-7 전건 계약 충족).
- `verify --code-scan-citation-check` → pass (matched_tokens: domain·layer·exports·reason·code-scan).
- 1차 시도는 `plan_contract_unmet`으로 거부됐다. 원인은 W-1 셀의 `str|None` 리터럴 파이프가 표 열을 분할해 실행 그룹·완료 기준 열이 밀린 것. 표기를 바꿔 재검증 통과. **도구가 잡아낸 실제 결함이며 우회하지 않았다.**

## GATE — plan.scenario_gate (진행 중)

- `scenario-coverage-build` → requirements 17 / features 0 / hypotheses 4 / scenarios 13.
- 1차 `scenario-coverage-check` → `coverage_unmet`, missing hypotheses: [H-2].
- 조치: H-2(host 미비교로 인한 동명 레포 오동일 판정)는 수용한 트레이드오프지만 커버가 없으면 근거 없는 수용이 된다. S-14를 추가해 두 호스트가 `match`로 판정되는 사실과 README·스키마 `_help`에 그 동작이 기술되어 있는지를 함께 관찰하도록 고정했다.
- 2차 `scenario-coverage-check` → `all_covered: true` (scenarios 14).
- 판단축은 `opal-evaluator-agent`에 디스패치했다(Producer=PM ≠ Evaluator 분리 유지). 축⑥ 경계·부정에 대해 "반증 표본이 무조건 match 반환 구현을 탈락시키기에 충분한가"를 명시 요청했다.

## 선행 조사 — W-1 착수 기반 (평가자 대기 중 병행)

평가자가 읽는 파일(TASK·PLAN·TEST-SCENARIO)을 건드리지 않는 범위에서 기존 테스트 자산만 실측했다.

- `conftest.py` exports 7종 — `run_git`·`make_bare_remote`·`clone_repo`·`GitFixtureWorkspace`·`git_workspace`·`GitProjectRootFixture`·`project_root_with_workspace`. 로컬 bare remote + 상태별 clone 8종을 subprocess로 구성하며 전역 git config 의존을 `-c user.email/-c user.name` 주입으로 제거해 뒀다.
- `run_sync_cli(workspace_path, *extra_args)`가 CLI subprocess 단일 진입점이다. 주석이 "내부 함수 import 금지 (red-first §4)"를 명시한다 — W-1의 정규화 테스트도 내부 함수를 직접 import하지 않고 CLI 경유로 관찰해야 한다.
- 기존 테스트 17건. W-1~W-5는 이 파일에 추가하며 기존 17건은 S-8 회귀 판정의 기준선이다.
- 임의 remote 형식 주입은 `run_git(["remote","set-url","origin", <형식>], cwd=repo)`로 가능하다 — 네트워크 없이 S-1~S-4·S-14의 URL 변형을 만들 수 있다.
- 신규 서브명령(`init`·`clone`)은 `run_sync_cli`가 `sync`를 하드코딩하고 있어 그대로 못 쓴다. 서브명령을 인자로 받는 러너가 W-2에서 필요하다.

**착수 차단 없음.** 평가자 verdict만 대기 중이다.

## GATE — plan.scenario_gate → PASS

두 증거 모두 확보했다(`harness/scenario-gate.md` tool-gated 요건).

- 결정론: `scenario-coverage-check` → `all_covered: true`
- 판단: `opal-evaluator-agent` iteration 1 → `{goal: 2, adoption: 2, boundary: 2}`, 평균 2.0, `gaps: []`, `verdict: pass`

축⑥ 중점 질의에 대한 평가자 판정: 반증 3쌍이 서로 다른 오구현 계열을 각각 저격한다 — S-1은 "무조건 match"와 org만 비교, S-2는 repo basename만 비교하고 org를 버리는 구현, S-3은 `startswith`·접두 일치 구현. S-1 단독이면 org 무시 구현이, S-1+S-2면 접두 일치 구현이 살아남는데 S-3이 잔여를 닫는다는 분석이다.

### advisory 2건 반영 (verdict pass 이후 PM 판단)

평가자가 감점 없이 남긴 advisory를 그대로 두지 않고 닫았다. 근거는 둘 다 **미정의 구간**이라 구현 단계에서 조용히 갈리기 때문이다.

1. `cmd_clone` 대상 디렉토리 충돌 — PLAN W-5가 "이미 존재하면 거부"를 계약으로 박았는데 확인 시나리오가 없었다. 파괴적 연산의 유일한 방어선이다 → **S-15** 추가.
2. 대소문자 판정 미정의 — `Storelink-IO/Blend` vs `storelink-io/blend`가 TASK·PLAN·시나리오 어디에도 정의되지 않아 구현자 재량으로 갈린다 → PLAN `Decisions and contracts`에 "대소문자는 비교에서 무시" 행을 추가하고 **S-16**으로 고정했다. 판단 근거: GitHub·GitLab이 `org/repo`를 대소문자 구분 없이 같은 레포로 해석하므로, 구분하면 정당한 선언이 `mismatch` 오탐으로 막힌다.
3. 추가로 평가자가 축①에서 지적한 `cmd_clone` 성공 경로 미검증(부정 경로만 있음)도 **S-17**로 닫았다.

**투명성 기재**: S-15~S-17은 평가자 verdict 수신 **이후** 추가되었으므로 평가자가 채점한 산출물에는 포함되지 않았다. 순수 additive이며 평가자 자신의 advisory를 닫는 변경이라 재평가를 요청하지 않았다. 추가 후 `scenario-coverage-check`를 재실행해 `all_covered: true`(scenarios 17)를 재확인했다.

## GATE — plan.pm_gate → PASS

산출물을 형식 확인이 아니라 직접 대조해 검증했다(agentic §4 강화 검토 3·6항).

- Artifact Gate: TASK 5,529 / PLAN 11,425 / TEST-SCENARIO 6,429 / AGENTIC-LOG / gate-history 전건 실재·비어있지 않음.
- 계약 재검사(PLAN 수정 후 재실행): `--plan-contract-check` pass (W-1~W-7), `--code-scan-citation-check` pass.
- 연결 실측: AC 10건·C 7건·H 4건 전건이 TEST-SCENARIO `검증 대상`에 등장한다. 미연결 0.
- 미승인 폴백 없음 — TASK.md 1차 방식(선언 파일 + 6상태 대조 + 승인 후 clone)에서 이탈한 지점이 없다.

## 트랙 강업 판정 (opds → opd) — 유지

`track-escalation.md` 핵심 질문 "현재 단계 이후에 외부 영향이 있는 동작·계약·구조 결정을 새로 해야 하는가?" → **아니오.**

- 외부 영향이 있는 결정 8건이 PLAN `Decisions and contracts`에 전부 확정돼 있다 — 정체성 축, 3진 판정, URL 미노출, 선언 부재 폴백, 6상태, state 불변, init 계약, clone 분리, 대소문자.
- EXECUTE에서 남은 것은 확정된 계약의 구현이며 새 계약 결정이 아니다.
- 따라서 `opds`를 계속한다. 파일 수·변경량은 판정에 쓰지 않았다.

## EXECUTE — RED 디스패치 (진행 중)

- `scenario-init` 17건 등록. `red_required: true`는 S-1~S-7 7건이며 나머지 10건은 구현 후 검증이다.
- RED 작성은 `opal-test-agent` red mode에 디스패치했다. **PM이 직접 쓰면 안 된다** — `red-first.md` §1.5 "구현자와 다른 주체가 공개 인터페이스를 검증하는 실패 테스트를 작성한다". actor=pm에서 PM이 구현자이므로 RED 작성 주체는 반드시 분리된다.
- 디스패치 프롬프트에 3개 [MUST]를 원문 인용으로 주입했다 — 내부 함수 import 금지, mock/patch 금지, 실패 관찰 불가 시 BLOCKED 반환.

### GREEN 착수 전 확정한 세부 (PM 판단 기록)

RED 대기 중 읽기 전용 조회로 두 가지를 확정했다. 둘 다 PLAN 계약을 바꾸지 않고 그 안의 미상세 지점을 좁힌 것이다.

1. **`run.sh` 무변경** — 래퍼가 `exec "$VENV_PYTHON" "$SCRIPT_DIR/git_sync_tool.py" "$@"`로 인자를 그대로 전달한다. 신규 서브명령 `init`·`clone`은 래퍼 수정 없이 동작한다.
2. **선언 파일 조회 위치** — PLAN은 `{프로젝트}/.opal/workspace.json`이라고만 적었는데, 도구가 받는 인자는 프로젝트 루트가 아니라 순회 대상 경로다. 다음으로 좁힌다.
   - `<path>/.git`이 존재(단일 git 루트 분기) → **선언을 조회하지 않는다.** 자식이 없으므로 선언 개념이 성립하지 않고, 현행 동작이 그대로 유지된다.
   - 그 외(컨테이너 분기) → `<path>.parent/.opal/workspace.json`을 조회한다. blend 기준 `workspace/`의 부모인 프로젝트 루트에서 찾는다.
   - 근거: SKILL STEP 1의 기존 3분기가 이미 "`<경로>/workspace` 존재 시 그 경로를 순회, 아니면 단일 루트"로 갈라져 있어 같은 축을 재사용한다. 새 인자(`--project-root`)를 만들면 표면이 늘고 기존 호출 형식이 바뀐다.

## GATE — RED 산출물 검토 → FAIL (재지시)

`opal-test-agent`가 14개 테스트를 추가하고 "14 failed / 기존 17 passed"를 보고했다. **자기보고를 그대로 수용하지 않고 테스트 본문을 직접 읽어 검증했다**(agentic §4-6 산출물 직접 Read 의무).

### 발견 — 결함 RED 5건

S-4(4 파라미터)와 S-5가 구현으로 GREEN이 될 수 없다.

```python
run_git(["remote", "set-url", "origin", origin_url], cwd=fx.repo_behind)   # 도달 불가 URL
...
assert repo.get("status") == "updated"        # ← fetch 성공을 전제
assert repo.get("pulled_commits") == fx.behind_n
```

`updated`·`already-current`는 `git fetch` 성공이 전제다. origin이 `git@github-iskang:...`·`https://github.com/...`을 가리키면 도달 불가라 `failed/fetch-failed`로 떨어진다. 정규화를 구현해도 이 단언은 계속 실패한다. conftest 규율상 네트워크 접근이 금지라 도달 가능하게 만들 수도 없다.

워커 보고의 S-4 서술("가짜 URL이라 fetch 실패 등으로 걸림")이 바로 그 증상인데, 워커는 이를 정상 RED로 보고했다. **RED가 "실패한다"는 사실만으로는 유효하지 않다 — 실패 사유가 구현으로 해소되는 것이어야 한다.**

### 왜 PM이 직접 고치지 않았나

`red-first.md` §1.5 (5): "GREEN과 수정 루프에서는 RED 테스트의 기대 계약을 약화·삭제하지 않는다." 구현자인 PM이 단언을 완화하면 이 조항 위반이고 생성자≠검증자 분리도 깨진다. 작성 주체에게 반환했다.

### 재지시 내용

TEST-SCENARIO S-4·S-5의 기대 결과는 "4형식 모두 match" / "둘 다 match"까지이고 pull 성공을 요구하지 않는다. 테스트가 시나리오를 넘어 과잉 단언한 것이므로 시나리오 계약으로 되돌리는 것은 약화가 아니라 정렬이다. 두 관심사를 분리하도록 지시했다 — (1) 정규화 판정은 도달 불가 URL로도 관찰 가능(선언 대조가 fetch보다 앞), (2) match 이후 정상 경로는 도달 가능한 로컬 bare 경로로만 검증.

S-1~S-3·S-6·S-7은 대조가 fetch보다 앞에서 끝나므로 유효한 RED다. 무수정 지시했다.

## GATE — RED 재작성 1차 검토 → S-4 통과 / S-5 FAIL (PM 지시 오류 정정)

재작성본도 자기보고로 받지 않고 본문을 직접 읽었다.

### S-4 — 통과

`status == "updated"`·`pulled_commits` 단언이 제거되고 `repo` 정규화 키 일치로 대체됐다. 도달성과 무관하게 구현만으로 GREEN이 된다.

```python
assert repo.get("repo") == "storelink-io/blend"
```

### S-5 — FAIL, 그리고 원인은 PM 지시다

재작성본이 정규화에 **로컬 절대경로 → `부모디렉터리명/basename` 환원**을 요구한다.

```python
org_name = behind_path.parent.name          # tmp 디렉터리 이름 (_remotes)
assert repo_with_suffix.get("repo") == f"{org_name}/{behind_path.stem}"
```

**이 요구는 내 재지시가 유도했다.** 직전 반환에서 "match 이후 정상 경로는 도달 가능한 로컬 bare 경로로 검증하라"고 적었고, 워커는 그 지시를 정확히 따랐다. 워커 판단 오류가 아니라 PM 지시 오류다.

왜 받아들이면 안 되는가:

- PLAN `Decisions and contracts`의 정규화 대상은 `git@host:org/repo`·`ssh://`·`https://` 3형식이다. 로컬 파일시스템 경로는 범위 밖이다.
- 임의 경로의 마지막 2세그먼트를 org/repo로 읽으면 `/Users/me/projects/backend`가 `projects/backend`가 된다. 원격 좌표가 아니라 우연히 같은 모양인 문자열이고, 서로 다른 레포가 같은 키로 충돌한다 — **H-1(미탐)을 새로 만드는 설계다.**
- 테스트가 `"host": "local"`, `org`를 tmp 디렉터리명으로 선언한다는 것 자체가 신호다. 실사용자는 그런 선언을 쓰지 않는다.
- 심링크 의존이 불필요한 플랫폼 결합을 만든다.

### 정정한 지시

S-5의 검증 축은 `.git` 접미사 유무이며 도달성이 필요 없다. S-4와 같은 방식(원격 URL 형식 + `repo` 키 일치)으로 되돌리고 pull 단언·심링크를 제거하도록 지시했다.

"match 이후 실제 sync 수행"은 S-8(선언 부재 회귀)과 S-9(`active`·있음 → sync)가 이미 소유하므로 커버리지 공백이 생기지 않는다. S-5가 그 축을 떠안을 이유가 없었다.

**교훈**: 테스트를 도달 가능하게 만들려고 픽스처 구조를 정규화 계약에 끌어들이면, 테스트 편의가 제품 계약을 오염시킨다. 검증 축에 필요 없는 조건은 애초에 요구하지 말았어야 했다.

## 계약 보강 — 정규화 범위 경계 명시 (근본 원인 차단)

S-5 사고의 근본 원인은 워커 판단도 PM 지시도 아니라 **PLAN에 배제가 적혀 있지 않았다**는 점이다. 정규화 대상 3형식은 적었지만 "로컬 경로는 대상이 아니다"를 적지 않아, 도달 가능한 remote가 필요해진 순간 로컬 경로 환원이 자연스러운 선택지로 보였다.

PLAN `Decisions and contracts`에 행을 추가했다.

> 로컬 파일시스템 경로는 정규화 대상이 아니다 — `normalize_repo_coord`는 `git@host:org/repo`·`ssh://`·`https://` 3형식만 환원한다. 절대경로·상대경로·`file://`는 환원하지 않고 None을 반환하며 `compare_repo_coord`가 `unknown`으로 판정해 pull을 보류한다.

이 결정은 C-4(fail-closed)와 결이 같다 — 환원할 수 없으면 같다고 보지 않고 보류한다. `--plan-contract-check` 재통과 확인했다.

**이게 GREEN 구현에도 직접 적용된다**: 픽스처의 로컬 bare 경로를 origin으로 둔 기존 17건 회귀 테스트는 선언 파일이 없으므로 대조 자체가 일어나지 않아 영향받지 않는다(C-1 선언 부재 폴백). 선언이 있는데 origin이 로컬 경로인 조합은 `unknown`으로 보류된다.

---

# 재개 세션 (2026-09-17 15:07~) — RED 증거부터 EXECUTE 완주

이전 세션은 RED 증거 명령을 실행하기 직전에 중단됐다. `RESUME.md`의 순서를 그대로 따랐다.

## RED 증거 확보

```
14 failed, 17 passed  (pytest tests/test_git_sync_tool.py)
```

실패 14건의 사유가 전부 선언 로더·정규화 부재였다 — `repo` 키 없음 / `reason` None / `WORKSPACE_CONFIG_INVALID` 미존재. **도달 불가 URL로 인한 fetch 실패가 단독 사유인 케이스는 0건**이었다(RESUME.md가 무효 판정 기준으로 지정한 조건). 기존 17건은 전부 통과해 회귀 기준선이 유지됐다.

S-1~S-7에 `scenario-red` 기록 후 `scenario-lock` 완료.

## GREEN — W-1~W-7 순차

PLAN의 실행 그룹 P1~P6을 순서대로 수행했다. 같은 파일을 연속 수정하므로 병렬 없음.

| 항목 | 결과 |
|---|---|
| W-1 정규화·3진 대조 | `normalize_repo_coord`(3형식만 환원)·`compare_repo_coord`(match/mismatch/unknown) 신설 |
| W-2 스키마·로더 | `schema/workspace.schema.json` 신설, `load_workspace_config`(부재=None)·`validate_workspace_config` hand-rolled, 오류코드 2종 추가 |
| W-3 `init` | 탐지 기반 초안. `--dry-run`·`--force`, `state` 전건 `active`, 환원 실패는 `unresolved[]`로 분리 |
| W-4 6상태·sync 통합 | 선언 부재 시 기존 분기 그대로(키 집합 동일), 선언 시 `repo`·`declaration` 필드 추가 |
| W-5 `clone` | 인자 리스트 실행, 점유 디렉토리 거부, 응답에 URL 미포함 |
| W-6 SKILL | STEP 1 선언 조회 분기, STEP 2 판정표, STEP 3 ④-2 선언 대조 섹션, STEP 4 조치 5행 + 접속 방식 세션 1회 질의 |
| W-7 README | 서브명령 3종, 선언 대조 절, 3진·6상태표, 오류 코드 8종 |

## 구현 중 확정한 판단 3건

### (1) 판정값을 `reason` 하나에 몰지 않았다

PLAN은 `reason` enum에 4종 추가를 적었지만, `deferred`·있음은 **sync를 수행하면서 동시에 선언 어긋남을 보고**해야 한다. sync가 성공하면 `status=updated`·`reason=null`이 되어 보고가 사라진다.

`repositories[]`에 `declaration` 필드를 따로 두고, pull을 막는 판정(`mismatch`·`unknown`·`undeclared`·`not-cloned`)만 `reason`에도 싣는다. RED가 고정한 `reason == "mismatch"` 계약은 그대로 만족한다.

### (2) origin URL을 `git remote get-url`이 아니라 `git config --get`으로 읽는다

`remote get-url`은 `url.<base>.insteadOf` 재작성을 적용해 로컬 접속 경로를 돌려준다. 그 재작성은 **사용자별 접속 방식이지 레포 정체성이 아니다** — 판정에 새면 같은 레포가 사용자마다 다른 좌표로 읽힌다(C-2 위반). 설정 원문을 읽도록 고정했다.

테스트에서 원격 좌표와 fetch 도달성을 동시에 만족시키는 수단도 이 성질을 그대로 쓴다(`insteadOf`로 로컬 bare 연결, 좌표는 원격 형식 유지).

### (3) 스키마 엄격도를 판정 영향 기준으로 갈랐다

실환경 선언 파일을 확인했더니 `schema_version`이 문자열 `"1.0"`이고 `_help`·`clone_branch` 키를 쓰고 있었다. 초안의 `additionalProperties: false`대로면 **실사용 중인 파일이 전건 거부**된다.

거부 기준을 "판정을 바꾸는 위반"으로 좁혔다.

- 수용: `1`·`"1"`·`"1.0"` 표기 차이, 사람용 필드(`_help`·`note`·`clone_branch`)
- 거부 유지: `state` enum 위반, `dir` basename 위반, `dir`·`repo` 중복, **알려지지 않은 키**(`stat` 같은 오타가 통과하면 `state` 판정이 사라진 줄 모른 채 동작한다)

S-7b(사람 표기 수용)·S-7c(미지 키 거부) 2건을 추가해 경계를 양쪽에서 고정했다.

## 계약 위반 1건 자체 발견·수정

실환경 `init --dry-run`이 `CONFIG_EXISTS`로 거부됐다. **쓰지 않는 경로인데 기존 파일 존재로 막히는 것은 AC-6 위반**이고, 선언이 이미 있을 때 디스크와의 차이를 보려면 열려 있어야 하는 경로다. 존재 검사에서 `--dry-run`을 제외하고 S-11에 (b-2) 케이스를 추가했다.

## 검증 결과

| 축 | 결과 |
|---|---|
| pytest 전건 | **42 passed** (기존 17 + 139 RED 14 + 구현 후 11) |
| `code-scan validate` | OK |
| 실환경 `init --dry-run` | 자식 4건의 SSH 별칭 remote를 전부 환원, 손으로 쓴 선언과 좌표 완전 일치, `unresolved` 0건 |

## 배포 검증 (S-13 / H-4)

install 재실행 후 배포본을 직접 확인했다.

| 확인 | 결과 |
|---|---|
| `schema/workspace.schema.json` 배포 경로 실재 | 존재 — `install_dir`이 `opal/tools/` 전체를 복사한다는 실측이 맞았다 |
| 도구 3파일(구현·README·스키마) 소스 대비 diff | 완전 동일 |
| SKILL.md diff | 변경이력 절만 차이 — install이 배포 시 제거하는 설계다(내용 동일) |
| 배포본 실행 | `run.sh init --dry-run` 성공, 자식 4건 환원, `unresolved` 0건 |

**install 스크립트 관측 2건** (이 태스크 범위 밖, 개선 후보):

- 비대화형 모드가 마지막에 `opal-cli console scan $HOME`으로 홈 디렉토리 전체를 스캔해 **15분 이상** 걸린다. 도구 배포 자체는 수초 만에 끝나는데 배포 검증까지의 대기가 이 스캔에 묶인다.
- 첫 실행을 중단했을 때 이미 복사된 자산과 이후 소스 수정분이 어긋난 상태가 남았다. 재실행으로 해소되지만, 중단 시점에 따라 배포본이 소스보다 과거인 구간이 생긴다.

## ERROR — 독립 검증이 H-1 미탐 실증 (Critical)

TEST 단계 독립 검증 워커(`opal-test-agent`)가 **내 구현과 내 테스트가 둘 다 놓친 미탐**을 실증했다.

- 재현: 선언 `orgA` + `team/repo`, 실제 origin `https://gitlab.com/orgB/team/repo.git`
- 관측: `declaration: "match"` → fetch 도달 가능하게 만들면 `already-current`까지 진행. **서로 다른 조직의 저장소를 조용히 같다고 판정하고 pull 경로에 넣었다.**
- 원인: `_coord_from_path`가 경로의 **마지막 2세그먼트만** 취했다. 3세그먼트 이상(GitLab subgroup·조직 계층)에서 상위 조직이 소실된다.
- 판정: 이것은 PLAN이 막으려던 H-1 그 자체다. H-2(host 미비교)처럼 문서화된 수용 트레이드오프가 아니다.

**내 시나리오 S-1~S-17에 3세그먼트 좌표 케이스가 하나도 없었다.** 반증쌍을 `blend` vs `blend-admin`·`other-org/blend`·`blend2`처럼 전부 2세그먼트로만 구성했고, 계층 축을 아예 생각하지 못했다. 생성자와 평가자를 분리한 것이 실제로 결함을 잡은 사례다.

## FIX — 좌표를 경로 전체로 (선행: 위 ERROR)

| 변경 | 내용 |
|---|---|
| `_coord_from_path` | 마지막 2세그먼트 절단 제거 — host를 뺀 **경로 전체**를 좌표로 쓴다. 자르면 조용한 미탐, 안 자르면 시끄러운 mismatch다 |
| `declared_coord` | `repo`를 **항상 `org` 아래 경로**로 해석하도록 고정. `/` 포함을 "전체 좌표"로 달리 읽던 분기를 제거했다 — 같은 문자열이 위치에 따라 다른 조직을 가리키면 사람이 읽는 의미와 판정이 갈린다 |
| `cmd_init` | 다수 `org`와 다른 조직의 자식을 초안에 끼워넣지 않고 `other_org[]`로 분리 보고. 억지로 넣으면 `org/다른org/repo`로 읽힌다 |
| 테스트 | S-3b(계층 미탐 반증)·S-3c(같은 계층 동치)·S-11b(다른 org 분리) 3건 추가 |
| 문서 | README·스키마 `_help`에 "정체성 키는 host를 뺀 경로 전체", 계층 미절단 근거, `unresolved`/`other_org` 구분 반영 |

## DECISION — `repo`의 `/` 해석을 org 상대로 고정

두 해석이 가능했다. (a) `/`가 있으면 전체 좌표 (b) 항상 `org` 아래 경로.

(b)를 택했다. (a)는 같은 `team/repo` 문자열이 선언 위치에 따라 다른 조직을 가리킬 수 있어 사람이 읽는 의미와 도구 판정이 갈린다. (b)에서 다른 조직을 쓰려고 `repo`에 org를 적으면 좌표가 어긋나 `mismatch`로 **드러난다** — 조용한 오탐이 아니라 시끄러운 거부다. C-4 fail-closed와 결이 같다.

## GATE — TEST (Fail → 수정 → 재검증 대기)

첫 판정은 **Fail**이다. 워커가 Critical 1건을 반환했고 실제 결함이었다. 통과 개수(42/42)만 봤다면 놓쳤을 지점이다. 수정 후 44→47건으로 늘려 재실행했다.

## GATE — TEST (Pass, 2차)

수정본에 대해 같은 독립 검증자가 `status: pass`, blockers 0건을 반환했다. 직접 확인한 근거는 다음과 같다.

| 확인 축 | 결과 |
|---|---|
| 원 미탐 재현 입력 | 실 저장소 종단 재실행 — `mismatch` + `repo: orgB/team/repo` + HEAD 불변 |
| 계층 깊이 불일치(양방향) | 전부 `mismatch`. 올바른 인코딩(`team/blend` 선언 vs `org/team/blend` 실제)은 `match` |
| self-hosted 서브패스 접두 | 접두가 좌표에 포함돼 `mismatch` — 계약 문면대로이며 정당한 거부로 판정 |
| 기존 2세그먼트 선언 | 회귀 없음 |
| `init` → 선언 기록 → `sync` 왕복 | 혼합 org fixture에서 성립. 다른 org 자식은 초안 제외 후 `undeclared`로 정직하게 드러남 |
| C-1 회귀 | 선언 부재 경로 응답 키 집합 동일 |
| pytest | 45 passed |

**advisory 2건은 문서로 반영했다** (기능 변경 없음).

- self-hosted 서브패스(`https://host/gitlab/org/repo`) 사례를 README 환원 예시 표에 추가하고, 그 경우 `org`에 접두를 포함해 적어야 함을 명시했다.
- **한 선언 파일은 `org` 하나만 표현한다**는 구조적 한계를 README 제약 절에 명시했다. `repo`가 항상 `org` 아래 경로이므로 다른 조직의 자식을 같은 파일에서 `active`로 선언할 수 없다. `init`이 `other_org[]`로, `sync`가 `undeclared`로 드러내므로 조용히 깨지지는 않는다. 여러 조직을 아우르는 워크스페이스는 현재 형식의 범위 밖이며, TASK의 어떤 AC도 이를 요구하지 않는다.

## GATE — TEST PM Gate (Pass)

| 기준 | 판정 근거 |
|---|---|
| TASK 요구 100% 충족 | AC-1~AC-10 각각이 실행되는 테스트로 입증. 독립 검증자가 "이름만 그럴듯한 빈 단언 없음"을 별도 확인 |
| 산출물 직접 검증 | 구현·테스트·README·SKILL·스키마를 직접 읽고 enum·필드·오류 코드가 일치함을 대조 |
| 이전 단계 일관성 | PLAN `Decisions and contracts` 대비 변경 2건(좌표 전체 경로화, `repo`의 org 상대 해석)은 PLAN보다 **강화**된 방향이며 C-4 fail-closed와 정합 |
| 미승인 폴백 | 없음. 정규화 범위 3형식 계약 유지 |
| 동작 증거 | pytest 45 passed + 실환경 `init --dry-run` + 배포본 실행 — grep 수준 판정 없음 |

**PLAN과 달라진 2건은 DONE.md에 계약 갱신으로 남긴다** — 문서만 보고 구현을 읽으면 어긋나는 구간이기 때문이다.

## CLOSE (캡틴 승인 후 진입)

| 행 | 처리 |
|---|---|
| DONE.md 생성 | 작성 완료. PLAN 대비 강화된 계약 2건을 본문에 명시 |
| 관련 문서 동기화 | `docs/ARCHITECTURE.md` 3행 갱신(도구·스킬 요약에 선언 대조·`init`/`clone` 반영). `PROJECT.md`·`CONVENTIONS.md`는 사실 변화 없음 |
| brain ingest | `concept/identity-coord-truncation-is-a-miss` 신규. 070 사건 페이지와 상호 연결 |
| 회고/개선 후보 | fw 2건(반증 축 점검항목 · install 홈 스캔 지연), local 1건(brain-tool `add-page` 인자) |
| worktree finalize | N/A — `--wt` 미사용 |
| CLOSE 최종 | `complete` |

**CLOSE 중 도구가 잡은 것 2건** (우회하지 않고 정정했다):

- `close.done_md` 진입이 `worker_duration_undeclared`로 차단됐다. 이전 세션의 PLAN 행이 워커 소요를 기록하지도 미측정을 선언하지도 않은 상태였다. actor=pm 직접 수행이므로 `--worker-duration-unknown`으로 선언해 해소했다.
- `brain-tool add-page`의 위치 인자에 브레인 루트를 넘겨 슬러그가 `brain`인 페이지가 생성됐다. 위치 인자는 페이지 슬러그다. 파일 삭제 후 `index` 재생성으로 정리하고 올바른 슬러그로 재작성했으며, lint의 고립·미연결 경고까지 해소했다.

커밋은 하지 않았다 — `guards.md` §커밋 규칙에 따라 캡틴의 명시 요청을 기다린다.

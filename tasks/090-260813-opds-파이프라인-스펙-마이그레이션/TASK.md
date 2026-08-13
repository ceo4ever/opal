# TASK: 미전환 6 pilot 파이프라인 스펙 마이그레이션 — 10/10 완전 전환

> 작성일: 2026-08-13 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

미전환 6 pilot(opdd·opgc·opwt·oppl·oppd·opsdd) 전부의 파이프라인 행 구성을 `references/pipeline.json`으로 이관하여, **10/10 pilot이 단일 SSOT·단일 파싱 경로**를 쓰도록 만든다. 행 구성은 전후 동등해야 하며(oppl·oppd는 예외 규정 D-7a·D-7b 적용), oppl·oppd의 `init` 하드 실패를 함께 해소한다. deprecated `.md` 파싱 경로는 호출자 0건이 된다.

## 배경

파이프라인 행 정의가 여러 곳에 흩어져 있고, 그중 하나는 이미 실제와 어긋나 있다. 후속 개선(실행 스펙 승격·도구 구동 전환)이 pipeline.json을 전제하는데, 현재는 10 pilot 중 4개만 이를 보유해 개선 혜택이 40%에 머문다.

## 배경 분석 (대화에서 도출)

### (1) pipeline.json 전환이 4/10만 완료됐다

`state-tool init` 호출부 실측 결과다.

| 상태 | pilot | init 인자 |
|------|-------|----------|
| 전환 완료 (4종) | opd · opds · opdw · opp | `--rows-from .../references/pipeline.json` |
| **미전환 (6종)** | opdd · opgc · oppd · oppl · opsdd · opwt | `--rows-from .../SKILL.md` (deprecated) |

- `.md` 파싱 경로는 `build_rows_from_skill_md`이며 deprecation 경고를 유지한 채 여전히 주 경로다 (`opal/tools/state-tool/state_tool.py:768`).
- 미전환 6종에서 SKILL.md의 행 표는 "사람 열람용 미러"가 아니라 **실제로 파싱되는 SSOT**다.

### (2) registry `pipeline` 필드가 실제와 불일치한다

`opal/core/references/opal-skills-registry.json`의 `pipeline` 값과 실제 단계를 1:1 대조했다.

| pilot | registry.pipeline | 실제 | 판정 |
|-------|------------------|------|------|
| opd | TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE | TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE | TEST·CLOSE 누락 |
| opds | TASK → PLAN+TEST-SCENARIO → EXECUTE | TASK → PLAN → EXECUTE → TEST → CLOSE | TEST·CLOSE 누락 |
| opp | TASK → PLAN → EXECUTE | TASK → PLAN → EXECUTE → CLOSE | CLOSE 누락 |
| opdw | TASK → WIREFRAME → EXECUTE | TASK → WIREFRAME → EXECUTE → CLOSE | CLOSE 누락 |
| opgc | SCAN → CHECK → REPORT → **APPLY** → CLOSE | SCAN → CHECK → REPORT → CLOSE | 없는 단계 기재 |
| opsdd | SPEC → VERIFY → PLAN → TASKS → VERIFY → LOOP → DONE | TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE | 전면 상이 |
| oppd | (필드 없음) | PLAN → WBS → EXECUTE | 결측 |
| opdd | TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE | 동일 | 정합 |
| opwt · oppl | 요약 표기 | — | 판정 보류 |

- 확정 드리프트 6건 + 결측 1건이다.

### (3) 최상위 `pm_gate` 배열은 소비처가 없다

- `pm_gate` 문자열은 `state_tool.py`에 3회 등장하나 전부 `--task-step plan.pm_gate` **help 문자열**이다 (`:2376`, `:2391`, `:2419`).
- `validate_pipeline_spec`의 필수 필드는 `spec_version`/`skill`/`meta`/`task_steps` 4종뿐이라 검증 대상도 아니다 (`:890`).
- 전환 완료 4 pilot이 모두 이 배열을 선언하지만 읽는 코드가 0건이다.

### (4) 현재 pipeline.json은 init 1회만 소비된다

- `build_rows_from_pipeline_json`이 `cmd_init`에서만 호출되고, 이후 전 과정은 `state.json`만 참조한다.
- `spec-validate`가 검사하는 항목은 7종이며 `id` 1..N 순차 검사를 포함한다 (`:875-936`).

### (5) SKILL.md 행 표와 pipeline.json은 현재 일치한다

- 전환 완료 4 pilot의 미러 표와 `task_steps`를 프로그램 대조한 결과 4/4 일치했다.
- 즉 이번 마이그레이션의 기준값은 **현행 SKILL.md 행 표**이며, 이관 후에도 동일해야 한다.

## 확정된 설계 방향 (대화에서 합의)

| # | 결정 | 근거 |
|---|------|------|
| D-1 | 이번 태스크 범위는 **행 구성 이관과 registry 정합**까지다. 실행 스펙 필드(`agent`/`model`/`inputs`/`outputs`/`gate`) 추가는 후속 태스크로 분리한다 | 후속 개선이 이 태스크를 기반으로 하므로 기반을 먼저 확정 |
| D-2 | 신규 6 pilot의 pipeline.json에 **최상위 `pm_gate` 배열을 만들지 않는다** | 소비처 0인 죽은 데이터를 증식시키지 않는다 (배경 분석 (3)) |
| D-3 | 기존 4 pilot의 죽은 `pm_gate` 배열은 이번에 **건드리지 않는다** | 후속 태스크에서 `task_steps[].gate`로 인라인 이관하며 함께 제거 |
| D-4 | **행 구성 전후 동등**이 최우선 제약이다. 행 개수·순서·`stage`·`item`이 달라지면 실패로 간주한다 | 마이그레이션은 형식 이관이지 파이프라인 변경이 아니다 |
| D-5 | SKILL.md 행 표는 **삭제하지 않고 미러로 존치**한다 | 표 제거는 후속 태스크(SKILL.md 감량)의 범위 |
| D-6 | ANALYSIS PM Gate 제거 검토는 **이번 범위에서 제외**한다 | 별건이며 opd 단독 사안 |
| D-7 | **제외 pilot 없음.** 대상은 미전환 **6종 전부**(opdd·opgc·opwt·oppl·oppd·opsdd)이며 전환 후 10/10이 된다 | 캡틴 확정(2026-08-13, 최종). 4차 조정에서 opsdd까지 포함 확정 |
| D-7c | **opsdd는 `meta.stages`에 `EXECUTE`를 쓰고 산문의 `EXECUTE-LOOP` 표기는 일절 변경하지 않는다** | 행 표 25행의 stage는 이미 전부 STAGE_ENUM 유효값이며 `EXECUTE`를 쓴다(파서 직접 실행 검증, 미등록 stage 0건). `EXECUTE-LOOP`은 **Phase 이름**이고 `EXECUTE`는 **stage 값**으로 서로 다른 개념이다 — opd(`STEP 3.5 TEST-SCENARIO`)·oppd(`Phase 2: WBS`)도 동일 패턴이다. 개명 시 8개 파일 41곳(`execute-loop-guide.md` **파일명 포함**, brain 페이지 3종, README, ARCHITECTURE, 다이어그램 HTML, `opal-harness-semi-agentic.md:32` 모드 경계 SSOT, `op-sdd-plan/SKILL.md`)이 연쇄 변경되어 문서 개편으로 변질된다 |
| D-7b | **oppd 행 구성은 실사용 선례 8행을 baseline으로 삼고 3개 표준화 판단을 적용해 13행으로 확정**한다 | 선례: `003-oppd-invest-stock/state.json` (2026-06-21, `current_status: done`, 8행 전건 done — 이 구조로 태스크가 실제 완주됨). 표준화 판단 3건은 캡틴 권고안 승인 — ① TASK 2행 추가(다른 9 pilot과 일관) ② Phase별 PM Gate 행 분리(`SKILL.md:117` "PM Gate 단일 mark만 사용" 규정 부합) ③ `--wbs` 플래그 경로의 EXECUTE 행은 런타임 `mark --na` 처리 |
| D-7a | **oppl은 결함 해소를 겸한다.** 현재 `init --rows-from SKILL.md`가 하드 실패하므로 "전후 동등"의 `전`을 파서로 뜰 수 없다. 대신 **SKILL.md 행 표 19행을 baseline으로 직접 대조**한다 | 파서 미검출 원인은 ① 섹션 헤더가 `## STATE.md 초기 생성`(`:121`)이라 헤더 정규식 미매칭, ② 표 헤더가 `\| # \| Stage \| 항목 \|`(`:137`)이라 표 헤더 정규식 미매칭. 행 정규식 자체는 19건 정상 매칭됨(`state_tool.py:816-820` 직접 검증) |
| D-8 | registry `pipeline` 정합화는 **10종 전부**(기존 4 + 신규 6)를 대상으로 한다. oppd의 `domain` 결측도 함께 채운다(`"domain": "dev"`) | 전 pilot이 `meta.stages`를 보유하게 되어 파생 검증이 성립한다. `domain`은 동일 오브젝트·비소비 필드라 함께 처리가 효율적 |
| D-9 | R-2 잔존 검증에서 **`## 변경이력` 섹션 이후 행은 제외**한다 | 과거 이력 개변 금지가 우선 (PLAN decision_required `ac_interpretation`) |
| D-10 | **잔존 검증 범위를 pilot SKILL.md 밖으로 확장**한다. 코어 레퍼런스·하네스·단계 스킬의 구형 지시 4곳을 함께 정정한다 | 목표-커버 게이트 iteration 1 평가자 gap(⑤축 1점). `opal/core/references/tools.md:152`는 **이미 전환된 opp를 `.md` 경로로 호출하라는 실행 예시**라 지금도 틀린 명령이며, 남겨두면 다음 사람이 그대로 복사해 구형 경로를 재도입한다. 도구 자신의 에러 메시지·분기 설명(`state_tool.py`·`state-tool/README.md`)은 **사용 지시가 아니므로 대상이 아니다** |

**oppd 확정 행 구성 (13행)** — D-7b 적용 결과

| id | key | stage | item | 출처 |
|----|-----|-------|------|------|
| 1 | `task.task_md` | TASK | 작업 | 표준화 판단 ① |
| 2 | `task.user_confirm` | TASK | 사용자 확인 | 표준화 판단 ① |
| 3 | `plan.prd_trd` | PLAN | Phase1 PRD/TRD 작성 (opwt) | 선례 행 1 |
| 4 | `plan.spec_validate` | PLAN | Phase1 명세 검증 (op-spec-validator) | 선례 행 2 |
| 5 | `plan.pm_gate` | PLAN | PM Gate | 표준화 판단 ② |
| 6 | `plan.user_confirm` | PLAN | Phase1 사용자 확정 | 선례 행 3 |
| 7 | `wbs.wbs_md` | WBS | Phase2 WBS 작성 | 선례 행 4 (PM 검수를 ②로 분리) |
| 8 | `wbs.pm_gate` | WBS | PM Gate | 표준화 판단 ② |
| 9 | `wbs.user_confirm` | WBS | Phase2 사용자 확정 | 선례 행 5 |
| 10 | `execute.actions` | EXECUTE | Phase3 액션 실행 (동적 추가) | 선례 행 6 |
| 11 | `execute.pm_gate` | EXECUTE | PM Gate | 표준화 판단 ② |
| 12 | `execute.user_confirm` | EXECUTE | 사용자 확인 | 선례 행 7 |
| 13 | `close.done_md` | CLOSE | DONE.md 생성 | 선례 행 8 |

> `meta.stages`: `["TASK","PLAN","WBS","EXECUTE","CLOSE"]`. `WBS`는 STAGE_ENUM에 존재함을 확인했다.
> `--wbs` 플래그 경로에서는 id 10~12가 미완으로 남으며 런타임에서 `mark --na`로 처리한다 (표준화 판단 ③). `conditional` 필드는 넣지 않는다(D-1 — 실행 스펙 필드는 후속 범위).

> **[이월] 후속 태스크로 넘기는 항목**: 실행 스펙 필드 승격(D-1) / 죽은 `pm_gate` 배열 정리(D-3) / SKILL.md 행 표 삭제·감량(D-5) / ANALYSIS PM Gate 제거(D-6). **이번 태스크로 `init` 불가 pilot은 0개가 되고, deprecated `.md` 파싱 경로의 호출자도 0건이 된다.**

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 미전환 **6종 전부**(opdd·opgc·opwt·oppl·oppd·opsdd)의 행 구성을 `references/pipeline.json`으로 이관하고 `state-tool init` 호출을 전환하여, **10/10 pilot**이 단일 파싱 경로를 쓰게 한다. oppl·oppd는 현재 `init` 하드 실패 상태이므로 이 이관이 결함 해소를 겸한다. 함께 registry `pipeline` 필드 10종을 정합화한다 | - | 배경 분석 (1)(2) / 확정 방향 D-7·D-7a·D-7b·D-7c·D-8 |
| 범위 | **포함** — 미전환 6 pilot pipeline.json 신설 / 동 6 pilot SKILL.md init 인자 전환·미러 주석(oppd는 행 표 신설) / registry `pipeline` 10건 정합 + oppd `domain` 보강 / 전후 동등 검증 / oppl·oppd `init` 하드 실패 해소. **제외** — 실행 스펙 필드 추가(D-1) · 죽은 `pm_gate` 정리(D-3) · SKILL.md 행 표 삭제(D-5) · ANALYSIS PM Gate 제거(D-6) · state-tool 소스 변경 · oppl SKILL.md 표 헤더(`Stage`) 개명 · **opsdd 산문 `EXECUTE-LOOP` 표기 개명(D-7c)** | - | 확정 방향 D-1·D-3·D-5·D-6·D-7·D-7c·D-8 |
| 제약 | (a) `state_tool.py` **소스 무변경** — 데이터·문서만 편집한다. (b) 행 구성 전후 동등(D-4). (c) `spec-validate`의 7종 검사를 전부 통과해야 한다. (d) 기존 태스크의 `state.json`은 소급 변경하지 않는다. (e) 배포 경계 — `~/.opal/` 직접 편집 금지, 프로젝트 소스만 수정한다. (f) opsdd 산문의 `EXECUTE-LOOP` 표기 17곳과 `references/execute-loop-guide.md`는 **일절 수정하지 않는다**(D-7c). (g) oppd 행 구성은 D-7b 확정 13행에서 임의 변경 금지 | - | `state_tool.py:875-936` / `docs/CONVENTIONS.md` |
| 완료기준 | (0) **`opal/`·`docs/`·`README.md` 범위에서 deprecated `.md` 파싱 경로를 지시·예시하는 문서 지점 0건**(제외: `opal/tools/state-tool/**`의 에러 메시지·분기 설명, pilot SKILL.md의 `## 변경이력` 이후 행, `.opal/brain/**`). (1) 미전환 6종이 `--rows-from .../references/pipeline.json`을 호출하여 **10/10 pilot 전환**이 완료된다. (2) `state-tool spec-validate` **10건** 전부 `ok:true`·violations 0. (3) 파서 동작 4종(opdd·opgc·opwt·opsdd)은 마이그레이션 전후 `init` 산출 `rows[]`가 **완전 동일**(개수·순서·stage·item)하고, **oppl은 SKILL.md 행 표 19행**과, **oppd는 D-7b 확정 13행**과 `task_steps`가 1:1 완전 일치한다. (4) 전환 대상 6종의 SKILL.md에서 `rows-from.*SKILL.md`가 **`## 변경이력` 섹션 밖 0건**(D-9). (5) registry `pipeline` 필드가 10종 각각의 `meta.stages`와 정합하고 oppd `domain`이 보강된다. (6) opsdd 산문 `EXECUTE-LOOP` 17곳 + `execute-loop-guide.md` 변경 **0건**(D-7c). (7) **oppl·oppd `init`이 각각 exit 0**(rows 19 / rows 13)으로 성공한다. (8) **deprecated `build_rows_from_skill_md` 경로를 지시하는 pilot 0건** | - | 확정 방향 D-4·D-7·D-7a·D-7b·D-7c·D-8·D-9 |

## 요구사항

- [ ] **R-1. 미전환 6 pilot에 `references/pipeline.json` 신설**
  - 무엇을: 현행 SKILL.md 행 표를 `spec_version`/`skill`/`meta`/`task_steps` 구조로 이관
  - 어디에: `opal/skills/{opal-pilot-data-design,opal-pilot-gc,opal-pilot-write-tech,opal-pilot-project-loop,opal-pilot-project-dev,opal-pilot-sdd}/references/pipeline.json`
  - 왜: 이 6종이 deprecated `.md` 파싱 경로에 남아 있음. 4종(opdd·opgc·opwt·opsdd)은 파싱이 정상 동작하고, oppl은 표 19행이 온전하며, oppd는 실사용 선례 8행 기반으로 baseline이 확정됨 (배경 분석 (1) / D-7a·D-7b·D-7c)
  - AC: 6개 파일이 생성된다. opdd 15행 / opgc 7행 / opwt 10행 / oppl 19행 / **opsdd 25행**은 해당 SKILL.md 행 표와 **1:1 완전 일치**하고, **oppd 13행은 TASK.md §확정된 설계 방향 D-7b 표와 `id`·`key`·`stage`·`item` 전부 완전 일치**한다. **opsdd `meta.stages`는 `EXECUTE`를 쓴다(`EXECUTE-LOOP` 금지 — D-7c)**. `key`는 `{stage_slug}.{item_slug}` 패턴을 만족하고 스펙 내 유일하다

- [ ] **R-2. 6 pilot SKILL.md의 `init` 호출 인자 전환**
  - 무엇을: `--rows-from {...}/SKILL.md` → `--rows-from {...}/references/pipeline.json`. 해당 SKILL.md 내 **모든 등장 지점**을 교체한다(opdd 3회·opgc 5회·opwt 6회·oppl 3회·oppd 2회·opsdd 6회 등장, 변경이력 포함 수치)
  - 어디에: 각 pilot SKILL.md의 "STATE.md 초기 생성" `[MUST]` 블록 및 본문 내 동일 지시 전부
  - 왜: 파싱 경로를 pipeline.json 단일화 (교체형 목표)
  - AC: 대상 6종 SKILL.md에서 `rows-from.*SKILL.md` 매칭이 **`## 변경이력` 섹션 밖 0건**(D-9)이고, `--rows-from .../pipeline.json` 매칭이 각 파일에 **1건 이상** 존재한다

- [ ] **R-3. 행 표를 미러로 명시**
  - 무엇을: 6 pilot SKILL.md 행 표 상단에 (oppd는 행 표가 없으므로 D-7b 13행 미러 표를 신설하고 그 위에) "사람 열람용 미러 — SSOT는 `references/pipeline.json`, 편집 금지" 주석 삽입
  - 어디에: 각 pilot SKILL.md의 행 표 직전
  - 왜: 전환 완료 4 pilot과 동일 표기로 통일하고 손편집을 차단 (D-5)
  - AC: 대상 6 pilot 전부 행 표 앞에 동일 취지의 미러 주석이 존재하고, oppd에는 13행 미러 표가 신설된다. **oppl의 표 헤더 `| # | Stage | 항목 |`은 개명하지 않는다**(미러이므로 파서 매칭 불요, 범위 밖)

- [ ] **R-4. registry `pipeline` 필드 정합화 (10종) + oppd `domain` 보강**
  - 무엇을: pipeline.json 보유 10종(opd·opds·opdw·opp·opdd·opgc·opwt·oppl·oppd·opsdd)의 `pipeline` 값을 해당 `meta.stages`에서 파생한 표기로 교체하고, oppd 항목에 `"domain": "dev"`를 추가
  - 어디에: `opal/core/references/opal-skills-registry.json`
  - 왜: 확정 드리프트 6건 + 결측 1건 전부 해소. opsdd 값은 `TASK → SPEC → REVIEW → DESIGN → EXECUTE → VERIFY → CLOSE`로 교체한다(D-7c) (배경 분석 (2) / D-8)
  - AC: **10종 전부** `pipeline` 필드가 존재하고, 각 값을 `" → "`로 분해한 리스트가 해당 pipeline.json `meta.stages`와 **순서·원소 완전 일치**한다. oppd에 `domain`이 존재한다

- [ ] **R-5. 전후 동등 실증 (교체형 목표 검증)**
  - 무엇을: 파서 동작 4종(opdd·opgc·opwt·opsdd)은 마이그레이션 전(`.md` 파싱)과 후(`.json` 파싱)의 `init` 산출 `rows[]`를 대조한다. **oppl**은 `.md` init이 하드 실패하므로 SKILL.md `:137-155` 행 표 19행을 행 정규식(`state_tool.py:816-820`)으로 직접 추출한 것을 baseline으로 대조한다(D-7a). **oppd**는 before가 존재하지 않으므로 D-7b 확정 13행을 baseline으로 대조한다
  - 어디에: 스크래치패드 등 **레포 밖** 경로에서 실행 (레포 파일 생성·수정 0건)
  - 왜: 형식 이관이 파이프라인 변경으로 번지지 않았음을 증명 (D-4)
  - AC: **4 pilot** 전후 `rows[]`가 `row_id`·`stage`·`item` 기준 **완전 동일**하고, oppl은 표 19행 ↔ `task_steps` 19개, oppd는 D-7b 13행 ↔ `task_steps` 13개가 1:1 동일하다. **잔존 검증** — 대상 6종에서 `.md` 파싱 경로 호출 0건(변경이력 제외). **채택 검증** — **10/10 pilot**이 `.json` 경로로 실제 init에 성공한다. 검증 종료 후 임시 산출물이 레포에 0건 잔류한다

- [ ] **R-6. `spec-validate` 전수 통과 (10건)**
  - 무엇을: pipeline.json 보유 10개 파일에 `state-tool spec-validate` 실행
  - 어디에: `opal/skills/{opal-pilot-dev,opal-pilot-dev-short,opal-pilot-dev-wireframe,opal-pilot-project,opal-pilot-data-design,opal-pilot-gc,opal-pilot-write-tech,opal-pilot-project-loop,opal-pilot-project-dev,opal-pilot-sdd}/references/pipeline.json`
  - 왜: 스펙 무결성을 도구로 집행 (제약 (c))
  - AC: 10건 전부 `ok:true`이며 `violations_count: 0`이다

- [ ] **R-7. opsdd `EXECUTE-LOOP` 산문 무변경 보장**
  - 무엇을: opsdd 산문의 `EXECUTE-LOOP` 표기와 관련 가이드 문서가 변경되지 않았음을 확인
  - 어디에: `opal/skills/opal-pilot-sdd/SKILL.md`의 `EXECUTE-LOOP` 17곳, `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`, 그 외 6개 파일(brain 3종·README·ARCHITECTURE·다이어그램 HTML·`opal-harness-semi-agentic.md`·`op-sdd-plan/SKILL.md`)
  - 왜: Phase 이름과 stage 값은 다른 개념이며, 개명 시 8파일 41곳이 연쇄 변경되어 문서 개편으로 변질됨 (D-7c), 제약 (f)
  - AC: `execute-loop-guide.md` 변경 **0건**(파일명 포함). opsdd SKILL.md의 `EXECUTE-LOOP` 등장 횟수가 작업 전후 **17회로 동일**. 위 6개 외부 파일 변경 **0건**

- [ ] **R-8. oppl·oppd `init` 하드 실패 해소 실증**
  - 무엇을: oppl·oppd로 `state-tool init`을 각각 실제 실행하여 성공을 확인
  - 어디에: 스크래치패드 등 레포 밖 경로
  - 왜: 두 pilot 모두 현재 `skill_md_parse_error: header not found`로 태스크 시작 자체가 불가능 (D-7a·D-7b)
  - AC: 전환 전 두 pilot의 `--rows-from .../SKILL.md` 호출이 `skill_md_parse_error`로 실패함을 각각 기록하고, 전환 후 `--rows-from .../pipeline.json` 호출이 **oppl `rows_count: 19` / oppd `rows_count: 13`** 으로 각각 exit 0 · `ok:true` 성공한다

- [ ] **R-9. 레포 전역 구형 지시 4곳 정정**
  - 무엇을: pilot SKILL.md 밖에서 deprecated `.md` 파싱 경로를 지시·예시하는 문서 지점을 `references/pipeline.json` 기준으로 정정
  - 어디에: `opal/core/references/tools.md`(시놉시스 `:84`, 실행 예시 `:152`) · `opal/core/references/harness/task-process.md:49` · `opal/skills/op-task/SKILL.md:223`
  - 왜: `tools.md:152`는 이미 전환된 opp를 `.md`로 호출하라는 **현재도 틀린 예시**이며, 남기면 이번 태스크가 만든 상태가 되돌려진다 (D-10)
  - AC: 위 3개 파일에서 `.md` 파싱을 **지시·예시하는 표현 0건**이고, 각 파일에 변경이력 1행이 추가된다. **제외 대상 확인** — `opal/tools/state-tool/state_tool.py`와 `opal/tools/state-tool/README.md`의 `.md` 언급은 도구 자신의 에러 메시지·분기 설명이므로 **변경 0건**이어야 한다

## 제약 조건

- `opal/tools/state-tool/state_tool.py` **소스 무변경** — 이번 태스크는 데이터·문서만 편집한다
- 행 구성 전후 동등 — 행 개수·순서·`stage`·`item` 변경 금지
- `stage` 값은 `state.schema.json`의 19종 enum 안에 있어야 한다
- `key`는 `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$` 패턴을 만족해야 한다
- `id`는 1..N 순차여야 한다 (`spec-validate` ⑥)
- 기존 태스크 `state.json` 소급 변경 금지
- 배포 경계 — `~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install로 배포

## 기술 스택

- Markdown / JSON (데이터·문서)
- Python 3 (`state-tool` CLI 호출 — 소스는 변경하지 않음)
- Bash (검증 스크립트)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `build_rows_from_pipeline_json`·`validate_pipeline_spec` 계약 |
| D-2 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | `stage` enum 19종·`key` 패턴 |
| D-3 | 설계 | 전환 완료 pipeline.json | `opal/skills/opal-pilot-dev/references/pipeline.json` | 신규 6종의 구조 기준 견본 |
| D-4 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | `pipeline` 필드 정합 대상 |
| D-5 | 설계 | 하네스 State 절 | `opal/core/references/harness/state.md` | state-tool 사용 의무 |
| D-6 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 산출물 근거 기재 포맷 |

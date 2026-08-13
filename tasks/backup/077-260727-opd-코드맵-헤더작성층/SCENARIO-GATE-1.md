# SCENARIO GATE 1 — 목표-커버 루브릭 판단축 채점 (①⑤⑥)

> 실행 일시: 2026-07-28 14:16 KST | phase: `scenario-rubric` | iteration: 1
> 판정 주체: opal-evaluator-agent (verdict-only · mutate 금지)
> scenario_source: `tasks/077-260727-opd-코드맵-헤더작성층/TEST-SCENARIO.md` (S-1~S-25)
> 참조 입력: `TASK.md`(목표·F-1~F-13 AC·확정 방향 12항) / `PLAN.md`(H-1~H-18·Step 상세) / `.scenario-coverage-input.json`(플래그 산정)
> 기준 SSOT: `opal/core/references/harness/scenario-gate.md` §2(6축·판정주체 분리) · §5-1(수렴 임계)
> 판정 범위: **①⑤⑥ 판단축만**. ②③④ 결정론축은 test-tool `scenario-coverage-check` exit 0으로 이미 통과 처리되어 재판정하지 않는다(§2 [MUST] 경계).
> CONTRACT.md: 부재 — `scenario-rubric`은 CONTRACT 루브릭절 병합 대상이 아니므로(별도 트랙) 판정에 영향 없음.

## 1. 판단축별 판정

| 축 | 점수 | 통과선 | 판정 |
|----|------|--------|------|
| ① 목표 달성 | **2** | ≥1 | 통과 |
| ⑤ 채택/잔존 | **1** | ≥1 | 통과(부분) |
| ⑥ 경계/부정 | **2** | ≥1 | 통과 |

**평균 = (2+1+2)/3 = 1.67** (임계 ≥1.5 충족) · **0점 축 없음** → **verdict: pass**

---

### ① 목표 달성 — 2점

**목표 문장**(TASK.md §작업 목표): "`@header` 메타를 소스 인라인 주석과 프로젝트 외부 파일(`.opal/code-map/`) 두 소스에서 동등하게 관리·조회할 수 있게 하고, 비어 있는 헤더 작성층(초안 생성·기록 위치 판정·정합 검증·hook 감시)을 신설한다."

목표는 두 절로 분해된다 — (a) 소스 무수정 자산화·조회 (b) 작성층 4서브명령 + hook 신설. 두 절 모두 **운영 계층(L3)에서 직접 검증**된다.

| 근거 | 인용 |
|------|------|
| 목표 전용 시나리오 존재 (070 결함의 직접 대응) | S-24 §대상: "**태스크 목표 자체** — 소스 파일을 수정하지 않고 기존 코드 전량을 code-scan 조회 자산으로 만든다", 계층 L3 |
| (a) "소스 0수정" 우회 불가 검증 | S-24 기대결과②: "픽스처 **소스 파일 0개 수정**(`git status` 기준 소스 diff 0)" — 산문 선언이 아니라 VCS 상태로 집행 |
| (a) "조회 가능" 검증 | S-24 기대결과③: "4-pass 후 `scan`/`domain`/`layer` 결과에 readonly 스코프 파일이 **전부 등장**" — 인라인 0건인 파일이 조회에 잡히는지를 직접 확인 |
| (b) 작성층 완주 검증 | S-24 기대결과①: "discover→scaffold→(description 채움)→target→validate **4-pass 완주**" + ④ "`validate` exit 0"(= `uncovered` 0 = 커버리지 완성) |
| (b) hook 감시 절 검증 | S-25(is_goal_scenario) — 실 세션 `Write`/`Edit`에서 matcher 발동 관측, 미발동 시 폴백 판정까지 사전 정의 |
| 자기적용(dogfooding) 병행 | S-24 기대결과⑤: 자체 저장소 4항목 로그 증명 + ⑥ 신규 테스트 파일 8종이 `@header` 보유하고 `scan`에 잡힘 |
| 3 지원조건 중 범위 내 2종 커버 | readonly → S-24/S-12, 공유 레포(스코프 한정) → S-19/S-16. "레거시 대량(파일럿)"은 확정 방향 12에서 후속 태스크로 명시 제외 — 범위 정합 |

**관찰(감점 사유 아님)**: 확정 방향 11("4서브명령은 인라인에도 적용")의 인라인 트랙은 L3 4-pass가 아니라 L2(S-12 `inline` reason, S-13 합산 커버리지, S-14 draft 해소)에서만 커버된다. 목표 문장의 무게 중심이 code-map 절에 있어 ① 판정에는 영향을 주지 않는다.

---

### ⑤ 채택/잔존 — 1점

**교체형 목표 존재 여부: 존재한다**(자체 판단). 이 태스크는 순수 신규 기능이 아니라 아래 4종의 기존 상태 교체를 포함한다.

| # | 교체 대상 | 구형 상태 | 잔존0 검증 | 신형 채택 검증 |
|---|----------|----------|-----------|--------------|
| 1 | `header-rules.md` §8 작성 규칙 | "별도 도구 없음" | **있음** — S-21 기대②: "`header-rules.md`에서 '별도 도구 없음' grep **0건**" | **있음** — S-21 기대③: 4단 판정·3단 시점·권한 경계 3표 존재 |
| 2 | code-scan 도구 래퍼 규약 | `tool-scan usage code-scan` = `help_exec_failed`(exit 127) | 해당 상태 자체가 소멸 | **있음** — S-22 기대②: "`ok: true` + 신규 서브명령 포함(**현재는 `help_exec_failed`**)" — before/after 명시 |
| 3 | `extractHeader` 단일 해석 → `resolveHeader` 2소스 | 인라인만 해석 | S-7: legacy 골든 바이트 동일 + `_source` 키 0건 | **있음** — S-5(`_source` 5종), S-8(readonly 파일 단일 조회가 0건 아님 = PM Gate 8번 경로 채택) |
| 4 | brain `sync-header` 단방향 계약 | 소스 역기록 금지 문언 | **있음** — S-21 기대④: "단방향 계약 문언 **diff 0**"(보존형 잔존 검증) | S-21 기대④: 2소스 의미 1문장 추가 |

교체 4종 모두 최소 한 방향이 검증되고, #1·#2·#4는 양방향이 검증된다 → **0점 아님**.

**2점에 이르지 못한 이유 — 미검증 교체 효과 3건**:

1. **저장소 자체 스캔 범위 교체가 시나리오에 없다.** PLAN.md:297이 "`.opal/code-scan.json` 신설은 이 저장소의 brain `sync-header`·`missing` 결과를 **즉시 바꾼다**(전체 순회 → 3스코프 한정) — 의도된 개선이며 **dogfooding 로그로 증명한다**"고 스스로 선언했으나, S-24 기대결과⑤의 dogfooding 4항목은 (8커맨드 골든 회귀 / `discover --dry-run` / `validate --changed` / `tool-scan usage`)뿐이고 이 교체 효과 항목이 없다. PLAN이 증명 방법으로 지목한 자리가 비어 있다.
2. **`missing` 커맨드의 채택 효과가 미검증.** 태스크 배경(TASK.md:29)이 문제로 지목한 대상은 "`code-scan missing`은 나열만 하고 채우는 수단을 제공하지 않는다"인데, code-map 자산화 후 그 파일들이 `missing`에서 빠지는지를 확인하는 시나리오가 없다. S-24 ④ `validate` exit 0이 `uncovered` 0으로 등가 보증을 하지만, 그것은 신설 도구의 자기 보고이며 사용자가 관측하는 기존 커맨드의 변화가 아니다. (구조 확인: 8커맨드 전량이 `scanAll:318`을 경유하므로 커맨드별 미채택 위험 자체는 낮다 — `cmdMissing:578`, PLAN Step은 `:324` 1줄 교체. 따라서 코드 경로 리스크가 아니라 **채택 관측 누락**으로만 감점했다.)
3. **`pm-review-gate.md` 신규 절차 채택이 검사 항목으로 특정되지 않았다.** 해당 문서는 S-21 대상 7문서에 포함되지만 기대결과 ①~⑤ 중 pm-review-gate 고유 검사가 없어 "변경이력 행 추가"(①)로만 덮인다. `:52-56` PM Gate 8번이 매니페스트 유래 헤더도 인정하도록 바뀌었는지가 문서 차원에서 검증되지 않는다.

---

### ⑥ 경계/부정 — 2점

프롬프트가 지목한 6개 경계 범주가 모두 시나리오로 도출되어 있다. 25 시나리오 중 14건이 경계·부정 경로다.

| 경계 범주 | 시나리오 | 인용 |
|----------|---------|------|
| 스키마 위반 | S-4 | "`unsupported_version`·`invalid_index` + exit 1" — 스키마 오류 exit 1 / 위반 exit 2 계약 분리까지 확인 |
| 충돌 거부 | S-11 | "`mirror_collision` exit 1로 거부되고 **어떤 매니페스트도 쓰이지 않음**(부분 쓰기 없음)" |
| 멱등 가드 거부 | S-9 | "index 존재 시 `index_exists` exit 1" + `--dry-run` 파일 미생성 |
| 잘못된 설정값 | S-17 | "`bogus`=`auto` 폴백 + stderr 경고 + **stdout JSON 무오염**" — 채널 분리까지 규정 |
| 깨진 입력 | S-18 | 이벤트 JSON 5종 중 "깨진 JSON"·"`file_path` 부재" → "stdout **0바이트**, 전 케이스 **exit 0**(fail-safe)" |
| 권한 침범 | S-15 | `dir` 조작·`files` 키 가감·`layer` 기재 → "각 전용 detail로 거부 + exit 2" + ⑤ "침범 기재된 `layer`가 `scan` 결과를 바꾸지 않음" |
| 실행 환경 부재 | S-22 | "`OPAL_NODE_BIN=/nonexistent run.sh --help` → `node_missing` JSON + exit 1" |
| 정책 차단·해소 경로 | S-13 / S-14 | 5종 위반 + exit 0/1/2 계약 / "scaffold 직후 exit 2(`draft` N건) → 채움 후 exit 0" |
| 계약된 한계 고정 | S-3 | 주석 내 존재를 "**통과**(계약된 한계 — 문법 파서 미도입)"로 명시 고정 |
| 경계값·미해당 | S-1 / S-12 | "스코프 외는 `null`" / "code-map 부재 트리는 항상 `inline`" |
| 오염 부정 | S-19 / S-23 | `fixtures/` 0건 · 저장소 파일 0건 / 무시 예외와 무시 유지 동시 확인 |

**관찰(감점 사유 아님)**: `index.json`의 스키마 위반은 S-4로 커버되나, **패키지 매니페스트 파일 자체가 파싱 불가한 JSON**일 때 8커맨드가 fail-safe하게 동작하는지는 시나리오에 없다. hook에는 동일 범주(깨진 JSON)를 S-18로 명시 커버한 반면 조회 경로에는 대응이 없다. 다음 회차에 넣으면 좋으나 ⑥의 존재·범위 임계에는 미달하지 않는다.

---

## 2. 결과 계약

```json
{
  "scores": { "goal": 2, "adoption": 1, "boundary": 2 },
  "average": 1.67,
  "gaps": [
    "⑤ 채택/잔존: S-24 기대결과⑤ dogfooding 항목에 '저장소 자체 .opal/code-scan.json 신설 전후로 missing·brain sync-header 대상 집합이 전체 순회에서 3스코프 한정으로 좁혀졌음을 로그로 대조' 항목을 추가하라. PLAN.md:297이 이 교체 효과의 증명 방법으로 dogfooding 로그를 지목했으나 현재 4항목(골든 회귀/dry-run/--changed/tool-scan usage)에 해당 항목이 없다.",
    "⑤ 채택/잔존: code-map 자산화 후 기존 missing 커맨드의 결과 축소를 검증하는 기대결과를 추가하라. S-24에 '4-pass 이전 missing --json에 나열되던 readonly 스코프 파일이 4-pass 이후 missing 결과에서 0건이 된다'는 전후 대조를 넣을 것. 현재는 validate exit 0(신설 도구의 자기 보고)만 있어, 태스크 배경(TASK.md:29 'missing은 나열만 하고 채우는 수단이 없다')이 해소됐음을 기존 커맨드 관측으로 확인하지 못한다.",
    "⑤ 채택/잔존: S-21 기대결과에 pm-review-gate.md 고유 검사 항목을 추가하라. 현재 7문서 목록에는 포함되나 기대결과 ①~⑤에 해당 문서 검사가 없어 '변경이력 행 추가'로만 덮인다. pm-review-gate.md:52-56 PM Gate 8번 절차가 매니페스트 유래 헤더(_source: file|package|rule|domain)도 검증 통과로 인정하도록 갱신됐는지를 grep 가능한 문언 검사로 특정할 것."
  ],
  "verdict": "pass"
}
```

## 3. 종합 판정

**verdict: pass** — `scenario-gate.md` §5-1 수렴 조건(판단축 각 ≥1점, 0점 축 없음, 평균 ≥1.5)을 충족한다(평균 1.67).

070 결함 유형(목표 검증 시나리오 자체의 부재)은 재발하지 않았다 — S-24가 태스크 목표를 명시 대상으로 삼아 L3에서 `git status` diff 0 + 조회 결과 등장 + `validate` exit 0으로 집행하며, S-25가 hook 감시 절을 실 세션에서 관측한다.

`gaps[]` 3건은 모두 ⑤ 채택/잔존축의 **관측 누락**이며 게이트 차단 사유가 아니다(해당 축 1점 = 통과선 충족). 다만 3건 모두 기존 시나리오(S-24, S-21)에 기대결과 행을 추가하는 수준의 저비용 보강이므로, 반영은 PM(오케스트레이터)의 판단에 맡긴다 — 본 에이전트는 판정만 반환하며 산출물을 수정하지 않았다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-28 | iteration 1 판단축(①⑤⑥) 채점 — goal 2 / adoption 1 / boundary 2, 평균 1.67, verdict pass + gaps 3건 |

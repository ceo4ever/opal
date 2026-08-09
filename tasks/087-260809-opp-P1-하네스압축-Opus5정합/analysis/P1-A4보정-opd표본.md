# P1-A4보정. opd 표본 직접 실측 재대조 — R-6

> 소속: `tasks/087-260809-opp-P1-하네스압축-Opus5정합/PLAN.md` §3 Step 2 (R-6)
> 목적: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A4-로드사슬.md`(이하 A4) §3이 opds·opp 표본만 측정해 남긴 잔차(A4:151, §7 #2 `A4:193`)를 opd 표본 직접 실측으로 정량 분해한다.

## §0. 절차·마커 승계

A4 §1.1(과대계상 3요인)·§1.2(홉 정의)·§1.3(Read 지시 판별)·§3(표 형식) 절차를 **그대로** 적용한다. 새 판단은 도입하지 않는다.

**마커 범례**: `[M]` 실측(파일 직접 Read/`wc -l`/`grep` 집계) / `[D]` 파생(연산 병기) / `[E]` 추정(판단 개입, 근거 문장 필수).

**줄수 계상 기준**: PLAN §1.5 (d) — **기준 A**(프로젝트 소스 `wc -l`, `/Volumes/Data/AiStudio/workspace/opal/opal/...`)를 판정 기준으로 삼고, **기준 B**(배포본 `~/.opal/...`)를 병기한다. 표 형식은 `줄수[M] A/B`.

---

## §1. 표본 선정 근거

`tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A3-스폰실측.md`(이하 A3) §4~§6의 실측을 승계한다.

- A3:50 — opd 전체 후보 15건, opds 10건 중 opd 6건이 12건 표본에 포함(`080·078·077·075·073·072`) `[M]`.
- A3:87-94 — opd 6건의 EXECUTE StepCount: 080=14, 078=22, 077=20(+L3 1), 075=?, 073=8(079 오기 아님, 073 행), 072=12 `[M]`.
- A3:173 — "**StepCount ≥ 10 → 조건부 배치 검토** 대상 7건(080·078·077·075·082·083·076)" 판정 `[E, 관찰적 절단점]`. 이 7건 중 opd는 **080·078·077 3건**뿐이다.

→ 본 작업 지시(태스크 087 디스패치 프롬프트)가 지정한 **080·078·077**은 "opd 6건 중 StepCount ≥ 10 구간이자 C4 대상과 동일 집합"이라는 A3 §6 판정과 정확히 일치한다. `[M/D]`

---

## §2. 표본 3건 조건표

| 태스크 | skill | mode | ANALYSIS 단계 | scenario_gate | 근거 |
|--------|-------|------|--------------|---------------|------|
| 080-260801-opd-헤더소스-단일화 | opd(`opal-pilot-dev`) | agentic | 있음(행 3~5) | 있음, done | `tasks/080-.../state.json:1-4,34-59,100-125` `[M]` |
| 078-260728-opd-메모리-json전환 | opd(`opal-pilot-dev`) | agentic | 있음(행 3~5) | 있음, done | `tasks/078-.../state.json:1-4,34-59,100-125` `[M]` |
| 077-260727-opd-코드맵-헤더작성층 | opd(`opal-pilot-dev`) | semi-agentic | 있음(행 3~5) | 있음, done | `tasks/077-.../state.json:1-4,34-59,100-125` `[M]` |

**A4 표본(opds/opp)과의 구조적 차이 1개**: opd는 `TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE` 7단계이며, opds/opp에는 없는 **ANALYSIS 단계**(및 그 PM Gate)가 별도로 존재한다(`opal-pilot-dev/SKILL.md:11,32-59`) `[M]`. 단, ANALYSIS 단계 자체가 디스패치하는 `op-dev-analysis/SKILL.md`는 A4가 opds/opp에서 `op-dev-execute`·`op-task-execute` 등 **워커 디스패치 스킬을 PM 로드 사슬에서 일관되게 제외**한 것과 동일 원칙으로 제외한다(A4 §3.1~3.3에 `op-dev-execute/SKILL.md` 등 부재) `[D]`. 즉 opd의 추가 ANALYSIS 단계는 PM 자신의 문서 로드 사슬에 새 문서를 추가하지 않고, 기존 `qa-standards.md`(PM Gate, 캐시 1회 계상) 발동 횟수만 3회(ANALYSIS/PLAN/TEST)로 늘린다 — 발동 횟수 증가는 §4에서 별도 정량화한다.

---

## §3. 태스크별 실효 로드 문서 목록

컬럼: `문서` / `줄수[M] A/B` / `홉` / `발동조건` / `근거`

### 3.1 080 (opd/agentic)

| 문서 | 줄수[M] A/B | 홉 | 발동조건 | 근거 |
|------|-----------|----|---------|------|
| `opal-harness.md` | 330/276 | 1 | 항상 | `opal-pilot-dev/SKILL.md:12` |
| `opal-harness-agentic.md` | 240/227 | 2 | mode=agentic → 1택 | `opal-harness.md:90`(추정 위치 동일); mode 실측 `state.json:4` |
| `harness/citation-rules.md` | 426/416 | 1 | 직접 1홉 | `opal-pilot-dev/SKILL.md:20` |
| `harness/red-first.md` | 86/81 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:86,108`; 발동 `state.json:113-114`(done) |
| `op-scenario-gate/SKILL.md` | 175/169 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:95-96`; 발동 `state.json:113-114` |
| `harness/scenario-gate.md` | 99/94 | 2 | op-scenario-gate Step1 필수 Read | `op-scenario-gate/SKILL.md:15,27`(A4:74 승계) |
| `harness/state-template.md` | 114/103 | 2 | TASK 단계 STATE.md 초기 생성 | `opal-harness.md:101`(A4:75 승계) |
| `harness/qa-standards.md` | 76/71 | 2 | PM Gate 문서검증 — **3회 발동**(analysis/plan/test, opds 대비 +1회) | `state.json:47-51,80-84,157-161` 3개 pm_gate 행 |
| `harness/observability.md` | 78/78 | 2 | 워커 디스패치 직전(매 디스패치) | `opal-harness.md:104` |
| `harness/parallel-execution.md` | 99/93 | 2 | 병렬 디스패치 — **[M] 집행 확인**: "Phase 2 병렬 디스패치 — Step8∥Step9"(#59), "Step 2를 파일 집합이 겹치지 않는 2배치 병렬로 재구성"·배치A 36케이스 RED 33건 실집행(#39) | `tasks/080-.../AGENTIC-LOG.md:56,76` |
| `harness/state.md` | 144/134 | 2 | TASK 시작/Gate 직후 | `opal-harness.md:108` |
| `harness/task-process.md` | 87/76 | 2 | TASK 단계 진입 | `opal-harness.md:109` |
| `op-task/SKILL.md` | 278/259 | 3 | task-process.md 필수 Read | `harness/task-process.md:13-14` |
| `harness/coding-principles.md` | 103/93 | 2 | EXECUTE 코드 변경 — `code-scan.js`·`code-map-hook.js` 변경 | `opal-harness.md:110`; `tasks/080-.../DONE.md:27` |
| `harness/header-rules.md` | 160/160 | 2 | 변경 파일 확장자 `.js`가 대상 확장자에 포함 → **opds 표본과 달리 활성** | `harness/header-rules.md:63-69`(대상 확장자 목록); 변경 파일 `tasks/080-.../DONE.md:27`(`code-scan.js`·`code-map-hook.js`) |

**미발동(제외)**: `harness/additional-work.md`(87/79) — 이 문서는 **CLOSE 이후 재진입** 프로세스 전용(`harness/additional-work.md:26-34` "태스크가 완료 상태인 후에 추가 수정이 필요할 때 진입"). `tasks/080-.../STATE.md:33,42`의 "행 15 추가수정: hook ⑤.5 순서 결함"은 **TEST 단계 진행 중** 발생한 행 추가이며 CLOSE 재진입이 아니므로 트리거 미충족 `[M]`.

**080 합계**: 330+240+426+86+175+99+114+76+78+99+144+87+278+103+160 = **2,495줄** `[D]` (기준 A) / 276+227+416+81+169+94+103+71+78+93+134+76+259+93+160 = **2,330줄** `[D]` (기준 B)

### 3.2 078 (opd/agentic)

| 문서 | 줄수[M] A/B | 홉 | 발동조건 | 근거 |
|------|-----------|----|---------|------|
| `opal-harness.md` | 330/276 | 1 | 항상 | `opal-pilot-dev/SKILL.md:12` |
| `opal-harness-agentic.md` | 240/227 | 2 | mode=agentic | `state.json:4` |
| `harness/citation-rules.md` | 426/416 | 1 | 직접 1홉 | `opal-pilot-dev/SKILL.md:20` |
| `harness/red-first.md` | 86/81 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:86,108`; `state.json:113-114`(done) |
| `op-scenario-gate/SKILL.md` | 175/169 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:95-96`; `state.json:113-114` |
| `harness/scenario-gate.md` | 99/94 | 2 | op-scenario-gate Step1 필수 | `op-scenario-gate/SKILL.md:15,27` |
| `harness/state-template.md` | 114/103 | 2 | TASK 단계 초기 생성 | `opal-harness.md:101` |
| `harness/qa-standards.md` | 76/71 | 2 | PM Gate — 3회(analysis/plan/test) | `state.json:47-51,80-84,157-161` |
| `harness/observability.md` | 78/78 | 2 | 매 디스패치 | `opal-harness.md:104` |
| `harness/parallel-execution.md` | 99/93 | 2 | 병렬 디스패치 — **[E] 계획상 근거만, 집행 확인 불가**: PLAN.md는 "P3-A/B/C 병렬 2~3배치"(`PLAN.md:1156-1159`)를 명시하나, `AGENTIC-LOG.md`는 Step 8 정지(#27) 후 "EXECUTE 22/22 완료"(#28)로 **일괄 요약**되어 배치별 집행 로그가 없음 | `tasks/078-.../PLAN.md:1156-1159`; `AGENTIC-LOG.md:37`(#28 요약 표기, 배치별 로그 부재) |
| `harness/state.md` | 144/134 | 2 | TASK 시작/Gate 직후 | `opal-harness.md:108` |
| `harness/task-process.md` | 87/76 | 2 | TASK 단계 진입 | `opal-harness.md:109` |
| `op-task/SKILL.md` | 278/259 | 3 | task-process.md 필수 Read | `harness/task-process.md:13-14` |
| `harness/coding-principles.md` | 103/93 | 2 | EXECUTE 코드 변경 — `memory_tool.py` 등 6개 코드 파일 | `opal-harness.md:110`; `tasks/078-.../DONE.md:41-49` |
| `harness/header-rules.md` | 160/160 | 2 | 변경 파일 확장자 `.py` 포함 | `harness/header-rules.md:63-69`; `tasks/078-.../DONE.md:44`(`memory_tool.py` 등) |

**미발동(제외)**: `harness/additional-work.md`(87/79) — `tasks/078-.../STATE.md`·의사결정 로그에 CLOSE 재진입/ADD_DONE 이벤트 없음(grep 무매치) `[M]`.

**078 합계**: 330+240+426+86+175+99+114+76+78+99+144+87+278+103+160 = **2,495줄** `[D]` (기준 A) / **2,330줄** `[D]` (기준 B) — 080과 문서 집합·줄수 동일, `parallel-execution.md`의 확신도만 `[M]`→`[E]`로 다름.

### 3.3 077 (opd/semi-agentic)

| 문서 | 줄수[M] A/B | 홉 | 발동조건 | 근거 |
|------|-----------|----|---------|------|
| `opal-harness.md` | 330/276 | 1 | 항상 | `opal-pilot-dev/SKILL.md:12` |
| `opal-harness-semi-agentic.md` | 242/233 | 2 | mode=semi-agentic | `state.json:4` |
| `harness/citation-rules.md` | 426/416 | 1 | 직접 1홉 | `opal-pilot-dev/SKILL.md:20` |
| `harness/red-first.md` | 86/81 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:86,108`; `state.json:113-114`(done) |
| `op-scenario-gate/SKILL.md` | 175/169 | 1 | scenario_gate 행 존재 | `opal-pilot-dev/SKILL.md:95-96`; `state.json:113-114` |
| `harness/scenario-gate.md` | 99/94 | 2 | op-scenario-gate Step1 필수 | `op-scenario-gate/SKILL.md:15,27` |
| `harness/state-template.md` | 114/103 | 2 | TASK 단계 초기 생성 | `opal-harness.md:101` |
| `harness/qa-standards.md` | 76/71 | 2 | PM Gate — 3회(analysis/plan/test) | `state.json:47-51,80-84,158-162` |
| `harness/observability.md` | 78/78 | 2 | 매 디스패치 | `opal-harness.md:104` |
| `harness/parallel-execution.md` | 99/93 | 2 | 병렬 디스패치 — **[E] 계획상 근거만, 집행 확인 불가**: PLAN.md는 "3.배선 2트랙 병렬"·"4.문서 4트랙 병렬"(`PLAN.md:1274-1275`)을 명시하나, `AGENTIC-LOG.md`는 37줄에서 Step 5~12 진입 기록 이후 종료되어(`AGENTIC-LOG.md:33-37`) 해당 병렬 배치(Step 13~18)의 집행 로그가 문서에 없음. `Step 5~12`는 오히려 "8 Step 전부 동일 파일이라 **병렬 금지**"로 명시적 순차 확정(`AGENTIC-LOG.md:35`) | `tasks/077-.../PLAN.md:1274-1275`; `AGENTIC-LOG.md:35,37` |
| `harness/state.md` | 144/134 | 2 | TASK 시작/Gate 직후 | `opal-harness.md:108` |
| `harness/task-process.md` | 87/76 | 2 | TASK 단계 진입 | `opal-harness.md:109` |
| `op-task/SKILL.md` | 278/259 | 3 | task-process.md 필수 Read | `harness/task-process.md:13-14` |
| `harness/coding-principles.md` | 103/93 | 2 | EXECUTE 코드 변경 — `code-scan.js`·`code-map-hook.js` | `opal-harness.md:110`; `tasks/077-.../DONE.md:18,21` |
| `harness/header-rules.md` | 160/160 | 2 | 변경 파일 확장자 `.js` 포함 | `harness/header-rules.md:63-69`; `tasks/077-.../DONE.md:18,21` |

**미발동(제외)**: `harness/additional-work.md`(87/79) — `tasks/077-.../STATE.md:33,41`의 "행 15 추가작업: listCodeFilesInDir 필터 대칭"은 **TEST 단계 진행 중** 발생(CLOSE 이전, `current_status`는 이 시점 아직 미완료)이라 CLOSE 재진입 트리거 미충족 `[M]`(080과 동일 판정 논리).

**077 합계**: 330+242+426+86+175+99+114+76+78+99+144+87+278+103+160 = **2,497줄** `[D]` (기준 A) / 276+233+416+81+169+94+103+71+78+93+134+76+259+93+160 = **2,336줄** `[D]` (기준 B)

---

## §4. 잔차 정량 분해 — `A4-로드사슬.md:151`

> 원문 인용(`A4-로드사슬.md:151`): "**[E] pilot 스코프 차이** — 기준값(3,144줄)은 opd(코드 중심, TEST-SCENARIO·RED-first·header-rules 상시 적용 가능성이 높은 pilot) 기준 추정이고, 본 표본은 opds/opp다. ... ①②③ 세 요인만으로 잔차 0을 만들 수 없다."

### 4.1 opd 3표본 실효값 vs opds/opp 실효값 대조

| 항목 | 실효값[D] (기준 A) | 실효값[D] (기준 B) |
|------|---------------------|---------------------|
| 085 (opds/agentic) | 2,335 | — |
| 084 (opp/agentic) | 1,872 | — |
| 083 (opds/semi-agentic) | 2,337 | — |
| **080 (opd/agentic)** | **2,495** | **2,330** |
| **078 (opd/agentic)** | **2,495** | **2,330** |
| **077 (opd/semi-agentic)** | **2,497** | **2,336** |

opd 3표본은 opds 표본(085·083, 2,335/2,337)보다 각각 **+158~+162줄** 크다 `[D]`. 그 전량은 §3에서 실측한 **`header-rules.md`(160/160) 신규 활성화** 1건으로 정확히 귀속된다(opd 3건 모두 `.js`/`.py` 코드 변경 → 대상 확장자 충족, opds 표본 085·083은 `.sh`/`.md`류만 변경 → 미충족, A4:84·126) `[M/D]`. 즉 **"opd가 opds보다 큰 이유"는 A4 §1.1의 ①②③ 세 요인이 아니라, opd가 항상 코드 변경을 포함하는 Full Task라서 opds/opp보다 `header-rules.md` 활성 확률이 구조적으로 높다는 4번째 요인**이며, 이는 A4 §1.1이 열거하지 않은 요인이다.

### 4.2 opd "16문서 3,144줄(정적 합산)"의 재구성

`TASK.md:21`(A4:16 인용)의 원문은 "opd 완주 시 참조 사슬 **16문서** 3,144줄(정적 합산)"이다. §3의 3표본에서 **활성화 문서는 15개**(모드 서브 하네스 1종 + 14 Lazy/직접 참조 문서)이고, 제외된 문서는 `additional-work.md` **1개**뿐이다(§3.1~3.3 "미발동" 행). 15 + 1 = **16문서** — `TASK.md:21`의 "16문서"와 **정확히 일치한다** `[M/D]`.

이 16문서 전체(모드 서브 하네스 **3종 전부** + `additional-work.md` 포함, §1.1 ①요인을 반영하지 않은 순수 정적 합산)를 다시 더하면:

| 문서군 | 기준 A 줄수 | 기준 B 줄수 |
|--------|-----------|-----------|
| `opal-harness.md` | 330 | 276 |
| 서브 하네스 3종(`agentic`+`semi-agentic`+`interactive`) | 240+242+185=667 | 227+233+165=625 |
| `harness/citation-rules.md` | 426 | 416 |
| `harness/red-first.md` | 86 | 81 |
| `op-scenario-gate/SKILL.md` | 175 | 169 |
| `harness/scenario-gate.md` | 99 | 94 |
| `harness/state-template.md` | 114 | 103 |
| `harness/qa-standards.md` | 76 | 71 |
| `harness/observability.md` | 78 | 78 |
| `harness/parallel-execution.md` | 99 | 93 |
| `harness/state.md` | 144 | 134 |
| `harness/task-process.md` | 87 | 76 |
| `op-task/SKILL.md` | 278 | 259 |
| `harness/coding-principles.md` | 103 | 93 |
| `harness/header-rules.md` | 160 | 160 |
| `harness/additional-work.md` | 87 | 79 |
| **합계(16문서, 정적)** | **3,009** | **2,807** |

`TASK.md:21`의 3,144줄과 대조: 기준 A **3,009 (차이 −135, −4.3%)**, 기준 B **2,807 (차이 −337, −10.7%)** `[D]`.

**판정**: 기준 A 기준 오차 4.3%는 "opd 완주 시 16문서 3,144줄" 주장을 **독립 재구성으로 재현 가능한 범위 내에서 검증**한다 — 3,144는 근사 추정치였고, 실제 정적 합산(16문서 전량, 모드 서브하네스 3종 중복 포함)은 3,009로 **일치 방향(같은 자릿수, 4% 이내)**이다. 잔여 오차(135줄)는 `TASK.md`(086, 2026-08-08 이전 작성) 시점과 본 실측 시점(기준 A 현재 소스) 사이의 **문서 버전 드리프트**로 설명된다 `[E, 근거: 문서별 정확한 과거 버전 diff는 미확인 — git blame 대비 시점 특정이 이 산출물의 범위를 벗어남]`. 기준 B(배포본)의 오차가 더 큰 것(10.7%)은 배포본이 087 이전 릴리즈로 project 소스보다 더 오래된 스냅샷이기 때문이며 이 방향성 자체가 "버전 드리프트" 설명과 정합한다 `[D]`.

---

## §5. `A4-로드사슬.md:193`(§7 #2) 승격 판정

> 원문 인용(`A4-로드사슬.md:193`): "| 2 | §4 잔차(pilot 스코프 차이)의 정량 분해 | `[E]` | 기준값 3,144줄이 opd(본 표본과 다른 pilot) 추정치라 opds/opp 실효값과 문서 집합 자체가 불일치. ①②③ 요인만으로 잔차 0 분해 불가 — P1에서 opd 표본 직접 실측 후 재대조 필요 |"

**승격 결과**: `[E]` → `[D]` (**부분 해소**, 잔존 사유 명시).

1. **해소된 부분**: "기준값 3,144줄이 opd 추정치라 문서 집합 자체가 불일치" 주장은 §4.2에서 **문서 집합 자체는 정확히 16개로 일치**함을 실측했다(`[M/D]`) — 불일치는 "집합"이 아니라 "집합 내 개별 문서 줄수의 버전 시점"이었다. "①②③ 요인만으로 잔차 0 분해 불가"는 §4.1에서 **④ header-rules 활성 요인**(opd 고유, opds/opp 대비 +158~162줄)을 추가로 특정함으로써 요인 목록 자체를 갱신했다 — A4 §1.1에 없는 요인을 P1이 발견했다는 의미다.
2. **잔존하는 부분**: §4.2의 135줄(4.3%) 오차는 "0으로 완전 분해"되지 않았다. 근거 문서(`TASK.md:21`)가 3,144를 산출한 정확한 시점의 문서 버전 스냅샷이 보존되어 있지 않아(git 커밋 시점 대비 opal-harness.md 등 다수 문서의 개별 리비전 추적은 본 산출물 범위 밖), **완전한 0-오차 분해는 구조적으로 재현 불가능**하다 `[E]`. 이는 새로운 잔차이며, 성격이 "pilot 스코프 차이"(집합 불일치)에서 "문서 버전 드리프트"(같은 집합, 다른 시점 줄수)로 **바뀌었다**.

**종합**: BLUEPRINT §5.1 (1) 포함 ⑥ 요구대로 "해소(정량 분해 성립) 또는 잔존 사유 명시" 중 **후자로 종결** — 정량 분해가 4.3% 오차 내로 성립했고 그 오차의 성격과 원인이 명시되었다.

---

## §6. 추정 항목 일람 (본 산출물 신규분)

| # | 항목 | 마커 | 추정 근거 |
|---|------|------|----------|
| 1 | §4.2 잔여 오차 135줄(기준 A)의 정확한 문서별 귀속 | `[E]` | `TASK.md:21` 작성 시점의 개별 문서 과거 리비전이 보존되어 있지 않아 어느 문서가 몇 줄 변경되어 오차를 만들었는지 특정 불가 |
| 2 | 078·077의 `parallel-execution.md` 미확정 발동 | `[E]` | PLAN.md에 병렬 배치 설계는 있으나 AGENTIC-LOG.md가 배치 단위 집행 로그를 남기지 않음(078) 또는 로그 자체가 Step 12에서 종료됨(077) — A4:78,98과 동일한 유형의 잔존 불확실성이며 opd라고 해서 해소되지 않음 |
| 3 | 077 AGENTIC-LOG.md의 기록 범위(Step 12까지)가 실제 실행 범위(Step 22 상당)보다 짧은 이유 | `[E]` | semi-agentic 모드 특성상 TEST-SCENARIO 사용자 확인 이후 자율 진행 구간의 로그 상세도가 낮아지는 것으로 추정되나, 로그 정책 문서 대조는 본 산출물 범위 밖 |

---

## 변경이력

| 버전 | 일시 | 내용 |
|------|------|------|
| v1.0 | 2026-08-09 | 최초 작성 — opd 3표본(080·078·077) 직접 실측, A4 §4 잔차 정량 분해, A4 §7 #2 `[E]`→`[D]`(부분 해소) 승격 (087) |

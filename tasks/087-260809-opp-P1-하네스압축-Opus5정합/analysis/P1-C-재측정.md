# P1-C. C1·C2·C3·C5 재측정 (편집 후)

> 소속: `tasks/087-260809-opp-P1-하네스압축-Opus5정합/PLAN.md` §3 Step 10
> 성격: **측정·판정 전용**. 이 문서는 소스 문서를 1건도 수정하지 않는다. 판정이 Fail이어도 재편집하지 않고 그대로 보고한다.
> 대조군("전" 값): `analysis/P1-B0-기준선.md` (Step 1) · Step 3 판정: `analysis/P1-C5-게이트판정.md`
> 마커 범례: `[M]` 직접 측정 / `[D]` 파생 계산 / `[E]` 추정

---

## 0. 기준 B 측정 방법론 sanity check [M]

**방법**: `~/.opal/`는 087의 소스 편집을 아직 재배포하지 않았다(`scripts/install-mac.sh:207-221`의 `strip_deploy_md`가 `## 변경이력` 섹션부터 파일 끝까지 제거). 따라서 편집 후 배포본 줄수는 소스에서 strip을 시뮬레이션(`awk '/^## 변경이력/{exit} {print}' <소스> | wc -l`)해 산출한다.

**검증 대상**: 이번 태스크에서 **편집하지 않은** 파일 4건.

```bash
for f in harness/red-first.md harness/coding-principles.md opal-harness-semi-agentic.md ../skills/op-scenario-gate/SKILL.md; do :; done
# 실제 실행 (경로 전체)
awk '/^## 변경이력/{exit} {print}' opal/core/references/harness/red-first.md | wc -l   # → 81
wc -l ~/.opal/references/harness/red-first.md                                          # → 81
awk '/^## 변경이력/{exit} {print}' opal/core/references/harness/coding-principles.md | wc -l  # → 93
wc -l ~/.opal/references/harness/coding-principles.md                                  # → 93
awk '/^## 변경이력/{exit} {print}' opal/core/references/opal-harness-semi-agentic.md | wc -l  # → 233
wc -l ~/.opal/references/opal-harness-semi-agentic.md                                  # → 233
awk '/^## 변경이력/{exit} {print}' opal/skills/op-scenario-gate/SKILL.md | wc -l        # → 169
wc -l ~/.opal/skills/op-scenario-gate/SKILL.md                                          # → 169
```

| 파일 | 시뮬레이션 [M] | 실제 배포본 [M] | 일치 |
|------|---------------|----------------|------|
| `harness/red-first.md` | 81 | 81 | ✅ |
| `harness/coding-principles.md` | 93 | 93 | ✅ |
| `opal-harness-semi-agentic.md` | 233 | 233 | ✅ |
| `op-scenario-gate/SKILL.md` | 169 | 169 | ✅ |

**판정: 4/4 전건 일치 — 시뮬레이션 유효.** 아래 기준 B 계산에 이 방법을 사용한다.

> **부수 발견(측정에 영향 없음, 보고)**: `harness/observability.md`는 변경이력 헤더가 표준 형식 `## 변경이력`이 아니라 평문 `변경이력:`이다(`docs/CONVENTIONS.md` §변경이력 작성 의무의 헤더 규격 미준수, **087 편집 이전부터 존재한 기존 결함** — `git diff`로 확인, 087은 헤더 문자열을 건드리지 않음). 이로 인해 `strip_deploy_md`가 이 파일에서 실제로도 stripping을 수행하지 못한다 — 즉 시뮬레이션(패턴 미매치 → 전체 유지)과 실제 배포 동작(헤더 미매치 → 전체 유지)이 **같은 이유로 일치**하여 수치 자체는 왜곡되지 않는다(소스=배포본=67줄). 판정에는 영향 없으나 컨벤션 위반 사실은 별도 보고한다.

---

## C1 — 실효 로드 재측정

**판정식(기준 B, §2.6)**: 재측정 3값(083/084/085) 전건 ≤ (2,176 / 1,733 / 2,170) AND max ≤ 2,000
**기준 A(소스) 값은 부수 기록으로 병기.**

### 1. 편집 후 파일별 줄수 [M]

```bash
wc -l opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md
```

| 파일 | 소스(기준 A) [M] | 배포본 시뮬레이션(기준 B) [M] |
|------|------------------|-------------------------------|
| `opal-harness.md` | 311 | 256 |
| `harness/citation-rules.md` | 305 | 294 |
| `harness/citation-rules-dev.md` (신규) | 50 | 45 |
| `harness/citation-rules-planning.md` (신규) | 106 | 101 |
| `harness/red-first.md` | 86 | 81 |
| `op-scenario-gate/SKILL.md` | 175 | 169 |
| `harness/scenario-gate.md` | 85 | 79 |
| `harness/state-template.md` | 99 | 87 |
| `harness/qa-standards.md` | 66 | 60 |
| `harness/observability.md` | 67 | 67 |
| `harness/parallel-execution.md` | 108 | 101 |
| `harness/state.md` | 118 | 107 |
| `harness/task-process.md` | 82 | 70 |
| `op-task/SKILL.md` | 268 | 248 |
| `harness/coding-principles.md` | 103 | 93 |
| `opal-harness-agentic.md` (미편집) | 240 | 227 |
| `opal-harness-semi-agentic.md` (미편집) | 242 | 233 |

### 2. 신규 부록 발동 조건 판정 (A4 §1.1 ② 기준) [D]

- **`citation-rules-planning.md`**: 발동 조건 = "기획 산출물(정책서·PRD·TRD·IA·와이어프레임 등) 작성 시"(`citation-rules.md:291`). 085(opds)·084(opp)·083(opds) 3표본 모두 TASK/ANALYSIS/PLAN/EXECUTE 산출물이며 기획 산출물(PRD/IA 등)을 생산하지 않는다(`A4-로드사슬.md` §3.1~3.3 문서 목록에 기획 산출물 없음, PLAN.md N-1 근거와 동일). → **3표본 전건 미발동, 실효 로드 합계에서 제외.**
- **`citation-rules-dev.md`**: 발동 조건 = "코드·설계 산출물(ANALYSIS/PLAN/EXECUTE 관련) = 개발 트랙"(`citation-rules.md:47`). 085·084·083 모두 PLAN/EXECUTE 단계를 보유(`A4-로드사슬.md` §2 표: 085 TASK→PLAN→EXECUTE→TEST→CLOSE, 084 TASK→PLAN→EXECUTE→CLOSE, 083 TASK→PLAN→EXECUTE→TEST→CLOSE) → 3표본 전건 개발 트랙 산출물 생산 → **3표본 전건 발동, 실효 로드 합계에 포함(홉 2, citation-rules.md 경유).**

### 3. 표본 3건 실효 로드 재계산 [D]

`A4-로드사슬.md` §3.1~3.3 문서 목록에 위 편집 후 줄수를 대입하고, `citation-rules-dev.md`(발동)를 추가, `citation-rules-planning.md`(미발동)는 제외했다.

#### 085 (opds/agentic) — A4 §3.1 14종 + citation-rules-dev.md

`opal-harness.md(311)+opal-harness-agentic.md(240)+citation-rules.md(305)+red-first.md(86)+op-scenario-gate/SKILL.md(175)+scenario-gate.md(85)+state-template.md(99)+qa-standards.md(66)+observability.md(67)+parallel-execution.md(108)+state.md(118)+task-process.md(82)+op-task/SKILL.md(268)+coding-principles.md(103)+citation-rules-dev.md(50)`

| 기준 | 합계 [D] | 현행값(§2.6) | ≤ 현행값 | ≤ 2,000 |
|------|---------|-------------|---------|---------|
| A(소스) | **2,163** | 2,335(A4 원값) | ✅ | — (기준 A는 2,000 판정 대상 아님, 부수 기록) |
| B(배포본) | **1,984** | 2,170 | ✅ | ✅ |

#### 084 (opp/agentic) — A4 §3.2 10종 + citation-rules-dev.md

`opal-harness.md(311)+opal-harness-agentic.md(240)+citation-rules.md(305)+state-template.md(99)+qa-standards.md(66)+observability.md(67)+parallel-execution.md(108)+state.md(118)+task-process.md(82)+op-task/SKILL.md(268)+citation-rules-dev.md(50)`

| 기준 | 합계 [D] | 목표(§2.6, "증가 금지") | 판정 |
|------|---------|------------------------|------|
| A(소스) | **1,714** | (기준 A 부수 기록, A4 원값 1,872 대비 감소) | ✅ |
| B(배포본) | **1,562** | ≤ 1,733(증가 금지) | ✅ |

#### 083 (opds/semi-agentic) — A4 §3.3 14종 + citation-rules-dev.md

`opal-harness.md(311)+opal-harness-semi-agentic.md(242)+citation-rules.md(305)+red-first.md(86)+op-scenario-gate/SKILL.md(175)+scenario-gate.md(85)+state-template.md(99)+qa-standards.md(66)+observability.md(67)+parallel-execution.md(108)+state.md(118)+task-process.md(82)+op-task/SKILL.md(268)+coding-principles.md(103)+citation-rules-dev.md(50)`

| 기준 | 합계 [D] | 현행값(§2.6) | ≤ 현행값 | ≤ 2,000 |
|------|---------|-------------|---------|---------|
| A(소스) | **2,165** | 2,337(A4 원값) | ✅ | — (부수 기록) |
| B(배포본) | **1,990** | 2,176 | ✅ | ✅ |

### C1 종합 판정

| 표본 | 기준 B 재측정 | 현행값 | 목표 | 재측정 ≤ 현행값 | 재측정 ≤ 2,000 |
|------|-------------|-------|------|-----------------|-----------------|
| 083 | 1,990 | 2,176 | ≤2,000 | ✅ | ✅ (여유 10줄) |
| 084 | 1,562 | 1,733 | 증가 금지(≤1,733) | ✅ | ✅ |
| 085 | 1,984 | 2,170 | ≤2,000 | ✅ | ✅ (여유 16줄) |

**C1 = Pass.** 3값 전건 현행값 이하 AND max(1,990) ≤ 2,000. 083이 여유 10줄로 가장 타이트하다(H-1 리스크가 실제로 임박했으나 미달 없이 충족).

---

## C2 — 홉 재추적

**판정식**: Top5 홉 평균 ≤ 2.0 AND `op-task/SKILL.md` ≤ 2홉. 잔존 3홉 노드 0건 필수(§2.6 함의).

### 1. Step 1 확정 3홉 후보 9건의 현재 홉수 [M]

| # | 노드 | Step 1(편집 전) 판정 | 현재(편집 후) 홉 | 근거 |
|---|------|---------------------|-----------------|------|
| 1 | `op-task/SKILL.md` | 확정 3홉 | **2홉** | `opal-harness.md:119`(표B) — `task-process.md:13`가 Read 지시를 포인터로 대체(`op-task/SKILL.md는 opal-harness.md §2 규칙 인덱스에서 로드된다`) |
| 2 | `pm/context-injection.md` | 확정 3홉 | **2홉** | `opal-harness.md:122`(표B) — `pm-review-gate.md:96`은 "표 B 규칙 인덱스 경유 — 2홉" 정합 표기로 변경 |
| 3 | `pm/dispatch-process.md` | 확정 3홉 | **2홉** | `opal-harness.md:123`(표B) — `pm-review-gate.md:25` 정합 표기 |
| 4 | `header-standard.md` | 확정 3홉 | **2홉** | `opal-harness.md:125`(표B) |
| 5 | `op-dev-qa/SKILL.md` | 판별 보류 | **2홉** | `opal-harness.md:121`(표B) — `pm-review-gate.md:31` 정합 표기 |
| 6 | `op-task-qa/SKILL.md` | 판별 보류 | **2홉** | `opal-harness.md:120`(표B) |
| 7 | `opal-loop-action-agent/AGENT.md` | 판별 보류 | **홉 미계상(단순 인용)** | `observability.md:44` — "해당 채널의 관측성은 이 문서가 아니라 호출 주체가 소유하며…" 형태(적용 범위 제외 선언), Read 지시 아님. `observability.md` v1.4 변경이력(`:67`)에 "단순 인용, 홉 미계상"으로 명시 판정됨 |
| 8 | `pm/code-scan-management.md` | 판별 보류(신규 발견) | **2홉** | `opal-harness.md:124`(표B) |
| 9 | `opal-convention-checker/AGENT.md` | 판별 보류(신규 발견) | **2홉** | `opal-harness.md:126`(표B) |

**잔존 3홉 노드 = 0건.** 9건 중 8건이 `opal-harness.md` §2 표 B(규칙 인덱스, 직접 참조)에 전건 등재되어 2홉으로 평탄화됐고, 1건(`opal-loop-action-agent/AGENT.md`)은 Read 지시가 아닌 단순 인용으로 재확인되어 홉 계상 대상에서 제외된다.

### 2. 3홉+ 잔존 여부 전수 재확인 [M]

편집된 6개 모듈(`state.md`·`state-template.md`·`qa-standards.md`·`observability.md`·`scenario-gate.md`·`parallel-execution.md`) 및 `pm-review-gate.md`의 Read/따른다/참조 간선을 재점검한 결과, §1 표 9건 외 신규 3홉 후보는 발견되지 않았다(`parallel-execution.md:73`의 `dispatch-process.md` 참조도 표B 경유로 2홉).

### 3. Top5 재선정 (A4 §5 선정 기준: ① 홉 깊이 → ② 발동 빈도 → ③ 줄수) [D]

3홉 노드가 0건이므로 최대 홉은 2다. 2홉 노드 중 ② 발동 빈도(표본 3건 실측, A4 §3 기준) → ③ 줄수 순으로 상위 5건을 선정했다.

| 순위 | 문서 | 홉 | 발동 빈도(표본 3건) | 줄수 [M] | 근거 |
|------|------|----|--------------------|---------|------|
| 1 | `op-task/SKILL.md` | 2 | 3/3 (TASK 단계마다) | 268 | `opal-harness.md:119` |
| 2 | `opal-harness-{agentic,semi-agentic}.md`(모드 서브 하네스) | 2 | 3/3 (매 세션 1택) | 240~242 | `opal-harness.md:87-90`(A4 §5 순위5와 동일, 유지 대상) |
| 3 | `header-standard.md` | 2 | 0/3(표본 미발동, 실사용은 코드 변경 시) | 301 | `opal-harness.md:125` |
| 4 | `opal-convention-checker/AGENT.md` | 2 | 0/3 | 255 | `opal-harness.md:126` |
| 5 | `op-dev-qa/SKILL.md` | 2 | 0/3 | 194 | `opal-harness.md:121` |

**Top5 홉 평균 = (2+2+2+2+2)/5 = 2.0.**

### C2 종합 판정

| 항목 | 값 | 판정식 | Pass/Fail |
|------|----|--------|-----------|
| Top5 홉 평균 | 2.0 | ≤ 2.0 | ✅ |
| `op-task/SKILL.md` 홉 | 2 | ≤ 2 | ✅ |
| 잔존 3홉 노드 | 0건 | == 0 | ✅ |

**C2 = Pass.**

---

## C3 — 표 등재

**판정식**: `opal-harness.md` 표 A(하네스 모듈) 데이터 행수 == 12 AND `A4-로드사슬.md` §6 "표 누락(불완전 등재)" 판정 == 0건

### 1. 표 A 데이터 행수 재측정 [M]

Step 10 지시서의 원안 명령(`sed -n '/^### 하네스 모듈/,/^### /p' ... | grep -c '^| \``)은 표 A의 실제 셀 포맷(1열이 한글 모듈명, 2열이 백틱 경로)과 불일치하여 **0을 반환**했다(방법 오류, 별도 보정 명령으로 재측정):

```bash
awk '/^### 하네스 모듈/{f=1} f&&/^### 규칙 인덱스/{exit} f' opal/core/references/opal-harness.md | grep -c '^|'
# → 14 (헤더 1 + 구분선 1 + 데이터 12)
```

데이터 행 12건: State 템플릿·추가작업·QA 표준·Observability·병렬 처리·@header 규칙·인용 규칙·State 관리·TASK 공통 프로세스·Coding Principles·RED-first 규칙·**PM 검토 게이트**(신규 추가, `opal-harness.md:106`).

**표 A 데이터 행수 = 12.** (11→12, R-2 이행 확인)

### 2. 표 누락(불완전 등재) 재판정 [M/D]

`harness/` 디렉토리 실파일 = **19개**(기존 17 + 신규 2: `citation-rules-planning.md`·`citation-rules-dev.md`).

| 분류 | 파일 | 판정 |
|------|------|------|
| 표 A 등재(12) | state-template·additional-work·qa-standards·observability·parallel-execution·header-rules·citation-rules·state·task-process·coding-principles·red-first·**pm-review-gate** | 등재 |
| 의도적 배제(5, A4 §6 기존 판정 유지) | doc-code-mismatch·memory-learning·pm-improvement-loop·scenario-gate·skill-commands | 배제(다른 소유 문서·Lazy 트리거 체계) — `opal-harness.md` 본문에서 신규 참조 없음(`grep -c` 0건 확인) |
| 신규 의도적 배제(2, 087 신설) | citation-rules-planning·citation-rules-dev | 배제 — `opal-harness.md` 직접 참조 0건(§0 sanity check 인접 grep 결과), `citation-rules.md` 본문 조건부 포인터로만 도달(2홉, 표A 관할 밖) |

`grep -n 'citation-rules-planning\|citation-rules-dev' opal/core/references/opal-harness.md` → **0건**(직접 참조 없음, 표 A 관할 대상 아님 확인).

**표 누락(불완전 등재) 판정 = 0건.** 12(등재) + 5(기존 배제) + 2(신규 배제) = 19 전건 설명됨.

### C3 종합 판정

| 항목 | 값 | 판정식 | Pass/Fail |
|------|----|--------|-----------|
| 표 A 데이터 행수 | 12 | == 12 | ✅ |
| 표 누락 판정 | 0건 | == 0 | ✅ |

**C3 = Pass.**

---

## C5 — 도구 게이트

**판정식**: G1 ≥ 26 AND G3 ≥ 72 (Step 1 기준선) AND Step 3 판정표 미기재 == 0

### 1. Step 1과 완전히 동일한 명령 재실행 [M]

```bash
cd /Volumes/Data/AiStudio/workspace/opal
SCOPE="opal/core/references/opal-harness.md opal/core/references/harness opal/skills/op-task/SKILL.md"
grep -rhoE '~/\.opal/tools/(state-tool|test-tool|backlog-tool)/run\.sh' $SCOPE | wc -l
# → 26
for f in opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md; do
  awk '/^## 변경이력/{exit} {print}' "$f"; done | grep -oE '(state-tool|test-tool|backlog-tool)' | wc -l
# → 70
```

> 실행 환경 참고: 본 셸의 `grep` 함수 별칭(ugrep 래퍼)이 `zsh`의 기본 비-word-split 동작과 겹쳐 `$SCOPE` 다중 경로 인자를 한 문자열로 처리하는 결함이 있어 `setopt shwordsplit`으로 우회했다 — 측정 명령 자체·결과값은 Step 1과 동일 정의를 사용했다.

| 지표 | Step 1(전) | Step 10(후, 재측정) [M] | 판정식 | Pass/Fail |
|------|-----------|------------------------|--------|-----------|
| **G1** | 26 | **26** | ≥ 26 | ✅ |
| **G3** | 72 | **70** | ≥ 72 | ❌ **Fail** |

### 2. G3 감소 원인 추적 (파일별 대조) [M]

```bash
for f in opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md; do
  n=$(awk '/^## 변경이력/{exit} {print}' "$f" | grep -oE '(state-tool|test-tool|backlog-tool)' | wc -l)
  echo "$n  $f"
done
```

| 파일 | Step 1 기준선(전) [M] | 현재(후) [M] | 차 |
|------|----------------------|-------------|-----|
| `opal-harness.md` | (§1.1 M-1 대상, 26행 중 6행) | 13(본문 언급 수, 명령행 아님) | — |
| `pm-review-gate.md` | 5(PLAN §참고값) | 5 | 0 |
| `state-template.md` | 5(PLAN §참고값) | 5 | 0 |
| **`state.md`** | **26**(PLAN §참고값, Step 7 완료 기준) | **24** | **−2** |
| `scenario-gate.md` | 8(PLAN §참고값) | 8 | 0 |
| `qa-standards.md` | 2(PLAN §참고값) | 2 | 0 |
| `observability.md` | 0(PLAN §참고값) | 0 | 0 |

`git diff opal/core/references/harness/state.md`로 원인을 특정했다 — §파이프라인 todo 미러 절 압축 중 아래 문장이 요약되며 `state-tool` 언급이 3회 → 1회로 줄었다(순 −2):

- **삭제된 원문**: "- **갱신**: `init` 직후 **state-tool**이 distinct 단계 목록으로 `todo_mirror`(`action=create`)를 출력하고 hook이 주입 → PM이 일괄 생성한다. 이후 `advance`/`mark`/`block` 호출 직후 **state-tool**이 재파생한 `todo_mirror`(`action=update`)를 출력하고 hook이 주입 → PM이 갱신한다. **state-tool** 호출과 1:1로 동반하며 별도 트리거를 만들지 않는다." (3건)
- **대체된 압축 서술**: "**미러 규칙**: … 갱신은 `init`(create) 이후 `advance`/`mark`/`block`(update)마다 **state-tool** 호출과 1:1 동반. …" (1건)

**결론**: Step 7이 자신의 완료 기준("`state.md`의 도구명 언급 수 ≥ Step 1 실측값 26")을 충족하지 못한 채 `[x] 완료`로 처리됐다. 이 축소가 `run.sh` 호출 명령행(G1, 11건 보존 확인됨) 자체를 지운 것은 아니고 본문 서술 중 `state-tool` **단어 언급**만 압축 과정에서 누락됐다.

### 3. Step 3 판정표 미기재 확인 [M]

`analysis/P1-C5-게이트판정.md` §3 — 48행 전건에 `게이트 성격`·`대체 가능성`·`근거`·`조치` 기재 확인, 공란 0건, `조치=삭제` 0건(§1 "실측 결론(선반영)" 및 §3 표 발췌 확인). **미기재 == 0 충족.**

### C5 종합 판정

| 항목 | 값 | 판정식 | Pass/Fail |
|------|----|--------|-----------|
| G1 | 26 | ≥ 26 | ✅ |
| G3 | 70 | ≥ 72 | ❌ |
| Step 3 판정표 미기재 | 0건 | == 0 | ✅ |

**C5 = Fail.** (G1·미기재 조건은 충족하나 G3가 기준선 대비 −2로 미달)

---

## 종합 판정표

| 기준 | 판정식 | 측정값 | Pass/Fail |
|------|--------|--------|-----------|
| **C1** | 재측정 3값(083/084/085) ≤ 현행값(2,176/1,733/2,170) AND max ≤ 2,000 (기준 B) | 1,990 / 1,562 / 1,984 | ✅ Pass |
| **C2** | Top5 홉 평균 ≤ 2.0 AND `op-task/SKILL.md` ≤ 2홉 AND 잔존 3홉 0건 | 평균 2.0 / 2홉 / 0건 | ✅ Pass |
| **C3** | 표 A 데이터 행수 == 12 AND 표 누락 판정 == 0건 | 12 / 0건 | ✅ Pass |
| **C5** | G1 ≥ 26 AND G3 ≥ 72 AND Step3 미기재 == 0 | G1=26 / **G3=70** / 미기재=0 | ❌ **Fail** |

**하나라도 Fail이면 `status: blocked` + `decision_required`로 PM 에스컬레이션한다(§3 Step 10 완료 기준). C5가 Fail이므로 본 산출물은 PM 에스컬레이션 대상이다. 본 문서 작성 과정에서 소스 문서는 1건도 재편집하지 않았다.**

### PM 에스컬레이션 안건

- **원인**: `harness/state.md`의 Step 7 편집이 §파이프라인 todo 미러 절 압축 시 `state-tool` 언급 3건을 1건으로 과압축(순 −2), Step 7 자체 완료 기준("도구명 언급 수 ≥ Step 1 실측값 26")을 충족하지 못한 상태로 `[x] 완료` 처리됨.
- **영향 범위**: G1(명령행 26, 보존 확인) 영향 없음. G3(본문 언급 70 < 72)만 미달 — 삭제된 3문장 모두 `run.sh` 호출문이 아닌 서술문(todo_mirror 메커니즘 설명)이라 실제 도구 게이트 기능 손상은 없으나, C5 판정식(§2.6 H-4 운영 정의)은 문면상 미달이다.
- **PM 결정 필요 사항**: (a) `state.md`에 `state-tool` 언급 2건을 원복하는 재편집(Step 7 재오픈)을 지시할지, (b) G3 판정식 자체가 서술 언급 총량이라는 대리 지표의 한계(실제 게이트 기능 무손상)를 인정해 예외 승인할지. 본 산출물은 임의로 어느 쪽도 선택하지 않고 판정 그대로("Fail")를 보고한다.

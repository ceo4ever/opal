# PLAN: P1 — 하네스 압축 + Opus 5 정합

> 작성일: 2026-08-09 | 입력: TASK.md | 출력: PLAN.md
> 유일 기준 SSOT: `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` §5.1 (범위·완료기준·롤백·불변 제약을 재정의하지 않고 소비한다)
> 작업 성격: **순수 문서(.md) 변경** — 코드 파일 0건, code-scan 미사용(대상이 마크다운 하네스·참조·스킬 문서)

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | P1 범위·완료기준 SSOT | `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` §5.1 (`:104-133`) | 범위 ①~⑥ / P1-C1~C5 판정식 / 롤백 단위 / 불변 제약 3종 |
| D-2 | 소스 | 스폰 실측 | `tasks/086-.../analysis/A3-스폰실측.md` (`:113-123,151-173`) | C4 기준선(K4·StepCount≥10·비EXECUTE 48행) |
| D-3 | 소스 | 로드 사슬 실측 | `tasks/086-.../analysis/A4-로드사슬.md` (`:32-41,136-142,159-167,171-186,191-193`) | C1~C3 기준선·홉 정의·표 등재 결손·§7 #2 잔차 |
| D-4 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` (실측 330줄) | R-1·R-2·R-4·R-5 주 대상 |
| D-5 | 설계 | 하네스 모듈 17종 | `opal/core/references/harness/*.md` | R-1 대상, 규칙 인덱스 재편 |
| D-6 | 설계 | PM 검토 게이트 | `opal/core/references/harness/pm-review-gate.md` (실측 173줄) | R-2 표 등재 대상, 3홉 경유 지점 |
| D-7 | 설계 | TASK 단계 스킬 | `opal/skills/op-task/SKILL.md` (실측 278줄) | R-3 홉 단축 대상 |
| D-8 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` (실측 426줄) | 산출물 인용 규칙 + C1 최대 절감 후보 |
| D-9 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` §변경이력 작성 의무 / §배포 경계 / §플랫폼 분기 격리 / §Citation Rules | 편집 규율 |
| D-10 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 문서 레지스트리·구성 |
| D-11 | 설계 | 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` Step 6 (`:149-160`) | R-4 조건부 분할 배치의 인접 SSOT(산출량 상한 3파일) |
| D-12 | 배경 | P0 결론 brain 페이지 | `.opal/brain/pages/concept/fw-structure-p0-blueprint.md` | P0 확정 맥락(K4·로드 기준선 채택 근거) |
| D-13 | 외부 | Opus 5 프롬프팅 가이드 | [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) | R-5 겹침 판정의 외부 근거 |
| D-14 | 소스 | 배포 스크립트 | `scripts/install-mac.sh:207-221` | 변경이력 strip 사실 — C1 측정 기준 판단 근거 |

### 1.2 [MUST] 인용 — `docs/CONVENTIONS.md`

- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
  → 본 PLAN의 **모든 변경 대상 경로는 `opal/` 프로젝트 소스**다. `~/.opal/`는 **측정에만** 사용한다(읽기 전용).
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."
  → 변경하는 모든 문서에 `(087)` 표기 행 추가. **각 편집 Step의 완료 기준에 편입**한다.
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."
  → R-5(작업 ⑤)의 집행 규칙: **하네스 본문에 특정 모델(Opus 5) 전제 규칙을 신규로 남기지 않는다.** 삭제는 (a) 모델 무관하게 도구가 이미 집행 중인 중복분에 한정한다. 모델 특성 의존 판단은 산출물(analysis)에 기록하되 하네스 본문에 조건문으로 넣지 않는다.
- [MUST] `docs/CONVENTIONS.md` §Citation Rules: "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`)."
- [MUST] `docs/CONVENTIONS.md` §Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
  → **PLAN 단계에서는 PLAN.md만 작성했고 대상 문서는 1건도 수정하지 않았다.**

### 1.3 [MUST] 인용 — BLUEPRINT §5.1 (4) 불변 제약 3종 (원문)

- [MUST] `BLUEPRINT.md` §5.1 (4): "**도구 게이트 제거 0건**: P1은 문서 편집만 수행한다. 편집 전후로 `state-tool`/`test-tool`/`backlog-tool` 호출 지시 문장 수를 grep 카운트로 대조하여 **감소 0건**을 P1-C5에 편입한다."
- [MUST] `BLUEPRINT.md` §5.1 (4): "**pilot alias 진입점 무중단**: `opal-harness.md`·`opal/core/AGENT.md`의 pilot alias 진입 표를 편집 범위에서 **제외**하고, 재편 대상은 규칙 인덱스·모듈 표에 한정한다."
- [MUST] `BLUEPRINT.md` §5.1 (4): "**하위호환 기본값 규율**: 조건부 배치 규칙의 **기본값을 현행 동작(순차 배치)**으로 두고, StepCount ≥ 10 구간에서만 신규 경로가 발동하도록 한다."

### 1.4 관련 파일 (실측)

| 파일 | 역할 | 변경 필요 | 근거(줄번호·실측) |
|------|------|----------|-------------------|
| `opal/core/references/opal-harness.md` | 공통 하네스 · 규칙 인덱스 | ✅ R-1·R-2·R-4·R-5 | 330줄 (`wc -l`), 모듈 표 `:99-113`(데이터 행 11) |
| `opal/core/references/harness/citation-rules.md` | 인용 규칙 | ✅ R-1(C1 절감) | 426줄, §8 기획 전용 `:324-416`(93줄) |
| `opal/core/references/harness/pm-review-gate.md` | PM 검토 게이트 | ✅ R-2(피등재)·R-1 | 173줄, 3홉 경유 지점 `:31,96` |
| `opal/core/references/harness/task-process.md` | TASK 공통 프로세스 | ✅ R-3 | 87줄, `:13-14`가 op-task 3홉 간선 |
| `opal/skills/op-task/SKILL.md` | TASK 단계 스킬 | ✅ R-3 | 278줄, 홉 Top5 순위 1 |
| `opal/core/references/harness/parallel-execution.md` | 병렬 처리 원칙 | ✅ R-4 SSOT | 99줄 |
| `opal/core/references/harness/state.md` | State 관리 | ✅ R-1(C1) | 144줄, 도구 호출행 11 |
| `opal/core/references/harness/state-template.md` | State 템플릿 | ✅ R-1(C1) | 114줄 |
| `opal/core/references/harness/qa-standards.md` | QA 표준 | ✅ R-1(C1) | 76줄 |
| `opal/core/references/harness/observability.md` | 관측 | ✅ R-1(C1) | 78줄 |
| `opal/core/references/harness/scenario-gate.md` | 목표-커버 게이트 | ✅ R-1(C1) | 99줄 |
| `opal/core/references/pm/dispatch-process.md` | 실행 라우팅 | ✅ R-4 포인터 1줄 | 183줄, Step 6 `:149-160` |
| `opal/core/references/harness/{additional-work,coding-principles,red-first,header-rules,doc-code-mismatch,memory-learning,pm-improvement-loop,skill-commands}.md` | 나머지 8종 | ⬜ 원칙적 미변경 | 표 등재·홉 재편 대상 아님(A4 §6 "의도적 배제" 5종 포함) |
| `opal/core/AGENT.md` | 부트스트랩 | ❌ **편집 금지** | 불변 제약 2 — alias/Lazy 진입 표 제외 |
| `opal/core/references/opal-harness-{semi-agentic,interactive,agentic}.md` | 모드 서브 하네스 | ❌ 범위 밖 | BLUEPRINT §5.1 (1) 제외 — "개선 대상 아님" |

### 1.5 현재 상태 (실측 결과)

**(a) 홉 그래프 — C2 관련.** A4 §1.2 홉 정의(1홉 = pilot SKILL.md가 직접 Read 지시, 2홉 = 1홉 문서가 Read 지시, …)를 적용해 `opal-harness.md` + `harness/*.md`의 Read 지시 간선을 전수 grep한 결과, **3홉 노드는 A4 §5 Top5의 4건에 국한되지 않는다**:

| 3홉 노드 | 경유(2홉 문서) | 근거 |
|----------|---------------|------|
| `opal/skills/op-task/SKILL.md` (278줄) | `harness/task-process.md` | `task-process.md:13-14` |
| `opal/skills/op-dev-qa/SKILL.md` (194줄) | `harness/pm-review-gate.md` | `pm-review-gate.md:31` |
| `opal/skills/op-task-qa/SKILL.md` (169줄) | `harness/pm-review-gate.md` | `pm-review-gate.md:31` |
| `opal/core/references/pm/context-injection.md` (111줄) | `harness/pm-review-gate.md` | `pm-review-gate.md:96` |
| `opal/core/references/pm/dispatch-process.md` (183줄) | `harness/pm-review-gate.md`, `harness/parallel-execution.md` | `pm-review-gate.md`(§워커 중단 절), `parallel-execution.md` |
| `opal/agents/opal-loop-action-agent/AGENT.md` | `harness/observability.md` | `observability.md` — **Read 지시/단순 인용 판별 필요** (A4 §1.3) |

> **C2 판정식의 함의**: "재추적 Top5 홉 평균 ≤ 2.0"은 **Top5에 3홉 노드가 1건이라도 남으면 (3+2+2+2+2)/5 = 2.2 로 실패**한다. 즉 C2는 사실상 **하네스 그래프에서 도달 가능한 모든 3홉+ Read 간선을 ≤2홉으로 평탄화**할 것을 요구한다. 이것이 R-1(규칙 인덱스 재편, 1홉 지향)의 실질 정의다.

**(b) 표 등재 — C3 관련.** `opal-harness.md` "하네스 모듈" 표(`:99-113`)의 **데이터 행 = 11**(`:101-111`) [M 확인 — BLUEPRINT §5.1 인용치와 일치]. `harness/` 실파일 = **17종** [M 확인 — `ls` 카운트, BLUEPRINT 인용치와 일치]. `pm-review-gate.md` 미등재 = A4 §6 판정 "표 누락(불완전 등재)" 1건 [M 확인].

**(c) 도구 게이트 grep 기준선 — C5 관련.** BLUEPRINT는 "호출 지시 문장 수"라 했으나 **집계식이 정의되어 있지 않다**. 아래 3종을 실측하고 본 PLAN에서 판정식의 운영 정의를 확정한다. 측정 스코프 = `opal/core/references/opal-harness.md` + `opal/core/references/harness/` + `opal/skills/op-task/SKILL.md`.

| 지표 | 정의 | 기준선(2026-08-09 실측) |
|------|------|------------------------|
| **G1** | 도구 실행 명령 행 — `~/.opal/tools/(state-tool\|test-tool\|backlog-tool)/run.sh` 출현 수 | **26** |
| **G2** | 도구명 총 언급 수(변경이력 포함) | **86** |
| **G3** | 도구명 총 언급 수(**`## 변경이력` 이후 제외** — 본문 한정) | **72** |

> **운영 정의(본 PLAN 확정)**: C5의 "호출 지시 문장 수"는 **G1(도구 실행 명령 행) AND G3(본문 도구명 언급)** 2축으로 판정한다. G2는 변경이력 서술을 포함하므로 채택하지 않는다 — 변경이력은 지시문이 아니고, `install-mac.sh:207-221`이 배포 시 strip 하므로 런타임 게이트 집행력과 무관하다. **판정: 편집 후 G1 ≥ 26 AND G3 ≥ 72 (감소 0건).**

**(d) 실효 로드 기준선 — C1 관련 · [중요 불일치 보고].** A4 §3의 실효 로드값(085=2,335 / 084=1,872 / 083=2,337)은 **프로젝트 소스 파일의 `wc -l`**로 계상되어 있다. 그러나 `scripts/install-mac.sh:207-221`의 `strip_deploy_md` / `strip_deploy_md_recursive`가 배포 시 `## 변경이력` 섹션부터 파일 끝까지 제거하므로, **런타임에 실제로 로드되는 `~/.opal/` 배포본은 소스보다 짧다**:

| 문서 | 소스 줄수 | 배포본 줄수 | 차 |
|------|----------|------------|-----|
| `opal-harness.md` | 330 | 276 | −54 |
| `harness/citation-rules.md` | 426 | 416 | −10 |
| `op-task/SKILL.md` | 278 | 259 | −19 |
| `harness/task-process.md` | 87 | 76 | −11 |
| (이하 동일 경향) | — | — | — |

| 표본 | A4 값(소스 기준) | 배포본 기준 재계산 [D] | 차 |
|------|-----------------|----------------------|-----|
| 085 (opds/agentic) | 2,335 | **2,170** | −165 |
| 084 (opp/agentic) | 1,872 | **1,733** | −139 |
| 083 (opds/semi-agentic) | 2,337 | **2,176** | −161 |

> **PM 보고 사항 (문서/실측 불일치)**: A4 §3의 줄수는 소스 기준이며 실질 로드량을 **약 6~7% 과대계상**한다. 본 PLAN은 **C1 판정을 A4와 동일한 소스 기준(기준 A)으로 수행**한다 — 판정식이 "재측정 3값 전건 ≤ 현행값"이라 기준을 바꾸면 동일 비교가 깨지고, 기준만 바꿔 달성하는 것은 실질 절감이 아니기 때문이다. 배포본 기준(기준 B) 값은 **부수 기록**으로 남기고, 기준 재베이스라인 여부는 PM 판단 사항으로 에스컬레이션한다(§5 H-1).

**(e) K4 분해 검산 — C4 관련.** A3 §4의 K4는 `비EXECUTE 행수 + EXECUTE StepCount (+L3)`로 완전 분해된다 [D, 본 PLAN 검산]:

| 태스크 | 080 | 078 | 077 | 075 | 073 | 072 | 085 | 083 | 082 | 081 | 079 | 076 |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| pilot | opd | opd | opd | opd | opd | opd | opds | opds | opds | opds | opds | opds |
| 비EXECUTE | 5 | 5 | 5+1(L3) | 5 | 5 | 5 | 3 | 3 | 3 | 3 | 3 | 3 |
| StepCount | 14 | 22 | 20 | 8 | 9 | 7 | 6 | 13 | 16 | 8 | 5 | 11 |
| K4 (A3 §4) | 19 | 27 | 26 | 13 | 14 | 12 | 9 | 16 | 19 | 11 | 8 | 14 |
| 검산 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

이 분해가 성립하므로 **C4는 "조건부 배치 규칙을 동일 표본에 적용했을 때의 K4′ 재집계"로 결정론적으로 계산 가능**하다(§2.4).

### 1.6 영향 범위

- **문서 전용** — `opal/tools/` 코드·`state.json` 스키마·`pipeline.json` 무변경. 롤백은 BLUEPRINT §5.1 (3)대로 문서 전용 1커밋 revert로 완결되며 진행 중 태스크의 STATE.md 영향 0.
- **런타임 반영 경로**: 소스 편집 → `./scripts/install-mac.sh` 재배포 시 반영. 본 태스크는 재배포를 강제하지 않으며, 재측정은 **소스 기준**으로 수행한다.
- **하위호환**: R-4 규칙은 StepCount ≥ 10에서만 발동하고 기본값은 현행(순차 배치)이므로, StepCount < 10인 태스크(073·072·085·081·079)의 동작은 무변경이다.
- **역방향 위험**: 홉 평탄화로 `opal-harness.md`에 표가 추가되면 줄수가 늘어 C1과 상충한다(§5 H-2). 표 신설분은 8~12줄 이내로 제한한다.

---

## 2. 구현 계획

### 2.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/core/references/harness/citation-rules-planning.md` | 인용 규칙 §8 비즈니스 용어 우선 원칙(기획 산출물 전용) 분리 — 조건부 로드 | C1 최대 절감 후보. 원본 `citation-rules.md:324-416`(93줄), 기획 트랙(opwt) 전용이라 opd/opds/opp 표본 전건 미발동 (A4 §3에 기획 산출물 없음) |
| N-2 | `opal/core/references/harness/citation-rules-dev.md` | 인용 규칙 개발 트랙 부록(§1.5 개발 열·§2.5 [MUST] 토큰 6종) 분리 — 조건부 로드 | `citation-rules.md:133-168` 개발 트랙 전용 |
| N-3 | `tasks/087-.../analysis/P1-B0-기준선.md` | 편집 전 기준선 실측 (G1/G3·홉 그래프 전수·표 행수·실효 로드 2기준) | C5 전후 대조·C1~C3 재측정의 대조군 |
| N-4 | `tasks/087-.../analysis/P1-A4보정-opd표본.md` | R-6 — opd 표본 직접 실측 + A4 §4 잔차 재대조 | BLUEPRINT §5.1 (1) 포함 ⑥, `A4-로드사슬.md:191-193` |
| N-5 | `tasks/087-.../analysis/P1-C5-게이트판정.md` | R-5 — 비EXECUTE 고정 게이트 48행 건별 대체 가능성 판정표 | C5 "판정 미기재 게이트 == 0" |
| N-6 | `tasks/087-.../analysis/P1-C-재측정.md` | R-7 — C1·C2·C3·C5 재측정 결과 | C1~C3·C5 판정식 실증 |
| N-7 | `tasks/087-.../analysis/P1-C4-재집계.md` | R-7 — C4 K4′ 재집계 결과 | C4 판정식 실증 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/opal-harness.md` | ① §2에 "규칙 인덱스(직접 참조)" 표 신설 — 3홉 노드 전건 승격 ② 하네스 모듈 표에 `pm-review-gate.md` 행 추가(11→12행) ③ §2~§10 stub 중복 서술을 모듈 표 열로 흡수(본문 압축) ④ §7 병렬 처리 stub에 조건부 분할 배치 1줄 포인터 ⑤ R-5 판정상 "모델 무관·도구 집행 중복분" 삭제 ⑥ 변경이력 행 추가 | R-1·R-2·R-3·R-4·R-5, D-1 §5.1 (1) ①②③④⑤ |
| M-2 | `opal/core/references/harness/citation-rules.md` | §8 → N-1 분리, §2.5(+§1.5 개발 열) → N-2 분리, 분리 지점에 조건부 로드 포인터 삽입, 변경이력 행 추가 | C1 절감(최대 −126줄 목표) |
| M-3 | `opal/core/references/harness/task-process.md` | "스킬 영역(op-task/SKILL.md Read 지시)" 절을 **인덱스 포인터로 대체** — op-task는 M-1 규칙 인덱스에서 직접 참조(2홉화). 채번·저장 경로 규칙은 유지. 변경이력 행 추가 | R-3, `A4-로드사슬.md:161` 권고 |
| M-4 | `opal/skills/op-task/SKILL.md` | 도달 경로 주석 갱신(2홉 진입 명시) + 중복 서술 정리. **`state-tool` 호출 지시 행 보존.** 변경이력 행 추가 | R-3, C5 |
| M-5 | `opal/core/references/harness/parallel-execution.md` | **R-4 조건부 분할 배치 규칙 SSOT 신설** — 기본값=현행 순차, StepCount ≥ 10에서만 발동, 배치 크기 B, 산출량 상한 3파일 우선 규칙. 변경이력 행 추가 | R-4, D-1 §5.1 (4) 하위호환 |
| M-6 | `opal/core/references/harness/pm-review-gate.md` | 모듈 표 등재에 맞춘 헤더 stub 정합(로드 시점 명시) + 하위 3홉 참조를 인덱스 경유로 정합. 변경이력 행 추가 | R-2·R-1 |
| M-7 | `opal/core/references/harness/state.md` | 중복 서술 압축(C1). **`state-tool` 명령 행 11건 전건 보존** | C1·C5 |
| M-8 | `opal/core/references/harness/state-template.md` | 중복 서술 압축(C1). 도구 명령 행 보존 | C1·C5 |
| M-9 | `opal/core/references/harness/qa-standards.md` | 중복 서술 압축(C1) | C1 |
| M-10 | `opal/core/references/harness/observability.md` | 중복 서술 압축(C1) + 하위 참조 Read/인용 판별 정합 | C1·C2 |
| M-11 | `opal/core/references/harness/scenario-gate.md` | 중복 서술 압축(C1). `test-tool` 언급 8건 전건 보존 | C1·C5 |
| M-12 | `opal/core/references/pm/dispatch-process.md` | Step 6에 조건부 분할 배치 SSOT 포인터 1줄 추가(수치 비복제) | R-4 정합, `dispatch-process.md:157-160` |
| M-13 | `tasks/087-.../STATE.md` | 단계 진행 갱신 — **`state-tool`로만** | `docs/CONVENTIONS.md` §State 관리 |
| M-14 | `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A3-스폰실측.md` | `:173` C4 대상 집합 7건→6건·"139 중 108(77.7%)"→96/139(69.1%)·미만 5건→6건 정정 + EXECUTE 합계 139/140 정의 각주 신설 + `[정오 2026-08-09, 087]` 블록 | **R-8** (캡틴 결정 2026-08-09), §5 불일치 표 #7 |
| M-15 | `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` | §5.1 (2) P1-C4 대상 집합 인용 문구를 실측값과 동기화 + `[정오 2026-08-09, 087]` 블록. **판정식·임계값 12.0/8.0 불변** | **R-8**, D-1 §5.1 (2) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | 없음 | 파일 삭제 0건. R-5의 삭제는 **파일 단위가 아닌 문장 단위**이며, 삭제 대상은 N-5 판정표에서 "모델 무관 + 도구 집행 중복" 판정을 받은 산문에 한정한다 |

### 2.2 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 기준선 실측 (편집 전 필수) | N-3 | 중 |
| 2 | R-6 opd 표본 재대조 | N-4 | 중 |
| 3 | R-5 게이트 48행 건별 판정 | N-5 | 상 |
| 4 | `opal-harness.md` 단일 파일 집중 편집 | M-1 | 상 |
| 5 | citation-rules 분할 | M-2, N-1, N-2 | 상 |
| 6 | 홉 단축 + R-4 규칙 본문 | M-3, M-4, M-5 | 중 |
| 7 | 하네스 모듈 압축 A | M-6, M-7, M-8 | 중 |
| 8 | 하네스 모듈 압축 B | M-9, M-10, M-11 | 중 |
| 9 | dispatch-process 포인터 | M-12 | 하 |
| 10 | C1·C2·C3·C5 재측정 | N-6 | 상 |
| 11 | C4 K4′ 재집계 | N-7 | 상 |
| 12 | 상위 SSOT 정오 반영 (R-8) | M-14, M-15 | 중 |

> `docs/` 관련 문서 최신화는 EXECUTE 체크리스트 대상이 아니다 — `opal/skills/opal-pilot-project/SKILL.md:123-126`(CLOSE STEP 4 2항)이 소유한다(§3 말미 참조).

> **의존 원칙**: 측정(1~3) → 편집(4~9) → 재측정(10~11). 편집 Step은 **파일 집합이 서로 비중첩**이며, 동일 파일을 건드리는 변경은 모두 하나의 Step에 묶여 있다(`opal-harness.md`는 M-1 단독, R-1·R-2·R-4·R-5 변경이 전부 Step 4에 집중).

### 2.3 핵심 설계 — R-1/R-2/R-3 (규칙 인덱스 재편 + 홉 평탄화)

**설계 결정 D-A: C3(표 12행)과 C2(홉 평탄화)의 충돌을 표 분리로 해소한다.**

C3 판정식은 `표 행수 == 12`(→ D-1 §5.1 (2))로 **상한이자 하한**이다. 홉 평탄화 대상(op-task/SKILL.md 등 5~6종)을 같은 표에 넣으면 행수가 12를 넘어 C3가 실패한다. 따라서:

- **표 A — "하네스 모듈"** (기존, `opal-harness.md:99-113`): Lazy 로드되는 `harness/` 모듈 전용. **데이터 행 11 → 12**(`pm-review-gate.md` 1행 추가)로 정확히 맞춘다. 이 표에 다른 행을 추가하지 않는다. (→ D-1 §5.1 (2) P1-C3)
- **표 B — "규칙 인덱스(직접 참조)"** (신설): `harness/` 모듈이 **아닌** 문서(단계 스킬·PM 절차 문서)를 하네스가 직접 지시하여 2홉으로 만드는 인덱스. 표 A와 소유 도메인이 다르므로 의미상으로도 분리가 옳다.

표 B 초안 (행은 Step 1 기준선 실측의 3홉 노드 전수 결과로 확정):

| 문서 | 로드 시점 | 탐색 경로 |
|------|----------|----------|
| `op-task/SKILL.md` | TASK 단계 진입 시 | `{프로젝트}/.opal/skills/op-task/SKILL.md` → `~/.opal/skills/op-task/SKILL.md` |
| `op-task-qa/SKILL.md` | PM Gate 문서검증 시 (비개발 트랙) | `~/.opal/skills/op-task-qa/SKILL.md` |
| `op-dev-qa/SKILL.md` | PM Gate 문서검증 시 (개발 트랙) | `~/.opal/skills/op-dev-qa/SKILL.md` |
| `pm/context-injection.md` | 워커 컨텍스트 주입 시 | `~/.opal/references/pm/context-injection.md` |
| `pm/dispatch-process.md` | 실행 라우팅·재배치 판정 시 | `~/.opal/references/pm/dispatch-process.md` |

- **R-2 표 A 추가 행**: `| PM 검토 게이트 | harness/pm-review-gate.md | PM Gate 수행 시 / 워커 완료 수신 직후 | §1 |` — 로드 시점 문구는 `pm-review-gate.md:4` 원문("PM Gate 수행 시 / 워커 완료 수신 직후")을 그대로 사용한다.
- **R-3 홉 단축 방식**: `task-process.md:13-14`의 "op-task/SKILL.md를 Read한다" 간선을 제거하고 표 B 행으로 대체한다 → op-task 최단 경로 = opal-harness.md(1홉) → op-task/SKILL.md(2홉). **≤2홉 충족** (→ D-1 §5.1 (2) P1-C2)
- **불변 제약 2 준수**: 표 A·표 B는 모두 **규칙 인덱스·모듈 표**이며, `opal/core/AGENT.md`의 Lazy 트리거 표(`AGENT.md:54-64`)와 pilot alias 진입 경로는 **1자도 편집하지 않는다**. (→ D-1 §5.1 (4))

### 2.4 핵심 설계 — R-4 (StepCount ≥ 10 조건부 분할 배치)

**설계 결정 D-B: 규칙 SSOT는 `harness/parallel-execution.md`(하네스 모듈, 범위 내), `pm/dispatch-process.md`는 포인터 1줄만 둔다(수치 비복제).**

규칙 본문 초안 (`parallel-execution.md` 신설 절):

> **조건부 분할 배치 (기본값 = 현행 순차 배치)**
> 1. **기본값**: PLAN.md §4 실행 체크리스트의 EXECUTE Step은 현행대로 순차 배치한다. 이 절의 신규 경로는 **발동하지 않는다.**
> 2. **발동 조건**: EXECUTE StepCount ≥ 10 인 경우에만 아래 3~5를 적용한다. StepCount < 10이면 1의 기본값을 유지한다.
> 3. **묶음**: 의존 관계가 없는 연속 Step을 **배치 크기 B = 5**로 묶어 1회 디스패치한다.
> 4. **상한 우선**: 묶은 배치의 산출 파일 합집합이 3개를 초과하면 3개 이하가 되도록 다시 분할한다 — `pm/dispatch-process.md` Step 6 항목 5(산출량 상한)가 본 절보다 우선한다.
> 5. **동일 파일 규율**: 동일 파일을 변경하는 Step은 분할하지 않고 같은 배치에 순차 편집으로 묶는다.

- [MUST] `BLUEPRINT.md` §5.1 (4): "조건부 배치 규칙의 **기본값을 현행 동작(순차 배치)**으로 두고, StepCount ≥ 10 구간에서만 신규 경로가 발동하도록 한다" → 위 1·2가 이 제약의 직접 구현이다.

**B = 5 선택 근거 (결정론적 계산).** §1.5 (e)의 K4 분해로 K4′를 계산한다: `K4′ = 비EXECUTE + Σ 배치수`, 배치수 = `ceil(StepCount / B)`(상한 규칙 미발동 가정 상한값).

| pilot | 대상(StepCount≥10) | 미대상(현행 유지) | K4′ 합계 | 평균 | 판정식 임계 | 결과 |
|-------|-------------------|------------------|---------|------|------------|------|
| opd | 080(14)→5+3=8, 078(22)→5+5=10, 077(20)→6+4=10 | 075 13 + 073 14 + 072 12 = 39 | 39+28 = **67** | **11.17** | ≤ 12.0 | ✅ |
| opds | 083(13)→3+3=6, 082(16)→3+4=7, 076(11)→3+3=6 | 085 9 + 081 11 + 079 8 = 28 | 28+19 = **47** | **7.83** | ≤ 8.0 | ✅ |

> 참고: **B = 4**이면 opd 70/11.67 ✅, opds 48/8.00 ✅(경계 동점), **B = 3**이면 opd 75/12.5 ❌. 따라서 **B = 5를 기본값으로 채택**하고, B ≥ 4를 하한으로 명시한다. 단 위 값은 §4 상한 규칙(산출 파일 3개)이 발동하지 않는 경우의 상한이며, 실제 K4′는 Step 11에서 각 표본 PLAN.md의 Step별 `**파일**` 합집합으로 재집계한다(§5 H-3).

**설계 결정 D-C: 조건부 규칙 발동 대상은 A3 §5 StepCount 실측에 따라 6건이다 (상위 SSOT 인용치 7건과 다름 — 실측 우선).**

- 발동 대상(StepCount ≥ 10) = **6건: 080(14)·078(22)·077(20)·082(16)·083(13)·076(11)**, EXECUTE 행 합 = **96**.
- 미발동(현행 순차 유지) = **6건: 075(8)·073(9)·072(7)·085(6)·081(8)·079(5)**.
- 근거: `A3-스폰실측.md:129`(opd StepCount `14+22+20+8+9+7`, 태스크 순서 080·078·077·**075**·073·072) · `:141`(opds `6+13+16+8+5+11`, 085·083·082·081·079·076) · `:163-164`(배수 표 `opd (7,9,8,20,22,14)` / `opds (11,5,8,16,13,6)`). 세 곳 모두 **075 = 8**로 일치한다.
- `A3-스폰실측.md:173`(및 이를 그대로 인용한 `BLUEPRINT.md` §5.1 (2) P1-C4)은 대상을 **7건(075 포함)**, EXECUTE 행 비중을 **"139 중 108(77.7%)"**로 서술하나, 075는 A3 자신이 정한 절단점(StepCount ≥ 10) 미만이고 실측 합은 96이다. 또한 A3 §5는 EXECUTE 합계를 `:151`에서 **140**, `:165`·`:173`에서 **139**로 혼용한다. → **문서/코드 불일치 규칙에 따라 실측(6건·96)을 채택**하고, 정정 사실을 §5 불일치 표 #7에 기재하여 PM에 보고한다.
- **판정식 영향: 없음.** P1-C4 판정식은 "**동일 표본 재집계** K4 평균 ≤ 12.0(opd) AND ≤ 8.0(opds)"이므로 분모는 대상 집합이 아니라 **pilot별 표본 6건 전체**다(opd 6 / opds 6). 대상 집합이 7건→6건으로 정정되어도 분모·임계값은 불변이며, 정정의 효과는 "075를 현행 K4 13 그대로 계상한다"는 분자 계산 방식에만 미친다 — 이는 [MUST] `BLUEPRINT.md` §5.1 (4) 하위호환 기본값 규율(StepCount < 10은 현행 유지)과 정확히 일치한다.

### 2.5 핵심 설계 — R-5 (Opus 5 겹침 판정) · 플랫폼 중립성

**대상 모집단**: A3 §5(`:151-157`)의 비EXECUTE 고정 게이트 **48행** = opd 6건 × 5단계(TASK/ANALYSIS/PLAN/TEST-SCENARIO/TEST) = 30 + opds 6건 × 3단계(TASK/PLAN/TEST) = 18. [D, 본 PLAN 검산]

**판정표 스키마** (N-5, 48행 전건):

| 열 | 내용 |
|----|------|
| `task` / `stage` | 표본 태스크 번호 / 게이트 단계 |
| `게이트 성격` | 도구 집행(state-tool/test-tool) / 산문 지시 / 사용자 게이트 |
| `대체 가능성` | `대체가능(모델무관 중복)` / `대체불가(도구 집행)` / `대체불가(사용자 승인)` / `대체불가(플랫폼 의존 위험)` |
| `근거` | `{경로}:{라인}` |
| `조치` | `삭제` / `유지` / `유지(도구 게이트)` |

- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리 적용 규칙 — **삭제 허용 범위는 (a) 모델 무관하게 도구가 이미 집행 중인 중복 산문에 한정**한다. 모델 특성에 의존하는 지시는 삭제하지도, 하네스 본문에 조건문으로 남기지도 않고 **`대체불가(플랫폼 의존 위험)`로 판정 기재만 하고 유지**한다. 결과적으로 **하네스 본문에 Opus 5(또는 임의 모델) 전제 규칙이 신규로 추가되는 일은 0건**이다.
- **C5 판정식 2축**: ① 판정 미기재 게이트 == 0 (48행 전건 `대체 가능성` + `근거` 채움) ② G1 ≥ 26 AND G3 ≥ 72 (§1.5 (c) 운영 정의). `조치=삭제`는 도구 게이트 행(`state-tool`/`test-tool`/`backlog-tool` 포함 문장)에 **절대 적용하지 않는다**.

### 2.6 핵심 설계 — C1 라인 예산 (최고 위험 항목)

> **[기준 변경 2026-08-09, 캡틴 승인 — H-1 발동]** C1 판정 기준을 **기준 A(소스) → 기준 B(배포본 `~/.opal/`)로 재베이스라인**한다.
> - **사유**: `scripts/install-mac.sh:207-221`의 `strip_deploy_md`가 배포 시 `## 변경이력`을 제거하므로, 런타임에 실제 로드되는 것은 배포본이다. A4 §3의 소스 `wc -l` 계상은 실질 로드를 6~7% 과대계상한 오류이며, 이 불일치는 **PLAN 착수 시점 §1.5 (d)에 기록되어 H-1로 관리**되어 왔다(사후 발명이 아니다).
> - **결정 시점 실측**: Step 4·5 완료 후 083 = 기준 A 2,197(추가 −197 필요, 남은 대상 975줄의 20% 압축) / 기준 B 2,034(추가 −34 필요). 기준 A는 문서 품질 손상 없이는 도달 불가로 판정.
> - **완화가 아님**: 기준 B에서도 083·085는 추가 절감을 요구받는다(−34 / −28). 기준만 바꿔 통과하는 구조가 아니다.
> - **판정식 불변**: "재측정 3값 전건 ≤ 현행값 AND max ≤ 2,000"은 그대로다. 바뀐 것은 **줄수 계상 방식**이며, 전후 대조는 동일 기준(B) 내에서 수행한다.
> - 근거: `AGENTIC-LOG.md` 판단 9 / BLUEPRINT §5.1 (2) P1-C1

**목표(기준 B — 배포본)**: 083: 2,176 → ≤ 2,000 (**−176**), 085: 2,170 → ≤ 2,000 (**−170**), 084: 1,733 → ≤ 1,733(증가 금지). 083/085가 최대 제약이다.
**참고(기준 A — 소스, 부수 기록)**: 083: 2,337 / 085: 2,335 / 084: 1,872. 재측정 시 양 기준을 **병기**한다.

| 파일 | 현재 | 절감 수단 | 목표 절감 |
|------|------|----------|----------|
| `citation-rules.md` | 426 | §8(93줄) → N-1 분리, §2.5+§1.5 개발 열(약 36줄) → N-2 분리, §3.1/3.2 예시 압축 | **−126** |
| `opal-harness.md` | 330 | §2~§10 stub 8개의 "적용 주체/적용 시점/PM Gate 검증" 3행 반복을 표 A 열로 흡수 | **−45** (표 B 신설 +10 상쇄 후 순 −35) |
| `task-process.md` | 87 | op-task 포인터 절 제거(표 B로 이관) + 중복 압축 | **−27** |
| `state.md` | 144 | 서술 중복 압축(도구 명령 행 11건 보존) | **−25** |
| `state-template.md` | 114 | 서술 중복 압축 | **−15** |
| `op-task/SKILL.md` | 278 | 중복 서술 정리 | **−25** |
| `scenario-gate.md` | 99 | 서술 중복 압축(test-tool 언급 8건 보존) | **−15** |
| `qa-standards.md` | 76 | 서술 중복 압축 | **−10** |
| `observability.md` | 78 | 서술 중복 압축 | **−10** |
| `parallel-execution.md` | 99 | R-4 규칙 추가 | **+12** |
| **합계** | — | — | **−286 (083/085 기준)** |

> **[E] 부족분 51줄**: 위 예산은 목표 −337에 **51줄 부족**하다. Step 10에서 실측 후 미달이면 **예비 절감 후보**를 순차 적용한다 — ① `citation-rules.md` §6 사람/AI 탐색 가이드(`:251-275`, 25줄) 부록 이관 ② `qa-standards.md`·`state-template.md` 예시 블록 추가 압축 ③ `pm-review-gate.md` 서술 압축. 그래도 미달이면 **PLAN 재설계 없이 임의 감축을 시도하지 않고 `decision_required`로 PM 에스컬레이션**한다(§5 H-1). 이때 대안 안건은 "기준 B(배포본) 재베이스라인 채택 여부"이며, 기준 B에서는 083 = 2,176 → −176만 필요하므로 위 예산으로 충족된다.
> **금지**: `## 변경이력` 표를 C1 절감 수단으로 삭제·축약하지 않는다 — (a) `docs/CONVENTIONS.md` §변경이력 작성 의무 위반 (b) 배포 시 strip되므로 실질 로드 절감 0 (c) G2 감소로 C5 오탐 유발.

---

## 3. 실행 체크리스트

> 총 12개 Step. Phase 0(측정) → Phase 1(편집) → Phase 2(재측정) → Phase 3(상위 SSOT 정오 + `docs/` 갱신). `docs/` 갱신은 CLOSE 훅 소유이므로 Step으로 두지 않는다(§3 말미).
> **파일 집합 규율**: 각 Step의 산출·수정 파일 합집합 ≤ 3개. `opal-harness.md`를 건드리는 변경은 전부 Step 4 하나에 묶여 있다.

### Phase 0 — 기준선 측정 (편집 전 필수 · Step 1~3 병렬 가능)

#### Step 1: 기준선 실측 수집 (C5 전후 대조 대조군)
- [x] 완료
- **파일**: `tasks/087-260809-opp-P1-하네스압축-Opus5정합/analysis/P1-B0-기준선.md` (신규 1개)
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. 도구 게이트 카운트 G1/G2/G3 실측 — 아래 명령 그대로 실행하고 출력값을 표로 기재:
     ```bash
     cd /Volumes/Data/AiStudio/workspace/opal
     SCOPE="opal/core/references/opal-harness.md opal/core/references/harness opal/skills/op-task/SKILL.md"
     # G1 도구 실행 명령 행
     grep -rhoE '~/\.opal/tools/(state-tool|test-tool|backlog-tool)/run\.sh' $SCOPE | wc -l
     # G2 도구명 총 언급(변경이력 포함)
     grep -rhoE '(state-tool|test-tool|backlog-tool)' $SCOPE | wc -l
     # G3 본문 한정(변경이력 제외) — 파일별 합산
     for f in opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md; do
       awk '/^## 변경이력/{exit} {print}' "$f"; done | grep -oE '(state-tool|test-tool|backlog-tool)' | wc -l
     # G1 파일별 내역(삭제 금지 행 목록 확보)
     grep -rnE '~/\.opal/tools/(state-tool|test-tool|backlog-tool)/run\.sh' $SCOPE
     ```
  2. 파일별 소스 줄수 실측: `wc -l opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md opal/core/references/pm/*.md`
  3. 배포본 줄수 실측(읽기 전용): `wc -l ~/.opal/references/opal-harness.md ~/.opal/references/harness/*.md ~/.opal/skills/op-task/SKILL.md`
  4. 표 A 데이터 행수 실측: `awk 'NR>=101 && NR<=111' opal/core/references/opal-harness.md | grep -c '^|'`
  5. **홉 그래프 3홉+ 전수 조사** — `opal-harness.md` 및 표 A 등재 모듈 각각에서 `grep -nE 'Read|탐색|따른다|참조'` 로 `.md` 참조를 추출하고, `A4-로드사슬.md:45`(§1.3) 기준으로 **Read 지시 / 단순 인용**을 건별 판별하여 3홉 이상 노드를 전건 열거한다(§1.5 (a) 6건은 후보이며 최종은 실측 결과).
  6. 표본 3건(085/084/083) 실효 로드를 A4 §3 문서 목록 그대로 기준 A(소스)·기준 B(배포본) 2벌로 재계산한다.
- **완료 기준**: G1/G2/G3 3값 + 파일별 줄수 2벌 + 표 A 행수 + 3홉 노드 전수 목록 + 표본 3건 실효 로드 2벌이 모두 명령 출력과 함께 기재됨. **C5 전후 대조의 "전" 값이 확정**된다.
- **테스트**: 문서에 기재된 명령을 재실행하여 동일 값 재현
- **의존**: 없음

#### Step 2: R-6 — opd 표본 직접 실측 재대조
- [x] 완료
- **파일**: `tasks/087-.../analysis/P1-A4보정-opd표본.md` (신규 1개)
- **agent**: `opal-task-agent`
- **작업 내용**: A3 §4의 opd 6건 중 **080·078·077 3건**을 선정(StepCount ≥ 10 구간이자 C4 대상과 동일 집합)하여, A4 §3과 **동일 절차**(§1.1 과대계상 3요인 · §1.2 홉 정의)로 실효 로드 문서 목록·줄수·홉·발동조건·근거를 표로 작성한다. 그 결과로 `A4-로드사슬.md:151` 잔차("pilot 스코프 차이")를 정량 분해하고, `A4-로드사슬.md:193`(§7 #2)의 `[E]` 항목을 `[M]`/`[D]`로 승격하거나 잔존 사유를 명시한다.
- **완료 기준**: opd 3표본 실효 로드값이 `[M]`/`[D]` 마커와 함께 산출되고, A4 §7 #2 잔차가 **해소(정량 분해 성립) 또는 잔존 사유 명시**로 종결됨. BLUEPRINT §5.1 (1) 포함 ⑥ 충족.
- **테스트**: 각 문서 줄수를 `wc -l`로 재확인, 홉은 근거 줄번호로 역추적 가능
- **의존**: 없음 (Step 1과 병렬)

#### Step 3: R-5 — 비EXECUTE 고정 게이트 48행 건별 판정
- [x] 완료
- **파일**: `tasks/087-.../analysis/P1-C5-게이트판정.md` (신규 1개)
- **agent**: `opal-task-agent`
- **작업 내용**: §2.5 스키마대로 **48행 전건** 판정표를 작성한다. 모집단 근거는 `A3-스폰실측.md:151-157`(비EXECUTE 48행 = opd 6×5 + opds 6×3). 각 행에 대해 게이트 성격·대체 가능성·근거·조치를 기재하고, `조치=삭제` 행은 **삭제 대상 문장의 정확한 경로:줄번호 목록**을 부록으로 산출한다. [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리 — 모델 특성 의존 지시는 `대체불가(플랫폼 의존 위험)`으로 판정하고 유지한다. `state-tool`/`test-tool`/`backlog-tool` 포함 문장은 무조건 `유지(도구 게이트)`로 판정한다.
- **완료 기준**: 표 행수 == 48 AND `대체 가능성` 공란 == 0 AND `근거` 공란 == 0 AND 삭제 대상 목록에 도구 게이트 문장 0건. (→ D-1 §5.1 (2) P1-C5 전반부 "판정 미기재 게이트 == 0")
- **테스트**: `grep -c '^| 0' analysis/P1-C5-게이트판정.md` 로 행수 검산, 삭제 목록을 Step 1의 G1 파일별 내역과 교차 대조
- **의존**: 없음 (Step 1·2와 병렬)

### Phase 1 — 편집 (Step 4~9 · 순차)

#### Step 4: `opal-harness.md` 단일 파일 집중 편집 (R-1·R-2·R-4 stub·R-5)
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md` (수정 1개 — **이 파일의 모든 변경은 본 Step에서 완결한다**)
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. **R-2**: 하네스 모듈 표(표 A, `:99-113`)에 `pm-review-gate.md` 행 1개 추가 → 데이터 행 **11 → 12**. 로드 시점 문구는 `pm-review-gate.md:4` 원문 사용. **표 A에 다른 행을 추가하지 않는다.**
  2. **R-1**: §2에 "규칙 인덱스(직접 참조)" 표 B를 신설하고, Step 1이 확정한 3홉 노드를 전건 등재한다(§2.3 초안 기준). 표 B는 **8~12줄 이내**로 제한한다.
  3. **R-1(C1)**: §2~§10 각 stub의 "적용 주체 / 적용 시점 / PM Gate 검증" 반복 3행을 표 A의 열로 흡수하고 stub 본문을 1~2줄로 축약한다.
  4. **R-4**: §7 병렬 처리 stub에 조건부 분할 배치 SSOT 포인터 1줄 추가(수치 비복제 — 규칙 본문은 Step 6의 `parallel-execution.md` 소유).
  5. **R-5**: Step 3 판정표에서 `조치=삭제`로 판정된 문장 중 이 파일에 속한 것만 삭제한다.
  6. **변경이력** 행 추가: `| v7.0 | 2026-08-09 HH:mm | §2 규칙 인덱스 재편 — 하네스 모듈 표에 pm-review-gate 행 추가(11→12), 규칙 인덱스(직접 참조) 표 신설로 3홉 노드 2홉화, §2~§10 stub 중복 흡수, §7 조건부 분할 배치 포인터 추가 (087) |` (일시는 `node ~/.opal/tools/date/date.js` 로 KST 취득)
- **금지 사항 (위반 시 산출물 부적합)**:
  - [MUST] `opal/core/AGENT.md`를 **열지도 편집하지도 않는다**. 이 파일의 pilot alias·Lazy 트리거 진입 표는 편집 범위 제외다. (→ D-1 §5.1 (4))
  - [MUST] `## 변경이력` 표의 기존 행을 삭제·축약하지 않는다.
  - [MUST] `state-tool`/`test-tool`/`backlog-tool` 호출 지시 문장(§3 state-tool [MUST] 블록의 명령 6행 포함)을 삭제·이관하지 않는다.
  - [MUST] 특정 모델(Opus 5 등) 전제 규칙·플랫폼 조건문을 **신규 추가하지 않는다**. (`docs/CONVENTIONS.md` §플랫폼 분기 격리)
- **완료 기준**:
  - 표 A 데이터 행수 == 12 (C3)
  - 표 B에 Step 1의 3홉 노드 전건 등재 → 해당 노드 최단 경로 == 2홉 (C2)
  - 이 파일의 `run.sh` 호출 행 수 및 본문(변경이력 제외) 도구명 언급 수가 각각 **Step 1 산출 `P1-B0-기준선.md`의 `opal-harness.md` 실측값 이상** (C5). 참고값: 호출 행 6 / 본문 언급 13 — **판정 기준은 Step 1 실측값이다.**
  - `wc -l` ≤ 300 (C1 예산: 330 → 목표 295±5)
  - 변경이력 행 1개 추가 (`docs/CONVENTIONS.md` §변경이력 작성 의무)
- **테스트**: `awk` 표 행수 카운트 + `grep -c` 도구 카운트 + `wc -l` + `git diff --stat`
- **의존**: Step 1, Step 3

#### Step 5: citation-rules 분할 (C1 최대 절감)
- [x] 완료
- **파일**: `opal/core/references/harness/citation-rules.md` (수정), `opal/core/references/harness/citation-rules-planning.md` (신규), `opal/core/references/harness/citation-rules-dev.md` (신규) — **3개**
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. `citation-rules.md:324-416`(§8 비즈니스 용어 우선 원칙, 기획 산출물 전용)을 `citation-rules-planning.md`로 **이동**하고, 원 위치에 조건부 로드 포인터 2~3줄을 남긴다(로드 조건: "기획 산출물(정책서·IA·와이어프레임 등) 작성 시").
  2. `citation-rules.md:133-168`(§2.5 개발 트랙 [MUST] 토큰 6종)과 §1.5의 개발 트랙 전용 서술을 `citation-rules-dev.md`로 이동하고 동일하게 포인터를 남긴다(로드 조건: "개발 트랙 산출물 작성 시").
  3. §3.1/3.2 예시 블록의 중복 예시를 압축한다.
  4. 신규 2파일에 `## 변경이력` 표를 신설하고 초기 행을 기재, `citation-rules.md`에도 변경이력 행 추가 (모두 `(087)`).
  5. 표 A(`opal-harness.md`)는 **건드리지 않는다** — 신규 2파일은 표 A가 아니라 `citation-rules.md` 본문의 조건부 포인터로만 도달한다(2홉 유지, C3 12행 불변).
- **완료 기준**: `wc -l citation-rules.md` ≤ 305 (426 → 목표 −126 이상) AND 신규 2파일 존재 AND `citation-rules.md`에 두 부록의 조건부 로드 포인터가 각 1건 존재 AND 표 A 행수 여전히 12 (C1·C3)
- **테스트**: `wc -l` 3파일 + `grep -n 'citation-rules-\(planning\|dev\)' citation-rules.md` + Step 4 산출물 표 A 행수 재확인
- **의존**: Step 4

#### Step 6: 홉 단축 마무리 + R-4 규칙 본문
- [x] 완료
- **파일**: `opal/core/references/harness/task-process.md`, `opal/skills/op-task/SKILL.md`, `opal/core/references/harness/parallel-execution.md` — **3개**
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. **R-3**: `task-process.md:13-14`의 op-task Read 지시를 제거하고 "op-task/SKILL.md는 `opal-harness.md` §2 규칙 인덱스(직접 참조)에서 로드된다"는 포인터로 대체한다. 채번 규칙(`memory-tool` 명령 행)·저장 경로 규칙은 **원문 보존**. 중복 서술 압축.
  2. **R-3**: `op-task/SKILL.md` 상단 실행 컨텍스트에 2홉 진입 경로를 명시하고 중복 서술을 정리한다. **`state-tool` 호출 지시 행(1건) 보존.**
  3. **R-4**: `parallel-execution.md`에 §2.4의 조건부 분할 배치 규칙 본문(1~5항)을 신설한다. 기본값 = 현행 순차, 발동 = StepCount ≥ 10, 배치 크기 B = 5(하한 4), 산출량 상한 3파일 우선, 동일 파일 순차 편집.
  4. 3파일 모두 변경이력 행 추가 `(087)`.
- **금지 사항**: [MUST] `BLUEPRINT.md` §5.1 (4) — 조건부 규칙에 "기본값 = 현행 순차 배치" 문장이 **명시적으로** 있어야 하며, StepCount < 10 경로의 동작 변경 서술을 넣지 않는다.
- **완료 기준**:
  - `grep -c 'op-task/SKILL.md' task-process.md` 의 결과 중 **Read 지시가 0건**(포인터만 잔존) → op-task 최단 경로 2홉 (C2)
  - `parallel-execution.md`에 "기본값" + "StepCount" + "10" + "B = 5"(또는 배치 크기 5) 4개 토큰 전건 존재 (C4 전제)
  - 3파일 도구 게이트 카운트가 Step 1 기준선 대비 감소 0 (C5)
  - 3파일 변경이력 행 각 1개 추가
- **테스트**: `grep -n` 토큰 확인 + 도구 카운트 재실행 + 홉 재추적(op-task 진입 경로가 표 B 1건뿐인지)
- **의존**: Step 4

#### Step 7: 하네스 모듈 압축 A
- [x] 완료
- **파일**: `opal/core/references/harness/pm-review-gate.md`, `opal/core/references/harness/state.md`, `opal/core/references/harness/state-template.md` — **3개**
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. `pm-review-gate.md`: 헤더 stub의 로드 시점을 표 A 등재 문구와 일치시키고, 하위 3홉 참조(`op-dev-qa/SKILL.md`·`op-task-qa/SKILL.md`·`pm/context-injection.md`·`pm/dispatch-process.md`)를 "표 B 규칙 인덱스 경유" 문구로 정합한다(참조 자체는 유지, 최단 경로는 표 B가 제공).
  2. `state.md`·`state-template.md`: 서술 중복 압축. **`state-tool` 명령 행(각 11건·1건) 및 도구명 언급(26건·5건) 전건 보존.**
  3. 3파일 변경이력 행 추가 `(087)`.
- **완료 기준**:
  - 3파일 합계 `wc -l` ≤ (173+144+114) − 40 = 391 (C1)
  - 3파일 각각의 도구명 언급 수(`## 변경이력` 제외 본문) ≥ **Step 1 산출 `P1-B0-기준선.md`의 해당 파일 실측값** (C5). 참고값(PLAN 작성 시점 사전 실측): `pm-review-gate.md` 5 / `state.md` 26 / `state-template.md` 5 — **판정 기준은 참고값이 아니라 Step 1 실측값이다.**
  - `state.md`의 `run.sh` 호출 행 수 ≥ Step 1 실측값(참고값 11), `state-template.md` ≥ Step 1 실측값(참고값 1), `pm-review-gate.md` ≥ Step 1 실측값(참고값 2)
  - 변경이력 3행 추가
- **테스트**: `wc -l` + 파일별 `grep -c` 도구 카운트
- **의존**: Step 4

#### Step 8: 하네스 모듈 압축 B
- [x] 완료
- **파일**: `opal/core/references/harness/qa-standards.md`, `opal/core/references/harness/observability.md`, `opal/core/references/harness/scenario-gate.md` — **3개**
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. 3파일 서술 중복 압축(C1 예산 각 −10/−10/−15).
  2. `observability.md`의 `opal-loop-action-agent/AGENT.md` 참조가 Step 1 판별에서 **Read 지시**로 분류되었으면 표 B 경유 문구로 정합하고, **단순 인용**이면 인용임을 명시한다(홉 계상 제외 근거 확보).
  3. `scenario-gate.md`의 `test-tool` 언급 8건 전건 보존.
  4. 3파일 변경이력 행 추가 `(087)`.
- **완료 기준**:
  - 3파일 합계 `wc -l` ≤ (76+78+99) − 35 = 218 (C1)
  - 3파일 각각의 도구명 언급 수(본문 한정) ≥ **Step 1 산출 `P1-B0-기준선.md`의 해당 파일 실측값** (C5). 참고값: `scenario-gate.md` 8(전건 `test-tool`) / `qa-standards.md` 2 / `observability.md` 0 — **판정 기준은 Step 1 실측값이다.**
  - 3파일에서 새로 생기는 3홉 노드 0건 (C2)
  - 변경이력 3행 추가
- **테스트**: `wc -l` + `grep -c test-tool` + 홉 재추적
- **의존**: Step 4

#### Step 9: `pm/dispatch-process.md` 포인터 정합
- [x] 완료
- **파일**: `opal/core/references/pm/dispatch-process.md` — **1개**
- **agent**: `opal-task-agent`
- **작업 내용**: Step 6 항목 5(산출량 상한, `:157-160`) 뒤에 조건부 분할 배치 SSOT 포인터 1줄을 추가한다 — "StepCount ≥ 10 구간의 조건부 분할 배치 규칙은 `harness/parallel-execution.md`가 소유한다(본 절은 산출량 상한만 소유하며 배치 크기를 재서술하지 않는다)." 변경이력 행 추가 `(087)`.
- **완료 기준**: 포인터 1줄 존재 AND 배치 크기 수치(B=5)가 이 파일에 **복제되지 않음**(수치 비복제 규율) AND 변경이력 1행 추가
- **테스트**: `grep -n 'parallel-execution' opal/core/references/pm/dispatch-process.md`, `grep -c 'B = 5\|배치 크기' ` == 0
- **의존**: Step 6

### Phase 2 — 재측정 (R-7 · Step 10~11)

#### Step 10: C1·C2·C3·C5 재측정
- [x] 완료
- **파일**: `tasks/087-.../analysis/P1-C-재측정.md` (신규 1개)
- **agent**: `opal-task-agent`
- **작업 내용**: Step 1과 **완전히 동일한 명령**을 재실행하여 전/후 대조표를 만든다.
  ```bash
  cd /Volumes/Data/AiStudio/workspace/opal
  SCOPE="opal/core/references/opal-harness.md opal/core/references/harness opal/skills/op-task/SKILL.md"
  # C5-a G1
  grep -rhoE '~/\.opal/tools/(state-tool|test-tool|backlog-tool)/run\.sh' $SCOPE | wc -l          # 판정: >= 26
  # C5-b G3
  for f in opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md; do
    awk '/^## 변경이력/{exit} {print}' "$f"; done | grep -oE '(state-tool|test-tool|backlog-tool)' | wc -l   # 판정: >= 72
  # C3 표 A 데이터 행수
  sed -n '/^### 하네스 모듈/,/^### /p' opal/core/references/opal-harness.md | grep -c '^| `'      # 판정: == 12
  # C1 파일별 줄수 (기준 A: 소스)
  wc -l opal/core/references/opal-harness.md opal/core/references/harness/*.md opal/skills/op-task/SKILL.md
  ```
  - **C1**: A4 §3의 문서 목록에 편집 후 줄수를 대입해 085/084/083 실효 로드를 재계산한다(기준 A). 신설 부록(N-1/N-2)은 **각 표본의 발동 조건을 A4 §1.1 ②대로 판정**하여 미발동이면 제외한다. 판정: `재측정 3값 전건 ≤ (2,335 / 1,872 / 2,337)` AND `max ≤ 2,000`. 기준 B 값도 병기한다.
  - **C2**: A4 §1.2·§1.3 절차로 홉을 재추적하고 §5 선정 기준(홉 깊이 → 발동 빈도 → 줄수)으로 **Top5를 재선정**한다. 판정: `Top5 홉 평균 ≤ 2.0` AND `op-task/SKILL.md ≤ 2홉`. **3홉 노드가 1건이라도 남으면 평균 2.2로 실패**하므로 잔존 3홉 노드를 0으로 명시 확인한다.
  - **C3**: 판정 `표 A 데이터 행수 == 12` AND `A4 §6 "표 누락(불완전 등재)" 판정 == 0건`.
  - **C5**: 판정 `G1 ≥ 26 AND G3 ≥ 72` AND Step 3 판정표 미기재 == 0.
- **완료 기준**: C1·C2·C3·C5 4개 기준 각각에 대해 **판정식·측정 명령·측정값·Pass/Fail**이 표로 기재됨. 하나라도 Fail이면 `status: blocked` + `decision_required`로 PM 에스컬레이션(임의 재편집 금지).
- **테스트**: 기재된 명령 재실행 시 동일 값 재현
- **의존**: Step 4~9 전건

#### Step 11: C4 K4′ 재집계
- [x] 완료
- **파일**: `tasks/087-.../analysis/P1-C4-재집계.md` (신규 1개)
- **agent**: `opal-task-agent`
- **작업 내용**: A3 §4 동일 표본 12건에 Step 6이 확정한 조건부 분할 배치 규칙을 적용해 K4′를 재집계한다.
  1. 각 표본의 StepCount 재확인: `grep -c '^#### Step' tasks/{080,078,077,075,073,072,085,083,082,081,079,076}-*/PLAN.md`
  2. **미발동 6건(075·073·072·085·081·079)**은 StepCount < 10이므로 **K4 현행값(13·14·12·9·11·8)을 그대로** 사용한다([MUST] `BLUEPRINT.md` §5.1 (4) 하위호환 기본값 규율).
  3. **발동 대상 6건(080·078·077·082·083·076)**은 각 PLAN.md의 Step별 `**파일**` 항목을 읽어 **의존 관계 + 산출 파일 합집합 ≤ 3** 제약 하에 배치를 구성하고 배치 수를 센다. K4′ = 비EXECUTE 행수(+L3) + 배치 수.
     > **각주 — 대상 집합 정정**: `A3-스폰실측.md:173`·`BLUEPRINT.md` §5.1 (2)는 대상을 "7건(075 포함), 139 중 108(77.7%)"으로 인용하나, A3 §5 실측(`:129,141,163-164`)상 075 = StepCount 8로 절단점 미만이다. 실측 우선 원칙에 따라 **6건·EXECUTE 합 96**으로 확정한다(§2.4 D-C, §5 불일치 표 #7).
  4. `opd 평균 = Σ/6`, `opds 평균 = Σ/6`을 계산한다 — 분모는 대상 집합이 아니라 **pilot별 표본 6건 전체**다(§2.4 D-C "판정식 영향: 없음").
- **완료 기준**:
  - `opd K4′ 평균 ≤ 12.0` AND `opds K4′ 평균 ≤ 8.0` (→ D-1 §5.1 (2) P1-C4)
  - 태스크별 배치 구성 근거(Step 묶음·파일 합집합)가 표로 기재됨
  - **BLUEPRINT/A3 인용 집합(7건·108행)과 실측 집합(6건·96행)의 차이가 건별로 확정·기재됨** — 12건 전건에 대해 `StepCount 실측값 / 발동 여부 / A3:173 인용과의 일치 여부`가 표에 기재되고, 075의 배제 근거가 `{경로}:{라인}`으로 인용됨. A3 §5의 EXECUTE 합계 혼용(140 `:151` vs 139 `:165,173`)도 어느 값을 채택했는지 명시함
  - 미달이면 배치 크기 B 상향(≤ 산출량 상한이 허용하는 범위)을 **Step 6 재편집 제안으로 PM에 반환**하고, 임의로 판정식을 완화하지 않는다
- **테스트**: §2.4의 상한 계산값(opd 11.17 / opds 7.83)과 대조 — 실측 K4′는 상한 규칙 때문에 이보다 크거나 같아야 하며, 작으면 계산 오류다
- **의존**: Step 6

### Phase 3 — 상위 SSOT 정오 반영 (R-8 · 캡틴 결정 2026-08-09)

#### Step 12: 086 산출물(A3·BLUEPRINT) 산술 오류 정정
- [x] 완료
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A3-스폰실측.md`, `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` — **2개**
- **agent**: `opal-task-agent`
- **작업 내용**:
  1. **`A3-스폰실측.md:173` 대상 집합·비율 정정** — "표본 12건 중 **7건**: 080·078·077·075·082·083·076" → **6건: 080·078·077·082·083·076**. "전체 EXECUTE 행수 **139 중 108(77.7%)**" → **Step 11 재집계값으로 교체하고 직접 검산하여 기재**한다. 검산 기준값(본 PLAN 사전 계산, Step 11에서 재확인): 대상 6건 StepCount 합 = 14+22+20+16+13+11 = **96**, 분모 139(L3 미포함) → **96/139 = 69.1%**. "StepCount 10 미만 **5건**(073·072·085·081·079)" → **6건(075 포함): 075·073·072·085·081·079**.
  2. **EXECUTE 합계 혼용 해소 (정의 명시 방식 — 어느 쪽도 삭제하지 않는다)** — 같은 문서가 두 값을 무구분 사용하고 있다:
     - **139 = StepCount 합계(L3 보정 미포함)** — `:129`(opd 80) + `:141`(opds 59). 사용처: `:165` 배수 표 "전체 12건 11.58x (139/12)", `:173` 조건부화 기준선 비율.
     - **140 = EXECUTE 행수(L3 보정 포함)** — `:151` "80+59+1(L3, 077 추가행)", `:155` 표 "EXECUTE(+L3 보정) 140 / 74.5%". 사용처: K4 분해·비EXECUTE 48행 대비 비율.
     → 두 값이 처음 등장하는 지점(`:151`·`:165` 인근)에 **정의 각주를 달아** "139 = StepCount 합(L3 미포함), 140 = EXECUTE 행수(L3 1건 보정 포함)"을 명시하고, `:173` 비율이 **139(L3 미포함) 기준**임을 병기한다. L3 포함 기준(97/140 = 69.3%)도 참고로 병기할 수 있으나, **채택 기준은 139**로 단일화한다.
  3. **`BLUEPRINT.md` §5.1 (2) P1-C4 인용 문구 동기화** — "A3 표본 12건 중 7건 = 080·078·077·075·082·083·076, 전체 EXECUTE 행 139 중 108 = 77.7%" 부분을 위 정정값(6건·96·69.1%)으로 교체한다.
     - [MUST] **판정식 본문 `동일 표본 재집계 K4 평균 ≤ 12.0(opd) AND ≤ 8.0(opds)`과 임계값 `12.0`/`8.0`, 목표 배율 서술(`3.1배(18.50/6) → 2.0배 이내(≤12.0)`, `3.2배(12.83/4) → 2.0배 이내(≤8.0)`)은 1자도 변경하지 않는다.** 이번 정정은 **인용 서술의 산술 오류 수정**이지 완료기준 변경이 아니다.
  4. **정오 표기 (양 문서 필수)** — 각 정정 위치 직후에 인용 블록을 붙인다:
     ```
     > **[정오 2026-08-09, 087]** 원 서술 "…" → 정정 "…". 근거: `{경로}:{라인}`
     ```
     원 서술을 반드시 병기한다. 커밋 `4d2115f`로 확정된 문서를 사후 수정하므로 **무엇이 어떻게 바뀌었는지 문서 자체에서 추적 가능**해야 한다. 근거는 `A3-스폰실측.md:129,141,163-164`(075 = StepCount 8, 3곳 일치) 및 `tasks/087-.../analysis/P1-C4-재집계.md`(Step 11 재집계)를 인용한다.
  5. **`tasks/086-.../DONE.md`는 수정하지 않는다** — 완료 기록의 사후 개변 금지. 정오는 A3·BLUEPRINT 본문에만 남긴다.
- **금지 사항**:
  - [MUST] 판정식·임계값·완료기준 수치 변경 0건. 변경 대상은 **대상 집합 서술·합계 수치·비율**에 한정한다.
  - [MUST] 086의 다른 analysis 문서(`A1-중복률.md`·`A2-스키마소요.md`·`A4-로드사슬.md`)와 `BLUEPRINT.md`의 §5.2(P2)·§5.3(P3) 절은 건드리지 않는다.
  - [MUST] `tasks/086-.../DONE.md`·`STATE.md`·`state.json` 무변경.
- **완료 기준**:
  - `A3-스폰실측.md`에서 정정 전 표기 잔재 0건 — `grep -c '7건\|108(77.7\|077·075' tasks/086-*/analysis/A3-스폰실측.md` == 0
  - `A3-스폰실측.md`에 139/140 정의 각주가 각 1건 이상 존재하고, 어느 판정에 쓰이는지 명시됨
  - `BLUEPRINT.md` §5.1 (2) P1-C4의 대상 집합이 실측값(6건·96·69.1%)과 일치
  - `BLUEPRINT.md`의 `12.0`/`8.0` 임계값 문자열 불변 — `git diff tasks/086-*/BLUEPRINT.md`에 임계값 라인의 수치 변경 0건
  - 양 문서에 `[정오 2026-08-09, 087]` 블록 존재 + 원 서술 병기 + `{경로}:{라인}` 근거 인용
  - `git diff --stat tasks/086-*/` 변경 파일이 **정확히 2개**(A3-스폰실측.md, BLUEPRINT.md)
- **테스트**:
  ```bash
  cd /Volumes/Data/AiStudio/workspace/opal
  grep -n '7건\|108\|077·075' tasks/086-*/analysis/A3-스폰실측.md   # 정정 잔재 0건 확인
  grep -n '12\.0\|8\.0' tasks/086-*/BLUEPRINT.md                    # 임계값 불변 확인
  grep -n '\[정오 2026-08-09, 087\]' tasks/086-*/analysis/A3-스폰실측.md tasks/086-*/BLUEPRINT.md
  git diff --stat tasks/086-260809-opp-fw-구조개선-청사진-실측/
  ```
- **의존**: **Step 11** — C4 재집계로 실측 집합이 최종 확정된 뒤에 정정한다. 순서가 뒤바뀌면 재검증되지 않은 값이 상위 SSOT에 들어간다.

### `docs/` 갱신 — EXECUTE 체크리스트 대상 아님 (CLOSE 훅 소유)

`docs/` 관련 문서 최신화는 **별도 Step으로 두지 않는다.** `opal/skills/opal-pilot-project/SKILL.md:123-126`(STEP 4 CLOSE 2항 "관련 문서 업데이트")이 이미 "PROJECT.md 레지스트리 + 이번 태스크의 `changed_files`를 종합해 관련 문서(ARCHITECTURE.md·기획서 등)를 식별하고, 대상이 있으면 PM 판단으로 직접 수정하거나 워커를 디스패치하며, 없으면 자연 스킵(no-op)"으로 소유하고 있다. EXECUTE 체크리스트에 동일 작업을 다시 정의하면 **중복 정의(SSOT 이원화)**가 되고, 하네스 §1 「디스패치 의무 원칙」상 EXECUTE 단계를 PM 직접 실행으로 대체하는 형태가 되어 규칙과도 충돌한다.

- 본 태스크의 `changed_files`에는 `opal/core/references/opal-harness.md`·`harness/*.md`·`opal/skills/op-task/SKILL.md`가 포함되므로, CLOSE 훅이 `docs/ARCHITECTURE.md`·`docs/PROJECT.md`·`docs/CONVENTIONS.md`의 하네스 구조 서술(표 A/표 B 이원화, `citation-rules` 3파일 분할)을 대조 대상으로 식별하게 된다.
- CLOSE 훅에 넘길 대조 힌트(참고용, 본 PLAN이 실행하지 않음): `grep -n 'opal-harness\|citation-rules\|harness/' docs/ARCHITECTURE.md docs/PROJECT.md docs/CONVENTIONS.md`

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] C1: 085/084/083 실효 로드 재측정값이 전건 현행값 이하이고 max ≤ 2,000 (기준 A)
- [ ] C2: 재추적 Top5 홉 평균 ≤ 2.0 AND `op-task/SKILL.md` ≤ 2홉 AND 잔존 3홉 노드 0건
- [ ] C3: 하네스 모듈 표 데이터 행수 == 12 AND "표 누락(불완전 등재)" 판정 0건
- [ ] C4: K4′ 재집계 opd 평균 ≤ 12.0 AND opds 평균 ≤ 8.0
- [ ] C5: 게이트 48행 판정 미기재 0건 AND G1 ≥ 26 AND G3 ≥ 72
- [ ] R-6: A4 §7 #2 잔차가 정량 분해 또는 잔존 사유 명시로 종결
- [x] R-8: `A3-스폰실측.md:173` 대상 집합(7건→6건)·비율(139 중 108 → 96/139 = 69.1%)·미만 건수(5→6) 정정 완료 AND EXECUTE 합계 139/140 정의 각주 신설 AND `BLUEPRINT.md` §5.1 (2) P1-C4 인용 문구 동기화 AND 양 문서에 `[정오 2026-08-09, 087]` 블록 존재

### 일관성 테스트
- [ ] `opal/core/AGENT.md` 변경 0건 (`git diff --stat`으로 확인) — pilot alias 진입점 무중단
- [ ] `opal-harness-{semi-agentic,interactive,agentic}.md` 변경 0건 — 범위 밖
- [ ] `opal/tools/`·`*/pipeline.json`·`state.json` 스키마 변경 0건 — 문서 전용 1커밋 롤백 성립
- [ ] `~/.opal/` 하위 파일 변경 0건 (`docs/CONVENTIONS.md` §배포 경계)
- [ ] 조건부 배치 규칙에 "기본값 = 현행 순차 배치" 명시 존재 AND StepCount < 10 경로 동작 무변경
- [ ] 하네스·스킬 본문에 특정 모델 전제 규칙·플랫폼 조건문 **신규 추가 0건** (`docs/CONVENTIONS.md` §플랫폼 분기 격리)
- [ ] 표 A와 표 B 간 문서 중복 등재 0건 (같은 문서가 두 표에 동시 등장 금지)
- [ ] 수치 SSOT 단일성 — 배치 크기 B가 `parallel-execution.md` 외 파일에 복제되지 않음
- [ ] C4 대상 집합 정정(7건→6건, 108행→96행)이 §5 불일치 표 #7과 Step 11 산출물 양쪽에 근거 인용과 함께 기재됨 — 상위 SSOT 인용치를 조용히 다르게 쓴 곳 0건
- [ ] `docs/` 관련 문서 최신화가 EXECUTE 체크리스트에 중복 정의되지 않음 — 소유는 `opal/skills/opal-pilot-project/SKILL.md:123-126`(CLOSE) 단일
- [ ] 편집 Step의 도구 게이트 완료 기준이 **Step 1 실측값 참조** 형태이며, PLAN 작성 시점 참고값이 판정 기준으로 하드코딩되지 않음
- [ ] **BLUEPRINT 판정식·임계값 변경 0건** — `BLUEPRINT.md` §5.1 (2)의 P1-C1~C5 판정식 본문과 임계값(2,000 / 2.0 / 12행·0건 / 12.0·8.0 / 0건)이 Step 12 정정 후에도 불변 (`git diff tasks/086-*/BLUEPRINT.md`로 확인). P1의 완료기준을 P1 스스로 완화한 흔적 0건
- [ ] Step 12 변경 파일이 정확히 2개(A3·BLUEPRINT) — `tasks/086-.../DONE.md`·`STATE.md`·`state.json`·A1·A2·A4·§5.2·§5.3 무변경

### 문서 품질
- [ ] 변경한 모든 문서에 `## 변경이력` 행 추가, 일시 `YYYY-MM-DD HH:mm`(KST), 내용에 `(087)` 포함
- [ ] 기존 변경이력 행 삭제·축약 0건
- [ ] 신규 2파일(N-1·N-2)에 `## 변경이력` 표 신설
- [ ] analysis 산출물 전건에 `{경로}:{라인}` 인용 및 `[M]`/`[D]`/`[E]` 마커 기재
- [ ] 한국어 본문 + 영어 코드/필드명, kebab-case 파일 네이밍 준수
- [ ] 재측정 산출물에 **재현 가능한 bash 명령**이 그대로 기재됨 (측정 불가 항목 0건)

---

## 5. 리스크 및 대응 · 리스크 가설 표

| ID | 가설(깨질 수 있는 계약) | 영향 | 검증 계층 권고 | 대응 / 시나리오 후보 |
|----|------------------------|------|---------------|---------------------|
| **H-1** | **C1 라인 예산 51줄 부족** — §2.6 예산 합계 −286 < 목표 −337. 소스 기준(기준 A)에서 083/085가 2,000줄을 못 넘길 수 있다 | C1 Fail → P1 완료 불가 | Step 10 실측 | ① 예비 절감 후보 3종 순차 적용 ② 그래도 미달이면 **임의 감축 금지**, `decision_required`로 PM 에스컬레이션. 안건: "A4 줄수가 소스 기준이라 실질 로드를 6~7% 과대계상(`install-mac.sh:207-221` strip) → 기준 B(배포본) 재베이스라인 채택 여부". 기준 B에서는 083=2,176로 −176만 필요해 현 예산으로 충족 |
| **H-2** | **C1 ↔ C2·C3 상충** — 홉 평탄화(표 B 신설)·표 등재(표 A +1행)는 `opal-harness.md` 줄수를 늘려 C1을 압박한다 | C1 여유 잠식 | Step 4 완료 기준(`wc -l` ≤ 300) | 표 B를 8~12줄로 하드캡, stub 흡수(−45)로 순증을 상쇄. Step 4 단독 완료 기준에 줄수 상한을 명시했다 |
| **H-3** | **C4 배치 규칙 ↔ 산출량 상한 3파일 상충** — B=5로 묶어도 배치의 산출 파일 합집합이 3을 넘으면 재분할되어 실효 B가 3으로 붕괴, opd 평균 12.5로 Fail | C4 Fail | Step 11 실측(표본 PLAN.md 파일 집합) | 실효 B는 각 표본의 파일 중첩도에 의존한다. Step 11에서 실측 후 미달이면 B 상향 또는 "동일 파일 Step 묶음 우선" 규칙 강화를 **Step 6 재편집 제안**으로 반환. 판정식 완화 금지 |
| **H-4** | **C5 grep 카운트 정의 미확정** — BLUEPRINT가 집계식을 정의하지 않아 변경이력 서술까지 세면(G2) 정상 편집도 감소로 오판된다 | C5 오탐 | Step 1·Step 10 | 본 PLAN §1.5 (c)에서 **G1 AND G3** 2축으로 운영 정의 확정. G2는 채택하지 않음. 변경이력 축약을 절감 수단에서 명시 배제 |
| **H-5** | **C2 Top5 재선정의 이동 표적** — 기존 3홉 4건을 평탄화해도 미탐지 3홉 노드가 Top5로 승격하면 평균 > 2.0 | C2 Fail | Step 1(전수 조사) → Step 10 | Step 1에서 **3홉+ 전수 조사**를 선행 완료 기준으로 못박음. Step 8에서도 "새로 생기는 3홉 노드 0건"을 완료 기준에 포함 |
| **H-6** | **R-5 삭제가 플랫폼 중립성을 훼손** — Opus 5 자기검증 전제로 산문을 지우면 타 모델(Codex 등)에서 게이트 공백 발생 | 프레임워크 이식성 손상, 되돌리기 어려움 | Step 3 판정표 + Step 10 | 삭제 허용 범위를 **(a) 모델 무관 + 도구 집행 중복분**으로 한정. 모델 의존 판단은 `대체불가(플랫폼 의존 위험)`로 유지 판정만 기재. 하네스 본문 모델 전제 규칙 신규 추가 0건을 QA 일관성 항목으로 검증 |
| **H-7** | **동일 파일 다중 Step 충돌** — 후행 Step의 전체 저장이 선행 편집을 덮어쓴다 | 편집 유실 | Step 구성 검토 | Step 4가 `opal-harness.md` 전 변경을 단독 소유. Phase 1 각 Step의 파일 집합이 비중첩임을 §3 서두에 명시. 워커에 `Write` 대신 `Edit` 사용 지시 |
| **H-8** | **A4/BLUEPRINT 인용 수치와 현재 파일 불일치** | 기준선 오류 | Step 1 | 현재까지 재확인 결과 **330줄·17종·11행·3홉 전건 일치**(§1.5 (b)). 유일한 불일치는 **줄수 계상 기준(소스 vs 배포본)**이며 H-1로 관리 |
| **H-9** | **재배포 미수행으로 런타임 미반영** | 편집 효과가 실사용에 반영 안 됨 | CLOSE 단계 | 재측정은 소스 기준이므로 판정에는 영향 없음. `./scripts/install-mac.sh` 재배포는 **캡틴 지시 시** 수행(커밋 규칙과 동일 게이트) |
| **H-10** | **확정 커밋 문서의 사후 수정이 086 태스크 기록의 무결성을 훼손** — Step 12는 커밋 `4d2115f`로 확정된 A3·BLUEPRINT를 087에서 되돌아가 고친다. 정정 흔적이 남지 않으면 "086이 원래 그렇게 썼다"로 오독되고, 판정식까지 손대면 **P1이 자기 완료기준을 스스로 완화한 것**이 된다 | 근거 추적 단절 · 완료기준 자기완화(중대) | Step 12 완료 기준 + QA 일관성(`git diff`) | ① **정오 블록 병기 의무** — 원 서술을 지우지 않고 `[정오 2026-08-09, 087]` + 원문 + 정정문 + `{경로}:{라인}` 근거를 남긴다 ② **DONE.md·STATE.md·state.json 불가침** — 완료 기록은 개변하지 않는다 ③ **판정식·임계값 변경 0건**을 Step 12 [MUST] 금지 사항 + QA 일관성 항목으로 이중 집행 ④ **의존 순서 강제** — Step 11(재집계) 이후에만 정정하여 재검증되지 않은 값의 유입을 막는다 ⑤ 변경 파일을 정확히 2개로 한정 |

### 문서/코드 불일치 보고 (PM 확인 요청)

| # | 항목 | 문서 서술 | 실제 파일 | 조치 |
|---|------|----------|----------|------|
| 1 | `opal-harness.md` 줄수 | BLUEPRINT §5.1 "330줄" | 330줄 (`wc -l`) | 일치 — 조치 없음 |
| 2 | `harness/` 실파일 | BLUEPRINT §5.1 "17종" | 17개 | 일치 — 조치 없음 |
| 3 | 하네스 모듈 표 데이터 행 | BLUEPRINT §5.1 "11개" | 11개 (`:101-111`) | 일치 — 조치 없음 |
| 4 | `op-task/SKILL.md` 홉·줄수 | A4 §5 "3홉·278줄" | 3홉(`task-process.md:13-14`)·278줄 | 일치 — 조치 없음 |
| 5 | **실효 로드 계상 기준** | A4 §3이 소스 `wc -l` 사용 | 런타임은 배포본 로드, `install-mac.sh:207-221`이 변경이력 strip → 실질 6~7% 적음 | **불일치 — PM 판단 필요**. 본 PLAN은 기준 A(소스)로 판정하되 기준 B를 병기. H-1 참조 |
| 6 | 3홉 노드 개수 | A4 §5는 Top5 4건만 열거 | `pm/dispatch-process.md` 등 **추가 3홉 노드 존재 가능** | **보강 필요** — Step 1에서 전수 조사로 확정. C2 달성의 전제 |
| 7 | **C4 대상 집합·EXECUTE 행 합** | `A3-스폰실측.md:173` 및 이를 인용한 `BLUEPRINT.md` §5.1 (2) P1-C4 — "표본 12건 중 **7건**: 080·078·077·**075**·082·083·076", "전체 EXECUTE 행수 **139 중 108(77.7%)**", "StepCount 10 미만 **5건**(073·072·085·081·079)" | A3 §5 StepCount 실측 기준 **6건: 080(14)·078(22)·077(20)·082(16)·083(13)·076(11)**, EXECUTE 행 합 **96**. 미발동은 **6건**(075·073·072·085·081·079). **075 = StepCount 8**로 절단점(≥10) 미만 — `A3-스폰실측.md:129`(opd `14+22+20+8+9+7`, 순서 080·078·077·075·073·072) · `:141`(opds `6+13+16+8+5+11`) · `:163-164`(배수 표 `opd (7,9,8,20,22,14)` / `opds (11,5,8,16,13,6)`) 3곳 전건 일치. 또한 A3 §5는 EXECUTE 합계를 `:151`에서 **140**, `:165`·`:173`에서 **139**로 혼용 | **실측 우선 채택 + 087 Step 12에서 상위 SSOT 정정(캡틴 승인 2026-08-09)** — 본 PLAN §2.4 D-C·Step 11은 6건·96행으로 계산하고, **Step 12(R-8)가 A3 `:173`과 BLUEPRINT §5.1 (2) 본문을 실측값으로 정정**한다(정오 블록 병기, DONE.md 불가침). **P1-C4 판정식 자체에는 영향 없음**(분모는 pilot별 표본 6건 전체, 임계값 12.0/8.0 불변 — Step 12 금지 사항으로 명문화). Step 11 완료 기준에 "인용 집합 vs 실측 집합 건별 확정·기재"를 편입 |

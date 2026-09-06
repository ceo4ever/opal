# PLAN: 워커 커밋 금지 주입 슬롯화 — 프레임워크 보증 경로 신설

> 작성일: 2026-08-21 | 입력: TASK.md (ANALYSIS.md 없음 — Short Task)
> 모드: Multi-Feature | 실행 모드: 복잡 | 코드 변경 0줄 (전량 Markdown SSOT 개정)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

하네스 §1 Guards가 소유한 커밋 금지 규칙은 워커에게 도달하지 않는다 — 워커는 `[WORKER]` 마커로 부트스트랩을 생략해 하네스를 직접 읽지 않으므로 PM의 디스패치 주입이 유일한 전역 도달점인데, 주입 템플릿(`pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 §핵심 제약)에 해당 슬롯이 없다. 본 태스크는 그 슬롯을 신설(R-1·R-2)하고, 우발적으로 흩어진 복제 경로를 SSOT 포인터로 정리한다(R-3·R-4·R-5).

핵심 구조 사실 3건(실측):
- `pm/dispatch-process.md`는 PM이 **무조건 로드**하는 문서다 — `opal/core/references/opal-pm.md:49`(PM 직접 작업 시 Steps 1~3 실행) · `opal-pm.md:57`("상세 절차(Step 0~7 전체): `opal/core/references/pm/dispatch-process.md` 참조. Lazy 트리거: 워커 디스패치 직전"). 따라서 이 문서에 항목을 넣으면 파일럿 종류와 무관하게 전 디스패치에 도달한다.
- 파일럿 10종은 **전부** 상단에 하네스 폴백 로드 1줄을 보유한다(예: `opal/skills/opal-pilot-dev-short/SKILL.md:14` "부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다"). 즉 파일럿 독자(=PM)의 하네스 도달은 이미 10/10이다.
- 그런데 파일럿 10종 중 `pm/dispatch-process.md`를 참조하는 파일은 **0건**이다(레포 전수 grep — 참조자는 `opal-pm.md`·`opal-harness.md`·`harness/pm-review-gate.md`·`harness/parallel-execution.md`·`pm/asis-analysis.md`·`op-dev-execute/SKILL.md`뿐). 파일럿 → 주입 SSOT 링크 부재가 R-3의 실제 결손이다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 주입 슬롯 신설 — 「전 워커 공통 고정」 3번째 항목 | R-1 | P0 | 없음 |
| F-002 | 주입 템플릿 산문·변경이력 정합 (2항목 → 3항목, 근거 병기) | R-2 | P0 | F-001 (동일 파일·동일 편집 단위) |
| F-003 | 파일럿 10종 주입 지시 편재 해소 — 포인터 일원화 | R-3 | P0 | 없음 |
| F-004 | 단계 스킬 절대 금지 표 보강 + 원격 카운트 복제 제거 | R-4 | P1 | 없음 |
| F-005 | 프로젝트 문서 복제 축약 (CONVENTIONS.md 포인터화 + PROJECT.md 레지스트리 정합) | R-5 | P1 | **F-001** (현행 유일 도달 경로 선제거 금지) |

### 1.3 기능 의존 그래프

```
F-001 ─┬─ F-002  (동일 파일 — 같은 Step에서 처리)
       └─────────────────────────── F-005 (순서 제약: R-1 완료 후에만 적용)

F-003  (독립)
F-004  (독립)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다(`<!-- PENDING-BLOCK-B -->` 자리에 전건 전재).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `pm/dispatch-process.md:94-95` 슬롯 | 「전 워커 공통 고정」 항목 집합이 3건으로 확정되고 `← 전 워커 공통 고정` 표기 행 수가 계약이 된다. 표기 누락 시 PM이 신규 항목을 조건부 항목으로 오독해 문서 선별 결과에 따라 스킵할 수 있다 | P0 | L1(문자열 실측) | S-1, S-3 |
| H-2 | F-002 `pm/dispatch-process.md:115` 각주 | 현행 각주는 "근거 문서가 없는 운영 규율이다"라는 **집합 전체에 대한 단정**이다. 신규 항목은 하네스 §1 파생이므로 문장을 그대로 두고 개수만 3으로 바꾸면 각주가 거짓이 된다 — 항목 성격 2분류 서술이 필수다 | P1 | L1(문자열 실측 + 판독) | S-2, S-3 |
| H-3 | F-002 변경이력 표 | `pm/dispatch-process.md:191`(v1.6 행)에 "전 워커 공통 고정 2항목"이 사실 기록으로 존재한다. R-2 AC를 파일 전역 0건으로 집행하면 과거 사실을 위조하게 되어 변경이력 의무와 충돌한다 | P1 | L1(범위 한정 grep) | S-2 (판정식 보정 필요) |
| H-4 | F-004 `op-dev-execute/SKILL.md:97` | 개수 서술이 **참조 문서 쪽에 원격 복제**되어 있다("전 워커 공통 고정 2항목"). 여기를 고치지 않으면 SSOT는 3항목, 소비자는 2항목으로 즉시 어긋난다 — D-6 §교훈의 재현 | P0 | L1(문자열 실측) | S-2 확장 / 신규 후보 S-2b |
| H-5 | F-003 파일럿 10종 | 파일럿의 `[PM 컨텍스트 주입]` 블록은 **PM 대상 지시**이고 워커 대상 프롬프트 본문이 아니다. 이를 워커 전달 경로로 오인해 항목을 10곳에 열거하면 동일 문언 10복제가 고착된다 | P1 | L2(전 문서 집합 대조) | S-5, S-6 |
| H-6 | F-003 `opal-pilot-gc/SKILL.md:219` | gc는 `[MUST] 커밋 금지 (git commit 호출 금지)`를 **디스패치 프롬프트 리터럴 본문**에 이미 보유한다. 이는 규범 복제가 아니라 주입 산출물 자체다 — "단일 형태 통일" AC를 층 구분 없이 적용하면 유효한 방어를 제거한다 | P1 | L2(층 구분 판독) | S-6 |
| H-7 | F-005 `docs/CONVENTIONS.md` | 커밋 금지 원문이 **2곳**에 있다 — `:203`(§구현 규칙 §Guards)과 `:188`(§커밋 규칙 §규칙 "커밋은 캡틴이 명시적으로 요청할 때만 수행"). TASK.md는 `:203`만 지목했으므로 `:188`을 놓치면 AC(a) "원문 서술 0건"이 미충족된다 | P0 | L1(전수 grep) | S-8 |
| H-8 | F-005 `docs/PROJECT.md:223` | 레지스트리 행의 용도 서술이 "커밋 규칙, 구현 규칙(Guards/...)"으로 CONVENTIONS.md의 Guards 원문 보유를 전제한다. 포인터화 후 이 행을 방치하면 SSOT 간 내부 모순이 남는다 | P1 | L2(교차 판독) | S-10 |
| H-9 | F-005 순서 | R-5를 R-1보다 먼저 적용하면 **커밋 금지 도달 경로가 일시적으로 0개**가 된다(하네스는 워커 미독, 주입 슬롯 미신설, 컨벤션 원문 제거 완료 상태) | P0 | L2(Phase 배치 검사) | S-12 |
| H-10 | 전 변경 | `pm/dispatch-process.md`·`docs/CONVENTIONS.md`·`opal-pilot-gc/SKILL.md`는 기존 도구 테스트가 실제로 읽는 파일이다 — `opal/tools/worktree-tool/tests/test_worktree_tool.py:669-672`, `opal/tools/code-scan/tests/test-regression.js:325,731,733`, `opal/tools/memory-tool/tests/test_memory_tool.py:2578`. 편집 구간이 어긋나면 무관한 테스트가 깨진다 | P1 | L2(회귀 실행) | S-16 |
| H-11 | 전 변경 | 배포본(`~/.opal/`)과 소스가 이원화된 상태다. 소스만 고치면 이번 세션의 PM/워커 런타임에는 규칙이 적용되지 않는다(install 미실행) — "적용됐다"는 오판정 위험 | P1 | L1(배포본 diff 부정 검증) | S-13 |
| H-12 | 전 변경 | 스킬·참조 문서 수정 시 변경이력 행 추가가 의무다(D-2 §금지사항). 12개 파일 × 행 추가를 누락하면 컨벤션 위반으로 산출물 부적합 | P2 | L1(변경이력 존재 검사) | S-4 확장 |

---

## 2. 기능별 분석

### F-001: 주입 슬롯 신설

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 + 워커 컨텍스트 주입 템플릿 SSOT | 수정 |
| 가이드 | `opal/core/references/opal-harness.md` | 커밋 규칙 SSOT (§1 Guards) — 읽기만 | 무변경 |
| 가이드 | `opal/core/references/opal-pm.md` | 위 문서의 무조건 로드 지점 — 읽기만 | 무변경 |

#### 2.1.2 현재 구현
`pm/dispatch-process.md:91-97` §핵심 제약 코드블록:
```
- [MUST] <문서명> §N: <규칙 원문>  ← 원문 인용 필수 항목
- [MUST] CONVENTIONS.md §N: <컨벤션 강제 규칙 원문>  ← 컨벤션 [MUST]/금지/네이밍 (해당 시)
- [MUST] 증분 저장: ...  ← 전 워커 공통 고정
- [MUST] 입력 축소: ...  ← 전 워커 공통 고정
- {선호사항 또는 가이드라인}: {설명}  ← 요약 허용 항목
```
`← 전 워커 공통 고정` 표기 행이 **2개**(`:94`, `:95`)다. 규칙 SSOT는 `opal/core/references/opal-harness.md:42` — "**커밋은 사용자가 명시적으로 요청할 때만 수행한다.** EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다. 완료 보고만 하고 사용자 지시를 기다린다."

#### 2.1.3 영향 범위
- 상위 소비자: PM(`opal-pm.md:49`,`:57` 무조건 로드) → 전 파일럿 전 디스패치.
- 하위 파생: `op-dev-execute/SKILL.md:97`이 이 절을 SSOT로 지목(원격 카운트 보유 → F-004에서 동시 처리).
- 테스트 의존: `opal/tools/worktree-tool/tests/test_worktree_tool.py:669-672`가 이 파일에서 `## 작업 경로`·`절대경로` 문자열 존재를 검사(§워커 컨텍스트 주입 템플릿 `:101-105` 블록). 본 변경은 `:94-95`·`:115`·변경이력만 건드리므로 미영향 — 단 회귀 실행으로 실증한다.

---

### F-002: 주입 템플릿 산문·변경이력 정합

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/pm/dispatch-process.md` | `:115` 각주 + `:181-192` 변경이력 표 | 수정 |

#### 2.2.2 현재 구현
`:115` 각주 원문(1문장에 4개 주장이 결합):
> **전 워커 공통 고정 2항목**(증분 저장 · 입력 축소)은 Step 2 문서 선별 결과와 무관하게 **모든 워커 디스패치에 항상 포함**한다 — 문서에서 추출한 [MUST]와 달리 근거 문서가 없는 운영 규율이다. 워커가 중단되더라도 직전 완결 산출물까지 보존되게 하는 것이 목적이며, 단계 스킬은 이 문언을 복제하지 않고 본 템플릿을 참조한다. 근거: `tasks/078-...` §8, `tasks/079-...` §8.

"근거 문서가 없는 운영 규율이다"는 **집합 전체에 대한 단정**이다(H-2). 신규 항목은 하네스 §1 파생이므로 개수만 교체하면 문장이 거짓이 된다.

변경이력 표 최신 행: `:192` `| v1.7 | 2026-08-15 16:16 | ... (092) |` → 신규 v1.8 행 추가.

#### 2.2.3 영향 범위
`:191`(v1.6 행)이 "전 워커 공통 고정 2항목"을 **사실 기록**으로 보유(H-3). 변경이력은 시점 기록이므로 개정 대상이 아니다 — R-2 AC 판정 범위를 규범 서술 구간으로 한정해야 한다(§3.2.2 결정).

---

### F-003: 파일럿 10종 주입 지시 편재 해소

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | opd — `:203` 축약형 1건 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds — `:49` 열거형, `:152` 축약형 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw — `:81` 열거형 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project/SKILL.md` | opp — `:63` 열거형, `:87` 축약형 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd — 블록 부재, `:399`·`:506`·`:407` harness_guards 파라미터 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl — 블록 부재, `:362` 디스패치 idiom 절 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt — `:221`·`:317`·`:344` 축약형 3건 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd — 블록 부재, `:114`·`:180` 프롬프트 리터럴 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-gc/SKILL.md` | opgc — 블록 부재, `:219` 프롬프트 리터럴에 커밋 금지 보유 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-data-design/SKILL.md` | opdd — 블록 부재, `:106` 프롬프트 리터럴 | 수정 |

#### 2.3.2 현재 구현 — 실측 3형태

| 형태 | 문언 | 보유 파일럿 |
|------|------|-----------|
| A. 열거형 (3항목 리스트, "1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, **커밋 규칙**)" 포함) | `dev-short:49-52`, `dev-wireframe:81-84`, `project:63-66` | 3종 |
| B. 축약형 ("하네스 Guards 핵심 규칙 + ..." — 커밋 미명시) | `dev:203`, `dev-short:152`, `project:87`, `write-tech:221·317·344` | 4종(중복 포함 6건) |
| C. 블록 부재 (프롬프트 리터럴에 `**하네스 Guards**:` 필드만) | `project-dev`, `project-loop`, `sdd`, `gc`, `data-design` | 5종 |

형태 C 리터럴 실측:
- `sdd:114-121` — `**하네스 Guards**: 구현 금지. SPEC.md 외 파일 생성 금지.` + `**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식...}` ← **핵심 제약 필드가 이미 주입 템플릿 계약을 참조**한다
- `data-design:106` — `**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지...` (핵심 제약 필드 없음)
- `project-dev:407` — `harness_guards: "PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지..."`
- `gc:219` — `- [MUST] 커밋 금지 (git commit 호출 금지)` ← 유일하게 커밋 금지를 리터럴 보유

#### 2.3.3 영향 범위
- 파일럿 SKILL.md의 독자는 항상 PM이다(파일럿은 오케스트레이터 스킬이며 워커가 로드하지 않는다). PM은 부트스트랩으로 `opal-pm.md`를 로드하고 `:57`이 `pm/dispatch-process.md`를 디스패치 직전 Lazy 로드로 지정한다 → 파일럿의 `[PM 컨텍스트 주입]` 블록은 **리마인더**이고 전달 기제가 아니다(H-5).
- `opal/tools/memory-tool/tests/test_memory_tool.py:2578`이 `opal/skills/opal-pilot-gc/SKILL.md` 경로를 참조 무결성 검사 대상으로 보유 — 경로 존재만 검사하며 본문 미검사(무영향, 회귀로 실증).
- 워커 정의 계층 참고: 액션·체커 6종은 커밋 금지를 자체 보유(`opal/agents/opal-loop-action-agent/AGENT.md:354` "커밋하지 않는다 — PM이 머지/커밋을 관리한다", `opal-task-action-agent/AGENT.md:249·261`, `opal-sdd-action-agent/AGENT.md:122·252`)이나 코드 변경 4종(`opal-be-agent`·`opal-fe-agent`·`opal-db-agent`·`opal-task-agent`)은 "커밋" 문자열 **0건**이다. 이 결손은 F-001의 주입 슬롯이 전 디스패치에 항목을 실어 보냄으로써 해소되며, AGENT.md 개정은 본 태스크 범위가 아니다(§9 R-3 참조).

---

### F-004: 단계 스킬 절대 금지 표 보강 + 원격 카운트 복제 제거

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 단계 스킬 — `:108-115` 절대 금지 표(6행), `:97` 원격 카운트, `:200-210` 변경이력 | 수정 |

#### 2.4.2 현재 구현
`:106-115` §가드레일 §절대 금지 표 — 컬럼 `# | 금지 행동 | 이유`, 6행(#1 PLAN 외 파일, #2 설계 임의 변경, #3 영역 침범, #4 미승인 패키지, #5 시크릿 하드코딩, #6 RED 테스트 수정). git 관련 행은 없다.
`:97` — "산출물 저장 시점·입력 축소 규율 자체의 SSOT는 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 §핵심 제약**(전 워커 공통 고정 2항목)**이며, 본 스킬은 이를 복제하지 않는다."

#### 2.4.3 영향 범위
이 파일은 op-dev-execute를 로드하는 전 워커(be/fe/db/task 4종 + 액션 에이전트)가 직접 Read하는 경로다 → 주입(F-001)과 독립된 **이중 방어**. `:97`은 카운트 원격 복제로 F-001 적용 즉시 어긋난다(H-4).

---

### F-005: 프로젝트 문서 복제 축약

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `docs/CONVENTIONS.md` | `:188` §커밋 규칙 §규칙, `:203` §구현 규칙 §Guards, `:270-280` 변경이력 | 수정 |
| 문서 | `docs/PROJECT.md` | `:223` 문서 레지스트리 CONVENTIONS.md 행, `:258-` 변경이력 | 수정 |

#### 2.5.2 현재 구현 — 복제 2곳(실측)
- `docs/CONVENTIONS.md:188` (§커밋 규칙 → §규칙, 4 bullet 중 첫째): `- 커밋은 캡틴이 명시적으로 요청할 때만 수행`
- `docs/CONVENTIONS.md:203` (§구현 규칙 → §Guards): `- 커밋은 사용자가 명시적으로 요청할 때만 수행한다 — EXECUTE 완료·DONE.md 생성·테스트 통과 후에도 자동 커밋 금지.` (`:204`에 이미 `- 근거: opal/core/references/opal-harness.md §1 Guards` 보유)
- `docs/PROJECT.md:223`: `| docs/CONVENTIONS.md | 코드 및 문서 컨벤션 | 네이밍, 파일 구조, 커밋 규칙, 구현 규칙(Guards/디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기) | Framework | 개발 작업 시 항상 |`

규범 근거 — CONVENTIONS.md는 코드 컨벤션 문서이고 그 §커밋 규칙은 메시지 형식·단위를 뜻한다:
- `[MUST]` `opal/skills/opal-project-init/references/docs-guide.md` §docs/CONVENTIONS.md — 코드 컨벤션: "코드 작성 시 따라야 할 규칙. 워커가 코드를 쓸 때 직접 참조한다."
- `[MUST]` `opal/skills/opal-project-init/references/docs-guide.md` §구조 템플릿: "## 커밋 규칙 / {커밋 메시지 형식, 단위}"

#### 2.5.3 영향 범위
- `opal/agents/opal-convention-checker/AGENT.md:17`("이 에이전트는 규칙을 내장하지 않는다. 모든 컨벤션 규칙은 반드시 `docs/CONVENTIONS.md`에서만 로드한다")·`:60`(섹션별 규칙 파싱)은 **섹션 일반 파싱**이며 §Guards의 커밋 bullet을 하드코딩하지 않는다 → 무영향.
- `opal/tools/code-scan/tests/test-regression.js:325,731,733`이 `docs/CONVENTIONS.md` §@header 규칙 본문을 검사한다. 본 변경은 §커밋 규칙·§Guards만 건드림 → 미영향(회귀로 실증).
- CONVENTIONS.md는 「개발 작업 시 항상」 로드 문서(`docs/PROJECT.md:223`)이므로, 원문 제거 후에도 포인터가 남아 PM의 하네스 도달은 유지된다. 워커 도달은 F-001이 담당한다.

---

## 3. 기능별 설계

### F-001: 주입 슬롯 신설

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/pm/dispatch-process.md` | 가이드 | §워커 컨텍스트 주입 템플릿 §핵심 제약 코드블록의 `:95` 직후에 `← 전 워커 공통 고정` 표기 신규 1행 삽입 | `opal/core/references/pm/dispatch-process.md:94-95` |

#### 3.1.2 설계 — 신규 항목 문언 확정 (설계 쟁점 4)

삽입 위치: `:95` 다음 행(공통 고정 3항목을 연속 배치, `{선호사항...}` 행보다 위).

**확정 문언**(1행, 기존 2항목과 동일 형식 `- [MUST] <제목>: <내용>  ← 전 워커 공통 고정`):

```
- [MUST] git 이력 변경 금지: `git commit`·`git push`·`git reset`·`git rebase`를 실행하지 않는다. 변경은 워킹트리에 남기고 완료 보고한다. 커밋·머지는 소유자 권한이다(규칙 SSOT: `opal/core/references/opal-harness.md` §1 커밋 규칙).  ← 전 워커 공통 고정
```

**금지 서브명령 범위 결정 — commit/push에 reset·rebase를 포함한다.** 근거 3건:
1. `[MUST]` `opal/core/references/opal-harness.md` §1 커밋 규칙: "**커밋은 사용자가 명시적으로 요청할 때만 수행한다.** EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다. 완료 보고만 하고 사용자 지시를 기다린다." → commit 금지가 SSOT 직접 파생. push는 commit 없이는 성립하지 않으나 이미 커밋된 이력의 원격 반영도 소유자 결정 사안이므로 병기한다.
2. `[MUST]` `opal/core/references/harness/pm-review-gate.md:21` §워커 중단 시 산출물 실측 판정: "**산출물 확정** — `git status --short`와 `git diff --stat`으로 실제 생성·수정된 파일을 확정한다. 판정 근거는 워커 반환 텍스트가 아니라 워킹트리다." → **워킹트리가 PM 판정의 유일한 증거 입력**이다. 워커가 `commit`하면 증거가 워킹트리에서 사라지고, `reset`하면 증거가 파괴된다. 따라서 이력을 되돌리는 `reset`·`rebase`는 commit과 동일 위험군이다.
3. `opal/core/references/opal-harness.md:21` §Git 사전 점검: "**커밋되지 않은 변경**: 사용자에게 커밋/스태시를 제안한 후 진행" → 미커밋 상태는 사용자 결정 표면이며 워커가 임의 해소할 대상이 아니다.

**제외 결정**: `git add`·`stash`·`checkout`/`switch`·`branch`는 열거하지 않는다 — (a) `add`는 워킹트리 내용을 파괴하지 않고 PM의 `git status --short` 판정에 그대로 노출된다, (b) `stash`·`checkout`은 worktree 격리 태스크에서 정당 용도가 있을 수 있어 전면 금지 시 과잉 차단이 된다, (c) 열거를 늘리면 항목이 규칙에서 목록으로 변질되어 D-6 §교훈(열거 고착)을 재현한다. 대신 제목 "git 이력 변경 금지"가 범주를 규정하므로 미열거 이력 변경 명령도 제목 해석으로 포섭된다.

**형식 준수 확인**: `- [MUST] ` 접두 + `<제목>: ` + 내용 + `  ← 전 워커 공통 고정`(2공백 + 화살표) — `:94`·`:95`와 동일. 백틱 코드 스팬으로 서브명령 표기(citation-rules.md §2 코드 근거 관행과 충돌 없음).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음. **install 미실행** — 배포본(`~/.opal/`)은 본 태스크에서 갱신하지 않는다. `[MUST]` `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (표기 행 3개) | 산출물 검사 | `grep -c '← 전 워커 공통 고정' opal/core/references/pm/dispatch-process.md` == 3 (S-1) |
| TS-002 | R-1 AC (commit·push 금지 + 워킹트리 보존) | 산출물 검사 | 신규 행에 `git commit`·`git push`·`git reset`·`git rebase`와 "워킹트리에 남기고 완료 보고" 문구가 모두 존재 (S-1) |
| TS-003 | R-2 AC (근거 병기) | 산출물 검사 | 신규 행에 `opal-harness.md` §1 포인터 존재 (S-3) |

---

### F-002: 주입 템플릿 산문·변경이력 정합

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/pm/dispatch-process.md` | 가이드 | `:115` 각주를 3항목 + 성격 2분류 구조로 재작성 | `opal/core/references/pm/dispatch-process.md:115` |
| 2 | `opal/core/references/pm/dispatch-process.md` | 가이드 | 변경이력 표에 v1.8 행 추가 (`:192` 다음) | `[MUST]` `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무." |

#### 3.2.2 설계 — 각주 재작성 + AC 판정 범위 확정 (설계 쟁점 2 인접 / H-2·H-3)

`:115` 교체안(단일 문장 → 헤드 1문장 + 성격별 2 bullet):

```
> **전 워커 공통 고정 3항목**(증분 저장 · 입력 축소 · git 이력 변경 금지)은 Step 2 문서 선별 결과와 무관하게 **모든 워커 디스패치에 항상 포함**한다 — 문서에서 추출한 [MUST]와 달리 문서 선별 경로를 타지 않는다. 단계 스킬은 이 문언을 복제하지 않고 본 템플릿을 참조한다.
> - **증분 저장 · 입력 축소** — 근거 문서가 없는 운영 규율이다. 워커가 중단되더라도 직전 완결 산출물까지 보존되게 하는 것이 목적이다. 근거: `tasks/078-260728-opd-메모리-json전환/DONE.md` §8(완화 조합 도출 후 전량 성공), `tasks/079-260730-opds-히스토리-정정명령/DONE.md` §8(선제 적용 → 인프라 실패 0건).
> - **git 이력 변경 금지** — 규칙 SSOT는 `opal/core/references/opal-harness.md` §1 커밋 규칙이며 본 항목은 그 **워커 도달 경로**다. 워커는 `[WORKER]` 마커로 부트스트랩을 생략해 하네스를 직접 읽지 않으므로(`~/.opal/AGENT.md` §부트스트랩 §[WORKER 규칙]) 주입이 유일한 전역 도달점이다. 워킹트리 보존은 `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정의 입력 조건이기도 하다.
```

이 구조가 H-2를 해소한다 — "근거 문서가 없는 운영 규율"이라는 단정을 해당 2항목으로 한정하고, 신규 항목에는 SSOT 포인터를 병기한다(R-2 AC "신규 항목의 근거를 하네스 §1 포인터로 병기" 충족).

**AC 판정 범위 확정 (H-3 — R-2 AC 문면 보정)**: R-2 AC 문면은 "파일 내 「공통 고정 2항목」 문자열이 0건"이나, `:191`(v1.6 변경이력 행)은 2026-08-02 시점에 실제로 2항목을 추가했다는 **사실 기록**이다. 이를 지우면 `.opal/AGENT.md` §금지사항 변경이력 의무의 취지(시점 기록 보존)를 위반한다. 따라서 판정식을 다음으로 확정한다:

| 판정 항목 | 집행식 | 기대 |
|----------|--------|------|
| 규범 서술 구간에 구 표현 0건 | `awk 'NR>=81 && NR<=180' <file> \| grep -c '공통 고정 2항목'` | 0 |
| 신 표현 존재 | `grep -c '공통 고정 3항목' <file>` | >= 1 |
| 변경이력 구간의 사실 기록 보존 | `sed -n '/^## 변경이력/,$p' <file> \| grep -c '공통 고정 2항목'` | 1 (v1.6 행 — 유지) |

> TEST-SCENARIO.md S-2의 판정식이 파일 전역 0건으로 작성될 경우 위 3행 판정식으로 보정해야 한다 (PM 보강 시 반영 대상).

변경이력 v1.8 행 문안:
```
| v1.8 | 2026-08-21 {HH:MM} | §워커 컨텍스트 주입 템플릿 §핵심 제약에 전 워커 공통 고정 **3번째 항목** "git 이력 변경 금지"(commit·push·reset·rebase 실행 금지 + 워킹트리 보존·완료 보고) 신설 — 워커는 `[WORKER]` 마커로 부트스트랩을 생략해 하네스를 직접 읽지 않으므로 주입이 유일한 전역 도달점이다. 규칙 SSOT는 `opal-harness.md` §1 커밋 규칙이며 본 항목은 도달 경로일 뿐 규칙을 재정의하지 않는다. §115 각주를 2항목 → 3항목으로 갱신하고 항목 성격을 2분류(운영 규율 2건 / 하네스 파생 1건)로 분해 (097) |
```

#### 3.2.3 환경 변경 / 3.2.4 배치·마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-2 AC (2항목 0건) | 산출물 검사 | 규범 구간(81~180행) `공통 고정 2항목` 0건 (S-2, 보정 판정식) |
| TS-005 | R-2 AC (3항목 1건 이상) | 산출물 검사 | `공통 고정 3항목` >= 1건 (S-2) |
| TS-006 | R-2 AC (변경이력 097 행) | 산출물 검사 | 변경이력 표에 `(097)` 행 1건 존재 (S-4) |
| TS-007 | H-3 | 회귀 테스트 | 변경이력 구간의 v1.6 행 `공통 고정 2항목` 기록 1건 보존 (S-4 확장) |

---

### F-003: 파일럿 10종 주입 지시 편재 해소

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | `:203` 축약형 → 정규 포인터형 교체 + 변경이력 행 | `opal/skills/opal-pilot-dev/SKILL.md:203` |
| 2 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 오케스트레이터 | `:49-52` 열거형 → 정규 포인터형(4행 → 1행), `:152` 축약형 → 정규형 + 변경이력 행 | `opal/skills/opal-pilot-dev-short/SKILL.md:49-52,152` |
| 3 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 오케스트레이터 | `:81-84` 열거형 → 정규 포인터형 + 변경이력 행 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:81-84` |
| 4 | `opal/skills/opal-pilot-project/SKILL.md` | 오케스트레이터 | `:63-66` 열거형 → 정규형, `:87` 축약형 → 정규형 + 변경이력 행 | `opal/skills/opal-pilot-project/SKILL.md:63-66,87` |
| 5 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 오케스트레이터 | Phase 3 첫 디스패치 절(`:397` 인접)에 정규 포인터 블록 신설 + 변경이력 행 | `opal/skills/opal-pilot-project-dev/SKILL.md:397-407` |
| 6 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | `:362` 디스패치 idiom 절에 정규 포인터 블록 신설 + 변경이력 행 | `opal/skills/opal-pilot-project-loop/SKILL.md:362` |
| 7 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 오케스트레이터 | `:221`·`:317`·`:344` 축약형 3건 → 정규형 + 변경이력 행 | `opal/skills/opal-pilot-write-tech/SKILL.md:221,317,344` |
| 8 | `opal/skills/opal-pilot-sdd/SKILL.md` | 오케스트레이터 | Phase 1 첫 디스패치 절(`:110` 인접)에 정규 포인터 블록 신설 + 변경이력 행 | `opal/skills/opal-pilot-sdd/SKILL.md:110-121` |
| 9 | `opal/skills/opal-pilot-gc/SKILL.md` | 오케스트레이터 | §2.3 병렬 디스패치 프롬프트 템플릿(`:207` 인접) 직전에 정규 포인터 블록 신설 + 변경이력 행. `:219` 리터럴은 **유지** | `opal/skills/opal-pilot-gc/SKILL.md:207,219` |
| 10 | `opal/skills/opal-pilot-data-design/SKILL.md` | 오케스트레이터 | 첫 디스패치 절(`:94` 인접)에 정규 포인터 블록 신설 + 변경이력 행 | `opal/skills/opal-pilot-data-design/SKILL.md:94-106` |

#### 3.3.2 설계 — R-3 방식 택일 (설계 쟁점 1)

**결정: (b) 포인터 일원화를 채택한다.**

**정규 문언 (10종 공통, 1행)**:
```
> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.
```
- 단계별 고유 payload가 있는 지점은 문말에 ` 단계 추가 전달: <payload>`만 덧붙인다. 예: `dev:203`·`dev-short:152` → ` 단계 추가 전달: TEST-SCENARIO.md 경로 · changed_files.` (기존 정보 손실 0)
- bullet 표기를 쓰는 파일(`write-tech`)은 `> ` 대신 `- ` 접두를 유지한다 — 문서 내 리스트 구조 보존이며 문언 자체는 동일하다.

**근거 4건**:
1. `[MUST]` `.opal/AGENT.md` §업무 수행 지침: "하네스 변경 시: `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다." → (a)안은 하네스 §1 규칙을 10곳에 발췌하는 행위다.
2. `tasks/094-260815-opd-STATE-저널화/DONE.md` §교훈 — SSOT 값을 산문에 복제하면 필연적으로 어긋나며, 구조적 해법은 **열거 제거 + 포인터 대체**다. 본 태스크는 그 교훈이 이미 실현된 실패를 발견했다: `op-dev-execute/SKILL.md:97`이 항목 **개수**를 원격 복제해 F-001 적용 즉시 어긋난다(H-4). 열거 대상이 규칙 원문이면 어긋남 폭은 더 크다.
3. **도달 보장 상충의 해소** — (b)안의 우려는 "파일럿 SKILL만 읽는 경로에서 한 단계 우회"다. 실측상 그 경로는 존재하지 않는다: 파일럿 SKILL.md의 독자는 항상 PM이고, PM은 부트스트랩에서 `opal-pm.md`를 로드하며 `opal-pm.md:57`이 "상세 절차(Step 0~7 전체): `opal/core/references/pm/dispatch-process.md` 참조. **Lazy 트리거: 워커 디스패치 직전**"으로 무조건 로드를 지정한다. 즉 파일럿을 읽는 시점에 주입 템플릿은 이미 로드 예정 문서다 — 실질 hop 증가는 0이다. 반대로 (a)안은 파일럿 열거와 템플릿 본문이 어긋날 때 **어느 쪽이 유효한지 판정 불가**한 상태를 만든다.
4. `.opal/brain/pages/concept/anchor-load-condition-must-match-target.md` — 규칙은 **무조건 로드되는 문서**에 두고 조건부 문서에는 참조 1줄만 남긴다는 이미 승격된 프레임워크 설계 원칙. `pm/dispatch-process.md`는 무조건 로드(근거 3), 파일럿 SKILL.md는 조건부 로드(선택된 1종만) → 규칙의 자리는 전자다.

**부수 효과(의도된 개선)**: 파일럿 → 주입 SSOT 참조가 0건 → 10건이 되어, 현재 끊겨 있는 파일럿-주입 링크가 처음으로 문서화된다. 이는 (a)안으로는 얻을 수 없다.

**"단일 형태" 정의 (H-6 — 층 구분)**: 통일 대상은 **PM 대상 지시 층**(`[PM 컨텍스트 주입]` 블록)이다. `gc:219`의 `- [MUST] 커밋 금지 (git commit 호출 금지)`는 **워커에게 전달되는 프롬프트 리터럴 본문**, 즉 주입의 산출물이지 규범 복제가 아니다 → 존치한다. 동일하게 `sdd:114·180`·`data-design:106`·`project-dev:407`의 `**하네스 Guards**:` / `harness_guards:` 필드는 **단계 고유 가드**(예: "SPEC.md 외 파일 생성 금지")이므로 본 태스크에서 재작성하지 않는다. S-6 판정은 `[PM 컨텍스트 주입]` 블록의 형태 동일성으로 한정한다.

**변경이력 행 문안 (10종 공통 골자)**:
```
| v{다음} | 2026-08-21 {HH:MM} | §[PM 컨텍스트 주입] 블록을 `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 포인터로 일원화 — 주입 항목 열거(하네스 Guards·참조 문서·기술 스택 3항목)를 제거하고 SSOT 참조 1줄로 대체. 전 워커 공통 고정(git 이력 변경 금지 포함)이 파일럿 종류와 무관하게 도달하도록 함 (097) |
```
(블록 신설 파일럿은 "열거를 제거하고" → "주입 SSOT 참조 블록을 신설하고"로 조정)

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-3 AC (10종 전부 보유) | 통합 테스트 | `grep -l 'pm/dispatch-process.md' opal/skills/opal-pilot-*/SKILL.md \| wc -l` == 10 (S-5) |
| TS-009 | R-3 AC (단일 형태) | 통합 테스트 | 전 파일럿의 `[PM 컨텍스트 주입]` 블록이 정규 문언 패턴 1종만 매치하고, 열거형 잔존(`1. 하네스 Guards 핵심 규칙`) 0건 (S-6) |
| TS-010 | H-6 | 회귀 테스트 | `opal-pilot-gc/SKILL.md`의 `[MUST] 커밋 금지 (git commit 호출 금지)` 리터럴 1건 보존 (S-6 보조) |
| TS-011 | H-12 | 산출물 검사 | 파일럿 10종 전부 변경이력 표에 `(097)` 행 1건 (S-4 확장) |

---

### F-004: 단계 스킬 절대 금지 표 보강

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | §절대 금지 표에 #7 행 추가 (6행 → 7행) | `opal/skills/op-dev-execute/SKILL.md:108-115` |
| 2 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | `:97` 원격 카운트 "(전 워커 공통 고정 2항목)" → "(전 워커 공통 고정 항목)" — 개수 제거 | H-4, D-6 §교훈 |
| 3 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | 변경이력 v2.5 행 추가 | `[MUST]` `.opal/AGENT.md` §금지사항 변경이력 의무 |

#### 3.4.2 설계

**신규 표 행 (#7)**:
```
| 7 | `git commit`·`git push`·`git reset`·`git rebase` 실행 | 커밋·머지는 소유자 권한 — 자동 커밋 금지(`opal/core/references/opal-harness.md` §1 커밋 규칙). 변경은 워킹트리에 남긴다: PM의 산출물 실측 판정 근거가 워킹트리이므로(`opal/core/references/harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정) 이력 변경은 판정 입력을 파괴한다 |
```
R-4 AC "신규 행의 이유 칼럼에 하네스 §1 근거 포인터가 있다" 충족.

**카운트 원격 복제 제거 (H-4) — 설계 원칙**: 개수는 **목록을 소유한 문서**에만 둔다. `pm/dispatch-process.md:115`는 목록 소유자이므로 "3항목" 표기가 정당한 지역 정보다. `op-dev-execute/SKILL.md:97`은 참조자이므로 개수를 보유하면 원격 복제가 된다 → 개수를 제거하고 절 이름만 남긴다. 이 분리가 R-2 AC("3항목 1건 이상")와 D-6 §교훈(복제 제거)을 동시에 만족시키는 유일한 배치다.

교체 대상 `:97` 문말:
- 현행: `... §핵심 제약(전 워커 공통 고정 2항목)이며, 본 스킬은 이를 복제하지 않는다.`
- 개정: `... §핵심 제약(전 워커 공통 고정 항목)이며, 본 스킬은 이를 복제하지 않는다 — 항목 수·문언은 그 문서가 소유한다.`

#### 3.4.3 환경 변경 / 3.4.4 배치·마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-4 AC (표 6→7행) | 산출물 검사 | §절대 금지 표 데이터 행 수 == 7이고 `| 7 |` 행이 존재 (S-7) |
| TS-013 | R-4 AC (이유 칼럼 포인터) | 산출물 검사 | #7 행 이유 칼럼에 `opal-harness.md` §1 포인터 존재 (S-7) |
| TS-014 | H-4 | 산출물 검사 | `op-dev-execute/SKILL.md` 규범 구간에 `공통 고정 2항목` 0건 (S-2 확장 — 신규 판정 후보 S-2b) |

---

### F-005: 프로젝트 문서 복제 축약 (교체형 — F-001 완료 후)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/CONVENTIONS.md` | 문서 | `:203` §Guards 커밋 bullet 제거 (`:204` 근거 행은 존치 — §Guards 전체 근거) | `docs/CONVENTIONS.md:203-204` |
| 2 | `docs/CONVENTIONS.md` | 문서 | `:188` §커밋 규칙 §규칙 첫 bullet을 포인터로 교체 | `docs/CONVENTIONS.md:188` |
| 3 | `docs/CONVENTIONS.md` | 문서 | 변경이력 v1.7.0 행 추가 | `[MUST]` `.opal/AGENT.md` §금지사항 변경이력 의무 |
| 4 | `docs/PROJECT.md` | 문서 | `:223` 레지스트리 CONVENTIONS.md 행 용도 서술 정합 | `docs/PROJECT.md:223` |
| 5 | `docs/PROJECT.md` | 문서 | 변경이력 행 추가 | 동일 |

#### 3.5.2 설계 — 파급 범위 (설계 쟁점 2) 및 2곳 처리 (H-7)

**(1) `:203` 제거**: §Guards의 커밋 bullet 1행을 삭제한다. `:204`의 `- 근거: opal/core/references/opal-harness.md §1 Guards`는 §Guards 절 전체의 근거 행이므로 그대로 둔다 → R-5 AC (b) "하네스 §1을 가리키는 포인터 1건 존재"가 이 행으로 충족된다(신규 행 추가 불필요).

**(2) `:188` 포인터 교체** (TASK.md 미지목 — 본 PLAN에서 추가): §커밋 규칙 §규칙의 4 bullet 중 첫째 `- 커밋은 캡틴이 명시적으로 요청할 때만 수행`은 하네스 §1과 동일 규칙의 두 번째 복제다. AC (a) "커밋 금지 규칙 원문 서술이 0건"을 문면대로 충족하려면 이 행도 처리해야 한다.
```
- 커밋 실행 시점 규칙(사용자 요청 시에만 수행 · 자동 커밋 금지)은 `opal/core/references/opal-harness.md` §1 Guards가 소유한다 — 본 절은 커밋 **메시지 형식·단위**만 규정한다.
```
나머지 3 bullet(`커밋 메시지는 한국어` / `하나의 태스크 = 하나의 커밋` / `CLOSE 시 메모리 히스토리 행 …`)은 메시지 형식·단위 규칙이므로 존치한다 — `[MUST]` `opal/skills/opal-project-init/references/docs-guide.md` §docs/CONVENTIONS.md 구조: "## 커밋 규칙 / {커밋 메시지 형식, 단위}".

**(3) `docs/PROJECT.md:223` 레지스트리 정합 (설계 쟁점 2)**: 현행 용도 서술은 `네이밍, 파일 구조, 커밋 규칙, 구현 규칙(Guards/디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기)`. 개정안:
```
| `docs/CONVENTIONS.md` | 코드 및 문서 컨벤션 | 네이밍, 파일 구조, 커밋 메시지 형식·단위, 구현 규칙(디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기). 승인 게이트·커밋 실행 시점 등 Guards 규칙 원문은 `opal/core/references/opal-harness.md` §1이 소유하고 본 문서는 포인터만 둔다 | Framework | 개발 작업 시 항상 |
```
- `커밋 규칙` → `커밋 메시지 형식·단위` (docs-guide 규범과 정합)
- 구현 규칙 열거에서 `Guards/` 제거 후, Guards 소유권을 하네스로 명시하는 문장 추가
- **AC 추가 (설계 쟁점 2 요구)**: `docs/PROJECT.md:223` 행에 `Guards`가 CONVENTIONS.md 보유 항목으로 열거되지 않고, 하네스 §1 소유임을 명시하는 문구가 1건 존재한다.

> §Guards 절 자체는 CONVENTIONS.md에 존치한다(승인 게이트·CLOSE 확인 등 나머지 bullet은 이번 범위 밖 — TASK.md §제약 "변경이력 표 일괄 제거는 별도 태스크"와 같은 최소 변경 원칙). 본 태스크는 **커밋 조항 1건**만 포인터화한다.

**(4) 순서 제약 집행 (설계 쟁점 3 / H-9)**: F-005는 Phase 2에 배치하고 Step 7의 `의존`을 Step 1로 고정한다 — §4.1·§4.2 참조. Phase 1 미완료 상태에서 Step 7을 실행하면 도달 경로 0 구간이 발생한다.

**(5) STATE 저널 기록 (R-5 AC (c))**: R-5가 R-1 완료 후에 적용됐음을 STATE 저널에 남긴다. 집행 수단은 `state-tool`의 `--note`(`opal/tools/state-tool/state_tool.py:395` `append_decision_log`, `:464` note 경로) — Step 8에서 `mark --task-step execute.implement --note`로 기록한다. `[MUST]` `docs/CONVENTIONS.md` §State 관리: "파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지."

#### 3.5.3 환경 변경 / 3.5.4 배치·마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-5 AC (a) 구형 잔존 0 | 산출물 검사 | `docs/CONVENTIONS.md`에 커밋 금지 **원문 서술** 0건 — `:188`·`:203` 패턴 모두 부재 (S-8) |
| TS-016 | R-5 AC (b) 신형 채택 | 산출물 검사 | 하네스 §1을 가리키는 포인터 >= 1건 (S-9) |
| TS-017 | 설계 쟁점 2 신규 AC | 통합 테스트 | `docs/PROJECT.md` 레지스트리 CONVENTIONS.md 행에 `Guards` 보유 열거 없음 + 하네스 소유 명시 1건 (S-10) |
| TS-018 | R-5 AC (c) | 산출물 검사 | STATE.md 의사결정 로그에 R-1 선행 완료 확인 기록 1건 (S-12 보조) |
| TS-019 | H-9 | 통합 테스트 | PLAN §4.1에서 R-5 Step이 R-1 Step보다 후행 Phase에 배치 (S-12) |
| TS-020 | H-10 | 회귀 테스트 | `test_worktree_tool.py`·`test-regression.js`·`test_memory_tool.py` 전건 pass, 실패 수 증가 0 (S-16) |
| TS-021 | H-11 | 회귀 테스트 | `~/.opal/` 하위 대응 파일이 본 태스크로 변경되지 않음 — install 미실행 확인 (S-13) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1 | opal-task-agent | 병렬 가능 | 주입 슬롯 신설 — **F-005의 선행 조건** |
| 1 | F-004 | 2 | opal-task-agent | 병렬 가능 | 독립 파일 |
| 1 | F-003 | 3, 4, 5, 6 | opal-task-agent | 병렬 가능 | 파일럿 10종을 3+3+3+1로 비중첩 분할 |
| 2 | F-005 | 7 | PM 직접 | 순차 | **Step 1 완료 후에만 착수** (H-9 — 도달 경로 0 구간 방지) |
| 2 | F-005 | 8 | PM 직접 | 순차 | Step 7 완료 후 STATE 저널 기록 (R-5 AC (c)) |

> **순서 제약의 구조적 집행**: F-005(교체형)를 Phase 2로 격리하고 Step 7의 `의존`을 Step 1로 고정한다. Phase 1 전 Step 완료 = Phase 2 진입 조건이므로, R-1 미완 상태에서 CONVENTIONS.md 원문이 제거될 경로가 존재하지 않는다.
>
> **산출량 상한 준수**: 단일 디스패치 산출 파일 3개 이하 — `opal/core/references/pm/dispatch-process.md` Step 6 항목 5. 동일 파일을 건드리는 Step은 같은 배치로 묶었다(Step 1이 R-1·R-2 동시 처리, Step 2가 R-4 3개 편집 동시 처리, Step 7이 CONVENTIONS.md 3개 편집 동시 처리).

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 2개 | 실행 모드: 복잡 | 산출 파일 총 14개

#### Step 1: 주입 슬롯 신설 + 산문·변경이력 정합
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/dispatch-process.md` (1개)
- **작업 내용**: ①`:95` 직후에 §3.1.2 확정 문언 1행 삽입 ②`:115` 각주를 §3.2.2 교체안(3항목 + 성격 2 bullet)으로 재작성 ③변경이력 표 `:192` 다음에 v1.8 행 추가(§3.2.2 문안, 시각은 `~/.opal/tools/date/run.sh` 등 KST 실측)
- **완료 기준**: `grep -c '← 전 워커 공통 고정'` == 3 / 규범 구간(81~180행) `공통 고정 2항목` 0건 / `공통 고정 3항목` >= 1건 / 변경이력 `(097)` 행 1건 / 변경이력 구간 v1.6 행의 `공통 고정 2항목` 기록 1건 보존
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005, TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: 단계 스킬 절대 금지 표 보강 + 원격 카운트 제거
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-execute/SKILL.md` (1개)
- **작업 내용**: ①§절대 금지 표에 §3.4.2 #7 행 추가 ②`:97` 문말을 §3.4.2 개정안으로 교체(개수 제거) ③변경이력 v2.5 행 추가
- **완료 기준**: 표 데이터 행 7개이고 `| 7 |` 행에 `opal-harness.md` §1 포인터 존재 / 파일 규범 구간 `공통 고정 2항목` 0건 / 변경이력 `(097)` 행 1건
- **테스트**: TS-012, TS-013, TS-014
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 — 서로 다른 파일)

#### Step 3: 파일럿 정규화 A그룹 (dev · dev-short · dev-wireframe)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (3개)
- **작업 내용**: 각 파일의 `[PM 컨텍스트 주입]` 블록(dev `:203` / dev-short `:49-52`·`:152` / dev-wireframe `:81-84`)을 §3.3.2 정규 문언으로 교체. 단계 고유 payload는 문말 `단계 추가 전달:` 로 보존. 각 파일 변경이력 행 추가
- **완료 기준**: 3파일 전부 `pm/dispatch-process.md` 참조 보유 / 열거형 잔존(`1. 하네스 Guards 핵심 규칙`) 0건 / payload 정보 손실 0(TEST-SCENARIO.md·changed_files 언급 보존) / 변경이력 `(097)` 행 각 1건
- **테스트**: TS-008, TS-009, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: 파일럿 정규화 B그룹 (project · project-dev · project-loop)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md` (3개)
- **작업 내용**: project는 `:63-66`·`:87` 교체. project-dev는 Phase 3 디스패치 절(`:397` 인접)에, project-loop는 `:362` 디스패치 idiom 절에 정규 블록 신설. `harness_guards` 파라미터 값(`:407`)은 단계 고유 가드이므로 무변경. 각 파일 변경이력 행 추가
- **완료 기준**: 3파일 전부 `pm/dispatch-process.md` 참조 보유 / 열거형 잔존 0건 / 기존 `harness_guards` 문안 무변경 / 변경이력 `(097)` 행 각 1건
- **테스트**: TS-008, TS-009, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: 파일럿 정규화 C그룹 (write-tech · sdd · gc)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`, `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-gc/SKILL.md` (3개)
- **작업 내용**: write-tech는 `:221`·`:317`·`:344` 3건을 정규 문언으로 교체(bullet `- ` 접두 유지). sdd는 `:110` 인접에 정규 블록 신설, `:114`·`:180` 프롬프트 리터럴 무변경. gc는 `:207` §2.3 직전에 정규 블록 신설, **`:219` `[MUST] 커밋 금지` 리터럴 존치**(H-6). 각 파일 변경이력 행 추가
- **완료 기준**: 3파일 전부 `pm/dispatch-process.md` 참조 보유 / gc `:219` 리터럴 1건 보존 / sdd 프롬프트 리터럴 무변경 / 변경이력 `(097)` 행 각 1건
- **테스트**: TS-008, TS-009, TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: 파일럿 정규화 D그룹 (data-design)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-data-design/SKILL.md` (1개)
- **작업 내용**: 첫 디스패치 절(`:94` 인접)에 정규 블록 신설. `:106` `**하네스 Guards**:` 리터럴은 단계 고유 가드로 무변경. 변경이력 행 추가
- **완료 기준**: `pm/dispatch-process.md` 참조 1건 / `:106` 리터럴 무변경 / 변경이력 `(097)` 행 1건
- **테스트**: TS-008, TS-009, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 7: 프로젝트 문서 복제 축약 (CONVENTIONS.md + PROJECT.md)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md`, `docs/PROJECT.md` (2개)
- **작업 내용**: ①`docs/CONVENTIONS.md:203` 커밋 bullet 삭제(`:204` 근거 행 존치) ②`:188` bullet을 §3.5.2 (2) 포인터 문안으로 교체 ③변경이력 v1.7.0 행 추가 ④`docs/PROJECT.md:223` 레지스트리 행을 §3.5.2 (3) 개정안으로 교체 ⑤`docs/PROJECT.md` 변경이력 행 추가
- **완료 기준**: CONVENTIONS.md 커밋 금지 원문 0건 / 하네스 §1 포인터 >= 1건 / §커밋 규칙 나머지 3 bullet 보존 / PROJECT.md 레지스트리 행에 `Guards` 보유 열거 없음 + 하네스 소유 명시 1건 / 두 파일 변경이력 `(097)` 행 각 1건
- **테스트**: TS-015, TS-016, TS-017, TS-019
- **실행 방법**: direct
- **의존**: **Step 1** (H-9 — R-1 완료 전 적용 금지)

#### Step 8: STATE 저널에 순서 준수 기록
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `tasks/097-260821-opds-커밋금지-워커주입-슬롯화/STATE.md` (state-tool 자동 갱신, 1개)
- **작업 내용**: `~/.opal/tools/state-tool/run.sh mark <task-path> --task-step execute.implement --done --note 'R-5(CONVENTIONS.md 포인터화)는 R-1(주입 슬롯 신설) 완료 확인 후 적용 — 도달 경로 0 구간 없음'` 실행. state.json 직접 편집 금지
- **완료 기준**: STATE.md 의사결정 로그에 해당 note 1건 기록 / `state-tool show` 정합
- **테스트**: TS-018
- **실행 방법**: direct
- **의존**: Step 7

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 ∥ Step 3 ∥ Step 4 ∥ Step 5 ∥ Step 6 | 파일 교집합 0 — 6개 Step이 서로 다른 파일 집합을 수정한다. `harness/parallel-execution.md` §산출량 상한 참조 규칙에 따라 각 디스패치 산출 파일 3개 이하 유지 |
| Step 1 → Step 7 | **순서 제약 (H-9)** — 현행 유일 도달 경로(CONVENTIONS.md 원문)를 R-1 신설 전에 제거하면 커밋 금지 도달 경로가 0개가 된다 |
| Step 7 → Step 8 | 저널 기록은 R-5 적용 사실을 대상으로 한다 — 적용 전 기록은 허위 |
| Step 3·4·5·6 상호 | 파일럿 10종 비중첩 3+3+3+1 분할 — `pm/dispatch-process.md` Step 6 항목 5 산출량 상한 |
| Step 2 ↔ Step 1 카운트 정합 | 두 Step이 각각 다른 파일의 카운트 서술을 다룬다(SSOT 3항목 명시 / 참조자 개수 제거). 파일이 다르므로 병렬 가능하나, TEST 단계에서 **교차 검증**(TS-005 + TS-014)으로 정합을 확인한다 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 주입 슬롯 3행 존재 + 신규 문언 필수 요소 | TS-001, TS-002, TS-003 | 표기 행 3개, commit·push·reset·rebase + 워킹트리 보존 문구 + 하네스 §1 포인터 전부 존재 |
| F-002 | 각주 3항목 정합 + 성격 2분류 + 변경이력 | TS-004~TS-007 | 규범 구간 구 표현 0건, 신 표현 >= 1건, 변경이력 097 행 1건, v1.6 사실 기록 보존 |
| F-003 | 파일럿 10/10 도달 경로 + 단일 형태 | TS-008~TS-011 | 참조 보유 10파일, 열거형 잔존 0건, gc 리터럴 보존, 변경이력 10행 |
| F-004 | 금지 표 7행 + 이유 포인터 + 원격 카운트 제거 | TS-012~TS-014 | 표 7행, #7 포인터 존재, `2항목` 0건 |
| F-005 | 컨벤션 원문 0 + 포인터 1 + 레지스트리 정합 + 순서 기록 | TS-015~TS-019 | 원문 0건, 포인터 >= 1건, PROJECT.md 행 정합, STATE 저널 기록 1건, Phase 배치 후행 |

### 5.2 회귀 테스트
- [ ] `opal/tools/worktree-tool/tests/test_worktree_tool.py` 전건 pass — `:669-672`가 `pm/dispatch-process.md`의 `## 작업 경로`·`절대경로` 존재를 검사한다 (TS-020)
- [ ] `opal/tools/code-scan/tests/test-regression.js` 전건 pass — `:325,731,733`이 `docs/CONVENTIONS.md` §@header 규칙 본문을 검사한다 (TS-020)
- [ ] `opal/tools/memory-tool/tests/test_memory_tool.py` 전건 pass — `:2578`이 `opal-pilot-gc/SKILL.md` 참조 무결성을 검사한다 (TS-020)
- [ ] `opal/tools/state-tool/tests/test_state_tool.py` 전건 pass — `:74`가 opd `pipeline.json`을 읽는다(본 태스크 미변경 파일)
- [ ] `state-tool spec-validate` pass — pipeline.json 전 파일 diff 0건
- [ ] 파일럿 10종 `pipeline.json` diff 0건 — 본 태스크는 SKILL.md 산문만 수정하며 파이프라인 행 스펙을 건드리지 않는다
- [ ] `~/.opal/` 배포본 무변경 — install 미실행 (TS-021)
- [ ] `git log` HEAD 불변 — 자동 커밋 0건

### 5.3 코드/문서 품질
- [ ] 변경 12개 문서 전부 변경이력 표 행 추가 (`.opal/AGENT.md` §금지사항 변경이력 의무)
- [ ] 변경이력 일시는 KST 실측값 사용 (추정 금지)
- [ ] 커밋 규칙 **원문**은 `opal-harness.md` §1에만 존재 — 나머지는 포인터 (TASK.md §제약 SSOT 단일화)
- [ ] 특정 AI 도구 전용 permission·hook 장치 추가 0건 — `[MUST]` `docs/PROJECT.md` §프로젝트 원칙 3: "플랫폼 독립성 — Claude Code, Cursor, Gemini, Codex 등 어디서든 동작해야 한다"
- [ ] 하드코딩된 플랫폼 분기 추가 0건 — `[MUST]` `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다."
- [ ] 외부 프로젝트명·경로·태스크번호 인용 0건 (TASK.md §제약 외부 프로젝트 비참조)
- [ ] 모든 설계 결정에 경로/줄번호 인용 — `[MUST]` `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

### 5.4 보안
- [ ] 변경 파일 전량 `.md` — 시크릿·토큰·자격증명 기재 0건
- [ ] `.env`·인증 파일 신규 생성 0건
- [ ] 절대경로 노출 점검 — 문서 인용은 레포 상대경로 사용(홈 디렉토리 절대경로 기재 금지, `~/.opal/` 배포 경로 표기는 규범 인용 목적에 한정)
- [ ] `git` 실행 명령을 문서에 예시로 기재할 때 실행 가능한 파괴적 스크립트 형태로 남기지 않는다(코드 스팬 인용만)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 14개 | 복잡 |
| 모듈 범위 | 다중 (core/references · skills/op-dev-* · skills/opal-pilot-* × 10 · docs/) | 복잡 |
| 작업 유형 | 프레임워크 SSOT 구조 개선 (주입 계약 신설 + 복제 정리) | 복잡 |
| 외부 의존성 | 없음 (신규 패키지·API·도구 0) | 단순 |
| **실행 모드** | **복잡** | Step·파일·모듈 3기준 초과 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬 6 — 파일 교집합 0)
  A1 opal-task-agent : Step 1  (pm/dispatch-process.md)                    [F-001·F-002]
  A2 opal-task-agent : Step 2  (op-dev-execute/SKILL.md)                   [F-004]
  A3 opal-task-agent : Step 3  (pilot dev / dev-short / dev-wireframe)      [F-003]
  A4 opal-task-agent : Step 4  (pilot project / project-dev / project-loop) [F-003]
  A5 opal-task-agent : Step 5  (pilot write-tech / sdd / gc)                [F-003]
  A6 opal-task-agent : Step 6  (pilot data-design)                          [F-003]

Batch 2 (순차 — A1 완료 필수, H-9)
  PM 직접 : Step 7  (docs/CONVENTIONS.md · docs/PROJECT.md)                 [F-005]
  PM 직접 : Step 8  (STATE 저널 기록)                                        [F-005]

Batch 3
  opal-test-agent : TS-001~TS-021 실행 (TEST-SCENARIO.md S-1~S-17)
```

**그룹핑 근거**: ①파일 충돌 방지 — 동일 파일을 수정하는 편집은 전부 같은 Step에 묶었다(dispatch-process.md 3개 편집 = Step 1, op-dev-execute 3개 편집 = Step 2, CONVENTIONS.md 3개 편집 = Step 7) ②모듈 응집 — 파일럿 10종을 오케스트레이터 계층 단일 작업 유형으로 묶고 산출량 상한 3으로만 분할 ③`docs/` 편집은 PM 직접(plan-guide §agent 필드 배정 규칙 「문서 → PM 직접」)

### C-2. 스킬 요구사항
- 기존 스킬로 충분 — `op-dev-execute`(EXECUTE 단계 스킬, `opal/skills/op-dev-execute/SKILL.md`)를 그대로 사용한다.
- 갭 판별: 6개 Step이 동일 패턴(마크다운 부분 편집 + 변경이력 행 추가)을 반복하지만, 이는 이미 `op-dev-execute` + `.opal/AGENT.md` §금지사항으로 규정된 절차다 → 신규 스킬 후보 아님.
- **주의**: Step 2는 `op-dev-execute/SKILL.md` 자체를 수정한다. 워커가 이 스킬을 로드해 실행하므로, 워커 로드 시점과 편집 시점이 겹친다. 실질 위험은 없다(로드는 Read 1회, 편집은 그 이후)나 Step 2 워커에게 "자기 스킬 파일을 편집한다"는 사실을 디스패치 프롬프트에 명시한다.

### C-3. 도구 요구사항
| 도구 | 용도 |
|------|------|
| `grep` / `awk` / `sed` | 위치 특정 + 범위 한정 판정식 집행 (입력 축소 규율 준수) |
| `~/.opal/tools/state-tool/run.sh` | 파이프라인 행 전환 + `--note` 의사결정 로그 (Step 8) |
| `~/.opal/tools/date/run.sh` | 변경이력 KST 실측 일시 |
| `pytest` / `node` | 회귀 실행 (worktree-tool · memory-tool · state-tool · code-scan 테스트) |
| `git status --short` / `git diff --stat` | 산출물 실측 (실행만, 이력 변경 명령 금지) |
| 신규 설치 | **없음** |

### C-4. 테스트 전략
- **기능 테스트**: TEST-SCENARIO.md S-1~S-4·S-7~S-9·S-13~S-15(L1) — 실 파일 grep 판정. TS-001~TS-007, TS-012~TS-016, TS-021 대응.
- **통합 테스트**: S-5·S-6·S-10~S-12·S-16(L2) — 전 문서 집합 대조 + Phase 배치 검사 + 도구 회귀. TS-008~TS-011, TS-017~TS-020 대응.
- **회귀 스위트**: `python3 -m pytest opal/tools/worktree-tool/tests opal/tools/memory-tool/tests opal/tools/state-tool/tests` + `node opal/tools/code-scan/tests/test-regression.js` — 실패 수 증가 0이 Pass 조건(기존 RED 테스트는 RED 유지가 정상).
- **부정 검증**: S-13(배포본 무변경) · S-14(외부 프로젝트 참조 0) · S-15(자동 커밋 0) — 본 태스크의 제약 자체가 검증 대상이다.
- **수동(L3)**: S-17 [SUPERVISOR] — 신규 주입 문언의 워커 통제력에 대한 소유자 수용 판정.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 프레임워크 SSOT | Markdown (참조 문서·스킬 정의) | `op-dev-execute` |
| 검증 | grep/awk/sed 문자열 판정, pytest, node | `op-dev-test-agent` |
| 상태 집행 | `state-tool` (Python CLI) | - |

> 코드 변경 0줄 — React/Next.js/Python 등 언어 스택 스킬(vercel-labs, trailofbits) 및 ui-designer는 적용 대상이 아니다. FE 화면 설계 없음.

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 API·UI 컴포넌트 조회 불요 — 대상이 전부 로컬 프레임워크 문서다. context7·shadcn MCP 미사용 |

> brain 사전 조회: `brain-tool search` 3회(워커 컨텍스트 주입 커밋 금지 / 하네스 Guards 주입 / dispatch-process 템플릿) 전건 matches 0 — 관련 과거 결정 없음(신규 설계). 단, 설계 근거로 활용한 기존 brain 페이지 2건은 §8.3 D-11·D-12로 등재.

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | 커밋 규칙 SSOT (§1 커밋 규칙 `:42`), Git 사전 점검 `:21` |
| D-2 | 설계 | 프로젝트 AGENT.md | `.opal/AGENT.md` | 배포 경계·플랫폼 분기·변경이력 의무·하네스 SSOT 수정 지침 |
| D-3 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 주입 템플릿 (`:91-97` 핵심 제약, `:115` 각주, `:181-192` 변경이력) — R-1·R-2 대상 |
| D-4 | 설계 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | 절대 금지 표 `:108-115`, 원격 카운트 `:97` — R-4 대상 |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 복제 조항 `:188`·`:203`, §State 관리 도구 규율 — R-5 대상 |
| D-6 | 설계 | 094 DONE.md | `tasks/094-260815-opd-STATE-저널화/DONE.md` | SSOT 산문 복제 교훈(열거 제거 + 포인터 대체) + 코드 0줄 태스크 검증 선례 |
| D-7 | 설계 | docs-guide.md | `opal/skills/opal-project-init/references/docs-guide.md` | CONVENTIONS.md 규범 정의(코드 컨벤션) + §커밋 규칙 = 메시지 형식·단위 |
| D-8 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | `:49`·`:57` — dispatch-process.md 무조건 로드 지점 (설계 쟁점 1 근거 3) |
| D-9 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | `:21` 워킹트리 = PM 판정 유일 증거 입력 (설계 쟁점 4 근거 2) |
| D-10 | 설계 | PROJECT.md | `docs/PROJECT.md` | `:223` 문서 레지스트리 (R-5 파급), §프로젝트 원칙 3 플랫폼 독립성 |
| D-11 | 설계 | brain — 앵커 로드 조건 | `.opal/brain/pages/concept/anchor-load-condition-must-match-target.md` | 규칙은 무조건 로드 문서에, 조건부 문서에는 참조 1줄 (설계 쟁점 1 근거 4) |
| D-12 | 설계 | brain — SSOT 미등록 완화 재발 | `.opal/brain/pages/concept/mitigation-recurs-without-ssot-registration.md` | 실증된 대응을 재현 가능한 SSOT로 옮기는 것이 핵심이라는 선례 |
| D-13 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 원칙, §2 인용 포맷·[MUST] 토큰 |
| D-14 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py:395,464` | `append_decision_log` — Step 8 저널 기록 집행 수단 |
| D-15 | 소스 | test_worktree_tool.py | `opal/tools/worktree-tool/tests/test_worktree_tool.py:669-672` | dispatch-process.md 본문 검사 — 회귀 대상 (H-10) |
| D-16 | 소스 | test-regression.js | `opal/tools/code-scan/tests/test-regression.js:325,731,733` | CONVENTIONS.md 본문 검사 — 회귀 대상 (H-10) |
| D-17 | 소스 | test_memory_tool.py | `opal/tools/memory-tool/tests/test_memory_tool.py:2578` | opal-pilot-gc/SKILL.md 참조 무결성 — 회귀 대상 (H-10) |
| D-18 | 소스 | opal-convention-checker AGENT.md | `opal/agents/opal-convention-checker/AGENT.md:17,60` | CONVENTIONS.md 섹션 일반 파싱 — R-5 무영향 근거 (설계 쟁점 5) |
| D-19 | 소스 | 액션 에이전트 3종 AGENT.md | `opal/agents/opal-loop-action-agent/AGENT.md:354`, `opal-task-action-agent/AGENT.md:249,261`, `opal-sdd-action-agent/AGENT.md:122,252` | 커밋 금지 자체 보유 계층 실측 (§2.3.3) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | R-2 AC를 파일 전역 grep으로 집행하면 변경이력 v1.6 사실 기록을 지우게 된다 (H-3) | F-002 | 중 | §3.2.2 3행 판정식으로 AC 범위를 규범 구간에 한정. TEST-SCENARIO S-2 판정식 보정을 PM 보강 대상으로 명시 |
| R-2 | `op-dev-execute/SKILL.md:97`의 원격 카운트를 놓치면 적용 즉시 SSOT 어긋남 (H-4) | F-004 | 상 | Step 2 작업 내용에 명시 편입 + TS-014로 판정. TASK.md R-4에 없던 항목이므로 EXECUTE 디스패치 프롬프트에 강조 주입 |
| R-3 | 코드 변경 워커 4종(be/fe/db/task) AGENT.md는 커밋 금지 0건이며 본 태스크 범위 밖이다 | F-001 | 중 | F-001 주입 슬롯이 전 디스패치에 항목을 실어 도달을 보증한다. AGENT.md 계층 보강은 별도 태스크 후보로 백로그 제안(§보고) — 본 태스크에서 열거하면 6종 복제가 재발한다 |
| R-4 | 파일럿 10종 편집 중 payload 정보(TEST-SCENARIO 경로·changed_files) 유실 | F-003 | 중 | 정규 문언 문말 `단계 추가 전달:` 접미로 보존을 규정. Step 3~6 완료 기준에 "payload 정보 손실 0" 명시 |
| R-5 | install 미실행이므로 이번 세션의 PM·워커 런타임에는 규칙이 적용되지 않는다 (H-11) | 전체 | 중 | 소스 diff 보고 + 배포본 무변경 부정 검증(TS-021). 배포는 소유자 지시 시에만 수행 — `[MUST]` `.opal/AGENT.md` §금지사항 배포 경계 |
| R-6 | gc `:219` 리터럴을 "단일 형태 통일"로 오해해 제거하면 유효 방어가 사라진다 (H-6) | F-003 | 중 | §3.3.2에 층 구분(PM 지시 층 vs 프롬프트 리터럴 층)을 명문화하고 TS-010으로 존치를 판정 |
| R-7 | Step 7을 Phase 1과 병렬 실행하면 도달 경로 0 구간 발생 (H-9) | F-005 | 상 | Phase 2 격리 + Step 7 `의존: Step 1` 고정 + TS-019 배치 검사 + Step 8 저널 기록으로 사후 추적 |
| R-8 | 문서 편집이 무관한 도구 테스트를 깨뜨린다 (H-10) | 전체 | 중 | 편집 구간을 §@header 규칙·§작업 경로 블록 밖으로 한정. 회귀 4스위트 실행을 §5.2 필수 항목으로 고정 |

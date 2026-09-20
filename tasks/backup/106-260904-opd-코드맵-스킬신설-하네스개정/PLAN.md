# PLAN: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 작성일: 2026-09-04 21:47 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (F-001 ~ F-006)

## 결론

- **DEC-1** R-4 신설 검증은 **`state-tool` 확장**으로 확정 — `verify --code-scan-citation-check` 라우터 + `cmd_advance`/`cmd_mark`의 EXECUTE 첫 행 자동 훅. `code-scan`은 태스크 폴더·PLAN.md 개념을 갖지 않아 응집도가 깨진다.
- **DEC-2** `pipeline.json`은 **기존 `plan.pm_gate.gate.checklist` 1행 확장**으로 확정 — 행 수·key 불변이므로 R-6 AC(a) 원문을 그대로 유지한다(재정의 불요).
- **DEC-3** `opal-pm.md` §12는 **「유지」 블록 1행 추가 + 표 하단 축 구분 각주 1줄** — "Gate ❌ 미적용"은 파이프라인 게이트 3종 한정임을 각주가 명문화해 자기모순을 제거한다.
- **DEC-4** 기존 PostToolUse hook 재사용만으로는 R-2 **불충족**(inline 모드 즉시 이탈 + 경고 등급) — `git diff --name-only` 신호 + **기존** `code-scan validate --changed` 재사용으로 신규 도구 0건.
- **DEC-5** `SubagentStop` hook **탈락** — 사후 발동(사전 차단 불가) + 판정 대상 특정 불가 + Claude 전용 경로(플랫폼 독립성 위반).
- **DEC-6** 변경이력은 **문서별 기존 형태 준수**(헤딩형 7 / 인라인형 1 / 컬럼 순서 이종 1) — §4.2 각 Step 완료 기준에 문서별로 명시했다.
- 최대 리스크는 신설 훅의 발동 반경이다 — EXECUTE 단계 보유 파이프라인이 8종이므로, 3중 graceful skip 게이트(자산 → PLAN.md → 적용 범위)를 판정 로직보다 **앞**에 둬 오탐을 설계로 배제한다(H-6·H-7).

---

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| `[결정]` 최초 생성·환경설정은 하네스가 아닌 독립 스킬(opi식 2모드) | 유효 | - |
| `[결정]` 갱신은 매번 트리거되는 하네스 규정으로 편입 | 유효 | - |
| `[결정]` 소비는 2단 절차(1차 code-scan → 2차 grep) | 유효 | - |
| `[결정]` 스킬 신설 + 하네스 개정 통합 태스크 | 유효 | - |
| `[결정]` 레거시 backfill 팬아웃 · `split` 샤딩 · `opi` Phase 편입 범위 제외 | 유효 | - |
| `[결정]` 스킬명 `opal-code-map-builder` / 약어 `opcmb` | 유효 | `opal/core/references/opal-skills-registry.json` 실측 — alias 29종에 `opcmb` 미포함(중복 0) |
| `[결정]` 스킬 범위는 `manifest` 중심, `inline`은 종료 분기 | 유효 | - |
| `[결정]` 하네스 모드 `agentic` | 유효 | - |
| `[사실]` `opal-harness.md` §8 Lazy 트리거가 EXECUTE 코드 파일 변경으로 한정 | 승계(ANALYSIS 대조 확인) | `opal/core/references/opal-harness.md:259` "적용 시점: EXECUTE 단계에서 코드 파일 변경 시" |
| `[사실]` 두 관리 방식은 상호 배타·프로젝트당 1택 | 승계(ANALYSIS 대조 확인) | `opal/core/references/header-standard.md:191` (→ D-1 §7) |

> `사실오류` 0건. `수정필요` 0건. TASK.md의 확정 지위를 박탈한 항목은 없다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`@header` 자산의 **생성**(신설 스킬 `opcmb`)·**갱신**(L2 완료 시점 게이트)·**소비**(2단 규율 + 도구 집행)의 3국면을 완결한다. 자산이 없는 프로젝트(이 레포: `headerSource: inline` + code-map 부재)에서 신설 집행이 오탐을 내지 않도록 3중 graceful skip을 설계로 못 박고, 기존 pilot 파이프라인 행 구성은 무변경으로 보존한다.

### 1.2 기능 목록 — R-N ↔ F-NNN 커버리지 대조

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `opal-code-map-builder`(`opcmb`) 스킬 신설 + 약어 등록 | R-1 | P0 | 없음 |
| F-002 | L2 경량 트랙 @header 갱신 검증 게이트 신설 | R-2 | P0 | 없음 |
| F-003 | 소비 2단 규율(1차 code-scan → 2차 grep) 명문화 | R-3 | P0 | 없음 |
| F-004 | 소비 집행 승격 — PM 자기판정 → 도구 판정 | R-4 | P0 | 없음 |
| F-005 | 미보급 프로젝트 폴백(오탐 0건) | R-5 | P0 | F-002, F-004 |
| F-006 | 회귀 보존 — 기존 파이프라인 무변경 검증 | R-6 | P0 | F-001~F-005 |

**커버리지 대조 — 누락 0건 / 과잉 0건**

| R-N | AC 수 | 사상 F-ID | 커버 Step | 커버 TS-ID | 누락 |
|-----|-------|----------|----------|-----------|------|
| R-1 스킬 신설 | 4 (a~d) | F-001 | 1, 2, 3 | TS-001 ~ TS-003 | 없음 |
| R-2 갱신 트리거 하네스 편입 | 3 (a~c) | F-002 | 7, 8 | TS-004 ~ TS-006 | 없음 |
| R-3 소비 2단 규율 | 3 (a~c) | F-003 | 9, 10 | TS-007 | 없음 |
| R-4 소비 집행 승격 | 3 (a~c) | F-004 | 4, 5, 6 | TS-008 ~ TS-010 | 없음 |
| R-5 미보급 폴백 | 2 (a~b) | F-005 | 4, 6, 7 (공동 소속) | TS-011, TS-012 | 없음 |
| R-6 회귀 보존 | 2 (a~b) + 신설 (c)(d) | F-006 | 12 | TS-013 ~ TS-016 | 없음 |
| 부속 — install 배포 영향 | (완료기준) | F-001 | 14 | TS-017 | 없음 |
| 부속 — 변경이력 규약(DEC-6) | (제약 ⑤) | 전 F | 전 Step 완료 기준 | TS-018 | 없음 |

### 1.3 기능 의존 그래프

```
F-001 ─┐
F-002 ─┼─→ F-005 ─→ F-006
F-003 ─┤            ↑
F-004 ─┴────────────┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다. H-1~H-5는 ANALYSIS §5 리스크 5건 승계, H-6~H-12는 PLAN 신규.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 / `opal-pm.md` §12 표 | "L2 = Gate 미적용" 명시 원칙과 새 검증 행의 문면 자기모순 → PM이 어느 쪽을 따를지 판단 분기 | P1 | L1(문서 정합 판독) | S-후보: DEC-3 각주가 파이프라인 게이트 3종 한정임을 명시하는지 문면 검사 |
| H-2 | F-004 집행 지점 선정 | PreToolUse `Task` hook 인프라 0건 + 플랫폼 분기 격리 원칙 — hook 경로를 택하면 Cursor/Gemini에서 규칙이 소멸 | P1 | L1(설계 판정) | S-후보: DEC-1·DEC-5 근거가 PLAN에 명시되고 채택안이 플랫폼 독립 경로인지 |
| H-3 | 전 F / 개정 8문서 | `.opal/AGENT.md` 변경이력 누락 금지 vs 문서별 마커·컬럼 형태 이종 → 잘못된 형태로 행 삽입 시 표 파손 | P2 | L1(형태 대조) | S-후보: DEC-6 표대로 8문서 각각의 기존 형태를 유지했는지 |
| H-4 | F-004 / `pipeline.json` ×3 | 신규 게이트 행 추가 방식은 `task_steps` 행 수를 바꿔 R-6 AC(a)와 정면 충돌 | P0 | L1(행 수·key diff) | S-후보: opd 16 / opds 11 / opp 9 및 key 집합 개정 전후 동일 |
| H-5 | F-001 / 레지스트리 | alias 영구 점유 — 중복 등록 시 `skill-registry match` 라우팅 비결정 | P1 | L2(`skill-registry validate` 실행) | S-후보: `match opcmb` 단일 해석 + alias 총계 30종 |
| H-6 | F-004 / `cmd_advance`·`cmd_mark` 훅 | 발동 반경 — EXECUTE 단계 보유 파이프라인 8종(opd·opds·opp·opdw·oppd·oppl·opsdd·opwt)에서 훅이 무조건 발동해 기존 태스크 진입을 차단 | P0 | L2(8 파이프라인 실행 관측) | S-후보: 8종 각각에서 조건 미해당 시 exit code·stdout 키 집합이 개정 전과 동일 |
| H-7 | F-004 / `auto_pass` 거부 위치 | `_run_clarification_hook`은 `auto_pass` 거부를 graceful skip **앞**에 둬, 같은 배치를 답습하면 문서 전용 태스크에서도 거부가 발생(R-5 오탐) | P0 | L2(문서 태스크 + `--auto-pass` 실행) | S-후보: `--auto-pass`가 실린 문서 태스크 EXECUTE 진입이 exit 0으로 통과 |
| H-8 | F-004 / `state_tool.py` | 파일 상단 `@header` 미갱신 → 다음 CLOSE에서 `validate --changed`가 `newly_uncovered`로 자기 차단 | P1 | L2(`code-scan validate --changed state_tool.py`) | S-후보: 수정 후 exit 0 · `newly_uncovered` 0 |
| H-9 | F-001 / `docs/CONVENTIONS.md` | 약어 표는 레지스트리 사본인데 실측 결손 2건(`opgr`·`opeli5`) — `opcmb`만 더하면 총계가 또 틀린다 | P2 | L1(표 ↔ 레지스트리 대조) | S-후보: 표 총계·항목이 레지스트리 30종과 1:1 일치 |
| H-10 | F-004 / 인용 판정 로직 | 토큰 매칭이 "실질 인용"과 "단순 언급"을 구분하지 못해 미탐(느슨) 또는 오탐(엄격) | P1 | L2(양성·음성 표본 2케이스) | S-후보: 인용 있는 PLAN.md pass / 인용 없는 PLAN.md exit≠0 |
| H-11 | F-004·F-005 / 배포 경계 | `~/.opal/` 미재배포 상태에서 AC(b)(c)를 실측하면 구 배포본이 판정 — 통과·실패 모두 무의미 | P0 | L2(install 후 배포본 실행) | S-후보: `~/.opal/tools/state-tool/run.sh`가 신설 플래그를 인식 |
| H-12 | 부속 / `docs/PROJECT.md`·`ARCHITECTURE.md` | 스킬 수 셀이 실측(44)과 이미 2건 드리프트 — `+1`만 하면 45가 아니라 43이 되어 오차가 커진다 | P2 | L1(`find` 실측 대조) | S-후보: 셀 값이 실측 45와 일치 |

---

## 2. 기능별 분석

> **[MUST] 승계 원천 2원 규정** — 아래 파일 맵은 ANALYSIS.md §1.1 「관련 파일 목록」 앞 4열을, 확정값은 ANALYSIS.md §8 「다음 단계 입력」 3열을 재조사 없이 승계했다(5열째 `근거(줄번호)`는 절단). 재도출 0건.

### F-001: `opcmb` 스킬 신설 + 약어 등록

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-code-map-builder/SKILL.md` | 신설 스킬 본체 (init\|update 2모드) | 신규 |
| 문서 | `opal/core/references/opal-skills-registry.json` | 약어 SSOT — `opcmb` 항목 추가 | 수정 |
| 문서 | `docs/CONVENTIONS.md` | 약어 표 사본 갱신 | 수정 |

#### 2.1.2 현재 구현

- 레지스트리는 `$schema`/`version`/`updated_at`/`groups`/`changelog` 5키 구조이며 `groups.opal`에 프레임워크 운영 스킬 13종이 등재되어 있다(`opal-skills-registry.json` 실측). `opi` 항목은 `name`/`alias`/`description`/`triggers`/`paths` 5키다.
- 스킬 라우팅은 레지스트리 구동이다 — `skill-registry.js`가 `opal-skills-registry.json`을 로드해 `match`/`get`/`list`를 제공하며(`opal/tools/skill-registry/skill-registry.js:131`), `//` 커맨드 해석이 이 경로를 탄다. 따라서 **레지스트리 등록만으로 `//opcmb`가 발동**하고 별도 라우팅 표 신설은 불요다.
- 최근 등재 스킬 2종(`opal-brain`·`opal-improve`)의 SKILL.md frontmatter는 `name`/`description`/`alias`/`triggers`/`version`(+`domain`) 형태다 — R-1 AC(a)의 5필드와 정합한다.
- `code-scan` 서브명령 15종 중 code-map 계열 6종(`init`/`discover`/`scaffold`/`target`/`validate`/`split`)의 CLI 계약은 `code-scan.js:118-175` USAGE 블록이 SSOT다. `init`은 `--header-source` 필수·`--write`·`--force`, `discover`는 `--out`/`--dry-run`, `scaffold`는 `--dry-run`을 받는다.

#### 2.1.3 영향 범위

- 직접: 위 3파일.
- 간접: `skill-registry.js`의 로드 대상 데이터만 늘어나며 코드 무변경. `opal-help` SKILL.md의 커맨드 예시 표는 레지스트리 조회를 원천으로 선언하므로(`opal/skills/opal-help/SKILL.md:26`) 사본 갱신 의무 대상이 아니다 — 범위 제외.
- 간접: `opal-harness.md` §9 도구 표는 **도구** 목록이며 스킬을 등재하지 않는다 → `opcmb` 등재 불요(ANALYSIS §1.1 마지막 행의 "PLAN 판단" 항목을 **무변경**으로 확정).

---

### F-002: L2 경량 트랙 @header 갱신 검증 게이트

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/opal-pm.md` | §12 L2 표에 @header 검증 게이트 행 추가 | 수정 |
| 문서 | `opal/core/references/harness/header-rules.md` | §갱신 시점 표에 L2 완료 시점 행 추가 | 수정 |

#### 2.2.2 현재 구현

- `header-rules.md:32-42` §갱신 시점 (3단) — (a) 워커 같은 자리 / (b) CLOSE 진입 전 `validate --changed` 차단 / (c) PostToolUse hook 경고. L2에는 CLOSE가 없어 (b)가 붙을 자리가 없다.
- `opal-pm.md:202-216` §L2 하네스 적용 범위 — 유지 4행(Guards / @header 규칙 / OPAL Tools / Coding Principles) + 미적용 5행. 미적용 행은 `opal-pm.md:212` "Gate (QA Gate, State Gate, PM Gate)"로 **파이프라인 게이트 3종을 열거**한다.
- **실측 (E1)**: 이 레포(`headerSource: inline`, code-map 부재)에서 `node opal/tools/code-scan/code-scan.js validate --changed <path>` 실행 결과 — 인라인 헤더 보유 코드 파일은 `coverage 100% (1/1)` exit 0, 헤더 없는 `.md`는 `coverage 0% (0/1)` + `violations[0].sub = "pre_existing"` **exit 0**(비차단). 즉 `validate --changed`는 inline 모드에서도 정상 동작하며 레거시 파일로 인한 오탐이 없다.
- **실측 (E1)**: `code-map-hook.js:126-128`은 `mode === 'inline'`이면 즉시 무출력 exit 0 — 이 레포에서 PostToolUse hook은 **어떤 검사도 수행하지 않는다**. manifest 모드에서도 출력은 `additionalContext` 경고이며 차단이 아니다(`code-map-hook.js:158-165`).

#### 2.2.3 영향 범위

- 직접: 위 2파일.
- 간접: L2 경량 트랙 이용 흐름 전체(PM 직접 수정). 파이프라인·`state.json`은 미경유이므로 `state-tool` 무변경.
- 간접: `validate --changed`는 기존 서브명령이므로 `code-scan.js` **무변경** — DEC-4의 직접 귀결.

---

### F-003: 소비 2단 규율 명문화

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/opal-pm.md` | §13에 2단 소비 절차 명문화 | 수정 |
| 문서 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악 — grep 전환 조건 보강 | 수정 |

#### 2.3.2 현재 구현

- `opal-pm.md:220-236` §13 — 상황별 활용 방법 5행 표 + 원칙 1줄 + 빈 결과 폴백 포인터. 2차 전환 조항은 없다.
- `opal-pm.md:237` — grep 관련 유일 조항이 **사용자 오버라이드**("사용자가 'grep으로 해'…")로, 소유자 권한 행사이지 절차 진행 경로가 아니다.
- `dispatch-process.md:130` "코드 변경·코드 탐색이 필요한 작업이면 디스패치 전 code-scan을 무조건 호출한다", `:134` "(Glob/Grep 직행 금지)".
- `header-rules.md:129-137` §빈 결과 폴백 3분기 — ① 매칭 0건 → Glob/Grep **보강**, ② 저커버리지(<30%) → 동시 활용, ③ 정상. 즉 "1차 실패 시" 경로는 이미 명문이고, **"1차 성공 후 상세 전환"**만 미서술이다.

#### 2.3.3 영향 범위

- 직접: 위 2파일. `opal-pm.md`는 F-002와 **동일 파일**이므로 같은 디스패치에 묶어 순차 편집한다(`pm/dispatch-process.md` Step 6 산출량 상한 규정).
- 간접: `opal-be-agent`/`opal-plan-agent` AGENT.md의 "적극 활용한다" 권고 문면 — 2단 절차의 1차 수단을 그대로 가리키므로 문면 개정 불요. 범위 제외(ANALYSIS §3.2 PLAN 판단 항목을 **무변경**으로 확정).

---

### F-004: 소비 집행 승격 (PM 자기판정 → 도구 판정)

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | 인용 검증 라우터 + EXECUTE 진입 자동 훅 신설 | 수정 |
| 문서 | `opal/core/references/harness/pm-review-gate.md` | §표준 검토 항목 14 집행 방식 승격 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/references/pipeline.json` | `plan.pm_gate.gate.checklist` 1행 확장 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 동일 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project/references/pipeline.json` | 동일 | 수정 |

#### 2.4.2 현재 구현

- `pm-review-gate.md:112-119` 항목 14 — 트리거/검증 내용/적용 범위/판정/Pass 조건 5요소가 이미 정의되어 있으나 **판정 주체가 PM 자신**이다. Pass 조건은 "code-scan 결과 표(domain/layer/depends/exports 중 1개 이상, 또는 신규 서브명령 결과 필드 1개 이상) 또는 명시적 인용문 존재"로, **판정 기준 자체는 이미 결정론적**이다 — 승격에 필요한 것은 새 기준이 아니라 새 **집행 주체**다.
- `state_tool.py`의 게이트 인프라 실측:
  - `err(command, code, message=None, exit_code=1, **kwargs)` — 단일 라인 JSON + **기본 exit 1**.
  - `_run_clarification_hook(task_path, state, row_index, command, auto_pass, force)` — 단계 전환 자동 훅의 **완성된 선례**. `cmd_advance`(`state_tool.py:1498`)와 `cmd_mark`(`state_tool.py:1789`)에서 **상태 변경 전 구간**에 각 1줄로 호출되며, 발동 조건 4단(단계 존재 / 대상 행 stage / 자기 stage 첫 행 / 직전 행 stage) → `auto_pass` 거부 → `force` 우회 → graceful skip 2단 → 판정 순서를 갖는다.
  - `find_project_root(task_path)`(`state_tool.py:695-702`) — 조상 중 `.opal/MEMORY.json` 보유 디렉토리 반환, 없으면 `None`. 프로젝트 루트 해석에 재사용 가능.
  - `check_gate_artifacts`/`build_gate_payload` — `gate.artifacts` 결정론 존재 검증 + `checklist` stdout 반환. `--force` 시 호출자가 의사결정 로그에 기재하는 우회 계약 보유.
  - `verify --evidence-check`(098/100) — 인용 4형식 파서(`_extract_citations`/`_grade_citation`)와 항상 exit 0 라우터. **인용 파싱 자산은 이미 존재**한다.
- **실측 (E1)**: `~/.opal/tools/state-tool/run.sh verify tasks/106-.../ --evidence-check` 실행 → `ok:true`·`evidence_check:"routed"`·exit 0. 배포본에서 `verify` 라우터가 정상 동작함을 확인.
- `pipeline.json` 실측 — `plan.pm_gate.gate.checklist` 항목 수: opd 4 / opds 4 / opp 3. `gate`는 `artifacts`·`checklist` 2필드이며 `validate_pipeline_spec`(`state_tool.py:1221-1236`)이 두 필드의 존재·타입·비공백만 검사하고 **미지 키를 거부하지 않는다**. 단 `schema/state.schema.json`의 `gate`는 `additionalProperties: false`이므로 **새 gate 필드 신설은 스키마 2파일 동반 변경을 유발** → 채택하지 않는다(DEC-2 근거 보강).

#### 2.4.3 영향 범위

- 직접: 위 5파일.
- 간접(중대): `_run_code_scan_citation_hook`은 `cmd_advance`/`cmd_mark` 공용 경로에 삽입되므로 **EXECUTE 단계를 보유한 8 파이프라인 전체**가 발동 반경이다 — 실측: opd(row 12) / opds(7) / opp(6) / opdw(6) / oppd(10) / oppl(13) / opsdd(18) / opwt(6). EXECUTE 미보유 2종(opdd·opgc)은 무영향.
- 간접: `todo_mirror_hook.py`는 `mark` stdout의 `todo_mirror` dict만 소비하므로, 신규 필드를 stdout에 얹지 않으면 무영향.
- 간접: `state.json`·`STATE.md` 스키마 **미접촉**(신규 영속 필드 0건) → 기존 태스크 폴더 하위호환 보존.

---

### F-005: 미보급 프로젝트 폴백

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | 훅 3중 graceful skip 게이트 + `reason` 계약 | 수정(F-004와 동일 Step) |
| 문서 | `opal/core/references/harness/pm-review-gate.md` | 항목 14 스킵 조건 3종 명시 | 수정(F-004와 동일 Step) |
| 문서 | `opal/core/references/harness/header-rules.md` | §갱신 시점 (d) 미발동 조건 명시 | 수정(F-002와 동일 Step) |

#### 2.5.2 현재 구현

- `code-map-hook.js:87-165` 조기 이탈 10단이 **직접 재사용 가능한 선례**다. ⑤단(모드 게이트, `:126-128`)과 ⑥단(자산 존재 게이트, `:131-132`)이 이 레포 상태를 무출력 exit 0으로 통과시키는 계약을 이미 구현한다.
- **[MUST]** `opal/tools/code-scan/code-map-hook.js:121-124`: "이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다" — 순서 자체가 계약이다. 신설 훅도 동일 원칙으로 자산 게이트를 판정 로직 **앞**에 배치한다.
- 이 레포 실측 — `.opal/code-scan.json`의 `headerSource: "inline"`, `.opal/code-map/` 디렉토리 **부재**(`ls .opal/` 결과 8항목 중 없음).

#### 2.5.3 영향 범위

- 직접: F-002·F-004 산출물 내부(별도 파일 0건).
- 간접: 이 레포에서 실행되는 모든 태스크의 EXECUTE 진입 — 3중 게이트가 없으면 전건 차단되는 최악 시나리오. H-6·H-7의 완화 수단이 곧 F-005다.

---

### F-006: 회귀 보존

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서(참고) | `opal/skills/opal-pilot-{dev,dev-short,project}/references/pipeline.json` | 회귀 대조 기준 | 무변경 대조 |
| 문서(참고) | `opal/skills/*/references/pipeline.json` (10종) | EXECUTE 보유 8종 훅 반경 대조 | 무변경 대조 |

#### 2.6.2 현재 구현

- 대조 기준값(ANALYSIS §8 승계 + PLAN 재실측 일치): opd **16행** / opds **11행** / opp **9행**. 10 pipeline 전수 행 수: opdd 15 / opds 11 / opdw 9 / opd 16 / opgc 7 / oppd 13 / oppl 19 / opp 9 / opsdd 25 / opwt 10.
- `state-tool spec-validate`가 `pipeline.json` 스펙 위반을 결정론 검증한다(`state_tool.py:1161` `validate_pipeline_spec`).

#### 2.6.3 영향 범위

- 직접: 없음(검증 전용).
- 간접: F-004 Step 4·5의 산출물 품질에 전적으로 의존.

---

## 3. 기능별 설계

### F-001: `opcmb` 스킬 신설 + 약어 등록

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-code-map-builder/SKILL.md` | 스킬 | `init`\|`update` 2모드 · `code-scan` 서브명령 호출층 | TASK R-1 / (→ D-12 §모드 판별) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 문서 | `groups.opal`에 `opcmb` 항목 1건 + `version` 3.13.0→3.14.0 + `updated_at` + `changelog` 1건 | (→ D-9) |
| 2 | `docs/CONVENTIONS.md` | 문서 | §약어 (Alias) 「프레임워크 운영」 표에 `opcmb` 행 + 결손 2건(`opgr`·`opeli5`) 보정 + 총계 27→30 | (→ D-8 §약어) |

#### 3.1.2 설계

**[MUST]** `docs/CONVENTIONS.md` §약어 (Alias): "SSOT: `opal/core/references/opal-skills-registry.json` — 약어의 등록·변경은 레지스트리에서만 수행한다." → 등록 행위는 Step 2(레지스트리)가 유일 원천이고 Step 3(CONVENTIONS)은 **사본 반영**이다. 순서를 뒤집지 않는다.

**[MUST]** `docs/CONVENTIONS.md` §네이밍 규칙 §파일/폴더: "스킬 폴더: `{그룹}-{역할}`" → `opal-code-map-builder`는 `opal-` 그룹 접두 + `code-map-builder` 역할로 이 규칙을 만족한다(kebab-case).

**[MUST]** `docs/CONVENTIONS.md` §변경이력: "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)" · "버전: semver (`vX.Y.Z`)" → 신설 SKILL.md의 변경이력 표와 개정 8문서의 행 삽입에 공통 적용한다.

**SKILL.md frontmatter 계약** (R-1 AC(a) — `opal-brain`·`opal-improve` 실측 형태 준용):

```yaml
name: opal-code-map-builder
description: |
  **@header 자산 구축·환경설정 스킬**. ...
  모드: init | update.
alias: opcmb
triggers:
  - "^opcmb$"
  - "^opal-code-map-builder$"
  - "(?i)(코드\\s*맵|code-?map|헤더\\s*자산)"
version: "1.0"
domain: metadata
```

**모드 판별 — 자산 존재 감지** (ANALYSIS §8 확정값 승계, → D-12 §모드 판별 준용):

| 조건 | 모드 |
|------|------|
| `.opal/code-scan.json` 부재 (또는 `headerSource` 미설정·무효) | **init** — 설정 확정부터 |
| `.opal/code-scan.json` 유효 + `headerSource: manifest` + `.opal/code-map/index.json` 부재 | **init** — 매니페스트 구축부터 |
| `.opal/code-scan.json` 유효 + `headerSource: manifest` + `index.json` 존재 | **update** |
| `.opal/code-scan.json` 유효 + `headerSource: inline` | **종료 분기** — `code-scan missing` 안내 반환 |

> `index.json`의 `status: draft|reviewed`는 **판별에 사용하지 않는다**(ANALYSIS §8 확정값) — 소유자 리뷰 완료 표시 전용이다 (→ D-1 §7.1 `status` 행).

**STEP 시퀀스** (ANALYSIS §7 Q7 승계, → D-3 §index.json PM·소유자 관리 의무 3단을 STEP 2~4에 사상):

| STEP | 행위 | 도구 호출 | 산출물 |
|------|------|----------|--------|
| 0 | 모드 판별 (위 표) | 파일 존재 확인 | 모드 확정 1줄 보고 |
| 1 | `headerSource` 2택을 소유자에게 제시 → 확정값 수령 | `code-scan init --header-source <값> --write` | `.opal/code-scan.json` |
| 1-x | `inline` 확정 시 **종료 분기** | `code-scan missing` | 미작성 파일 목록 + "이후 갱신은 하네스 §갱신 시점이 처리한다" 안내 |
| 2 | `manifest` — 초안 생성 | `code-scan discover [--out\|--dry-run]` | `.opal/code-map/index.json` (`status: draft`, `origin: discover`) |
| 3 | **소유자 리뷰 게이트** — `scopes`(root/anchors/stripPrefix/include/exclude)·`layerRules`·`domains` 요약 제시 후 승인 대기 | 없음 | 리뷰 요약 + 승인 |
| 4 | `status: draft` → `reviewed` 전환 | 없음(PM 또는 소유자 직접) | `index.json` 갱신 |
| 5 | 매니페스트 골격 생성 | `code-scan scaffold [--dry-run]` | `.opal/code-map/{scope}/*.json` |
| 6 | 무결성 확인 + 완료 보고 | `code-scan validate` | 커버리지·위반 요약 |

**소유자 리뷰 게이트 표현** (ANALYSIS 「PLAN 결정 필요」 4번째 항목 확정): 다른 pilot의 **"사용자 확인" 관용구를 그대로 사용**한다 — 산출물 요약 제시 → 승인 대기. code-map 전용 문구를 신설하지 않는다. 근거: (→ D-3 §index.json PM·소유자 관리 의무 2번) "도구는 도메인 경계·`include`/`exclude` 파일 집합 필터 정책을 판정하지 않는다"가 이미 리뷰 주체를 소유자로 못 박고 있어, 새 문구는 중복 규정이 된다.

**[MUST]** `opal/core/references/header-standard.md` §7: "`headerSource`는 프로젝트당 전역 1개다. … 두 소스는 모드에 의해 상호 배타이므로 경합·병합 규칙이 존재하지 않는다." → STEP 1의 2택은 **1회 확정**이며, 스킬은 모드 병합·자동 폴백·스코프별 재선언 경로를 만들지 않는다.

**레지스트리 항목** (→ D-9, `opi`/`opim` 항목 형태 준용):

| 키 | 값 |
|----|-----|
| `name` | `opal-code-map-builder` |
| `alias` | `opcmb` |
| `description` | `@header 자산(code-map 매니페스트) 구축·환경설정 — init \| update 2모드` |
| `triggers` | `["^opal-code-map-builder$", "^opcmb$", "(?i)(코드\\s*맵|code-?map|헤더\\s*자산)"]` |
| `paths` | `["~/.opal/skills/opal-code-map-builder/SKILL.md"]` |
| 소속 `group` | `opal` (프레임워크 운영) |

#### 3.1.3 환경 변경

해당 없음 — 신설 스킬 폴더는 `install-mac.sh:1236` 글롭 루프와 `scripts/install/windows.ps1:494-503` `$skillSrcs` 순회가 **자동 포함**한다(§8.4 install 배포 영향 실측 참조). 스크립트 수정 불요.

#### 3.1.4 배치/마이그레이션

해당 없음.

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(a) | 산출물 검사 | `opal/skills/opal-code-map-builder/SKILL.md` 존재 + frontmatter에 `name`·`description`·`alias`·`triggers`·`version` 5필드 전건 비공백 |
| TS-002 | R-1 AC(b) | 기능 테스트 | `skill-registry.js get opcmb` 단일 항목 반환 + `match "opcmb"` 단일 해석 + alias 총계 30종 + 중복 0건 |
| TS-003 | R-1 AC(c)(d) | 산출물 검사 | SKILL.md에 (i) 2택 제시 → `code-scan init --header-source <값> --write` 호출 절차 (ii) `manifest`의 `discover`→리뷰→`scaffold` 3단 (iii) `inline` 종료 분기 + `code-scan missing` 안내 반환이 각각 명시 |

---

### F-002: L2 경량 트랙 @header 갱신 검증 게이트

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/header-rules.md` | 문서 | §갱신 시점 (3단)→(4단): L2 완료 시점 행 (d) 추가 + 미발동(폴백) 조건 + 미수행 탐지 조건 | `header-rules.md:32-42` |
| 2 | `opal/core/references/opal-pm.md` | 문서 | §12 L2 표 「유지」 블록 1행 + 표 하단 축 구분 각주 1줄 | `opal-pm.md:202-216` |

#### 3.2.2 설계

**DEC-4 확정 — L2 완료 시점 감지 방식**

| 후보 | 판정 | 근거 |
|------|------|------|
| (α) 기존 PostToolUse hook(`code-map-hook.js`) 재사용 | **불충족 — 탈락** | ① `code-map-hook.js:126-128`이 `mode === 'inline'`에서 즉시 무출력 exit 0 → 이 레포처럼 inline 프로젝트에서는 **한 건도 검사하지 않는다**. ② manifest 모드에서도 출력이 `additionalContext` **경고**이며 차단이 아니다(`:158-165`) → R-2가 요구하는 "검증 게이트"가 성립하지 않는다. ③ 매 Edit 단위 발동이라 "완료 시점"이라는 축 자체가 없다 |
| (β) `git diff --name-only` + 기존 `code-scan validate --changed` | **채택** | ① git이 변경 파일 집합의 SSOT이므로 L2가 `state.json`을 경유하지 않아도 신호가 항상 재구성된다(ANALYSIS §4 발견 3). ② `validate --changed`는 **기존 서브명령**이므로 신규 도구 0건 — §2 Simplicity First 정합. ③ 실측으로 inline 모드 동작·`pre_existing` 비차단이 확인되어 폴백이 도구 계약으로 이미 보장된다 |
| (γ) L2 전용 신규 hook/도구 신설 | 탈락 | (β)가 기존 자산으로 충족하므로 **[MUST]** `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." 위반 |

**`header-rules.md` §갱신 시점 신설 행 (d)** — 표 제목 `(3단)`→`(4단)`, 도입문 "3개 시점"→"4개 시점":

| # | 시점 | 주체 | 수단 |
|---|------|------|------|
| (d) | **L2 경량 트랙 완료 시점** | PM | `git diff --name-only HEAD`(+ untracked)로 변경 파일을 재구성해 `code-scan validate --changed <목록>` 실행 — exit≠0(`counts.newly_uncovered` ≥1건)이면 **L2 종료 선언 전에** @header를 같은 자리에 기록한다 |

폴백(미발동) 조건 — **[MUST] 판정보다 앞에 평가한다** (→ D-10b `code-map-hook.js:121-124` 순서 계약 재사용):

1. `.opal/code-scan.json` 부재 또는 `headerSource` ∉ {`inline`, `manifest`} → 미발동
2. 변경 파일 중 code-scan 적용 대상 확장자가 0건(순수 `.md`·설정 수정 등, 프로젝트 `extensions` 기준) → 미발동
3. `uncovered:pre_existing`만 존재 → 도구가 exit 0을 돌려주므로 비차단 (레거시 소급 부여는 `discover`/`scaffold`의 몫 — (b) 행과 동일 계약)

미수행 탐지 조건 (R-2 AC(c)):

> (d) 미수행은 그 파일이 다음 태스크의 변경 대상이 될 때 (b) CLOSE 게이트에서 `counts.newly_uncovered`로 누적 탐지된다 — L2가 헤더를 남기지 않은 파일은 HEAD에 헤더가 없으므로 (b)의 `newly_uncovered` 판정에 걸린다. 즉 (d)는 (b)의 **선행 방어선**이며, 두 시점의 판정 수단은 동일 명령이다.

**DEC-3 확정 — `opal-pm.md` §12 문면**

| 후보 | 판정 | 근거 |
|------|------|------|
| (α) 표 「유지」 블록에 1행 추가 + 표 하단 축 구분 각주 1줄 | **채택** | `opal-pm.md:212`의 미적용 행은 "Gate (QA Gate, State Gate, PM Gate)"로 **파이프라인 게이트 3종을 열거**한다 — @header 갱신 검증은 파이프라인 행·`state.json`을 경유하지 않는 별개 축이므로 열거 대상 밖이다. 각주 1줄로 이 축 구분을 명문화하면 자기모순이 소멸한다 |
| (β) 별도 각주로만 분리(표 무변경) | 탈락 | R-2 AC(a) "§12 표에 @header 검증 행이 추가되고 적용 여부가 명시된다"를 문면상 충족하지 못한다 |
| (γ) 미적용 행 자체를 개정 | 탈락 | **[MUST]** `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." — 파이프라인 게이트 3종 규정은 이번 태스크의 대상이 아니다 |

신설 행(「유지」 블록, 기존 "@header 규칙" 행 바로 아래):

```
| **유지** | @header 갱신 검증 (L2 완료 시점 — `code-scan validate --changed`) | ✅ |
```

신설 각주(`opal-pm.md:216` 기존 각주 아래 1줄):

> ⚠️ 위 「미적용」의 "Gate"는 **태스크 파이프라인 게이트 3종**(QA Gate / State Gate / PM Gate)에 한정된다. @header 갱신 검증은 파이프라인 행·`state.json`을 경유하지 않고 변경 파일 목록이라는 객관 입력만으로 도구가 판정하는 **별개 축**이므로 미적용 대상이 아니다. 상세: `harness/header-rules.md` §갱신 시점 (4단) (d).

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-2 AC(a) | 산출물 검사 | `opal-pm.md` §12 「유지」 블록에 @header 검증 행 1건 + 축 구분 각주 1줄 존재 / 기존 「미적용」 5행 무변경 |
| TS-005 | R-2 AC(b) | 산출물 검사 | `header-rules.md` §갱신 시점 표 제목이 (4단) + (d) L2 완료 시점 행 존재 + (a)(b)(c) 3행 원문 무변경 |
| TS-006 | R-2 AC(c) | 산출물 검사 | (d) 미수행 탐지 조건이 "(b) CLOSE 게이트 `validate --changed` exit≠0"으로 명시 + 모드별 차단 사유 2종(`newly_uncovered` / `no_entry`)이 함께 기재 |

---

### F-003: 소비 2단 규율 명문화

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-pm.md` | 문서 | §13에 「2단 소비 절차」 표 신설 + 문언 모순 방지 1줄 + 오버라이드 구분 1줄 | `opal-pm.md:220-237` |
| 2 | `opal/core/references/pm/dispatch-process.md` | 문서 | §code-scan 사전 범위 파악 불릿 1건 추가(2차 전환 포인터) | `dispatch-process.md:126-135` |

#### 3.3.2 설계

**`opal-pm.md` §13 신설 표** (기존 활용 방법 표 아래, `opal-pm.md:237` 사용자 오버라이드 **위**):

| 단 | 수단 | 목적 | 전환 조건 |
|----|------|------|----------|
| 1차 | `code-scan scan`/`domain`/`layer`/`search`/`exports`/`depends` | **범위 축소** — 후보 파일 집합 확정 | 항상 먼저. 건너뛸 수 없다 |
| 2차 | Grep / Glob | **상세 확인** — 확정된 후보 파일 안의 본문·줄번호 확인 | 1차로 후보가 확정된 뒤. 또는 `harness/header-rules.md` §빈 결과 폴백 ①②(매칭 0건·커버리지 30% 미만) 발동 시 |

문언 모순 방지 1줄 (R-3 AC(c)):

> `pm/dispatch-process.md` §code-scan 사전 범위 파악의 "Glob/Grep 직행 금지"는 **1차를 건너뛴 직행**을 금지하는 것이고, 2차 전환은 1차를 수행한 뒤의 정당 경로다 — 두 규정은 적용 지점이 다른 별개 규칙이며 충돌하지 않는다.

소유자 오버라이드 구분 1줄 (R-3 AC(b)):

> 아래 **사용자 오버라이드**는 1차 자체를 면제하는 **소유자 권한 행사**이고, 위 2차 전환은 1차를 수행한 뒤의 **절차 진행**이다. 전자는 근거 인용 의무의 판정 대상이 아니며(`harness/citation-rules.md` §9 (f)), 후자는 1차 산출물이 전제 조건이다.

**`dispatch-process.md` 신설 불릿** (`:135` 기존 마지막 불릿 아래):

> - 1차 code-scan으로 후보를 확정한 뒤 상세 확인이 필요하면 Grep/Glob으로 전환한다 — 전환 규정의 원문은 `opal/core/references/opal-pm.md` §13 「2단 소비 절차」가 소유한다. 본 항목의 "Glob/Grep 직행 금지"는 1차를 건너뛴 직행을 금지하는 것이다.

> **[MUST]** `opal/core/references/harness/citation-rules.md` §2.2: "산출물에 소스코드 원문 블록을 기재하지 않는다" → 위 3개 삽입 문면은 모두 산문 1~2줄이며, 규정 원문 소유권은 §13에 단일화하고 `dispatch-process.md`는 포인터만 둔다(복제 금지).

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-3 AC(a)(b)(c) | 산출물 검사 | §13에 2단 표 존재(4열) + 전환 조건 명시 + 오버라이드 구분 1줄 + "Glob/Grep 직행 금지"와의 비모순 1줄 / `dispatch-process.md`에 포인터 불릿 1건이며 규정 원문 복제 0건 |

---

### F-004: 소비 집행 승격 (PM 자기판정 → 도구 판정)

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `_check_code_scan_citation`·`_collect_plan_target_files`·`_run_code_scan_citation_hook` 신설 + `cmd_verify` 분기 + `cmd_advance`/`cmd_mark` 호출 1줄씩 + `ERROR_CODES` 1종 + argparse 플래그 1종 + 파일 상단 `@header` 갱신 | `state_tool.py:2448`(선례)·`:1498`·`:1789` |
| 2 | `opal/core/references/harness/pm-review-gate.md` | 문서 | §표준 검토 항목 14 — 판정 수단·집행 지점·스킵 조건 3종으로 재작성(PM 자기판정 문구 제거) | `pm-review-gate.md:112-119` |
| 3 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 오케스트레이터 | `plan.pm_gate.gate.checklist` 1행 추가 (4→5) | 실측 |
| 4 | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 오케스트레이터 | 동일 (4→5) | 실측 |
| 5 | `opal/skills/opal-pilot-project/references/pipeline.json` | 오케스트레이터 | 동일 (3→4) | 실측 |

#### 3.4.2 설계

**DEC-1 확정 — 신설 검증 서브명령의 소속: `state-tool` 확장**

| 판단 축 | `state-tool` 확장 | `code-scan` 자체 서브명령 |
|---------|------------------|--------------------------|
| (i) 파이프라인 게이트 통합 편의 | **우위** — 1st 인자가 이미 태스크 폴더이며, `cmd_advance`/`cmd_mark`의 단계 전환 훅 지점(`state_tool.py:1498`·`:1789`)과 `--force --note` 우회·의사결정 로그 계약을 그대로 재사용한다 | 열위 — 태스크 폴더·`state.json`·의사결정 로그 개념이 전무하다. 게이트에 붙이려면 `state-tool`이 `code-scan`을 subprocess로 호출하는 층을 새로 만들어야 한다 |
| (ii) 도구 응집도 | **우위** — 판정 대상이 **PLAN.md(태스크 산출물)** 이므로 산출물 검증 도구의 관할이다. `verify`는 이미 TASK.md·TEST-SCENARIO.md를 판정한다 | 열위 — `code-scan`은 "@header 메타블록 스캔"이 자기 정의(`code-scan.js:118` USAGE)이며 PLAN.md 파서를 갖지 않는다. 태스크 산출물 판정을 넣으면 도구 정의가 깨진다 |
| (iii) `verify --evidence-check` 로직 재사용 비용 | **우위** — `_extract_citations`·`_locate_*`·`err(exit 1)`·플래그 상호배타 검사(`evidence_check_flag_conflict`)를 그대로 재사용. 신규 파서 0건 | 열위 — Node.js로 인용 파서를 새로 작성(중복 구현) |
| 배포·플랫폼 | 동등 — 둘 다 `~/.opal/tools/` 배포, 플랫폼 독립 | 동등 |

> **결론**: 3축 전건 `state-tool` 우위 → **`state-tool` 확장 채택**. `code-scan.js` **무변경**.

**DEC-5 확정 — `SubagentStop` hook 후보: 탈락(열위)**

| 판정 축 | 결과 |
|---------|------|
| 사전 차단 가능성 | **불가** — `SubagentStop`은 서브에이전트 **종료 후** 발동한다. R-4가 막으려는 것은 "인용 없는 디스패치"이므로, 이미 디스패치가 끝난 뒤의 발동은 목적을 달성하지 못한다 |
| 판정 대상 특정 | **불가** — 현 matcher는 `""`(전체)이며 hook payload에 태스크 폴더·PLAN.md 경로가 실리지 않는다. 어느 태스크의 어느 PLAN.md를 판정할지 결정할 입력이 없다 |
| 플랫폼 독립성 | **위반** — `opal/core/hooks/claude-hooks.json`은 Claude 전용 경로다. 집행을 여기 두면 Cursor·Gemini·Codex에서 규칙이 소멸한다. `docs/PROJECT.md` §프로젝트 원칙 3 "플랫폼 독립성" · `docs/CONVENTIONS.md` §플랫폼 분기 격리 위반 |
| 현 용도 결합 | 현 matcher는 osascript 알림 1줄 전용이다. 판정 파이프라인으로 전용하면 알림 기능과 결합되어 어느 쪽 실패가 다른 쪽을 죽인다 |
| **판정** | **탈락** — DEC-1 채택안 대비 4축 전건 열위. 채택하지 않는다 |

**DEC-2 확정 — `pipeline.json` 영향 방식: (i) 기존 게이트 행의 `gate.checklist` 확장**

| 후보 | 판정 | 근거 |
|------|------|------|
| (i) 기존 `plan.pm_gate.gate.checklist` 1행 추가 | **채택** | ① `task_steps` 행 수·key **불변** → R-6 AC(a) 원문 그대로 충족(재정의 불요). ② `schema/state.schema.json`의 `gate`는 `additionalProperties: false`이므로 새 gate 필드 신설은 스키마 2파일을 동반 변경시키는데, `checklist` 확장은 스키마 **무변경**이다. ③ `build_gate_payload`가 `checklist`를 `mark` stdout으로 결정론 반환하므로 PM 도달이 보장된다 |
| (ii) 신규 게이트 행 추가(opd 16→17 등) | 탈락 | R-6 AC(a)를 "무변경"에서 "의도된 증가 후 무결성 검증"으로 재정의해야 하고, 10 pipeline 중 3종만 행 수가 달라져 파이프라인 간 비대칭이 생긴다. 얻는 것은 없다 |

신설 `checklist` 항목 문면 (3 pipeline 공통 — 파이프라인 무관 표현):

```
"code-scan 결과 인용 — state-tool verify <태스크폴더> --code-scan-citation-check 통과 (코드 변경 태스크 한정, 문서 태스크는 skipped)"
```

> 삽입 위치: 각 `plan.pm_gate.gate.checklist` 배열 **말미**. 기존 항목의 문면·순서는 손대지 않는다 (**[MUST]** §3 Surgical Changes).

**신설 도구 계약 — `state_tool.py`**

(1) `_collect_plan_target_files(plan_md_path) -> list[str]`
- PLAN.md §4.2 각 Step의 `**파일**:` 라인에서 경로 토큰을 수집한다(쉼표·공백 분리, 백틱 제거).
- 반환은 경로 문자열 목록. 섹션·라인 부재 시 `[]`.

(2) `_check_code_scan_citation(plan_md_path) -> list[str] | None`
- 판정 기준은 **신설하지 않고** `pm-review-gate.md:118-119` 항목 14 Pass 조건을 그대로 집행한다 — 아래 토큰 중 **1건 이상** PLAN.md 본문에 존재하면 통과.

| 토큰군 | 토큰 |
|--------|------|
| 조회 계열 결과 필드 | `domain` · `layer` · `depends` · `exports` |
| code-map 계열 결과 필드 | `write_to` · `reason` · `coverage` · `counts` |
| 명령 인용 | `code-scan` (명령 문자열) |

- 반환: `[]`(통과) / `["citation_absent"]`(미충족) / `None`(§4.2 섹션 자체 부재 → 하위호환 skip).

(3) `_run_code_scan_citation_hook(task_path, state, row_index, command, auto_pass=False, force=False)`
- `_run_clarification_hook`(`state_tool.py:2448`) 구조를 준용한다. **게이트 순서가 계약이다** — **[MUST]** `opal/tools/code-scan/code-map-hook.js:121-124`: "이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다".

| # | 게이트 | 미해당 시 |
|---|--------|----------|
| ① | 발동 조건 — 대상 행 `stage == "EXECUTE"` **AND** 자기 stage의 첫 행(`row_index == 0 or rows[row_index-1]["stage"] != "EXECUTE"`) | `return` (무영향) |
| ② | `force` → **거부(`err`)만 무력화**하고 ③④⑤⑥⑦를 계속 통과시킨 뒤 `missing`을 반환 — 호출자(`cmd_mark`)가 그 반환값으로 `decision = code_scan_citation_force`를 기재한다 | 우회 허용(exit 0) |
> **[Step 18 개정]** 초판은 ②를 조기 `return`으로 설계했으나, 그러면 문서 전용·미보급 프로젝트의 `--force`까지 전부 의사결정 로그에 기재되어 오탐이 발생하고 091 `gate_artifact_force`(실제 미충족만 기재)와 비대칭이 된다. 조기 반환을 제거하고 「거부만 무력화」로 바꿔 **실제로 거부될 상태에서만** 기재한다. 게이트 순서 계약(①→⑦)과 그 보호 대상(조용히 이탈해야 할 트리에서 거부·출력 금지)은 보존된다 — ⑥⑦의 `err`가 force에서 발생하지 않으므로 force 경로의 exit code·stdout이 종전과 동일하다.
| ③ | **자산 게이트 (F-005)** — `find_project_root(task_path)`가 `None`, 또는 `<root>/.opal/code-scan.json` 부재, 또는 `headerSource` ∉ {`inline`,`manifest`} | `return` (`code_scan_unavailable`) |
| ④ | **산출물 게이트** — `<task_path>/PLAN.md` 부재 | `return` (하위호환) |
| ⑤ | **적용 범위 게이트 (F-005)** — `_collect_plan_target_files()` 결과에 code-scan 적용 확장자가 0건(프로젝트 `extensions` 기준) | `return` (`doc_only_task`) |
| ⑥ | `auto_pass` → 우회 불가(`err`) | **[MUST] ③④⑤ 뒤에 둔다** — 앞에 두면 문서 전용 태스크에서 거부가 발생해 R-5 오탐 0건이 깨진다(H-7). `_run_clarification_hook`의 배치를 그대로 답습하지 않는다 |
| ⑦ | 판정 — `_check_code_scan_citation()`가 `None`이면 `return`, `[]`이면 `return`, 그 외면 `err(command, "code_scan_citation_unmet", ...)` | exit 1 |

- 호출 지점: `cmd_advance`(`state_tool.py:1498` `_run_clarification_hook` 호출 직후) · `cmd_mark`(`:1789` 직후) 각 1줄. **`save_state_json()` 이전 검증 구간**이므로 거부 시 파일이 오염되지 않는다.

(4) `ERROR_CODES` 1종 추가

```
"code_scan_citation_unmet": "PLAN.md에 code-scan 결과 인용 없음 — EXECUTE 진입 차단 (pm-review-gate.md 항목 14): {missing}"
```

(5) `verify` 라우터 분기 — `p_vfy.add_argument("--code-scan-citation-check", action="store_true", dest="code_scan_citation_check", ...)`
- `cmd_verify`의 `evidence_check` 분기 **뒤**, `fix_mode` 분기 **앞**에 배치.
- `--clarification-check`·`--evidence-check`와 동시 지정 시 기존 `evidence_check_flag_conflict` 패턴과 동형으로 거부한다(무성 무시 방지).
- 반환 JSON: `{"ok": true|false, "command": "verify", "code_scan_citation_check": "pass"|"skipped"|"unmet", "reason": <skip 사유>, "target_files": [...], "matched_tokens": [...]}`
- exit: `pass`/`skipped` → 0, `unmet` → `err(..., exit_code=1)`.
- 스킵 사유 도메인은 훅과 동일 3값으로 닫는다 — `code_scan_unavailable` / `plan_md_absent` / `doc_only_task`.

**(6) 파일 상단 `@header` 갱신 (H-8)** — `state_tool.py:6` `description` 필드에 이번 변경 요약을 기존 관행대로 태스크 번호(`106`) 접두로 추가하고, `exports`에 신설 함수 3종을 추가한다. **[MUST]** `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다."

**`pm-review-gate.md` 항목 14 재작성 문면** (5요소 유지 + 판정 주체 교체):

| 요소 | 개정 후 |
|------|--------|
| 트리거 조건 | (기존 유지) `changed_files` 또는 `target`에 code-scan 지원 확장자 포함 |
| 검증 내용 | (기존 유지) PLAN.md Step 본문에 code-scan 결과가 인용되었는가 |
| **판정 수단** | **신설** — `~/.opal/tools/state-tool/run.sh verify <태스크폴더> --code-scan-citation-check`. exit 0 = `pass`\|`skipped`, exit≠0 = `code_scan_citation_unmet`. **PM 자기판정 문구 제거** |
| **집행 지점** | **신설** — EXECUTE 단계 첫 행의 `advance`/`mark`가 동일 판정을 자동 재실행해 진입을 차단한다. `--force --note`로만 우회하며 우회 시 의사결정 로그에 기록된다 |
| **스킵 조건 3종 (F-005)** | **신설** — ① `.opal/code-scan.json` 부재·`headerSource` 무효 ② PLAN.md 부재 ③ PLAN.md §4.2 대상 파일에 code-scan 적용 확장자 0건(순수 문서 태스크) |
| 판정 | (기존 유지) 인용 부재 시 Fail → 재디스패치 1회 |
| Pass 조건 | (기존 유지) — 도구가 이 조건을 그대로 집행한다는 1줄 추가 |

> **[MUST]** `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." → 판정(verdict)은 도구가 결정론으로 내고, PM은 실행·보고만 한다. 항목 14에서 PM이 "인용했는지 스스로 판단"하는 문면은 남기지 않는다.

#### 3.4.3 환경 변경

해당 없음(신규 패키지 0건). 단 `~/.opal/` 재배포가 R-4 AC(b)(c) 실측의 **전제 조건**이다(H-11) → §4.2 Step 14.

#### 3.4.4 배치/마이그레이션

`state.json` 스키마 무변경 → 마이그레이션 해당 없음. 기존 태스크 폴더는 게이트 ④(PLAN.md 부재) 또는 ⑤(적용 범위)에서 자연 스킵된다.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-4 AC(a) | 산출물 검사 | PLAN.md에 후보 3종(state-tool / code-scan / SubagentStop) 비교표와 확정 1종 + 탈락 근거가 명시 |
| TS-009 | R-4 AC(b) | 기능 테스트 | 인용 토큰 0건 PLAN.md + 코드 확장자 대상 파일을 가진 임시 태스크 폴더에서 `verify --code-scan-citation-check` → `ok:false`·`error: code_scan_citation_unmet`·**exit 1**. 동일 폴더에서 EXECUTE 첫 행 `mark` → 동일 코드로 거부 + `state.json` 무변경 |
| TS-010 | R-4 AC(c) | 기능 테스트 | 인용 토큰 ≥1건 PLAN.md에서 `verify --code-scan-citation-check` → `code_scan_citation_check: "pass"`·exit 0. EXECUTE 첫 행 `mark` 정상 진행 |
| TS-018 | 제약 ⑤ / DEC-6 | 산출물 검사 | 개정 8문서 각각의 변경이력 마커·컬럼 순서가 DEC-6 표의 기존 형태와 일치 + 행 1건 추가(태스크 번호 `(106)` 포함) |

---

### F-005: 미보급 프로젝트 폴백

#### 3.5.1 파일 변경 계획

**수정** — 전건 F-002·F-004 Step에 동봉(별도 파일 0건).

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | 훅 게이트 ③⑤ + `reason` 3값 도메인 | Step 4에 포함 |
| 2 | `opal/core/references/harness/pm-review-gate.md` | 문서 | 항목 14 스킵 조건 3종 | Step 6에 포함 |
| 3 | `opal/core/references/harness/header-rules.md` | 문서 | §갱신 시점 (d) 미발동 조건 3종 | Step 7에 포함 |

#### 3.5.2 설계

폴백 설계 원형은 `code-map-hook.js` 조기 이탈 순서를 그대로 재사용한다(ANALYSIS §8 확정값 승계):

```
[hook.js 선례]   ⑤ 모드 게이트(inline 즉시 이탈)  →  ⑥ 자산 존재 게이트(index.json)  →  판정
[신설 훅]        ③ 자산 게이트(code-scan.json·headerSource)  →  ④ PLAN.md  →  ⑤ 적용 범위  →  ⑥ auto_pass  →  ⑦ 판정
[신설 (d) 행]    1 자산 게이트  →  2 적용 범위(확장자 0건)  →  3 pre_existing 비차단  →  validate 실행
```

> **[MUST] 순서를 바꾸지 않는다** — `opal/tools/code-scan/code-map-hook.js:121-124`가 순서 자체를 계약으로 못 박고 있으며, 게이트를 자산 로딩·판정 아래로 내리면 조용히 통과해야 할 트리에서 출력·거부가 발생한다.

이 레포의 기대 판정(오탐 0건 조건):

| 집행 경로 | 이 레포에서의 기대 결과 | 이탈 게이트 |
|-----------|----------------------|-----------|
| R-2 (d) L2 게이트 — 문서만 수정한 L2 | 미발동 | 적용 범위(확장자 0건) |
| R-2 (d) L2 게이트 — 코드 수정 L2 | 발동, `pre_existing`만이면 exit 0 | 도구 계약(비차단) |
| R-4 훅 — 문서 태스크(태스크 106 자신) | `doc_only_task` skip, exit 0 | ⑤ 적용 범위 |
| R-4 훅 — 코드 태스크 + 인용 보유 | `pass`, exit 0 | ⑦ 판정 통과 |
| R-4 훅 — `.opal/code-scan.json`이 없는 타 프로젝트 | `code_scan_unavailable` skip, exit 0 | ③ 자산 게이트 |

> `headerSource: inline` + code-map 부재는 **정상 상태**이며 훅·게이트는 `manifest` 자산 존재를 요구하지 않는다 — ③은 `code-scan.json`의 존재·유효성만 본다. code-map 부재를 조건으로 걸면 inline 프로젝트 전건이 스킵되어 R-4가 무력화된다.

#### 3.5.3 환경 변경 / 3.5.4 배치·마이그레이션

해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-5 AC(a) | 기능 테스트 | 이 레포에서 ① 태스크 106 폴더 대상 `verify --code-scan-citation-check` → `skipped`(`doc_only_task`)·exit 0 ② `.md`만 변경한 목록으로 `validate --changed` → exit 0 ③ 오탐(거부·경고 발화) **0건** |
| TS-012 | R-5 AC(b) | 산출물 검사 | 폴백 조건이 3곳에 명시 — `state_tool.py` 훅 게이트 ③⑤ + `reason` 3값 / `pm-review-gate.md` 항목 14 스킵 조건 3종 / `header-rules.md` (d) 미발동 조건 3종. 게이트 순서가 판정보다 앞임을 주석 또는 문면으로 확인 |

---

### F-006: 회귀 보존

#### 3.6.1 파일 변경 계획

변경 없음(검증 전용).

#### 3.6.2 설계 — R-6 AC 최종 문면 (DEC-2 (i) 반영)

> DEC-2에서 **행 수 불변** 방식을 택했으므로 AC(a)(b)는 TASK.md 원문을 그대로 유지하고, 신설 훅의 발동 반경(H-6)을 덮기 위해 (c)(d) 2건을 **추가**한다.

- **(a)** *(원문 유지)* opd/opds/opp의 `task_steps` 행 수·key가 개정 전후 동일하다.
  - 대조 기준값: **opd 16 / opds 11 / opp 9**, key 집합 동일. `gate.checklist` 항목 수 변화(opd 4→5 / opds 4→5 / opp 3→4)는 행 수·key를 바꾸지 않으므로 (a) 위반이 아니다. `gate` 필드 집합은 `artifacts`·`checklist` 2종 불변이며 `schema/state.schema.json` 무변경이다.
- **(b)** *(원문 유지)* 기존 태스크 폴더에서 `state-tool show`가 오류 없이 동작한다.
- **(c)** *(신설)* EXECUTE 단계를 보유한 8 파이프라인(opd·opds·opp·opdw·oppd·oppl·opsdd·opwt)에서 신설 훅이 **graceful skip 또는 정상 판정으로만** 동작하며, 조건 미해당 경로의 exit code와 stdout 키 집합이 개정 전과 동일하다. EXECUTE 미보유 2종(opdd·opgc)은 무영향이다.
- **(d)** *(신설)* `state-tool spec-validate`가 개정된 3개 `pipeline.json`에 대해 violations **0건**을 반환한다.

#### 3.6.3 환경 변경 / 3.6.4 배치·마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-6 AC(a) | 회귀 테스트 | 3 `pipeline.json`의 `len(task_steps)` = 16/11/9 + key 집합 개정 전후 동일(git diff에 `key`·`id`·`stage`·`item` 변경 0건) |
| TS-014 | R-6 AC(b) | 회귀 테스트 | 최근 태스크 3폴더 이상에서 `state-tool show <path>` exit 0 + 오류 0건 |
| TS-015 | R-6 AC(c) | 회귀 테스트 | 8 파이프라인 각각에서 EXECUTE 첫 행 진입 시 훅이 skip 또는 pass. 조건 미해당 호출의 stdout 키 집합이 개정 전과 동일 |
| TS-016 | R-6 AC(d) | 회귀 테스트 | `state-tool spec-validate` × 3 → violations 0건 |
| TS-017 | 완료기준(install) | 기능 테스트 | `./scripts/install-mac.sh` 후 `~/.opal/skills/opal-code-map-builder/SKILL.md` 존재 + `~/.opal/references/opal-skills-registry.json`에 `opcmb` 반영 + install 스크립트 diff 0건 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2, 3 | opal-task-agent / PM 직접 | 순차 | 레지스트리는 SKILL.md 이후, CONVENTIONS는 레지스트리 이후 |
| 2 | F-004, F-005 | 4 | opal-be-agent | 단독 | Python 도구 코드. 최장 임계 경로 |
| 2-b | F-004 | **15** | opal-be-agent | Step 5·6과 병렬 | **PM 추가** — `ERROR_CODES` 45→46 종수 단언 6건 + README 카탈로그 (Step 4 파생) |
| 3 | F-004 | 5, 6 | opal-task-agent | 병렬 가능 | 독립 파일(3 json / 1 md). Step 4의 명령명·에러코드 확정 후 |
| 4 | F-002, F-003, F-005 | 7, 8+9, 10 | opal-task-agent | 8·9는 **같은 디스패치**(동일 파일 `opal-pm.md`) | Phase 1~3과 독립 — 병렬 가능 |
| 5 | F-006 | 11, 12 | opal-task-agent / PM 직접 | 순차 | 전 Step 완료 후 |
| 6 | 부속 | 13, 14 | PM 직접 | 순차 | docs/ 갱신 → install 재배포 |

> **산출량 상한** (`pm/dispatch-process.md` Step 6): 단일 디스패치 산출 파일 3개 초과 금지. Phase 3은 Step 5(3파일)·Step 6(1파일)로 분할했다. Step 8·9는 동일 파일이므로 분할하지 않고 한 디스패치에 묶어 순차 편집한다.

### 4.2 실행 체크리스트

> 총 **19개 Step**(원 14 + PM 추가 5 — Step 15·16 PLAN 결손 보강, Step 17·18 TEST Fail 해소, Step 19 검증 2원화) | Phase **6개** | 실행 모드: **복잡**

#### Step 1: `opal-code-map-builder` SKILL.md 신설

- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-code-map-builder/SKILL.md` (신규)
- **작업 내용**: §3.1.2의 frontmatter 계약(5필드) · 모드 판별 4분기 표(자산 존재 감지) · STEP 0~6 시퀀스 표를 그대로 구현한다. `inline` 종료 분기는 `code-scan missing` 안내 반환으로 닫고, 소유자 리뷰 게이트는 기존 "사용자 확인" 관용구를 사용한다. 문서 말미에 `## 변경이력` 표(`버전 | 일시 | 변경내용`, v1.0 초기 작성 `(106)`)를 둔다.
- **완료 기준**: (a) frontmatter `name`·`description`·`alias`(=`opcmb`)·`triggers`·`version` 5필드 비공백 (b) 모드 판별 4분기 중 `inline` 종료 분기가 `code-scan missing` 반환을 명시 (c) `manifest` 경로가 `init`→`discover`→소유자 리뷰→`status: reviewed`→`scaffold`→`validate` 순으로 기술 (d) `headerSource` 병합·자동 폴백·스코프별 재선언 경로를 신설하지 않음 (e) `## 변경이력` 표 v1.0 행 존재
- **테스트**: TS-001, TS-003
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: 스킬 레지스트리에 `opcmb` 등록

- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: `groups.opal` 배열 말미에 §3.1.2 레지스트리 항목 표대로 1건 추가한다(`name`/`alias`/`description`/`triggers`/`paths` — `opi` 항목 형태 준용). `version` 3.13.0→**3.14.0**, `updated_at`을 KST 오늘 날짜로 갱신하고 `changelog` 배열에 항목 1건(`version` 3.14.0, `task` "106")을 추가한다.
- **완료 기준**: (a) `opcmb` 항목 1건 (b) alias 총계 **30종** + 중복 0건 (c) `skill-registry.js get opcmb`·`match "opcmb"`가 단일 해석 반환 (d) JSON 파싱 성공 (e) 기존 29종 항목 무변경 (f) `changelog` 행 1건 추가
- **테스트**: TS-002
- **실행 방법**: sub-agent
- **의존**: Step 1 (등록 대상 SKILL.md 실물이 선행해야 `paths` 유효)

#### Step 3: `docs/CONVENTIONS.md` 약어 표 사본 갱신

- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: §약어 (Alias) 「프레임워크 운영」 표에 `opcmb` 행을 추가하고, 실측 결손 2건(`opgr`·`opeli5`)을 함께 보정한 뒤 도입문 총계를 "현재 **27종**"→"현재 **30종**"으로 고친다(H-9). 근거: 본 표가 스스로 "레지스트리의 사본"임을 선언하므로 사본 정합 회복은 규정 집행이다.
- **완료 기준**: (a) 표 항목·총계가 레지스트리 실측 30종과 1:1 일치 (b) `## 변경이력` 표(`버전 | 일시 | 변경내용`)에 v1.9.0 행 1건 추가, 변경내용에 `(106)` 포함 (c) 약어 표 외 절 무변경
- **테스트**: TS-002, TS-018
- **실행 방법**: direct
- **의존**: Step 2 (레지스트리가 SSOT — 사본은 그 뒤)

#### Step 4: `state_tool.py` — 인용 검증 라우터 + EXECUTE 진입 자동 훅 신설

- [x] 완료
- **소속 기능**: F-004, F-005
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: §3.4.2 (1)~(6)을 구현한다 — `_collect_plan_target_files` / `_check_code_scan_citation` / `_run_code_scan_citation_hook` 3함수 신설, `ERROR_CODES`에 `code_scan_citation_unmet` 1종 추가, `cmd_verify`에 `--code-scan-citation-check` 분기(`evidence_check` 뒤·`fix_mode` 앞) + 플래그 상호배타 거부, `cmd_advance`(`:1498` 직후)·`cmd_mark`(`:1789` 직후)에 훅 호출 각 1줄, 파일 상단 `@header` `description`·`exports` 갱신. **게이트 순서 ①~⑦을 표 그대로 배치하고 `auto_pass` 거부(⑥)를 graceful skip(③④⑤) 뒤에 둔다.**
- **완료 기준**: (a) 게이트 ①~⑦ 순서가 코드에 그대로 구현되고 ⑥이 ③④⑤ 뒤에 위치 (b) `verify --code-scan-citation-check` 반환 JSON의 `code_scan_citation_check` 3값(`pass`/`skipped`/`unmet`) · `reason` 3값(`code_scan_unavailable`/`plan_md_absent`/`doc_only_task`)으로 도메인이 닫힘 (c) `unmet` 시 exit 1, 그 외 exit 0 (d) `state.json`·`STATE.md`·`schema/*.json` **무변경**(신규 영속 필드 0건) (e) 훅 호출이 `save_state_json()` **이전** 검증 구간에 위치 (f) 파일 상단 `@header` `description`에 `106` 접두 요약 + `exports`에 신설 3함수 추가 (g) `code-scan validate --changed opal/tools/state-tool/state_tool.py` exit 0
- **테스트**: TS-009, TS-010, TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: 3 pipeline.json의 `plan.pm_gate.gate.checklist` 확장

- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev-short/references/pipeline.json`, `opal/skills/opal-pilot-project/references/pipeline.json`
- **작업 내용**: 각 파일의 `plan.pm_gate.gate.checklist` 배열 **말미**에 §3.4.2 신설 문면 1행을 추가한다. `task_steps` 행 추가·삭제·`key`/`id`/`stage`/`item` 변경, `gate.artifacts` 변경, 새 `gate` 필드 신설을 하지 않는다.
- **완료 기준**: (a) `checklist` 길이 opd 4→5 / opds 4→5 / opp 3→4 (b) `len(task_steps)` = 16/11/9 불변 + key 집합 불변 (c) `gate` 필드 집합이 `artifacts`·`checklist` 2종 불변 (d) `state-tool spec-validate` × 3 → violations 0건 (e) 기존 checklist 항목의 문면·순서 무변경
- **테스트**: TS-013, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 4 (checklist 문면이 신설 명령명을 인용)

#### Step 6: `pm-review-gate.md` 항목 14 집행 승격

- [x] 완료
- **소속 기능**: F-004, F-005
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/pm-review-gate.md`
- **작업 내용**: §표준 검토 항목 14(`:112-119`)를 §3.4.2 재작성 표대로 고친다 — **판정 수단**(`verify --code-scan-citation-check` + exit 규약)·**집행 지점**(EXECUTE 첫 행 자동 훅 + `--force --note` 우회)·**스킵 조건 3종**을 신설하고 PM 자기판정 문구를 제거한다. 기존 트리거 조건·검증 내용·판정·Pass 조건은 유지한다. 항목 8·13은 손대지 않는다.
- **완료 기준**: (a) 항목 14에 판정 수단·집행 지점·스킵 조건 3종이 존재 (b) "PM이 판정한다" 계열 문면 0건 (c) 스킵 조건이 F-005 폴백 3종과 문면 일치 (d) 항목 1~13·자가 진단 절 무변경 (e) `## 변경이력` 표(`버전 | 날짜 | 내용`)에 v1.11 행 1건 추가, `(106)` 포함
- **테스트**: TS-012, TS-018
- **실행 방법**: sub-agent
- **의존**: Step 4 (도구 계약·에러코드 확정 후)

#### Step 7: `header-rules.md` §갱신 시점 (4단) — L2 완료 시점 행 신설

- [x] 완료
- **소속 기능**: F-002, F-005
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/header-rules.md`
- **작업 내용**: §갱신 시점 표 제목 `(3단)`→`(4단)`, 도입문 "3개 시점"→"4개 시점"으로 고치고 §3.2.2의 (d) 행을 추가한다. 이어 폴백(미발동) 조건 3종과 미수행 탐지 조건 1문단을 표 아래에 기재한다. (a)(b)(c) 3행 원문과 `[MUST]` 일괄 갱신 금지 문단, §워커 권한 경계 이하는 손대지 않는다.
- **완료 기준**: (a) 표 제목 (4단) + (d) 행 존재 (b) (a)(b)(c) 원문 무변경 (c) 폴백 3종이 "판정보다 앞에 평가한다"는 순서 계약과 함께 기재 (d) 미수행 탐지 조건이 (b) CLOSE 게이트 `validate --changed` exit≠0으로 명시되고, **모드별 차단 사유 2종**(`inline` = `counts.newly_uncovered` ≥1 / `manifest` 관리 하위 = `violations[].sub == "no_entry"`)이 함께 기재 — `code-scan.js:3207`이 관리 매니페스트 하위 누락을 git 무관하게 `no_entry`로 분류하고 `:3434-3436` 차단 필터가 이를 통과시키지 않으므로, `newly_uncovered` 단독 인용은 manifest 모드를 포괄하지 못한다 (e) **변경이력이 인라인형** — `## 변경이력` 헤딩을 만들지 않고 기존 `변경이력:`(`:149`) 형태를 유지하며 `버전 | 일시 | 변경내용` 표에 v1.9 행 1건 추가, `(106)` 포함 (DEC-6)
- **테스트**: TS-005, TS-006, TS-012, TS-018
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 8: `opal-pm.md` §12 — L2 표 유지 행 + 축 구분 각주

- [x] 완료
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: §L2 하네스 적용 범위 표(`:202-214`)의 「유지」 블록에서 기존 "@header 규칙" 행 바로 아래에 §3.2.2 신설 행 1건을 추가하고, `:216` 각주 아래에 축 구분 각주 1줄을 추가한다. 「미적용」 5행(특히 `:212` Gate 행)은 손대지 않는다.
- **완료 기준**: (a) 「유지」 블록 5행(기존 4 + 신설 1) (b) 「미적용」 5행 원문 무변경 (c) 축 구분 각주가 "파이프라인 게이트 3종 한정"과 `header-rules.md` §갱신 시점 (4단) (d) 포인터를 포함 (d) §12 그 외 절 무변경
- **테스트**: TS-004
- **실행 방법**: sub-agent
- **의존**: Step 7 (각주가 (4단) (d)를 인용) · **Step 9와 동일 디스패치**

#### Step 9: `opal-pm.md` §13 — 2단 소비 절차 명문화

- [x] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: §13(`:220-237`)의 활용 방법 표 아래·사용자 오버라이드(`:237`) **위**에 §3.3.2의 「2단 소비 절차」 4열 표를 신설하고, 문언 모순 방지 1줄과 소유자 오버라이드 구분 1줄을 함께 기재한다. 기존 활용 방법 5행 표·원칙 문단·`brain ↔ code-scan` 역할 분담 표는 손대지 않는다.
- **완료 기준**: (a) 4열(단/수단/목적/전환 조건) 2행 표 존재 (b) 2차 전환 허용 조건이 "1차 후보 확정 후" 또는 "빈 결과 폴백 ①②"로 명시 (c) 오버라이드와의 구분 1줄 존재 (d) "Glob/Grep 직행 금지"와의 비모순 1줄 존재 (e) `:237` 오버라이드 문단 원문 무변경 (f) `## 변경이력` 표(`버전 | 날짜 | 내용`)에 v2.5 행 1건 추가, `(106)` 포함 — Step 8·9 통합 1행으로 기재
- **테스트**: TS-007, TS-018
- **실행 방법**: sub-agent
- **의존**: Step 8 (동일 파일 순차 편집 — 같은 디스패치에 묶는다)

#### Step 10: `dispatch-process.md` — 2차 전환 포인터 보강

- [x] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**: §code-scan 사전 범위 파악(`:126-135`)의 마지막 불릿 아래에 §3.3.2 신설 불릿 1건(2차 전환 포인터)을 추가한다. 규정 원문은 복제하지 않고 `opal-pm.md` §13을 가리킨다. `:130` 무조건 호출 문면과 `:134` 직행 금지 문면은 손대지 않는다.
- **완료 기준**: (a) 포인터 불릿 1건 추가 (b) 규정 원문 복제 0건(§13 포인터만) (c) `:130`·`:134` 원문 무변경 (d) `## 변경이력` 표(`버전 | 날짜 | 변경내용`)에 v1.10 행 1건 추가, `(106)` 포함
- **테스트**: TS-007, TS-018
- **실행 방법**: sub-agent
- **의존**: Step 9 (포인터 대상 §13이 선행)

#### Step 11: 훅 발동 반경 회귀 대조 (8 파이프라인)

- [x] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: (검증 전용 — 파일 변경 0건. 관측 결과는 `STATE.md` 자유 기재 1줄)
- **작업 내용**: EXECUTE 단계를 보유한 8 파이프라인(opd·opds·opp·opdw·oppd·oppl·opsdd·opwt)에 대해 신설 훅의 발동 경로를 실측한다 — 임시 태스크 폴더에 각 `pipeline.json`으로 `state-tool init` 후 EXECUTE 첫 행 `advance`를 호출하고, 스킵 사유·exit code·stdout 키 집합을 개정 전 기준선과 대조한다. EXECUTE 미보유 2종(opdd·opgc)은 무영향 확인만 한다.
- **완료 기준**: (a) 8종 전건에서 skip 또는 pass만 관찰(예기치 않은 거부 0건) (b) 조건 미해당 호출의 stdout 키 집합이 개정 전과 동일 (c) 임시 폴더는 관측 후 정리 (d) 관측 스코프와 실행 명령을 결과에 병기 (**[MUST]** `harness/citation-rules.md` §9 (a): E1 인용은 관측 스코프·실행 명령 병기 의무)
- **테스트**: TS-015
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 5, Step 14 (배포본 실행 — H-11)

#### Step 12: 회귀·폴백 실측 검증

- [x] 완료
- **소속 기능**: F-005, F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: (검증 전용 — 파일 변경 0건)
- **작업 내용**: ① 3 `pipeline.json`의 `len(task_steps)`·key 집합을 git diff로 대조 ② `state-tool spec-validate` × 3 ③ 최근 태스크 3폴더 이상에서 `state-tool show` ④ 이 레포에서 `verify --code-scan-citation-check`(태스크 106 폴더) → `skipped`/`doc_only_task` ⑤ `.md`만 담은 목록으로 `code-scan validate --changed` → exit 0.
- **완료 기준**: (a) 행 수 16/11/9 + key 집합 동일 (b) spec-validate violations 0건 (c) `show` 오류 0건 (d) ④⑤ 모두 exit 0 + 오탐 0건 (e) 각 실행 명령·스코프를 결과에 병기
- **테스트**: TS-011, TS-013, TS-014, TS-016
- **실행 방법**: direct
- **의존**: Step 5, Step 14

#### Step 13: docs/ 갱신 — 스킬 수 셀 정합

- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`, `docs/ARCHITECTURE.md`
- **작업 내용**: 신설 스킬 1건 반영으로 스킬 수 셀을 **실측값**으로 갱신한다 — `docs/PROJECT.md:37`(42종), `docs/ARCHITECTURE.md:77`·`:217`·`:425`(42개). 개정 시점 `find opal/skills -mindepth 1 -maxdepth 1 -type d | wc -l` 실측값(현재 44 + 신설 1 = **45**)을 쓴다. 기존 드리프트 2건이 함께 해소되며(H-12), 스킬 수 셀 외에는 어떤 문장도 손대지 않는다.
- **완료 기준**: (a) 4개 셀 값이 실측값과 일치 (b) 스킬 수 셀 외 무변경 (c) 두 문서의 `## 변경이력` 표에 각 1행 추가(`docs/PROJECT.md`는 `일시 (KST) | 버전 | 변경 내용` 형태 확인 후 기존 형태 준수), `(106)` 포함
- **테스트**: TS-018 + `find` 실측 대조
- **실행 방법**: direct
- **의존**: Step 1

#### Step 14: install 재배포 + 배포본 실측

- [x] 완료
- **소속 기능**: F-001, F-004
- **영역**: 환경
- **agent**: PM 직접
- **파일**: (스크립트 변경 0건 — `scripts/install-mac.sh`·`scripts/install/windows.ps1` 실측 결과 수정 불요)
- **작업 내용**: `./scripts/install-mac.sh`로 재배포한 뒤 ① `~/.opal/skills/opal-code-map-builder/SKILL.md` 존재 ② 배포본 레지스트리에 `opcmb` 반영 ③ `~/.opal/tools/state-tool/run.sh verify --help`에 신설 플래그 노출을 확인한다. **[MUST]** `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- **완료 기준**: (a) 3항목 전건 확인 (b) install 스크립트 2파일 git diff 0건 (c) 배포본 SKILL.md에서 변경이력 절이 strip된 상태 확인(`install-mac.sh` strip 동작 정상)
- **테스트**: TS-017
- **실행 방법**: direct
- **의존**: Step 1 ~ Step 10


#### Step 15: `ERROR_CODES` 종수 단언 6건 + README 카탈로그 종수 갱신 [PM 추가 — PLAN 결손 보강]

- [x] 완료
- **소속 기능**: F-004
- **영역**: 도구(테스트·문서)
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`, `opal/tools/state-tool/README.md`
- **추가 근거**: Step 4가 `ERROR_CODES`에 `code_scan_citation_unmet` 1종을 등재해 종수가 45→46이 되었고, 종수·키집합 단언 6건이 실패한다(PM 실측: `374 passed, 6 failed`). 원 PLAN에 이 Step이 없었다 — **098이 동일 문제를 H-10 「테스트 선갱신」으로 흡수한 선례**가 있으며(`test_state_tool.py:2501` 주석 `[098 H-10 선갱신]`), 106에는 대응 Step이 누락됐다. Step 4 Guards가 두 파일을 금지 대상으로 뒀으므로 워커가 스스로 고칠 수 없었다.
- **작업 내용**: 실패 6건의 기대값을 45→**46**으로 갱신하고 `EXPECTED_CODES` 목록에 `code_scan_citation_unmet`를 추가한다. `README.md`는 `:136`("에러 코드는 45종 그대로다")·`:392` 카탈로그 헤더 종수·표 말미에 `| 46 | code_scan_citation_unmet | ... |` 행 1건을 반영한다(`test_s7_error_catalog_marker_import_realignment`가 README 종수를 대조하므로 두 파일이 함께 맞아야 한다).
- **대상 단언 6건**: `TestErrorCodesCompleteness::test_error_codes_count` · `::test_all_28_codes_registered` · `::test_s7_error_catalog_marker_import_realignment` · `TestR11Invariants::test_r11_invariants_S40`(subcheck `error_codes_key_set_untouched`) · `TestT103WorkerDuration::test_s10_error_codes_untouched` · `TestT103WorkerDurationWarning::test_w13_warning_catalog_is_separate_from_error_codes`
- **완료 기준**: (a) `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → **0 failed** (b) 기존 통과 케이스 374건 **감소 0건** (c) 기대값 변경이 종수·키집합 단언에 한정 — 동작 검증 케이스의 단언을 고치지 않는다 (d) README 카탈로그 46종 + 행 1건 추가 + `:136` 문면 정정 (e) `state_tool.py` **무변경**(Step 4 산출물 보존) (f) README `## 변경이력` 표에 행 1건 추가, `(106)` 포함
- **테스트**: TS-013(회귀), 신설 TS-019(테스트 스위트 0 failed)
- **실행 방법**: sub-agent
- **의존**: Step 4


#### Step 16: `state-tool/README.md` — `verify --code-scan-citation-check` 절 신설 [PM 추가 — PLAN 결손 보강 2]

- [x] 완료
- **소속 기능**: F-004
- **영역**: 도구(문서)
- **agent**: PM 직접
- **파일**: `opal/tools/state-tool/README.md`
- **추가 근거**: Step 15 워커가 보고 — Step 4가 신설한 `--code-scan-citation-check`를 **산문으로 설명하는 README 절이 어느 Step에도 배정되지 않았다**. PM 실측: README `:275`에 `### verify` 절이 실재하며 다른 플래그(`--red-check`·`--fix-mode`·`--clarification-check`·`--evidence-check`)를 열거하는 구조인데 신규 플래그만 빠졌다. **선례 098 v1.8**은 카탈로그 정정과 함께 `verify --evidence-check` 신규 절을 README에 추가했다 — 106에 그 대응이 없었다.
- **작업 내용**: `### verify` 절 도입문의 분기 열거에 `--code-scan-citation-check` 추가 + 상호배타 3종으로 정정. `#### --code-scan-citation-check` 하위 절 신설 — 판정 대상(PLAN.md §4.2 본문)·반환 3값·스킵 `reason` 3값 + 순서 계약·집행 지점 2곳·플래그 상호배타·영속 무변경·규정 SSOT 포인터. `## 변경이력` v1.14 행 1건.
- **완료 기준**: (a) 도입문 분기 열거에 신규 플래그 포함 (b) 하위 절 존재 + `reason` 3값 전건 기재 (c) `[MUST] 판정보다 앞에 평가한다` 순서 계약 기재 (d) 변경이력 v1.14 행 `(106)` 포함 (e) 종수 대조 테스트 회귀 0건
- **실측 결과**: `#### --code-scan-citation-check` 절 `:369` 신설, README numstat `+33/-5`, `pytest -k "ErrorCodes or R11Invariants"` → **27 passed** 회귀 0건
- **테스트**: TS-019(회귀)
- **실행 방법**: direct
- **의존**: Step 4, Step 15


#### Step 17: `opcmb` SKILL.md STEP 3·4·6 보강 [PM 추가 — TEST S-20 Fail 해소]

- [x] 완료
- **소속 기능**: F-001 | **agent**: opal-task-agent | **파일**: `opal/skills/opal-code-map-builder/SKILL.md`
- **추가 근거**: TEST S-20 Fail — STEP 3·4가 `discover`의 빈 `layerRules`·`domains`를 소유자가 채운다는 지시를 빠뜨렸고, STEP 6이 `validate` exit 0을 완료 조건처럼 읽히게 서술했다. 워커 보조 실측으로 값 기입 시 exit 0 도달 확인 → **도달 불가가 아니라 문면 결손**
- **실측 결과**: 229행 → **268행**. 음성 경로(빈 값 미확정 강행) 재완주로 **S-20 Fail 관측값 재현**(`uncovered:incomplete` detail `layer,domain` + `draft`), 정상 경로는 골격 완료 exit 2·커버리지 100%, 기입 후 exit 0. 모드 판별 4분기·§경계 절 무변경, 변경이력 v1.1
- **완료 기준**: (a) STEP 3 빈 값 소유자 확정 지시 + 근거 인용 (b) STEP 4 `reviewed` 전환 전 반영 확인 (c) STEP 6 정상 종료 2종 구분 + 완료 보고 3항 (d) 기존 절 무변경 (e) 변경이력 v1.1 (f) 삭제 라인 대상 절 한정 — **전건 충족**

#### Step 18: code-scan 인용 게이트 `force` 우회 의사결정 로그 정합 [PM 추가 — TEST S-25 ① Fail 해소]

- [x] 완료
- **소속 기능**: F-004 | **agent**: opal-be-agent | **파일**: `opal/tools/state-tool/state_tool.py`
- **추가 근거**: TEST S-25 ① Fail — `pm-review-gate.md` 항목 14가 "우회 사실은 의사결정 로그에 남는다"고 단언하나 `cmd_mark`가 `decision`을 `worker_scope_force`·`gate_artifact_force` 2경로에서만 설정했다(**문서↔집행 불일치**). PM 확정 방향: **문서를 낮추지 않고 구현을 문서에 맞춘다**(091 선례 `gate_artifact_force` 강제 기록과의 비대칭 해소)
- **실측 결과**: `+26/-8`. `decision = code_scan_citation_force` 기재 확인 · **`ERROR_CODES` 46 불변**(사유 키는 `decision` 문자열, 에러 코드 아님) · 오탐 0건 대조군 2건(문서 전용·인용 존재 + force → 무기재) · 기존 2 경로 코드 무변경(force 관련 테스트 **31 passed**) · `pytest` **379 passed / 0 failed** · @header 순증 **+2바이트** · `cmd_advance`는 `--force` 인자 부재 실측으로 미변경(불가능 시나리오 방어 금지)
- **완료 기준**: (a)~(f) **전건 충족**

#### Step 19: code-scan 인용 게이트 동작 케이스 회귀 고정 [PM 추가 — 검증 2원화]

- [x] 완료
- **소속 기능**: F-004 | **agent**: opal-test-agent | **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **추가 근거**: Step 18 워커 보고 — `test_state_tool.py`에 인용 게이트의 **동작** 케이스가 0건이고 106 반영은 종수 단언 6건뿐이다. Step 18의 신규 계약이 회귀 테스트로 고정되어 있지 않다. **작성자는 구현자(Step 18 = opal-be-agent)와 분리한다**(H-9 검증 2원화)
- **작업 내용**: 4케이스 신설 — ① 인용 0건 + `--force --note` → `code_scan_citation_force` 기재 ② 문서 전용 태스크 + force → 무기재(오탐 0건) ③ 인용 존재 + force → 무기재 ④ `--auto-pass` 단독 거부 불변(게이트 ⑥ 회귀)
- **완료 기준**: (a) 4케이스 전건 통과 (b) 기존 379 passed 감소 0건 (c) mock 미사용 — `run.sh` subprocess 실호출 + 실 파일 상태 (d) `ERROR_CODES` 종수 46 불변 (e) @header 창문 순증 ≈ 0
- **의존**: Step 18

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 레지스트리 `paths`가 SKILL.md 실물을 가리킨다 |
| Step 2 → Step 3 | **[MUST]** `docs/CONVENTIONS.md` §약어: "약어의 등록·변경은 레지스트리에서만 수행한다" — 사본은 SSOT 이후 |
| Step 4 → Step 5 | `checklist` 문면이 신설 명령명·플래그를 인용 |
| Step 4 → Step 6 | 항목 14 판정 수단·에러코드가 도구 계약에 종속 |
| Step 7 → Step 8 | §12 각주가 §갱신 시점 (4단) (d)를 포인터로 인용 |
| Step 8 → Step 9 | **동일 파일**(`opal-pm.md`) 순차 편집 — 같은 디스패치에 묶어 후행 저장의 선행 덮어쓰기를 방지 (`pm/dispatch-process.md` Step 6) |
| Step 9 → Step 10 | 포인터 대상 §13이 선행 |
| Step 1‖Step 4‖Step 7 | 독립 파일·독립 기능 — Phase 1·2·4 병렬 가능 |
| Step 5 ‖ Step 6 | 독립 파일(3 json / 1 md) |
| Step 14 → Step 11, 12 | 배포본으로 실측해야 판정이 유효(H-11) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | SKILL.md frontmatter 5필드 + 2모드 분기 문면 | TS-001, TS-003 | 5필드 비공백 · `inline` 종료 분기가 `code-scan missing` 반환 명시 · `manifest` 6-STEP 시퀀스 존재 |
| F-001 | 레지스트리 등록 + 사본 정합 | TS-002 | `get`/`match` 단일 해석 · alias 30종 · 중복 0 · CONVENTIONS 표 1:1 일치 |
| F-002 | L2 게이트 2문서 문면 | TS-004, TS-005, TS-006 | §12 유지 행 + 축 구분 각주 · (4단) (d) 행 · 미수행 탐지 조건 명시 |
| F-003 | 2단 소비 절차 + 비모순 | TS-007 | 4열 2행 표 · 전환 조건 · 오버라이드 구분 · 직행 금지와 비모순 |
| F-004 | 도구 판정 승격 (양성·음성) | TS-008, TS-009, TS-010 | 인용 부재 exit 1(`code_scan_citation_unmet`) · 인용 보유 exit 0(`pass`) · `state.json` 무변경 |
| F-005 | 이 레포 오탐 0건 + 폴백 문면 | TS-011, TS-012 | `doc_only_task` skip exit 0 · `validate --changed` exit 0 · 폴백 조건 3곳 명시 · 게이트 순서 판정보다 앞 |
| F-006 | 파이프라인 회귀 0 | TS-013 ~ TS-016 | 행 수 16/11/9 + key 동일 · spec-validate 0건 · `show` 오류 0 · 8 파이프라인 skip/pass만 |

### 5.2 회귀 테스트

- [ ] 3 `pipeline.json`의 `task_steps` 행 수(16/11/9)·`key`·`id`·`stage`·`item` 개정 전후 동일
- [ ] `state-tool spec-validate` × 3 → violations 0건
- [ ] `schema/state.schema.json`·`schema/pipeline-spec.schema.json` git diff 0건
- [ ] 기존 태스크 폴더 3건 이상에서 `state-tool show` exit 0
- [ ] EXECUTE 보유 8 파이프라인에서 훅이 skip 또는 pass만 (예기치 않은 거부 0건)
- [ ] EXECUTE 미보유 2종(opdd·opgc) 무영향
- [ ] `--auto-pass`가 실린 문서 전용 태스크의 EXECUTE 진입이 exit 0 통과 (H-7)
- [ ] `code-scan.js`·`code-map-hook.js` git diff 0건 (DEC-4·DEC-1의 귀결)
- [ ] `verify --evidence-check`·`--clarification-check` 기존 3경로 exit 0 동작 불변
- [ ] install 스크립트 2파일 git diff 0건

### 5.3 코드/문서 품질

- [ ] 개정 8문서 + 신설 1문서의 변경이력이 **문서별 기존 형태**(DEC-6 표)를 준수 — 마커 형태·컬럼 순서·정렬 방향
- [ ] 변경내용에 태스크 번호 `(106)` 포함, 일시 `YYYY-MM-DD HH:mm` KST, 버전 semver
- [ ] 규정 원문 복제 0건 — 2단 소비 절차 원문은 `opal-pm.md` §13 단일 소유, 폴백 순서 계약 원문은 `code-map-hook.js` 주석 단일 소유(포인터만 둔다)
- [ ] `state_tool.py` 파일 상단 `@header` 갱신(`description`·`exports`) → `code-scan validate --changed` exit 0
- [ ] **[MUST]** `harness/citation-rules.md` §2.2 준수 — 산출물에 소스코드 원문 블록 0건
- [ ] `~/.opal/` 직접 편집 0건 (전 변경이 프로젝트 소스 → install 경로)
- [ ] 플랫폼 조건문 신설 0건 (`claude-hooks.json` 무변경 — DEC-5 귀결)

### 5.4 보안

- [ ] 신설 코드에 하드코딩 토큰·시크릿 0건
- [ ] `_collect_plan_target_files`가 수집한 경로를 파일 열기에 사용하지 않는다(확장자 판정 전용) — 경로 조작·디렉토리 탈출 표면 0
- [ ] 에러 메시지에 절대경로·홈 디렉토리 노출 0건 — 기존 `_redact_path_like()` 계열 관행 준수(094 SEC-FOLLOWUP 선례)
- [ ] `--force` 우회 시 의사결정 로그 기록 경로가 살아 있음(무성 우회 0건)
- [ ] 임시 태스크 폴더(Step 11)가 검증 후 정리되어 잔여 산출물 0건

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 14개 | 복잡 |
| 변경 파일 수 | 13개 (신규 1 + 수정 12) | 복잡 |
| 모듈 범위 | 다중 — 스킬/가이드/오케스트레이터/도구/문서 5축 | 복잡 |
| 작업 유형 | 신규 개발(스킬 1종) + 도구 집행 배선 + 하네스 개정 | 복잡 |
| 외부 의존성 | 없음(신규 패키지·MCP 0건) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬)
├─ A1 [opal-be-agent]    Step 4                      (state_tool.py 1파일)
├─ A2 [opal-task-agent]  Step 1 → 2                  (SKILL.md, registry 2파일)
└─ A3 [opal-task-agent]  Step 7 → 8+9 → 10           (header-rules, opal-pm, dispatch-process 3파일)

Batch 2 (A1 완료 후, 병렬)
├─ A4 [opal-task-agent]  Step 5                      (pipeline.json ×3)
└─ A5 [opal-task-agent]  Step 6                      (pm-review-gate.md 1파일)

Batch 3 (PM 직접, 순차)
└─ Step 3 → Step 13 → Step 14

Batch 4 (배포 후 검증)
├─ A6 [opal-task-agent]  Step 11
└─ Step 12 [PM 직접]
```

**그룹핑 근거**:
1. **파일 충돌 방지** — Step 8·9가 모두 `opal-pm.md`를 수정하므로 A3 단일 에이전트에 순차 배치. 동일 파일을 두 배치로 쪼개지 않는다.
2. **모듈 응집도** — Python 도구(A1)와 Markdown 규정(A3)을 분리해 전문 에이전트 매핑에 정합시킨다.
3. **산출량 상한** — 각 에이전트의 산출 파일이 3개 이하다(A1:1 / A2:2 / A3:3 / A4:3 / A5:1).
4. **임계 경로** — Step 4(A1) → Step 5·6(Batch 2) → Step 14 → Step 11·12. A2·A3는 이 경로와 독립이므로 Batch 1 병렬로 흡수한다.

### C-2. 스킬 요구사항

| 요구 | 매칭 | 판정 |
|------|------|------|
| 신설 SKILL.md의 OPAL 규격 준수 | `opal-skill-creator`(osc) | **패턴 참고용** — 직접 호출하지 않는다. §3.1.2가 frontmatter·구조를 이미 확정했고, osc는 레지스트리 등록까지 자동 수행해 Step 2의 수동 통제(version/changelog 문면)와 이중화된다 |
| Python 도구 수정 | 기존 스킬 없음 | 인라인 지침(§3.4.2 계약)으로 충분 — Step 1건뿐이므로 스킬 후보 아님 |
| 문서 개정 4건 | 기존 스킬 없음 | 인라인 지침. 동일 패턴이 3 Step 이상이지만(Step 7·8·9·10) 문면이 각기 달라 스킬화 이득이 없다 |

> 신규 스킬 갭 **0건** — 이번 태스크에 추가 스킬 신설은 필요하지 않다.

### C-3. 도구 요구사항

| 도구 | 용도 | 신규 설치 |
|------|------|----------|
| `code-scan` | `validate --changed`(H-8 자기 검증) · `missing`(F-001 종료 분기 문면 확인) | 불요 (기존) |
| `state-tool` | `spec-validate`·`show`·`init`·`advance`·`verify` (회귀·훅 반경 실측) | 불요 (기존) |
| `skill-registry` | `get`/`match`/`validate` (TS-002) | 불요 (기존) |
| `date` | 변경이력 KST 일시 취득 (추측 금지) | 불요 (기존) |
| `scripts/install-mac.sh` | 배포 (Step 14) | 불요 (기존) |
| MCP | — | 불요 — 외부 라이브러리 조사 0건 |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 |
|------|------|------|
| L1 산출물 검사 | TS-001, TS-003 ~ TS-008, TS-012, TS-018 | 문면·구조 검사(grep/파싱). 파일 변경 없이 판정 |
| L2 도구 실행 | TS-002, TS-009 ~ TS-011, TS-013, TS-014, TS-016, TS-017 | **배포본**으로 실행(H-11). 양성·음성 표본 2케이스 필수(TS-009/TS-010) |
| L2 회귀 | TS-015 | 임시 태스크 폴더 × 8 파이프라인. 정리 필수 |
| 기준선 | 개정 전 `git stash` 또는 `git show HEAD:<path>` 기반 stdout 키 집합·exit code 비교 | TS-015의 "개정 전과 동일" 판정 근거 |

> `opal-test-agent` 디스패치는 불요하다 — 유닛 테스트 프레임워크 대상 코드가 아니라 CLI 관측·문면 검사이며, `opal/tools/state-tool/tests/`의 기존 테스트가 있으면 그 스위트를 함께 돌린다(TEST 단계 판단).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 프레임워크 문서·스킬 | Markdown + YAML frontmatter | op-dev-plan(본 스킬), 인라인 지침 |
| 도구 | Python 3 (`state_tool.py`) | 인라인 지침 (§3.4.2 계약) |
| 도구(무변경 대조) | Node.js (`code-scan.js` v1.6.0, `code-map-hook.js`) | — |
| 설정·스펙 | JSON (`opal-skills-registry.json` v3.13.0, `pipeline.json`, `schema/*.json`) | — |
| 배포 | Bash (`install-mac.sh`), PowerShell (`install/windows.ps1`) | — |

> **§6.2 델타**: 변경 없음(SSOT 그대로) — ANALYSIS §6.2 승계. 전체 스택은 `docs/PROJECT.md`가 SSOT이며 재기재하지 않는다.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 순수 프레임워크 내부 문서·도구 개정. 외부 라이브러리 조사 불요 (ANALYSIS §2·§6.4 승계) |

### 8.3 참조 문서 (설계 결정 근거)

> ANALYSIS.md §0 참조 문서 표(D-1 ~ D-16)를 그대로 승계한다. 재조사 0건.

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §7 2소스 표현·§7.1~7.5 필드·상속 계약 — 병합 금지 제약의 원천 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §갱신 시점 (3단)·§빈 결과 폴백 — F-002 개정 대상 |
| D-3 | 설계 | code-scan.json PM 관리 의무 | `opal/core/references/pm/code-scan-management.md` | §생성 시점·§headerSource 최초 설정 절차·§index.json PM·소유자 관리 의무 — F-001 절차 원천 |
| D-4 | 설계 | OPAL PM 행동 프로세스 | `opal/core/references/opal-pm.md` | §12 L2 트랙·§13 code-scan 활용 규칙 — F-002·F-003 개정 대상 |
| D-5 | 설계 | PM 디스패치 전 프로세스 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악·Step 6 산출량 상한 — F-003 개정 대상 + 배치 규율 |
| D-6 | 설계 | PM 검토 게이트 | `opal/core/references/harness/pm-review-gate.md` | §표준 검토 항목 14 — F-004 개정 대상 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | §Core Stance enforce · §2 Simplicity First · §3 Surgical Changes |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | §네이밍·§약어 (Alias)·§변경이력·§@header 규칙·§배포 경계·§플랫폼 분기 격리 |
| D-9 | 소스 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 약어 SSOT — 실측 29종, `opcmb` 미등록 |
| D-10 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | USAGE 15서브명령 계약(`:118-175`) — F-001 호출층 |
| D-10b | 소스 | code-map hook | `opal/tools/code-scan/code-map-hook.js` | 조기 이탈 10단 + 순서 계약 주석(`:121-124`) — F-005 폴백 원형 |
| D-11 | 설계 | 모드 라우팅 선례 | `opal/skills/opal-brain/SKILL.md` | 명시 라우팅(첫 인자) — F-001 후보(탈락) |
| D-12 | 설계 | 2모드 자동 판별 선례 | `opal/skills/opal-project-init/SKILL.md` | 자산 존재 감지 — F-001 채택 방식 |
| D-13 | 설계 | OPAL 하네스 | `opal/core/references/opal-harness.md` | §8 Lazy 트리거·§9 도구 표 — 등재 불요 판정 근거 |
| D-14 | 소스 | PM Gate 정의 SSOT | `opal/skills/opal-pilot-{dev,dev-short,project}/references/pipeline.json` | 회귀 대조(F-006) + `gate.checklist` 확장 대상 |
| D-15 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | `_run_clarification_hook` 선례·`err` exit 규약·`find_project_root`·`verify` 라우터 — F-004 구현 원천 |
| D-16 | 소스 | hook 설정 | `opal/core/hooks/claude-hooks.json` | PostToolUse 2 matcher + `SubagentStop` 1 matcher — DEC-5 판정 근거 |
| D-17 | 소스 | state-tool 스키마 | `opal/tools/state-tool/schema/state.schema.json` | `gate`의 `additionalProperties: false` — DEC-2 근거 보강 (PLAN 신규) |
| D-18 | 소스 | install 스크립트 | `scripts/install-mac.sh`, `scripts/install/windows.ps1` | 스킬 배포 글롭 루프 — §8.4 배포 영향 실측 (PLAN 신규) |
| D-19 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §2.2 원문 블록 금지 · §9 (a) E1 스코프 병기 · §9 (f) 결정 비판정 |
| D-20 | 설계 | 분석 코어 | `opal/core/references/harness/analysis-core.md` | §5 영역 축(프레임워크 태스크) · §6 영향 범위 도출 (PLAN 신규) |

### 8.4 install 배포 영향 — 실측 결과

| 확인 항목 | 실측 | 결론 |
|----------|------|------|
| macOS 배포 — OPAL 스킬 복사 | `scripts/install-mac.sh:1236` `for skill_dir in "$opal_dir/skills"/*/;` 글롭 루프 + `:1235` `find … -type d \| wc -l` 동적 계수 | **신설 폴더 자동 포함**. 하드코딩 스킬명 목록 **0건**(`grep opal-project-init scripts/install-mac.sh` → 0건) |
| Windows 배포 — 스킬 복사 | `scripts/install/windows.ps1:494-503` `$skillSrcs = @(skills, opal\skills)` 순회 + `Copy-Item -Recurse`, `:508` 동적 계수 | **자동 포함** |
| 배포본 클린 대상 | `install-mac.sh:1208` `clean_dirs=("skills" …)` / `windows.ps1:441` 동일 | 재배포 시 `~/.opal/skills/` 전체 교체 — 신설 스킬 반영 보장 |
| 레지스트리 배포 | `references`가 clean+재배포 대상 | `opal-skills-registry.json` 갱신분 자동 전파 |
| 변경이력 strip | `install-mac.sh:1243` `strip_deploy_md_recursive` / `windows.ps1:506` `Remove-ChangelogRecursive` | 소스 유지·배포본 제거 (`docs/CONVENTIONS.md` §변경이력 작성 의무 정합) |
| **스크립트 수정 필요 여부** | — | **불요** — Step으로 넣지 않는다. 대신 Step 14에서 배포 결과를 실측 확인한다(TS-017), 완료 기준에 "install 스크립트 2파일 git diff 0건"을 명시 |

> `.opal/AGENT.md` PM 검토 기준 "부트스트래퍼·MCP 등 배포 영향 항목이 install 스크립트에 반영되었는가" → **반영 불요**(동적 열거로 이미 커버). 부트스트래퍼·MCP 변경 0건.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 신설 훅이 EXECUTE 보유 8 파이프라인 전체에서 발동 (H-6) | F-004 | 기존 태스크 진입 차단 | 게이트 ③④⑤ 3중 graceful skip을 판정보다 앞에 배치 + Step 11에서 8종 전수 실측 + `--force --note` 탈출구 유지 |
| 2 | `auto_pass` 거부 위치를 선례대로 앞에 두면 문서 태스크 오탐 (H-7) | F-004, F-005 | R-5 AC(a) 실패 | ⑥을 ③④⑤ 뒤로 배치하도록 Step 4 완료 기준 (a)에 명문화 |
| 3 | `state_tool.py` `@header` 미갱신 → 다음 CLOSE 자기 차단 (H-8) | F-004 | CLOSE 진입 불가 | Step 4 완료 기준 (f)(g)에 `@header` 갱신 + `validate --changed` exit 0 편입 |
| 4 | 배포 미반영 상태 실측 → 판정 무의미 (H-11) | F-004, F-005 | 검증 신뢰도 0 | Step 14를 Step 11·12의 **선행 의존**으로 배치 |
| 5 | L2 게이트 표 원칙 자기모순 (H-1, ANALYSIS 승계) | F-002 | PM 판단 분기 | DEC-3 — 유지 행 + 축 구분 각주. 미적용 행 원문 무변경 |
| 6 | 변경이력 형태 이종(헤딩형 7 / 인라인형 1 / 컬럼 순서 1) (H-3, 승계) | 전 F | 표 파손 | DEC-6 표를 각 Step 완료 기준에 문서별로 인라인 명시 |
| 7 | `pipeline.json` 행 증설 시 R-6 충돌 (H-4, 승계) | F-004, F-006 | AC 재정의 강요 | DEC-2 (i) — `checklist` 확장으로 행 수 불변. `gate` 필드 신설 회피(스키마 무변경) |
| 8 | 인용 판정 미탐/오탐 (H-10) | F-004 | 게이트 무력화 또는 과차단 | 판정 기준을 신설하지 않고 `pm-review-gate.md:118-119` Pass 조건을 그대로 집행 + TS-009/TS-010 양성·음성 2표본 필수 |
| 9 | alias 표 사본 결손 2건 (H-9) | F-001 | 사본 총계 재오류 | Step 3에서 `opgr`·`opeli5` 동반 보정 + 총계 30종 |
| 10 | docs/ 스킬 수 셀 드리프트 (H-12) | F-001 | 문서 신뢰도 저하 | Step 13에서 `find` 실측값 사용(+1 산술 금지) |
| 11 | PreToolUse `Task` hook 부재 (H-2, 승계) | F-004 | 플랫폼 종속 집행 | DEC-1·DEC-5 — hook 경로 전건 탈락, `state-tool`(플랫폼 독립)로 확정. `claude-hooks.json` 무변경 |
| 12 | 용어 일관성 — "게이트"가 파이프라인 게이트와 도구 판정 양쪽을 지칭 (`citation-rules.md` §7.1 검출 의무) | F-002, F-004 | 문서 간 오독 | DEC-3 각주가 축을 명시 분리. F-004 문면은 "판정 수단"·"집행 지점"으로 용어를 분리하여 파이프라인 게이트 3종과 혼동을 차단. `decision_required` 에스컬레이션 대상은 아님(동일 개념의 다른 토큰이 아니라 다른 개념의 같은 토큰이며, 각주로 해소됨) |

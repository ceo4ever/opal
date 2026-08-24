# PLAN: ANALYSIS 분석 코어 공유 SSOT 신설

> 작성일: 2026-08-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (F-001~F-008)

## 결론

- 8개 기능 / 13개 Step / **6개 Phase**(문서 체인 3 + docs 갱신 1 + state-tool 병렬 트랙 1 + 마무리 1), **복잡 모드**. 개수 SSOT는 §4.1 표다.
- PLAN 결정 4건: ① `confirmed_ratio`는 **분리형**(기존 키 의미 불변 + `direction_confirmed_ratio` 신설) ② 하네스 「해당 §」는 **§2 재사용 + §2 하위 stub 서브섹션 신설**(최상위 절 신설 금지) ③ `analysis.pm_gate.checklist`는 **4항목**으로 확정 ④ MUST 트리거 관용구 잔존은 **R-9 AC 위반 아님**(판정식 교체 + 트리거 예외 명문화).
- H-7 대응: R-5 Q표는 **강도 「권장」 유지**(결정 G 준수) + **배치는 템플릿 실물 섹션**(산문 금지)으로 이원 처리한다.
- H-4 대응: `qa-dev-guide.md`와 거울 사본 `op-dev-qa/SKILL.md`는 **Step 7 단일 Step**에서 함께 갱신한다(분리 금지).
- H-6 유지: `state_tool.py` 변경은 재배포 전까지 워커 런타임에 미반영 — Step 11·13 완료 기준에 "소스 GREEN까지가 완료, 런타임 반영은 범위 밖"을 명시했다.
- 범위 확장 2건(소유자 확인 필요): `opal/tools/state-tool/README.md`(계약 문서 정합, Step 11 편입) · `docs/ARCHITECTURE.md`·`docs/PROJECT.md`(Step 12).
- AC-G1은 Step 11(R-10 GREEN) 선행조건으로 배선했고, AC-G4는 이번 회차 측정 불가로 확정 승계했다.
- **분량 목표(500줄) 초과 사유**: 요구사항 12 · 기능 8 · Step 13 · TS 36 · 리스크 14를 형식 계약(§2.N.1 / §3.N.5 / §4.2 Step 10필드 / §5.1)대로 전개하면 표·Step 골격만으로 하한이 형성된다 — 산문을 압축하고 판정표를 그룹 병합해도 900줄 선이 최소치다.

---

## 확정 입력 판정

> TASK.md `[결정]` 16건은 재설계 대상이 아니다(SKILL.md §확정 입력 소비 규약). `[사실]` 6건은 ANALYSIS.md §확정 입력 판정에서 `유효(대조 확인)` 판정을 이미 받았으므로 **승계**하며 재확인하지 않는다.

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 16건 전건 — A(선조회 3단) · C(SSOT 수렴) · D(MCP 복제 제거) · F(기술 컨텍스트 승격) · G(Q표 권장) · H(핸드오프 표) · I(덤프 차단) · E(PM Gate 보강) · J(plan-guide 동일 개정) · K(재확인 면제) · L(PLAN 승계) · 배치(harness/analysis-core.md) · 역할 분리 · B 흡수 · 목표 달성 측정 · 임계 기준 | 해당없음(결정) | 재설계 면제 — `~/.opal/skills/op-dev-plan/SKILL.md` §확정 입력 소비 규약 |
| [사실] 6건 전건 — evidence-check 라우터·exit 0 / 파싱 대상=명확화 결과 표만 / ANALYSIS는 [결정]만 면제 / PLAN 재사용 지시 위치·강도 / brain 선별·stale 스냅샷 / E5 단독 인용 금지 | 승계 | ANALYSIS.md §확정 입력 판정에서 전건 `유효(대조 확인)` — 재확인하지 않는다 |

---

## PLAN 결정 4건 (ANALYSIS 「PLAN 결정 필요」 소비)

### PD-1. `confirmed_ratio` 분모 — **분리형 채택**

- **결정**: 기존 `confirmed_ratio` 키는 **분모·의미를 불변**으로 유지(명확화 결과 항목 전용)하고, `## 확정된 설계 방향` 항목은 신규 키 `direction_confirmed_ratio`로 **분리 반환**한다. `items[]`·`unconfirmed[]`는 **병합**하되 각 item에 `source` 필드(`clarification` \| `confirmed_direction`)를 추가한다.
- **근거**: 기존 키의 분모를 늘리면 값 형식이 동일해 소비자가 파괴를 감지하지 못하는 **조용한 계약 파괴**가 된다(`opal/tools/state-tool/state_tool.py:2554-2557`의 `len(items)` 분모, `opal/tools/state-tool/README.md:288-289`). 신규 키 추가는 미인지 소비자에게 무해하다. `items[]` 병합은 R-10 AC (a)가 명시적으로 요구하므로 따르고, `source` 필드로 소비자가 분리 계산할 여지를 남긴다.
- **파급**: H-2 완화. H-9 신설(README 갱신 누락 시 계약 문서 drift) → Step 11에 README 편입.

### PD-2. 하네스 모듈 표 「해당 §」 — **§2 재사용 + §2 하위 stub 서브섹션 신설**

- **결정**: `opal/core/references/opal-harness.md` §2 아래에 `### 분석 코어 적용 의무` stub 서브섹션을 신설하고, 모듈 표 신규 행의 「해당 §」에 **`§2`**를 기재한다. 최상위 절(§11 등) 신설·기존 절 번호 재배치는 **금지**한다.
- **근거**: 선례 2건이 동형이다 — `QA 표준`(`harness/qa-standards.md`)과 `인용 규칙`(`harness/citation-rules.md`)이 모두 「해당 §」=`§2`이며, §2 하위에 각각 `### QA 산출물 표준 및 검증`(`opal/core/references/opal-harness.md:116`)·`### Citation Rules 적용 의무`(`:125`) stub을 보유한다. 빈 값은 4열 스키마(`:99`)를 깨고, 최상위 절 신설은 타 문서의 `opal-harness.md §N` 인용을 전부 깨뜨린다(H-11).
- **신규 행 값**: 모듈=`분석 코어` / 파일=`harness/analysis-core.md` / 로드 시점=`ANALYSIS 단계 진입 시 · PLAN 단계 2단계(기능별 분석) 진입 시` / 해당 §=`§2`.

### PD-3. `analysis.pm_gate.checklist` 문구 — **4항목 확정**

- **결정**: `opal/skills/opal-pilot-dev/references/pipeline.json:9-10`의 `["-"]`를 아래 4항목으로 교체한다.
  1. `"ANALYSIS.md §0 참조 문서 — code-scan·brain 선조회 결과 1건 이상"`
  2. `"ANALYSIS.md §확정 입력 판정 — TASK.md [결정]·[사실] 전건 판정(누락 0)"`
  3. `"ANALYSIS.md §다음 단계 입력 — 항목|확정값|근거 3열 표 존재"`
  4. `"소스코드 원문 블록 0건 (코드펜스는 실행 명령·시그니처 한정)"`
- **근거**: 스키마 제약은 "존재 + 문자열 배열 + 비어있지 않음"뿐이고 길이·형식 제약은 없다(`opal/tools/state-tool/state_tool.py:1162-1178`). 선례는 1~5개 범위이며 섹션 포인터형과 판정 조건 서술형이 혼재한다(`opal/skills/opal-pilot-dev/references/pipeline.json:13`의 `plan.pm_gate` 4항목). 4항목은 선례 중앙값이며 R-5·R-6·R-7·R-8 AC와 1:1 대응한다.
- **[MUST]** `docs/CONVENTIONS.md` §State 관리: "**PM Gate 정의의 SSOT는 pilot `references/pipeline.json`의 `task_steps[].gate`**(`artifacts`·`checklist`)다 — SKILL.md에 산출물·체크리스트를 표로 중복 게재하지 않는다." → checklist 문구를 `opal-pilot-dev/SKILL.md`에 복제하지 않는다.

### PD-4. MUST 트리거 관용구 잔존 — **R-9 AC 위반 아님**

- **결정**: `opal/skills/op-dev-analysis/SKILL.md:20` ↔ `opal/skills/op-dev-plan/references/plan-guide.md:11`의 1건 잔존을 **허용**한다. 개정 후에도 유지한다.
- **근거 2축**: (a) R-9 AC (b)는 ANALYSIS §7 Q2를 근거로 이미 "텍스트 정확 일치는 판정 대상이 아니다 → 절차 서술 문단 수 감소 + 포인터 대응"으로 판정식이 교체되어 있다(TASK.md R-9 원문) — 원문 AC가 "0건"을 요구하지 않는다. (b) 이 문장은 SSOT(`opal/core/references/harness/citation-rules.md`)를 **로드시키는 트리거 관용구**이며, 각 스킬 진입점마다 존재해야 규범 로드가 발동한다 — 제거하면 규범 도달 경로가 끊긴다.
- **부수 조치**: `analysis-core.md` §품질 체크리스트에 "SSOT 로드 트리거 관용구·`citation-rules.md` §3.1 강제 참조표 헤더·마크다운 표 구분선은 dedup 판정 비대상" 예외 1줄을 명문화하고, R-2·R-9 재현 스크립트의 제외 목록에 반영한다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

ANALYSIS·PLAN 두 단계가 공유하는 분석 절차 SSOT(`opal/core/references/harness/analysis-core.md`)를 신설하고, 지식 선조회·확정 승계·중복 제거를 통해 확정 사실의 재도출을 제거한다. 절차는 신규 SSOT가, 산출물 형식은 각 스킬이 소유하는 역할 분리를 유지한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 분석 코어 SSOT 신설 + 하네스 등록 | R-1 | P0 | 없음 |
| F-002 | 분석 절차 중복 제거·포인터화 | R-2 | P0 | F-001 |
| F-003 | 기술 컨텍스트 정합(MCP 복제 제거 + §6 SSOT 승격) | R-3, R-4 | P0 | F-001 |
| F-004 | ANALYSIS 산출물 템플릿 확장(Q표·핸드오프·덤프 금지) | R-5, R-6, R-7(a) | P0 | F-001 |
| F-005 | QA·게이트 검증 축 보강 | R-7(b), R-8, R-11(c) | P0 | F-004 |
| F-006 | PLAN 트랙 동반 적용·승계 [MUST]화 | R-9, R-11(a)(b) | P0 | F-001 |
| F-007 | evidence-check 확정 승계 파서 | R-10 | P0 | 없음(병렬 트랙) |
| F-008 | 목표 달성 실측(재생성 대조) | R-12 | P1 | F-001~F-007 |

**R→F 양방향 매핑 (누락 0)**

| R | F | R | F |
|---|---|---|---|
| R-1 | F-001 | R-7 | F-004(a) + F-005(b) |
| R-2 | F-002 | R-8 | F-005 |
| R-3 | F-003 | R-9 | F-006 |
| R-4 | F-003 | R-10 | F-007 |
| R-5 | F-004 | R-11 | F-006(a)(b) + F-005(c) |
| R-6 | F-004 | R-12 | F-008 |

> 역방향: F-001={R-1} F-002={R-2} F-003={R-3,R-4} F-004={R-5,R-6,R-7a} F-005={R-7b,R-8,R-11c} F-006={R-9,R-11ab} F-007={R-10} F-008={R-12}. 합집합 = R-1~R-12 (12/12).

### 1.3 기능 의존 그래프

```
F-001 ─┬─ F-002 ──────────────┐
       ├─ F-003 ──────────────┤
       ├─ F-004 ── F-005 ─────┼── F-008
       └─ F-006 ──────────────┤
F-007 (독립 병렬 트랙) ────────┘
```

---

## 리스크 가설 표

> ANALYSIS H-1~H-8 승계 + PLAN 고유 H-9~H-14 신설. TEST-SCENARIO.md §1의 입력.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-007 / `state_tool.py` | `_locate_clarification_table`은 표 전용 — 불릿 리스트 재사용 불가, 형제 파서 신설 필요(공수 과소추정) | P1 | L1(단위) 의무 | S-1 불릿 섹션 파싱 |
| H-2 | F-007 / `confirmed_ratio` | 분모 확대 시 기존 "4요소" 전제 소비자 파괴 → PD-1로 분리형 채택하여 완화 | P1 | L1 회귀 의무 | S-2 기존 ratio 불변 |
| H-3 | 범위 / `op-task-plan/plan-guide.md` | opp·oppd 경로 미커버 비대칭 — TASK.md에 배제가 명시 결정으로 미기재 | P2 | L3(문서 판단) | S-3 배제 명시 확인 |
| H-4 | F-005 / `op-dev-qa/SKILL.md` | 거울 사본을 별도 Step으로 분리하면 즉시 drift 재발 → Step 7 단일 Step 배치로 방어 | P1 | L1(문서 대조) 의무 | S-4 R/P 번호 동일성 |
| H-5 | F-001 / 하네스 모듈 표 | 「해당 §」 대응 절 부재 → PD-2로 §2 재사용 + stub 신설 확정 | P2 | L1 | S-5 4열 완비 |
| H-6 | F-007 / 배포 경계 | install 재배포가 범위 밖 — `state_tool.py` GREEN이어도 워커 런타임(`~/.opal/tools/state-tool/`)은 구버전 유지. **EXECUTE가 이를 "완료"로 오인하면 안 된다** | P1 | L3(소유자 통보) | S-6 미반영 사실 명시 |
| H-7 | F-004 / Q표 배치 | 산문 규칙은 준수율 0% 선례 — 템플릿 실물 섹션이 아니면 R-5가 형식만 통과하고 행동은 불변 | P1 | L1(템플릿 섹션 존재) + L3 | S-7 실물 섹션 확인 |
| H-8 | F-008 / 재생성 대조 | ANALYSIS 서술을 그대로 신뢰하면 실행 오류 — PM이 재생성본을 직접 Read해 baseline 대조 필요 | P2 | L3(PM 교차검증) | S-8 교차검증 기록 |
| H-9 | F-007 / `README.md` | 신규 키 `direction_confirmed_ratio` 추가 후 README 미갱신 시 계약 문서 drift(코드는 GREEN, 문서는 stale) | P1 | L1(문서 대조) | S-9 README 키 기재 |
| H-10 | F-002 / 이관 절차 | 이관은 "analysis-core.md 작성 + **원본 삭제** + 포인터 삽입" 3단 — 원본 삭제 누락 시 중복이 오히려 +1이 되어 R-2 AC (a)가 역행한다 | P0 | L1(정규화 dedup 계수) 의무 | S-10 원본 잔존 0건 |
| H-11 | F-001 / `opal-harness.md` | 최상위 절 신설 시 §번호 재배치 → 타 문서의 `opal-harness.md §N` 인용 전건 파손 | P0 | L1(grep 회귀) | S-11 절 번호 불변 |
| H-12 | 문서 / `docs/ARCHITECTURE.md` | "harness/ 17파일" 수치가 `:80`·`:382` 2곳에 존재 — 한쪽만 고치면 문서 내부 drift | P2 | L1 | S-12 2곳 동시 갱신 |
| H-13 | F-002 / R-2 판정식 | R-2 AC 스코프가 `opal/skills/op-dev-analysis/**`라 신설 SSOT(`opal/core/references/harness/`)가 스코프 밖 — 이관본이 양쪽에 남아도 AC가 Pass할 수 있다(위양성 Pass) | P1 | L1(스코프 확장 계수) 의무 | S-13 스코프 확장 판정 |
| H-14 | Phase 2 병렬 | Tier2 5개 Step을 병렬 디스패치하면 워커별로 `analysis-core.md` 섹션 앵커명을 각자 추측 → 포인터 링크가 서로 다른 이름을 가리켜 깨진다 | P0 | L1(앵커 일치 grep) 의무 | S-14 앵커 계약 준수 |

---

## 2. 기능별 분석

> ANALYSIS.md가 존재하므로 각 F의 현재 구현은 ANALYSIS 결과를 참조하여 간략 기재한다(재조사 없음).
> 영역 축은 프레임워크 문서·스킬 태스크 축(**가이드 / 스킬 / 오케스트레이터 / 환경 / BE / 문서**)을 사용한다.

### F-001: 분석 코어 SSOT 신설 + 하네스 등록

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/analysis-core.md` | 신규 절차 SSOT | 신규 |
| 가이드 | `opal/core/references/opal-harness.md` | §2 모듈 표 + stub 서브섹션 | 수정 |

#### 2.1.2 현재 구현·영향 범위
절차 SSOT는 `harness/*.md`에 두고 스킬이 Read로 참조하는 포인터 패턴이 전역 규범이다(ANALYSIS §1.2). 모듈 표는 4열 스키마이며 탐색 경로는 표 하단 각주 1곳에 고정된다(`opal/core/references/opal-harness.md:99` `:114`).

`analysis-core.md`를 Read하게 될 소비자는 F-002·F-003·F-004·F-006의 4파일뿐이다(ANALYSIS §7 Q8 — 에이전트는 SKILL.md 경유 간접 참조라 자동 전파).

### F-002: 분석 절차 중복 제거·포인터화

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | 품질 체크리스트(10항목) | 수정 |
| 가이드 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 파일 탐색·깊이·의존성·체크리스트(9항목) | 수정 |

#### 2.2.2 현재 구현·영향 범위
`opal/skills/op-dev-analysis/SKILL.md:166-179` ↔ `opal/skills/op-dev-analysis/references/analysis-guide.md:146-163`에 체크리스트가 복제되어 있고, 정규화 후 20자 이상 완전 일치가 **5건**이다(ANALYSIS §7 Q2). `opal/skills/op-dev-analysis/references/analysis-guide.md:11-24`는 Glob/Grep 직행을 지시해 PM 선조회 규범(`opal/core/references/pm/dispatch-process.md:120-129`)과 충돌한다.

`analysis-guide.md`를 참조하는 문서는 `op-dev-analysis/SKILL.md` 1개뿐(ANALYSIS §7 Q8). `opal-project-init/references/code-analysis-guide.md`는 이름만 유사한 별개 파일(오탐 주의).

### F-003: 기술 컨텍스트 정합

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | MCP 매핑 기준 + §6 템플릿 | 수정 |

#### 2.3.2 현재 구현·영향 범위
`opal/skills/op-dev-analysis/references/tech-context-guide.md:92-107`이 미등록 MCP를 매핑 기준으로 제시하며, 등록본(`opal/core/references/mcps.md:14-65`)과 불일치한다. 이 파일은 analysis-core.md 이관 항목 매칭 **0건**이므로 고유 영역을 유지한다(ANALYSIS §4-2).

`op-dev-analysis` 계열 3파일 외 참조 0건(ANALYSIS §7 Q8).

### F-004: ANALYSIS 산출물 템플릿 확장

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS.md 통일 형식 §0~§6 + 확정 입력 소비 규약 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 디스패치 프롬프트 | 수정 |

#### 2.4.2 현재 구현·영향 범위
통일 형식은 `opal/skills/op-dev-analysis/SKILL.md:72-156`에 §0~§6까지 정의되어 있고, Q표·핸드오프 표 섹션은 없다(현장 발명 3종이 표준화되지 않은 상태 — TASK.md 배경 (2)-6). STEP 2 디스패치 프롬프트는 `opal/skills/opal-pilot-dev/SKILL.md:38-50`이며 질문 주입 슬롯이 없다.

템플릿 변경은 이후 생성되는 모든 ANALYSIS.md에 적용된다. 기존 산출물은 비소급(`opal/core/references/harness/citation-rules.md` §5).

### F-005: QA·게이트 검증 축 보강

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | ANALYSIS R-1~R-6 / PLAN P-1~P-7 원본 | 수정 |
| 스킬 | `opal/skills/op-dev-qa/SKILL.md` | R/P 번호 거울 사본 | 수정 |
| 환경 | `opal/skills/opal-pilot-dev/references/pipeline.json` | `analysis.pm_gate.checklist` | 수정 |

#### 2.5.2 현재 구현·영향 범위
검증 ID는 `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-104`가 원본이고 `opal/skills/op-dev-qa/SKILL.md:118-121`이 거울 사본이다 — 개별 번호를 나열하는 문서는 이 2개뿐(ANALYSIS §7 Q6). `analysis.pm_gate.checklist`는 placeholder `["-"]`(`opal/skills/opal-pilot-dev/references/pipeline.json:9-10`).

`op-task-qa/SKILL.md`·`pm-review-gate.md`·`agents.md`는 스킬명만 인용하므로 영향 없음(ANALYSIS §7 Q6 전수 grep).

### F-006: PLAN 트랙 동반 적용·승계 [MUST]화

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | 6영역 축·ANALYSIS 재사용 지시·품질 체크리스트 | 수정 |

#### 2.6.2 현재 구현·영향 범위
재사용 지시는 `opal/skills/op-dev-plan/references/plan-guide.md:104`("간략 작성", `[MUST]` 아님)에만 있고 `:88`(2.N.1)·`:115`(2.N.3)에는 없다. 6영역 라벨 정의는 `:90-98`이 소유한다.

opds(`opal-pilot-dev-short`)는 `op-dev-plan`을 그대로 호출하므로 자동 전파된다(`opal/skills/opal-pilot-dev-short/SKILL.md:45`). `op-task-plan/references/plan-guide.md`는 별개 파일이라 미전파(H-3).

### F-007: evidence-check 확정 승계 파서

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/tests/test_state_tool.py` | 근거 판정 테스트 | 수정(RED 선작성) |
| BE | `opal/tools/state-tool/state_tool.py` | evidence-check 파서 | 수정(GREEN) |
| BE | `opal/tools/state-tool/README.md` | 반환 계약 문서 | 수정(정합 편입) |

#### 2.7.2 현재 구현·영향 범위
체인은 `cmd_verify`(`opal/tools/state-tool/state_tool.py:2560`) → `_check_evidence_gate`(`:2495`) → `_locate_clarification_table`(`:2228`, 표 전용) + `_evaluate_evidence_item`(`:2453`) + `_has_decision_tag`(`:2447`)다. verdict는 `확정`/`미확정` 2값이며 분모는 `len(items)`(`:2554-2555`). `TestT098EvidenceCheck`(`:4225`) docstring이 "열 4개 고정, 열 추가는 설계에 없다"를 명문화한다(`:4237-4238`).

`state_tool.py`는 code-scan `depends` 상 역의존이 `test_worktree_tool.py`뿐이다(ANALYSIS §0). 배포 경로 `~/.opal/tools/state-tool/`는 재배포 전까지 미반영(H-6).

### F-008: 목표 달성 실측

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.baseline.md` | 대조 baseline(고정 완료) | 읽기 전용 |
| 문서 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md` | 재생성 산출물 | 신규 |

#### 2.8.2 현재 구현·영향 범위
baseline은 ANALYSIS PM Gate 통과 시점 사본으로 이미 고정되어 있다(태스크 폴더 실재). 재생성은 표준 opd STEP 2 프롬프트(수동 슬롯 제거)로 수행한다(ANALYSIS §7 Q9-2).

측정 전용 — 프레임워크 소스 무변경. baseline 덮어쓰기 금지.

---

## 3. 기능별 설계

### F-001: 분석 코어 SSOT 신설 + 하네스 등록

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/core/references/harness/analysis-core.md` | 가이드 | ANALYSIS·PLAN 공유 절차 SSOT | (→ D-1 §Q1) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 가이드 | §2 모듈 표 1행 추가 + §2 하위 `### 분석 코어 적용 의무` stub 신설 | `opal/core/references/opal-harness.md:99-116` / PD-2 |

#### 3.1.2 설계 — `analysis-core.md` 섹션 앵커 계약 (H-14 방어)

Step 1이 **먼저 확정**하고 Phase 2의 모든 포인터가 이 앵커명을 그대로 인용한다. 앵커명 임의 변경 금지.

| # | 섹션 헤딩(고정 앵커) | 소유 항목 | 성격 |
|---|---------------------|----------|------|
| 1 | `## 1. 지식 선조회 3단` | brain → code-scan → docs 레지스트리 → 과거 태스크 산출물 | 신규 저술 |
| 2 | `## 2. 증분 소비 규율` | 선조회 결과 존재 시 재도출 금지 · 확정 입력 승계 | 신규 저술 |
| 3 | `## 3. 델타 탐색 규율` | 선조회 결과와의 차분만 탐색 | 신규 저술 |
| 4 | `## 4. 분석 깊이 기준` | 태스크 유형별 깊이 표 | 이관(`opal/skills/op-dev-analysis/references/analysis-guide.md:46-65`) |
| 5 | `## 5. 관련 파일 맵 6영역 축` | FE/BE/DB/환경/배치/공통 라벨 + 프레임워크 축 | 이관(`opal/skills/op-dev-plan/references/plan-guide.md:90-98`) |
| 6 | `## 6. 의존성·영향 범위 도출` | 직접/간접·호출자/피호출자·공유 상태·테스트 | 이관(`opal/skills/op-dev-analysis/references/analysis-guide.md:32-37` `:114-134`) |
| 7 | `## 7. 분석 품질 체크리스트` | 통합 체크리스트(SSOT 1곳) + dedup 예외 규칙(PD-4) | 통합 이관 |

- **[MUST]** brain `new-ssot-pointer-not-value-copy`(E5, task:098 DONE §3 동반 E4): 이 문서는 타 문서의 **수치·목록·개수를 복제하지 않고 포인터만** 둔다 — 폴백 3분기는 `opal/core/references/harness/header-rules.md` §빈 결과 폴백, 근거 등급표는 `opal/core/references/harness/citation-rules.md` §9, MCP 등록 목록은 `opal/core/references/mcps.md`, 루프 상한은 `opal/core/references/opal-harness.md` §1을 각각 포인터로 참조한다.
- **[MUST]** `opal/core/references/harness/citation-rules.md:97`: "ANALYSIS·PLAN 등 산출물에 **소스코드 원문 블록을 기재하지 않는다**. 대체: `경로:줄번호` 인용 + 필요 시 **1~3줄 약식 발췌**까지만 허용한다." → §7 체크리스트에 포인터로 배선(R-7 (a), 원문 복제 아님).
- **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 `## 변경이력` 표에 행을 추가한다." → 신규 문서 포함 전 대상 파일에 적용.
- **[MUST]** `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다." → 선조회 3단은 도구 래퍼(`~/.opal/tools/*/run.sh`) 호출로만 기술한다.

**§1 지식 선조회 3단 — 실행 계약**

```bash
# 1단 brain — 과거 결정·교훈 (E5, E1~E4 동반 인용 필수)
~/.opal/tools/brain-tool/run.sh search "<키워드>"
# 2단 code-scan — 구조·@header 검색 (부재/커버리지 30% 미만이면 Glob/Grep 병용)
~/.opal/tools/code-scan/run.sh scan <scope> ; ~/.opal/tools/code-scan/run.sh search "<키워드>"
# 3단 docs 레지스트리 → 과거 태스크 산출물 (brain이 대체하지 못하는 잔여분)
```

폴백 분기 판정은 `opal/core/references/harness/header-rules.md` §빈 결과 폴백이 소유한다(수치 비복제).

#### 3.1.3 환경 변경 / 3.1.4 배치
해당 없음 / 해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (a) | 산출물 검사 | `analysis-core.md`가 지정 경로에 존재하고 §1~§7 앵커 7개가 모두 존재 |
| TS-002 | R-1 AC (b) | 산출물 검사 | 모듈 표에 `analysis-core.md` 행 1개 추가, 4열(모듈·파일·로드 시점·해당 §) 전부 채워짐 |
| TS-003 | H-11 | 회귀 테스트 | `grep -rn "opal-harness.md §" opal/` 결과의 절 번호가 변경 전후 동일 |
| TS-004 | H-14 | 회귀 테스트 | Phase 2 산출물의 `analysis-core.md §N` 인용이 TS-001 앵커 목록과 100% 일치 |

### F-002: 분석 절차 중복 제거·포인터화

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-analysis/SKILL.md` | 스킬 | §분석 품질 체크리스트(`:166-179`) **본문 삭제 후** `analysis-core.md §7` 포인터로 교체 | (→ D-1 §Q1-7) |
| 2 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 가이드 | `:11-24` Glob/Grep 직행 → `analysis-core.md §1` 선조회 포인터 교체 · `:46-65` 깊이 기준 → §4 포인터 · `:32-37` `:114-134` → §6 포인터 · `:146-163` 체크리스트 → §7 포인터 | (→ D-1 §Q1) |

#### 3.2.2 설계

- **이관 3단 절차(H-10 방어)**: ① `analysis-core.md`에 내용 작성 → ② 원본 파일에서 **해당 본문 삭제** → ③ 포인터 1줄 삽입. ②를 빠뜨리면 중복이 +1이 되어 R-2 AC가 역행한다. 각 Step 완료 기준에 "원본 본문 잔존 0건"을 명시한다.
- **포인터 형식**: `> 절차 SSOT: `opal/core/references/harness/analysis-core.md` §N — 본 문서는 포인터만 둔다.` (선례: `docs/CONVENTIONS.md:222` 등급표 포인터 패턴)
- **R-2 판정식 스코프 확장(H-13 방어)**: AC (a) 원문 스코프는 `opal/skills/op-dev-analysis/**`지만, 이관 성공 여부는 신설 SSOT를 포함해야 판정된다. 판정 스코프를 `opal/skills/op-dev-analysis/**` **+ `opal/core/references/harness/analysis-core.md`**로 확장한다. 예외 목록: SSOT 로드 트리거 관용구 1건 · `citation-rules.md` §3.1 강제 참조표 헤더 · 마크다운 표 구분선(PD-4).

#### 3.2.3 환경 변경 / 3.2.4 배치
해당 없음 / 해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-2 AC (a) | 기능 테스트 | 확장 스코프에서 정규화 후 2회 이상 출현 체크리스트 문장 0건(예외 3종 제외) |
| TS-006 | R-2 AC (b) | 산출물 검사 | 3파일 각각이 `analysis-core.md` 포인터 1개 이상 보유 |
| TS-007 | H-10 | 회귀 테스트 | 이관 대상 원본 구간(`:46-65` `:146-163` 등)에 본문 잔존 0건 |

### F-003: 기술 컨텍스트 정합

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | 가이드 | `:92-107` 하드코딩 MCP 목록 삭제 → 등록본 조회 규칙 교체 (R-3) · §6 템플릿을 "프로젝트 SSOT 경로 + 이번 태스크 델타" 2필드로 재설계 (R-4) | `opal/core/references/mcps.md:14-65` |

#### 3.3.2 설계

- **R-3 대체 규칙 문장**: "MCP는 등록본 `opal/core/references/mcps.md`를 조회하거나 `~/.opal/tools/tool-scan/run.sh which <도구>`로 라우팅한 뒤 **필요한 것만** 기재한다. 미등록 MCP 기재 금지." — 등록 MCP 개수·이름을 이 문서에 복제하지 않는다(개수 복제 금지 제약).
- **R-4 §6 템플릿 2필드 구조**: `### 6.1 기술 스택` = ① `프로젝트 SSOT: <경로>` 1줄 ② `| 카테고리 | 기술 | 델타 |` 표. 표에는 **이번 태스크 델타만** 기재하고 전체 스택 재기재를 금지하는 문장을 둔다.
- 이 파일은 `analysis-core.md` 이관 대상이 아니다(ANALYSIS §4-2) — 고유 영역 유지.

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음 / 해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-3 AC (a) | 기능 테스트 | `grep -Ec "supabase\|github\|figma\|sentry" tech-context-guide.md` → 0 |
| TS-009 | R-3 AC (b) | 산출물 검사 | 등록본 조회·미등록 금지 취지 문장 존재 |
| TS-010 | R-4 AC | 산출물 검사 | §6 템플릿이 SSOT 경로 + 델타 2필드이고 전체 재기재 금지 문장 존재 |

### F-004: ANALYSIS 산출물 템플릿 확장

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-analysis/SKILL.md` | 스킬 | 통일 형식에 §7 Q표 · §8 핸드오프 표 **실물 섹션** 추가 · 확정 입력 판정표에 `승계` 값 추가(R-10 (c)) · 원문 덤프 금지 포인터(R-7 (a)) | (→ D-2) / H-7 |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | STEP 2 디스패치 프롬프트에 질문 주입 슬롯 1개 추가 | `opal/skills/opal-pilot-dev/SKILL.md:38-50` |

#### 3.4.2 설계

**H-7 대응 — 「권장」 강도 유지 + 실물 섹션 배치**

결정 G("강제가 아닌 권장으로 시작")는 **작성 의무의 강도**를 규정하고, H-7은 **배치 형태**를 규정한다 — 충돌하지 않으므로 둘 다 만족시킨다.

- 강도: `> 권장(강제 아님) — PM이 질문을 주입하지 않았으면 "해당 없음"으로 닫는다.`
- 배치: 통일 형식 코드펜스 안에 **실물 H2 섹션**으로 넣는다(산문 서술 금지).

**추가할 템플릿 섹션 2개**(`op-dev-analysis/SKILL.md` 통일 형식 코드펜스 내부, §6 다음):

| 신규 섹션 | 헤딩 레벨 | 하위 구성 | 강도 |
|----------|----------|----------|------|
| `7. 지정 분석 질문 Q1~QN 답변` | H2 | 인용문 1줄 — "PM 디스패치 프롬프트의 질문 슬롯에 대응. 미주입 시 '해당 없음'" | **권장(강제 아님)** |
| `8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값` | H2 | `항목\|확정값\|근거` 3열 표 + H3 하위 `PLAN 결정 필요` `항목\|쟁점\|근거` 3열 표 | **고정 섹션** |

- §8은 **고정 섹션**(R-6 AC — 3열 골격). 「PLAN 결정 필요」 분리 표는 확정값 표에 미결 항목이 섞이는 것을 막는다(ANALYSIS 핸드오프 계약 B-5 선례).
- 확정 입력 판정표 판정값 집합: `해당없음(결정)` / `유효(대조 확인)` / **`승계`** / `수정필요` / `사실오류`.
- **디스패치 슬롯 추가 형태**(`opal/skills/opal-pilot-dev/SKILL.md` STEP 2 프롬프트 내 1줄):
  `**분석 질문**: {Q1~QN — PM이 이번 태스크에서 워커가 답해야 할 질문. 없으면 "없음"}`

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음 / 해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-5 AC | 산출물 검사 | 템플릿에 Q표 실물 섹션 존재 + "권장(강제 아님)" 표기 존재 |
| TS-012 | R-5 AC | 산출물 검사 | STEP 2 프롬프트에 질문 주입 슬롯 1개 추가 |
| TS-013 | R-6 AC | 산출물 검사 | §8 핸드오프 섹션 존재 + 3열 표 골격 |
| TS-014 | R-7 AC (a) | 산출물 검사 | 원문 블록 금지가 `citation-rules.md §2.2` 포인터 형태로 존재(원문 복제 아님) |
| TS-015 | R-10 AC (c) | 산출물 검사 | 판정표 템플릿에 `승계` 값 기재 |

### F-005: QA·게이트 검증 축 보강

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | 가이드 | ANALYSIS 축에 R-7·R-8 신설, PLAN 축에 P-8 신설 | `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-104` |
| 2 | `opal/skills/op-dev-qa/SKILL.md` | 스킬 | 거울 사본 R/P 번호 범위·설명 동시 갱신 | `opal/skills/op-dev-qa/SKILL.md:118-121` / H-4 |
| 3 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 환경 | `analysis.pm_gate.checklist` = PD-3 4항목 | `opal/skills/opal-pilot-dev/references/pipeline.json:9-10` |

#### 3.5.2 설계 — 신규 검증 행

| 축 | # | 검증 항목 | 확인 내용 | R 매핑 |
|----|---|----------|----------|--------|
| ANALYSIS | R-7 | 원문 덤프 차단 | 소스코드 원문 블록이 0건인가? 코드펜스가 실행 명령·시그니처로 한정되는가? | R-7 (b) |
| ANALYSIS | R-8 | 098 규약 준수 | 확정 입력 판정표가 전건 판정되고, 근거 등급(E1~E5)·관측 스코프·실행 명령이 병기되었는가? | R-8 (a) |
| PLAN | P-8 | 확정 승계 준수 | ANALYSIS 핸드오프 표 항목을 재도출 없이 인용했는가? `[MUST] 재도출 금지` 위반 0건인가? | R-11 (c) |

- **[MUST] H-4**: 위 3행 추가와 `opal/skills/op-dev-qa/SKILL.md:118-121`의 번호 범위 갱신(`R-1 ~ R-6` → `R-1 ~ R-8`, `P-1 ~ P-7` → `P-1 ~ P-8`)은 **동일 Step(Step 7)**에서 수행한다. 별도 Step 분리 금지.
- **[MUST]** `docs/CONVENTIONS.md` §State 관리: PM Gate 정의 SSOT는 pipeline.json이므로 checklist 문구를 SKILL.md에 표로 중복 게재하지 않는다.

#### 3.5.3 환경 변경 / 3.5.4 배치
`pipeline.json` JSON 파싱 유지 — 변경 후 `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev/references/pipeline.json`로 검증.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-7 AC (b) | 산출물 검사 | QA 표에 코드펜스 관련 검증 행(R-7) 1개 추가 |
| TS-017 | R-8 AC (a) | 산출물 검사 | QA 표에 확정 입력 판정·근거 등급 검증 행(R-8) 추가 |
| TS-018 | R-8 AC (b) | 기능 테스트 | `spec-validate` exit 0 + `analysis.pm_gate.checklist`가 4항목 배열 |
| TS-019 | R-11 AC (c) | 산출물 검사 | PLAN 축에 P-8 승계 준수 행 1개 추가 |
| TS-020 | H-4 | 회귀 테스트 | `qa-dev-guide.md`와 `op-dev-qa/SKILL.md`의 R/P 번호 범위가 일치 |

### F-006: PLAN 트랙 동반 적용·승계 [MUST]화

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-plan/references/plan-guide.md` | 가이드 | 0단계에 `analysis-core.md` Read 지시 배선 · 2단계(`:88-123`) 자체 절차 서술을 §4·§5·§6 포인터로 대체 · `:88` `:104` `:115`에 승계 지시 + `[MUST] 재도출 금지` 삽입 | `opal/skills/op-dev-plan/references/plan-guide.md:25-39` `:88-123` |

#### 3.6.2 설계

- **R-9 판정식(ANALYSIS §7 Q2 교체판)**: 2단계 자체 절차 서술 **문단 수 before/after**를 실측 병기하고, 감소분마다 `analysis-core.md` 포인터가 1:1 대응함을 보인다. 텍스트 정확 일치 0건 판정은 사용하지 않는다(개정 전에도 0건).
- **R-11 승계 [MUST] 문장**(3곳 삽입):
  `> [MUST] ANALYSIS.md §8 「다음 단계 입력」 확정값은 재조사 없이 승계한다 — 승계 항목의 재도출을 금지한다. 미결 항목은 §8 「PLAN 결정 필요」 표에서만 소비한다.`
- 삽입 위치: `:88`(2.N.1 관련 파일 맵) · `:104`(2.N.2 현재 구현 — 기존 "간략 작성"을 `[MUST]`로 승격) · `:115`(2.N.3 영향 범위).
- 6영역 축 정의(`:90-98`)는 `analysis-core.md §5`로 이관하고 plan-guide는 포인터만 남긴다(H-10 3단 절차 적용).
- PD-4에 따라 `opal/skills/op-dev-plan/references/plan-guide.md:11` MUST 트리거 관용구는 **존치**한다.

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음 / 해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-021 | R-9 AC (a) | 산출물 검사 | plan-guide에 `analysis-core.md` Read 지시 존재 |
| TS-022 | R-9 AC (b) | 기능 테스트 | 2단계 자체 절차 문단 수 감소 + 감소분마다 포인터 대응(before/after 실측 병기) |
| TS-023 | R-11 AC (a) | 산출물 검사 | 2.N.1·2.N.3에 승계 지시 존재 |
| TS-024 | R-11 AC (b) | 산출물 검사 | `[MUST] 재도출 금지` 문장 존재 |

### F-007: evidence-check 확정 승계 파서

#### 3.7.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/tests/test_state_tool.py` | BE | 신규 계약 RED 테스트 선작성(실 파일 픽스처, mock 금지) | `opal/tools/state-tool/tests/test_state_tool.py:4225-4260` |
| 2 | `opal/tools/state-tool/state_tool.py` | BE | 불릿 섹션 파서 신설 + verdict `승계` + `direction_confirmed_ratio` | `opal/tools/state-tool/state_tool.py:2228` `:2453` `:2495-2557` |
| 3 | `opal/tools/state-tool/README.md` | BE | 반환 계약 갱신(신규 키·verdict·`source` 필드) — **범위 확장 1건, 소유자 확인 필요** | H-9 |

#### 3.7.2 설계 — 함수 시그니처·반환 계약

```python
# 신규 — _locate_clarification_table(:2228)의 형제 함수, :2268 직후 신설
def _locate_confirmed_direction_items(lines, root=None):
    """TASK.md '## 확정된 설계 방향' 섹션의 최상위 불릿을 항목으로 수집한다.
    섹션 부재 시 None을 반환한다(호출자 graceful skip — 표 파서와 독립)."""
    # -> list[dict] | None ; dict = {"element": str, "confirmed": str,
    #                                "dependency": str, "source": "confirmed_direction"}

# 확장 — 기존 판정 함수에 verdict '승계' 추가
def _evaluate_evidence_item(confirmed_cell, dependency_cell, root=None):
    """[결정] -> '확정'(기존) / [사실]+유효 인용 -> '승계'(신규) / 그 외 -> '미확정'."""

# 확장 — 병합 지점
def _check_evidence_gate(task_md_path):
    """반환: {"items": [...],                      # 두 소스 병합, item에 source 필드
              "confirmed_ratio": float,            # 명확화 결과 전용 — 분모 불변(PD-1)
              "direction_confirmed_ratio": float | None,  # 신규 키, 섹션 부재 시 None
              "unconfirmed": [element, ...]}"""
```

- **verdict 규칙**: `[결정]` → `확정`(`_has_decision_tag`(`:2447`) 그대로 재사용, 등급 판정 면제) / `[사실]` + E1~E4 유효 인용 → `승계` / `[사실]` + 인용 없음·경로 부재 → `미확정`. `확정`·`승계` 모두 confirmed로 계수한다.
- **[MUST] 계약 유지**(TASK.md §제약): `--evidence-check` 3개 반환 경로 모두 `sys.exit(0)` 유지(`opal/tools/state-tool/state_tool.py:2621` `:2630` `:2639`), `--clarification-check` 상호 배타 로직(`:2579-2580`) 재사용 — 신규 플래그 신설 금지.
- **[MUST] 표 열 확장 금지**: `opal/tools/state-tool/tests/test_state_tool.py:4237-4238`의 "열 4개 고정" 계약을 유지한다 — 별도 섹션 파서로만 구현.
- **[MUST]** `opal/core/references/harness/red-first.md`: 테스트(Step 10) → 구현(Step 11) 순서를 지킨다.
- **[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다." → 소스만 수정하고 재배포는 소유자 몫(H-6).

#### 3.7.3 환경 변경 / 3.7.4 배치
해당 없음(표준 라이브러리·pytest만 사용). `./scripts/install-mac.sh` 재배포는 **범위 밖**(TASK.md §제약) — H-6 유지.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-025 | R-10 AC (a) | 기능 테스트 | `## 확정된 설계 방향` 항목이 `items[]`에 `source="confirmed_direction"`으로 포함 |
| TS-026 | R-10 AC (b) | 기능 테스트 | 3개 반환 경로 모두 exit 0 |
| TS-027 | R-10 AC (d) | 회귀 테스트 | `pytest opal/tools/state-tool/tests/test_state_tool.py` 통과 수 감소 0건 |
| TS-028 | R-10 AC (d) | 회귀 테스트 | `pytest opal/tools/state-tool/` 통과 수 감소 0건 |
| TS-029 | H-2 / PD-1 | 회귀 테스트 | 기존 `confirmed_ratio` 분모가 명확화 결과 항목 수로 불변 |
| TS-030 | H-1 | 기능 테스트 | 섹션 부재 TASK.md에서 신규 파서가 `None` 반환 → graceful skip |
| TS-031 | H-9 | 산출물 검사 | README에 `direction_confirmed_ratio`·`승계`·`source` 기재 |

### F-008: 목표 달성 실측

#### 3.8.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md` | 문서 | 개정 규범만으로 재생성한 대조 산출물 | (→ D-1 §Q9-2) |

#### 3.8.2 설계 — 판정 명령·선행조건

| AC | 판정 명령 | 선행조건 | 이번 회차 |
|----|-----------|---------|----------|
| AC-G1 | `~/.opal/tools/state-tool/run.sh verify <task-path> --evidence-check`의 `items[].verdict`에 `승계` 존재 | **Step 11(R-10 GREEN) 완료 필수** | 조건부 측정 |
| AC-G2 | `grep -Ec "code-scan\|brain" .../ANALYSIS-REGEN.md` ≥ 1 | 없음 | 측정 |
| AC-G3 | baseline·재생성에 동일 awk 코드펜스 계수 적용 후 비율 비교 | 없음 | 측정(천장 효과 명시) |
| AC-G4 | ANALYSIS↔PLAN 쌍 정규화 20자 일치 계수 대조 | baseline PLAN.md 필요 | **측정 불가 — 확정 승계** |

- 재생성은 **표준 opd STEP 2 프롬프트**로 수행한다(수동 Q표·선조회 슬롯 제거 — 신 규범 자체 유도력이 측정 대상).
- baseline `ANALYSIS.baseline.md` **덮어쓰기 금지**.
- **H-8**: PM이 재생성본을 직접 Read해 baseline과 대조한다 — 워커 서술을 그대로 신뢰하지 않는다.
- **H-6 완료 기준**: AC-G1 측정 시 `state_tool.py` 소스가 GREEN이어도 배포본은 구버전일 수 있다 — 측정은 소스 직접 실행(`python3 opal/tools/state-tool/state_tool.py verify ...`)으로 수행하고, 배포본 미반영 사실을 DONE.md에 명시한다.

#### 3.8.3 환경 변경 / 3.8.4 배치
해당 없음 / 해당 없음.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-032 | AC-G1 | 통합 테스트 | Step 11 완료 후 `승계` verdict 1건 이상 |
| TS-033 | AC-G2 | 기능 테스트 | 재생성본에 code-scan·brain 인용 1건 이상 |
| TS-034 | AC-G3 | 기능 테스트 | 코드펜스 내부 줄 비율이 baseline 대비 감소(또는 천장 효과 사유 명시) |
| TS-035 | AC-G4 | 산출물 검사 | DONE.md에 "측정 불가(선행조건 미충족)" 명시 |
| TS-036 | R-12 표본 한계 | 산출물 검사 | DONE.md에 "재생성 1회 = 존재 증명, 통계 아님" + 천장 효과 명시 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| 1 (Tier1) | F-001 | 1 | 순차 | 단독 선행 — §1~§7 앵커 계약 확정(H-14 방어) |
| 2 (Tier2) | F-001, F-002, F-003, F-004, F-006 | 2, 3, 4, 5, 6 | **5개 병렬 가능** | Tier1 완료 후 상호 독립(ANALYSIS §1.1 Tier 판정) — 단 Step 3·4는 동일 스킬 디렉토리라 파일은 서로 다름 |
| 3 (Tier3) | F-004, F-005 | 7, 8, 9 | 병렬 가능 | Step 3(SKILL.md 판정표 형식) 확정 후에만 진입 |
| T (Tier4) | F-007 | 10 → 11 | 순차(RED→GREEN) | **문서 트랙과 독립 병렬** — Phase 1~3 어느 시점에도 착수 가능 |
| 4 | - | 12 | 순차 | docs/ 갱신(PM 직접) |
| 5 | F-008 | 13 | 순차 | Step 1~12 + Step 11 GREEN 완료 후 |

### 4.2 실행 체크리스트

> 총 13개 Step | Phase 6개(문서 4 + 병렬 트랙 1 + 마무리 1) | 실행 모드: **복잡**

#### Step 1: analysis-core.md 신설 (앵커 계약 확정)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/analysis-core.md`
- **작업 내용**: §3.1.2 앵커 계약 표대로 §1~§7 작성. 신규 저술 3항목(선조회 3단·증분 소비·델타 탐색), 이관 4항목(깊이·6영역·의존성/영향범위·체크리스트). 타 문서 수치·목록·개수는 포인터로만 참조. §7에 dedup 예외 3종(PD-4) 명문화. `## 변경이력` 표 신설.
- **완료 기준**: 파일 존재 + §1~§7 앵커 7개 전부 존재 + 수치 복제 0건(폴백 분기·등급표·MCP 목록·루프 상한이 전부 포인터) + 소스코드 원문 블록 0건
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: opal-harness.md 모듈 등록
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §2 모듈 표에 PD-2 신규 행 1개 추가 + §2 하위 `### 분석 코어 적용 의무` stub 서브섹션 신설. **최상위 절 번호 변경 금지.** 변경이력 행 추가.
- **완료 기준**: 4열 전부 채워진 행 1개 추가 + stub 서브섹션 존재 + 기존 §1~§10 번호 불변
- **테스트**: TS-002, TS-003
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: op-dev-analysis/SKILL.md 개정 (체크리스트 포인터화 + 템플릿 확장)
- [x] 완료
- **소속 기능**: F-002, F-004
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-analysis/SKILL.md`
- **작업 내용**: (a) `:166-179` 체크리스트 **본문 삭제 후** `analysis-core.md §7` 포인터 교체(H-10 3단) (b) 통일 형식에 §7 Q표 실물 섹션(권장 표기) + §8 핸드오프 표(3열) + 「PLAN 결정 필요」 분리 표 추가 (c) 확정 입력 판정표에 `승계` 값 추가 (d) 원문 덤프 금지를 `citation-rules.md §2.2` 포인터로 배선. 변경이력 행 추가.
- **완료 기준**: 체크리스트 본문 잔존 0건 + Q표·핸드오프 실물 섹션 존재 + `승계` 값 기재 + `:20` MUST 트리거 관용구 **존치**(PD-4)
- **테스트**: TS-006, TS-007, TS-011, TS-013, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: analysis-guide.md 개정 (선조회 교체 + 절차 이관)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-analysis/references/analysis-guide.md`
- **작업 내용**: `:11-24` Glob/Grep 직행 서술을 `analysis-core.md §1` 선조회 포인터로 교체(PM 규범 충돌 해소) · `:46-65` 깊이 기준 → §4 포인터 · `:32-37` `:114-134` 의존성/영향범위 → §6 포인터 · `:146-163` 체크리스트 → §7 포인터. 각 이관은 **원본 본문 삭제 후** 포인터 삽입. 변경이력 행 추가.
- **완료 기준**: 이관 4구간 본문 잔존 0건 + 포인터 4개 삽입 + 앵커명이 Step 1 계약과 100% 일치
- **테스트**: TS-005, TS-006, TS-007, TS-004
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 5: tech-context-guide.md 개정 (MCP 복제 제거 + §6 SSOT 승격)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-analysis/references/tech-context-guide.md`
- **작업 내용**: `:92-107` 하드코딩 MCP 목록 삭제 후 등록본 조회·`tool-scan which` 라우팅 규칙으로 교체(등록 MCP 개수·이름 복제 금지). §6 템플릿을 "프로젝트 SSOT 경로 + 델타" 2필드로 재설계하고 전체 스택 재기재 금지 문장 삽입. 변경이력 행 추가.
- **완료 기준**: `supabase|github|figma|sentry` 매치 0건 + 미등록 기재 금지 문장 존재 + §6 2필드 구조 + 재기재 금지 문장 존재
- **테스트**: TS-008, TS-009, TS-010, TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: plan-guide.md 개정 (analysis-core 배선 + 승계 [MUST]화)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**: 0단계에 `analysis-core.md` Read 지시 추가 · 2단계(`:88-123`) 자체 절차 서술을 §4·§5·§6 포인터로 대체(문단 수 before/after 실측 기록) · `:88` `:104` `:115` 3곳에 §3.6.2 승계 [MUST] 문장 삽입(`:104`는 "간략 작성" → `[MUST]` 승격) · 6영역 축(`:90-98`)은 §5 포인터로 교체. `:11` MUST 트리거 관용구 **존치**. 변경이력 행 추가.
- **완료 기준**: Read 지시 존재 + 승계 [MUST] 3곳 삽입 + 문단 수 감소분마다 포인터 1:1 대응(before/after 수치 기록) + `:11` 존치 확인
- **테스트**: TS-021, TS-022, TS-023, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 7: QA 검증 축 3행 추가 (원본 + 거울 사본 동시)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 가이드 + 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-qa/references/qa-dev-guide.md`, `opal/skills/op-dev-qa/SKILL.md`
- **작업 내용**: qa-dev-guide `:67-104`에 §3.5.2 3행(R-7·R-8·P-8) 추가하고, **같은 Step에서** `opal/skills/op-dev-qa/SKILL.md:118-121` 거울 사본의 번호 범위·설명을 동시 갱신(`R-1~R-6`→`R-1~R-8`, `P-1~P-7`→`P-1~P-8`). 두 파일 변경이력 행 추가.
- **완료 기준**: 3행 추가 + 두 파일의 R/P 번호 범위 일치(drift 0건) — **[MUST] 별도 Step 분리 금지(H-4)**
- **테스트**: TS-016, TS-017, TS-019, TS-020
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 8: opd STEP 2 질문 주입 슬롯 추가
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: STEP 2 디스패치 프롬프트(`:38-50`)에 `**분석 질문**: {Q1~QN ... 없으면 "없음"}` 슬롯 1줄 추가. checklist 문구는 pipeline.json 소유이므로 복제 금지. 변경이력 행 추가.
- **완료 기준**: 슬롯 1개 추가 + PM Gate checklist 문구 복제 0건
- **테스트**: TS-012
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 9: pipeline.json analysis.pm_gate.checklist 채움
- [x] 완료
- **소속 기능**: F-005
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/references/pipeline.json`
- **작업 내용**: `:9-10`의 `["-"]`를 PD-3 4항목 배열로 교체.
- **완료 기준**: `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev/references/pipeline.json` exit 0 + checklist 4항목
- **테스트**: TS-018
- **실행 방법**: direct
- **의존**: Step 3

#### Step 10: evidence-check RED 테스트 선작성
- [x] 완료
- **소속 기능**: F-007
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: §3.7.2 계약에 대한 RED 테스트 작성 — ① `## 확정된 설계 방향` 항목의 `items[]` 편입(`source` 필드) ② verdict `승계` ③ `direction_confirmed_ratio` 신규 키 ④ 기존 `confirmed_ratio` 분모 불변 ⑤ 섹션 부재 시 graceful skip ⑥ exit 0 유지. **mock 금지, 실 파일 픽스처**. 기존 "열 4개 고정" 계약 위반 없음.
- **완료 기준**: 신규 테스트가 **모두 실패(RED)**하고 기존 테스트는 전부 통과 — `pytest opal/tools/state-tool/tests/test_state_tool.py`
- **테스트**: TS-025~TS-030 (RED 상태)
- **실행 방법**: sub-agent
- **의존**: 없음 (문서 트랙과 독립)

#### Step 11: evidence-check 파서 구현 (GREEN) + README 정합
- [x] 완료
- **소속 기능**: F-007
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/README.md`
- **작업 내용**: `_locate_confirmed_direction_items` 신설(`:2268` 직후) · `_evaluate_evidence_item`(`:2453`)에 `승계` 추가 · `_check_evidence_gate`(`:2495-2557`)에서 병합 + `direction_confirmed_ratio` 반환. `_has_decision_tag` 재사용, 신규 플래그 신설 금지, exit 0 3경로 유지. README 반환 계약 절 갱신(신규 키·verdict·`source`).
- **완료 기준**: Step 10 RED 전건 GREEN + 단일 파일/디렉토리 두 스코프 모두 통과 수 감소 0건 + README 기재 완료. **[MUST] 배포본 미반영이 정상 상태다(H-6) — `~/.opal/tools/state-tool/` 재배포는 범위 밖이며 이를 미완료로 판정하지 않는다.**
- **테스트**: TS-025~TS-031 (GREEN) / `pytest opal/tools/state-tool/tests/test_state_tool.py` · `pytest opal/tools/state-tool/`
- **실행 방법**: sub-agent
- **의존**: Step 10

#### Step 12: docs/ 갱신
- [x] 완료
- **소속 기능**: F-001 (파급)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`
- **작업 내용**: ARCHITECTURE `:80`·`:382` 두 곳의 "harness/ 17파일" → "18파일" 동시 정정(H-12). PROJECT §주요 컴포넌트에 `analysis-core.md` 행 신설(선례: `scenario-gate.md` 행 `docs/PROJECT.md:199`) — 수치·목록 복제 없이 SSOT 포인터만. 두 문서 변경이력 행 추가.
- **완료 기준**: 두 파일 수치 정정 2곳 + PROJECT 행 1개 추가 + 수치 복제 0건
- **테스트**: TS-012 외 — `grep -c "harness/ 17파일" docs/ARCHITECTURE.md` → 0
- **실행 방법**: direct
- **의존**: Step 1, Step 2

#### Step 13: R-12 목표 달성 실측 (재생성 대조)
- [x] 완료
- **소속 기능**: F-008
- **영역**: 공통
- **agent**: PM 직접
- **파일**: `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md`
- **작업 내용**: 동일 TASK.md 입력 + **표준 opd STEP 2 프롬프트**(수동 슬롯 제거)로 ANALYSIS 1회 재생성 → `ANALYSIS-REGEN.md` 저장. §3.8.2 표대로 AC-G1~G4 판정. PM이 재생성본을 직접 Read해 baseline 대조(H-8).
- **완료 기준**: AC-G2·AC-G3 실측 완료 + AC-G1은 Step 11 GREEN 확인 후 측정(선행조건 충족 시) + AC-G4는 "측정 불가(선행조건 미충족)" 명시 + 천장 효과·표본 한계 기록. baseline 무변경.
- **테스트**: TS-032~TS-036
- **실행 방법**: direct
- **의존**: Step 1~12 전건 (특히 **Step 11 GREEN이 AC-G1의 선행조건**)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2~6 | 앵커 계약이 확정돼야 포인터가 유효 — Tier1 단독 선행(ANALYSIS §1.1) |
| Step 2 ∥ 3 ∥ 4 ∥ 5 ∥ 6 | Tier2 5개는 상호 독립·서로 다른 파일(ANALYSIS §1.1 Tier2 병렬 판정) |
| Step 3 → Step 7, 8, 9 | Tier3는 SKILL.md 확정 입력 판정표 **형식**에만 의존(Tier2 나머지 4개와는 무의존) |
| Step 7 내부 2파일 | 거울 사본 drift 방지 — 분리하면 H-4 재발, 동일 Step 강제 |
| Step 10 → Step 11 | RED-first (`opal/core/references/harness/red-first.md`) |
| Step 10·11 ∥ Step 1~9 | state-tool 트랙은 문서 체인과 의존 0 — 별도 병렬 트랙(ANALYSIS §1.3) |
| Step 1, 2 → Step 12 | docs/ 수치는 신설 파일 확정 후에만 정정 가능 |
| Step 11 → Step 13 | AC-G1의 `승계` verdict는 R-10 GREEN 이후에만 존재(ANALYSIS §7 Q9-4) |

---

## 5. QA 체크리스트

### 5.1 기능별 QA (R-1~R-12 전건 커버)

| F-ID | QA 항목 | TS-ID | Pass 조건 | R 커버 |
|------|---------|-------|----------|--------|
| F-001 | SSOT 신설 + 앵커 7개 | TS-001 | 파일 존재 + 앵커 7/7 | R-1 (a) |
| F-001 | 하네스 모듈 등록 | TS-002, TS-003 | 4열 행 1개 + 절 번호 불변 | R-1 (b) |
| F-001 | 앵커 계약 준수 | TS-004 | Phase 2 포인터의 `analysis-core.md §N` 앵커명 100% 일치 | R-1 (a) / H-14 |
| F-002 | 체크리스트 dedup | TS-005, TS-007 | 확장 스코프 중복 0건(예외 3종 제외) + 원본 잔존 0건 | R-2 (a) |
| F-002 | 포인터 보유 | TS-006 | 3파일 각 1개 이상 | R-2 (b) |
| F-003 | MCP 복제 제거 | TS-008, TS-009 | 정규식 매치 0 + 금지 문장 존재 | R-3 |
| F-003 | §6 SSOT 승격 | TS-010 | 2필드 구조 + 재기재 금지 문장 | R-4 |
| F-004 | Q표 실물 섹션 | TS-011, TS-012 | 섹션 존재 + "권장(강제 아님)" + 슬롯 1개 | R-5 |
| F-004 | 핸드오프 표 | TS-013 | 고정 섹션 + 3열 골격 | R-6 |
| F-004 | 원문 덤프 금지 배선 | TS-014 | 포인터 형태 문장 존재 | R-7 (a) |
| F-005 | QA 코드펜스 축 | TS-016 | R-7 행 1개 추가 | R-7 (b) |
| F-005 | 098 규약 검증 축 | TS-017 | R-8 행 추가 | R-8 (a) |
| F-005 | pm_gate checklist | TS-018 | spec-validate exit 0 + 4항목 | R-8 (b) |
| F-005 | P축 승계 검증 | TS-019, TS-020 | P-8 행 + 거울 사본 일치 | R-11 (c) |
| F-006 | analysis-core 배선 | TS-021, TS-022 | Read 지시 + 문단 감소·포인터 1:1 | R-9 |
| F-006 | 승계 [MUST]화 | TS-023, TS-024 | 2.N.1·2.N.3 지시 + MUST 문장 | R-11 (a)(b) |
| F-007 | 파서 확장 | TS-025, TS-030 | items[] 편입 + graceful skip | R-10 (a) |
| F-007 | exit 0 계약 | TS-026 | 3경로 exit 0 | R-10 (b) |
| F-007 | 판정값 `승계` | TS-015 | 템플릿에 값 기재 | R-10 (c) |
| F-007 | 회귀 0건 | TS-027, TS-028, TS-029 | 두 스코프 통과 수 감소 0 + 기존 ratio 불변 | R-10 (d) |
| F-007 | 계약 문서 정합 | TS-031 | README에 신규 키·verdict·`source` 기재 | R-10 (a) / H-9 |
| F-008 | 목표 달성 대조 | TS-032, TS-033, TS-034, TS-035, TS-036 | AC-G1~G4 판정 기록 + 측정 불가 사유·천장 효과·표본 한계 명시 | R-12 |

### 5.2 회귀 테스트
- [ ] `pytest opal/tools/state-tool/tests/test_state_tool.py` — 통과 수 감소 0건 (단일 파일 스코프)
- [ ] `pytest opal/tools/state-tool/` — 통과 수 감소 0건 (디렉토리 스코프)
- [ ] `~/.opal/tools/state-tool/run.sh spec-validate` — 10개 pilot 전건 exit 0
- [ ] `grep -rn "opal-harness.md §" opal/` — 절 번호 참조 파손 0건 (H-11)
- [ ] `analysis-core.md §N` 인용의 앵커명이 Step 1 계약과 100% 일치 (H-14)
- [ ] 이관 원본 구간 본문 잔존 0건 (H-10)

### 5.3 코드/문서 품질
- [ ] 변경 전 파일 전건에 `## 변경이력` 행 추가 (버전·KST 일시·태스크 번호 `(100)`) — `docs/CONVENTIONS.md` §변경이력 작성 의무
- [ ] `~/.opal/` 배포본 직접 편집 0건 — `docs/CONVENTIONS.md` §배포 경계
- [ ] 신설 SSOT에 타 문서 수치·목록·개수 복제 0건 (brain `new-ssot-pointer-not-value-copy`)
- [ ] 산출물·가이드에 소스코드 원문 블록 0건 — `opal/core/references/harness/citation-rules.md:97`
- [ ] 플랫폼 조건문 추가 0건 — `docs/CONVENTIONS.md` §플랫폼 분기 격리
- [ ] 실측 수치 전건에 관측 스코프·실행 명령 병기 — `citation-rules.md` §9 (a)
- [ ] 타 프로젝트 경로·출처 기재 0건

### 5.4 보안
- [ ] 코드에 하드코딩된 토큰/시크릿 0건 (`state_tool.py` 변경분)
- [ ] `.env`·인증 파일이 `.gitignore`에 포함되어 있음
- [ ] 신규 파서가 TASK.md 외부 경로를 읽지 않음(경로 순회 없음)
- [ ] `_resolve_citation_exists` 경유 파일 존재 검사가 프로젝트 루트 밖을 참조하지 않음

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 13개 | 복잡 |
| 변경 파일 수 | 15개 (신규 2 + 수정 13) | 복잡 |
| 모듈 범위 | 다중 (harness · 3개 스킬 · 오케스트레이터 · 도구 · docs) | 복잡 |
| 작업 유형 | 신규 SSOT 신설 + 대규모 개선 | 복잡 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

- **Batch 1**: A1(opal-task-agent) — Step 1. 단독.
- **Batch 2**: A2 — Step 2 / A3 — Step 3 / A4 — Step 4 / A5 — Step 5 / A6 — Step 6. **5 병렬**. 파일 충돌 0(각 에이전트 1파일 전담).
- **Batch 3**: A7 — Step 7(2파일, 동일 에이전트 강제 — H-4) / A8 — Step 8 / PM — Step 9. 3 병렬.
- **Batch T**(Batch 1~3과 동시 진행 가능): B1(opal-be-agent) — Step 10 → Step 11. `state_tool.py`·테스트·README를 **동일 에이전트**에 배치(파일 충돌 방지 + 계약 정합).
- **Batch 4**: PM — Step 12.
- **Batch 5**: PM — Step 13(Batch 3·T 완료 후).

> 그룹핑 근거: 동일 파일 수정 Step은 동일 에이전트(Step 3·7의 다파일 묶음), 동일 모듈 응집(state-tool 3파일 = B1), 독립 모듈 분리(Tier2 5 병렬).

### C-2. 스킬 요구사항

| 대상 | 스킬 | 갭 |
|------|------|-----|
| Step 1~9, 12 | 기존 `op-dev-execute` + `analysis-core.md`(본 태스크 산출물) | 없음 |
| Step 10, 11 | `opal/core/references/harness/red-first.md` | 없음 |
| Step 13 | `op-dev-analysis` 개정본(측정 대상 자체) | 없음 |

> 갭 판별: "이관 3단 절차(작성→원본 삭제→포인터)"가 Step 3·4·5·6 **4개 Step**에서 반복된다 → 스킬 후보 기준(3개 이상) 충족하나, 본 태스크 1회성이므로 **인라인 지침**(§3.2.2)으로 처리하고 스킬화는 하지 않는다.

### C-3. 도구 요구사항

| 도구 | 용도 |
|------|------|
| `~/.opal/tools/state-tool/run.sh spec-validate` | Step 9 검증 |
| `pytest` | Step 10·11 |
| `~/.opal/tools/brain-tool/run.sh` · `code-scan/run.sh` | Step 1 선조회 절차 실증 |
| `node ~/.opal/tools/date/date.js` | 변경이력 KST 일시 취득 |

신규 CLI·MCP·패키지 설치 없음.

### C-4. 테스트 전략

- **기능 테스트**: `pytest opal/tools/state-tool/tests/test_state_tool.py`(단일 파일) — TS-025~TS-031.
- **회귀 테스트**: `pytest opal/tools/state-tool/`(디렉토리) + `spec-validate` 10 pilot + 앵커/절번호 grep 회귀.
- **문서 검증**: 정규화 dedup 계수 스크립트(ANALYSIS §7 Q2 재현 명령 + 예외 3종 제외 목록 추가)를 R-2·R-9 판정에 재사용.
- **보안**: 시크릿 스캔 + `.gitignore` 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (OPAL 규범 문서) | 해당 없음(프레임워크 자기 참조) |
| 코드 | Python 3 + pytest | 해당 없음 |
| 데이터 | JSON (`pipeline.json`) | 해당 없음 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 등록 MCP 전건이 본 태스크와 무관(ANALYSIS §6.3) |

### 8.3 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ANALYSIS 산출물 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md` | Q1~Q9 확정값·Tier·리스크 승계 |
| D-2 | 설계 | 분석 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | 통일 형식·체크리스트 개정 대상 |
| D-3 | 설계 | 분석 가이드 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 절차 이관 원본 |
| D-4 | 설계 | 기술 컨텍스트 가이드 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | MCP 복제 제거·§6 승격 대상 |
| D-5 | 설계 | PLAN 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | 승계 [MUST]화·포인터화 대상 |
| D-6 | 설계 | Dev QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | 검증 축 3행 추가 대상 |
| D-7 | 설계 | op-dev-qa 스킬 | `opal/skills/op-dev-qa/SKILL.md` | R/P 거울 사본 동시 갱신 |
| D-8 | 설계 | 하네스 | `opal/core/references/opal-harness.md` | 모듈 표 4열 스키마·stub 선례(PD-2) |
| D-9 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 원문 금지(§2.2)·근거 등급(§9)·비소급(§5) |
| D-10 | 설계 | RED-first | `opal/core/references/harness/red-first.md` | Step 10→11 순서 근거 |
| D-11 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py` | 파서 확장 지점·반환 계약 |
| D-12 | 소스 | state-tool 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 열 4개 고정 계약 |
| D-13 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | evidence-check 반환 계약 문서 |
| D-14 | 설계 | opd pipeline.json | `opal/skills/opal-pilot-dev/references/pipeline.json` | pm_gate checklist 선례(PD-3) |
| D-15 | 설계 | opd 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 프롬프트 슬롯 |
| D-16 | 설계 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` | 변경이력·배포 경계·State SSOT·플랫폼 분기 [MUST] |
| D-17 | 설계 | 프로젝트 아키텍처 | `docs/ARCHITECTURE.md` | harness 파일 수 정정 대상 |
| D-18 | 설계 | 프로젝트 개요 | `docs/PROJECT.md` | 주요 컴포넌트 행 신설 대상 |
| D-19 | 설계 | MCP 레지스트리 | `opal/core/references/mcps.md` | R-3 등록본 조회 규칙 |
| D-20 | 지식 | brain concept 3건 | `.opal/brain/pages/concept/{new-ssot-pointer-not-value-copy,template-precedence-over-prose-norms,analysis-drift-pm-cross-verify-lesson}.md` | 수치 복제 금지·템플릿 우위·PM 교차검증 (E5 — D-9·D-11·D-1 E1~E4 동반) |

---

## 9. 리스크 및 대응

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 이관 시 원본 삭제 누락으로 중복 +1 (H-10) | F-002, F-006 | 높음 | 3단 절차 명문화 + 완료 기준에 "본문 잔존 0건" |
| 2 | Tier2 병렬 워커가 앵커명을 각자 추측 (H-14) | F-001~F-006 | 높음 | Step 1에서 앵커 계약 표 고정 + TS-004 검증 |
| 3 | 거울 사본 drift 재발 (H-4) | F-005 | 중간 | Step 7 단일 Step 강제 + TS-020 |
| 4 | 기존 `confirmed_ratio` 계약 파괴 (H-2) | F-007 | 중간 | PD-1 분리형 + TS-029 회귀 |
| 5 | 재배포 미실행으로 도구가 구버전 유지 (H-6) | F-007, F-008 | 중간 | Step 11·13 완료 기준에 명시 + DONE.md 기재, 측정은 소스 직접 실행 |
| 6 | R-2 판정 스코프 위양성 Pass (H-13) | F-002 | 중간 | 판정 스코프에 `analysis-core.md` 포함 |
| 7 | 하네스 절 번호 재배치로 인용 파손 (H-11) | F-001 | 높음 | 최상위 절 신설 금지(PD-2) + TS-003 grep 회귀 |
| 8 | Q표가 산문으로만 남아 준수율 0% (H-7) | F-004 | 중간 | 템플릿 실물 섹션 배치 + TS-011 |
| 9 | opp/oppd 경로 비대칭 (H-3) | 범위 | 낮음 | 배제를 PLAN·DONE.md에 명시 결정으로 기록 |
| 10 | 재생성 대조 천장 효과 (H-8, R-12) | F-008 | 낮음 | 대조 성격을 "개선 증명"이 아닌 "규범만으로 동등 재현" 으로 DONE.md에 명시 + PM 직접 Read 교차검증 |
| 11 | README 계약 문서 drift (H-9) | F-007 | 중간 | Step 11에 README 편입(범위 확장 1건, 소유자 확인) |
| 12 | docs/ 수치 2곳 부분 갱신 (H-12) | 문서 | 낮음 | Step 12에서 2곳 동시 정정 + grep 검증 |

# ANALYSIS: 테스트 수행 도구 체계 — FE/BE 2단계(단위·통합) 재정의

> 작성일: 2026-06-23
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | test-tools-schema.yaml | `opal/core/references/test-tools-schema.yaml` | 도구 레지스트리 스키마 — dtp-* 고아 참조 위치 |
| D-2 | 설계 | test-tools.yaml 템플릿 | `opal/templates/test-tools.yaml` | 도구 인스턴스 템플릿 — 현행 카테고리 구조 |
| D-3 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | M1/M2/M3 + 4단계 탐지 + 도구 결정 이중 규정 |
| D-4 | 설계 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | 테스트 워커 3+1모드, E2E 도구 순서 표기 |
| D-5 | 설계 | test-engineer.md | `opal/agents/opal-test-agent/personas/test-engineer.md` | 테스트 페르소나 — 도구명 없는 의무 위치 |
| D-6 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | L1~L4 검증 루프 + PASS-or-fix 한도 + harness SSOT 포인터 |
| D-7 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | 자동 루핑 제약 한도 SSOT (§1 Guards 표) |
| D-8 | 설계 | tools.md | `opal/core/references/tools.md` | cmux-tool macOS 전용 명시 |
| D-9 | 설계 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 단계 자가 점검(L1/L2) 수행 범위 |
| D-10 | 설계 | op-dev-test-scenario SKILL.md | `opal/skills/op-dev-test-scenario/SKILL.md` | 시나리오 작성 스킬 — test-scenario-guide 호출 경로 |
| D-11 | 설계 | qa-engineer 페르소나 (test-scenario) | `opal/skills/op-dev-test-scenario/personas/qa-engineer.md` | test-tools.yaml 참조 의무 선언 위치 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/test-tools-schema.yaml` | 도구 레지스트리 스키마 정의 — dtp-* 참조 4건 내포 | ✅ R1·R2 | L19-20, L44, L139, L150 |
| `opal/templates/test-tools.yaml` | 도구 인스턴스 템플릿 — TS 단일 스택 기본, dtp-* 참조 2건 | ✅ R1·R2 | L11, L27 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | TEST-SCENARIO.md 작성 가이드 — M1/M2/M3 + 4단계 탐지 + 도구 결정 이중 규정 | ✅ R3·R6 | L107, L131-142 |
| `opal/agents/opal-test-agent/AGENT.md` | 테스트 워커 — BE/FE/E2E/red 4모드, E2E 도구 순서 | ✅ R4·R6 | L59, L161 |
| `opal/agents/opal-test-agent/personas/test-engineer.md` | 테스트 페르소나 — FE/BE 집중 영역 정의, 도구명 없는 의무 | ✅ R4 | L23-27, L31-35, L47-53 |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | L1~L4 검증 루프 상세, harness §1 SSOT 포인터 | ✅ R5 | L53-57, L515-530 |

### 1.2 아키텍처 패턴

현행 테스트 체계는 3개 레이어의 독립 체인으로 구성된다.

1. **레지스트리 레이어** (`test-tools-schema.yaml` + `test-tools.yaml`): 도구 정의·설치·버전 관리 스키마. 현재 소비자(dtp-*)가 삭제되어 실질적으로 고아 상태.
2. **시나리오 레이어** (`test-scenario-guide.md`): TEST-SCENARIO.md 작성 규칙, L/M 계층 결정, 4단계 스택 탐지. 도구 결정을 자체 탐지로 수행하며 레지스트리를 실질 참조하지 않음.
3. **실행 레이어** (`opal-test-agent/AGENT.md` + `test-engineer.md`): 시나리오 실행, 판정, 결과 기록. 레지스트리 미참조.

### 1.3 의존성 맵

```
test-scenario-guide.md
  ← op-dev-test-scenario/SKILL.md (D-10:34 "Read test-scenario-guide.md")
  ← op-dev-test-scenario/personas/qa-engineer.md (D-11:15 "test-tools.yaml 레지스트리를 참조")
  ← opal-test-agent/AGENT.md (L77 red mode: "test-scenario-guide.md 탐지 4단계 적용")

opal-test-agent/AGENT.md
  → personas/test-engineer.md (L36 "Read personas/test-engineer.md")
  ← op-dev-execute/SKILL.md (L64 "L3 시나리오: TEST 단계로 위임")

verification-loop-guide.md
  → opal-harness.md §1 (L515-530 "수치 복제 금지, 본 표를 참조")
  ← opal-pilot-project-dev/SKILL.md (oppd Phase 3)

test-tools-schema.yaml / test-tools.yaml
  ← 스스로만 참조 (dtp-* 파이프라인 삭제 후 실질 소비자 없음)
  ← qa-engineer.md L15 (참조 의무 선언만 존재, 실제 호출 파이프라인 없음)
```

### 1.4 테스트 현황

이 태스크는 코드가 아닌 OPAL 프레임워크 문서·YAML 파일들이 대상이다. 기존 테스트 스위트 없음. 완료 기준은 TASK.md §완료기준 ①~⑥으로 정의.

---

## 2. 외부 조사 결과

해당 없음 — 모든 분석 대상은 프로젝트 내부 OPAL 프레임워크 문서.

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일 | 변경 필요 섹션 | 변경 이유 |
|------|-------------|---------|
| `opal/core/references/test-tools-schema.yaml` | `stack.description` (L18-21), `global.description` (L43-44), `resolution_order` (L138-143), `scenario_type_mapping.description` (L149-151) | dtp-* 참조 4건 제거·교체 + 2단계 구조 반영 |
| `opal/templates/test-tools.yaml` | 파일 헤더 주석 (L9-12), `global` 섹션 주석 (L26-27), `tools` 섹션 구조 전체 | dtp-* 참조 2건 제거 + unit/통합 2단계 구조로 재편 + FE/BE 도구 매트릭스 반영 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | L107 (L1 시나리오 "도구" 필드 설명), L131-142 (Step 4-a 4단계 탐지), L75-94 (M 매핑 표) | 도구 결정 SSOT 통합 + 2단계 명명 + FE/BE 도구 + E2E 우선순위 명문화 |
| `opal/agents/opal-test-agent/AGENT.md` | L41-83 (3+1모드 섹션), L159-163 (M2 처리 행동 규칙) | 2단계 체계 반영, E2E 도구 순서 cmux→playwright로 통일 |
| `opal/agents/opal-test-agent/personas/test-engineer.md` | L23-35 (BE/FE mode 집중 영역), L47-53 (코드 품질 검사 기준) | "도구명 없는 의무" — 접근성(WCAG)·실DB 항목에 도구 매핑 추가 |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | §1 개요 헤더 (L1-4), §2 계층 정의 표 (L53-57) | "단위=EXECUTE / 통합=TEST" 명명 정합 + L3a/L3b 명칭이 새 2단계 명명과 혼동되지 않도록 주석 배선 |

### 3.2 간접 영향

| 파일 | 영향 사유 | 변경 여부 |
|------|---------|---------|
| `opal/skills/op-dev-test-scenario/personas/qa-engineer.md` | L15 "test-tools.yaml 레지스트리를 참조" — 레지스트리 구조 변경 시 연동 | 조건부: 레지스트리 SSOT 격상 시 참조 경로 일치 확인 필요 |
| `opal/skills/op-dev-qa/personas/qa-engineer.md` | test-tools.yaml 참조 확인됨 (grep) | 조건부: 내용 확인 후 PLAN에서 결정 |
| `opal/skills/op-dev-execute/SKILL.md` | L64 "L3 시나리오: TEST 단계로 위임" — 새 2단계 분담과 정합. Step 3-S L1/L2 자가 점검 범위가 새 단위 정의와 일치하는지 확인 필요 | TASK.md 변경 범위 밖(제외) — PLAN이 판단 |

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경: 해당 없음
- [ ] API 인터페이스 변경: 해당 없음
- [ ] 설정/환경변수 변경: 해당 없음
- [ ] 빌드/배포 파이프라인 변경: 해당 없음
- [x] 프레임워크 문서·YAML 변경: 6파일

---

## 4. 핵심 발견 사항

### F-1: dtp-* 고아 참조 — 전수 목록 6건

`grep -rn "dtp-agent\|dtp-test" opal/` 실행 결과:

| 파일 | 줄번호 | 참조 내용 |
|------|--------|---------|
| `opal/core/references/test-tools-schema.yaml` | L19-20 | `dtp-agent의 Step 1-b 도구 추론과 dtp-test의 Step 1-a fallback 추론에 사용된다.` |
| `opal/core/references/test-tools-schema.yaml` | L44 | `dtp-test가 항상 실행한다 (required: true 기본값).` |
| `opal/core/references/test-tools-schema.yaml` | L139 | `description: dtp-test의 레지스트리 탐색 순서` |
| `opal/core/references/test-tools-schema.yaml` | L150 | `dtp-agent의 Step 1-b와 test-scenario-guide.md의 매핑 테이블에 사용된다.` |
| `opal/templates/test-tools.yaml` | L11 | `둘 다 없으면 dtp-test가 package.json / pyproject.toml 기반으로 추론 (fallback)` |
| `opal/templates/test-tools.yaml` | L27 | `# dtp-test가 항상 실행한다.` |

현행 살아있는 소비자: `op-dev-test-scenario`(test-scenario-guide.md 4단계 탐지) + `opal-test-agent`가 실질 경로이며, 두 파일 모두 test-tools.yaml/schema를 직접 읽지 않는다.

test-tools.yaml 참조 파일 전수(`grep -rln "test-tools.yaml\|test-tools-schema" opal/`):
- `opal/core/references/test-tools-schema.yaml` (자기 참조)
- `opal/templates/test-tools.yaml` (자기 참조)
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` (L107 참조, 실 호출 없음)
- `opal/skills/op-dev-test-scenario/personas/qa-engineer.md` (L15 참조 의무 선언만)
- `opal/skills/op-dev-qa/personas/qa-engineer.md` (참조 선언)

### F-2: 도구 결정 이중 규정 — 동일 파일 내 충돌 정확한 위치

`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` 내 충돌:

- **L107** (L1 시나리오 작성 요령 "도구" 항목): `.opal/test-tools.yaml 또는 프로젝트 설정에서 결정 (vitest/pytest 등)`
- **L131-142** (Step 4-a, [MUST]): `[MUST] 시나리오 작성 전 테스트 러너·위치를 아래 4단계 우선순위로 탐지한다. 특정 프레임워크 하드코딩 금지` — ① CONVENTIONS.md → ② 스택 문서 → ③ 설정파일(package.json 등) → ④ 기존 테스트 관례

L107은 레지스트리(YAML) 참조, L131은 동적 파일 탐지로 서로 다른 방법을 지시하며, 우선순위 관계가 명시되지 않는다. 또한 qa-engineer.md L15도 레지스트리 참조를 의무화하나 Step 4-a와 연동 방법이 없다.

### F-3: E2E 도구 우선순위 비결정 — 2개 문서 역순 표기

| 문서 | 위치 | 표기 | 필요 교정 |
|------|------|------|---------|
| `test-scenario-guide.md` | L72 (M2 정의) | `cmux browser / playwright / cypress` (순서 불명) | cmux 1순위 명시 |
| `test-scenario-guide.md` | L83 (FE 매핑 표) | `cmux browser / playwright` (cmux 앞, 우선순위 불명시) | 우선순위 명시 |
| `opal-test-agent/AGENT.md` | L161 | `playwright/cmux 도구 환경을 확인 후 실행` (playwright 앞) | cmux 1순위로 역전 교정 |

TASK.md 확정 설계 C: `cmux 1순위 → playwright 폴백`. AGENT.md L161은 반대 순서.

cmux macOS 전용 명시 위치: `opal/core/references/tools.md:L297` — `의존성: cmux 0.64.3 이상 (macOS 전용, 선택 설치)`. 테스트 규정 6파일 어디에도 플랫폼 가드 없음.

### F-4: "단위=EXECUTE / 통합=TEST" 캡틴 매핑 vs 현행 파이프라인 단계 분담 델타

현행 분담 실측:

- **EXECUTE 단계** (`op-dev-execute/SKILL.md` Step 3-S, L60-66):
  - TEST-SCENARIO.md의 L1 + L2 시나리오 자가 점검 수행
  - L3 시나리오는 TEST 단계로 위임 (L64)
  - 즉, EXECUTE 워커가 단위(L1) + 프로세스 통합(L2)을 직접 실행

- **TEST 단계** (`opal-test-agent/AGENT.md`, L23-83):
  - L1/L2 시나리오 실행 (TEST-SCENARIO.md 기반, 최종 판정)
  - 코드 품질(lint/type/format) + 보안 검사 포함 (Steps 5-6)
  - L3 [SUPERVISOR] 는 PM 반환

캡틴 매핑 목표 (TASK.md 설계 A):
- 단위 테스트(lint+build+unit) = EXECUTE(구현 워커 자가검증)
- 통합 테스트(E2E+실환경·사람제어) = TEST(opal-test-agent)

**델타 — 무엇을 어디로 옮겨야 하는가**:

| 검사 항목 | 현행 위치 | 목표 위치 | 이동 필요 |
|---------|---------|---------|---------|
| lint | EXECUTE 자가(oppd L1 루핑) + TEST에서도 독립 실행(test-engineer L47) | EXECUTE 귀속, TEST에서 중복 제거 여부 명시 | test-engineer.md lint 위상 재정의 |
| build/type | EXECUTE 자가(oppd L2 루핑) | EXECUTE | 정합 |
| unit test (L1 시나리오) | EXECUTE 자가(Step 3-S) | EXECUTE | 정합 — 명칭만 "단위" 재라벨 |
| API/실DB 통합 (L2 시나리오) | TEST-SCENARIO L2, opal-test-agent | TEST (통합 귀속) | 캡틴 매핑: "통합 = TEST" → L2 시나리오 귀속 확인 |
| E2E (cmux→playwright) | TEST M2 | TEST | 정합 — 우선순위만 교정 |
| 실환경/사람 | TEST M3 [SUPERVISOR] | TEST | 정합 |

핵심 델타: test-engineer.md가 lint/type 검사를 TEST 단계에서도 독립 실행(L47-53)하는데, 새 체계에서 이것이 EXECUTE 완료 전제로 불필요한 중복인지, 아니면 TEST 단계 독립 재검이 필요한지를 명시해야 한다.

### F-5: verification-loop-guide.md — SSOT 포인터 준수 현황

verification-loop-guide.md §7 (L515-530):
- L515: `→ opal-harness.md §1 참조`
- L522-525 표: lint:∞, build:2, test:3, E2E:1, PLAN재진입:→harness §1 참조
- L530: `참조 경로: opal/core/references/opal-harness.md §1 > Guards > 자동 루핑 제약`

opal-harness.md §1 표(L48-56): lint:제한없음, build/type:2, L3a:3, L3b:1, QA:0, PLAN재진입:2

**판정**: verification-loop-guide §7 표에 lint/build/test/E2E 수치가 기재되어 있어 사실상 복제. 단, L530 포인터 참조로 SSOT 선언. scope:action의 PLAN 재진입 한도는 수치 미복제 — 이 부분은 원칙 준수. TASK.md 제약("수치 복제 금지") 관점에서 §7 표의 수치 기재가 위반인지 PLAN이 판단 필요.

### F-6: 분석 대상 경로 — 소스(opal/) 확인

TASK.md 제약 §2: `~/.opal/ 직접 편집 금지 — 소스 opal/ 수정 후 install 재배포`

분석 대상 6파일 모두 소스 경로 `opal/` 하위임 확인됨. 배포본 직접 편집 금지 원칙과 충돌 없음.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | **2단계 재라벨링 vs L1-L4 계층 명명 충돌** — verification-loop-guide의 L1(lint)/L2(build)/L3a(unit)/L3b(E2E)/L4(QA) 계층 명명과 test-scenario-guide의 L1/L2/L3 계층(기능단위/통합/사용자협업) 명명이 다른 축. 새 "단위=EXECUTE/통합=TEST" 2단계 명명이 3번째 축으로 추가되면 L1~L4가 3가지 다른 의미로 쓰이는 혼동 발생 | 중 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:L53-57` |
| R-2 | **dtp-* 제거 후 레지스트리 재고아화 위험** — test-tools.yaml을 실질 소비하는 경로가 현재 없음. R1(SSOT 격상)을 위해 소비 파이프라인을 새로 연결하지 않으면 레지스트리가 다시 고아 상태로 남음 | 높음 | `opal/core/references/test-tools-schema.yaml:L19-20,L44,L139,L150` |
| R-3 | **test-engineer.md FE 접근성 도구 미결** — FE 접근성(WCAG) 검사 의무(L31-35)에 도구 미지정. axe-core/lighthouse 등 후보를 test-tools.yaml에 등록하고 매핑해야 하나 도구 선택은 PLAN에서 결정 필요 | 중 | `opal/agents/opal-test-agent/personas/test-engineer.md:L31-35` |
| R-4 | **cmux 플랫폼 가드 완전 부재** — cmux macOS 전용(`opal/core/references/tools.md:L297`)이지만 테스트 규정 6파일 모두 플랫폼 가드 없음. "cmux 미설치/비-macOS = playwright 폴백" 단일 규칙을 어느 파일에 어떤 형태로 삽입할지 PLAN에서 결정 필요 | 중 | `opal/core/references/tools.md:L297` |
| R-5 | **루프 한도 수치 복제 위험** — test-tools.yaml 새 구조나 test-scenario-guide 변경 시 검증 한도 수치를 직접 기재하면 SSOT 이중화. 포인터 참조 패턴 유지 필수 | 낮음 | `opal/core/references/opal-harness.md §1:L44-64` / `tasks/039-260623-opd-테스트도구-fe-be-2단계-재정의/TASK.md:L81` |
| R-6 | **op-dev-execute Step 3-S와 새 단위 정의 범위 충돌 가능** — 현재 Step 3-S가 L1+L2 시나리오를 EXECUTE에서 모두 실행하는데, 캡틴 설계 A에서 "통합=TEST"로 L2 귀속을 이동하면 Step 3-S에서 L2 실행을 제외해야 할 수 있음. 단 op-dev-execute/SKILL.md는 TASK.md 변경 범위 밖 — PLAN에서 판단 필요 | 낮음 | `opal/skills/op-dev-execute/SKILL.md:L60-64` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 비고 |
|----------|------|------|
| 문서 형식 | Markdown (.md) | OPAL 프레임워크 스킬/에이전트/레퍼런스 |
| 설정 형식 | YAML (.yaml) | 도구 레지스트리 스키마·템플릿 |
| 대상 테스트 도구 (규정 대상, 코드 아님) | pytest, vitest, jest | unit 테스트 |
| | eslint, ruff | lint |
| | tsc --noEmit, mypy, pyright | type check |
| | cmux, playwright | E2E (cmux macOS 전용) |
| | gitleaks | security |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | ANALYSIS 기반으로 변경 영향 범위를 PLAN.md로 설계 |

### 6.3 추천 MCP

해당 없음 — 외부 라이브러리 조사 불필요. 내부 문서 변경 태스크.

---

## 7. SSOT 충돌 지점 정밀 분석

### 7.1 도구 결정 SSOT — 충돌 위치와 통합 후보

| 문서 | 위치 | 내용 |
|------|------|------|
| `test-scenario-guide.md` | L107 | `.opal/test-tools.yaml 또는 프로젝트 설정에서 결정` |
| `test-scenario-guide.md` | L131-142 | `[MUST] 4단계 탐지 우선순위` |
| `qa-engineer.md` | L15 | `test-tools.yaml 레지스트리를 참조하여 도구를 결정한다` |

통합 방향 후보(PLAN에서 확정):
- (a) test-tools.yaml 존재 시 우선 사용 → 없으면 4단계 탐지 폴백
- (b) 4단계 탐지 ① 위치에 test-tools.yaml을 포함하여 흡수

### 7.2 E2E 우선순위 SSOT — 교정 대상 파일 2개

| 문서 | 위치 | 현재 표기 | 교정 방향 |
|------|------|---------|---------|
| `test-scenario-guide.md` | L72 | `cmux browser / playwright / cypress` (순서 불명) | `cmux 1순위 → playwright 폴백` 명시 |
| `test-scenario-guide.md` | L83 | `cmux browser / playwright` (우선순위 불명시) | 우선순위 명시 추가 |
| `opal-test-agent/AGENT.md` | L161 | `playwright/cmux` (playwright 앞) | cmux 1순위로 역전 교정 |

### 7.3 루프 한도 SSOT — 포인터 준수 현황

| 문서 | 현황 | 판정 |
|------|------|------|
| `verification-loop-guide.md §7` (L515-530) | 표에 수치 기재(lint:∞, build:2, test:3, E2E:1) + L530 포인터 참조 | 수치 복제 있음, 포인터 선언 있음. PLAN이 수치 제거 여부 결정 |
| `opal-harness.md §1` (L44-64) | SSOT 표 | 기준 |

---

## 8. 변경 영향 범위 — 파일별 섹션 × 정합 의존

```
test-tools-schema.yaml
  변경: dtp-* 4건 → op-dev-test-scenario/opal-test-agent 교체 + 2단계 구조 서술 추가
  연동: test-tools.yaml 헤더 주석과 동기화 필요

test-tools.yaml
  변경: dtp-* 2건 교체 + tools 섹션에 2단계(단위/통합) 구조 + FE/BE 매트릭스
  연동: schema 구조 동기화 / qa-engineer.md 참조 경로 유효성 유지

test-scenario-guide.md
  변경: L107 도구 결정 기술 통합 SSOT로 재기술
        L131-142 4단계 탐지를 폴백 위치로 재편
        L72/L83 E2E 우선순위 cmux→playwright 명시
        2단계 명명(단위/통합) 매핑 추가
  연동: AGENT.md M2 표기와 동일 방향 / qa-engineer.md 행동 규칙 정합

opal-test-agent/AGENT.md
  변경: L161 playwright→cmux 순서 역전 교정 + 2단계 체계 반영
  연동: test-scenario-guide.md E2E 우선순위와 동일 방향 필수

personas/test-engineer.md
  변경: FE 접근성 의무(L31)에 도구 매핑 추가(PLAN 확정 후)
        코드 품질 검사 기준(L47-53) — lint가 단위(EXECUTE)인지 재검(TEST)인지 위상 명시
  연동: AGENT.md 모드별 집중 영역과 정합 / test-tools.yaml에 접근성 도구 등록 연동

verification-loop-guide.md
  변경: §1 개요에 "단위=EXECUTE / 통합=TEST" 2단계 명명과 L1~L4 계층명이 별도 축임을 명시
        (수치 복제 여부는 PLAN 결정)
  연동: harness §1 포인터 참조 유지 필수
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 | 초기 작성 — op-dev-analysis 기반 현행 구조·결함·델타·SSOT 충돌·변경 영향 범위 분석 (039) |

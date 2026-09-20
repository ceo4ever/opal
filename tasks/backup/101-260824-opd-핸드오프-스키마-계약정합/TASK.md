# TASK: ANALYSIS→PLAN 핸드오프 스키마 계약 정합 + 확정 입력 판정값 템플릿 승격

> 작성일: 2026-08-24 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

ANALYSIS→PLAN 핸드오프 계약이 서로 충족 불가능한 요구를 하는 3지점(승계 지시·핸드오프 표 스키마·PM Gate 체크리스트)을 정합시킨다. 아울러 태스크 100에서 산출물에만 적용되고 템플릿에 승격되지 않아 즉시 회귀한 확정 입력 판정값 개선을 템플릿으로 올린다.

## 배경

태스크 100은 "이미 확정된 사실의 재도출 제거"를 목표로 ANALYSIS·PLAN 공유 SSOT(`analysis-core.md`)를 신설했다. 그러나 DONE.md가 S-33 Fail로 기록한 계약 불일치가 **배포된 채로 남아 있어**, PLAN 워커가 `[MUST]` 승계를 구조적으로 충족할 수 없다.

충족 불가 시 워커의 선택지는 두 가지뿐이다 — (a) `[MUST]` 위반, (b) 재도출 복귀. (b)는 태스크 100이 제거하려던 바로 그 행동이므로, 현 상태는 태스크 100의 목표가 실행 시점에 무력화되는 구조다.

또한 태스크 100의 grill 라운드에서 얻은 확정 입력 판정값 개선(`해당없음(결정)` 2분리)이 산출물에만 적용되고 템플릿에 승격되지 않아, 같은 태스크의 재생성 대조본에서 즉시 소실됐다.

## 배경 분석 (대화에서 도출)

### (1) 계약 3지점 실측

| # | 지점 | 실측 내용 | 근거 |
|---|------|----------|------|
| A | PLAN 승계 지시 | ANALYSIS 「다음 단계 입력」 표 확정값의 재조사 없는 승계를 `[MUST]`로 요구하고, 6영역 분류 축·라벨 정의는 `analysis-core.md` §5를 따르게 한다 | `opal/skills/op-dev-plan/references/plan-guide.md:92` |
| B | PLAN 파일 맵 컬럼 규정 | 관련 파일 맵 컬럼을 `영역 \| 경로 \| 역할 \| 변경유형`으로 규정 (§2.N.1 하위 테이블) | `opal/skills/op-dev-plan/references/plan-guide.md:351` |
| C | 6영역 축 SSOT | `영역 \| 경로 \| 역할 \| 변경 유형` 4열 축을 정의 | `opal/core/references/harness/analysis-core.md:102-104` |
| D | ANALYSIS 핸드오프 표 | 「다음 단계 입력」 표는 `항목 \| 확정값 \| 근거` **3열**이며, 파일 경로·6영역 라벨·변경 유형을 담을 열이 없다 | `opal/skills/op-dev-analysis/SKILL.md:165-166` |
| E | PM Gate 고정 | analysis 게이트 체크리스트가 "`항목\|확정값\|근거` 3열 표 존재"를 통과 조건으로 고정 | `opal/skills/opal-pilot-dev/references/pipeline.json` `task_steps[3].gate.checklist[2]` |

**판정**: A·B·C가 요구하는 4개 필드를 D의 3열 표가 담을 수 없고, E가 그 3열 스키마를 게이트로 고정하고 있다. 세 지점이 동시에 참일 수 없는 **계약 불일치**다.

### (2) 신규 발견 — ANALYSIS §1.1도 6영역 라벨을 담지 못한다

태스크 100 DONE.md가 제시한 해소안 ⓑ("2.N.1을 승계 대상에서 제외하고 ANALYSIS §1.1 직접 인용")를 실측 검증한 결과, §1.1 관련 파일 목록의 컬럼은 `파일 \| 역할 \| 변경 필요 \| 근거(줄번호)`이며 **영역 열이 없다**(`opal/skills/op-dev-analysis/SKILL.md:97-99`). ⓑ안 단독으로는 6영역 라벨 요구가 여전히 미해결로 남는다.

### (3) 판정값 회귀 실증

| 산출물 | `[결정]` 항목 판정값 | 근거 |
|--------|--------------------|------|
| grill 반영본 | `해당없음(결정)` — 11행 전건 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md:15-25` |
| 표준 프롬프트 재생성본 | `유효` — 16건 일괄 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md:13` |
| 현행 템플릿 | `유효 / 승계 / 수정필요 / 사실오류` (4값, 결정·사실 미분리) | `opal/skills/op-dev-analysis/SKILL.md:84` |

산출물에서 얻은 개선이 템플릿에 없으면 다음 회차에 재현되지 않는다는 것이 같은 태스크 안에서 실증됐다.

### (4) 신규 발견 — `승계` 토큰의 이의(異義) 충돌

| 사용처 | 값 집합 | 의미 | 근거 |
|--------|--------|------|------|
| ANALYSIS 확정 입력 판정 | `유효 / 승계 / 수정필요 / 사실오류` | 상류(브레인·과거 산출물)에서 이미 대조 확인된 항목 | `opal/skills/op-dev-analysis/SKILL.md:27` |
| state-tool `verify --evidence-check` | `확정 / 승계 / 미확정` | `[사실]` 태그 + 유효 인용으로 4축 통과 (계수상 `확정`과 동등) | `opal/tools/state-tool/state_tool.py:2519,2532-2533` |

같은 토큰이 두 층에서 다른 값 집합·다른 판정 기준으로 쓰인다. `citation-rules.md` §7.1 영역 간 용어 일관성 검출 대상에 해당한다.

## 확정된 설계 방향 (대화에서 합의)

- [결정] 태스크 100 후속 이월 1번(핸드오프 표 스키마)과 3번(`해당없음(결정)` 템플릿 승격)을 하나의 태스크로 묶어 처리한다 — 두 항목의 수정 대상 파일이 `op-dev-analysis/SKILL.md`로 겹친다.
- [결정] 파일 3개 이상 + PM Gate 스키마 변경을 수반하므로 L2 경량 트랙이 아닌 풀 파이프라인(`opd`, semi-agentic)으로 진행한다.
- [결정] 계약 해소 방식(스키마 확장 / 승계 원천 재지정 / 양자 혼합)은 ANALYSIS·PLAN에서 결정한다 — TASK 단계에서 선택하지 않는다.
- [사실] 태스크 100의 산출물은 커밋과 `install` 재배포가 모두 완료된 상태다 — 소스는 `opal/core/references/harness/analysis-core.md:1`·`opal/tools/state-tool/state_tool.py:2519`에 실재하고, 배포 관측(E1, 스코프=홈 배포본 2파일)은 `ls ~/.opal/references/harness/analysis-core.md && grep -c "_locate_confirmed_direction_items" ~/.opal/tools/state-tool/state_tool.py` 실행에서 파일 존재 + 4건을 반환했다.
- [사실] 계약 불일치는 산출물 1건의 오류가 아니라 규범 3지점의 구조적 불일치다 — `opal/skills/op-dev-plan/references/plan-guide.md:92`(승계 `[MUST]`)·`opal/skills/op-dev-analysis/SKILL.md:165-166`(3열 표)·`opal/skills/opal-pilot-dev/references/pipeline.json:1`(게이트 고정) 세 지점이 동시에 참일 수 없다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | ANALYSIS→PLAN 핸드오프 계약 3지점을 상호 충족 가능하게 정합시키고, 확정 입력 판정값 2분리를 템플릿으로 승격한다 | - | `opal/skills/op-dev-plan/references/plan-guide.md:92` · `opal/skills/op-dev-analysis/SKILL.md:165-166` |
| 범위 | **포함** — `op-dev-analysis/SKILL.md` 통일 형식·판정값, `op-dev-plan/references/plan-guide.md` 2.N.1 승계 지시, `opal-pilot-dev/references/pipeline.json` analysis 게이트 체크리스트, **`harness/analysis-core.md:59` 승계 지시(ANALYSIS 실측으로 발견된 4번째 계약 지점 — 2026-08-24 소유자 승인으로 편입)**, **`op-dev-qa/SKILL.md`+`qa-dev-guide.md` P-8 거울 사본(M-3 판정 결과 포함)**, **`op-dev-plan/SKILL.md:117` 관련 파일 맵 컬럼 표기 통일(EXECUTE 실측으로 발견된 SSOT 불일치 선재 결함 — 2026-08-24 소유자 승인으로 편입)**, 변경 문서 변경이력. **제외** — `op-task-plan/references/plan-guide.md`(opp·oppd 경로), state-tool 코드 변경, `install` 재배포·커밋 | §1.1 영역 열 추가 여부(M-1), `승계` 토큰 이의 해소 범위(M-2), `op-dev-qa` 검증 축 동반 개정 필요 여부(M-3) | `opal/skills/opal-pilot-dev/references/pipeline.json` `task_steps[3].gate.checklist[2]` · 제외 근거 `tasks/100-260822-opd-분석코어-공유SSOT/DONE.md` §8 측정 한계 |
| 제약 | 프레임워크 소스만 수정하고 `~/.opal/` 배포본을 직접 편집하지 않는다 · 변경 문서에 변경이력 행을 추가한다 · 최상위 절 번호를 신설하지 않는다(타 문서의 `§N` 인용 파손 방지) | - | [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." · 절 번호 근거 `tasks/100-260822-opd-분석코어-공유SSOT/DONE.md` §4 PD-2 |
| 완료기준 | R-1~R-5 AC 전건 Pass + 개정 스키마로 실제 ANALYSIS 1건이 PLAN 2.N.1 요구 필드를 재도출 없이 공급함을 검증 | - | `opal/core/references/opal-harness.md` §1 Guards: 자동 루핑 제약·회귀 방지 |

## 요구사항

- [ ] **R-1** ANALYSIS 「다음 단계 입력」 핸드오프 계약을 PLAN 2.N.1이 요구하는 필드(파일 경로·6영역 라벨·역할·변경 유형)를 공급할 수 있게 정합시킨다.
  - 무엇을: 핸드오프 표 스키마 확장 또는 승계 원천 재지정(택1 또는 혼합) — 방식은 PLAN에서 결정
  - 어디에: `opal/skills/op-dev-analysis/SKILL.md` §8 (필요 시 §1.1 동반)
  - 왜: A·B·C가 요구하는 4필드를 D의 3열이 담지 못한다(배경 분석 (1))
  - AC: 개정 후 PLAN 2.N.1이 요구하는 4필드가 ANALYSIS.md 산출물에서 **재도출 없이 전건 조달 가능**하고, 조달 경로가 `plan-guide.md`에 단일 지점으로 명시된다. 구형 3열 단독 계약을 지시하는 문장이 전 소스에서 0건이다.

- [ ] **R-2** analysis PM Gate 체크리스트를 R-1 개정 스키마와 정합시킨다.
  - 무엇을: `task_steps[3].gate.checklist` 항목 개정
  - 어디에: `opal/skills/opal-pilot-dev/references/pipeline.json`
  - 왜: 현재 체크리스트가 구형 3열 표 존재를 통과 조건으로 고정하여, R-1 개정 시 게이트가 신형 산출물을 거부하거나 구형을 강제한다
  - AC: `state-tool spec-validate`가 exit 0을 반환하고, 체크리스트 문언이 R-1 개정 스키마와 문자열 수준에서 일치하며, 구형 스키마를 지시하는 항목이 0건이다.

- [ ] **R-3** `plan-guide.md` 2.N.1의 승계 지시를 실제 조달 가능한 원천으로 재지정한다.
  - 무엇을: `[MUST]` 승계 대상 원천 명시 (R-1 결정 결과 반영)
  - 어디에: `opal/skills/op-dev-plan/references/plan-guide.md:92` (필요 시 `:102` 동반)
  - 왜: 현 지시는 조달 불가능한 원천을 `[MUST]`로 요구한다
  - AC: 2.N.1이 지시하는 원천이 R-1 산출물에 실재하고, PLAN 워커가 해당 원천만으로 §2.N.1 하위 테이블 4열을 채울 수 있음을 시나리오 1건으로 검증한다.

- [ ] **R-4** 확정 입력 판정값을 `[결정]`/`[사실]` 2분리로 템플릿에 승격한다.
  - 무엇을: 판정값 집합을 결정 계열(`해당없음(결정)` 기본 + 사실 오류 내재 시 강등)과 사실 계열(대조 확인 결과)로 분리하여 템플릿 표에 기재
  - 어디에: `opal/skills/op-dev-analysis/SKILL.md:27, 84`
  - 왜: 산출물에만 적용된 개선이 재생성본에서 즉시 소실됐다(배경 분석 (3))
  - AC: 템플릿 표에 2분리 판정값이 실물로 기재되고, 구형 단일 4값 나열(`유효 / 승계 / 수정필요 / 사실오류`)이 소스에서 0건이며, 개정 템플릿으로 생성한 ANALYSIS 1건이 `[결정]` 항목에 결정 계열 판정값을 채택함을 검증한다.

- [ ] **R-5** 변경한 모든 프레임워크 문서에 변경이력 행을 추가한다.
  - 무엇을: 변경이력 표에 행 추가 (일시 KST + 태스크 번호 101)
  - 어디에: 변경된 스킬·가이드·참조 문서 전건
  - 왜: 프로젝트 금지사항 — 변경이력 누락 금지
  - AC: `changed_files` 중 변경이력 표를 보유한 문서 전건에 `(101)` 태그 행이 1개씩 추가되어 있다.

## 미확정 사항 (ANALYSIS·PLAN에서 결정)

| # | 항목 | 쟁점 |
|---|------|------|
| M-1 | ANALYSIS §1.1 관련 파일 목록에 영역 열을 추가할지 | 추가하면 6영역 라벨이 §1.1에서 조달 가능해지나, 표 열이 4→5로 늘어 기존 산출물과의 형식 차이가 생긴다 (배경 분석 (2)) |
| M-2 | `승계` 토큰 이의 충돌을 이번 태스크에서 해소할지 | ANALYSIS 판정값의 `승계`와 state-tool verdict의 `승계`가 다른 의미다. 해소하면 R-4와 같은 표를 만지므로 묶기 효율이 있으나, state-tool 반환 계약에 닿으면 범위가 코드로 확대된다 (배경 분석 (4)) |
| M-3 | `op-dev-qa` 검증 축(P-8 확정 승계 준수)을 동반 개정할지 | R-1이 승계 원천을 바꾸면 기존 검증 축이 구형 원천을 검사하게 된다. `op-dev-qa/SKILL.md`와 `qa-dev-guide.md` 거울 사본 2곳 동시 갱신이 필요하다 |

## 제약 조건

- `~/.opal/` 배포본을 직접 편집하지 않는다. 프로젝트 소스만 수정한다.
- 변경 문서에 변경이력 행을 추가한다 (일시 KST + 태스크 번호).
- 최상위 절 번호를 신설하지 않는다 — 타 문서의 `§N` 인용을 파손한다.
- 커밋과 `install` 재배포는 소유자 권한이며 이 태스크의 범위 밖이다.
- 작업 시작 시점에 워킹트리에 태스크 101과 무관한 미커밋 변경이 존재한다 (`opal/core/PRINCIPLES.md`, `opal/core/references/opal-doc-standard.md`, `opal/core/references/opal-skills-registry.json` 수정 + `opal/skills/opal-eli5/`, `opal/skills/opal-grill/` 미추적).

## 기술 스택

- Markdown — 프레임워크 스킬·가이드·참조 문서 (주 변경 대상)
- JSON — `pipeline.json` 파이프라인 스펙, `state.schema.json`
- Python 3 — `state-tool` (`spec-validate` 검증에만 사용, 코드 변경 없음)
- Bash / Node.js — OPAL 도구 래퍼 (`run.sh`, `date.js`)

> 루트에 `package.json` · `pyproject.toml` · `requirements.txt` · `go.mod` · `Cargo.toml` 없음 — 프레임워크 문서 저장소 성격.

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-analysis SKILL | `opal/skills/op-dev-analysis/SKILL.md` | 핸드오프 표·판정값 템플릿 SSOT — R-1·R-4 주 변경 대상 |
| D-2 | 설계 | plan-guide (dev) | `opal/skills/op-dev-plan/references/plan-guide.md` | 2.N.1 승계 지시·파일 맵 컬럼 규정 — R-3 대상 |
| D-3 | 설계 | pipeline.json (opd) | `opal/skills/opal-pilot-dev/references/pipeline.json` | analysis PM Gate 체크리스트 — R-2 대상 |
| D-4 | 설계 | analysis-core | `opal/core/references/harness/analysis-core.md` | 6영역 축 SSOT §5 — 계약의 기준 |
| D-5 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` | §7 용어 일관성(M-2) · §9 근거 등급 |
| D-6 | 설계 | 태스크 100 DONE | `tasks/100-260822-opd-분석코어-공유SSOT/DONE.md` | S-33 Fail 원문·후속 이월 목록 |
| D-7 | 소스 | 태스크 100 ANALYSIS | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md` | 판정값 2분리 적용 원본 (R-4 승격 대상 문언) |
| D-8 | 소스 | 태스크 100 ANALYSIS-REGEN | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md` | 판정값 회귀 실증 대조본 |
| D-9 | 설계 | op-dev-qa 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | M-3 검증 축 동반 개정 판단 |

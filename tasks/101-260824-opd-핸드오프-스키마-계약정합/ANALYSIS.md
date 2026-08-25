# ANALYSIS: ANALYSIS→PLAN 핸드오프 스키마 계약 정합 + 확정 입력 판정값 템플릿 승격

> 작성일: 2026-08-24
> 입력: TASK.md
> 출력: ANALYSIS.md

## 확정 입력 판정

TASK.md `## 확정된 설계 방향`에는 `[결정]` 3건, `[사실]` 2건이 있다(전건 판정, 누락 0).

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 태스크 100 후속 이월 1번+3번을 하나의 태스크로 묶어 처리 | 해당없음(결정) | - |
| [결정] L2가 아닌 풀 파이프라인(opd, semi-agentic)으로 진행 | 해당없음(결정) | - |
| [결정] 계약 해소 방식은 ANALYSIS·PLAN에서 결정(TASK 단계 미선택) | 해당없음(결정) | - |
| [사실] 태스크 100의 산출물은 커밋과 install 재배포가 모두 완료된 상태 | 유효(대조 확인) | E1(스코프: 홈 배포본 2파일 + 소스 git log), 실행: `ls ~/.opal/references/harness/analysis-core.md`(존재 확인) + `grep -c "_locate_confirmed_direction_items" ~/.opal/tools/state-tool/state_tool.py`(4건) + `git log --oneline -1 -- opal/core/references/harness/analysis-core.md`(`d9dda2f feat(100)` 확인) — TASK.md 진술과 실측 일치 |
| [사실] 계약 불일치는 산출물 1건의 오류가 아니라 규범 3지점의 구조적 불일치 | 수정필요(3→4지점) | 3지점은 유효하나 **4번째 지점이 누락**됐다 — `opal/core/references/harness/analysis-core.md:59`가 동일한 "ANALYSIS.md §다음 단계 입력(§8)" 단일 경로를 `[MUST]` 재도출 금지로 재천명한다: "TASK.md `[결정]` 항목과 ANALYSIS.md §다음 단계 입력(§8 「PLAN이 재조사 없이 쓸 수 있는 확정값」)의 확정값은 재조사 없이 그대로 승계한다." 이 문장은 TASK.md 범위(§범위 포함/제외)에 `analysis-core.md`가 아예 등재되지 않아 R-1 AC("구형 3열 단독 계약을 지시하는 문장이 전 소스에서 0건")를 문자 그대로 충족하려면 반드시 동반 개정이 필요하다(§4 핵심 발견 1, §8 PLAN 결정 필요 참조). |

> 위 표는 TASK.md 원문 판정용이며, R-4가 템플릿에 승격할 판정값 스킴(결정 계열 `해당없음(결정)` / 사실 계열 `유효(대조 확인)`·`수정필요`·`사실오류`)을 본 산출물부터 선적용했다 — task:100 `ANALYSIS.md:9-25`(grill 반영본, D-7)와 동일 표기 (§7 Q1 권고안의 논거이기도 함).

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-analysis SKILL | `opal/skills/op-dev-analysis/SKILL.md` | 핸드오프 표·판정값 템플릿 SSOT — R-1·R-4 주 변경 대상 |
| D-2 | 설계 | plan-guide (dev) | `opal/skills/op-dev-plan/references/plan-guide.md` | 2.N.1 승계 지시·파일 맵 컬럼 규정 — R-3 대상 |
| D-3 | 설계 | pipeline.json (opd) | `opal/skills/opal-pilot-dev/references/pipeline.json` | analysis PM Gate 체크리스트 — R-2 대상 |
| D-4 | 설계 | analysis-core | `opal/core/references/harness/analysis-core.md` | 6영역 축 SSOT §5 + §2의 4번째 승계 지시 지점(신규 발견, 핵심 발견 1) |
| D-5 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` | §7 용어 일관성(M-2) · §9 근거 등급 |
| D-6 | 설계 | 태스크 100 DONE | `tasks/100-260822-opd-분석코어-공유SSOT/DONE.md` | S-33 Fail 원문·후속 이월 목록 |
| D-7 | 소스 | 태스크 100 ANALYSIS | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md` | 판정값 2분리 적용 원본(§확정 입력 판정) + §1.1 5열 실사용례(순서(Tier) 열, 영역 열은 없음) |
| D-8 | 소스 | 태스크 100 ANALYSIS-REGEN | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md` | 판정값 회귀 실증 대조본(`유효` 일괄 16건) |
| D-9 | 설계 | op-dev-qa 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | M-3 검증 축(R-7·R-8·P-8) 동반 개정 판단 |
| D-10 | 설계 | op-dev-qa SKILL | `opal/skills/op-dev-qa/SKILL.md` | P-8 거울 사본(H-4 방어 대상) |
| D-11 | 지식 | brain: handoff-contract-table-schema-mismatch | `.opal/brain/pages/concept/handoff-contract-table-schema-mismatch.md` | 본 태스크 직접 선행 지식(E5, task:100 DONE §6 동반 인용) |
| D-12 | 지식 | brain: template-precedence-over-prose-norms | `.opal/brain/pages/concept/template-precedence-over-prose-norms.md` | 템플릿 우위 법칙 — Q1 권고안(스킬 SKILL.md 템플릿 우선 개정) 근거 |
| D-13 | 지식 | brain: shared-ssot-procedure-artifact-role-split | `.opal/brain/pages/concept/shared-ssot-procedure-artifact-role-split.md` | 절차(analysis-core.md)/산출물 형식(SKILL.md) 역할 분리 — Q1 권고안이 이 분리를 어기지 않는지 판정에 사용 |
| D-14 | 지식 | brain: decision-vs-fact-claim-separation | `.opal/brain/pages/concept/decision-vs-fact-claim-separation.md` | 결정/사실 분리 원칙 — R-4·확정 입력 판정 표 근거 |

> **3단-B 트리거 판정**: T3 성립(TASK.md가 `task:100`을 반복 인용) — 과거 산출물(DONE.md·ANALYSIS.md·ANALYSIS-REGEN.md) 조회를 수행했다(§0 D-6~D-8).
> **2단 code-scan**: 본 태스크는 프레임워크 문서·스킬 태스크(코드 미변경)이므로 `analysis-core.md` §1 "문서·규범 전용 태스크에서는 2단이 0건을 반환할 수 있다" 분기에 해당 — code-scan 대신 Grep으로 대상 파일 5+1건을 직접 확인했다(폴백 병행, §1 3층 위치 표 "폴백 병행" 허용 범위).

## 1. 기존 코드 분석

> 본 태스크는 프레임워크 문서·스킬 태스크이므로 `analysis-core.md` §5 "프레임워크 문서·스킬 태스크 축"(스킬/가이드/오케스트레이터/에이전트/문서/환경/배치)을 사용한다.

### 1.1 관련 파일 목록

| 영역 | 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|------|----------|-------------|
| 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 산출물 통일 형식·확정 입력 판정값 SSOT | §1.1 템플릿(영역 열 추가, M-1)·§8 템플릿(승계 원천 명확화)·§확정 입력 판정 판정값 스킴(R-4) 개정 | `opal/skills/op-dev-analysis/SKILL.md:81-86`(판정값 4값), `:97-99`(§1.1 4열, 영역 없음), `:165-166`(§8 3열) |
| 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 2단계 승계 지시·파일 맵 컬럼 규정 | `:92,96,102`의 승계 원천 지시문 재지정(R-3) | `opal/skills/op-dev-plan/references/plan-guide.md:92`, `:96`, `:102`, `:351`(컬럼 규정, 근거 원본) |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/references/pipeline.json` | analysis PM Gate 체크리스트 스펙 | `task_steps[3].gate.checklist` 항목 추가(신형 스키마 정합, R-2) | `opal/skills/opal-pilot-dev/references/pipeline.json:13`(3열 표 존재 체크) |
| 문서 | `opal/core/references/harness/analysis-core.md` | ANALYSIS·PLAN 공유 절차 SSOT — 6영역 축(§5) + 승계 규율(§2) | `:59`의 승계 지시문 동반 재지정(TASK.md 범위 미등재 — 신규 발견, R-1 AC 문자 충족 위해 필수) | `opal/core/references/harness/analysis-core.md:59`(승계 지시), `:98-108`(§5 6영역 축) |
| 스킬 | `opal/skills/op-dev-qa/SKILL.md` | PM Gate 검증 기준 라이브러리(P-8 정의) | P-8 "ANALYSIS 핸드오프 표" 참조를 §1.1/§8 이중 지정으로 명확화(M-3, R-1 부수) | `opal/skills/op-dev-qa/SKILL.md:121,123` |
| 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | P-8 거울 사본(H-4 동시 갱신 대상) | 위와 동일 내용 동시 개정 | `opal/skills/op-dev-qa/references/qa-dev-guide.md:93` |

> R-5(변경이력) 적용 대상은 위 6파일 전건(변경이력 표 보유 문서) — `pipeline.json`은 변경이력 표가 없는 JSON이라 R-5 적용 예외(문서 규칙은 "변경이력 표를 보유한 문서"에 한정, TASK.md R-5 AC와 일치).

### 1.2 아키텍처 패턴

- 3층 구조(오케스트레이터 → 단계 스킬 → 워커)이며, ANALYSIS→PLAN 핸드오프는 산문 `[MUST]` 지시(plan-guide.md) + 산출물 템플릿(SKILL.md) + 게이트 체크리스트(pipeline.json) 3중 배선으로 집행된다(`opal/core/references/opal-harness.md` §1 Guards 패턴과 동형).
- `analysis-core.md`는 "절차 SSOT, 형식은 각 스킬 소유"(D-13) 원칙 아래 §5에서 6영역 축을 **정의**하지만, ANALYSIS §1.1은 그 축을 **아직 적용하지 않고 있다** — SSOT 신설(task:100) 이후 소비 측 동기화가 §1.1에서 누락된 상태(§4 핵심 발견 2).

### 1.3 의존성 맵

| 원천 | 소비처 | 관계 |
|------|--------|------|
| `analysis-core.md` §5 (6영역 축 정의) | `plan-guide.md` §2.N.1 | 승계 `[MUST]` 지시가 §5 축을 인용 |
| `analysis-core.md` §5 | `plan-guide.md` §3.N.1 | 파일 변경 계획 표에서 영역 열 실사용 |
| `analysis-core.md` §5 | `op-dev-analysis/SKILL.md` §1.1 | **미접속** — 영역 열이 없어 축을 소비하지 않음(M-1) |
| `op-dev-analysis/SKILL.md` §8 (확정값 3열) | `plan-guide.md:92,96,102` | 승계 `[MUST]` 지시의 원천 |
| `op-dev-analysis/SKILL.md` §8 | `analysis-core.md:59` | 동일 승계 경로 재천명(신규 발견) |
| `op-dev-analysis/SKILL.md` §8 | `pipeline.json` `analysis.pm_gate` item[2] | 게이트 체크리스트가 3열 표 존재를 검사 |
| `op-dev-qa/SKILL.md` P-8 | `qa-dev-guide.md` P-8 | 거울 사본 — H-4 동시 갱신 의무 |

### 1.4 테스트 현황

- 프레임워크 문서 태스크라 코드 테스트는 없다. 검증은 `state-tool spec-validate`(pipeline.json 스키마 검증, R-2 AC) + PM Gate 문서검증(qa-dev-guide.md 기준)으로 대체된다.

## 2. 외부 조사 결과

해당 없음 — 외부 라이브러리·API 미개입.

## 3. 영향 범위

### 3.1 직접 영향

- `opal/skills/op-dev-analysis/SKILL.md`(§1.1·§8·확정 입력 판정 템플릿), `opal/skills/op-dev-plan/references/plan-guide.md`(:92,96,102), `opal/skills/opal-pilot-dev/references/pipeline.json`(`task_steps[3].gate.checklist`), `opal/core/references/harness/analysis-core.md`(:59) — §1.1 파일 맵 표 참조.

### 3.2 간접 영향

- `opal/skills/op-dev-qa/SKILL.md` + `opal/skills/op-dev-qa/references/qa-dev-guide.md`(P-8 정의, M-3) — 승계 원천이 바뀌면 검증 축이 구형 원천만 검사하게 되어 동반 개정 필요.
- 향후 생성될 ANALYSIS.md/PLAN.md 전건 — 템플릿 변경 시점 이후 산출물부터 신형 스키마 적용(레거시 소급 없음, `citation-rules.md` §5).
- `docs/PROJECT.md` §주요 컴포넌트 `analysis-core.md` 행 — 본문 수치 무변경이면 갱신 불요(포인터만 두는 정책, `docs/PROJECT.md:199` 확인).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [ ] 설정/환경변수 변경 — 해당 없음
- [x] 빌드/배포 파이프라인 변경 — `pipeline.json` PM Gate 체크리스트 스펙 변경(state-tool spec-validate 대상)

## 4. 핵심 발견 사항

1. **계약 불일치 지점이 3곳이 아니라 4곳이다** — TASK.md가 특정한 3지점(plan-guide.md:92, SKILL.md:165-166, pipeline.json:13) 외에, `analysis-core.md:59`가 동일한 "§8 다음 단계 입력" 단일 승계 경로를 `[MUST]`로 재천명한다. `analysis-core.md`는 TASK.md 범위표(§범위 포함/제외)에 등재되지 않아, 이를 놓치면 R-1 AC("구형 3열 단독 계약을 지시하는 문장이 전 소스에서 0건")가 문자 그대로 미충족된다(§확정 입력 판정 표 [사실] 2 참조).
2. **§1.1도 6영역 축 SSOT(analysis-core.md §5)를 아직 소비하지 않는다** — `analysis-core.md` §5는 "관련 파일 맵 6영역 축"을 ANALYSIS·PLAN 공유 SSOT로 명명했지만(모듈 role 서술: "관련 파일 맵" 그 자체), 실제로 이 축을 적용하는 곳은 PLAN §2.N.1 지시문·§3.N.1 파일 변경 계획 표뿐이고 ANALYSIS §1.1은 독자 4열 스키마(`파일|역할|변경 필요|근거`)를 유지한다. task:100의 ANALYSIS.md조차 이를 우회하려 임시로 "순서(Tier)" 열을 추가했을 뿐(D-7, `tasks/100.../ANALYSIS.md:66`) 영역 열은 넣지 않았다 — SSOT 신설 후 소비 동기화가 누락된 채로 한 태스크를 그대로 통과한 사례다.
3. **DONE.md §6 S-33의 "순서" 필드 요구는 현재 소스로 확인되지 않는다** — plan-guide.md 전체에서 "순서"는 §4 실행 체크리스트의 "의존성 순서: 하위 레이어 먼저"(`plan-guide.md:219`, Step 배치 규칙)에만 등장하며 §2.N.1/§3.N.1 파일 맵 컬럼 규정과는 무관하다. `plan-guide.md:351`의 컬럼 규정은 `영역 | 경로 | 역할 | 변경유형` 4필드이며 "순서"는 없다(§7 Q2 상세).
4. **`승계` 토큰의 이의(異義) 충돌은 노출 경로가 분리돼 있다** — ANALYSIS "확정 입력 판정"표는 ANALYSIS 워커가 산문으로 직접 작성하는 반면, state-tool verdict `승계`는 `verify --evidence-check`가 TASK.md `## 확정된 설계 방향` 불릿(`_locate_confirmed_direction_items`, `state_tool.py:100` 변경이력)을 대상으로 계산하는 별도 JSON 출력이다. 두 값이 같은 표·같은 산출물에 동시 렌더링되는 경로가 소스 상 확인되지 않는다(§7 Q4 상세).
5. **op-dev-qa의 P-8만 유일하게 취약하다** — R-7(원문 덤프 차단)·R-8(098 규약 준수)은 각각 "§확정 입력 판정" 표와 코드펜스 비율을 검사할 뿐 §8/§1.1 스키마와 무관하여 Q1 권고안 적용에도 불변이다. P-8("ANALYSIS 핸드오프 표 항목을 재도출 없이 인용")만 참조 대상 표가 바뀌면 문언이 stale해진다(§7 Q5 상세).

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-T1 | `analysis-core.md:59`가 TASK.md 범위 밖에 있어 R-1 AC 미충족 위험 | High | `opal/core/references/harness/analysis-core.md:59` |
| R-T2 | §1.1에 영역 열을 추가하면 기존 ANALYSIS.md(4~5열)와 신형(5~6열) 간 열 수 불일치가 생기나, 레거시 소급 변경은 규칙상 불요 | Low | `opal/core/references/harness/citation-rules.md` §5 레거시 호환 |
| R-T3 | op-dev-qa 거울 사본(SKILL.md/qa-dev-guide.md) 중 한쪽만 개정 시 H-4류 drift 재발 | Medium | `opal/skills/op-dev-qa/SKILL.md:123`, `opal/skills/op-dev-qa/references/qa-dev-guide.md:93` — task:100 DONE.md §3.2 "거울 사본 동시 갱신(H-4 방어)" 선례 |
| R-T4 | pipeline.json 체크리스트 항목 문구를 SKILL.md 확정 입력 판정표 최종 문구 확정 전에 고정하면 재작업 발생(task:100 ANALYSIS.md "PLAN 결정 필요" 동일 패턴 재확인) | Medium | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.md:329`(`pipeline.json checklist 정확한 문구 — PLAN이 확정`) |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 문서 포맷 | Markdown | - |
| 스펙 포맷 | JSON | `pipeline.json` |
| 검증 도구 | Python 3 (state-tool) | `spec-validate` 서브커맨드만 사용, 코드 변경 없음 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음) | 프레임워크 문서 편집 태스크 — 별도 외부 스킬 불필요 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | 외부 라이브러리 조사 없음 |

## 7. 지정 분석 질문 Q1~Q6 답변

### Q1 — 계약 해소 3안 실측 비교 + 권고안

| 안 | 변경 파일 수(실측) | 기존 산출물 호환성 | 게이트 파급 | 아키텍처 정합성 |
|----|---------------------|---------------------|------------|-----------------|
| ⓐ PLAN §2.N.1 하위 표 별도 규정 | plan-guide.md(신규 서브표 규정, 텍스트 증가) **+** SKILL.md(원천 데이터 보강 불가피 — ⓑ 또는 ⓒ 중 하나를 반드시 동반) **+** pipeline.json **+** analysis-core.md:59 = **최소 4~6파일**, ⓑ보다 항상 같거나 많음(규정만 추가하고 데이터 원천은 그대로면 실행 불가) | ⓑ·ⓒ와 동일(원천 미확정) | ⓑ와 동일 파급 + PLAN 쪽 신규 서브표 문서화 부담 | 규정 이중화 — "표를 승계하라"는 요구와 "표에 들어갈 필드를 또 규정"하는 지시가 plan-guide.md에 중복 축적 |
| ⓑ 2.N.1 승계 원천을 ANALYSIS §1.1로 재지정 + §1.1에 영역 열 추가(M-1) | SKILL.md(§1.1+§8 명확화) + plan-guide.md(:92,96,102 원천 재지정) + pipeline.json(체크리스트 1건 추가) + analysis-core.md(:59 재지정) + qa 거울 사본 2개 = **6파일**, TASK.md 범위표의 5파일과 거의 일치(analysis-core.md만 추가) | §1.1 열 추가는 구 산출물 대비 초과 컬럼 — 레거시 호환 예외(citation-rules §5)로 문제 없음. §8은 스키마 불변이라 완전 호환 | pipeline.json 기존 항목(3열 체크) **불변**, 신규 항목 1건만 **추가** — 최소 파급 | `analysis-core.md` §5가 이미 정의한 6영역 축(D-13 "절차 SSOT")을 §1.1이 그대로 소비하도록 만들 뿐 — SSOT 재정의·값복제 없음 |
| ⓒ ANALYSIS §8 핸드오프 표 스키마 자체 확장 | SKILL.md(§8 3→N열) + plan-guide.md(경미) + pipeline.json(**기존 항목 문구 전면 재작성** — 열 수 변경) + analysis-core.md(:59, §8 스키마 인용부 동반 수정) + qa 거울 사본 2개 = **6파일**이나 pipeline.json 항목이 신규 추가가 아니라 **교체**라 회귀 리스크가 더 큼 | §8이 결정형 항목(예: task:100의 "구현 순서"·"install 재배포 리스크")과 파일형 항목을 한 표에 섞어야 해 **희소 표**(결정형 행은 파일경로/영역 칸이 공란) 발생 — 기존 3열 산출물과 완전 비호환(전 칸 재작성 필요) | 체크리스트 item[2]를 열 수까지 문자열 재작성해야 함(문구 rewrite, 부수 참조 누락 위험 ↑) | `analysis-core.md` §5의 6영역 축을 §8에 **재정의**하는 셈 — "SSOT는 포인터, 값 복제 금지" 원칙(D-13)과 충돌 소지 |

**권고안(ⓑ)**: 2.N.1의 승계 원천을 §8(다음 단계 입력)에서 **§1.1(관련 파일 목록)로 재지정**하고, §1.1에 M-1(영역 열)을 동시 적용한다. §8은 파일 단위가 아닌 결정형 확정값(구현 순서, 배치 리스크 등, D-7 실사용례 참조)의 3열 스키마를 그대로 유지한다.

- **근거 1(파급 최소)**: 위 표 실측대로 ⓑ는 pipeline.json 기존 체크리스트 항목을 건드리지 않고 1건만 추가한다. ⓐ·ⓒ는 각각 규정 이중화 또는 항목 전면 재작성이 필요하다.
- **근거 2(아키텍처 정합)**: `analysis-core.md` §5는 이미 "관련 파일 맵 6영역 축"이라는 명칭으로 이 축을 소유하고 있다(§5 표제 자체가 "관련 파일 맵"). ⓑ는 ANALYSIS §1.1("관련 파일 목록")이 그 SSOT를 뒤늦게 소비하도록 연결할 뿐 새 스키마를 만들지 않는다. ⓒ는 §8에 같은 축을 다시 새겨 넣어 SSOT 포인터 원칙(D-13)을 훼손한다.
- **근거 3(레거시 비파괴)**: §8은 스키마 불변이므로 §8을 인용하는 다른 규범(analysis-core.md:59 자체는 원천 지시만 §1.1로 갈아탄다) 외에는 부수 파손이 없다.
- **[MUST]** `op-dev-analysis/SKILL.md:97-99` §1.1 표에 현재 영역 열이 없다는 제약(TASK.md 지정)은 ⓑ의 전제 조건 M-1로 흡수했다 — ⓑ는 M-1을 함께 채택해야 완결된다(M-1 단독 기각 시 ⓑ 성립 불가).

### Q2 — PLAN 2.N.1 승계 필드 확정

| 소스 | 필드 목록 | 판정 |
|------|----------|------|
| `tasks/100-.../DONE.md` §6 S-33 | "파일·6영역 라벨·변경 유형·**순서**" 4개 | **현행 소스와 불일치** — plan-guide.md 전체에서 "순서"는 §4 실행 체크리스트 "의존성 순서: 하위 레이어 먼저"(`:219`)에만 등장하고, 이는 Step 배치 규칙이지 §2.N.1/§3.N.1 파일 맵 컬럼 규정이 아니다. DONE.md 서술은 task:100 자체의 사후 요약(회고)이며 원 컬럼 규정 원문을 다시 인용한 것이 아니다. |
| `plan-guide.md:351` | `영역 \| 경로 \| 역할 \| 변경유형` 4열, 순서 없음 | **현행 소스와 일치** — 이 줄 자체가 "관련 파일 맵 컬럼 / §2.N.1 하위 테이블" 파싱 규칙 원문이며(§PLAN.md 파싱 규칙 표), `analysis-core.md:102-104`의 6영역 축 표(`영역\|경로\|역할\|변경 유형`)와 컬럼명·순서까지 동일하다(교차 확인). |

**확정 목록(근거 포함)**: PLAN 2.N.1이 승계받아야 하는 필드는 **영역·경로·역할·변경유형 4개**다(`plan-guide.md:351` = `analysis-core.md:102-104`, 두 소스가 동일 4필드로 상호 확인됨). "순서"는 §2.N.1 필드가 아니다.

### Q3 — M-1(§1.1 영역 열 추가) 파급 범위 실측

| 축 | 실측 결과 |
|----|----------|
| PM Gate | `pipeline.json:13`(task_steps[3])은 §1.1 컬럼 수를 검사하지 않는다(§다음 단계 입력=§8만 체크) — 열 추가 자체는 게이트를 깨지 않는다. 단, Q1 권고안(ⓑ) 채택 시에는 §1.1이 새 승계 원천이 되므로 **신규 검사 항목 1건 추가**가 필요(R-2 소관). |
| QA 검증 축(op-dev-qa) | ANALYSIS R-1~R-8 중 §1.1 컬럼 수를 명시 검사하는 항목은 0건(R-2 "변경 파일 완전성"·R-3 "변경 파일 완전성"은 목록 누락 여부만 확인). PLAN P-4("파일 목록 일치")도 파일 존재 여부 매칭이라 컬럼 수 불변경. **M-1 단독으로는 QA 검증 축 파손 0건.** |
| 기존 태스크 산출물 호환성 | task:100 ANALYSIS.md(D-7)는 이미 4열 템플릿을 5열(순서(Tier) 추가)로 임의 확장해 사용한 선례가 있다 — 열 추가가 실무에서 이미 1회 발생했다. `state_tool.py`에는 §1.1 파싱 함수가 없음(Bash 검증, `grep -n "관련 파일\|1\.1" state_tool.py` → 무관 매치만 반환) — 도구 파손 리스크 0. `citation-rules.md` §5 "레거시 호환" 원칙에 따라 구 산출물 소급 변경 불요. |

**결론**: M-1(영역 열 추가)의 **독자적** 파급은 게이트·QA·도구 3축 모두 0건이며, Q1 ⓑ안 채택 시에만 게이트 쪽에 신규 항목 1건 추가가 뒤따른다.

### Q4 — M-2(`승계` 토큰 이의 충돌) 실제 혼동 여부 판정

**판정: 실제 혼동 지점 없음 — 이번 태스크 범위 제외 타당.**

- ANALYSIS `확정 입력 판정` 표의 `승계`는 ANALYSIS 워커가 산문으로 직접 기재하는 값이며 대상 산출물은 `ANALYSIS.md`다(`op-dev-analysis/SKILL.md:27`).
- state-tool verdict `승계`는 `state-tool verify --evidence-check`가 **TASK.md** `## 확정된 설계 방향` 섹션의 최상위 불릿을 `_locate_confirmed_direction_items()`로 파싱해 계산하는 JSON 출력이다(`state_tool.py` 변경이력 100번 항목, `_has_fact_tag()`/`_CONFIRMED_VERDICTS` 신설 서술). 파싱 대상 섹션명("확정된 설계 방향")과 문서(TASK.md)가 ANALYSIS `확정 입력 판정`(문서: ANALYSIS.md, 섹션명 다름)과 다르다.
- Bash로 `state_tool.py`를 검색한 결과(§0 2단 code-scan 대체 조사), ANALYSIS.md의 "확정 입력 판정" 표를 파싱하는 함수는 존재하지 않는다 — 두 값 집합이 같은 표·같은 렌더 경로에서 동시 노출되는 지점이 소스 상 확인되지 않는다.
- 따라서 `citation-rules.md` §7.1 "영역 간 용어 일관성 검출 대상"에 해당하는 실질 위험(같은 화면·같은 표에서 다른 의미로 나타나 혼동)은 이번 케이스에서 성립하지 않는다 — 두 값은 서로 다른 문서·다른 소비자를 향한 **평행한 어휘**일 뿐이다.

### Q5 — M-3(op-dev-qa 검증 축 3개) Q1 권고안 적용 시 영향 + 동반 개정 파일

| 검증 ID | Q1(ⓑ) 적용 시 영향 | 동반 개정 필요 |
|---------|---------------------|----------------|
| R-7(원문 덤프 차단) | 무영향 — 코드펜스/원문 블록 검사이며 §1.1·§8 스키마와 무관 | 불필요 |
| R-8(098 규약 준수) | 무영향 — "확정 입력 판정" 표(본 산출물 최상단)를 검사하는 축이며 §8 핸드오프 표와는 별개 섹션 | 불필요 |
| P-8(확정 승계 준수) | **파손** — 현재 문언 "ANALYSIS 핸드오프 표 항목을 재도출 없이 인용"이 어느 표를 가리키는지 불명확해진다. Q1(ⓑ) 채택 시 파일 맵 항목의 실제 승계 원천이 §8→§1.1로 바뀌므로, PM Gate 검증자가 여전히 §8만 대조하면 §1.1 재도출 위반을 놓친다 | **필요** — `opal/skills/op-dev-qa/SKILL.md:121,123` + `opal/skills/op-dev-qa/references/qa-dev-guide.md:93`(거울 사본 2곳, H-4 동시 갱신) — 문언에 "§1.1 관련 파일 목록(파일 맵) + §8 다음 단계 입력(결정형 확정값)" 이중 지정 추가 |

### Q6 — pipeline.json `task_steps[3].gate.checklist` 원문 전건 + Q1 적용 시 수정 항목

**원문(4항목, `opal/skills/opal-pilot-dev/references/pipeline.json` id=4, key=`analysis.pm_gate`)**:

| # | 체크리스트 원문 |
|---|----------------|
| item[0] | ANALYSIS.md §0 참조 문서 — code-scan·brain 선조회 결과 1건 이상 |
| item[1] | ANALYSIS.md §확정 입력 판정 — TASK.md [결정]·[사실] 전건 판정(누락 0) |
| item[2] | ANALYSIS.md §다음 단계 입력 — 항목\|확정값\|근거 3열 표 존재 |
| item[3] | 소스코드 원문 블록 0건 (코드펜스는 실행 명령·시그니처 한정) |

**Q1(ⓑ) 적용 시 수정 항목**:

- item[0], item[1], item[3] — **불변**(§0/§확정 입력 판정/원문 차단 검사는 스키마 변경과 무관).
- item[2]("§다음 단계 입력 — 항목|확정값|근거 3열 표 존재") — **문구 자체는 불변**(§8은 결정형 확정값 표로 존속하며 3열 스키마도 유지). 단, R-1의 AC("구형 3열 단독 계약을 지시하는 문장이 전 소스에서 0건")를 충족하려면 이 항목이 "파일 맵 전체를 커버하는 유일한 계약"으로 오독되지 않도록 **신규 item 추가**가 필요하다: 예) `"ANALYSIS.md §1.1 관련 파일 목록 — 영역 열 포함(analysis-core.md §5 6영역 축 정합)"`. 항목 수는 4→**5개**로 증가(R-2 소관, 정확한 문구는 PLAN이 확정 — task:100 ANALYSIS.md의 동일 패턴 선례, §8 PLAN 결정 필요 참조).

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| 계약 불일치 지점 수 | 3곳이 아니라 **4곳**(plan-guide.md:92,96,102 / SKILL.md:165-166 / pipeline.json:13 / **analysis-core.md:59**) | §7 Q1, §4 핵심 발견 1 |
| 권고 해소안 | ⓑ — PLAN 2.N.1 승계 원천을 §8→§1.1로 재지정 + §1.1에 영역 열 추가(M-1 긍정 채택) | §7 Q1 |
| PLAN 2.N.1 확정 필드 목록 | 영역·경로·역할·변경유형 4개(순서 없음) — `plan-guide.md:351` = `analysis-core.md:102-104` 상호 확인 | §7 Q2 |
| M-1 판정 | 채택(영역 열 추가) — 게이트·QA·도구 3축 독자 파급 0건 실측 확인 | §7 Q3 |
| M-2 판정 | 이번 태스크 범위 제외 — 두 `승계` 값이 같은 표·문서에서 동시 노출되는 경로 없음(실질 혼동 없음) | §7 Q4 |
| M-3 판정 | R-1 부수 작업으로 포함 — P-8만 파손, R-7·R-8은 무영향. `op-dev-qa/SKILL.md:121,123` + `qa-dev-guide.md:93` 거울 사본 2곳 동시 개정 | §7 Q5 |
| pipeline.json 체크리스트 item[2] | 문구 불변(§8 3열 스키마 유지) — item[2]를 재작성하지 않는다 | §7 Q6 |
| pipeline.json 체크리스트 신규 item | §1.1 영역 열 포함 여부 검사 1건 추가(4→5항목), 정확한 문구는 PLAN이 확정 | §7 Q6 |
| §8(다음 단계 입력) 스키마 | **불변** — 3열(`항목\|확정값\|근거`) 유지, 결정형 확정값(구현 순서·배치 리스크 등) 전용으로 역할 축소 | §7 Q1 |
| R-4 판정값 스킴 | 결정 계열 `해당없음(결정)` + 사실 계열 `유효(대조 확인)`/`수정필요`/`사실오류` 2분리(task:100 grill 반영본과 동일) | §확정 입력 판정, D-7 |
| 변경 대상 파일(총 6개) | `op-dev-analysis/SKILL.md`·`op-dev-plan/plan-guide.md`·`opal-pilot-dev/pipeline.json`·`analysis-core.md`·`op-dev-qa/SKILL.md`·`op-dev-qa/qa-dev-guide.md` | §1.1, §7 Q1·Q5 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| `analysis-core.md`를 TASK.md 범위(§범위 포함)에 추가할지 | TASK.md 범위표에 미등재된 4번째 계약 지점이라, PLAN이 소유자에게 범위 확장을 명시 확인받거나 자체 판단으로 포함할지 결정 필요(포함하지 않으면 R-1 AC 미충족) | §확정 입력 판정 [사실] 2, §4 핵심 발견 1 |
| §1.1 신규 컬럼의 정확한 헤더 표기·위치 | "영역"을 첫 컬럼에 둘지(analysis-core.md §5 순서 정합) 마지막에 둘지, "변경 필요"를 "변경유형"(신규/수정)으로 명칭까지 통일할지는 PLAN이 설계 | §7 Q2·Q3, `op-dev-analysis/SKILL.md:97-99` |
| pipeline.json 신규 item 정확한 문구 | 스키마 제약(비어있지 않은 문자열 배열)과 기존 4항목 스타일은 확정됐으나, 구체적 문구는 SKILL.md §1.1 최종 형식 확정 후 PLAN이 결정(task:100의 동일 선례 — `tasks/100.../ANALYSIS.md:329`) | §7 Q6 |
| P-8 문언에 §1.1/§8 이중 지정을 어떤 표현으로 쓸지 | "핸드오프 표"라는 포괄 용어를 유지하며 괄호 병기할지, 두 항목으로 분리할지(P-8/P-8b) PLAN이 결정 | §7 Q5 |

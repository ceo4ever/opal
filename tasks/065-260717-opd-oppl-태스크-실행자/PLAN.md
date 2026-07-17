# PLAN: oppl 태스크 실행자(opal-loop-action-agent) 도입 — 태스크 단위 컨텍스트 격리

> 작성일: 2026-07-17 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡
> 트랙: 개발 (프레임워크 md 문서 산출물)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

oppl(opal-pilot-project-loop)의 태스크 내부 파이프라인(T1~T5+G)을 **태스크당 1회 디스패치되는 일회용 실행자 `opal-loop-action-agent`**에 위임하여, PM 세션의 컨텍스트 누적을 "태스크당 결과 보고 1건" 수준으로 격리한다. 실행자는 생성자·Evaluator·test-agent를 **각각 별도 에이전트로 내부 디스패치**하여 검증 2원화(생성자≠평가자, H-9)를 유지하며, 비가역 행동·에스컬레이션은 위임받지 않고 `blocked`로 PM에 반환한다. PM의 루프 수준 판단(L0/L∞/done-check/사람 게이트/보고)은 불변이다 (→ D-1 §확정 방향 §1).

### 1.2 참조 문서 (§8.3에 전체 테이블 — 여기서는 [MUST] 제약 인용)

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 본 PLAN의 모든 `changed_files`는 프로젝트 소스 경로(`opal/agents/`, `opal/skills/`)여야 한다.
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다." (일시 `YYYY-MM-DD HH:mm` KST + semver + 태스크 번호 065 괄호 포함)
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/` …)에서 수행한다."
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: "구체적 재시도 횟수·최대 반복 수는 여기서 새로 정의하지 않는다." → 신규 AGENT.md도 하네스 §1 표를 **참조만** 하고 수치를 복제하지 않는다.
- [MUST] `opal/skills/opal-pilot-project-loop/references/verification.md` §3: "이 순서가 뒤바뀌면 명세 리뷰 게이트가 무력화된다(H-9)." → 실행자 내부에서도 G(구현 전)→test-agent(구현 후) 순서가 강행되어야 한다.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `opal-loop-action-agent` 신규 에이전트 정의 | R-1, R-3(일부) | P0 | 없음 |
| F-002 | oppl SKILL.md 태스크당 실행자 1회 디스패치 개편 | R-2, R-3(일부) | P0 | F-001 |
| F-003 | references 정합 갱신 (loop-control·contract, verification 무변경) | R-4 | P0 | F-002 |
| F-004 | 배포 반영 + 동작 실증 | R-5, R-6 | P1 | F-001, F-002, F-003 |

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 (에이전트 정의) ─→ F-002 (SKILL.md 개편) ─→ F-003 (references 정합) ─→ F-004 (배포·실증)
```

> 순차 의존: 신규 AGENT.md가 실행자 계약을 확정한 뒤에야 SKILL.md가 그 계약을 참조해 개편되고, references는 개편된 SKILL.md 서술과 모순 없이 정합되어야 하며, 실증은 세 산출물이 모두 확정된 후 수행한다 (→ TASK.md §설계 요구사항 5 Phase 그룹핑).

### 1.5 핵심 설계 결정 (M-N)

| ID | 결정 | 근거 |
|----|------|------|
| M-1 | **입력 명세 10필드 확정** — ANALYSIS §2.1 제안 9필드 + `acceptance`(수용기준 배열) 추가 | 수용기준은 T2 RED-first 시나리오·G 루브릭 판정의 기준 원천 (→ D-6 §2.3 루브릭절); opsdd `ac_mapping` 선례 (→ D-3 §입력 명세) |
| M-2 | **내부 디스패치 토폴로지 4축 분리** — 생성자(T1 op-dev-plan / T3 op-dev-execute 재개) · Evaluator(G) · test-agent(T2 RED / T4a GREEN) · conv·sec-checker(T4b) 각각 별도 에이전트 | 생성자≠평가자 유지(H-9) (→ TASK.md §확정 방향 §3); oppd 선례 내부 재디스패치 (→ D-2 §실행 프로세스) |
| M-3 | **3-SSOT 도구 호출 경계** — 실행자는 `test-tool scenario-*`만 호출하고 `backlog-tool`·`state-tool`은 호출하지 않는다 | backlog(L∞)·STATE는 PM 단독 갱신 오너십 (→ D-1 §병렬 실행 "STATE.md는 PM 단독 갱신", §L∞); test-scenario는 태스크 내부 tool-gated 증거 |
| M-4 | **CONTRACT drift 경계 (ANALYSIS §3.3 refine)** — 실행자는 `CONTRACT.md`를 직접 수정하지 않는다. 계약 미접촉(#1)은 정상 진행, 계약 갱신이 필요한 drift(#2~#4)는 `blocked` 반환 → PM이 오너십 계층 분류·반영·에스컬레이션 | CONTRACT 반영=PM 헌법 (→ D-4 §3); 생성자≠평가자 + opal-task-action-agent §8 "WBS/TRD/PRD 직접 수정 금지" 선례 (→ D-2 §행동 규칙 8) |
| M-5 | **결과 계약 6필드 확정** `{task_id, verdict, scenario_results, changed_files, done_md_path, blockers}` | TASK.md §확정 방향 §5 (→ D-7); ANALYSIS §2.3 압축형 |
| M-6 | **재시도 상한 = harness §1 포인터만** (수치 복제 금지). G 재작업=`PLAN 재진입` 행 / 구현 수준(L1~L3b)=해당 행 | [MUST] loop-control.md §2 (→ D-5 §2) |
| M-7 | **blocked 반환 트리거 목록 명문화** — 비가역 행동·에스컬레이션·계약갱신 drift·무진전·상한 초과·하드블로커·decision_required(용어 불일치) | TASK.md §확정 방향 §4; loop-control.md §7 하드블로커·§9 사람 게이트 (→ D-5) |
| M-8 | **검증 2원화 순서 강행 가드** — G(구현 전)가 T3 이전 완료, T4a(구현 후)는 T3 완료 후, timestamp evidence(QA-SPEC < result존), `scenario-lock` red_not_confirmed 시 G 진입 금지 | [MUST] verification.md §3 순서 불변 4항목 (→ D-4 검증 §3) |
| M-9 | **T5 DONE.md 작성 주체 = 실행자** — 결과 계약 소스(scenario_results·verification_log)를 실행자가 보유 | opal-sdd-action-agent가 TEST.md를 직접 작성하는 선례 (→ D-3 §5단계) |
| M-10 | **verification.md 무변경 확정** — §3 순서 논리는 주체 중립적(PM/실행자 동일 적용) | ANALYSIS §3.2; 무변경이므로 변경이력 행 추가하지 않음 |
| M-11 | **실행자 STATE.md 직접 갱신 금지** — PM에게 위임 | opal-task-action-agent §행동 규칙 2 mirror (→ D-2) |
| M-12 | **배포(install-mac.sh 실행)는 사람 게이트** | [MUST] loop-control.md §9 배포 범주 (→ D-5 §9) |
| M-13 | **frontmatter 확정** — name `opal-loop-action-agent`, model `advanced`, icon `🔁` | 계열 관례(TASK.md §확정 방향 §2); action 에이전트 model advanced 선례 (→ D-2·D-3 frontmatter) |

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다. ANALYSIS §6의 4대 리스크 + 설계 결정에서 파생한 3건.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 AGENT.md 실행 프로세스 | 검증 2원화 순서 역전 — G(Evaluator, 구현 전)와 T4a(test-agent, 구현 후) 순서가 실행자 내부에서 뒤바뀌면 G 게이트 무력화(H-9) | P0 | L2(문서 순서 가드 명시) + L3(실증: timestamp evidence QA-SPEC < result존) | S-1 |
| H-2 | F-001 blocked 반환 계약 | 비가역 행동(배포·DB·확정) 무단 진행 — 실행자가 사람 게이트 대상 행동을 자율 실행 | P0 | L2(blocked 트리거 목록 명시) + L3(실증: 비가역 트리거 주입 시 blocked 관찰) | S-2 |
| H-3 | F-001 재시도 상한 절 | 재시도 상한 SSOT 복제 — AGENT.md에 수치를 하드코딩하면 harness §1 SSOT와 drift | P1 | L1(grep: AGENT.md에 재시도 정수 리터럴 부재 + harness §1 포인터 존재) | S-3 |
| H-4 | F-001·F-002 tool-gated 증거 | PM 컨텍스트 손실 — G verdict 직접 관찰을 잃은 PM이 사후 검증할 증거(QA-SPEC.md·test-scenario.json·verification_log)가 산출되지 않음 | P1 | L2(산출물 자동생성 규칙 명시) + L3(실증: 태스크 폴더에 5종 증거 존재) | S-4 |
| H-5 | F-001 3-SSOT 도구 규칙 (M-3) | 3-SSOT 경계 침범 — 실행자가 `backlog-tool`/`state-tool`을 직접 호출하여 PM 단독 갱신 오너십·동시 쓰기 안전성(H-3) 침범 | P1 | L1(grep: AGENT.md에 backlog-tool·state-tool run.sh 호출 부재) + L3(실증: 실행자 로그에 두 도구 미호출) | S-5 |
| H-6 | F-001·F-003 CONTRACT 경계 (M-4) | CONTRACT drift 무단 반영 — 실행자가 `CONTRACT.md`를 직접 수정(생성자≠평가자·PM 반영 헌법 위반) | P1 | L2(AGENT.md 금지 규칙 + contract.md §4 경계 명시) | S-6 |
| H-7 | F-001 T2 RED-first | RED self-confirming 우회 — 실행자가 `scenario-red` 증거 없이 `scenario-lock`으로 동결하여 RED 미관찰 상태를 G에 진입 | P0 | L1(도구 계약: init red_confirmed=false 시드 무력화, lock red_not_confirmed 거부 — 기존 tool-gated) + L3(실증: 증거 없는 lock 거부) | S-7 |

**깨질 수 있는 계약 도출 근거**:
- H-1: `verification.md` §3 "순서 불변 규칙" 4항목 — G가 T3 이전, T4a가 T3 이후. 순서 역전은 하드블로커(loop-control.md §7).
- H-2·H-6: `loop-control.md` §9 사람 게이트 + `contract.md` §4 오너십 계층 — 비가역/외부노출은 실행자 권한 밖.
- H-7: SKILL.md §T2 "scenario-init은 red_confirmed를 항상 false로 생성 … locked 이후 scenario-red 거부" (056/ADD-1) — 실행자가 이 tool-gated 순서를 그대로 준수해야 한다.

---

## 2. 기능별 분석

### F-001: `opal-loop-action-agent` 신규 에이전트 정의

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 실행자 정의 (frontmatter·입력·프로세스·계약) | 신규 |
| 에이전트 | `opal/agents/opal-task-action-agent/AGENT.md` | 준거 구조 (입력 명세·내부 재디스패치·VERIFY·결과 계약) | 참조 |
| 에이전트 | `opal/agents/opal-sdd-action-agent/AGENT.md` | 동형 선례 (VERIFY 구조 참조·자체 산출물 작성) | 참조 |

#### 2.1.2 현재 구현 (ANALYSIS 참조)

- oppd 선례(`opal/agents/opal-task-action-agent/AGENT.md`)는 `## 입력 명세`(7필드 표) → `## 실행 프로세스`(6단계 ASCII + 단계별 상세) → `## 결과 반환 형식`(성공/실패 JSON) → `## 행동 규칙` → `## 참조 문서` → `## 변경이력` 골격을 사용한다 (→ D-2). Evaluator에 해당하는 명세 리뷰 게이트는 없고 QA(opal-task-qa-agent)를 쓴다.
- opsdd 선례(→ D-3)는 자신이 산출물(TEST.md)을 직접 작성하고, VERIFY 구조를 oppd AGENT.md로 포인터 참조한다.
- oppl 태스크 내부 파이프라인은 이들과 달리 **G 명세 리뷰 게이트(Evaluator, 구현 전)**와 **RED-first 동결(test-tool scenario-*)**을 갖는다 (→ D-1 §태스크 내부 파이프라인 줄 284~339). 실행자는 이 두 요소를 내부로 흡수하되 도구 호출 경계(M-3)와 순서 가드(M-8)를 지켜야 한다.

#### 2.1.3 영향 범위

- **호출자(상위)**: oppl PM(L0 태스크 선택 후 태스크당 1회 디스패치). 실행자 완료 후 PM이 backlog-tool mark·STATE mark로 상태 반영.
- **피호출자(하위)**: 생성자(opal-fe/be/db/task-agent), opal-evaluator-agent, opal-test-agent, opal-convention-checker, opal-security-checker — 모두 기존 에이전트 재사용(신규 없음).
- **워커 중첩 깊이**: PM(L0) → 실행자(L1) → 워커(L2) = 2단계 (oppd Phase 3 동형, → D-2·ANALYSIS §5).
- **배포 경로**: `install-mac.sh`가 `opal/agents/*`를 자동 포함 (→ ANALYSIS §4·D-8) — 신규 에이전트는 별도 스크립트 수정 없이 배포된다.

### F-002: oppl SKILL.md 태스크당 실행자 1회 디스패치 개편

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 본문 — 태스크 내부 파이프라인·디스패치·검증 2원화·스킬 탐색 경로 | 수정 |

#### 2.2.2 현재 구현 (ANALYSIS §1.2 참조 — 11개 개편 지점)

`opal/skills/opal-pilot-project-loop/SKILL.md`의 현재 서술은 **PM이 태스크당 노미널 ~3회 디스패치**(하이브리드 C)를 직접 지휘하는 구조다 (→ D-1 줄 343~365). ANALYSIS §1.2가 전수한 11개 지점(줄번호 포함)이 개편 대상이다:

| # | 절 | 줄(현재) | 현재 서술 요지 | 변경 방향 |
|----|-----|---------|--------------|----------|
| 1 | §T1 명세·설계 | 306 | "생성자를 resolve하여 디스패치한다" | "실행자가 생성자를 resolve하여 내부 디스패치" |
| 2 | §T1 마커 | 289 | "[생성자 디스패치]" | "[실행자→생성자 내부 디스패치]" |
| 3 | §T2 | 308~315 | "동일 생성자 디스패치 내에서(또는 연속 호출로)" | "실행자가 scenario-* 도구를 호출, test-agent(red)를 내부 디스패치" |
| 4 | §G 게이트 | 317~327 | "[워커 디스패치] opal-evaluator-agent를 디스패치" | "실행자가 opal-evaluator-agent를 내부 디스패치" |
| 5 | §T3 마커 | 296·329 | "[생성자 디스패치 재개]" | "[실행자→생성자 재개 지시]" |
| 6 | §T4a | 298·331~335 | "[워커 디스패치] opal-test-agent를 디스패치" | "실행자가 opal-test-agent를 내부 디스패치" |
| 7 | §T4b | 301·337 | "저위험 인라인 / 고위험 디스패치" | "실행자가 규모 판정 후 인라인 또는 내부 디스패치" |
| 8 | §디스패치 표 | 347~351 | 표 ①②③ (PM 직접) | "실행자 내부" 명시 — PM 디스패치는 실행자 1회 |
| 9 | §디스패치 설명 | 345·353 | "태스크당 노미널 ~3회 디스패치" | "PM은 태스크당 실행자 1회 디스패치 (내부 생성자/Evaluator/test-agent 별도)" |
| 10 | §디스패치 idiom | 355~364 | "생성자 도메인 resolve" + "T1~T3 범위로 한정된 지시" | "실행자가 도메인 resolve 후 생성자 내부 디스패치" + "T1~T5+G 전체가 실행자 위임 범위" |
| 11 | §검증 2원화 | 368~371 | "순서가 뒤바뀌면 G 게이트 무력화" (주체 PM) | 내용 유지, 주체를 "실행자 내부"로 명시 |

#### 2.2.3 영향 범위

- **소비자**: oppl PM(런타임), install(배포), Loop 2 실행 흐름. 개편이 PM의 L0/L∞/게이트 소유를 건드리면 안 된다 (→ TASK.md R-2 AC "PM의 L0/L∞/게이트 소유는 변경 없음").
- **정합 대상**: §자율 게이트 흐름(줄 422~431)의 "Loop 2 L0~L✓ PM 자율 관리 (태스크별 G 게이트 + T4a/T4b 포함)"는 실행자 위임 후에도 유효하므로 문구를 "태스크별 실행자 디스패치"로 정합.
- **하류 문서**: references 3종(F-003)이 SKILL.md 개편과 모순 없어야 한다.

### F-003: references 정합 갱신

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | §3 예산 절 "하이브리드 C" 서술 정합 | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-loop/references/contract.md` | §4 오너십 계층에 실행자 drift 경계 명시 | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §3 순서 논리 (주체 중립) | 무변경(근거 기록) |

#### 2.3.2 현재 구현 (ANALYSIS §3 참조)

- **loop-control.md**: ANALYSIS §3.1이 "줄 50"으로 지목. 실제 본문(→ D-5 §3 줄 50)은 "디스패치 하이브리드 C(생성자 1회 + Evaluator 1회, 태스크당 ~2~3 디스패치 — SPEC §03 note)를 초과하는 재디스패치가 반복되면 예산 소진 신호로 간주"다. 예산 관찰 단위를 "실행자 1회 디스패치(내부 재디스패치는 실행자 자체 예산 관리)"로 정합해야 한다. §2 상한 참조 원칙은 불변.
- **contract.md**: §4 오너십 계층 4단계(줄 54~74)는 판단 주체가 PM/통합 게이트/사용자다. **실행자가 CONTRACT.md를 직접 수정하지 않고 계약 갱신 필요 drift는 blocked 반환한다**는 경계(M-4)를 §4 또는 §5에 추가해야 한다 (→ D-6).
- **verification.md**: §3 순서 불변 규칙은 "누가"에 무관한 순서 논리(G before T3, T4a after T3). 주체가 PM이든 실행자든 동일 적용되므로 무변경. PLAN이 무변경 근거를 명시적으로 기록(M-10).

#### 2.3.3 영향 범위

- 세 references는 SKILL.md `## 루프 제어`·`## CONTRACT 거버넌스`·`## 검증 2원화` 절이 인라인 참조한다. 개편된 SKILL.md 서술과 references가 상호 모순이 없어야 한다 (→ TASK.md R-4 AC "하이브리드 C 언급 지점 전수 확인").

### F-004: 배포 반영 + 동작 실증

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경(배포) | `scripts/install-mac.sh` | `opal/agents/*` 자동 포함 + 어댑터 배포 (줄 462~464, 641) | 무변경(확인만) |
| 배포 산출 | `~/.opal/agents/opal-loop-action-agent/` | install 후 배포 결과 (검증 대상) | 생성(런타임) |
| 문서 | `docs/PROJECT.md` | Project Loop 컴포넌트 표에 실행자 등록 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | oppl 구조에 실행자 계층 반영 | 수정 |

#### 2.4.2 현재 구현 (ANALYSIS §4 참조)

- install-mac.sh는 `install_claude_agents`·`emit_platform_agent_adapter`(→ D-8, 줄 462~464·641)로 `opal/agents/*`를 자동 변환 배포한다. 신규 에이전트 폴더를 두면 별도 스크립트 작업 없이 포함된다.
- `docs/PROJECT.md` §주요 컴포넌트(Project Loop 파이프라인) 표(→ 현재 줄 103~108)에는 oppl·evaluator·backlog-tool·test-tool만 있고 실행자가 없다. 실행자 도입은 "새 컴포넌트/에이전트 추가"이므로 문서 갱신 대상(plan-guide §4.2 docs 갱신 규칙: 시스템 구조 변경 → ARCHITECTURE.md).

#### 2.4.3 영향 범위

- 배포(install-mac.sh 실행)는 loop-control.md §9 "배포" 범주 = 사람 게이트(M-12) → TEST/CLOSE에서 사용자 승인 후 실행.
- R-6 실증은 배포 전에도 프로젝트 로컬 에이전트 정의(`opal/agents/opal-loop-action-agent/AGENT.md`)를 직접 참조시키는 방식으로 수행 가능(§7 C-4 참조).

---

## 3. 기능별 설계

### F-001: `opal-loop-action-agent` 신규 에이전트 정의

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | oppl Loop 2 태스크당 1회 디스패치 실행자 정의 | (→ D-2 구조 준거, D-1 §태스크 내부 파이프라인) |

#### 3.1.2 AGENT.md 설계 (섹션별)

**(a) frontmatter** (M-13):
```yaml
name: opal-loop-action-agent
description: |
  oppl Loop 2에서 태스크당 1회 디스패치되는 일회용 실행자.
  T1 명세·설계 → T2 RED-first 시나리오 → G 명세 리뷰(Evaluator 별도) → T3 구현
  → T4a 테스트(test-agent 별도) → T4b 규칙검사 → T5 마무리(DONE.md)를 내부 디스패치로 완주한다.
  검증 2원화(생성자≠평가자, H-9)를 내부에서 유지하며, 비가역 행동·에스컬레이션은 blocked로 PM에 반환한다.
model: advanced
icon: "🔁"
```
> `model: advanced` 근거: action 에이전트 계열 공통 (→ D-2·D-3 frontmatter). name·icon은 TASK.md §확정 방향 §2 계열 관례.

**(b) 입력 명세** (M-1 — 10필드 표):

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| task_id | O | 태스크 ID (예: `T01`) — backlog.json |
| task_goal | O | 태스크 목표 (title/slice) |
| task_scope | O | 변경 대상 파일/모듈 |
| task_area | O | `fe`\|`be`\|`db`\|`공통`\|`통합` — 생성자 도메인 resolve (→ D-1 §디스패치 표) |
| acceptance | O | 수용기준 배열 — T2 시나리오·G 루브릭 기준 [ANALYSIS 9필드에 추가 확정] |
| task_folder | O | 태스크 폴더 경로 `tasks/{NNN}-oppl-…/tasks/T{NN}-…/` |
| verify_commands | O | 검증 명령 (lint/build/test) — T3 자체검증·T4a |
| contract_path | O | `CONTRACT.md` 경로 (oppl 특화) — G 게이트·기계검증절 기준 |
| project_root | O | 프로젝트 루트 |
| project_context | O | 참조 문서 목록 (docs/PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md, CONTRACT.md) |

> 인라인 인용: 9필드는 (→ D-2 §입력 명세)·(→ D-3 §입력 명세) 준용, `acceptance` 추가는 (→ D-6 §2.3 루브릭절) — 수용기준이 RED-first·루브릭 판정의 기준 원천.

**(c) 실행 프로세스** (M-2·M-8 — T1~T5+G ASCII + 단계별 상세):
```
1. T1 명세·설계
   → 실행자가 task_area로 생성자 resolve → Agent 도구로 내부 디스패치 (op-dev-plan, model: advanced)
   → PLAN.md(태스크 미시설계 + 테스트 시나리오) 생성
   → blocked 반환 시 status: blocked

2. T2 테스트시나리오 (RED-first) — 실행자가 도구 호출 주체 (M-3)
   → 실행자: test-tool scenario-init (PLAN.md 시나리오 기반; red_confirmed=false 시드)
   → 실행자→opal-test-agent(mode: red) 내부 디스패치 → 실패 테스트 작성·실행(RED 실관찰)
   → 실행자: scenario-red --evidence → scenario-lock (red_not_confirmed면 G 진입 거부, H-7)

3. G 명세 리뷰 게이트 (Evaluator, 구현 전) ★검증 2원화 ① (H-1)
   → 실행자→opal-evaluator-agent 내부 디스패치 (phase: spec-review, contract_path 전달)
   → verdict fail → T1 재작업 (상한: harness §1 'PLAN 재진입' 행 — 수치 복제 금지, M-6)
   → verdict pass → T3

4. T3 구현
   → 실행자→생성자(T1과 동일 에이전트) 재개 지시 (op-dev-execute, model: standard)
   → 하네스 §1 lint/build/test 재시도 한도 내 자체 검증
   → changed_files 반환

5. T4a 테스트 (test-agent, 구현 후) ★검증 2원화 ② (H-1)
   → 실행자→opal-test-agent 내부 디스패치 → test-scenario.json 시나리오 실행
   → 실행자: scenario-mark(result) → scenario-status
   → fail → T3 재작업 (하네스 §1 한도) / 회귀 → 즉시 blocked

6. T4b 규칙검사
   → 실행자가 규모 판정: 저위험 = 인라인 요약 / 고위험 = conv·sec-checker 내부 디스패치

7. T5 마무리
   → 실행자가 DONE.md 작성 (M-9) → 결과 계약 반환
```

**순서 강행 가드** (M-8, [MUST] verification.md §3):
- G(구현 전)는 항상 T3 이전 완료 — verdict fail이면 T3 진입 금지.
- T4a(구현 후)는 T3 완료 후에만 — 구현 없는 상태에서 test-agent 호출 금지.
- **순서 evidence**: QA-SPEC.md(G) 시점 < test-scenario.json result존(T4a) 시점 (→ D-4 검증 §3 "순서 증거").
- `scenario-lock`이 `red_not_confirmed` 반환 시 G 진입 금지 (self-confirming 차단, H-7).
- drift 재콜백(구현/테스트 중 CONTRACT 불일치)은 2원화 순서의 유일한 예외이나, 실행자는 계약 갱신을 수행하지 않고 blocked 반환(M-4).

**(d) 재시도 상한** (M-6, [MUST] loop-control.md §2):
- 구현 수준(L1 lint~L3b E2E): `opal/core/references/opal-harness.md` §1 자동 루핑 제약 표를 **참조** (수치 복제 금지).
- 설계 수준(G 게이트 루브릭 미달·PLAN 재진입): harness §1 "PLAN 재진입" 행 참조.
- 상한 초과 → 자율 재시도 중단 → blocked 반환(에스컬레이션).

**(e) blocked 반환 계약** (M-7):
- 트리거: ① 비가역 행동(배포·DB·확정) 요구 ② 에스컬레이션 대상 ③ 계약 갱신 필요 drift(#2~#4) ④ 무진전 감지 ⑤ 반복 상한 초과 ⑥ 하드블로커(순서 역전·SSOT 손상·readonly 위반) ⑦ decision_required(용어 불일치, citation-rules §7.5).
- 처리: `status: blocked` + `blockers[]`(사유·유형) 반환. 실행자는 소유자에게 직접 에스컬레이션하지 않고 PM이 수행 (→ TASK.md §확정 방향 §4).

**(f) 결과 반환 형식** (M-5 — 6필드):
```json
{
  "task_id": "T01",
  "verdict": "All Pass | Partial Fail | Critical Fail | blocked",
  "scenario_results": [{"id":"S1","result":"pass","evidence":"…"}],
  "changed_files": ["…"],
  "done_md_path": "tasks/{NNN}-oppl-…/tasks/T01-…/DONE.md",
  "blockers": []
}
```
> 스키마 근거: TASK.md §확정 방향 §5 (→ D-7) / ANALYSIS §2.3. `scenario_results`는 verification.md §5.3 공통 결과 계약 `{대상,결과,사유,시점}`을 시나리오별로 담는다 (→ D-4 §5.3).

**(g) 3-SSOT 도구 호출 규칙** (M-3):
- 실행자는 `test-tool scenario-*`(init/red/lock/mark/status)만 호출한다.
- `backlog-tool`·`state-tool`은 호출하지 않는다 — backlog(L∞)·STATE는 PM 단독 갱신 오너십 (→ D-1 §병렬 실행·§L∞).

**(h) 행동 규칙** (opal-task-action-agent §행동 규칙 mirror + oppl 특화):
- 사용자와 직접 상호작용하지 않는다 — 결과만 PM에 반환.
- [MUST] STATE.md를 직접 갱신하지 않는다 — PM에게 위임(M-11).
- [MUST] `CONTRACT.md`를 직접 수정하지 않는다 — 계약 갱신 drift는 blocked(M-4).
- 하네스 §1 재시도 한도 준수(수치 복제 금지).
- 회귀 감지 시 즉시 중단·blocked 반환.
- 커밋하지 않는다 — PM 관리.
- [MUST] `~/.opal/` 직접 수정 금지 — 프로젝트 소스만.

**(i) 참조 문서 표 + (j) 변경이력** (v1.0, `2026-07-17 12:12` KST, 065).

#### 3.1.3 환경 변경
해당 없음 (도구·패키지 추가 없음).

#### 3.1.4 배치/마이그레이션
해당 없음 (배포는 F-004에서 install로 처리).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(입력·프로세스·계약·상한·blocked 섹션 존재) | 산출물 검사 | AGENT.md에 frontmatter·입력 명세(10필드)·실행 프로세스(T1~T5+G)·재시도 상한·blocked·결과 계약(6필드)·3-SSOT 규칙 섹션이 모두 존재 |
| TS-002 | H-1(순서 가드) | 산출물 검사 | AGENT.md에 "G 구현 전 / T4a 구현 후" 순서 강행 문구 + timestamp evidence 규칙 존재 |
| TS-003 | H-3(상한 복제 금지) | 산출물 검사 | AGENT.md에 재시도 정수 리터럴 부재 + harness §1 포인터 존재 (grep) |
| TS-004 | H-5(3-SSOT 경계) | 산출물 검사 | AGENT.md에 backlog-tool·state-tool run.sh 호출 부재, test-tool scenario-* 호출만 존재 |

### F-002: oppl SKILL.md 태스크당 실행자 1회 디스패치 개편

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | §태스크 내부 파이프라인(지점 1~7,11)·§디스패치(지점 8~10) 실행자 위임 개편 + §스킬 탐색 경로에 실행자 추가 + 변경이력 | (→ ANALYSIS §1.2, D-1) |

#### 3.2.2 설계 (11개 지점 반영 + 신규 디스패치 서술)

**§태스크 내부 파이프라인 (지점 1~7, 11)**:
- ASCII 다이어그램 마커를 `[실행자→생성자 내부 디스패치]`·`[실행자→Evaluator 내부 디스패치]`·`[실행자→test-agent 내부 디스패치]`로 교체(지점 2·4·5·6).
- 인트로에 [MUST] 1문장 추가: "PM은 L0 태스크 선택 후 **태스크당 `opal-loop-action-agent`를 1회 디스패치**하며, T1~T5+G 전체를 실행자가 내부 디스패치로 완주한다. PM의 L0/L∞/done-check/사람 게이트 소유는 불변이다." (→ TASK.md R-2 AC).
- T2 서술(지점 3): "실행자가 scenario-* 도구를 호출하고 test-agent(red)를 내부 디스패치" — 도구 호출 주체=실행자(M-3) 명시. red_confirmed 시드 무력화 문구는 유지.
- T4b(지점 7): "실행자가 규모 판정 후 인라인 또는 conv·sec-checker 내부 디스패치".

**§디스패치 (지점 8~10 — 제목·표·설명 개편)**:
- 절 제목/서술: "하이브리드 C(태스크당 ~3회)" → "**태스크당 실행자 1회 디스패치** (실행자 내부: 생성자·Evaluator·test-agent 별도)".
- 표 갱신: PM 디스패치는 `opal-loop-action-agent` 1행. 기존 ①②③은 "실행자 내부 디스패치"로 하위 표기.
- idiom(지점 10): "생성자 디스패치는 … T1~T3 범위로 한정된 지시" → "실행자가 area로 생성자 도메인 resolve 후 내부 디스패치하며, T1~T5+G 전체가 실행자 위임 범위다(G 게이트가 실행자 내부에서 T2와 T3를 끊는다)".
- 실행자 디스패치 프롬프트 idiom 추가: `[WORKER]` 마커 + 입력 명세 10필드 전달.

**§검증 2원화 (지점 11)**: 순서 불변 내용 유지, 주체를 "실행자 내부에서 G(구현 전)→test-agent(구현 후)"로 명시. verification.md §3 포인터 유지.

**§스킬 탐색 경로**: `opal-loop-action-agent` 항목 추가 (`{프로젝트}/.opal/agents/…` → `~/.opal/agents/…`).

**§자율 게이트 흐름**: "Loop 2 L0~L✓ — PM 자율 관리 (태스크별 실행자 디스패치)"로 문구 정합.

**§변경이력**: v1.2 행 추가 (`2026-07-17 12:12` KST, 065).

#### 3.2.3 환경 변경 / 3.2.4 배치·마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-2 AC(디스패치 표 실행자 1회) | 산출물 검사 | §디스패치가 "실행자 1회 디스패치" 기준으로 갱신, "T1~T3 한정" 문구가 실행자 위임으로 대체 |
| TS-006 | R-2 AC(PM 소유 불변) | 산출물 검사 | "PM의 L0/L∞/게이트 소유 불변" 문구 존재 |
| TS-007 | R-3 AC(2원화·에스컬레이션 명시) | 산출물 검사 | H-9 순서 불변 참조 + blocked 에스컬레이션 경로가 SKILL.md 또는 AGENT.md에 원문 존재 |
| TS-008 | R-2 AC(11지점 전수) | 산출물 검사 | ANALYSIS §1.2의 11개 지점이 모두 반영됨 (지점별 대조) |

### F-003: references 정합 갱신

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `…/references/loop-control.md` | 가이드 | §3 예산 "하이브리드 C … ~2~3 디스패치" → "실행자 1회 디스패치(내부 재디스패치는 실행자 예산)" + 변경이력 | (→ ANALYSIS §3.1, D-5 §3) |
| 2 | `…/references/contract.md` | 가이드 | §4(또는 §5)에 실행자 CONTRACT 직접수정 금지·계약갱신 drift blocked 경계 명시 + 변경이력 | (→ ANALYSIS §3.3, D-6 §4) |

**무변경(근거 기록)**

| 경로 | 무변경 근거 |
|------|-----------|
| `…/references/verification.md` | §3 순서 불변 규칙은 주체 중립(G before T3, T4a after T3 — PM/실행자 동일 적용). 변경 불필요 → 변경이력 행 추가하지 않음 (M-10, ANALYSIS §3.2) |

#### 3.3.2 설계

- **loop-control.md §3**: "PM은 각 태스크 파이프라인 완주를 하나의 비용 단위로 취급하고, **태스크당 실행자 1회 디스패치**를 기준으로 관찰한다. 실행자 내부 재디스패치(생성자/Evaluator/test-agent)는 실행자 자체 예산 관리 대상이며, 실행자가 반복 재디스패치로 상한을 초과하면 blocked 반환 → PM이 예산 소진 신호로 관찰한다." §2 상한 참조 원칙([MUST] 수치 비복제)은 불변.
- **contract.md §4 말미(또는 §5)**: 신규 문단 — "**실행자 경계**: `opal-loop-action-agent`는 태스크 파이프라인 중 CONTRACT.md를 직접 수정하지 않는다. 계약 미접촉 내부 구현(#1)은 정상 진행하고, 계약 갱신이 필요한 drift(#2 내부조정~#4 외부노출)를 감지하면 `blocked`로 PM에 반환한다. drift binary 판정·오너십 계층 분류·CONTRACT.md 반영은 PM(또는 거버넌스 지정 주체) 소관이다 — 생성자≠평가자·CONTRACT 반영=PM 헌법(§3) 유지." (M-4)

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-4 AC(하이브리드 C 전수) | 산출물 검사 | SKILL.md·references 3종에서 "하이브리드 C"·"~2~3 디스패치" 잔존 없음 또는 정합 처리 (grep) |
| TS-010 | R-4 AC(변경 문서 변경이력) | 산출물 검사 | loop-control.md·contract.md에 065 변경이력 행 존재, verification.md는 무변경(행 없음) |
| TS-011 | H-6(CONTRACT 경계) | 산출물 검사 | contract.md에 실행자 CONTRACT 직접수정 금지·blocked 반환 문구 존재 |

### F-004: 배포 반영 + 동작 실증

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/PROJECT.md` | 문서 | Project Loop 컴포넌트 표에 `opal-loop-action-agent` 행 + 변경이력 | (→ plan-guide §4.2 docs 규칙) |
| 2 | `docs/ARCHITECTURE.md` | 문서 | oppl 구조에 실행자 계층(PM→실행자→워커) 반영 | (→ 시스템 구조 변경) |

**무변경(확인만)**

| 경로 | 확인 내용 |
|------|----------|
| `scripts/install-mac.sh` | `opal/agents/*` 자동 포함(줄 462~464·641) — 신규 에이전트 스크립트 수정 불필요 (→ ANALYSIS §4·D-8) |

#### 3.4.2 설계

- **R-5 배포**: install-mac.sh 무변경 확인 후, 사용자 승인(사람 게이트, M-12) 하에 `./scripts/install-mac.sh` 실행 → `~/.opal/agents/opal-loop-action-agent/AGENT.md` 및 플랫폼 어댑터(`~/.claude/agents/…`) 존재 확인.
- **R-6 실증**: TEST 단계에서 PM이 실행자 1회 디스패치로 샘플 태스크(T1~T5+G)를 완주시키고 결과 계약을 관찰한다. **배포 전 실증 방법**: 프로젝트 로컬 에이전트 정의(`opal/agents/opal-loop-action-agent/AGENT.md`)를 디스패치 프롬프트에 직접 참조 경로로 주입한다 (SKILL.md §스킬 탐색 경로 "`{프로젝트}/.opal/agents/` → `~/.opal/agents/`" 우선순위 활용). 상세는 §7 C-4.

#### 3.4.3 환경 변경
install-mac.sh 실행(배포) — 사람 게이트 대상.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 AC(배포 존재) | 통합 테스트 | install 실행 후 `~/.opal/agents/opal-loop-action-agent/` 존재 (또는 어댑터 산출 확인) |
| TS-013 | R-6 AC(완주+계약) | 기능 테스트 | 실행자 1회 디스패치로 샘플 태스크 T1~T5+G 완주 + 6필드 결과 계약 반환 |
| TS-014 | H-1(순서 evidence) | 통합 테스트 | 완주 태스크 폴더에서 QA-SPEC.md 시점 < test-scenario.json result존 시점 |
| TS-015 | H-2(비가역 blocked) | 기능 테스트 | 비가역 트리거(배포/DB) 주입 샘플에서 실행자가 status: blocked 반환 |
| TS-016 | H-4(증거 자동생성) | 산출물 검사 | 완주 태스크 폴더에 PLAN.md·test-scenario.json·QA-SPEC.md·DONE.md 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | 신규 AGENT.md — 실행자 계약 확정 |
| 2 | F-002 | 2, 3 | opal-task-agent | 순차 | SKILL.md 개편 (F-001 계약 참조) |
| 3 | F-003 | 4, 5, 6 | opal-task-agent | 4·5 병렬 가능 / 6 확인 | references 정합 (SKILL.md 서술 참조) |
| 4 | F-004 | 7, 8 | opal-task-agent / PM 직접 | 순차 | 배포 확인 + docs 갱신 |
| TEST | F-004 | (TEST 단계) | opal-test-agent + PM | 순차 | R-6 실증 — §7 C-4 |

> 전문 에이전트 매핑: 이 태스크는 전부 프레임워크 md 문서 작업이므로 코드 영역(FE/BE/DB)이 없다. Framework 영역 전문 에이전트는 `opal-task-agent`(범용)이다 (→ D-PROJECT §프로젝트 구성 "Framework … opal-task-agent (범용)"). docs 갱신 Step만 PM 직접.

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 4개 | 실행 모드: 복잡

#### Step 1: `opal-loop-action-agent/AGENT.md` 신규 작성
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md` (신규)
- **작업 내용**: §3.1.2 (a)~(j) 전 섹션 작성 — frontmatter(name/description/model:advanced/icon:🔁), 입력 명세 10필드(M-1), 실행 프로세스 T1~T5+G ASCII+단계 상세(M-2), 순서 강행 가드(M-8), 재시도 상한 harness §1 포인터(M-6, 수치 복제 금지), blocked 반환 계약(M-7), 결과 계약 6필드(M-5), 3-SSOT 도구 호출 규칙(M-3, test-tool만), 행동 규칙(STATE·CONTRACT 직접수정 금지 M-11·M-4), 참조 문서 표, 변경이력 v1.0.
- **완료 기준**: TS-001~TS-004 Pass — 전 섹션 존재 + 상한 리터럴 부재 + test-tool만 호출.
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: oppl SKILL.md §태스크 내부 파이프라인 개편 (지점 1~7, 11)
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: §3.2.2 "태스크 내부 파이프라인" 지점 반영 — ASCII 마커 실행자 위임 교체(2·4·5·6), 인트로 [MUST] 실행자 1회 디스패치 문장(PM L0/L∞/게이트 불변), T2 도구 호출 주체=실행자(3), T4b 실행자 판정(7), §검증 2원화 주체 명시(11).
- **완료 기준**: TS-006, TS-007(부분), TS-008(지점 1~7,11) Pass.
- **테스트**: TS-006, TS-007, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: oppl SKILL.md §디스패치 개편 (지점 8~10) + 탐색경로·게이트흐름·변경이력
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: §3.2.2 "디스패치" 지점 8~10 — 절 제목/표를 실행자 1회 디스패치로 갱신, idiom "T1~T3 한정" → "T1~T5+G 실행자 위임" + 실행자 디스패치 프롬프트 idiom(10필드), §스킬 탐색 경로에 opal-loop-action-agent 추가, §자율 게이트 흐름 문구 정합, §변경이력 v1.2 행(065).
- **완료 기준**: TS-005, TS-008(지점 8~10) Pass.
- **테스트**: TS-005, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: loop-control.md §3 예산 정합 + 변경이력
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/loop-control.md`
- **작업 내용**: §3.3.2 — §3 예산 "하이브리드 C … ~2~3 디스패치" → "실행자 1회 디스패치(내부 재디스패치는 실행자 예산)". §2 상한 참조 원칙 불변. 변경이력 v1.1 행(065).
- **완료 기준**: TS-009(loop-control 부분), TS-010 Pass.
- **테스트**: TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: contract.md §4 실행자 drift 경계 명시 + 변경이력
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/contract.md`
- **작업 내용**: §3.3.2 — §4 말미(또는 §5)에 "실행자 경계" 문단 추가(M-4: CONTRACT 직접수정 금지·계약갱신 drift blocked·판정/반영 PM 소관). 변경이력 v1.1 행(065).
- **완료 기준**: TS-011 Pass.
- **테스트**: TS-011
- **실행 방법**: sub-agent
- **의존**: Step 3 (Step 4와 병렬 가능)

#### Step 6: verification.md 무변경 근거 확인
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/verification.md` (무변경)
- **작업 내용**: §3 순서 불변 규칙이 주체 중립(PM/실행자 동일 적용)임을 확인하고 무변경 판정(M-10). 파일 편집·변경이력 행 추가 없음. 확인 결과를 EXECUTE 로그/DONE.md에 1줄 기록.
- **완료 기준**: TS-009(verification 잔존 하이브리드 C 없음 확인), TS-010(변경이력 행 미추가) Pass.
- **테스트**: TS-009, TS-010
- **실행 방법**: direct
- **의존**: Step 3

#### Step 7: install 배포 반영 확인 (R-5)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 환경(배포)
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (무변경 확인)
- **작업 내용**: install-mac.sh가 `opal/agents/*`를 자동 포함(줄 462~464·641)함을 확인. 스크립트 수정 불필요. **install 실행 자체는 배포=사람 게이트(M-12)** — TEST/CLOSE에서 사용자 승인 후 수행하며, 이 Step은 "스크립트 수정 불필요" 판정과 실행 절차 준비까지만 한다.
- **완료 기준**: TS-012 준비 — install 경로 자동 포함 확인. 실제 실행·존재 검증은 사용자 승인 후 TEST에서.
- **테스트**: TS-012
- **실행 방법**: direct
- **의존**: Step 1

#### Step 8: docs/ 갱신 — PROJECT.md·ARCHITECTURE.md에 실행자 반영
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`, `docs/ARCHITECTURE.md`
- **작업 내용**: PROJECT.md §주요 컴포넌트(Project Loop) 표에 `opal-loop-action-agent` 행 추가 + 변경이력. ARCHITECTURE.md oppl 절에 PM→실행자→워커 계층 반영. (신규 에이전트/시스템 구조 변경 → docs 갱신 규칙)
- **완료 기준**: 두 문서에 실행자 반영 + PROJECT.md 변경이력 행(065).
- **테스트**: 산출물 검사 (문서 대조)
- **실행 방법**: direct
- **의존**: Step 1, Step 3

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | SKILL.md가 실행자 계약(입력·결과)을 참조하므로 AGENT.md 확정 후 |
| Step 2 → Step 3 | 동일 파일(SKILL.md) 순차 수정 — 편집 충돌 방지 |
| Step 3 → Step 4·5·6 | references가 개편된 SKILL.md 서술과 정합해야 함 |
| Step 4 ∥ Step 5 | 독립 파일(loop-control.md ↔ contract.md), 독립 내용 |
| Step 6 | 무변경 확인 — 편집 없음, Step 3 후 언제든 |
| Step 1 → Step 7 | 신규 에이전트 폴더 존재 후 배포 경로 확인 |
| Step 1·3 → Step 8 | 실행자 정의·SKILL 개편 확정 후 docs 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | AGENT.md 필수 섹션·계약 완비 | TS-001 | frontmatter·입력 10필드·프로세스 T1~T5+G·상한·blocked·결과 6필드·3-SSOT 규칙 존재 |
| F-001 | 검증 2원화 순서 가드 명시 | TS-002 | G 구현 전/T4a 구현 후 + timestamp evidence 문구 존재 |
| F-001 | 상한 SSOT 비복제 | TS-003 | 재시도 정수 리터럴 부재 + harness §1 포인터 존재 |
| F-001 | 3-SSOT 도구 경계 | TS-004 | test-tool scenario-*만, backlog/state-tool 미호출 |
| F-002 | 디스패치 실행자 1회 개편 | TS-005 | §디스패치 실행자 1회 + "T1~T3 한정" 대체 |
| F-002 | PM 소유 불변 | TS-006 | L0/L∞/게이트 소유 불변 문구 존재 |
| F-002 | 2원화·에스컬레이션 명시 | TS-007 | H-9 순서 참조 + blocked 에스컬레이션 경로 원문 |
| F-002 | 11개 지점 전수 반영 | TS-008 | ANALYSIS §1.2 지점 1~11 모두 반영 |
| F-003 | 하이브리드 C 정합 | TS-009 | 잔존 "하이브리드 C"·"~2~3 디스패치" 없음/정합 |
| F-003 | 변경 문서 변경이력 | TS-010 | loop-control·contract 065 행 존재, verification 무변경 |
| F-003 | CONTRACT 경계 명시 | TS-011 | contract.md 실행자 직접수정 금지·blocked 문구 |
| F-004 | 배포 존재 | TS-012 | install 후 `~/.opal/agents/opal-loop-action-agent/` 존재 |
| F-004 | 동작 실증 | TS-013, TS-014, TS-015, TS-016 | 샘플 완주 + 계약 반환 + 순서 evidence + blocked + 증거 자동생성 |

### 5.2 회귀 테스트

- [ ] oppl 기존 3-SSOT tool-gated 흐름(backlog/state/test-scenario) 비파괴 — 실행자 도입이 PM의 backlog-tool/state-tool 호출 경로를 바꾸지 않는가.
- [ ] Loop 1(D1~D7)·D7 사람 게이트·CLOSE 진입 게이트 불변 — 실행자는 Loop 2 태스크 내부에만 관여.
- [ ] oppd(opal-task-action-agent)·opsdd(opal-sdd-action-agent) 무변경 (→ TASK.md §제약).
- [ ] SKILL.md ↔ references 3종 상호 참조 무결성 (인라인 참조 절 명칭 유지).

### 5.3 코드/문서 품질

- [ ] 프로젝트 컨벤션 준수 — frontmatter 필드·변경이력 포맷(`YYYY-MM-DD HH:mm` KST·semver·태스크번호 065).
- [ ] [MUST] 변경한 스킬·에이전트·참조 문서마다 변경이력 행 추가 (verification.md는 무변경이므로 제외).
- [ ] 용어 일관성 — "실행자=opal-loop-action-agent", "생성자", "Evaluator/평가자"를 문서 전반 일관 사용 (citation-rules §7).
- [ ] [MUST] `~/.opal/` 직접 편집 없음 — 모든 changed_files가 프로젝트 소스.

### 5.4 보안

- [ ] AGENT.md·SKILL.md·references에 하드코딩된 토큰/시크릿/절대 경로(사용자 홈 외) 없음.
- [ ] 실행자가 비가역 행동(배포·DB·확정)을 자율 실행하지 않음 (blocked 반환) — H-2 검증.
- [ ] 실행자 readonly 경계 — CONTRACT.md·STATE.md·backlog.json 직접 mutate 없음 (H-5·H-6).

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 6개 (신규 1 + 수정 5: SKILL.md·loop-control·contract·PROJECT.md·ARCHITECTURE.md) | 복잡 |
| 모듈 범위 | 다중 (에이전트+오케스트레이터+가이드+문서+배포) | 복잡 |
| 작업 유형 | 신규 에이전트 도입 + 대규모 문서 개편 | 복잡 |
| 외부 의존성 | 없음 (기존 도구·에이전트 재사용) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1: Step 1 (F-001 AGENT.md) ── opal-task-agent
   ↓
Batch 2: Step 2 → Step 3 (F-002 SKILL.md, 동일 파일 순차) ── opal-task-agent
   ↓
Batch 3: Step 4 ∥ Step 5 (F-003 loop-control ∥ contract, 독립 파일) ── opal-task-agent
         + Step 6 (verification 무변경 확인) ── direct
   ↓
Batch 4: Step 7 (배포 확인) ── opal-task-agent ∥ Step 8 (docs 갱신) ── PM 직접
```

**그룹핑 원칙 적용**:
- **파일 충돌 방지**: SKILL.md를 건드리는 Step 2·3은 반드시 동일 에이전트·순차 (Batch 2).
- **모듈 응집도**: references(Step 4·5·6)는 F-003 응집 그룹.
- **병렬 극대화**: 독립 파일 Step 4∥5, Step 7∥8.

### C-2. 스킬 요구사항

- 기존 스킬 매칭: EXECUTE는 `op-dev-execute`(문서 편집)로 충분. 신규 스킬 갭 없음 — 모든 Step이 md 편집 단일 패턴이므로 인라인 지침으로 처리.
- 실행자 자체는 스킬이 아니라 에이전트(AGENT.md)이며, 내부에서 op-dev-plan·op-dev-execute를 생성자에게 위임한다.

### C-3. 도구 요구사항

- CLI: `scripts/install-mac.sh`(R-5 배포, 사람 게이트). `grep`(TS-003·004·009 산출물 검사).
- 신규 도구·MCP·패키지: 없음.

### C-4. 테스트 전략 (R-6 동작 실증)

TEST 단계에서 opal-test-agent + PM이 수행한다. **배포 전 실증**을 위해 프로젝트 로컬 에이전트 정의를 직접 참조시킨다:

1. **샘플 태스크 준비**: 최소 얇은 슬라이스 1개(예: 순수 함수 1개 추가/문서 1개) + acceptance 1~2건 + test-scenario spec.
2. **실행자 디스패치(1회)**: PM이 `opal-loop-action-agent`를 디스패치하되, 배포 전이므로 프롬프트에 **프로젝트 로컬 정의 경로**(`opal/agents/opal-loop-action-agent/AGENT.md`)를 명시 주입한다 (SKILL.md §스킬 탐색 경로 "`{프로젝트}/.opal/agents/` 우선" 규칙 활용). 입력 명세 10필드 전달.
3. **관찰 항목**:
   - T1~T5+G 완주 + 6필드 결과 계약 반환 (TS-013).
   - 순서 evidence: QA-SPEC.md(G) 시점 < test-scenario.json result존(T4a) 시점 (TS-014, H-1).
   - 증거 자동생성: PLAN.md·test-scenario.json·QA-SPEC.md·DONE.md 존재 (TS-016, H-4).
   - 내부 디스패치 분리: 생성자·Evaluator·test-agent가 각각 별도 에이전트로 호출됨 (생성자≠평가자, H-1).
   - 3-SSOT 경계: 실행자 로그에 backlog-tool·state-tool 미호출 (H-5).
4. **비가역 blocked 실증**(TS-015, H-2): 비가역 트리거(예: acceptance에 "DB 마이그레이션 적용" 포함) 샘플을 별도 디스패치 → `status: blocked` 반환 관찰.
5. **배포 검증**(TS-012, R-5): 사용자 승인(사람 게이트) 후 `./scripts/install-mac.sh` 실행 → `~/.opal/agents/opal-loop-action-agent/` + 플랫폼 어댑터 존재 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 에이전트/스킬/가이드 정의 | Markdown (AGENT.md / SKILL.md / *.md) | op-dev-execute (문서 편집) |
| 배포 | Bash (install-mac.sh 어댑터) | — (무변경 확인) |
| 도구 | Node.js (test-tool scenario-* — 실행자 내부 호출) | — (코드 변경 없음) |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 프레임워크 문서 태스크로 외부 라이브러리 API 조회 불필요 — context7/shadcn 미사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 개편 대상 본문 — §태스크 내부 파이프라인·§디스패치·§검증 2원화 |
| D-2 | 설계 | oppd 액션 에이전트 (선례) | `opal/agents/opal-task-action-agent/AGENT.md` | 실행자 구조·입력 명세·내부 재디스패치·결과 계약·행동 규칙 준거 |
| D-3 | 설계 | opsdd 액션 에이전트 (선례 2) | `opal/agents/opal-sdd-action-agent/AGENT.md` | 동형 선례 — 입력 명세·자체 산출물 작성·VERIFY 포인터 |
| D-4 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §3 순서 불변(H-9)·§5.3 결과 계약 스키마 |
| D-5 | 설계 | 루프 제어 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | §2 상한 참조 원칙·§3 예산·§7 하드블로커·§9 사람 게이트 |
| D-6 | 설계 | CONTRACT 거버넌스 | `opal/skills/opal-pilot-project-loop/references/contract.md` | §2.3 루브릭절·§3 반영=PM·§4 오너십 계층 |
| D-7 | 기획 | TASK.md | `tasks/065-…/TASK.md` | 확정 설계 방향 6항목·R-1~R-6·제약 |
| D-8 | 소스 | 설치 스크립트 | `scripts/install-mac.sh` (줄 462~464·641) | agents 자동 배포 경로 (ANALYSIS §4 스팟체크) |
| D-9 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 근거 제시·[MUST]·§7 decision_required |
| D-PROJECT | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 원칙·프로젝트 구성(Framework=opal-task-agent) |
| D-CONV | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 변경이력 의무·배포 경계 [MUST] |
| D-HARNESS | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` §1 | 자동 루핑 제약 수치 SSOT (참조·비복제) |

> 유형: `기획`/`설계`/`소스`/`외부`. 포맷: citation-rules.md §3.1.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 검증 2원화 순서 역전(H-1/H-9) | F-001 | P0 | AGENT.md 순서 강행 가드(M-8) + 실증 timestamp evidence(TS-014) |
| R-2 | 비가역 행동 무단 진행(H-2) | F-001 | P0 | blocked 반환 계약(M-7) + 비가역 트리거 실증(TS-015) |
| R-3 | 재시도 상한 SSOT 복제(H-3) | F-001 | P1 | harness §1 포인터만(M-6) + grep 검사(TS-003) |
| R-4 | PM 컨텍스트 손실(H-4) | F-001·F-002 | P1 | 증거 자동생성(QA-SPEC/test-scenario/verification_log) + STATE 추적(TS-016) |
| R-5 | 3-SSOT 경계 침범(H-5) | F-001 | P1 | 실행자 test-tool만 호출(M-3) + backlog/state 미호출 실증 |
| R-6 | CONTRACT drift 무단 반영(H-6) | F-001·F-003 | P1 | 실행자 CONTRACT 직접수정 금지(M-4) + contract.md 경계 명시(TS-011) |
| R-7 | RED self-confirming 우회(H-7) | F-001 | P0 | scenario-init 시드 무력화·lock red_not_confirmed 거부(기존 tool-gated) 준수 |
| R-8 | 용어 불일치 (실행자/액션 에이전트 혼용) | F-001·F-002 | P2 | 용어 일관성 검토(citation-rules §7) — "실행자=opal-loop-action-agent" 통일 |
| R-9 | SKILL↔references 참조 절 명칭 drift | F-002·F-003 | P2 | 인라인 참조 절 명칭 유지 + 회귀 테스트(§5.2) |

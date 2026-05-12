# TASK: 카르파시 행동 원칙 흡수 — Coding Principles SSOT 신설 + TASK AC 보강

> 작성일: 2026-05-12 | 작업 유형: 신규 + 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 — `https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md` 비교 검토 후 채택
> 출력: TASK.md

## 작업 목표

카르파시 `CLAUDE.md` 4원칙(§1 Think / §2 Simplicity / §3 Surgical / §4 Goal-Driven)을 OPAL 4단계(TASK / PLAN / TEST-SCENARIO / EXECUTE) + QA Gate에 매핑한 단일 SSOT(`harness/coding-principles.md`)를 신설하고, 기존 `op-task` AC 시스템을 카르파시 §4 기준으로 보강한다.

## 배경

카르파시 `CLAUDE.md`는 LLM 코딩 실수를 줄이는 4가지 행동 원칙을 매우 간결하게 정의한다. 우리 OPAL은 PM 오케스트레이션·하네스·게이트 시스템은 강력하지만, **워커 코딩 행동 원칙 SSOT가 부재**하다 — Simplicity/Surgical 원칙이 명시되지 않아 워커가 자기검증할 기준이 없고, TASK.md AC도 작성 가이드는 있으나 카르파시 §4 수준의 "검증 가능성" 기준이 약하다. 이로 인해 EXECUTE 산출물에 사변적 추가·인접 코드 "개선"·발생 불가능 시나리오 방어 코드가 끼어들 위험이 있다.

## 배경 분석 (대화에서 도출)

### 카르파시 CLAUDE.md 4원칙 ↔ OPAL 단계 매트릭스

| 카르파시 원칙 | TASK | PLAN | TEST-SCENARIO | EXECUTE | QA Gate |
|--------------|:----:|:----:|:------------:|:-------:|:-------:|
| §1 Think Before Coding | ✅ 주 | ✅ 주 | — | — | — |
| §2 Simplicity First | — | ✅ 설계 | ✅ 시나리오 (희박 케이스) | ✅ 구현 | ✅ 검증 |
| §3 Surgical Changes | — | — | — | ✅ 주 | ✅ 검증 |
| §4 Goal-Driven | ✅ success_criteria | — | ✅ verify check | ✅ verify loop | — |

### 기존 OPAL 구조 (확인 결과)

- `op-task/SKILL.md` 템플릿: 이미 요구사항 항목별 4필드(무엇을·어디에·왜·AC) 보유. AC 작성 가이드도 Bad/Good 예시 1쌍 포함 → 카르파시 §4의 70% 충족.
- 적용 부재: 워커 코딩 행동 SSOT (`harness/coding-principles.md` 미존재).
- 연동 부재: AC ↔ TEST-SCENARIO verify check 매핑 룰.
- "그냥 해" 표(opal/core/AGENT.md 또는 글로벌 SSOT): 현재 `@header` 등 유지 항목은 있으나 코딩 원칙 부재.

### 워커 로딩 패턴 선택 (하이브리드)

OPAL은 PM 주입형(`header-rules`)과 워커 자가 로드형(스킬 SKILL.md) 두 패턴이 공존. 코딩 원칙은 광역 룰이므로 **워커 자가 로드 + PM 의무 명시**의 하이브리드 채택.

| 레이어 | 동작 |
|--------|------|
| SSOT 파일 | `harness/coding-principles.md` 신설 |
| 워커 에이전트 정의 | 코드 변경 에이전트(opal-fe-agent / opal-be-agent / opal-task-agent)에 "EXECUTE 진입 시 §4 Read 의무" 1줄 추가 |
| PM 디스패치 프롬프트 | "coding-principles.md 준수" 1줄 (전체 텍스트 주입 X) |
| PM Gate | 산출물 사후 검증 (별도 태스크 P2에서 처리) |

### 희박 케이스 분류 매트릭스 (TEST-SCENARIO §3)

| 발생 가능성 | 영향도 | 처리 |
|----------|--------|------|
| 높음 | 높음 | 시나리오 필수 (Golden Path) |
| 높음 | 낮음 | 시나리오 작성 |
| 낮음 | 높음 | 시나리오 작성 + 정당화 명시 |
| 낮음 | 낮음 | 시나리오 제외 또는 Known Issue 명시 |
| 불가능 | — | 작성 금지 (위반 시 QA Fail) |

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 사항 | 근거 |
|---|----------|------|
| D-1 | P1(코딩 원칙 SSOT) + P3(B2+B3 — TASK AC 보강 + AC↔TEST-SCENARIO 매핑) 묶음 단일 태스크로 진행. P2(PM Gate Surgical 검증)는 별도 태스크 분리 | 검증 깔끔, P1·P3가 카르파시 §1·§4를 동일 레이어에서 다룸 |
| D-2 | 단일 SSOT 파일 + 단계별 §1~§6 섹션 구조 (옵션 A) | 카르파시 4원칙은 *연결된 한 체계*. 분리 시 원리 손실. OPAL 다른 SSOT(`opal-harness.md`)와 정합 |
| D-3 | 워커 자가 로드 + PM 의무 명시 하이브리드 채택 | OPAL 기본 패턴(스킬 자가 로드) 정합, SSOT 변경 시 PM 로직 무영향, 토큰 효율 |
| D-4 | TEST-SCENARIO §3에 희박 케이스 분류 매트릭스(발생 가능성 × 영향도) 포함 | 카르파시 §2 *"impossible scenarios"* 룰을 검증 시나리오로 확장 |
| D-5 | PM "그냥 해/직접 수행" 시에도 적용 — `@header`와 같은 위치(코드 파일 변경 시 보편 룰) | AGENT.md "그냥 해 적용 범위" 표 정합 |
| D-6 | P3는 *기존 AC 시스템 보강*. 새 필드 신설 아님 — Bad/Good 예시 추가 + AC↔TEST-SCENARIO 매핑 룰 명시 (B1 태스크 전체 차원 완료기준 신설은 제외) | 우리 AC 시스템이 이미 §4를 70% 구현. 변경 최소·효과 최대 |

## 요구사항

### F-1. coding-principles.md SSOT 신설 (P1)

| 필드 | 내용 |
|------|------|
| **무엇을** | 카르파시 §1~§4를 OPAL 단계 매트릭스로 매핑한 SSOT 파일을 신설한다 |
| **어디에** | `opal/core/references/harness/coding-principles.md` |
| **왜** | 워커/PM 코딩 행동 원칙 SSOT 부재. 카르파시 §2(Simplicity)·§3(Surgical)·§4(Goal-Driven) 정신 흡수 (D-1, D-2) |
| **AC** | (a) 파일이 위 경로에 존재한다. (b) `§1 TASK / §2 PLAN / §3 TEST-SCENARIO / §4 EXECUTE / §5 QA Gate / §6 적용 매트릭스` 6섹션 헤딩이 모두 존재한다. (c) §3에 발생 가능성 × 영향도 매트릭스 5행이 모두 등재된다. (d) 헤더 frontmatter에 "적용 주체: 코드 변경하는 모든 주체"와 "로드 시점: 워커 EXECUTE 진입 / PM 그냥 해 진입" 두 줄이 명시된다. (e) 변경이력 표 v1.0 행 1개 포함 |

### F-2. 워커 자가 로드 룰 등재 (P1 하이브리드)

| 필드 | 내용 |
|------|------|
| **무엇을** | 코드 변경 워커 3종 에이전트 정의에 "EXECUTE 진입 시 `harness/coding-principles.md` §4 Read 의무" 1줄을 추가한다 |
| **어디에** | `agents/opal-fe-agent.md` / `agents/opal-be-agent.md` / `agents/opal-task-agent.md` 세 파일 |
| **왜** | SSOT 신설만으로는 워커가 안 읽으면 무의미. 자가 로드 명시 필요 (D-3) |
| **AC** | (a) 3개 파일 각각에 `harness/coding-principles.md` 문자열을 포함한 의무 줄 1개 이상 존재. (b) 각 파일 변경이력 표에 1행 추가 |

### F-3. PM "그냥 해" 적용 범위 표 갱신 (P1)

| 필드 | 내용 |
|------|------|
| **무엇을** | "그냥 해/직접 수행" 시 하네스 적용 범위 표에 `Coding Principles` 행을 `✅ 유지`로 추가한다 |
| **어디에** | `opal/core/AGENT.md`(글로벌 AGENT.md SSOT의 프로젝트 소스). 정확한 표 위치는 ANALYSIS 단계에서 확인 |
| **왜** | PM이 "그냥 해" 시에도 coding-principles 준수해야 함을 명시 (D-5) |
| **AC** | (a) 적용 범위 표 "유지" 카테고리에 `Coding Principles` 행이 등재. (b) 해당 SSOT의 변경이력 표에 1행 추가 |

### F-4. op-task AC 작성 가이드 보강 (P3 B3)

| 필드 | 내용 |
|------|------|
| **무엇을** | `op-task/SKILL.md`의 "AC 작성 가이드"에 카르파시 §4 원문 인용 + Bad/Good 예시 1개 이상 추가 |
| **어디에** | `opal/skills/op-task/SKILL.md` AC 작성 가이드 섹션 |
| **왜** | 모호한 AC("make it work")가 EXECUTE/QA에서 끝없는 clarification 유발 (D-6) |
| **AC** | (a) 카르파시 §4 인용문 *"Strong criteria let you loop independently. Weak criteria require constant clarification."* 가 가이드에 포함. (b) 기존 Bad/Good 표가 최소 2행(기존 1행 + 신규 1행 이상). (c) op-task SKILL.md 변경이력 표 1행 추가 |

### F-5. AC ↔ TEST-SCENARIO 매핑 룰 명시 (P3 B2)

| 필드 | 내용 |
|------|------|
| **무엇을** | TEST-SCENARIO 작성 단계 스킬에 "각 TASK.md AC가 어느 verify check에 대응하는지" 매핑 표를 의무화한다 |
| **어디에** | `opal/skills/op-task-plan/SKILL.md` 또는 TEST-SCENARIO 작성 스킬 (정확한 위치는 ANALYSIS 단계에서 확인) |
| **왜** | AC와 TEST-SCENARIO가 따로 작성되어 추적성 약함. 검증 사슬 단단화 (D-6) |
| **AC** | (a) 단계 스킬에 "AC ↔ verify check 매핑 표 의무" 룰 추가. (b) 매핑 표 형식 예시(2열 이상: AC ID / verify check 위치) 제공. (c) 해당 SKILL.md 변경이력 표 1행 추가 |

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 배포 파일 직접 수정 금지. 프로젝트 소스(`opal/`, `agents/`, `skills/`)만 수정. install 재실행은 별도 안내.
- **하네스 SSOT 정합**: 코딩 원칙 SSOT는 `harness/` 모듈 테이블(`opal-harness.md` §2)에 행을 추가하여 Lazy 로드 트리거를 명시한다.
- **변경이력 표 의무**: 모든 수정 파일은 변경이력 표에 일시(KST) + 태스크 번호 포함 행 추가.
- **카르파시 원문 인용 시**: 영문 그대로 인용 + 한국어 설명 병기.
- **하위 호환**: 기존 AC 시스템·기존 op-task 흐름과 충돌하지 않아야 한다 (보강이지 치환 아님).
- **plan-only 절제**: F-3 "정확한 표 위치는 ANALYSIS 단계에서 확인" — TASK 단계에서 글로벌 SSOT 파일 위치를 확정하지 않고 분석으로 미룬다.

## 기술 스택

- Markdown (모든 산출물)
- Bash (state-tool / date-tool 호출)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 외부 | karpathy-skills CLAUDE.md | [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md) | 원천 — 4원칙 흡수 대상 |
| D-2 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md` | 하네스 모듈 테이블 §2 — coding-principles.md 행 추가 위치 |
| D-3 | 소스 | task-process.md | `opal/core/references/harness/task-process.md` | TASK 단계 공통 프로세스 — 변경 영향 없음 확인용 |
| D-4 | 소스 | op-task SKILL.md | `opal/skills/op-task/SKILL.md` | F-4 보강 대상 (AC 작성 가이드) |
| D-5 | 소스 | header-rules.md | `opal/core/references/harness/header-rules.md` | F-2 워커 자가 로드 패턴 vs PM 주입 패턴 참조 비교 |
| D-6 | 소스 | AGENT.md (글로벌) | `opal/core/AGENT.md` (프로젝트 소스) | F-3 "그냥 해" 적용 범위 표 갱신 대상 — 정확한 위치 ANALYSIS에서 확정 |
| D-7 | 소스 | reporting-template.md | `opal/core/references/harness/reporting-template.md` | 3블록 보고 형식 — TASK·PLAN 산출물 보고 정합용 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

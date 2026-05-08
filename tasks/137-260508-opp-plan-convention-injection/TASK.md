# TASK: PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화

> 작성일: 2026-05-08 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

PLAN 워커가 PLAN.md를 작성할 때 `docs/CONVENTIONS.md`의 강제 규칙([MUST]/금지/네이밍)을 [MUST] 원문 인용 포맷으로 반드시 PLAN.md에 박도록 하네스/에이전트/스킬에 의무 규약을 신설한다. PLAN.md에 박힌 코드 예시가 컨벤션을 위반하면 EXECUTE 워커가 그 예시를 따라 잘못된 코드를 생산하므로, 사전 차단을 통해 오염 전파를 막는다.

## 배경

이전 세션에서 사후 검증 자동화(태스크 136 — PM Gate 컨벤션 자동 진단)를 설계하던 중 PLAN.md의 코드 예시가 EXECUTE 워커 컨텍스트로 흘러들어 컨벤션 위반을 그대로 코드로 만들어내는 갭이 발견되었다.

```
PLAN 워커 → 컨벤션 위반 코드 예시를 PLAN.md에 박음
  → EXECUTE 워커가 PLAN.md를 컨텍스트로 Read
  → EXECUTE 워커가 잘못된 예시를 따라 코드 생산
  → 컨벤션 위반이 changed_files로 전파
  → 사후 검출(태스크 136 §13)에서 1회 재지시 → 같은 PLAN.md 보고 같은 패턴 반복 위험
```

사후 검출(B = 태스크 136)은 changed_files만 검사하므로 PLAN.md 자체의 잘못된 예시는 못 잡고, 잡힐 때는 이미 코드가 만들어진 후 재작업 코스트가 발생한다. **사전 주입(제안 A)이 근본 해결**이며, 본 태스크는 사전 주입에 한정한다.

## 배경 분석 (대화에서 도출)

| 단계 | 현재 상태 | 갭 |
|------|----------|-----|
| PM 디스패치 측 (D-1 §Step 3) | 인용 의무 룰 존재 — `[MUST] <문서명> §N: <원문>` 포맷 강제 | "원문 인용 필수" 카탈로그에 **컨벤션 [MUST] 항목**이 명시 부재 — PM 재량 누락 가능 |
| PLAN 에이전트 측 (D-2) | 자체 로드 문서로 `docs/CONVENTIONS.md` Read 명시 | Read만 강제, **PLAN.md에 [MUST] 포맷으로 박는 의무**는 미정의 |
| PLAN 스킬 측 (D-3 / D-4) | citation-rules.md 트리거 1줄 주입 (v1.4 / v1.3) + §2.4 [MUST] 포맷 적용 명시 | 품질 체크리스트에 "**컨벤션 [MUST] 인용 적용 여부**" 항목 부재 — QA Gate에서 자동 검출 안 됨 |
| 인용 규약 측 (D-5 §2.5) | [MUST] 토큰 대상 6종(필드명/함수 시그니처/타입명/ERD 컬럼/IA 화면 ID/정책 조항) | 7번째 토큰 후보 **"코드 컨벤션 강제 규칙"** 추가 검토 필요 |

**상위 수준 결론**: 4개 지점이 **하나의 SSOT + 적용 일례**의 관계인지 또는 **독립 강제 지점**인지가 불명확. PLAN 단계에서 정밀 분석으로 결정.

## 확정된 설계 방향 (대화에서 합의)

1. **본 태스크는 사전 주입(제안 A)에 한정**. 사후 검증(B = 태스크 136)과 책임 분리.
2. **잠재 적용 지점 4개**는 PLAN 단계에서 영향 범위 정밀 분석 후 채택 여부 결정. TASK.md에서는 후보만 정리.
3. **최소 변경 원칙**: 동일 효과를 내는 중복 강제 지점이 있으면 SSOT 한 곳만 손대고 나머지는 참조로 연결.
4. **하위 호환**: `docs/CONVENTIONS.md` 부재 프로젝트는 현 동작(Step 3 인용 의무 룰의 자연스러운 스킵) 유지.

## 잠재 적용 지점

| # | 파일 | 변경 검토 내용 | 강제 주체 | 영향 범위 |
|---|------|--------------|---------|---------|
| 1 | `opal/core/references/pm/dispatch-process.md` §Step 3 인용 의무 카탈로그 | "원문 인용 필수" 행에 **CONVENTIONS.md [MUST]/금지/네이밍 규칙**을 명시적 대상으로 추가 | PM (디스패치 측) | 모든 PLAN 워커 디스패치 시 PM이 컨벤션 [MUST] 인용을 워커 프롬프트 핵심 제약 필드에 반드시 박도록 강제 |
| 2 | `opal/agents/opal-plan-agent/AGENT.md` 행동 규칙 | 자체 로드한 CONVENTIONS.md [MUST] 항목을 **PLAN.md §1 또는 §2에 [MUST] 포맷으로 박는 의무**를 행동 규칙에 신설 | PLAN 에이전트 (워커 측) | opal-plan-agent 디스패치 시 PLAN.md 산출물에 컨벤션 [MUST] 인용이 반드시 적용됨 |
| 3 | `opal/skills/op-task-plan/SKILL.md` + `opal/skills/op-dev-plan/SKILL.md` 품질 체크리스트 | "**컨벤션 [MUST] 인용이 §1 참조 문서 테이블 또는 §2 핵심 설계에 적용되어 있는가**" 항목을 품질 체크리스트에 추가 | PLAN.md 산출물 측 | QA Gate에서 자동 검출 가능 (op-task-qa 또는 op-dev-qa가 체크리스트 갱신) |
| 4 | `opal/core/references/harness/citation-rules.md` §2.5 [MUST] 토큰 대상 | 현재 6종 토큰에 7번째 **"코드 컨벤션 강제 규칙"** 추가 (선택 — 일반화 vs 개별 강제 트레이드오프) | 인용 규약 측 (선택) | 모든 산출물(TASK/ANALYSIS/PLAN/EXECUTE) 작성 시 컨벤션 [MUST] 토큰 일반화 |

## 요구사항 (잠정 — PLAN 단계에서 정밀화)

- [x] **R-1: PM 디스패치 측 강제** — PLAN 워커 디스패치 시 PM이 `docs/CONVENTIONS.md`의 [MUST] 강제 규칙을 워커 프롬프트의 핵심 제약 필드에 원문 인용 포맷으로 박는 절차가 하네스에 명시된다.
  - 어디에: 잠재 적용 지점 #1 (D-1 §Step 3 인용 의무 카탈로그) 또는 동등 위치
  - 왜: 확정 방향 §1 — PM 재량 누락 차단
  - AC: D-1 §Step 3의 "원문 인용 필수" 카탈로그에 "코드 컨벤션의 [MUST]/금지/네이밍 규칙"이 추가되어 있고, PLAN 워커 디스패치 프롬프트 템플릿(opp/opd/opds/opdw)에 컨벤션 [MUST] 인용이 핵심 제약 필드의 필수 항목으로 명시되어 있다.

- [x] **R-2: PLAN 에이전트 측 강제** — opal-plan-agent가 자체 로드한 `docs/CONVENTIONS.md`의 강제 규칙을 PLAN.md에 [MUST] 원문 인용 포맷으로 박는 의무가 행동 규칙에 명시된다.
  - 어디에: 잠재 적용 지점 #2 (D-2 행동 규칙)
  - 왜: 확정 방향 §1 — PLAN 에이전트가 Read만 하고 PLAN.md에 옮기지 않는 갭 차단
  - AC: D-2 §행동 규칙에 "[MUST] CONVENTIONS.md [MUST] 항목을 PLAN.md §1 참조 문서 테이블 또는 §2 핵심 설계에 [MUST] 포맷으로 인용해야 한다"가 추가되어 있다.

- [x] **R-3: PLAN.md 산출물 측 검증** — PLAN.md 품질 체크리스트에 "컨벤션 [MUST] 인용 적용 여부"가 검증 항목으로 추가되어 QA Gate에서 자동 검출된다.
  - 어디에: 잠재 적용 지점 #3 (D-3 + D-4 §품질 체크리스트)
  - 왜: 확정 방향 §1 — 워커가 의무를 누락한 경우 QA Gate에서 검출
  - AC: D-3 §품질 체크리스트와 D-4 §품질 체크리스트(또는 동등 섹션)에 "컨벤션 [MUST] 인용이 PLAN.md에 적용되어 있는가" 항목이 추가되어 있다.

- [x] **R-4: 인용 규약 측 토큰 확장 결정** — citation-rules.md §2.5 [MUST] 토큰 대상 확장 여부를 PLAN 단계에서 결정한다.
  - 어디에: 잠재 적용 지점 #4 (D-5 §2.5)
  - 왜: 확정 방향 §3 — 최소 변경 원칙 충돌 회피 (R-1~R-3가 이미 충분하면 §2.5 확장 불필요)
  - AC: D-5 §2.5에 "코드 컨벤션 강제 규칙" 토큰이 7번째로 추가되어 있거나, PLAN.md §리스크에 "추가하지 않은 사유"가 명시되어 있다.

- [x] **R-5: 하위 호환 명문화** — `docs/CONVENTIONS.md` 부재 프로젝트는 본 변경의 영향을 받지 않고 기존 동작(인용 의무 룰 자연 스킵)을 유지한다.
  - 어디에: 변경된 모든 지점 (R-1~R-4 적용 위치)
  - 왜: 확정 방향 §4 — 기존 프로젝트 깨짐 방지
  - AC: 각 변경 지점에 "CONVENTIONS.md 부재 시 본 의무는 자동 스킵"이 명문화되어 있거나, 부재 시 자연 스킵되는 동작이 PLAN.md §리스크에 검증되어 있다.

- [x] **R-6: 적용 지점 결정 근거 PLAN.md 기재** — 4개 잠재 적용 지점 중 채택 / 비채택 / 부분 채택 결정의 근거가 PLAN.md §1 현황 조사 또는 §2 구현 계획에 기재된다.
  - 어디에: PLAN.md §1 / §2
  - 왜: 확정 방향 §2·§3 — 정밀 분석 위임의 의사결정 추적
  - AC: PLAN.md에 "잠재 적용 지점 #1·#2·#3·#4 각각의 채택 여부와 근거"가 표 또는 목록으로 정리되어 있다.

## 제약 조건

- **`~/.opal/` 배포 파일 직접 편집 금지** — 모든 변경은 프로젝트 진본(`opal/...`)만 대상. 배포본은 빌드/sync로 동기화. 메모리 `feedback_deploy_boundary.md` 룰.
- **하위 호환** — `docs/CONVENTIONS.md` 부재 프로젝트의 기존 PLAN 워커 디스패치 흐름이 깨지면 안 된다.
- **136과 분리** — 본 태스크는 사전 주입(제안 A)만 다룸. 사후 검증(B)은 136에서 별도 처리 (다른 세션에서 진행 중).
- **citation-rules.md §2.4 [MUST] 포맷 준수** — 모든 신설 의무 규약은 `[MUST] '경로' §N: <원문>` 포맷으로 기재.
- **PLAN 정밀 분석 위임** — 4개 잠재 적용 지점의 실제 채택 여부, 변경 분량, 표현 방식은 PLAN 워커가 영향 범위 분석 후 결정. TASK.md는 후보만 제시.
- **최소 변경 원칙** — SSOT가 한 곳에 있고 다른 지점은 참조로 연결되는 구조면 SSOT 한 곳만 변경. 4개 지점 전부 변경이 아니어도 됨.

## 기술 스택

- Markdown, YAML (OPAL 프레임워크 문서/에이전트 정의)
- 코드 변경 없음 (문서·에이전트·스킬 정의 변경 한정)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 SSOT — 잠재 적용 지점 #1 (§Step 3 인용 의무 카탈로그) |
| D-2 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | PLAN 에이전트 행동 규칙 + 자체 로드 문서 명세 — 잠재 적용 지점 #2 |
| D-3 | 설계 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | 범용 PLAN 단계 스킬 + 품질 체크리스트 — 잠재 적용 지점 #3a |
| D-4 | 설계 | op-dev-plan SKILL.md | `opal/skills/op-dev-plan/SKILL.md` | dev PLAN 단계 스킬 + 품질 체크리스트 — 잠재 적용 지점 #3b |
| D-5 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규약 SSOT — 잠재 적용 지점 #4 (§2.5 [MUST] 토큰 대상) |
| D-6 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 컨벤션 SSOT — 인용 대상 |
| D-7 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | 프로젝트 정의 + 문서 테이블 |
| D-8 | 설계 | task 136 TASK.md | `tasks/136-260508-opp-pm-gate-convention-auto-check/TASK.md` | 사후 검증(B) 분리 명시 — 본 태스크와의 책임 분담 근거 (다른 세션 진행 중) |
| D-9 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | PM 행동 프로세스 — §3 디스패치 전 프로세스 진입점 |
| D-10 | 설계 | opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md | `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/SKILL.md` | PLAN 단계 디스패치 프롬프트 템플릿 보유 — R-1 적용 영향 범위 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

# 스킬 생성 요청서 (초안) — opal-pilot-project-loop

> 상태: 초안 (검토용) | 작성 맥락: oppd 대체 후보, 루프 방식 오케스트레이터
> 실제 생성은 확정 후 `skill-creator`로 진행

---

## 1. 메타

| 항목 | 값 |
|------|-----|
| name | `opal-pilot-project-loop` |
| alias(트리거) | **[미결정]** `oppl` 후보 (기존 opp/oppd/opsdd와 충돌 없음, 확인 필요) |
| 계열 | 프로젝트급 오케스트레이터 (opp/oppd/opsdd와 동렬) |
| version | 1.0.0 (신규) |
| 대체 대상 | oppd (검증 후 deprecate 경로) |

---

## 2. 정의

사용자 요청을 충분히 분석해 프로젝트 계획을 수립하고, **목표가 실제로 충족될 때까지 반복(loop)** 하여 완수하는 오케스트레이터.
oppd와 목적은 동일(규모 있는 프로젝트의 완전한 완수)하나, **선형 Phase가 아니라 종료조건이 있는 수렴 루프**로 구동한다.

### oppd 대비 존재 이유 (차별점)

| 축 | oppd (현행) | loop (신규) |
|----|------------|-------------|
| 제어구조 | 선형 3-Phase + 전환 게이트 | **수렴 루프** (계획→실행→검증→재계획) |
| 실행 단위 | 전체 WBS 일괄 | **태스크(얇은 수직 슬라이스) 1개씩 반복** |
| 재계획 | scope 3분기 등 무거운 규칙 | **루프의 일부로 자연 흡수** (백로그 갱신) |
| 완료 판정 | 액션 소진 | **종료조건 충족까지 반복** |
| 검증 | 단계 뒤 별도 게이트 | **루프에 verify 내장** (evaluator-optimizer) |
| 인터뷰 | opwt에 암묵 위임(얕음) | **1급 단계로 승격** |

---

## 3. 설계 근거 (loop engineering — 출처 기반)

- **루프 엔지니어링**: "루프를 설계하는 실무 — 목표 명시·트리거·무한실행 방지 가드레일" (Data Science Dojo). "한 번 응답이 아니라 행동→관찰→다음 결정→목표 충족까지 반복" (MindStudio).
- **루프 사이클**: gather context → take action → **verify(환경 진실로 검증)** → repeat (Anthropic). = Perceive→Reason→Plan→Act→Observe (Data Science Dojo).
- **필요 역할**: Orchestrator / Planner / Executor / Reviewer(=Evaluator) (Anthropic orchestrator-workers + evaluator-optimizer, MindStudio).
- **종료·안전 필수**: 반복 상한 · 토큰/비용 예산 · 무진전 감지 · 검증가능 기준의 목표 체크 · 비가역 행동 전 사람 승인 (Data Science Dojo, MindStudio).
- **원칙**: 단순·조합가능 패턴 우선, 복잡도는 결과가 좋아질 때만 (Anthropic).

> 출처: Anthropic *Building Effective AI Agents* / Anthropic *Multi-agent research system* / Data Science Dojo *Agentic Loops: ReAct→Loop Engineering (2026)* / MindStudio *What Is Loop Engineering*.

---

## 4. 핵심 개념 · 계층 · 용어

```
프로젝트  ── 설계 루프 ─→  PRD.md · TRD.md · PROJECT_PLAN.md(살아있는 백로그)
   └─ 실행 루프  ── 문서 없음, 백로그에서 태스크만 꺼내 반복 관리
        └─ 태스크(=슬라이스)  ── 단계별 문서 산출 + 단계별 에이전트
             └─ 단계: 분석·설계 → 테스트시나리오(RED) → 구현 → 검증 → 마무리
```

| 용어 | 정의 |
|------|------|
| 태스크(=슬라이스) | 단일 책임 + 하나의 수용기준으로 독립 검증 가능한 최소 증분 |
| PROJECT_PLAN.md | 실행 루프의 **살아있는 백로그** — WHAT/순서/종료조건만. HOW(상세설계) 미포함 |
| 2단 설계 | **거시**(TRD+PLAN, 설계 루프) + **미시**(태스크별, 실행 시점) |

> ⚠️ 명칭 충돌 정리 필요: `PROJECT_PLAN.md`(프로젝트 백로그) ↔ 태스크별 `PLAN.md`(미시 설계). 서로 다른 이름으로 확정.

---

## 5. 워크플로우

### Loop 1 — 설계 수렴 루프 (인터뷰 중심)

```
반복: 인터뷰 질문 → 사용자 답 → PRD/TRD/PLAN 갱신 → "명확한가?" 자가판정
종료조건: 목표·범위·제약·완료기준(4요소) 잠김 + 미해결 질문 0
산출물: PRD.md / TRD.md / PROJECT_PLAN.md
게이트: 사용자 확정 (설계 루프 → 실행 루프 전환 지점)
```

### Loop 2 — 실행 수렴 루프 (태스크 반복)

```
while (종료조건 미충족):
    다음 우선 태스크 선택 (백로그 의존성·우선순위)
      → 태스크 파이프라인 완주 (아래 5단계)
      → 관찰 → PROJECT_PLAN 갱신 (완료 표시 / 신규 태스크 추가)
      → 종료조건 판정
종료조건: PLAN의 모든 수용기준 GREEN + 회귀 0
루프 제어: §8 참조 (반복 상한·예산·무진전 감지·목표 체크)
```

### 태스크 내부 5단계 파이프라인 (문서 산출)

| 단계 | 정의 | 산출 문서 | 완료기준 |
|------|------|-----------|----------|
| 1 분석·설계 | 태스크 한정 미시 설계 | `PLAN.md`(태스크) | 변경 파일·인터페이스 확정 |
| 2 테스트 시나리오 | 수용기준→실행가능 테스트 (RED-first) | `TEST-SCENARIO.md` | RED(실패) 확인 |
| 3 구현 | 설계대로 코드 | 코드 변경 | 테스트 GREEN 목표 |
| 4 검증 | L1 lint→L2 build→L3 test 루프 | 검증 로그 | 전 계층 PASS + 회귀 0 |
| 5 마무리·관찰 | 랩업 + 백로그 갱신 | `DONE.md`(태스크) | PROJECT_PLAN 갱신 |

---

## 6. 에이전트 구성표 (기존 OPAL 자산 재사용)

| 루프/단계 | 역할(loop engineering) | OPAL 에이전트 |
|-----------|----------------------|---------------|
| 전체 | Orchestrator | PM(알투) — 루프 지휘·백로그 관리·게이트 |
| 설계 루프 | 인터뷰·기획 | `opal-planning-agent` (+ opwt 재사용 옵션) |
| 태스크 1 분석·설계 | Planner | `opal-plan-agent` |
| 태스크 2 테스트시나리오 | Planner/QA | `opal-plan-agent` / `opal-task-qa-agent` |
| 태스크 3 구현 | Executor | `opal-be-agent` / `opal-fe-agent` / `opal-db-agent` (영역별) |
| 태스크 4 검증 | Reviewer/Evaluator | `opal-test-agent` (+ `opal-convention-checker`·`opal-security-checker`) |
| 태스크 5 마무리 | Orchestrator | PM 직접 |

---

## 7. 산출물 · 폴더 구조

```
tasks/{NNN}-oppl-{프로젝트명}/
├── TASK.md              ← 전체 그림
├── STATE.md             ← 루프 상태·재개 지점 (세션 독립)
├── PRD.md / TRD.md      ← 설계 루프 산출 (확정 후 docs/ 승격)
├── PROJECT_PLAN.md      ← 살아있는 백로그
├── DONE.md              ← 전체 완료 랩업
└── tasks/
    ├── T01-{태스크명}/ { PLAN.md, TEST-SCENARIO.md, DONE.md, (검증로그) }
    ├── T02-{태스크명}/
    └── ...
```

---

## 8. 단계 기술 표준 (모든 단계 공통 8필드)

각 단계를 요청서/스킬에 기술할 때 아래 8필드로 통일한다:

| 필드 | 질문 |
|------|------|
| 정의(what) | 이 단계가 뭔가 |
| 목적(why) | 왜 필요한가 |
| 선행조건/필수입력 | 진입 전 충족될 것 (앞 단계 산출물) |
| 절차(how) | 수행 스텝 |
| 담당/도구(who) | 어느 에이전트·도구 |
| 산출물(output) | 무엇을 만드나 |
| 완료기준/검증 | 언제 통과인가 (기계적으로) |
| 게이트 | 사용자 확인? PM 자율? |

---

## 9. 루프 제어 (종료·안전 — 근거 기반 필수)

| 요소 | 내용 |
|------|------|
| 반복 상한 | 루프별 hard iteration cap |
| 토큰/비용 예산 | run 단위 budget |
| 무진전 감지 | 목표에 가까워지지 않으면 중단 |
| 목표 달성 체크 | 검증가능 기준(수용 테스트)으로 판정 |
| 경로 분리 | 성공 / 실패 / 에스컬레이션 |
| 에러 처리 | 복구가능 vs 하드블로커 구분, 유형별 전략 |
| 컨텍스트 관리 | 이전 반복을 압축 작업기억으로 요약 + 실행 로그 |
| 사람 게이트 | 비가역 행동(배포·DB·TRD/PRD 변경) 전 사용자 승인 |
| evaluator-optimizer | 검증 단계 = 생성↔평가 피드백 반복 (루프 내장) |

---

## 10. 재사용 vs 신규 제작

| 재사용 (그대로) | 신규 제작 (loop 고유) |
|----------------|----------------------|
| opwt / opal-plan·be·fe·db·test·qa 에이전트 | 수렴 루프 제어구조 (종료조건·무진전·예산) |
| state-tool (STATE 관리) | 인터뷰 1급 설계 루프 |
| 검증 계층(L1~L3) · RED-first | 살아있는 백로그(PROJECT_PLAN) 운용 |
| brain-ingest 훅 | evaluator-optimizer 검증 내장 |

---

## 11. 미결정 / 오픈 이슈 (확정 필요)

1. **[미결정] 디스패치 단위** — 태스크 단위 위임(A, 권고: `opal-task-action-agent` 1회로 5단계 완주) vs 단계 단위 디스패치(B, 무거움) vs 하이브리드(C).
2. **[미결정] alias** — `oppl` 등 확정 + skills-registry 충돌 확인.
3. **[미결정] 명칭** — `PROJECT_PLAN.md` ↔ 태스크 `PLAN.md` 구분 명칭.
4. **[미결정] oppd 처리** — 병행 유지 후 deprecate 시점.
5. **[미결정] 모드** — 3-way(semi-agentic/interactive/agentic) 승계 여부.

---

## 12. 다음 단계

1. §11 오픈 이슈 확정
2. 확정본을 `skill-creator`로 넘겨 SKILL.md 생성
3. 기존 하네스(Guards/State/Observability/citation-rules) 승계 확인

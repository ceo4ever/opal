# PLAN: 루프 액션 에이전트 내부 디스패치 채널 opal-agent 전환 — 동기/비동기 이원화

> 작성일: 2026-07-17 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 7개)
> 실행 모드: 복잡 (프레임워크 문서 4종 개정 + 신규 규약 3종 + 실증 설계)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-loop-action-agent`의 내부 4축 디스패치(생성자·Evaluator·test-agent·checker)를 플랫폼 Agent 도구에서 opal-agent(claude headless CLI) 채널로 전환한다. 호출 모드를 단계별로 동기/비동기 이원화하고(장시간 T1·T2·T3=비동기+결과 파일, 단시간 G·T4a·T4b=동기), 생성자 세션을 T1→T3 resume으로 잇는다. 065에서 관측된 릴레이 마찰(부모 턴 조기 종료·손자 보고 우회·서브에이전트 재개 불가)을 결과 파일 결정론과 fresh 프로세스 컨텍스트 주입으로 구조적으로 제거한다. 1차 릴리스는 claude 한정이며, 065 확정 계약(검증 2원화 `065-H-9`·blocked 7종·3-SSOT 경계·결과 계약 6필드)은 불변 유지한다.

### 1.2 참조 문서 (설계 결정 근거)

> §8.3에 전체 테이블. 인라인 인용은 아래 D-ID로 단축 참조한다 (citation-rules.md §3.2).

핵심 근거: D-1 AGENT.md(개정 본체), D-2 opal-agent README, D-3 opal_agent.py(코드 SSOT), D-4 oppl SKILL, D-5 opal-harness §5/§6, D-6 observability.md, D-9 brain concept(065 확정), D-11 opal-model-mapping.

**[MUST] 인용 (재해석 금지 제약)**:

- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." (→ D-12)
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (→ D-12)
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임)." (→ D-12) — R-6 플랫폼 가용성 표 설계 시 조건 분기가 아닌 "1차 릴리스 범위 명시"로 서술하여 준수.
- [MUST] `TASK.md` §제약 조건: "`--dangerously-skip-permissions` 금지."
- [MUST] `TASK.md` §제약 조건: "Bash 타임아웃(기본 2분·최대 10분)이 동기 호출의 상한 — 장시간 축은 반드시 비동기."
- [MUST] `memory/console-brain-subscription-auth.md`: "구독(로컬 claude -p) 사용 — API키·SDK 금지."
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: 재시도 수치 비복제 — harness §1 포인터 유지.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | AGENT.md 내부 디스패치 절 재작성 (4축×호출모드 매트릭스) | R-1 | P0 | 없음 |
| F-002 | 결과 파일 규약 (3-분리 캡처·스키마·완료 마커·수거 실패 처리) | R-2 | P0 | F-001 |
| F-003 | 생성자 resume 연속성 (cold-prime session_id, T1→T3) | R-3 | P0 | F-001 |
| F-004 | 권한 표준 (축별 `--allowedTools` allowlist, skip-permissions 금지) | R-4 | P0 | F-001 |
| F-005 | 하네스·oppl 정합 보강 + 변경이력 행 | R-5 | P0 | F-001~F-004 |
| F-006 | 1차 릴리스 범위 + 플랫폼 가용성 표 | R-6 | P1 | F-001 |
| F-007 | 동작 실증 설계 (065 S-7/S-8급 시나리오) | R-7 | P0 | F-001~F-006 |

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┐
       ├─ F-003 ─┤
       ├─ F-004 ─┼─ F-005 ── F-007
       └─ F-006 ─┘
```

F-001(AGENT.md 재작성)이 골격이고 F-002/003/004/006은 그 위의 규약·표 신설. F-005(정합)는 앞 5개 완료 후 하네스·oppl 문서에 반영. F-007(실증)은 전체 문서 정합 후 TEST 단계에서 실행.

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 된다. L1=문서/정적 검사, L2=실증(샘플 태스크 완주), L3=회귀.
>
> **[네임스페이스 각주]** 본 표의 `H-N`(H-1~H-11)은 **066 태스크 로컬 가설 네임스페이스**이며, 065 확정 계약 명칭 `065-H-9`(검증 2원화 순서)와 **무관하다**. 065 계약을 참조할 때는 본 문서 전반에서 `065-H-9` 접두 표기를 사용해 구분한다. TEST-SCENARIO.md는 이 로컬 H-N을 S-N/TS-N으로 매핑하여 소비한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 AGENT.md §실행 프로세스 | "Agent 도구" 내부 디스패치 서술 잔존 → 채널 전환 미완 | P0 | L1(grep) | S-1: 개정 후 `AGENT.md`에 내부 디스패치용 "Agent 도구" 문구 0건 |
| H-2 | F-002 결과 파일 3-분리 캡처 | 하드에러(exit 2) 시 result.json 공백 → 완료 오판 (R-I) | P0 | L2 | S-4·S-6: exitcode 파일 존재=완료마커, exit 2에서 err.log 채워짐 |
| H-3 | F-003 cold-prime session_id | T1 `--session-id` ≠ T3 `--resume` → 생성자 재개 유실 | P0 | L2 | S-2: T1·T3 동일 uuid 관측(session.json) |
| H-4 | F-004 축별 allowedTools | headless에서 필요 도구 미허용 → 워커 무진전 중단 | P1 | L2 | S-1: 각 축 완주(권한 프롬프트 없이) |
| H-5 | F-004 권한 명문화 | `--dangerously-skip-permissions` 사용/금지 누락 → 보안 계약 위반 | P0 | L1(grep) | S-5: 문서에 금지 명문 + 명령 예시에 skip 플래그 0건 |
| H-6 | F-005 하네스·oppl 정합 | Agent 도구 전제 서술과 opal-agent 채널 서술 공존 모순 | P1 | L1(대조) | S-7: observability.md §행위주체 적용 범위 명확, oppl↔AGENT 모순 0 |
| H-7 | F-005 변경이력 | 변경 문서 변경이력 행 누락 → CONVENTIONS 위반 | P1 | L1 | S-8: 변경 문서 4종 전부 066 행 존재 |
| H-8 | F-001 모델 매핑 (R-G) | `--model`에 레벨명(light/standard/advanced) 그대로 전달 → 실모델 미지정 | P1 | L2 | S-1: T1 `--model opus`(advanced) 등 실모델명 관측 |
| H-9 | F-002 비동기 타임아웃 (R-D) | 단시간 축이 Bash 상한(≤10분) 초과 → no-progress/blocked | P1 | L2 | S-3: G/T4a/T4b 타임아웃 내 완주 또는 blocked 정상 반환 |
| H-10 | F-005 T2 축 귀속 불일치 | oppl SKILL §디스패치 "생성자 디스패치 연속" ↔ AGENT.md/brain "test-agent(mode:red)" 모순 (문서/문서 불일치) | P2 | L1 | S-7: T2 = test-agent축으로 양 문서 정합 |
| H-11 | F-007 blocked 유지 | 비가역 fixture가 blocked 아닌 강행 → 065 계약 회귀 | P0 | L2/L3 | S-3: 비가역 fixture blocked 반환 유지 |

---

## 2. 기능별 분석

> ANALYSIS.md 있음 → F별 분석 간략 작성, 설계에 집중 (SKILL.md §입력 분기).

### F-001: AGENT.md 내부 디스패치 절 재작성

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 내부 4축 디스패치 서술 본체 | 수정 |
| 소스 | `opal/tools/opal-agent/opal_agent.py` | 채널 능력 SSOT (참조만) | 참조 |
| 소스 | `opal/tools/opal-agent/README.md` | 명령 형태·플래그 SSOT (참조만) | 참조 |

#### 2.1.2 현재 구현

내부 4축은 예외 없이 Agent 도구를 전제로 서술된다 — "Agent 도구" 명시는 T1(`AGENT.md:42`)·행동규칙 6번(`:139`) 2곳, 나머지 T2~T4b(`:46-71`)는 암묵 전제 (→ D-13 §4-1). 축 정의 SSOT는 brain concept: 생성자(T1/T3)·Evaluator(G)·test-agent(T2 RED/T4a GREEN)·checker(T4b) (→ D-9 §결정 내용). opal-agent는 동기·resume·session-id·allowedTools·JSON을 기존 기능으로 전부 지원하나 백그라운드는 미내장 (→ D-13 §1.6).

#### 2.1.3 영향 범위

간접 영향: 생성자(fe/be/db/task-agent)·Evaluator·test-agent·checker AGENT.md는 변경 대상이 아니나, 이번 개정으로 headless(`claude -p`, `[WORKER]` fresh 프로세스)로 호출되는 경로가 신설된다 — 각 에이전트가 세션 컨텍스트 미공유 환경에서 동작하려면 입력 재주입 필요 (→ D-13 §3.2, R-C).

### F-002: 결과 파일 규약

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 §결과 파일 규약 절 | 수정(신규 절) |

#### 2.2.2 현재 구현

`main()`은 라이브러리를 항상 `output_format="json"`으로 실행하며 `--json` 시 stdout에 `result.raw`(claude 원문 JSON)를 출력한다 (→ D-3:714,723 / D-13 §1.5.2). 하드에러(exit 2)는 stdout 공백·stderr에만 메시지 (→ D-3:718-720 / D-13 §1.5.4). 종료코드: 0 성공 / 1 is_error / 2 하드에러 (→ D-13 §1.5.3). claude 결정론 보장 필드는 `result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms` 5개뿐 (→ D-13 §1.5.2).

#### 2.2.3 영향 범위

결과 파일은 태스크 폴더 내 전송 산출물이며, 루프 액션 에이전트의 결과 계약 6필드(불변)와 별개 (→ D-9 §결정 내용).

### F-003: 생성자 resume 연속성

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 §생성자 resume 절차 절 | 수정(신규 절) |

#### 2.3.2 현재 구현

ClaudeAdapter는 `new_session_id`(cold `--session-id`) ↔ `session_id`(warm `--resume`)를 상호배타로 처리 (→ D-3:193-196,567-570). cold `--session-id`는 claude 전용 (→ D-13 §1.6). 059에서 caller-supplied cold 세션 지정이 도입됨 (→ D-2 README:201-215).

#### 2.3.3 영향 범위

resume는 생성자축(T1→T3)에만 적용. T2(test-agent)·G(Evaluator)는 각자 독립 세션 (→ D-9 §결정: "test-agent(T2 RED/T4a GREEN)"·"생성자(①과 동일 에이전트) 재개").

### F-004: 권한 표준 (allowedTools)

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 §allowedTools 표준 절 | 수정(신규 절) |

#### 2.4.2 현재 구현

`--allowed-tools A,B`(CLI) → claude `--allowedTools`로 매핑, 콤마 구분 (→ D-2 README:143,164 / D-3:191-192,643-646). 헤드리스에서 --allowedTools 화이트리스트 + skip-permissions 미사용이면 미허용 도구는 프롬프트 불가로 사실상 차단 → allowlist는 축별로 완전해야 함.

#### 2.4.3 영향 범위

프로젝트 스코프 한정 — MCP·외부 네트워크 도구 미포함.

### F-005: 하네스·oppl 정합 + 변경이력

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 참조 | `opal/core/references/harness/observability.md` | 행위주체 표시 적용 범위 (Agent 도구 전제) | 수정 |
| 참조 | `opal/core/references/opal-harness.md` | §5 Observability·§6 Model Mapping stub | 수정(포인터 보강) |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 태스크 내부 파이프라인·디스패치 절 | 수정 |

#### 2.5.2 현재 구현

observability.md §행위주체 표시는 "Agent 도구로 에이전트를 디스패치할 때"를 아이콘 룩업·선언 트리거로 명시 (→ D-6:46,52). 적용 주체는 PM (→ D-6:42). oppl SKILL §디스패치는 "루프 액션 에이전트 → 생성자/Evaluator/test-agent: opsdd EXECUTE-LOOP 서술형 디스패치 준용" (→ D-4:374), §파이프라인 ASCII는 "[루프 액션 에이전트→…내부 디스패치]" 주석 (→ D-4:291-306). §디스패치 표 ①은 T1+T2를 "생성자"에 귀속 (→ D-4:357) — brain/AGENT.md의 test-agent(T2 RED) 귀속과 불일치(H-10).

#### 2.5.3 영향 범위

opal-harness.md §5/§6은 SSOT stub이므로 발췌·복제 없이 포인터만 보강 (→ D-5:167-189, loop-control §2 비복제 원칙).

### F-006: 1차 릴리스 범위 + 플랫폼 가용성 표

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 §플랫폼 가용성 절 | 수정(신규 절) |

#### 2.6.2 현재 구현

opal-agent 검증 상태: claude/codex ✅ E2E, gemini/grok/cursor ⚠️ 명령 조립/미검증 (→ D-2 README:40-49). cold `--session-id`는 claude 전용 (→ D-13 §1.6).

#### 2.6.3 영향 범위

플랫폼 조건문 금지([MUST] CONVENTIONS §플랫폼 분기 격리) → "가용성 표 + 1차 범위 명시" 형태로만 서술.

### F-007: 동작 실증 설계

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `tasks/066-…/TEST-SCENARIO.md` | 실증 시나리오 (PM이 STEP 3.5에서 작성) | 신규(PM) |

#### 2.7.2 현재 구현

opal-agent 채널 전환 자체 검증 테스트는 부재 — R-7에서 신규 정의 (→ D-13 §1.4). 065 S-7/S-8이 완주·재개·blocked 실증 준거 (→ D-7).

#### 2.7.3 영향 범위

실증은 개정된 AGENT.md 배포(install) 후 PM이 샘플 태스크에 루프 액션 에이전트를 디스패치하여 수행 — TEST 단계 산출.

---

## 3. 기능별 설계

### F-001: AGENT.md 내부 디스패치 절 재작성

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | §실행 프로세스(T1~T5+G) 전면 재작성 — Agent 도구 → opal-agent 채널(동기/비동기), 축×호출모드 매트릭스, `[WORKER]` 마커, 명령 형태, 결과 수거 방식 | (→ D-1:38-72, D-9) |
| 2 | 〃 | 에이전트 | §행동 규칙 6번 "Agent 도구를 통해 내부 디스패치" → opal-agent 채널 서술로 교체 | (→ D-1:139) |

#### 3.1.2 핵심 설계

**결정 R-A(축 명명 vs 동기/비동기 이원화 불일치 해소)** — 두 개념을 직교 분리한다 (→ D-9 §결정, D-13 §4-3):

- **축(axis)** = *누구를* 부르는가 (디스패치 대상 에이전트 정체성). 검증 2원화(생성자≠평가자, `065-H-9`)의 근거. 065 불변: 생성자·Evaluator·test-agent·checker 4축.
- **호출 모드(call mode)** = *어떻게* 부르는가 (단계별 소요시간에 따른 동기/비동기). 축이 아니라 **단계(phase)** 단위로 결정한다.

동일 test-agent축이 T2(비동기 그룹)·T4a(동기 그룹)에서 다른 호출 모드를 갖는 모순은, "축=정체성 / 호출모드=단계"로 분리하면 해소된다. AGENT.md에 아래 **단계×축×호출모드 매트릭스**를 명시한다 (→ D-1, D-9, TASK §확정 방향 2):

| 단계 | 축 | 대상 에이전트 | 호출 모드 | model 레벨 | 재개 |
|------|-----|-------------|----------|-----------|------|
| T1 명세·설계 | 생성자 | area resolve(fe/be/db/task) | **비동기** | advanced (T1 기존 지정, → D-1:42) | cold prime |
| T2 RED 시나리오 | test-agent | opal-test-agent(mode:red) | **비동기** | standard (test-agent frontmatter, `opal/agents/opal-test-agent/AGENT.md:7`) | — |
| G 명세 리뷰 | Evaluator | opal-evaluator-agent(spec-review) | **동기** | advanced (evaluator frontmatter, `opal/agents/opal-evaluator-agent/AGENT.md:7`) | — |
| T3 구현 | 생성자 | T1과 동일(warm resume) | **비동기** | standard (T3 기존 지정, → D-1:58) | `--resume` |
| T4a GREEN 검증 | test-agent | opal-test-agent | **동기** | standard (test-agent frontmatter, `opal/agents/opal-test-agent/AGENT.md:7`) | — |
| T4b 규칙검사 | checker | conv/sec-checker (고위험만) | **동기** | 체커 frontmatter 준용 — conv=standard(`opal/agents/opal-convention-checker/AGENT.md:7`) / sec=advanced(`opal/agents/opal-security-checker/AGENT.md:7`) | — |

> model 레벨 규칙: T1(advanced)·T3(standard)는 AGENT.md 기존 지정(→ D-1:42,58)을 유지하고, 그 외 축은 **대상 에이전트 frontmatter `model` 레벨을 그대로 준용**한다(셀 값이 곧 준용 결과 — 각주와 셀은 동일 규칙의 두 표현이며 모순이 아니다). 저위험 T4b는 인라인 경량화 시 호출 자체 생략 (→ D-4:339). 각 셀의 레벨을 R-G 절차로 실모델명 치환한다.

**결정 R-B(비동기 축 구현 경계 명문화)** — opal-agent는 백그라운드 미내장(`subprocess.run` 블로킹 전용, → D-3:592-618, D-13 §1.6)이므로, 비동기화는 **호출측 Bash `run_in_background` + 결과 파일 리다이렉트**로 구현한다. 이는 "opal-agent 도구 개조"가 아니라 "opal-agent를 감싸는 호출 패턴"이므로 TASK §범위 제외(도구 개조)에 해당하지 않는다 (→ D-13 §4-2). AGENT.md에 이 경계를 명문화한다.

**결정 R-G(모델 매핑 책임 소재)** — opal-agent `--model`은 레벨→실모델 자동 치환이 없다(pass-through, → D-3:637, D-13 §1.3). 따라서 **루프 액션 에이전트가 레벨→실모델 치환을 직접 수행**한다: 위 매트릭스의 레벨을 `~/.opal/references/opal-model-mapping.md` §2 claude 컬럼(effective setting 반영, `light=haiku/standard=sonnet/advanced=opus`)으로 치환하여 `--model <실모델명>`을 조립한다 (→ D-11 §2·§4, ANALYSIS §1.3이 "호출측이 직접 수행" 결론). AGENT.md는 치환 절차를 서술하고 매핑 수치는 SSOT 포인터로만 참조(비복제).

**동기 축 명령 형태** (G/T4a/T4b — Bash foreground):

```bash
~/.opal/tools/opal-agent/run.sh \
  --provider claude --opal-bootstrap off \
  --model <실모델명> \
  --allowed-tools <축별 allowlist> \
  --timeout <축별 초> --cwd <project_root> --json \
  "<[WORKER] 마커 + 재주입 컨텍스트 + 지시>" \
  > <task_folder>/.oppl-run/<phase>.result.json \
  2> <task_folder>/.oppl-run/<phase>.err.log; echo $? > <task_folder>/.oppl-run/<phase>.exitcode
```

동기 축은 Bash 반환 stdout·exit로 즉시 수거하되, 결과 파일도 함께 남겨 증거 균일성을 확보한다.

**비동기 축 명령 형태** (T1/T2/T3 — Bash `run_in_background: true`, 동일 리다이렉트 3종). 수거는 §F-002 완료 마커로 판정.

**결정 R-C(fresh 프로세스 컨텍스트 재주입 최소 입력 목록)** — headless는 세션 미공유(→ D-2 README:169-170)이므로 각 축 프롬프트에 아래를 명시 주입한다:

| 주입 항목 | 전 축 공통 | 축별 추가 |
|----------|-----------|----------|
| `[WORKER]` 첫 줄 마커 | O (`--opal-bootstrap off`) | — |
| 단계 스킬 경로 | O | T1: op-dev-plan / T3: op-dev-execute / G: evaluator / T4a·T2: test-agent / T4b: conv·sec-checker |
| task_folder·project_root·project_context(docs 목록) | O | — |
| acceptance(수용기준) | O | T1·T2·G 필수 |
| 이전 산출물 경로 | — | G: PLAN.md·USER_FLOW.md·test-scenario.json / T3: PLAN.md·QA-SPEC.md / T4a: test-scenario.json |
| contract_path(CONTRACT.md) | — | G·T3·T4b |
| verify_commands | — | T3·T4a |
| 전문 에이전트 매핑(생성자 area) | — | T1 |

### F-002: 결과 파일 규약

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | 신규 §결과 파일 규약 절 — 경로·3-분리 스키마·완료 마커·수거 실패 처리 | (→ D-13 §1.5, §4-6, R-F/H/I) |

#### 3.2.2 핵심 설계

**결정 R-I(3-분리 캡처)** — 하드에러(exit 2) 시 stdout이 완전히 비므로(→ D-3:718-720), stdout·stderr·exit code 3종을 함께 파일로 캡처해야 완료 판정이 결정론적이다 (→ D-13 §4-6). 경로 규약:

```
<task_folder>/.oppl-run/<phase>.result.json    ← stdout (claude raw JSON; exit 2 시 공백 가능)
<task_folder>/.oppl-run/<phase>.err.log         ← stderr ([opal-agent 오류] 메시지 등)
<task_folder>/.oppl-run/<phase>.exitcode        ← 종료 코드 (★완료 마커)
```

`<phase>` ∈ `{t1, t2, g, t3, t4a, t4b}`.

**완료 마커** = `.exitcode` 파일의 **존재**. `echo $? > …exitcode`는 opal-agent 명령 종료 후에만 실행되므로, 파일 존재 = 프로세스 완료의 결정론적 신호다. `.result.json` 존재/비존재로 완료를 판정하지 않는다(R-I).

**결정 R-H(스키마를 opal-agent 보장 필드 중심 설계 — 예)** — 결과 파일 스키마는 claude 원문 JSON 중 opal-agent가 명시적으로 소비/보장하는 5필드만 참조한다: `result`(텍스트)·`session_id`·`is_error`·`total_cost_usd`·`duration_ms` (→ D-13 §1.5.2). 문서화되지 않은 claude CLI 자체 필드(`type`/`num_turns`/`usage` 등)에는 의존하지 않는다 → R-H 리스크(별도 CLI 문서 조사) 회피.

**완료 판정 로직** (exitcode 파일 읽은 뒤):

| exitcode | 의미 | 처리 |
|----------|------|------|
| `0` | 성공 | `.result.json`의 `result`/`session_id` 파싱 → 다음 단계 |
| `1` | is_error(에이전트 자체 실패, 프로세스 정상) | 해당 단계 fail로 취급 → 재작업(재시도 상한 내) |
| `2` | 하드에러(CLI 실행 실패) | `.err.log` 확인 → 재시도 상한 내 재시도, 초과 시 blocked |
| (파일 없음, 타임아웃 경과) | 미완료/무진전 | no-progress → blocked (트리거 #4) |

**결정 R-F(경로 충돌·동시성)** — 한 루프 액션 에이전트 인스턴스 내 단계는 의존 체인(T1→T2→G→T3→T4a→T4b)으로 **순차**라 단계 간 동시성 없음. 서로 다른 태스크는 `task_folder`가 달라 격리. 재시도는 이전 증거를 보존하기 위해 시도 접미사를 붙인다: `<phase>.a<N>.result.json`(N=2부터). 최신 시도 = 최대 N. 따라서 경로 충돌은 발생하지 않는다.

**수거 실패 처리** — 완료 마커 부재로 타임아웃 감지 시 무진전(blocked #4), exit 2 상한 초과 시 blocked(#5). blocked 반환은 065 계약(7종 트리거) 그대로 (→ D-9).

### F-003: 생성자 resume 연속성

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | 신규 §생성자 resume 절차 절 — cold prime → warm resume | (→ D-2 README:201-215, D-3:193-196) |

#### 3.3.2 핵심 설계

**결정 #8(cold prime vs 자연 발급 재사용) → cold prime 채택** (→ ANALYSIS §4.4). 근거: 비동기 T1 결과 파싱 성공 여부와 무관하게 세션 id가 사전 확정되어 T3 재개 명령을 선(先)조립할 수 있고, 059 caller-supplied cold 설계 취지(생성자 재개 복원)와 정합한다 (→ D-2 README:201-203).

절차:
1. 루프 액션 에이전트가 T1 디스패치 전 UUID 생성(`uuidgen` 또는 python `uuid.uuid4()`).
2. `<task_folder>/.oppl-run/session.json`에 보존: `{"constructor_session_id": "<uuid>", "created": "<ISO8601>", "provider": "claude"}`.
3. T1: `run.sh --provider claude --session-id <uuid> …` (cold, → D-3:193-194).
4. T3: `run.sh --provider claude --resume <uuid> …` (warm, `--session-id`와 상호배타, → D-3:195-196,567-570).

**session_id 보존 위치** = `.oppl-run/session.json`. **재개 명령 형태** = 위 4번. claude 전용(cold `--session-id`는 claude만, → D-13 §1.6) — 1차 범위와 일치. T2·G·T4a는 각자 독립 세션(resume 미적용).

### F-004: 권한 표준 (allowedTools)

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | 신규 §allowedTools 표준 절 — 축별 allowlist + skip-permissions 금지 | (→ D-2 README:143,164, TASK §제약) |

#### 3.4.2 핵심 설계

**결정 R-4(축별 표준 allowlist, 프로젝트 스코프 한정)** — `--allowed-tools`는 콤마 구분 (→ D-2 README:143). skip-permissions 미사용 시 미허용 도구는 headless에서 차단되므로 축별로 완전해야 한다:

| 단계 | allowlist | 근거 |
|------|-----------|------|
| T1 (plan) | `Read,Grep,Glob,Write,Edit,Bash` | 코드 분석 + PLAN.md 작성 + code-scan/date bash |
| T2 (test red) | `Read,Grep,Glob,Write,Edit,Bash` | 실패 테스트 작성·실행 |
| G (evaluator) | `Read,Grep,Glob` | 읽기 전용 명세 리뷰 (verdict만 반환) |
| T3 (execute) | `Read,Grep,Glob,Write,Edit,Bash` | 구현 + lint/build/test |
| T4a (test green) | `Read,Grep,Glob,Bash` | 시나리오 실행 (테스트 파일 기존 존재) |
| T4b (conv/sec) | `Read,Grep,Glob` | 읽기 전용 규칙 검사 |

**[MUST] `--dangerously-skip-permissions` 사용 금지** — 모든 축 명령에서 이 플래그를 쓰지 않으며, allowlist로만 자동 실행을 제한한다 (→ TASK §제약). 프로젝트 스코프 한정(`--cwd <project_root>`) — MCP·네트워크·시스템 도구 미포함. AGENT.md에 금지를 명문화한다.

### F-005: 하네스·oppl 정합 + 변경이력

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/observability.md` | 참조 | §행위주체 표시 적용 범위 명확화 — opal-agent 내부 채널은 아이콘 룩업 대상 아님 | (→ D-6:46,52, R-#9) |
| 2 | `opal/core/references/opal-harness.md` | 참조 | §5·§6 stub에 opal-agent 채널 포인터 1줄 보강(비복제) | (→ D-5:167-189) |
| 3 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | §파이프라인·§디스패치 idiom을 opal-agent 채널로 정합 + T2 축 귀속 정정 | (→ D-4:291-306,357,374) |
| 4 | 위 3종 + AGENT.md | 참조/에이전트/오케스트레이터 | 각 §변경이력 표에 066 행 추가 | [MUST] CONVENTIONS §변경이력 |

#### 3.5.2 핵심 설계

**결정 #9(Observability 적용 범위)** (→ ANALYSIS §4.5) — observability.md §행위주체 표시(아이콘 룩업·선언 형식)의 트리거는 "PM이 Agent 도구로 디스패치할 때"로 유지한다(적용 주체 PM, → D-6:42,46). 루프 액션 에이전트의 내부 opal-agent 채널 디스패치는 (a) PM 발화가 아니고 (b) Agent 도구가 아니므로 아이콘 룩업 대상이 **아니다**. 대신 루프 액션 에이전트가 **결과 파일(.oppl-run/*)·결과 요약**으로 자체 관측성을 확보한다는 한 문단을 observability.md에 추가한다(범위를 좁혀 정의). 이로써 R-#9의 "동일 관측 규칙 그대로 적용되는가" 모호성을 제거.

**opal-harness.md §5/§6 보강(비복제)** — §5는 observability.md, §6은 opal-model-mapping.md를 가리키는 SSOT stub이므로 (→ D-5:167-189), "opal-agent 채널 내부 디스패치 관측·모델 매핑은 각 SSOT 참조" 포인터 1줄만 추가한다. 수치·규칙 복제 금지(loop-control §2, harness §1 포인터 원칙).

**oppl SKILL 정합** — §파이프라인 ASCII 주석(→ D-4:291-306)의 "[…내부 디스패치]"를 "[opal-agent 채널 — 동기/비동기]"로, §디스패치 idiom(→ D-4:374)의 "opsdd EXECUTE-LOOP 서술형 디스패치 준용"을 "opal-agent 채널 호출(동기/비동기 이원화·`[WORKER]` 마커)"로 정합. PM→루프 액션 에이전트 디스패치는 Agent 도구 유지(불변, → D-4:372, TASK §확정 방향 7).

**결정 H-10 정정(T2 축 귀속 불일치, 문서/문서)** — oppl SKILL §디스패치 표 ①이 T1+T2를 "생성자"에 귀속(→ D-4:357)하나, SSOT(brain concept "test-agent(T2 RED/T4a GREEN)", → D-9 / AGENT.md:46-49)는 T2를 test-agent축으로 정의한다. **SSOT 기준으로 test-agent축으로 정정**하고 SKILL 표 주석을 "① T1 생성자 / T2 test-agent(mode:red)"로 분리한다. 이 불일치를 PLAN.md에 명기(§9 R-2).

**변경이력 행(066)** — 4개 문서 각 §변경이력에 `YYYY-MM-DD HH:mm KST | 내용(066)` 행 추가. install이 배포본에서 strip (→ D-12 §변경이력 작성 의무).

### F-006: 1차 릴리스 범위 + 플랫폼 가용성 표

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | 신규 §플랫폼 가용성 절 — claude 한정 1차 + 점진 검증 | (→ D-2 README:40-49) |

#### 3.6.2 핵심 설계

**결정 R-6(플랫폼 가용성 표)** — [MUST] 플랫폼 조건문 금지(CONVENTIONS §플랫폼 분기 격리, → D-12)를 준수하여, 본문 로직에 `if claude` 분기를 넣지 않고 **가용성 표 + 범위 문구**로만 서술:

| provider | 내부 채널 가용성 | 근거 |
|----------|----------------|------|
| claude | **1차 릴리스(E2E 실측, cold session-id 지원)** | (→ D-2 README:44,201) |
| codex | 후속 검증 후보(E2E 실측 있으나 cold session-id 미지원) | (→ D-2 README:45) |
| gemini/grok/cursor | 점진 검증(명령 조립·미검증) | (→ D-2 README:46-48) |

문구: "본 채널은 claude를 1차 릴리스 범위로 하며, 타 provider는 opal-agent 검증 상태 상향 시 점진 확대한다." 행위 자체는 provider 중립(opal-agent `--provider`가 어댑터 계층에서 흡수).

### F-007: 동작 실증 설계

#### 3.7.1 파일 변경 계획

TEST-SCENARIO.md는 PM이 STEP 3.5에서 별도 작성(SKILL.md §입출력). PLAN은 실증 시나리오 후보를 §3.7.2에 설계 입력으로 제공.

#### 3.7.2 실증 시나리오 설계 (065 S-7/S-8급, TEST-SCENARIO 입력)

전제: 개정 AGENT.md를 `./scripts/install-mac.sh`로 배포([MUST] 배포 경계) 후, PM이 소형 샘플 태스크(예: 단일 유틸 함수 slice)에 루프 액션 에이전트를 1회 디스패치.

| 후보 | 내용 | 기대 |
|------|------|------|
| S-1 | 내부 워커 전원 opal-agent 채널로 완주 | PM 재개 지시 **0회** + 결과 계약 6필드 반환 + `--model` 실모델명·축별 allowlist 관측 |
| S-2 | T1→T3 resume 연속성 | `.oppl-run/session.json`의 uuid가 T1 `--session-id`·T3 `--resume`에서 동일 관측 |
| S-3 | 비가역 fixture(배포/DB 요구) 주입 | `status: blocked` 반환 유지(065 계약 불변) + 타임아웃 축 정상 |
| S-4 | 결과 파일 규약 준수(비동기 축) | `.oppl-run/<phase>.{result.json,err.log,exitcode}` 3종 존재, exitcode=완료 마커 |
| S-5 | 하드에러 fixture(강제 실패) | exit 2 + err.log 채워짐 + result.json 공백을 결정론적으로 미완료 판별 |
| S-6(L1) | 문서 정적 검사 | AGENT.md 내부 디스패치 "Agent 도구" 0건, skip-permissions 0건, 변경 문서 4종 066 행 |

#### 3.7.3 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | AGENT.md §실행 프로세스에 4축×호출모드 매트릭스 존재, 내부 디스패치용 "Agent 도구" 문구 0건 |
| TS-002 | R-2 AC | 산출물 검사 | §결과 파일 규약에 경로·5필드 스키마·완료 마커·수거 실패 처리 명문 |
| TS-003 | R-2 AC | 기능 테스트 | 비동기 축 exit 2 시 err.log 채워짐·result.json 공백을 미완료로 판별 |
| TS-004 | R-3 AC | 기능 테스트 | T1 `--session-id` = T3 `--resume` = session.json uuid (동일) |
| TS-005 | R-4 AC | 보안 테스트 | 축별 allowlist 문서화 + `--dangerously-skip-permissions` 금지 명문 + 명령 예시에 skip 0건 |
| TS-006 | R-5 AC | 산출물 검사 | observability.md에 opal-agent 채널 적용 범위, oppl↔AGENT 모순 0, 변경 문서 4종 066 행 |
| TS-007 | R-6 AC | 산출물 검사 | 플랫폼 가용성 표 존재 + 플랫폼 조건문 미도입 |
| TS-008 | R-7 AC | 통합 테스트 | 샘플 태스크 완주 PM 재개 0회 + resume 연속성 + blocked 유지 + 결과 파일 수거 실측 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차(골격) | AGENT.md §실행 프로세스 재작성 |
| 2 | F-002·F-003·F-004·F-006 | 2,3,4,5 | opal-task-agent | 순차(동일 파일 AGENT.md) | 신규 절 4종 — 파일 충돌로 순차 |
| 3 | F-005 | 6,7,8 | opal-task-agent | 6∥7∥8(독립 파일) | observability·harness·oppl 정합 |
| 4 | F-005 | 9 | opal-task-agent | 순차 | 변경이력 4종 일괄 |
| 5 | F-007 | 10 | PM 직접 | 순차(TEST 단계) | 실증 시나리오 → TEST-SCENARIO |
| 6 | 문서 | 11 | PM 직접 | 순차 | docs/ 갱신 판단 |

### 4.2 실행 체크리스트

> 총 11개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: AGENT.md §실행 프로세스 전면 재작성 (골격)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: §실행 프로세스(T1~T5+G, `:38-72`)를 단계×축×호출모드 매트릭스(§3.1.2)로 재작성. Agent 도구 서술 제거, opal-agent 동기/비동기 명령 형태·`[WORKER]` 마커·컨텍스트 재주입 목록(R-C)·모델 매핑 절차(R-G)·비동기 경계(R-B) 반영. 행동 규칙 6번 교체.
- **완료 기준**: 4축×호출모드 매트릭스 존재, 내부 디스패치용 "Agent 도구" 문구 0건, 명령 형태 2종(동기/비동기) 존재
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: §결과 파일 규약 절 신설
- [x] 완료
- **소속 기능**: F-002
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: 3-분리 캡처 경로(§3.2.2)·5필드 스키마(R-H)·완료 마커(exitcode 파일 존재)·완료 판정 로직 표·재시도 접미사(R-F)·수거 실패→blocked 처리 명문화.
- **완료 기준**: 경로 규칙·필수 필드·완료 마커·수거 실패 처리 4항목 존재
- **테스트**: TS-002, TS-003
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: §생성자 resume 절차 절 신설
- [x] 완료
- **소속 기능**: F-003
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: cold prime(§3.3.2) 4단계 절차 — UUID 생성 → session.json 보존 → T1 `--session-id` → T3 `--resume`. 상호배타·claude 전용 명시.
- **완료 기준**: session_id 보존 위치·재개 명령 형태 존재
- **테스트**: TS-004
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: §allowedTools 표준 절 신설
- [x] 완료
- **소속 기능**: F-004
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: 축별 allowlist 표(§3.4.2) + [MUST] `--dangerously-skip-permissions` 금지 명문 + 프로젝트 스코프(`--cwd`) 한정.
- **완료 기준**: 6단계 allowlist 문서화 + skip-permissions 금지 명문
- **테스트**: TS-005
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 5: §플랫폼 가용성 절 신설
- [x] 완료
- **소속 기능**: F-006
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: 플랫폼 가용성 표(§3.6.2) + 1차 claude 범위 문구. [MUST] 플랫폼 조건문 미도입 준수.
- **완료 기준**: 가용성 표 존재, 본문에 플랫폼 if 분기 없음
- **테스트**: TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: observability.md 적용 범위 정합
- [x] 완료
- **소속 기능**: F-005
- **영역**: 참조
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/observability.md`
- **작업 내용**: §행위주체 표시 트리거를 PM×Agent 도구로 유지 명확화 + opal-agent 내부 채널은 아이콘 룩업 대상 아님·결과 파일/요약으로 관측성 확보 문단 추가(§3.5.2 결정 #9).
- **완료 기준**: opal-agent 채널 적용 범위 문단 존재
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1
- **비고**: Step 7·8과 병렬 가능(독립 파일)

#### Step 7: opal-harness.md §5/§6 포인터 보강
- [x] 완료
- **소속 기능**: F-005
- **영역**: 참조
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §5·§6 stub에 opal-agent 채널 내부 디스패치 관측·모델 매핑 SSOT 포인터 1줄씩 추가(비복제, loop-control §2 원칙).
- **완료 기준**: 포인터 존재, 수치·규칙 복제 0
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1
- **비고**: Step 6·8과 병렬 가능

#### Step 8: oppl SKILL.md 정합 + T2 축 정정
- [x] 완료
- **소속 기능**: F-005
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: §파이프라인 ASCII 주석·§디스패치 idiom을 opal-agent 채널로 정합(§3.5.2). §디스패치 표 ① T2 축 귀속을 test-agent(mode:red)로 정정(H-10). PM→루프 액션 에이전트 Agent 도구 유지 불변 확인.
- **완료 기준**: oppl↔AGENT 서술 모순 0, T2=test-agent축 정합
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1
- **비고**: Step 6·7과 병렬 가능

#### Step 9: 변경이력 행 일괄 추가(4종)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: AGENT.md, observability.md, opal-harness.md, oppl SKILL.md
- **작업 내용**: 4개 문서 §변경이력에 `YYYY-MM-DD HH:mm KST | 내용(066)` 행 추가. semver 증가. KST는 `node ~/.opal/tools/date/date.js datetime`로 취득.
- **완료 기준**: 변경 문서 4종 전부 066 행 존재, 일시 형식 준수
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 2,3,4,5,6,7,8

#### Step 10: 실증 실행 (TEST 단계)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `tasks/066-…/TEST-SCENARIO.md`(PM STEP 3.5) + 실증 로그
- **작업 내용**: AGENT.md 배포(install) 후 샘플 태스크에 루프 액션 에이전트 1회 디스패치 → S-1~S-6 실증(§3.7.2). 재개 0회·resume·blocked·결과 파일 수거 관측.
- **완료 기준**: TS-008 PASS + 증거 기록
- **테스트**: TS-008
- **실행 방법**: direct (PM, TEST 단계)
- **의존**: Step 1~9

#### Step 11: docs/ 갱신 판단
- [x] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`(해당 시)
- **작업 내용**: opal-agent 내부 채널이 Project Loop 컴포넌트 서술(내부 디스패치 메커니즘)에 영향하는지 판단. 구조 서술이 Agent 도구 전제이면 갱신, 아니면 "영향 없음" 기록.
- **완료 기준**: 갱신 또는 "영향 없음" 판단 기록
- **테스트**: 산출물 검사
- **실행 방법**: direct (PM)
- **의존**: Step 1~9

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2,3,4,5 | 동일 파일(AGENT.md) 순차 수정 — 충돌 방지 |
| Step 2 → 3 → 4 → 5 | 동일 파일 AGENT.md 연속 절 추가 — 순차 |
| Step 6 ∥ Step 7 ∥ Step 8 | 독립 파일(observability/harness/oppl) — 병렬 가능 |
| Step 6,7,8 → Step 9 | 변경이력은 대상 문서 확정 후 일괄 |
| Step 9 → Step 10 → Step 11 | 실증은 배포 후, docs 판단은 실증 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 4축×호출모드 매트릭스·명령 형태·컨텍스트 재주입 존재, Agent 도구 문구 잔존 0 | TS-001 | grep "Agent 도구"(내부 디스패치 맥락) 0건 |
| F-002 | 결과 파일 3-분리·완료 마커·수거 실패 처리 명문 | TS-002,003 | 4항목 존재 + exit 2 결정론 판별 서술 |
| F-003 | cold prime session_id 보존·재개 명령 형태 | TS-004 | T1 `--session-id`=T3 `--resume` 절차 존재 |
| F-004 | 축별 allowlist + skip-permissions 금지 | TS-005 | 6축 allowlist + [MUST] 금지 명문 |
| F-005 | 하네스·oppl 정합 + T2 축 정정 + 변경이력 4종 | TS-006 | 모순 0 + 066 행 4종 |
| F-006 | 플랫폼 가용성 표 + 조건문 미도입 | TS-007 | 표 존재 + if 분기 0 |
| F-007 | 샘플 완주(재개 0)·resume·blocked·결과 파일 | TS-008 | 실증 PASS + 증거 |

### 5.2 회귀 테스트
- [ ] 065 확정 계약 불변: 검증 2원화 순서(`065-H-9`)·blocked 7종·3-SSOT 경계(test-tool만)·결과 계약 6필드 서술 유지
- [ ] PM→루프 액션 에이전트 채널 Agent 도구 유지(전환 대상은 내부 축만)
- [ ] 순서 강행 가드(G 전 T3 금지·red_not_confirmed G 거부) 서술 보존

### 5.3 코드/문서 품질
- [ ] [MUST] 변경 문서 전부 §변경이력 066 행(YYYY-MM-DD HH:mm KST, semver) — CONVENTIONS §변경이력
- [ ] SSOT 비복제 — harness §5/§6·loop-control §2 포인터 유지, 수치 미복제
- [ ] 인라인 인용·[MUST] 포맷 준수(citation-rules §2·§4)

### 5.4 보안
- [ ] [MUST] `--dangerously-skip-permissions` 명령 예시 0건 + 금지 명문
- [ ] allowlist 프로젝트 스코프 한정(MCP·네트워크 도구 미포함)
- [ ] [MUST] 구독 로컬 claude -p 사용, API키·SDK 미도입 (console-brain-subscription-auth)
- [ ] `.oppl-run/` 결과 파일에 시크릿 노출 없음 확인

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 11개 | 복잡 |
| 변경 파일 수 | 4개(AGENT.md·observability·harness·oppl) | 복잡 |
| 모듈 범위 | 다중(에이전트·하네스·오케스트레이터) | 복잡 |
| 작업 유형 | 대규모 개선(채널 전환 + 규약 3종 신설) | 복잡 |
| 외부 의존성 | opal-agent 채널(기존 도구, 개조 없음) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- 전 Step 단일 에이전트 `opal-task-agent`(프레임워크 문서 영역) — FE/BE/DB 없음(순수 Markdown).
- Batch 1: Step 1 (AGENT.md 골격, 단독).
- Batch 2: Step 2→3→4→5 (동일 파일 순차, 파일 충돌 방지 규칙).
- Batch 3: Step 6 ∥ 7 ∥ 8 (독립 파일 병렬).
- Batch 4: Step 9 (변경이력 일괄).
- Batch 5: Step 10·11 (PM 직접, TEST/docs).

### C-2. 스킬 요구사항
- Step 1~9: op-dev-execute(문서 편집). 신규 스킬 갭 없음 — 반복 패턴은 있으나 1태스크 국소이므로 인라인 지침.

### C-3. 도구 요구사항
- Read/Edit/Write(문서), Bash(`node ~/.opal/tools/date/date.js datetime` KST), 배포 검증 `./scripts/install-mac.sh`.
- 실증(Step 10): `~/.opal/tools/opal-agent/run.sh`, Bash `run_in_background`.

### C-4. 테스트 전략
- L1 정적: grep("Agent 도구"·skip-permissions)·변경이력 행·문서 모순 대조 (TS-001,002,005,006,007).
- L2 실증: 샘플 태스크 완주·resume·blocked·결과 파일 수거 (TS-003,004,008) — 배포 후 PM 디스패치.
- 회귀: 065 계약 4종 불변 대조(§5.2).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown(AGENT.md·SKILL.md·하네스) | op-dev-plan/execute |
| 채널 | Claude Code headless(`claude -p`, `--resume`/`--session-id`/`--allowedTools`/`--output-format json`) | opal-agent |
| 셸 | Bash(`run.sh` 래퍼, `run_in_background`) | — |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 조회 불요 — 전부 OPAL 내부 소스 (ANALYSIS §6.3) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 루프 액션 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 개정 본체 — 내부 디스패치 절 |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | 명령 형태·플래그·검증 상태·cold session |
| D-3 | 소스 | opal-agent 구현 | `opal/tools/opal-agent/opal_agent.py` | 채널 능력 SSOT(코드) — 출력·종료코드·상호배타 |
| D-4 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 정합 대상 — 파이프라인·디스패치 |
| D-5 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | §5/§6 stub 보강 지점 |
| D-6 | 설계 | Observability 모듈 | `opal/core/references/harness/observability.md` | 행위주체 표시 Agent 도구 전제 |
| D-7 | 기록 | 065 AGENTIC-LOG | `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md` | 릴레이 마찰·실증 준거 |
| D-9 | 지식 | brain concept | `.opal/brain/pages/concept/oppl-executor-delegation-architecture.md` | 065 확정(4축·3-SSOT·blocked 7종·결과 6필드) |
| D-11 | 설계 | 모델 매핑 | `~/.opal/references/opal-model-mapping.md` | 레벨↔실모델 SSOT |
| D-12 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 변경이력·배포 경계·플랫폼 격리 [MUST] |
| D-13 | 설계 | 066 ANALYSIS | `tasks/066-…/ANALYSIS.md` | 능력 매트릭스·출력 계약·리스크 R-A~R-I |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 헤드리스 fresh 프로세스에서 생성자/Evaluator/test-agent AGENT.md가 요구 입력을 프롬프트 밖에서 기대(세션 상속 전제) → 동작 불완전 | F-001 | 중 | R-C 재주입 목록 완비 + S-1 실증. 미검증 리스크(ANALYSIS §3.2) — TEST에서 확인 |
| R-2 | 문서/문서 불일치 — oppl SKILL §디스패치 "생성자 디스패치 연속"(T1+T2) ↔ SSOT test-agent(T2 RED). **SSOT 기준 정정**(H-10, Step 8) | F-005 | 저 | brain concept·AGENT.md 기준으로 test-agent축 정정, PLAN 명기 |
| R-3 | Bash 타임아웃 상한 내 단시간 축 완료 실측 부재(R-D) | F-002 | 중 | 축별 `--timeout` 배분(G 300s/T4a 540s/T4b 300s, Bash ms 상회) + S-3 실증, 초과 시 blocked |
| R-4 | 구독 rate limit — 태스크당 내부 프로세스 4~6개 병렬도 영향 | F-001 | 저 | 단계 순차(동시성 없음)로 완화, 실측은 후속 |
| R-5 | 결과 파일 `.oppl-run/`가 커밋/gitignore 미정 | F-002 | 저 | 전송 산출물이므로 gitignore 권고 문구 AGENT.md에 부기(EXECUTE 재량) |
| R-6 | claude 외 provider cold session-id 미지원 → resume 연속성 claude 한정 | F-003,006 | 저 | 1차 범위 claude 명시로 정합(R-6) |

> **decision_required 없음** — R-A(축/호출모드 분리)·R-G(모델 매핑 책임=루프 액션 에이전트)·#8(cold prime)·#9(observability 범위 축소) 등 위임된 9개 결정은 전부 SSOT 근거로 PLAN 설계 결정으로 확정. H-10 문서 불일치는 SSOT(brain/AGENT.md)가 명확하여 정정으로 처리(에스컬레이션 불요). opal-agent 도구 개조 불요(비동기는 호출측 래핑, R-B).

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-17 14:03 | 초기 작성 — 7기능(F-001~F-007) 설계, 4축×호출모드 매트릭스(R-A), 결과 파일 3-분리 규약(R-F/H/I), cold prime resume(#8), 축별 allowlist(R-4), 하네스·oppl 정합·T2 축 정정(H-10), 플랫폼 가용성 표(R-6), 실증 시나리오 설계(R-7), 리스크 가설 표 H-1~H-11, 11-Step 실행 체크리스트(복잡 모드). decision_required 없음 (066) |
| v1.1 | 2026-07-17 14:03 | PM Gate 보완(1/3) — 결함1(정합성): §3.1.2 매트릭스 model 셀을 대상 에이전트 frontmatter 실측값으로 정정(G=advanced `evaluator:7` / T4b=체커 준용 conv standard·sec advanced), 각주-셀 모순 해소. 결함2(명확성): 리스크 표 H-N을 066 로컬 네임스페이스로 명시하는 각주 추가 + 065 계약 참조를 `065-H-9` 접두 표기로 전면 구분(§1.1·§3.1.2·§5.2) (066) |

---
name: opal-pilot-dev-wireframe
description: |
  **Wireframe UI 오케스트레이터**. 와이어프레임 설계부터 UI 구현까지 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-wireframe", "opdw".
  "화면 구현", "UI 만들어줘", "화면 수정" 등 기존 프로젝트 기반 UI 작업은 opal-pilot-dev 또는 opal-pilot-dev-short에서 ui-designer plan-driven 모드로 수행한다.
---

# Wireframe UI 오케스트레이터

## Harness
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## 입력물에 따른 분기

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 | .md/.txt/.pdf/.docx 파일 | WIREFRAME |
| 이미지(스케치/스크린샷) | .png/.jpg 파일 | WIREFRAME |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

---

## STEP 1: TASK (Wireframe 특화)

Harness "TASK 공통 프로세스"를 따르되, 아래를 추가:
- 기술 환경 (React/Next.js 버전, shadcn/ui 여부)
- 출력 모드: 프로토타입(bundle.html) vs 프로덕션(Next.js)
- 입력물 분류 + wireframe.md 경로 (기존/생성 필요)
- 보고 시 입력물 분기 판별 결과 포함

TASK 완료 → 사용자 보고.

> **[MUST] 행 갱신**: `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done` 호출. LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다. 행을 mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다.
> **단계 시작 (P-3)**: `~/.opal/tools/state-tool/run.sh advance <task-path> --row <N>` 호출로 해당 단계 작업 행을 🔄로 전환.
> **단계 건너뛰기 차단**: state-tool stage-transition guard가 단계 N의 필수 행이 완료되지 않으면 단계 N+1 진입(mark)을 자동 거부한다 (PLAN §M-A). 행에 의존하지 않는다.
> **사용자 확인 (P-5)**: 사용자 발화 후 PM이 `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done --owner user --note '소유자 확인: TASK 완료'` 호출.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-3 / P-5

---

## STEP 2: WIREFRAME

> wireframe.md가 이미 존재하면 **스킵** → EXECUTE.

워커 디스패치로 wireframe.md 생성. **model**: standard.
- 스킬: op-dev-wireframe, 입력: TASK.md + 정책서/이미지
- 완료
  → **PM Gate** (TASK.md 요구사항 체크박스 갱신 + wireframe 직접 검증 — 점검 목록 참조):
    1. `{wireframe.md 경로}` Read — 화면 목록·요구사항 커버 확인
    2. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (wireframe.md 화면 대조)
       - [ ] 화면 구성 및 레이아웃의 완성도 (op-dev-qa/SKILL.md 와이어프레임 검증 기준 참조)
       - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
       - [ ] TASK.md 요구사항 체크박스 갱신 완료
  → PM Gate 통과 후 해당 행을 단일 mark. 사용자에게 WIREFRAME 결과 보고.

state-tool 호출:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 4 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 5 --done --owner user --note '소유자 확인: WIREFRAME 완료'
```

> **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
> 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
> 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
> 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)

---

## STEP 3: EXECUTE (UI 구현)

### 3-1. 라우팅 결정 (v2.2 신설)

와이어프레임 파이프라인의 EXECUTE는 **FE 단일 라우팅**을 사용한다 (분배 디스패치 대상 아님).

- **기본 에이전트**: `opal-fe-agent` (FE 전문)
- **근거**: wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 없다(op-dev-wireframe 산출물). 와이어프레임 구현은 본질적으로 FE 작업이므로 UI 전문 에이전트를 직접 지정한다.
- **폴백**: `opal-fe-agent` 사용 불가 플랫폼이면 `opal-task-agent`로 디스패치 (op-dev-execute/SKILL.md 매핑에 따라 generalist-guide로 폴백).

### 3-2. 디스패치 프롬프트

워커 디스패치로 wireframe.md 기반 UI 구현. **model**: standard.

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{태스크명}/
**checklist_source**: wireframe.md
**UI 구현 모드**: ui-designer scaffold(프로토타입) 또는 plan-driven(프로덕션)
**담당 Step**: wireframe.md 전체 (분배 없음)
**Scope 제한**: FE 영역. 영역 외 파일 수정 시 즉시 블로커 보고.
**하네스 Guards**: wireframe.md에 없는 화면 추가 금지. 설계 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}
```

> **에이전트별 자동 가이드 선택**: `opal-fe-agent`로 라우팅되면 워커는 op-dev-execute/SKILL.md 매핑에 따라 execute-specialist-guide.md를 자동 Read한다.

### 3-3. 완료 후

1. **PM Gate** (빌드/린트 결과 + wireframe↔코드 대조 직접 검증 + 체크리스트 갱신 — 점검 목록 참조):
   1. `{wireframe.md 경로}` Read — wireframe.md 화면 목록 확인
   2. 변경 파일 코드 리뷰 — 빌드/린트 결과 및 코드 품질 확인
   3. 검증 체크리스트:
      - [ ] 빌드/린트 오류 없음 (op-dev-qa/SKILL.md EXECUTE-UI 검증 기준 참조)
      - [ ] wireframe.md 화면 목록 전체 구현 여부 (wireframe↔코드 대조)
      - [ ] 컨벤션 자동 진단 PASS (changed_files 컨벤션 적용 대상 ≥1건 시 발동, GC-CONVENTION-*.md Critical/High 0건)
      - [ ] TASK.md 요구사항 체크박스 갱신 완료
   → PM Gate 통과 후 해당 행을 단일 mark.
2. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

state-tool 호출:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 7 --done  # PM Gate
~/.opal/tools/state-tool/run.sh mark <task-path> --row 8 --done --owner user --note '소유자 확인: EXECUTE 완료'
```

보고 형식:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {GC-CONVENTION-*.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

---

## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 후 행 9(CLOSE 행) mark (`~/.opal/tools/state-tool/run.sh mark <task-path> --row 9 --done` 호출 — P-1). 행을 mark하는 것 자체가 state 기록이다.

> **CLOSE 진입 게이트 자동 검증 (§2.16 G-13)**: CLOSE 단계 첫 행 mark 시 도구가 직전 단계 사용자 확인 행의 `owner=user` 여부를 자동 검증한다. 미통과 시 `close_gate_violation` 에러 반환 — agentic 모드의 `--auto-pass`도 거부됨.

> **추가작업 발생 시 (P-6)**: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after 9 --stage CLOSE --item '추가 작업 항목'` 호출 → current_status 자동 `additional_work` 전환.
> 근거: `PLAN.md` §3 Step 8 P-1 / P-6 / P-8 / §2.16 G-13

2. 완료 보고

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

Harness STATE.md 템플릿에 적용:
- `{모드}`: Wireframe UI
- `{단계 목록}`: TASK / WIREFRAME / EXECUTE / CLOSE
- `{산출물 목록}`: TASK.md, wireframe.md(기존 존재 가능), GC-CONVENTION-*.md, DONE.md

**진행 현황 행 예시** (아래 표는 `state init --rows-from <SKILL.md>` 또는 `--rows-spec` 인자의 SSOT — LLM이 직접 작성하는 것은 금지된다):

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opdw --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-dev-wireframe/SKILL.md` 호출. 기본값: `semi-agentic`. `--rows-from`이 아래 표를 파싱하여 행 구성을 자동 추출한다. 행 데이터를 직접 편집하지 않는다.
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-15 / `PLAN.md` §2.3 / §2.20.2 / §3 Step 8 (P-3 advance, P-1 mark)

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | 사용자 확인 | ⬜ | - |
| 3 | WIREFRAME | 작업 | ⬜ | - |
| 4 | WIREFRAME | PM Gate | ⬜ | - |
| 5 | WIREFRAME | 사용자 확인 | ⬜ | - |
| 6 | EXECUTE | 작업 | ⬜ | - |
| 7 | EXECUTE | PM Gate | ⬜ | - |
| 8 | EXECUTE | 사용자 확인 | ⬜ | - |
| 9 | CLOSE | DONE.md 생성 | ⬜ | - |
```

> TASK.md 생성은 행 1(TASK 작업)에 흡수. wireframe.md 생성은 행 3(WIREFRAME 작업)에 흡수. State Gate 행은 state-tool stage-transition guard(PLAN §M-A)로 이전 완료 — 행으로 강제하지 않는다.
> WIREFRAME 스킵 시 (wireframe.md 기존 존재): WIREFRAME 단계 행(#3-#5)을 `-`로 표기한다.

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| WIREFRAME | TASK.md, wireframe.md | TASK.md 요구사항, wireframe.md 화면 목록; op-dev-qa/SKILL.md 와이어프레임 검증 기준 참조 |
| EXECUTE | changed_files, GC-CONVENTION-*.md | 빌드/린트 결과, wireframe↔코드 대조, 컨벤션 자동 진단; op-dev-qa/SKILL.md EXECUTE-UI 검증 기준 참조 |

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opdw {작업}`)은 semi-agentic 모드. WIREFRAME(PLAN-equivalent)까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- WIREFRAME 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opdw 작업` | semi-agentic (기본) |
| `//opdw --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opdw --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 활성화

STATE.md 모드 필드를 지정하여 기록한다 (기본: `semi-agentic`):

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill opdw --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-dev-wireframe/SKILL.md
```

### 자율 게이트 흐름 (semi-agentic)

```
TASK → WIREFRAME Gate → EXECUTE Gate → CLOSE
사용자   사용자 승인        PM 자율         사용자 승인 필수
         (모드 경계)
```

- WIREFRAME Gate까지 사용자 승인 필수 (interactive 동작)
- WIREFRAME 사용자 확인 행 통과 후 EXECUTE Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- 자율 통과 시 `mark --row N --done --auto-pass --note '<근거>'` 호출 (P-8)
- **CLOSE 단계 최초 진입 행은 `--auto-pass` 금지** (`agentic_close_gate_requires_user` — §2.16 G-13)
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.3 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.4 | 2026-04-01 | WIREFRAME/EXECUTE 워커 디스패치에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v1.5 | 2026-04-02 | 서브 하네스 [MUST] 추가 + WIREFRAME/EXECUTE PM Gate 추가 (072) |
| v1.6 | 2026-04-07 | TASK/WIREFRAME/EXECUTE 각 단계 Gate 순서에 State Gate 추가 + Agentic Mode 섹션 신설 (094) |
| v1.7 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v1.8 | 2026-04-09 | STATE.md 도메인 치환값 — 진행 현황 행 예시 신규 추가 (산출물 생성 행 포함) (101) |
| v1.9 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.0 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.1 | 2026-04-15 | STEP 4 CLOSE 단계 신설 + EXECUTE PM Gate 후 State Gate/사용자 확인 추가 + 진행 현황 행 CLOSE 2행 구조 반영 + 보고 형식 C안 적용 (121) |
| v2.2 | 2026-04-23 11:39 | STEP 3 EXECUTE를 FE 단일 라우팅(opal-fe-agent)으로 지정 — 와이어프레임 전용 흐름상 PLAN.md §4.2 분배 디스패치 미적용 근거 명시, 디스패치 프롬프트에 담당 Step/Scope 제한 필드 추가 (129) |
| v2.3 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v2.4 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). "STATE.md 도메인 치환값" SSOT 보존 + `--rows-from` 파싱 SSOT 명시. agentic 활성화에 `--auto-pass` + CLOSE 진입 게이트 거부 정책 추가 (134) |
| v2.5 | 2026-05-08 | PM Gate 점검 목록 EXECUTE 행 산출물에 GC-CONVENTION-*.md 추가 — 컨벤션 자동 진단 EXECUTE PM Gate 발동 (136) |
| v2.6 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 + Harness 절 3-way 분기 + WIREFRAME 모드 경계 명시 (140) |
| v2.7 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v2.8 | 2026-06-07 | STATE 행 20→9 재구성 — opds 패턴 적용 + op-dev-qa 디스패치→PM Gate 흡수: State Gate 행(#8/#10/#15/#17/#20) 제거(guard로 이전), QA Gate 행(#6/#13)+QA 산출물 행(#7/#14) 제거, 산출물 행 작업 행 흡수, gate-pass 제거, WIREFRAME·EXECUTE PM Gate에 빌드/린트·wireframe↔코드 대조 직접 검증 체크리스트 추가 (014) |

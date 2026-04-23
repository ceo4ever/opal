# TASK: op-dev-execute 에이전트별 지침 구획화 + EXECUTE 디스패치 라우팅 전파

> 작성일: 2026-04-22 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 + 진단 대화
> 출력: TASK.md

## 작업 목표

op-dev-execute 스킬을 **공통/전문/범용 3구획** 구조로 재편하여 전문 에이전트(opal-fe-agent 등)와 범용 에이전트(opal-task-agent)가 각자에게 맞는 지침만 Read하도록 정리하고, PM이 직접 워커를 디스패치하는 오케스트레이터(opds/opd/opdw/sdd)의 EXECUTE 단계에 **PLAN.md §4.2 agent 필드 기반 Step별 분배 디스패치** 절차를 추가한다.

## 배경

PLAN 단계에서 op-dev-plan(v2.2, 117 태스크)이 각 Step에 `agent` 필드를 배정하도록 개선되었으나, **EXECUTE 단계 오케스트레이터 매뉴얼에 "Step별 agent 필드를 순회하여 전문 에이전트에게 분배 디스패치"하는 절차가 누락**되어 있다. 결과적으로 PM은 op-dev-execute 워커를 단일로 디스패치하고, 대부분 범용 에이전트(opal-task-agent)가 모든 Step을 처리한다. 이는 opal-fe-agent/opal-be-agent의 페르소나·도메인 도구·ui-designer 연동 등을 무력화한다.

추가로 op-dev-execute 스킬 자체가 **FE/BE 페르소나 선택 로직**(L22-37), **FE 역할 분담**(L130-175), **활용 스킬/MCP 테이블**(L178-194)을 포함해 전문 에이전트의 책임 영역과 중복된다. 전문 에이전트가 이 스킬을 Read하면 페르소나·도메인 지식 중복이 발생한다.

## 배경 분석 (대화에서 도출)

### 1. OPAL 계층 관계 재확인

| 종류 | 역할 | 주체 |
|------|------|------|
| opal-pilot-* (오케스트레이터 스킬) | **PM의 매뉴얼/도구** — 에이전트가 아님 | PM이 Read하여 프로세스 수행 |
| op-dev-* (단계 스킬) | 단계별 실행 매뉴얼 | 워커가 Read하여 실행 |
| opal-*-agent | 실제 액션 주체(페르소나) | 서브에이전트 |

### 2. 현재 증상 (대화에서 확인)

1. PLAN.md §4.2 실행 체크리스트는 각 Step에 `agent` 필드를 정상 기재
2. 그러나 opds STEP 3(`opal-pilot-dev-short/SKILL.md:62-66`)과 opd STEP 4(`opal-pilot-dev/SKILL.md:79-100`)는 `op-dev-execute 워커 디스패치` 한 줄만 지시 — agent 필드 순회 절차 없음
3. PM이 기본 워커(opal-task-agent)로 디스패치 → 모든 Step이 범용 워커에서 수행됨

### 3. op-dev-execute 스킬 적합성 분석

| 영역 | 위치 | 공통/중복 |
|------|------|---------|
| 금지 행동 / 보안 가드레일 / 블로커 / 결과 반환 | `references/execute-guide.md` 대부분 | ✅ 공통 |
| 체크리스트 갱신 / @header / QA 자체 검증 | SKILL.md Step 4·5, 3-H | ✅ 공통 |
| 페르소나 선택 (FE/BE 분기 Read) | SKILL.md L22-37 | ❌ 전문 에이전트와 중복 |
| FE 역할 분담 (ui-designer 연동) | SKILL.md L130-175 | ❌ opal-fe-agent AGENT.md와 중복 |
| 활용 스킬/MCP (FE/BE) | SKILL.md L178-194 | ❌ 전문 에이전트 AGENT.md와 중복 |

### 4. 파이프라인별 디스패치 패턴

| 오케스트레이터 | 디스패치 방식 | 이번 태스크 처리 |
|-------------|-------------|---------------|
| opds / opd / opdw / sdd | **PM이 직접** op-dev-execute 디스패치 | STEP EXECUTE에 분배 절차 추가 필요 |
| oppd | `opal-task-action-agent` 경유, `action_domain` 기반 에이전트 선택 (127 진행 중) | 스킬 구획화(R-1~R-4)만으로 자동 혜택, 라우터 수정 불필요 |

## 확정된 설계 방향 (대화에서 합의)

### §1. op-dev-execute 스킬 3구획 구조 (파일 분리)

```
opal/skills/op-dev-execute/
├── SKILL.md                                   # 진입점 + 에이전트별 guide 매핑
├── references/
│   ├── execute-guide.md                       # 공통 규칙·프로세스 (모든 워커)
│   ├── execute-specialist-guide.md            # 신규 — 전문 에이전트 지침
│   └── execute-generalist-guide.md            # 신규 — 범용 에이전트 지침
└── personas/                                  # 기존 유지 (범용 에이전트가 동적 Read)
    ├── frontend-engineer.md
    └── backend-engineer.md
```

### §2. 가이드 선택 방식: B안 (워커 자기 판단)

- `applied_guide` 같은 신규 디스패치 파라미터는 **도입하지 않는다**
- SKILL.md 내부의 "에이전트 이름별 guide 매핑 테이블"에 따라 **워커가 자기 에이전트 이름으로 Read 대상을 결정**한다
- 근거: 워커는 자기 에이전트를 알고 있으므로 PM 부담 없이 자동 선택 가능, 오케스트레이터 프롬프트 변경 최소화

**매핑 테이블 (SKILL.md에 배치)**:

| 에이전트 | Read 대상 |
|---------|---------|
| opal-fe-agent, opal-be-agent, opal-db-agent | execute-guide.md + execute-specialist-guide.md |
| opal-task-agent (범용) | execute-guide.md + execute-generalist-guide.md |
| 기타 / 미지정 | execute-guide.md + execute-generalist-guide.md (폴백) |

### §3. 오케스트레이터 EXECUTE 분배 디스패치 범위

- opds, opd, opdw, sdd — PM이 직접 디스패치 → **Step별 분배 절차 추가**
- oppd — 라우터(opal-task-action-agent) 경유 → **이번 변경 대상 아님** (127 진행 중, 충돌 회피)

### §4. 에이전트 AGENT.md는 수정 불필요

`opal-fe-agent`, `opal-be-agent`, `opal-db-agent`, `opal-task-agent` 모두 이미 "스킬 SKILL.md Read" 프로세스를 보유한다. 스킬이 매핑 테이블로 가이드를 자동 선택하므로 에이전트 프로세스 변경 없음.

## 요구사항

- [x] **R-1** op-dev-execute SKILL.md 구조 재편
  - **무엇을**: (a) "실행 가이드 선택" 섹션 신설 + 에이전트 이름별 guide 매핑 테이블 삽입 (b) 페르소나 선택 로직(L22-37)·FE 역할 분담(L130-175)·활용 스킬/MCP 테이블(L178-194)을 SKILL.md에서 제거하고 references 쪽으로 이관 (c) "실행 컨텍스트" 섹션의 문구를 새 구조에 맞게 재정의
  - **어디에**: `opal/skills/op-dev-execute/SKILL.md`
  - **왜**: 확정 방향 §1, §2 — 공통/전문/범용 구획 구조 + 워커 자기 판단 방식
  - **AC**: SKILL.md에 "실행 가이드 선택" 섹션이 있고, 매핑 테이블이 §2와 동일하게 명시되어 있다. 기존 "페르소나"·"FE 역할 분담"·"활용 스킬/MCP" 섹션은 SKILL.md에서 제거되고 references 파일로 이관되어 있다. 변경이력 행이 추가되어 있다.

- [x] **R-2** execute-guide.md 공통 부분 정비
  - **무엇을**: FE ui-designer 연동 항목(현행 L64-67)을 execute-specialist-guide.md로 이관. 나머지는 모든 워커 공통 가이드로 유지
  - **어디에**: `opal/skills/op-dev-execute/references/execute-guide.md`
  - **왜**: 확정 방향 §1 — 공통 규칙 SSOT 유지, 도메인 분기 제거
  - **AC**: execute-guide.md에 FE 전용 절차가 남아있지 않다. 모든 워커가 Read해도 충돌 없는 내용만 포함한다. 변경이력 행이 추가되어 있다.

- [x] **R-3** execute-specialist-guide.md 신규 작성
  - **무엇을**: 전문 에이전트(opal-fe-agent/opal-be-agent/opal-db-agent)가 op-dev-execute 수행 시 따를 지침
  - **어디에**: `opal/skills/op-dev-execute/references/execute-specialist-guide.md` (신규)
  - **왜**: 확정 방향 §1 — 전문 에이전트 지침 분리
  - **AC**: 최소 아래 5개 항목이 포함된다: (a) 페르소나 처리 — 에이전트 AGENT.md의 페르소나 우선 사용, 스킬의 페르소나 Read 불요 (b) Scope — 디스패치 프롬프트의 "담당 Step" 범위만 수행 (c) 도메인 도구 — 에이전트 AGENT.md의 MCP/스킬 활용 테이블 참조 (d) FE 전문 케이스 — ui-designer 연동 조건·연결 지점 명시 (e) 영역 침범 방지 — 에이전트 AGENT.md의 "금지 규칙" 1차 기준 + 공통 가드레일은 execute-guide.md 참조

- [x] **R-4** execute-generalist-guide.md 신규 작성
  - **무엇을**: 범용 에이전트(opal-task-agent)가 op-dev-execute 수행 시 따를 지침. 기존 SKILL.md의 페르소나 선택 로직·FE 역할 분담·활용 스킬/MCP 테이블을 이관
  - **어디에**: `opal/skills/op-dev-execute/references/execute-generalist-guide.md` (신규)
  - **왜**: 확정 방향 §1 — 범용 에이전트 지침 분리
  - **AC**: 최소 아래 4개 항목이 포함된다: (a) 페르소나 처리 — FE/BE/공통 영역에 따라 `personas/frontend-engineer.md` 또는 `personas/backend-engineer.md` 동적 Read (b) Scope — 단일 워커가 디스패치 범위 전체를 순차 처리 (c) FE 역할 분담(ui-designer vs op-dev-execute) — 기존 SKILL.md L130-175 내용 이관 (d) 활용 스킬/MCP (FE/BE) — 기존 SKILL.md L178-194 이관. 공통 규칙은 execute-guide.md 참조로 명시.

- [x] **R-5** opds(opal-pilot-dev-short) STEP 3 EXECUTE 분배 디스패치 절차 추가
  - **무엇을**: STEP 3 EXECUTE에 "PLAN.md §4.2 실행 체크리스트의 Step별 agent 필드를 읽어, Phase 순서대로 해당 전문 에이전트에게 분배 디스패치" 절차를 명시. 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 추가
  - **어디에**: `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 3
  - **왜**: 확정 방향 §3 — PM이 직접 디스패치하는 오케스트레이터
  - **AC**: STEP 3 EXECUTE에 (a) PLAN.md §4.2 agent 필드 순회 (b) 영역별 Step 묶음 생성 (c) Phase 순서 분배 디스패치 절차가 명시되어 있다. 디스패치 프롬프트 예시에 `담당 Step`·`Scope 제한` 필드가 포함된다. 변경이력 행이 추가되어 있다.

- [x] **R-6** opd(opal-pilot-dev) STEP 4 EXECUTE 분배 디스패치 절차 추가
  - **무엇을**: R-5와 동일 패턴 적용 (Full Task)
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` STEP 4
  - **왜**: 확정 방향 §3
  - **AC**: STEP 4 EXECUTE에 분배 디스패치 절차 명시 + 디스패치 프롬프트 갱신 + 변경이력 행 추가

- [x] **R-7** opdw(opal-pilot-dev-wireframe) EXECUTE 분배 디스패치 절차 추가
  - **무엇을**: 와이어프레임 파일럿의 EXECUTE 단계가 op-dev-execute를 사용하는 경로에 동일 패턴 적용. 와이어프레임 전용 흐름상 분배가 불필요한 경우 근거를 PLAN.md에 명시
  - **어디에**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
  - **왜**: 확정 방향 §3 — Phase 2 포함
  - **AC**: op-dev-execute 호출 경로에 분배 디스패치 절차가 명시되어 있거나, 와이어프레임 전용 흐름상 분배가 불필요하다는 근거가 PLAN.md에 기재되어 있다. 변경이력 행이 추가되어 있다.

- [x] **R-8** sdd(opal-pilot-sdd) EXECUTE 분배 디스패치 절차 추가
  - **무엇을**: SDD 파이프라인의 op-dev-execute 호출 경로에 동일 패턴 적용. `execute-loop-guide.md` 정합성 확인
  - **어디에**: `opal/skills/opal-pilot-sdd/SKILL.md` + `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
  - **왜**: 확정 방향 §3 — Phase 2 포함
  - **AC**: SDD의 op-dev-execute 호출 경로에 분배 디스패치 절차가 명시되어 있거나, SDD 전용 흐름상 분배 방식이 다르다면 PLAN.md에 근거가 명시되어 있다. 변경이력 행이 추가되어 있다.

- [x] **R-9** 변경이력 갱신 (전체)
  - **무엇을**: 수정된 모든 파일에 변경이력 행 추가 (버전·일시·변경내용·(129) 참조)
  - **어디에**: 수정 대상 전체 파일
  - **왜**: 하네스 컨벤션
  - **AC**: 수정된 모든 파일의 변경이력 테이블에 오늘 날짜(2026-04-22)와 변경 요약, (129) 참조가 기재되어 있다.

## 제약 조건

- **127 진행 중 태스크와의 충돌 회피**: `opal-task-action-agent/AGENT.md`와 `opal-pilot-project-dev/SKILL.md`는 127 태스크 범위이므로 **이번 태스크에서 수정하지 않는다**. oppd(opal-task-action-agent 경유)는 스킬 구획화(R-1~R-4)만으로 자동 혜택을 받으므로 라우터 수정 불필요.
- **에이전트 AGENT.md 수정 금지**: opal-fe-agent/opal-be-agent/opal-db-agent/opal-task-agent 모두 현재 구조(스킬 SKILL.md Read) 유지. 스킬이 guide 매핑을 자동 수행.
- **배포 금지** (확정 기준 §2): `~/.opal/` 경로 직접 수정 금지, `install-mac.sh` 실행 금지. 모든 변경은 소스 경로(`opal/skills/`)에서만 수행.
- **스킬 YAML frontmatter 임의 삭제 금지** (프로젝트 AGENT.md 금지사항).
- **하네스 우회 금지** — 이번 변경이 하네스(opal-harness.md)의 Guards/Gates/State 규칙을 우회해서는 안 된다.
- **기존 태스크 호환** — v2.0 이전 형식의 PLAN.md(§4 없음 / agent 필드 없음)에 대한 폴백 규칙 유지: agent 필드가 없으면 generalist guide + opal-task-agent 폴백.
- **커뮤니티 스킬 원본 수정 금지** (프로젝트 AGENT.md 금지사항) — 이번 범위엔 커뮤니티 스킬 없음.

## 기술 스택

- OPAL 프레임워크 (Markdown 기반 스킬/에이전트 정의)
- 도구: Edit/Write (소스 수정), Bash (MEMORY.md 갱신), Read/Grep (영향 검증)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | 핵심 수정 대상 (구획화) |
| D-2 | 소스 | execute-guide.md | `opal/skills/op-dev-execute/references/execute-guide.md` | 공통 부분 정비 대상 |
| D-3 | 소스 | op-dev-plan SKILL.md | `opal/skills/op-dev-plan/SKILL.md` | agent 필드 배정 규칙 참조(§4.2) |
| D-4 | 소스 | plan-guide.md | `opal/skills/op-dev-plan/references/plan-guide.md` | agent 배정 상세 참조 |
| D-5 | 소스 | opal-pilot-dev-short | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 수정 대상 (R-5) |
| D-6 | 소스 | opal-pilot-dev | `opal/skills/opal-pilot-dev/SKILL.md` | opd 수정 대상 (R-6) |
| D-7 | 소스 | opal-pilot-dev-wireframe | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 수정 대상 (R-7) |
| D-8 | 소스 | opal-pilot-sdd | `opal/skills/opal-pilot-sdd/SKILL.md` | sdd 수정 대상 (R-8) |
| D-9 | 소스 | execute-loop-guide.md | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | SDD 실행 루프 정합성 확인 |
| D-10 | 소스 | opal-fe-agent | `opal/agents/opal-fe-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-11 | 소스 | opal-be-agent | `opal/agents/opal-be-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-12 | 소스 | opal-db-agent | `opal/agents/opal-db-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-13 | 소스 | opal-task-agent | `opal/agents/opal-task-agent/AGENT.md` | 범용 에이전트 기준 (수정 대상 아님) |
| D-14 | 소스 | 127 TASK.md | `tasks/127-260418-opp-oppd-specialist-agent-routing/TASK.md` | 진행 중 태스크 — 충돌 회피 근거 |
| D-15 | 문서 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 프로젝트 컨벤션 (네이밍, @header) |
| D-16 | 문서 | docs/PROJECT.md | `docs/PROJECT.md` | 프로젝트 정의·문서 레지스트리 |

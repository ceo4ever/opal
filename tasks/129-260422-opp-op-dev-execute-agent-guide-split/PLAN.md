# PLAN: op-dev-execute 에이전트별 지침 구획화 + EXECUTE 디스패치 라우팅 전파

> 작성일: 2026-04-22
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | 핵심 수정 대상 (구획화 진입점) |
| D-2 | 소스 | execute-guide.md | `opal/skills/op-dev-execute/references/execute-guide.md` | 공통 가이드 정비 대상 (FE 분기 이관) |
| D-3 | 소스 | personas/frontend-engineer.md | `opal/skills/op-dev-execute/personas/frontend-engineer.md` | 범용 에이전트 동적 Read 대상 |
| D-4 | 소스 | personas/backend-engineer.md | `opal/skills/op-dev-execute/personas/backend-engineer.md` | 범용 에이전트 동적 Read 대상 |
| D-5 | 소스 | op-dev-plan SKILL.md | `opal/skills/op-dev-plan/SKILL.md` | §4.2 agent 필드 배정 규칙 (v2.2, 117) |
| D-6 | 소스 | opal-pilot-dev-short | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds STEP 3 EXECUTE 수정 대상 (R-5) |
| D-7 | 소스 | opal-pilot-dev | `opal/skills/opal-pilot-dev/SKILL.md` | opd STEP 4 EXECUTE 수정 대상 (R-6) |
| D-8 | 소스 | opal-pilot-dev-wireframe | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw STEP 3 EXECUTE 수정 대상 (R-7) |
| D-9 | 소스 | opal-pilot-sdd | `opal/skills/opal-pilot-sdd/SKILL.md` | sdd Phase 4 EXECUTE-LOOP 확인 대상 (R-8) |
| D-10 | 소스 | execute-loop-guide.md | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | SDD 실행 루프 정합성 확인 (R-8) |
| D-11 | 소스 | opal-sdd-action-agent | `opal/agents/opal-sdd-action-agent/AGENT.md` | SDD EXECUTE 디스패치 경로 실측 (간접 경유) |
| D-12 | 소스 | opal-fe-agent | `opal/agents/opal-fe-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-13 | 소스 | opal-be-agent | `opal/agents/opal-be-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-14 | 소스 | opal-db-agent | `opal/agents/opal-db-agent/AGENT.md` | 전문 에이전트 기준 (수정 대상 아님) |
| D-15 | 소스 | opal-task-agent | `opal/agents/opal-task-agent/AGENT.md` | 범용 에이전트 기준 (수정 대상 아님) |
| D-16 | 기획 | 127 TASK.md | `tasks/127-260418-opp-oppd-specialist-agent-routing/TASK.md` | 진행 중 태스크 — 충돌 회피 근거 |
| D-17 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력/네이밍/frontmatter 규약 |
| D-18 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷 (PLAN §2 인라인 인용) |
| D-19 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | PM 금지사항·확정 기준 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 진입점 스킬 | ✅ 수정 | `opal/skills/op-dev-execute/SKILL.md:22-37` (페르소나 블록), `:130-175` (FE 역할), `:178-194` (MCP 테이블) |
| `opal/skills/op-dev-execute/references/execute-guide.md` | 공통 EXECUTE 가이드 | ✅ 수정 | `opal/skills/op-dev-execute/references/execute-guide.md:64-67` (FE ui-designer 분기) |
| `opal/skills/op-dev-execute/references/execute-specialist-guide.md` | 전문 에이전트 가이드 | ✅ 신규 | - |
| `opal/skills/op-dev-execute/references/execute-generalist-guide.md` | 범용 에이전트 가이드 | ✅ 신규 | - |
| `opal/skills/op-dev-execute/personas/frontend-engineer.md` | FE 페르소나 | ⬜ 유지 | `opal/skills/op-dev-execute/personas/frontend-engineer.md:1-16` |
| `opal/skills/op-dev-execute/personas/backend-engineer.md` | BE 페르소나 | ⬜ 유지 | `opal/skills/op-dev-execute/personas/backend-engineer.md:1-16` |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 | ✅ 수정 | `opal/skills/opal-pilot-dev-short/SKILL.md:62-66` (STEP 3 EXECUTE) |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 | ✅ 수정 | `opal/skills/opal-pilot-dev/SKILL.md:79-106` (STEP 4 EXECUTE) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 오케스트레이터 | ✅ 수정 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:61-80` (STEP 3 EXECUTE) |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 오케스트레이터 | ⬜ 변경 없음 (근거 명시) | `opal/skills/opal-pilot-sdd/SKILL.md:183-232` (Phase 4 EXECUTE-LOOP) |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | SDD 루프 가이드 | ⬜ 변경 없음 (근거 명시) | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md:1-434` |
| `opal/agents/opal-fe-agent/AGENT.md` | FE 전문 에이전트 | ❌ 금지(TASK 제약) | `opal/agents/opal-fe-agent/AGENT.md:1-97` |
| `opal/agents/opal-be-agent/AGENT.md` | BE 전문 에이전트 | ❌ 금지(TASK 제약) | `opal/agents/opal-be-agent/AGENT.md:1-97` |
| `opal/agents/opal-db-agent/AGENT.md` | DB 전문 에이전트 | ❌ 금지(TASK 제약) | `opal/agents/opal-db-agent/AGENT.md:1-103` |
| `opal/agents/opal-task-agent/AGENT.md` | 범용 에이전트 | ❌ 금지(TASK 제약) | `opal/agents/opal-task-agent/AGENT.md:1-63` |
| `opal/agents/opal-task-action-agent/AGENT.md` | 127 태스크 범위 | ❌ 금지(127 충돌) | - |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 127 태스크 범위 | ❌ 금지(127 충돌) | - |

### 현재 상태

**op-dev-execute 스킬 구조**:
- `SKILL.md` v1.3이 페르소나 선택 로직(L22-37), 단순/복잡 모드 동작, FE 역할 분담 테이블(L130-175), FE/BE 활용 MCP 테이블(L178-194), PLAN.md 기반 실행(L196-209)을 모두 보유
- `references/execute-guide.md` v1.1이 금지 행동·보안·PLAN.md §4 읽기 규칙을 공통으로 다루되, L64-67에 FE ui-designer 분기 포함
- `personas/frontend-engineer.md`, `personas/backend-engineer.md`가 각 16줄 소형 원칙·행동 규칙 기재
- 워커는 현재 무조건 `execute-guide.md` + FE/BE에 따라 페르소나 1개를 Read

**오케스트레이터 EXECUTE 단계**:
- `opal-pilot-dev-short/SKILL.md:62-66` (STEP 3): `op-dev-execute 워커 디스패치` 한 줄 — agent 필드 순회 없음
- `opal-pilot-dev/SKILL.md:79-106` (STEP 4): 디스패치 프롬프트 블록만 존재 — agent 필드 순회 없음
- `opal-pilot-dev-wireframe/SKILL.md:61-80` (STEP 3): `스킬: op-dev-execute, checklist_source: wireframe.md` — wireframe.md 기반, PLAN.md §4.2 미사용
- `opal-pilot-sdd/SKILL.md:183-232` (Phase 4): `opal-sdd-action-agent` 단일 디스패치 경유, ACT 단위. agent의 EXECUTE 단계 내부는 `opal-task-agent` 고정 (AGENT.md:103-129)

**op-dev-plan의 agent 필드 배정 규칙**:
- v2.2(117)에서 `§4.2 실행 체크리스트` Step에 `영역`·`agent` 필드가 추가됨 (`opal/skills/op-dev-plan/SKILL.md:268-283`)
- 영역 → 기본 agent 매핑: FE→opal-fe-agent, BE→opal-be-agent, DB→opal-db-agent, 환경/배치/공통→opal-task-agent (`opal/skills/op-dev-plan/SKILL.md:376-385`)

**전문 에이전트(opal-fe-agent/be/db) 구조**:
- 실행 프로세스가 "스킬 SKILL.md Read → 페르소나 Read → references/ Read → 프로세스 수행" 공통 골격
- FE 페르소나는 에이전트 자체에서 `personas/frontend-engineer.md` Read (에이전트 레벨) + 스킬의 페르소나 블록도 동일 경로 Read (중복)
- FE 에이전트는 MCP/스킬 활용 테이블(shadcn MCP, context7, ui-designer 등)을 AGENT.md:52-64에 보유 — 스킬의 L178-194와 중복

**범용 에이전트(opal-task-agent)**:
- AGENT.md:12-27에 "스킬 SKILL.md Read → personas/ → references/ → 프로세스" 공통 프로세스. FE/BE 분기는 스킬 내부에 위임.

**127 충돌 회피 경계**:
- 127 TASK.md는 `opal-task-action-agent/AGENT.md`, `opal-pilot-project-dev/SKILL.md`를 수정 대상으로 명시 — 129는 두 파일 수정 금지
- 127은 oppd Phase 3의 `action_domain` 라우팅을 다루며, oppd→opal-task-action-agent→op-dev-* 경유 라우팅이 대상. oppd는 129 분배 디스패치 범위에서 제외됨 (TASK §3)

### 영향 범위

**직접 영향 (수정 파일)**:
1. op-dev-execute SKILL.md — Minor 구조 재편(§페르소나 삭제, FE 역할·MCP 테이블 이관, "실행 가이드 선택" 섹션 신설)
2. execute-guide.md — FE ui-designer 분기 제거 → specialist-guide로 이관
3. 신규 references/execute-specialist-guide.md
4. 신규 references/execute-generalist-guide.md
5. opds STEP 3 — 분배 디스패치 절차 추가 + 디스패치 프롬프트 확장
6. opd STEP 4 — 동 (디스패치 프롬프트 블록 내부 확장)
7. opdw STEP 3 — FE 단일 라우팅(opal-fe-agent)으로 지정 + 근거 명시 (와이어프레임 전용 흐름은 분배 미적용)

**간접 영향**:
- PLAN.md §4.2 agent 필드 기반 디스패치 활성화 → FE Step은 opal-fe-agent로 라우팅되어 페르소나·MCP 활용이 에이전트 AGENT.md를 1차 기준으로 삼음(중복 제거 효과)
- oppd(opal-pilot-project-dev)는 127 범위 — 129는 스킬 구획화만으로 자동 혜택(opal-task-action-agent가 전문 에이전트를 호출하면 에이전트가 SKILL.md 매핑 테이블로 specialist-guide 선택)
- opsdd(opal-pilot-sdd)는 opal-sdd-action-agent 경유 — 현재 AGENT.md:103-129가 `opal-task-agent`를 EXECUTE에 고정. 매핑 테이블은 agent 이름에 따라 generalist-guide로 자동 폴백되므로 **동작 호환**

**하위 호환성**:
- agent 필드 없는 PLAN.md(v2.0 이전) — 워커가 자기 이름을 알 수 없더라도, 스킬 매핑 테이블의 "기타/미지정" 행이 generalist-guide + opal-task-agent로 폴백되어 동작 유지
- execution-plan.json 기반 과거 태스크 — execute-guide.md의 과거 태스크 폴백 규칙 유지, 영향 없음

**배포 경계**:
- 모든 변경은 `opal/skills/`·`opal/agents/` 소스 경로에서 수행 ([MUST] `.opal/AGENT.md` §확정 기준 #2)
- `~/.opal/` 배포는 캡틴이 `install-mac.sh`로 별도 수행 — 129 범위 밖

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/skills/op-dev-execute/references/execute-specialist-guide.md` | 전문 에이전트(opal-fe/be/db-agent)용 지침 — 페르소나 처리·Scope·도메인 도구·FE 전문 케이스·영역 침범 방지 | TASK R-3 AC (a~e 5항목), 확정 방향 §1 |
| N-2 | `opal/skills/op-dev-execute/references/execute-generalist-guide.md` | 범용 에이전트(opal-task-agent)용 지침 — 페르소나 선택·Scope·FE 역할 분담·FE/BE MCP 테이블 | TASK R-4 AC (a~d 4항목), 확정 방향 §1 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/skills/op-dev-execute/SKILL.md` | (a) "실행 컨텍스트" 갱신 — 매핑 기반 guide 선택 흐름 명시 (b) "페르소나" 섹션(L22-37) 제거 (c) "Step 1 실행 가이드 로딩" → "Step 1 실행 가이드 선택" 섹션으로 재작성 + 매핑 테이블 삽입 (d) "FE 역할 분담"(L130-175)·"활용 스킬/MCP"(L178-194) 섹션 제거 (e) "PLAN.md 기반 실행" 섹션(L196-209) 축약 — FE 세부는 specialist-guide로 이관 (f) 변경이력 v2.0 추가 | TASK R-1 AC, 확정 방향 §1·§2 |
| M-2 | `opal/skills/op-dev-execute/references/execute-guide.md` | (a) "PLAN.md 기반 실행" L64-67 FE ui-designer 분기 제거 → specialist-guide·generalist-guide로 이관 (b) "FE/BE 침범 금지" 같은 공통 가드레일은 유지 (c) 변경이력 v1.2 추가 | TASK R-2 AC, 확정 방향 §1 |
| M-3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 3 EXECUTE에 "PLAN.md §4.2 agent 필드 순회 → 영역별 Step 묶음 → Phase 순서 분배 디스패치" 절차 추가. 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 추가. agent 필드 없는 PLAN.md 폴백(opal-task-agent 단일) 명시. 변경이력 v3.1 추가 | TASK R-5 AC, 확정 방향 §3 |
| M-4 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 4 EXECUTE에 동일 분배 디스패치 절차 추가. 디스패치 프롬프트 확장(담당 Step·Scope 제한). FE/BE 병렬 섹션은 agent 필드 기반으로 일반화. 변경이력 v3.2 추가 | TASK R-6 AC, 확정 방향 §3 |
| M-5 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | STEP 3 EXECUTE에 "UI 단일 FE 라우팅" 절차 명시 — wireframe.md 기반이므로 PLAN.md §4.2 agent 필드 순회 없음. 기본 에이전트를 `opal-fe-agent`로 지정 + 근거 명시(와이어프레임 전용 흐름). 변경이력 v2.2 추가 | TASK R-7 AC (근거 기재 대안), 확정 방향 §3 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | - | 삭제 대상 없음 (기존 personas/ 유지, 기존 파일 내 섹션 이관만 수행) |

#### 변경 없음 (근거 기재)

| # | 파일 경로 | 근거 |
|---|----------|------|
| U-1 | `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 4 EXECUTE-LOOP가 `opal-sdd-action-agent` 단일 디스패치(ACT 단위) 경유 — PM이 직접 op-dev-execute를 디스패치하지 않음. opal-sdd-action-agent 내부(AGENT.md:103-129)가 `opal-task-agent`로 op-dev-execute를 고정 호출하지만, 129 제약상 agent AGENT.md 수정 금지. SKILL.md 매핑 테이블이 agent 이름(opal-task-agent)을 `generalist-guide` 폴백으로 해석하므로 동작 정합. opal-sdd-action-agent의 전문 에이전트 라우팅은 127 패턴 연장선(별도 태스크) |
| U-2 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | SDD 루프는 ACT 단위 실행이며 TS 매핑 기반. PLAN.md §4.2 agent 필드 분배 대상 아님(ACT.md는 op-sdd-action-plan이 생성). op-dev-execute의 SKILL.md 매핑이 자동 적용되므로 가이드 변경 불필요 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 공통 가이드 정비 (FE 분기 제거) | `execute-guide.md` (M-2) | 낮음 |
| 2 | 전문 에이전트 가이드 신규 작성 | `execute-specialist-guide.md` (N-1) | 중간 |
| 3 | 범용 에이전트 가이드 신규 작성 (기존 SKILL.md 내용 이관) | `execute-generalist-guide.md` (N-2) | 중간 |
| 4 | op-dev-execute SKILL.md 재편 (매핑 테이블 + 섹션 정리) | `op-dev-execute/SKILL.md` (M-1) | 중간 |
| 5 | opds STEP 3 분배 디스패치 절차 추가 | `opal-pilot-dev-short/SKILL.md` (M-3) | 중간 |
| 6 | opd STEP 4 분배 디스패치 절차 추가 | `opal-pilot-dev/SKILL.md` (M-4) | 중간 |
| 7 | opdw STEP 3 FE 단일 라우팅 + 근거 명시 | `opal-pilot-dev-wireframe/SKILL.md` (M-5) | 낮음 |

> 원칙: **하위 레이어(가이드 파일) 먼저 → 상위 레이어(SKILL.md) → 오케스트레이터** 순. 신규 references/ 파일이 선행되어야 op-dev-execute SKILL.md의 매핑 테이블 참조 대상이 존재.

### 핵심 설계

#### M-1. op-dev-execute/SKILL.md 재편

**version**: v1.3 → **v2.0** (Major — 구조 전환).

> [MUST] `docs/CONVENTIONS.md` §변경이력: "버전: semver(`vX.Y.Z`)". 114 태스크에서 op-dev-plan v1.1→v2.0(기능 중심 구조 전면 개편) 선례를 따라, 3구획 분리라는 구조 전환은 Major 버전으로 기재.

**주요 섹션 변경**:

1. **프론트매터**: `name`/`description`/`version` 유지. description에 "에이전트 이름 기반 매핑으로 specialist/generalist 가이드를 자동 선택" 한 줄 추가 (→ D-17 §YAML Frontmatter).

2. **"실행 컨텍스트" 섹션 갱신** (기존 L12-20):
   - 실행 주체 문구에 "에이전트 이름 → 매핑 테이블 → 실행 가이드 자동 선택" 흐름 명시
   - 폴백 규칙: "agent 필드 없음 / 미지정 에이전트 → generalist 가이드"

3. **"페르소나" 섹션 제거** (기존 L22-37):
   - 이관처: specialist는 "에이전트 AGENT.md의 페르소나 우선" 문구만 execute-specialist-guide.md로, generalist는 `personas/frontend-engineer.md`·`backend-engineer.md` 동적 Read 절차를 execute-generalist-guide.md로
   - SKILL.md에는 "페르소나 처리는 선택된 가이드(specialist/generalist)에 위임한다" 한 줄로 치환

4. **"프로세스 — Step 1 실행 가이드 로딩" 재작성** (기존 L41-47):
   - 제목을 "Step 1. 실행 가이드 선택 및 로딩"으로 변경
   - 매핑 테이블 삽입 (확정 방향 §2의 3행 그대로):

     ```markdown
     | 에이전트 | Read 대상 |
     |---------|---------|
     | opal-fe-agent, opal-be-agent, opal-db-agent | references/execute-guide.md + references/execute-specialist-guide.md |
     | opal-task-agent (범용) | references/execute-guide.md + references/execute-generalist-guide.md |
     | 기타 / 미지정 | references/execute-guide.md + references/execute-generalist-guide.md (폴백) |
     ```

   - 워커 자기 판단 절차: "본 에이전트 이름을 확인 → 매핑 테이블 조회 → 두 파일 Read" 3단계 명시

5. **"Step 2 체크리스트 확인"·"Step 3 코드 작성 및 검증"·"Step 3-H @header"·"Step 4 체크리스트 갱신"·"Step 5 QA 체크리스트 검증" 유지** (기존 L49-89)

6. **"가드레일", "실행 모드" 섹션 유지** (기존 L91-128) — 공통 가드레일로 간주

7. **"FE 역할 분담: ui-designer vs op-dev-execute" 섹션 제거** (기존 L130-175):
   - 이관처: execute-generalist-guide.md (범용 에이전트는 자체적으로 FE/BE 분기 필요)
   - specialist 에이전트는 AGENT.md의 "금지 규칙" 및 ui-designer MCP 테이블이 이미 있으므로 execute-specialist-guide.md에는 "FE 전문 케이스 — ui-designer 연동 지점"만 간결히 기재

8. **"활용 스킬/MCP (FE)"·"활용 MCP (BE)" 섹션 제거** (기존 L177-194):
   - 이관처: execute-generalist-guide.md (범용 에이전트가 스킬 내부에서 참조)
   - specialist 에이전트는 AGENT.md MCP/스킬 활용 테이블을 1차 기준으로 삼으므로 중복 제거

9. **"PLAN.md 기반 실행" 섹션 축약** (기존 L196-209):
   - 공통 규칙(Phase 그룹핑·의존 순서)만 남기고 FE 세부 순서(비UI→UI→통합)는 execute-generalist-guide.md로 이관
   - specialist용 FE ui-designer 연동 조건은 execute-specialist-guide.md에 인용

10. **"블로커 처리", "결과 반환", "EXECUTE 품질 체크리스트" 유지** (기존 L211-248)

11. **변경이력 추가**:

    ```markdown
    | v2.0 | 2026-04-22 HH:mm | 3구획 구조 전환 — references/ 에 execute-specialist-guide.md / execute-generalist-guide.md 신설, SKILL.md에 에이전트 이름 매핑 테이블 삽입, 페르소나/FE 역할 분담/FE·BE MCP 테이블 섹션을 범용 가이드로 이관, 실행 컨텍스트·Step 1·PLAN.md 기반 실행 섹션 재작성 (129) |
    ```

    > [MUST] `docs/CONVENTIONS.md` §변경이력: "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)". 실제 시각은 EXECUTE 시점 타임스탬프로 채운다.

#### M-2. references/execute-guide.md 정비

**version**: v1.1 → **v1.2** (Minor — 분기 제거).

**주요 변경**:

1. **PLAN.md 기반 실행 L64-67** (FE ui-designer 분기) **제거**:
   - 치환 문구: "FE Step 중 ui-designer 연동이 필요한 경우는 **선택된 실행 가이드**(specialist 또는 generalist)의 FE 절차를 따른다"
2. **나머지 섹션(금지 행동·보안 가드레일·실행 모드별 동작·체크리스트 갱신·블로커·동적 스킬·품질 체크리스트) 유지** — 모든 워커 공통
3. **변경이력 추가**:

   ```markdown
   | v1.2 | 2026-04-22 HH:mm | FE ui-designer 분기(L64-67) 제거 → specialist/generalist 가이드로 위임. 나머지 공통 규칙 유지 (129) |
   ```

#### N-1. execute-specialist-guide.md 신규 작성

**대상 워커**: opal-fe-agent, opal-be-agent, opal-db-agent

**필수 섹션** (TASK R-3 AC a~e 커버):

```markdown
# EXECUTE 전문 에이전트 가이드

> 대상: opal-fe-agent / opal-be-agent / opal-db-agent
> 사전 로드: references/execute-guide.md (공통 규칙)

## 1. 페르소나 처리
- 전문 에이전트는 **AGENT.md에 정의된 페르소나를 1차 기준**으로 삼는다.
- 스킬의 `personas/` 폴더는 **Read하지 않는다**(AGENT.md가 이미 같은 페르소나를 Read함 — 중복 방지).
- 예: opal-fe-agent는 AGENT.md §페르소나가 `personas/frontend-engineer.md`를 Read하므로 스킬 레벨 재Read 불요.

## 2. Scope
- 오케스트레이터 디스패치 프롬프트의 **담당 Step** 필드에 명시된 Step만 수행한다.
- 다른 영역(FE 에이전트 ← BE 파일 등)으로 **침범하지 않는다** — AGENT.md §금지 규칙이 1차 기준.
- PLAN.md §4.2의 자신에게 배정된 Step의 `agent` 필드가 자기 에이전트 이름과 일치하는지 확인 후 실행.

## 3. 도메인 도구 / MCP / 스킬
- **AGENT.md의 "MCP/스킬 활용" 테이블을 1차 참조**한다.
  - opal-fe-agent: shadcn MCP, context7, ui-designer, vercel-labs 스킬
  - opal-be-agent: context7, sequential-thinking
  - opal-db-agent: context7 (ORM/마이그레이션)
- 스킬 SKILL.md의 MCP 목록은 중복이므로 **보조 참조**로만 사용한다.

## 4. FE 전문 케이스 (opal-fe-agent 전용)
- UI 구현이 담당 Step에 포함된 경우:
  - PLAN.md §3.N.2의 `##### 화면: {화면명}` 서브섹션을 Read
  - `ui-designer` 스킬 plan-driven 모드로 전달 (탐색 경로: `{프로젝트}/.opal/skills/ui-designer/SKILL.md` → `~/.opal/skills/ui-designer/SKILL.md`)
- 비UI FE 작업(API 연동·상태 관리·타입 정의 등)은 FE 에이전트가 직접 수행.
- ui-designer 연동 판단 기준: PLAN.md의 해당 F-NNN에 `##### 화면:` 서브섹션이 존재하면 UI 구현 판정.

## 5. 영역 침범 방지
- **1차 기준**: 자신의 AGENT.md §금지 규칙 (예: opal-fe-agent는 `backend/`·`api/` 수정 금지).
- **공통 가드레일**: `references/execute-guide.md` §절대 금지 #3 "다른 영역 침범 금지"를 함께 준수.
- 담당 Step 외 파일을 수정해야 할 경우 즉시 블로커 보고 → PM이 Step 재할당.

## 6. 결과 반환
- `changed_files`는 자신의 영역(FE/BE/DB) 파일만 포함 — 침범 감지 시 블로커.
- 나머지 반환 규약은 AGENT.md §결과 반환 형식 및 execute-guide.md §결과 반환과 동일.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-22 HH:mm | 초기 작성 — 전문 에이전트 EXECUTE 지침 분리 (129) |
```

> [MUST] `.opal/AGENT.md` §금지사항: "스킬/에이전트 YAML frontmatter 임의 삭제 금지". 이 파일은 references/이므로 frontmatter 없음(스킬 본체만 해당).

#### N-2. execute-generalist-guide.md 신규 작성

**대상 워커**: opal-task-agent 및 기타/미지정 (폴백)

**필수 섹션** (TASK R-4 AC a~d 커버):

```markdown
# EXECUTE 범용 에이전트 가이드

> 대상: opal-task-agent (범용) / 기타·미지정 에이전트 (폴백)
> 사전 로드: references/execute-guide.md (공통 규칙)

## 1. 페르소나 처리 (FE/BE/공통 분기)

범용 에이전트는 작업 유형에 따라 페르소나를 **동적 Read**한다:

- **FE 작업** (PLAN.md §4.2 Step의 `영역: FE` 또는 파일 경로상 FE 판정 시):
  `opal/skills/op-dev-execute/personas/frontend-engineer.md` Read
- **BE 작업** (`영역: BE`):
  `opal/skills/op-dev-execute/personas/backend-engineer.md` Read
- **공통/환경/배치/문서 작업**: 페르소나 Read 불필요 — 범용 원칙만 적용

페르소나 파일이 없으면 아래 내장 역할을 따른다:
- FE: 시니어 프론트엔드 엔지니어 (React, shadcn/ui, 접근성 중시)
- BE: 시니어 백엔드 엔지니어 (API 설계, 데이터 모델링, 보안 중시)

## 2. Scope
- 단일 워커가 **디스패치 범위 전체를 순차 처리**한다.
- PLAN.md §4.2 Step을 Phase 그룹핑 → 의존 순서 준수 → 전체 완료까지 수행.
- 다중 영역(FE+BE) 혼합 Step도 동일 워커 내부에서 순차 처리.

## 3. FE 역할 분담 — ui-designer vs op-dev-execute

FE 태스크에서 UI 구현과 비UI 작업을 명확히 구분한다.

### ui-designer 담당 (UI 구현)
shadcn/ui + React 컴포넌트 전문. 화면에 보이는 것을 만드는 작업.

| 작업 | 예시 |
|------|------|
| 페이지 레이아웃 | 전체 화면 구조, 헤더/사이드바/콘텐츠 배치 |
| UI 컴포넌트 구현 | 버튼, 폼, 테이블, 카드, 다이얼로그 등 |
| shadcn 컴포넌트 조합 | shadcn MCP 조회 → 설치 → 조합 |
| 스타일링 | Tailwind CSS, 반응형 레이아웃 |
| 인터랙션 UI | 탭, 아코디언, 드롭다운, 모달 등 |
| 폼 UI | 입력 필드, 유효성 표시, 에러 메시지 표시 |

**호출 방법**: PLAN.md §3.N.2 `##### 화면: {화면명}` 서브섹션을 Read하여 ui-designer plan-driven 모드 입력으로 전달.

탐색 경로: `{프로젝트}/.opal/skills/ui-designer/SKILL.md` → `~/.opal/skills/ui-designer/SKILL.md`

### op-dev-execute 담당 (비UI FE 작업)
화면 뒤에서 동작하는 것.

| 작업 | 예시 |
|------|------|
| API 연동 | fetch/axios, API 클라이언트, 에러 처리 |
| 상태 관리 | zustand, context, React Query 설정 |
| 라우팅 설정 | Next.js app router, 페이지 구조 |
| 타입 정의 | TypeScript 인터페이스, OpenAPI 타입 생성 |
| 유틸리티 | 헬퍼 함수, 포맷터, 밸리데이터 |
| 환경 설정 | .env, 빌드 설정, 패키지 설치 |
| 인증/인가 로직 | 토큰 관리, 가드, 미들웨어 |

### 실행 순서 (FE 태스크)

PLAN.md §4 실행 체크리스트 기반:

1. 비UI 작업 먼저 (op-dev-execute): 라우팅·타입 정의·API 클라이언트·상태 관리
2. UI 구현 (ui-designer): PLAN.md §3.N.2 FE 화면 설계 섹션을 ui-designer plan-driven 모드 입력으로 전달
3. 통합 (op-dev-execute): API 연결·이벤트 핸들러 바인딩·최종 조립
4. 각 Step 완료 후 QA 체크리스트 검증

## 4. 활용 스킬/MCP

### FE
| 스킬/MCP | 담당 | 용도 |
|----------|------|------|
| **ui-designer** (plan-driven) | UI 구현 | 화면 레이아웃 + shadcn 컴포넌트 구현 |
| shadcn MCP | UI 구현 | 컴포넌트 검색·조회·설치 (ui-designer가 사용) |
| vercel-labs/shadcn | UI 구현 | shadcn Critical Rules, 폼/레이아웃 패턴 |
| vercel-labs/react-best-practices | 비UI | React 패턴 (상태 관리, 훅 등) |
| vercel-labs/next-best-practices | 비UI | Next.js 패턴 (라우팅, RSC 등) |
| vercel-labs/composition-patterns | 공통 | 컴포넌트 조합 패턴 |
| anthropics/frontend-design | 공통 | FE 아키텍처/UX 설계 참조 |
| context7 | 비UI | 라이브러리 문서 조회 |

### BE
| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | 라이브러리 문서 조회 (Python, Flutter, Kotlin, Go 등) | 외부 라이브러리 API 확인 시 |

## 5. 공통 규칙 참조
금지 행동·보안 가드레일·블로커 처리·결과 반환은 **references/execute-guide.md**를 따른다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-22 HH:mm | 초기 작성 — 범용 에이전트 EXECUTE 지침 분리 (기존 SKILL.md L22-37 페르소나, L130-175 FE 역할, L178-194 MCP 이관) (129) |
```

#### M-3. opal-pilot-dev-short/SKILL.md (opds) STEP 3 EXECUTE 분배 디스패치

**version**: v3.0 → **v3.1** (Minor — EXECUTE 절차 확장).

**기존 (L62-66)**:
```
op-dev-execute 워커 디스패치. **model**: standard. checklist_source: PLAN.md 섹션 "3. 실행 체크리스트". execution-plan.json 있으면 전달.
```

**치환**:

```markdown
## STEP 3: EXECUTE

### 3-1. 분배 디스패치 절차 (v3.1 신설)

1. **PLAN.md §4.2 실행 체크리스트 Read** — 각 Step의 `영역`·`agent` 필드를 확인한다.
2. **영역별 Step 묶음 생성** — 동일 agent(opal-fe-agent, opal-be-agent, opal-db-agent, opal-task-agent)가 배정된 Step을 하나의 배치로 묶는다.
3. **Phase 순서 순회** — PLAN.md §4.1 Phase 그룹핑에 따라 Phase별로:
   - Phase 내 독립 배치가 복수면 Agent 도구 병렬 호출
   - 순차 의존이 있으면 순차 호출
4. **각 배치마다 워커 디스패치** — 해당 agent로 op-dev-execute 워커 디스패치 (model: standard).
5. **폴백** — PLAN.md §4.2에 agent 필드가 없거나 "미지정"인 경우 `opal-task-agent` 단일 디스패치로 PLAN 전체를 처리한다.

### 3-2. 디스패치 프롬프트

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{태스크명}/
**checklist_source**: {PLAN.md 경로}, 섹션: 4.2 실행 체크리스트
**담당 Step**: {이 워커가 처리할 Step 번호 목록 — 예: 3, 5, 7}
**Scope 제한**: {agent 영역 — FE / BE / DB / 공통}. 영역 외 파일 수정 시 즉시 블로커 보고.
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}
```

> **에이전트별 자동 가이드 선택**: 워커는 op-dev-execute/SKILL.md의 매핑 테이블에 따라 자기 에이전트 이름으로 execute-specialist-guide.md 또는 execute-generalist-guide.md를 자동 Read한다. PM이 `applied_guide` 파라미터를 주입하지 않는다.

### 3-3. EXECUTE 완료 후
모든 배치 완료 → changed_files 병합 → **State Gate** → **TEST 단계 진입**.
```

**변경이력 추가**:
```markdown
| v3.1 | 2026-04-22 HH:mm | STEP 3 EXECUTE에 PLAN.md §4.2 agent 필드 기반 분배 디스패치 절차 추가 — 영역별 Step 묶음·Phase 순서 순회·담당 Step/Scope 제한 필드 추가·agent 필드 없음 폴백 규칙 명시 (129) |
```

#### M-4. opal-pilot-dev/SKILL.md (opd) STEP 4 EXECUTE 분배 디스패치

**version**: v3.1 → **v3.2** (Minor — EXECUTE 절차 확장).

**M-3과 동일 패턴 적용** — 기존 STEP 4 EXECUTE 블록(L79-106) 내부의 디스패치 프롬프트를 아래로 교체:

- 섹션 이름: "STEP 4: EXECUTE" 유지. 내부에 "4-1. 분배 디스패치 절차", "4-2. 디스패치 프롬프트", "4-3. FE/BE 병렬" 하위 구조 도입
- FE/BE 병렬 섹션(L97-100)을 agent 필드 기반 일반화로 재작성 — `execution-plan.json` 기반 기존 서술은 폴백으로 유지
- 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 추가 (M-3 §3-2 동일)
- "자동 가이드 선택" 안내 문구 추가

**변경이력 추가**:
```markdown
| v3.2 | 2026-04-22 HH:mm | STEP 4 EXECUTE에 PLAN.md §4.2 agent 필드 기반 분배 디스패치 절차 추가 — FE/BE 병렬 섹션 agent 필드 기반 일반화·담당 Step/Scope 제한 필드 추가·execution-plan.json 폴백 유지 (129) |
```

#### M-5. opal-pilot-dev-wireframe/SKILL.md (opdw) STEP 3 EXECUTE 단일 라우팅

**version**: v2.1 → **v2.2** (Minor — 라우팅 명시).

**근거 (TASK R-7 AC 대안 기재)**:
- opdw의 EXECUTE는 **wireframe.md**를 checklist_source로 사용 (`opal/skills/opal-pilot-dev-wireframe/SKILL.md:64`).
- wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 존재하지 않는다 (op-dev-wireframe은 wireframe.md만 작성).
- 따라서 **Step별 분배 디스패치는 적용 대상이 아니다**.
- 대신, 와이어프레임 UI 구현은 본질적으로 FE 작업이므로 **단일 FE 라우팅**(opal-fe-agent)으로 지정하여 ui-designer 연동·페르소나·shadcn MCP 등을 활성화한다.

**치환 내용** (STEP 3의 "스킬: op-dev-execute, checklist_source: wireframe.md" 블록):

```markdown
## STEP 3: EXECUTE (UI 구현)

### 3-1. 라우팅 결정 (v2.2 신설)

와이어프레임 파이프라인의 EXECUTE는 **FE 단일 라우팅**을 사용한다 (분배 디스패치 대상 아님).

- **기본 에이전트**: `opal-fe-agent` (FE 전문)
- **근거**: wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 없다(op-dev-wireframe 산출물). 와이어프레임 구현은 본질적으로 FE 작업이므로 UI 전문 에이전트를 직접 지정한다.
- **폴백**: `opal-fe-agent` 사용 불가 플랫폼이면 `opal-task-agent`로 디스패치 (op-dev-execute/SKILL.md 매핑에 따라 generalist-guide로 폴백).

### 3-2. 디스패치 프롬프트

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
(기존 §EXECUTE 완료 후 절차 유지)
```

**변경이력 추가**:
```markdown
| v2.2 | 2026-04-22 HH:mm | STEP 3 EXECUTE를 FE 단일 라우팅(opal-fe-agent)으로 지정 — 와이어프레임 전용 흐름상 PLAN.md §4.2 분배 디스패치 미적용 근거 명시, 디스패치 프롬프트에 담당 Step/Scope 제한 필드 추가 (129) |
```

#### U-1, U-2. opsdd / execute-loop-guide 변경 없음 (근거)

- **opsdd Phase 4 EXECUTE-LOOP**는 ACT 단위로 `opal-sdd-action-agent` 단일 디스패치 (`opal/skills/opal-pilot-sdd/SKILL.md:183-232`). PM이 직접 op-dev-execute를 디스패치하지 않는다.
- **opal-sdd-action-agent 내부 3단계 EXECUTE**는 `opal-task-agent`로 op-dev-execute 호출을 고정 (`opal/agents/opal-sdd-action-agent/AGENT.md:103-129`). 129 제약상 에이전트 AGENT.md 수정 금지(TASK §제약 조건 + [MUST] `.opal/AGENT.md` §확정 기준 #2에 따른 소스 수정 원칙은 유효하나, 129의 요구사항 R-1~R-8은 에이전트 AGENT.md를 수정 대상에서 제외).
- op-dev-execute/SKILL.md의 에이전트 이름 매핑 테이블은 `opal-task-agent → generalist-guide`로 자동 폴백하므로 **동작 정합**하다. SDD ACT 단위 실행은 PLAN.md §4.2 agent 필드 구조와 다른 체계(ACT 내부에서 op-sdd-action-plan이 자체 PLAN.md를 생성)이므로 분배 디스패치 범위 밖이다.
- **opal-sdd-action-agent의 전문 에이전트 라우팅은 127 패턴의 연장선** — 별도 태스크로 다룰 수 있으나 129 범위 아님(TASK §배경 분석 §4, oppd와 동일 이유).

따라서 **R-8은 "변경 없음 + PLAN.md에 근거 명시"로 확정**(TASK R-7/R-8 AC 대안 조항).

> [MUST] `tasks/129-.../TASK.md` §제약 조건: "127 진행 중 태스크와의 충돌 회피 — `opal-task-action-agent/AGENT.md`와 `opal-pilot-project-dev/SKILL.md`는 127 태스크 범위이므로 이번 태스크에서 수정하지 않는다".

---

## 3. 실행 체크리스트

> 총 8개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | 공통 가이드 정비 — 다른 파일의 참조 기반 |
> | 2 | 2, 3 | 병렬 | 신규 references/ 두 파일 (독립) |
> | 3 | 4 | 순차 | op-dev-execute SKILL.md — Phase 2 가이드가 필요 |
> | 4 | 5, 6, 7 | 병렬 | 오케스트레이터 3종 (독립 파일) |
> | 5 | 8 | 순차 | QA 검증용 변경이력 최종 확인 |

### Step 1: execute-guide.md 정비 (FE 분기 제거)

- [x] 완료
- **파일**: `opal/skills/op-dev-execute/references/execute-guide.md`
- **작업 내용**:
  - §PLAN.md 기반 실행의 L64-67 (FE ui-designer 분기 4번 항목)을 "FE Step 중 ui-designer 연동이 필요한 경우는 선택된 실행 가이드(specialist 또는 generalist)의 FE 절차를 따른다"로 치환
  - 변경이력 v1.2 행 추가 (일시 `2026-04-22 HH:mm` KST)
- **완료 기준**: FE 전용 분기 문구가 제거되고, specialist/generalist 위임 문구가 삽입되었다. 공통 규칙(금지 행동·보안·모드·체크리스트·블로커·결과 반환·품질 체크리스트)은 그대로 남는다. 변경이력 테이블에 v1.2 행이 추가되어 있다.
- **테스트**: Grep으로 `ui-designer`·`§3.N.2` 문자열이 execute-guide.md에 남아있는지 확인 → 치환 후 문구 1회(위임 문구)만 존재해야 한다.
- **의존**: 없음

### Step 2: execute-specialist-guide.md 신규 작성

- [x] 완료
- **파일**: `opal/skills/op-dev-execute/references/execute-specialist-guide.md` (신규)
- **작업 내용**:
  - 파일 신규 생성. 상단에 "대상: opal-fe-agent / opal-be-agent / opal-db-agent" 한 줄
  - 섹션: §1 페르소나 처리 (AGENT.md 우선, `personas/` 불요) / §2 Scope (담당 Step 한정) / §3 도메인 도구 (AGENT.md MCP 테이블 1차) / §4 FE 전문 케이스 (ui-designer 연동 조건) / §5 영역 침범 방지 (AGENT.md §금지 규칙 + execute-guide.md §절대 금지 #3) / §6 결과 반환
  - 변경이력 v1.0 행 추가
- **완료 기준**: TASK R-3 AC의 5개 항목(a~e)이 모두 §1~§5에 포함되어 있다. 변경이력 행이 있다.
- **테스트**: Grep으로 `페르소나`·`Scope`·`도메인 도구`·`ui-designer`·`영역 침범` 5개 키워드 모두 출현 확인.
- **의존**: 없음 (Step 1과 독립 — 병렬 가능)

### Step 3: execute-generalist-guide.md 신규 작성

- [x] 완료
- **파일**: `opal/skills/op-dev-execute/references/execute-generalist-guide.md` (신규)
- **작업 내용**:
  - 파일 신규 생성. 상단에 "대상: opal-task-agent (범용) / 기타·미지정 에이전트 (폴백)" 한 줄
  - 섹션: §1 페르소나 처리 (FE/BE/공통 분기, `personas/` 동적 Read) / §2 Scope (단일 워커 순차) / §3 FE 역할 분담 (ui-designer vs op-dev-execute 테이블 이관 — 기존 SKILL.md L130-175) / §4 활용 스킬/MCP (기존 SKILL.md L178-194 FE·BE 테이블 이관) / §5 공통 규칙 참조 (execute-guide.md로 위임)
  - 변경이력 v1.0 행 추가
- **완료 기준**: TASK R-4 AC의 4개 항목(a~d)이 §1~§4에 포함되고, §5에서 execute-guide.md 참조가 명시되어 있다. 기존 SKILL.md의 L22-37·L130-175·L178-194 내용이 누락 없이 이관되었다.
- **테스트**:
  1. Grep으로 `frontend-engineer.md`·`backend-engineer.md`·`ui-designer`·`shadcn MCP`·`context7`·`vercel-labs` 키워드 모두 출현 확인
  2. 기존 SKILL.md와 교차 검증 (이관 누락 여부)
- **의존**: 없음 (Step 1·Step 2와 독립 — 병렬 가능)

### Step 4: op-dev-execute/SKILL.md 재편 (v2.0)

- [x] 완료
- **파일**: `opal/skills/op-dev-execute/SKILL.md`
- **작업 내용**:
  - frontmatter `version: 1.2` → `version: 2.0`. description에 "에이전트 이름 매핑으로 specialist/generalist 가이드를 자동 선택" 한 줄 추가
  - "실행 컨텍스트" 섹션에 매핑 기반 선택 흐름 한 줄 추가
  - "페르소나" 섹션(L22-37) **제거**
  - "프로세스 — Step 1 실행 가이드 로딩"을 "Step 1. 실행 가이드 선택 및 로딩"으로 재작성 + 매핑 테이블(3행) 삽입
  - "FE 역할 분담: ui-designer vs op-dev-execute" 섹션(L130-175) **제거**
  - "활용 스킬/MCP (FE)"·"활용 MCP (BE)" 섹션(L178-194) **제거**
  - "PLAN.md 기반 실행" 섹션 축약 — FE 세부 순서 문구(L203-207) 제거 (generalist-guide로 이관됨)
  - 변경이력 v2.0 행 추가
- **완료 기준**:
  - frontmatter version이 2.0이다
  - 매핑 테이블이 §2(확정 방향)과 글자 그대로 일치한다 (3행: specialist / generalist / 기타 폴백)
  - 제거 대상 3개 섹션이 모두 제거되었다
  - 잔여 공통 섹션(가드레일·실행 모드·블로커·결과 반환·품질 체크리스트·Step 3-H @header)은 보존되었다
  - 변경이력 테이블에 v2.0 행이 있다
- **테스트**:
  1. Grep으로 `personas/frontend-engineer`·`FE 역할 분담`·`활용 스킬/MCP (FE)` 문자열이 SKILL.md에서 제거되었는지 확인
  2. "매핑 테이블" 섹션에 3개 에이전트 그룹이 모두 명시되어 있는지 확인
  3. references/ 신규 파일 경로 2개가 모두 참조되는지 확인
- **의존**: Step 1, Step 2, Step 3 (신규 references 파일이 선행)

### Step 5: opal-pilot-dev-short/SKILL.md (opds) STEP 3 분배 디스패치

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**:
  - STEP 3 EXECUTE 섹션(L62-66)을 "3-1 분배 디스패치 절차 / 3-2 디스패치 프롬프트 / 3-3 EXECUTE 완료 후"로 재구성
  - 3-1: PLAN.md §4.2 agent 필드 순회 4단계(Read → 묶음 → Phase 순회 → 디스패치) + 폴백 규칙(agent 없음 → opal-task-agent 단일)
  - 3-2: 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 추가
  - 3-3: 기존 "changed_files 반환 → State Gate → TEST 진입" 흐름 유지
  - "에이전트별 자동 가이드 선택" 안내 문구 추가
  - 변경이력 v3.1 행 추가
- **완료 기준**:
  - STEP 3에 3-1/3-2/3-3 세 하위 섹션이 있다
  - 디스패치 프롬프트 예시에 `담당 Step`·`Scope 제한` 필드가 포함된다
  - agent 필드 없음 폴백이 명시되어 있다
  - 변경이력 v3.1 행이 있다
- **테스트**: Grep으로 `agent 필드`·`담당 Step`·`Scope 제한`·`폴백` 키워드 출현 확인. 변경이력 최상단 행이 v3.1인지 확인.
- **의존**: Step 4 (op-dev-execute SKILL.md 매핑 테이블 참조 필요)

### Step 6: opal-pilot-dev/SKILL.md (opd) STEP 4 분배 디스패치

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  - STEP 4 EXECUTE 섹션(L79-106)을 "4-1 분배 디스패치 절차 / 4-2 디스패치 프롬프트 / 4-3 FE/BE 병렬(폴백) / 4-4 EXECUTE 완료 후"로 재구성
  - 4-1: M-3와 동일 4단계 + 폴백
  - 4-2: 기존 디스패치 프롬프트 블록에 `담당 Step`·`Scope 제한` 필드 추가
  - 4-3: 기존 "FE/BE 병렬 (execution-plan.json 존재 시)" 문구를 agent 필드 기반 일반화로 재작성, execution-plan.json 폴백 유지
  - 4-4: 기존 "EXECUTE 완료 후" 흐름 유지
  - "에이전트별 자동 가이드 선택" 안내 문구 추가
  - 변경이력 v3.2 행 추가
- **완료 기준**:
  - STEP 4에 4-1/4-2/4-3/4-4 네 하위 섹션이 있다
  - 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 포함
  - FE/BE 병렬 섹션이 agent 필드 기반으로 재작성됨
  - 변경이력 v3.2 행이 있다
- **테스트**: Grep으로 `agent 필드`·`담당 Step`·`Scope 제한`·`execution-plan.json 폴백` 키워드 확인.
- **의존**: Step 4 (Step 5와 병렬 가능 — 독립 파일)

### Step 7: opal-pilot-dev-wireframe/SKILL.md (opdw) STEP 3 FE 단일 라우팅

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**:
  - STEP 3 EXECUTE 섹션(L61-80)을 "3-1 라우팅 결정 / 3-2 디스패치 프롬프트 / 3-3 완료 후"로 재구성
  - 3-1: FE 단일 라우팅 근거 명시(wireframe.md 기반, PLAN.md §4.2 없음) + 기본 에이전트 `opal-fe-agent` + 폴백 `opal-task-agent`
  - 3-2: 디스패치 프롬프트에 `담당 Step: wireframe.md 전체 (분배 없음)`, `Scope 제한: FE 영역` 필드 추가
  - 3-3: 기존 "완료 후" 흐름 유지 (op-dev-qa → State Gate → PM Gate)
  - "에이전트별 자동 가이드 선택" 안내 문구 추가
  - 변경이력 v2.2 행 추가
- **완료 기준**:
  - STEP 3에 3-1/3-2/3-3 세 하위 섹션이 있다
  - 3-1에 "와이어프레임 전용 흐름상 분배 디스패치 미적용" 근거가 명시되어 있다
  - 기본 에이전트가 `opal-fe-agent`로 지정되어 있다
  - 변경이력 v2.2 행이 있다
- **테스트**: Grep으로 `opal-fe-agent`·`와이어프레임 전용`·`분배 디스패치 미적용`·`폴백` 키워드 확인.
- **의존**: Step 4 (Step 5, 6과 병렬 가능 — 독립 파일)

### Step 8: 변경이력 최종 검증 (R-9)

- [x] 완료
- **파일**: 수정된 전체 (M-1 ~ M-5, N-1 ~ N-2 총 7개 파일)
- **작업 내용**:
  - 7개 파일 각각의 변경이력 테이블을 Read하여 아래 항목 확인:
    - 일시 형식이 `YYYY-MM-DD HH:mm` KST 기준인가 ([MUST] `docs/CONVENTIONS.md` §변경이력)
    - (129) 참조가 포함되어 있는가
    - 버전이 예상대로(v2.0/v1.2/v3.1/v3.2/v2.2/v1.0/v1.0)인가
  - 누락/오류 발견 시 수정
- **완료 기준**: 7개 파일의 변경이력이 일관되게 갱신되어 있고, (129) 참조와 KST 일시가 모두 포함되어 있다.
- **테스트**: Grep으로 `(129)` 카운트 = 7 (최소 1회/파일).
- **의존**: Step 1~7 전체

---

## 4. QA 체크리스트

### 기능 테스트

- [x] **R-1**: op-dev-execute/SKILL.md에 "실행 가이드 선택" 섹션이 있고, 매핑 테이블 3행(specialist / generalist / 기타 폴백)이 TASK §2와 글자 그대로 일치한다
- [x] **R-1**: 기존 "페르소나"·"FE 역할 분담"·"활용 스킬/MCP" 섹션이 SKILL.md에서 **제거**되었고, references로 이관되었다
- [x] **R-2**: execute-guide.md에 FE 전용 절차(ui-designer 분기)가 남아있지 않다. 모든 워커가 Read해도 충돌 없는 공통 내용만 포함한다
- [x] **R-3**: execute-specialist-guide.md에 (a) 페르소나 처리 (b) Scope (c) 도메인 도구 (d) FE 전문 케이스 (e) 영역 침범 방지 5개 항목이 모두 있다
- [x] **R-4**: execute-generalist-guide.md에 (a) 페르소나 처리 (b) Scope (c) FE 역할 분담 (d) 활용 스킬/MCP 4개 항목이 모두 있고, 공통 규칙은 execute-guide.md로 위임 명시
- [x] **R-5**: opds STEP 3 EXECUTE에 (a) PLAN.md §4.2 agent 필드 순회 (b) 영역별 Step 묶음 (c) Phase 순서 분배 디스패치 절차가 명시되어 있다. 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 포함
- [x] **R-6**: opd STEP 4 EXECUTE에 동일 절차가 명시되어 있다. 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 포함. execution-plan.json 폴백 유지
- [x] **R-7**: opdw STEP 3 EXECUTE에 FE 단일 라우팅(opal-fe-agent)이 지정되고, 와이어프레임 전용 흐름상 PLAN.md §4.2 분배 디스패치 미적용 근거가 명시되어 있다
- [x] **R-8**: opsdd/execute-loop-guide는 변경 없음 — PLAN.md에 근거가 명시되어 있다(U-1, U-2 항목)
- [x] **R-9**: 7개 수정/신규 파일 모두 변경이력에 (129) 참조와 KST 일시가 기재되어 있다

### 일관성 테스트

- [x] 매핑 테이블의 에이전트 이름(opal-fe-agent / opal-be-agent / opal-db-agent / opal-task-agent)이 실제 존재하는 에이전트 폴더와 일치한다 (`opal/agents/` 하위 디렉토리 확인)
- [x] execute-specialist-guide.md가 언급하는 AGENT.md §금지 규칙·§MCP 테이블이 실제 4개 에이전트 AGENT.md에 존재한다 (수정 금지 대상이지만 **참조 정합성** 확인)
- [x] execute-generalist-guide.md로 이관된 FE 역할 분담·MCP 테이블이 **누락/중복 없이** 옮겨졌다 (기존 SKILL.md L130-175 / L178-194와 1:1 대조)
- [x] opds/opd/opdw의 변경이력 버전 증가 규칙이 semver(`vX.Y.Z`)를 따른다 ([MUST] `docs/CONVENTIONS.md` §변경이력)
- [x] 127 범위 파일(opal-task-action-agent/AGENT.md, opal-pilot-project-dev/SKILL.md) 및 에이전트 AGENT.md 4종(opal-fe/be/db/task-agent)이 **변경되지 않았다**
- [x] op-dev-execute/SKILL.md의 frontmatter `name` / `description` 키가 유지되고 `version`만 업데이트되었다 ([MUST] `.opal/AGENT.md` §금지사항: "스킬/에이전트 YAML frontmatter 임의 삭제 금지")
- [x] 과거 태스크 호환 — agent 필드 없는 PLAN.md가 들어오면 opds/opd STEP의 폴백 규칙(opal-task-agent 단일 디스패치 → generalist-guide 자동 선택)이 작동한다 (문서 흐름 검증)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따른다
- [x] kebab-case 파일/폴더 네이밍을 따른다 (`execute-specialist-guide.md`, `execute-generalist-guide.md`)
- [x] 모든 신규/수정 파일의 변경이력 일시가 `YYYY-MM-DD HH:mm` KST 포맷이다
- [x] 매핑 테이블이 마크다운 테이블 형식으로 올바르게 렌더링된다
- [ ] 인라인 인용(`(→ D-N §N)`, `` `경로:줄번호` ``)이 citation-rules.md §2 포맷을 따른다

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 FE 역할 분담·MCP 테이블 이관 시 누락 | 범용 에이전트가 FE 세부 가이드를 잃어 품질 저하 | Step 3 완료 기준에 "기존 SKILL.md L130-175 / L178-194와 1:1 대조" 명시. QA 일관성 테스트에서 재확인 |
| 매핑 테이블 에이전트 이름 오타 | 워커가 guide 선택 실패 → 폴백만 동작 | frontmatter·실제 에이전트 폴더명과 정확히 대조. QA 일관성 테스트 항목으로 검증 |
| opsdd가 장기적으로 전문 에이전트 라우팅 필요 | SDD 태스크에서 FE/BE 자동 라우팅 미적용 | **129 범위 밖** — U-1/U-2 근거 명시로 마감. 별도 태스크(127 패턴 확장)로 포괄 |
| 127 충돌 — 동일 타임존에 oppd 관련 파일 수정 | 병렬 태스크 간 충돌 | TASK §제약 조건 및 PLAN U-1 근거에 따라 129는 127 범위 파일(opal-task-action-agent/AGENT.md, opal-pilot-project-dev/SKILL.md) 수정 금지. QA 일관성 테스트 항목으로 확인 |
| 에이전트 AGENT.md 수정 필요성 재발견 | R-5~R-7 AC 미충족 우려 | TASK §확정된 설계 방향 §4 "에이전트 AGENT.md는 수정 불필요"를 근거로 유지. 필요 시 별도 태스크 제안 |
| v1.3 → v2.0 버전 점프 타당성 | Minor vs Major 경계 논란 | [MUST] `docs/CONVENTIONS.md` §변경이력 + 114 선례(op-dev-plan v1.1→v2.0)에 근거. Major = 구조 전환(파일 분리·워커 자기 판단 방식 도입) 기준 적용 |
| wireframe.md 기반 EXECUTE가 향후 PLAN.md §4.2 구조로 전환될 가능성 | opdw 라우팅 규칙 재설계 필요 | 현재 opdw R-7은 "근거 기재" 대안으로 처리. 구조 전환 시 별도 태스크로 M-5 재작성 |
| `applied_guide` 도입 재요청 | B안 자기 판단에서 A안 명시 주입으로 회귀 논의 | TASK §확정된 설계 방향 §2 "applied_guide 파라미터는 도입하지 않는다" 고정. 변경 요청 시 PM/소유자 승인 필요 |

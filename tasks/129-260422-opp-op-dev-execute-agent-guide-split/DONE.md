# DONE: op-dev-execute 에이전트별 지침 구획화 + EXECUTE 디스패치 라우팅 전파

> 완료일: 2026-04-23 12:31 KST | 모드: Project Task (opp, interactive) | 작업 유형: 개선

## 완료 요약

`op-dev-execute` 스킬을 **공통(execute-guide) / 전문(execute-specialist-guide) / 범용(execute-generalist-guide)** 3구획으로 분리하고, SKILL.md에 **에이전트 이름 기반 매핑 테이블**을 삽입하여 워커가 자기 판단으로 가이드를 자동 선택하도록 전환(B안). PM이 직접 디스패치하는 오케스트레이터 3종(opds/opd/opdw)의 EXECUTE 단계에 PLAN.md §4.2 agent 필드 기반 분배 디스패치 절차를 추가. opsdd 및 oppd는 라우팅 구조상 변경 없이 스킬 구획화 혜택을 자동으로 받으므로 범위에서 제외(U-1/U-2 및 127 충돌 회피).

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/skills/op-dev-execute/SKILL.md` | v1.3 → **v2.0 (Major)** — frontmatter version 상승, "실행 가이드 선택" 섹션 신설 + 에이전트 매핑 테이블 3행 삽입, "페르소나"(구 L22-37) · "FE 역할 분담"(구 L130-175) · "활용 스킬/MCP (FE)·(BE)"(구 L178-194) 섹션 제거 → references/로 이관, "실행 컨텍스트" · "PLAN.md 기반 실행" 섹션 재작성 |
| 2 | `opal/skills/op-dev-execute/references/execute-guide.md` | v1.1 → v1.2 — FE ui-designer 분기(구 L64-67) 제거, specialist/generalist 위임 문구로 치환 |
| 3 | `opal/skills/op-dev-execute/references/execute-specialist-guide.md` | **신규 v1.0** — 전문 에이전트(opal-fe/be/db-agent) 지침. §1 페르소나(AGENT.md 우선) / §2 Scope / §3 도메인 도구 / §4 FE 전문 케이스 / §5 영역 침범 방지 / §6 결과 반환 |
| 4 | `opal/skills/op-dev-execute/references/execute-generalist-guide.md` | **신규 v1.0** — 범용 에이전트(opal-task-agent) 지침. §1 페르소나 동적 Read / §2 Scope / §3 FE 역할 분담 / §4 활용 스킬·MCP / §5 공통 규칙 참조. 기존 SKILL.md L22-37 · L130-175 · L178-194 1:1 이관 |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | v3.0 → v3.1 — STEP 3 EXECUTE를 3-1/3-2/3-3 하위 구조로 재구성, 분배 디스패치 4단계 + 폴백 명시, 디스패치 프롬프트에 `담당 Step`·`Scope 제한` 필드 추가 |
| 6 | `opal/skills/opal-pilot-dev/SKILL.md` | v3.1 → v3.2 — STEP 4 EXECUTE를 4-1/4-2/4-3/4-4 하위 구조로 재구성, FE/BE 병렬 섹션을 agent 필드 기반 일반화, execution-plan.json 폴백 유지 |
| 7 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | v2.1 → v2.2 — STEP 3 EXECUTE를 3-1/3-2/3-3 하위 구조로 재구성, FE 단일 라우팅(`opal-fe-agent`) + 폴백 지정, 와이어프레임 전용 흐름상 분배 디스패치 미적용 근거 명시 |

## 핵심 변경 사항

### Before

- `op-dev-execute/SKILL.md` 단일 파일이 공통 규칙 + 페르소나 선택 + FE 역할 분담 + FE/BE MCP 테이블을 모두 보유 → 전문 에이전트(opal-fe-agent 등)가 스킬 Read 시 AGENT.md와 **중복·충돌 발생**
- opds/opd EXECUTE 단계는 `op-dev-execute 워커 디스패치` 한 줄만 지시 → PM이 기본 워커(opal-task-agent)로 단일 디스패치 → **PLAN.md §4.2 agent 필드가 실질적으로 무시됨** → 범용 에이전트가 모든 Step을 혼자 수행하여 전문 에이전트의 페르소나·ui-designer 연동·도메인 MCP가 활성화되지 않음
- opdw EXECUTE도 단일 디스패치 구조로 FE 전문 경로 미활용

### After

- `op-dev-execute/SKILL.md` 매핑 테이블이 워커 에이전트 이름으로 Read 대상을 자동 결정:
  - `opal-fe-agent` / `opal-be-agent` / `opal-db-agent` → `execute-guide.md` + `execute-specialist-guide.md`
  - `opal-task-agent` → `execute-guide.md` + `execute-generalist-guide.md`
  - 기타·미지정 → generalist 폴백
- opds/opd EXECUTE에 "PLAN.md §4.2 agent 필드 순회 → 영역별 Step 묶음 → Phase 순서 분배 디스패치" 4단계 절차 + `담당 Step`·`Scope 제한` 디스패치 필드 추가 → 전문 에이전트가 자기 영역 Step만 수행하며 페르소나·도메인 도구 자동 활성
- opdw는 wireframe.md 기반이라 PLAN.md §4.2 부재 → FE 단일 라우팅(`opal-fe-agent`)으로 지정 + 근거 명시
- 에이전트 AGENT.md 4종 수정 없음 — 기존 "스킬 SKILL.md Read" 프로세스가 그대로 매핑 테이블을 해석

### 하위 호환성

- agent 필드 없는 PLAN.md(v2.0 이전) → opds/opd STEP의 `폴백` 규칙(`opal-task-agent` 단일 디스패치)으로 진입 → SKILL.md 매핑의 "기타/미지정" 행이 generalist-guide로 자동 선택 → 기존 동작 유지

## 테스트 결과

| 단계 | QA 판정 | 비고 |
|------|---------|------|
| PLAN | **Pass** (Critical 0 / Warning 1 / Info 1) | Warning 즉시 조치(Phase 카운트 표기 수정), Info(§4 QA R-N 추적성) 수용 |
| EXECUTE | **Pass** (Critical 0 / Warning 1 / Info 0) | Warning(타임스탬프 날짜) — KST 도구 반환값과 일치하여 수용 |

PM Gate(git status 실측):
- 수정 5 + 신규 2 파일 PLAN §1 테이블과 일치
- 보호 대상(127 범위 2종 + 에이전트 AGENT.md 4종 + opsdd 2종) 전부 미변경
- 7개 파일 변경이력에 `(129)` 참조 + `YYYY-MM-DD HH:mm` KST 포맷 준수

## 산출물 목록

| 파일 | 설명 |
|------|------|
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/TASK.md` | 요구사항 정의 (R-1~R-9, 확정 설계 방향 §1~§4) |
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/PLAN.md` | 구현 계획 (8 Step / 5 Phase, M-1~M-5 + N-1~N-2 + U-1~U-2) |
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/QA-PLAN.md` | PLAN QA 리포트 (Pass) |
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/QA-EXECUTE.md` | EXECUTE QA 리포트 (Pass) |
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/STATE.md` | 상태 관리 + 의사결정 로그 (9건) |
| `tasks/129-260422-opp-op-dev-execute-agent-guide-split/DONE.md` | 완료 리포트 (이 파일) |

## 후속 작업 (이번 범위 밖)

- **127 완료 후 oppd 정합성 재점검**: `opal-task-action-agent`가 전문 에이전트(opal-fe/be-agent)로 라우팅할 때 매핑 테이블이 specialist-guide를 자동 선택하는지 실사용 검증
- **opsdd 전문 에이전트 라우팅**: `opal-sdd-action-agent`의 내부 `opal-task-agent` 고정을 action_domain 패턴(127)으로 확장하는 후속 태스크 검토
- **커밋·배포**: 캡틴 지시 시 수행 (하네스 Guards — 자동 커밋 금지, `install-mac.sh` 실행 금지)

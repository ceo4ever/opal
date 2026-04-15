---
@header
type: done
task: "117 전문 개발 에이전트 시스템 설계"
layer: task
---

# DONE: 117 specialist-agent-system

> 완료일: 2026-04-15 | 소요 단계: TASK → PLAN → EXECUTE
> 커밋: `1838b6f feat(117): 전문 에이전트(Specialist Agent) 체계 구축`

## 완료 요약

OPAL 프레임워크에 **도메인 전문 에이전트(Specialist Agent) 체계**를 도입했다. 범용 `opal-task-agent` 하나에 의존하던 워커 구조를, 도메인/역할별 전문 에이전트 6종으로 분화하고, PM이 단계+도메인에 따라 적합한 에이전트를 선택·라우팅하는 구조로 전환했다.

## 신규 생성 (6종 전문 에이전트)

| 에이전트 | 역할 | persona |
|---------|------|---------|
| `opal-fe-agent` | FE 구현 (React, shadcn/ui, Tailwind) | frontend-engineer.md |
| `opal-be-agent` | BE 구현 (API 설계, OWASP, 레이어 구조) | backend-engineer.md |
| `opal-plan-agent` | PLAN 설계 (advanced 고정, 에이전트 라우팅) | software-architect.md |
| `opal-test-agent` | 테스트 (BE/FE/E2E 모드, 기존 op-dev-test-agent 리네이밍+강화) | test-engineer.md |
| `opal-planning-agent` | 서비스 기획 (opwt 파이프라인) | service-planner.md |
| `opal-db-agent` | DB 모델 설계+구현 (개념/논리/물리, DBML, 표준사전) | db-architect.md |

> 각 에이전트에 `personas/` 분리 + `code-scan` 자체 탐색 절차 3단계 내장.

## 주요 변경 파일

| 파일 | 핵심 변경 |
|------|----------|
| `opal/core/references/agents.md` | 전문 에이전트 매핑 테이블 + 폴백 규칙 + 추가 가이드 |
| `opal/core/references/opal-pm.md` | §3 Step 0/6/7, §4 영역 침범+인터페이스 체크, §5 자기 개선, §6 컨텍스트 주입, §10 통합 조율, §11 프로젝트 에이전트 관리 신설 |
| `opal/skills/op-dev-plan/SKILL.md` + `plan-guide.md` | Step 형식에 `영역`+`agent` 필드 + docs/ 갱신 Step 자동 생성 규칙 |
| `opal/skills/op-dev-{analysis,execute}/SKILL.md` | 실행 주체 "전문 에이전트 또는 opal-task-agent (폴백)" 표기 |
| `opal/skills/op-task-execute/SKILL.md` | 실행 주체 갱신 (범용 EXECUTE도 전문 에이전트 라우팅 수용) |
| `scripts/install-mac.sh` | 에이전트 소스 이원화 (`opal/agents/` + `agents/`) |
| `docs/CONVENTIONS.md` | 에이전트 소스 경로 규칙(`opal/agents/`), 전문 에이전트 네이밍 체계 |
| `docs/ARCHITECTURE.md` | 서브에이전트 다이어그램에 전문 에이전트 추가 |

## 디렉토리 재구성

| 변경 | 전 | 후 |
|------|---|---|
| 이동 | `agents/opal-task-agent/` | `opal/agents/opal-task-agent/` |
| 이동 | `agents/opal-task-qa-agent/` | `opal/agents/opal-task-qa-agent/` |
| 이동+리네이밍 | `agents/op-dev-test-agent/` | `opal/agents/opal-test-agent/` (내용 강화) |
| 이동+참조 갱신 | `agents/opal-task-action-agent/` | `opal/agents/opal-task-action-agent/` |
| 유지 | `agents/wtm-agent/` | `agents/wtm-agent/` (OPAL 무관 범용) |

## 검증 결과

| 항목 | 결과 |
|------|------|
| 신규 생성 N1~N6 (6개 AGENT.md + 6개 persona) | ✅ 모두 존재 확인 |
| 수정 M1~M15 (15개 파일) | ✅ 커밋 diff에 모두 포함 |
| 삭제/이동 D1~D3 (agents/ 하위 4종) | ✅ agents/에 wtm-agent만 잔존 |
| 커밋 반영 | ✅ 1838b6f (main 브랜치, origin/main 대비 +2) |
| 총 변경 규모 | 32개 파일, +3,297줄 / −120줄 |

## 적용된 요구사항

- R-1: 전문 에이전트 6종 신규 생성 ✅
- R-2: PM 프로세스(opal-pm.md) 전문 에이전트 선택/라우팅 로직 추가 ✅
- R-3: op-dev-plan SKILL에 `영역`+`agent` 필드 도입 ✅
- R-4: EXECUTE/ANALYSIS/TEST-SCENARIO/범용 EXECUTE 실행 주체 갱신 ✅
- R-5: OPAL 전용 에이전트를 `opal/agents/`로 집결 + wtm-agent 분리 ✅
- R-6: install-mac.sh 에이전트 소스 이원화 ✅
- R-7: docs/CONVENTIONS.md / ARCHITECTURE.md 갱신 ✅

## 후속 액션 (권장)

1. README.md 업데이트 — 전문 에이전트 체계를 아키텍처 개요에 반영
2. 116 폴더 정리 — Template+Factory 초안(orphan) 처리 방향 결정
3. 프로젝트별 전문 에이전트 상속 가이드 (opal-pm.md §11) 실사용 피드백 수집

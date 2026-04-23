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
| v1.0 | 2026-04-23 11:39 | 초기 작성 — 전문 에이전트 EXECUTE 지침 분리 (129) |

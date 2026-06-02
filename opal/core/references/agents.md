# OPAL Agents Registry

OPAL 에이전트가 호출할 수 있는 서브에이전트 목록.
각 에이전트는 독립 컨텍스트에서 실행되며, 호출 시 해당 AGENT.md(또는 SKILL.md)를 Read로 읽어 지시를 전달한다.

## opal-pilot 에이전트

opal-pilot 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe, opal-pilot-project)가 호출하는 서브에이전트.

### opal-task-agent

- **역할**: 범용 워커 — 오케스트레이터가 전달한 단계 스킬(op-task-plan, op-task-execute, op-dev-analysis, op-dev-plan 등)의 SKILL.md를 Read하고 프로세스를 따라 산출물 생성
- **호출 시점**: 각 단계 시작 시 오케스트레이터가 디스패치
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨벤션
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **참고**: opal-pilot-project에서는 op-task-plan(advanced), op-task-execute(standard)을 사용

### opal-task-qa-agent

- **역할**: 범용 QA 워커 — 오케스트레이터가 전달한 qa_skill(op-dev-qa 또는 op-task-qa)의 SKILL.md를 Read하고 산출물 품질 검증
- **호출 시점**: 단계 완료 후 QA Gate에서 오케스트레이터가 디스패치
- **입력**: qa_skill, 검증 대상 산출물 경로, 단계명, TASK.md 경로
- **출력**: QA-{단계}.md 리뷰 문서

### opal-test-agent

- **역할**: Test 에이전트 — TEST-SCENARIO.md 기반 동적 검증 (테스트 실행 + 결과 채움 + 판정), BE/FE/E2E 3가지 모드 지원
- **호출 시점**: EXECUTE 완료 후 오케스트레이터가 호출
- **단계**: TEST
- **영역**: 공통
- **model**: standard
- **자체 로드 문서**: `docs/ARCHITECTURE.md` (테스트 섹션), 테스트 모드에 따라 도메인 문서 선택 로드
- **입력**: scenario_path, changed_files, mode(full-simple/full-complex/short), test_mode(be/fe/e2e)
- **출력**: TEST-SCENARIO.md (결과 채움 + 판정)
- **에이전트 경로**: `opal/agents/opal-test-agent/`

### opal-task-action-agent

- **역할**: 액션 에이전트 — oppd Phase 3에서 개별 액션을 자율 실행 (PLAN → QA → EXECUTE → 검증 루핑 → TEST)
- **호출 시점**: oppd Phase 3에서 액션 실행 시 디스패치
- **입력**: action_id, action_goal, action_scope, verify_commands, task_folder, project_context
- **출력**: 액션 결과 (status, verdict, verification_log, changed_files, failure_context)

## opal-pilot-gc 서브에이전트

`opal-pilot-gc`(opgc) 경량 Pilot이 **CHECK 단계에서 병렬 디스패치**하는 서브에이전트. 각 에이전트는 독립 컨텍스트에서 실행되어 **자기완결 보고서**(체크리스트 내장, 5단계 상태 모델)를 생성한다.

### opal-security-checker

- **역할**: 코드 보안 체크 전담 — OWASP Top 10 (2021) / CWE Top 25 / SANS Top 25 기준의 Base 원칙 강제 적용 + `docs/SECURITY.md`가 있으면 병합하여 시크릿·인증/인가·입력 검증·의존성·로깅·암호화·설정을 점검. 부재 시 초안 생성을 유도(opi 재사용)
- **호출 시점**: opal-pilot-gc의 CHECK 단계 (병렬)
- **단계**: CHECK (opal-pilot-gc 내부 단계)
- **영역**: 보안
- **model**: advanced
- **자체 로드 문서**: `~/.opal/skills/opal-pilot-gc/references/base-security-checklist.md`, `~/.opal/skills/opal-pilot-gc/references/report-security-template.md`, `docs/SECURITY.md`(허브, 있는 경우 — 허브+링크 체이닝), 커뮤니티 스킬 래핑(`openai/security-best-practices`)
- **입력**: 대상 파일 목록, 범위(`staged`/`all`), 기술 스택 감지 결과, `docs/SECURITY.md` 경로(있는 경우), `scope`(`frontend`/`backend`/`batch`/`mobile`/`all` — 선택, 허브+링크 상세 문서 매칭용)
- **출력**: `GC-SECURITY-{타임스탬프}[-{element}].md` — 체크리스트 내장 자기완결 보고서 (요약 지표 + 5단계 상태 + 카테고리/심각도/Base vs 프로젝트 출처 + 문서 업데이트 제안). 진단 전담이므로 `changed_files`에 소스 파일 포함 금지(보고서만)
- **에이전트 경로**: `opal/agents/opal-security-checker/`

### opal-convention-checker

- **역할**: 코드 컨벤션 체크 전담 — 프로젝트 `docs/CONVENTIONS.md`를 **유일 기준**으로 네이밍·들여쓰기·파일 구조·죽은 코드·미사용 import·문서화 규칙을 점검. 문서 부재 시 초안 생성을 유도(opi 재사용). **프레임워크 내장 공통 기본값 없음**
- **호출 시점**: opal-pilot-gc의 CHECK 단계 (병렬)
- **단계**: CHECK (opal-pilot-gc 내부 단계)
- **영역**: 컨벤션
- **model**: standard
- **자체 로드 문서**: `docs/CONVENTIONS.md`(허브, 필수 — 부재 시 초안 유도. 허브+링크 체이닝), `~/.opal/skills/opal-pilot-gc/references/base-convention-checklist.md`, `~/.opal/skills/opal-pilot-gc/references/report-convention-template.md`
- **입력**: 대상 파일 목록, 범위(`staged`/`all`), `docs/CONVENTIONS.md` 경로, `scope`(`frontend`/`backend`/`batch`/`mobile`/`all` — 선택, 허브+링크 상세 문서 매칭용)
- **출력**: `GC-CONVENTION-{타임스탬프}[-{element}].md` — 체크리스트 내장 자기완결 보고서. 진단 전담이므로 `changed_files`에 소스 파일 포함 금지(보고서만)
- **에이전트 경로**: `opal/agents/opal-convention-checker/`

## 전문 에이전트 (Specialist)

PM이 PLAN.md의 단계+영역 조합으로 직접 디스패치하는 전문 워커 에이전트.
각 에이전트는 해당 도메인의 전문 지식과 자체 로드 문서를 보유하며, 범용 opal-task-agent 대신 투입된다.

### opal-plan-agent

- **역할**: PLAN 단계 전문 워커 — 코드 분석 + 기능 중심 설계 + 테스트 시나리오 작성을 고품질로 수행. PM이 전달한 전문 에이전트 매핑 테이블을 참조하여 PLAN.md §4 실행 체크리스트의 각 Step에 agent 필드를 배정한다.
- **호출 시점**: PLAN 단계 시작 시 오케스트레이터가 디스패치
- **단계**: PLAN
- **영역**: 공통
- **model**: advanced (오버라이드 불가)
- **자체 로드 문서**: `docs/` 전체 (PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md, FRONTEND.md, BACKEND.md 및 하위 모든 도메인 문서)
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 전문 에이전트 매핑 테이블
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **에이전트 경로**: `opal/agents/opal-plan-agent/`

### opal-fe-agent

- **역할**: FE 전문 워커 — PM이 PLAN.md의 FE 영역 Step을 디스패치하면, 해당 단계 스킬을 Read하고 FE 전문 지식(React, shadcn/ui, Tailwind, 접근성, 반응형)으로 구현을 수행한다.
- **호출 시점**: EXECUTE 단계 FE 영역 Step 시작 시 오케스트레이터가 디스패치
- **단계**: EXECUTE
- **영역**: FE
- **model**: standard
- **자체 로드 문서**: `docs/FRONTEND.md`, `docs/CONVENTIONS.md` (FE 섹션) — BE 계층 문서 로드 제외
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨벤션
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **에이전트 경로**: `opal/agents/opal-fe-agent/`

### opal-be-agent

- **역할**: BE 전문 워커 — PM이 PLAN.md의 BE 영역 Step을 디스패치하면, 해당 단계 스킬을 Read하고 BE 전문 지식(RESTful API, OWASP, 레이어 구조, N+1 방지, 시크릿 관리)으로 구현을 수행한다.
- **호출 시점**: EXECUTE 단계 BE 영역 Step 시작 시 오케스트레이터가 디스패치
- **단계**: EXECUTE
- **영역**: BE
- **model**: standard
- **자체 로드 문서**: `docs/BACKEND.md`, `docs/BE-FRAMEWORK.md`, `docs/CONVENTIONS.md` (BE 섹션) — FE 전용 문서 로드 제외
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨벤션
- **출력**: 산출물(.md) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **에이전트 경로**: `opal/agents/opal-be-agent/`

### opal-db-agent

- **역할**: DB 모델링 전문 워커 — 서비스 기획서를 참고하여 데이터 모델링(개념/논리/물리)을 수행하고 마이그레이션 코드를 구현한다. PLAN 단계에서 DB 설계 산출물(MD, DBML), EXECUTE 단계에서 마이그레이션 코드(SQL)를 담당한다.
- **호출 시점**: PLAN(DB 설계) 또는 EXECUTE(마이그레이션 구현) 단계 DB 영역 Step 시작 시 오케스트레이터가 디스패치
- **단계**: PLAN, EXECUTE
- **영역**: DB
- **model**: standard
- **자체 로드 문서**: `docs/db/` 내 모든 .md 파일, `docs/db/schema.dbml`, 표준사전(엑셀 — PM이 경로 주입), `docs/SERVICE.md` / `docs/SPEC.md` / `docs/PRD.md` (참조용)
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 표준사전 경로(옵션)
- **출력**: 설계 문서(MD) + 스키마(DBML) 또는 마이그레이션 코드(SQL) + 결과 반환
- **에이전트 경로**: `opal/agents/opal-db-agent/`

### opal-planning-agent

- **역할**: 서비스 기획 전문 워커 — 서비스 초기 기획부터 기획서(PRD, TRD, 서비스 정책서, IA, 와이어프레임, WBS, 외부 API 명세서 등) 작성/수정/관리를 수행한다. opwt(opal-pilot-write-tech) 파이프라인의 EXECUTE 단계에서 투입된다.
- **호출 시점**: EXECUTE 단계 기획 영역 Step 시작 시 오케스트레이터가 디스패치
- **단계**: EXECUTE
- **영역**: 기획
- **model**: advanced (오버라이드 불가)
- **자체 로드 문서**: `docs/PROJECT.md`, 기존 기획 산출물 전체(PRD, TRD, 서비스 정책서, IA, 외부 API 명세서, 개발 WBS 등), 와이어프레임·ERD(오케스트레이터가 경로 명시 시)
- **입력**: 스킬 경로, 태스크 폴더, 이전 산출물, 대상 문서 유형
- **출력**: 기획 산출물(.md 또는 .xlsx) + 결과 반환 (artifact_path, summary, status, blockers, changed_files)
- **에이전트 경로**: `opal/agents/opal-planning-agent/`

## 전문 에이전트 매핑 테이블

PM이 단계+영역으로 에이전트를 선택하고, opal-plan-agent가 PLAN.md §4 실행 체크리스트의 agent 필드를 배정할 때 참조하는 테이블.

| 에이전트 | 단계 | 영역 | model | 자체 로드 문서 |
|----------|------|------|-------|--------------|
| opal-plan-agent | PLAN | 공통 | advanced | 전체 docs/ |
| opal-fe-agent | EXECUTE | FE | standard | FRONTEND.md, CONVENTIONS.md (FE) |
| opal-be-agent | EXECUTE | BE | standard | BACKEND.md, BE-FRAMEWORK.md, CONVENTIONS.md (BE) |
| opal-db-agent | PLAN, EXECUTE | DB | standard | DB 설계 문서, 표준사전(엑셀) |
| opal-planning-agent | EXECUTE | 기획 | advanced | 기획 산출물, 와이어프레임 등 |
| opal-test-agent | TEST | 공통 | standard | ARCHITECTURE.md (테스트 섹션) |
| opal-security-checker | CHECK (opgc) | 보안 | advanced | base-security-checklist, SECURITY.md (허브+링크 체이닝 — conventions-hub-model.md 참조) |
| opal-convention-checker | CHECK (opgc) | 컨벤션 | standard | CONVENTIONS.md, base-convention-checklist (허브+링크 체이닝 — conventions-hub-model.md 참조) |

## 플랫폼 sub-agent 어댑터 변환 규칙

OPAL 에이전트(`~/.opal/agents/{name}/AGENT.md`)를 각 AI 플랫폼의 sub-agent로 등록하기 위한 어댑터 변환 규칙이다.
`scripts/install-mac.sh`의 `install_{claude,cursor,gemini}_agents` 함수가 이 규칙을 참조한다.

### 플랫폼별 메커니즘 (2026-04 기준)

| 플랫폼 | 메커니즘 | 등록 경로 | 공식 문서 |
|--------|---------|----------|----------|
| Claude Code | 지원 | `~/.claude/agents/{name}.md` | [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents) |
| Cursor | 지원 (v2.4+) | `~/.cursor/agents/{name}.md` | [Cursor Subagents](https://cursor.com/docs/subagents) |
| Gemini CLI | 지원 | `~/.gemini/agents/{name}.md` | [Gemini CLI Subagents](https://geminicli.com/docs/core/subagents/) |
| Antigravity | **미지원** | (없음) | [Sub-agents 기능 요청](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) — 내부 팀 검토 중 |

### frontmatter 변환 규칙

OPAL frontmatter → 플랫폼 frontmatter:

| OPAL 필드 | Claude Code | Cursor | Gemini CLI |
|----------|------------|--------|-----------|
| `name` | `name` (그대로) | `name` (그대로) | `name` (그대로) |
| `description` | `description` (그대로) | `description` (그대로) | `description` (그대로) |
| `model: light` | `model: haiku` | `model: inherit` | `model: gemini-3.1-flash-lite` |
| `model: standard` | `model: sonnet` | `model: inherit` | `model: gemini-flash-latest` |
| `model: advanced` | `model: opus` | `model: inherit` | `model: gemini-pro-latest` |
| `icon` | (제거 — 미지원) | (제거 — 미지원) | (제거 — 미지원) |
| (기타 OPAL 전용 필드) | (제거) | (제거) | (제거) |

> Cursor는 사용자가 IDE에서 모델 제공자를 직접 설정하므로 `inherit`로 위임한다 (→ `opal/core/references/opal-model-mapping.md` §4 Cursor 특이사항).

> Cursor `inherit` 정책은 사용자 IDE 모델 설정 위임을 의미한다. Cursor가 향후 `light/standard/advanced` alias를 도입하면 본 표와 `scripts/install-mac.sh` `emit_platform_agent_adapter` 함수의 인라인 매핑을 동시 갱신해야 한다.

### 본문(System Prompt) 처리

OPAL `AGENT.md` 본문은 **변경 없이** 어댑터 markdown body로 그대로 복사된다.
어댑터 파일 상단에 `AUTO-GENERATED` 주석 헤더를 삽입하여 직접 편집을 가드한다 (편집은 `opal/agents/{name}/AGENT.md` 소스에서 수행).

### Antigravity 미지원 처리

Antigravity는 2026-04 기준 커스텀 sub-agent를 지원하지 않는다 ([공식 응답](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) — "feature request has been escalated to the relevant internal teams for review").
대안 메커니즘인 [Agent Skills](https://antigravity.google/docs/skills)는 SKILL.md 기반 지식 패키징 시스템이며 sub-agent 추상화와 다르므로, 본 태스크 범위에서 적용 제외한다.
향후 Antigravity가 sub-agent를 출시하면 `install_antigravity_agents()`를 추가하고 이 표를 갱신한다.

> 현재 Antigravity 사용 시 OPAL 부트스트래퍼는 `~/.gemini/GEMINI.md`(Antigravity가 Gemini CLI 호환 경로 사용)를 통해 동작하며, sub-agent 디스패치만 미지원이다.

## 폴백 규칙

1. agents.md에 전문 에이전트 섹션 없음 → 기존 방식 (opal-task-agent + PM 컨텍스트 주입)
2. 매핑 테이블에 해당 단계/영역 없음 → 해당 단계는 기존 방식
3. 매핑 있음 → 전문 에이전트 사용

## 탐색 경로

에이전트 파일 탐색 우선순위 (배포 후):

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

소스 경로 (개발):
- OPAL 전용: `opal/agents/{agent-name}/AGENT.md`
- 범용: `agents/{agent-name}/AGENT.md`

## web-to-markdown 에이전트

### opal-wtm-agent

- **역할**: web-to-markdown 스킬 워커 — Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) 폴백으로 단일 URL 또는 사용자 cmux surface(B/C 모드)를 마크다운으로 변환
- **호출 시점**: web-to-markdown 스킬에서 URL/surface별로 오케스트레이터가 디스패치
- **단계**: 도구성 워커 (파이프라인 단계 외)
- **영역**: 공통
- **model**: light
- **입력**: `url | --surface <handle> [url]`, `save_path`, `mode (full|clean|wireframe)`, `--wait <ms>` (기본 2000)
- **출력**: 마크다운 파일(`{save_path}/{slug}.md`) + JSON 결과 (총 8필드):
  ```json
  {
    "artifact_path": "...",
    "summary": "...",
    "status": "completed",
    "blockers": [],
    "changed_files": ["..."],
    "method": "cmux|webfetch|playwright-cli",
    "mode": "A|B|C|null",
    "user_owned": false
  }
  ```
- **에이전트 경로**: `opal/agents/opal-wtm-agent/`

## 에이전트 추가 가이드

### 프레임워크 에이전트 추가

1. `opal/agents/{agent-name}/AGENT.md` 작성
2. 이 파일(agents.md)의 해당 섹션 + 매핑 테이블에 등록
3. `install-mac.sh`로 배포

### 프로젝트 전문 에이전트 생성 (프레임워크 에이전트 확장)

기존 프레임워크 전문 에이전트를 프로젝트에 맞게 확장한다. PM이 생성/관리한다 (opal-pm.md §11 참조).

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md` 작성
2. frontmatter에 `extends: ~/.opal/agents/{agent-name}/AGENT.md` 명시
3. 본문에 "프레임워크 에이전트를 Read하고 따른다" + 프로젝트 전용 규칙(확정 기준, 추가 참조 문서, 추가 금지사항) 작성
4. 탐색 경로 우선순위로 자동 발견 (프로젝트 > 프레임워크)

프로젝트 에이전트 예시:
```markdown
---
name: opal-be-agent
extends: ~/.opal/agents/opal-be-agent/AGENT.md
project: mams
---

# opal-be-agent — mams 프로젝트 확장

## 프레임워크 에이전트 로드
`~/.opal/agents/opal-be-agent/AGENT.md`를 Read하고 따른다.

## 프로젝트 전용 규칙

### 확정 기준
- API 응답은 camelCase
- BaseRepository 반드시 상속
- 소프트 삭제 패턴 적용

### 추가 참조 문서
- docs/BE-FRAMEWORK.md

### 추가 금지사항
- raw SQL 금지
- user_no 하드코딩 금지
```

### 프로젝트 전용 에이전트 추가 (신규 에이전트)

프레임워크에 없는 프로젝트 전용 에이전트를 새로 만든다.

1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md` 작성
2. 매핑은 PM이 프로젝트 컨텍스트에서 판단
3. 탐색 경로 우선순위로 자동 발견

## 향후 추가 에이전트

새로운 에이전트 등록 시 아래 형식으로 추가:

```markdown
### {agent-name}

- **역할**: {한줄 설명}
- **호출 시점**: {언제 호출되는지}
- **단계**: {PLAN / EXECUTE / TEST / 공통}
- **영역**: {FE / BE / DB / 기획 / 공통}
- **model**: {advanced / standard / light}
- **자체 로드 문서**: {로드할 문서 목록}
- **입력**: {필요한 입력}
- **출력**: {생성하는 산출물}
- **에이전트 경로**: `opal/agents/{agent-name}/`
```

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-04-30 | 플랫폼 sub-agent 어댑터 변환 규칙 §추가 — Claude/Cursor/Gemini 4개 플랫폼 메커니즘 표 + frontmatter 변환 규칙 + Antigravity 미지원 처리 (133) |
| v1.2 | 2026-04-30 | emit_platform_agent_adapter description 평탄화 — Claude Code 파서 호환 (133) |
| v1.3 | 2026-04-30 | AUTO-GENERATED 헤더 검사 범위를 전체 파일로 확장 — frontmatter 외 헤더 위치 오탐지 결함 수정 (133) |
| v1.4 | 2026-05-12 21:35 KST | §wtm-agent → §opal-wtm-agent 갱신 — Phase 1(WebFetch)→Phase 2(cmux 조건부)→Phase 3(playwright-tool CLI) 폴백, 입력 `--surface` 3모드, 출력 JSON 8필드, 에이전트 경로 opal/agents/opal-wtm-agent/ (002) |
| v1.5 | 2026-06-02 20:16 KST | Gemini 변환 표 부동 별칭 전환 — light=`gemini-3.1-flash-lite` 핀, standard=`gemini-flash-latest`, advanced=`gemini-pro-latest` (011) |

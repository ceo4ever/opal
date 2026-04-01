# TEST SCENARIO: dtp-dev-full-agent + dtp-dev-short-agent → dtp-dev-agent 통합

> 작성일: 2026-03-21 | 상태: 작성 완료

## 시나리오 목록

**문서 전용 변경** — 마크다운 파일만 생성/삭제/수정. 코드 테스트 대상 없음.

### S-1: dtp-dev-agent/AGENT.md (Claude) 생성 및 내용 정합성

| 항목 | 내용 |
|------|------|
| 대상 | `agents/claude/dtp-dev-agent/AGENT.md` 신규 생성 및 내용 정합성 (Full+Short 통합) |
| 조건 | 기존 `dtp-dev-full-agent/AGENT.md` + `dtp-dev-short-agent/AGENT.md` 두 파일 존재 |
| 기대 결과 | 1. 파일이 생성되었는가? 2. YAML frontmatter에 `name: dtp-dev-agent`, `description` 포함? 3. "역할", "실행 프로세스", "단계별 가이드 매핑" (Full+Short 통합 테이블), "반환 형식", "실행 규칙 1~5번", "STATE.md 갱신" 섹션 포함? 4. "EXECUTE 단계 추가 규칙"에 Full(단순+복잡) + Short(EXECUTE-SHORT) 모두 포함? |
| 도구 | 파일 존재 + 내용 정합성 (마크다운 검증) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-2: dtp-dev-agent.md (Cursor) 생성 및 플랫폼 포맷 일관성

| 항목 | 내용 |
|------|------|
| 대상 | `agents/cursor/dtp-dev-agent.md` 신규 생성 (Cursor 플랫 파일 형식) |
| 조건 | 기존 `agents/cursor/dtp-dev-full-agent.md` + `dtp-dev-short-agent.md` 두 파일 존재 |
| 기대 결과 | 1. 파일이 생성되었는가? 2. Claude 버전과 동일한 내용 구조? 3. Cursor 플랫 파일 형식(마크다운 전문)? 4. YAML frontmatter 포함? |
| 도구 | 파일 존재 + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-3: dtp-dev-agent/SKILL.md (Antigravity) 생성 및 스킬 포맷 호환성

| 항목 | 내용 |
|------|------|
| 대상 | `agents/antigravity/dtp-dev-agent/SKILL.md` 신규 생성 (Antigravity 스킬 형식) |
| 조건 | 기존 `agents/antigravity/dtp-dev-full-agent/` + `dtp-dev-short-agent/` 두 디렉토리 존재 |
| 기대 결과 | 1. 디렉토리 + 파일이 생성되었는가? 2. Claude 버전과 동일한 내용 구조? 3. Antigravity SKILL.md 포맷(YAML frontmatter + 마크다운 본문)? 4. `name: dtp-dev-agent`, `type: agent` 포함? |
| 도구 | 디렉토리/파일 존재 + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-4: 기존 에이전트 파일 6개 삭제 확인

| 항목 | 내용 |
|------|------|
| 대상 | 6개 파일 삭제: `agents/claude/dtp-dev-full-agent/AGENT.md`, `agents/claude/dtp-dev-short-agent/AGENT.md`, `agents/cursor/dtp-dev-full-agent.md`, `agents/cursor/dtp-dev-short-agent.md`, `agents/antigravity/dtp-dev-full-agent/`, `agents/antigravity/dtp-dev-short-agent/` |
| 조건 | 모든 파일/디렉토리가 존재 |
| 기대 결과 | 1. 6개 모두 삭제되었는가? 2. 부모 디렉토리는 유지되는가? (e.g., `agents/claude/`, `agents/cursor/`, `agents/antigravity/`) |
| 도구 | 파일/디렉토리 존재 확인 (ls/find 명령) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-5: modes/dev-full.md 워커 에이전트명 갱신

| 항목 | 내용 |
|------|------|
| 대상 | `skills/dev-task-pilot/modes/dev-full.md` — 워커 에이전트명 참조 변경 |
| 조건 | 파일이 `dtp-dev-full-agent` 문자열을 포함 |
| 기대 결과 | 1. 파일이 존재하는가? 2. `dtp-dev-full-agent` → `dtp-dev-agent`로 완전히 교체되었는가? 3. 다른 내용(파이프라인 설명, 단계 등)은 변경 없는가? |
| 도구 | grep + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-6: modes/dev-short.md 워커 에이전트명 갱신

| 항목 | 내용 |
|------|------|
| 대상 | `skills/dev-task-pilot/modes/dev-short.md` — 워커 에이전트명 참조 변경 |
| 조건 | 파일이 `dtp-dev-short-agent` 문자열을 포함 |
| 기대 결과 | 1. 파일이 존재하는가? 2. `dtp-dev-short-agent` → `dtp-dev-agent`로 완전히 교체되었는가? 3. 다른 내용(파이프라인 설명, 단계 등)은 변경 없는가? |
| 도구 | grep + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-7: agents.md 레지스트리 갱신

| 항목 | 내용 |
|------|------|
| 대상 | `opal/core/references/agents.md` — 에이전트 레지스트리 |
| 조건 | 파일이 `dtp-dev-full-agent` + `dtp-dev-short-agent` 섹션을 각각 포함 |
| 기대 결과 | 1. 두 섹션이 삭제되었는가? 2. `dtp-dev-agent` 단일 섹션이 생성되었는가? 3. 새 섹션에 Full Task + Short Task 모두 설명하는가? 4. 실행 프로세스/반환 형식 등은 공통 부분 기재, EXECUTE 추가 규칙은 Full+Short 통합 기재? |
| 도구 | grep + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-8: CLAUDE.md 에이전트 구조 문서 갱신

| 항목 | 내용 |
|------|------|
| 대상 | `CLAUDE.md` — 에이전트 디렉토리 구조 및 설명 |
| 조건 | 파일에 `dtp-dev-full-agent`, `dtp-dev-short-agent` 언급 포함 |
| 기대 결과 | 1. 두 항목이 제거되었는가? 2. `dtp-dev-agent`만 남아있는가? 3. 설명이 Full+Short 모드 모두 다루는가? 4. 다른 에이전트(dtp-wireframe-ui-agent 등)는 변경 없는가? |
| 도구 | grep + 내용 비교 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-9: 3개 플랫폼 파일 내용 일관성

| 항목 | 내용 |
|------|------|
| 대상 | `agents/claude/dtp-dev-agent/AGENT.md` vs `agents/cursor/dtp-dev-agent.md` vs `agents/antigravity/dtp-dev-agent/SKILL.md` |
| 조건 | 3개 파일이 모두 생성됨 |
| 기대 결과 | 1. 3개 파일의 핵심 내용(역할, 프로세스, 단계 매핑, 규칙, STATE.md 갱신)이 동일한가? 2. 플랫폼별 포맷 차이만 있고 실질 내용은 일관성 있는가? |
| 도구 | 내용 비교 (diff 또는 수동 검사) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-10: 기존 Full Task / Short Task / Wireframe UI 동작 영향 없음

| 항목 | 내용 |
|------|------|
| 대상 | 3개 모드(Full/Short/Wireframe UI) 모두 기존 워커 에이전트명 → dtp-dev-agent로 정상 라우팅되는가? |
| 조건 | 1. modes/dev-full.md + modes/dev-short.md 워커명 갱신됨 2. modes/wireframe-ui.md는 변경 없음 3. dtp-dev-agent 생성됨 |
| 기대 결과 | 1. modes/dev-full.md가 dtp-dev-agent를 호출하는가? 2. modes/dev-short.md가 dtp-dev-agent를 호출하는가? 3. modes/wireframe-ui.md는 여전히 dtp-wireframe-ui-agent를 호출하는가? |
| 도구 | grep + 경로 추적 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

---

## 코드 품질

(문서 전용 변경 — 마크다운 검증만 해당)

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 마크다운 문법 | markdownlint 또는 수동 | _{채움}_ | _{채움}_ |
| 2 | 참조 링크 유효성 | grep + 파일 존재 확인 | _{채움}_ | _{채움}_ |
| 3 | 일관성 (3개 플랫폼) | 수동 비교 | _{채움}_ | _{채움}_ |

---

## 보안

(문서 전용 변경 — 해당 없음)

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | N/A | 문서만 변경, 코드 없음 |
| 2 | .gitignore 확인 | N/A | 문서만 변경, 코드 없음 |

---

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | Full Task 파이프라인(ANALYSIS→PLAN→TODO→EXECUTE) | _{채움}_ | modes/dev-full.md이 dtp-dev-agent를 정상 호출하는가? |
| 2 | Short Task 파이프라인(PLAN-SHORT→EXECUTE-SHORT) | _{채움}_ | modes/dev-short.md이 dtp-dev-agent를 정상 호출하는가? |
| 3 | 기존 dtp-dev-full-agent / dtp-dev-short-agent 참조 제거 | _{채움}_ | 삭제된 파일을 참조하는 다른 곳이 없는가? |
| 4 | dtp-wireframe-ui-agent 유지 | _{채움}_ | 이 에이전트는 변경되지 않았는가? |

---

## 판정

**_{dtp-test가 채움: All Pass / Partial Fail / Critical Fail}_ — _{판정 근거}_**

---

## 설계 피드백

**없음** — TEST-SCENARIO.md 작성 과정에서 설계 빈틈이 발견되지 않았습니다.

기존 Full/Short 에이전트 구조가 명확하고, 통합 설계(공통 섹션 + 개별 섹션)가 타당합니다. PLAN.md에서 제시한 구조(단계 매핑 테이블, EXECUTE 추가 규칙의 Full+Short 세분)가 적절합니다.

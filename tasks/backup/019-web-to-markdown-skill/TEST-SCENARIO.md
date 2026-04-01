# TEST-SCENARIO: web-to-markdown 스킬 개발

> 작성일: 2026-03-20 | 태스크: 019-web-to-markdown-skill | 유형: Short Task
> 실행일: 2026-03-20 | 상태: **실행 완료**

---

## 문서 전용 변경 -- 코드 테스트 대상 없음

이 태스크의 모든 변경 파일은 `.md`(마크다운)이다. 런타임 코드가 없으므로 코드 단위 테스트, 보안 테스트, 회귀 테스트는 해당 없음. 아래 시나리오는 문서 품질(내용 정합성, 참조 링크, 구조 검증)에 집중한다.

---

## 시나리오 목록

### S-1: SKILL.md 기본/clean 모드 정합성 검증

| 항목 | 내용 |
|------|------|
| **대상** | `skills/web-to-markdown/SKILL.md` -- 콘텐츠 추출 모드 섹션 |
| **조건** | PLAN.md 변경 1에 따라 기본 모드(full)와 clean 모드가 분리 정의되어 있을 때 |
| **기대 결과** | (1) 기본 모드에서 nav/sidebar/header/footer 제거 지시가 없음, (2) clean 모드에서 nav/header/footer/sidebar 제거 지시가 있음, (3) WebFetch prompt가 모드별로 분기됨, (4) Phase 2 정제 규칙도 모드별로 분기됨, (5) 산출물 메타데이터에 `추출 모드: full \| clean` 필드가 존재함 |
| **도구** | Read, Grep |

**실행 명령**:
1. `Read skills/web-to-markdown/SKILL.md` -- 전체 내용 확인
2. `Grep "nav|sidebar|header|footer" skills/web-to-markdown/SKILL.md` -- 구조 요소 언급 위치 확인
3. `Grep "추출 모드" skills/web-to-markdown/SKILL.md` -- 산출물 메타데이터 필드 확인

**실행 결과**: **Pass**
- (1) full 모드 WebFetch prompt(58줄): "구조 요소는 보존해줘" -- nav/sidebar/header/footer **제거 지시 없음** (확인)
- (2) clean 모드 WebFetch prompt(63줄): "nav, header, footer, sidebar...비본문 요소는 제거" -- **제거 지시 있음** (확인)
- (2-b) "clean 모드 추가 제거 대상"(167-174줄): nav, header, footer, aside, sidebar 등 명시적 제거 대상 목록 존재 (확인)
- (3) Phase 1 WebFetch prompt가 full/clean 별도 코드 블록으로 분기됨(56-64줄) (확인)
- (4) Phase 2 정제 규칙: "추출 모드(full/clean)에 따라 MD 정제"(105줄, 138줄) -- 모드별 분기 명시 (확인)
- (5) 산출물 메타데이터(198줄): `추출 모드: {full | clean}` 필드 존재 (확인)

---

### S-2: wtm-worker 에이전트 3개 플랫폼 파일 존재 및 구조 검증

| 항목 | 내용 |
|------|------|
| **대상** | `agents/claude/wtm-worker/AGENT.md`, `agents/cursor/wtm-worker.md`, `agents/antigravity/wtm-worker/SKILL.md` |
| **조건** | PLAN.md 변경 2에 따라 3개 에이전트 파일이 생성되어 있을 때 |
| **기대 결과** | (1) 3개 파일 모두 존재, (2) 각 파일에 YAML frontmatter(name, description)가 있음, (3) 입력(URL, 저장 경로, 추출 모드)과 출력(성공 여부, 사용 방식, 저장 경로) 명세가 포함됨, (4) dtp-agent 구조와 일관된 포맷 유지 |
| **도구** | Read, Glob |

**실행 명령**:
1. `Read agents/claude/wtm-worker/AGENT.md` -- 파일 존재 및 내용 확인
2. `Read agents/cursor/wtm-worker.md` -- 파일 존재 및 내용 확인
3. `Read agents/antigravity/wtm-worker/SKILL.md` -- 파일 존재 및 내용 확인
4. `Grep "^(name|description):" agents/claude/wtm-worker/AGENT.md` -- YAML frontmatter 확인
5. `Grep "^(name|description):" agents/cursor/wtm-worker.md` -- YAML frontmatter 확인
6. `Grep "^(name|description):" agents/antigravity/wtm-worker/SKILL.md` -- YAML frontmatter 확인

**실행 결과**: **Pass**
- (1) 3개 파일 모두 존재 (확인)
  - `agents/claude/wtm-worker/AGENT.md` -- 84줄
  - `agents/cursor/wtm-worker.md` -- 93줄
  - `agents/antigravity/wtm-worker/SKILL.md` -- 84줄
- (2) 3개 파일 모두 YAML frontmatter에 `name: wtm-worker`, `description: |` 존재 (확인)
  - Claude: name, description, model, color 필드
  - Cursor: name, description, model, readonly, tools, max_turns, timeout_mins 필드
  - Antigravity: name, description 필드
- (3) 입력 명세: 3개 파일 모두 "url", "save_path", "mode" (full/clean) 입력 정의 (확인)
  - 출력 명세: 3개 파일 모두 "url", "save_path", "method", "status", "summary" 반환 정의 (확인)
- (4) dtp-agent 구조와 일관성:
  - 역할/입력/실행 프로세스/반환 형식 섹션 구조가 dtp-agent의 역할/입력/실행 프로세스 패턴과 일치 (확인)
  - Claude: AGENT.md 디렉토리 기반, Cursor: 플랫 .md + tools 목록, Antigravity: SKILL.md 폴백 모드 안내 (확인)

---

### S-3: SKILL.md 에이전트 탐색 경로 및 참조 완전성 검증

| 항목 | 내용 |
|------|------|
| **대상** | `skills/web-to-markdown/SKILL.md` -- 복수 URL 처리 섹션 |
| **조건** | PLAN.md 변경 3에 따라 wtm-worker 에이전트 탐색 경로가 추가되어 있을 때 |
| **기대 결과** | (1) 탐색 경로 6개가 우선순위 순서대로 명시됨 (프로젝트 로컬 3개 -> 글로벌 3개), (2) 경로 내 에이전트 이름이 `wtm-worker`로 통일됨, (3) SKILL.md 전체 500줄 이하 |
| **도구** | Read, Grep |

**실행 명령**:
1. `Grep "wtm-worker" skills/web-to-markdown/SKILL.md` -- 에이전트 탐색 경로 확인
2. `wc -l skills/web-to-markdown/SKILL.md` -- 줄 수 확인

**실행 결과**: **Pass**
- (1) 탐색 경로 6개 확인 (244-250줄):
  1. `{프로젝트}/.cursor/agents/wtm-worker.md` (프로젝트 로컬)
  2. `{프로젝트}/.claude/agents/wtm-worker/AGENT.md` (프로젝트 로컬)
  3. `{프로젝트}/.agent/skills/wtm-worker/SKILL.md` (프로젝트 로컬)
  4. `~/.cursor/agents/wtm-worker.md` (글로벌)
  5. `~/.claude/agents/wtm-worker/AGENT.md` (글로벌)
  6. `~/.gemini/antigravity/skills/wtm-worker/SKILL.md` (글로벌)
  - 순서: 프로젝트 로컬 3개 -> 글로벌 3개 (확인)
- (2) 6개 경로 모두 에이전트 이름이 `wtm-worker`로 통일됨 (확인)
- (3) SKILL.md 총 323줄 -- 500줄 제한 이내 (확인)

---

### S-4: OPAL 레지스트리 등록 및 기존 항목 보존 검증

| 항목 | 내용 |
|------|------|
| **대상** | `~/.opal/references/skills.md` -- 프레임워크 스킬 테이블 |
| **조건** | PLAN.md 변경 4에 따라 web-to-markdown 행이 추가되어 있을 때 |
| **기대 결과** | (1) web-to-markdown 행이 테이블에 존재함, (2) 트리거 키워드와 설명이 PLAN.md 명세와 일치함, (3) 기존 등록된 프레임워크 스킬 7개가 삭제/변경 없이 유지됨 |
| **도구** | Read, Grep |

**실행 명령**:
1. `Grep "web-to-markdown" ~/.opal/references/skills.md` -- 행 존재 확인
2. `Grep "^\| (dev-task-pilot|api-analyzer|doc-writer|interview|version-mgr|wireframe-builder|ui-designer|web-to-markdown)" ~/.opal/references/skills.md` -- 전체 프레임워크 스킬 행 확인
3. `Grep "wtm-worker" ~/.opal/references/agents.md` -- agents 레지스트리 등록 확인

**실행 결과**: **Pass**
- (1) web-to-markdown 행 존재 (19줄): `| web-to-markdown | "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와" | URL -> 웹 콘텐츠를 정제된 마크다운으로 변환 (2단계 폴백: WebFetch -> Playwright) |` (확인)
- (2) 트리거 키워드 일치 검증:
  - PLAN.md 명세: "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와"
  - skills.md 등록: 동일 5개 키워드 (확인)
- (3) 기존 프레임워크 스킬 7개 보존 확인:
  - dev-task-pilot (12줄) -- 보존
  - api-analyzer (13줄) -- 보존
  - doc-writer (14줄) -- 보존
  - interview (15줄) -- 보존
  - version-mgr (16줄) -- 보존
  - wireframe-builder (17줄) -- 보존
  - ui-designer (18줄) -- 보존
  - 총 8개 행 (기존 7 + 신규 1) -- 기존 항목 삭제/변경 없음 (확인)
- (추가) agents.md에 wtm-worker 섹션 등록 확인 (55줄) -- 역할, 호출 시점, 입력, 출력 명세 존재 (확인)

---

## 코드 품질/보안/회귀

**문서 전용 변경 -- 코드 테스트 스킵**

| 항목 | 결과 | 상세 |
|------|------|------|
| 코드 린트 | Skip | 문서 전용 변경 -- 코드 파일 없음 |
| 타입 체크 | Skip | 문서 전용 변경 -- 코드 파일 없음 |
| 포맷터 | Skip | 문서 전용 변경 -- 코드 파일 없음 |
| 회귀 테스트 | Skip | 문서 전용 변경 -- 테스트 스위트 해당 없음 |
| 보안 스캔 | Pass | 변경 파일 6개에서 password/secret/token/api_key 패턴 미검출 |

---

## 종합 판정

| 시나리오 | 결과 | 비고 |
|----------|------|------|
| S-1 | **Pass** | full/clean 모드 분리, WebFetch prompt 분기, Phase 2 분기, 산출물 메타데이터 모두 정상 |
| S-2 | **Pass** | 3개 플랫폼 파일 존재, YAML frontmatter 정상, 입출력 명세 완비, dtp-agent 구조 일관 |
| S-3 | **Pass** | 탐색 경로 6개 순서 정상, wtm-worker 이름 통일, 323줄 (500줄 이내) |
| S-4 | **Pass** | web-to-markdown 행 등록, 트리거 일치, 기존 7개 스킬 보존, agents.md에도 등록 완료 |
| **종합** | **All Pass** | 문서 전용 변경 -- 4개 시나리오 전체 Pass, 보안 스캔 Pass |

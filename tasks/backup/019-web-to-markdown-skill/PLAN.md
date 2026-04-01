# PLAN: web-to-markdown 스킬 개발

> 작성일: 2026-03-20 | 유형: Short Task | 태스크: 019-web-to-markdown-skill

---

## Part A: 코드 분석

### 현재 상태

**skills/web-to-markdown/SKILL.md** (288줄, v1.0 초안)
- 2단계 폴백 전략(WebFetch -> Playwright)이 잘 설계되어 있음
- **문제**: "본문 추출 및 MD 정제" 섹션(141-178줄)이 기본 모드에서 nav/header/footer/sidebar를 제거하도록 되어 있음
- TASK.md 요구사항: 전체 콘텐츠(nav/sidebar 포함)가 기본 모드, clean 옵션으로 본문만 추출
- WebFetch prompt(48줄)에도 "비본문 요소 제거" 지시가 하드코딩되어 있어 변경 필요
- 복수 URL 병렬 처리 섹션은 서브에이전트 디스패치 구조가 있으나, 에이전트 탐색 경로 미명시

**에이전트 파일 (미존재)**
- `agents/claude/wtm-worker/AGENT.md` -- 미생성
- `agents/cursor/wtm-worker.md` -- 미생성
- `agents/antigravity/wtm-worker/SKILL.md` -- 미생성

**OPAL 레지스트리** (`~/.opal/references/skills.md`)
- 프레임워크 스킬 7개 등록, web-to-markdown 미등록

### 영향 범위

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `skills/web-to-markdown/SKILL.md` | 수정 | 기본/clean 모드 전환, WebFetch prompt 수정, 에이전트 경로 추가 |
| `agents/claude/wtm-worker/AGENT.md` | 신규 | Claude 플랫폼 워커 에이전트 |
| `agents/cursor/wtm-worker.md` | 신규 | Cursor 플랫폼 워커 에이전트 |
| `agents/antigravity/wtm-worker/SKILL.md` | 신규 | Antigravity 플랫폼 워커 에이전트 |
| `~/.opal/references/skills.md` | 수정 | 레지스트리에 web-to-markdown 등록 |

---

## Part B: 구현 계획

### 변경 1: SKILL.md -- 기본/clean 모드 전환

**현재**: "본문 추출 및 MD 정제" 섹션에서 nav/header/footer/sidebar/aside를 무조건 제거
**변경**:
- "콘텐츠 추출 모드" 섹션을 신설하여 두 가지 모드를 정의:
  - **기본 모드 (full)**: 전체 콘텐츠 보존. `<script>`, `<style>`, `<noscript>`, `<iframe>`, 광고, 쿠키 배너, 트래킹 픽셀만 제거. nav/sidebar/header/footer는 유지하되 마크다운 구조로 변환
  - **clean 모드**: 기존 제거 대상(nav/header/footer/sidebar 등)을 모두 제거하여 본문만 추출
- 기존 "제거 대상 (기본 모드)" 섹션을 "제거 대상" 공통 + "clean 모드 추가 제거"로 분리
- **Phase 1 (WebFetch)** prompt를 모드별로 분기:
  - 기본: "이 페이지의 전체 콘텐츠를 마크다운으로 변환해줘. script/style 태그만 제거하고 nav, sidebar 등 구조 요소는 보존해줘."
  - clean: 기존 prompt 유지 (비본문 제거)
- **Phase 2 (Playwright)** HTML 정제도 동일하게 모드 분기:
  - 기본: Playwright로 획득한 HTML에서 script/style/iframe만 제거 후 MD 변환 (구조 요소 보존)
  - clean: 기존 정제 규칙 적용 (nav/header/footer/sidebar 등 추가 제거)
- 산출물 메타데이터에 `추출 모드: full | clean` 필드 추가
- 사용 예시 섹션 추가 (모드 지정 방법 안내)

> **Playwright MCP 연동**: 초안에 이미 Phase 2 도구 선택 우선순위(Playwright MCP → Playwright 스크립트)와 MCP 등록 방법이 명시되어 있으므로, TASK.md의 "Playwright MCP 연동 검토" 요구사항은 충족됨. 추가 변경 불필요.

### 변경 2: wtm-worker 에이전트 생성 (3개 플랫폼)

dtp-agent 구조를 참고하되, 역할을 web-to-markdown 단일 URL 처리에 특화:
- **역할**: 단일 URL을 받아 Phase 1/2 폴백 전략으로 마크다운 변환 수행
- **입력**: URL, 저장 경로, 추출 모드(full/clean)
- **출력**: 성공 여부, 사용 방식(WebFetch/Playwright), 저장 경로
- **플랫폼별 차이**:
  - Claude: `AGENT.md` (기본 YAML frontmatter)
  - Cursor: 플랫 `.md` (tools, max_turns, timeout_mins YAML)
  - Antigravity: `SKILL.md` (폴백 모드 안내)

### 변경 3: SKILL.md -- 에이전트 탐색 경로 추가

복수 URL 처리 섹션에 wtm-worker 에이전트 탐색 경로를 명시:
```
탐색 경로 (우선순위):
1. {프로젝트}/.cursor/agents/wtm-worker.md
2. {프로젝트}/.claude/agents/wtm-worker/AGENT.md
3. {프로젝트}/.agent/skills/wtm-worker/SKILL.md
4. ~/.cursor/agents/wtm-worker.md
5. ~/.claude/agents/wtm-worker/AGENT.md
6. ~/.gemini/antigravity/skills/wtm-worker/SKILL.md
```

### 변경 4: OPAL 레지스트리 등록

`~/.opal/references/skills.md`의 프레임워크 스킬 테이블에 행 추가:
```
| web-to-markdown | "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와" | URL을 입력받아 웹 콘텐츠를 정제된 마크다운으로 변환 |
```

---

## Part C: 실행 체크리스트

- [x] **Step 1**: SKILL.md 수정 -- 기본/clean 모드 전환 (콘텐츠 추출 모드 섹션 신설, WebFetch prompt 분기, Phase 2 모드 분기, 산출물 메타데이터 추가)
- [x] **Step 2**: SKILL.md 수정 -- 복수 URL 섹션에 wtm-worker 에이전트 탐색 경로 추가
- [x] **Step 3**: wtm-worker 에이전트 3개 플랫폼 파일 생성 (agents/claude/wtm-worker/AGENT.md, agents/cursor/wtm-worker.md, agents/antigravity/wtm-worker/SKILL.md)
- [x] **Step 4**: OPAL 레지스트리(~/.opal/references/skills.md + agents.md)에 web-to-markdown + wtm-worker 등록
- [x] **Step 5**: 버전 태깅 확인 -- SKILL.md v1.0 유지, 변경이력 업데이트 완료 (323줄, 500줄 이하)

---

## Part D: QA 체크리스트

### 기능 테스트
- [x] SKILL.md가 500줄 이하인지 확인 — 323줄
- [x] 기본 모드(full)에서 nav/sidebar 제거 지시가 없는지 확인 — full prompt에 "구조 요소 보존" 명시
- [x] clean 모드에서 nav/header/footer/sidebar 제거 지시가 있는지 확인 — clean 모드 추가 제거 섹션 존재
- [x] WebFetch prompt가 모드별로 분기되는지 확인 — full/clean 각각 별도 prompt
- [x] 산출물 메타데이터에 추출 모드 필드가 있는지 확인 — `추출 모드: {full | clean}` 필드 존재
- [x] wtm-worker 에이전트 3개 파일이 모두 존재하는지 확인 — claude/cursor/antigravity 모두 생성
- [x] 에이전트 탐색 경로가 6개 경로 모두 명시되어 있는지 확인

### 회귀 테스트
- [x] Phase 1/2 폴백 전략이 변경되지 않았는지 확인
- [x] 저장 경로 우선순위가 유지되는지 확인
- [x] slug 생성 규칙이 유지되는지 확인
- [x] 에지 케이스 처리 테이블이 유지되는지 확인
- [x] 의존성 테이블이 유지되는지 확인

### 코드 품질
- [x] 한국어 본문, 영어 코드/필드명 컨벤션 준수
- [x] YAML frontmatter 형식 정합성 (name, description 필드)
- [x] 에이전트 파일이 dtp-agent 구조와 일관성 유지
- [x] 변경이력 테이블에 v1.0 변경내용 업데이트

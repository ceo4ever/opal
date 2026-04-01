# TODO: Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 작성일: 2026-03-07 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 10개 Step | 실행 모드: 복잡

### Step 1: QA 호출 구조 개선 — 레퍼런스 가이드 수정

- **파일**: `claude/skills/task-flow/references/research-guide.md`, `plan-guide.md`, `todo-guide.md`, `execute-guide.md`
- **작업 내용**: 4개 가이드의 "품질 체크리스트" 섹션 아래에 "⚠️ QA 에이전트 호출 (필수)" 섹션 추가. PLAN 3.1절의 추가 내용 적용.
- **완료 기준**: 4개 파일 모두에 QA 에이전트 호출 섹션이 존재하고, "SKILL.md의 QA 에이전트 호출 규칙 참조" 문구 포함
- **테스트**: Grep으로 4개 파일에서 "QA 에이전트 호출" 섹션 존재 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

### Step 2: QA 호출 구조 개선 — AGENT.md 표현 수정

- **파일**: `claude/agents/task-flow-qa/AGENT.md`
- **작업 내용**: description의 "자동 호출됩니다" 표현을 PLAN 3.1절의 변경 후 문구로 수정
- **완료 기준**: "자동 호출" 문구 제거, "메인 에이전트가 명시적으로 호출" 문구 존재
- **테스트**: Grep으로 "자동 호출" 부재 확인 + "명시적으로 호출" 존재 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

### Step 3: QA 호출 구조 개선 — SKILL.md QA 호출 강조 + Antigravity 탐색 경로

- **파일**: `claude/skills/task-flow/SKILL.md`
- **작업 내용**:
  1. 각 STEP(1~5)의 마지막 한 줄 QA 호출 지시를 별도 서브섹션("### ⚠️ QA 에이전트 호출 (필수)")으로 교체 (PLAN 3.1절 참조). STEP 5는 단순/복잡 모드 실행 흐름 내에 QA 호출이 포함되어 있으므로, 해당 흐름 내에서 강조 블록 형태로 적용
  2. QA/Planner/Test 에이전트 탐색 경로에 Antigravity 경로 추가 + Cursor 플랫 파일 경로로 업데이트 (PLAN 3.1절 참조)
- **완료 기준**: STEP 1~5 각각에 "### ⚠️ QA 에이전트 호출" 서브섹션 또는 동등한 강조 블록 존재. 탐색 경로에 `.agent/skills/` 및 `~/.gemini/antigravity/skills/` 포함. Cursor 경로가 `{name}.md` 형식
- **테스트**: Grep으로 "⚠️ QA 에이전트 호출" 5회 이상 확인. 탐색 경로에 antigravity 포함 확인
- **실행 방법**: direct
- **의존**: Step 1, Step 2
- **상태**: ✅ 완료

### Step 4: Cursor 에이전트 플랫 파일 전환

- **파일**: `cursor/agents/task-flow-qa.md`, `task-flow-planner.md`, `task-flow-test.md` (신규), `cursor/agents/task-flow-qa/`, `task-flow-planner/`, `task-flow-test/` (삭제)
- **작업 내용**:
  1. 각 `cursor/agents/{name}/AGENT.md`의 내용을 `cursor/agents/{name}.md`로 이동
  2. task-flow-qa.md에는 Step 2의 "자동 호출" 수정도 적용
  3. 기존 디렉토리(`cursor/agents/{name}/`) 삭제
- **완료 기준**: `cursor/agents/` 아래에 3개 `.md` 파일만 존재하고, 디렉토리 없음
- **테스트**: ls로 cursor/agents/ 구조 확인 (디렉토리 없음, .md 파일 3개)
- **실행 방법**: direct
- **의존**: Step 2
- **상태**: ✅ 완료

### Step 5: Antigravity 스킬 — 단순 복사 (5개)

- **파일**: `antigravity/skills/api-analyzer/SKILL.md`, `doc-writer/SKILL.md`, `interview/SKILL.md`, `version-mgr/SKILL.md`, `wireframe-builder/SKILL.md`
- **작업 내용**: `claude/skills/{name}/`의 전체 디렉토리(SKILL.md + 하위 파일)를 `antigravity/skills/{name}/`으로 복사
- **완료 기준**: 5개 스킬 디렉토리가 antigravity/skills/ 아래에 존재하고, claude/ 버전과 내용 동일
- **테스트**: diff -r로 claude/skills/{name}/과 antigravity/skills/{name}/ 디렉토리 전체 비교 (SKILL.md + 하위 파일 포함)
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

### Step 6: Antigravity task-flow + references

- **파일**: `antigravity/skills/task-flow/SKILL.md`, `antigravity/skills/task-flow/references/*.md` (5개)
- **작업 내용**:
  1. Step 1, 3 수정이 완료된 `claude/skills/task-flow/`를 `antigravity/skills/task-flow/`로 복사
  2. SKILL.md를 Antigravity 특화 수정 (PLAN 3.4절):
     - "에이전트" → "스킬" 용어 변경
     - 탐색 경로를 Antigravity 전용으로 교체
     - 호출 방법을 스킬 호출 방식으로 변경
- **완료 기준**: antigravity/skills/task-flow/SKILL.md에 "스킬 탐색 경로"가 `.agent/skills/` 기준으로 존재. references/ 5개 파일 존재
- **테스트**: Grep으로 SKILL.md에서 ".agent/skills/" 존재 확인. 파일 수 확인
- **실행 방법**: direct
- **의존**: Step 1, Step 3
- **상태**: ✅ 완료

### Step 7: Antigravity 에이전트→스킬 변환 (3개)

- **파일**: `antigravity/skills/task-flow-qa/SKILL.md`, `task-flow-planner/SKILL.md`, `task-flow-test/SKILL.md`
- **작업 내용**: PLAN 3.5절의 변환 규칙에 따라 `claude/agents/{name}/AGENT.md`를 SKILL.md 포맷으로 변환:
  - YAML frontmatter: `model`, `readonly` 제거, description 보강
  - 본문: "에이전트" → "스킬" 용어 교체
  - task-flow-qa: "자동 호출" 수정 반영
- **완료 기준**: 3개 SKILL.md에 `name`과 `description` frontmatter 존재. `model:`, `readonly:` 없음. 본문 내 검증 기준/프로세스 유지
- **테스트**: YAML frontmatter 파싱 확인. "model:" 부재 확인
- **실행 방법**: direct
- **의존**: Step 2
- **상태**: ✅ 완료

### Step 8: 템플릿 생성

- **파일**: `templates/GEMINI.md`, `templates/r2/gemini-snippet.md`
- **작업 내용**:
  1. `templates/CLAUDE.md`를 기반으로 `templates/GEMINI.md` 작성 (PLAN 3.6절)
  2. `templates/r2/claude-snippet.md`를 기반으로 `templates/r2/gemini-snippet.md` 작성 (PLAN 3.6절)
- **완료 기준**: GEMINI.md에 필수 섹션(Project Overview, Language, Tech Stack, Architecture, Code Conventions) 존재. gemini-snippet.md에 알투 핵심 요소(정체성, 성격, 주도성, 역할) 포함
- **테스트**: 섹션 키워드 Grep 확인. claude-snippet.md와 구조 비교
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

### Step 9: Cursor 스킬 미러 동기화

- **파일**: `cursor/skills/` (전체)
- **작업 내용**: Step 1, 3에서 수정된 `claude/skills/`의 내용을 `cursor/skills/`에 재복사하여 동기화
- **완료 기준**: claude/skills/와 cursor/skills/의 내용이 동일 (diff 없음)
- **테스트**: diff -r로 두 디렉토리 비교
- **실행 방법**: direct
- **의존**: Step 1, Step 3
- **상태**: ✅ 완료

### Step 10: 프로젝트 문서 업데이트

- **파일**: `CLAUDE.md`, `README.md`
- **작업 내용**:
  1. CLAUDE.md: 소스 구조에 `antigravity/` 추가, 배포 구조에 Antigravity 경로 추가, Cursor 에이전트 구조를 플랫 파일로 업데이트, 에이전트 탐색 경로에 Antigravity 추가
  2. README.md: Antigravity 설치 섹션 추가, Antigravity 프로젝트 설정 섹션 추가, Cursor 에이전트 마이그레이션 안내 추가
- **완료 기준**: CLAUDE.md에 "antigravity/" 구조 기술 존재. README.md에 "Antigravity" 설치 가이드 섹션 존재
- **테스트**: Grep으로 두 문서에서 "antigravity" 키워드 존재 확인
- **실행 방법**: direct
- **의존**: Step 1~9 (모든 파일 변경 확정 후)
- **상태**: ✅ 완료

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] TASK A-1: antigravity/skills/ 아래 6개 스킬 디렉토리 존재, 각각 SKILL.md 포함 (name + description frontmatter)
- [ ] TASK A-2: antigravity/skills/ 아래 3개 에이전트 변환 스킬(task-flow-qa, task-flow-planner, task-flow-test) 존재
- [ ] TASK A-3: templates/GEMINI.md 존재, 필수 섹션 포함
- [ ] TASK A-4: templates/r2/gemini-snippet.md 존재, 알투 핵심 요소 포함
- [ ] TASK A-5: claude/skills/task-flow/SKILL.md 탐색 경로에 Antigravity 경로 포함
- [ ] TASK A-6: CLAUDE.md와 README.md에 Antigravity 관련 내용 존재
- [ ] TASK B-0: cursor/agents/ 아래에 플랫 파일(.md) 3개 존재, 디렉토리 없음
- [ ] TASK C-1: references 가이드 4개에 "QA 에이전트 호출" 섹션 존재
- [ ] TASK C-2: task-flow-qa AGENT.md에 "자동 호출" 문구 없음, "명시적으로 호출" 존재
- [ ] TASK C-3: task-flow SKILL.md 각 STEP에 "⚠️ QA 에이전트 호출" 서브섹션 존재

### B-2. 회귀 테스트

- [ ] claude/agents/ 디렉토리 구조 유지 (task-flow-qa/, task-flow-planner/, task-flow-test/ 디렉토리 기반 그대로)
- [ ] claude/skills/ 5개 스킬(task-flow 제외) 내용 변경 없음
- [ ] claude/skills/task-flow/SKILL.md의 기존 워크플로우 로직 유지 (5단계 파이프라인, 구현 금지 원칙 등)
- [ ] templates/cursor-rules/*.mdc 파일 변경 없음
- [ ] templates/r2/000-r2-persona.mdc, claude-snippet.md 변경 없음

### B-3. 코드 품질

- [ ] 모든 SKILL.md에 유효한 YAML frontmatter (name + description)
- [ ] 파일/폴더명 kebab-case 준수
- [ ] 문서 본문 한국어 + 기술 용어 영어 병기 규칙 준수
- [ ] Markdown 문법 오류 없음

### B-4. 보안

- [ ] 민감 정보(API 키, 토큰 등) 없음
- [ ] .gitignore 변경 불필요 (Markdown 파일만)

---

## 복잡도 판별

| 기준 | 판정 | 근거 |
|------|------|------|
| Step 수 | 복잡 (10개 > 5) | ✓ |
| 변경 파일 수 | 복잡 (30개+ > 3) | ✓ |
| 모듈 범위 | 복잡 (3-플랫폼 + 템플릿 + 문서) | ✓ |
| 작업 유형 | 복잡 (신규 개발 + 기능 개선) | ✓ |
| 외부 의존성 | 단순 (없음) | |

**판정: 복잡 모드**

단, 모든 작업이 Markdown 파일 생성/수정이고 외부 의존성이 없으므로, 실제 난이도는 낮습니다. **Planner 에이전트 호출 없이 메인 에이전트가 직접 실행하는 것을 권장합니다** — Step 간 의존성이 단순하고, 파일 간 충돌 위험이 낮으며, 모두 direct 실행이 가능합니다.

---

## 승인 요청

> ⚠️ 위 TODO가 캡틴의 승인을 받으면 EXECUTE 단계를 시작합니다.
> 복잡도는 복잡 모드이나, 실제로는 Markdown 파일 작업이므로 메인 에이전트가 Step 순서대로 직접 실행합니다.
> Part C(Planner 에이전트)는 생략을 권장합니다. 캡틴이 원하시면 호출할 수 있습니다.

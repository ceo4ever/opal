# PLAN: OPAL 프로젝트 메모리 시스템

> 작성일: 2026-03-17 | 모드: Short Task | 참조: TASK.md | 버전: v4.0

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/AGENT.md` | 에이전트 코어 정의, 부트스트랩 절차 | Yes — "기억과 학습" 저장소 + "프로젝트 컨텍스트" 메모리 로드 |
| `opal/skills/orchestrator/SKILL.md` | 오케스트레이션 스킬 | Yes — 메모리 읽기/쓰기 트리거 추가 |
| `opal/templates/project-agent.md` | 프로젝트 에이전트 템플릿 | No — 다음 태스크에서 개편 |
| `opal/skills/project-init/SKILL.md` | 프로젝트 초기화 스킬 | No — 다음 태스크에서 개편 |

### 현재 구현

**AGENT.md "기억과 학습" (62-69행):**
- 저장 대상 정의됨 (패턴, 선호, 이슈, 아키텍처 결정)
- 활용 방법 정의됨
- **문제: 실제 저장소(파일 경로/형식)가 없음**

**부트스트랩 "프로젝트 컨텍스트" (128-135행):**
- CLAUDE.md, .cursor/rules/, GEMINI.md, .opal/AGENT.md를 읽음
- 메모리 관련 항목 없음

**오케스트레이터:**
- Step 1~5: 로드 → 해석 → 실행 → 검토 → 보고
- 메모리 읽기/쓰기 없음

### 영향 범위

- AGENT.md: 부트스트랩 절차에 조건부 Read 추가 (비파괴적)
- orchestrator: Step 1에 메모리 로드, 새 Step 6에 메모리 갱신
- 기존 `.opal/AGENT.md`만 있는 프로젝트: 영향 없음 (메모리는 "있으면 읽기")

## 2. 구현 계획

### 설계 결정

#### D1: 메모리 저장 경로 — 홈 디렉토리 (프로젝트 외부)

```
~/.opal/projects/{경로인코딩}/
├── MEMORY.md              ← 인덱스 (링크 + 작업 히스토리)
└── memory/
    ├── preferences.md     ← 소유자 선호
    ├── patterns.md        ← 프로젝트 패턴
    ├── issues.md          ← 반복 이슈
    └── ...필요 시 추가
```

- `{경로인코딩}`: 프로젝트 절대 경로를 `-`로 인코딩 (예: `/Volumes/Data/project` → `-Volumes-Data-project`)
- Claude Code 내장 메모리(`~/.claude/projects/{path}/memory/`)와 동일한 패턴
- 프로젝트 디렉토리를 더럽히지 않음 (git 무관)
- 부트스트랩 시 MEMORY.md(인덱스)만 읽고, 관련 파일만 선택적 Read → 토큰 효율
- 작업 히스토리는 MEMORY.md에 직접 기록 (FIFO 10개)

#### D2: 메모리 독립 생성 (project-init 비의존)

프로젝트 에이전트(`.opal/AGENT.md`)가 없어도 메모리를 사용할 수 있다:

| 트리거 | 동작 |
|--------|------|
| 소유자 "기억해둬" | `~/.opal/projects/{경로}/` 없으면 디렉토리 생성 → `MEMORY.md` + `memory/{type}.md` 생성 |
| 태스크 완료 시 | `MEMORY.md` 있으면 → 작업 히스토리 갱신 / 없으면 → 무시 (자동 생성하지 않음) |
| 소유자 "메모리 만들어" | `~/.opal/projects/{경로}/MEMORY.md` + `memory/` 생성 |

#### D3: Claude Code 내장 메모리와 완전 분리

- Claude Code 메모리 (`~/.claude/projects/.../memory/`): 플랫폼 전용, OPAL 불관여
- OPAL 메모리 (`{프로젝트}/.opal/memory/`): 프로젝트 디렉토리, 크로스 플랫폼, git 추적 가능

### 메모리 파일 형식

**MEMORY.md (인덱스):**
```markdown
# {프로젝트명} Memory

> 최종 갱신: YYYY-MM-DD

## 메모리 목록
| 파일 | 설명 |
|------|------|

## 작업 히스토리 (최대 10개)
| 작업 | 결과 | 날짜 |
|------|------|------|
```

**개별 메모리 파일 (memory/*.md):**
```markdown
---
name: {메모리 이름}
description: {한 줄 설명 — 관련성 판단에 사용}
type: {preferences | patterns | issues | architecture}
---

{메모리 내용}
```

### 메모리 항목 유형

| 유형 | 파일명 | 저장 기준 | 예시 |
|------|--------|----------|------|
| 소유자 선호 | `preferences.md` | 소유자가 명시한 작업 방식 | "커밋 메시지는 한국어로" |
| 프로젝트 패턴 | `patterns.md` | 2회 이상 반복된 코드/설계 패턴 | "서비스는 항상 index.ts re-export" |
| 반복 이슈 | `issues.md` | 동일 유형 문제 2회 이상 | "strict 모드 null 체크 누락" |
| 아키텍처 결정 | `architecture.md` | 기술 스택/구조/패턴 선택 시 | "ESM 전환 — CJS 불필요" |
| 기타 | 자유 파일명 | 위 유형에 해당하지 않는 기억 | 소유자 요청에 따라 |

### 생명주기

**생성:**
- 소유자 명시 요청 시 ("기억해둬", "메모리 만들어")
- `.opal/` 없으면 디렉토리부터 생성

**읽기:**
- 부트스트랩 시: `.opal/MEMORY.md` 있으면 Read → 인덱스 확인
- 태스크 시작 시: 관련 메모리 선택적 Read (인덱스의 description으로 판단)

**갱신 트리거:**
1. 소유자 "기억해둬" → 해당 유형 파일에 추가 (없으면 파일 생성 + MEMORY.md 인덱스 갱신)
2. 태스크 완료 → MEMORY.md 작업 히스토리 1행 추가
3. 아키텍처 결정 발생 → memory/architecture.md에 추가
4. 반복 이슈 2회 이상 → memory/issues.md에 추가
5. 패턴 2회 이상 확인 → memory/patterns.md에 추가

**정리:**
- 작업 히스토리: 10개 초과 시 FIFO
- 소유자 "이건 해결됐어" → 해당 이슈 제거
- 소유자 "메모리 정리해" → 에이전트가 정리 제안 → 승인 후 실행

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/AGENT.md` | "기억과 학습" 저장소/규칙 추가, "프로젝트 컨텍스트"에 MEMORY.md 추가 |
| 2 | `opal/skills/orchestrator/SKILL.md` | Step 1 메모리 로드, Step 6 메모리 갱신 추가 |
| 3 | (신규) `opal/templates/memory-index.md` | MEMORY.md 초기 템플릿 |

### 핵심 설계

**AGENT.md "프로젝트 컨텍스트" 변경:**

```markdown
## 프로젝트 컨텍스트

각 프로젝트에 진입하면 해당 프로젝트의 설정 파일을 읽어 컨텍스트를 파악한다:

- `CLAUDE.md` (Claude Code)
- `.cursor/rules/` (Cursor)
- `GEMINI.md` (Antigravity)
- `.opal/AGENT.md` (OPAL 프로젝트 에이전트)
- `.opal/MEMORY.md` (OPAL 프로젝트 메모리 — 있으면 읽기)
```

**AGENT.md "기억과 학습" 변경:**

```markdown
### 기억과 학습

프로젝트 경험을 `{프로젝트}/.opal/` 하위에 축적한다:

- **저장소**: `~/.opal/projects/{경로인코딩}/MEMORY.md` (인덱스) + `~/.opal/projects/{경로인코딩}/memory/*.md` (개별 파일)
- **저장하는 것**: 프로젝트 패턴, 소유자 선호, 반복되는 이슈와 해결법, 아키텍처 결정 근거
- **저장하지 않는 것**: 일회성 작업 내용, 임시 상태, 검증되지 않은 추측
- **활용 방법**: 새 작업을 시작할 때 MEMORY.md를 읽고, 관련 메모리를 선택적으로 로드
- **소유자 요청 시**: "이거 기억해둬" → 즉시 해당 유형의 메모리 파일에 기록 (없으면 생성)
- **갱신 트리거**: 태스크 완료, 아키텍처 결정, 소유자 명시 요청, 반복 이슈, 패턴 인식
- **정리**: 작업 히스토리 10개 FIFO, 소유자 요청 시 정리 제안
- **독립 생성**: `.opal/AGENT.md`가 없어도 소유자 요청 시 `.opal/MEMORY.md` + `memory/` 생성 가능
```

**orchestrator Step 1 변경:**

```markdown
### Step 1: 프로젝트 에이전트 로드

1. `{프로젝트}/.opal/AGENT.md`를 Read로 읽어 프로젝트 컨텍스트를 파악한다.
2. `~/.opal/projects/{경로인코딩}/MEMORY.md`가 있으면 Read로 읽어 프로젝트 메모리 인덱스를 로드한다.
3. 현재 작업과 관련된 메모리가 있으면 해당 memory/*.md를 선택적으로 Read한다.
```

**orchestrator Step 6 (신규):**

```markdown
### Step 6: 메모리 갱신

작업 완료 후, `~/.opal/projects/{경로인코딩}/MEMORY.md`가 존재하면 다음을 확인하고 갱신한다:

1. 태스크가 완료되었는가? → 작업 히스토리에 1행 추가 (10개 초과 시 FIFO)
2. 새로운 아키텍처 결정이 있었는가? → memory/architecture.md에 추가
3. 새로운 프로젝트 패턴을 발견했는가? → memory/patterns.md에 추가
4. 소유자가 선호를 명시했는가? → memory/preferences.md에 추가

메모리 파일이 없는 항목은 새로 생성하고 MEMORY.md 인덱스에 링크를 추가한다.
MEMORY.md 자체가 없으면 갱신을 스킵한다 (자동 생성하지 않음).
```

### 다음 태스크 (참고)

프로젝트 에이전트 개편은 별도 태스크로 진행:
- `.opal/AGENT.md` 분리형 구조 (ARCHITECTURE.md, CONVENTIONS.md)
- `project-init` 마이그레이션 모드
- 기존 프로젝트 지원

## 3. 실행 체크리스트

- [x] Step 1: 메모리 템플릿 생성 — (신규) `opal/templates/memory-index.md` — MEMORY.md 초기 템플릿
- [x] Step 2: AGENT.md 수정 — `opal/core/AGENT.md` — "기억과 학습" 저장소 추가, "프로젝트 컨텍스트" 메모리 추가
- [x] Step 3: orchestrator 수정 — `opal/skills/orchestrator/SKILL.md` — Step 1 메모리 로드, Step 6 메모리 갱신 추가
- [x] Step 4: 배포 동기화 — `~/.opal/` 하위 배포 파일에 변경 적용 + templates/ 복사

## 4. QA 체크리스트

### 기능 테스트
- [x] `.opal/MEMORY.md` 없는 프로젝트에서 부트스트랩 정상 동작 ("있으면 읽기")
- [x] 소유자 "기억해둬" 시 `.opal/MEMORY.md` + `memory/{type}.md` 생성
- [x] orchestrator가 MEMORY.md → 관련 memory/*.md 선택적 로드
- [x] orchestrator Step 6이 메모리 갱신을 정상 수행

### 회귀 테스트
- [x] `.opal/` 없는 프로젝트에서 에러 없음
- [x] 기존 `.opal/AGENT.md`만 있는 프로젝트에서 에러 없음
- [x] Claude Code / Cursor / Gemini CLI 동일 동작
- [x] Claude Code 내장 메모리와 경로 충돌 없음

### 코드 품질
- [x] OPAL 문서 표준 준수
- [x] 한국어 본문 + 영어 기술 용어
- [x] 최소 diff (기존 구조 존중)
- [x] 템플릿 토큰 효율 (빈 상태 20행 이하)

# Wireframe UI 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)
> 워커 에이전트: `dtp-wireframe-ui-agent`
> QA 에이전트: `dtp-qa-wireframe-agent`

## 파이프라인 개요

```
TASK → WIREFRAME → EXECUTE → QA
```

```
[오케스트레이터: TASK] → 입력물 분류
        │
        ├── wireframe.md 있음 → WIREFRAME 스킵
        ├── 정책서/기획서 있음 → [wireframe-builder 스킬]
        └── 구두 요청만 → [interview 스킬] → [wireframe-builder 스킬]
        │
[워커: WIREFRAME] → [QA: wireframe 검증] → 검토
        │
[워커: EXECUTE (UI 구현)] → 검토
        │
[QA: 빌드/린트 + wireframe↔코드 대조] → 완료 보고
```

---

## STEP 1: TASK (Wireframe 특화)

**오케스트레이터가 직접 수행한다** (워커 불필요).

**상세 가이드**: `references/wireframe-task-guide.md`를 읽고 따른다.

### 1단계: 목표 확인

- 구현할 화면/기능 목록 파악
- 기술 환경: React 프레임워크 버전, shadcn/ui 설치 여부, 기존 컴포넌트 패턴
- 출력 모드 결정: 프로토타입(bundle.html) vs 프로덕션(Next.js)

### 2단계: 입력물 분류 및 경로 결정

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 존재 | .md/.txt/.pdf/.docx 파일 | WIREFRAME (wireframe-builder 호출) |
| 이미지(스케치/스크린샷) 존재 | .png/.jpg 파일 | WIREFRAME (wireframe-builder 호출) |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

### 3단계: TASK.md 작성 (Wireframe 특화)

```markdown
# TASK: {화면명} UI 구현

> 작성일: YYYY-MM-DD | 작업 유형: Wireframe UI

## 구현 목표
{구현할 화면 목록}

## 기술 환경
- 프레임워크: {React/Next.js 버전}
- shadcn/ui: {설치됨/미설치}
- 출력 모드: {프로토타입/프로덕션}
- 기존 컴포넌트: {재활용 가능한 컴포넌트 목록}

## 입력물
- {입력물 유형}: {경로 또는 설명}

## wireframe.md 경로
- {기존 wireframe.md 경로, 또는 "생성 필요"}

## 스코프
- 구현 디렉토리: {prototype/ 또는 app/(wireframe)/ 등}
- 본 프로젝트 통합 전략: {프로토타입 검증 후 이관 / 직접 프로덕션 구현}
```

### 4단계: 보고 및 승인 요청

```
📋 [TASK] Wireframe UI 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TASK.md

입력물 분류: {wireframe.md 존재 / 생성 필요}
다음 단계: {WIREFRAME / EXECUTE (wireframe.md 있을 시)}

진행할까요?
```

---

## STEP 2: WIREFRAME (wireframe.md 생성)

> wireframe.md가 이미 존재하면 이 단계를 **스킵**하고 EXECUTE로 이동한다.

**오케스트레이터가 dtp-wireframe-ui-agent를 디스패치한다.**

워커는 wireframe-builder 스킬을 읽고 실행하여 wireframe.md를 생성한다.

### 워커 디스패치 프롬프트

```
dev-task-pilot WIREFRAME 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: WIREFRAME
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}

**스킬 가이드** (읽고 프로세스를 따르라):
- wireframe-builder 스킬 (탐색 경로에서 SKILL.md를 찾아 읽어라)

**입력물**:
- {TASK.md에 기재된 입력물 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/wireframe.md}

**실행 규칙**:
1. wireframe-builder SKILL.md를 찾아 읽는다
2. SKILL.md의 프로세스에 따라 wireframe.md를 생성한다
3. 완료 시 artifact_path, summary, status를 반환한다
4. QA 에이전트는 호출하지 않는다
```

### wireframe-builder 스킬 탐색 경로

1. `{프로젝트}/.cursor/skills/wireframe-builder/SKILL.md`
2. `{프로젝트}/.claude/skills/wireframe-builder/SKILL.md`
3. `~/.cursor/skills/wireframe-builder/SKILL.md`
4. `~/.claude/skills/wireframe-builder/SKILL.md`
5. `~/.gemini/antigravity/skills/wireframe-builder/SKILL.md`

### 워커 완료 시

워커가 wireframe.md를 반환하면, **오케스트레이터가 dtp-qa-wireframe-agent를 호출**한다.
QA가 `references/wireframe-qa-guide.md`의 WIREFRAME 단계 기준(W-1~W-5)으로 검증.

```
📋 [WIREFRAME] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/wireframe.md
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-WIREFRAME.md

[QA 요약]
- 검증 항목 W-1~W-5 중 {통과}개 Pass, {경고}개 Warning
- 판정: {✅ Pass / ⚠️ Needs Revision}

승인하시면 EXECUTE (UI 구현)로 넘어갑니다.
```

---

## STEP 3: EXECUTE (UI 구현)

wireframe.md가 사용자의 승인을 받으면, **오케스트레이터가 dtp-wireframe-ui-agent를 디스패치한다.**

워커는 ui-designer 스킬을 읽고 실행하여 UI를 구현한다.

### 워커 디스패치 프롬프트

```
dev-task-pilot EXECUTE-WIREFRAME 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: EXECUTE-WIREFRAME
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/wireframe.md}

**스킬 가이드** (읽고 프로세스를 따르라):
- ui-designer 스킬 (탐색 경로에서 SKILL.md를 찾아 읽어라)

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**실행 규칙**:
1. ui-designer SKILL.md를 찾아 읽는다
2. SKILL.md의 프로세스에 따라 wireframe.md를 UI로 구현한다
3. 출력 모드: {TASK.md에 기재된 프로토타입/프로덕션}
4. 완료 시 changed_files, summary, status를 반환한다
5. QA 에이전트는 호출하지 않는다
```

### ui-designer 스킬 탐색 경로

1. `{프로젝트}/.cursor/skills/ui-designer/SKILL.md`
2. `{프로젝트}/.claude/skills/ui-designer/SKILL.md`
3. `~/.cursor/skills/ui-designer/SKILL.md`
4. `~/.claude/skills/ui-designer/SKILL.md`
5. `~/.gemini/antigravity/skills/ui-designer/SKILL.md`

### 워커 완료 시

워커가 UI 구현 결과를 반환하면, **오케스트레이터가 dtp-qa-wireframe-agent를 호출**한다.

---

## STEP 4: QA (빌드/린트 + wireframe↔코드 대조)

**오케스트레이터가 dtp-qa-wireframe-agent를 호출한다.**

QA가 `references/wireframe-qa-guide.md`의 EXECUTE 단계 기준(E-1~E-6)으로 검증.

### QA 에이전트 호출

```
dtp-qa-wireframe-agent로서 Wireframe UI EXECUTE 결과를 검증하라.

**검증 시점**: EXECUTE
**태스크 폴더**: {tasks/{NNN}-{name}/}
**wireframe.md 경로**: {tasks/{NNN}-{name}/wireframe.md}
**변경 파일 목록**: {EXECUTE 워커가 반환한 changed_files}

**QA 가이드**:
- {skills/dev-task-pilot/references/wireframe-qa-guide.md 절대 경로}

**QA 문서 저장 경로**: {tasks/{NNN}-{name}/QA-EXECUTE-UI.md}
```

### 완료 보고

QA 완료 후, 오케스트레이터가 **DONE.md를 생성**하고 사용자에게 보고:

```
📋 [EXECUTE] Wireframe UI 완료 보고

📎 산출물: {구현된 UI 파일 경로}
📎 QA 리뷰: tasks/{NNN}-{태스크명}/QA-EXECUTE-UI.md
📎 완료 리포트: tasks/{NNN}-{태스크명}/DONE.md

[QA 요약]
- 빌드: {Pass / Fail}
- 린트: {Pass / Fail}
- 화면 커버리지: {N/M 구현됨}
- 컴포넌트 대조: {N/M 일치}
- 판정: {✅ Pass / ⚠️ Needs Revision}
```

---

## 산출물 저장 구조

```
tasks/{NNN}-{태스크명}/
├── STATE.md             ← 실시간 상태 추적
├── TASK.md              ← 작업 정의서 (Wireframe 특화)
├── wireframe.md         ← wireframe-builder 산출물 (또는 기존 파일 참조)
├── QA-WIREFRAME.md      ← WIREFRAME 단계 QA 리뷰
├── QA-EXECUTE-UI.md     ← EXECUTE 단계 QA 리뷰 (빌드/린트 + 대조)
└── DONE.md              ← 완료 리포트
```

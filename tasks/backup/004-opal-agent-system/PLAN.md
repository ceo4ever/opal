# OPAL AI 에이전트 시스템 — 구현 계획

> 작성일: 2026-03-09 | 작성자: R2 | 버전: v1.0

## 1. 파일 범위

### 신규 생성 (9개)

| # | 파일 | 역할 |
|---|------|------|
| 1 | `templates/opal/bootstrapper/claude-bootstrap.md` | Claude Code 부트스트래퍼 |
| 2 | `templates/opal/bootstrapper/cursor-bootstrap.mdc` | Cursor 부트스트래퍼 |
| 3 | `templates/opal/bootstrapper/gemini-bootstrap.md` | Antigravity 부트스트래퍼 |
| 4 | `templates/opal/core/AGENT.md` | 에이전트 핵심 정의 |
| 5 | `templates/opal/core/identity-template.md` | 정체성 템플릿 |
| 6 | `templates/opal/skills/onboarding/SKILL.md` | 초기 정체성 인터뷰 스킬 |
| 7 | `templates/opal/skills/project-init/SKILL.md` | 프로젝트 에이전트 생성 스킬 |
| 8 | `templates/opal/skills/orchestrator/SKILL.md` | 프로젝트 오케스트레이션 스킬 |
| 9 | `templates/opal/templates/project-agent.md` | 프로젝트 에이전트 기본 템플릿 |

### 수정 (2개)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 10 | `scripts/install-mac.sh` | install_r2 → install_opal, 마커 전환, 메뉴 변경 |
| 11 | `CLAUDE.md` (프로젝트 루트) | R2 설명을 OPAL로 업데이트 |

### 삭제 (3개)

| # | 파일 | 이유 |
|---|------|------|
| 12 | `templates/r2/000-r2-persona.mdc` | OPAL 구조로 대체 |
| 13 | `templates/r2/claude-snippet.md` | OPAL 부트스트래퍼로 대체 |
| 14 | `templates/r2/gemini-snippet.md` | OPAL 부트스트래퍼로 대체 |

## 2. 구현 순서

```
Step 1: 소스 구조 생성 (templates/opal/ 디렉토리)
Step 2: AGENT.md + identity-template.md 작성 (core/)
Step 3: 부트스트래퍼 3개 작성 (bootstrapper/)
Step 4: 스킬 3개 작성 (skills/)
Step 5: 프로젝트 에이전트 템플릿 작성 (templates/)
Step 6: install-mac.sh 수정
Step 7: CLAUDE.md 업데이트
Step 8: 기존 R2 파일 삭제
```

## 3. 핵심 파일 설계

### 3.1 AGENT.md (에이전트 핵심 정의)

`~/.opal/AGENT.md`로 배포되는 에이전트 코어 파일. 모든 플랫폼에서 부트스트래퍼가 Read로 로드한다.

**구조**:

```markdown
# OPAL AI Agent

## 부트스트랩

1. ~/.opal/identity.md를 Read로 읽어 에이전트 정체성을 로드한다.
2. identity.md가 없으면 ~/.opal/skills/onboarding/SKILL.md를 Read로 읽어 온보딩을 시작한다.
3. 프로젝트 진입 시 {프로젝트}/.opal/AGENT.md를 확인하여 오케스트레이션 모드 결정.

## 정체성 적용

identity.md에서 읽은 정보를 기반으로:
- {name}({alias})로 자신을 인식
- 소유자를 {owner_name} 또는 {owner_alias}로 호칭
- {personality_summary} 톤으로 대화
- {traits} 성격 특성 반영

## 핵심 역할

### 1. AI 개인 비서
- 소유자의 질문, 아이디어 정리, 기술 판단 지원
- 일상 업무 및 단순 작업 직접 수행
- 주도적 제안 (위험 감지, 개선, 맥락 연결, 범위 확인)

### 2. 프로젝트 오케스트레이터
- 프로젝트 에이전트가 있으면 오케스트레이션 모드
  → ~/.opal/skills/orchestrator/SKILL.md 읽어 실행
- 없으면 직접 수행 또는 프로젝트 에이전트 생성 제안
  → ~/.opal/skills/project-init/SKILL.md 읽어 실행

## 행동 규칙

### 주도성
- 위험 감지: 잠재적 문제 발견 시 즉시 알림
- 개선 제안: 더 나은 방법이 있으면 근거와 함께 제시
- 맥락 연결: 이전 작업/기존 코드 관련 사항 연결
- 범위 확인: 모호하거나 범위가 클 때 정리 후 확인
- 최종 결정은 항상 소유자에게

### 보고 형식

간단 보고 (소규모):
> **{name}**: {완료 내용 1줄}. {후속 질문}

상세 보고 (다단계):
---
**{name} 보고**
{작업 요약 1-2줄}
- 수행 내용: {핵심 변경}
- 산출물: {파일 경로}
- 특이 사항: {있으면 기재}
다음은 어떻게 할까요?
---

## 스킬 참조

### 플랫폼 스킬 (각 AI 플랫폼 디렉토리에서 탐색)
- task-flow, api-analyzer, doc-writer, interview, version-mgr, wireframe-builder
- task-flow-qa, task-flow-planner, task-flow-test

### OPAL 전용 스킬 (~/.opal/skills/)
- onboarding: 초기 정체성 인터뷰
- project-init: 프로젝트 에이전트 생성
- orchestrator: 프로젝트 오케스트레이션
```

### 3.2 부트스트래퍼

#### Claude (claude-bootstrap.md)

스니핏 형식 (마커 기반 삽입용):

```markdown
# OPAL 부트스트래퍼 (Claude Code)

> 사용법: 이 내용을 `~/.claude/CLAUDE.md`에 추가한다.

---

아래 내용을 복사하여 `~/.claude/CLAUDE.md`에 추가:

---

\```markdown
# OPAL AI Agent

세션 시작 시 ~/.opal/AGENT.md를 Read로 읽어 AI 에이전트로 활성화한다.
파일이 없으면 ~/.opal/skills/onboarding/SKILL.md를 읽어 온보딩을 시작한다.
\```
```

#### Cursor (cursor-bootstrap.mdc)

```yaml
---
description: OPAL AI 에이전트 부트스트래퍼. 세션 시작 시 에이전트를 활성화한다.
globs:
alwaysApply: true
---

# OPAL AI Agent

세션 시작 시 ~/.opal/AGENT.md를 Read로 읽어 AI 에이전트로 활성화한다.
파일이 없으면 ~/.opal/skills/onboarding/SKILL.md를 읽어 온보딩을 시작한다.
```

#### Antigravity (gemini-bootstrap.md)

Claude와 동일 구조, 대상 파일만 `~/.gemini/GEMINI.md`로 변경.

### 3.3 온보딩 스킬 (onboarding/SKILL.md)

```yaml
---
name: onboarding
description: |
  OPAL AI 에이전트 초기 정체성 설정 스킬.
  ~/.opal/identity.md가 없을 때 자동 실행되어, 사용자와 인터뷰를 통해 에이전트 정체성을 정의한다.
---
```

**프로세스**:
1. 환영 메시지 출력 (OPAL 소개)
2. Round 1: 기본 정체성 질문 (name, alias, owner_name, owner_alias, personality_summary)
3. Round 2: 성격 디테일 (tone, role_summary, traits) — 선택적 확장
4. identity-template.md를 기반으로 identity.md 생성
5. 생성된 정체성 확인 → 사용자 승인
6. 완료 보고

### 3.4 프로젝트 초기화 스킬 (project-init/SKILL.md)

**프로세스**:
1. 프로젝트 구조 분석 (package.json, requirements.txt, 기존 설정 파일 등)
2. 프로젝트 스택/규칙 인터뷰 (필요 시)
3. project-agent.md 템플릿 기반으로 `{프로젝트}/.opal/AGENT.md` 생성
4. 생성된 에이전트 정의 확인 → 사용자 승인

### 3.5 오케스트레이터 스킬 (orchestrator/SKILL.md)

**프로세스**:
1. `{프로젝트}/.opal/AGENT.md` Read
2. 사용자 지시를 프로젝트 에이전트 컨텍스트에 맞게 해석
3. 서브에이전트(Task 도구)로 프로젝트 에이전트 실행
   - Antigravity: 서브에이전트 미지원 → 동일 컨텍스트에서 프로젝트 에이전트 규칙 적용하여 실행
4. 결과 수신 및 품질 검토
5. 사용자에게 보고

### 3.6 프로젝트 에이전트 템플릿 (project-agent.md)

```markdown
# {프로젝트명} 프로젝트 에이전트

## 프로젝트 개요
- 이름: {프로젝트명}
- 기술 스택: {스택}
- 주요 디렉토리: {구조}

## 프로젝트 규칙
- 코드 컨벤션: {컨벤션}
- 브랜치 전략: {전략}
- 테스트 정책: {정책}

## 작업 수행 규칙
이 에이전트는 OPAL 에이전트의 지시를 받아 작업을 수행한다.
1. 지시 수신 → 작업 범위 확인
2. 작업 수행 → 결과 반환
3. 불명확한 점이 있으면 질문으로 반환
```

### 3.7 install-mac.sh 변경

**핵심 변경사항**:

1. 마커 상수 변경:
   ```bash
   OPAL_START="# === OPAL START ==="
   OPAL_END="# === OPAL END ==="
   R2_START="# === R2 START ==="   # 하위 호환용
   R2_END="# === R2 END ==="       # 하위 호환용
   ```

2. `install_r2` → `install_opal`:
   - 부트스트래퍼 3개 설치 (기존 마커 방식 유지)
   - `~/.opal/`에 core + skills + templates 설치

3. `install_opal_section`: R2 마커도 인식하여 OPAL로 교체

4. 메뉴 변경:
   ```
   [4] R2 알투 (AI 파트너 페르소나) → [4] OPAL (AI 에이전트)
   ```

5. `print_summary` 업데이트:
   ```
   ~/.opal/ 경로 표시
   ```

## 4. 배포 결과 검증

설치 후 예상 파일 구조:

```
~/.opal/
├── AGENT.md               ← 에이전트 핵심 정의
├── identity.md            ← (온보딩 후 생성)
├── skills/
│   ├── onboarding/SKILL.md
│   ├── project-init/SKILL.md
│   └── orchestrator/SKILL.md
└── templates/
    ├── identity-template.md
    └── project-agent.md

~/.claude/CLAUDE.md        ← OPAL 부트스트래퍼 섹션 포함
~/.cursor/rules/000-opal-agent.mdc  ← OPAL 부트스트래퍼
~/.gemini/GEMINI.md        ← OPAL 부트스트래퍼 섹션 포함
```

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-09 | R2 | 최초 작성 — 9개 신규 파일, 2개 수정, 3개 삭제 계획 |

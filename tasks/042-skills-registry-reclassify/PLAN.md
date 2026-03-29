# PLAN: 컴포넌트 리네이밍 + 레거시 정리

> 작성일: 2026-03-29
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/otp-*/` (5개 디렉토리, 7파일) | 오케스트레이터 스킬 | 예 (rename + 내부 참조) |
| `skills/dtp-*/` (8개 디렉토리, 28파일) | 단계 스킬 | 예 (rename + 내부 참조) |
| `agents/dtp-worker/` | 범용 워커 | 예 (rename + 내부) |
| `agents/dtp-qa-worker/` | QA 워커 | 예 (rename + 내부) |
| `agents/dtp-test-worker/` | Test 워커 | 예 (rename + 내부) |
| `agents/wtm-worker/` | WTM 워커 | 예 (rename + 내부) |
| `skills/dev-task-pilot/` (12파일) | 레거시 오케스트레이터 | 삭제 |
| `agents/dtp-dev-agent/` 외 5개 | 레거시 에이전트 | 삭제 |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 (SSOT) | 예 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | 예 |
| `opal/core/references/opal-harness.md` | 하네스 | 예 |
| `opal/core/AGENT.md` | 글로벌 에이전트 | 예 |
| `CLAUDE.md` | 소스 구조 설명 | 예 |
| `README.md` | 프로젝트 소개 | 예 |
| `skills/opal-project-init/SKILL.md` | 프로젝트 초기화 | 예 (참조) |
| `opal/skills/opal-project-dev-pilot/SKILL.md` | 프로젝트 파일럿 | 예 (참조) |
| `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` | 로드맵 가이드 | 예 (약어) |
| `opal/skills/opal-agent-creator/SKILL.md` | 에이전트 생성기 | 예 (참조) |
| `skills/web-to-markdown/SKILL.md` | WTM 스킬 | 예 (wtm-worker 참조) |
| `opal/tools/skill-registry/skill-registry.js` | CLI 도구 | 아니오 (데이터 드리븐) |
| `scripts/install-mac.sh` | 설치 스크립트 | 아니오 (clean deploy) |

### 현재 구현

**JSON 레지스트리** (`opal-skills-registry.json`):
- v2.0.0, 그룹 구조: `otp` (5개), `dtp` (8개), `standalone` (5개), `opal` (7개) = 25개
- `dispatched_by` 필드에 오케스트레이터명 참조 (dtp 그룹)
- `paths` 필드에 디렉토리 경로 포함

**skill-registry.js**:
- `flattenGroups()`로 JSON 그룹을 플랫 배열로 변환 — 그룹명을 `_group` 필드로 보존
- `list --group=X`로 그룹 필터링
- **그룹명이 코드에 하드코딩되지 않음** — JSON 데이터만 변경하면 됨

**각 SKILL.md 내부**:
- YAML frontmatter `name` 필드
- description에 트리거 약어 포함
- 본문에서 다른 스킬/에이전트를 정식명으로 참조

### 영향 범위

- **디렉토리 rename**: 스킬 13개 + 에이전트 4개 = 17개
- **디렉토리 삭제**: 스킬 1개 + 에이전트 6개 = 7개
- **파일 수정**: 40+ 파일 (대부분 find-replace)
- **install-mac.sh**: 변경 불필요 (clean deploy 방식 — 소스 삭제/rename 시 자동 반영)
- **skill-registry.js**: 변경 불필요 (데이터 드리븐)

## 2. 구현 계획

### 리네이밍 매핑 (전체)

**오케스트레이터**:

| 현재 | 변경 후 | 약어 |
|------|--------|------|
| otp-dev | opal-pilot-dev | opd |
| otp-dev-short | opal-pilot-dev-short | opds |
| otp-wf | opal-pilot-dev-wireframe | opdw |
| otp-write | opal-pilot-write | opw |
| otp-write-tech | opal-pilot-write-tech | opwt |

**단계 스킬 (dev)**:

| 현재 | 변경 후 |
|------|--------|
| dtp-analysis | op-dev-analysis |
| dtp-plan | op-dev-plan |
| dtp-todo | op-dev-todo |
| dtp-test-scenario | op-dev-test-scenario |
| dtp-execute | op-dev-execute |
| dtp-wireframe | op-dev-wireframe |

**단계 스킬 (범용)**:

| 현재 | 변경 후 |
|------|--------|
| dtp-task | op-task |
| dtp-qa | op-task-qa |

**에이전트**:

| 현재 | 변경 후 |
|------|--------|
| dtp-worker | op-dev-agent |
| dtp-qa-worker | op-task-qa-agent |
| dtp-test-worker | op-dev-test-agent |
| wtm-worker | wtm-agent |

**JSON 그룹 키**:

| 현재 | 변경 후 |
|------|--------|
| otp | opal-pilot |
| dtp | op-dev + op-task (분리) |
| standalone | standalone (유지) |
| opal | opal (유지) |

### 파일 변경 계획

#### 삭제

| # | 파일 경로 | 이유 |
|---|----------|------|
| D1 | `skills/dev-task-pilot/` (12파일) | 레거시 오케스트레이터 |
| D2 | `agents/dtp-dev-agent/` | 레거시 → op-dev-agent로 대체 |
| D3 | `agents/dtp-qa-dev-agent/` | 레거시 → op-task-qa-agent로 대체 |
| D4 | `agents/dtp-dev-test-agent/` | 레거시 → op-dev-test-agent로 대체 |
| D5 | `agents/dtp-wireframe-ui-agent/` | 레거시 → op-dev-agent로 대체 |
| D6 | `agents/dtp-qa-wireframe-agent/` | 레거시 → op-task-qa-agent로 대체 |
| D7 | `agents/dtp-action-plan-agent/` | 레거시 → op-dev-agent로 대체 |

#### 디렉토리 rename

| # | 현재 | 변경 후 |
|---|------|--------|
| R1 | `skills/otp-dev/` | `skills/opal-pilot-dev/` |
| R2 | `skills/otp-dev-short/` | `skills/opal-pilot-dev-short/` |
| R3 | `skills/otp-wf/` | `skills/opal-pilot-dev-wireframe/` |
| R4 | `skills/otp-write/` | `skills/opal-pilot-write/` |
| R5 | `skills/otp-write-tech/` | `skills/opal-pilot-write-tech/` |
| R6 | `skills/dtp-task/` | `skills/op-task/` |
| R7 | `skills/dtp-analysis/` | `skills/op-dev-analysis/` |
| R8 | `skills/dtp-plan/` | `skills/op-dev-plan/` |
| R9 | `skills/dtp-todo/` | `skills/op-dev-todo/` |
| R10 | `skills/dtp-test-scenario/` | `skills/op-dev-test-scenario/` |
| R11 | `skills/dtp-execute/` | `skills/op-dev-execute/` |
| R12 | `skills/dtp-wireframe/` | `skills/op-dev-wireframe/` |
| R13 | `skills/dtp-qa/` | `skills/op-task-qa/` |
| R14 | `agents/dtp-worker/` | `agents/op-dev-agent/` |
| R15 | `agents/dtp-qa-worker/` | `agents/op-task-qa-agent/` |
| R16 | `agents/dtp-test-worker/` | `agents/op-dev-test-agent/` |
| R17 | `agents/wtm-worker/` | `agents/wtm-agent/` |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/core/references/opal-skills-registry.json` | 그룹 키(otp→opal-pilot, dtp→op-dev+op-task), 각 스킬 name/alias/triggers/paths/dispatched_by |
| M2 | `opal/core/references/agents.md` | 에이전트 이름/설명 갱신, 레거시 제거 |
| M3 | `opal/core/references/opal-harness.md` | dtp-qa→op-task-qa, dtp-task→op-task 참조 + 용어 정의 섹션 추가 |
| M4 | `opal/core/AGENT.md` | `//` 커맨드 예시 약어 갱신 (otpd→opd 등) |
| M5 | `CLAUDE.md` | 소스 구조 디렉토리명 + 컴포넌트 의존 관계 + 레거시 표기 제거 |
| M6 | `README.md` | 에이전트 테이블, 스킬 설명 갱신 |
| M7-M11 | 각 오케스트레이터 SKILL.md (5개) | YAML name, description, 디스패치 경로, 에이전트 참조 |
| M12-M19 | 각 단계 스킬 SKILL.md (8개) | YAML name, description, dispatched_by 서술 |
| M20-M23 | 각 에이전트 AGENT.md (4개) | YAML name, description, 스킬 참조 |
| M24 | `skills/opal-project-init/SKILL.md` | otp-* 참조를 opal-pilot-* 으로 |
| M25 | `opal/skills/opal-project-dev-pilot/SKILL.md` | otp-*/dtp-* 참조 + 약어 |
| M26 | `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` | 약어 갱신 (otpd→opd 등) |
| M27 | `opal/skills/opal-agent-creator/SKILL.md` | dtp-qa, wtm-worker 참조 |
| M28 | `skills/web-to-markdown/SKILL.md` | wtm-worker → wtm-agent |
| M29 | `opal/core/references/skills.md` | dtp-analysis 등 참조 갱신 |

### 구현 순서

| 순서 | 작업 | 파일 수 | 예상 난이도 |
|------|------|--------|-----------|
| 1 | 레거시 삭제 | 7 디렉토리 | 쉬움 |
| 2 | 디렉토리 rename | 17 디렉토리 | 쉬움 |
| 3 | SKILL.md/AGENT.md 내부 수정 | 17 파일 | 보통 (반복) |
| 4 | JSON 레지스트리 갱신 | 1 파일 | 보통 |
| 5 | 레지스트리/하네스 문서 갱신 | 3 파일 | 보통 |
| 6 | 프로젝트 문서 갱신 | 2 파일 (CLAUDE.md, README.md) | 보통 |
| 7 | 기타 스킬 참조 갱신 | 5 파일 | 쉬움 (find-replace) |
| 8 | 글로벌 AGENT.md + 용어 정의 | 1 파일 | 쉬움 |
| 9 | 검증 | - | 쉬움 |

### 핵심 설계

#### 용어 정의 (opal-harness.md에 추가)

```markdown
## 0. 용어 정의

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| opal-pilot | OPAL Pilot | 태스크 파이프라인을 조종하는 오케스트레이터 |
| op-dev | OPAL Pilot Dev Phase | dev 도메인 단계 스킬 (코드 변경 수반) |
| op-task | OPAL Pilot Task Phase | 범용 단계 스킬 (도메인 무관) |
| opd / opds / opdw | OPAL Pilot Dev 약어 | Full / Short / Wireframe |
| opw / opwt | OPAL Pilot Write 약어 | Write / Write-Tech |
```

#### JSON 그룹 구조 (변경 후)

```json
{
  "groups": {
    "opal-pilot": [ ...5개 오케스트레이터... ],
    "op-dev": [ ...6개 dev 단계 스킬... ],
    "op-task": [ ...2개 범용 단계 스킬... ],
    "standalone": [ ...5개 독립 스킬... ],
    "opal": [ ...7개 OPAL 관리 스킬... ]
  }
}
```

### 의존성 및 환경 변경

- 없음. 순수 rename + 문서 수정.

### 테스트 전략

| 테스트 | 방법 | 성공 기준 |
|--------|------|----------|
| JSON 유효성 | `node skill-registry.js validate` | valid: true, 25개 (삭제 후 동일) |
| 약어 매칭 | `node skill-registry.js match "//opds"` | found: true, name: opal-pilot-dev-short |
| 그룹 필터 | `node skill-registry.js list --group=opal-pilot` | 5개 |
| 그룹 필터 | `node skill-registry.js list --group=op-dev` | 6개 |
| 그룹 필터 | `node skill-registry.js list --group=op-task` | 2개 |
| 경로 존재 | validate의 warnings | op-* 경로에 SKILL.md 존재 확인 |
| 레거시 부재 | `ls skills/dev-task-pilot` | 존재하지 않음 |
| 레거시 부재 | `ls agents/dtp-dev-agent` | 존재하지 않음 |

## 3. 실행 체크리스트

> 총 9개 Step | 실행 모드: 단순

### Step 1: 레거시 삭제
- [ ] 완료
- **파일**: `skills/dev-task-pilot/`, `agents/dtp-dev-agent/`, `agents/dtp-qa-dev-agent/`, `agents/dtp-dev-test-agent/`, `agents/dtp-wireframe-ui-agent/`, `agents/dtp-qa-wireframe-agent/`, `agents/dtp-action-plan-agent/`
- **작업 내용**: 7개 디렉토리 삭제 (rm -rf)
- **완료 기준**: 해당 디렉토리가 존재하지 않음
- **테스트**: `ls skills/dev-task-pilot 2>&1` → "No such file"
- **실행 방법**: direct
- **의존**: 없음

### Step 2: 디렉토리 rename
- [ ] 완료
- **파일**: skills/ 13개 + agents/ 4개 = 17개 디렉토리
- **작업 내용**: git mv로 17개 디렉토리 rename (리네이밍 매핑 테이블 참조)
- **완료 기준**: 새 이름으로 디렉토리 존재, 기존 이름 없음
- **테스트**: `ls skills/opal-pilot-dev/SKILL.md` → 존재
- **실행 방법**: direct
- **의존**: Step 1

### Step 3: SKILL.md / AGENT.md 내부 수정 (17파일)
- [ ] 완료
- **파일**: 오케스트레이터 SKILL.md 5개, 단계 스킬 SKILL.md 8개, 에이전트 AGENT.md 4개
- **작업 내용**:
  - YAML frontmatter `name` 필드 갱신
  - `description` 내 약어/트리거 갱신
  - 본문 내 다른 스킬/에이전트 참조를 새 이름으로 변경
  - dispatched_by 서술 갱신 (단계 스킬)
  - 디스패치 경로 갱신 (오케스트레이터)
  - 변경이력에 리네이밍 이력 추가
- **완료 기준**: 모든 SKILL.md/AGENT.md에서 otp-*/dtp-*/worker 문자열이 사라짐
- **테스트**: `grep -r "otp-dev\|dtp-" skills/ agents/ --include="*.md"` → 매치 없음
- **실행 방법**: direct
- **의존**: Step 2

### Step 4: JSON 레지스트리 갱신
- [ ] 완료
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**:
  - 그룹 키: otp → opal-pilot, dtp → op-dev + op-task (분리)
  - 각 스킬: name, alias, triggers, paths 갱신
  - dtp 그룹의 dispatched_by를 새 오케스트레이터명으로
  - version 범프 (2.0.0 → 3.0.0)
- **완료 기준**: `node skill-registry.js validate` → valid: true
- **테스트**: validate + match "//opds" + list --group=opal-pilot
- **실행 방법**: direct
- **의존**: Step 2

### Step 5: 레지스트리/하네스 문서 갱신
- [ ] 완료
- **파일**: `opal/core/references/agents.md`, `opal/core/references/opal-harness.md`, `opal/core/references/skills.md`
- **작업 내용**:
  - agents.md: 레거시 에이전트 제거, 신규 에이전트명 반영
  - opal-harness.md: dtp-qa→op-task-qa, dtp-task→op-task + 용어 정의 섹션 추가
  - skills.md: dtp-analysis 등 기술 스택 추천 내 참조 갱신
- **완료 기준**: 각 문서에서 dtp-*/otp-* 문자열이 사라짐
- **테스트**: `grep -r "otp-\|dtp-" opal/core/references/ --include="*.md"` → 매치 없음
- **실행 방법**: direct
- **의존**: Step 1, 2

### Step 6: 프로젝트 문서 갱신 (CLAUDE.md, README.md)
- [ ] 완료
- **파일**: `CLAUDE.md`, `README.md`
- **작업 내용**:
  - CLAUDE.md: 소스 구조 디렉토리명, 컴포넌트 의존 관계, 레거시 표기 제거
  - README.md: 에이전트 테이블, 스킬 설명 갱신
- **완료 기준**: 두 문서에서 dev-task-pilot/otp-*/dtp-*/*-worker 문자열이 사라짐
- **테스트**: `grep "dev-task-pilot\|otp-\|dtp-\|worker" CLAUDE.md README.md` → 매치 없음
- **실행 방법**: direct
- **의존**: Step 1, 2

### Step 7: 기타 스킬 참조 갱신
- [ ] 완료
- **파일**: `skills/opal-project-init/SKILL.md`, `opal/skills/opal-project-dev-pilot/SKILL.md`, `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md`, `opal/skills/opal-agent-creator/SKILL.md`, `skills/web-to-markdown/SKILL.md`
- **작업 내용**: otp-*/dtp-*/약어/wtm-worker 참조를 새 이름으로 변경
- **완료 기준**: 해당 파일에서 old 이름 사라짐
- **테스트**: grep 확인
- **실행 방법**: direct
- **의존**: Step 2

### Step 8: 글로벌 AGENT.md 갱신
- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: `//` 커맨드 예시 약어 (otpds→opds 등) 갱신
- **완료 기준**: 커맨드 예시가 새 약어 사용
- **테스트**: grep 확인
- **실행 방법**: direct
- **의존**: Step 2

### Step 9: 최종 검증
- [ ] 완료
- **파일**: -
- **작업 내용**:
  - `node opal/tools/skill-registry/skill-registry.js validate` 실행
  - `node opal/tools/skill-registry/skill-registry.js match "//opds"` 테스트
  - `node opal/tools/skill-registry/skill-registry.js list --group=opal-pilot` 테스트
  - 프로젝트 전체에서 old 이름 잔존 검색 (tasks/ 제외)
- **완료 기준**: validate 통과, match 정상, old 이름 잔존 없음
- **테스트**: 위 명령어 모두 성공
- **실행 방법**: direct
- **의존**: Step 3, 4, 5, 6, 7, 8

## 4. QA 체크리스트

### 기능 테스트
- [ ] JSON validate → valid: true, 25개 스킬
- [ ] match "//opd" → opal-pilot-dev
- [ ] match "//opds" → opal-pilot-dev-short
- [ ] match "//opdw" → opal-pilot-dev-wireframe
- [ ] match "//opw" → opal-pilot-write
- [ ] match "//opwt" → opal-pilot-write-tech
- [ ] list --group=opal-pilot → 5개
- [ ] list --group=op-dev → 6개
- [ ] list --group=op-task → 2개
- [ ] 모든 SKILL.md 경로가 존재 (validate warnings 0)

### 회귀 테스트
- [ ] 커뮤니티 스킬 매칭 정상 (community-skills-registry.json 미변경)
- [ ] standalone 스킬 매칭 정상
- [ ] install-mac.sh 변경 없음 확인

### 코드 품질
- [ ] old 이름 잔존 없음 (tasks/ 제외, grep 전수 검색)
- [ ] JSON 구조 일관성 (그룹 키와 스킬 데이터 정합)
- [ ] 용어 정의가 opal-harness.md에 문서화됨

### 보안
- [ ] 코드에 하드코딩된 토큰/시크릿이 없는가
- [ ] .env 파일이 .gitignore에 포함되어 있는가

## 5. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 |
| 변경 파일 수 | 40+개 | 복잡 |
| 모듈 범위 | 다중 (skills, agents, references, docs) | 복잡 |
| 작업 유형 | 리팩토링 (rename) | 단순 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **단순** | 파일 수는 많지만 모든 작업이 find-replace 패턴의 반복. Step 간 의존이 직선이고, 의사결정 포인트 없음 |

## 6. 실행 아키텍처 (복잡 모드 시)

해당 없음 (단순 모드).

## 7. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 데이터 | JSON | 없음 (직접 편집) |
| 문서 | Markdown | 없음 |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 미사용으로 MCP 조회 불필요 |

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| old 이름 잔존 | 부트스트랩/디스패치 시 경로 오류 | Step 9에서 전수 grep 검증 |
| 배포본(~/.opal/) 동기화 | install-mac.sh 재실행 전까지 구버전 유지 | 완료 후 install-mac.sh 재실행 안내 |
| 메모리 파일 내 old 이름 | 과거 기록과 불일치 | 메모리는 이력이므로 수정하지 않음 — 새 세션에서 자연스럽게 갱신 |
| .claude/settings.json 약어 | 훅 규칙 미작동 | 캡틴에게 수동 갱신 안내 |

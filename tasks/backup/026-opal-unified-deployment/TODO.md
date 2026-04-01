# TODO: OPAL 프레임워크 배포 구조 통합 -- ~/.opal/ 단일 배포

> 작성일: 2026-03-21 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 13개 Step | 실행 모드: 복잡

### Step 1: 소스 agents/ 디렉토리 플랫화 -- Claude 포맷 이동
- [x] 완료
- **파일**: `agents/claude/*` -> `agents/`
- **작업 내용**: `agents/claude/` 하위 7개 에이전트 디렉토리(dtp-dev-agent, dtp-wireframe-ui-agent, dtp-qa-dev-agent, dtp-qa-wireframe-agent, dtp-action-plan-agent, dtp-dev-test-agent, wtm-worker)를 `agents/`로 `git mv`
- **완료 기준**: `agents/dtp-dev-agent/AGENT.md` 등 7개 디렉토리가 `agents/` 직하에 존재
- **테스트**: `ls agents/*/AGENT.md` 결과 7개 파일 확인
- **실행 방법**: direct
- **의존**: 없음

### Step 2: 소스 agents/ 디렉토리 플랫화 -- Cursor/Antigravity 삭제
- [x] 완료
- **파일**: `agents/cursor/`, `agents/antigravity/`
- **작업 내용**: `git rm -r agents/cursor/ agents/antigravity/`
- **완료 기준**: `agents/cursor/`, `agents/antigravity/` 디렉토리 존재하지 않음
- **테스트**: `ls agents/` 결과에 `cursor/`, `antigravity/` 없음
- **실행 방법**: direct
- **의존**: Step 1

### Step 3: OPAL 전용 스킬 opal- 접두사 적용
- [x] 완료
- **파일**: `opal/skills/{onboarding,orchestrator,project-init,skill-manager}/`
- **작업 내용**: 4개 디렉토리를 `git mv`로 opal- 접두사 적용. `onboarding` -> `opal-onboarding`, `orchestrator` -> `opal-orchestrator`, `project-init` -> `opal-project-init`, `skill-manager` -> `opal-skill-manager`
- **완료 기준**: `opal/skills/opal-onboarding/SKILL.md` 등 4개 디렉토리 존재
- **테스트**: `ls opal/skills/` 결과에 opal- 접두사 디렉토리 4개 확인
- **실행 방법**: direct
- **의존**: 없음

### Step 4: OPAL 코어 경로 수정 -- AGENT.md
- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: OPAL 전용 스킬 참조 경로를 opal- 접두사로 변경. `~/.opal/skills/onboarding/` -> `~/.opal/skills/opal-onboarding/`, `~/.opal/skills/orchestrator/` -> `~/.opal/skills/opal-orchestrator/`, `~/.opal/skills/project-init/` -> `~/.opal/skills/opal-project-init/`
- **완료 기준**: AGENT.md 내 onboarding, orchestrator, project-init 경로가 모두 opal- 접두사 포함
- **테스트**: `grep -c 'skills/onboarding\|skills/orchestrator\|skills/project-init' opal/core/AGENT.md` 결과 0
- **실행 방법**: direct
- **의존**: Step 3

### Step 5: OPAL 부트스트래퍼 경로 수정
- [x] 완료
- **파일**: `opal/bootstrapper/cursor-bootstrap.mdc`
- **작업 내용**: OPAL 전용 스킬 참조 경로를 opal- 접두사로 변경. `~/.opal/skills/onboarding/` -> `~/.opal/skills/opal-onboarding/`
- **완료 기준**: cursor-bootstrap.mdc 내 `skills/onboarding/` 참조가 `skills/opal-onboarding/`으로 변경됨
- **테스트**: `grep 'opal-onboarding' opal/bootstrapper/cursor-bootstrap.mdc` 매치 존재
- **실행 방법**: direct
- **의존**: Step 3

### Step 6: 참조 레지스트리 수정 -- skills.md
- [x] 완료
- **파일**: `opal/core/references/skills.md`
- **작업 내용**: (1) 프레임워크 스킬 탐색 경로 5개 -> 2개로 축소 (`{프로젝트}/.opal/skills/` + `~/.opal/skills/`). (2) OPAL 전용 스킬 경로를 opal- 접두사로 변경
- **완료 기준**: 탐색 경로가 2개이고, OPAL 전용 스킬이 opal- 접두사 사용
- **테스트**: `grep -c '~/.claude/skills\|~/.cursor/skills\|~/.gemini' opal/core/references/skills.md` 결과 0
- **실행 방법**: direct
- **의존**: Step 3

### Step 7: 참조 레지스트리 수정 -- agents.md
- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: 에이전트 탐색 경로 8개 -> 2개로 축소 (`{프로젝트}/.opal/agents/` + `~/.opal/agents/`). wtm-worker 에이전트가 누락되어 있으면 추가
- **완료 기준**: 탐색 경로가 2개이고, 플랫폼별 경로 없음
- **테스트**: `grep -c '~/.claude/agents\|~/.cursor/agents\|~/.gemini' opal/core/references/agents.md` 결과 0
- **실행 방법**: direct
- **의존**: Step 1

### Step 8: 스킬 내 탐색 경로 수정 -- dev-task-pilot
- [x] 완료
- **파일**: `skills/dev-task-pilot/SKILL.md`, `skills/dev-task-pilot/modes/wireframe-ui.md`, `skills/dev-task-pilot/references/execute-plan-guide.md`
- **작업 내용**: (1) SKILL.md의 에이전트 탐색 경로 8개 -> 2개. (2) wireframe-ui.md의 스킬 탐색 경로 2곳 각각 5개 -> 2개. (3) execute-plan-guide.md의 스킬 탐색 경로 4개 -> 2개
- **완료 기준**: 3개 파일 모두에서 플랫폼별 경로 제거, `~/.opal/` 경로만 존재
- **테스트**: `grep -rn '~/.claude/\|~/.cursor/\|~/.gemini/' skills/dev-task-pilot/` 결과 0줄
- **실행 방법**: sub-agent
- **의존**: Step 1

### Step 9: 스킬 내 탐색 경로 수정 -- web-to-markdown, opal-agent-creator
- [x] 완료
- **파일**: `skills/web-to-markdown/SKILL.md`, `skills/opal-agent-creator/SKILL.md`
- **작업 내용**: (1) web-to-markdown의 에이전트 탐색 경로 6개 -> 2개. (2) opal-agent-creator의 에이전트 탐색 경로 템플릿 8개 -> 2개
- **완료 기준**: 2개 파일에서 플랫폼별 경로 제거
- **테스트**: `grep -c '~/.claude/agents\|~/.cursor/agents\|~/.gemini/' skills/web-to-markdown/SKILL.md skills/opal-agent-creator/SKILL.md` 결과 0
- **실행 방법**: sub-agent
- **의존**: Step 1

### Step 10: install-mac.sh 전면 재설계
- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: (1) 메뉴 구조를 3개로 재설계: [1] OPAL 설치, [2] MCP 서버 설정, [3] 전체 설치, [0] 종료. (2) `install_claude()`, `install_cursor()`, `install_antigravity()` 함수 삭제. (3) `install_opal()` 확장: 프레임워크 스킬(`skills/` -> `~/.opal/skills/`), OPAL 전용 스킬(`opal/skills/` -> `~/.opal/skills/`), 에이전트(`agents/` -> `~/.opal/agents/`) 배포 추가. hooks 설정 이관. (4) `print_cleanup_notice()` 추가: 레거시 배포 경로 정리 안내. (5) 배너, `print_summary()` 업데이트
- **완료 기준**: 스크립트 실행 시 새 메뉴 표시, `~/.opal/`로 통합 배포, 레거시 정리 안내 출력
- **테스트**: `bash -n scripts/install-mac.sh` 문법 검증 통과. 실행 후 `~/.opal/skills/` 14개 + `~/.opal/agents/` 7개 디렉토리 확인
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3

### Step 11: CLAUDE.md 아키텍처 설명 업데이트
- [x] 완료
- **파일**: `CLAUDE.md`
- **작업 내용**: (1) 소스 구조 다이어그램: `agents/` 플랫화 반영, `opal/skills/` opal- 접두사 반영. (2) 배포 구조 다이어그램: `~/.opal/` 단일 배포로 변경, `~/.claude/`, `~/.cursor/`, `~/.gemini/`에서 skills/agents 제거 (MCP + 부트스트래퍼만 유지). (3) 컴포넌트 유형 테이블: 에이전트 수 `7개 x 1포맷`으로 변경. (4) 에이전트 추가 가이드: 단일 `agents/{name}/AGENT.md` 생성으로 변경
- **완료 기준**: CLAUDE.md의 소스 구조, 배포 구조, 컴포넌트 테이블, 에이전트 추가 가이드가 통합 구조 반영
- **테스트**: `grep -c 'agents/claude\|agents/cursor\|agents/antigravity' CLAUDE.md` 결과 0
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3

### Step 12: README.md 업데이트
- [x] 완료
- **파일**: `README.md`
- **작업 내용**: (1) 2계층 아키텍처 다이어그램에서 플랫폼별 배포 경로를 `~/.opal/` 단일 경로로 변경. (2) 설치 가이드 메뉴를 3개 항목으로 변경. (3) 플랫폼별 수동 설치 명령 제거
- **완료 기준**: README.md에 플랫폼별 스킬/에이전트 배포 경로 없음, 새 메뉴 구조 반영
- **테스트**: `grep -c '~/.claude/skills\|~/.cursor/skills\|~/.gemini/antigravity/skills' README.md` 결과 0
- **실행 방법**: sub-agent
- **의존**: Step 10, Step 11

### Step 13: 전체 검증
- [x] 완료
- **파일**: 전체
- **작업 내용**: (1) 소스 agents/ 구조 최종 확인 (7개 에이전트 디렉토리, 플랫폼 하위 없음). (2) 모든 파일에서 레거시 플랫폼별 글로벌 경로가 탐색 경로에서 제거되었는지 grep 확인. (3) opal- 접두사 적용 완전성 확인. (4) install-mac.sh 문법 검증
- **완료 기준**: 모든 검증 통과
- **테스트**: (a) `ls agents/` 7개 디렉토리만 존재. (b) 글로벌 탐색 경로에 `~/.claude/skills`, `~/.cursor/skills`, `~/.gemini/antigravity/skills`, `~/.claude/agents`, `~/.cursor/agents` 없음 (프로젝트 레벨 경로는 허용). (c) `bash -n scripts/install-mac.sh` 통과
- **실행 방법**: direct
- **의존**: Step 1~12 전체

---

## Part B: QA 체크리스트

### B-1. 기능 테스트
- [ ] `~/.opal/skills/` 하위에 프레임워크 스킬 10개 + OPAL 전용 스킬 4개 = 14개 디렉토리 배포 확인
- [ ] `~/.opal/agents/` 하위에 에이전트 7개 디렉토리 배포 확인
- [ ] 부트스트래퍼가 Claude/Cursor/Gemini에 기존대로 설치되는지 확인
- [ ] MCP 설정이 기존대로 플랫폼별 동작하는지 확인
- [ ] Claude Code hooks 설정이 기존대로 머지되는지 확인
- [ ] 레거시 정리 안내 메시지가 기존 배포 경로 존재 시 출력되는지 확인
- [ ] 탐색 경로가 모든 파일에서 2계층(`{프로젝트}/.opal/` + `~/.opal/`)으로 통일되었는지 확인
- [ ] OPAL 전용 스킬이 opal- 접두사로 일관되게 참조되는지 확인

### B-2. 회귀 테스트
- [ ] OPAL 부트스트래퍼(CLAUDE.md, .cursorrules, GEMINI.md 삽입)가 기존대로 동작하는지 확인
- [ ] `~/.opal/AGENT.md` 복사가 기존대로 동작하는지 확인
- [ ] `~/.opal/references/` 복사가 기존대로 동작하는지 확인
- [ ] `~/.opal/community-skills/` 복사가 기존대로 동작하는지 확인
- [ ] `~/.opal/templates/` 복사가 기존대로 동작하는지 확인
- [ ] install-mac.sh의 MCP 설정 머지 로직이 기존대로 동작하는지 확인

### B-3. 코드 품질
- [ ] 파일/폴더 네이밍이 kebab-case 준수
- [ ] 문서 본문 한국어, 코드/변수명 영어 컨벤션 준수
- [ ] install-mac.sh 쉘 스크립트 문법 검증 (`bash -n`) 통과
- [ ] CLAUDE.md 소스 구조/배포 구조 다이어그램이 실제 구조와 일치
- [ ] README.md 아키텍처 다이어그램이 실제 구조와 일치

### B-4. 보안
- [ ] install-mac.sh에 하드코딩된 경로 외 민감 정보 없음
- [ ] .gitignore에 identity.md 등 개인 설정 파일 포함 확인

---

## 복잡도 판별

| 기준 | 값 | 판정 |
|------|-----|------|
| Step 수 | 13개 | 복잡 (>=6) |
| 변경 파일 수 | 19개+ | 복잡 (>=4) |
| 모듈 범위 | agents, skills, opal/core, scripts, docs | 복잡 (다중 모듈) |
| 작업 유형 | 대규모 구조 개선 | 복잡 |
| 외부 의존성 | 없음 | 단순 |

**결과: 복잡 모드** (5개 기준 중 4개 해당)

---

## Part C: 실행 아키텍처 (복잡 모드)

> 복잡 모드로 판정되었으므로 실행 아키텍처를 정의한다.

### C-1. 에이전트 토폴로지

Step 간 의존성 DAG:

```
[Step 1] agents/ 플랫화 ─┬─> [Step 2] Cursor/Antigravity 삭제
                         ├─> [Step 7] agents.md 수정
                         ├─> [Step 8] dev-task-pilot 경로 수정
                         ├─> [Step 9] web-to-markdown, opal-agent-creator 경로 수정
                         └─┐
[Step 3] opal- 접두사 ──┬─┤─> [Step 10] install-mac.sh 재설계
                       ├──┤
                       ├──┘─> [Step 11] CLAUDE.md 업데이트
                       ├─> [Step 4] AGENT.md 경로 수정
                       ├─> [Step 5] 부트스트래퍼 경로 수정
                       └─> [Step 6] skills.md 수정

[Step 10, 11] ──────────> [Step 12] README.md 업데이트

[Step 1~12] ────────────> [Step 13] 전체 검증
```

**실행 배치 (Batch)**:

| 배치 | Step | 설명 | 병렬 가능 |
|------|------|------|----------|
| Batch 1 | Step 1, Step 3 | 구조 변경 (git mv) | 병렬 |
| Batch 2 | Step 2, Step 4, Step 5, Step 6, Step 7 | 삭제 + 경로 참조 수정 (opal 코어/레지스트리) | 병렬 |
| Batch 3 | Step 8, Step 9, Step 10, Step 11 | 스킬 경로 수정 + install-mac.sh + CLAUDE.md | 병렬 |
| Batch 4 | Step 12 | README.md 업데이트 | 단독 |
| Batch 5 | Step 13 | 전체 검증 | 단독 |

### C-2. 스킬 요구사항

기존 스킬로 충분하다. 신규 스킬 불필요.

### C-3. 도구 요구사항

- `git mv` -- 파일/디렉토리 이동 (이력 보존)
- `git rm -r` -- 디렉토리 삭제
- `bash -n` -- 쉘 스크립트 문법 검증
- 추가 CLI/MCP/패키지 설치 불필요

### C-4. 테스트 전략

코드 기반 태스크가 아닌 프레임워크 구조 변경이므로 dtp-dev-test-agent 동적 검증 대신 Step 13의 수동 검증으로 대체한다.

검증 항목:
1. 소스 디렉토리 구조가 목표와 일치하는지 `ls` 확인
2. 글로벌 탐색 경로에서 레거시 플랫폼 경로가 완전 제거되었는지 `grep` 확인
3. install-mac.sh 문법 검증 `bash -n` 통과
4. opal- 접두사 적용 완전성 `grep` 확인

---

## 승인 요청

> 위 TODO가 사용자의 승인을 받으면 EXECUTE 단계를 시작합니다.
> 복잡 모드: 워커가 Part C 토폴로지에 따라 5개 배치로 순차 실행하며, 각 배치 내 Step은 병렬 실행합니다.

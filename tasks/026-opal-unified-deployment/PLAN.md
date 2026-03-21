# PLAN: OPAL 프레임워크 배포 구조 통합 -- ~/.opal/ 단일 배포

> 작성일: 2026-03-21 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

없음. 기존 파일의 구조 변경과 수정만 발생한다.

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `scripts/install-mac.sh` | 플랫폼별 스킬/에이전트 복사 제거, `~/.opal/` 단일 배포로 변경, 메뉴 구조 재설계, 레거시 정리 로직 추가 |
| 2 | `opal/core/references/skills.md` | 프레임워크 스킬 탐색 경로 5개 -> 2개 (프로젝트 + `~/.opal/`), OPAL 전용 스킬 opal- 접두사 반영 |
| 3 | `opal/core/references/agents.md` | 에이전트 탐색 경로 8개 -> 2개 (프로젝트 + `~/.opal/`) |
| 4 | `skills/dev-task-pilot/SKILL.md` | 에이전트 탐색 경로 블록 수정 (8개 -> 2개) |
| 5 | `skills/dev-task-pilot/modes/wireframe-ui.md` | 스킬 탐색 경로 블록 2곳 수정 (5개 -> 2개) |
| 6 | `skills/dev-task-pilot/references/execute-plan-guide.md` | 스킬 탐색 경로 블록 수정 (4개 -> 2개) |
| 7 | `skills/web-to-markdown/SKILL.md` | 에이전트 탐색 경로 블록 수정 (6개 -> 2개) |
| 8 | `skills/opal-agent-creator/SKILL.md` | 에이전트 탐색 경로 템플릿 수정 (8개 -> 2개) |
| 9 | `opal/core/AGENT.md` | OPAL 전용 스킬 경로 opal- 접두사 반영 |
| 10 | `opal/bootstrapper/cursor-bootstrap.mdc` | OPAL 전용 스킬 경로 opal- 접두사 반영 |
| 11 | `CLAUDE.md` | 소스 구조 + 배포 구조 다이어그램 전면 업데이트 |
| 12 | `README.md` | 2계층 아키텍처 다이어그램 + 설치 가이드 업데이트 |

### 이동/삭제 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 13 | `agents/claude/*` -> `agents/*` | 7개 에이전트 디렉토리를 상위로 이동 (dtp-dev-agent, dtp-wireframe-ui-agent, dtp-qa-dev-agent, dtp-qa-wireframe-agent, dtp-action-plan-agent, dtp-dev-test-agent, wtm-worker) |
| 14 | `agents/cursor/` | 디렉토리 전체 삭제 |
| 15 | `agents/antigravity/` | 디렉토리 전체 삭제 |
| 16 | `opal/skills/onboarding/` -> `opal/skills/opal-onboarding/` | 디렉토리 이름 변경 |
| 17 | `opal/skills/project-init/` -> `opal/skills/opal-project-init/` | 디렉토리 이름 변경 |
| 18 | `opal/skills/orchestrator/` -> `opal/skills/opal-orchestrator/` | 디렉토리 이름 변경 |
| 19 | `opal/skills/skill-manager/` -> `opal/skills/opal-skill-manager/` | 디렉토리 이름 변경 |

### 영향 확인 (변경 없지만 검증 필요)

| # | 파일 경로 | 확인 사항 |
|---|----------|----------|
| 1 | `opal/core/mcps/*.json` | MCP 설정은 플랫폼별 유지 -- 변경 없음 확인 |
| 2 | `opal/bootstrapper/claude-bootstrap.md` | OPAL 부트스트래퍼는 기존 방식 유지 -- 변경 없음 확인 |
| 3 | `opal/bootstrapper/gemini-bootstrap.md` | 동일 |
| 4 | `opal/core/hooks/claude-hooks.json` | hooks 설정은 플랫폼 네이티브 -- 변경 없음 확인 |

## 2. 구현 순서

의존 받는 쪽(하위 레이어)부터 구현한다.

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 소스 agents/ 디렉토리 구조 플랫화 | `agents/` (git mv + 삭제) | 낮음 |
| 2 | OPAL 전용 스킬 opal- 접두사 적용 | `opal/skills/` (git mv) | 낮음 |
| 3 | 참조 레지스트리 수정 | `opal/core/references/skills.md`, `agents.md` | 낮음 |
| 4 | OPAL 코어 경로 수정 | `opal/core/AGENT.md`, `opal/bootstrapper/cursor-bootstrap.mdc` | 낮음 |
| 5 | 스킬 내 탐색 경로 수정 | 5개 스킬 파일 | 중간 |
| 6 | install-mac.sh 전면 재설계 | `scripts/install-mac.sh` | 높음 |
| 7 | 프로젝트 문서 업데이트 | `CLAUDE.md`, `README.md` | 중간 |

## 3. 핵심 설계

### 3.1 소스 agents/ 구조 변경

**현재**:
```
agents/
├── claude/
│   ├── dtp-dev-agent/AGENT.md
│   ├── ...
│   └── wtm-worker/AGENT.md
├── cursor/
│   ├── dtp-dev-agent.md
│   └── ...
└── antigravity/
    ├── dtp-dev-agent/SKILL.md
    └── ...
```

**목표**:
```
agents/
├── dtp-dev-agent/AGENT.md
├── dtp-wireframe-ui-agent/AGENT.md
├── dtp-qa-dev-agent/AGENT.md
├── dtp-qa-wireframe-agent/AGENT.md
├── dtp-action-plan-agent/AGENT.md
├── dtp-dev-test-agent/AGENT.md
└── wtm-worker/AGENT.md
```

작업:
- `agents/claude/*` 7개 디렉토리를 `agents/`로 이동 (`git mv`)
- `agents/cursor/`, `agents/antigravity/` 삭제 (`git rm -r`)

### 3.2 OPAL 전용 스킬 opal- 접두사 적용

**현재**: `opal/skills/{onboarding,orchestrator,project-init,skill-manager}/`
**목표**: `opal/skills/{opal-onboarding,opal-orchestrator,opal-project-init,opal-skill-manager}/`

작업: `git mv` 4회

경로 참조 수정 대상:
- `opal/core/AGENT.md` 라인 10: `~/.opal/skills/onboarding/` -> `~/.opal/skills/opal-onboarding/`
- `opal/core/AGENT.md` 라인 42: `~/.opal/skills/orchestrator/` -> `~/.opal/skills/opal-orchestrator/`
- `opal/core/AGENT.md` 라인 47: `~/.opal/skills/project-init/` -> `~/.opal/skills/opal-project-init/`
- `opal/bootstrapper/cursor-bootstrap.mdc` 라인 10: `~/.opal/skills/onboarding/` -> `~/.opal/skills/opal-onboarding/`
- `opal/core/references/skills.md`: OPAL 전용 스킬 테이블의 경로 4개

### 3.3 탐색 경로 통합

모든 탐색 경로를 2계층으로 단순화한다:

**에이전트 탐색 경로** (새):
```
1. {프로젝트}/.opal/agents/{agent-name}/AGENT.md
2. ~/.opal/agents/{agent-name}/AGENT.md
```

**스킬 탐색 경로** (새):
```
1. {프로젝트}/.opal/skills/{skill}/SKILL.md
2. ~/.opal/skills/{skill}/SKILL.md
```

수정 대상 파일과 변경 포인트:

| 파일 | 위치 | 변경 |
|------|------|------|
| `opal/core/references/agents.md` | 라인 62-69 | 8개 경로 -> 2개 |
| `opal/core/references/skills.md` | 라인 21-25 | 5개 경로 -> 2개 |
| `skills/dev-task-pilot/SKILL.md` | 라인 120-131 | 8개 에이전트 경로 -> 2개 |
| `skills/dev-task-pilot/modes/wireframe-ui.md` | 라인 130-136 | 5개 스킬 경로 -> 2개 (wireframe-builder) |
| `skills/dev-task-pilot/modes/wireframe-ui.md` | 라인 191-197 | 5개 스킬 경로 -> 2개 (ui-designer) |
| `skills/dev-task-pilot/references/execute-plan-guide.md` | 라인 59-64 | 4개 스킬 경로 -> 2개 |
| `skills/web-to-markdown/SKILL.md` | 라인 235-241 | 6개 에이전트 경로 -> 2개 |
| `skills/opal-agent-creator/SKILL.md` | 라인 216-224 | 8개 에이전트 경로 템플릿 -> 2개 |

### 3.4 install-mac.sh 재설계

**메뉴 구조**:

```
[1] OPAL 설치     (스킬 + 에이전트 + 참조 + 커뮤니티 스킬 + 부트스트래퍼 + hooks)
[2] MCP 서버 설정  (플랫폼별 MCP 설정)
[3] 전체 설치      (1 + 2)
[0] 종료
```

**install_opal() 함수 변경**:

현재의 `install_opal()`을 확장하여 프레임워크 스킬과 에이전트도 `~/.opal/`로 배포한다.

```bash
install_opal() {
    # 1. AGENT.md 복사
    cp opal/core/AGENT.md ~/.opal/AGENT.md

    # 2. 프레임워크 스킬 복사 (skills/ -> ~/.opal/skills/)
    install_dir skills/ ~/.opal/skills/

    # 3. OPAL 전용 스킬 복사 (opal/skills/ -> ~/.opal/skills/)
    #    opal- 접두사가 붙어 있으므로 프레임워크 스킬과 충돌 없음
    install_dir opal/skills/ ~/.opal/skills/   # cp -Rf 머지

    # 4. 에이전트 복사 (agents/ -> ~/.opal/agents/)
    install_dir agents/ ~/.opal/agents/

    # 5. 템플릿, 참조 레지스트리, 커뮤니티 스킬 (기존과 동일)
    install_dir opal/templates/ ~/.opal/templates/
    install_opal_references
    install_opal_community_skills

    # 6. 부트스트래퍼 설치 (기존과 동일)
    install_opal_section ... Claude
    install_opal_section ... Cursor
    install_opal_section ... Gemini

    # 7. Claude Code hooks (기존 install_claude에서 이동)
    merge_hooks_config ~/.claude/settings.json opal/core/hooks/claude-hooks.json
}
```

**삭제할 함수**:
- `install_claude()` -- 역할이 `install_opal()`로 통합 (hooks만 이관)
- `install_cursor()` -- 역할 없음
- `install_antigravity()` -- 역할 없음

**레거시 정리 로직**:

첫 실행 시 기존 플랫폼별 배포 파일 정리 안내를 출력한다. 자동 삭제는 위험하므로 안내만 한다.

```bash
print_cleanup_notice() {
    # ~/.claude/skills/, ~/.claude/agents/ 존재 시 안내
    # ~/.cursor/skills/, ~/.cursor/agents/ 존재 시 안내
    # ~/.gemini/antigravity/skills/ 존재 시 안내
    echo "기존 배포 파일이 남아 있습니다. 수동 삭제를 권장합니다:"
    echo "  rm -rf ~/.claude/skills/ ~/.claude/agents/"
    echo "  rm -rf ~/.cursor/skills/ ~/.cursor/agents/"
    echo "  rm -rf ~/.gemini/antigravity/skills/"
    echo "  rm -rf ~/.gemini/agents/"
}
```

**배너 업데이트**:

```bash
print_banner() {
    # "Claude Code . Cursor . Antigravity . OPAL" -> "OPAL Framework Installer"
}
```

**print_summary() 업데이트**:

플랫폼별 경로 대신 `~/.opal/` 중심으로 요약 출력.

### 3.5 CLAUDE.md 업데이트

**소스 구조** 섹션:

```
agents/                          <- 에이전트 (단일 포맷, AGENT.md)
├── dtp-dev-agent/
├── dtp-wireframe-ui-agent/
├── dtp-qa-dev-agent/
├── dtp-qa-wireframe-agent/
├── dtp-action-plan-agent/
├── dtp-dev-test-agent/
└── wtm-worker/
```

(플랫폼별 하위 디렉토리 제거)

**배포 구조** 섹션:

```
~/.opal/                         <- OPAL 에이전트 홈 (유일한 배포 경로)
├── AGENT.md
├── identity.md
├── references/
├── skills/                      <- 프레임워크 스킬 + OPAL 전용 스킬 (opal- 접두사)
│   ├── dev-task-pilot/
│   ├── api-analyzer/
│   ├── ...
│   ├── opal-onboarding/
│   ├── opal-orchestrator/
│   ├── opal-project-init/
│   └── opal-skill-manager/
├── agents/                      <- 에이전트 (AGENT.md)
│   ├── dtp-dev-agent/
│   └── ...
├── community-skills/
└── templates/
```

`~/.claude/`, `~/.cursor/`, `~/.gemini/` 섹션에서 skills/agents 관련 내용 제거. MCP와 부트스트래퍼만 남긴다.

**컴포넌트 유형 테이블**:

에이전트 수: `agents/` 7개 x 1 포맷 (이전: 6개 x 3 플랫폼 + wtm-worker 누락)

**에이전트 추가 가이드**:

3개 플랫폼별 파일 생성 -> 단일 `agents/{name}/AGENT.md` 생성으로 변경.

### 3.6 README.md 업데이트

2계층 아키텍처 다이어그램에서 플랫폼별 배포 경로를 `~/.opal/` 단일 경로로 변경.

설치 가이드에서 메뉴를 3개 항목(OPAL 설치 / MCP 설정 / 전체)으로 변경하고, 플랫폼별 수동 설치 명령 제거.

## 4. 의존성 및 환경 변경

추가 패키지나 환경 설정 변경은 없다. 순수 파일 구조 변경 + 내용 수정 작업이다.

다만 설치 스크립트 변경 후 재설치가 필요하므로, 작업 완료 후 `./scripts/install-mac.sh`를 재실행하여 `~/.opal/`에 최신 파일을 배포해야 한다.

## 5. 테스트 전략

이 태스크는 코드가 아닌 프레임워크 구조 변경이므로, 자동화 테스트 대신 수동 검증을 수행한다.

### 설치 스크립트 검증

- `./scripts/install-mac.sh` 실행 후 `~/.opal/skills/`, `~/.opal/agents/` 경로에 파일이 올바르게 배포되는지 확인
- 프레임워크 스킬 10개 + OPAL 전용 스킬 4개 = `~/.opal/skills/` 하위 14개 디렉토리
- 에이전트 7개 = `~/.opal/agents/` 하위 7개 디렉토리
- 부트스트래퍼가 기존대로 Claude/Cursor/Gemini에 설치되는지 확인
- MCP 설정이 기존대로 동작하는지 확인

### 탐색 경로 검증

- 각 스킬/에이전트 파일에서 `~/.opal/` 경로가 올바르게 참조되는지 grep 확인
- 플랫폼별 경로(`~/.claude/skills/`, `~/.cursor/skills/` 등)가 글로벌 탐색 경로에서 완전히 제거되었는지 확인
- 프로젝트 레벨 경로(`{프로젝트}/.opal/`)는 유지되는지 확인

### OPAL 전용 스킬 경로 검증

- `opal/core/AGENT.md`에서 `opal-onboarding`, `opal-orchestrator`, `opal-project-init` 경로가 올바른지 확인
- `opal/core/references/skills.md`에서 OPAL 전용 스킬 경로가 업데이트되었는지 확인

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 배포 파일 잔존 | `~/.claude/skills/` 등에 이전 파일이 남아 혼란 가능 | install-mac.sh에 정리 안내 메시지 출력 (자동 삭제는 위험하므로 수동 안내) |
| Gemini CLI 에이전트 미배포 | `~/.gemini/agents/`에 에이전트가 없어짐 (Gemini CLI 네이티브 기능 미지원) | Gemini CLI는 OPAL 부트스트래퍼를 통해 `~/.opal/agents/`를 참조하므로 실질적 영향 없음. Gemini CLI 네이티브 에이전트 기능이 필요해지면 별도 대응 |
| opal- 접두사 적용 시 누락 참조 | AGENT.md, 부트스트래퍼 외에도 참조하는 곳이 있을 수 있음 | grep으로 `skills/onboarding`, `skills/orchestrator`, `skills/project-init`, `skills/skill-manager` 전체 검색하여 누락 확인 |
| git mv 후 이력 추적 | git mv로 이동 시 이력이 끊길 수 있음 | `git mv`를 사용하면 rename으로 인식되어 이력 유지됨. 한 커밋에서 mv + 내용 수정을 함께 하면 추적이 어려우므로, 구조 변경과 내용 수정을 분리 커밋 고려 |

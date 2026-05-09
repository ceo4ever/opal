# OPAL Doctor

OPAL 환경 상태를 진단하는 도구. 4개 섹션(Dependencies / OPAL Paths / MCP Registration / Bootstrappers)을 순차 점검하고 결과를 요약한다.

## 사용법

```bash
# opal-cli 경유 (Step 2 PATH 등록 완료 후)
opal-cli doctor

# 직접 실행
~/.opal/tools/doctor/run.sh
```

## 출력 포맷

```
[OPAL Doctor]

[1/4] Dependencies
  ✓ bash 5.x
  ✓ git 2.43.x
  ✓ Node.js v18.x
  ✓ python3 3.11.x
  ✓ curl 8.x
  ⚠ playwright — 옵션, 미설치 (npx @playwright/mcp@latest)

[2/4] OPAL Paths
  ✓ ~/.opal/AGENT.md
  ✓ ~/.opal/identity.md
  ✓ ~/.opal/skills/ (29 skills)
  ✓ ~/.opal/agents/ (10 agents)
  ✓ ~/.opal/bin/opal-cli  →  ~/.opal/tools/opal-cli/run.sh

[3/4] MCP Registration
  ✓ Claude: context7, playwright, shadcn, sequential-thinking
  ✓ Cursor: context7, playwright, shadcn, sequential-thinking
  ✓ Gemini: context7, playwright, shadcn, sequential-thinking

[4/4] Bootstrappers
  ✓ ~/.claude/CLAUDE.md (OPAL marker)
  ✓ ~/.cursor/rules/000-opal-agent.mdc
  ✓ ~/.gemini/GEMINI.md (OPAL + HARDENING markers)

판정: All Pass (14 ✓, 0 ⚠, 0 ✗ / 총 14건)
```

## 심각도

| 기호 | 의미 | exit code 영향 |
|------|------|--------------|
| ✓ | Pass — 정상 | 없음 |
| ⚠ | Warn — 옵션 항목 누락 또는 부분 등록 | exit 0 유지 |
| ✗ | Fail — 필수 항목 누락 | exit 1 |

## Exit Code

| 코드 | 조건 |
|------|------|
| 0 | Fail 없음 (Pass/Warn만 있어도 0) |
| 1 | Fail 1건 이상 |

## 체크 항목

### [1/4] Dependencies

| 항목 | 필수/옵션 | 조건 |
|------|---------|------|
| bash | 필수 | 설치 여부 |
| git | 필수 | 설치 여부 |
| Node.js | 필수 | v18+ 여부 |
| python3 | 필수 | 설치 여부 |
| curl | 필수 | 설치 여부 |
| playwright | 옵션 | npx @playwright/mcp@latest 사용 가능 여부 |

### [2/4] OPAL Paths

| 항목 | 필수/권고 | 조건 |
|------|---------|------|
| `~/.opal/AGENT.md` | 필수 | 파일 존재 |
| `~/.opal/identity.md` | 필수 | 파일 존재 (onboarding으로 생성) |
| `~/.opal/skills/` | 필수 | 디렉토리 존재 |
| `~/.opal/agents/` | 필수 | 디렉토리 존재 |
| `~/.opal/bin/opal-cli` | 권고 | symlink 또는 파일 존재 |

### [3/4] MCP Registration

OPAL 공식 MCP 서버 (context7, playwright, shadcn, sequential-thinking)의 플랫폼별 등록 상태를 확인한다.

| 플랫폼 | 확인 방법 |
|--------|---------|
| Claude | `claude mcp list` CLI 출력 파싱 |
| Cursor | `~/.cursor/mcp.json` JSON 파싱 |
| Gemini | `~/.gemini/settings.json` + `~/.gemini/antigravity/mcp_config.json` 합산 |

### [4/4] Bootstrappers

| 항목 | 필수/권고 | 조건 |
|------|---------|------|
| `~/.claude/CLAUDE.md` | 필수 | `=== OPAL START ===` 마커 존재 |
| `~/.cursor/rules/000-opal-agent.mdc` | 권고 | 파일 존재 |
| `~/.gemini/GEMINI.md` | 권고 | OPAL + HARDENING 마커 모두 존재 |

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `~/.opal/AGENT.md — 미존재` | OPAL 미설치 | `curl -fsSL .../install.sh \| bash` 재실행 |
| `~/.opal/identity.md — 미존재` | onboarding 미완료 | `//onboarding` 실행 후 정체성 설정 |
| `~/.opal/bin/opal-cli — 미존재` | `install_opal_bin` 미실행 | install-mac.sh 재실행 |
| `Claude: MCP 미등록` | claude CLI 없음 또는 미등록 | `opal-cli mcp add` 또는 `claude mcp add <name> -- <cmd>` |
| `CLAUDE.md OPAL 마커 없음` | 부트스트래퍼 미삽입 | install 재실행 또는 수동 마커 삽입 |

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-08 KST | 초기 구현 — 4섹션 doctor README (139) |

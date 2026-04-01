# RESEARCH: OPAL MCP 관리 체계 구축

> 작성일: 2026-03-12 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `scripts/install-mac.sh` | 프레임워크 설치 스크립트 | 수정 (MCP 설치 함수 추가) |
| `opal/core/references/mcps.md` | MCP 레지스트리 (현재 비어있음) | 수정 (기본 MCP 등록) |
| `opal/core/` | OPAL 코어 디렉토리 | 신규 (`mcps/` 디렉토리 추가) |
| `community-skills/vercel-labs/shadcn/mcp.md` | shadcn MCP 설정 참조 | 없음 (참조만) |

### 현재 구현 패턴

**install-mac.sh 핵심 구조:**
- `install_dir()` — 디렉토리 복사 (신규/덮어쓰기)
- `install_opal_section()` — 마커 기반 텍스트 블록 머지 (CLAUDE.md, GEMINI.md용)
- `install_opal()` — OPAL 전체 설치 오케스트레이터
- 플랫폼별 설치 함수: `install_claude()`, `install_cursor()`, `install_antigravity()`

**기존 머지 패턴:**
- 텍스트 파일(CLAUDE.md)은 `# === OPAL START ===` / `# === OPAL END ===` 마커로 섹션 교체
- JSON 머지 로직은 현재 없음

### 의존성 맵

```
install-mac.sh
├── opal/core/AGENT.md → ~/.opal/AGENT.md
├── opal/core/references/ → ~/.opal/references/
├── opal/skills/ → ~/.opal/skills/
├── opal/templates/ → ~/.opal/templates/
├── community-skills/ → ~/.opal/community-skills/
├── skills/ → ~/.claude/skills/, ~/.cursor/skills/, ~/.gemini/antigravity/skills/
├── agents/{platform}/ → 각 플랫폼 agents/
└── opal/bootstrapper/ → CLAUDE.md, .cursor/rules/, GEMINI.md
    (신규 추가)
    └── opal/core/mcps/ → ~/.claude/mcp.json, ~/.cursor/mcp.json
```

## 2. 외부 조사 결과

### 플랫폼별 MCP 설정 포맷

**핵심 발견: 모든 플랫폼이 동일한 JSON 스키마를 사용한다.**

| 플랫폼 | 설정 경로 | 루트 키 |
|--------|----------|--------|
| Claude Code | `~/.claude/mcp.json` | `mcpServers` |
| Cursor | `~/.cursor/mcp.json` | `mcpServers` |
| VS Code | `~/.vscode/mcp.json` | `mcpServers` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `mcpServers` |

**공통 JSON 구조:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/server-name"],
      "env": { "API_KEY": "${ENV_VAR}" }
    }
  }
}
```

### MCP 설치 3가지 패턴 상세

**패턴 1: 설정 머지형 (stdio 로컬 + 원격 URL)**
```json
// stdio 로컬
{ "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"] }

// 원격 URL
{ "url": "https://mcp.example.com/v1", "headers": { "Authorization": "Bearer ${TOKEN}" } }
```

**패턴 2: CLI 위임형**
```bash
npx shadcn@latest mcp init    # 에디터 자동 감지 → mcp.json 생성
```

**패턴 3: 패키지 설치형**
```bash
npm install -g github-mcp-server
# → 이후 패턴 1과 동일하게 설정 머지
```

### JSON 머지 방법

**macOS에서의 옵션:**
- `jq` — 가장 깔끔하지만 기본 설치 아님 (Homebrew 필요)
- `python3 -c` — macOS 기본 포함, JSON 처리 가능
- `sed/awk` — 기본 포함이지만 JSON 처리에 취약

**권장: `python3` 사용** — macOS에 기본 포함, JSON 머지에 안전, 외부 의존성 없음

```bash
python3 -c "
import json, sys
existing = json.load(open(sys.argv[1])) if os.path.exists(sys.argv[1]) else {'mcpServers': {}}
new_servers = json.load(open(sys.argv[2]))
existing['mcpServers'].update(new_servers['mcpServers'])
json.dump(existing, open(sys.argv[1], 'w'), indent=2)
" "$target" "$source"
```

## 3. 영향 범위

| 영향 대상 | 내용 | 위험도 |
|-----------|------|--------|
| `install-mac.sh` | MCP 설치 함수 추가 (기존 로직 변경 없음) | 낮음 |
| `~/.claude/mcp.json` | 신규 생성 또는 머지 | 중간 (기존 설정 보존 필요) |
| `~/.cursor/mcp.json` | 신규 생성 또는 머지 | 중간 (동일) |
| `opal/core/references/mcps.md` | 빈 레지스트리에 항목 추가 | 낮음 |
| `opal/core/mcps/` | 신규 디렉토리 | 없음 |
| `CLAUDE.md` (소스 구조 문서) | 디렉토리 구조에 mcps/ 반영 | 낮음 |

## 4. 핵심 발견 사항

1. **플랫폼 포맷이 통일됨** — Claude Code, Cursor, VS Code 모두 `{ "mcpServers": { ... } }` 동일 구조. 플랫폼별 변환 불필요, 경로만 다름.

2. **python3이 안전한 머지 도구** — macOS 기본 포함, jq 없이도 JSON 머지 가능. install-mac.sh의 외부 의존성을 늘리지 않음.

3. **MCP 설정 템플릿은 서버 단위 JSON 파일로 관리 가능** — `opal/core/mcps/{server-name}.json` 형태로, 각 서버의 설정을 개별 파일로 두면 추가/삭제가 용이.

4. **CLI 위임형은 install-mac.sh보다 skill-manager 영역** — `shadcn mcp init` 같은 CLI 위임은 설치 시점이 아닌 프로젝트 작업 시점에 실행하는 게 자연스러움. install-mac.sh에서는 설정 머지형에 집중.

5. **Antigravity(Gemini)는 MCP 설정 경로가 불분명** — `~/.gemini/` 하위에 표준 mcp.json이 없음. 현재는 Claude Code + Cursor만 지원하고 향후 확장.

## 5. 제약/리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 기존 mcp.json 덮어쓰기 | 사용자 설정 손실 | python3 JSON 머지로 기존 키 보존 |
| python3 미설치 환경 | 설치 실패 | macOS는 기본 포함, 없으면 경고 후 스킵 |
| npm/npx 미설치 | 패키지 설치형/CLI 위임형 불가 | Node.js 없으면 안내 메시지, 설정 머지형만 실행 |
| MCP 서버 버전 변경 | 설정 호환성 | `npx -y` 플래그로 최신 버전 자동 사용 |

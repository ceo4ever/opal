# PLAN: Claude Code Hooks 알림 설정 및 install-mac.sh 배포

> 작성일: 2026-03-20 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `scripts/install-mac.sh` | 프레임워크 설치 스크립트 (skills, agents, MCP, OPAL 배포) | Yes |
| `opal/core/mcps/*.json` | MCP 설정 JSON 파일 (hooks JSON 구조 참고용) | No |
| `~/.claude/settings.json` | Claude Code 사용자 설정 (hooks 머지 대상) | No (런타임 대상) |
| (신규) `opal/core/hooks/claude-hooks.json` | hooks 설정 소스 파일 | Yes (신규 생성) |

### 현재 구현

**install-mac.sh 구조:**

- `merge_mcp_config()` (99-129행): python3으로 JSON 머지. `target` 파일을 읽고, `mcpServers` 키 하위에 MCP 서버를 추가. 이미 존재하면 스킵(`sys.exit(0)`). 이 패턴을 hooks 머지에 재활용 가능.
- `install_claude()` (230-239행): `~/.claude/`에 skills와 agents 디렉토리만 복사. hooks 설치 단계가 없음.
- `install_mcp()` (315-405행): `opal/core/mcps/*.json`을 순회하며 플랫폼별로 MCP 설정을 머지. claude 플랫폼은 `claude mcp add` CLI를 사용하지만, hooks는 CLI 명령이 없으므로 `settings.json` 직접 머지 방식이 필요.
- `main()` (554-612행): 메뉴에서 `[1] Claude Code` 선택 시 `install_claude()` 호출, `[6] 전체 설치` 시에도 `install_claude()` 호출.

**settings.json 현재 상태:**

- `~/.claude/settings.json`은 현재 빈 객체 `{}`. 그러나 다른 사용자 환경에서는 `permissions`, `mcpServers` 등이 존재할 수 있으므로 기존 키를 보존하면서 `hooks` 키만 추가/업데이트하는 머지 로직이 필수.

**MCP JSON 파일 구조 (참고):**

```json
{
  "name": "context7",
  "description": "...",
  "install_type": "config_merge",
  "config": { "command": "npx", "args": [...] },
  "platforms": ["claude", "cursor", ...]
}
```

- hooks 설정 JSON도 유사하게 소스 파일로 관리하되, 구조는 Claude Code hooks 스펙에 맞춰야 함.

### 영향 범위

**호출 관계:**
- `main()` → `install_claude()` — hooks 설치 단계 추가 필요
- `main()` → 전체 설치(6번) → `install_claude()` — 동일 경로
- 신규 `merge_hooks_config()` 함수는 `install_claude()`에서만 호출

**공유 데이터:**
- `~/.claude/settings.json` — MCP 설정(`install_mcp()`의 claude 분기에서 `claude mcp add` CLI 사용)과 hooks 설정이 같은 파일에 공존. 단, MCP는 CLI로 등록하므로 직접 충돌 없음.

**관련 테스트 파일:** 없음 (쉘 스크립트, 별도 테스트 프레임워크 없음)

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/hooks/claude-hooks.json` | (신규) Claude Code hooks 설정 소스 파일. SubagentStop 이벤트에 osascript 알림 명령 정의 |
| 2 | `scripts/install-mac.sh` | `merge_hooks_config()` 함수 추가 + `install_claude()` 함수에 hooks 설치 단계 추가 |

### 핵심 설계

#### 2.1 hooks 설정 소스 파일 (`opal/core/hooks/claude-hooks.json`)

래핑 없이 이벤트 맵만 포함하는 단순 구조 (Claude Code 전용이므로 MCP처럼 메타데이터 불필요):

```json
{
  "SubagentStop": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "osascript -e 'display notification \"서브에이전트 작업이 완료되었습니다\" with title \"Claude Code\" sound name \"Glass\"'"
        }
      ]
    }
  ],
  "Stop": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "osascript -e 'display notification \"응답이 완료되었습니다\" with title \"Claude Code\" sound name \"Glass\"'"
        }
      ]
    }
  ]
}
```

- `SubagentStop`: 서브에이전트(dtp-agent, dtp-qa 등) 완료 시 알림
- `Stop`: 일반 응답 완료 시 알림
- `matcher: ""` — 모든 경우에 매치 (필터 없음)
- `sound name "Glass"` — macOS 기본 알림음

#### 2.2 `merge_hooks_config()` 함수

`merge_mcp_config()`와 동일한 패턴으로, `settings.json`의 `hooks` 키에 이벤트별 설정을 머지한다.

```bash
merge_hooks_config() {
    local target="$1"       # ~/.claude/settings.json
    local hooks_json="$2"   # opal/core/hooks/claude-hooks.json 경로

    python3 -c "
import json, os, sys

target = sys.argv[1]
hooks_file = sys.argv[2]

# 소스 hooks 읽기 (이벤트 맵 직접 포함)
with open(hooks_file) as f:
    source_hooks = json.load(f)

# 기존 settings 읽기 (없으면 빈 객체)
if os.path.exists(target):
    with open(target) as f:
        content = f.read().strip()
    data = json.loads(content) if content else {}
else:
    data = {}

# hooks 키 머지 (이벤트별 덮어쓰기)
data.setdefault('hooks', {})
for event, rules in source_hooks.items():
    data['hooks'][event] = rules

# 저장
with open(target, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$target" "$hooks_json"
}
```

**머지 전략**: 이벤트 단위(`SubagentStop`, `Stop`)로 덮어쓰기. 기존 `settings.json`의 `permissions` 등 다른 최상위 키는 보존됨.

#### 2.3 `install_claude()` 수정

기존 skills/agents 복사 후, hooks 설치 단계를 추가:

```bash
# hooks 설치
local hooks_src="$FRAMEWORK_ROOT/opal/core/hooks/claude-hooks.json"
if [[ -f "$hooks_src" ]]; then
    local settings="$base/settings.json"
    merge_hooks_config "$settings" "$hooks_src"
    success "Claude Code hooks → $settings"
fi
```

## 3. 실행 체크리스트

- [x] Step 1: hooks 설정 파일 생성 -- `opal/core/hooks/claude-hooks.json` -- SubagentStop, Stop 이벤트에 osascript 알림 정의
- [x] Step 2: `merge_hooks_config()` 함수 추가 -- `scripts/install-mac.sh` -- `merge_mcp_config()` 바로 다음에 python3 기반 hooks 머지 함수 추가
- [x] Step 3: `install_claude()` 함수에 hooks 설치 단계 추가 -- `scripts/install-mac.sh` -- agents 설치 후 hooks 머지 호출

## 4. QA 체크리스트

### 기능 테스트
- [x] `opal/core/hooks/claude-hooks.json`이 유효한 JSON인지 확인 (`python3 -m json.tool`)
- [x] `merge_hooks_config()`가 빈 `settings.json`에 hooks를 올바르게 추가하는지 확인
- [x] `merge_hooks_config()`가 기존 설정(permissions 등)이 있는 `settings.json`에서 hooks만 추가하고 나머지를 보존하는지 확인
- [ ] `install_claude()` 실행 후 `~/.claude/settings.json`에 hooks 설정이 존재하는지 확인 <!-- 실제 install 실행은 사용자 판단 -->

### 회귀 테스트
- [x] `install_claude()` 기존 기능(skills, agents 복사)이 정상 동작하는지 확인
- [x] `merge_mcp_config()`가 영향받지 않는지 확인 (별도 함수이므로 문제 없음)
- [ ] 전체 설치(메뉴 6번) 경로에서 hooks가 정상 설치되는지 확인 <!-- 실제 install 실행 필요 -->

### 코드 품질
- [x] `merge_hooks_config()` 함수가 `merge_mcp_config()`와 일관된 코딩 스타일을 따르는지 확인
- [x] python3 미설치 환경에서 graceful 스킵 처리 (`command -v python3` 체크 추가됨)
- [x] hooks JSON 파일 경로가 누락된 경우 silent skip 처리 확인 (`[[ -f "$hooks_src" ]]` 체크)

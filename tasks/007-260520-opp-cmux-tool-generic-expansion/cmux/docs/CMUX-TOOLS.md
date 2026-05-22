---
@header {
  "module": "cmux-tools",
  "layer": "reference",
  "domain": "dev-tool",
  "description": "cmux CLI 명령 레퍼런스 · Socket API · Claude Code hooks 레시피 — CMUX.md에서 분리된 기술 참조 문서",
  "exports": ["CLI레퍼런스", "단축키레퍼런스", "브라우저-CLI", "Claude-Code-hooks-레시피", "SocketAPI"],
  "depends": ["cmux-guide"]
}
---

# cmux Tools 레퍼런스

> 이 문서는 [CMUX.md](./CMUX.md)에서 분리된 기술 레퍼런스다.  
> 워크플로우·예시·설정 가이드는 CMUX.md를 먼저 읽어라.

---

## 1. CLI 명령 레퍼런스 [일반]

<!-- 아래 명령/플래그는 cmux 공식 문서·GitHub 기반이며, 버전에 따라 달라질 수 있음 -->
<!-- 실제 사용 시 반드시 'cmux <subcommand> --help'로 검증 권장 -->

### 1-1. Workspace / Surface 관리

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux new-workspace` | 새 Workspace 생성 | `cmux new-workspace --name mams-main` |
| `cmux new-surface` | 새 Surface(탭) 생성 | `cmux new-surface --name be --cwd workspace/backend --command "uv run ..."` |
| `cmux close-surface` | Surface 닫기 | `cmux close-surface be` |
| `cmux list-panes` | 현재 pane 목록 조회 | `cmux list-panes` |
| `cmux list-pane-surfaces` | Surface 목록 조회 | `cmux list-pane-surfaces` |
| `cmux focus-pane` | pane 포커스 이동 | `cmux focus-pane --name be` |
| `cmux surface-health` | Surface 상태 확인 | `cmux surface-health be` |

> `cmux new-surface --help` 로 `--name`/`--cwd`/`--command` 등 정확한 플래그 검증 권장

### 1-2. 명령 전송

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux send` | Surface에 텍스트 전송 | `cmux send --surface be "ls -la"` |
| `cmux send-key` | Surface에 키 전송 | `cmux send-key --surface be "Ctrl+C"` |
| `cmux send-panel` | 특정 panel에 텍스트 전송 | `cmux send-panel --panel 0 "text"` |
| `cmux send-key-panel` | 특정 panel에 키 전송 | `cmux send-key-panel --panel 0 "Enter"` |

> `cmux send-key --help`로 키 이름 포맷('Ctrl+C', 'Enter' 등) 검증 권장

### 1-3. Split / Pane 관리

| 명령 | 설명 |
|------|------|
| `cmux new-split` | 현재 Surface에 split pane 추가 |
| `cmux new-pane` | 새 pane 추가 |
| `cmux drag-surface-to-split` | Surface를 split으로 드래그 |
| `cmux reorder-surface` | Surface 순서 변경 |
| `cmux reorder-workspace` | Workspace 순서 변경 |
| `cmux move-workspace-to-window` | Workspace를 다른 창으로 이동 |

### 1-4. 알림

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux notify` | macOS 알림 전송 | `cmux notify --title "제목" --subtitle "부제목" --body "내용"` |

> cmux notify 플래그: `--title`/`--subtitle`/`--body` (공식 플래그 — `cmux notify --help`로 검증)

### 1-5. 기타

| 명령 | 설명 |
|------|------|
| `cmux claude-hook` | Claude Code hook 트리거 |
| `cmux trigger-flash` | 화면 플래시 효과 |
| `cmux focus-webview` | 내장 브라우저 포커스 |

---

## 2. 단축키 레퍼런스 [일반]

<!-- 아래 단축키는 cmux 기본 설정 기준이며, 사용자 정의로 변경 가능 -->
<!-- 'cmux --help' 또는 설정 UI에서 실제 바인딩 확인 권장 -->

### 2-1. Navigation

| 단축키 | 동작 |
|--------|------|
| `⌘P` | 커맨드 팔레트 (cmux.json 명령 검색) |
| `⌘T` | 새 Surface 생성 |
| `⌘W` | 현재 Surface 닫기 |
| `⌘1`~`⌘8` | Surface 순서대로 이동 |
| `⌘⇧[` / `⌘⇧]` | 이전/다음 Surface |
| `⌘⇧←` / `⌘⇧→` | Split pane 간 이동 |

### 2-2. 브라우저

| 단축키 | 동작 |
|--------|------|
| `⌘⇧L` | 브라우저 좌우 분할 오픈 |
| `⌘⇧R` | 브라우저 새로고침 |
| `⌘⇧B` | 브라우저 뒤로가기 |
| `⌘⇧F` | 브라우저 앞으로가기 |

### 2-3. 터미널

| 단축키 | 동작 |
|--------|------|
| `⌘K` | 현재 pane 클리어 |
| `⌘C` | 복사 |
| `⌘V` | 붙여넣기 |
| `⌘+` | 폰트 크기 증가 |
| `⌘-` | 폰트 크기 감소 |
| `⌘0` | 폰트 크기 초기화 |
| `⌘⇧↵` | 전체화면 (Ghostty 설정 필요) |

---

## 3. 브라우저 CLI [일반]

<!-- cmux browser 서브커맨드는 버전에 따라 달라질 수 있음 -->
<!-- 'cmux browser --help' 로 전체 서브커맨드 목록 확인 권장 -->

### 3-1. 기본 제어

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux browser open` | 브라우저 오픈 | `cmux browser open http://localhost:3000` |
| `cmux browser open-split` | 브라우저 분할 오픈 | `cmux browser open-split http://localhost:8000/docs` |
| `cmux browser navigate` | URL 이동 | `cmux browser navigate http://localhost:3000/login` |
| `cmux browser url` | 현재 URL 조회 | `cmux browser url` |
| `cmux browser back` | 뒤로가기 | `cmux browser back` |
| `cmux browser forward` | 앞으로가기 | `cmux browser forward` |
| `cmux browser reload` | 새로고침 | `cmux browser reload` |

### 3-2. 상호작용

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux browser click` | 요소 클릭 | `cmux browser click "#submit-btn"` |
| `cmux browser fill` | 입력 필드 채우기 | `cmux browser fill "#email" "user@example.com"` |
| `cmux browser type` | 텍스트 타이핑 | `cmux browser type "Hello World"` |
| `cmux browser press` | 키 누르기 | `cmux browser press "Enter"` |
| `cmux browser select` | select 요소 선택 | `cmux browser select "#dropdown" "option-value"` |
| `cmux browser hover` | 요소 호버 | `cmux browser hover "#menu-item"` |
| `cmux browser focus` | 요소 포커스 | `cmux browser focus "#input"` |

### 3-3. 읽기 / 분석

| 명령 | 설명 | 예시 |
|------|------|------|
| `cmux browser snapshot` | Accessibility tree 스냅샷 | `cmux browser snapshot` |
| `cmux browser get` | 요소 텍스트/속성 조회 | `cmux browser get "#title"` |
| `cmux browser eval` | JavaScript 실행 | `cmux browser eval "document.title"` |
| `cmux browser wait` | 요소 출현 대기 | `cmux browser wait "#success-msg"` |

> 위 모든 서브커맨드의 selector 포맷(CSS selector / XPath 등)은 `cmux browser <sub> --help`로 검증 권장

---

## 4. Claude Code hooks 레시피 [일반]

### 4-1. hooks 적용 방법

`.claude/settings.local.json`의 `hooks` 섹션에 추가한다.  
샘플 파일: `.opal/cmux/config/claude-hooks.sample.json`

```bash
# 샘플 확인
cat .opal/cmux/config/claude-hooks.sample.json

# 현재 settings.local.json 확인
jq '.hooks' .claude/settings.local.json
```

### 4-2. Stop hook (응답 완료 알림)

```json
"Stop": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "[ -S /tmp/cmux.sock ] && cmux notify --title 'Claude Code' --subtitle 'MAMS' --body 'Response ready — review' || true"
      }
    ]
  }
]
```

### 4-3. Notification hook (권한 요청 알림)

```json
"Notification": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "[ -S /tmp/cmux.sock ] && cmux notify --title 'Claude Code' --subtitle 'MAMS' --body 'Permission requested' || true"
      }
    ]
  }
]
```

### 4-4. PreCompact hook (컨텍스트 압축 임박 알림)

```json
"PreCompact": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "[ -S /tmp/cmux.sock ] && cmux notify --title 'Claude Code' --subtitle 'MAMS' --body 'Context compact imminent' || true"
      }
    ]
  }
]
```

### 4-5. 가드 패턴

```bash
# cmux 소켓 미존재 시 skip (스크립트에서)
[ -S /tmp/cmux.sock ] || exit 0

# hook 명령 내 가드 (|| true 로 hook 실패 방지)
[ -S /tmp/cmux.sock ] && cmux notify ... || true
```

---

## 5. Socket API [일반]

<!-- Socket API는 JSON-RPC over Unix socket 방식 -->
<!-- browser.* 네임스페이스 존재 여부는 런타임 검증 권장: echo ...|nc -U /tmp/cmux.sock -->

### 5-1. 소켓 연결

```bash
# 소켓 경로
CMUX_SOCKET_PATH=/tmp/cmux.sock          # stable
CMUX_SOCKET_PATH=/tmp/cmux-nightly.sock  # nightly

# 연결 확인
ls -la /tmp/cmux.sock
```

### 5-2. JSON-RPC 기본 형식

```bash
# 요청
echo '{"jsonrpc":"2.0","method":"<namespace>.<method>","params":{...},"id":1}' \
  | nc -U /tmp/cmux.sock

# 응답 예시
{"jsonrpc":"2.0","result":{...},"id":1}
```

### 5-3. 알려진 네임스페이스

| 네임스페이스 | 주요 메서드 | 비고 |
|-------------|-----------|------|
| `workspace.*` | `workspace.list`, `workspace.create` | Workspace 관리 |
| `surface.*` | `surface.list`, `surface.focus`, `surface.close` | Surface 관리 |
| `notification.*` | `notification.send` | 알림 전송 |
| `system.*` | `system.info` | 시스템 정보 |
| `browser.*` | `browser.navigate`, `browser.snapshot`, `browser.fill` 등 | 브라우저 제어 (런타임 검증 권장) |

```bash
# surface.list 예시
echo '{"jsonrpc":"2.0","method":"surface.list","params":{},"id":1}' \
  | nc -U /tmp/cmux.sock

# browser.url.get 예시 (browser.* 네임스페이스 노출 여부 먼저 확인)
echo '{"jsonrpc":"2.0","method":"browser.url.get","params":{},"id":2}' \
  | nc -U /tmp/cmux.sock
```

> Socket API 전체 메서드 목록은 [cmux Socket API 문서](https://www.mintlify.com/manaflow-ai/cmux/automation/socket-api) 참조  
> (2026-04-18 기준 — 버전 업그레이드 시 재확인 권장)

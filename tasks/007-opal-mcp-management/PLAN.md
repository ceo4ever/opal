# PLAN: OPAL MCP 관리 체계 구축

> 작성일: 2026-03-12 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/core/mcps/shadcn.json` | shadcn MCP 서버 설정 템플릿 |
| 2 | `opal/core/mcps/README.md` | MCP 템플릿 작성 가이드 및 스키마 설명 |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 3 | `scripts/install-mac.sh` | `install_mcp()` 함수 추가 + `install_opal()`에서 호출 |
| 4 | `opal/core/references/mcps.md` | shadcn MCP 서버 등록 |
| 5 | `CLAUDE.md` | 소스 구조에 `mcps/` 반영 |

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | MCP 설정 템플릿 구조 정의 | `opal/core/mcps/shadcn.json`, `README.md` | 낮음 |
| 2 | JSON 머지 함수 구현 | `scripts/install-mac.sh` | 중간 |
| 3 | MCP 설치 함수 구현 | `scripts/install-mac.sh` | 중간 |
| 4 | install_opal()에 MCP 설치 연결 | `scripts/install-mac.sh` | 낮음 |
| 5 | MCP 레지스트리 업데이트 | `opal/core/references/mcps.md` | 낮음 |
| 6 | CLAUDE.md 소스 구조 반영 | `CLAUDE.md` | 낮음 |
| 7 | 설치 테스트 | - | 낮음 |

## 3. 핵심 설계

### 3.1 MCP 설정 템플릿 (`opal/core/mcps/{server}.json`)

각 MCP 서버의 설정을 개별 JSON 파일로 관리한다. 플랫폼 공통 포맷.

**스키마:**
```json
{
  "name": "shadcn",
  "description": "shadcn/ui 컴포넌트 검색/설치 MCP",
  "install_type": "config_merge",
  "config": {
    "command": "npx",
    "args": ["-y", "shadcn@latest", "mcp"]
  },
  "platforms": ["claude", "cursor"]
}
```

**필드 설명:**
- `name`: mcpServers 객체의 키로 사용
- `description`: references/mcps.md 등록용 설명
- `install_type`: 설치 패턴 (`config_merge` | `cli_delegate` | `package_install`)
- `config`: `mcpServers.{name}` 아래에 들어갈 설정 객체
- `platforms`: 설치 대상 플랫폼 목록

> `cli_delegate`, `package_install` 타입은 install-mac.sh에서는 스킵하고, 안내 메시지만 출력.
> 실제 실행은 런타임에 skill-manager 또는 알투가 처리.

### 3.2 JSON 머지 함수 (`merge_mcp_config`)

python3을 사용하여 기존 mcp.json에 새 서버 항목을 안전하게 머지한다.

```bash
merge_mcp_config() {
    local target="$1"    # ~/.claude/mcp.json
    local name="$2"      # "shadcn"
    local config="$3"    # '{"command":"npx","args":[...]}'

    python3 -c "
import json, os, sys
target = sys.argv[1]
name = sys.argv[2]
config = json.loads(sys.argv[3])

if os.path.exists(target):
    with open(target) as f:
        data = json.load(f)
else:
    data = {}

data.setdefault('mcpServers', {})

if name in data['mcpServers']:
    # 이미 등록된 서버는 스킵 (사용자 설정 보존)
    sys.exit(0)

data['mcpServers'][name] = config

with open(target, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$target" "$name" "$config"
}
```

**핵심 원칙:**
- 기존 키가 있으면 **덮어쓰지 않고 스킵** (사용자 커스텀 보존)
- 파일이 없으면 신규 생성
- python3 미설치 시 경고 후 스킵

### 3.3 MCP 설치 함수 (`install_mcp`)

`opal/core/mcps/*.json` 파일을 순회하며 플랫폼별 mcp.json에 머지한다.

```bash
install_mcp() {
    local mcp_src="$FRAMEWORK_ROOT/opal/core/mcps"

    if [[ ! -d "$mcp_src" ]]; then
        warn "opal/core/mcps/ 디렉토리가 없습니다 (스킵)"
        return
    fi

    if ! command -v python3 &>/dev/null; then
        warn "python3이 없어 MCP 설정을 자동 머지할 수 없습니다"
        return
    fi

    local count=0
    for mcp_file in "$mcp_src"/*.json; do
        [[ -f "$mcp_file" ]] || continue

        local name config install_type platforms
        name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['name'])")
        config=$(python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))")
        install_type=$(python3 -c "import json; print(json.load(open('$mcp_file'))['install_type'])")
        platforms=$(python3 -c "import json; print(' '.join(json.load(open('$mcp_file'))['platforms']))")

        # config_merge만 자동 설치, 나머지는 안내만
        if [[ "$install_type" != "config_merge" ]]; then
            info "  $name: $install_type 타입 — 수동 설치 필요 (npx/npm)"
            continue
        fi

        for platform in $platforms; do
            local target=""
            case "$platform" in
                claude) target="$USER_HOME/.claude/mcp.json" ;;
                cursor) target="$USER_HOME/.cursor/mcp.json" ;;
            esac

            if [[ -n "$target" ]]; then
                mkdir -p "$(dirname "$target")"
                merge_mcp_config "$target" "$name" "$config"
                ((count++))
            fi
        done

        success "$name → 설정 머지 완료"
    done

    [[ $count -eq 0 ]] && info "머지할 MCP 서버가 없습니다" || success "MCP 서버 ${count}건 설정 완료"
}
```

### 3.4 install_opal() 연결

기존 `install_opal()` 함수 끝에 MCP 설치를 추가:

```bash
# install_opal() 끝에 추가
echo ""
info "MCP 서버 설정..."
install_mcp
```

## 4. 의존성 및 환경 변경

| 항목 | 내용 |
|------|------|
| python3 | macOS 기본 포함. 없는 경우 경고 후 스킵 |
| 추가 패키지 | 없음 |
| 새 디렉토리 | `opal/core/mcps/` |

## 5. 테스트 전략

| 테스트 | 검증 내용 | 방법 |
|--------|----------|------|
| 신규 설치 | mcp.json 없는 상태에서 생성 확인 | 임시 디렉토리에서 install_mcp 실행 |
| 머지 설치 | 기존 mcp.json에 새 항목 추가 확인 | 기존 설정이 있는 상태에서 실행 |
| 중복 스킵 | 이미 등록된 서버 덮어쓰기 안 함 확인 | 동일 서버 두 번 실행 |
| python3 없음 | 경고 메시지 출력 후 스킵 | PATH에서 python3 제외 후 실행 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 mcp.json 손상 | 사용자 MCP 설정 유실 | 기존 키 스킵 정책 + 파일 존재 시 백업 고려 |
| python3 JSON 파싱 오류 | 설치 중단 | try/except로 감싸고 실패 시 스킵 |
| 향후 MCP 포맷 변경 | 템플릿 호환성 | 템플릿 스키마를 README.md에 문서화하여 유지보수 용이 |

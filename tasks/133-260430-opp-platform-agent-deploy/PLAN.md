# PLAN: 멀티 플랫폼 에이전트 배포 메커니즘 구축

> 작성일: 2026-04-30 | 입력: TASK.md | 출력: PLAN.md
> 적용 스킬: op-task-plan
> 모드: agentic

---

## 0. 하네스 제약 (PLAN 단계 [MUST])

PLAN 단계에서 워커가 반드시 준수하고, EXECUTE 단계 워커도 그대로 승계하는 제약이다.

- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." → PLAN 단계는 PLAN.md 외 어떤 파일도 생성·수정하지 않는다.
- [MUST] `` `.opal/AGENT.md` §확정 기준 #2 ``: "`~/.opal/` 경로 파일을 Edit/Write하지 않는다. 수정 대상은 반드시 소스 경로에서 찾아 수정한다." → 모든 변환 규칙·함수는 소스 경로(`opal/`, `scripts/`)에 작성한다.
- [MUST] `` `.opal/AGENT.md` §금지사항 §배포 관련 ``: "`install-mac.sh` 실행, `~/.opal/`에 파일 직접 복사/생성/수정 금지. 캡틴이 명시적으로 '배포해줘'라고 지시하지 않는 한 배포 행위를 수행하지 않는다." → install-mac.sh 자체는 본 태스크의 수정 대상이지만, **실행은 본 태스크 범위 밖**이다.
- [MUST] `` `opal/core/references/harness/citation-rules.md` §0 ``: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다." → 4개 플랫폼 조사 결과는 §1 참조 문서 테이블 + §2.1 §2.2 §2.3 §2.4 인라인 인용으로 뒷받침된다.

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 어댑터 자동 생성 함수 추가 대상 |
| D-2 | 소스 | OPAL 에이전트 정의 | `opal/agents/` (12개) + `agents/` (1개) | 변환 입력 SSOT — 13개 AGENT.md |
| D-3 | 설계 | 에이전트 카탈로그 | `opal/core/references/agents.md` | 에이전트 목록 + 변환 규칙 추가 후보 위치 |
| D-4 | 설계 | 모델 매핑 SSOT | `opal/core/references/opal-model-mapping.md` | `light/standard/advanced` → 플랫폼 모델명 매핑 (§2 매핑 테이블) |
| D-5 | 설계 | PROJECT.md | `docs/PROJECT.md` | 플랫폼 독립성 원칙(§프로젝트 원칙 #3) |
| D-6 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 금지 규칙(§금지사항 §배포 관련) + `~/.opal/` 직접 수정 금지(§확정 기준 #2) |
| D-7 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | PLAN 산출물 인용 의무 + [MUST] 포맷 |
| D-8 | 외부 | Claude Code 서브에이전트 공식 문서 | [Claude Code — Create custom subagents](https://code.claude.com/docs/en/sub-agents) | 등록 경로 `~/.claude/agents/{name}.md` + frontmatter 스키마 + 모델 alias `sonnet/opus/haiku/inherit` |
| D-9 | 외부 | Cursor 서브에이전트 공식 문서 | [Cursor Docs — Subagents](https://cursor.com/docs/subagents) | 등록 경로 `~/.cursor/agents/` + frontmatter 스키마 + 모델 `inherit/fast/<full-id>` |
| D-10 | 외부 | Gemini CLI 서브에이전트 공식 문서 | [Gemini CLI — Subagents](https://geminicli.com/docs/core/subagents/) + [GitHub 원본](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md) | 등록 경로 `~/.gemini/agents/` + frontmatter 스키마 + `model` 기본 `inherit` |
| D-11 | 외부 | Antigravity 서브에이전트 공식 입장 | [Google AI Developers Forum — Antigravity sub agents](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) | 커스텀 서브에이전트 미지원 — 기능 요청 단계, 내부 검토 중(2026-03) |
| D-12 | 외부 | Antigravity Agent Skills 공식 문서 | [Antigravity — Agent Skills](https://antigravity.google/docs/skills) | Antigravity는 Skills(`.agent/skills/`, `~/.gemini/antigravity/skills/`)만 지원 — Sub-agent 메커니즘 부재 |

### 1.2 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `scripts/install-mac.sh` | 통합 설치 스크립트 — OPAL 에이전트를 `~/.opal/agents/`로 배포 | ✅ 신규 함수 추가 | `scripts/install-mac.sh:456-486` (현재 `install_opal()` 내부 에이전트 복사 블록), `scripts/install-mac.sh:561` (`install_claude_permissions` 호출 위치 — 어댑터 함수 호출 삽입 후보) |
| `opal/core/references/agents.md` | 에이전트 카탈로그 — 13개 등록 | ✅ 변환 규칙 섹션 추가 | `opal/core/references/agents.md:178-247` (에이전트 추가 가이드 + 향후 추가 에이전트) |
| `opal/core/references/opal-model-mapping.md` | 모델 레벨 SSOT | ⚠️ 경량 갱신 (Cursor/Antigravity 컬럼/주석 추가는 별도 결정) | `opal/core/references/opal-model-mapping.md:17-25` (§2 플랫폼별 매핑 테이블) |
| `opal/agents/{*}/AGENT.md` (12개) + `agents/wtm-agent/AGENT.md` (1개) | OPAL 에이전트 SSOT — 변환 입력 | ❌ 변경 없음 | `opal/agents/opal-be-agent/AGENT.md:1-9` (frontmatter 예시), `opal/agents/opal-task-agent/AGENT.md:1-8` (frontmatter 예시) |

> 근거 포맷: `경로:N-M`. citation-rules §2.2 적용.

### 1.3 4개 플랫폼 sub-agent 메커니즘 조사 결과

플랫폼별 공식 문서 확인 결과를 표로 정리한다. 각 행의 결정은 §1.1 D-8 ~ D-12 근거에 기반한다.

| 항목 | Claude Code | Cursor | Gemini CLI | Antigravity |
|------|------------|--------|-----------|------------|
| 메커니즘 존재 | ✅ 존재 | ✅ 존재 (v2.4+) | ✅ 존재 | ❌ **부재** (기능 요청 상태) |
| 사용자 등록 경로 | `~/.claude/agents/{name}.md` | `~/.cursor/agents/{name}.md` | `~/.gemini/agents/{name}.md` | (없음 — Skills만 존재) |
| 프로젝트 등록 경로 | `.claude/agents/` | `.cursor/agents/` | `.gemini/agents/` | (해당 없음) |
| 파일 형식 | YAML frontmatter + Markdown body | YAML frontmatter + Markdown body | YAML frontmatter + Markdown body | (해당 없음) |
| 필수 frontmatter | `name`, `description` | (없음 — 모두 선택; 누락 시 파일명 기반 derive) | `name`, `description` | (해당 없음) |
| 선택 frontmatter | `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`, `initialPrompt` | `model`(inherit/fast/full-id), `readonly`, `is_background` | `kind(local/remote)`, `tools`, `mcpServers`, `model`, `temperature`, `max_turns`, `timeout_mins` | (해당 없음) |
| `model` 허용 값 | `sonnet` / `opus` / `haiku` / 풀 ID(`claude-opus-4-7` 등) / `inherit` (기본) | `inherit` (기본) / `fast` / 풀 ID(`claude-4-sonnet`, `gpt-5-mini` 등) | `gemini-3-preview`, `gemini-3-flash-preview` 등 풀 ID / 기본 `inherit` | (해당 없음) |
| 본문(Body) 처리 | "system prompt" — frontmatter 외 본문이 그대로 system prompt가 됨 | "system prompt" — 본문이 system prompt | "The body of the markdown file becomes the agent's System Prompt." | (해당 없음) |
| 디스패치 호출 | Task tool의 `subagent_type`(name) 자동/명시 위임 | Agent tool에 의한 자동 위임 + `/name` 명시 호출 + 자연 발화 인식 | 자동 위임 + `@subagent-name` 명시 호출 | (해당 없음) |
| 적용 결정 | ✅ 적용 (R-1) | ✅ 적용 (R-2) | ✅ 적용 (R-3) | ❌ **적용 제외 (R-4)** — 사유: "this feature request has been escalated to the relevant internal teams for review" (→ D-11) |

> Antigravity 적용 제외 사유: 공식 Google 답변에 따르면 커스텀 서브에이전트는 "기능 요청 단계 — 내부 팀 검토 중"이며 (→ D-11), 공식 문서 [Agent Skills](https://antigravity.google/docs/skills)는 SKILL.md 기반 "지식 패키징 시스템"으로 sub-agent 메커니즘과 다른 차원의 추상화다 (→ D-12). 본 태스크는 "OPAL 에이전트를 sub-agent로 등록"이 목적이므로, Antigravity는 향후 기능 출시 시 재조사 대상으로 유보한다.

### 1.4 현재 상태

**OPAL 에이전트 SSOT (총 13개)**:
- `opal/agents/`: opal-be-agent, opal-convention-checker, opal-db-agent, opal-fe-agent, opal-plan-agent, opal-planning-agent, opal-sdd-action-agent, opal-security-checker, opal-task-action-agent, opal-task-agent, opal-task-qa-agent, opal-test-agent (12개)
- `agents/`: wtm-agent (1개)

**install-mac.sh 현재 동작 (`install_opal()`)**:
- `scripts/install-mac.sh:456-486`: OPAL 에이전트를 `~/.opal/agents/{name}/AGENT.md` 형태로 디렉토리째 복사한다 (`install_dir` 헬퍼 사용).
- `scripts/install-mac.sh:530-564`: `~/.claude/CLAUDE.md`, `~/.cursor/rules/000-opal-agent.mdc`, `~/.gemini/GEMINI.md`에 OPAL 부트스트래퍼 마커 블록을 삽입한다 (`install_opal_section`).
- `scripts/install-mac.sh:561`: `install_claude_permissions` 호출 — `~/.claude/settings.json`의 `permissions.allow`에 `Read(~/.opal/**)` 추가.
- `scripts/install-mac.sh:564`: `install_gemini_config` 호출 — `~/.gemini/settings.json`의 `context.includeDirectories`에 `~/.opal/`, `~/.gemini/` 추가.

**부재**:
- `~/.claude/agents/`, `~/.cursor/agents/`, `~/.gemini/agents/`로의 어댑터 자동 생성 함수가 install-mac.sh에 **없다** (→ D-1, TASK §배경 분석).

**모델 매핑 SSOT 상태**:
- `opal/core/references/opal-model-mapping.md` §2: Claude/Gemini/OpenAI 3컬럼만 정의. Cursor 컬럼은 §4의 "사용자 설정 모델 제공자에 따라 매핑이 달라진다"는 주석으로 처리됨 (→ D-4).
- `opal/runtimes/framework/data/model_mapping.json`: **존재하지 않음** (TASK §관련 문서 D-3에서 언급되었으나 실제 부재). 본 태스크에서는 신규 생성하지 않고 markdown SSOT를 활용한다 (§3 SSOT 결정 참조).

### 1.5 영향 범위

- **scripts/install-mac.sh**: 신규 함수 3개 추가 + 호출 시점 1곳 추가. 기존 함수는 변경 없음 (회귀 위험 낮음).
- **opal/core/references/agents.md**: §변환 규칙 신규 섹션 추가. 기존 카탈로그/매핑 테이블/폴백 규칙은 변경 없음.
- **opal/core/references/opal-model-mapping.md**: 갱신 없음 (이번 태스크 범위에서는 §3 SSOT 결정에 따라 agents.md에 변환 규칙 통합).
- **OPAL 에이전트 본문**: **변경 금지** ([MUST] TASK §확정된 설계 방향 #4 "OPAL `AGENT.md` 본문은 워커 system prompt로 그대로 사용").
- **사용자 데이터 보존**: `~/.claude/agents/`, `~/.cursor/agents/`, `~/.gemini/agents/`에 사용자 수동 작성 파일이 있을 수 있음 → **OPAL 어댑터는 OPAL 에이전트 이름과 동일한 파일만 덮어쓰고, 사용자 파일은 보존한다** (cleanup 시 OPAL 마커 또는 화이트리스트 사용).

---

## 2. 구현 계획

### 2.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| (없음) | - | 본 태스크는 기존 파일 수정으로 완결된다 | `opal/runtimes/framework/data/model_mapping.json`은 신규 생성하지 않는다 (→ §3 SSOT 결정) |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `scripts/install-mac.sh` | 어댑터 생성 함수 3개 추가(`install_claude_agents`, `install_cursor_agents`, `install_gemini_agents`) + 공통 헬퍼 1개(`emit_platform_agent_adapter`) + `install_opal()` 부트스트래퍼 블록 뒤에서 호출 | `scripts/install-mac.sh:456-486` (에이전트 복사 위치), `:561-564` (호출 삽입 위치 후보) |
| M-2 | `opal/core/references/agents.md` | §변환 규칙 신규 섹션 추가 — 플랫폼별 frontmatter 변환 규칙 표 + Antigravity 적용 제외 사유 | `opal/core/references/agents.md:178-247` (에이전트 추가 가이드 옆에 신규 §추가) |
| M-3 | `opal/core/references/agents.md` 변경이력 | 변경 행 추가 | `opal/core/references/agents.md` 변경이력 테이블 (현재 없으면 신규 섹션 추가) |
| M-4 | `scripts/install-mac.sh` 헤더 주석 | "v{X} — 플랫폼 어댑터 생성 추가" 주석 한 줄 추가 (간이 변경이력) | `scripts/install-mac.sh:1-7` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | - | 기존 자산 삭제 없음 |

### 2.2 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 변환 규칙 SSOT 작성 (agents.md §변환 규칙) | `opal/core/references/agents.md` | 중 |
| 2 | install-mac.sh 공통 헬퍼 `emit_platform_agent_adapter` 추가 | `scripts/install-mac.sh` | 중 |
| 3 | install-mac.sh `install_claude_agents()` 함수 추가 | `scripts/install-mac.sh` | 중 |
| 4 | install-mac.sh `install_cursor_agents()` 함수 추가 | `scripts/install-mac.sh` | 하 (Claude와 거의 동일) |
| 5 | install-mac.sh `install_gemini_agents()` 함수 추가 | `scripts/install-mac.sh` | 하 (Claude와 거의 동일) |
| 6 | install-mac.sh `install_opal()` 본문에서 3개 함수 호출 | `scripts/install-mac.sh:561` 직후 | 하 |
| 7 | 변경이력 갱신 (agents.md, install-mac.sh 헤더 주석) | 양 파일 | 하 |
| 8 | 검증 절차 문서화 (DONE.md 작성 시 사용할 체크리스트는 PLAN §5에 존재) | (실제 실행은 EXECUTE 단계 또는 캡틴이 명시 지시) | 하 |

> 의존성 원칙: 변환 규칙 SSOT(Step 1)을 먼저 확정해야 install-mac.sh 함수 설계의 일관성이 보장된다 (→ D-3).

### 2.3 핵심 설계

#### M-1: scripts/install-mac.sh — 어댑터 생성 함수 추가

##### 공통 헬퍼: `emit_platform_agent_adapter`

**입력**:
- `$1`: 소스 에이전트 디렉토리 (예: `~/.opal/agents/opal-be-agent/` — install_opal 직후이므로 배포본 사용 가능)
- `$2`: 출력 파일 경로 (예: `$USER_HOME/.claude/agents/opal-be-agent.md`)
- `$3`: 플랫폼 ID (`claude` | `cursor` | `gemini`)

**의사 코드**:

```bash
emit_platform_agent_adapter() {
    local src_dir="$1"
    local dst_file="$2"
    local platform="$3"

    local agent_md="$src_dir/AGENT.md"
    [[ -f "$agent_md" ]] || return 0

    # 1) frontmatter / body 분리 (Python 사용 — bash awk보다 견고)
    /usr/bin/python3 - "$agent_md" "$dst_file" "$platform" <<'PYEOF'
import re, sys, yaml  # PyYAML이 venv에 설치되어 있음 (opal/tools/requirements.txt 확인 필요)
src, dst, platform = sys.argv[1], sys.argv[2], sys.argv[3]

text = open(src).read()
m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.DOTALL)
if not m:
    sys.exit(0)  # frontmatter 없는 파일은 스킵

fm = yaml.safe_load(m.group(1))
body = m.group(2)

# 2) frontmatter 변환 (플랫폼별 변환 규칙)
out_fm = {
    'name': fm['name'],
    'description': (fm.get('description') or '').strip(),
}
# model 매핑
opal_model = fm.get('model', 'standard')
mapping = {
    'claude': {'light': 'haiku', 'standard': 'sonnet', 'advanced': 'opus'},
    'cursor': {'light': 'inherit', 'standard': 'inherit', 'advanced': 'inherit'},  # Cursor는 사용자 설정에 위임
    'gemini': {'light': 'gemini-2.5-flash-lite', 'standard': 'gemini-2.5-flash', 'advanced': 'gemini-2.5-pro'},
}
out_fm['model'] = mapping[platform].get(opal_model, 'inherit')

# icon 등 OPAL 전용 필드는 제거 (각 플랫폼 스키마에 없음)
# Claude는 color 필드 지원하나, 본 태스크에서는 의도적으로 미설정 (단순화)

# 3) OPAL 자체 로드 헤더 주입 — body 앞에 PM/스킬 자체 로드 안내
header = (
    f"<!-- AUTO-GENERATED by install-mac.sh from ~/.opal/agents/{fm['name']}/AGENT.md. DO NOT EDIT. -->\n"
    f"<!-- SSOT: opal/agents/{fm['name']}/AGENT.md (project), ~/.opal/agents/{fm['name']}/AGENT.md (deploy). -->\n\n"
)

# 4) 출력
import os
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, 'w') as f:
    f.write('---\n')
    f.write(yaml.safe_dump(out_fm, allow_unicode=True, sort_keys=False).strip() + '\n')
    f.write('---\n\n')
    f.write(header)
    f.write(body)
PYEOF
}
```

설계 결정 근거:
- frontmatter 분리에 Python+PyYAML 사용 — bash awk/sed로 다중라인 description(`|` 블록 스타일)을 견고히 처리하기 어려움. install-mac.sh는 이미 `python3`을 사용한다 (→ `scripts/install-mac.sh:99-159` `merge_mcp_config`/`merge_hooks_config`). PyYAML은 `opal/tools/requirements.txt`로 venv에 설치되므로, **순수 stdlib만 쓰는 폴백** 또는 venv 사용을 EXECUTE Step 2에서 결정한다.
- `name`/`description`/`model` 3필드만 출력 — 각 플랫폼 스키마 공통 핵심 (→ D-8 "Only `name` and `description` are required", D-9 frontmatter 표 §2, D-10 frontmatter 표 §1).
- `icon`은 모든 플랫폼에서 미지원 → 제거 (TASK §확정된 설계 방향 #3 "icon 등 잡 필드는 플랫폼별로 무시 또는 제거").
- `model: standard/light/advanced` → 플랫폼별 모델명 변환 — `opal/core/references/opal-model-mapping.md` §2 매핑 표를 그대로 사용 (→ D-4). Cursor는 `inherit` 통일 (사용자 모델 설정 위임 — opal-model-mapping §4 "Cursor 특이사항" 근거).
- 본문 앞에 `AUTO-GENERATED` 주석 헤더 삽입 — 캡틴이 어댑터 파일을 직접 수정하지 못하도록 가드. SSOT 경로 명시 (→ TASK §확정된 설계 방향 #1 "`~/.opal/agents/`(OPAL SSOT)는 변경 없음 — 모든 어댑터는 SSOT에서 변환 생성").

##### `install_claude_agents()`

```bash
install_claude_agents() {
    local agents_src="$USER_HOME/.opal/agents"
    local agents_dst="$USER_HOME/.claude/agents"

    [[ -d "$agents_src" ]] || { warn "~/.opal/agents 부재 — Claude 어댑터 스킵"; return; }
    mkdir -p "$agents_dst"

    local count=0
    for agent_dir in "$agents_src"/*/; do
        [[ -d "$agent_dir" ]] || continue
        local agent_name; agent_name="$(basename "$agent_dir")"
        emit_platform_agent_adapter "$agent_dir" "$agents_dst/$agent_name.md" "claude"
        ((count++))
    done

    success "Claude Code 어댑터 ${count}개 → $agents_dst/"
}
```

##### `install_cursor_agents()` / `install_gemini_agents()`

`install_claude_agents()`와 동일 구조. `agents_dst`만 다름 (`~/.cursor/agents`, `~/.gemini/agents`)이고, `emit_platform_agent_adapter`의 platform 인자만 `cursor`/`gemini`로 바꾼다.

##### Antigravity (R-4 적용 제외)

해당 함수 미생성. install-mac.sh 본문 주석으로 사유를 기재한다:

```bash
# Antigravity는 커스텀 서브에이전트를 미지원 (2026-04 기준).
# Google 공식 응답: "feature request escalated to internal teams for review."
# 출처: https://discuss.ai.google.dev/t/antigravity-sub-agents/114381
# 참고: Antigravity는 Skills(`.agent/skills/`, `~/.gemini/antigravity/skills/`)만 제공.
# 향후 기능 출시 시 본 스크립트에 install_antigravity_agents() 추가 검토.
```

##### 호출 위치

`scripts/install-mac.sh:561` `install_claude_permissions` 호출 직후, `install_gemini_config` 호출 직전에 신규 호출 블록 삽입:

```bash
# ── 플랫폼 sub-agent 어댑터 ──
install_claude_agents
install_cursor_agents
install_gemini_agents
# Antigravity는 미지원 (위 주석 참조)
```

근거: 어댑터 생성은 `~/.opal/agents/`로의 OPAL 배포가 끝난 뒤(`scripts/install-mac.sh:485` `agent_count` 출력 직후 영역) + 부트스트래퍼 마커 삽입(`:542-558`)이 끝난 뒤에 수행해야 한다. 그래야 `~/.opal/agents/` 디렉토리가 변환 입력 SSOT로 안정 확보된다 (→ TASK §확정된 설계 방향 #1).

#### M-2: opal/core/references/agents.md — §변환 규칙 신규 섹션

`opal/core/references/agents.md:178` "## 에이전트 추가 가이드" 직전에 다음 섹션을 추가한다 (또는 §전문 에이전트 매핑 테이블 직후 §폴백 규칙 직전).

##### 추가 섹션 개요

```markdown
## 플랫폼 sub-agent 어댑터 변환 규칙

OPAL 에이전트(`~/.opal/agents/{name}/AGENT.md`)를 각 AI 플랫폼의 sub-agent로 등록하기 위한 어댑터 변환 규칙이다.
`scripts/install-mac.sh`의 `install_{claude,cursor,gemini}_agents` 함수가 이 규칙을 참조한다.

### 플랫폼별 메커니즘 (2026-04 기준)

| 플랫폼 | 메커니즘 | 등록 경로 | 공식 문서 |
|--------|---------|----------|----------|
| Claude Code | 지원 | `~/.claude/agents/{name}.md` | [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents) |
| Cursor | 지원 (v2.4+) | `~/.cursor/agents/{name}.md` | [Cursor Subagents](https://cursor.com/docs/subagents) |
| Gemini CLI | 지원 | `~/.gemini/agents/{name}.md` | [Gemini CLI Subagents](https://geminicli.com/docs/core/subagents/) |
| Antigravity | **미지원** | (없음) | [Sub-agents 기능 요청](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) — 내부 팀 검토 중 |

### frontmatter 변환 규칙

OPAL frontmatter → 플랫폼 frontmatter:

| OPAL 필드 | Claude Code | Cursor | Gemini CLI |
|----------|------------|--------|-----------|
| `name` | `name` (그대로) | `name` (그대로) | `name` (그대로) |
| `description` | `description` (그대로) | `description` (그대로) | `description` (그대로) |
| `model: light` | `model: haiku` | `model: inherit` | `model: gemini-2.5-flash-lite` |
| `model: standard` | `model: sonnet` | `model: inherit` | `model: gemini-2.5-flash` |
| `model: advanced` | `model: opus` | `model: inherit` | `model: gemini-2.5-pro` |
| `icon` | (제거 — 미지원) | (제거 — 미지원) | (제거 — 미지원) |
| (기타 OPAL 전용 필드) | (제거) | (제거) | (제거) |

> Cursor는 사용자가 IDE에서 모델 제공자를 직접 설정하므로 `inherit`로 위임한다 (→ `opal/core/references/opal-model-mapping.md` §4 Cursor 특이사항).

### 본문(System Prompt) 처리

OPAL `AGENT.md` 본문은 **변경 없이** 어댑터 markdown body로 그대로 복사된다.
어댑터 파일 상단에 `AUTO-GENERATED` 주석 헤더를 삽입하여 직접 편집을 가드한다 (편집은 `opal/agents/{name}/AGENT.md` 소스에서 수행).

### Antigravity 미지원 처리

Antigravity는 2026-04 기준 커스텀 sub-agent를 지원하지 않는다 ([공식 응답](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) — "feature request has been escalated to the relevant internal teams for review").
대안 메커니즘인 [Agent Skills](https://antigravity.google/docs/skills)는 SKILL.md 기반 지식 패키징 시스템이며 sub-agent 추상화와 다르므로, 본 태스크 범위에서 적용 제외한다.
향후 Antigravity가 sub-agent를 출시하면 `install_antigravity_agents()`를 추가하고 이 표를 갱신한다.
```

설계 결정 근거:
- 변환 규칙을 `agents.md`에 두는 이유: §3 SSOT 결정 참조.
- 모든 매핑은 [MUST] 토큰 — 재해석 여지 차단을 위해 표 형태 + 풀 포맷 인용 (citation-rules §2.5).

#### M-3 / M-4: 변경이력

- `opal/core/references/agents.md`: 파일 끝에 변경이력 테이블이 없으면 신규 섹션 추가, 있으면 행 추가.
- `scripts/install-mac.sh`: 헤더 주석(`scripts/install-mac.sh:1-7`)에 한 줄 추가 — 형식은 기존 install-mac.sh 컨벤션에 맞춤 (변경이력 테이블이 없으므로 인라인 주석 한 줄로 처리).

---

## 3. SSOT 위치 결정 (frontmatter 변환 규칙)

TASK §미확정 사항: "frontmatter 변환 규칙 SSOT의 정확한 위치 (model_mapping.json 확장 vs agents.md 신규 섹션 vs 신규 변환 규칙 파일)".

### 후보 안 비교

| 안 | 위치 | 장점 | 단점 |
|----|------|------|------|
| (a) | `opal/runtimes/framework/data/model_mapping.json` 확장 | 데이터 SSOT 패턴 — bash/Python에서 JSON 파싱 일관 | **파일 자체가 부재** (§1.4 확인). 신규 생성 필요. JSON으로는 "Antigravity 적용 제외 사유"같은 산문 메타데이터 표현이 어렵다 |
| (b) | `opal/core/references/agents.md` 신규 §추가 | 에이전트 카탈로그 옆 — 사람·AI 모두 동일 위치에서 스키마 + 매핑 + 적용 제외 사유까지 일괄 조회. 인용 비용 최저 (citation-rules §2.1) | 산문 표 — 자동 파싱 시 markdown 표 파서 필요. install-mac.sh는 표를 직접 읽지 않고 함수에 매핑을 인라인 작성 (안 (b) 채택 시) |
| (c) | 신규 파일 `opal/core/references/platform-agent-mapping.md` | 단일 책임 원칙 — 변환 규칙만 분리 | 신규 파일은 디스커버리 비용 — agents.md를 거쳐 한 번 더 점프해야 함. 현재 13개 에이전트 + Antigravity 제외 사유 분량은 1개 섹션으로 충분 |

### 최종 결정: **안 (b)**

근거:
1. **"카탈로그가 자기 변환 규칙을 동봉"** — 에이전트 추가 시 (`agents.md:178-204` "에이전트 추가 가이드") 변환 규칙도 같은 파일에서 갱신되어 일관성 자동 보장.
2. **install-mac.sh 함수의 매핑 데이터는 인라인 정의** — 어차피 bash dict로 들고 있어야 하므로, JSON SSOT를 별도로 두면 "JSON과 bash 인라인의 이중 진실" 문제 발생. agents.md 표는 사람/AI의 공식 문서고, install-mac.sh는 배포 도구로서 매핑을 인라인 보유 (변경 시 양쪽 동시 갱신 — 변경 빈도 낮으므로 수용 가능).
3. **`opal/runtimes/framework/data/`는 현재 부재** (§1.4) — 본 태스크 범위에서 신규 디렉토리/파일을 만들 의무가 없다. TASK §확정된 설계 방향 #5는 "활용 또는"으로 둘 중 한 곳을 허용한다.
4. **"Antigravity 적용 제외 사유" 산문 메타데이터 수용** — JSON으로는 자연스럽지 않으나 markdown은 자연스럽다 (→ D-11 인용을 그대로 표에 박아둘 수 있다).

> 향후 자동 생성 도구가 필요해지면, agents.md 표를 자동 파싱하여 model_mapping.json을 derive하는 어댑터를 별도 태스크로 분리한다.

---

## 4. 실행 체크리스트

> 총 8개 Step | Phase 4개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | 변환 규칙 SSOT 확정 — 후속 모든 Step의 기준 |
| 2 | 2 | 순차 | 공통 헬퍼 — Step 3-5의 의존 |
| 3 | 3, 4, 5 | 병렬 | 동일 파일(`install-mac.sh`)을 수정하므로 **실제로는 순차 작성**하되, 함수 정의가 독립적이라 논리상 병렬 가능 |
| 4 | 6 | 순차 | install_opal() 본문 호출 추가 — Step 3-5 완료 의존 |
| 4 | 7 | 순차 | 변경이력 갱신 — Step 1, 6 완료 의존 |
| 4 | 8 | 순차 | 검증 절차 (R-6) — 캡틴 명시 지시 시에만 실행 |

> Phase 3 비고: 동일 파일 내 함수이므로 EXECUTE 워커는 한 번에 묶어 작성한다 (편집 충돌 방지).

### Step 1: 변환 규칙 SSOT 작성 (agents.md §추가)

- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**:
  - `## 에이전트 추가 가이드` 섹션 직전(또는 §전문 에이전트 매핑 테이블 직후, §폴백 규칙 직전)에 `## 플랫폼 sub-agent 어댑터 변환 규칙` 섹션 신규 추가
  - 본 PLAN §2.3 M-2의 표/문구를 그대로 옮긴다 (4개 플랫폼 메커니즘 표 + frontmatter 변환 규칙 표 + 본문 처리 + Antigravity 미지원 처리)
  - 모든 외부 참조는 `[사이트명](URL)` 포맷 (citation-rules §2.3)
- **완료 기준**:
  - agents.md를 Read하면 §플랫폼 sub-agent 어댑터 변환 규칙 섹션이 존재한다
  - 4개 플랫폼 모두 표에 등장한다 (Claude/Cursor/Gemini/Antigravity)
  - Antigravity 미지원 사유에 [discuss.ai.google.dev URL](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) 인용이 포함된다
- **테스트**: `grep -n '플랫폼 sub-agent 어댑터 변환 규칙' opal/core/references/agents.md` → 1행 매치
- **의존**: 없음

### Step 2: install-mac.sh 공통 헬퍼 추가

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - `install_gemini_config()` 함수 직전(또는 직후) 영역에 `emit_platform_agent_adapter()` 함수 추가
  - 본 PLAN §2.3 M-1 의사 코드를 실제 bash + Python heredoc으로 구현
  - frontmatter 분리: Python `re` + `yaml` 사용. `yaml`이 stdlib에 없으므로 `~/.opal/.venv/bin/python3`을 사용하거나, 더 간단히 `awk`로 frontmatter/body 경계를 찾고 `yq`/Python으로 파싱
  - 폴백: PyYAML 미설치 시에도 동작하도록 stdlib만 사용하는 간이 파서를 우선 적용 (정규식 기반 — frontmatter는 단순 key/value + multi-line description은 `|` 블록 스타일)
- **완료 기준**:
  - `bash -n scripts/install-mac.sh`가 syntax error 없음
  - `emit_platform_agent_adapter` 함수 정의가 파일에 존재한다
- **테스트**: `bash -n scripts/install-mac.sh; echo "syntax OK: $?"` → `syntax OK: 0`
- **의존**: Step 1

### Step 3: install_claude_agents() 함수 추가

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - `install_gemini_config()` 함수 영역 근처에 `install_claude_agents()` 추가
  - PLAN §2.3 M-1 §`install_claude_agents()` 의사 코드를 실제 bash로 구현
  - 입력: `~/.opal/agents/`, 출력: `~/.claude/agents/{name}.md`
- **완료 기준**:
  - 함수 정의 존재 + bash syntax 통과
  - 함수 본문 안에서 `emit_platform_agent_adapter "$agent_dir" "$agents_dst/$agent_name.md" "claude"` 호출
- **테스트**: `bash -n scripts/install-mac.sh` 통과 + `grep -c '^install_claude_agents()' scripts/install-mac.sh` → 1
- **의존**: Step 2

### Step 4: install_cursor_agents() 함수 추가

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: Step 3 함수를 복사하고 `claude` → `cursor`로 치환 (출력 경로 `~/.cursor/agents/`, platform 인자 `cursor`)
- **완료 기준**: 함수 정의 존재 + syntax 통과
- **테스트**: `grep -c '^install_cursor_agents()' scripts/install-mac.sh` → 1
- **의존**: Step 2

### Step 5: install_gemini_agents() 함수 추가

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: Step 3 함수를 복사하고 `claude` → `gemini`로 치환 (출력 경로 `~/.gemini/agents/`, platform 인자 `gemini`)
- **완료 기준**: 함수 정의 존재 + syntax 통과
- **테스트**: `grep -c '^install_gemini_agents()' scripts/install-mac.sh` → 1
- **의존**: Step 2

### Step 6: install_opal() 본문에 호출 추가

- [x] 완료
- **파일**: `scripts/install-mac.sh:561` 직후
- **작업 내용**:
  - `install_claude_permissions` 호출 라인 다음, `install_gemini_config` 호출 라인 직전에 신규 블록 삽입:
    ```bash
    # ── 플랫폼 sub-agent 어댑터 ──
    install_claude_agents
    install_cursor_agents
    install_gemini_agents
    # Antigravity 미지원 (~~사유 인용~~)
    ```
  - Antigravity 사유 주석 한 줄 — `# Antigravity: custom sub-agent 미지원 (https://discuss.ai.google.dev/t/antigravity-sub-agents/114381)`
- **완료 기준**:
  - `install_opal()` 함수 안에 3개 함수 호출이 추가된다
  - bash syntax 통과
- **테스트**: `bash -n scripts/install-mac.sh; sed -n '555,575p' scripts/install-mac.sh` → 3개 함수 호출 라인 보임
- **의존**: Step 3, 4, 5

### Step 7: 변경이력 갱신

- [x] 완료
- **파일**: `opal/core/references/agents.md` + `scripts/install-mac.sh:1-7` (헤더 주석)
- **작업 내용**:
  - agents.md 파일 끝에 변경이력 섹션이 없으면 추가하고, "v{X.Y} | 2026-04-30 | 알투 | 플랫폼 sub-agent 어댑터 변환 규칙 §추가 (133)" 행 삽입
  - install-mac.sh 헤더 주석에 한 줄 추가: `# v{X.Y} 2026-04-30: 플랫폼 sub-agent 어댑터 자동 생성 (Claude/Cursor/Gemini, Antigravity 미지원) — task 133`
- **완료 기준**: 양 파일에 변경이력 행 존재
- **테스트**: `grep '133' opal/core/references/agents.md scripts/install-mac.sh` → 양 파일 매치
- **의존**: Step 1, 6

### Step 8: 검증 절차 — R-6 (캡틴 명시 지시 시 실행)

- [ ] 완료
- **파일**: 실행 산출물은 DONE.md에 기록 (별도 단계)
- **작업 내용**:
  - **본 Step은 PLAN 산출물에 절차 정의만 기재** ([MUST] §0 Guards). 실제 실행은 캡틴이 "배포해줘 / 검증해줘"로 명시 지시할 때만 수행.
  - 검증 절차 (Claude Code 우선 — silent 폴백 가설 입증):
    1. 캡틴 승인 후 `bash scripts/install-mac.sh` 실행 (메뉴 1번 OPAL 설치)
    2. `ls ~/.claude/agents/` → 13개 `.md` 파일 존재 확인
    3. `head -10 ~/.claude/agents/opal-task-agent.md` → frontmatter `name: opal-task-agent`, `model: sonnet`(standard 매핑) 확인
    4. Claude Code 세션에서 Task tool로 `subagent_type: "opal-task-agent"` 디스패치 — 응답에서 `~/.opal/agents/opal-task-agent/AGENT.md`의 system prompt가 발화되는지 확인 (예: "범용 워커 / 오케스트레이터 프롬프트에서 스킬 경로 확인" 같은 문구 출현)
    5. `subagent_type: "general-purpose"`로 동일 작업을 분리 디스패치 → 응답이 4와 다른지 비교 (silent 폴백 가설이 맞다면 기존엔 둘 다 같았어야 함)
  - Cursor/Gemini는 캡틴이 별도 환경 가용 시 동일 패턴으로 검증
- **완료 기준**: DONE.md에 검증 결과(통과/실패) + 출력 로그 캡처 기록
- **테스트**: 위 5단계가 모두 통과 (또는 각 단계 결과 명시)
- **의존**: Step 6 + 캡틴의 명시 실행 허가 ([MUST] §0)

---

## 5. QA 체크리스트

### 5.1 기능 테스트

- [ ] **R-1 충족**: install-mac.sh 실행 후 `~/.claude/agents/`에 13개 `.md` 파일이 생성되고 각 frontmatter `name` 필드가 OPAL 에이전트 이름과 일치
- [ ] **R-2 충족**: `~/.cursor/agents/`에 13개 `.md` 파일 생성 + `name` 일치
- [ ] **R-3 충족**: `~/.gemini/agents/`에 13개 `.md` 파일 생성 + `name` 일치
- [ ] **R-4 충족**: install-mac.sh 안에 Antigravity 미지원 주석이 인용 URL과 함께 존재 + agents.md §변환 규칙에 미지원 사유 기재
- [ ] **R-5 충족**: agents.md §플랫폼 sub-agent 어댑터 변환 규칙 섹션이 존재하고, OPAL `light/standard/advanced` → 플랫폼 모델명 매핑 표가 명시됨
- [ ] **R-6 충족**: PLAN.md §4 Step 8에 silent 폴백 검증 절차가 명시됨 (5단계)
- [ ] **R-7 충족**: agents.md, install-mac.sh 양 파일에 변경이력 행 추가

### 5.2 일관성 테스트

- [ ] OPAL `AGENT.md` 본문은 변경되지 않는다 (`opal/agents/`, `agents/` 둘 다)
- [ ] 어댑터 파일 상단 `AUTO-GENERATED` 주석이 SSOT 경로를 정확히 가리킨다 (`opal/agents/{name}/AGENT.md` 또는 `~/.opal/agents/{name}/AGENT.md`)
- [ ] `name` 필드는 OPAL frontmatter와 어댑터 frontmatter가 1:1 일치
- [ ] `description`은 멀티라인(`|` 블록 스타일)도 깨지지 않고 보존됨
- [ ] `icon` 필드는 어댑터 frontmatter에서 제거됨 (Claude/Cursor/Gemini 모두 미지원)
- [ ] Cursor 어댑터의 `model` 필드는 모두 `inherit` (사용자 모델 설정 위임)
- [ ] Gemini 어댑터의 `model` 필드는 `gemini-2.5-flash-lite/flash/pro` 중 하나 (opal-model-mapping.md §2 일치)
- [ ] Claude 어댑터의 `model` 필드는 `haiku/sonnet/opus` 중 하나

### 5.3 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [ ] kebab-case 파일/폴더 네이밍 (어댑터 파일명 = OPAL 에이전트 이름 = kebab-case)
- [ ] YAML frontmatter 유효성 (각 어댑터 파일 `python3 -c "import yaml; yaml.safe_load(open('파일'))"` 통과)
- [ ] PLAN.md §1 참조 문서 테이블 12행 (D-1~D-12) 모두 유형/경로(URL)/참조 이유 컬럼 채워짐 (citation-rules §3.1)
- [ ] PLAN.md §2 핵심 설계 인라인 인용 — 모든 주요 설계 결정 뒤에 `(→ D-N)` 또는 풀 포맷
- [ ] PLAN.md §0에 [MUST] 4건 명시 (citation-rules §2.4)

---

## 6. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | Cursor `~/.cursor/agents/`가 v2.4 이전 버전에서 무시됨 | 어댑터 파일은 생성되나 Cursor가 인식 못 함 | install-mac.sh 안내 메시지에 "Cursor v2.4+ 필요" 명시 (→ D-9 [Cursor Subagents](https://cursor.com/docs/subagents)). 사용자 환경 감지는 본 태스크 범위 밖 |
| R-T2 | Antigravity 정책 변경 시 본 태스크 재방문 필요 | R-4 적용 제외 사유가 무효화될 수 있음 | agents.md §변환 규칙에 "향후 기능 출시 시 갱신" 주석 명시 (M-2). 정기 점검 메모리 등록은 별도 태스크 |
| R-T3 | OPAL frontmatter 멀티라인 `description: \|`이 PyYAML 외 파서에서 깨짐 | 어댑터 description 누락/오염 | EXECUTE Step 2에서 PyYAML 우선 사용. stdlib 폴백은 정규식 다중라인 매칭으로 처리하고, 실패 시 description 빈 문자열로 폴백 + warn 로그 |
| R-T4 | 사용자가 `~/.claude/agents/`에 수동 작성한 파일이 OPAL 어댑터와 이름 충돌 | 사용자 파일 덮어쓰기 위험 | OPAL 어댑터는 frontmatter `name`이 OPAL 에이전트 13개와 일치하는 파일만 생성한다. 사용자 파일은 다른 이름이면 보존됨. 동일 이름이라면 `AUTO-GENERATED` 헤더 부재 시 덮어쓰기 거부 + warn (EXECUTE Step 2에서 가드 로직 추가) |
| R-T5 | `model` 매핑 테이블이 향후 모델 출시로 stale | 어댑터 모델 필드가 구식 모델명 가리킴 | `opal/core/references/opal-model-mapping.md` §2 + agents.md §변환 규칙 표가 SSOT — 모델 출시 시 양 표 동시 갱신. 변경이력에 명시 |
| R-T6 | install-mac.sh 실행을 본 태스크 EXECUTE에서 워커가 자동 수행 시도 | [MUST] §0 #3 위반 — 배포 무단 실행 | EXECUTE 워커는 Step 8을 **건너뛰고** Step 1-7만 수행. Step 8은 캡틴 명시 지시 시 별도 실행 (이 PLAN의 §4 Step 8 의존성 컬럼 참조) |
| R-T7 (citation §7.1) | 영역 간 용어 불일치 — `subagent_type`(Claude) vs `agent name`(Cursor) vs `@agent-name`(Gemini) | 호출 인터페이스가 플랫폼별 다름 — 사용자 혼동 | 본 태스크는 어댑터 파일 생성까지만 다룸. 호출 시 인터페이스 차이는 PLAN §1.3 표에 명시되어 사용자 참조 가능. agents.md §변환 규칙에 "디스패치 인터페이스" 행 추가는 향후 enhancement |

---

## 7. 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-30 | 초기 작성 — 4개 플랫폼 조사(Claude/Cursor/Gemini 지원, Antigravity 미지원) + frontmatter 변환 규칙 + install-mac.sh 함수 설계 + 검증 절차 (133) |

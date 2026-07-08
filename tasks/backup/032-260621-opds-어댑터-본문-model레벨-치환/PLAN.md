# PLAN: install 어댑터 본문 model 레벨명 치환 — 액션 에이전트 sub-dispatch 모델 버그 수정

> 작성일: 2026-06-21 | 입력: TASK.md (ANALYSIS.md 없음 — 본 PLAN에서 직접 코드 분석 수행)
> 모드: Multi-Feature (F-001~F-005, 5개 기능)
> 적용 스킬: op-dev-plan v2.6 | 실행 모드: **복잡** (§6 참조)

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

oppd Phase 3 액션 에이전트(`opal-task-action-agent`·`opal-sdd-action-agent`)가 sub-worker를 디스패치할 때, 에이전트 본문에 적힌 모델 **레벨명**(`model: advanced/standard/light`)이 Agent 도구 `model` 파라미터에 그대로 전달되어 enum(`sonnet/opus/haiku/fable`) 검증을 위반한다. 근본 원인은 **install 어댑터(`emit_platform_agent_adapter`)가 frontmatter `model:`만 플랫폼 실모델명으로 변환하고 본문(body)은 verbatim 복사**하는 변환 경계 비대칭이다 (`scripts/install-mac.sh:556-565` vs `:601`). 확정 방향은 **옵션 A — 어댑터가 본문의 인라인 `model: <레벨>` sub-dispatch 토큰도 frontmatter와 동일한 `mapping[platform]` dict로 치환**한다. 소스는 플랫폼 중립(레벨명) 유지, 변환은 배포 시점 어댑터에서만 수행한다.

> **[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."** → 본문 레벨명 치환을 어댑터에만 추가하고, 에이전트 AGENT.md 본문은 레벨명(플랫폼 중립)을 유지한다. (→ D-6 §플랫폼 분기 격리)

> **[MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다."** → EXECUTE는 `scripts/`·`opal/core/` 소스만 수정하고, 배포본 검증은 install 재배포로 확인한다. (→ D-6 §배포 경계)

> **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."** → install-mac.sh 헤더 changelog·windows.ps1 `.NOTES 변경이력`·agents.md `## 변경이력` 표에 각각 (032) 행을 추가한다. (→ D-6 §변경이력 작성 의무)

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | install-mac.sh 본문 model 레벨 치환 (어댑터 확장) | F-001 | P0 | 없음 |
| F-002 | cursor `inherit` 엣지 — 본문 오버라이드 토큰 제거 | F-002 | P0 | F-001 (동일 치환 함수 내) |
| F-003 | windows.ps1 미러 (Markdown + Codex TOML body 경로) | F-003 | P0 | F-001 (로직 SSOT) |
| F-004 | 회귀 방지 — 정규식 앵커 + 비대상 에이전트 본문 불변 | F-004 | P0 | F-001, F-003 |
| F-005 | agents.md 문서 동기 + 3개 변경이력 행 | F-005 | P1 | F-001 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 (cursor 분기 — 동일 함수 내)
       ├─ F-003 (windows.ps1 미러 — 로직 SSOT 공유)
       ├─ F-004 (회귀 — F-001·F-003 정규식 앵커 검증)
       └─ F-005 (agents.md 동기 — F-001 동작 서술)
```

> F-002는 F-001과 **물리적으로 같은 치환 함수/분기 내**에서 구현된다(별도 파일 아님). F-003은 F-001 로직을 PowerShell로 미러. F-004는 F-001·F-003의 정규식 앵커 설계를 검증하는 횡단 요구사항.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 본문 치환 정규식 | 정규식이 **prose 자기참조** 라인(`frontmatter의 \`model: standard\`를 따른다` — opal-be-agent:89·opal-db-agent:130)까지 오염 → 의미 왜곡(`model: sonnet`로 변질) | P1 | L1(grep 단위) + L2(실 install 재배포) | S-RED2, S-REG1, S-REG2 |
| H-2 | F-001 mapping 재사용 | frontmatter용 `mapping[platform]` dict를 body에 재사용 시, 레벨명 외 토큰(`opus` 하드코딩·`inherit`)에 매칭 실패 → KeyError 또는 미치환 잔존 | P0 | L1(grep) + L2(재배포 후 0건 grep) | S-GREEN1, S-EDGE-CURSOR |
| H-3 | F-002 cursor inherit | cursor mapping이 전 레벨 `inherit` → body가 `model: inherit`로 치환되면 Agent 도구 model 파라미터로 오인 시 또 enum 위반 (claude만 고치고 cursor 누락 시 동일 버그 재현) | P0 | L1(cursor 산출물 grep) | S-EDGE-CURSOR |
| H-4 | F-003 windows.ps1 미러 | PowerShell `-replace`(정규식) 동작이 Python `re.sub`와 미세하게 달라 양 플랫폼 산출물 비대칭 발생 (028 교훈: install 3개소 stale) | P1 | L1(스크립트 정합 grep) + 정적 검토 | S-MIRROR1 |
| H-5 | F-001/F-003 토큰 형태 | body sub-dispatch 토큰이 2가지 형태(`(skill, model: lvl)` 바레paren / `` `skill` (model: lvl) `` 백틱-paren)로 존재 → 정규식이 한 형태만 커버 시 잔존 | P0 | L1(GREEN grep 0건) | S-GREEN1, S-GREEN2 |
| H-6 | 031/032 소스 충돌 | 진행 중 태스크 031이 `opal-task-action-agent/AGENT.md` 본문을 `model: opus`(claude 실모델명) 하드코딩으로 재작성(uncommitted) → 옵션 A(소스=레벨명) 전제 위반. 어댑터가 `opus`를 레벨명으로 인식 못해 gemini/codex 배포 시 `opus` 잔존(신규 cross-platform 버그) | P0 | (설계 결정 — decision_required) | §9 R-3, decision_required |
| H-7 | F-005 문서-코드 SSOT | agents.md §본문 처리 "변경 없이 복사" 진술이 F-001 후 거짓이 됨 → 후속 워커가 어댑터 동작을 오해 | P2 | L1(문서 grep) | S-DOC1 |

**가설 도출 노트**: H-1은 본 PLAN의 직접 코드 분석에서 발견한 **TASK.md [설계잠금-1]이 놓친 hazard** — be/db 에이전트 본문에 `model: standard` prose 자기참조가 실재하므로(§2 F-001 분석), 단순 `model:\s*(level)\b` 정규식은 이들을 오염시킨다. H-6은 git working tree에서 발견한 031/032 **레이어 충돌**(§9 R-3).

---

## 2. 기능별 분석

### F-001: install-mac.sh 본문 model 레벨 치환 (어댑터 확장)

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스크립트 | `scripts/install-mac.sh:461-602` | `emit_platform_agent_adapter` — frontmatter 변환 + body verbatim 직렬화 | 수정 |
| 에이전트 | `opal/agents/opal-task-action-agent/AGENT.md` | sub-dispatch 본문 토큰 보유 에이전트 (현재 031이 `opus` 하드코딩 중) | 참조 (032 미수정 — §9 R-3) |
| 에이전트 | `opal/agents/opal-sdd-action-agent/AGENT.md:40,44` | sub-dispatch 본문 레벨명 토큰 보유 자매 에이전트 | 참조 (032 미수정) |
| 에이전트 | `opal/agents/opal-be-agent/AGENT.md:89`, `opal-db-agent/AGENT.md:130` | **prose 자기참조** `model: standard` (치환 비대상 — 회귀 보호 대상) | 참조 |
| 설계 | `opal/core/references/opal-model-mapping.md` §2 | 레벨↔플랫폼 매핑 SSOT | 참조 |

#### 2.1.2 현재 구현 (직접 코드 분석)

`emit_platform_agent_adapter`(`scripts/install-mac.sh:461-602`)는 내장 Python heredoc으로 다음을 수행한다:

1. AGENT.md를 `^---\n(.*?)\n---\n?(.*)$` 정규식으로 frontmatter(`fm_raw`)와 body(`body`)로 분리 (`:499-504`).
2. frontmatter 파싱 → `opal_model = fm.get('model', 'standard')` (`:556`).
3. **플랫폼별 모델 매핑 dict** 정의 (`:559-564`):
   ```python
   mapping = {
       'claude': {'light': 'haiku', 'standard': 'sonnet', 'advanced': 'opus'},
       'cursor': {'light': 'inherit', 'standard': 'inherit', 'advanced': 'inherit'},
       'gemini': {'light': 'gemini-3.1-flash-lite', 'standard': 'gemini-flash-latest', 'advanced': 'gemini-pro-latest'},
       'codex': {'light': 'gpt-5.4-mini', 'standard': 'gpt-5.4', 'advanced': 'gpt-5.5'},
   }
   model_value = mapping.get(platform, {}).get(opal_model, 'inherit')
   ```
4. frontmatter 직렬화 (3필드: name/description/model) (`:584-588`).
5. **`f.write(body)`로 body를 무변환 직렬화** (`:601`) ← **변환 경계 비대칭 지점**.

> 핵심: mapping dict(`:559-564`)는 이미 `opal/core/references/opal-model-mapping.md` §2 SSOT와 동기되어 있다 (→ D-5 §2). F-001은 이 동일 dict를 body 치환에 재사용한다 (TASK.md F-001 "동일 mapping dict 재사용").

#### 2.1.3 영향 범위

- **호출자**: `install_claude_agents`(`:605`)·`install_cursor_agents`·`install_gemini_agents`·`install_codex_agents`가 platform별로 `emit_platform_agent_adapter`를 호출.
- **본문 토큰 보유 에이전트** (직접 grep 확인 — `opal/agents/*/AGENT.md` body NR>9):
  - `opal-sdd-action-agent`: `model: advanced`(L40), `model: standard`(L44) — **레벨명, 치환 대상** ✓
  - `opal-be-agent:89`·`opal-db-agent:130`: `frontmatter의 \`model: standard\`를 따른다` — **prose 자기참조, 치환 비대상** ⚠ (H-1)
  - `opal-task-action-agent`: 현재 031이 `model: opus` 하드코딩(uncommitted) — 레벨명 부재 (§9 R-3)
- **토큰 형태 2종** (배포본 `~/.claude_platform_mkt/agents/`에서 확인 — H-5):
  - 바레-paren: `(op-dev-plan, model: advanced)` (앞 `, `, 뒤 `)`)
  - 백틱-skill paren: `` `op-dev-plan` (model: advanced) `` (앞 `(`, 뒤 `)`)

---

### F-002: cursor `inherit` 엣지 — 본문 오버라이드 토큰 제거

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스크립트 | `scripts/install-mac.sh` (F-001 치환 함수 내 cursor 분기) | cursor는 mapping 결과가 `inherit` | 수정 (F-001 내) |

#### 2.2.2 현재 구현

cursor mapping은 전 레벨 `inherit`(`:561`). frontmatter는 `model: inherit`로 출력되어 정상(Cursor가 IDE 모델 설정 위임). 그러나 **body**의 `model: advanced`를 단순 mapping 적용하면 `model: inherit`가 되며, 이는 sub-dispatch 시 Agent 도구 `model` 파라미터로 전달될 경우 enum(`sonnet/opus/haiku/fable`) 위반이다 (H-3). `inherit`는 Cursor 어댑터 frontmatter 전용 값이지 Agent 도구 디스패치 인자가 아니다.

#### 2.2.3 영향 범위

- cursor 어댑터 산출물(`~/.cursor/agents/*.md`) body. claude/gemini/codex는 실모델명으로 치환되어 무관.
- claude만 고치고 cursor를 누락하면 cursor 환경에서 **동일 버그가 재현**된다 (TASK.md F-002 "왜").

---

### F-003: windows.ps1 미러 (Markdown + Codex TOML body 경로)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스크립트 | `scripts/install/windows.ps1:1507-1611` | `Install-PlatformAgents` — install-mac.sh 어댑터 PowerShell 이식 | 수정 |
| 스크립트 | `scripts/install/windows.ps1:1443-1495` | `Get-AgentFrontmatter` — fm/body 분리 헬퍼 (`$fm.Body` 반환) | 참조 |

> TASK.md는 경로를 `scripts/windows.ps1`로 기재했으나 실제 경로는 **`scripts/install/windows.ps1`**이다 (find 확인). PLAN에서 정정.

#### 2.3.2 현재 구현 (직접 코드 분석)

`Install-PlatformAgents`(`:1507`)는 platform별 `ModelMap` 해시테이블을 보유(`:1522-1543`) — install-mac.sh mapping과 동일 4컬럼(claude/cursor/gemini/codex). body는 2개 경로로 직렬화:
- **Markdown(claude/cursor/gemini)**: `:1604` — `... + $header + $fm.Body` (body verbatim).
- **Codex TOML**: `:1574` `$escapedBody = $fm.Body -replace ...` → `:1582` `developer_instructions` 삽입 (body verbatim, escape만).

> 치환 미러 지점 = body가 `$fm.Body`로 직렬화에 투입되기 직전. Markdown 경로(`:1604` 전)와 TOML 경로(`:1574` escape 전) 모두에 적용 가능하도록 **공통 변환 함수**로 추출 권고.

#### 2.3.3 영향 범위

- Windows 사용자 배포본(`~/.claude\agents`, `~/.cursor\agents`, `~/.gemini\agents`, `~/.codex\agents`).
- 028 교훈: install 3개소(install-mac.sh·windows.ps1)가 stale 비동기되면 플랫폼 비대칭 버그 발생 (→ D-5 §2 Codex 정합 기록).

---

### F-004: 회귀 방지 — 정규식 앵커 + 비대상 에이전트 본문 불변

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스크립트 | `scripts/install-mac.sh` (F-001 정규식 패턴) | 치환 앵커 한정 | 수정 (F-001 내) |
| 스크립트 | `scripts/install/windows.ps1` (F-003 정규식 패턴) | 미러 앵커 한정 | 수정 (F-003 내) |

#### 2.4.2 현재 구현

회귀 대상은 3종:
1. **prose 자기참조 오염** (H-1): `opal-be-agent:89`·`opal-db-agent:130`의 `frontmatter의 \`model: standard\`를 따른다`. TASK.md [설계잠금-1] `model:\s*(level)\b`만으로는 이 라인이 오염된다(`model: sonnet`로 변질).
2. **비대상 11개 에이전트 본문 diff** — sub-dispatch 없는 에이전트 본문은 불변이어야 한다.
3. **frontmatter `model:` 변환 불변** — 13개 전체 frontmatter 변환 동작은 F-001 추가로 영향받지 않아야 한다 (body 치환은 frontmatter 직렬화 `:584-588`와 독립).

#### 2.4.3 영향 범위

전체 13개 에이전트 × 4 플랫폼 = 52개 배포본. 본문 변경은 **sub-dispatch 레벨명 토큰을 가진 에이전트로 한정**되어야 한다 (현재 소스 기준: sdd-action-agent + (031 충돌 해소 시) task-action-agent).

---

### F-005: agents.md 문서 동기 + 3개 변경이력 행

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/agents.md:189-192` | §"본문(System Prompt) 처리" — "변경 없이 복사" 진술 | 수정 |
| 문서 | `opal/core/references/agents.md:333-343` | §변경이력 표 | 수정 (행 추가) |
| 스크립트 | `scripts/install-mac.sh:6-` | 헤더 `# 변경이력:` (shell 주석, strip 비대상) | 수정 (행 추가) |
| 스크립트 | `scripts/install/windows.ps1:33-` | `.NOTES 변경이력:` 블록 | 수정 (행 추가) |

#### 2.5.2 현재 구현

`agents.md:189-192` §본문 처리:
```
OPAL `AGENT.md` 본문은 **변경 없이** 어댑터 markdown body로 그대로 복사된다.
어댑터 파일 상단에 `AUTO-GENERATED` 주석 헤더를 삽입하여 직접 편집을 가드한다 ...
```
F-001 후 "변경 없이"는 거짓이 된다(본문 인라인 model 레벨 토큰은 변환됨). `## 변경이력` 표는 v1.7까지 기록(`:343`). install-mac.sh 헤더 `# 변경이력:`는 `##`-markdown 헤딩이 아니므로 `strip_deploy_md`(`:219`, `^## 변경이력$` 매칭)에 strip되지 않는다 → 소스 changelog가 유효한 SSOT.

#### 2.5.3 영향 범위

agents.md는 어댑터 변환 규칙 SSOT(`:457`에서 install-mac.sh가 참조). 문서-코드 불일치 시 후속 워커가 어댑터 동작을 오해(H-7).

---

## 3. 기능별 설계

### F-001: install-mac.sh 본문 model 레벨 치환 (어댑터 확장)

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 스크립트 | `f.write(body)`(`:601`) 직전에 body 인라인 `model: <레벨>` sub-dispatch 토큰을 `mapping[platform]` 실모델명으로 치환하는 로직 추가 | `scripts/install-mac.sh:559-565,601` (→ D-1) |

#### 3.1.2 API·데이터 모델·설계

**[설계잠금-1 확정] 본문 치환 정규식 — sub-dispatch 토큰 한정 앵커**

TASK.md [설계잠금-1]의 `model:\s*(light|standard|advanced)\b`는 prose 자기참조(`model: standard`를 따른다)를 오염시키므로(H-1, §2.4.2), 본 PLAN은 **sub-dispatch 토큰의 구조적 앵커**로 한정한다.

배포본에서 확인된 sub-dispatch 토큰은 항상 **괄호 내부**에서 `, model: <레벨>` 또는 `(model: <레벨>` 형태로 등장하며, 뒤에 `)`가 따른다 (§2.1.2 H-5). 반면 prose 자기참조는 `` `model: standard` `` (백틱 내부) + 뒤에 `를 따른다`가 온다. 이를 구별하는 정규식:

```python
# F-001 본문 치환 — emit_platform_agent_adapter Python heredoc, f.write(body) 직전
# sub-dispatch 토큰: 괄호 내 ", model: <레벨>" 또는 "(model: <레벨>" + 뒤 ")"
# prose 자기참조(`model: standard`를 따른다)는 백틱 내부이며 ")"가 없어 미매칭.
_LEVEL_RE = re.compile(r'(?P<lead>[,(]\s*)model:\s*(?P<lvl>light|standard|advanced)\b')

def _sub_body_model(m):
    lvl = m.group('lvl')
    repl = mapping.get(platform, {}).get(lvl)
    if repl is None:
        return m.group(0)            # 매핑 부재 → 원문 유지 (H-2 방어)
    if repl == 'inherit':
        # F-002 cursor: 오버라이드 토큰 자체 제거 (아래 [설계잠금-2])
        lead = m.group('lead')
        # ", model: lvl" → "" (선행 콤마+공백 제거) / "(model: lvl" → "(" (여는 괄호 보존)
        return '(' if lead.lstrip().startswith('(') else ''
    return f"{m.group('lead')}model: {repl}"

body = _LEVEL_RE.sub(_sub_body_model, body)
```

- 앵커 `[,(]\s*` (선행 콤마 또는 여는 괄호)로 sub-dispatch 토큰만 포착 → prose 자기참조(선행 백틳 `` ` ``) 미매칭 (H-1 방어). [MUST] 단어 경계 `\b`로 레벨명 부분 매칭 차단 (TASK.md F-004).
- 두 토큰 형태 모두 커버 (H-5): `(op-dev-plan, model: advanced)` → lead=`, `, `` `op-dev-plan` (model: advanced) `` → lead=`(`.
- `mapping.get(platform, {}).get(lvl)`가 None이면 원문 유지 (레벨명 오타·미지원 플랫폼 방어, H-2).

> [MUST] 정규식은 frontmatter가 아닌 **`body` 문자열에만** 적용한다 — 어댑터는 이미 `:504`에서 body를 분리 보유하므로 frontmatter 변환(`:556-588`)과 완전 독립이다. (→ D-1:504,556-588)

> 본 정규식은 `opus`·`sonnet`·`haiku`·`inherit` 등 **이미 실모델명/inherit인 토큰을 매칭하지 않는다**(레벨명 3종만 alternation). 따라서 031이 하드코딩한 `model: opus`는 어떤 플랫폼에서도 변환되지 않고 잔존한다 → §9 R-3 / decision_required.

#### 3.1.3 환경 변경
해당 없음 (Bash + 내장 Python3 `re`, 추가 패키지 없음).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-001 AC (RED) | 회귀/RED 증거 | 수정 전 배포본 `opal-sdd-action-agent.md` body에 `model: advanced`·`model: standard` 잔존 (≥1건) |
| TS-002 | F-001 AC (GREEN) | 기능 테스트 | 재배포 후 claude 산출물 body에 `model: opus`/`model: sonnet` 출현 + body `model: advanced/standard/light` **0건** |
| TS-003 | F-001 AC | 기능 테스트 | gemini 산출물 body에 `model: gemini-pro-latest`/`gemini-flash-latest` 출현, 레벨명 0건 |

---

### F-002: cursor `inherit` 엣지 — 본문 오버라이드 토큰 제거

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 스크립트 | F-001 치환 함수 내 `repl == 'inherit'` 분기 — body sub-dispatch 오버라이드 토큰을 **제거**(주석째 삭제)하여 model 오버라이드 없이 디스패치되도록 | `scripts/install-mac.sh:561` (→ D-1) |

#### 3.2.2 설계

**[설계잠금-2 확정] cursor inherit → 본문 오버라이드 토큰 제거**

cursor는 mapping 결과가 `inherit`(`:561`). body에 `model: inherit`를 남기면 Agent 도구 model 파라미터로 오인 시 enum 위반(H-3). 해법은 **오버라이드 토큰 자체를 제거**하여, 액션 에이전트가 model 오버라이드 없이 디스패치 → target 에이전트 frontmatter(cursor에서 `inherit`)를 상속하게 한다 (TASK.md [설계잠금-2] 권고 해법).

제거 형태 (§3.1.2 `_sub_body_model`의 `repl == 'inherit'` 분기):
- `(op-dev-plan, model: advanced)` → `(op-dev-plan)` — 선행 `, ` 포함 토큰 제거.
- `` `op-dev-plan` (model: advanced) `` → `` `op-dev-plan` () `` ... → **여는 괄호 보존 후속 처리 필요**.

> **세부 확정**: 백틱-skill 형태 `(model: advanced)`는 토큰 제거 시 빈 괄호 `()`가 남는다. 빈 괄호는 무해(렌더·파싱 영향 없음)하나 가독성을 위해 EXECUTE에서 `\s*\(\s*\)` 후처리로 빈 괄호를 제거하는 2차 정리를 적용한다. 바레-paren 형태 `(op-dev-plan, model: advanced)`는 `, model: advanced` 제거 → `(op-dev-plan)` (괄호 내용 보존). **판정 기준은 "Agent 도구 model 파라미터로 전달될 수 있는 `model: <레벨>` 또는 `model: inherit` 토큰이 cursor body에 0건"** (TS-004).

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | F-002 AC | 기능 테스트 | 재배포 후 cursor 산출물(`~/.cursor/agents/opal-sdd-action-agent.md`) body에 `model: inherit`·`model: <레벨>` 토큰 0건 (오버라이드 토큰 제거됨) |
| TS-005 | F-002 AC | 기능 테스트 | cursor body에서 sub-dispatch 라인이 skill 식별자(`op-dev-plan` 등)는 유지하되 model 오버라이드만 제거됨 (빈 괄호 잔존 없음) |

---

### F-003: windows.ps1 미러

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install/windows.ps1` | 스크립트 | `Install-PlatformAgents`에 body model 레벨 치환 로직 미러 — Markdown 경로(`:1604` 전)와 Codex TOML 경로(`:1574` escape 전) 모두에 적용. cursor=`inherit` 시 토큰 제거 (F-002 미러) | `scripts/install/windows.ps1:1522-1543,1574,1604` (→ D-2) |

#### 3.3.2 설계

install-mac.sh `_sub_body_model`(§3.1.2)을 PowerShell로 미러. `ModelMap`(`:1522-1543`)은 이미 동기 — body 치환에 재사용한다.

```powershell
# F-003: body sub-dispatch 토큰 치환 헬퍼 — Get-AgentFrontmatter 직후, body 직렬화 전 호출
function Convert-BodyModelTokens {
    param([string]$Body, [hashtable]$ModelMap)
    # 앵커: 괄호 내 ", model: <레벨>" 또는 "(model: <레벨>"
    return [regex]::Replace($Body, '([,(]\s*)model:\s*(light|standard|advanced)\b', {
        param($m)
        $lead = $m.Groups[1].Value
        $lvl  = $m.Groups[2].Value
        $repl = $ModelMap[$lvl]
        if (-not $repl) { return $m.Value }          # 매핑 부재 → 원문 유지
        if ($repl -eq 'inherit') {                    # cursor: 오버라이드 토큰 제거
            if ($lead.TrimStart().StartsWith('(')) { return '(' } else { return '' }
        }
        return "$lead" + "model: $repl"
    })
}
# 빈 괄호 정리(F-002 cursor): '(\s*)' 후처리 — install-mac.sh와 동일 규칙
```

호출 지점:
- Markdown(`:1604`): `$fm.Body` → `Convert-BodyModelTokens $fm.Body $cfg.ModelMap` 결과를 직렬화에 투입.
- Codex TOML(`:1574`): escape 전 동일 변환 적용.

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 — PowerShell `-replace`/`[regex]::Replace`가 Python `re.sub`와 동등한 결과를 내는지 정적 검토 + (가능 시) Windows VM 검증 (H-4, TS-006).

#### 3.3.3 환경 변경
해당 없음 (PowerShell `[regex]` 내장).

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | F-003 AC | 산출물 검사 | windows.ps1에 body 치환 로직 존재 + 정규식 패턴(`[,(]\s*model:\s*(light\|standard\|advanced)\b`)·매핑 4컬럼(claude/cursor/gemini/codex)이 install-mac.sh와 동기 (정적 diff) |
| TS-007 | F-003 AC | 산출물 검사 | windows.ps1 치환이 Markdown 경로(`:1604`)·Codex TOML 경로(`:1574`) 양쪽에 적용됨 (grep으로 호출 지점 2곳 확인) |

---

### F-004: 회귀 방지 — 정규식 앵커 + 비대상 에이전트 본문 불변

#### 3.4.1 파일 변경 계획

**수정** — F-001·F-003 정규식 앵커 설계에 흡수 (별도 파일 변경 없음). 검증 전용 요구사항.

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | (F-001·F-003 정규식) | 스크립트 | `[,(]\s*` 선행 앵커 + `\b` 단어 경계로 prose 자기참조·일반 단어 오염 차단 | `opal/agents/opal-be-agent/AGENT.md:89`, `opal-db-agent/AGENT.md:130` (→ D-3) |

#### 3.4.2 설계

**[설계잠금-4 확정] 회귀 검증 grep 명령** (재배포 전 baseline 캡처 → 재배포 후 비교):

1. **prose 자기참조 불변** (H-1):
   ```bash
   grep -n "frontmatter의 .model: standard.를 따른다" ~/.claude/agents/opal-be-agent.md ~/.claude/agents/opal-db-agent.md
   # 기대: 양 파일 모두 'model: standard' 원문 유지 (sonnet으로 변질 0건)
   ```
2. **비대상 11개 에이전트 본문 diff 0** (H-1·F-004 AC):
   ```bash
   # 재배포 전 baseline 백업 → 재배포 후 diff. sub-dispatch 없는 에이전트 목록:
   # be/convention-checker/db/fe/plan/planning/security-checker/task/task-qa/test/wtm
   for a in opal-be-agent opal-convention-checker opal-db-agent opal-fe-agent opal-plan-agent \
            opal-planning-agent opal-security-checker opal-task-agent opal-task-qa-agent \
            opal-test-agent opal-wtm-agent; do
     diff <(sed -n '/^---$/,$p' BASELINE/$a.md) <(sed -n '/^---$/,$p' ~/.claude/agents/$a.md) && echo "$a: body UNCHANGED"
   done
   ```
3. **13개 frontmatter `model:` 불변** (F-004 AC):
   ```bash
   # 재배포 전후 frontmatter model 값 비교 (line<=9 영역)
   for a in ~/.claude/agents/opal-*.md; do awk 'NR<=9 && /^model:/' "$a"; done
   # 기대: 재배포 전후 동일 (F-001 body 치환이 frontmatter에 영향 없음)
   ```
4. **본문 변경 에이전트 = 레벨명 sub-dispatch 보유 에이전트로 한정** (F-004 AC):
   ```bash
   # 현재 소스 기준 본문 변경 대상: opal-sdd-action-agent (+ 031 충돌 해소 시 opal-task-action-agent)
   # 그 외 0개여야 함.
   ```

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | F-004 AC | 회귀 테스트 | prose 자기참조 라인(be:89·db:130)이 재배포 후 `model: standard` 원문 유지 (오염 0건) |
| TS-009 | F-004 AC | 회귀 테스트 | sub-dispatch 없는 11개 에이전트 배포본 body diff 0 |
| TS-010 | F-004 AC | 회귀 테스트 | 13개 에이전트 frontmatter `model:` 값 재배포 전후 불변 |

---

### F-005: agents.md 문서 동기 + 3개 변경이력 행

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/agents.md:189-192` | 문서 | §본문 처리: "변경 없이 복사" → "복사되되 인라인 `model: <레벨>` sub-dispatch 토큰은 플랫폼 실모델명으로 변환(cursor는 토큰 제거)" 취지로 정정 | `opal/core/references/agents.md:191` (→ D-8) |
| 2 | `opal/core/references/agents.md:333-343` | 문서 | §변경이력 표에 v1.8 (032) 행 추가 | `docs/CONVENTIONS.md §변경이력` (→ D-6) |
| 3 | `scripts/install-mac.sh:6-` | 스크립트 | 헤더 `# 변경이력:`에 (032) 행 추가 | `scripts/install-mac.sh:7` (→ D-1) |
| 4 | `scripts/install/windows.ps1:33-` | 스크립트 | `.NOTES 변경이력:` 블록에 (032) 행 추가 | `scripts/install/windows.ps1:33` (→ D-2) |

#### 3.5.2 설계

`agents.md:191` 정정 문안 (취지):
> OPAL `AGENT.md` 본문은 어댑터 markdown body로 복사된다. 단, 본문에 등장하는 **인라인 `model: <레벨>` sub-dispatch 오버라이드 토큰**(괄호 내 `, model: <레벨>`/`(model: <레벨>` 형태)은 frontmatter와 동일하게 §frontmatter 변환 규칙 표의 플랫폼 실모델명으로 변환된다. Cursor(`inherit`)는 해당 토큰을 제거하여 model 오버라이드 없이 디스패치되도록 한다. prose 자기참조(백틱 내 `` `model: <레벨>` ``)는 변환 대상이 아니다.

> [MUST] §본문 처리에서 "본문은 **변경 없이** 그대로 복사된다"는 **무조건 진술이 남아있지 않아야 한다** (F-005 AC). §frontmatter 변환 규칙(`:169-187`) 인근에 본문 변환을 함께 기재한다 (TASK.md F-005 "어디에").

> 변경이력 일시: `2026-06-21 HH:mm KST` (EXECUTE 시점 KST), 버전 semver, `(032)` 태스크 번호 포함 — `docs/CONVENTIONS.md §변경이력 작성 의무` (→ D-6).

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-005 AC | 산출물 검사 | agents.md §본문 처리에 "인라인 model 레벨 토큰 변환" 취지 기재 + "변경 없이 그대로 복사" 무조건 진술 부재 |
| TS-012 | F-005 AC | 산출물 검사 | agents.md `## 변경이력` 표 + install-mac.sh `# 변경이력:` + windows.ps1 `.NOTES 변경이력:` 3곳에 (032) 행 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0 | (선결) | — | PM 직접 | 게이트 | **decision_required (R-3) 해소** — 031/032 소스 충돌. 미해소 시 F-001 어댑터는 작성하되 task-action-agent 검증은 보류 |
| 1 | F-001, F-002 | 1 | opal-task-agent | 단일 | install-mac.sh 어댑터 body 치환 + cursor 분기 (동일 함수) |
| 1 | F-003 | 2 | opal-task-agent | 순차 (F-001 로직 확정 후) | windows.ps1 미러 |
| 1 | F-005 | 3 | opal-task-agent | 병렬 가능 (Step 1·2와 독립 파일 일부) | agents.md 정정 + 3개 changelog 행 |
| 2 | F-001~F-004 | 4 | opal-task-agent | 순차 (Step 1~3 완료 후) | install 재배포 + GREEN/회귀 grep 검증 |

> 전 Step이 Framework 영역(`scripts/`·`opal/core/`)이며 단일 워커(opal-task-agent) 내 순차 처리가 안전하다 (파일 충돌·로직 SSOT 공유). PM 매핑 테이블상 Framework → **opal-task-agent(범용)** 단일 디스패치 (TASK.md EXECUTE 영역 배정).

### 4.2 실행 체크리스트

> 총 4개 Step | Phase 2개(+선결 게이트) | 실행 모드: **복잡** (외부 동작 변경·다중 파일·RED-first)

#### Step 1: install-mac.sh 어댑터 본문 model 레벨 치환 (F-001 + F-002)
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: 스크립트
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (`emit_platform_agent_adapter`, `:601` `f.write(body)` 직전)
- **작업 내용**: §3.1.2 `_LEVEL_RE` + `_sub_body_model` 추가. 앵커 `[,(]\s*model:\s*(light|standard|advanced)\b`로 sub-dispatch 토큰만 치환. `mapping[platform]` 재사용. `repl == 'inherit'`(cursor) 분기는 오버라이드 토큰 제거 + 빈 괄호 정리(F-002). mapping 부재 시 원문 유지.
- **완료 기준**: 정규식이 prose 자기참조(be:89·db:130) 미매칭 + 두 토큰 형태(바레-paren·백틱-paren) 모두 커버. frontmatter 변환 로직(`:556-588`) 무수정.
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005
- **실행 방법**: sub-agent
- **의존**: 없음 (단, Phase 0 게이트 권고)

#### Step 2: windows.ps1 어댑터 본문 치환 미러 (F-003)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 스크립트
- **agent**: opal-task-agent
- **파일**: `scripts/install/windows.ps1` (`Install-PlatformAgents`, `:1574` TOML escape 전 + `:1604` Markdown 직렬화 전)
- **작업 내용**: §3.3.2 `Convert-BodyModelTokens` 추가. `ModelMap`(`:1522-1543`) 재사용. Markdown·Codex TOML 양 경로에 적용. cursor `inherit` 토큰 제거 미러.
- **완료 기준**: 정규식 패턴·매핑 4컬럼이 install-mac.sh와 동기. body 치환이 양 직렬화 경로에 적용됨.
- **테스트**: TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1 (로직 SSOT 확정 후 미러)

#### Step 3: agents.md 문서 동기 + 3개 변경이력 행 (F-005)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/agents.md:189-192,333-343`, `scripts/install-mac.sh:6-`, `scripts/install/windows.ps1:33-`
- **작업 내용**: §3.5.2 — agents.md §본문 처리 정정(무조건 "변경 없이 복사" 진술 제거 + 인라인 model 토큰 변환 기재) + agents.md `## 변경이력` v1.8 (032) 행 + install-mac.sh `# 변경이력:` (032) 행 + windows.ps1 `.NOTES 변경이력:` (032) 행.
- **완료 기준**: 3곳 변경이력 행 존재 + agents.md §본문 처리에서 "변경 없이 그대로 복사" 무조건 진술 부재.
- **테스트**: TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1 (어댑터 동작 확정 후 서술)

#### Step 4: install 재배포 + GREEN/회귀 grep 검증 (F-001~F-004)
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003, F-004
- **영역**: 스크립트 (검증)
- **agent**: opal-task-agent
- **파일**: (배포본 검증 — 소스 미수정) `~/.claude/agents/*`, `~/.cursor/agents/*`, `~/.gemini/agents/*`
- **작업 내용**: ① 재배포 전 배포본 baseline 백업 (RED 증거 캡처 — TS-001) → ② `bash scripts/install-mac.sh`(또는 어댑터 재실행 경로) → ③ §3.4.2 grep 4종 + GREEN grep(TS-002·003·004) 실행 → ④ 비대상 11개 본문 diff 0·frontmatter 불변 확인.
- **완료 기준**: RED(TS-001) → GREEN(TS-002~005) 전환 입증 + 회귀(TS-008~010) 0건.
- **테스트**: TS-001(RED), TS-002, TS-003, TS-004, TS-005, TS-008, TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | F-003은 F-001 로직(`_sub_body_model`)을 미러하므로 로직 확정 후 진행 |
| Step 1 → Step 3 | F-005 §본문 처리 서술은 F-001 확정 동작(앵커·cursor 제거)을 정확히 기술해야 함 |
| Step 3 ∥ Step 2 | agents.md/changelog는 windows.ps1과 독립 파일이나, 둘 다 Step 1 후행이므로 동일 워커 순차로 처리(파일 충돌 회피) |
| Step 1~3 → Step 4 | 재배포 검증은 모든 소스 수정 완료 후 1회 수행 (RED→GREEN 입증) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 본문 sub-dispatch 레벨 토큰이 실모델명으로 치환되는가 | TS-002, TS-003 | 재배포 후 claude=opus/sonnet·gemini=실모델명 출현 + 레벨명 0건 |
| F-002 | cursor body에 model 오버라이드 토큰이 제거되는가 | TS-004, TS-005 | cursor body에 `model: inherit`/`model: <레벨>` 0건 + 빈 괄호 잔존 0건 |
| F-003 | windows.ps1이 install-mac.sh와 동기 미러되는가 | TS-006, TS-007 | 정규식·매핑 4컬럼 동기 + Markdown·TOML 양 경로 적용 |
| F-004 | 비대상 에이전트 본문·frontmatter가 불변인가 | TS-008, TS-009, TS-010 | prose 자기참조 불변 + 11개 본문 diff 0 + 13개 frontmatter 불변 |
| F-005 | agents.md/changelog 3곳이 동기되는가 | TS-011, TS-012 | §본문 처리 정정 + 3곳 (032) 행 |

### 5.2 회귀 테스트
- [ ] prose 자기참조(be:89·db:130) `model: standard` 원문 유지 (TS-008)
- [ ] sub-dispatch 없는 11개 에이전트 배포본 body diff 0 (TS-009)
- [ ] 13개 에이전트 frontmatter `model:` 값 재배포 전후 불변 (TS-010)
- [ ] 기존 frontmatter 변환(claude advanced→opus 등) 동작 비파괴

### 5.3 코드/문서 품질
- [ ] install-mac.sh·windows.ps1·agents.md 3곳 변경이력 행 추가 (KST 일시·semver·(032))
- [ ] 플랫폼 분기는 어댑터에만 — 에이전트 AGENT.md 본문은 레벨명(중립) 유지
- [ ] 정규식 앵커 `[,(]\s*` + `\b`로 오염 방지 (주석으로 의도 명시)

### 5.4 보안
- [ ] 하드코딩 시크릿/토큰 없음 (정규식·매핑 dict만 추가)
- [ ] 배포본 직접 편집 금지 — 소스만 수정 후 install 재배포 (CONVENTIONS §배포 경계)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 4개 | 단순 |
| 변경 파일 수 | 3개 (install-mac.sh, windows.ps1, agents.md) | 단순 |
| 모듈 범위 | 다중 (Bash/Python + PowerShell + 문서, 어댑터 2 미러) | 복잡 |
| 작업 유형 | 어댑터 동작 변경 (배포 변환 메커니즘) + self-confirming 위험 영역 | 복잡 |
| 외부 의존성 | 없음 (내장 정규식) | 단순 |
| **실행 모드** | **복잡** | RED-first + 양 플랫폼 어댑터 미러 + 회귀 횡단 검증으로 복잡 모드 적용 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
[Phase 0 게이트] decision_required(R-3) — PM/사용자
        │
        ▼
[Batch 1] opal-task-agent (순차 단일 워커)
        Step 1 (install-mac.sh F-001+F-002)
          → Step 2 (windows.ps1 F-003 미러)
          → Step 3 (agents.md + 3 changelog F-005)
        │
        ▼
[Batch 2] opal-task-agent
        Step 4 (재배포 + RED→GREEN + 회귀 grep — F-001~F-004)
```

**그룹핑 근거**: 전 Step이 동일 영역(Framework 스크립트·문서)이며 install-mac.sh↔windows.ps1 로직 SSOT 공유·agents.md가 어댑터 동작 서술 → 파일 충돌·정합성 위해 단일 워커 순차. 병렬 분리 이득 없음(파일 의존).

### C-2. 스킬 요구사항

- 기존 스킬 매칭: `op-dev-execute`(EXECUTE), `op-dev-test-scenario`(별도 PM 작성 — TEST-SCENARIO.md). 신규 스킬 불요.
- 갭 판별: 정규식 치환은 1개 함수(install-mac.sh) + 1개 미러(windows.ps1) = 인라인 지침으로 충분 (스킬 후보 아님).

### C-3. 도구 요구사항

- CLI: `bash`, `grep`, `diff`, `awk` (검증). `python3`(install 내장). PowerShell(windows.ps1 — macOS에서 정적 검토만, 실행 검증은 Windows VM 후속).
- MCP/패키지: 없음.

### C-4. 테스트 전략

- 기능 테스트: TS-002~007 (재배포 후 배포본 grep — claude/cursor/gemini 산출물).
- 회귀 테스트: TS-008~010 (baseline diff + frontmatter 불변).
- RED 증거: TS-001 (수정 전 배포본 레벨명 잔존).
- 산출물 검사: TS-006·007·011·012 (정적 grep/diff).
- 실행 명령: `bash scripts/install-mac.sh` → §3.4.2 grep 4종 + GREEN grep. (TEST-SCENARIO.md에서 PM이 상세 명령 확정 — STEP 3.5.)

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 어댑터 (macOS) | Bash + 내장 Python3 `re` | (인라인 지침) |
| 어댑터 (Windows) | PowerShell `[regex]::Replace` | (인라인 지침) |
| 문서 | Markdown | op-dev-execute |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 API 불요 — 내장 정규식만 사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 어댑터 frontmatter 변환·body 직렬화 현 동작 (461-602), mapping dict(559-565), 헤더 changelog(6-) |
| D-2 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | 어댑터 미러 함수 `Install-PlatformAgents`(1507-1611), ModelMap(1522-1543), body 직렬화(1574 TOML·1604 MD), `.NOTES 변경이력`(33-) |
| D-3 | 소스 | 본문 토큰 보유 에이전트 | `opal/agents/opal-sdd-action-agent/AGENT.md`, `opal-be-agent/AGENT.md:89`, `opal-db-agent/AGENT.md:130` | sub-dispatch 레벨명 토큰(치환 대상) + prose 자기참조(치환 비대상, 회귀 보호) |
| D-4 | 소스 | opal-task-action-agent | `opal/agents/opal-task-action-agent/AGENT.md` | 031 uncommitted 변경으로 본문 `model: opus` 하드코딩 — 옵션 A 전제 충돌 (R-3) |
| D-5 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 레벨↔플랫폼 매핑 SSOT v1.5 (§2 매핑 테이블 — 어댑터 dict 동기 근거) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·플랫폼 분기 격리·변경이력 작성 의무 ([MUST] 인용 — §1.1) |
| D-7 | 설계 | agents.md | `opal/core/references/agents.md` | §본문 처리(189-192) "변경 없이 복사" 진술(F-005 정정 대상) + frontmatter 변환 규칙 표(169-187) + 변경이력(333-343) |
| D-8 | 설계 | opal-harness.md | `opal/core/references/harness/citation-rules.md` | 인용 규칙 + decision_required 계약(§7.4·7.5) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 정규식이 prose 자기참조(be:89·db:130) 오염 → `model: standard`가 `model: sonnet`로 변질 | F-001, F-004 | P1 | `[,(]\s*` 선행 앵커로 sub-dispatch 토큰만 포착 (백틱 자기참조 미매칭). TS-008로 검증. |
| R-2 | 두 토큰 형태(바레-paren·백틱-paren) 중 한쪽만 커버 → 레벨명 잔존 | F-001, F-003 | P0 | lead 그룹 `[,(]`가 양 형태 포착. TS-002·005로 0건 검증. |
| R-3 | **031/032 소스 레이어 충돌** — 진행 중 031이 `opal-task-action-agent/AGENT.md` 본문을 `model: opus`(claude 실모델명) 하드코딩으로 재작성(uncommitted). 옵션 A(소스=플랫폼 중립 레벨명)의 전제를 위반. 어댑터는 `opus`를 레벨명으로 인식 못해 gemini/codex 배포 시 `model: opus`가 잔존(신규 cross-platform 버그) | F-001, (031 경계) | P0 | **decision_required 에스컬레이션** (아래). 032 어댑터는 그대로 작성(레벨명만 변환). task-action-agent 소스를 레벨명으로 되돌릴지는 031 소유자/사용자 결정. TASK.md §제약 "031 미간섭"과 충돌하므로 자율 결정 금지. |
| R-4 | windows.ps1 PowerShell 정규식이 Python `re.sub`와 미세 차이 → 양 플랫폼 비대칭 (028 stale 교훈) | F-003 | P1 | 정규식 패턴 문자 단위 동기 + 정적 diff(TS-006). 실행 검증은 Windows VM 후속(TS-006 노트). |
| R-5 | agents.md "변경 없이 복사" 잔존 → 후속 워커 어댑터 동작 오해 | F-005 | P2 | F-005에서 무조건 진술 제거 + 인라인 변환 기재. TS-011 검증. |

### decision_required (R-3 — 031/032 레이어 충돌)

> **[PM 검증 — 2026-06-21 RESOLVED / 오경보]**: PM이 직접 검증한 결과 R-3의 전제("031이 task-action-agent 본문을 `model: opus` 하드코딩")는 **사실이 아니다**. `grep -c opus opal/agents/opal-task-action-agent/AGENT.md` = **0건**, `git diff HEAD`에 `model:` 변경 라인 없음 — 031은 이 파일을 수정(미커밋, B7 재설계)했으나 **본문 dispatch 토큰은 레벨명(advanced/light/standard)을 그대로 유지**한다(37·46·50·70·90·98줄). 워커가 frontmatter의 `opus`(정상 변환값)를 본문으로 오독한 것으로 판단. → **충돌 없음. task-action-agent는 sdd-action-agent와 동일한 정상 치환·검증 대상**이다. Phase 0 게이트 및 "task-action-agent 검증 보류" 서술은 무효화하며, Step 4 회귀/GREEN 검증은 두 액션 에이전트 모두를 포함한다. 032는 어댑터(install·windows·agents.md)만 수정하므로 031 소스와 파일 충돌 없음(forward-compatible).

```json
{
  "decision_required": [
    {
      "type": "task_layer_conflict",
      "summary": "031(uncommitted)이 opal-task-action-agent/AGENT.md 본문을 model: opus 하드코딩으로 재작성 → 032 옵션 A(소스=플랫폼 중립 레벨명) 전제 위반. 어댑터는 opus를 변환 안 해 gemini/codex에 opus 잔존(신규 버그).",
      "tokens": ["model: opus", "model: advanced", "model: standard", "model: light"],
      "areas": ["에이전트", "스크립트"],
      "source_refs": [
        "opal/agents/opal-task-action-agent/AGENT.md:35-39,45-58,78-106 (031 uncommitted: opus 하드코딩)",
        "opal/agents/opal-sdd-action-agent/AGENT.md:40,44 (레벨명 유지 — 정상)",
        "docs/CONVENTIONS.md §플랫폼 분기 격리"
      ],
      "options": [
        "A) task-action-agent 소스 본문의 model: opus → 레벨명(advanced 등)으로 되돌려 옵션 A 정합 회복. 단 TASK.md §제약 '031 미간섭' 위반 — 031 소유자 합의 필요.",
        "B) 032는 어댑터(install·windows·agents.md)만 수정하고 task-action-agent 소스는 031 완료 후 별도 정합. 032 검증은 sdd-action-agent로만 RED→GREEN 입증, task-action-agent는 보류.",
        "C) 031과 032를 병합 처리 — 어댑터 + 양 액션 에이전트 소스 레벨명 복원을 한 작업으로."
      ],
      "suggested_resolution": "B 권고 — 032 어댑터 메커니즘은 031과 forward-compatible(레벨명 몇 줄이든 무관). task-action-agent 소스의 opus 하드코딩 복원은 031 소유자/사용자가 결정. 032는 sdd-action-agent로 RED→GREEN 입증 가능."
    }
  ]
}
```

> [MUST] `opal/core/references/harness/citation-rules.md` §7.5: "결정성 이슈는 agentic 모드에서도 사용자 에스컬레이션 필수이며, PM이 자율 결정하지 않는다." → R-3은 임의 결정하지 않고 PM/사용자에게 에스컬레이션한다. (→ D-8 §7.5)

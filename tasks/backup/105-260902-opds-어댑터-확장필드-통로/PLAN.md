# PLAN: 플랫폼 sub-agent 어댑터 확장 필드 통로 신설 + effort 첫 적용

> 작성일: 2026-09-02 | 입력: TASK.md (ANALYSIS.md 없음 — Short Task, 코드 분석을 본 PLAN에서 직접 수행)
> 모드: Multi-Feature (F-001~F-005)

## 결론

- **통로의 형태**: 플랫폼 분기를 `{OPAL 필드 → 플랫폼별 (배치 모드, 대상 키명, 값 맵)}` **단일 JSON 스펙 상수**에 가두고, emit은 그 스펙을 순회하며 **배치 모드 3종(`key` / `model_param` / `omit`)에만 분기**한다 — 플랫폼명 조건문은 신규로 등장하지 않는다 (TASK.md R-1 AC).
- **미러 규약의 강화**: 스펙을 **JSON 리터럴 텍스트**로 표현하여 Bash(내장 Python `json.loads`)와 PowerShell(`ConvertFrom-Json`)이 **동일한 바이트열**을 소비하게 한다 — 기존 "문자 단위 동일 정규식"이라는 사람 규약을 **기계 검증 가능한 텍스트 동일성**으로 승격한다 (H-4).
- **기존 동작 보존의 구조적 보장 3중**: ① 스펙의 `order` 필드가 기존 emit 순서(name→description→model)를 고정하고 신규 필드는 그 뒤에만 온다 ② `effort`는 `default` 없음 → 미선언 시 순회에서 pair가 생성되지 않아 출력 델타 0 ③ **차등 골든 테스트**(`git show HEAD:` 구판 emitter vs 신판 emitter × 실제 에이전트 15종 × 4플랫폼 → `diff` 공집합)로 바이트 동일성을 자동 검증한다 (F-005).
- **`name`/`description`/`model` 흡수**: R-1 AC가 흡수를 명시 요구하며, 위 3중 보장으로 회귀 위험이 자동 검증 범위로 들어오므로 흡수한다 (§3.1.2 D-결정 1).
- **값 도메인**: 공통 4값 항등 + Claude `max` 항등 + Codex `max→xhigh` 축약. 미정의 값은 **stderr 경고 후 해당 필드만 생략**하고 install은 계속한다. 단 `model` 필드만 기존 `fallback`(`inherit`/`gpt-5.5`) 동작을 스펙 키로 보존한다 (H-3).
- **R-6은 교체 + 마이그레이션 2건**: `install_codex_config`가 `[agents]` 헤더 존재 시 통째 스킵하므로, 기존 설치 머신은 스크립트만 고쳐서는 legacy 키가 영구 잔존한다 — **기존 블록 내 `max_threads` 키 in-place 치환 경로**를 함께 넣어야 R-6 AC (b)가 성립한다 (H-6, 신규 발견).
- **비대상 발견 2건을 PM에 보고**: (a) mac Codex 경로는 본문 model 토큰 변환(`_sub_body_model`)을 적용하지 않는데 windows Codex 경로는 적용한다 — 이미 존재하는 미러 위반 (b) mac/windows md 산출물은 AUTO-GENERATED 헤더 문구가 서로 다르다. 두 사실 때문에 R-4 AC의 "산출물 동일" 판정 범위를 **frontmatter 블록**으로 한정해야 한다 (§9 R-3, R-4).
- 분량 초과 사유: 어댑터 2언어 × 4플랫폼 × 2출력포맷의 조합 계약을 명세해야 하고, 바이트 동일성 보장 설계를 별도로 기술해야 한다.

---

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| `[결정]` 어댑터에 확장 필드 변환 테이블을 신설한다 (필드명·값·배치 3중 변환을 한 자료구조가 소유) | 유효 | - |
| `[사실]` 단순 pass-through로는 성립하지 않는다 (Cursor는 model 값 합성, 값 도메인 상이) | 유효 | E1 확인 — `scripts/install-mac.sh:584-589`는 3필드 고정 append, Cursor 매핑은 `scripts/install-mac.sh:561`에서 전 레벨 `inherit`로 고정되어 대괄호 파라미터 삽입 지점이 없음 |
| `[결정]` effort 실적용 대상은 Claude Code·Codex 2종 | 유효 | - |
| `[결정]` Gemini는 키를 생략한다 | 유효 | - |
| `[결정]` Cursor는 테이블에 자리만 예약(미적용) | 유효 | - |
| `[결정]` 플랫폼 분기는 전부 어댑터 계층 테이블 안에 가둔다 | 유효 | - |
| `[결정]` Codex `max_threads` legacy alias 정리를 본 태스크에 포함 | 수정필요 | 범위 보강 필요 — `scripts/install-mac.sh:823-826`이 `[agents]` 헤더 존재 시 `return`하므로 **스크립트 리터럴 교체만으로는 기존 설치 머신의 config.toml이 갱신되지 않는다**. R-6 AC (b)("재배포 후 `~/.codex/config.toml`에 `max_concurrent_threads_per_session = 6`이 존재")를 충족하려면 기존 블록 in-place 치환 경로가 추가로 필요하다 (F-004) |
| `[결정]` 에이전트별 effort 값 배정은 이월 | 유효 | - |

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

플랫폼 sub-agent 어댑터가 frontmatter를 `name`/`description`/`model` 3필드로 하드코딩 재조립하는 구조를, OPAL 필드 → 플랫폼 필드의 **선언적 변환 스펙(JSON)** 을 순회하는 통로로 바꾼다. 그 위에 `effort`를 첫 실적용 필드로 Claude(독립 키 `effort`)·Codex(이름 다른 독립 키 `model_reasoning_effort`)에 태우고, Gemini는 생략·Cursor는 예약한다. 부수로 Codex `[agents] max_threads` legacy alias를 정식 키로 교체한다. **최상위 제약은 effort 미선언 에이전트 산출물의 바이트 동일성**이며, 이를 차등 골든 테스트로 자동 보증한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | mac 어댑터 확장 필드 변환 스펙 + 모드 기반 emit | R-1, R-2, R-3 | P0 | F-005(테스트 자산 선행 권장) |
| F-002 | windows.ps1 미러 반영 | R-4 | P0 | F-001 |
| F-003 | 변환 SSOT 표 갱신 (`agents.md`) | R-5 | P0 | F-001 |
| F-004 | Codex `max_threads` legacy alias 교체 + 기존 config 마이그레이션 | R-6 | P1 | 없음 |
| F-005 | 회귀 검증 자산 (차등 골든 + 스펙 미러 diff + effort 케이스) | R-1~R-4 AC 검증 수단 · 완료기준 (a)~(c) | P0 | 없음 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-005 (검증 자산 · 베이스라인) ──┬─→ F-001 (mac 통로) ──┬─→ F-002 (windows 미러)
                                 │                      └─→ F-003 (SSOT 표)
F-004 (codex legacy alias) ──────┘  (독립 — 병렬 가능)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 — 3필드 하드코딩 emit → 스펙 순회 흡수 (`scripts/install-mac.sh:584-589`) | **배포 산출물 바이트 계약** — 필드 순서·`description` 공백 시 생략·`yaml_escape` 적용 지점이 어긋나면 15개 에이전트 × 4플랫폼 전량이 재작성되고, 사용자 파일 충돌 가드(`:569-574`)를 통과한 파일이 무의미하게 갱신된다 | P0 | L1(차등 골든, 필수) + L3(실 install 재배포) | S-1 구판·신판 emitter 산출물 diff 공집합 / S-2 재배포 후 `~/.claude|.cursor|.gemini/agents/*.md` `git diff` 무변화 대조 |
| H-2 | F-001 — Codex TOML 경로 스펙 흡수 (`scripts/install-mac.sh:795-802`) | **TOML 직렬화 계약** — `toml_escape` 미적용 또는 값 따옴표 누락 시 `codex doctor`가 malformed로 거부하여 Codex 에이전트 15종이 전량 미로드된다 | P0 | L1(단위) + L3(`codex doctor --json` 실측) | S-3 effort 선언/미선언 각 1건 emit 후 `codex doctor` 0 warn·0 fail |
| H-3 | F-001 R-3 — 미정의 effort 값 처리 | **install 완주 계약** — 오타 값에서 예외를 던지면 install 전체가 중단되어 배포 불능. 반대로 값 검증 없이 통과시키면 Codex가 unknown value로 파일을 거부한다 | P0 | L1(단위 — 경고 문자열 + 필드 생략 + exit 0) | S-4 `effort: hihg` 입력 → stderr 경고 1행 + 산출물에 effort 키 부재 + 나머지 필드 정상 |
| H-4 | F-002 — PowerShell 미러 | **미러 규약** (`scripts/install/windows.ps1:93`) — 두 언어의 스펙 표현이 갈리면 플랫폼별로 다른 산출물이 나오고, 검증은 Windows 머신에서만 가능해 로컬(mac)에서 회귀를 못 잡는다. 본 환경에 `pwsh` 미설치(실측)로 런타임 검증 불가 | P1 | L1(스펙 JSON 리터럴 텍스트 diff — 언어 독립) + Windows 머신 수동 L3 | S-5 두 스크립트에서 스펙 JSON 블록 추출 후 바이트 diff 공집합 / S-6 Windows 실행 후 frontmatter 블록 대조 |
| H-5 | F-002 — PowerShell 값 처리 세부 | **타입 계약** — `ConvertFrom-Json`은 `PSCustomObject`를 반환하므로 hashtable 인덱싱(`$map[$key]`)이 실패한다. `Get-AgentFrontmatter`(`:1601-1657`)는 `name/description/model` 3키만 `switch`로 추출하므로 `effort`가 파싱 단계에서 소실된다 | P1 | L1(정적 리뷰 + Windows 실행) | S-6에 포함 — `effort` 선언 에이전트가 Windows에서 키를 잃지 않는지 |
| H-6 | F-004 — `max_threads` 교체 | **멱등 스킵 계약** (`scripts/install-mac.sh:823-826` / `windows.ps1:1826-1829`) — `[agents]` 헤더 존재 시 통째 스킵하므로 **기존 설치 머신에서 legacy 키가 영구 잔존**한다. R-6 AC (b)가 이 경로에서 실패한다 | P1 | L1(단위 — 3케이스: 파일 없음 / `[agents]` 없음 / legacy 키 포함) + L3(실 config.toml) | S-7 legacy 키를 가진 config.toml 픽스처 → 재실행 후 `max_threads` 0건 & 정식 키 1건 & 다른 블록(`[mcp_servers]`) 무손상 |
| H-7 | F-003 — SSOT 표 갱신 | **문서-코드 축자 일치 계약** (R-5 AC) — 표의 4플랫폼 셀 값이 스펙 JSON과 어긋나면 다음 필드 추가자가 표를 믿고 잘못 구현한다 | P2 | L1(문서 검사 — 표 셀 ↔ 스펙 JSON 대조) | S-8 표의 `effort` 행 4셀과 스펙 JSON의 `to`/`values` 축자 대조 |
| H-8 | F-001/F-002 — 본문 토큰 변환 경로 (`_sub_body_model` `:596-620`) | **경계 계약** — frontmatter 스펙 순회를 도입하면서 `mapping` dict를 스펙 파생값으로 바꾸면, 본문 치환의 입력이 바뀌어 body 변환 결과가 달라질 수 있다. 정규식은 `body` 문자열에만 적용됨(`:604` 주석)이 전제 | P0 | L1(차등 골든에 body 포함 — 파일 전체 diff) | S-1에 포함 (파일 전체 비교이므로 body 회귀도 함께 잡힘) |
| H-9 | 전체 — 실 install 재배포 | **사용자 파일 충돌 가드** — 재배포 검증 중 `~/.claude/agents/` 등에 사용자 관리 파일이 있으면 스킵되어 "변화 없음"이 오탐(false pass)이 된다 | P2 | L3(재배포 전 대상 디렉토리 15/15 AUTO-GENERATED 헤더 보유 확인) | S-9 재배포 전 헤더 카운트 사전 확인 |

**참고 — 이번 변경으로 새로 발생하지 않으나 검증 판정에 영향을 주는 기존 결함 2건** (§9 R-3·R-4에 기재).

---

## 2. 기능별 분석

### F-001: mac 어댑터 확장 필드 변환 스펙 + 모드 기반 emit

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `scripts/install-mac.sh` | `emit_platform_agent_adapter()` — Claude/Cursor/Gemini md 어댑터 emit (`:462-643`) | 수정 |
| 공통 | `scripts/install-mac.sh` | `install_codex_agents()` — Codex TOML 어댑터 emit (`:700-810`) | 수정 |
| 문서 | `opal/core/references/agents.md` | 변환 SSOT 표 (`:186-194`) — F-003이 담당 | 수정 |

#### 2.1.2 현재 구현

- **md 경로** — `emit_platform_agent_adapter(src_dir, dst_file, platform)`이 venv/시스템 Python을 골라(`:471-476`) heredoc Python을 실행한다. frontmatter는 PyYAML 우선·정규식 폴백(`:489-542`)으로 파싱하며, **폴백 파서는 모든 `key: value` 라인을 `fm` dict에 담는다**(`:513-542`) — 즉 `effort`는 파싱 단계에서는 이미 살아 있고, 버려지는 지점은 직렬화다.
- 플랫폼 model 매핑은 함수 내부 인라인 dict `mapping`(`:559-566`)이며, **frontmatter 변환과 본문 토큰 치환(`_sub_body_model` `:607-618`)이 이 dict를 공유**한다(`:602` 주석 "mapping[platform]는 frontmatter 변환과 동일 dict 재사용").
- 직렬화는 `out_lines`에 3줄을 무조건 append하는 고정 코드(`:584-589`)이며, 주석이 "출력 frontmatter 직렬화 (3필드만)"(`:576`)로 의도를 명시한다. `yaml_escape`(`:577-583`)가 값 인용을 담당한다.
- **Codex 경로** — `install_codex_agents()`가 **별도의 heredoc Python**을 갖는다. 자체 `codex_model_map`(`:734-739`), 자체 폴백 파서(`:768-773`, md 경로보다 단순 — 블록 스타일 미지원), 자체 `toml_escape`(`:788-790`), 그리고 `name`/`description`/`model`/`developer_instructions` 4줄 고정 write(`:795-802`).
- 즉 **mac에는 어댑터 emit이 물리적으로 2벌 존재**한다(windows는 `Install-PlatformAgents` 1벌 + `Format` 분기). 스펙을 도입하면 mac의 2벌이 같은 스펙을 봐야 한다.

#### 2.1.3 영향 범위

- 호출자: `install_claude_agents()`(`:645-666`), `install_cursor_agents()`(`:668-689`), `install_gemini_agents()`(`:691~`) → 각 15회 호출. `install_codex_agents()`는 자체 루프.
- 피영향 산출물: `~/.claude/agents/*.md`, `~/.cursor/agents/*.md`, `~/.gemini/agents/*.md`(각 15개), `~/.codex/agents/*.toml`(15개) = **60 파일**.
- 공유 상태: `mapping` dict가 frontmatter·본문 양쪽에 쓰이므로(H-8) 스펙 도입 시 본문 경로에 넘기는 값이 **기존 `{light,standard,advanced}→실모델명` 3키 dict와 동형**임을 유지해야 한다.
- 기존 테스트: `scripts/tests/`에 어댑터 emit을 다루는 자산 **없음**(실측 — `test_archive_contents.sh` / `test_console_scan.sh` / `test_download_contract.sh` / `test_version_stamp.sh` / `test_merge_hooks.py` 5종). → F-005에서 신설한다.
- 테스트 seam 제약: `scripts/install-mac.sh:2098`이 가드 없는 `main "$@"` → **source 불가**. 함수 구간 추출(`sed` 범위) 방식으로 seam을 만든다(§3.5.2).

### F-002: windows.ps1 미러 반영

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `scripts/install/windows.ps1` | `Get-AgentFrontmatter`(`:1601-1657`) — 3키 한정 파서 | 수정 |
| 공통 | `scripts/install/windows.ps1` | `Install-PlatformAgents`(`:1699-1815`) — 4플랫폼 통합 emit(md/toml `Format` 분기) | 수정 |
| 공통 | `scripts/install/windows.ps1` | `Format-YamlValue`(`:1655-1663`) — YAML 값 인용 | 참조(무변경) |

#### 2.2.2 현재 구현

- `Get-AgentFrontmatter`가 `switch ($key)`로 **`name`/`description`/`model` 3키만** 수집하고 나머지를 버린다(`:1645-1649`) — mac 폴백 파서와 달리 **확장 필드가 파서 단계에서 소실**된다. 반환은 `@{Name;Description;Model;Body}` 4키 hashtable(`:1656`).
- `Install-PlatformAgents`는 `$platforms` hashtable에 4플랫폼의 `Dst`/`ModelMap`/`Format`을 선언하고(`:1714-1735`), 루프에서 `$cfg.ModelMap[$fm.Model]` 조회 후 미스 시 `Format`에 따라 `gpt-5.5`/`inherit` 폴백(`:1747-1748`).
- md 직렬화는 `$fmLines` 3줄 고정(`:1791-1796`), TOML 직렬화는 4줄 고정(`:1768-1777`).
- `Convert-BodyModelTokens`(`:1665-1697`)가 md·TOML 양 경로에 적용된다(`:1753`).

#### 2.2.3 영향 범위

- mac과 동일한 60 파일. 단 Windows 머신에서만 실행되며 **본 환경에 `pwsh` 미설치(실측)** → 런타임 검증은 언어 독립 정적 대조(스펙 JSON diff)로 대체하고 실행 검증은 Windows 머신 수동으로 남긴다(H-4).
- `$fm.Model`은 `Get-AgentFrontmatter` 반환 키 → 확장 필드 도입 시 반환 계약이 4키 → 5키(`Fields` 맵 추가)로 바뀐다. `Get-AgentFrontmatter`의 다른 호출처 존재 여부 확인 필요(현 시점 `Install-PlatformAgents` 1곳).

### F-003: 변환 SSOT 표 갱신

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/agents.md` | §frontmatter 변환 규칙 표 (`:186-194`) + 변경이력 표 (`:346~`) | 수정 |

#### 2.3.2 현재 구현

- 표는 행=OPAL 필드, 열=4플랫폼 구조이며 `model`은 레벨별로 3행으로 펼쳐져 있다(`:190-192`). 마지막 두 행이 `icon`(제거) / `(기타 OPAL 전용 필드)`(제거)(`:193-194`) — **"기타=제거"가 현행 설계의 명문**이다.
- 표 아래에 Codex 모델값 SSOT 포인터, Cursor `inherit` 위임 설명, Cursor alias 도입 시 동시 갱신 의무가 주석으로 붙어 있다(`:196-200`).
- 변경이력 표는 최신 v2.0(2026-07-10)까지 기재 → 다음은 **v2.1**.

#### 2.3.3 영향 범위

- 이 표가 어댑터 구현의 SSOT이므로 스펙 JSON과 축자 일치해야 한다(H-7). §본문 처리 절(`:204-205`)은 이번 변경 대상 아님(본문 경로 불변).

### F-004: Codex `max_threads` legacy alias 교체 + 기존 config 마이그레이션

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `scripts/install-mac.sh` | `install_codex_config()` (`:812-841`) | 수정 |
| 환경 | `scripts/install/windows.ps1` | `Install-CodexConfig` (`:1817-1857`) | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | `:250` — `max_threads` 명시 서술 | 수정 |

#### 2.4.2 현재 구현

- mac: `[agents]` 헤더를 `grep -q '^\[agents\]'`로 검사해 있으면 `info` 후 `return`(`:823-826`). 없으면 주석 2줄 + `[agents]` + 3키를 파일 끝에 append(`:830-838`).
- windows: 동일 로직의 PowerShell 등가(`:1827-1852`), 정규식 `(?m)^\[agents\]`.
- 두 곳 모두 함수 주석에 `max_threads=6`이 문서화되어 있다(`:815-816` / `:1821-1823`) → 주석도 함께 교체 대상.
- `docs/ARCHITECTURE.md:250`이 `max_threads`를 명시 → 문서 갱신 대상(docs Step).

#### 2.4.3 영향 범위

- 신규 머신: append 경로만 타므로 리터럴 교체로 충분.
- 기존 머신(본 개발 환경 포함): 스킵 경로 → **영구 잔존**(H-6). AC (b) 충족을 위해 in-place 치환 경로 필요.
- 훼손 금지 대상: 같은 파일의 `[mcp_servers]` 등 타 블록(`:819` 주석이 명시한 계약).

### F-005: 회귀 검증 자산

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/tests/test_agent_adapter_fields.sh` | 어댑터 확장 필드 통로 회귀 테스트 (차등 골든 + 모드별 단위 + 스펙 미러 diff + codex config 마이그레이션) | 신규 |

#### 2.5.2 현재 구현

- `scripts/tests/`에 어댑터 관련 자산 없음. 기존 셸 테스트 관용은 `test_archive_contents.sh`가 대표 — `set -euo pipefail` / `REPO_ROOT` 산출 / `PASS_COUNT`·`FAIL_COUNT` + `pass()`·`fail()` / `mktemp -d` + `trap rm -rf EXIT` / **bash 3.2 호환(연관배열·`mapfile` 미사용)** / 네트워크 미사용 / 종료코드 0|1.
- Python 단위 테스트 관용은 `test_merge_hooks.py` — `@header` 블록 + `importlib`로 하이픈 파일 로드. 본 태스크의 로직은 heredoc 내부라 import 대상 파일이 없으므로 **셸 테스트 + 함수 구간 추출 seam**을 택한다.

#### 2.5.3 영향 범위

- 신규 파일만 추가하므로 기존 자산 영향 없음. CI 등록 여부는 현재 저장소에 테스트 러너 집합 스크립트가 없어 **수동 실행**(`bash scripts/tests/test_agent_adapter_fields.sh`)을 전제한다.

---

## 3. 기능별 설계

### F-001: mac 어댑터 확장 필드 변환 스펙 + 모드 기반 emit

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | (없음) | — | 스펙은 `install-mac.sh` 내부 상수로 둔다 — 별도 파일은 릴리스 아카이브 `export-ignore` 경로 리스크(`scripts/tests/test_archive_contents.sh` 배경 참조)를 새로 만든다 | `scripts/tests/test_archive_contents.sh:5-13` |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 공통 | 어댑터 섹션 상단에 `OPAL_ADAPTER_FIELD_SPEC` JSON 상수(bash 변수) 신설 | R-1 (→ D-1 §frontmatter 변환 규칙) |
| 2 | `scripts/install-mac.sh` | 공통 | `emit_platform_agent_adapter` — 스펙을 env로 전달, `mapping` 인라인 dict를 스펙 파생으로 교체, `out_lines` 3줄 고정을 스펙 순회 emit으로 교체 | `scripts/install-mac.sh:559-566`, `:584-589` |
| 3 | `scripts/install-mac.sh` | 공통 | `install_codex_agents` — 동일 스펙 소비, `codex_model_map` 제거, 4줄 고정 write를 스펙 순회 + TOML 직렬화로 교체 | `scripts/install-mac.sh:734-739`, `:795-802` |
| 4 | `scripts/install-mac.sh` | 문서 | 파일 헤더 변경이력에 `v4.6` 행 추가 | [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 \"## 변경이력\" 표에 행을 추가한다." |

#### 3.1.2 API·데이터 모델 설계

##### D-결정 1 — 스펙 자료구조: JSON 리터럴 (쟁점 1)

**결정**: 변환 테이블을 **JSON 텍스트 리터럴** 하나로 표현하고, Bash 측은 `json.loads(os.environ[...])`, PowerShell 측은 `ConvertFrom-Json`으로 소비한다.

근거 및 트레이드오프:

| 후보 | 장점 | 채택하지 않은 이유 |
|------|------|------------------|
| 언어별 네이티브 리터럴 (Python dict / PS hashtable) | 가독성, 파싱 비용 0 | 두 표현이 손으로 유지되어 **미러 검증이 사람 눈에 의존**한다 — 기존 규약(`scripts/install/windows.ps1:93` "문자 단위 동일 정규식")이 이미 이 취약점 위에 서 있다 |
| 외부 JSON 파일 (`opal/core/adapter-field-spec.json`) | 완전한 단일 소유 | 릴리스 아카이브·배포 경로에 새 의존이 생긴다(`.gitattributes export-ignore` 앵커 결함 전례). install 실패 모드가 늘어난다 |
| **JSON 리터럴 상수 (채택)** | 두 스크립트가 **바이트 동일 텍스트**를 품어 `diff`로 미러를 기계 검증 가능. 파일 의존 0 | 리터럴 중복 1건 — 단, 중복이 **검증 가능한 중복**이라는 점이 핵심 (S-5) |

**스펙 스키마**:

```
{ "fields": [ FieldSpec, ... ] }

FieldSpec := {
  "opal":          <string>   OPAL frontmatter 키명
  "order":         <int>      emit 순서 (오름차순). name=10, description=20, model=30, effort=40
  "required":      <bool>     true면 값 부재 시 디렉토리명 폴백(name 전용)
  "default":       <string?>  값 부재 시 사용할 OPAL 값 (model="standard"). 없으면 부재 = 생략
  "omit_if_empty": <bool>     빈 문자열이면 생략 (description=true)
  "flatten":       <bool>     공백 평탄화 적용 (description=true)
  "platforms": { "<platform>": PlatformSpec, ... }
}

PlatformSpec := {
  "mode":     "key" | "model_param" | "omit"
  "to":       <string?>   대상 필드명 (mode=key) / 대괄호 파라미터명 (mode=model_param)
  "attach":   <string?>   mode=model_param일 때 합성 대상 pair 키 (기본 "model")
  "values":   <object?>   OPAL 값 → 플랫폼 값 맵. 생략 시 항등(값 그대로)
  "fallback": <string?>   values 미스 시 사용할 값. 없으면 "경고 후 생략"
  "note":     <string?>   예약·비활성 사유 주석 (동작 무영향)
}
```

**배치 4형태의 선언 방식** (쟁점 2) — 4형태는 `mode` 3값 + `to` 필드명으로 표현된다. emit은 **`mode` 값에만 분기**하며 플랫폼명은 스펙 조회 키로만 등장한다(R-1 AC "기존 `platform` 변수의 테이블 조회는 허용"):

| 배치 형태 | 스펙 표현 | emit 동작 |
|----------|----------|----------|
| ① 독립 키 (이름 동일) | `mode:"key"`, `to` == `opal` | pair(`to`, 변환값) 추가 |
| ② 독립 키 (이름 다름) | `mode:"key"`, `to` != `opal` | 동일 — **①과 같은 코드 경로**. 이름 차이는 데이터일 뿐 분기가 아니다 |
| ③ model 값 내 합성 | `mode:"model_param"`, `to`=파라미터명, `attach`="model" | params 목록에 (`to`,값) 축적 → 순회 종료 후 `attach` pair의 값을 `base[k1=v1,k2=v2]`로 재작성 |
| ④ 미지원 생략 | `mode:"omit"` | 아무 것도 하지 않음 |

##### `effort` 행 스펙 (R-2 AC — Claude=① / Codex=② / Cursor=③예약 / Gemini=④)

| 플랫폼 | mode | to | values | 비고 |
|--------|------|----|--------|------|
| claude | `key` | `effort` | `low→low, medium→medium, high→high, xhigh→xhigh, max→max` | [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents) — 독립 필드 |
| codex | `key` | `model_reasoning_effort` | `minimal→minimal, low→low, medium→medium, high→high, xhigh→xhigh, max→xhigh` | [Codex Config Reference](https://learn.chatgpt.com/docs/config-file/config-reference) — 이름 다른 독립 키. `max` 미지원 → 인접 상한 `xhigh`로 축약 |
| cursor | `omit` (+ `note`: 예약) | — | — | **예약**: `inherit` 정책상 대괄호 부착 지점이 없다(TASK.md 확정 §5). 활성화 시 `mode`를 `model_param`, `to`를 `effort`로 바꾸는 것만으로 전환된다 |
| gemini | `omit` | — | — | [Gemini CLI Subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md) — 필드 표에 부재 |

**Cursor 예약을 `omit`으로 두는 이유**: `model_param`으로 선언하고 값 맵만 비우면 "예약"과 "미지원"이 스펙상 구분되지 않는다. `mode:"omit"` + `note:"reserved: model_param/effort — cursor inherit 정책 해제 후 활성"`이 **동작은 미지원과 동일하되 의도는 구분**되며, R-2 AC의 "자리만 예약"과 정확히 일치한다.

##### D-결정 2 — `name`/`description`/`model` 흡수 (쟁점 4)

**흡수한다.** R-1 AC가 명시 요구("`name`/`description`/`model` 3필드도 동일 테이블 경로로 emit된다")한다.

| 축 | 흡수 | 별도 유지 |
|----|------|----------|
| 이득 | 경로 단일화 — 신규 필드가 기존 필드와 같은 코드로 검증된다. `mapping` 인라인 dict가 스펙 파생이 되어 model 매핑 SSOT가 1곳으로 수렴 | 회귀 표면 최소 |
| 위험 | 60개 산출물 바이트 회귀 (H-1) | 통로가 "3필드 + 나머지" 2계층으로 남아 R-1 AC 미충족 |
| 완화 | **차등 골든 테스트**(S-1)가 위험을 자동 탐지 범위로 흡수 | — |

**바이트 동일성 구조 보장 3중** (최상위 제약):
1. `order` 오름차순 emit + `name=10/description=20/model=30`으로 기존 순서 고정. 신규 필드는 `order >= 40`이라 항상 뒤.
2. `effort`에 `default` 없음 → OPAL frontmatter 미선언 시 pair 미생성 → 출력 델타 0. `description`은 `omit_if_empty:true`로 기존 `if description:`(`:586`) 보존.
3. 값 인용은 기존 `yaml_escape`(`:577-583`)/`toml_escape`(`:788-790`) 함수를 **그대로 재사용**한다(재작성 금지) — 인용 규칙 변화 여지를 없앤다.
4. (검증) 차등 골든 테스트 S-1이 구판·신판 산출물 diff 공집합을 강제.

##### D-결정 3 — 값 도메인 변환 규칙 (쟁점 3 / R-3)

```
resolve(field, platformSpec, raw):
  if platformSpec.values is absent:  return raw                     # 항등
  if raw in platformSpec.values:     return platformSpec.values[raw]
  if platformSpec.fallback is set:   return platformSpec.fallback   # model 전용 — 기존 동작 보존
  warn(stderr, "unsupported <opal> value '<raw>' for platform <p> — field omitted")
  return OMIT                                                       # install 계속 (exit 0)
```

- `model` FieldSpec만 `fallback`을 갖는다: claude/cursor/gemini = `inherit`, codex = `gpt-5.5` — 현행 `mapping.get(platform,{}).get(opal_model,'inherit')`(`:567`)와 `codex_model_map.get(opal_model,'gpt-5.5')`(`:783`)의 축자 등가.
- `effort`는 `fallback` 없음 → 오타 시 경고 + 생략 (R-3 AC "전체 실패시키지 않는다").
- 경고 문구는 mac·windows 동일 문자열로 고정한다: `warn: unsupported {opal} value '{raw}' for platform {platform} — field omitted`.

##### 함수 시그니처 (mac heredoc Python — 두 heredoc 공통 형태)

```
load_spec() -> dict                                  # json.loads(os.environ['OPAL_ADAPTER_FIELD_SPEC'])
resolve_value(pspec: dict, raw: str, ctx: str) -> str|None     # None = 생략
build_pairs(spec: dict, fm: dict, platform: str, agent_name: str) -> list[tuple[str,str]]
model_level_map(spec: dict, platform: str) -> dict   # 본문 토큰 치환용 {light,standard,advanced}→실모델명 (H-8 계약 유지)
serialize_yaml(pairs) -> list[str]                   # yaml_escape 재사용
serialize_toml(pairs) -> list[str]                   # toml_escape 재사용
```

- `model_level_map()`은 스펙의 `model` FieldSpec `platforms[platform].values`를 그대로 반환한다 → `_LEVEL_RE`/`_sub_body_model`(`:596-620`)은 **로직 무변경**으로 이 dict를 받는다. 본문 변환 회귀 표면을 0으로 유지한다(H-8).
- `build_pairs`는 `mode`에만 분기한다. `model_param` 누적분은 `attach` pair를 찾아 `f"{base}[{','.join(k+'='+v)}]"`로 재작성한다(Cursor 활성화 대비 — 현재 미도달 경로이나 R-2 AC의 "각 배치 방식 최소 1개 단위 테스트"를 위해 구현하고 합성 테스트로 커버한다).

#### 3.1.3 환경 변경

해당 없음 — 신규 패키지 없음. Python stdlib `json`만 추가 사용(PyYAML 부재 폴백 경로에서도 안전).

#### 3.1.4 배치/마이그레이션

해당 없음 (F-004가 별도 담당).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (기존 3필드 흡수 · 회귀 0) | 회귀 테스트 | 구판(`git show HEAD:scripts/install-mac.sh`) emitter와 신판 emitter의 산출물이 15 에이전트 × 4플랫폼 = 60건 전부 `diff` 공집합 |
| TS-002 | R-1 AC (플랫폼명 조건 분기 신규 추가 금지) | 산출물 검사 | `emit_platform_agent_adapter`·`install_codex_agents` 본문에서 `platform ==`/`platform in (`/`== 'claude'` 등 플랫폼명 리터럴 비교가 0건 (스펙 조회 `spec[...][platform]`·`.get(platform)`은 허용) |
| TS-003 | R-2 AC (①독립 키) | 기능 테스트 | `effort: high` 선언 에이전트 → Claude md frontmatter에 `effort: high` 1행 존재 |
| TS-004 | R-2 AC (②이름 다른 독립 키) | 기능 테스트 | 동일 입력 → Codex toml에 `model_reasoning_effort = "high"` 1행 존재 |
| TS-005 | R-2 AC (③model 값 내 합성) | 단위 테스트 | `mode:"model_param"`을 임시 활성한 스펙 주입 시 `model: <base>[effort=high]` 형태로 합성 (Cursor 예약 경로의 실행 가능성 확인) |
| TS-006 | R-2 AC (④미지원 생략) | 기능 테스트 | 동일 입력 → Gemini md에 `effort` 문자열 0건, Cursor md에 `effort`·`[effort=` 0건 |
| TS-007 | R-3 AC (값 축약) | 기능 테스트 | `effort: max` → Claude `effort: max`, Codex `model_reasoning_effort = "xhigh"` |
| TS-008 | R-3 AC (미정의 값) | 기능 테스트 | `effort: hihg` → stderr에 `unsupported effort value` 경고, 산출물에 effort 키 부재, 종료코드 0, `name`/`description`/`model` 정상 출력 |
| TS-009 | H-2 (TOML 유효성) | 통합 테스트 | effort 선언/미선언 각 1건을 `~/.codex/agents/`에 배치 후 `codex doctor --json` → 해당 파일 관련 warn·fail 0 |
| TS-010 | H-8 (본문 토큰 불변) | 회귀 테스트 | TS-001의 diff에 body 구간 차이 0 (파일 전체 비교로 커버) |

### F-002: windows.ps1 미러 반영

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install/windows.ps1` | 공통 | `$OpalAdapterFieldSpec` here-string(JSON) 상수 신설 — **mac의 JSON 리터럴과 바이트 동일** | R-4, `scripts/install/windows.ps1:93` |
| 2 | `scripts/install/windows.ps1` | 공통 | `Get-AgentFrontmatter` — 3키 `switch`를 전 키 수집으로 확장, 반환에 `Fields` 해시 추가(기존 4키 유지) | `scripts/install/windows.ps1:1645-1656` |
| 3 | `scripts/install/windows.ps1` | 공통 | `Install-PlatformAgents` — `$platforms`의 `ModelMap`을 스펙 파생으로 교체, md/toml 고정 직렬화를 pair 순회로 교체 | `:1714-1735`, `:1768-1777`, `:1791-1796` |
| 4 | `scripts/install/windows.ps1` | 문서 | 파일 헤더 변경이력에 `v1.20.0` 행 추가 (mac `v4.6` 대칭 문구) | [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 |

#### 3.2.2 설계

- **JSON → 인덱싱 가능 구조 변환** (H-5): `ConvertFrom-Json`은 `PSCustomObject`를 반환하므로, 소비 직전에 `$spec.fields | ForEach-Object { ... }` + 속성 접근(`$p.mode`)을 쓰거나, PS 7의 `-AsHashtable`에 의존하지 않고 **PS 5.1 호환 헬퍼** `ConvertTo-OpalHashtable`로 재귀 변환한다. PS 5.1 호환은 기존 파일의 명시 계약이다 (`scripts/install/windows.ps1:1679-1680`: "NUL 이스케이프(`u{...})는 PS5.1 비호환이므로 … PS5.1+/7+ 공통").
- **`ModelMap` 계약 유지**: `Convert-BodyModelTokens`(`:1665-1697`)는 `[hashtable]$ModelMap` 파라미터 타입이 강제되어 있다 → 스펙에서 파생한 `{light;standard;advanced}` **hashtable**을 그대로 넘겨 본문 변환 로직을 무변경 유지한다(H-8 대칭).
- **미러 판정 기준**: 함수 본문의 문자 단위 일치는 언어가 달라 불가능하다. 본 태스크는 미러 규약을 **"스펙 JSON 리터럴 블록의 바이트 동일 + 배치 모드 3종의 동일 의미 구현"** 으로 재정의하고, 그 사실을 windows.ps1 v1.20.0 변경이력 행과 mac v4.6 행 양쪽에 기재한다.
- **경고 문구 동일화**: `Write-OpalWarn "unsupported {opal} value '{raw}' for platform {p} — field omitted"` (mac stderr 문구와 동일 본문).

#### 3.2.3 환경 변경

해당 없음. 단 **본 환경에 `pwsh` 미설치(실측)** → 실행 검증 불가, 정적 대조 + Windows 수동 검증으로 대체 (H-4, §9 R-1).

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-4 AC (미러) | 산출물 검사 | 두 스크립트에서 스펙 JSON 블록을 추출해 `diff` → 공집합 (언어 독립 자동 검증) |
| TS-012 | R-4 AC (산출물 동일) | 통합 테스트 (Windows 수동) | 동일 에이전트 1종 이상에 대해 mac·windows 산출물의 **frontmatter 블록**이 개행 문자 제외 동일 (판정 범위 한정 근거: §9 R-3·R-4) |
| TS-013 | H-5 (PS 파서 소실) | 통합 테스트 (Windows 수동) | `effort` 선언 에이전트가 Windows 산출물에서도 `effort`/`model_reasoning_effort` 키를 보유 |
| TS-014 | H-5 (PS 5.1 호환) | 산출물 검사 | 변경 구간에 PS 7 전용 구문(`-AsHashtable`, `??`, `?.`, `u{}` 이스케이프) 0건 |

### F-003: 변환 SSOT 표 갱신

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/agents.md` | 문서 | 변환 표에 `effort` 행 추가(4셀) + `(기타 OPAL 전용 필드) → (제거)` 행을 `(변환 테이블 미등재 필드) → (제거)`로 정정 | R-5 AC, `opal/core/references/agents.md:186-194` |
| 2 | `opal/core/references/agents.md` | 문서 | 표 하단에 스펙 위치·배치 모드 3종 설명 주석 추가(스펙 SSOT 포인터) | R-5 AC "표의 값이 R-1 테이블 구현과 축자 일치" |
| 3 | `opal/core/references/agents.md` | 문서 | 변경이력 `v2.1` 행 추가 (일시 KST, 태스크 번호 `(105)`) | [MUST] `docs/CONVENTIONS.md` §변경이력: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" |

#### 3.3.2 설계 — 표 갱신 형태

`effort`는 `model`처럼 값별 행 전개를 하면 6행(minimal/low/medium/high/xhigh/max)이 되어 표가 비대해진다. **1행 + 값역 주석** 형태로 기재한다:

| OPAL 필드 | Claude Code | Cursor | Gemini CLI | Codex CLI |
|----------|------------|--------|-----------|-----------|
| `effort` | `effort` (그대로) | (제거 — 예약, `inherit` 정책 해제 전 미적용) | (제거 — 미지원) | `model_reasoning_effort` (`max`→`xhigh`, 그 외 그대로) |

- 하단 주석에 값역 명시: 공통 `low`/`medium`/`high`/`xhigh` 항등, Claude 전용 `max` 항등, Codex 전용 `minimal` 항등, Codex `max`→`xhigh` 축약, 미정의 값은 경고 후 생략.
- 하단 주석에 스펙 위치 명시: `scripts/install-mac.sh` `OPAL_ADAPTER_FIELD_SPEC` / `scripts/install/windows.ps1` `$OpalAdapterFieldSpec` (양자 바이트 동일).
- `(기타 OPAL 전용 필드)` 행 정정 문구: `(변환 테이블 미등재 필드)` → 4셀 모두 `(제거)`. 의미가 "설계상 버림"에서 "등재하면 통과"로 바뀌는 것이 이번 변경의 핵심이다.

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-5 AC (행 존재·4셀) | 산출물 검사 | 표에 `effort` 행 1개, 4개 셀 모두 비어있지 않음, Gemini 셀에 "(제거 — 미지원)" 포함 |
| TS-016 | R-5 AC (축자 일치) | 산출물 검사 | 표의 Claude 셀 `effort`·Codex 셀 `model_reasoning_effort`·Codex 축약 `max→xhigh`가 스펙 JSON의 `to`/`values`와 문자 일치 (H-7) |
| TS-017 | 제약 (변경이력) | 산출물 검사 | `agents.md` 변경이력 표 최종 행이 `v2.1` + `(105)` 포함 |

### F-004: Codex `max_threads` legacy alias 교체 + 기존 config 마이그레이션

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 환경 | `install_codex_config` — append 리터럴 `max_threads = 6` → `max_concurrent_threads_per_session = 6`, 함수 주석 동시 교체, **legacy 키 in-place 치환 경로 추가** | R-6, `scripts/install-mac.sh:815`, `:834`, `:823-826` |
| 2 | `scripts/install/windows.ps1` | 환경 | `Install-CodexConfig` — 동일 (PowerShell 등가) | `scripts/install/windows.ps1:1822`, `:1836`, `:1826-1829` |
| 3 | `docs/ARCHITECTURE.md` | 문서 | `:250`의 `max_threads` 서술을 정식 키로 교체 + 변경이력 행 | `docs/ARCHITECTURE.md:250` |

#### 3.4.2 설계 — 멱등 스킵 경로 보강 (H-6)

현행 판정은 2분기(파일에 `[agents]` 있음 → 스킵 / 없음 → append)다. **3분기로 확장**한다:

| 상태 | 판정 | 동작 |
|------|------|------|
| `[agents]` 없음 (또는 파일 부재) | append | 정식 키로 블록 추가 (기존 경로, 리터럴만 교체) |
| `[agents]` 있음 + `max_threads` 라인 있음 | migrate | 해당 라인만 `max_concurrent_threads_per_session = <기존값>`으로 in-place 치환. 다른 라인·블록 무손상 |
| `[agents]` 있음 + `max_threads` 없음 | 스킵 | 기존 `info` 후 return |

- 치환 대상 정규식(양 언어 동일 의미): 행 시작 + 선택적 공백 + `max_threads` + 공백 + `=` — 주석 라인(`#`으로 시작)은 값 라인과 별도로 처리하되, mac 함수 주석/생성 주석의 `max_threads` 문구도 교체 대상에 포함한다(R-6 AC (a) "두 스크립트에서 `max_threads` 기재가 0건").
- mac은 `sed -i ''` 대신 임시 파일 + `mv`(원자적 교체)로 처리한다 — BSD/GNU `sed -i` 인자 비호환 회피.
- 값은 보존한다(사용자가 6에서 바꿨을 수 있음). 파일 없음 경로에서만 기본값 6.

#### 3.4.3 환경 변경

`~/.codex/config.toml` 형상 변경 — 사용자 로컬 파일이므로 **재배포 전 백업 사본 확보**를 실행 체크리스트 완료 기준에 포함한다.

#### 3.4.4 배치/마이그레이션

위 migrate 분기가 마이그레이션 본체. 롤백은 백업 사본 복원.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-6 AC (a) | 산출물 검사 | `grep -rn 'max_threads' scripts/` 결과 0건 |
| TS-019 | R-6 AC (b) — 신규 머신 | 단위 테스트 | config.toml 부재 픽스처 → 실행 후 `[agents]` + `max_concurrent_threads_per_session = 6` + `max_depth` + `job_max_runtime_seconds` 존재 |
| TS-020 | H-6 — 기존 머신 | 단위 테스트 | legacy 키 포함 `[agents]` + `[mcp_servers]` 픽스처 → 실행 후 `max_threads` 0건, 정식 키 1건(값 보존), `[mcp_servers]` 블록 무손상 |
| TS-021 | H-6 — 멱등 | 단위 테스트 | TS-020 결과에 2회차 실행 → 파일 바이트 무변화 |
| TS-022 | R-6 AC (b) | 통합 테스트 | 실 재배포 후 `codex doctor` 0 fail |

### F-005: 회귀 검증 자산

#### 3.5.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `scripts/tests/test_agent_adapter_fields.sh` | 배치 | 어댑터 확장 필드 통로 회귀 테스트 (TS-001~008, TS-011, TS-014, TS-018~021) | R-2 AC "각 배치 방식이 최소 1개 단위 테스트로 검증된다" |

#### 3.5.2 설계

**seam 확보** — `scripts/install-mac.sh:2098`의 가드 없는 `main "$@"` 때문에 `source` 불가. **함수 구간 추출** 방식을 쓴다:

```
extract_fn <script-path> <fn-name>  →  sed -n '/^<fn>() {/,/^}/p'
```
- 대상: `emit_platform_agent_adapter`, `install_codex_config`, 스펙 상수 블록.
- 추출본을 스크래치 셸 파일로 모아 `source` 후 `USER_HOME`/`OPAL_ADAPTER_FIELD_SPEC`만 주입해 호출한다.
- **install-mac.sh에 `main` 실행 가드를 넣지 않는다** — `curl | bash` 파이프 실행에서 `BASH_SOURCE[0]`가 비어 install이 조용히 아무 것도 하지 않는 실패 모드를 새로 만들 수 있다. 테스트 측 추출로 해결한다.

**차등 골든 테스트 (TS-001, 핵심 안전망)**:
```
1. git show HEAD:scripts/install-mac.sh > $SCRATCH/old.sh        # 변경 전 emitter
2. extract_fn old.sh / 워킹트리 install-mac.sh → old_fn.sh / new_fn.sh
3. for agent in opal/agents/*/ ; for platform in claude cursor gemini ; 
     old emit → $SCRATCH/old/<p>/<a>.md ; new emit → $SCRATCH/new/<p>/<a>.md
   codex 경로는 install_codex_agents 추출본으로 동일 대조
4. diff -r $SCRATCH/old $SCRATCH/new  → 반드시 공집합
```
- 입력은 **프로젝트 소스 `opal/agents/*/AGENT.md` 15종**(변경이력 미strip)을 쓴다 — 구판·신판이 같은 입력을 받으므로 strip 여부는 무관하고, 배포본 상태에 의존하지 않아 재현성이 높다.
- 이 테스트는 F-001 착수 **전에 먼저 통과**해야 한다(구판==구판 → trivially pass). 그 상태를 확인해야 테스트 자체의 결함을 배제할 수 있다.

**스펙 미러 diff (TS-011)**:
```
awk 범위 추출: '# >>> OPAL_ADAPTER_FIELD_SPEC >>>' ~ '# <<< OPAL_ADAPTER_FIELD_SPEC <<<'
두 스크립트에서 추출한 JSON 본문을 diff → 공집합
추가로 python3 -c 'json.load' 로 양쪽 파싱 성공 확인
```
- 두 스크립트에 **동일한 센티넬 주석 마커**를 넣어 추출을 결정론화한다.

**관용 준수**: `set -euo pipefail` / `REPO_ROOT` / `pass()`·`fail()` 카운터 / `mktemp -d` + `trap` / **bash 3.2 호환(연관배열·`mapfile` 금지)** / 네트워크 미사용 / 종료코드 0|1 — 근거 `scripts/tests/test_archive_contents.sh:15-31`.

**환경 의존 가드**: `codex` CLI 부재 시 TS-009/TS-022는 SKIP 처리(카운터 별도)하고 전체를 실패시키지 않는다. `pwsh` 미설치이므로 PowerShell 실행 테스트는 본 스크립트 범위에서 제외한다.

#### 3.5.3 환경 변경

해당 없음 (bash + python3 + jq는 모두 기존 환경에 존재 — 실측 확인).

#### 3.5.4 배치/마이그레이션

해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-023 | F-005 자체 건전성 | 회귀 테스트 | 코드 변경 전 실행 시 TS-001이 PASS(구판==구판), effort 케이스(TS-003·004·007)는 FAIL — 즉 **RED이 먼저 확인**된 뒤 F-001이 GREEN으로 만든다 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| 1 | F-005, F-004 | 1, 2 | 병렬 가능 | 서로 다른 파일 영역(테스트 신규 / codex config 함수). 단 Step 2는 Step 1의 TS-018~021 케이스를 필요로 하므로 순차 권장 |
| 2 | F-001 | 3, 4 | 순차 | 동일 파일(`install-mac.sh`) 연속 수정 — 반드시 같은 에이전트 |
| 3 | F-002 | 5 | 순차 | F-001 확정 스펙을 미러 |
| 4 | F-005, F-003 | 6, 7 | 병렬 가능 | 테스트 실행(코드) / SSOT 표(문서) 독립 |
| 5 | 전체 | 8 | 순차 | 실 install 재배포 + 실측 검증 |
| 6 | 문서 | 9 | 순차 | docs/ 갱신 (PM 직접) |

### 4.2 실행 체크리스트

> 총 9개 Step | Phase 6개 | 실행 모드: **복잡**

#### Step 1: 회귀 검증 자산 신설 (RED 확인 포함)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/tests/test_agent_adapter_fields.sh` (신규)
- **작업 내용**: `test_archive_contents.sh` 관용(`set -euo pipefail`·PASS/FAIL 카운터·`mktemp -d`+`trap`·bash 3.2 호환·네트워크 미사용)을 따라 테스트 신설. ① `extract_fn` 헬퍼(sed 범위 추출) ② 차등 골든(TS-001·010: `git show HEAD:scripts/install-mac.sh` 구판 vs 워킹트리 신판 × `opal/agents/*` 15종 × 4플랫폼 `diff -r`) ③ 배치 모드 4형태 케이스(TS-003~006) ④ 값 도메인 케이스(TS-007·008) ⑤ 플랫폼명 분기 스캔(TS-002) ⑥ 스펙 미러 diff(TS-011, 센티넬 마커 기반) ⑦ PS 7 전용 구문 스캔(TS-014) ⑧ codex config 3분기 + 멱등(TS-018~021) ⑨ `codex` CLI 부재 시 SKIP 가드. **install-mac.sh에 `main` 실행 가드를 추가하지 않는다**(§3.5.2)
- **완료 기준**: 코드 변경 전 상태에서 실행 시 TS-001·TS-010·TS-018 이외 effort 관련 케이스가 **FAIL로 명확히 리포트**되고(RED 확인), TS-001은 PASS하며, 스크립트가 `bash -n` 문법 검사를 통과한다
- **테스트**: TS-023
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: Codex `max_threads` legacy alias 교체 + 마이그레이션 경로
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (`install_codex_config` `:812-841`), `scripts/install/windows.ps1` (`Install-CodexConfig` `:1817-1857`)
- **작업 내용**: 양 스크립트에서 `max_threads` 리터럴·주석을 `max_concurrent_threads_per_session`으로 전량 교체. 멱등 판정을 2분기 → 3분기로 확장(§3.4.2): `[agents]` 존재 + legacy 키 존재 시 **해당 라인만 in-place 치환(값 보존, 타 블록 무손상)**. mac은 임시 파일 + `mv`(BSD/GNU `sed -i` 비호환 회피). 양 파일 헤더 변경이력 행 추가
- **완료 기준**: `grep -rn 'max_threads' scripts/` 0건. TS-019~021 PASS. `~/.codex/config.toml` 백업 사본이 스크래치에 확보됨
- **테스트**: TS-018, TS-019, TS-020, TS-021
- **실행 방법**: sub-agent
- **의존**: Step 1 (테스트 케이스 선행)

#### Step 3: mac — 변환 스펙 상수 + md 어댑터 경로 테이블화
- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (어댑터 섹션 `:454-643`)
- **작업 내용**: ① 어댑터 섹션 상단에 센티넬 주석(`# >>> OPAL_ADAPTER_FIELD_SPEC >>>` / `# <<< ... <<<`)으로 감싼 `OPAL_ADAPTER_FIELD_SPEC` JSON 상수 신설 — `name`(10)/`description`(20)/`model`(30)/`effort`(40) 4 FieldSpec, 4플랫폼 PlatformSpec, `model`만 `fallback` 보유(§3.1.2 D-결정 3) ② `emit_platform_agent_adapter`가 스펙을 env로 heredoc에 전달 ③ 인라인 `mapping` dict(`:559-566`) 제거 → `model_level_map(spec, platform)` 파생. `_LEVEL_RE`/`_sub_body_model`(`:596-620`) **로직 무변경** ④ `out_lines` 3줄 고정(`:584-589`) → `build_pairs()` + `serialize_yaml()`. `yaml_escape`(`:577-583`) 재사용 ⑤ `build_pairs`는 `mode`(`key`/`model_param`/`omit`)에만 분기 — 플랫폼명 리터럴 비교 금지 ⑥ 미정의 값 = stderr 경고 + 필드 생략, 종료코드 0
- **완료 기준**: TS-001(Claude/Cursor/Gemini 45건 diff 공집합)·TS-002·TS-003·TS-005·TS-006·TS-007(Claude측)·TS-008·TS-010 PASS. `bash -n scripts/install-mac.sh` 통과
- **테스트**: TS-001, TS-002, TS-003, TS-005, TS-006, TS-007, TS-008, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: mac — Codex TOML 어댑터 경로 테이블화
- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (`install_codex_agents` `:700-810`)
- **작업 내용**: Codex heredoc이 동일 `OPAL_ADAPTER_FIELD_SPEC`을 소비하도록 전환. `codex_model_map`(`:734-739`) 제거 → 스펙 파생. 4줄 고정 write(`:795-802`) → `build_pairs()` + `serialize_toml()`(`toml_escape` `:788-790` 재사용). `developer_instructions`는 pair 체계 밖의 본문 슬롯으로 유지(스펙 미등재). **본문 `body`는 현행대로 무변환 유지**(§9 R-3의 기존 비대칭을 이번 태스크에서 건드리지 않는다 — 건드리면 바이트 동일성 제약과 충돌)
- **완료 기준**: TS-001의 codex 15건 포함 60건 전체 diff 공집합. TS-004·TS-007(Codex측)·TS-009 PASS. `codex doctor --json`이 프로브 파일에 대해 0 warn·0 fail(프로브 삭제 후 원복 확인)
- **테스트**: TS-001, TS-004, TS-007, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3 (동일 파일·동일 스펙 상수)

#### Step 5: windows.ps1 미러 반영
- [x] 완료
- **소속 기능**: F-002
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install/windows.ps1` (`Get-AgentFrontmatter` `:1601-1657`, `Install-PlatformAgents` `:1699-1815`)
- **작업 내용**: ① `$OpalAdapterFieldSpec` here-string 신설 — **mac JSON 리터럴과 바이트 동일**, 동일 센티넬 주석으로 감쌈 ② `ConvertTo-OpalHashtable` 재귀 변환 헬퍼(PS 5.1 호환, `-AsHashtable` 미사용) ③ `Get-AgentFrontmatter` 3키 `switch`(`:1645-1649`)를 전 키 수집으로 확장, 반환에 `Fields` 추가(기존 `Name`/`Description`/`Model`/`Body` 4키 유지) ④ `$platforms`의 `ModelMap`을 스펙 파생 hashtable로 교체 — `Convert-BodyModelTokens`의 `[hashtable]` 파라미터 계약 유지 ⑤ md `$fmLines`(`:1791-1796`)·TOML(`:1768-1777`) 고정 직렬화를 pair 순회로 교체, `Format-YamlValue`(`:1655-1663`) 재사용 ⑥ 경고 문구를 mac과 동일 본문으로 ⑦ 헤더 변경이력 `v1.20.0` 행 추가(미러 규약 재정의 사실 명기)
- **완료 기준**: TS-011(스펙 JSON diff 공집합)·TS-014(PS 7 전용 구문 0건) PASS. 변경 구간 정적 리뷰로 배치 모드 3종이 mac과 동일 의미임을 확인. **Windows 실행 검증(TS-012·013)은 미수행 상태로 완료 보고에 명시**(pwsh 미설치 — H-4)
- **테스트**: TS-011, TS-014 (TS-012·TS-013은 Windows 머신 이월)
- **실행 방법**: sub-agent
- **의존**: Step 3, Step 4 (확정 스펙 필요)

#### Step 6: 전체 테스트 실행 + GREEN 확인
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/tests/test_agent_adapter_fields.sh`
- **작업 내용**: 전체 스위트 실행. Step 1에서 RED였던 케이스가 전건 GREEN인지 확인. 기존 자산 회귀 확인차 `scripts/tests/test_archive_contents.sh`·`test_version_stamp.sh`도 실행. 실패 시 원인을 Step 3~5로 되돌려 수정
- **완료 기준**: `bash scripts/tests/test_agent_adapter_fields.sh` 종료코드 0, FAIL 0건 (SKIP은 사유와 함께 리포트 허용). 기존 테스트 2종 종료코드 0
- **테스트**: TS-001~TS-011, TS-014, TS-018~TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 3, 4, 5

#### Step 7: 변환 SSOT 표 갱신
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/agents.md` (`:186-194`, 변경이력 `:346~`)
- **작업 내용**: §3.3.2 형태로 `effort` 행 추가(4셀), `(기타 OPAL 전용 필드)` → `(변환 테이블 미등재 필드)` 정정, 하단에 값역 주석 + 스펙 위치 포인터(`OPAL_ADAPTER_FIELD_SPEC` / `$OpalAdapterFieldSpec`, 바이트 동일 규약) + 배치 모드 3종 설명 추가. 변경이력 `v2.1` 행 추가(KST 일시, `(105)`)
- **완료 기준**: TS-015·TS-016·TS-017 PASS — 특히 표 셀 값이 스펙 JSON의 `to`/`values`와 축자 일치
- **테스트**: TS-015, TS-016, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 3 (스펙 확정 후)

#### Step 8: 실 install 재배포 + 4플랫폼 실측 검증 (3-Run 절차)
- [ ] 완료
- **소속 기능**: F-001, F-002, F-004
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: (수정) `opal/agents/probe-effort-105/AGENT.md` (임시 프로브 — 검증 후 삭제), (실행) `./scripts/install-mac.sh`, (검증 대상) `~/.claude/agents/`, `~/.cursor/agents/`, `~/.gemini/agents/`, `~/.codex/agents/`, `~/.codex/config.toml`
- **작업 내용**:
  **[MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."** — 프로브 에이전트도 예외가 아니다. 배포 디렉토리(`~/.opal/agents/`·`~/.claude/agents/` 등)에 파일을 직접 쓰지 않고, **프로젝트 소스 `opal/agents/`에 생성한 뒤 install을 경유**해 배포본을 생성한다.
  ① **사전 스냅샷 (프로브 없는 15종 상태)**: 4개 배포 디렉토리의 `AUTO-GENERATED` 헤더 보유 파일 수가 15/15인지 확인(H-9 오탐 차단), 60개 산출물 + `~/.codex/config.toml`을 스크래치에 백업. 이 스냅샷이 ③의 유일한 회귀 기준선이다.
  ② **Run A (소스 15종, 프로브 없음)**: `./scripts/install-mac.sh` 재배포 실행.
  ③ **Run A 사후 — 회귀 판정**: 스냅샷 대비 60개 산출물 `diff` 공집합 (완료기준 (a)). **프로브 도입 전에 이 판정을 끝낸다** — 프로브가 소스에 존재하는 동안에는 배포 대상이 16종이 되어 파일 수가 달라지므로, 60건 기준선 비교는 Run A에서만 유효하다.
  ④ **Run B (소스 16종, 프로브 추가)**: `opal/agents/probe-effort-105/AGENT.md`를 신규 생성한다 — frontmatter `name: probe-effort-105` / `description` 1줄 / `model: standard` / **`effort: high`**, 본문은 1~2줄 더미(인라인 `model: <레벨>` sub-dispatch 토큰을 넣지 않는다 — 본문 변환 경로를 이 검증에 섞지 않기 위함). install 재실행 후 확인: Claude `~/.claude/agents/probe-effort-105.md`에 `effort: high` 1행 / Codex `~/.codex/agents/probe-effort-105.toml`에 `model_reasoning_effort = "high"` 1행 (완료기준 (b)) / Gemini `~/.gemini/agents/probe-effort-105.md`·Cursor `~/.cursor/agents/probe-effort-105.md`에 `effort` 문자열·`[effort=` 0건 (완료기준 (c)). **동시에 기존 15종 60건이 ①의 스냅샷과 여전히 `diff` 공집합인지 재확인**한다(프로브 추가가 타 에이전트 산출물에 영향을 주지 않음 = 스펙 순회가 에이전트 단위로 독립임의 확인).
  ⑤ **Run C (프로브 소스 삭제, 15종 복귀)**: `opal/agents/probe-effort-105/`를 삭제하고 install 재실행. `~/.opal/agents/`는 install의 `clean_dirs`에 포함되어(`scripts/install-mac.sh:1037`) 자동으로 15종으로 복귀하지만, **플랫폼 어댑터 디렉토리(`~/.claude|.cursor|.gemini|.codex/agents/`)는 clean 대상이 아니므로 고아 어댑터 4개(md 3 + toml 1)가 잔존할 수 있다** — 잔존 여부를 확인하고 잔존 시 해당 4개 파일만 삭제한다(모두 `AUTO-GENERATED` 헤더 보유 = 사용자 파일 아님). 최종적으로 4개 디렉토리 전부 15/15로 복귀하고 `probe-effort-105` 문자열이 배포 경로 전체에서 0건임을 확인한다.
  ⑥ `~/.codex/config.toml`에 `max_concurrent_threads_per_session = 6` 존재 + `max_threads` 0건.
  ⑦ `codex doctor --json` 0 warn·0 fail (완료기준 (d)) — Run C 완료 후(15종 복귀 상태)에 실행한다.
- **완료 기준**: ①~⑦ 전건 확인. 특히 **(가)** ③의 60건 diff 공집합이 프로브 도입 **전** 시점에 확정되었을 것 **(나)** `opal/agents/`가 15종으로 원복되고 `git status --porcelain opal/agents/`가 비어 있을 것 **(다)** 4개 배포 디렉토리 각 15/15 + `grep -rl 'probe-effort-105'`를 5개 배포 경로에 적용한 결과 0건(프로브 잔존 0) **(라)** `~/.codex/config.toml` 백업 사본 확보 및 최종 상태 확인 완료
- **테스트**: TS-009, TS-012(mac측), TS-022 + 완료기준 (a)~(d)
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 7

#### Step 9: docs/ 갱신
- [ ] 완료
- **소속 기능**: F-004 (+ F-001 파급)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md` (`:250` + 변경이력)
- **작업 내용**: `:250`의 `install_codex_config()` 서술에서 `max_threads`를 `max_concurrent_threads_per_session`으로 정정하고, `install_codex_agents()`/`emit_platform_agent_adapter` 서술에 **확장 필드 변환 스펙 통로**가 생겼다는 1문장을 추가한다(어댑터 구조 변경 = 시스템 구조 변경). 변경이력 행 추가. `docs/CONVENTIONS.md` §플랫폼 분기 격리는 문구 변경 불요(스펙 도입이 이 규칙을 강화할 뿐 규칙 자체는 불변)로 판정
- **완료 기준**: `grep -n 'max_threads' docs/` 0건. ARCHITECTURE.md 변경이력 최신 행에 태스크 번호 `(105)` 포함
- **테스트**: 산출물 검사 (grep)
- **실행 방법**: direct
- **의존**: Step 8

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | Step 2의 완료 기준이 Step 1이 만든 TS-019~021 케이스에 의존 |
| Step 1 → Step 3 | 차등 골든 안전망이 없는 상태에서 emit을 건드리면 바이트 회귀를 탐지할 수단이 없다 (최상위 제약) |
| Step 2 ∥ Step 3 | 파일은 같으나(`install-mac.sh`) 함수 구간이 완전 분리(`install_codex_config` vs 어댑터 섹션) — 다만 동일 파일 편집 충돌 회피를 위해 **같은 에이전트에 순차 배치**한다(§7 C-1 그룹핑 규칙 1) |
| Step 3 → Step 4 | 동일 파일, Step 3이 만든 스펙 상수를 Step 4가 소비 |
| Step 4 → Step 5 | windows는 mac 확정 스펙의 미러 — 스펙이 흔들리면 재작업 |
| Step 6 ∥ Step 7 | 코드 테스트 실행 vs 참조 문서 편집 — 대상 파일 무교집합 |
| Step 6, 7 → Step 8 | 재배포는 코드·문서 확정 후 1회만 수행(사용자 환경 변경이므로 반복 최소화) |
| Step 8 → Step 9 | 실측으로 확정된 사실만 docs에 기재 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | effort 미선언 에이전트 산출물 바이트 동일 | TS-001, TS-010 | 구판 vs 신판 60건 `diff -r` 공집합 |
| F-001 | 플랫폼명 하드코딩 분기 미신설 | TS-002 | emit 함수 본문에 플랫폼명 리터럴 비교 0건 |
| F-001 | 배치 4형태 동작 | TS-003, TS-004, TS-005, TS-006 | 각 형태 최소 1케이스 PASS |
| F-001 | 값 도메인 변환·미정의 값 방어 | TS-007, TS-008 | `max`→Claude `max`/Codex `xhigh`; 오타 시 경고+생략+exit 0 |
| F-001 | Codex TOML 유효성 | TS-009 | `codex doctor --json` 0 warn·0 fail |
| F-002 | 스펙 미러 바이트 동일 | TS-011 | 두 스크립트 스펙 JSON 블록 diff 공집합 |
| F-002 | PS 5.1 호환 | TS-014 | PS 7 전용 구문 0건 |
| F-002 | Windows 산출물 정합 (이월) | TS-012, TS-013 | Windows 머신에서 frontmatter 블록 동일 + effort 키 보존 |
| F-003 | SSOT 표 갱신·축자 일치 | TS-015, TS-016, TS-017 | effort 행 4셀 + 스펙과 문자 일치 + v2.1 변경이력 |
| F-004 | legacy alias 제거·마이그레이션·멱등 | TS-018~TS-022 | `max_threads` 0건 · 3분기 전건 PASS · 2회차 바이트 무변화 · `codex doctor` 0 fail |
| F-005 | 테스트 자산 건전성 | TS-023 | 변경 전 RED / 변경 후 GREEN 전이가 관측됨 |

### 5.2 회귀 테스트

- [ ] `bash scripts/tests/test_agent_adapter_fields.sh` 종료코드 0, FAIL 0
- [ ] `bash scripts/tests/test_archive_contents.sh` 종료코드 0 (신규 파일이 릴리스 아카이브 계약을 깨지 않음)
- [ ] `bash scripts/tests/test_version_stamp.sh` 종료코드 0
- [ ] `bash -n scripts/install-mac.sh` 문법 통과
- [ ] 재배포 후 `~/.claude|.cursor|.gemini/agents/*.md` 15/15, `~/.codex/agents/*.toml` 15/15 존재 (수량 회귀 없음)
- [ ] 재배포 후 4플랫폼 배포본 사전 스냅샷 대비 diff 공집합
- [ ] 본문 인라인 `model: <레벨>` sub-dispatch 토큰 변환 결과 불변 (TS-010)
- [ ] `~/.codex/config.toml`의 `[mcp_servers]` 등 타 블록 무손상

### 5.3 코드/문서 품질

- [ ] `docs/CONVENTIONS.md` §변경이력 작성 의무 준수 — `install-mac.sh`(v4.6) · `windows.ps1`(v1.20.0) · `agents.md`(v2.1) · `docs/ARCHITECTURE.md` 4건 모두 행 추가, 일시 KST `YYYY-MM-DD HH:mm`, 태스크 번호 `(105)` 포함
- [ ] `docs/CONVENTIONS.md` §플랫폼 분기 격리 준수 — 플랫폼 차이가 어댑터 계층 스펙 안에만 존재
- [ ] `docs/CONVENTIONS.md` §배포 경계 준수 — `~/.opal/` 직접 편집 0건, 모든 변경이 `scripts/`·`opal/`에서 수행된 후 install로 전파
- [ ] `agents.md` 표 ↔ 스펙 JSON 축자 일치 (H-7)
- [ ] 테스트 스크립트가 bash 3.2 호환(연관배열·`mapfile` 미사용)
- [ ] git 이력 변경 없음 — 워킹트리에만 변경 잔류 (커밋은 소유자 권한)

### 5.4 보안

- [ ] 스펙 JSON·테스트 픽스처에 토큰·시크릿·개인 경로 하드코딩 0건
- [ ] `~/.codex/config.toml` in-place 치환이 사용자 자격증명·`[mcp_servers]` 설정을 손상시키지 않음 (TS-020)
- [ ] 테스트가 `mktemp -d` 스크래치에서만 쓰기하며 `trap`으로 정리 (사용자 홈 오염 0)
- [ ] Step 8 프로브 에이전트·백업 파일이 검증 후 완전 삭제 (잔여물 0)
- [ ] 어댑터가 사용자 관리 파일(AUTO-GENERATED 헤더 부재)을 덮어쓰지 않는 기존 가드(`scripts/install-mac.sh:569-574`) 동작 불변

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 |
| 변경 파일 수 | 5개 (`install-mac.sh`, `windows.ps1`, `agents.md`, `docs/ARCHITECTURE.md`, `test_agent_adapter_fields.sh` 신규) | 복잡 |
| 모듈 범위 | 다중 (Bash 어댑터 / PowerShell 어댑터 / 참조 문서 / 테스트) | 복잡 |
| 작업 유형 | 대규모 개선 (emit 구조 전환) | 복잡 |
| 외부 의존성 | 신규 패키지 없음. 검증에 `codex` CLI(존재) / `pwsh`(**부재**) | 단순(구현) / 제약(검증) |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 ── A1(opal-task-agent) : Step 1                 [테스트 자산 — 독립 파일]
Batch 2 ── A2(opal-task-agent) : Step 2 → 3 → 4         [install-mac.sh 단독 소유 — 파일 충돌 방지]
Batch 3 ── A3(opal-task-agent) : Step 5                 [windows.ps1 단독 소유]
Batch 4 ── A4(opal-task-agent) : Step 6                 [테스트 실행]
        ∥  A5(opal-task-agent) : Step 7                 [agents.md — 무교집합]
Batch 5 ── A6(opal-task-agent) : Step 8                 [재배포 실측]
Batch 6 ── PM                  : Step 9                 [docs/]
```

**그룹핑 근거**: Step 2·3·4가 모두 `scripts/install-mac.sh`를 수정하므로 규칙 1(파일 충돌 방지)에 따라 **반드시 단일 에이전트 A2**에 배치한다. Step 5는 `windows.ps1` 단독이므로 분리하되, A2 완료 후 실행(스펙 확정 의존).

### C-2. 스킬 요구사항

- 단계 스킬: `op-dev-execute`(구현 Step), `op-dev-test`(Step 6·8 검증). 기존 자산으로 충족 — 신규 스킬 갭 없음.
- 패턴 반복 판별: "install 스크립트 mac·windows 미러 수정"이 Step 2·5에서 2회 → 임계(3회) 미만이므로 **인라인 지침**으로 처리(스킬 신설 불요).

### C-3. 도구 요구사항

| 도구 | 상태 | 용도 |
|------|------|------|
| `bash` 3.2+, `python3` | 존재 (`/opt/homebrew/bin/python3`) | 어댑터 실행·테스트 |
| `jq` | 존재 (`/usr/bin/jq`) | 스펙 JSON 검증 보조 |
| `codex` CLI | 존재 (`~/.local/bin/codex`) | TS-009·TS-022 `codex doctor --json` |
| `pwsh` | **부재** | Step 5 런타임 검증 불가 → 정적 대조로 대체, TS-012·013은 Windows 머신 이월 (H-4) |
| `git` | 존재 | 차등 골든의 구판 소스 취득(`git show HEAD:`) — **읽기 전용, 이력 변경 없음** |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 |
|------|------|------|
| L1 단위/차등 | TS-001~008, 010, 011, 014, 018~021, 023 | `bash scripts/tests/test_agent_adapter_fields.sh` (Step 1 RED → Step 6 GREEN) |
| L2 통합 | TS-009 (`codex doctor --json` 프로브) | Step 4·6 |
| L3 실배포 | TS-022, 완료기준 (a)~(d) | Step 8 — 사전 스냅샷/사후 diff/프로브 원복 |
| L3b 이월 | TS-012, TS-013 (Windows) | Windows 머신 수동 — 완료 보고에 미검증 사실 명기 |
| 회귀 | 기존 스위트 2종 | Step 6 |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 어댑터 (mac) | Bash 3.2 + 내장 Python heredoc (PyYAML 우선 / stdlib 정규식 폴백) | 해당 없음 — 커뮤니티 스킬 매칭 없음 |
| 어댑터 (windows) | PowerShell 5.1 호환 | 해당 없음 |
| 데이터 포맷 | JSON (스펙) / YAML frontmatter (md 산출물) / TOML (Codex 산출물) | 해당 없음 |
| 테스트 | Bash 테스트 스크립트 (`scripts/tests/` 관용) | 해당 없음 |

> `trailofbits/modern-python` 등 커뮤니티 스킬은 애플리케이션 Python 프로젝트 대상이며, install 스크립트 내장 heredoc(stdlib 한정·venv 비의존이 요구사항)에는 적용하지 않는다.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (미사용) | 대상이 프로젝트 내부 셸/PowerShell 어댑터이고, 플랫폼 필드 사양은 TASK.md 배경 분석 (2)에서 공식 문서 + 로컬 CLI 실측으로 이미 확정되어 있어 추가 라이브러리 문서 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 에이전트 어댑터 규칙 | `opal/core/references/agents.md` | frontmatter 변환 SSOT 표(`:186-194`) — R-5 대상, 스펙 값의 축자 기준 |
| D-2 | 소스 | mac install 스크립트 | `scripts/install-mac.sh` | 어댑터 emit 본체 — `:462-643`(md), `:700-810`(Codex), `:812-841`(config) |
| D-3 | 소스 | windows install 스크립트 | `scripts/install/windows.ps1` | mac 미러 — `:1601-1657`, `:1665-1697`, `:1699-1815`, `:1817-1857`. `:93`이 미러 규약 원문 |
| D-4 | 설계 | 모델 매핑 | `opal/core/references/opal-model-mapping.md` | §5 레벨→실값 2단 + 셀 단위 오버라이드 — 값 맵 스키마의 선례 |
| D-5 | 외부 | Claude Code Sub-agents | [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents) | `effort` 독립 필드·허용값 근거 |
| D-6 | 외부 | Codex Config Reference | [Codex Config Reference](https://learn.chatgpt.com/docs/config-file/config-reference) | `model_reasoning_effort` 값역 + `max_threads` legacy alias 근거 |
| D-7 | 외부 | Cursor Subagents | [Cursor Subagents](https://cursor.com/docs/agent/subagents) | model 값 대괄호 파라미터(`model_param` 모드) 근거 |
| D-8 | 외부 | Gemini CLI Subagents | [Gemini CLI Subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md) | effort 미지원(`omit` 모드) 근거 |
| D-9 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 변경이력 의무·플랫폼 분기 격리·배포 경계·Guards |
| D-10 | 소스 | 릴리스 아카이브 회귀 테스트 | `scripts/tests/test_archive_contents.sh` | 셸 테스트 관용(카운터·scratch·bash 3.2 호환) + 신규 파일 배치 리스크 근거(`:5-13`) |
| D-11 | 소스 | merge-hooks 단위 테스트 | `scripts/tests/test_merge_hooks.py` | 로직 seam 분리 선례(install-mac.sh v4.1, 076) |
| D-12 | 설계 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` | `:250` Codex 어댑터·`max_threads` 서술 — Step 9 갱신 대상 |

**[MUST] 인용 (설계에 직접 구속력이 있는 항목)**

- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다."
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 \"## 변경이력\" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
- [MUST] `docs/CONVENTIONS.md` §Guards: "사용자가 명시적으로 \"승인\", \"진행해\", \"구현해\" 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
- [MUST] `scripts/install/windows.ps1:93`: "install-mac.sh `_sub_body_model` 미러(문자 단위 동일 정규식)"
- [MUST] `opal/core/references/agents.md:196`: "Codex 컬럼 모델값은 `opal/core/references/opal-model-mapping.md` §2 Codex 컬럼(SSOT v1.4)과 동일하게 유지한다."
- [MUST] `scripts/install-mac.sh:604`: "정규식은 frontmatter가 아닌 `body` 문자열에만 적용된다(:504에서 분리 보유 — frontmatter 변환과 독립)."

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `pwsh` 미설치로 windows 어댑터 런타임 검증 불가 (실측) | F-002 | 중 — Windows 사용자에게만 회귀가 노출될 수 있음 | 스펙 JSON 바이트 diff(TS-011) + PS 5.1 구문 스캔(TS-014)으로 정적 방어. TS-012·013은 Windows 머신 이월로 명시하고 완료 보고에 미검증 사실을 기재 |
| R-2 | 스펙 JSON 리터럴이 두 스크립트에 중복 존재 | F-001, F-002 | 중 — 한쪽만 갱신되면 플랫폼별 산출물이 갈림 | 센티넬 주석 + TS-011 자동 diff. `agents.md`에 "양자 바이트 동일" 규약을 명문화 |
| R-3 | **[기존 결함, 비대상]** mac Codex 경로는 본문 model 토큰 변환 미적용(`scripts/install-mac.sh:802` `toml_escape(body)`), windows Codex 경로는 적용(`scripts/install/windows.ps1:1753`) — 이미 존재하는 미러 위반 | F-002 | 중 — R-4 AC "산출물 동일" 판정이 Codex TOML 본문에서 실패한다 | **이번 태스크에서 고치지 않는다** — 고치면 sub-dispatch 토큰을 가진 에이전트의 Codex 산출물 바이트가 바뀌어 최상위 제약("effort 미선언 산출물 바이트 동일")과 정면 충돌한다. R-4 판정 범위를 **frontmatter 블록**으로 한정하고, 별건 태스크로 PM에 보고 |
| R-4 | **[기존 결함, 비대상]** mac/windows md 산출물의 AUTO-GENERATED 헤더 문구 상이(`install-mac.sh` vs `install-windows.ps1`, SSOT 주석 줄 수도 상이) | F-002 | 저 | R-3과 동일 처리 — R-4 AC 판정 범위를 frontmatter 블록으로 한정 |
| R-5 | 기존 설치 머신에서 `[agents]` 멱등 스킵으로 legacy 키 잔존 (H-6) | F-004 | 중 — R-6 AC (b) 미충족 | 3분기 마이그레이션 경로 추가(§3.4.2) + TS-020·021로 검증 |
| R-6 | Step 8 재배포가 사용자 실환경(`~/.claude` 등 60파일 + `~/.codex/config.toml`)을 변경 | 전체 | 중 | 사전 스냅샷 백업 + 사후 diff 공집합 확인 + 프로브 완전 원복을 완료 기준에 명시. `~/.opal/` **직접 편집은 하지 않고** install 경유만 사용 |
| R-7 | 차등 골든이 `git show HEAD:`에 의존 — 워킹트리가 이미 더러우면 기준이 흔들림 | F-005 | 저 | 테스트 시작 시 `git status --porcelain scripts/install-mac.sh`가 비어있지 않으면 "baseline=HEAD" 사실을 리포트에 명시. **git 이력은 변경하지 않는다**(읽기 전용) |
| R-8 | `model_param` 모드가 현재 어떤 플랫폼에서도 활성이 아니어서 실사용 미검증 코드가 됨 | F-001 | 저 | TS-005가 임시 스펙 주입으로 경로를 실행 검증한다 (dead code 방지) |
| R-9 | `Get-AgentFrontmatter` 반환 계약 변경(4키→5키)이 다른 호출처를 깰 가능성 | F-002 | 저 | 현 시점 호출처는 `Install-PlatformAgents` 1곳(실측). 기존 4키를 **제거하지 않고 추가만** 하여 하위호환 유지 |

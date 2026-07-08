# QA-EXECUTE: 009-260524-opp-codex-bootstrapper-integration

> 검증 일시: 2026-05-24 (KST) | QA 워커: opal-task-qa-agent | 대상: EXECUTE 단계 변경 파일 12개 + PLAN.md §5

---

## 1. 요약

- **전체 판정**: CONDITIONAL_PASS
- **검증 항목**: 25개 (§5.1 기능 10 + §5.2 일관성 5 + §5.3 문서 품질 5 + §D 코딩 원칙 5) / 통과 **24** / 경고 **1**
- **Blocker**: 0건
- **Major**: 0건
- **Minor**: 1건 — windows.ps1 PowerShell `-replace '\\', '\\'` 백슬래시 이스케이프 무효 패턴 (TOML triple-quote 파싱은 정상이나 AGENT.md 본문에 `\` 포함 시 TOML 유효성 깨질 수 있음)

---

## 2. 검증 결과 — 항목별 (A/B/C/D/E)

### A. 기능 테스트 (§5.1 — 10항목)

| # | 검증 항목 | 결과 | 근거 (파일:줄 또는 명령 출력) |
|---|----------|------|---------------------------|
| A-1 | R-1 codex-bootstrap.md 파일 존재 | Pass | `test -f opal/bootstrapper/codex-bootstrap.md` 확인 |
| A-2 | R-1 코드블록 내 2줄 부트스트랩 명령 | Pass | `grep -c "OPAL AI Agent — 필수 부트스트랩"` → 1. 코드블록 내 `~/.opal/AGENT.md` + `~/.opal/identity.md` 2줄 존재 확인 |
| A-3 | R-1 변경이력 v1.0/2026-05-24/태스크 009 | Pass | `opal/bootstrapper/codex-bootstrap.md:25-27`: v1.0 / 2026-05-24 / 태스크 009 행 존재 |
| A-4 | R-2(a) codex 분기 호출 + graceful skip | Pass | `scripts/install-mac.sh:1025-1026` install_opal_section codex-bootstrap.md 호출, `scripts/install-mac.sh:1341` `warn "codex CLI 없음 — 수동 등록: ..."` |
| A-5 | R-2(b) mcps/*.json platforms에 codex | Pass | `python3 -c "..."` → 4개 파일 모두 `['claude', 'cursor', 'gemini', 'antigravity', 'codex']` 확인 |
| A-6 | R-2(c) emit_platform_agent_adapter MODEL_MAP codex 행 | Pass | `scripts/install-mac.sh:553`: `'codex': {'light': 'gpt-5-mini', 'standard': 'gpt-5-codex', 'advanced': 'gpt-5.1-codex-max'}` |
| A-7 | R-2(d) 변경이력 v2.6/2026-05-24/태스크 009 | Pass | `scripts/install-mac.sh:23`: `v2.6 2026-05-24: Codex CLI 통합 ...` |
| A-8 | R-3 linux.sh 코드 본문 무변경 + 변경이력 v1.1 | Pass | `bash -n scripts/install/linux.sh` 통과. `scripts/install/linux.sh:20` v1.1 행 존재. 코드 본문(L22 이하) 무변경 |
| A-9 | R-4 windows.ps1 codex 분기 3개 존재 | Pass | Register-Bootstrapper `L826-829`, Install-OpalMcp `L1186-1201`, Install-PlatformAgents `L1315-1318` 확인 |
| A-10 | R-5 opal-model-mapping.md Codex 컬럼 + 변경이력 v1.2 | Pass | 4컬럼(Claude/Gemini/OpenAI/Codex) + 3행 확인. `opal/core/references/opal-model-mapping.md:84` v1.2 행 존재 |
| A-11 | R-6 AGENT.md "Codex — 자동 삽입 스킵" 단락 + v2.8 | Pass | `opal/core/AGENT.md:280` 단락 존재. `L328` v2.8 행 존재. 사유(글로벌 자동 로드)와 M-2 결정 일치 |
| A-12 | R-7 PROJECT.md 플랫폼 독립성 문장 "Codex" 등장 | Pass | `docs/PROJECT.md:17` "Claude Code, Cursor, Gemini, Codex 등" 확인 |

> **R-1 AC 표현 불일치 (Info)**: TASK.md R-1 AC에 "마커 블록(`# === OPAL START ===`/`# === OPAL END ===`)을 포함하며"라고 기술되어 있으나, 실제 SSOT 파일(codex-bootstrap.md)에는 마커가 없다. 이는 claude-bootstrap.md/gemini-bootstrap.md와 동일한 패턴이며(두 파일도 마커 없음), 마커는 `install_opal_section()` 실행 시 타겟 파일에 삽입된다. TASK.md AC 문구 자체가 부정확하게 작성된 것으로 구현은 올바르다.

### B. 일관성 테스트 (§5.2 — 5항목)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| B-1 | 모델 매핑 SSOT 3곳 동기화 | Pass | opal-model-mapping.md / install-mac.sh:553 / windows.ps1:1317 → 3곳 모두 light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max 동일 |
| B-2 | 마커 블록 내용 3개 파일 문자 동일 | Pass | sed 추출 결과 codex/claude/gemini 코드블록 내부 본문 7줄 완전 일치 |
| B-3 | 자동 삽입 정책 동기화 | Pass | `opal/core/AGENT.md:282-284` 사유(글로벌 자동 로드)와 PLAN.md §M-2 결정 근거 일치 |
| B-4 | 함수 시그니처 일관성 | Pass | install_codex_agents() — 인자 없음, `~/.opal/agents` 부재 시 `warn ... return` 패턴 동일. `scripts/install-mac.sh:661-670` vs 595-602(claude)/617-625(cursor)/639-648(gemini) |
| B-5 | MCP scope_flag 빈 문자열 처리 | Pass | `install_mcp_cli "$bin" "" "$name"` → `$scope_flag` unquoted 사용 시 빈 문자열 = 인자 0개 (word splitting 확인). `scripts/install-mac.sh:1214` |

### C. 문서 품질 (§5.3 — 5항목)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| C-1 | 한국어 본문 + 영어 코드/필드명 | Pass | 전체 변경 파일 검토 — 본문 한국어, 코드/필드명 영어 준수 |
| C-2 | kebab-case 파일/폴더 네이밍 | Pass | codex-bootstrap.md (kebab-case), install_codex_agents (snake_case 함수명 패턴 동일) |
| C-3 | 변경이력 표 포맷 SSOT 동일 | Pass | codex-bootstrap.md / opal-model-mapping.md / AGENT.md / linux.sh / install-mac.sh / windows.ps1 모두 기존 변경이력 포맷 준수 |
| C-4 | §3.3 인라인 인용 — M-1~M-6 URL/경로:줄 | Pass | PLAN.md §2 M-1~M-6 모두 URL 인용 또는 백틱 경로:줄번호 부착 확인 |
| C-5 | [MUST] 인용 — Codex sub-agent 필수 3필드 | Pass | PLAN.md §3.3 U-1 `[MUST] [Subagents — Codex](https://developers.openai.com/codex/subagents)` 포맷 확인 |

### D. 코딩 원칙 준수

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| D-1 | 사변적 추가 없음 (범위 외 기능 추가 금지) | Pass | Codex plugin 등록 등 범위 외 기능 없음. 변경 파일 12개 모두 PLAN.md §3.1 변경 계획 범위 내 |
| D-2 | 인접 코드 개선 없음 (Claude/Cursor/Gemini 기존 통합 미수정) | Pass | install_claude_agents/install_cursor_agents/install_gemini_agents 미수정 확인. emit_platform_agent_adapter에 codex 행 추가만 수행 |
| D-3 | 불가능 시나리오 방어 코드 없음 | Pass | codex CLI 미설치 시 warn+return (graceful skip) — 발생 가능한 정상 케이스 |
| D-4 | 변경이력 6개 파일 모두 추가 | Pass | codex-bootstrap.md(v1.0) / opal-model-mapping.md(v1.2) / AGENT.md(v2.8) / install-mac.sh(v2.6) / linux.sh(v1.1) / windows.ps1(v1.8.0) 모두 확인 |
| D-5 | PLAN 범위만 변경 | Pass | PLAN.md §3.1 N-1(1개) + U-1~U-7(7개) = 8개 파일 + PLAN.md 자체 + 4개 mcps/*.json = 12개. 추가 변경 파일 없음 |

### E. 잔존 리스크 검증

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| E-1 | windows.ps1 TOML 직렬화 — PowerShell 백슬래시 escape | Warning | `scripts/install/windows.ps1:1349,1351`: `-replace '\\', '\\'`는 PowerShell 정규식 치환에서 `\` → `\` (무효). Python install-mac.sh의 `toml_escape`가 `s.replace('\\', '\\\\')` 으로 올바르게 처리하는 것과 불일치. 단, TOML triple-quoted basic string 내부에서 `\` 는 유효 TOML이지만 TOML spec 상 `\`로 시작하는 escape sequence가 잘못된 경우 파싱 오류 가능. 실 환경 검증은 별도 Windows 세션 필요 (EXECUTE 워커 리스크 R-T2 명시 반영) |

---

## 3. TASK 요구사항 매핑 (R-1~R-8) — 실제 EXECUTE 산출물과 정합성

| TASK 요구사항 | AC | 실제 산출물 | 충족 여부 |
|--------------|-----|------------|----------|
| R-1 codex-bootstrap.md 신규 작성 | 파일 존재 + 마커 내용 2줄 + 변경이력 v1.0 | `opal/bootstrapper/codex-bootstrap.md` 생성. 코드블록 내 2줄 명령. v1.0 행 존재 | Pass |
| R-2 install-mac.sh Codex 통합 | (a) codex 분기 + graceful skip (b) mcps platforms에 codex (c) MODEL_MAP codex 행 (d) 변경이력 v2.6 | 모두 확인 | Pass |
| R-3 linux.sh Codex 분기 | 변경이력 v1.1 + 위임 상속 | `scripts/install/linux.sh:20` v1.1 행. exec 위임으로 자동 상속 | Pass |
| R-4 windows.ps1 Codex 분기 | Register-Bootstrapper / Install-OpalMcp / Install-PlatformAgents codex 분기 | 3개 분기 모두 존재. 변경이력 v1.8.0 | Pass |
| R-5 opal-model-mapping.md codex 컬럼 | §2 Codex 컬럼 + 3행 + 변경이력 v1.2 | Codex 컬럼(gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max) + v1.2 행 | Pass |
| R-6 AGENT.md Codex 스킵 단락 + v2.8 | "Codex — 자동 삽입 스킵" 단락 + 변경이력 v2.8 | `opal/core/AGENT.md:280`, `L328` 확인 | Pass |
| R-7 PROJECT.md 플랫폼 독립성 Codex | 플랫폼 독립성 문장에 Codex 등장 | `docs/PROJECT.md:17` 확인 | Pass |
| R-8 변경이력 누락 금지 | 수정된 모든 문서에 변경이력 행 추가 | 6개 파일 모두 추가 (codex-bootstrap.md/opal-model-mapping.md/AGENT.md/install-mac.sh/linux.sh/windows.ps1) | Pass |

---

## 4. 일관성 검증 결과 — 모델 매핑·마커·함수 시그니처·MCP 스코프

**모델 매핑 3곳 동기화**: 완전 일치 확인.

```
opal-model-mapping.md: light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max
install-mac.sh:553:    'codex': {'light': 'gpt-5-mini', 'standard': 'gpt-5-codex', 'advanced': 'gpt-5.1-codex-max'}
windows.ps1:1317:      ModelMap = @{ light = 'gpt-5-mini'; standard = 'gpt-5-codex'; advanced = 'gpt-5.1-codex-max' }
```

**마커 블록 본문 3파일 동일**: codex/claude/gemini 코드블록 내부 7줄 완전 일치 확인.

**함수 시그니처 일관성**: `install_codex_agents()` — 인자 없음, `~/.opal/agents` 부재 시 `warn "~/.opal/agents 부재 — Codex 어댑터 스킵"; return` 패턴. claude/cursor/gemini 동일.

**MCP scope_flag**: `install_mcp_cli "$bin" "" "$name"` — 빈 문자열 unquoted 전달 시 word splitting으로 인자 미주입 확인. TOML 포맷 분기 처리 정상.

---

## 5. 코딩 원칙 준수

`opal/core/references/harness/coding-principles.md` §4 외과적 변경 + §5 QA Gate 기준 검증:

- **PLAN.md 범위 내 파일만 변경**: 12개 파일 모두 PLAN.md §3.1 N-1/U-1~U-7 범위 내. 범위 외 파일 수정 없음.
- **인접 코드 미개선**: install_claude_agents/cursor/gemini 기존 함수 무변경. emit_platform_agent_adapter에 codex 행만 추가.
- **사변적 추가 없음**: Codex plugin 등록, config.toml 추가 키 등 범위 외 기능 없음.
- **불가능 케이스 방어 없음**: graceful skip은 실제 발생 가능한 CLI 미설치 케이스 대응.

---

## 6. 발견사항

### 6.1 Blocker

없음.

### 6.2 Major

없음.

### 6.3 Minor

**M-1. windows.ps1 TOML 백슬래시 이스케이프 무효 패턴**

- 파일: `scripts/install/windows.ps1:1349,1351`
- 패턴: `$escapedBody = $fm.Body -replace '\\', '\\'` — PowerShell `-replace`는 정규식 치환. 치환 문자열 `'\\'`는 literal `\` (PowerShell은 치환 문자열에서 `\`를 문자 그대로 해석). 결과: `\` → `\` (무효).
- Python 대응: `scripts/install-mac.sh` `toml_escape` 함수는 `s.replace('\\', '\\\\')` — `\` → `\\` 올바르게 처리.
- 위험: AGENT.md 본문에 `\` 포함 시 TOML multi-line basic string 내부에서 `\x`, `\n`, `\"` 등 유효하지 않은 escape sequence가 발생하여 TOML 파싱 오류 가능.
- 처리: EXECUTE 워커가 리스크 R-T2로 명시. 별도 Windows 실 환경 검증 세션 권고. 현재 `~/.opal/agents/` 내 AGENT.md에 `\` 없으면 영향 없음.

**M-2. R-1 AC 표현 불일치 (Info)**

- TASK.md R-1 AC에 "마커 블록(`# === OPAL START ===`/`# === OPAL END ===`)을 포함하며"라고 기술.
- 실제 codex-bootstrap.md에는 마커 없음 — claude-bootstrap.md/gemini-bootstrap.md와 동일 패턴.
- SSOT 파일에는 마커가 없고 install_opal_section()이 타겟에 삽입하는 구조가 올바름.
- 구현은 정확하며 AC 문구 자체가 부정확. 다음 태스크에서 TASK.md 표현 정정 권고.

---

## 7. 체크리스트 갱신 결과

PLAN.md §5 QA 체크리스트는 EXECUTE 워커가 이미 전체 [x]로 갱신하였으며, 본 QA 검증 결과 모든 항목이 실제 산출물과 일치함을 확인하였다. 갱신 필요 항목 없음.

- §5.1 기능 테스트: 10/10 검증 통과 (체크박스 [x] 유지)
- §5.2 일관성 테스트: 5/5 검증 통과 (체크박스 [x] 유지)
- §5.3 문서 품질: 5/5 검증 통과 (체크박스 [x] 유지)

---

## 8. 권고

**CONDITIONAL_PASS — PM Gate 진입 권고 (단, Minor M-1 보강 권고)**

핵심 기능 요구사항(R-1~R-8) 전체 충족, 일관성·문서 품질 기준 충족. Blocker/Major 없음.

다음 보강 후 PM Gate 진입 권고:
1. (권고) `scripts/install/windows.ps1:1349,1351` 백슬래시 escape 패턴 수정 — `-replace '\\', '\\'` → `-replace '\\', '\\\\'`. 현재 `~/.opal/agents/` AGENT.md에 `\` 없으면 즉시 영향 없으나 향후 방어.
2. (참고) TASK.md R-1 AC 표현 정정 — 다음 태스크 기회에 반영.

---

## 9. 잔존 리스크 (EXECUTE 워커 보고 사항 검토)

**windows.ps1 TOML 직렬화 — Windows 실 환경 검증 별도 세션 필요 판정: 유지**

정적 분석 결과:
- PowerShell `developer_instructions = '"`"`"`r`n$escapedBody`r`n`"`"`"`r`n'` → `developer_instructions = """<CRLF><body><CRLF>"""` (TOML multi-line basic string, 유효 형식)
- `"` 이스케이프 (`-replace '"', '\"'`): 정상 (`"` → `\"`)
- `\` 이스케이프 (`-replace '\\', '\\'`): 무효 (`\` → `\` 변화 없음) — **Minor 발견**

TOML spec 상 multi-line basic string 내 `\` 단독 사용은 유효한 escape sequence `\n`, `\t`, `\\`, `\"` 등의 시작으로 해석됨. 현재 AGENT.md 본문에 백슬래시가 없으면 영향 없으나, 실 Windows PowerShell 5.1/7 환경에서 파싱 테스트는 별도 세션에서 수행해야 한다.

**결론**: EXECUTE 워커 보고 "별도 QA 세션 필요" 판단 유지. N/A(실 환경 미확보).

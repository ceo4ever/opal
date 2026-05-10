# PLAN: OPAL 보안 강화 — SECURITY.md 신설 + High 4 + Medium 핵심 fix

> 작성일: 2026-05-10 | 입력: TASK.md + GC-SECURITY-260510-2007.md + 캡틴 결정 (TASK.md §확정된 설계 방향 §1~§10)
> 출력: PLAN.md (본 문서)
> 작업 모드: semi-agentic | 적용 스킬: opp | 영역: Framework 단일

---

## §0. 캡틴 결정 SSOT (변경 금지)

본 PLAN은 TASK.md §확정된 설계 방향 §1~§10을 SSOT로 그대로 승계한다. PLAN 작성 중 §1~§10 결정 사항을 임의 변경하지 않는다.

| # | 결정 항목 | 핵심 결정 | 인용 |
|---|---------|---------|------|
| 0.1 | 범위 | High 4 + Medium 핵심(GC-006/007/010) + SECURITY.md 신설 / Low/일부 Medium은 후속 분리 | TASK.md §확정된 설계 방향 §1, §7, §8 |
| 0.2 | SECURITY.md 6 섹션 | 위협 모델 / install 무결성 / MCP 신뢰 경계 / fetch 신뢰 / 의존성 핀 / ReDoS 방어 | TASK.md §2 + GC-SECURITY §5 |
| 0.3 | install 무결성 | release tag(v*) sha256sums.txt 부재 시 동의 prompt 또는 `OPAL_ALLOW_UNVERIFIED=1`. 비대화형 거부. main UNVERIFIED 경고 | TASK.md §3, R-2 |
| 0.4 | fetch 신뢰 | registry v2.1 (`commit_sha` 신설). Unknown 라이선스 두 번째 확인 | TASK.md §4, R-3 |
| 0.5 | MCP spawn | command 화이트리스트(`npx`/`npm`/`node`/`python3`). fork repo banner 경고 + 동의 | TASK.md §5, R-4 |
| 0.6 | ReDoS | skill-registry trigger 휴리스틱 + 입력 길이 256자 + path 정규화(GC-013 보너스) | TASK.md §6, R-5 |
| 0.7 | mac/Windows 동등 처리 | 모든 보안 강화는 양 OS 동시 적용 | TASK.md §9 |
| 0.8 | 회귀 검증 의무 | install / `claude mcp list` / `//pdf` 매칭 / opal-cli doctor / opal-cli uninstall — mac+Windows 양쪽 검증 | TASK.md §10, R-9 |

[MUST] `opal-pilot-project` 워커 PLAN 작성 행동 규칙: "TASK.md §확정된 설계 방향 §1~§10은 변경 금지". PM이 디스패치 프롬프트에서 명시한 SSOT 제약을 그대로 승계한다.

---

## §1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | TASK.md (본 태스크) | `tasks/144-260510-opp-security-hardening/TASK.md` | 요구사항 SSOT (R-1~R-9 + 캡틴 결정 §1~§10 + 미확정 사항 P-D-1~P-D-8) |
| D-2 | 보고 | GC-SECURITY 진단 보고서 | `tasks/144-260510-opp-security-hardening/GC-SECURITY-260510-2007.md` | 14건 발견 사항 (High 4 / Medium 6 / Low 3 / Info 1) + §5 SECURITY.md 골격 입력 자료 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·Guards·커밋·플랫폼 분기·@header 규칙 |
| D-4 | 설계 | PROJECT.md | `docs/PROJECT.md` | Framework 단일 영역 → opal-task-agent 폴백 / 외부 의존 서비스 (MCP/Python/Node) |
| D-5 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 외부 의존 서비스 §MCP 서버 / 배포 채널 §GitHub Releases |
| D-6 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷·[MUST] 토큰·decision_required 계약 |
| D-7 | 설계 | reporting-template.md | `opal/core/references/harness/reporting-template.md` | §8.1 PLAN 완료 보고 5요소 표준 |
| D-8 | 컨텍스트 | 142 DONE.md | `tasks/142-260510-opp-community-skills-fetch-migration/DONE.md` | community-skills-registry v2 + null source_repo 7건 (R-3 컨텍스트) |
| D-9 | 컨텍스트 | 141 DONE.md | `tasks/141-260510-opp-readme-mit-license-p0/DONE.md` | docs/JSON config 변경이력 면제 선례 (SECURITY.md / playwright.json 면제 판단) |
| D-10 | 소스 | scripts/install.sh | `scripts/install.sh` | mac/Linux one-liner 진입점 — verify_checksum (L202-256) 무조건 skip 위치 |
| D-11 | 소스 | scripts/install.ps1 | `scripts/install.ps1` | Windows one-liner 진입점 — Verify-Checksum (L162-211) 무조건 skip 위치 |
| D-12 | 소스 | scripts/install/windows.ps1 | `scripts/install/windows.ps1` | Windows 본체 — clean_dirs Remove-Item (L411-420) + Install-OpalMcp (L1080-1130) |
| D-13 | 소스 | scripts/install-mac.sh | `scripts/install-mac.sh` | mac 본체 — clean_dirs (L730-739) + install_mcp_cli (L1032-1046) |
| D-14 | 소스 | opal-cli/lib/update.sh | `opal/tools/opal-cli/lib/update.sh` | 업데이트 시 체크섬 검증 (L163-183) — install.sh와 동일 패턴 적용 필요 |
| D-15 | 소스 | opal-cli/lib/uninstall.sh | `opal/tools/opal-cli/lib/uninstall.sh` | rm -rf "$opal_home" (L66-67) — OPAL_HOME 가드 추가 위치 |
| D-16 | 소스 | opal-cli/lib/mcp.sh | `opal/tools/opal-cli/lib/mcp.sh` | _mcp_add (L101-206) — command 화이트리스트 추가 위치 |
| D-17 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | matchByTriggers (L101-122) ReDoS / resolveFirstPath (L124-135) path 정규화 |
| D-18 | 소스 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | §6 자동 fetch 흐름 동의 prompt (L127-143) |
| D-19 | 소스 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | v2 → v2.1 (`commit_sha` 신설) + Unknown 라이선스 7건 위치 |
| D-20 | 소스 | mcps/playwright.json | `opal/core/mcps/playwright.json` | `@latest` 핀 (R-6) + `--output-dir /tmp/playwright-mcp` (R-7) |
| D-21 | 소스 | mcps/shadcn.json | `opal/core/mcps/shadcn.json` | `@latest` 핀 (R-6) |
| D-22 | 소스 | mcps/context7.json | `opal/core/mcps/context7.json` | `@latest` 핀 (R-6) |
| D-23 | 소스 | mcps/sequential-thinking.json | `opal/core/mcps/sequential-thinking.json` | 버전 미지정 (R-6) |
| D-24 | 외부 | OWASP Top 10 (2021) | https://owasp.org/Top10/ | A05/A06/A08 위반 기준 — SECURITY.md §위협 모델 인용 |
| D-25 | 외부 | CWE Top 25 / SANS Top 25 | https://cwe.mitre.org/top25/ | CWE-22/78/94/377/829/1333 위반 기준 — SECURITY.md §위협 모델 인용 |
| D-26 | 외부 | npm registry (4 패키지) | `npm view {pkg} version` | R-6 마이너 핀 결정 — playwright/mcp@0.0.75 / shadcn@4.7 / context7-mcp@2.2 / server-sequential-thinking@2025.12.18 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부` / `보고` / `컨텍스트`.

### 적용 [MUST] 인용 (재해석 금지 제약)

- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."
- [MUST] `docs/CONVENTIONS.md` §Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다."
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 = 한국어(기술 용어는 영어 병기) / 코드/변수/필드명 = English / 파일/폴더 이름 = English, kebab-case (Python 파일은 snake_case)."
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다."
- [MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §제약 조건: "기존 사용자 호환성 유지 — 정상 사용자(ceo4ever/opal에서 release tag 설치)는 변화 없어야. 즉 fork 또는 main 설치만 새 prompt/거부 동작."
- [MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §제약 조건: "mac/Windows 동등 처리 — 모든 보안 강화는 양 OS 동등 적용."
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `docs/SECURITY.md` | 보안 모델 SSOT (신규) | **Y** (신규) | - |
| `scripts/install.sh` | mac/Linux one-liner 진입 (343 lines) | **Y** | `scripts/install.sh:202-256` (verify_checksum 무조건 skip) |
| `scripts/install.ps1` | Windows one-liner 진입 (319 lines) | **Y** | `scripts/install.ps1:162-211` (Verify-Checksum 무조건 skip) |
| `opal/tools/opal-cli/lib/update.sh` | opal-cli update (249 lines) | **Y** | `opal/tools/opal-cli/lib/update.sh:163-183` (sha256 fetch 실패 시 skip) |
| `scripts/install/windows.ps1` | Windows 본체 (1325 lines) | **Y** | `scripts/install/windows.ps1:411-420` (clean_dirs) + `:1080-1130` (Install-OpalMcp) + `:411-420` (Remove-Item) |
| `scripts/install-mac.sh` | mac 본체 (1285 lines) | **Y** | `scripts/install-mac.sh:730-739` (clean_dirs) + `:1032-1046` (install_mcp_cli) |
| `opal/tools/opal-cli/lib/uninstall.sh` | uninstall (193 lines) | **Y** | `opal/tools/opal-cli/lib/uninstall.sh:47, 66-67` (rm -rf "$opal_home") |
| `opal/tools/opal-cli/lib/mcp.sh` | mcp 서브커맨드 (316 lines) | **Y** | `opal/tools/opal-cli/lib/mcp.sh:101-206` (_mcp_add) |
| `opal/tools/skill-registry/skill-registry.js` | 스킬 레지스트리 CLI (399 lines) | **Y** | `opal/tools/skill-registry/skill-registry.js:101-135` (matchByTriggers + resolveFirstPath) |
| `opal/skills/opal-skill-manager/SKILL.md` | 스킬 관리 스킬 (148 lines) | **Y** | `opal/skills/opal-skill-manager/SKILL.md:60-72, 127-143` (fetch 흐름) |
| `opal/core/references/community-skills-registry.json` | 커뮤니티 스킬 레지스트리 (51 lines) | **Y** | `opal/core/references/community-skills-registry.json:1-50` (v2 → v2.1, Unknown 7건) |
| `opal/core/mcps/playwright.json` | Playwright MCP 정의 (10 lines) | **Y** | `opal/core/mcps/playwright.json:7` (`@latest` + `/tmp/playwright-mcp`) |
| `opal/core/mcps/shadcn.json` | shadcn MCP 정의 (10 lines) | **Y** | `opal/core/mcps/shadcn.json:7` (`@latest`) |
| `opal/core/mcps/context7.json` | context7 MCP 정의 (10 lines) | **Y** | `opal/core/mcps/context7.json:7` (`@latest`) |
| `opal/core/mcps/sequential-thinking.json` | Sequential Thinking MCP 정의 (10 lines) | **Y** | `opal/core/mcps/sequential-thinking.json:7` (버전 미고정) |

### 현재 상태

1. **install 무결성**: `install.sh:226-228` / `install.ps1:188-190` / `update.sh:181-182` 모두 `sha256sums.txt` fetch 실패 시 `warn` 로그만 출력하고 통과. release tag(v*)인지 main인지 구분 없음. 비대화형 모드(curl|bash) 가드 없음.
2. **community-skills-registry v2**: `$schema: opal-community-skills-registry-v2`, `version: 2.0.0`. `source_repo: null` 7건 (google-labs-code/design-md/enhance-prompt/react-components/remotion/stitch-loop + trailofbits/modern-python + getsentry/code-review). `license: "Unknown"` 12건 (google-labs-code 5 + vercel-labs 5 + trailofbits 1 + getsentry 1).
3. **MCP spawn**: `install-mac.sh:1041-1046` install_mcp_cli + `windows.ps1:1080-1130` Install-OpalMcp + `mcp.sh:155-198` _mcp_add 모두 `command`/`args`를 검증 없이 spawn. `OPAL_REPO != ceo4ever/opal` 분기 없음.
4. **MCP `@latest`**: 4개 mcps/*.json 중 3개 (`shadcn.json`/`playwright.json`/`context7.json`)가 `@latest` 사용. `sequential-thinking.json`은 버전 미고정.
5. **playwright /tmp**: `playwright.json:7` `--output-dir /tmp/playwright-mcp` (mac/Linux 영향, Windows는 `$env:TEMP`로 v0.3.13에서 치환됨).
6. **ReDoS**: `skill-registry.js:101-122` matchByTriggers — 정규식 `try/catch`만 있음, 길이/`.*`/nested quantifier 검사 없음. 입력 길이 제한 없음. `resolveFirstPath:124-135` `~` 치환 후 `path.resolve` 미수행 → traversal 가능.
7. **OPAL_HOME 가드**: `uninstall.sh:67` `rm -rf "$opal_home"` (가드 없음). `install-mac.sh:736` clean_dirs 루프 (가드 없음). `windows.ps1:418` Remove-Item (가드 없음). `OPAL_HOME=/`로 호출 시 `rm -rf /skills /agents ...`로 시스템 손상 가능.
8. **opal-skill-manager SKILL.md §6**: 동의 prompt가 `라이선스: {license}`만 표시. Unknown 빨간 경고 / 두 번째 확인 / commit_sha 검증 없음.

### 영향 범위

- **install 흐름**: mac/Linux/Windows one-liner + opal-cli update — 정상 사용자(ceo4ever/opal release tag)는 변화 없어야 함 (sha256sums.txt 정상 fetch → 검증 통과). fork repo / main 브랜치 / sha256sums.txt 부재 시에만 새 prompt/거부.
- **MCP 흐름**: mac/Windows 본체 + opal-cli mcp add — 화이트리스트 외 command가 ceo4ever/opal mcps/*.json에 들어있지 않으므로 정상 사용자 영향 없음. fork repo 사용자만 banner 경고.
- **community-skills fetch**: opal-skill-manager 동의 prompt 강화 — 기존 사용자도 prompt 형식 변경 (Unknown 빨간 경고 추가). 기존 설치 스킬에는 영향 없음.
- **ReDoS / path 정규화**: skill-registry.js 변경은 trigger 매칭(`//pdf` 등) + `match` 명령 응답 형식. 정상 패턴은 영향 없음, 위험 패턴(google-labs-code/react-components의 `(?i)(stitch.*react|react\s*component.*stitch)`는 `.*` 2회 — 길이/임계값 따라 reject 가능 → P-D-7 결정 영향).
- **OPAL_HOME 가드**: 표준 설치(`$HOME/.opal`)는 영향 없음. `OPAL_HOME` 명시 사용자(현재 사용 사례 미확인)만 영향. `OPAL_HOME_OVERRIDE=1` 옵트인 제공.
- **MCP `@latest` 핀**: 사용자 install/update 시 `claude mcp list`에 새 버전 표시. 기존 사용자가 `update` 시 새 버전으로 갱신.
- **SECURITY.md 신설**: 비기능 영향 — opal-pilot-gc baseline + 사용자 신뢰 모델 명문화.

---

## §2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `docs/SECURITY.md` | OPAL 보안 모델 SSOT — 6 섹션 골격 (위협 모델 / install 무결성 / MCP 신뢰 경계 / fetch 신뢰 / 의존성 핀 / ReDoS 방어) | TASK.md R-1 + GC-SECURITY-260510-2007.md §5 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `scripts/install.sh` | release tag(v*) sha256sums.txt 부재 시 `OPAL_ALLOW_UNVERIFIED=1` 검사 + 비대화형(stdin pipe) 거부 + main UNVERIFIED banner | R-2 / `scripts/install.sh:206-256` |
| M-2 | `scripts/install.ps1` | release tag sha256sums.txt 부재 시 `$env:OPAL_ALLOW_UNVERIFIED -eq '1'` 검사 + 비대화형 거부 + main UNVERIFIED banner | R-2 / `scripts/install.ps1:162-211` |
| M-3 | `opal/tools/opal-cli/lib/update.sh` | release tag sha256sums.txt 부재 시 `OPAL_ALLOW_UNVERIFIED=1` 검사 + main 명시 시 UNVERIFIED banner | R-2 / `opal/tools/opal-cli/lib/update.sh:163-183` |
| M-4 | `opal/core/references/community-skills-registry.json` | `$schema: opal-community-skills-registry-v2.1` + `version: 2.1.0` + `commit_sha` 옵션 필드 추가 (신규 항목 옵션, 기존 항목 미작성 허용) | R-3 / `opal/core/references/community-skills-registry.json:1-50` |
| M-5 | `opal/skills/opal-skill-manager/SKILL.md` | §6 동의 prompt에 Unknown 라이선스 빨간 경고 + 두 번째 확인 + commit_sha 정보 노출 | R-3 / `opal/skills/opal-skill-manager/SKILL.md:127-143` |
| M-6 | `scripts/install-mac.sh` | `install_mcp_cli`에 command 화이트리스트(`npx`/`npm`/`node`/`python3`) + `OPAL_REPO != ceo4ever/opal` fork banner + `clean_dirs` 루프에 OPAL_HOME 가드 | R-4 + R-8 / `scripts/install-mac.sh:730-739, 1032-1046` |
| M-7 | `scripts/install/windows.ps1` | `Install-OpalMcp`에 command 화이트리스트 + fork banner + `clean_dirs` Remove-Item 가드 | R-4 + R-8 / `scripts/install/windows.ps1:411-420, 1080-1130` |
| M-8 | `opal/tools/opal-cli/lib/mcp.sh` | `_mcp_add`에 command 화이트리스트 검증 | R-4 / `opal/tools/opal-cli/lib/mcp.sh:101-206` |
| M-9 | `opal/tools/opal-cli/lib/uninstall.sh` | `rm -rf "$opal_home"` 직전에 `[[ "$opal_home" == "$HOME/.opal" ]] || error` 가드 + `OPAL_HOME_OVERRIDE=1` 옵트인 | R-8 / `opal/tools/opal-cli/lib/uninstall.sh:47, 66-67` |
| M-10 | `opal/tools/skill-registry/skill-registry.js` | `matchByTriggers` ReDoS 휴리스틱 (길이 100자 / `.*` 2회 / nested quantifier reject) + 입력 길이 제한 256자 + `validate`에 ReDoS 분석 + `resolveFirstPath`에 `path.resolve` + homedir 가드 | R-5 + GC-013 보너스 / `opal/tools/skill-registry/skill-registry.js:101-135, 305-316` |
| M-11 | `opal/core/mcps/shadcn.json` | `shadcn@latest` → `shadcn@4.x` (마이너 핀) | R-6 / `opal/core/mcps/shadcn.json:7` + npm registry shadcn@4.7.0 |
| M-12 | `opal/core/mcps/playwright.json` | `@playwright/mcp@latest` → `@playwright/mcp@0.0.x` 마이너 핀 + `--output-dir /tmp/playwright-mcp` → `~/.opal/cache/playwright-mcp` | R-6 + R-7 / `opal/core/mcps/playwright.json:7` + npm registry @playwright/mcp@0.0.75 |
| M-13 | `opal/core/mcps/context7.json` | `@upstash/context7-mcp@latest` → `@upstash/context7-mcp@2.x` (마이너 핀) | R-6 / `opal/core/mcps/context7.json:7` + npm registry @upstash/context7-mcp@2.2.4 |
| M-14 | `opal/core/mcps/sequential-thinking.json` | `@modelcontextprotocol/server-sequential-thinking` (버전 미고정) → `@modelcontextprotocol/server-sequential-thinking@2025.12.x` (캘린더 핀) | R-6 / `opal/core/mcps/sequential-thinking.json:7` + npm registry @modelcontextprotocol/server-sequential-thinking@2025.12.18 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | 본 태스크는 추가/수정만 — 삭제 없음 |

### 구현 순서

의존성 원칙: **레지스트리/스키마 → 도구 → install 본체 → SECURITY.md (요약 인용)** 순. `OPAL_HOME` 가드는 install 본체와 함께 변경. SECURITY.md는 본체 변경의 결정 사항을 인용하므로 마지막.

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | MCP 4개 JSON 핀 + playwright 경로 변경 | mcps/{shadcn,playwright,context7,sequential-thinking}.json | 낮음 |
| 2 | community-skills-registry v2.1 + opal-skill-manager SKILL.md prompt 강화 | community-skills-registry.json + opal-skill-manager/SKILL.md | 중간 |
| 3 | skill-registry.js ReDoS + path 정규화 | skill-registry.js | 중간 |
| 4 | opal-cli/lib/uninstall.sh OPAL_HOME 가드 | uninstall.sh | 낮음 |
| 5 | opal-cli/lib/mcp.sh 화이트리스트 | mcp.sh | 중간 |
| 6 | install-mac.sh: install_mcp_cli 화이트리스트 + fork banner + clean_dirs 가드 | install-mac.sh | 중간 |
| 7 | install/windows.ps1: Install-OpalMcp 화이트리스트 + fork banner + Remove-Item 가드 | install/windows.ps1 | 중간 |
| 8 | install.sh: verify_checksum prompt + 비대화형 거부 + main banner | install.sh | 중간 |
| 9 | install.ps1: Verify-Checksum prompt + 비대화형 거부 + main banner | install.ps1 | 중간 |
| 10 | opal-cli/lib/update.sh: 동일 로직 | update.sh | 중간 |
| 11 | docs/SECURITY.md 신설 (6 섹션) | docs/SECURITY.md | 중간 |
| 12 | 회귀 검증 (install/MCP/// 매칭/doctor/uninstall 흐름) | (런타임 검증) | 중간 |

### 핵심 설계

각 파일별 변경 내용을 설계 결정 + 인용으로 명시한다. 코드 작성은 EXECUTE 단계에서 수행 (Guards 준수).

#### N-1: `docs/SECURITY.md` 신설 — 6 섹션 SSOT

(→ D-2 §5 권장 SECURITY.md 골격)

```markdown
# OPAL 보안 모델 (SECURITY.md)

> 작성일: 2026-05-10 | 적용 버전: v0.4.x+
> 목적: OPAL 프레임워크의 보안 baseline 명문화 — opal-pilot-gc 비교 baseline + 사용자 신뢰 모델 SSOT

## §1 위협 모델
- 공개 OSS 프레임워크 / curl-pipe-bash 신뢰 모델 / fork 가능성 / third-party skill supply chain
- 적용 표준: OWASP Top 10 (2021) — A05/A06/A08 / CWE Top 25 — CWE-22/78/94/377/829/1333

## §2 install 무결성 (GC-DP-001/003)
- release tag(v*) 자산은 sha256sums.txt + actions/attest-build-provenance@v2 로 무결성 확보
- main 브랜치 설치는 UNVERIFIED — `OPAL_ALLOW_UNVERIFIED=1` 명시 옵트인 또는 사용자 동의 prompt
- 비대화형(curl|bash, OPAL_AUTO_INSTALL=1) 모드에서 sha256sums.txt 부재 시 기본 거부

## §3 MCP 등록 신뢰 경계 (GC-DP-002/005)
- command 화이트리스트: `npx` / `npm` / `node` / `python3` — 그 외 reject
- `OPAL_REPO != ceo4ever/opal` (fork) 설치 시 banner 경고 + 명시 동의
- `version_pinned: "x.y.z"` 신규 MCP 등록 정책 (PLAN의 R-6 결정으로 4개 기존 MCP 모두 마이너 핀 적용)

## §4 third-party 스킬 fetch (GC-DP-004)
- registry v2.1: `commit_sha` 옵션 필드 신설
- `license: "Unknown"` 항목 빨간 경고 + 두 번째 확인 강제
- vercel-labs/skills 카탈로그 미등재(`source_repo: null`) 7건은 수동 설치 안내

## §5 의존성 핀
- MCP `@latest` 금지 — 마이너 핀 의무 (`x.y` 또는 `^x.y.z`)
- requirements.txt — `pip-compile`로 lock 생성 (별도 후속 태스크 GC-005)

## §6 ReDoS 방어
- skill-registry trigger 휴리스틱: 길이 100자 초과 / `.*` 2회 이상 / nested quantifier reject
- 입력 길이 제한 256자
- path 치환 후 `path.resolve` + homedir 가드 (CWE-22)
```

[MUST] `docs/SECURITY.md`는 docs 면제 (D-9 141 v0.3.15 선례) — 변경이력 표 미작성. 단, "작성일: 2026-05-10" + "적용 버전: v0.4.x+" 메타데이터로 추적성 확보.

#### M-1, M-2, M-3: install 무결성 강화 (R-2)

(→ D-1 R-2 + D-2 §3 GC-001 + D-10 D-11 D-14)

설계 결정:

1. **release tag(v*) sha256sums.txt 부재 시 분기**:
   - 비대화형 모드 (`! -t 0` stdin pipe / `OPAL_AUTO_INSTALL=1` env): 기본 **거부** — `error "sha256sums.txt 없음 — 비대화형 모드에서 거부 (release 자산 미생성). 옵트인: OPAL_ALLOW_UNVERIFIED=1 명시"`
   - 대화형 모드: prompt — `read -r -p "sha256sums.txt 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N]"` (디폴트 N)
   - `OPAL_ALLOW_UNVERIFIED=1` 명시: 모든 모드에서 통과 (UNVERIFIED 경고만)

2. **main 브랜치 설치**: stdout에 명확한 banner — `warn "[UNVERIFIED] main 브랜치 설치 — 무결성 검증 없음"`. release tag가 아니므로 sha256sums.txt 검사 자체 skip (이전 동작과 동일).

3. **정상 사용자 흐름 (회귀 0)**: ceo4ever/opal에서 release tag(v0.x.y) 설치 시 sha256sums.txt 정상 fetch → 검증 통과 → 새 prompt 미발동.

4. **PowerShell 분기**: install.ps1은 `$env:OPAL_ALLOW_UNVERIFIED` / `$env:OPAL_AUTO_INSTALL` 검사. `$Host.UI.RawUI` 미접근 환경(curl|iex)은 비대화형 간주.

5. **update.sh**: install.sh와 동일 패턴. main 명시 시(`opal-cli update --to main`)는 UNVERIFIED banner.

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §3: "비대화형 모드 기본 거부. main 브랜치 UNVERIFIED 경고."

#### M-4: community-skills-registry.json v2 → v2.1 (R-3 a)

(→ D-1 R-3 + D-19)

설계 결정:

1. **스키마 minor bump**:
   - `$schema: "opal-community-skills-registry-v2"` → `"opal-community-skills-registry-v2.1"`
   - `version: "2.0.0"` → `"2.1.0"`
   - `schema_notes` 갱신: "v2.1: commit_sha 옵션 필드 신설 — 검증 가능한 스킬만 채움. v2 호환 유지 (commit_sha 미작성 시 null로 간주)."

2. **`commit_sha` 옵션 필드**:
   - 위치: `source_repo` 다음 (각 항목 객체의 키 순서: `name` → `alias` → `description` → `triggers` → `source_repo` → `commit_sha` → `license`)
   - 값: `null` (옵션 — 본 태스크에서는 12개 Apache-2.0 anthropics + 1개 openai 항목에 한해 추후 채우는 것이 가능. 본 태스크는 필드 신설만 — 실제 commit_sha 값 채우기는 후속 별도 태스크)
   - **본 태스크 범위 (P-D-1 결정)**: anthropics 18건 모두 `commit_sha: null` 명시 추가 (필드 존재 보장). 다른 그룹은 미추가 (skill-registry.js validate가 옵션 필드로 인식).

3. **호환성**: `skill-registry.js validate`는 v2.1 스키마 인식 — `$schema === 'opal-community-skills-registry-v2.1'` 또는 `'opal-community-skills-registry-v2'` 모두 통과.

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §제약 조건: "142가 도입한 `community-skills-registry.json` v2를 v2.1로 minor bump (스키마 호환 유지)."

#### M-5: opal-skill-manager SKILL.md 동의 prompt 강화 (R-3 b)

(→ D-1 R-3 + D-18)

설계 결정 — §6 prompt 형식:

```markdown
이 스킬은 외부 스킬입니다.
- 출처: {source_repo}
- 라이선스: {license}{license == "Unknown" ? "  ⚠️ 라이선스 미확인 (Unknown License) / Unknown license — proceed at your own risk" : ""}
- commit SHA: {commit_sha || "미고정 (HEAD 가변)"}

다운로드해서 설치할까요? (Y/n)
```

- `license == "Unknown"` 시 **두 번째 확인** 추가 (P-D-3 영문+한글 병기):
  ```
  라이선스가 확인되지 않은 스킬입니다. 정말로 설치하시겠습니까?
  This skill has an unverified license. Are you sure you want to install? (y/N)
  ```
  - 디폴트 `N` (재해석 방지)

- §1 스킬 검색의 안내 메시지에도 "라이선스 미확인 시 빨간 경고 표시" 명시.

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §4: "Unknown 라이선스 두 번째 확인."

#### M-6, M-7, M-8: MCP spawn 신뢰 경계 (R-4)

(→ D-1 R-4 + D-2 §3 GC-003 + D-13 D-12 D-16)

설계 결정:

1. **command 화이트리스트** (3개 위치 동등 적용):
   - 허용 set: `{npx, npm, node, python3}` (절대경로 변종 `/usr/bin/python3` 등은 `basename` 후 검증)
   - bash:
     ```bash
     local cmd_basename
     cmd_basename="$(basename "$command")"
     case "$cmd_basename" in
         npx|npm|node|python3) ;;
         *) error "MCP command '$command' 화이트리스트 미통과 — npx/npm/node/python3만 허용"; return 1 ;;
     esac
     ```
   - PowerShell (Install-OpalMcp):
     ```powershell
     $allowedCmds = @('npx','npm','node','python3','python')
     $cmdBase = [IO.Path]::GetFileNameWithoutExtension($cfgWin.command)
     if ($allowedCmds -notcontains $cmdBase) {
         throw "[OPAL] MCP command '$($cfgWin.command)' 화이트리스트 미통과"
     }
     ```

2. **fork repo banner** (install 시작 시 한 번 — P-D-2 결정):
   - 트리거: `[[ "${OPAL_REPO:-ceo4ever/opal}" != "ceo4ever/opal" ]]`
   - bash:
     ```
     ════════════════════════════════════════════════════════
     ⚠️  FORK INSTALL — OPAL_REPO=$OPAL_REPO
     이 설치본은 OPAL 공식 저장소(ceo4ever/opal)가 아닙니다.
     MCP 서버 등록 항목을 직접 검토하세요.
     계속하시겠습니까? [y/N]
     ════════════════════════════════════════════════════════
     ```
   - 비대화형 모드(`OPAL_AUTO_INSTALL=1` 또는 `! -t 0`)에서는 거부 (단, `OPAL_ALLOW_FORK=1` 옵트인 시 통과).
   - PowerShell도 동일 메시지 + `Read-Host` (비대화형은 throw).

3. **mcp.sh `_mcp_add`** (opal-cli mcp 서브커맨드):
   - `command` 변수 추출 직후 화이트리스트 검증.
   - fork banner는 install 시작 시 한 번이면 충분하므로 mcp.sh에서는 추가하지 않음 (의존: install_mcp 호출 흐름이 banner를 이미 띄움). `opal-cli mcp add` 직접 호출 시에도 화이트리스트는 가드 역할.

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §5: "command 화이트리스트(`npx`/`npm`/`node`/`python3`). fork repo banner 경고."

#### M-9: opal-cli uninstall OPAL_HOME 가드 (R-8)

(→ D-1 R-8 + D-2 §3 GC-010 + D-15)

설계 결정 — `cmd_uninstall` L47 직후 + `rm -rf "$opal_home"` 직전 가드:

```bash
local opal_home="${OPAL_HOME:-$HOME/.opal}"
local opal_home_canon
opal_home_canon="$(cd "$opal_home" 2>/dev/null && pwd -P || echo "$opal_home")"
local default_canon
default_canon="$(cd "$HOME/.opal" 2>/dev/null && pwd -P || echo "$HOME/.opal")"

if [[ "$opal_home_canon" != "$default_canon" ]] && [[ "${OPAL_HOME_OVERRIDE:-}" != "1" ]]; then
    error "비표준 OPAL_HOME 거부: $opal_home (예상: $HOME/.opal). 옵트인: OPAL_HOME_OVERRIDE=1 명시"
    return 1
fi
```

- P-D-6 결정: `OPAL_HOME_OVERRIDE=1` 옵트인 환경 변수 추가 (CI/test 환경 호환).
- mac/Linux는 `pwd -P` 정규화. realpath 사용 시 GNU/BSD 호환성 문제 회피.
- `install-mac.sh:730-739` clean_dirs 루프에도 동일 가드 추가 (M-6에서 처리).
- PowerShell 동일: `[IO.Path]::GetFullPath($OpalHome)` ≠ `[IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.opal'))` 비교 (M-7에서 처리).

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §7: "GC-010 OPAL_HOME 가드 — `[[ "$opal_home" == "$HOME/.opal" ]]` 가드를 uninstall.sh / install-mac.sh / windows.ps1에 일괄 추가."

#### M-10: skill-registry.js ReDoS + path 정규화 (R-5 + GC-013 보너스)

(→ D-1 R-5 + D-2 §3 GC-004 + D-17)

설계 결정 — 의사코드 (P-D-7 임계값):

```javascript
// === ReDoS 방어 (GC-004) ===

const MAX_INPUT_LENGTH = 256;        // 입력 길이 제한
const MAX_PATTERN_LENGTH = 100;      // 패턴 길이 임계값
const MAX_DOTSTAR_COUNT = 2;         // .* 발생 횟수 임계값

function isUnsafeRegex(pattern) {
  if (pattern.length > MAX_PATTERN_LENGTH) {
    return { unsafe: true, reason: `pattern length > ${MAX_PATTERN_LENGTH}` };
  }
  // .* 또는 .+ 발생 횟수
  const dotStarCount = (pattern.match(/\.[*+]/g) || []).length;
  if (dotStarCount >= MAX_DOTSTAR_COUNT) {
    return { unsafe: true, reason: `.* / .+ count >= ${MAX_DOTSTAR_COUNT}` };
  }
  // nested quantifier: (xxx+)+ / (xxx*)* / (xxx+)* 류
  if (/\([^)]*[+*]\)[+*]/.test(pattern)) {
    return { unsafe: true, reason: 'nested quantifier' };
  }
  return { unsafe: false };
}

function matchByTriggers(skills, input) {
  // 입력 길이 제한
  if (input.length > MAX_INPUT_LENGTH) {
    return null;  // 길이 초과 입력은 매칭 skip (반환 null로 안전)
  }
  for (const skill of skills) {
    if (!skill.triggers) continue;
    for (const pattern of skill.triggers) {
      // ReDoS 휴리스틱 사전 검사
      let pat = pattern;
      let flags = '';
      if (pat.startsWith('(?i)')) { flags = 'i'; pat = pat.slice(4); }
      const safety = isUnsafeRegex(pat);
      if (safety.unsafe) continue;  // 위험 패턴 skip (매칭하지 않음)
      try {
        const regex = new RegExp(pat, flags);
        if (regex.test(input)) return skill;
      } catch (e) { /* invalid regex, skip */ }
    }
  }
  return null;
}

// === path 정규화 (GC-013 보너스) ===

function resolveFirstPath(paths) {
  if (!paths) return null;
  for (const p of paths) {
    let resolved = p
      .replace(/^~/, os.homedir())
      .replace(/\{project\}/g, process.cwd());
    // path.resolve로 정규화 + homedir/cwd 하위 검증
    resolved = path.resolve(resolved);
    const homeDir = os.homedir();
    const cwd = process.cwd();
    if (!resolved.startsWith(homeDir) && !resolved.startsWith(cwd)) {
      // homedir 또는 cwd 하위가 아니면 skip (CWE-22 path traversal 방어)
      continue;
    }
    if (fs.existsSync(resolved)) return resolved;
  }
  // 폴백: 기존과 호환 (마지막 path 반환 — 단, 정규화는 적용)
  if (paths.length === 0) return null;
  const fallback = paths[paths.length - 1].replace(/^~/, os.homedir());
  return path.resolve(fallback);
}

// === validate에 ReDoS 분석 추가 ===

function validate() {
  // ... 기존 validate ...
  for (const skill of skills) {
    if (skill.triggers) {
      for (const pattern of skill.triggers) {
        let pat = pattern;
        if (pat.startsWith('(?i)')) pat = pat.slice(4);
        const safety = isUnsafeRegex(pat);
        if (safety.unsafe) {
          warnings.push(`${skill.name}: trigger ReDoS 위험 — ${safety.reason} (pattern: ${pattern})`);
        }
      }
    }
  }
  // ...
}
```

- 헤더 변경이력 행 추가 (M-10):
  ```
  v1.1 2026-05-10 HH:MM KST: ReDoS 휴리스틱 + 입력 길이 제한 256자 + path 정규화 (144)
  ```

- **거짓양성 영향 분석** (현재 trigger 패턴 검사):
  - `google-labs-code/react-components`: `(?i)(stitch.*react|react\s*component.*stitch)` — `.*` 1회 + `\s*` 1회 → 미위험 (DOTSTAR_COUNT=1, length<100). 통과.
  - `getsentry/code-review`: `(?i)(코드\s*리뷰|PR\s*리뷰|code\s*review)` — 미위험.
  - 모든 기존 패턴은 임계값 미통과 → **거짓양성 0** (잠정 — 실행 검증 시 100% 확인).

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §6: "skill-registry trigger 패턴 휴리스틱 검사(길이 100자 초과 / `.*` 2회 이상 / nested quantifier reject). 입력 길이 제한 256자."

#### M-11, M-12, M-13, M-14: MCP `@latest` 핀 (R-6) + playwright 경로 (R-7)

(→ D-1 R-6 R-7 + D-2 §3 GC-006 GC-007 + D-20~D-23 + D-26 npm registry)

설계 결정 — P-D-4 마이너 핀 (npm registry 기준):

| 파일 | Before | After | 근거 |
|------|--------|-------|------|
| `mcps/shadcn.json:7` | `["-y", "shadcn@latest", "mcp"]` | `["-y", "shadcn@^4.7", "mcp"]` | npm shadcn@4.7.0 |
| `mcps/playwright.json:7` | `["@playwright/mcp@latest", "--output-dir", "/tmp/playwright-mcp"]` | `["@playwright/mcp@^0.0.75", "--output-dir", "~/.opal/cache/playwright-mcp"]` | npm @playwright/mcp@0.0.75 + R-7 경로 변경 |
| `mcps/context7.json:7` | `["-y", "@upstash/context7-mcp@latest"]` | `["-y", "@upstash/context7-mcp@^2.2"]` | npm @upstash/context7-mcp@2.2.4 |
| `mcps/sequential-thinking.json:7` | `["-y", "@modelcontextprotocol/server-sequential-thinking"]` | `["-y", "@modelcontextprotocol/server-sequential-thinking@^2025.12"]` | npm @modelcontextprotocol/server-sequential-thinking@2025.12.18 (캘린더 버전) |

- **playwright `--output-dir` 결정**: `~/.opal/cache/playwright-mcp` 사용 (mac/Linux). 
  - `~`는 MCP 클라이언트(claude/cursor/gemini)가 spawn할 때 expand 보장 안됨 → **절대 경로** 사용 권장. 단, `mcps/*.json`은 OS 무관해야 하므로 `~`를 그대로 두고, mac/Linux install이 사전에 `mkdir -p ~/.opal/cache/playwright-mcp` (0700) 보장 + Windows install이 `$env:TEMP` 치환은 v0.3.13에서 이미 처리됨.
  - **P-D-5 결정**: 신규 경로(`~/.opal/cache/playwright-mcp/`)만 사용. 기존 `/tmp/playwright-mcp/` 잔존 디렉토리 마이그레이션 없음 (사용자 영향 미미 — playwright MCP 첫 실행 시 자동 생성).
  - 단, `~` expand 안전성 확보를 위해 install이 등록 직전에 `[[ "${args_json}" == *"~/"* ]]` 검출 시 `${HOME}/...` 절대 경로로 expand하여 `claude mcp add --` 인자에 전달 (M-6 install_mcp_cli + M-7 Install-OpalMcp + M-8 _mcp_add 분기).

- mac/Linux install이 등록 직전: `mkdir -p "$HOME/.opal/cache/playwright-mcp" && chmod 700 "$HOME/.opal/cache"` (clean_dirs 루프 외 — community-skills/와 동일하게 보존 대상).

- Windows: `$env:TEMP\playwright-mcp` 치환은 v0.3.13에서 처리됨. R-7은 Windows 무영향.

[MUST] `tasks/144-260510-opp-security-hardening/TASK.md` §확정된 설계 방향 §7: "GC-006 MCP `@latest` 핀 — 4개 mcps/*.json에 마이너 버전 핀."

---

## §3. 실행 체크리스트

> 총 13개 Step | Phase 6개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1, 2, 3, 4 | 병렬 | mcps/*.json 4개 — 독립 파일 |
| 2 | 5, 6 | 병렬 | community-skills-registry.json + opal-skill-manager/SKILL.md (독립) |
| 3 | 7, 8 | 병렬 | skill-registry.js + uninstall.sh (독립) |
| 4 | 9, 10 | 병렬 | mcp.sh + (없음 — Step 11/12로 통합) |
| 5 | 11, 12 | 순차 | install-mac.sh + install/windows.ps1 (각자 mac/Windows 영역 — 동시 변경 의무로 같은 Phase) — **PowerShell+bash 동시 변경 시 회귀 위험** 고려해 EXECUTE에서 순차 권장 |
| 6 | 13, 14, 15 | 순차 | install.sh → install.ps1 → update.sh (모두 verify_checksum 동등 패턴) |
| 7 | 16 | 단독 | docs/SECURITY.md (모든 결정 사항 인용) |
| 8 | 17 | 단독 | 회귀 검증 |

> 실제 EXECUTE는 Phase 1-4 병렬 + Phase 5-8 순차로 수행. 각 Step에 `agent` 필드는 PROJECT.md Framework 단일 영역 → 폴백 `opal-task-agent`.

### Step 1: MCP shadcn.json 마이너 핀

- [x] 완료
- **파일**: `opal/core/mcps/shadcn.json`
- **agent**: opal-task-agent (Framework 폴백)
- **작업 내용**: `args` 배열 L7 `"shadcn@latest"` → `"shadcn@^4.7"` 변경. 다른 키 변경 없음.
- **완료 기준**: `python3 -c "import json; print(json.load(open('opal/core/mcps/shadcn.json'))['config']['args'][1])"` → `shadcn@^4.7` 출력
- **테스트**: install 후 `claude mcp list`에 shadcn@4.7.x 표시
- **AC 매핑**: R-6 (1)
- **변경이력**: JSON config 면제 (D-9 141 선례) — 미작성
- **의존**: 없음

### Step 2: MCP playwright.json 마이너 핀 + 경로 변경

- [x] 완료
- **파일**: `opal/core/mcps/playwright.json`
- **agent**: opal-task-agent
- **작업 내용**: `args` L7 `"@playwright/mcp@latest"` → `"@playwright/mcp@^0.0.75"` 변경 + `"/tmp/playwright-mcp"` → `"~/.opal/cache/playwright-mcp"` 변경
- **완료 기준**: JSON 파싱 정상 + 두 args 항목 모두 갱신
- **테스트**: install 후 `claude mcp list`에서 playwright@0.0.x + 새 경로 확인
- **AC 매핑**: R-6 (1) + R-7 (1)
- **변경이력**: JSON config 면제 — 미작성
- **의존**: 없음

### Step 3: MCP context7.json 마이너 핀

- [x] 완료
- **파일**: `opal/core/mcps/context7.json`
- **agent**: opal-task-agent
- **작업 내용**: `args` L7 `"@upstash/context7-mcp@latest"` → `"@upstash/context7-mcp@^2.2"` 변경
- **완료 기준**: JSON 파싱 정상 + args 갱신
- **테스트**: install 후 `claude mcp list`에서 context7@2.2.x 확인
- **AC 매핑**: R-6 (1)
- **변경이력**: JSON config 면제 — 미작성
- **의존**: 없음

### Step 4: MCP sequential-thinking.json 마이너 핀

- [x] 완료
- **파일**: `opal/core/mcps/sequential-thinking.json`
- **agent**: opal-task-agent
- **작업 내용**: `args` L7 `"@modelcontextprotocol/server-sequential-thinking"` → `"@modelcontextprotocol/server-sequential-thinking@^2025.12"` 변경 (캘린더 버전 핀)
- **완료 기준**: JSON 파싱 정상 + args 갱신
- **테스트**: install 후 `claude mcp list`에서 server-sequential-thinking@2025.12.x 확인
- **AC 매핑**: R-6 (1)
- **변경이력**: JSON config 면제 — 미작성
- **의존**: 없음

### Step 5: community-skills-registry.json v2.1 + commit_sha 신설

- [x] 완료
- **파일**: `opal/core/references/community-skills-registry.json`
- **agent**: opal-task-agent
- **작업 내용**: 
  1. `$schema: "opal-community-skills-registry-v2"` → `"opal-community-skills-registry-v2.1"`
  2. `version: "2.0.0"` → `"2.1.0"`
  3. `updated_at: "2026-05-10"` 갱신
  4. `schema_notes` 갱신 — "v2.1: commit_sha 옵션 필드 신설"
  5. anthropics 그룹 18건 모두 `source_repo` 다음에 `commit_sha: null` 추가 (필드 존재 보장)
- **완료 기준**: JSON 파싱 정상 + `node ~/.opal/tools/skill-registry/skill-registry.js validate` 실행 시 v2.1 인식 + warning만 (Unknown 라이선스 12건은 정상 warning)
- **테스트**: validate 성공 출력 + `$schema` 필드 v2.1 확인
- **AC 매핑**: R-3 (1)(3)
- **변경이력**: JSON config 면제 — 미작성 (D-9 141 선례) **단**, TASK.md §제약 조건이 "community-skills-registry.json도 변경이력 행 추가" 명시 — JSON에는 변경이력 표를 둘 수 없으므로, `schema_notes` 필드로 갈음 (`"v2.1: commit_sha 옵션 필드 신설 (144)"` 형식으로 태스크 번호 포함)
- **의존**: 없음

### Step 6: opal-skill-manager SKILL.md 동의 prompt 강화

- [x] 완료
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **agent**: opal-task-agent
- **작업 내용**:
  1. §6 prompt 형식 갱신 — Unknown 라이선스 빨간 경고 + 두 번째 확인 (영문+한글 병기) + commit_sha 노출
  2. §1 스킬 검색 안내에도 "라이선스 미확인 시 빨간 경고" 명시
  3. 변경이력 행 추가: `v1.2 | 2026-05-10 HH:MM KST | Unknown 라이선스 두 번째 확인 + commit_sha 노출 + 빨간 경고 (144)`
- **완료 기준**: §6 텍스트가 Unknown 분기 포함 + 변경이력 행 추가
- **테스트**: 수동 — 가상 시나리오로 google-labs-code/react-components 매칭 → prompt에 "⚠️ 라이선스 미확인" + 두 번째 확인 표시 검증
- **AC 매핑**: R-3 (2)
- **변경이력**: 추가 의무 (스킬 SKILL.md)
- **의존**: 없음

### Step 7: skill-registry.js ReDoS + path 정규화

- [x] 완료
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `MAX_INPUT_LENGTH=256` / `MAX_PATTERN_LENGTH=100` / `MAX_DOTSTAR_COUNT=2` 상수 추가
  2. `isUnsafeRegex(pattern)` 함수 신설 (§2 핵심 설계 의사코드 참조)
  3. `matchByTriggers` 입력 길이 제한 + isUnsafeRegex 사전 검사
  4. `resolveFirstPath` `path.resolve` + `os.homedir()` / `process.cwd()` 하위 검증
  5. `validate` 함수에 ReDoS 분석 warning 추가
  6. 헤더 변경이력 행: `v1.1 2026-05-10 HH:MM KST: ReDoS 휴리스틱 + path 정규화 (144)`
- **완료 기준**: 
  - `node ~/.opal/tools/skill-registry/skill-registry.js validate` 정상 실행
  - 위험 패턴 입력 시 — 가상 trigger `"(.+)+abc"` 등록 시 validate가 warning 출력
  - 256자 초과 입력 — `node ~/.opal/tools/skill-registry/skill-registry.js match "$(printf 'x%.0s' {1..300})"` → `{found: false}` 반환
- **테스트**: 위 명령 실행 + 정상 패턴(`(?i)(pdf|\\.pdf)`)이 여전히 매칭됨 확인
- **AC 매핑**: R-5 (1)(2)(3)
- **변경이력**: @header 내 변경이력 행 추가
- **의존**: 없음

### Step 8: opal-cli/lib/uninstall.sh OPAL_HOME 가드

- [x] 완료
- **파일**: `opal/tools/opal-cli/lib/uninstall.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. L47 `local opal_home=...` 직후에 정규화된 경로 비교 가드 추가 (§2 M-9 의사코드)
  2. `OPAL_HOME_OVERRIDE=1` 옵트인 환경 변수 처리
  3. 변경이력 행: `v1.0.1 2026-05-10 HH:MM 비표준 OPAL_HOME 거부 가드 (144)`
- **완료 기준**:
  - `OPAL_HOME=/tmp/test ~/.opal/bin/opal-cli uninstall --yes` → "비표준 OPAL_HOME 거부" 에러 + exit 1
  - `OPAL_HOME=/tmp/test OPAL_HOME_OVERRIDE=1 ~/.opal/bin/opal-cli uninstall --yes` → 통과 (설치 안된 상태에서는 "이미 제거되어 있습니다")
  - 표준: `~/.opal/bin/opal-cli uninstall --yes` → 정상 동작
- **테스트**: 위 3개 시나리오 실행
- **AC 매핑**: R-8 (1)(2)(3)
- **변경이력**: 행 추가
- **의존**: 없음

### Step 9: opal-cli/lib/mcp.sh command 화이트리스트

- [x] 완료
- **파일**: `opal/tools/opal-cli/lib/mcp.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `_mcp_add` 함수 L136 `command=...` 추출 직후 화이트리스트 검증 (§2 M-6 의사코드)
  2. 변경이력 행: `v1.0.1 2026-05-10 HH:MM command 화이트리스트 검증 (144)`
- **완료 기준**:
  - 가상 mcps/*.json에 `command: "curl"` 작성 후 `opal-cli mcp add` → reject + exit 1
  - 표준 mcps (4개) → 정상 동작
- **테스트**: 위 시나리오 실행
- **AC 매핑**: R-4 (1)
- **변경이력**: 행 추가
- **의존**: 없음

### Step 10: scripts/install-mac.sh — install_mcp_cli 화이트리스트 + fork banner + clean_dirs OPAL_HOME 가드

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `install_opal()` 진입부에 `OPAL_HOME` 가드 (M-9 패턴 — clean_dirs 루프 직전)
  2. `install_mcp` 또는 `install_mcp_cli`에 command 화이트리스트 검증 (M-6 패턴)
  3. install 진입점에 fork repo banner (`OPAL_REPO != ceo4ever/opal` 시 banner + 비대화형 거부) 
  4. playwright `~/.opal/cache/playwright-mcp` 디렉토리 0700 mkdir 보장 + args의 `~/...` → `${HOME}/...` expand
  5. 변경이력 행: `v? 2026-05-10 HH:MM command 화이트리스트 + fork banner + OPAL_HOME 가드 + playwright cache (144)`
- **완료 기준**:
  - `OPAL_REPO=test/fork bash scripts/install-mac.sh` (대화형) → fork banner 표시
  - `OPAL_REPO=test/fork OPAL_AUTO_INSTALL=1 bash scripts/install-mac.sh` → reject (옵트인 없으면 거부)
  - `OPAL_HOME=/tmp/test bash scripts/install-mac.sh` → 거부
  - 표준 사용자: `bash scripts/install-mac.sh` → 변화 없음
- **테스트**: 위 시나리오 실행 + `claude mcp list`에서 playwright 새 경로 확인
- **AC 매핑**: R-4 (2)(3) + R-7 (2) + R-8 (1)
- **변경이력**: 행 추가
- **의존**: 없음 (Step 1-9와 독립이지만 EXECUTE는 11과 순차로 권장)

### Step 11: scripts/install/windows.ps1 — Install-OpalMcp 화이트리스트 + fork banner + Remove-Item 가드

- [x] 완료
- **파일**: `scripts/install/windows.ps1`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `Install-OpalFramework` 진입부 `clean Dirs` 루프 직전에 OPAL_HOME 가드 (PowerShell 변종)
  2. `Install-OpalMcp`에 command 화이트리스트 검증
  3. install 진입점에 fork repo banner
  4. 변경이력 행: `v? 2026-05-10 HH:MM command 화이트리스트 + fork banner + OPAL_HOME 가드 (144)`
- **완료 기준**:
  - `$env:OPAL_REPO='test/fork'; iex (irm ...)` → fork banner
  - `$env:OPAL_HOME='C:\test'; iex (irm ...)` → reject
  - 표준 사용자: 변화 없음
- **테스트**: Windows 환경에서 위 시나리오 (mac에서는 dry-run + Read 검증)
- **AC 매핑**: R-4 (2)(3) + R-8 (1)
- **변경이력**: 행 추가
- **의존**: Step 10 (mac 검증 후 Windows로 이식 — bash↔ps1 동기화 보장)

### Step 12: scripts/install.sh — verify_checksum prompt + 비대화형 거부 + main banner

- [x] 완료
- **파일**: `scripts/install.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `verify_checksum` 함수 L226-228 `warn ... return 0` 분기 — release tag(v*) + sha256sums.txt 부재 시:
     - `[[ ! -t 0 ]] || [[ "${OPAL_AUTO_INSTALL:-}" == "1" ]]` (비대화형) → `[[ "${OPAL_ALLOW_UNVERIFIED:-}" == "1" ]] || error "..."` (옵트인 없으면 거부)
     - 대화형 → prompt `[y/N]` (디폴트 N → error)
  2. `main()` L329에 main 브랜치 UNVERIFIED banner (release tag 외 모든 버전 — `if [[ "${OPAL_VERSION}" != v* ]]; then warn "[UNVERIFIED] ..."; fi`)
  3. 변경이력 행: `v1.3 2026-05-10 HH:MM verify_checksum 강화 — sha256sums.txt 부재 시 prompt/거부 + main UNVERIFIED banner (144)`
- **완료 기준**:
  - `OPAL_VERSION=main bash scripts/install.sh` → "[UNVERIFIED]" banner 출력
  - `OPAL_VERSION=v0.4.0 OPAL_REPO=test/empty bash scripts/install.sh < /dev/null` → 비대화형 + sha256sums.txt 미존재 → 거부
  - `OPAL_VERSION=v0.4.0 OPAL_ALLOW_UNVERIFIED=1 ... bash` → 통과
  - 정상: `OPAL_VERSION=v0.4.0 bash scripts/install.sh` (ceo4ever/opal) → sha256sums.txt fetch 성공 → 변화 없음
- **테스트**: dry-run 가능 (`OPAL_DRY_RUN=1`) + 실제 fetch 시나리오
- **AC 매핑**: R-2 (1)(2)(3)(4)
- **변경이력**: 행 추가
- **의존**: 없음 (Step 13과 동등 패턴이므로 검증 후 이식)

### Step 13: scripts/install.ps1 — Verify-Checksum prompt + 비대화형 거부 + main banner

- [x] 완료
- **파일**: `scripts/install.ps1`
- **agent**: opal-task-agent
- **작업 내용**:
  1. `Verify-Checksum` L188-190 catch 분기에 PowerShell 변종 — `$env:OPAL_ALLOW_UNVERIFIED -eq '1'` 검사 + 비대화형 검출(`$Host.UI.RawUI` 미접근 시) → throw
  2. `Invoke-OpalInstall`에 main banner
  3. 변경이력 행: `v1.0.6 2026-05-10 HH:MM Verify-Checksum 강화 (144)`
- **완료 기준**: install.sh와 동등한 동작 (PowerShell 환경)
- **테스트**: Windows + WSL 환경에서 검증
- **AC 매핑**: R-2 (1)(2)(3)(4)
- **변경이력**: 행 추가
- **의존**: Step 12 (bash 검증 후 PowerShell 이식)

### Step 14: opal-cli/lib/update.sh — verify_checksum 동등 패턴

- [x] 완료
- **파일**: `opal/tools/opal-cli/lib/update.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. L181-182 `warn "sha256sums.txt 다운로드 실패 — 체크섬 검증 생략"` 분기에 install.sh와 동일 prompt/거부 로직
  2. main 명시 시(`opal-cli update --to main`) UNVERIFIED banner
  3. 변경이력 행: `v1.0.4 2026-05-10 HH:MM verify_checksum 강화 (144)`
- **완료 기준**:
  - `opal-cli update --to main` → UNVERIFIED banner
  - `OPAL_AUTO_INSTALL=1 opal-cli update --to v0.4.0` (sha256sums.txt 미존재 가상 시나리오) → 거부
- **테스트**: 위 시나리오
- **AC 매핑**: R-2 (1)(2)(3)(4)
- **변경이력**: 행 추가
- **의존**: Step 12 (install.sh 패턴 이식)

### Step 15: docs/SECURITY.md 신설

- [x] 완료
- **파일**: `docs/SECURITY.md` (신규)
- **agent**: opal-task-agent
- **작업 내용**: §2 N-1 설계의 6 섹션 골격 그대로 작성. 각 섹션은:
  - §1 위협 모델: OWASP Top 10 / CWE Top 25 / SANS Top 25 인용 (D-24 D-25)
  - §2 install 무결성: 본 PLAN의 Step 12-14 결정 인용 + GC-DP-001/003 매핑
  - §3 MCP 신뢰 경계: Step 9-11 결정 인용 + GC-DP-002/005 매핑 + 4개 MCP 마이너 핀 표
  - §4 third-party fetch: Step 5-6 결정 인용 + GC-DP-004 매핑 + Unknown 라이선스 12건 표
  - §5 의존성 핀: Step 1-4 결정 + 후속 GC-005 (requirements.lock) 명시
  - §6 ReDoS 방어: Step 7 결정 + 임계값 표
- **완료 기준**: 6 섹션 모두 작성 + opal-pilot-gc가 `docs/SECURITY.md` 인식 (base-security-checklist 외 추가 baseline으로 동작)
- **테스트**: 수동 리뷰 — 6 섹션 모두 GC-DP-001~005 매핑 + 한국어 본문 + 영어 코드/필드명 규칙 준수
- **AC 매핑**: R-1 (모든 항목)
- **변경이력**: docs 면제 (D-9 141 선례) — 메타데이터로 갈음 (작성일 + 적용 버전)
- **의존**: Step 1-14 (모든 결정 사항 인용 필요)

### Step 16: 회귀 검증

- [ ] 완료
- **파일**: (런타임 검증)
- **agent**: opal-task-agent (또는 사용자 직접)
- **작업 내용**:
  1. `bash scripts/install-mac.sh` (캡틴 mac 환경) → 정상 종료
  2. `claude mcp list` → 4개 MCP 모두 새 버전으로 등록 + playwright 새 경로
  3. `//pdf` 매칭 → 정상 (anthropics/pdf trigger 매칭, 256자 미만)
  4. `~/.opal/bin/opal-cli doctor` → 모든 섹션 통과
  5. `OPAL_HOME=/tmp/test ~/.opal/bin/opal-cli uninstall --yes` → 거부 + exit 1
  6. `~/.opal/bin/opal-cli uninstall --yes` (실제 시나리오는 캡틴 판단 — dry-run으로 가드만 검증)
- **완료 기준**: 모든 시나리오 정상 동작
- **테스트**: 위 6개 시나리오 실행
- **AC 매핑**: R-9 (1)(2)(3)(4)(5)
- **변경이력**: 해당 없음
- **의존**: Step 1-15

---

## §4. QA 체크리스트

### 4.1 기능 테스트

- [x] **R-1 SECURITY.md**: 6 섹션 모두 작성됨 + GC-DP-001~005 매핑 + opal-pilot-gc 인식 (수동 검증)
- [x] **R-2 install 무결성**: 
  - [ ] release tag + sha256sums.txt 정상 → 검증 통과 (회귀 0) — Step 16 캡틴 실환경 검증
  - [x] release tag + sha256sums.txt 부재 + 비대화형 → 거부 (코드 구현 완료)
  - [x] release tag + sha256sums.txt 부재 + `OPAL_ALLOW_UNVERIFIED=1` → 통과 + 경고 (코드 구현 완료)
  - [x] main 브랜치 → UNVERIFIED banner (DRY_RUN 검증 완료)
  - [x] 3 파일 (install.sh / install.ps1 / update.sh) 모두 동등 동작
- [x] **R-3 fetch 신뢰**: 
  - [x] community-skills-registry.json v2.1 스키마 + commit_sha 옵션 필드
  - [x] opal-skill-manager Unknown 라이선스 두 번째 확인
  - [x] skill-registry.js validate가 v2.1 인식 (v2 + v2.1 모두 통과)
- [x] **R-4 MCP spawn**: 
  - [x] 화이트리스트 외 command (e.g. `curl`) → reject (3 파일 모두 구현 완료)
  - [x] OPAL_REPO=fork → banner 출력 (코드 구현 완료)
  - [x] OPAL_REPO=ceo4ever/opal → 변화 없음 (분기 조건 확인)
- [x] **R-5 ReDoS**: 
  - [x] 위험 패턴(`(.+)+abc`) 등록 시 validate warning (isUnsafeRegex 검출 확인)
  - [x] 256자 초과 입력 → match skip (`found: false` 검증 완료)
  - [x] 정상 패턴(`(?i)(pdf|\\.pdf)`) 매칭 정상 (`found: true` 검증 완료)
  - [x] resolveFirstPath path.resolve + homedir 가드 (코드 구현 완료)
- [x] **R-6 MCP 핀**: 
  - [x] 4개 mcps/*.json 모두 specific 버전 (마이너 핀) — JSON 검증 완료
  - [ ] `claude mcp list`에서 새 버전 표시 — Step 16 캡틴 실환경 검증
- [x] **R-7 /tmp 경로**: 
  - [x] playwright.json output-dir 갱신 (`~/.opal/cache/playwright-mcp`)
  - [x] mac install이 `~/.opal/cache/playwright-mcp/` 0700 디렉토리 생성 (코드 구현)
  - [x] Windows 분기 무영향 (기존 $env:TEMP 치환 로직 유지)
- [x] **R-8 OPAL_HOME 가드**: 
  - [x] `OPAL_HOME=/tmp/test` 호출 시 reject (3 위치 모두 구현)
  - [x] `OPAL_HOME_OVERRIDE=1` 옵트인 시 통과 (코드 구현)
- [ ] **R-9 회귀**: install / `claude mcp list` / `//pdf` / doctor / uninstall — Step 16 캡틴 실환경 검증

### 4.2 일관성 테스트

- [x] mac (install-mac.sh) ↔ Windows (install/windows.ps1) command 화이트리스트 동등
- [x] mac ↔ Windows fork banner 메시지 동등 (한국어 본문)
- [x] mac ↔ Windows OPAL_HOME 가드 동등
- [x] install.sh ↔ install.ps1 ↔ update.sh verify_checksum 분기 동등
- [x] community-skills-registry.json v2.1 ↔ skill-registry.js validate v2.1 인식 (v2+v2.1 모두)
- [x] opal-skill-manager prompt 형식 ↔ skill-registry.js 응답의 commit_sha 필드
- [x] 4개 mcps/*.json 마이너 핀 형식 통일 (`@^x.y` 형식 통일)
- [x] SECURITY.md 인용 ↔ PLAN.md 결정 사항 정합 (양방향 cross-ref)

### 4.3 문서 품질

- [x] SECURITY.md 한국어 본문 + 영어 코드/필드명 규칙 준수 (CONVENTIONS.md §언어 규칙)
- [x] kebab-case 파일/폴더 네이밍 준수 (해당 없음 — 기존 파일만 수정)
- [x] 변경이력 의무 준수:
  - [x] install.sh / install.ps1 / install-mac.sh / install/windows.ps1 — 헤더 변경이력 행
  - [x] opal-cli/lib/{update,uninstall,mcp}.sh — 헤더 변경이력 행
  - [x] skill-registry.js — @header 내 변경이력 행
  - [x] opal-skill-manager/SKILL.md — `## 변경이력` 표 행
  - [x] community-skills-registry.json — `schema_notes` 필드에 (144) 명시
  - [x] 4개 mcps/*.json + SECURITY.md — 면제 (D-9 141 선례)
- [x] @header 규칙 준수 (해당 코드 파일은 모두 헤더 보유 — 변경이력만 행 추가)

### 4.4 프로젝트 컨벤션 준수

- [x] [MUST] D-3 §변경이력 작성 의무 — 의무 파일 모두 행 추가
- [x] [MUST] D-3 §Guards — EXECUTE 전 사용자 승인 게이트 보장 (PLAN 단계 종료)
- [x] [MUST] D-3 §플랫폼 분기 격리 — install 분기는 install.sh/install.ps1 한 곳, 본체 분기는 install-mac.sh/install/windows.ps1 한 곳
- [x] [MUST] D-3 §언어 규칙 — 본문 한국어 + 코드/필드명 영어
- [x] [MUST] D-3 §배포 경계 — 모든 변경은 프로젝트 소스 (`opal/`, `skills/`, `scripts/`)에서만 수행

---

## §5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-1 | install/MCP/// 매칭 흐름 회귀 | 정상 사용자 (ceo4ever/opal release tag) install/update 차단 | Step 16 회귀 검증 — 5개 시나리오. 정상 흐름은 sha256sums.txt 정상 fetch → 분기 미발동. CI release.yml이 sha256sums.txt 보장 (D-10) |
| R-2 | ReDoS 휴리스틱 거짓양성 | 정상 trigger 패턴이 reject되어 // 매칭 실패 | 현재 모든 trigger 패턴 사전 검사 — 임계값(길이 100 / `.*` 2회 / nested) 미통과 0건. 위험 의심 패턴(`stitch.*react|react\s*component.*stitch`)은 `.*` 1회로 통과. EXECUTE 시 `validate` 출력 100% 확인 |
| R-3 | MCP 마이너 핀 비호환 | install 후 MCP 동작 실패 | npm registry 최신 버전 기반(D-26) — `^x.y` semver는 patch+minor 자동 갱신 허용. 단, sequential-thinking@2025.12.x 캘린더 버전은 `^2025.12` semver 호환 미보장 — 실제 패키지 동작 EXECUTE 시 확인 |
| R-4 | playwright `~/.opal/cache/` 경로 expand 실패 | playwright MCP 시작 실패 | install이 args의 `~/...` → `${HOME}/...` 절대 경로 expand. 3개 install 위치(install-mac.sh + windows.ps1 + mcp.sh) 모두 동등 처리 (M-6 의사코드) |
| R-5 | OPAL_HOME_OVERRIDE 누설 | CI/test 환경에서 가드 우회 가능 — 의도된 동작이지만 문서화 부재 시 보안 약점 | SECURITY.md §위협 모델에 "OPAL_HOME_OVERRIDE는 CI/test 한정 옵트인" 명시 |
| R-6 | fork banner 비대화형 거부의 영향 | curl|bash 자동화 사용자(fork repo)에 install 차단 | `OPAL_ALLOW_FORK=1` 옵트인 환경 변수 제공. SECURITY.md §3에 명시. |
| R-7 | community-skills-registry.json 변경이력 면제 적정성 | TASK.md §제약 조건이 "registry도 변경이력 행 추가" 명시 — JSON에 `## 변경이력` 표 둘 수 없음 | `schema_notes` 필드에 "v2.1: ... (144)" 형식으로 태스크 번호 명시. PM 검토 게이트에서 면제 적정성 확인 — **decision_required 후보** (P-D 결정 사항으로 처리) |
| R-8 | npm registry latest 버전과 mcps/*.json 핀 격차 | 핀 적용 시점 후 latest 갱신으로 사용자가 outdated 버전 사용 | `^x.y` 사용 → minor+patch 자동 추적. SECURITY.md §5에 "MCP 핀은 분기마다 갱신 의무" 명시. 후속 별도 태스크에서 분기별 핀 갱신 |
| R-9 | install.ps1 비대화형 검출의 PowerShell 한계 | `$Host.UI.RawUI` 접근이 일부 환경(Constrained Language Mode)에서 throw → 정상 사용자 차단 가능성 | try/catch 보호 + 폴백 — 검출 실패 시 비대화형으로 간주(보수적). EXECUTE에서 Windows 환경 검증 |
| R-T1 | 영역 간 용어 일관성 — `OPAL_HOME` (bash) ↔ `OpalHome` (PowerShell) | 환경 변수 동기화 필요 — bash는 `OPAL_HOME` env, PowerShell은 `$env:OPAL_HOME` 또는 파라미터 `$OpalHome` | 양 분기 모두 `$env:OPAL_HOME` 또는 `$OPAL_HOME` 환경 변수로 통일. install/windows.ps1의 `$OpalHome` 파라미터는 `$env:OPAL_HOME` ?? `Join-Path $env:USERPROFILE '.opal'` 폴백 (기존 패턴 유지) |

---

## §6. PM 검토 기준 (PLAN 검증)

PM이 PLAN.md를 검토할 때 확인해야 할 항목:

### 6.1 캡틴 결정 SSOT 정합

- [ ] §0 표가 TASK.md §확정된 설계 방향 §1~§10을 변경 없이 승계
- [ ] R-1~R-9 모두 §3 실행 체크리스트의 Step에 매핑됨

### 6.2 회귀 위험 통제

- [ ] §5 R-1: 정상 사용자(ceo4ever/opal release tag) 흐름이 영향 없음 — sha256sums.txt 정상 fetch 분기로 보장
- [ ] §5 R-2: 모든 기존 trigger 패턴이 ReDoS 휴리스틱 통과 (validate 사전 검증)
- [ ] §5 R-3: MCP 핀이 npm registry 최신 버전 기반 — `^x.y` semver 호환 검증

### 6.3 142 fetch 흐름 정합

- [ ] community-skills-registry.json v2 → v2.1 minor bump (스키마 호환)
- [ ] skill-registry.js validate가 v2 + v2.1 모두 인식 (기존 사용자 호환)

### 6.4 변경이력 의무 (D-3 §변경이력 작성 의무)

- [ ] 의무 8 파일 — 변경이력 행 추가 명시 (install.sh / install.ps1 / install-mac.sh / install/windows.ps1 / opal-cli/lib/{update,uninstall,mcp}.sh / skill-registry.js / opal-skill-manager/SKILL.md)
- [ ] 면제 6 파일 — community-skills-registry.json (schema_notes로 갈음) + 4개 mcps/*.json + SECURITY.md (D-9 141 선례)
- [ ] R-7 결정 사항 — community-skills-registry.json의 schema_notes 갈음이 적정한지 PM 게이트에서 결정

### 6.5 mac/Windows 동등성

- [ ] Step 10/11 — install-mac.sh + install/windows.ps1 모두 화이트리스트 + fork banner + OPAL_HOME 가드 동등
- [ ] Step 12/13 — install.sh + install.ps1 모두 verify_checksum 동등
- [ ] R-7 (Windows 무영향) 명시

### 6.6 보고 5요소 (reporting-template §8.1)

- [ ] 의사결정 요약 / 변경 범위 / 체크포인트 / 실행 구성 / 다음 액션 5요소가 워커 결과 보고에 포함

---

## §7. 미확정 사항 결정 결과 (P-D-1 ~ P-D-8)

TASK.md §미확정 사항을 PLAN 워커가 결정한 결과:

| ID | 결정 사항 | TASK.md 디폴트 | **PLAN 결정** | 근거 |
|----|----------|---------------|---------------|------|
| **P-D-1** | release tag 외 main 설치 흐름의 prompt 형식 | banner + 비대화형 거부 + `OPAL_ALLOW_UNVERIFIED=1` 옵트인 | **디폴트 채택** — main 브랜치는 sha256sums.txt 검증 자체 skip + UNVERIFIED banner 표시 (release tag만 sha256sums.txt 부재 시 prompt/거부) | TASK.md §3 + GC-001 영향 — main 분기는 항상 검증 불가, banner로 사용자 인지 충분 |
| **P-D-2** | MCP fork install banner의 trigger 시점 | install 시작 — 한 번만 | **디폴트 채택** — install 시작 시 한 번. mcp.sh `_mcp_add` 직접 호출 시 추가 banner 없음 (화이트리스트 가드만) | UX 일관성 + 노이즈 최소화. fork repo 한 번 동의 후 모든 MCP 등록 자동 |
| **P-D-3** | community-skills 라이선스 Unknown 두 번째 확인 텍스트 | 영문+한글 병기 | **디폴트 채택 + 디폴트 N** — "라이선스가 확인되지 않은 스킬입니다. 정말로 설치하시겠습니까? / This skill has an unverified license. Are you sure you want to install? (y/N)" | 한국어 사용자 + 국제 사용자 동등. 디폴트 N으로 사고 방지 |
| **P-D-4** | MCP `@latest` 핀의 구체 버전 | 마이너 핀 (`x.y` 또는 `^x.y.z`) | **마이너 핀 `^x.y` 채택** (npm registry 기준 — D-26): shadcn@^4.7 / @playwright/mcp@^0.0.75 / @upstash/context7-mcp@^2.2 / @modelcontextprotocol/server-sequential-thinking@^2025.12 | npm 표준 semver. 캘린더 버전(sequential-thinking)은 `^2025.12`로 동일 형식. patch 자동 갱신 허용 → 보안 패치 미수신 위험 회피 |
| **P-D-5** | playwright `/tmp` → `~/.opal/cache/` 변경의 사용자 영향 | 신규 경로만 사용 | **디폴트 채택** — 기존 `/tmp/playwright-mcp/` 잔존 무시. install이 `~/.opal/cache/playwright-mcp/` 0700 보장 + args expand | 마이그레이션 미필요 — playwright MCP 첫 실행 시 자동 생성. 사용자 영향 미미 |
| **P-D-6** | OPAL_HOME 가드 메시지 형식 | 명확한 reject 메시지 + 옵트인 가능 여부 | **`OPAL_HOME_OVERRIDE=1` 옵트인 채택**. 메시지: "비표준 OPAL_HOME 거부: $opal_home (예상: $HOME/.opal). 옵트인: OPAL_HOME_OVERRIDE=1 명시" | CI/test 환경 호환 + 명확한 옵트인 경로 |
| **P-D-7** | ReDoS 휴리스틱의 정확한 임계값 | 길이 100, `.*` 2회, nested quantifier | **디폴트 채택** — `MAX_PATTERN_LENGTH=100` / `MAX_DOTSTAR_COUNT=2` / nested quantifier `(xxx[+*])[+*]` 정규식 검출. 입력 길이 `MAX_INPUT_LENGTH=256` | 모든 기존 trigger 패턴 통과 (거짓양성 0). nested quantifier는 보수적 정규식 — `(.+)+` / `(\d+)*` 패턴 검출 |
| **P-D-8** | SECURITY.md의 §7 영역별 분리 여부 | 단일 영역(Framework)이라 허브 단독 | **단일 허브 채택** — §7 영역별 분리 미적용. PROJECT.md "프로젝트 구성" 단일 Framework 영역 (D-4) | 허브+링크 모델 미적용 — 단일 허브로 충분 |

추가 미확정 사항 (PLAN 작성 중 발견):

| ID | 결정 사항 | **PLAN 결정** | 근거 |
|----|----------|---------------|------|
| P-D-9 | community-skills-registry.json 변경이력 면제 적정성 | `schema_notes` 필드에 (144) 태스크 번호 명시으로 갈음. PM 게이트에서 최종 확인 (R-7 리스크) | TASK.md §제약 조건 명시 + JSON 표 부재 |
| P-D-10 | fork banner 비대화형 옵트인 | `OPAL_ALLOW_FORK=1` 환경 변수 제공 (SECURITY.md §3에 명시) | curl|bash 자동화 fork repo 사용자 호환 |
| P-D-11 | commit_sha 옵션 필드의 본 태스크 범위 | anthropics 18건만 `null` 명시 추가 (필드 존재 보장). 다른 그룹은 미추가 | 본 태스크는 스키마 신설만 — 실제 commit_sha 값 채우기는 후속 별도 태스크 |

### decision_required (PM 에스컬레이션 후보)

본 PLAN에는 §7.4 영역 간 용어 불일치(decision_required)는 발견되지 않았다. 모든 OPAL_HOME / OPAL_REPO / OPAL_ALLOW_* 환경 변수는 양 OS 분기에서 동일 토큰으로 사용 (R-T1 리스크는 PowerShell 파라미터 변환 문제 — 코드 레벨에서 흡수 가능).

P-D-9 (community-skills-registry.json 변경이력 갈음)은 PM 게이트에서 최종 결정을 받아야 한다 — TASK.md §제약 조건이 "변경이력 행 추가" 명시한 항목에 대한 면제 결정이므로.

---

## 종합 — PLAN 완료 보고 5요소 (reporting-template §8.1)

### 1. 의사결정 요약 (P-D-1 ~ P-D-11)

- **P-D-1~P-D-8**: TASK.md 디폴트 모두 채택. 단, P-D-1은 main 분기 banner-only로 명확화 (release tag만 prompt/거부).
- **P-D-9 (신설)**: community-skills-registry.json의 변경이력 갈음 형식 (`schema_notes` 필드에 (144) 명시) — **PM 게이트 결정 권장**.
- **P-D-10 (신설)**: fork banner 비대화형 옵트인 `OPAL_ALLOW_FORK=1` 추가.
- **P-D-11 (신설)**: 본 태스크 범위에서 anthropics 18건만 `commit_sha: null` 필드 명시 추가 (스키마 신설만 — 실제 값 채우기는 후속 태스크).

### 2. 변경 범위

- **신규 1 파일**: `docs/SECURITY.md` (6 섹션 골격)
- **수정 14 파일**:
  - install 흐름 5: install.sh / install.ps1 / install-mac.sh / install/windows.ps1 / opal-cli/lib/update.sh
  - opal-cli 도구 2: opal-cli/lib/uninstall.sh / opal-cli/lib/mcp.sh
  - Node 도구 1: skill-registry.js
  - 스킬 1: opal-skill-manager/SKILL.md
  - 레지스트리 1: community-skills-registry.json
  - MCP 4: mcps/{shadcn,playwright,context7,sequential-thinking}.json

### 3. 체크포인트

- **회귀 위험**: 정상 사용자(ceo4ever/opal release tag) 흐름은 sha256sums.txt 정상 fetch 분기 → 변화 없음. CI release.yml이 sha256sums.txt 보장 (D-10).
- **142 정합**: registry v2 → v2.1 minor bump (스키마 호환). skill-registry.js validate가 v2/v2.1 모두 인식 — 기존 사용자 호환.
- **기존 사용자 영향**: fork repo / main 브랜치 / `OPAL_HOME` 명시 사용자만 새 prompt/거부 동작. 정상 사용자 0 영향.
- **ReDoS 거짓양성**: 모든 기존 trigger 패턴 사전 검사 통과 (임계값 100/2/nested 미통과 0건).

### 4. 실행 구성

- **총 16개 Step / 8 Phase**:
  - Phase 1 (Step 1-4): 4개 mcps/*.json 병렬
  - Phase 2 (Step 5-6): registry + opal-skill-manager 병렬
  - Phase 3 (Step 7-8): skill-registry.js + uninstall.sh 병렬
  - Phase 4 (Step 9): mcp.sh 단독
  - Phase 5 (Step 10-11): install-mac.sh → install/windows.ps1 순차 (mac 검증 후 Windows 이식)
  - Phase 6 (Step 12-14): install.sh → install.ps1 → update.sh 순차
  - Phase 7 (Step 15): docs/SECURITY.md 단독 (모든 결정 사항 인용)
  - Phase 8 (Step 16): 회귀 검증 (사용자 직접 또는 워커)
- **agent 라우팅**: 모든 Step `opal-task-agent` (Framework 단일 영역 → PROJECT.md 폴백)

### 5. 다음 액션

1. **PM 검토 게이트** — 본 PLAN.md를 캡틴이 검토.
2. **승인 시 EXECUTE 진입** — Step 1-16 순서로 실행. semi-agentic 모드: PLAN까지 캡틴 검토 → EXECUTE 이후 PM 자율 → CLOSE 진입 캡틴 승인.
3. **EXECUTE 종료 후**:
   - QA Gate (op-task-qa)
   - 회귀 검증 (Step 16)
   - DONE.md 생성
   - 캡틴 확인 게이트 (memory feedback "DONE.md 생성 후 사용자 확인 게이트 거친 뒤 커밋")
   - 커밋 (캡틴 명시 요청 시)

---

> 본 PLAN.md는 op-task-plan 스킬 + opal-pilot-project 오케스트레이터의 PLAN 단계 산출물이며, TASK.md §확정된 설계 방향 §1~§10 (캡틴 결정 SSOT)을 변경 없이 승계한다. 모든 결정 사항은 §1 참조 문서 테이블의 D-1~D-26과 [MUST] 인용으로 추적 가능하다.

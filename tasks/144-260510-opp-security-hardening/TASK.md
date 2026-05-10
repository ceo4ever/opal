# TASK: OPAL 보안 강화 — SECURITY.md 신설 + High 4 + Medium 일부 fix

> 작성일: 2026-05-10 | 작업 유형: 개선 (보안) | 적용 스킬: opp | 모드: semi-agentic
> 입력: GC-SECURITY 보고서 (`GC-SECURITY-260510-2007.md` — 본 폴더) + 캡틴 결정 (2026-05-10 20:30)
> 출력: TASK.md / PLAN.md / DONE.md + 실제 코드/문서 변경

## 작업 목표

OPAL v0.4.0 시점에 발견된 14건의 보안 이슈(High 4 / Medium 6 / Low 3 / Info 1) 중 **High 4건 + Medium 핵심 일부 + SECURITY.md 신설**을 본 태스크에서 처리하여 오픈소스 공개 프레임워크로서의 신뢰 모델을 명문화·강화한다.

## 배경

OPAL이 v0.4.0 (community-skills fetch 전환 + MIT 라이선스 + 오픈소스 공개)으로 진화한 시점에 보안 진단(opal-security-checker, 2026-05-10) 수행. **Critical 0 / High 4 / Medium 6 / Low 3 / Info 1** — 즉시 차단 사유는 없으나 install·MCP·third-party fetch 흐름의 무결성·의존성 핀·라이선스 검증을 강화할 필요가 있다는 판정.

특히 (1) `curl ... | bash` one-liner 사용자가 sha256sums.txt 부재 시 무결성 검증 없이 임의 tarball 실행, (2) 142가 도입한 `npx skills add` fetch 흐름에 commit_sha 핀·라이선스 Unknown 강조 누락, (3) MCP `command`/`args`가 fork된 repo의 임의 명령으로 영속 등록 가능, (4) skill-registry trigger 정규식 ReDoS 방어 없음 — 4건이 핵심.

`docs/SECURITY.md`가 부재하여 위 위험들을 추적·검증할 baseline이 없음 (Info GC-014).

## 배경 분석 (대화에서 도출)

상세는 본 폴더의 `GC-SECURITY-260510-2007.md` (전체 14건 발견사항 + 권장 해결방안 + 문서 업데이트 제안 §4·§5) 참조. 본 TASK는 그 보고서의 §3 High 4건 + §3 Medium 핵심 일부 + §5 SECURITY.md 신설을 직접 매핑한다.

## 확정된 설계 방향 (대화에서 합의)

1. **범위는 High 4건 + Medium 핵심 + SECURITY.md 신설** — 캡틴 결정. Low 3건과 일부 Medium은 후속 분리.
2. **SECURITY.md를 SSOT로 신설** — 본 태스크에서 6개 섹션 골격 작성. 향후 GC가 비교 baseline으로 사용 (위 보고서 §5 골격 채택).
3. **install 무결성 강화 (GC-001 / GC-DP-001/003)** — release tag(v*) 패턴 + sha256sums.txt 부재 시 사용자 동의 prompt 또는 명시 플래그 요구. 비대화형 모드 기본 거부. main 브랜치 UNVERIFIED 경고.
4. **third-party fetch 신뢰 모델 (GC-002 / GC-DP-004)** — `community-skills-registry.json` 스키마에 `commit_sha` 필드 신설. `opal-skill-manager` 동의 prompt에서 `license: "Unknown"` 빨간 경고 + 두 번째 확인. fetch 후 실행 가능 파일 두 번째 동의는 PLAN에서 구체화.
5. **MCP spawn 신뢰 경계 (GC-003 / GC-DP-002/005)** — `command` 화이트리스트(`npx`, `npm`, `node`, `python3`만). `OPAL_REPO != ceo4ever/opal`인 경우 banner 경고 + 사용자 동의. release tag 무결성 통과 시에만 비대화형 자동 등록.
6. **ReDoS 방어 (GC-004)** — skill-registry trigger 패턴 휴리스틱 검사(길이 100자 초과 / `.*` 2회 이상 / nested quantifier reject). 입력 길이 제한 256자. validate 단계에 ReDoS 분석 추가.
7. **Medium 핵심 포함 범위**:
   - **GC-006 MCP `@latest` 핀** — 4개 mcps/*.json에 마이너 버전 핀 (예: `shadcn@2.x`)
   - **GC-007 /tmp/playwright-mcp 경로** — mac/Linux도 `~/.opal/cache/playwright-mcp/` 또는 `mktemp -d`로 변경 (Windows는 이미 v0.3.13 hotfix에서 `$env:TEMP`로 치환)
   - **GC-010 OPAL_HOME 가드** — `[[ "$opal_home" == "$HOME/.opal" ]]` 가드를 uninstall.sh / install-mac.sh / windows.ps1에 일괄 추가
8. **후속 분리** (별도 태스크 또는 Low 모음):
   - GC-005 (requirements.txt 핀): pip-compile 도입 — 별도 태스크 (도구 chain 구축 필요)
   - GC-008 (hooks/MCP JSON Schema 검증): JSON Schema + ajv 도입 — 별도 태스크
   - GC-009 (chmod +x 검증): 작은 변경이지만 보안 외 일관성 영역
   - GC-011 (winget 자동설치 prompt): UX 결정 영역 — 별도 결정
   - GC-012 (echo -e → printf): 일관성 정리 — 후속 P1
   - GC-013 (skill-registry path 정규화): 작은 변경 — 본 태스크 R-4 ReDoS와 함께 처리 가능 (선택)
9. **mac/Windows 동등 처리** — install 분기는 양 OS 동시 변경 의무.
10. **회귀 검증** — 본 태스크는 보안 강화라 회귀 시나리오가 핵심: install one-liner 정상 동작 / fetch 흐름 정상 동작 / MCP 등록 정상 동작 / // 커맨드 매칭 정상 동작.

## 요구사항

- [x] **R-1 SECURITY.md 신설**: GC-SECURITY 보고서 §5 골격 기반 6개 섹션. 무엇을: §1 위협 모델 / §2 install 무결성 / §3 MCP 등록 신뢰 경계 / §4 third-party 스킬 fetch / §5 의존성 핀 / §6 ReDoS 방어 / 어디에: `docs/SECURITY.md` (신규) / 왜: GC 비교 baseline + 사용자에게 신뢰 모델 명시 / AC: 6개 섹션 모두 작성, 각 섹션이 GC-DP-001~005 매핑, opal-pilot-gc가 본 문서를 인식

- [x] **R-2 install 무결성 강화 (GC-001)**: `install.sh` / `install.ps1` / `opal-cli/lib/update.sh` 3 파일. 무엇을: release tag(v*) 패턴 + sha256sums.txt 부재 시 사용자 동의 prompt 또는 `--insecure`/`OPAL_ALLOW_UNVERIFIED=1` 명시 플래그 요구. main 브랜치/HEAD는 stdout에 "UNVERIFIED — 무결성 검증 없음" 명확 경고. 비대화형 모드(pipe 또는 OPAL_AUTO_INSTALL=1)에서는 검증 실패 시 기본 거부. / 어디에: 3 파일 / 왜: curl|bash 신뢰 모델 / AC: (1) release tag 설치에서 sha256sums.txt fetch 실패 시 비대화형은 거부 / (2) main 설치는 명확 경고 / (3) `OPAL_ALLOW_UNVERIFIED=1` 옵트인 시에만 통과 / (4) 변경이력 3 파일 모두 추가

- [x] **R-3 third-party fetch 신뢰 모델 (GC-002)**: 무엇을: (a) `community-skills-registry.json` 스키마 v2.1로 `commit_sha` 필드 신설(현재 `source_repo` 다음에 추가, 옵션 필드 — 검증 가능한 스킬만 채움) / (b) `opal-skill-manager/SKILL.md` §6 자동 fetch 흐름의 동의 prompt에 `license: "Unknown"` 강조 + 두 번째 확인 강제 / (c) 해당 라이선스 미상 7개 스킬(getsentry/google-labs-code/trailofbits)에 명시적 경고 / 어디에: 2 파일 / 왜: supply-chain 위험 / AC: (1) 스키마 v2.1 검증 통과 / (2) 동의 prompt가 Unknown 라이선스 시 빨간 경고 + 두 번째 확인 / (3) skill-registry.js validate가 v2.1 인식 / (4) 변경이력 추가

- [x] **R-4 MCP spawn 신뢰 경계 (GC-003)**: 무엇을: (a) `install-mac.sh install_mcp_cli` + `windows.ps1 Install-OpalMcp` + `opal-cli/lib/mcp.sh _mcp_add` 3 파일에 command 화이트리스트 검증(`npx` / `npm` / `node` / `python3`만 허용, 그 외는 reject) / (b) `OPAL_REPO != ceo4ever/opal`인 경우 install 시작 banner에 "FORK INSTALL — MCP 등록 검토 필수" + 사용자 명시 동의 prompt / 어디에: 3 파일 + install 진입점 banner / 왜: fork 영속 백도어 회피 / AC: (1) 화이트리스트 외 command가 mcps/*.json에 들어가도 install 시 reject / (2) fork repo 설치 시 banner 출력 / (3) 변경이력 추가

- [x] **R-5 ReDoS 방어 (GC-004 + 보너스 GC-013)**: 무엇을: `skill-registry.js`에 (a) trigger 패턴 휴리스틱 검사(길이 > 100 / `.*` 2회 이상 / nested quantifier `(.+)+` 류 reject) / (b) 입력 길이 제한 256자 / (c) `validate`에 ReDoS 분석 추가 / (d) `resolveFirstPath` `~` 치환 후 `path.resolve` + homedir 검증 (GC-013 보너스) / 어디에: `opal/tools/skill-registry/skill-registry.js` / 왜: catastrophic backtracking 방어 + path traversal 방어 / AC: (1) 위험 패턴 등록 시 validate가 reject / (2) 256자 초과 입력은 trigger 매칭 skip / (3) 변경이력 추가 / [QA-Warning] PLAN §2 거짓양성 분석에서 react-components 패턴 `(?i)(stitch.*react|react\s*component.*stitch)`가 `.*` 1회로 잘못 기재됨 — 실제 2회이므로 `MAX_DOTSTAR_COUNT=2` 임계값에 걸려 reject됨. EXECUTE 전 임계값 검토 필요.

- [x] **R-6 MCP `@latest` 핀 (GC-006)**: 무엇을: 4개 `opal/core/mcps/*.json`(`shadcn.json` / `playwright.json` / `context7.json` / `sequential-thinking.json`) 모두 `@latest` 제거 + 마이너 버전 핀(현재 latest 기준 시점, e.g. `shadcn@2.x`) 적용. 신규 MCP 등록 정책으로 `version_pinned` 필드 의무화는 SECURITY.md §3에 명문화. / 어디에: 4 파일 / 왜: latest 자동 fetch가 임의 코드 실행 위험 / AC: (1) 4개 JSON 모두 specific 버전 명시 / (2) install 후 `claude mcp list`에서 새 버전 표시

- [x] **R-7 /tmp 경로 보안 (GC-007)**: 무엇을: `playwright.json`의 `--output-dir /tmp/playwright-mcp` → `~/.opal/cache/playwright-mcp/` 사용자 홈 경로로 변경. install이 mac/Linux에서 `mkdir -p ~/.opal/cache/` (0700) 보장. Windows는 v0.3.13에서 이미 `$env:TEMP`로 치환되므로 무영향. / 어디에: `opal/core/mcps/playwright.json` + (필요 시) install 분기 / 왜: race condition + symlink attack 방어 / AC: (1) playwright.json output-dir 갱신 / (2) install이 mac에서 0700 디렉토리 생성 / (3) Windows 분기 무영향 검증

- [x] **R-8 OPAL_HOME 가드 (GC-010)**: 무엇을: `opal-cli/lib/uninstall.sh` + `install-mac.sh` clean_dirs 루프 + `windows.ps1` Remove-Item 호출 3 위치에 가드 추가: bash `[[ "$opal_home" == "$HOME/.opal" ]] || error "비표준 OPAL_HOME 거부"` / PowerShell `if ($OpalHome -ne (Join-Path $env:USERPROFILE '.opal')) { throw }` / 어디에: 3 파일 / 왜: `OPAL_HOME=/` 등 광범위 삭제 사고 방지 / AC: (1) 가드 라인 명시 추가 / (2) `OPAL_HOME=/tmp/test`로 호출 시 reject 검증 / (3) 변경이력 추가

- [x] **R-9 회귀 검증**: 무엇을: 본 태스크 변경 적용 후 install one-liner / `claude mcp list` / `//pdf` 트리거 매칭 / opal-cli doctor / opal-cli uninstall 흐름 정상 동작 검증. / 어디에: mac (캡틴 환경) + Windows (push 후 캡틴 환경) / 왜: 보안 강화로 인한 회귀 가능성 / AC: (1) install 정상 종료 / (2) MCP 등록 정상 / (3) 트리거 매칭 정상 / (4) doctor 모든 섹션 통과 / (5) uninstall 가드 검증

## 제약 조건

- **변경이력 의무 (CONVENTIONS.md §변경이력 작성 의무)**: install.sh / install.ps1 / install-mac.sh / install/windows.ps1 / opal-cli/lib/update.sh / opal-cli/lib/uninstall.sh / opal-cli/lib/mcp.sh / skill-registry.js / opal-skill-manager/SKILL.md / community-skills-registry.json / 4개 mcps/*.json 모두 변경이력 행 추가. SECURITY.md / playwright.json은 docs/JSON config 면제 (141 v0.3.15 선례).
- **CONVENTIONS.md / Guards 준수**: 사용자 명시 승인 후에만 EXECUTE. 자동 커밋 금지.
- **기존 사용자 호환성 유지**: 본 태스크는 install 흐름의 안전성을 강화하지만 정상 사용자(ceo4ever/opal에서 release tag 설치)는 변화 없어야. 즉 fork 또는 main 설치만 새 prompt/거부 동작.
- **mac/Windows 동등 처리**: 모든 보안 강화는 양 OS 동등 적용.
- **회귀 검증 의무**: 본 태스크는 보안 강화라 install/MCP/// 매칭 흐름이 모두 정상 동작해야 — mac+Windows 양쪽 검증.
- **SECURITY.md 형식**: `docs/CONVENTIONS.md` 한국어 본문 + 영어 코드/필드명 규칙 준수.
- **142 fetch 흐름과 정합**: 142가 도입한 `community-skills-registry.json` v2를 v2.1로 minor bump (스키마 호환 유지).

## 기술 스택

- **install 스크립트**: bash (mac) / PowerShell (Windows)
- **CLI 도구**: Node.js v18+ (skill-registry.js)
- **MCP 등록**: claude/cursor/gemini CLI + JSON config
- **third-party fetch**: `npx skills` (vercel-labs/skills 외부 의존)
- **레지스트리**: JSON v2 → v2.1 minor bump (R-3)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 보고 | GC-SECURITY 보고서 | `tasks/144-260510-opp-security-hardening/GC-SECURITY-260510-2007.md` | 14건 발견 사항 + 해결 방안 + §5 SECURITY.md 골격 SSOT |
| D-2 | 외부 | OWASP Top 10 (2021) | https://owasp.org/Top10/ | A05/A06/A08 위반 기준 |
| D-3 | 외부 | CWE Top 25 / SANS Top 25 | https://cwe.mitre.org/top25/ | CWE-22/78/94/377/829/1333 위반 기준 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·Guards·커밋·플랫폼 분기 |
| D-5 | 설계 | PROJECT.md | `docs/PROJECT.md` | Framework 단일 영역 → opal-task-agent 폴백 |
| D-6 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 외부 의존 서비스 / 배포 모델 |
| D-7 | 컨텍스트 | 142 DONE.md | `tasks/142-260510-opp-community-skills-fetch-migration/DONE.md` | community-skills-registry v2 + null source_repo 7건 (R-3 컨텍스트) |
| D-8 | 컨텍스트 | 141 DONE.md | `tasks/141-260510-opp-readme-mit-license-p0/DONE.md` | docs 면제 선례 (변경이력 면제 판단) |
| D-9 | 외부 | shields.io | https://shields.io | (선택) SECURITY.md 배지 |
| D-10 | 소스 | release.yml | `.github/workflows/release.yml` | sha256sums.txt 생성 보장 검증 (R-2 후속) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

## 미확정 사항 (PLAN에서 결정)

| ID | 결정 사항 | PLAN 워커 디폴트 |
|----|----------|----------------|
| P-D-1 | release tag 외 main 설치 흐름의 prompt 형식 (interactive vs banner-only) | banner + 비대화형 모드는 거부 + `OPAL_ALLOW_UNVERIFIED=1` 옵트인 |
| P-D-2 | MCP fork install banner의 trigger 시점 (install 시작 vs MCP 등록 직전) | install 시작 — 한 번만 |
| P-D-3 | community-skills 라이선스 Unknown 두 번째 확인 텍스트 | 영문+한글 병기 |
| P-D-4 | MCP `@latest` 핀의 구체 버전 (PLAN 시점에 npm registry 조회) | 마이너 핀 (`x.y` 또는 `^x.y.z`) |
| P-D-5 | playwright `/tmp` → `~/.opal/cache/` 변경의 사용자 영향 (기존 캐시 마이그레이션) | 신규 경로만 사용, 기존 `/tmp/playwright-mcp/` 잔존은 무시 |
| P-D-6 | OPAL_HOME 가드 메시지 형식 | 명확한 reject 메시지 + 옵트인 가능 여부(예: `OPAL_HOME_OVERRIDE=1`) |
| P-D-7 | ReDoS 휴리스틱의 정확한 임계값 | 길이 100, `.*` 2회, nested quantifier 검출 |
| P-D-8 | SECURITY.md의 §7 영역별 분리 여부 | 단일 영역(Framework)이라 허브 단독 — 분리 안 함 |

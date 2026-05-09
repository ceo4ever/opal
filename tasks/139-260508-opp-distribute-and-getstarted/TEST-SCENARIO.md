# TEST SCENARIO: 배포 채널 정비 + Get Started UX 통합 (139)

> 작성일: 2026-05-08 | 상태: 작성 완료
> 입력: TASK.md, PLAN.md
> 출력 채움 담당: op-dev-test-agent (실행 명령/결과/상세)

## 시나리오 목록

### S-1: mac one-liner 신규 설치 (TS-001)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install.sh` + `scripts/install/macos.sh` + `~/.opal/bin/opal-cli` |
| 조건 | macOS, ~/.opal/ 부재 상태, bash·git·curl·tar·node·python3 사전 설치 |
| 기대 결과 | `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh \| bash` 실행 → ~/.opal/ 생성 (AGENT.md, identity.md(신규 시 onboarding 진입), skills/, agents/, references/, tools/, .venv/, templates/, community-skills/), ~/.opal/bin/opal-cli symlink 존재, 재실행 시 idempotent (마커 1회만) |
| 도구 | 수동 통합 검증 (clean macOS / 가상 머신 또는 격리 home dir) |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움: Pass / Fail / Skip}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-2: opal-cli update 사용자 데이터 보존 (TS-002, TS-009)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `opal/tools/opal-cli/lib/update.sh` + `scripts/install-mac.sh` 보존 정책 |
| 조건 | 기존 ~/.opal/ 존재, ~/.opal/identity.md 사용자 편집 상태, ~/.opal/projects/ 데이터 존재 |
| 기대 결과 | `opal-cli update` 실행 → ~/.opal/identity.md·projects/ 보존 (mtime/내용), ~/.opal/skills/·agents/·references/·tools/ 갱신, --to vX.Y 핀 옵션으로 특정 release 다운로드 |
| 도구 | 수동 검증 + diff 기반 보존 점검 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-3: opal-cli doctor 4섹션 출력 (TS-003)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `opal/tools/doctor/run.sh` + `lib/checks.sh` |
| 조건 | 정상 환경: bash·git·node·python3 모두 v18+, ~/.opal/ 정상 배포, MCP 등록 완료, 부트스트래퍼 마커 존재 |
| 기대 결과 | 4 섹션 모두 ✓ + exit 0. 의도적 결손(예: ~/.opal/AGENT.md rm) 시 해당 행 ✗ + exit 1 |
| 도구 | 수동 검증 + 결손 케이스 시뮬레이션 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-4: opal-cli uninstall 부트스트래퍼 마커 회수 (TS-004)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `opal/tools/opal-cli/lib/uninstall.sh` |
| 조건 | ~/.opal/ 정상 배포, ~/.claude/CLAUDE.md·~/.gemini/GEMINI.md 안에 OPAL/R2 마커 블록 존재 |
| 기대 결과 | `opal-cli uninstall` → ~/.opal/ 디렉토리 제거 (.opal/identity.md·projects/는 사용자 확인 후), CLAUDE.md/GEMINI.md에서 OPAL/R2 START~END 블록만 제거되고 파일 자체 보존 + 다른 사용자 콘텐츠 보존 |
| 도구 | 수동 검증 + diff |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-5: Linux 신규 설치 (TS-005)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install.sh` Linux uname 분기 |
| 조건 | Ubuntu 22.04 LTS Docker 또는 VM, bash·git·curl·tar·node·python3 사전 설치 |
| 기대 결과 | install.sh 실행 → install/linux.sh 또는 install/macos.sh 동일 흐름으로 ~/.opal/ 정상 생성 (Linux는 macOS와 동일 동작 가정 — bash 표준 의존) |
| 도구 | Docker 또는 VM 1회 검증 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-6: Windows 신규 설치 (TS-006)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install.ps1` + ExecutionPolicy 안내 |
| 조건 | Windows 10/11 PowerShell 5.1+ 또는 7.x, ExecutionPolicy = RemoteSigned 또는 ByPass |
| 기대 결과 | `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1)` → ~/.opal/ 생성 (Windows의 경우 %USERPROFILE%\.opal\). Restricted 정책에서 README 안내한 ByPass 명령 동작 |
| 도구 | Windows VM 1회 검증 (TASK R5 — 1회 통과로 충분 처리) |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-7: 셸 분기 idempotent (TS-007 / R2)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install-mac.sh` 신규 `register_path_in_shell_rc()` |
| 조건 | ~/.zshrc·~/.bashrc·~/.profile 중 1개 이상 존재 (다양한 조합 커버) |
| 기대 결과 | install 실행 후 존재하는 모든 rc 파일에 `# === OPAL PATH ===` 마커 + `export PATH="$HOME/.opal/bin:$PATH"` 라인 1회만 추가. 재실행 시 추가 안 됨 (idempotent). fish 사용자 안내 메시지 출력 (fish 설치 시) |
| 도구 | 산출물 검사 (grep 카운트) |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-8: strip 누락 방지 (TS-008 / R3)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install-mac.sh:717-718` 직후 strip_deploy_md_recursive 신규 호출 |
| 조건 | install 1회 완료 |
| 기대 결과 | `~/.opal/tools/opal-cli/`·`~/.opal/tools/doctor/` 하위 모든 .md 파일에서 `^## 변경이력$` 라인 부재 (배포본에 변경이력 노출 없음) |
| 도구 | 산출물 검사 (find + grep) |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-9: install_opal() 호출 그래프 보존 (TS-010 / ANALYSIS §3.2)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / `scripts/install-mac.sh:637-804` 변경 후 |
| 조건 | 본 태스크 변경 전·후 파일 비교 |
| 기대 결과 | install_opal() 함수 본체에서 함수 호출 순서가 변경 없이 보존 (추가만 허용 — install_opal_bin, strip_deploy_md_recursive 추가 외 변경 없음). diff 결과가 추가 라인만 포함 |
| 도구 | git diff + 호출 시퀀스 추출 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-10: PATH 충돌 회피 (TS-011 / R1)

| 항목 | 내용 |
|------|------|
| 대상 | F-001 / D1 결정 = `opal-cli` 명칭 |
| 조건 | 검증 환경 A: opalrb 미설치 / 환경 B: `brew install opal` 후 opalrb 존재 |
| 기대 결과 | A·B 모두 `which opal-cli` → `~/.opal/bin/opal-cli`. B에서 `which opal` → opalrb 그대로 (간섭 없음). 셸 재시작 후에도 동일 |
| 도구 | 환경 분리 수동 검증 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-11: 부트스트랩 next-action 보고 (TS-012)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / `opal/core/AGENT.md:44-54` 보고 형식 + 신규 `[안내]` 라인 |
| 조건 | 신규 세션 시작 (Claude Code / Cursor / Gemini 중 1개) |
| 기대 결과 | 첫 응답에 두 줄 출력 — `[부트스트랩] ✅ identity ✅ harness ✅ PM ⏳ ...` (기존 형식 보존) + `[안내] {next-action}` (신규). 기존 한 줄 형식이 변경되지 않음 |
| 도구 | AI 도구 재시작 후 첫 응답 캡처 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-12: identity 미존재 → onboarding 자동 발화 (TS-013)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / `opal/core/AGENT.md` Eager Step 2 기존 흐름 |
| 조건 | `~/.opal/identity.md` 부재 (`mv ~/.opal/identity.md{,.bak}`), `~/.opal/AGENT.md` 정상 |
| 기대 결과 | 신규 세션 첫 응답에 opal-onboarding Step 1 환영 메시지 ("OPAL(Open Protocol for Agentic Links) 에이전트 설정을 시작합니다 ...") 출력 |
| 도구 | AI 도구 재시작 후 첫 응답 캡처 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-13: 프로젝트 폴더 (a) 분기 (TS-014)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / cwd 분기 → (a) `//opi` 권유 |
| 조건 | `cd <프로젝트>/`, `.opal/AGENT.md` 존재 |
| 기대 결과 | 첫 응답 `[안내]`에 `//opi` 또는 `//opp/opd/opds`로 진입하라는 안내 포함 |
| 도구 | AI 도구 재시작 후 첫 응답 캡처 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-14: 비프로젝트 위치 (b) 분기 (TS-015)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / cwd 분기 → (b) 비서 모드 + 보조 안내 |
| 조건 | `cd ~`, `.opal/AGENT.md` 미존재 |
| 기대 결과 | 첫 응답 `[안내]`에 비서 모드 안내 + `//opi`로 프로젝트 초기화 가능 안내 포함 |
| 도구 | AI 도구 재시작 후 첫 응답 캡처 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-15: //start 재진입 가이드 (TS-016)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / `opal/skills/opal-start/SKILL.md` |
| 조건 | 신규 세션 또는 기존 세션 중간에 `//start` 입력 |
| 기대 결과 | skill-registry가 `opal-start` 매칭 → Step 1(환경 진단: identity / AGENT / cwd / doctor 권유) → Step 2(분기별 안내: a/b 메뉴) 출력 |
| 도구 | skill-registry CLI + 실제 대화 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-16: opal-onboarding triggers 추가 (TS-017)

| 항목 | 내용 |
|------|------|
| 대상 | F-002 / `opal/skills/opal-onboarding/SKILL.md:1-6` |
| 조건 | install 1회 완료 후 ~/.opal/skills/opal-onboarding/SKILL.md 배포본 |
| 기대 결과 | frontmatter에 `triggers:` 키 존재 + `//onboarding` 항목 포함. `node ~/.opal/tools/skill-registry/skill-registry.js match "//onboarding"` → onboarding(또는 opal-onboarding) 스킬 매칭 |
| 도구 | 산출물 검사 + skill-registry CLI |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-17: GitHub Release Workflow 가동 (TS-018)

| 항목 | 내용 |
|------|------|
| 대상 | F-003 / `.github/workflows/release.yml` |
| 조건 | 캡틴 명시 승인 후 `git tag v0.1 && git push origin v0.1` |
| 기대 결과 | Workflow 실행 → opal-v0.1.tar.gz + sha256sums.txt 생성 + actions/attest-build-provenance v2 attestation. GitHub Release 페이지에 두 자산 업로드. `gh attestation verify opal-v0.1.tar.gz --repo ceo4ever/opal` Pass |
| 도구 | GitHub Actions UI + gh CLI |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-18: {REPO_URL} 치환 완료 (TS-019)

| 항목 | 내용 |
|------|------|
| 대상 | F-003 / `README.md`, 기타 마크다운 |
| 조건 | Step 13 완료 후 git working tree |
| 기대 결과 | `git grep '{REPO_URL}'` 결과 0건 (모두 `https://github.com/ceo4ever/opal`로 치환됨) |
| 도구 | git grep |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-19: ARCHITECTURE.md 현행 전환 (TS-020)

| 항목 | 내용 |
|------|------|
| 대상 | F-003 / `docs/ARCHITECTURE.md:241-250` |
| 조건 | Step 15 완료 후 |
| 기대 결과 | §배포 채널 표에 GitHub Releases·opal-cli가 "현행", Homebrew·npm이 "예정" 표기. 결정 근거 주석에 "139에서 1차 채널 구현 완료" 문구 |
| 도구 | 산출물 검사 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-20: 변경이력 정합성 (TS-021)

| 항목 | 내용 |
|------|------|
| 대상 | F-003 / 영향 SKILL/AGENT/참조 문서 일괄 |
| 조건 | Step 16 완료 후 |
| 기대 결과 | `opal/core/AGENT.md`, `opal/skills/opal-onboarding/SKILL.md`, `opal/skills/opal-start/SKILL.md`, `opal/tools/opal-cli/README.md`, `opal/tools/doctor/README.md`, `opal/core/references/skills.md` (해당 시), `scripts/install-mac.sh` 헤더 등 모든 영향 파일에 `(139)` 변경이력 행 + KST 일시 + 변경내용 |
| 도구 | git grep `'(139)'` + 영향 파일 목록 비교 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### S-21: release.yml sanity check (TS-022)

| 항목 | 내용 |
|------|------|
| 대상 | F-003 / release.yml 옵션 검증 |
| 조건 | Step 17 완료 후 GitHub Actions UI |
| 기대 결과 | (선택) workflow 안에 attestation 검증 또는 install dry-run sanity 단계가 있으면 Pass. 없으면 Skip 처리 |
| 도구 | GitHub Actions 로그 |
| 실행 명령 | _{op-dev-test-agent가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

## 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 (Bash) | shellcheck `scripts/*.sh scripts/install/*.sh opal/tools/opal-cli/**/*.sh opal/tools/doctor/**/*.sh` | _{채움}_ | _{채움}_ |
| 2 | 린트 (PowerShell) | PSScriptAnalyzer `scripts/install.ps1` | _{채움}_ | _{채움}_ |
| 3 | 린트 (YAML) | yamllint `.github/workflows/release.yml` | _{채움}_ | _{채움}_ |
| 4 | 린트 (Markdown) | markdownlint `README.md` | _{채움}_ | _{채움}_ |
| 5 | 타입 체크 | _해당 없음 (Bash/PowerShell/YAML/MD)_ | _{채움}_ | _{채움}_ |
| 6 | 포맷터 | (shfmt 권장 — Bash) / (Format-Script — PowerShell) | _{채움}_ | _{채움}_ |

## 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | _{채움}_ | `git grep -nE "(password\|token\|api_key\|secret\|AWS_)" -- '*.sh' '*.ps1' '*.yml'` 결과 0건 기대 |
| 2 | .gitignore 확인 | _{채움}_ | 본 태스크 신규 파일은 모두 소스 — 별도 ignore 항목 추가 불필요. 단 `~/.opal/.venv/`는 deploy target이므로 영향 없음 |
| 3 | TLS 강제 (one-liner) | _{채움}_ | `scripts/install.sh`에 `curl -fsSL --proto '=https' --tlsv1.2` 사용 확인 |
| 4 | 체크섬 검증 | _{채움}_ | install.sh / install.ps1 내 verify_checksum 함수 호출 확인 |
| 5 | release.yml permissions 최소화 | _{채움}_ | `contents: write` / `id-token: write` / `attestations: write` 외 권한 없음 확인 |
| 6 | uninstall 데이터 손실 방지 | _{채움}_ | uninstall 시 ~/.opal/identity.md·projects/ 보존(또는 사용자 확인) 동작 확인 |

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | install-mac.sh 메뉴 1·2·3·4·0 동작 | _{채움}_ | 변경 전과 동일 동작 (호출 그래프 보존) |
| 2 | 기존 OPAL/R2 마커 호환 (`scripts/install-mac.sh:255-274`) | _{채움}_ | 기존 R2 마커 사용자 환경에서 OPAL 마커로 자동 전환 |
| 3 | 부트스트랩 한 줄 체크리스트 형식 (`opal/core/AGENT.md:44-54`) | _{채움}_ | 기존 형식 보존, [안내] 라인은 별도 |
| 4 | Lazy 트리거 테이블 7행 (`opal/core/AGENT.md:21-36`) | _{채움}_ | 행 수·내용 보존 |
| 5 | opal-onboarding 자동 발화 (identity 부재) | _{채움}_ | 기존 자동 발화 경로 보존, triggers는 명시 호출 보강만 |
| 6 | install_opal_section / extract_bootstrap_content | _{채움}_ | 4-backtick / 3-backtick 분기 보존 |

## 판정

**_{op-dev-test-agent가 채움: All Pass / Partial Fail / Critical Fail}_ -- _{판정 근거}_**

## 설계 피드백

시나리오 작성 과정에서 발견한 PLAN 빈틈:

1. **scripts/install/linux.sh 명시적 분리 미정** — install.sh 안의 `exec_platform_installer`가 macOS는 `install/macos.sh`를 호출한다고 명시했으나, Linux는 동일 파일을 재사용할지 별도 `install/linux.sh`를 둘지 PLAN §3.1 표에 명시되지 않음. 본 태스크는 macOS·Linux를 동일 bash 흐름으로 처리하는 것을 가정하므로 `install/macos.sh`를 두 OS에서 공용하거나, 동일 wrapper에서 `uname` 분기를 한 번 더 처리하는 두 옵션 중 EXECUTE 단계에서 결정 필요.
2. **opal-skills-registry.json 자동 동기화 메커니즘 미확인** — Step 11에서 `skills.md` 갱신만 명시했으나, JSON SSOT(`opal/core/references/opal-skills-registry.json`) 갱신 자동/수동 여부 미확인. install 시 자동 빌드 도구가 있는지(`opal/tools/skill-registry/`) EXECUTE 단계에서 확인 후 Step 11 작업 내용 보강 필요.
3. **Windows uninstall 흐름 미명시** — `opal-cli uninstall` (PLAN Step 3·§3.1.2)이 macOS 기준만 명시. Windows에서는 부트스트래퍼 위치(`%USERPROFILE%\.claude\CLAUDE.md` 등)와 PATH 등록 위치(시스템/사용자 환경 변수)가 다르므로, install.ps1 안에 `Uninstall-Opal` 함수 또는 별도 `uninstall.ps1` 신설을 EXECUTE 단계에서 검토. 본 태스크 범위에서는 macOS·Linux uninstall 우선 검증.
4. **doctor exit code 정책 vs. CI 사용 시나리오 미정** — TS-022에서 release.yml 안에서 doctor 호출 가능성을 언급했으나, CI 환경(GitHub Actions runner)에서 `~/.opal/`가 없으므로 doctor 자체 실행이 의미 없음. release.yml은 release 자산만 생성하고 doctor는 사용자 환경 진단 전용으로 구분하는 것이 적절. TS-022는 Skip 처리 가능.
5. **install 후 첫 세션 onboarding 자동 발화 시나리오 (S-12)와 부트스트랩 보고 (S-11) 충돌 가능성** — identity.md 부재 상태에서 신규 세션 시 onboarding이 우선이므로 부트스트랩 보고가 출력되지 않을 수 있다. 두 시나리오는 상호배타적으로 검증 (S-11은 identity 존재, S-12는 부재).

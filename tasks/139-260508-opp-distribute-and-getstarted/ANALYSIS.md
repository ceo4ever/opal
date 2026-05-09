# ANALYSIS: 배포 채널 정비 + Get Started UX 통합 (139)

> 작성일: 2026-05-08
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | TASK.md | `tasks/139-260508-opp-distribute-and-getstarted/TASK.md` | 작업 목표·범위·위험 |
| D-2 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 배포 모델, 2-Layer, 외부 의존 서비스 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | Guards·배포 경계·플랫폼 분기·변경이력 규칙 |
| D-4 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | PM 검토 기준 6항목, 금지사항 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 현행 설치 본체 (1173줄), 함수 그룹 분석 |
| D-6 | 소스 | core/AGENT.md (부트스트래퍼) | `opal/core/AGENT.md` | Eager/Lazy 부트스트랩, cwd 분기 삽입 위치 |
| D-7 | 소스 | opal-onboarding SKILL.md | `opal/skills/opal-onboarding/SKILL.md` | 현행 onboarding 트리거·환영 메시지 |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷 규칙 |
| D-9 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards·디스패치 의무·State |
| D-10 | 외부 | Homebrew formula: opal | [opal — Homebrew Formulae](https://formulae.brew.sh/formula/opal) | `opal` 명칭 충돌 점검 |
| D-11 | 외부 | npm: opal | [opal - npm](https://www.npmjs.com/package/opal) | npm `opal` 충돌 점검 |
| D-12 | 외부 | actions/attest-build-provenance | [attest-build-provenance](https://github.com/actions/attest-build-provenance) | GitHub Release attestation 구현 패턴 |
| D-13 | 외부 | curl-to-shell 보안 패턴 | [How to build a trustworthy curl pipe bash workflow](https://operous.dev/blog/how-to-build-a-trustworthy-curl-pipe-bash-workflow/) | One-liner installer 보안·체크섬·idempotent 패턴 |
| D-14 | 외부 | PowerShell irm/iex 패턴 | [PowerShell One-Liners for Installation](https://knowledge.buka.sh/powershell-one-liners-for-installation-what-does-irm-bun-sh-install-ps1-iex-really-do/) | install.ps1 표준 패턴 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `scripts/install-mac.sh` | OPAL 설치 본체 (macOS) — 1173줄, 대화형 메뉴 | 수정 (B 함수 분해 + D CLI PATH 등록) | `scripts/install-mac.sh:88-99` (show_menu), `:637-804` (install_opal) |
| `opal/core/AGENT.md` | 에이전트 코어 정의, Eager/Lazy 부트스트랩 | 수정 (F cwd 판별 + a/b next-action) | `opal/core/AGENT.md:11-19` (Eager 단계), `:87-114` (역할 전환) |
| `opal/skills/opal-onboarding/SKILL.md` | identity.md 부재 시 자동 발화, 재진입 진입점 없음 | 수정 (H triggers 보강) | `opal/skills/opal-onboarding/SKILL.md:1-6` (frontmatter — triggers 필드 없음) |
| `README.md` | 설치 섹션: `{REPO_URL}` 플레이스홀더, git clone 방식만 안내 | 수정 (I 4 Step, one-liner 삽입) | `README.md:78-82` (설치 명령) |
| `scripts/install.sh` | macOS/Linux 통합 one-liner 진입 부트스트랩 | 신규 (A) | - (부재 확인) |
| `scripts/install.ps1` | Windows one-liner 진입 부트스트랩 | 신규 (A) | - (부재 확인) |
| `scripts/install/macos.sh` | install-mac.sh 함수 분해 후 위치 | 신규/리팩 (B) | - (부재 확인) |
| `opal/tools/opal-cli/` | `opal` CLI 진입점 (install/update/doctor/uninstall/mcp) | 신규 (C, D) | - (부재 확인) |
| `opal/tools/doctor/run.sh` | 의존성·경로·MCP·부트스트래퍼 정합성 점검 | 신규 (E) | - (부재 확인) |
| `opal/skills/opal-start/SKILL.md` | `//start` 재진입 가이드 스킬 | 신규 (G) | - (부재 확인) |
| `.github/workflows/release.yml` | 태그 push → tarball + 체크섬 + attestation | 신규 (J) | - (.github/ 디렉토리 자체 부재) |
| `docs/ARCHITECTURE.md` | "배포 채널(예정)" 섹션 | 수정 (K) | `docs/ARCHITECTURE.md:241-250` |
| `opal/core/references/skills.md` | 스킬 레지스트리 허브 | 수정 (G opal-start 등록) | `opal/core/references/skills.md:1-74` |

### 1.2 아키텍처 패턴

**현행 배포 흐름**

- 소스 → `scripts/install-mac.sh` → `~/.opal/` 단일 경로 통합 배포
- 부트스트래퍼 마커: `# === OPAL START ===` / `# === OPAL END ===` (하위 호환: R2_START/END) — `scripts/install-mac.sh:25-32`
- `strip_deploy_md()` / `strip_deploy_md_recursive()`: 배포 시 `## 변경이력` 섹션 자동 strip — `scripts/install-mac.sh:182-199`
- `extract_bootstrap_content()`: 4-backtick 우선 → 3-backtick 폴백 — `scripts/install-mac.sh:201-209`
- `install_opal_section()`: OPAL/R2 마커 교체 or 파일 말미 추가 — `scripts/install-mac.sh:211-285`
- `emit_platform_agent_adapter()`: OPAL 에이전트를 Claude/Cursor/Gemini 어댑터로 변환·배포, AUTO-GENERATED 충돌 가드 포함 — `scripts/install-mac.sh:426-567`
- `install_opal()`: 전체 설치 오케스트레이터 함수 — `scripts/install-mac.sh:637-804`
- 사용자 보존 경로: `~/.opal/identity.md`, `~/.opal/AGENT.md` — `scripts/install-mac.sh:654`

**부트스트랩 Eager/Lazy 분리**

- Eager: identity.md → harness → PM → PM 컨텍스트 → 부트스트래퍼 자동 삽입 → 활성화 — `opal/core/AGENT.md:11-19`
- Lazy: `//` 커맨드, 워커 디스패치, MCP 요청 시 각각 트리거 — `opal/core/AGENT.md:21-36`
- **현행 미비점**: cwd 프로젝트 판별 후 next-action 분기 메시지가 없음 — `opal/core/AGENT.md:44-54` (부트스트랩 완료 보고에 분기 없음)

**install-mac.sh 함수 그룹 분류 (분해 설계 참조용)**

| 그룹 | 함수들 | 줄 범위 |
|------|-------|---------|
| detect_* | `detect_framework_root`, `detect_user` | :52-87 |
| merge_* | `merge_mcp_config`, `merge_hooks_config` | :104-164 |
| install_dir | `install_dir` | :166-180 |
| strip_* | `strip_deploy_md`, `strip_deploy_md_recursive` | :182-199 |
| extract_* | `extract_bootstrap_content` | :201-209 |
| install_opal_section | `install_opal_section` | :211-285 |
| install_gemini_* | `install_gemini_hardening`, `install_gemini_config` | :287-416 |
| install_claude_permissions | `install_claude_permissions` | :344-381 |
| emit_* | `emit_platform_agent_adapter` | :426-567 |
| install_*_agents | `install_claude_agents`, `install_cursor_agents`, `install_gemini_agents` | :569-633 |
| install_opal | `install_opal` (메인 오케스트레이터) | :637-804 |
| install_opal_* | `install_opal_community_skills`, `install_opal_venv`, `install_opal_references` | :806-896 |
| find_cli_bin, install_mcp* | MCP 설치 | :930-1056 |
| print_*, main | 출력·진입점 | :1058-1173 |

### 1.3 의존성 맵

```
scripts/install.sh (신규)
  └─ GitHub Releases tarball 다운로드 → sha256 체크섬 검증
  └─ scripts/install/macos.sh 또는 install-mac.sh 호출

scripts/install.ps1 (신규)
  └─ Invoke-RestMethod로 tarball 다운로드
  └─ 동일 install 로직 (PowerShell 구현)

opal/tools/opal-cli/ (신규)
  ├─ opal install     → scripts/install-mac.sh (또는 macos.sh) 실행
  ├─ opal update      → tarball 재다운로드 + 재설치 (--to vX.Y 옵션)
  ├─ opal doctor      → opal/tools/doctor/run.sh 호출
  ├─ opal uninstall   → ~/.opal/ 제거 + 부트스트래퍼 마커 회수
  └─ opal mcp         → install_mcp() 로직 래핑

opal/tools/doctor/run.sh (신규)
  ├─ 의존성 점검: bash/git/Node.js/Python 버전
  ├─ 경로 점검: ~/.opal/ 디렉토리 구조
  ├─ MCP 점검: claude/cursor/gemini 등록 상태
  └─ 부트스트래퍼 점검: CLAUDE.md/GEMINI.md OPAL 마커 존재

opal/core/AGENT.md (수정)
  └─ Eager Step 7 이후: cwd 판별(.opal/AGENT.md 존재 여부)
     → (a) 프로젝트: "//opi 권유" next-action 삽입
     → (b) 비프로젝트: "비서 모드 + 보조 안내" 삽입

opal/skills/opal-start/SKILL.md (신규)
  └─ triggers: ["//start", "시작", "처음부터"]
  └─ 현재 상태 진단 → identity.md 존재? → //opi 여부? → 다음 액션 권유
```

**install-mac.sh 핵심 호출 그래프**

```
main()
  ├─ detect_framework_root() + detect_user()
  └─ [메뉴 1/3] install_opal()
       ├─ strip_deploy_md()           → AGENT.md → ~/.opal/AGENT.md
       ├─ install_dir()               → skills/, agents/, templates/
       ├─ strip_deploy_md_recursive() → ~/.opal/skills/, agents/
       ├─ install_opal_venv()
       ├─ install_opal_references()
       ├─ install_opal_community_skills()
       ├─ merge_hooks_config()        → ~/.claude/settings.json
       ├─ install_opal_section()      → ~/.claude/CLAUDE.md, ~/.gemini/GEMINI.md
       ├─ install_gemini_hardening()  → ~/.gemini/GEMINI.md
       ├─ install_claude_permissions()
       ├─ install_claude_agents() ─┐
       ├─ install_cursor_agents()  ├─ emit_platform_agent_adapter() × N
       └─ install_gemini_agents() ─┘
            └─ install_gemini_config()
```

### 1.4 테스트 현황

- 현행 자동 테스트 없음 — 수동 실행 검증에 의존
- `scripts/install-mac.sh` 실행 자체가 통합 검증 역할
- TASK.md §검증 시나리오(S1~S11)가 최초 테스트 명세 역할 예정
- `.github/workflows/` 디렉토리 자체 부재 → S10(GitHub Release Workflow) 포함 CI 최초 도입

---

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

#### One-liner installer 표준 패턴 (→ D-13)

| 도구 | curl 플래그 | 핵심 보안 특징 |
|------|-----------|-------------|
| Homebrew | `-fsSL` | TLS 강제 |
| rustup | `--proto '=https' --tlsv1.2 -sSf` | TLS 버전 명시 + 프로토콜 제한 |
| nvm | `-o-` | 버전 핀 (태그 URL) |
| oh-my-zsh | `-fsSL` + `sh -c "(...)"`  | 서브셸 격리 |

**공통 보안 패턴 (OPAL 현행 적용 여부)**:
- `set -euo pipefail` — 오류 즉시 중단 → 이미 적용 (`scripts/install-mac.sh:13`)
- 전체 스크립트 `main()` 래핑 → 부분 실행 방지 → 이미 적용 (`:1122-1173`)
- 체크섬 별도 보관 (tarball과 분리된 위치) → 신규 구현 필요
- idempotent (재실행 시 사용자 데이터 보존) → 이미 적용 (`:654`)
- `--dry-run` 플래그 → 미지원, PLAN에서 검토 필요

#### GitHub Release attestation (→ D-12)

- `actions/attest-build-provenance` v2: 태그 push → tarball에 SLSA 빌드 출처 서명
- `subject-checksums` 입력: `sha256sums.txt` 파일을 attestation 대상 목록으로 자동 사용
- 검증 명령: `gh attestation verify <artifact> --repo <owner/repo>`
- 체크섬 생성: `sha256sum tarball.tar.gz > sha256sums.txt`

#### PowerShell 설치 패턴 (→ D-14)

```powershell
# 표준 one-liner (bun, uv, winget 스타일)
irm https://raw.githubusercontent.com/{owner}/{repo}/HEAD/scripts/install.ps1 | iex

# ExecutionPolicy 우회가 필요한 경우 (uv 패턴)
powershell -ExecutionPolicy ByPass -c "irm https://.../install.ps1 | iex"
```

- `irm` = Invoke-RestMethod (HTTP 다운로드), `iex` = Invoke-Expression (실행)
- ExecutionPolicy: `Unrestricted`, `RemoteSigned`, `ByPass` 중 하나 필요 (TASK R5)

### 2.2 버전 호환성 — `opal` 명칭 충돌 점검

| 채널 | 패키지명 | 상태 | 충돌 여부 |
|------|---------|------|---------|
| Homebrew formula | `opal` | 존재 — Ruby-to-JS 트랜스파일러 (opalrb.com) | **충돌 있음** |
| npm | `opal` | 존재 — v0.6.4, 11년 전 배포, 방치 상태 | 충돌 있음 (방치) |
| npm | `opal-security` | 활성 (v5.1.2, 13일 전) — Opal Security 사 CLI | 간접 충돌 (다른 제품) |
| Linux distro | 해당 없음 | 주요 패키지 매니저에서 `opal` 미확인 | - |

`brew install opal`은 이미 `opalrb` Ruby 트랜스파일러를 설치한다. `~/.opal/bin/opal` PATH 등록 시 macOS 환경에서 PATH 순서 충돌 가능성 존재. **decision_required** (아래 §부록).

---

## 3. 영향 범위

### 3.1 직접 영향

| 영역 | 변경 대상 | 변경 유형 |
|------|----------|---------|
| A | `scripts/install.sh`, `scripts/install.ps1` | 신규 |
| B | `scripts/install-mac.sh` → `scripts/install/macos.sh` 함수 분해 | 수정/리팩 |
| C | `opal/tools/opal-cli/` 디렉토리 + 서브커맨드 구현 | 신규 |
| D | `install_opal()` 내 `~/.opal/bin/opal` PATH 등록 로직 | 수정 |
| E | `opal/tools/doctor/run.sh` | 신규 |
| F | `opal/core/AGENT.md` Eager 분기 보강 | 수정 |
| G | `opal/skills/opal-start/SKILL.md` + `opal/core/references/skills.md` | 신규·수정 |
| H | `opal/skills/opal-onboarding/SKILL.md` triggers + 환영 메시지 | 수정 |
| I | `README.md` §설치 4 Step + one-liner | 수정 |
| J | `.github/workflows/release.yml` | 신규 |
| K | `docs/ARCHITECTURE.md` 배포 채널 "예정" → "현행" 전환 | 수정 |

### 3.2 간접 영향

**install-mac.sh 함수 분해 시 호출 그래프 보존 의무**:
- `install_opal()` 내 함수 호출 순서 변경 금지 (`scripts/install-mac.sh:637-804`)
- `install_opal_section()` — OPAL/R2 마커 하위 호환성 유지 필수 (`scripts/install-mac.sh:25-32`)

**strip_deploy_md 적용 범위 확장 필요**:
- 신규 `opal/tools/opal-cli/`, `opal/tools/doctor/` 경로에 .md 파일 추가 시 `strip_deploy_md_recursive` 호출 명시 필요 (`scripts/install-mac.sh:675,707,894` 기존 패턴 참조)

**변경이력 의무 대상** (→ D-3 §변경이력 작성 의무):
- `opal/core/AGENT.md` — (139) 항목 추가
- `opal/skills/opal-onboarding/SKILL.md` — (139) 항목 추가
- 신규 스킬·도구 — 초기 변경이력 행 포함 필수

**부트스트래퍼 마커 호환성**:
- 기존 사용자 환경의 `# === OPAL START ===` 마커는 `opal update` 재배포로 교체 — 호환성 파괴 없이 update 가능해야 함
- `opal uninstall` 시: CLAUDE.md, GEMINI.md에서 OPAL START~END 블록 삭제, 파일 자체 보존

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [x] 설정/환경변수 변경 — `~/.opal/bin/` PATH 등록 → `~/.zshrc`/`~/.bashrc`/`~/.profile` 셸별 분기 필요
- [x] 빌드/배포 파이프라인 변경 — `.github/workflows/release.yml` 신규 (CI 파이프라인 최초 도입)

---

## 4. 핵심 발견 사항

1. **`opal` 바이너리 명칭이 Homebrew core formula와 충돌** — `brew install opal`은 이미 Ruby 트랜스파일러 opalrb를 설치한다 (→ D-10). Homebrew tap은 후속 태스크 out-of-scope이나, `~/.opal/bin/opal` PATH 등록 자체가 macOS에서 PATH 순서 충돌을 유발할 수 있다. `opal-cli`, `opalx`, `op` 등 대안 명칭을 PLAN 전 결정해야 한다 (decision_required).

2. **install-mac.sh 함수 분해 시 strip_deploy_md 적용 범위를 명시적으로 확장해야 한다** — 현행 `install_opal()`은 `~/.opal/skills/`, `~/.opal/agents/`, `~/.opal/references/`에만 `strip_deploy_md_recursive`를 호출한다. 신규 `opal/tools/opal-cli/`, `opal/tools/doctor/` 경로에 .md 파일이 생기면 이를 누락하면 배포본에 변경이력이 노출된다 (`scripts/install-mac.sh:675,707,894`).

3. **부트스트랩 cwd 분기 삽입 위치가 명확히 특정된다** — `opal/core/AGENT.md` Eager 단계 Step 7 "에이전트 활성화" 직전에 cwd 판별 + next-action 라인을 추가하면 된다. 기존 Lazy 테이블과 보고 형식을 건드리지 않는다 (`opal/core/AGENT.md:11-19`, `:44-54`).

4. **opal-onboarding SKILL.md에 triggers 필드가 없다** — frontmatter에 `triggers:` 키 자체가 없어 (`opal/skills/opal-onboarding/SKILL.md:1-6`) 현재는 AGENT.md 부트스트랩에서만 호출된다. 명시적 재호출(`//onboarding`)을 가능하게 하려면 frontmatter에 triggers 추가가 필요하다.

5. **README 설치 섹션 `{REPO_URL}` 미완성 + one-liner 전무** — `README.md:79`의 `git clone {REPO_URL}`이 플레이스홀더 상태이며, one-liner installer 명령이 전혀 없다. one-liner 삽입과 동시에 실제 GitHub URL을 확정해야 한다 (decision_required).

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R1 | **`opal` 바이너리 PATH 충돌** — macOS에서 opalrb 설치 환경의 PATH 순서에 따라 Ruby 트랜스파일러 충돌 | 높음 | D-10; `docs/ARCHITECTURE.md:245-246` |
| R2 | **셸 환경 분기** — `~/.opal/bin/opal` PATH 등록 시 zsh/bash/fish rc 파일 분기 필요. `detect_user()`는 현재 홈 디렉토리만 처리 | 중간 | `scripts/install-mac.sh:66-87` |
| R3 | **strip_deploy_md 누락** — 신규 opal-cli/doctor 디렉토리 .md 파일이 `strip_deploy_md_recursive` 호출 누락 시 배포본에 변경이력 노출 | 중간 | `scripts/install-mac.sh:675,707,894` |
| R4 | **update 시 사용자 데이터 보존 범위 미정의** — `opal update`가 `~/.opal/tools/`(커스텀 도구), `~/.opal/community-skills/` 처리 방침 미정 | 중간 | `scripts/install-mac.sh:646-654` |
| R5 | **Windows PowerShell ExecutionPolicy** — `Restricted` 정책 환경에서 `irm ... | iex` 오류. `-ExecutionPolicy ByPass` 래핑 또는 사용자 안내 필요 | 중간 | D-14; `tasks/139-260508-opp-distribute-and-getstarted/TASK.md §R5` |
| R6 | **GitHub 레포 URL 미확정** — `README.md:79`의 `{REPO_URL}` 플레이스홀더. one-liner 삽입 전 레포 공개 URL 확정 필요 | 중간 | `README.md:79` |
| R7 | **npm `opal` 방치 패키지** — v0.6.4 (11년 방치) 충돌 위험 낮으나, 후속 `@opal/cli` 명칭 선점 시점 검토 필요 | 낮음 | D-11 |
| R8 | **PLAN 비대화** — 영역 11종(A~K) 단일 PLAN.md 과부하 위험 → 영역 그룹(A/B/C/D/E · F/G/H · I/J/K) 분할 필요 | 낮음 | `tasks/139-260508-opp-distribute-and-getstarted/TASK.md §R1` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전/비고 |
|----------|------|---------|
| 언어 (스크립트) | Bash | `set -euo pipefail`, macOS `/bin/bash` |
| 언어 (신규) | PowerShell | Windows install.ps1 |
| 언어 (도구) | Python | `/usr/bin/python3` + `~/.opal/.venv/` |
| 언어 (도구) | Node.js | v18+ (skill-registry, check-env.js) |
| 포맷 | Markdown + YAML frontmatter | 스킬·에이전트·부트스트래퍼 |
| CI | GitHub Actions | `.github/workflows/` 신규 도입 |
| 배포 저장소 | GitHub Releases | 태그 기반 tarball + 체크섬 |
| 체크섬/서명 | sha256sum + actions/attest-build-provenance | SLSA 빌드 출처 서명 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | 영역 그룹(A/B/C/D/E · F/G/H · I/J/K) 분할 구현 계획 수립 |
| op-dev-execute | Bash 스크립트·SKILL.md·AGENT.md·GitHub Actions YAML 구현 |
| op-dev-test-scenario | S1~S11 시나리오 상세화 (플랫폼 × OS × 분기 매트릭스) |
| op-dev-todo | PLAN 후 실행 체크리스트 확장 |
| op-dev-qa | EXECUTE 완료 후 품질 검증 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | GitHub Actions API 문서, actions/attest-build-provenance 사용법 조회 |

---

## 부록: decision_required

```json
{
  "decision_required": [
    {
      "type": "naming_conflict",
      "summary": "`opal` 바이너리 명칭이 Homebrew core formula(opalrb)와 충돌",
      "tokens": ["opal", "~/.opal/bin/opal"],
      "areas": ["C (CLI 진입점)", "D (PATH 등록)"],
      "source_refs": [
        "docs/ARCHITECTURE.md:245-246",
        "https://formulae.brew.sh/formula/opal"
      ],
      "suggested_resolution": "바이너리 명칭을 opal-cli, opalx, op 중 하나로 변경하거나, PATH 등록 시 충돌 경고 가드 추가. 최종 결정은 PLAN 전 사용자 승인 필요."
    },
    {
      "type": "config_required",
      "summary": "GitHub 레포 URL 미확정 — one-liner 및 README에 삽입할 실제 URL",
      "tokens": ["{REPO_URL}", "raw.githubusercontent.com"],
      "areas": ["A (install bootstrap)", "I (README)"],
      "source_refs": ["README.md:79"],
      "suggested_resolution": "레포 공개 URL 확정 후 PLAN 또는 EXECUTE 단계에서 일괄 치환"
    }
  ]
}
```

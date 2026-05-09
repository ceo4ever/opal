# PLAN: 배포 채널 정비 + Get Started UX 통합 (139)

> 작성일: 2026-05-08 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (3개 기능 = 영역 그룹 G1/G2/G3)
> 영역 그룹 분할 근거: ANALYSIS R8 (영역 11종 단일 PLAN 비대화) + TASK §위험 R1

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL을 **불특정 다수에게 안전하고 일관되게 배포**하기 위한 1차 배포 채널(GitHub Releases + one-liner installer + `opal-cli` 단일 진입점)을 구축하고, **설치 직후 첫 사용자 경험(Get Started)을 단일 시나리오**(부트스트랩 cwd 분기 + `//start` 재진입 가이드 + onboarding 트리거 보강)로 정비한다. 캡틴 확정 결정 D1·D2를 기반으로 구현한다.

> **[MUST]** `tasks/139-260508-opp-distribute-and-getstarted/TASK.md ## 캡틴 확정 결정 사항`: "D1 바이너리 명칭 = `opal-cli` — Homebrew core `opal`(opalrb) 충돌 회피 / D2 GitHub 레포 URL = `https://github.com/ceo4ever/opal`"

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | G1 배포 인프라 (install/CLI/doctor) | TASK 영역 A·B·C·D·E | P0 | 없음 |
| F-002 | G2 Get Started UX (부트스트랩/스킬/온보딩) | TASK 영역 F·G·H | P0 | F-001 (CLI doctor 호출 의존) |
| F-003 | G3 문서·CI (README/Release Workflow/변경이력) | TASK 영역 I·J·K | P0 | F-001, F-002 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (G1 배포 인프라)
  ├─ A install bootstrap (install.sh / install.ps1)
  ├─ B install 본체 분리 (install/macos.sh)
  ├─ C opal-cli 진입점 (install/update/doctor/uninstall/mcp)
  ├─ D PATH 등록 + ~/.opal/bin/opal-cli
  └─ E doctor 도구
        │
        ▼
F-002 (G2 UX) ────────── doctor 호출 의존
  ├─ F 부트스트랩 cwd 분기 (opal/core/AGENT.md)
  ├─ G //start 재진입 스킬
  └─ H opal-onboarding triggers 보강
        │
        ▼
F-003 (G3 문서·CI) ───── 실제 명령/구조 확정 후 문서화
  ├─ I README §설치 4 Step + one-liner 삽입
  ├─ J GitHub Release Workflow (.github/workflows/release.yml)
  └─ K ARCHITECTURE.md §배포 채널 "예정" → "현행" + 변경이력 동기화
```

---

## 2. 기능별 분석

### F-001: G1 배포 인프라

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.sh` | macOS/Linux 통합 one-liner 진입 부트스트랩 (tarball 다운로드·검증·플랫폼별 install 호출) | 신규 |
| 배치 | `scripts/install.ps1` | Windows one-liner 진입 부트스트랩 (irm/iex 패턴) | 신규 |
| 배치 | `scripts/install/macos.sh` | 현행 install-mac.sh의 함수 분해 결과 (재배치) | 신규 (B 리팩) |
| 배치 | `scripts/install-mac.sh` | install_opal/install_opal_section/strip_deploy_md_recursive 등 — D 영역 PATH 등록 + 신규 도구 디렉토리 strip 호출 추가 | 수정 |
| 환경 | `opal/tools/opal-cli/run.sh` | `opal-cli` 진입점 디스패처 (install/update/doctor/uninstall/mcp 서브커맨드) | 신규 |
| 환경 | `opal/tools/opal-cli/lib/install.sh` | install 서브커맨드 — 1차 설치 재실행 (scripts/install/macos.sh 호출) | 신규 |
| 환경 | `opal/tools/opal-cli/lib/update.sh` | update 서브커맨드 — release tarball 재다운로드 + 사용자 데이터 보존 + `--to vX.Y` 핀 옵션 | 신규 |
| 환경 | `opal/tools/opal-cli/lib/doctor.sh` | doctor 서브커맨드 — `opal/tools/doctor/run.sh` 위임 | 신규 |
| 환경 | `opal/tools/opal-cli/lib/uninstall.sh` | uninstall 서브커맨드 — `~/.opal/` 제거 + 부트스트래퍼 마커 회수 | 신규 |
| 환경 | `opal/tools/opal-cli/lib/mcp.sh` | mcp 서브커맨드 — install_mcp() 로직 래핑 호출 | 신규 |
| 환경 | `opal/tools/opal-cli/README.md` | opal-cli 사용법 (서브커맨드, 옵션, 예시) | 신규 |
| 환경 | `opal/tools/doctor/run.sh` | doctor 본체 — 의존성/경로/MCP/부트스트래퍼 정합성 점검 | 신규 |
| 환경 | `opal/tools/doctor/lib/checks.sh` | 개별 체크 함수 (check_deps / check_paths / check_mcp / check_bootstrappers) | 신규 |
| 환경 | `opal/tools/doctor/README.md` | doctor 사용법 + 출력 포맷 | 신규 |

근거: `tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md §1.1` (관련 파일 목록), `scripts/install-mac.sh:637-804` (install_opal 호출 그래프), `scripts/install-mac.sh:182-199` (strip_deploy_md_recursive)

#### 2.1.2 현재 구현

ANALYSIS §1.2~§1.3에 기록된 현행 흐름:

- **install_opal() 메인 오케스트레이터** — `scripts/install-mac.sh:637-804` (`detect_framework_root` → `mkdir ~/.opal` → 사용자 데이터 보존 후 framework 디렉토리 클린 → AGENT/skills/agents/templates/tools/venv/references/community-skills/hooks/bootstrappers/permissions/플랫폼 어댑터 순차 호출). 호출 그래프가 ANALYSIS §1.3 install-mac.sh 핵심 호출 그래프에 명시됨.
- **strip_deploy_md_recursive** — `scripts/install-mac.sh:192-199` 구현, 호출 위치 `scripts/install-mac.sh:675` (`~/.opal/skills` 직후), `:707` (`~/.opal/agents` 직후), `:894` (`~/.opal/references` 직후). 신규 `~/.opal/tools/opal-cli/`, `~/.opal/tools/doctor/`에 `*.md` 파일이 생기지만 `install_dir "$opal_dir/tools" "$opal_home/tools"` (`scripts/install-mac.sh:717-718`) 직후 `strip_deploy_md_recursive` 호출이 없음 → 신규 호출 추가 필요. (→ D-2 §4 핵심 발견 #2)
- **install_opal_section / extract_bootstrap_content** — `scripts/install-mac.sh:201-285` — 부트스트래퍼 OPAL/R2 마커 호환 교체 로직.
- **strip_deploy_md** — `scripts/install-mac.sh:184-188` — `## 변경이력` 섹션 이후 strip.
- **사용자 데이터 보존** — `scripts/install-mac.sh:646-654` (clean_dirs = skills/agents/references/community-skills/templates/tools, 보존 = identity.md, AGENT.md, projects/). 신규 `opal-cli update`는 이 정책을 그대로 따르되 `community-skills/`·`tools/` 사용자 커스텀 경로 처리 방침을 명문화해야 함 (R4).
- **부트스트래퍼 마커** — `scripts/install-mac.sh:25-32` (`OPAL_START` / `OPAL_END` / `R2_START` / `R2_END` / `HARDENING_START` / `HARDENING_END`). uninstall은 OPAL/R2 마커 블록만 제거하고 파일 자체는 보존해야 함.

신규 구성요소:
- **scripts/install.sh / install.ps1** — 부재 확인됨 (ANALYSIS §1.1). curl-to-shell·irm/iex 표준 패턴 적용 (→ D-13, D-14).
- **opal-cli / doctor** — 부재 확인됨. 모두 신규.

#### 2.1.3 영향 범위

- **install_opal() 함수 호출 그래프 보존 의무** (ANALYSIS §3.2) — `scripts/install-mac.sh:637-804` 호출 순서 변경 금지 — `[MUST]` `tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md §3.2`: "install_opal() 내 함수 호출 순서 변경 금지"
- **strip_deploy_md_recursive 적용 범위 확장** — 신규 `opal/tools/opal-cli/`, `opal/tools/doctor/` 경로의 .md 파일이 `~/.opal/tools/` 배포 후에 누락되지 않도록 호출 추가 필요 (`scripts/install-mac.sh:717-718` 직후).
- **PATH 등록 셸 분기** — `~/.zshrc` / `~/.bashrc` / `~/.profile` (fish 사용자 안내) idempotent 처리 (R2). 현행 `detect_user()`는 홈 디렉토리만 처리하므로 신규 함수 추가.
- **opal-cli 명칭 충돌 회피** — `opal-cli`로 결정(D1)되어 Homebrew core `opal`(opalrb)와 PATH 충돌 회피.
- **uninstall 시 파일 보존** — CLAUDE.md / GEMINI.md는 OPAL/R2 마커 블록만 제거, 파일 자체는 보존 (ANALYSIS §3.2 부트스트래퍼 마커 호환성).

---

### F-002: G2 Get Started UX

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md` | Eager Step 7 직전 cwd 분기 (a/b next-action) 보강 | 수정 |
| 스킬 | `opal/skills/opal-start/SKILL.md` | `//start` 재진입 가이드 — 현재 상태 진단 → 다음 액션 권유 | 신규 |
| 스킬 | `opal/skills/opal-start/references/start-flow.md` | 상태 진단·라우팅 흐름 가이드 | 신규 |
| 스킬 | `opal/skills/opal-onboarding/SKILL.md` | frontmatter `triggers:` 키 신설 + Step 1 환영 메시지에 //start 안내 보강 | 수정 |
| 문서 | `opal/core/references/skills.md` | opal-start 등록 (기술 스택별 추천 / 공통 표 갱신 검토) | 수정 |

근거: `tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md §1.1` (관련 파일 목록), `opal/core/AGENT.md:11-19` (Eager Step), `opal/skills/opal-onboarding/SKILL.md:1-6` (frontmatter)

#### 2.2.2 현재 구현

- **부트스트랩 Eager 단계** — `opal/core/AGENT.md:11-19` Step 1~7. Step 7 "정체성 + 하네스 + PM 행동 프로세스 + PM 컨텍스트 기반으로 에이전트를 활성화한다" 직전이 cwd 분기 삽입 위치 (ANALYSIS §4 핵심 발견 #3).
- **부트스트랩 완료 보고** — `opal/core/AGENT.md:44-54` 한 줄 체크리스트 출력. 분기 결과(a/b)를 이 보고 직후 한 줄 next-action 라인으로 추가하면 기존 출력 형식을 유지하면서 안내 가능.
- **역할 전환** — `opal/core/AGENT.md:87-114` — 이미 `.opal/AGENT.md` 존재 여부로 비서/PM 자동 전환을 정의. cwd 분기는 이 자동 전환 결과를 사용자에게 가시화하는 역할.
- **opal-onboarding** — `opal/skills/opal-onboarding/SKILL.md:1-6` frontmatter에 `triggers:` 키 자체 부재 (ANALYSIS §4 핵심 발견 #4). `description`만으로 트리거되며 `//onboarding` 명시 호출 진입점이 없음. Step 1 환영 메시지(`opal/skills/opal-onboarding/SKILL.md:32-39`)는 작업 완료 후 //start로 재진입 가능함을 안내하지 않음.
- **opal-start** — 부재 확인됨. 신규.

#### 2.2.3 영향 범위

- **부트스트랩 출력 형식 비파괴 의무** — `opal/core/AGENT.md:44-54`의 `[부트스트랩] ✅ ... ⏳ ...` 한 줄 형식은 유지하고, next-action 라인은 별도 줄로 추가한다.
- **Lazy 트리거 테이블 정합성** — `opal/core/AGENT.md:21-36` Lazy 테이블에 `//start` 항목을 신설하지 않고, `//`커맨드 입력 시 `harness/skill-commands.md` 로드로 자동 매칭되므로 별도 행 추가 불필요 (테이블 행 추가 시 기존 7행 패턴 깨짐).
- **opal-onboarding triggers 추가 범위** — frontmatter에 `triggers: ["//onboarding", "정체성 재설정", "온보딩 다시"]` 형태. Step 11 부트스트래퍼 삽입 절차(`opal/skills/opal-onboarding/SKILL.md:212-246`)에 영향 없음.
- **skills.md 등록** — `opal/core/references/skills.md`는 기술 스택별 추천 표만 있고 OPAL 자체 스킬 목록은 별도 등록 영역이 없음. opal-skills-registry.json이 SSOT (`opal/core/references/skills.md:3-7`)이므로 JSON 레지스트리에도 opal-start 추가 필요. 단, 이 태스크 범위에서 JSON 갱신은 install 시 자동 동기화되는지 확인 후 결정.

---

### F-003: G3 문서·CI

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `README.md` | §설치 4 Step + one-liner (mac/linux/win) + `{REPO_URL}` → `https://github.com/ceo4ever/opal` 치환 | 수정 |
| 환경 | `.github/workflows/release.yml` | 태그 push → tarball + sha256sums.txt + attest-build-provenance | 신규 |
| 문서 | `docs/ARCHITECTURE.md` | §배포 채널 "예정" → "현행" 전환 + 외부 의존 서비스 정합성 | 수정 |
| 문서 | `opal/core/AGENT.md` 변경이력 | (139) 행 추가 | 수정 |
| 문서 | `opal/skills/opal-onboarding/SKILL.md` 변경이력 | (139) 행 추가 | 수정 |
| 문서 | 신규 스킬·도구 변경이력 | opal-start, opal-cli, doctor 초기 변경이력 행 | 신규 |

근거: `tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md §1.1` (관련 파일 목록), `README.md:78-82` (`{REPO_URL}` 플레이스홀더), `docs/ARCHITECTURE.md:241-250` (배포 채널 예정 표)

#### 2.3.2 현재 구현

- **README §설치** — `README.md:78-82` `git clone {REPO_URL} opal` + `./scripts/install-mac.sh` 안내. one-liner 명령 전무. `README.md:64-141`이 전체 §설치 섹션. (→ D-2 §3.2 의존성 흐름)
- **.github/workflows/** — 디렉토리 자체 부재 (ANALYSIS §1.4) → CI 최초 도입.
- **docs/ARCHITECTURE.md §배포 채널 (예정)** — `docs/ARCHITECTURE.md:241-250`에 4행 표 (GitHub Releases / opal CLI / Homebrew / npm) + "결정 근거: 태스크 138(opi) 검토 → 후속 태스크 139에서 구현 PLAN 수립 예정" 주석. 1차 항목은 "현행"으로 전환, 2차/후속 항목은 "예정" 유지.
- **변경이력** — 컨벤션 (`docs/CONVENTIONS.md ## 변경이력 작성 의무`) — 일시 KST + 태스크 번호 (139) 포함. 배포 시 `install-mac.sh strip_deploy_md`가 자동 strip하므로 소스에는 유지.

#### 2.3.3 영향 범위

- **README ↔ install.sh ↔ Workflow 정합성** — README의 one-liner URL이 release.yml의 자산 경로 + install.sh의 fetch URL과 일치해야 함. 모두 `https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.{sh,ps1}` 패턴 (→ D-13, D-14 + D2).
- **ARCHITECTURE.md 외부 의존 서비스 정합성** — `docs/ARCHITECTURE.md:208-240` "외부 의존 서비스" 섹션의 MCP·Python·Node.js 항목은 변경 없음. §배포 채널만 "예정" → "현행" 전환.
- **변경이력 누락 금지** — `docs/CONVENTIONS.md ## 변경이력 작성 의무` + `.opal/AGENT.md ## 금지사항`: "변경이력 누락 금지". F-001/F-002에서 수정·신규되는 모든 SKILL/AGENT 산출물에 (139) 행 자동 추가 의무.

---

## 3. 기능별 설계

### F-001: G1 배포 인프라

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `scripts/install.sh` | 배치 | macOS/Linux 통합 one-liner 진입 (tarball 다운로드 → 체크섬 검증 → uname 분기 → install/macos.sh 호출) | (→ D-13) |
| 2 | `scripts/install.ps1` | 배치 | Windows one-liner 진입 (Invoke-RestMethod tarball 다운로드 → 체크섬 → install/windows.ps1 호출) | (→ D-14) |
| 3 | `scripts/install/macos.sh` | 배치 | install-mac.sh 함수 그룹 분해 결과 (B 리팩 시 위치) — 단계적 마이그레이션 우선 wrapper만 신설 | (→ D-1 영역 B) |
| 4 | `opal/tools/opal-cli/run.sh` | 환경 | 진입점 디스패처 — `opal-cli {install\|update\|doctor\|uninstall\|mcp} [args...]` | (→ D-1 영역 C) |
| 5 | `opal/tools/opal-cli/lib/install.sh` | 환경 | install 서브커맨드 (재실행) | - |
| 6 | `opal/tools/opal-cli/lib/update.sh` | 환경 | update 서브커맨드 (--to vX.Y, 사용자 데이터 보존) | (→ D-12) |
| 7 | `opal/tools/opal-cli/lib/doctor.sh` | 환경 | doctor 서브커맨드 (위임) | - |
| 8 | `opal/tools/opal-cli/lib/uninstall.sh` | 환경 | uninstall 서브커맨드 (~/.opal/ 제거 + 부트스트래퍼 마커 회수) | `scripts/install-mac.sh:25-32` |
| 9 | `opal/tools/opal-cli/lib/mcp.sh` | 환경 | mcp 서브커맨드 (install_mcp 래핑) | `scripts/install-mac.sh:966-1056` |
| 10 | `opal/tools/opal-cli/README.md` | 문서 | opal-cli 사용법 | - |
| 11 | `opal/tools/doctor/run.sh` | 환경 | doctor 본체 | (→ D-1 영역 E) |
| 12 | `opal/tools/doctor/lib/checks.sh` | 환경 | 개별 체크 함수 모음 | - |
| 13 | `opal/tools/doctor/README.md` | 문서 | doctor 사용법 + 출력 포맷 | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배치 | (a) `install_opal()` 말미에 `install_opal_bin()` 호출 추가 — `~/.opal/bin/opal-cli` symlink 생성 + `~/.opal/bin/`을 PATH에 추가하는 셸 rc 분기 함수 신설 / (b) `~/.opal/tools/` 배포(`scripts/install-mac.sh:717-718`) 직후 `strip_deploy_md_recursive "$opal_home/tools"` 호출 추가 / (c) 기존 호출 그래프(`:637-804`) 변경 금지 | `scripts/install-mac.sh:637-804` (호출 그래프 보존), `scripts/install-mac.sh:675,707,894` (strip 패턴), `scripts/install-mac.sh:25-32` (마커) |

근거 단축 참조: D-1=ANALYSIS.md, D-5=install-mac.sh, D-12=attest-build-provenance, D-13=curl-pipe-bash, D-14=PowerShell irm/iex.

#### 3.1.2 API·데이터 모델·화면 설계

##### opal-cli 진입점 시그니처

```bash
# 사용법
opal-cli install                        # 처음 설치 (one-liner 외 수동 진입점)
opal-cli update [--to vX.Y]             # 업데이트 (사용자 데이터 보존)
opal-cli doctor                         # 진단
opal-cli uninstall                      # 제거 (~/.opal + 부트스트래퍼 마커)
opal-cli mcp [add|list|remove] [name]   # MCP 관리 (install_mcp 래핑)
opal-cli --version                      # 버전 출력 (release tag)
opal-cli --help                         # 사용법 출력

# 진입 경로
~/.opal/bin/opal-cli  →  ~/.opal/tools/opal-cli/run.sh (symlink)
```

`run.sh`는 첫 인자로 서브커맨드를 받아 `lib/{서브커맨드}.sh`에 위임한다. 알 수 없는 서브커맨드는 `--help` 표시 후 exit 1. (→ D-13 표준 보안 패턴)

> **[MUST]** `tasks/139-260508-opp-distribute-and-getstarted/TASK.md ## 캡틴 확정 결정 사항`: "D1 바이너리 명칭 = `opal-cli`" — PATH 등록은 `~/.opal/bin/opal-cli`이며 `opal`(opalrb 충돌 회피)을 사용하지 않는다.

##### one-liner installer 표준 보안 패턴

`scripts/install.sh` 기본 골격 (→ D-13):

```bash
#!/usr/bin/env bash
set -euo pipefail

OPAL_REPO="${OPAL_REPO:-ceo4ever/opal}"           # D2
OPAL_VERSION="${OPAL_VERSION:-main}"              # 또는 vX.Y 태그
TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/heads/${OPAL_VERSION}.tar.gz"
SHA_URL="https://github.com/${OPAL_REPO}/releases/download/${OPAL_VERSION}/sha256sums.txt"

main() {
  detect_platform              # uname → macos | linux
  check_deps                   # bash, git, curl, tar
  fetch_tarball                # curl -fsSL --proto '=https' --tlsv1.2
  verify_checksum              # sha256sum -c (SHA_URL이 존재할 때)
  extract_to_tmp
  exec_platform_installer      # macos.sh / linux.sh
}

main "$@"
```

> **[MUST]** `tasks/139-260508-opp-distribute-and-getstarted/TASK.md ## 캡틴 확정 결정 사항`: "D2 GitHub 레포 URL = `https://github.com/ceo4ever/opal`" — One-liner: `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh \| bash` / PowerShell: `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1)`.

##### scripts/install.ps1 진입 골격 (→ D-14)

```powershell
$ErrorActionPreference = 'Stop'
$OpalRepo    = if ($env:OPAL_REPO)    { $env:OPAL_REPO    } else { 'ceo4ever/opal' }
$OpalVersion = if ($env:OPAL_VERSION) { $env:OPAL_VERSION } else { 'main' }

function Test-Deps { ... }    # git, tar, sha256
function Fetch-Tarball { ... }
function Verify-Checksum { ... }
function Invoke-PlatformInstaller { ... }

Test-Deps
Fetch-Tarball
Verify-Checksum
Invoke-PlatformInstaller
```

ExecutionPolicy 안내(R5): README §설치 — `iex (irm ...)` 사용 시 정책이 `Restricted`이면 `powershell -ExecutionPolicy ByPass -c "irm <URL> | iex"` 패턴 명시. (→ D-14)

##### install_opal_bin 신규 함수 (D 영역, scripts/install-mac.sh 수정)

```bash
install_opal_bin() {
    local bin_dir="$USER_HOME/.opal/bin"
    local cli_target="$USER_HOME/.opal/tools/opal-cli/run.sh"

    [[ -f "$cli_target" ]] || { warn "opal-cli/run.sh 부재 — bin 생성 스킵"; return; }
    chmod +x "$cli_target"
    mkdir -p "$bin_dir"
    ln -sfn "$cli_target" "$bin_dir/opal-cli"
    success "opal-cli 심볼릭 링크 → $bin_dir/opal-cli"

    register_path_in_shell_rc "$bin_dir"
}

# zsh / bash / fish 안내 분기 (R2 완화)
register_path_in_shell_rc() {
    local bin_dir="$1"
    local marker="# === OPAL PATH ==="
    local rc_files=("$USER_HOME/.zshrc" "$USER_HOME/.bashrc" "$USER_HOME/.profile")
    local export_line='export PATH="$HOME/.opal/bin:$PATH"'

    for rc in "${rc_files[@]}"; do
        [[ -f "$rc" ]] || continue
        if grep -qF "$marker" "$rc"; then
            success "PATH 이미 등록됨: $rc"
            continue
        fi
        printf '\n%s\n%s\n%s\n' "$marker" "$export_line" "# === OPAL PATH END ===" >> "$rc"
        success "PATH 등록 → $rc"
    done

    # fish는 별도 안내 (config.fish 구조 다름)
    if command -v fish &>/dev/null; then
        info "fish 사용자: ~/.config/fish/config.fish 에 다음 줄을 추가하세요:"
        info "  set -gx PATH \$HOME/.opal/bin \$PATH"
    fi
}
```

근거: `scripts/install-mac.sh:25-32` (마커 패턴 — OPAL PATH 마커도 동일 컨벤션 적용), `scripts/install-mac.sh:184-188` (strip 안전성 — `## 변경이력`이 아니므로 영향 없음).

##### doctor 출력 포맷

```text
[OPAL Doctor]

[1/4] Dependencies
  ✓ bash 5.2.x
  ✓ git 2.43.x
  ✓ Node.js v18.x
  ✓ Python 3.11.x

[2/4] OPAL Paths
  ✓ ~/.opal/AGENT.md
  ✓ ~/.opal/identity.md
  ✓ ~/.opal/skills/ (29 skills)
  ✓ ~/.opal/agents/ (10 agents)
  ✓ ~/.opal/bin/opal-cli  → ~/.opal/tools/opal-cli/run.sh

[3/4] MCP Registration
  ✓ Claude: context7, playwright, shadcn, sequential-thinking
  ✓ Cursor: context7, playwright (mcp.json)
  ✓ Gemini: context7, playwright

[4/4] Bootstrappers
  ✓ ~/.claude/CLAUDE.md (OPAL marker)
  ✓ ~/.cursor/rules/000-opal-agent.mdc
  ✓ ~/.gemini/GEMINI.md (OPAL + HARDENING markers)

판정: All Pass (0 warnings, 0 errors)
```

오류/경고 시 `Fail`/`Warn`을 표시하고, exit code 1/0로 구분하여 CI에서 활용 가능하게 한다. (→ D-12 attestation 검증 단계와 연동)

##### update 시 사용자 데이터 보존 정책 (R4 완화)

`opal-cli update`는 다음 정책을 따른다:

| 항목 | 처리 |
|------|------|
| `~/.opal/identity.md` | 보존 (덮어쓰기 금지) |
| `~/.opal/AGENT.md` | install_opal()의 `strip_deploy_md` 결과로 덮어쓰기 (사용자 편집 금지 영역) |
| `~/.opal/projects/` | 보존 |
| `~/.opal/skills/` | 클린 후 재배포 (커스텀 스킬은 `~/.opal/skills.user/` 별도 영역으로 이동 — 후속 태스크) |
| `~/.opal/agents/` | 클린 후 재배포 |
| `~/.opal/community-skills/` | 보존 (사용자가 추가 vendor 디렉토리 둘 가능) — `cp -Rf` 덮어쓰기, 추가 vendor 디렉토리는 유지 |
| `~/.opal/tools/` | 클린 후 재배포 (사용자 커스텀 도구는 `~/.opal/tools.user/` 별도 영역 — 후속 태스크) |
| `~/.opal/bin/opal-cli` | symlink 재생성 |
| `~/.opal/.venv/` | 보존 + requirements.txt 재적용 (`install_opal_venv` 정책 따라) |

근거: `scripts/install-mac.sh:646-654` 현행 보존 정책 + ANALYSIS R4 완화. `~/.opal/skills.user/`·`~/.opal/tools.user/` 분리는 본 태스크 범위 외이며, update 매뉴얼에 "사용자 커스텀 스킬은 현재 update 시 보존되지 않으니 별도 디렉토리 보관 권장" 경고 표시.

#### 3.1.3 환경 변경

- **신규 패키지**: 없음 (Bash/PowerShell 표준만 사용 — TASK §R5)
- **신규 환경 변수**: `OPAL_REPO`(기본 `ceo4ever/opal`), `OPAL_VERSION`(기본 `main` 또는 release tag)
- **PATH 변경**: `~/.opal/bin`을 `~/.zshrc`/`~/.bashrc`/`~/.profile`에 export 라인 idempotent 추가 (마커 `# === OPAL PATH ===` / `# === OPAL PATH END ===`)

#### 3.1.4 배치/마이그레이션

- B 영역 함수 분해: 본 태스크에서는 `scripts/install/macos.sh` wrapper만 신설(현행 install-mac.sh를 source하여 호출)하고, 함수 그룹별 분해는 호출 그래프 보존을 위해 후속 리팩 태스크로 분리 권장 (R3 — 단일 PR 실패 롤백 폭 축소).
- 기존 사용자 환경: `opal-cli update` 첫 실행 시 OPAL/R2 마커 호환 그대로 작동 (`scripts/install-mac.sh:255-274`).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | TASK S1 (mac one-liner 신규 설치) | 통합 테스트 | `curl -fsSL .../install.sh \| bash` 실행 → `~/.opal/` 생성, `~/.opal/bin/opal-cli` symlink, 재실행 시 idempotent |
| TS-002 | TASK S5 (`opal update`) | 통합 테스트 | `opal-cli update` 실행 → `~/.opal/identity.md` 보존, `~/.opal/skills/` 갱신, `--to v0.1` 핀 옵션 동작 |
| TS-003 | TASK S6 (`opal doctor` mac) | 기능 테스트 | `opal-cli doctor` → 4 섹션 모두 출력, exit 0, 일부 결손 시 exit 1 |
| TS-004 | TASK S7 (`opal uninstall`) | 통합 테스트 | `opal-cli uninstall` → `~/.opal/` 제거, CLAUDE.md/GEMINI.md OPAL 블록 회수, 파일 자체 보존 |
| TS-005 | TASK S8 (Linux 신규 설치) | 통합 테스트 | Linux Bash 환경에서 install.sh → `~/.opal/` 정상 생성 |
| TS-006 | TASK S9 (Windows 신규 설치) | 통합 테스트 | PowerShell `irm \| iex` → `~/.opal/` 생성 (이미지/VM에서 1회 검증) |
| TS-007 | ANALYSIS R2 (셸 분기) | 산출물 검사 | `~/.zshrc`·`~/.bashrc`·`~/.profile` 중 존재하는 파일 모두에 OPAL PATH 마커 1회만 추가 (idempotent) |
| TS-008 | ANALYSIS R3 (strip 누락) | 산출물 검사 | `~/.opal/tools/opal-cli/`·`~/.opal/tools/doctor/` 하위 .md에 `## 변경이력` 섹션 부재 |
| TS-009 | ANALYSIS R4 (update 보존 범위) | 기능 테스트 | update 후 `~/.opal/identity.md`·`projects/` 보존, `skills/`·`agents/` 갱신 |
| TS-010 | ANALYSIS §3.2 (호출 그래프 보존) | 산출물 검사 | install-mac.sh:637-804 함수 호출 순서가 변경 전/후 동일 (diff 점검) |
| TS-011 | ANALYSIS R1 (PATH 충돌) | 산출물 검사 | `which opal-cli` → `~/.opal/bin/opal-cli`, Homebrew opalrb 환경에서 `which opal` → opalrb 그대로 (간섭 없음) |

---

### F-002: G2 Get Started UX

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-start/SKILL.md` | 스킬 | `//start` 진입점 — 현재 상태 진단 + 다음 액션 권유 | (→ D-1 영역 G) |
| 2 | `opal/skills/opal-start/references/start-flow.md` | 가이드 | 진단 흐름 + 분기 라우팅 가이드 | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 에이전트 | (a) Eager Step 7 직전에 cwd 분기 라인 추가 — `.opal/AGENT.md` 존재 시 (a) "//opi 권유" / 미존재 시 (b) "비서 모드 + 보조 안내" / (b) "부트스트랩 완료 보고" 출력 직후 next-action 한 줄 추가 / (c) 변경이력 (139) 행 | `opal/core/AGENT.md:11-19`, `:44-54` |
| 2 | `opal/skills/opal-onboarding/SKILL.md` | 스킬 | (a) frontmatter `triggers: ["//onboarding", "정체성 재설정", "온보딩 다시"]` 신설 / (b) Step 9 완료 후 `//start` 안내 1줄 추가 / (c) 변경이력 (139) 행 | `opal/skills/opal-onboarding/SKILL.md:1-6`, `:150-167` |
| 3 | `opal/core/references/skills.md` | 문서 | OPAL 자체 스킬 목록(또는 하단 참조 섹션)에 opal-start 추가 (skill-registry JSON SSOT 보조) | `opal/core/references/skills.md:1-7` |

#### 3.2.2 API·데이터 모델·화면 설계

##### 부트스트랩 cwd 분기 삽입 위치 (opal/core/AGENT.md)

`opal/core/AGENT.md:11-19` Eager 단계 Step 7 "정체성 + 하네스 + ... 활성화한다" 직전에 Step 6.5(또는 Step 7 사전 처리)로 다음을 삽입:

```markdown
6.5. 현재 작업 디렉토리(cwd)를 판별하여 next-action 라인을 결정한다:
   - `.opal/AGENT.md`가 존재 → 이 cwd는 OPAL 프로젝트 → next-action = "프로젝트 작업이라면 `//opi` 또는 `//opp/opd/opds` 등으로 진입하세요"
   - `.opal/AGENT.md` 미존재 → 이 cwd는 비프로젝트 → next-action = "프로젝트 초기화는 `//opi`, 일반 비서 작업은 자연어로 요청하세요"
```

`opal/core/AGENT.md:44-54` "부트스트랩 완료 보고" 한 줄 체크리스트 직후에 다음 한 줄을 추가:

```
[안내] {next-action}
```

근거: `opal/core/AGENT.md:11-19`, `:44-54` + ANALYSIS §4 핵심 발견 #3 ("Eager Step 7 직전이 cwd 분기 삽입 위치"). 기존 출력 형식과 Lazy 트리거 테이블을 건드리지 않는다.

##### //start 스킬 frontmatter

```yaml
---
name: opal-start
description: |
  **재진입 가이드 스킬** — 현재 OPAL 환경 상태를 진단하여 사용자에게 다음 액션을 권유한다. //start, "시작", "처음부터" 등으로 호출된다.
triggers:
  - "//start"
  - "시작"
  - "처음부터"
version: 1.0.0
---
```

##### //start 프로세스

```markdown
### Step 1: 환경 진단

다음을 순차 점검:
1. ~/.opal/identity.md 존재? → 없으면 → opal-onboarding 위임
2. ~/.opal/AGENT.md 존재? → 없으면 → "OPAL 미설치" 안내 (one-liner 명령)
3. cwd에 .opal/AGENT.md 존재? → 분기 결정 (a/b)
4. 의심 가는 결손 → opal-cli doctor 실행 권유 (CLI 미설치 시 직접 ~/.opal/tools/doctor/run.sh 실행 안내)

### Step 2: 분기별 안내

(a) 프로젝트 폴더:
  "현재 OPAL 프로젝트입니다. 다음 중 선택하세요:
   - //opi    프로젝트 정의 갱신
   - //opp    범용 작업 (문서/설정)
   - //opds   개발 Short Task
   - //opd    개발 Full Task
   - opal-cli doctor    환경 진단"

(b) 비프로젝트:
  "현재 비프로젝트 위치입니다.
   - //opi    여기에 OPAL 프로젝트 초기화
   - 또는 자연어로 비서에게 작업 요청"
```

근거: ANALYSIS §1.1 (skill 부재) + TASK §검증시나리오 S11.

##### opal-onboarding triggers (수정)

`opal/skills/opal-onboarding/SKILL.md:1-6` frontmatter에 `triggers:` 키 신설:

```yaml
---
name: onboarding
description: |
  **OPAL AI 에이전트 초기 정체성 설정 스킬**. ...
triggers:
  - "//onboarding"
  - "정체성 재설정"
  - "온보딩 다시"
---
```

근거: ANALYSIS §4 핵심 발견 #4 ("frontmatter에 triggers 키 자체가 없어 명시적 재호출 진입점이 없다") + `opal/skills/opal-onboarding/SKILL.md:1-6`.

#### 3.2.3 환경 변경

- 추가 패키지: 없음
- 환경 변수: 없음
- skill-registry JSON 갱신: install 시 자동 동기화되는지(`opal/core/references/opal-skills-registry.json` 빌드 절차) 확인. 자동 미지원 시 PLAN Step에 수동 갱신 항목 추가.

#### 3.2.4 배치/마이그레이션

- 해당 없음 (마크다운 변경만)

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | TASK S1·S2 (부트스트랩 체크리스트) | 산출물 검사 | 새 세션 첫 응답에 `[부트스트랩] ✅ identity ...` + `[안내] {next-action}` 두 줄 표시 |
| TS-013 | TASK S2 (identity 미존재 → onboarding 자동 발화) | 기능 테스트 | identity.md 부재 상태에서 신규 세션 → opal-onboarding Step 1 환영 메시지 출력 |
| TS-014 | TASK S3 (a 분기) | 기능 테스트 | `cd <프로젝트>/` (·.opal/AGENT.md 존재) 후 신규 세션 → next-action에 `//opi` 권유 포함 |
| TS-015 | TASK S4 (b 분기) | 기능 테스트 | `cd ~` (.opal/AGENT.md 없음) 후 신규 세션 → 비서 모드 + 보조 안내 표시 |
| TS-016 | TASK S11 (//start 재진입) | 기능 테스트 | `//start` → 환경 진단 결과 출력 + 다음 액션 권유 (a/b 분기) |
| TS-017 | ANALYSIS §4 #4 (triggers 추가) | 산출물 검사 | `opal/skills/opal-onboarding/SKILL.md` frontmatter에 `triggers:` 키 존재 + skill-registry match가 `//onboarding`을 onboarding 스킬에 매칭 |

---

### F-003: G3 문서·CI

#### 3.3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `.github/workflows/release.yml` | 환경 | 태그 push 트리거 → tarball + sha256sums.txt 생성 + actions/attest-build-provenance v2 서명 | (→ D-12) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `README.md` | 문서 | (a) `README.md:79`의 `git clone {REPO_URL} opal` → `https://github.com/ceo4ever/opal` 치환 / (b) §설치를 4 Step으로 정리: ① one-liner 실행 / ② 부트스트랩 체크리스트 확인 / ③ //opi 또는 //start 진입 / ④ 트러블슈팅 / (c) mac/linux/win 별 one-liner 명령 명시 | `README.md:64-141`, TASK D2 |
| 2 | `docs/ARCHITECTURE.md` | 문서 | §배포 채널 4행 표(`docs/ARCHITECTURE.md:241-250`)에서 GitHub Releases / opal-cli 행을 "현행"으로, Homebrew tap / npm 행은 "예정" 유지. 결정 근거 주석 갱신 (138 검토 → 139 구현 완료) | `docs/ARCHITECTURE.md:241-250` |
| 3 | `opal/core/AGENT.md` | 문서 | 변경이력 표에 (139) 행 추가 — Eager Step 6.5 cwd 분기 삽입 + 부트스트랩 보고 next-action 라인 | `opal/core/AGENT.md:295-307` |
| 4 | `opal/skills/opal-onboarding/SKILL.md` | 문서 | 변경이력 행 추가 (139) | `opal/skills/opal-onboarding/SKILL.md` |
| 5 | `opal/core/references/skills.md` | 문서 | opal-start 등록 (해당 시 변경이력 동기화) | `opal/core/references/skills.md:1-7` |

#### 3.3.2 API·데이터 모델·화면 설계

##### .github/workflows/release.yml 골격 (→ D-12)

```yaml
name: release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write
  id-token: write
  attestations: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build tarball
        run: |
          TAG="${GITHUB_REF_NAME}"
          ARCHIVE="opal-${TAG}.tar.gz"
          tar --exclude='.git' --exclude='tasks' -czf "$ARCHIVE" .
          sha256sum "$ARCHIVE" > sha256sums.txt
      - uses: actions/attest-build-provenance@v2
        with:
          subject-checksums: sha256sums.txt
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            opal-*.tar.gz
            sha256sums.txt
```

근거: [actions/attest-build-provenance v2](https://github.com/actions/attest-build-provenance) — `subject-checksums: sha256sums.txt`로 SHA-256 체크섬 목록 자동 attestation. 검증 명령 `gh attestation verify <artifact> --repo ceo4ever/opal`.

##### README §설치 4 Step 골격 (수정)

```markdown
## 설치

### Step 1: 사전 요구사항 확인

| 항목 | 요구사항 |
|------|---------|
| OS | macOS / Linux / Windows |
| 필수 도구 | bash(또는 PowerShell), git, Node.js v18+, Python 3 |
| AI 플랫폼 | Claude Code, Cursor, Gemini (Antigravity) |

### Step 2: One-liner 설치

**macOS / Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh | bash
```

**Windows (PowerShell)**
```powershell
iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1)
```

`Restricted` 정책 환경에서는:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1 | iex"
```

### Step 3: 부트스트랩 체크리스트 확인

AI 도구를 재시작하면 첫 응답에 다음과 같이 표시된다:
```
[부트스트랩] ✅ identity ✅ harness ✅ PM ⏳ registry ⏳ references ⏳ model-mapping
[안내] 프로젝트 작업이라면 `//opi` 또는 `//opp/opd/opds`로 진입하세요
```

### Step 4: 다음 단계

- 프로젝트 초기화: `//opi`
- 재진입 가이드: `//start`
- 환경 진단: `opal-cli doctor`
```

근거: TASK §결정사항 + D2 + ANALYSIS §4 #5 (`README.md:79` `{REPO_URL}` 미완성).

##### docs/ARCHITECTURE.md §배포 채널 갱신

```markdown
### 배포 채널

| 채널 | 단계 | 상태 | 비고 |
|------|------|------|------|
| GitHub Releases | 1차 | **현행** | 태그 기반 tarball + sha256sums.txt + attestation, one-liner 진입점 |
| `opal-cli` CLI | 1차 | **현행** | `install`/`update`/`doctor`/`uninstall`/`mcp` 단일 진입점 (~/.opal/bin/opal-cli) |
| Homebrew tap | 2차 | 예정 | macOS 사용자 대상 `brew install opal-cli` (명칭은 별도 결정) |
| npm 패키지 | 후속 | 예정 | cross-platform 통합 |

> 결정 근거: 태스크 138 검토 → 139에서 1차 채널 구현 완료 (캡틴 결정 D1·D2).
```

근거: `docs/ARCHITECTURE.md:241-250` 현행 표 + TASK D1·D2 + ANALYSIS §1.1.

#### 3.3.3 환경 변경

- 신규: `.github/workflows/release.yml` (CI 파이프라인 최초 도입)
- GitHub Repository Settings: Releases 권한 + id-token write 권한 (workflow permissions에서 처리, repo settings 변경 불필요)

#### 3.3.4 배치/마이그레이션

- v0.1 첫 release 태그 push 시 release.yml 1회 검증 (TASK S10)
- 기존 README의 `{REPO_URL}` 참조는 단일 치환 (다른 곳에 동일 플레이스홀더가 있는지 grep으로 사전 점검)

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | TASK S10 (Release Workflow) | 통합 테스트 | `git tag v0.1 && git push origin v0.1` → release.yml 실행 → tarball + sha256sums.txt + attestation 생성, GitHub Release 페이지에 업로드 |
| TS-019 | ANALYSIS R6 (REPO_URL 미확정) | 산출물 검사 | `git grep '{REPO_URL}'` 결과 0건 (모두 ceo4ever/opal로 치환) |
| TS-020 | TASK §결정사항 (현행 전환) | 산출물 검사 | `docs/ARCHITECTURE.md`의 §배포 채널 표에 GitHub Releases·opal-cli가 "현행"으로 표기 |
| TS-021 | `docs/CONVENTIONS.md ## 변경이력 작성 의무` | 산출물 검사 | 모든 수정·신규 SKILL/AGENT/참조 문서에 (139) 변경이력 행 존재 |
| TS-022 | TASK S6 doctor (CI 호출) | 통합 테스트 | release.yml 안에서 doctor 또는 install dry-run 단계가 통과 (선택 — release.yml에 sanity check 추가 시) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| 1 | F-001 | 1~7 | 순차 (파일 의존) — 일부 병렬 가능 | G1 배포 인프라 — F-002 doctor 호출 의존이므로 먼저 |
| 2 | F-002 | 8~12 | F-001 완료 후 순차 | G2 UX — F는 G로 부트스트랩 분기, G·H는 독립이므로 G/H 병렬 가능 |
| 3 | F-003 | 13~18 | F-001·F-002 완료 후 순차 | G3 문서·CI — 실제 명령·구조 확정 후 문서화 |

### 4.2 실행 체크리스트

> 총 18개 Step | Phase 3개 | 실행 모드: **복잡** (Step 18, 변경 파일 25+, 다중 모듈, 신규 개발, 외부 의존성 GitHub Actions/curl/PowerShell)

#### Step 1: scripts/install/macos.sh wrapper 신설 (B 영역 부분 진입)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install/macos.sh` (신규)
- **작업 내용**: 현행 `scripts/install-mac.sh`를 source하는 wrapper 스크립트 신설. 함수 그룹별 분해는 후속 리팩 태스크로 분리(R3 롤백 폭 축소). 본 Step은 install.sh가 호출할 수 있는 진입점 제공이 목적.
- **완료 기준**: `bash scripts/install/macos.sh` 실행 시 install-mac.sh와 동일 동작 (대화형 메뉴 표시)
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: scripts/install-mac.sh 수정 (D 영역 PATH 등록 + strip 확장)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  1. `install_opal_bin()` + `register_path_in_shell_rc()` 함수 신설 (§3.1.2 코드 골격 참조)
  2. `install_opal()` 말미(`scripts/install-mac.sh:803` 직전)에 `install_opal_bin` 호출 추가
  3. `~/.opal/tools/` 배포(`scripts/install-mac.sh:717-718`) 직후 `strip_deploy_md_recursive "$opal_home/tools"` 호출 추가
  4. 기존 호출 그래프(`:637-804`) 변경 금지 — 추가만 허용
- **완료 기준**: install-mac.sh 재실행 → `~/.opal/bin/opal-cli` symlink 존재 (단, opal-cli/run.sh 부재 시 warn 출력 후 스킵 — Step 3 이전), `~/.zshrc`에 OPAL PATH 마커 1회만 추가
- **테스트**: TS-007, TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 가능, 단 install_opal_bin은 Step 3 후 동작)

#### Step 3: opal/tools/opal-cli/ 신규 구현 (C 영역)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/run.sh`, `opal/tools/opal-cli/lib/{install,update,doctor,uninstall,mcp}.sh`, `opal/tools/opal-cli/README.md`
- **작업 내용**:
  - `run.sh` 디스패처 — 첫 인자로 서브커맨드 받아 `lib/{서브커맨드}.sh` 실행, `--version`/`--help` 처리
  - `lib/install.sh` — `scripts/install/macos.sh` 또는 install-mac.sh 호출
  - `lib/update.sh` — release tarball 재다운로드 + 사용자 데이터 보존 (§3.1.2 update 정책) + `--to vX.Y` 핀
  - `lib/doctor.sh` — `~/.opal/tools/doctor/run.sh` 위임
  - `lib/uninstall.sh` — `~/.opal/` 제거 + CLAUDE.md/GEMINI.md OPAL/R2 마커 블록 제거 (`scripts/install-mac.sh:25-32`)
  - `lib/mcp.sh` — install_mcp 로직 래핑 (`scripts/install-mac.sh:966-1056` 참조)
  - 모든 .sh 파일 상단에 @header 블록 + 변경이력 라인 (CONVENTIONS §@header 규칙)
  - README.md에 (139) 초기 변경이력 행
- **완료 기준**: `~/.opal/tools/opal-cli/run.sh install --help` 동작, doctor 위임 정상
- **테스트**: TS-002, TS-004
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 4 doctor와 독립이지만 doctor 호출 link는 Step 4 완료 후 동작)

#### Step 4: opal/tools/doctor/ 신규 구현 (E 영역)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/tools/doctor/run.sh`, `opal/tools/doctor/lib/checks.sh`, `opal/tools/doctor/README.md`
- **작업 내용**:
  - `run.sh` — 4 섹션 순차 출력 (Dependencies / Paths / MCP / Bootstrappers)
  - `lib/checks.sh` — `check_deps`, `check_paths`, `check_mcp`, `check_bootstrappers` 함수 (§3.1.2 출력 포맷)
  - exit code: 0(All Pass) / 1(Fail or Warn)
  - @header + 변경이력 (139) 신설
- **완료 기준**: `~/.opal/tools/doctor/run.sh` 정상 환경에서 4섹션 모두 ✓ + exit 0, AGENT.md 삭제 시 exit 1 + 해당 행 ✗
- **테스트**: TS-003
- **실행 방법**: sub-agent
- **의존**: Step 2 (PATH 등록 후 사용자가 `opal-cli doctor`로 호출 가능)

#### Step 5: scripts/install.sh 신규 (A 영역 — macOS/Linux)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.sh`
- **작업 내용**: §3.1.2 골격 (set -euo pipefail / detect_platform / check_deps / fetch_tarball / verify_checksum / extract_to_tmp / exec_platform_installer). curl 플래그 `-fsSL --proto '=https' --tlsv1.2`. `OPAL_REPO`(기본 `ceo4ever/opal`), `OPAL_VERSION`(기본 `main`).
- **완료 기준**: `bash scripts/install.sh` 로컬 실행 → tarball 다운로드 시도 (네트워크 의존). dry-run 모드(`OPAL_DRY_RUN=1`)에서 실제 fetch 없이 흐름 검증.
- **테스트**: TS-001, TS-005
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3 (install/macos.sh + opal-cli 존재 후 의미 있음)

#### Step 6: scripts/install.ps1 신규 (A 영역 — Windows)

- [x] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.ps1`
- **작업 내용**: §3.1.2 골격. `Test-Deps` / `Fetch-Tarball` / `Verify-Checksum` / `Invoke-PlatformInstaller`. ExecutionPolicy 안내는 README §설치에 별도 (Step 13).
- **완료 기준**: PowerShell `Set-StrictMode -Version 3.0` 환경에서 syntax 검증 통과 (PSScriptAnalyzer 권장). 실제 실행은 TS-006(Windows VM)에서 검증.
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1 (install/macos.sh와 대칭으로 install/windows.ps1 wrapper 별도 신설 — 본 Step 범위에 포함)

#### Step 7: F-001 통합 검증

- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: (검증 전용)
- **작업 내용**: `./scripts/install-mac.sh` 1번 메뉴 실행 → `~/.opal/bin/opal-cli` 심볼릭 링크 + `opal-cli doctor` 실행 → 4섹션 정상 출력 + exit 0. zsh/bash 두 환경에서 PATH 등록 idempotent 확인.
- **완료 기준**: TS-001, TS-003, TS-007, TS-008, TS-010, TS-011 모두 Pass
- **테스트**: TS-001, TS-003, TS-007, TS-008, TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3, 4

#### Step 8: opal/core/AGENT.md cwd 분기 + 부트스트랩 보고 next-action (F 영역)

- [x] 완료
- **소속 기능**: F-002
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:
  1. `:11-19` Eager 단계 사이에 Step 6.5(cwd 분기) 1단락 추가 (§3.2.2 마크다운 골격)
  2. `:44-54` 부트스트랩 완료 보고 한 줄 체크리스트 직후 `[안내] {next-action}` 라인 추가
  3. 변경이력(`:295-307`) 표에 (139) 행 추가 (KST 일시 + 변경내용)
  4. Lazy 트리거 테이블 비변경 (기존 7행 보존)
- **완료 기준**: TS-012(부트스트랩 보고 형식 비파괴 + next-action 1줄 추가), TS-014/TS-015(a/b 분기 메시지 정확)
- **테스트**: TS-012, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: Phase 1 완료

#### Step 9: opal/skills/opal-start/ 신규 (G 영역)

- [x] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-start/SKILL.md`, `opal/skills/opal-start/references/start-flow.md`
- **작업 내용**: §3.2.2 frontmatter + Step 1·2 프로세스. references/start-flow.md에 진단·라우팅 흐름 상세. (139) 변경이력 초기 행.
- **완료 기준**: `node ~/.opal/tools/skill-registry/skill-registry.js match "//start"`가 `opal-start` 매칭 (skill-registry JSON 동기화 후)
- **테스트**: TS-016
- **실행 방법**: sub-agent
- **의존**: Phase 1 완료 (doctor 호출 안내 의존)

#### Step 10: opal/skills/opal-onboarding/SKILL.md triggers + 환영 메시지 보강 (H 영역)

- [x] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-onboarding/SKILL.md`
- **작업 내용**:
  1. frontmatter `triggers: ["//onboarding", "정체성 재설정", "온보딩 다시"]` 신설 (`:1-6`)
  2. Step 9 완료 메시지(`:154-166`) 직후 "다음에 다시 정체성을 변경하려면 `//start` 또는 `//onboarding`을 사용하세요" 1줄 추가
  3. 변경이력 표에 (139) 행 추가
- **완료 기준**: TS-017
- **테스트**: TS-013, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 9 (//start 안내 일관성)

#### Step 11: opal/core/references/skills.md 갱신

- [x] 완료 (2026-05-09, PM 직접)
- **소속 기능**: F-002
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/core/references/opal-skills-registry.json` (SSOT 갱신, version 3.3.0 → 3.4.0)
- **작업 내용**: opal-start를 opal 그룹에 추가 (alias: start, triggers 3종). skills.md는 기술 스택 추천 영역이라 별도 갱신 불필요.
- **완료 기준**: ✅ JSON SSOT의 opal 그룹 entries 8 → 9, opal-start present
- **테스트**: TS-016
- **실행 방법**: direct
- **의존**: Step 9

#### Step 12: F-002 통합 검증

- [x] 완료 (2026-05-09, 정적 검증 + skill-registry 소스 JSON 시뮬레이션)
- **소속 기능**: F-002
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: (검증 전용)
- **작업 내용**: 실제 신규 세션을 가정한 대화 시뮬레이션 — 프로젝트 폴더 cwd, 비프로젝트 cwd 두 환경에서 부트스트랩 보고 결과 차이 확인. `//start`, `//onboarding` 호출 시 매칭 동작 확인.
- **완료 기준**: TS-012, TS-013, TS-014, TS-015, TS-016, TS-017 모두 Pass
- **테스트**: TS-012~TS-017
- **실행 방법**: sub-agent
- **의존**: Step 8, 9, 10, 11

#### Step 13: README.md §설치 4 Step 갱신 (I 영역)

- [x] 완료 (2026-05-09, PM 직접)
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `README.md`
- **작업 내용**:
  1. `README.md:79`의 `{REPO_URL}` 치환 — `https://github.com/ceo4ever/opal`
  2. §설치(`:64-141`)를 Step 1~4로 재구성 (§3.3.2 골격)
  3. mac/linux/win one-liner 명령 명시 (§3.3.2 골격)
  4. ExecutionPolicy 안내 1줄 추가
- **완료 기준**: TS-019(`{REPO_URL}` 0건), 외부 사용자가 README만 보고 설치 가능
- **테스트**: TS-019
- **실행 방법**: direct
- **의존**: Phase 1, 2 완료

#### Step 14: .github/workflows/release.yml 신규 (J 영역)

- [x] 완료
- **소속 기능**: F-003
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `.github/workflows/release.yml`
- **작업 내용**: §3.3.2 골격 (태그 push 트리거 / tarball / sha256sums / attest-build-provenance v2 / softprops/action-gh-release@v2)
- **완료 기준**: YAML 문법 검증 통과 (yamllint 또는 GitHub Actions schema). 실제 검증은 v0.1 태그 push 시 (TS-018).
- **테스트**: TS-018
- **실행 방법**: sub-agent
- **의존**: Phase 1 완료 (release 자산 = ~/.opal/ 배포 결과 의미를 갖기 위해)

#### Step 15: docs/ARCHITECTURE.md §배포 채널 갱신 (K 영역)

- [x] 완료 (2026-05-09, PM 직접)
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: `:241-250` 표를 §3.3.2 골격으로 갱신. GitHub Releases·opal-cli "현행", Homebrew·npm "예정". 결정 근거 주석 갱신.
- **완료 기준**: TS-020
- **테스트**: TS-020
- **실행 방법**: direct
- **의존**: Phase 1, 2 완료

#### Step 16: 변경이력 동기화 (K 영역)

- [x] 완료 (2026-05-09, PM 직접) — 19개 영향 파일에 (139) 표기 일관 + install-mac.sh:11 "task 139" → "(139)" 정정
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/core/AGENT.md`, `opal/skills/opal-onboarding/SKILL.md` (신규는 Step 3·4·9·10에서 일괄 처리됨)
- **작업 내용**: Step 8·10에서 누락된 변경이력 보완. 모든 영향 SKILL/AGENT/참조 문서에 (139) 행 + KST 일시 + 변경내용 정합성 확인. `git grep -l '(139)'` 결과와 영향 파일 목록 일치 확인.
- **완료 기준**: TS-021
- **테스트**: TS-021
- **실행 방법**: direct
- **의존**: Step 8, 10, 13, 15

#### Step 17: 첫 release 태그 push 검증 (J 영역)

- [ ] 완료
- **소속 기능**: F-003
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: (운영 검증)
- **작업 내용**: v0.1 태그 push → release.yml 실행 → tarball + sha256sums.txt + attestation 생성 확인. `gh attestation verify opal-v0.1.tar.gz --repo ceo4ever/opal` Pass.
- **완료 기준**: TS-018, TS-022
- **테스트**: TS-018, TS-022
- **실행 방법**: direct (캡틴 명시 승인 후 실제 태그 push)
- **의존**: Step 14

#### Step 18: 프로젝트 메모리 갱신

- [x] 완료 (2026-05-09 09:07, PM 직접) — .opal/MEMORY.md 작업 히스토리에 139 (P1) 완료 행 추가
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `.opal/MEMORY.md`, `.opal/memory/feedback_*.md` (해당 시)
- **작업 내용**: 1차 배포 채널 가동 + opal-cli 명칭 결정 + 부트스트랩 분기 도입을 메모리 항목으로 기록. 후속 태스크 예약(Homebrew tap, npm 패키지, install-mac.sh 함수 분해 리팩) 노트.
- **완료 기준**: 메모리 인덱스에 신규 항목 등록
- **테스트**: -
- **실행 방법**: direct
- **의존**: Step 17 완료 + 캡틴 검토

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일 (install/macos.sh wrapper vs install-mac.sh 수정) |
| Step 3 ∥ Step 4 | 독립 디렉토리 (opal-cli vs doctor) — 단 Step 4가 먼저 완료되면 Step 3 doctor 위임 검증이 동시 가능 |
| Step 5, Step 6 → Step 1·3 | install.sh / install.ps1는 install/macos.sh wrapper + opal-cli가 존재해야 의미 |
| Step 7 → Steps 1~6 | F-001 통합 검증은 모든 신규 컴포넌트 후 |
| Step 8·9·10 (G2 내) | Step 9 → Step 10 (//start 안내가 onboarding Step에 인용됨), Step 8 ∥ Step 9 (독립 파일) |
| Step 11 → Step 9 | skills.md 갱신은 opal-start 신규 후 |
| Step 12 → Steps 8~11 | F-002 통합 검증 |
| Step 13 → Phase 1·2 | README는 실제 명령·구조 확정 후 |
| Step 14 → Phase 1 | release.yml 자산 의미 = ~/.opal/ 배포 결과 |
| Step 15·16 → Steps 8~14 | 문서·변경이력 정합성 |
| Step 17 → Step 14 | 실제 태그 push 검증 |
| Step 18 → Step 17 | 메모리 갱신은 최종 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | one-liner 신규 설치 mac | TS-001 | `~/.opal/`·`~/.opal/bin/opal-cli` 정상, 재실행 idempotent |
| F-001 | `opal-cli update` 사용자 데이터 보존 | TS-002, TS-009 | identity.md·projects/ 보존, skills/·agents/ 갱신 |
| F-001 | `opal-cli doctor` 4섹션 출력 | TS-003 | All Pass + exit 0, 결손 시 Fail + exit 1 |
| F-001 | `opal-cli uninstall` 부트스트래퍼 마커 회수 | TS-004 | `~/.opal/` 제거, CLAUDE.md/GEMINI.md OPAL 블록 제거, 파일 보존 |
| F-001 | Linux 신규 설치 | TS-005 | install.sh Linux uname 분기 정상 |
| F-001 | Windows 신규 설치 | TS-006 | install.ps1 정상 + ExecutionPolicy 안내 |
| F-001 | 셸 분기 idempotent (R2) | TS-007 | zsh/bash/profile 모두 마커 1회만 |
| F-001 | strip 누락 방지 (R3) | TS-008 | 신규 tools 배포본에 변경이력 부재 |
| F-001 | 호출 그래프 보존 (§3.2) | TS-010 | install_opal() 호출 순서 변경 없음 |
| F-001 | PATH 충돌 회피 (R1) | TS-011 | opal-cli vs opalrb 간섭 없음 |
| F-002 | 부트스트랩 next-action 보고 | TS-012 | 한 줄 체크리스트 + [안내] 라인 출력 |
| F-002 | identity 미존재 자동 발화 | TS-013 | onboarding Step 1 환영 메시지 출력 |
| F-002 | (a) 프로젝트 분기 | TS-014 | `//opi` 권유 포함 |
| F-002 | (b) 비프로젝트 분기 | TS-015 | 비서 모드 + 보조 안내 표시 |
| F-002 | `//start` 재진입 | TS-016 | 환경 진단 + 다음 액션 권유 |
| F-002 | onboarding triggers 추가 | TS-017 | skill-registry match 동작 |
| F-003 | Release Workflow 가동 | TS-018 | tarball + sha256sums + attestation 생성 |
| F-003 | `{REPO_URL}` 치환 완료 | TS-019 | git grep 결과 0 |
| F-003 | ARCHITECTURE.md "현행" 전환 | TS-020 | §배포 채널 표 갱신 |
| F-003 | 변경이력 정합성 | TS-021 | 영향 파일 모두 (139) 행 |
| F-003 | release.yml sanity check | TS-022 | (선택) attestation 검증 Pass |

### 5.2 회귀 테스트

- [ ] 기존 `./scripts/install-mac.sh` 메뉴 1·2·3·4·0 모두 변경 전과 동일 동작 (호출 그래프 보존)
- [ ] 기존 ~/.opal/ 배포 사용자 환경에서 `opal-cli update` 실행 시 OPAL/R2 마커 호환 교체 정상 (`scripts/install-mac.sh:255-274`)
- [ ] 기존 부트스트랩 체크리스트(`opal/core/AGENT.md:44-54`) 한 줄 형식 유지 — `[안내]` 라인은 별도 줄로 추가만
- [ ] Lazy 트리거 테이블(`opal/core/AGENT.md:21-36`) 7행 그대로 보존
- [ ] 기존 opal-onboarding의 자동 발화 경로(identity.md 부재 시) 동작 보존 — triggers 추가는 명시 호출 보강만

### 5.3 코드/문서 품질

- [ ] 프로젝트 컨벤션 준수 (`docs/CONVENTIONS.md`) — kebab-case 폴더명, @header 블록, 변경이력 행
- [ ] `[MUST]` 토큰: 캡틴 결정 D1·D2 원문 인용 (§1.1)
- [ ] PLAN.md §3.N.5 테스트 시나리오와 §5.1 QA 매트릭스의 TS-ID 일치
- [ ] 모든 신규/수정 SKILL/AGENT/참조 문서에 변경이력 (139) 행

### 5.4 보안

- [ ] one-liner installer는 TLS 강제 (`curl -fsSL --proto '=https' --tlsv1.2`) — D-13 패턴 적용 확인
- [ ] sha256 체크섬 검증 단계 누락 없음 (verify_checksum)
- [ ] release.yml `permissions:` 최소 권한 (contents: write, id-token: write, attestations: write — 그 외 명시적으로 read)
- [ ] `.gitignore`에 `.opal/.venv/`, `tasks/*/STATE.md` 등 의도치 않은 자산 제외 점검 (현행 그대로 유지 가정)
- [ ] PowerShell 스크립트에 하드코딩 비밀 없음
- [ ] uninstall 시 `~/.opal/identity.md` 명시 보존(또는 사용자 확인) — 실수 데이터 손실 방지

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 18개 | 복잡 |
| 변경 파일 수 | 25+개 (신규 13, 수정 12+) | 복잡 |
| 모듈 범위 | scripts/ + opal/tools/ + opal/skills/ + opal/core/ + .github/ + docs/ + README + 다중 레이어 | 복잡 |
| 작업 유형 | 신규 개발(배포 채널 + CLI + doctor + 스킬) + 대규모 개선 | 복잡 |
| 외부 의존성 | GitHub Actions, curl, PowerShell, attest-build-provenance v2 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬 가능 — F-001 신규 컴포넌트)
  ├─ A1: opal-task-agent — Step 1 (scripts/install/macos.sh wrapper)
  ├─ A2: opal-task-agent — Step 2 (install-mac.sh PATH + strip 확장)
  ├─ A3: opal-task-agent — Step 3 (opal-cli/)
  └─ A4: opal-task-agent — Step 4 (doctor/)

Batch 2 (Batch 1 의존 — F-001 통합)
  ├─ A5: opal-task-agent — Step 5 (install.sh)
  ├─ A6: opal-task-agent — Step 6 (install.ps1)
  └─ A7: opal-task-agent — Step 7 (F-001 통합 검증)

Batch 3 (F-002 — Phase 1 완료 후)
  ├─ A8: opal-task-agent — Step 8 (AGENT.md cwd 분기) ∥ A9: Step 9 (opal-start)
  ├─ A10: opal-task-agent — Step 10 (onboarding triggers)
  ├─ A11: PM 직접 — Step 11 (skills.md)
  └─ A12: opal-task-agent — Step 12 (F-002 통합 검증)

Batch 4 (F-003 — Phase 1·2 완료 후)
  ├─ A13: PM 직접 — Step 13 (README)
  ├─ A14: opal-task-agent — Step 14 (release.yml)
  ├─ A15: PM 직접 — Step 15 (ARCHITECTURE.md)
  ├─ A16: PM 직접 — Step 16 (변경이력 동기화)
  ├─ A17: opal-task-agent — Step 17 (태그 push 검증, 캡틴 승인 후)
  └─ A18: PM 직접 — Step 18 (메모리 갱신)
```

**그룹핑 우선순위 적용**:
- 파일 충돌 방지: Step 2(install-mac.sh)와 Step 1(install/macos.sh)은 다른 파일 — 충돌 없음
- 모듈 응집도: opal-cli 하위 lib/*.sh는 Step 3 단일 에이전트 처리 (파일 충돌 방지)
- 병렬 극대화: Batch 1 4개 에이전트 병렬 가능

### C-2. 스킬 요구사항

| 영역 | 스킬 | 매칭 |
|------|------|------|
| Bash 스크립트 | (인라인 지침 — Bash·sh 표준 패턴) | 갭 없음 |
| PowerShell | (인라인 지침 — Microsoft.PowerShell 모듈 표준) | 갭 없음 |
| GitHub Actions | (인라인 지침 — actions/attest-build-provenance v2 사용 패턴) | 갭 없음 |
| SKILL.md·AGENT.md 마크다운 | OPAL 컨벤션 준수 (`docs/CONVENTIONS.md`) | 갭 없음 |
| TEST 단계 | op-dev-test-agent (별도 트리거) | 갭 없음 |

> 본 태스크에서 3개 이상 Step에서 동일 패턴 반복은 없음 — 신규 스킬 도출 불필요. 모두 인라인 지침으로 처리.

### C-3. 도구 요구사항

| 도구 | 용도 | 비고 |
|------|------|------|
| `curl` | one-liner installer 다운로드 | 표준 |
| `tar` | tarball 압축/해제 | 표준 |
| `sha256sum` (mac: `shasum -a 256`) | 체크섬 검증 | 표준 |
| `gh` CLI | attestation 검증 (TS-018) | 사용자 환경 권장 (CI는 자동) |
| GitHub Actions: `actions/checkout@v4`, `actions/attest-build-provenance@v2`, `softprops/action-gh-release@v2` | release.yml | 외부 의존 |
| context7 MCP | actions/attest-build-provenance v2 최신 사용법 (필요 시) | 선택 |

### C-4. 테스트 전략

op-dev-test-agent 디스패치 시 검증 모드 (BE/FE/E2E 중) → **BE 모드(스크립트·문서 중심)**.

- **기능 테스트**: TS-001~TS-022 시나리오를 각 Phase 완료 시점에 실행. 운영체제·플랫폼 의존 시나리오(TS-005 Linux, TS-006 Windows, TS-018 CI)는 별도 환경에서 1회 검증.
- **회귀 테스트**: install-mac.sh 메뉴 1·2·3·4 동작 변경 전후 비교. ANALYSIS §1.3 호출 그래프 ASCII와 실제 호출 순서 diff.
- **코드 품질**: shellcheck (Bash), PSScriptAnalyzer (PowerShell), yamllint (release.yml), markdownlint (README/AGENT/SKILL).
- **보안**: 하드코딩 시크릿 스캔(`git grep -E "password|token|api_key|secret" -- '*.sh' '*.ps1' '*.yml'` Pass), `.gitignore`에 `.opal/identity.md` 보호 (단, 본 프로젝트는 deploy 소스이므로 보호 대상 없음).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 셸 (mac/linux) | Bash | 인라인 지침 |
| 셸 (windows) | PowerShell | 인라인 지침 |
| 패키지 (Python venv) | Python 3.x + requirements.txt | 인라인 지침 |
| 패키지 (CLI 도구) | Node.js 18+ | 인라인 지침 |
| CI | GitHub Actions | 인라인 지침 |
| 마크다운 | OPAL CONVENTIONS | `docs/CONVENTIONS.md` |
| 체크섬 | sha256 + actions/attest-build-provenance v2 | `[attest-build-provenance](https://github.com/actions/attest-build-provenance)` |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 (선택) | actions/attest-build-provenance v2 최신 사용법 — `subject-checksums` 입력 / SLSA 빌드 출처 서명 / `gh attestation verify` (ANALYSIS §2.1) |

> 본 태스크 PLAN 작성 시 MCP 호출은 ANALYSIS 단계에서 이미 수행됨 (D-12, D-13, D-14 외부 인용). PLAN 단계에서 추가 호출 불필요.

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ANALYSIS.md | `tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md` | 영역 11종·관련 파일 맵·핵심 발견·R1~R8·decision_required |
| D-2 | 설계 | TASK.md | `tasks/139-260508-opp-distribute-and-getstarted/TASK.md` | 결정사항 + 캡틴 확정(D1·D2) + 검증 시나리오 S1~S11 + R1~R5 |
| D-3 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 2-Layer 모델 + 외부 의존 서비스 + 배포 채널 (예정) |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙 (Guards/디스패치/@header/Citation/State/도구·배포 경계·플랫폼 분기) + 변경이력 작성 의무 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 현행 1173줄 — 마커·strip·install_opal·플랫폼 어댑터 |
| D-6 | 소스 | core/AGENT.md | `opal/core/AGENT.md` | Eager/Lazy 부트스트랩 + cwd 분기 삽입 위치 |
| D-7 | 소스 | opal-onboarding SKILL.md | `opal/skills/opal-onboarding/SKILL.md` | 트리거·환영 메시지·재설정 절차 |
| D-8 | 소스 | README.md | `README.md` | §설치 4 Step 갱신 대상 + `{REPO_URL}` 치환 위치 |
| D-9 | 설계 | citation-rules.md | `~/.opal/references/harness/citation-rules.md` | 인용 포맷 규칙 + [MUST] 토큰 + 트랙별 매트릭스 |
| D-10 | 설계 | agents.md | `~/.opal/references/agents.md` | 전문 에이전트 매핑 테이블 + agent 필드 배정 규칙 |
| D-11 | 외부 | Homebrew formula opal | [opal — Homebrew Formulae](https://formulae.brew.sh/formula/opal) | `opal` 명칭 충돌 점검 — D1 결정 근거 |
| D-12 | 외부 | actions/attest-build-provenance | [attest-build-provenance v2](https://github.com/actions/attest-build-provenance) | release.yml attestation 구현 패턴 |
| D-13 | 외부 | curl-pipe-bash 보안 패턴 | [How to build a trustworthy curl pipe bash workflow](https://operous.dev/blog/how-to-build-a-trustworthy-curl-pipe-bash-workflow/) | one-liner installer TLS·체크섬·idempotent |
| D-14 | 외부 | PowerShell irm/iex 패턴 | [PowerShell One-Liners for Installation](https://knowledge.buka.sh/powershell-one-liners-for-installation-what-does-irm-bun-sh-install-ps1-iex-really-do/) | install.ps1 표준 패턴 + ExecutionPolicy |

> 인용 형식: `~/.opal/references/harness/citation-rules.md` §3.1·§3.2 참조. 본문 §2·§3에서 `(→ D-N)` 단축 참조 또는 `` `경로:줄번호` `` 풀 포맷을 혼용한다.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-A1 | install_opal() 호출 그래프 변경 시 기존 사용자 환경 회귀 | F-001 | 높음 | Step 2에 "추가만 허용, 기존 호출 순서 변경 금지" 명시. TS-010(diff 점검) Pass 필수 |
| R-A2 | strip_deploy_md_recursive 호출 누락 → 배포본에 변경이력 노출 (ANALYSIS R3) | F-001 | 중간 | Step 2 (c) 항목 명시 — `~/.opal/tools/` 직후 호출 추가. TS-008 Pass 필수 |
| R-A3 | `~/.opal/bin/opal-cli` PATH 등록이 zsh/bash/fish 환경별 차등 동작 (ANALYSIS R2) | F-001 | 중간 | §3.1.2 `register_path_in_shell_rc` 함수가 zsh/bash/profile 모두에 idempotent 추가, fish는 별도 안내. TS-007 Pass |
| R-A4 | `opal-cli update` 사용자 데이터 보존 범위 미정 (ANALYSIS R4) | F-001 | 중간 | §3.1.2 update 정책 표 명문화. 사용자 커스텀 스킬은 본 태스크 범위 외 — 매뉴얼에 경고 명시 |
| R-A5 | Windows ExecutionPolicy `Restricted` 환경에서 `irm \| iex` 실패 (ANALYSIS R5) | F-001, F-003 | 중간 | install.ps1 본체에는 우회 불포함, README §설치에 `-ExecutionPolicy ByPass` 안내 1줄 (Step 13) |
| R-A6 | Windows VM 검증 1회 부담 (TASK R5) | F-001 | 낮음 | TS-006은 1회 통과로 충분 처리, 후속 태스크에서 정기 회귀 |
| R-B1 | 부트스트랩 보고 형식 변경이 기존 사용자에 혼란 | F-002 | 중간 | `[부트스트랩] ... ` 한 줄은 보존, `[안내] ...`는 별도 줄로 추가만 (Step 8 작업 내용 명시) |
| R-B2 | Lazy 트리거 테이블 변경 시 부트스트랩 비정상 위험 | F-002 | 중간 | Step 8 작업 내용에 "Lazy 트리거 테이블 비변경" 명시 |
| R-B3 | opal-skills-registry.json 자동 동기화 미지원 시 //start 매칭 실패 | F-002 | 중간 | Step 11에서 JSON 갱신 또는 install 시 자동 빌드 메커니즘 확인. 미지원 시 매뉴얼 갱신 |
| R-C1 | release.yml 첫 실행 시 권한·시크릿 오류 (CI 최초 도입) | F-003 | 중간 | Step 17 캡틴 명시 승인 후 v0.1 태그 push, 실패 시 권한 설정 점검. permissions 최소화로 사전 방어 |
| R-C2 | `{REPO_URL}` 치환 누락 (ANALYSIS R6) | F-003 | 중간 | TS-019 산출물 검사 — `git grep '{REPO_URL}'` 0건 |
| R-C3 | 변경이력 누락 (CONVENTIONS 의무) | F-003 | 중간 | Step 16 정합성 검토. TS-021 산출물 검사 |
| R-C4 | npm `opal` 방치 패키지 후속 충돌 (ANALYSIS R7) | F-003 후속 | 낮음 | 본 태스크 out-of-scope. 후속 Homebrew/npm 채널 태스크에서 명칭 결정 시 재검토 |
| R-C5 | ARCHITECTURE.md "현행" 전환 시 후속 채널(Homebrew/npm) 정합성 | F-003 | 낮음 | §3.3.2 골격 — Homebrew/npm은 "예정" 유지 |
| R-D1 | 영역 11종 단일 PLAN 비대화 (ANALYSIS R8) | 전 기능 | 낮음 | 본 PLAN을 G1/G2/G3 3개 Feature로 분할 — §1.2·§1.3에 명시 |

# PLAN: Linux 설치 스크립트 신설 — scripts/install/linux.sh

> 작성일: 2026-05-20 | 입력: TASK.md | 출력: PLAN.md
> 적용 스킬: opp | 모드: agentic | 태스크: 006

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install 메인 디스패처 | `scripts/install.sh` | Linux 분기 호출 경로(`exec_platform_installer`) 정의 위치 + fallback 안내 라인 326~333 |
| D-2 | 소스 | macOS wrapper | `scripts/install/macos.sh` | Linux wrapper 구현 패턴 직접 참조 (44줄, exec 위임 패턴) |
| D-3 | 소스 | macOS 실제 설치 로직 | `scripts/install-mac.sh` | Linux 호환성 판단 + 재사용 가능 부분 식별 (1345줄) |
| D-4 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 폴더 구조맵 / 네이밍 규칙 |
| D-5 | 기획 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` | source/runtime 구분 + 어댑터 계층 원칙 |
| D-6 | 기획 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 셸 스크립트 작성 규칙 / 변경이력 / @header / 플랫폼 분기 격리 |
| D-7 | 기획 | 보안 모델 | `docs/SECURITY.md` | curl-pipe-bash 보안 패턴 / sha256 / `set -euo pipefail` / OPAL_HOME 가드 |
| D-8 | PM | PM 프로필 | `.opal/AGENT.md` | 금지사항 / 배포 경계 / 변경이력 의무 |
| D-9 | 외부 | Playwright Linux 캐시 경로 | [Playwright Docs — Browsers/Managing](https://playwright.dev/docs/browsers#managing-browser-binaries) | Linux의 기본 캐시 경로(`~/.cache/ms-playwright`) 확인 근거 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `scripts/install.sh` | 메인 디스패처 (플랫폼 감지 + tarball 검증) | **수정** (Linux fallback 제거) | `scripts/install.sh:325-335` (fallback 블록) |
| `scripts/install/macos.sh` | macOS wrapper (`install-mac.sh`로 exec) | 변경 없음 (참조용) | `scripts/install/macos.sh:1-44` |
| `scripts/install/linux.sh` | **신규** Linux wrapper | **신규 생성** | - |
| `scripts/install-mac.sh` | 실제 설치 로직 (1345줄) | 변경 없음 (이번 태스크 범위 밖) | `scripts/install-mac.sh:1-1345` |
| `scripts/install/windows.ps1` | Windows 진입점 | 변경 없음 (참조용) | - |

### `install-mac.sh` 함수별 Linux 호환성 정밀 분석

이 표는 M-1(구현 전략) 결정의 핵심 근거다. 1345줄 전체를 함수 단위로 분류한다.

| # | 함수 / 라인 | 역할 | macOS 의존성 | Linux 호환 분류 |
|---|------------|------|-------------|----------------|
| F-1 | `print_banner` (55-62) | 배너 출력 | "(macOS)" 텍스트 라벨 | 부분 호환 (라벨만 macOS 명시) |
| F-2 | `detect_framework_root` (64-76) | 프레임워크 루트 탐지 | 없음 — `BASH_SOURCE`/`dirname` 사용 | **Linux 호환** |
| F-3 | `detect_user` (78-107) | 사용자/홈 디렉토리 결정 | 없음 — `$HOME`/`whoami` 표준 | **Linux 호환** |
| F-4 | `show_menu` (109-120) | 대화형 메뉴 | 없음 — `read -rp` | **Linux 호환** |
| F-5 | `merge_mcp_config` (124-154) | MCP JSON 머지 | **`/usr/bin/python3` 하드코딩** | 부분 호환 (python3 경로 폴백 필요) |
| F-6 | `merge_hooks_config` (156-184) | hooks JSON 머지 | **`/usr/bin/python3` 하드코딩** | 부분 호환 |
| F-7 | `install_dir` (186-200) | 디렉토리 복사 | 없음 — `cp -Rf` 표준 | **Linux 호환** |
| F-8 | `strip_deploy_md` (204-208) | .md 변경이력 stripping | **`/usr/bin/awk` 하드코딩** | 부분 호환 (PATH의 `awk` 사용 권장) |
| F-9 | `strip_deploy_md_recursive` (212-219) | 재귀 stripping | **`/usr/bin/find`, `/usr/bin/grep`, `/usr/bin/awk`, `/bin/mv` 하드코딩** | 부분 호환 |
| F-10 | `extract_bootstrap_content` (221-229) | bootstrap 컨텐츠 추출 | 없음 — `grep`/`sed` PATH | **Linux 호환** |
| F-11 | `install_opal_section` (231-305) | CLAUDE.md 마커 처리 | 없음 — bash 내장만 사용 | **Linux 호환** |
| F-12 | `install_gemini_hardening` (307-360) | GEMINI hardening 마커 | 없음 | **Linux 호환** |
| F-13 | `install_claude_permissions` (364-401) | Claude 권한 등록 | **`/usr/bin/python3` 하드코딩** | 부분 호환 |
| F-14 | `install_gemini_config` (405-436) | Gemini config 등록 | **`/usr/bin/python3` 하드코딩** | 부분 호환 |
| F-15 | `emit_platform_agent_adapter` (446-587) | 어댑터 emit (Claude/Cursor/Gemini) | **`/usr/bin/python3` 폴백 + venv 우선** | **Linux 호환** (venv python3 + fallback OK on Linux) |
| F-16 | `install_claude_agents`/`cursor_agents`/`gemini_agents` (589-653) | 어댑터 분기 | 없음 — `$USER_HOME/.{claude,cursor,gemini}` 표준 | **Linux 호환** |
| F-17 | `install_opal_bin` (659-692) | bin symlink + PATH 등록 | 없음 — `ln -sfn` 표준 | **Linux 호환** |
| F-18 | `register_path_in_shell_rc` (697-719) | shell rc 파일에 PATH 추가 | 없음 — `.zshrc`/`.bashrc`/`.profile` 표준 (fish 안내) | **Linux 호환** (Linux 기본은 bash) |
| F-19 | `install_opal` (723-918) | 메인 설치 로직 | 위 함수들 합성 + python3 호출 + venv | 부분 호환 (python3 경로 의존) |
| F-20 | `install_opal_venv` (920-973) | Python venv + Playwright | **`~/Library/Caches/ms-playwright` 하드코딩** (945) | **macOS 전용** (Linux 캐시 경로 다름 — `~/.cache/ms-playwright`) |
| F-21 | `install_opal_references` (975-989) | 참조 레지스트리 복사 | 없음 — `cp`/`mkdir` 표준 | **Linux 호환** |
| F-22 | `print_cleanup_notice` (993-1019) | 레거시 경로 안내 | 없음 — 사용자 홈 경로만 점검 | **Linux 호환** |
| F-23 | `find_cli_bin` (1023-1041) | CLI 바이너리 탐지 | 없음 — `command -v` + 인자 폴백 | **Linux 호환** (호출 시 폴백 경로만 다름) |
| F-24 | `install_mcp_cli` (1043-1065) | MCP CLI 등록 + 화이트리스트 | 없음 — basename + 명령어 화이트리스트 | **Linux 호환** |
| F-25 | `install_mcp` (1067-1198) | MCP 메인 + fork banner + playwright cache 디렉토리 | **`/opt/homebrew/bin/gemini`, `/usr/local/bin/gemini` 폴백 (1160)** + `/usr/bin/python3` 하드코딩 | 부분 호환 (Homebrew 경로는 Linux 무의미하지만 `command -v gemini` 1차 시도라서 안전) |
| F-26 | `count_items`/`print_summary` (1202-1262) | 설치 요약 출력 | 없음 — `ls`/`grep` 표준 | **Linux 호환** |
| F-27 | `main` (1266-1343) | 메뉴/비대화형 분기 | 없음 — 위 함수들 호출 | **Linux 호환** |

**분류 합계**:
- **Linux 호환** (수정 없이 동작): 14개 (F-2/3/4/7/10/11/12/15/16/17/18/21/22/23/24/26/27 = 17개 함수)
- **부분 호환** (사소한 경로/라벨 차이): 9개 (F-1/5/6/8/9/13/14/19/25)
- **macOS 전용** (Linux에서 결함 발생): **1개 (F-20 `install_opal_venv` Playwright 캐시 경로)**

### 핵심 발견

> **재사용 가능성이 매우 높다**. 1345줄 중 macOS 전용 분기는 **1개 라인**(`install_opal_venv` Line 945의 `~/Library/Caches/ms-playwright`)뿐이며, 나머지 "부분 호환" 항목은 `/usr/bin/python3` 등 절대 경로 하드코딩이지만 **Ubuntu/Debian의 표준 python3 위치도 `/usr/bin/python3`** 이므로 실제 호환된다 (Alpine/RHEL은 `/usr/bin/python3` 또는 `/usr/local/bin/python3`). Homebrew 경로 폴백(F-25)은 `command -v gemini`가 1차이므로 Linux에서는 무의미할 뿐 실패하지 않는다.

→ **단순 위임(전략 A)이 가장 합리적**이며, Playwright 캐시 분기 1줄만 수정하면 즉시 동작 가능하다.

### 현재 상태

- `scripts/install.sh:311`에서 Linux 분기 호출 경로(`scripts/install/linux.sh`)가 이미 정의됨 (D-1).
- `scripts/install.sh:325-335`에서 `linux.sh` 파일 부재 시 fallback 안내 후 `exit 1`로 차단됨 (D-1).
- `scripts/install/macos.sh` (44줄, D-2)이 `install-mac.sh`로 exec 위임하는 깔끔한 패턴 보유 → Linux wrapper 직접 모델.
- `install-mac.sh` 내부 1345줄 중 Linux 부적합 코드는 **Playwright 캐시 경로 1줄**.

### 영향 범위

| 영향 항목 | 내용 |
|----------|------|
| `scripts/install.sh` | Linux fallback 블록(326~333) 제거 또는 데드코드화 |
| `scripts/install/linux.sh` (신규) | Linux 진입점 추가 |
| `scripts/install-mac.sh` | Playwright 캐시 경로 OS별 분기 1줄 추가 (전략 A의 단일 결함 수리) |
| 보안 정책 | 변경 없음 — `set -euo pipefail`, sha256 검증, `OPAL_HOME` 가드 모두 install.sh + install-mac.sh에서 처리됨 |
| 변경이력 | install.sh, linux.sh, install-mac.sh 헤더 모두 v?.? 2026-05-20 행 추가 필요 (D-6 §변경이력 작성 의무) |

### 외부 컨텍스트 — Linux의 Playwright 캐시

- macOS: `~/Library/Caches/ms-playwright`
- Linux: `~/.cache/ms-playwright` (XDG `$XDG_CACHE_HOME` 기본값 `~/.cache`)
- Windows: `%USERPROFILE%\AppData\Local\ms-playwright`

출처: [Playwright Docs — Browsers/Managing](https://playwright.dev/docs/browsers#managing-browser-binaries)

---

## 2. 구현 계획

### 2.1 의사결정 (PLAN에서 결정)

#### M-1: Linux 설치 로직 구현 전략 — **전략 A (단순 위임) 채택**

**결정**: `scripts/install/linux.sh`는 `scripts/install/macos.sh`와 동일한 패턴으로 `scripts/install-mac.sh`에 exec 위임한다. 단, `install-mac.sh`의 단일 macOS 의존성(Playwright 캐시 경로)은 OS 감지로 분기한다.

**근거**:
1. §1 정밀 분석 결과 `install-mac.sh` 1345줄 중 macOS 전용은 **1줄**(`~/Library/Caches/ms-playwright`)뿐 (→ §1 표 F-20).
2. 전략 B(별도 신설)는 1345줄 중복 — 사용자 데이터 보존 로직(`clean_dirs`)·MCP 등록·어댑터 emit·OPAL_HOME 가드 등이 중복 유지보수 위험 (→ `docs/CONVENTIONS.md` §"플랫폼 분기 격리").
3. 전략 C(`install-core.sh`로 일반화)는 v0.5.0 베타 진입로 차단을 즉시 푸는 본 태스크의 긴급도에 비해 리팩토링 범위가 과도하다 (TASK.md §배경 — "오픈소스 공개 직후 첫 Linux 설치자 차단").
4. v0.6/v1.0 로드맵에서 `install-core.sh` 리네이밍은 별도 태스크로 분리 — 현재는 최소 변경으로 R-3(시나리오 차단 해소)를 달성한다.

**[MUST]** `docs/CONVENTIONS.md` §"플랫폼 분기 격리": "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다." → 본 결정은 OS 차이를 `install-mac.sh` 내부 단일 함수(`install_opal_venv`)에 격리하므로 컨벤션과 정합. 다만 향후 `install-core.sh`로 일반화 시 함수명 변경 필요 (별도 태스크).

**트레이드오프**: 파일명 `install-mac.sh`가 macOS 한정인 듯한 인상을 주는 단점이 있으나, 변경이력 + linux.sh 위임 주석으로 명시한다. 후속 리네이밍 태스크에서 해결.

#### M-2: 지원 Linux 배포판 범위 — **Ubuntu/Debian 명시 지원, RHEL/Fedora/Arch는 "best effort"**

**결정**:
- **명시 지원**: Ubuntu 22.04+ / Debian 12+ (apt 기반).
- **Best effort**: RHEL/Fedora/CentOS Stream / Arch — 의존성(`curl`/`tar`/`git`/`python3`)이 PATH에 존재하면 동작하나, 미설치 시 자동 설치는 시도하지 않는다.
- **명시 비지원**: Alpine (musl libc) — Playwright 브라우저 미지원 (Playwright 공식이 glibc만 지원).

**근거**:
1. `scripts/install.sh:158`의 `check_deps()`가 이미 `curl`/`tar`/`git`만 검증하고, `python3`/`node`는 `install-mac.sh` 내부에서 graceful skip된다 (→ `scripts/install-mac.sh:832-844`, `1075-1078`).
2. apt/yum/pacman 분기 자동 설치는 sudo 권한 필요 → curl-pipe-bash 보안 모델(D-7 §1 위협 모델)과 충돌. **자동 설치 시도 금지**.
3. Ubuntu/Debian이 OSS 사용자 분포 1위 (Linux 사용자층 가정).

#### M-3: 선행 의존성 처리 — **안내만, 자동 설치 없음**

**결정**:
- 필수 의존성 부재 시: `error` 후 설치 명령 안내 (예: `sudo apt install python3 python3-venv`).
- 선택 의존성 부재 시: `warn` 후 graceful skip (현행 `install-mac.sh` 패턴 유지).
- macOS 어댑터(Claude/Cursor/Gemini) 중 Linux 의미 있는 것: **3개 모두 유효** (Claude Code / Cursor / Gemini CLI 모두 Linux 지원, Antigravity만 Linux 미배포).
- Playwright 브라우저 자동 설치: macOS와 동일 (`venv/bin/playwright install chromium`).

**근거**:
1. `docs/SECURITY.md` §1 위협 모델 — curl-pipe-bash + sudo는 위협 표면 증가.
2. 현행 `install-mac.sh:832-844` (Node.js)와 `:1075-1078` (python3)이 graceful skip 패턴 — Linux도 동일 적용.
3. `~/.claude/`, `~/.cursor/`, `~/.gemini/` 디렉토리 구조는 OS 무관 (사용자 홈 기준).

#### M-4: 셸 감지·PATH 등록 방식 — **현행 `register_path_in_shell_rc()` 그대로 적용**

**결정**: 별도 신설 없이 `install-mac.sh:697-719`의 `register_path_in_shell_rc()` 함수를 재사용한다. 이 함수는 이미 `.zshrc`/`.bashrc`/`.profile` 3개 + fish 안내를 모두 처리한다.

**근거**:
1. 함수 본문이 OS 독립적 — `$USER_HOME/.{zshrc,bashrc,profile}`은 Linux도 동일 위치.
2. fish 안내(`~/.config/fish/config.fish`)는 Linux에서도 표준 위치.
3. Linux 기본 셸은 bash이므로 `.bashrc` 등록이 1차 적용되어 자연스럽게 동작한다.

### 2.2 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `scripts/install/linux.sh` | Linux 설치 진입점 (install-mac.sh로 exec 위임) | M-1 결정 + `scripts/install/macos.sh:1-44` 패턴 직접 모방 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| U-1 | `scripts/install.sh` | `exec_platform_installer()` 함수 내 Linux fallback 안내 블록(326-333) 제거. 변경이력에 v1.4 행 추가. | `scripts/install.sh:325-335` — linux.sh 신설 후 데드코드 |
| U-2 | `scripts/install-mac.sh` | `install_opal_venv()` 내 Playwright 캐시 경로(945)에 OS 감지 분기 추가: `[[ "$(uname -s)" == "Linux" ]] && pw_cache="$USER_HOME/.cache/ms-playwright"`. 변경이력에 v2.2 행 추가. | M-1 트레이드오프 — 전략 A의 단일 결함 수리. D-9 Playwright Docs 근거 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 2.3 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | Playwright 캐시 OS 분기 추가 | `scripts/install-mac.sh` (수정) | 낮음 (1줄 추가) |
| 2 | `linux.sh` 신규 작성 (macos.sh 패턴 복제) | `scripts/install/linux.sh` (신규) | 낮음 (44줄) |
| 3 | `install.sh` Linux fallback 블록 제거 + 변경이력 행 추가 | `scripts/install.sh` (수정) | 낮음 (8줄 삭제 + 1줄 변경이력) |
| 4 | dry-run 검증 (`OPAL_DRY_RUN=1` + 플랫폼 mock) | (검증 단계) | 낮음 |
| 5 | 실제 Linux 검증 (docker 또는 Linux 머신) | (검증 단계) | 중간 (환경 의존) |

> **Phase 그룹핑** — Step 1, 2, 3은 서로 다른 파일을 대상으로 하고 직접적 의존이 없으므로 병렬 가능. 단 Step 3은 Step 2의 파일이 존재한다는 가정에 의존 (런타임에는 install.sh가 추출된 tarball에서 linux.sh를 찾으므로 같은 커밋에 함께 포함되어야 함).

### 2.4 핵심 설계

#### 2.4.1 `scripts/install/linux.sh` (신규)

`scripts/install/macos.sh` 의 구조를 그대로 복제하되 라벨만 `Linux`로 변경한다 (→ D-2).

```bash
#!/bin/bash
#
# scripts/install/linux.sh — Linux 설치 진입점 (install-mac.sh wrapper)
#
# 역할: install.sh 및 opal-cli 가 호출할 수 있는 Linux 전용 설치 진입점.
#       현행 scripts/install-mac.sh 를 exec 로 위임한다.
#       install-mac.sh 내부는 OS 감지를 통해 Linux 호환 분기(Playwright 캐시 경로)를
#       처리하므로 동일 스크립트를 안전하게 재사용 가능하다.
#       후속: install-core.sh로 리네이밍 검토 (v0.6 로드맵).
#
# Usage:
#   bash scripts/install/linux.sh [args...]
#
# 근거:
#   tasks/006-260520-opp-install-linux/PLAN.md §의사결정 M-1 (전략 A — 단순 위임)
#   tasks/006-260520-opp-install-linux/PLAN.md §1 install-mac.sh 함수별 호환성 분석
#
# 변경이력:
#   v1.0 2026-05-20: 신규 작성 — Linux one-liner 진입점 (006)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALLER="${REPO_ROOT}/scripts/install-mac.sh"

if [[ ! -f "${INSTALLER}" ]]; then
    echo "[ERROR] install-mac.sh 를 찾을 수 없습니다: ${INSTALLER}" >&2
    echo "        프로젝트 루트에서 실행하거나 REPO_ROOT 환경변수를 설정하세요." >&2
    exit 1
fi

if [[ ! -x "${INSTALLER}" ]]; then
    chmod +x "${INSTALLER}"
fi

exec bash "${INSTALLER}" "$@"
```

**설계 결정 인용**:
- `set -euo pipefail` 의무 — `[MUST] docs/SECURITY.md §2`: "scripts/install.sh / scripts/install.ps1 / opal/tools/opal-cli/lib/update.sh ... set -euo pipefail 필수" (인접 파일 동일 규약).
- exec 위임 패턴 — `scripts/install/macos.sh:38-44` 그대로 (→ D-2).
- 변경이력 형식 — `[MUST] docs/CONVENTIONS.md §변경이력 작성 의무`: "스킬·에이전트·참조 문서를 변경하면 ## 변경이력 표에 행을 추가한다 ... 태스크 번호를 괄호로 포함 — 예: (138)" → `(006)` 표기.

#### 2.4.2 `scripts/install.sh` 수정

`exec_platform_installer()` 함수의 Linux fallback 블록(라인 326~333)을 제거한다. linux.sh 신설 후 도달 불가능한 데드코드.

**변경 전** (`scripts/install.sh:325-335`):
```bash
if [[ ! -f "${installer_path}" ]]; then
    # Linux 전용 installer 미구현 시 fallback 안내
    if [[ "${OPAL_PLATFORM}" == "linux" ]]; then
        warn "Linux 전용 설치 스크립트가 아직 준비 중입니다 (scripts/install/linux.sh)."
        warn "Linux 사용자는 다음 명령으로 수동 설치하세요:"
        warn "  git clone https://github.com/${OPAL_REPO}.git opal"
        warn "  bash opal/scripts/install-mac.sh"
        exit 1
    fi
    error "플랫폼 설치 스크립트를 찾을 수 없습니다: ${installer_path}"
fi
```

**변경 후**:
```bash
if [[ ! -f "${installer_path}" ]]; then
    error "플랫폼 설치 스크립트를 찾을 수 없습니다: ${installer_path}"
fi
```

→ Linux 분기와 macOS 분기를 동일하게 처리. 두 플랫폼 모두 `installer_path` 부재 시 동일 에러 메시지로 명확히 실패한다.

**변경이력 행 추가**:
```
#   v1.4 2026-05-20: Linux fallback 안내 블록 제거 — scripts/install/linux.sh 신설로 데드코드 (006)
```

#### 2.4.3 `scripts/install-mac.sh` 수정

`install_opal_venv()` 함수 Line 945의 Playwright 캐시 경로를 OS별 분기로 변경한다.

**변경 전** (`scripts/install-mac.sh:945`):
```bash
local pw_cache="$USER_HOME/Library/Caches/ms-playwright"
```

**변경 후**:
```bash
# Playwright 캐시 경로: macOS ~/Library/Caches, Linux ~/.cache (XDG 표준)
# 출처: https://playwright.dev/docs/browsers#managing-browser-binaries
local pw_cache
if [[ "$(uname -s)" == "Linux" ]]; then
    pw_cache="$USER_HOME/.cache/ms-playwright"
else
    pw_cache="$USER_HOME/Library/Caches/ms-playwright"
fi
```

**변경이력 행 추가**:
```
#   v2.2 2026-05-20: install_opal_venv Playwright 캐시 경로 OS 분기 — Linux는 ~/.cache/ms-playwright (XDG 표준). Linux one-liner 진입점 신설 동반 수정 (006)
```

**설계 결정 인용**:
- Playwright 캐시 경로 — [Playwright Docs — Browsers/Managing](https://playwright.dev/docs/browsers#managing-browser-binaries) (→ D-9).
- 변경이력 형식 — `[MUST] docs/CONVENTIONS.md §변경이력 작성 의무`.

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 3개
>
> | Phase | Step | 실행 | agent | 비고 |
> |-------|------|------|-------|------|
> | 1     | 1, 2 | 병렬 | opal-task-agent | 독립 파일 (install-mac.sh 수정 + linux.sh 신규) |
> | 2     | 3    | 순차 | opal-task-agent | Step 2 의존 (linux.sh 존재 가정) |
> | 3     | 4, 5, 6 | 순차 | opal-task-agent + PM | 검증 단계 |

**에이전트 배정 근거**: 본 태스크는 셸 스크립트 작업으로 BE/FE 도메인 구분이 없고 GA 영향이 제한적이므로 범용 워커 `opal-task-agent` (standard) 배정이 적절. 디스패치 매핑 테이블의 권고와 일치 (디스패치 프롬프트 §전문 에이전트 매핑 테이블).

### Step 1: install-mac.sh Playwright 캐시 OS 분기 추가

- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. Line 945의 `local pw_cache="$USER_HOME/Library/Caches/ms-playwright"`를 OS 감지 분기로 교체 (→ §2.4.3).
  2. 헤더 변경이력 표(Line 8~18) 끝에 `v2.2 2026-05-20: ... (006)` 행 추가.
- **완료 기준**:
  - `grep -n "pw_cache" scripts/install-mac.sh`에서 `uname -s` 분기 코드 확인.
  - `head -25 scripts/install-mac.sh | grep "v2.2"`에 변경이력 행 존재.
- **테스트**:
  - macOS에서 `bash -n scripts/install-mac.sh` (syntax check) 통과.
  - macOS에서 `OPAL_DRY_RUN=1 OPAL_AUTO_INSTALL=1 bash scripts/install-mac.sh` 시 `pw_cache`가 `Library/Caches` 경로로 결정됨 (Darwin).
- **의존**: 없음

### Step 2: scripts/install/linux.sh 신규 생성

- [ ] 완료
- **파일**: `scripts/install/linux.sh` (신규)
- **agent**: opal-task-agent
- **작업 내용**:
  1. §2.4.1의 전체 내용을 파일로 작성.
  2. `chmod +x scripts/install/linux.sh` (선택 — install.sh가 런타임에 `chmod +x` 호출하므로 필수 아님).
- **완료 기준**:
  - `ls -la scripts/install/linux.sh` 존재 확인.
  - `bash -n scripts/install/linux.sh` syntax check 통과.
  - 헤더에 변경이력 표 + `(006)` 태스크 번호 포함.
- **테스트**:
  - macOS에서 `bash scripts/install/linux.sh --help`(또는 임의 인자) 실행 시 install-mac.sh로 exec되어 메뉴 또는 비대화형 분기 진입 확인.
- **의존**: 없음

### Step 3: install.sh Linux fallback 블록 제거 + 변경이력 갱신

- [ ] 완료
- **파일**: `scripts/install.sh`
- **agent**: opal-task-agent
- **작업 내용**:
  1. Line 325~335의 `if [[ ! -f "${installer_path}" ]]; then ... fi` 블록을 §2.4.2 "변경 후" 형태로 단순화.
  2. 주석 라인 302의 `Linux: scripts/install/linux.sh (미구현 시 fallback 안내)`를 `Linux: scripts/install/linux.sh`로 수정.
  3. 헤더 변경이력 표 끝에 `v1.4 2026-05-20: ... (006)` 행 추가.
- **완료 기준**:
  - `grep -n "준비 중" scripts/install.sh` 출력 없음 (fallback 메시지 완전 제거).
  - `grep -n "v1.4" scripts/install.sh` 변경이력 행 존재.
  - `bash -n scripts/install.sh` syntax check 통과.
- **테스트**:
  - macOS에서 `OPAL_DRY_RUN=1 bash scripts/install.sh` 실행 시 macOS 분기 정상 동작 (회귀 방지).
- **의존**: Step 2 (linux.sh 존재 시 의미 있음 — 단 install.sh 자체는 syntax check만으로도 검증 가능).

### Step 4: macOS 로컬 dry-run 회귀 검증

- [ ] 완료
- **파일**: (테스트 산출물 없음 — STATE.md 기록)
- **agent**: opal-task-agent
- **작업 내용**:
  1. `OPAL_DRY_RUN=1 bash scripts/install.sh`를 macOS 환경에서 실행하여 macOS 분기가 회귀 없이 동작하는지 확인.
  2. 출력 로그에서 `Linux 전용 설치 스크립트가 아직 준비 중입니다` 문자열 부재 확인.
  3. tarball 다운로드/검증 단계가 정상 동작 (DRY-RUN 모드에서 시뮬레이션).
- **완료 기준**:
  - `[opal] WARN: Linux 전용 설치 스크립트가 아직 준비 중입니다` 메시지가 어떤 분기에서도 출력되지 않음.
  - macOS 분기에서 `[DRY-RUN] exec_platform_installer 생략` + `실행 예정 경로: .../scripts/install/macos.sh` 출력.
- **테스트**:
  - `OPAL_DRY_RUN=1 bash scripts/install.sh 2>&1 | tee /tmp/opal-dryrun-mac.log`
  - `grep "준비 중" /tmp/opal-dryrun-mac.log` 출력 없음.
- **의존**: Step 1, 2, 3

### Step 5: Linux 검증 (docker 컨테이너 또는 mock)

- [ ] 완료
- **파일**: (테스트 산출물 없음 — STATE.md 기록)
- **agent**: opal-task-agent
- **작업 내용**:
  1. 가능 옵션:
     - **옵션 A** (권장): docker — `docker run --rm -v $(pwd):/opal -w /opal ubuntu:22.04 bash -c "apt-get update && apt-get install -y curl tar git python3 python3-venv && OPAL_DRY_RUN=1 bash scripts/install.sh"`.
     - **옵션 B** (mock): macOS에서 `uname` 함수를 임시 export해 `Linux` 반환하도록 wrapping (단, 실제 Linux 경로 검증은 불가).
     - **옵션 C** (실제): 캡틴 보유 Linux 머신에서 실행.
  2. `scripts/install/linux.sh` 진입 후 install-mac.sh로 exec 위임되어 메뉴 또는 비대화형 분기 진입 확인.
  3. Playwright 캐시 경로가 `~/.cache/ms-playwright`로 결정되는지 확인 (Linux 분기).
- **완료 기준**:
  - Linux 환경(또는 mock)에서 `Linux 전용 설치 스크립트가 아직 준비 중입니다` 메시지 출력 없음.
  - install-mac.sh의 비대화형 자동 설치 분기에 진입하여 `step "OPAL 자산 배포 중..."` 출력 확인.
- **테스트**:
  - 옵션 A 사용 시 docker 컨테이너 종료 코드 0.
  - 옵션 B 사용 시 mock 로그에 `Linux` 플랫폼 감지 + linux.sh 호출 경로 출력 확인.
- **의존**: Step 4
- **블로커 대응**: docker 미설치 또는 Linux 머신 부재 시 옵션 B (mock)로 폴백하고 STATE.md에 한계 기록. 실제 Linux 검증은 PM이 캡틴에게 보고하여 CLOSE 직전 또는 후속 추가작업으로 이전.

### Step 6: 최종 R-1~R-5 AC 매핑 확인

- [ ] 완료
- **파일**: (검증 메모만 — DONE.md에 반영)
- **agent**: PM 직접
- **작업 내용**:
  - R-1 (linux.sh 존재 + 진입점 동작) ← Step 2 + Step 5
  - R-2 (install.sh fallback 제거) ← Step 3 + Step 4
  - R-3 (one-liner 시나리오 fallback 없음) ← Step 5
  - R-4 (PLAN 전략 결정 + EXECUTE 일치) ← M-1 + Step 2
  - R-5 (변경이력 행 추가) ← Step 1, 2, 3 (3개 스크립트 모두)
- **완료 기준**: 5개 AC가 모두 산출물(파일 또는 로그)로 검증 가능.
- **테스트**: 5개 AC별 grep 명령 또는 로그 첨부.
- **의존**: Step 1~5 전체.

---

## 4. QA 체크리스트

### 4.1 기능 테스트

- [ ] R-1: `scripts/install/linux.sh` 파일이 존재하고 `bash -n` 통과한다.
- [ ] R-1: macOS에서 `bash scripts/install/linux.sh` 실행 시 install-mac.sh로 exec되어 메뉴 또는 비대화형 분기 진입한다 (Step 2 테스트 로그).
- [ ] R-2: `scripts/install.sh`의 `exec_platform_installer()`에 "준비 중" 경고가 없다 (Step 3 grep).
- [ ] R-2: `OPAL_DRY_RUN=1 bash scripts/install.sh` 실행 시 macOS 분기 회귀 없음 (Step 4 로그).
- [ ] R-3: Linux 환경(또는 mock)에서 one-liner fallback 메시지 출력 없음 (Step 5).
- [ ] R-3: Linux Playwright 캐시 경로가 `~/.cache/ms-playwright`로 결정된다 (Step 5).

### 4.2 일관성 테스트

- [ ] `scripts/install/linux.sh`의 헤더/구조가 `scripts/install/macos.sh` 패턴과 일치한다 (라벨만 Linux로 변경).
- [ ] `scripts/install.sh` 변경 후에도 Linux/macOS 분기 모두 동일한 `installer_path` 부재 처리 분기로 통합된다.
- [ ] 어댑터 계층 격리 원칙 위반 없음 — install-mac.sh 본체에 추가된 OS 분기는 어댑터 함수(`install_opal_venv`) 내부에 격리됨 (`docs/CONVENTIONS.md` §"플랫폼 분기 격리" 준수).

### 4.3 문서/변경이력 품질

- [ ] `scripts/install/linux.sh` 헤더에 `v1.0 2026-05-20 ... (006)` 변경이력 행 존재.
- [ ] `scripts/install.sh` 헤더에 `v1.4 2026-05-20 ... (006)` 변경이력 행 추가.
- [ ] `scripts/install-mac.sh` 헤더에 `v2.2 2026-05-20 ... (006)` 변경이력 행 추가.
- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수 (`docs/CONVENTIONS.md` §언어 규칙).
- [ ] kebab-case 파일명 준수 — `linux.sh` (단일 단어 OK), `install-mac.sh` 기존 그대로.

### 4.4 보안/하네스 준수

- [ ] `linux.sh`에 `set -euo pipefail` 포함 (`docs/SECURITY.md` §2 인접 파일 동일 규약).
- [ ] linux.sh가 `OPAL_HOME` 가드를 우회하지 않음 — install-mac.sh로 위임하므로 가드는 자동 적용 (`docs/SECURITY.md` §7).
- [ ] 자동 커밋 금지 원칙 준수 — EXECUTE 워커는 파일 변경만 수행하고 커밋은 캡틴 명시 요청 시에만 (`docs/CONVENTIONS.md` §커밋 규칙).

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | `install-mac.sh`가 Linux에서 실행될 때 `/usr/bin/python3` 절대 경로가 부재할 수 있음 (Alpine 등 musl 배포판) | python3 호출 함수(`merge_mcp_config`, `install_claude_permissions`, `install_gemini_config` 등) 실패 | M-2에 따라 Alpine은 비지원 명시. Ubuntu/Debian/RHEL/Fedora는 `/usr/bin/python3` 존재 (표준 위치). 후속 v0.6에서 `command -v python3` 우선 + 폴백 패턴으로 리팩토링 검토 (별도 태스크). |
| R-T2 | Playwright 브라우저가 Linux에서 설치 실패 (libnss/libgbm 등 시스템 라이브러리 누락) | venv 설치는 성공하나 브라우저 미설치 | `install-mac.sh:957-961`의 graceful skip 패턴이 이미 적용됨 — `warn` 후 수동 명령 안내. 별도 조치 불필요. |
| R-T3 | Linux 실제 환경 검증 불가 (캡틴 로컬 macOS, docker 미보장) | R-3 AC 완료 보고가 mock 기반에 그칠 위험 | Step 5 옵션 A(docker)를 1차 시도, 실패 시 옵션 B(mock)로 폴백하고 STATE.md에 한계 명시. CLOSE 단계에서 캡틴이 실제 Linux 머신에서 추가 검증을 진행하는 것을 권장. |
| R-T4 | `scripts/install/macos.sh`와 `linux.sh`가 동일 패턴이라 중복 — DRY 위반 | 향후 변경 시 양쪽 동기 업데이트 필요 | M-1 트레이드오프에 명시. v0.6 로드맵에서 `install-core.sh`로 일반화 + `install/{macos,linux}.sh` 양쪽 위임 패턴 통합 — 별도 태스크. |
| R-T5 | install.sh와 install-mac.sh 변경이력 누락 — `docs/CONVENTIONS.md` §변경이력 작성 의무 위반 | PM 검토 게이트 실패 | Step 1, 3 완료 기준에 변경이력 grep 명시. EXECUTE QA에서 헤더 검증 필수. |
| R-T6 | install-mac.sh 파일명이 macOS 한정 인상을 주지만 실제로는 Linux도 호출 — 사용자/리뷰어 혼란 | 가독성 저하 | linux.sh 헤더 주석에 "후속: install-core.sh로 리네이밍 검토 (v0.6 로드맵)" 명시 (§2.4.1). 변경이력 v2.2 메시지에서도 Linux 동반 동작 명시. |

> §7 영역 간 용어 일관성 검토 (citation-rules.md §7): 본 태스크는 단일 도메인(셸 스크립트)이고 FE↔BE/정책↔코드/ERD↔코드/IA↔라우트 영역 쌍이 없으므로 검출 대상 없음.

---

## 6. 추가 검토 메모 (PM 자율 결정 기록 — agentic 모드)

- **M-1 전략 선택의 자율 결정**: TASK.md §미확정 사항 1에서 PM 자율 결정 위임. 정밀 분석 결과 macOS 의존성이 1줄에 그쳐 전략 A를 자율 결정. 추후 캡틴 검토 시 이의 제기 가능하나, 전략 B/C는 본 태스크 시급도(v0.5.0 베타 진입로 차단)에 비해 과도한 범위로 판단.
- **AGENTIC-LOG.md 기록 필요**: M-1, M-2 결정 근거를 EXECUTE 단계에서 별도 기록 (하네스 §3 폴백 승인 의무).

---

## 7. 메모 — docs/ 갱신 Step 판단

본 태스크 코드 변경은 다음 docs/ 문서에 영향을 미치지 않는다:

- `docs/PROJECT.md` — 폴더 구조맵 갱신 불필요 (`scripts/install/` 폴더는 이미 존재, 새 파일만 추가).
- `docs/ARCHITECTURE.md` — 배포 모델 다이어그램에 영향 없음 (install-mac.sh 위임 구조 유지).
- `docs/CONVENTIONS.md` — 컨벤션 변경 없음.
- `docs/SECURITY.md` — 보안 정책 변경 없음 (sha256/OPAL_HOME 가드 등 모두 install.sh/install-mac.sh가 처리, 신규 linux.sh는 단순 위임).

→ **docs/ 갱신 Step 추가 불필요**. PM은 CLOSE 단계 DONE.md 작성 시 본 항목을 확인하고 변경 없음을 명시한다.

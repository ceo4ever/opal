# TASK: Linux 설치 스크립트 신설 — scripts/install/linux.sh

> 작성일: 2026-05-20 | 작업 유형: 신규 | 적용 스킬: opp | 모드: agentic
> 입력: 캡틴이 OPAL Linux one-liner 설치 시 fallback 안내만 출력되는 현황을 보고 → //opp --agentic 호출
> 출력: TASK.md

## 작업 목표

Linux 사용자가 macOS와 동등한 one-liner (`curl ... | bash`) 흐름으로 OPAL을 설치할 수 있도록, `scripts/install/linux.sh`를 신설하고 `scripts/install.sh`의 Linux 분기 fallback 안내를 제거한다.

## 배경

OPAL v0.5.0(2026-05-10) 베이스라인 리셋과 v0.4.x 시기 배포 정비(태스크 139, 144)를 거치며 `scripts/install.sh`가 macOS/Linux 통합 진입점으로 설계되었으나, **Linux 측 진입점(`scripts/install/linux.sh`)이 아직 구현되지 않은 상태**다. v0.5.0 베타 공개 시점에 Linux 사용자가 one-liner를 실행하면 다음 메시지를 받고 차단된다:

```
[opal] WARN: Linux 전용 설치 스크립트가 아직 준비 중입니다 (scripts/install/linux.sh).
[opal] WARN: Linux 사용자는 다음 명령으로 수동 설치하세요:
[opal] WARN:   git clone https://github.com/ceo4ever/opal.git opal
[opal] WARN:   bash opal/scripts/install-mac.sh
```

캡틴이 직접 Linux 환경에서 `curl -fsSL ... install.sh | OPAL_ALLOW_UNVERIFIED=1 bash`를 실행하여 이 차단을 확인했다 (2026-05-20 08:30 KST). 오픈소스 공개 직후 첫 Linux 설치자가 부딪히는 진입 장벽이므로 즉시 해소가 필요하다.

## 배경 분석 (대화에서 도출)

### 현재 설치 스크립트 구조

| 파일 | 라인 수 | 역할 |
|------|--------|------|
| `scripts/install.sh` | 369 | 메인 디스패처 — 플랫폼 감지 + tarball 다운로드 + sha256 검증 + 플랫폼 installer 호출 |
| `scripts/install/macos.sh` | 44 | macOS wrapper — `scripts/install-mac.sh`로 단순 exec 위임 |
| `scripts/install/linux.sh` | **부재** | **이번 태스크 대상** |
| `scripts/install-mac.sh` | 1345 | 실제 macOS 설치 로직 (메뉴, R2 마커, PATH 등록, venv, MCP, 어댑터 등) |
| `scripts/install.ps1` | - | Windows PowerShell (별도 트랙) |

### install.sh의 Linux 분기 (이미 구현된 부분)

`scripts/install.sh`의 `exec_platform_installer()` 함수 (라인 299~340):

```bash
case "${OPAL_PLATFORM}" in
    macos)  installer_path="${OPAL_EXTRACT_DIR}/scripts/install/macos.sh" ;;
    linux)  installer_path="${OPAL_EXTRACT_DIR}/scripts/install/linux.sh" ;;
esac

if [[ ! -f "${installer_path}" ]]; then
    if [[ "${OPAL_PLATFORM}" == "linux" ]]; then
        warn "Linux 전용 설치 스크립트가 아직 준비 중입니다 ..."
        # ... fallback 안내 후 exit 1
    fi
fi
```

→ **`scripts/install/linux.sh` 파일만 신설하면 install.sh의 호출 흐름은 그대로 동작한다**.

### install-mac.sh의 macOS 의존성 (호환성 판단 필요)

`install-mac.sh`(1345줄) 내부에 macOS 전용 기능이 어디까지 섞여 있는지가 PLAN의 핵심 조사 항목이다. 헤더 변경이력에서 확인된 기능 목록:

- 셸 RC 파일 PATH 등록 (`install_opal_bin`/`register_path_in_shell_rc`)
- Python venv (`install_opal_venv`) — pip 호출
- Claude Code / Cursor / Gemini / Antigravity 플랫폼 어댑터 자동 생성
- R2/OPAL 마커 처리 (CLAUDE.md, GEMINI.md 부트스트래퍼 삽입)
- community-skills fetch
- Playwright cache 디렉토리
- 비대화형 모드(`OPAL_AUTO_INSTALL=1` / pipe stdin)

macOS 전용으로 의심되는 항목 (PLAN에서 검증 필요):
- `defaults` 명령 사용 여부
- Homebrew(`brew`) 의존 여부
- `launchd` plist 처리 여부
- macOS keychain 사용 여부
- 사용자 디렉토리 감지 방식 (`/Users/` vs `/home/`)
- shell rc 파일 위치 추정 (`~/.zshrc`/`~/.bashrc` 양쪽 지원 여부)

## 확정된 설계 방향 (대화에서 합의)

- **태스크 작업 범위는 "Q1 — Linux 설치 스크립트 신설"로 한정**. sha256sums.txt 핫픽스(Q2), v0.5.1 패치 묶음(Q3)은 본 태스크 범위 밖.
- **사고 복구는 본 태스크 시작 전에 완료**. `docs/` 폴더는 `git checkout HEAD`로 복원되었고, browser-editor 외래 파일은 `~/tmp/browser-editor-docs-rescue/`로 대피 완료.
- **모드는 agentic** (CLOSE 진입만 캡틴 승인 필수). PLAN/EXECUTE 게이트는 PM 자율 통과, AGENTIC-LOG.md에 판단 근거를 기록한다.

## 미확정 사항 (PLAN에서 결정)

1. **Linux 설치 로직 구현 전략**:
   - (A) `install/macos.sh`처럼 `install-mac.sh`로 단순 위임 — 가장 가벼우나 macOS 의존성 잔존 위험
   - (B) `install-linux.sh`를 별도 신설 — 깨끗하지만 1345줄 중복 위험
   - (C) `install-mac.sh`를 플랫폼 중립 `install-core.sh`로 일반화 후 양쪽이 위임 — 가장 깨끗하나 리팩토링 범위 큼
   → PLAN에서 `install-mac.sh` 내부 의존성을 정밀 스캔한 뒤 결정

2. **지원 Linux 배포판 범위**: Ubuntu/Debian만? RHEL/Fedora/Arch도? (PLAN에서 `apt`/`yum`/`pacman` 분기 필요 여부 판단)

3. **선행 의존성 처리**:
   - `node` / `python3` / `pip` / `git` / `curl` 부재 시 안내만 할지, 자동 설치 시도할지
   - macOS 어댑터(Claude/Cursor/Gemini) 중 Linux에서 의미 있는 것 선별
   - Playwright 등 macOS에서 자동 설치되던 항목의 Linux 대응

4. **셸 감지·PATH 등록 방식**: Linux는 `bash`/`zsh`/`fish` 다양 — 기본 셸 감지 + RC 파일 결정 로직

## 요구사항

- [ ] **R-1**: `scripts/install/linux.sh`가 신규 생성되어 있고, `bash scripts/install/linux.sh [args...]` 진입점이 정의되어 있다.
  - **무엇을**: Linux 설치 진입점 스크립트 신설
  - **어디에**: `scripts/install/linux.sh` (신규)
  - **왜**: `scripts/install.sh`의 `exec_platform_installer()`가 호출 경로로 이미 지정 (`install.sh` 라인 311)
  - **AC**: `scripts/install/linux.sh` 파일이 존재하고 실행 비트 또는 `chmod +x` 처리 후 `bash linux.sh --help` 또는 dry-run에서 종료 코드 0을 반환한다.

- [ ] **R-2**: `scripts/install.sh`의 Linux fallback 안내(라인 326~333)가 제거되거나 "linux.sh 부재 시"가 아닌 정상 분기 후 호출로 전환되어 있다.
  - **무엇을**: fallback 안내 블록 제거 또는 정상 호출로 대체
  - **어디에**: `scripts/install.sh` `exec_platform_installer()` 함수 내부
  - **왜**: linux.sh 신설 후 fallback 코드는 데드 코드가 됨. v1.x 변경이력 행 추가 필수.
  - **AC**: install.sh dry-run (`OPAL_DRY_RUN=1`) 실행 시 Linux 분기에서 "준비 중" 경고가 출력되지 않고 `scripts/install/linux.sh` 실행 경로만 안내된다.

- [ ] **R-3**: Linux 환경에서 one-liner (`curl -fsSL ... install.sh | bash`)가 fallback 안내 없이 install-{linux 또는 core} 단계로 진입한다.
  - **무엇을**: one-liner 흐름 동작 검증
  - **어디에**: `scripts/install.sh` + `scripts/install/linux.sh` 연계
  - **왜**: 캡틴 보고 시나리오 그대로 재현되지 않아야 함
  - **AC**: 캡틴이 보고한 시나리오(`curl ... | OPAL_ALLOW_UNVERIFIED=1 bash`)에서 "Linux 전용 설치 스크립트가 아직 준비 중입니다" 경고가 출력되지 않는다.

- [ ] **R-4**: PLAN 단계에서 결정된 구현 전략(A/B/C 중 1)이 PLAN.md에 명시되고 EXECUTE 결과가 그 결정과 일치한다.
  - **무엇을**: 전략 결정 및 일관성
  - **어디에**: `PLAN.md` §의사결정 + EXECUTE 산출물
  - **왜**: agentic 모드 PM 자율 통과 시에도 폴백/이탈은 추적 필요 (하네스 §3 폴백 승인 의무)
  - **AC**: PLAN.md에 M-N 결정 항목으로 전략 선택과 근거가 1줄 이상 명시되어 있고, EXECUTE changed_files가 그 전략과 정합한다.

- [ ] **R-5**: 변경이력 갱신 — `install.sh`와 신규 `linux.sh` 헤더에 `v?.? 2026-05-20: ... (006)` 행이 기재되어 있다.
  - **무엇을**: 변경이력 표 행 추가
  - **어디에**: 각 스크립트 헤더 주석 변경이력 섹션
  - **왜**: 프로젝트 금지사항 §"변경이력 누락 금지"
  - **AC**: `head -50` 출력에 태스크 번호(006) 포함 행이 존재한다.

## 제약 조건

- **하네스 Guards**: 캡틴 명시 승인 없이 자동 커밋 금지. CLOSE 진입 직전 캡틴 승인 필수 (agentic 모드 공통 게이트).
- **배포 경계 준수**: `~/.opal/` 직접 편집 금지. 모든 수정은 프로젝트 소스(`scripts/`)에서 수행하고 install로 재배포는 별도 판단.
- **변경이력 누락 금지**: 스크립트 헤더 변경이력 표에 행 추가 의무.
- **하드코딩된 플랫폼 분기 추가 금지**: 신규 Linux 분기는 어댑터 계층(`scripts/install/`)에서만 처리. install.sh 본체에 OS별 if 추가 최소화.
- **호환성**: 최소 검증 대상은 Ubuntu/Debian 계열(가장 일반적인 Linux 사용자층). Alpine/RHEL/Arch는 PLAN에서 범위 결정.
- **검증 방식**: 실제 Linux 머신 또는 docker 컨테이너에서 dry-run 가능. macOS 개발 환경에서는 `OPAL_DRY_RUN=1` + 플랫폼 감지를 mock하여 흐름 검증.

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Shell | Bash (POSIX 호환 우선) |
| 플랫폼 | Linux (Ubuntu/Debian 우선, 그 외 PLAN 결정) |
| 의존 도구 | curl, tar, git, node (선택), python3+venv (선택) |
| 보안 | `set -euo pipefail`, `curl --proto '=https' --tlsv1.2`, sha256 검증 |

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install 메인 디스패처 | `scripts/install.sh` | Linux 분기 호출 경로(`exec_platform_installer`) 정의 위치 |
| D-2 | 소스 | macOS wrapper | `scripts/install/macos.sh` | Linux wrapper 구현 패턴의 직접 참조 (44줄, exec 위임 패턴) |
| D-3 | 소스 | macOS 실제 설치 로직 | `scripts/install-mac.sh` | Linux 호환성 판단 + 재사용 가능 부분 식별 (1345줄) |
| D-4 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 폴더 구조맵 / 네이밍 규칙 / 컴포넌트 표준 확인 |
| D-5 | 기획 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` | source/runtime 구분 + 어댑터 계층 원칙 |
| D-6 | 기획 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 셸 스크립트 작성 규칙 / 변경이력 / 헤더 규칙 |
| D-7 | 기획 | 보안 모델 | `docs/SECURITY.md` | curl-pipe-bash 보안 패턴 / sha256 검증 의무 |
| D-8 | PM | PM 프로필 | `.opal/AGENT.md` | 금지사항 / 배포 경계 / 변경이력 의무 |

# PLAN: 설치 스크립트 Python 최소버전 게이트 + 3.14 설치 유도 (플랫폼 대칭화)

> 작성일: 2026-08-10 | 태스크: 087 | 파이프라인: opp (agentic)
> 입력: TASK.md
> 출력: PLAN.md

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md (087) | `tasks/087-260810-opp-파이썬-버전게이트-설치유도/TASK.md` | 요구사항 R-1~R-9, 확정 설계 방향 F-1~F-6 |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh` | macOS/Linux 공용 인스톨러 본체 — venv 생성·재사용 결함(`:1311-1332`), Node 안내 대칭 패턴(`:1209-1210`) |
| D-3 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | 미러링 원본 SSOT — `Find-Python`(`:577-598`), `Install-WindowsPython`(`:600-670`), 호출부(`:351-363`) |
| D-4 | 소스 | linux.sh | `scripts/install/linux.sh` | Linux 진입점 — install-mac.sh 단순 위임(`:39`) 확인 |
| D-5 | 소스 | macos.sh | `scripts/install/macos.sh` | macOS 진입점 — install-mac.sh 단순 위임(`:44`) 확인 |
| D-6 | 소스 | doctor checks.sh | `opal/tools/doctor/lib/checks.sh` | `_resolve_python3`(`:52-65`), python 체크(`:102-110`), Node 하한 판정 선례(`:88-100`) |
| D-7 | 소스 | requirements.txt | `opal/tools/requirements.txt` | `mcp>=1.1.0` 하한 근거(`:23`), 경로 주석 오류(`:2`, `:27`) |
| D-8 | 소스 | opal-cli update.sh | `opal/tools/opal-cli/lib/update.sh` | 업데이트 경로가 `install/macos.sh`·`install-mac.sh`만 호출(`:394-397`) — Linux에서 linux.sh 미경유 |
| D-9 | 소스 | install.sh | `scripts/install.sh` | one-liner 플랫폼 디스패치(`:466-477`) — macos.sh / linux.sh 선택 |
| D-10 | 소스 | 기존 테스트 하네스 | `scripts/tests/test_version_stamp.sh`, `scripts/tests/test_console_scan.sh` | bash 3.2 호환·mktemp 격리·pass/fail 카운터 패턴 (`test_version_stamp.sh:11-40`), 실 `~/.opal/` 불가침 격리 규약 (`test_console_scan.sh:17-20`) |
| D-11 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 작성 의무·배포 경계·플랫폼 분기 격리(§구현 규칙) |
| D-12 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 2-Layer 배포 모델(§배포 모델), Python 의존성 절(`:310-314`), Node.js 도구 절(`:316-320`), 변경이력 표(`:398~`) |
| D-13 | 설계 | PROJECT.md | `docs/PROJECT.md` | 원칙 3 플랫폼 독립성(`:17`), 프로젝트 구성 — Framework 전문 에이전트(`:158`) |
| D-14 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 금지사항 4종(`:59-66`), 도메인 검토 기준(`:19-25`) |
| D-15 | 설계 | citation-rules.md | `~/.opal/references/harness/citation-rules.md` | 인용 포맷 §2 / 단계별 의무 §4 / 용어 일관성 §7 |
| D-16 | 설계 | coding-principles.md | `~/.opal/references/harness/coding-principles.md` | §2 PLAN(Simplicity First), §4 EXECUTE(Surgical·증거) |
| D-17 | 외부 | Homebrew Formula python@3.14 | [formulae.brew.sh — python@3.14](https://formulae.brew.sh/formula/python@3.14) | macOS 자동 설치 수단(포뮬러명·keg-only 경로 규약) |
| D-18 | 외부 | Python Downloads | [python.org/downloads](https://www.python.org/downloads/) | 폴백 수동 설치 안내 URL (Windows 안내 `windows.ps1:620`와 대칭) |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `scripts/install-mac.sh` | **macOS+Linux 공용** 인스톨러 본체 | **예** (핵심) | `:1311-1332` venv 생성/재사용, `:1223` 호출부, `:1883` 메뉴[4] 호출부, `:1209-1210` Node 안내 선례 |
| `scripts/install/windows.ps1` | Windows 인스톨러 (미러링 SSOT) | **예** | `:577-598` Find-Python, `:600-670` Install-WindowsPython, `:351-363` 호출부, `:903-909` Install-OpalVenv |
| `scripts/install/linux.sh` | Linux 진입 래퍼 | **예** (주석·변경이력만) | `:39` `exec bash "${INSTALLER}"` — 로직 없음 |
| `scripts/install/macos.sh` | macOS 진입 래퍼 | 아니오 | `:44` `exec bash "${INSTALLER}"` — 동일 위임, 변경 불요 |
| `opal/tools/doctor/lib/checks.sh` | doctor 사후 진단 | **예** | `:52-65` `_resolve_python3`, `:102-110` python 체크 |
| `opal/tools/requirements.txt` | Python 의존성 목록 | **예** | `:2` 경로 주석 오류, `:23` `mcp>=1.1.0`, `:27` 동일 경로 오류 |
| `docs/ARCHITECTURE.md` | 아키텍처 문서 | **예** (docs 갱신) | `:310-314` Python 의존성 절에 요구 버전 미기재 (Node 절 `:316-320`은 점검 동작을 명시) |

### 현재 상태 (실측)

**(1) POSIX 계열은 단일 스크립트다 — Linux는 별도 구현이 아니다**

- `scripts/install/macos.sh:44` 와 `scripts/install/linux.sh:39` 는 **둘 다** `exec bash "${INSTALLER}"` 로 `scripts/install-mac.sh` 에 위임한다. 로직이 0줄이다 (→ D-4, D-5).
- `scripts/install.sh:472-477` 이 `uname` 판정으로 두 래퍼 중 하나를 고르고, `opal/tools/opal-cli/lib/update.sh:394-397` 은 **linux.sh를 아예 호출하지 않고** `install/macos.sh` → `install-mac.sh` 순으로 폴백한다 (→ D-8).
- 즉 **Linux 사용자의 `opal-cli update` 경로는 linux.sh를 경유하지 않는다.** 게이트를 linux.sh에 넣으면 이 경로에서 통째로 우회된다.
- install-mac.sh는 이미 OS 분기 선례를 갖는다 — `:1339` `if [[ "$(uname -s)" == "Linux" ]]` (Playwright 캐시 경로).

**(2) venv 결함 (재확인)**

- `scripts/install-mac.sh:1324` `python3 -m venv "$venv_dir"` — PATH의 `python3`를 버전 확인 없이 사용.
- `scripts/install-mac.sh:1326-1328` — `.venv` 디렉토리 존재만으로 `"venv 기존 사용"` 통과. 버전 재검증 없음.
- 호출부는 **단일 병목**이다: `install_opal()` 내부 `:1223` 과 메뉴 [4] `:1883` 두 곳뿐이며 둘 다 `install_opal_venv` 를 부른다. → 게이트를 `install_opal_venv` 진입부에 두면 전 경로가 덮인다.

**(3) 소유자 머신 실측 (비파괴 검증의 기준선)**

| 항목 | 실측값 |
|------|--------|
| `~/.opal/.venv/pyvenv.cfg` | `version = 3.14.3` / `home = /opt/homebrew/opt/python@3.14/bin` |
| PATH `python3` | `/opt/homebrew/bin/python3` → 3.14.3 |
| `python3.14` | `/opt/homebrew/bin/python3.14` → 3.14.3 |
| `/usr/bin/python3` | **3.9.6** (Apple 시스템 인터프리터) |
| `brew` | `/opt/homebrew/bin/brew` 보유 |
| `pwsh` | **미보유** — PowerShell 파서 검증 불가 |
| `bash -n` (3개 셸 스크립트) | 전부 PASS (변경 전 기준선 확보) |

→ **`/usr/bin/python3`(3.9.6)가 이 머신에 실재한다.** 이것이 "3.9 환경 모의"의 실물 픽스처가 된다. 별도 컨테이너·모의 없이 실제 3.9 인터프리터와 실제 3.9 venv로 게이트 거부를 증명할 수 있다.

**(4) `/usr/bin/python3` 하드코딩 6개소의 성격**

`:155`, `:188`, `:374`, `:416`, `:1232`, `:1613` — 전부 **install 시점의 stdlib-only JSON/정규식 처리**(설정 머지·어댑터 생성)다. venv 생성 이전에 실행되어야 하므로 시스템 인터프리터 고정이 의도된 설계다. 3.9.6에서 정상 동작한다. 예외로 `:925`(setting.json scaffold 병합)만 `/usr/bin/python3`가 아닌 PATH `python3`를 사용해 패턴이 어긋난다.

**(5) Windows 규약 (미러링 SSOT)**

- `windows.ps1:592` — `"$output" -match '^Python\s+\d+\.\d+'` 패턴 매칭만 수행, 하한 판정 없음.
- `windows.ps1:613` — `if ($env:OPAL_AUTO_INSTALL_PYTHON -eq '0')` 가 **함수 최상단 첫 분기**. 이 배치가 옵트아웃 검증 가능성의 근거다.
- `windows.ps1:618-622` — winget 미보유 시 warn + python.org 안내 + `$false` 반환 (graceful).
- `windows.ps1:654-666` — PATH 미반영 대비 **표준 설치 경로 직접 탐색** 폴백.
- `windows.ps1:903-909` — `Install-OpalVenv` 는 Python 부재 시 warn 후 `return` (설치 중단 아님).

**(6) doctor 현황**

`opal/tools/doctor/lib/checks.sh:52-65` `_resolve_python3` 는 `python3 → python → py` 순회 + `^3\.[0-9]+\.[0-9]+$` 검증만 한다. 3.9.6도 `_pass` 처리된다(`:107`). 반면 Node는 이미 하한 판정 선례를 갖는다 — `:93-97` `if [[ "${nmaj:-0}" -ge 18 ]] ... else _fail "Node.js ${nver} — v18+ 필요"`. **이 Node 패턴이 Python 판정의 사내 선례다.** `_resolve_python3` 의 유일한 호출처는 `:104` 하나다.

### 영향 범위

| 영향 대상 | 내용 | 위험도 |
|----------|------|--------|
| macOS 클린 설치 | 3.11 미만만 있으면 **설치가 중단**됨 (현행: 통과 후 pip 실패) | 중 — 의도된 fail-fast (F-6) |
| Linux 전 경로 | 동일 게이트가 install-mac.sh 경유로 자동 적용 | 중 |
| Windows 기존 3.11+ 환경 | `Find-Python` 후보 순서 확장 — 동작 불변 기대 | 저 |
| Windows 기존 3.9/3.10 환경 | 자동 설치가 신규 트리거됨 | 중 |
| 소유자 머신 재설치 | 3.14.3이므로 게이트 통과·venv 재생성 없음 | 무 |
| `/usr/bin/python3` 6개소 | **미변경** (§6 리스크 R-2 참조) | 무 |
| 배포본 `~/.opal/` | 직접 편집 없음 — 소스만 수정 | 무 |
| 작업트리 086 미커밋 변경 | 계획 범위에서 완전 제외 | 무 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

없음. (검증 하네스는 스크래치패드에서 임시 생성하며 저장소에 파일을 추가하지 않는다 — §5 참조)

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `scripts/install-mac.sh` | Python 버전 계약 상수 블록 + 게이트 함수군 8종 신설, `install_opal_venv` 배선, 변경이력 | R-1·R-2·R-3·R-4·R-6·R-9 (→ D-1) |
| M-2 | `scripts/install/windows.ps1` | 상수 2종 + `Test-PythonMinVersion` 신설, `Find-Python` 하한 판정, `Install-WindowsPython` 상수화, 호출부 문구, 변경이력 | R-1·R-5·R-9 (→ D-3) |
| M-3 | `scripts/install/linux.sh` | 게이트 위치 명시 주석 + 변경이력 (동작 무변경) | R-6 위치 정합 (→ D-4) |
| M-4 | `opal/tools/doctor/lib/checks.sh` | 하한 상수 + `_version_ge` 신설, `_resolve_python3` 후보 확장, python 체크 실패 판정, 변경이력 | R-7 (→ D-6) |
| M-5 | `opal/tools/requirements.txt` | 요구 Python 버전 명시 + `~/.opal/venv/` → `~/.opal/.venv/` 정정 (2개소) | R-8 (→ D-7) |
| M-6 | `docs/ARCHITECTURE.md` | §Python 의존성에 요구 버전 1행 추가 | docs 갱신 (→ D-12 `:309-313`) |

#### 삭제

없음.

### 설계 결정 (TASK 대비 이탈 1건 — PM Gate 확인 요망)

> **DD-1. R-6의 구현 위치를 `scripts/install/linux.sh` → `scripts/install-mac.sh`(Linux 분기)로 변경한다.**
>
> - TASK.md R-6은 구현 위치를 `scripts/install/linux.sh`로 지정한다 (→ D-1 R-6).
> - 그러나 `scripts/install/linux.sh:39` 는 `exec bash "${INSTALLER}"` 단일 위임이며 자체 로직이 0줄이다 (→ D-4).
> - 결정적 근거: `opal/tools/opal-cli/lib/update.sh:394-397` 이 `install/macos.sh` → `install-mac.sh` 순으로만 폴백하고 **linux.sh를 호출하지 않는다** (→ D-8). linux.sh에 게이트를 두면 Linux 사용자의 `opal-cli update` 경로에서 게이트가 100% 우회된다.
> - 따라서 게이트는 install-mac.sh에 두고, 설치 수단만 `uname -s` 로 분기한다 — 이는 install-mac.sh의 기존 OS 분기 선례(`:1339` Playwright 캐시)와 동일 패턴이며 F-5(판정 공통·설치수단 어댑터 분기)에 정합한다.
> - R-6의 AC("자동 설치를 시도하는 코드가 없다")는 그대로 충족되고, 위치 지정은 linux.sh에 **게이트 소재를 가리키는 주석**(M-3)으로 보완한다.

### 구현 순서

| 순서 | 작업 | 파일 | Step | 예상 난이도 |
|------|------|------|------|-----------|
| 1 | 상수 + 게이트 함수군 신설 | `scripts/install-mac.sh` | Step 1 | 상 |
| 2 | Windows 하한 판정 미러링 | `scripts/install/windows.ps1` | Step 2 | 중 |
| 3 | doctor 하한 판정 | `opal/tools/doctor/lib/checks.sh` | Step 3 | 하 |
| 4 | requirements 주석 정정 | `opal/tools/requirements.txt` | Step 4 | 하 |
| 5 | `install_opal_venv` 배선 (Step 1 의존) | `scripts/install-mac.sh` | Step 5 | 중 |
| 6 | linux.sh 위치 주석 | `scripts/install/linux.sh` | Step 6 | 하 |
| 7 | 변경이력 일괄 갱신 | 4개 파일 | Step 7 | 하 |
| 8 | ARCHITECTURE.md 갱신 | `docs/ARCHITECTURE.md` | Step 8 | 하 |
| 9 | 검증 실행 (PM 직접) | — | Step 9 | 중 |

> 원칙: 의존 받는 쪽(상수·순수 함수)을 먼저 만들고(Step 1), 그것을 소비하는 배선(Step 5)을 뒤에 둔다 (→ D-16 §2).

---

### 핵심 설계

#### 2.1 공통 제약 (전 Step 적용)

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 변경 대상은 `scripts/`, `opal/tools/`, `docs/` 프로젝트 소스로 한정한다. 본 태스크는 install 실행(배포)을 포함하지 않는다.
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → 하한 판정은 플랫폼 무관 순수 함수로 두고, `uname -s` 분기는 **설치 수단 함수 1개**(`install_platform_python`) 내부에만 존재한다.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" → Step 7에서 `(087)` 표기로 일괄 적용한다.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층에서만 흡수한다."
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 = English" / "문서 본문 = 한국어" → 신설 함수명·상수명은 영어, 로그 문구는 한국어(기존 스크립트 전례와 동일).
- [MUST] `~/.opal/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다." → EXECUTE 완료 후 자동 커밋·자동 배포(install 실행) 금지.
- [MUST] **bash 3.2 호환** — macOS 기본 bash는 3.2이며 `scripts/install-mac.sh:46` 이 `set -euo pipefail` 아래에서 실행된다. 연관배열(`declare -A`)·`mapfile`·`${var,,}` 사용 금지. 기존 테스트 하네스도 동일 제약을 명시한다 (`scripts/tests/test_version_stamp.sh:11`).
- [MUST] **`local` 선언과 명령 치환 대입 분리** — `local x="$(cmd)"` 는 `local` 의 종료코드가 `cmd` 의 실패를 가리므로 금지한다. `local x; x="$(cmd)" || return 1` 형태로 쓴다. 기존 코드도 이 형태를 따른다 (`scripts/install-mac.sh:1201-1202`).
- 변경 범위 밖 파일(특히 작업트리에 미커밋 상태로 존재하는 `docs/architecture-diagram/`, `.opal/brain/`)은 **읽지도 쓰지도 않는다** (→ D-16 §4 Surgical).

#### 2.2 `scripts/install-mac.sh` — Python 버전 계약 (R-1)

`# ─── OPAL Markers ───` 블록 직후(현행 `:58-65` 뒤, `# ─── Logging ───` `:67` 앞)에 상수 블록을 신설한다. 위치 근거: 로깅 함수보다 앞에 두어 순수 함수가 로깅에 의존하지 않음을 구조로 강제한다.

```bash
# ─── Python Version Contract (087) ───────────────────────
# BEGIN opal-python-contract
OPAL_PYTHON_MIN="3.11"          # 하한 — 미달 시 설치 중단
OPAL_PYTHON_TARGET="3.14"       # 자동 설치/권장 대상
OPAL_PYTHON_DOWNLOAD_URL="https://www.python.org/downloads/"
# 동일 계약 미러: scripts/install/windows.ps1 $OpalPythonMin/$OpalPythonTarget,
#                opal/tools/doctor/lib/checks.sh OPAL_PYTHON_MIN/OPAL_PYTHON_TARGET
# END opal-python-contract
```

- 하한 `3.11` / 대상 `3.14` 분리 근거: (→ D-1 F-2). 하한을 3.14로 못 박으면 3.12·3.13 사용자가 불필요하게 차단된다.
- 하한 `3.11` 의 하위 근거: `opal/tools/requirements.txt:23` `mcp>=1.1.0` 이 Python 3.10 이상을 요구한다. 3.11은 여기에 1버전 여유를 둔 값이다 (→ D-1 §A).
- `BEGIN`/`END` ASCII 센티널은 검증 하네스가 결정적으로 블록을 추출하기 위한 seam이다 (§5 참조). 다국어 괘선(`─`)에 의존하는 sed 패턴을 피한다.
- [MUST] R-1 AC 준수: 상수 정의부 외에 `3.11`·`3.14` 문자열 리터럴이 install-mac.sh 내에 **0건**이어야 한다. 후보 인터프리터 목록도 리터럴 나열이 아니라 두 상수에서 **파생**한다 (§2.3 `python_candidates`).

#### 2.3 `scripts/install-mac.sh` — 게이트 함수군 신설 (R-2·R-3·R-4·R-6)

`install_opal_venv()`(현행 `:1311`) **직전**에 함수군을 삽입한다. 함수는 두 부류로 엄격히 분리한다.

**[MUST] 순수/비순수 분리 규약** — 아래 6개 함수는 **로그를 출력하지 않고 파일을 쓰지 않으며 전역을 읽지 않는다**(상수 2종 제외). 모든 입력은 인자로 받는다. 이 순수성이 §5 비파괴 검증의 전제이며, 특히 `venv_meets_min` 이 `~/.opal/.venv` 를 **읽기만** 한다는 보장의 근거다.

| # | 시그니처 | 반환 | 대응 Windows SSOT |
|---|---------|------|------------------|
| F-a | `python_candidates()` | stdout: 후보 명령명 개행 구분 | (신설 — 상수 파생) |
| F-b | `python_version_of <py>` | stdout `"MAJ.MIN"` / rc 0·1 | (신설) |
| F-c | `python_meets_min <py>` | rc 0(충족)·1(미달) | (신설 — `Test-PythonMinVersion` 과 쌍) |
| F-d | `find_python()` | stdout 절대경로 / rc 0·1 | `Find-Python` (`windows.ps1:577`) |
| F-e | `venv_meets_min <venv_dir>` | rc 0·1 | (신설) |
| F-f | `python_autoinstall_enabled()` | rc 0(활성)·1(옵트아웃) | `windows.ps1:613` 분기 |
| F-g | `install_platform_python()` | rc 0·1 + 로그 | `Install-WindowsPython` (`windows.ps1:600`) |
| F-h | `ensure_python()` | 전역 `OPAL_PYTHON_BIN` 설정, rc 0·1 + 로그 | `windows.ps1:351-356` 호출부 |

시그니처 계약을 `[MUST]` 포맷으로 확정한다:

- [MUST] 신설 — `scripts/install-mac.sh` (`install_opal_venv` 직전, 현행 `:1311` 기준 위치): `python_candidates()` → stdout에 `python3.14`, `python3.13`, `python3.12`, `python3.11`, `python3` 를 이 순서로 출력한다. 목록은 리터럴이 아니라 `OPAL_PYTHON_TARGET` 마이너부터 `OPAL_PYTHON_MIN` 마이너까지 **내림차순 파생** + 마지막에 `python3`(PATH 기본) 를 덧붙인 결과다.
- [MUST] 신설 — `python_version_of <python_path_or_name>` → 성공 시 stdout에 `"<major>.<minor>"` 를 출력하고 rc 0. 실행 불가·파싱 실패 시 출력 없이 rc 1. 구현은 `"$py" -c 'import sys; print("%d.%d" % sys.version_info[:2])'` 를 사용한다 (`--version` 문자열 파싱보다 견고).
- [MUST] 신설 — `python_meets_min <python_path_or_name>` → 해당 인터프리터가 `OPAL_PYTHON_MIN` 이상이면 rc 0, 미달·해석 실패면 rc 1. 비교는 major/minor 정수 비교이며 `(( ... )) && return 0` 형태로 작성한다(`set -e` 하에서 AND-리스트 예외로 안전함을 실측 확인).
- [MUST] 신설 — `find_python()` → `python_candidates()` 순회 중 `command -v` 로 해석되고 `python_meets_min` 을 통과하는 **첫 후보의 절대 경로**를 stdout에 출력하고 rc 0. 모든 후보가 미달·부재면 출력 없이 rc 1. → R-2 AC("3.11 이상 인터프리터의 절대 경로 반환 / 3.11 미만만 존재하면 빈 값 + 실패 상태") 직결.
- [MUST] 신설 — `venv_meets_min <venv_dir>` → `<venv_dir>/pyvenv.cfg` 의 `version = X.Y.Z` 를 읽어 `OPAL_PYTHON_MIN` 이상이면 rc 0. 파일 부재·키 부재·파싱 실패·미달은 모두 rc 1. **쓰기 작업을 하지 않는다.** 근거: 소유자 머신 `~/.opal/.venv/pyvenv.cfg` 에 `version = 3.14.3` 존재 실측, 3.9 venv도 동일 키를 기록한다.
- [MUST] 신설 — `python_autoinstall_enabled()` → `[[ "${OPAL_AUTO_INSTALL_PYTHON:-1}" != "0" ]]` 판정 결과를 rc로 반환한다. **`OPAL_AUTO_INSTALL_PYTHON` 문자열은 install-mac.sh 전체에서 이 함수 안 1회만 등장한다.** 신규 환경변수명을 만들지 않는다 (→ D-1 F-3).
- [MUST] 신설 — `install_platform_python()` → rc 0(설치 후 하한 충족 인터프리터 확보) / rc 1(스킵·실패). **첫 분기는 반드시 옵트아웃 검사**여야 한다 — `windows.ps1:613` 의 배치를 문자 그대로 미러링한다. 이 배치가 §5-(c) 옵트아웃 검증의 성립 조건이다.
- [MUST] 신설 — `ensure_python()` → 성공 시 전역 `OPAL_PYTHON_BIN` 에 절대 경로를 설정하고 rc 0. 실패 시 원인·해결 안내를 출력하고 rc 1. **`exit` 를 직접 호출하지 않는다** — 종료 결정은 호출자(`install_opal_venv`)가 내린다(테스트 가능성 확보).

`install_platform_python()` 의 플랫폼 어댑터 분기 (F-4·F-5):

```
1. python_autoinstall_enabled 실패        → info "자동 설치 옵트아웃(OPAL_AUTO_INSTALL_PYTHON=0) — 스킵" ; return 1
2. case "$(uname -s)" in
     Darwin)  command -v brew 없음 → warn + brew 설치 URL + $OPAL_PYTHON_DOWNLOAD_URL 안내 ; return 1
              brew install "python@${OPAL_PYTHON_TARGET}"  (실패 시 warn + URL 안내 ; return 1)
              find_python 재시도 → 실패 시 "$(brew --prefix)/opt/python@${OPAL_PYTHON_TARGET}/bin/python${OPAL_PYTHON_TARGET}" 직접 탐색
     Linux)   info "Linux는 자동 설치를 수행하지 않습니다" + 배포판 패키지 매니저/python.org 안내 ; return 1
     *)       return 1
   esac
```

- macOS 자동 설치 수단은 `brew install python@3.14` 이며 포뮬러명은 `python@${OPAL_PYTHON_TARGET}` 로 파생한다 ([Homebrew python@3.14](https://formulae.brew.sh/formula/python@3.14)).
- brew 설치 직후 PATH 미반영 대비 **prefix 직접 탐색** 폴백은 `windows.ps1:654-666`(winget 표준 경로 직접 탐색)의 macOS 등가물이다 (→ D-1 F-1 미러링).
- [MUST] `Linux` 분기에는 **패키지 매니저를 호출하는 코드를 넣지 않는다** — `apt`/`dnf`/`pacman` 어떤 것도 실행하지 않는다 (→ D-1 F-4, R-6 AC). 안내는 배포판 중립 1~2줄로 제한하여 배포판별 분기가 생기지 않게 한다.
- 안내 문구는 `scripts/install-mac.sh:1209-1210`(Node 미설치 안내)의 문형을 따른다 — `warn` 1줄 + `info "  설치: <URL> 또는 <명령>"` 1줄 (→ D-2).

#### 2.4 `scripts/install-mac.sh` — `install_opal_venv` 배선 (R-3 fail-fast · R-4 재검증)

현행 `:1311-1333` 을 다음 순서로 재구성한다.

```
install_opal_venv() {
    local venv_dir="$USER_HOME/.opal/.venv"
    local req_src="..."                       # :1313 유지
    [[ -f "$req_src" ]] || { warn ...; return; }   # :1315-1318 유지

    # (신설) 게이트 — F-6 fail-fast
    if ! ensure_python; then
        error "Python ${OPAL_PYTHON_MIN} 이상을 확보하지 못해 설치를 중단합니다."
        exit 1
    fi

    # (신설) R-4 — 기존 venv 버전 재검증
    if [[ -d "$venv_dir" ]] && ! venv_meets_min "$venv_dir"; then
        warn "기존 venv가 Python ${OPAL_PYTHON_MIN} 미만입니다 — 폐기 후 재생성합니다: $venv_dir"
        rm -rf "$venv_dir"
    fi

    if [[ ! -d "$venv_dir" ]]; then
        "$OPAL_PYTHON_BIN" -m venv "$venv_dir"      # :1324 python3 → $OPAL_PYTHON_BIN
        success "venv 생성: $venv_dir ($("$OPAL_PYTHON_BIN" -V 2>&1))"
    else
        success "venv 기존 사용: $venv_dir"
    fi
    ... 이하 :1331 이후 pip 블록 불변 ...
}
```

- [MUST] `scripts/install-mac.sh:1324` 의 `python3 -m venv` 를 `"$OPAL_PYTHON_BIN" -m venv` 로 치환한다. 이것이 결함 B-1의 직접 수정점이다 (→ D-1 §B-1).
- [MUST] R-3 AC (c) "최종적으로 3.11+ 확보 실패 시 **exit 0이 아닌 상태로 중단**" → `exit 1` 을 사용한다. `return` 은 호출자가 계속 진행하므로 AC를 만족하지 못한다.
- `rm -rf "$venv_dir"` 는 **`venv_meets_min` 이 rc 1을 반환한 경우에만** 실행된다. `-d` 검사와 결합되어 있어 `$venv_dir` 이 항상 `$USER_HOME/.opal/.venv` 리터럴 파생임을 보장한다. → 리스크 R-3 참조.
- 재생성 사실은 `warn` 으로 출력한다 — R-4 AC("재생성 사실이 로그에 출력된다")는 quiet 기본 모드에서도 보여야 하므로 `info`/`success`(`:72-73`, `OPAL_VERBOSE=1` 시에만 출력)가 아닌 `warn`(`:74`, 항상 출력)을 쓴다. **로그 레벨 선택이 AC 충족의 일부다.**
- 게이트 위치가 `install_opal_venv` 진입부인 근거: 호출부가 `:1223`(전체 설치)과 `:1883`(메뉴 [4])뿐이며 (→ D-2), 여기 한 곳에 두면 대화형·비대화형·`opal-cli update` 전 경로가 덮인다.

#### 2.5 `scripts/install/windows.ps1` — 하한 판정 미러링 (R-1·R-5)

**(1) 상수** — `# ─── 상수 ───` 블록 말미(`$HardeningEnd` `:127` 바로 아래, `# ─── 유틸리티 ───` `:129` 앞)에 추가한다.

```powershell
# Python 버전 계약 — install-mac.sh OPAL_PYTHON_MIN/OPAL_PYTHON_TARGET 미러 (087)
$OpalPythonMin    = '3.11'
$OpalPythonTarget = '3.14'
```

**(2) `Test-PythonMinVersion` 신설** — `Find-Python`(`:577`) 직전에 배치.

- [MUST] 신설 — `scripts/install/windows.ps1`: `function Test-PythonMinVersion { param([Parameter(Mandatory)][string]$PythonPath) }` → `[bool]` 반환. 대상 인터프리터가 `$OpalPythonMin` 이상이면 `$true`. 판정 규칙(major/minor 정수 비교)은 bash `python_meets_min` 과 **문자 그대로 동일한 계약**이다 (→ D-1 F-5).

**(3) `Find-Python` 개정** — 현행 `:587-597`.

- [MUST] 현행 `scripts/install/windows.ps1:587`: `foreach ($name in @('python3', 'python', 'py'))` → 후보 목록 앞에 `$OpalPythonTarget`~`$OpalPythonMin` 파생 versioned 이름(`python3.14`…`python3.11`)을 **덧붙인** 목록으로 교체한다.
- [MUST] 현행 `scripts/install/windows.ps1:592`: `if ($LASTEXITCODE -eq 0 -and "$output" -match '^Python\s+\d+\.\d+') { return $cmd.Source }` → 패턴 매칭 통과에 더해 `Test-PythonMinVersion $cmd.Source` 가 `$true` 인 경우에만 `return` 하도록 조건을 강화한다. 미달 후보는 **채택하지 않고 다음 후보로 계속 순회**한다.
- [MUST] `Find-Python` 은 **모든 후보를 끝까지 순회한 뒤에만** `$null` 을 반환한다. 첫 후보가 미달이라는 이유로 조기 포기하면, 3.11+가 다른 경로에 있는 사용자에게 불필요한 winget 설치가 트리거된다 (→ §6 리스크 R-5).
- → R-5 AC("3.9만 설치된 상태에서 `Find-Python` 이 해당 인터프리터를 채택하지 않고 자동 설치 경로로 분기") 직결.

**(4) `Install-WindowsPython` 상수화** — 현행 `:600-670`. **구조·옵트아웃 동작은 변경하지 않는다.**

- `:613` 옵트아웃 첫 분기 — **불변** (bash 미러링의 SSOT이므로 손대지 않는다).
- [MUST] 현행 `scripts/install/windows.ps1:629`: `winget install --id Python.Python.3.14 ...` → `--id "Python.Python.$OpalPythonTarget"` 로 상수 참조화 (R-1 AC).
- [MUST] 현행 `scripts/install/windows.ps1:656-657`: `'Programs\Python\Python314\python.exe'` / `'Python314\python.exe'` → `"Python$($OpalPythonTarget -replace '\.','')"` 파생으로 치환.
- `:624`, `:636`, `:650`, `:663`, `:668` 의 `3.14` 표기 로그 문구도 `$OpalPythonTarget` 보간으로 통일한다.
- `:624` 문구 `'Python 미설치 감지 — ...'` → `'Python 미설치 또는 최소 버전 미달 감지 — ...'` 로 정정 (트리거 조건 확대 반영).

**(5) 호출부·안내 문구** — `:351-363`, `:903-909`, `:1856-1857`.

- `:351-356` 의 `if (-not $py) { if (Install-WindowsPython) { $py = Find-Python } }` 제어 흐름은 **구조 변경 없이 그대로 둔다.** `Find-Python` 이 하한 미달을 `$null` 로 반환하게 되었으므로 자동 설치 트리거가 자동으로 "미설치 또는 하한 미달"로 확대된다 — R-5의 "트리거 조건 확대"는 별도 조건문 추가 없이 달성된다 (최소 변경).
- `:360` `'Python 미설치 — ...'` → `"Python ${OpalPythonMin} 이상 미확보 — ..."` 로 문구 정정.
- `:904-909` `Install-OpalVenv` 의 Python 부재 안내에 하한 문구를 포함시킨다(진단성). **동작(warn 후 `return`)은 변경하지 않는다** — 근거: R-5 AC는 자동 설치 분기까지만 요구하며, Windows에 fail-fast를 신규 도입하는 것은 TASK 범위 초과다 (→ §6 리스크 R-6).
- `:1857` 마무리 안내의 `winget install Python.Python.3.14` → `$OpalPythonTarget` 보간.

#### 2.6 `opal/tools/doctor/lib/checks.sh` — 하한 판정 (R-7)

- `# ─── 공통 상수 ───`(현행 `:23-25`, `OPAL_HOME` 정의부)에 `OPAL_PYTHON_MIN` / `OPAL_PYTHON_TARGET` 을 추가한다. 변수명을 install-mac.sh와 **동일하게** 맞춘다(§6 리스크 R-7 용어 일관성).
- [MUST] 신설 — `opal/tools/doctor/lib/checks.sh`: `_version_ge <ver> <min>` → `<ver>` 이 `<min>` 이상이면 rc 0. `3.9.6` 같은 3자리와 `3.11` 2자리를 모두 받아 major/minor만 비교한다.
- [MUST] 현행 `opal/tools/doctor/lib/checks.sh:54`: `for cmd in python3 python py; do` → 후보 앞에 `python3.14`…`python3.11` 파생 이름을 덧붙이고, **하한을 충족하는 첫 후보를 우선 채택**한다. 하한 충족 후보가 없으면 기존처럼 "3.x인 첫 후보"를 반환하여 `check_deps` 가 실제 버전을 표시할 수 있게 한다(진단 정보 보존).
- [MUST] 현행 `opal/tools/doctor/lib/checks.sh:104-110`: `_pass "${py_cmd} ${py_ver}"` → `_version_ge "$py_ver" "$OPAL_PYTHON_MIN"` 통과 시에만 `_pass`, 미달이면 `_fail "${py_cmd} ${py_ver} — Python ${OPAL_PYTHON_MIN}+ 필요 (권장 ${OPAL_PYTHON_TARGET})"`.
- 메시지 형식은 동일 파일의 Node 선례를 그대로 따른다 — `opal/tools/doctor/lib/checks.sh:96`: `_fail "Node.js ${nver:-?} — v18+ 필요"` (→ D-6). 새 표현을 발명하지 않는다.
- `_resolve_python3` 의 호출처는 `:104` 단 1곳이므로 (전수 grep 확인) 변경 파급은 이 함수 내부로 닫힌다.
- → R-7 AC("Python 3.9 환경에서 python 항목이 실패로 표시되고 요구 하한이 메시지에 포함") 직결.

#### 2.7 `opal/tools/requirements.txt` — 요구 버전 명시 + 경로 정정 (R-8)

- [MUST] 현행 `opal/tools/requirements.txt:2`: `# 설치: ~/.opal/venv/bin/pip install -r requirements.txt` → `~/.opal/.venv/bin/pip` 로 정정. 실제 경로 근거: `scripts/install-mac.sh:1312` `local venv_dir="$USER_HOME/.opal/.venv"`.
- [MUST] 현행 `opal/tools/requirements.txt:27`: `# 설치 후 별도 초기화 필요: ~/.opal/venv/bin/playwright install` → **동일 오류가 여기에도 있다.** 함께 정정한다. (TASK R-8은 `:1-2`만 지목했으나 AC가 "`~/.opal/venv/` 표기가 파일 내 0건"이므로 `:27` 정정이 AC 충족의 필수 조건이다.)
- `:1` 아래에 요구 버전 주석 2줄 추가: 요구 Python 3.11 이상 / 권장 3.14. 하한 근거를 같은 주석에 병기한다 — `mcp>=1.1.0`(`:23`)이 Python 3.10+ 를 요구.
- 패키지 버전 지정자(`mcp>=1.1.0` 등)는 **일절 변경하지 않는다** — 본 태스크는 의존성 해석 실패의 원인(인터프리터 버전)을 고치는 것이지 의존성 자체를 바꾸는 것이 아니다 (→ D-16 §4 Surgical).

#### 2.8 `scripts/install/linux.sh` — 게이트 소재 주석 (R-6 위치 정합)

- 헤더 `역할:` 절(현행 `:5-9`)에 1~2줄을 추가한다: Python 하한 게이트는 위임 대상인 `scripts/install-mac.sh` 의 `ensure_python()` 에 있으며, Linux는 자동 설치를 수행하지 않고 안내만 한다는 사실.
- **실행 코드는 1줄도 추가하지 않는다.** `:39` `exec bash "${INSTALLER}"` 불변.
- 근거: DD-1. 이 주석이 없으면 후속 유지보수자가 "Linux에는 게이트가 없다"고 오판할 수 있다.

#### 2.9 `docs/ARCHITECTURE.md` — Python 요구 버전 명시 (docs 갱신)

- `docs/ARCHITECTURE.md:310-314` §Python 의존성 절에 1행 추가: 요구 Python 3.11 이상(권장 3.14), 미달 시 설치 스크립트가 중단하고 설치를 안내한다는 사실.
- 판단 근거: 이 절은 Node 의존성에 대해서는 이미 "설치 스크립트가 `node --version`을 점검하고 누락 시 경고만 출력(강제 종료하지 않음)"(`:316-320`)을 명시한다. Python이 이제 **강제 종료** 동작을 갖게 되므로, 두 항목의 서술 비대칭을 남기면 문서가 실제 동작과 어긋난다.

---

## 3. 실행 체크리스트

> 총 9개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2, 3, 4 | **병렬** | 서로 다른 파일, 상호 의존 없음 |
> | 2 | 5, 6 | 병렬 | Step 5는 Step 1 의존(동일 파일 순차) / Step 6은 독립 |
> | 3 | 7, 8 | 병렬 | Step 7은 Step 1·2·3·5·6 이후(동일 파일) / Step 8은 독립 |
> | 4 | 9 | 순차 | 전 Step 완료 후 PM 직접 검증 |

### Step 1: install-mac.sh — Python 버전 계약 상수 + 게이트 함수군 신설

- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §2.2 상수 블록을 `:65` 뒤(`# ─── Logging ───` `:67` 앞)에 `BEGIN/END opal-python-contract` 센티널과 함께 삽입. §2.3 함수 8종(F-a~F-h)을 `install_opal_venv()`(현행 `:1311`) 직전에 `BEGIN/END opal-python-gate` 센티널과 함께 삽입. F-a~F-f는 순수 함수(로그·파일쓰기·전역참조 금지), F-g·F-h만 로그 허용.
- **완료 기준**:
  (1) `bash -n scripts/install-mac.sh` exit 0
  (2) `grep -cE '"3\.11"|"3\.14"|[^0-9]3\.11[^0-9]|[^0-9]3\.14[^0-9]' scripts/install-mac.sh` 결과가 상수 정의 블록 내부 2건에만 해당 (R-1 AC)
  (3) `grep -c 'OPAL_AUTO_INSTALL_PYTHON' scripts/install-mac.sh` == 1 (R-1·F-3)
  (4) `install_platform_python` 본문의 첫 실행 분기가 옵트아웃 검사 (`windows.ps1:613` 미러)
  (5) `install_platform_python` 의 `Linux)` 분기에 `apt`/`dnf`/`pacman`/`yum` 문자열 0건 (R-6 AC)
  (6) 두 센티널 쌍이 각각 정확히 1회씩 존재
- **테스트**: §5-(a) 문법 검사 + §5-(b) 하네스 추출·실행
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 2: windows.ps1 — 상수화 + 하한 판정 미러링

- [ ] 완료
- **파일**: `scripts/install/windows.ps1`
- **작업 내용**: §2.5 (1)~(5) 전부. 상수 2종 추가(`:135` 뒤), `Test-PythonMinVersion` 신설(`:577` 앞), `Find-Python` 후보 확장 + 하한 조건 강화(`:587-597`), `Install-WindowsPython` 리터럴 상수화(`:629`, `:656-657`, 로그 문구), 호출부·안내 문구 정정(`:360`, `:904-909`, `:1857`).
- **완료 기준**:
  (1) `Python.Python.3.14` / `Python314` 하드코딩 리터럴 0건, 전부 `$OpalPythonTarget` 파생
  (2) `windows.ps1:613` 옵트아웃 첫 분기가 **원문 그대로 유지**됨 (diff에 미포함)
  (3) `Find-Python` 이 하한 미달 후보에서 `return` 하지 않고 순회를 계속함
  (4) `Install-WindowsPython` 의 함수 구조(옵트아웃 → winget 부재 → 설치 → PATH 갱신 → 직접 탐색) 5단계 순서 불변
  (5) `Install-OpalVenv` 의 제어 흐름(`return`) 불변 — 문구만 변경
- **테스트**: §5-(a) PowerShell 구문 검사 (pwsh 부재 시 대체 절차)
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 3: doctor checks.sh — 하한 판정 추가

- [ ] 완료
- **파일**: `opal/tools/doctor/lib/checks.sh`
- **작업 내용**: §2.6 전부. 공통 상수부(`:23-25`)에 `OPAL_PYTHON_MIN`/`OPAL_PYTHON_TARGET` 추가, `_version_ge` 신설, `_resolve_python3`(`:52-65`) 후보 확장 + 하한 우선 채택, `check_deps` python 블록(`:104-110`) 실패 판정.
- **완료 기준**:
  (1) `bash -n opal/tools/doctor/lib/checks.sh` exit 0
  (2) 3.9 인터프리터만 해석되는 상황에서 `_fail` 경로를 타고, 메시지에 `3.11` 문자열이 포함됨 (R-7 AC)
  (3) 메시지 형식이 동일 파일 `:96` Node 선례(`— v18+ 필요`)와 동형
  (4) `_resolve_python3` 의 반환 계약(`"<cmd>|<ver>"`, 실패 시 rc 1)이 변경되지 않음 — 호출처 `:104` 무수정 가능
- **테스트**: §5-(d)
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 4: requirements.txt — 요구 버전 명시 + 경로 주석 정정

- [ ] 완료
- **파일**: `opal/tools/requirements.txt`
- **작업 내용**: §2.7 전부. `:1` 아래 요구 버전 주석 2줄 추가, `:2`·`:27` 의 `~/.opal/venv/` → `~/.opal/.venv/` 정정.
- **완료 기준**:
  (1) `grep -c '~/.opal/venv/' opal/tools/requirements.txt` == 0 (R-8 AC)
  (2) 상단 주석에 `3.11` 이상 요구 기재
  (3) 패키지 행(`:5-32`)의 버전 지정자 diff 0건
- **테스트**: 위 grep 2건
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 5: install-mac.sh — install_opal_venv 게이트 배선

- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §2.4 전부. `install_opal_venv()`(`:1311-1333`)에 `ensure_python` 게이트 + `exit 1` fail-fast, `venv_meets_min` 재검증 + `rm -rf` 재생성, `:1324` `python3` → `"$OPAL_PYTHON_BIN"` 치환, 재생성 로그를 `warn` 레벨로 출력.
- **완료 기준**:
  (1) `bash -n scripts/install-mac.sh` exit 0
  (2) `install_opal_venv` 내 `python3 -m venv` 리터럴 0건
  (3) fail-fast 경로가 `exit 1`(≠ `return`)
  (4) `rm -rf` 가 `venv_meets_min` 실패 분기 안에만 존재하고 대상이 `$venv_dir` 단일 변수
  (5) 재생성 안내가 `warn`(항상 출력) — `info`/`success`(`OPAL_VERBOSE=1` 한정) 아님
  (6) `:1331-1333` pip 블록, `:1335` 이후 Playwright 블록 diff 0건
- **테스트**: §5-(a), §5-(b) venv 픽스처 검증
- **의존**: Step 1
- **agent**: `opal-task-agent`

### Step 6: linux.sh — 게이트 소재 주석

- [ ] 완료
- **파일**: `scripts/install/linux.sh`
- **작업 내용**: §2.8. 헤더 `역할:` 절(`:5-9`)에 게이트 소재 + Linux 자동설치 미수행 사실을 1~2줄로 명시.
- **완료 기준**:
  (1) `bash -n scripts/install/linux.sh` exit 0
  (2) `set -euo pipefail`(`:23`) 이후 실행 코드 라인 diff 0건 — 주석·변경이력만 변경
  (3) 자동 설치 관련 실행 코드 0줄 (R-6 AC)
- **테스트**: §5-(a) + `git diff` 육안 확인
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 7: 변경이력 일괄 갱신 (R-9)

- [ ] 완료
- **파일**: `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/install/linux.sh`, `opal/tools/doctor/lib/checks.sh`
- **작업 내용**: §8 변경이력 갱신 계획의 삽입 위치·버전·문구대로 4개 파일에 행 추가.
- **완료 기준**:
  (1) 4개 파일 각각에 `(087)` 을 포함한 신규 행이 정확히 1건씩 추가
  (2) 일시가 `YYYY-MM-DD HH:mm KST` 형식이고 실제 작업 일시(2026-08-10)
  (3) 버전이 각 파일 기존 최신 버전의 다음 semver
  (4) 기존 변경이력 행 diff 0건
  (5) 4개 파일 문법 검사 재통과
- **테스트**: `grep -c '(087)'` 파일별 1건 + §5-(a) 재실행
- **의존**: Step 1, 2, 3, 5, 6
- **agent**: `opal-task-agent`

### Step 8: ARCHITECTURE.md — Python 요구 버전 명시

- [ ] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §2.9. `:310-314` §Python 의존성에 요구 버전 + 미달 시 중단 동작 1행 추가. 문서 하단 변경이력 표(`:398~`)에도 행 추가.
- **완료 기준**:
  (1) §Python 의존성에 `3.11` 이상 요구가 기재됨
  (2) Node 절(`:316-320`)의 "경고만 출력" 서술과 비대칭이 해소됨(Python은 중단됨이 명시)
  (3) 문서 변경이력 표에 087 행 1건 추가
- **테스트**: 육안 검토 (문서 변경)
- **의존**: 없음
- **agent**: PM 직접

### Step 9: 검증 실행 (PM 직접)

- [ ] 완료
- **파일**: 없음 (스크래치패드 하네스만 사용)
- **작업 내용**: §5 검증 절차 (a)~(e)를 순서대로 실행하고 결과를 기록.
- **완료 기준**: §5의 기대값 표가 전부 일치. 불일치 1건이라도 있으면 해당 Step으로 되돌린다.
- **테스트**: §5 자체
- **의존**: Step 1~8
- **agent**: PM 직접

---

## 4. QA 체크리스트

### 기능 테스트 (요구사항 대응)

- [ ] **R-1** — `3.11`/`3.14` 리터럴이 install-mac.sh·windows.ps1 각각의 상수 정의부 외 0건이고, `OPAL_AUTO_INSTALL_PYTHON` 문자열이 파일당 1회만 등장
- [ ] **R-2** — `find_python` 이 3.11+ 절대경로를 반환하고, 3.11 미만만 있는 조건에서 빈 출력 + rc 1
- [ ] **R-3(a)** — `OPAL_AUTO_INSTALL_PYTHON=0` 시 자동 설치를 건너뜀
- [ ] **R-3(b)** — brew 미보유 조건에서 python.org URL 출력
- [ ] **R-3(c)** — 3.11+ 확보 실패 시 exit 0이 아닌 상태로 중단 + 원인 문구 출력
- [ ] **R-4** — 3.9 venv 픽스처에 대해 `venv_meets_min` rc 1 (재생성 대상 판정) + 재생성 로그가 quiet 모드에서도 출력
- [ ] **R-5** — `Find-Python` 이 하한 미달 인터프리터를 채택하지 않고 순회 계속, 전부 미달 시 `$null`
- [ ] **R-6** — Linux 분기에 자동 설치 코드 0줄, 안내 후 중단
- [ ] **R-7** — 3.9 조건에서 doctor python 항목 `_fail` + 메시지에 하한 포함
- [ ] **R-8** — `~/.opal/venv/` 표기 0건, 상단에 3.11+ 요구 기재
- [ ] **R-9** — 4개 파일에 087 행 추가

### 일관성 테스트

- [ ] 하한 값 `3.11` 이 install-mac.sh · windows.ps1 · checks.sh 3개 파일에서 **동일**
- [ ] 대상 값 `3.14` 가 install-mac.sh · windows.ps1 에서 **동일**
- [ ] 옵트아웃 환경변수명이 3플랫폼 문서·코드에서 `OPAL_AUTO_INSTALL_PYTHON` 단일 (신규 명칭 0건)
- [ ] bash `install_platform_python` 의 단계 순서가 `Install-WindowsPython`(`windows.ps1:613-669`) 5단계와 대응
- [ ] 안내 문구 문형이 `install-mac.sh:1209-1210`(Node) 및 `windows.ps1:620` 과 동형
- [ ] doctor 실패 메시지가 `checks.sh:96`(Node) 형식과 동형
- [ ] 순수 함수 6종에 `info`/`warn`/`success`/`error`/`echo` 호출 0건
- [ ] `local x="$(cmd)"` 패턴 신규 도입 0건

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/변수명 규칙 준수 (`docs/CONVENTIONS.md` §언어 규칙)
- [ ] 변경이력 일시 형식 `YYYY-MM-DD HH:mm` KST + 태스크 번호 `(087)` 괄호 표기 (`docs/CONVENTIONS.md` §변경이력)
- [ ] `~/.opal/` 배포본 파일 변경 0건 (`git status` 로 확인 — `.opal/`(프로젝트)와 `~/.opal/`(배포본) 혼동 금지)
- [ ] 086 태스크 미커밋 파일(`docs/architecture-diagram/`, `.opal/brain/`) 변경 0건
- [ ] PLAN 범위 밖 파일 변경 0건 (`git status --short` 가 M-1~M-6 6개 파일 + 086 기존 미커밋분만 표시)

---

## 5. 검증 절차 (PM이 EXECUTE 후 직접 실행)

> 본 태스크는 `opp` 파이프라인이라 TEST 단계가 없다. 아래는 PM이 EXECUTE 완료 후 직접 실행하는 절차이며, 헌법 §4 "Completion requires evidence"의 증거 산출 경로다 (→ D-16 §4).
>
> **[MUST] 격리 원칙** — 아래 절차는 `~/.opal/.venv`(소유자 머신 실환경, 실측 3.14.3)를 **삭제·변경하지 않는다.** 쓰기가 발생하는 모든 픽스처는 스크래치패드 아래에만 생성한다. `install_opal_venv` 를 실제로 실행하는 절차는 (e)에 한정하며 선택 사항이다.
>
> 아래 `$SP` 는 세션 스크래치패드 경로다:
> `SP=/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/<session>/scratchpad/087-verify`

### (a) 문법 검사

**bash** — 3개 스크립트. 변경 전 기준선은 이번 PLAN 조사에서 3건 전부 PASS로 실측했다.

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework
for f in scripts/install-mac.sh scripts/install/linux.sh opal/tools/doctor/lib/checks.sh; do
  bash -n "$f" && echo "PASS $f" || echo "FAIL $f"
done
```

기대: 3행 모두 `PASS`.

**PowerShell** — 이 머신에 `pwsh` 가 **없다**(실측). 두 경로로 나눈다.

```bash
# 경로 1 — pwsh 보유 환경(Windows/설치 후)에서:
pwsh -NoProfile -Command '
  $errs = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile(
      (Resolve-Path ./scripts/install/windows.ps1), [ref]$null, [ref]$errs)
  if ($errs) { $errs | ForEach-Object { $_.Message }; exit 1 } else { "PS PARSE OK" }'
```

```bash
# 경로 2 — pwsh 부재 시(현 머신) 결정적 대체 검사:
python3 - <<'PY'
import re, sys
s = open('scripts/install/windows.ps1', encoding='utf-8').read()
# 문자열/주석을 제거하지 않은 조잡 검사이므로 "변경 전후 델타 0" 만을 판정 근거로 삼는다.
for ch_open, ch_close in (('{','}'), ('(',')'), ('[',']')):
    print(ch_open, s.count(ch_open) - s.count(ch_close))
PY
```

- 판정: `git stash` 로 변경 전 값을 한 번 측정하고, 변경 후 **동일 값**이면 괄호 균형이 보존된 것으로 본다(절대값이 0일 필요는 없다 — 문자열 리터럴 안의 괄호 때문).
- [MUST] 잔여 리스크 기록: Windows **런타임** 검증은 이 머신에서 불가하다. `scripts/install/windows.ps1:10` 이 이미 "실제 Windows 환경 검증은 TS-006(Windows VM) 에서 1회 수행 예정"을 명시하므로, 본 태스크의 Windows 런타임 검증도 동일 경로로 이월하고 DONE 보고에 미검증 항목으로 남긴다.

### (b) 3.9 게이트 거부 검증 (비파괴)

이 머신에는 실제 3.9.6 인터프리터가 `/usr/bin/python3` 로 존재한다(실측). **모의가 아니라 실물로** 검증한다.

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework
SP=<scratchpad>/087-verify && mkdir -p "$SP"

# 1) 센티널 블록만 추출해 순수 함수 하네스를 구성 (install-mac.sh 자체는 실행하지 않는다)
{
  echo 'set -uo pipefail'
  sed -n '/^# BEGIN opal-python-contract$/,/^# END opal-python-contract$/p'   scripts/install-mac.sh
  sed -n '/^# BEGIN opal-python-gate$/,/^# END opal-python-gate$/p'           scripts/install-mac.sh
} > "$SP/harness.sh"
grep -c '^# BEGIN' "$SP/harness.sh"     # 기대: 2

# 2) 하네스 로드
source "$SP/harness.sh"

# 3) 판정 검증
python_candidates                                    # 기대: python3.14/3.13/3.12/3.11/python3 (5행, 이 순서)
python_meets_min /usr/bin/python3;        echo "sys3.9 rc=$?"   # 기대: rc=1  ← 게이트 거부 증명
python_meets_min "$(command -v python3)"; echo "brew  rc=$?"    # 기대: rc=0
find_python;                              echo "find  rc=$?"    # 기대: 3.11+ 절대경로 + rc=0

# 4) 3.9 venv 픽스처 — 실제 3.9.6으로 진짜 venv를 만들어 R-4를 증명 (스크래치패드에만 생성)
/usr/bin/python3 -m venv "$SP/venv39"
grep '^version' "$SP/venv39/pyvenv.cfg"              # 기대: version = 3.9.6
venv_meets_min "$SP/venv39";        echo "venv39 rc=$?"   # 기대: rc=1  ← 재생성 대상 판정
venv_meets_min "$HOME/.opal/.venv"; echo "real   rc=$?"   # 기대: rc=0  ← 읽기 전용, 무변경

# 5) 실 venv 무변경 확인
ls -la "$HOME/.opal/.venv/pyvenv.cfg"                # mtime 이 (4) 실행 전과 동일해야 한다
```

| 검증 항목 | 명령 | 기대 |
|----------|------|------|
| 3.9 인터프리터 거부 | `python_meets_min /usr/bin/python3` | rc 1 |
| 3.14 인터프리터 채택 | `python_meets_min $(command -v python3)` | rc 0 |
| 후보 순서 | `python_candidates` | 5행, 내림차순 + `python3` |
| 3.9 venv 재생성 판정 | `venv_meets_min $SP/venv39` | rc 1 |
| 실 venv 통과·무변경 | `venv_meets_min ~/.opal/.venv` | rc 0, mtime 불변 |

> `venv_meets_min` 이 §2.3에서 "쓰기 금지 순수 함수"로 규정된 것이 이 비파괴 검증의 성립 근거다.

### (c) 옵트아웃 경로 검증

```bash
source "$SP/harness.sh"

python_autoinstall_enabled;                        echo "default rc=$?"   # 기대: rc=0 (활성)
OPAL_AUTO_INSTALL_PYTHON=0 python_autoinstall_enabled; echo "optout rc=$?" # 기대: rc=1 (비활성)

# 실제로 설치 명령이 호출되지 않음을 스텁으로 증명한다
brew() { echo "!!! BREW-CALLED !!!"; return 0; }
export -f brew 2>/dev/null || true
OPAL_AUTO_INSTALL_PYTHON=0 install_platform_python; echo "rc=$?"
#   기대: 출력에 "!!! BREW-CALLED !!!" 가 없고, 옵트아웃 안내 문구 + rc=1
unset -f brew
```

- 이 검증이 성립하려면 `install_platform_python` 의 **첫 분기가 옵트아웃 검사**여야 한다 — §2.3 `[MUST]` 로 강제했고, `windows.ps1:613` 과 동일 배치다.
- 스텁 함수 `brew` 는 `command -v brew` 에도 잡히므로, 옵트아웃이 뚫릴 경우 반드시 `BREW-CALLED` 가 출력된다. 즉 **거짓 통과가 불가능한 형태**다.

### (d) doctor 하한 판정 검증

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework
{
  echo 'PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0'
  cat opal/tools/doctor/lib/checks.sh
} > "$SP/checks-harness.sh"
source "$SP/checks-harness.sh"

_version_ge "3.9.6"  "3.11"; echo "3.9.6  rc=$?"   # 기대: rc=1
_version_ge "3.11.0" "3.11"; echo "3.11.0 rc=$?"   # 기대: rc=0
_version_ge "3.14.3" "3.11"; echo "3.14.3 rc=$?"   # 기대: rc=0
_version_ge "3.10.9" "3.11"; echo "3.10.9 rc=$?"   # 기대: rc=1  ← 경계 바로 아래

# 3.9만 보이는 PATH를 구성해 check_deps 의 python 블록이 _fail 로 가는지 확인
mkdir -p "$SP/fakebin" && ln -sf /usr/bin/python3 "$SP/fakebin/python3"
( PATH="$SP/fakebin:/usr/bin:/bin"; source "$SP/checks-harness.sh"; check_deps ) | grep -i python
#   기대: ✗ 기호 + "3.11" 문자열 포함 (R-7 AC)
```

> 서브셸(`( ... )`) 안에서 PATH를 좁히므로 현재 셸 환경이 오염되지 않는다.

### (e) 실환경 스모크 (선택 — 멱등성/무해성 확인)

```bash
OPAL_VERBOSE=1 bash scripts/install-mac.sh    # 메뉴에서 [4] Python 패키지 선택
```

| 확인 항목 | 기대 |
|----------|------|
| 게이트 판정 | 3.14.3 채택, 자동 설치 미트리거 |
| venv 재생성 | **발생하지 않음** ("venv 기존 사용" 경로) |
| brew 호출 | 없음 |
| 종료 상태 | 0 |

> **주의**: 이 절차는 실 `~/.opal/.venv` 에 `pip install` 을 재실행한다(요구사항이 이미 충족되어 있으므로 실질 무변경, 멱등). venv 삭제·재생성은 발생하지 않아야 하며, 만약 발생하면 `venv_meets_min` 구현 결함이므로 **즉시 중단하고 Step 5로 되돌린다**. 실행 여부는 PM이 판단한다.

---

## 6. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | **brew 미보유 macOS** — `command -v brew` 실패 시 자동 설치 불가 | 클린 맥에서 설치가 중단됨. 현행은 통과 후 pip 단계에서 난해한 오류로 실패 | 중단 자체는 F-6에 따른 의도된 동작. 안내에 **2경로**를 제시한다 — Homebrew 설치 URL + `$OPAL_PYTHON_DOWNLOAD_URL` 직접 다운로드. `windows.ps1:618-622`(winget 미보유 폴백)와 동일 구조로 맞춘다. 실패 문구에 현재 감지된 버전을 포함해 원인을 즉시 알린다 |
| R-2 | **`/usr/bin/python3` 하드코딩 6개소와 신규 게이트의 공존** (`:155`,`:188`,`:374`,`:416`,`:1232`,`:1613`) | 변경 시 install 전 구간 회귀 위험 | **존치 결정.** 근거 3가지 — (1) 6개소 전부 stdlib-only JSON/정규식 처리이며 3.9.6에서 정상 동작한다 (2) venv 생성 **이전**에 실행되어야 하므로 시스템 인터프리터 고정이 의도된 설계다 (3) 신규 게이트가 결정하는 `OPAL_PYTHON_BIN` 은 **venv 생성 전용**이라 목적이 다르다. 두 인터프리터가 공존하는 것이 정상이며, 이를 통합하면 blast radius만 확대된다 (→ D-16 §4 Surgical). 별건 관찰: `:925` 만 `/usr/bin/python3` 가 아닌 PATH `python3` 를 써 패턴이 어긋나나 동작에 영향 없으므로 **본 태스크 범위 외**(별도 태스크 후보로 기록) |
| R-3 | **`rm -rf "$venv_dir"` 오작동** — 변수 미설정 시 파국적 삭제 | 사용자 홈 손상 가능 | `$venv_dir` 은 `install_opal_venv` 지역 변수로 `:1312` 에서 `$USER_HOME/.opal/.venv` 리터럴 파생이며 외부 입력이 아니다. 추가로 `[[ -d "$venv_dir" ]]` 선행 검사 + `venv_meets_min` 실패 분기 안에서만 실행되도록 이중 가드. `set -u`(`:46`)가 미설정 변수 참조를 차단한다 |
| R-4 | **기존 3.14 venv 소유자 머신에서 재설치 시 무해성(멱등성)** | 오탐으로 정상 venv가 삭제되면 소유자 환경 파괴 | 실측 기준선 확보: `~/.opal/.venv/pyvenv.cfg` 에 `version = 3.14.3` 존재. `venv_meets_min` 은 이 값으로 rc 0을 반환하므로 재생성 분기에 진입하지 않는다. §5-(b) 5)에서 mtime 불변을, §5-(e)에서 "venv 기존 사용" 경로 진입을 각각 증명한다. **파싱 실패를 미달로 취급하는 설계**가 위험 방향이므로, `pyvenv.cfg` 부재/키 부재 시에도 실제 3.9 venv만 걸리도록 §5-(b) 4)에서 진짜 3.9 venv로 대조한다 |
| R-5 | **Windows `Find-Python` 변경이 기존 정상 환경에 주는 영향** | 3.11+ 사용자에게 불필요한 winget 설치 트리거 | 3중 완화 — (1) 후보 목록에 versioned 이름을 **덧붙이기만** 하고 기존 `python3/python/py` 순서는 유지하므로, Windows가 `python3.14.exe` 를 표준 배포하지 않는 사실상 대부분의 환경에서 **탐색 결과가 불변**이다 (2) `Find-Python` 이 **모든 후보를 끝까지 순회**한 뒤에만 `$null` 을 반환하도록 `[MUST]` 강제 — `py` 런처가 구버전을 가리켜도 다른 후보에 3.11+가 있으면 채택된다 (3) 옵트아웃 `OPAL_AUTO_INSTALL_PYTHON=0` 이 이미 존재하고 안내 문구에 노출됨(`windows.ps1:362`). 잔여 리스크는 §5-(a) 경로 2의 미검증 항목으로 이월 |
| R-6 | **Windows는 fail-fast 미적용 — 플랫폼 간 동작 비대칭** | 3.9 Windows에서 winget 실패 시 venv 없이 설치가 계속되어 조용히 열화 | **의도된 범위 제한.** R-5 AC는 자동 설치 분기까지만 요구하며, Windows에 fail-fast를 신규 도입하는 것은 TASK 범위 초과이자 기존 정상 환경 회귀 위험이다. 완화로 `Install-OpalVenv`(`:904-909`) 스킵 안내에 하한 문구를 넣어 **진단 가능**하게만 만든다. 완전 대칭화는 Windows 실환경 검증(TS-006 경로)과 묶어 후속 태스크로 남긴다 |
| R-7 | **하한 상수 3중 정의 드리프트** — install-mac.sh / windows.ps1 / checks.sh | 한 곳만 갱신되면 게이트와 진단이 어긋남 | 물리적 SSOT 통합은 불가하다(3개 언어 + doctor는 `~/.opal/` 배포본에서 실행되어 `scripts/` 에 접근 못 함). 대신 (1) 세 파일 **변수명을 `OPAL_PYTHON_MIN`/`OPAL_PYTHON_TARGET` 로 통일**(PowerShell만 언어 관례상 `$OpalPythonMin`) (2) 각 정의부에 상호 참조 주석 1줄 (3) QA §일관성 테스트에 "3개 파일 하한 값 동일" 항목 상설화 |
| R-8 | **fail-fast `exit 1` 이 대화형 메뉴 루프를 종료시킴** (`:1856-1901`) | 메뉴 [4]만 쓰려던 사용자에게 갑작스러운 종료로 보임 | F-6이 요구하는 동작이므로 유지하되, 종료 직전 **원인 1줄 + 해결 명령 1줄 + 옵트아웃 안내 1줄**을 출력해 사용자가 다음 행동을 알 수 있게 한다 |
| R-9 | **Linux 기존 3.9/3.10 사용자의 신규 차단** | 지금까지 "통과"하던 설치가 이제 중단됨 | 실질 회귀가 아니다 — `opal/tools/requirements.txt:23` `mcp>=1.1.0` 이 Python 3.10+ 를 요구하므로 해당 환경은 어차피 pip 단계에서 실패했다. 변경의 순효과는 **실패 시점을 앞당기고 원인을 명시**하는 것이다. 이 사실을 DONE 보고에 명기한다 |
| R-10 | **작업트리에 086 미커밋 변경 존재** (`docs/architecture-diagram/`, `.opal/brain/`) | EXECUTE 중 오염 시 두 태스크의 diff가 섞임 | 전 Step의 대상 파일을 M-1~M-6 6개로 고정. Step 9 완료 후 `git status --short` 로 6개 파일 + 086 기존 미커밋분만 존재함을 확인한다. 커밋·스테이징은 수행하지 않는다 ([MUST] Guards) |
| R-T1 | **용어 일관성** — 동일 개념의 상수명이 bash `OPAL_PYTHON_MIN` ↔ PowerShell `$OpalPythonMin` ↔ doctor `OPAL_PYTHON_MIN` | 표기 차이가 드리프트로 오인될 수 있음 | 각 언어의 네이밍 관례를 따른 것이며 **값·의미가 동일**하므로 `terminology_mismatch` 가 아니다 (citation-rules §7.1 판정). doctor를 install-mac.sh와 동일 표기로 맞춰 bash 계열 2개 파일은 완전 일치시킨다. `decision_required` 에스컬레이션 불요 |

---

## 7. 리스크 가설 표 (H-N)

> 변경 단위별로 "깨질 수 있는 계약"을 가설화한다. 본 태스크에 TEST 단계는 없으므로, 각 가설의 검증은 §5 절차 또는 QA 항목에 직접 매핑한다.

| # | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 경로 |
|---|----------|-----------------|----------|----------|
| H-1 | `install_opal_venv` fail-fast | `install_opal()`(`:1223`)이 venv 이후 단계(참조 레지스트리·부트스트래퍼·어댑터·대시보드, `:1225-1302`)를 실행하지 못하고 종료 | Python 미달 사용자는 **OPAL 자산 배포 자체를 못 받음** — 현행보다 강한 차단 | §5-(e) + R-8 대응. 게이트를 `install_opal_venv` 진입부에 둔 이상 이 파급은 불가피하며 F-6의 명시적 선택이다 |
| H-2 | `find_python` 후보 확장 | `python3.14` 가 PATH에 있으나 **PATH `python3` 와 다른 인터프리터**인 경우 venv가 예상과 다른 인터프리터로 생성됨 | 소유자 머신은 둘 다 3.14.3(실측)이라 무영향. 다른 환경에서는 더 높은 버전이 선택되는 방향이라 안전 | §5-(b) `find_python` 출력 경로 육안 확인 |
| H-3 | `venv_meets_min` pyvenv.cfg 파싱 | `pyvenv.cfg` 에 `version` 키가 없는 비표준 venv를 미달로 오판 → 정상 venv 삭제 | 파국적(사용자 환경 파괴) | §5-(b) 4)에서 실 venv rc 0 + mtime 불변 확인. 오판 시 §5-(e) 중단 규약 발동 |
| H-4 | `Find-Python` 하한 조건 강화 | `py` 런처가 구버전을 가리키는 환경에서 자동 설치가 신규 트리거 | 사용자 동의 없는 환경 변경 | R-5 대응(전수 순회 + 옵트아웃). Windows 런타임 검증은 이월 |
| H-5 | doctor `_resolve_python3` 후보 확장 | 반환 계약(`"<cmd>\|<ver>"` / rc)이 바뀌면 유일 호출처 `:104` 가 깨짐 | doctor 전체 abort (`set -e` 환경) | Step 3 완료 기준 (4) + §5-(d) |
| H-6 | 상수 파생 후보 목록 | `OPAL_PYTHON_MIN` 과 `OPAL_PYTHON_TARGET` 의 major가 다르면 파생 루프가 잘못된 목록 생성 | 후보 탐색 전면 실패 | 두 상수 모두 major 3 고정. §5-(b) `python_candidates` 5행 출력 확인 |
| H-7 | requirements.txt 주석 정정 | 주석만 변경했는데 패키지 행이 함께 바뀌면 의존성 해석이 달라짐 | 설치 실패 | Step 4 완료 기준 (3) — 패키지 행 diff 0건 |
| H-8 | 변경이력 일괄 갱신 | 셸 스크립트 헤더 주석 편집 중 `set -euo pipefail`(`:46`) 위쪽 구조 훼손 | 스크립트 전체 파싱 실패 | Step 7 완료 기준 (5) — 문법 검사 재실행 |

---

## 8. 변경이력 갱신 계획 (R-9)

> [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."

| 파일 | 삽입 위치 | 기존 최신 | 신규 버전 | 행 문구(요지) |
|------|----------|----------|----------|--------------|
| `scripts/install-mac.sh` | 헤더 주석 블록 **`:43` 바로 아래**(`:44` `#` 앞) — v4.3 행 다음 | `v4.3 2026-08-04 15:24 KST` (`:43`) | **v4.4** | Python 버전 계약 상수 + 게이트 함수군 8종 신설(`python_candidates`/`python_meets_min`/`find_python`/`venv_meets_min`/`python_autoinstall_enabled`/`install_platform_python`/`ensure_python`) + `install_opal_venv` fail-fast·기존 venv 하한 재검증 재생성 — macOS brew 자동설치·Linux 안내 어댑터 분기, 구버전 Python으로 venv가 조용히 생성·재사용되던 결함 fix (087) |
| `scripts/install/windows.ps1` | `.NOTES` 변경이력 **`:97` 바로 아래**(`:98` `#>` 앞) — v1.18.0 행 다음 | `v1.18.0 2026-07-17` (`:97`) | **v1.19.0** | `Test-PythonMinVersion` 신설 + `Find-Python` 하한 판정 추가(미달 인터프리터 비채택 → 자동 설치 트리거를 "미설치 또는 하한 미달"로 확대) + `Install-WindowsPython` 의 3.14 리터럴을 `$OpalPythonTarget` 상수 파생으로 전환, install-mac.sh v4.4 대칭 (087) |
| `scripts/install/linux.sh` | 헤더 주석 **`:20` 바로 아래**(`:21` `#` 앞) — v1.1 행 다음 | `v1.1 2026-05-24` (`:20`) | **v1.2** | Python 하한 게이트 소재 명시 주석 추가 — 게이트는 위임 대상 `install-mac.sh` 의 `ensure_python()` 에 있으며 Linux는 자동 설치 없이 안내만 수행(동작 무변경, 주석 전용) (087) |
| `opal/tools/doctor/lib/checks.sh` | 헤더 주석 **`:20` 바로 아래**(`:21` `#` 앞) — v1.3 행 다음 | `v1.3 2026-05-10 14:50 KST` (`:20`) | **v1.4** | `_version_ge` 신설 + `_resolve_python3` 후보에 versioned 이름 추가·하한 우선 채택 + `check_deps` python 항목이 하한 미달 시 `_fail` 로 표시(요구 하한 메시지 포함) — 3.9 환경이 "정상" 통과하던 진단 갭 fix (087) |
| `docs/ARCHITECTURE.md` | 문서 하단 `## 변경이력` 표 말미 | (기존 최신 행) | — | §Python 의존성에 요구 버전(3.11+, 권장 3.14) 및 미달 시 설치 중단 동작 명시 (087) |

- `opal/tools/requirements.txt` 는 변경이력 블록이 없는 의존성 목록 파일이므로 행 추가 대상이 아니다 (TASK R-9의 대상 목록과 정합).
- 일시는 EXECUTE 실제 수행 시각(KST)을 기입한다. PLAN 작성일(2026-08-10) 기준.
- [MUST] 기존 변경이력 행은 **한 글자도 수정하지 않는다** (Step 7 완료 기준 (4)).

---

## 9. TASK 요구사항 커버리지 매핑

| 요구사항 | Step | 검증 |
|---------|------|------|
| R-1 공통 Python 버전 계약 | Step 1, 2 | Step 1 완료기준 (2)(3) / Step 2 완료기준 (1) / QA §일관성 |
| R-2 macOS 탐색 + 하한 판정 | Step 1 | §5-(b) `find_python`·`python_meets_min` |
| R-3 자동 설치 + 폴백 + fail-fast | Step 1, 5 | §5-(c) 옵트아웃 / Step 5 완료기준 (3) / R-1 대응 |
| R-4 기존 venv 재검증·재생성 | Step 5 | §5-(b) 4) 3.9 venv 픽스처 |
| R-5 Windows 하한 판정 | Step 2 | Step 2 완료기준 (3) / §5-(a) 경로 1·2 |
| R-6 Linux 하한 판정 + 안내 | Step 1(Linux 분기), Step 6 | Step 1 완료기준 (5) / Step 6 완료기준 (3) / **DD-1 이탈 확인 필요** |
| R-7 doctor 최소버전 판정 | Step 3 | §5-(d) |
| R-8 requirements 버전·경로 | Step 4 | Step 4 완료기준 (1)(2) |
| R-9 변경이력 갱신 | Step 7 | §8 + Step 7 완료기준 |
| (docs 갱신) | Step 8 | Step 8 완료기준 |

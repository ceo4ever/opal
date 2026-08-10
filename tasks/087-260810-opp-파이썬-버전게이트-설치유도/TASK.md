# TASK: 설치 스크립트 Python 최소버전 게이트 + 3.14 설치 유도 (플랫폼 대칭화)

> 작성일: 2026-08-10 | 작업 유형: 수정(결함) | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

macOS/Linux 설치 경로에 Python 최소버전 게이트와 3.14 설치 유도를 신설하고, Windows의 기존 자동 설치 규약과 대칭을 맞춘다. 동시에 3플랫폼 공통으로 "구버전 Python이 조용히 채택되는" 결함을 차단한다.

## 배경

다른 개발자의 macOS에서 OPAL 설치 중 `mcp>=1.1.0` 의존성 해석이 실패했다. 실패 로그가 `Requires-Python >=3.10` 배포판을 전부 "Ignored" 처리하고 `Could not find a version that satisfies the requirement mcp>=1.1.0 (from versions: none)`로 종료되었다 — 실행 중인 pip의 Python이 3.10 미만일 때만 발생하는 패턴이다.

macOS 기본 인터프리터(`/usr/bin/python3`)는 3.9.6이며 Apple이 갱신하지 않는다. 설치 스크립트가 Python 버전을 확인하지 않고 PATH의 `python3`를 그대로 사용하므로, Homebrew Python이 없는 클린 맥에서는 항상 3.9로 venv가 생성되어 설치가 실패한다.

## 배경 분석 (대화에서 도출)

### A. 실패 재현 조건 (실측)

| 항목 | 값 | 근거 |
|------|-----|------|
| macOS 시스템 Python | 3.9.6 | `/usr/bin/python3 -V` 실행 결과 |
| `mcp` 요구 하한 | Python 3.10 이상 | `opal/tools/requirements.txt:23`: "mcp>=1.1.0" |
| 소유자 머신 상태 | venv 3.14.3 + mcp 1.27.0 정상 | `~/.opal/.venv/pyvenv.cfg` 실측 — 결함이 드러나지 않은 이유 |

### B. macOS 경로 결함 (2건)

| # | 결함 | 위치 | 내용 |
|---|------|------|------|
| B-1 | 버전 미검증 venv 생성 | `scripts/install-mac.sh:1324` | `python3 -m venv "$venv_dir"` — PATH의 `python3`를 버전 확인 없이 사용 |
| B-2 | 구버전 venv 무검증 재사용 | `scripts/install-mac.sh:1323-1327` | `.venv` 디렉토리 존재 시 `"venv 기존 사용"`으로 통과 — 한 번 3.9로 만들어지면 재설치를 반복해도 동일 오류가 영구화 |

### C. 플랫폼 비대칭 (핵심 발견)

| 플랫폼 | 인터프리터 검출 | 자동 설치 유도 | 하한 판정 | 근거 |
|--------|---------------|--------------|----------|------|
| Windows | 있음 (`Find-Python`) | **있음** — winget으로 Python 3.14 | **없음** | `scripts/install/windows.ps1:577-598`, `:600` |
| macOS | 없음 | 없음 | 없음 | `scripts/install-mac.sh` 전수 grep 결과 Python 사전 점검 0건 |
| Linux | 없음 | 없음 | 없음 | `scripts/install/linux.sh` — Python 관련 코드 0줄 |

- Windows는 이미 `winget install --id Python.Python.3.14 --silent --scope user`로 자동 설치하며, 옵트아웃 환경변수 `OPAL_AUTO_INSTALL_PYTHON=0`과 winget 미보유 시 python.org 안내 폴백까지 갖췄다 (`scripts/install/windows.ps1:600` 이하).
- 즉 소유자가 기대한 "3.14 설치 유도"는 **Windows 기준으로는 이미 확립된 규약**이며, macOS/Linux에만 미이식된 상태다.

### D. Node.js와의 비대칭 (동일 스크립트 내부)

- `scripts/install-mac.sh:1209-1210`은 Node 미설치 시 경고와 함께 `"설치: https://nodejs.org/ 또는 brew install node"`를 안내한다.
- 같은 스크립트가 Python에 대해서는 존재 확인·버전 확인·설치 안내를 **전혀 하지 않는다**.
- 결과적으로 실패 심각도는 Python이 더 큼에도(Node 부재는 기능 제한, Python 버전 미달은 설치 중단) 안내는 Node만 존재한다.

### E. Windows 잔여 갭

- `Find-Python`은 `^Python\s+\d+\.\d+` 패턴만 검사하고 버전 하한을 보지 않는다 (`scripts/install/windows.ps1:592`).
- 따라서 자동 설치는 "Python 미설치"에서만 트리거되고, "Python 3.9가 이미 설치됨" 상태는 그대로 채택되어 macOS와 동일한 pip 실패가 발생한다.

### F. doctor 사후 검출 갭

- `opal/tools/doctor/lib/checks.sh:52`의 `_resolve_python3`는 Microsoft Store stub 회피만 수행하고 버전 하한을 판정하지 않는다.
- 3.9.6 환경도 "python3 정상"으로 통과시켜, 설치 실패 후 원인 진단에 도움을 주지 못한다.

### G. 부수 발견 (문서 불일치)

- `opal/tools/requirements.txt:2` 주석이 설치 경로를 `~/.opal/venv/bin/pip`로 안내하나, 실제 경로는 `~/.opal/.venv`다 (`scripts/install-mac.sh:1312`).

## 확정된 설계 방향 (대화에서 합의)

| # | 결정 | 근거 |
|---|------|------|
| F-1 | Windows의 기존 규약을 SSOT로 삼아 macOS/Linux에 **미러링**한다 (신규 설계 아님) | Windows에 이미 자동 설치·옵트아웃·폴백이 구현되어 있음 (배경 분석 §C) |
| F-2 | 하한은 `3.11`, 자동 설치/권장 대상은 `3.14`로 **분리**한다 | 하한을 3.14로 못 박으면 3.12·3.13 사용자를 불필요하게 차단 |
| F-3 | 옵트아웃 환경변수는 기존 `OPAL_AUTO_INSTALL_PYTHON=0`을 **그대로 재사용**한다 (신규 명칭 금지) | 플랫폼 간 사용자 인터페이스 통일 |
| F-4 | 자동 설치는 Windows(winget)·macOS(brew)에만 적용하고 **Linux는 안내만** 한다 | 배포판별 패키지 매니저 분기가 어댑터를 비대하게 만듦 |
| F-5 | 하한 판정 로직은 **플랫폼 공통**으로 유지하고, 설치 수단만 어댑터로 분기한다 | `.opal/AGENT.md` PM 검토 기준: "Claude Code/Cursor/Gemini 등 플랫폼 분기를 어댑터 계층에 격리했는가" |
| F-6 | 하한 미달 시 경고 후 진행이 아니라 **fail-fast + 설치 안내**로 처리한다 | Python 버전 미달은 설치가 실제로 중단되므로 경고 수준이 부적절 |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | macOS/Linux에 Python 하한 게이트 + 설치 유도를 신설하고, 3플랫폼 공통으로 구버전 Python 채택을 차단한다 | - | 배경 분석 §B·§C·§E |
| 범위 | 포함: `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/install/linux.sh`, `opal/tools/doctor/lib/checks.sh`, `opal/tools/requirements.txt` / 제외: Linux 자동 설치 구현, `~/.opal/` 배포본 직접 편집, 커밋·배포 실행 | - | F-4 / `.opal/AGENT.md` §금지사항 |
| 제약 | 하한 3.11 · 자동설치 대상 3.14 · 옵트아웃 `OPAL_AUTO_INSTALL_PYTHON=0` 재사용 · 판정 공통/설치수단 어댑터 분기 · 변경이력 행 추가 의무 | - | F-2·F-3·F-5 / `.opal/AGENT.md` §업무 수행 지침 |
| 완료기준 | 아래 R-1~R-9의 AC가 전부 Pass하고, 3.9 환경 모의 검증에서 설치가 안내와 함께 중단된다 | - | 요구사항 섹션 |

## 요구사항

- [ ] **R-1. 공통 Python 버전 계약 정의**
  - 무엇을: 하한(`3.11`)·자동설치 대상(`3.14`)·옵트아웃 변수명(`OPAL_AUTO_INSTALL_PYTHON=0`)을 단일 상수로 선언
  - 어디에: `scripts/install-mac.sh` 상단 상수부 + `scripts/install/windows.ps1` 상단 상수부
  - 왜: 값이 여러 곳에 흩어지면 플랫폼 간 드리프트가 발생 (F-5)
  - AC: 세 값이 각 스크립트에서 **상수로 1회씩만 정의**되고, 이후 사용처는 모두 그 상수를 참조한다 (하드코딩된 `3.11`/`3.14` 리터럴이 상수 정의부 외에 0건)

- [ ] **R-2. macOS 인터프리터 탐색 + 하한 판정 신설**
  - 무엇을: `python3.14 → python3.13 → python3.12 → python3.11 → python3` 순으로 탐색하고 하한 미달을 판정하는 함수 추가
  - 어디에: `scripts/install-mac.sh` (`install_opal_venv()` 앞)
  - 왜: PATH의 `python3`가 3.9.6으로 해석되어 설치가 실패 (배경 분석 §B-1)
  - AC: 탐색 함수가 3.11 이상 인터프리터의 절대 경로를 반환하고, 3.11 미만만 존재하면 비어 있는 값과 실패 상태를 반환한다

- [ ] **R-3. macOS 자동 설치 유도 + 폴백 안내 + fail-fast**
  - 무엇을: 하한 미달·미설치 시 `brew install python@3.14` 자동 설치를 시도하고, 실패·brew 미보유 시 python.org 안내 후 설치 중단
  - 어디에: `scripts/install-mac.sh` (R-2 함수 직후 호출부)
  - 왜: Windows에만 존재하는 자동 설치 규약을 미러링 (F-1)
  - AC: (a) `OPAL_AUTO_INSTALL_PYTHON=0`이면 자동 설치를 건너뛴다 (b) brew 미보유 시 python.org URL이 출력된다 (c) 최종적으로 3.11+ 확보 실패 시 **exit 0이 아닌 상태로 중단**되며 원인 문구가 출력된다

- [ ] **R-4. 기존 venv 버전 재검증 + 재생성**
  - 무엇을: `.venv` 존재 시 `pyvenv.cfg`의 `version`을 읽어 하한 미달이면 폐기 후 재생성
  - 어디에: `scripts/install-mac.sh:1323-1327` 재사용 분기
  - 왜: 구버전 venv가 재설치를 반복해도 살아남아 오류가 영구화 (배경 분석 §B-2)
  - AC: 3.9로 만든 `.venv`가 존재하는 상태에서 설치를 실행하면 해당 venv가 **재생성되고**, 재생성 사실이 로그에 출력된다

- [ ] **R-5. Windows 하한 판정 추가 (구버전도 자동설치 트리거)**
  - 무엇을: `Find-Python`의 채택 조건에 하한 판정을 추가하고, 자동 설치 트리거 조건을 `미설치` → `미설치 또는 하한 미달`로 확대
  - 어디에: `scripts/install/windows.ps1:587-598` (`Find-Python`) + `:351-362` 호출부
  - 왜: 현재 패턴 매칭이 버전 하한을 보지 않아 3.9가 그대로 채택됨 (배경 분석 §E)
  - AC: Python 3.9만 설치된 상태를 가정한 판정에서 `Find-Python`이 해당 인터프리터를 **채택하지 않고**, 자동 설치 경로로 분기한다

- [ ] **R-6. Linux 하한 판정 + 설치 안내 (자동 설치 제외)**
  - 무엇을: 인터프리터 탐색·하한 판정 후, 미달 시 배포판 중립 설치 안내와 함께 중단
  - 어디에: `scripts/install/linux.sh`
  - 왜: Linux는 패키지 매니저 분기 비용이 커 자동 설치를 제외 (F-4)
  - AC: 하한 미달 시 안내 문구가 출력되고 설치가 중단되며, **자동 설치를 시도하는 코드가 없다**

- [ ] **R-7. doctor 최소버전 판정 추가**
  - 무엇을: `_resolve_python3` 결과에 하한 판정을 추가하여 미달 시 실패 항목으로 표시
  - 어디에: `opal/tools/doctor/lib/checks.sh:52` / `:102-109`
  - 왜: 3.9 환경이 "정상"으로 통과되어 사후 진단이 불가 (배경 분석 §F)
  - AC: Python 3.9 환경에서 `doctor` 실행 시 python 항목이 **실패로 표시**되고 요구 하한이 메시지에 포함된다

- [ ] **R-8. requirements.txt 요구 버전 명시 + 경로 주석 정정**
  - 무엇을: 파일 상단에 요구 Python 버전(3.11+, 권장 3.14)을 명시하고, 설치 경로 주석을 `~/.opal/.venv`로 정정
  - 어디에: `opal/tools/requirements.txt:1-2`
  - 왜: 요구 버전이 어디에도 문서화되어 있지 않고, 경로 주석이 실제와 불일치 (배경 분석 §G)
  - AC: 상단 주석에 `3.11` 이상 요구가 기재되고, `~/.opal/venv/` 표기가 파일 내 0건이다

- [ ] **R-9. 변경이력 갱신**
  - 무엇을: 수정한 스크립트의 변경이력 표/주석 블록에 행 추가 (일시 KST + 태스크 번호 087)
  - 어디에: `scripts/install-mac.sh` 헤더 변경이력, `scripts/install/windows.ps1` `.NOTES` 변경이력
  - 왜: [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
  - AC: 변경 대상 스크립트마다 087 태스크 번호와 KST 일시를 포함한 행이 1건 이상 추가되었다

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 수정 대상은 `scripts/`, `opal/tools/` 프로젝트 소스로 한정한다.
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → 하한 판정은 공통 규칙으로 두고 설치 수단(winget/brew/안내)만 플랫폼별로 분기한다.
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다." → 본 태스크는 커밋·배포(install 실행)를 포함하지 않는다.
- 기존 옵트아웃 환경변수명 `OPAL_AUTO_INSTALL_PYTHON`을 변경하지 않는다 (Windows 사용자 호환).
- 자동 설치는 사용자 환경을 변경하는 행위이므로 옵트아웃 경로가 반드시 동작해야 한다.
- 작업트리에 선행 태스크(086)의 미커밋 변경이 존재하므로, 해당 파일들을 건드리지 않는다.

## 기술 스택

- Bash (`scripts/install-mac.sh`, `scripts/install/linux.sh`, `opal/tools/doctor/lib/checks.sh`)
- PowerShell (`scripts/install/windows.ps1`)
- Python venv / pip (`opal/tools/requirements.txt`)
- 패키지 매니저: Homebrew (macOS), winget (Windows)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install-mac.sh | `scripts/install-mac.sh` | venv 생성·재사용 결함 위치 (`:1209-1210`, `:1311-1332`) |
| D-2 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | 미러링할 자동 설치 규약 원본 (`:351-362`, `:577-598`, `:600~`) |
| D-3 | 소스 | linux.sh | `scripts/install/linux.sh` | Python 처리 부재 확인 및 안내 추가 대상 |
| D-4 | 소스 | doctor checks.sh | `opal/tools/doctor/lib/checks.sh` | 사후 진단 하한 판정 추가 대상 (`:52`, `:102-109`) |
| D-5 | 소스 | requirements.txt | `opal/tools/requirements.txt` | `mcp>=1.1.0` 하한 근거 및 주석 정정 대상 (`:2`, `:23`) |
| D-6 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 금지사항(배포 경계·플랫폼 분기·변경이력) 및 PM 검토 기준 |
| D-7 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards(커밋 규칙·구현 금지 원칙) |

# DONE: 설치 스크립트 Python 최소버전 게이트 + 3.14 설치 유도 (플랫폼 대칭화)

> 완료일: 2026-08-10 23:40 KST | 태스크: 087 | 파이프라인: opp (agentic)
> 산출물: TASK.md · PLAN.md · AGENTIC-LOG.md · GC-CONVENTION-2026-08-10T23-28.md · DONE.md

---

## 1. 무엇을 해결했나

다른 개발자의 macOS에서 OPAL 설치가 `mcp>=1.1.0` 의존성 해석 실패로 중단됐다. 설치 스크립트가 Python 버전을 확인하지 않고 PATH의 `python3`를 그대로 써서, macOS 기본 인터프리터(3.9.6)로 venv가 만들어진 것이 원인이었다.

세 가지를 고쳤다.

1. **버전 게이트 신설** — 3.11 미만이면 pip 단계까지 가지 않고, 원인 문구와 함께 설치를 중단한다.
2. **설치 유도 대칭화** — Windows에만 있던 자동 설치 규약을 macOS(Homebrew)에 이식하고 Linux는 안내만 한다.
3. **구버전 venv 영구화 차단** — 기존 venv도 매 설치마다 버전을 재검증하여 미달이면 폐기·재생성한다.

---

## 2. 근본 원인 (진단 확정)

| # | 결함 | 위치 | 성격 |
|---|------|------|------|
| B-1 | PATH `python3`를 버전 확인 없이 venv 생성에 사용 | `scripts/install-mac.sh:1324`(변경 전) | macOS 기본 3.9.6이 그대로 채택됨 |
| B-2 | `.venv` 디렉토리 존재만으로 재사용 통과 | `scripts/install-mac.sh:1326-1328`(변경 전) | 한 번 3.9로 만들어지면 재설치해도 오류가 영구화 |
| C-1 | 자동 설치 유도가 Windows에만 존재 | `scripts/install/windows.ps1:600` | macOS/Linux 미이식 (플랫폼 비대칭) |
| C-2 | Node에는 설치 안내가 있는데 Python에는 없음 | `scripts/install-mac.sh:1209-1210` 대비 | 실패 심각도는 Python이 더 큰데 안내가 없음 |
| E-1 | Windows도 "미설치"만 감지하고 "구버전"은 통과 | `scripts/install/windows.ps1:592`(변경 전) | 3.9가 이미 깔린 Windows는 동일 실패 |
| F-1 | doctor가 3.9.6을 정상 통과시킴 | `opal/tools/doctor/lib/checks.sh:52`(변경 전) | 사후 진단으로도 못 잡음 |

**핵심**: 캡틴 머신에서 증상이 안 보인 이유는 Homebrew Python 3.14가 이미 PATH에 있었기 때문이다. Homebrew Python이 없는 클린 맥은 100% 이 오류를 맞는다.

---

## 3. 설계 — 판정은 공통, 설치 수단만 어댑터

### 버전 계약 (3파일 동일 값)

| 값 | 의미 | 근거 |
|----|------|------|
| `3.11` | 하한 — 미달 시 설치 중단 | `mcp` SDK가 Python 3.10+ 요구, 1버전 여유 |
| `3.14` | 자동 설치·권장 대상 | Windows 기존 규약과 동일, 캡틴 머신 3.14.3 실동작 |
| `OPAL_AUTO_INSTALL_PYTHON=0` | 자동 설치 옵트아웃 | **기존 Windows 환경변수명 재사용** (신규 명칭 만들지 않음) |

하한과 자동설치 대상을 분리한 이유: 하한을 3.14로 못 박으면 3.12·3.13 사용자가 불필요하게 차단된다.

### 어댑터 분기

플랫폼 분기는 `install_platform_python()` **단일 함수 안에만** 존재한다. 하한 판정 로직은 플랫폼 무관 순수 함수로 유지했다.

| 플랫폼 | 설치 수단 | 폴백 |
|--------|----------|------|
| macOS | `brew install python@3.14` | brew 미보유 시 Homebrew URL + python.org 2경로 안내 |
| Windows | `winget install Python.Python.3.14` (기존) | winget 미보유 시 python.org 안내 (기존) |
| Linux | **없음** (확정 결정) | 배포판 중립 안내만 — 패키지 매니저 호출 코드 0줄 |

### 게이트 위치 — TASK 대비 이탈 1건 (DD-1, 사전 승인)

TASK.md R-6은 게이트를 `scripts/install/linux.sh`에 두라고 지정했으나, 이 파일은 `exec bash "${INSTALLER}"` 단일 위임이라 로직이 0줄이다.

결정타는 `opal/tools/opal-cli/lib/update.sh:394-397`이 `install/macos.sh` → `install-mac.sh` 순으로만 폴백하고 **linux.sh를 호출하지 않는다**는 사실이다. linux.sh에 게이트를 두면 Linux 사용자의 `opal-cli update` 경로에서 100% 우회된다.

→ 게이트를 macOS/Linux 공용 본체인 `install-mac.sh`의 `install_opal_venv()` 진입부에 두었다. 호출부가 `:1223`(전체 설치)과 메뉴 [4] 두 곳뿐이라 **대화형·비대화형·update 전 경로가 한 지점에서 덮인다.** linux.sh에는 게이트 소재를 가리키는 주석만 남겼다.

### 순수/비순수 함수 분리

신설 8함수 중 6개(`python_candidates`·`python_version_of`·`python_meets_min`·`find_python`·`venv_meets_min`·`python_autoinstall_enabled`)를 **로그·파일쓰기·전역참조 없는 순수 함수**로 강제했다. 이 순수성이 캡틴 실환경(`~/.opal/.venv`)을 건드리지 않고 게이트를 검증할 수 있게 한 구조적 근거다.

---

## 4. 변경 파일

| 파일 | 변경 | 버전 |
|------|------|------|
| `scripts/install-mac.sh` | 버전 계약 상수 3종 + 게이트 함수 8종 신설, `install_opal_venv` 배선(fail-fast·venv 재검증·인터프리터 치환) | v4.4 |
| `scripts/install/windows.ps1` | 상수 2종 + `Test-PythonMinVersion` 신설, `Find-Python` 하한 판정, 3.14 리터럴 상수화 | v1.19.0 |
| `scripts/install/linux.sh` | 게이트 소재 주석 (실행 코드 무변경) | v1.2 |
| `opal/tools/doctor/lib/checks.sh` | 상수 + `_version_ge` 신설, `_resolve_python3` 후보 확장, `check_deps` 하한 실패 판정 | v1.4 |
| `opal/tools/requirements.txt` | 요구 버전 명시 + `~/.opal/venv/` → `~/.opal/.venv/` 오타 2개소 정정 | — |
| `docs/ARCHITECTURE.md` | Python 의존성 절에 요구 버전·중단 동작 명시 (Node 절과의 서술 비대칭 해소) | — |

합계 6개 파일 / +329 -26.

---

## 5. 검증 결과

### 게이트 판정 (PM 직접 실행 — 구현 워커와 분리)

이 머신에 실제 3.9.6 인터프리터(`/usr/bin/python3`)가 존재하므로, **모의가 아니라 실물로** 검증했다.

| 항목 | 명령 | 결과 |
|------|------|------|
| 3.9.6 거부 | `python_meets_min /usr/bin/python3` | rc 1 ✅ |
| 3.14 채택 | `find_python` | `/opt/homebrew/bin/python3.14` rc 0 ✅ |
| 후보 순서 | `python_candidates` | `python3.14→3.13→3.12→3.11→python3` 5행 ✅ |
| 3.9 venv 재생성 판정 | `venv_meets_min <실제 3.9 venv>` | rc 1 ✅ |
| 실 venv 유지 | `venv_meets_min ~/.opal/.venv` | rc 0 ✅ |

3.9 venv 픽스처는 `/usr/bin/python3 -m venv`로 **스크래치패드에 실제 생성**했다(`version = 3.9.6` 확인).

### 비파괴 보장 (캡틴 실환경)

| 항목 | 결과 |
|------|------|
| 재생성 분기 진입 여부 | **미진입** — `[[ -d ]] && ! venv_meets_min` 조건 평가 결과 |
| `~/.opal/.venv/pyvenv.cfg` mtime | `1775181326` → `1775181326` (**불변**) |

### 옵트아웃 (거짓 통과 불가 형태)

`brew` 스텁 함수를 심고 `OPAL_AUTO_INSTALL_PYTHON=0`으로 실행 → `!!! BREW-CALLED !!!` **미출력**, `[INFO] 자동 설치 옵트아웃 — 스킵` + rc 1. 옵트아웃이 뚫리면 반드시 스텁이 호출되므로 통과가 위조될 수 없다.

### doctor

| 입력 | 기대 | 결과 |
|------|------|------|
| `_version_ge 3.9.6 3.11` | rc 1 | ✅ |
| `_version_ge 3.10.9 3.11` | rc 1 | ✅ (경계 바로 아래) |
| `_version_ge 3.11.0 3.11` | rc 0 | ✅ |
| `_version_ge 3.14.3 3.11` | rc 0 | ✅ |

3.9만 노출한 PATH에서 `check_deps` 실행 → `✗ python3 3.9.6 — Python 3.11+ 필요 (권장 3.14)` 출력 확인.

### 정적 검사 · 품질 게이트

| 항목 | 결과 |
|------|------|
| `bash -n` (install-mac.sh / linux.sh / checks.sh) | 3건 PASS |
| PowerShell 괄호 균형 델타 | `[0, 4, 0]` — 변경 전과 동일 |
| R-1 리터럴 격리 | `install-mac.sh`의 `3.11`/`3.14` 출현 = 상수 정의 2줄뿐 |
| 옵트아웃 변수 단일성 | `OPAL_AUTO_INSTALL_PYTHON` = 1회 |
| 컨벤션 자동 진단 | **Critical 0 / High 0** (Low 1 / Info 1) |
| 변경 범위 | 6개 파일로 격리 (`git status` 확인) |

---

## 6. 미해결로 남기는 것

| # | 항목 | 사유 | 이관처 |
|---|------|------|--------|
| 1 | **Windows 런타임 검증** | 이 머신에 `pwsh` 부재 — 정적 검증(괄호 균형)만 수행 | `windows.ps1:10`의 기존 TS-006(Windows VM) 경로 |
| 2 | **실환경 설치 스모크** | `install-mac.sh` 실제 실행은 실 venv에 pip 재설치를 유발하여 미수행 | 재생성 분기 조건을 실 venv로 평가해 "미진입"을 증명하는 방식으로 대체 |
| 3 | **Windows fail-fast 미적용** | 의도된 범위 제한 — Windows에 강제 중단을 신규 도입하는 것은 TASK 범위 초과이자 기존 정상 환경 회귀 위험 | 완전 대칭화는 TS-006과 묶어 후속 태스크 |
| 4 | **배포 미수행** | 본 태스크는 소스 수정까지이며 `install` 실행을 포함하지 않음 | 반영하려면 재설치 필요 |

---

## 7. 수용 판정한 관측 (고치지 않은 이유)

**`/usr/bin/python3` 하드코딩 6개소 — 존치 결정**
`:155`, `:188`, `:374`, `:416`, `:1232`, `:1613`은 전부 stdlib-only JSON/정규식 처리이며 **venv 생성 이전에 실행**되어야 한다. 3.9.6에서 정상 동작하고, 신규 게이트가 결정하는 인터프리터는 **venv 생성 전용**이라 목적이 다르다. 통합하면 blast radius만 커진다.

**`scripts/install-mac.sh:925` 패턴 불일치**
setting.json scaffold 병합만 `/usr/bin/python3`가 아닌 PATH `python3`를 쓴다. 동작에 영향이 없어 범위 외로 기록한다.

**컨벤션 Low 1건**
`linux.sh` 변경이력 행에 `HH:mm`이 없다. 해당 파일 기존 행(v1.0/v1.1) 관례를 따른 것이며, `CONVENTIONS.md`의 변경이력 규칙이 스킬·에이전트·참조문서로 범위를 한정하고 있어 위반이 아니라 범위 질문으로 판정했다.

---

## 8. 이번 태스크에서 배운 것

### (1) 플랫폼 규약은 한쪽에만 생기고 다른 쪽에 이식되지 않는다

Windows에는 이미 winget 자동 설치·옵트아웃·폴백이 완비돼 있었는데 macOS/Linux에는 **한 줄도 없었다**. 이런 비대칭은 "새 기능을 설계"하는 문제가 아니라 **"기존 규약을 찾아 미러링"** 하는 문제다. 신규 설계로 접근했다면 옵트아웃 환경변수명이 갈라져 사용자 인터페이스가 분열됐을 것이다.

교훈: 플랫폼 하나에서 결함을 발견하면, **다른 플랫폼에 이미 해법이 있는지 먼저 확인한다.**

### (2) "위임만 하는 파일"에 게이트를 두면 우회된다

`linux.sh`는 얇은 래퍼처럼 보였지만, 진짜 문제는 얇다는 것이 아니라 **일부 진입 경로가 그 파일을 아예 거치지 않는다**는 것이었다. `opal-cli update`는 linux.sh를 호출하지 않는다.

교훈: 게이트를 배치하기 전에 **모든 진입 경로를 역추적**한다. 파일 크기가 아니라 호출 그래프가 판단 기준이다.

### (3) 존재 검사와 버전 검사는 다른 게이트다

Windows는 "Python 미설치"만 자동 설치 트리거로 삼았다. 그래서 3.9가 이미 깔린 머신은 조용히 통과했다. macOS의 `.venv` 재사용 분기도 같은 형태였다 — **디렉토리 존재 = 정상**으로 취급했다.

교훈: `-d`/`command -v` 같은 존재 검사를 정상 판정으로 쓰면, 그 자원이 **낡은 채로 영구화**된다. 존재 검사 옆에는 항상 적합성 검사가 필요하다.

### (4) 순수 함수 분리가 파괴적 검증을 비파괴 검증으로 바꾼다

`venv_meets_min`을 "로그도 안 쓰고 파일도 안 쓰는" 순수 함수로 규정한 덕분에, 캡틴의 실제 `~/.opal/.venv`(3.14.3)를 대상으로 판정만 돌려보고 mtime 불변을 증명할 수 있었다. 함수가 로그나 부수효과를 품고 있었다면 실환경 검증 자체가 불가능했다.

교훈: 위험한 동작(`rm -rf`)을 결정하는 **판정부와 실행부를 분리**하면, 판정부만 실환경에 안전하게 노출해 검증할 수 있다.

### (5) 실패를 늦추는 것보다 앞당기는 것이 낫다

기존 동작도 결국 pip 단계에서 중단됐다(`set -e`). 즉 이번 fail-fast는 "차단을 강화"한 게 아니라 **중단 시점을 앞당기고 원인을 명시**한 것이다. 사용자가 보는 것이 pip 로그 200줄에서 한 줄 안내로 바뀌었다.

교훈: 어차피 실패할 실행이라면, **가장 이른 지점에서 가장 읽기 쉬운 문구로** 실패시킨다.

---

## 9. 후속 이관 목록 (범위 외 — 별도 태스크 후보)

| # | 항목 | 근거 |
|---|------|------|
| 1 | Windows 런타임 검증 + fail-fast 완전 대칭화 | §6-1, §6-3 |
| 2 | `install-mac.sh:925` 인터프리터 패턴 정합 | §7 |
| 3 | `CONVENTIONS.md` §변경이력 적용 범위 명문화 (`scripts/`·`opal/tools/**` 스크립트 헤더 포함 여부) | 컨벤션 진단 §4 제안 |

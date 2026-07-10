# TEST-SCENARIO: opal-cli install 서브커맨드 완전 제거

> 작성일: 2026-07-10 | 입력: PLAN.md §리스크 가설 표, TASK.md 요구사항 AC
> 검증 대상: `opal/tools/opal-cli/` 소스 (비파괴 — 소스 직접 실행)
> 실행: opal-test-agent (mode=CLI/BE)

---

## 0. RED-first 적용 판단

| 항목 | 판단 | 근거 |
|------|------|------|
| RED-first 적용 | **부분 적용 (동작 시나리오 한정) — 전통적 실패-우선 테스트 코드 작성은 불요** | 본 태스크는 신규 함수/로직 추가가 없는 **순수 제거 + 안내 문구 리다이렉트**다. 검증 대상이 "부재(negative existence)"와 "문자열 정합"이라 자동화 실패-테스트를 별도 작성할 실익이 낮다. 대신 **변경 전/후 동작 대비**(before: install이 동작/에러 → after: unknown 흡수)를 관찰하는 방식으로 RED→GREEN 취지를 충족한다. |
| self-confirming 위험 | 낮음 | 검증이 소스 문자열/실행 결과의 객관 관찰(grep 카운트, 종료코드, 출력 매칭)이라 "구현이 곧 검증"이 되는 순환 없음. |

**RED 상태 사전 기록 (변경 전 baseline — EXECUTE 전 1회 캡처 권장)**:
- `bash opal/tools/opal-cli/run.sh --help | grep -c install` → **현재 > 0** (변경 후 0 기대)
- `bash opal/tools/opal-cli/run.sh install` → **현재: install 로직 진입** ("설치 스크립트를 찾을 수 없습니다" 등, exit 1) — 변경 후: "알 수 없는 서브커맨드: install" 로 성격 전환
- `grep -rn "opal-cli install" opal/tools/opal-cli/` → **현재 다수(≥8건)** (변경 후 0, 변경이력 제외)
- `test -f opal/tools/opal-cli/lib/install.sh` → **현재 존재** (변경 후 부재)

---

## 1. 검증 전략 — 소스 직접 실행 (비파괴)

> ⚠️ opal-cli는 배포본(`~/.opal/bin/opal-cli` → `~/.opal/tools/opal-cli/run.sh`)에서 실행되지만, **재배포는 CLOSE 후 캡틴 지시 영역**이다. TEST 단계는 **소스 파일을 직접 실행**하여 비파괴 검증한다.

**원리 (재배포 불필요)**: `run.sh`는 `BASH_SOURCE` symlink chain을 따라 `SCRIPT_DIR/lib`를 lib 경로로 잡는다(`run.sh:27~34`). 소스 경로 `opal/tools/opal-cli/run.sh`를 직접 실행하면 `LIB_DIR = opal/tools/opal-cli/lib`(소스 lib)가 되어 **소스 변경이 그대로 반영**된다. 따라서:

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework   # 프로젝트 루트 (실경로 기준)
RUN=opal/tools/opal-cli/run.sh
```
로 모든 서브커맨드를 소스 기준으로 실행 가능.

**상태 의존 분기 재현**: `run.sh`·lib 전부 `${OPAL_HOME:-$HOME/.opal}`을 사용하므로, `OPAL_HOME`을 임시 경로로 override하여 "미설치/컴포넌트 누락" 분기를 안전하게 재현한다(실제 ~/.opal 무손상).

```bash
# 미설치 재현
OPAL_HOME=$(mktemp -d)/nonexistent bash "$RUN" update
# 컴포넌트 누락 재현 (~/.opal 존재하나 doctor/uvicorn/dashboard 없음)
TMP=$(mktemp -d); OPAL_HOME="$TMP" bash "$RUN" doctor
```

**주의**: `set -euo pipefail`(run.sh:20)로 인해 파이프 검증 시 종료코드에 유의. grep 카운트는 서브셸/`|| true`로 감싸 파이프라인 조기 종료를 방지한다.

---

## 2. 시나리오 (S-N ↔ 리스크 가설 ↔ TS)

| S-ID | 대응 H | 대응 TS | 유형 | 검증 계층 |
|------|--------|---------|------|----------|
| S-1 | H-1 | TS-001 | 산출물+동작 | L1 |
| S-2 | H-2 | TS-002, TS-003 | 동작+산출물 | L1 |
| S-3 | H-1 | 회귀 | 동작 | L1 |
| S-4 | H-1 | 회귀 | 동작 | L1 |
| S-5 | H-4 | TS-004 | 동작 | L1 |
| S-6 | H-3 | TS-007 | 동작 | L1 |
| S-7 | H-5 | TS-006 | 동작+산출물 | L1 |
| S-8 | H-6 | TS-005 | 산출물 | L1 |
| S-9 | H-7 | TS-008, TS-009 | 산출물 | L1 |
| S-10 | H-7 | TS-010 | 산출물 | L1 |

---

## 3. 시나리오 상세 + 실행 명령

### S-1 — help에 install 미노출 (H-1 / TS-001)
```bash
bash "$RUN" --help | grep -c 'install' || true
```
- **기대**: `0` (install 행·예시 모두 제거)

### S-2 — `opal-cli install` unknown 흡수 + install.sh 부재 (H-2 / TS-002, TS-003)
```bash
bash "$RUN" install; echo "exit=$?"        # 기대: "알 수 없는 서브커맨드: install" + usage, exit=1
bash "$RUN" install 2>&1 | grep -c '설치 스크립트\|installer\|scripts/install' || true  # 기대: 0 (설치 시도 없음)
test -f opal/tools/opal-cli/lib/install.sh && echo FOUND || echo ABSENT   # 기대: ABSENT
grep -rn 'cmd_install\|lib/install.sh' opal/tools/opal-cli/ | grep -v '변경이력\|scripts/install' || true  # 기대: 0건
```
- **기대**: 종료코드 1, unknown 메시지, 설치 관련 출력 0, 파일 ABSENT, 잔존 참조 0.

### S-3 — 정상 서브커맨드 회귀: help/version (H-1)
```bash
bash "$RUN" --help | grep -E 'update|doctor|uninstall|mcp|console' | wc -l   # 기대: ≥5 (모두 노출)
OPAL_HOME=/nonexistent-xyz bash "$RUN" --version   # VERSION 부재 fallback 경로도 정상 (crash 없음)
```
- **기대**: 5개 서브커맨드 모두 help에 노출, --version 정상 처리.

### S-4 — 정상 서브커맨드 회귀: dispatch 파이프 무손상 (H-1)
```bash
bash "$RUN" doctor --help | grep -c 'doctor' || true      # 기대: ≥1 (doctor.sh 정상 로드)
bash "$RUN" console --help | grep -c 'console' || true    # 기대: ≥1
bash "$RUN" update --help 2>&1 | grep -c 'update\|사용법' || true  # 기대: ≥1
# unknown 대비: mcp/uninstall 도 lib 로드 성공 확인
bash "$RUN" mcp 2>&1 | head -1   # 기대: mcp.sh 정상 진입 (lib 못 찾음 오류 아님)
```
- **기대**: 각 lib이 정상 로드되어 자기 help/동작 진입 (dispatch case 파이프 보존 확인).

### S-5 — --version fallback 문구 정합 (H-4 / TS-004)
```bash
OPAL_HOME=$(mktemp -d) bash "$RUN" --version   # VERSION 없는 임시 홈
```
- **기대**: 출력에 `install` 없음. 신규 설치 원라이너(`scripts/install.sh`) 안내 포함.

### S-6 — update 미설치 리다이렉트 = 원라이너 (순환 없음) (H-3 / TS-007)
```bash
OPAL_HOME=$(mktemp -d)/gone bash "$RUN" update 2>&1 | tee /tmp/s6.log; echo "exit=$?"
grep -c 'opal-cli update' /tmp/s6.log || true        # 기대: 0 (자기 자신 재실행 안내 금지 — 순환 방지)
grep -c 'scripts/install.sh\|curl -fsSL' /tmp/s6.log || true  # 기대: ≥1 (원라이너 안내)
```
- **기대**: "OPAL이 설치되어 있지 않습니다" 후 **원라이너** 안내. `opal-cli update` 재실행 안내 없음(H-3).

### S-7 — 배포본 손상 리다이렉트 = opal-cli update (H-5 / TS-006)
```bash
TMP=$(mktemp -d)   # ~/.opal 존재하나 doctor/uvicorn/dashboard 없음
OPAL_HOME="$TMP" bash "$RUN" doctor 2>&1 | grep -c 'opal-cli update' || true   # 기대: ≥1
OPAL_HOME="$TMP" bash "$RUN" console start 2>&1 | grep -c 'opal-cli update' || true  # 기대: ≥1
OPAL_HOME="$TMP" bash "$RUN" doctor 2>&1 | grep -c 'opal-cli install' || true  # 기대: 0
bash "$RUN" console --help | grep -c 'opal-cli update' || true   # 전제 안내(console.sh:123) 기대: ≥1
```
- **기대**: doctor/console 컴포넌트 누락 시 **opal-cli update**(재배포) 안내, install 안내 0.

### S-8 — install 문자열 전수 제거 (H-6 / TS-005)
```bash
grep -rn 'opal-cli install' opal/tools/opal-cli/ | grep -vi '변경이력\|changelog\|v1\.\|(055)\|(139)' || true
```
- **기대**: 0건 (변경이력/역사 기록 행 제외).

### S-9 — 문서 정합: README·ARCHITECTURE (H-7 / TS-008, TS-009)
```bash
# README: install 미노출 (변경이력 표 행 제외)
grep -n 'install' opal/tools/opal-cli/README.md | grep -vi '변경이력\|install-mac\|(055)\|(139)' || true   # 기대: 0건
# ARCHITECTURE 라인 309 서브커맨드 목록에 install 없음
grep -n 'opal-cli` CLI' docs/ARCHITECTURE.md   # 해당 행 확인
sed -n '309p' docs/ARCHITECTURE.md | grep -c '`install`' || true   # 기대: 0
```
- **기대**: README install 미노출(원라이너·install-mac 서술은 무관/허용), ARCHITECTURE 목록에서 install 제거.

### S-10 — 변경이력 행 존재 (H-7 / TS-010)
```bash
grep -c '(055)' opal/tools/opal-cli/run.sh || true            # 기대: ≥1 (헤더 변경이력)
grep -c '(055)' opal/tools/opal-cli/README.md || true         # 기대: ≥1
grep -c 'Task 055\|(055)' docs/ARCHITECTURE.md || true        # 기대: ≥1
```
- **기대**: run.sh 헤더·README 표·ARCHITECTURE 표에 055 변경이력 행 존재.

---

## 4. 회귀 스위트 (전 서브커맨드 무손상)

```bash
bash "$RUN"            2>&1 | grep -c '서브커맨드를 입력' || true   # 인자 없음 → 안내 + usage
bash "$RUN" bogus-xyz  2>&1 | grep -c '알 수 없는 서브커맨드' || true  # unknown 표준 처리 정상
bash "$RUN" --help     | grep -cE 'update|doctor|uninstall|mcp|console' || true  # ≥5
```
- **기대**: install 제거가 unknown 처리·인자 없음 처리·타 서브커맨드 노출에 회귀를 유발하지 않음.

---

## 5. 판정 기준

| 결과 | 조건 |
|------|------|
| **PASS** | S-1~S-10 전부 기대값 일치 + §4 회귀 스위트 통과 |
| **FAIL** | 하나라도 불일치 — 특히 S-2(install 흡수)·S-3/S-4(회귀)·S-6(순환)·S-8(grep 0)은 P0/P1 게이트 |

> **재배포 검증(참고, TEST 범위 외)**: CLOSE 후 캡틴이 `./scripts/install-mac.sh` 재배포 → `opal-cli install`(배포본) unknown 처리·`opal-cli update`/`doctor`/`console` 정상 재확인. TEST 단계는 소스 직접 실행으로 완결한다.

---

## 6. 실행 결과 (opal-test-agent, 소스 직접 실행 — 비파괴)

> 실행: 2026-07-10 | mode=CLI/BE(cwd=프로젝트 루트) | `RUN=opal/tools/opal-cli/run.sh`, `OPAL_HOME` override로 상태 분기 재현.

### ⚠️ 시나리오 결함 발견 — bare `grep 'install'` 오탐 (uninstall/install-all/install.sh 서브스트링 포함)
S-1, S-2(4번 체크), S-5, S-8, S-9 의 원 시나리오 명령이 단어경계 없는 bare 패턴을 사용해 `uninstall`·`mcp install-all`(기존 기능)·`scripts/install.sh`(부트스트랩 원라이너, 별개 스크립트)·changelog 문구까지 오탐한다. **정상 서브커맨드 보존(uninstall) 및 무관 기존 기능(install-all)이 걸리는 것은 결함이 아니다.** 아래 표는 원 명령 결과와 함께, 단어경계·제외패턴으로 보정한 실질 판정을 병기한다.

### S-1 — help에 install 미노출 (H-1 / TS-001)
- 원 명령(`grep -c 'install'`) = **2** (uninstall 2건에 의한 오탐, install 서브커맨드 아님)
- 보정(`grep -cwE 'install'`) = **0** ✅ / uninstall 보존(`grep -cE 'uninstall'`) = **2** ✅
- **결과: PASS**

### S-2 — `opal-cli install` unknown 흡수 + install.sh 부재 (H-2 / TS-002, TS-003)
- `bash "$RUN" install` → `[ERROR] 알 수 없는 서브커맨드: install` + usage 전문 출력, **exit=1** ✅
- 설치 관련 출력(`설치 스크립트|installer|scripts/install`) 카운트 = **0** ✅ (설치 시도 없음)
- `test -f lib/install.sh` → **ABSENT** ✅
- `grep -rn 'cmd_install\|lib/install.sh'` 원 명령(제외: 변경이력/scripts/install) = **2건** — 단, 둘 다 run.sh:18·README.md:159의 "(055) lib/install.sh 삭제" **changelog 서술**이며 실질 코드 잔존 아님. changelog 제외 패턴(`(055)|삭제`) 추가 보정 시 = **0건** ✅
- **결과: PASS** (원 명령의 2건은 changelog 문구 오탐 — 결함 아님)

### S-3 — 정상 서브커맨드 회귀: help/version (H-1)
- `--help | grep -E 'update|doctor|uninstall|mcp|console' | wc -l` = **14** (≥5) ✅
- `OPAL_HOME=/nonexistent-xyz bash "$RUN" --version` → `opal-cli (미설치 — 원라이너로 설치: curl -fsSL .../scripts/install.sh | bash)`, **exit=0**, crash 없음 ✅
- **결과: PASS**

### S-4 — 정상 서브커맨드 회귀: dispatch 파이프 무손상 (H-1)
- `doctor --help` grep 'doctor' = **2** (≥1) ✅ / `console --help` grep 'console' = **5** (≥1) ✅ / `update --help` grep 'update\|사용법' = **4** (≥1) ✅
- `mcp` (인자 없음) 첫 줄 = `사용법: opal-cli mcp <subcommand> [options]` — lib 정상 로드(못 찾음 오류 아님) ✅
- **결과: PASS**

### S-5 — --version fallback 문구 정합 (H-4 / TS-004)
- `OPAL_HOME=$(mktemp -d) bash "$RUN" --version` → `opal-cli (미설치 — 원라이너로 설치: curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash)`, exit=0
- 원 명령 bare `grep -c 'install'` = **1** — 시나리오 자체가 자기矛盾: "install 없음"을 요구하면서 동시에 "scripts/install.sh 원라이너 안내 포함"을 요구하므로 bare count는 구조적으로 항상 ≥1이 됨(원라이너 URL 자체가 install.sh를 포함). **시나리오 결함**으로 기록.
- 실질 판정(`grep -c 'opal-cli install'` 서브커맨드 문구) = **0** ✅ / 원라이너 안내(`scripts/install.sh|curl -fsSL`) = **1**(≥1) ✅
- **결과: PASS** (실질 의도 기준)

### S-6 — update 미설치 리다이렉트 = 원라이너 (순환 없음) (H-3 / TS-007)
- `OPAL_HOME=.../gone bash "$RUN" update` → `[ERROR] OPAL이 설치되어 있지 않습니다: .../gone` + `신규 설치: curl -fsSL .../scripts/install.sh | bash` (+ PowerShell 안내), **exit=1**
- `opal-cli update` 재귀 안내 카운트 = **0** ✅ (순환 없음, H-3 충족) / 원라이너 카운트 = **1**(≥1) ✅
- **결과: PASS**

### S-7 — 배포본 손상 리다이렉트 = opal-cli update (H-5 / TS-006)
- `OPAL_HOME=$TMP bash "$RUN" doctor` → `[ERROR] doctor 도구를 찾을 수 없습니다: .../tools/doctor/run.sh` + `opal-cli update` 안내, 카운트=**1**(≥1) ✅ / install 안내 카운트=**0** ✅
- `console --help` 전제 안내(`opal-cli update`, console.sh:124) 카운트=**1**(≥1) ✅
- `OPAL_HOME=$TMP bash "$RUN" console start` — **환경 제약**: 실제 로컬에 OPAL Console 데몬이 이미 포트 127.0.0.1:7823에서 정상 서비스 중(`curl .../health` → `{"status":"ok",...}`, `lsof -i :7823` → 실행 중 프로세스 확인). `console.sh`의 `start` 액션은 `OPAL_HOME`과 무관하게 고정 포트 health-check를 최우선으로 수행(console.sh:41~44)하므로 "이미 실행 중" WARN으로 조기 반환되어, 컴포넌트 누락 분기(46~54행)에 도달하지 못함 — **코드 결함 아님(정상 중복기동 방지 설계), 사용자 실환경 데몬을 중지시키는 파괴적 조치는 TEST 비파괴 원칙상 배제**하고 소스 정적 검증으로 대체: console.sh:46~54가 doctor.sh와 동일 패턴(`error "...를 찾을 수 없습니다"` + `error "opal-cli update 로 최신 배포본을 재배포하세요."` + `exit 1`)으로 구현되어 있음을 확인 — install 안내 없음, update 안내로 일관.
- **결과: PASS** (console start 동적 실행은 환경 제약으로 정적 검증 대체, 구조적 정합성 확인)

### S-8 — install 문자열 전수 제거 (H-6 / TS-005)
- 원 명령(changelog 제외) = **0건** ✅
- 단어경계 전수 보정(`grep -rnwE 'install'`, uninstall/changelog/install-mac/scripts-install 제외) → 잔존 8건 확인, 전부 (a) `mcp install-all`(기존 무관 기능, README.md:29/61/148, mcp.sh 5건) 또는 (b) `install.sh` 부트스트랩 스크립트 참조(update.sh 3건, console.sh 1건 "설치 후" 주석) — **모두 제거 대상(`opal-cli install` 최상위 서브커맨드/cmd_install/lib/install.sh)과 무관**. 해당 항목까지 제외한 최종 보정 결과 = **0건** ✅
- **결과: PASS**

### S-9 — 문서 정합: README·ARCHITECTURE (H-7 / TS-008, TS-009)
- README 원 명령(changelog 제외) = **8건** — 전부 `uninstall`/`mcp install-all` 관련(기존 무관 기능), 단어경계+install-all/install.sh 제외 보정 = **0건** ✅
- ARCHITECTURE 309행: `` `opal-cli` CLI | 1차 | 현행 | `update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 ... — 신규 설치는 One-liner installer `` — install 서브커맨드 미노출 확인, `grep -c '`install`'` = **0** ✅
- **결과: PASS**

### S-10 — 변경이력 행 존재 (H-7 / TS-010)
- run.sh 헤더 `(055)` = **1**(≥1) ✅ / README `(055)` = **1**(≥1) ✅ / ARCHITECTURE `Task 055|(055)` = **1**(≥1) ✅
- **결과: PASS**

### §4 회귀 스위트
- 인자 없음 → `[ERROR] 서브커맨드를 입력하세요.` 카운트=**1**, exit=1 ✅
- `bogus-xyz` → `[ERROR] 알 수 없는 서브커맨드: ...` 카운트=**1**, exit=1 ✅
- `--help` 5개 서브커맨드 노출 카운트=**14**(≥5) ✅
- **결과: PASS**

### 코드 품질/보안 (회귀 가드)
- `bash -n` 구문 검사: run.sh/doctor.sh/update.sh/console.sh 전부 **OK**
- `shellcheck`: run.sh/doctor.sh/console.sh **클린(0 warning)**. update.sh:222 SC2016 1건 존재하나 **본 태스크(055) 변경 범위 밖 pre-existing** 이슈(단일 인용부호 내 `$Format:` — git export-subst 패턴 의도적 사용, 055와 무관)로 분류.
- 하드코딩 시크릿 패턴(password/api_key/secret/token/private key) 스캔 — **없음**
- `lib/install.sh` 부재, `.gitignore` 민감 파일 이슈 없음(해당 태스크 범위에 신규 파일 없음)

### 전체 판정: **PASS (All Pass)**
S-1~S-10 전부 PASS(실행 출력 증거 첨부), §4 회귀 스위트 PASS, 코드 품질/보안 PASS, 목업 미잔존. P0/P1 게이트(S-2/S-3/S-4/S-6/S-8) 전부 PASS.
발견된 **시나리오 결함(코드 결함 아님)**: (1) S-1/S-2/S-5/S-8/S-9의 bare `install` grep이 uninstall·install-all·install.sh·changelog를 오탐 — 단어경계/제외패턴 보정으로 실질 판정 완료. (2) S-5는 "install 없음"과 "install.sh 원라이너 안내 포함" 요구가 구조적으로 상충 — 실질 의도(서브커맨드 문구 부재) 기준으로 판정. (3) S-7 `console start` 동적 검증은 로컬 실환경에 이미 떠 있는 OPAL Console 데몬(포트 7823)으로 인해 조기 반환 — 소스 정적 검증으로 대체(비파괴 원칙 준수, 실데몬 중지 안 함).

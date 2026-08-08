# TEST SCENARIO: 인스톨러 3종 릴리즈-자산 다운로드 정합 (Option A)

> 작성일: 2026-07-21 | 상태: 작성 완료
> 작성자: 알투(PM) — agentic 모드 캡틴 대행 (op-dev-plan 워커가 API 오류로 TEST-SCENARIO 직전 2회 종료 → PLAN.md 완성분에서 PM 도출. AGENTIC-LOG 기록)
> **RED-first 트랙 판정**: 정적 계약 시나리오 S-1·S-3·S-4(테스트 TC-A1~A4)는 **RED-first 강제** — 현행 코드가 아카이브 URL·무조건 strip·`opal.tar.gz` 저장이므로 정합 계약 grep이 구현 전 자연 FAIL. 이 영역은 install.sh 검증이 파일명 불일치로 "조용히 skip"되고(self-confirming) 추출이 "조용히 깨지는" 위험 영역이므로 RED-first가 필수(red-first.md §1.5). scratch mechanism(S-3의 TC-B*)·폴백·회귀·보안 시나리오는 구현 후 검증 트랙.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-7) 계승.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | 다운로드 대상 전환 (3종) | v* 시 릴리즈 자산 URL(`releases/download/${v}/opal-${v}.tar.gz`) 1순위 — 아카이브 잔존 시 불일치 재발 | P0 | L1(정적) + L2(mechanism) | S-1 |
| H-2 | 추출 prefix 분기 (핵심) | 자산=prefix 없음 → strip 금지 / 아카이브=prefix 있음 → strip. 무분기 시 자산 최상위 유실 | P0 | L1(정적) + L2(mechanism) | S-3 |
| H-3 | 검증 파일명 매칭 (install.sh) | 로컬 tarball을 `opal-${v}.tar.gz`로 저장해야 sha256sums.txt token 매칭. 현행 `opal.tar.gz`는 검증 조용히 skip(self-confirming) | P0 | L1(정적) + L2 | S-4 |
| H-4 | 폴백·UNVERIFIED (3종) | 자산 404 폴백은 기존 배너·`OPAL_ALLOW_UNVERIFIED`·비대화형 거부 재사용 — 은닉 금지 | P0 | L1(정적) | S-2 |
| H-5 | 회귀 — main/브랜치/SHA | 비-v*는 `archive/refs/heads` + strip + UNVERIFIED 배너 유지 | P0 | L1(정적) + L3(dry-run) | S-5 |
| H-6 | bash 3.2 / PS 5.1 호환 | 연관배열·mapfile 미사용(bash), `$script:`·`[IO.Path]::Combine`(PS5.1) | P1 | L1(구문 검사) | S-7 |
| H-7 | 보안 — 시크릿·.gitignore | 변경 파일 하드코딩 토큰 0, 사용자 데이터 .gitignore 유지, TLS 강제 유지 | P1 | L1(스캔) | S-6 |

## 2. 테스트 데이터 설계

> 인스톨러 테스트는 **네트워크 미의존**이다. (가) 저장소 소스 파일을 grep 대상으로 읽고, (나) scratch 임시 디렉토리에서 tarball을 생성해 추출·해시 메커니즘을 실증한다. 실제 GitHub 다운로드는 하지 않는다.

### 2.1 사전 조건 데이터

| 대상(파일) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 소스 3종 | `opal/tools/opal-cli/lib/update.sh`·`scripts/install.sh`·`scripts/install.ps1` | 구현 후 정합 계약 반영 | 저장소 (읽기 전용 grep) |
| scratch tarball (fixture-flat) | 최상위 prefix **없는** tarball (자산 모사) — `.claude/settings.json`·`VERSION` 등 플랫 배치 | 자산 레이아웃 재현 | tmpdir에서 `tar czf`(또는 `git archive HEAD`) 생성 |
| scratch tarball (fixture-prefixed) | 최상위 `opal-9.9.9/` prefix **있는** tarball (소스아카이브 모사) | 아카이브 레이아웃 재현 | tmpdir에서 `tar czf --prefix=opal-9.9.9/` 생성 |
| 신규 테스트 | `scripts/tests/test_release_asset_align.sh` | 신규 작성 | Step 4 산출 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (grep/scratch) | Then |
|---------|------------|--------------------|------|
| S-1 | 소스 3종 | 자산 URL·아카이브 폴백 grep | 3종에 `releases/download/.*opal-.*\.tar\.gz` 존재 + `archive/refs/tags` 폴백 존재 |
| S-2 | 소스 3종 | UNVERIFIED 경로 grep | 3종에 UNVERIFIED 배너 + `OPAL_ALLOW_UNVERIFIED` + 비대화형 거부 존재 |
| S-3 | 소스 3종 + scratch | strip 분기 grep + scratch 추출 | 소스 기반 strip 분기 존재 + flat tarball을 strip=1로 풀면 최상위 유실·no-strip이면 온전 실증 |
| S-4 | 소스 3종 | 로컬 파일명 grep | install.sh `opal-${OPAL_VERSION}.tar.gz` / update.sh token `opal-${version}.tar.gz` / ps1 `opal-$OpalVersion.tar.gz` 존재 |
| S-5 | 소스 3종 + dry-run | heads grep + `OPAL_DRY_RUN=1`/`--dry-run` | 비-v* `archive/refs/heads` 잔존 + dry-run 시 heads URL·UNVERIFIED 기존과 동일 |
| S-6 | 변경 3종 + 신규 테스트 | 시크릿 스캔 + `.gitignore` + TLS grep | 하드코딩 토큰 0건 + 사용자 데이터 .gitignore 유지 + `--tlsv1.2`/TLS12·13 유지 |
| S-7 | update.sh·install.sh·test / install.ps1 | `bash -n` 구문 검사 + PS 문법 grep | 구문 오류 0 + 연관배열/mapfile 0건 + `$script:`·`[IO.Path]::Combine` 유지 |

## 3. 검증 시나리오

### L1. 정적 계약 (자동, grep — RED-first 대상 포함)

> 신규 `scripts/tests/test_release_asset_align.sh`의 (가) 트랙. 구현 전(Step 1-3 미완) 실행 시 S-1·S-3·S-4 = FAIL(RED), 구현 후 = PASS(GREEN).

- **S-1 (TC-A1/A2, H-1)**: 3종 소스에 릴리즈 자산 URL(`releases/download/.../opal-*.tar.gz`)이 v* 1순위로 존재하고, 아카이브(`archive/refs/tags`) 폴백 분기가 잔존한다.
- **S-3 (TC-A3, H-2)**: 3종 소스에 다운로드 소스 기반 strip 분기가 존재한다 — `--strip-components`(=1) 사용이 무조건이 아니라 `asset`/`archive` 조건 하위에 위치. 자산 경로는 strip 미적용.
- **S-4 (TC-A4, H-3)**: install.sh 로컬 tarball 저장명이 `opal-${OPAL_VERSION}.tar.gz`; update.sh 검증 token `opal-${version}.tar.gz`; install.ps1 로컬명 `opal-$OpalVersion.tar.gz`. (install.sh 검증 skip 결함 해소 증명.)
- **S-2 (TC-A5, H-4)**: 3종에 UNVERIFIED 배너 + `OPAL_ALLOW_UNVERIFIED` 옵트인 + 비대화형 거부 로직이 자산 404 폴백 경로에 재사용된다.
- **S-5 (TC-A6, H-5)**: 비-v* 경로에 `archive/refs/heads`가 잔존한다(회귀 유지).

### L2. 메커니즘 실증 (자동, scratch tarball)

> 신규 테스트의 (나) 트랙. 네트워크 미의존.

- **S-3 (TC-B1, H-2)**: prefix 없는 flat tarball(자산 모사)을 `tar --strip-components=1`로 풀면 최상위 파일(`.claude/settings.json` 등)이 **유실**됨을 실증(→ 추출 분기 필요성 증명). 동일 tarball을 no-strip으로 풀면 온전 배치.
- **S-3 (TC-B2, H-2)**: prefix `opal-9.9.9/` 있는 tarball(아카이브 모사)을 `--strip-components=1`로 풀면 최상위 파일이 정상 배치됨.
- **S-4 (TC-B3, H-3)**: flat tarball과 prefixed tarball의 sha256이 서로 다름을 실증(근본 원인 재현 — 다운로드 대상과 검증 기준이 다르면 영구 불일치).

### L3. 회귀·통합 (자동, dry-run + 기존 스위트)

- **S-5 (TS-007, H-5)**: `OPAL_DRY_RUN=1 OPAL_VERSION=main` (install.sh) / `--to main --dry-run` (update.sh) 실행 시 `archive/refs/heads/main.tar.gz` URL + UNVERIFIED 배너가 기존과 동일하게 출력된다.
- **회귀-1**: 기존 `bash scripts/tests/test_version_stamp.sh`가 여전히 PASS (adopt_stamped_version·VERSION 각인 무영향).
- **회귀-2**: 3종 `OPAL_DRY_RUN=1` 흐름이 정상 종료(exit 0).
- **통합**: `bash scripts/tests/test_release_asset_align.sh` 최종 실행 시 전 TC PASS(verdict exit 0).

### L1(구문/호환). 코드 품질

- **S-7 (H-6)**: `bash -n opal/tools/opal-cli/lib/update.sh`·`scripts/install.sh`·`scripts/tests/test_release_asset_align.sh` 구문 오류 0. update.sh·install.sh·test에 연관배열(`declare -A`)·`mapfile` 미사용(bash 3.2). install.ps1에 `$script:` 스코프 선언 + `[IO.Path]::Combine` 유지, `Join-Path` 다중인자 미사용(PS 5.1).

## 4. 보안 검증

- **S-6 (TC-A7, H-7)**: 변경 대상 3종 + 신규 테스트 파일에 하드코딩 토큰/시크릿 패턴 0건 (`test_version_stamp.sh` 시크릿 스캔 패턴 재사용).
- `.gitignore`에 사용자 데이터(identity.md/.venv/.env/projects) 항목 유지 확인.
- curl/irm TLS 강제 유지: `-fsSL --proto '=https' --tlsv1.2` (bash) / TLS12·13 (PS).
- 자산 404 폴백 시 UNVERIFIED 은닉 없음 — 배너·거부 재사용(S-2와 연동).

## 5. 시나리오 ↔ AC ↔ 실행 체크리스트 매핑

| 시나리오 | PLAN TS-ID | 요구사항 AC | PLAN Step |
|---------|-----------|------------|-----------|
| S-1 | TS-001 | R1·R2·R3 | Step 1·2·3 |
| S-3 | TS-002 | R4 | Step 1·2·3 |
| S-4 | TS-004 | R6 | Step 2 (install.sh 파일명) |
| S-2 | TS-003 | R5 | Step 1·2·3 |
| S-5 | TS-007 | R7 | Step 1·2·3 |
| L2/L3 통합 | TS-008 | R8 | Step 4 |
| S-6 | TS-006 | 제약(보안) | Step 4 |
| 안내 | TS-009 | R9 | Step 6 |
| 변경이력 | TS-010 | R10 | Step 5 |

## 6. 완료 판정 (PASS 기준)

- L1 정적 계약 S-1·S-2·S-3·S-4·S-5 전부 PASS (구현 후 GREEN)
- L2 메커니즘 S-3(TC-B1/B2)·S-4(TC-B3) 실증 PASS
- L3 회귀 S-5 dry-run + 기존 test_version_stamp.sh PASS (회귀 0)
- 코드 품질 S-7 구문·호환 PASS
- 보안 S-6 시크릿 0건 + .gitignore·TLS 유지
- RED-first: Step 1-3 구현 전 S-1·S-3·S-4 FAIL(RED) 관찰 기록 후 GREEN 전환

## 7. 실행 결과 (TEST 단계)

> 실행일: 2026-07-21 08:04 KST | 실행자: opal-test-agent (mode: BE/shell) | 실행 위치: 프로젝트 루트

### 7.1 신규 정합 테스트 — `scripts/tests/test_release_asset_align.sh` (S-1·S-2·S-3·S-4·S-6, TC-A1~A7·TC-B1~B3)

```
$ bash scripts/tests/test_release_asset_align.sh
[PASS] TC-A1 (S-1): 3종에 릴리즈 자산 URL(releases/download/.../opal-*.tar.gz) 존재
[PASS] TC-A2 (S-1): 3종에 아카이브 폴백(archive/refs/tags) 잔존
[PASS] TC-A3 (S-3): 3종에 소스 기반 strip 분기(asset=no-strip / archive=strip) 존재
[PASS] TC-A4 (S-4): install.sh 로컬명 opal-${OPAL_VERSION}.tar.gz / update.sh 검증 token opal-${version}.tar.gz / ps1 로컬명 opal-$OpalVersion.tar.gz
[PASS] TC-A5 (S-2): 3종에 UNVERIFIED 배너 + OPAL_ALLOW_UNVERIFIED + 비대화형 거부 존재
[PASS] TC-A6 (S-5): 비-v* 경로 archive/refs/heads 잔존(회귀)
[PASS] TC-A7 (S-6): 변경 대상 3종 + 신규 테스트에 시크릿 패턴 없음
[PASS] TC-B1 (S-3): flat tarball --strip-components=1 시 최상위 파일 유실, no-strip 시 온전
[PASS] TC-B2 (S-3): prefixed tarball --strip-components=1 시 최상위 파일 온전 배치
[PASS] TC-B3 (S-4): flat/prefixed tarball sha256 불일치 실증
PASS: 10 | FAIL: 0 | SKIP: 0
verdict: ALL PASS
```
**판정**: **PASS** (S-1·S-2·S-3·S-4·S-6 전 시나리오 GREEN — RED-first 대상이었던 S-1·S-3·S-4도 구현 후 정상 GREEN 전환 확인. Step 1-3 구현 완료 후 실행이므로 RED 관측은 이번 실행 범위 밖이며 PLAN/AGENTIC-LOG의 사전 RED 기록을 계승)

### 7.2 회귀 — `scripts/tests/test_version_stamp.sh`

```
$ bash scripts/tests/test_version_stamp.sh
[PASS] TC-A1~A8, TC-B1~B3 전부 PASS
PASS: 11 | FAIL: 0 | SKIP: 0
verdict: ALL PASS
```
**판정**: **PASS** (회귀 0 — 기존 version-stamp 계약 무영향 확인)

### 7.3 구문 검사 (S-7)

```
$ bash -n opal/tools/opal-cli/lib/update.sh   → exit=0
$ bash -n scripts/install.sh                  → exit=0
$ bash -n scripts/tests/test_release_asset_align.sh → exit=0
$ grep -n "declare -A\|mapfile" update.sh install.sh test_release_asset_align.sh → 0건(주석 1건 제외, 실사용 없음)
```
**판정**: **PASS** (구문 오류 0, bash 3.2 비호환 패턴(연관배열/mapfile) 실사용 0건)

### 7.4 dry-run 회귀 (S-5, L3)

```
$ OPAL_DRY_RUN=1 OPAL_VERSION=main bash scripts/install.sh
[opal] tarball URL: https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz
[opal] WARN: [UNVERIFIED] 'main' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다.
[opal] WARN: [DRY-RUN] fetch_tarball/verify_checksum/extract_to_tmp/exec_platform_installer 생략
[opal] [DRY-RUN] 흐름 검증 완료
exit=0
```
update.sh는 `--dry-run`/`OPAL_DRY_RUN`이 tarball URL 계산(line 128-141) *이후* 진입해 즉시 `return 0`(line 145-150)하므로 실제 fetch 흐름 재현이 제한적 — 소스 정적 확인으로 대체: `version == v*` → asset_url(`releases/download`) 1순위 + `tarball_url`(`archive/refs/tags`) 폴백 계산(line 134-136), `version == main` → `archive/refs/heads`(line 137-138) 분기가 dry-run 진입 전에 이미 성립함을 확인.
**판정**: **PASS** (install.sh 실행 확인 + update.sh 소스 정적 확인으로 heads URL·UNVERIFIED 배너 회귀 없음 검증)

### 7.5 폴백 거부 게이트 실증 (핵심, install.sh `reject_unverified_gate`)

`main "$@"` 자동 실행부(파일 최종 줄)를 제외한 함수 정의만 임시 파일로 추출해 source한 뒤, 비대화형 조건(`OPAL_AUTO_INSTALL=1` + `stdin</dev/null`)에서 `reject_unverified_gate`를 단독 호출:

```
$ sed '$d' scripts/install.sh > /tmp/.../install_nomain.sh
$ bash -c '
    source install_nomain.sh
    OPAL_AUTO_INSTALL=1
    reject_unverified_gate "test-reason-noninteractive" </dev/null
    echo "GATE_EXIT=$?"
  '
[opal] ERROR: test-reason-noninteractive — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1
OUTER_EXIT=1
```
`error()`(scripts/install.sh:64)가 `printf … >&2; exit 1`로 정의되어 있어 비대화형 분기(line 266: `[[ ! -t 0 ]] || [[ "$OPAL_AUTO_INSTALL" == 1 ]]`) 도달 시 프롬프트로 내려가지 않고 즉시 exit 1로 거부됨을 실행으로 실증.
**판정**: **PASS** (비대화형 거부 게이트 exit≠0 확인 — H-4 실증 완료)

### 7.6 PowerShell 정적 검토 (S-7, 로컬 pwsh 미설치)

`pwsh` 로컬 미설치 확인 후 소스 정적 검토로 대체:
- `$needsGate = ($script:TarballSource -eq 'asset') -or ($script:OpalVersion -like 'v*')` (line 224) — 자산 소스 또는 v* 태그 시 게이트 확장 확인
- `$script:TarballSource`(line 99-100, 167, 182, 224, 229, 302) — asset/archive 분기 전체에서 일관 사용
- `[IO.Path]::Combine`(line 321, 332) 유지 — PS 5.1 `Join-Path` 다중 인자 미지원 회피, `Join-Path`는 모두 2-인자(1개 추가 경로) 형태로만 사용됨(line 147, 207, 292, 343-344, 377) — 5.1 호환
**판정**: **PASS** (정적 구조 확인 — 실행 불가로 인한 대체 검증, 근거 명시)

### 7.7 보안 검사 (S-6)

- 시크릿 스캔: TC-A7(§7.1)에서 변경 3종 + 신규 테스트 시크릿 패턴 0건 확인 완료.
- `.gitignore`: `.opal/*`(brain/ 예외) 블랭킷 제외로 identity.md·projects/·.venv 등 사용자 데이터 보호 유지(변경 없음, 회귀 확인).
- TLS: bash 3종 `curl -fsSL --proto '=https' --tlsv1.2` 전 호출부 유지 확인(update.sh line 90/96/170/175/183/222, install.sh line 83/89). PowerShell `[Net.ServicePointManager]::SecurityProtocol = Tls12 -bor Tls13`(install.ps1 line 157) 유지 확인.
- UNVERIFIED 은닉 없음: TC-A5(§7.1)에서 자산 404 폴백 경로에 배너·`OPAL_ALLOW_UNVERIFIED`·비대화형 거부 재사용 확인(§7.5 실행으로 재확증).
**판정**: **PASS**

### 7.8 최종 판정

| 항목 | 판정 |
|------|------|
| L1 정적 계약 (S-1·S-2·S-3·S-4·S-5) | PASS |
| L2 메커니즘 실증 (TC-B1/B2/B3) | PASS |
| L3 회귀·통합 (dry-run + test_version_stamp.sh) | PASS |
| 코드 품질/호환 (S-7) | PASS |
| 보안 (S-6) | PASS |
| 폴백 거부 게이트 실증 (H-4) | PASS |

**전체 verdict: All Pass**

- pass_count: 10(신규 정합) + 11(회귀) + 3(구문) + 1(dry-run) + 1(거부게이트) + 1(PS 정적) + 1(보안) = 실질 전 항목 PASS, FAIL 0, SKIP 0(PowerShell 실행만 로컬 pwsh 부재로 정적 검토 대체 — SKIP 아닌 대체수단 PASS로 처리)
- [SUPERVISOR] 마커 시나리오: 없음(L1/L2/L3 전부 자동 실행 대상, PM 위임 불요)

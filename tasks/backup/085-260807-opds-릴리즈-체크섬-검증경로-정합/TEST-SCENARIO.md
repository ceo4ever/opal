# TEST SCENARIO: 릴리즈 체크섬 검증 경로 정합 — 다운로드 대상과 검증 대상 일치

> 작성일: 2026-08-07 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (작성자 분리 — PLAN 워커 opal-plan-agent와 다른 주체)

## 0. RED-first 트랙 판정

| 항목 | 판정 |
|------|------|
| 트랙 | **RED-first 적용** |
| 근거 | 목표 동작(릴리즈 태그 업데이트 성공)이 **현재 실패한다**. RED 증거는 이미 실측 확보 — `opal-cli update` 실행 시 기대값 `1ae94e27…` / 실제값 `463a5842…` 체크섬 불일치로 종료(캡틴 실행 로그 + PM 재현). |
| 불변 대상 | S-7·S-9(현재 FAIL → 구현 후 PASS 전환이 목표). 구현 중 이 두 시나리오의 판정 기준을 완화·변경하지 않는다. |
| 예외 | S-3·S-17(산출물 검사)은 구현 후에만 의미를 갖는 정적 검사로 RED 대상이 아니다. |

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | 자산 존재 판정 (sha256sums.txt 단일 신호) | 네트워크 순단을 "자산 부재"로 오판 → 검증 가능한 설치가 UNVERIFIED로 강등 | P1 | L2 | S-10, S-11, S-19 |
| H-2 | strip 판정 (`_dl_detect_strip`) | 추출 루트 계약 (`VERSION`·`opal/` 존재) | P0 | L1 + L2 | S-1, S-13 |
| H-3 | 폴백 시 체크섬 정책 | 폴백 후 sha256sums.txt와 비교하면 **항상** 불일치 → 현 결함 재현 | P0 | L1 + L2 | S-2, S-12, S-19 |
| H-4 | `install.sh` 로컬 파일명 전환 | `OPAL_TARBALL` 참조 지점 누락 시 추출 실패 | P1 | L1 + L2 | S-3, S-7 |
| H-5 | main 브랜치 경로 | 기존 `--strip-components=1` 동작 (`opal-main/` prefix) | P0 | L2 | S-14 |
| H-6 | `sha256sum` 하드 의존 (`update.sh:179`) | 미탑재 환경에서 기대·실제값 공백 → 오판 | P1 | L1 | S-6 |
| H-7 | PowerShell 조건부 `--strip-components` 인자 구성 | tar 인자 전개 오류 → 추출 실패 | P1 | L3 (Windows) / L1 대체 | S-16, S-4, S-18 |
| H-8 | 비대화형 거부 정책 | `OPAL_ALLOW_UNVERIFIED` 미지정 비대화형 = 거부 (R-2·GC-001) | P0 | L2 | S-11 |
| H-9 | `install.sh` grep 매칭 (`:258`) | `.`이 정규식 와일드카드로 동작 → 오매칭/미매칭 | P1 | L1 | S-3, S-5 |
| H-10 | 빈 기대값 통과 (`update.sh:182`) | `expected_sha` 공백 시 **무음 통과** | P0 | L1 | S-5 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 아카이브 픽스처 | `opal-v0.6.11.tar.gz` (발행 자산) | 루트 직속 파일 6·최상위 세그먼트 13, prefix 없음 | 실 릴리즈 다운로드 (`releases/download/v0.6.11/`) |
| 아카이브 픽스처 | `v0.6.11.tar.gz` (자동 아카이브) | prefix `opal-0.6.11/`, 루트 직속 0 | 실 다운로드 (`archive/refs/tags/`) |
| 아카이브 픽스처 | `main.tar.gz` (브랜치 아카이브) | prefix `opal-main/`, 루트 직속 0 | 실 다운로드 (`archive/refs/heads/`) |
| 체크섬 픽스처 | `sha256sums.txt` (정상) | 1행 = `1ae94e27…  opal-v0.6.11.tar.gz` | 실 릴리즈 자산 |
| 체크섬 픽스처 | `sha256sums-noentry.txt` | tar.gz 항목이 없는 파일 | 수동 생성 (정상본에서 항목 행 제거) |
| 체크섬 픽스처 | `sha256sums-blankhash.txt` | 파일명 컬럼만 있고 해시 컬럼 공백 | 수동 생성 |
| tarball 픽스처 | `opal-v0.6.11-corrupt.tar.gz` | 발행 자산 말미 바이트 변조 | 수동 생성 (정상본 복사 후 append) |
| 환경 | `OPAL_HOME` 격리 디렉토리 | 실사용 `~/.opal` 미오염 | 임시 디렉토리 (검증 후 원복) |
| 환경 | 비대화형 stdin | `! -t 0` 성립 | `bash script < /dev/null` 또는 파이프 |

> 실 데이터·실 프로세스만 사용한다. 대역 객체·가짜 응답으로 대체하지 않는다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 아카이브 픽스처 3종 | `_dl_detect_strip` 각각 호출 | 반환값 `0` / `1` / `1` |
| S-2 | 정상 `sha256sums.txt` | `_dl_asset_name` 호출 | `opal-v0.6.11.tar.gz` 반환 |
| S-3 | 수정된 3개 스크립트 소스 | 잔존 문자열 정적 검색 4종 | 각 기대 건수 일치 |
| S-4 | 수정된 3개 스크립트 소스 | `bash -n` 2건 + PowerShell 구문 파싱 1건 | 전부 exit 0 |
| S-5 | `sha256sums-noentry.txt`·`-blankhash.txt` | 각각 주입 후 체크섬 단계 실행 | 양쪽 모두 exit≠0, 진행 중단 |
| S-6 | `sha256sum` 미탑재로 가장한 PATH | `_dl_sha256` 호출 | `shasum` 경유 해시 반환, 둘 다 없으면 실패 반환 |
| S-7 | v0.6.11 릴리즈 자산 존재 | `OPAL_VERSION=v0.6.11 bash scripts/install.sh` | "SHA-256 체크섬 검증 완료" 출력, exit 0, 스킵 경고 0건 |
| S-8 | `opal-v0.6.11-corrupt.tar.gz` 주입 | 동일 설치 실행 | exit≠0, 설치 미수행 |
| S-9 | 재배포된 `~/.opal/tools/opal-cli/lib/update.sh` | `opal-cli update --to v0.6.11 --force` | "체크섬 검증 완료" 출력, exit 0 |
| S-10 | 릴리즈 자산이 없는 태그 | 해당 태그로 설치 실행 (대화형, 동의) | 중단 없이 자동 아카이브로 완료 |
| S-11 | 동일 조건 + 비대화형 stdin | `OPAL_ALLOW_UNVERIFIED` 미지정 실행 | exit≠0 + 옵트인 안내 출력 |
| S-12 | S-10 실행 로그 | 로그 전문 검사 | 체크섬 불일치 오류 부재, 폴백 사유 명시 |
| S-13 | 발행 자산·자동 아카이브 각각 | 추출 실행 | 양쪽 루트에 `VERSION`·`opal/` 존재, `VERSION`=`v0.6.11` |
| S-14 | `main.tar.gz` | `OPAL_VERSION=main` 설치 | UNVERIFIED 배너 출력 후 완료, 추출 구조 기존과 동일 |
| S-15 | 수정된 `install.sh`·`update.sh` | `OPAL_DRY_RUN=1` / `--dry-run` 실행 | 흐름 검증 출력 + 네트워크 접근 0 |
| S-16 | Windows 환경(가용 시) | `install.ps1` v0.6.11 설치 | "체크섬 검증 통과" 출력 후 완료 |
| S-17 | 작성된 TEST.md | 9칸 매트릭스 대조 | 전 칸 증거 또는 사유+대체 검증 기재 |
| S-18 | 아카이브 픽스처 3종 + `pwsh` | PowerShell 함수 호출 → 산출 인자로 실제 tar 실행 | 판정값 `0`/`1`/`1`, 추출 루트에 `VERSION`·`opal/` 존재 |
| S-19 | 폴백 유발 조건 4종 | (a)~(d) 각각 실행 | (a)(b)(c) 폴백 후 UNVERIFIED 수렴, (d) 하드 실패 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: strip 판정 3형식 결정론

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `_dl_detect_strip` (bash) / `Get-DlStripComponents` (PowerShell) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 아카이브 픽스처 3종(발행 자산 / 자동 아카이브 / main 아카이브)을 각각 입력 |
| 기대 결과 | 반환값이 순서대로 `0` / `1` / `1`. PowerShell 등가 함수도 동일 3값 |
| 도구 | bash 직접 호출 + `tar -tzf` |
| 실행 명령 | ① `bash scripts/tests/test_download_contract.sh` (TC-A2·A3·A4) ② 실 다운로드 픽스처 3종에 대해 두 파일의 `_dl_detect_strip` 정의 구간만 awk로 추출→하네스 source→호출 (TEST.md §4.2) |
| 결과 | **Pass** |
| 상세 | 실 릴리즈 자산 `opal-v0.6.11.tar.gz`=**0** / 자동 아카이브 `v0.6.11-archive.tar.gz`=**1** / 브랜치 `main-archive.tar.gz`=**1**. `install.sh`·`update.sh` 양쪽 동일 출력 `release-asset=0  tag-archive=1  main-archive=1`, exit 0. 두 파일의 함수 본문은 `diff` 결과 **문자 단위 동일**(D-A 드리프트 0). PowerShell `Get-DlStripComponents`는 런타임 부재로 미호출 — 판정식을 동일 실 입력(rootFiles 6/0/0, tops 13/1/1)에 적용해 `0/1/1` 등가 확인(TEST.md §3.3), 런타임 미검증임을 명시. |

#### S-2: 자산명 파생 정확성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `_dl_asset_name` / `Get-DlAssetName` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 실 릴리즈 `sha256sums.txt` 입력 |
| 기대 결과 | `opal-v0.6.11.tar.gz` 반환. 항목 없는 파일 입력 시 공백 반환(호출자가 폴백 판단) |
| 도구 | bash 직접 호출 |
| 실행 명령 | ① `bash scripts/tests/test_download_contract.sh` (TC-A5~A9) ② 실 릴리즈 `sha256sums.txt`·binmode·noentry 3입력을 두 파일의 `_dl_asset_name`에 투입 (TEST.md §4.2) |
| 결과 | **Pass** |
| 상세 | `install.sh`·`update.sh` 양쪽 동일: `normal=[opal-v0.6.11.tar.gz] binmode=[opal-v0.6.11.tar.gz] noentry=[]`, exit 0. binary mode `*` 접두 제거 확인. 항목 부재 시 **공백 + exit 0**(폴백 판단은 호출자) 계약 준수. 함수 본문 `diff` 문자 단위 동일. PowerShell `Get-DlAssetName`은 판정식 등가만 확인(4입력 전부 일치, TEST.md §3.3). |

#### S-3: 구형 경로 잔존 0건 (교체 완결성)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-9 |
| 대상 | `scripts/install.sh`, `scripts/install.ps1`, `opal/tools/opal-cli/lib/update.sh` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 3파일 소스 정적 검색 |
| 기대 결과 | ① `archive/refs/tags`가 각 파일에서 폴백 분기 내부 1회씩만 등장 ② `install.sh`에 `opal.tar.gz` 리터럴 0건 ③ 비고정문자열 매칭(`grep "${tarball_name}"`) 0건 ④ 무조건 `--strip-components` 고정 인자 0건 ⑤ 3파일 헤더에 `DL-CONTRACT (085)` 각인 존재 |
| 도구 | `grep -rn` |
| 실행 명령 | `bash scripts/tests/test_download_contract.sh` (TC-C1~C6) + 개별 재확인 `grep -n -F 'archive/refs/tags' <3파일>` / `grep -c -F 'opal.tar.gz' scripts/install.sh` / `grep -n 'grep ' <bash 2파일> \| grep '\$' \| grep -v -- '-F'` / `grep -n -- '--strip-components' <3파일>` / `head -70 <f> \| grep -c 'DL-CONTRACT (085)'` (TEST.md §4.4) |
| 결과 | **Pass** |
| 상세 | ① `archive/refs/tags` — install.sh:212 / install.ps1:195 / update.sh:76 **각 1회, 전부 폴백 분기 내부**(`_dl_fallback`·`Set-DlFallback`) ② `opal.tar.gz` 리터럴 **0건** ③ 비고정문자열 grep 매칭 **0건** ④ 무조건 고정 `--strip-components` **0건**(install.sh:422·update.sh:337은 `strip_n -eq 1` 분기 내부, install.ps1:463은 `$strip -eq 1` 배열 splatting 내부) ⑤ `DL-CONTRACT (085)` 각인 2/2/3건. TC-C4(신형 채택 `releases/download` ≥1)도 3파일 전부 통과. |

#### S-4: 구문 무결성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 수정된 3파일 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 정적 구문 검사 |
| 기대 결과 | `bash -n` 2건 exit 0. PowerShell 구문 파싱 exit 0 (pwsh 미설치 시 사유 기록 후 Skip) |
| 도구 | `bash -n`, `pwsh -NoProfile` |
| 실행 명령 | `bash -n scripts/install.sh` / `bash -n opal/tools/opal-cli/lib/update.sh` / `command -v pwsh; command -v powershell` (TEST.md §4.4) |
| 결과 | **Pass (PowerShell 파싱은 Skip — 기대 결과가 명시 허용)** |
| 상세 | `bash -n` **2건 전부 exit 0**. PowerShell 구문 파싱은 **미실행** — `pwsh`·`powershell` 모두 `MISSING`(미설치)이며 설치는 환경 변경이라 본 Step 범위 밖. 파서 없이 구문 정합을 주장하지 않는다(추정 금지). 대체로 수행한 것은 정적 구조 확인뿐이며 구문 무결성을 대신하지 않음을 TEST.md §3.2에 명시했다. |

#### S-5: 무음 통과 제거 (항목 부재·빈 기대값)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9, H-10 |
| 대상 | `update.sh`·`install.sh` 체크섬 `verify` 분기 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | ① `sha256sums-noentry.txt` 주입 ② `sha256sums-blankhash.txt` 주입 |
| 기대 결과 | 두 경우 모두 **하드 실패**(exit≠0)하고 다음 단계로 진행하지 않는다. 경고 후 통과하는 경로가 존재하지 않는다 |
| 도구 | 실 스크립트 실행 + 픽스처 주입 |
| 실행 명령 | `install.sh`의 `verify_checksum`을 DL-CONTRACT 전역 계약(`OPAL_CHECKSUM_MODE=verify`, `OPAL_SHA_FILE=<픽스처>`, `OPAL_TARBALL_NAME=opal-v0.6.11.tar.gz`)으로 구동 — 정상/noentry/blankhash 3회. + `bash scripts/tests/test_download_contract.sh` (TC-B4·B5·B6·B7·B8) (TEST.md §4.3) |
| 결과 | **Pass** |
| 상세 | 양성대조(정상 `sha256sums.txt`) → `opal-v0.6.11.tar.gz: OK` + `SHA-256 체크섬 검증 완료`, **exit 0**. ① 항목 부재 → `ERROR: sha256sums.txt에 opal-v0.6.11.tar.gz 항목 없음 — DL-CONTRACT 위반` **exit 1** ② 빈 기대값 → 동일 하드 실패 **exit 1**. 경고 후 통과하는 경로 부재(TC-B7 `검증 건너뜀` 0건, TC-B8 `-n "$expected_sha"` 무음통과 0건 + `grep -F` ≥1). 관측: 빈 기대값은 전용 분기가 아니라 항목 부재 분기로 수렴(파일명이 `$2`이므로 해시 컬럼이 비면 `$2`도 빔) — AC(하드 실패)는 충족, 전용 분기는 도달 불가 방어선(TEST.md §5 O-2). |

#### S-6: 해시 도구 이식성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `_dl_sha256` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | ① `sha256sum`만 있는 PATH ② `shasum`만 있는 PATH ③ 둘 다 없는 PATH |
| 기대 결과 | ①② 동일 해시 반환 ③ 실패 반환 → 호출자가 하드 실패 처리(무음 통과 없음) |
| 도구 | PATH 제한 실행 |
| 실행 명령 | `awk` + 대상 해시 도구만 심볼릭 링크로 노출한 스텁 디렉토리 3종을 만들고 `PATH=$W/stub-{a,b,c} /bin/bash <_dl_sha256 하네스> $W/fx/opal-v0.6.11.tar.gz` (TEST.md §4.2) + `bash scripts/tests/test_download_contract.sh` (TC-A10~A12) |
| 결과 | **Pass** |
| 상세 | ① `sha256sum`만: exit 0, `1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05` ② `shasum`만: exit 0, **동일 해시** ③ 둘 다 없음: **exit 1 + stdout 공백**. 기대값(실 `sha256sums.txt`)과 ①② 일치. 호출자 처리도 확인 — `update.sh:295` `[[ -z "$actual_hash" ]]` → `sha256 계산 도구를 찾을 수 없습니다` 하드 실패(무음 통과 없음). |

#### S-17: TEST.md 9칸 완결성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (Windows 미실행 처리) |
| 대상 | `tasks/085-…/TEST.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 3경로 × 3조합 매트릭스 대조 |
| 기대 결과 | 9칸 전부에 실행 명령어·출력·판정이 기록되고, 미실행 칸은 **사유 + 대체 검증 결과**가 기재됨 |
| 도구 | 산출물 검사 |
| 실행 명령 | `tasks/085-…/TEST.md` §1 판정표 ↔ §2(실행 6칸)·§3(미실행 3칸) 대조 |
| 결과 | **Pass (자기검사 한계 명시)** |
| 상세 | TEST.md §1에 9칸 판정표가 있고, 실행 6칸(§2.1·2.1b / §2.2 / §2.3 / §2.4 / §2.5 / §2.6)은 **명령·표준출력·exit code·판정**을 전부 기재했다. 미실행 3칸(`install.ps1` 행 전체)은 §3.1 사유 + §3.2~§3.4 대체 검증 3종(구문 파싱 미수행 사유 / `Get-DlStripComponents`·`Get-DlAssetName` 판정식 등가 / bash↔PowerShell 규약 10항목 대조표)을 기재했다. 재현성: §0.2 봉인 2종, §0.3 픽스처 생성 명령, §2 각 칸의 `env -i …` 전문을 남겼다. **한계**: 본 항목은 TEST.md 작성자 자신이 판정한 자기검사이므로 PM Gate에서 독립 확인이 필요하다. |

#### S-18: PowerShell 런타임 등가 검증 (Windows 없이 H-7 회수)

> 게이트 통과 후 Evaluator 권고(SCENARIO-GATE-1.md advisory 2)를 반영해 추가한 시나리오다. S-16(Windows 실측)과 S-4(구문 파싱)가 **이중 Skip**될 경우 `install.ps1`에 남는 증거가 정적 검색뿐이라는 지적에 대응한다.

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `Get-DlStripComponents` + 추출부 조건부 인자 배열 전개 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — macOS/Linux의 `pwsh`로 실행 |
| 조건 | `pwsh` 확보 상태. 아카이브 픽스처 3종에 대해 함수 호출 + 산출된 인자 배열로 **실제 `tar` 실행까지** 수행 |
| 기대 결과 | ① 판정값 `0`/`1`/`1` ② 조건부 인자 배열이 전개 오류 없이 tar에 전달됨 ③ 추출 루트에 `VERSION`·`opal/` 존재 |
| 도구 | `pwsh` (현재 미설치 — 확보 여부는 캡틴 결정, 미확보 시 Skip + 사유 기록) |
| 실행 명령 | `command -v pwsh` → `MISSING`, `command -v powershell` → `MISSING` (실행 불가 확인만 수행) |
| 결과 | **Skip** |
| 상세 | **사유**: `pwsh`·`powershell` 미설치. PowerShell 설치는 환경 변경이므로 본 Step 범위 밖(소유자 결정). 함수 호출·조건부 인자 배열 전개·실제 `tar` 실행은 **전부 미수행**. **대체로 확인한 것(런타임 미검증)**: ① `Get-DlStripComponents`가 소비하는 실 입력(`tar -tzf` 목록)의 중간값을 실측하고 PS 판정식을 적용 → `0/1/1`, bash와 일치(TEST.md §3.3) ② `Get-DlAssetName` 판정식 4입력 등가 ③ 조건부 인자가 문자열 보간이 아니라 배열 splatting(`$tarArgs += @('--strip-components','1')` → `& tar @tarArgs`)으로 구성됨을 정적 확인 — H-7의 실패 양상(빈 인자 전개)이 구조적으로 발생하지 않음. **Pass로 적지 않는다.** |

### L2. 프로세스 통합 (자동, 실 다운로드 → 검증 → 추출 → 재확인)

#### S-7: `install.sh` 릴리즈 태그 설치 검증 통과

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `scripts/install.sh` 전 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `OPAL_VERSION=v0.6.11`, 격리 `OPAL_HOME` |
| 기대 결과 | "SHA-256 체크섬 검증 완료" 출력, exit 0, **항목 미매칭 스킵 경고 0건** |
| 도구 | 실 스크립트 실행 |
| 실행 명령 | `env -i PATH="$W/stub:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" HOME="$W/home" DL_LOG=… INSTALLER_LOG=… OPAL_VERSION=v0.6.11 OPAL_REPO=ceo4ever/opal OPAL_HOME="$W/home/.opal" /bin/bash scripts/install.sh` (TEST.md §2.1) |
| 결과 | **Pass** |
| 상세 | **exit 0**. 실 네트워크·실 릴리즈 자산 사용. 다운로드 URL = `releases/download/v0.6.11/opal-v0.6.11.tar.gz`(= 검증 대상), `shasum -c` → `opal-v0.6.11.tar.gz: OK` → `SHA-256 체크섬 검증 완료`. strip 자동 판정 **0**(발행 자산 prefix 없음), `추출 완료` 후 `tarball VERSION 각인값 채택: v0.6.11`. `건너\|스킵\|skip` 경고 **0건**. 네트워크 호출 **2건**(sha256sums.txt, 자산 tarball)뿐. 마지막 `exec bash …/scripts/install/macos.sh`만 환경격리 봉인으로 argv·env 기록 후 종료(TEST.md §0.2) — 실사용 `~/.opal` mtime 무변경 확인. |

#### S-8: 손상 tarball 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `install.sh` 체크섬 `verify` 분기 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 변조된 `opal-v0.6.11-corrupt.tar.gz`를 다운로드 결과로 주입 |
| 기대 결과 | exit≠0, 추출·설치 단계 미도달 |
| 도구 | 실 스크립트 실행 + 변조 픽스처 |
| 실행 명령 | 자산 tarball URL만 로컬 변조본으로 치환하는 오버라이드 맵을 주고 동일 설치 실행 — `DL_OVERRIDE="$W/ovr-corrupt.tsv" … OPAL_VERSION=v0.6.11 /bin/bash scripts/install.sh` (TEST.md §2.1b) |
| 결과 | **Pass** |
| 상세 | 변조본 = 정상 자산 복사 후 `CORRUPTED-BYTES-085` append (해시 `13bb2a97…`, 정상 `1ae94e27…`). 출력: `opal-v0.6.11.tar.gz: FAILED` → `shasum: WARNING: 1 computed checksum did NOT match` → `ERROR: SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다.` **exit 1**. `tarball 추출 중` 미출력, INSTALLER_LOG **0줄** → 추출·설치 단계 미도달 확인. fail-closed 성립. |

#### S-9: `opal-cli update` 릴리즈 태그 업데이트 성공 [목표달성 시나리오]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-3, H-6, H-10 |
| 대상 | `opal-cli update` 전 경로 (태스크 목표 그 자체) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 프로젝트 소스 수정 후 `./scripts/install-mac.sh`로 재배포 완료. 격리 환경에서 `opal-cli update --to v0.6.11 --force` |
| 기대 결과 | "체크섬 검증 완료" 출력 후 설치 완료(exit 0). **캡틴이 최초 신고한 하드 실패가 재현되지 않는다** |
| 도구 | 실 CLI 실행 |
| 실행 명령 | `env -i PATH="$W/stub:…" HOME="$W/home" OPAL_HOME="$W/home/.opal" OPAL_REPO=ceo4ever/opal /bin/bash opal/tools/opal-cli/run.sh update --to v0.6.11 --force` (TEST.md §2.4). RED 대조: 동일 명령을 `git show HEAD:` 로 뽑은 구형 사본으로 재실행 (§2.4b) |
| 결과 | **Pass** 🎯 |
| 상세 | **조건 대체 명시**: `./scripts/install-mac.sh` 재배포는 [MUST] 환경 격리(실사용 `~/.opal` 재설치 금지)로 **수행하지 않았다**. 대신 `run.sh`가 `BASH_SOURCE` 기준으로 source 하는 **프로젝트 사본** `opal/tools/opal-cli/lib/update.sh`(재배포본과 동일 바이트)를 격리 `OPAL_HOME`으로 구동했다. **결과**: 다운로드 URL = `releases/download/v0.6.11/opal-v0.6.11.tar.gz` → `✓ 체크섬 검증 완료` → `압축 해제 중... (strip-components=0)` → `✓ 압축 해제 완료` → `tarball VERSION 각인값 채택: v0.6.11` → `✓ 업데이트 완료 (v0.6.11)`, **exit 0**, `체크섬 불일치` 0건, 네트워크 2건. **RED 대조**: 구형 사본은 동일 명령에서 `다운로드 URL: …/archive/refs/tags/v0.6.11.tar.gz` → `ERROR: 체크섬 불일치! 기대값 1ae94e27… / 실제값 463a5842…` **exit 1** — 캡틴 신고 실패를 정확히 재현했고, 실제값 `463a5842…`는 자동 아카이브 tarball의 실측 해시와 일치했다. **최초 신고 하드 실패가 수정본에서 해소됨을 확정.** |

#### S-10: 릴리즈 자산 부재 시 무중단 폴백

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 3경로 공통 폴백 분기 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 릴리즈 자산이 없는 태그 지정(실행 전 자산 유무 실제 확인), 대화형 + 진행 동의 |
| 기대 결과 | 설치가 **중단되지 않고** 자동 아카이브로 완료. 폴백 사유가 로그에 명시됨 |
| 도구 | 실 스크립트 실행 |
| 실행 명령 | `expect -f "$W/s10.exp"` — pty를 띄워 `DL_DENY_PAT='releases/download/.*/sha256sums\.txt'` 하에 `install.sh`를 실행하고 프롬프트에 `y` 응답 (TEST.md §2.2c) |
| 결과 | **Pass** |
| 상세 | **자산 유무 사전 확인**: 릴리즈 목록 API 조회 결과 v0.6.0~v0.6.11 전 태그가 자산 2개를 보유하고, 유일하게 자산 0인 v0.5.0은 루트에 `VERSION`이 없어 규약과 무관한 사후조건 실패를 유발한다. 따라서 PLAN §3.6.2 2안(시스템 설정 변경 없는 PATH 스텁)으로 v0.6.11의 `sha256sums.txt`만 404 처리했다. **결과**: `WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)` → `tarball URL: …/archive/refs/tags/v0.6.11.tar.gz` → 프롬프트 `[y/N] y` → `WARN: [UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행` → `추출 중... (strip-components=1)` → `추출 완료` → `VERSION 각인값 채택: v0.6.11` → 인스톨러 도달, **exit 0**. 중단 없음 + 폴백 사유 명시 1건. |

#### S-11: 비대화형 + 자산 부재 → 거부 (fail-closed 보존)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-8 |
| 대상 | UNVERIFIED 3분기 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | S-10과 동일 태그 + 비대화형 stdin, `OPAL_ALLOW_UNVERIFIED` 미지정 |
| 기대 결과 | exit≠0 + 옵트인 안내 출력. `OPAL_ALLOW_UNVERIFIED=1` 지정 시에는 경고 후 진행 |
| 도구 | 실 스크립트 실행 |
| 실행 명령 | `… DL_DENY_PAT='releases/download/.*/sha256sums\.txt' OPAL_VERSION=v0.6.11 /bin/bash scripts/install.sh < /dev/null` (옵트인 없음 / 있음 2회) + `update.sh` 동일 2회 (TEST.md §2.2a·2.2b, §2.5a·2.5b) |
| 결과 | **Pass** |
| 상세 | **install.sh** — 옵트인 미지정: `ERROR: 릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1` **exit 1**, INSTALLER_LOG 0줄. `OPAL_ALLOW_UNVERIFIED=1`: `WARN: [UNVERIFIED] … 무결성 검증 없이 진행` 후 strip=1 추출·인스톨러 도달 **exit 0**. **update.sh** — 옵트인 미지정: `ERROR: … 비대화형 모드에서 무결성 검증 없는 업데이트를 거부합니다.` **exit 1**. 옵트인 지정: `✓ 업데이트 완료 (v0.6.11)` **exit 0**. fail-closed(R-2·GC-001·H-8) 3경로 중 bash 2경로 실증 완료. |

#### S-12: 폴백 시 잘못된 비교 금지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 폴백 경로의 체크섬 정책 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | sha256sums.txt는 받았으나 tarball 자산 다운로드가 실패해 폴백한 상황 |
| 기대 결과 | 로그에 체크섬 불일치 오류가 **부재**. 받아둔 sha 파일이 비교에 사용되지 않고 UNVERIFIED 경로로 수렴 |
| 도구 | 실 스크립트 실행 + 로그 검사 |
| 실행 명령 | 조건 정합 실행 — `DL_DENY_PAT='releases/download/v0\.6\.11/opal-v0\.6\.11\.tar\.gz'`(sha256sums.txt는 **정상 수신**, 자산 tarball만 실패) 로 `install.sh` 실행 후 로그 전문 검사 (TEST.md §2.2d(c)). 보조로 S-10 로그도 동일 검사 |
| 결과 | **Pass** |
| 상세 | 시나리오 조건 그대로 재현: `체크섬 파일 확인 중: …/sha256sums.txt`(200 수신) → `tarball 다운로드 중...` → `curl: (22) 404` → `WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패` → `폴백 tarball URL: …/archive/refs/tags/v0.6.11.tar.gz` → `WARN: [UNVERIFIED] …` → `추출 중... (strip-components=1)`. **로그 검사**: `체크섬 불일치\|FAILED\|검증 실패` **0건**, `SHA-256 검증 중` **0건** → 받아둔 sha 파일이 비교에 사용되지 않고 UNVERIFIED로 수렴. 코드 근거: `_dl_fallback`이 `rm -f "${OPAL_SHA_FILE}"` 후 `OPAL_SHA_FILE=""`. H-3(현 결함) 재현 없음. |

#### S-13: 추출 사후조건 — 두 아카이브 형식

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | 3경로 추출부 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | ① 발행 자산(prefix 없음) ② 자동 아카이브(prefix 있음) 각각 추출 |
| 기대 결과 | 양쪽 모두 추출 루트에 `VERSION`·`opal/` 존재. 추출 후 읽은 `VERSION` 각인값이 `v0.6.11` |
| 도구 | 실 스크립트 실행 |
| 실행 명령 | ① 실 스크립트 경로: S-7(발행 자산, strip 0)·S-11b(자동 아카이브, strip 1) 실행 로그 ② 직접 대조: `tar -xzf opal-v0.6.11.tar.gz -C ex-0` / `tar -xzf v0.6.11-archive.tar.gz -C ex-1 --strip-components=1` 후 루트 검사 ③ `bash scripts/tests/test_download_contract.sh` (TC-B1·B2·B3) (TEST.md §4.5) |
| 결과 | **Pass** |
| 상세 | 직접 대조: `opal-v0.6.11.tar.gz strip=0 VERSION=O opal/=O VERSION내용=[v0.6.11]` / `v0.6.11-archive.tar.gz strip=1 VERSION=O opal/=O VERSION내용=[v0.6.11]`. 실 스크립트 경로에서도 양 형식 모두 `추출 완료` 후 `tarball VERSION 각인값 채택: v0.6.11 (API 미사용)` 출력 — `adopt_stamped_version`이 추출 루트의 `VERSION`을 읽어 `v0.6.11`을 얻었다는 증거. 사후조건 위반 아카이브에는 하드 실패(TC-B3 exit≠0)로 조용한 진행 없음. |

#### S-14: main 브랜치 회귀 무변경

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 브랜치 설치 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `OPAL_VERSION=main` 설치 |
| 기대 결과 | 기존과 동일하게 UNVERIFIED 배너 출력 후 완료. 배너 문구·위치 무변경, 추출 구조 동일 |
| 도구 | 실 스크립트 실행 + 변경 전후 출력 대조 |
| 실행 명령 | `… OPAL_VERSION=main /bin/bash scripts/install.sh < /dev/null` 및 `… /bin/bash opal/tools/opal-cli/run.sh update --to main --force`. 배너 대조: `git show HEAD:<f> \| grep -n 'UNVERIFIED.*브랜치'` ↔ `grep -n 'UNVERIFIED.*브랜치' <f>` (TEST.md §2.3·§2.6) |
| 결과 | **Pass** |
| 상세 | **install.sh**: `WARN: [UNVERIFIED] 'main' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다.` → `tarball URL: …/archive/refs/heads/main.tar.gz`(RG-1 URL 무변경) → `브랜치 설치 — SHA-256 무결성 검증 대상 아님` → `추출 중... (strip-components=1)` → **exit 0**. 네트워크 **1건**뿐 — 브랜치 경로는 `sha256sums.txt`를 조회조차 하지 않는다. **update.sh**: `--to main --force` → 동일 URL → `[UNVERIFIED] 'main' 브랜치 업데이트 …` → strip 1 추출 → **exit 0**, 네트워크 1건. **배너 대조**: 두 파일 모두 문자열 **완전 동일**(install.sh HEAD:371 ↔ WT:507, update.sh HEAD:169 ↔ WT:273). 상대 위치도 동일 — install.sh는 `main()` 안 DRY-RUN 경고 직후·`detect_platform` 직전, update.sh는 `✓ 다운로드 완료` 직후. 실측 출력 순서가 HEAD와 일치. 추출 구조(strip 1 → `VERSION`·`opal/`) 동일. |

#### S-15: DRY-RUN 네트워크 무접근 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `install.sh` DRY-RUN, `update.sh --dry-run` |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `OPAL_DRY_RUN=1 bash scripts/install.sh` / `opal-cli update --dry-run` |
| 기대 결과 | 흐름 검증 출력 후 종료, **네트워크 접근 0회**(자산 존재 판정이 DRY-RUN에서 조기 반환됨) |
| 도구 | 실 스크립트 실행 + 네트워크 차단 환경 대조 |
| 실행 명령 | 모든 `curl` 호출 URL을 기록하는 PATH 스텁을 걸고 4회 실행 — `OPAL_DRY_RUN=1 /bin/bash scripts/install.sh` / `OPAL_DRY_RUN=1 OPAL_VERSION=v0.6.11 …` / `run.sh update --dry-run --to v0.6.11` / `run.sh update --dry-run` (TEST.md §2.3b) |
| 결과 | **Pass** |
| 상세 | ① install.sh DRY-RUN(버전 미지정) — 네트워크 **0건**, `[DRY-RUN] resolve_download_plan 생략 — 네트워크 조회 없음` → fetch/verify/extract/installer 전부 생략 → `[DRY-RUN] 흐름 검증 완료`, exit 0 (RG-7) ② install.sh DRY-RUN + `v0.6.11` — **0건** ③ `update --dry-run --to v0.6.11` — **0건**, `[dry-run] 다운로드 소스: releases/download/v0.6.11/<sha256sums.txt 파생 자산명> …`, exit 0 (RG-8: `_dl_resolve_plan` 이전 종료) ④ `update --dry-run`(버전 미지정) — **1건**(`api.github.com/…/releases/latest`). ④의 1건은 latest 태그 조회로 `_dl_resolve_plan` **이전**의 사전존재 동작이며 HEAD도 동일 위치에서 동일 호출을 한다 → 회귀 아님. 관측: ②에서 DRY-RUN 안내 URL이 `archive/refs/heads/v0.6.11.tar.gz`로 표시된다(HEAD는 `refs/tags/…`) — 표시 전용 경미 회귀, TEST.md §5 O-1로 보고. |

#### S-19: 폴백 진입 4경로 완전성

> 게이트 통과 후 Evaluator 권고(SCENARIO-GATE-1.md advisory 3)를 반영해 추가했다. 폴백 진입 경로 중 (b)·(d)가 기대 결과로 명시되지 않았다는 지적에 대응한다.

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-3 |
| 대상 | 3경로 공통 `resolve_download_plan` / `fetch_tarball` 폴백 분기 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 폴백 진입 4경로를 각각 유발 — (a) sha256sums.txt 다운로드 실패 (b) sha 파일은 받았으나 `.tar.gz` 항목 파싱 결과 공백 (c) 릴리즈 자산 tarball 다운로드 실패 (d) 폴백 후 자동 아카이브 다운로드마저 실패 |
| 기대 결과 | (a)(b)(c) 전부 폴백 강등 후 UNVERIFIED 정책으로 수렴(중단 없음). **(d)는 하드 실패**(exit≠0) — 무한 폴백·무음 진행 없음 |
| 도구 | 실 스크립트 실행 + 픽스처·네트워크 차단 주입 |
| 실행 명령 | `install.sh` 4회 — (a) `DL_DENY_PAT='releases/download/.*/sha256sums\.txt'` (b) `DL_OVERRIDE=<.tar.gz 항목 없는 sha 파일>` (c) `DL_DENY_PAT='…/opal-v0\.6\.11\.tar\.gz'` (d) `DL_DENY_PAT='…/opal-v0\.6\.11\.tar\.gz\|archive/refs/tags/v0\.6\.11\.tar\.gz'`, 전부 `OPAL_ALLOW_UNVERIFIED=1`. `update.sh`도 (a)(b·옵트인)(d) 3회 (TEST.md §2.2d·§2.5) |
| 결과 | **Pass** |
| 상세 | **install.sh 4/4**: (a) exit **0** / 사유 `릴리즈 자산 없음 (sha256sums.txt 조회 실패)` (b) exit **0** / 사유 `sha256sums.txt 형식 이상 (.tar.gz 항목 없음)` (c) exit **0** / 사유 `릴리즈 자산 다운로드 실패` — 폴백 후 재다운로드 성공, (d) exit **1** — `폴백 다운로드 URL … curl: (22) 404` → `ERROR: tarball 다운로드 실패` **하드 실패**, 무한 폴백·무음 진행 없음. 4경로 전부에서 `SHA-256 검증 중\|체크섬 불일치\|FAILED` **0건**. **update.sh**: (a) 비대화형 거부 exit 1 / (a+옵트인) exit 0 UNVERIFIED 수렴 / (d) exit 1 하드 실패. **미실행 1분기**: `update.sh` × 대화형 프롬프트 `y` 동의(pty). 동일 3분기 코드형을 `install.sh`에서 pty로 실증했고(S-10) update.sh는 옵트인·거부 2분기를 실증했다 — 사유: 대표 실증으로 갈음, 추정 기재 없음. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-16: `install.ps1` Windows 실측 설치 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `scripts/install.ps1` 릴리즈 태그 설치 전 경로 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. Windows 환경 확보 시 M1 자동 실행으로 승격 가능 |
| 조건 | Windows + PowerShell 5.1 이상, v0.6.11 지정 설치 |
| 기대 결과 | "체크섬 검증 통과" 출력 후 설치 완료. 현행의 예외 중단이 재현되지 않음 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Skip (미실행 — PM/캡틴 반환)** — 캡틴 실측 회신 시 이 칸을 Pass/Fail로 갱신 |
| 상세 | opal-test-agent는 L3 [SUPERVISOR] 시나리오를 실행하지 않는다. 더불어 실행 환경이 macOS이고 `pwsh`·`powershell` 모두 미설치(`command -v` 결과 `MISSING`)여서 자동 승격도 불가하다. TEST-SCENARIO.md §S-16 "미보유 시 대체 경로"와 PLAN §3.6.2에 따라 **사유 + 대체 검증 3종**을 `TEST.md` §3.1~§3.4에 기재했다 — ① PowerShell 구문 파싱 미수행 사유(파서 부재, 추정 금지) ② `Get-DlStripComponents`·`Get-DlAssetName` 판정식을 실 입력에 적용한 등가 대조(`0/1/1`, 자산명 4입력 일치 — **런타임 미검증** 명시) ③ bash↔PowerShell 규약 10항목 대조표(7항목 완전 일치, #5 폴백 로그 문구만 미세 드리프트). **Pass로 기록하지 않았다.** |

> **PM 요청 양식 (캡틴 대상)**
> - 요청 내용: Windows 환경에서 `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)` 기반 v0.6.11 설치 1회 실행
> - 확인 항목: ① "체크섬 검증 통과" 출력 여부 ② exit 정상 종료 여부 ③ 설치 후 `~/.opal/VERSION`이 `v0.6.11`인지
> - 회신 형식: 출력 전문 붙여넣기 또는 스크린샷
> - **미보유 시 대체 경로**: Windows 환경이 없으면 이 시나리오를 Skip 처리하고, TEST.md에 사유 + 대체 검증 3종(PowerShell 구문 파싱 / `Get-DlStripComponents`·`Get-DlAssetName` 단위 판정 / bash↔PowerShell 규약 대조표)을 기재한다. AC가 이를 허용한다.

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC (신형 채택) | H-2·H-3·H-6·H-10 | L2 | S-9 | `TEST.md`:[T085/L2-F1-verify] | **목표달성 시나리오** — 캡틴 신고 실패의 해소 확인 |
| F-1 AC (구형 잔존 0) | H-4 | L1 | S-3 | `TEST.md`:[T085/L1-F1-residual] | 릴리즈 태그 경로 자동 아카이브 URL 0건 |
| F-1 AC (무음 통과 제거) | H-10 | L1 | S-5 | `TEST.md`:[T085/L1-F1-silentpass] | PLAN 추가 발견 결함 |
| F-2 AC (검증 통과) | H-4 | L2 | S-7 | `TEST.md`:[T085/L2-F2-verify] | — |
| F-2 AC (스킵 경고 0건) | H-9 | L1+L2 | S-3, S-7 | `TEST.md`:[T085/L1-F2-grep] | 고정문자열 매칭 전환 확인 |
| F-2 AC (손상 거부) | H-10 | L2 | S-8 | `TEST.md`:[T085/L2-F2-corrupt] | 보안 시나리오 |
| F-3 AC (Windows 설치 완료) | H-7 | L3 | S-16 | `TEST.md`:[T085/L3-F3-win] | 환경 부재 시 사유+대체 검증 허용 |
| F-4 AC (무중단 폴백) | H-1 | L2 | S-10 | `TEST.md`:[T085/L2-F4-fallback] | — |
| F-4 AC (비대화형 거부) | H-1·H-8 | L2 | S-11 | `TEST.md`:[T085/L2-F4-noninteractive] | fail-closed 보존 |
| F-4 AC (잘못된 비교 금지) | H-3 | L2 | S-12 | `TEST.md`:[T085/L2-F4-nocompare] | 현 결함 재현 방지 |
| F-5 AC (두 형식 추출) | H-2 | L1+L2 | S-1, S-13 | `TEST.md`:[T085/L1-F5-strip] | 판정 단위 + 실추출 |
| F-6 AC (9칸 증거) | H-7 | L1 | S-17 | `TEST.md`:[T085/L1-F6-matrix] | 산출물 완결성 |
| 회귀 (main 무변경) | H-5 | L2 | S-14 | `TEST.md`:[T085/L2-RG-main] | RG-1·RG-2·RG-3 |
| 회귀 (DRY-RUN) | H-1 | L2 | S-15 | `TEST.md`:[T085/L2-RG-dryrun] | RG-7·RG-8 |
| 보조 (자산명 파생) | H-3 | L1 | S-2 | `TEST.md`:[T085/L1-assetname] | 규약 D-B 전제 |
| 보조 (해시 도구 이식성) | H-6 | L1 | S-6 | `TEST.md`:[T085/L1-sha-portable] | — |
| 보조 (구문 무결성) | H-7 | L1 | S-4 | `TEST.md`:[T085/L1-syntax] | — |
| 보강 (PowerShell 런타임 등가) | H-7 | L1 | S-18 | `TEST.md`:[T085/L1-ps-runtime] | 게이트 후 추가 — Windows 없이 H-7 회수 (`pwsh` 확보 시) |
| 보강 (폴백 4경로 완전성) | H-1·H-3 | L2 | S-19 | `TEST.md`:[T085/L2-fallback-paths] | 게이트 후 추가 — (d) 재다운로드 실패는 하드 실패 |

> TASK.md 요구사항 F-1~F-6 전부가 매핑되었고, 가설 H-1~H-10 전부가 최소 1개 시나리오에 연결되었다. 미매핑 시나리오 없음.
> FE 화면·인증/인가·외부 API 연동 변경이 없으므로 M2(E2E 자동화) 의무 트리거는 발동하지 않는다.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `shellcheck` 0.11.0 | **Pass** | `shellcheck -S error` → **2파일 모두 exit 0, error 레벨 0건**. 전체 레벨은 각 1건 note `[SC2016] Expressions don't expand in single quotes`(`install.sh:488`, `update.sh:361` — `'$Format:'` 리터럴 판별로 **의도된 코드**). HEAD 기준선 대조 결과 HEAD도 동일 1건씩(`install.sh:352`, `update.sh:222`) → **신규 지적 0건**. `install.ps1`은 PSScriptAnalyzer 미가용으로 미실행. |
| 2 | 타입 체크 | 해당 없음 (셸·PowerShell) | **N/A** | 정적 타입 시스템 부재 — 검사 대상 아님. |
| 3 | 포맷터 | 해당 없음 | **N/A** | 프로젝트에 셸 포맷터(shfmt 등) 설정 없음. |
| 4 | 구문 검사 | `bash -n` × 2, PowerShell 파싱 × 1 | **Pass (PS는 Skip)** | `bash -n scripts/install.sh` exit 0, `bash -n opal/tools/opal-cli/lib/update.sh` exit 0. PowerShell 파싱은 **Skip** — `pwsh`·`powershell` 미설치(`command -v` → `MISSING`). 파서 없이 통과를 주장하지 않는다. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | `grep -nEi 'api[_-]?key\|secret\|passwd\|password\|PRIVATE KEY\|ghp_\|github_pat_\|AKIA[0-9A-Z]{16}\|Bearer '` → 3파일 **각 0건**. 인증 토큰을 요구하는 호출 없음(전부 공개 릴리즈 자산 익명 GET). |
| 2 | .gitignore 확인 | **Pass** | `.gitignore`에 `.opal/*`(2행)·`.env`(25행) 존재. `git status --short` = 변경 3파일 + 신규 테스트 1 + 태스크 폴더뿐 — 민감 파일 추적 없음. 검증 픽스처·로그·스텁은 전부 스크래치패드(`$W`)에 생성했고 저장소에 남기지 않았다. |
| 3 | 무결성 검증 우회 경로 신규 0건 (`verify` 모드에 skip/warn-continue 분기 부재) | **Pass** | `grep -cE '검증 건너\|graceful skip'` → 3파일 각 **0건**. `verify` 분기 내 `return 0`(하드 실패 아닌 통과) → install.sh **0건** / update.sh **0건**. 계약 3종 밖 모드값은 bash `*)`·PowerShell `default {}`에서 **하드 실패**(fail-closed, D-6). 실증: 항목 부재·빈 기대값·손상 tarball 3종 전부 exit≠0 (S-5·S-8). |
| 4 | 비대화형 기본 거부(fail-closed) 유지 | **Pass** | 3파일 모두 옵트인 / 비대화형 거부 / 프롬프트 기본 N 3분기 유지(bash `! -t 0 \|\| OPAL_AUTO_INSTALL=1`, PS `-not [Environment]::UserInteractive -or OPAL_AUTO_INSTALL=1`). **실행 증거 2건** — install.sh 비대화형 exit 1(S-11), update.sh 비대화형 exit 1(S-19a). 옵트인 지정 시에만 exit 0. |
| 5 | 신규 다운로드 전부에 `--proto '=https' --tlsv1.2` / TLS 강제 적용 | **Pass (관측 1건)** | `install.sh` curl 5개소(`:89 :95 :254 :299 :315`)·`update.sh` curl 5개소(`:98 :179 :185 :252 :258`) **전부** `--proto '=https' --tlsv1.2` 동반. `install.ps1`은 `Set-DlSecurityProtocol`(Tls12, 가용 시 Tls13 bor)을 `Resolve-DownloadPlan:239`·`Fetch-Tarball:317`에서 다운로드 직전 호출 — HEAD의 무조건 `Tls12 -bor Tls13` 대비 .NET<4.8 환경 즉시 throw 결함이 제거된 **개선**. 관측: `install.ps1 Resolve-DefaultVersion`(`:77 :83`) API 호출에는 TLS 설정이 선행하지 않으나 **HEAD 동일(사전존재)**, 본 태스크 신규 도입 아님. |

## 7. 판정

**All Pass -- 실행 가능한 6칸(3경로×3조합 중 `install.ps1` 행 제외)과 L1/L2 시나리오 16건이 실 데이터·실 프로세스로 전부 Pass, 실패 0건. 계약 테스트 26/26 PASS. 목표달성 시나리오 S-9는 구형 코드의 하드 실패 재현(`기대값 1ae94e27… / 실제값 463a5842…`, exit 1)과 수정본의 성공(exit 0, `체크섬 검증 완료`)을 동일 명령·동일 환경에서 대조해 해소를 확정했다. 미실행은 S-16·S-18 2건(Skip)이며 둘 다 Windows·`pwsh` 부재가 사유로, TEST-SCENARIO.md §S-16 대체 경로와 PLAN §3.6.2가 허용하는 "사유 + 대체 검증 3종" 형식으로 `TEST.md` §3에 기재했다. 코드 품질은 HEAD 대비 신규 지적 0건, 보안 5항목 전부 Pass. 단, 아래 2건을 PM 확인 사항으로 함께 반환한다 — ① S-16은 [SUPERVISOR] 시나리오로 캡틴의 Windows 실측 회신이 남아 있다 ② 고치지 않은 관측 6건(O-1~O-6, `TEST.md` §5). 그중 O-1(DRY-RUN 안내 URL이 릴리즈 태그에서도 `archive/refs/heads/…`로 표시 — HEAD는 `refs/tags/…`)은 표시 전용이지만 경미한 회귀이므로 후속 판단이 필요하다.**

### PM Gate 체크 (7대 강제 룰)

- [x] 대역 객체·가짜 응답 지시가 시나리오 본문에 부재 (실 데이터·실 프로세스만 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 → M2 의무 트리거 미발동 (해당 없음)
- [x] **목표 커버** — TASK.md 요구사항 F-1~F-6 전체가 §4에 커버되고, 태스크 목표를 직접 검증하는 목표달성 시나리오(S-9)가 §3 L2에 존재

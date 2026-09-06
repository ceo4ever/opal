# RED EVIDENCE — 085 릴리즈 체크섬 검증 경로 정합

> 작성일: 2026-08-07 | 작성자: opal-test-agent (mode: red) | 트랙: RED-first
> 규칙 SSOT: `opal/core/references/harness/red-first.md` (§1 RED→GREEN, §2 작성자≠구현자, §3 테스트 불변성, §4 공개 인터페이스)
> 시나리오 SSOT: `TEST-SCENARIO.md` §3 (S-1·S-2·S-3·S-5·S-6·S-13)
> 설계 SSOT: `PLAN.md` §3.0 DL-CONTRACT (D-B~D-F), §3.1.2, §3.2.2

---

## 1. 산출물

| 항목 | 값 |
|------|-----|
| 테스트 파일 | `scripts/tests/test_download_contract.sh` (신규, 실행 권한 부여) |
| 케이스 수 | 26 |
| 커버 시나리오 | S-1, S-2, S-3, S-5, S-6, S-13 (L1 자동화 가능 범위) |
| 대상 파일 수정 | **0건** — `install.sh` / `install.ps1` / `update.sh` / `release.yml` 미변경 (git status 확인) |
| 네트워크 접근 | **0회** — 아카이브 픽스처는 `git archive`로 로컬 생성 |

---

## 2. 실행 명령 · 결과

```bash
bash scripts/tests/test_download_contract.sh
```

| 항목 | 값 |
|------|-----|
| exit code | **1** |
| PASS | 2 |
| **FAIL** | **24** |
| SKIP | 0 |
| verdict | `FAIL (24 failures)` |

**[MUST] RED 성립**: exit code ≠ 0 (=1). 미구현 상태에서 계약이 실패함을 실행 출력으로 입증했다.

---

## 3. 케이스별 집계

### (가) 헬퍼 함수 계약 — TC-A* (S-1 / S-2 / S-6)

| 케이스 | 시나리오 | 판정 | 실패 사유 |
|--------|---------|------|----------|
| TC-A1 | S-1/S-2/S-6 | FAIL | 헬퍼 7종 전부 미정의 (update.sh 4종 + install.sh 3종) |
| TC-A2 | S-1 | FAIL | `update.sh`에 `_dl_detect_strip` 없음 |
| TC-A3 | S-1 | FAIL | `install.sh`에 `_dl_detect_strip` 없음 |
| TC-A4 | S-1 / D-A | FAIL | 양쪽 미정의 — 본문 동일성 대조 불가 |
| TC-A5 | S-2 | FAIL | `update.sh`에 `_dl_asset_name` 없음 |
| TC-A6 | S-2 | FAIL | 동상 (binary mode `*` 접두 케이스) |
| TC-A7 | S-2 | FAIL | 동상 (항목 없는 파일 → 공백 케이스) |
| TC-A8 | S-2 | FAIL | `install.sh`에 `_dl_asset_name` 없음 |
| TC-A9 | S-2 / D-A | FAIL | 양쪽 미정의 |
| TC-A10 | S-6 | FAIL | `update.sh`에 `_dl_sha256` 없음 |
| TC-A11 | S-6 | FAIL | 동상 |
| TC-A12 | S-6 | FAIL | 동상 |

### (나) 추출 사후조건 · 체크섬 하드 실패 — TC-B* (S-13 / S-5)

| 케이스 | 시나리오 | 판정 | 실패 사유 |
|--------|---------|------|----------|
| TC-B1 | S-13 | FAIL | prefix 없는 아카이브에 `--strip-components=1` 고정 적용 → 추출 루트에 `VERSION`·`opal/` **둘 다 부재**. **현 결함의 정확한 재현** |
| TC-B2 | S-13 | **PASS** | prefix 있는 아카이브는 현행 고정 strip=1로도 정상 — 회귀 가드로 유지 (RG-2) |
| TC-B3 | S-13 | FAIL | 구조 위반 아카이브에서 exit 0 — 사후조건 검사 부재로 **조용한 진행** |
| TC-B4 | S-5 (양성대조) | FAIL | `verify_checksum`이 계약 전역(`OPAL_CHECKSUM_MODE`/`OPAL_SHA_FILE`/`OPAL_TARBALL_NAME`)이 아니라 `SHA_URL` 네트워크 경로에 결합 → `SHA_URL: unbound variable` |
| TC-B5 | S-5 | FAIL | 항목 부재 픽스처 주입 시 종료가 **계약 밖 하네스 오류**(unbound variable)로 발생 — 의도된 거부가 아님 |
| TC-B6 | S-5 | FAIL | 빈 해시 픽스처에서 동상 |
| TC-B7 | S-5 | FAIL | `verify_checksum` 본문에 `curl` 2건 + "검증 건너뜀"(경고 후 통과) 경로 2건 잔존 |
| TC-B8 | S-5 | FAIL | `update.sh`에 무음 통과 조건 `-n "$expected_sha"` 1건 잔존(H-10) / `grep -F` 0건(H-9) |

> **양성대조 설계 근거**: TC-B4가 통과하기 전에는 TC-B5·TC-B6의 exit≠0을 하드 실패 증거로 인정하지 않는다.
> `harness_error()` 가드가 `unbound variable` / `command not found` / `syntax error`를 감지하면 강제 FAIL 처리한다.
> reward hacking(우연한 오류로 인한 통과)을 차단하기 위한 장치다.

### (다) 구형 경로 잔존 0건 — TC-C* (S-3)

| 케이스 | 시나리오 | 판정 | 실패 사유 |
|--------|---------|------|----------|
| TC-C1 | S-3① | FAIL | `install.sh:180` `OPAL_TARBALL="${OPAL_TMP}/opal.tar.gz"` 1건 잔존 |
| TC-C2 | S-3② | FAIL | `install.sh:258` / `update.sh:181` — 변수 보간 + `-F` 부재 grep 2건 |
| TC-C3 | S-3③ | **PASS** | 코드 라인 기준 `archive/refs/tags` 3파일 각 1회 — 폴백 전용 유지 가드 |
| TC-C4 | S-3 (신형 채택) | FAIL | 3파일 모두 릴리즈 자산 tarball URL(`releases/download/…/{자산명}`) 구성 0건 |
| TC-C5 | S-3④ | FAIL | `install.sh:295` / `install.ps1:260` / `update.sh:211` — strip 판정값 미참조 고정 인자 |
| TC-C6 | S-3⑤ | FAIL | 3파일 헤더에 `DL-CONTRACT (085)` 각인 없음 |

---

## 4. 실행 출력 전문

```text
== (가) 헬퍼 함수 계약 (TC-A*, S-1·S-2·S-6) — RED 시점 FAIL 예상 ==

[FAIL] TC-A1 (S-1/S-2/S-6): DL-CONTRACT 헬퍼 정의 존재 (update.sh 4종 / install.sh 2종+계획함수)
       detail: 미정의: update.sh:_dl_sha256 update.sh:_dl_asset_name update.sh:_dl_detect_strip update.sh:_dl_resolve_plan install.sh:_dl_asset_name install.sh:_dl_detect_strip install.sh:resolve_download_plan
[FAIL] TC-A2 (S-1): update.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1
       detail: update.sh에 _dl_detect_strip 정의 없음
[FAIL] TC-A3 (S-1): install.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1
       detail: install.sh에 _dl_detect_strip 정의 없음
[FAIL] TC-A4 (S-1/D-A): install.sh·update.sh의 _dl_detect_strip 본문 동일
       detail: 한쪽 이상 미정의 (update.sh:X install.sh:X)
[FAIL] TC-A5 (S-2): update.sh _dl_asset_name(정상 sha256sums.txt) = opal-v0.6.11.tar.gz
       detail: update.sh에 _dl_asset_name 정의 없음
[FAIL] TC-A6 (S-2): update.sh _dl_asset_name(binary mode '*' 접두) = opal-v0.6.11.tar.gz
       detail: update.sh에 _dl_asset_name 정의 없음
[FAIL] TC-A7 (S-2): update.sh _dl_asset_name(.tar.gz 항목 없음) = 공백
       detail: update.sh에 _dl_asset_name 정의 없음
[FAIL] TC-A8 (S-2): install.sh _dl_asset_name 3입력 판정 (정상/binmode/항목없음)
       detail: install.sh에 _dl_asset_name 정의 없음
[FAIL] TC-A9 (S-2/D-A): install.sh·update.sh의 _dl_asset_name 본문 동일
       detail: 한쪽 이상 미정의 (update.sh:X install.sh:X)
[FAIL] TC-A10 (S-6): _dl_sha256 — sha256sum만 있는 PATH에서 기준 해시 반환
       detail: update.sh에 _dl_sha256 정의 없음
[FAIL] TC-A11 (S-6): _dl_sha256 — shasum만 있는 PATH에서 동일 해시 반환
       detail: update.sh에 _dl_sha256 정의 없음
[FAIL] TC-A12 (S-6): _dl_sha256 — 해시 도구 둘 다 없는 PATH에서 실패 반환(exit≠0, stdout 공백)
       detail: update.sh에 _dl_sha256 정의 없음

== (나) 추출·체크섬 행위 (TC-B*, S-13·S-5) — RED 시점 FAIL 예상 ==

[FAIL] TC-B1 (S-13): extract_to_tmp(prefix 없는 아카이브) → 루트에 VERSION·opal/ 존재
       detail: extract_dir='/var/folders/.../ex.VLa85t/opal-extracted' VERSION=X opal/=X | out='[opal] tarball 추출 중...
[opal] 추출 완료: /var/folders/.../ex.VLa85t/opal-extracted
EXTRACT_DIR=/var/folders/.../ex.VLa85t/opal-extracted'
[PASS] TC-B2 (S-13): extract_to_tmp(prefix 있는 자동 아카이브) → 루트에 VERSION·opal/ 존재
[FAIL] TC-B3 (S-13): extract_to_tmp(구조 위반 아카이브) → 하드 실패(exit≠0), 조용한 진행 금지
       detail: exit=0 — VERSION·opal/ 부재에도 통과했습니다 (사후조건 검사 부재) | out='[opal] tarball 추출 중...
[opal] 추출 완료: /var/folders/.../ex.l6yjvf/opal-extracted
EXTRACT_DIR=/var/folders/.../ex.l6yjvf/opal-extracted'
[FAIL] TC-B4 (S-5, 양성대조): verify_checksum(정상 sha256sums.txt 주입) → exit 0 + 검증 완료 출력
       detail: exit=1 msg=0 out='/var/folders/.../harness.57291.sh: line 19: SHA_URL: unbound variable' (verify_checksum이 OPAL_CHECKSUM_MODE/OPAL_SHA_FILE/OPAL_TARBALL_NAME 계약으로 구동되어야 함)
[FAIL] TC-B5 (S-5): verify_checksum(항목 부재 sha256sums.txt) → 하드 실패(exit≠0)
       detail: 계약 밖 하네스 오류로 종료 — 의도된 거부가 아님 | out='/var/folders/.../harness.57291.sh: line 19: SHA_URL: unbound variable'
[FAIL] TC-B6 (S-5): verify_checksum(빈 해시 sha256sums.txt) → 하드 실패(exit≠0)
       detail: 계약 밖 하네스 오류로 종료 — 의도된 거부가 아님 | out='/var/folders/.../harness.57291.sh: line 19: SHA_URL: unbound variable'
[FAIL] TC-B7 (S-5): install.sh verify_checksum 본문에 네트워크 호출·경고후통과 경로 부재
       detail: curl 호출 2건(다운로드는 resolve_download_plan 책임) / '검증 건너뜀' 경로 2건
[FAIL] TC-B8 (S-5): update.sh 체크섬 분기 — 빈 기대값 무음 통과 패턴 0건 + 고정문자열 매칭
       detail: 무음통과 조건('-n $expected_sha') 1건(기대 0) / 'grep -F' 0건(기대 ≥1)

== (다) 구형 잔존 정적 검사 (TC-C*, S-3) ==

[FAIL] TC-C1 (S-3①): install.sh에 'opal.tar.gz' 리터럴 0건
       detail: 1건 잔존 — 로컬 저장명이 발행 자산명으로 전환되지 않았습니다: 180:    OPAL_TARBALL="${OPAL_TMP}/opal.tar.gz"
[FAIL] TC-C2 (S-3②): 2개 bash 파일에 비고정문자열 grep 매칭(변수 보간 + -F 부재) 0건
       detail: 잔존:
install.sh: 258:    sha_entry="$(grep "${tarball_name}" "${sha_file}" 2>/dev/null || true)"
update.sh: 181:            expected_sha=$(grep "opal-${version}.tar.gz" "$sha_file" 2>/dev/null | awk '{print $1}') || true
[PASS] TC-C3 (S-3③): 3파일 각각 코드 라인의 'archive/refs/tags' 정확히 1회(폴백 분기 전용)
[FAIL] TC-C4 (S-3, 신형 채택): 3파일 각각 릴리즈 자산 tarball URL(releases/download, sha256sums.txt 아님) 구성 라인 ≥1
       detail: 기대 ≥1, 실제: install.sh=0 install.ps1=0 update.sh=0 — 릴리즈 자산이 다운로드 대상으로 채택되지 않았습니다
[FAIL] TC-C5 (S-3④): 3파일에 무조건 고정 '--strip-components' 0건 (판정값 참조가 12줄 이내 선행해야 함)
       detail: 판정값 미참조(고정) 잔존: install.sh:line(295) install.ps1:line(260) update.sh:line(211)
[FAIL] TC-C6 (S-3⑤): 3파일 헤더(첫 70줄)에 'DL-CONTRACT (085)' 각인 존재
       detail: 각인 누락: install.sh install.ps1 update.sh

========================================================
PASS: 2 | FAIL: 24 | SKIP: 0
========================================================
verdict: FAIL (24 failures)
```

> 출력 전문의 임시 경로(`/var/folders/fc/w424kvjn3mxfk6nyzkw_8b740000gn/T/tmp.ZAE629CPMc/…`)와 ANSI 색상 코드는 가독성을 위해 축약했다. 그 외 문자열은 실행 출력 그대로다.

---

## 5. 테스트 설계 판단 근거

### 5.1 헬퍼 로드 방식 — 함수 정의 구간 추출 후 하네스 source

대상 3파일은 실행 부수효과가 크다:

- `scripts/install.sh` — 최상위에서 `resolve_default_version()` 즉시 실행(GitHub API 호출) + 말미 `main "$@"` → `source` 불가.
- `opal/tools/opal-cli/lib/update.sh` — `cmd_update()` 전 경로가 네트워크 + `~/.opal` 파괴적 재설치.
- `scripts/install.ps1` — `pwsh` 미설치 환경 → 본 파일에서는 정적 검사만 수행(런타임 등가 검증은 S-18 별도).

따라서 `awk`로 **해당 함수 정의 구간만 추출**해 임시 하네스에 넣고 실행한다. 이 방식은 (a) 네트워크 0회 (b) 실사용 `~/.opal` 미오염 (c) 반환값·exit code·표준출력만 검증(red-first.md §4)을 동시에 만족한다.

### 5.2 픽스처 — 네트워크 없이 로컬 생성

| 픽스처 | 생성 방법 | 성격 |
|--------|----------|------|
| A1 | `git archive --format=tar.gz HEAD` | prefix 없음 = **발행 자산 등가**. 실측 루트 직속 6 / 최상위 세그먼트 13 — `TEST-SCENARIO.md` §2.1의 발행 자산 특성과 동일 |
| A2 | `git archive --prefix=opal-0.6.11/ …` | 자동 아카이브 등가 |
| A3 | `git archive --prefix=opal-main/ …` | main 아카이브 등가 |
| A4 | `tar -czf`(README.md만) | 사후조건 위반 — `VERSION`·`opal/` 부재 |
| `sha256sums.txt` 3종 | 실 릴리즈 포맷(`<64hex>  <파일명>`)으로 로컬 작성, 해시는 A1의 **실제 sha256** | 정상 / binary mode(`*` 접두) / 항목 부재 / 빈 해시 |

대역 객체·모의 라이브러리·가짜 응답은 사용하지 않았다 (`opal/core/PRINCIPLES.md` §4).

### 5.3 기대치 실현 가능성 사전 확인

기대 기준을 정하기 전에 실제 도구 동작을 실측했다 — 달성 불가능한 기대치를 심지 않기 위함이다.

| 확인 항목 | 실측 결과 |
|-----------|----------|
| `shasum -a 256 -c <정상> --ignore-missing` | `OK`, exit 0 |
| `shasum -a 256 -c <항목부재> --ignore-missing` | `no file was verified`, exit 1 |
| `shasum -a 256 -c <빈해시> --ignore-missing` | `no properly formatted SHA checksum lines found`, exit 1 |
| `git archive HEAD` 루트 구조 | 루트 직속 6 / 최상위 세그먼트 13 → 판정 규칙상 strip **0** |

### 5.4 커버 범위 밖 (본 파일에서 검증하지 않음)

| 시나리오 | 사유 |
|---------|------|
| S-4 (구문 무결성) | `bash -n` / `pwsh` 파싱 — TEST 단계 코드 품질 검사에서 수행 |
| S-7~S-12, S-14, S-15, S-19 | L2 — 실 네트워크·실 설치 필요. RED 단계 제약(네트워크 미사용)과 충돌 |
| S-16 | L3 `[SUPERVISOR]` — Windows 실측, 캡틴 담당 |
| S-17 | 산출물(TEST.md) 검사 — 구현 후에만 의미 (TEST-SCENARIO.md §0 예외) |
| S-18 | `pwsh` 런타임 등가 — `pwsh` 미설치. `install.ps1`은 TC-C3·C4·C5·C6 정적 검사로만 커버 |
| `update.sh` 체크섬 분기 행위 검증 | 해당 로직이 `cmd_update()` 내부 인라인이라 함수 추출 불가. TC-B8 정적 검사 + L2 S-9로 회수 |

---

## 6. 구현 워커(GREEN)가 반드시 만족시켜야 할 계약

### C-1. 헬퍼 정의 (TC-A1)

| 파일 | 필수 함수 |
|------|----------|
| `opal/tools/opal-cli/lib/update.sh` | `_dl_sha256` / `_dl_asset_name` / `_dl_detect_strip` / `_dl_resolve_plan` |
| `scripts/install.sh` | `_dl_asset_name` / `_dl_detect_strip` / `resolve_download_plan` |

top-level(`^name() {` 또는 `^function name {`)에 정의하고 닫는 `}`는 열 0에 둔다 — 추출기가 인식하는 형식이다.

### C-2. `_dl_detect_strip` (TC-A2·A3·A4)

- 인자 1개(tarball 경로) → 표준출력 `0` 또는 `1`, exit 0.
- prefix 없음 → `0`, tag prefix → `1`, main prefix → `1`.
- **두 bash 파일 본문이 문자 단위 동일**해야 한다 (PLAN §3.0 D-A 정합 수단 (a)).

### C-3. `_dl_asset_name` (TC-A5~A9)

- 인자 1개(sha 파일) → 첫 `.tar.gz` 파일명을 표준출력, exit 0.
- binary mode `*` 접두는 제거한다.
- `.tar.gz` 항목이 없으면 **공백 출력 + exit 0** (호출자가 폴백 판단).
- **두 bash 파일 본문이 문자 단위 동일**해야 한다.

### C-4. `_dl_sha256` (TC-A10~A12)

- `sha256sum`만 있는 PATH / `shasum`만 있는 PATH에서 **동일한 64자 해시**를 표준출력, exit 0.
- 둘 다 없으면 **exit≠0 + 표준출력 공백** (무음 통과 금지). 외부 의존은 `awk`까지만 허용.

### C-5. `extract_to_tmp` (TC-B1~B3, `scripts/install.sh`)

- 입력 전역: `OPAL_DRY_RUN` / `OPAL_TMP` / `OPAL_TARBALL`. 산출 전역: `OPAL_EXTRACT_DIR`.
- prefix 유무와 무관하게 추출 루트에 `VERSION`(파일)·`opal/`(디렉토리)이 존재해야 한다.
- 사후조건 위반 시 **exit≠0** — 조용한 진행 금지.

### C-6. `verify_checksum` (TC-B4~B7, `scripts/install.sh`)

- 입력 전역: `OPAL_DRY_RUN` / `OPAL_PLATFORM` / `OPAL_TMP` / `OPAL_TARBALL` / `OPAL_TARBALL_NAME` / `OPAL_SHA_FILE` / `OPAL_CHECKSUM_MODE`.
  **`SHA_URL` 등 네트워크 전역에 결합하지 않는다** — 다운로드는 `resolve_download_plan` 책임.
- 본문에 `curl` 0건, "검증 건너뜀" 계열 경고 후 통과 경로 0건.
- `OPAL_CHECKSUM_MODE=verify` + 정상 sha → exit 0 + `체크섬 검증 완료` 출력.
- 항목 부재 / 빈 해시 → **exit≠0** (하드 실패).

### C-7. `update.sh` 체크섬 분기 (TC-B8)

- `-n "$expected_sha"` 형태의 무음 통과 조건 **0건** (H-10).
- 항목 매칭에 `grep -F` 사용 **1건 이상** (H-9).

### C-8. 구형 경로 잔존 0건 (TC-C1~C6)

| # | 계약 |
|---|------|
| C-8-1 | `install.sh`에 `opal.tar.gz` 리터럴 **0건** |
| C-8-2 | 2개 bash 파일에 "변수 보간 + `-F` 부재" grep 라인 **0건** |
| C-8-3 | 3파일 각각 코드 라인 기준 `archive/refs/tags` **정확히 1회**(폴백 분기 전용, 주석 제외) |
| C-8-4 | 3파일 각각 `releases/download` 자산 tarball URL 구성 라인 **1건 이상**(sha256sums.txt 라인 제외) |
| C-8-5 | 모든 `--strip-components` 사용처는 12줄 이내에 `_dl_detect_strip` / `Get-DlStripComponents` / `strip_n` / `$strip` 참조가 선행해야 한다 |
| C-8-6 | 3파일 헤더(첫 70줄)에 `DL-CONTRACT (085)` 각인 (`DL-CONTRACT (task 085)` 표기도 허용) |

---

## 7. 불변성 선언 [MUST]

`red-first.md` §3에 따라 **`scripts/tests/test_download_contract.sh`는 GREEN·fix 루핑 중 수정 금지 대상**이다.
테스트 약화·삭제·기대치 완화로 통과를 유도하는 행위는 블로커로 처리한다.
기대 기준에 설계상 오류가 발견되면 코드 수정이 아니라 **PM 에스컬레이션**으로 처리한다.

---

## 변경이력

| 버전 | 일시 | 내용 |
|------|------|------|
| v1.0 | 2026-08-07 | 초기 작성 — RED 증거 확보 (opal-test-agent, mode: red) (085) |

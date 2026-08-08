# CONTRACT CROSSCHECK — 085 DL-CONTRACT 3경로 규약 정합 정적 대조 (S-5)

> 작성일: 2026-08-07 09:37 KST | 작성자: opal-task-agent (Step 4) | 단계: EXECUTE / PLAN §4.2 Step 4
> 규약 SSOT: `PLAN.md` §3.0 DL-CONTRACT (D-A~D-G)
> 대조 대상: `opal/tools/opal-cli/lib/update.sh` (v1.1) / `scripts/install.sh` (v1.6) / `scripts/install.ps1` (v1.1)
> 참조: `RED-EVIDENCE.md` §6 (GREEN 계약 C-1~C-8), `scripts/tests/test_download_contract.sh`

> ⚠️ **§0~§9 는 1회차(fix 반영 전) 기록이며 이력 보존용으로 그대로 둔다.**
> **현행 판정은 §10 「2회차 재판정」이 SSOT다.** 2회차 결과: **8항목 전부 일치 / 신규 회귀 0건 / Step 4 완료 기준 충족**.

---

# ────────── 1회차 (2026-08-07 09:37 KST, fix 5건 반영 전) ──────────

## 0. 결론

| 항목 | 결과 |
|------|------|
| 대조표 8항목 | **일치 6 / 부분일치 2** (4번·5번) |
| 정적 검사 4종 | **4종 전부 기대값 충족** |
| RED 계약 테스트 재실측 | `PASS 26 / FAIL 0 / SKIP 0` — `verdict: ALL PASS` |
| 발견 불일치 | **총 7건** (P2 3건 / P3 4건) + 사전존재 관측 2건 |
| 완료 기준 판정 | **조건부 미달** — 완료 기준이 "8행 전부 일치"이므로 D-3·D-4가 미해소 상태에서는 Step 4를 `[x]`로 닫을 수 없다. PM 판단 필요 |

**핵심 소견**: 발견된 불일치 중 **PowerShell 관련 4건(D-3·D-4·D-5·D-9)은 코드가 PLAN을 어긴 것이 아니라 PLAN §3.3.2 자체가 §3.0 D-A(3경로 문구·동작 동일)와 어긋난 것**이다. 구현 워커는 PLAN을 충실히 따랐으므로 되돌릴 대상은 Step 2가 아니라 **규약 문서(PLAN §3.3.2) 또는 규약 완화 승인**이다.

---

## 1. 대조표 8항목

### 1-1. 자산 존재 판정 신호 — `sha256sums.txt` 다운로드 성공 여부 단일 신호인가

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:96-101` — `releases/download/{v}/sha256sums.txt` curl 실패 → 즉시 `_dl_fallback`. HEAD 프로브·GitHub API 조회 0건 |
| `install.sh` | **일치** | `:248-263` — 동일 구조. `--fail`로 404를 실패로 승격 |
| `install.ps1` | **일치** | `:211-221` — `Invoke-RestMethod ... -ErrorAction Stop` + `catch { Set-DlFallback }` |

- 3경로 모두 판정용 추가 왕복 0회(D-B 충족). `install.sh:250`은 조회 URL을 사용자에게 노출하고 `update.sh`·`install.ps1`도 각각 로그를 남긴다.

### 1-2. 자산명 파생 — 하드코딩 없이 sha 파일 파일명 컬럼에서 파생, `*` 접두 제거

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:55-57` `_dl_asset_name` — `$2` 컬럼 → `sub(/^\*/,"",n)` → `/\.tar\.gz$/` 첫 항목 |
| `install.sh` | **일치** | `:189-191` — `update.sh:55-57`과 **바이트 단위 동일**(`diff` 무출력으로 실측 확인, D-A 정합수단 (a) 충족) |
| `install.ps1` | **일치** | `:144-151` `Get-DlAssetName` — `-split '\s+'` → `cols[1]` → `-replace '^\*',''` → `-like '*.tar.gz'`. 논리 등가 |

- 3경로 어디에도 `opal-{tag}.tar.gz` 형태의 **검증 대상 자산명 하드코딩 없음**. `update.sh:90`·`install.sh:242`·`install.ps1:194,203`의 `opal-{v}.tar.gz`는 브랜치 아카이브의 **로컬 저장명**이며 검증에 쓰이지 않는다.
- `install.ps1:144`은 PLAN §3.3.2 원안에 없던 `-ErrorAction SilentlyContinue`를 추가해, 파일 부재 시 throw 대신 `$null` 반환 → 폴백 유도. **PLAN보다 개선**(규약 D-C의 "공백이면 폴백"에 더 부합).

### 1-3. 로컬 저장명 = 발행 자산명 (verify 모드)

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:112` `_DL_NAME="$asset"` → `:251` `tarball_path="$tmp_dir/$_DL_NAME"` |
| `install.sh` | **일치** | `:274` `OPAL_TARBALL_NAME="${asset}"` → `:284` `OPAL_TARBALL="${OPAL_TMP}/${OPAL_TARBALL_NAME}"` |
| `install.ps1` | **일치** | `:231` `$script:DlName = $asset` → `:275` `$outFile = Join-Path $DestDir $script:DlName` |

- 구 결함(다운로드는 archive, 검증은 발행 자산 기준)의 원인이 3경로에서 모두 제거됐다. `install.sh`의 `opal.tar.gz` 리터럴 잔존 0건(정적 검사 ②).

### 1-4. 폴백 3동작 — URL 재지정 + 로컬명 분리(`-archive` 접미) + sha 파일 폐기

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `_dl_fallback :71-80` — `:76` URL=`archive/refs/tags/{v}.tar.gz` / `:77` `opal-{v}-archive.tar.gz` / `:72-75` sha 파일 `rm -f` + 변수 공백화 |
| `install.sh` | **일치** | `_dl_fallback :205-214` — `:210` / `:211` / `:206-209` 동일 3동작 |
| `install.ps1` | **부분일치 (→ D-3)** | `Set-DlFallback :154-177` — URL(`:165`)·로컬명(`:166`)·`DlShaFile=$null`(`:174`)은 충족. 그러나 **첫 폴백 경로(sha 다운로드 실패)에서 실제 파일 삭제가 동작하지 않는다** |

- 3경로 모두 폴백 시 `CHECKSUM_MODE=unverified` 강등(update.sh:78 / install.sh:212 / install.ps1:167) — H-3(sha 파일 비교 금지)은 **모드 강등만으로도** 보장된다. D-3은 파일 잔존 문제이며 비교에 재사용되지는 않는다.
- 폴백 1회 강등(재귀 금지)도 3경로 동일: `update.sh:253-265` / `install.sh:306-322` / `install.ps1:295-311` — 2차 실패는 전부 하드 실패.

### 1-5. 폴백 로그 문구 — 사유가 사용자에게 드러나는가

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:79` `warn "릴리즈 자산 미사용 폴백: ${3}"` — 사유 3종: `:99` `릴리즈 자산 없음 (sha256sums.txt 조회 실패)` / `:107` `sha256sums.txt 형식 이상 (.tar.gz 항목 없음)` / `:255` `릴리즈 자산 다운로드 실패` |
| `install.sh` | **일치** | `:213` 동일 형식 + 사유 3종 `:261` / `:269` / `:310` — `update.sh`와 문구 동일 |
| `install.ps1` | **부분일치 (→ D-4·D-5)** | `:176` 폴백 배너는 동일하나 사유 문자열이 축약(`:219` `릴리즈 자산 없음` / `:226` `sha256sums.txt 형식 이상`). 후속 `unverified`·`branch` 사용자 안내(`:373,379,382,390`)는 여전히 구 어휘 `sha256sums.txt 없음` 사용 |

- "사유가 드러나는가"라는 기능 요건은 3경로 충족. **D-A 정합수단 (a) "로그 문구를 3경로 동일하게 사용"** 기준으로는 `install.ps1`만 어긋난다.

### 1-6. 체크섬 3모드 — `verify` / `unverified` / `branch` 값 집합 동일, 각 분기 동작 동형

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `case "$_DL_MODE" :270-319` — `branch :271-274` / `verify :275-302` / `unverified :303-318`. 값 생산처 `:78,91,113` |
| `install.sh` | **일치** | `case "${OPAL_CHECKSUM_MODE}" :340-391` — `verify :341-369` / `unverified :370-386` / `branch :387-390`. 값 생산처 `:212,235,243,275` |
| `install.ps1` | **일치** | `switch ($script:DlMode) :338-397` — `verify :340-369` / `unverified :371-387` / `branch :389-391` + `default :393-396` fail-closed throw. 값 생산처 `:167,195,204,232` |

- **값 집합 3종 완전 일치**. 3경로 모두 verify 분기에 skip·warn-continue 우회 경로 **0건** (모든 이탈이 `error`/`return 1`/`throw`).
- `unverified` 3분기(옵트인 / 비대화형 거부 / 프롬프트 default N)도 3경로 동형: `update.sh:305-317` / `install.sh:372-385` / `install.ps1:372-386`. **fail-closed(H-8) 보존**.
- 다만 verify 분기의 **비교 수단은 3경로 3종**(→ D-1), bash 2경로에는 `default`/`*)` 분기 부재(→ D-6).

### 1-7. strip 판정식 — `루트 직속 0 AND 최상위 세그먼트 1종 → 1`

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:61-67` `_dl_detect_strip` — `print (root == 0 && n == 1) ? 1 : 0` |
| `install.sh` | **일치** | `:195-201` — `update.sh:61-67`과 **바이트 단위 동일**(`diff` 무출력 실측) |
| `install.ps1` | **일치** | `:257-259` — `if ($rootFiles.Count -eq 0 -and $tops.Count -eq 1) { return 1 } else { return 0 }`. 논리 등가, PLAN §3.0 D-D PowerShell 원안 그대로 |

- 고정 `--strip-components` 잔존 0건(정적 검사 ③). `install.ps1:429`는 `if ($strip -eq 1)` 내부에서만 인자를 추가하며, PLAN H-7이 요구한 **배열 splatting**(`:428-430`) 준수.
- 실패 시 동작만 비대칭: bash는 `|| true` → 빈 값 → strip 0 → 사후조건이 회수(`update.sh:325`, `install.sh:408`), PowerShell은 즉시 `throw`(`:251,254`). 둘 다 fail-closed이며 PLAN D-D가 명시한 설계 그대로 → **일치**로 판정.

### 1-8. 추출 사후조건 — `VERSION`·`opal/` 존재 검사 + 위반 시 하드 실패

| 경로 | 판정 | 근거 |
|------|------|------|
| `update.sh` | **일치** | `:339-342` — `[[ ! -f "$extract_dir/VERSION" \|\| ! -d "$extract_dir/opal" ]]` → `error` + `return 1` |
| `install.sh` | **일치** | `:420-422` — 동일 검사 → `error`(=`exit 1`) |
| `install.ps1` | **일치** | `:449-453` — `Test-Path VERSION` + `Test-Path opal` → `throw`. `tar` exit≠0을 관용 처리(`:442-446`)하되 **최종 판정은 사후조건**에 위임 (PLAN §3.3.2 "관용 조건을 사후조건으로 승격" 준수) |

- 3경로 모두 오류 메시지에 `strip=` 값을 포함해 진단 가능. "조용한 진행 금지" 충족.

---

## 2. 정적 검사 4종 결과

| # | 명령 | 기대 | 실측 | 판정 |
|---|------|------|------|------|
| ① | `grep -rn "archive/refs/tags" scripts/install.sh scripts/install.ps1 opal/tools/opal-cli/lib/update.sh` | 각 파일 폴백 분기 1회씩 | 코드 라인 각 1건 — `install.sh:210`(`_dl_fallback`) / `install.ps1:165`(`Set-DlFallback`) / `update.sh:76`(`_dl_fallback`). 그 외 3건(`install.sh:37`, `install.ps1:37`, `update.sh:21`)은 **변경이력 주석** | **PASS** |
| ② | `grep -rn "opal.tar.gz" scripts/install.sh` | 0건 | exit 1, 출력 없음 | **PASS** |
| ③ | `grep -rn "strip-components" <3파일>` | 조건부 분기 내부에만 | 실행 라인 3건 전부 조건부 내부 — `install.sh:412`(`if [[ "${strip_n}" -eq 1 ]]`) / `update.sh:328`(`if [[ "$strip_n" -eq 1 ]]`) / `install.ps1:429`(`if ($strip -eq 1)`). 나머지 5건은 로그·주석 문자열 | **PASS** |
| ④ | `grep -rn "DL-CONTRACT (085)" <3파일>` | 3파일 전부 존재 | `update.sh:25,27,30` / `install.sh:42,46,181` / `install.ps1:49,53` — 3파일 모두 **헤더 70줄 이내** 각인 존재 | **PASS** |

**보강 실측**

| 검사 | 결과 |
|------|------|
| `bash -n scripts/install.sh` | PASS |
| `bash -n opal/tools/opal-cli/lib/update.sh` | PASS |
| `pwsh` 구문 파싱 | **미실행** — `command -v pwsh` 부재. PLAN Step 2 완료 기준의 "pwsh 미설치 시 사유 기록" 적용. `install.ps1`은 본 문서 §4의 **코드 정독**과 TC-C3~C6 정적 검사로만 커버됨 |
| `_dl_asset_name` 본문 `diff`(update.sh ↔ install.sh) | **무출력 = 바이트 동일** (D-A 정합수단 (a), RED C-3) |
| `_dl_detect_strip` 본문 `diff`(update.sh ↔ install.sh) | **무출력 = 바이트 동일** (D-A 정합수단 (a), RED C-2) |
| `bash scripts/tests/test_download_contract.sh` | `PASS 26 / FAIL 0 / SKIP 0` — `verdict: ALL PASS` (독립 재실측) |
| `OPAL_DRY_RUN=1 bash scripts/install.sh` | 네트워크 접근 0, `[DRY-RUN] 흐름 검증 완료` 출력 확인 |

---

## 3. 회귀 보존 RG-1 ~ RG-8 (PLAN §3.0 D-E)

| # | 항목 | 판정 | 근거 |
|---|------|------|------|
| RG-1 | main 브랜치 URL `archive/refs/heads/{branch}.tar.gz` | **보존** | `update.sh:89` / `install.sh:241`(+DRY-RUN `:233`) / `install.ps1:202`(+DRY-RUN `:193`) — URL 형태 무변경 |
| RG-2 | main 브랜치 추출 strip=1 | **보존** | 판정식이 main 아카이브(단일 prefix)에 대해 1 반환. RED TC-B2 PASS로 회귀 가드 유지 |
| RG-3 | main 브랜치 UNVERIFIED 배너 위치·문구 | **보존** | `install.sh:497`·`install.ps1:508` 문구·위치(`main`/`Invoke-OpalInstall` 선두) 무변경. `update.sh:273`은 문구 완전 동일, 위치도 원본과 같이 **다운로드 직후**(원본 `:167-170` ↔ 현행 `:270-274`) 유지 |
| RG-4 | 릴리즈 태그 + sha 부재 시 3분기 | **보존** | `unverified` 모드로 원 코드 이식 — `install.sh:372-385`(원본 `:232-247`), `update.sh:305-317`, `install.ps1:372-386` |
| RG-5 | `install.sh` `OPAL_TARBALL` 참조 지점 | **보존** | 변수 유지·값만 변경. 현행 참조 `:127`(선언) `:284`(설정) `:311`(폴백 재설정) `:304,320`(curl) `:408,412,415`(추출) — 구 리터럴 경로 잔존 0건 |
| RG-6 | `install.ps1` `--exclude` 4종 | **보존** | `:430` `tasks/*`, `*/tasks/*`, `tasks`, `*/tasks` 4종 전부 유지. strip 인자와 독립 배열로 append |
| RG-7 | `install.sh` DRY-RUN 네트워크 0 | **보존** | `resolve_download_plan:232-238` 조기 반환 + `resolve_default_version:80-83` 조기 반환. 실측으로 확인 |
| RG-8 | `opal-cli update --dry-run` | **보존(형태 변경 → D-7)** | `update.sh:220-230` — `_dl_resolve_plan` **이전** 반환으로 신규 네트워크 0. 단 구 `info "다운로드 URL: ..."` 대신 소스 서술문 출력으로 형태가 바뀜 |

---

## 4. PowerShell 경로 단독 정독 판정 (RED 테스트 미커버 영역)

> RED 테스트는 bash 2파일만 행위 검증한다(`RED-EVIDENCE.md` §5.4 S-18). `install.ps1`은 TC-C3·C4·C5·C6 정적 문자열 검사만 받았다. 아래는 8항목을 **코드 정독**으로 판정한 결과다.

| 8항목 | ps1 판정 | 비고 |
|-------|---------|------|
| 1 존재 판정 신호 | 일치 | `:211-221` |
| 2 자산명 파생 | 일치 | `:144-151` |
| 3 로컬명=자산명 | 일치 | `:231,275` |
| 4 폴백 3동작 | **부분일치** | D-3 |
| 5 폴백 로그 문구 | **부분일치** | D-4·D-5 |
| 6 체크섬 3모드 | 일치 (+`default` fail-closed로 bash보다 강함) | `:338-397` |
| 7 strip 판정식 | 일치 | `:257-259` |
| 8 추출 사후조건 | 일치 | `:449-453` |

**PowerShell 특유 우려 지점 (실행 검증 불가 — Step 5 대체 검증 또는 S-16 캡틴 실측 대상)**

| # | 지점 | 내용 |
|---|------|------|
| PS-1 | `:209`, `:285` `[Net.SecurityProtocolType]::Tls13` | .NET Framework 4.8 미만(Windows PowerShell 5.1 구환경)에는 `Tls13` 열거 멤버가 없어 `$ErrorActionPreference='Stop'` 하에서 즉시 throw된다. 원본 `:153`에 이미 있던 패턴이라 **신규 결함은 아니나**, 이번 변경으로 **노출 지점이 1→2곳**이 되었고 그중 `:209`는 릴리즈 태그 설치의 **최초 관문**이다. 구환경에서는 폴백조차 타지 못하고 설치 전체가 중단된다 (→ D-9) |
| PS-2 | `:248` `& tar -tzf` in `try` | PS 5.1에서 네이티브 명령이 stderr에 쓰면 `NativeCommandError`가 발생할 수 있다. `catch`가 `throw`로 승격하므로 fail-closed지만, 정상 tarball에서도 tar 경고 1줄로 설치가 중단될 여지가 있다 |
| PS-3 | `:216` `Invoke-RestMethod -OutFile` (sha), `:289,303` (tarball) | `Invoke-WebRequest`가 아닌 `Invoke-RestMethod`로 바이너리를 받는 기존 패턴을 답습. 원본 동일 패턴이므로 회귀는 아니나, `Invoke-RestMethod`는 리다이렉트·콘텐츠 협상 동작이 `curl -L`과 다를 수 있어 **릴리즈 자산 URL(리다이렉트 필수)에서 최초로 검증되는 경로**다 → Step 5 실측 우선순위 상 |
| PS-4 | `:377` `[Environment]::UserInteractive` | `iex (irm ...)` 원라이너 실행 시에도 `$true`를 반환하는 것이 일반적이라, bash의 `[[ ! -t 0 ]]`(파이프 감지)과 **비대화형 판정 기준이 다르다**. `unverified` 모드에서 bash는 자동 거부, PowerShell은 프롬프트 대기가 될 수 있다. 사전존재 로직(PLAN §3.3.2가 이식 지시)이며 fail-closed 방향은 유지되나 UX·자동화 동작이 비동형 |
| PS-5 | `:72,78` `Resolve-DefaultVersion`의 API 호출 | `SecurityProtocol` 설정(`:209`/`:285`)보다 **먼저** 실행된다. 사전존재이며 이번 신규 다운로드(sha·tarball)는 전부 TLS 강제 선행을 충족 (→ D-8) |

---

## 5. 발견한 불일치 전건 (7건 + 관측 2건)

> **본 Step에는 수정 권한이 없다.** 전건 미수정으로 기록만 남긴다.

### D-1 (P2) — verify 분기의 해시 비교 수단이 3경로 3종

| 경로 | 방식 |
|------|------|
| `update.sh:277-301` | `grep -F` 부분문자열 매칭 → `awk '{print $1}'` → `_dl_sha256` 자체 계산 비교 |
| `install.sh:341-368` | `grep -F` **존재 확인만**, 실제 비교는 `shasum -a 256 -c sha256sums.txt --ignore-missing`(macOS) / `sha256sum -c ...`(Linux)에 위임. `:350` `expected_hash`는 **빈 기대값 하드 실패(H-10) 가드 전용**이며 비교에는 사용되지 않음 |
| `install.ps1:345-366` | 파일명 컬럼 **정확 일치**(`-eq`) 탐색 → `Get-FileHash` 비교 |

- PLAN §3.0 D-C 의사코드는 단일 동작(`entry → expected → actual → 비교`)을 지시했으나, PLAN §3.2.2(`:604-610`)가 `install.sh`에 한해 `shasum -c` 위임을 명시했다. **구현은 PLAN을 따랐고, 비동형은 PLAN 내부 불일치에서 발생**한다.
- 3경로 모두 fail-closed(불일치·부재·파싱실패 전부 하드 실패)이므로 **보안 구멍 아님**. 규약 동형성 관점의 드리프트.
- 부수 이식성: `--ignore-missing`은 Digest::SHA ≥6.00 / coreutils ≥8.25 필요. 본 머신 실측 `shasum 6.02` 지원 확인, 대상 파일 전무 시 `no file was verified` + exit 1(fail-closed) 확인. `update.sh`는 자체 비교라 이 의존이 없다.

### D-2 (P2) — bash 2경로의 `grep -F`는 부분문자열 매칭

- `update.sh:279` `grep -F -- "$_DL_NAME" "$_DL_SHA_FILE"`, `install.sh:344` 동일 형태.
- `sha256sums.txt`에 `opal-v0.6.11.tar.gz.sig` 같은 **상위문자열 항목이 먼저** 오면 그 줄의 해시가 기대값으로 채택돼 오탐 하드 실패가 난다. `install.ps1:351`은 컬럼 정확 일치라 영향 없음.
- 현행 `release.yml` 자산 구성(sha 파일 1행)에서는 미발현. fail-closed이므로 P2.
- 참고: RED 계약 C-7이 `grep -F` **사용**을 요구하므로, 개선하려면 `grep -F` 유지 + `awk` 컬럼 정확 일치 후단 필터를 덧붙이는 형태여야 한다(테스트 수정 불필요).

### D-3 (P2, PowerShell) — 폴백 3동작 중 'sha 파일 폐기'가 첫 폴백 경로에서 미동작

- `Resolve-DownloadPlan`은 `$script:DlShaFile = $shaFile`을 **다운로드 성공 이후**(`:222`)에 설정한다.
- sha 다운로드 실패 시 `catch`(`:218-221`)에서 `Set-DlFallback`이 호출되는데, 그 시점 `$script:DlShaFile`은 여전히 `$null`(`:105`)이므로 `:171`의 삭제 조건이 거짓 → **부분 수신된 `$shaFile`이 tmpDir에 잔존**한다.
- bash 2경로는 sha 경로 변수를 curl **이전에** 설정하므로(`update.sh:97`, `install.sh:249`) 정상 폐기된다.
- 실동작 위험은 낮다: 폴백 후 모드가 `unverified`로 강등되어 `Verify-Checksum`이 sha 파일을 읽지 않고, tmpDir는 `:528-539` `finally`에서 통째 삭제된다. 그러나 **대조표 4항(폴백 3동작) 규약 위반**이다.
- 원인은 PLAN §3.3.2 `:697`이 `$script:DlShaFile = $shaFile`을 verify 확정 직전에 두도록 지시한 데 있다. 구현은 이를 `:222`로 **앞당겨 두 번째 폴백(`:226` 형식 이상)은 이미 커버**했다 — PLAN보다 나은 상태이나 첫 폴백만 남았다.
- 제안(PM 판단): `:212` `$shaFile` 계산 직후로 `$script:DlShaFile = $shaFile` 이동 1줄. `Set-DlFallback`은 `Test-Path` 가드가 있어 부작용 없음.

### D-4 (P3) — 폴백 사유 문구 3경로 불일치

| 사유 | bash 2경로 | `install.ps1` |
|------|-----------|--------------|
| sha 조회 실패 | `릴리즈 자산 없음 (sha256sums.txt 조회 실패)` | `릴리즈 자산 없음` (`:219`) |
| 형식 이상 | `sha256sums.txt 형식 이상 (.tar.gz 항목 없음)` | `sha256sums.txt 형식 이상` (`:226`) |
| 자산 다운로드 실패 | `릴리즈 자산 다운로드 실패` | `릴리즈 자산 다운로드 실패` (`:299`) — 동일 |

- D-A 정합수단 (a) "로그 문구를 3경로 동일하게 사용" 위반. 축약형은 PLAN §3.3.2 `:692,694`가 그대로 지시한 값 → **PLAN 발원**.

### D-5 (P3) — `install.ps1`의 unverified·branch 사용자 안내가 구 어휘 유지

- `:373` `[UNVERIFIED] sha256sums.txt 없음 — OPAL_ALLOW_UNVERIFIED=1로 …`, `:379`, `:382` — bash 2경로는 전부 `릴리즈 자산 없음 — …`으로 갱신됨(`install.sh:373,378,381` / `update.sh:306,308,311`).
- 특히 `:390` `branch` 분기 `"[OPAL] sha256sums.txt 없음 (브랜치 설치) — 체크섬 검증 건너뜀"`은 **브랜치 경로에서 sha를 애초에 조회조차 하지 않으므로 사실과 다른 안내**다.
- PLAN §3.3.2 `:745`가 "`unverified`·`branch` 모드는 기존 `:190-211` 코드를 그대로 이식"이라 지시 → **PLAN 발원**.
- 대비: `install.sh`는 같은 branch 분기에서 PLAN §3.2.2 `:616`의 `"sha256sums.txt 없음 (브랜치 설치) — 체크섬 검증 건너뜀"`을 **의도적으로 이탈**해 `:389` `info "브랜치 설치 — SHA-256 무결성 검증 대상 아님"`으로 바꿨다. RED TC-B7이 `verify_checksum` 본문의 "검증 건너뜀" 계열 문자열 0건을 요구하기 때문이며, **정당한 이탈**이다. 결과적으로 branch 분기 문구가 3경로 3종이 되었다.

### D-6 (P3) — bash 2경로 체크섬 `case`에 `*)` 기본 분기 부재

- `install.ps1:393-396`은 `default { throw }`로 fail-closed. `install.sh:340-391`·`update.sh:270-319`의 `case`는 모드가 3값 밖이면 **무음 통과**한다.
- 현 호출 순서(`resolve_download_plan`이 항상 3값 중 하나를 설정)로는 도달 불가하나, "무음 스킵 금지" 규약과 어긋나며 향후 리팩터링 시 조용한 우회로가 된다.

### D-7 (P3) — RG-8 dry-run 출력 형태 변경

- 구: `info "다운로드 URL: $tarball_url"`을 dry-run에서도 출력(원본 `update.sh` 다운로드 URL 라인).
- 현: `:222` `[dry-run] 다운로드 소스: releases/download/${version}/<sha256sums.txt 파생 자산명> (자산 부재 시 자동 아카이브 폴백)`.
- 네트워크 0 유지·소스 안내라는 RG-8 취지는 충족. 자산명은 네트워크 없이 알 수 없으므로 **구체 URL 출력은 설계상 불가능**하다. 규약 위반이 아니라 RG-8 문언(`URL만 출력`)의 갱신이 필요한 사안.

### 관측 D-8 (사전존재) — `install.ps1` API 호출 2건에 TLS 강제 선행 없음

- `:72`, `:78` `Invoke-RestMethod`가 `[Net.ServicePointManager]::SecurityProtocol` 설정(`:209`/`:285`)보다 먼저 실행된다. v1.0.1부터 존재하며 이번 변경과 무관.
- **보안 계약 판정**: 이번에 추가된 신규 다운로드(sha `:216`, tarball `:289,303`)는 전부 TLS 강제 선행을 충족. bash 2경로의 신규 curl(`update.sh:98,252,258` / `install.sh:252-260,297-305,313-321`)도 전부 `--proto '=https' --tlsv1.2` 적용 확인 — **누락 0건**.

### 관측 D-9 (사전존재) — `Tls13` 열거 멤버 참조 확산

- §4 PS-1 참조. 원본 1곳(`:153`) → 현행 2곳(`:209`, `:285`). 신규 결함은 아니나 노출면 확대.

---

## 6. 보안 계약 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| 신규 다운로드 TLS 강제 | **충족** | bash: 신규 curl 6건 전부 `--proto '=https' --tlsv1.2`. PowerShell: sha·tarball 다운로드 직전 `SecurityProtocol = Tls12 -bor Tls13` |
| `verify` 모드 skip 우회 분기 | **0건** | 3경로 verify 분기의 모든 이탈 경로가 `error`/`return 1`/`throw`. `install.sh`에서 구 `warn ... 건너뜀; return 0` 2경로 제거 확인(RED TC-B7 PASS) |
| `verify` 모드 warn-continue | **0건** | `grep "건너뜀"` 결과 `install.ps1:390`(branch 분기) 단 1건 — verify 아님 |
| 폴백 시 sha 비교 금지(H-3) | **충족** | 3경로 모두 폴백이 `unverified`로 모드 강등 → verify 분기 진입 불가. D-3은 파일 잔존일 뿐 비교 재사용 아님 |
| 비대화형 fail-closed(H-8) | **충족** | `install.sh:377-379` / `update.sh:307-309` / `install.ps1:377-380` — 옵트인 없으면 거부 (판정 기준 차이는 PS-4) |
| 하드코딩 시크릿 | **0건** | 3파일에 자격증명·토큰 리터럴 없음 |
| RED 테스트 파일 수정 | **0건** | `scripts/tests/test_download_contract.sh` 미변경 (`red-first.md` §3 준수) |

---

## 7. 변경이력 헤더 검증 (D-F)

| 파일 | 부여 버전 | 실측 | 태스크 번호 | KST 일시 | 판정 |
|------|---------|------|-----------|---------|------|
| `opal/tools/opal-cli/lib/update.sh` | v1.1 | `:25` `v1.1 2026-08-07 09:19 KST: … (085)` | `(085)` ✓ | `2026-08-07 09:19 KST` ✓ | **일치** |
| `scripts/install.sh` | v1.6 | `:42-44` `v1.6 2026-08-07 09:28 KST: … (085)` | `(085)` ✓ | `2026-08-07 09:28 KST` ✓ | **일치** |
| `scripts/install.ps1` | v1.1 | `:49-51` `v1.1   2026-08-07 09:21  … (085)` | `(085)` ✓ | `2026-08-07 09:21` ✓ (블록 관례상 KST 접미 없음 — 기존 v1.0~v1.0.7과 동일 형식) | **일치** |

- `install.ps1` `.NOTES` 블록(`:28-29`)은 v1.0에서 정지 상태 **무변경** — PLAN D-F 지시(§9 R-7 관찰 기록만) 준수.
- 3파일 모두 `DL-CONTRACT (085)` 규약 각인 1줄을 헤더에 보유(`update.sh:27` / `install.sh:46` / `install.ps1:53`).

---

## 8. 범위 준수

| 항목 | 판정 | 근거 |
|------|------|------|
| `.github/workflows/release.yml` | **무변경** | `git diff --stat -- .github/workflows/release.yml` 무출력 |
| `.gitattributes` | **무변경** | `git diff --stat -- .gitattributes` 무출력 |
| 변경 파일 (D-G 결론 준수) | 3파일 + 테스트 1 | `opal/tools/opal-cli/lib/update.sh`, `scripts/install.ps1`, `scripts/install.sh` (수정) / `scripts/tests/test_download_contract.sh` (신규, RED 단계 산출) |
| 본 Step 산출 | 1파일 신규 | `tasks/085-…/CONTRACT-CROSSCHECK.md` — 소스 3파일·RED 테스트·PLAN.md·TEST-SCENARIO.md **미수정** |

---

## 9. PM 판단 요청 사항

| # | 사안 | 선택지 |
|---|------|--------|
| Q-1 | **D-3** (ps1 첫 폴백 sha 파일 잔존) | (a) Step 2로 반려, `install.ps1:212`에 1줄 이동 / (b) 실위험 없음으로 수용 + PLAN §3.3.2 주석 보강 |
| Q-2 | **D-4·D-5** (ps1 문구 드리프트) | (a) Step 2로 반려, 문구를 bash와 통일 / (b) PLAN §3.0 D-A 정합수단 (a)의 "문구 동일" 범위를 **폴백 배너 형식까지**로 완화 명시 |
| Q-3 | **D-1·D-2·D-6** (verify 비교 수단·매칭 정밀도·default 분기) | 전부 fail-closed라 즉시 위험 없음. 후속 태스크 이월 여부 |
| Q-4 | **D-7** (RG-8 출력 형태) | PLAN §3.0 D-E RG-8 문언 갱신 여부 |
| Q-5 | **PS-1/PS-3/PS-4** | `pwsh` 부재로 정적 판정만 수행. Step 5 대체 검증 또는 S-16 캡틴 Windows 실측에 반영 요망 |
| Q-6 | PLAN §4.2 체크박스 정합 | Step 3만 `[x]`, Step 1·2는 구현 완료 상태인데 `[ ]`로 남아 있음. Step 4는 완료 기준("8행 전부 일치") 미충족으로 **미체크 유지**. PLAN.md 수정 권한이 본 Step에 없어 갱신하지 않음 |

---

# ────────── 2회차 재판정 (2026-08-07, fix 5건 반영 후) ──────────

> 재판정자: opal-task-agent (Step 4 재대조 2회차) | 대상 파일 mtime: `install.ps1` 09:46 / `install.sh` 09:48 / `update.sh` 09:48
> **판정 원칙**: 1회차 보고·워커 보고를 재인용하지 않는다. 3파일을 전문 정독하고, D-2·D-6 은 **자체 픽스처로 실측**했다.
> **네트워크 사용**: 0회. 모든 실측은 로컬 픽스처 + `curl` 스텁(호출 계수용)으로 수행했다.

## 10. 8항목 재판정 요약

| 결과 | 건수 |
|------|------|
| **일치** | **8 / 8** |
| 부분일치 | 0 |
| 불일치 | 0 |

| # | 항목 | 1회차 | 2회차 | 전환 근거 |
|---|------|-------|-------|----------|
| 1 | 자산 존재 판정 신호 | 일치 | **일치** | `update.sh:96-101` / `install.sh:249-265` / `install.ps1:241-254` — 판정용 추가 왕복 0회 유지 |
| 2 | 자산명 파생 | 일치 | **일치** | `update.sh:55-57` ↔ `install.sh:191-193` md5 `27c24265…` **동일**, `install.ps1:162-182` 논리 등가 |
| 3 | 로컬 저장명 = 발행 자산명 | 일치 | **일치** | `update.sh:112,251` / `install.sh:276,286` / `install.ps1:263,307` |
| 4 | 폴백 3동작 | **부분일치** | **일치** ✅ | D-3 해소 — `install.ps1:243-245`가 `$script:DlShaFile` 을 다운로드 시도 **이전**에 기록. 폴백 진입점 3곳(`:252` `:258` `:331`) 전부에서 `:201-204` 삭제 조건이 참이 된다 |
| 5 | 폴백 로그 문구 | **부분일치** | **일치** ✅ | D-5 해소 — `건너뜀` 0건 / `sha256sums.txt 없음` 0건(grep 실측). `unverified` 4문구·`branch` 문구가 bash 리터럴과 일치 |
| 6 | 체크섬 3모드 | 일치 | **일치** (강화) | D-6 반영 — bash 2경로에도 `*)` fail-closed 추가(`install.sh:397-400` / `update.sh:323-327`). 3경로 전부 4분기 |
| 7 | strip 판정식 | 일치 | **일치** | `update.sh:61-67` ↔ `install.sh:197-203` md5 `f20e4b90…` **동일**, `install.ps1:291` 논리 등가 |
| 8 | 추출 사후조건 | 일치 | **일치** | `update.sh:348-351` / `install.sh:430-432` / `install.ps1:483-487` |

**→ PLAN §4.2 Step 4 완료 기준("8행 전부 일치") 충족.**

---

## 11. fix 5건 검증 (각 `파일:줄번호` 근거 + 실측)

### F-1 · D-3 — `install.ps1` sha 경로 사전 기록

| 항목 | 결과 |
|------|------|
| 코드 | `scripts/install.ps1:242-245` — `$shaFile = Join-Path $DestDir 'sha256sums.txt'` 직후 `$script:DlShaFile = $shaFile` |
| 다운로드 시도 | `:247-250` `try { Invoke-RestMethod -Uri $shaUrl -OutFile $shaFile -ErrorAction Stop }` — **기록 이후** |
| 첫 폴백 | `:251-254` `catch { Set-DlFallback -Reason '릴리즈 자산 없음'; return }` → `Set-DlFallback :201-204`의 `if ($script:DlShaFile -and (Test-Path …)) { Remove-Item … }` 조건이 **참** |
| 판정 | **의도대로 반영.** 부분 수신 파일 폐기가 성립하는 순서다 (코드 정독) |
| 3경로 동형 | bash 도 동일 순서 — `install.sh:251`(경로 설정) → `:254-262`(curl), `update.sh:97`(경로 설정) → `:98`(curl) |
| 잔여 | `Resolve-DownloadPlan` 진입부에 `$script:DlShaFile` **리셋이 없다** (bash 는 `install.sh:232` / `update.sh:86`에서 초기화) → §12 N-2 |

### F-2 · D-5 — `install.ps1` 폴백 후 안내 문구 정합

| grep | 결과 |
|------|------|
| `grep -rn "건너뜀" <3파일>` | **0건** |
| `grep -rn "sha256sums.txt 없음" <3파일>` | **0건** |

| 지점 | `install.ps1` | bash 대응 |
|------|--------------|----------|
| 옵트인 | `:405` `[UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행` | `install.sh:379` / `update.sh:310` — **문자 동일** |
| 비대화형 거부 | `:411` `릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: …` | `install.sh:384` — 옵트인 표기만 플랫폼 문법 차이(`$env:OPAL_ALLOW_UNVERIFIED='1'`) |
| 프롬프트 | `:414` `릴리즈 자산 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N]` | `install.sh:387` / `update.sh:315` — **문자 동일** |
| 사용자 동의 | `:418` `[UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행` | `install.sh:391` / `update.sh:320` — **문자 동일** |
| branch | `:424` `[OPAL] 브랜치 설치 — SHA-256 무결성 검증 대상 아님` | `install.sh:395` — 문자 동일(접두 관례 차) |

**판정: 의도대로 반영.** 단, `:424`가 `Write-Warning`(경고)인 반면 `install.sh:395`는 `info`(정보) → 심각도 비동형 잔존(§12 N-1).

### F-3 · PS-1 — `Tls13` 열거 멤버 부재 환경 대응

`scripts/install.ps1:137-160` `Set-DlSecurityProtocol`

```
:148  $tls12  = [Net.SecurityProtocolType]::Tls12
:149  $target = $tls12
:150  if ([Enum]::GetNames([Net.SecurityProtocolType]) -contains 'Tls13') {
:151      $target = $tls12 -bor [Net.SecurityProtocolType]::Tls13
:152  }
:153-159  try { …SecurityProtocol = $target } catch { …SecurityProtocol = $tls12 }
```

| 검증 항목 | 판정 |
|-----------|------|
| 구환경에서 `::Tls13` 리터럴이 **평가되지 않는가** | **충족.** PowerShell 은 static 멤버를 **런타임**에 해석하며, `:151`은 `:150` 조건이 참일 때만 실행되는 블록 본문이다. 파싱 시점 평가·바인딩이 없으므로 `.NET < 4.8`에서 throw 되지 않는다 (코드 정독 — `pwsh` 부재로 실행 검증 불가) |
| 열거에는 있으나 SChannel 미지원(`NotSupportedException`) | **충족.** `:156-159` 포괄 catch → `Tls12` 축퇴 |
| TLS 1.2 미만 축퇴 경로 | **부재.** 두 대입 모두 `Tls12` 이상. `Tls12` 대입 자체가 실패하면 예외가 전파되어 설치 중단 = fail-closed |
| 직접 참조 잔존 | `grep -n "Tls1" install.ps1` → 코드 라인은 `:148 :150 :151` 3건뿐, 전부 헬퍼 내부. 구 `:209`/`:285` 인라인 참조 **제거 확인** → 1회차 D-9(노출면 확대) **해소** |
| 호출 지점 | `:239`(릴리즈 태그 sha 다운로드 직전) / `:317`(tarball 다운로드 직전) — 신규 다운로드 3건 전부 선행 |

### F-4 · D-2 — bash 2경로 파일명 컬럼 정확 일치 (**실측**)

코드: `install.sh:349-350`, `update.sh:282-283` — `grep -F` 전필터 유지(RED C-7) + `awk -v want=… '{ n=$2; sub(/^\*/,"",n); if (n==want) { print; exit } }'` 후단 확정.

**픽스처 실측** (자체 제작, 네트워크 0):

| 픽스처 | 구성 | 구(舊) `grep -F \| head -1` | 현행 `install.sh` | 현행 `update.sh` |
|--------|------|------------------------------|-------------------|------------------|
| A | `{자산}.tar.gz.sig`(FAKE 해시) **먼저**, `{자산}.tar.gz`(REAL) 나중 | `deadbeef…` = **오탐** | `d4e4877b…` = **정탐** | `d4e4877b…` = **정탐** |
| B | `*{자산}.tar.gz.asc` → `*{자산}.tar.gz.sig` → `*{자산}.tar.gz` (binary mode 접두) | `deadbeef…` = **오탐** | `d4e4877b…` = **정탐** | `d4e4877b…` = **정탐** |

**종단 실측**

| 케이스 | 결과 |
|--------|------|
| `install.sh verify_checksum` — 픽스처 A 주입 | `exit=0` + `opal-v0.6.11.tar.gz: OK` + `SHA-256 체크섬 검증 완료` |
| `update.sh` verify 분기 — 픽스처 A 주입 | `exit=0` + `체크섬 검증 완료` |
| `update.sh` verify 분기 — tarball 변조 | `exit=1` + `체크섬 불일치!` + 기대/실제 해시 출력 (fail-closed 유지) |

**판정: 의도대로 반영. 오탐 → 정탐 전환을 실측으로 입증.**
부기: 현행 `release.yml:34`은 `sha256sum "${ARCHIVE}" > sha256sums.txt` — 1행 단일 자산이므로 이 결함은 미발현 상태였고, fix 는 방어적 선반영이다.

### F-5 · D-6 — bash 2경로 체크섬 `case`에 `*)` 하드 실패 (**실측**)

코드: `install.sh:397-400`(→ `error` = `exit 1`) / `update.sh:323-327`(→ `error` + `return 1`).

| 파일 | 모드 값 | exit | 메시지 |
|------|--------|------|--------|
| `install.sh` | `bogus` | **1** | `체크섬 모드 값 이상: 'bogus' — DL-CONTRACT 위반. 설치를 중단합니다.` |
| `install.sh` | `` (공백) | **1** | 동일 형식 |
| `install.sh` | `VERIFY` (대문자) | **1** | 동일 형식 |
| `install.sh` | `verify ` (후행 공백) | **1** | 동일 형식 |
| `update.sh` | `bogus` | **1** | `체크섬 모드 값 이상: 'bogus' — DL-CONTRACT 위반. 업데이트를 중단합니다.` |
| `update.sh` | `` (공백) | **1** | 동일 형식 |
| `update.sh` | `VERIFY` | **1** | 동일 형식 |

**판정: 의도대로 반영. 두 bash 파일 모두 3종 밖 값에서 exit≠0 실측 확인.** 3경로 전부 fail-closed 기본 분기 보유(`install.ps1:427-430`).

---

## 12. fix 가 새로 만든 문제 — **회귀 0건**, 신규 발견 5건(전부 P3, fix 기인 아님)

> **회귀·부작용 판정: 0건.** 아래 검사 전부에서 fix 5건에 기인한 새 결함을 찾지 못했다.
> `shellcheck -S warning` 2파일 무출력 / `bash -n` 2파일 통과 / RED 계약 26 PASS 0 FAIL / 공유 헬퍼 2종 md5 불변 / RG-1~RG-8 보존 / dry-run 네트워크 호출 수 원본과 동일.
> 아래 5건은 **재대조 과정에서 새로 관측된 잔여 드리프트**이며, fix 이전에도 동일하게 존재했다(원본·1회차 대조로 확인). 전부 fail-closed·무해이나 기록을 남긴다.

| # | 등급 | 내용 | 근거 | fix 기인? |
|---|------|------|------|-----------|
| N-1 | P3 | `install.ps1:424` branch 분기가 `Write-Warning`(경고), `install.sh:395`는 `info`(정보) — 문구는 D-5 fix 로 동일해졌으나 **심각도가 비동형**. main 브랜치 설치 시 RG-3 배너(`:541-543`)와 합쳐 경고가 2회 노출된다 | 원본 `install.ps1`(HEAD) 도 `Write-Warning` 계열 → **회귀 아님** | 아니오 |
| N-2 | P3 | `install.ps1 Resolve-DownloadPlan`에 진입부 `$script:DlShaFile` **리셋 부재**. bash 2경로는 함수 진입 즉시 초기화(`install.sh:232` / `update.sh:86`) | 현재 호출 1회뿐이라 실동작 무해. D-3 fix 가 "사전 기록" 순서를 도입했으므로 대칭 리셋이 있어야 완전 동형 | 아니오(fix 가 노출) |
| N-3 | P3 | **변경이력 타임스탬프 정체** — fix 2배치를 기존 버전 엔트리에 접었으나 시각은 fix 이전값 유지. `update.sh:25` `09:19` / `install.sh:42` `09:28` / `install.ps1:49` `09:21` vs 실제 최종 수정 `09:48` / `09:48` / `09:46` | D-F "KST 일시" 정확성 관점 미세 어긋남. 버전 번호·태스크 번호 각인은 정상 | 예(무해) |
| N-4 | P3 | bash 2경로 verify 분기에 **sha 파일 존재 선검사 부재** — 파일이 실제로 없어도 `sha256sums.txt에 {자산} 항목 없음` 으로 보고한다(**실측**: `install.sh` exit=1 / `update.sh` exit=1, 둘 다 문구가 사실과 다름). `install.ps1:373-375`는 `Test-Path` 로 `찾을 수 없습니다` 를 구분 | 둘 다 하드 실패이므로 보안 영향 0. 진단 문구 품질 사안 | 아니오 |
| N-5 | P3 | `expected_hash` 추출식 미세 드리프트 — `install.sh:356` `awk 'NF >= 2 { print $1; exit }'` vs `update.sh:288` `awk '{print $1}'` | 선택식(`n == want`)이 이미 `$2` 존재를 보장하므로 동작 동일. 두 하드 실패 가드(`install.sh:357` / `update.sh:290`)는 현재 도달 불가한 방어선 | 아니오 |

**추가 관측 (사전존재, 불일치 아님)**

| # | 내용 |
|---|------|
| O-1 | CRLF 개행 `sha256sums.txt` 는 `_dl_asset_name` 이 `$2` 말미 `\r` 때문에 `.tar.gz$` 매칭에 실패해 **빈 값 → `unverified` 폴백**으로 강등된다(실측: CRLF `''` / LF `opal-v0.6.11.tar.gz`). 즉 D-2 fix 의 정확 일치가 CRLF 하드 실패를 새로 유발하지 **않는다** — verify 분기 자체에 도달하지 않는다. `release.yml` 은 Linux runner 생성이라 LF |
| O-2 | `opal-cli update --dry-run` 을 `--to` 없이 호출하면 버전 자동조회 API **2회**가 여전히 발생한다(curl 스텁 실측). 원본 HEAD 도 dry-run 게이트가 버전 조회 **뒤**에 있었으므로 RG-8 보존이며 회귀 아님. `install.sh` dry-run(0회)·`install.ps1` dry-run(`:73` 조기 반환, 0회)과는 비대칭 |
| O-3 | `install.ps1:461-464` `--exclude` 4종이 배열 원소로 재구성되어 원본의 `--exclude='tasks/*'` 인라인 형태를 대체했다. 4종 개수·패턴 동일 → RG-6 보존이며, 빈 인자 주입 위험이 제거된 개선 |

---

## 13. 정적 검사 4종 + 보강 실측 (2회차 재실행)

| # | 명령 | 기대 | 실측 | 판정 |
|---|------|------|------|------|
| ① | `grep -rn "archive/refs/tags" <3파일>` | 각 파일 폴백 분기 1회 | 코드 라인 각 1건 — `install.sh:212` / `install.ps1:195` / `update.sh:76`. 나머지 3건은 변경이력 주석 | **PASS** |
| ② | `grep -rn "opal\.tar\.gz" scripts/install.sh` | 0건 | 0건 | **PASS** |
| ③ | `grep -rn "strip-components" <3파일>` | 조건부 분기 내부에만 | 실행 라인 3건 — `install.sh:422`(`if [[ "${strip_n}" -eq 1 ]]`) / `update.sh:337`(`if [[ "$strip_n" -eq 1 ]]`) / `install.ps1:463`(`if ($strip -eq 1)`). 나머지는 로그·주석 | **PASS** |
| ④ | `grep -rn "DL-CONTRACT (085)" <3파일>` | 3파일 전부 헤더 각인 | `update.sh:25,27,30` / `install.sh:42,48,183` / `install.ps1:49,58` — 전부 첫 70줄 이내 존재 | **PASS** |

| 보강 검사 | 결과 |
|-----------|------|
| `bash -n scripts/install.sh` | **PASS** |
| `bash -n opal/tools/opal-cli/lib/update.sh` | **PASS** |
| `shellcheck -S warning scripts/install.sh` | **무출력 (PASS)** — 2회차 신규 추가 검사 |
| `shellcheck -S warning opal/tools/opal-cli/lib/update.sh` | **무출력 (PASS)** — `-e SC2148`(lib 파일 shebang 없음) 제외 |
| `pwsh` 구문 파싱 | **미실행** — `command -v pwsh`·`powershell` 둘 다 부재. `install.ps1` 은 전문 코드 정독 + TC-C3~C6 정적 검사로만 커버 (1회차와 동일 사유) |
| `_dl_asset_name` md5 (install.sh ↔ update.sh) | `27c24265bfb274007201182e7e17a02f` **양측 동일** + `diff` 무출력 |
| `_dl_detect_strip` md5 (install.sh ↔ update.sh) | `f20e4b90275f5709190b10fab6fa55b9` **양측 동일** + `diff` 무출력 |
| `bash scripts/tests/test_download_contract.sh` | **`PASS 26 / FAIL 0 / SKIP 0` — `verdict: ALL PASS`** (독립 재실측) |
| RED 테스트 파일 무변경 | `scripts/tests/test_download_contract.sh` mtime `09:15:09` — fix 배치(`09:46`~`09:48`) **이전**. 미수정 확인 (`red-first.md` §3 준수) |
| `PLAN.md` / `TEST-SCENARIO.md` 무변경 | mtime `09:32:01` / `09:04:54` — fix 이전. 미수정 확인 |

---

## 14. 회귀 보존 RG-1 ~ RG-8 재확인

| # | 항목 | 판정 | 2회차 근거 |
|---|------|------|-----------|
| RG-1 | main 브랜치 URL `archive/refs/heads/{branch}.tar.gz` | **보존** | `update.sh:89` / `install.sh:243`(+DRY-RUN `:235`) / `install.ps1:232`(+DRY-RUN `:223`) — URL 형태 무변경 |
| RG-2 | main 브랜치 추출 strip=1 | **보존** | 판정식 md5 불변 + RED TC-B2 PASS(prefix 있는 아카이브 → 루트에 VERSION·opal/) |
| RG-3 | main UNVERIFIED 배너 위치·문구 | **보존** | `install.sh:506-508` / `install.ps1:541-543` 문구·위치 무변경. `update.sh:271-274` 는 다운로드 직후 위치·문구 유지. **D-5 fix 가 배너를 건드리지 않았음 확인** |
| RG-4 | 릴리즈 태그 + sha 부재 시 3분기 | **보존** | `install.sh:376-392` 실측 — 비대화형+옵트인 없음 `exit=1` / `OPAL_ALLOW_UNVERIFIED=1` `exit=0`. `update.sh:307-322` / `install.ps1:403-419` 동형 |
| RG-5 | `install.sh` `OPAL_TARBALL` 참조 지점 | **보존** | `:129`(선언) `:286`(설정) `:313`(폴백 재설정) `:306,322`(curl) `:418,422,425`(추출). 구 리터럴 경로 0건 |
| RG-6 | `install.ps1` `--exclude` 4종 | **보존** | `:464` 4종 전부 유지, strip 인자와 독립 배열 append (O-3) |
| RG-7 | `install.sh` DRY-RUN 네트워크 0 | **보존** | **curl 스텁 실측 — 호출 0건.** `[DRY-RUN] 흐름 검증 완료` 출력 |
| RG-8 | `opal-cli update --dry-run` | **보존** | **curl 스텁 실측** — `--to v9.9.9 --dry-run` **0건**, 버전 미지정 시 2건(원본 HEAD 와 동일 위치·동일 횟수, O-2). `_dl_resolve_plan` 이전 반환으로 **신규** 네트워크 0 |

---

## 15. 보안 계약 재확인

| 항목 | 판정 | 2회차 근거 |
|------|------|-----------|
| 신규 다운로드 TLS 강제 | **충족** | bash 신규 curl 6건 전부 `--proto '=https' --tlsv1.2`(`update.sh:98,252,258` / `install.sh:254-262,299-307,315-323`). PowerShell 신규 다운로드 3건 전부 `Set-DlSecurityProtocol` 선행(`:239` → `:249` sha / `:317` → `:321,335` tarball) |
| TLS 축퇴 하한 | **충족** | `install.ps1:148-159` — 어떤 경로에서도 `Tls12` 미만으로 내려가지 않음. PS-1 fix 가 하한을 낮추지 **않았음** 확인 |
| `verify` 모드 skip 우회 분기 | **0건** | 3경로 verify 분기의 모든 이탈이 `error`/`return 1`/`throw`. `grep "건너뜀"` **0건** |
| 모드 값 이상 시 무음 통과 | **0건** | 3경로 전부 기본 분기 하드 실패 — bash 2경로 **실측 exit=1**(§11 F-5), `install.ps1:427-430` throw |
| 폴백 시 sha 비교 금지(H-3) | **충족** | 폴백 3경로 모두 모드를 `unverified` 로 강등 + **sha 파일 실제 폐기**(D-3 해소로 PowerShell 첫 폴백까지 성립) |
| 비대화형 fail-closed(H-8) | **충족** | `install.sh:383-385` 실측 `exit=1` / `update.sh:311-314` / `install.ps1:409-412`. (판정 기준 차이 PS-4 는 미해소 — `pwsh` 부재) |
| 하드코딩 시크릿 | **0건** | 3파일에 자격증명·토큰 리터럴 없음 |
| RED 테스트 파일 수정 | **0건** | mtime 대조로 확인 (§13) |

---

## 16. 범위 확인

| 항목 | 판정 | 근거 |
|------|------|------|
| `.github/workflows/release.yml` | **무변경** | `git diff --stat` 무출력 + `git status --short -- .github/` 무출력 |
| `.gitattributes` | **무변경** | `git diff --stat` 무출력 + `git status --short` 무출력 |
| 전체 변경 파일 | 4건 | `opal/tools/opal-cli/lib/update.sh`, `scripts/install.ps1`, `scripts/install.sh` (수정) / `scripts/tests/test_download_contract.sh` (RED 단계 신규). 그 외 `.opal/MEMORY.json`(PM 세션 산출, 본 태스크 소스 아님) |
| 본 Step 2회차 산출 | 1파일 갱신 | 본 문서만. 소스 3파일·RED 테스트·`PLAN.md`·`TEST-SCENARIO.md` **미수정** (mtime 대조로 확인) |

---

## 17. 1회차 불일치 7건 + 관측 2건 최종 상태

| # | 등급 | 2회차 상태 | 근거 |
|---|------|-----------|------|
| D-1 | P2 | **PM 수용 (미해소, 위험 없음)** | verify 비교 수단 3경로 3종 유지. 3경로 전부 fail-closed 재확인 |
| D-2 | P2 | **해소** ✅ | §11 F-4 픽스처 실측 — 오탐 → 정탐 |
| D-3 | P2 | **해소** ✅ | §11 F-1 `install.ps1:243-245` |
| D-4 | P3 | **PM 수용 (미해소, 무해)** | 폴백 사유 괄호 부연 축약 잔존 (`:252` `:258`). 사유 식별성은 3경로 동일 |
| D-5 | P3 | **해소** ✅ | §11 F-2 grep 0건 + 문구 대조 |
| D-6 | P3 | **해소** ✅ | §11 F-5 두 bash 파일 exit≠0 실측 |
| D-7 | P3 | **PM 수용 (코드 아닌 RG-8 서술 사안)** | `update.sh:222` 소스 서술문 유지 |
| D-8 | 관측 | **사전존재 유지** | `install.ps1:77,83` API 호출이 TLS 강제보다 선행. 이번 변경 무관 |
| D-9 | 관측 | **해소** ✅ | `Tls13` 인라인 참조 2곳 → `Set-DlSecurityProtocol` 헬퍼 1곳으로 통합, 조건부 평가 |
| PS-1 | 우려 | **해소** ✅ | §11 F-3 |
| PS-2 | 우려 | **잔존** | `install.ps1:280` `& tar -tzf` in `try` — `pwsh` 부재로 실행 검증 불가. Step 5 / S-16 Windows 실측 대상 |
| PS-3 | 우려 | **잔존** | `Invoke-RestMethod -OutFile` 로 바이너리 수신(`:249,321,335`). 원본 답습, 리다이렉트 동작은 Windows 실측 필요 |
| PS-4 | 우려 | **잔존** | `:409` `[Environment]::UserInteractive` 와 bash `[[ ! -t 0 ]]` 의 비대화형 판정 기준 차. fail-closed 방향은 유지 |

---

## 18. PM 판단 요청 (2회차)

| # | 사안 | 성격 |
|---|------|------|
| Q'-1 | **N-1** (`install.ps1:424` `Write-Warning` vs `install.sh:395` `info`) | 후속 이월 권고. 브랜치 설치 시 경고 2중 노출뿐, 기능 영향 0 |
| Q'-2 | **N-2** (`Resolve-DownloadPlan` 진입부 리셋 부재) | 후속 이월 권고. 1줄 추가로 완전 동형화 가능하나 현재 도달 불가 |
| Q'-3 | **N-3** (변경이력 타임스탬프 정체 3파일) | Step 5 마무리 시 3파일 헤더 시각 갱신 여부 |
| Q'-4 | **N-4** (bash verify 분기 sha 파일 존재 선검사 부재) | 진단 문구 품질. 후속 이월 |
| Q'-5 | **PS-2·PS-3·PS-4** | `pwsh`·`powershell` 모두 부재로 2회차에서도 실행 검증 불가. S-16 캡틴 Windows 실측 필수 |
| Q'-6 | PLAN §4.2 체크박스 | Step 4 는 **완료 기준 충족** — `[x]` 전환 가능. Step 1·2 미체크 상태도 함께 정리 필요. 본 Step 은 `PLAN.md` 수정 권한 없음 |

---

## 변경이력

| 버전 | 일시 | 내용 |
|------|------|------|
| v1.0 | 2026-08-07 09:37 KST | 신규 작성 — 8항목 대조표 + 정적 검사 4종 + RG-1~RG-8 + PowerShell 단독 판정 + 불일치 7건 (085 Step 4) |
| v2.0 | 2026-08-07 | **2회차 재판정 추가** (§10~§18) — fix 5건 반영 후 8항목 전부 일치 전환(항목 4·5 부분일치 해소), fix 5건 개별 검증(D-2·D-6 자체 픽스처 실측), 회귀 0건 + 신규 발견 5건(N-1~N-5, 전부 P3)·관측 3건(O-1~O-3), 정적 검사 4종+shellcheck 재실행, RG-1~RG-8·보안 계약 재확인, 범위 무변경 확인. §0~§9(1회차)는 원문 보존 (085 Step 4 재대조) |

# TEST: 릴리즈 체크섬 검증 경로 정합 — 3경로 × 3조합 실측 기록

> 실행일: 2026-08-07 | 실행자: opal-test-agent (test_mode: BE / 스크립트 실행 검증) | PLAN §4.2 Step 5
> 대상 커밋: 작업트리 (HEAD = `5bd0e26`, 미커밋 변경 3파일)
> 시나리오 SSOT: `TEST-SCENARIO.md` (S-1~S-19) | 설계 SSOT: `PLAN.md` §3.0·§3.6.2

---

## 0. 실행 환경과 격리 정책

| 항목 | 값 |
|------|-----|
| OS / 셸 | Darwin 25.5.0 (arm64) / GNU bash 3.2.57(1) |
| 해시 도구 | `/sbin/sha256sum`, `/usr/bin/shasum` (양쪽 존재) |
| 정적 분석 | `shellcheck` 0.11.0 |
| PowerShell | **`pwsh`·`powershell` 모두 미설치** (→ S-4 부분 / S-16 / S-18 Skip 사유) |
| 대화형 pty | `/usr/bin/expect` (S-10 대화형 동의 재현에 사용) |
| 작업 루트 | `/Volumes/Data/AIStudio/workspace/ai-framework` |
| 격리 작업 디렉토리 | `$W` = `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/c184aa0c-f911-43de-bad1-44e7ddf69d20/scratchpad/t085` |

### 0.1 [MUST] 환경 격리 — 실제로 지킨 것

- **`./scripts/install-mac.sh`를 실행하지 않았다.** 따라서 `~/.opal/tools/opal-cli/lib/update.sh`는 **재배포하지 않았다**.
  대신 PLAN §3.6.4의 "재배포된 사본"을 **프로젝트 사본 직접 구동**으로 대체했다 —
  `bash opal/tools/opal-cli/run.sh update ...` 는 `BASH_SOURCE` 기준으로 `opal/tools/opal-cli/lib/update.sh`(프로젝트 사본)를 source 하므로
  재배포본과 **동일 바이트의 코드**가 실행된다. `OPAL_HOME`·`HOME`은 격리 디렉토리로 지정했다.
- **`~/.opal/` 아래에 아무것도 쓰지 않았다.** 검증 전후 mtime 동일:

  ```
  $ stat -f '%Sm %N' ~/.opal ~/.opal/VERSION ~/.opal/tools/opal-cli/lib/update.sh
  Aug  6 12:41:33 2026 /Users/iskang/.opal
  Aug  6 12:41:38 2026 /Users/iskang/.opal/VERSION
  Aug  6 12:41:23 2026 /Users/iskang/.opal/tools/opal-cli/lib/update.sh
  ```
  (검증 세션은 2026-08-07 11:31~ 진행 — 전 구간 무오염)
- **소스 3파일과 RED 테스트 파일을 수정하지 않았다.** 읽기·실행만 수행했다.

### 0.2 경계 봉인(seam) 2종 — 무엇을 가로챘고 왜인가

실 스크립트·실 네트워크·실 릴리즈 자산을 그대로 쓰되, 아래 **두 지점만** 프로세스 경계에서 봉인했다.
둘 다 SUT(=DL-CONTRACT 다운로드·검증·추출 경로) **바깥**이며, 소스 코드는 일절 변경하지 않았다.

| # | 봉인 지점 | 수단 | 이유 | 영향 |
|---|----------|------|------|------|
| 1 | 플랫폼 설치 스크립트 `exec`/호출 (`exec bash .../scripts/install/macos.sh`, `bash "$installer"`) | `$W/stub/bash` — PATH 선행 스텁. 해당 경로 인자일 때만 argv·env를 기록하고 exit 0, 그 외 모든 호출은 `/bin/bash`에 위임 | `install-mac.sh`/`macos.sh`는 실사용 `~/.opal`을 파괴적으로 재설치한다. [MUST] 환경 격리 위반 회피 | 다운로드→검증→추출→VERSION 각인 채택까지 **전 구간 실행**. 마지막 인스톨러 호출만 기록으로 대체 |
| 2 | 네트워크 결함 주입 (`curl`) | `$W/stub/curl` — PATH 선행 스텁. ① 모든 호출 URL을 `$DL_LOG`에 기록 ② `$DL_DENY_PAT` 매칭 URL만 `exit 22`(404 등가) ③ `$DL_OVERRIDE` 매칭 URL은 로컬 픽스처를 `-o` 대상에 복사. 그 외 전부 `/usr/bin/curl`에 위임 | 재릴리즈 없이 "자산 부재"·"다운로드 실패"·"손상 tarball"을 재현. PLAN §3.6.2가 권고한 3방법 중 **시스템 설정 변경이 없는** 방식 | 결함을 주입하지 않은 칸(S-7·S-9·S-13·S-14)은 **전부 실 네트워크·실 릴리즈 자산** |

> 스텁 shebang은 `#!/bin/bash`(절대경로)로 고정했다 — `#!/usr/bin/env bash`였다면 스텁 `bash` 자신을 재귀 호출한다.
> 명령 치환 `$(...)`은 PATH 조회를 거치지 않으므로 스크립트 내부 서브셸은 스텁의 영향을 받지 않는다.

### 0.3 픽스처 — 전부 실 다운로드본

```
$ cd $W/fx
$ curl -fsSL --proto '=https' --tlsv1.2 -o sha256sums.txt          "https://github.com/ceo4ever/opal/releases/download/v0.6.11/sha256sums.txt"
$ curl -fsSL --proto '=https' --tlsv1.2 -o opal-v0.6.11.tar.gz     "https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz"
$ curl -fsSL --proto '=https' --tlsv1.2 -o v0.6.11-archive.tar.gz  "https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz"
$ curl -fsSL --proto '=https' --tlsv1.2 -o main-archive.tar.gz     "https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz"
```

```
=== sha256sums.txt 전문 ===
1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05  opal-v0.6.11.tar.gz

=== 실측 해시 ===
1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05  opal-v0.6.11.tar.gz   (발행 자산)
463a584266a5483bd477ce7fd6c0c295eac1d787d6b92f186f647fb2e3eb4c19  v0.6.11-archive.tar.gz (자동 아카이브)
dc2193acc607d704241242dc2e2165892428f717bfe3d797d0a79650b86add7a  main-archive.tar.gz
13bb2a9772082658ed552be1d0756a38a6558a93813c30a0fba00468938463e1  opal-v0.6.11-corrupt.tar.gz (말미 19바이트 변조)

=== tar 최상위 구조 ===
opal-v0.6.11.tar.gz        entries=981  root-direct=6  top-segments=13  sample=.claude/
v0.6.11-archive.tar.gz     entries=982  root-direct=0  top-segments=1   sample=opal-0.6.11/
main-archive.tar.gz        entries=982  root-direct=0  top-segments=1   sample=opal-main/
```

> **핵심 대조**: 캡틴이 최초 신고한 실패의 `실제값 463a5842…`는 **자동 아카이브 tarball의 해시와 정확히 일치**한다.
> 즉 구형 코드가 `archive/refs/tags/v0.6.11.tar.gz`(463a5842…)를 받아놓고 `sha256sums.txt`가 기술한 발행 자산(1ae94e27…)과 비교한 것이 근본 원인임이 **실측으로 확정**되었다.

파생 픽스처 (수동 생성):
```
sha256sums-noentry.txt    : ff95f101…  RELEASE-NOTES.md        (.tar.gz 항목 없음)
sha256sums-blankhash.txt  : "  opal-v0.6.11.tar.gz\n"         (해시 컬럼 공백)
sha256sums-binmode.txt    : 1ae94e27… *opal-v0.6.11.tar.gz    (binary mode '*' 접두)
opal-v0.6.11-corrupt.tar.gz : 정상본 복사 + 'CORRUPTED-BYTES-085' append
```

### 0.4 자산 부재 시뮬레이션 — 실행 전 실제 자산 유무 확인

```
$ curl -fsSL "https://api.github.com/repos/ceo4ever/opal/releases?per_page=100" | jq -r '.[] | "\(.tag_name)\t\(.assets|length)\t\([.assets[].name]|join(","))"'
v0.6.11  2  opal-v0.6.11.tar.gz,sha256sums.txt
v0.6.10  2  opal-v0.6.10.tar.gz,sha256sums.txt
...  (v0.6.0 까지 전부 자산 2개)
v0.5.0   0
```
- **v0.6.0 이상 전 태그가 자산을 보유**하므로 "자산 없는 과거 태그" 방법(PLAN §3.6.2 3안)은 v0.5.0만 가능하다.
- v0.5.0은 실제로 자산이 없음을 확인(`releases/download/v0.5.0/sha256sums.txt` → **HTTP 404**, `archive/refs/tags/v0.5.0.tar.gz` → **HTTP 200**).
- 그러나 v0.5.0 트리 루트에는 **`VERSION` 파일이 없다**(API git/trees 확인). 추출 사후조건(`VERSION`·`opal/`)에서 규약과 무관한 이유로 하드 실패하므로 폴백 칸의 대조군으로 부적합하다.
- 따라서 **PATH 스텁 방식(PLAN §3.6.2 2안, 시스템 설정 변경 없음)** 을 채택해 v0.6.11 태그에서 `sha256sums.txt`/자산 tarball만 선택적으로 404 처리했다.

---

## 1. 9칸 매트릭스 판정 요약

| 경로 \ 조합 | 릴리즈 태그 (verify) | 자산 부재 폴백 (unverified) | main 브랜치 (branch) |
|------------|---------------------|--------------------------|---------------------|
| `install.sh` | **PASS** (§2.1 — S-7·S-8) | **PASS** (§2.2 — S-10·S-11·S-12·S-19) | **PASS** (§2.3 — S-14) |
| `install.ps1` | **SKIP** (§3 — pwsh·Windows 부재, 대체 검증 3종 기재) | **SKIP** (§3, 동일) | **SKIP** (§3, 동일) |
| `update.sh` | **PASS** (§2.4 — S-9 목표달성) | **PASS** (§2.5 — S-19) | **PASS** (§2.6 — S-14) |

전체: **PASS 6칸 / SKIP 3칸 (`install.ps1` 행 전체) / FAIL 0칸**

---

## 2. 실행 가능 6칸 — 명령·출력·exit code

모든 실행의 공통 전제:
```
W=/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/c184aa0c-f911-43de-bad1-44e7ddf69d20/scratchpad/t085
cd /Volumes/Data/AIStudio/workspace/ai-framework
ENVBASE="env -i PATH=$W/stub:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin HOME=$W/home"
```

### 2.1 [T085/L2-F2-verify] `install.sh` × 릴리즈 태그 — **PASS** (S-7)

```
$ env -i PATH="$W/stub:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" HOME="$W/home" \
    DL_LOG="$W/logs/s7.net" INSTALLER_LOG="$W/logs/s7.inst" \
    OPAL_VERSION=v0.6.11 OPAL_REPO=ceo4ever/opal OPAL_HOME="$W/home/.opal" \
    /bin/bash scripts/install.sh
```
```
[opal] OPAL 설치 시작 (repo: ceo4ever/opal, version: v0.6.11)
[opal] 플랫폼 감지: macos
[opal] 의존성 확인 완료: curl, tar, git
[opal] 체크섬 파일 확인 중: https://github.com/ceo4ever/opal/releases/download/v0.6.11/sha256sums.txt
[opal] tarball URL: https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz
[opal] tarball 다운로드 중...
[opal] tarball 다운로드 완료: /var/folders/.../tmp.vkUpJDOaVp/opal-v0.6.11.tar.gz
[opal] SHA-256 검증 중...
opal-v0.6.11.tar.gz: OK
[opal] SHA-256 체크섬 검증 완료
[opal] tarball 추출 중... (strip-components=0)
[opal] 추출 완료: /var/folders/.../tmp.vkUpJDOaVp/opal-extracted
[opal] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
[opal] macos 설치 스크립트 실행 중...
INSTALLER_INTERCEPTED argv=/var/folders/.../opal-extracted/scripts/install/macos.sh
  OPAL_SOURCE_DIR=/var/folders/.../opal-extracted
  OPAL_VERSION=v0.6.11
```
```
EXIT=0
네트워크 호출 (2건):
  1  https://github.com/ceo4ever/opal/releases/download/v0.6.11/sha256sums.txt
  2  https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz
'건너|스킵|skip' 경고 건수 = 0
```

| AC | 판정 |
|----|------|
| "SHA-256 체크섬 검증 완료" 출력 | **O** |
| exit 0 | **O** |
| 항목 미매칭 스킵 경고 0건 | **O** (0건) |
| 다운로드 대상 = 검증 대상 (`releases/download/.../opal-v0.6.11.tar.gz`) | **O** |
| strip 자동 판정 = 0 (발행 자산은 prefix 없음) | **O** |

### 2.1b [T085/L2-F2-corrupt] `install.sh` × 손상 tarball 거부 — **PASS** (S-8)

```
$ printf 'releases/download/v0\\.6\\.11/opal-v0\\.6\\.11\\.tar\\.gz\t%s\n' \
    "$W/fx/opal-v0.6.11-corrupt.tar.gz" > "$W/ovr-corrupt.tsv"
$ env -i PATH="$W/stub:..." HOME="$W/home" DL_OVERRIDE="$W/ovr-corrupt.tsv" \
    DL_LOG="$W/logs/s8.net" INSTALLER_LOG="$W/logs/s8.inst" \
    OPAL_VERSION=v0.6.11 OPAL_REPO=ceo4ever/opal /bin/bash scripts/install.sh
```
```
[opal] 체크섬 파일 확인 중: .../releases/download/v0.6.11/sha256sums.txt
[opal] tarball URL: .../releases/download/v0.6.11/opal-v0.6.11.tar.gz
[opal] tarball 다운로드 중...
[opal] tarball 다운로드 완료: /var/folders/.../tmp.J1UUoJLg5R/opal-v0.6.11.tar.gz
[opal] SHA-256 검증 중...
opal-v0.6.11.tar.gz: FAILED
shasum: WARNING: 1 computed checksum did NOT match
shasum: /var/folders/.../sha256sums.txt: no file was verified
[opal] ERROR: SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다.
```
```
EXIT=1
INSTALLER_LOG = (빈 파일) → 추출·설치 단계 미도달
```

| AC | 판정 |
|----|------|
| exit≠0 | **O** (1) |
| 추출·설치 단계 미도달 | **O** (`추출 중` 출력 없음, 인터셉트 로그 0줄) |

### 2.2 [T085/L2-F4-fallback / noninteractive / nocompare] `install.sh` × 자산 부재 폴백 — **PASS** (S-10·S-11·S-12·S-19)

**(a) S-11 비대화형 + 옵트인 미지정 → 거부**

```
$ env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG=... INSTALLER_LOG=... \
    DL_DENY_PAT='releases/download/.*/sha256sums\.txt' \
    OPAL_VERSION=v0.6.11 OPAL_REPO=ceo4ever/opal \
    /bin/bash scripts/install.sh < /dev/null
```
```
[opal] 체크섬 파일 확인 중: .../releases/download/v0.6.11/sha256sums.txt
[opal] WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
[opal] tarball URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
[opal] tarball 다운로드 중...
[opal] tarball 다운로드 완료: /var/folders/.../opal-v0.6.11-archive.tar.gz
[opal] ERROR: 릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1
exit=1        installer-intercepted: 0 lines
```

**(b) S-11 비대화형 + `OPAL_ALLOW_UNVERIFIED=1` → 경고 후 진행**

```
$ (동일 + OPAL_ALLOW_UNVERIFIED=1)
[opal] WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
[opal] WARN: [UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행
[opal] tarball 추출 중... (strip-components=1)
[opal] 추출 완료: /var/folders/.../opal-extracted
[opal] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
INSTALLER_INTERCEPTED argv=/var/folders/.../opal-extracted/scripts/install/macos.sh
exit=0
```

**(c) S-10 대화형 + 진행 동의 (pty = `expect`)**

```
$ cat > "$W/s10.exp" <<'EOF'
set timeout 120
spawn /bin/bash $W/run10.sh          ;# run10.sh = 위 (a)와 동일 env + install.sh 실행
expect { -re {진행하시겠습니까.*\[y/N\]} { send "y\r" } timeout { exit 99 } }
expect eof
EOF
$ expect -f "$W/s10.exp"
```
```
[opal] WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
[opal] tarball URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
[opal] tarball 다운로드 완료: /var/folders/.../opal-v0.6.11-archive.tar.gz
릴리즈 자산 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N] y
[opal] WARN: [UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행
[opal] tarball 추출 중... (strip-components=1)
[opal] 추출 완료: /var/folders/.../opal-extracted
[opal] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
INSTALLER_INTERCEPTED argv=/var/folders/.../opal-extracted/scripts/install/macos.sh
RUNNER_EXIT=0
```
로그 검사(S-12):
```
'체크섬 불일치|FAILED|검증 실패' 건수 = 0     ← 폴백 시 잘못된 비교 부재
'릴리즈 자산 미사용 폴백' 건수         = 1     ← 폴백 사유 명시
'sha256sums.txt에|SHA-256 검증 중' 건수 = 0     ← sha 파일이 비교에 쓰이지 않음
```

**(d) S-19 폴백 진입 4경로 완전성** — exit code 일람

```
$ r19() { env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG=/dev/null INSTALLER_LOG=/dev/null \
      DL_DENY_PAT="$2" DL_OVERRIDE="$3" OPAL_VERSION=v0.6.11 OPAL_REPO=ceo4ever/opal \
      OPAL_ALLOW_UNVERIFIED=1 /bin/bash scripts/install.sh < /dev/null > "$W/logs/x.out" 2>&1; ... }
$ r19 a 'releases/download/.*/sha256sums\.txt' ""
$ r19 b "" "$W/ovr-noentry.tsv"                       # sha256sums.txt를 .tar.gz 항목 없는 파일로 치환
$ r19 c 'releases/download/v0\.6\.11/opal-v0\.6\.11\.tar\.gz' ""
$ r19 d 'releases/download/v0\.6\.11/opal-v0\.6\.11\.tar\.gz|archive/refs/tags/v0\.6\.11\.tar\.gz' ""
```
```
S-19(a) exit=0 | 체크섬비교흔적=0 | 폴백사유=릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
S-19(b) exit=0 | 체크섬비교흔적=0 | 폴백사유=릴리즈 자산 미사용 폴백: sha256sums.txt 형식 이상 (.tar.gz 항목 없음)
S-19(c) exit=0 | 체크섬비교흔적=0 | 폴백사유=릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패
S-19(d) exit=1 | 체크섬비교흔적=0 | 폴백사유=릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패
```
(c)의 전문 — **sha256sums.txt는 정상 수신했으나 자산 tarball만 실패한 경우**(S-12의 정확한 조건):
```
[opal] 체크섬 파일 확인 중: .../releases/download/v0.6.11/sha256sums.txt      ← 200 수신
[opal] tarball URL: .../releases/download/v0.6.11/opal-v0.6.11.tar.gz
[opal] tarball 다운로드 중...
curl: (22) The requested URL returned error: 404
[opal] WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패
[opal] 폴백 tarball URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
[opal] tarball 다운로드 완료: .../opal-v0.6.11-archive.tar.gz
[opal] WARN: [UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행
[opal] tarball 추출 중... (strip-components=1)
```
→ 받아둔 sha 파일이 폐기되고 **비교가 일어나지 않았다**(`SHA-256 검증 중` 미출력). H-3 결함 재현 없음.

(d) 전문:
```
[opal] tarball 다운로드 중...
curl: (22) The requested URL returned error: 404
[opal] WARN: 릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패
[opal] 폴백 tarball URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
curl: (22) The requested URL returned error: 404
[opal] ERROR: tarball 다운로드 실패: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
```
→ **하드 실패(exit 1)**. 무한 폴백·무음 진행 없음.

| AC | 판정 |
|----|------|
| S-10 무중단 폴백 + 사유 로그 | **O** |
| S-11 비대화형 거부 / 옵트인 진행 | **O** (exit 1 / exit 0) |
| S-12 폴백 시 sha 비교 부재 | **O** (비교 흔적 0건) |
| S-19 (a)(b)(c) UNVERIFIED 수렴 / (d) 하드 실패 | **O** (0/0/0/1) |

### 2.3 [T085/L2-RG-main] `install.sh` × main 브랜치 — **PASS** (S-14)

```
$ env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG="$W/logs/s14i.net" INSTALLER_LOG=... \
    OPAL_VERSION=main OPAL_REPO=ceo4ever/opal /bin/bash scripts/install.sh < /dev/null
```
```
[opal] OPAL 설치 시작 (repo: ceo4ever/opal, version: main)
[opal] WARN: [UNVERIFIED] 'main' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다.
[opal] 플랫폼 감지: macos
[opal] 의존성 확인 완료: curl, tar, git
[opal] tarball URL: https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz
[opal] tarball 다운로드 중...
[opal] tarball 다운로드 완료: /var/folders/.../tmp.42hOxPFf2x/opal-main.tar.gz
[opal] 브랜치 설치 — SHA-256 무결성 검증 대상 아님
[opal] tarball 추출 중... (strip-components=1)
[opal] 추출 완료: /var/folders/.../tmp.42hOxPFf2x/opal-extracted
[opal] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
INSTALLER_INTERCEPTED argv=/var/folders/.../opal-extracted/scripts/install/macos.sh
exit=0
네트워크 호출 (1건): https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz
```
> 브랜치 경로는 `sha256sums.txt`를 **조회조차 하지 않는다**(호출 1건) — RG-1 URL 무변경 확인.

배너 문구·위치 무변경 대조 (HEAD vs 작업트리):
```
$ git show HEAD:scripts/install.sh | grep -n 'UNVERIFIED.*브랜치 설치'
371:        warn "[UNVERIFIED] '${OPAL_VERSION}' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
$ grep -n 'UNVERIFIED.*브랜치 설치' scripts/install.sh
507:        warn "[UNVERIFIED] '${OPAL_VERSION}' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
```
문자열 **완전 동일**. 상대 위치도 동일 — 양쪽 모두 `main()` 안, DRY-RUN 경고 직후·`detect_platform` 직전:
```
HEAD  : main() → info 시작 → DRY-RUN warn → [배너] → detect_platform → check_deps → fetch_tarball
작업트리: main() → info 시작 → DRY-RUN warn → [배너] → detect_platform → check_deps → prepare_tmp → resolve_download_plan → fetch_tarball
```

### 2.3b [T085/L2-RG-dryrun] DRY-RUN 네트워크 무접근 — **PASS** (S-15)

```
$ OPAL_DRY_RUN=1 /bin/bash scripts/install.sh                     → 네트워크 호출 0건, exit 0
$ OPAL_DRY_RUN=1 OPAL_VERSION=v0.6.11 /bin/bash scripts/install.sh → 네트워크 호출 0건
$ /bin/bash opal/tools/opal-cli/run.sh update --dry-run --to v0.6.11 → 네트워크 호출 0건, exit 0
$ /bin/bash opal/tools/opal-cli/run.sh update --dry-run              → 1건 (api.github.com/.../releases/latest)
```
```
[opal] WARN: === DRY-RUN 모드 — 실제 설치 없이 흐름만 검증합니다 ===
[opal] WARN: [DRY-RUN] resolve_download_plan 생략 — 네트워크 조회 없음
[opal] WARN: [DRY-RUN] fetch_tarball 생략 — 실제 다운로드 없음
[opal] WARN: [DRY-RUN] verify_checksum 생략
[opal] WARN: [DRY-RUN] extract_to_tmp 생략
[opal] WARN: [DRY-RUN] exec_platform_installer 생략
[opal] [DRY-RUN] 실행 예정 경로: /var/folders/.../opal-extracted/scripts/install/macos.sh
[opal] [DRY-RUN] 흐름 검증 완료
```
```
[INFO] [dry-run] 다운로드 소스: releases/download/v0.6.11/<sha256sums.txt 파생 자산명> (자산 부재 시 자동 아카이브 폴백)
[INFO] [dry-run] 실제 다운로드 및 설치를 수행하지 않습니다.
```
> 4번째 케이스의 1건은 **버전 미지정 시 latest 태그 조회**로, `_dl_resolve_plan` **이전**의 사전존재 동작이다.
> HEAD도 동일 위치에서 동일 호출을 한다(`git show HEAD:...update.sh` 87~90행). RG-8("계획 수립 이전 종료") 충족 — 회귀 아님.

### 2.4 [T085/L2-F1-verify] `update.sh` × 릴리즈 태그 — **PASS** 🎯 (S-9, 목표달성 시나리오)

```
$ mkdir -p "$W/home/.opal"; printf 'v0.6.10\n' > "$W/home/.opal/VERSION"
$ env -i PATH="$W/stub:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" HOME="$W/home" \
    DL_LOG="$W/logs/s9.net" INSTALLER_LOG="$W/logs/s9.inst" \
    OPAL_HOME="$W/home/.opal" OPAL_REPO=ceo4ever/opal \
    /bin/bash opal/tools/opal-cli/run.sh update --to v0.6.11 --force
```
```
[INFO] 로컬 버전: v0.6.10
[INFO] 업데이트: v0.6.10 → v0.6.11
[INFO] 업데이트 버전: v0.6.11
[INFO] 다운로드 URL: https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz
[INFO] tarball 다운로드 중...
  ✓ 다운로드 완료
[INFO] 체크섬 검증 중...
  ✓ 체크섬 검증 완료
[INFO] 압축 해제 중... (strip-components=0)
  ✓ 압축 해제 완료
[INFO] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
[INFO] 업데이트 설치 중... (사용자 데이터 보존)
[WARN] 업데이트 주의: 사용자 커스텀 스킬(skills/)은 클린 후 재배포됩니다.
[WARN] 커스텀 스킬이 있으면 ~/.opal/skills.user/에 백업해두세요 (후속 태스크에서 자동화 예정).
INSTALLER_INTERCEPTED argv=/var/folders/.../tmp.nH3l5tnJou/opal-src/scripts/install/macos.sh
  FRAMEWORK_ROOT=/var/folders/.../tmp.nH3l5tnJou/opal-src
  OPAL_VERSION=v0.6.11
  OPAL_AUTO_INSTALL=1
  ✓ 업데이트 완료 (v0.6.11)
```
```
EXIT=0
'체크섬 불일치' 건수 = 0
네트워크 호출 (2건):
  1  https://github.com/ceo4ever/opal/releases/download/v0.6.11/sha256sums.txt
  2  https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz
```

#### 2.4b RED 대조 — 구형 코드(HEAD)로 동일 명령 재현

```
$ git -C . show HEAD:opal/tools/opal-cli/lib/update.sh > "$W/old/lib/update.sh"
$ git -C . show HEAD:opal/tools/opal-cli/run.sh        > "$W/old/run.sh"
$ env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG="$W/logs/red.net" \
    OPAL_HOME="$W/home/.opal" OPAL_REPO=ceo4ever/opal \
    /bin/bash "$W/old/run.sh" update --to v0.6.11 --force
```
```
[INFO] 로컬 버전: v0.6.10
[INFO] 업데이트: v0.6.10 → v0.6.11
[INFO] 업데이트 버전: v0.6.11
[INFO] 다운로드 URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz     ← 구형: 자동 아카이브
[INFO] tarball 다운로드 중...
  ✓ 다운로드 완료
[INFO] 체크섬 검증 중...
[ERROR] 체크섬 불일치! 다운로드가 손상되었을 수 있습니다.
[ERROR]   기대값: 1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05
[ERROR]   실제값: 463a584266a5483bd477ce7fd6c0c295eac1d787d6b92f186f647fb2e3eb4c19
OLD-CODE EXIT=1
```

| 항목 | 구형 (HEAD) | 신형 (작업트리) |
|------|------------|----------------|
| 다운로드 URL | `archive/refs/tags/v0.6.11.tar.gz` | `releases/download/v0.6.11/opal-v0.6.11.tar.gz` |
| 체크섬 기대값 | `1ae94e27…` (발행 자산) | `1ae94e27…` (발행 자산) |
| 체크섬 실제값 | `463a5842…` (자동 아카이브) | `1ae94e27…` — **일치** |
| exit code | **1 (하드 실패)** | **0** |

> **캡틴이 최초 신고한 하드 실패가 동일 명령·동일 환경에서 재현되고, 수정본에서 해소됨을 실측 확인했다.** F-1 AC 충족.

### 2.5 [T085/L2-fallback-paths] `update.sh` × 자산 부재 폴백 — **PASS** (S-19)

```
$ ru() { env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG=... INSTALLER_LOG=... \
      DL_DENY_PAT="$deny" OPAL_HOME="$W/home/.opal" OPAL_REPO=ceo4ever/opal $xenv \
      /bin/bash opal/tools/opal-cli/run.sh update "$@" < /dev/null; }
```

**(a) 비대화형 + 옵트인 미지정 → 거부 (exit 1)**
```
deny='releases/download/.*/sha256sums\.txt' ; args=--to v0.6.11 --force
[INFO] 로컬 버전: v0.6.10
[INFO] 업데이트: v0.6.10 → v0.6.11
[WARN] 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
[INFO] 다운로드 URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
[INFO] tarball 다운로드 중...
  ✓ 다운로드 완료
[ERROR] 릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 업데이트를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1
exit=1   net(2)
```

**(b) 비대화형 + `OPAL_ALLOW_UNVERIFIED=1` → UNVERIFIED 수렴 (exit 0)**
```
[WARN] 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)
[WARN] [UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행
[INFO] 압축 해제 중... (strip-components=1)
  ✓ 압축 해제 완료
[INFO] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
INSTALLER_INTERCEPTED argv=/var/folders/.../tmp.EfaQFRQNZj/opal-src/scripts/install/macos.sh
  ✓ 업데이트 완료 (v0.6.11)
exit=0   net(2)
```

**(d) 폴백 후 자동 아카이브 재다운로드마저 실패 → 하드 실패 (exit 1)**
```
deny='releases/download/v0\.6\.11/opal-v0\.6\.11\.tar\.gz|archive/refs/tags/v0\.6\.11\.tar\.gz'
[INFO] 다운로드 URL: https://github.com/ceo4ever/opal/releases/download/v0.6.11/opal-v0.6.11.tar.gz
[INFO] tarball 다운로드 중...
curl: (22) The requested URL returned error: 404
[WARN] 릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패
[INFO] 폴백 다운로드 URL: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
curl: (22) The requested URL returned error: 404
[ERROR] tarball 다운로드 실패: https://github.com/ceo4ever/opal/archive/refs/tags/v0.6.11.tar.gz
exit=1   net(3)
```
> (c) 경로(sha는 수신, 자산 tarball만 실패)는 (d)의 첫 단계 로그가 그대로 증명한다 — 폴백 후 `체크섬 검증 중` 미출력.
> **미실행**: `update.sh` × 대화형 프롬프트 동의(pty) 조합. install.sh에서 동일 3분기 코드형을 pty로 실증했고(§2.2c), update.sh는 옵트인/거부 2분기를 실증했다. 나머지 1분기(대화형 y)는 미실행 — 사유: 우선순위상 install.sh 실증으로 대표했다.

### 2.6 [T085/L2-RG-main] `update.sh` × main 브랜치 — **PASS** (S-14)

```
$ env -i PATH="$W/stub:..." HOME="$W/home" DL_LOG="$W/logs/s14u.net" INSTALLER_LOG=... \
    OPAL_HOME="$W/home/.opal" OPAL_REPO=ceo4ever/opal \
    /bin/bash opal/tools/opal-cli/run.sh update --to main --force < /dev/null
```
```
[INFO] 로컬 버전: v0.6.10
[INFO] 업데이트 버전: main
[INFO] 다운로드 URL: https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz
[INFO] tarball 다운로드 중...
  ✓ 다운로드 완료
[WARN] [UNVERIFIED] 'main' 브랜치 업데이트 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다.
[INFO] 압축 해제 중... (strip-components=1)
  ✓ 압축 해제 완료
[INFO] tarball VERSION 각인값 채택: v0.6.11 (API 미사용)
INSTALLER_INTERCEPTED argv=/var/folders/.../tmp.ARC9ii80Pm/opal-src/scripts/install/macos.sh
  ✓ 업데이트 완료 (v0.6.11)
exit=0
네트워크 호출 (1건): https://github.com/ceo4ever/opal/archive/refs/heads/main.tar.gz
```
배너 대조:
```
$ git show HEAD:opal/tools/opal-cli/lib/update.sh | grep -n 'UNVERIFIED.*브랜치'
169:        warn "[UNVERIFIED] '${version}' 브랜치 업데이트 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
$ grep -n 'UNVERIFIED.*브랜치' opal/tools/opal-cli/lib/update.sh
273:            warn "[UNVERIFIED] '${version}' 브랜치 업데이트 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
```
문자열 **완전 동일**. 출력 순서도 동일 — HEAD는 `다운로드 완료` 직후 무조건 분기, 작업트리는 `다운로드 완료` 직후 `case branch)` 분기. 실측 출력 순서(`✓ 다운로드 완료` → `[WARN] [UNVERIFIED] …` → `압축 해제 중`)가 HEAD와 일치.

---

## 3. 미실행 3칸 (`install.ps1` 행) — 사유 + 대체 검증

### 3.1 미실행 사유

| 항목 | 내용 |
|------|------|
| 칸 | `install.ps1` × 릴리즈 태그 / 자산 부재 폴백 / main 브랜치 — **3칸 전부** |
| 시나리오 | S-16 (L3 [SUPERVISOR]), S-18 (pwsh 런타임 등가), S-4의 PowerShell 구문 파싱 |
| 사유 | ① 실행 환경이 macOS(Darwin 25.5.0)이며 **Windows 환경이 없다** ② `pwsh`·`powershell` **둘 다 미설치** — `command -v pwsh` / `command -v powershell` 모두 결과 없음. ③ PowerShell 설치는 환경 변경이므로 본 Step 범위 밖(소유자 결정 사항) |
| 확인 명령 | `for t in pwsh powershell; do printf '%-12s %s\n' "$t" "$(command -v $t \|\| echo MISSING)"; done` → `pwsh MISSING` / `powershell MISSING` |
| 판정 | **SKIP** — Pass 아님. S-16은 [SUPERVISOR] 마커 시나리오로 **PM/캡틴에 반환**한다 |

> TEST-SCENARIO.md §S-16 "미보유 시 대체 경로"와 PLAN §3.6.2 "Windows 대체 검증"이 이 처리를 명시적으로 허용한다(F-6 AC).

### 3.2 대체 검증 ① — PowerShell 구문 파싱

**미수행.** `pwsh -NoProfile -Command "[ScriptBlock]::Create((Get-Content -Raw ./scripts/install.ps1)) | Out-Null"` 는 인터프리터 부재로 실행 불가하다.
파서 없이 구문 정합을 주장할 수 없으므로 **추정하지 않는다**. 이 항목은 미확정으로 남긴다.

대신 수행한 정적 검사(구문 무결성을 대신하지는 않는다):
```
$ grep -n -- '--strip-components\|StripComponents' scripts/install.ps1
267:function Get-DlStripComponents {
270:        tarball 최상위 구조를 판정하여 --strip-components 값(0|1)을 반환한다 (DL-CONTRACT 085).
461:    $strip   = Get-DlStripComponents -TarballPath $TarballPath
463:    if ($strip -eq 1) { $tarArgs += @('--strip-components', '1') }
$ grep -n -F 'archive/refs/tags' scripts/install.ps1
195:    $script:DlUrl  = "https://github.com/$OpalRepo/archive/refs/tags/$($script:OpalVersion).tar.gz"   ← Set-DlFallback 내부 1회
$ head -70 scripts/install.ps1 | grep -c 'DL-CONTRACT (085)'
2
```
조건부 인자는 문자열 보간이 아닌 **배열 splatting**(`$tarArgs += @('--strip-components','1')` → `& tar @tarArgs`)으로 구성되어 있어 빈 인자 전개 오류(H-7의 실패 양상)가 구조적으로 발생하지 않는다 — **정적 확인**이며 런타임 실증은 아니다.

### 3.3 대체 검증 ② — `Get-DlStripComponents`·`Get-DlAssetName` 판정식 등가 (실 데이터 입력)

PowerShell 런타임이 없으므로 **함수 호출은 하지 못했다.** 대신 두 함수가 소비하는 **실제 입력**(실 릴리즈 tarball의 `tar -tzf` 목록, 실 `sha256sums.txt`)에 대해
PowerShell 코드가 계산하는 중간값(`rootFiles.Count`, `tops.Count`, `cols[1]`)을 실측하고 판정식을 적용해 bash 구현과 대조했다.

**`Get-DlStripComponents`** — 판정식 `rootFiles.Count -eq 0 -and tops.Count -eq 1 → 1, else 0`

| 입력 (실 다운로드본) | entries | rootFiles | tops | PS 판정 | bash 판정 | 대조 |
|---|---|---|---|---|---|---|
| `opal-v0.6.11.tar.gz` (발행 자산) | 981 | 6 | 13 | **0** | **0** | 일치 |
| `v0.6.11-archive.tar.gz` (자동 아카이브) | 982 | 0 | 1 | **1** | **1** | 일치 |
| `main-archive.tar.gz` (브랜치) | 982 | 0 | 1 | **1** | **1** | 일치 |

기대값 `0 / 1 / 1` 충족. 두 구현의 연산 정의도 항목별로 동형:

| 연산 | bash (`_dl_detect_strip`) | PowerShell (`Get-DlStripComponents`) | 동형 |
|------|--------------------------|--------------------------------------|------|
| 목록 취득 | `tar -tzf "$1"` | `& tar -tzf $TarballPath \| Where-Object { $_ }` | O (동일 외부 명령) |
| 빈 줄 제거 | `NF == 0 { next }` | `Where-Object { $_ }` | O |
| 루트 직속 판정 | `$0 !~ /\//` → `root++` | `$_ -notmatch '/'` → `$rootFiles` | O |
| 최상위 세그먼트 | `awk -F/ { tops[$1]=1 }` | `($_ -split '/', 2)[0] \| Sort-Object -Unique` | O |
| 반환식 | `(root == 0 && n == 1) ? 1 : 0` | `if ($rootFiles.Count -eq 0 -and $tops.Count -eq 1) { 1 } else { 0 }` | O |
| 목록 실패 처리 | 파이프 실패 → 호출자 `\|\| true` → 빈 문자열 (→ §5 O-5) | `throw`(exit≠0 또는 entries 0) | **차이** (PS가 더 엄격) |

**`Get-DlAssetName`** — 판정식 `행 공백분할 → cols.Count>=2 → cols[1]에서 '^\*' 제거 → '*.tar.gz' like → 첫 매치 반환`

| 입력 | PS 판정 | bash 판정 | 대조 |
|---|---|---|---|
| `sha256sums.txt` (실 릴리즈) | `opal-v0.6.11.tar.gz` | `opal-v0.6.11.tar.gz` | 일치 |
| `sha256sums-binmode.txt` (`*` 접두) | `opal-v0.6.11.tar.gz` | `opal-v0.6.11.tar.gz` | 일치 |
| `sha256sums-noentry.txt` | `(공백)` | `(공백)` | 일치 |
| `sha256sums-blankhash.txt` | `(공백)` | `(공백)` | 일치 |

> **한계 명시**: 위 표는 *알고리즘 판정식*을 실 입력에 적용한 결과다. PowerShell 파서·`Set-StrictMode 3.0`·`$ErrorActionPreference='Stop'` 하의 실제 런타임 거동(예: `$LASTEXITCODE` 시점, `-split` 정규식 해석)은 **검증되지 않았다.** S-18은 여전히 Skip이다.

### 3.4 대체 검증 ③ — bash ↔ PowerShell 규약 8항목 대조표 (PLAN §3.0)

| # | 규약 항목 | `install.sh` / `update.sh` (bash) | `install.ps1` (PowerShell) | 판정 |
|---|----------|-----------------------------------|---------------------------|------|
| 1 | 자산 존재 판정 신호 | `sha256sums.txt` 다운로드 성공 여부 단일 신호 (`curl --fail`) | 동일 — `Invoke-RestMethod … -ErrorAction Stop` try/catch (`:249`) | **일치** |
| 2 | 자산명 파생 | `_dl_asset_name` — sha 파일 파일명 컬럼에서 첫 `.tar.gz`, `*` 접두 제거 | `Get-DlAssetName` (`:162`) — 동일 로직 | **일치** (§3.3 실측 대조) |
| 3 | 로컬명 = 자산명 | `OPAL_TARBALL_NAME="${asset}"` / `_DL_NAME="$asset"` | `$script:DlName = $asset` (`:263`) + `# [MUST] 로컬명 = 발행 자산명` | **일치** |
| 4 | 폴백 3동작 (URL 재지정 / 로컬명 분리 / sha 폐기) | `_dl_fallback`: `archive/refs/tags` URL + `opal-{ver}-archive.tar.gz` + `rm -f $SHA_FILE` | `Set-DlFallback` (`:185`): 동일 3동작 + `Remove-Item -LiteralPath $script:DlShaFile` | **일치** |
| 5 | 폴백 로그 문구 | `릴리즈 자산 미사용 폴백: 릴리즈 자산 없음 (sha256sums.txt 조회 실패)` / `… sha256sums.txt 형식 이상 (.tar.gz 항목 없음)` / `… 릴리즈 자산 다운로드 실패` | `[OPAL] 릴리즈 자산 미사용 폴백: 릴리즈 자산 없음` / `… sha256sums.txt 형식 이상` / `… 릴리즈 자산 다운로드 실패` | **미세 드리프트** — 접두 `[OPAL]` 유무, 괄호 상세구 2건 누락 (→ §5 O-4) |
| 6 | 체크섬 3모드 | `verify` / `unverified` / `branch` + `*)` 하드 실패 | `switch ($script:DlMode)`: `'verify'` / `'unverified'` / `'branch'` / `default { throw }` (`:371-434`) | **일치** |
| 6a | verify — 고정문자열 매칭 | `grep -F` 전필터 + awk `$2` 정확 일치 | 정규식 미사용 — `$name -eq $script:DlName` 컬럼 정확 일치 (`:384`) | **일치** |
| 6b | verify — 항목 부재/빈 기대값 | 2개 분리 error, 둘 다 하드 실패 | 단일 `throw` (`:392`)로 통합, 하드 실패 | **행위 일치** (메시지 세분도만 차이) |
| 6c | unverified 3분기 | 옵트인 `OPAL_ALLOW_UNVERIFIED=1` / 비대화형 거부(`! -t 0` \|\| `OPAL_AUTO_INSTALL=1`) / 프롬프트 기본 N | 옵트인 `$env:OPAL_ALLOW_UNVERIFIED -eq '1'` / 비대화형 거부(`$env:OPAL_AUTO_INSTALL -eq '1'` -or `-not [Environment]::UserInteractive`) / `Read-Host` 기본 N | **일치** |
| 6d | branch | 배너는 상위에서 1회, 여기선 "검증 대상 아님" | 동일 — 배너는 `Invoke-OpalInstall`, 여기선 `브랜치 설치 — SHA-256 무결성 검증 대상 아님` (`:424`) | **일치** |
| 7 | strip 판정식 | `_dl_detect_strip` → 조건부 `--strip-components=1` | `Get-DlStripComponents` → 배열 splatting `if ($strip -eq 1) { $tarArgs += @('--strip-components','1') }` (`:463`) | **일치** (§3.3 실측 대조) |
| 8 | 추출 사후조건 | `[[ ! -f VERSION \|\| ! -d opal ]]` → error | `Test-Path VERSION` -and `Test-Path opal` → `throw` (`:483-487`) | **일치** |
| 9 | DL-CONTRACT 각인 | 헤더 각인 존재 (install.sh 2건 / update.sh 3건) | 헤더 각인 존재 (2건) | **일치** |
| 10 | TLS 강제 | `curl --proto '=https' --tlsv1.2` 전수 | `Set-DlSecurityProtocol` (Tls12, 가용 시 Tls13 bor) — `Resolve-DownloadPlan`·`Fetch-Tarball` 다운로드 직전 호출 | **일치** (HEAD 대비 개선: Tls13 열거 부재 환경에서 즉시 throw 하던 결함 제거) |

**드리프트 판정: 8항목 중 7항목 완전 일치, 1항목(#5 로그 문구) 미세 드리프트.** 행위 계약(#1~4·6~8·10)에는 드리프트가 없다.

---

## 4. L1 단위·정적 검증 (9칸 보강)

### 4.1 계약 테스트 26케이스 — `scripts/tests/test_download_contract.sh`

```
$ bash scripts/tests/test_download_contract.sh
```
```
== (가) 헬퍼 함수 계약 (TC-A*, S-1·S-2·S-6) ==
[PASS] TC-A1  DL-CONTRACT 헬퍼 정의 존재 (update.sh 4종 / install.sh 2종+계획함수)
[PASS] TC-A2  update.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1
[PASS] TC-A3  install.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1
[PASS] TC-A4  install.sh·update.sh의 _dl_detect_strip 본문 동일
[PASS] TC-A5  update.sh _dl_asset_name(정상) = opal-v0.6.11.tar.gz
[PASS] TC-A6  update.sh _dl_asset_name(binary mode '*' 접두) = opal-v0.6.11.tar.gz
[PASS] TC-A7  update.sh _dl_asset_name(.tar.gz 항목 없음) = 공백
[PASS] TC-A8  install.sh _dl_asset_name 3입력 판정
[PASS] TC-A9  install.sh·update.sh의 _dl_asset_name 본문 동일
[PASS] TC-A10 _dl_sha256 — sha256sum만 있는 PATH에서 기준 해시 반환
[PASS] TC-A11 _dl_sha256 — shasum만 있는 PATH에서 동일 해시 반환
[PASS] TC-A12 _dl_sha256 — 둘 다 없는 PATH에서 실패 반환(exit≠0, stdout 공백)
== (나) 추출·체크섬 행위 (TC-B*, S-13·S-5) ==
[PASS] TC-B1  extract_to_tmp(prefix 없는 아카이브) → 루트에 VERSION·opal/ 존재
[PASS] TC-B2  extract_to_tmp(prefix 있는 자동 아카이브) → 루트에 VERSION·opal/ 존재
[PASS] TC-B3  extract_to_tmp(구조 위반 아카이브) → 하드 실패(exit≠0)
[PASS] TC-B4  verify_checksum(정상 주입) → exit 0 + 검증 완료 출력
[PASS] TC-B5  verify_checksum(항목 부재) → 하드 실패(exit≠0)
[PASS] TC-B6  verify_checksum(빈 해시) → 하드 실패(exit≠0)
[PASS] TC-B7  install.sh verify_checksum 본문에 네트워크 호출·경고후통과 경로 부재
[PASS] TC-B8  update.sh 체크섬 분기 — 빈 기대값 무음 통과 0건 + 고정문자열 매칭
== (다) 구형 잔존 정적 검사 (TC-C*, S-3) ==
[PASS] TC-C1  install.sh에 'opal.tar.gz' 리터럴 0건
[PASS] TC-C2  2개 bash 파일에 비고정문자열 grep 매칭 0건
[PASS] TC-C3  3파일 각각 코드 라인의 'archive/refs/tags' 정확히 1회
[PASS] TC-C4  3파일 각각 releases/download 자산 URL 구성 라인 ≥1
[PASS] TC-C5  3파일에 무조건 고정 '--strip-components' 0건
[PASS] TC-C6  3파일 헤더에 'DL-CONTRACT (085)' 각인 존재

========================================================
PASS: 26 | FAIL: 0 | SKIP: 0
========================================================
verdict: ALL PASS
EXIT=0
```
> **RED 테스트 파일은 읽기·실행만 했고 수정하지 않았다** (red-first.md §3 준수).

### 4.2 S-1 / S-2 / S-6 — 실 다운로드 픽스처 재확인 (계약 테스트는 `git archive` 픽스처 사용)

```
$ # 함수 정의 구간만 awk로 추출해 임시 하네스에 source (install.sh는 최상위 자동 실행이 있어 직접 source 불가)
$ /bin/bash $W/h1.sh
[scripts/install.sh] release-asset=0  tag-archive=1  main-archive=1   exit=0
[lib/update.sh]      release-asset=0  tag-archive=1  main-archive=1   exit=0

$ diff <(xf install.sh _dl_detect_strip) <(xf update.sh _dl_detect_strip) && echo 동일
_dl_detect_strip: 문자 단위 동일
$ diff <(xf install.sh _dl_asset_name)  <(xf update.sh _dl_asset_name)  && echo 동일
_dl_asset_name: 문자 단위 동일

$ /bin/bash $W/h2.sh
[install.sh] normal=[opal-v0.6.11.tar.gz] binmode=[opal-v0.6.11.tar.gz] noentry=[]   exit=0
[update.sh]  normal=[opal-v0.6.11.tar.gz] binmode=[opal-v0.6.11.tar.gz] noentry=[]   exit=0

$ # S-6: PATH를 심볼릭 링크 스텁 디렉토리로 제한 (awk + 대상 해시 도구만 노출)
PATH=stub-a   exit=0 stdout=[1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05]   # sha256sum만
PATH=stub-b   exit=0 stdout=[1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05]   # shasum만
PATH=stub-c   exit=1 stdout=[]                                                                   # 둘 다 없음
기대값(sha256sums.txt): 1ae94e27edb74bad14d060a5ed997558198cb3b0d75cfd75204ef9743782cf05
```

### 4.3 S-5 — 무음 통과 제거 (실 릴리즈 자산 + 실 sha 파일 주입)

```
$ # verify_checksum을 DL-CONTRACT 전역 계약으로 구동 (OPAL_CHECKSUM_MODE=verify, 네트워크 0회)
----- 정상 (양성대조) (sha256sums.txt) -----
[opal] SHA-256 검증 중...
opal-v0.6.11.tar.gz: OK
[opal] SHA-256 체크섬 검증 완료
exit=0
----- 항목 부재 (sha256sums-noentry.txt) -----
[opal] ERROR: sha256sums.txt에 opal-v0.6.11.tar.gz 항목 없음 — DL-CONTRACT 위반. 설치를 중단합니다.
exit=1
----- 빈 기대값 (sha256sums-blankhash.txt) -----
[opal] ERROR: sha256sums.txt에 opal-v0.6.11.tar.gz 항목 없음 — DL-CONTRACT 위반. 설치를 중단합니다.
exit=1
```
> 두 결함 입력 모두 **하드 실패**. 경고 후 통과하는 경로는 존재하지 않는다.
> 관측: 빈 기대값 입력은 전용 분기(`체크섬 기대값 파싱 실패`)가 아니라 항목 부재 분기로 수렴한다 — 파일명 컬럼이 `$2`이므로 해시 컬럼이 비면 `$2`가 비고 정확 일치에 실패하기 때문. **AC(하드 실패)는 충족**이며, 전용 분기는 방어적 이중화로 남는다 (→ §5 O-2).

### 4.4 S-3 / S-4 — 잔존 0건 · 구문 무결성

```
$ grep -n -F 'archive/refs/tags' <3파일>   (주석 제외)
scripts/install.sh:212                     TARBALL_URL=".../archive/refs/tags/${OPAL_VERSION}.tar.gz"     ← _dl_fallback 내부
scripts/install.ps1:195                    $script:DlUrl = ".../archive/refs/tags/$(...).tar.gz"          ← Set-DlFallback 내부
opal/tools/opal-cli/lib/update.sh:76       _DL_URL=".../archive/refs/tags/${2}.tar.gz"                     ← _dl_fallback 내부
→ 각 파일 정확히 1회, 전부 폴백 분기 내부

$ grep -c -F 'opal.tar.gz' scripts/install.sh                              → 0
$ grep -n 'grep ' <bash 2파일> | grep '\$' | grep -v -- '-F'               → (없음) 비고정문자열 매칭 0건
$ grep -n -- '--strip-components' <3파일>
scripts/install.sh:422                     tar … --strip-components=1      ← `if [[ "${strip_n}" -eq 1 ]]` 내부
opal/tools/opal-cli/lib/update.sh:337      tar … --strip-components=1      ← `if [[ "$strip_n" -eq 1 ]]` 내부
scripts/install.ps1:463                    $tarArgs += @('--strip-components','1')  ← `if ($strip -eq 1)` 내부
→ 무조건 고정 인자 0건

$ for f in <3파일>; do head -70 "$f" | grep -c 'DL-CONTRACT (085)'; done   → 2 / 2 / 3   (전부 ≥1)

$ bash -n scripts/install.sh                        → exit 0
$ bash -n opal/tools/opal-cli/lib/update.sh         → exit 0
$ command -v pwsh; command -v powershell            → 둘 다 MISSING → PowerShell 구문 파싱 Skip
```

### 4.5 S-13 — 추출 사후조건 (실 아카이브 2형식)

```
$ tar -xzf opal-v0.6.11.tar.gz    -C ex-0                        # strip 0
$ tar -xzf v0.6.11-archive.tar.gz -C ex-1 --strip-components=1   # strip 1
opal-v0.6.11.tar.gz      strip=0  VERSION=O  opal/=O  VERSION내용=[v0.6.11]
v0.6.11-archive.tar.gz   strip=1  VERSION=O  opal/=O  VERSION내용=[v0.6.11]
```
> 실 스크립트 경로에서도 동일하게 확인됨 — §2.1(발행 자산, strip 0)·§2.2(자동 아카이브, strip 1) 양쪽에서
> `추출 완료` 후 `tarball VERSION 각인값 채택: v0.6.11`가 출력되었다(= `adopt_stamped_version`이 추출 루트의 `VERSION`을 읽어 `v0.6.11`을 얻었다는 증거).

---

## 5. 발견했으나 고치지 않은 결함·관측 (보고 전용)

> 하네스 Guard 준수: 소스 3파일·RED 테스트 파일을 수정하지 않았다. 아래는 **보고만** 한다.

| ID | 심각도 | 위치 | 내용 | 회귀 여부 |
|----|--------|------|------|----------|
| **O-1** | 낮음 (표시 전용) | `install.sh:234-240`, `install.ps1:220-227` | DRY-RUN 조기 반환이 **버전 종류와 무관하게** `archive/refs/heads/{version}.tar.gz` + `mode=branch`를 출력한다. `OPAL_DRY_RUN=1 OPAL_VERSION=v0.6.11`에서 `…/archive/refs/heads/v0.6.11.tar.gz`라는 실재하지 않는 URL이 안내된다 | **경미한 회귀**. HEAD는 모듈 스코프에서 `v*`→`archive/refs/tags/…`를 구성해 DRY-RUN에서도 태그 URL을 출력했다. 실제 다운로드는 없으므로 기능 영향 0, 안내 정확도만 저하 |
| **O-2** | 정보 | `install.sh:355-359`, `update.sh:289-293` | "체크섬 기대값 파싱 실패" 전용 분기가 실질적으로 **도달 불가**하다. 파일명은 `$2`, 기대값은 `$1`이므로 `$2`가 존재하면 `$1`은 항상 비지 않는다. 빈 해시 입력은 앞선 "항목 없음" 분기로 수렴 | 신규. **AC 위반 아님**(양쪽 다 하드 실패). 방어적 이중화로 유지 타당 |
| **O-3** | 정보 | `update.sh:282-293` | verify 모드의 "항목 부재" 하드 실패도 통합 흐름에서는 **구조적으로 도달 불가**. `_dl_asset_name`이 sha 파일의 동일 컬럼에서 자산명을 파생하므로 정확 일치가 항상 성립 | 신규. 계약 방어선으로서 유지 타당. 단, 이 분기의 실증은 함수 단위 주입(TC-B5)에만 의존한다 |
| **O-4** | 낮음 | `install.ps1:184-206` | 폴백 사유 문구가 bash 2경로와 미세 드리프트. bash `릴리즈 자산 없음 (sha256sums.txt 조회 실패)` ↔ ps1 `릴리즈 자산 없음`; bash `sha256sums.txt 형식 이상 (.tar.gz 항목 없음)` ↔ ps1 `sha256sums.txt 형식 이상`. 접두 `[OPAL] ` 유무도 다름 | 신규. PLAN §3.0 규약 8항목 중 #5(폴백 로그 문구) 미충족. 행위 영향 없음 |
| **O-5** | 낮음 | `install.sh:418`, `update.sh:334` | `strip_n="$(_dl_detect_strip … \|\| true)"` — 목록 조회가 실패하면 `strip_n`이 **빈 문자열**이 되고, `[[ "" -eq 1 ]]`는 오류 없이 false가 되어 **무음으로 strip=0 경로**를 탄다. (실측: 비-gzip 파일 입력 시 `strip_n=[]`, 분기 판정 `strip=0 경로`, rc=0) | 신규. 후속 추출 사후조건(`VERSION`·`opal/`)이 결국 하드 실패로 잡으므로 **무음 진행은 발생하지 않는다**. 다만 오류 메시지가 "구조 이상"으로 표시되어 실제 원인(목록 조회 실패)을 가린다. PowerShell `Get-DlStripComponents`는 이 경우 `throw`하여 더 엄격하다 |
| **O-6** | 정보 | `update.sh:385` | `OPAL_AUTO_INSTALL=1 … bash "$installer"` — 인스톨러 호출이 PATH의 `bash`를 사용한다(본 검증의 seam 1이 여기 걸렸다). 보안상 실질 위험은 낮으나 절대경로 사용이 더 견고하다 | 사전존재 (HEAD 동일) |

---

## 6. 코드 품질 · 보안

### 6.1 코드 품질

| # | 검사 | 명령 | 결과 |
|---|------|------|------|
| 1 | 린트 (bash) | `shellcheck -f gcc scripts/install.sh` | **note 1건** — `:488:10 [SC2016] Expressions don't expand in single quotes` (`'$Format:'` 리터럴 판별 — 의도된 코드) |
| 1 | 린트 (bash) | `shellcheck -f gcc opal/tools/opal-cli/lib/update.sh` | **note 1건** — `:361:17 [SC2016]` (동일 사유) |
| 1a | 린트 기준선 대조 | HEAD 사본에 동일 실행 | HEAD도 각 1건 동일 [SC2016] (`install.sh:352`, `update.sh:222`) → **신규 지적 0건** |
| 1b | error 레벨 | `shellcheck -S error <2파일>` | **exit 0, 0건** (Step 1·3 완료 기준 충족) |
| 2 | 타입 체크 | 해당 없음 (셸·PowerShell) | — |
| 3 | 포맷터 | 해당 없음 | — |
| 4 | 구문 검사 | `bash -n scripts/install.sh` / `bash -n opal/tools/opal-cli/lib/update.sh` | **2/2 exit 0** |
| 4a | 구문 검사 (PS) | `pwsh -NoProfile -Command "[ScriptBlock]::Create(...)"` | **Skip** — `pwsh`·`powershell` 미설치 |

`shellcheck` 버전: 0.11.0.

### 6.2 보안

| # | 항목 | 명령·근거 | 결과 |
|---|------|----------|------|
| 1 | 하드코딩 시크릿 스캔 | `grep -nEi 'api[_-]?key\|secret\|passwd\|password\|PRIVATE KEY\|ghp_\|github_pat_\|AKIA[0-9A-Z]{16}\|Bearer ' <3파일>` | **0건** (파일별 0/0/0) |
| 2 | .gitignore 확인 | `.gitignore` — `.opal/*`(2행), `.env`(25행). `git status --short` = 변경 3파일 + 신규 테스트 1 + 태스크 폴더 | **민감 파일 추적 없음.** 검증 산출물은 전부 `$W`(스크래치패드)에 생성했고 저장소에 남기지 않았다 |
| 3 | 무결성 검증 우회 경로 신규 0건 | `grep -cE '검증 건너\|graceful skip' <3파일>` → 0/0/0. `verify` 분기 내 `return 0` → install.sh 0건 / update.sh 0건. `case`에 `*)`(bash)·`default`(ps1) 하드 실패 분기 존재 | **0건 — verify 모드에 skip/warn-continue 경로 부재** |
| 4 | 비대화형 기본 거부(fail-closed) 유지 | 3파일 전부에 3분기 존재(§3.4 #6c). 실측: install.sh 비대화형 → exit 1 (§2.2a), update.sh 비대화형 → exit 1 (§2.5a) | **유지 확인 (실행 증거 2건)** |
| 5 | 신규 다운로드 TLS 강제 | `install.sh` curl 5개소 전부 `--proto '=https' --tlsv1.2` (`:89 :95 :254 :299 :315`). `update.sh` curl 5개소 전부 동일 (`:98 :179 :185 :252 :258`). `install.ps1`은 `Set-DlSecurityProtocol`(Tls12, 가용 시 Tls13)을 `Resolve-DownloadPlan:239`·`Fetch-Tarball:317`에서 다운로드 직전 호출 | **전수 적용.** 단 `install.ps1` `Resolve-DefaultVersion`(`:77 :83`)의 API 호출에는 TLS 설정이 선행하지 않는다 — **HEAD 동일(사전존재)**, 신규 도입 아님 |

---

## 7. 네트워크 사용 내역

실 다운로드를 사용했다. 전부 `github.com` / `api.github.com` 읽기 전용 GET이며, 쓰기·인증 호출은 없다.

| 구분 | 건수 | 용처 |
|------|------|------|
| 사전 조사 (직접) | 5 | 릴리즈 목록 API 1 · v0.5.0 자산 유무 확인 HEAD 2 · git tree API 2 (v0.5.0 / v0.6.11 루트에 `VERSION` 존재 여부) |
| 픽스처 다운로드 (직접) | 4 | `sha256sums.txt`, `opal-v0.6.11.tar.gz`, `archive/refs/tags/v0.6.11.tar.gz`, `archive/refs/heads/main.tar.gz` |
| 시나리오 실행 (스텁 경유 기록) | 30 | `sha256sums.txt` ×12 · `archive/refs/tags/v0.6.11.tar.gz` ×9 · `releases/download/…/opal-v0.6.11.tar.gz` ×6 · `archive/refs/heads/main.tar.gz` ×2 · `api…/releases/latest` ×1 |
| **합계** | **약 39** | |

DRY-RUN 칸(§2.3b) 3케이스는 네트워크 호출 **0건**으로 기록되었다.

---

## 8. 시나리오별 판정 색인

| 시나리오 | 계층 | 판정 | 근거 절 |
|---------|------|------|--------|
| S-1 strip 판정 3형식 | L1 | PASS | §4.1 TC-A2·A3·A4, §4.2 |
| S-2 자산명 파생 | L1 | PASS | §4.1 TC-A5~A9, §4.2 |
| S-3 구형 경로 잔존 0건 | L1 | PASS | §4.1 TC-C1~C6, §4.4 |
| S-4 구문 무결성 | L1 | PASS (부분 Skip) | §4.4 — bash 2/2 exit 0 / PowerShell 파싱 Skip(기대 결과가 명시 허용) |
| S-5 무음 통과 제거 | L1 | PASS | §4.3, §4.1 TC-B4~B8 |
| S-6 해시 도구 이식성 | L1 | PASS | §4.2, §4.1 TC-A10~A12 |
| S-7 install.sh 릴리즈 태그 | L2 | PASS | §2.1 |
| S-8 손상 tarball 거부 | L2 | PASS | §2.1b |
| **S-9 opal-cli update** | L2 | **PASS** 🎯 | §2.4 + RED 대조 §2.4b |
| S-10 무중단 폴백 | L2 | PASS | §2.2c |
| S-11 비대화형 거부 | L2 | PASS | §2.2a·2.2b, §2.5a |
| S-12 폴백 시 잘못된 비교 금지 | L2 | PASS | §2.2c 로그검사, §2.2d(c) |
| S-13 추출 사후조건 2형식 | L2 | PASS | §4.5, §2.1·§2.2b |
| S-14 main 브랜치 회귀 | L2 | PASS | §2.3, §2.6 |
| S-15 DRY-RUN 네트워크 0 | L2 | PASS | §2.3b |
| S-16 Windows 실측 [SUPERVISOR] | L3 | **SKIP** | §3.1 — Windows·PowerShell 부재. 대체 검증 3종 §3.2~3.4. **PM/캡틴 반환 대상** |
| S-17 TEST.md 9칸 완결성 | L1 | PASS (자기검사 한계 명시) | 본 문서 §1·§2·§3 — 9칸 전부 판정 기재, 미실행 3칸에 사유+대체 검증 기재 |
| S-18 PowerShell 런타임 등가 | L1 | **SKIP** | §3.1 — `pwsh` 미설치. 판정식 등가 대조는 §3.3에 기재하되 **런타임 미검증**임을 명시 |
| S-19 폴백 4경로 완전성 | L2 | PASS | §2.2d (install.sh 4/4), §2.5 (update.sh 3/4 — 대화형 y 1분기 미실행) |

**집계: PASS 16 / SKIP 2 (S-16·S-18) / FAIL 0**

---

## 9. 최종 판정

**All Pass (조건부)** — 실행 가능한 6칸 전부와 L1/L2 시나리오 16건이 실 데이터·실 프로세스로 PASS했고, 실패 0건이다.
`install.ps1` 행 3칸은 **환경 부재로 SKIP**이며, TEST-SCENARIO.md §S-16과 PLAN §3.6.2·D-9 §F-6 AC가 허용하는 "사유 + 대체 검증 3종" 형식으로 기록했다.
S-16은 [SUPERVISOR] 시나리오이므로 **Windows 실측은 캡틴 확인 사항으로 PM에 반환**한다.

목표달성 시나리오 S-9는 구형 코드에서의 실패 재현(`실제값 463a5842…`)과 수정본에서의 성공(exit 0)을 **같은 명령·같은 환경에서 대조**하여 확정했다.

---

## 변경이력

- v1.0 2026-08-07 11:5x KST: 신규 작성 — 9칸 매트릭스 실측 기록 (opal-test-agent, Step 5) (085)

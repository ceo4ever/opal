# PLAN: 인스톨러 3종 릴리즈-자산 다운로드 정합 (Option A)

> 작성일: 2026-07-21 | 입력: TASK.md (ANALYSIS.md 없음 → 코드 직접 분석)
> 모드: Multi-Feature (5개 기능) | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

인스톨러 3종(`opal-cli update` / `install.sh` / `install.ps1`)이 v* 릴리즈 업데이트 시 **GitHub 자동생성 소스아카이브**(`archive/refs/tags/*`, 최상위 prefix `opal-X.Y.Z/` 있음)를 다운로드하면서 **릴리즈 자산 기준 `sha256sums.txt`**(워크플로우가 `git archive HEAD`로 만든 prefix 없는 `opal-vX.Y.Z.tar.gz`)로 검증하여 구조적(재현성 100%) 체크섬 불일치로 하드 실패한다. 캡틴 확정 Option A에 따라 **다운로드 대상을 릴리즈 자산으로 통일**하고, 다운로드 소스에 맞춰 추출 prefix 분기·폴백·검증을 정합화한다. 릴리즈 자산 404 시 기존 아카이브 폴백을 UNVERIFIED로 유지하여 회귀를 방지한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | update.sh 릴리즈-자산 정합 (다운로드·추출·폴백·검증) | R1, R4(update), R5, R6, R7 | P0 | 없음 |
| F-002 | install.sh 릴리즈-자산 정합 (다운로드·추출·폴백·검증) | R2, R4(install), R5, R6, R7 | P0 | 없음 |
| F-003 | install.ps1 릴리즈-자산 정합 (다운로드·추출·폴백·검증) | R3, R5, R6, R7 | P0 | 없음 |
| F-004 | 정합 검증 테스트 추가 | R8 | P0 | F-001, F-002, F-003 |
| F-005 | 재릴리즈 안내 + 변경이력 갱신 | R9, R10 | P1 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (update.sh) ─┐
F-002 (install.sh) ─┼─→ F-004 (테스트)
F-003 (install.ps1)─┘         │
        └────────────────────┴─→ F-005 (안내·변경이력)
```

F-001·F-002·F-003은 독립 파일이라 병렬 가능. F-004(테스트)는 세 파일의 정합 계약을 검증하므로 코드 수정 후 실행. F-005는 실제 수정 내용을 반영하므로 최종.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | 다운로드 대상 전환 (3종) | v* 시 릴리즈 자산 URL(`releases/download/${v}/opal-${v}.tar.gz`)을 1순위로 받아야 함 — 아카이브 URL 잔존 시 불일치 재발 | P0 | L1(정적 계약) + L2(mechanism) | S-1 |
| H-2 | **추출 prefix 분기 (핵심)** | 자산=prefix 없음 → `--strip-components=1` 금지 / 아카이브 폴백=prefix 있음 → strip 적용. 무분기 시 자산 추출 조용히 깨짐(`.claude/` 등 최상위 유실) | P0 | L1(정적) + L2(mechanism: strip이 무-prefix tarball 최상위 파일 유실 실증) | S-3 |
| H-3 | 검증 파일명 매칭 (install.sh) | 로컬 tarball을 `opal-${v}.tar.gz`로 저장해야 sha256sums.txt token/`shasum -c --ignore-missing`와 매칭. 현행 `opal.tar.gz`는 token 불일치로 검증이 **조용히 skip**됨(self-confirming) | P0 | L1(정적) + L2(파일명 실증) | S-4 |
| H-4 | 폴백·UNVERIFIED 경로 (3종) | 자산 404 폴백은 기존 무결성 배너·`OPAL_ALLOW_UNVERIFIED`·비대화형 거부 재사용해야 함. 소스 기반으로 분기 전환 시 UNVERIFIED 은닉 위험 | P0 | L1(정적 계약) | S-2 |
| H-5 | 회귀 — main/브랜치/SHA 경로 | 비-v* 경로는 기존 `archive/refs/heads` + strip + UNVERIFIED 배너 그대로 유지해야 함 | P0 | L1(정적) + L3(dry-run) | S-5 |
| H-6 | bash 3.2 / PS 5.1 호환 | 연관배열·mapfile 미사용(bash), `Join-Path` 다중인자 미사용(PS 5.1), 소스 추적 변수는 case/문자열 비교 | P1 | L1(정적 문법 검사) | S-7 |
| H-7 | 보안 — 시크릿·.gitignore | 변경 파일에 하드코딩 토큰 없음, 사용자 데이터(identity/.venv/.env) .gitignore 유지 | P1 | L1(스캔) | S-6 |

**RED-first 판정**: H-1·H-2·H-3(정적 계약 시나리오 S-1·S-3·S-4)은 **RED-first 강제**. 현행 코드는 아카이브 URL·무조건 strip·`opal.tar.gz` 저장이므로 정합 계약 grep 테스트가 자연 RED → 구현 후 GREEN. 이 영역은 "다운로드-검증-추출이 서로 다른 산출물을 비교해도 에러 없이 통과(install.sh) 또는 조용히 깨짐(추출)"하는 **self-confirming 위험 영역**이므로 RED-first가 필수다. 상세는 TEST-SCENARIO.md §1·§0.

---

## 2. 기능별 분석

### F-001: update.sh 릴리즈-자산 정합

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `opal/tools/opal-cli/lib/update.sh` | `opal-cli update` 서브커맨드 — tarball 재다운로드·검증·추출·재설치 | 수정 |
| 환경(참조) | `.github/workflows/release.yml` | 릴리즈 자산·sha256sums.txt 생성 방식 (변경 없음) | 참조 |

#### 2.1.2 현재 구현
- tarball URL 결정 `update.sh:127-133`: v*이면 `archive/refs/tags/${version}.tar.gz`, main이면 `archive/refs/heads/main.tar.gz` — **둘 다 GitHub 소스아카이브(prefix 있음)**.
- 다운로드 `update.sh:161`: `curl ... -o "$tarball_path"` (로컬명 `opal.tar.gz`, `update.sh:160`).
- UNVERIFIED 배너 `update.sh:168-170`: `version != v*`이면 무결성 배너.
- 검증 `update.sh:172-205`: `version == v*`일 때 `releases/download/${version}/sha256sums.txt` 받아 `grep "opal-${version}.tar.gz"` token으로 기대 해시 추출→비교. sha256sums.txt 부재 시 `OPAL_ALLOW_UNVERIFIED`/비대화형 거부/대화형 prompt.
- 추출 `update.sh:207-213`: `tar --strip-components=1 ... || tar ...` — **무조건 strip 우선**, 실패 시 no-strip 폴백(오류 은닉).

#### 2.1.3 영향 범위
- 호출자: `opal-cli` 디스패처 → `cmd_update`. 추출 후 `install-mac.sh`/`macos.sh`를 `OPAL_AUTO_INSTALL=1 OPAL_VERSION=$version FRAMEWORK_ROOT=$extract_dir`로 실행(`update.sh:246`) — 추출 레이아웃이 깨지면 재설치가 전부 실패.
- `adopt_stamped_version` 상응 로직 `update.sh:215-226`: `$extract_dir/VERSION` 각인값 채택 — 추출 정상 배치에 의존.
- 검증 token은 `version`(예 `v0.6.10`) 기반이라 sha256sums.txt의 `opal-v0.6.10.tar.gz`와 매칭됨(update.sh는 basename 무관, token 기반 — install.sh와 다름).

---

### F-002: install.sh 릴리즈-자산 정합

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.sh` | macOS/Linux one-liner 진입 — fetch→verify→extract→플랫폼 인스톨러 | 수정 |

#### 2.2.2 현재 구현
- URL 구성 `install.sh:115-121`: v*이면 `archive/refs/tags`, 그 외 `archive/refs/heads`. `SHA_URL`은 항상 `releases/download/${OPAL_VERSION}/sha256sums.txt` `install.sh:121`.
- 로컬 tarball명 `install.sh:180`: `OPAL_TARBALL="${OPAL_TMP}/opal.tar.gz"` — **정적 `opal.tar.gz`**.
- 검증 `install.sh:210-279`: sha256sums.txt 받고 `basename "${OPAL_TARBALL}"`(=`opal.tar.gz`)로 `grep` → sha256sums.txt token은 `opal-v*.tar.gz`이므로 **매칭 실패 → sha_entry 빈값 → "항목 없음, 검증 건너뜀"**(`install.sh:260-263`). 즉 현행 install.sh는 v*에서도 **검증이 조용히 skip**됨(H-3 근거). v* + sha256sums.txt 부재 시 prompt/거부 `install.sh:232-247`.
- 추출 `install.sh:283-299`: `tar --strip-components=1` **무조건 적용** `install.sh:295`.

#### 2.2.3 영향 범위
- 흐름: `main()` `install.sh:362-381` → detect_platform→check_deps→fetch_tarball→verify_checksum→extract_to_tmp→adopt_stamped_version→exec_platform_installer.
- `verify_checksum`은 `OPAL_PLATFORM`(shasum vs sha256sum) 분기 사용 `install.sh:268-276`.
- URL 상수(`TARBALL_URL`)가 fetch_tarball보다 먼저 top-level에서 확정 `install.sh:115-119` → 소스 폴백을 넣으려면 fetch 시점에 404 감지가 필요 → 구조 조정 대상.

---

### F-003: install.ps1 릴리즈-자산 정합

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.ps1` | Windows one-liner 진입 — Fetch→Verify→Invoke-PlatformInstaller | 수정 |

#### 2.3.2 현재 구현
- URL 구성 `install.ps1:94-102`: v*이면 `archive/refs/tags`, 그 외 `archive/refs/heads`. `$ShaUrl`은 항상 `releases/download/$OpalVersion/sha256sums.txt`.
- 로컬 tarball명 `install.ps1:141`: `opal-$OpalVersion.tar.gz` — **이미 자산 token과 동일한 이름**(예 `opal-v0.6.10.tar.gz`). 따라서 PS는 파일명 매칭은 이미 정합, 다운로드 소스만 아카이브라 콘텐츠 불일치로 `throw` `install.ps1:227-229`.
- 검증 `install.ps1:164-232`: `$script:OpalVersion -like 'v*'` 분기, sha256sums.txt 받아 `Split-Path -Leaf` token 정규식 매칭→`Get-FileHash` 비교.
- 추출 `install.ps1:260-261`: `tar --strip-components 1 --exclude='tasks/*' ...` **무조건 strip**. (릴리즈 자산은 `git archive HEAD` + `.gitattributes export-ignore`로 tasks/ 이미 제외 → 자산 경로에서 `--exclude`는 무해하나 strip은 금지.)

#### 2.3.3 영향 범위
- `Invoke-OpalInstall` `install.ps1:308-356` → Test-Deps→Fetch-Tarball→Verify-Checksum→Invoke-PlatformInstaller.
- PS 5.1 제약: `[IO.Path]::Combine` 사용 중(`Join-Path` 다중인자 회피, `install.ps1:275,286`), `Set-StrictMode -Version 3.0` → 미선언 변수 접근 금지. 소스 추적 변수는 `$script:` 스코프로 선언 필요.
- extraction 후 exit code 관용 처리 `install.ps1:262-270`(opal/ 존재 시 진행). 무-strip 경로에서도 이 관용 로직 재사용 가능.

---

### F-004: 정합 검증 테스트 추가

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/tests/test_release_asset_align.sh` | 다운로드 대상 선택·추출 prefix 분기·폴백·검증 매칭·회귀 정합 검증 | 신규 |
| 배치(참조) | `scripts/tests/test_version_stamp.sh` | 테스트 작성 패턴(정적 계약 grep + scratch mechanism) 참조 | 참조 |

#### 2.4.2 현재 구현
- `test_version_stamp.sh`는 (가) 저장소 계약 grep 검증(TC-A*, RED 시점 FAIL) + (나) scratch repo mechanism 검증(TC-B*, RED 시점 PASS) 2트랙 구조. bash 3.2 호환(연관배열·mapfile 미사용, case 패턴). `pass/fail/skip` 카운터 + verdict exit code.
- 네트워크 미의존: 실제 GitHub 다운로드 없이 소스 파일 grep + scratch tarball 생성으로 계약·메커니즘 검증. F-004도 동일 원칙(오프라인).

#### 2.4.3 영향 범위
- 독립 신규 파일. 3종 인스톨러 소스를 grep 대상으로 읽기만 함(수정 없음).
- CI/수동 실행: `bash scripts/tests/test_release_asset_align.sh`.

---

### F-005: 재릴리즈 안내 + 변경이력 갱신

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `tasks/070-.../DONE.md` (또는 릴리즈 노트 초안) | 구버전 사용자 복구용 원라이너 재설치 안내 | 신규(EXECUTE/CLOSE 시) |
| 배치 | `opal/tools/opal-cli/lib/update.sh` | 헤더 변경이력에 070 행 추가 | 수정 |
| 배치 | `scripts/install.sh` | 헤더 변경이력에 070 행 추가 | 수정 |
| 배치 | `scripts/install.ps1` | 헤더 변경이력에 070 행 추가 | 수정 |

#### 2.5.2 현재 구현
- 3종 파일 모두 헤더 주석 내 `변경이력:` 블록 보유(`update.sh:17-24`, `install.sh:32-41`, `install.ps1:36-48`). 태스크 번호를 괄호로 병기하는 관례(`(139)`, `(048)` 등).
- 부트스트랩 함정: Option A 수정본은 새 tarball에 실리지만 update를 실행하는 주체는 구버전 인스톨러 → v0.6.x(자산 보유) 사용자는 `opal-cli update`로 자가 도달 불가. 복구는 수정된 main install.sh/ps1 원라이너 재설치.

#### 2.5.3 영향 범위
- 변경이력은 각 스크립트 헤더에 국한(코드 로직 무영향). 배포 시 install-mac.sh가 변경이력 섹션을 strip하나 소스에는 유지( `docs/CONVENTIONS.md §변경이력 작성 의무`).

---

## 3. 기능별 설계

> 공통 인용: 다운로드 대상·검증 기준의 근본 원인은 (→ D-1 §근본 원인)·(→ D-4 §Build tarball). 릴리즈 자산은 `git archive --format=tar.gz -o opal-${TAG}.tar.gz HEAD`로 생성되어 **최상위 prefix 없음** (`.github/workflows/release.yml:29-34`). GitHub 소스아카이브(`archive/refs/*`)는 최상위 `opal-X.Y.Z/` prefix 있음 (→ D-1 §배경 분석).

[MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `scripts/`, ...)에서 수행한다." → 모든 수정은 `opal/tools/opal-cli/lib/update.sh`·`scripts/*`에서 수행하고 `./scripts/install-mac.sh` 재배포로 검증한다.

[MUST] `docs/CONVENTIONS.md` §커밋 규칙: "커밋은 캡틴이 명시적으로 요청할 때만 수행" → EXECUTE 완료 후에도 자동 커밋 금지.

[MUST] `TASK.md` §제약 조건: "릴리즈 자산 404 폴백은 반드시 UNVERIFIED로 취급 (무결성 저하 은닉 금지)."

### 공통 설계 계약 (3종 인스톨러 공통 규약)

1. **다운로드 대상 결정 규약** (v* 태그일 때):
   - 1순위 자산: `https://github.com/${repo}/releases/download/${version}/opal-${version}.tar.gz`
   - curl/irm 성공 → 소스 = `asset`
   - 실패(404 등) → 폴백 `https://github.com/${repo}/archive/refs/tags/${version}.tar.gz`, 소스 = `archive`
   - 비-v*(main/브랜치/SHA): `https://github.com/${repo}/archive/refs/heads/${version}.tar.gz`, 소스 = `archive` (회귀 유지, →D-2 `install.sh:117-118`)
2. **추출 분기 규약** (다운로드 소스 기준):
   - 소스 = `asset` → strip **없이** 추출 (prefix 없음)
   - 소스 = `archive` → `--strip-components=1` 적용 (prefix `opal-X.Y.Z/` 제거)
3. **검증 분기 규약** (다운로드 소스 기준):
   - 소스 = `asset` → sha256sums.txt 받아 `opal-${version}.tar.gz` token 매칭 검증(PASS 필수)
   - 소스 = `archive` (v* 자산 404 폴백 or 비-v*) → UNVERIFIED로 취급, 기존 배너·`OPAL_ALLOW_UNVERIFIED`·비대화형 거부 재사용
4. **소스 상태 전파**: 판정 결과(asset/archive)를 다운로드→검증→추출 단계로 전달할 변수를 도입한다 (bash: 일반 변수 + case 비교 / PS: `$script:` 스코프 변수).

### F-001: update.sh 릴리즈-자산 정합

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/update.sh` | 배치 | tarball URL 결정부에 자산 1순위 + 아카이브 폴백 도입, 다운로드 시 404 감지→소스 판정, 검증/추출을 소스 기반 분기로 전환 | `update.sh:127-213` |

#### 3.1.2 설계 (함수/로직)
- **다운로드 대상 + 소스 판정**: `update.sh:127-136`의 `tarball_url` 결정 + `update.sh:159-165`의 다운로드를 통합 조정.
  - 신규 로컬 변수: `local tarball_source="archive"` (기본).
  - v*이면 먼저 자산 URL로 curl 시도. 성공 시 `tarball_source="asset"`. 실패(비-0 exit) 시 아카이브 tags URL로 재시도(`tarball_source="archive"`). 비-v*이면 heads URL(`tarball_source="archive"`).
  - bash 3.2 호환: 별도 함수 대신 인라인 `if curl ...; then ... else curl ... fi` 사용 또는 헬퍼 함수 `_download_tarball()` 도입. (→ D-1 §확정 방향 §1·§2)
- **UNVERIFIED 배너 조건 확장** `update.sh:168-170`: 기존 `version != v*` → `tarball_source == archive`로 전환(자산 404 폴백도 UNVERIFIED 배너 대상). [MUST] TASK §제약(무결성 은닉 금지).
- **검증 분기** `update.sh:172-205`: 조건을 `version == v*` → `tarball_source == asset`로 변경. asset일 때만 sha256sums.txt 검증(기존 `grep "opal-${version}.tar.gz"` token 유지 — sha256sums.txt와 정합, →D-4 §sha256sum). archive(v* 폴백)일 때는 기존 sha256sums.txt 부재 분기와 동일한 UNVERIFIED 처리(`OPAL_ALLOW_UNVERIFIED`/비대화형 거부/prompt) 재사용.
- **추출 분기** `update.sh:207-213`: `tar --strip-components=1 || tar` 무조건 폴백 제거 → 소스 기반 명시 분기.
  ```
  if [ "$tarball_source" = "asset" ]; then
      tar -xzf "$tarball_path" -C "$extract_dir"           # prefix 없음 → strip 금지
  else
      tar -xzf "$tarball_path" -C "$extract_dir" --strip-components=1  # prefix 제거
  fi
  ```
  bash 3.2 호환: `case`/`[ = ]` 문자열 비교. (→ D-1 §추출 로직 주의)

#### 3.1.3 환경 변경
해당 없음 (curl 이미 의존, 신규 패키지 없음).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 AC | 산출물 검사(grep) | update.sh에 `releases/download/.../opal-${version}.tar.gz` 자산 URL + 아카이브 폴백 분기 존재 |
| TS-002 | R4 AC | 산출물 검사 + 통합 | 소스=asset 시 no-strip, archive 시 strip 분기 존재 + scratch tarball 추출 시 최상위 파일 온전 |
| TS-003 | R5 AC | 산출물 검사 | archive 폴백 경로에서 UNVERIFIED 배너/거부 로직 재사용 |
| TS-007 | R7 AC | 회귀/dry-run | `--to main --dry-run` 시 heads URL + UNVERIFIED, 기존과 동일 |

### F-002: install.sh 릴리즈-자산 정합

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.sh` | 배치 | 자산 1순위 + 아카이브 폴백, 로컬 tarball명 `opal-${OPAL_VERSION}.tar.gz`로 정합, 검증/추출 소스 기반 분기 | `install.sh:111-299` |

#### 3.2.2 설계 (함수/로직)
- **URL·소스 판정**: top-level 상수 `TARBALL_URL` `install.sh:115-119`는 자산 URL을 1순위로 구성하되, 실제 404 감지는 `fetch_tarball` 내에서 수행하고 전역 `OPAL_TARBALL_SOURCE`(asset/archive)를 설정한다.
  - 신규 전역: `OPAL_TARBALL_SOURCE="archive"`, `OPAL_ASSET_URL`/`OPAL_ARCHIVE_URL` 분리 구성. v*이면 asset 우선, 실패 시 archive tags. 비-v*이면 archive heads.
- **로컬 tarball명 정합** [MUST] H-3 대응: `OPAL_TARBALL="${OPAL_TMP}/opal.tar.gz"` `install.sh:180` → 소스=asset일 때 `OPAL_TARBALL="${OPAL_TMP}/opal-${OPAL_VERSION}.tar.gz"`로 저장. 이래야 `verify_checksum`의 `basename` grep `install.sh:255-258` + `shasum -c --ignore-missing` `install.sh:269/273`가 sha256sums.txt token `opal-v*.tar.gz`와 매칭된다. (현행 `opal.tar.gz`는 token 불일치로 검증이 조용히 skip됨 — self-confirming 결함.)
- **fetch_tarball** `install.sh:178-204`: DRY-RUN 유지. 실경로에서 asset URL curl → 성공 시 source=asset·파일명 자산형. 실패 시 archive URL curl → source=archive·파일명은 무관(검증 skip). curl 플래그 `-fsSL --proto '=https' --tlsv1.2` 유지 [MUST] `install.sh:23`.
- **verify_checksum** `install.sh:210-279`: 검증 실행 조건을 `OPAL_VERSION == v*` → `OPAL_TARBALL_SOURCE == asset`로 전환. asset이면 sha256sums.txt 받아 검증(PASS 필수). archive(v* 폴백)이면 기존 v* + sha256sums.txt 부재 분기와 동일 UNVERIFIED 처리(`install.sh:232-247`) 재사용. 비-v*는 기존 graceful skip `install.sh:248-250` 유지.
- **extract_to_tmp** `install.sh:283-299`: `--strip-components=1` 무조건 `install.sh:295` → 소스 기반 분기.
  ```
  if [ "${OPAL_TARBALL_SOURCE}" = "asset" ]; then
      tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" || error "tarball 추출 실패"
  else
      tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" --strip-components=1 || error "tarball 추출 실패"
  fi
  ```
- main UNVERIFIED 배너 `install.sh:369-372`: 비-v* 조건 유지. 추가로 v* asset 404 폴백 시에도 UNVERIFIED 인지 가능하도록 verify_checksum 내 배너로 커버.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R2 AC | 산출물 검사(grep) | install.sh에 자산 URL + 아카이브 폴백 분기 존재 |
| TS-002 | R4 AC | 산출물 검사 + 통합 | 소스 기반 strip 분기 존재 + scratch 추출 검증 |
| TS-004 | R6 AC | 산출물 검사 | 로컬 tarball명이 `opal-${OPAL_VERSION}.tar.gz`(asset)로 저장되어 sha256sums.txt token 매칭 |
| TS-003 | R5 AC | 산출물 검사 | archive 폴백 UNVERIFIED 재사용 |
| TS-007 | R7 AC | 회귀/dry-run | `OPAL_VERSION=main OPAL_DRY_RUN=1` 시 heads URL + UNVERIFIED |

### F-003: install.ps1 릴리즈-자산 정합

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.ps1` | 배치 | 자산 1순위 + 아카이브 폴백, 검증/추출 소스 기반 분기 (`$script:TarballSource`) | `install.ps1:94-304` |

#### 3.3.2 설계 (함수/로직)
- **URL·소스 판정**: `install.ps1:97-102`의 `$TarballUrl` 단일 구성 → `$AssetUrl`/`$ArchiveUrl` 분리 + `$script:TarballSource = 'archive'` 초기화.
- **Fetch-Tarball** `install.ps1:129-162`: v*이면 `$AssetUrl`로 `Invoke-RestMethod` try → 성공 시 `$script:TarballSource='asset'`. catch 시 `$ArchiveUrl`로 재시도 `$script:TarballSource='archive'`. 비-v*은 `$ArchiveUrl`. 로컬 파일명은 이미 `opal-$OpalVersion.tar.gz` `install.ps1:141` 유지(자산 token 정합). TLS12/13 강제 `install.ps1:153` 유지.
- **Verify-Checksum** `install.ps1:164-232`: 검증 조건 `$script:OpalVersion -like 'v*'` → `$script:TarballSource -eq 'asset'`로 전환. asset이면 sha256sums.txt 검증(기존 `Get-FileHash`·정규식 token 매칭 `install.ps1:213-229`). archive(v* 폴백)이면 기존 sha256sums.txt catch 분기의 UNVERIFIED 처리(`install.ps1:191-206`) 재사용.
- **Invoke-PlatformInstaller 추출** `install.ps1:260-261`: `--strip-components 1` 무조건 → 소스 기반 분기.
  ```
  if ($script:TarballSource -eq 'asset') {
      & tar -xzf $TarballPath -C $extractDir            # prefix 없음 → strip 금지
  } else {
      & tar -xzf $TarballPath -C $extractDir --strip-components 1 `
          --exclude='tasks/*' --exclude='*/tasks/*' --exclude='tasks' --exclude='*/tasks'
  }
  ```
  자산은 `git archive HEAD`가 `.gitattributes export-ignore`로 tasks/ 이미 제외 → `--exclude` 불필요. exit code 관용 로직 `install.ps1:262-270` 재사용.
- main UNVERIFIED 배너 `install.ps1:324-326`: 비-v* 유지. v* asset 404 폴백은 Verify-Checksum 내 배너로 커버.
- **PS 5.1 호환** [MUST] H-6: `$script:` 스코프 변수 명시(`Set-StrictMode -Version 3.0` `install.ps1:34` 준수), `[IO.Path]::Combine` 유지, `Join-Path` 다중인자 미사용.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R3 AC | 산출물 검사(grep) | install.ps1에 자산 URL + 아카이브 폴백 분기 존재 |
| TS-002 | R4 AC | 산출물 검사 | `$script:TarballSource` 기반 strip 분기 존재 |
| TS-003 | R5 AC | 산출물 검사 | archive 폴백 UNVERIFIED 재사용 |
| TS-006 | 제약 AC | 산출물 검사 | `$script:` 스코프 + `[IO.Path]::Combine` 유지(PS5.1 호환) |
| TS-007 | R7 AC | 회귀 | 비-v* 시 heads URL + UNVERIFIED 배너 |

### F-004: 정합 검증 테스트 추가

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `scripts/tests/test_release_asset_align.sh` | 배치 | 다운로드 대상·추출 분기·폴백·검증 매칭·회귀·보안 정합 검증 (오프라인) | (→ D-5) |

#### 3.4.2 설계 (테스트 구조)
- `test_version_stamp.sh` 패턴 채용 (→ D-5 `test_version_stamp.sh:1-234`): 2트랙 — (가) 정적 계약 grep(TC-A*, RED 시점 FAIL 예상), (나) scratch mechanism(TC-B*, RED 시점 PASS).
- bash 3.2 호환: 연관배열·mapfile 미사용, case 패턴, `pass/fail/skip` 카운터 + verdict exit code.
- **(가) 정적 계약** (3종 소스 grep):
  - TC-A1(S-1): 3종에 `releases/download/.*opal-.*\.tar\.gz` 자산 URL 존재.
  - TC-A2(S-1): 3종에 아카이브 폴백(`archive/refs/tags`) 잔존(폴백용).
  - TC-A3(S-3): 3종에 소스 기반 strip 분기(자산 no-strip / archive strip) 존재 — `strip-components` 사용이 무조건이 아닌 조건 분기 하위임을 grep로 확인.
  - TC-A4(S-4): install.sh 로컬 tarball명 `opal-${OPAL_VERSION}.tar.gz` 패턴 존재; update.sh 검증 token `opal-${version}.tar.gz` 존재; ps1 파일명 `opal-$OpalVersion.tar.gz` 존재.
  - TC-A5(S-2): 3종에 UNVERIFIED 배너 + `OPAL_ALLOW_UNVERIFIED` + 비대화형 거부 존재.
  - TC-A6(S-5): 비-v* 경로 `archive/refs/heads` 잔존(회귀).
- **(나) scratch mechanism** (오프라인 tarball):
  - TC-B1(S-3): prefix 없는 tarball(자산 모사: `tar czf` from flat dir 또는 `git archive HEAD`)을 `--strip-components=1`로 풀면 최상위 파일이 **유실**됨을 실증(추출 분기 필요성 증명). 무-strip으로 풀면 온전.
  - TC-B2(S-3): prefix 있는 tarball(아카이브 모사: `--prefix=opal-9.9.9/`)을 `--strip-components=1`로 풀면 최상위 파일 온전 배치.
  - TC-B3(S-4): 두 tarball의 sha256이 다름을 실증(근본 원인 재현) — flat vs prefixed 해시 불일치.
- **보안**: TC-A7(S-6) 변경 대상 3종 + 신규 테스트 파일 시크릿 패턴 스캔(`test_version_stamp.sh:209-234` 패턴 재사용).

#### 3.4.3 환경 변경
해당 없음 (bash/tar/git — 기존 의존).

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R8 AC | 통합/회귀 | `bash scripts/tests/test_release_asset_align.sh` 실행 시 GREEN(구현 후 전 PASS), RED 시점(구현 전) TC-A* FAIL |
| TS-006 | 제약 AC | 보안/정적 | 변경 파일·신규 테스트에 시크릿 패턴 0건 |

### F-005: 재릴리즈 안내 + 변경이력 갱신

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/update.sh` | 배치 | 헤더 변경이력에 070 행 추가 | `update.sh:17-24` |
| 2 | `scripts/install.sh` | 배치 | 헤더 변경이력에 070 행 추가 | `install.sh:32-41` |
| 3 | `scripts/install.ps1` | 배치 | 헤더 변경이력에 070 행 추가 | `install.ps1:36-48` |

**신규 생성** (CLOSE 단계 산출)
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 4 | `tasks/070-.../DONE.md` | 문서 | 구버전 사용자 복구 원라이너 재설치 안내 포함 | (→ D-1 §부트스트랩 함정) |

#### 3.5.2 설계 (안내 문구)
- 릴리즈 노트/DONE.md 초안 안내 (→ D-1 §부트스트랩 함정 §복구 경로):
  > **기존 v0.6.x 사용자 필수 조치**: `opal-cli update`로는 본 수정본에 자가 도달할 수 없습니다(구버전 인스톨러가 여전히 아카이브를 받아 릴리즈-자산 체크섬으로 검증하여 동일 실패). 아래 원라이너로 재설치하세요.
  > - macOS/Linux: `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash`
  > - Windows: `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)`
- 변경이력 행 포맷 [MUST] `docs/CONVENTIONS.md` §변경이력: `YYYY-MM-DD HH:mm` (KST) + semver + 태스크 번호 `(070)`. 예: `v1.0.7 2026-07-21 HH:mm KST: 릴리즈 자산 다운로드 전환 + 소스별 추출 prefix 분기 + 404 아카이브 폴백 UNVERIFIED (070)`.

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R9 AC | 산출물 검사 | DONE.md/릴리즈 노트 초안에 원라이너 재설치 안내 존재 |
| TS-010 | R10 AC | 산출물 검사 | 3종 파일 변경이력에 070 행 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002, F-003 | 1, 2, 3 | opal-task-agent | 병렬 가능 | 독립 파일 3종 |
| 2 | F-004 | 4 | opal-task-agent | 순차 | 코드 수정 후 정합 검증 |
| 3 | F-005 | 5, 6 | opal-task-agent / PM 직접 | 순차 | 실제 수정 반영 |
| 3 | (문서 판단) | 7 | PM 직접 | 조건부 | ARCHITECTURE.md 갱신 판단 |

### 4.2 실행 체크리스트
> 총 7개 Step | Phase 3개 | 실행 모드: 복잡

#### Step 1: update.sh 릴리즈-자산 정합
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/update.sh`
- **작업 내용**: (1) tarball URL 결정부(줄 127-133)에 v* 자산 1순위 URL + 404 시 아카이브 tags 폴백 도입, 다운로드부(줄 159-165)에서 소스 판정 변수(`tarball_source` asset/archive) 설정. (2) UNVERIFIED 배너(줄 168-170)를 `tarball_source==archive` 기준으로 확장. (3) 검증부(줄 172-205)를 `tarball_source==asset`일 때만 실행, archive 폴백은 기존 UNVERIFIED 재사용. (4) 추출부(줄 207-213)의 무조건 `--strip-components=1 || tar` 폴백을 소스 기반 명시 분기로 교체(asset=no-strip, archive=strip). bash 3.2 호환(case/문자열 비교).
- **완료 기준**: TS-001·TS-002·TS-003·TS-007 grep/dry-run 통과. 자산 URL·폴백·소스 기반 추출/검증 분기 존재.
- **테스트**: TS-001, TS-002, TS-003, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: install.sh 릴리즈-자산 정합
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.sh`
- **작업 내용**: (1) URL 구성(줄 111-121)을 자산/아카이브 분리, `OPAL_TARBALL_SOURCE` 전역 도입. (2) `fetch_tarball`(줄 178-204)에서 v* 자산 우선 curl→404 시 아카이브 폴백, source 설정. (3) [MUST] asset 소스일 때 로컬 tarball명을 `opal-${OPAL_VERSION}.tar.gz`로 저장(줄 180) — sha256sums.txt token/`shasum -c` 매칭. (4) `verify_checksum`(줄 210-279) 실행 조건을 `OPAL_TARBALL_SOURCE==asset`로 전환, archive 폴백은 기존 UNVERIFIED 재사용. (5) `extract_to_tmp`(줄 295)를 소스 기반 strip 분기로 교체. bash 3.2 호환.
- **완료 기준**: TS-001·TS-002·TS-004·TS-003·TS-007 통과. 로컬 파일명 정합으로 검증 skip 결함 해소.
- **테스트**: TS-001, TS-002, TS-004, TS-003, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: install.ps1 릴리즈-자산 정합
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.ps1`
- **작업 내용**: (1) URL 구성(줄 94-102)을 `$AssetUrl`/`$ArchiveUrl` 분리 + `$script:TarballSource='archive'` 초기화. (2) `Fetch-Tarball`(줄 129-162)에서 v* 자산 우선 irm→catch 시 아카이브 폴백, source 설정(로컬명 `opal-$OpalVersion.tar.gz` 유지). (3) `Verify-Checksum`(줄 164-232) 조건을 `$script:TarballSource -eq 'asset'`로 전환, archive 폴백 UNVERIFIED 재사용. (4) `Invoke-PlatformInstaller` 추출(줄 260-261)을 소스 기반 strip 분기로 교체(asset=no-strip). PS 5.1 호환(`$script:` 스코프, `[IO.Path]::Combine`).
- **완료 기준**: TS-001·TS-002·TS-003·TS-006·TS-007 통과.
- **테스트**: TS-001, TS-002, TS-003, TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: 정합 검증 테스트 작성
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/tests/test_release_asset_align.sh` (신규)
- **작업 내용**: `test_version_stamp.sh` 패턴으로 2트랙 테스트 작성 — (가) 3종 소스 정적 계약 grep(자산 URL·폴백·소스 기반 strip 분기·검증 파일명 정합·UNVERIFIED 재사용·회귀 heads), (나) scratch tarball mechanism(prefix 유무별 strip 결과·flat/prefixed 해시 불일치 실증) + 시크릿 스캔. bash 3.2 호환, verdict exit code.
- **완료 기준**: `bash scripts/tests/test_release_asset_align.sh` 실행 시 구현 후 전 PASS(GREEN). RED-first: Step 1-3 이전 실행 시 TC-A* FAIL 관찰(TEST-SCENARIO §0 참조).
- **테스트**: TS-008, TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3

#### Step 5: 3종 스크립트 변경이력 070 행 추가
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/update.sh`, `scripts/install.sh`, `scripts/install.ps1`
- **작업 내용**: 3종 헤더 변경이력 블록에 070 행 추가 — `YYYY-MM-DD HH:mm KST` + semver + `(070)` + 변경 요약(릴리즈 자산 전환·추출 분기·폴백).
- **완료 기준**: TS-010 통과 — 3종 파일 변경이력에 070 행 존재.
- **테스트**: TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3

#### Step 6: 재릴리즈 복구 안내 문구 산출
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `tasks/070-.../DONE.md` (또는 릴리즈 노트 초안)
- **작업 내용**: 구버전 v0.6.x 사용자 복구용 원라이너 재설치 안내(macOS/Linux·Windows)를 DONE.md/릴리즈 노트 초안에 포함. 부트스트랩 함정(자가 도달 불가) 설명 동반.
- **완료 기준**: TS-009 통과 — 안내 문구 산출물에 존재.
- **테스트**: TS-009
- **실행 방법**: direct
- **의존**: Step 1, 2, 3

#### Step 7: (조건부) docs/ARCHITECTURE.md 갱신 판단
- [ ] 완료
- **소속 기능**: F-002 (시스템 배포 흐름)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 배포 채널 표(§ 줄 325-327)의 "태그 기반 tarball" 서술이 다운로드 대상 릴리즈-자산 전환을 반영하는지 검토. 표현 정확성 유지되면 갱신 스킵, 소스아카이브→릴리즈-자산 전환을 명시할 가치가 있으면 1줄 보강.
- **완료 기준**: 갱신 필요 여부 판정 + (필요 시) 반영. 스킵 시 사유 DONE.md 기재.
- **테스트**: 산출물 검사(수동)
- **실행 방법**: direct
- **의존**: Step 1, 2, 3

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 ∥ Step 3 | 독립 파일(update.sh / install.sh / install.ps1), 공유 상태 없음 |
| Step 1,2,3 → Step 4 | 테스트가 3종 정합 계약을 grep 검증 → 코드 수정 완료 후 GREEN 관찰 |
| Step 1,2,3 → Step 5 | 변경이력은 실제 수정 반영 |
| Step 1,2,3 → Step 6 | 안내 문구는 확정된 동작 기반 |
| Step 1,2,3 → Step 7 | 아키텍처 문서는 최종 동작 기준 판단 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | update.sh 자산 우선·폴백·추출·검증 정합 | TS-001,002,003,007 | 자산 URL·폴백·소스 분기 grep 통과 + dry-run 회귀 동일 |
| F-002 | install.sh 자산 정합 + 검증 파일명 매칭 | TS-001,002,004,003,007 | 로컬명 `opal-${v}.tar.gz`로 검증 실행(skip 결함 해소) |
| F-003 | install.ps1 자산 정합 + PS5.1 호환 | TS-001,002,003,006,007 | `$script:TarballSource` 분기 + `[IO.Path]::Combine` 유지 |
| F-004 | 정합 검증 테스트 GREEN | TS-008,006 | 테스트 실행 전 PASS + RED-first FAIL 관찰 |
| F-005 | 복구 안내 + 변경이력 070 | TS-009,010 | 안내 문구 + 3종 070 행 존재 |

### 5.2 회귀 테스트
- [ ] `--to main` / `OPAL_VERSION=main`: 기존 `archive/refs/heads` + strip + UNVERIFIED 배너 그대로 (TS-007)
- [ ] commit SHA / 미기록 버전 경로 기존 동작 유지
- [ ] 기존 `scripts/tests/test_version_stamp.sh` 여전히 PASS (adopt_stamped_version·VERSION 각인 무영향)
- [ ] `OPAL_DRY_RUN=1` 흐름 검증 3종 정상

### 5.3 코드/문서 품질
- [ ] bash 3.2 호환 (연관배열·mapfile 미사용, case/문자열 비교) — update.sh·install.sh·test
- [ ] PowerShell 5.1 호환 (`$script:` 스코프, `[IO.Path]::Combine`, `Join-Path` 다중인자 미사용) — install.ps1
- [ ] 3종 변경이력 070 행 (KST 일시·semver·태스크번호)
- [ ] @header/헤더 주석 규칙 준수

### 5.4 보안
- [ ] 변경 3종 + 신규 테스트에 하드코딩 토큰/시크릿 없음 (TS-006 스캔)
- [ ] `.gitignore`에 identity.md/.venv/.env/projects 사용자 데이터 유지 (`.gitignore:20,22`)
- [ ] curl/irm TLS 강제 유지 (`-fsSL --proto '=https' --tlsv1.2` / TLS12·13)
- [ ] 자산 404 폴백 UNVERIFIED 은닉 없음 (배너·거부 재사용)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 3 수정 + 1 신규 테스트 (+DONE/문서) = 4+ | 복잡 |
| 모듈 범위 | 다중 (opal-cli/lib + scripts + scripts/tests) | 복잡 |
| 작업 유형 | 오류 수정 | 단순 |
| 외부 의존성 | 없음 (curl/tar/git 기존) | 단순 |
| **실행 모드** | **복잡** | 5기준 중 3개 복잡 트리거 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **Batch 1 (병렬)**: 3종 인스톨러 수정. 독립 파일이나 TASK 가이드상 단일 `opal-task-agent`로 배정(범용 shell/ps 수정). 파일 충돌 없음 → 필요 시 3개 opal-task-agent 병렬 디스패치 가능(Step 1·2·3). 각 Step은 동일 공통 계약(§3 공통 설계)을 공유하므로 디스패치 시 공통 규약을 함께 주입.
- **Batch 2 (순차)**: Step 4 테스트 작성·실행 (opal-task-agent). Batch 1 완료 후.
- **Batch 3 (순차)**: Step 5 변경이력(opal-task-agent) + Step 6·7 문서(PM 직접). Batch 1 완료 후.

```
[Batch1]  Step1(update.sh) ∥ Step2(install.sh) ∥ Step3(install.ps1)   agent=opal-task-agent
             │                    │                    │
             └────────────────────┴────────────────────┘
[Batch2]                    Step4(test) ── opal-task-agent
[Batch3]         Step5(변경이력) opal-task-agent │ Step6(안내)·Step7(docs) PM 직접
```

### C-2. 스킬 요구사항
- 기존 스킬 매칭: 없음(순수 shell/ps 수정 — 전용 스킬 불요). 공통 계약 4항목(§3)이 3개 Step에서 반복되나 인라인 지침으로 충분(스킬 후보 아님 — 1태스크 한정).

### C-3. 도구 요구사항
- CLI: bash 3.2+, curl, tar, git (기존 의존). PowerShell 5.1+ / tar (Windows). 신규 설치 없음.
- MCP: 불요.

### C-4. 테스트 전략
- 기능/정합: `bash scripts/tests/test_release_asset_align.sh` (신규, 오프라인 grep + scratch mechanism).
- 회귀: `bash scripts/tests/test_version_stamp.sh` (기존 유지 확인) + 3종 `OPAL_DRY_RUN=1` 흐름.
- 코드 품질: `bash -n`(구문 검사) update.sh·install.sh·test; PowerShell `Test-ScriptFileInfo`/파싱(가능 환경) 또는 수동 리뷰.
- 보안: 테스트 내 시크릿 스캔 TC + `.gitignore` 확인.
- 상세: TEST-SCENARIO.md.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 설치 스크립트 | Bash (macOS/Linux, 3.2 호환) | 없음 (인라인 지침) |
| 설치 스크립트 | PowerShell 5.1+ (Restricted/RemoteSigned) | 없음 |
| 릴리즈 | GitHub Releases / Actions (release.yml 참조, 변경 없음) | 없음 |
| 테스트 | shell 기반 (`scripts/tests/*.sh`) | test_version_stamp 패턴 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 순수 shell/ps 수정 — 외부 라이브러리 API 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | TASK.md | `tasks/070-260721-opds-인스톨러-릴리즈자산-정합/TASK.md` | 근본 원인·확정 설계 방향·부트스트랩 함정·요구사항 R1-R10 |
| D-2 | 소스 | update.sh | `opal/tools/opal-cli/lib/update.sh` | 수정 대상 1 — 다운로드·검증·추출 현행 로직 |
| D-3 | 소스 | install.sh | `scripts/install.sh` | 수정 대상 2 — URL·verify_checksum·extract 현행 |
| D-4 | 소스 | install.ps1 | `scripts/install.ps1` | 수정 대상 3 — Fetch/Verify/Invoke 현행 |
| D-5 | 소스 | release.yml | `.github/workflows/release.yml` | 자산 생성 방식(`git archive HEAD` prefix 없음) + sha256sums.txt token |
| D-6 | 소스 | test_version_stamp.sh | `scripts/tests/test_version_stamp.sh` | 테스트 패턴(정적 계약 + scratch mechanism, bash 3.2) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·커밋·변경이력·구현 규칙 [MUST] |
| D-8 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 산출물 인용 포맷 |
| D-9 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 배포 채널 서술(§325-327) — docs 갱신 판단 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 추출 분기 누락 → 자산 추출 조용히 깨짐(최상위 유실) | F-001,F-002,F-003 | P0 | 소스 기반 명시 strip 분기 + scratch mechanism 테스트(TC-B1/B2) 실증 |
| R-2 | install.sh 검증 파일명 미정합 → 검증 조용히 skip(self-confirming) | F-002 | P0 | 로컬명 `opal-${v}.tar.gz` 저장 + TC-A4 grep 검증 |
| R-3 | 자산 404 폴백 시 UNVERIFIED 은닉 | 3종 | P0 | 기존 배너·거부 로직 소스 기반 재사용 + TC-A5 |
| R-4 | 회귀 — main/브랜치 경로 변형 | 3종 | P0 | heads URL·strip·배너 무변경 + TS-007 dry-run + TC-A6 |
| R-5 | 부트스트랩 함정 — 구버전 자가 도달 불가 | F-005 | P1 | 원라이너 재설치 안내 필수 산출(R9) |
| R-6 | bash 3.2 / PS 5.1 비호환 문법 | 3종·F-004 | P1 | 연관배열·mapfile 회피(case), `$script:`·`[IO.Path]::Combine` + `bash -n` |
| R-7 | 테스트 self-confirming(항상 통과) | F-004 | P1 | RED-first — 구현 전 TC-A* FAIL 관찰 후 GREEN 전환 |

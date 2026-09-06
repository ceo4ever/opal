# TASK: 릴리즈 체크섬 검증 경로 정합 — 다운로드 대상과 검증 대상 일치

> 작성일: 2026-08-07 | 작업 유형: 오류 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

설치·업데이트 스크립트가 릴리즈 태그 설치 시 **체크섬이 발행된 자산과 동일한 파일**을 내려받도록 정합시켜, `opal-cli update` 하드 실패와 `install.sh`의 검증 무음 스킵을 동시에 해소한다.

## 배경

v0.6.11 릴리즈 직후 `opal-cli update` 실행이 체크섬 불일치로 하드 실패했다. 릴리즈 산출물 자체는 정상(무결성·VERSION 각인·export-ignore 모두 검증 통과)이며, 결함은 **소비 측(설치·업데이트 스크립트)** 에만 존재한다.

원인은 발행 자산과 다운로드 자산이 서로 다른 파일이라는 점이다. 릴리즈 워크플로우는 `git archive` 산출물에 대해 체크섬을 발행하는데, 스크립트들은 GitHub이 자동 생성하는 별개의 아카이브를 내려받는다. 두 파일은 압축 방식과 디렉토리 구조가 달라 해시가 원천적으로 일치할 수 없다.

이 결함은 릴리즈 워크플로우 도입(태스크 139) 이후 계속 존재했으나, 소유자 환경이 main 브랜치 기반 설치(`v0.6.8-1-g4cf9238`)여서 체크섬 분기 자체를 우회해 왔다. v0.6.11이 릴리즈 태그로 업데이트를 시도한 첫 사례다.

## 배경 분석 (대화에서 도출)

### A-1. 발행 자산 ≠ 다운로드 자산 (실측)

| 구분 | 파일 | SHA-256 | 상위 디렉토리 |
|------|------|---------|--------------|
| 발행 자산 (워크플로우 `git archive`) | `opal-v0.6.11.tar.gz` | `1ae94e27…` | 없음 (루트 직접) |
| 다운로드 자산 (GitHub 자동 아카이브) | `archive/refs/tags/v0.6.11.tar.gz` | `463a5842…` | `opal-0.6.11/` |

- `sha256sums.txt`에 기재된 값은 `1ae94e27…`이며, 발행 자산을 직접 받아 `shasum -a 256 -c` 실행 시 **OK**로 검증됨.
- 소유자 로그의 실제값 `463a5842…`는 자동 아카이브의 해시와 정확히 일치 — 재현 완료.
- 두 아카이브 모두 `export-ignore`·`export-subst`는 정상 적용됨(자동 아카이브의 `VERSION`도 `v0.6.11`로 각인). 즉 **내용 문제가 아니라 파일 동일성 문제**다.

### A-2. 결함 지점 3곳 — 소스 위치

| # | 파일 | 현상 | 근거 |
|---|------|------|------|
| A-2-1 | `opal/tools/opal-cli/lib/update.sh` | 자동 아카이브를 받아 `opal-${version}.tar.gz` 항목과 비교 → 하드 실패 | `opal/tools/opal-cli/lib/update.sh:132` (URL), `:181` (grep 대상) |
| A-2-2 | `scripts/install.ps1` | 로컬 파일명이 `opal-$OpalVersion.tar.gz`라 항목이 정확 매칭 → `throw` | `scripts/install.ps1:141` (파일명), `:98` (URL) |
| A-2-3 | `scripts/install.sh` | 로컬 파일명이 `opal.tar.gz`라 항목 미매칭 → **검증 무음 스킵** | `scripts/install.sh:180` (파일명), `:116` (URL), `:261` (스킵 분기) |

### A-3. 파급 범위 — 2곳 차단, 1곳 보안 갭

| 경로 | 릴리즈 태그(v*) 설치 시 현재 동작 | 판정 |
|------|--------------------------------|------|
| `opal-cli update` | 해시 불일치 하드 실패 | 차단 |
| `install.ps1` (Windows) | 예외 throw로 설치 중단 | 차단 |
| `install.sh` (mac/linux) | 항목 미매칭 경고 후 검증 생략하고 설치 진행 | 무결성 미검증 |
| main 브랜치 설치 | 기존 설계대로 UNVERIFIED 배너 | 정상 |

- `install.sh`의 미매칭은 grep 패턴 `opal.tar.gz`의 `.`이 정규식 와일드카드로 동작해 `opal-v0.6.11.tar.gz`와 매칭되지 않아 발생한다 — 실측으로 미매칭 확인.
- 결과적으로 mac/linux 신규 설치는 실패 대신 **검증 없이 통과**해 왔고, 무결성 검증 도입 의도(R-2·GC-001)가 무력화된 상태다.

### A-4. 구조 차이에 따른 파생 제약

발행 자산은 상위 디렉토리가 없다(`git archive`에 `--prefix` 미지정 — `.github/workflows/release.yml:33`). 다운로드 대상을 발행 자산으로 바꾸면 기존 `--strip-components=1` 추출이 루트 파일(`VERSION` 등)을 잘라내므로 추출 분기도 함께 조정해야 한다. 이미 발행된 v0.6.7~v0.6.11 자산이 전부 prefix 없음이므로, 워크플로우에 `--prefix`를 추가하더라도 **기존 릴리즈 호환 분기는 여전히 필요**하다.

## 확정된 설계 방향 (대화에서 합의)

| # | 방향 | 근거 |
|---|------|------|
| S-1 | 릴리즈 태그 설치 시 **다운로드 대상을 릴리즈 자산**(`releases/download/{tag}/opal-{tag}.tar.gz`)으로 전환한다 | 검증 대상과 다운로드 대상을 일치시키는 것이 근본 해소이며, provenance 증명(`attest-build-provenance`)도 이 자산을 대상으로 발행됨 (`.github/workflows/release.yml:37-40`) |
| S-2 | 릴리즈 자산이 없으면 **자동 아카이브로 폴백**하고, 이때는 기존 UNVERIFIED 경로(옵트인·프롬프트·비대화형 거부)를 그대로 적용한다 | "release 자산 없어도 항상 동작" 설계 의도(태스크 139) 보존 |
| S-3 | 추출 시 **상위 디렉토리 유무를 판정**하여 `--strip-components` 적용을 분기한다 | A-4 — 발행 자산은 prefix 없음, 자동 아카이브는 prefix 있음 |
| S-4 | `install.sh`의 파일명·grep 매칭 취약점을 정정한다 | A-3 — 무음 스킵이 검증 도입 의도를 무력화 |
| S-5 | 3개 경로(`install.sh`·`install.ps1`·`update.sh`)를 **동일 규약**으로 정합시킨다 | 플랫폼 독립성 원칙 (`docs/PROJECT.md` §프로젝트 원칙 3) |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 릴리즈 태그 설치·업데이트 시 다운로드 대상과 체크섬 발행 대상을 일치시켜 하드 실패 2건과 검증 무음 스킵 1건을 해소한다 | - | A-1 실측 해시 대조 |
| 범위 | **포함**: `scripts/install.sh`·`scripts/install.ps1`·`opal/tools/opal-cli/lib/update.sh` 3파일의 URL 결정·체크섬 검증·추출 분기 / **제외**: 재릴리즈(태그 발행)·`release.yml` 아카이브 형식 변경·main 브랜치 설치 경로 동작 | `release.yml` `--prefix` 추가 여부는 PLAN에서 판단 (추가하더라도 기존 릴리즈 호환 분기는 필수 — A-4) | A-4 |
| 제약 | 이미 발행된 v0.6.7~v0.6.11 릴리즈(전부 prefix 없음)에서 동작해야 한다 / 릴리즈 자산 부재 시 무중단 폴백 / 플랫폼 3경로 동일 규약 / 배포 경계 준수(`~/.opal/` 직접 편집 금지) | - | S-2·S-3·S-5, `.opal/AGENT.md` §금지사항 |
| 완료기준 | 3경로 × (릴리즈 태그 / 자산 부재 폴백 / main 브랜치) 조합에서 기대 동작이 실측 검증되고, 자동 아카이브 URL이 릴리즈 태그 경로에서 0건 잔존한다 | - | 요구사항 AC |

## 요구사항

- [ ] **F-1. `update.sh` 다운로드 대상 전환** — 릴리즈 태그(`v*`) 업데이트 시 릴리즈 자산 URL을 사용한다.
  - 어디에: `opal/tools/opal-cli/lib/update.sh` — tarball URL 결정부 (`:127-133`)
  - 왜: A-2-1 — 검증 대상과 다른 파일을 받아 하드 실패
  - AC: v0.6.11 태그로 `opal-cli update` 실행 시 체크섬 검증이 **통과**하고 설치가 완료된다. 릴리즈 태그 경로에서 `archive/refs/tags` URL 사용이 **0건**이다(폴백 분기 제외).

- [ ] **F-2. `install.sh` 다운로드 대상 전환 + 매칭 정정** — 릴리즈 자산을 받고, 체크섬 항목이 실제로 매칭되게 한다.
  - 어디에: `scripts/install.sh` — URL 결정부(`:112-118`), 로컬 파일명(`:180`), `verify_checksum` 매칭부(`:253-261`)
  - 왜: A-2-3 — 무음 스킵으로 무결성 검증이 무력화됨
  - AC: v0.6.11 태그 설치 시 "체크섬 검증 완료"가 출력된다. 항목 미매칭으로 인한 **스킵 경고가 발생하지 않는다**. 의도적으로 손상시킨 tarball에 대해서는 설치가 **거부**된다.

- [ ] **F-3. `install.ps1` 다운로드 대상 전환** — Windows 경로를 동일 규약으로 정합시킨다.
  - 어디에: `scripts/install.ps1` — URL 결정부(`:95-102`), 다운로드 파일명(`:141`), `Verify-Checksum`(`:164-231`)
  - 왜: A-2-2 — 현재 릴리즈 태그 설치가 예외로 중단됨
  - AC: v0.6.11 태그 설치 시 "체크섬 검증 통과"가 출력되고 설치가 완료된다.

- [ ] **F-4. 릴리즈 자산 부재 시 폴백** — 자산이 없으면 자동 아카이브로 폴백하고 기존 UNVERIFIED 정책을 적용한다.
  - 어디에: 3파일 공통 — URL 결정 + 체크섬 분기
  - 왜: S-2 — "release 자산 없어도 항상 동작" 설계 의도 보존
  - AC: 릴리즈 자산이 없는 태그에 대해 설치가 **중단되지 않고** 자동 아카이브로 진행되며, `OPAL_ALLOW_UNVERIFIED=1` 미지정 비대화형 환경에서는 기존대로 **거부**된다.

- [ ] **F-5. 추출 구조 분기** — 상위 디렉토리 유무에 따라 `--strip-components` 적용을 분기한다.
  - 어디에: 3파일 공통 — 추출부 (`update.sh:210-213`, `install.sh` `extract_to_tmp`, `install.ps1` 추출부)
  - 왜: A-4 — 발행 자산은 prefix 없음, 자동 아카이브는 prefix 있음
  - AC: 두 형식 모두에서 추출 결과 루트에 `VERSION`·`opal/`이 존재하고, 추출 후 `VERSION` 각인값이 `v0.6.11`로 읽힌다.

- [ ] **F-6. 3경로 × 3조합 실측 검증** — 플랫폼 경로별 동작을 증거와 함께 확인한다.
  - 어디에: TEST-SCENARIO.md
  - 왜: S-5 — 3경로 동일 규약 보장, self-confirming 방지
  - AC: `install.sh`·`install.ps1`·`update.sh` 각각에 대해 (릴리즈 태그 / 자산 부재 폴백 / main 브랜치) 3조합의 실행 증거가 기록되고 전부 기대 동작과 일치한다. Windows 실행이 불가한 환경이면 그 사유와 대체 검증 방법을 명시한다.

## 제약 조건

- 이미 발행된 릴리즈(v0.6.7~v0.6.11)는 전부 상위 디렉토리 없는 자산이므로, 재릴리즈 없이 **현행 자산에서 동작**해야 한다.
- 릴리즈 자산 부재 시에도 설치가 중단되지 않아야 한다 (기존 무중단 설계 보존).
- 무결성 검증을 우회하는 방향의 해소(예: 체크섬 비교 삭제, 조건부 스킵 확대)는 채택하지 않는다 — R-2·GC-001 의도 유지.
- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다."
- 플랫폼 분기는 어댑터 계층에서만 수행한다 (`.opal/AGENT.md` §금지사항 — 하드코딩된 플랫폼 분기 추가 금지).
- 재릴리즈(다음 패치 태그 발행)는 이 태스크 범위 밖이며 별도 소유자 승인을 받는다.

## 기술 스택

- Bash (`scripts/install.sh`, `opal/tools/opal-cli/lib/update.sh`)
- PowerShell (`scripts/install.ps1`)
- GitHub Actions (`.github/workflows/release.yml` — 참조 전용, 변경은 범위 밖)
- 검증 도구: `curl`, `shasum`/`sha256sum`, `tar`, `Get-FileHash`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | update.sh | `opal/tools/opal-cli/lib/update.sh` | 업데이트 경로 URL 결정·체크섬·추출 로직 (F-1·F-4·F-5) |
| D-2 | 소스 | install.sh | `scripts/install.sh` | mac/linux 설치 경로 동일 3지점 (F-2·F-4·F-5) |
| D-3 | 소스 | install.ps1 | `scripts/install.ps1` | Windows 설치 경로 동일 3지점 (F-3·F-4·F-5) |
| D-4 | 설계 | release.yml | `.github/workflows/release.yml` | 발행 자산 생성 방식·prefix 부재·provenance 대상 확인 (A-1·A-4) |
| D-5 | 설계 | .gitattributes | `.gitattributes` | `export-ignore`·`export-subst` 적용 범위 (A-1) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙(Guards·도구·배포 경계·플랫폼 분기) |
| D-7 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙 3(플랫폼 독립성)·프로젝트 구성 영역 매칭 |
| D-8 | 설계 | AGENT.md | `.opal/AGENT.md` | 금지사항(배포 경계·플랫폼 분기)·PM 검토 기준 |

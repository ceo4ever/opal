# TASK: 버전을 릴리스 아카이브에 각인 (export-subst) — 설치 시점 API 의존 제거

> 작성일: 2026-06-29 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (`//opds --agentic`)
> 출력: TASK.md

## 작업 목표

설치·업데이트 시 GitHub API로 버전을 결정하는 현 구조를 제거하고, **릴리스(git archive 생성) 시점에 버전을 산출물(`VERSION` 파일)에 각인**(`export-subst`)하여 설치기가 tarball 내 `VERSION`을 읽도록 전환한다. API 실패(403 rate limit·네트워크 차단) 시 버전 라벨이 `main`으로 오염되는 문제를 근본 제거한다.

## 배경

`opal-cli --version`이 `main`으로 표기되는 현상에서 출발. 현재 버전 관리 모델은 버전을 **소스에 두지 않고 설치 시점에 외부 조회로 결정**한다:

- `install.sh` `resolve_default_version()` / `update.sh` `cmd_update()`: ① GitHub API `/releases/latest` → ② `/tags?per_page=1` 폴백 → ③ 둘 다 실패 시 `main` 폴백
- `install-mac.sh:1223` 우선순위: `$OPAL_VERSION`(API로 해석) → `git describe`(git clone 경로) → `main` → `~/.opal/VERSION`에 기록
- 따라서 버전 라벨 = "설치기가 그 순간 어떤 ref를 알아내 받았는가"라는 런타임 결정 → API가 죽으면 버전을 알 수 없음 → `main`

## 배경 분석 (대화에서 도출)

| 사실 | 근거 (확인됨) |
|------|--------------|
| 저장소에 커밋된 `VERSION` 파일 없음 | `git ls-files \| grep VERSION` → 결과 없음 |
| 버전은 설치 시점 API 조회로 결정 | `install.sh:69-101` resolve_default_version / `update.sh:78-108` |
| API 폴백 종착점이 `main` | `install.sh:100`, `update.sh:106`, `install-mac.sh:1763` |
| 캡틴 PC가 `main`이 된 직접 원인 | `~/.opal/VERSION`=`main`, GitHub API `releases/latest`·`tags` 둘 다 **HTTP 403** (rate limit) 확인 |
| `.gitattributes` 이미 존재 (export-ignore 사용 중) | `tasks/`·`docs/`·`.opal/`·`.github/` export-ignore. export-subst는 미사용 |
| 릴리스 워크플로우가 `git archive` 사용 | `.github/workflows/release.yml:30` `git archive --format=tar.gz` |
| Windows 설치기도 버전 로직 보유 | `scripts/install.ps1` 존재 + 버전 처리 검출 |
| export-subst 메커니즘 동작 입증 | scratchpad 데모: 태그 archive→`VERSION`=`v0.6.5`, main archive→`v0.6.5-1-gd359eeb`, 작업트리→플레이스홀더 그대로 |

## 확정된 설계 방향 (대화에서 합의)

**방식 (B) — git-archive `export-subst`** 채택 (업계 표준 2갈래 중 "빌드 시점 각인"의 git 네이티브 변형). 릴리스 자동화 도구 도입(release-please 등, 방식 A)은 후속 과제로 분리.

핵심 메커니즘:
1. 루트에 `VERSION` 파일 생성, 내용은 한 줄 `$Format:%(describe:tags)$`
2. `.gitattributes`에 `VERSION export-subst` 추가
3. GitHub이 **태그 archive 생성 시 git이 치환** → tarball 내 `VERSION`에 실제 태그(`v0.6.5`)가 박힘
4. 설치기는 **추출한 tarball의 `VERSION`을 읽기만** 함 (API 미사용)
5. 플레이스홀더가 미치환(=git clone)이면 `git describe` 폴백 (기존 경로 유지)

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 버전을 릴리스 아카이브에 각인하여 설치기가 tarball 내 `VERSION`을 읽도록 전환, API 의존·`main` 오염 제거 | - | 배경 분석 표 전체 |
| 범위 | **포함**: ① 루트 `VERSION`(`$Format:...$`) + `.gitattributes` `export-subst` ② `install.sh`·`opal-cli/lib/update.sh`·`install-mac.sh`·`install.ps1`의 버전 결정을 "tarball 내 VERSION 우선 → 미치환 시 git describe 폴백"으로 전환. **제외**: 릴리스 자동화 도구(방식 A), v0.6.4 이하 소급 적용(불가) | - | 확정된 설계 방향 |
| 제약 | `~/.opal/` 직접 수정 금지(프로젝트 소스만)·플랫폼 분기는 install 어댑터 한정·export-subst는 새 태그(v0.6.5)부터 효과(검증은 로컬 git archive)·변경이력 행 추가 의무 | - | PM 프로필 금지사항 / `.gitattributes:8` |
| 완료기준 | (1) 로컬 `git archive <태그>` 산출 tarball의 `VERSION`에 실제 태그 각인 (2) 설치기가 API 미사용으로 tarball `VERSION`을 읽어 `~/.opal/VERSION` 기록 (3) API 완전 실패 시뮬레이션에서도 태그 설치본은 `main`이 아닌 정확 버전 (4) git clone 경로는 git describe 폴백 유지 (5) 4개 설치기(sh/ps1/mac/update) 동작 일관 | - | 확정된 설계 방향 |

## 요구사항

- [ ] **R1**: 루트에 `VERSION` 파일 생성 — 내용 한 줄 `$Format:%(describe:tags)$`. (어디에: 저장소 루트 / 왜: 각인 대상 / AC: 파일 존재 + 내용이 정확히 해당 플레이스홀더)
- [ ] **R2**: `.gitattributes`에 `VERSION export-subst` 추가 (단, export-ignore 대상에서 `VERSION`은 제외되지 않도록 확인). (AC: `git check-attr export-subst VERSION` → `set`)
- [ ] **R3**: `install.sh` `resolve_default_version`/다운로드 흐름을 "다운로드한 tarball에 `VERSION`이 있고 플레이스홀더가 치환되어 있으면 그 값을 사용, 아니면 기존 API/`git describe`/`main` 폴백"으로 전환. (AC: 태그 archive 설치 시 API 호출 없이 정확 버전 기록)
- [ ] **R4**: `opal-cli/lib/update.sh`를 R3과 동일 원칙으로 전환. (AC: API 403 시뮬레이션에서도 `--to <태그>` 및 latest 경로에서 tarball `VERSION` 우선 사용)
- [ ] **R5**: `install-mac.sh`의 VERSION 기록 우선순위(`:1223` 부근)에 "tarball 내 VERSION" 단계를 최상위로 삽입, 기존 `$OPAL_VERSION`→`git describe`→`main`은 폴백으로 강등. (AC: 우선순위 주석·코드 일치)
- [ ] **R6**: `install.ps1`을 R3과 동일 원칙으로 전환 (플랫폼 일관성). (AC: Windows 경로도 tarball `VERSION` 우선)
- [ ] **R7**: 회귀 테스트 — 로컬 `git archive`로 태그/브랜치/작업트리 3경로의 `VERSION` 결과를 검증하는 자동 테스트 추가. (AC: 태그→실태그, 브랜치→describe, 작업트리→플레이스홀더 미치환 폴백 확인)
- [ ] **R8**: 변경한 스크립트·문서의 변경이력 표에 행 추가 (일시 KST + 태스크 048).

## 제약 조건

- 배포 경계: `~/.opal/` 배포 파일 직접 수정 금지. 프로젝트 소스(`scripts/`, `opal/tools/opal-cli/`, `.gitattributes`, `VERSION`)만 수정 후 install 재배포는 캡틴이 수행.
- 플랫폼 분기는 install 어댑터 계층에서만 (로직에 하드코딩 금지).
- export-subst는 설정 커밋 이후 생성되는 archive부터 적용 → 첫 실효는 v0.6.5. 검증은 로컬 `git archive`로 가능(원격 태그 불필요).
- git clone(개발자) 경로에서는 플레이스홀더가 치환되지 않으므로 `git describe` 폴백을 반드시 유지.
- 커밋은 캡틴 명시 요청 시에만.

## 기술 스택

- Bash (install.sh, install-mac.sh, opal-cli/lib/update.sh — bash 3.2 호환 필요)
- PowerShell (install.ps1)
- git `export-subst` / `$Format:%(describe:tags)$` (git 2.32+)
- 테스트: shell 기반 (git archive 실측)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install.sh | `scripts/install.sh` | 버전 결정 로직 (resolve_default_version) |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh` | VERSION 기록 우선순위 (:1223) |
| D-3 | 소스 | opal-cli update | `opal/tools/opal-cli/lib/update.sh` | update 버전 결정 로직 |
| D-4 | 소스 | install.ps1 | `scripts/install.ps1` | Windows 버전 로직 (플랫폼 일관성) |
| D-5 | 소스 | .gitattributes | `.gitattributes` | export-subst 추가 + export-ignore 상호작용 |
| D-6 | 소스 | release workflow | `.github/workflows/release.yml` | git archive 기반 릴리스 — 각인 적용 지점 |

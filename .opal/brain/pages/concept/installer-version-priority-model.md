---
type: concept
title: 설치기 버전 결정 우선순위 모델 (4종 공통)
tags:
- version
- install
- priority
- architecture
sources:
- task:048
related:
- version-stamp-export-subst-decision
- opal-adapter-platform-isolation
created: '2026-06-29'
updated: '2026-06-29'
status: active
---
## 개념 요약

OPAL 설치기 4종(install.sh / install-mac.sh / install.ps1 / windows.ps1)이 공유하는 버전 결정 우선순위 모델이다. 태스크 048 이후 API 조회는 tarball URL 결정용으로만 존속하며, `~/.opal/VERSION`에 기록되는 버전은 각인값을 최우선으로 하는 4단계 우선순위로 결정된다.

## 배경·문제 (WHY)

설치 시점 API 조회 단일 의존 방식은 rate limit·네트워크 차단 시 `main`이 버전으로 기록되는 오염 문제가 있었다 (근거: task:048 PLAN.md §1.1). 각인값(tarball 내 VERSION)을 최우선으로 두면 API 완전 차단 환경에서도 정확한 버전이 기록된다. tarball URL을 결정하려면 추출 전 ref가 필요하므로 API 조회는 URL 결정용으로만 잔존하고, 버전 기록 결정은 추출 후 override하는 2단계 구조가 설계되었다.

## 결정 내용 (HOW)

**버전 결정 우선순위 (4종 설치기 공통)**:

| 우선순위 | 소스 | 조건 |
|---------|------|------|
| 1 | 추출된 tarball 루트의 `VERSION` 각인값 | `$Format:` 잔존 없음(치환 완료) |
| 2 | `$OPAL_VERSION` 환경변수 (one-liner installer 전달값) | 명시적 설정된 경우 |
| 3 | `git describe --tags` | git clone 경로 — `.git` 존재 시 |
| 4 | `main` | 모든 폴백 실패 시 |

**미치환 placeholder 판별 기준**: `$Format:` 문자열 잔존 여부 (부분 매칭)
- bash: `case "$stamped" in *'$Format:'*) : ;; esac` — bash 3.2 호환
- PowerShell: `$stamped -notlike '*$Format:*'` — 리터럴 `$` 매칭

**2단계 구조**: tarball URL 결정(`resolve_default_version`)은 추출 전 실행(API 조회 포함). 각인값 채택은 추출 후 override — URL용 ref 결정과 기록 버전 결정이 분리된다.

## 영향·관계

- `scripts/install.sh` — `adopt_stamped_version()`: `OPAL_EXTRACT_DIR/VERSION` → `OPAL_VERSION` override
- `scripts/install-mac.sh` — `record_installed_version()`: `FRAMEWORK_ROOT/VERSION` 최우선, `~/.opal/VERSION` 기록
- `opal/tools/opal-cli/lib/update.sh` — 추출 후 `extract_dir/VERSION` → `version` 변수 override
- `scripts/install.ps1` — 추출 후 `$extractDir/VERSION` → `$script:OpalVersion` override
- `scripts/install/windows.ps1` — `$repoRoot/VERSION` 최우선 읽기 (install-mac.sh 대칭)

[[version-stamp-export-subst-decision]] — 각인 메커니즘 설계 전체

## 근거 출처

- task:048 DONE.md §버전 결정 우선순위
- task:048 PLAN.md §3.2~3.5 (설치기별 설계 상세)

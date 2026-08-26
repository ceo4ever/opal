---
type: concept
title: 버전 결정 모델 전환 — 설치 시점 API 조회 → 릴리스 시점 export-subst 각인
tags:
- version
- install
- git
- export-subst
- architecture
sources:
- task:048
related:
- installer-version-priority-model
- red-test-commit-coercion-guard-lesson
- opal-adapter-platform-isolation
created: '2026-06-29'
updated: '2026-06-29'
status: active
---
## 개념 요약

OPAL 설치·업데이트가 버전을 결정하는 방식을 "설치 시점 GitHub API 조회"에서 "릴리스(git archive) 시점 git이 VERSION 파일에 실태그를 각인(export-subst)"하는 구조로 전환했다. 버전은 산출물(tarball)의 속성이며, 설치기는 읽기만 한다. API 403·네트워크 차단과 무관하게 정확한 버전이 기록된다.

## 배경·문제 (WHY)

GitHub API(`/releases/latest`, `/tags`)는 rate limit 403이나 네트워크 차단 시 응답하지 않아 버전 라벨이 `main`으로 오염되는 문제가 있었다 (근거: `scripts/install.sh:100`, `opal/tools/opal-cli/lib/update.sh:107`). 버전 정보를 외부 네트워크에 의존하지 않고 릴리스 산출물 자체에 포함시키는 것이 근본 해결책으로 채택되었다 (근거: task:048 PLAN.md §1.1).

## 결정 내용 (HOW)

**각인 메커니즘**:
- 루트 `VERSION` 파일 한 줄: `$Format:%(describe:tags)$`
- `.gitattributes`에 `VERSION export-subst` 규칙 추가
- `git archive <태그>` 실행 시 git이 placeholder를 실태그(`v0.6.5` 등)로 자동 치환
- git clone(개발자 작업트리)은 `$Format:%(describe:tags)$` 미치환 상태 유지 → `git describe` 폴백으로 처리

동작 경로별 치환 결과:
- 태그 archive (릴리스 tarball) → `v0.6.5` (clean 태그)
- HEAD-after-tag archive → `v0.6.5-3-gabcdef7` (describe 형식)
- git clone / 작업트리 → `$Format:%(describe:tags)$` (미치환 placeholder)

**설치기 판별 원칙 (4종 공통)**: 추출된 tarball의 `VERSION` 파일을 읽어 `$Format:` 문자열이 잔존하면 미치환(폴백 유지), 잔존하지 않으면 각인값을 채택해 `OPAL_VERSION`을 override한다.

**실효 제약**: export-subst는 설정 커밋 이후 생성되는 archive부터 적용된다. v0.6.4 이하 소급 불가. 첫 효과는 v0.6.5.

## 영향·관계

- `VERSION` (신규) — 루트 각인 플레이스홀더
- `.gitattributes` — `VERSION export-subst` 규칙 추가
- `scripts/install.sh` — `adopt_stamped_version()` 헬퍼 추가, extract 후 호출
- `opal/tools/opal-cli/lib/update.sh` — 추출 직후 각인값으로 `version` override
- `scripts/install-mac.sh` — `record_installed_version()` 함수 분리, 각인값 최우선
- `scripts/install.ps1` — 추출 후 `$extractDir/VERSION` 읽어 `-notlike '*$Format:*'` 판별
- `scripts/install/windows.ps1` — `$repoRoot/VERSION` 각인값 최우선 읽기 (install-mac.sh 대칭)

[[installer-version-priority-model]] — 우선순위 모델 상세
[[red-test-commit-coercion-guard-lesson]] — 이 전환에서 발생한 RED 테스트 설계 결함 교훈

## 근거 출처

- task:048 DONE.md (결과 요약·변경 파일 목록)
- task:048 PLAN.md §1.1, §3.1 (설계 배경·메커니즘 실측 검증)
- task:048 AGENTIC-LOG.md (가드 위반 적발·정정 이력)

## 관련 페이지

- [[opal-adapter-platform-isolation]]

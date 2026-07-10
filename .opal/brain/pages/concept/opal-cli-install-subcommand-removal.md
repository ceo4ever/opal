---
type: concept
title: opal-cli install 서브커맨드 완전 제거 — 컨텍스트별 리다이렉트 원칙
tags:
- install
- opal-cli
- deploy
- ux
sources:
- task:055
related:
- installer-version-priority-model
- linux-install-script
created: '2026-07-10'
updated: '2026-07-10'
status: active
---
## 개념 요약

`opal-cli install` 서브커맨드를 디스패처에서 완전 제거했다(리다이렉트 스텁 없음). 이식 경로는 이미 3종으로 완비되어 있었다 — 신규 설치는 원라이너(`scripts/install.sh` / `install.ps1`), 기존 배포본 갱신·복구는 `opal-cli update`(원격 tarball + 데이터 보존), 개발자 로컬 배포는 `install-mac.sh` 직접 실행. `opal-cli install`은 이 셋 중 어디에도 속하지 않는 네 번째 진입점으로, 로컬 소스(FRAMEWORK_ROOT/소스 레포)가 있어야만 동작하는 수동 명령이었다.

## 배경·문제 (WHY)

`opal-cli install`은 소스가 없는 머신에서 실행하면 "설치 스크립트를 찾을 수 없음 → clone 하라"로만 안내되는 UX 함정이었다(근거: task:055 DONE.md §배경). 즉 이 서브커맨드는 소스 레포 존재를 전제하는데, 정작 그 전제가 필요한 사람(신규 사용자)일수록 소스가 없다는 역설이 있었다. 이미 완비된 원라이너·update 경로와 기능이 중복되면서도 실패 모드가 더 나쁜 진입점이었기 때문에, 소유자 결정으로 스텁 없는 완전 제거를 채택했다(근거: task:055 DONE.md §핵심 설계 결정).

## 결정 내용 (HOW)

**완전 제거, 리다이렉트 스텁 없음**: `opal-cli install` 입력은 dispatch의 `*)` unknown 분기로 흡수되어 "알 수 없는 서브커맨드" + usage 출력 후 exit 1(설치 시도 자체가 없음). `lib/install.sh`는 git rm으로 삭제(근거: `opal/tools/opal-cli/run.sh`, `opal/tools/opal-cli/lib/install.sh` — task:055 DONE.md §변경 내역).

**컨텍스트별 리다이렉트 원칙 (D-A 표준)** — install을 대체하던 연쇄 안내 문구는 상황에 따라 다른 명령으로 분기한다:

| 상황 | 판별 조건 | 리다이렉트 대상 | 이유 |
|------|----------|----------------|------|
| 미설치 | `~/.opal` 부재 | 신규 설치 원라이너 | `opal-cli update`는 `~/.opal` 존재를 전제하므로 이 상황에서 안내하면 순환(H-3) |
| 배포본 손상 | `~/.opal` 존재, 컴포넌트(uvicorn/dashboard/doctor 등) 누락 | `opal-cli update` (재배포, 데이터 보존) | 신규 설치가 아니라 복구가 정답 — 원라이너로 안내하면 사용자 혼란(H-5) |

**순환 방지 근거**: `update.sh`는 자기 자신이 "update 실행 중 미설치 감지"를 처리하는 코드 경로이므로, 여기서 다시 `opal-cli update`를 안내하면 순환 안내가 된다. `cmd_update`는 `~/.opal` 부재 시 진행 자체가 불가능하므로 반드시 원라이너를 안내해야 한다(근거: task:055 PLAN.md §H-3, `update.sh`).

**기각된 대안**: "install=OS 감지 + 기존 삭제 + 원격 재설치"안은 사용자 데이터 소실 위험이 있거나 `update`와 기능이 중복되어 배제했다.

## 영향·관계

- `opal/tools/opal-cli/run.sh` — dispatch case에서 `install` 제거, usage 목록·`--version` fallback 문구 갱신.
- `opal/tools/opal-cli/lib/install.sh` — 삭제(참조 0).
- `opal/tools/opal-cli/lib/update.sh` — 미설치 감지 안내를 원라이너로 교체(순환 회피).
- `opal/tools/opal-cli/lib/doctor.sh`, `lib/console.sh` — 컴포넌트 누락 안내를 `opal-cli update`로 교체.
- `opal/tools/opal-cli/README.md`, `docs/ARCHITECTURE.md` — install 언급 제거·서브커맨드 목록 정합화.
- [[installer-version-priority-model]] — 동일 이식 경로 4종(install.sh/install-mac.sh/install.ps1/windows.ps1)의 버전 결정 모델과 배포 채널 맥락을 공유.

## 근거 출처

- task:055 DONE.md §배경, §핵심 설계 결정, §변경 내역
- task:055 PLAN.md §H-3, §H-5, §3.2.2 리다이렉트 표준안(D-A)

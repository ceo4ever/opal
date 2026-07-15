---
type: concept
title: 콘솔 쓰기 예외 라우터 격리 패턴
tags:
- architecture
- console
- security
- pattern
- write-isolation
sources:
- task:036
- task:061
related:
- daemon-as-tool-orchestrator
- opal-console
- opal-security-model
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

읽기 전용 원칙의 콘솔 대시보드에서 예외적으로 쓰기가 필요한 기능이 생기면, 쓰기 권한을 전용 라우터 1곳에만 몰아주고 쓰기 대상 파일을 명시 화이트리스트로 한정하는 아키텍처 패턴이다. 브레인 질의 라우터(선례)에 이어 설정 라우터에 두 번째로 적용되면서, 반복 가능한 표준 패턴으로 확립되었다.

## 배경·문제 (WHY)

- 콘솔은 원칙적으로 읽기 전용 대시보드로 설계되었다 — 데몬은 도구 오케스트레이터이고 데이터 SSOT는 각 프로젝트 파일이다(근거: task:021, [[daemon-as-tool-orchestrator]]).
- 그러나 실제 사용에서 예외적 쓰기가 필요한 기능이 반복적으로 발생한다 — 첫 사례는 브레인 질의(브레인 세션 프라임·질의 제출)였고, 두 번째 사례는 설정 화면의 프라임 풀 토글이었다.
- 데몬이 127.0.0.1 로컬 바인딩·무인증으로 동작하므로(근거: task:061 TASK.md §제약 조건), 쓰기 가능 경로가 늘어날수록 공격 표면이 넓어진다는 위험이 있다(추론: 코드패턴 — 무인증 로컬 데몬 특성상).
- 대안으로 "필요한 라우터마다 개별적으로 쓰기를 허용"하는 방식도 있었으나, 쓰기 지점이 분산되면 검토·감사가 어려워진다는 트레이드오프로 기각되었다(추론: 코드패턴).

## 결정 내용 (HOW)

- 쓰기 가능 라우터를 파일 단위로 격리한다 — 브레인 질의는 브레인 라우터 하나에만(근거: task:036, `dashboard/backend/routers/brain.py:6` "LLM 호출은 이 라우터에만 격리"), 설정 쓰기는 설정 라우터 하나에만(근거: task:061, `dashboard/backend/routers/config.py:6` "브레인 라우터 격리 원칙 준수") 한정한다.
- 쓰기 대상 파일을 명시 화이트리스트로 제한한다 — 설정 라우터의 경우 `~/.opal/console.config.json` 1종(`prewarm_projects` 필드 갱신 한정, task:061 범위 축소 기준)만 허용한다.
- 요청 본문의 경로 문자열을 그대로 신뢰하지 않고, 서버가 사전에 검증한 프로젝트 목록과 대조해 절대경로를 재구성한다(`_require_project_path`, `dashboard/backend/routers/config.py:57-73` — 빈 값·비스캔 프로젝트는 400 거부 + 거부 로깅).
- 두 라우터 모두 LLM/서브프로세스 호출을 자기 자신에게만 격리한다 — 설정 라우터는 LLM 호출 0회(파일 쓰기 + `prewarm()` 호출만 수행).
- 기존 read-only 라우터·어댑터(대시보드/프로젝트/태스크/메모리/환경)는 쓰기 호출을 절대 추가하지 않는다.

## 영향·관계

- `dashboard/backend/routers/brain.py` — 1번째 적용(브레인 질의 POST, task:036).
- `dashboard/backend/routers/config.py` — 2번째 적용(설정 프라임 토글 POST, task:061).
- 향후 콘솔에 새 쓰기 기능이 추가될 때(예: console.config 전반 편집·프로젝트 로컬 설정 편집 — [[console-settings-incremental-scope-policy]] 참조) 이 패턴을 그대로 재사용할 것으로 예상된다.
- [[daemon-as-tool-orchestrator]] — 이 패턴이 예외를 두는 상위 원칙.
- [[opal-console]] — 이 패턴이 적용되는 대상 컴포넌트.
- [[opal-security-model]] — 무인증 로컬 데몬 전제 하에서 쓰기 표면을 최소화하는 보안 원칙과 정합.

## 근거 출처

task:036(브레인 POST 선례) · task:061 PLAN.md §3.1.2, TASK.md §제약 조건 · `docs/ARCHITECTURE.md` §OPAL Console "[예외·격리]" 다이어그램 표기.

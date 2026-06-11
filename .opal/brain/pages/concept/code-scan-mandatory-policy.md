---
type: concept
title: code-scan 무조건화 규약 — 코드 작업 한정 강제 (010)
tags:
- code-scan
- pm
- policy
- dispatch
sources:
- task:010
related: [wiki-intelligence-decisions-016, brain-tool]
created: '2026-06-11'
updated: '2026-06-11'
status: active
---

## 개요

코드 변경·코드 탐색이 필요한 작업에 한해, PM 디스패치 전 code-scan 호출을 조건부 옵션에서 **무조건 1순위 강제**로 격상했다. scan.json 부재 시 인터럽트 없는 즉석 자동 생성, 빈 결과 폴백 3분기, 사용자 오버라이드를 규약화한다.

## 결정 배경 (WHY)

code-scan 활용률이 낮은 근본 원인은 트리거가 조건부였기 때문이다:

- `dispatch-process.md` §code-scan 사전 범위 파악이 "`.opal/code-scan.json`이 존재하는 프로젝트에서" 조건부 진입이었고, "없으면 Glob/Grep 폴백"이라는 회피 경로가 매끄럽게 제공됐다.
- `core/AGENT.md`도 동일 조건부 문구 + "scan.json 없으면 사용 생략" 회피 경로 존재.
- 016 opal-brain 도입 이후 `brain-tool analyze`가 code-scan @header 집계에 종속되므로, code-scan 보급률이 brain 지식 품질의 상한이 된다는 새로운 인센티브가 확인됐다.

## 결정 내용

### F-1 코드 작업 무조건화

**코드/문서 판별 기준**: 변경·탐색 대상에 code-scan 지원 확장자(코드 파일) 또는 코드 구조 이해가 포함되면 **코드 작업**, 순수 .md 문서·기획·정책만이면 **문서 작업**.

- 코드 작업이면 디스패치 전 code-scan **무조건 호출**. 순수 문서 작업만 명시적 스킵 허용.
- 적용 위치: `opal/core/references/pm/dispatch-process.md` v1.4 + `opal/core/AGENT.md` v3.3 + `opal/core/references/opal-pm.md` v1.2 §9

### F-3 scan.json 즉석 자동 생성

PM이 code-scan을 첫 호출하는 시점에 `.opal/code-scan.json`이 부재하면, **사용자 인터럽트 없이 즉석 추론으로 생성**한다:

| 항목 | 추론 소스 |
|------|----------|
| `scopes` | `docs/PROJECT.md §프로젝트 구성` 요소·경로 표 (부재 시 1-depth 스캔) |
| `extensions` | 프로젝트 실재 확장자 자동 감지 + `.md` 기본 포함 |
| `exclude` | 기본값 + `backup`·`.pytest_cache`·`.next`·`.nuxt` 등 보강 |

생성 직후 보고 형식: "`📂 code-scan.json 자동 생성: scopes={N}종 · extensions=[...] · exclude=[...]`"

적용 위치: `opal/core/references/pm/code-scan-management.md` v1.1

### F-4 빈 결과 폴백 3분기

| 분기 | 조건 | 대응 |
|------|------|------|
| ① 매칭 0건 | `search`/`exports` 결과 0건 | Glob/Grep 보강 (code-scan 결과 + 추가 탐색) |
| ② 저커버리지 | `scan`/`domain`/`layer` @header 커버리지 30% 미만 | code-scan + Glob/Grep 동시 활용 |
| ③ 정상 | 그 외 | code-scan 결과만 |

폴백(①②) 발동 시 STATE.md **자유 텍스트 영역**(블로커/다음 액션 — 현황판 표 행 아님, state-tool 비경유)에 `code-scan 폴백: {사유}` 1줄 기록.

적용 위치: `opal/core/references/harness/header-rules.md` v1.1

### F-5 PM Gate 14번 항목

코드 변경 태스크의 디스패치 컨텍스트에 code-scan 결과(domain/layer/depends/exports)가 인용되었는지 검증. 순수 문서 작업은 N/A.

적용 위치: `opal/core/references/harness/pm-review-gate.md` v1.5

## 영향 범위

- `opal/core/references/pm/dispatch-process.md` — 무조건화·자동생성·폴백 체인 (v1.4)
- `opal/core/AGENT.md` — 역할 분담 표 + 오버라이드 + 자동 생성 교체 (v3.3)
- `opal/core/references/pm/code-scan-management.md` — 즉석 생성 규약 (v1.1)
- `opal/core/references/harness/header-rules.md` — 폴백 3분기 표 + STATE 기록 규약 (v1.1)
- `opal/core/references/harness/pm-review-gate.md` — Gate 14번 항목 신설 (v1.5)
- `opal/core/references/opal-pm.md` — §9 무조건화 정합 (v1.2)

## 관련

- [[wiki-intelligence-decisions-016]] — brain↔code-scan 역할 분담의 원점 결정 (016)
- [[brain-tool]] — analyze/sync-header가 code-scan @header 의존 — 이 규약의 brain 품질 상한 근거

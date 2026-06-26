---
type: concept
title: 도구 사용법 선확인·에러 종류 진단후 폴백 규율
tags: [design-principle, tool-usage, mams-lesson, fallback, error-handling]
sources: [task:044]
related: []
created: 2026-06-26
updated: 2026-06-26
status: active
---

## 개요

도구를 처음 호출하기 전 서브명령·인자를 추측하지 말고 `tool-scan usage <도구>` 또는 도구의 `--help`(live)로 사용법을 먼저 확인한다. 실패 시에는 에러 종류를 진단한 후 폴백 여부를 결정한다 — 맹목적으로 다른 도구로 갈아타는 것은 금지다. MAMS cmux 사건(존재하지 않는 `take-screenshot` 서브명령 추측 호출 → 무분별 Playwright 폴백)의 재발 방지를 위해 AGENT.md 규율 문단으로 명문화됐다. (근거: task:044 DONE.md §1, PLAN.md §F-005 R-6·R-7)

## 결정 배경 (WHY)

cmux-tool은 12개 서브명령을 가지지만 AGENT.md 인지 맵에 cmux-tool 행이 없고 localhost 접근 행이 playwright MCP만 안내하고 있었다. 이 오라우팅 상태에서 PM이 서브명령을 추측하면 존재하지 않는 명령을 호출하게 되고, 실패 시 즉시 Playwright로 폴백하는 패턴이 발생했다. 이는 문제의 근원을 진단하지 않고 다른 도구로 도망가는 맹목 폴백이다. (추론: 코드패턴 `opal/core/AGENT.md:254` 수정 전 상태)

## 결정 내용

**사용법 선확인 규율** (AGENT.md §도구·MCP 적극 활용 규칙에 명문화):
- 도구를 처음 호출하기 전, 추측하지 말고 정확한 서브명령·인자를 확인한다.
- 확인 경로: `tool-scan usage <도구>` 또는 도구의 `--help`(live).

**에러 시 종류 기반 진단 후 폴백** (맹목 폴백 금지):
- 호출이 실패하면 다른 도구로 즉시 갈아타지 말고 에러 종류를 먼저 진단한다.
- `usage` 에러(잘못된 서브명령·인자 오류) → **호출 수정**, 폴백 금지.
- `cmux_not_installed` 등 환경 부재 에러 → **폴백 허용**.
- cmux-tool manifest `fallback` 계약이 에러 종류별 허용 여부를 명시한다.

**올바른 도구로 채널링**:
- 정식 OPAL 래퍼(예: `cmux-tool`)가 있으면 raw 외부 CLI(`cmux` 직접) 대신 래퍼를 사용한다.

## 영향 범위

- `opal/core/AGENT.md` — §도구·MCP 적극 활용 규칙에 사용법 선확인·에러 진단후 폴백 문단 추가
- `opal/tools/tool-scan/manifest.json` — cmux-tool `fallback` 에러계약 필드
- `~/.opal/AGENT.md` — install 재배포 후 실세션 발효

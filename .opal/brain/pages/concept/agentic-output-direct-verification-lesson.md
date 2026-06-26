---
type: concept
title: agentic 산출물 직접 검증 의무 — PM 직접 실행이 self-confirming을 포착
tags: [lesson, verification, self-confirming, pm-discipline, red-first]
sources: [task:044]
related: []
created: 2026-06-26
updated: 2026-06-26
status: active
---

## 개요

단위 테스트가 모두 GREEN이어도 PM이 직접 실행 검증을 수행하지 않으면 숨겨진 버그를 놓칠 수 있다. tool-scan 태스크에서 워커(opal-test-agent + opal-be-agent)가 22/22 GREEN을 보고했지만, PM이 직접 실행한 결과 `usage <tool>`이 대상 도구가 아닌 tool-scan 자기 자신의 `--help`를 반환하는 버그를 발견했다. 테스트가 stub 주입으로 실제 경로 해석 로직을 검증하지 못한 맹점이었다. (근거: task:044 DONE.md §4)

## 결정 배경 (WHY)

`usage` 서브명령은 대상 도구의 `run.sh --help`를 실행해야 한다. 실제 구현(`tool_scan.py:275`)에서 `_TOOL_DIR/run.sh`를 참조할 때 tool-scan 자기 자신의 `TOOL_DIR`를 사용해 자기 `run.sh`를 실행하고 있었다. 단위 테스트는 항상 `TOOL_SCAN_HELP_CMD` 환경변수로 stub을 주입해서 실제 경로 해석 코드 경로를 실행하지 않았다. 따라서 테스트는 GREEN이지만 실제 동작은 틀렸다. (근거: task:044 DONE.md §4 `tool_scan.py:275`)

## 결정 내용

- **PM 직접 실행 검증 의무**: 워커가 GREEN을 보고해도 PM이 직접 핵심 기능을 실행 검증하는 것은 선택이 아니라 의무다. 특히 도구 자신이 주제인 작업(tool-scan: 도구 사용법 확인 도구)은 더욱 그렇다.
- **단위 테스트 stub 맹점 인식**: stub/mock 주입은 격리를 보장하지만 실제 경로 해석·환경 통합 로직을 우회한다. L3b(smoke test) 수준의 실제 환경 실행 검증이 보완 필요하다.
- **도구 자체 로직 = RED-first 작성자 ≠ 구현자**: 자기 도구 로직(특히 경로·환경 의존)은 구현자가 테스트를 작성하면 self-confirming 위험이 높다. RED-first 분리 원칙이 필수다. (근거: task:044 PLAN.md §H-2, R-2)
- **fix**: `~/.opal/tools/<name>/run.sh` 경로 해석 로직으로 수정. fix 루프 1/3으로 해결.

## 영향 범위

이 교훈은 tool-scan 특정이 아닌 모든 OPAL 도구 개발에 적용되는 PM 검증 규율이다. agentic 파이프라인에서 워커가 "통과" 보고를 해도 PM이 직접 실행 검증하는 절차가 self-confirming 오류를 포착하는 마지막 안전망이다.

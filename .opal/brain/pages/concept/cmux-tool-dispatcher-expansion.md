---
type: concept
title: cmux-tool 범용 디스패처 확장 (12+1종 서브명령)
tags:
- tool
- cmux
- dispatcher
- task
sources:
- task:007
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

`cmux-tool`을 cmux browser 공식 명령 12+1종을 노출하는 범용 디스패처로 확장하고, `opal/core/references/tools.md`에 5행 트리거 매트릭스로 등록했다. WebFetch를 완전 제거하고 cmux→playwright 2단 체인으로 단순화했다.

## 배경·문제 (WHY)

기존 cmux-tool이 extract 모드 1종만 지원했다. 웹 크롤링·E2E·정보 수집·웹 테스트에서 cmux 명령을 다목적으로 활용하려면 서브명령 라우터가 필요했다.

## 결정 내용 (HOW)

- 12+1종 서브명령: 필수 7(navigate/click/fill/snapshot/screenshot/eval/extract) + 선택 5 + 레거시 `extract`.
- 공통 5필드 출력: `ok`/`command`/`surface`/`user_owned`/`error` + 명령별 특화.
- 폴백 트리거 4종: `not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed` → playwright 직행(silent).
- `opal-wtm-agent`: `command -v cmux` 단일 분기로 OS+설치 흡수, silent fallback(요약 필드에 표기 없음).
- 신규 lib/ 4개 + examples/ 2개 + docs/CMUX-REFERENCE.md 추가.

## 영향·관계

- `opal/core/references/tools.md` 신규 섹션 추가.
- [[wtm-agent-cmux-integration]] 에서 시작된 cmux 통합의 2단계 심화.

## 근거 출처

`sources: task:007` — DONE.md §핵심 결정 M-1~M-7 참조.

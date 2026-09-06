---
type: entity
title: header-standard.md — @header 작성 표준
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- header-standard
- reference
- code-scan
sources:
- task:107
related:
- code-scan-tool
- regulation-tool-four-way-mismatch
- prohibit-by-property-not-name
- tag-removal-is-not-history-removal
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

`@header` 메타블록의 필드 정의·작성 기준·삽입 위치·2소스(인라인/code-map) 표현 규칙을 정하는 표준 문서다. 태스크 107 이전에는 필드 정의(§2)와 exports 작성 가이드(§4)만 있었고 "이력을 어디에 어떻게 남기는가"에 대한 원칙이 없어, 워커들이 `description`·`note`에 시점별 변경을 append하는 관행이 누적됐다(근거: `opal/core/references/header-standard.md`; `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` §1).

## 책임 (WHAT)

- 필드 정의: `module`·`layer`·`domain`·`description`·`exports`·`depends`·`note`·`feature` 8필드의 필수 여부·타입·의미를 규정한다(`opal/core/references/header-standard.md` §2).
- 이력 비기재 원칙(§2.1, 태스크 107 신설): `@header`의 어느 필드에도 변경 이력을 기재하지 않는다 — 이력의 소재는 `git log`와 `tasks/{NNN}-*/DONE.md` 2곳뿐이며, `@header`는 현재 시점의 사실만 담는다. 필드 갱신은 이전 값 옆에 덧붙이지 않고 제자리에서 교체한다. 적용 범위는 `@header` JSON 블록 전체다(근거: `opal/core/references/header-standard.md` §2.1, task:107).
- 이력 전용 필드 신설 금지(§2, 태스크 107 신설): `changelog`·`history`·`revisions` 등 이름을 불문하고 이력 전용 필드를 만들지 않는다(근거: task:107 `AGENTIC-LOG.md` "[DECISION] `changelog` 28건 전건 편입" 절).
- `description`·`depends`·`note`·`feature` 작성 가이드(§4.2, 태스크 107 신설): 각 필드가 "담는 것"과 "담지 않는 것"을 표로 구분한다 — 특히 `description`·`note`는 "서로 다른 태스크 번호가 2개 이상 쌓이는 형태"를 담지 않는 것으로 명시하고, 자산의 출신 태스크 1개를 단발로 인용하는 것은 허용한다(근거: `opal/core/references/header-standard.md` §4.2).

## 설계 배경 (WHY)

이력 비기재 원칙과 임계값 2는 임의 선택이 아니다 — "단발 출처 인용(1개)"과 "이력 누적(2개 이상)"을 가르는 축 정의 자체의 귀결이며, `code-scan.js`의 `TASK_TAG_THRESHOLD` 상수와 같은 근거를 공유한다(근거: task:107 PLAN §3.2.2 (A), `opal/core/references/header-standard.md` §4.2 "임계값 근거"). 규정 문면과 감지 도구가 이 근거를 함께 참조하도록 설계된 것은, 같은 태스크에서 규정과 도구가 네 방향으로 어긋난 경험(→ [[regulation-tool-four-way-mismatch]]) 때문에 사후에 정합성을 명시적으로 맞춘 결과다(근거: task:107 `AGENTIC-LOG.md`).

`changelog` 등 이름을 불문하는 금지 조항은, 이름 하나를 금지해도 다른 이름으로 부활 가능하다는 문제를 규정 문면 차원에서 막기 위함이다(근거: [[prohibit-by-property-not-name]]).

## 관계 (HOW)

- [[code-scan-tool]] — `code-scan validate`가 이 문서 §2.1·§4.2의 규정을 `header_history`·`undeclared_field` 비차단 경고로 집행한다.
- [[regulation-tool-four-way-mismatch]] — 이 문서와 `code-scan.js`가 함께 개정되며 겪은 규정-도구 불일치 4건.
- [[prohibit-by-property-not-name]] — §2 "이름 불문" 조항의 설계 논리.
- [[tag-removal-is-not-history-removal]] — §2.1 원칙을 적용할 때 "태그만 제거"로는 불충분하다는 실측.

## 소스 커버리지

| 절 | 경로 | 설명 |
|----|------|------|
| §2 필드 정의 | `opal/core/references/header-standard.md:11` | 8필드 표, 이력 전용 필드 신설 금지 조항 |
| §2.1 이력 비기재 원칙 | `opal/core/references/header-standard.md:41` | 태스크 107 신설 |
| §4.2 작성 가이드 | `opal/core/references/header-standard.md:173` | `description`·`depends`·`note`·`feature` 담는 것/담지 않는 것 |

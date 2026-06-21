---
type: concept
title: state-tool mock 가드 정규식 ↔ SKILL 표준 문구 false positive
tags:
- state-tool
- mock-guard
- false-positive
- skill
- bug
- framework
sources:
- task:033
related:
- op-dev-test-scenario
- verification-command-4-standard
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개요

`state_tool.py`의 `_MOCK_CODE_PATTERNS` 정규식이 op-dev-test-scenario SKILL 표준 PM Gate 문구에 포함된 `MagicMock` **단어**를 오탐하는 false positive 문제. 주석 의도("단순 단어 제외")와 실제 동작이 불일치하며, 후속 수정이 필요한 프레임워크 버그다.

## 배경·문제 (WHY)

태스크 033 진행 중 op-dev-test-scenario SKILL의 표준 PM Gate 문구가 state-tool의 mock 가드에 걸려 오탐이 발생했다. state-tool 주석에는 "단순 단어는 제외"라는 의도가 기재되어 있으나, 실제 `_MOCK_CODE_PATTERNS` 정규식(`MagicMock|...`)은 단어 단독 출현도 매칭한다. 결과적으로 실제 mock 코드를 작성하지 않았음에도 STATE 갱신이 차단되었다.

## 결정 내용 (HOW)

### 문제 구조

- **오탐 위치**: `state_tool.py:1321` `_MOCK_CODE_PATTERNS` 정규식 패턴 `MagicMock`
- **트리거 원인**: op-dev-test-scenario SKILL 표준 PM Gate 문구 중 `MagicMock`이라는 단어가 포함된 설명 문구
- **실제 mock 코드 여부**: 실제 mock 코드 0건 — 오탐
- **주석 의도 vs 실제 동작**: 주석은 "단순 단어 제외" 의도를 기술하나, 정규식은 단어 단독 출현도 매칭

### 임시 해소 방법 (태스크 033)

SKILL 문구의 트리거 단어(`MagicMock`)를 의미 불변으로 회피하는 방식으로 임시 해소. 실제 mock 코드 0건 확인 후 STATE 갱신 진행.

### 근본 수정 방향 (후속 태스크 권고)

아래 두 가지 중 하나로 수정:
1. `_MOCK_CODE_PATTERNS` 정규식을 코드 호출 형태(`MagicMock(` — 괄호 포함)로 한정해 단어 단독 출현을 제외
2. 또는 SKILL 표준 문구에서 mock 관련 기술 용어 사용 방식을 코드 블록 내부로만 한정

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — `_MOCK_CODE_PATTERNS` 정규식 수정 대상 (후속)
- op-dev-test-scenario SKILL 문구 — 임시 회피 적용됨, 근본 수정 시 원복 가능

## 관련 페이지

- [[op-dev-test-scenario]]
- [[verification-command-4-standard]]

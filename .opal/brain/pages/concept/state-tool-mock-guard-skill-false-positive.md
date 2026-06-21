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
- task:034
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

### 근본 수정 완료 (태스크 034)

두 층위로 근본 수정했다. 실제 mock 코드 검출(헌법 §4)은 보존하고 오탐만 제거.

**#1 — 정규식 오탐 (산문)**: `_MOCK_CODE_PATTERNS`에서 첫 대안 `MagicMock`(맨 단어)을 **제거**했다. 검토 결과 `Mock\(` 대안이 `MagicMock()` 호출의 끝부분 `Mock(`을 이미 매칭하므로 `MagicMock` 단어 대안은 **잉여**였다(`MagicMock\(` 한정안과 동일 결과 → 더 surgical한 제거 채택). 033의 SKILL 문구 임시 회피는 도구 수정이 근본이므로 별도 원복 불요.

**#2 — 메타-순환 (문서 예시) — 034에서 새로 발견**: #1을 고쳐도 나머지 5개 코드형 대안(`unittest\.mock`/`@patch\b`/`mock\.patch`/`Mock\(`/`@mock\.`)이 **문서화용 인라인 백틱 코드 예시**(`` `m = Mock()` ``)를 라인 단위 스캔에서 그대로 매칭했다. mock 가드를 검증·문서화하는 태스크(034 자신의 TEST-SCENARIO.md, raw 스캔 시 37건)의 TEST 단계가 구조적으로 막히는 **메타-순환**. → `_check_mock_patterns`에 **인라인 백틱 제거(`re.sub(r"`[^`]*`", "", line)`) + 코드펜스 상태추적** 전처리를 추가해 해소. 문서 예시(백틱)는 통과, 코드펜스 내부·백틱 밖 bare 라인의 실제 mock 코드는 계속 검출.

**기각된 대안**: (i) 코드펜스 내부만 검사 → 기존 테스트 3개(bare 라인 mock)를 회귀시킴. (iii) 메타 마커 파일 전체 스킵 → 헌법 §4 무력화 위험. (ii) 인라인 백틱 제거만이 문서 예시 통과 + bare/코드펜스 정탐을 모두 충족. `--force` 우회는 가드 본질 약화로 거부.

**교훈**: mock/credential 등 "금지 패턴 가드"를 검증·문서화하는 태스크는 가드 자신에 걸리는 메타-순환을 구조적으로 안고 있다. 가드는 **실제 코드(코드펜스/bare)와 문서 표기(인라인 백틱)를 구분**해야 한다.

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — 정규식 1대안 제거(#1) + `_check_mock_patterns` 전처리(#2) **수정 완료**, install 재배포로 발효
- op-dev-test-scenario SKILL 문구 — 033 임시 회피분은 도구 근본 수정으로 무해화(원복 불요)

## 관련 페이지

- [[op-dev-test-scenario]]
- [[verification-command-4-standard]]

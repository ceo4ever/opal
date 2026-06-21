---
type: concept
title: brain validate 선택 필드 평탄성 집행 (tags/sources/related flat string[])
tags: [brain-tool, validate, enforce, flatness, frontmatter]
sources: [task:035]
related: [brain-tool, state-tool-mock-guard-skill-false-positive, opal-brain-system]
created: 2026-06-22
updated: 2026-06-22
status: active
---

## 개요

`brain_tool.py`의 `validate_frontmatter`에 선택 필드(`tags`/`sources`/`related`)의 평탄성 검사를 추가한 설계 결정. 중첩 리스트(`[['a','b']]`)·비문자열 요소(`[1,2]`)를 `frontmatter_invalid` violation으로 집행한다. 헌법 Core Stance "Enforce, don't just advise" 적용.

## 결정 배경 (WHY)

034 brain related 정비(`[[state-tool-mock-guard-skill-false-positive]]`) 중 `related: [[a,b]]` 형태의 이중 대괄호 YAML이 PyYAML에 의해 중첩 리스트 `[['a','b']]`로 파싱되는 사각지대가 발견됐다. `validate_frontmatter`는 필수 5필드·type enum·status enum만 검사하고 선택 필드의 값 형식은 검사하지 않았기 때문에 이 결함이 조용히 통과했다.

미검출 시 두 가지 잠복 결함이 발생한다.

- **tags 중첩** → `_score_page`(`brain_tool.py:610`)의 tag 정확일치 실패 → `--tag` 검색 누락
- **related 중첩** → `cmd_lint`(`brain_tool.py:840`)의 `for r in related` 순회에서 `f"[[{r}]]"` 오매칭 → 링크 그래프 순회 누락

"검증 도구가 형식을 집행하지 않으면 조용한 누락이 잠복한다" 는 교훈으로, 도구가 구조적으로 차단해야 한다는 원칙이 적용됐다.

## 결정 내용

**삽입 위치**: `validate_frontmatter`의 status enum 검사 다음, `return issues` 직전 (`brain_tool.py:291-293` 구간).

**통과 조건**: `v is None`(필드 부재) → 즉시 continue. 빈 리스트 `[]` → `all()` 빈 시퀀스 True 자동 통과. 별도 분기 불필요.

**위반 조건**: list가 아님, 또는 요소 중 하나라도 str이 아님 → `"{key} must be a flat list of strings"` detail 추가.

```python
# 선택 필드 평탄성 검사 (035) — tags/sources/related = flat list[str]
for key in OPTIONAL_FRONTMATTER:
    v = fm.get(key)
    if v is None:
        continue
    if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
        issues.append(f"{key} must be a flat list of strings")
```

기존 상수 `OPTIONAL_FRONTMATTER`(`:51`) 재사용 — 신규 상수 0. 시그니처·반환 계약 불변(Surgical).

**RED-first 강제**: 검증 로직 변경은 self-confirming 위험이 높으므로 RED 테스트(opal-test-agent)와 GREEN 구현(opal-task-agent)을 분리 디스패치. 수정 전 6 FAIL 증거 확보 후 GREEN 진입.

## 영향 범위

- `opal/tools/brain-tool/brain_tool.py` — `validate_frontmatter` 9줄 추가 + @header 변경이력
- `opal/tools/brain-tool/tests/test_brain_tool.py` — 평탄성 RED-first 케이스 9개 추가
- 페이지 생성(`cmd_add_page`) 및 brain 전체 검증(`cmd_validate`) 경로에서 자동 집행

## 유사 계열

034의 `state-tool-mock-guard` 수정과 동일한 "도구 집행" 계열이다 — 조용한 누락을 도구가 구조적으로 막는 패턴.

## 관련 페이지

- [[brain-tool]]
- [[state-tool-mock-guard-skill-false-positive]]
- [[opal-brain-system]]

---
type: concept
title: brain-tool search 공백 무시 매칭 — 한국어 복합명사 띄어쓰기 편차 흡수
tags:
- architecture
- brain
- search
- korean
- normalization
sources:
- task:025
related:
- brain-search-on-demand
created: '2026-06-16'
updated: '2026-06-16'
status: active
---
## 개념 요약

brain-tool search가 한국어 복합명사의 띄어쓰기 편차를 흡수하도록, **검색 시점 공백 무시(whitespace-insensitive) 매칭**을 도입했다. 정규화는 검색 순간의 휘발성 사본에만 적용되며, 저장 문서·원본·스니펫 표시용 원문은 변경되지 않는다.

## 결정 배경 (WHY)

한국어 복합명사는 작성자마다 띄어쓰기가 달라(`"자동 취소"` vs `"자동취소"`) brain 검색이 갈리는 문제가 실사용에서 빈번히 발생했다. 캡틴 실증 요구: `"자동 취소"` ≡ `"자동취소"`, `"선정 자동 취소"` ≡ `"선정자동취소"` ≡ `"선정자동 취소"` 가 동일 결과를 내야 했다. 배포본(`~/.opal/tools/brain-tool/`) 실데이터(`"파이프라인"` 계열 29건)로도 검증 완료.

## 결정 내용 (HOW)

### 핵심 설계 원칙

- **휘발성 정규화**: 비교 직전 쿼리와 비교 대상 양쪽의 사본에서 공백을 제거한 뒤 substring 비교. 디스크 `.md` 파일·메모리 원본은 불변(마이그레이션 없음). (`opal/tools/brain-tool/brain_tool.py` `_norm`/`_score_page` — `task:025`)
- **4필드 일괄 정규화**: 제목·파일명·태그·본문 4개 비교 필드에 동일한 정규화를 적용해 비대칭(한 필드만 정규화되는 문제)을 방지한다. (`brain_tool.py` `_score_page` — `task:025`)
- **스니펫은 원문 노출**: 매칭 위치를 정규화 기준으로 찾되, 표시 스니펫은 원문(공백 포함)으로 역매핑하여 출력한다. (`brain_tool.py` `_make_snippet` — `task:025`)
- **비대칭(부분문자열 포함 방향) 보존**: 짧은 쿼리는 긴 복합어 페이지를 포함(넓게), 긴 쿼리는 짧은 페이지를 포함하지 않음(좁게). `in` 방향을 유지해 정밀도 붕괴를 막는다.
- **태그 필터(`--tag`)는 정확 일치 유지**: 태그 가중치(+2) 매칭만 정규화 적용, 필터 동작은 기존과 동일.

### 비채택 옵션

토큰화·stopword·OR 매칭은 정밀도 위험과 실요구 초과(현 규모 54페이지)로 제외. 정규식 `--regex` 옵션은 캡틴 결정으로 범위 외. 인덱싱·임베딩은 현 규모 과설계로 병목 관측 시 별도 스파이크로 분리.

## 영향 범위

- `opal/tools/brain-tool/brain_tool.py` — `_norm` 헬퍼 신설, `_score_page`·`_make_snippet`·`cmd_search` 전환
- `opal/tools/brain-tool/tests/test_brain_tool.py` — 등가/비대칭/스니펫/계약/회귀 테스트 추가 (89 passed)
- `opal/tools/brain-tool/README.md` — §5 공백 무시 매칭 설명 + 변경이력 v1.1 (025)
- `~/.opal/tools/brain-tool/` — install-mac.sh 경유 재배포 완료, 소스↔배포본 diff 무차이

## 관련 페이지

- [[brain-search-on-demand]] — search 후보 목록 반환·on-demand 주입 정책 (태스크 016)
- [[opal-brain-system]] — brain-tool이 속한 brain 시스템 전반

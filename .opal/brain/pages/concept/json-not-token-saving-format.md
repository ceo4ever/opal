---
type: concept
title: JSON은 토큰 절약 포맷이 아니다 — 절약 원천의 정직한 귀속
tags:
- json
- token
- ssot
- measurement
- memory
sources:
- task:078
related:
- memory-tool
- three-layer-memory-architecture
created: '2026-07-29'
updated: '2026-07-29'
status: draft
---
## 개요

JSON으로의 포맷 전환 자체는 토큰 절약 수단이 아니다. 행 단위로 비교하면 JSON은 키를 반복 기술해야 하므로 마크다운 표보다 오히려 무겁다(행당 약 45 B 손해). 실제 절약은 포맷 전환이 아니라 **조회 경로 전환**(필요한 것만 필터링해 보여주기)과 **규범 문서 슬림화**에서 나온다. (근거: task:078 DONE §1, TASK.md §배경 분석 (2))

## 결정 배경 (WHY)

SSOT를 `.opal/MEMORY.md`(HTML 주석 마커 + 마크다운 표)에서 `.opal/MEMORY.json`(스키마 검증 JSON)으로 전환하는 태스크에서, 착수 전 "JSON 전환 = 토큰 절약"이라는 암묵적 기대가 있었다. 하지만 실측은 이를 부정했다. (근거: task:078 TASK.md §배경 분석 (2))

- `state-tool`의 SSOT는 이미 JSON이지만, `state.json`(3,377 B)이 `STATE.md`(1,730 B)보다 크다.
- `.opal/brain/index.md`(27,243 B)를 JSON으로 바꾸면 마크다운 표보다 더 커진다 — brain은 애초 전체 로드가 아니라 `search` 후보→선택 주입 구조라 이 이슈 자체가 발생하지 않는다.

이 근거들 때문에 078 태스크는 `state.json`/`STATE.md`와 `brain/index.md`를 **비범위로 명시 고정**했다(무분별한 "SSOT는 JSON으로" 확산을 차단). (근거: task:078 DONE §6 비범위)

## 결정 내용

078에서 실제로 확인된 절약 원천은 두 가지뿐이다.

| 절약 원천 | 실측 | 비고 |
|-----------|------|------|
| 브리핑 조회를 전체 Read에서 필터 조회로 전환 (`show --brief` vs `show`) | 1,422 B vs 2,781 B = **−49%** | PM 부트스트랩 브리핑 경로 자체를 바꾼 것 — JSON 여부와 무관하게도 얻을 수 있는 절약 |
| 규범 문서 슬림화 (`memory-learning.md`) | 105줄 → **81줄** | 마커·표 서술을 코드 위임 서술로 교체 |

MEMORY 본체 스캐폴딩 제거(`MEMORY.md` → `MEMORY.json`, 3,518 B → 2,938 B = −16.5%)는 마커·표 헤더 등 **포맷 고유의 보일러플레이트 제거** 효과이지, "JSON이 md보다 조밀해서"가 아니다 — 행이 늘어나면 이 이점은 역전된다.

**1순위 정당화는 절약이 아니라 도구 정확성**이다: 마커·표 파싱은 변형(헤더 컬럼 순서, 자유텍스트 상태값 등)에 취약한 계층이었고, 문서 스키마 런타임 검증으로 이 취약 계층 자체를 소멸시킨 것이 이 태스크의 실제 가치다. (근거: task:078 DONE §1)

## 영향 범위

향후 "SSOT를 JSON으로 바꾸면 토큰이 준다"는 제안이 재점화될 때, 이 실측 3종(state.json/STATE.md, brain/index.md, 행당 45B 손해)을 근거로 우선 반박하고 — 절약을 원한다면 포맷 전환이 아니라 **조회 경로**(필터 조회)와 **문서 슬림화**에서 찾도록 유도한다.

## 관련 페이지

- [[memory-tool]] — 이 판단이 적용된 실제 전환 대상 도구

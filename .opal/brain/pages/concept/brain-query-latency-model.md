---
type: concept
title: 브레인 질의 latency 모델 — 병목 위치와 경량화 방향
tags: [brain, latency, architecture, optimization, async]
sources: [task:037]
related: [brain-tool, opal-console, brain-search-on-demand, bootstrap-marker-skip-ladder]
created: 2026-06-23
updated: 2026-08-20
status: active
---

## 개요

브레인 질의의 실제 처리 시간 병목은 **in-agent 멀티턴 LLM 루프**이지, OPAL 프레임워크 로딩이나 brain-tool 검색이 아니다. brain-tool의 키워드 검색 및 랭킹은 결정론적 파이썬 로직으로 0.15초 내 완료된다.

## 결정 배경 (WHY)

- 브레인 질의 콜드 시간 ≈69초, 웜 시간 ≈20초를 측정·분석한 결과, 대부분의 시간이 `claude -p` 서브프로세스 내 멀티턴 에이전트 루프(도구 호출 왕복 N회)에서 소모된다.
- brain-tool의 검색·랭킹(`pages/` 파일 스캔 + TF-IDF 유사 키워드 매칭)은 OPAL 프레임워크가 실행되는 파이썬 프로세스에서 결정론적으로 처리되어 ≈0.15초.
- "질문→검색어 변환"만 1턴 LLM으로 수행하고, 검색 자체는 brain-tool에 위임하면 멀티턴 루프를 "검색 밖+합성 1턴"(≈21초)으로 압축할 수 있다는 PoC가 완료됨.

## 결정 내용 (HOW)

**현재 구조(037 기준)**:
- `claude -p` (in-agent) → 멀티턴 루프: 질문 이해 → brain-tool search → 페이지 fetch → 합성 (≈21~69초)
- 콜드 경로는 opbr 세션 초기화(≈5초) + 위 루프

**최적화 방향 — 폐기 (소유자 판정 2026-08-20)**:
- 당시 권고안은 스킬에 경량 모드를 신설해 멀티턴을 2턴+도구로 압축하는 것이었고 PoC로 콜드 ≈21~26초(기존 69초 대비 ≈3.2배)를 실증했다.
- **그러나 소유자가 이 방향을 폐기했다.** 경량 모드 플래그를 추가하는 접근으로는 해결할 문제가 아니라는 판단이다. 대안 방향은 미정이다.
- **이 문서에 남은 유효한 지식은 병목의 위치(아래 인사이트)이며, 그 대책은 아직 열려 있다.** 경량 모드 재제안 시 이 폐기 기록을 먼저 확인할 것.

**인사이트**: brain-tool 랭킹 알고리즘은 LLM 추론 없이 결정론적 파이썬으로 동작 → 검색 단계를 LLM 루프 밖으로 빼낼수록 latency가 단축된다.

## 영향 범위

- 037 기준 현재 구현: 비동기 잡+폴링으로 fetch 타임아웃 해소됨 (latency 자체는 동일)
- 후속 태스크 예약 없음 — 경량 모드 방향은 폐기되고 대응 메모리도 정리됐다(2026-08-20). 병목 진단만 유효하게 남았다.
- `brain-tool search` 결정론성: `~/.opal/tools/brain-tool/` 파이썬 구현, 외부 LLM 호출 없음

## 관련 페이지

- [[brain-tool]]
- [[opal-console]]
- [[brain-search-on-demand]]
- [[bootstrap-marker-skip-ladder]] — 이 지연 병목 분석을 근거로 "[ASSISTANT] 캡의 목적은 지연 단축이 아니라 tier 격리"임을 명확화한 후속 결정(task:051)

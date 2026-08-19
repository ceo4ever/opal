# 010 후속/폐기 기록 — code-scan PM 우선 무조건화

> 등록일시: 2026-06-11 22:43 KST
> 태스크: 010-260526-opp-code-scan-pm-mandate

## 후속 ① — Phase 2 워커 자체 탐색 강제 (대기)

**내용**: 010 Phase 2 후속 — 워커 자체 탐색 강제(code-scan 우선) 격상.

**사유**: Phase 1은 PM 레이어만 무조건화하여 워커(execute 단계)의 탐색 방식은 여전히 자율에 맡겨진다.
워커가 Glob/Grep 직행 탐색을 그대로 사용하면 PM 규약과 일관성이 무너진다.
Phase 1 운영 후 실제 워커 탐색 패턴 데이터가 쌓이면 Phase 2로 격상 여부를 판단한다.

**상태**: 대기 (운영 데이터 축적 후 판단)

---

## 후속 ② — OPAL 본 프로젝트 @header 커버리지 확충 (대기)

**내용**: 010 후속 — OPAL 본 프로젝트 @header 커버리지 확충. brain analyze 품질의 원료.

**사유**: 현재 OPAL 프로젝트의 @header 커버리지가 약 2파일 수준(016 세션 확인)으로 극히 낮다.
brain `analyze`와 `sync-header`는 code-scan @header 정량 집계에 의존하므로(brain_tool.py:6),
@header 커버리지가 낮으면 brain 지식 품질의 상한이 낮아진다.
016 세션에서 확인된 수준(2파일)을 기점으로 커버리지 확충 태스크를 별도 편성할 것.

**상태**: 대기

---

## 폐기 기록 — 010 v2 폐기: Phase 3 .md @header 표준화

**내용**: 010 v2 폐기 — Phase 3 .md @header 표준화.

**사유**: v1 태스크 정의에 포함된 "Phase 3 — .md 문서 파일 @header 표준화"는 010 v2 재정의 시 폐기.
문서 요약·검색 기능은 brain ingest가 흡수하므로(016 W2 — ingest 트리거 규칙) 별도 .md @header 표준화가
중복이며 불필요하다. F-3 extensions에 `.md` 기본 포함은 brain @header 자산화 목적의 옵션 기본값으로만
유지하되, 전 .md 파일에 @header 강제하는 표준화 작업은 진행하지 않는다.

**상태**: 폐기 기록

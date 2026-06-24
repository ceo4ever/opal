---
type: concept
title: CLOSE 관련 문서 업데이트 — brain ingest 직전 최신화
tags:
- close
- pipeline
- brain-ingest
- document-standard
sources:
- task:042
related: []
created: '2026-06-24'
updated: '2026-06-24'
status: active
---
## 개념 요약

모든 파일럿의 CLOSE 단계에서 brain ingest를 디스패치하기 **직전에** "관련 문서 업데이트" 절차를 수행하도록 흐름을 변경한 설계 결정이다. 태스크 결과로 내용이 달라진 기획·설계 문서를 먼저 최신화한 뒤 brain에 누적함으로써, 누적되는 지식의 신선도와 품질을 보장한다.

## 배경·문제 (WHY)

기존 CLOSE 흐름은 `DONE.md 생성 → op-brain-ingest → 완료 보고`였다 (근거: task:042 PLAN §2.1.2). 이 순서에서는 PROJECT.md 레지스트리에 등재된 관련 문서(ARCHITECTURE.md·기획서 등)가 태스크 결과를 아직 반영하지 못한 상태로 ingest될 수 있어, brain에 옛 내용이 적재되는 품질 저하가 발생했다 (근거: task:042 TASK §배경). "문서를 먼저 최신화한 뒤 그 결과를 ingest한다"는 순서가 ingest 품질의 전제 조건이라는 판단이 결정의 핵심이다.

## 결정 내용 (HOW)

- **삽입 위치**: DONE.md 생성 직후, op-brain-ingest 디스패치 직전. 이 순서 계약이 태스크의 핵심 AC다 (근거: task:042 PLAN H-2).
- **판별 기준**: `docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 **양쪽 종합**하여 갱신 대상 문서를 식별한다.
- **수행·비차단 설계**: 갱신 대상이 있으면 PM이 직접 수정하거나 적합한 워커를 디스패치한다. 대상이 없으면 자연 스킵(no-op)이며 CLOSE를 중단시키지 않는다 — brain ingest의 비차단 원칙과 동일한 결.
- **단방향 원칙 유지**: 이 절차는 관련 문서를 최신화할 뿐, brain → 코드·문서 역수정 금지 원칙과 충돌하지 않는다. 문서 최신화는 태스크 산출의 정상 연장이다.

## 영향·관계

- 8개 파일럿 SKILL.md의 CLOSE 단계에 적용됐다: opd·opp·opdd·opds·opdw·opgc·opsdd·opwt (근거: task:042 DONE 변경 파일 표).
- 구조에 따라 3패턴으로 분기 처리됐다 — A(numbered-list, brain=항목2, 6개) / B(numbered-list, brain=항목4, opsdd) / C(무번호 서브섹션, opgc). 패턴 A·B는 후속 항목 번호 +1 재정렬이 동반됐고, opgc는 무번호 단락이라 재정렬 비해당.
- 설계 제안서 `docs/proposals/opal-brain-design.md` §8.2의 CLOSE 흐름 기술이 4항목으로 갱신됐다.
- [[op-brain-ingest]] — 본 절차 직후에 디스패치되는 CLOSE 경량 ingest 워커
- [[opal-brain-design-proposal]] — CLOSE 흐름(§8.2)을 정의하는 brain 설계 제안서

## 근거 출처

task:042 (CLOSE 단계 관련 문서 업데이트 스텝 추가). PLAN §2.1.2 / H-2, TASK §배경, DONE 변경 파일 표.

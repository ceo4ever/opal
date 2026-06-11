---
type: concept
title: opwt v4 산출물 체계 재설계 (PRD 8섹션 + interview 통합)
tags:
- opwt
- planning
- output
- framework
- task
sources:
- task:008
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

`opal-pilot-write-tech`(opwt) 스킬을 v3.4→v4.0으로 개편했다. PRD 6섹션→8섹션, WBS 제거, 기능 시나리오 다이어그램·화면 흐름도 신설, interview 스킬 Round 1/2/3 통합, 산출물 저장 default 7폴더 트리 확정이 핵심이다.

## 배경·문제 (WHY)

`app-planning-presentation` 교육 자료의 산출물 체계와 opwt SSOT 간 괴리가 있었다. PRD 섹션 부족, 시나리오·화면 흐름도 정의 모호, interview 단계 분리 불명확이 문제였다.

## 결정 내용 (HOW)

- PRD 8섹션 확정(서비스 기획서 + 요구사항 명세서 통합 흡수).
- WBS(PMO 그룹) 완전 제거; 선택 산출물 4→5종.
- TASK 단계: interview 스킬 Round 1/2/3 통합, 질문 Q6 "산출물 저장 경로" 추가.
- default 저장 트리: `100.기획/` 하위 7폴더(110~170, 10 간격 prefix).
- Mermaid 시각화 표준 §11 신규 절 — 필수 3종(IA/시나리오/화면흐름도) + 권장 4종.

## 영향·관계

- 변경 파일: `opal-pilot-write-tech/SKILL.md`, `references/network-guide.md`, `references/consistency-rules.md`.
- [[opal-architecture]] opwt 스킬 산출물 체계 변경.

## 근거 출처

`sources: task:008` — DONE.md §1~§5 참조.

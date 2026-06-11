---
type: concept
title: opal-project-init — 프로젝트 환경 초기화
tags:
- skill
- init
- project
- docs
sources:
- skill:opal-project-init
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

프로젝트 환경 초기화 및 최신화 스킬(opi). 프로젝트를 분석하고 사용자와 대화하여 docs/(PROJECT.md, ARCHITECTURE.md 등)와 .opal/(AGENT.md, MEMORY.md)를 직접 작성한다.

## 배경·문제 (WHY)

모든 OPAL 스킬(opd/opds/opwt 등)은 프로젝트 컨텍스트 문서를 전제한다. 플레이스홀더 치환이 아닌 에이전트가 코드를 분석한 후 직접 작성하는 방식으로 품질을 보장한다.

## 결정 내용 (HOW)

코드 분석 → 사용자 인터뷰 → 문서 직접 작성 → 사용자 검토 → 피드백 반영 사이클. docs/ 수정 전 백업 프로토콜 강제. 기존 문서가 있으면 코드와 비교하여 최신화 제안.

## 영향·관계

oppd(프로젝트 라이프사이클)의 선행 조건. opi가 생성한 docs/PROJECT.md는 모든 파일럿 스킬의 컨텍스트 로딩 기준이 된다.

## 관련

- [[opal-project-definition]] — opi가 생성하는 docs/PROJECT.md의 기준이 되는 프레임워크 정의
- [[opal-architecture]] — opi가 생성·최신화하는 ARCHITECTURE.md의 참조 구조
- [[skill-opal-pilot-project-dev]] — opi 완료 후 진입하는 프로젝트 개발 라이프사이클 오케스트레이터

## 근거 출처

file_path: `opal/skills/opal-project-init/SKILL.md`

---
type: concept
title: OPAL 부트스트랩 2-tier 모델 (비서/PM 분리)
tags:
- bootstrap
- 2tier
- architecture
- pm-gate
- assistant-tier
sources:
- task:049
related:
- opal-bootstrap-skip-gate
- bootstrapper-marker-ssot-single-point
- opal-adapter-platform-isolation
- bootstrap-marker-skip-ladder
created: '2026-06-30'
updated: '2026-07-02'
status: active
---

## 개요

OPAL 부트스트랩은 두 단계(tier)로 분리된다. 비서(Lite) tier는 전역 마커를 통해 모든 세션에서 항상 로드되고, PM(Full) tier는 현재 작업 디렉토리에 프로젝트 초기화 신호가 존재하는 경우에만 승격 로드된다. 이 구조로 "프레임워크 사용자레벨 설치 + PM 부트스트랩은 프로젝트레벨 opt-in"이 달성된다 (task:049 DONE.md §결과 요약).

## 결정 배경 (WHY)

기존 부트스트랩은 모든 세션에서 헌법·정체성·하네스·PM·프로젝트 컨텍스트를 한꺼번에 로드했다. 이 설계에는 두 가지 모순이 내재해 있었다.

첫째, "전역 비서 유지" 요구와 "비-opi 폴더에서 PM 미로드" 요구가 단일 tier 구조에서 충돌했다. 전역 마커가 비서를 활성화하면서 동시에 PM도 로드하는 것이 불가피했기 때문이다 (task:049 PLAN §1.1, M-비서/PM 모순).

둘째, OPAL 헌법(PRINCIPLES)의 "플랫폼 분기는 어댑터에만, 로직은 AGENT.md" 원칙상 tier 분기 로직을 부트스트래퍼나 install 스크립트에 배치할 수 없었다. 로직의 위치가 단일 파일로 제한되면서 2-tier 구조를 AGENT.md 한 파일에 집중시키는 방식이 선택되었다 (task:049 PLAN §3.1.2, `opal/core/PRINCIPLES.md` Core Stance).

## 결정 내용

부트스트랩 Eager 단계는 Phase A(비서 tier)와 Phase B(PM tier)로 분리된다.

Phase A는 모든 세션에서 항상 실행된다. 스킵 게이트 확인, 정체성 로드, 헌법 로드, 보고 형식·도구 인지맵·커맨드 레지스트리 해석 능력 활성화가 여기에 포함된다. 비서 tier는 `//` 레지스트리 해석 능력을 보유하므로, 비-opi 폴더에서도 `//opi` 커맨드를 발동하여 프로젝트 OPAL화 진입점을 보존한다 (task:049 PLAN §3.1.2, D-1 §Lazy 트리거 테이블).

Phase B는 현재 디렉토리에 프로젝트 초기화 신호가 존재하는 경우에만 실행된다. 하네스, PM 레퍼런스, 프로젝트 에이전트 정의, 메모리 브리핑이 여기서 로드된다. 프로젝트 초기화 신호가 없는 경우 Phase B 전체가 스킵된다.

2-tier 로직은 AGENT.md 단일 파일에 집중하고, 부트스트래퍼(진입점 어댑터) 4종은 AGENT.md를 가리키는 진입 역할만 수행한다. 마커 콘텐츠 자체는 변경이 거의 없으며, AGENT.md가 2-phase로 바뀐 결과로 전역 마커가 자동으로 비서 tier부터 시작하게 된다 (task:049 PLAN §3.3.2).

## 영향 범위

- 부트스트랩 진입점 4종(`opal/bootstrapper/`) — 의미 정합·변경이력 행 추가(진입점 역할은 불변)
- 에이전트 정의(`opal/core/AGENT.md`) — Phase A/B 구분 + Phase B 게이트 명문화
- opi 스킬(`opal/skills/opal-project-init/`) — Codex `AGENTS.md` 템플릿 신규 + apply.js 배열 1행 추가
- 시스템 구조 문서(`docs/ARCHITECTURE.md`) — 2-tier 진입 모델 절 추가

## 관련 페이지

- [[opal-bootstrap-skip-gate]]
- [[bootstrapper-marker-ssot-single-point]]
- [[opal-pm-promotion-gate]]
- [[bootstrap-marker-skip-ladder]] — 헤드리스(`claude -p`) 호출을 위해 이 2-tier 모델에 `[ASSISTANT]` 중간 단을 추가한 후속 결정(task:051)

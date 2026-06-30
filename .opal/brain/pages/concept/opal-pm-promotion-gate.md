---
type: concept
title: PM 승격 게이트 — 프로젝트 초기화 신호 존재 조건
tags:
- bootstrap
- pm-gate
- opi
- 2tier
- project-level
sources:
- task:049
related:
- opal-bootstrap-2tier-model
- bootstrapper-marker-ssot-single-point
- opal-bootstrap-skip-gate
created: '2026-06-30'
updated: '2026-06-30'
status: active
---

## 개요

OPAL 부트스트랩의 PM(Full) tier 승격 여부는 현재 작업 디렉토리에 프로젝트 에이전트 정의 파일이 존재하는지로 판정된다. 이 단일 파일 존재 신호가 "opi로 초기화된 프로젝트"임을 나타내는 게이트로 기능한다 (task:049 DONE.md 핵심 설계 결정 #2).

## 결정 배경 (WHY)

PM 승격 게이트에 사용할 신호를 선택할 때, 새 신호를 도입하는 대신 기존에 이미 같은 의미로 사용되던 파일 존재 여부를 재활용하는 방향이 선택되었다.

AGENT.md의 역할전환 표는 이미 해당 파일 존재 시 PM 모드, 부재 시 비서 모드로 동작을 구분하고 있었다. 부트스트랩 완료 보고의 PM모드 칼럼도 동일 신호를 사용했다. 즉 부트스트랩 Eager 단계의 heavy 로드(하네스·PM·프로젝트 컨텍스트)를 같은 신호 앞으로 끌어올리는 것만으로 정합 리스크 없이 2-tier 게이팅이 완성되었다 (task:049 PLAN §2.1.2, `opal/core/AGENT.md:108-111`).

새 게이트 값 도입이나 `setting.json` 스키마 변경 없이 기존 신호를 재활용함으로써 PRINCIPLES §2 "현재 요구사항만 해결, 투기적 추상화 금지" 원칙도 준수된다.

## 결정 내용

게이트 조건은 단일 파일 존재 여부이다. 해당 파일이 존재하면 Phase B(PM tier) 전체가 실행되고, 부재하면 Phase B 전체가 스킵된다.

이 설계로 "프로젝트레벨 opt-in" 의미가 달성된다. opi(opal-project-init 스킬)로 프로젝트를 초기화하면 해당 파일이 생성되고, 이후 그 디렉토리에서 열리는 모든 세션이 자동으로 PM tier로 승격된다. 반대로 opi를 실행하지 않은 일반 폴더는 비서 tier만 활성화된다.

`//` 커맨드 레지스트리 해석 능력은 비서 tier(Phase A)에 포함되므로, 비-opi 폴더에서도 `//opi` 발동이 가능하다. 이 불변식 덕분에 어느 폴더에서나 OPAL화 진입점이 유지된다 (task:049 DONE.md 핵심 설계 결정 #6, PLAN §3.1.2).

install 스크립트와 부트스트래퍼 마커는 이 게이트 로직을 담지 않는다. 2-tier 분기 로직 전체는 AGENT.md 한 파일에만 위치하여 어댑터 역할과 로직 역할이 분리된다 (task:049 PLAN §3.1.2, task:049 DONE.md 핵심 설계 결정 #3).

## 영향 범위

- `opal/core/AGENT.md` Phase B 게이트 명문화 — "현재 cwd에 프로젝트 초기화 신호 존재 시에만"
- 역할전환 표·완료 보고 PM모드 칼럼 — 동일 신호, 정합 유지
- opi 스킬(`opal/skills/opal-project-init/`) — 프로젝트 초기화 시 게이트 신호 파일 생성

## 관련 페이지

- [[opal-bootstrap-2tier-model]]
- [[opal-bootstrap-skip-gate]]
- [[bootstrapper-marker-ssot-single-point]]

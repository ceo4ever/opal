---
type: concept
title: Console 브레인 질의 인증 — 종량제 API 금지, 소유자 구독 사용
tags:
- console
- brain
- auth
- cost
- task-036
sources:
- task:036
- task:094
related:
- brain-tool
created: '2026-08-20'
updated: '2026-08-20'
status: draft
---
## 결정

OPAL Console의 브레인 질의는 **종량제 API가 아니라 소유자의 Claude 구독**을 사용한다. 백엔드가 로컬에 설치된 대화형 CLI를 비대화형 모드로 호출해 응답을 받는 구조다.

**금지 사항** — 아래는 절대 사용하지 않는다.

- 공급자 SDK 직접 호출
- API 키 환경변수 주입
- 안전 모드 우회·최소 실행 플래그

## 왜 이렇게 결정했는가

Console은 소유자 개인 머신에서 도는 읽기 전용 관리 대시보드다. 여기에 종량제 과금 경로를 열면 **웹 화면을 열어두기만 해도 비용이 발생**할 수 있고, 키가 로컬 설정 파일에 상주해야 한다. 이미 보유한 구독을 쓰면 두 문제가 동시에 사라진다.

## 어떻게 집행되는가

집행은 산문 규칙이 아니라 **코드 주석의 금지 선언 + 실제 호출 경로 부재**로 이뤄진다.

- 어댑터 상단에 금지 항목을 `[MUST]` 주석으로 명시한다 (`dashboard/backend/adapters/opbr_adapter.py:23`)
- 공급자 SDK import 0건 · API 키 참조는 위 금지 주석 1건뿐 (2026-08-20 실측)
- 질의는 세션 어댑터를 통해 로컬 CLI 비대화형 호출로 처리한다 (`dashboard/backend/adapters/brain_session.py:39`)

## 관련

- Console 브레인 화면은 휘발성 단일 세션으로 동작하며 프라임 풀로 콜드 지연을 완화한다 (태스크 063)
- 이 원칙은 태스크 036에서 Console 6번째 메뉴를 추가할 때 확정됐다

## 관련 페이지

- [[brain-tool]]

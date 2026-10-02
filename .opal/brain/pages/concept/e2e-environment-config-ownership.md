---
type: concept
title: E2E 실행 환경은 프로젝트 설정 파일 하나가 선언한다
tags:
- e2e
- config
- task
sources:
- task:159
- task:179
related: [opal-e2e, test-tool, e2e-journey-library, e2e-harness-three-responsibility-split]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

프로젝트마다 다른 E2E 실행 환경(서비스 기동·상태 확인, 표면, 비밀값 이름, 데이터·외부 연동 정책)을 프로젝트 설정 파일(`.opal/e2e/environment.json`) 하나로 선언·검증하도록 한 결정이다. 검증·해석은 테스트 도구의 환경 모듈 한 곳이 맡는다(`tasks/159-260926-opds-E2E-테스트환경-설정체계/DONE.md:5`, `opal/tools/test-tool/lib/e2e/environment.py`).

## 핵심 결정

- 환경 다루기 명령을 셋으로 나눴다. 읽기 전용 검토(후보 보고), 구조 검증(위반 코드 11종, 비밀값 원문은 거부), 표면별 실제 준비 판정(기동·상태 확인·실행기 확인, 데스크톱 실행기 부재를 성공으로 가장하지 않음)이다(`tasks/159-260926-opds-E2E-테스트환경-설정체계/DONE.md:7-10`).
- 실행은 대상 트리의 설정으로 서비스를 의존 순서대로 한 번씩 띄우고, 설정 부재·무효·표면 선택 실패는 서비스를 띄우지 않고 차단으로 끝낸다. 테스트 도구 코드의 대시보드 고정 기동 경로는 없앴다(`tasks/159-260926-opds-E2E-테스트환경-설정체계/DONE.md:11-13`).
- 환경 설정 모드는 검토 → (후보 부족 시) 프로젝트 정의 문서 기반 추정 → 인터뷰 확정 → 검증 후 사용자 확인 → 확인 뒤에만 기록 → 준비 판정 보고 순서다(`tasks/159-260926-opds-E2E-테스트환경-설정체계/DONE.md:14-20`).
- 실행 판정과 종료 코드의 소유자는 계속 테스트 도구다(`tasks/159-260926-opds-E2E-테스트환경-설정체계/DONE.md:21`).

## 세션 부트스트랩 훅 (태스크 179)

환경 파일에 선택 키(`session_bootstrap`)를 두어, 서비스가 준비된 뒤 프로젝트가 선언한 명령을 1회 실행해 인증 헤더와 브라우저 진입 fragment를 받는다. 이로써 프레임워크 도구는 특정 프로젝트의 인증 방식을 직접 알지 않는다. 실패는 기동 실패와 같은 인프라 오류로 끝나며, 인증 값은 증적에서 마스킹된다. 키가 없는 기존 환경은 동작이 변하지 않는다. (근거: task:179 PLAN§D-20, `opal/tools/test-tool/lib/e2e/environment.py`)

## 관련 페이지

- [[opal-e2e]] · [[test-tool]]
- [[e2e-journey-library]] · [[e2e-harness-three-responsibility-split]]

---
type: concept
title: 테스트 소스 경로와 배포본 경로의 계층 차이가 실사용 불가를 덮는다
tags:
- testing
- deployment
- layered-verification
- task-105
sources:
- task:105
related:
- silent-success-defect-class
created: '2026-09-03'
updated: '2026-09-03'
status: draft
---
## 개요

단위 테스트가 소스 경로를 호출하고 스킬 문서가 배포본을 호출하면, 두 경로의 계층 차이 때문에 자동 검증 전건 Pass가 실사용 불가 상태를 덮을 수 있다. 자동 검증 39건과 컨벤션 진단 Critical/High 0건, 회귀 41/41이 모두 통과한 상태에서도, 실제 배포본을 그대로 실행하는 시나리오 1건만이 결함을 검출했다.

## 결정 배경 (WHY)

(근거: task:105 DONE.md §3.9) 신규 로직(`scan-risk` 서브명령)은 소스 저장소(`opal/tools/skill-registry/skill-registry.js`)에는 반영됐으나 배포본(`~/.opal/tools/skill-registry/skill-registry.js`)에는 반영되지 않았다. 단위 테스트(`test-scan-risk.js`) 16건은 전부 소스 경로를 직접 호출해 통과했고, 컨벤션 자동 진단도 소스 diff만 본다. 그런데 스킬 절차 문서(`SKILL.md`)가 실제 사용자 실행 시점에 부르는 것은 배포본 경로다. 배포본에 `scan-risk`가 없어 `Unknown command`로 종료 코드 1이 나며 개정된 절차가 4단에서 멈춘다.

이 결함은 40건의 시나리오 중 L3 [SUPERVISOR] 등급 1건 — 절차 전체를 실제 배포본 경로로 완주 실행하는 시나리오 — 만이 검출했다. 나머지 39건은 소스 경로 또는 절차 일부만 검증해 이 계층 차이를 넘어서지 못했다.

## 결정 내용

- **일반 원칙**: 도구를 수정하는 태스크에서 "테스트가 통과했다"는 소스 경로 기준 사실이지, 최종 사용자가 실제로 호출하는 경로(배포본·패키지·빌드 산출물 등) 기준 사실이 아닐 수 있다. 두 경로가 분리된 프로젝트(예: 소스 저장소 → `install` 스크립트로 배포되는 OPAL 구조)에서는 검증 계층에 배포본 실행 시나리오를 반드시 포함해야 한다.
- **검출 가능한 검증 등급**: 소스 단위 테스트·정적 컨벤션 진단은 이 계층 차이를 원리적으로 검출할 수 없다. 배포본을 실제로 실행하는 L3급 시나리오(사람 또는 격리 환경에서 실제 절차 완주)만이 검출 가능하다.
- **재배포는 별도 관문**: 배포본 갱신(`./scripts/install-mac.sh` 재실행)은 소유자 권한이며, 소스 수정과 재배포 사이에는 항상 이 간극이 존재할 수 있다는 것을 전제해야 한다.

## 영향 범위

- `opal/tools/skill-registry/skill-registry.js` (소스) ↔ `~/.opal/tools/skill-registry/skill-registry.js` (배포본) — 이 태스크에서 간극이 실측됨
- 시나리오 설계: 배포본 경로를 직접 실행하는 L3 시나리오를 신규 도구 도입 시 필수 포함 항목으로 고려

## 관련 페이지

- [[silent-success-defect-class]]

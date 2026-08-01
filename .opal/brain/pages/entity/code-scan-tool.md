---
type: entity
title: code-scan
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: opal/tools/code-scan/code-scan.js
header_synced: <YYYY-MM-DD>
tags:
- tool
- util
- code-scan
sources:
- task:077
- code:opal/tools/code-scan/
related:
- brain-code-scan-role-division
- code-header-dual-source-inheritance
- exports-generation-tool-verification-division
created: '2026-08-01'
updated: '2026-08-01'
status: draft
---
## 개요

소스 코드 안에 흩어진 설계 메타데이터(도메인·레이어·의존관계·노출 인터페이스)를 한곳에서 조회하는 도구였다가, 이번 작업으로 그 메타데이터를 실제로 채워 넣는 작성층까지 갖추게 됐다 — 조회 전용에서 조회+작성 도구로 성격이 바뀌었다(근거: task:077 DONE.md §1).

## 책임 (WHAT)

- 헤더 조회: 전체 스캔·도메인별/레이어별 조회·키워드 검색·노출 인터페이스 검색·요약·의존관계 추적·미보유 목록까지 여덟 가지 조회 동작을 제공한다(`opal/tools/code-scan/code-scan.js:1-24`).
- 헤더 발견·초안 생성: 아직 헤더가 없는 영역을 찾아내고 처음 채울 골격을 만들어 준다(근거: task:077 PLAN F-003·F-004).
- 기록 위치 판정: 파일 하나를 주면 그 파일의 헤더를 인라인과 외부 지도 중 어디에 남겨야 하는지 알려준다(`opal/tools/code-scan/code-scan.js:755` `decideTarget`).
- 커버리지·위반 검증: 연결 끊김·미커버·충돌·초안 상태·존재하지 않는 노출 인터페이스 다섯 가지 위반을 검사하고, 변경된 파일만 골라 검사하는 모드를 지원한다(`opal/tools/code-scan/code-scan.js:1448` `cmdValidate`).
- 여러 소속 영역에 걸쳐 이름이 같은 항목을 한 번에 조회하는 기능도 제공한다(근거: task:077 PLAN F-008).

## 설계 배경 (WHY)

기존 여덟 가지 조회 동작은 하나도 건드리지 않고 그 위에 작성 기능을 얹었다 — 외부 지도가 없는 프로젝트에서는 이전과 완전히 동일한 결과가 나와야 한다는 제약을 지키기 위해서다(근거: task:077 TASK.md 제약②, PLAN§3.2.2(H)). 문법 해석기 없이 판단하도록 만든 것은, 새 의존성을 들이지 않는다는 이 도구군 전체의 원칙을 지키기 위함이다(추론: 코드패턴).

## 관계 (HOW)

- 세션 중 파일이 저장될 때마다 헤더 기록이 누락됐는지 조용히 확인해 주는 후킹이 함께 배치된다. 이 후킹은 [[code-map-write-location-decision]]에서 정한 판정 로직을 그대로 재사용한다(`opal/tools/code-scan/code-map-hook.js`).
- 프로젝트 안 다른 도구들과 동일한 공통 실행 규약(래퍼 진입점)을 이번에 새로 갖췄다(`opal/tools/code-scan/run.sh`).
- [[brain-code-scan-role-division]] — opal-brain과의 역할 경계.
- [[code-header-dual-source-inheritance]] — 조회 시 헤더를 해석하는 규칙.
- [[exports-generation-tool-verification-division]] — 노출 인터페이스 필드의 생성·검증 분업.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `run.sh` | `opal/tools/code-scan/run.sh` | 공통 래퍼 진입점 |
| `code-map-hook.js` | `opal/tools/code-scan/code-map-hook.js` | 저장 시점 기록 누락 감지 후킹 |
| `loadCodeMap` | `opal/tools/code-scan/code-scan.js:506` | 외부 지도 로더 |
| `mirrorPathForDir` | `opal/tools/code-scan/code-scan.js:573` | 소스 디렉토리 → 지도 경로 사상 |
| `resolveHeader` | `opal/tools/code-scan/code-scan.js:688` | 5단 상속 해석기 |
| `decideTarget` | `opal/tools/code-scan/code-scan.js:755` | 기록 위치 4단 판정 |
| `cmdValidate` | `opal/tools/code-scan/code-scan.js:1448` | 위반 5종 + 커버리지 검증 |

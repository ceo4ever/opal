---
type: concept
title: Read 기반 설정파일 게이트 패턴
tags:
- bootstrap
- permission
- gate
- read-pattern
- session-toggle
sources:
- task:043
related:
- opal-bootstrap-skip-gate
- opal-adapter-platform-isolation
created: '2026-06-24'
updated: '2026-06-24'
status: active
---
## 개요

매 세션 실행이 필요한 게이트(조건 분기)를 설계할 때, Bash 명령 대신 **이미 권한이 등록된 Read 경로의 설정파일**로 구현하면 새 권한 표면 없이 무프롬프트 게이트를 달성할 수 있다. task:043에서 `echo $OPAL_BOOTSTRAP`(Bash) 게이트를 `~/.opal/setting.json` Read 게이트로 전환하며 도출된 설계 원칙이다.

## 결정 배경 (WHY)

Claude Code에서 `echo $VAR`(셸 변수 확장, simple_expansion)는 read-only 허용 규칙으로 자동 승인되지 않아 매 세션 권한 프롬프트를 유발한다 (근거: task:043 PLAN §1.2). 반면 `Read(~/.opal/**)` 경로는 install이 이미 Claude Code 권한에 글롭으로 등록하므로, 동일 경로 아래에 설정파일을 두면 **추가 권한 등록 없이** 무프롬프트 동작을 보장한다 (근거: task:043 PLAN §1.2 귀결).

## 결정 내용

- **원칙**: Bash 권한 프롬프트를 피해야 하는 매 세션 게이트는 기존에 부여된 Read 경로의 설정파일로 설계한다.
- **구현 패턴**: `Read(<기존_무프롬프트_경로>/setting.json)` → JSON 파싱 → 필드 값으로 분기.
- **fail-safe 필수**: 파일 부재·필드 부재·파싱 실패 시 게이트를 무시하고 정상 동작으로 수렴해야 한다. 게이트 오동작이 기능 누락이 아닌 기본 동작으로 안전하게 폴백되도록 설계한다.
- **create-if-absent 배포**: 설정파일은 존재하지 않을 때만 기본값으로 생성한다(멱등). 재설치 후에도 사용자 편집값이 보존된다 (근거: task:043 PLAN §3.1.2).
- **소스 분리**: 배포 소스(`*.default.json`)와 배포본(실제 경로의 `*.json`)을 명명으로 구분한다 — 소스는 기본값만 보유, 사용자 토글은 배포본에만 반영된다.

## 영향 범위

- 최초 적용 사례: [[opal-bootstrap-skip-gate]] — `~/.opal/setting.json` `bootstrap` 필드로 전체 부트스트랩 스킵 여부 결정.
- 적용 가능 영역: 매 세션 실행이 필요하면서도 Bash 권한이 없거나 최소화해야 하는 모든 게이트 (예: 향후 feature flag, 디버그 모드 토글 등).
- 향후 설정 키 확장 거점: `~/.opal/setting.json` 객체에 키를 누적하여 여러 게이트를 단일 파일로 관리할 수 있다.

## 관련 페이지

- [[opal-bootstrap-skip-gate]]
- [[opal-adapter-platform-isolation]]

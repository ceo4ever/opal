---
type: concept
title: opal-pilot-gc — GC 진단 오케스트레이터
tags:
- skill
- pilot
- gc
- security
- convention
sources:
- skill:opal-pilot-gc
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

경량 Pilot — 코드 컨벤션·보안 진단 오케스트레이터. 커밋 전 보안·컨벤션 진단을 4단계 파이프라인(SCAN → CHECK → REPORT → CLOSE)으로 수행하며 소스 파일을 직접 수정하지 않는다.

## 배경·문제 (WHY)

커밋 전 보안/컨벤션 문제를 사전에 발견할 필요가 있다. 진단 전담(수정 없음) 원칙으로 CLOSE 단계에서 opds 체인 안내를 통해 수정을 이관한다.

## 결정 내용 (HOW)

--security/--convention/--scope 플래그로 범위 선택. CHECK 단계에서 opal-security-checker와 opal-convention-checker를 병렬 디스패치. GC-SECURITY-{ts}.md 자기완결 보고서 산출. 소스 파일 수정 절대 금지.

## 영향·관계

opal-security-checker, opal-convention-checker 워커 에이전트에 의존. 수정 필요 시 opds 체인으로 이관한다.

## 관련

- [[opal-security-model]] — CHECK 단계에서 opal-security-checker가 비교 기준으로 사용하는 보안 baseline
- [[opal-conventions]] — CHECK 단계에서 opal-convention-checker가 참조하는 컨벤션 규칙
- [[opal-project-definition]] — SCAN 단계 영역 매칭 및 전문 에이전트 선정의 기준

## 근거 출처

file_path: `opal/skills/opal-pilot-gc/SKILL.md`

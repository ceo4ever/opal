---
type: concept
title: op-spec-validator — SDD 명세 검증 워커 스킬
tags:
- sdd
- validator
- skill
sources:
- skill:op-spec-validator
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

PRD/TRD 문서를 읽고 체크리스트 기반으로 명세 완성도를 판정하는 SDD 명세 검증 워커 스킬. 사용자 직접 호출 불가.

## 역할·호출 시점·핵심 규칙

- **역할**: PRD/TRD/ALL 검증; 항목별 {item, result, reason, suggestion} 구조화 판정 결과 반환
- **호출 시점**: 오케스트레이터(oppd 1-1b 등)가 경로로 직접 로드하여 디스패치; 사용자 직접 호출 불가(alias/triggers 없음)
- **핵심 규칙**: 서브에이전트 생성 없음; 필수 입력 PRD 경로·TRD 경로·검증 대상(PRD/TRD/ALL)

## 파일 참조

`file_path: opal/skills/op-spec-validator/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]] — 이 워커 스킬을 oppd 파이프라인 내에서 디스패치하는 SDD 오케스트레이터
- [[op-sdd-spec]] — 이 스킬이 검증 대상으로 삼는 SPEC.md를 생성하는 단계 스킬

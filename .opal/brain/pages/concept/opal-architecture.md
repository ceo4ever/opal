---
type: concept
title: OPAL 시스템 아키텍처
tags:
- architecture
- framework
- layer
- deploy
sources:
- doc:docs/ARCHITECTURE.md
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL은 Global Layer(`~/.opal/` — 모든 프로젝트 공유 프레임워크 자산)와 Project Layer(`{프로젝트}/` — 프로젝트별 컨텍스트)의 2-레이어 아키텍처로 동작한다.

## 핵심 구조

- AI 플랫폼(Claude/Cursor/Gemini)이 부트스트래퍼를 통해 OPAL 에이전트를 활성화한다.
- 오케스트레이터(`opal-pilot-*`)가 하네스(Guards/Gates/State)를 준수하며 서브에이전트 10개에 작업을 디스패치한다.
- 스킬은 `SKILL.md + references/ + personas/` 3-파일 구조; 에이전트는 `AGENT.md` 단일 파일이다.
- 배포는 `install-mac.sh`가 소스(`opal/`)에서 `~/.opal/`로 통합 배포하고, 에이전트 어댑터는 플랫폼별 디렉토리(`~/.claude/agents/` 등)에 별도 생성된다.

## 적용 범위

전체 OPAL 프레임워크(스킬 30개+, 에이전트 11개, 도구, MCP 설정, 배포 채널).

## 참조

`file_path: docs/ARCHITECTURE.md`

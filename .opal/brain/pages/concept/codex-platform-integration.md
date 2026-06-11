---
type: concept
title: Codex CLI OPAL 4번째 플랫폼 통합
tags:
- codex
- platform
- bootstrap
- mcp
- task
sources:
- task:009
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OpenAI Codex CLI를 OPAL의 4번째 통합 플랫폼(Claude Code·Cursor·Antigravity Gemini에 이어)으로 편입했다. 부트스트래퍼·sub-agent 어댑터·MCP 등록·모델 매핑 4축으로 통합하고, `install-mac.sh` 한 곳에 codex 분기를 격리하여 linux.sh가 위임으로 자동 상속하는 구조다.

## 배경·문제 (WHY)

Codex CLI 출시로 플랫폼 지원 범위 확장 필요. 프로젝트 자동 삽입은 글로벌이 항상 먼저 로드되므로 스킵(Claude/Cursor 패턴 동일).

## 결정 내용 (HOW)

- 글로벌 진입점: `~/.codex/AGENTS.md` + OPAL 마커(idempotent 삽입).
- Sub-agent: `~/.codex/agents/<name>.toml` — 13개 어댑터 생성.
- MCP: `codex mcp add` CLI 등록.
- 모델 매핑: light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max.
- `install-mac.sh`에 `install_codex_agents()` 신설, codex 분기 격리.

## 영향·관계

- 신규 파일: `opal/bootstrapper/codex-bootstrap.md`.
- 수정: `opal/core/AGENT.md`, `opal/core/references/opal-model-mapping.md`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`.
- [[opal-architecture]] 플랫폼 독립성 구조에 Codex 추가.

## 근거 출처

`sources: task:009` — DONE.md §1~§2 참조.

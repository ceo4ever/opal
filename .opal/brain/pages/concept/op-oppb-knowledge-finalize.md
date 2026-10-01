---
type: concept
title: op-oppb-knowledge-finalize — OPPB 프로젝트 지식 1회 반영 단계 스킬
tags:
- oppb
- knowledge
- skill
sources:
- skill:op-oppb-knowledge-finalize
related: [opal-pilot-project-build, op-oppb-project-slice, worktree-close-brain-write-contract, op-brain-ingest]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

OPPB 프로젝트 전체에서 모인 지식 후보 중 실패·폐기분을 걸러 내고, 메모리 도구와 brain 도구를 프로젝트 단위로 정확히 한 번 호출해 허브의 메모리·brain에 반영하는 P5 단계 스킬이다(`opal/skills/op-oppb-knowledge-finalize/SKILL.md:3-6`).

## 현재 계약

- OPPB에서 메모리와 brain은 이 단계 전까지 읽기 전용이다. 미니 태스크는 결과에 후보만 남기고, 이 스킬이 유일한 쓰기 지점이다(`opal/skills/op-oppb-knowledge-finalize/SKILL.md:16-19`).
- 쓰기 대상은 허브이며 프로젝트 작업본의 brain·메모리는 끝까지 바뀌지 않아야 한다. 허브 경로는 인자로만 받고 추론하지 않는다(`opal/skills/op-oppb-knowledge-finalize/SKILL.md:21-23`, `:35`).
- 실행 전 게이트로 이미 반영됨(멱등), 허브 merge 관측, 선행 지식 쓰기 0건, 미정착 미니 태스크 0건, 허브 경로가 작업본이 아님을 순서대로 확인하고, 하나라도 어긋나면 아무것도 쓰지 않고 차단한다(`opal/skills/op-oppb-knowledge-finalize/SKILL.md:42-53`).
- 후보는 미니 태스크마다 수용된 시도 하나의 결과에서만 모으고, 후보에 없는 내용을 새로 지어내지 않는다(`opal/skills/op-oppb-knowledge-finalize/SKILL.md:57-62`).

## 관련 페이지

- [[opal-pilot-project-build]]
- [[op-oppb-project-slice]]
- [[worktree-close-brain-write-contract]] · [[op-brain-ingest]] — 일반 Pilot의 CLOSE 지식 반영 경로

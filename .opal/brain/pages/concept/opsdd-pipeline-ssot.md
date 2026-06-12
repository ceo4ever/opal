---
type: concept
title: opsdd 파이프라인 정본 — SKILL.md SSOT (7단계)
tags: [opsdd, pipeline, ssot, workflow]
sources: [task:018]
related: [readme-ssot-principle]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

opsdd 파이프라인의 유일한 정본은 `~/.opal/skills/opal-pilot-sdd/SKILL.md`다. 정본 표기는 `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE` (7단계)다.

## 결정 배경 (WHY)

task:018(README 최신화) 과정에서 opsdd 파이프라인 표기가 3곳에서 상충함이 발견됐다:

| 출처 | 표기 |
|------|------|
| 레지스트리(`opal-skills-registry.json:99`) | `SPEC → VERIFY → PLAN → TASKS → VERIFY → LOOP → DONE` |
| PROJECT.md | `SPEC → VERIFY → PLAN → TASKS → EXECUTE` |
| SKILL.md(정본) | `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE` |

TASK §제약 'SSOT 우선' + doc-code-mismatch 원칙에 따라 SKILL.md를 정본으로 확정했다.

## 결정 내용

- 정본: `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`
- 이 7단계 표기를 README, 비교표, 사용법 설명 등 모든 등장 위치에서 통일 사용한다.
- 레지스트리·PROJECT.md의 상이 표기는 별도 SSOT 정합 태스크에서 정정 권고 (후속 태스크 후보).

## 영향 범위

- `README.md` 비교표(`README.md:265`)·사용법(`README.md:533`) — task:018에서 정정 완료
- 향후 레지스트리(`opal/core/references/opal-skills-registry.json`) 및 `docs/PROJECT.md` 정합 필요

## 관련 페이지

- [[readme-ssot-principle]]

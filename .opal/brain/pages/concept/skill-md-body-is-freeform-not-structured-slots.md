---
type: concept
title: SKILL.md 본문은 정형 슬롯이 아니라 완결된 자유 형식 문서다
tags:
- skill-authoring
- parsing
- documentation
- lesson
sources:
- task:140
related:
- skill-opal-skill-creator
- readme-ssot-principle
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

스킬 절차 문서(`SKILL.md`) 본문은 정형화된 슬롯(Quick Start·Usage·Arguments·Options·Examples 같은 고정 영어 heading)의 모음이 아니라, 각 스킬이 자유롭게 구성한 완결된 문서다. 이 사실은 55개 스킬 전수 측정으로 확인됐다 — heading 매칭 기반 자동 추출은 사실상 작동하지 않는다. (근거: task:140 DONE.md "달성하지 못한 것", ANALYSIS 전수 측정)

## 결정 배경 (WHY)

OPAL Console 스킬 문서 화면(task:140)은 `SKILL.md` 본문에서 Quick Start·Usage·Arguments·Options·Examples 섹션을 heading 기반으로 추출해 상세 화면에 표시하려 했다. 그러나 실제 55개 스킬 전수를 측정한 결과 `quick_start` 0/55, `usage_markdown` 0/55, `arguments` 0/55, `options` 0/55, `examples` 0/55로, 표준 heading을 쓰는 스킬이 하나도 없었다. 가장 흔하게 관측된 heading(`## 쓰는 법`)조차 보유 파일이 1개뿐이었다. (근거: task:140 DONE.md, ANALYSIS 측정)

반면 YAML frontmatter(`name`, `description`)는 55/55로 균일했다 — 구조화된 데이터는 frontmatter에만 있고, 본문은 스킬 작성자마다 다른 자유 형식(`## 입력 분기`, `## STEP 1: TASK` 등)을 쓴다. (근거: task:140 DONE.md 결과)

## 결정 내용

- **frontmatter는 구조화 데이터로 신뢰할 수 있다.** `name`·`description` 같은 frontmatter 필드는 파싱 대상으로 안전하다.
- **본문은 heading 매칭으로 슬롯을 추출하는 방식이 성립하지 않는다.** 각 `SKILL.md`가 자기 완결적 문서 형식을 자유롭게 채택하므로, 특정 영어 heading을 전제한 파서는 거의 모든 스킬에서 빈 결과를 낸다.
- **후속 대응 방향(task:140 종료 시점 결정)**: heading 기반 섹션 추출을 재시도하는 대신, 좌측 스킬 목록 + 우측 `README.md`(또는 `SKILL.md` 폴백) 원문 렌더 구조로 전환한다. 원문을 그대로 보여주는 편이 각 스킬의 실제 문서 형식을 왜곡 없이 전달한다.
- **파싱 실패는 발명하지 않고 부재로 표시한다.** 추출 실패 필드는 `null`/`[]`로 반환하고, UI는 거짓 기본값 대신 명시적 생략이나 "없음"으로 표현해야 한다 — 이 원칙 자체는 유지되지만, 표시 대상 자체를 heading 슬롯에서 원문 렌더로 바꾸는 것이 근본 대응이다.

## 영향 범위

- `dashboard/backend/parsers/skill_parser.py` — heading 기반 섹션 추출 로직 (task:140에서 도입했으나 0/55 성공률로 사용자 가치가 없음이 확인됨)
- 후속 태스크의 상세 화면 설계 — README/SKILL.md 원문 렌더 구조로 교체 예정
- 스킬 작성 규약을 다루는 향후 결정 — 본문 표준화를 강제할지, 원문 렌더를 유지할지의 선택지에 이 실측이 근거로 쓰인다

## 관련 페이지

- [[skill-opal-skill-creator]]
- [[readme-ssot-principle]]

---
name: op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규
description: 현재 op-task-qa가 코드 개발 QA 특화(qa-dev-guide.md) — op-dev-qa로 리네이밍 후 범용 op-task-qa 신규 생성 필요
type: task
---

현재 op-task-qa 스킬이 코드 개발 관점의 QA 가이드(qa-dev-guide.md, qa-wireframe-guide.md)를 가지고 있어 범용 오케스트레이터(opal-project-pilot)의 QA Gate로 부적합하다.

**계획:**
1. op-task-qa → op-dev-qa로 리네이밍 (코드 개발 특화)
2. 범용 op-task-qa 신규 생성 (도메인 무관)
3. op-task-qa-agent도 리네이밍 검토 필요

**영향 범위:**
- 기존 오케스트레이터(opds/opd/opdw)의 QA Gate 참조 변경
- 하네스의 QA Gate 탐색 경로 변경
- agents.md, skills.md, opal-skills-registry.json 업데이트

**Why:** 045 태스크에서 opal-project-pilot 도입하면서, PLAN 후 QA Gate에 범용 QA가 필요함을 확인.

**How to apply:** 별도 태스크로 진행. 영향 범위가 크므로 신중히.

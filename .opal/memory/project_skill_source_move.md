---
name: OPAL 전용 스킬 소스 디렉토리 이동
description: opal-pilot/op-dev/op-task/opal-* 스킬을 skills/ → opal/skills/로 이동하여 standalone만 skills/에 남기는 작업
type: task
---

OPAL 전용 스킬(opal-pilot-*, op-dev-*, op-task-*, opal-agent-creator, opal-skill-creator, opal-project-init)을 `opal/skills/`로 이동하고, `skills/`에는 standalone만 남긴다.

**Why:** 042에서 리네이밍은 완료했으나 소스 위치는 미변경. OPAL 전용과 standalone이 `skills/`에 혼재 중.
**How to apply:** 별도 태스크로 진행. install-mac.sh 배포 로직, JSON paths, 내부 참조 모두 갱신 필요.

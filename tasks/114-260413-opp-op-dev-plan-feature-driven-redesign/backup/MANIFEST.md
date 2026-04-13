# backup MANIFEST

> 백업 시점: 2026-04-13 13:48 KST
> 태스크: 114-op-dev-plan 탑다운 기능 중심 구조 개편
> 목적: 수정 전 원본 보관 (롤백 안전성)

## 백업 파일 목록

| # | 원본 경로 | 백업 경로 | 크기(bytes) |
|---|----------|----------|-----------|
| 1 | `opal/skills/op-dev-plan/SKILL.md` | `backup/opal/skills/op-dev-plan/SKILL.md` | 11108 |
| 2 | `opal/skills/op-dev-plan/references/plan-guide.md` | `backup/opal/skills/op-dev-plan/references/plan-guide.md` | 14208 |
| 3 | `opal/skills/op-dev-execute/SKILL.md` | `backup/opal/skills/op-dev-execute/SKILL.md` | 9845 |
| 4 | `opal/skills/op-dev-execute/references/execute-guide.md` | `backup/opal/skills/op-dev-execute/references/execute-guide.md` | 7777 |
| 5 | `opal/skills/op-dev-qa/SKILL.md` | `backup/opal/skills/op-dev-qa/SKILL.md` | 6354 |
| 6 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md` | 5336 |
| 7 | `skills/ui-designer/SKILL.md` | `backup/skills/ui-designer/SKILL.md` | 12377 |
| 8 | `skills/ui-designer/modes/plan-driven.md` | `backup/skills/ui-designer/modes/plan-driven.md` | 4348 |

## 복원 방법

```bash
# 태스크 루트에서 실행
cp -R backup/opal /Volumes/Data/AiStudio/workspace/opal/
cp -R backup/skills /Volumes/Data/AiStudio/workspace/opal/
```

## 변경이력

| 일시 | 변경내용 |
|------|---------|
| 2026-04-13 13:48 KST | 초기 작성 — 태스크 114 수정 전 원본 8개 파일 백업 |

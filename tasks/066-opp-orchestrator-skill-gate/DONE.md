# DONE: 오케스트레이터 스킬 게이트

> 완료일: 2026-04-01 | 태스크: 066

## 완료 요약

태스크 폴더 생성 시점부터 오케스트레이터 스킬이 강제 결정되도록 op-task, harness, PROJECT.md, AGENT.md를 업데이트했다. 다음 태스크부터 `tasks/{NNN}-{스킬약어}-{설명}/` 형식이 적용된다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/op-task/SKILL.md` | 저장경로에 스킬약어 추가, TASK.md 헤더에 `적용 스킬` 필드, STEP 5(오케스트레이터 선택+추천테이블+완료보고) 추가 |
| `~/.opal/skills/op-task/SKILL.md` | 소스와 동기화 |
| `opal/core/references/opal-harness.md` | §4 스킬약어 전달 의무 + 완료 보고 형식에 `적용 스킬` 추가 |
| `~/.opal/references/opal-harness.md` | 소스와 동기화 |
| `docs/PROJECT.md` | tasks/ 네이밍 규칙 `{NNN}-{스킬약어}-{설명}/` 명확화 |
| `.opal/AGENT.md` | 확정 기준 #1 추가 — 폴더 생성 전 오케스트레이터 결정 필수 |

## QA 결과

- 전체 6개 Step [x] 완료
- QA 체크리스트 11/12 통과 (변경이력 섹션 미정의 N/A 처리)

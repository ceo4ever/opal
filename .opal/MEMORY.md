# opal Memory Index

> 최종 갱신: 2026-03-30 22:30

## 메모리 카테고리

| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**

## 메모리

| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|---|----------|----------|------|------|------|
| 1 | 2026-03-22 | task | 예정 | [memory/project_security_task.md](memory/project_security_task.md) | 보안 전용 스킬+에이전트 생성 |
| 3 | 2026-03-27 | project | 유효 | [memory/project_opi_vision.md](memory/project_opi_vision.md) | opi 비전: 프로젝트=WHAT/WHY, 스킬=HOW |
| 4 | 2026-03-30 22:00 | task | 예정 | [memory/task_agentic_loop.md](memory/task_agentic_loop.md) | oppd에 agentic 자율 루핑(QA/TEST) 장치 설계 |

## 작업 히스토리 (최대 10개, FIFO)

| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|---|------|------|------|---------|---------|
| 0 | 오케스트레이터 정비 — opw 삭제 + 리네이밍 + oppd opwt 연동 (052) | 완료 | tasks/052-orchestrator-cleanup/ | 2026-03-30 21:30 | 2026-03-30 22:30 |
| 1 | OPAL 전용 스킬 소스 이동 (051) | 완료 | tasks/051-opal-skill-source-move/ | 2026-03-30 | 2026-03-30 |
| 2 | opi 범용 프로젝트 분석 개선 (050) | 완료 | tasks/050-opi-universal-analysis/ | 2026-03-30 | 2026-03-30 |
| 3 | 워커 에이전트 프로젝트 컨텍스트 자율 로딩 (049) | 완료 | tasks/049-agent-project-context/ | 2026-03-30 | 2026-03-30 |
| 4 | CLAUDE.md 슬림화 + PM 컨텍스트 최적화 (047) | 완료 | tasks/047-opi-claude-md-slim/ | 2026-03-30 | 2026-03-30 |
| 5 | QA 에이전트 통합 (048) | 완료 | tasks/048-qa-agent-unify/ | 2026-03-29 | 2026-03-29 |
| 6 | op-task-qa → op-dev-qa 리네이밍 + 범용 QA (046) | 완료 | tasks/046-qa-skill-rename/ | 2026-03-29 | 2026-03-29 |
| 7 | 멀티 플랫폼 모델 매핑 참조 + 스킬 적용 (044) | 완료 | tasks/044-model-mapping-reference/ | 2026-03-29 | 2026-03-30 |
| 8 | opal-project-pilot + 범용 스킬 + 에이전트 리네이밍 (045) | 완료 | tasks/045-opal-project-pilot/ | 2026-03-29 | 2026-03-29 |
| 9 | opal-doc-standard v2.0 문서 유형 확장 (043) | 완료 | tasks/043-doc-standard-enhancement/ | 2026-03-29 | 2026-03-29 |
| 10 | 컴포넌트 리네이밍 + 레거시 정리 (042) | 완료 | tasks/042-skills-registry-reclassify/ | 2026-03-29 | 2026-03-29 |

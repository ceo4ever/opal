# opal Memory Index

> 최종 갱신: 2026-04-17 17:09
> last_task_number: 123

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

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|----------|------|------|------|
| 2026-03-22 | project | 진행 중 | [memory/project_security_task.md](memory/project_security_task.md) | 보안 전용 컴포넌트 — TEST(코드 보안) 122에서 완료, PLAN(설계 보안)은 후속 분리 유지 |
| 2026-04-09 | task | 예정 | [memory/task_098_vector_store.md](memory/task_098_vector_store.md) | OPAL Vector Store — sqlite-vec 기반 문서 벡터 검색 도구 (PLAN ✅, EXECUTE 보류) |


## 작업 히스토리 (최대 10개, FIFO)

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-04-17 | 산출물 인용 위치 추적 하네스 — Citation Rules (123) | 완료 | tasks/123-260417-opp-citation-rules/ | 2026-04-17 08:35 | 2026-04-17 09:25 |
| 2026-04-17 | opal-pilot-gc 경량 Pilot + 보안/컨벤션 에이전트 개발 (122) | 완료 | tasks/122-260417-opp-opal-gc/ | 2026-04-17 07:42 | 2026-04-17 17:09 |
| 2026-04-15 | 파이프라인 현황판 CLOSE 단계 분리 (121) | 완료 | tasks/121-260415-opp-close-stage-separation/ | 2026-04-15 15:18 | 2026-04-15 17:20 |
| 2026-04-15 | opal-pm.md 핵심 제약 인용 의무 규칙 추가 + 파일럿 디스패치 템플릿 보완 (120) | 완료 | tasks/120-260415-opp-pm-constraint-citation-rule/ | 2026-04-15 15:10 | 2026-04-15 15:24 |
| 2026-04-15 | README.md 업데이트 — 최근 변경 반영 + 설치/설정 확장 (119) | 완료 | tasks/119-260415-opp-readme-update/ | 2026-04-15 14:28 | 2026-04-15 14:51 |
| 2026-04-15 | code-scan search/exports 정규식 전환 (118) | 완료 | tasks/118-260415-opp-code-scan-regex-search/ | 2026-04-15 14:09 | 2026-04-15 14:22 |
| 2026-04-15 | 전문 개발 에이전트 시스템 설계 (117) | 완료 | tasks/117-260415-opp-specialist-agent-system/ | 2026-04-15 08:02 | 2026-04-15 14:20 |
| 2026-04-13 | PLAN 워커 TEST-SCENARIO 통합 + QA Gate 제거 + PM Gate 검증 강화 (115) | 완료 | tasks/115-260413-opp-plan-ts-merge-pm-gate/ | 2026-04-13 17:23 | 2026-04-13 |
| 2026-04-13 | op-dev-plan 탑다운 기능 중심 구조 개편 + 후속 파이프라인 정합화 (114) | 완료 | tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/ | 2026-04-13 12:28 | 2026-04-13 14:11 |
| 2026-04-12 | .md @header 필드 재정의 — 기획/설계 layer 5개 (113) | 완료 | tasks/113-260412-opp-header-standard-md-layer/ | 2026-04-12 18:20 | 2026-04-12 18:30 |
| 2026-04-12 | 역할 전환 메커니즘 v2 — 프로젝트 기반 자동 전환 (112) | 완료 | tasks/112-260412-opp-role-switch-v2/ | 2026-04-12 14:11 | 2026-04-12 14:46 |
| 2026-04-12 | opal-harness.md 모듈화 — harness/ 폴더 분리 (111) | 완료 | tasks/111-260412-opp-harness-modularize/ | 2026-04-12 11:59 | 2026-04-12 12:57 |

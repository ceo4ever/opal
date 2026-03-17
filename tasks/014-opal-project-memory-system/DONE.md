# DONE: OPAL 프로젝트 메모리 시스템

> 완료일: 2026-03-17 | 모드: Short Task | 작업 유형: 신규 개발

## 완료 요약

프로젝트별 메모리 시스템을 설계·구현했다. `{프로젝트}/.opal/MEMORY.md` 인덱스 + `memory/*.md` 개별 파일 구조로, 부트스트랩 시 인덱스만 읽고 필요한 메모리를 선택적으로 로드하는 토큰 효율적 방식이다. project-init 없이도 소유자 요청 시 독립 생성 가능하다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/templates/memory-index.md` | (신규) MEMORY.md 초기 템플릿 (13행) |
| 2 | `opal/core/AGENT.md` | "기억과 학습" 섹션에 저장소/갱신 규칙 추가, "프로젝트 컨텍스트"에 MEMORY.md 항목 추가 |
| 3 | `opal/skills/orchestrator/SKILL.md` | Step 1을 3단계로 확장 (메모리 로드), Step 6 메모리 갱신 신규 추가 |

## 핵심 변경 사항

### Before
- AGENT.md "기억과 학습": 행동 규칙만 정의, 실제 저장소 없음
- orchestrator: 메모리 관련 로직 없음
- 세션 간 프로젝트 기억 유지 불가

### After
- 저장소 정의: `{프로젝트}/.opal/MEMORY.md` (인덱스) + `memory/*.md` (개별 파일)
- 5가지 갱신 트리거: 태스크 완료, 아키텍처 결정, 소유자 요청, 반복 이슈, 패턴 인식
- 독립 생성: `.opal/AGENT.md` 없이도 메모리 단독 생성 가능
- orchestrator: Step 1에서 메모리 로드, Step 6에서 메모리 갱신
- 정리 규칙: 작업 히스토리 FIFO 10개, 소유자 요청 시 정리 제안

## QA 결과

| 단계 | 판정 | 상세 |
|------|------|------|
| QA-PLAN (v3.0) | Pass | 5/5 항목 통과 |
| QA-EXECUTE | Pass | 7/7 항목 통과, 소스-배포 동기화 확인 |
| 셀프 QA | Pass | 12/12 항목 통과 (기능 4, 회귀 4, 품질 4) |

## 산출물 목록

| 파일 | 설명 |
|------|------|
| TASK.md | 작업 정의서 |
| PLAN.md (v3.0) | 구현 계획 (메모리 스코프) |
| QA-PLAN.md | PLAN QA 리뷰 |
| QA-EXECUTE.md | EXECUTE QA 리뷰 |
| DONE.md | 본 완료 리포트 |

## 후속 태스크

프로젝트 에이전트 개편 (별도 태스크):
- `.opal/AGENT.md` 분리형 구조 (ARCHITECTURE.md, CONVENTIONS.md)
- `project-init` 마이그레이션 모드 (기존 프로젝트 지원)

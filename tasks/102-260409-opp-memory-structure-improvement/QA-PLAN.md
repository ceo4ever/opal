# QA: PLAN — MEMORY.md 구조 개선 — 태스크 번호 관리 + 타임스탬프 + 테이블 형식

> 검토일: 2026-04-09 | 판정: Pass

## 1. 요약

MEMORY.md의 구조적 문제(태스크 번호 미관리, 순번 컬럼 의미 없음, 타임스탬프 시간 누락)를 개선하는 태스크의 실행 계획이다.
총 5개 Step, 2개 Phase로 구성되며, Step 1~4는 병렬 실행 가능하고 Step 5(MEMORY.md 마이그레이션)는 Step 2 완료 후 순차 실행한다.
주요 변경 대상은 `opal/tools/date/date.js` 신규 생성, `opal/core/AGENT.md` + `opal-harness.md` + `op-task/SKILL.md` 수정, `.opal/MEMORY.md` 마이그레이션 5개 파일이다.
TASK.md 요구사항 7개 모두 PLAN Step에 빠짐없이 반영되었으며, 각 Step의 완료 기준이 구체적으로 명시되어 있다.
harness 파일 크기(13806 tokens) 리스크에 대한 대응 방안(offset/limit Read + 핀포인트 Edit)이 명시되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 각 Step마다 파일 경로, 작업 내용, 완료 기준, 테스트 방법이 명시됨 |
| GP-2 | 의존성 순서 | Pass | Phase 1(병렬: Step 1-4) → Phase 2(순차: Step 5) 순서가 올바름. Step 5가 Step 2 완료 후 실행됨을 명시 |
| GP-3 | TASK 반영 | Pass | 요구사항 7개 모두 PLAN Step에 매핑됨 (상세 교차 참조 §4 참조) |
| GP-4 | 파일 목록 완전성 | Pass | TASK.md 영향 파일 테이블과 PLAN.md 파일 변경 계획이 일치. `scripts/install-mac.sh`는 수정 불필요(자동 배포)로 분류됨 |
| GP-5 | 설계 구체성 | Pass | date.js 설계, AGENT.md 변경 전/후, harness 추가 내용, op-task SKILL.md 변경 전/후, MEMORY.md 마이그레이션 절차까지 상세 명세됨 |
| GP-6 | 체크리스트 커버리지 | Pass | 5개 Step이 7개 요구사항을 완전히 커버. QA 체크리스트 §4에 기능·일관성·문서 품질 검증 항목이 구체적으로 나열됨 |

## 3. 지적 사항

지적 사항 없음

### 심각도 분류

- Critical: 없음
- Warning: 없음
- Info: 없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md 요구사항 #1 (`last_task_number` 채번 규칙) | Step 3 (harness §4 채번 절차) + Step 5 (MEMORY.md 헤더 `last_task_number: 102`) 에서 반영 | Pass |
| TASK.md 요구사항 #2 (메모리 인덱스 형식 변경) | Step 2 (AGENT.md 정의 갱신) + Step 5 (MEMORY.md 실제 테이블 변경) 에서 반영 | Pass |
| TASK.md 요구사항 #3 (작업 히스토리 형식 변경) | Step 2 (AGENT.md 정의 갱신) + Step 5 (MEMORY.md 실제 테이블 변경, FIFO 10개 적용) 에서 반영 | Pass |
| TASK.md 요구사항 #4 (타임스탬프 KST 의무화) | Step 2 (AGENT.md 타임스탬프 취득 규칙 추가) + Step 3 (harness §4/§5 bash 의무 규칙 추가) 에서 반영 | Pass |
| TASK.md 요구사항 #5 (`date.js` 신규 구현) | Step 1 (date.js 유틸리티 구현) 에서 반영. 3가지 포맷(yymmdd/date/datetime) 모두 명세됨 | Pass |
| TASK.md 요구사항 #6 (태스크 폴더명 명명 규칙 변경) | Step 3 (harness §4 저장 경로 갱신) + Step 4 (op-task SKILL.md 저장 경로 갱신) 에서 반영 | Pass |
| TASK.md 요구사항 #7 (MEMORY.md 데이터 마이그레이션) | Step 5 에서 반영. 13개 → 10개 FIFO 삭제 대상 명시, 등록일자 추출 방법 명시 | Pass |
| TASK.md 제약 조건 (~/.opal/ 배포본 직접 수정 금지) | PLAN 파일 목록이 모두 `opal/core/`, `opal/skills/`, `opal/tools/` 소스 경로 사용 | Pass |
| TASK.md 제약 조건 (기존 태스크 소급 변경 불필요) | PLAN §5 리스크 테이블에 "허용된 혼재"로 명시됨 | Pass |

## 5. 판정

**Pass**

TASK.md 요구사항 7개가 PLAN Step에 모두 반영되었고, 각 Step의 완료 기준이 검증 가능하며, Phase 구조(병렬/순차) 의존성이 올바르다. harness 파일 크기 리스크에 대한 대응 방안도 명시되어 즉시 EXECUTE 단계로 진행 가능하다.

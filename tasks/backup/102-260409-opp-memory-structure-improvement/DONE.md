# DONE: MEMORY.md 구조 개선 — 태스크 번호 관리 + 타임스탬프 + 테이블 형식

> 완료일: 2026-04-09 13:01
> 태스크: 102 | 스킬: opp

## 완료 요약

MEMORY.md 구조적 문제 5가지를 해결하고, 날짜 유틸리티 툴을 신규 구현했다.

## 변경 파일

| 파일 | 유형 | 내용 |
|------|------|------|
| `opal/tools/date/date.js` | 신규 생성 | KST 날짜/시각 취득 Node.js 유틸리티 (yymmdd/date/datetime) |
| `opal/core/AGENT.md` | 수정 | 메모리 인덱스/히스토리 형식 갱신, 타임스탬프 취득 bash 의무 규칙 추가 |
| `opal/core/references/opal-harness.md` | 수정 | §4 채번 규칙 + 폴더명 날짜 포함, §5 KST bash 의무 규칙 추가 |
| `opal/skills/op-task/SKILL.md` | 수정 | 저장 경로 날짜 포함 형식 + last_task_number 채번 방식으로 갱신 |
| `.opal/MEMORY.md` | 수정 | last_task_number 추가, 테이블 형식 변경, 데이터 마이그레이션 |

## 주요 변경 내용

### date.js 유틸리티
- `node ~/.opal/tools/date/date.js yymmdd` → `260409` (폴더명용)
- `node ~/.opal/tools/date/date.js date` → `2026-04-09` (등록일자용)
- `node ~/.opal/tools/date/date.js datetime` → `2026-04-09 13:01` (타임스탬프용)

### MEMORY.md 구조 변경
- `last_task_number: 102` 필드 추가
- 메모리 인덱스: `| # | 등록일시 | ...` → `| 등록일시 | ...`
- 작업 히스토리: `| # | 작업 | ...` → `| 등록일자 | 작업 | ...`
- 13개 → 10개 FIFO 적용

### 태스크 폴더명 새 규칙
- `tasks/{NNN}-{스킬약어}-{태스크명}/` → `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`

## 잔존 Minor 이슈

- `opal/skills/op-task/SKILL.md` 완료 보고 코드 블록 내 구 폴더명 형식 잔존 (기능 영향 없음, 추후 패치 권장)

## QA 결과

- QA Gate (PLAN): Pass
- QA Gate (EXECUTE): Pass (Minor 1건)

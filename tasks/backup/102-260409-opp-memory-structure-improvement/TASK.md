# TASK: MEMORY.md 구조 개선 — 태스크 번호 관리 + 타임스탬프 + 테이블 형식

> 작성일: 2026-04-09 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

MEMORY.md의 구조적 문제(태스크 번호 미관리, 순번 컬럼 불필요, 타임스탬프 시간 누락)를 개선하고, PM이 KST 시각을 bash로 주입하는 행위를 의무화한다. 태스크 폴더명에 날짜를 포함하는 새 명명 규칙도 적용한다.

## 배경

MEMORY.md 작업 히스토리와 메모리 인덱스 테이블에 여러 구조적 문제가 누적되어 있다.

## 배경 분석 (대화에서 도출)

### 현재 문제 5가지

1. **태스크 번호를 메모리에서 관리하지 않음**: 신규 태스크 생성 시 NNN을 결정하려면 `tasks/` 폴더를 스캔하거나 히스토리를 뒤져야 함 — 비효율적이고 오류 가능성 있음
2. **작업 히스토리 순번(`#`) 컬럼 의미 없음**: 현재 모두 `| 0 |`으로 기록되어 식별 불가능, 관리 부담만 가중
3. **메모리 인덱스 순번(`#`) 컬럼 불필요**: 등록일시가 더 유의미한 식별 기준이며, 순번 컬럼이 맨 앞에 있어 가독성을 해침
4. **시작일시/완료일시에 시간 누락**: `YYYY-MM-DD`만 기록되어 같은 날 복수 태스크 작업 시 순서 불명확. AGENT.md에 `HH:mm` 기록 의무가 명시되어 있음에도 반복 미준수
5. **KST 시각 bash 주입 부담**: 알투가 타임스탬프 기록 시 `TZ=Asia/Seoul date` 명령 실행을 부담스러워하여 날짜만 기록하는 패턴 반복
6. **작업 히스토리에 등록일자 없음**: 히스토리 행에서 언제 태스크가 시작됐는지 한눈에 파악 불가
7. **태스크 폴더명에 날짜 없음**: `{NNN}-{스킬}-{이름}` 형식이라 폴더명만 보고 작업 시점 파악 불가

### 영향 파일

| 파일 | 변경 범위 |
|------|---------|
| `.opal/MEMORY.md` | 구조 변경 + 기존 데이터 마이그레이션 |
| `opal/core/AGENT.md` | 기억과 학습 섹션 — 형식 정의 갱신 |
| `opal/core/references/opal-harness.md` | §4 태스크 번호 채번 규칙, §5 타임스탬프 규칙 추가 |

## 확정된 설계 방향 (대화에서 합의)

### §1 last_task_number 관리

- MEMORY.md에 `last_task_number` 필드를 추가한다
- 신규 태스크 생성 시: MEMORY.md에서 `last_task_number` 읽기 → +1 계산 → MEMORY.md 갱신 → 폴더 생성
- harness §4에 이 절차를 명시한다

### §2 테이블 형식 변경

- **메모리 인덱스**: `| # | 등록일시 | ...` → `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- **작업 히스토리**: `| # | 작업 | ...` → `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
  - `등록일자`: `YYYY-MM-DD` (태스크 TASK 단계 시작일, 시간 불필요)

### §4 태스크 폴더명 명명 규칙 변경

- 현재: `tasks/{NNN}-{스킬약어}-{태스크명}/`
- 변경: `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`
- `{YYMMDD}`: TASK 단계 시작일 (KST) — `TZ=Asia/Seoul date +%y%m%d` 로 취득
- harness §4 저장 경로 규칙, op-task SKILL.md 저장 경로 규칙에 반영

### §3 타임스탬프 — KST bash 의무화

- 형식: `YYYY-MM-DD HH:mm` (KST)
- PM은 타임스탬프 기록 시 **반드시** `TZ=Asia/Seoul date "+%Y-%m-%d %H:%M"` 명령을 실행하여 현재 KST 시각을 취득한다
- "컨텍스트에 날짜가 있으니 bash 생략" 행위 금지 — 시간(HH:mm)까지 정확히 기록해야 하므로 bash 실행은 선택이 아니라 필수
- harness §4와 §5에 이 규칙을 명시한다

## 요구사항

- [x] **`last_task_number` 필드 추가 및 채번 규칙 수립**
  - 무엇을: MEMORY.md 헤더에 `last_task_number: 101` 추가 + harness §4 TASK 공통 프로세스에 "MEMORY.md에서 last_task_number 읽어 +1, 생성 후 갱신" 절차 명시
  - 어디에: `.opal/MEMORY.md`, `opal/core/references/opal-harness.md` §4, `opal/core/AGENT.md`
  - 왜: tasks/ 폴더 스캔 없이 메모리에서 즉시 다음 번호 취득 가능
  - AC: MEMORY.md에 `last_task_number` 필드가 존재하고, harness §4에 채번 절차가 명시된다

- [x] **메모리 인덱스 테이블 형식 변경 (`#` 제거, 등록일시 맨 앞)**
  - 무엇을: 메모리 인덱스 테이블에서 `#` 컬럼 제거, 형식을 `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`로 변경
  - 어디에: `.opal/MEMORY.md` + `opal/core/AGENT.md` 메모리 인덱스 형식 정의
  - 왜: 순번은 관리 부담 대비 가치 없음, 등록일시가 핵심 식별 정보
  - AC: MEMORY.md 메모리 인덱스 테이블이 `| 등록일시 | ...` 형식이고, 기존 데이터가 마이그레이션되며, AGENT.md 정의가 갱신된다

- [x] **작업 히스토리 테이블 형식 변경 (`#` 제거, 등록일자 맨 앞 추가)**
  - 무엇을: 작업 히스토리 테이블에서 `#` 컬럼 제거, 형식을 `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`로 변경
  - 어디에: `.opal/MEMORY.md` + `opal/core/AGENT.md` 작업 히스토리 형식 정의
  - 왜: `| 0 |`으로만 채워진 순번은 노이즈, 등록일자로 히스토리 시점을 한눈에 파악
  - AC: MEMORY.md 작업 히스토리 테이블이 `| 등록일자 | 작업 | ...` 형식이고, 기존 데이터가 마이그레이션된다

- [x] **타임스탬프 KST HH:mm 의무화 — harness + AGENT.md 명시**
  - 무엇을: harness §4와 §5에 "PM은 타임스탬프 기록 시 `TZ=Asia/Seoul date` 실행 필수" 규칙 추가. AGENT.md 기억과 학습 섹션 갱신
  - 어디에: `opal/core/references/opal-harness.md` §4, §5 + `opal/core/AGENT.md`
  - 왜: bash 실행 부담으로 시간 기록이 반복 누락되는 근본 원인 제거 — 규칙으로 강제
  - AC: harness에 KST bash 명령 필수 실행 규칙이 명시되고, AGENT.md 타임스탬프 형식에 `HH:mm` 의무가 재확인된다

- [x] **`opal/tools/date/date.js` 날짜 툴 신규 구현**
  - 무엇을: `node ~/.opal/tools/date/date.js [format]` 형태로 호출하는 Node.js 유틸리티 생성. 현재까지 논의된 포맷을 기본 제공하고, 포맷 추가가 쉬운 구조로 설계
  - 어디에: `opal/tools/date/date.js` (소스), 배포 경로는 `install-mac.sh` 담당
  - 지원 포맷 (초기 버전):
    - `yymmdd` → `260409` (짧은일자 - 폴더이름 등)
    - `date` → `2026-04-09` (일자 - YYYY-MM-DD, 등록일자 등)
    - `datetime` → `2026-04-09 10:29:33` (일시 - YYYY-MM-DD HH:mm:ss, 타임스탬프용, 시작일시, 등록일시 등 )
  - 왜: 날짜/시각 취득 로직을 단일 지점에서 관리 — 포맷·타임존 변경 시 `date.js` 1곳만 수정하면 전체 적용
  - AC: `node opal/tools/date/date.js yymmdd` 실행 시 KST 기준 `YYMMDD` 문자열 출력, 나머지 포맷도 동일하게 동작, 인자 없을 시 사용법 출력

- [x] **태스크 폴더명 명명 규칙 변경 — 날짜 포함**
  - 무엇을: 폴더 형식을 `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`으로 변경, harness §4 저장 경로 규칙 + op-task SKILL.md 저장 경로 규칙 갱신
  - 어디에: `opal/core/references/opal-harness.md` §4 + `opal/core/skills/op-task/SKILL.md`
  - 왜: 폴더명만 보고 작업 시점을 즉시 파악 가능, 날짜-번호 정렬 일관성 확보
  - AC: harness §4 저장 경로 규칙이 날짜 포함 형식으로 갱신되고, op-task SKILL.md 저장 경로도 동기화된다

- [x] **`.opal/MEMORY.md` 기존 데이터 마이그레이션**
  - 무엇을: 현재 MEMORY.md의 메모리 인덱스 + 작업 히스토리 데이터를 새 형식으로 변환 (시간은 알 수 없으므로 기존 날짜 유지, 등록일자는 시작일시 날짜 사용)
  - 어디에: `.opal/MEMORY.md`
  - 왜: 구조 변경 후 기존 데이터가 새 테이블 형식과 일치해야 함
  - AC: 기존 데이터가 새 형식으로 모두 변환되고, 데이터 누락이 없다

## 제약 조건

- `~/.opal/` 배포본 직접 수정 금지 — 소스(`opal/core/`, `opal/core/references/`)에서만 수정
- 기존 완료 태스크의 STATE.md 소급 변경 불필요 (신규 태스크부터 적용)
- 기존 작업 히스토리의 시간 정보는 알 수 없으므로 날짜만 유지 (레거시 허용)

## 기술 스택

- Markdown 문서
- OPAL AGENT.md, harness 구조

## 관련 문서

- `opal/core/AGENT.md` — 기억과 학습 섹션 (메모리 인덱스 형식, 작업 히스토리 형식)
- `opal/core/references/opal-harness.md` — §4 TASK 공통 프로세스 (저장 경로 규칙), §5 프로젝트 메모리 동기화
- `.opal/MEMORY.md` — 실제 메모리 데이터

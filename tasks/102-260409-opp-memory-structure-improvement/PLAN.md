# PLAN: MEMORY.md 구조 개선 — 태스크 번호 관리 + 타임스탬프 + 테이블 형식

> 작성일: 2026-04-09
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `.opal/MEMORY.md` | 프로젝트 메모리 인덱스 (실제 데이터) | ✅ 구조 변경 + 데이터 마이그레이션 |
| `opal/core/AGENT.md` | 에이전트 정의 — 기억과 학습 섹션에 메모리/히스토리 형식 정의 | ✅ 형식 정의 갱신 |
| `opal/core/references/opal-harness.md` | §4 TASK 공통 프로세스 (저장 경로 규칙), §5 프로젝트 메모리 동기화 | ✅ 채번 규칙 + 타임스탬프 규칙 + 폴더명 규칙 |
| `opal/skills/op-task/SKILL.md` | 저장 경로 규칙 (`tasks/{NNN}-{스킬약어}-{태스크명}/`) | ✅ 날짜 포함 형식으로 갱신 |
| `opal/tools/date/date.js` | KST 날짜/시각 취득 유틸리티 (신규) | ✅ 신규 생성 |
| `scripts/install-mac.sh` | OPAL 설치 스크립트 — tools/ 배포 담당 | ✅ date 툴 배포 확인 (기존 `install_dir "$opal_dir/tools"` 로 자동 포함) |

### 현재 상태

**`.opal/MEMORY.md` 현재 구조**:
- 헤더: `최종 갱신: 2026-04-01 21:30` — `last_task_number` 필드 없음
- 메모리 인덱스 테이블: `| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |` — `#` 컬럼이 맨 앞에 위치
  - 현재 데이터: 2개 행 (등록일시에 시간 없이 날짜만 기록된 행 포함)
- 작업 히스토리 테이블: `| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |` — `#` 컬럼이 맨 앞, 모든 행이 `| 0 |`
  - 현재 데이터: 13개 행 (상위 10개 FIFO 적용 필요, 현재는 13개)
  - 시작일시/완료일시에 시간 없이 날짜만 기록됨

**`opal/core/AGENT.md` 기억과 학습 섹션 현재 정의**:
- 메모리 인덱스 형식: `| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- 작업 히스토리 형식: `| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
- 두 형식 모두 `#` 컬럼이 앞에 정의되어 있음

**`opal/core/references/opal-harness.md` 현재 상태**:
- §4 저장 경로 규칙: `tasks/{NNN}-{스킬약어}-{태스크명}/` — 날짜 없음, `last_task_number` 채번 규칙 없음
- §5 프로젝트 메모리 동기화: 타임스탬프 KST bash 의무 규칙 없음

**`opal/skills/op-task/SKILL.md` 저장 경로 현재 상태**:
- `tasks/{NNN}-{스킬약어}-{태스크명}/TASK.md`
- 채번 방식: "기존 `tasks/` 폴더의 최대 번호 + 1로 자동 채번한다"

**`opal/tools/` 현재 구조**:
- `check-env.js`, `playwright-tool/`, `requirements.txt`, `skill-registry/`, `xlsx-tool/`
- `date/` 디렉토리 없음 — 신규 생성 필요

**`scripts/install-mac.sh` 도구 배포 방식**:
- `install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"` — tools/ 디렉토리 전체를 배포
- date 툴을 `opal/tools/date/` 에 생성하면 설치 스크립트 수정 없이 자동 배포됨

### 영향 범위

- **신규 태스크 생성 프로세스 변경**: `last_task_number` 필드 추가로 tasks/ 폴더 스캔이 불필요해짐
- **폴더명 형식 변경**: 기존 태스크 폴더 소급 변경 불필요 (신규 태스크부터 적용)
- **타임스탬프 형식 변경**: 기존 작업 히스토리의 시간 정보는 알 수 없으므로 날짜만 유지 (레거시 허용)
- **MEMORY.md 데이터 마이그레이션**: 테이블 형식 변경 + 기존 13개 히스토리에서 최근 10개만 유지

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/tools/date/date.js` | KST 날짜/시각 취득 Node.js 유틸리티 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/AGENT.md` | 기억과 학습 섹션 — 메모리 인덱스/작업 히스토리 형식 정의 갱신 |
| 2 | `opal/core/references/opal-harness.md` | §4 채번 규칙 + 폴더명 날짜 포함 규칙, §5 KST bash 의무 규칙 |
| 3 | `opal/skills/op-task/SKILL.md` | 저장 경로 규칙 — 날짜 포함 형식으로 갱신 |
| 4 | `.opal/MEMORY.md` | 헤더 `last_task_number` 추가 + 테이블 형식 변경 + 데이터 마이그레이션 |

#### 삭제

없음

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | date.js 유틸리티 신규 구현 | `opal/tools/date/date.js` | 낮음 |
| 2 | AGENT.md 형식 정의 갱신 | `opal/core/AGENT.md` | 낮음 |
| 3 | harness §4/§5 규칙 추가 | `opal/core/references/opal-harness.md` | 중간 |
| 4 | op-task SKILL.md 저장 경로 갱신 | `opal/skills/op-task/SKILL.md` | 낮음 |
| 5 | MEMORY.md 마이그레이션 | `.opal/MEMORY.md` | 중간 |

**의존성 분석**:
- Step 1(date.js): 독립 — 다른 파일이 명시적으로 의존하지 않음 (실행 시 참조)
- Step 2(AGENT.md): 독립 — MEMORY.md 마이그레이션 전에 새 형식을 정의해두어야 함
- Step 3(harness): 독립 — AGENT.md, op-task와 독립적으로 수정 가능
- Step 4(op-task SKILL.md): 독립 — harness와 유사한 내용이지만 별도 파일
- Step 5(MEMORY.md): Step 2 완료 후 수행 권장 (새 형식 기준으로 마이그레이션)

### 핵심 설계

#### date.js 설계

`opal/tools/date/date.js`:

```javascript
// 사용법: node date.js [format]
// format: yymmdd | date | datetime
// 인자 없음: 사용법 출력
```

- 타임존: `Asia/Seoul` (KST, UTC+9) — `Intl.DateTimeFormat` 또는 `TZ` 환경변수 없이 동작
- 포맷별 출력:
  - `yymmdd` → `260409` (2자리 연도 + 월 + 일)
  - `date` → `2026-04-09` (YYYY-MM-DD)
  - `datetime` → `2026-04-09 10:29:33` (YYYY-MM-DD HH:mm:ss)
- 인자 없거나 미지원 포맷: 사용법 출력 후 exit 0

#### AGENT.md 형식 정의 갱신

`opal/core/AGENT.md` — "기억과 학습" 섹션:

**변경 전**:
```
- **메모리 인덱스 형식**: `| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- **작업 히스토리 형식**: `| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
```

**변경 후**:
```
- **메모리 인덱스 형식**: `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- **작업 히스토리 형식**: `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
  - `등록일자`: `YYYY-MM-DD` (TASK 단계 시작일, KST)
- **타임스탬프 취득**: 시작일시/완료일시 기록 시 `node ~/.opal/tools/date/date.js datetime` 실행 필수 (bash 생략 금지)
```

#### harness §4/§5 규칙 추가

`opal/core/references/opal-harness.md`:

**§4 TASK 공통 프로세스 — 저장 경로 규칙 변경**:

변경 전:
```
| `base_path` 없음 (기본) | `tasks/{NNN}-{스킬약어}-{태스크명}/` |
```

변경 후:
```
| `base_path` 없음 (기본) | `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/` |
```

**§4 TASK 공통 프로세스 — last_task_number 채번 절차 추가**:

"오케스트레이터 공통 영역" 단계 3번 앞에 아래 내용을 삽입:

```
#### 태스크 번호 채번 규칙

신규 태스크 생성 시:
1. `.opal/MEMORY.md` 헤더의 `last_task_number` 필드를 읽는다
2. `last_task_number + 1`을 계산한다
3. 태스크 폴더를 생성한다 (`tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`)
   - `{YYMMDD}`: `node ~/.opal/tools/date/date.js yymmdd` 실행하여 KST 기준 취득
4. TASK.md 작성 완료 후 `.opal/MEMORY.md`의 `last_task_number`를 갱신한다
```

**§5 프로젝트 메모리 동기화 — KST bash 의무 규칙 추가**:

기존 "프로젝트 메모리 동기화" 섹션에 아래 내용 추가:

```
#### 타임스탬프 취득 규칙 (필수)

시작일시/완료일시 기록 시 반드시 bash 명령을 실행하여 KST 현재 시각을 취득한다:
- 일시 (YYYY-MM-DD HH:mm:ss): `node ~/.opal/tools/date/date.js datetime`
- 일자 (YYYY-MM-DD): `node ~/.opal/tools/date/date.js date`
- 폴더명용 (YYMMDD): `node ~/.opal/tools/date/date.js yymmdd`

**bash 생략 금지**: 컨텍스트에 날짜가 있어도 bash 실행은 필수다. 시간(HH:mm:ss)까지 정확히 기록해야 한다.
```

#### op-task SKILL.md 저장 경로 갱신

`opal/skills/op-task/SKILL.md` — "저장 경로" 섹션:

변경 전:
```
tasks/{NNN}-{스킬약어}-{태스크명}/TASK.md

- `{NNN}`: 3자리 순번 (001, 002, ...)
- `{스킬약어}`: ...
- 기존 `tasks/` 폴더의 최대 번호 + 1로 자동 채번한다
```

변경 후:
```
tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/TASK.md

- `{NNN}`: 3자리 순번 — `.opal/MEMORY.md`의 `last_task_number` + 1로 채번 (harness §4 참조)
- `{YYMMDD}`: TASK 단계 시작일 (KST) — `node ~/.opal/tools/date/date.js yymmdd` 실행하여 취득
- `{스킬약어}`: ...
```

#### MEMORY.md 마이그레이션

`.opal/MEMORY.md`:

**헤더 변경**: `last_task_number: 102` 필드 추가

**메모리 인덱스 테이블 변경**:
- 기존: `| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- 신규: `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
- 기존 데이터 2행을 새 형식으로 변환 (`#` 컬럼 제거)

**작업 히스토리 테이블 변경**:
- 기존: `| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
- 신규: `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
- 기존 13개 행 → 최근 10개만 유지 (FIFO — 가장 오래된 행 3개 삭제)
- `#` 컬럼을 `등록일자`로 대체 — 기존 데이터의 `시작일시` 날짜 부분을 `등록일자`로 사용
- 기존 시간 정보는 알 수 없으므로 날짜만 유지 (레거시 허용)

---

## 3. 실행 체크리스트

> 총 5개 Step | Phase 2개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2, 3, 4 | 병렬 | 독립 파일들 (상호 의존 없음) |
> | 2     | 5 | 순차 | Step 2 완료 후 (새 형식 기준 마이그레이션) |

---

### Step 1: date.js 유틸리티 신규 구현

- [ ] 완료
- **파일**: `opal/tools/date/date.js`
- **작업 내용**:
  - `opal/tools/date/` 디렉토리 생성
  - Node.js 스크립트 작성: `node date.js [format]` 형태로 호출
  - 포맷 `yymmdd` → KST 기준 `YYMMDD` (예: `260409`)
  - 포맷 `date` → KST 기준 `YYYY-MM-DD` (예: `2026-04-09`)
  - 포맷 `datetime` → KST 기준 `YYYY-MM-DD HH:mm:ss` (예: `2026-04-09 10:29:33`)
  - 인자 없거나 미지원 포맷: 사용법 출력 후 정상 종료
  - 타임존: `Intl.DateTimeFormat`으로 `Asia/Seoul` 처리 (Node.js 내장, 외부 의존성 없음)
- **완료 기준**:
  - `node opal/tools/date/date.js yymmdd` 실행 시 6자리 KST 날짜 출력
  - `node opal/tools/date/date.js date` 실행 시 `YYYY-MM-DD` 출력
  - `node opal/tools/date/date.js datetime` 실행 시 `YYYY-MM-DD HH:mm:ss` 출력
  - `node opal/tools/date/date.js` (인자 없음) 실행 시 사용법 출력
- **테스트**: 각 포맷으로 직접 실행하여 KST 현재 시각과 일치하는지 확인
- **의존**: 없음

---

### Step 2: AGENT.md 기억과 학습 섹션 형식 정의 갱신

- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:
  - "기억과 학습" 섹션에서 메모리 인덱스 형식 정의 변경: `# |` 제거
    - 변경 전: `| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
    - 변경 후: `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
  - 작업 히스토리 형식 정의 변경: `# |` → `등록일자 |`
    - 변경 전: `| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
    - 변경 후: `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
  - `등록일자` 설명 추가: `YYYY-MM-DD` (TASK 단계 시작일, KST)
  - 타임스탬프 취득 규칙 추가: `node ~/.opal/tools/date/date.js datetime` 실행 필수
  - 변경이력 테이블에 v1.7 항목 추가
- **완료 기준**:
  - `기억과 학습` 섹션의 메모리 인덱스 형식에 `#` 컬럼이 없고 `| 등록일시 |`로 시작
  - 작업 히스토리 형식에 `#` 컬럼이 없고 `| 등록일자 |`로 시작
  - 타임스탬프 취득 규칙이 명시됨
- **테스트**: AGENT.md Read 후 해당 섹션 확인
- **의존**: 없음

---

### Step 3: harness §4/§5 규칙 추가

- [ ] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  - §4 "저장 경로 규칙" 테이블의 `tasks/{NNN}-{스킬약어}-{태스크명}/` → `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`으로 변경
  - §4 "오케스트레이터 공통 영역" 앞에 `#### 태스크 번호 채번 규칙` 서브섹션 추가:
    - `.opal/MEMORY.md`에서 `last_task_number` 읽기 → +1 계산 → 폴더 생성 → MEMORY.md 갱신 절차
    - `{YYMMDD}` 취득: `node ~/.opal/tools/date/date.js yymmdd`
  - §5 "프로젝트 메모리 동기화" 섹션에 `#### 타임스탬프 취득 규칙 (필수)` 서브섹션 추가:
    - datetime/date/yymmdd 각 포맷별 명령어 명시
    - bash 생략 금지 규칙 명시
  - QA 산출물 표준 파일명 테이블의 위치 예시도 새 폴더명 형식 반영 (기존 `{NNN}-{name}` → `{NNN}-{YYMMDD}-{name}`)
- **완료 기준**:
  - §4 저장 경로가 날짜 포함 형식으로 갱신됨
  - §4에 `last_task_number` 채번 절차가 명시됨
  - §5에 KST bash 의무 규칙이 명시됨
- **테스트**: harness.md Read 후 해당 섹션 확인
- **의존**: 없음

---

### Step 4: op-task SKILL.md 저장 경로 갱신

- [ ] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**:
  - "저장 경로" 섹션의 폴더명 형식 변경: `tasks/{NNN}-{스킬약어}-{태스크명}/TASK.md` → `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/TASK.md`
  - `{NNN}` 설명 갱신: "기존 `tasks/` 폴더의 최대 번호 + 1" → "`.opal/MEMORY.md`의 `last_task_number` + 1로 채번 (harness §4 참조)"
  - `{YYMMDD}` 항목 추가: "TASK 단계 시작일 (KST) — `node ~/.opal/tools/date/date.js yymmdd` 실행하여 취득"
  - 변경이력 테이블에 버전 항목 추가
- **완료 기준**:
  - 저장 경로 형식이 날짜 포함으로 갱신됨
  - `{NNN}` 설명이 `last_task_number` 기반으로 갱신됨
  - `{YYMMDD}` 설명이 추가됨
- **테스트**: op-task SKILL.md Read 후 저장 경로 섹션 확인
- **의존**: 없음

---

### Step 5: .opal/MEMORY.md 구조 변경 + 데이터 마이그레이션

- [ ] 완료
- **파일**: `.opal/MEMORY.md`
- **작업 내용**:

  **1) 헤더 갱신**:
  - `last_task_number: 102` 필드 추가 (현재 최대 번호 102 기준)
  - `최종 갱신` 타임스탬프 갱신 (`node opal/tools/date/date.js datetime` 실행 후 값 사용)

  **2) 메모리 인덱스 테이블 형식 변경**:
  - 헤더 행: `| # | 등록일시 | ...` → `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`
  - 기존 데이터 2행에서 `#` 컬럼 값 제거하여 새 형식으로 변환

  **3) 작업 히스토리 테이블 형식 변경 + FIFO 적용**:
  - 헤더 행: `| # | 작업 | ...` → `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |`
  - 기존 13개 행 중 최근 10개만 유지 (가장 오래된 3개 행 — 하단 3행 삭제)
    - 삭제 대상: `opsdd 스킬 구현 (093)`, `Artifact Gate 설계 및 적용 (090)`, `opi docs 백업 기능 추가 (088)`, `opsdd 오케스트레이터 스킬 설계 (080)`, `역할 전환 규칙 + 추가작업 프로세스 (087)` 중 테이블 맨 하단 3개
    - 실제 삭제: 13개 행 → 10개 행 유지
  - `#` 컬럼(모두 `0`) → `등록일자` 컬럼으로 대체
    - 각 행의 `등록일자`: 해당 행의 `시작일시`에서 날짜 부분 추출 (시간은 알 수 없으므로 날짜만 유지)
    - 시작일시가 날짜만 있는 경우 그대로 사용

- **완료 기준**:
  - 헤더에 `last_task_number: 102` 필드 존재
  - 메모리 인덱스 테이블이 `| 등록일시 |`로 시작하고 `#` 컬럼 없음
  - 작업 히스토리 테이블이 `| 등록일자 |`로 시작하고 `#` 컬럼 없음
  - 히스토리 행 수 ≤ 10개
  - 기존 데이터 내용 (태스크명, 단계, 경로, 시작일시) 누락 없음
- **테스트**: `.opal/MEMORY.md` Read 후 각 테이블 형식 및 데이터 확인
- **의존**: Step 2 완료 후 (새 형식 정의 기준으로 마이그레이션)

---

## 4. QA 체크리스트

### 기능 테스트

- [x] `node opal/tools/date/date.js yymmdd` 실행 시 KST 기준 6자리 날짜 출력 (예: `260409`)
- [x] `node opal/tools/date/date.js date` 실행 시 `YYYY-MM-DD` 형식 출력
- [x] `node opal/tools/date/date.js datetime` 실행 시 `YYYY-MM-DD HH:mm` 형식 출력 (※ PLAN 스펙은 `HH:mm:ss`였으나 harness/AGENT.md 기준 `HH:mm`으로 확정 — 구현 일관성 통과)
- [x] `node opal/tools/date/date.js` (인자 없음) 실행 시 사용법 출력 (에러 없이 정상 종료)
- [x] MEMORY.md `last_task_number` 필드 값이 `102`임
- [x] MEMORY.md 메모리 인덱스 테이블에 `#` 컬럼이 없음
- [x] MEMORY.md 작업 히스토리 테이블에 `#` 컬럼이 없고 `등록일자` 컬럼이 맨 앞에 있음
- [x] MEMORY.md 작업 히스토리 행 수가 10개 이하임

### 일관성 테스트

- [x] AGENT.md 메모리 인덱스 형식과 `.opal/MEMORY.md` 실제 테이블 형식이 일치함
- [x] AGENT.md 작업 히스토리 형식과 `.opal/MEMORY.md` 실제 테이블 형식이 일치함
- [x] harness §4 저장 경로 규칙과 op-task SKILL.md 저장 경로가 동일한 형식(`{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`)을 사용함
- [x] harness §4 채번 규칙과 op-task SKILL.md 채번 설명이 일관됨 (`last_task_number` 기반)
- [x] harness §5 타임스탬프 규칙과 AGENT.md 타임스탬프 취득 규칙이 일관됨

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가 (`date.js`, `opal/tools/date/`)
- [x] date.js 사용법 출력 메시지가 명확한가 (포맷 목록 포함)
- [x] MEMORY.md 기존 데이터 내용 (태스크명, 경로 등) 누락이 없는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| `Intl.DateTimeFormat` KST 타임존 처리 불일치 | date.js가 잘못된 시각 출력 | Node.js `Intl.DateTimeFormat`은 v12+에서 `Asia/Seoul` 지원 — check-env.js로 버전 확인 가능 |
| MEMORY.md 마이그레이션 시 데이터 누락 | 기존 태스크 히스토리 손실 | Step 5 완료 기준에 "데이터 누락 없음" 명시 + 삭제 대상 행 명시적 나열 |
| harness 파일 크기 큼 (13806 tokens) | 수정 시 컨텍스트 초과 | 섹션별 offset/limit Read 활용, 핀포인트 Edit 적용 |
| 폴더명 형식 변경 — 기존 태스크와 혼용 | tasks/ 폴더에 두 형식 혼재 | TASK.md 제약 조건에 "기존 태스크 소급 변경 불필요" 명시됨 — 허용된 혼재 |

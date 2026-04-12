# PLAN: opal-harness.md 구조화 리팩토링

> 작성일: 2026-04-12
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 오케스트레이터 공통 인프라 레퍼런스 (~751줄) | **예** — R-1, R-2, R-3, R-5 |
| `opal/core/references/opal-harness-interactive.md` | interactive 모드 서브 하네스 | **예** — R-4, R-5 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 오케스트레이터 스킬 | 아니오 — 이미 파이프라인 현황판 예시 보유 (lines 287-330) |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 오케스트레이터 스킬 | **예** — 하네스 참조 경로 수정 필요 (line 430) |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | oppd 병렬 실행 가이드 | **예** — 하네스 참조 경로 수정 필요 (lines 308, 372) |

### 현재 상태

#### R-1: opsdd 파이프라인 현황판 예시 (opal-harness.md lines 233-273)
- opal-harness.md §3에 opsdd 전용 43행 파이프라인 현황판 예시가 인라인됨
- opsdd SKILL.md lines 287-330에 **동일한** 파이프라인 현황판이 이미 독립 존재 (상태 컬럼 `⬜` 포함 실제 운용 버전)
- 하네스 쪽 예시는 `| # | Phase | 항목 |` 3컬럼 요약 형태, SKILL.md 쪽은 `| # | Phase | 항목 | 상태 | 시점 |` 5컬럼 운용 형태
- **순수 제거 가능**: 하네스 예시는 SKILL.md의 "STATE.md 도메인 치환값" 존재를 확인하는 예시일 뿐, 독자적 구속력 없음

#### R-2: 병렬 실행 State (opal-harness.md lines 330-386)
- opal-harness.md §3에 oppd 전용 병렬 실행 State 정의 (~55줄): 상태값 열거형, 그룹 요약/태스크 상세 테이블, 머지 이력 테이블, 검증 루프 로그 테이블, 운영 규칙
- **이미 이관 완료된 내용**:
  - oppd SKILL.md lines 520-536: 병렬 실행 현황 + 그룹 요약 + 액션 상세 + 머지 이력 + 검증 루프 로그 테이블
  - oppd `references/parallel-execution-guide.md` lines 370-382: 상태값 열거형 + worktree 컬럼 형식 + STATE.md 예시
- **참조 업데이트 필요**: 3곳에서 "하네스 '병렬 실행 State' 참조" 문구 존재
  - oppd SKILL.md line 430: `하네스 "병렬 실행 State" 참조`
  - parallel-execution-guide.md line 308: `하네스 병렬 실행 State 구조 준수`
  - parallel-execution-guide.md line 372: `하네스에 정의된 병렬 실행 State 구조를 따른다`
- opal-harness.md line 180의 주석 `병렬 실행 State의 열거형과 독립된다`도 갱신 필요

#### R-3: State Gate 자가 점검 프롬프트 레거시 값 (opal-harness.md line 403)
- 현재 프롬프트 3번 항목에 deprecated 상태값 사용:
  ```
  `상태` 필드가 올바른 값인가? (단계 완료: `QA Gate 대기` / QA Gate 통과: `PM Gate 대기` / PM Gate 통과: `사용자 확인 대기` / 사용자 확인 완료: `완료` / 다음 단계 진입: `진행 중`)
  ```
- line 178에서 이 값들을 명시적으로 deprecated 선언함:
  ```
  기존 STATE.md의 `QA Gate 대기` / `PM Gate 대기` / `사용자 확인 대기` 값은 파이프라인 현황판 테이블로 통합되어 더 이상 사용하지 않는다.
  ```
- 현행 상태 관리는 파이프라인 현황판 테이블 행 기반으로 운용됨 → 자가 점검 프롬프트도 행 기반 확인으로 교체해야 함

#### R-4: 수행 순서 강제 원칙 중복
- opal-harness.md line 168: `**수행 순서 강제 원칙**: 파이프라인 현황판 테이블은 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.`
- opal-harness-interactive.md lines 119-127: `### 순서 강제 원칙` + 앞 행 상태 테이블 (✅/- → 가능, ⬜/🔄 → 불가, ❌ → 불가)
- 공통 하네스 §3에 정의를 유지하고, interactive 서브 하네스 §4에서는 참조로 교체

### 영향 범위

- **외부 참조 62개**: §번호(특히 §3)를 참조하는 외부 문서가 다수 — §번호 자체는 변경하지 않으므로 기존 참조 모두 유효
- **oppd 생태계 3파일**: 하네스에서 "병렬 실행 State"를 제거하면, oppd SKILL.md와 parallel-execution-guide.md에서 하네스 참조 문구를 자체 참조로 갱신해야 함
- **opal-harness.md line 180 주석**: `병렬 실행 State의 열거형과 독립된다` — 병렬 실행 State 정의가 oppd로 이동했으므로 참조 경로 갱신 필요
- **기존 오케스트레이터 동작**: 영향 없음 — opsdd 예시 제거는 SKILL.md에 원본이 있고, 병렬 실행 State 제거는 oppd 생태계에 원본이 있으며, State Gate 수정은 현행 파이프라인 현황판 기반으로 정합성 개선

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| - | (없음) | - |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | R-1: opsdd 예시 제거, R-2: 병렬 실행 State 제거 + 참조 주석 갱신, R-3: State Gate 자가 점검 프롬프트 갱신, R-5: 변경이력 추가 |
| 2 | `opal/core/references/opal-harness-interactive.md` | R-4: 순서 강제 원칙 → §3 참조로 교체, R-5: 변경이력 추가 |
| 3 | `opal/skills/opal-pilot-project-dev/SKILL.md` | R-2 후속: "하네스 '병렬 실행 State' 참조" → parallel-execution-guide.md 자체 참조로 갱신 |
| 4 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | R-2 후속: 하네스 참조 문구 2곳 → 자체 정의 참조로 갱신 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opal-harness.md §3 정리 (R-1, R-2, R-3, R-5) | opal-harness.md | 중 |
| 2 | opal-harness-interactive.md §4 정리 (R-4, R-5) | opal-harness-interactive.md | 하 |
| 3 | oppd SKILL.md 참조 갱신 | oppd SKILL.md | 하 |
| 4 | parallel-execution-guide.md 참조 갱신 | parallel-execution-guide.md | 하 |

### 핵심 설계

#### opal-harness.md (Step 1)

**R-1 제거 — opsdd 파이프라인 현황판 예시 (lines 233-273)**:
- `#### opsdd (opal-pilot-sdd) 파이프라인 현황판 행 예시` 서브섹션 전체(헤더 + 테이블 43행)를 삭제
- 삭제 범위: line 233 (`#### opsdd (opal-pilot-sdd) 파이프라인 현황판 행 예시`) ~ line 273 (`| 37 | DONE | 사용자 확인 |`)
- 삭제 후 빈 줄 정리 — `산출물 행 규칙` 서브섹션 뒤에 바로 `### ADD_DONE.md 템플릿`이 이어지도록 함

**R-2 제거 — 병렬 실행 State (lines 330-386)**:
- `### 병렬 실행 State` 서브섹션 전체를 삭제
- 삭제 범위: line 330 (`### 병렬 실행 State`) ~ line 386 (`- 동시 갱신 충돌 방지: 오케스트레이터가 순차적으로 결과를 수집하여 갱신`)
- 삭제 후 빈 줄 정리 — `### 추가작업 프로세스` 서브섹션 종료 구분선 뒤에 바로 `### 세션 복원`이 이어지도록 함

**R-2 후속 — line 180 주석 갱신**:
- 현재: `> \`추가작업중\` / \`추가작업완료\`는 기본 상태값(완료 후 후속 작업 전용)이며, 병렬 실행 State의 열거형과 독립된다.`
- 변경: `> \`추가작업중\` / \`추가작업완료\`는 기본 상태값(완료 후 후속 작업 전용)이며, oppd 병렬 실행 State의 열거형과 독립된다 (상세: oppd SKILL.md 참조).`

**R-3 갱신 — State Gate 자가 점검 프롬프트 (line 403)**:
- 현재 3번 항목: deprecated 상태값 나열 (`QA Gate 대기` / `PM Gate 대기` / `사용자 확인 대기`)
- 변경: 파이프라인 현황판 행 기반 확인으로 교체
  ```
  > 3. 파이프라인 현황판 테이블에서 현재 단계의 행이 올바른 상태값인가? (완료 행: ✅ / 진행 중 행: 🔄 / 미착수 행: ⬜) `상태:` 필드가 적절한 값인가? (진행 중 / 완료 / 추가작업중 / 추가작업완료)
  ```

**R-5 변경이력**:
- 새 행 추가: `| v3.7 | 2026-04-12 | §3 State 리팩토링 — opsdd 파이프라인 현황판 예시 제거(opsdd SKILL.md에 존재), 병렬 실행 State 제거(oppd SKILL.md/guide에 존재), State Gate 자가 점검 프롬프트 deprecated 상태값 갱신 (110) |`

#### opal-harness-interactive.md (Step 2)

**R-4 — 순서 강제 원칙 중복 제거**:
- 현재 §4 (lines 119-127):
  ```markdown
  ### 순서 강제 원칙

  파이프라인 현황판 테이블에서 현재 행보다 앞 행이 ✅ 또는 `-`가 아니면 현재 행을 진행할 수 없다.

  | 앞 행 상태 | 현재 행 진입 |
  |----------|------------|
  | ✅ 또는 - | 가능 |
  | ⬜ 또는 🔄 | **불가** — 앞 행 완료 후 진입 |
  | ❌ | **불가** — 에스컬레이션 해소 후 진입 |
  ```
- 변경:
  ```markdown
  ### 순서 강제 원칙

  공통 하네스 §3 "수행 순서 강제 원칙" 참조. 앞 행 상태별 진입 가능 여부는 아래 테이블을 따른다.

  | 앞 행 상태 | 현재 행 진입 |
  |----------|------------|
  | ✅ 또는 - | 가능 |
  | ⬜ 또는 🔄 | **불가** — 앞 행 완료 후 진입 |
  | ❌ | **불가** — 에스컬레이션 해소 후 진입 |
  ```
- **판단 근거**: 상세 테이블은 interactive §4에서 Gate Fail 공통 처리의 일부로 즉시 참조해야 하는 운용 테이블이므로 테이블 자체는 유지하되, 원칙의 출처를 §3 참조로 명시하여 원본 일원화를 달성한다. 원칙 서술 문장(`파이프라인 현황판 테이블에서 현재 행보다 앞 행이...`)을 참조 문구로 교체한다.

**R-5 변경이력**:
- 새 행 추가: `| v2.3 | 2026-04-12 | §4 순서 강제 원칙 — 직접 서술 → 공통 하네스 §3 참조로 교체 (원칙 일원화) (110) |`

#### oppd SKILL.md (Step 3)

- line 430 변경:
  - 현재: `- **Fallback**: worktree/Agent 도구 미지원 시 순차 실행으로 폴백 (하네스 "병렬 실행 State" 참조)`
  - 변경: `- **Fallback**: worktree/Agent 도구 미지원 시 순차 실행으로 폴백 (parallel-execution-guide.md §7 "STATE.md 갱신" 참조)`

#### parallel-execution-guide.md (Step 4)

- line 308 변경:
  - 현재: `머지 완료 시 STATE.md에 이력을 기록한다 (하네스 병렬 실행 State 구조 준수).`
  - 변경: `머지 완료 시 STATE.md에 이력을 기록한다 (§7-3 병렬 실행 State 구조 준수).`

- line 372 변경:
  - 현재: `하네스에 정의된 병렬 실행 State 구조를 따른다.`
  - 변경: `이 가이드(§7-2, §7-3)에 정의된 병렬 실행 State 구조를 따른다.`

## 3. 실행 체크리스트

> 총 4개 Step | Phase 2개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2 | 병렬 | 독립 파일 (opal-harness.md, opal-harness-interactive.md) |
> | 2     | 3, 4 | 병렬 | 독립 파일 (oppd SKILL.md, parallel-execution-guide.md) — Step 1 의존 (제거 완료 후 참조 갱신) |

### Step 1: opal-harness.md §3 정리 (R-1, R-2, R-3, R-5)
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  1. lines 233-273: `#### opsdd (opal-pilot-sdd) 파이프라인 현황판 행 예시` 서브섹션 전체 삭제 (R-1)
  2. lines 330-386: `### 병렬 실행 State` 서브섹션 전체 삭제 (R-2)
  3. line 180: `병렬 실행 State의 열거형과 독립된다` → `oppd 병렬 실행 State의 열거형과 독립된다 (상세: oppd SKILL.md 참조)` (R-2 후속)
  4. line 403: State Gate 자가 점검 프롬프트 3번 항목의 deprecated 상태값을 파이프라인 현황판 행 기반 확인으로 교체 (R-3)
  5. 변경이력에 v3.7 행 추가 (R-5)
  6. 삭제 후 빈 줄/구분선 정리
- **완료 기준**:
  - opal-harness.md에 `opsdd` 파이프라인 현황판 예시가 없다
  - opal-harness.md에 `### 병렬 실행 State` 섹션이 없다
  - State Gate 자가 점검 프롬프트에 `QA Gate 대기`, `PM Gate 대기`, `사용자 확인 대기` 문자열이 없다
  - 변경이력에 110번 태스크 기록이 있다
  - §번호(§0~§9)가 변경되지 않았다
- **테스트**: Grep으로 삭제 대상 문자열 부재 확인 + §번호 보존 확인
- **의존**: 없음

### Step 2: opal-harness-interactive.md §4 순서 강제 원칙 참조 교체 (R-4, R-5)
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**:
  1. §4 `### 순서 강제 원칙` 서브섹션의 원칙 서술 문장을 공통 하네스 §3 참조 문구로 교체 (상세 테이블은 유지)
  2. 변경이력에 v2.3 행 추가
- **완료 기준**:
  - `### 순서 강제 원칙` 아래 첫 문장에 "공통 하네스 §3" 참조가 명시되어 있다
  - 앞 행 상태 테이블(`✅ 또는 -`, `⬜ 또는 🔄`, `❌`)은 유지되어 있다
  - 변경이력에 110번 태스크 기록이 있다
- **테스트**: Read로 §4 순서 강제 원칙 섹션 확인 — 참조 문구 존재 + 테이블 유지
- **의존**: 없음

### Step 3: oppd SKILL.md 참조 경로 갱신 (R-2 후속)
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**:
  1. line 430: `하네스 "병렬 실행 State" 참조` → `parallel-execution-guide.md §7 "STATE.md 갱신" 참조`
- **완료 기준**:
  - oppd SKILL.md에 `하네스 "병렬 실행 State" 참조` 문자열이 없다
  - 대체 참조 경로(`parallel-execution-guide.md §7`)가 올바르다
- **테스트**: Grep으로 기존 문자열 부재 + 새 참조 존재 확인
- **의존**: Step 1 (하네스에서 병렬 실행 State 제거 완료 후)

### Step 4: parallel-execution-guide.md 참조 경로 갱신 (R-2 후속)
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md`
- **작업 내용**:
  1. line 308: `하네스 병렬 실행 State 구조 준수` → `§7-3 병렬 실행 State 구조 준수`
  2. line 372: `하네스에 정의된 병렬 실행 State 구조를 따른다` → `이 가이드(§7-2, §7-3)에 정의된 병렬 실행 State 구조를 따른다`
- **완료 기준**:
  - parallel-execution-guide.md에 `하네스 병렬 실행 State` 또는 `하네스에 정의된 병렬 실행 State` 문자열이 없다
  - 자체 참조 경로(§7-3, §7-2)가 올바르다
- **테스트**: Grep으로 기존 참조 문자열 부재 + 새 참조 존재 확인
- **의존**: Step 1 (하네스에서 병렬 실행 State 제거 완료 후)

## 4. QA 체크리스트

### 기능 테스트
- [x] R-1: opal-harness.md에 opsdd 파이프라인 현황판 예시가 없고, opsdd SKILL.md에 동일 정보가 존재한다
- [x] R-2: opal-harness.md에 `### 병렬 실행 State` 섹션이 없고, oppd SKILL.md + parallel-execution-guide.md에 동일 정보가 존재한다
- [x] R-3: State Gate 자가 점검 프롬프트에 `QA Gate 대기`, `PM Gate 대기`, `사용자 확인 대기` deprecated 상태값이 없다
- [x] R-4: opal-harness-interactive.md §4에서 순서 강제 원칙을 직접 서술하지 않고 공통 하네스 §3을 참조한다
- [x] R-5: opal-harness.md와 opal-harness-interactive.md 변경이력에 110번 태스크가 기록되어 있다

### 일관성 테스트
- [x] §번호(§0~§9)가 변경 전후 동일한가
- [x] 하네스를 참조하는 외부 문서(`하네스 §3 참조` 등)의 참조 경로가 여전히 유효한가
- [x] oppd SKILL.md와 parallel-execution-guide.md의 하네스 참조가 모두 자체 참조로 갱신되었는가
- [x] opal-harness.md line 180의 `병렬 실행 State` 주석이 갱신되었는가
- [x] 기존 오케스트레이터(opp/opds/opd/opwt/opsdd/oppd)의 `하네스 §3` 참조가 여전히 유효한가 (§3 번호 미변경이므로 유효)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 삭제 후 빈 줄/구분선이 깔끔하게 정리되었는가
- [x] 변경이력 행의 형식이 기존 행과 일관적인가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| oppd 참조 갱신 누락 시 런타임에 "하네스 병렬 실행 State" 참조 시도 → 섹션 미발견 | 중 — oppd 오케스트레이터 병렬 실행 시 혼란 | Step 3, 4에서 Grep으로 `하네스.*병렬 실행 State` 패턴 잔여 확인 |
| opal-harness.md line 180 주석 미갱신 시 독자 혼란 | 하 — 주석이므로 동작 영향 없음 | Step 1 작업 내용에 명시적으로 포함 |
| State Gate 자가 점검 프롬프트 교체 시 의미 변질 | 중 — PM이 잘못된 기준으로 점검 | 현행 파이프라인 현황판 운용 방식과 정확히 대응하는 문구로 교체 (§3 이벤트 테이블 기반) |
| interactive §4 테이블 제거 시 Gate Fail 처리 시 참조 누락 | 중 — PM이 앞 행 상태 확인 실패 가능 | 테이블은 유지하되, 원칙 출처만 §3 참조로 변경 (운용 테이블 보존) |

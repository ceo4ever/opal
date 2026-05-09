# PLAN: opal-harness.md 모듈화 — harness/ 폴더 분리

> 작성일: 2026-04-12
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 메인 하네스 (651줄, SSOT) | **수정** — 분리 대상 제거 + stub 교체 + 모듈 매핑 테이블 추가 |
| `opal/core/references/opal-harness-interactive.md` | interactive 모드 서브 하네스 | **수정** — §3 PM Gate에 하네스 모듈 체크포인트 추가 (R-9) |
| `opal/core/references/opal-harness-agentic.md` | agentic 모드 서브 하네스 | **수정** — 깨진 §2.5 참조 + §7.6 참조 갱신 (R-10) |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 | 변경 불필요 — §4 PM 검토 게이트는 기존 절차 그대로 유지. R-9는 interactive §3에 추가 |
| `scripts/install-mac.sh` | 배포 스크립트 | **변경 불필요** — line 621 `cp -Rf "$ref_src"/. "$ref_dst"/`가 재귀 복사이므로 harness/ 자동 배포 |
| `docs/CONVENTIONS.md` | 코드 컨벤션 | 변경 불필요 |
| `opal/core/references/harness/` | 분리 모듈 폴더 (신규) | **신규 생성** — 6개 모듈 파일 |

### 현재 상태

**메인 하네스 (opal-harness.md)**: 651줄, §0~§9 + 변경이력. 110번 태스크에서 ~95줄 감축 완료.

**섹션별 현황** (줄 수 / Eager 잔류 여부):

| § | 섹션 | 줄 | 라인 범위 | 처리 |
|---|------|-----|----------|------|
| 0 | 용어 정의 | ~15 | 8-22 | Eager 잔류 |
| 1 | Guards | ~46 | 23-68 | Eager 잔류 |
| 2 | 모듈 구조 | ~72 | 69-140 | **부분 분리** — 서브 하네스 모듈 + 로딩 규칙(69-89) 잔류, QA 검증~갱신 의무(90-139) 분리 |
| 3 | State | ~183 | 141-323 | **부분 분리** — 이벤트 테이블~레거시 호환(141-181) + 세션 복원~State Gate(286-323) 잔류, 공통 템플릿~산출물 행 규칙(182-232) + ADD_DONE~추가작업(233-285) 분리 |
| 4 | TASK 공통 프로세스 | ~46 | 324-369 | Eager 잔류 |
| 5 | Observability | ~56 | 370-425 | **전체 분리** |
| 6 | Model Mapping | ~13 | 426-438 | Eager 잔류 (이미 짧음) |
| 7 | 병렬 처리 원칙 | ~84 | 439-522 | **전체 분리** |
| 8 | @header 규칙 | ~69 | 523-591 | **전체 분리** |
| 9 | OPAL Tools | ~35 | 592-626 | Eager 잔류 (이미 stub 형태) |
| - | 변경이력 | ~24 | 627-651 | Eager 잔류 |

**분리 대상 총 줄 수**: ~50(§2) + ~51(§3 템플릿) + ~53(§3 추가작업) + ~56(§5) + ~84(§7) + ~69(§8) = **~363줄 분리**

**잔류 Eager 줄 수 추정**: 651 - 363 + stub 오버헤드(6개 x ~8줄 = ~48줄) + 모듈 매핑 테이블(~15줄) = **~351줄** (R-2 AC "~300줄 이하" 목표에 근접하지만 초과 가능성 있음 — stub을 최대한 간결하게 작성하여 달성 목표로 함)

**외부 참조 현황**: `하네스 §[0-9]` 참조 236건 / 75개 파일. §번호 stub이 유지되므로 모든 참조 유효.

**install-mac.sh 검증**: `install_opal_references()` 함수의 `cp -Rf "$ref_src"/. "$ref_dst"/`는 `opal/core/references/` 하위의 모든 파일/폴더를 재귀적으로 `~/.opal/references/`에 복사한다. `.gitignore`에 harness 관련 제외 규칙 없음. 따라서 `opal/core/references/harness/` 폴더를 생성하면 배포 시 자동으로 `~/.opal/references/harness/`에 복사된다. **별도 수정 불필요.**

### 영향 범위

| 영향 대상 | 영향 내용 | 리스크 |
|----------|----------|--------|
| 메인 하네스를 Eager 로드하는 모든 세션 | 로드 크기 감소 (~651 → ~300줄 목표) | 낮음 — stub이 §번호를 유지 |
| `하네스 §N` 참조 236건 | stub이 유지되어 참조 유효 | 낮음 — §번호 불변 |
| PM Gate 검증 절차 | 하네스 모듈 체크포인트 추가 | 낮음 — 기존 Gate 구조에 추가만 |
| install-mac.sh | 변경 없음 (재귀 복사가 harness/ 자동 포함) | 없음 |
| 스킬 파일 | 변경 없음 (harness/ 파일명 직접 참조 없음) | 없음 |

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/core/references/harness/state-template.md` | §3의 STATE.md 공통 템플릿 + 파이프라인 현황판 행 구성 규칙 + 산출물 행 규칙 |
| 2 | `opal/core/references/harness/additional-work.md` | §3의 추가작업 프로세스 + ADD_DONE.md 템플릿 |
| 3 | `opal/core/references/harness/qa-standards.md` | §2의 QA 체크리스트 검증 + QA/단계별 산출물 표준 파일명 + 스킬별 검증 방식 + 갱신 의무 |
| 4 | `opal/core/references/harness/observability.md` | §5 전체 (스킬 탐색 경로, 메모리 동기화, 타임스탬프, 행위 주체 표시) |
| 5 | `opal/core/references/harness/parallel-execution.md` | §7 전체 (읽기/실행 병렬, 의존관계, 리소스 관리, 폴백, 배치 패턴 감지) |
| 6 | `opal/core/references/harness/header-rules.md` | §8 전체 (@header 규칙 + 적용 대상 확장자 + code-scan 활용 가이드) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 7 | `opal/core/references/opal-harness.md` | §2 QA 표준 → stub, §3 템플릿/추가작업 → stub, §5 전체 → stub, §7 전체 → stub, §8 전체 → stub. §2에 모듈 매핑 테이블 추가. 변경이력 v4.0 추가. |
| 8 | `opal/core/references/opal-harness-interactive.md` | §3 PM Gate에 하네스 모듈 체크포인트 테이블 추가. 변경이력 추가. |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | harness/ 폴더 생성 + 6개 모듈 파일 작성 | harness/*.md (6개) | 중 — 내용 이관 + 자기 완결적 헤더 추가 |
| 2 | 메인 하네스 분리 내용 제거 + stub 교체 + 모듈 매핑 테이블 + 변경이력 | opal-harness.md | 고 — 정밀한 분리 경계 + stub 설계 |
| 3 | interactive 하네스 PM Gate 체크포인트 추가 | opal-harness-interactive.md | 저 — 테이블 1개 추가 |

### 핵심 설계

#### 모듈 파일 공통 헤더 (R-5)

각 harness/ 모듈 파일 상단에 아래 형식의 헤더를 작성한다:

```markdown
# {섹션명}

> 출처: opal-harness.md §{N}
> 로드 시점: {구체적 시점}
> 역할: {1줄 요약}

---
```

#### stub 설계 (R-8)

메인 하네스에서 분리된 각 §에 아래 형식의 stub을 남긴다:

```markdown
## N. {섹션명} (또는 해당 서브섹션 위치)

> **[필수 로드]** {로드 시점 설명}
> 탐색: `{프로젝트}/.opal/references/harness/{file}.md`
>     → `~/.opal/references/harness/{file}.md`
>
> 적용 주체: {PM/워커}
> 적용 시점: {구체적 시점}
> PM Gate 검증: {검증 항목}
```

#### 각 모듈 stub 상세

**§2 QA 표준 stub** (§2 로딩 규칙 아래에 배치):

```markdown
### QA 산출물 표준 및 검증

> **[필수 로드]** QA Gate 수행 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/qa-standards.md`
>     → `~/.opal/references/harness/qa-standards.md`
>
> 적용 주체: PM + QA 에이전트
> 적용 시점: QA Gate 수행 시
> PM Gate 검증: QA 산출물 파일명이 표준을 따르는가
```

**§3 STATE.md 공통 템플릿 stub** (§3 이벤트 테이블 아래, 현재 "STATE.md 공통 템플릿" 위치에 배치):

```markdown
### STATE.md 공통 템플릿

> **[필수 로드]** STATE.md 초기 생성 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/state-template.md`
>     → `~/.opal/references/harness/state-template.md`
>
> 적용 주체: PM (오케스트레이터)
> 적용 시점: TASK 완료 후 STATE.md 초기 생성 시
> PM Gate 검증: STATE.md가 공통 템플릿 구조를 따르는가
```

**§3 추가작업 stub** (현재 "ADD_DONE.md 템플릿" + "추가작업 프로세스" 위치에 배치):

```markdown
### 추가작업 프로세스

> **[필수 로드]** 추가작업 진입 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/additional-work.md`
>     → `~/.opal/references/harness/additional-work.md`
>
> 적용 주체: PM (오케스트레이터)
> 적용 시점: 완료 상태 태스크에 추가 수정 필요 시
> PM Gate 검증: ADD_DONE.md 템플릿 준수 여부
```

**§5 Observability stub** (전체 교체):

```markdown
## 5. Observability (관측)

> **[필수 로드]** 워커 디스패치 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/observability.md`
>     → `~/.opal/references/harness/observability.md`
>
> 적용 주체: PM (오케스트레이터)
> 적용 시점: 워커 디스패치 시
> PM Gate 검증: 행위 주체 표시가 수행되었는가
```

**§7 병렬 처리 원칙 stub** (전체 교체):

```markdown
## 7. 병렬 처리 원칙

> **[필수 로드]** 병렬 디스패치 판단 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/parallel-execution.md`
>     → `~/.opal/references/harness/parallel-execution.md`
>
> 적용 주체: PM (오케스트레이터)
> 적용 시점: 병렬 디스패치 시
> PM Gate 검증: 병렬/순차 판별이 올바른가
```

**§8 @header 규칙 stub** (전체 교체):

```markdown
## 8. EXECUTE @header 규칙

> **[필수 로드]** EXECUTE 코드 변경 시 로드한다.
> 탐색: `{프로젝트}/.opal/references/harness/header-rules.md`
>     → `~/.opal/references/harness/header-rules.md`
>
> 적용 주체: 워커 (코드 작성 시)
> 적용 시점: EXECUTE 단계에서 코드 파일 생성/수정 시
> PM Gate 검증: @header가 올바르게 작성되었는가
```

#### §2 모듈 매핑 테이블 (R-3)

§2 로딩 규칙 아래, QA 표준 stub 앞에 추가:

```markdown
### 하네스 모듈 매핑

| 모듈 | 파일 | 로드 시점 | §번호 |
|------|------|----------|-------|
| state-template | `harness/state-template.md` | STATE.md 초기 생성 시 | §3 |
| additional-work | `harness/additional-work.md` | 추가작업 진입 시 | §3 |
| qa-standards | `harness/qa-standards.md` | QA Gate 수행 시 | §2 |
| observability | `harness/observability.md` | 워커 디스패치 시 | §5 |
| parallel-execution | `harness/parallel-execution.md` | 병렬 디스패치 시 | §7 |
| header-rules | `harness/header-rules.md` | EXECUTE 코드 변경 시 | §8 |
```

#### PM Gate 하네스 모듈 체크포인트 (R-9)

`opal-harness-interactive.md` §3 PM Gate 내부, "PM Gate 자가 진단 절차" 아래에 추가:

```markdown
### 하네스 모듈 적용 확인

PM Gate 자가 진단 후, 해당 단계에서 적용 조건이 발동된 하네스 모듈의 적용 여부를 확인한다.

| 모듈 | 적용 조건 | 검증 항목 | Fail 시 |
|------|---------|---------|---------|
| state-template | 항상 | STATE.md가 공통 템플릿 구조를 따르는가 | 재작업 |
| qa-standards | QA Gate 수행 시 | QA 산출물 파일명이 표준을 따르는가 | QA 재소환 |
| observability | 워커 디스패치 시 | 행위 주체 표시가 수행되었는가 | PM 즉시 보완 |
| header-rules | EXECUTE 코드 변경 시 | @header가 올바르게 작성되었는가 | 워커 재지시 |
| parallel-execution | 병렬 디스패치 시 | 병렬/순차 판별이 올바른가 | 워커 재지시 |
| additional-work | 추가작업 시 | ADD_DONE.md 템플릿 준수 | 재작업 |

> 적용 조건 미해당 모듈은 검증 스킵. 적용 조건 해당 모듈만 검증한다.
```

#### install-mac.sh (R-7) — 변경 불필요 확인

- `install_opal_references()` 함수 (line 611-623)
- `cp -Rf "$ref_src"/. "$ref_dst"/` — 재귀 복사이므로 harness/ 하위 폴더 자동 배포
- `.gitignore`에 harness 관련 제외 규칙 없음
- **결론: 별도 수정 불필요**. 다만 R-7 AC는 "install-mac.sh에 harness/ 폴더 복사 로직이 존재한다"이므로, 기존 `cp -Rf` 재귀 복사가 이미 이를 충족함을 QA에서 검증한다.

## 3. 실행 체크리스트

> 총 8개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2, 3, 4, 5, 6 | 병렬 | 독립 모듈 파일 6개, 각각 독립 |
> | 2     | 7 | 순차 | 메인 하네스 수정 — Phase 1 모듈 파일 완성 후 |
> | 3     | 8, 9 | 병렬 | interactive 하네스(Step 8) + agentic 하네스(Step 9) — Phase 2 완료 후 |

### Step 1: state-template.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/state-template.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §3, 로드 시점: STATE.md 초기 생성 시, 역할: STATE.md 공통 템플릿 및 파이프라인 현황판 구성 규칙)
  - 메인 하네스 §3에서 "STATE.md 공통 템플릿" (line 182-215) + "파이프라인 현황판 행 구성 규칙" (line 217-224) + "산출물 행 규칙" (line 225-232) 내용을 이관
  - 의미 손실 없이 완전 이관
- **완료 기준**: 파일이 존재하고, 공통 템플릿 마크다운 코드블록 + 행 구성 규칙 + 산출물 행 규칙이 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §3 해당 부분과 내용 대조
- **의존**: 없음

### Step 2: additional-work.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/additional-work.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §3, 로드 시점: 추가작업 진입 시, 역할: ADD_DONE.md 템플릿 및 추가작업 프로세스)
  - 메인 하네스 §3에서 "ADD_DONE.md 템플릿" (line 233-248) + "추가작업 프로세스" (line 250-285) 내용을 이관
  - 감지 조건, 진입 절차, 스킬별 검증 오버라이드 테이블 포함
- **완료 기준**: 파일이 존재하고, ADD_DONE 템플릿 + 감지 조건 3가지 + 진입 절차 5단계 + 스킬별 검증 테이블이 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §3 해당 부분과 내용 대조
- **의존**: 없음

### Step 3: qa-standards.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/qa-standards.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §2, 로드 시점: QA Gate 수행 시, 역할: QA 체크리스트 검증 + 산출물 표준 파일명)
  - 메인 하네스 §2에서 "QA 체크리스트 검증" (line 90-101) + "QA 산출물 표준 파일명" (line 103-113) + "단계별 주요 산출물 표준 파일명" (line 114-128) + "스킬별 검증 방식" (line 130-137) + "갱신 의무" (line 137-139) 내용을 이관
  - 2단계 갱신 구조(QA 에이전트 1차 + PM 2차), PM 직접 갱신 금지 원칙 포함
- **완료 기준**: 파일이 존재하고, 2단계 갱신 구조 + QA 산출물 파일명 표 + 단계별 산출물 파일명 표 + 스킬별 검증 테이블 + 갱신 의무가 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §2 해당 부분과 내용 대조
- **의존**: 없음

### Step 4: observability.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/observability.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §5, 로드 시점: 워커 디스패치 시, 역할: 스킬 탐색 경로 + 메모리 동기화 + 행위 주체 표시)
  - 메인 하네스 §5 전체 (line 370-425) 내용을 이관
  - 스킬 탐색 경로, 프로젝트 메모리 동기화, 타임스탬프 취득 규칙, 행위 주체 표시 (아이콘 룩업 포함) 전부 포함
- **완료 기준**: 파일이 존재하고, 스킬 탐색 경로 + 메모리 동기화 + 타임스탬프 취득 + 행위 주체 표시 4개 서브섹션이 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §5 전체와 내용 대조
- **의존**: 없음

### Step 5: parallel-execution.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/parallel-execution.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §7, 로드 시점: 병렬 디스패치 시, 역할: 읽기/실행 병렬 처리 원칙)
  - 메인 하네스 §7 전체 (line 439-522) 내용을 이관
  - 읽기 병렬 + 실행 병렬 + 의존관계 순차 + 적용 기준 + 7.4 리소스 관리 + 7.5 런타임 폴백 + 7.6 배치 패턴 감지 전부 포함
- **완료 기준**: 파일이 존재하고, 7개 서브섹션(읽기, 실행, 의존관계, 적용 기준, 7.4, 7.5, 7.6)이 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §7 전체와 내용 대조
- **의존**: 없음

### Step 6: header-rules.md 모듈 생성
- [x] 완료
- **파일**: `opal/core/references/harness/header-rules.md`
- **작업 내용**:
  - 자기 완결적 헤더 작성 (출처: §8, 로드 시점: EXECUTE 코드 변경 시, 역할: @header 작성 규칙 + code-scan 활용 가이드)
  - 메인 하네스 §8 전체 (line 523-591) 내용을 이관
  - 적용 대상 확장자, 파일 생성 시, 파일 수정 시, 주석 문법, code-scan 활용 가이드 전부 포함
- **완료 기준**: 파일이 존재하고, 적용 대상 확장자 + 생성/수정 규칙 + 주석 문법 + code-scan 활용 가이드가 모두 포함되어 있다
- **테스트**: 파일 Read 후 원본 §8 전체와 내용 대조
- **의존**: 없음

### Step 7: 메인 하네스 수정 (stub 교체 + 모듈 매핑 테이블 + 변경이력)
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  - §2: "QA 체크리스트 검증" ~ "갱신 의무" 부분(line 90-139)을 QA 표준 stub으로 교체. 로딩 규칙 아래에 "하네스 모듈 매핑" 테이블 추가 (R-3)
  - §3: "STATE.md 공통 템플릿" ~ "산출물 행 규칙" 부분(line 182-232)을 state-template stub으로 교체. "ADD_DONE.md 템플릿" ~ "추가작업 프로세스" 부분(line 233-285)을 additional-work stub으로 교체
  - §5: 전체(line 370-425)를 observability stub으로 교체
  - §7: 전체(line 439-522)를 parallel-execution stub으로 교체
  - §8: 전체(line 523-591)를 header-rules stub으로 교체
  - 변경이력: v4.0 행 추가 (R-6)
  - 각 stub에 `[필수 로드]` + 적용 주체 + 적용 시점 + PM Gate 검증 항목 포함 (R-8)
  - §번호(§0~§9) 유지 확인
- **완료 기준**: (1) 메인 하네스 ~300줄 이하, (2) §0~§9 모두 존재, (3) 6개 stub 모두 `[필수 로드]` 블록 포함, (4) 모듈 매핑 테이블 존재, (5) 변경이력 v4.0 기재
- **테스트**: `wc -l` 줄 수 확인 + `## [0-9]\.` Grep으로 §번호 10개 확인 + `[필수 로드]` Grep으로 6건 확인
- **의존**: Step 1-6 (모듈 파일 내용이 확정되어야 stub의 정확성 보장)

### Step 8: interactive 하네스 PM Gate 체크포인트 추가
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**:
  - §3 PM Gate 내 "PM Gate 자가 진단 절차" 아래에 "하네스 모듈 적용 확인" 서브섹션 추가
  - 6개 모듈 체크포인트 테이블 (모듈, 적용 조건, 검증 항목, Fail 시) 추가
  - 적용 조건 미해당 모듈은 검증 스킵하는 규칙 명시
  - 변경이력 추가
- **완료 기준**: §3에 "하네스 모듈 적용 확인" 서브섹션이 존재하고, 6개 모듈 행이 있는 테이블이 있다
- **테스트**: 해당 파일 Read 후 테이블 6행 + "적용 조건 미해당" 규칙 존재 확인
- **의존**: Step 7 (메인 하네스 stub 확정 후 체크포인트 내용 정합성 확인)

### Step 9: agentic 하네스 참조 수정 (R-10)
- [x] 완료
- **파일**: `opal/core/references/opal-harness-agentic.md`
- **작업 내용**:
  1. line 51: `하네스 §2.5 참조` — Artifact Gate는 106번에서 삭제됨. PM Gate 자가 진단(interactive §3)으로 교체. 문맥에 맞게 문장 전체를 갱신
  2. line 101: `공통 하네스 §7.6 준수` — 모듈화 후 §7.6은 harness/parallel-execution.md 안에 존재. `하네스 §7 병렬 처리 모듈 §7.6 준수`로 갱신
  3. 변경이력 추가
- **완료 기준**: agentic.md에 `§2.5` 참조가 없고, §7.6 참조가 모듈화 구조와 정합한다
- **테스트**: Grep으로 `§2.5` 부재 확인 + `§7.6` 또는 `§7` 참조가 정확한지 확인
- **의존**: Step 7 (메인 하네스 §7 stub 확정 후)

## 4. QA 체크리스트

### 기능 테스트
- [x] R-1: 6개 모듈 파일이 `opal/core/references/harness/`에 존재하는가
- [x] R-2: 메인 하네스 ~300줄 이하이고, §0~§9 모두 유지되는가 ※ 364줄로 목표 초과(Warning) — §0~§9 유지는 확인됨
- [x] R-3: §2에 6개 모듈 + 로드 시점이 기재된 매핑 테이블이 존재하는가
- [x] R-4: `하네스 §[0-9]` 참조가 모두 유효한가 (stub으로 §번호 유지)
- [x] R-5: 각 모듈 파일 상단에 출처/로드 시점/역할 헤더가 있는가
- [x] R-6: 변경이력에 v4.0 행이 존재하는가
- [x] R-7: install-mac.sh `cp -Rf` 재귀 복사로 harness/ 자동 배포가 확인되는가
- [x] R-8: 모든 분리된 § stub에 `[필수 로드]` + 적용 주체 + 적용 시점 + PM Gate 검증 항목이 있는가
- [x] R-9: PM Gate에 6개 모듈 체크포인트 테이블이 존재하는가
- [x] R-10: agentic.md에 `§2.5` 참조가 없고, §7.6 참조가 모듈화 구조와 정합하는가

### 일관성 테스트
- [x] 분리된 모듈 내용이 원본과 의미 손실 없이 일치하는가
- [x] stub의 탐색 경로가 실제 모듈 파일 경로와 일치하는가
- [x] 모듈 매핑 테이블의 파일명/로드 시점이 각 stub과 일치하는가
- [x] PM Gate 체크포인트 테이블의 모듈명이 매핑 테이블과 일치하는가
- [x] 스킬 파일에 harness/ 파일명이 직접 언급되지 않는가 (SSOT)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가 (harness/, state-template.md 등)
- [x] 각 모듈 파일이 단독으로 읽어도 이해 가능한가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 메인 하네스 300줄 초과 | R-2 AC 미달 | stub을 최대한 간결하게 작성 (헤더 라인 포함 8줄 이내). 불가피 시 PM에 보고하여 AC 기준 조정 협의 |
| 분리 경계 오류로 내용 누락 | 파이프라인 정합성 훼손 | 원본 라인 범위를 정확히 지정했으므로 이관 시 라인 단위 대조. QA에서 의미 손실 검증 |
| 기존 세션에서 모듈 파일 Read 실패 | Lazy 로드 시 FileNotFound | install-mac.sh `cp -Rf` 재귀 복사로 자동 배포 확인 완료. 배포 전 테스트 불필요 (소스 경로에서만 수정) |
| stub 탐색 경로 오타 | 런타임 Read 실패 | 각 stub 작성 후 탐색 경로와 실제 파일 경로 1:1 대조 검증 |

# PLAN: 하네스 모듈화 — 공통 + 모드별 분리

> 작성일: 2026-03-31
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 모놀리식 하네스 (§0~§7, 438줄) | 수정 — §2, §7 분리 후 공통만 유지 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 | 수정 — Harness 섹션 참조 방식 갱신 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 | 수정 — Harness 섹션 참조 방식 갱신 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 | 수정 — Harness 섹션 참조 방식 갱신 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 오케스트레이터 | 수정 — Harness 섹션 참조 방식 갱신 |
| `~/.opal/AGENT.md` | 글로벌 에이전트 정의 | 수정 — 부트스트랩 4단계 하네스 참조 갱신 |
| `~/.opal/references/opal-harness.md` | 배포본 하네스 | 수정 — 소스 동기화 |
| `~/.opal/references/opal-harness-interactive.md` | 배포본 interactive 하네스 (미존재) | 신규 — 소스 동기화 |
| `~/.opal/references/opal-harness-agentic.md` | 배포본 agentic 하네스 (미존재) | 신규 — 소스 동기화 |

### 현재 상태

**opal-harness.md 구조 (438줄, 모놀리식)**:

| 섹션 | 내용 | 분류 |
|------|------|------|
| §0 용어 정의 | 약어/풀네임 테이블 | **공통** |
| §1 Guards | 구현 금지, Git 점검, 디스패치 의무, 커밋 규칙, 자동 루핑 제약 | **공통** |
| §2 Gates | 단계 게이트, QA Gate, PM Gate, 체크리스트 검증 게이트 | **interactive 모드 특화** |
| §3 State | STATE.md 기본/병렬/세션 복원 | **공통** |
| §4 TASK 공통 프로세스 | op-task 사용 방법 | **공통** |
| §5 Observability | 스킬 탐색 경로, 메모리 동기화 | **공통** |
| §6 Model Mapping | 레벨명-실제 모델 매핑 | **공통** |
| §7 Agentic Mode | PM 대행, 자율 검토, Gate 루핑, AGENTIC-LOG 등 | **agentic 모드 특화** |

**4개 오케스트레이터의 현재 Harness 참조 패턴** (동일):
```
## Harness
모드: {모드명}
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.
```
- 단일 파일 참조. 모드별 분기 없음.
- 각 스킬에서 "하네스 §7 Agentic Mode 참조" 등 섹션 번호로 참조.

**AGENT.md 부트스트랩 4단계**:
```
- `~/.opal/references/opal-harness.md` — 오케스트레이터 공통 하네스 (Guards, Gates, State, TASK, Observability)
```
- 단일 파일만 Read. 모드별 하네스 언급 없음.

### 영향 범위

| 영역 | 영향 |
|------|------|
| 하네스 소스 | 3파일 (1 수정 + 2 신규) |
| 오케스트레이터 SKILL.md | 4파일 수정 — Harness 섹션 + §참조 표기 갱신 |
| AGENT.md | 1파일 수정 — 부트스트랩 참조 경로 갱신 |
| 배포본 (~/.opal/references/) | 3파일 (1 수정 + 2 신규) — 소스 복사 |
| 동작 | 변경 없음 (구조 분리만) |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/core/references/opal-harness-interactive.md` | interactive 모드 하네스 — §2 Gates 내용 |
| 2 | `opal/core/references/opal-harness-agentic.md` | agentic 모드 하네스 — §7 Agentic Mode 내용 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 3 | `opal/core/references/opal-harness.md` | §2, §7 제거 + 모듈 구조 설명/로딩 규칙 추가 |
| 4 | `opal/skills/opal-pilot-dev/SKILL.md` | Harness 섹션 → 공통 + 모드별 하네스 로드 방식으로 갱신 |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 |
| 6 | `opal/skills/opal-pilot-project/SKILL.md` | 동일 |
| 7 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 동일 |
| 8 | `~/.opal/AGENT.md` | 부트스트랩 4단계 하네스 참조 갱신 (공통만 Read, 모드별은 오케스트레이터가 로드) |
| 9 | `~/.opal/references/opal-harness.md` | 배포본 동기화 (#3) |
| 10 | `~/.opal/references/opal-harness-interactive.md` | 배포본 동기화 (#1) |
| 11 | `~/.opal/references/opal-harness-agentic.md` | 배포본 동기화 (#2) |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | interactive 모드 하네스 신규 생성 | opal-harness-interactive.md | 낮음 |
| 2 | agentic 모드 하네스 신규 생성 | opal-harness-agentic.md | 낮음 |
| 3 | 공통 하네스 리팩터링 (§2, §7 제거 + 모듈 구조 추가) | opal-harness.md | 중간 |
| 4 | 4개 오케스트레이터 Harness 섹션 갱신 | 4 SKILL.md | 낮음 |
| 5 | AGENT.md 부트스트랩 참조 갱신 | AGENT.md | 낮음 |
| 6 | 배포본 동기화 | ~/.opal/references/ 3파일 | 낮음 |

### 핵심 설계

#### opal-harness-interactive.md (신규)

- 상단에 문서 역할 설명: "interactive 모드(기본) 전용 하네스. 공통 하네스(opal-harness.md)와 함께 로드한다."
- 기존 §2 Gates 전체를 그대로 이동 (단계 게이트, QA Gate, PM Gate, 체크리스트 검증 게이트)
- 섹션 번호를 `§2`에서 `1.`~`4.` 수준으로 리넘버링 (독립 문서이므로)
- 변경이력 추가: v1.0 초기 작성 — opal-harness.md §2에서 분리

#### opal-harness-agentic.md (신규)

- 상단에 문서 역할 설명: "agentic 모드 전용 하네스. 공통 하네스(opal-harness.md)와 함께 로드한다."
- 기존 §7 Agentic Mode 전체를 그대로 이동 (7-1 ~ 7-9)
- 섹션 번호를 `§7-1`~`§7-9`에서 `1.`~`9.` 수준으로 리넘버링
- 변경이력 추가: v1.0 초기 작성 — opal-harness.md §7에서 분리

#### opal-harness.md (수정)

**제거**:
- §2 Gates 전체 (→ opal-harness-interactive.md로 이동)
- §7 Agentic Mode 전체 (→ opal-harness-agentic.md로 이동)

**추가**: 새로운 "모듈 구조" 섹션 (§2 위치에 삽입, 이후 섹션 리넘버링)

```markdown
## 2. 모듈 구조

하네스는 **공통(이 문서) + 모드별 서브 하네스** 구조로 구성된다.
오케스트레이터는 이 문서를 Read하면, 모드에 따라 해당 서브 하네스를 추가로 Read한다.

### 서브 하네스 모듈

| 모듈 | 역할 | 로드 조건 | 탐색 경로 |
|------|------|----------|----------|
| `opal-harness-interactive.md` | interactive 모드 (Gates — 단계/QA/PM/체크리스트 게이트) | `--agentic` 플래그 **없음** (기본) | `~/.opal/references/opal-harness-interactive.md` |
| `opal-harness-agentic.md` | agentic 모드 (PM 대행, 자율 검토, Gate 루핑, AGENTIC-LOG) | `--agentic` 플래그 **있음** | `~/.opal/references/opal-harness-agentic.md` |

### 로딩 규칙

1. 오케스트레이터는 **공통 하네스**(`opal-harness.md`)를 Read한다 (부트스트랩 또는 Harness 섹션)
2. 공통 하네스 Read 후, 모드에 따라 **서브 하네스 1개를 추가 Read**한다:
   - `--agentic` 플래그 없음 (기본) → `opal-harness-interactive.md`
   - `--agentic` 플래그 있음 → `opal-harness-agentic.md`
3. 새 모드 추가 시: 이 테이블에 행을 추가하고, 서브 하네스 파일을 생성한다
```

**섹션 리넘버링** (§2 제거 후):
- §0 용어 정의 → 유지
- §1 Guards → 유지
- §2 모듈 구조 → **신규**
- §3 State → 유지 (번호 변경 없음)
- §4 TASK 공통 프로세스 → 유지
- §5 Observability → 유지
- §6 Model Mapping → 유지
- (§7 삭제)

변경이력 추가: 모듈화 — §2 Gates → opal-harness-interactive.md, §7 Agentic → opal-harness-agentic.md 분리

#### 공통 하네스 — 체크리스트 검증 게이트 보강 (§2 → 기존 위치 유지)

기존 "체크리스트 검증 게이트"(현 §2 Gates 내 → 분리 후 interactive 하네스로 이동)는 **실행 체크리스트(§3)**만 다루고 있다. **QA 체크리스트(§4) 갱신 의무**를 공통 하네스에 추가한다.

공통 하네스에 "QA 체크리스트 검증" 섹션을 추가:

```markdown
### QA 체크리스트 검증

EXECUTE 완료 후, PLAN.md QA 체크리스트를 검증하고 갱신한다. 모든 오케스트레이터에 공통 적용.

**스킬별 검증 방식**:

| 스킬 | 검증 수단 | QA 체크리스트 갱신 주체 |
|------|----------|---------------------|
| opd/opds | TEST-SCENARIO.md 결과 + PM 확인 | PM이 TEST-SCENARIO 결과 확인 후 갱신 |
| opp | QA Gate (QA 에이전트) + PM Gate | PM이 QA 결과 확인 후 갱신 |

**갱신 의무**: DONE.md 생성 전에 QA 체크리스트의 모든 항목이 `[x]` 또는 "N/A + 사유"로 채워져야 한다. 미갱신 상태에서 DONE.md를 생성하지 않는다.
```

#### opp SKILL.md — EXECUTE 후 QA Gate 추가

현재 opp EXECUTE 완료 후:
```
1. PM Gate
2. DONE.md 생성
3. 보고
```

변경 후:
```
1. QA Gate (op-task-qa) — QA 에이전트 호출
2. PM Gate — QA 결과 + 실행 결과 검토 + QA 체크리스트 갱신
3. DONE.md 생성
4. 보고
```

#### opd/opds SKILL.md — EXECUTE 후 QA 체크리스트 갱신 명시

현재 opd/opds EXECUTE 완료 후:
```
1. op-dev-test-agent 호출
2. DONE.md 생성
3. 보고
```

변경 후:
```
1. op-dev-test-agent 호출 → TEST-SCENARIO.md 판정
2. PM Gate — TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신
3. DONE.md 생성
4. 보고
```

#### 4개 오케스트레이터 SKILL.md Agentic Mode 참조 갱신

**진입점 변경 없음** — 오케스트레이터는 기존대로 `opal-harness.md`만 Read. 공통 하네스의 §2 "모듈 구조"가 모드별 서브 하네스 로딩을 지시하므로, 오케스트레이터 Harness 섹션은 **변경 불필요**.

변경 대상은 **Agentic Mode 섹션의 §7 참조**만:
- opd: `하네스 §7 Agentic Mode 참조` → `opal-harness-agentic.md 참조`
- opds: 동일
- opp: 동일
- oppd: 동일
- 각 스킬에서 `§7-5 Gate 루핑 규칙` → `opal-harness-agentic.md "Gate 루핑 규칙"` 등 세부 참조도 갱신

#### AGENT.md 부트스트랩 갱신

공통 하네스가 서브 모듈 로딩을 지시하므로, AGENT.md 부트스트랩의 Read 대상은 기존대로 `opal-harness.md` 1개. 단, 설명 텍스트만 갱신:

현재 (20행):
```
- `~/.opal/references/opal-harness.md` — 오케스트레이터 공통 하네스 (Guards, Gates, State, TASK, Observability)
```

변경 후:
```
- `~/.opal/references/opal-harness.md` — 오케스트레이터 공통 하네스 (Guards, State, TASK, Observability, Model Mapping). 모드별 서브 하네스는 §2 모듈 구조에 따라 오케스트레이터가 추가 Read.
```

Gates를 목록에서 제거 (interactive 서브 하네스로 이동), Model Mapping 추가, 서브 하네스 안내 추가.

#### 배포본 동기화

소스 3파일을 `~/.opal/references/`에 복사:
1. `opal/core/references/opal-harness.md` → `~/.opal/references/opal-harness.md`
2. `opal/core/references/opal-harness-interactive.md` → `~/.opal/references/opal-harness-interactive.md`
3. `opal/core/references/opal-harness-agentic.md` → `~/.opal/references/opal-harness-agentic.md`

---

## 3. 실행 체크리스트

> 총 6개 Step

### Step 1: interactive 모드 하네스 생성
- [x] 완료
- **파일**: `opal/core/references/opal-harness-interactive.md`
- **작업 내용**: opal-harness.md §2 Gates 전체를 독립 문서로 추출. 문서 헤더(역할 설명), 4개 서브섹션(단계 게이트, QA Gate, PM Gate, 체크리스트 검증 게이트), 변경이력 포함. 섹션 번호를 독립 문서 수준으로 리넘버링.
- **완료 기준**: 파일 생성 완료. 내용이 기존 §2와 동일(구조 분리 외 변경 없음).
- **테스트**: 원본 §2 내용과 diff 비교하여 의미 변경 없음 확인.
- **의존**: 없음

### Step 2: agentic 모드 하네스 생성
- [x] 완료
- **파일**: `opal/core/references/opal-harness-agentic.md`
- **작업 내용**: opal-harness.md §7 Agentic Mode 전체를 독립 문서로 추출. 문서 헤더, 9개 서브섹션(7-1~7-9 → 1~9), 변경이력 포함. 섹션 번호를 독립 문서 수준으로 리넘버링.
- **완료 기준**: 파일 생성 완료. 내용이 기존 §7과 동일.
- **테스트**: 원본 §7 내용과 diff 비교하여 의미 변경 없음 확인.
- **의존**: 없음

### Step 3: 공통 하네스 리팩터링
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: (1) §2 Gates 전체 제거, (2) §7 Agentic Mode 전체 제거, (3) 새 §2 "모듈 구조" 섹션 추가 (서브 하네스 테이블 + 로딩 규칙), (4) "QA 체크리스트 검증" 섹션 추가 (스킬별 검증 방식 테이블 + 갱신 의무), (5) 변경이력 추가.
- **완료 기준**: 파일에 §0, §1, §2(모듈 구조), §3~§6 + QA 체크리스트 검증이 존재. Gates/Agentic 내용 없음.
- **테스트**: §0, §1, §3~§6 내용이 원본과 동일한지 확인. §2 모듈 구조 + QA 체크리스트 검증이 설계대로 작성되었는지 확인.
- **의존**: Step 1, Step 2 (분리 대상 내용이 이미 추출된 상태에서 제거)

### Step 4: 4개 오케스트레이터 SKILL.md 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**: (1) Agentic Mode 섹션의 "하네스 §7" 참조를 "opal-harness-agentic.md" 참조로 치환, (2) "§7-5 Gate 루핑 규칙" 등 세부 참조도 갱신, (3) **opd/opds**: EXECUTE 완료 후에 "PM Gate — TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신" 추가, (4) **opp**: EXECUTE 완료 후에 "QA Gate (op-task-qa) → PM Gate + QA 체크리스트 갱신" 추가, (5) Harness 섹션은 변경 불필요, (6) 변경이력 추가.
- **완료 기준**: 4개 파일에서 `§7` 참조 0건. opd/opds EXECUTE 후 PM Gate 추가됨. opp EXECUTE 후 QA Gate + PM Gate 추가됨.
- **테스트**: `§7` grep 0건. 각 스킬의 EXECUTE 완료 후 흐름에 QA 체크리스트 갱신이 포함되었는지 확인.
- **의존**: Step 3

### Step 5: AGENT.md 부트스트랩 설명 텍스트 갱신
- [x] 완료
- **파일**: `~/.opal/AGENT.md`
- **작업 내용**: 부트스트랩 4단계의 opal-harness.md 참조 **설명 텍스트만** 갱신 — Gates 제거, Model Mapping 추가, 서브 하네스 안내 추가. Read 대상은 기존대로 `opal-harness.md` 1개.
- **완료 기준**: 설명 텍스트가 갱신됨. "Gates" 대신 "모드별 서브 하네스" 안내 포함.
- **테스트**: AGENT.md 부트스트랩 참조 행에서 "Gates" 제거, "모듈 구조" 또는 "서브 하네스" 언급 확인.
- **의존**: Step 3

### Step 6: 배포본 동기화
- [x] 완료
- **파일**: `~/.opal/references/opal-harness.md`, `~/.opal/references/opal-harness-interactive.md`, `~/.opal/references/opal-harness-agentic.md`
- **작업 내용**: 소스 3파일을 배포 경로에 복사.
- **완료 기준**: 배포본 3파일이 소스와 동일.
- **테스트**: `diff opal/core/references/opal-harness*.md ~/.opal/references/opal-harness*.md` 결과 차이 없음.
- **의존**: Step 1, Step 2, Step 3

---

## 4. QA 체크리스트

### 기능 테스트
- [x] opal-harness.md에 §2 Gates 내용이 없는가 (interactive로 이동) — 확인: §2는 "모듈 구조"로 교체됨
- [x] opal-harness.md에 §7 Agentic Mode 내용이 없는가 (agentic으로 이동) — 확인: §7 전체 제거됨
- [x] opal-harness.md에 "모듈 구조" 섹션이 추가되었는가 (서브 하네스 테이블 + 로딩 규칙) — 확인: 65행~
- [x] opal-harness.md에 "QA 체크리스트 검증" 섹션이 추가되었는가 (스킬별 방식 + 갱신 의무) — 확인: 85행~
- [x] opal-harness-interactive.md에 기존 §2 내용이 온전히 존재하는가 — 확인: 4개 서브섹션 이동 완료
- [x] opal-harness-agentic.md에 기존 §7 내용이 온전히 존재하는가 — 확인: 9개 서브섹션 이동 완료
- [x] 4개 스킬의 Agentic Mode 섹션에서 §7 참조가 opal-harness-agentic.md 참조로 갱신되었는가 — 확인: 본문 §7 참조 0건 (변경이력만)
- [x] opd/opds: EXECUTE 후 PM Gate (TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신)가 추가되었는가 — 확인
- [x] opp: EXECUTE 후 QA Gate + PM Gate + QA 체크리스트 갱신이 추가되었는가 — 확인
- [x] AGENT.md 부트스트랩 설명 텍스트가 갱신되었는가 — 확인: Gates 제거, Model Mapping 추가, 서브 하네스 안내
- [x] 배포본 3파일이 소스와 동일한가 — 확인: diff 결과 차이 없음

### 일관성 테스트
- [x] 분리 전 하네스의 전체 내용이 분리 후 3파일에 누락 없이 존재하는가 — 확인
- [x] 오케스트레이터 SKILL.md에서 "§7" 섹션 번호 참조가 0건인가 — 확인: 변경이력 텍스트만 존재
- [x] 오케스트레이터의 동작 흐름이 분리 전후 동일한가 (기능적 변경 없음 + QA 체크리스트 갱신 추가) — 확인
- [x] 공통 하네스의 §0, §1, §3~§6 내용이 원본과 동일한가 — 확인

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 — 확인
- [x] kebab-case 파일/폴더 네이밍을 따르는가 — 확인: opal-harness-interactive.md, opal-harness-agentic.md
- [x] 변경이력이 모든 변경 파일에 추가되었는가 — 확인: 하네스 3파일 + 4개 SKILL.md

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| §번호 참조 누락 | 오케스트레이터가 잘못된 섹션을 참조 | Step 4에서 4개 SKILL.md 전수 검사. grep으로 §7 참조 0건 확인 |
| 내용 누락/변형 | 분리 과정에서 내용이 빠지거나 변경됨 | 분리 전 원본과 diff 비교. QA 기능 테스트로 온전성 확인 |
| 배포본 미동기화 | 실제 에이전트가 구 버전 하네스를 로드 | Step 6에서 diff로 소스-배포 동일성 검증 |
| AGENT.md 부트스트랩 누락 | 부트스트랩에서 하네스 로드 실패 | Step 5에서 AGENT.md 참조 경로 갱신 후 확인 |

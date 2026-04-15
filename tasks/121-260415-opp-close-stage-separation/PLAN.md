# PLAN: 파이프라인 현황판 CLOSE 단계 분리

> 작성일: 2026-04-15
> 입력: TASK.md
> 출력: PLAN.md
> 버전: v2 (C안 + R-7 반영)

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/harness/state-template.md` | 파이프라인 현황판 행 구성 규칙 SSOT | **Yes** — CLOSE 단계 규칙 추가, "최종 단계 예외 규칙" 제거, CLOSE 진입 게이트 원칙 반영 |
| `opal/core/references/opal-harness.md` | §1 Guards + §3 이벤트 테이블 + 상태 전이 흐름 | **Yes** — §1 CLOSE 진입 게이트 Guard 신설(R-7) + §3 CLOSE 단계 이벤트 귀속 + 레거시 호환 원칙 |
| `opal/core/references/opal-harness-agentic.md` | §7 유지되는 규칙 | **Yes** — "CLOSE 진입 게이트" 행 추가 (R-7) |
| `opal/core/references/harness/additional-work.md` | 추가작업 프로세스 | **Yes** — CLOSE 재진입 개념 명시 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 치환값 | **Yes** — CLOSE 단계 행 분리 + EXECUTE 끝 State Gate/사용자 확인 추가 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 치환값 | **Yes** — CLOSE 단계 행 분리 + TEST 끝 State Gate/사용자 확인 추가 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 치환값 | **Yes** — CLOSE 단계 행 분리 + TEST 끝 State Gate/사용자 확인 추가 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 치환값 | **Yes** — CLOSE 단계 행 분리 + EXECUTE 끝 State Gate/사용자 확인 추가 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 치환값 | **Yes** — CLOSE 단계 + QA 끝 State Gate/사용자 확인 추가 + 단계 목록 갱신 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 치환값 | **Yes** — DONE→CLOSE 리네이밍 + 4행→2행 통일 (VERIFY의 State Gate/사용자 확인이 CLOSE 진입 게이트) |

### 현재 상태

#### state-template.md (L44-58)

현재 행 구성 규칙은 3가지 카테고리로 구분된다:
- **TASK 단계**: `작업`, `TASK.md 생성`, `사용자 확인` (Gate 없음)
- **일반 단계**: `작업`, `{산출물} 생성`, `QA Gate`, `{QA 산출물} 생성`, `State Gate`, `PM Gate`, `State Gate`, `사용자 확인`
- **최종 단계(EXECUTE/TEST)**: PM Gate 직후 `DONE.md 생성`, 이어서 `State Gate`, `사용자 확인`

"최종 단계" 예외 규칙이 별도로 존재하며, DONE.md 생성 행이 최종 단계 PM Gate 직후에 부착되는 구조다.

산출물 행 규칙 L58에도 `DONE.md 행: 최종 단계 PM Gate 직후, 사용자 확인 직전에 위치`로 명시.

→ **C안 적용 후**: "최종 단계 예외 규칙" 소멸. 모든 단계가 일반 단계 패턴(`... PM Gate → State Gate → 사용자 확인`)을 100% 준수. CLOSE 단계는 2행(`DONE.md 생성 / State Gate`)으로 구성되며, 직전 단계의 `사용자 확인`이 CLOSE 진입 게이트 역할.

#### opal-harness.md §1 Guards + §3 이벤트 테이블 (L124-139)

§1 Guards에는 현재 "구현 금지 원칙", "Gate 통과 원칙" 등이 정의되어 있으나 **CLOSE 진입 게이트 규칙은 없다**. R-7에 의해 "CLOSE 진입 게이트" 서브섹션 신설 필요.

이벤트 테이블에 `사용자 확인 완료`, `태스크 완료`, `추가작업 진입`, `추가작업 완료` 이벤트가 있으나 **단계 귀속이 없다** (이벤트와 단계의 연결이 암묵적). "상태: 필드 전이 흐름" (L145-151)에도 CLOSE 단계 언급이 없다.

레거시 호환 노트 (L153)가 기존 Gate 상태값 관련으로 존재하므로, CLOSE 레거시 호환 원칙도 여기에 추가 가능하다.

#### opal-harness-agentic.md §7 유지되는 규칙 (R-7 대상)

§7 "유지되는 규칙" 테이블에 기존 Guard 규칙(구현 금지, Gate 통과 등)이 "agentic 모드에서도 유지됨"으로 나열되어 있다. **CLOSE 진입 게이트 행이 없다**. R-7에 의해 "CLOSE 진입 게이트 — agentic 모드에서도 CLOSE 진입은 사용자 승인 필수" 행 추가 필요.

#### additional-work.md

"진입 절차" (L42-46)는 5단계:
1. STATE.md `완료` → `추가작업중`
2. 추가작업 수행
3. ADD_DONE.md 작성
4. 스킬별 검증
5. STATE.md `추가작업중` → `추가작업완료`

현재 CLOSE 단계 개념 없이 평면적 절차로 기술. ADD_DONE.md 생성이 CLOSE 재진입과 연결되지 않음.

#### 6개 SKILL.md 진행 현황 행 예시 분석

**opp** (opal-pilot-project): EXECUTE 단계 마지막 3행이 DONE.md 생성 / State Gate / 사용자 확인 (L117 #17, L118 #18, L119 #19). 단계 목록: `TASK / PLAN / EXECUTE`.

→ **C안 적용 후**: EXECUTE 끝에서 마감 3행 제거. PM Gate 후 `State Gate / 사용자 확인` 2행 신규 추가 (일반 단계 패턴 준수 = CLOSE 진입 게이트). CLOSE 2행(`DONE.md 생성 / State Gate`) 추가.

**opd** (opal-pilot-dev): TEST 단계 마지막 3행이 DONE.md 생성 / State Gate / 사용자 확인 (L183 #22, L184 #23, L185 #24). 단계 목록: `TASK / ANALYSIS / PLAN / EXECUTE / TEST`.

→ **C안 적용 후**: TEST 끝에서 마감 3행 제거. PM Gate 후 `State Gate / 사용자 확인` 2행 신규 추가. CLOSE 2행 추가.

**opds** (opal-pilot-dev-short): TEST 단계 마지막 3행이 DONE.md 생성 / State Gate / 사용자 확인 (L180 #16, L181 #17, L182 #18). 단계 목록: `TASK / PLAN / EXECUTE / TEST`.

→ **C안 적용 후**: 동일 패턴. TEST PM Gate 후 `State Gate / 사용자 확인` 추가 + CLOSE 2행.

**opdw** (opal-pilot-dev-wireframe): EXECUTE 단계 마지막 3행이 DONE.md 생성 / State Gate / 사용자 확인 (L103 #17, L104 #18, L105 #19). 단계 목록: `TASK / WIREFRAME / EXECUTE`.

→ **C안 적용 후**: EXECUTE PM Gate 후 `State Gate / 사용자 확인` 추가 + CLOSE 2행.

**opwt** (opal-pilot-write-tech): **진행 현황 행 예시 테이블 없음**. QA 단계 본문(L196, L201)에 `DONE.md를 생성한다`로 기술. 단계 목록: `TASK → ANALYSIS → PLAN → EXECUTE → QA`. 행 예시가 없으므로 CLOSE 단계를 QA 단계 본문의 DONE.md 부분에서 분리하고, `{단계 목록}`에 CLOSE를 추가하는 방식으로 처리. QA 끝에 `State Gate / 사용자 확인` 추가 필요.

**opsdd** (opal-pilot-sdd): 기존 `DONE` Phase가 독립 존재 (Phase 6, L257-264). 파이프라인 현황판 행 #34-#37이 DONE Phase에 해당 (`State Gate / DONE.md 생성 / State Gate / 사용자 확인`). 단계 목록: `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / DONE`.

→ **C안 적용 후**: DONE→CLOSE 리네이밍. 기존 4행(State Gate / DONE.md 생성 / State Gate / 사용자 확인)을 **2행**(DONE.md 생성 / State Gate)으로 통일. 이유: VERIFY Phase 끝에 이미 `State Gate / 사용자 확인`이 존재(L32-33)하므로 이것이 CLOSE 진입 게이트 역할. 기존 #34 첫 State Gate와 #37 사용자 확인은 중복 → 제거.

### 영향 범위

**직접 변경 (10개 파일)**:
1. `opal/core/references/harness/state-template.md` — 행 구성 규칙 변경 (CLOSE 단계 추가, 최종 단계 예외 제거, CLOSE 진입 게이트 원칙)
2. `opal/core/references/opal-harness.md` — §1 CLOSE 진입 게이트 Guard 신설(R-7) + §3 이벤트 테이블 + 상태 전이 흐름 + 레거시 호환 원칙
3. `opal/core/references/opal-harness-agentic.md` — §7 유지되는 규칙에 "CLOSE 진입 게이트" 행 추가 (R-7)
4. `opal/core/references/harness/additional-work.md` — CLOSE 재진입 원칙
5. `opal/skills/opal-pilot-project/SKILL.md` — 진행 현황 행 + 단계 목록 + STEP 3 EXECUTE 본문
6. `opal/skills/opal-pilot-dev/SKILL.md` — 진행 현황 행 + 단계 목록 + STEP 5 TEST 본문
7. `opal/skills/opal-pilot-dev-short/SKILL.md` — 진행 현황 행 + 단계 목록 + STEP 4 TEST 본문
8. `opal/skills/opal-pilot-dev-wireframe/SKILL.md` — 진행 현황 행 + 단계 목록 + STEP 3 EXECUTE 본문
9. `opal/skills/opal-pilot-write-tech/SKILL.md` — QA 단계 본문 + 단계 목록
10. `opal/skills/opal-pilot-sdd/SKILL.md` — DONE→CLOSE 리네이밍 + 4행→2행 통일 + 진행 현황 행 + 단계 목록 + Phase 6 본문

**간접 영향 (변경 불필요)**:
- 기존 tasks/ 폴더의 STATE.md 파일 — 레거시 호환 원칙에 의해 소급 변경 없음
- 120번 태스크 — 절대 건드리지 않음

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| - | 없음 | - |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/harness/state-template.md` | CLOSE 단계 공통 블록 규칙 추가 (2행: DONE.md 생성 / State Gate) + "최종 단계" 예외 규칙 제거 + 산출물 행 규칙 갱신 + CLOSE 진입 게이트 원칙 반영 |
| 2 | `opal/core/references/opal-harness.md` | §1 Guards에 "CLOSE 진입 게이트" 서브섹션 신설(R-7) + §3 이벤트 테이블 CLOSE 귀속 + 상태 전이 흐름 CLOSE 명시 + 레거시 호환 원칙 |
| 3 | `opal/core/references/opal-harness-agentic.md` | §7 유지되는 규칙 테이블에 "CLOSE 진입 게이트" 행 추가(R-7) |
| 4 | `opal/core/references/harness/additional-work.md` | CLOSE 재진입 원칙 + 진입 절차 재표현 |
| 5 | `opal/skills/opal-pilot-project/SKILL.md` | 단계 목록에 CLOSE 추가 + EXECUTE 마감 3행 제거 + EXECUTE 끝 State Gate/사용자 확인 2행 추가 + CLOSE 2행 추가 + STEP 본문/보고 형식 조정 |
| 6 | `opal/skills/opal-pilot-dev/SKILL.md` | 단계 목록에 CLOSE 추가 + TEST 마감 3행 제거 + TEST 끝 State Gate/사용자 확인 2행 추가 + CLOSE 2행 추가 + STEP 본문 조정 |
| 7 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 단계 목록에 CLOSE 추가 + TEST 마감 3행 제거 + TEST 끝 State Gate/사용자 확인 2행 추가 + CLOSE 2행 추가 + STEP 본문 조정 |
| 8 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 단계 목록에 CLOSE 추가 + EXECUTE 마감 3행 제거 + EXECUTE 끝 State Gate/사용자 확인 2행 추가 + CLOSE 2행 추가 + STEP 본문 조정 |
| 9 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 단계 목록에 CLOSE 추가 + QA 본문에서 DONE.md 분리 + QA 끝 State Gate/사용자 확인 추가 + CLOSE 관련 기술 추가 |
| 10 | `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 6 DONE→CLOSE 리네이밍 + 4행→2행 통일 + 단계 목록 갱신 + 진행 현황 행 갱신 + Phase 6 본문/요약 갱신 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | CLOSE 단계 행 구성 규칙 (SSOT) | state-template.md | 중 |
| 2 | §1 CLOSE 진입 게이트 Guard + §3 이벤트 테이블 + 상태 전이 + 레거시 호환 | opal-harness.md | 중 |
| 3 | §7 유지되는 규칙에 CLOSE 진입 게이트 행 추가 | opal-harness-agentic.md | 하 |
| 4 | 추가작업 CLOSE 재진입 | additional-work.md | 하 |
| 5 | opp 치환값 갱신 | opal-pilot-project/SKILL.md | 중 |
| 6 | opd 치환값 갱신 | opal-pilot-dev/SKILL.md | 중 |
| 7 | opds 치환값 갱신 | opal-pilot-dev-short/SKILL.md | 중 |
| 8 | opdw 치환값 갱신 | opal-pilot-dev-wireframe/SKILL.md | 중 |
| 9 | opwt 치환값 갱신 | opal-pilot-write-tech/SKILL.md | 중 |
| 10 | opsdd 치환값 갱신 | opal-pilot-sdd/SKILL.md | 중 |

### 핵심 설계

#### C안 핵심 원칙 (v2 신규)

**CLOSE 단계는 2행이다**:
```
| N   | CLOSE | DONE.md 생성 | ⬜ | - |
| N+1 | CLOSE | State Gate   | ⬜ | - |
```

- CLOSE 단계에 **"사용자 확인" 행 없음**
- 직전 단계(EXECUTE/TEST/QA/VERIFY)의 **"사용자 확인"이 CLOSE 진입 게이트** 역할

**각 SKILL.md의 최종 단계에 `State Gate + 사용자 확인` 2행을 신규 추가**:

기존 최종 단계의 마지막이 `PM Gate`까지였던 곳에 아래 2행을 추가하여 일반 단계 패턴을 100% 준수:
```
| N   | {최종단계} | State Gate   | ⬜ | - |
| N+1 | {최종단계} | 사용자 확인   | ⬜ | - |
```

이 `사용자 확인`이 곧 태스크 마감 승인이며, CLOSE 단계 진입을 허가하는 게이트다.

**보고 형식 (C안)**:

EXECUTE/TEST/QA/VERIFY 완료 보고:
```
📋 [{단계}] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {QA-{단계}.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

CLOSE 완료 보고 (사용자 확인 없이 자동 진행 후 마감):
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

#### state-template.md 변경 명세

**제거할 내용**:

L47 현재:
```
- 최종 단계(EXECUTE/TEST): PM Gate 직후 `DONE.md 생성`, 이어서 `State Gate`, `사용자 확인`
```

L58 현재:
```
6. DONE.md 행: 최종 단계 PM Gate 직후, 사용자 확인 직전에 위치
```

**추가할 내용**:

L47 교체 → CLOSE 단계 규칙:
```
- CLOSE 단계: 모든 파이프라인의 마지막 단계. `DONE.md 생성`, `State Gate` 순 (2행). Gate(QA/PM) 없음. 사용자 확인 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할.
```

L58 교체 → DONE.md 행 규칙을 CLOSE 귀속으로 변경:
```
6. DONE.md 행: CLOSE 단계의 첫 행에 위치
```

**CLOSE 진입 게이트 원칙** (R-7 연계, CLOSE 단계 규칙 서술 내부):
```
> **CLOSE 진입 게이트**: 사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다.
```

#### opal-harness.md 변경 명세

**§1 Guards — "CLOSE 진입 게이트" 서브섹션 신설** (R-7):
```markdown
### CLOSE 진입 게이트

사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다(다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외).
```

**§3 이벤트 테이블 변경** (L134, L137-139 영역):

현재 `사용자 확인 완료` 이벤트(L134)에 단계 귀속이 없다. `태스크 완료`(L137), `추가작업 진입`(L138), `추가작업 완료`(L139) 역시 단계 귀속 없음.

변경: 이벤트 테이블 내 설명 열에 CLOSE 귀속 명시:
- `태스크 완료` (L137): "CLOSE 단계 완료 시 발생"으로 보강
- `추가작업 진입/완료` (L138-139): "CLOSE 단계 재진입/완료"로 보강

**상태 전이 흐름 변경** (L147-151):

현재:
```
진행 중 → (Gate 통과) → 완료
완료 → 추가작업중 → 추가작업완료
```

변경:
```
진행 중 → (CLOSE 단계 완료) → 완료
완료 → 추가작업중(CLOSE 재진입) → 추가작업완료
```

**레거시 호환 원칙 추가** (L153 레거시 호환 노트 뒤에):

```
> **레거시 호환 (CLOSE 단계)**: 기존 STATE.md(CLOSE 단계 도입 전 생성)는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다. 기존 STATE.md의 "최종 단계에 부착된 마감 블록"은 레거시 구조로 유효하다.
```

#### opal-harness-agentic.md 변경 명세 (R-7 신규)

**§7 "유지되는 규칙" 테이블에 행 추가**:

```
| CLOSE 진입 게이트 | 사용자의 확인된 지시(`승인`/`확인`/`확인완료` 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 이 규칙은 유지 — 다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외. |
```

변경이력 행 추가.

#### additional-work.md 변경 명세

**"추가작업 프로세스" 서두에 원칙 추가**:

```
> **CLOSE 재진입 원칙**: 추가작업은 CLOSE 단계를 재진입하여 수행한다. ADD_DONE.md 생성 → State Gate는 CLOSE 단계의 마감 블록과 동일한 패턴을 따른다.
```

**진입 절차 변경** (L42-46):

현재:
```
1. STATE.md 상태를 `완료` → `추가작업중`으로 갱신
2. 추가작업 수행
3. ADD_DONE.md 작성 (DONE.md는 원본 완료 기록으로 보존, 수정 금지)
4. 스킬별 검증 수행 (아래 테이블 참조)
5. STATE.md 상태를 `추가작업중` → `추가작업완료`로 갱신
```

변경:
```
1. STATE.md 상태를 `완료` → `추가작업중`으로 갱신
2. 추가작업 수행
3. CLOSE 단계 재진입: ADD_DONE.md 작성 (DONE.md는 원본 완료 기록으로 보존, 수정 금지)
4. 스킬별 검증 수행 (아래 테이블 참조)
5. State Gate (STATE.md 갱신 확인)
6. 사용자 확인
7. STATE.md 상태를 `추가작업중` → `추가작업완료`로 갱신
```

> 기존 진입 절차 5단계에서 3단계에 "CLOSE 단계 재진입" 명시 + 5/6단계(State Gate + 사용자 확인)을 CLOSE 패턴으로 추가.

#### opp (opal-pilot-project) SKILL.md 변경 명세

**단계 목록** (L99): `TASK / PLAN / EXECUTE` → `TASK / PLAN / EXECUTE / CLOSE`

**Harness 모드** (L13): `Project Task (TASK → PLAN → EXECUTE)` → `Project Task (TASK → PLAN → EXECUTE → CLOSE)`

**STEP 3 EXECUTE 본문** (L73-88): EXECUTE 완료 후 절차에서 마감 블록 분리
- L77 "3. **모든 체크리스트 갱신 완료 확인 후** DONE.md 생성" → 제거 (CLOSE로 이동)
- L78 "4. 사용자에게 완료 보고" → CLOSE 단계로의 전이 보고로 변경

보고 형식 변경:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {QA-EXECUTE.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

**CLOSE 단계 섹션 신규 추가** (STEP 3 뒤):
```markdown
## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성
2. State Gate (하네스 §3 참조)
3. 완료 보고

보고 형식:
\```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
\```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.
```

**진행 현황 행 예시 변경**:

EXECUTE 단계에서 마감 3행(DONE.md 생성 / State Gate / 사용자 확인) 제거. PM Gate 후 `State Gate / 사용자 확인` 2행 신규 추가. CLOSE 2행 추가:

현재 (L104-125):
```
| 12 | EXECUTE | 작업 | ⬜ | - |
| 13 | EXECUTE | QA Gate | ⬜ | - |
| 14 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 15 | EXECUTE | State Gate | ⬜ | - |
| 16 | EXECUTE | PM Gate | ⬜ | - |
| 17 | EXECUTE | DONE.md 생성 | ⬜ | - |
| 18 | EXECUTE | State Gate | ⬜ | - |
| 19 | EXECUTE | 사용자 확인 | ⬜ | - |
```

변경:
```
| 12 | EXECUTE | 작업 | ⬜ | - |
| 13 | EXECUTE | QA Gate | ⬜ | - |
| 14 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 15 | EXECUTE | State Gate | ⬜ | - |
| 16 | EXECUTE | PM Gate | ⬜ | - |
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | 사용자 확인 | ⬜ | - |
| 19 | CLOSE   | DONE.md 생성 | ⬜ | - |
| 20 | CLOSE   | State Gate | ⬜ | - |
```

> EXECUTE에서 마감 3행(#17-19) 제거 → PM Gate(#16) 후 State Gate(#17) + 사용자 확인(#18) 추가 → CLOSE 2행(#19-20) 추가. 총 행수 19→20.

**Agentic Mode** (L149-155): 흐름도에 CLOSE 추가
```
TASK (PM 직접) → PLAN Gate → EXECUTE Gate → CLOSE
                  PM 자율 검토   PM 자율 검토   (사용자 승인 후 자동 진행)
```

#### opd (opal-pilot-dev) SKILL.md 변경 명세

**단계 목록** (L154): `TASK / ANALYSIS / PLAN / EXECUTE / TEST` → `TASK / ANALYSIS / PLAN / EXECUTE / TEST / CLOSE`

**Harness 모드** (L12): `Full Task (TASK → ANALYSIS → PLAN → EXECUTE → TEST)` → `Full Task (TASK → ANALYSIS → PLAN → EXECUTE → TEST → CLOSE)`

**STEP 5 TEST PASS 절차** (L128-129):
- `→ DONE.md 생성 (checkpoint-guide.md 참조)` → 제거 (CLOSE로 이동)
- `→ 사용자에게 완료 보고` → CLOSE 단계로의 전이 보고로 변경

**CLOSE 단계 섹션 신규 추가** (STEP 5 뒤):
```markdown
## STEP 6: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성 (checkpoint-guide.md 참조)
2. State Gate (하네스 §3 참조)
3. 완료 보고

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.
```

**진행 현황 행 예시 변경**:

TEST 단계에서 마감 3행 제거. PM Gate 후 State Gate / 사용자 확인 추가. CLOSE 2행 추가:

현재 TEST 마지막 (L181-185):
```
| 21 | TEST | PM Gate | ⬜ | - |
| 22 | TEST | DONE.md 생성 | ⬜ | - |
| 23 | TEST | State Gate | ⬜ | - |
| 24 | TEST | 사용자 확인 | ⬜ | - |
```

변경:
```
| 21 | TEST | PM Gate | ⬜ | - |
| 22 | TEST | State Gate | ⬜ | - |
| 23 | TEST | 사용자 확인 | ⬜ | - |
| 24 | CLOSE | DONE.md 생성 | ⬜ | - |
| 25 | CLOSE | State Gate | ⬜ | - |
```

> 총 행수 24→25.

**Agentic Mode**: 흐름도에 CLOSE 추가.

#### opds (opal-pilot-dev-short) SKILL.md 변경 명세

**단계 목록** (L158): `TASK / PLAN / EXECUTE / TEST` → `TASK / PLAN / EXECUTE / TEST / CLOSE`

**Harness 모드** (L13): `Short Task (TASK → PLAN → EXECUTE → TEST)` → `Short Task (TASK → PLAN → EXECUTE → TEST → CLOSE)`

**STEP 4 TEST PASS 절차** (L93-95):
- `→ DONE.md 생성` → 제거 (CLOSE로 이동)
- `→ 사용자에게 완료 보고` → CLOSE 단계로의 전이 보고로 변경

**CLOSE 단계 섹션 + 진행 현황 행**: opd와 동일 패턴.

현재 TEST 마지막 (L179-182):
```
| 15 | TEST | PM Gate | ⬜ | - |
| 16 | TEST | DONE.md 생성 | ⬜ | - |
| 17 | TEST | State Gate | ⬜ | - |
| 18 | TEST | 사용자 확인 | ⬜ | - |
```

변경:
```
| 15 | TEST | PM Gate | ⬜ | - |
| 16 | TEST | State Gate | ⬜ | - |
| 17 | TEST | 사용자 확인 | ⬜ | - |
| 18 | CLOSE | DONE.md 생성 | ⬜ | - |
| 19 | CLOSE | State Gate | ⬜ | - |
```

> 총 행수 18→19.

**Agentic Mode**: 흐름도에 CLOSE 추가.

#### opdw (opal-pilot-dev-wireframe) SKILL.md 변경 명세

**단계 목록** (L80): `TASK / WIREFRAME / EXECUTE` → `TASK / WIREFRAME / EXECUTE / CLOSE`

**Harness 모드** (L12): `Wireframe UI (TASK → WIREFRAME → EXECUTE)` → `Wireframe UI (TASK → WIREFRAME → EXECUTE → CLOSE)`

**STEP 3 EXECUTE 완료 후** (L70-72):
- "3. DONE.md 생성 → 사용자 완료 보고" → CLOSE 단계로의 전이 보고로 변경

**CLOSE 단계 섹션 + 진행 현황 행**: EXECUTE 마감 3행 제거. PM Gate 후 State Gate / 사용자 확인 추가. CLOSE 2행 추가.

현재 EXECUTE 마지막 (L103-105):
```
| 17 | EXECUTE | DONE.md 생성 | ⬜ | - |
| 18 | EXECUTE | State Gate | ⬜ | - |
| 19 | EXECUTE | 사용자 확인 | ⬜ | - |
```

변경:
```
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | 사용자 확인 | ⬜ | - |
| 19 | CLOSE   | DONE.md 생성 | ⬜ | - |
| 20 | CLOSE   | State Gate | ⬜ | - |
```

> PM Gate(#16) 이후에 State Gate(#17) + 사용자 확인(#18) 신규 추가. CLOSE 2행(#19-20). 총 행수 19→20.

**Agentic Mode**: 흐름도에 CLOSE 추가.

#### opwt (opal-pilot-write-tech) SKILL.md 변경 명세

**단계 목록** (L213): `TASK → ANALYSIS → PLAN → EXECUTE → QA` → `TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE` (모드에 따라 일부 생략 유지)

**QA 단계 본문** (L195-202):
- L196 "모든 항목이 `[x]` 또는 "N/A + 사유"로 채워진 후 DONE.md를 생성한다." → "모든 항목이 `[x]` 또는 "N/A + 사유"로 채워져야 한다."로 변경 (DONE.md 생성은 CLOSE로 이동)
- L201 "**Pass**: DONE.md 생성" → "**Pass**: CLOSE 단계로 전이"
- QA 단계 끝에 `State Gate / 사용자 확인` 2행 추가 (일반 단계 패턴 준수 = CLOSE 진입 게이트)

**CLOSE 단계 섹션 신규 추가** (QA 단계 뒤, STATE.md 네트워크 확장 앞):
```markdown
## CLOSE 단계

QA 최종 판정 Pass 후 태스크를 마감한다.

1. DONE.md 생성
2. State Gate (하네스 §3 참조)
3. 완료 보고

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.
```

> opwt는 진행 현황 행 예시 테이블이 없으므로 테이블 수정 불필요. 단계 목록 + 본문 수정만.

#### opsdd (opal-pilot-sdd) SKILL.md 변경 명세

**핵심**: opsdd는 이미 독립된 `DONE` Phase (Phase 6)를 가지고 있으므로, `DONE` → `CLOSE`로 **리네이밍** + **4행→2행 통일**이 핵심.

**단계 목록** (L273): `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / DONE` → `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE`

**Phase 6 제목** (L257): `## Phase 6: DONE` → `## Phase 6: CLOSE`

**Phase 6 본문** (L259-264): "최종 확인" 텍스트의 DONE 참조를 CLOSE로 조정. "4. DONE.md 생성" 은 유지 (DONE.md는 산출물명이므로 변경 불필요).

**6단계 파이프라인 요약** (L33-53): `Phase 6: DONE` → `Phase 6: CLOSE`. 설명 텍스트 내 "DONE" 참조를 "CLOSE"로 갱신.

**진행 현황 행 예시** (L329-332):

현재:
```
| 34 | DONE | State Gate | ⬜ | |
| 35 | DONE | DONE.md 생성 | ⬜ | |
| 36 | DONE | State Gate | ⬜ | |
| 37 | DONE | 사용자 확인 | ⬜ | |
```

변경:
```
| 34 | CLOSE | DONE.md 생성 | ⬜ | |
| 35 | CLOSE | State Gate | ⬜ | |
```

> opsdd VERIFY Phase 끝에 이미 `State Gate`(L32) + `사용자 확인`(L33)이 존재. 이것이 C안의 "CLOSE 진입 게이트" 역할. 따라서 기존 #34 첫 State Gate(중복)와 #37 사용자 확인(VERIFY에서 이미 수행)은 제거. 4행→2행 통일. 총 행수 37→35.

**Agentic Mode**: 흐름도의 "DONE" → "CLOSE" 리네이밍.

**STATE.md 구조 예시** (L280 내부): `Phase: {현재 Phase}` 설명에서 DONE → CLOSE 갱신.

---

## 3. 실행 체크리스트

> 총 11개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1    | 순차 | state-template.md SSOT |
> | 2     | 2, 3, 4 | 병렬 | opal-harness.md(R-7 포함), opal-harness-agentic.md(R-7), additional-work.md (독립 파일) |
> | 3     | 5, 6, 7, 8, 9, 10, 11 | 병렬 | 6개 SKILL.md + 변경이력 (독립 파일, Step 1 의존) |

### Step 1: state-template.md CLOSE 단계 규칙 추가

- [x] 완료
- **파일**: `opal/core/references/harness/state-template.md`
- **작업 내용**:
  1. L47 "최종 단계(EXECUTE/TEST)" 예외 규칙을 **삭제**하고, 아래로 교체:
     ```
     - CLOSE 단계: 모든 파이프라인의 마지막 단계. `DONE.md 생성`, `State Gate` 순 (2행). Gate(QA/PM) 없음. 사용자 확인 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할.
     ```
  2. L58 "DONE.md 행" 규칙을 아래로 교체:
     ```
     6. DONE.md 행: CLOSE 단계의 첫 행에 위치
     ```
  3. CLOSE 진입 게이트 원칙 서술 추가 (R-7 연계):
     ```
     > **CLOSE 진입 게이트**: 사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다.
     ```
  4. 변경이력 테이블에 행 추가 (신규 버전, 태스크 121 참조)
- **완료 기준**: state-template.md에 "CLOSE 단계" 규칙이 존재하고 2행 구성(DONE.md 생성 / State Gate)으로 명시됨. "최종 단계(EXECUTE/TEST)" 문구가 제거됨. CLOSE 진입 게이트 원칙이 서술됨.
- **테스트**: Grep으로 "최종 단계" 문구 부재 확인 + "CLOSE 단계" 문구 존재 확인 + "CLOSE 진입 게이트" 존재 확인
- **의존**: 없음

### Step 2: opal-harness.md §1 CLOSE 진입 게이트 Guard + §3 이벤트 테이블 + 상태 전이 + 레거시 호환

- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  1. §1 Guards에 "CLOSE 진입 게이트" 서브섹션 신설 (R-7):
     ```
     ### CLOSE 진입 게이트
     사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가.
     이 규칙은 agentic 모드에서도 유지된다(다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외).
     ```
  2. §3 이벤트 테이블에서 `태스크 완료`(L137) 행의 설명을 보강하여 CLOSE 단계 귀속 명시
  3. `추가작업 진입`(L138), `추가작업 완료`(L139) 행에 "CLOSE 재진입" 개념 명시
  4. "상태: 필드 전이 흐름" (L147-151) 코드 블록에 CLOSE 단계 언급 추가
  5. L153 레거시 호환 노트 뒤에 CLOSE 레거시 호환 원칙 추가:
     ```
     > **레거시 호환 (CLOSE 단계)**: 기존 STATE.md(CLOSE 단계 도입 전 생성)는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다.
     ```
  6. 변경이력 테이블에 행 추가
- **완료 기준**: §1에 "CLOSE 진입 게이트" Guard 존재. 이벤트 테이블에서 `태스크 완료 / 추가작업 진입 / 추가작업 완료`가 CLOSE와 연관 기술됨. 상태 전이 흐름에 CLOSE 언급. 레거시 호환 원칙 존재.
- **테스트**: Read로 §1 Guards + §3 해당 섹션 확인
- **의존**: Step 1 (SSOT 확정 후 참조)

### Step 3: opal-harness-agentic.md §7 CLOSE 진입 게이트 행 추가 (R-7)

- [x] 완료
- **파일**: `opal/core/references/opal-harness-agentic.md`
- **작업 내용**:
  1. §7 "유지되는 규칙" 테이블에 "CLOSE 진입 게이트" 행 추가:
     ```
     | CLOSE 진입 게이트 | 사용자의 확인된 지시(승인/확인/확인완료 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 유지 — 다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외. |
     ```
  2. 변경이력 테이블에 행 추가 (태스크 121 참조)
- **완료 기준**: §7 유지되는 규칙 테이블에 "CLOSE 진입 게이트" 행이 존재하며 "agentic 모드에서도 CLOSE 진입은 사용자 승인 필수"임이 명시됨.
- **테스트**: Read로 §7 테이블 확인
- **의존**: Step 1 (SSOT 확정 후 참조)

### Step 4: additional-work.md CLOSE 재진입

- [x] 완료
- **파일**: `opal/core/references/harness/additional-work.md`
- **작업 내용**:
  1. "추가작업 프로세스" 서두(L26-28 부근)에 CLOSE 재진입 원칙 블록쿼트 추가
  2. 진입 절차(L42-46)에서 3단계에 "CLOSE 단계 재진입" 명시, 5/6단계(State Gate + 사용자 확인) 추가
  3. 변경이력 테이블이 없으면 하단에 추가 (현재 없음 — 신규 생성)
- **완료 기준**: "CLOSE 재진입" 원칙이 명시됨. 진입 절차에 State Gate + 사용자 확인이 CLOSE 패턴으로 포함됨.
- **테스트**: Read로 진입 절차 확인
- **의존**: Step 1 (SSOT 확정 후 참조)

### Step 5: opp SKILL.md CLOSE 단계 분리

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**:
  1. Harness 모드(L13): 단계에 CLOSE 추가
  2. 단계 목록(L99): `TASK / PLAN / EXECUTE` → `TASK / PLAN / EXECUTE / CLOSE`
  3. STEP 3 EXECUTE 본문(L73-88): DONE.md 생성 제거(CLOSE로 이동). 보고 형식을 C안으로 변경: `📋 [EXECUTE] 완료 보고 ... 다음 단계(CLOSE)로 넘어갈까요?`
  4. STEP 4: CLOSE 섹션 신규 추가 (EXECUTE 뒤, STATE.md 도메인 치환값 앞). 보고 형식: `✅ [CLOSE] 태스크 완료 ... 태스크가 완료되었습니다.`
  5. 진행 현황 행 예시: EXECUTE 마감 3행(DONE.md 생성/State Gate/사용자 확인) 제거 + PM Gate 후 State Gate/사용자 확인 2행 신규 추가 + CLOSE 2행(DONE.md 생성/State Gate) 추가 (총 행수 19→20)
  6. "추가작업" 참조를 STEP 3에서 STEP 4(CLOSE)로 이동
  7. Agentic Mode 흐름도에 CLOSE 추가
  8. 변경이력 행 추가
- **완료 기준**: 단계 목록에 CLOSE 포함. EXECUTE 단계에 DONE.md 행 없고 State Gate/사용자 확인 행 있음. CLOSE 단계 2행(DONE.md 생성/State Gate)이 진행 현황 마지막에 존재. STEP 4: CLOSE 섹션 존재.
- **테스트**: Grep으로 진행 현황 행 예시에서 CLOSE 단계 행 확인 + EXECUTE 단계에 DONE.md 행 부재 확인 + CLOSE에 사용자 확인 행 부재 확인
- **의존**: Step 1

### Step 6: opd SKILL.md CLOSE 단계 분리

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  1. Harness 모드(L12): 단계에 CLOSE 추가
  2. 단계 목록(L154): CLOSE 추가
  3. STEP 5 TEST PASS 절차: DONE.md 생성/완료 보고를 CLOSE로 이동. 보고 형식을 C안으로 변경.
  4. STEP 6: CLOSE 섹션 신규 추가
  5. 진행 현황 행 예시: TEST 마감 3행 제거 + PM Gate 후 State Gate/사용자 확인 2행 신규 추가 + CLOSE 2행 추가 (총 행수 24→25)
  6. "추가작업" 참조를 STEP 5에서 STEP 6(CLOSE)로 이동
  7. Agentic Mode 흐름도에 CLOSE 추가
  8. 변경이력 행 추가
- **완료 기준**: 단계 목록에 CLOSE 포함. TEST 단계에 DONE.md 행 없고 State Gate/사용자 확인 행 있음. CLOSE 단계 2행 존재. STEP 6: CLOSE 섹션 존재.
- **테스트**: Grep으로 확인
- **의존**: Step 1

### Step 7: opds SKILL.md CLOSE 단계 분리

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**:
  1. Harness 모드(L13): 단계에 CLOSE 추가
  2. 단계 목록(L158): CLOSE 추가
  3. STEP 4 TEST PASS 절차: DONE.md 생성/완료 보고를 CLOSE로 이동. 보고 형식을 C안으로 변경.
  4. STEP 5: CLOSE 섹션 신규 추가
  5. 진행 현황 행 예시: TEST 마감 3행 제거 + PM Gate 후 State Gate/사용자 확인 2행 신규 추가 + CLOSE 2행 추가 (총 행수 18→19)
  6. "추가작업" 참조를 STEP 4에서 STEP 5(CLOSE)로 이동
  7. Agentic Mode 흐름도에 CLOSE 추가
  8. 변경이력 행 추가
- **완료 기준**: 단계 목록에 CLOSE 포함. TEST 단계에 DONE.md 행 없고 State Gate/사용자 확인 행 있음. CLOSE 단계 2행 존재.
- **테스트**: Grep으로 확인
- **의존**: Step 1

### Step 8: opdw SKILL.md CLOSE 단계 분리

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**:
  1. Harness 모드(L12): 단계에 CLOSE 추가
  2. 단계 목록(L80): CLOSE 추가
  3. STEP 3 EXECUTE 완료 후: DONE.md 생성을 CLOSE로 이동. 보고 형식을 C안으로 변경.
  4. STEP 4: CLOSE 섹션 신규 추가
  5. 진행 현황 행 예시: EXECUTE 마감 3행 제거 + PM Gate 후 State Gate/사용자 확인 2행 신규 추가 + CLOSE 2행 추가 (총 행수 19→20)
  6. Agentic Mode 흐름도에 CLOSE 추가
  7. 변경이력 행 추가
- **완료 기준**: 단계 목록에 CLOSE 포함. EXECUTE 단계에 DONE.md 행 없고 State Gate/사용자 확인 행 있음. CLOSE 단계 2행 존재.
- **테스트**: Grep으로 확인
- **의존**: Step 1

### Step 9: opwt SKILL.md CLOSE 단계 분리

- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **작업 내용**:
  1. 단계 목록(L213): `TASK → ANALYSIS → PLAN → EXECUTE → QA` → `TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE`
  2. QA 단계 본문(L196): DONE.md 생성 문구를 QA에서 분리 (CLOSE로 이동)
  3. QA PM 최종 판정(L201): "Pass: DONE.md 생성" → "Pass: CLOSE 단계로 전이"
  4. QA 단계 끝에 `State Gate / 사용자 확인` 관련 기술 추가 (CLOSE 진입 게이트)
  5. CLOSE 단계 섹션 신규 추가 (QA 단계 뒤)
  6. "추가작업" 참조를 QA에서 CLOSE로 이동
  7. 변경이력 행 추가
- **완료 기준**: 단계 목록에 CLOSE 포함. QA 단계 본문에 DONE.md 생성이 제거됨. QA 끝에 사용자 확인 관련 기술 존재. CLOSE 단계 섹션 존재.
- **테스트**: Read로 QA 단계 + CLOSE 단계 확인
- **의존**: Step 1

### Step 10: opsdd SKILL.md DONE→CLOSE 리네이밍 + 4행→2행 통일

- [x] 완료
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**:
  1. 단계 목록(L273): `DONE` → `CLOSE`
  2. Phase 6 제목(L257): `Phase 6: DONE` → `Phase 6: CLOSE`
  3. Phase 6 본문(L259-264): 텍스트 내 단계명 DONE→CLOSE 갱신 (DONE.md 산출물명은 유지)
  4. 6단계 파이프라인 요약(L33-53): `Phase 6: DONE` → `Phase 6: CLOSE`, 설명 갱신
  5. 진행 현황 행 예시(L329-332): 4행(`State Gate / DONE.md 생성 / State Gate / 사용자 확인`) → **2행**(`DONE.md 생성 / State Gate`)으로 통일. VERIFY Phase 끝(L32-33)의 `State Gate + 사용자 확인`이 CLOSE 진입 게이트이므로 기존 #34 첫 State Gate와 #37 사용자 확인은 중복 제거. 총 행수 37→35.
  6. STATE.md 구조 예시 내 DONE 참조 → CLOSE 갱신
  7. Agentic Mode 흐름도: DONE→CLOSE 갱신
  8. 변경이력 행 추가
- **완료 기준**: 단계명이 모두 CLOSE로 변경됨 (DONE.md 산출물명은 유지). 진행 현황 행이 **2행**으로 통일. 파이프라인 요약이 CLOSE로 갱신.
- **테스트**: Grep으로 "| DONE |" 패턴 부재 확인 (단계명으로서) + "| CLOSE |" 존재 확인 + CLOSE 행이 정확히 2행(DONE.md 생성 / State Gate)인지 확인
- **의존**: Step 1

### Step 11: 변경이력 일괄 확인

- [x] 완료
- **파일**: 10개 변경 파일 전체
- **작업 내용**: 각 파일의 변경이력 테이블에 신규 버전 행이 추가되었는지 일괄 확인. 태스크 번호 121 참조. 일시 형식: `YYYY-MM-DD HH:mm` (KST) 또는 기존 파일의 형식과 일치.
  - state-template.md: 변경이력 없음 → 신규 추가 불필요 (현재 변경이력 테이블 없음 — 확인 필요)
  - opal-harness.md: 기존 v4.0까지 존재 → v4.1 추가
  - opal-harness-agentic.md: 기존 최신 버전 확인 후 +0.1 추가
  - additional-work.md: 변경이력 없음 → 신규 변경이력 섹션 추가
  - 6개 SKILL.md: 각 최신 버전 +0.1 추가
- **완료 기준**: 변경된 모든 파일(10개)에 태스크 121 참조 변경이력 행 존재.
- **테스트**: 각 파일 하단 Read로 변경이력 확인
- **의존**: Step 1~10

---

## 4. QA 체크리스트

### 기능 테스트

- [x] **R-1**: state-template.md에 "CLOSE 단계" 규칙이 존재하고, "최종 단계(EXECUTE/TEST)" 예외 규칙이 완전히 제거되었는가
- [x] **R-1**: CLOSE 단계의 **2행** 구성(DONE.md 생성 / State Gate)이 state-template.md에 명시되어 있는가 (사용자 확인 행 없음)
- [x] **R-1**: 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할임이 state-template.md에 서술되어 있는가
- [x] **R-2**: opal-harness.md §3 이벤트 테이블에서 `태스크 완료 / 추가작업 진입 / 추가작업 완료` 이벤트가 CLOSE 단계와 연관 기술되어 있는가
- [x] **R-2**: 상태 전이 흐름에 CLOSE 단계가 종료 단계로 명시되어 있는가
- [x] **R-3**: 6개 SKILL.md 모두 `단계 목록`에 `CLOSE`가 포함되어 있는가 (opp, opd, opds, opdw, opwt, opsdd)
- [x] **R-3 opp/opd/opds/opdw**: 진행 현황 행 예시에서 기존 최종 단계 끝에 `State Gate / 사용자 확인` 2행이 추가되고, CLOSE 단계 **2행**(DONE.md 생성 / State Gate)이 존재하는가
- [x] **R-3 opwt**: QA 단계 본문에서 DONE.md 생성이 제거되고, QA 끝 사용자 확인 기술이 존재하고, CLOSE 단계 섹션이 신설되어 있는가
- [x] **R-3 opsdd**: Phase 6이 DONE→CLOSE로 리네이밍되고, 진행 현황 행이 4행→2행으로 통일되었는가
- [x] **R-4**: additional-work.md에 "추가작업은 CLOSE 단계를 재진입한다" 원칙이 명시되어 있는가
- [x] **R-4**: 진입 절차에 State Gate + 사용자 확인이 CLOSE 패턴으로 포함되어 있는가
- [x] **R-5**: 레거시 호환 원칙("기존 STATE.md는 소급 변경하지 않는다")이 opal-harness.md §3에 존재하는가
- [x] **R-6**: 변경된 모든 파일(**10개**)의 변경이력 테이블에 태스크 121 참조 행이 추가되어 있는가
- [x] **R-7**: opal-harness.md §1 Guards에 "CLOSE 진입 게이트" 서브섹션이 존재하고, "사용자의 확인된 지시가 없으면 CLOSE 진입 불가" 규칙이 명시되어 있는가
- [x] **R-7**: state-template.md CLOSE 단계 규칙에 "CLOSE 진입 게이트" 원칙이 서술되어 있는가
- [x] **R-7**: opal-harness-agentic.md §7 유지되는 규칙 테이블에 "CLOSE 진입 게이트" 행이 추가되어 "agentic 모드에서도 CLOSE 진입은 사용자 승인 필수"임이 명시되어 있는가

### 일관성 테스트

- [x] 5개 SKILL.md(opp, opd, opds, opdw, opsdd)의 CLOSE 단계 구성이 동일한가 (**2행**: DONE.md 생성 / State Gate)
- [x] 5개 SKILL.md의 CLOSE 단계 행 번호가 각 스킬의 이전 단계 마지막 행 +1로 연속되는가
- [x] 이전 최종 단계(EXECUTE/TEST/QA/VERIFY)에서 DONE.md 생성 행이 완전히 제거되었는가
- [x] 이전 최종 단계 끝에 `State Gate / 사용자 확인` 2행이 추가되었는가 (일반 단계 패턴 준수)
- [x] opp/opdw의 EXECUTE 단계에서 "추가작업" 참조가 제거되고 CLOSE로 이동되었는가
- [x] opd/opds의 TEST 단계에서 "추가작업" 참조가 제거되고 CLOSE로 이동되었는가
- [x] opwt의 QA 단계에서 "추가작업" 참조가 제거되고 CLOSE로 이동되었는가
- [x] Agentic Mode 흐름도에 CLOSE가 모든 6개 SKILL.md에서 추가되었는가
- [x] state-template.md의 CLOSE 규칙(2행)과 6개 SKILL.md의 CLOSE 행 구성이 일치하는가
- [x] R-7 CLOSE 진입 게이트 규칙이 3개 문서(opal-harness.md, state-template.md, opal-harness-agentic.md)에서 일관되게 서술되어 있는가
- [x] CLOSE 완료 보고 형식과 EXECUTE/TEST/QA/VERIFY 완료 보고 형식이 C안 지정대로 구분되어 있는가

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 기존 문서의 톤/구조와 일관된 스타일로 작성되었는가
- [x] "최종 단계 예외 규칙" 문구가 state-template.md에서 실제로 사라졌는가 (Grep 검증)
- [x] DONE.md 산출물명과 CLOSE 단계명이 혼동 없이 구분되어 기술되어 있는가 (특히 opsdd)
- [x] 변경이력 일시 형식이 `YYYY-MM-DD HH:mm` (KST) 또는 기존 파일의 형식(날짜만)과 일치하는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 레거시 STATE.md 호환성 깨짐 | 진행 중인 태스크의 세션 복원 실패 | R-5 레거시 호환 원칙으로 소급 변경 금지. 기존 STATE.md 구조 그대로 유효. |
| 120번 태스크와의 충돌 | 다른 알투가 작업 중인 파일 수정 | 120번 태스크 폴더 절대 불가침. 스킬 SKILL.md 수정은 120번 STATE.md에 영향 없음 (SKILL.md는 신규 태스크 생성 시만 적용). |
| 6개 SKILL.md 간 CLOSE 표현 편차 | 일관성 결여로 혼란 | QA 체크리스트 "일관성 테스트"에서 6개 파일 간 CLOSE 구성 동일성 검증. |
| opsdd DONE→CLOSE 리네이밍 시 DONE.md 산출물명과 혼동 | "DONE" 단계명 vs "DONE.md" 파일명 혼란 | CLOSE는 단계명, DONE.md는 산출물명으로 명확히 구분. opsdd 본문에서 "Phase 6: CLOSE" + "DONE.md 생성"으로 표기. |
| opwt 진행 현황 행 예시 부재 | opwt만 CLOSE 행 추가 검증 불가 | opwt는 네트워크 기반 STATE.md 확장 구조이므로 행 예시 없는 것이 정상. 단계 목록 + 본문 기술로 충분. 필요 시 후속 태스크로 행 예시 추가 검토. |
| additional-work.md에 변경이력 테이블 부재 | R-6 변경이력 추가 불가 | 변경이력 섹션을 신규 생성하여 v1.0(초기 작성) + v1.1(CLOSE 재진입, 121) 행 추가. |
| R-7 CLOSE 진입 게이트를 에이전트가 무시할 수 있음 | 사용자 의도 없이 자동 마감 발생 | opal-harness-agentic.md §7에 명시적 예외 규칙으로 등록하여 PM 자율 진행에서도 CLOSE 진입만은 차단. state-template.md + opal-harness.md §1에도 이중 명시. |
| 3개 문서 간 CLOSE 진입 게이트 규칙 불일치 | 규칙 해석 혼란 | QA 일관성 테스트에 3개 문서(opal-harness.md, state-template.md, opal-harness-agentic.md) 규칙 동일성 검증 항목 추가. |

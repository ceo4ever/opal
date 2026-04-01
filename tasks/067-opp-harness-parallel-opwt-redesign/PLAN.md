# PLAN: 하네스 병렬 처리 원칙 추가 + opwt 재설계

## 실행 순서

```
Step 1: opal-harness.md — §7 병렬 처리 원칙 추가
Step 2: opwt SKILL.md — 재설계 (TASK/ANALYSIS/PLAN/EXECUTE/QA)
Step 3: 배포 동기화 (소스 → ~/.opal/)
```

Step 1 완료 후 Step 2 진행 (opwt가 harness 원칙을 참조하므로 순차).
Step 3은 Step 1, 2 완료 후 병렬 복사 가능.

---

## Step 1: opal-harness.md §7 추가

**파일**: `opal/core/references/opal-harness.md`
**변경 유형**: 신규 섹션 추가 (기존 섹션 변경 없음)
**삽입 위치**: `## 변경이력` 직전

### 추가 내용

```markdown
## 7. 병렬 처리 원칙

모든 오케스트레이터에 공통 적용. **병렬 가능한 작업은 무조건 병렬로, 의존관계 있는 작업만 순차로.**

### 읽기: 병렬 툴콜 (서브에이전트 불필요)

독립된 파일/문서는 한 번의 응답에서 병렬 Read 호출한다.

```
# 올바른 예 — 병렬
Read(docs/PRD.md)
Read(docs/TRD.md)      ← 동시 호출
Read(docs/policy.md)

# 잘못된 예 — 순차
Read(docs/PRD.md) → 완료 후 → Read(docs/TRD.md) → 완료 후 → ...
```

### 실행: 병렬 서브에이전트 (Agent 디스패치)

독립적인 분석/작성/QA 작업은 한 번의 응답에서 병렬 Agent 디스패치한다.

```
# 올바른 예 — 병렬
Agent(문서1 분석 워커)
Agent(문서2 분석 워커)   ← 동시 디스패치
Agent(문서3 분석 워커)

# 잘못된 예 — 순차
Agent(문서1) → 완료 후 → Agent(문서2) → ...
```

### 의존관계: 순차 유지

`depends_on`이 있는 작업은 선행 작업 완료 후 실행한다.

```
독립 → 병렬 실행
의존 → 선행 완료 후 순차 실행
```

### 적용 기준

| 작업 유형 | 병렬 방법 | 서브에이전트 |
|----------|---------|------------|
| 파일/문서 읽기 | 병렬 툴콜 | ❌ 불필요 |
| 문서 분석 (독립) | Agent 병렬 디스패치 | ✅ 필요 |
| 문서 작성 (독립) | Agent 병렬 디스패치 | ✅ 필요 |
| QA 검증 (독립) | Agent 병렬 디스패치 | ✅ 필요 |
| 의존관계 있는 작업 | 순차 | 해당 없음 |
```

**변경이력 추가**: `v2.1 | 2026-04-01 | §7 병렬 처리 원칙 추가 — 읽기(툴콜)/실행(Agent) 병렬 필수 원칙 (067)`

---

## Step 2: opwt SKILL.md 재설계

**파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
**변경 유형**: 전체 재작성 (핵심 로직 보존)

### 재설계 구조

```
Harness 섹션 (기존 유지)
모드 정의 (기존 유지, Phase → 표준 단계명으로 용어 변경)
커버 범위 (기존 유지)
산출물 저장 구조 (기존 유지)

TASK 단계 [신규]
ANALYSIS 단계 [Phase 1 → 표준화]
PLAN 단계 [Phase 2 → 표준화]
EXECUTE 단계 [Phase 3 → 표준화]
QA 단계 [Phase 4 → 표준화]

STATE.md 네트워크 확장 (기존 유지 + 단계명 수정)
게이트 체크포인트 (기존 유지 + 단계명 수정)
문서 표준 (기존 유지)
참조 가이드 (기존 유지)
```

### 모드별 단계 선택 (변경)

| 모드 | 기존 | 변경 후 |
|------|------|--------|
| 작성 | Phase 2(간략) → Phase 3 → Phase 4 | TASK → PLAN(간략) → EXECUTE → QA |
| 수정 | Phase 1 → Phase 2 → Phase 3 → Phase 4 | TASK → ANALYSIS → PLAN → EXECUTE → QA |
| 분석 | Phase 1 → Phase 2(진단보고) → Phase 3(보완) → Phase 4 | TASK → ANALYSIS → PLAN(진단보고) → QA |

### TASK 단계 [신규]

PM 직접 수행. op-task 프로세스 기반 + opwt 전용 확인 항목:

1. 모드 결정 (작성 / 수정 / 분석)
2. 대상 문서 유형 확인 (PRD/TRD/정책서/IA/외부 API 명세서 등)
3. 외부 참조 산출물 여부 확인 (와이어프레임, ERD 등)
4. 산출물 저장 경로 확인 (`docs/PROJECT.md` 기반)
5. TASK.md 작성
6. STATE.md 초기화

### ANALYSIS 단계 [Phase 1 → 표준화]

- **읽기**: 기존 문서 경로 병렬 Read (하네스 §7 병렬 처리 원칙)
- **분석**: 문서별 워커 병렬 디스패치 (요약/이슈 반환)
- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- 기존 워커 프롬프트 형식 유지 (`[WORKER]` 마커, PM 컨텍스트 주입)

### PLAN 단계 [Phase 2 → 표준화]

- PM 직접 수행: 워커 결과 종합 → 교차 논리 검토 → 누락/불일치 진단
- 외부 참조 산출물 병렬 Read 후 진단
- `diagnosis.json` 생성 → 배치 편성(`depends_on` 기반)
- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- **게이트**: diagnosis.json 사용자 확인 (interactive) / PM 자율 승인 (agentic)

### EXECUTE 단계 [Phase 3 → 표준화]

- `diagnosis.json` 파싱 → 배치별 순회
- 독립 배치: 워커 병렬 디스패치
- 의존 배치: 순차 실행
- **STATE 갱신**: 배치 완료마다 STATE.md 갱신
- 기존 워커 프롬프트 형식 유지

### QA 단계 [Phase 4 → 표준화]

- QA 워커 디스패치 (`references/consistency-rules.md` 기반)
- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- PM 최종 판정: Pass → DONE.md / Fail → EXECUTE 부분 재진입

**버전**: v2.0 (메이저 — 구조 재설계)

---

## Step 3: 배포 동기화

병렬 복사:
- `opal/core/references/opal-harness.md` → `~/.opal/references/opal-harness.md`
- `opal/skills/opal-pilot-write-tech/SKILL.md` → `~/.opal/skills/opal-pilot-write-tech/SKILL.md`

---

## QA 체크리스트

- [ ] §7 추가 후 기존 §0-§6 내용 변경 없음
- [ ] 병렬 원칙 예시 코드가 명확하고 실행 가능한 수준
- [ ] opwt TASK 단계가 TASK.md + STATE.md를 생성하는가
- [ ] 각 단계에 STATE.md 갱신 지시가 명시되어 있는가
- [ ] 모드별 단계 선택이 정확하게 정의되어 있는가
- [ ] 핵심 로직 보존 (diagnosis.json, 배치 편성, network-guide, consistency-rules)
- [ ] [WORKER] 마커 + PM 컨텍스트 주입 유지
- [ ] 소스/배포 양쪽 모두 수정되었는가
- [ ] 변경이력이 두 파일 모두에 기록되었는가

---
name: op-task-execute
description: |
  **범용 실행 스킬**. PLAN.md의 실행 체크리스트를 따라 파일 작성/수정/삭제를 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-project-pilot)가 EXECUTE 단계를 디스패치할 때.
  필수 입력: checklist_source (경로 + 섹션, 오케스트레이터 지정). 보장 출력: 파일 변경 + changed_files.
---

# op-task-execute — 범용 실행

## 실행 컨텍스트

- **호출자**: 오케스트레이터(opal-project-pilot)가 EXECUTE 단계를 디스패치
- **실행 주체**: 워커 에이전트 (opal-task-agent)
- **입력**: `checklist_source` (오케스트레이터가 경로+섹션 지정) — PLAN.md 섹션 3 실행 체크리스트
- **출력**: 파일 변경 + `changed_files` 목록

## op-dev-execute와의 차이점

| 항목 | op-dev-execute | op-task-execute |
|------|---------------|----------------|
| 도메인 | 코드 개발 (FE/BE) | 도메인 무관 |
| 페르소나 | FE/BE 전환 | generalist-executor (단일) |
| execution-plan.json | 지원 | 미사용 |
| ui-designer 연동 | FE 화면 구현 위임 | 없음 |
| 보안 가드레일 | SQL Injection, 하드코딩 시크릿 등 | 없음 (범용이므로) |
| FE/BE 병렬 | 지원 | 없음 (순차 실행) |
| 영역 침범 금지 | FE/BE 워커 분리 | 없음 |
| 실행 모드 | 단순/복잡 (서브에이전트 배치) | 단일 모드 (순차 direct) |

---

## 페르소나

`personas/generalist-executor.md`를 Read하여 실행 원칙과 행동 규칙을 적용한다.

페르소나 파일이 없으면: 정확하고 계획에 충실한 실행자 역할을 따른다.

---

## 프로세스

### Step 1. 실행 가이드 로딩

```
Read references/execute-guide.md
```

가이드의 금지 행동, 가드레일, 실행 규칙을 숙지한다.

### Step 2. 체크리스트 확인

오케스트레이터가 지정한 `checklist_source`에서 실행 항목을 파악한다.
PLAN.md 섹션 3 실행 체크리스트를 읽어 전체 Step과 의존성을 파악한다.

### Step 3. 순서대로 실행

실행 체크리스트의 Step을 의존성 순서대로 하나씩 실행한다.

각 Step 실행 절차:
1. 대상 파일 확인 (이미 존재하면 Read → 내용 파악)
2. Write/Edit로 파일 작성/수정 (또는 Bash로 삭제)
3. Step의 완료 기준에 따라 검증
4. PLAN.md 체크박스 갱신: `- [ ] 완료` → `- [x] 완료`

### Step 4. 체크리스트 갱신

각 Step 완료 시 즉시 체크박스를 갱신한다.

### Step 5. QA 체크리스트 검증

모든 Step 완료 후, PLAN.md 섹션 4 QA 체크리스트를 자체 검증한다.
통과한 항목: `- [ ]` → `- [x]`

### Step 6. 결과 반환

워커는 오케스트레이터에 결과를 반환한다.

---

## 가드레일

### 절대 금지

| # | 금지 행동 | 이유 |
|---|----------|------|
| 1 | PLAN.md에 없는 파일 생성/수정 | 계획 밖 변경은 추적 불가 |
| 2 | PLAN에서 확정된 설계를 임의로 변경 | QA를 통과한 설계를 무효화 |

### 블로커 처리

블로커가 발생하면:
1. **즉시 중단** — 추측으로 해결하지 않는다
2. **사용자 보고**: Step 번호, 구체적 상황, 가능한 원인, 해결 방안 제안
3. **사용자 지시 대기** — 지시에 따라 재개 또는 건너뛰기

---

## 결과 반환

```json
{
  "artifact_path": "tasks/{NNN}-{태스크명}/",
  "summary": "{실행 요약}",
  "status": "completed | blocked",
  "blockers": [],
  "changed_files": ["파일1", "파일2"]
}
```

---

## EXECUTE 품질 체크리스트

- [ ] 모든 Step 체크박스가 [x] 또는 사용자 승인으로 건너뛰어졌는가
- [ ] 각 Step의 완료 기준이 통과되었는가
- [ ] 블로커 발생 시 사용자에게 보고되었는가
- [ ] 변경 파일 목록이 PLAN.md의 파일 목록과 일치하는가
- [ ] QA 체크리스트 체크박스가 갱신되었는가
- [ ] PLAN.md에 없는 파일을 생성/수정하지 않았는가

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 — op-dev-execute 기반 범용화 (FE/BE 특화 제거) |
| v1.1 | 2026-03-29 | 리네이밍: op-execute → op-task-execute |

# OPAL Harness -- 오케스트레이터 공통 인프라

> opal-pilot-* 오케스트레이터가 공유하는 프로세스 규칙.
> 각 opal-pilot SKILL.md 상단에서 이 문서를 Read하고, 도메인 고유 부분만 직접 정의한다.

---

## 0. 용어 정의

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| opal-pilot | OPAL Pilot | 태스크 파이프라인을 조종하는 오케스트레이터 |
| op-dev | OPAL Pilot Dev Phase | dev 도메인 단계 스킬 (코드 변경 수반) |
| op-task | OPAL Pilot Task Phase | 범용 단계 스킬 (도메인 무관) |
| opd / opds / opdw | OPAL Pilot Dev 약어 | Full / Short / Wireframe |
| opw / opwt | OPAL Pilot Write 약어 | Write / Write-Tech |

---

## 1. Guards (제약)

### 구현 금지 원칙 (최우선 규칙)

**사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다.**

- 허용: 산출물 문서(.md) 작성, QA 에이전트 호출, 코드베이스 읽기/분석, 웹 검색
- 금지 (승인 전): 소스 코드 파일 생성/수정, 패키지 설치, DB 스키마 변경, 설정 파일 수정

### Git 사전 점검

태스크 시작 전 `git status`를 확인한다:
- **클린 상태**: 진행
- **커밋되지 않은 변경**: 사용자에게 커밋/스태시를 제안한 후 진행

### 커밋 규칙

**커밋은 사용자가 명시적으로 요청할 때만 수행한다.** EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다. 완료 보고만 하고 사용자 지시를 기다린다.

---

## 2. Gates (체크포인트)

### 단계 게이트

각 단계 완료 시 사용자에게 보고하고 승인을 받는다.

| 응답 | 동작 |
|------|------|
| "확인", "다음", "승인" | 다음 단계 진행 |
| 피드백/수정 요청 | 현재 단계 수정 후 재보고 |
| "중단", "보류" | 산출물 저장 후 대기 |

### QA Gate

단계 완료 후 op-task-qa 에이전트를 호출하여 산출물을 검증한다.
- op-task-qa 탐색: `{프로젝트}/.opal/skills/op-task-qa/SKILL.md` -> `~/.opal/skills/op-task-qa/SKILL.md`

### PM Gate

`.opal/AGENT.md`가 존재하면 PM 검토 기준으로 산출물을 검토한다.
상세: 글로벌 AGENT.md "PM 컨텍스트 로드 > PM 검토 게이트".
AGENT.md 미존재 시 스킵.

---

## 3. State (상태 관리)

### STATE.md 기본 구조

오케스트레이터 전용. 단계 스킬은 STATE.md를 갱신하지 않는다 (EXECUTE Step 진행 제외).

| 이벤트 | 갱신 주체 | 내용 |
|--------|----------|------|
| TASK 완료 | 오케스트레이터 | STATE.md 초기 생성 |
| 단계 시작 | 오케스트레이터 | 단계, 상태: 진행 중 |
| 단계 완료 | 오케스트레이터 | 완료 산출물 갱신, 상태: 대기 중 |
| EXECUTE Step 완료 | 워커 | 진행: Step N/M 완료 |
| 블로커 | 워커 | 상태: 블로커 + 블로커 섹션 |
| 완료 | 오케스트레이터 | 상태: 완료 |

### STATE.md 공통 템플릿

각 opal-pilot는 이 템플릿의 `{모드}`, `{단계 목록}`, `{산출물 목록}`을 도메인에 맞게 치환한다.

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: {모드}
- 단계: {단계 목록}
- 진행: {Step N/M 완료 (EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
{산출물 목록}

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{다음으로 수행할 작업}
```

### 세션 복원

새 세션에서 `tasks/{NNN}-{name}/STATE.md`가 존재하면 Read하여 정확한 지점에서 재개한다.

---

## 4. TASK 공통 프로세스

오케스트레이터가 **직접 수행**한다 (워커 디스패치 없음).

1. `op-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/op-task/SKILL.md` -> `~/.opal/skills/op-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.
3. STATE.md를 생성한다.
4. 사용자에게 보고하고 다음 단계 승인을 받는다.

```
📋 [TASK] 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/TASK.md
다음 단계({다음 단계명})로 넘어갈까요?
```

> 도메인별 추가 확인 필드(문서 유형, 출력 모드 등)는 각 opal-pilot SKILL.md에서 정의.

---

## 5. Observability (관측)

### 스킬 탐색 경로

dev 단계 스킬:
1. `{프로젝트}/.opal/skills/op-dev-{stage}/SKILL.md`
2. `~/.opal/skills/op-dev-{stage}/SKILL.md`

범용 단계 스킬:
1. `{프로젝트}/.opal/skills/op-task{-suffix}/SKILL.md`
2. `~/.opal/skills/op-task{-suffix}/SKILL.md`

에이전트:
1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

### 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.md`가 존재하면, 단계 완료 시 작업 히스토리를 갱신한다:
- 단계 완료: `단계` 컬럼 -> `{단계} -> {다음} 대기`
- DONE.md 생성: `단계` 컬럼 -> `완료 (커밋해시)`

---

## 6. Model Mapping (모델 매핑)

오케스트레이터가 워커를 디스패치할 때, model 필드는 플랫폼 중립적인 레벨명을 사용한다.
레벨별 플랫폼 매핑: `~/.opal/references/opal-model-mapping.md` 참조.

| 레벨 | 용도 |
|------|------|
| `light` | 단순 작업 (분류, 포맷 변환, 검색 기반 분석) |
| `standard` | 범용 작업 (코드 작성, 문서 작성, 일반 분석) |
| `advanced` | 복잡 추론 (아키텍처 설계, 깊은 분석) |

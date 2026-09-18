# opal-pilot-project

문서 작성, 간단한 코드 수정, 설정 변경 등 프로젝트의 범용 태스크를 4단계로 수행하는 오케스트레이터.

## 개요

- 코드 개발이나 기획 산출물처럼 전용 파이프라인이 있는 작업이 아닌, 그 사이에 걸치는 범용 작업을 처리한다.
- TASK → PLAN → EXECUTE → CLOSE의 짧은 파이프라인으로 진행되며, 별도의 코드 테스트 단계는 없다.
- 각 단계 완료 시 PM이 산출물을 직접 검증(PM Gate)한 뒤 사용자에게 보고한다.
- CLOSE 단계에서 관련 문서 동기화와 brain ingest(프로젝트에 brain이 있는 경우)를 함께 수행한다.

## 언제 쓰나

문서 작성, 설정 변경, 워크플로우 수행처럼 범용적인 작업에 사용한다. 아래처럼 전용 파이프라인이 있는 작업은 해당 스킬을 사용한다.

| 상황 | 사용할 스킬 |
|---|---|
| 코드 개발이 수반되는 작업 | `opal-pilot-dev-short`(opds) 또는 `opal-pilot-dev`(opd) |
| 기획 산출물 세트(PRD, TRD 등) 작성/관리 | `opal-pilot-write-tech`(opwt) |
| 와이어프레임부터 UI 구현까지 | `opal-pilot-dev-wireframe`(opdw) |
| 그 외 범용 작업(문서 작성, 설정 변경 등) | `opal-pilot-project`(opp) |

## 사용법

```
//opp {작업 요청}
```

모드 플래그로 진행 방식을 지정할 수 있다.

| 호출 | 모드 |
|---|---|
| `//opp 작업` | semi-agentic (기본) — PLAN까지 사용자 검토, EXECUTE부터 PM 자율 |
| `//opp --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opp --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

어떤 모드라도 **CLOSE 진입은 항상 사용자 승인이 필요**하다.

## 파이프라인

```
TASK → PLAN → EXECUTE → CLOSE
```

- **TASK**: 요구사항을 정리해 TASK.md를 작성한다.
- **PLAN**: 워커(`op-task-plan`)가 실행 계획을 수립해 PLAN.md를 작성한다. PM Gate에서 TASK.md 요구사항 커버 여부와 실행 체크리스트 완성도를 검증한다.
- **EXECUTE**: 워커(`op-task-execute`)가 PLAN.md의 실행 체크리스트에 따라 작업을 수행한다. PM Gate에서 체크리스트 완료 여부와 컨벤션 진단 결과를 검증한다.
- **CLOSE**: DONE.md를 생성하고, 태스크로 내용이 달라진 관련 문서(ARCHITECTURE.md 등)를 동기화하며, 프로젝트에 brain이 있으면 op-brain-ingest로 산출물을 누적한다.

## 산출물

- `TASK.md`, `PLAN.md`, `DONE.md`
- (컨벤션 적용 대상이 있는 경우) `GC-CONVENTION-*.md`

## 관련 스킬

- `op-task` — TASK 단계 공통 프로세스
- `op-task-plan` — PLAN 단계 워커 (실행 계획 수립)
- `op-task-execute` — EXECUTE 단계 워커 (작업 수행)
- `op-task-qa` — 필요 시 QA 워커
- `op-brain-ingest` — CLOSE 단계에서 산출물을 프로젝트 brain에 누적 (brain 사용 프로젝트 한정)

## FAQ

### 코드 개발 작업에도 쓸 수 있나요?
간단한 설정 변경 정도라면 가능하지만, 코드 구현이 본격적으로 수반되는 작업은 테스트 단계가 있는 `opal-pilot-dev-short`(opds)나 `opal-pilot-dev`(opd)를 사용하는 것이 맞다.

### PLAN 단계에서 어떤 검증을 거치나요?
PM이 PLAN.md를 직접 읽고 TASK.md 요구사항이 모두 반영됐는지, 실행 체크리스트에 완료 기준이 명시됐는지, 설계상 빈틈이 없는지를 확인한 뒤에만 EXECUTE로 넘어간다.

### agentic 모드에서도 승인이 필요한 순간이 있나요?
있다. CLOSE 단계 진입만큼은 어떤 모드에서도 사용자 승인이 필수다.

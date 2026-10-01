---
type: entity
title: opal-self-pm
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- skill
- operator
- pm
- task-122
sources:
- task:122
- task:154
- task:166
- skill:opal-self-pm
related: [actor-axis-orthogonal-to-mode, self-pm-tool]
created: '2026-09-12'
updated: '2026-10-01'
status: active
---
## 개요

`opal-self-pm`(`//oppm`)은 소유자가 "대화하면서 직접 해달라"고 요청할 때 발동하는 대화형 PM 작업 루프다. 단계 파이프라인을 가진 Pilot이 아니라, `opal-brain`(`opbr`)과 같은 유형의 operator 스킬이다. 질문 1개를 던지고 조회·정리를 반복해 작업 범위를 확정한 뒤 PM이 직접 조회·작성·수정·검증하고, 완료 전 지식 영향을 전수 판정한 뒤 종료한다.

## 책임 (WHAT)

- 신규 작업은 정식 태스크 폴더에 TASK.md와 실행 기록을 준비한다. TASK·DONE은 수행·검토 기록이며 PLAN 등은 필요 시 작성한다. 현재 기록과 표준 사건 로그는 같은 실행 ID를 공유한다.
- 진입 시 [[self-pm-tool]]에 `init`을 호출해 목표를 기록하고, 이후 단계 전이를 그 도구로 남긴다.
- 질문은 한 번에 하나씩만 던지며, 답변 후 조회·정리를 거쳐 결정을 누적한다.
- 파일·설정·데이터를 쓰기 전에 목표·범위·변경 대상·결정과 가정·검증 방법·예상 영향의 6항목 계약을 제시하고 사용자 승인을 받는다.
- 수정 범위 조사에서 찾은 지식·관련 문서를 영향 후보 집합으로 승계하고, 실행 중에는 새 결정·변경 파일·소비자만 증분 추가한다.
- 완료 직전에는 전체 탐색을 반복하지 않고 영향 후보와 최종 변경의 정합성만 확인한다. 기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan 8영역을 전부 판정하고, 영향 있는 문서는 실제 갱신한 뒤 현재 판정 8건을 전체 교체한다.
- PROJECT는 문서 라우팅 인덱스로 사용하되 완전성 증거로 간주하지 않는다. 초기 조사에서 변경 표면과 직접 소비자·참조자를 역추적하고, 종료 시에는 새 범위만 추가 확인해 후보를 경로별로 닫는다.
- 규칙·gate·workflow·수용 기준·예외·선택 원칙의 의미 변경은 brain이 존재하면 WHY 동기화 대상으로 우선 판정한다. owner 문서가 WHAT의 SSOT라는 이유만으로 brain을 `no-op` 처리하지 않는다.
- 사용자가 최종 확인을 발화하기 전에는 종결 선언을 하지 않는다. 수정 의견은 확인으로 간주하지 않고, 보정·재검증과 새 gate를 거친다.
- 독립 검증이 필요하면 GC 스킬을 호출하고 PM이 자기 작업을 직접 채점하지 않는다.

## 대상 프로젝트 적용

OPAL FW 저장소는 스킬의 개발·배포 위치이며 실행 대상의 문서 구조가 아니다. 실제 개발 프로젝트의 PROJECT 문서를 읽어 동기화 대상과 공통·영역별 컨벤션을 선별하고 TASK의 영향 후보로 승계한다. 선택된 레지스트리 경로·패턴이 실제로 해석되는지 확인하고 코드 경로와 문서 폴더의 별칭이 다르면 매핑 근거를 남긴다. PROJECT가 누락되거나 낡을 수 있으므로 TASK 직접 지목, changed files, 규칙·인터페이스의 소비자와 참조자, 선별 문서의 필수 종속 원문을 함께 확인한다. 실행 중에는 증분만 보강하고 종료 시에는 최종 변경과 정합성만 검증한다. 8영역은 누락 방지 관점이며 고정 경로 목록이 아니다.

## 설계 배경 (WHY)

- 정식 태스크 폴더는 추적·재개·사용자 검토의 단위이며 파이프라인 도입을 뜻하지 않는다. 필수 TASK·DONE과 선택 PLAN은 실제 수행을 설명하고 operator 경계를 유지한다.
- `opal-self-pm`은 Pilot이 아니라 `opal-brain`과 동일 유형이므로 `state-tool init --skill` enum과 3-SSOT에 접촉하지 않는다.
- 독립 검증 경계와 GC 호출 지점의 공유 계약은 `harness/actor.md`가 소유하고, `opal-self-pm`은 호출 시점만 규정한다.
- (근거: task:166) PROJECT만 읽으면 레지스트리 자체의 누락을 발견할 수 없는 자기참조 문제가 있다. 그래서 PROJECT는 후보를 찾는 인덱스로 제한하고, 변경 표면·직접 소비자·참조자의 독립 역추적을 합쳐 문서 후보를 닫는다.
- (근거: task:166) 관련 지식·문서 탐색은 수정 범위를 정할 때 이미 수행된다. 종료 시 같은 탐색을 반복하면 워크플로우만 길어지고 초기 판단 맥락을 잃을 수 있으므로, 초기 후보를 승계하고 실행 중 증분·최종 정합만 확인한다.
- (근거: task:166) 현재 규범 WHAT과 채택 이유 WHY는 소유 위치가 다르다. owner SSOT는 brain 생략 근거가 아니며, 의미 있는 규범 변경은 관련 WHY가 이미 존재하는지 확인한 뒤 update 또는 제한된 no-op 사유로 닫는다.
- (근거: task:166) `knowledge_impact`는 현재 상태 스냅샷이다. 재판정 결과를 append하면 상충 판정이 공존하므로 8영역 전체를 `--set-field`로 교체하고, 과거 오판·보정 이력은 run-log가 소유한다.

## 관계 (HOW)

- [[actor-axis-orthogonal-to-mode]] — Pilot actor 축과 대비되는 별개 경로다.
- [[self-pm-tool]] — 현재 실행 기록의 저장 도구. 시간순 사건은 run-log가 소유한다.
- `docs/PROJECT.md` — 관련 문서 라우팅 인덱스. 변경 표면 역추적을 대체하지 않는다.
- `op-gc-security`·`op-gc-convention`·`op-gc-report` — 독립 검증이 필요할 때 호출하는 대상이다.

## 소스 커버리지

| 식별자 | 경로 | 설명 |
|---|---|---|
| 루프 절차 | `opal/skills/opal-self-pm/SKILL.md` | 질문·계약·실행·동기화·확인·종료 |
| 지식 판정 | `opal/skills/opal-self-pm/references/knowledge-sync.md` | 영향 후보 승계, 증분 보강, 종료 정합, brain 기준, 현재 스냅샷 |
| 수행 기록 | `opal/skills/opal-self-pm/references/task-records.md` | 태스크 문서·run-log·수정 요청 gate |
| 도구 | `opal/tools/self-pm-tool/` | 8필드 현재 기록과 전체 교체 |

# opal-pilot-dev-wireframe

와이어프레임 설계부터 UI 구현까지 한 번에 진행하는 오케스트레이터.

## 개요

- 정책서·요구사항 문서·스케치 이미지·구두 요청 등 입력물을 받아 와이어프레임을 설계하고, 이어서 화면을 구현한다.
- TASK → WIREFRAME → EXECUTE → CLOSE의 4단계로 진행하며, 이미 `wireframe.md`가 있으면 WIREFRAME 단계를 스킵하고 바로 EXECUTE로 넘어간다.
- EXECUTE는 UI 구현에 특화된 FE 전문 워커로 단일 라우팅된다(작업을 여러 담당자로 분배하지 않는다).

## 언제 쓰나

신규 화면을 와이어프레임부터 설계해서 구현까지 진행할 때 사용한다. 이미 존재하는 프로젝트에서 화면을 수정하거나 추가 구현만 필요한 경우는 다른 스킬을 쓴다.

| 상황 | 사용할 스킬 |
|---|---|
| 신규 화면을 와이어프레임 설계부터 시작 | `opal-pilot-dev-wireframe`(opdw) |
| 기존 프로젝트에서 "화면 구현", "UI 만들어줘", "화면 수정" 등 | `opal-pilot-dev`(opd) 또는 `opal-pilot-dev-short`(opds)의 UI 담당 워커(plan-driven 모드) |

## 사용법

```
//opdw {작업 요청}
```

모드 플래그:

| 호출 | 모드 |
|---|---|
| `//opdw 작업` | semi-agentic (기본) — WIREFRAME까지 사용자 검토, EXECUTE부터 PM 자율 |
| `//opdw --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opdw --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

어떤 모드라도 **CLOSE 진입은 항상 사용자 승인이 필요**하다.

## 파이프라인

```
TASK → WIREFRAME → EXECUTE → CLOSE
```

- **TASK**: 기술 환경(React/Next.js 버전, shadcn/ui 여부), 출력 모드(프로토타입 bundle.html vs 프로덕션 Next.js), 입력물 분류(문서/이미지/구두 요청)를 함께 확인한다.
- **WIREFRAME**: `wireframe.md`가 없으면 워커(`op-dev-wireframe`)가 TASK.md와 입력 문서·이미지를 바탕으로 화면 목록과 레이아웃을 설계한다. 이미 존재하면 이 단계는 스킵된다. PM Gate에서 TASK.md 요구사항 커버 여부와 화면 구성 완성도를 검증한다.
- **EXECUTE**: FE 전문 워커(기본 `opal-fe-agent`, 불가 시 `opal-task-agent` 폴백)가 wireframe.md 전체를 기준으로 화면을 구현한다(`op-dev-execute`). 프로토타입(ui-designer scaffold) 또는 프로덕션(plan-driven) 모드로 진행한다. PM Gate에서 빌드/린트 결과와 wireframe↔코드 대조, 컨벤션 진단을 검증한다.
- **CLOSE**: DONE.md 생성, 관련 문서(와이어프레임 포함) 동기화, brain ingest.

## 산출물

- `TASK.md`, `wireframe.md`(입력 시점에 이미 존재할 수 있음), `DONE.md`
- (컨벤션 적용 대상이 있는 경우) `GC-CONVENTION-*.md`

## 관련 스킬

- `op-dev-wireframe` — WIREFRAME 단계 워커 (화면 설계)
- `op-dev-execute` — EXECUTE 단계 워커 (UI 구현)
- `op-dev-qa` — 와이어프레임·빌드 검증 기준 참조
- `op-task` — TASK 단계 공통 프로세스

## FAQ

### wireframe.md가 이미 있으면 어떻게 되나요?
WIREFRAME 단계 전체가 스킵되고 바로 EXECUTE로 진입한다.

### EXECUTE에서 여러 워커가 나눠서 작업하나요?
아니다. 와이어프레임 기반 구현은 본질적으로 FE 작업이므로 담당을 나누지 않고 FE 전문 워커 하나가 wireframe.md 전체를 구현한다.

### 기존 화면을 수정하고 싶을 때도 이 스킬을 쓰나요?
아니다. 이미 운영 중인 프로젝트에서 화면을 구현·수정하는 작업은 `opal-pilot-dev` 또는 `opal-pilot-dev-short`가 담당한다.

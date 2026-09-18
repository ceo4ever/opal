# opal-pilot-write-tech

PRD, TRD, 서비스 정책서, IA 등 기획 산출물을 하나의 논리적 네트워크로 관리하는 오케스트레이터.

## 개요

- 문서 간 정합성을 유지하면서 PRD·TRD·서비스 정책서·IA 등 여러 기획 문서를 병렬로 분석·작성한다.
- PM이 교차 논리 검토, 문서별 조치 결정(보강/재작성/신규), 배치 편성, 최종 정합성 판정을 직접 수행한다.
- 독립적인 문서는 읽기·분석·작성을 병렬로 처리하고, 의존관계가 있는 문서만 순차로 처리한다.
- 작업 성격에 따라 세 가지 모드(작성/수정/분석)로 나뉘며, 모드별로 거치는 단계가 다르다.

## 언제 쓰나

기획 산출물 세트를 새로 작성하거나, 기존 기획 문서를 수정·보강하거나, 문서 간 정합성만 진단하고 싶을 때 사용한다.

| 상황 | 사용할 스킬 |
|---|---|
| PRD/TRD/정책서/IA 등 기획 산출물 세트 작성·관리 | `opal-pilot-write-tech`(opwt) |
| 코드 개발 작업 | `opal-pilot-dev`(opd) 또는 `opal-pilot-dev-short`(opds) |
| 범용 작업(문서 하나만 간단히 수정 등) | `opal-pilot-project`(opp) |

## 사용법

```
//opwt {작업 요청}
```

모드 플래그:

| 호출 | 모드 |
|---|---|
| `//opwt 작업` | semi-agentic (기본) |
| `//opwt --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opwt --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

TASK 단계에서 interview를 통해 작성할 산출물(필수 4종: PRD/TRD/서비스 정책서/IA, 선택 5종, 프로젝트 특화 외부 API 명세서)과 저장 경로를 결정한다.

## 파이프라인

작업 성격에 따라 아래 세 가지 조합 중 하나로 진행된다.

| 모드 | 단계 |
|---|---|
| 작성 | TASK → PLAN(간략) → EXECUTE → QA → CLOSE |
| 수정 | TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE |
| 분석 | TASK → ANALYSIS → PLAN(진단보고) → QA → CLOSE |

- **TASK**: PM이 interview 스킬로 작성할 산출물, 외부 참조 문서, 저장 경로를 확인해 TASK.md에 기록한다.
- **ANALYSIS**(수정/분석 모드만): 기존 문서를 병렬로 읽고 문서별 워커를 병렬 디스패치해 요약·이슈를 취합한다.
- **PLAN**: PM이 직접 교차 논리 검토를 수행해 문서별 조치(보강/재작성/신규)를 결정하고 `diagnosis.json`으로 배치를 편성한다(작성 모드는 신규 작성 대상만 확정하는 간략 진단).
- **EXECUTE**(작성/수정 모드만): `diagnosis.json`의 배치별로 워커를 병렬 또는 순차 디스패치해 문서를 작성·보강한다. 배치가 끝날 때마다 PM Gate를 거친다.
- **QA**: PM이 유형 간/내 정합성을 검증하는 QA 워커를 디스패치하고, PLAN.md의 QA 체크리스트를 결과로 갱신한다. Fail 시 실패한 문서만 EXECUTE로 재진입한다.
- **CLOSE**: DONE.md 생성, 관련 문서 동기화, brain ingest.

## 산출물

- `TASK.md`, `ANALYSIS.md`(수정/분석 모드), `PLAN.md`, `diagnosis.json`, `DONE.md`
- 기획 산출물 본체(저장 경로는 TASK 단계에서 결정): 예) `100.기획/110.PRD/PRD.md`, `120.TRD/TRD.md`, `130.정책서/*.md`, `140.IA/ia.json` + `ia-sitemap.md` 등

## 관련 스킬

- `op-brain-ingest` — CLOSE 단계에서 산출물을 프로젝트 brain에 누적 (brain 사용 프로젝트 한정)

## FAQ

### 어떤 모드로 진행할지는 누가 정하나요?
TASK 단계 interview에서 사용자가 선택한다. 기존 문서 유무와 요청 내용에 따라 작성/수정/분석 중 하나로 결정된다.

### 문서 저장 경로는 어떻게 정해지나요?
`docs/PROJECT.md`에 이미 등록된 경로가 있으면 그것을 우선 사용하고, 없으면 기본 트리(`100.기획/` 이하)를 제안한다. 사용자가 다른 컨벤션을 원하면 자유롭게 지정할 수 있다.

### 문서 간 충돌은 언제 발견되나요?
PLAN 단계의 교차 논리 검토와 QA 단계의 정합성 검증, 두 시점에서 확인한다. QA에서 실패하면 실패한 문서만 다시 EXECUTE로 돌아간다.

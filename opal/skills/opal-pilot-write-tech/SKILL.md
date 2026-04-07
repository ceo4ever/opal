---
name: opal-pilot-write-tech
description: |
  **서비스 기획 산출물 네트워크 오케스트레이터**. 기술 산출물(PRD, TRD, 서비스 정책서, IA 등)을 논리적 네트워크로 관리한다.
  PM이 워커를 병렬 디스패치하여 문서를 분석/작성하고, 교차 논리 검토와 정합성 검증으로 문서 간 일관성을 보장한다.
  반드시 이 스킬: "opal-pilot-write-tech", "opwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토", "기획 문서 최신화".
---

# opal-pilot-write-tech

서비스 기획 산출물 네트워크 오케스트레이터.

## Harness

> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.
> 병렬 처리 원칙은 하네스 §7을 따른다 — 읽기는 병렬 툴콜, 독립 작업은 병렬 Agent 디스패치.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

## 설계 원칙

- **문서가 인터페이스** — 프로젝트 문서(`docs/`)만 참조, 다른 스킬의 존재를 모른다
- **PM 중심 관리** — 교차 검토/진단/배치 편성/최종 판정/문서 등록
- **병렬 우선** — 독립 문서는 읽기/분석/작성 모두 병렬. 의존관계 있는 문서만 순차

## 커버 범위

**필수 4종**: PRD, TRD, 서비스 정책서(복수), IA(기능 포함 — JSON + Mermaid 사이트맵 이중 출력)
**선택 4종**: 기능도, 순서도, 운영 정책서, 서비스 매뉴얼
**프로젝트 특화 선택**: 외부 API 명세서 (외부 API 연동 프로젝트 한정 — 메타, 구글광고 등 서드파티 API 스펙 기획 산출물화)
**PMO**: 개발 WBS (기획 산출물 기반 개발 항목 구조화 — IA/기능 목록을 입력으로 MECE 분해)
**순서 체인**: PRD → TRD → 서비스 정책서 → IA (역방향도 가능)
**외부 참조**: 와이어프레임, ERD 등 프로젝트 내 기존 문서를 참조하여 작성 품질 향상 (읽기 전용, 선택적)

## 산출물 저장 구조

- `docs/` = 메타 문서 (`PROJECT.md`가 SSOT), 산출물은 별도 폴더
- PM이 `docs/PROJECT.md`로 기존 구조 파악 → 없으면 default 제안 → `PROJECT.md`에 기록

## 3가지 모드와 단계 선택

| 모드 | 단계 |
|------|------|
| 작성 | TASK → PLAN(간략) → EXECUTE → QA |
| 수정 | TASK → ANALYSIS → PLAN → EXECUTE → QA |
| 분석 | TASK → ANALYSIS → PLAN(진단보고) → QA |

---

## TASK 단계

오케스트레이터가 **직접 수행**한다. 하네스 §4 TASK 공통 프로세스 기반 + opwt 전용 확인 항목.

### opwt 전용 확인 항목

1. **모드 결정**: 작성 / 수정 / 분석
2. **대상 문서 유형**: PRD, TRD, 정책서, IA, 외부 API 명세서, 개발 WBS 등 (복수 선택 가능)
3. **외부 참조 여부**: 와이어프레임, ERD 등 참조할 기존 산출물 확인
4. **산출물 저장 경로**: `docs/PROJECT.md`로 기존 구조 파악 → 없으면 제안

### 완료 처리

- TASK.md 작성 (모드, 대상 문서 유형, 외부 참조, 저장 경로 포함)
- STATE.md 초기화 (하네스 §3 STATE.md 공통 템플릿 + 네트워크 확장 섹션 포함)
- **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
- 보고 후 다음 단계 승인 (interactive) / 자율 진행 (agentic)

---

## ANALYSIS 단계

> **적용 모드**: 수정, 분석

### 읽기 (병렬 툴콜)

기존 문서 경로를 스캔하여 독립 문서를 **병렬 Read**한다.

### 분석 (병렬 Agent 디스패치)

문서별 워커를 **병렬 디스패치**하여 요약/이슈를 반환받는다.

- 워커 프롬프트: `references/network-guide.md` "Phase 1 워커 프롬프트"
- **[PM 컨텍스트 주입]** 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### 산출물

워커 분석 결과를 취합하여 `ANALYSIS.md`로 저장한다.

```
tasks/{NNN}-opwt-{name}/ANALYSIS.md
- 문서별 요약 및 이슈 목록
- 워커별 반환 결과 취합
```

### STATE 갱신

- 단계 시작 시: `단계: ANALYSIS 진행 중`
- 단계 완료 시: `ANALYSIS ✅`, 완료 산출물 갱신

### 게이트

ANALYSIS 완료 후 아래 절차를 순서대로 수행한다:

1. **PM Gate (자가 체크)** — ANALYSIS는 PM이 직접 수행하는 단계이므로 외부 QA 에이전트 호출 없이 PM이 자가 점검한다.
   - AGENT.md 검토 기준(§4) 7항목을 체크한다
   - ANALYSIS.md 내용이 모든 워커 결과를 취합하고 있는지 확인한다
   - 문서별 요약 및 이슈 목록이 누락 없이 작성되었는지 확인한다
   - Artifact Gate: `ANALYSIS.md` 파일이 존재하고 내용이 있는지 확인한다
2. **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
3. 사용자 확인 (interactive) / PM 자율 승인 (agentic)

---

## PLAN 단계

PM이 **직접 수행**한다.

### 수정/분석 모드 (전체 진단)

1. ANALYSIS.md 결과 기반 종합
2. 외부 참조 산출물 **병렬 Read** (와이어프레임, ERD 등)
3. 교차 논리 검토 — 누락/불일치 진단
4. 문서별 조치 결정 (보강/재작성/신규)
5. `diagnosis.json` 생성 → `depends_on` 기반 배치 편성

### 작성 모드 (간략 진단)

기존 문서 없음 → 신규 작성 대상 문서 목록 확정 → `diagnosis.json` 생성

### 산출물

`PLAN.md` 작성 후 태스크 폴더에 저장한다.

```
tasks/{NNN}-opwt-{name}/PLAN.md
- 교차 논리 검토 결과 및 진단 근거
- 배치 편성 요약 (diagnosis.json 인간 가독 버전)
- QA 체크리스트 (EXECUTE 완료 후 갱신)
```

`diagnosis.json`은 EXECUTE 단계의 기계 처리용 별첨으로 별도 저장한다.

### 공통

- **STATE 갱신**: 단계 시작/완료 시 STATE.md 갱신
- **QA Gate** (op-task-qa) — PLAN.md 검증
- **Artifact Gate** (하네스 §2.5 참조)
- **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
- **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조)
- **게이트**: PLAN.md + 배치 계획 사용자 확인 (interactive) / PM 자율 승인 (agentic)

---

## EXECUTE 단계

> **적용 모드**: 작성, 수정

`diagnosis.json` 파싱 → 배치별 순회:

- **독립 배치**: 워커 **병렬** 디스패치
- **의존 배치**: 선행 배치 완료 후 순차 실행

### 워커 디스패치

- 워커 프롬프트: `references/network-guide.md` "Phase 3 워커 프롬프트"
- **[PM 컨텍스트 주입]** 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### STATE 갱신

- 배치 시작 시: `Batch N 진행 중`
- 배치 완료 시: STATE.md 배치 계획 테이블 갱신

### 게이트 (배치별)

배치 완료
  → **QA Gate** (op-task-qa)
  → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인)
  → **PM Gate** (배치 단위 간이 검토 — 하네스 §3 참조. 전체 PM Gate는 QA 단계 최종 판정에서 수행)
  → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)
배치 완료 후 `docs/PROJECT.md` 등록 확인

---

## QA 단계

QA 워커 디스패치 (`references/consistency-rules.md` 기반, 유형 간+내 검증).

- **[PM 컨텍스트 주입]** QA 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### STATE 갱신

- 단계 시작/완료 시 STATE.md 갱신 (하네스 §3 State Gate 기준 적용)

### 산출물

PLAN.md의 QA 체크리스트를 검증 결과로 갱신한다 (하네스 §2 QA 체크리스트 갱신 의무).
모든 항목이 `[x]` 또는 "N/A + 사유"로 채워진 후 DONE.md를 생성한다.

### PM 최종 판정

- **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → **PM Gate** 진입
- **Pass**: DONE.md 생성
- **Fail**: EXECUTE 부분 재진입 (실패 문서만)

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 네트워크 확장

하네스 STATE.md 기본 구조에 도메인 고유 섹션 추가:

- `{모드}`: 작성/수정/분석
- `{단계 목록}`: TASK → ANALYSIS → PLAN → EXECUTE → QA (모드에 따라 일부 생략)
- **네트워크 상태**: 산출물 | 유형 | 상태 | 버전 | 경로
- **배치 계획**: Batch | 문서 | 의존 | 상태

---

## 문서 표준

opal-doc-standard 적용: `~/.opal/references/opal-doc-standard.md`

## 참조 가이드

- `references/network-guide.md` — 산출물 정의, 연결 맵, diagnosis.json 스키마, 워커 프롬프트, 배치 규칙, IA 형식, **외부 참조 산출물 가이드**
- `references/consistency-rules.md` — 유형 간/내 검증, QA 워커 프롬프트, **외부 참조 검증**

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.3 | 2026-04-01 | 외부 참조 산출물 지원 — diagnosis.json reference_artifacts[], 워커 프롬프트 확장, 외부 참조 검증 규칙 (062) |
| v1.4 | 2026-04-01 | 외부 API 명세서 프로젝트 특화 선택 타입 추가 — 서드파티 API 기획 산출물화, 내부 API와 구분 (064) |
| v1.5 | 2026-04-01 | IA 산출물 JSON + Mermaid 사이트맵 이중 출력으로 확정 — 변환 스펙, classDef 기준, 분리 규칙 (065) |
| v1.6 | 2026-04-01 | Phase 1/3/4 워커 디스패치에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v2.0 | 2026-04-01 | 재설계 — Phase 1-4 → 하네스 표준 단계(TASK/ANALYSIS/PLAN/EXECUTE/QA), TASK 단계 추가, 각 단계 STATE 갱신 명시, 병렬 원칙 적용 (067) |
| v2.1 | 2026-04-01 | 단계별 산출물 문서 추가 — ANALYSIS.md(워커 결과 취합), PLAN.md(진단 근거+배치+QA체크리스트), QA 단계 PLAN.md 갱신 의무 (067) |
| v2.2 | 2026-04-02 | ANALYSIS 게이트 + PLAN QA Gate + EXECUTE 배치별 QA Gate 추가 (072) |
| v2.3 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.4 | 2026-04-06 | PMO 그룹 신설 + 개발 WBS 추가 — 커버 범위 및 TASK 확인 항목 갱신 (089) |
| v2.5 | 2026-04-06 | ANALYSIS PM Gate(자가 체크) 추가 + EXECUTE 배치 게이트 "PM 검토" → "PM Gate" 명확화 (090) |
| v2.6 | 2026-04-07 | TASK/ANALYSIS/PLAN/EXECUTE/QA 각 단계 Gate에 State Gate 참조 추가 (094) |

---
name: op-brain-ingest
description: |
  **CLOSE 단계 경량 워커 — 태스크 산출물을 프로젝트 brain에 자동 누적**.
  CLOSE 파일럿(opp 등)이 DONE.md 생성 직후 디스패치한다.
  brain(.opal/brain/)이 없는 프로젝트에서는 즉시 no-op(status: skipped)를 반환한다.
  반드시 이 스킬을 사용해야 하는 상황: CLOSE 단계 파일럿이 DONE.md 생성 후 brain ingest를 디스패치할 때.
version: "1.0"
domain: knowledge
dispatched_by: "CLOSE 단계 파일럿 (opp — 이후 확산 예정)"
---

# op-brain-ingest — CLOSE 경량 ingest 워커

## 역할

CLOSE 단계에서 디스패치되는 경량 워커다. 완료된 태스크의 의사결정·신규 컴포넌트·인터페이스 변경·도메인 지식을 `brain-tool`을 통해 `.opal/brain/`에 누적한다.

이 워커는 **단방향**이다 — brain 페이지 작성만 수행하며, 기존 코드·문서를 역수정하는 것은 절대 금지된다.

---

## 입력

- **태스크 폴더 경로** (DONE.md·PLAN.md·TASK.md가 있는 디렉토리)
- 예: `tasks/015-260610-opp-opal-brain/`

---

## 절차

### STEP 1 — brain 존재 확인

1. 태스크 폴더에서 프로젝트 루트를 추론한다 (태스크 폴더의 상위 디렉토리).
2. `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **없으면**: 즉시 `{ "ingested_pages": [], "status": "skipped", "summary": "brain 미존재 — no-op" }`를 반환하고 종료한다. CLOSE를 막지 않는다.
   - **있으면**: STEP 2로 진행한다.

### STEP 2 — 소스 Read

아래 순서로 파일을 Read한다. 없는 파일은 건너뛴다.

1. `DONE.md` — 완료 요약·최종 산출물 목록
2. `PLAN.md` — 의사결정(M-N/결정 N 형식 섹션)·핵심 설계 섹션
3. `TASK.md` — 요구사항·제약 조건

### STEP 3 — ingest 대상 판별

Read한 내용을 기준으로 아래 기준에 따라 ingest 대상·제외를 판별한다.

> **[SSOT] 백필 기준 재사용**: 아래 포함/제외 기준은 `opal-brain //opbr ingest task:NNN` 모드의 001~015 소급 백필(M-3)에서도 **동일하게 재사용**된다. 백필 판별 로직을 별도로 정의하지 않는다 — 이 절이 유일한 기준 SSOT다.

> **[동적 타입]**: 페이지 타입(`entity`, `concept`, `flow`, `synthesis` 등)은 `.opal/brain/templates/schema-template.md` §1.5 테이블에서 brain-tool이 동적 로드한다. 아래 테이블의 "페이지 타입" 열은 기본 4종 예시이며, brain이 커스텀 타입으로 초기화된 경우 해당 타입을 사용한다.

#### 포함 기준 (하나라도 충족 시 ingest)

| 기준 | 설명 | 페이지 타입 |
|------|------|-----------|
| 아키텍처 결정 | 설계 방향·패턴·접근법이 결정된 내용 (PLAN.md "결정 N" 섹션) | `concept` |
| 신규 컴포넌트 | 새로 생성된 도구·스킬·에이전트·참조 문서 | `entity` |
| 인터페이스 변경 | 서브커맨드·API·입출력 스펙 변경 | `entity` 또는 `concept` |
| 도메인 지식 | 프로젝트 WHY·HOW에 해당하는 인사이트·원칙 | `concept` |
| 흐름 변경 | 파이프라인·프로세스·단계 구조의 유의미한 변경 | `flow` |

#### 제외 기준 (ingest 불필요)

| 제외 사유 | 예시 |
|----------|------|
| 오타·포맷 수정 | 마크다운 공백, 줄바꿈, 오타 교정 |
| trivial 설정값 변경 | 버전 숫자 bump, 파일명 변경 |
| 이미 brain에 동일 내용이 존재 | 기존 페이지와 중복 (멱등 skip) |
| 임시·실험적 변경 | 되돌려진 변경, 파일럿 테스트 |

> 판별이 불확실한 경우 ingest하지 않고 STEP 6에서 이유를 명시한다.

### STEP 4 — concept/entity 페이지 작성

ingest 대상별로 brain 페이지 본문을 작성한다.

#### 페이지 작성 규칙

- **frontmatter 필수 키**: `type`, `title`, `created`, `updated`, `status`, `sources`
- **언어**: 본문 한국어, frontmatter 키·파일명 English
- **파일명**: `kebab-case.md`, `pages/{type}/` 하위에 저장
- **sources**: `task:<태스크번호>` 형식으로 출처 명시 (예: `task:015`)
- **코드 참조**: 코드 본문 복제 금지 — `` `file_path:line` `` 형식 참조만 허용
- **비즈니스 용어 우선**: 본문은 비즈니스 용어/자연어로 서술한다. 코드 식별자를 본문 주어로 나열 금지 — 괄호+`file_path:line` 근거로만 병기한다 (상세: `opal/core/references/harness/citation-rules.md` §8)
- **관련 링크**: `[[페이지파일명]]` 교차참조 사용

#### 페이지 구조 예시 (concept 타입 — 아키텍처 결정)

```markdown
---
type: concept
title: <결정 제목>
tags: [<관련 태그>]
sources: [task:<번호>]
related: [[<관련 페이지>]]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: active
---

## 개요

<결정 내용 1-2문장>

## 결정 배경 (WHY)

<왜 이 결정을 내렸는지 — PLAN.md 결정 섹션 요약>

## 결정 내용

<구체적 설계 방향·채택 근거>

## 영향 범위

<이 결정이 영향을 미치는 컴포넌트·파일>

## 관련 페이지

- [[<관련 페이지>]]
```

#### 페이지 구조 예시 (entity 타입 — 신규 컴포넌트)

```markdown
---
type: entity
title: <컴포넌트명>
tags: [<layer>, <domain>]
sources: [task:<번호>]
related: [[<관련 페이지>]]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: active
---

## 개요

<컴포넌트 역할 1-2문장>

## 설계 배경 (WHY)

<왜 이 컴포넌트가 필요한지>

## 인터페이스

<주요 입출력·서브커맨드·API — 코드 참조: `file_path:line`>

## 관련 페이지

- [[<관련 페이지>]]
```

### STEP 5 — brain-tool 호출

#### 5-1. 페이지별 add-page

작성한 각 페이지에 대해 brain-tool add-page를 호출한다:

```bash
~/.opal/tools/brain-tool/run.sh add-page pages/<type>/<kebab-name>.md \
  --type <entity|concept|flow|synthesis> \
  --title "<제목>" \
  --tags "<태그>" \
  --sources "task:<태스크번호>"
```

- `ok: false` → 에러 코드 확인. `duplicate_page`이면 멱등 skip(정상). 그 외는 에스컬레이션.

#### 5-2. index 갱신

모든 add-page 완료 후 **1회** index를 호출한다:

```bash
~/.opal/tools/brain-tool/run.sh index
```

#### 5-3. log 기록

```bash
~/.opal/tools/brain-tool/run.sh log \
  --op ingest \
  --summary "CLOSE ingest — 태스크 <번호> <태스크명>" \
  --new "<페이지1>,<페이지2>,..." \
  --sources "task:<태스크번호>"
```

### STEP 6 — 결과 반환

아래 형식으로 결과를 반환한다:

```json
{
  "ingested_pages": ["pages/concept/<name>.md", "pages/entity/<name>.md"],
  "status": "completed",
  "summary": "태스크 <번호> CLOSE ingest — concept <N>건, entity <M>건 누적"
}
```

brain 부재 시:

```json
{
  "ingested_pages": [],
  "status": "skipped",
  "summary": "brain 미존재 — no-op (프로젝트 루트: <경로>)"
}
```

---

## 집행 경계 ([MUST])

- `index.md` / `log.md`는 **brain-tool로만** 갱신한다. LLM이 직접 편집하는 것은 금지된다.
- brain → 코드·문서 역방향 수정은 **절대 금지**. 이 워커는 brain 페이지 작성 전용이다.
- CLOSE 단계를 막아서는 안 된다. brain 부재 또는 brain-tool 에러 발생 시 `status: skipped`로 안전 반환한다.
- 페이지 본문은 LLM이 작성하고, add-page/index/log 집행은 brain-tool이 전담한다.

---

## brain-tool 에러 대응

| 에러 코드 | 처리 |
|----------|------|
| `brain_not_initialized` | STEP 1에서 이미 체크 — 도달 불가. 만약 발생 시 `status: skipped` 반환 |
| `duplicate_page` | 멱등 skip — 정상. 해당 페이지를 `ingested_pages`에서 제외하고 계속 진행 |
| `invalid_page_type` | 타입 재검토 후 재시도. 실패 시 해당 페이지 건너뛰고 나머지 계속 진행 |
| `frontmatter_invalid` | 해당 페이지 frontmatter 수정 후 재시도. 실패 시 건너뛰기 |
| 그 외 `ok: false` | 에러 코드·detail을 summary에 기록하고 `status: completed_with_errors` 반환 |

> 어떤 에러도 CLOSE를 중단시키지 않는다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — CLOSE 경량 ingest 워커. brain 미존재 no-op, 포함/제외 기준, brain-tool add-page/index/log 절차, 에러 안전 처리 (015) |
| v1.1 | 2026-06-11 19:20 | STEP 3에 백필 기준 SSOT 재사용 명시(M-3) + 동적 타입 로드(SCHEMA §1.5) 정합 안내 추가 (016) |
| v1.2 | 2026-06-16 | STEP 4 작성 규칙에 비즈니스 용어 우선 불릿 추가 — citation-rules §8 참조 (024) |

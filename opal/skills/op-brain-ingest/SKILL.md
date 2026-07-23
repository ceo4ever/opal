---
name: op-brain-ingest
description: |
  **CLOSE 단계 경량 워커 — 태스크 산출물을 프로젝트 brain에 자동 누적**.
  CLOSE 파일럿(opp 등)이 DONE.md 생성 직후 디스패치한다.
  brain(.opal/brain/)이 없는 프로젝트에서는 즉시 no-op(status: skipped)를 반환한다.
  반드시 이 스킬을 사용해야 하는 상황: CLOSE 단계 파일럿이 DONE.md 생성 후 brain ingest를 디스패치할 때.
version: "1.3"
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

> **[MUST] term 채택 게이트**: `term` 타입은 SCHEMA §1.5에 term이 채택된 프로젝트에서만 후보를 추출한다. term이 미채택된 프로젝트(순수 기술 레포 등)에서 term 추출을 시도하면 `invalid_page_type` SCHEMA 위반이 발생한다 — 미채택 시 term 추출을 수행하지 않는다. opal-brain `//opbr init` 채택 가이드와 연동한다.

#### 포함 기준 (하나라도 충족 시 ingest)

| 기준 | 설명 | 페이지 타입 |
|------|------|-----------|
| 아키텍처 결정 | 설계 방향·패턴·접근법이 결정된 내용 (PLAN.md "결정 N" 섹션) | `concept` |
| 신규 컴포넌트 | 새로 생성된 도구·스킬·에이전트·참조 문서 | `entity` |
| 인터페이스 변경 | 서브커맨드·API·입출력 스펙 변경 | `entity` 또는 `concept` |
| 도메인 지식 | 프로젝트 WHY·HOW에 해당하는 인사이트·원칙 | `concept` |
| 흐름 변경 | 파이프라인·프로세스·단계 구조의 유의미한 변경 | `flow` |
| 신규 업무 용어·업무 표면 후보 | DONE.md·PLAN.md에 등장한 새 업무 용어·상태명·업무 접점 (term 타입 채택 프로젝트에서만) | `term` (status: draft) |

#### 제외 기준 (ingest 불필요)

| 제외 사유 | 예시 |
|----------|------|
| 오타·포맷 수정 | 마크다운 공백, 줄바꿈, 오타 교정 |
| trivial 설정값 변경 | 버전 숫자 bump, 파일명 변경 |
| 이미 brain에 동일 내용이 존재 | 기존 페이지와 중복 (멱등 skip) |
| 임시·실험적 변경 | 되돌려진 변경, 파일럿 테스트 |
| 미실체 지식 — 아직 실재하지 않는 것 | 개선사항·오류·향후 계획·미확정 설계, 착수 전 설계 기록, 미해결 이슈 → brain 아니라 memory로 (활용은 memory에서) |

> **판별 신호**: 구조적 신호(섹션 헤딩·전용 섹션)에 미실체 마커가 있으면 제외한다. 정상 지식이 산문에서 "향후"를 단순 언급하는 경우는 제외하지 않는다(오검출 최소화). brain-tool `add-page`(`--body-file`)·`lint`(`speculative` kind)가 이를 결정론적으로 집행한다.
>
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
- **소유자 지칭 일반화(오염 금지)**: 지식 본문에서 소유자를 지칭할 때는 역할 일반어('소유자')만 사용한다. 특정인 호칭·이름이나 로드된 레포 컨텍스트(MEMORY·직전 태스크 산출물)의 지배 호칭을 계승하지 않는다. 출처(DONE.md 등)가 특정 호칭을 쓰더라도 지식에는 '소유자'로 일반화한다. (이 워커는 부트스트랩을 스킵하므로 이 규칙을 본 SKILL.md에서 직접 적용한다.)

#### term 페이지 작성 규칙 (term 타입 채택 프로젝트 전용)

> **[MUST]**: term 페이지는 반드시 `status: draft`로 등록한다. draft 상태는 답변 검색에 노출되지 않으며, 소유자/PM 확정 후 `active`로 승격한다.

- **frontmatter 선택 키**: 아래 3종을 적절히 추가한다 (필수 키 type/title/created/updated/status/sources는 기존 §2.1 공통 규칙 준수).

  | 키 | 타입 | 설명 |
  |----|------|------|
  | `aliases` | string[] | 별칭·동의 표현 (검색 보강 및 alias_collision lint 대상) |
  | `actors` | string[] | 업무 행위자 (예: PM, 운영자, 구매자) |
  | `surfaces` | string[] | 업무 표면 — 용어가 등장하는 화면·프로세스 |

- **본문**: 업무 의미를 2~4문장으로 서술한다. 비즈니스 용어 우선(코드 식별자를 본문 주어로 나열 금지). 기존 §8 비즈니스 용어 우선 불릿과 정합 (→ `opal/core/references/harness/citation-rules.md` §8).
- **다층 근거 `sources`**: 코드참조(`file_path:line`)만이 아닌 정책참조(`POL-{번호}`)·IA참조(`ia:{system}:{screen}`)를 병기하여 다층 근거를 구성한다 (형식은 brain SCHEMA §4 링크 규칙 참조).
- **파일명·경로**: `pages/term/<kebab-term-name>.md`

#### term 페이지 구조 예시

```markdown
---
type: term
title: <업무 용어명>
aliases: [<별칭1>, <별칭2>]
actors: [<행위자1>]
surfaces: [<화면·프로세스1>]
tags: [<관련 태그>]
sources: [task:<번호>, POL-<번호>]
related: [[<관련 페이지>]]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: draft
---

<업무 의미 2~4문장. 비즈니스 언어로 서술. 코드 식별자는 `경로:줄번호` 근거로만 병기.>

## 관련 페이지

- [[<관련 페이지>]]
```

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

> **[MUST] @header 전사 금지**: code-scan @header(module/layer/domain/exports)를 본문 1~4섹션에 기계 복사하지 않는다. @header 필드는 frontmatter와 §소스 커버리지(부록)에만 둔다. 본문은 사고하여 합성한다.
>
> **[MUST] provenance 3종**: `## 설계 배경 (WHY)`의 각 주장 문장에 아래 3종 중 하나를 태깅한다.
> - `(근거: <doc>/POL-N/task:NNN PLAN§X)` — 문서·정책·태스크에서 확인된 WHY
> - `(추론: 코드패턴)` — 코드 구조에서 추론한 WHY (단정 금지)
> - `(WHY 미확보)` — WHY 입력이 없어 미확보 (솔직 표기 — 날조 금지)
>
> **[MUST] §8.9 비위반**: 5섹션 헤딩은 `## 누가/왜/어떻게` 형식이 아닌 도메인 의미 헤딩 + 괄호 보조 레이블(WHAT/WHY/HOW) 형식이다 — citation-rules §8.9 비위반.

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

<비즈니스 프레이밍 — 이 엔티티가 무엇이고 왜 존재하는지 1~3문장. 비즈니스 용어 우선. 코드 식별자 본문 주어 금지 (citation-rules §8.2)>

## 책임 (WHAT)

<노출 인터페이스·책임을 기능 단위로 서술. 각 책임에 `file_path:line` 인용 병기 (citation-rules §8.4)>

## 설계 배경 (WHY)

<왜 이렇게 설계했는가 — 결정·기각된 대안·맥락. 각 주장에 provenance 3종 중 하나 태깅 [MUST]. HOW 누수 금지(관계 서술은 §관계로). 5W1H는 사고틀로만 (citation-rules §8.9)>

## 관계 (HOW)

<의존·피의존·협력 엔티티. wikilink [[페이지명]] 사용>

- [[<관련 페이지>]]

## 소스 커버리지

<코드 식별자·enum·exports를 부록으로 분리. line number 포함 `file_path:line` 표. 본문(1~4)에서 강등 배치 (citation-rules §8.8)>

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `<식별자>` | `<file_path:line>` | <설명> |
```

### STEP 5 — brain-tool 호출

#### 5-1. 페이지별 add-page

작성한 각 페이지에 대해 brain-tool add-page를 호출한다. **STEP 4에서 작성한 본문을 스크래치 파일로 저장하고 `--body-file`로 넘겨야 도구가 실제 본문을 스캔한다** (미지정 시 템플릿 본문만 기록되어 미실체 게이트가 발동하지 않는다):

```bash
~/.opal/tools/brain-tool/run.sh add-page pages/<type>/<kebab-name>.md \
  --type <entity|concept|flow|synthesis> \
  --title "<제목>" \
  --tags "<태그>" \
  --sources "task:<태스크번호>" \
  --body-file <본문 파일 경로 — STEP4에서 작성한 페이지 본문을 저장한 스크래치 .md>
```

- `ok: false` → 에러 코드 확인. `duplicate_page`이면 멱등 skip(정상). `speculative_content`이면 §brain-tool 에러 대응 표에 따라 skip-and-continue. 그 외는 에스컬레이션.

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
| `speculative_content` | 미실체 마커 감지 거부. 해당 페이지를 건너뛰고 나머지 계속 진행(skip-and-continue). **CLOSE 비차단** |
| 그 외 `ok: false` | 에러 코드·detail을 summary에 기록하고 `status: completed_with_errors` 반환 |

> 어떤 에러도 CLOSE를 중단시키지 않는다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — CLOSE 경량 ingest 워커. brain 미존재 no-op, 포함/제외 기준, brain-tool add-page/index/log 절차, 에러 안전 처리 (015) |
| v1.1 | 2026-06-11 19:20 | STEP 3에 백필 기준 SSOT 재사용 명시(M-3) + 동적 타입 로드(SCHEMA §1.5) 정합 안내 추가 (016) |
| v1.2 | 2026-06-16 | STEP 4 작성 규칙에 비즈니스 용어 우선 불릿 추가 — citation-rules §8 참조 (024) |
| v1.3 | 2026-06-17 | CLOSE ingest term 추출 — STEP3 채택 게이트(채택 프로젝트만) + 포함 기준에 term draft 행 추가 + STEP4 term 작성 규칙(aliases/actors/surfaces·draft) (027) |
| v1.4 | 2026-06-23 | STEP 4 entity 예시 5섹션 표준화 + @header 전사 금지·provenance [MUST] (038) |
| v1.5 | 2026-07-10 13:43 | 소유자 호칭 오염 차단 — term 페이지 승격 문구의 특정인 호칭을 "소유자/PM"으로 역할 일반어화 + 페이지 작성 규칙에 "소유자 지칭 일반화(오염 금지)" 불릿 신설(지식 본문은 항상 '소유자'로 일반화, 출처의 개인 호칭 계승 금지) (054) |
| v1.6 | 2026-07-23 10:15 | 미실체 지식 등록 차단 게이트 SSOT — §STEP3 제외 기준 표에 "미실체 지식" 행 + 판별 신호(구조적 헤딩 우선, 오검출 최소화) 추가, brain-tool 에러 대응 표에 `speculative_content`(skip-and-continue, CLOSE 비차단) 행 추가, STEP5-1 add-page 예시에 `--body-file` 인자 반영(실제 본문 스캔) (071) |

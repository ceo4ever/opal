---
name: opal-brain
description: |
  **프로젝트 브레인 — 영속 지식 위키 생성·누적·질의·정비**. 프로젝트의 WHY·HOW 지식을 마크다운 네이티브 위키로 누적하고 PM·워커가 참조할 수 있게 한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-brain", "opbr", "프로젝트 브레인", "지식 위키".
  모드: init | ingest | query | lint. 모드 미지정 시 PM이 의도를 판별한다.
alias: opbr
triggers:
  - "^opbr$"
  - "^opal-brain$"
  - "(?i)(프로젝트\\s*브레인|지식\\s*위키)"
version: "1.0"
domain: knowledge
pipeline: "MODE: init | ingest | query | lint"
---

# opal-brain (프로젝트 브레인)

## Harness

이 스킬은 단일 pilot 구조다. 하네스 부트스트랩에서 로드되지 않은 경우:
- `~/.opal/references/opal-harness.md` Read.

모드 라우팅 후 brain-tool은 `~/.opal/tools/brain-tool/run.sh`로 호출한다. 출력이 `"ok": false`이면 `"error"` 필드를 확인하여 사용자에게 에스컬레이션한다.

---

## 모드 라우팅

첫 인자(또는 호출 문구)에서 모드를 판별한다.

| 트리거 | 라우팅 대상 |
|--------|------------|
| `//opbr init` | [STEP: init](#step-init--brain-부트스트랩) |
| `//opbr ingest <소스>` | [STEP: ingest](#step-ingest--지식-누적) |
| `//opbr ingest --all` | [STEP: ingest](#step-ingest--지식-누적) — `--all` 배치 모드 |
| `//opbr ask "질문"` / `//opbr query` | [STEP: query](#step-query--지식-질의) |
| `//opbr lint` | [STEP: lint](#step-lint--무결성-정비) |
| 모드 미지정 | PM이 의도를 판별하여 가장 적합한 모드 제안 |

> 모드 미지정 예시: "//opbr opal-brain이 어떻게 동작해?" → PM이 query 모드로 라우팅 제안.

---

## STEP: init — brain 부트스트랩

> **프로젝트당 1회**. 이미 `.opal/brain/`이 존재하면 `brain_already_initialized` 에러로 거부한다. 재초기화는 `--force`로만 가능하다.

### 전제 확인

1. `.opal/code-scan.json` 존재 여부 확인.
   - 없으면: "init을 실행하려면 `.opal/code-scan.json`이 필요합니다. `code-scan-management.md` §생성 시점을 참고해 먼저 생성해주세요." 보고 후 중단.

### brain 골격 생성

2. brain-tool init 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh init <프로젝트-루트>
   ```
   - `ok: false` → 에러 보고 후 중단.
   - 생성 결과(`created`, `schema_written`) 확인.

### 핵심 엔티티 시드 (결정4 임계값)

3. code-scan.json을 Read하여 @header 목록을 파악한다.
4. 아래 **시드 선별 기준** 중 하나라도 충족하는 모듈에 대해 entity 페이지를 생성한다.

| 기준 | 임계값 | 설명 |
|------|--------|------|
| exports 수 | `exports` ≥ 3 | 인터페이스 면적이 큰 모듈 |
| 피의존도 | 다른 모듈 ≥ 2개가 의존 | 허브 역할 모듈 |
| 레이어 | `layer` ∈ {orchestrator, tool, pilot, core} | 오케스트레이터·도구·파일럿은 무조건 시드 |
| 도메인 대표 | 각 `domain`당 최소 1개 | 도메인 조망 보장 |

> 4기준 **모두 미충족** → index.md 카탈로그에만 등록(페이지 미생성). lazy 전략.

5. 선별된 각 모듈에 대해 entity 페이지 작성 후 brain-tool add-page 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh add-page pages/entity/<module-name>.md \
     --type entity --title "<모듈명>" \
     --tags "<layer>,<domain>" \
     --sources "code:<source_ref>"
   ```
   - 페이지 본문에 @header 필드(module/layer/domain/exports/source_ref/header_synced) 시드.
   - 본문 구조: `## 개요`, `## 설계 배경 (WHY)`, `## 인터페이스`, `## 관련 페이지`.

6. 전체 맵 index 등록:
   ```bash
   ~/.opal/tools/brain-tool/run.sh index
   ```

7. init log 기록:
   ```bash
   ~/.opal/tools/brain-tool/run.sh log \
     --op init \
     --summary "brain 부트스트랩 — 핵심 엔티티 <N>개 시드" \
     --new "<entity1>,<entity2>,..."
   ```

### --scope / --full / --ingest-all 옵션

| 옵션 | 동작 |
|------|------|
| `//opbr init` (기본) | 전체 맵 + 결정4 임계값 핵심 엔티티 시드 |
| `//opbr init --scope <도메인/레이어>` | 해당 범위 모듈만 시드 |
| `//opbr init --full` | 임계값 무시 — 모든 @header를 entity 페이지로 시드 (골격만, 얕음) |
| `//opbr init --ingest-all` | init 직후 ingest --all 자동 실행 (깊은 분석, 비용 큼 — 사용자 확인 후 실행) |

### init 완료 보고

```
[brain init] 완료
.opal/brain/ 골격 생성됨
핵심 엔티티 시드: <N>개 / 전체 모듈 <M>개
index.md 전체 맵 등록 완료
```

---

## STEP: ingest — 지식 누적

소스(코드/문서/외부 URL/파일)를 읽어 요약 페이지를 작성하고 index·log를 갱신한다.

### 소스 유형별 처리

| 소스 유형 | 처리 방법 |
|----------|----------|
| **내부 코드** | @header 흡수 + `file_path:line` 참조. 코드 본문 복제 금지 — 코드가 SSOT |
| **내부 문서** (docs/*.md) | 개념 페이지에서 `[[]]` 참조, 필요 시 요약 — docs가 SSOT |
| **외부 URL** | web-to-markdown 스킬(`//wtm`) → `sources/<id>/raw.md` + `meta.yaml` 저장 후 요약 페이지 |
| **파일** (PDF/xlsx/이미지) | xlsx-tool 또는 Read 도구 → `sources/<id>/raw.md` + `meta.yaml` 저장 후 요약 페이지 |

> **[MUST] 단방향 동기화**: brain에서 코드·문서를 역방향으로 수정하는 것은 금지된다. brain은 참조·요약·WHY만 담는다.

### 단일 소스 ingest 절차

1. 소스 Read / 변환 (외부 소스는 wtm/xlsx-tool 사용).
2. 외부 소스인 경우: `sources/<source-id>/raw.md` + `sources/<source-id>/meta.yaml` 저장.
   - `meta.yaml` 필수 필드: `url`, `collected_at`, `license`.
3. 페이지 타입 결정: entity / concept / flow / synthesis.
4. 페이지 본문 작성 (LLM 담당) — frontmatter 포함.
5. brain-tool add-page 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh add-page pages/<type>/<name>.md \
     --type <type> --title "<제목>" \
     --tags "<태그>" --sources "<출처>"
   ```
6. log 기록:
   ```bash
   ~/.opal/tools/brain-tool/run.sh log \
     --op ingest --summary "<요약>" \
     --new "<페이지명>" --sources "<출처>"
   ```

### ingest --all 배치 정책 (결정5)

`//opbr ingest --all [--scope <도메인/레이어>]` 호출 시:

| 항목 | 정책 |
|------|------|
| 배치 크기 | **5 자산/배치** — 하네스 §7 병렬 한도 준수 |
| 멱등 skip 판정 | `(source_ref, header_synced)` 쌍 — 이미 최신 상태이면 skip |
| 진행률 보고 | 배치별 `{done:N, total:M, skipped:K}` 누적 출력 |
| 재개 메커니즘 | log.md 배치 완료 마커 → 중단 후 재실행 시 멱등 skip 자동 재개 |
| index 원자화 | LLM은 페이지만 작성, `brain-tool index`는 전체 배치 완료 후 **1회** 실행 |

> `--ingest-all` 전체 실행 전 사용자 확인 요청 필수 (비용·시간 명시).

---

## STEP: query — 지식 질의

brain에 축적된 지식으로 질문에 답한다.

### 질의 절차

1. brain-tool search로 관련 페이지 탐색:
   ```bash
   ~/.opal/tools/brain-tool/run.sh search "<질문 키워드>" [--type T] [--tag X] [--limit 10]
   ```
2. 반환된 `matches` 중 관련도 높은 페이지를 Read한다.
3. 페이지 내용 + 인용(출처 명시)으로 답변을 합성한다.
4. 답변 품질 평가:
   - 새로운 인사이트를 담는 **가치 있는 답**이면 → synthesis 페이지로 파일링 제안.
   - 단순 정보 재조합이면 → 파일링 생략.

### synthesis 페이지 파일링 제안 형식

```
이 답변을 synthesis 페이지로 저장할까요?
제안 파일명: pages/synthesis/<kebab-name>.md
제목: "<질의에서 파생된 분석 제목>"
```

사용자 승인 시 brain-tool add-page + log 호출로 파일링한다.

### query log 기록

```bash
~/.opal/tools/brain-tool/run.sh log \
  --op query --summary "<질문 요약>" \
  [--new "<synthesis 페이지명>"]
```

---

## STEP: lint — 무결성 정비

brain의 품질 문제를 탐지하고 정비 방안을 제안한다.

### lint 절차

1. brain-tool lint 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh lint [--brain-path .opal/brain]
   ```
2. 반환된 `issues` 목록을 유형별로 분류하여 리포트한다.

| issue kind | 설명 | 권고 조치 |
|------------|------|----------|
| `orphan` | 다른 페이지에서 참조되지 않는 고아 페이지 | 관련 페이지에 링크 추가 또는 삭제 |
| `stale` | `header_synced`가 code-scan 최신 시각보다 오래된 entity | `sync-header` 실행 |
| `broken_link` | `[[링크]]`가 존재하지 않는 페이지를 참조 | 링크 수정 또는 대상 페이지 생성 |
| `missing_link` | 관련 페이지가 있으나 링크 누락 | `related` frontmatter 추가 |
| `unsourced` | `sources` frontmatter 없이 주장하는 페이지 | 출처 추가 또는 draft 상태로 강등 |
| `contradiction` | 서로 다른 페이지에서 모순되는 내용 | 검토 후 최신 정보 반영 |

3. 이슈 건수 요약 후 사용자에게 정비 제안:
   ```
   [brain lint] 결과
   orphan: N건 / stale: N건 / broken_link: N건 / ...
   우선 정비 권고: <상위 이슈 설명>
   정비를 진행할까요?
   ```
4. 사용자 승인 시 이슈별 정비 실행 (페이지 수정·링크 추가·stale 해소 등).
5. 정비 완료 후 `brain-tool index` + `brain-tool log --op lint` 호출.

---

## 공통 규칙

### 집행 경계 ([MUST])

- `index.md` / `log.md`는 **brain-tool로만** 갱신한다. LLM이 직접 편집하는 것은 금지된다.
- 페이지 본문은 LLM이 작성하며, 인덱싱·log append·frontmatter 검증은 도구가 전담한다.
- @header → brain 단방향 동기화만 허용. brain → 코드 역방향 수정은 **절대 금지**.

### brain 부재 시 안전 처리

`.opal/brain/` 디렉토리가 없는 프로젝트에서 ingest/query/lint 호출 시:
```
이 프로젝트에 brain이 아직 초기화되지 않았습니다.
`//opbr init`을 먼저 실행해주세요.
```
에러 없이 no-op 반환한다.

### 언어 규칙 ([MUST])

- 페이지 본문: 한국어
- frontmatter 키·파일명·디렉토리명: English
- 파일명: kebab-case.md (`pages/entity/state-tool.md`)

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — 단일 pilot + 4모드(init/ingest/query/lint), 결정4 임계값·결정5 배치정책·결정7 SCHEMA 기반 (015) |

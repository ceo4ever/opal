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
version: "1.5"
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
| `//opbr query --read-only "<질의>"` | [STEP: query — 비대화형 read-only 모드](#비대화형-read-only-모드-opbr-query---read-only) — 기계 소비자(콘솔·자동화) 전용 |
| `//opbr lint` | [STEP: lint](#step-lint--무결성-정비) |
| 모드 미지정 | PM이 의도를 판별하여 가장 적합한 모드 제안 |

> 모드 미지정 예시: "//opbr opal-brain이 어떻게 동작해?" → PM이 query 모드로 라우팅 제안.

---

## STEP: init — brain 부트스트랩

> **프로젝트당 1회**. 이미 `.opal/brain/`이 존재하면 `brain_already_initialized` 에러로 거부한다. 재초기화는 `--force`로만 가능하다.

### STEP 0 — origin 분석·타입 제안·SCHEMA 확정

> **[MUST] (M-1 B안 채택)** init 시작 전 반드시 수행한다. 결정론적 작업(통계 집계)은 brain-tool이 담당하고, LLM은 그 결과 위에서 의미 판단만 수행한다.

**0-1. origin 정량 집계:**
```bash
~/.opal/tools/brain-tool/run.sh analyze [--brain-path <프로젝트-루트>]
```
반환 JSON에는 domain별 모듈 수·layer 분포·exports 합계·피의존도·seed_candidates 목록이 포함된다.

**0-2. 분석 결과 위에서 LLM이 타입 세트·도메인·index 카테고리·핵심 시드 대상을 제안한다:**

| 제안 항목 | 근거 |
|----------|------|
| 타입 세트 | 기본 4종(entity/concept/flow/synthesis)을 검토 후보로 제시. origin에 `layer:pilot` 또는 `layer:orchestrator`가 존재하면 `flow` 채택 강제. `docs/proposals/` 또는 `docs/ARCHITECTURE.md`가 존재하면 `concept` 채택 강제. **`term` 타입**: 비즈니스 도메인 프로젝트(POL/IA/도메인 업무 용어가 존재하는 프로젝트)면 채택 제안, 순수 기술 레포면 제외. op-brain-ingest 채택 게이트와 연동 — term 미채택 시 CLOSE ingest에서 draft term 추출 안 함. 그 외 신규 타입은 origin 특성 근거와 함께 제안 |
| index 카테고리 | analyze JSON의 domain 집계 → 모듈 ≥ 1개인 모든 domain을 index 카테고리 후보로 제시 |
| 핵심 시드 대상 | `exports ≥ 3` OR `피의존도 ≥ 2` OR `layer ∈ {orchestrator, tool, pilot, core}` OR `domain 대표 1개` — analyze JSON의 `seed_candidates` 활용 |

사용자에게 제안 내용을 제시하고 확인을 받는다:
```
[brain init] origin 분석 완료
─────────────────────────────
도메인: <domain1>(<N>개 모듈), <domain2>(<M>개 모듈), ...
레이어 분포: orchestrator(<N>), tool(<M>), ...
시드 후보: <module1>, <module2>, ...

제안 타입 세트: entity, concept, flow, synthesis
  * flow: layer:orchestrator 존재 → 강제 채택
  * 신규 타입 제안 없음

제안 index 카테고리: <domain1>, <domain2>, ...
제안 핵심 시드: <module1>(exports=5), <module2>(layer:orchestrator), ...

이 구성으로 SCHEMA를 확정하고 brain을 초기화할까요? (수정 원하시면 타입 목록·카테고리·시드를 알려주세요)
```

**0-3. 사용자 확인 후, 확정 타입 세트를 `--types`로 전달하여 SCHEMA 확정 및 골격 생성:**
```bash
~/.opal/tools/brain-tool/run.sh init <프로젝트-루트> --types <csv-타입-목록>
```
- 예: `--types entity,concept,flow,synthesis`
- 미지정 시 DEFAULT_PAGE_TYPES(기본 4종) 사용.
- `ok: false` → 에러 보고 후 중단.
- 생성 결과(`created`, `schema_written`) 확인.

### 전제 확인

1. `.opal/code-scan.json` 존재 여부 확인.
   - 없으면: "init을 실행하려면 `.opal/code-scan.json`이 필요합니다. `code-scan-management.md` §생성 시점을 참고해 먼저 생성해주세요." 보고 후 중단.
   - code-scan.json이 존재하면 STEP 0을 실행한다.
   - 부재 시 STEP 0의 analyze를 건너뛰고 타입 세트를 사용자에게 직접 확인한다(폴백).

### brain 골격 생성

2. STEP 0-3에서 `brain-tool init --types <csv>` 호출 완료 (위에서 수행).

### 핵심 엔티티 시드 (결정4 임계값)

3. STEP 0의 analyze `seed_candidates`를 사용한다. (code-scan.json 재Read 불필요)
4. 아래 **시드 선별 기준** 중 하나라도 충족하는 모듈에 대해 entity 페이지를 생성한다.

| 기준 | 임계값 | 설명 |
|------|--------|------|
| exports 수 | `exports` ≥ 3 | 인터페이스 면적이 큰 모듈 |
| 피의존도 | 다른 모듈 ≥ 2개가 의존 | 허브 역할 모듈 |
| 레이어 | `layer` ∈ {orchestrator, tool, pilot, core} | 오케스트레이터·도구·파일럿은 무조건 시드 |
| 도메인 대표 | 각 `domain`당 최소 1개 | 도메인 조망 보장 |

> 4기준 **모두 미충족** → index.md 카탈로그에만 등록(페이지 미생성). lazy 전략.

5. 선별된 각 모듈에 대해 entity 페이지 작성 후 brain-tool add-page 호출 (add-page 직전 §공통 규칙 > **코드→브레인 저술 자기검토 게이트** 4항목 통과 확인):
   ```bash
   ~/.opal/tools/brain-tool/run.sh add-page pages/entity/<module-name>.md \
     --type entity --title "<모듈명>" \
     --tags "<layer>,<domain>" \
     --sources "code:<source_ref>"
   ```

   **[MUST] 입력 큐레이션 선행** (entity 본문 작성 전):
   1. `docs/PROJECT.md` 문서 레지스트리에서 해당 모듈 관련 docs 확인.
   2. 관련 태스크 `tasks/NNN/PLAN.md`(설계 결정) 확인 — git 커밋 메시지 태스크 번호로 역추적 가능.
   3. 관련 기존 brain 페이지(concept/entity) 후보 확인.
   4. 위 입력에서 WHY를 합성. 없으면 `(추론: 코드패턴)` 또는 `(WHY 미확보)`로 솔직 표기.

   **[MUST] @header 전사 금지**: code-scan @header(module/layer/domain/exports)를 본문 1~4섹션에 기계 복사하지 않는다. @header 필드는 frontmatter와 §소스 커버리지(부록)에만 둔다. 본문은 사고하여 합성한다.

   **entity 본문 5섹션 표준** (§8.9 비위반 — 주 헤딩은 도메인 의미 헤딩이며 괄호는 보조 레이블이므로 `## 누가/왜/어떻게` 형식 금지 대상이 아님):

   | # | 섹션 헤딩 | 역할 | 작성 규율 |
   |---|----------|------|----------|
   | 1 | `## 개요` | 비즈니스 프레이밍 1~3문장 | 비즈니스 용어 우선. 코드 식별자 본문 주어 금지 (§8.2) |
   | 2 | `## 책임 (WHAT)` | 노출 인터페이스·책임을 기능 단위로 서술 | 각 책임에 `` `file_path:line` `` 인용 병기 |
   | 3 | `## 설계 배경 (WHY)` | 결정·기각된 대안·맥락 | **[MUST] provenance 3종 태깅** (아래). HOW 누수 금지. 5W1H는 사고틀로만 |
   | 4 | `## 관계 (HOW)` | 의존·피의존·협력 엔티티 | wikilink `[[페이지명]]` 사용 |
   | 5 | `## 소스 커버리지` | 코드 식별자·enum·exports 부록 분리 | line number 포함 `` `file_path:line` `` 표 (§8.8) |

   **[MUST] provenance 3종** — `## 설계 배경 (WHY)` 각 주장 문장은 아래 3종 중 하나를 반드시 태그한다:

   | 태그 | 의미 | 사용 조건 |
   |------|------|----------|
   | `(근거: <doc>/POL-N/task:NNN PLAN§X)` | 문서·정책·태스크에서 확인된 WHY | 큐레이션된 입력에 WHY 출처가 있을 때 |
   | `(추론: 코드패턴)` | 코드 구조에서 추론한 WHY (직접 근거 없음) | 코드만으로 합리적 추론 시 — 단정 금지 |
   | `(WHY 미확보)` | WHY 입력이 없어 미확보 | 솔직 표기 — 날조 금지 |

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
| `//opbr init` (기본) | STEP 0 분석→확인 후 확정 타입으로 골격 생성 + 결정4 임계값 핵심 엔티티 시드 |
| `//opbr init --scope <도메인/레이어>` | 해당 범위 모듈만 시드 |
| `//opbr init --full` | 임계값 무시 — 모든 @header를 entity 페이지로 시드 (골격만, 얕음) |
| `//opbr init --ingest-all` | init 직후 ingest --all 자동 실행 (깊은 분석, 비용 큼 — 사용자 확인 후 실행) |

### init 완료 보고

```
[brain init] 완료
.opal/brain/ 골격 생성됨
확정 타입 세트: <type1>, <type2>, ...
핵심 엔티티 시드: <N>개 / 전체 모듈 <M>개
index.md 전체 맵 등록 완료
```

### 재생성 런북 (brain 전체 재시드)

기존 entity 페이지 품질이 낮아 개선된 5섹션 규율로 전체 재생성이 필요할 때 사용한다.

① 백업: `.opal/brain/pages/synthesis/` + 수기 편집 페이지를 별도 경로로 복사
   (⚠️ synthesis는 query 파생물 — ingest-scan 미대상이라 init로 복구 불가 → 유실 방지 필수)

② 삭제: `.opal/brain/pages/entity/` 직접 삭제 (entity만 재생성) 또는 `.opal/brain/` 전체 삭제
   ⚠️ `//opbr init --force` 만으로는 `pages/`가 보존되어 재생성되지 않는다 (`brain_tool.py:436-440` `exist_ok=True`)

③ 재생성: `//opbr init` (개선된 5섹션 규율 적용)  [+ 필요 시 `ingest --all`로 concept 재생성]

④ 복원: 백업한 `synthesis/` + 수기 페이지를 `.opal/brain/pages/`로 복원

---

## STEP: ingest — 지식 누적

소스(코드/문서/외부 URL/파일/태스크)를 읽어 요약 페이지를 작성하고 index·log를 갱신한다.

> **[MUST] 단방향 동기화 — origin→wiki 읽기만. wiki→origin 역수정 금지.** (TASK §제약 인용)
>
> **[MUST] 복사 아닌 요약+참조 — 내부 문서/코드는 포인터, 외부 소스만 sources/ 원본.** (TASK §제약 인용)

### 소스 유형별 처리

| 소스 유형 | 처리 방법 |
|----------|----------|
| **내부 코드** | @header 흡수 + `file_path:line` 참조. 코드 본문 복제 금지 — 코드가 SSOT |
| **내부 문서** (docs/*.md / 스킬·참조) | **3~6줄 요약(목적·핵심 결정·적용 범위) + `file_path` 포인터**. 본문 복제 금지 — 원본 파일이 SSOT |
| **태스크** (`tasks/NNN/`) | DONE.md·PLAN.md·TASK.md 읽기 → concept 1개 (핵심 결정). `sources:[task:NNN]` 형식 |
| **외부 URL** | web-to-markdown 스킬(`//wtm`) → `sources/<id>/raw.md` + `meta.yaml` 저장 후 요약 페이지 |
| **파일** (PDF/xlsx/이미지) | xlsx-tool 또는 Read 도구 → `sources/<id>/raw.md` + `meta.yaml` 저장 후 요약 페이지 |

### 단일 소스 ingest 절차

1. 소스 Read / 변환 (외부 소스는 wtm/xlsx-tool 사용).
2. 외부 소스인 경우: `sources/<source-id>/raw.md` + `sources/<source-id>/meta.yaml` 저장.
   - `meta.yaml` 필수 필드: `url`, `collected_at`, `license`.
3. 페이지 타입 결정: entity / concept / flow / synthesis (또는 SCHEMA에서 확정한 타입).
4. 페이지 본문 작성 (LLM 담당) — frontmatter 포함. **작성 후 §공통 규칙 > 코드→브레인 저술 자기검토 게이트 4항목 통과 확인** (위반 시 재작성).
5. brain-tool add-page 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh add-page pages/<type>/<name>.md \
     --type <type> --title "<제목>" \
     --tags "<태그>" --sources "<출처>"
   ```
   > **[MUST] source_ref 형식**: add-page `--sources` 값은 `brain-tool ingest-scan`이 반환한 `source_ref` 필드 값을 **그대로** 사용한다 (예: `doc:docs/ARCHITECTURE.md`, `skill:op-task-plan`, `task:016`). 임의 형식(전체 경로 등)으로 기재하면 멱등 skip 판정이 깨진다.
6. log 기록:
   ```bash
   ~/.opal/tools/brain-tool/run.sh log \
     --op ingest --summary "<요약>" \
     --new "<페이지명>" --sources "<출처>"
   ```

### ingest --all 배치 정책 (결정5 + M-2 확장)

`//opbr ingest --all [--scope <도메인/레이어>]` 호출 시:

**스캔 목록 획득 — 결정론적 작업은 brain-tool 전담:**
```bash
~/.opal/tools/brain-tool/run.sh ingest-scan --source all
```
반환 목록에는 docs/.md·스킬·참조·tasks/NNN 각각의 `path`·`type`·`skip`(멱등 판정) 필드가 포함된다. `skip:true` 항목은 건너뛴다.

**소스별 LLM 처리 깊이 (M-2 B안):**

| 소스 범주 | 페이지 타입 | 본문 깊이 |
|----------|-----------|---------|
| `docs/*.md` | concept | **3~6줄 요약(목적·핵심 결정·적용 범위) + `file_path` 포인터** |
| `opal/skills/**` | concept | **3~6줄 요약 + `file_path` 포인터** |
| `opal/*/references/**` | concept | **3~6줄 요약 + `file_path` 포인터** |
| 코드 @header | — | **ingest --all 미해당** — entity는 `//opbr init` 시드 경로에서만 생성됨. ingest-scan은 docs/skills/tasks→concept만 스캔하며 코드→entity 분기가 없다 (`brain_tool.py:1082-1135`) |
| 신규 업무 용어·상태·업무 표면 후보 | term (`status: draft`) | **업무 의미 2~4문장 + `aliases`/`actors`/`surfaces` frontmatter 선택 키 + 다층 근거 `sources` 병기**. [MUST] term 타입이 채택된 프로젝트에서만 추출(미채택 프로젝트는 건너뜀). [MUST] draft 페이지는 답변에 쓰지 않으며, 캡틴/PM 확정 시 `active` 승격. |

**배치 정책:**

| 항목 | 정책 |
|------|------|
| 배치 크기 | **5 자산/배치** — 하네스 §7 병렬 한도 준수 |
| 멱등 skip 판정 | `brain-tool ingest-scan`의 `skip:true` 항목 제외 (결정론적 도구 판정). **[MUST] add-page `--sources` 값은 ingest-scan이 반환한 `source_ref` 그대로 사용** (예: `skill:op-task-plan`, `doc:docs/ARCHITECTURE.md`). 임의 형식 사용 시 멱등 skip이 깨진다. |
| 진행률 보고 | 배치별 `{done:N, total:M, skipped:K}` 누적 출력 |
| 재개 메커니즘 | log.md 배치 완료 마커 → 중단 후 재실행 시 멱등 skip 자동 재개 |
| index 원자화 | LLM은 페이지만 작성, `brain-tool index`는 전체 배치 완료 후 **1회** 실행 |

> `--all` 전체 실행 전 사용자 확인 요청 필수 (비용·시간 명시).

### ingest task:NNN 모드 + 001~015 백필

#### task:NNN 단일 태스크 ingest

`//opbr ingest task:NNN` 호출 시:

1. `tasks/NNN/` 디렉토리에서 순서대로 Read한다.
   - `DONE.md` → 완료 요약·최종 산출물
   - `PLAN.md` → 의사결정(M-N/결정 N 섹션)·핵심 설계
   - `TASK.md` → 요구사항·제약 조건
2. **포함/제외 기준** — `opal/skills/op-brain-ingest/SKILL.md` §STEP 3 기준을 재사용(SSOT):
   - **포함**: 아키텍처 결정·신규 컴포넌트·인터페이스 변경·도메인 지식·흐름 변경
   - **제외**: 오타/포맷 수정·trivial 설정값·이미 brain에 동일 내용 존재·임시/실험적 변경
3. 포함 판정 시 concept 페이지 1개 작성:
   - 본문: 핵심 결정 요약 (3~6줄) + `sources: [task:NNN]`
   - 파일명: `pages/concept/<kebab-task-summary>.md`
   - 작성 후 §공통 규칙 > 코드→브레인 저술 자기검토 게이트 4항목 통과 확인 (위반 시 재작성).
4. brain-tool add-page + log 호출:
   ```bash
   ~/.opal/tools/brain-tool/run.sh add-page pages/concept/<name>.md \
     --type concept --title "<태스크 핵심 결정 제목>" \
     --tags "task" --sources "task:<NNN>"
   ~/.opal/tools/brain-tool/run.sh log \
     --op ingest --summary "task:<NNN> 백필" \
     --new "<페이지명>" --sources "task:<NNN>"
   ```

#### 001~015 선별 백필 절차 (M-3 B안)

`//opbr ingest --all` 또는 별도 백필 명령 시 1회 실행. 단발 실행이므로 사용자 확인 후 진행한다.

1. `brain-tool ingest-scan --source tasks` 호출 → 001~015 태스크 목록 + 멱등 skip 판정 수신.
2. skip:false 태스크에 대해 **op-brain-ingest §STEP 3 포함/제외 기준** 적용:
   - DONE.md가 없는 태스크 → 제외 (완료 검증 불가).
   - 제외 기준(오타·trivial)에 해당하는 태스크 → 제외.
   - 포함 기준(아키텍처 결정·신규 컴포넌트 등)에 해당하는 태스크 → concept 페이지화.
3. 포함 태스크 목록을 사용자에게 제시하여 최종 확인 후 5자산/배치 정책으로 실행.
4. 백필 완료 후 `brain-tool index` 1회 실행.

---

## STEP: query — 지식 질의

brain에 축적된 지식으로 질문에 답한다.

> **[MUST] search는 후보 목록만 반환하고 선택된 페이지만 주입(RAG식 전량 로드 금지).** (TASK §제약 인용)
>
> `//opbr ask` = 사용자가 직접 페이지를 선택하는 대화형 모드.

### 질의 절차 (후보→선택→주입)

**0. [term 우선] brain-tool search로 관련 term 페이지 탐색 (draft 제외 — 기본 동작):**
```bash
~/.opal/tools/brain-tool/run.sh search "<질문 키워드>" --type term [--limit 5]
```
- term 타입이 채택된 프로젝트에서만 수행. 미채택이면 건너뜀.
- draft term은 기본 검색에서 제외된다(결정론적 필터, `--include-draft` 미사용). [MUST] 이 draft 제외는 brain-tool이 결정론적으로 집행한다.
- 매칭된 term이 있으면 해당 업무 언어를 우선 참조하여 답변을 업무 언어로 합성한다. [MUST] "업무 언어 번역"은 brain-tool이 강제하지 못하는 **advisory LLM 행동**이다 — 규칙 준수는 LLM 스스로 판단하며 결정론적 집행 범위 밖이다.

**[진입점 ③] 미등록 업무 용어 발견 시 draft term 등록 제안 (term 타입 채택 프로젝트 한정):**
- 질의어 또는 질의 문맥에서 **미등록 업무 용어**(term 페이지 없음)가 발견되면(LLM 판단), `status: draft` term 등록을 **제안**한다.
- [MUST] **자동 등록 금지** — 노이즈·오등록 방지를 위해 반드시 사용자 확정 게이트를 거친다.
- 사용자 확정 시 해당 term 페이지 frontmatter의 `status`를 `active`로 전환하고 `brain-tool index`를 재실행한다 → draft→active 승격 흐름.
- 이 흐름은 질의가 살아있는 업무 어휘의 자연스러운 발견 진입점임을 반영한다.

```
[brain query] 미등록 업무 용어 발견
─────────────────────────────────────
"<질의어>"에 대한 term 페이지가 없습니다.
draft term으로 등록할까요?

등록 시: pages/term/<kebab-name>.md (status: draft) 생성
          사용자 확정 시 status: active 승격 + index 재생성
확정 전 draft는 답변 검색에 쓰이지 않습니다.
```

**1. brain-tool search로 후보 목록 탐색 (본문 로드 없음):**
```bash
~/.opal/tools/brain-tool/run.sh search "<질문 키워드>" [--type T] [--tag X] [--limit 10]
```
반환값: `matches` 배열 — 각 항목은 `page`(파일 경로)·`title`·`score`·`snippet`(발췌, 본문 전체 X)만 포함.

**2. 후보 목록을 사용자에게 제시한다:**
```
[brain query] 관련 페이지 후보
──────────────────────────────
1. pages/concept/xxx.md  score:0.91  "..."
2. pages/entity/yyy.md   score:0.84  "..."
3. pages/flow/zzz.md     score:0.72  "..."

어떤 페이지를 참조할까요? (번호 입력, 복수 선택 가능 / 'all'은 금지)
```

`//opbr ask` 모드: 사용자가 직접 번호 또는 파일명을 지정한다.
그 외 모드: PM이 score 상위 페이지를 선별하되, 불확실하면 사용자 확인을 요청한다.

**3. 선택된 페이지만 Read하여 컨텍스트에 주입한다:**
- 선택 페이지 파일을 Read 도구로 읽어 내용을 파악한다.
- **선택되지 않은 페이지는 Read하지 않는다.**

**4. 주입된 페이지 내용 + 인용(출처 명시)으로 답변을 합성한다.**

**5. 답변 품질 평가:**
- 새로운 인사이트를 담는 **가치 있는 답**이면 → synthesis 페이지로 파일링 제안.
- 단순 정보 재조합이면 → 파일링 생략.

### synthesis 페이지 파일링 제안 형식

> **[MUST]** 파일링(add-page) 직전 §공통 규칙 > 코드→브레인 저술 자기검토 게이트 4항목을 통과 확인한다. synthesis도 지식 산출물이므로 §8 비즈니스 용어 우선 원칙의 대상이다 (위반 시 본문 재작성 후 파일링).

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

### 비대화형 read-only 모드 (`//opbr query --read-only`)

기계 소비자(OPAL Console·자동화)용. `//opbr ask` 대화형 절차를 다음으로 대체한다(`ask` 분기는 변경 없음):

- **자동 선별**: term-우선 + search 후 score 상위 N(기본 3) 페이지를 **자동 선택**한다. "어떤 페이지를 참조할까요?" 등 사용자 확인을 **요청하지 않는다**.
- **항상 최종 답변 합성**: 후보 목록만 제시하고 멈추지 않는다. 선택 페이지 본문을 근거로 최종 답변을 합성한다.
- **순수 read-only**: 진입점③(미등록 term draft 등록 제안)·Step 5(synthesis 파일링 제안)·query log 기록(`brain-tool log`)을 **모두 생략**한다. brain에 어떤 쓰기·제안도 하지 않는다.
- **출력 계약**: 응답은 아래 JSON 코드펜스 **하나만** 출력한다(보고형식·산문·후보목록 표 없이). 인용은 합성에 실제 사용한 페이지로 채운다.
  ```json
  {"answer":"<최종 답변 텍스트>","citations":[{"page":"<페이지 경로>","title":"<제목>","type":"<concept|entity|flow|synthesis|term>"}]}
  ```
- (헤드리스 호출 시 부트스트랩 완료 보고가 앞에 출력될 수 있으나, 소비자는 JSON 펜스만 발췌한다.)

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
| `term_duplicate` | 서로 다른 term 페이지의 표준명(`title`)이 정규화 시 동일·중복 | 중복 표준명 병합 — 한 페이지에 통합하고 나머지 삭제 |
| `alias_collision` | 한 term의 `aliases` 항목이 다른 term의 `title` 또는 `aliases`와 충돌 | 별칭 정리 — 충돌 별칭을 삭제하거나 term 통합 |

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

### 코드→브레인 저술 자기검토 (§8 비즈니스 용어 우선 게이트) [MUST]

> 소스 코드/문서를 분석해 brain 페이지(entity/concept/synthesis)를 저술할 때, **add-page 직전** 작성 본문을 아래 4항목으로 자기검토하고 위반 시 재작성 후 파일링한다. 근거: `citation-rules.md` §8.

| # | 체크 항목 | 확보 품질 | 근거 |
|---|----------|----------|------|
| 1 | 각 모듈/로직의 **비즈니스 의미를 구체적으로** 서술했는가 (모호한 일반 서술 "처리한다/관리한다" 금지) | 구체성 | §8.2 |
| 2 | 본문 문장의 **주어가 비즈니스 용어/자연어**인가 (코드 식별자·변수명을 주어로 나열하지 않았는가) | 자연스러운 문장 | §8.2.1 |
| 3 | 코드 식별자 언급 시 **`비즈니스 용어(코드 식별자)` 형식으로 병기**했고, **코드블록이 본문 서술을 대체하지 않았는가** | 자연스러운 문장 | §8.2.2·§8.8 |
| 4 | 모든 서술에 **`` `경로:줄번호` `` 전체 경로**로 출처(근거)를 병기했는가 (파일명·약칭 단독 금지) | 소스 위치 근거 | §2.2 |

**허용 / 금지 경계**

| 구분 | 예시 |
|------|------|
| ❌ 금지 | "`autoSelCancelYn`가 N이 아니고 `basicPugCpMsnBscId`가 null이 아니면 자동 취소된다." (식별자가 주어) |
| ❌ 금지 | "이 모듈은 데이터를 처리한다" (구체성 없음) |
| ❌ 금지 | 본문 대신 코드블록만 붙여 의미 설명을 대체 |
| ❌ 금지 | `brain_tool.py`처럼 파일명만 인용(줄번호·경로 누락) |
| ✅ 허용 | "자동취소가 켜져 있고(`a.java:120`) 기본 미션이 지정되어 있으면(`b.java:88`) 자동으로 취소된다." |
| ✅ 허용 | 코드 식별자·enum은 별도 "소스 커버리지/개발자 부록" 또는 `sources`로 강등 배치(§8.8) |

> 개발 트랙 산출물(ANALYSIS/PLAN/EXECUTE)은 코드 토큰 직접 인용이 정상이므로 이 게이트 대상이 아니다(§8 서두 단서).

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — 단일 pilot + 4모드(init/ingest/query/lint), 결정4 임계값·결정5 배치정책·결정7 SCHEMA 기반 (015) |
| v1.1 | 2026-06-11 19:20 | init STEP 0 신설(analyze→타입 제안→사용자 확인→`init --types` SCHEMA 확정), ingest --all 범위 확장(docs·스킬·참조 concept 요약+포인터, ingest-scan 활용), ingest task:NNN 모드+001~015 백필 절차 추가(op-brain-ingest 기준 재사용), query 후보 목록→선택→선택 페이지만 주입으로 정정(W5 RAG식 전량 로드 금지), [MUST] 단방향·전량로드금지 인용 명문화 (016) |
| v1.2 | 2026-06-11 21:42 | [MUST] source_ref 형식 규칙 명시 — add-page `--sources` 값은 ingest-scan `source_ref` 그대로 사용, 임의 형식(전체 경로 등) 금지(멱등 skip 보호). 단일 소스 절차 5항 + 배치 정책 멱등 행 2곳 추가 (016) |
| v1.3 | 2026-06-17 | term 타입 운영 — init 채택 가이드 / ingest draft term 추출 / query business-first+진입점③(미등록 용어 발견→draft 제안→확정 시 active) / lint term_duplicate·alias_collision (027) |
| v1.4 | 2026-06-22 | 036: query --read-only 비대화형 계약 추가 — 모드 라우팅 표에 `//opbr query --read-only "<질의>"` 행 명시, §STEP query 하단에 "비대화형 read-only 모드" 절 신설(자동 선별·항상 합성·순수 read-only·JSON 출력 계약) |
| v1.5 | 2026-06-23 | 038: entity 5섹션 표준화 + @header 전사 금지·provenance 3종·입력 큐레이션 선행 [MUST] + 재생성 런북 신설 + ingest --all drift 정정 (038) |
| v1.6 | 2026-07-01 22:34 KST | 코드→브레인 저술 자기검토 게이트(§8 비즈니스 용어 우선) 공통 규칙에 신설 — 3대 품질(구체성·자연스러운 문장·소스 위치 근거) 4항목 체크리스트 + 허용/금지 경계. entity 시드·concept ingest(단일/task:NNN)·synthesis 파일링 add-page 직전 참조. (L2 경량) |

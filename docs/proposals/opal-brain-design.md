# OPAL Project Brain 설계 제안서

> 상태: **구현 완료 (015 코어 + 016 지능화)** | 작성: 알투(PM) | 작성일: 2026-06-09
> 근거: Karpathy llm-wiki + OPAL 프레임워크 융합
> 015: brain-tool·opal-brain·op-brain-ingest 코어 완성 / 016: 지능화(init 분석·ingest --all 문서·3계층·index 비상주·이름 확정·git 추적)

---

## 1. 배경 & 목적

### 1.1 문제 정의

OPAL은 프로젝트 지식을 **여러 곳에 흩어서** 보유한다:

| 계층 | 현재 자산 | 담는 것 |
|------|----------|--------|
| Schema(규약) | `docs/PROJECT.md`·`CONVENTIONS.md`·`.opal/AGENT.md` | 프로젝트 정의·컨벤션·PM 역할 |
| Log(연대기) | `.opal/MEMORY.md` 작업 히스토리 | 태스크 진행 이력 |
| Index(구조) | `.opal/code-scan.json` (@header) | 코드가 **무엇이** 있는가 |
| **지식(WHY/HOW)** | **— 없음** | **왜·어떻게 그렇게 되었는가** |

흩어진 지식은 **매번 다시 분석**해야 한다. PM이 작업할 때마다 코드를 재탐색하고, 과거 결정의 맥락은 git log·완료된 태스크 폴더를 뒤져야 복원된다. 이는 Karpathy가 지적한 RAG의 한계 — "매 질의마다 재검색·재합성" — 와 동일하다.

### 1.2 목적

llm-wiki 사상("영속적·복리적 아티팩트")을 OPAL 네이티브로 구현하여 **프로젝트 브레인(Project Brain)**을 구축한다. 핵심은 빠진 한 조각, **누적되는 지식 페이지**를 채우고 이를 OPAL 파이프라인이 자동으로 키우고 활용하게 만드는 것이다.

### 1.3 설계 원칙 (헌법 상속)

- **User sovereignty**: brain 자동 ingest도 사람이 읽는 .md로 산출 → 사후 검토 가능
- **Enforce, don't advise**: index·log·링크 무결성은 프로즈가 아닌 `brain-tool`로 집행
- **Simplicity first**: 외부 지식만 원본 저장, 내부 코드는 참조만 (중복 회피)
- **Platform-independent**: 마크다운 네이티브 — 특정 도구·대시보드에 종속되지 않음

---

## 2. llm-wiki 사상 요약 (출처 분석)

| 개념 | 내용 |
|------|------|
| 본질 | RAG가 아닌 **영속·복리 아티팩트** — 교차참조·모순 플래그가 이미 페이지에 누적됨 |
| 3계층 | Raw sources(불변 원본) / Wiki(LLM 생성 .md) / Schema(규약 문서) |
| 특수 파일 | `index.md`(카테고리 카탈로그) · `log.md`(append-only 연대기) |
| 페이지 타입 | 엔티티 / 개념 / 비교 / 합성 (원자적 분리) |
| 워크플로우 | **Ingest**(원본→요약→index·관련 페이지 갱신→log) / **Query**(index→페이지→인용 합성, 좋은 답은 다시 페이지로) / **Lint**(모순·stale·고아·누락 링크 점검) |
| 링크 | Obsidian 스타일 `[[페이지명]]` 교차참조 |
| 역할 분담 | 사람은 큐레이션·질문, LLM은 요약·교차참조·파일링·북키핑 grunt work |

---

## 3. OPAL 융합 원칙 — 경계 정의

brain은 기존 자산을 **대체하지 않고 보완**한다. 역할이 겹치지 않도록 경계를 명확히 한다.

| 자산 | 역할 | brain과의 관계 |
|------|------|---------------|
| `code-scan.json` | 코드 구조 지도 (WHAT exists) | brain entity 페이지가 **@header를 시드로 흡수**(단방향: 코드→brain) + `file_path` 참조. 코드 본문은 복제 금지 |
| `.opal/MEMORY.md` | PM **운영 기억** (피드백·선호·작업이력) | 별개. brain은 **프로젝트 도메인 지식** |
| `docs/*.md` | 프로젝트 **규약·정의** (사람이 직접 관리, SSOT) | brain `SCHEMA.md`가 이를 참조. brain은 docs를 ingest해 개념 페이지화 가능 |
| `understand-anything` | knowledge graph JSON + 대시보드 | **선택적 보강** — brain(.md SSOT)에서 파생 그래프 생성용. 의존성 아님 |

> **한 줄 요약**: code-scan = "무엇이 있나", MEMORY = "PM이 어떻게 일하나", **brain = "이 프로젝트가 왜·어떻게 그렇게 되었나"**.

---

## 4. 디렉토리 구조

```
.opal/brain/
  SCHEMA.md            # 위키 규약 (페이지 포맷·네이밍·링크 규칙) = llm-wiki schema 계층
  index.md             # 카테고리별 카탈로그 (도메인/개념/엔티티/흐름/합성)
  log.md               # append-only ingest 연대기
  pages/
    entity/            # 코드 엔티티 페이지 (모듈·서비스·도구·스킬)
    concept/           # 개념·아키텍처 결정 페이지 (왜 이렇게 설계했나)
    flow/              # 비즈니스·데이터·파이프라인 흐름 페이지
    synthesis/         # 질의에서 파생된 분석·비교 페이지 (복리 누적)
  sources/             # ★ 외부 소스 원본 보관 (웹·PDF·이미지·캡틴 제공 자료)
    <source-id>/
      raw.md           # 변환된 원본 (wtm-agent/xlsx-tool 산출)
      meta.yaml        # 출처 URL·수집일·라이선스
```

> 내부 코드/문서는 `sources/`에 넣지 않는다 — git+code-scan이 SSOT. brain 페이지가 `file_path:line`으로 참조한다.

---

## 5. SCHEMA.md — 위키 규약

`SCHEMA.md`는 brain의 "헌법"으로, 모든 페이지가 따르는 규약을 정의한다. (init 시 프로젝트별 생성)

### 5.1 페이지 frontmatter 표준

```yaml
---
type: entity | concept | flow | synthesis   # 페이지 타입 (SCHEMA §1.5 동적 선언 — 기본 4종은 검토 후보)
title: state-tool 설계
tags: [tool, pipeline, state]
sources: [code:opal/tools/state-tool/, task:013, task:014]   # 근거 출처 / task:NNN drill-down 지원
related: [[opal-harness]], [[pipeline-state]]                 # 교차참조
created: 2026-06-09
updated: 2026-06-09
status: active | stale | draft
---
```

> **페이지 타입 동적화 (016 M-1 B안)**: `type` 값은 하드코딩이 아닌 SCHEMA.md §1.5 테이블에서 동적 로드한다. brain-tool은 `load_page_types(brain_root)` 함수로 타입 세트를 파싱하며, SCHEMA 부재 시 `DEFAULT_PAGE_TYPES = ["entity","concept","flow","synthesis"]`로 graceful 폴백한다. init이 origin 분석(analyze) 결과를 바탕으로 타입 세트를 채택/제외/추가/교체하여 SCHEMA에 확정한다.

### 5.1.1 entity 페이지 — @header 시드 매핑

entity 페이지는 빈 페이지로 시작하지 않는다. `code-scan.json`이 파싱한 **@header 메타블록을 frontmatter·본문 시드로 흡수**한다. (단방향 동기화: 코드 @header가 SSOT, brain은 스냅샷 + 누적 지식)

```yaml
---
type: entity
title: state-tool
# ↓ @header에서 자동 시드 (brain-tool이 code-scan.json에서 가져옴)
module: state_tool
layer: util
domain: opal-pipeline
exports: [cmd_init, cmd_mark, cmd_advance, ...]
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-06-09        # 마지막 @header 동기화 시각
# ↑ 여기까지 시드 / 아래는 brain 누적
tags: [tool, pipeline]
related: [[opal-harness]]
---

## 개요
<@header description 시드>

## 설계 배경 (WHY) — brain 누적
<태스크 013·014에서 누적된 결정·맥락>
```

> @header = 구조(WHAT), brain 본문 = 이유·관계·결정(WHY/HOW). 코드 본문은 복제하지 않고 `source_ref`로 참조한다.

### 5.2 네이밍 규칙

- 파일명: `kebab-case.md` (예: `state-tool-design.md`)
- 페이지명 = frontmatter `title`, 링크는 파일명 기준 `[[state-tool-design]]`
- 타입별 디렉토리 강제 (`pages/{type}/`)

### 5.3 링크 규칙

- 교차참조: `[[페이지파일명]]` (Obsidian 호환)
- 코드 참조: `` `file_path:line` `` (OPAL 클릭 가능 형식)
- 외부 소스 참조: `[[source:source-id]]`

### 5.4 index.md 구조

```markdown
# Project Brain Index
> 갱신: <brain-tool 자동>

## 도메인
- [[domain-pipeline]] — 파이프라인 오케스트레이션 (페이지 5)

## 개념
- [[state-tool-design]] — STATE 결정론적 집행 #tool #pipeline

## 엔티티
- [[opal-pilot-project]] — 범용 오케스트레이터

## 합성
- [[interactive-vs-agentic]] — 모드 비교 분석 (질의 2026-06-08 파생)
```

### 5.5 log.md 구조 (append-only)

```markdown
## [2026-06-09] ingest | 태스크 015 CLOSE — opal-brain 신설
- 신규: [[opal-brain-skill]], [[brain-tool]]
- 갱신: [[index]], [[opal-harness]]
- 출처: task:015
```

---

## 6. opal-brain 스킬 (단일 pilot + 4모드)

레지스트리 등록(`opal-skills-registry.json`):

```json
{
  "name": "opal-brain",
  "alias": "opbr",
  "description": "프로젝트 브레인 — 영속 지식 위키 생성·누적·질의·정비",
  "triggers": ["^opbr$", "^opal-brain$", "(?i)(프로젝트\\s*브레인|지식\\s*위키)"],
  "domain": "knowledge",
  "pipeline": "MODE: init | ingest | query | lint"
}
```

### 6.0 brain 라이프사이클 (init = 프로젝트 최초 1회)

opal-brain **스킬·도구의 설치**(글로벌)와 **프로젝트 brain 부트스트랩**(`//opbr init`)은 다른 층위다.

| 시점 | 동작 | 빈도 | 위치 |
|------|------|------|------|
| 프레임워크 설치 | install로 opal-brain 스킬·brain-tool 배포 | 머신당 1회 | `~/.opal/` (전 프로젝트 공용) |
| **프로젝트 부트스트랩** | `//opbr init` — 골격·SCHEMA·핵심 엔티티 시드 | **프로젝트당 1회** | `.opal/brain/` |
| 운영 | ingest / query / lint + CLOSE 자동 ingest | 반복 | `.opal/brain/` |

> `//opi`(프로젝트 OPAL 셋업)와 동일 위상. init은 1회성 셋업이며, 이후 자산 추가는 init이 아니라 **ingest**로 한다. init 재실행은 기존 brain 존재 시 거부하고, `--force`로만 재초기화한다.

### 6.1 모드별 동작

| 모드 | 커맨드 | 동작 | 워커/도구 |
|------|--------|------|----------|
| **init** | `//opbr init` | **[016 M-1 B안]** STEP 0: `brain-tool analyze` → origin 정량 집계(domain·layer·exports·피의존도) → LLM이 타입 세트·도메인·시드 대상 제안 → 사용자 확인 → `init --types` 로 SCHEMA 타입 확정 → 골격 생성 + 핵심 엔티티 @header 시드 (범위 정책 §6.1.1) | brain-tool analyze + init + code-scan 연동 |
| **ingest** | `//opbr ingest <소스>` | 소스(코드/문서/외부 URL/파일/task:NNN) 읽기 → 요약 페이지 작성 → index·관련 페이지 갱신 → log 기록 | wtm-agent(외부) + 분석 워커 + brain-tool |
| **ingest --all** | `//opbr ingest --all [--scope X]` | **[016 M-2 B안]** `brain-tool ingest-scan --source all` → docs·스킬·참조·tasks 목록 + 멱등 skip 판정 → 5자산/배치 순차 처리. docs/.md·스킬·참조는 **3~6줄 요약+포인터** concept, 코드 @header는 entity 시드. 진행률 보고 | brain-tool ingest-scan + 배치 워커 |
| **query** | `//opbr ask "질문"` | `brain-tool search` → **후보 목록(title·score·snippet)** 반환 → 제시 → 선택 → **선택 페이지만 Read 주입** → 합성 답변. 가치 있는 답은 synthesis/ 페이지로 파일링 제안 | brain-tool search + 합성 워커 |
| **lint** | `//opbr lint` | 모순·stale·고아 페이지·누락 링크·근거 없는 주장 탐지 후 정비 제안 | brain-tool lint |

### 6.1.1 init 등록 범위 정책 (★ 전체 미러 아님)

init은 프로젝트의 **모든 자산을 페이지화하지 않는다.** 전체 페이지화는 code-scan과 1:1 중복이며 noise·sync 부담만 키운다 (헌법 "Simplicity first"). 대신 3계층으로 차등 등록한다:

| 계층 | init 등록 | 단위 | 근거 |
|------|----------|------|------|
| **맵** (index.md) | code-scan 구조 **전체** 카탈로그 등록 | 도메인/레이어 (가벼운 목록) | 전체 조망은 index로 충분 |
| **핵심 엔티티 페이지** | **선별 시드만** — 주요 도구·오케스트레이터·핵심 모듈 | 선별 entity | 지식 가치 높은 것 우선 |
| **나머지** | 등록 안 함 → ingest/query/CLOSE 시 **점진 생성** | lazy | 복리 누적 (llm-wiki 사상) |

**핵심 엔티티 선별 기준 (016 M-1 B안 — `SEED_THRESHOLDS` SSOT: `brain_tool.py` 상수)**:

- `exports ≥ 3` OR `피의존도 ≥ 2` OR `layer ∈ {orchestrator, tool, pilot, core}` OR `domain 대표 1개`
- 구체적 정량값은 `brain-tool analyze` 결과(domain별 모듈수·layer 분포) 위에서 LLM이 제안 → 사용자 확인으로 확정 (결정론적 집계 = brain-tool, 의미 판단 = LLM)

**범위 조절 옵션**:

| 옵션 | 동작 |
|------|------|
| `//opbr init` (기본) | 전체 맵 + 핵심 엔티티 시드 (경량) |
| `//opbr init --scope <도메인/레이어>` | 해당 범위만 시드 |
| `//opbr init --full` | 모든 @header를 entity 페이지로 시드 (골격만, 얕음) |
| `//opbr init --ingest-all [--scope X]` | init 직후 **전체 자산 자동 분석 ingest** 실행 (= `//opbr ingest --all`, 병렬 배치, 비용 큼) |

> **얕음/깊음 구분**: `--full`은 @header 기반 골격 시드(얕음), `--ingest-all`은 자산을 실제로 읽고 요약·관계·개념을 추출하는 분석 ingest(깊음). 깊은 전체 ingest는 명시 옵션이며 기본값이 아니다.

### 6.2 모드 라우팅

`opal-brain` pilot은 첫 인자로 모드를 받아 분기한다. 모드 미지정 시 PM이 의도를 판별해 제안(주도성 원칙).

---

## 7. brain-tool 도구

`~/.opal/tools/brain-tool/run.sh` — index·log·링크를 **결정론적으로** 관리 (LLM 직접 편집 금지, state-tool과 동형 패턴).

### 7.1 서브커맨드

| 커맨드 | 용도 |
|--------|------|
| `init <brain-path>` | brain 골격 디렉토리·SCHEMA·빈 index/log 생성 (`--types <csv>` 옵션으로 확정 타입 세트 전달) |
| `add-page <path> --type <T> --title <..>` | 페이지 생성 + index 자동 등록 + frontmatter 검증 (타입은 SCHEMA §1.5 동적 로드) |
| `index` | pages/ 스캔 → index.md 재생성 (SSOT 동기화) |
| `log <op> <summary>` | log.md append (타임스탬프 자동) |
| `search <query>` | frontmatter tags·title·본문 검색 → **후보 목록**(page·title·score·snippet) 반환. 본문 포함 안 함 — PM이 선택 후 선택 페이지만 Read 주입 |
| `sync-header` | `code-scan.json`의 @header와 entity 페이지 frontmatter 비교 → drift 시 시드 갱신 + stale 표시 (단방향: code→brain) |
| `lint` | 링크 무결성·고아·stale(updated/header drift)·근거 누락 페이지 탐지 → JSON 리포트 |
| `validate` | 전체 brain 구조·frontmatter 표준 준수 검증 |
| `analyze` | **[016 신설]** code-scan @header 정량 집계(domain별 모듈수·layer 분포·exports·피의존도·seed_candidates) → JSON 반환. init 타입 제안의 결정론적 입력. LLM 요약은 수행하지 않음 |
| `ingest-scan` | **[016 신설]** `--source docs\|skills\|tasks\|all`로 .md 문서·tasks/NNN 목록 스캔 → 멱등 skip 판정 포함 JSON 목록 반환. 목록 산출은 도구, 본문 요약은 LLM |

### 7.2 집행 규칙

- index.md / log.md는 **brain-tool로만** 갱신 (LLM 마크다운 직접 편집 금지)
- 페이지 본문은 LLM 작성, 메타데이터·인덱싱은 도구 집행
- 출력 JSON (`"ok": true/false`), 에러 코드 카탈로그

---

## 8. OPAL 하네스/PM 융합 (캡틴 3대 요구)

### 8.1 PM/분석/설계 시 brain 참조 (요구 ①)

**code-scan PM 우선 규칙(태스크 010)과 동형 패턴으로 구현 완료 (016 W5).**

(a) **부트스트랩 융합 — [016 정정]** `AGENT.md` Lazy 트리거 테이블:

| 트리거 | 로드 대상 |
|--------|----------|
| brain 검색 키워드 명시 요청 또는 `//opbr` 커맨드 시 | `.opal/brain/` — **존재 여부만 경량 인지** (PM 컨텍스트 로드 시 brain 디렉토리 존재 확인에 한정; index.md 전체 자동 로드 안 함). 지식은 `brain-tool search` 후보→선택 주입으로 온디맨드 로드 |

> **정정 이유 (016 W5)**: 설계 초안이 "PM 컨텍스트 로드 시 함께 index.md 자동 로드"로 제안했으나, 이는 index 전체를 컨텍스트에 올리는 것으로 "전체 brain 로드 금지" 원칙 위반이다. 구현은 index 비상주(부트스트랩에서 존재 여부만 인지, 실제 지식은 search 후보→선택 주입으로 온디맨드)로 확정되었다.

(b) **PM 디스패치 전 프로세스 융합 — [016 확장]** `pm/dispatch-process.md` Step 1.5:

```
Step 1.5 — brain 사전 지식 참조 (3시점)
  ① 작업·분석·설계 전: PLAN 착수 전 / 구현 설계 시작 전 — 과거 아키텍처 결정·반복 패턴 확인
  ② 워커 디스패치 시: 각 Step 프롬프트 작성 직전 — 해당 Step 키워드로 관련 페이지 조회 후 주입
  ③ 사용자 질의: 구체적 질문 수신 즉시 — 과거 결정·맥락 근거로 답변 품질 향상

  흐름 (공통): brain-tool search <키워드> → 후보 목록(page·title·score·snippet) 반환
              → PM이 score 상위 선별(불확실 시 사용자 확인)
              → 선택된 페이지만 Read하여 워커 컨텍스트 주입
  [MUST] RAG식 전량 로드 금지 — index.md 전체 자동 로드 안 함, 선택된 페이지만 주입
```

(c) **프로젝트 AGENT.md 규칙** — "opal-brain 활용 규칙" (016 W4 PM 판단 ingest 포함):

| 상황 | 활용 방법 |
|------|----------|
| 작업 시작·분석·설계 전 | `brain-tool search <키워드>` → 후보 선별 → 선택 페이지만 주입 |
| 과거 결정의 맥락 필요 | `//opbr ask` 또는 brain 페이지 직접 Read |
| 작업 중 가치 지식 감지 | 아키텍처 결정·반복 패턴·캡틴 합의·비자명 해결 발생 시 ingest 실행 — **agentic=자율 ingest / semi·interactive=사용자 제안** |

### 8.2 CLOSE 시 자동 ingest (요구 ②)

**모든 pilot의 CLOSE 단계에 brain ingest 훅 구현 완료 (016 W6 — opp + 7 pilot 확산). 관련 문서 업데이트 스텝 추가 (042).**

```
CLOSE 단계:
  1. DONE.md 생성
  2. ★ 관련 문서 업데이트 (brain ingest 직전):
     PROJECT.md 레지스트리 + 태스크 changed_files 종합 → PM 판단 → 직접 수정 또는 워커 호출
     (갱신 대상 없으면 no-op — CLOSE 비중단)
  3. ★ brain ingest 훅:
     관련 문서 최신화 직후 → .opal/brain/ 존재 시 op-brain-ingest 디스패치(부재 시 no-op)
     (op-brain-ingest 탐색 경로 2단: 프로젝트 스킬 → 글로벌 스킬)
  4. 태스크 완료 보고
```

**ingest 대상 / 제외 기준** (op-brain-ingest §STEP 3 SSOT):

| ingest | 제외 |
|--------|------|
| 아키텍처 결정·신규 컴포넌트·인터페이스 변경·도메인 지식 | 오타·포맷·trivial 설정값 변경 |

- PM Gate 통과 후 실행 → 검증된 산출물만 누적
- agentic 모드여도 .md 산출이므로 사후 검토 가능 (헌법 §4 정합)
- 구현: CLOSE에서 `op-brain-ingest` 경량 워커 디스패치. 백필 기준은 동일 SSOT 재사용 (중복 로직 회피)

### 8.3 소스를 brain에 넣기 (요구 ③) — 하이브리드 권고

| 소스 유형 | 처리 | 이유 |
|----------|------|------|
| **내부 코드** | **@header를 entity 페이지 시드로 흡수** + `source_ref` 참조. 코드 본문 복제 금지 | @header는 경량 메타라 stale 위험 낮음, 코드가 SSOT (단방향 동기화) |
| **내부 문서** (docs/*.md / 스킬·참조) | **3~6줄 요약(목적·핵심 결정·적용 범위) + `file_path` 포인터**로 concept 페이지 생성. 본문 복제 금지 — 원본이 SSOT | docs/스킬이 SSOT (016 M-2 B안 확정) |
| **태스크** (`tasks/NNN/`) | DONE.md·PLAN.md 읽기 → concept 1개(핵심 결정). `sources:[task:NNN]` — drill-down 지원 | 3계층 기억 §8.4 참조 |
| **외부 소스**(웹·PDF·이미지·캡틴 제공) | `sources/`에 **원본 저장 + 요약 페이지** | git이 안 잡는 외부 지식 → 영속화 가치 |

- 외부 소스 변환은 기존 OPAL 도구 재사용: **wtm-agent**(웹→md), **xlsx-tool**(엑셀), 이미지/PDF Read
- `sources/<id>/meta.yaml`에 출처·수집일·라이선스 기록 (추적성)

### 8.4 3계층 기억 모델 (016 M-3 B안 확정)

OPAL의 기억은 3계층으로 분리된다:

| 계층 | 자산 | 역할 | 수명 |
|------|------|------|------|
| **단기 기억** | `.opal/MEMORY.md` | PM 운영 기억 — 피드백·선호·작업이력 (FIFO 10) | 세션~단기 |
| **장기 검색** | `.opal/brain/` | 프로젝트 WHY·HOW 지식 위키 — 요약·교차참조 | 영속 |
| **장기 원본** | `tasks/NNN/` | 태스크별 원본 산출물(PLAN/DONE/TASK) | 영속 |

- brain `sources:[task:NNN]`으로 장기 검색 → 장기 원본 drill-down 가능
- 001~015 소급 백필: DONE.md 있는 태스크 중 아키텍처/신규 컴포넌트/인터페이스 변경 포함 태스크만 선별 백필 (op-brain-ingest §STEP 3 기준 재사용). 5자산/배치·멱등 skip 정책 동일하게 적용

---

## 9. 부트스트랩 로딩 전략 (016 W5 정정 — index 비상주)

| 시점 | 로드 대상 | 방식 |
|------|----------|------|
| PM 컨텍스트 로드 시 | `.opal/brain/` **존재 여부만** 확인 | Lazy 경량 인지 (디렉토리 존재 확인에 한정) |
| 작업/분석/설계 진입 시 | `brain-tool search <키워드>` 후보 목록 | 동적 (키워드 기반) — 후보만 반환, 본문 없음 |
| 후보 선별 후 | 선택된 페이지만 Read | 온디맨드 |
| `//opbr` 커맨드 또는 검색 키워드 명시 요청 | brain-tool 호출 | Lazy 트리거 조건 충족 시에만 |

> **[016 정정]** 설계 초안은 "PM 컨텍스트 로드 시 `.opal/brain/index.md` Lazy 로드"로 제안했으나, 이는 index 전체를 컨텍스트에 올려 "전체 brain 로드 금지" 원칙 위반이다. 구현 확정: index 비상주 — 부트스트랩에서 brain 존재 여부만 경량 인지하고, 실제 지식은 `brain-tool search` 후보 목록 → PM 선별 → 선택 페이지 온디맨드 주입으로 접근한다. (AGENT.md Lazy 트리거 테이블·dispatch-process.md Step 1.5 참조)
>
> **원칙 유지**: 전체 brain을 컨텍스트에 올리지 않는다 — "index-driven discovery"는 index 목차를 로드하는 것이 아닌 search 후보 목록을 통한 선택적 접근으로 구현된다.

---

## 10. 배포 (install)

| 자산 | 배포 경로 | install 반영 |
|------|----------|-------------|
| `opal-brain` 스킬 | `~/.opal/skills/opal-brain/` | install-mac.sh / .ps1 / linux.sh 동기화 |
| `brain-tool` 도구 | `~/.opal/tools/brain-tool/` | venv 등록 |
| 레지스트리 항목 | `opal-skills-registry.json` | 신규 행 |
| 하네스 융합 | `opal-harness.md`·`dispatch-process.md`·`AGENT.md` | SSOT 수정 |
| `op-brain-ingest` 워커 스킬 | `~/.opal/skills/op-brain-ingest/` | (CLOSE 훅용) |

> `.opal/brain/` 자체는 **프로젝트 자산** — 각 프로젝트가 `//opbr init`으로 생성 (글로벌 배포 아님).

---

## 11. 단계별 구현 로드맵 (제안)

| Phase | 범위 | 산출물 |
|-------|------|--------|
| **P1** | brain-tool 도구 + SCHEMA 표준 | `brain-tool/`, `SCHEMA.md` 템플릿 |
| **P2** | opal-brain 스킬 (init·ingest·query·lint) + 레지스트리 | `opal-brain/SKILL.md`, registry 행 |
| **P3** | PM 융합 (참조 ①) — 부트스트랩·dispatch·AGENT.md | 하네스 문서 수정 |
| **P4** | CLOSE 자동 ingest 훅 (②) — pilot CLOSE 수정 + ingest 워커 | pilot SKILL 수정, `op-brain-ingest` |
| **P5** | 외부 소스 파이프라인 (③) — wtm-agent 연동 | sources/ 처리 로직 |
| **P6** | install 배포 + 현재 opal 프로젝트에 `//opbr init` 적용 | 배포 스크립트, opal brain 시드 |

> P1·P2가 코어. P3~P5는 융합. P6은 배포·검증. 풀 파이프라인(`//opp` 또는 `//opd`)으로 진행하며 PLAN에서 Phase 분해를 확정한다.

---

## 12. 리스크 및 결정 이력

| # | 항목 | 상태 | 해결/현황 |
|---|------|------|----------|
| R1 | CLOSE 자동 ingest가 모든 태스크에 적용 시 noise 누적 가능 | 완화 | op-brain-ingest §STEP 3 포함/제외 기준 SSOT로 엄격화. 백필·CLOSE 훅이 동일 기준 재사용 |
| R2 | 멀티 PC/멀티 에이전트 동시 ingest 시 index 충돌 | 진행 중 | brain-tool 원자적 index 재생성(전체 배치 완료 후 1회 write) 구현. git merge 전략은 사용자 책임 (016은 추적 전환 + 원자화까지, merge 전략은 후속 태스크) |
| R3 | understand-anything 그래프 연동 깊이 | 후속 | P1~P6 코어 완료 후 별도 태스크로 분리 권고 — 016 범위 외 |
| R4 | 기존 완료 태스크(001~015) 소급 ingest 여부 | **확정 (016 M-3 B안)** | **선별 백필** — DONE.md 있는 태스크 중 아키텍처/신규 컴포넌트/인터페이스 변경 포함 태스크만 concept 페이지화. `//opbr ingest --all` 시 또는 별도 명령으로 1회 실행. op-brain-ingest §STEP 3 기준 재사용. 5자산/배치·멱등 skip 동일 정책 |
| R5 | 코드 @header 변경 시 entity 페이지 시드 drift | 완화 | `brain-tool sync-header`로 단방향 재동기화 + lint stale 표시 (코드가 SSOT) |
| R6 | 전체 자산 ingest(`--all`) 토큰·시간 비용 | **확정 (016 M-2 B안)** | **5자산/배치 + 멱등 skip + 진행률 보고 + log.md 배치 완료 마커(재개용)**. 범위: docs·스킬·참조 → concept(3~6줄 요약+포인터), 코드 @header → entity. `ingest-scan` 도구가 결정론적 목록·skip 판정 담당 |
| R7 | init analyze가 code-scan.json 부재 프로젝트에서 무력 | 완화 | code-scan 부재 시 docs/ 폴더 구조·파일명 기반 폴백 제안 + 사용자 확인 (기존 init 전제 확인 절차 계승) |
| R8 | 이름 결정(M-4 A안)이 캡틴 "wiki" 비전과 표면 불일치 | **확정 (016 M-4 A안)** | §13 이름 결정 명문화 참조 |

---

## 13. 이름 결정 명문화 (016 M-4 A안 — R8 대응)

| 용어 | 유형 | 사용 맥락 |
|------|------|----------|
| `opal-wiki-pilot` | **비전·컨셉 명칭** | 캡틴 비전 문서·설계 제안서·고수준 설명에서만 사용. 구현 식별자가 아님 |
| `opal-brain` | **구현 식별자 (스킬명)** | SKILL.md·레지스트리·디렉토리명·코드·문서 본문에서 사용 |
| `opbr` | **구현 식별자 (alias)** | 쌍슬래시 커맨드(`//opbr`)·레지스트리 alias |
| `brain-tool` | **구현 식별자 (도구명)** | CLI 실행(`brain-tool/run.sh`)·코드·스킬 내 도구 호출에서 사용 |
| `.opal/brain/` | **구현 식별자 (디렉토리)** | git·파일 경로·스킬 내 경로 참조 |

> **결정 근거**: 015에서 `brain-tool·opal-brain·opbr·op-brain-ingest·.opal/brain/`을 기준으로 구현된 30+ 참조·6 PM 문서·레지스트리가 모두 `brain` 기준이다. 리네임은 016 핵심(지능화) 대비 가치가 낮고 회귀 위험이 크다. "opal-wiki-pilot"은 비전 용어로 설계 SSOT(이 문서)에만 병기한다.

---

## 14. git 추적 정책 (016 M-5 B안 확정)

| 자산 | git 추적 | 이유 |
|------|---------|------|
| `.opal/brain/` | **추적 (예외 허용)** | brain 페이지는 사람이 읽는 .md SSOT — 팀·멀티PC 공유 + 리뷰 가능 (헌법 "User sovereignty") |
| `.opal/` 나머지 | 무시 유지 | identity·MEMORY·code-scan.json 등 로컬/민감 데이터 |
| `.opal/code-scan.json` | 무시 유지 | 파생 캐시 — 재생성 가능 |

`.gitignore` 패턴:
```
.opal/*
!.opal/brain/
!.opal/brain/**
```

> 구현 확인: 현재 `.gitignore:2-4`에 이 패턴이 적용됨. brain을 git 추적하면 멀티PC ingest 시 index 충돌이 발생할 수 있으나, brain-tool 원자적 index 재생성(전체 배치 후 1회 write)으로 완화. merge conflict 해소는 사용자 책임.

---

## 15. 다음 액션

1. 015 코어 구현 완료 (brain-tool 10커맨드·opal-brain 4모드·op-brain-ingest·opp CLOSE 훅)
2. 016 지능화 구현 완료 (init 분석 STEP 0·ingest --all 문서·3계층·index 비상주·7 pilot 훅 확산·git 추적)
3. Step 18: 현 프로젝트 brain dogfooding — `//opbr ingest --all` + 001~015 선별 백필 실행 (016 install 후)

---

## 변경이력

| 일시 (KST) | 버전 | 변경내용 |
|-----------|------|---------|
| 2026-06-11 19:28 | v2.0 | (016) 지능화 확정 반영 — init 동적 분석(brain-tool analyze + M-1 B), ingest --all 문서 범위(M-2 B 3~6줄+포인터), 3계층 기억(§8.4), index 비상주(§9 정정), 이름 결정 명문화(§13 M-4 A), git 추적 정책(§14 M-5 B), §12 R4/R6 확정, §7.1 analyze/ingest-scan 서브커맨드 추가, §8.1 dispatch-process 3시점+후보→선택 주입, 상태 구현 완료로 갱신 |

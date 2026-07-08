# TASK: OPAL Project Brain — 프로젝트 지식 위키 시스템 신설

> 작성일: 2026-06-10 | 작업 유형: 신규 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 (llm-wiki 분석 → OPAL 융합 위키 시스템 설계·구현)
> 출력: TASK.md

## 작업 목표

Karpathy의 llm-wiki 사상("영속·복리 지식 아티팩트")을 OPAL 네이티브로 융합하여, 프로젝트 지식을 자동으로 생성·누적·질의·정비하는 **Project Brain** 시스템(스킬 `opal-brain`/`opbr` + 도구 `brain-tool` + 하네스 융합)을 신설한다.

## 배경

OPAL은 프로젝트 지식을 흩어서 보유한다 — Schema(`docs/`), Log(`MEMORY.md`), Index(`code-scan.json`). 그러나 "왜·어떻게 그렇게 되었는가"를 담는 **누적 지식 페이지**가 없어, 매 작업마다 코드·문서를 재분석하고 과거 결정의 맥락은 git log·완료 태스크를 뒤져 복원해야 한다. 이는 llm-wiki가 지적한 RAG의 한계(매 질의 재검색·재합성)와 동일하다. 빠진 조각을 채우고, OPAL 파이프라인이 brain을 자동으로 키우고(CLOSE ingest) 활용(PM 참조)하게 만든다.

## 배경 분석 (대화에서 도출)

1. **llm-wiki 핵심** — RAG가 아닌 영속·복리 아티팩트. 3계층(Raw sources / Wiki .md / Schema) + `index.md`(카탈로그)·`log.md`(연대기). 워크플로우 3종: Ingest / Query / Lint. 페이지 타입: 엔티티/개념/비교/합성. `[[]]` 교차참조.

2. **OPAL ↔ llm-wiki 대응 (70% 보유, 30% 공백)**:
   - Schema = `docs/PROJECT.md`·`CONVENTIONS.md`·`.opal/AGENT.md` ✅
   - log = `.opal/MEMORY.md` 작업 히스토리 ✅
   - index(코드 구조) = `.opal/code-scan.json` (@header) ✅ (구조만)
   - **누적 지식 페이지 (WHY/HOW)** = ❌ 공백
   - index/log 결정론적 관리 도구 = ❌ 공백

3. **기존 자산 관계**: `code-scan`(@header 정적 분석, WHAT), `understand-anything`(knowledge graph JSON+대시보드)은 보완·선택 대상이며 의존 대상 아님.

> 상세 분석·설계 근거는 제안서 `docs/proposals/opal-brain-design.md` (→ D-1) 전체 참조.

## 확정된 설계 방향 (대화에서 합의)

대화에서 캡틴과 합의된 핵심 결정 (제안서 D-1 반영 완료):

| # | 결정 | 내용 |
|---|------|------|
| 1 | 저장 형식 | **마크다운 네이티브** (사람·LLM·git 모두 접근). understand 그래프는 선택적 보강 |
| 2 | 스킬 구조 | **단일 pilot + 4모드** (`//opbr` init/ingest/query/lint) |
| 3 | 진행 방식 | 상세 설계 제안서 선작성 → 검토 → 파이프라인 (현재 단계) |
| 4 | @header 시드 | entity 페이지는 code-scan의 @header를 **단방향 시드**로 흡수 (코드가 SSOT) |
| 5 | init 범위 | 전체 미러 아님 — 맵(index)+핵심 엔티티 시드+점진 누적. `--scope`/`--full`/`--ingest-all` 옵션 |
| 6 | 라이프사이클 | init = 프로젝트당 1회 부트스트랩. 이후 자산 추가는 ingest |
| 7 | PM 참조 | PM/분석/설계 시 brain 우선 참조 (code-scan PM 우선 패턴과 동형) |
| 8 | CLOSE 자동 ingest | 모든 pilot CLOSE에 ingest 훅 — 결정·엔티티 자동 누적 (복리) |
| 9 | 소스 처리 | 내부 코드=참조+@header 시드, 외부 소스=`sources/` 원본 저장 (하이브리드) |
| 10 | 전체 자동 ingest | `//opbr ingest --all` — 명시 옵션, 병렬 배치, 멱등 skip |

## 요구사항

- [ ] **R1. brain-tool 도구** — `~/.opal/tools/brain-tool/run.sh` + 서브커맨드(init/add-page/index/log/search/sync-header/lint/validate). index·log·링크를 결정론적으로 집행(LLM 직접 편집 금지). 출력 JSON + 에러 코드.
  - 무엇을: brain-tool 신규 구현 / 어디에: `opal/tools/brain-tool/` / 왜: 확정 방향 §enforce(제안서 §7) / AC: run.sh 호출 시 8개 서브커맨드가 동작하고, `init`이 `.opal/brain/` 골격을 생성하며, `validate`가 frontmatter 표준 위반을 검출한다.

- [ ] **R2. SCHEMA 표준** — brain 위키 규약(페이지 frontmatter, 네이밍, `[[링크]]`, entity @header 시드 매핑, index/log 구조) 정의 + init 시 생성되는 `SCHEMA.md` 템플릿.
  - 무엇을: SCHEMA 표준·템플릿 작성 / 어디에: `opal/tools/brain-tool/templates/` 또는 스킬 references / 왜: 제안서 §5 / AC: SCHEMA.md에 4개 페이지 타입·frontmatter 필드·링크 규칙이 모두 정의되어 있다.

- [ ] **R3. opal-brain 스킬** — `opal/skills/opal-brain/SKILL.md` (단일 pilot, init/ingest/query/lint 4모드) + 레지스트리 등록(`opal-skills-registry.json`, alias `opbr`, domain knowledge).
  - 무엇을: opal-brain SKILL.md + 레지스트리 행 / 어디에: `opal/skills/opal-brain/`, `opal/core/references/opal-skills-registry.json` / 왜: 제안서 §6 / AC: `//opbr` 매칭이 skill-registry에서 성공하고, SKILL.md에 4모드 라우팅이 정의되어 있다.

- [ ] **R4. PM 참조 융합** — 부트스트랩 Lazy 트리거(`AGENT.md`)에 `brain/index.md` 추가 + PM 디스패치 전 프로세스(`pm/dispatch-process.md`)에 brain 조회 단계 + 프로젝트 `.opal/AGENT.md`에 "opal-brain 활용 규칙" 신설.
  - 무엇을: 부트스트랩·dispatch·AGENT.md 수정 / 어디에: 해당 SSOT 문서 / 왜: 제안서 §8.1, 요구 ① / AC: 세 문서에 brain 참조 규칙이 code-scan 우선 규칙과 동형으로 기재된다.

- [ ] **R5. CLOSE 자동 ingest 훅** — pilot CLOSE 단계에 brain ingest 훅 추가 + `op-brain-ingest` 경량 워커 스킬(또는 brain-tool 직접 호출). ingest 대상/제외 기준 명시.
  - 무엇을: pilot CLOSE 수정 + ingest 메커니즘 / 어디에: pilot SKILL.md, 신규 워커 스킬 / 왜: 제안서 §8.2, 요구 ② / AC: CLOSE 시 태스크 결정·신규 엔티티가 brain 페이지로 누적되고 log·index가 갱신된다 (PLAN에서 적용 pilot 범위 확정).

- [ ] **R6. 외부 소스 파이프라인** — 외부 소스(웹/PDF/이미지/파일)를 `.opal/brain/sources/`에 원본+요약 저장. wtm-agent·xlsx-tool 연동. 내부 코드는 참조만.
  - 무엇을: sources/ 처리 로직 / 어디에: opal-brain ingest 모드 / 왜: 제안서 §8.3, 요구 ③ / AC: `//opbr ingest <URL>` 시 sources/에 raw.md+meta.yaml가 저장되고 요약 페이지가 생성된다.

- [ ] **R7. 배포 + 시드 적용** — install 스크립트(mac/linux/windows)에 opal-brain 스킬·brain-tool 동기화 반영 + 현재 opal 프로젝트에 `//opbr init` 적용해 brain 시드 생성.
  - 무엇을: install 3종 수정 + opal brain 시드 / 어디에: `scripts/install/` / 왜: 제안서 §10, PM 배포 경계 원칙 / AC: install 후 `~/.opal/skills/opal-brain/`·`~/.opal/tools/brain-tool/`가 존재하고, opal 프로젝트에 `.opal/brain/`이 생성된다.

> Phase 분해·선별 임계값·배치 정책·CLOSE 적용 pilot 범위는 PLAN에서 확정한다. understand-anything 그래프 연동(R3 리스크)·기존 태스크 소급 ingest는 후속 태스크 분리 권고.

## 제약 조건

- **배포 경계 준수** — `~/.opal/` 직접 편집 금지. 프로젝트 소스(`opal/`, `scripts/`) 수정 후 install로 배포.
- **플랫폼 독립성** — brain 구조·SCHEMA는 마크다운 네이티브, 플랫폼 분기는 어댑터(install)에만.
- **하네스 정합** — index·log·링크는 brain-tool 집행(enforce, don't advise). state-tool 패턴 준용.
- **단방향 동기화** — @header→brain entity는 단방향(코드 SSOT), brain→코드 역방향 갱신 금지.
- **비용 관리** — `ingest --all`은 명시 옵션, 병렬 배치·멱등 skip로 토큰·시간 제어.
- **변경이력 의무** — 수정하는 스킬·참조 문서에 변경이력 행 추가 (일시 KST + 태스크 015).

## 기술 스택

- Markdown / YAML frontmatter (brain 페이지·SCHEMA)
- 도구 구현: Node.js 또는 Python (brain-tool — 기존 code-scan(Node)/state-tool(Python) 중 정합 선택, PLAN 결정)
- Bash (run.sh 래퍼, install 스크립트)
- 기존 OPAL 도구 연동: code-scan, wtm-agent, xlsx-tool, state-tool

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-brain 설계 제안서 | `docs/proposals/opal-brain-design.md` | 본 태스크의 설계 SSOT (13절 전체) |
| D-2 | 외부 | Karpathy llm-wiki | [llm-wiki gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md) | 위키 사상 원전 |
| D-3 | 설계 | OPAL 하네스 (SSOT) | `opal/core/references/opal-harness.md` | Guards/Gates/State/도구 패턴 |
| D-4 | 설계 | PM 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | R4 brain 참조 단계 삽입 위치 |
| D-5 | 설계 | code-scan 관리 | `opal/core/references/pm/code-scan-management.md` | PM 우선 활용 패턴 (R4 동형 기준) |
| D-6 | 소스 | state-tool | `opal/tools/state-tool/` | brain-tool 도구 구현 패턴 참조 |
| D-7 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 폴더 구조·네이밍·배포 경계 |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | @header·변경이력·도구/배포 규칙 |

# TASK: OPAL Project Brain 지능화 — opal-wiki-pilot 완성

> 작성일: 2026-06-11 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 (015 코어 위에 init 제안·ingest 전체·tasks 장기기억·트리거·검색 강화)
> 출력: TASK.md

## 작업 목표

015에서 만든 opal-brain 코어를 캡틴이 그린 **opal-wiki-pilot 비전**으로 지능화한다. 핵심은 (1) init이 origin을 분석해 wiki 구조를 제안하고, (2) ingest --all이 문서 전체를 적재하며, (3) tasks/를 장기기억으로 검색하고, (4) ingest/search가 적절한 시점에 자동 트리거되어 pilot·skill이 wiki를 브레인으로 활용하는 것이다.

## 배경

015가 brain 코어(brain-tool 도구 + opal-brain 4모드 스킬 + PM 융합 + opp CLOSE 훅 + brain 시드)를 완성했다. 그러나 캡틴 명확화로 두 핵심 지능이 부족함이 드러났다: init은 골격+@header 시드만(구조 제안 없음), ingest --all은 code-scan @header(코드 2개)만(문서 .md 미포함). 이 둘이 "wiki를 진짜 브레인으로 만드는" 심장이다.

## 배경 분석 (대화에서 도출)

- **origin ↔ wiki 작동 원리** — origin(`/docs`·`/tasks`·소스 = SSOT, git 관리) → wiki(`.opal/brain` = 요약+참조 파생) 단방향. wiki는 원본 복사 아닌 요약+포인터. 외부 소스(웹/PDF)만 `sources/`에 원본 보관.
- **3계층 기억** — MEMORY.md(단기·FIFO 10) → brain(장기 검색·요약) → tasks/(장기 원본). brain search로 발견 → tasks/ 원본 drill-down.
- **015 한계** — init만 실행하고 ingest --all을 안 해 시드 빈약(@header 2개). 문서(.md)는 code-scan 대상 외라 brain에 미반영.

## 확정된 설계 방향 (대화에서 합의 — 모든 a)

| # | 결정 | 내용 |
|---|------|------|
| 1 | 작동 원리 | origin=SSOT / wiki=요약+참조 파생 / **단방향**(origin→wiki). wiki 페이지=WHY/HOW 요약 + `file_path`·`task:NNN` 포인터 |
| 2 | wiki 깊이 | 요약+참조 (본문 복제 X). 외부 소스만 `sources/` 원본 보관 |
| 3 | init 동적 제안 | origin(docs/tasks/소스) 분석 → 프로젝트별 최적 wiki 도메인·구성 제안 → 사용자 확인 후 구성 |
| 4 | 구조 동적 수준 | **페이지 타입 세트 완전 동적** — 기본 4종(entity/concept/flow/synthesis)은 **검토 후보**일 뿐, init이 origin 분석으로 채택/제외/추가/전면 교체. SCHEMA가 타입 SSOT, brain-tool은 하드코딩 없이 SCHEMA에서 타입 동적 로드. 도메인·index 카테고리·시드 대상도 동적 |
| 5 | ingest --all 범위 | code-scan @header(코드)뿐 아니라 **docs·스킬·참조(.md) 전체**를 요약 페이지로 적재 |
| 6 | tasks 장기기억 | 3계층(MEMORY/brain/tasks) 명문화 + 기존 001~015 소급 백필 + `task:NNN` drill-down 링크 |
| 7 | ingest 트리거 | ① 태스크 종료(자동, 015 구현) ② 사용자 요청(구현) ③ **PM 판단(신규, 모드연동: agentic 자율 / semi·interactive 제안)** |
| 8 | search 시점 | **on-demand 3시점** — 작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의. **부트스트랩 전체 index 자동 로드 안 함**(컨텍스트 부담 회피). index는 brain-tool 내부 카탈로그로 LLM 비상주, search가 키워드 매칭 페이지만 반환 |
| 9 | pilot 확산 | opp CLOSE 파일럿(015) → 나머지 7 pilot(opd/opds/opdw/opwt/oppd/opsdd/opgc) 확산 |
| 10 | 배포·이름 | install 통합 실행(brain 글로벌 배포, //opbr 매칭 활성화) + 이름 정리(opal-brain vs opal-wiki 결정) |

## 요구사항

- [ ] **W1. init 동적 구조 제안 (페이지 타입 세트 포함)** — origin(docs/tasks/소스 @header·폴더구조) 분석 → **페이지 타입 세트(기본 4종 검토 + 프로젝트 고유 타입 추가/교체)** · 도메인 · index 카테고리 · 핵심 시드 대상 제안 → 사용자 확인 → SCHEMA 확정 → 구성.
  - 무엇을: opal-brain init에 분석·타입제안 단계 + brain-tool 타입 동적화 / 어디에: `opal/skills/opal-brain/SKILL.md` init STEP, `opal/tools/brain-tool/brain_tool.py`(`PAGE_TYPES`·`TYPE_TO_CATEGORY` 하드코딩 제거 → SCHEMA 로드) / 왜: 확정 §3·§4 / AC: `//opbr init` 시 origin 분석으로 타입 세트·도메인·구성을 제안하고, 사용자 확인 후 SCHEMA에 타입이 확정되며, brain-tool이 그 타입으로 검증·디렉토리를 구성한다.

- [ ] **W2. ingest --all 문서 전체** — docs/·스킬·참조(.md) + 소스 @header 전체를 요약 페이지로 적재. origin 본문 복제 없이 요약+참조. 결정5 배치 정책(5자산/배치, 멱등 skip).
  - 무엇을: ingest --all 소스 범위를 문서 전체로 확장 / 어디에: opal-brain ingest 모드 + brain-tool 보조(문서 스캔) / 왜: 확정 §5 / AC: `//opbr ingest --all` 시 docs·스킬·참조가 요약 페이지로 적재되고 각 페이지가 origin 경로를 참조한다.

- [ ] **W3. tasks 장기기억 3계층** — MEMORY(단기)/brain(장기검색)/tasks(장기원본) 역할을 문서·SCHEMA에 명문화 + tasks/를 1급 ingest 소스로(`ingest task:NNN`) + 기존 001~015 소급 백필 + brain 페이지에 `task:NNN` drill-down.
  - 무엇을: 3계층 명문화 + tasks ingest + 소급 백필 / 어디에: SCHEMA·SKILL·brain 페이지, `.opal/brain/` / 왜: 확정 §6 / AC: `//opbr ingest task:NNN`가 동작하고, 백필 후 brain search로 과거 태스크 결정을 검색·drill-down할 수 있다.

- [ ] **W4. ingest PM 판단 트리거** — PM이 작업 중 가치 있는 지식(아키텍처 결정·반복 패턴·캡틴 합의·비자명 해결)을 감지하면 ingest. 모드 연동(agentic 자율 / 그 외 제안).
  - 무엇을: PM 판단 ingest 규칙 / 어디에: `opal/core/AGENT.md` 또는 PM 참조 문서(opal-pm.md / pm/*) / 왜: 확정 §7 / AC: PM 행동 규칙에 ingest 판단 트리거와 모드별 동작이 명시된다.

- [ ] **W5. search on-demand 3시점 + 선택적 주입 + index 비상주** — 작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의. **흐름: brain-tool search가 후보 목록(page·title·score·snippet, 본문 X)만 반환 → 제시 → 선택 → 선택된 페이지만 Read하여 컨텍스트 주입.** 선택 주체: 사용자 질의(`//opbr ask`)=사용자 선택 / PM 자동(작업·디스패치 전)=PM이 score 상위 선별(불확실 시 사용자 확인). **015 R4의 부트스트랩 `brain/index.md` Lazy 자동 로드를 제거·정정**(부트스트랩은 brain 존재 여부만 경량 인지).
  - 무엇을: search 3시점 + 후보 제시→선택→주입 흐름 + R4 부트스트랩 index 로드 정정 / 어디에: `opal/core/AGENT.md`·`dispatch-process.md`·`opal-brain/SKILL.md`(query 모드) / 왜: 확정 §8 + 캡틴 선택적 주입·컨텍스트 부담 우려 / AC: search가 본문 아닌 후보 목록을 반환하고, 선택된 페이지만 컨텍스트에 주입되며, 부트스트랩에 index 전체 로드가 없다.

- [ ] **W6. 전체 pilot CLOSE ingest 확산** — opp 파일럿(015)을 나머지 7 pilot CLOSE에 확산. STATE 행 구조 불변(각 pilot rows 검증).
  - 무엇을: 7 pilot CLOSE에 op-brain-ingest 훅 / 어디에: `opal/skills/opal-pilot-*/SKILL.md` / 왜: 확정 §9 / AC: 7 pilot CLOSE에 ingest 훅이 삽입되고 각 pilot STATE rows_count가 불변이다.

- [ ] **W7. install 통합 배포 + 이름 정리 + brain git 추적 정책** — 016 코드 완료 후 install 실행(brain-tool·스킬 글로벌 배포). //opbr 레지스트리 매칭 활성화 검증. opal-brain vs opal-wiki 이름 결정·반영. **brain git 추적 정책 결정** — 현재 `.gitignore`가 `.opal/`을 무시해 `.opal/brain/`·`code-scan.json`이 커밋 제외됨. brain을 공유 자산으로 추적할지(`.gitignore` 예외 추가) vs 로컬 전용으로 둘지 결정.
  - 무엇을: install 실행 + 이름 정리 + brain git 정책 / 어디에: `scripts/install-mac.sh` 실행, 레지스트리/스킬 명, `.gitignore` / 왜: 확정 §10 + 커밋 시 발견 / AC: install 후 `~/.opal/tools/brain-tool`·`~/.opal/skills/opal-brain(또는 opal-wiki)` 존재 + `//opbr` 매칭 성공 + brain git 추적 여부 확정·반영.

> 페이지 타입 4종은 고정(확정 §4). init 분석 로직의 정량 기준·ingest --all 문서 요약 깊이·소급 백필 범위·이름 최종안은 PLAN에서 확정한다.

## 제약 조건

- **index 비상주 (컨텍스트 부담 회피)** — brain index 전체를 세션 컨텍스트에 자동 로드하지 않는다. search는 후보 목록만 반환하고 선택된 페이지만 주입(RAG식 전량 로드 금지). 부트스트랩은 brain 존재 여부만 경량 인지. (확정 §8, 캡틴 우려)
- **결정론적 작업 = brain-tool** — search·index·log·sync-header·lint·validate 등 결정론적 작업은 brain-tool(도구)이 수행한다. LLM은 페이지 본문 작성·관련성 판단·요약만 한다. (015 집행 경계 계승, "enforce, don't advise")
- **단방향 동기화** — origin→wiki 읽기만. wiki→origin 역수정 금지. (확정 §1)
- **복사 아닌 요약+참조** — 내부 문서/코드는 포인터, 외부 소스만 sources/ 원본. (확정 §2)
- **STATE 행 불변** — pilot CLOSE 훅 확산 시 각 pilot rows_count 회귀 금지(014 정합). 015 opp 9행 유지 검증 패턴 준용.
- **배포 경계** — `opal/`·`scripts/` 소스 수정 후 install 배포. `~/.opal` 직접 편집 금지.
- **015 자산 재사용** — brain-tool·opal-brain·op-brain-ingest를 확장하며, 기존 동작 회귀 금지.
- **변경이력 의무** — 수정 스킬·참조 문서에 변경이력 행 추가 (KST + 016).

## 기술 스택

- Python (brain-tool 확장 — 문서 스캔 보조), Markdown/YAML (wiki 페이지·SCHEMA), Bash/PowerShell (install)
- 기존 연동: code-scan(@header), web-to-markdown·xlsx-tool(외부 소스), state-tool(패턴)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-brain 설계 제안서 | `docs/proposals/opal-brain-design.md` | 015 설계 SSOT (지능화 기반) |
| D-2 | 소스 | 015 DONE.md | `tasks/015-260610-opp-opal-brain/DONE.md` | 코어 완료 산출물 + 016 이월 명세 |
| D-3 | 소스 | brain-tool | `opal/tools/brain-tool/` | 확장 대상 도구 (8커맨드) |
| D-4 | 소스 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` | init/ingest 모드 확장 대상 |
| D-5 | 소스 | brain SCHEMA | `opal/tools/brain-tool/templates/schema-template.md` | 3계층·페이지 표준 |
| D-6 | 설계 | PM 디스패치/code-scan 규칙 | `opal/core/AGENT.md`, `opal/core/references/pm/dispatch-process.md` | search 4시점·PM판단 ingest 융합 |
| D-7 | 소스 | pilot 7종 SKILL | `opal/skills/opal-pilot-*/SKILL.md` | W6 CLOSE 훅 확산 대상 |
| D-8 | 외부 | Karpathy llm-wiki | [llm-wiki gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md) | 위키 사상 원전 |

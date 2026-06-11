# PLAN: OPAL Project Brain 지능화 — opal-wiki-pilot 완성

> 작성일: 2026-06-11
> 입력: TASK.md (요구사항 W1~W7)
> 출력: PLAN.md
> 모드: agentic — TASK 이월 항목은 옵션 비교 + 권고안 + 근거로 확정한다

---

## 0. 이월 의사결정 확정 (agentic — PM 즉시 결정용)

> TASK.md가 "PLAN에서 확정한다"로 이월한 5개 항목을 각각 **옵션 비교 + 권고안 + 근거**로 제시한다. 각 결정에 M-N 식별자를 부여하여 본문 설계에서 인용한다.

### M-1. init 동적 분석 로직의 정량 기준

| 옵션 | 내용 | 트레이드오프 |
|------|------|-------------|
| A. LLM 자유 판단 | init이 origin을 읽고 타입·도메인을 자유 추론 | 결정성 없음 — 매 실행 결과 상이, "enforce, don't advise" 위반 |
| B. brain-tool 정량 추출 + LLM 큐레이션 (권고) | brain-tool이 code-scan @header에서 `domain`·`layer` 빈도·exports·피의존도를 **정량 집계**(`brain-tool analyze`)하고, LLM은 그 통계 위에서 타입 세트·도메인을 제안 | 결정성 있는 데이터 + LLM 의미 판단 분리 (헌법 정합) |
| C. 전량 페이지화 | 모든 @header를 entity로 | code-scan과 1:1 중복, noise (설계 §6.1.1 명시 반대) |

**권고: B.** 근거 — `[MUST] tasks/016/TASK.md §제약: "결정론적 작업 = brain-tool. search·index·log·sync-header·lint·validate 등 결정론적 작업은 brain-tool(도구)이 수행한다. LLM은 페이지 본문 작성·관련성 판단·요약만 한다."` → origin 통계 집계는 결정론적이므로 brain-tool `analyze` 신설. 정량 기준 SSOT는 기존 `SEED_THRESHOLDS`(`brain_tool.py:50-54`)를 계승·노출:

- **도메인 채택**: code-scan @header `domain` 값별 모듈 수 집계 → 모듈 ≥ 1개인 모든 domain을 index 카테고리 후보로 제시.
- **타입 세트 제안**: 기본 4종(entity/concept/flow/synthesis)을 **검토 후보**로 제시하되, origin에 `layer`로 `pilot`/`orchestrator`가 존재하면 `flow` 채택 강제, 아키텍처 결정 문서(`docs/proposals/`·`docs/ARCHITECTURE.md`)가 존재하면 `concept` 채택 강제. 후보 외 신규 타입은 LLM이 origin 특성 근거와 함께 제안 → 사용자 확인.
- **핵심 엔티티 시드 임계값** (`SEED_THRESHOLDS` 계승): `exports ≥ 3` OR `피의존도 ≥ 2` OR `layer ∈ {orchestrator, tool, pilot, core}` OR `domain 대표 1개`. (→ `brain_tool.py:50-54`, SKILL.md init STEP)

### M-2. ingest --all 문서 요약 깊이

| 옵션 | 깊이 | 토큰 비용 | 적합도 |
|------|------|----------|--------|
| A. 헤더+첫 단락만 | 얕음 | 최소 | 문서 WHY 누락 — 브레인 가치 저하 |
| B. 섹션 요약 + 포인터 (권고) | 중간 — 각 문서를 §단위로 요약, 본문 복제 없이 `file_path` 포인터 | 중간 (배치 5자산) | origin=SSOT 유지 + WHY 포착 정합 |
| C. 전문 재서술 | 깊음 | 최대 | 본문 복제에 근접 — `[MUST] §제약: "복사 아닌 요약+참조"` 위반 위험 |

**권고: B.** 근거 — `[MUST] tasks/016/TASK.md §제약: "복사 아닌 요약+참조 — 내부 문서/코드는 포인터, 외부 소스만 sources/ 원본."` 각 .md 문서당 1개 concept 페이지를 생성하되, 본문은 **3~6줄 요약(목적·핵심 결정·적용 범위) + `file_path` 포인터**로 한정. 코드 @header는 기존 entity 시드 깊이 유지(@header 흡수 + `source_ref`). (→ schema-template §2.2, SKILL.md ingest STEP)

### M-3. 소급 백필 범위 (001~015)

| 옵션 | 범위 | 비용 | 가치 |
|------|------|------|------|
| A. 전체 15태스크 본문 ingest | 001~015 DONE/PLAN 전량 | 큼 | noise 위험 (사소 태스크 포함) |
| B. 선별 백필 (권고) | DONE.md가 있는 태스크 중 **아키텍처/신규 컴포넌트/인터페이스 변경**을 포함한 태스크만 — 태스크당 concept 1개(핵심 결정) + `task:NNN` 링크 | 중간 | 복리 가치 높은 결정만 |
| C. 백필 생략 | tasks ingest 메커니즘만 구현, 백필은 사후 | 최소 | 3계층 "장기원본" 실증 안 됨 |

**권고: B.** 근거 — `op-brain-ingest/SKILL.md:50-70`의 포함/제외 기준을 백필에 재사용(중복 로직 회피). 15개 태스크 DONE.md를 스캔하여 제외 기준(오타·trivial)에 해당하지 않는 태스크만 concept 페이지화. 백필은 ingest --all과 동일 배치 정책(5자산/배치, 멱등 skip) 적용. 단발 실행이므로 사용자 확인 후 진행. (→ SKILL.md ingest `task:NNN` 모드)

### M-4. 이름 최종안 — opal-brain vs opal-wiki

| 옵션 | 장점 | 단점 |
|------|------|------|
| A. opal-brain 유지 (권고) | 015 자산(스킬명·alias `opbr`·brain-tool·`.opal/brain/`·레지스트리·페이지 30+ 참조·6 PM 문서)이 모두 `brain` 기준. 변경 시 전면 리네임 비용 + 회귀 위험 | "wiki-pilot" 비전 용어와 표면 불일치 |
| B. opal-wiki로 리네임 | 캡틴 비전 용어 정합 | 디렉토리/alias/레지스트리/30+ 페이지 링크/install/6 PM 문서 전면 교체 — 016 범위 폭증 + 회귀 |

**권고: A (opal-brain 유지).** 근거 — `[MUST] tasks/016/TASK.md §제약: "015 자산 재사용 — brain-tool·opal-brain·op-brain-ingest를 확장하며, 기존 동작 회귀 금지."` 이름 변경은 자산 재사용 원칙과 정면 충돌하며 016의 핵심(지능화) 대비 가치가 낮다. "opal-wiki-pilot"은 **비전·컨셉 명칭**으로 문서(설계 SSOT)에만 병기하고, 구현 식별자는 `opal-brain`/`opbr`/`brain-tool`을 유지한다. (→ schema-template, opal-brain/SKILL.md)

### M-5. brain git 추적 정책

| 옵션 | 내용 | 트레이드오프 |
|------|------|-------------|
| A. 로컬 전용 유지 | 현 `.gitignore`의 `.opal/` 무시 유지 | brain이 PC 간 공유 안 됨 — "프로젝트 자산" 비전 미달 |
| B. brain만 예외 추적 (권고) | `.gitignore`에 `!.opal/brain/` 예외 추가 (`.opal/` 나머지·`code-scan.json`은 계속 무시) | brain 페이지가 git에 커밋되어 팀·멀티PC 공유 + 리뷰 가능 |
| C. .opal/ 전체 추적 | `.opal/` 무시 해제 | identity·MEMORY·code-scan.json 등 로컬/민감 데이터까지 커밋 — 부적절 |

**권고: B.** 근거 — 설계 §R2(`docs/proposals/opal-brain-design.md:379`) "멀티 PC/멀티 에이전트 동시 ingest 시 index 충돌 → git merge 전략"은 brain이 git 추적됨을 전제. brain은 사람이 읽는 .md SSOT(헌법 "User sovereignty")이므로 공유 자산화가 정합. `.gitignore` 패턴:
```
.opal/
!.opal/brain/
!.opal/brain/**
```
단, `code-scan.json`은 계속 무시(파생 캐시). (→ `.gitignore:2`)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-brain 설계 SSOT | `docs/proposals/opal-brain-design.md` | 지능화 기반 설계 (13절) |
| D-2 | 소스 | 015 DONE | `tasks/015-260610-opp-opal-brain/DONE.md` | 코어 완료 범위 + 016 이월 명세 |
| D-3 | 소스 | brain-tool 본체 | `opal/tools/brain-tool/brain_tool.py` | W1 타입 동적화 대상 (하드코딩 상수 6종) |
| D-4 | 소스 | brain-tool 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 66 테스트 회귀 방지 기준 |
| D-5 | 소스 | opal-brain 스킬 | `opal/skills/opal-brain/SKILL.md` | W1 init / W2 ingest / W5 query 확장 대상 |
| D-6 | 소스 | brain SCHEMA 템플릿 | `opal/tools/brain-tool/templates/schema-template.md` | W1 타입 SSOT / W3 3계층 명문화 |
| D-7 | 설계 | PM AGENT | `opal/core/AGENT.md` | W4 PM 판단 ingest / W5 부트스트랩 index 정정 |
| D-8 | 설계 | PM 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | W4·W5 search 시점 융합 (Step 1.5) |
| D-9 | 소스 | op-brain-ingest 워커 | `opal/skills/op-brain-ingest/SKILL.md` | W3 백필 기준 재사용 / W6 확산 패턴 |
| D-10 | 소스 | opp pilot CLOSE | `opal/skills/opal-pilot-project/SKILL.md` | W6 확산 기준 패턴 (015 기구현) |
| D-11 | 소스 | install-mac.sh | `scripts/install-mac.sh` | W7 배포 (brain-tool chmod 기존 958-963줄) |
| D-12 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 구현 규칙·네이밍·변경이력 의무 |
| D-13 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | 배포 모델·구조 정합 |
| D-14 | 소스 | brain 시스템 개요 페이지 | `.opal/brain/pages/concept/opal-brain-system.md` | 015 과거 결정 맥락 |
| D-15 | 외부 | Karpathy llm-wiki | [llm-wiki gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md) | 위키 사상 원전 (3계층·타입·워크플로우) |

### 핵심 컨벤션 제약 (CONVENTIONS.md 인용)

- `[MUST] docs/CONVENTIONS.md §언어 규칙: "코드/변수/필드명: English / YAML frontmatter 키: English / 파일·폴더: kebab-case (Python 파일은 snake_case)"`
- `[MUST] docs/CONVENTIONS.md §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 YYYY-MM-DD HH:mm (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."`
- `[MUST] docs/CONVENTIONS.md §배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(opal/, skills/, agents/, scripts/)에서 수행한다."`
- `[MUST] docs/CONVENTIONS.md §플랫폼 분기 격리: "플랫폼별 차이는 어댑터 계층에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."`

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/brain-tool/brain_tool.py` | brain-tool CLI 본체 | **수정** (W1 타입 동적화, ingest 보조 명령, analyze 신설) | `brain_tool.py:29-60` (상수), `:288-331` (init), `:739-819` (argparse) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | 단위 테스트 | **수정** (동적 타입·신규 명령 테스트 추가, 66 회귀 유지) | `test_brain_tool.py:963-965` (`BT.PAGE_TYPES` 참조) |
| `opal/tools/brain-tool/templates/schema-template.md` | 타입 SSOT 규약 | **수정** (타입 동적 선언 블록 + 3계층 명문화) | `schema-template.md:41` (타입 enum) |
| `opal/skills/opal-brain/SKILL.md` | brain pilot 4모드 | **수정** (init 분석·타입제안, ingest --all 문서, query 후보→선택→주입, tasks ingest) | `SKILL.md:45-117` (init), `:120-168` (ingest), `:171-203` (query) |
| `opal/skills/op-brain-ingest/SKILL.md` | CLOSE 경량 워커 | **수정** (백필 기준 재사용 명시, 동적 타입 정합) | `op-brain-ingest/SKILL.md:50-70` |
| `opal/core/AGENT.md` | PM 부트스트랩·규칙 | **수정** (W5 index 비상주 정정, W4 PM 판단 ingest 규칙) | `AGENT.md:40` (brain index Lazy 행), `:191-203` (opal-brain 활용 규칙) |
| `opal/core/references/pm/dispatch-process.md` | PM 디스패치 | **수정** (W5 search 3시점·후보→선택→주입) | `dispatch-process.md:111-119` (Step 1.5) |
| `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,write-tech,project-dev,sdd,gc}/SKILL.md` | 7 pilot CLOSE | **수정** (brain ingest 훅 삽입, STATE 행 불변) | opp 기준 `opal-pilot-project/SKILL.md:118-135` |
| `scripts/install-mac.sh` | 배포 | **확인/수정** (brain-tool chmod 기존, date 의존 확인) | `install-mac.sh:958-963` |
| `.gitignore` | git 추적 | **수정** (M-5 brain 예외) | `.gitignore:2` |
| `docs/proposals/opal-brain-design.md` | 설계 SSOT | **수정** (지능화 반영 — docs/ 갱신 Step) | D-1 전체 |
| `.opal/brain/` | 현 프로젝트 brain | **갱신** (016 dogfooding — ingest --all + 백필 적용) | D-14 |

### 현재 상태

015가 brain 코어를 완성했다 — brain-tool 8커맨드(66 테스트 통과), opal-brain 4모드 스킬, op-brain-ingest 워커, opp CLOSE 훅, brain 시드(entity 2 + concept 1). 그러나:

1. **타입 하드코딩**: `brain_tool.py:29-38`이 `PAGE_TYPES`·`TYPE_TO_CATEGORY`·`CATEGORY_ORDER`를, `:57-60`이 `BRAIN_DIRS`를 하드코딩. `validate_frontmatter`(`:206`)·`render_index`(`:243`)·`cmd_add_page`(`:343`)·`cmd_validate`(`:719`)·argparse `choices=PAGE_TYPES`(`:771,796`)·`ERROR_CODES` 메시지(`:72`)가 모두 이 상수에 결합. → W1이 SCHEMA 동적 로드로 전환해야 할 대상.
2. **init이 골격+시드만**: 구조 제안 단계 없음 (SKILL.md `:45-117`).
3. **ingest --all이 코드만**: `SKILL.md:156-168` 배치 정책은 있으나 docs/.md 스캔 미포함.
4. **tasks 3계층 미명문화**: `task:NNN` ingest 모드·백필 메커니즘 부재.
5. **W5 부트스트랩 index 자동 로드**: `AGENT.md:40` Lazy 트리거가 `.opal/brain/index.md`를 PM 컨텍스트 로드 시 자동 로드 → TASK가 "정정" 요구(index 비상주).
6. **CLOSE 훅 opp 단독**: 7 pilot 미확산.
7. **install 미실행 + git 미추적**: `.gitignore:2`가 `.opal/` 무시.

### 영향 범위

- **brain-tool 타입 동적화**(W1)가 최하위 레이어 — `validate`/`add-page`/`index`/`sync-header` 전 명령이 타입 상수에 의존하므로 가장 먼저, 가장 신중히 변경. 66 테스트 회귀가 1차 가드.
- **argparse `choices=PAGE_TYPES` 제거**가 구조적 난점 — 파서 빌드 시점엔 brain_path 미확정이라 SCHEMA를 읽을 수 없음 → `--type` 검증을 argparse에서 명령 함수 내부(brain_root 확정 후)로 이동.
- **기존 테스트의 `BT.PAGE_TYPES` 참조**(`:965`) — 모듈 상수를 "기본 후보(DEFAULT_PAGE_TYPES)"로 보존하고, brain 인스턴스 타입은 SCHEMA에서 동적 로드하는 2계층 설계로 호환 유지.
- **W5 정정**은 PM 문서 3종(AGENT.md·dispatch-process.md·SKILL.md) 일관 수정 필요.
- **W6 7 pilot**은 각 STATE rows_count 불변이 핵심 가드(014 정합).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | (없음 — 신규 파일 없음. 전부 기존 자산 확장) | 015 자산 재사용 원칙 | `[MUST] TASK §제약 015 자산 재사용` |

> brain-tool에 신규 서브명령(`analyze`, `ingest-scan`)을 추가하되 기존 `brain_tool.py` 내 함수로 확장하므로 신규 파일 없음.

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| U-1 | `opal/tools/brain-tool/templates/schema-template.md` | 타입 세트 동적 선언 블록(§1.5 "페이지 타입 정의") 추가 — brain-tool이 파싱할 타입 SSOT. 3계층 기억(MEMORY/brain/tasks) 명문화 절 추가. `task:NNN` sources 형식 명시 | W1·W3 / D-1 §5 |
| U-2 | `opal/tools/brain-tool/brain_tool.py` | (a) `PAGE_TYPES`→`DEFAULT_PAGE_TYPES`(기본 후보), SCHEMA 파싱 `load_page_types(brain_root)` 신설 (b) `TYPE_TO_CATEGORY`·`CATEGORY_ORDER`·`BRAIN_DIRS` 동적 파생 (c) `--type` 검증을 argparse choices→명령 함수 내부 이동 (d) `analyze` 서브명령 신설(origin 정량 집계) (e) `ingest-scan` 서브명령 신설(docs/.md·tasks 스캔 목록 반환) (f) `log` op enum에 `ingest`/`backfill` 정합 | W1·W2·W3 / D-3 |
| U-3 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 동적 타입 로드 테스트 + analyze/ingest-scan 테스트 + argparse 변경 회귀 테스트 추가. 기존 66 테스트는 `DEFAULT_PAGE_TYPES` 폴백으로 통과 유지 | W1 / D-4 |
| U-4 | `opal/skills/opal-brain/SKILL.md` | (a) init에 STEP 0 "origin 분석·타입 세트 제안→사용자 확인→SCHEMA 확정" 추가 (b) ingest --all에 docs/.md·스킬·참조 스캔 범위 명문화(M-2 깊이) (c) `ingest task:NNN` 모드 + 001~015 백필 절차 추가(M-3) (d) query를 "후보 목록 반환→제시→선택→선택 페이지만 주입"으로 정정(W5) | W1·W2·W3·W5 / D-5 |
| U-5 | `opal/skills/op-brain-ingest/SKILL.md` | 백필 기준이 본 워커 포함/제외 기준과 동일함을 명시(재사용). 동적 타입(SCHEMA 로드) 정합 1줄 | W3 / D-9 |
| U-6 | `opal/core/AGENT.md` | (a) Lazy 트리거 테이블 `.opal/brain/index.md` 행을 **"brain 존재 여부 경량 인지(index 전체 자동 로드 안 함)"**로 정정(W5) (b) "opal-brain 활용 규칙"에 PM 판단 ingest 트리거(모드 연동) 추가(W4) | W4·W5 / D-7 |
| U-7 | `opal/core/references/pm/dispatch-process.md` | Step 1.5를 search **3시점**(작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의) + **후보 목록→score 선별→불확실 시 사용자 확인→선택 페이지만 주입** 흐름으로 확장(W5) | W5 / D-8 |
| U-8~U-14 | `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,write-tech,project-dev,sdd,gc}/SKILL.md` | 각 pilot CLOSE(또는 종료) 단계에 opp와 동형 brain ingest 훅 삽입. STATE rows_count 불변 | W6 / D-10 |
| U-15 | `scripts/install-mac.sh` | brain-tool chmod 기존 확인 + date.js 의존성(brain-tool이 `~/.opal/tools/date/date.js` 호출) 배포 검증. 변경 필요 시에만 수정 | W7 / D-11 |
| U-16 | `.gitignore` | M-5 — `!.opal/brain/` 예외 추가 | W7 / D-1 §R2 |
| U-17 | `docs/proposals/opal-brain-design.md` | 지능화 설계 반영(init 분석·ingest --all 문서·3계층·index 비상주 정정·이름 결정) — docs/ 갱신 Step | docs 정합 / D-1 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | - | 삭제 대상 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | SCHEMA 타입 동적 선언 + 3계층 명문화 | U-1 (schema-template) | 중 |
| 2 | brain-tool 타입 동적 로드 + analyze/ingest-scan + argparse 이동 | U-2 (brain_tool.py) | **상** |
| 3 | brain-tool 테스트 갱신 (66 회귀 + 신규) | U-3 (test) | 상 |
| 4 | opal-brain 스킬 4모드 확장 | U-4 (SKILL.md) | 상 |
| 5 | op-brain-ingest 백필 정합 | U-5 | 하 |
| 6 | PM AGENT.md 정정 (W4·W5) | U-6 | 중 |
| 7 | dispatch-process.md search 3시점 | U-7 | 중 |
| 8 | 7 pilot CLOSE 훅 확산 | U-8~U-14 | 중 (병렬 가능) |
| 9 | .gitignore brain 예외 | U-16 | 하 |
| 10 | install 검증 + (필요 시) 수정 | U-15 | 하 |
| 11 | 설계 SSOT 갱신 | U-17 | 하 |
| 12 | 현 프로젝트 brain dogfooding (ingest --all + 백필) | `.opal/brain/` | 중 (EXECUTE 후) |

### 핵심 설계

> 인라인 인용: `(→ D-N)` 또는 `` `경로:줄번호` ``. 필수 제약은 `[MUST]`.

#### U-1. schema-template.md — 타입 SSOT + 3계층

타입 세트를 brain-tool이 파싱 가능한 **선언 블록**으로 명문화한다. 현 `:41`의 산문 enum을 구조화된 블록으로 승격:

```markdown
## 1.5 페이지 타입 정의 (brain-tool 동적 로드 SSOT)

> brain-tool은 이 블록에서 타입 세트를 동적 로드한다. 하드코딩하지 않는다.

| type | category(index 헤더) | 설명 |
|------|---------------------|------|
| entity | 엔티티 | 코드 모듈·서비스·도구·스킬 |
| concept | 개념 | 아키텍처 결정·설계 배경 |
| flow | 흐름 | 파이프라인·프로세스 흐름 |
| synthesis | 합성 | 질의 파생 분석 |
```

- brain-tool 파싱 규약: `## 1.5 페이지 타입 정의` 절의 마크다운 테이블에서 `type`·`category` 컬럼을 읽어 타입 세트·`TYPE_TO_CATEGORY`·`CATEGORY_ORDER`(+`도메인` 선두)·`BRAIN_DIRS`(`pages/{type}`)를 파생. (→ D-3 W1)
- init이 origin 분석 후 이 테이블을 프로젝트별로 **채택/제외/추가/교체**하여 확정. (→ M-1)
- `[MUST] tasks/016/TASK.md §확정 §4: "페이지 타입 세트 완전 동적 — 기본 4종은 검토 후보일 뿐, init이 origin 분석으로 채택/제외/추가/전면 교체. SCHEMA가 타입 SSOT, brain-tool은 하드코딩 없이 SCHEMA에서 타입 동적 로드."`
- **3계층 기억** 절 신설: MEMORY.md(단기 FIFO 10) → brain(장기 검색·요약) → tasks/(장기 원본). brain `sources: [task:NNN]`로 drill-down. (→ M-3, TASK §확정 §6)

#### U-2. brain_tool.py — 타입 동적화 (W1 핵심)

2계층 타입 모델로 회귀 안전성 확보:

- `PAGE_TYPES` → `DEFAULT_PAGE_TYPES = ["entity","concept","flow","synthesis"]` 리네임 (기본 후보 + 테스트 호환). 기존 `BT.PAGE_TYPES` 참조 테스트(`test_brain_tool.py:965`)는 `DEFAULT_PAGE_TYPES` alias 또는 동명 보존으로 통과.
- 신설 `load_page_types(brain_root) -> (types:list, type_to_category:dict)`: `SCHEMA.md` §1.5 테이블 파싱. SCHEMA 부재/파싱 실패 시 `DEFAULT_PAGE_TYPES`로 폴백(graceful degradation). (→ U-1)
- `TYPE_TO_CATEGORY`·`CATEGORY_ORDER`·`BRAIN_DIRS`를 모듈 상수 → 명령 함수 내 동적 파생으로 전환.
- **argparse `choices=PAGE_TYPES` 제거**(`:771,796`): 파서 빌드 시점엔 brain_path 미확정. `--type` 값 검증을 `cmd_add_page`/`cmd_search` 내부에서 `load_page_types` 결과로 수행. 위반 시 기존 `invalid_page_type` 에러 코드 재사용(메시지의 하드코딩된 "entity|concept|flow|synthesis"는 동적 목록으로 치환). (→ `:72,343,771,796`)
- `cmd_init`에 `--types <csv>` 옵션 추가(선택) — SKILL이 사용자 확정 타입 세트를 init에 전달. 미지정 시 `DEFAULT_PAGE_TYPES`.
- 신설 `cmd_analyze`: code-scan @header 정량 집계(domain별 모듈수·layer 분포·exports·피의존도) → JSON 반환. LLM init 제안의 결정론적 입력. (→ M-1)
- 신설 `cmd_ingest_scan`: `--source docs|skills|tasks|all`로 .md 문서·`tasks/NNN` 목록을 멱등 skip 판정과 함께 반환(LLM이 배치 요약할 대상 목록). 본문 요약은 LLM, 목록 산출은 도구. (→ M-2 [MUST] 결정론적 작업=brain-tool)
- `LOG_OPS`(`:46`)에 `backfill` 추가(또는 `ingest` 재사용 — 권고: `ingest` 재사용으로 enum 불변, summary에 "backfill" 표기).

> `[MUST] tasks/016/TASK.md §제약: "결정론적 작업 = brain-tool ... LLM은 페이지 본문 작성·관련성 판단·요약만 한다."` → analyze·ingest-scan은 집계/목록(결정론) 전담, 요약은 LLM.

#### U-3. test_brain_tool.py — 회귀 + 신규

- 기존 66 테스트 전부 통과 유지가 1차 게이트. `DEFAULT_PAGE_TYPES` 폴백 경로로 무수정 통과 목표.
- 신규: (a) SCHEMA §1.5에 커스텀 타입(예 `decision`) 선언 → add-page/validate/index가 동적 타입 인식 (b) SCHEMA 부재 시 `DEFAULT_PAGE_TYPES` 폴백 (c) `--type` 무효값 → `invalid_page_type` (argparse choices 제거 후에도 유지) (d) `analyze`·`ingest-scan` happy-path.
- `[MUST] test_brain_tool.py:17-18: "실제 brain_tool.py를 import/subprocess로 호출하는 진짜 테스트(mock 금지). tmp_path 기반 — 실제 프로젝트 .opal/brain 오염 금지."`

#### U-4. opal-brain/SKILL.md — 4모드 지능화

- **init STEP 0 신설**: `brain-tool analyze` 호출 → 통계 위에서 타입 세트·도메인·index 카테고리·핵심 시드 대상 제안 → 사용자 확인 → 확정 타입을 `init --types`로 SCHEMA 확정 → 골격 생성. (→ M-1, TASK W1)
- **ingest --all 범위 확장**: 기존 5자산/배치·멱등 skip 정책(`:156-168`) 위에 `brain-tool ingest-scan --source all` 목록 → docs/.md·스킬·참조는 concept 요약(M-2 깊이), 코드 @header는 entity 시드. (→ M-2, TASK W2)
- **ingest task:NNN 모드 + 백필**: `tasks/NNN/`의 DONE/PLAN을 읽어 concept 페이지화(`sources:[task:NNN]`). 001~015 선별 백필 절차(M-3 기준 = op-brain-ingest 포함/제외 재사용). (→ M-3, TASK W3)
- **query 정정(W5)**: `brain-tool search`가 **후보 목록(page·title·score·snippet, 본문 X)** 반환 → 제시 → 선택 → **선택 페이지만 Read 주입**. `//opbr ask`=사용자 선택. (→ TASK W5)
- `[MUST] tasks/016/TASK.md §제약: "search는 후보 목록만 반환하고 선택된 페이지만 주입(RAG식 전량 로드 금지)."`
- `[MUST] tasks/016/TASK.md §제약: "단방향 동기화 — origin→wiki 읽기만. wiki→origin 역수정 금지."`

#### U-6. AGENT.md — W5 정정 + W4 PM 판단 ingest

- **W5**: Lazy 트리거 `:40` `.opal/brain/index.md` 행을 정정 — "PM 컨텍스트 로드 시 brain **존재 여부만 경량 인지**(index.md 전체 자동 로드 안 함). 지식은 search 후보→선택 주입으로 온디맨드 로드." (→ TASK W5)
- **W4**: "opal-brain 활용 규칙"(`:191-203`)에 PM 판단 ingest 트리거 행 추가 — "작업 중 가치 지식(아키텍처 결정·반복 패턴·캡틴 합의·비자명 해결) 감지 시 ingest. **모드 연동: agentic=자율 ingest / semi·interactive=사용자 제안**." (→ TASK W4·W7)

#### U-7. dispatch-process.md — search 3시점

Step 1.5(`:111-119`)를 확장: **3시점**(작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의) + 흐름 — `brain-tool search` 후보 목록 → PM이 score 상위 선별(불확실 시 사용자 확인) → 선택 페이지만 워커 컨텍스트 주입. (→ TASK W5)

#### U-8~U-14. 7 pilot CLOSE 훅

opp 패턴(`opal-pilot-project/SKILL.md:123-131`)을 각 pilot 종료 단계에 복제. STATE rows_count 불변(훅은 기존 "DONE.md 생성" 행 내부 동작으로 삽입, 행 추가 없음):

| pilot | 종료 단계 / DONE 행 | STATE rows | 다음 버전 |
|-------|--------------------|-----------|----------|
| opd | §6 CLOSE / 행 15 | 15 불변 | v4.1 |
| opds | §5 CLOSE / 행 10 | 10 불변 | v3.8 |
| opdw | §4 CLOSE / 행 9 | 9 불변 | v2.9 |
| opwt | CLOSE / 행 10 | 10 불변 | v4.3 |
| oppd | "DONE.md 작성" / Phase형 | rows 불변 | v4.6 |
| opsdd | Phase 6 CLOSE / 행 24 | 24 불변 | v3.5.0 |
| opgc | STEP 4 CLOSE / 행 7 | 7 불변 | v1.6 |

> `[MUST] tasks/016/TASK.md §제약: "STATE 행 불변 — pilot CLOSE 훅 확산 시 각 pilot rows_count 회귀 금지(014 정합). 015 opp 9행 유지 검증 패턴 준용."`
> 훅 본문: "DONE.md 생성 직후 → `.opal/brain/` 존재 시 op-brain-ingest 디스패치(부재 시 no-op) → 완료 보고." op-brain-ingest 탐색 경로 2단(프로젝트→글로벌) 동일.

#### U-16. .gitignore (M-5)

`.opal/` 무시는 유지하되 brain만 예외:
```
.opal/
!.opal/brain/
!.opal/brain/**
```
(→ M-5)

---

## 3. 실행 체크리스트

> 총 18개 Step | Phase 6개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SCHEMA 타입 SSOT (brain-tool이 의존) |
> | 2 | 2 | 순차 | brain-tool 동적화 (SCHEMA 의존) |
> | 3 | 3 | 순차 | brain-tool 테스트 (코드 의존) |
> | 4 | 4, 5, 6, 7 | 병렬 | 독립 스킬/문서 (brain-tool 계약 확정 후) |
> | 5 | 8, 9, 10, 11, 12, 13, 14 | 병렬 | 7 pilot 독립 파일 |
> | 6 | 15, 16, 17, 18 | 병렬→순차 | gitignore/install/설계 + dogfooding(EXECUTE 후) |

### Step 1: SCHEMA 타입 SSOT + 3계층 명문화
- [x] 완료
- **파일**: `opal/tools/brain-tool/templates/schema-template.md`
- **작업 내용**: §1.5 "페이지 타입 정의" 구조화 테이블(type·category·설명) 추가 — brain-tool 동적 로드 SSOT. 3계층 기억(MEMORY/brain/tasks) 절 추가. `sources:[task:NNN]` drill-down 형식 명시. 변경이력 행 추가
- **완료 기준**: §1.5 테이블이 기본 4종을 담되 "init이 채택/제외/추가/교체" 명문화. 3계층 절 존재. CONVENTIONS §변경이력 준수
- **테스트**: 마크다운 테이블 파싱 가능 형식 확인 (Step 3에서 brain-tool 파싱 검증)
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: brain-tool 타입 동적 로드 + analyze/ingest-scan
- [x] 완료
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: (a) `PAGE_TYPES`→`DEFAULT_PAGE_TYPES`, `load_page_types(brain_root)` 신설(SCHEMA §1.5 파싱, 부재 시 폴백) (b) `TYPE_TO_CATEGORY`/`CATEGORY_ORDER`/`BRAIN_DIRS` 동적 파생 (c) `--type` 검증 argparse choices→명령 함수 내부 이동 (d) `cmd_analyze`(code-scan 정량 집계) (e) `cmd_ingest_scan`(`--source docs|skills|tasks|all` 멱등 목록) (f) init `--types` 옵션. @header 갱신
- **완료 기준**: `validate`/`add-page`/`index`/`search`가 SCHEMA 타입을 동적 인식. argparse에 `choices=` 없이 `invalid_page_type` 검증 유지. `analyze`·`ingest-scan` JSON 반환
- **테스트**: Step 3 단위테스트. `bash opal/tools/brain-tool/run.sh analyze` happy-path
- **의존**: Step 1
- **agent**: opal-task-agent

### Step 3: brain-tool 테스트 갱신 (66 회귀 + 신규)
- [x] 완료
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: 동적 타입 테스트(커스텀 타입 선언·SCHEMA 부재 폴백·`--type` 무효값) + `analyze`/`ingest-scan` happy-path 추가. 기존 66 테스트 통과 유지
- **완료 기준**: `pytest`(또는 `python -m unittest`) 전체 통과 — 기존 66 + 신규 전부 green. mock 금지 규칙 준수
- **테스트**: `cd opal/tools/brain-tool && python -m pytest tests/ -v` (또는 `python -m unittest`)
- **의존**: Step 2
- **agent**: opal-task-agent

### Step 4: opal-brain 스킬 4모드 지능화
- [x] 완료
- **파일**: `opal/skills/opal-brain/SKILL.md`
- **작업 내용**: init STEP 0(analyze→타입 제안→확인→`init --types`), ingest --all 문서 범위(M-2 깊이), ingest task:NNN + 백필(M-3), query 후보→선택→주입(W5). 변경이력 행
- **완료 기준**: W1·W2·W3·W5 AC가 SKILL 절차로 명문화. [MUST] 단방향·index 비상주 인용 유지
- **테스트**: PM Gate 문서 검토 (요구사항→절차 매핑)
- **의존**: Step 3 (brain-tool 계약 확정)
- **agent**: opal-task-agent

### Step 5: op-brain-ingest 백필 정합
- [x] 완료
- **파일**: `opal/skills/op-brain-ingest/SKILL.md`
- **작업 내용**: 백필 기준이 본 워커 포함/제외 기준과 동일(재사용)임을 명시. 동적 타입(SCHEMA 로드) 정합 1줄. 변경이력 행
- **완료 기준**: 백필↔CLOSE ingest 기준 단일 SSOT 확인
- **테스트**: 문서 검토
- **의존**: Step 3
- **agent**: opal-task-agent

### Step 6: PM AGENT.md — W5 정정 + W4 PM 판단 ingest
- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: Lazy 트리거 `.opal/brain/index.md` 행을 "존재 여부 경량 인지(전체 자동 로드 안 함)"로 정정(W5). "opal-brain 활용 규칙"에 PM 판단 ingest 트리거(모드 연동) 추가(W4). 변경이력 행
- **완료 기준**: 부트스트랩에 index 전체 로드 없음. PM 판단 ingest 모드별 동작 명시
- **테스트**: 문서 검토 — W4·W5 AC 충족
- **의존**: Step 3
- **agent**: opal-task-agent

### Step 7: dispatch-process.md — search 3시점
- [x] 완료
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**: Step 1.5를 search 3시점 + 후보 목록→score 선별→불확실 시 사용자 확인→선택 페이지만 주입으로 확장. 변경이력 행
- **완료 기준**: 3시점 + 선택적 주입 흐름 명문화
- **테스트**: 문서 검토
- **의존**: Step 3
- **agent**: opal-task-agent

### Step 8~14: 7 pilot CLOSE brain ingest 훅 확산
- [x] 완료 (Step 8=opd, 9=opds, 10=opdw, 11=opwt, 12=oppd, 13=opsdd, 14=opgc — rows_count 불변: 15/10/9/10/Phase3행/24/7)
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md` / `-dev-short/` / `-dev-wireframe/` / `-write-tech/` / `-project-dev/` / `-sdd/` / `-gc/` SKILL.md
- **작업 내용**: 각 pilot 종료 단계(§2 U-8~U-14 표의 DONE 행)에 opp 동형 brain ingest 훅 삽입 — "DONE.md 생성 직후 → brain 존재 시 op-brain-ingest 디스패치(부재 시 no-op) → 완료 보고". 변경이력 행(각 다음 버전)
- **완료 기준**: 각 pilot에 훅 존재 + **STATE rows_count 불변**(opd 15·opds 10·opdw 9·opwt 10·oppd 불변·opsdd 24·opgc 7)
- **테스트**: 각 pilot STATE 행 테이블 rows_count 회귀 검증 (014 정합 패턴)
- **의존**: Step 5 (op-brain-ingest 정합 후)
- **agent**: opal-task-agent

### Step 15: .gitignore brain 예외 (M-5)
- [x] 완료
- **파일**: `.gitignore`
- **작업 내용**: `!.opal/brain/` + `!.opal/brain/**` 예외 추가. `code-scan.json`은 계속 무시
- **완료 기준**: `git check-ignore .opal/brain/index.md` 비매칭, `git check-ignore .opal/code-scan.json` 매칭
- **테스트**: `git check-ignore` 검증
- **의존**: 없음
- **agent**: opal-task-agent

### Step 16: install 배포 검증
- [x] 완료
- **파일**: `scripts/install-mac.sh` (+ `install.ps1` 존재 시 확인)
- **작업 내용**: brain-tool chmod(기존 958-963줄) 유효 확인. brain-tool이 의존하는 `~/.opal/tools/date/date.js` 배포 경로 확인. 누락 시에만 수정. 변경 시 변경이력 행
- **완료 기준**: install 후 `~/.opal/tools/brain-tool/run.sh` 실행 가능 + `//opbr` 레지스트리 매칭. 코드 변경 없으면 "검증 완료"로 기록
- **테스트**: `bash scripts/install-mac.sh`(메뉴 1) 후 `~/.opal/tools/brain-tool/run.sh validate --brain-path .opal/brain`
- **의존**: Step 2, 3, 4 (배포 대상 확정 후)
- **agent**: opal-task-agent

### Step 17: 설계 SSOT 갱신 (docs/)
- [x] 완료
- **파일**: `docs/proposals/opal-brain-design.md`
- **작업 내용**: 016 지능화 반영 — init 동적 분석·ingest --all 문서·3계층·index 비상주 정정(§9)·이름 결정(M-4)·git 정책(M-5). §12 R4(소급)·R6(배치)를 016 확정으로 갱신
- **완료 기준**: 설계 SSOT가 016 구현과 정합. 코드/문서 불일치 0
- **테스트**: 문서 검토
- **의존**: Step 4, 6, 7
- **agent**: opal-task-agent (docs/ 갱신 — PM Gate에서 docs 무효화 체크로 재검증)

### Step 18: 현 프로젝트 brain dogfooding
- [x] 완료 (49페이지: docs 5 + skills 32 + 백필 9 + 기존 3. validate valid / lint 0 — orphan 35건은 링크 패스 재지시 1회로 해소)
- **파일**: `.opal/brain/`
- **작업 내용**: 016 코드 완료 후 `//opbr ingest --all`(docs·스킬·참조) + 001~015 선별 백필 실행. validate/lint clean 확인
- **완료 기준**: brain 페이지 증가(시드 3 → docs/스킬 요약 + 백필 concept). `validate` valid / `lint` 0
- **테스트**: `brain-tool validate` + `brain-tool lint`
- **의존**: Step 16 (install 후)
- **agent**: opal-task-agent

---

## 4. QA 체크리스트

### 기능 테스트
- [x] W1 — `//opbr init`이 origin 분석(analyze)으로 타입 세트·도메인·시드 대상 제안, 사용자 확인 후 SCHEMA에 타입 확정, brain-tool이 그 타입으로 검증·디렉토리 구성 (SKILL init STEP 0 명문화 + analyze 배포본 동작 증거)
- [x] W1 — brain-tool이 SCHEMA §1.5에서 타입 동적 로드(하드코딩 없음), 커스텀 타입 인식 (TestDynamicPageTypes 6케이스 green)
- [x] W2 — `//opbr ingest --all`이 docs·스킬·참조를 요약 페이지로 적재, 각 페이지가 origin 경로 참조(본문 복제 없음) (dogfooding 실증 — docs 5 + skills 32 페이지)
- [x] W3 — `//opbr ingest task:NNN` 동작 + 선별 백필 후 search로 과거 결정 검색·drill-down (백필 9건 + search "codex" → 2후보 + task:009 링크 실재)
- [x] W4 — PM 규칙에 ingest 판단 트리거 + 모드별 동작(agentic 자율 / 그 외 제안) 명시 (AGENT.md v3.2)
- [x] W5 — search가 본문 아닌 후보 목록 반환, 선택 페이지만 주입, 부트스트랩에 index 전체 로드 없음 (search 출력에 본문 키 부재 실증 + AGENT.md Lazy 행 정정)
- [x] W6 — 7 pilot CLOSE에 ingest 훅 삽입 + 각 pilot rows_count 불변 (15/10/9/10/Phase3행/24/7 전건 증거)
- [x] W7 — install 후 brain-tool·스킬 배포 + `//opbr` 매칭 + git 추적 여부 확정·반영 (배포 4종 동작 증거 + check-ignore 증거)

### 일관성 테스트
- [x] brain-tool 기존 66 테스트 통과(회귀 0) + 신규 테스트 green (PM 독립 재실행: 83 passed)
- [x] STATE 행 불변 — 7 pilot rows_count 회귀 없음 (014 정합)
- [x] 단방향 동기화 — wiki→origin 역수정 없음 (전 워커 changed_files에 origin 문서 부재 확인)
- [x] index 비상주 — 3 PM 문서(AGENT.md·dispatch-process.md·SKILL.md) 일관 (전량 자동 로드 금지)
- [x] 이름 일관성 — 구현 식별자 `opal-brain`/`opbr`/`brain-tool` 유지(M-4), "opal-wiki-pilot"은 비전 용어로만 (설계 SSOT §13 명문화)
- [x] 변경이력 — 수정 스킬·에이전트·참조 문서 전부 행 추가(KST + 016)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명
- [x] kebab-case 파일/폴더 (Python snake_case)
- [x] YAML frontmatter 유효 (페이지·스킬) (brain-tool validate violations 0)
- [x] SCHEMA §1.5 테이블이 brain-tool 파싱 가능 형식 (load_page_types 테스트 green)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | argparse `choices=PAGE_TYPES` 제거 시 CLI UX 저하(자동 검증 손실) | `--type` 오타가 런타임에야 검출 | 명령 함수 내 `invalid_page_type` 검증 즉시 수행 + 에러 메시지에 동적 타입 목록 노출 |
| R-2 | SCHEMA §1.5 파싱 실패 시 brain 동작 불능 | brain-tool 전 명령 마비 | `load_page_types` 부재/실패 시 `DEFAULT_PAGE_TYPES` graceful 폴백 (Step 3 테스트로 보장) |
| R-3 | 기존 66 테스트의 `BT.PAGE_TYPES` 참조 깨짐 | 회귀 | `PAGE_TYPES` 동명 또는 `DEFAULT_PAGE_TYPES` alias 보존 |
| R-4 | 7 pilot 훅 삽입 중 STATE 행 실수 추가 | rows_count 회귀(014 위반) | 훅을 기존 "DONE.md 생성" 행 **내부 동작**으로 삽입(행 미추가). Step 8~14 완료 기준에 rows_count 검증 명시 |
| R-5 | ingest --all 문서 요약이 본문 복제로 흐름 | "복사 아닌 요약+참조" 위반 | M-2 깊이(3~6줄 요약+포인터) 명문화 + lint unsourced 검출 |
| R-6 | git brain 추적 후 멀티PC ingest index 충돌 | merge conflict | 설계 §R2 — brain-tool 원자적 index 재생성(전체 스캔 후 1회 write) + git merge는 사용자 책임 (016은 추적 전환만, merge 전략은 후속) |
| R-7 | init analyze가 `.opal/code-scan.json` 부재 프로젝트에서 무력 | 타입 제안 빈약 | code-scan 부재 시 docs/ 폴더 구조·파일명 기반 폴백 제안 + 사용자 확인으로 보완 (기존 init 전제 확인 절차 계승) |
| R-8 | 이름 결정(M-4 A안)이 캡틴 "wiki" 비전과 표면 불일치 | 용어 혼선 | 설계 SSOT(U-17)에 "opal-wiki-pilot=비전명 / opal-brain=구현명" 매핑 명문화 |

---

> **decision_required**: 없음 (이월 5항목은 §0에서 권고안 확정 — agentic 모드. 단 M-4 이름·M-5 git 정책은 표면 비전과 연관되므로 PM Gate에서 캡틴 최종 확인 권고).

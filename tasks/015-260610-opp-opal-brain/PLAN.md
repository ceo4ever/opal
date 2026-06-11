# PLAN: OPAL Project Brain — 프로젝트 지식 위키 시스템 신설

> 작성일: 2026-06-10
> 입력: `tasks/015-260610-opp-opal-brain/TASK.md`
> 출력: `tasks/015-260610-opp-opal-brain/PLAN.md`
> 트랙: 개발 트랙 (프레임워크 자산 — 도구·스킬·참조 문서·install)

---

## 0. 작업 성격 선언

본 태스크의 산출물은 **코드 앱이 아니라 OPAL 프레임워크 자산**이다. 영역은 `docs/PROJECT.md` §프로젝트 구성의 단일 요소 **Framework**(`opal/`, `skills/`, `agents/` — Markdown/YAML/Bash/Node.js, 전문 에이전트 `opal-task-agent`)에 귀속한다 (→ D-7 §프로젝트 구성). 따라서 §3 실행 체크리스트의 EXECUTE Step은 대부분 `opal-task-agent`로 배정하고, 동작 검증이 필요한 도구 구현(R1)에는 TEST Step을 별도 배치한다.

> **[MUST] PLAN 단계 출력 제약** — `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다." 본 PLAN은 설계 문서(.md)만 작성하며 어떤 코드/스킬/도구 파일도 생성하지 않는다 (→ D-8 §Guards).

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-brain 설계 제안서 | `docs/proposals/opal-brain-design.md` | 본 태스크 설계 SSOT (13절 전체) |
| D-2 | 외부 | Karpathy llm-wiki | [llm-wiki gist](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md) | 위키 사상 원전 |
| D-3 | 설계 | OPAL 하네스 (SSOT) | `opal/core/references/opal-harness.md` | Guards/State/도구 패턴 (§1·§3·§9) |
| D-4 | 설계 | PM 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | R4 brain 조회 단계 삽입 위치 |
| D-5 | 설계 | code-scan 관리 | `opal/core/references/pm/code-scan-management.md` | R4 "PM 우선 활용" 동형 기준 |
| D-6 | 소스 | state-tool 래퍼 | `opal/tools/state-tool/run.sh` | R1 run.sh 래퍼 + venv python 패턴 |
| D-6b | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | R1 서브커맨드/에러코드/KST date.js 호출 패턴 |
| D-6c | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | R4 @header 시드 데이터 출처(code-scan.json) 구조 |
| D-7 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 폴더 구조·네이밍·배포 경계·영역 |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | @header·변경이력·도구/배포/플랫폼분기 규칙 |
| D-9 | 소스 | install-mac.sh | `scripts/install-mac.sh` | R7 스킬·도구·레지스트리 동기화 지점 |
| D-10 | 소스 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | R3 레지스트리 등록 형식 |
| D-11 | 소스 | ~/.opal/AGENT.md | `opal/core/AGENT.md` (배포본 `~/.opal/AGENT.md`) | R4 Lazy 트리거 테이블 + code-scan 활용 규칙 동형 |
| D-12 | 소스 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | R5 CLOSE 단계 구조 + STATE 행 구성 |
| D-13 | 소스 | web-to-markdown 스킬 | `opal/skills/web-to-markdown/SKILL.md` | R6 외부 소스 변환 연동(wtm) |

> 본 PLAN의 모든 설계 결정은 위 문서 근거를 인용한다. `[MUST]` 토큰은 재해석 금지 (→ citation-rules.md §2.4).

### 핵심 [MUST] 제약 (원문 인용)

- `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." — 모든 R 산출물은 `opal/`·`scripts/` 소스에만 생성하고 install로 배포한다 (→ D-8).
- `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 State 관리: "STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." — brain-tool은 동일 철학(index·log는 도구가 집행, LLM 직접 편집 금지)으로 설계한다 (→ D-8 / D-1 §7.2).
- `[MUST]` `docs/CONVENTIONS.md` §언어 규칙: "문서 본문=한국어 / 코드·변수·필드명=English / YAML frontmatter 키=English / 파일·폴더=English kebab-case (Python 파일은 snake_case)." — brain 페이지·SCHEMA·도구 산출물 전부 적용 (→ D-8).
- `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다. 플랫폼별 차이는 어댑터 계층(install)에서만 흡수한다." — brain 구조·SCHEMA는 마크다운 네이티브, 플랫폼 분기는 install 3종에만 (→ D-8 / TASK §제약).
- `[MUST]` `docs/CONVENTIONS.md` §변경이력: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시 `YYYY-MM-DD HH:mm`(KST), 버전 semver, 변경내용에 태스크 번호 괄호 포함." — 수정 대상 전 문서에 `(015)` 변경이력 행 추가 (→ D-8).
- `[MUST]` `opal/core/references/opal-harness.md` §9 도구 호출 방식: "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다. 출력은 JSON이며, `\"ok\": false`이면 `\"error\"` 필드를 확인하여 에스컬레이션한다." — brain-tool 인터페이스 표준 (→ D-3).
- `[MUST]` 단방향 동기화 — `docs/proposals/opal-brain-design.md` §8.3: "@header를 entity 페이지 시드로 흡수 + `file_path:line` 참조. 코드 본문 복제 금지 … 코드가 SSOT(단방향 동기화)." brain→코드 역방향 갱신 금지 (→ D-1 §5.1.1 / §8.3).

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/run.sh` | venv python 래퍼 패턴 (R1 복제 원본) | 참조만 | `opal/tools/state-tool/run.sh:1-12` |
| `opal/tools/state-tool/state_tool.py` | 서브커맨드/argparse/JSON out/ERROR_CODES/KST date.js 호출 | 참조만 | `state_tool.py:14-22, 67-90, 140-148` |
| `opal/tools/code-scan/code-scan.js` | @header 스캐너 — `.opal/code-scan.json` 소비, JSON 출력 | 참조만 | `code-scan.js:29-34, 68-74` |
| `opal/tools/requirements.txt` | venv 의존성 (PyYAML 6.0.0 포함) | 변경 없음 | `requirements.txt:23` |
| `opal/tools/date/date.js` | KST 타임스탬프 도구 (`datetime` 서브명령) | 참조만 | - |
| `scripts/install-mac.sh` | 도구·스킬·레지스트리 동기화 | **수정** | `install-mac.sh:888-899(skills), 939-956(tools), 998-999(refs)` |
| `scripts/install/linux.sh` | linux 어댑터 진입점 | 검토 (위임 구조 확인) | `scripts/install/linux.sh` |
| `scripts/install.ps1` / `scripts/install/windows.ps1` | windows 어댑터 | **수정** | `scripts/install/windows.ps1` |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 SSOT | **수정**(opal-brain·op-brain-ingest 행 추가) | `opal-skills-registry.json:486-603(opal 그룹)` |
| `opal/core/AGENT.md` | 부트스트랩 Lazy 트리거 + code-scan 활용 규칙 | **수정**(R4) | `~/.opal/AGENT.md:27-43(Lazy), 175-188(code-scan 규칙)` |
| `opal/core/references/pm/dispatch-process.md` | PM 디스패치 5단계 | **수정**(R4 Step 1.5 신설) | `dispatch-process.md:29-66, 103-110` |
| `opal/skills/opal-pilot-project/SKILL.md` | opp CLOSE 단계 + STATE 행 | **수정**(R5 pilot) | `opal-pilot-project/SKILL.md:118-167` |
| 그 외 pilot 7종 SKILL.md | CLOSE 훅 적용 대상 | **수정**(R5, 범위 §2 결정 6) | `opal/skills/opal-pilot-*/SKILL.md` |
| `.opal/code-scan.json` | code-scan 설정 (현재 **부재**) | **신규**(R7 init 전제) | `find` 결과 0건 — 부재 확인 |

### 현재 상태

1. **도구 패턴 (R1·D2)** — `state-tool`은 `run.sh`(8줄 래퍼)가 `$HOME/.opal/.venv/bin/python`으로 `state_tool.py`를 exec한다 (→ `run.sh:1-12`). `state_tool.py`는 ① stdlib + 표준 import만, ② `argparse` 서브커맨드, ③ `ERROR_CODES` 상수 카탈로그(23종)로 모든 error를 표준화, ④ `get_kst_datetime()`이 `node ~/.opal/tools/date/date.js datetime`을 subprocess로 호출해 KST 시각을 얻는다 (→ `state_tool.py:67-90, 140-148`). `code-scan`은 Node.js(`code-scan.js`) 단일 파일이고 `.opal/code-scan.json`을 읽어 @header를 JSON으로 출력한다 (→ `code-scan.js:29-34`).

2. **install 동기화 (R7·D8)** — `install-mac.sh`는 (a) `opal/skills/*/` 디렉토리를 **루프로 자동 복사**(`install_dir`)하고 strip 처리한다 (→ `install-mac.sh:888-899`), (b) `opal/tools/`를 통째로 `install_dir`로 복사한 뒤 **도구별 `run.sh`에 개별 `chmod +x`** 를 건다(playwright/state/cmux — `install-mac.sh:944-963`), (c) venv는 `requirements.txt`로 설치(→ `:1072-1094`), (d) 레지스트리는 `install_opal_references`로 복사(→ `:998-999`). **결론: 스킬·도구·레지스트리는 디렉토리 단위 자동 동기화이므로 새 자산은 코드 추가 없이 복사된다. 유일한 명시 수정은 `brain-tool/run.sh`의 `chmod +x` 한 줄(state-tool 패턴 복제, `:951-956`).** windows.ps1은 별도 복사 로직이 있어 대칭 검토 필요.

3. **PM 융합 지점 (R4·D11/D4/D5)** — `~/.opal/AGENT.md` Lazy 트리거 테이블(→ `:27-43`)과 "code-scan 활용 규칙" 테이블(→ `:175-188`)이 R4가 동형으로 따라야 할 원본이다. `dispatch-process.md`는 Step 0~7 구조이며 brain 조회는 "code-scan 사전 범위 파악"(→ `:103-110`) 직전/직후에 동형 삽입한다.

4. **CLOSE·STATE 구조 (R5·D12)** — opp의 CLOSE(STEP 4)는 "① DONE.md 생성 후 행 9 mark → ② 완료 보고"의 2스텝이다 (→ `opal-pilot-project/SKILL.md:118-127`). STATE 표준 행은 9행(TASK 2 / PLAN 3 / EXECUTE 3 / CLOSE 1)이며 `init --rows-from <SKILL.md>`로 자동 추출된다 (→ `:152-167`). ingest 훅은 DONE.md 생성 직후·완료 보고 직전에 삽입된다.

5. **외부 소스 (R6·D13)** — `web-to-markdown`(alias `wtm`) 스킬과 `xlsx-tool`이 이미 존재해 외부 소스→md 변환에 재사용 가능하다 (→ D-1 §8.3).

6. **code-scan.json 부재 (R7 전제)** — 현 opal 프로젝트에 `.opal/code-scan.json`이 **없다**(find 0건). `//opbr init`이 @header 시드를 하려면 code-scan.json이 필요하므로, R7 시드 적용 전에 PM이 code-scan.json을 생성해야 한다 (→ D-5 §생성 시점 "PM이 직접 생성"). §5 리스크 등재.

### 영향 범위

- **신규 자산**: `opal/tools/brain-tool/`(도구), `opal/skills/opal-brain/`(pilot 스킬), `opal/skills/op-brain-ingest/`(CLOSE 훅 워커). 기존 동작에 회귀 영향 없음(추가형).
- **수정 자산**: AGENT.md·dispatch-process.md(부가 단계, 폴백 안전 — brain 부재 시 자연 스킵), pilot SKILL.md(CLOSE 훅·STATE 행), 레지스트리(행 추가), install 3종(chmod·복사 대칭). pilot STATE 행 변경 시 state-tool `--rows-from` 파싱 정합 필수(회귀 주의 → §5).
- **docs/ 영향**: `docs/PROJECT.md` 프로젝트 문서 테이블에 brain 관련 항목 추가 가능성, `docs/CONVENTIONS.md`에 brain SCHEMA 규약 링크 가능성 → docs/ 갱신 Step(§3 Step 12, agent: PM 직접)으로 처리.

---

## 2. 구현 계획

### 2.0 PLAN 확정 의사결정 (TASK 이월 8건)

#### 결정 1 — Phase 분해 (제안서 §11 재검토)

제안서 P1~P6을 의존성 기준으로 재배열한다. **하위 레이어(도구·표준) → 스킬 → 융합 → 배포** 순.

| Phase | 포함 R | 산출물 | 병렬/순차 | 의존 |
|-------|--------|--------|----------|------|
| **P1 코어** | R1, R2 | brain-tool + SCHEMA 표준/템플릿 | R2(표준)→R1(구현) 일부 순차, 그 외 병렬 | 없음 |
| **P2 스킬** | R3 | opal-brain SKILL.md + 레지스트리 행 | 순차 | P1(brain-tool 인터페이스 확정 필요) |
| **P3 PM 융합** | R4 | AGENT.md·dispatch·프로젝트 AGENT 규칙 | 3문서 병렬 | P1(brain-tool search 존재) |
| **P4 CLOSE 융합** | R5 | op-brain-ingest 워커 + pilot CLOSE 훅 + STATE 행 | 워커→pilot 순차 | P1·P2 |
| **P5 외부 소스** | R6 | opal-brain ingest 모드 sources/ 로직 | 순차 | P2 |
| **P6 배포·시드** | R7 | install 3종 + code-scan.json + `//opbr init` 시드 | install→시드 순차 | P1~P5 전부 |

> P3·P5는 P2 이후 서로 독립이라 병렬 가능. P4는 P2(ingest 모드)·op-brain-ingest 워커에 의존. P6은 최후 통합·검증.

#### 결정 2 — brain-tool 구현 언어: **Python** (택1)

| 후보 | 정합 대상 | 채택 근거 | 비채택 사유 |
|------|----------|----------|------------|
| **Python ✅** | state-tool | ① brain-tool의 본질이 state-tool과 동일(.md/index/log 결정론적 집행, run.sh+venv python 패턴 그대로 복제 → `run.sh:1-12`) ② frontmatter 파싱에 **PyYAML이 이미 venv에 존재**(추가 의존성 0, → `requirements.txt:23`) ③ KST 타임스탬프를 `date.js` subprocess로 재사용(state-tool과 동일 → `state_tool.py:140-148`) ④ ERROR_CODES 카탈로그 패턴 그대로 이식 | — |
| Node.js | code-scan | code-scan과 정합되나, code-scan은 brain의 **데이터 입력원**일 뿐(JSON 소비) 언어 결합 불요. Node는 YAML 파서 추가 의존 필요(npm). venv 외 별도 런타임 관리 부담 | 의존성·정합성 모두 열위 |

> **결론: Python.** `code-scan.json`은 Python에서 `json` stdlib로 읽으므로 언어 결합이 발생하지 않는다 (→ D-1 §5.1.1 @header 시드는 데이터 흐름이지 런타임 결합이 아님).

#### 결정 3 — brain-tool 서브커맨드 인터페이스 (8종)

모든 커맨드: 출력 `{"ok": bool, "command": str, ...}` (state-tool 동형), 실패 시 `{"ok": false, "error": "<code>", "detail": ...}`. 에러는 `ERROR_CODES` 카탈로그 상수 키만 사용(임의 변형 금지, → `state_tool.py:67` 패턴).

| 커맨드 | 인자 | 출력(성공) | 주요 에러 코드 |
|--------|------|-----------|---------------|
| `init <brain-path>` | `[--force]` | `{ok, command:"init", created:[dirs], schema_written:true}` | `brain_already_initialized`(force로만 재초기화 → D-1 §6.0), `brain_path_invalid` |
| `add-page <path>` | `--type <entity\|concept\|flow\|synthesis> --title <..> [--tags ..] [--sources ..]` | `{ok, page:<path>, indexed:true}` | `invalid_page_type`, `frontmatter_invalid`, `duplicate_page` |
| `index` | `[--brain-path .]` | `{ok, pages_scanned:N, index_written:true, categories:{..}}` | `brain_not_initialized`, `index_write_failed` |
| `log <op> <summary>` | `--op <ingest\|init\|lint\|query> --summary <..> [--new ..] [--updated ..] [--sources ..]` | `{ok, logged:true, timestamp:"<KST>"}` | `date_tool_failed`(KST), `log_append_failed` |
| `search <query>` | `[--type T] [--tag X] [--limit N]` | `{ok, matches:[{page, title, type, score, snippet}]}` | `brain_not_initialized`, `query_empty` |
| `sync-header` | `[--scope X] [--page P]` | `{ok, synced:[..], drift:[{page, field, old, new}], stale_marked:[..]}` | `code_scan_json_missing`, `header_parse_failed` |
| `lint` | `[--brain-path .]` | `{ok, issues:[{kind, page, detail}]}` (kind∈{orphan,stale,broken_link,missing_link,unsourced,contradiction}) | `brain_not_initialized` |
| `validate` | `[--brain-path .]` | `{ok, valid:bool, violations:[{page, rule, detail}]}` | `brain_not_initialized` |

> 집행 경계: `index`·`log`·`add-page`의 인덱싱은 **도구만** 수행, 페이지 본문은 LLM 작성(→ D-1 §7.2). `sync-header`는 단방향(코드 @header→brain frontmatter)만, 역방향 금지([MUST] 단방향 동기화).

#### 결정 4 — init 핵심 엔티티 선별 임계값 (제안서 §6.1.1 "선별 기준" 정량화)

init은 전체 미러가 아니라 3계층 차등 등록(→ D-1 §6.1.1). **선별 기준(정량 OR 정성)**:

| 기준 | 임계값 | 근거 |
|------|--------|------|
| (정량) exports 수 | code-scan @header `exports` ≥ 3 | 인터페이스 면적이 큰 모듈 = 지식 가치 高 |
| (정량) 피의존도 | `code-scan depends <module>` 역참조 ≥ 2 | 다른 모듈이 의존하는 허브 |
| (정성) 레이어 | `layer` ∈ {orchestrator, tool, pilot, core} | 오케스트레이터·도구는 무조건 시드 |
| (정성) 도메인 대표 | 각 `domain`당 최소 1개(대표 엔티티) | 도메인 조망 보장 |

- **판정 로직**: 위 4기준 중 **하나라도** 충족 → entity 페이지 시드(얕은 골격). 모두 미충족 → index.md 카탈로그에만 등록(페이지 미생성, lazy → D-1 §6.1.1 "나머지").
- `--full`은 임계값 무시 전체 @header 시드(얕음), `--ingest-all`은 임계값 무시 전체 분석 ingest(깊음, 비용 큼).
- 임계값은 brain-tool 상수(`SEED_THRESHOLDS`)로 노출하여 프로젝트별 조정 가능.

#### 결정 5 — `ingest --all` 배치 정책 (제안서 R6 완화)

| 항목 | 정책 | 근거 |
|------|------|------|
| 병렬 배치 크기 | 1배치 = **5 자산**(엔티티/파일 단위), 하네스 §7 병렬 한도 준수 | 토큰·동시성 제어 (→ D-3 §7) |
| 멱등 skip 판정 키 | `(source_ref, header_synced)` 쌍 — 페이지 frontmatter의 `header_synced`가 code-scan @header의 최신 스캔 시각과 같으면 skip | 재실행 안전 (→ D-1 §5.1.1) |
| 진행률 보고 | `ingest --all`이 배치별 `{done:N, total:M, skipped:K}` 누적 출력 | 관측성 |
| 재개 메커니즘 | log.md에 배치 완료 마커 append → 중단 후 재실행 시 멱등 skip이 자동 재개 역할 | append-only log 활용 (→ D-1 §5.5) |
| 동시 ingest 충돌 | brain-tool `index`/`log`를 **단일 도구 호출로 원자화**(LLM은 페이지만 작성, 인덱싱은 마지막에 1회 `index`) | 제안서 R2 멀티에이전트 충돌 완화 (→ D-1 §12 R2) |

#### 결정 6 — CLOSE 자동 ingest 적용 pilot 범위: **단계적(pilot 파일럿 후 확산)**

| 항목 | 결정 | 근거 |
|------|------|------|
| 적용 방식 | **단계적** — 015에서는 **opp(opal-pilot-project) 단독**에 ingest 훅 적용(파일럿). 나머지 7 pilot(opd/opds/opdw/opwt/oppd/opsdd/opgc)은 **후속 태스크로 확산** | noise 누적 리스크(→ D-1 §12 R1) + STATE 행 회귀 리스크 최소화. 태스크 014가 STATE 행을 pilot별로 막 재구성한 직후이므로 일괄 변경은 회귀 위험 高 |
| 구현 방식 | **`op-brain-ingest` 경량 워커로 분리** (pilot SKILL에 직접 인라인 금지) | 8 pilot 확산 시 중복 제거 + 단일 SSOT. CLOSE에서 워커 1회 디스패치(→ D-1 §8.2) |
| STATE 행 추가 여부 | **추가하지 않음** — ingest는 CLOSE 행(DONE.md 생성) 내부의 부수 작업으로 흡수. 별도 행 추가 시 014 정합 9행 구조가 깨짐 | `init --rows-from` 파싱 영향 0 (→ D-12 `:152-167`) |
| 적용 위치 | opp CLOSE STEP 4: ①DONE.md 생성 → **①.5 op-brain-ingest 디스패치(brain 존재 시에만, 미존재 시 자연 스킵)** → ②완료 보고 | brain 부재 프로젝트 안전 (→ D-12 `:118-127`) |
| 게이트 | PM Gate 통과 후 실행 — 검증된 산출물만 누적 | 헌법 §4 정합 (→ D-1 §8.2) |

#### 결정 7 — SCHEMA frontmatter·링크 표준 최종 확정 (제안서 §5 기반)

`SCHEMA.md`(init 시 생성)가 정의하는 표준을 brain-tool `validate`/`add-page`가 집행한다.

- **frontmatter 필수 키**: `type`(enum 4종), `title`, `created`, `updated`, `status`(enum: active|stale|draft). **선택 키**: `tags[]`, `sources[]`, `related[]`.
- **entity 추가 키(@header 시드)**: `module`, `layer`, `domain`, `exports[]`, `source_ref`, `header_synced` (→ D-1 §5.1.1).
- **네이밍**: 파일 `kebab-case.md`, `pages/{type}/` 디렉토리 강제, 링크는 파일명 기준 `[[kebab-name]]` (→ D-1 §5.2 / [MUST] 언어 규칙).
- **링크 3종**: 교차참조 `[[page-file]]` / 코드참조 `` `file_path:line` `` / 외부소스 `[[source:source-id]]` (→ D-1 §5.3).
- **index.md / log.md 구조**: 제안서 §5.4/§5.5 그대로 — index는 카테고리(도메인/개념/엔티티/흐름/합성)별 카탈로그, log는 append-only `## [날짜] op | 요약` (→ D-1 §5.4-5.5).
- **저장 위치**: SCHEMA 템플릿은 `opal/tools/brain-tool/templates/schema-template.md`(도구가 init 시 복사). 스킬 references에 사람용 규약 요약 사본 둘 수 있음.

#### 결정 8 — install 동기화 지점 (D9 코드 확인 결과)

| install 파일 | 필요 수정 | 정확한 위치/함수 | 근거 |
|--------------|----------|-----------------|------|
| `scripts/install-mac.sh` | **brain-tool/run.sh `chmod +x` 한 줄 추가** (state-tool 블록 복제). 스킬·도구 디렉토리·레지스트리는 **자동 동기화(수정 불요)** | tools 처리 블록 `:951-956`(state-tool chmod 옆) | `install-mac.sh:888-899(skill loop), 939-956(tool loop+chmod), 998-999(refs)` |
| `scripts/install/windows.ps1` | brain-tool run.sh 대응(.ps1은 chmod 불요지만 도구 복사·실행권한 로직 대칭 확인 필요) | windows tools 복사 블록(검토 후 확정) | D-9 windows.ps1 |
| `scripts/install/linux.sh` | install-mac.sh 위임 구조면 수정 불요(검토 후 확정) | `scripts/install/linux.sh` | D-9 |

> **핵심 발견**: 기존 install은 `opal/skills/*/`·`opal/tools/`를 **디렉토리 단위 루프로 자동 복사**하므로 새 스킬(opal-brain, op-brain-ingest)·새 도구(brain-tool)는 코드 추가 없이 배포된다. **유일한 명시 수정은 brain-tool/run.sh chmod(+ windows/linux 대칭)** — install 수정 부담 최소.

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/tools/brain-tool/run.sh` | venv python 래퍼 (state-tool 복제) | D-6, 결정 2 |
| N-2 | `opal/tools/brain-tool/brain_tool.py` | 8 서브커맨드 구현 (argparse + ERROR_CODES + KST) | D-6b, 결정 3 |
| N-3 | `opal/tools/brain-tool/templates/schema-template.md` | init 시 복사되는 SCHEMA 표준 | D-1 §5, 결정 7 |
| N-4 | `opal/tools/brain-tool/templates/index-template.md` | 빈 index.md 골격 | D-1 §5.4 |
| N-5 | `opal/tools/brain-tool/templates/log-template.md` | 빈 log.md 골격 | D-1 §5.5 |
| N-6 | `opal/tools/brain-tool/templates/page-{type}.md` ×4 | entity/concept/flow/synthesis 페이지 템플릿 | D-1 §5.1 |
| N-7 | `opal/tools/brain-tool/README.md` | 도구 사용법 (state-tool README 동형) | D-6 README 패턴 |
| N-8 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 서브커맨드 단위 테스트 | `state-tool/tests/` 패턴 |
| N-9 | `opal/skills/opal-brain/SKILL.md` | 단일 pilot + 4모드(init/ingest/query/lint) | D-1 §6, R3 |
| N-10 | `opal/skills/opal-brain/references/brain-schema.md` | SCHEMA 규약 사람용 요약(선택) | 결정 7 |
| N-11 | `opal/skills/op-brain-ingest/SKILL.md` | CLOSE 훅 경량 워커 스킬 | D-1 §8.2, 결정 6 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/opal-skills-registry.json` | `opal` 그룹에 opal-brain(alias opbr, domain knowledge) + op-brain-ingest(dispatched_by 전 pilot) 행 추가 | D-10, R3 |
| M-2 | `opal/core/AGENT.md` | Lazy 트리거 테이블에 `.opal/brain/index.md` 행 + "opal-brain 활용 규칙" 테이블(code-scan 규칙 동형) | D-11, R4(a)(c) |
| M-3 | `opal/core/references/pm/dispatch-process.md` | "Step 1.5 brain 참조" 신설(brain-tool search → 워커 컨텍스트 주입) | D-4, R4(b) |
| M-4 | `opal/skills/opal-pilot-project/SKILL.md` | CLOSE STEP 4에 ①.5 op-brain-ingest 디스패치(brain 존재 시) 삽입 + 변경이력 | D-12, R5(결정 6) |
| M-5 | `scripts/install-mac.sh` | tools 블록에 brain-tool/run.sh chmod +x 추가 + 변경이력 | D-9, 결정 8 |
| M-6 | `scripts/install/windows.ps1` | brain-tool 복사·실행 대칭 반영 | D-9, 결정 8 |
| M-7 | `scripts/install/linux.sh` | (검토 결과 위임 구조 아니면) brain-tool 대칭 반영 | D-9, 결정 8 |
| M-8 | `opal/core/references/opal-harness.md` | §9 등록 도구 표에 brain-tool 행 추가 + 변경이력 | D-3 §9 |
| M-9 | `.opal/code-scan.json` | R7 init 전제 — 신규 생성(PM 직접, code-scan-management.md §생성 시점) | D-5, 리스크 R-1 |
| M-10 | `docs/PROJECT.md` / `docs/CONVENTIONS.md` | brain 관련 문서·규약 반영(필요 시) | docs/ 갱신 Step |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | 없음 | 전 작업이 추가형(회귀 영향 없음) |

### 구현 순서

| 순서 | 작업 | 파일 | 난이도 |
|------|------|------|--------|
| 1 | SCHEMA 표준·템플릿 확정 (R2) | N-3~N-6 | 중 |
| 2 | brain-tool 구현 (R1) | N-1,N-2,N-7 | 상 |
| 3 | brain-tool 테스트 (R1 검증) | N-8 | 중 |
| 4 | opal-brain 스킬 + 레지스트리 (R3) | N-9,N-10,M-1 | 중 |
| 5 | PM 융합 3문서 (R4) | M-2,M-3 | 중 |
| 6 | op-brain-ingest 워커 + opp CLOSE 훅 (R5) | N-11,M-4 | 중 |
| 7 | 외부 소스 파이프라인 (R6) | N-9(ingest 모드) | 중 |
| 8 | install 3종 + 하네스 도구표 (R7 배포) | M-5~M-8 | 중 |
| 9 | code-scan.json 생성 + `//opbr init` 시드 (R7 적용) | M-9 | 하 |

### 핵심 설계

**brain-tool (N-1·N-2)** — `run.sh`는 `state-tool/run.sh`를 그대로 복제하되 스크립트명만 `brain_tool.py`로 교체 (→ `opal/tools/state-tool/run.sh:1-12`). `brain_tool.py`는 stdlib + PyYAML(frontmatter)만 import하고, `ERROR_CODES` 상수 카탈로그 + `argparse` 서브커맨드 8종(결정 3) + `get_kst_datetime()`(date.js subprocess, → `state_tool.py:140-148`)을 둔다. `index`/`log`는 도구만 갱신([MUST] 집행 경계, → D-1 §7.2). `sync-header`는 `.opal/code-scan.json`을 `json` stdlib로 읽어 단방향 시드([MUST] 단방향 동기화, → D-1 §8.3).

**opal-brain SKILL (N-9)** — YAML frontmatter(name/description/triggers/version) + 4모드 라우팅(첫 인자=모드, 미지정 시 PM 의도 판별 → D-1 §6.2). init은 결정 4 임계값으로 핵심 엔티티 선별, ingest는 결정 5 배치 정책, query는 index→페이지→인용 합성(가치 답은 synthesis 페이지 파일링 제안), lint는 brain-tool lint 호출 (→ D-1 §6.1). 외부 소스는 wtm/xlsx-tool 재사용 + `sources/<id>/`에 raw.md+meta.yaml (→ D-1 §8.3, D-13).

**op-brain-ingest 워커 (N-11)** — CLOSE에서 디스패치되는 경량 워커. DONE.md·PLAN 의사결정(M-N)·신규 엔티티를 읽어 concept/entity 페이지 작성 → brain-tool add-page/index/log 호출. ingest 대상/제외 기준(아키텍처 결정·신규 컴포넌트 vs 오타·trivial)을 SKILL.md에 명시 (→ D-1 §8.2). **brain 미존재 시 즉시 no-op 반환**(안전).

**PM 융합 (M-2·M-3)** — AGENT.md "opal-brain 활용 규칙" 테이블은 "code-scan 활용 규칙"(→ `~/.opal/AGENT.md:175-188`)과 동일 포맷: `작업 시작·분석·설계 전 → brain-tool search <키워드>` / `과거 결정 맥락 필요 → //opbr ask`. dispatch-process Step 1.5는 "code-scan 사전 범위 파악"(→ `dispatch-process.md:103-110`)과 동형으로 brain search 결과를 워커 컨텍스트에 주입. **brain/code-scan 부재 시 자연 스킵**([MUST] 동형 패턴, → D-5).

---

## 3. 실행 체크리스트

> 총 12개 Step | Phase 6개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | P1 | 1, 2 | 순차 | Step1(SCHEMA)→Step2(brain-tool, 템플릿 의존) |
> | P1 | 3 | 순차 | Step2 의존 (도구 테스트) |
> | P2 | 4 | 순차 | Step2 의존 (스킬이 brain-tool 인터페이스 참조) |
> | P3 | 5 | 순차 | Step2 의존, Step4와 병렬 가능 |
> | P4 | 6, 7 | 순차 | Step6(워커)→Step7(opp CLOSE 훅) |
> | P5 | 8 | 순차 | Step4 의존 (ingest 모드 확장) |
> | P6 | 9, 10 | 병렬 | install 3종(독립 파일) |
> | P6 | 11 | 순차 | Step9·10 의존 (배포 후 시드) |
> | docs | 12 | 순차 | 전 Step 의존 (문서 정합) |

### Step 1: SCHEMA 표준·페이지 템플릿 작성 (R2)
- [ ] 완료
- **파일**: N-3 `opal/tools/brain-tool/templates/schema-template.md`, N-4 index-template.md, N-5 log-template.md, N-6 page-{entity,concept,flow,synthesis}.md
- **작업 내용**: 결정 7의 frontmatter 표준(필수/선택/entity 추가 키), 네이밍·링크 3종 규칙, index/log 구조를 SCHEMA 템플릿에 정의. 4개 페이지 타입 템플릿 작성. 한국어 본문 + English frontmatter 키 ([MUST] 언어 규칙).
- **완료 기준**: SCHEMA.md에 4 페이지 타입·frontmatter 필드·링크 규칙이 모두 정의됨 (TASK R2 AC). YAML 파싱 유효.
- **테스트**: PyYAML로 frontmatter 파싱 성공 + 사람 리뷰.
- **의존**: 없음
- **agent**: opal-task-agent (EXECUTE)

### Step 2: brain-tool 도구 구현 (R1)
- [ ] 완료
- **파일**: N-1 run.sh, N-2 brain_tool.py, N-7 README.md
- **작업 내용**: state-tool run.sh 복제(스크립트명 교체). brain_tool.py에 8 서브커맨드(결정 3) + ERROR_CODES 카탈로그 + get_kst_datetime(date.js). init은 Step1 템플릿 복사. sync-header는 code-scan.json 단방향 시드([MUST] 단방향). @header 블록 작성(Python = snake_case 파일, → D-8 @header 규칙).
- **완료 기준**: `run.sh init/add-page/index/log/search/sync-header/lint/validate` 8종 동작. init이 `.opal/brain/` 골격 생성, validate가 frontmatter 위반 검출 (TASK R1 AC). 출력 JSON `{ok:...}`.
- **테스트**: Step3에서 단위 테스트.
- **의존**: Step 1
- **agent**: opal-task-agent (EXECUTE)

### Step 3: brain-tool 단위 테스트 (R1 검증)
- [ ] 완료
- **파일**: N-8 `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: 8 서브커맨드 happy-path + 주요 에러 코드(brain_not_initialized, invalid_page_type, frontmatter_invalid 등) 테스트. state-tool tests 패턴 준용.
- **완료 기준**: 전 테스트 통과(`~/.opal/.venv/bin/python -m pytest`). 에러 코드 카탈로그 키 정합.
- **테스트**: pytest 실행 결과 green.
- **의존**: Step 2
- **agent**: opal-test-agent (TEST)

### Step 4: opal-brain 스킬 + 레지스트리 등록 (R3)
- [ ] 완료
- **파일**: N-9 SKILL.md, N-10 references/brain-schema.md, M-1 opal-skills-registry.json
- **작업 내용**: 단일 pilot + 4모드 라우팅(D-1 §6). init 임계값(결정4)·ingest 배치(결정5) 명시. 레지스트리 `opal` 그룹에 opal-brain(alias opbr, triggers, domain knowledge, pipeline "MODE: init|ingest|query|lint") 행 추가 (→ D-10). 변경이력.
- **완료 기준**: `//opbr` 매칭이 레지스트리에서 성공, SKILL.md 4모드 라우팅 정의 (TASK R3 AC). frontmatter version·triggers 유효.
- **테스트**: skill-registry 검색으로 opbr 매칭 확인 (`opal-cli`/registry).
- **의존**: Step 2
- **agent**: opal-task-agent (EXECUTE)

### Step 5: PM 융합 — 부트스트랩·dispatch·AGENT 규칙 (R4)
- [ ] 완료
- **파일**: M-2 opal/core/AGENT.md, M-3 dispatch-process.md
- **작업 내용**: AGENT.md Lazy 테이블에 brain/index.md 행 + "opal-brain 활용 규칙" 테이블(code-scan 규칙 동형, → `:175-188`). dispatch-process Step 1.5 신설(brain search→주입, → `:103-110` 동형). brain 부재 시 자연 스킵 명시. 변경이력.
- **완료 기준**: 세 위치(Lazy 트리거 / AGENT 활용 규칙 / dispatch Step 1.5)에 brain 참조가 code-scan 우선 규칙과 동형으로 기재 (TASK R4 AC).
- **테스트**: 문서 정합 리뷰 — code-scan 규칙과 1:1 대응 확인.
- **의존**: Step 2 (brain-tool search 존재 전제)
- **agent**: opal-task-agent (EXECUTE)

### Step 6: op-brain-ingest 경량 워커 스킬 (R5)
- [ ] 완료
- **파일**: N-11 `opal/skills/op-brain-ingest/SKILL.md`
- **작업 내용**: CLOSE 디스패치 경량 워커. DONE.md·PLAN 의사결정·신규 엔티티 읽기→concept/entity 페이지 작성→brain-tool add-page/index/log. ingest 대상/제외 기준 명시(D-1 §8.2). brain 미존재 시 no-op 반환. 레지스트리 행(M-1에 함께 또는 별도). 변경이력.
- **완료 기준**: 워커가 brain-tool 호출로 페이지·log·index 갱신, brain 부재 시 안전 스킵.
- **테스트**: brain 시드(Step11) 후 모의 CLOSE로 ingest 동작 확인.
- **의존**: Step 2, Step 4
- **agent**: opal-task-agent (EXECUTE)

### Step 7: opp CLOSE 자동 ingest 훅 (R5 파일럿)
- [ ] 완료
- **파일**: M-4 opal/skills/opal-pilot-project/SKILL.md
- **작업 내용**: CLOSE STEP 4 ①DONE.md 생성 → **①.5 op-brain-ingest 디스패치(brain 존재 시, PM Gate 후)** → ②완료 보고 삽입 (→ `:118-127`). **STATE 행 추가 금지**(9행 구조 유지, 결정6). 변경이력.
- **완료 기준**: opp CLOSE에 ingest 훅 존재, STATE `--rows-from` 파싱 영향 0 (9행 유지).
- **테스트**: `state init --rows-from <opp SKILL.md>`가 여전히 9행 추출하는지 확인.
- **의존**: Step 6
- **agent**: opal-task-agent (EXECUTE)

### Step 8: 외부 소스 파이프라인 (R6)
- [ ] 완료
- **파일**: N-9 opal-brain SKILL.md (ingest 모드 확장)
- **작업 내용**: `//opbr ingest <URL/파일>` → wtm/xlsx-tool/이미지·PDF Read로 변환 → `sources/<id>/raw.md`+`meta.yaml`(출처·수집일·라이선스) 저장 → 요약 페이지 작성 + `[[source:id]]` 링크 (→ D-1 §8.3, D-13). 내부 코드는 참조만([MUST] 단방향).
- **완료 기준**: `//opbr ingest <URL>` 시 sources/에 raw.md+meta.yaml 저장 + 요약 페이지 생성 (TASK R6 AC).
- **테스트**: 샘플 URL ingest로 sources/ 산출 확인.
- **의존**: Step 4
- **agent**: opal-task-agent (EXECUTE)

### Step 9: install-mac.sh + 하네스 도구표 동기화 (R7)
- [ ] 완료
- **파일**: M-5 install-mac.sh, M-8 opal-harness.md
- **작업 내용**: install-mac.sh tools 블록에 brain-tool/run.sh `chmod +x` 추가(state-tool 블록 복제, → `:951-956`). 스킬·도구·레지스트리는 자동 동기화(수정 불요, 결정8). 하네스 §9 도구표에 brain-tool 행. 변경이력.
- **완료 기준**: install 후 `~/.opal/skills/opal-brain/`·`~/.opal/skills/op-brain-ingest/`·`~/.opal/tools/brain-tool/run.sh`(실행권한) 존재 (TASK R7 AC).
- **테스트**: `./scripts/install-mac.sh` 실행 후 경로·권한 확인.
- **의존**: Step 2, 4, 6
- **agent**: opal-task-agent (EXECUTE)

### Step 10: windows.ps1 / linux.sh 대칭 반영 (R7)
- [ ] 완료
- **파일**: M-6 scripts/install/windows.ps1, M-7 scripts/install/linux.sh
- **작업 내용**: windows.ps1 도구 복사·실행 로직에 brain-tool 대칭 반영. linux.sh가 mac 위임 구조면 수정 불요(검토 후 확정). [MUST] 플랫폼 분기는 어댑터(install)에만.
- **완료 기준**: 3 플랫폼 install이 brain-tool·스킬을 동일하게 배포.
- **테스트**: ps1 구문 검토 + (가능 시) 드라이런.
- **의존**: 없음 (Step 9와 독립 파일, 병렬)
- **agent**: opal-task-agent (EXECUTE)

### Step 11: code-scan.json 생성 + `//opbr init` 시드 적용 (R7)
- [ ] 완료
- **파일**: M-9 `.opal/code-scan.json`, `.opal/brain/`(시드 산출)
- **작업 내용**: PM이 `.opal/code-scan.json` 생성(Framework scope, → D-5 §생성 시점). install 후 `//opbr init` 실행 → 골격·SCHEMA·핵심 엔티티 시드(결정4 임계값). brain 부트스트랩.
- **완료 기준**: `.opal/brain/`에 SCHEMA.md·index.md·log.md·핵심 entity 페이지 생성, index 전체 맵 등록 (TASK R7 AC).
- **테스트**: `brain-tool validate`·`lint` green, index.md 카탈로그 확인.
- **의존**: Step 9, Step 10
- **agent**: opal-task-agent (EXECUTE)

### Step 12: docs/ 갱신 (문서 정합)
- [ ] 완료
- **파일**: M-10 docs/PROJECT.md, docs/CONVENTIONS.md (필요 시)
- **작업 내용**: brain 시스템 신설 반영 — PROJECT.md 문서 테이블/주요 컴포넌트에 opal-brain·brain-tool 항목, CONVENTIONS.md에 brain SCHEMA 규약 링크(해당 시).
- **완료 기준**: docs가 brain 신설 상태와 정합.
- **테스트**: 문서 리뷰.
- **의존**: 전 Step
- **agent**: PM 직접 (docs/ 갱신)

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] brain-tool 8 서브커맨드(init/add-page/index/log/search/sync-header/lint/validate)가 동작하고 JSON `{ok}` 출력 (R1)
- [ ] init이 `.opal/brain/` 골격 생성, validate가 frontmatter 위반 검출 (R1 AC)
- [ ] SCHEMA.md에 4 페이지 타입·frontmatter 필드·링크 규칙 정의 (R2 AC)
- [ ] `//opbr` 레지스트리 매칭 성공 + SKILL.md 4모드 라우팅 (R3 AC)
- [ ] AGENT.md·dispatch·AGENT 규칙 3위치에 brain 참조가 code-scan 동형 기재 (R4 AC)
- [ ] opp CLOSE에서 태스크 결정·신규 엔티티가 brain 페이지로 누적, log·index 갱신 (R5 AC)
- [ ] `//opbr ingest <URL>` 시 sources/에 raw.md+meta.yaml + 요약 페이지 (R6 AC)
- [ ] install 후 brain 스킬·도구 경로 존재 + `//opbr init`로 `.opal/brain/` 생성 (R7 AC)

### 일관성 테스트
- [ ] brain-tool run.sh가 state-tool run.sh 패턴과 동형(venv python exec)
- [ ] brain-tool ERROR_CODES가 state-tool 카탈로그 방식과 동형(상수 키만 사용)
- [ ] opp STATE 행이 9행 유지(state-tool `--rows-from` 파싱 회귀 없음)
- [ ] @header→brain 단방향만(역방향 갱신 코드 부재) — [MUST] 단방향 동기화
- [ ] 플랫폼 분기가 스킬·도구 본문이 아닌 install에만 존재 — [MUST] 플랫폼 분기 격리
- [ ] brain/code-scan 부재 프로젝트에서 PM 융합·CLOSE 훅이 자연 스킵(no-op)

### 문서 품질
- [ ] 한국어 본문 + English 코드/frontmatter 키/필드명 — [MUST] 언어 규칙
- [ ] kebab-case 파일/폴더 (Python 파일 snake_case)
- [ ] YAML frontmatter 유효 (PyYAML 파싱)
- [ ] 수정 대상 전 스킬·참조 문서에 `(015)` 변경이력 행 추가 — [MUST] 변경이력

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | `.opal/code-scan.json` 부재 — R7 init @header 시드 불가 | Step11 차단 | Step11에서 PM이 code-scan.json 선생성(Framework scope) → init 진행 (→ D-5 §생성 시점) |
| R-2 | opp CLOSE STATE 행 변경 시 014 정합 9행 구조 회귀 | state-tool `--rows-from` 파싱 오류 | 결정6 — ingest를 CLOSE 행 내부 흡수, 행 추가 금지. Step7 테스트로 9행 검증 |
| R-3 | CLOSE 자동 ingest noise 누적 (전 태스크 적용 시) | brain 품질 저하 | 결정6 — opp 단독 파일럿 후 확산. ingest 대상/제외 기준 + lint 주기 (→ D-1 §12 R1) |
| R-4 | `ingest --all` 토큰·시간 비용 | 비용 폭증 | 결정5 — 명시 옵션 + 5자산 배치 + 멱등 skip + 진행률·재개 (→ D-1 §12 R6) |
| R-5 | 멀티 에이전트 동시 ingest 시 index 충돌 | index.md 손상 | 결정5 — brain-tool index/log 원자 갱신(LLM은 페이지만, 인덱싱 1회) (→ D-1 §12 R2) |
| R-6 | @header drift로 entity 시드 stale | brain 정보 노후 | sync-header 단방향 재동기화 + lint stale 표시(코드 SSOT) (→ D-1 §12 R5) |
| R-7 | windows.ps1 도구 복사 로직이 mac과 비대칭 | windows 배포 누락 | Step10에서 ps1 복사 블록 직접 확인 후 대칭 반영 |
| R-8 | understand-anything 그래프 연동 깊이 | 범위 확대 | 후속 태스크 분리 권고(본 태스크 제외, → D-1 §12 R3) |

> **용어 일관성 검토 (citation-rules §7)**: brain 신규 도메인이라 기존 영역과 토큰 충돌 없음. "ingest/query/lint/init" 모드명·"entity/concept/flow/synthesis" 타입명은 llm-wiki 원전 용어를 일관 사용(→ D-2). `decision_required` 에스컬레이션 사항 없음.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — Phase 6분해, brain-tool Python 결정, 8서브커맨드 인터페이스, init 임계값, ingest 배치 정책, opp 단독 CLOSE 파일럿, SCHEMA 표준, install 동기화 지점 확정 + 12 Step 실행 체크리스트 (015) |

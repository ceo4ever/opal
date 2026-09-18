# TASK: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 작성일: 2026-09-04 | 작업 유형: 신규+개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`@header` 자산(인라인 주석 또는 `.opal/code-map/` 매니페스트)의 **최초 구축·환경설정을 독립 스킬로 제공**하고, **갱신 트리거와 소비 절차를 하네스에 편입**하여 자산의 생성–갱신–소비 3국면을 완결한다.

## 배경

`code-scan`은 code-map 계열 5서브명령(`discover`/`scaffold`/`target`/`validate`/`split`)을 이미 보유하지만, 이를 파이프라인으로 묶는 스킬이 프레임워크 전체에 없다. 하네스는 자산의 **증분 갱신**만 정의하고 최초 구축을 관할 밖으로 밀어냈으며, **소비 절차는 규정이 있으나 집행이 산문·자기판정**에 머문다. 결과적으로 자산을 만들 주체가 없고, 만들어도 읽도록 강제하는 장치가 없다.

## 배경 분석 (대화에서 도출)

### (1) 부재 실측 — 오케스트레이션 스킬 0건

- `opal/skills/`·`opal/agents/` 전수 검색 결과 `discover`/`scaffold`를 참조하는 스킬은 `opal-pilot-dev-wireframe` 1건뿐이며 UI 문맥의 동명이의어다.
- `code-scan`을 참조하는 16개 파일은 전부 **조회 계열**(`scan`/`search`/`domain`/`exports`) 사용이다.
- `opal-project-init`(opi)의 SKILL.md에는 `code-scan`·`code-map` 언급이 0건이다 — 프로젝트 자산 셋업 스킬인데 이 자산을 다루지 않는다.

### (2) 기존 pilot 10종 적합성 판정

| pilot | 부적합 사유 |
|-------|-----------|
| `opgc` | 진단 전담·수정 없음 — 자산 생성은 쓰기 행위 |
| `opds`/`opd` | 코드 로직 변경 + 동작검증 전제 — 대상은 메타데이터 자산 |
| `opdd` | 구조는 유사하나 DB 도메인 전용 |
| `opwt` | 산출물 종류 불일치 |
| `oppl` | 골격(백로그·수렴·사람게이트)은 최적이나, D5 실행 스켈레톤 P0 의무(BE 서버 기동+스웨거·FE dev·브라우저 관통)가 예외절 없이 D6 Evaluator 루브릭 binary로 집행되어 비-서비스 자산 구축은 D7에 도달하지 못한다 |
| `opp` | 수용 가능하나 절차를 PLAN이 매번 재설계한다 |

### (3) 하네스 정의 소재 3층 — 정의된 것은 증분 경로 하나뿐

| 층 | 소재 | 내용 |
|----|------|------|
| 하네스 본체 | `opal/core/references/opal-harness.md` §8 · §9 | §8은 본문 없는 위임 stub. Lazy 로드 시점이 "EXECUTE 단계에서 코드 파일 생성/수정 시"로 한정 |
| 증분 규정 | `opal/core/references/harness/header-rules.md` §갱신 시점 (3단) | (a) 워커 같은 자리 기록 / (b) CLOSE 진입 전 `validate --changed` 차단 / (c) PostToolUse hook 경고 |
| 최초 구축 | `opal/core/references/pm/code-scan-management.md` §.opal/code-map/index.json PM·소유자 관리 의무 | `discover` 초안 → 소유자 리뷰 → `status: draft`→`reviewed` **산문 3단**. 파이프라인 단계·게이트 산출물·`state-tool` 행·팬아웃 규율 없음 |

- `header-rules.md` §갱신 시점 (3단) (b) 행이 관할을 명시적으로 이관한다 — **"레거시 소급 부여는 이 게이트가 아니라 `discover`/`scaffold`의 몫이다."** 이관 문장은 있으나 수신 문서가 없다.
- `scaffold` 이후 **매니페스트 내용을 누가 어떤 순서로 채우는가**는 어느 문서에도 없다. `header-rules.md` 도입부가 "도구는 구조를 만들고 워커는 내용을 채운다"고 원칙만 밝힌다.

### (4) 집행 등급 비대칭 — 같은 자산의 쓰기와 읽기

| 대상 | 집행 형태 | 소재 |
|------|----------|------|
| `headerSource` 미설정 | 도구 차단 — 전 명령 exit 1 거부, 폴백 없음 | `opal/core/references/header-standard.md` §7 |
| 변경 파일 @header 누락 | 도구 차단 — `validate --changed` exit≠0이면 CLOSE 진입 차단 | `opal/core/references/harness/header-rules.md` §갱신 시점 (3단) |
| 디스패치 전 code-scan 호출 | **PM 자기판정** — PM Gate 검토 항목, 도구 게이트 없음 | `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14 |
| 워커의 자산 소비 | **권고** — "`.opal/code-scan.json`이 있으면", "적극 활용한다" | `opal/agents/opal-be-agent/AGENT.md` §도구 활용 · `opal/agents/opal-plan-agent/AGENT.md` §도구 활용 |

- 하단 2행은 헌법에 정면으로 걸린다 — `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."
- 특히 검토 항목 14는 **PM이 자기 디스패치 프롬프트의 인용 여부를 자기가 판정**하는 구조로, `opal-pilot-project-loop`가 검증 2원화(생성자≠평가자)로 해결한 문제와 동형이다.

### (5) 소비 규정 현황 — 1차는 명문, 2차 전환은 미서술

| 단계 | 현행 | 상태 |
|------|------|------|
| 1차 code-scan 범위 축소 | `opal/core/references/pm/dispatch-process.md` §code-scan 사전 범위 파악: "코드 변경·코드 탐색이 필요한 작업이면 디스패치 전 code-scan을 무조건 호출한다" | 명문 |
| 우회 봉쇄 | 동 §: "Glob/Grep 직행 금지" | 명문 |
| 2차 grep 전환 | 없음 — `opal/core/references/opal-pm.md` §13의 grep 조항은 **소유자 오버라이드**("사용자가 'grep으로 해'라고 명시하면")뿐 | 미서술 |

### (6) L2 경량 트랙 게이트 공백

| 변경 경로 | @header 작성 규정 | 갱신 검증 게이트 |
|-----------|------------------|-----------------|
| 태스크 EXECUTE → CLOSE | 있음 — 워커 같은 자리 기록 | 있음 — `validate --changed` exit≠0 → CLOSE 차단 |
| **L2 경량 트랙(PM 직접 수정)** | 있음 — `opal-pm.md` §12 표 "@header 규칙 ✅ 유지" | **없음 — 동일 표 "Gate ❌ 미적용"** |

- L2는 헤더를 쓰라는 의무는 지되 썼는지 확인하는 장치가 없다. `validate`는 CLOSE 진입 게이트에만 붙어 있고 L2에는 CLOSE가 없다.
- `opal-brain`의 ingest 트리거는 PM 주관 판단이지만, @header 갱신은 `changed_files`라는 객관 입력이 있어 **주관 판단 없이 결정론 집행이 가능**하다.

### (7) 2소스 관계 — code-map은 2방식 중 한쪽

- `header-standard.md` §7 제목이 관계를 그대로 쓴다 — "2소스 표현 — 인라인과 code-map". 상위 개념이 `@header`이고 인라인·code-map이 그 아래 두 소스다.
- 두 소스는 `headerSource`(프로젝트당 전역 1개)에 의해 **상호 배타**이며 경합·병합 규칙이 존재하지 않는다. `inline` 모드는 `.opal/code-map/`을 읽지도 쓰지도 않는다.
- 따라서 신설 스킬의 범위는 code-map보다 넓다 — `init`(설정 확정)은 두 모드 공통이고, `update`만 모드별로 갈린다.

## 확정된 설계 방향 (대화에서 합의)

- **[결정]** 최초 생성·환경설정은 **하네스에 넣지 않고 독립 스킬**로 제공한다. `opi`처럼 생성·업데이트 2모드를 갖는다.
- **[사실]** 이 결정은 규정 구조와 정합한다 — `opal-harness.md` §8의 Lazy 로드 시점이 "EXECUTE 단계에서 코드 파일 생성/수정 시"로 한정되어, 1회성 구축은 애초에 그 트리거에 속하지 않는다.
- **[결정]** 갱신은 **매번 트리거되는 하네스 규정**으로 편입한다 — 태스크 CLOSE, PM 직접 수정(L2) 완료 시점 등 소스 코드 변경이 발생한 경우.
- **[결정]** 소비는 **2단 절차**로 규정한다 — 1차 `code-scan`으로 빠르게 찾고, 상세 작업이 필요하면 2차로 grep으로 전환한다.
- **[결정]** 스킬 신설과 하네스 개정을 **하나의 태스크로 통합**하여 수행한다.
- **[사실]** 스킬이 다루는 두 관리 방식(인라인 헤더 / code-map)은 상호 배타이며 프로젝트당 하나만 선택 가능하다 — 근거 `header-standard.md` §7.
- **[결정]** 레거시 소급 기입(backfill) 팬아웃과 `split` 샤딩 모드는 이번 범위에서 제외한다.
- **[결정]** 스킬명은 `opal-code-map-builder`, 약어는 `opcmb`로 확정한다. 접미사 `-builder`는 `wireframe-builder`(wfb) 선례를 따른다.
- **[결정]** 스킬 범위는 `manifest` 구축 중심으로 둔다 — `inline`은 `headerSource` 확정·`code-scan.json` 기록 후 **종료 분기**이며, 종료 시 `code-scan missing` 안내를 반환한다.
- **[결정]** 하네스 모드는 `agentic`으로 진행한다 — PLAN까지의 사용자 검토를 PM 대행으로 대체하고, CLOSE 진입만 소유자 승인을 유지한다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `@header` 자산의 최초 구축·환경설정을 독립 스킬(2모드)로 제공하고, 갱신 트리거와 소비 2단 절차를 하네스에 편입한다 | - | `opal/core/references/opal-harness.md` §8 · `opal/core/references/header-standard.md` §7 |
| 범위 | **포함** — ① `opal-code-map-builder`(`opcmb`) 신설 — `manifest` 구축 중심, `inline`은 설정 후 종료 분기 (모드 `init`\|`update`) + 레지스트리·CONVENTIONS 약어 등록 ② L2 경량 트랙 갱신 검증 게이트 신설 ③ 소비 2단 규율 명문화 ④ 소비 절차 집행 승격(자기판정→도구 판정) ⑤ 미보급 프로젝트 폴백. **제외** — 레거시 소급 기입(backfill) 팬아웃 오케스트레이션, `split` 샤딩 모드, `opi`에의 Phase 편입 | `update` 모드 판별 방식(자산 존재 감지 vs 명시 라우팅) / ④의 집행 지점 | `opal/core/references/opal-pm.md` §12 · `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14 |
| 제약 | ① `~/.opal/` 직접 편집 금지 — 프로젝트 소스 수정 후 install 재배포 ② `headerSource`는 프로젝트당 전역 1개·2택·상호 배타, 병합 규칙 신설 금지 ③ 약어 등록은 레지스트리 JSON에서만 수행(CONVENTIONS 표는 사본) ④ L2 = "Gate 미적용" 설계 원칙과의 충돌을 예외 1행 또는 표 개정으로 해소해야 한다 ⑤ 문서 변경이력 규약은 `.opal/AGENT.md` 현행(행 추가 의무)을 따르되, 메모리에 기록된 변경이력 제거 A안(2026-08-14 확정, 미실행)과의 정합은 PLAN에서 판단 | ⑤의 처리 방향 | `.opal/AGENT.md` §금지사항 · `docs/CONVENTIONS.md` §약어 (Alias) · `opal/core/references/opal-pm.md` §12 |
| 완료기준 | R-1~R-6 AC 전건 충족 + 기존 pilot(opd/opds/opp) 파이프라인 행 구성·게이트 회귀 0 + 이 레포(`headerSource: inline`·code-map 부재)에서 신설 집행의 오탐 0건 | - | `.opal/code-scan.json` |

## 요구사항

- [ ] **R-1 스킬 신설** — 무엇을: `@header` 자산 관리 스킬 신설(모드 `init`\|`update`, `code-scan` 서브명령 호출층). 어디에: `opal/skills/opal-code-map-builder/SKILL.md`(신규) + `opal/core/references/opal-skills-registry.json` + `docs/CONVENTIONS.md` §약어 (Alias). 왜: 확정 방향 1항. **AC**: (a) SKILL.md가 지정 경로에 존재하고 frontmatter에 `name`·`description`·`alias`·`triggers`·`version` 5필드가 채워져 있다 (b) 레지스트리 JSON에 `name: opal-code-map-builder` · `alias: opcmb` 항목 1건이 추가되고 기존 29종과 중복 0건이다 (c) `init` 모드가 `headerSource` 2택을 소유자에게 제시한 뒤 `code-scan init --header-source <값> --write`를 호출하는 절차로 기술되어 있다 (d) `manifest`는 `discover`→소유자 리뷰→`scaffold` 절차를, `inline`은 설정 확정 후 종료 분기임을 각각 명시하고 종료 시 `code-scan missing` 안내를 반환한다
- [ ] **R-2 갱신 트리거 하네스 편입** — 무엇을: L2 경량 트랙 완료 시점의 @header 갱신 검증 게이트 신설. 어디에: `opal/core/references/opal-pm.md` §12(L2 하네스 적용 범위 표) + `opal/core/references/harness/header-rules.md` §갱신 시점 (3단). 왜: 배경 분석 (6) — 작성 의무는 있고 검증 게이트가 없다. **AC**: (a) `opal-pm.md` §12 표에 @header 검증 행이 추가되고 적용 여부가 명시된다 (b) `header-rules.md` 갱신 시점 표에 L2 완료 시점이 행으로 존재한다 (c) 검증 미수행이 탐지되는 조건이 **모드별로** 문서에 명시된다 — `inline`은 `counts.newly_uncovered` ≥1, `manifest` 관리 매니페스트 하위는 `violations[].sub == "no_entry"`. 두 경우 모두 `validate --changed` exit≠0으로 CLOSE 진입이 차단된다
- [ ] **R-3 소비 2단 규율 명문화** — 무엇을: 1차 `code-scan` 범위 축소 → 2차 grep 상세 전환의 정당 경로 서술. 어디에: `opal/core/references/opal-pm.md` §13 + `opal/core/references/pm/dispatch-process.md` §code-scan 사전 범위 파악. 왜: 배경 분석 (5) — 2차 전환이 미서술이라 양방향 오해가 남는다. **AC**: (a) §13에 2단 소비 절차가 표 또는 절로 존재한다 (b) grep 전환의 허용 조건이 명시되고 소유자 오버라이드 조항과 구분된다 (c) "Glob/Grep 직행 금지"와 문언상 모순이 없다
- [ ] **R-4 소비 집행 승격** — 무엇을: 소비 절차를 PM 자기판정에서 도구 판정으로 승격. 어디에: `code-scan` 도구 + `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14. 왜: `~/.opal/PRINCIPLES.md` §Core Stance "Enforce, don't just advise". **AC**: (a) 집행 방식이 ANALYSIS에서 2개 이상 후보로 비교되고 PLAN에서 1개로 확정된다 (b) 소비 미수행 케이스에서 비통과(exit≠0 또는 Fail)가 실행 출력으로 관찰된다 (c) 소비 수행 케이스에서 통과가 실행 출력으로 관찰된다
- [ ] **R-5 미보급 프로젝트 폴백** — 무엇을: `headerSource: inline` + code-map 부재가 정상 상태인 프로젝트에서 R-2·R-4 집행이 오탐을 내지 않게 하는 폴백. 어디에: R-2·R-4가 손대는 동일 문서 + 도구. 왜: 이 레포가 해당 상태다. **AC**: (a) 이 레포에서 R-2·R-4 집행 경로를 실행해 오탐 0건이 관찰된다 (b) 폴백 조건이 문서에 명시된다
- [ ] **R-6 회귀 보존** — 무엇을: 기존 파이프라인 무변경 확인. 어디에: `opal/skills/opal-pilot-{dev,dev-short,project}/references/pipeline.json` 및 관련 게이트. 왜: 하네스 개정이 기존 태스크 진행을 깨지 않아야 한다. **AC**: (a) opd/opds/opp의 `task_steps` 행 수·key가 개정 전후 동일하다 (b) 기존 태스크 폴더에서 `state-tool show`가 오류 없이 동작한다

## 제약 조건

- **배포 경계**: `~/.opal/` 배포본을 직접 수정하지 않는다. `opal/`·`skills/`·`agents/`·`scripts/` 소스를 수정한 뒤 install로 재배포한다.
- **플랫폼 분기 금지**: Claude/Cursor/Gemini 분기는 어댑터 계층(install)에서만 수행한다.
- **하네스 우회 금지**: CLOSE 진입 게이트를 포함한 Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다.
- **2소스 배타 유지**: `headerSource` 2택의 상호 배타 계약을 깨는 병합·폴백을 신설하지 않는다.
- **약어 영구 점유**: 신규 약어 1종은 되돌리기 비용이 크므로 TASK 단계에서 확정한다.

## 기술 스택

- Markdown (프레임워크 문서·스킬 정의)
- Node.js — `opal/tools/code-scan/code-scan.js` (v1.6.0), `code-map-hook.js`
- Python — `state-tool`(`state_tool.py`), `memory-tool`, `brain-tool`
- Bash — 도구 래퍼 `run.sh`, `scripts/install-mac.sh`
- JSON — `opal-skills-registry.json`(v3.13.0), `.opal/code-scan.json`, `.opal/code-map/index.json`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §7 2소스 표현·§7.1~7.3 index.json·매니페스트·`_source` 계약 — 스킬 범위 판정의 근거 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §갱신 시점 (3단)·§워커 권한 경계 — R-2 개정 대상 |
| D-3 | 설계 | code-scan.json PM 관리 의무 | `opal/core/references/pm/code-scan-management.md` | §생성 시점·§headerSource 필드 관리·§index.json PM·소유자 관리 의무 — R-1 절차 원천 |
| D-4 | 설계 | OPAL PM 행동 프로세스 | `opal/core/references/opal-pm.md` | §12 L2 트랙·§13 code-scan 활용 규칙 — R-2·R-3 개정 대상 |
| D-5 | 설계 | PM 디스패치 전 프로세스 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악 — R-3 개정 대상 |
| D-6 | 설계 | PM 검토 게이트 | `opal/core/references/harness/pm-review-gate.md` | §표준 검토 항목 8·14 — R-4 개정 대상 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | §Core Stance enforce 원칙 — R-4 근거 |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | §네이밍 규칙·§약어 (Alias) — R-1 명명·등록 규약 |
| D-9 | 소스 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 약어 SSOT(v3.13.0) — R-1 등록 대상 |
| D-10 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | 15서브명령 — R-1 호출층·R-4 집행 후보 |
| D-11 | 설계 | 모드 라우팅 선례 | `opal/skills/opal-brain/SKILL.md` | 자산 관리 스킬의 모드 라우팅 구조 — R-1 구조 준용 |
| D-12 | 설계 | 2모드 자동 판별 선례 | `opal/skills/opal-project-init/SKILL.md` | 초기화/최신화 2모드 판별 — R-1 `update` 판별 방식 후보 |

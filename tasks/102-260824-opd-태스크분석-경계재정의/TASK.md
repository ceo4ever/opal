# TASK: op-task 재정의 — 요구사항 도출기 전환 + 판정축 배선 + 자산 정합

> 작성일: 2026-08-24 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`op-task`를 "칸을 채우는 양식 생성기"에서 "요구사항을 날카롭게 만드는 도출기"로 되돌린다. TASK.md의 독자를 PM(판단 근거)과 하류 단계(분석·설계의 근거)로 확정하고, 이미 존재하나 아무 데서도 호출되지 않는 판정 2축을 보고·회수 경로에 배선하며, 17회 개정이 남긴 자기 정합 결함과 5개월 stale 참조 자산을 정리한다.

## 배경

`op-task`는 초기 작성(태스크 032) 이후 17회 개정됐으나 그 전부가 타 태스크의 하류 정합 패치였고, 스킬 자신을 위한 개정은 한 건도 없었다.

개정이 전부 '추가'였던 결과 무게중심이 이동했다. 스킬의 실질 가치인 요구사항 명확화 절차는 25줄로 초판 그대로인데, 양식·저장 경로·STATE 리마인더·체크리스트는 112줄로 불었다. 스킬은 "무엇을 물어야 하는가"가 아니라 "어느 칸을 채워야 하는가"를 지시하는 문서가 됐다.

개선이 없었던 것은 태만이 아니라 구조다. TASK 단계는 전 pilot에서 게이트 행이 없는 유일한 작업 단계이며, TASK.md는 하류 게이트의 **기준**으로만 쓰이고 그 자신의 품질은 어디서도 판정되지 않는다. 채점되지 않는 산출물의 생성기는 개선 신호를 받을 창구가 없다.

다만 판정 자체가 전무한 것은 아니다. 도구 층에는 TASK.md를 보는 축이 이미 둘 있다. 문제는 그중 하나가 항상 exit 0이고 어떤 파이프라인 행도 그것을 호출하지 않아 결과가 아무에게도 보이지 않는다는 점이다. 따라서 필요한 것은 게이트 신설이 아니라 배선이다.

## 확정된 설계 방향 (대화에서 합의)

### 결정 사항

- **[결정] D-1 경계 원칙** — TASK는 "무엇을·왜·어디까지"를, ANALYSIS는 "어디를·어떻게"를 소유한다. (구 102 TASK.md D-1 승계 — 유일 승계 항목)
- **[결정] D-2 정체 확정** — `op-task`는 **요구사항 도출기**다. 요구사항 명확화를 스킬의 중심 절차로 승격하고, 양식 절차(템플릿·저장 경로·STATE 리마인더·완료 보고)는 참조 파일로 외부화한다.
- **[결정] D-3 독자 확정** — TASK.md의 독자는 **PM(판단 근거)이자 하류 분석·설계의 근거 문서**다. 워커 자립 컨텍스트도, 실측 저장소도 아니다.
- **[결정] D-4 판정처** — 게이트 행을 신설하지 않는다. 이미 있는 판정 2축을 (a) TASK 완료 보고에 노출하고 (b) 하류 단계가 TASK.md 결손을 만났을 때 기록하는 회수 통로를 신설한다.
- **[결정] D-5 비판정 대상** — 요구사항의 내용(무엇을 원하는가)은 소유자 권한 행사이므로 판정 대상이 아니다. 판정 가능한 것은 4요소 잠금·`[사실]` 주장의 근거 귀속·필수 필드 존재 3종에 한정한다.
- **[결정] D-6 승계 범위** — 구 102 TASK.md에서 D-1만 승계하고 나머지(선조회 단 분할·후속 스킬 배선·순서 강제·안전장치 3종 등)는 폐기한다.
- **[결정] D-7 순서 강제** — 하류 회수 통로(R-4)는 `op-dev-analysis`·`op-dev-plan`을 접촉하므로 **태스크 101 CLOSE 이후에만** 착수한다. R-1·R-2·R-3·R-5·R-6·R-7은 선착수 가능하다.
- **[결정] D-8 범위 제외** — 변경이력 표 일괄 제거는 별건 태스크로 예정되어 있으므로 본 태스크에서 수행하지 않는다.
- **[결정] D-9 자기적용** — 본 TASK.md 자신을 새 경계로 작성한다(실측 덤프 없음, 사실은 태그·인용으로 압축, 미결은 ANALYSIS 위임).

### 확인된 사실

- **[사실] F-1** `op-task/SKILL.md` 변경이력 18행 중 v1.1~v2.7 17건 전부가 타 태스크 번호를 인용하며, 스킬 자체 발의 개정은 0건이다 (E2: `opal/skills/op-task/SKILL.md:269-286`).
- **[사실] F-2** 참조 자산 2종은 생성 이후 내용 개정이 0회이며 이동·리네이밍 커밋만 존재한다 (E1: `git log --oneline --follow -- opal/skills/op-task/references/task-guide.md` 및 동일 명령의 `personas/service-planner.md` — 스코프: 각 파일 전체 이력, 결과 각 3커밋 = 032 생성 / 042 리네이밍 / 051 이동).
- **[사실] F-3** TASK 단계는 검사한 4개 pilot 전부에서 `작업`·`사용자 확인` 2행뿐이고 게이트 행이 없다. 같은 파일의 ANALYSIS·PLAN·TEST-SCENARIO·TEST는 전부 게이트 행과 checklist를 보유한다 (E2: `opal/skills/opal-pilot-dev/references/pipeline.json` `task_steps`, `opal/skills/opal-pilot-dev-short/references/pipeline.json`, `opal/skills/opal-pilot-project/references/pipeline.json`, `opal/skills/opal-pilot-write-tech/references/pipeline.json`).
- **[사실] F-4** `verify --evidence-check`는 차단 없는 라우터로 항상 exit 0을 반환하며, 어떤 pipeline 행도 이를 호출하지 않는다 (E2: `opal/tools/state-tool/state_tool.py:2993` 및 동 파일 `:6` 서브명령 설명 "차단 없음"; F-3의 pipeline 4파일에 호출 지점 0건).
- **[사실] F-5** `op-task/SKILL.md` 한 파일 안에 호출자 목록이 4개 있고 서로 다르며, 어느 것도 레지스트리와 일치하지 않는다 — frontmatter 3개(`:5`), STEP 5 추천 테이블 5개(`:191-197`), STATE 리마인더 `--skill` 8개(`:217-218`), 레지스트리상 TASK 단계 보유 pilot 9개 (E2: `opal/core/references/opal-skills-registry.json` `groups.opal-pilot`). `opdd`·`oppl`은 네 목록 어디에도 없고, TASK 단계가 없는 `opgc`가 `--skill` 목록에 있다.
- **[사실] F-6** 완료 보고 형식의 산출물 경로에 `{YYMMDD}`가 빠져 저장 경로 규칙과 불일치한다 (E2: `opal/skills/op-task/SKILL.md:232` vs `opal/skills/op-task/SKILL.md:174` 및 `opal/core/references/harness/task-process.md:85`).
- **[사실] F-7** `## 저장 경로`가 H2라 `## 프로세스` 절이 STEP 4에서 종료되고, `### STEP 5`가 저장 경로의 하위 절로 매달린다 (E2: `opal/skills/op-task/SKILL.md:23`, `:171`, `:185`).
- **[사실] F-8** STEP 4가 TASK.md를 작성하는데 그 저장 경로와 헤더 `적용 스킬` 필드는 STEP 5 산출물인 스킬약어를 요구한다 — 문서 순서와 실행 순서가 반대다 (E2: `opal/skills/op-task/SKILL.md:114`, `:179`, `:185`).
- **[사실] F-9** `## 미확정 사항` 섹션은 STEP 2 산문에만 지시되고 STEP 4 템플릿에 없어, 실제 산출물에서 3가지 이름으로 표류했다 (E2: 지시 `opal/skills/op-task/SKILL.md:55` vs 템플릿 `:111-169`; 산출물 `tasks/096-260820-opds-메모리툴-참조무결성-고착해소/TASK.md:92`, `tasks/101-260824-opd-핸드오프-스키마-계약정합/TASK.md:105`, 구 102 TASK.md `## 분석 질문 (ANALYSIS 위임)`).
- **[사실] F-10** STEP 3(기술 스택 사전 판별)의 탐지 대상 6종이 이 저장소 루트에 전부 부재하여, 최근 5건 TASK.md의 `## 기술 스택` 절이 전건 "Markdown" 자답이다 (E1: `for d in tasks/098* tasks/099* tasks/100* tasks/101* tasks/102*; do sed -n '/^## 기술 스택/,/^## /p' "$d/TASK.md"; done` — 스코프: tasks/098~102 5건, 결과 5/5).
- **[사실] F-11** `task-guide.md`가 자체 품질 체크리스트 14항목을 보유해 SKILL.md 작성 체크리스트 13항목과 병존하며, 전자는 `명확화 결과`·`확정된 설계 방향` 두 섹션의 존재를 모르고 SKILL.md가 의무화한 요구사항 4필드(무엇을/어디에/왜/AC)를 언급하지 않는다 (E2: `opal/skills/op-task/references/task-guide.md:147-171`, `:23-45` vs `opal/skills/op-task/SKILL.md:243-261`, `:90-109`).
- **[사실] F-12** `opal-doc-standard` §0.1의 [MUST] 2종이 `op-task/SKILL.md`에 미적용이다 — 규약 1줄 명시 없음, frontmatter `version:` 필드 없음 (E2: `opal/core/references/opal-doc-standard.md:51` vs `opal/skills/op-task/SKILL.md:1-7`).
- **[사실] F-13** 실행 지시문 계열의 변경이력 일괄 정리는 별건 태스크로 예정되어 있다 (E2: `opal/core/references/opal-doc-standard.md:53`).
- **[사실] F-14** 태스크 101의 변경 대상 6파일에 `op-task`는 포함되지 않는다 (E2: `tasks/101-260824-opd-핸드오프-스키마-계약정합/PLAN.md:659`, `:623`).
- **[사실] F-15** 본 태스크 폴더는 TASK 작업 ✅ / TASK 사용자 확인 ⬜ 상태이며 산출물은 `TASK.md` 1건뿐이다 (E1: `~/.opal/tools/state-tool/run.sh show tasks/102-260824-opd-태스크분석-경계재정의 --format md` — 스코프: 해당 태스크 state.json 16행 전체).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `op-task`를 요구사항 도출기로 재정의하고(D-2), TASK.md 독자를 PM·하류 근거 문서로 확정하며(D-3), 판정 2축을 노출·회수 경로에 배선하고(D-4), 자기 정합 결함과 stale 참조 자산을 정리한다 | - | - |
| 범위 | 포함: `op-task/SKILL.md` 재구조화 · `references/task-guide.md`·`personas/service-planner.md` 정리 · 완료 보고 evidence-check 노출 · 하류 회수 통로 신설 · 자기 정합 결함 5종 · doc-standard §0.1 적용(변경이력 제외). 제외: 변경이력 표 일괄 제거(D-8) · 게이트 행 신설(D-4) · 도구 exit 0 계약 변경 · 구 102의 선조회 단 분할·후속 스킬 배선(D-6) | 양식 외부화의 분할 경계, `배경 분석` 섹션 존치 여부, STEP 3 폐지 여부는 ANALYSIS에서 확정 (Q-1·Q-2·Q-3) | `opal/core/references/opal-doc-standard.md:53` |
| 제약 | 배포 경계 준수(`opal/` 소스만 수정, `~/.opal/` 직접 편집 금지) · 하류 회수는 101 CLOSE 이후(D-7) · 플랫폼 분기 금지 · 소유자 결정은 판정 대상 아님(D-5) · 변경이력 행 추가 의무 | - | `opal/core/references/harness/citation-rules.md` §9 (f) / `tasks/101-260824-opd-핸드오프-스키마-계약정합/PLAN.md:659` |
| 완료기준 | `op-task/SKILL.md`에서 호출자 목록 불일치 0건·경로 표기 불일치 0건이고, 요구사항 명확화 절차가 스킬의 최상위 절차로 배치되며, TASK 완료 보고가 evidence-check 결과를 포함하고, 체크리스트가 1개로 단일화된다 | 하류 회수 통로의 구체 형식은 ANALYSIS에서 확정 (Q-4) | - |

## 요구사항

- [ ] **R-1 정체 재정의 — 요구사항 도출기 전환**
  - 무엇을: 요구사항 명확화를 스킬 최상위 절차로 승격하고, 양식 절차(템플릿·저장 경로·STATE 리마인더·완료 보고)를 참조 파일로 외부화
  - 어디에: `opal/skills/op-task/SKILL.md` + 신설 참조 파일(경계는 Q-1)
  - 왜: D-2 / F-1 — 17회 개정이 전부 양식 방향으로 누적되어 명확화 25줄 대 양식 112줄로 무게중심이 역전됐다
  - AC: SKILL.md 본문에서 요구사항 명확화 절차가 첫 번째 STEP으로 배치되고, 외부화 대상 4종이 SKILL.md 본문에 잔존 0건이며 참조 파일에 채택되어 실제로 로드 지시가 걸린다

- [ ] **R-2 독자 확정 — 실측 저장소화 차단**
  - 무엇을: "워커가 TASK.md만으로 컨텍스트를 독립적으로 파악" 문구를 철회하고, D-1 경계 원칙을 SKILL.md 상단에 명시
  - 어디에: `opal/skills/op-task/SKILL.md:83` 및 문서 상단
  - 왜: D-3 / D-1 — 이 한 줄이 TASK.md를 실측 덤프장으로 만드는 근거였다
  - AC: 해당 문구가 0건이고, D-1 경계 원칙 문장이 SKILL.md 상단에 존재하며, `배경 분석` 섹션 관련 지시가 새 경계와 모순되지 않는다

- [ ] **R-3 판정축 노출 — 죽은 도구 되살리기**
  - 무엇을: TASK 완료 보고에 `verify --evidence-check` 결과 1줄을 첨부하도록 지시 추가
  - 어디에: `opal/skills/op-task/SKILL.md` 완료 보고 형식 + `opal/core/references/harness/task-process.md` 완료 보고 블록
  - 왜: D-4 / F-4 — 판정은 이미 존재하나 호출자가 없어 결과가 아무에게도 보이지 않는다
  - AC: 두 파일의 완료 보고 형식에 evidence-check 결과 줄이 존재하고, 차단 지시가 0건이며(비차단 유지), `state_tool.py`의 exit 0 계약이 변경되지 않는다

- [ ] **R-4 하류 회수 통로 — 개선 신호 회수** *(101 CLOSE 이후 착수)*
  - 무엇을: ANALYSIS·PLAN이 TASK.md 결손을 만났을 때 이를 기록하는 통로를 신설
  - 어디에: `opal/skills/op-dev-analysis/SKILL.md`·`opal/skills/op-dev-plan/references/plan-guide.md`(구체 지점은 Q-4)
  - 왜: D-4 / F-3 — 채점되지 않는 근거 문서는 개선 신호를 받을 창구가 없다
  - AC: 회수 기록 지점이 최소 1개 지정되고, 101이 확정한 핸드오프 계약 문안을 훼손하지 않으며(101 변경 6파일의 신 문안 잔존 확인), 착수 시점이 101 CLOSE 이후임이 STATE 저널에 기록된다

- [ ] **R-5 자기 정합 결함 5종 정정**
  - 무엇을: (a) 호출자 목록 4중 불일치를 레지스트리 단일 참조로 교체 (b) 완료 보고 경로 `{YYMMDD}` 보정 (c) `## 저장 경로` 헤딩 레벨 복구 (d) STEP 5를 실행 순서 위치로 재배치 (e) 템플릿에 `## 미확정 사항` 섹션 추가
  - 어디에: `opal/skills/op-task/SKILL.md:5`, `:191-197`, `:217-218`, `:232`, `:171`, `:185`, `:111-169`
  - 왜: F-5·F-6·F-7·F-8·F-9 — 전부 통독 부재의 증거이며, (e)는 템플릿에 없는 규칙이 유도되지 않는다는 관측의 재현이다
  - AC: 파일 내 호출자 열거가 1곳으로 수렴하고 레지스트리와 일치하며, `{YYMMDD}` 누락 0건, `### STEP 5`가 `## 프로세스` 하위이고, 템플릿에 `## 미확정 사항` 섹션이 존재한다

- [ ] **R-6 참조 자산 정리**
  - 무엇을: 품질 체크리스트 2개를 1개로 단일화하고, 구판 요구사항 작성 규칙을 4필드 체계에 정합시키며, 페르소나에 §0.1 판정식을 적용
  - 어디에: `opal/skills/op-task/references/task-guide.md`, `opal/skills/op-task/personas/service-planner.md`
  - 왜: F-2·F-11 — 5개월간 내용 개정 0회로 SKILL.md와 경쟁하는 구판이 남아 있다
  - AC: 품질/작성 체크리스트가 정확히 1개이고, 구 체크리스트 잔존 0건이며, 남은 체크리스트가 `명확화 결과`·`확정된 설계 방향`·4필드를 전부 포함한다

- [ ] **R-7 doc-standard §0.1 적용**
  - 무엇을: 실행 지시문 규약 1줄을 SKILL.md 상단에 명시하고 frontmatter에 `version:` 필드를 추가
  - 어디에: `opal/skills/op-task/SKILL.md:1-7` 및 문서 상단
  - 왜: F-12 / D-8 — 어제 신설된 [MUST] 2종이 미적용이다. 변경이력 표 제거는 별건이므로 제외한다
  - AC: 규약 1줄과 frontmatter `version:`이 존재하고, 변경이력 표는 무변경으로 존치하며 본 태스크 행이 1행 추가된다

## 미확정 사항 (ANALYSIS에서 결정)

- **Q-1 양식 외부화 분할 경계** — 템플릿·저장 경로·STATE 리마인더·완료 보고 중 어디까지를 참조 파일로 내리고, 신설 파일을 1개로 할지 기능별로 나눌지.
- **Q-2 `배경 분석 (대화에서 도출)` 섹션 처리** — D-3에 따라 존재 근거가 약해졌으나, PM 자신의 판단 기록으로서의 가치가 남는지. 존치·축소·삭제 중 택1.
- **Q-3 STEP 3(기술 스택 사전 판별) 처리** — F-10에 따라 이 저장소에서는 no-op이나 타 프로젝트에서는 유효할 수 있다. 폐지·조건부화·존치 중 택1.
- **Q-4 하류 회수 통로의 구체 형식** — 어느 산출물의 어느 절에 어떤 형식으로 기록할지, 101 확정 문안과의 접점은 어디인지.
- **Q-5 태스크 폴더명** — 주제가 바뀌었으므로 `102-260824-opd-태스크분석-경계재정의`를 유지할지 개명할지.

## 제약 조건

- 배포 경계 준수 — `opal/` 소스만 수정하고 `~/.opal/` 배포본을 직접 편집하지 않는다.
- R-4는 태스크 101 CLOSE 이후에만 착수한다 (D-7).
- 게이트 행을 신설하지 않고 `state_tool.py`의 exit 0 계약을 변경하지 않는다 (D-4).
- 소유자 결정의 내용은 판정 대상으로 삼지 않는다 (D-5).
- 변경이력 표 일괄 제거를 수행하지 않는다 (D-8).
- 플랫폼 분기를 스킬 본문에 추가하지 않는다.
- 수정한 스킬·참조 문서에 변경이력 행을 추가한다.

## 기술 스택

- Markdown — 스킬 SKILL.md · 참조 문서 · 페르소나 (주 변경 대상)
- JSON — `opal/core/references/opal-skills-registry.json`(참조 원천), pilot `references/pipeline.json`(읽기 전용)
- Python 3 — `state-tool` (`verify --evidence-check` 호출 지시만, 코드 변경 없음)

> 루트에 `package.json`·`pyproject.toml`·`go.mod`·`Cargo.toml` 없음 — 프레임워크 문서 저장소 (F-10).

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | op-task SKILL | `opal/skills/op-task/SKILL.md` | 주 변경 대상 — R-1·R-2·R-3·R-5·R-7 |
| D-2 | 소스 | op-task 상세 가이드 | `opal/skills/op-task/references/task-guide.md` | R-6 변경 대상 — 경쟁 체크리스트 보유 |
| D-3 | 소스 | op-task 페르소나 | `opal/skills/op-task/personas/service-planner.md` | R-6 변경 대상 — §0.1 판정식 적용 |
| D-4 | 설계 | TASK 공통 프로세스 | `opal/core/references/harness/task-process.md` | R-3 변경 대상 — 완료 보고 블록 소유 |
| D-5 | 설계 | OPAL 문서 표준 | `opal/core/references/opal-doc-standard.md` | R-7 근거 — §0.1 [MUST] 2종 · §7 변경이력 별건 예정 |
| D-6 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | D-5 근거 — §9 (f) 결정 비판정 원칙 |
| D-7 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | R-5 (a) 단일 참조 원천 |
| D-8 | 설계 | pilot 파이프라인 스펙 | `opal/skills/opal-pilot-*/references/pipeline.json` | F-3·F-4 근거 — TASK 게이트 부재 · evidence-check 호출 0건 |
| D-9 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | F-4 근거 — evidence-check 비차단 계약 |
| D-10 | 설계 | 태스크 101 PLAN | `tasks/101-260824-opd-핸드오프-스키마-계약정합/PLAN.md` | D-7 순서 강제 근거 — 변경 6파일에 op-task 미포함 |

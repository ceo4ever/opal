# ANALYSIS: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 작성일: 2026-09-04
> 입력: TASK.md
> 출력: ANALYSIS.md

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| 최초 생성·환경설정은 독립 스킬(opi식 2모드)로 제공 | 해당없음(결정) | - |
| 갱신은 매번 트리거되는 하네스 규정으로 편입 | 해당없음(결정) | - |
| 소비는 2단 절차(1차 code-scan → 2차 grep 전환) | 해당없음(결정) | - |
| 스킬 신설·하네스 개정 통합 태스크 | 해당없음(결정) | - |
| 레거시 backfill 팬아웃·`split`·`opi` Phase 편입 범위 제외 | 해당없음(결정) | - |
| 스킬명 `opal-code-map-builder`(`opcmb`) 확정 | 해당없음(결정) | - |
| 스킬 범위는 `manifest` 구축 중심, `inline`은 종료 분기 | 해당없음(결정) | - |
| 하네스 모드 `agentic` | 해당없음(결정) | - |
| 이 결정은 `opal-harness.md` §8 Lazy 트리거가 EXECUTE 코드 파일 변경으로 한정된 규정 구조와 정합 | 유효(대조 확인) | `opal/core/references/opal-harness.md:255` "적용 시점: EXECUTE 단계에서 코드 파일 변경 시" — TASK.md 서술과 일치 |
| 두 관리 방식(인라인/code-map)은 상호 배타이며 프로젝트당 하나만 선택 가능 | 유효(대조 확인) | `opal/core/references/header-standard.md:191` "두 소스는 모드에 의해 상호 배타이므로 경합·병합 규칙이 존재하지 않는다" |

> `[사실]` 태그 항목 2건 모두 유효 확인. `[결정]` 태그 항목 전건 사실 오류 없음.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §7 2소스 표현·§7.1~7.5 필드·상속 계약 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §갱신 시점 (3단)·§워커 권한 경계·§code-scan 활용 가이드 §빈 결과 폴백 |
| D-3 | 설계 | code-scan.json PM 관리 의무 | `opal/core/references/pm/code-scan-management.md` | §생성 시점·§headerSource 필드 관리·§index.json PM·소유자 관리 의무 |
| D-4 | 설계 | OPAL PM 행동 프로세스 | `opal/core/references/opal-pm.md` | §12 L2 트랙·§13 code-scan 활용 규칙 |
| D-5 | 설계 | PM 디스패치 전 프로세스 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악·워커 컨텍스트 주입 템플릿 |
| D-6 | 설계 | PM 검토 게이트 | `opal/core/references/harness/pm-review-gate.md` | §표준 검토 항목 8·14 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | §Core Stance enforce 원칙 |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | §네이밍·§약어 (Alias) |
| D-9 | 소스 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 약어 SSOT — 실측 29종, `opcmb` 미등록 |
| D-10 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | 3651줄, 15서브명령 |
| D-10b | 소스 | code-map hook | `opal/tools/code-scan/code-map-hook.js` | 조기 이탈 10단 설계 — R-5 폴백 선례 |
| D-11 | 설계 | 모드 라우팅 선례 | `opal/skills/opal-brain/SKILL.md:28-42` | 명시 라우팅(첫 인자) — R-1 `update` 판별 후보 |
| D-12 | 설계 | 2모드 자동 판별 선례 | `opal/skills/opal-project-init/SKILL.md:54-62` | 자산 존재 감지 — R-1 `update` 판별 후보 |
| D-13 | 설계 | OPAL 하네스 | `opal/core/references/opal-harness.md` | §8 stub·§9 도구 표 |
| D-14 | 소스 | PM Gate 정의 SSOT | `opal/skills/opal-pilot-dev/references/pipeline.json` 등 | 회귀 대조(R-6) |
| D-15 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | 기존 `verify --evidence-check` 인용 판정 패턴 — R-4 도구화 후보 |
| D-16 | 소스 | hook 설정 | `opal/core/hooks/claude-hooks.json` | PostToolUse 대상 3종(Bash/Edit|Write|MultiEdit) — R-4 후보 실현 가능성 판정 |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 영역 | 경로 | 역할 | 변경 유형 | 근거(줄번호) |
|------|------|------|------|-------------|
| 스킬 | `opal/skills/opal-code-map-builder/SKILL.md` | 신설 스킬 본체 (init\|update 2모드) | 신규 | - |
| 문서 | `opal/core/references/opal-skills-registry.json` | 약어 SSOT — `opcmb` 항목 추가 | 수정 | `:2-3` (`version`/`updated_at`) |
| 문서 | `docs/CONVENTIONS.md` | 약어 표 사본 갱신 | 수정 | `docs/CONVENTIONS.md:78-87` (독립 스킬 표) |
| 문서 | `opal/core/references/opal-pm.md` | §12 L2 표에 @header 검증 게이트 행 추가 | 수정 | `opal/core/references/opal-pm.md` §12 "L2 하네스 적용 범위" 표 |
| 문서 | `opal/core/references/harness/header-rules.md` | §갱신 시점 표에 L2 완료 시점 행 추가 | 수정 | `opal/core/references/harness/header-rules.md:33-38`(갱신 시점 3단 표) |
| 문서 | `opal/core/references/opal-pm.md` | §13에 2단 소비 절차(1차 code-scan→2차 grep) 명문화 | 수정 | `opal/core/references/opal-pm.md` §13 |
| 문서 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악 — grep 전환 조건 보강 | 수정 | `opal/core/references/pm/dispatch-process.md:126-133`(§code-scan 사전 범위 파악) |
| 문서 | `opal/core/references/harness/pm-review-gate.md` | §표준 검토 항목 14 집행 방식 승격 | 수정 | `opal/core/references/harness/pm-review-gate.md:112-118`(항목 14) |
| 도구 후보 | `opal/tools/code-scan/code-scan.js` | R-4 집행 후보(신규 검증 경로) | 수정(PLAN 결정 필요) | `opal/tools/code-scan/code-scan.js`(3651줄, 15서브명령) |
| 도구 후보 | `opal/tools/state-tool/state_tool.py` | R-4 집행 후보(`mark`/`verify` 게이트 확장) | 수정(PLAN 결정 필요) | `opal/tools/state-tool/state_tool.py:1730`(`cmd_mark`) |
| 문서(참고) | `opal/core/references/opal-harness.md` | §8 stub·§9 도구 표 — opcmb 등재 필요 여부 PLAN 판단 | 수정(PLAN 결정 필요) | `opal/core/references/opal-harness.md:253-309` |

### 1.2 아키텍처 패턴

- 스킬은 `SKILL.md` frontmatter(`name`/`description`/`triggers`/`version`) + `references/` + `personas/` 3분할 구조를 따른다 — `docs/CONVENTIONS.md:91-100`.
- 모드 라우팅은 두 선례가 상이한 방식을 쓴다: `opal-brain`은 **첫 토큰 명시 라우팅**(`opal-brain/SKILL.md:28-42`), `opal-project-init`은 **자산 존재 감지**(`opal-project-init/SKILL.md:54-62`, `.opal/AGENT.md` 존재 여부 + 코드 유무 2단 판별).
- 도구 결정론 집행 원칙 — "도구는 구조를 만들고 워커는 내용을 채운다"(`header-rules.md:11`). code-scan 15서브명령 중 `discover`/`scaffold`/`target`/`validate`/`split`/`init` 6종이 code-map 계열이다(TASK.md 배경 (1)).

### 1.3 의존성 맵

- `opcmb` → `code-scan.js`(`init`/`discover`/`scaffold`/`validate` 서브명령) 직접 호출.
- `code-map-hook.js` → `code-scan.js`의 `decideTarget`/`loadCodeMap`/`loadConfig`/`findProjectRoot`를 `require`(`code-map-hook.js:18-23`) — R-5 폴백 설계가 이미 이 4개 함수 위에서 조기 이탈을 구현하고 있어 재사용 가능한 판정 소스다.
- `header-rules.md`/`opal-pm.md`/`pm-review-gate.md`/`dispatch-process.md`는 서로 포인터로 인용하며 원문 소유권이 분산(`code-scan.js`는 어느 문서도 아닌 코드가 실행 계약의 SSOT).

### 1.4 테스트 현황

- `code-scan` 도메인에 테스트 12파일 존재(PM 사전 code-scan summary 결과, TASK.md 사전 범위 파악 절 인용). 이번 태스크는 문서·스킬 신설이 중심이라 코드 변경분(R-4 도구화 시)에 대한 신규 유닛 테스트 필요 여부는 PLAN이 판단한다.
- `state_tool.py`에 이미 `verify --evidence-check`(`state_tool.py:98` 주석 블록의 "098" 항목)라는 인용 판정 결정론 서브명령이 존재 — 근거 등급 4축(인용 존재·인용 유효·등급 부여·E5 단독 아님) 판정 로직을 재사용 가능.

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 순수 프레임워크 내부 문서·도구 개정, 외부 라이브러리 의존 없음.

## 3. 영향 범위

### 3.1 직접 영향

- §1.1 파일 목록 전건.

### 3.2 간접 영향

- `opal-project-init`(`opi`)의 초기화·최신화 플로우 — 이번 범위는 `opi`에 code-map Phase를 편입하지 않으므로(TASK.md 확정 방향) `opi`는 무변경.
- 기존 pilot 3종(`opd`/`opds`/`opp`)의 `pipeline.json` — R-2·R-3은 산문 규정 문서만 개정하므로 직접 영향 없음. R-4 집행 지점이 **신규 게이트 행**(TEST-SCENARIO의 `scenario_gate` 선례처럼) 신설을 채택할 경우에만 `pipeline.json` 행이 늘어난다 — §7 Q6에서 상세.
- `opal-be-agent`/`opal-plan-agent` AGENT.md의 "적극 활용한다" 권고 문구 — R-4가 도구 판정으로 승격되면 이 문구들의 위상(권고→강제 경유)이 바뀔 수 있으나, 문면 자체 개정은 이번 범위(D-6/코드 도구)에 명시되지 않아 PLAN 판단 대상.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [x] 설정/환경변수 변경 — 없음(이 레포 `.opal/code-scan.json`은 무변경 대상, R-5는 폴백 "무영향" 검증용)
- [ ] 빌드/배포 파이프라인 변경 — install-mac.sh 배포 대상에 신설 스킬 폴더 자동 포함(기존 스킬 배포 규칙과 동형, 별도 스크립트 수정 불요 — PLAN에서 실측 확인 권고)

## 4. 핵심 발견 사항

1. **모드 판별 선례 2종은 판별 신호가 다르다** — `opbr`은 사용자 발화 첫 토큰(비대화형 CLI 스타일), `opi`는 파일시스템 자산 존재(`.opal/AGENT.md`). `opcmb`가 다루는 `.opal/code-map/index.json`은 `opi`의 `.opal/AGENT.md`와 같은 "프로젝트 자산 파일"이므로 자산 존재 감지 쪽이 구조적으로 더 가깝다.
2. **R-4의 핵심 난점은 실측으로 확인됨** — 디스패치 프롬프트는 어떤 파일에도 저장되지 않는다. `claude-hooks.json`(`opal/core/hooks/claude-hooks.json`)의 PostToolUse matcher는 `Bash`, `Edit|Write|MultiEdit` 2종뿐이며 Task(서브에이전트 디스패치) 도구를 겨냥한 hook은 현재 0건이다. 반면 PLAN.md Step 본문은 파일로 영속되고 디스패치 시 "그대로" 워커에 전달되는 것이 이미 규정된 경로다(`dispatch-process.md` Step 6 실행 라우팅) — 증거를 얹을 안정적인 자리는 PLAN.md Step 본문이지 디스패치 프롬프트 자체가 아니다.
3. **L2 완료 시점 감지는 `changed_files`라는 객관 신호가 이미 존재** — L2는 STATE.md/파이프라인 미적용이라 `state-tool`이 관측하지 못하지만, PM이 직접 수정한 파일 목록은 `git status`/`git diff --name-only`로 항상 재구성 가능하다(git 자체가 SSOT). 이 신호를 CLOSE류 게이트가 아니라 **PM의 다음 발화 시점 자기 점검**에 연결하는 것이 유일한 현실적 집행 지점이다.
4. **`code-map-hook.js`의 조기 이탈 설계가 R-5 폴백의 직접 재사용 가능한 선례다** — `headerSource !== 'manifest'`(⑤단) 또는 `index.json` 부재(⑥단)에서 무출력 exit 0을 이미 계약으로 못박고 있다(`code-map-hook.js:115-132`). 이 레포는 정확히 이 상태(`inline` + code-map 부재)이므로, R-2·R-4가 신설할 검증 로직도 동일 조기 이탈 순서(모드 게이트 → 자산 존재 게이트)를 앞단에 두면 오탐 0건이 구조적으로 보장된다.
5. **`state_tool.py`에 인용 판정 결정론 로직이 이미 존재한다** — `verify --evidence-check`(Task 098)는 표/불릿에서 인용 4형식을 파싱해 등급을 매기는 기능을 이미 구현하고 있다(`state_tool.py` 098/100 변경이력). R-4가 "PLAN.md Step 본문에 code-scan 결과 인용 여부"를 판정하려면 이 로직을 확장하는 편이 신규 파서를 작성하는 것보다 재사용 비용이 낮다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| L2 게이트와 표 원칙 충돌 | `opal-pm.md` §12 L2 표는 "Gate ❌ 미적용"이 명시 원칙이다. 새 검증 게이트 행을 그 표 안에 추가하면 문면상 자기모순(L2=Gate 없음 vs L2 전용 새 Gate)이 생긴다 | 중 | `opal/core/references/opal-pm.md` §12 "L2 하네스 적용 범위" 표 "Gate ❌ 미적용" |
| PreToolUse Task hook 부재 | 디스패치 프롬프트를 가로챌 hook 인프라가 현재 0건 — R-4를 hook 방식으로 구현하려면 신규 matcher(`Task`) 설계·검증이 필요하고, 이는 Claude Code 외 플랫폼(Cursor/Gemini)에서 동등 hook이 없을 수 있어 플랫폼 분기 격리 원칙(`docs/CONVENTIONS.md §플랫폼 분기 격리`)과 충돌 여지 | 중 | `opal/core/hooks/claude-hooks.json` (matcher 2종만 존재) |
| 변경이력 규약과 메모리 기록의 충돌 | `.opal/AGENT.md` §금지사항이 "변경이력 누락 금지"를 의무화하나, 프로젝트 메모리에 변경이력 표·버전표기 제거 A안(2026-08-14 확정, 미실행)이 남아있다. 실측 결과 개정 대상 6문서 전건에 "## 변경이력" 표가 실재한다(§7 Q5) — 미실행 A안과 무관하게 현행 규약은 행 추가를 요구한다 | 저 | `.opal/AGENT.md:62` "변경이력 누락 금지" |
| pipeline.json 행 증설 시 회귀 범위 확대 | R-4가 신규 PM Gate 행(TEST-SCENARIO `scenario_gate` 선례 방식)을 채택하면 opd/opds/opp `task_steps` 행 수가 바뀌어 R-6 AC(a) "행 수·key 동일" 조건과 정면 충돌한다 — PLAN은 "기존 행의 gate.checklist 확장" 대 "신규 행 추가" 중 하나를 명시적으로 택해야 한다 | 중 | `opal/skills/opal-pilot-dev/references/pipeline.json` 등 §7 Q6 |
| 레지스트리 약어 중복 검증 | `opcmb`는 현재 29종 등록 약어 어디에도 없음(실측 완료) — 등록 시 충돌 리스크는 낮으나 PLAN 단계에서 재확인 필요 | 저 | `opal/core/references/opal-skills-registry.json`(29종 alias 실측, `opcmb` 미포함) |

## 6. 기술 컨텍스트

### 6.1 프로젝트 SSOT

전체 기술 스택은 `docs/PROJECT.md`를 참조한다. 이 섹션은 재기재하지 않는다.

### 6.2 이번 태스크 델타

변경 없음(SSOT 그대로) — Markdown/Node.js/Python 기존 스택 내에서 문서·스킬만 추가.

### 6.3 추천 스킬

| 스킬 | 용도 |
|------|------|
| opal-skill-creator(osc) | 신설 스킬 SKILL.md frontmatter·구조 표준화 참고(직접 호출 대상 아님, 패턴 참고용) |

### 6.4 추천 MCP

해당 없음 — 외부 라이브러리 조사 불요.

## 7. 지정 분석 질문 Q1~Q7 답변

- **Q1** `update` 모드 판별 방식 → **자산 존재 감지((a) `opi` 방식)를 권고한다.** 근거: `opbr`(D-11, `opal-brain/SKILL.md:28-42`)은 지식 위키를 다루는 **동사형 CLI 라우터**(init/ingest/query/lint)로 상태가 없는 반복 조작이 대상이지만, `opi`(D-12, `opal-project-init/SKILL.md:54-62`)는 `opcmb`처럼 **"프로젝트 1회성 자산의 존재 여부"**로 초기화/최신화를 가른다. `opcmb`가 다루는 `.opal/code-map/index.json`(`manifest` 모드) 또는 `.opal/code-scan.json`의 `headerSource`(공통) 존재 여부는 `.opal/AGENT.md` 존재 여부와 동일한 성격의 판별 신호다. `status: draft|reviewed`(`header-standard.md:206`)는 판별에 **부적합** — 이는 소유자 리뷰 완료 여부를 나타내는 하위 상태이지 init/update 자체의 판별 축이 아니다(초안 상태에서도 update 흐름이 필요할 수 있음).
- **Q2** R-4 소비 집행 지점 → 후보 3개 비교 결과, **PLAN.md Step 본문 인용을 판정 대상으로 하는 도구 확장**(state-tool 유사 서브명령 신설 또는 `code-scan` 자체 검증 서브명령)이 가장 현실적이다.
  1. *PreToolUse Task hook*: (i) 증거 = 디스패치 프롬프트 텍스트 (ii) 구현 가능성 낮음 — 현재 hook matcher가 `Task` 도구를 겨냥한 사례 0건(`claude-hooks.json`)이며 플랫폼 독립성 원칙과 충돌 여지 (iii) 오탐 위험 높음 — 정규식 매칭으로 "실질 인용"과 "단순 언급"을 구분 못함.
  2. *state.json 저널 필드*: (i) 증거 = PM이 수동 기재하는 필드 (ii) 구현 가능성 높음(스키마 필드 추가는 경량) (iii) 오탐 위험 높음 — PM 자기 기재이므로 자기판정 문제가 그대로 이전됨(형태만 도구화, 실질은 여전히 prose 신뢰).
  3. *PLAN.md Step 본문 인용 검증*: (i) 증거 = 파일로 영속되는 PLAN.md Step 텍스트, `dispatch-process.md` Step 6에 따라 디스패치 프롬프트에 "그대로" 전달됨이 이미 규정된 경로 (ii) 구현 가능성 높음 — `state_tool.py`의 `verify --evidence-check`(098/100)가 표/불릿 인용 파싱 로직을 이미 보유해 확장 비용이 낮음 (iii) 오탐 위험 낮음 — 파일 근거이므로 재현 가능하고, PM Gate 항목 14의 기존 판정 기준(도메인/레이어/depends/exports 또는 신규 서브명령 필드 인용)을 그대로 재사용 가능. **PLAN 결정 필요**: 신설 서브명령을 `state-tool`(파이프라인 게이트 통합)과 `code-scan`(자기 서브명령) 중 어디에 둘지.
- **Q3** R-2 L2 게이트 → **(a) code-map 예외 1행 추가**를 권고한다. 근거: D-4 §12 표의 "Gate ❌ 미적용" 원칙은 **태스크 파이프라인 게이트**(State Gate/PM Gate) 전체를 가리키는 것이지 @header 갱신처럼 `changed_files`라는 객관 입력만으로 결정론 판정 가능한 별개 축을 배제하는 취지가 아니다(표 개정보다 예외절 추가가 원칙과 실무 요구를 모두 보존). **핵심 난점 실측**: L2는 `state-tool` 미경유이므로 `state.json`에 행이 생기지 않지만, PM이 손댄 파일은 `git status --porcelain`/`git diff --name-only`로 항상 재구성된다 — 완료 시점 감지는 **git diff 기반**이 유일한 현실적 신호원이다(PostToolUse hook으로 매 Edit마다 검사하는 방식은 `code-map-hook.js`가 이미 하고 있으므로 L2 전용 신규 장치는 불요할 수 있다 — PLAN에서 기존 hook 재사용 여부 판단 필요).
- **Q4** R-5 미보급 폴백 → `code-map-hook.js`의 조기 이탈 10단(`code-map-hook.js:87-165`)이 **직접 재사용 가능한 선례**다. ⑤단(`mode !== 'inline' && mode !== 'manifest'` 또는 `mode === 'inline'` → 무출력 exit 0, `:126-128`)과 ⑥단(`index.json` 부재 → 무출력 exit 0, `:131-132`)이 정확히 이 레포의 상태(`headerSource: inline` + code-map 부재)를 조용히 통과시키는 계약을 이미 구현하고 있다. R-2·R-4가 신설할 검증 로직도 동일 순서(모드 게이트 → 자산 존재 게이트가 실제 로직보다 선행)로 배치하면 오탐 0건이 설계로 보장된다. **[MUST]** 두 게이트의 순서를 바꾸면 안 된다는 교훈도 함께 재사용해야 한다 — `code-map-hook.js:121-124` 주석: "이 게이트는 ⑥ code-map 로딩보다 반드시 위에 있어야 한다".
- **Q5** 변경이력 규약 충돌 → 실측 결과 개정 대상 6문서(D-2·D-3·D-4·D-5·D-6·D-13) 중 **D-13(`opal-harness.md`)을 제외한 5문서 전건에 "## 변경이력" 표가 실재하며 지속 갱신 중**이다(`header-rules.md` v1.8까지, `code-scan-management.md` v1.5까지, `opal-pm.md`·`dispatch-process.md` v1.9까지, `pm-review-gate.md` v1.8까지 — 각 파일 말미 변경이력 표 실측). `opal-harness.md`도 §변경이력 절이 존재한다(`opal-harness.md:321` "## 변경이력"). 즉 메모리에 기록된 "A안(변경이력 표·버전표기 제거) 확정, 미실행" 상태와 무관하게, **현행 6문서 전건이 여전히 표 형식을 유지 중**이므로 이번 태스크는 기존 관행을 따라 행을 추가한다 — A안 집행은 이 태스크의 범위가 아니며(TASK.md 범위 제외 목록에 없으나 별도 태스크 없이 편입하면 스코프 크리프), PLAN에서 별도 결정 필요 항목으로만 표기한다.
- **Q6** 회귀 영향 범위 → R-2·R-3(문서만 개정)은 `pipeline.json`에 영향 없음(실측: `opal-pm.md`/`header-rules.md`/`dispatch-process.md` 어느 것도 `task_steps` 정의 소스가 아님). **R-4가 신규 게이트 행을 pipeline.json에 추가하는 방식을 채택하면** opd(16행)·opds(11행)·opp(9행) 전체의 `task_steps` 행 수가 바뀌어 R-6 AC(a)("행 수·key 개정 전후 동일")와 직접 충돌한다 — 이 경우 R-6은 "무변경"이 아니라 "의도된 증가 후 무결성 검증"으로 재정의해야 한다. PLAN은 (i) 기존 `execute.pm_gate`류 행의 `gate.checklist`에 문구만 추가(행 수 불변, R-6 그대로 충족) 대 (ii) TEST-SCENARIO `scenario_gate` 선례처럼 신규 행 추가(행 수 증가, R-6 AC 재정의 필요) 중 하나를 명시적으로 택해야 한다.
- **Q7** `opcmb` 서브명령 시퀀스 → **`manifest` 모드**: `code-scan init --header-source manifest --write` (headerSource 확정) → `code-scan discover [--out|--dry-run]`(초안 생성, `status: draft`) → **소유자 리뷰 게이트**(스킬 STEP에서 "소유자 확인 필요" 산출물 요약을 제시하고 승인 대기 — TASK.md 확정 모드가 `agentic`이므로 PLAN까지는 PM 대행이되 이 리뷰는 자산 자체의 신뢰도에 직결되므로 명시적 확인 문구를 스킬이 요구) → `status: reviewed` 전환(PM 또는 소유자) → `code-scan scaffold`(매니페스트 골격 생성) → 완료 보고. **`inline` 모드**: `code-scan init --header-source inline --write` → 종료 분기, `code-scan missing` 안내 반환(이후 갱신은 §갱신 시점 3단이 처리하므로 `opcmb`가 추가로 할 일이 없음이 확정 방향에 이미 명시됨). D-3 §index.json PM·소유자 관리 의무의 3단 흐름(discover→리뷰→reviewed)은 스킬 STEP 2~4에 그대로 매핑 가능하며, 소유자 리뷰 게이트는 **다른 pilot의 "사용자 확인" 행과 동일한 표현 방식**(스킬 산출물 제시 후 승인 대기)으로 표현하는 것이 기존 관용구와 정합적이다(PLAN에서 구체 STEP 번호·산출물명 확정).

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| `update` 판별 방식 | 자산 존재 감지(opi 방식) — `.opal/code-scan.json`(공통) + `.opal/code-map/index.json`(manifest 모드) 존재 여부 | §7 Q1 |
| `status` 필드 용도 | init/update 판별에 미사용 — 소유자 리뷰 완료 표시 전용 | §7 Q1, `header-standard.md:206` |
| R-4 집행 지점 1순위 후보 | PLAN.md Step 본문 인용 검증(파일 근거) — `state_tool.py` `verify --evidence-check`(098/100) 로직 확장 재사용 | §7 Q2 |
| R-5 폴백 설계 원형 | `code-map-hook.js` 조기 이탈 ⑤(모드 게이트)→⑥(자산 존재 게이트) 순서를 그대로 재사용 | §7 Q4, `code-map-hook.js:115-132` |
| Q5 변경이력 처리 | 6문서 전건 현행 표 형식 유지 중 — 이번 태스크는 행 추가로 진행, A안 집행은 별도 판단 | §7 Q5 |
| 레지스트리 실측값 | alias 29종, `opcmb` 미등록(중복 없음) | `opal-skills-registry.json` 실측 |
| pipeline.json 행 수 실측 | opd 16 / opds 11 / opp 9 (R-6 대조 기준값) | §7 Q6 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| R-4 신설 서브명령 소속 | `state-tool` 확장 vs `code-scan` 자체 서브명령 — 파이프라인 게이트 통합 편의 vs 도구 응집도 | §7 Q2 |
| R-2 L2 게이트 표현 방식 | opal-pm.md §12 표에 "예외 1행" 형태로 추가할지, 별도 각주로 뺄지 문면 확정 | §7 Q3 |
| R-4 pipeline.json 영향 방식 | 기존 게이트 행 `checklist` 확장(행 수 불변) vs 신규 게이트 행 추가(행 수 증가, R-6 AC 재정의) | §7 Q6 |
| 소유자 리뷰 게이트 표현 | opcmb STEP에서 "사용자 확인" 행 관용구를 그대로 쓸지, code-map 전용 문구를 신설할지 | §7 Q7 |

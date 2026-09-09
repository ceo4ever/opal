# ANALYSIS: opal-skill-wizard 신설 — 프로젝트 적합 스킬 제안 + 프로젝트 스코프 설치

> 작성일: 2026-09-03
> 입력: TASK.md
> 출력: ANALYSIS.md

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 제안 대상은 커뮤니티 스킬(skills.sh)로 한정, 미발견 시 opal-skill-creator 위임 | 해당없음(결정) | - |
| [결정] 설치 대상은 프로젝트 스코프를 신설(전역은 opal-skill-manager 유지) | 해당없음(결정) | - |
| [결정] wizard는 opal-skill-manager를 호출하지 않는다 | 해당없음(결정) | - |
| [결정] 기존 프로젝트 분석은 `docs/PROJECT.md` 재사용 + 결측만 인터뷰 | 해당없음(결정) | - |
| [결정] 설치 전 사전 검사는 공용 도구 `skill-registry.js scan-risk` 직접 호출 | 해당없음(결정) | 도구 실존 확인(`opal/tools/skill-registry/skill-registry.js:912`, `:726-845`) — 결정과 상충 없음 |
| [결정] 프로젝트 설치 이력 registry 신설 | 해당없음(결정) | - |
| [결정] 발동 경로는 OPAL 레지스트리 + `//` 커맨드, 플랫폼 네이티브 디렉토리 미사용 | 해당없음(결정) | - |
| [결정] 착수 트랙은 `//opd --agentic` (`opds`에서 승격) | 해당없음(결정) | 승격 근거: 요구사항 11건 > 8건, `opal/skills/opal-pilot-dev-short/SKILL.md` §조기 에스컬레이션 |
| [사실] 이 방식의 대가는 플랫폼 네이티브 description 자동 트리거를 쓸 수 없다는 점 — 발동은 알투(PM)의 레지스트리 해석 경로 한정 | 유효(대조 확인) | `opal/core/references/harness/skill-commands.md:11-24`(match 기반 라우팅) + `scripts/install-mac.sh:1723-1751`(네이티브 skills/ 디렉토리 레거시 지정·수동 삭제 권고) |

> TASK.md `## 확정된 설계 방향` 8개 `[결정]` 항목 + 1개 `[사실]` 항목 전건 판정 완료. `사실오류` 강등 0건.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 전역 설치 6단 흐름·설치 경로 규칙·§6 미설치 자동설치 라우팅의 현행 기준 |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 레지스트리 로더·경로 해석·match/get/list/validate·scan-risk 현행 구현 전문 |
| D-3 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | `//` 커맨드 해석·미설치 라우팅 규칙 |
| D-4 | 설계 | opal-project-init SKILL.md | `opal/skills/opal-project-init/SKILL.md` | 2모드(초기화/최신화) 판별·인터뷰 골격, PROJECT.md 표준 섹션 정의 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 플랫폼 네이티브 스킬 경로 폐기 안내(레거시 정리 notice) + 프로젝트 로컬 `.opal/` 무접촉 실측 |
| D-6 | 설계 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 스킬 등재 스키마·전건 alias 29종 |
| D-7 | 소스 | dashboard skill_adapter.py | `dashboard/backend/adapters/skill_adapter.py` | `skill-registry list` 소비 계약(하류 회귀 표면) |
| D-8 | 설계 | opal-skill-creator SKILL.md | `opal/skills/opal-skill-creator/SKILL.md` | 위임 대상 스킬의 진입 분기·Phase 1 입력 계약 |
| D-9 | 소스 | 기존 테스트 4파일 | `opal/tools/skill-registry/tests/*.js` | 실행 방법·HOME/cwd 오버라이드 fixture 격리 패턴 |
| D-10 | 설계 | analysis-core.md | `opal/core/references/harness/analysis-core.md` | §5 관련 파일 맵 축(프레임워크 문서·스킬 태스크 7축) |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷·근거 등급·확정 입력 판정 규칙 |
| D-12 | 설계 | docs/ARCHITECTURE.md | `docs/ARCHITECTURE.md` | §커뮤니티 스킬(187-198) — 레지스트리 이원 구조 기술 위치 확인 |
| D-13 | 설계 | 태스크 105 산출물 | `tasks/105-260902-opds-스킬-탐색설치-개선/PLAN.md`, `TEST-SCENARIO.md` | `list` JSON 배열 계약 회귀 위험(H-1) 선례 — 동일 파일 재작업 시 재사용 |
| D-14 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | `.opal/` 프로젝트 로컬 자산 규약, 문서 레지스트리 |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

> 축: `opal/core/references/harness/analysis-core.md` §5 "프레임워크 문서·스킬 태스크 축"(스킬/가이드/오케스트레이터/에이전트/문서/환경/배치) 적용. 이 축 목록에 "도구(tool)"가 없어 `skill-registry.js`·신규 테스트 파일에 라벨 공백이 발생함 — H-1로 하단에 기재.

| 영역 | 경로 | 역할 | 변경 유형 | 근거(줄번호) |
|------|------|------|------|-------------|
| 스킬 | `opal/skills/opal-skill-wizard/SKILL.md` | 신설 대상 — 2모드 제안·승인·설치 흐름 정의 | 신규 | - |
| 도구(축 공백, H-1) | `opal/tools/skill-registry/skill-registry.js` | `loadAllSkills()` 병합 확장(R-5), 프로젝트 스킬 경로 해석(R-6) | 수정 | `129-147`(loadAllSkills), `100-109`(resolveCommunitySkillPath), `255-323`(matchCommand), `327-340`(getCommand) |
| 가이드 | `opal/core/references/harness/skill-commands.md` | 프로젝트 스코프 미설치 라우팅 분기 추가(R-9) | 수정 | `11-24` |
| 문서 | `opal/core/references/opal-skills-registry.json` | wizard 등재 + 약어 배정(R-10) | 수정 | `groups.opal` 배열 말미(597-778), `changelog` 배열 말미(800-905) |
| 문서 | `docs/ARCHITECTURE.md` | 프로젝트 registry 스키마·이원 구조 확장 기술(R-7) | 수정 | `187-198`(§커뮤니티 스킬 인접 절) |
| 도구(축 공백, H-1) | `opal/tools/skill-registry/tests/*.js`(신규 파일) | 프로젝트 registry 유·무·파손 3케이스 회귀 테스트(R-8) | 신규 | - |

### 1.2 아키텍처 패턴

- `skill-registry.js`는 순수 함수 CLI 단일 파일이며 클래스 없이 `loadJsonFile → flattenGroups → merge` 파이프라인으로 3소스(main/community/user)를 병합한다(`:129-147`).
- `_source` 마커(`'main'`/`'community'`)가 스킬 항목마다 부착되어 `isCommunitySkill()`(`:112-114`) 판정과 `listCommand`의 `--group=community` 필터(`:349-351`)의 유일한 판별축이다.
- 경로 해석은 스킬 유형별로 분화되어 있다 — main 스킬은 `resolveFirstPath()`(정적 `paths` 배열에서 존재하는 첫 경로 선택, `:229-253`), community 스킬은 `resolveCommunitySkillPath()`(vendor 중첩 우선 → flat 폴백 → null, `:100-109`)로 완전히 다른 함수가 담당한다.
- `getReferencesDir()`(`:80-92`)는 이미 "1순위 cwd 소스 레이아웃 → 2순위 `~/.opal/` 배포 → 3순위 `__dirname` 기준 소스" 3단 폴백을 구현하고 있어, cwd 기반 판별의 선례가 같은 파일 안에 존재한다.
- `getCommand()`(`:327-340`)는 다른 서브커맨드와 달리 **경로 동적 계산을 전혀 하지 않는다** — `{_group, _source, ...rest}` 구조분해로 raw 필드를 그대로 반환할 뿐이다. community 스킬이어도 `resolveCommunitySkillPath()`를 호출하지 않는다.

### 1.3 의존성 맵

- `main()`(CLI 라우터, `:849-931`) → `matchCommand`/`getCommand`/`listCommand`/`validate`/`migrateCommand`/`parseSourceRepo`/`scanRiskCommand` 7개 서브커맨드 함수 → 전부 `loadAllSkills()`(`:129-147`)를 공유 소비한다. `loadAllSkills()` 1곳을 확장하면 7개 서브커맨드 전체에 파급된다.
- 외부 소비자는 3개 확인됨: (1) `dashboard/backend/adapters/skill_adapter.py:47`가 `list` 무인자 호출을 `run_tool`로 실행하고 반환 타입만 검사(`isinstance(result, list)` 분기 우선, `:53-54`), (2) `opal/skills/opal-skill-manager/SKILL.md`가 `match`/`list`를 다수 호출, (3) `opal/skills/opal-help/SKILL.md`가 `list`/`get`/`match`를 호출. `get` 서브커맨드를 직접 소비하는 외부 코드(스크립트/테스트)는 발견되지 않았다.
- `opal/core/references/harness/skill-commands.md:23-24`가 `//` 커맨드 라우팅에서 `match` 응답의 `installed` 필드에 의존해 `opal-skill-manager/SKILL.md §6`으로 분기시킨다 — 프로젝트 스코프 도입 시 이 분기 로직이 확장 대상이다(R-9).

### 1.4 테스트 현황

- 테스트 프레임워크: Node.js 내장 `node:test`(각 파일이 `test('...', () => {...})` + `node <파일>` 직접 실행 방식, 별도 러너 설정 없음).
- 기존 4개 파일 전건 존재 확인(`opal/tools/skill-registry/tests/`): `test-match.js`(21166B), `test-migrate.js`(20113B), `test-scan-risk.js`(37495B, 태스크 105 신규), `test-validate.js`(14773B).
- **실행 결과** — cwd `/Volumes/Data/AiStudio/workspace/opal`(리포지토리 루트) 스코프, 개별 파일 단위 `node <경로>` 직접 실행(E1):

| 파일 | 명령 | pass | fail |
|------|------|------|------|
| test-match.js | `node opal/tools/skill-registry/tests/test-match.js` | 11 | 0 |
| test-validate.js | `node opal/tools/skill-registry/tests/test-validate.js` | 5 | 0 |
| test-migrate.js | `node opal/tools/skill-registry/tests/test-migrate.js` | 9 | 0 |
| test-scan-risk.js | `node opal/tools/skill-registry/tests/test-scan-risk.js` | 16 | 0 |
| **합계** | 4개 파일 개별 실행 | **41** | **0** |

- 격리 방식: mock/monkeypatch 없이 실 fs 위 합성 fixture + `spawnSync`로 실제 CLI를 별도 프로세스로 실행한다. `os.tmpdir()`에 `mkdtempSync`로 임시 디렉토리를 만들고, `env.HOME`을 오버라이드해 `os.homedir()`가 fixture 디렉토리를 가리키게 하는 방식(`test-validate.js:93-95`, `test-match.js:126-135`)과, `spawnSync`의 `cwd` 옵션으로 프로세스 작업 디렉토리를 fixture 루트로 지정하는 방식(`test-match.js:135`)을 併用한다.
- `get` 서브커맨드 전용 테스트는 4개 파일 어디에도 없다(grep 0건) — 회귀 안전망 부재.

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 이번 태스크는 외부 라이브러리·API 신규 도입이 없다(순수 내부 Node.js CommonJS 확장 + Markdown 스킬 신설).

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/skill-registry/skill-registry.js` — `loadAllSkills()`·경로 해석 함수·`getCommand()` 확장
- `opal/skills/opal-skill-wizard/SKILL.md` — 신설
- `opal/core/references/harness/skill-commands.md` — 미설치 라우팅 절
- `opal/core/references/opal-skills-registry.json` — wizard 등재
- `docs/ARCHITECTURE.md` — 레지스트리 이원→다원 구조 기술

### 3.2 간접 영향

- `dashboard/backend/adapters/skill_adapter.py` + `dashboard/backend/tests/test_adapters.py::test_skill_adapter_list` — `list` 출력이 여전히 JSON 배열이어야 한다는 단정(`isinstance(result, list)`, `test_adapters.py:101`)에 의존. 태스크 105 PLAN이 동일 위험을 H-1로 이미 문서화했다(`tasks/105-260902-opds-스킬-탐색설치-개선/PLAN.md:77`).
- `opal/skills/opal-skill-manager/SKILL.md`·`opal/skills/opal-help/SKILL.md` — `match`/`get`/`list` 응답 필드에 의존하는 문서 절차. 필드 additive 확장은 안전하나 기존 필드 의미 변경은 두 문서 절차를 깨뜨린다.
- `opal/core/references/harness/skill-commands.md` 소비자(전 pilot의 `//` 커맨드 해석 경로) — `installed`/`ambiguous` 필드 의미가 프로젝트 스코프 도입 후에도 유지되어야 한다.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경
- [x] 설정/환경변수 변경 — 신규 프로젝트 registry 파일(`.opal/` 하위, 경로 미확정 — PLAN 결정 필요)
- [ ] 빌드/배포 파이프라인 변경

## 4. 핵심 발견 사항

1. `loadAllSkills()`(`skill-registry.js:129-147`)는 이미 3소스(main/community/user)를 `_source` 마커 + `flattenGroups()` 공용 함수로 병합하는 구조이므로, 프로젝트 registry를 4번째 소스로 additive 병합하는 확장은 기존 구조를 재사용할 수 있다 — 신규 병합 알고리즘 설계가 필요 없다.
2. `getReferencesDir()`(`:80-92`)가 이미 "cwd 우선 → HOME 배포 → `__dirname` 소스" 폴백 순서를 구현하고 있어, cwd 기반 프로젝트 루트 판별에 대한 선례가 같은 파일에 이미 존재한다. 단 이 함수는 "OPAL 프레임워크 자체의 소스 레이아웃"을 찾는 용도이지 "임의 위치에서 실행된 프로젝트의 루트"를 찾는 용도가 아니므로 그대로 재사용은 불가하고 별도 판별 로직이 필요하다.
3. `getCommand()`(`:327-340`)는 현재 어떤 스킬 유형에도 동적 경로 계산을 하지 않는 유일한 서브커맨드다. TASK.md R-6 AC("get 응답의 경로 필드로 반환")를 충족하려면 `getCommand()`에 신규 로직을 추가해야 하며, 이는 기존 "raw passthrough" 계약을 변경하는 것이므로 PLAN에서 명시적으로 다뤄야 한다.
4. 태스크 105가 동일 파일(`skill-registry.js`)에 이미 `scan-risk` 서브커맨드를 추가했고(커밋 `69f5ce1`), 114 착수 시점에는 **완전히 커밋·CLOSE 완료 상태**다 — TASK.md 작성 시점(같은 날 00:xx경)의 미커밋 관측은 그 사이 105가 EXECUTE~CLOSE까지 진행되며 stale이 되었다(§5 리스크 H-2 무효화 근거로 하단 Q5에 기록).
5. `dashboard/backend/adapters/skill_adapter.py`의 `list_skills()`는 필드 단위로 파싱하지 않고 최상위 반환 타입(list/dict/str)만 분기하므로(`:53-75`), `list` 출력 배열 안에 새 필드(예: project 스킬의 `_source` 유래 표시)가 추가되는 것은 이 소비자에 회귀를 일으키지 않는다 — 회귀 표면은 "배열이 아닌 형태로 바뀌는 경우"에 한정된다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| H-1 | `analysis-core.md` §5 "프레임워크 문서·스킬 태스크" 7축(스킬/가이드/오케스트레이터/에이전트/문서/환경/배치)에 "도구(CLI 코드)" 라벨이 없다 — `skill-registry.js`·신규 테스트 파일 분류 시 라벨 공백 발생 | 낮음(문서 정합성) | `opal/core/references/harness/analysis-core.md §5` |
| H-2 | `getCommand()`가 community 스킬에도 동적 경로 계산을 하지 않는 "raw passthrough" 구조라, R-6 AC(get 응답 경로 필드 반환)를 만족하려면 기존 계약을 변경해야 한다 — 회귀 범위 파악 필요(현재 `get` 전용 테스트 0건이라 계약 변경의 안전망이 없음) | 중간 | `opal/tools/skill-registry/skill-registry.js:327-340` |
| H-3 | `get` 서브커맨드는 4개 기존 테스트 파일 어디에도 커버되지 않는다(grep 0건) — R-6 구현 후 회귀를 잡아낼 기존 테스트가 없어, R-8 신규 테스트가 `get` 자체도 커버해야 한다 | 중간 | `opal/tools/skill-registry/tests/*.js`(grep 결과 0건) |
| H-4 | 프로젝트 registry 파일의 정확한 경로·파일명이 TASK.md에서 "PLAN에서 결정"으로 미확정 남아 있고, 후보에 따라 실제 설치 스킬 파일 저장 위치(`.opal/skills-registry.json` 단일 파일 vs `.opal/community-skills/` 서브구조)와 `resolveCommunitySkillPath()` 유사 함수 시그니처가 달라진다 | 중간 | TASK.md 명확화 결과 표(범위 열 미확정 항목) |
| H-5 | 프로젝트 루트 판별을 cwd 기준으로 할 경우, skill-registry.js가 프로젝트 하위 디렉토리(예: `dashboard/backend/`)에서 호출되면 cwd≠프로젝트 루트라 프로젝트 registry를 찾지 못한다. `getReferencesDir()`도 `process.cwd()` 단일 지점만 검사하고 상위 디렉토리 탐색(예: `.git`류 walk-up)은 하지 않아(`:83-84`) 동일 한계가 그대로 상속될 위험 | 중간 | `opal/tools/skill-registry/skill-registry.js:80-92` |
| H-6 | 전역(user-registry)과 프로젝트 registry에 동일 `name`이 있을 때 우선순위가 TASK.md에서 "PLAN에서 결정"으로 미확정 — `match`/`get`/`list`/`validate` 4개 서브커맨드 각각에 다른 영향을 미친다(Q3 참조) | 중간 | TASK.md 명확화 결과 표 |
| H-7 | `listCommand()`의 `--group=community` 필터가 `_source === 'community'` 단일 조건이므로(`:349-351`) 신규 `_source: 'project'` 마커는 이 필터에서 자연히 제외된다(안전) — 그러나 "프로젝트 스킬만 나열" 요구가 생기면 `listCommand()`에 신규 분기(`--group=project` 등)를 추가해야 하며 이는 R-5/R-6 범위 밖의 잠재 확장이다 | 낮음 | `opal/tools/skill-registry/skill-registry.js:348-355` |

## 6. 기술 컨텍스트

### 6.1 프로젝트 SSOT

전체 기술 스택은 `docs/PROJECT.md`(프로젝트 구조·컴포넌트 표)를 참조한다. 이 섹션은 재기재하지 않는다.

### 6.2 이번 태스크 델타

| 구분 | 항목 | 비고 |
|------|------|------|
| 신규 도입 | 프로젝트 스코프 스킬 registry(JSON, 경로 미확정) | `.opal/` 하위 신규 파일 — install-mac.sh가 프로젝트 로컬 `.opal/`을 쓰지 않음을 실측 확인(`scripts/install-mac.sh` grep 결과 0건, install은 `~/.opal/`만 기록) |
| 신규 도입 | `opal-skill-wizard` 신규 스킬(Markdown, OPAL 전용) | `opal/skills/opal-skill-wizard/SKILL.md` |

변경·신규 도입분 외 기존 스택(Node.js CommonJS, Markdown, Bash) 변경 없음.

### 6.3 추천 스킬

해당 없음 — 이번 태스크 자체가 스킬 신설이며, 구현에 필요한 별도 프레임워크 스킬은 식별되지 않는다.

### 6.4 추천 MCP

해당 없음 — 외부 라이브러리 문서 조회 불필요.

## 7. 지정 분석 질문 Q1~Q10 답변

- **Q1**: `loadAllSkills()`(`skill-registry.js:129-147`)의 `if (userReg) {...}` 블록(`:138-145`) 직후에 5번째 병합 단계로 `loadProjectRegistry(projectRoot)` 호출 + 동일한 override-loop(동일 `name`이면 `skills[idx]=` 대체, 아니면 push) 패턴을 추가하면 된다. `flattenGroups(projectReg, 'project')`로 `_source: 'project'` 마커를 부여해 기존 `isCommunitySkill()`(`_source==='community'` 단일 조건)과 자연 분리된다. 프로젝트 루트 판별은 3가지 선택지가 있다 — ① **cwd 기준**(`process.cwd()`): `getReferencesDir()`가 이미 쓰는 패턴(`:83-84`)이라 구현이 가장 단순하지만, 하위 디렉토리에서 CLI가 호출되면(H-5) 프로젝트 registry를 못 찾는다. ② **인자로 명시적 주입**(예: `--project-root=` 플래그 또는 신규 함수 파라미터): 정확하지만 `match`/`get`/`list`/`validate` 4개 CLI 진입점 전부와 skill-commands.md의 `//` 라우팅 절차, dashboard adapter까지 호출부를 모두 갱신해야 하는 배선 비용이 크다. ③ **환경변수**(예: `OPAL_PROJECT_ROOT`): 배선 비용은 낮지만 값 부재/오염 시 조용히 전역만 병합되는 실패 모드가 생기고, 오케스트레이터·워커 세션 간 환경변수 전파 보장이 필요하다. 세 방식 모두 PLAN에서 확정해야 한다(TASK.md 미확정 항목).
- **Q2**: 현재 `.opal/` 최상위에는 `AGENT.md`·`code-scan.json`·`worktree.json`·`MEMORY.json`·`brain/`·`memory/`가 있다(`ls .opal/` 실측, E1). 이 패턴과 정합하는 후보는 `.opal/skills-registry.json`(단일 파일, `code-scan.json`·`worktree.json`과 동일 계층) — 다만 이 경우 실제 설치된 스킬 파일 본체(SKILL.md)를 저장할 별도 디렉토리가 추가로 필요하다(예: `.opal/community-skills/{vendor}/{skill}/`, 전역 구조 미러링). 대안은 `.opal/community-skills/user-registry.json` + `.opal/community-skills/{vendor}/{skill}/`처럼 전역과 동일 서브구조를 프로젝트 루트에 그대로 두는 안 — 전역과 이름이 완전히 같아 사람이 스코프를 혼동하기 쉽다는 단점이 있다. install-mac.sh는 두 후보 모두에 손대지 않는다 — 프로젝트 상대 `.opal/` 경로에 대한 쓰기 동작이 실측 grep 결과 0건이다(`scripts/install-mac.sh` 전체에서 `.opal/`을 쓰는 곳은 `~/.opal/agents/...`류 홈 절대경로뿐).
- **Q3**: 현행 규칙은 "동일 `name`은 사용자 항목(user-registry) 우선"이다(`skill-registry.js:137-144`: `userSkills`를 순회하며 기존 배열에서 같은 `name`을 찾아 `skills[idx]=us`로 override, 없으면 push). 프로젝트를 이 뒤에 5번째로 병합하면 자연히 "프로젝트가 사용자보다 더 나중 = 더 우선"이 된다. 서브커맨드별 영향: `match`는 `matchByAlias`/`matchByTriggers`가 병합된 `skills` 배열을 그대로 쓰므로 override만 정확하면 자동 반영된다. `get`은 `skills.find()`가 병합 배열에서 첫 매치를 반환하므로 override가 배열 자체에 반영되어 있어야 한다(별도 로직 불필요). `list`는 override 후 배열에 프로젝트 항목만 남으므로 전역 항목이 "가려졌다"는 사실이 출력에서 사라진다 — 사용자가 섀도잉 여부를 알 수 없는 사이드이펙트가 생긴다(PLAN에서 표시 여부 결정 필요). `validate`는 override된 병합 배열만 검사하므로 전역 카탈로그의 동일 `name` 원본은 검증 대상에서 빠진다(기존 user-registry override와 동일한 기존 한계 상속, 신규 이슈 아님).
- **Q4**: `get`(`:327-340`)과 `match`(`:255-323`)는 경로 필드 계약이 이미 다르다 — `get`은 raw `paths`(배열, main) 또는 raw 커뮤니티 필드(경로 계산 없음)를 그대로 반환하고, `match`는 `resolveFirstPath()`(main, `:229-253`) 또는 `resolveCommunitySkillPath()`(community, `:100-109`)로 **단일 경로 문자열**을 계산해 반환한다. 따라서 R-6 AC("get 응답의 경로 필드로 반환")를 만족하려면 `get`에 신규 동적 계산을 추가해야 하는데, 이는 `get`이 지금까지 갖고 있던 "무계산 passthrough" 계약을 깨는 변경이다 — 이 계약에 의존하는 외부 소비자는 발견되지 않았다(`opal-help/SKILL.md`가 `get`을 호출하지만 필드 단정 없이 결과를 그대로 표시하는 절차이며, 코드 레벨 소비자는 0건). `resolveCommunitySkillPath()`(vendor 중첩 우선 → flat 폴백)와 `getCommunitySkillPath()`(canonical 설치 타깃 경로 계산, 존재 여부 무관하게 항상 값 반환, `:96-98`)는 역할이 분리되어 있다 — 전자는 "지금 어디 있는가"(조회), 후자는 "설치하면 어디에 둘 것인가"(설치 타깃 계산)이다. `dashboard/backend/adapters/skill_adapter.py`는 `list`만 호출하며(`get`/`match` 미사용, 코드 전체 grep 확인) 필드가 아닌 최상위 타입(list/dict/str)만 분기하므로(`:53-75`) 이번 변경의 직접 영향권 밖이다.
- **Q5**: 태스크 114 착수 시점 실측(`git status --porcelain`, `git log --oneline -5 -- opal/tools/skill-registry/skill-registry.js`, 스코프: 리포지토리 루트) 결과 `skill-registry.js`에 **미커밋 변경분이 없다** — 태스크 105의 변경분은 커밋 `69f5ce1`(`feat(105): opal-skill-manager 탐색·설치에 보안 4단 판정 + 후보 비교 도입`)로 이미 완전히 커밋되어 있고 (PM 교정: 워커가 인용한 `21037f6`은 동일 메시지의 별 브랜치 커밋이며, 현재 브랜치에서 이 파일을 변경한 커밋은 `69f5ce1`이다 — `git log --oneline -3 -- opal/tools/skill-registry/skill-registry.js` 실측, 스코프 리포지토리 루트 main), `state-tool show tasks/105-...` 조회 결과 전체 파이프라인(TASK~CLOSE)이 `완료` 상태다(마지막 행 "12 | CLOSE | DONE.md 생성 | ✅ | 2026-09-03 23:10:09"). TASK.md 작성 시점의 "미커밋" 관측(같은 날 00시대)은 105가 그 이후 EXECUTE~CLOSE까지 진행되며 stale이 된 것이다. 따라서 **충돌 회피 방안이 불필요** — 114은 이미 안정된 베이스 위에서 작업을 시작할 수 있다. 다만 105가 `scan-risk` 서브커맨드(`:655-845`)와 `main()` switch(`:912-918`)를 이미 추가해 놓았으므로, 114의 `loadAllSkills()`/`getCommand()` 확장은 이 기존 코드와 나란히(같은 파일, 다른 함수) 배치되는 형태가 된다 — 함수 단위로는 겹치지 않는다.
- **Q6**: 기존 테스트는 `opal/tools/skill-registry/tests/` 아래 4개 파일이다 — `test-match.js`·`test-migrate.js`·`test-scan-risk.js`·`test-validate.js`(전건 `ls` 실측). 실행 명령과 통과 수는 §1.4 표를 참조한다(cwd `/Volumes/Data/AiStudio/workspace/opal` 스코프, 개별 파일 `node <파일>` 직접 실행, 합계 41 pass / 0 fail, E1). 격리 방식은 `mkdtempSync` 임시 fixture 디렉토리 + `spawnSync`의 `env.HOME` 오버라이드(`os.homedir()` 리다이렉트) + `cwd` 옵션(프로세스 작업 디렉토리 지정) 併用이다(`test-match.js:126-135`, `test-validate.js:93-95,264-266`). 이 패턴은 프로젝트 registry의 유·무·파손 3케이스 테스트에 **그대로 재사용 가능**하다 — 프로젝트 registry가 cwd 기준으로 판별되는 설계라면 `spawnSync`의 `cwd` 옵션으로 fixture 프로젝트 루트를 지정하고, HOME 오버라이드는 전역(사용자/카탈로그) 격리에 병행 사용하면 두 스코프(전역/프로젝트)를 동시에 통제할 수 있다.
- **Q7**: 현재 등재된 alias 29종은 `erm`·`help`·`html-sa`·`mockup`·`next`·`oac`·`onb`·`opas`·`opbr`·`opd`·`opdd`·`opds`·`opdw`·`opeli5`·`opgc`·`opgr`·`opi`·`opim`·`opp`·`oppd`·`oppl`·`opsdd`·`opws`·`opwt`·`osc`·`osm`·`uid`·`wfb`·`wtm`이다(`opal-skills-registry.json` 전체 `alias` 필드 grep 실측). `opal-skill-manager`→`osm`, `opal-skill-creator`→`osc` 명명 패턴("스킬" 그룹 내 역할 이니셜 조합)을 따르면 `opal-skill-wizard`→**`osw`**가 자연스럽고 목록에 없어 충돌 0건이다. 대체 후보로 `oskw`(osm/osc와 유사 4자 변형)와 전체어 `wizard`도 목록에 없어 충돌 0건이나, 기존 짧은 3자 alias 관례(`osm`/`osc`/`opd` 등)에는 `osw`가 가장 정합적이다.
- **Q8**: `opal-skill-creator`는 "신규 생성"과 "개선" 2모드로 진입 분기하며(`SKILL.md:20-35`), 신규 생성 모드는 skill-creator 커뮤니티 스킬의 6단계(Capture Intent → Interview and Research → Write the SKILL.md → Test Cases → Running and evaluating → Improving the skill, `:61-77`)를 그대로 실행한다. 태스크 105가 `opal-skill-manager/SKILL.md`에 정의한 위임 페이로드(`requested_capability`·`requested_triggers`·`requested_output_format`·`searched_sources`·`candidates_evaluated`·`security_findings`·`skill_type_hint` 7필드, `SKILL.md:92-102`)는 필드명·용도 모두 skill-creator의 "Capture Intent"/"Interview and Research" 단계 입력과 1:1 대응하도록 설계되어 있어, wizard가 "적합 스킬 미발견" 경로에서 **동일 페이로드를 그대로 재사용할 수 있다** — 위임 트리거 조건(2단계 검색 0건 / 4단 2층 판정 후 잔존 후보 0건 / 사용자 전건 거부, `SKILL.md:85-88`)도 wizard의 skills.sh 직접 검색·2층 판정 절차(R-3/R-4)와 동일 구조이므로 조건 재사용도 가능하다.
- **Q9**: `docs/PROJECT.md`가 실제로 담는 항목은 (1) 프로젝트 개요 표(프로젝트명·도메인·현재 Phase), (2) 프로젝트 원칙 5항, (3) 프로젝트 구조(폴더 구조맵·네이밍 규칙), (4) 주요 컴포넌트(파이프라인별 표), (5) **프로젝트 구성**(요소·경로·기술 스택·전문 에이전트 4열 표, `PROJECT.md:213-217`), (6) 프로젝트 문서 레지스트리(5열 표)다 — wizard가 "이 프로젝트에 적합한 스킬"을 판단하는 데 직접 재사용 가능한 것은 (3) 폴더 구조맵(어떤 기술 영역이 존재하는지)과 (5) 프로젝트 구성 표(기술 스택 컬럼)다. 반면 스킬 제안에 필요하지만 PROJECT.md에 없는 항목은 ① **팀 작업 관습/워크플로우**(예: 특정 CI 도구, 코드 리뷰 방식 — opal-project-init 인터뷰 Q4 "특별히 지켜야 할 제약"에서 일부 커버되지만 구조화된 필드가 아님), ② **원하는 스킬의 기능 범주**(자동화 대상 작업 유형) 자체는 PROJECT.md 어디에도 없다 — 이는 wizard가 신규로 인터뷰해야 하는 결측 항목이다.
- **Q10**: 현행 `skill-commands.md:24` 문장은 `match` 응답의 `installed: false`(미설치 community 스킬) 단일 조건만으로 `opal-skill-manager/SKILL.md §6`을 지목한다. `installed`는 현재 "`resolveCommunitySkillPath()`가 null이 아니다"(community 한정)를 의미하는 불리언이고, `ambiguous`는 "basename이 여러 vendor와 충돌"(`matchByAlias`의 `__ambiguous` 반환, `:194-195`)을 의미한다. 프로젝트 스코프까지 포괄하려면 최소 3중 분기가 필요하다 — ① `_source==='community' && installed===false` → 기존과 동일하게 `opal-skill-manager §6`, ② `_source==='project'`(신설 마커) → `opal-skill-wizard`의 설치 절차로 라우팅(신규 분기), ③ `ambiguous:true`는 소스 무관 공통 분기로 유지. 이때 `installed` 필드의 의미도 "community 스킬의 clone-copy 설치 여부"에서 "해당 스킬이 정의는 됐지만 실물 SKILL.md가 아직 없는 상태 전반"으로 일반화해야 하며, 이는 `matchCommand()`가 project 스킬에 대해서도 `installed` 유사 필드를 계산해 반환하도록 확장하는 것을 전제한다(현재 `matchCommand`는 main/community 2분기만 존재, `:282-320`).

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| `loadAllSkills()` 확장 지점 | `skill-registry.js:138-145`(userReg 병합 블록) 직후에 5번째 병합 단계 추가, `flattenGroups(projectReg, 'project')`로 `_source:'project'` 마커 부여 | `opal/tools/skill-registry/skill-registry.js:129-147` |
| 전역 override 규칙 선례 | 동일 `name`은 나중에 병합되는 소스가 우선(`skills[idx]=` 대체) — 프로젝트를 최후 병합하면 프로젝트가 자동 최우선이 됨 | `opal/tools/skill-registry/skill-registry.js:137-144` |
| `get` 서브커맨드 현재 계약 | 경로 동적 계산 없음(main/community 공통, raw passthrough) — R-6 구현 시 이 계약을 깨는 것이 불가피함을 PLAN이 인지하고 설계할 것 | `opal/tools/skill-registry/skill-registry.js:327-340` |
| 기존 테스트 통과 기준선 | 4파일 41 pass / 0 fail(cwd 리포지토리 루트, 개별 실행) — R-8 회귀 판정의 베이스라인 | §1.4 실측(E1) |
| `get` 테스트 커버리지 | 0건(기존 4파일 어디에도 없음) — R-8 신규 테스트가 `get`도 반드시 포함해야 함 | `opal/tools/skill-registry/tests/*.js` grep 결과 |
| 태스크 105 충돌 여부 | 없음 — 105는 커밋 `69f5ce1`로 완전히 커밋·CLOSE 완료 상태(`state-tool show` 확인) | `git log --oneline -5 -- opal/tools/skill-registry/skill-registry.js` |
| install-mac.sh 프로젝트 `.opal/` 접촉 여부 | 없음(grep 0건, `~/.opal/` 홈 절대경로만 기록) — 프로젝트 registry 파일은 install 재실행에 안전 | `scripts/install-mac.sh`(전체 `.opal/` grep) |
| wizard alias 비충돌 후보 | `osw`(1순위, 명명 패턴 정합) / `oskw` / `wizard` — 등재 29종 alias와 충돌 0건 | `opal/core/references/opal-skills-registry.json`(alias 전건 grep) |
| skill-creator 위임 페이로드 재사용성 | 태스크 105가 정의한 7필드 위임 페이로드를 wizard가 그대로 재사용 가능(필드명·용도 1:1 대응 확인) | `opal/skills/opal-skill-manager/SKILL.md:92-102`, `opal/skills/opal-skill-creator/SKILL.md:61-77` |
| PROJECT.md 재사용 가능 항목 | 폴더 구조맵 + "프로젝트 구성" 4열 표(요소/경로/기술스택/전문에이전트) | `docs/PROJECT.md`(§프로젝트 구조, §프로젝트 구성) |
| PROJECT.md 결측 항목(인터뷰 필요) | 원하는 스킬의 기능 범주(자동화 대상 작업 유형) — PROJECT.md 어디에도 구조화된 필드 없음 | `docs/PROJECT.md` 전체 절 목록(§7 Q9) |
| `//` 라우팅 3중 분기 필요성 | community 미설치(기존 유지) / project 마커(신규, wizard로 라우팅) / ambiguous(소스 무관 공통) | `opal/core/references/harness/skill-commands.md:23-24` |
| `docs/ARCHITECTURE.md` 반영 위치 | §커뮤니티 스킬(187-198) 인접 절 — 현재 "레지스트리 구조" 전용 절은 없고 표 1행("레지스트리 (이원)")으로만 존재 | `docs/ARCHITECTURE.md:196` |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| 프로젝트 루트 판별 방식 | cwd 단순 판별(구현 쉬움·하위 디렉토리 호출 시 실패 위험) vs 명시적 인자 주입(정확·배선 비용 큼) vs 환경변수(배선 비용 낮음·조용한 실패 위험) — 3자 중 선택 | Q1, H-5 |
| 프로젝트 registry 파일 경로·파일명 | `.opal/skills-registry.json` 단일 파일(+ 별도 설치 디렉토리 필요) vs `.opal/community-skills/` 전역 미러링 서브구조(이름 혼동 위험) | Q2, H-4 |
| 전역-프로젝트 동일 `name` 충돌 우선순위 | 현행 override 방향(나중 병합=우선)을 그대로 적용해 프로젝트 최우선으로 할지, 별도 명시적 우선순위 규칙을 둘지 | Q3, H-6 |
| `list` 응답에서 섀도잉된 전역 항목 표시 여부 | override로 가려진 전역 스킬을 `list` 결과에서 어떻게든 노출할지(신규 필드 등), 현행처럼 완전히 숨길지 | Q3 |
| `get` 서브커맨드 경로 계산 계약 변경 범위 | project(및 필요 시 community) 스킬에도 동적 경로 계산을 추가할 것인지, 추가한다면 기존 "raw passthrough" 계약과의 하위호환을 어떻게 유지할지 | Q4, H-2, H-3 |
| `analysis-core.md` §5 축에 "도구" 라벨 추가 여부 | 이번 태스크 범위 밖이지만 `skill-registry.js`류 CLI 도구 파일의 §1.1 라벨 공백은 반복될 사안 — PLAN이 임시 라벨을 정하고 별도 개선 제안으로 분리할지 결정 | H-1 |

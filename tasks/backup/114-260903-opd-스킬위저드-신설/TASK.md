# TASK: opal-skill-wizard 신설 — 프로젝트 적합 스킬 제안 + 프로젝트 스코프 설치

> 작성일: 2026-09-03 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

프로젝트에 적합한 커뮤니티 스킬을 인터뷰·분석으로 도출해 제안하고, 승인된 스킬을 **프로젝트 스코프**에 설치하는 신규 스킬 `opal-skill-wizard`를 만든다. 설치된 스킬이 `//` 커맨드로 발동하도록 `skill-registry.js`에 프로젝트 registry 병합 경로를 추가한다.

## 배경

현행 OPAL에는 "이 프로젝트에 어떤 스킬이 필요한가"를 판단해 주는 컴포넌트가 없다. `opal-skill-manager`는 사용자가 이미 원하는 스킬을 알고 있을 때의 검색·설치 도구이며, 제안 기능이 없다. 또한 커뮤니티 스킬 설치 대상은 전역(`~/.opal/community-skills/`) 단일이라, 특정 프로젝트에만 필요한 스킬도 전역을 오염시킨다.

## 배경 분석 (대화에서 도출)

- 요청한 2모드 구조(신규=인터뷰 / 기존=분석+인터뷰)는 `opal-project-init`의 초기화·최신화 2모드와 동일 골격이다 — 모드 판별(`opal/skills/opal-project-init/SKILL.md:54`), 초기화(신규)(`:263`), 초기화(기존)(`:354`), 최신화 Phase 2.5 조건부 인터뷰(`:806`). 따라서 프로젝트 파악을 새로 구현하면 로직이 중복된다.
- 커뮤니티 스킬 설치 경로는 전역 단일이며 플랫폼 네이티브 디렉토리 복사를 금지하는 것이 현행 명문 규칙이다 (`opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙: "커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다. 플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다.").
- OPAL은 플랫폼 네이티브 스킬 디렉토리를 이미 폐기했다 — install이 `~/.claude/skills/`·`~/.cursor/skills/`·`~/.gemini/antigravity/skills/`를 **레거시로 지정하고 수동 삭제를 권고**하며 "스킬/에이전트가 이제 `~/.opal/` 단일 경로로 배포됩니다"라고 안내한다 (`scripts/install-mac.sh:1723-1751`). codex 스킬 경로는 이 목록에 없다.
- `//` 커맨드 발동은 네이티브 스킬 로더에 의존하지 않는다 — `skill-registry.js match`로 매칭 후 SKILL.md를 Read하고 프로세스를 따르는 경로다 (`opal/core/references/harness/skill-commands.md:11-23`). 부트스트래퍼가 배포되는 4개 플랫폼(claude·cursor·gemini·codex)에서 동일하게 성립한다 (`scripts/install-mac.sh:1264-1279`).
- 그러나 현행 레지스트리 로더는 프로젝트 경로를 읽지 않는다 — `loadAllSkills()`가 병합하는 소스는 3개이고 전부 전역 고정이다 (`opal/tools/skill-registry/skill-registry.js:129-140`). 경로 계산도 `getReferencesDir()`(`:80-92`)와 `os.homedir()` 기반 `loadUserRegistry()`(`:120`)뿐이며, 설치 경로 해석 `resolveCommunitySkillPath()`도 `~/.opal/community-skills/`만 탐색한다 (`:100-110`).
- 미설치 매칭 시 라우팅이 `opal-skill-manager` §6을 직접 지목하고 있다 (`opal/core/references/harness/skill-commands.md:24`: "`opal-skill-manager/SKILL.md §6`(미설치 매칭 시 자동 설치·실행) 절차를 먼저 따른다").
- 위험 패턴 스캔은 이미 도구로 존재한다 — `scan-risk` 서브명령이 `main()` switch에 등재되어 있고(`opal/tools/skill-registry/skill-registry.js:912`) 위험 패턴이 코드 상수로 정의되어 있다(`:675`). 단 이 변경분은 태스크 105의 미커밋 작업물이다.
- 동일 파일(`opal/tools/skill-registry/skill-registry.js`)을 태스크 105가 수정 중이며 미커밋 상태다 (`git status --porcelain` 실행 결과: ` M opal/tools/skill-registry/skill-registry.js`). 태스크 105는 TEST PM Gate 행에서 대기 중이다 (`~/.opal/tools/state-tool/run.sh show tasks/105-260902-opds-스킬-탐색설치-개선` 실행 결과: 9행 `TEST | PM Gate | ⬜`).

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` 제안 대상은 **커뮤니티 스킬(skills.sh)로 한정**하고, 적합 스킬이 없으면 `opal-skill-creator`로 위임해 신규 생성한다. OPAL 프레임워크 내장 스킬 안내는 범위에서 제외한다.
- `[결정]` 설치 대상은 **프로젝트 스코프**를 신설한다 — 전역(`~/.opal/community-skills/`)은 `opal-skill-manager`가 계속 담당하고, wizard는 프로젝트에만 설치한다.
- `[결정]` wizard는 **`opal-skill-manager`를 호출하지 않는다.** skills.sh 검색·clone·설치를 wizard가 직접 수행한다.
- `[결정]` 기존 프로젝트 분석은 `docs/PROJECT.md`를 입력으로 재사용하고, 결측 항목만 인터뷰로 보완한다. wizard가 프로젝트 파악을 처음부터 수행하지 않는다.
- `[결정]` 설치 전 사전 검사는 공용 도구 `skill-registry.js scan-risk`를 직접 호출해 수행한다. 스킬(`opal-skill-manager`)을 경유하지 않는다.
- `[결정]` 프로젝트 설치 이력 registry를 신설해 설치 이력·보안 판정·출처를 보존한다.
- `[결정]` 설치한 스킬의 발동 경로는 **OPAL 레지스트리 + `//` 커맨드**다. 플랫폼 네이티브 스킬 디렉토리(`.claude/skills/` 등)에 복사하지 않는다 — 4개 플랫폼에서 동일하게 동작하는 유일한 경로이며, 현행 명문 규칙과 정합한다.
- `[사실]` 이 방식의 대가는 플랫폼이 SKILL.md description으로 스킬을 자동 트리거하는 기능을 쓸 수 없다는 점이다 — 발동은 알투(PM)의 레지스트리 해석 경로로 한정된다 (`opal/core/references/harness/skill-commands.md:11-23`).
- `[결정]` 착수 트랙은 `//opd --agentic`이다 — `//opds --agentic`으로 착수했으나 요구사항 11건이 Short Task 기준(8건)을 초과해 캡틴 승인으로 Full Task 승격했다 (`opal/skills/opal-pilot-dev-short/SKILL.md` §에스컬레이션 규칙 「조기 에스컬레이션」).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 프로젝트 적합 커뮤니티 스킬을 인터뷰·분석으로 제안하고 승인분을 프로젝트 스코프에 설치하는 `opal-skill-wizard`를 신설하며, 설치분이 `//` 커맨드로 발동하도록 레지스트리 로더에 프로젝트 경로를 추가한다 | - | 현행 로더가 전역 3소스만 병합: `opal/tools/skill-registry/skill-registry.js:129-140` |
| 범위 | **포함** — (1) `opal/skills/opal-skill-wizard/SKILL.md` 신설(2모드: 신규 인터뷰 / 기존 PROJECT.md 재사용+결측 인터뷰) (2) `skill-registry.js`에 프로젝트 registry 병합 + 프로젝트 스킬 경로 해석 추가 (3) 프로젝트 registry 스키마 정의 (4) 해당 기능 테스트를 `opal/tools/skill-registry/tests/`에 추가 (5) `harness/skill-commands.md` 미설치 라우팅 절 개정 (6) 레지스트리 등재(`opal-skills-registry.json`) + 약어 배정 (7) 변경이력 행 추가. **제외** — `opal-skill-manager` 호출 연동, OPAL 내장 스킬 안내, 플랫폼 네이티브 디렉토리 배선, 전역 설치 경로 변경, `opal-project-init`에의 편입 | 전역·프로젝트 동일 `name` 충돌 시 우선순위 (PLAN에서 결정) / 프로젝트 registry 파일 경로·파일명 (PLAN에서 결정) / wizard 약어 (PLAN에서 결정) | 현행 충돌 규칙은 "동일 `name`은 사용자 항목 우선": `opal/tools/skill-registry/skill-registry.js:137-140` |
| 제약 | `~/.opal/` 배포본을 직접 수정하지 않고 프로젝트 소스를 수정한 뒤 install로 재배포하며, 플랫폼 분기를 어댑터 계층 밖에 하드코딩하지 않고, 문서 수정 시 변경이력 표에 행을 추가하며, `skill-registry.js` 변경은 기존 전역 3소스 동작을 깨지 않는 additive 방식으로 한정한다. 태스크 105와의 동일 파일 충돌은 해소되었다(105가 커밋 `69f5ce1`로 커밋·CLOSE 완료, 작업 트리 클린) | - | `.opal/AGENT.md` §업무 수행 지침 / §금지사항 / `git status --porcelain` 재실측(트리 클린 — 114 폴더만 미추적) / ANALYSIS.md §7 Q5 |
| 완료기준 | (1) `opal/skills/opal-skill-wizard/SKILL.md`가 존재하고 신규·기존 2모드의 판별 기준과 각 모드 절차가 절 단위로 존재한다 (2) 제안→승인→설치 흐름에 `scan-risk` 호출과 승인 게이트가 각 1회 이상 명시된다 (3) `skill-registry.js`가 프로젝트 registry를 병합하고, 프로젝트 스코프 스킬에 대해 `match`가 `found:true`를 반환한다 (4) 기존 전역 3소스 동작 회귀 0건이 테스트로 확인된다 (5) 신규 기능 테스트가 `opal/tools/skill-registry/tests/`에 추가되어 전건 통과한다 (6) `harness/skill-commands.md`에 프로젝트 스코프 미설치 라우팅이 반영되고 `opal-skill-manager` 단독 지목 문장이 잔존 0건이다 (7) `opal-skills-registry.json`에 wizard 항목이 등재되어 `match "{약어}"`가 이 스킬을 반환한다 (8) 변경이력 표에 이번 태스크(114) 행이 추가된다 | - | - |

## 요구사항

- [ ] **R-1** wizard SKILL.md 신설 — 무엇을: 2모드(신규 인터뷰 / 기존 분석+결측 인터뷰) 판별과 각 모드 절차, 제안→승인→설치 흐름을 정의 / 어디에: `opal/skills/opal-skill-wizard/SKILL.md` (신규) / 왜: 확정 방향(제안 컴포넌트 신설) / AC: 파일이 존재하고, 모드 판별 기준이 표 또는 절로 존재하며, 신규·기존 각 모드 절차가 별개 절로 존재하고, 제안→승인→설치 3단이 순서대로 기재된다
- [ ] **R-2** 기존 프로젝트 분석 입력 계약 — 무엇을: `docs/PROJECT.md`를 입력으로 재사용하고 결측 항목만 인터뷰로 보완하는 절차를 정의 / 어디에: `opal/skills/opal-skill-wizard/SKILL.md` / 왜: 확정 방향(중복 인터뷰 방지) / AC: 재사용할 PROJECT.md 항목 목록이 명시되고, PROJECT.md 부재 시 폴백 절차가 존재하며, 결측 판정 기준이 기재된다
- [ ] **R-3** skills.sh 직접 검색·설치 절차 — 무엇을: `opal-skill-manager` 호출 없이 검색·clone·프로젝트 스코프 복사를 수행하는 절차를 정의 / 어디에: `opal/skills/opal-skill-wizard/SKILL.md` / 왜: 확정 방향(manager 비호출) / AC: 검색 명령·clone 대상(임시 디렉토리)·복사 대상(프로젝트 경로)이 각각 명시되고, `opal-skill-manager`를 호출하라는 지시가 문서 전체에 0건이다
- [ ] **R-4** 설치 전 보안 검사 배선 — 무엇을: 복사 직전 `skill-registry.js scan-risk`를 호출하고 판정별 동작을 정의 / 어디에: `opal/skills/opal-skill-wizard/SKILL.md` / 왜: `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." / AC: `scan-risk` 호출이 복사 직전 단계에 명시되고, 판정별 동작(진행·확인 게이트·제외)이 표로 존재하며, 검사 실패 시 설치를 진행하지 않는다는 규칙이 명시된다
- [ ] **R-5** 프로젝트 registry 병합 — 무엇을: `loadAllSkills()`가 프로젝트 registry를 추가 병합하도록 확장 / 어디에: `opal/tools/skill-registry/skill-registry.js` / 왜: 현행 로더가 전역 3소스만 병합 (`opal/tools/skill-registry/skill-registry.js:129-140`) / AC: 프로젝트 registry에 등재된 스킬에 대해 `match "{name}"`이 `found:true`를 반환하고, 프로젝트 registry 부재·파손 시 CLI가 다운되지 않고 전역 3소스만으로 정상 동작한다
- [ ] **R-6** 프로젝트 스킬 경로 해석 — 무엇을: 프로젝트 스코프 설치 경로를 해석하는 함수 또는 분기를 추가 / 어디에: `opal/tools/skill-registry/skill-registry.js` / 왜: 현행 해석이 `~/.opal/community-skills/`만 탐색 (`opal/tools/skill-registry/skill-registry.js:100-110`) / AC: 프로젝트에 설치된 스킬의 SKILL.md 경로가 `get` 응답의 경로 필드로 반환되고, 미설치 시 기존과 동일하게 처리된다
- [ ] **R-7** 프로젝트 registry 스키마 정의 — 무엇을: 설치 이력 항목의 필드 집합(출처·commit·라이선스·보안 판정·스캔 시점 포함)을 정의 / 어디에: `opal/skills/opal-skill-wizard/SKILL.md` + `docs/ARCHITECTURE.md` / 왜: 확정 방향(설치 이력·판정 보존) / AC: 필드 목록이 표로 존재하고, `skill-registry.js validate` 실행이 이 스키마를 따르는 항목에서 error 0건으로 통과한다
- [ ] **R-8** 회귀 방지 + 신규 테스트 — 무엇을: 프로젝트 registry 병합·경로 해석 테스트 추가 및 기존 테스트 전건 통과 확인 / 어디에: `opal/tools/skill-registry/tests/` / 왜: 완료기준 (4)(5) / AC: 신규 테스트 파일이 추가되어 프로젝트 registry 유(有)·무(無)·파손 3케이스를 검증하고, 기존 테스트가 전건 통과하며 실행 명령과 통과 수를 스코프와 함께 기록한다
- [ ] **R-9** 미설치 라우팅 절 개정 — 무엇을: 프로젝트 스코프 미설치 매칭 시의 라우팅을 반영 / 어디에: `opal/core/references/harness/skill-commands.md` / 왜: 현행 문장이 `opal-skill-manager` §6을 단독 지목 (`opal/core/references/harness/skill-commands.md:24`) / AC: 프로젝트 스코프 분기가 문서에 존재하고, `opal-skill-manager`만을 유일 경로로 지목하는 문장이 0건이며, 변경이력 행이 추가된다
- [ ] **R-10** 레지스트리 등재 + 약어 배정 — 무엇을: wizard를 스킬 레지스트리에 등재하고 약어를 배정 / 어디에: `opal/core/references/opal-skills-registry.json` / 왜: `//` 커맨드 발동은 `match` 조회에 의존 (`opal/core/references/harness/skill-commands.md:11-23`) / AC: `match "{배정 약어}"` 실행이 `found:true` + `name: "opal-skill-wizard"`를 반환하고, 기존 스킬 약어와 충돌 0건임이 확인된다
- [ ] **R-11** 변경이력 행 추가 — 무엇을: 이번 태스크 행을 추가 / 어디에: 이번 태스크로 수정한 각 문서의 변경이력 표 / 왜: `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무." / AC: 수정한 문서마다 일시(KST)와 태스크 번호(114)를 포함한 행이 각 1건 추가된다

## 제약 조건

- [MUST] `.opal/AGENT.md` §업무 수행 지침: "`~/.opal/` 배포 파일을 직접 수정하지 않는다. 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)를 수정한 뒤 install로 재배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다."
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."
- [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- [MUST] `opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙: "커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다. 플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다." — 전역 담당은 manager로 유지되므로 wizard는 이 규칙의 전역 부분을 변경하지 않고 프로젝트 스코프만 추가한다.
- `skill-registry.js` 변경은 기존 전역 3소스 병합 동작을 보존하는 additive 방식으로 한정한다 (근거: `opal/tools/skill-registry/skill-registry.js:129-140`).
- **[해소]** 태스크 105의 동일 파일 병행 수정 위험은 해소되었다 — 105가 커밋 `69f5ce1`로 커밋되고 CLOSE까지 완료되어 작업 트리가 클린하다(`git status --porcelain` 재실측: 114 폴더만 미추적). 114은 안정된 베이스 위에서 시작한다. 커밋은 여전히 사용자 명시 요청 시에만 수행한다 (`~/.opal/references/opal-harness.md` §1 커밋 규칙).

## 기술 스택

- Node.js (CommonJS) — `opal/tools/skill-registry/skill-registry.js`
- Bash — `scripts/install-mac.sh` 배포 계층
- Markdown — 스킬·참조 문서 (SKILL.md, references)
- 프로젝트 루트에 `package.json`·`pyproject.toml`·`go.mod`·`Cargo.toml` 부재 — 패키지 매니저 비의존 (실행: `ls package.json pyproject.toml go.mod Cargo.toml` 결과 없음)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 전역 설치 경로 규칙·검색 절차의 현행 기준 |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 레지스트리 로더·경로 해석·`scan-risk` 현행 구현 |
| D-3 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | `//` 커맨드 해석·미설치 라우팅 규칙 |
| D-4 | 설계 | opal-project-init SKILL.md | `opal/skills/opal-project-init/SKILL.md` | 2모드 인터뷰·분석 골격 참고 (중복 회피 판단 근거) |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 플랫폼 네이티브 스킬 경로 폐기 사실·부트스트래퍼 배포 대상 |
| D-6 | 설계 | 프로젝트 PM 프로필 | `.opal/AGENT.md` | 배포 경계·플랫폼 분기·변경이력 금지사항 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | 도구 집행 원칙·수술적 변경 원칙 |
| D-8 | 외부 | skills.sh | [skills.sh](https://skills.sh/) | 커뮤니티 스킬 검색 소스 |
| D-9 | 설계 | 태스크 105 TASK.md | `tasks/105-260902-opds-스킬-탐색설치-개선/TASK.md` | 동일 파일 병행 수정 범위·`scan-risk` 도입 맥락 |

# TASK: 커뮤니티 스킬 관리 워크플로우 통일 (검색·설치·제거 + `//` 호출 미설치 분기)

> 작성일: 2026-07-17 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 + 사전 진단 대화 (D1~D4 결함 실측)
> 출력: TASK.md

## 작업 목표

커뮤니티 스킬의 검색·설치·제거·업데이트 워크플로우를 clone-copy(A안) 단일 방식으로 통일하고, `//xxx` 호출 시 미설치 스킬 처리 분기를 skill-commands.md(호출 경로)로 이관하여 매끄러운 단일 흐름을 만든다.

## 배경

캡틴이 커뮤니티 스킬(obra/brainstorming) 설치를 테스트하는 과정에서, 스킬 검색(`//` 커맨드)과 스킬 관리(skill-manager)의 흐름이 서로 어긋나 "설치했는데 미설치로 판정", "`//스킬명 + 텍스트` 매칭 실패", "미설치 시 에이전트 행동 미정의" 문제가 관측되었다.

## 배경 분석 (대화에서 도출)

사전 진단(2026-07-17, PM 실측)으로 확인된 결함 4종:

| # | 결함 | 실측 근거 |
|---|------|----------|
| D1 | 설치 레이아웃 불일치 — npx 시대 잔재 31개는 flat(`~/.opal/community-skills/pdf/`), registry 판정은 vendor 중첩(`anthropics/pdf/SKILL.md`)만 검사 → 설치본을 미설치로 오판 | `opal/tools/skill-registry/skill-registry.js:76-78` (`getCommunitySkillPath`), 디스크 실사(flat 31 + 중첩 1) |
| D2 | 매칭 비대칭 — `//pdf`는 원문 폴백으로 우연히 매칭, `//pdf 문서 만들어줘`는 found:false. alias 매칭이 풀네임(`anthropics/pdf`)만 인정 | `skill-registry.js:129-135` (`matchByAlias`), match 커맨드 실행 실측 |
| D3 | 워크플로우 문서 이원화 — `//` 시점 로드되는 skill-commands.md에 installed:false 분기 부재. 자동 설치 절차(§6)는 skill-manager SKILL.md에만 존재(명시 호출 시에만 로드) | `opal/core/references/harness/skill-commands.md` (분기 없음), `opal/skills/opal-skill-manager/SKILL.md` §6 |
| D4 | §6 설치 명령 자체가 오동작 — `npx skills add`는 설치 경로 지정 옵션이 없고 플랫폼 에이전트 디렉토리(`./.claude/skills/` 또는 `~/.claude/skills/`)에만 설치. `~/.opal/community-skills/`에는 도달 불가 | npx skills CLI `--help` + 스크래치패드 실설치 실측 (`→ ./.claude/skills/pdf` + `skills-lock.json` 생성 확인) |

추가 관찰: flat 31개는 v2.0(태스크 142) "번들→fetch 전환" 이전 v1 번들 설치분(2026-05-10 타임스탬프)이며, install의 사용자 데이터 보존 정책(142 D-4)으로 잔존.

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 사항 | 합의일 |
|---|----------|--------|
| C-1 | 설치 레이아웃 SSOT = **vendor 중첩**(`~/.opal/community-skills/{vendor}/{skill}/`). flat 잔재는 1회 마이그레이션으로 중첩 구조로 이동 | 2026-07-17 |
| C-2 | 설치 방식 = **A안(clone-copy) 통일**: `git clone --depth 1` → 스킬 폴더 추출 → vendor 중첩 경로 복사 → clone 시점 commit SHA를 registry `commit_sha`에 기록. `npx skills add`는 OPAL 흐름에서 제거 | 2026-07-17 |
| C-3 | `npx skills`는 **검색(find)·업데이트 확인(check) 전용**으로 역할 축소 | 2026-07-17 |
| C-4 | 검색·설치·제거·업데이트 관리 워크플로우 전체를 이번에 통일 (범위 확장 — 캡틴 지시) | 2026-07-17 |

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 커뮤니티 스킬 검색·설치·제거·업데이트 + `//` 미설치 분기를 clone-copy 단일 방식·단일 문서 흐름으로 통일 | - | D1~D4 실측 (배경 분석) |
| 범위 | 포함: `skill-registry.js`(판정·매칭), `skill-commands.md`(미설치 분기 SSOT), `opal-skill-manager/SKILL.md`(관리 절차 재작성), flat 잔재 마이그레이션, `community-skills-registry.json` 스키마 정합(install_command). 제외: 스킬 내재화(bundled) 옵션(별도 태스크), 신규 스킬 추가, dashboard/콘솔 | 마이그레이션 실행 주체(PLAN에서 결정: 1회 스크립트 vs skill-manager 최초 실행 훅 vs install 훅 — 142 D-4 보존 원칙과의 정합 검토 필수) | `scripts/install-mac.sh:1033` (community-skills 불가침) |
| 제약 | ① `~/.opal/` 직접 편집 금지 — 프로젝트 소스 수정 후 install 배포. ② 플랫폼 분기는 어댑터 계층만. ③ 변경이력 표 갱신 의무. ④ registry v2 스키마 하위호환 유지 | - | `.opal/AGENT.md` §금지사항 |
| 완료기준 | 요구사항 F-1~F-6 AC 전체 Pass + 기존 skill-registry 테스트 회귀 GREEN + E2E 시나리오(미설치 스킬 `//` 호출→설치→실행) PASS | - | TEST-SCENARIO.md |

## 요구사항

- [ ] **F-1 레이아웃 마이그레이션**: flat 잔재를 vendor 중첩 구조로 이동하는 마이그레이션을 구현한다.
  - 어디에: 마이그레이션 실행 주체는 PLAN에서 결정 (후보: `~/.opal/tools/` 스크립트 / skill-manager 절차 / install 훅)
  - 왜: C-1 (D1 해소)
  - AC: 마이그레이션 실행 후 `~/.opal/community-skills/` 1-depth에 vendor 디렉토리만 존재하고, registry 등재 스킬 전수가 `list --group=community`에서 `installed: true`로 판정된다. registry 미등재 flat 디렉토리는 삭제하지 않고 보존 또는 보고한다(142 D-4).
- [ ] **F-2 basename alias 매칭**: `//{스킬 basename}` 호출이 벤더 무관하게 매칭되도록 `matchByAlias`를 확장한다.
  - 어디에: `opal/tools/skill-registry/skill-registry.js:129-135`
  - 왜: D2 해소
  - AC: `match "//pdf 문서 만들어줘"` → `anthropics/pdf` + `cleanInput: "문서 만들어줘"` 반환. basename이 복수 벤더와 충돌하면 단일 자동 선택 대신 후보 목록(또는 명시 에러)을 반환한다.
- [ ] **F-3 미설치 분기 라우팅 정합**: `//xxx` 매칭 결과 `installed: false`일 때 skill-commands.md의 라우팅(소유자 선반영 v1.2, 2026-07-16)이 가리키는 skill-manager §6 절차를 A안 기준으로 재작성하여 라우팅↔절차를 정합시킨다.
  - 어디에: `opal/skills/opal-skill-manager/SKILL.md` §6 (+ 필요 시 `skill-commands.md` 라우팅 문구 미세 정합)
  - 왜: D3 해소 — 소유자가 skill-commands.md v1.2에 §6 라우팅을 선반영(절차 SSOT는 skill-manager §6 유지 방향으로 확정). 단 현행 §6은 npx add 기반(D4)이라 라우팅을 따라가도 오동작
  - AC: ① skill-commands.md의 미설치 라우팅이 §6을 가리키고 §6이 clone-copy 절차로 동작한다. ② 라이선스 확인된 스킬(MIT/Apache 등 명시)은 동의 대기 없이 자동 설치·즉시 실행, Unknown 라이선스만 확인 게이트(2차 확인, 기본 거부)를 거친다 — skill-commands.md v1.2 정책 원문과 §6이 모순 0. ③ 설치 후 매칭된 스킬의 SKILL.md를 즉시 Read·실행하는 단계가 §6에 명시된다.
- [ ] **F-4 설치 방식 A안 통일**: 설치 절차를 clone-copy + commit_sha 기록으로 단일화하고 `npx skills add` 지시를 전 문서에서 제거한다.
  - 어디에: `opal-skill-manager/SKILL.md` §2·§6, `skill-registry.js`(match 출력 `install_command` 필드), `community-skills-registry.json` schema_notes
  - 왜: C-2/C-3 (D4 해소)
  - AC: 프로젝트 소스 전체에서 `npx skills add`가 설치 지시로 등장하는 곳 0건(설명·변경이력 제외). match 출력의 설치 안내 필드가 clone-copy 절차와 정합한다. 설치 완료 시 registry 항목에 clone 시점 commit_sha가 기록된다.
- [ ] **F-5 관리 워크플로우 재작성**: skill-manager SKILL.md의 검색·설치·제거·업데이트 4절차를 A안 기준으로 재작성한다.
  - 어디에: `opal/skills/opal-skill-manager/SKILL.md`
  - 왜: C-4 — 관리 흐름 전체 통일
  - AC: ① 검색=`npx skills find`+설치 여부 대조 ② 설치=clone-copy(F-4) ③ 제거=vendor 중첩 디렉토리 삭제+registry 항목 제거 ④ 업데이트=upstream commit SHA 비교 후 재설치 제안 — 4절차가 각각 단계 목록으로 기재되고 상호 모순 문구 0건.
- [ ] **F-6 registry 갱신 경로 정의**: 사용자 PC에서 설치/제거 시 registry 갱신이 배포 경계와 충돌하지 않는 규칙을 명문화한다.
  - 어디에: `opal-skill-manager/SKILL.md` + 필요시 `skill-commands.md`
  - 왜: 설치 시 `~/.opal/references/community-skills-registry.json`을 갱신하는데, install이 이 파일을 재배포(덮어쓰기)하면 사용자 개인 설치 등록분이 소실될 수 있음 — 진단 중 발견된 잠재 리스크
  - AC: "사용자 설치 등록분과 install 배포본의 관계" 규칙이 문서에 명시되고, ANALYSIS에서 install 덮어쓰기 여부를 실측 확인한 결과가 반영된다.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- registry v2.1 스키마 하위호환 유지 (`commit_sha` 옵션 필드 체계 유지)
- 마이그레이션은 registry 미등재 사용자 데이터를 삭제하지 않는다 (142 D-4 보존 원칙)

## 기술 스택

- Node.js (skill-registry.js — 의존성 없는 단일 파일 CLI)
- Bash (마이그레이션·설치 절차, git CLI)
- Markdown (skill-commands.md, opal-skill-manager SKILL.md)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 판정·매칭 로직 수정 대상 (D1·D2) |
| D-2 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | 미설치 분기 SSOT 이관 대상 (D3) |
| D-3 | 설계 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 관리 워크플로우 재작성 대상 (D4·F-5) |
| D-4 | 설계 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | v2.1 스키마·install_command 정합 (F-4·F-6) |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | community-skills 불가침 정책(:1033)·registry 배포 경로 확인 (F-1·F-6) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드·문서 컨벤션 준수 |
| D-7 | 외부 | vercel-labs/skills CLI | [skills.sh](https://skills.sh/) | find/check 전용 역할 축소 근거 (실측: add는 경로 지정 불가) |

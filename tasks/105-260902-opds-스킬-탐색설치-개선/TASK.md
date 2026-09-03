# TASK: opal-skill-manager 탐색·설치 절차에 보안 판정 축 + 후보 비교 도입

> 작성일: 2026-09-02 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal-skill-manager`의 검색·설치 절차를 「검색 → 후보 3 선별 → shallow clone → 2층 판정 → 추천 1개 → 승인 → 복사·등록」으로 재작성하고, 현행에 없는 **보안 4단 판정 축**과 **후보 비교 절차**를 도입한다.

## 배경

외부 커뮤니티 스킬을 설치하는 현행 절차의 안전 판정 축은 라이선스 1축뿐이다. 라이선스가 확인된 스킬이라도 본문에 credential 접근·광범위 삭제·외부 실행이 들어 있으면 그대로 통과한다. 또한 검색 결과에서 어느 후보가 나은지 비교·추천하는 절차가 없어, 사용자가 후보를 직접 골라야 한다.

## 배경 분석 (대화에서 도출)

- 현행 스킬은 5개 절차(검색·설치·목록·삭제·업데이트 확인) + `//` 커맨드 미설치 자동 설치(§6)로 구성되며, 설치는 clone-copy 단일 방식이다 (`opal/skills/opal-skill-manager/SKILL.md` §1~§6).
- 안전 판정은 `license == "Unknown"` 단일 조건이고, RISKY 개념이 존재하지 않는다 (`opal/skills/opal-skill-manager/SKILL.md` §6 분기 판정).
- registry는 이미 OPAL 내부에 이원 구조로 존재한다 — 카탈로그 `~/.opal/references/community-skills-registry.json`(`$schema` v2.1, vendor 7개, install이 덮어씀) + 사용자 등록분 `~/.opal/community-skills/user-registry.json`(현재 미존재, 설치 이력 0건) (`opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙).
- 항목 스키마는 `{name, alias, description, triggers, source_repo, commit_sha, license}`이며, `validate()`는 `name`·`source_repo`·`license`만 검사하고 미지 필드는 무시한다 (`opal/tools/skill-registry/skill-registry.js:402-470`). 따라서 필드 추가는 additive로 안전하다.
- 후보 평가를 100점 루브릭으로 하면 같은 후보의 재채점 값이 달라져 재현 불가하다 — 헌법의 「Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose」에 저촉된다 (`~/.opal/PRINCIPLES.md` §Core Stance).
- 스펙 원안의 `skill-builder`에 대응하는 컴포넌트는 이미 `opal-skill-creator`로 존재한다 (`opal/skills/opal-skill-creator/SKILL.md`).

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` 탐색 소스는 `skills.sh` 단일로 한정한다 — 스펙 원안의 GitHub·기타 공개 소스 단계(Phase 3·4)는 채택하지 않는다.
- `[결정]` 후보는 최대 3개까지 선별하고, 3건을 모두 `git clone --depth 1`로 임시 디렉토리에 받아 SKILL.md 실물을 대조한 뒤 추천 1개를 낸다. clone은 임시 디렉토리이며 `~/.opal/community-skills/`로의 복사가 설치이므로, 승인 게이트는 설치 직전 1회를 유지한다.
- `[결정]` 평가는 100점 루브릭을 채택하지 않고 2층 판정으로 대체한다 — 1층은 도구가 참/거짓으로 탈락시키는 하드 필터, 2층은 3단 판정어(충족/부분/미달) + 실측값 비교 표이며 점수 합산을 금지한다.
- `[결정]` 보안 판정은 4단(SAFE / CAUTION / RISKY / UNKNOWN)을 도입한다.
- `[결정]` registry는 신설하지 않고 기존 이원 구조를 유지하며, 필드만 additive로 추가한다. 스펙 원안의 YAML 스키마 전환·Project Registry 스코프는 채택하지 않는다.
- `[사실]` 커뮤니티 스킬은 Global 전용(`~/.opal/community-skills/`)이며 플랫폼 네이티브 skills/ 디렉토리에 복사하지 않는 것이 현행 명문 규칙이다 (`opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙).
- `[결정]` 적합 스킬 미발견 시 `opal-skill-creator`로 위임하며, 위임 페이로드를 계약으로 정의한다.
- `[결정]` `//` 커맨드 자동 설치 정책(§6)의 승인 게이트 수준 자체는 이번 범위에서 변경하지 않는다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `opal-skill-manager` 검색·설치 절차를 후보 비교형으로 재작성하고 보안 4단 판정 축을 신설한다 | - | - |
| 범위 | **포함** — SKILL.md §1 검색·§2 설치 재작성, 1층 하드 필터 도구화, 2층 비교 표 규격, 보안 4단 판정, user-registry 필드 additive 추가, Match 등급화, `opal-skill-creator` 위임 계약, 변경이력 행 추가. **제외** — registry YAML 전환·Project/Hybrid 스코프·100점 루브릭·GitHub 등 추가 탐색 소스·§6 승인 게이트 수준 변경 | §6에 보안 판정 결과를 배선하는 최소 연동의 형태 (PLAN에서 결정) | 현행 절차 구성: `opal/skills/opal-skill-manager/SKILL.md` §1, §2, §6, §설치 경로 규칙 |
| 제약 | registry 필드 추가는 기존 스키마를 깨지 않는 additive 방식만 허용하고, `~/.opal/` 배포본을 직접 수정하지 않고 프로젝트 소스를 수정한 뒤 install로 재배포하며, 문서 수정 시 변경이력 표에 행을 추가한다 | - | `opal/tools/skill-registry/skill-registry.js:402-470` (미지 필드 무시) / `.opal/AGENT.md` §업무 수행 지침: "`~/.opal/` 배포 파일을 직접 수정하지 않는다" / `.opal/AGENT.md` §금지사항: "변경이력 누락 금지" |
| 완료기준 | (1) SKILL.md §1·§2가 6단 흐름으로 재작성되고 각 단계에 입출력이 명시된다 (2) 1층 하드 필터가 `skill-registry.js` 서브명령으로 존재하고 위험 패턴 검출 시 비-0 종료 또는 검출 목록 JSON을 반환한다 (3) 해당 서브명령의 테스트가 `opal/tools/skill-registry/tests/`에 추가되어 전건 통과한다 (4) 보안 4단 판정의 판정 조건과 판정별 동작이 표로 존재한다 (5) 2층 비교 표에 점수·합산 표기가 0건이다 (6) 변경이력 표에 이번 태스크 행이 추가된다 | - | - |

## 요구사항

- [ ] **R-1** 검색·설치 흐름 6단 재작성 — 무엇을: §1 검색·§2 설치를 「skills.sh 검색 → 후보 최대 3 선별 → 3건 shallow clone → 2층 판정 → 추천 1개 → 승인 → 복사·등록」으로 재작성 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §1, §2 / 왜: 확정 방향(후보 비교형 전환) / AC: 6단이 순서대로 절 또는 번호 항목으로 존재하고, 각 단에 입력과 출력이 1줄 이상 명시되며, `git clone --depth 1`이 임시 디렉토리 대상임과 복사가 설치임이 본문에 명시된다
- [ ] **R-2** 1층 하드 필터 도구화 — 무엇을: 위험 패턴 스캔 서브명령을 신설하여 clone된 디렉토리를 검사 / 어디에: `opal/tools/skill-registry/skill-registry.js` + `opal/skills/opal-skill-manager/SKILL.md` / 왜: 헌법 「a tool gates it, not prose」 (`~/.opal/PRINCIPLES.md` §Core Stance) / AC: 서브명령이 `main()` switch에 등재되고, 위험 패턴 목록이 코드 상수로 존재하며, 검출 결과를 `{ok, verdict, hits[]}` 형태 JSON으로 반환하고, 위험 패턴을 포함한 픽스처에서 검출 ≥1건 · 무해 픽스처에서 검출 0건을 테스트가 확인한다
- [ ] **R-3** 2층 비교 표 규격 정의 — 무엇을: 목적 적합·출력 형식 호환·유지 활동·부수효과 범위 4축을 3단 판정어(충족/부분/미달) 또는 실측값으로 비교하는 표 규격을 기재 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §2 / 왜: 확정 방향(루브릭 폐기) / AC: 4축이 표에 존재하고, 각 축의 표기 방식이 명시되며, 문서 전체에 점수·가중치·합산 표기가 0건이고, 판정 근거를 `SKILL.md:줄번호` 형식으로 인용하도록 지시하는 문장이 존재한다
- [ ] **R-4** 보안 4단 판정 도입 — 무엇을: SAFE/CAUTION/RISKY/UNKNOWN의 판정 조건과 판정별 동작(설치 진행·확인 게이트·추천 제외·추가 조사)을 정의 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §2 / 왜: 현행 안전 판정이 라이선스 1축뿐 (`opal/skills/opal-skill-manager/SKILL.md` §6) / AC: 4단이 모두 표에 존재하고 각 단에 판정 조건과 판정 시 동작이 채워지며, RISKY 판정 시 추천 후보에서 제외한다는 규칙이 명시된다
- [ ] **R-5** user-registry 필드 additive 추가 — 무엇을: 설치 기록 시 `trust`·`capabilities`·`scanned_at` 3필드를 함께 기록 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §2 user-registry.json 기록 규칙 / 왜: 판정 결과를 재조회 가능하게 보존 / AC: 3필드가 기록 규칙에 명시되고, 기존 7필드(`name`·`alias`·`description`·`triggers`·`source_repo`·`commit_sha`·`license`)가 유지되며, `skill-registry.js validate` 실행이 신규 필드 포함 항목에서 error 0건으로 통과한다
- [ ] **R-6** Match 등급화 — 무엇을: 설치 여부 대조 결과를 Exact / Partial / No Match 3등급으로 분류하고 등급별 동작을 정의 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §1 1단계 / 왜: 확정 방향(Reuse Before Install 명문화) / AC: 3등급이 표에 존재하고 각 등급의 판정 기준과 후속 동작이 명시되며, Exact Match 시 외부 검색을 수행하지 않는다는 규칙이 존재한다
- [ ] **R-7** `opal-skill-creator` 위임 계약 — 무엇을: 적합 스킬 미발견 시 넘길 페이로드(요청 capability·검색한 소스·후보별 미달 사유)를 계약으로 정의 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` / 왜: 확정 방향(위임 시 요구사항 재입력 방지) / AC: 페이로드 필드 목록이 존재하고, 위임 대상이 `opal-skill-creator`로 명시되며, 탐색한 소스와 미달 사유가 페이로드에 포함된다
- [ ] **R-8** 변경이력 행 추가 — 무엇을: 이번 개정 행을 추가 / 어디에: `opal/skills/opal-skill-manager/SKILL.md` §변경이력 / 왜: `.opal/AGENT.md` §금지사항: "변경이력 누락 금지" / AC: 버전·일시(KST)·변경내용·태스크 번호(105)를 포함한 행이 1건 추가된다

## 제약 조건

- [MUST] `.opal/AGENT.md` §업무 수행 지침: "`~/.opal/` 배포 파일을 직접 수정하지 않는다. 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)를 수정한 뒤 install로 재배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."
- [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- registry 스키마는 기존 v2.1 JSON 구조를 유지하며 필드 추가만 허용한다 — 항목 형상 변경·YAML 전환 금지.
- `npx skills add`는 계속 사용하지 않는다 (설치는 clone-copy 단일 방식 유지).
- 커밋은 사용자가 명시 요청할 때만 수행한다.

## 기술 스택

- Node.js — `opal/tools/skill-registry/skill-registry.js` (CommonJS, 외부 의존 없음)
- Node.js 테스트 — `opal/tools/skill-registry/tests/*.js` (test-match / test-migrate / test-validate)
- Markdown — 스킬 정의(`SKILL.md`) + frontmatter
- Bash — `git clone`·`git ls-remote`·`grep` 기반 절차, install-mac.sh 배포

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 개선 대상 본문 — 현행 5절차 + §6 자동 설치 |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 서브명령 신설 위치 + validate 필드 검사 범위 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·도구 배포 경계 규칙 |
| D-4 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 2-Layer 배포 모델·도구 계층 위치 |
| D-5 | 설계 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | 도구 집행 원칙·surgical changes |
| D-6 | 설계 | AGENT.md (PM 프로필) | `.opal/AGENT.md` | 배포 경계·변경이력·금지사항 |
| D-7 | 소스 | opal-skill-creator SKILL.md | `opal/skills/opal-skill-creator/SKILL.md` | 위임 대상 컴포넌트의 입력 형식 |
| D-8 | 설계 | skill-commands.md | `~/.opal/references/harness/skill-commands.md` | `//` 커맨드 미설치 라우팅이 §6을 참조하는 지점 |
| D-9 | 외부 | skills.sh | [skills.sh](https://skills.sh/) | 탐색 소스 — `npx skills find` 출력 필드 확인 |

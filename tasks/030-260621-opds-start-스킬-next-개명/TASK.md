# TASK: opal-start 스킬을 opal-next로 개명

> 작성일: 2026-06-21 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

재진입 가이드 스킬 `opal-start`(`//start`)를 **`opal-next`(`//next`)**로 개명한다. 이름이 기능("현재 상태 진단 → 다음 액션 안내")과 어긋나 `//opi`·`//onboarding`과 혼동되는 문제를 해소하고, 곧 신설할 `//help`(능력 카탈로그)와 역할 경계를 명확히 한다.

## 배경

`opal-start`의 실제 기능은 "현재 OPAL 환경 상태를 진단하여 다음 액션 하나를 권유"하는 **재진입 길잡이**다. 그러나 "start/시작"이라는 이름은 "처음 시작"을 연상시켜 프로젝트 초기화(`//opi`)·정체성 설정(`//onboarding`)과 의미가 충돌하고, 재진입·중간 길안내라는 핵심 성격이 드러나지 않는다. 캡틴이 "이름이 와닿지 않는다"고 지적했다.

## 배경 분석 (대화에서 도출)

개명 cascade 전수 조사 결과 (grep `opal-start` / `//start`, 소스 트리, `.opal/brain`·배포본 제외):

| 파일 | 현재 상태 | 조치 |
|------|----------|------|
| `opal/skills/opal-start/` (폴더) | 스킬 폴더 | → `opal-next/`로 rename |
| `opal/skills/opal-start/SKILL.md` | `name: opal-start`, triggers `//start`·"시작"·"처음부터", 본문 "opal-start — OPAL 재진입 가이드" | name·triggers·본문·변경이력 갱신 |
| `opal/skills/opal-start/references/start-flow.md` | 제목 "opal-start 진단·라우팅 흐름", 본문 `//start` 3곳 (L1·L3·L10·L136·L145) | → `next-flow.md` rename + 내용 `//next` 치환 |
| `opal/core/references/opal-skills-registry.json` (L595~606) | `"name": "opal-start"`, `"alias": "start"`, triggers `^opal-start$`·`^start$`·자연어, paths | name·alias·triggers·paths·description 갱신 + changelog 추가 |
| `opal/skills/opal-onboarding/SKILL.md` (L176) | "다음에 다시 정체성을 변경하려면 `//start` 또는 `//onboarding`을 사용하세요." | `//next`로 치환 |
| `README.md` (L125) | `| `//start` | 재진입 가이드 — 현재 상태 진단 + 다음 액션 권유 |` | `//next`로 치환 |

추가 확인:
- `scripts/`(install-mac.sh·windows.ps1)에 `opal-start` 하드코딩 **0건** — skills 디렉토리 통째 복사 방식으로 추정, 폴더 rename만으로 재배포 자동 반영 (PLAN에서 install 배포 로직 확정).
- 루트 부트스트랩 AGENT.md next-action 라인에 `//start` 언급 없음 (개명 영향 없음).
- `onboarding` SKILL.md L265 변경이력의 과거 `//start` 언급은 **사료(史料)**이므로 보존 (소급 변경 금지).

## 확정된 설계 방향 (대화에서 합의)

1. **새 이름 = `opal-next` / alias `//next`** — 캡틴이 4개 후보 중 선택 (트리거 "다음에 뭐 해야"와 직결, `//help`와 역할 구분 명확).
2. **`//start` alias·트리거 완전 제거** — 캡틴 지시 "alias 유지 안 해도 됨". 하위호환 alias 미유지. 자연어 트리거도 "다음" 중심으로 재편.
3. **기능·동작 불변** — 진단 항목·라우팅 분기 로직은 그대로. 이름/트리거/경로만 변경 (순수 rename + 참조 정합).

## 요구사항

- [ ] **R1. 폴더 rename** — `opal/skills/opal-start/` → `opal/skills/opal-next/` (하위 `SKILL.md`·`references/` 포함, git 추적 이력 보존)
  - 어디에: `opal/skills/`
  - 왜: 스킬 식별자 = 폴더명 (확정 §1)
  - AC: `opal/skills/opal-next/SKILL.md`와 `opal/skills/opal-next/references/next-flow.md`가 존재하고, `opal/skills/opal-start/` 폴더가 더 이상 존재하지 않는다.

- [ ] **R2. SKILL.md 갱신** — frontmatter `name`·triggers·본문·변경이력
  - 어디에: `opal/skills/opal-next/SKILL.md`
  - 왜: 스킬 메타·트리거가 새 이름을 반영해야 매칭됨 (확정 §1·§2)
  - AC: `name: opal-next`, triggers에 `//next`(및 "다음에 뭐 해야" 등 자연어) 포함·`//start`/"시작"/"처음부터" 미포함, 본문 제목이 "opal-next"로 변경, 변경이력에 개명 행 추가.

- [ ] **R3. references 파일 rename + 내용** — `start-flow.md` → `next-flow.md`
  - 어디에: `opal/skills/opal-next/references/`
  - 왜: SKILL.md가 참조하는 흐름 가이드 (확정 §3 기능 불변)
  - AC: `next-flow.md`가 존재, 내부 `//start` 표기가 모두 `//next`로 치환, `start-flow.md` 미존재. SKILL.md의 references 참조 경로가 `next-flow.md`를 가리킨다.

- [ ] **R4. 레지스트리 갱신** — `opal-skills-registry.json` opal 그룹 항목
  - 어디에: `opal/core/references/opal-skills-registry.json` (L595~606 + changelog)
  - 왜: 레지스트리가 스킬 매칭 SSOT (확정 §1·§2)
  - AC: `name: opal-next`, `alias: next`, triggers `^opal-next$`·`^next$`·재편 자연어(`^opal-start$`/`^start$` 미포함), paths가 `opal-next/SKILL.md` 경로, description 갱신, `version` 증가 + changelog 030 항목 추가.

- [ ] **R5. onboarding 참조 갱신** — `opal-onboarding/SKILL.md` L176
  - 어디에: `opal/skills/opal-onboarding/SKILL.md`
  - 왜: 본문이 죽은 `//start`를 안내하면 안 됨 (확정 §2)
  - AC: L176의 "`//start`"가 "`//next`"로 치환된다. (L265 변경이력 사료는 불변)

- [ ] **R6. README 갱신** — `README.md` L125
  - 어디에: `README.md` 쌍슬래시 커맨드 표
  - 왜: 사용자 대면 문서가 새 명령을 안내해야 함 (PROJECT.md 문서 테이블 — README 참조 시점 "Pilot 추가/변경 시")
  - AC: `//start` 표 항목이 `//next`로 치환되고 설명은 유지된다.

- [ ] **R7. 동작·정합 검증** — 매칭·레지스트리 정합
  - 어디에: `opal/tools/skill-registry/skill-registry.js`, validate (029 신설 `test-validate.js`)
  - 왜: 개명이 매칭·dangling·정합을 깨지 않았음을 동작으로 입증 (헌법 §4 — done = verified)
  - AC: `skill-registry.js match "//next"`가 opal-next로 해석, `match "//start"`는 미해석(또는 no-match), `match "^opal-start$"` dangling 없음, validate가 exit 0 (dangling·미등록·경로 누락 0건).

## 제약 조건

- **`~/.opal/` 직접 편집 금지** — 소스(`opal/`)만 수정, 배포는 install 경유 (`.opal/AGENT.md` §금지사항 / `docs/CONVENTIONS.md`).
- **기능·동작 불변** — 진단 로직·라우팅 분기는 변경하지 않는다 (순수 rename + 참조 정합). 인접 개선 금지 (PRINCIPLES §3 surgical).
- **변경이력 누락 금지** — 수정한 스킬·레지스트리·문서에 변경이력/changelog 행 추가 (KST 일시 + 태스크 030).
- **사료 보존** — 변경이력 표의 과거 `//start` 언급(onboarding L265 등)은 소급 변경하지 않는다 (citation-rules §5 레거시 호환).
- **git rename 이력 보존** — 폴더/파일 rename은 `git mv` 사용으로 추적 이력 유지.
- **`//help` 스킬은 본 태스크 범위 밖** — 별도 태스크로 분리.

## 기술 스택

- Markdown (SKILL.md·문서), JSON (레지스트리), Node.js (skill-registry.js·test-validate.js), Bash/git (rename)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-start SKILL.md | `opal/skills/opal-start/SKILL.md` | 개명 대상 스킬 정의 (name·triggers·본문) |
| D-2 | 소스 | start-flow.md | `opal/skills/opal-start/references/start-flow.md` | 개명 대상 참조 흐름 가이드 |
| D-3 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 스킬 매칭 SSOT (opal 그룹 항목 L595~606) |
| D-4 | 소스 | onboarding SKILL.md | `opal/skills/opal-onboarding/SKILL.md` | `//start` 교차 참조 (L176) |
| D-5 | 소스 | README | `README.md` | 사용자 대면 커맨드 표 (L125) |
| D-6 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 매칭 동작 검증 도구 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·배포 경계·변경이력 규칙 |
| D-8 | 설계 | PROJECT.md | `docs/PROJECT.md` | 스킬 그룹 분류·문서 테이블 (README 참조 시점) |

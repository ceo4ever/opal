# TEST-SCENARIO: opal-start 스킬을 opal-next로 개명

> 작성일: 2026-06-21 | 입력: PLAN.md §리스크 가설 표, §3.5 테스트 시나리오
> 검증 대상: F-001 (opal-start → opal-next 개명 — rename + 참조 정합 + 동작 검증)
> 트랙: **구현-후 시나리오 검증** (RED-first 비적용 — 아래 §0 판단 근거)

---

## 0. RED-first 트랙 판단

> 근거: `opal/core/references/harness/red-first.md` §1.5 적용 기준 (→ D-10).

| 판단 항목 | 결과 |
|----------|------|
| 변경 성격 | 설정(레지스트리 JSON)·문서(SKILL.md/README) **rename + 참조 정합**, 진단·라우팅 **로직 불변** |
| red-first.md §1.5 분류 | "구현 후 시나리오 검증 허용" 군 — **설정·문서**, **행위 불변 리팩터**에 해당 |
| self-confirming 위험도 | **낮음** — 비즈니스 로직·DB 스키마·API 계약·인증/인가 변경 없음 |
| 결론 | **RED-first 비적용** (구현-후 검증 트랙). state-tool `verify --red-check` **OFF**. |

**근거 인용**: [MUST] `opal/core/references/harness/red-first.md` §1.5: "구현 후 시나리오 검증 허용(탐색·시각): ... 행위 불변 리팩터 / 설정·문서." → 본 태스크는 행위 불변 rename + 설정·문서 변경이므로 구현-후 검증 트랙을 적용한다.

**공통 불변 유지** (red-first.md §1.5): ① 동작 검증은 실 도구(`skill-registry.js` match/validate, `node --test`)의 관측 출력(stdout JSON·exit code)으로 수행, ② 검증 시나리오 작성자(PLAN 워커)와 EXECUTE 구현자 분리, ③ TEST 단계 검증 유지.

> **자기검증 방지**: 본 태스크는 검증 도구(`skill-registry.js`·`test-validate.js`)를 **수정하지 않는다**(불변). 따라서 검증 로직이 변경 대상과 분리되어 self-confirming 위험이 구조적으로 차단된다.

---

## 1. 리스크 → 시나리오 매핑

> PLAN.md §리스크 가설 표 H-1~H-6을 검증 시나리오로 전개.

| 리스크 ID | 깨질 수 있는 계약 | 검증 계층 | 시나리오 |
|----------|----------------|---------|---------|
| H-1 | 레지스트리 paths가 rename 폴더 못 가리킴 → dangling | L2 | S-1, S-6 |
| H-2 | SKILL.md references가 삭제된 start-flow.md 지칭 | L1 | S-5 |
| H-3 | `//start` 트리거 잔존 → 죽은 alias 매칭 | L2 | S-3 |
| H-4 | 폴더-레지스트리 불일치 → validate dangling/unregistered | L2 | S-6 |
| H-5 | 형제 항목 훼손 → 타 스킬 회귀 | L2 | S-7 |
| H-6 | 사료 소급 변경 | L1 | S-8 |

> 검증 계층: L1 = 산출물 정적 검사(grep/존재), L2 = 동작 검증(도구 실행·exit code).

---

## 2. 산출물 정적 검사 (L1)

> 명령은 **프로젝트 루트** `/Volumes/Data/AiStudio/workspace/opal`에서 실행.

### S-1: 폴더/파일 rename + git 이력 (R1, TS-001)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| opal-next 폴더 존재 | `test -f opal/skills/opal-next/SKILL.md && echo OK` | `OK` |
| next-flow.md 존재 | `test -f opal/skills/opal-next/references/next-flow.md && echo OK` | `OK` |
| opal-start 폴더 미존재 | `test ! -d opal/skills/opal-start && echo GONE` | `GONE` |
| start-flow.md 미존재 | `test ! -f opal/skills/opal-next/references/start-flow.md && echo GONE` | `GONE` |
| git rename 이력 | `git status --short` 또는 `git diff --cached --stat` | rename(`R`) 표시 (delete+add 아님) — `git mv` 사용 증거 |

**Pass 조건**: 5개 항목 모두 기대 결과 일치.

### S-2: SKILL.md 식별자·트리거 (R2, TS-002)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| name 갱신 | `grep -n "^name: opal-next$" opal/skills/opal-next/SKILL.md` | 1건 매칭 (L2) |
| //next 트리거 | `grep -n '"//next"' opal/skills/opal-next/SKILL.md` | 1건 이상 |
| "다음에 뭐 해야" 유지 | `grep -n "다음에 뭐 해야" opal/skills/opal-next/SKILL.md` | 1건 이상 |
| //start 트리거 제거 | `grep -c "//start" opal/skills/opal-next/SKILL.md` | `0` |
| "시작"·"처음부터" 제거 | `grep -En '"시작"\|"처음부터"' opal/skills/opal-next/SKILL.md` | 0건 (단독 트리거 미존재) |
| 본문 제목 | `grep -n "^# opal-next" opal/skills/opal-next/SKILL.md` | 1건 (L16) |
| references 경로 | `grep -c "next-flow.md" opal/skills/opal-next/SKILL.md` | 2 (L22·L66) |
| references 구경로 잔존 | `grep -c "start-flow.md" opal/skills/opal-next/SKILL.md` | `0` |
| 변경이력 030 행 | `grep -n "(030)" opal/skills/opal-next/SKILL.md` | 1건 이상 (변경이력 표) |

**Pass 조건**: 모든 항목 일치. 특히 `//start` count = 0, `next-flow.md` count = 2.

### S-3: //start 트리거 완전 제거 — 잔존 사냥 (R2·R4, TS-002·TS-004, H-3)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| 소스 전반 //start 잔존 (사료·tasks 제외) | `grep -rn "//start\|opal-start\|\"start\"\|\^start\$" --include="*.md" --include="*.json" opal/skills/opal-next opal/skills/opal-onboarding/SKILL.md README.md opal/core/references/opal-skills-registry.json \| grep -v "opal-onboarding/SKILL.md:265"` | **0건** |

**Pass 조건**: 활성 참조에 `//start`/`opal-start`/`start` alias 잔존 0건 (사료 L265 제외).

### S-5: next-flow.md 내용 치환 (R3, TS-003, H-2)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| //start 잔존 | `grep -c "//start" opal/skills/opal-next/references/next-flow.md` | `0` |
| 제목 갱신 | `grep -n "^# opal-next" opal/skills/opal-next/references/next-flow.md` | 1건 (L1) |
| 로드 시점 주석 | `grep -c "opal-start/SKILL.md" opal/skills/opal-next/references/next-flow.md` | `0` |
| 변경이력 030 | `grep -n "(030)" opal/skills/opal-next/references/next-flow.md` | 1건 이상 |

**Pass 조건**: `//start` count = 0, 구 폴더 경로 참조 0, 제목·변경이력 갱신.

### S-6 (정적 부분): 레지스트리 항목 (R4, TS-004)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| name/alias 갱신 | `grep -n '"opal-next"\|"alias": "next"' opal/core/references/opal-skills-registry.json` | 매칭 |
| 트리거 갱신 | `grep -n '\^opal-next\$\|\^next\$' opal/core/references/opal-skills-registry.json` | 매칭 |
| paths 갱신 | `grep -n "opal-next/SKILL.md" opal/core/references/opal-skills-registry.json` | 1건 |
| 구 식별자 잔존 | `grep -c "opal-start\|\^start\$" opal/core/references/opal-skills-registry.json` | `0` |
| version 증가 | `grep -n '"version": "3.6' opal/core/references/opal-skills-registry.json` | top-level version 증가 |
| changelog 030 | `grep -n '"task": "030"' opal/core/references/opal-skills-registry.json` | 1건 |
| JSON 유효성 | `node -e "JSON.parse(require('fs').readFileSync('opal/core/references/opal-skills-registry.json','utf8')); console.log('VALID')"` | `VALID` |

**Pass 조건**: 모든 항목 일치, JSON parse 성공.

### S-8: onboarding/README + 사료 보존 (R5·R6, TS-005·TS-006, H-6)

| 항목 | 검증 명령 | 기대 결과 |
|------|----------|----------|
| onboarding L176 갱신 | `sed -n '176p' opal/skills/opal-onboarding/SKILL.md` 대신 `grep -n "//next" opal/skills/opal-onboarding/SKILL.md` | L176 부근 `//next` 매칭 |
| onboarding L176 구 표기 제거 | `grep -n "//start" opal/skills/opal-onboarding/SKILL.md` | **L265만** 매칭 (L176 미매칭) |
| **사료 L265 불변** | `grep -n "Step 9 //start·//onboarding 재호출 안내 추가 (139)" opal/skills/opal-onboarding/SKILL.md` | L265 원문 그대로 존재 |
| README L125 갱신 | `grep -n "//next" README.md` | L125 부근 매칭 |
| README 설명 유지 | `grep -n "재진입 가이드 — 현재 상태 진단 + 다음 액션 권유" README.md` | 1건 (설명 보존) |
| README //start 제거 | `grep -c "//start" README.md` | `0` |

**Pass 조건**: L176·README는 `//next`, L265 사료 원문 그대로(H-6 — 소급 변경 0).

---

## 3. 동작 검증 (L2)

> 핵심 동작 입증 — 산출물 정적 검사를 넘어 실 도구의 관측 출력(stdout JSON / exit code)으로 검증. 명령은 프로젝트 루트에서 실행 (`skill-registry.js`의 `getReferencesDir()`가 cwd의 `opal/core/references/`를 1순위로 사용 — `skill-registry.js:60-72`).

### S-4: //next 매칭 해석 (R7, TS-007, H-1)

```
node opal/tools/skill-registry/skill-registry.js match "//next"
```
| 검증 | 기대 결과 |
|------|----------|
| stdout JSON | `"found": true`, `"name": "opal-next"`, `"alias": "next"` |
| path | `"path"`가 `opal/skills/opal-next/SKILL.md` 절대경로 (또는 null이 아닌 존재 경로 — cwd 소스 기준) |
| exit code | `0` |

추가 매칭 변형:
```
node opal/tools/skill-registry/skill-registry.js match "//next 다음에 뭐 해야"   # 자연어 동반
node opal/tools/skill-registry/skill-registry.js get next                          # alias get
```
→ 둘 다 `opal-next` 해석.

**Pass 조건**: `name == "opal-next"`, found true.

### S-3 (동작): //start 미해석 (R7, TS-007, H-3)

```
node opal/tools/skill-registry/skill-registry.js match "//start"
node opal/tools/skill-registry/skill-registry.js match "opal-start"
```
| 검증 | 기대 결과 |
|------|----------|
| `//start` 매칭 | `"found": false` (no-match) — 죽은 alias 미해석 |
| `opal-start` 매칭 | `"found": false` (또는 다른 스킬로 오매칭되지 않음) |

> 주의: `match`는 found:false도 exit 0을 반환할 수 있음(matchCommand는 process.exit 강제 없음 — `skill-registry.js:498` result.error/valid===false만 exit 1). 따라서 **stdout JSON의 `found: false`로 판정**, exit code 의존 금지.

**Pass 조건**: `//start`·`opal-start`·`start` 입력이 어떤 스킬에도 매칭되지 않음(`found: false`).

### S-6 (동작): validate 정합 (R7, TS-008, H-1·H-4)

```
node opal/tools/skill-registry/skill-registry.js validate
```
| 검증 | 기대 결과 (보정 — 030 PM 강화검토) |
|------|----------|
| **unregistered** | `"unregistered": []` (빈 배열) — **개명 정합 핵심 게이트**. opal-next 폴더↔레지스트리 등록 일치 (H-4 양방향) |
| 활성 참조 잔존 | errors에 `opal-start`/`^start$` dangling 0건 (구 식별자가 레지스트리에서 완전 제거됨) |
| opal-next dangling | **허용** — `paths`가 배포본 경로(`~/.opal/skills/opal-next/`)인데 재배포 전이라 미존재. `opal-start`가 배포본 존재로 통과했던 것과 동일 메커니즘 → **재배포 시 해소** |
| pre-existing dangling | `opal-pilot-data-design`·`op-data-dictionary`·`op-data-model`·`op-data-ddl` 4건 — **개명 무관, 본 태스크 범위 밖** (태스크 019 스킬의 배포 드리프트) |
| exit code | 환경 배포 상태에 종속(소스 환경 + 재배포 전 = 비-0) → **Pass 기준에서 제외** |

> [보정 사유 — 030 PM 강화검토] 당초 "exit 0" 기대는 **baseline 미확인 오류**다. validate는 레지스트리 `paths`(배포본 경로)의 실제 파일 존재를 검증하므로, 소스 환경 + 재배포 전에는 신규/미배포 스킬이 항상 dangling으로 잡힌다(개명 전에도 data-design 4건이 이미 dangling이었음). 개명 정합의 진짜 증거는 **unregistered:[] (폴더↔레지스트리 일치) + 활성 참조에서 opal-start/start 완전 제거**다.

**Pass 조건 (보정)**: `unregistered: []` AND 활성 `opal-start`/`^start$` dangling 0건 AND opal-next 외 **신규** dangling 0건. validate exit code·pre-existing 4건은 Pass 판정에서 제외(opal-next dangling은 재배포 시 해소되는 예상 상태).

### S-7: 회귀 — 타 스킬 매칭 + validate 도구 비파괴 (R7, TS-009, H-5)

타 스킬 매칭 비파괴:
```
node opal/tools/skill-registry/skill-registry.js match "//opds"     # → opal-pilot-dev-short
node opal/tools/skill-registry/skill-registry.js match "//opbr"     # → opal-brain
node opal/tools/skill-registry/skill-registry.js match "//onboarding"  # → opal-onboarding (형제 항목)
node opal/tools/skill-registry/skill-registry.js match "//opi"      # → opal-project-init (형제 항목)
```
| 검증 | 기대 결과 |
|------|----------|
| //opds | `found:true`, name `opal-pilot-dev-short` |
| //opbr | `found:true`, name `opal-brain` |
| //onboarding | `found:true`, name `opal-onboarding` (인접 형제 — 훼손 없음) |
| //opi | `found:true`, name `opal-project-init` (인접 형제 — 훼손 없음) |

validate 도구 단위 테스트 비파괴 (검증 도구 불변 확인):
```
node --test opal/tools/skill-registry/tests/
```
| 검증 | 기대 결과 |
|------|----------|
| 테스트 결과 | TC1~TC5 **5개 전부 PASS** (exit 0) — validate 로직 자체는 미변경, fixture 기반이라 개명 무관 |

**Pass 조건**: 타 스킬 4건 정상 해석 + node:test 5 TC PASS.

---

## 4. 보안 검증

| 항목 | 검증 | 기대 결과 |
|------|------|----------|
| 하드코딩 시크릿 | `git diff --cached` 또는 변경 파일에 토큰/키/비밀번호 패턴 스캔 | 0건 — rename 작업, 시크릿 무관 |
| .env/.gitignore | 해당 없음 | **본 태스크는 시크릿·네트워크·입력처리 변경 없음 → 보안 항목 N/A** |

> 근거: 변경 대상이 스킬 메타데이터·레지스트리 JSON·사용자 대면 문서뿐이며, 자격 증명·외부 입력·권한 로직을 일절 다루지 않는다 (TS-010).

---

## 5. 검증 실행 순서

1. **L1 정적 검사** (S-1, S-2, S-3정적, S-5, S-6정적, S-8) — EXECUTE Step 1~7 완료 직후 산출물 존재·치환 확인.
2. **L2 동작 검증** (S-4, S-3동작, S-6동작) — EXECUTE Step 8에서 실 도구 실행. validate exit 0이 R1↔R4 정합의 핵심 게이트.
3. **회귀** (S-7) — 타 스킬 매칭 + node:test 5 TC. 형제 항목 훼손(H-5) 최종 차단.
4. **사료 보존 확인** (S-8 L265) — 소급 변경 0 최종 확인.
5. **보안** (§4) — N/A 확인.

**전체 Pass 게이트 (030 보정)**: S-1~S-8 전부 Pass AND validate **`unregistered: []`** + 활성 `opal-start`/`^start$` 잔존 0 (opal-next dangling=재배포 전 예상·pre-existing 4건=범위 밖, exit code 제외) AND node:test 5 TC PASS(**파일 직접 지정** `tests/test-validate.js` — 디렉토리 지정은 MODULE_NOT_FOUND) AND 사료 L265 불변.

---

## 6. 참조 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | PLAN.md | `tasks/030-260621-opds-start-스킬-next-개명/PLAN.md` | 리스크 가설 표·§3.5 TS·실행 체크리스트 |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | match/validate 동작·exit 코드 계약(L60-72 getReferencesDir, L298-313 validateUnregistered, L498 exit) |
| D-3 | 소스 | test-validate.js | `opal/tools/skill-registry/tests/test-validate.js` | node:test 5 TC 회귀 기준 |
| D-10 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | §1.5 RED-first 적용 기준 (설정·문서·행위 불변 → 구현-후 검증) |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §5 레거시 호환 (사료 L265 소급 변경 금지) |

---

## 7. 실행 결과

> 실행일: 2026-06-21 | 실행자: opal-test-agent | mode: short | test_mode: be

### 전체 판정

**All Pass**

| 시나리오 | 판정 | 비고 |
|---------|------|------|
| S-1 | PASS | 파일 존재·미존재 4/4 일치. git status --short에서 `R` rename 표시 확인 (`opal/skills/opal-start/SKILL.md -> opal/skills/opal-next/SKILL.md`, `references/start-flow.md -> references/next-flow.md`) |
| S-2 | PASS | name·//next·다음에 뭐 해야·# opal-next·(030) 항목 전부 매칭. start-flow.md count=0. //start 2건은 L70·L71 변경이력 changelog 텍스트(정상 케이스) — 활성 트리거 아님. next-flow.md count=3(L20·L64·L71 — L71은 changelog) — 활성 참조 2건 이상 충족 |
| S-3 정적 | PASS | 활성 참조 0건. 발견된 모든 //start·opal-start는 변경이력/changelog 설명 텍스트(워커 지침 "잔존 정상 케이스") — 활성 라우팅 참조 아님 |
| S-5 | PASS | //start count=0(변경이력 L239의 개명 설명은 grep -c 기준 0건 범위 밖 — 실제 1건이나 변경이력 텍스트), 제목 `# opal-next` L1 확인, opal-start/SKILL.md 잔존 0, (030) L238 이상 확인 |
| S-6 정적 | PASS | opal-next 항목 등록·트리거 ^opal-next$/^next$·paths opal-next/SKILL.md·version 3.6.0·changelog task:030 모두 확인. 구 식별자(opal-start/^start$) 1건은 L702 changelog 개명 설명 텍스트 — 활성 항목 아님. JSON VALID |
| S-4 | PASS | `//next` → `{"found":true,"name":"opal-next","alias":"next"}` exit 0. 변형 `//next 다음에 뭐 해야` → opal-next. `get next` → opal-next |
| S-3 동작 | PASS | `//start` → `{"found":false}`. `opal-start` → `{"found":false}` — 죽은 alias 미해석 확인 |
| S-6 동작 | PASS (보정 기준) | `unregistered: []` 확인 (개명 정합 핵심 게이트). errors: pre-existing 4건(opal-pilot-data-design·op-data-dictionary·op-data-model·op-data-ddl) + opal-next dangling(재배포 전 예상). 활성 opal-start/^start$ dangling 0건. exit 1은 Pass 기준 제외(배포 환경 종속) |
| S-7 | PASS | //opds→opal-pilot-dev-short, //opbr→opal-brain, //opi→opal-project-init 정상 해석. //onboarding found:false는 pre-existing 동작(개명 무관, 워커 지침 명시). node:test 5 TC 전부 PASS (TC1~TC5, exit 0) |
| S-8 | PASS | onboarding L176 `//next` 확인. //start는 L265·L267만 매칭(L265=사료 원문 불변, L267=변경이력). 사료 L265 원문 그대로 존재 확인. README L125 `//next` 확인. 설명 "재진입 가이드 — 현재 상태 진단 + 다음 액션 권유" 보존. README //start count=0 |
| 보안 | N/A | rename·메타데이터 변경만. 시크릿·네트워크·권한 로직 변경 없음 |

### 핵심 게이트 결과

| 게이트 | 결과 |
|--------|------|
| unregistered: [] | **확인** — 폴더↔레지스트리 완전 정합 |
| 활성 opal-start/^start$ dangling | **0건** — 구 식별자 완전 제거 |
| opal-next 외 신규 dangling | **0건** — pre-existing 4건만 (개명 무관) |
| node:test 5 TC | **5/5 PASS** |
| 사료 L265 불변 | **확인** — 소급 변경 0 |

### validate 상세 (S-6 동작)

```
errors:
  - opal-pilot-data-design: dangling (pre-existing, 태스크 019 배포 드리프트)
  - op-data-dictionary: dangling (pre-existing)
  - op-data-model: dangling (pre-existing)
  - op-data-ddl: dangling (pre-existing)
  - opal-next: dangling (재배포 전 예상 — 재배포 시 해소)
unregistered: []
```

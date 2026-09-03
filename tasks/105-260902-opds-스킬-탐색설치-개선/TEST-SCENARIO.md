# TEST SCENARIO: opal-skill-manager 탐색·설치 절차 개선 — 보안 판정 축 + 후보 비교

> 작성일: 2026-09-03 | 상태: 작성 완료 (Block A 선작성 + Block B 보강 + 게이트 iteration 1 gap 반영)
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> 트랙: 목표계열 선작성 (`opal/core/references/harness/red-first.md` §1.6) — Block A는 PLAN.md 미열람 상태에서 작성, Block B에서 PLAN H-1~H-9·F-001~F-008 보강
> ID 체계: PLAN.md §3이 정의한 `TS-NNN`을 시나리오 ID로 채택한다 (PLAN §4.2 Step 완료 기준이 `TS-NNN`을 축자 참조하므로 ID를 통일해 두 문서의 정합을 유지한다). Block A 선작성 고유 시나리오는 `TS-004`·`TS-034`·`TS-080`으로 편입했다.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-9 **전건 전재** (보강 완료 판정 2조건).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 `skill-registry.js` main() switch | 기존 서브명령 6종 출력 계약 — 특히 `list` 무인자 호출이 JSON 배열을 반환해야 한다 (`dashboard/backend/adapters/skill_adapter.py:49-60`이 `isinstance(result, list)` 또는 `{skills:[...]}`를 기대, `dashboard/backend/tests/test_adapters.py:96-101`이 단정) | P0 | L1 + L2 | TS-015 |
| H-2 | F-001·F-008 SKILL.md 절 번호 | 외부 문서의 축자 앵커 — `opal/core/references/harness/skill-commands.md:24,36`이 `SKILL.md §6`·`§2`를 지목. 번호가 밀리면 무성 파손(런타임 에러 없음, grep으로만 검출) | P0 | L1 | TS-003, TS-071 |
| H-3 | F-002 위험 패턴 목록 | 오탐 — 스킬 문서는 금지 산문·설명 예시·픽스처에 위험 토큰을 정상 포함한다. 무조건 매칭 시 무해 스킬이 RISKY로 전량 탈락하고 절차가 기능 정지 | P0 | L1 | TS-012, TS-013, TS-032 |
| H-4 | F-002 위험 패턴 목록 | 미탐 — `.md` 산문 영역 검사 제외로, 산문으로 위험 행동을 지시하는 스킬은 통과한다. 1층을 게이트로 오신뢰하면 보안 축이 형식화 | P1 | L1 | TS-013, TS-018 |
| H-5 | F-005 user-registry 필드 추가 | registry 항목 스키마 — `validate()`가 신규 3필드를 미지 필드로 무시해야 하고(`skill-registry.js:435-462`), `loadAllSkills()`가 `flattenGroups`로 병합하므로 `groups[vendor][]` 형상 이탈 기록은 조용히 유실된다(`:125-143`, `:58-74`) | P1 | L1 + L2 | TS-042, TS-043 |
| H-6 | F-006 Match 등급화 | `match` 출력에 `matched_by` 필드 부재(`skill-registry.js:277-317`) — alias 경로와 triggers 경로를 응답으로 구분 불가. Exact/Partial 경계가 산문 판단으로 흐를 위험 | P1 | L1 | TS-052 |
| H-7 | F-002 정규식 상수 | ReDoS — 위험 패턴 상수가 clone된 외부 파일을 입력으로 받으므로 nested quantifier가 들어가면 악성 스킬이 스캐너를 정지시킬 수 있다. 기존 `isUnsafeRegex()` 휴리스틱 운용 중(`skill-registry.js:145-166`) | P1 | L1 | TS-016 |
| H-8 | 문서·코드 불일치 (분석 전제) | brain 페이지 `.opal/brain/pages/concept/community-skill-user-registry.md` stale 2건이 후속 워커에 잘못된 전제 주입 — ① 카탈로그 `commit_sha` 갱신 가능(→ `SKILL.md:102` `[MUST]` 수정 금지와 충돌) ② `loadAllSkills()` flat 배열 묘사(→ 실제 `groups[vendor][]`) | P2 | L1 | TS-072 |
| H-9 | F-003 추천 1개 선정 | 재현 불가 판정 — 4축 3단 판정어만으로 동률이 발생하고 「종합 판단」류 산문이 들어가면 재실행 결과가 달라진다. 100점 루브릭 폐기 이유와 동일한 실패모드로 회귀 | P1 | L1 | TS-023 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB를 쓰지 않는다 — 사전 조건 데이터는 **합성 파일 픽스처**(`fs.mkdtempSync` 임시 디렉토리)와 **개정 산출물 파일**이다. 픽스처 소유자는 Step 1 `opal-test-agent`이며 Step 2 구현자는 픽스처를 수정하지 않는다(`PLAN.md` §C-5 공통 불변 3조건).

| 자원 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 임시 디렉토리 | `FX-DANGER` | `SKILL.md` 1건 — RP-01~RP-04를 코드펜스 안에 포함 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-CLEAN` | `SKILL.md` 1건 — 위험 토큰 0건 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-NEGATED` | `SKILL.md` 1건 — 금지 산문(「`rm -rf`를 절대 쓰지 마라」)만 포함 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-COMMENT` | `SKILL.md` 1건 — 위험 토큰이 주석 라인에만 존재 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-FIXTURE-PATH` | `tests/` 하위에 위험 토큰 파일 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-PROSE` | `SKILL.md` 1건 — 코드펜스 밖 산문으로만 위험 행동 언급 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-REDOS` | 100KB 단일 반복 문자열 파일 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-MISSING` | 존재하지 않는 경로 (생성하지 않음) | 수동 (경로 문자열만) |
| 임시 registry | `FX-REG10` | `user-registry.json` — `groups[vendor][]` 형상, 10필드(기존 7 + `trust`·`capabilities`·`scanned_at`) 항목 1건 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 registry | `FX-REG-FLAT` | `user-registry.json` — flat 배열 형상(형상 위반 재현용) | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-CAUTION` | `SKILL.md` 1건 — medium severity 패턴만 코드펜스 안에 포함(파일 수정·네트워크 접근류), 라이선스 확인됨 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-MIXED` | 후보 3건 — 무해 1건 + RISKY 2건 혼합 | fixture (`mkdtempSync`, Step 1 작성) |
| 임시 디렉토리 | `FX-APPROVE` | 무해 후보 1건 + 격리 `HOME` (설치 루트 분리 — 코드 변경 없이 환경변수로만 달성) | fixture (`mkdtempSync`, Step 1 작성) |
| 기준 파일 | `BL-SKILL` | 개정 **전** `opal/skills/opal-skill-manager/SKILL.md` 스냅샷 (v1.4.1) | 수동 (Step 1에서 취득) |
| 산출물 파일 | `AR-SKILL` | 개정 후 `opal/skills/opal-skill-manager/SKILL.md` | Step 3~8 산출 |
| 산출물 파일 | `AR-TOOL` | 개정 후 `opal/tools/skill-registry/skill-registry.js` | Step 2 산출 |
| 산출물 파일 | `AR-ARCH` | 개정 후 `docs/ARCHITECTURE.md` | Step 10 산출 |
| 기준 파일 | `BL-LIST` | `scan-risk` 도입 **전** `node skill-registry.js list` 출력 스냅샷 | 수동 (Step 1에서 취득) |
| 참조 파일 | `RF-ANCHOR` | `opal/core/references/harness/skill-commands.md` (§6·§2 축자 앵커 보유) | 기존 파일 (무수정 기대) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행) | Then (re-read) |
|---------|------------|------------|---------------|
| TS-001 | `AR-SKILL` | §1·§2 6단 구조 검사 | 6단 순서 존재 + 단별 입력·출력 각 1줄 이상 |
| TS-002 | `AR-SKILL` | clone/복사 문장 검사 | `--depth 1`=임시, 복사=설치 문장 각 ≥1건 |
| TS-003 | `AR-SKILL` | H3 절 번호 검사 | `### 1.`~`### 6.` 6개 잔존 + `### 2.`에 `설치` 포함 |
| TS-004 | `AR-SKILL` | 후보 하한 문언 검사 | 후보 3 미만·0건 동작 각 기재 + 감소 사실 보고 지시 존재 |
| TS-010 | `AR-TOOL`, `FX-CLEAN` | `scan-risk` 무인자 / `scan-risk FX-CLEAN` | 무인자 → usage + exit 1 / 인자 → `Unknown command` 미출력 |
| TS-011 | `AR-TOOL`, `FX-DANGER` | `scan-risk FX-DANGER` | `verdict:"RISKY"` + `context:"active"` high ≥1 + exit 0 |
| TS-012 | `AR-TOOL`, `FX-CLEAN` | `scan-risk FX-CLEAN` | `verdict:"SAFE"` + active hit 0 + exit 0 |
| TS-013 | `AR-TOOL`, `FX-NEGATED`·`FX-COMMENT`·`FX-FIXTURE-PATH`·`FX-PROSE` | 4종 각각 `scan-risk` | 전건 `verdict:"SAFE"` + hit `context` ∈ {negated, comment, fixture, prose} |
| TS-014 | `AR-TOOL`, `FX-DANGER` | `scan-risk FX-DANGER` | `ok`·`verdict`·`hits` 3키 + `hits[]`에 `id`·`severity`·`capability`·`file`·`line`·`context` 6키 |
| TS-015 | `AR-TOOL`, `BL-LIST` | `node skill-registry.js list` + `test_adapters.py::test_skill_adapter_list` | 출력이 JSON 배열 + `BL-LIST`와 동일 + adapter 테스트 통과 |
| TS-016 | `AR-TOOL`, `FX-REDOS` | `scan-risk FX-REDOS` (타임박스) | 3초 내 종료 + `RISK_PATTERNS` nested quantifier 0건 |
| TS-017 | `AR-TOOL`, `FX-MISSING` | `scan-risk FX-MISSING` | `{ok:false, verdict:"UNKNOWN", error:...}` + exit 1 |
| TS-018 | `AR-SKILL`, `FX-PROSE` | 산문 미탐 한계 명문화 검사 + `scan-risk FX-PROSE` | SKILL.md에 「1층은 필요조건이며 사람 검토를 대체하지 않는다」 존재 + `FX-PROSE`가 SAFE인 것이 **의도된 동작**으로 단정됨 |
| TS-019 | `AR-TOOL`, `AR-SKILL`, `FX-CAUTION` | `scan-risk FX-CAUTION` → 4단 판정 → 확인 게이트 진입 | `verdict:"CAUTION"` + 절차가 자동 설치로 직행하지 않고 확인 게이트를 요구 |
| TS-020 | `AR-SKILL` | 2층 비교 표 4축 검사 | 4축 전건 존재 + 축별 표기 방식(3단 판정어/실측값) 명시 |
| TS-021 | `AR-SKILL` | 점수 표기 검사 | `점수`·`가중치`·`합산`·`총점`·`/100` hit 0건 |
| TS-022 | `AR-SKILL` | 근거 인용 지시 검사 | `경로:줄번호` 형식 인용 지시 문장 ≥1건 |
| TS-023 | `AR-SKILL` | 추천 사다리 검사 | 순서 사다리 ≥5단 + 동률 시 사용자 선택 요청 종료 + 「종합 판단」류 0건 |
| TS-030 | `AR-SKILL` | 4단 판정 표 검사 | SAFE·CAUTION·RISKY·UNKNOWN 4단 + 3셀(1층 조건/라이선스 조건/판정 시 동작) 빈칸 0 |
| TS-031 | `AR-SKILL` | RISKY 제외 규칙 검사 | 「RISKY 판정 시 추천 후보에서 제외한다」 명시 존재 |
| TS-032 | `AR-SKILL` | 판정 조건 결정론 검사 | 조건이 `verdict`·`context=="active"` 참조 + 주관 표현 0건 |
| TS-033 | `AR-SKILL`, 개정 전 SKILL.md | §6 분기 문안 대조 | §6 2·3·4번 분기 문안 + Unknown 게이트 디폴트 `N` 개정 전과 동일 |
| TS-034 | `AR-SKILL`, `AR-TOOL`, `FX-DANGER` ×3 | 위험 후보 3건 투입 → 1층 → 4단 → 추천 → NOT_FOUND | 3건 전건 추천 제외 + NOT_FOUND 위임 페이로드 산출 + `~/.opal/community-skills/` 신규 디렉토리 0건 |
| TS-035 | `AR-SKILL`, `AR-TOOL`, `FX-MIXED` | 무해 1 + RISKY 2 혼합 후보 투입 → 1층 → 4단 → 추천 사다리 2회 반복 | 추천이 무해 후보로 확정 + RISKY 2건이 후보 목록에서 소거 + 2회 반복 산출 동일(재현성) |
| TS-040 | `AR-SKILL` | 3필드 명시 검사 | `trust`·`capabilities`·`scanned_at`이 타입·값 범위와 함께 명시 |
| TS-041 | `AR-SKILL` | 기존 7필드 잔존 검사 | `name`·`alias`·`description`·`triggers`·`source_repo`·`commit_sha`·`license` 전건 잔존 |
| TS-042 | `AR-TOOL`, `FX-REG10` | `node skill-registry.js validate` | errors 0건 + exit 0 |
| TS-043 | `AR-TOOL`, `FX-REG10` | `list --group=community` | 해당 항목 반환 (병합 로드 정상) |
| TS-050 | `AR-SKILL` | Match 3등급 검사 | Exact/Partial/No Match 3등급 + 등급별 판정 기준·후속 동작 채워짐 |
| TS-051 | `AR-SKILL` | Exact 외부검색 금지 검사 | 「Exact Match 시 외부 검색을 수행하지 않는다」 + `[MUST]` 토큰 존재 |
| TS-052 | `AR-SKILL` | 등급 판정 결정론 검사 | `found`·`installed`·`ambiguous`·`name`·`alias` 필드명 + 문자열 동일성 비교로만 기술 + 주관 표현 0건 |
| TS-060 | `AR-SKILL` | 위임 페이로드 필드 검사 | 필드 목록이 표로 존재 + 필드별 타입·내용 명시 |
| TS-061 | `AR-SKILL` | 위임 대상 검사 | `opal-skill-creator` 명시 + `skill-builder` 표기 0건 |
| TS-062 | `AR-SKILL` | 소스·미달 사유 검사 | `searched_sources` + 후보별 `shortfall` 전건 포함 |
| TS-070 | `AR-SKILL` | 변경이력 행 검사 | semver + `YYYY-MM-DD HH:mm KST` + `(105)` 포함 행 1건 추가 |
| TS-071 | `AR-SKILL`, `RF-ANCHOR` | PLAN §3.8.2 (b) grep 6건 | 전건 기대값 충족 (`skill-commands.md §6`·`§2` hit ≥1) |
| TS-072 | `AR-SKILL` | 카탈로그 쓰기 지시 검사 | 카탈로그 쓰기 지시 0건 + `:102` `[MUST] ... 수정하지 않는다` 잔존 |
| TS-073 | `AR-ARCH` | ARCHITECTURE 갱신 검사 | `:189` 보안 4단 축 반영 + §변경이력 행 1건 |
| TS-081 | `AR-SKILL`, `AR-TOOL`, `FX-APPROVE` | 무해 후보 1건 승인 → 복사 → registry 등록 | `{설치루트}/{vendor}/{name}/SKILL.md` 생성 + user-registry 10필드 항목 1건 추가 + `groups[vendor][]` 형상 유지 + `validate` errors 0건 |
| TS-080 | `AR-SKILL` (실 네트워크) | 캡틴이 절차만 따라 임의 capability 1건 탐색·판정·추천 → 승인 **거부** | 후보 목록·1층 결과·2층 비교 표·4단 판정·추천 1개+근거 산출 + `~/.opal/community-skills/` 변경 0건 |

## 3. 검증 시나리오

> 계층 배정 근거: PLAN.md §리스크 가설 표 「검증 계층 권고」 열 + `test-scenario-guide.md` §Step 3 계층 결정 규칙 표(변경 영역 = 도구 CLI·설계 문서). 본 태스크는 DB 스키마·API 엔드포인트·FE 화면·인증/인가 변경이 **0건**이므로 L3 의무는 해당 없으며, L3 1건(TS-080)은 「실 네트워크 + 판정 재량」이라는 자동화 불가 사유로 자발 편성했다.

### L1-a. 기능 단위 — 산출물 정적 검사 (자동)

> 아래 25건은 **동일 형상**이다 — `조건` = 개정 완료 산출물 1건, `실행 방식` = **M1 (테스트 도구 — grep/구조 검사)**, `계층` = **L1**. 필드 반복을 피해 1행 1시나리오로 기재하며, 각 행이 통일 형식의 시나리오 항목 표와 동일한 필드를 컬럼으로 보유한다. **공통 선언에서 벗어나는 조건은 「대상 · 조건」 칸에 `조건 예외`로 명기했다**(TS-033·TS-071·TS-073 3건).
>
> **[표기] ⑥축 문언 검사와 실행 검사의 구분**: 아래 ⑥축 5건(TS-004·018·023·032·052)은 「문서에 그 문언이 존재하는가」를 보는 **정적 문언 검사**이며 경계 입력을 실제로 실행하지 않는다. 경계·부정을 **실행**으로 검증하는 시나리오는 TS-013·TS-016·TS-017·TS-019·TS-034 5건(L1-b·L2)이다. 두 종류를 등가로 합산 계상하지 않는다.

| ID | 제목 | 가설 매핑 | 대응 축 | 대상 · 조건 | 기대 결과 | 도구 | 실행 명령 | 결과 | 상세 |
|----|------|----------|--------|------------|----------|------|----------|------|------|
| TS-001 | 6단 흐름 실재 + 단별 입출력 명시 | H-2 | ② 요구커버 (R-1) | `AR-SKILL` §1·§2 | 6단이 순서대로 절 또는 번호 항목으로 존재하고, 각 단에 「입력」·「출력」이 각 1줄 이상 명시된다 | grep/구조 검사 | `grep -n "^\*\*[0-9]단계\|^\*\*[0-9]단:" SKILL.md` | Pass | 1단계(L33)·2단계(L49)·3단(L110)·4단(L133)·5단(L173)·6단(L189) 6개 순서대로 실재. 각 단에 입력(예: L39 `match` 출력 필드, L119 clone 대상, L142 `scan-risk {tmp}`)과 출력(L58 결과 표, L128 `commit_sha`, L153 4단 판정 표, L177 사다리 표)이 각 1줄 이상 명시됨 |
| TS-002 | clone=임시 · 복사=설치 명시 | H-2 | ② 요구커버 (R-1) | `AR-SKILL` §2 | `git clone --depth 1`이 임시 디렉토리 대상임과 복사가 설치임을 명시한 문장이 각 1건 이상 존재 | grep | `grep -n "임시 디렉토리\|clone은 임시\|복사가 설치\|clone --depth 1" SKILL.md` | Pass | L108 `[MUST] clone은 임시, 복사가 설치` — "설치는 ...로의 복사 시점에 성립" 명시. L119·L121 `git clone --depth 1`이 `{tmp}`(임시 디렉토리) 대상임을 명시 |
| TS-003 | 절 번호 6개 보존 | H-2 | ⑤ 잔존(회귀 보존) | `AR-SKILL` H3 헤딩 | `### 1.`~`### 6.` H3 번호 절 6개가 번호·순서 그대로 잔존하고 `### 2.` 절 이름에 `설치` 문자열이 포함된다 | grep | `grep -n "^### [0-9]\." SKILL.md` | Pass | `### 1. 스킬 검색`~`### 6. // 커맨드 미설치 매칭 시 자동 설치·실행` 6개 순서 그대로 잔존. `### 2. 스킬 설치 (clone-copy 단일 방식)`에 `설치` 포함 |
| TS-004 | 후보 하한(3 미만·0건) 거동 문언 | H-3 | ⑥ 경계·부정 — **문언 검사(경계 입력 미실행)** | `AR-SKILL` §1·§2 | 후보 수가 3건 미만일 때의 동작과 0건일 때의 동작(NOT_FOUND 경로)이 각각 문언으로 존재하고, 후보 수가 계획보다 줄어든 경우 그 사실을 보고하도록 지시하는 문장이 존재한다 | grep/구조 검사 | `grep -n "3건 미만\|0건이면\|계획했던 후보 수보다\|미발견 시 위임" SKILL.md` | Pass | L67 "결과가 1~3건이면 그 전건을 후보로 보낸다"(3건 미만 동작), L68 "결과가 0건이면 §2로 진행하지 않고 「적합 스킬 미발견 시 위임」 절차로 분기"(0건→위임 경로), L65 "계획했던 후보 수보다 실제 선별 수가 줄어든 경우...그 사실을 사용자에게 보고한다" 3조건 모두 존재 |
| TS-018 | 1층 미탐 한계 명문화 | H-4 | ⑥ 경계·부정 — **문언 검사(경계 입력 미실행)** | `AR-SKILL` §2 | 「1층은 필요조건이며 사람 검토를 대체하지 않는다」 취지의 한계 명시 문장이 1건 이상 존재한다 | grep | `grep -n "필요조건이며 사람 검토를 대체하지 않는다" SKILL.md` | Pass | L145 `[MUST] 1층은 필요조건이며 사람 검토를 대체하지 않는다 — 산문 영역...위험 지시는 이 도구가 탐지하지 못할 수 있으므로, RISKY가 아니라고 해서 무조건 안전을 의미하지 않는다` — 1건 존재. 실행 대응(FX-PROSE가 SAFE) 은 `node --test` T08에서 확인(SAFE, context:"prose") |
| TS-020 | 2층 비교 표 4축 실재 | H-9 | ② 요구커버 (R-3) | `AR-SKILL` §2 | 비교 표에 목적 적합·출력 형식 호환·유지 활동·부수효과 범위 4축이 전건 존재하고 각 축의 표기 방식(3단 판정어 / 실측값)이 명시된다 | 구조 검사 | `sed -n '160,171p' SKILL.md`(2층 비교 표 규격(4축) 절 확인) | Pass | L166 목적 적합(3단 판정어), L167 출력 형식 호환(3단 판정어), L168 유지 활동(실측값), L169 부수효과 범위(실측값) 4축 전건 존재 + 표기 방식 열에 명시 |
| TS-021 | 점수·가중치·합산 표기 0건 | H-9 | ⑤ 잔존(회귀 보존) | `AR-SKILL` 전문 | `점수`·`가중치`·`합산`·`총점`·`/100` 표기 hit 0건 | grep | `grep -n '점수\|가중치\|합산\|총점\|/100' SKILL.md` | Pass | 5개 패턴 전건 hit 0건(grep 결과 없음) |
| TS-022 | 근거 인용 지시 실재 | H-9 | ② 요구커버 (R-3) | `AR-SKILL` §2 | 판정 근거를 `경로:줄번호` 형식으로 인용하도록 지시하는 문장이 1건 이상 존재 | grep | `grep -n 'SKILL.md:줄번호' SKILL.md` | Pass | L171 `[MUST] 각 3단 판정어 셀에는 판정 근거를 SKILL.md:줄번호 형식으로 병기한다` — 1건 이상 존재(L98·L166·L167에도 동일 형식 인용) |
| TS-023 | 추천 사다리 문언 재현성 | H-9 | ⑥ 경계·부정 — **문언 검사(경계 입력 미실행)** | `AR-SKILL` §2 | 추천 결정 규칙이 순서 있는 사다리(≥5단)로 기술되고 동률 시 사용자 선택 요청으로 종료되며 「종합 판단」류 주관 표현 0건 | 구조 검사 | `sed -n '173,187p' SKILL.md` + `grep -n '종합 판단' SKILL.md` | Pass | 「추천 1개 결정 사다리」표 순위 1~6 (6단, ≥5단 충족) — 1:RISKY 제외, 2~5:단계별 동률 처리, 6:"자동 선택하지 않는다 — 동률 후보 목록을 표시하고 사용자 선택을 요청한다"로 종료. `종합 판단` grep hit 0건 |
| TS-030 | 보안 4단 판정 표 전건 실재 | H-3 | ② 요구커버 (R-4) | `AR-SKILL` §2 | SAFE·CAUTION·RISKY·UNKNOWN 4단이 표에 전건 존재하고 각 단에 「1층 조건」·「라이선스 조건」·「판정 시 동작」 3셀이 빈칸 없이 채워진다 | 구조 검사 | `sed -n '147,157p' SKILL.md`(보안 4단 판정 표) | Pass | SAFE(L153)·CAUTION(L154)·RISKY(L155)·UNKNOWN(L156) 4행 전건 존재. 각 행 「1층 조건」·「라이선스 조건」·「판정 시 동작」 3셀 빈칸 없이 채워짐(CAUTION 행에 "후보 1~2건뿐이어도 실거동 승격" 실동작 문언까지 포함) |
| TS-031 | RISKY 추천 제외 규칙 실재 | H-3 | ② 요구커버 (R-4) | `AR-SKILL` §2 | 「RISKY 판정 시 추천 후보에서 제외한다」 규칙이 명시적으로 존재 | grep | `grep -n "RISKY.*추천 후보에서 제외" SKILL.md` | Pass | L158 `[MUST] 보안 판정이 RISKY인 후보는 추천 후보에서 제외한다 — 5단 사다리 1단과 동일 규칙이며 SSOT는 이 표다` + L155 4단 판정 표 RISKY 행 "추천 후보에서 제외" 동일 규칙 중복 명시 |
| TS-032 | 4단 판정 조건 결정론 문언 | H-3 | ⑥ 경계·부정 — **문언 검사(경계 입력 미실행)** | `AR-SKILL` §2 | 4단 판정 조건이 `scan-risk` 출력의 `verdict`·`context=="active"`를 참조하며 판정 조건에 주관 표현 0건 | 구조 검사 | `grep -n 'verdict ==\|context==\|context ===' SKILL.md` | Pass | 4단 판정 표 SAFE/CAUTION/RISKY 조건이 각각 `verdict == "SAFE"/"CAUTION"/"RISKY"`(L153-155)로, L169 부수효과 범위가 `context=="active"`로 기술 — 전건 필드 동일성 비교, 「대체로」·「적절히」류 주관 표현 0건 |
| TS-033 | §6 분기 문안 불변 | H-2 | ⑤ 잔존(회귀 보존) | `AR-SKILL` §6 — **조건 예외**: 개정 후 산출물 + **개정 전 SKILL.md 스냅샷(`BL-SKILL`)** 2건 대조 | §6의 2·3·4번 분기 문안과 Unknown 게이트 디폴트 `N`이 개정 전과 동일 | diff/grep | `git show HEAD:opal/skills/opal-skill-manager/SKILL.md > /tmp/skill_before.md` 후 `awk '/^2\. \`license == "Unknown"\`/,/^## 변경이력/'`로 2·3·4번 분기 구간을 before/after 각각 추출해 `diff` | Pass | `diff` exit 0 (바이트 동일) — 2번(Unknown 게이트, 디폴트 `N` 포함)·3번(source_repo null)·4번(ambiguous) 분기 문안이 개정 전후 완전 동일. 1번 분기만 scan-risk 삽입으로 변경(범위 밖) |
| TS-040 | user-registry 3필드 명시 | H-5 | ② 요구커버 (R-5) | `AR-SKILL` §2 | 기록 규칙에 `trust`·`capabilities`·`scanned_at` 3필드가 타입·값 범위와 함께 명시된다 | 구조 검사 | `sed -n '208,214p' SKILL.md`(추가 3필드 정의 표) | Pass | L212 `trust`(string, `SAFE`\|`CAUTION`\|`RISKY`\|`UNKNOWN`), L213 `capabilities`(string[], capability 라벨 중복제거 목록), L214 `scanned_at`(string, ISO 8601 UTC 예시 포함) — 3필드 전건 타입·값범위 명시 |
| TS-041 | 기존 7필드 잔존 | H-5 | ⑤ 잔존(회귀 보존) | `AR-SKILL` §2 | 기존 7필드(`name`·`alias`·`description`·`triggers`·`source_repo`·`commit_sha`·`license`)가 스키마 서술에 전건 잔존 | grep | `grep -n "name, alias, description, triggers, source_repo, commit_sha, license" SKILL.md` | Pass | L204 `groups[vendor][] = [{ name, alias, description, triggers, source_repo, commit_sha, license, trust, capabilities, scanned_at }]` — 기존 7필드 전건 잔존 확인(순서·이름 동일) |
| TS-050 | Match 3등급 실재 | H-6 | ② 요구커버 (R-6) | `AR-SKILL` §1 | Exact / Partial / No Match 3등급이 표에 존재하고 각 등급에 판정 기준·후속 동작이 채워진다 | 구조 검사 | `grep -n "Exact Match\|Partial Match\|No Match" SKILL.md` | Pass | L43 Exact Match, L44 Partial Match, L45 No Match 3등급 전건 존재. 각 행에 판정 기준(`match` 출력 필드 조건)·후속 동작 셀이 빈칸 없이 채워짐 |
| TS-051 | Exact 시 외부검색 금지 규칙 | H-6 | ② 요구커버 (R-6) | `AR-SKILL` §1 | 「Exact Match 시 외부 검색을 수행하지 않는다」 규칙이 `[MUST]` 토큰과 함께 존재 | grep | `grep -n "Reuse Before Install" SKILL.md` | Pass | L47 `[MUST] Reuse Before Install — Exact Match 시 외부 검색(2단계 npx skills find)을 수행하지 않는다` — `[MUST]` 토큰 동반 존재 |
| TS-052 | 등급 판정 결정론 문언 | H-6 | ⑥ 경계·부정 — **문언 검사(경계 입력 미실행)** | `AR-SKILL` §1 | 판정 기준이 `match` 출력 필드명(`found`·`installed`·`ambiguous`·`name`·`alias`)과 문자열 동일성 비교로만 기술되고 주관 표현 0건 | 구조 검사 | `sed -n '39,47p' SKILL.md` | Pass | L39 "판정 입력은 match 출력의 기존 필드(found·installed·ambiguous·name·alias)뿐이며...문자열 동일성 비교로만 등급을 가른다 — 주관 판단을 쓰지 않는다". L43-45 3등급 조건이 전건 `found:true`/`installed:true`/`ambiguous:true`/문자열 동일 조건으로만 기술, 주관 표현 0건 |
| TS-060 | 위임 페이로드 필드 실재 | 해당 없음(E-5) | ② 요구커버 (R-7) | `AR-SKILL` §1 말미 | 페이로드 필드 목록이 표로 존재하고 각 필드에 타입·내용이 명시된다 | 구조 검사 | `sed -n '90,101p' SKILL.md`(위임 페이로드 표) | Pass | `requested_capability`~`skill_type_hint` 7필드 표 전건 존재, 각 행에 타입·내용·creator 측 소비 지점 3열 빈칸 없이 채워짐 |
| TS-061 | 위임 대상 채택 + 구 명칭 소거 | 해당 없음(E-5) | ⑤ **채택**(신형 명칭 채택 · 구형 `skill-builder` 잔존 0) | `AR-SKILL` | 위임 대상이 `opal-skill-creator`로 명시되고 `skill-builder` 표기 0건 | grep | `grep -n "opal-skill-creator\|skill-builder" SKILL.md` | Pass | `opal-skill-creator` 3건(L83·L88·L102) 명시, `skill-builder` grep hit 0건 |
| TS-062 | 탐색 소스·미달 사유 포함 | 해당 없음(E-5) | ② 요구커버 (R-7) | `AR-SKILL` | `searched_sources`와 후보별 미달 사유(`shortfall`)가 페이로드 필드에 전건 포함 | grep | `grep -n "searched_sources\|shortfall" SKILL.md` | Pass | L97 `searched_sources`(string[], 탐색 소스 목록), L98 `candidates_evaluated`의 `shortfall`(2층 비교 표 미달/부분 축 근거 인용) — 위임 페이로드 표에 2건 전건 포함 |
| TS-070 | 변경이력 행 추가 | 해당 없음(E-5) | ② 요구커버 (R-8) | `AR-SKILL` §변경이력 | 버전(semver)·일시(`YYYY-MM-DD HH:mm KST`)·변경내용(태스크 번호 `(105)` 포함) 행 1건이 추가된다 | grep | `tail -10 SKILL.md`(변경이력 표 마지막 행) | Pass | L328 `v1.5 \| 2026-09-03 00:52 KST \| ...(105)` — semver(v1.5)·`YYYY-MM-DD HH:mm KST` 형식 일시·`(105)` 태스크 번호 포함 행 1건 추가 확인 |
| TS-071 | 외부 절 번호 앵커 무결 | H-2 | ⑤ 잔존(회귀 보존) | `AR-SKILL` + **조건 예외**: 외부 참조 파일 `RF-ANCHOR`(`opal/core/references/harness/skill-commands.md`) 동반 Read | PLAN §3.8.2 (b) 6개 grep 전건 기대값 충족 — `skill-commands.md`의 `SKILL.md §6`·`§2` 지목이 유효하게 남는다 | grep -F | `grep -n "SKILL.md §6\|SKILL.md §2\|§6\|§2" opal/core/references/harness/skill-commands.md` + `grep -n "^### 6\.\|^### 2\." SKILL.md` | Pass | `skill-commands.md` L24·L36 `opal-skill-manager/SKILL.md §6`, L24·L49 `§2` 지목 유효 — `SKILL.md`의 `### 6. // 커맨드 미설치 매칭 시 자동 설치·실행`, `### 2. 스킬 설치`가 실제로 존재해 앵커 무결 |
| TS-072 | 카탈로그 불가침 유지 | H-8 | ⑤ 잔존(회귀 보존) | `AR-SKILL` | 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`) 쓰기 지시 0건 && `:102`의 `[MUST] ... 수정하지 않는다` 금지 문장 잔존 | grep | `grep -n "카탈로그.*수정하지 않는다\|프레임워크 카탈로그" SKILL.md` | Pass | 카탈로그 쓰기 지시 0건(전건 "수정하지 않는다" 금지 방향) — L200·L217·L238·L273 4곳 모두 무수정 규칙. `git show HEAD:...SKILL.md`의 `:102`(개정 전) 문장 `[MUST] ~/.opal/references/community-skills-registry.json(프레임워크 카탈로그)은 설치 시 수정하지 않는다.`가 개정 후 L200에 바이트 동일하게 잔존(§1·§2 재작성으로 줄번호만 이동, 문장 불변) |
| TS-073 | ARCHITECTURE 갱신 | 해당 없음(E-5) | ② 요구커버 (R-8 파생) | **조건 예외**: 대상이 `AR-SKILL`이 아니라 `AR-ARCH`(`docs/ARCHITECTURE.md`) | `docs/ARCHITECTURE.md:189` 서술이 보안 4단 축을 반영하고 §변경이력 행 1건 추가 | grep | `sed -n '189p' docs/ARCHITECTURE.md` + `grep -n "scan-risk\|SAFE\|CAUTION\|RISKY\|UNKNOWN" docs/ARCHITECTURE.md` | Pass | L189 "설치 가부는 2축 판정으로 결정한다...두 축을 합쳐 SAFE / CAUTION / RISKY / UNKNOWN 4단으로 판정하며..." — 보안 4단 축 반영 확인. §변경이력 L495 `2026-09-03 00:59 ...(태스크 105)` 행 1건 추가 |

### L1-b. 기능 단위 — 도구 동적 검사 (자동)

#### TS-010: `scan-risk` 서브명령이 switch에 등재되어 호출된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대응 축 | ② 요구커버 (R-2) |
| 대상 | `AR-TOOL` `main()` switch |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-CLEAN` |
| 기대 결과 | 무인자 호출 → usage 출력 + exit 1. `scan-risk FX-CLEAN` → `Unknown command` 미출력 |
| 도구 | `node --test` (`node:test` + `spawnSync` CLI 블랙박스) |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` |
| 결과 | Pass |
| 상세 | T01/TS-010(무인자→usage+exit 1) ok, T02/TS-010(존재 dir→Unknown command 미출력+JSON stdout) ok. 16/16 전건 pass, 0 fail(전체 파일 1회 실행 로그로 그룹 2 전체 커버) |

#### TS-011: 위험 픽스처에서 RISKY와 active hit를 검출한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대응 축 | ② 요구커버 (R-2) |
| 대상 | `AR-TOOL` `scanRiskCommand()` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-DANGER` — RP-01~RP-04를 코드펜스 안에 포함 |
| 기대 결과 | `verdict:"RISKY"`, `hits[]`에 `context:"active"` severity high ≥1건, exit 0 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T03) |
| 결과 | Pass |
| 상세 | T03/TS-011 ok — verdict:"RISKY", context:"active" severity high ≥1건, exit 0 확인. 추가로 본 test-agent가 실 FX-DANGER 3건(TS-034용)을 별도 스캔해도 전건 RISKY 재확인 |

#### TS-012: 무해 픽스처에서 active hit가 0건이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대응 축 | ② 요구커버 (R-2) |
| 대상 | `AR-TOOL` `scanRiskCommand()` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-CLEAN` — 위험 토큰 0건 |
| 기대 결과 | `verdict:"SAFE"`, active hit 0건, exit 0 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T07) |
| 결과 | Pass |
| 상세 | T07/TS-012 ok — verdict:"SAFE", active hit 0건, exit 0 확인 |

#### TS-013: 오탐 억제 4규칙이 무해 픽스처 4종을 통과시킨다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-3** (P0 — 이 태스크 최대 설계 리스크), H-4 |
| 대응 축 | ⑥ 경계·부정 |
| 대상 | `AR-TOOL` 오탐 억제 상수 + `context` 태그 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-NEGATED`(금지 산문) · `FX-COMMENT`(주석 라인) · `FX-FIXTURE-PATH`(`tests/` 하위) · `FX-PROSE`(산문 언급만) 4종 |
| 기대 결과 | 전건 `verdict:"SAFE"` && 해당 hit의 `context`가 `negated`/`comment`/`fixture`/`prose` 중 하나로 기록된다. 개정된 `opal-skill-manager/SKILL.md` 자신이 위험 패턴 목록을 본문에 게재하므로 이 스킬 문서를 스캔했을 때 자기 자신이 RISKY로 판정되는 메타-순환 오탐이 발생하지 않는다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T08) + `node opal/tools/skill-registry/skill-registry.js scan-risk opal/skills/opal-skill-manager`(메타-순환 실측) |
| 결과 | Pass |
| 상세 | T08/TS-013 ok — FX-NEGATED·FX-COMMENT·FX-FIXTURE-PATH·FX-PROSE 4종 전건 SAFE, context ∈ {negated,comment,fixture,prose} 확인. 추가로 개정된 SKILL.md 자신(`opal/skills/opal-skill-manager`)을 실제 scan-risk로 스캔한 결과 `"verdict":"SAFE"` 1건만 반환 — 메타-순환 오탐 0건 실증 |

#### TS-014: 반환 JSON이 계약 형상을 지킨다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대응 축 | ② 요구커버 (R-2) |
| 대상 | `AR-TOOL` `scan-risk` 출력 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-DANGER` |
| 기대 결과 | 출력 JSON에 `ok`·`verdict`·`hits` 3키가 존재하고 `hits[]` 각 항목에 `id`·`severity`·`capability`·`file`·`line`·`context` 6키가 존재한다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T04) |
| 결과 | Pass |
| 상세 | T04/TS-014 ok — 반환 JSON `ok`·`verdict`·`hits` 3키 + `hits[]` 각 항목 `id`·`severity`·`capability`·`file`·`line`·`context` 6키 형상 계약 확인 |

#### TS-016: ReDoS 병리 입력에서 타임박스 내 종료한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-7** |
| 대응 축 | ⑥ 경계·부정 (보안) |
| 대상 | `AR-TOOL` `RISK_PATTERNS` 정규식 상수 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-REDOS` — 100KB 단일 반복 문자열 |
| 기대 결과 | 스캔이 3초 내 종료하고 `RISK_PATTERNS` 전건 nested quantifier 0건이다 (기존 `isUnsafeRegex()` 기준 통과) |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T10, T11) |
| 결과 | Pass |
| 상세 | T10/TS-016(FX-REDOS 100KB → 22.9ms 종료, 3초 타임박스 이내) ok. T11/TS-016(RISK_PATTERNS 10종 전건 `isUnsafeRegex()` nested quantifier 0건) ok — RP-01~RP-10 소스(:675-684) 전건 선형 정규식(비-nested), `.*`/`.+` ≤2회, 길이 ≤100자 확인 |

#### TS-017: 존재하지 않는 디렉토리에서 UNKNOWN으로 종료한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대응 축 | ⑥ 경계·부정 |
| 대상 | `AR-TOOL` `scan-risk` 오류 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-MISSING` — 생성하지 않은 경로 문자열 |
| 기대 결과 | `{ok:false, verdict:"UNKNOWN", error:...}` + exit 1 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T12) |
| 결과 | Pass |
| 상세 | T12/TS-017 ok — `{ok:false, verdict:"UNKNOWN", error:...}` + exit 1 확인 |

#### TS-042: 10필드 user-registry가 validate를 통과한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-5** |
| 대응 축 | ② 요구커버 (R-5) |
| 대상 | `AR-TOOL` `validate()` 미지 필드 무시 경로 (`skill-registry.js:435-462`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-REG10` — `groups[vendor][]` 형상, 10필드 항목 1건 |
| 기대 결과 | `node skill-registry.js validate` errors 0건, exit 0 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T14) |
| 결과 | Pass |
| 상세 | T14/TS-042 ok — `errors:[]`, `valid:true`, exit 0. 본 test-agent가 격리 HOME(TS-081 절차)에서 재확인한 별도 `validate` 실행도 `"errors": []` 동일 |

#### TS-019: CAUTION 판정이 확인 게이트를 요구한다 (경계 — 4단 중간값 실동작)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-4 |
| 대응 축 | ⑥ 경계·부정 — **실행 검사** |
| 도출 근거 | 게이트 iteration 1 gap **G-5** — 4단 판정 중 SAFE·RISKY·UNKNOWN은 실동작 검증이 있으나 CAUTION만 문언 검사(TS-030)에 머물렀다 |
| 대상 | `AR-TOOL` `scan-risk` severity 분류 + `AR-SKILL` 4단 판정 표의 CAUTION 행 동작 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-CAUTION` — medium severity hit만 존재(파일 수정·네트워크 접근류), 라이선스 확인됨, active hit 1건 |
| 기대 결과 | **(실행 단정만)** `verdict:"CAUTION"`이 반환되고 `hits[].severity`가 `medium`이며, `hits[].context`가 `active`이고 exit 0이다. RISKY와 달리 후보 목록에 잔존한다 |
| 분리 고지 | 「CAUTION 행 동작 문언」·「후보 1~2건 시 승격 여부 문언」 2항은 **문언 검사**이므로 본 시나리오에서 제외하고 TS-030(4단 표 3셀 빈칸 0)이 흡수한다 — G-4의 문언/실행 분리 원칙을 시나리오 내부에서 재혼합하지 않는다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T09) |
| 결과 | Pass |
| 상세 | T09/TS-019 ok — verdict:"CAUTION", hits[].severity:"medium", hits[].context:"active", active high 0, exit 0 확인 |

### L2. 프로세스 통합 (자동)

#### TS-015: `list` 출력 계약이 무수정으로 보존되고 OPAL Console 어댑터가 통과한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1** (P0) |
| 대응 축 | ⑤ 잔존 (회귀) |
| 대상 | `AR-TOOL` `listCommand()` + `dashboard/backend/adapters/skill_adapter.py:49-60` |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — 도구 출력 대조 + 다운스트림 테스트 실행)** |
| 조건 | `BL-LIST` — `scan-risk` 도입 전 `list` 출력 스냅샷 |
| 기대 결과 | `node skill-registry.js list` 출력이 JSON 배열이고 `BL-LIST`와 동일하며, `dashboard/backend/tests/test_adapters.py::test_skill_adapter_list`가 통과한다. 기존 `tests/` 3파일(`test-match.js`·`test-migrate.js`·`test-validate.js`)도 전건 통과한다 |
| 도구 | `node --test` + `pytest` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js`(T13) + `python3 -m pytest dashboard/backend/tests/test_adapters.py::test_skill_adapter_list -v` + `node --test opal/tools/skill-registry/tests/test-match.js opal/tools/skill-registry/tests/test-migrate.js opal/tools/skill-registry/tests/test-validate.js` |
| 결과 | Pass |
| 상세 | T13/TS-015 ok — `list` 출력이 JSON 배열 + BL-LIST 스냅샷과 동일 확인, 실 레지스트리 `list`도 JSON 배열 + 키 계약 유지. `test_skill_adapter_list` PASSED (1 passed in 0.03s). 기존 `tests/` 3파일 25/25 pass, 0 fail — 4파일 합산 41/41 전건 pass |

#### TS-043: 병합 로드가 신규 필드 항목을 반환한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-5** |
| 대응 축 | ② 요구커버 (R-5) |
| 대상 | `AR-TOOL` `loadAllSkills()` + `flattenGroups()` 병합 경로 (`skill-registry.js:125-143`, `:58-74`) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `FX-REG10` (정상 형상) · `FX-REG-FLAT` (형상 위반) |
| 기대 결과 | `list --group=community`가 `FX-REG10` 항목을 반환한다. `FX-REG-FLAT`은 조용히 무시되어 반환되지 않으며, 이 유실이 재현됨을 단정한다(형상 제약 `[MUST]`의 필요성 증거) |
| 도구 | `node --test` |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-scan-risk.js` (T15, T16) |
| 결과 | Pass |
| 상세 | T15/TS-043 ok — FX-REG10 항목(`fxvendor/fx-user-skill`)이 `list --group=community`에 병합 반환 + 카탈로그 항목(`fxvendor/fx-pdf`)도 함께 반환(override 아님). T16/TS-043 ok — FX-REG-FLAT(flat 배열)은 조용히 무시되어 미반환(`fxvendor/fx-flat-skill` 부재) + CLI 다운 0(exit 0), 형상 유실 재현 확인 |

#### TS-034: RISKY 후보가 전량 제외되고 위임 경로로 종료된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-9 |
| 대응 축 | ⑥ 경계·부정 (부정 경로 통합) |
| 대상 | 1층 하드 필터 → 4단 판정 → 추천 사다리 → NOT_FOUND 위임 연결 전체 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — 로컬 픽스처 3건으로 절차 통합 실행)** |
| 조건 | `FX-DANGER` 계열 3건을 후보로 투입 (전건 RISKY 판정 대상) |
| 기대 결과 | 3건 전건이 추천 후보에서 제외되고, 잔존 후보 0건이므로 NOT_FOUND로 판정되어 `opal-skill-creator` 위임 페이로드(`searched_sources` + 후보별 `shortfall` 포함)가 산출된다. 임의 후보가 승인 없이 `~/.opal/community-skills/`로 복사되지 않는다 |
| 도구 | `node --test` + 임시 디렉토리 픽스처 |
| 실행 명령 | 3개 합성 danger 후보 디렉토리(`mktemp -d`, RP-01~RP-04 코드펜스 포함)를 생성해 `node opal/tools/skill-registry/skill-registry.js scan-risk {tmp candN}` 3회 개별 실행 + 실행 전후 `ls -la ~/.opal/community-skills/` 스냅샷 대조 |
| 결과 | Pass |
| 상세 | 3개 후보 전건 `"verdict":"RISKY"` + `context:"active"` hit 4건씩(RP-01~RP-04) 실측. SKILL.md §2 4단 판정 표(L155)·사다리 1단(L179 "보안 판정이 RISKY인 후보는 추천 후보에서 제외")에 따라 3건 전건 추천 후보에서 제외 → 잔존 후보 0건 → §2 L187 "전 후보가 1단(RISKY 제외)에서 탈락하면 「적합 스킬 미발견 시 위임」(§1 말미) 절차로 분기" 규칙에 의해 NOT_FOUND 위임 경로로 귀결(§1 위임 페이로드 표에 `searched_sources`·`candidates_evaluated[].shortfall` 필드 존재는 TS-060·062에서 별도 확인). `ls -la ~/.opal/community-skills/`가 실행 전후 완전 동일(diff 없음) — 승인 없는 복사 0건 실증 |

#### TS-035: 혼합 후보에서 신형 절차가 무해 후보를 채택하고 재현한다 (채택 — 실행 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-9 |
| 대응 축 | ⑤ **채택**(신형 절차 채택 실행 검증) |
| 도출 근거 | 게이트 iteration 1 gap **G-3** — ⑤축 8건 중 7건이 회귀 보존이고 채택 검증이 TS-061 문언 대조 1건뿐이었다. 신형 절차가 실제로 작동해 올바른 후보를 고르는지를 실행으로 검증한다 |
| 대상 | 1층 하드 필터 → 4단 판정 → 2층 비교 → 추천 사다리 전체 (신형 절차 채택) |
| 계층 | L2 |
| **실행 방식** | **M2 (E2E 자동화 — 격리 `HOME`에서 에이전트가 개정된 SKILL.md 절차를 수행하고, 산출 상태를 단정)**. **[MUST] M1 금지** — 추천 사다리는 `skill-registry.js`가 아니라 `SKILL.md` 절차가 소유하므로(신규 코드는 `scan-risk` 1종뿐, `PLAN.md:883`), node 테스트가 사다리를 재구현해 자기 구현을 단정하면 self-confirming이다(`PLAN.md:1128-1130`). **수행자는 `opal-test-agent`이며 SKILL.md 작성자(Step 3~8 워커)와 분리한다** |
| 조건 | `FX-MIXED` — 무해 1건 + RISKY 2건. 격리 `HOME` |
| 기대 결과 | (a) 추천이 무해 후보 1건으로 확정된다 (b) RISKY 2건이 후보 목록에서 소거되어 추천 대상에 나타나지 않는다 (c) 동일 후보 집합으로 사다리를 2회 적용했을 때 추천 결과와 사다리 통과 단계가 동일하다(재현성 — 문언 검사 TS-023의 실행 대응) |
| 도구 | `opal-test-agent`(mode: e2e) + 격리 `HOME` + `skill-registry.js validate`/`list` 조회 |
| 실행 명령 | 격리 `HOME`(`mktemp -d`) 하에서 후보 3건(candA=무해 `safe-formatter`, candB·candC=RISKY) 디렉토리 생성 → `HOME={ISO_HOME} node skill-registry.js scan-risk {tmp candN}`를 각 후보에 대해 **2회 반복 실행**(재현성 확인) → SKILL.md §2 4단 판정 표·5단 추천 사다리(개정된 SKILL.md 절차, node 재구현 없음)를 test-agent가 직접 적용해 추천 확정 |
| 결과 | Pass |
| 상세 | 1회차: candA=SAFE, candB=RISKY, candC=RISKY. 2회차(재실행): candA=SAFE, candB=RISKY, candC=RISKY — 완전 동일(재현성 (c) 충족). §2 4단 판정 표·사다리 1단 적용 → candB·candC 추천 후보에서 제외(소거, (b) 충족) → 잔존 후보 candA 유일 → 사다리 2단("목적 적합==충족인 후보가 유일 → 추천") 적용 → candA(safe-formatter) 추천 확정((a) 충족). SKILL.md 절차를 test-agent가 직접 수행했으며 `skill-registry.js`에 사다리 로직을 재구현하지 않음(N-1 준수) |

#### TS-081: 승인부터 복사·등록까지 목표 종점이 완결된다 (목표달성 — 실행 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-9 |
| 대응 축 | **① 목표달성**(종점 검증) |
| 도출 근거 | 게이트 iteration 1 gap **G-2** — TS-080은 조건상 승인을 **거부**하므로 목표 문장의 종점(「승인 → 복사·등록」)이 어떤 계층에서도 미검증이었다. R-5는 픽스처 `validate`로 대리 검증했을 뿐 복사·등록 경로를 실행하지 않았다 |
| 대상 | 6단 흐름의 5·6단 — 승인 → `~/.opal/community-skills/{vendor}/{name}/` 복사 → user-registry 기록 |
| 계층 | L2 |
| **실행 방식** | **M2 (E2E 자동화 — 격리 `HOME`에서 에이전트가 개정된 SKILL.md 절차를 수행하고, 파일시스템·registry 상태를 단정)**. **[MUST] M1 금지 · 신규 구현 요건 0건** — 복사·등록은 `SKILL.md` 절차 소유이며 `skill-registry.js`에 경로 오버라이드(`--dest` 등)를 **신설하지 않는다**(격리는 `HOME` 환경변수로 달성 → `PLAN.md` §3 구현 설계 무변경). **수행자는 `opal-test-agent`이며 SKILL.md 작성자와 분리한다** |
| 조건 | `FX-APPROVE` — 무해 후보 1건. **격리 `HOME`으로 설치 루트를 분리하여 실 `~/.opal/community-skills/`를 건드리지 않는다** |
| 기대 결과 | (a) `{설치루트}/{vendor}/{name}/SKILL.md`가 생성된다 (b) `user-registry.json`에 10필드 항목 1건이 추가되고 `trust`·`capabilities`·`scanned_at`이 채워진다 (c) 기록 형상이 `groups[vendor][]`를 유지한다 (d) `node skill-registry.js validate` errors 0건 (e) 프레임워크 카탈로그 파일이 수정되지 않았다(mtime·내용 동일) |
| 도구 | `opal-test-agent`(mode: e2e) + 격리 `HOME` + `skill-registry.js validate`/`list` 조회 |
| 실행 명령 | 신규 격리 `HOME`(`mktemp -d`)에 `.opal/references/opal-skills-registry.json`(빈 groups, main 스킬 dangling 오탐 방지)·`.opal/references/community-skills-registry.json`(실 프레임워크 카탈로그 **복사본**, 무수정 검증용)·무해 candA(FX-APPROVE) 준비 → SKILL.md §2 6단 절차대로 `{ISO_HOME}/.opal/community-skills/fx-approve/safe-formatter/SKILL.md`로 `cp` 복사 + `user-registry.json` 10필드 항목 작성(`groups.fx-approve[]` 형상) → `cd {비-opal WORKDIR} && HOME={ISO_HOME} node skill-registry.js validate` / `list --group=community` 실행 → 카탈로그 파일 `stat -f %m`·`md5` 전후 비교 |
| 결과 | Pass |
| 상세 | (a) `{ISO_HOME}/.opal/community-skills/fx-approve/safe-formatter/SKILL.md` 생성 확인(`ls -la`). (b) `user-registry.json`에 `fx-approve/safe-formatter` 10필드(`name`·`alias`·`description`·`triggers`·`source_repo`·`commit_sha`·`license`·`trust`·`capabilities`·`scanned_at`) 항목 1건 추가, `trust:"SAFE"`·`capabilities:[]`·`scanned_at` ISO8601 채워짐. (c) `groups.fx-approve[]` 형상 유지 — `list --group=community` 출력에 `"name":"fx-approve/safe-formatter","installed":true` 정상 반환으로 형상 파싱 성공 실증. (d) `validate` 결과 `"errors": []`, `"valid": true`. (e) 카탈로그 파일 mtime(`1788441406`→`1788441406`)·md5(`574e67...`→`574e67...`) 전후 완전 동일 — 무수정 확인. 실 `~/.opal/community-skills/`는 별도로 무변경 확인(아래 완료 보고 참조) |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### TS-080: 개정된 절차만으로 실제 스킬 1건을 탐색·판정·추천까지 완주한다 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-4, H-9 (판정 축 전체의 실사용 검증) |
| 대응 축 | **① 목표달성**(사용자 계층 완주 — 종점 검증은 TS-081이 담당) |
| 도출 근거 | TASK.md §작업 목표 — 6단 흐름이 실제로 동작하는가. **Block A 선작성 고유 시나리오** (PLAN 유래 TS 33건에 대응 0건) |
| 대상 | 개정된 `opal-skill-manager` 절차 전체 (사용자 관점 완주) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 실 네트워크(skills.sh 조회 + GitHub clone)와 2층 판정 재량이 필요해 자동화 불가. M2 대체 불가 |
| 조건 | 임의 capability 요청 1건. 네트워크 가용. **승인 단계에서 거부를 선택해 실제 설치는 수행하지 않는다** |
| 기대 결과 | 아래 6개 체크 항목이 **각각 Pass/Fail로 판정**된다 — (a) 후보 목록이 **3건 이하**이고 각 후보에 `name`·`source_repo`·`license` 3필드가 채워진다 (b) 후보별 `scan-risk` 출력의 `verdict`가 SAFE/CAUTION/RISKY/UNKNOWN **4단 중 정확히 1값**이다 (c) 2층 비교 표의 4축 × 후보 수 셀에 **빈칸 0건** (d) RISKY 판정 후보가 있으면 추천 목록에서 제외되었고, 없으면 「RISKY 0건」이 기록된다 (e) 추천 1개에 `경로:줄번호` 형식 근거 인용이 **≥1건** 붙는다. 추가로 (f) 승인 거부 시 `~/.opal/community-skills/` 하위 신규 디렉토리 0건 && `user-registry.json` 변경 0건 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| PM 요청 양식 | 「TS-080 수동 확인 요청 — 개정된 `opal/skills/opal-skill-manager/SKILL.md` §1·§2만 보고 임의 capability 1건을 탐색해 주십시오. 승인 단계에서 **거부**를 선택하십시오. 확인 결과는 위 (a)~(f) 6개 체크 항목별로 **Pass / Fail** 하나씩만 회신해 주시면 됩니다. 절차 문언에서 막힌 지점은 판정과 별개인 **참고 의견**으로 자유 기재해 주십시오(판정에 반영하지 않음).」 |
| 결과 | **Pass — 6항목 전건** (부분 Pass → Pass 승격, 재검증 2026-09-03 23:20). (a) Pass / **(b) Pass — 캡틴이 재배포를 완료해 결함 A 해소. 배포본 `scan-risk` 재실행 결과 `ok:true`·`verdict:"SAFE"`·exit 0** / (c) Pass / (d) Pass / (e) Pass / (f) Pass. 수행자 PM ≠ 판정자 캡틴 분리 적용. 최초 판정(2026-09-03, 부분 Pass — (b) Fail)은 재배포 전 상태 기준이었다 |
| 실행 기록 | capability=「릴리스 노트 작성」. 1단계 `match "릴리스 노트"` → `{"found": false}` No Match / 2단계 `npx --yes skills find "release notes"` → **6건** 검출 → 상위 3건 선별(6→3 감소 보고) / 3단 `parse-source-repo` ×3 + `git clone --depth 1` ×3 전건 성공, 원본 탐지 폴백 실측(phuryn=`pm-execution/skills/release-notes` **3단(find)** · nexu-io=`skills/release-notes-one-pager` 2단 · every-app=`.agents/skills/openseo-release-notes` **3단(find)**) / 4단 `scan-risk` ×3 → 3건 전건 `verdict:"SAFE"`·active hit 0건, 라이선스 MIT·Apache-2.0·MIT / 5단 사다리 **2단에서 확정** → `phuryn/pm-skills@release-notes` / 6단 승인 **거부** — 복사·등록 미수행. 임시 디렉토리 4개 경로 검증 후 삭제 |
| 항목별 실측 | **(a)** 후보 3건, `name`·`source_repo`는 2단계에서, `license`는 3단 `LICENSE` 파일로 확보 — v1.5.1 개정 문언과 일치 **(b)** 배포본 호출은 `Unknown command: scan-risk` exit 1로 **실행 불가**(결함 A 미해소, 재배포 대기), 소스 경로로는 3건 전건 `SAFE` 1값 **(c)** 4축 × 3후보 = **12셀 빈칸 0건** **(d)** **RISKY 0건** 기록 **(e)** 추천 근거 `SKILL.md:8`·`SKILL.md:63` **2건** **(f)** 사전·사후 vendor 목록 `diff` 동일(8개), 신규 디렉토리 0건, `user-registry.json` 사전·사후 모두 **ABSENT** |
| 검증 등급 | **부분 검증** — 수행을 PM이 대행했으므로 「사람이 문서만 보고 절차를 따라갈 수 있는가」라는 문서 가독성 검증은 제외된다. 판정 독립성(판정자≠설계자)은 유지 |
| 검출 결함 | **TS-080 실행이 결함 3건을 검출했다** — **A** 배포본 `scan-risk` 부재로 절차 4단 실행 불가(재배포 대기, 문서 미수정 대상) · **B** `npx skills find` 출력에 `license` 없어 2단계 선별 기준 ① 적용 불가 → `test.fix_1`에서 교정(v1.5.1) · **C** 「출력 형식 호환」 축 미지정 시 처리 부재 → `해당 없음` 규칙으로 교정(v1.5.1). 자동 검증 39건·컨벤션 진단이 전부 통과한 상태에서 검출됐고, 단위 테스트가 **소스 경로**를 호출하고 SKILL.md가 **배포본**을 호출하는 계층 차이 때문에 구조적으로 잡히지 않았다 |
| 상세 | 캡틴 수동 확인 대기 — PM 요청 양식(위 「PM 요청 양식」 행) 참조. opal-test-agent는 [SUPERVISOR] 마커 시나리오를 대행하지 않으며, 실 네트워크(skills.sh 조회 + GitHub clone)와 2층 판정 재량이 필요해 자동화 불가하므로 미실행 상태로 PM에 반환한다 |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC / 요구사항 | 기능 | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|--------------|------|---------|---------|---------|-----------------|------|
| R-1 AC (6단 존재·입출력) | F-001 | H-2 | L1 | TS-001 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-1 AC (clone=임시/복사=설치) | F-001 | H-2 | L1 | TS-002 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-1 AC (절 번호 보존) | F-001 | H-2 | L1 | TS-003 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-1 AC (후보 하한 거동) | F-001 | H-3 | L1 | TS-004 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | **선작성 고유** · ⑥ 문언 검사 |
| R-2 AC (switch 등재) | F-002 | H-1 | L1 | TS-010 | `tests/test-scan-risk.js` | |
| R-2 AC (위험 검출 ≥1) | F-002 | H-3 | L1 | TS-011 | `tests/test-scan-risk.js` | |
| R-2 AC (무해 검출 0) | F-002 | H-3 | L1 | TS-012 | `tests/test-scan-risk.js` | |
| R-2 AC (오탐 억제) | F-002 | H-3, H-4 | L1 | TS-013 | `tests/test-scan-risk.js` | ⑥ **실행 검사** |
| R-2 AC (JSON 형상) | F-002 | H-1 | L1 | TS-014 | `tests/test-scan-risk.js` | |
| R-2 AC (ReDoS 내성) | F-002 | H-7 | L1 | TS-016 | `tests/test-scan-risk.js` | ⑥ **실행 검사**(보안) |
| R-2 AC (UNKNOWN 경로) | F-002 | H-1 | L1 | TS-017 | `tests/test-scan-risk.js` | ⑥ **실행 검사** |
| R-4 AC (CAUTION 실동작) | F-004 | H-3, H-4 | L1 | TS-019 | `tests/test-scan-risk.js` | ⑥ **실행 검사** · G-5 보강 |
| R-2 미탐 한계 명문화 | F-002 | H-4 | L1 | TS-018 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | **선작성 고유** · ⑥ 문언 검사 |
| R-3 AC (4축 존재) | F-003 | H-9 | L1 | TS-020 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-3 AC (점수 0건) | F-003 | H-9 | L1 | TS-021 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-3 AC (근거 인용 지시) | F-003 | H-9 | L1 | TS-022 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-3 AC (추천 재현성) | F-003 | H-9 | L1 | TS-023 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑥ 문언 검사 (실행 대응 = TS-035) |
| R-4 AC (4단 전건) | F-004 | H-3 | L1 | TS-030 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-4 AC (RISKY 제외) | F-004 | H-3 | L1 | TS-031 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-4 AC (판정 결정론) | F-004 | H-3 | L1 | TS-032 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑥ 문언 검사 |
| R-4 범위 경계 (§6 불변) | F-004 | H-2 | L1 | TS-033 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-4 + R-7 (제외 → 위임 결합) | F-004, F-007 | H-3, H-9 | L2 | TS-034 | §3 L2 TS-034 `실행 명령` 참조 (scan-risk 실호출 + 절차 판정) | **선작성 고유** · ⑥ **실행 검사** |
| R-3 + R-4 (신형 절차 채택) | F-003, F-004 | H-3, H-9 | L2 | TS-035 | §3 L2 TS-035 `실행 명령` 참조 (M2 — 격리 HOME 절차 수행) | ⑤ **채택 실행** · G-3 보강 |
| R-5 AC (3필드 명시) | F-005 | H-5 | L1 | TS-040 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-5 AC (기존 7필드 유지) | F-005 | H-5 | L1 | TS-041 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-5 AC (validate error 0) | F-005 | H-5 | L1 | TS-042 | `tests/test-scan-risk.js` 또는 신규 | |
| R-5 형상 제약 | F-005 | H-5 | L2 | TS-043 | `tests/test-scan-risk.js` (FX-REG10 / FX-REG-FLAT TC) | |
| R-6 AC (3등급 존재) | F-006 | H-6 | L1 | TS-050 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-6 AC (Exact 외부검색 금지) | F-006 | H-6 | L1 | TS-051 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-6 AC (등급 결정론) | F-006 | H-6 | L1 | TS-052 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑥ 문언 검사 |
| R-7 AC (페이로드 필드) | F-007 | 해당 없음(E-5) | L1 | TS-060 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-7 AC (위임 대상) | F-007 | 해당 없음(E-5) | L1 | TS-061 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 채택 |
| R-7 AC (소스·미달 사유) | F-007 | 해당 없음(E-5) | L1 | TS-062 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-8 AC (변경이력 행) | F-008 | 해당 없음(E-5) | L1 | TS-070 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| R-8 AC (외부 앵커 무결) | F-008 | H-2 | L1 | TS-071 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-8 파생 (카탈로그 불가침) | F-008 | H-8 | L1 | TS-072 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | ⑤ 잔존 |
| R-8 파생 (ARCHITECTURE 갱신) | F-008 | 해당 없음(E-5) | L1 | TS-073 | 테스트 파일 없음 — 정적 검사, §3 L1-a `실행 명령` 참조 | |
| H-1 회귀 (list 계약) | F-002 | H-1 | L2 | TS-015 | `test_adapters.py::test_skill_adapter_list` | ⑤ 잔존 |
| TASK §작업 목표 (종점 완결) | F-001, F-005 | H-5, H-9 | L2 | TS-081 | §3 L2 TS-081 `실행 명령` 참조 (M2 — 격리 HOME 절차 수행) | **① 목표달성 실행** · G-2 보강 |
| TASK §작업 목표 (절차 완주) | F-001~F-007 | H-3, H-4, H-9 | L3 | TS-080 | 수동 [SUPERVISOR] | **① 목표달성 · 선작성 고유** |

**커버리지 확인 (게이트 iteration 2 시점)**

| 축 | 판정 | 근거 |
|----|------|------|
| ① 목표달성 | ✅ | TS-081(L2 실행 — 승인→복사·등록 종점) + TS-080(L3 수동 — 절차 완주, 6개 체크 항목 판정) |
| ② 요구커버 | ✅ | R-1~R-8 전건 매핑 (8/8, 미매핑 R 0건) |
| ③ 기능커버 | ✅ | F-001~F-008 전건 매핑 (8/8, 미매핑 F 0건) |
| ④ 리스크커버 | ✅ | H-1~H-9 전건 매핑 (9/9, 미매핑 H 0건) |
| ⑤ 채택·잔존 | ✅ | **채택 실행** TS-035 + **채택 문언** TS-061 + **잔존(회귀 보존)** TS-003·TS-015·TS-021·TS-033·TS-041·TS-071·TS-072 7건 — 채택과 잔존을 표기상 분리했다 |
| ⑥ 경계·부정 | ✅ | **실행 검사** TS-013·TS-016·TS-017·TS-019·TS-034 5건 + **문언 검사** TS-004·TS-018·TS-023·TS-032·TS-052 5건 (등가 합산하지 않음) |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A (설정 없음) | N/A | `find . -maxdepth 2 -iname ".eslintrc*" -o -iname "eslint.config.*"` 결과 0건 — 프로젝트 루트에 eslint 설정 파일 부재. `~/.opal/tools/test-tool/run.sh resolve` 스택 조회는 fe/be 프레임워크 프리셋(eslint/ruff)을 제안하나 실제 설정 파일 미존재로 강제 실행하지 않음 |
| 2 | 타입 체크 | N/A (설정 없음) | N/A | `tsconfig.json` 프로젝트 루트에 부재 — 순수 Node.js CommonJS 스크립트(`skill-registry.js`)로 TS 타입체크 대상 아님 |
| 3 | 포맷터 | N/A (설정 없음) | N/A | `.prettierrc*` 부재 확인 |
| 4 | 기존 테스트 회귀 (`tests/test-match.js`·`test-migrate.js`·`test-validate.js`) | `node --test` | Pass | `node --test opal/tools/skill-registry/tests/test-match.js opal/tools/skill-registry/tests/test-migrate.js opal/tools/skill-registry/tests/test-validate.js` → 25/25 pass, 0 fail. `test-scan-risk.js` 16/16 별도 pass 포함 4파일 합산 41/41 |
| 5 | @header 기록 위치 (`code-scan target`) | `~/.opal/tools/code-scan/run.sh target` | Pass | `run.sh target opal/tools/skill-registry/skill-registry.js` → `write_to: inline`(`header_source_inline`). 파일 L1-46 인라인 `@header`의 `@exports`(L10-11)에 `scan-risk <dir>` 신규 서브명령이 반영됨. `@description`(L9)에도 "scan-risk도 제공한다" 갱신 확인 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `git diff -- skill-registry.js SKILL.md docs/ARCHITECTURE.md`와 신규 `tests/test-scan-risk.js` 전체에 대해 `grep -inE "password\s*=|secret\s*=|api_key\s*=|token\s*=|BEGIN PRIVATE KEY"` 실행 — hit 0건(exit 1 = no match). 위험 패턴 상수(`RISK_PATTERNS`)나 픽스처 문자열도 실 시크릿이 아닌 정규식/합성 예문뿐 |
| 2 | .gitignore 확인 | Pass | `git status --short` 확인 결과 임시 디렉토리·픽스처 산출물(TS-034/035/081에서 생성한 `mktemp -d` 경로들)은 시스템 임시 디렉토리(`/var/folders/...`)에 위치해 저장소 밖이므로 커밋 대상에 원천적으로 포함되지 않음. 저장소 내 변경 파일은 `.opal/MEMORY.json`·`docs/ARCHITECTURE.md`·`opal/skills/opal-skill-manager/SKILL.md`·`opal/tools/skill-registry/skill-registry.js`(기존 추적 파일)와 신규 `opal/tools/skill-registry/tests/test-scan-risk.js`·`tasks/105-.../` 뿐이며 임시 산출물 누출 0건 |
| 3 | `RISK_PATTERNS` nested quantifier 0건 (ReDoS) | Pass | T11/TS-016 인용 — `[T11/TS-016] RISK_PATTERNS 전건 nested quantifier 0건 (isUnsafeRegex 기준)` ok (duration 0.315ms). `skill-registry.js:674-685` RISK_PATTERNS 10종(RP-01~RP-10) 전건이 `isUnsafeRegex()` 기준(길이 ≤100자, `.*`/`.+` ≤2회, `(xxx+)+`류 nested quantifier 없음)을 통과 |

## 7. 판정

**All Pass -- 40건 전건 Pass.** 자동 검증 39건 전건 Pass(실제 명령 출력 증거), §5 코드 품질 전건 Pass/N/A(린트·타입·포맷터 설정 파일 부재), §6 보안 3건 전건 Pass, 컨벤션 자동 진단 Critical/High **0건**(`GC-CONVENTION-20260903-2225.md`). TS-080(L3/M3)은 캡틴 결정에 따라 「PM 수행 + 캡틴 판정」으로 분리 실행되어 최초 **부분 Pass**((b) Fail — 배포본 미반영)로 확정됐고, 캡틴이 `./scripts/install-mac.sh` 재배포를 완료한 뒤 2026-09-03 23:20 재검증에서 (b)가 Pass로 승격되어 **6항목 전건 Pass**가 됐다(배포본 `scan-risk` `ok:true`·`verdict:"SAFE"`·exit 0, 배포본 grep hit 8건). TS-080이 검출한 결함 B·C는 `test.fix_1`에서 교정 완료(v1.5.1)되고 회귀 보호 대상 TS 12건 무손상을 PM이 재실측했다. 사전 결함(`op-scenario-gate` unregistered errors 1건)은 태스크 이전부터 존재하며 이번 변경으로 오류 건수 증가 없음(회귀 아님). **검증 등급 유의**: TS-080은 캡틴 결정에 따라 수행을 PM이 대행했으므로 「사람이 문서만 보고 절차를 따라갈 수 있는가」라는 문서 가독성 검증은 제외된 **부분 검증**이다. 판정 독립성(판정자≠설계자)은 유지됐다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인) — TEST-SCENARIO.md·test-scan-risk.js에 `grep -in "mock\|patch\|MagicMock"` 결과 실 mock 사용 0건(주석상 "mock 0건" 원칙 서술만 존재)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 — EXECUTE 산출물 기준 확인, test-agent가 추가 수정하지 않음
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음) — EXECUTE 산출물 기준, test-agent 범위 밖(수정 안 함)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 — TS-080, 캡틴 확정 판정으로 **부분 Pass**((b) Fail) 기록. Pass 오기재 없음
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **해당 없음**: PLAN.md 예상 변경 파일 4개(`skill-registry.js`·`tests/test-scan-risk.js`·`SKILL.md`·`ARCHITECTURE.md`)에 FE 화면·컴포넌트·인증/인가·외부 API 연동이 0건
- [x] 목표 커버 — TASK.md R 전체가 §4에 커버되고 목표달성 시나리오가 §3에 최소 1건 존재 (TS-080, TS-081 실행 완료로 종점 보강)

## 부록. 선작성이 발견한 조기 경보 (PM Gate 보고 대상)

| # | 발견 | 성격 | 처리 |
|---|------|------|------|
| E-1 | **철회.** Block A 시점에 「교체형 목표인데 R-1 AC에 구형 잔존 0 기준이 없다」고 기록했으나, PLAN.md §C-5는 이 태스크를 교체형이 아닌 **추가형**(기존 절차에 판정 축을 추가, 절 번호 보존 in-place 삽입)으로 판정했고 근거가 더 견고하다 — 현행 SKILL.md에는 제거할 100점 루브릭이 애초에 존재하지 않는다(루브릭은 캡틴이 제시한 외부 스펙안에만 있었다). 잔존 축은 PLAN이 다른 형태로 커버했다(TS-003 절 헤딩 잔존 · TS-033 §6 문안 불변 · TS-041 기존 7필드 잔존 · TS-072 `[MUST]` 금지문 잔존) | 판정 철회 | ⑤축은 8건으로 커버 완료. 추가 시나리오 불요 |
| E-2 | ①목표달성 축이 L3/M3 수동으로만 성립한다 — 실 네트워크와 2층 판정 재량 때문에 자동화 경로가 없다. 자동 검증만으로는 ①축이 커버되지 않는다 | 검증 계층 제약 | TS-080으로 편성. **TEST 단계에 캡틴 수동 확인 1회 예약 필요** |
| E-3 | 선작성 고유 기여 실측 — PLAN 유래 TS 33건에 **대응 0건**인 시나리오가 3건 발생했다: TS-004(후보 하한 거동) · TS-034(RISKY 전량 제외 → 위임 통합) · TS-080(절차 완주 목표달성). 모두 채택 관점(①⑥축)에서만 도출되는 항목이다 | 트랙 효과 실측 | `red-first.md` §1.6 근거(095 실측 「선작성 고유 3건, PLAN 유래 대응 0건」)와 동일 패턴 재현 — DONE.md에 기록 |
| E-4 | PLAN.md §C-5는 「§1.6 선작성 트랙 착수하지 않는다」로 판정했으나 PM은 이미 Block A를 선작성했다. 오케스트레이터 배선(`opal-pilot-dev-short/SKILL.md` STEP 2 (a))이 선작성을 PM 소관으로 규정하므로 트랙 판정 권한은 PM에 있고, 워커의 §C-5 판정은 자기 범위(RED-first 트랙) 밖이다 | 권한 경계 | PM 판정 유지(선작성 실행). E-3이 사후 정당화 근거. `red-first.md` §1.6과 §C-5 기재 의무의 주체 분리를 프레임워크 개선 후보로 이월 |
| E-5 | Block B 보강 중 PLAN 공백 1건 검출 — PLAN.md §리스크 가설 표 H-1~H-9에 **F-007(`opal-skill-creator` 위임 계약)·변경이력 행·ARCHITECTURE 갱신에 대응하는 가설이 없다**. 해당 5개 시나리오(TS-060·061·062·070·073)는 리스크 가설 없이 AC 직결로만 성립한다. ④리스크커버 축(PLAN H → 시나리오 매핑 완전)은 9/9로 충족하나, 역방향(시나리오 → H)이 비는 구간이다 | PLAN 커버 공백 | 가설 ID를 `해당 없음(E-5)`로 명시 기재하여 공란을 제거했다. 위임 계약·문서 갱신은 파괴 대상 계약이 없어 가설이 성립하지 않는 것이 정상이므로 PLAN 재작성은 불요 — PM Gate 기록으로 종결 |
| E-6 | **목표-커버 게이트 iteration 1 `verdict: fail`** (결정론 exit 0 / 판단축 ①=1·⑤=1·⑥=2, 평균 1.33 < 1.5). 0점 축은 없었고 평균 미달이 원인이다. 평가자가 제기한 6건을 전건 반영했다 — **G-1** TS-080 기대 결과를 (a)~(f) 6개 Pass/Fail 체크 항목으로 치환하고 「막힌 지점」을 참고 의견으로 강등 · **G-2** 목표 종점(승인→복사·등록) 미검증 해소를 위해 **TS-081** 신설(L2/M1, 격리 설치 루트) · **G-3** ⑤축 과대 표기 시정 — 회귀 보존 7건을 「잔존(회귀 보존)」으로 정직 표기하고 신형 채택 실행 검증 **TS-035** 신설 · **G-4** ⑥축 문언 검사 5건과 실행 검사 5건을 표기상 분리하고 등가 합산 제거 · **G-5** CAUTION 실동작 미검증 해소를 위해 `FX-CAUTION` 픽스처 + **TS-019** 신설 · **G-6** L1-a 25건에 `제목` 컬럼 추가 + TS-033·TS-071·TS-073 조건 예외 명기 | 게이트 반려 반영 | 시나리오 37 → **40건**. 픽스처 4종 추가(`FX-CAUTION`·`FX-MIXED`·`FX-APPROVE`·`BL-SKILL`). iteration 2 재호출 |
| E-7 | **PLAN 보완 필요 1건 (EXECUTE 디스패치 시 주입)** — 신규 TS-019·TS-035·TS-081은 PM 보강분이라 PLAN.md §4.2 Step 1(RED 픽스처 7종)·Step 9(검증) 작업 내용에 반영되어 있지 않다. TS-081은 격리 설치 루트가 필요해 `~/.opal/community-skills/`를 건드리지 않는 경로 오버라이드가 구현 요건으로 추가된다 | PLAN↔시나리오 델타 | PLAN.md를 재작성하지 않고 **EXECUTE 디스패치 프롬프트에 델타를 명시 주입**한다 — 픽스처 7종 → **10종**, 검증 대상 TS 33 → **40건** |
| E-8 | **목표-커버 게이트 iteration 2 `verdict: pass`** — ①=2·⑤=2·⑥=2, 평균 **2.0**, gaps 0. 평가자가 G-1~G-6 **전건 닫힘**으로 독립 확인했다(`SCENARIO-GATE-2.md`). 수렴 조건 성립: Step 3 exit 0 + Step 4 pass 두 증거 확보 | 게이트 통과 | `plan.scenario_gate` 행 mark 근거 |
| E-9 | **평가자 신규 검출 3건 — 점수 미반영이나 EXECUTE 전 교정 완료.** **N-1(중요)** TS-035·TS-081의 `M1` 지정이 구현 실물과 불일치했다 — 신규 코드는 `scan-risk` 1종뿐이고(`skill-registry.js:671-707` switch 6종 + 신설 1종) **복사·등록·추천 사다리는 `SKILL.md` 절차 소유**이므로 node 테스트가 이를 재구현해 단정하면 PLAN §C-5 self-confirming 회피 원칙과 충돌한다 → **M2(격리 `HOME`에서 `opal-test-agent`가 절차 수행, 수행자≠SKILL.md 작성자)로 재지정**했고, 격리를 `HOME` 환경변수로만 달성하므로 `--dest` 등 **신규 구현 요건이 0건**이 되어 PLAN §3 설계가 무변경으로 유지된다 · **N-2** TS-019가 실행 검사 라벨인데 기대 결과 3항 중 2항이 문언 검사였다 → 실행 단정만 남기고 문언 2항은 TS-030으로 이전 · **N-3** TS-080 서두 「5개 체크 항목」이 실제 (a)~(f) 6항과 불일치 → 6개로 정정 | 게이트 후 교정 | **E-7 철회** — N-1 해소로 신규 구현 요건이 사라져 PLAN 델타는 「픽스처 7→10종, 검증 TS 33→40건」만 남는다(프롬프트 주입으로 충분) |

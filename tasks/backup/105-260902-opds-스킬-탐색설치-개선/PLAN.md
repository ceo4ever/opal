# PLAN: opal-skill-manager 탐색·설치 절차에 보안 판정 축 + 후보 비교 도입

> 작성일: 2026-09-02 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석 수행)
> 모드: Multi-Feature (F 8개)

---

## 결론

- **절 번호를 보존한 in-place 재작성으로 간다** — `§1`·`§2`·`§6` 상위 절 번호를 그대로 두고 신규 규격(2층 비교 표·보안 4단·Match 등급·위임 계약)을 각 절의 하위 블록으로 삽입한다. `~/.opal/references/harness/skill-commands.md:24,36`이 `§6`·`§2`를 축자 지목하므로 절 번호 이동은 곧 포인터 파손이다.
- **1층 하드 필터는 `scan-risk <dir>` 신규 서브명령 1개로 도구화한다** — 기존 서브명령 6종(`match`/`get`/`list`/`validate`/`migrate`/`parse-source-repo`)의 출력 계약은 무수정이다. 특히 `list`는 OPAL Console이 소비한다(`dashboard/backend/adapters/skill_adapter.py:49-60`).
- **오탐 억제가 이 태스크의 최대 설계 리스크다** — 스킬 문서는 "`rm -rf`를 절대 쓰지 마라" 같은 금지 산문을 정상적으로 포함한다. 따라서 `.md`는 **코드펜스·인라인 코드 스팬 내부만** 검사하고, 부정 문맥어·주석·픽스처 경로 hit는 `context` 태그로 분리하여 **verdict 승격에서 배제**한다.
- **점수를 쓰지 않고 추천 1개를 결정론적으로 뽑는다** — 4축 3단 판정어 + 실측값 위에 **사전식(lexicographic) 우선순위 사다리** 5단을 얹는다. 가중치·합산 표기 0건을 유지한다(`~/.opal/PRINCIPLES.md` §Core Stance).
- **RED-first는 F-002에만 적용한다** — 신규 CLI 출력 계약 + 오탐 억제 규칙은 self-confirming 위험이 높다. 나머지 7개 F는 문서 재작성으로 「설정·문서」 트랙이다(`opal/core/references/harness/red-first.md` §1.5).
- **`trust`·`capabilities`·`scanned_at` 3필드는 스키마 교체 없이 추가 가능하다** — `validate()`가 community v2 스킬에 대해 `name`·`source_repo`·`license`만 검사하고 미지 필드를 무시함을 코드로 재확인했다(`opal/tools/skill-registry/skill-registry.js:435-462`).
- **리스크**: brain 페이지 stale 서술 2건, `match` 출력에 `matched_by` 필드 부재로 Exact/Partial 판정 근거 축소, 산문 영역 스캔 제외로 인한 false negative 잔존 — 아래 §리스크 가설 표 H-1~H-9.

---

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| 탐색 소스는 `skills.sh` 단일로 한정 (Phase 3·4 미채택) | 유효 | - |
| 후보 최대 3개 선별 + 3건 `git clone --depth 1` 임시 디렉토리 + 승인 게이트 설치 직전 1회 | 유효 | - |
| 100점 루브릭 폐기 → 2층 판정(1층 하드 필터 + 2층 3단 판정어), 점수 합산 금지 | 유효 | - |
| 보안 판정 4단(SAFE/CAUTION/RISKY/UNKNOWN) 도입 | 유효 | - |
| registry 신설 없이 기존 이원 구조 유지 + 필드 additive 추가 | 유효 | `opal/tools/skill-registry/skill-registry.js:435-462` — community v2 분기가 `name`·`source_repo`·`license`만 검사, 미지 필드 무시 확인 |
| 적합 스킬 미발견 시 `opal-skill-creator`로 위임 + 페이로드 계약 정의 | 유효 | `opal/skills/opal-skill-creator/SKILL.md` §Phase 1 실행 방법 — Capture Intent(목적·트리거·출력 형식) 입력 지점 실재 확인 |
| `//` 커맨드 자동 설치 정책(§6) 승인 게이트 수준 불변 | 유효 | - |
| `[사실]` 커뮤니티 스킬은 Global 전용(`~/.opal/community-skills/`), 플랫폼 네이티브 skills/ 복사 안 함 | 유효 (E2 확인) | `opal/skills/opal-skill-manager/SKILL.md:146` / `docs/ARCHITECTURE.md:195` |
| `[사실]` `skill-builder` 대응 컴포넌트가 `opal-skill-creator`로 이미 존재 | 유효 (E2 확인) | `opal/skills/opal-skill-creator/SKILL.md:1-7` |

> `사실오류` 판정 0건. 단, TASK.md §배경 분석의 인용 좌표 1건이 실제와 어긋난다 — TASK.md:20이 `skill-registry.js:402-470`을 「validate 필드 검사 범위」로 지목했고 실측 범위는 `402-470`이 맞으나(`validate()` 함수 시작 402, community v2 분기 435-462), PM 디스패치 프롬프트가 기재한 「현재 1071줄 규모」는 **실측 726줄**과 불일치한다(§리스크 H-8). 확정 지위에 영향을 주는 오류가 아니므로 `사실오류`로 격상하지 않는다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-skill-manager`의 커뮤니티 스킬 검색·설치 절차를 「skills.sh 검색 → 후보 최대 3 선별 → 3건 shallow clone → 2층 판정 → 추천 1개 → 승인 → 복사·등록」 6단 흐름으로 재작성한다. 현행 안전 판정 축이 라이선스 1축뿐이라(`opal/skills/opal-skill-manager/SKILL.md:183-203`) 라이선스가 확인된 스킬은 credential 접근·광범위 삭제·외부 실행 코드를 담고 있어도 그대로 통과한다. 이를 **위험 패턴 스캔 도구(1층 하드 필터)** + **보안 4단 판정(2층)** 으로 게이트하고, 후보 비교 표와 결정론적 추천 사다리를 도입한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 검색·설치 6단 흐름 재작성 (§1·§2 in-place, 절 번호 보존) | R-1 | P0 | F-002, F-003, F-004, F-006 |
| F-002 | 1층 하드 필터 도구화 — `scan-risk` 서브명령 + 위험 패턴 상수 + 오탐 억제 규칙 + 테스트 | R-2 | P0 | 없음 |
| F-003 | 2층 비교 표 규격 정의 (4축 3단 판정어/실측값, 점수 0건) + 추천 1개 결정 사다리 | R-3 | P0 | F-002 |
| F-004 | 보안 4단 판정 도입 (SAFE/CAUTION/RISKY/UNKNOWN) + 1층↔4단 매핑 표 | R-4 | P0 | F-002 |
| F-005 | user-registry 필드 additive 추가 (`trust`·`capabilities`·`scanned_at`) | R-5 | P0 | F-004 |
| F-006 | Match 등급화 (Exact / Partial / No Match) + 등급별 동작 | R-6 | P1 | 없음 |
| F-007 | `opal-skill-creator` 위임 계약 (페이로드 필드 정의) | R-7 | P1 | F-003 |
| F-008 | 변경이력 행 추가 + 외부 절 번호 앵커 축자 무결 검증 | R-8 | P0 | F-001~F-007 |

> **R 커버리지**: R-1→F-001 / R-2→F-002 / R-3→F-003 / R-4→F-004 / R-5→F-005 / R-6→F-006 / R-7→F-007 / R-8→F-008. **누락 0건 (8/8)**.

### 1.3 기능 의존 그래프 (ASCII)

```
F-002 (scan-risk 도구화) ──┬─→ F-003 (2층 비교 표) ──→ F-007 (creator 위임 계약) ──┐
                           │                                                       │
                           └─→ F-004 (보안 4단) ──→ F-005 (user-registry 필드) ────┤
                                     │                                             │
F-006 (Match 등급화) ────────────────┴─→ F-001 (§1·§2 6단 재작성) ────────────────┴─→ F-008 (변경이력 + 앵커 검증)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 `skill-registry.js` main() switch | 기존 서브명령 6종 출력 계약. 특히 `list` 무인자 호출이 JSON 배열을 반환해야 한다 — `dashboard/backend/adapters/skill_adapter.py:49-60`이 `isinstance(result, list)` 또는 `{skills:[...]}`를 기대하고 `dashboard/backend/tests/test_adapters.py:96-101`이 이를 단정한다. `scan-risk` 추가가 usage 문자열·switch 구조를 건드리면서 `list` 분기를 손상시키면 OPAL Console 스킬 화면이 즉시 파손된다 | P0 | L1(단위: `list` 출력 형상 회귀) + L2(통합: `test_adapters.py::test_skill_adapter_list` 실행) | S 후보: `scan-risk` 추가 전후 `node skill-registry.js list` 출력 바이트 동일성 + adapter 테스트 통과 |
| H-2 | F-001·F-008 SKILL.md 절 번호 | 외부 문서의 축자 앵커. `~/.opal/references/harness/skill-commands.md:24`가 `opal-skill-manager/SKILL.md §6`과 `§2`를, `:36`이 `§6`을 지목한다(소스: `opal/core/references/harness/skill-commands.md:24,36`). §1·§2 재작성 중 신규 절을 상위 레벨로 삽입해 번호가 밀리면 이 포인터가 무성 파손된다 (grep으로만 검출 가능, 런타임 에러 없음) | P0 | L1(정적: `grep -F` 축자 일치 + `### 2.`·`### 6.` 헤딩 잔존 확인) | S 후보: 개정 후 `grep -Fn 'opal-skill-manager/SKILL.md §6'`·`§2` hit ≥1 && SKILL.md에 `### 2. 스킬 설치`·`### 6.` 헤딩 존재 |
| H-3 | F-002 위험 패턴 목록 | **오탐(false positive)** — 스킬 문서는 금지 서술("`rm -rf`를 쓰지 마라", "`sudo` 없이 실행")·설명 예시·테스트 픽스처에 위험 토큰을 정상적으로 포함한다. 무조건 매칭하면 무해 스킬이 RISKY로 판정되어 추천 후보에서 전량 탈락하고, 절차가 「후보 3개 전부 제외」로 기능 정지한다 | P0 | L1(단위: 무해 픽스처 6종 — 금지 산문/주석/픽스처 경로/인라인 코드 설명/`.env` 언급/장문 라인 → active hit 0건) | S 후보: 무해 픽스처에서 `verdict == "SAFE"` && `hits[].context=="active"` 0건 |
| H-4 | F-002 위험 패턴 목록 | **미탐(false negative)** — `.md` 산문 영역을 검사 제외하므로, 코드펜스 밖 산문으로 위험 행동을 지시하는 스킬("홈 디렉토리를 정리하려면 rm 명령으로 전체 삭제하라")은 통과한다. 1층이 게이트라고 오신뢰되면 보안 축이 형식화된다 | P1 | L1(단위: 산문 지시형 픽스처 → hit 0건이 **의도된 동작**임을 테스트로 고정) + 문서에 한계 명시 | S 후보: 산문 지시 픽스처가 SAFE로 나오는 것을 기대값으로 단정 + SKILL.md에 「1층은 필요조건이며 사람 검토를 대체하지 않는다」 문장 존재 |
| H-5 | F-005 user-registry 필드 추가 | registry 항목 스키마. `validate()`가 신규 3필드를 미지 필드로 무시해야 한다(`opal/tools/skill-registry/skill-registry.js:435-462`). 또한 `loadAllSkills()`가 user-registry를 `flattenGroups`로 병합하므로 `groups[vendor][]` 형상을 벗어난 기록(flat 배열 등)은 조용히 무시되어 설치 이력이 유실된다(`opal/tools/skill-registry/skill-registry.js:125-143`, `58-74`) | P1 | L1(단위: 3필드 포함 user-registry 픽스처 → `validate` errors 0건) + L2(`list --group=community`가 해당 항목을 반환) | S 후보: `trust`/`capabilities`/`scanned_at` 포함 항목으로 `validate` exit 0 + `groups[vendor][]` 형상 위반 시 유실 재현 |
| H-6 | F-006 Match 등급화 | `match` 출력에 **`matched_by` 필드가 없다** — alias 경로(`matchByAlias`)와 triggers 경로(`matchByTriggers`) 중 무엇이 매칭했는지 응답에서 구분 불가하다(`opal/tools/skill-registry/skill-registry.js:277-317`). Exact/Partial 경계를 도구 출력만으로 결정론 판정할 수 없어 산문 판단으로 흐를 위험 | P1 | L1(정적: SKILL.md의 등급 판정 규칙이 `name`/`alias` 문자열 동일성 비교라는 기계적 조건으로만 기술되었는지 검사) | S 후보: 등급 판정 규칙에 「검색어와 반환 `name` 또는 `alias`의 문자열 동일성」이 명시되고 주관적 형용사 0건 |
| H-7 | F-002 정규식 상수 | ReDoS. `skill-registry.js`는 registry `triggers`에 대해 `isUnsafeRegex()` 휴리스틱(`MAX_PATTERN_LENGTH=100`/`MAX_DOTSTAR_COUNT=2`/nested quantifier)을 이미 운용한다(`opal/tools/skill-registry/skill-registry.js:145-166`). 위험 패턴 상수는 코드 소유이지만 clone된 외부 파일 내용을 입력으로 받으므로, nested quantifier 패턴이 들어가면 악성 스킬이 스캐너 자체를 정지시킬 수 있다 | P1 | L1(단위: 전 패턴이 `isUnsafeRegex()` 기준을 통과 + 100KB 병리 입력에서 스캔 3초 내 종료) | S 후보: 위험 패턴 상수 전건 nested quantifier 0건 + 대용량 반복 문자열 파일 스캔 타임박스 |
| H-8 | 문서·코드 불일치 (분석 전제) | brain 페이지 `.opal/brain/pages/concept/community-skill-user-registry.md`의 stale 서술 2건이 후속 워커에게 잘못된 전제를 주입한다 — ① "registry 등재 스킬 → `~/.opal/references/community-skills-registry.json` 기존 항목에 `commit_sha` 갱신 가능"은 현행 `opal/skills/opal-skill-manager/SKILL.md:102`의 `[MUST] ... 설치 시 수정하지 않는다`와 정면 충돌 ② `loadAllSkills()` 예시 코드가 flat 배열 병합으로 묘사되었으나 실제는 `groups[vendor][]` + `flattenGroups` 경유(`opal/tools/skill-registry/skill-registry.js:125-143`). 추가로 PM 프롬프트의 「skill-registry.js 1071줄」은 실측 726줄과 불일치 | P2 | L1(정적: PLAN·EXECUTE 산출물이 카탈로그 갱신 절차를 기술하지 않았는지 검사) | S 후보: 개정된 SKILL.md에 카탈로그 파일 쓰기 지시 0건 + `[MUST]` 금지 문장 잔존 |
| H-9 | F-003 추천 1개 선정 | 재현 불가 판정. 4축 3단 판정어만으로는 동률 후보가 발생하며, 여기서 「종합적으로 판단」류 산문이 들어가면 같은 후보 집합의 재실행 결과가 달라진다 — 100점 루브릭을 폐기한 이유와 동일한 실패모드로 회귀한다(`~/.opal/PRINCIPLES.md` §Core Stance) | P1 | L1(정적: 추천 규칙이 순서 있는 사다리로 기술되고 동률 시 사용자 선택 요청으로 종료되는지 검사) | S 후보: SKILL.md에 우선순위 사다리 5단 존재 + 점수·가중치·합산 표기 0건(`grep -E '점수\|가중치\|합산\|/100'` hit 0) |

**보강 지시**: H-1·H-2·H-3은 P0이며 검증 계층이 각각 다르다(런타임 계약 / 정적 축자 / 단위 픽스처). TEST-SCENARIO 작성 시 3건을 별개 시나리오로 분리한다.

---

## 2. 기능별 분석

### F-001: 검색·설치 6단 흐름 재작성

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §1 검색(29-70) · §2 설치(72-108) 본문 | 수정 |
| 가이드 | `opal/core/references/harness/skill-commands.md` | `§6`·`§2` 축자 앵커 보유(24, 36) | 무변경 (검증 대상) |
| 문서 | `docs/ARCHITECTURE.md` | 커뮤니티 스킬 설치 정책 서술(189-197) | 수정 (F-008 Step) |

#### 2.1.2 현재 구현

현행 §1은 2단계(1단계 설치 여부 대조 `match` → 2단계 `npx skills find` 생태계 검색 + 폴백 안내)이며, 후보 비교·추천 절차가 없다(`opal/skills/opal-skill-manager/SKILL.md:29-70`). 현행 §2는 6단계 절차(파싱 → clone → 복사 원본 4단 폴백 탐지 → commit_sha 확보 → tmp 정리 → user-registry 기록)로, clone 대상은 **사용자가 이미 지목한 1건**이다(`:72-108`). 즉 「3건 clone 후 대조」 개념 자체가 없다.

상위 절 헤딩은 `### 1. 스킬 검색`(29) / `### 2. 스킬 설치 (clone-copy 단일 방식)`(72) / `### 3.`(110) / `### 4.`(122) / `### 5.`(132) / `### 6.`(176) 이며, `## 설치 경로 규칙`(144)·`## 참고`(169)가 §5와 §6 사이에 끼어 있다 — 즉 번호 절과 비번호 절이 혼재한다. 이 배치가 절 번호 보존 전략의 제약 조건이다.

#### 2.1.3 영향 범위

- **호출자**: `~/.opal/references/harness/skill-commands.md:24,36` — `//` 커맨드 라우팅이 `§6`·`§2`를 축자 지목 (H-2)
- **도구 측 참조**: `matchCommand`의 `install_command` 문자열이 `opal-skill-manager §설치 (clone-copy: ...)`로 **절 이름 기반**이다(`opal/tools/skill-registry/skill-registry.js:286`) — 절 번호가 아니므로 이 경로는 안전하다. 단 「설치」라는 절 이름은 보존해야 한다.
- **문서**: `docs/ARCHITECTURE.md:189`이 "라이선스가 확인된 스킬은 자동 설치, Unknown 라이선스만 확인 게이트를 거친다"로 서술 — 보안 4단 도입 후 stale이 된다.

---

### F-002: 1층 하드 필터 도구화 (`scan-risk`)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` | CLI 라우터 + 서브명령 구현 (726줄, CommonJS, 외부 의존 0) | 수정 |
| 도구 | `opal/tools/skill-registry/tests/test-scan-risk.js` | 신규 단위 테스트 (RED-first) | 신규 |
| 도구 | `opal/tools/skill-registry/tests/test-validate.js` | 기존 테스트 패턴 원본 (CLI 블랙박스 + `mkdtempSync` 합성 픽스처) | 무변경 (참조) |
| 공통 | `dashboard/backend/adapters/skill_adapter.py` | `list` 무인자 호출 소비자 | 무변경 (회귀 검증 대상) |

#### 2.2.2 현재 구현

- CLI 라우터 `main()`은 `skill-registry.js:653-724`. `args[0]`을 `switch`로 분기하며 서브명령 6종(`match`/`get`/`list`/`validate`/`migrate`/`parse-source-repo`)을 처리하고, 미지 명령은 `default`에서 `Unknown command: {cmd}` + `process.exit(1)`이다(`:715-717`).
- 종료 코드 규약: 결과를 `console.log(JSON.stringify(result, null, 2))`로 출력한 뒤 `result.error` 또는 `result.valid === false`일 때만 `exit 1`이다(`:720-723`). 즉 **정상 실행은 항상 exit 0이고 판정은 JSON 본문으로 전달**하는 것이 이 도구의 기존 계약이다.
- usage 안내는 `:658-666`에 서브명령별 1줄로 열거된다.
- 의존은 Node 내장 3종(`fs`/`path`/`os`)뿐이다(`:46-48`).
- ReDoS 방어 상수·헬퍼가 이미 존재한다: `MAX_INPUT_LENGTH=256`/`MAX_PATTERN_LENGTH=100`/`MAX_DOTSTAR_COUNT=2` + `isUnsafeRegex()` (`:145-166`).
- `list` 출력은 `listCommand()`가 `filtered.map(...)`으로 **배열**을 반환한다(`:340-369`). community 스킬 항목에만 `installed` 필드를 덧붙인다(`:361-364`).

기존 테스트 3종의 공통 패턴(`opal/tools/skill-registry/tests/test-validate.js:23-30`, `test-migrate.js:35-45`):
- `node:test` + `node:assert/strict` + `node:child_process.spawnSync` — **CLI 블랙박스** 검증
- `fs.mkdtempSync(path.join(os.tmpdir(), ...))`로 실 파일시스템 합성 픽스처 — mock/monkeypatch 0
- 파일 상단 인라인 `@header` 블록(`@module`/`@layer`/`@domain`/`@description`/`@depends`) + TC↔시나리오 매핑 주석 + 변경이력 주석
- `after()`로 픽스처 정리

#### 2.2.3 영향 범위

- **직접 의존**: `main()` switch에 case 1개 + usage 1줄 추가. 기존 case 블록 무수정.
- **간접 의존**: `dashboard/backend/adapters/skill_adapter.py:49-60` → `node skill-registry.js list` 무인자 호출. `dashboard/backend/tests/test_adapters.py:96-101`이 `isinstance(result, list)`를 단정. **`list` 분기·`listCommand()` 무수정이 필수 제약**(H-1).
- **공유 상태**: 없음. `scan-risk`는 인자로 받은 디렉토리만 읽고 아무것도 쓰지 않는다(read-only).
- **@header 처리**: `node ~/.opal/tools/code-scan/code-scan.js target opal/tools/skill-registry/skill-registry.js` → `write_to: inline` / `reason: header_source_inline` (실행 관측, E1). 즉 **인라인 주석 헤더를 갱신**하며 `.opal/code-map/`은 쓰지 않는다.

---

### F-003: 2층 비교 표 규격 정의

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §2 내 비교 표 규격 블록 | 수정 |

#### 2.3.2 현재 구현

비교·평가 절차가 존재하지 않는다. §1 2단계는 `npx skills find` 결과를 `| 스킬명 | 설명 | 설치 |` 3열 표로 나열하고 Unknown 라이선스에 경고를 붙이는 데서 끝난다(`opal/skills/opal-skill-manager/SKILL.md:51-59`). 어느 후보가 나은지 판단하는 축·표기·근거 인용 규칙이 0건이다.

#### 2.3.3 영향 범위

F-001의 4단(2층 판정)·5단(추천 1개)이 이 규격을 소비한다. F-007 위임 페이로드의 「후보별 미달 사유」가 이 표의 미달 축을 그대로 인용한다.

---

### F-004: 보안 4단 판정 도입

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §2 내 4단 판정 표 + §6 배선 | 수정 |

#### 2.4.2 현재 구현

안전 판정은 §6 분기 판정 4갈래이며 축은 `license`·`source_repo`·`ambiguous` 3필드뿐이다(`opal/skills/opal-skill-manager/SKILL.md:183-207`):

1. `license ≠ "Unknown"` + `source_repo` 있음 → **동의 prompt 없이 자동 설치·실행**(`:185-191`)
2. `license == "Unknown"` → y/N 확인 게이트, 디폴트 `N`(`:192-203`)
3. `source_repo == null` → 미등재 안내(`:204-205`)
4. `ambiguous: true` → candidates 표시 후 정식명 재호출 유도(`:206-207`)

즉 **RISKY 개념이 없고**, 라이선스가 확인되면 본문 내용과 무관하게 1번 경로로 자동 설치된다. 이것이 이 태스크의 배경 문제다.

#### 2.4.3 영향 범위

- §6의 1번 경로에 보안 판정을 배선해야 하지만, TASK.md §확정된 설계 방향은 「§6 승인 게이트 **수준** 자체는 변경하지 않는다」로 못박았다. 따라서 §6에는 **판정 결과를 참조하는 최소 연동**만 넣는다(아래 §3.4.2 (c)).
- `docs/ARCHITECTURE.md:189`의 정책 서술이 stale이 된다 → F-008 docs 갱신 Step.

---

### F-005: user-registry 필드 additive 추가

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §2 user-registry.json 기록 규칙(104-108) | 수정 |
| 도구 | `opal/tools/skill-registry/skill-registry.js` | `validate()` 미지 필드 무시 동작 | **무변경** |

#### 2.5.2 현재 구현

- 기록 규칙: 경로 `~/.opal/community-skills/user-registry.json`, 스키마는 카탈로그와 동일 `groups[vendor][] = [{name, alias, description, triggers, source_repo, commit_sha, license}]` 7필드, 부재 시 생성·존재 시 병합, 동일 `name`은 override (`opal/skills/opal-skill-manager/SKILL.md:104-108`).
- 카탈로그 실측: `$schema: "opal-community-skills-registry-v2.1"`, `groups` 키 7종(`anthropics`/`google-labs-code`/`vercel-labs`/`trailofbits`/`getsentry`/`openai`/`obra`), 항목 형상은 위 7필드와 일치 (`opal/core/references/community-skills-registry.json`, E1 파싱 관측).
- `validate()` community v2 분기는 `source_repo` 미정 → warning, `license` 부재·Unknown → warning, `paths` 미검사이며 **미지 필드에 대한 검사·거부 로직이 없다**(`opal/tools/skill-registry/skill-registry.js:435-462`). name 중복·alias 중복만 error다(`:465-473`).
- `loadUserRegistry()`는 부재/파손 시 `null`을 반환해 CLI 다운을 막고(`:115-123`), `loadAllSkills()`가 `flattenGroups(userReg, 'community')`로 병합하며 동일 `name`은 사용자 항목이 override한다(`:125-143`).
- **런타임 실측**: `~/.opal/community-skills/user-registry.json`은 **미존재**(설치 이력 기록 0건). 반면 `~/.opal/community-skills/` 하위에는 `anthropics/`·`getsentry/`·`google-labs-code/`·`obra/`·`openai/`·`modern-python/` 6개 디렉토리가 실재한다 — 즉 기록 없는 설치분이 이미 있고, `modern-python/`은 vendor 미중첩 flat 잔재다(`migrate` 훅 대상).

#### 2.5.3 영향 범위

필드 3개 추가는 `validate`·`match`·`list` 어디에도 영향이 없다(미지 필드 무시). 단 `groups[vendor][]` 형상을 벗어나면 `flattenGroups`가 조용히 건너뛴다(`:58-74`) — 기록 규칙 문구에 형상 제약을 명시해야 한다(H-5).

---

### F-006: Match 등급화

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §1 1단계(33-43) | 수정 |

#### 2.6.2 현재 구현

§1 1단계는 `match` 결과를 3갈래로 처리한다(`opal/skills/opal-skill-manager/SKILL.md:33-43`): `installed: true` → 안내 + 추가 검색 질의 / `ambiguous: true` → candidates 표시 + 정식명 재호출 / `installed: false` 또는 미매칭 → 2단계 진행. 등급 개념·「Exact 시 외부 검색 금지」 규칙이 없어, 설치된 스킬이 정확히 매칭돼도 사용자가 원하면 외부 검색으로 흘러간다.

`matchCommand` 반환 필드(community 경로): `found`·`name`·`group`·`alias`·`description`·`path`·`domain`·`cleanInput`·`installed`·`source_repo`·`license`·`install_command`·`install_method` (`opal/tools/skill-registry/skill-registry.js:286-302`). ambiguous 경로는 `found`·`ambiguous`·`alias`·`candidates[]`·`cleanInput` (`:259-271`). 미매칭은 `{found:false, input}` (`:317`).

**`matched_by` 필드 부재** — alias 경로(`matchByAlias`, `:273-274` 이전 분기)와 triggers 경로(`matchByTriggers`, `:274`) 중 무엇이 매칭했는지 응답에 노출되지 않는다(H-6).

#### 2.6.3 영향 범위

`skill-commands.md`가 소비하는 필드는 `installed`·`ambiguous`·`candidates`뿐이다(`opal/core/references/harness/skill-commands.md:24-25`). 등급화는 SKILL.md 내부 서술이므로 외부 계약 영향 0.

---

### F-007: `opal-skill-creator` 위임 계약

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | 위임 계약 블록 (§1 내) | 수정 |
| 스킬 | `opal/skills/opal-skill-creator/SKILL.md` | 위임 수신 측 입력 형식 | 무변경 (참조) |

#### 2.7.2 현재 구현

skill-manager에 위임 절차가 0건이다. `opal-skill-creator`의 입력 지점은 Phase 1 신규 생성 모드의 skill-creator 6단 프로세스이며, 1단이 **Capture Intent — 스킬 목적, 트리거, 출력 형식 파악**, 2단이 **Interview and Research — 에지 케이스, 입출력 형식, 의존성 확인**이다(`opal/skills/opal-skill-creator/SKILL.md:63-64`). 또한 OPAL 규칙(한국어 본문/명령형/500줄 이하/`references/` 분리)을 컨텍스트로 전달하도록 지시한다(`:72-77`). 즉 위임 페이로드는 **Capture Intent 3항목 + Interview 입력**을 선충족하는 형태여야 재입력이 발생하지 않는다.

#### 2.7.3 영향 범위

수신 측 무변경. 페이로드는 F-003 비교 표의 미달 축을 인용하므로 F-003 확정 후 작성해야 한다.

---

### F-008: 변경이력 + 절 번호 앵커 무결 검증

#### 2.8.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §변경이력 표(209-217) | 수정 |
| 가이드 | `opal/core/references/harness/skill-commands.md` | 축자 앵커 보유 | 무변경 (검증) |
| 문서 | `docs/ARCHITECTURE.md` | 커뮤니티 스킬 정책 서술(189-197) | 수정 |

#### 2.8.2 현재 구현

변경이력 표는 `| 버전 | 일시 | 변경내용 |` 3열이고 최신 행이 `v1.4.1 | 2026-07-17 09:26 KST | ... (064 S-9 fix)`다(`opal/skills/opal-skill-manager/SKILL.md:211-217`). 일시 포맷은 `YYYY-MM-DD HH:mm KST`, 변경내용에 태스크 번호를 괄호로 포함한다 — `docs/CONVENTIONS.md` §변경이력 작성 의무와 일치.

#### 2.8.3 영향 범위

`install-mac.sh`가 배포 시 변경이력 섹션을 자동 strip 한다(`docs/CONVENTIONS.md` §변경이력 작성 의무) — 소스에만 유지되므로 배포본 검증 대상이 아니다.

---

## 3. 기능별 설계

### F-001: 검색·설치 6단 흐름 재작성

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | `### 1. 스킬 검색`(29-70)·`### 2. 스킬 설치 (clone-copy 단일 방식)`(72-108)을 6단 흐름으로 in-place 재작성. **상위 절 번호·절 이름 보존** | `opal/core/references/harness/skill-commands.md:24,36` (§2·§6 축자 앵커) |

#### 3.1.2 설계

**(a) [MUST] 절 번호 보존 규칙**

[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리는 스킬 본문의 조건문을 금지하나, 절 구조 자체에 대한 규정은 없다. 대신 외부 축자 앵커 보호를 위해 아래를 강제한다:

- [MUST] `### 1.`·`### 2.`·`### 3.`·`### 4.`·`### 5.`·`### 6.` 여섯 개 H3 번호 절의 **번호와 순서를 변경하지 않는다**.
- [MUST] `### 2.` 절 이름에 `설치` 문자열을 유지한다 — `matchCommand`가 `install_command`에 `opal-skill-manager §설치 (clone-copy: ...)`를 생성한다(`opal/tools/skill-registry/skill-registry.js:286`).
- [MUST] 신규 규격(2층 비교 표·보안 4단 판정·Match 등급·위임 계약)은 **`####` 이하 하위 헤딩 또는 굵은 라벨 블록**으로 기존 절 내부에 삽입한다. 새 H3 번호 절을 §2와 §6 사이에 만들지 않는다.
- 신규 최상위 절이 불가피하면 `### 6.` **뒤에만** 추가한다(뒤 추가는 기존 번호를 밀지 않는다).

**(b) 6단 흐름 배치**

| 단 | 단계명 | 배치 절 | 입력 | 출력 |
|----|--------|--------|------|------|
| 1 | skills.sh 검색 | §1 | 사용자 검색어 | `npx skills find` 결과 항목 목록 (`name`·`description`·`source_repo`·`license`) |
| 2 | 후보 최대 3 선별 | §1 | 1단 결과 목록 | 후보 표 (최대 3행, `name`·`source_repo`·`license`) |
| 3 | 3건 shallow clone | §2 | 후보 표 | 후보별 임시 디렉토리 경로 + `commit_sha` |
| 4 | 2층 판정 | §2 | 후보별 임시 디렉토리 경로 | 후보별 1층 결과(`scan-risk` JSON) + 보안 4단 판정 + 2층 비교 표 |
| 5 | 추천 1개 | §2 | 2층 비교 표 | 추천 후보 1건 + 추천 사유(축별 인용) + 탈락 후보별 사유 |
| 6 | 승인 → 복사·등록 | §2 | 추천 후보 1건 | `~/.opal/community-skills/{vendor}/{basename}/` 복사 완료 + `user-registry.json` 항목 기록 |

**(c) [MUST] clone은 임시, 복사가 설치**

[MUST] 본문에 아래 2문을 명시한다 (R-1 AC):
- `git clone --depth 1`의 대상은 **임시 디렉토리**이며 clone 자체는 설치가 아니다.
- **설치는 `~/.opal/community-skills/{vendor}/{basename}/`로의 복사 시점에 성립**하므로, 승인 게이트는 6단(복사 직전) 1회를 유지한다.

근거: `opal/skills/opal-skill-manager/SKILL.md:81-99` (현행 clone→복사 순서) / TASK.md §확정된 설계 방향 「승인 게이트는 설치 직전 1회를 유지한다」.

**(d) 복사 원본 탐지 폴백 보존**

[MUST] 현행 §2 3단계의 4단 폴백 탐지(`{tmp}/{subdir}/SKILL.md` → `{tmp}/skills/{basename}/SKILL.md` → `find {tmp} -maxdepth 3 -type d -name {basename}` → 실패 시 후보 경로 목록 보고 후 중단)를 6단 흐름의 3단·6단에 그대로 승계한다 — 실 clone으로 검증된 동작이다(`opal/skills/opal-skill-manager/SKILL.md:85-94`, 064 S-9). **빈 디렉토리 복사 금지** 규칙도 유지한다.

**(e) 후보 수 상한 처리**

- 1단 결과가 4건 이상이면 상위 3건만 3단으로 보낸다. 선별 기준은 결정론적 순서 — ① `license != "Unknown"` 우선 ② `source_repo` 있음 우선 ③ `npx skills find` 출력 순서. 「관련성 높은 순」 같은 주관 기준을 쓰지 않는다(H-9).
- 1단 결과가 0건이면 6단으로 가지 않고 **F-007 위임 경로**로 분기한다.

**(f) 3건 clone의 비용·정리**

- 3건 clone은 `--depth 1`이므로 후보당 수 MB 수준이다. 각 후보별 임시 디렉토리를 별도 `mktemp -d`로 만들고, 5단 추천 확정 후 **채택 1건을 제외한 나머지를 즉시 삭제**하며 6단 완료 후 전량 삭제한다.
- [MUST] 삭제 경로가 임시 디렉토리 하위임을 검증한 뒤 `rm -rf`를 수행한다 — §4 삭제 절차가 이미 동일한 경로 검증 규율을 쓴다(`opal/skills/opal-skill-manager/SKILL.md:127`).

#### 3.1.3 환경 변경

해당 없음 (신규 패키지 0 — `git`·`npx`·`node`는 현행 절차가 이미 사용).

#### 3.1.4 배치/마이그레이션

해당 없음. 단 §관리 진입 훅의 `migrate` 1회 멱등 실행은 현행 그대로 유지한다(`opal/skills/opal-skill-manager/SKILL.md:14-25`).

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (6단 존재) | 산출물 검사 | §1·§2에 6단이 순서대로 절 또는 번호 항목으로 존재하고, 각 단에 「입력」·「출력」이 각 1줄 이상 명시된다 |
| TS-002 | R-1 AC (clone=임시, 복사=설치) | 산출물 검사 | `git clone --depth 1`이 임시 디렉토리 대상임과 복사가 설치임을 명시한 문장이 각 1건 이상 존재 |
| TS-003 | R-1 AC + H-2 | 산출물 검사 | `### 1.`~`### 6.` H3 번호 절 6개가 번호·순서 그대로 잔존하고, `### 2.` 절 이름에 `설치` 문자열이 포함된다 |

---

### F-002: 1층 하드 필터 도구화 (`scan-risk`)

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/skill-registry/tests/test-scan-risk.js` | 도구 | `scan-risk` CLI 블랙박스 단위 테스트 (RED-first) | `opal/tools/skill-registry/tests/test-validate.js:23-30` (동일 패턴) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | 위험 패턴 상수 `RISK_PATTERNS` + 오탐 억제 상수 + `scanRiskCommand(dir)` 신설, `main()` switch에 `case 'scan-risk'` + usage 1줄 추가, 인라인 `@header`의 `@exports`·변경이력 갱신 | `opal/tools/skill-registry/skill-registry.js:653-724` / `code-scan target` → `write_to: inline` |

#### 3.2.2 설계

**(a) [MUST] 무수정 경계**

[MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." — 아래를 손대지 않는다:
- `listCommand()` (`:340-369`) 및 `case 'list'` 분기 (`:691-700`) — OPAL Console 소비 계약 (H-1)
- `matchCommand`·`getCommand`·`validate`·`migrateCommand`·`parseSourceRepo` 본문 전량
- `main()`의 종료 코드 규약 (`:720-723`)
- `loadAllSkills`·`flattenGroups`·`getReferencesDir` 등 데이터 로딩 계층

**(b) 함수 시그니처**

```
scanRiskCommand(dir: string) -> {
  ok: boolean,              // 스캔 수행 성공 여부
  verdict: 'SAFE'|'CAUTION'|'RISKY'|'UNKNOWN',
  dir: string,              // 정규화된 절대 경로
  scanned: number,          // 검사한 파일 수
  hits: Array<{
    id: string,             // 패턴 ID (RP-01 ~ RP-10)
    severity: 'high'|'medium',
    capability: string,     // R-5 capabilities 라벨 (아래 (e))
    file: string,           // dir 기준 상대 경로
    line: number,           // 1-based
    excerpt: string,        // 매칭 라인 (최대 200자 truncate)
    context: 'active'|'prose'|'negated'|'comment'|'fixture'
  }>,
  skipped: Array<{ file: string, reason: string }>,
  error?: string            // ok:false 일 때만
}
```

- 반환은 `case 'scan-risk'`에서 그대로 `result`에 담기며 `main()`이 JSON을 stdout에 출력한다(`:720`).
- **종료 코드**: 스캔이 수행되면 verdict와 무관하게 **exit 0**, 스캔 불가(디렉토리 부재/SKILL.md 부재/전 파일 skip)면 `{ok:false, error:...}`로 기존 `result.error` 규약을 타 **exit 1**이 된다(`:721-723`). R-2 AC의 「비-0 종료 **또는** 검출 목록 JSON 반환」 중 후자를 채택한다 — 절차가 verdict를 읽어 4단 판정으로 넘겨야 하므로 검출이 곧 실패여서는 안 된다.

**(c) 위험 패턴 목록 (구체 후보안)**

`RISK_PATTERNS` 코드 상수. [MUST] 전 패턴은 nested quantifier를 쓰지 않고 선형이어야 한다 — `isUnsafeRegex()`가 이미 같은 기준을 운용한다(`opal/tools/skill-registry/skill-registry.js:145-166`, H-7).

| ID | 대상 행위 | 패턴(개념) | severity | 사유 |
|----|----------|-----------|----------|------|
| RP-01 | 광범위 삭제 | `rm` + `-r`/`-f` 계열 플래그 + 대상이 `/`·`~`·`$HOME`·`*` | high | 사용자 데이터 비가역 파괴 |
| RP-02 | 권한 상승 | 라인 선두 또는 `;`/`&&`/`\|` 직후의 `sudo` | high | 시스템 전역 변경 |
| RP-03 | 원격 코드 실행 | `curl` 또는 `wget` 출력이 파이프로 `sh`/`bash`/`zsh`(선택 `sudo`)에 투입 | high | 미검증 코드 실행 — 스캔 자체를 무의미화 |
| RP-04 | credential 접근 | `~/.ssh`, `id_rsa`, `id_ed25519`, `.aws/credentials`, `.netrc`, `.npmrc`, `security find-generic-password` | high | 자격증명 탈취 |
| RP-05 | 비밀 파일 접근 | `.env` 파일 경로 참조 | medium | 정상 용례 다수(프로젝트 설정 읽기) — 단독으로는 high 아님 |
| RP-06 | 동적 실행 | `eval` 호출 형태(`eval` + 여는 괄호/따옴표/백틱) | medium | 난독화 실행 경로 |
| RP-07 | 난독화 | `base64 -d` / `base64 --decode` / `base64 -D` | medium | 페이로드 은닉 |
| RP-08 | 데이터 유출 | `curl`에 `-X POST`·`--data`·`-d ` 중 하나 동반 | medium | 로컬 데이터 외부 전송 |
| RP-09 | 권한 완화 | `chmod` + `777` (선택 `-R`) | medium | 파일 권한 무력화 |
| RP-10 | 지속성 확보 | `crontab -`, `launchctl load`, `~/Library/LaunchAgents` | medium | 스킬 실행 종료 후 잔존 |

> TASK.md 예시 7종(`rm -rf`·`sudo`·`curl\|wget … \| sh`·`~/.ssh`·`.env`·`eval`·`base64 -d`)은 RP-01·02·03·04·05·06·07로 전건 대응한다. RP-08~10은 동일 위협 축(유출·권한·지속성)의 최소 확장이며, 그 이상은 추가하지 않는다 — [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."

**(d) [MUST] 오탐 억제 규칙 — 검사 범위 4중 축소**

이 규칙이 H-3의 유일한 방어선이다.

| # | 규칙 | 근거 |
|---|------|------|
| 억제-1 | **파일 확장자 화이트리스트** — `.md`·`.sh`·`.bash`·`.zsh`·`.js`·`.mjs`·`.cjs`·`.py`·`.rb`·`.ts`만 검사. `.git/`·`node_modules/`·`dist/`·`build/` 디렉토리와 바이너리(NUL 바이트 포함 파일)는 `skipped[]`로 기록하고 건너뛴다 | 이미지·바이너리에서 우연 일치 제거 |
| 억제-2 | **`.md`는 코드 영역만 검사** — 코드펜스(``` 또는 ~~~) 내부 라인과 인라인 코드 스팬(백틱으로 감싼 구간)만 검사 대상이다. 순수 산문 라인의 매칭은 `context: 'prose'`로 기록만 하고 verdict 승격에 쓰지 않는다 | 스킬 문서의 금지·설명 서술이 최대 오탐원 (H-3) |
| 억제-3 | **부정 문맥 배제** — 매칭 라인에 부정 토큰(`절대`, `금지`, `하지 마`, `never`, `do not`, `don't`, `avoid`, `MUST NOT`, `SHOULD NOT`, `無`)이 함께 있으면 `context: 'negated'`로 기록하고 verdict 승격에서 제외 | "`rm -rf`를 절대 쓰지 마라"류 정상 서술 |
| 억제-4 | **주석·픽스처 강등** — 코드 파일에서 라인이 주석으로 시작(`#`·`//`·`*`)하면 `context: 'comment'`, 파일 경로가 `tests/`·`test/`·`fixtures/`·`__fixtures__/`·`examples/` 하위면 `context: 'fixture'`로 기록하고 verdict 승격에서 제외 | 테스트 픽스처가 위험 문자열을 정상 포함 |

추가 가드:
- 라인 길이 2000자 초과 라인은 검사하지 않고 `skipped[]`에 기록한다 (성능·ReDoS, H-7).
- 파일 크기 1MB 초과는 `skipped[]` 기록 후 건너뛴다.
- [MUST] `hits[]`는 배제된 항목까지 **전량 반환**한다 — 배제 사실이 `context`로 감사 가능해야 한다. 은닉하지 않는다.

**(e) verdict 산출 규칙 (도구 측)**

`context === 'active'` hit만 사용한다:

| 조건 | verdict |
|------|---------|
| `ok === false` (스캔 불가) | `UNKNOWN` |
| active hit 중 `severity === 'high'` ≥ 1건 | `RISKY` |
| active high 0건 && active `severity === 'medium'` ≥ 1건 | `CAUTION` |
| active hit 0건 | `SAFE` |

[MUST] 도구는 라이선스를 판정 입력으로 쓰지 않는다 — 라이선스 축은 SKILL.md가 §3.4.2 (b) 표에서 합성한다. 도구 책임은 「본문 위험 패턴」 단일 축으로 봉인한다.

`capability` 라벨(R-5 `capabilities` 필드의 값): RP-01→`fs:destructive` / RP-02→`system:privilege` / RP-03→`exec:remote` / RP-04→`secret:credential` / RP-05→`secret:env` / RP-06→`exec:dynamic` / RP-07→`obfuscation:base64` / RP-08→`network:outbound` / RP-09→`fs:permission` / RP-10→`system:persistence`.

**(f) main() 배선**

- usage 블록(`:658-666`)에 1줄 추가: `scan-risk <dir>    clone 디렉토리 위험 패턴 스캔 (1층 하드 필터)`
- usage 첫 줄의 서브명령 열거에 `scan-risk` 추가
- switch에 case 추가 (기존 case 무수정):

```
case 'scan-risk':
  if (!args[1]) { console.error('Usage: skill-registry.js scan-risk <dir>'); process.exit(1); }
  result = scanRiskCommand(args[1]);
  break;
```

- 인라인 `@header`의 `@exports`(`:9-10`)에 `scan-risk <dir>` 추가 + `@description`에 1층 하드 필터 1문 추가 + 변경이력 주석(`:12`)에 `v1.4 2026-09-02 KST: scan-risk 서브명령 신설 (105)` 행 추가. [MUST] 기록 위치는 인라인이다 — `code-scan target opal/tools/skill-registry/skill-registry.js` → `write_to: inline` / `reason: header_source_inline` (E1 실행 관측).

#### 3.2.3 환경 변경

해당 없음. Node 내장 모듈만 사용한다(`fs`/`path` — 기존 import 재사용, `opal/tools/skill-registry/skill-registry.js:46-48`). 신규 패키지 0.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-2 AC (switch 등재) | 기능 테스트 | `node skill-registry.js scan-risk` 무인자 → usage + exit 1. `scan-risk <존재하는 dir>` → `Unknown command` 미출력 |
| TS-011 | R-2 AC (위험 픽스처 검출 ≥1) | 기능 테스트 | RP-01~RP-04를 코드펜스 안에 담은 `SKILL.md` 픽스처 → `verdict:"RISKY"`, `hits[]`에 `context:"active"` high ≥1건, exit 0 |
| TS-012 | R-2 AC (무해 픽스처 검출 0) | 기능 테스트 | 위험 토큰 없는 정상 픽스처 → `verdict:"SAFE"`, active hit 0건, exit 0 |
| TS-013 | H-3 (오탐 억제) | 기능 테스트 | 금지 산문("`rm -rf`를 절대 쓰지 마라")·주석 라인·`tests/` 하위 파일·산문 언급만 담은 픽스처 4종 → 전건 `verdict:"SAFE"` && 해당 hit의 `context`가 `negated`/`comment`/`fixture`/`prose` 중 하나로 기록 |
| TS-014 | R-2 AC (JSON 형상) | 기능 테스트 | 출력 JSON에 `ok`·`verdict`·`hits` 3키가 존재하고 `hits[]` 각 항목에 `id`·`severity`·`capability`·`file`·`line`·`context` 6키 존재 |
| TS-015 | H-1 (list 계약 회귀) | 회귀 테스트 | `node skill-registry.js list` 출력이 JSON 배열이고, `scan-risk` 도입 전후 동일. `dashboard/backend/tests/test_adapters.py::test_skill_adapter_list` 통과 |
| TS-016 | H-7 (ReDoS) | 보안 테스트 | 100KB 반복 문자열 파일 스캔이 3초 내 종료하고 `RISK_PATTERNS` 전건 nested quantifier 0건 |
| TS-017 | R-2 AC (UNKNOWN 경로) | 기능 테스트 | 존재하지 않는 디렉토리 → `{ok:false, verdict:"UNKNOWN", error:...}` + exit 1 |

---

### F-003: 2층 비교 표 규격 정의

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §2 4단에 「2층 비교 표 규격」 블록 + 5단에 「추천 1개 결정 사다리」 블록 삽입 | TASK.md R-3 / `~/.opal/PRINCIPLES.md` §Core Stance |

#### 3.3.2 설계

**(a) 4축 표기 규격**

| 축 | 표기 방식 | 판정 기준 | 근거 인용 의무 |
|----|----------|----------|--------------|
| 목적 적합 | 3단 판정어 `충족` / `부분` / `미달` | 요청 capability를 스킬이 수행하는가 — `충족`=전량 / `부분`=일부 또는 우회 필요 / `미달`=미수행 | `SKILL.md:줄번호` |
| 출력 형식 호환 | 3단 판정어 `충족` / `부분` / `미달` | 요청한 출력 형식·경로 규약과 스킬의 산출물이 일치하는가 | `SKILL.md:줄번호` |
| 유지 활동 | **실측값** — 최신 커밋 ISO 날짜 | `git -C {tmp} log -1 --format=%cI` | 명령 출력 |
| 부수효과 범위 | **실측값** — `active hit 수 / 최고 severity` (예: `2 / medium`) | `scan-risk` 출력의 `context=="active"` hit 집계 | `scan-risk` JSON |

**(b) [MUST] 점수 금지**

[MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." — 100점 루브릭은 같은 후보의 재채점 값이 달라져 재현 불가이므로 폐기한다. 본문에 **점수·가중치·합산·`/100`·`총점` 표기를 0건으로 유지**한다.

**(c) 판정 근거 인용 지시**

[MUST] 각 3단 판정어 셀에 판정 근거를 `SKILL.md:줄번호` 형식으로 병기하도록 지시하는 문장을 본문에 둔다 (R-3 AC). 형식 규정은 `opal/core/references/harness/citation-rules.md` §2.2 코드 근거를 따른다.

**(d) 추천 1개 결정 사다리 (결정론)**

동률 시 다음 단으로 내려가는 **순서 있는 사다리**다. 합산이 아니다 (H-9).

| 순위 | 조건 | 처리 |
|------|------|------|
| 1 | 보안 판정이 `RISKY`인 후보 | **추천 후보에서 제외** (탈락, 이후 단 진입 없음) |
| 2 | `목적 적합 == 충족`인 후보가 유일 | 그 후보를 추천 |
| 3 | (2에서 복수) `출력 형식 호환 == 충족`인 후보가 유일 | 그 후보를 추천 |
| 4 | (3에서 복수) `부수효과 범위`의 active hit 수가 최소인 후보가 유일 | 그 후보를 추천 |
| 5 | (4에서 복수) 유지 활동 최신 커밋 날짜가 가장 늦은 후보가 유일 | 그 후보를 추천 |
| 6 | 위 전 단에서 동률 | **자동 선택하지 않는다** — 동률 후보 목록을 표시하고 사용자 선택을 요청한다 |

- 1단에서 전 후보가 탈락하면 F-007 위임 경로로 분기한다.
- `목적 적합 == 미달`인 후보는 2단 이전에 탈락시킨다.

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-3 AC (4축 존재) | 산출물 검사 | 비교 표에 목적 적합·출력 형식 호환·유지 활동·부수효과 범위 4축이 전건 존재하고 각 축의 표기 방식(3단 판정어 / 실측값)이 명시된다 |
| TS-021 | R-3 AC (점수 0건) | 산출물 검사 | SKILL.md 전문에 `점수`·`가중치`·`합산`·`총점`·`/100` 표기 hit 0건 |
| TS-022 | R-3 AC (근거 인용 지시) | 산출물 검사 | 판정 근거를 `SKILL.md:줄번호` 형식으로 인용하도록 지시하는 문장이 1건 이상 존재 |
| TS-023 | H-9 (재현성) | 산출물 검사 | 추천 결정 규칙이 순서 있는 사다리(≥5단)로 기술되고 동률 시 사용자 선택 요청으로 종료되며, 「종합 판단」류 주관 표현 0건 |

---

### F-004: 보안 4단 판정 도입

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §2 4단에 보안 4단 판정 표(판정 조건 + 판정별 동작) 삽입 + §6 1번 경로에 판정 참조 1문 배선 | `opal/skills/opal-skill-manager/SKILL.md:183-207` (현행 라이선스 1축) |

#### 3.4.2 설계

**(a) 1층 결과 ↔ 4단 판정 매핑 (필수 포함 #6)**

우선순위는 `RISKY` > `UNKNOWN` > `CAUTION` > `SAFE`이며 **가장 높은 단이 최종 판정**이다.

| 판정 | 1층 조건 (`scan-risk` 출력) | 라이선스 조건 | 판정 시 동작 |
|------|---------------------------|-------------|------------|
| **SAFE** | `ok:true` && `verdict == "SAFE"` (active hit 0건) | `license != "Unknown"` | **설치 진행** — 추가 게이트 없음. 6단 승인 1회만 |
| **CAUTION** | `ok:true` && `verdict == "CAUTION"` (active medium ≥1, active high 0) | `license != "Unknown"` | **확인 게이트** — 검출 목록(`id`·`capability`·`file:line`)을 표시하고 설치 여부를 묻는다 (y/N, 디폴트 `N`) |
| **RISKY** | `ok:true` && `verdict == "RISKY"` (active high ≥1) | 무관 | **추천 후보에서 제외** — 추천 사다리 1단에서 탈락시키고 설치를 제안하지 않는다. 사용자가 명시적으로 강행을 요구하면 검출 목록 + high 항목을 재표시한 뒤에만 진행한다 |
| **UNKNOWN** | `ok:false` (디렉토리·SKILL.md 부재, 전 파일 skip) **또는** `verdict != "RISKY"`이면서 라이선스 미확인 | `license == "Unknown"` 또는 스캔 불가 | **추가 조사** — 후보로 유지하되 **추천 1순위로 올리지 않는다**. 현행 Unknown 라이선스 게이트 문안(`opal/skills/opal-skill-manager/SKILL.md:193-202`)을 그대로 적용하고, 스캔 불가 사유를 함께 표시한다 |

**(b) [MUST] RISKY 제외 규칙**

[MUST] 보안 판정이 `RISKY`인 후보는 추천 후보에서 제외한다 (R-4 AC). §3.3.2 (d) 사다리 1단과 동일 규칙이며 SSOT는 이 표다 — 사다리 쪽은 이 표를 참조한다.

**(c) §6 최소 연동 (승인 게이트 수준 불변)**

TASK.md §확정된 설계 방향: 「`//` 커맨드 자동 설치 정책(§6)의 승인 게이트 수준 자체는 이번 범위에서 변경하지 않는다」. 따라서 §6에는 아래만 추가한다:

- §6 1번 경로(`license != "Unknown"` + `source_repo` 있음 → 자동 설치)의 **clone 직후·복사 직전**에 `scan-risk`를 1회 실행하고, `verdict == "RISKY"`이면 자동 설치를 중단하고 검출 목록을 표시한다는 1문.
- §6 2번(Unknown) 경로의 게이트 문안·디폴트 `N`·3번(미등재)·4번(ambiguous) 분기는 **문안 그대로 유지**한다.
- 비차단 통지 1줄(`opal/skills/opal-skill-manager/SKILL.md:187-189`)에 `· trust {verdict}` 토큰 1개를 덧붙인다.

근거: 라이선스 확인 스킬의 「동의 대기 없이 자동 설치」 결정은 소유자 확정 사항이다(`opal/skills/opal-skill-manager/SKILL.md:181`, 064). RISKY 차단은 승인 게이트 **수준**을 올리는 것이 아니라 **자동 경로의 진입 조건**을 좁히는 것이므로 확정 방향과 충돌하지 않는다.

#### 3.4.3 환경 변경

해당 없음.

#### 3.4.4 배치/마이그레이션

해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-4 AC (4단 존재) | 산출물 검사 | SAFE·CAUTION·RISKY·UNKNOWN 4단이 표에 전건 존재하고 각 단에 「1층 조건」·「라이선스 조건」·「판정 시 동작」 3셀이 빈칸 없이 채워진다 |
| TS-031 | R-4 AC (RISKY 제외) | 산출물 검사 | 「RISKY 판정 시 추천 후보에서 제외한다」 규칙이 명시적으로 존재 |
| TS-032 | R-4 AC + H-3 | 산출물 검사 | 4단 판정 조건이 `scan-risk` 출력의 `verdict`·`context=="active"`를 참조하며, 판정 조건에 주관 표현 0건 |
| TS-033 | §6 불변 | 회귀 테스트 | §6의 2·3·4번 분기 문안과 Unknown 게이트 디폴트 `N`이 개정 전과 동일 |

---

### F-005: user-registry 필드 additive 추가

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §2 「user-registry.json 기록 규칙」(104-108)의 스키마 줄에 3필드 추가 + 형상 제약 1문 추가 | `opal/tools/skill-registry/skill-registry.js:435-462` (미지 필드 무시) |

#### 3.5.2 설계

**(a) 필드 정의**

기존 7필드(`name`·`alias`·`description`·`triggers`·`source_repo`·`commit_sha`·`license`)를 **전량 유지**하고 아래 3필드를 추가한다:

| 필드 | 타입 | 값 | 출처 |
|------|------|----|------|
| `trust` | string | `"SAFE"` \| `"CAUTION"` \| `"RISKY"` \| `"UNKNOWN"` | §3.4.2 (a) 4단 판정 최종값 |
| `capabilities` | string[] | active hit의 `capability` 라벨 중복 제거 목록 (예: `["network:outbound","secret:env"]`). active hit 0건이면 `[]` | `scan-risk` 출력 `hits[].capability` (§3.2.2 (e)) |
| `scanned_at` | string | ISO 8601 UTC (예: `"2026-09-02T04:11:00Z"`) | 4단 판정 확정 시각 |

**(b) [MUST] 형상 제약**

[MUST] 기록은 `groups[vendor][] = [{ ... 10필드 }]` 형상을 유지한다 — `flattenGroups()`가 `registry.groups`의 배열/중첩 객체만 순회하므로 flat 배열 등 다른 형상은 조용히 무시되고 설치 이력이 유실된다(`opal/tools/skill-registry/skill-registry.js:58-74`, H-5).

[MUST] `docs/CONVENTIONS.md` §배포 경계: "커뮤니티 스킬 레지스트리 이원 경계: … 사용자 설치 등록분은 `~/.opal/community-skills/user-registry.json`(install 불가침 — 142 D-4)에 기록한다. 사용자 등록분을 references 쪽에 기록하지 않는다 (Task 064)." — 3필드는 **user-registry에만** 기록한다. 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`)는 무수정 유지 규칙을 그대로 둔다(`opal/skills/opal-skill-manager/SKILL.md:102`).

[MUST] `docs/CONVENTIONS.md` §배포 경계: "런타임 사용자 데이터 쓰기는 이 금지의 대상이 아니다 — skill-manager가 스킬 설치/제거 시 `~/.opal/community-skills/`(스킬 본체·`user-registry.json`)를 갱신하는 것은 사용자 요청 기반 런타임 데이터 조작이며, 프레임워크 파일 직접 편집과 구분된다." — user-registry 쓰기는 배포 경계 위반이 아니다.

**(c) 하위호환**

- 기존 항목(3필드 없음)은 그대로 유지한다. 마이그레이션·백필을 수행하지 않는다 — `~/.opal/community-skills/user-registry.json`은 현재 미존재이므로 백필 대상이 0건이다(E1 실측).
- §4 삭제 절차·§5 업데이트 확인 절차는 무변경이다 (필드 추가는 읽기 측에 영향 없음).

#### 3.5.3 환경 변경

해당 없음.

#### 3.5.4 배치/마이그레이션

해당 없음 (백필 0건).

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R-5 AC (3필드 명시) | 산출물 검사 | 기록 규칙에 `trust`·`capabilities`·`scanned_at` 3필드가 타입·값 범위와 함께 명시된다 |
| TS-041 | R-5 AC (기존 7필드 유지) | 산출물 검사 | 기존 7필드가 스키마 서술에 전건 잔존 |
| TS-042 | R-5 AC + H-5 | 기능 테스트 | 10필드 항목을 담은 합성 `user-registry.json` 픽스처로 `node skill-registry.js validate` → errors 0건, exit 0 |
| TS-043 | H-5 (형상) | 기능 테스트 | 동일 픽스처에서 `list --group=community`가 해당 항목을 반환 (병합 로드 정상) |

---

### F-006: Match 등급화

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §1 1단계(33-43)를 3등급 표로 재작성 | `opal/tools/skill-registry/skill-registry.js:259-317` (match 반환 필드) |

#### 3.6.2 설계

**(a) 3등급 판정 기준 + 동작**

판정 입력은 `match` 출력의 기존 필드뿐이다(`matched_by` 부재 — H-6). 판정은 **문자열 동일성 비교**로만 기술한다.

| 등급 | 판정 기준 (`match` 출력) | 후속 동작 |
|------|------------------------|----------|
| **Exact Match** | `found:true` && `installed:true` && (`name`이 검색어와 문자열 동일 \|\| `alias`가 검색어에서 추출한 alias와 문자열 동일) | 설치된 스킬 정보를 안내하고 **종료**. [MUST] 외부 검색(2단계 `npx skills find`)을 수행하지 않는다 |
| **Partial Match** | `found:true` && `installed:true` && Exact 조건 불성립 (= triggers 정규식 유래 매칭), **또는** `ambiguous:true` | 매칭된 스킬을 안내하고 "찾으시는 것이 맞습니까? 아니면 외부 검색을 진행할까요?"를 묻는다. `ambiguous:true`이면 `candidates` 목록(vendor별 `name`·`source_repo`·`license`·`installed`)을 표시하고 정식명(`vendor/skill`)으로 재호출을 유도한다 — 자동 선택하지 않는다 |
| **No Match** | `found:false`, **또는** `found:true && installed:false` | 6단 흐름 1단(skills.sh 검색)으로 진행한다. `installed:false`이면 해당 후보를 1단 결과의 우선 후보로 넘긴다(`source_repo` 기지) |

**(b) [MUST] Reuse Before Install**

[MUST] Exact Match 시 외부 검색을 수행하지 않는다 (R-6 AC). 현행은 "추가로 다른 스킬도 검색할까요?"로 외부 검색을 유도했다(`opal/skills/opal-skill-manager/SKILL.md:39-41`) — 이 문안을 Exact 등급에서 제거한다. 사용자가 **명시적으로** 다른 스킬 검색을 요청하면 그때 1단으로 진입한다(사용자 요청은 등급 판정과 별개 경로).

**(c) `matched_by` 미도입 결정**

`match` 출력에 `matched_by` 필드를 추가하면 Exact/Partial 경계가 도구 판정이 되어 더 견고하다. 그러나 R-6의 「어디에」는 SKILL.md §1 1단계 단일이며, [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."에 따라 **이번 범위에서 도입하지 않는다**. 후속 백로그 후보로 §9에 기재한다.

#### 3.6.3 환경 변경

해당 없음.

#### 3.6.4 배치/마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R-6 AC (3등급 존재) | 산출물 검사 | Exact / Partial / No Match 3등급이 표에 존재하고 각 등급에 판정 기준·후속 동작이 채워진다 |
| TS-051 | R-6 AC (Exact 외부검색 금지) | 산출물 검사 | 「Exact Match 시 외부 검색을 수행하지 않는다」 규칙이 `[MUST]` 토큰과 함께 존재 |
| TS-052 | H-6 (결정론) | 산출물 검사 | 판정 기준이 `match` 출력 필드명(`found`·`installed`·`ambiguous`·`name`·`alias`)과 문자열 동일성 비교로만 기술되고 주관 표현 0건 |

---

### F-007: `opal-skill-creator` 위임 계약

#### 3.7.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §1 말미에 「적합 스킬 미발견 시 위임」 블록 추가 (위임 대상 + 페이로드 필드 목록 + 분기 조건) | `opal/skills/opal-skill-creator/SKILL.md:63-77` (Capture Intent / Interview 입력) |

#### 3.7.2 설계

**(a) 분기 조건 (위임 진입)**

아래 중 하나에서 위임한다:
- 1단(skills.sh 검색) 결과 0건
- 2층 판정 후 잔존 후보 0건 (전 후보 `RISKY` 탈락 또는 `목적 적합 == 미달`)
- 사용자가 추천 후보를 전건 거부

**(b) 위임 대상**

[MUST] 위임 대상은 `opal-skill-creator`다 (R-7 AC). `skill-builder`라는 컴포넌트는 OPAL에 존재하지 않는다 — `opal/skills/opal-skill-creator/SKILL.md:1-7`이 실 대응 컴포넌트다.

**(c) 페이로드 필드 목록 (계약)**

| 필드 | 타입 | 내용 | creator 측 소비 지점 |
|------|------|------|---------------------|
| `requested_capability` | string | 사용자가 요구한 기능을 1~2문으로 정규화한 서술 | Capture Intent — 스킬 목적 (`opal/skills/opal-skill-creator/SKILL.md:63`) |
| `requested_triggers` | string[] | 사용자 발화에서 추출한 트리거 표현 목록 | Capture Intent — 트리거 (동 `:63`) |
| `requested_output_format` | string | 기대 산출물 형식·경로 규약 | Capture Intent — 출력 형식 (동 `:63`) |
| `searched_sources` | string[] | 탐색한 소스 목록 (예: `["skills.sh (npx skills find \"{query}\")"]`) + 검색어 원문 | 재탐색 방지 (중복 탐색 억제) |
| `candidates_evaluated` | object[] | 후보별 `{name, source_repo, license, trust, shortfall}` — `shortfall`은 2층 비교 표의 `미달`/`부분` 축과 그 근거 인용(`SKILL.md:줄번호`) | Interview and Research — 에지 케이스·의존성 (동 `:64`) |
| `security_findings` | object[] | 후보별 `scan-risk` active hit 요약 `{name, verdict, capabilities[]}` | 신규 스킬이 회피해야 할 위험 행위 입력 |
| `skill_type_hint` | string | `"프레임워크 스킬"` \| `"OPAL 전용 스킬"` 중 추정값 (미정이면 `"미정"`) | 스킬 유형 판단 기준 (동 `:38-47`) |

[MUST] `searched_sources`와 `candidates_evaluated[].shortfall`을 페이로드에 포함한다 (R-7 AC — 탐색한 소스와 미달 사유). 목적은 위임 후 요구사항 재입력을 0으로 만드는 것이다.

**(d) 위임 방식**

`opal-skill-creator`의 SKILL.md를 Read하고 위 페이로드를 컨텍스트로 전달하여 Phase 1 신규 생성 모드로 진입한다. skill-manager는 skill-creator를 수정하지 않는다(동 `:50`).

#### 3.7.3 환경 변경

해당 없음.

#### 3.7.4 배치/마이그레이션

해당 없음.

#### 3.7.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | R-7 AC (필드 목록) | 산출물 검사 | 페이로드 필드 목록이 표로 존재하고 각 필드에 타입·내용이 명시된다 |
| TS-061 | R-7 AC (대상 명시) | 산출물 검사 | 위임 대상이 `opal-skill-creator`로 명시되고 `skill-builder` 표기 0건 |
| TS-062 | R-7 AC (소스·미달 사유) | 산출물 검사 | `searched_sources`와 후보별 미달 사유(`shortfall`)가 페이로드 필드에 전건 포함 |

---

### F-008: 변경이력 + 절 번호 앵커 무결 검증

#### 3.8.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §변경이력 표에 `v1.5` 행 1건 추가 | `docs/CONVENTIONS.md` §변경이력 작성 의무 |
| 2 | `docs/ARCHITECTURE.md` | 문서 | §커뮤니티 스킬(189-197) 정책 서술에 보안 4단 판정 축 반영 + `skill-registry.js` 서브명령 `scan-risk` 반영 | `docs/ARCHITECTURE.md:189` (stale이 되는 서술) |

#### 3.8.2 설계

**(a) [MUST] 변경이력 행 포맷**

[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"

추가 행:

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.5 | `YYYY-MM-DD HH:mm KST` (실행 시점 — `~/.opal/tools/date`로 취득) | §1·§2를 6단 흐름(skills.sh 검색 → 후보 최대 3 선별 → shallow clone → 2층 판정 → 추천 1개 → 승인 → 복사·등록)으로 재작성 + 보안 4단 판정(SAFE/CAUTION/RISKY/UNKNOWN) 신설 + 1층 하드 필터 `scan-risk` 서브명령 도구화 + 2층 비교 표 4축(점수 폐기) + Match 3등급화 + user-registry `trust`/`capabilities`/`scanned_at` additive 추가 + `opal-skill-creator` 위임 계약 (105) |

- 버전은 현행 최신 `v1.4.1`(`opal/skills/opal-skill-manager/SKILL.md:217`) 다음의 minor 증가 → `v1.5`. 절차 재작성 규모이므로 patch가 아니다.
- 일시는 추측하지 않고 `~/.opal/tools/date`로 실측 취득한다.

**(b) [MUST] 절 번호 앵커 축자 무결 검증**

[MUST] 개정 완료 후 아래 검증을 수행하고 결과를 EXECUTE 보고에 기재한다. SSOT 선행 개정 원칙(`.opal/brain/pages/concept/skill-quoting-ssot-must-edit-ssot-first.md`)에 따라 `grep -F` 축자 일치로 확인한다:

```bash
# 1) 외부 앵커가 지목하는 절이 잔존하는가
grep -Fn 'opal-skill-manager/SKILL.md §6' opal/core/references/harness/skill-commands.md   # hit ≥ 1 기대
grep -Fn 'opal-skill-manager/SKILL.md §2' opal/core/references/harness/skill-commands.md   # hit ≥ 1 기대
grep -n '^### 2\. ' opal/skills/opal-skill-manager/SKILL.md   # 「설치」 포함 헤딩 1건 기대
grep -n '^### 6\. ' opal/skills/opal-skill-manager/SKILL.md   # hit 1건 기대
grep -cE '^### [1-6]\. ' opal/skills/opal-skill-manager/SKILL.md   # 6 기대

# 2) 도구가 생성하는 절 이름 참조가 유효한가
grep -Fn '§설치' opal/tools/skill-registry/skill-registry.js   # :286 — SKILL.md에 「설치」 절 존재 확인
```

- 절 번호가 불가피하게 이동한 경우에만 `opal/core/references/harness/skill-commands.md:24,36`을 동반 개정하고, 개정 시 §변경이력 행을 그 문서에도 추가한다. **번호 보존 설계(§3.1.2 (a))가 성공하면 이 동반 개정은 발생하지 않는다.**
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다." — 검증·개정 대상은 소스 `opal/core/references/harness/skill-commands.md`이며 배포본 `~/.opal/references/harness/skill-commands.md`를 편집하지 않는다.

**(c) docs/ARCHITECTURE.md 갱신 범위**

- `:189` "라이선스가 확인된 스킬은 자동 설치, Unknown 라이선스만 확인 게이트를 거친다." → 보안 4단 판정 축(본문 위험 패턴 스캔 + 라이선스 2축)을 반영한 서술로 교체.
- `:196` 레지스트리(이원) 행 말미에 사용자 등록분의 판정 필드(`trust`·`capabilities`·`scanned_at`) 1구 추가.
- `:81` tools/ 표 `skill-registry/` 항목에 `scan-risk`(1층 하드 필터) 1구 추가.
- `docs/ARCHITECTURE.md` §변경이력에 행 1건 추가.

#### 3.8.3 환경 변경

해당 없음.

#### 3.8.4 배치/마이그레이션

해당 없음. `./scripts/install-mac.sh` 재배포는 소유자 판단 사항이며 이 태스크의 Step에 포함하지 않는다.

#### 3.8.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-070 | R-8 AC | 산출물 검사 | 변경이력 표에 버전(semver)·일시(`YYYY-MM-DD HH:mm KST`)·변경내용(태스크 번호 `(105)` 포함) 행 1건이 추가된다 |
| TS-071 | H-2 | 산출물 검사 | §3.8.2 (b) 6개 grep 전건 기대값 충족 |
| TS-072 | H-8 | 산출물 검사 | 개정된 SKILL.md에 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`) 쓰기 지시 0건 && `:102`의 `[MUST] ... 수정하지 않는다` 금지 문장 잔존 |
| TS-073 | F-008 (c) | 산출물 검사 | `docs/ARCHITECTURE.md:189` 서술이 보안 4단 축을 반영하고 §변경이력 행 1건 추가 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-002 (RED) | 1 | opal-test-agent (mode: red) | 순차 | RED-first 강제 구간. 실패 증거(exit≠0) 기록 후 Phase 2 진입 |
| 2 | F-002 (GREEN) | 2 | opal-task-agent | 순차 | Step 1 RED 증거 확보 후. `skill-registry.js` 단일 파일 |
| 3 | F-001·F-003·F-004·F-005·F-006·F-007·F-008(a) | 3, 4, 5, 6, 7, 8 | opal-task-agent | **단일 디스패치 내 순차** | **[MUST] 6개 Step 전부 동일 파일(`SKILL.md`)이므로 분할 금지 — 후행 저장이 선행 편집을 덮어쓰는 충돌 방지** |
| 4 | F-008(b) | 9 | opal-task-agent | 순차 | 앵커 축자 검증 + `list` 계약 회귀 확인 |
| 5 | F-008(c) | 10 | PM 직접 | 순차 | `docs/ARCHITECTURE.md` 갱신 |

> **산출량 상한 판정**: Phase 3의 산출 파일은 `SKILL.md` **1개**다 — 6 Step이지만 단일 파일이므로 3파일 상한에 저촉되지 않으며 분할 대상이 아니다. Phase 1·2는 각 1파일, Phase 5는 1파일.

### 4.2 실행 체크리스트

> 총 10개 Step | Phase 5개 | 실행 모드: **복잡**

#### Step 1: `scan-risk` RED 테스트 작성

- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-test-agent (mode: red)
- **파일**: `opal/tools/skill-registry/tests/test-scan-risk.js` (신규)
- **작업 내용**: TS-010~TS-014·TS-016·TS-017 대응 RED 테스트를 작성한다. 기존 패턴 준수 — `node:test`+`node:assert/strict`+`spawnSync` CLI 블랙박스, `fs.mkdtempSync`로 합성 픽스처, mock 0, 인라인 `@header` + TC↔시나리오 매핑 주석 + 변경이력 주석, `after()` 정리 (`opal/tools/skill-registry/tests/test-validate.js:23-30`, `test-migrate.js:35-45`). 픽스처는 최소 7종 — ① RP-01~04 코드펜스(위험) ② 무해 ③ 금지 산문 ④ 주석 라인 ⑤ `tests/` 하위 ⑥ 산문 언급만 ⑦ 100KB 반복 문자열. §3.2.2 (b) 반환 형상 계약을 assert 기준으로 고정한다
- **완료 기준**: `node --test opal/tools/skill-registry/tests/test-scan-risk.js` 실행 시 **exit code ≠ 0**이고, 현행 CLI가 `Unknown command: scan-risk`를 반환한다는 사실이 RED 증거로 기록된다 (`opal/tools/skill-registry/skill-registry.js:715-717`)
- **테스트**: TS-010, TS-011, TS-012, TS-013, TS-014, TS-016, TS-017
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `scan-risk` 서브명령 구현 (GREEN)

- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: §3.2.2에 따라 `RISK_PATTERNS` 상수(RP-01~RP-10) + 오탐 억제 상수(확장자 화이트리스트·제외 디렉토리·부정 토큰·픽스처 경로) + `scanRiskCommand(dir)` 신설. `main()`에 `case 'scan-risk'` + usage 1줄 추가. 인라인 `@header`의 `@exports`·`@description`·변경이력 주석 갱신. **[MUST] `listCommand()`·`case 'list'`·기타 기존 서브명령 본문·종료 코드 규약(`:720-723`) 무수정** — [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- **완료 기준**: Step 1 테스트 전건 통과(exit 0) && `node skill-registry.js list` 출력이 Step 2 전과 동일한 JSON 배열 && `RISK_PATTERNS` 전건 nested quantifier 0건 && @header 기록 위치가 인라인(`code-scan target` → `write_to: inline`)
- **테스트**: TS-010~TS-017
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: SKILL.md §1 1단계 Match 등급화

- [ ] 완료
- **소속 기능**: F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §1 1단계(33-43)를 §3.6.2 (a) 3등급 표로 재작성하고 (b) Reuse Before Install `[MUST]` 규칙을 추가한다. `### 1.` 헤딩 번호·이름 보존
- **완료 기준**: TS-050·TS-051·TS-052 충족
- **테스트**: TS-050, TS-051, TS-052
- **실행 방법**: direct (Phase 3 단일 디스패치 내 1번째 편집)
- **의존**: Step 2

#### Step 4: SKILL.md §1·§2 6단 흐름 재작성

- [ ] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §3.1.2 (a)~(f)에 따라 §1 2단계·§2 전체를 6단 흐름으로 재작성한다. 절 번호·절 이름 보존, 신규 규격은 `####`/굵은 라벨 블록으로 삽입. 복사 원본 4단 폴백 탐지(`:85-94`)와 빈 디렉토리 복사 금지 규칙 승계. clone=임시 / 복사=설치 2문 명시. 후보 상한 3 + 결정론 선별 기준 + 임시 디렉토리 정리 규율 기재
- **완료 기준**: TS-001·TS-002·TS-003 충족 && 4단 폴백 탐지 문안 잔존
- **테스트**: TS-001, TS-002, TS-003
- **실행 방법**: direct (Phase 3 단일 디스패치 내 2번째 편집)
- **의존**: Step 3

#### Step 5: SKILL.md 보안 4단 판정 표 + §6 최소 연동

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §3.4.2 (a) 1층↔4단 매핑 표를 §2 4단에 삽입하고 (b) RISKY 제외 `[MUST]` 규칙을 명시한다. (c)에 따라 §6 1번 경로에 `scan-risk` 실행 + RISKY 자동 설치 중단 1문과 통지 라인 `· trust {verdict}` 토큰만 추가하고 §6 2·3·4번 분기 문안은 무수정 유지
- **완료 기준**: TS-030·TS-031·TS-032·TS-033 충족
- **테스트**: TS-030, TS-031, TS-032, TS-033
- **실행 방법**: direct (Phase 3 단일 디스패치 내 3번째 편집)
- **의존**: Step 4

#### Step 6: SKILL.md 2층 비교 표 규격 + 추천 사다리

- [ ] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §3.3.2 (a) 4축 표기 규격 표 + (c) 근거 인용 지시문 + (d) 추천 1개 결정 사다리 6단을 §2 4·5단에 삽입한다. 점수·가중치·합산 표기 0건 유지
- **완료 기준**: TS-020·TS-021·TS-022·TS-023 충족
- **테스트**: TS-020, TS-021, TS-022, TS-023
- **실행 방법**: direct (Phase 3 단일 디스패치 내 4번째 편집)
- **의존**: Step 5

#### Step 7: SKILL.md user-registry 필드 additive 추가

- [ ] 완료
- **소속 기능**: F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §2 「user-registry.json 기록 규칙」(104-108) 스키마 줄을 10필드로 갱신하고 §3.5.2 (a) 필드 정의 표 + (b) 형상 제약 `[MUST]` 2문을 추가한다. 카탈로그 무수정 `[MUST]`(`:102`) 잔존 확인
- **완료 기준**: TS-040·TS-041 충족 && `:102` 금지 문장 잔존
- **테스트**: TS-040, TS-041, TS-042, TS-043
- **실행 방법**: direct (Phase 3 단일 디스패치 내 5번째 편집)
- **의존**: Step 6

#### Step 8: SKILL.md `opal-skill-creator` 위임 계약 + 변경이력 행

- [ ] 완료
- **소속 기능**: F-007, F-008
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §3.7.2 (a)~(d) 위임 블록(분기 조건·대상·페이로드 7필드 표·위임 방식)을 §1 말미에 추가한다. 이어서 §3.8.2 (a) `v1.5` 변경이력 행을 추가한다 — 일시는 `~/.opal/tools/date`로 실측 취득하고 추측하지 않는다. **변경이력 행은 SKILL.md 편집의 마지막 작업이다**
- **완료 기준**: TS-060·TS-061·TS-062·TS-070 충족
- **테스트**: TS-060, TS-061, TS-062, TS-070
- **실행 방법**: direct (Phase 3 단일 디스패치 내 6번째 편집)
- **의존**: Step 7

#### Step 9: 절 번호 앵커 축자 검증 + `list` 계약 회귀

- [ ] 완료
- **소속 기능**: F-008, F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: (읽기·검증만) `opal/skills/opal-skill-manager/SKILL.md`, `opal/core/references/harness/skill-commands.md`, `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: §3.8.2 (b) grep 6건을 실행하고 결과를 보고한다. `node --test opal/tools/skill-registry/tests/` 전건 실행. `node skill-registry.js list`가 JSON 배열임을 확인하고 가능하면 `dashboard/backend/tests/test_adapters.py::test_skill_adapter_list`를 실행한다. 절 번호가 이동했다면 `opal/core/references/harness/skill-commands.md:24,36`을 동반 개정하고 해당 문서 §변경이력에 행을 추가한다
- **완료 기준**: TS-071·TS-015·TS-021·TS-072 충족. grep 6건 전건 기대값 일치 && `tests/` 4파일 전건 통과 && `list` 출력이 JSON 배열
- **테스트**: TS-015, TS-021, TS-071, TS-072
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: `docs/ARCHITECTURE.md` 갱신

- [ ] 완료
- **소속 기능**: F-008
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §3.8.2 (c)에 따라 `:189` 정책 서술(보안 4단 축 반영) · `:196` 레지스트리 행(판정 3필드) · `:81` tools/ 표 `skill-registry/` 항목(`scan-risk`) 3곳을 갱신하고 §변경이력에 행 1건을 추가한다
- **완료 기준**: TS-073 충족
- **테스트**: TS-073
- **실행 방법**: direct
- **의존**: Step 9

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED-first 강제 — RED 실패 증거 없이 GREEN 진입 금지 ([MUST] `opal/core/references/harness/red-first.md` §1) |
| Step 2 → Step 3 | SKILL.md가 `scan-risk` 서브명령명·출력 형상(`verdict`·`hits[].context`)을 축자 인용해야 하므로 구현 확정 후 문서화 |
| Step 3 → 4 → 5 → 6 → 7 → 8 | **동일 파일(`SKILL.md`) 순차 수정** — 6 Step이 같은 파일을 편집하므로 단일 디스패치 내 순차 편집으로 묶는다. 병렬·분할 시 후행 저장이 선행 편집을 덮어쓴다 |
| Step 8 → Step 9 | 검증은 전 편집 완료 후 1회 |
| Step 9 → Step 10 | 앵커 검증 결과에 따라 `skill-commands.md` 동반 개정이 발생할 수 있고, ARCHITECTURE 서술이 확정 문안을 인용해야 함 |
| Step 1 ∥ Step 3~8 (불가) | Step 3~8이 Step 2에 의존하고 Step 2가 Step 1에 의존 — 전 구간 순차 사슬 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 6단 흐름이 입출력과 함께 §1·§2에 존재하고 절 번호가 보존되었는가 | TS-001, TS-002, TS-003 | 6단 전건 존재 + 각 단 입력·출력 1줄 이상 + `### 1.`~`### 6.` 6개 잔존 |
| F-002 | `scan-risk`가 switch에 등재되고 위험/무해 픽스처를 정확히 분류하는가 | TS-010~TS-017 | 위험 픽스처 active high ≥1 && 무해·오탐 픽스처 6종 전건 active hit 0 && `list` 출력 불변 |
| F-003 | 4축 비교 표가 존재하고 점수 표기가 0건이며 추천이 결정론적인가 | TS-020~TS-023 | 4축 전건 + 점수/가중치/합산 hit 0 + 사다리 ≥5단 |
| F-004 | 4단 판정 조건·동작이 표로 채워지고 RISKY 제외 규칙이 명시되었는가 | TS-030~TS-033 | 4단 × 3셀 빈칸 0 + RISKY 제외 `[MUST]` 존재 + §6 2·3·4번 문안 불변 |
| F-005 | 3필드가 기록 규칙에 명시되고 기존 7필드가 유지되며 validate가 통과하는가 | TS-040~TS-043 | 10필드 명시 + `validate` errors 0 + `list --group=community` 반환 |
| F-006 | 3등급 판정 기준·동작이 기계적 조건으로 기술되고 Exact 시 외부검색 금지가 명시되었는가 | TS-050~TS-052 | 3등급 전건 + `[MUST]` 금지 규칙 + 주관 표현 0 |
| F-007 | 위임 대상·페이로드 필드·탐색 소스·미달 사유가 계약으로 존재하는가 | TS-060~TS-062 | 필드 7종 표 + `opal-skill-creator` 명시 + `skill-builder` 표기 0 |
| F-008 | 변경이력 행이 규격대로 추가되고 외부 앵커가 무손상인가 | TS-070~TS-073 | semver+KST일시+`(105)` 행 1건 + grep 6건 기대값 일치 + ARCHITECTURE 갱신 |

### 5.2 회귀 테스트

- [ ] `node skill-registry.js list` (무인자) 출력이 개정 전과 동일한 JSON 배열이다 — OPAL Console 소비 계약 (H-1)
- [ ] `dashboard/backend/tests/test_adapters.py::test_skill_adapter_list` 통과
- [ ] `node --test opal/tools/skill-registry/tests/` 전건(`test-match`·`test-migrate`·`test-validate`·`test-scan-risk`) 통과
- [ ] `node skill-registry.js match "pdf"`·`get`·`validate`·`migrate --dry-run`·`parse-source-repo` 5종 출력 형상 불변
- [ ] SKILL.md §3·§4·§5·§관리 진입 훅·§설치 경로 규칙·§참고 절이 무수정으로 잔존
- [ ] §6의 2번(Unknown 게이트, 디폴트 `N`)·3번(미등재)·4번(ambiguous) 분기 문안 불변

### 5.3 코드/문서 품질

- [ ] [MUST] `docs/CONVENTIONS.md` §@header 규칙 — `skill-registry.js` @header 기록 위치가 `code-scan target` 판정(`write_to: inline`)과 일치하며 `@exports`에 `scan-risk`가 반영되었다
- [ ] [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 — SKILL.md·ARCHITECTURE.md 양쪽에 변경이력 행이 추가되었고 일시가 `~/.opal/tools/date` 실측값이다
- [ ] [MUST] `docs/CONVENTIONS.md` §배포 경계 — `~/.opal/` 하위 프레임워크 파일 편집 0건 (변경은 `opal/`·`docs/`에서만)
- [ ] [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리 — SKILL.md 본문에 플랫폼 조건문 추가 0건
- [ ] [MUST] `docs/CONVENTIONS.md` §도구 우선 원칙 — 위험 패턴 판정을 산문 지시가 아니라 `scan-risk` 도구가 수행한다
- [ ] [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes — `skill-registry.js` 기존 함수 리팩터링 0건
- [ ] [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First — 신규 패키지 0, 위험 패턴 10종 이내, 추측성 확장 0
- [ ] `git commit`·`git push`·`git reset`·`git rebase` 실행 0건 — 변경은 워킹트리에 남긴다
- [ ] SKILL.md 500줄 이하 유지 (`opal/skills/opal-skill-creator/SKILL.md:76` 문서 표준)

### 5.4 보안

- [ ] `scan-risk`는 **읽기 전용**이다 — 인자 디렉토리 외부를 읽지 않고 아무 파일도 쓰지 않는다
- [ ] `RISK_PATTERNS` 전건이 nested quantifier를 포함하지 않는다 (ReDoS, H-7 / `opal/tools/skill-registry/skill-registry.js:145-166` 기준)
- [ ] 대용량·병리 입력(100KB 반복 문자열, 2000자 초과 라인, 바이너리)에서 스캔이 타임박스 내 종료한다
- [ ] `hits[].excerpt`가 200자로 truncate되어 credential 원문을 장문 노출하지 않는다
- [ ] 위험 패턴 스캔 결과가 사람 검토를 대체하지 않는다는 한계 문장이 SKILL.md에 존재한다 (H-4)
- [ ] 임시 clone 디렉토리 삭제 시 경로가 임시 디렉토리 하위임을 검증한 뒤 `rm -rf`를 수행하도록 기재되었다
- [ ] 코드에 하드코딩된 토큰/시크릿이 없다

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 10개 | 복잡 |
| 변경 파일 수 | 4개 (신규 1 + 수정 3) | 복잡 |
| 모듈 범위 | 다중 (스킬 문서 + Node 도구 + 도구 테스트 + 설계 문서) | 복잡 |
| 작업 유형 | 대규모 개선 (절차 재작성 + 신규 서브명령) | 복잡 |
| 외부 의존성 | 없음 (신규 패키지 0, Node 내장 모듈만) | 단순 |
| **실행 모드** | **복잡** | 5기준 중 4건 복잡 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1: [opal-test-agent (mode: red)]        Step 1        → test-scan-risk.js (RED 증거)
              │
Batch 2: [opal-task-agent #A]                 Step 2        → skill-registry.js
              │
Batch 3: [opal-task-agent #B]                 Step 3~8      → SKILL.md (단일 파일 6회 순차 편집)
              │
Batch 4: [opal-task-agent #C]                 Step 9        → 검증 전용 (쓰기 0, 조건부 skill-commands.md)
              │
Batch 5: [PM 직접]                            Step 10       → docs/ARCHITECTURE.md
```

**그룹핑 근거**:
1. **파일 충돌 방지 최우선** — Step 3~8은 `SKILL.md` 단일 파일이므로 반드시 같은 에이전트(#B)에 배치한다. 분할하면 후행 저장이 선행 편집을 덮어쓴다.
2. **작성자≠구현자** — Step 1(RED 테스트)과 Step 2(구현)를 다른 에이전트로 분리한다 ([MUST] `opal/core/references/harness/red-first.md` §2).
3. **검증자 분리** — Step 9는 Step 2·3~8을 수행하지 않은 별 에이전트(#C)에 배치하여 self-confirming을 억제한다.
4. **병렬 불가** — 전 Batch가 선행 산출물을 입력으로 요구하는 단일 사슬이다. 병렬 이득 0.

### C-2. 스킬 요구사항

| 요구 | 매칭 | 갭 |
|------|------|----|
| RED 테스트 작성 | `opal-test-agent` (mode: red) 기존 역할 | 없음 |
| 스킬 문서 재작성 | 신규 스킬 불요 — PLAN §3이 편집 지시를 전량 명세 | 없음 |
| Node CLI 서브명령 구현 | 기존 파일 패턴 승계 (`migrateCommand`·`parseSourceRepo`가 동형 선례) | 없음 |

갭 판별: 동일 패턴이 3개 이상 Step에 반복되지 않으므로 신규 스킬 후보 0건 — PLAN 인라인 지침으로 충분하다.

### C-3. 도구 요구사항

| 도구 | 용도 | 상태 |
|------|------|------|
| `node` (18+) | `skill-registry.js` 실행 + `node --test` | 기설치 (`docs/ARCHITECTURE.md:359`) |
| `~/.opal/tools/code-scan/code-scan.js target` | @header 기록 위치 판정 | 기설치 (E1 실행 확인) |
| `~/.opal/tools/date` | 변경이력 KST 일시 실측 | 기설치 |
| `grep -F` | 축자 앵커 검증 | 시스템 |
| Python venv (`~/.opal/.venv`) | `test_adapters.py` 실행 (Step 9, 가용 시) | 조건부 — 미가용이면 `list` 출력 직접 대조로 대체 |

신규 패키지·MCP 0건.

### C-4. 테스트 전략

- **RED (Step 1)**: `node --test opal/tools/skill-registry/tests/test-scan-risk.js` → exit ≠ 0 증거 기록. [MUST] `opal/core/references/harness/red-first.md` §3 — GREEN 루핑 중 이 파일 수정 금지.
- **GREEN (Step 2)**: 동일 명령 exit 0.
- **회귀 (Step 9)**: `node --test opal/tools/skill-registry/tests/` 4파일 전건 + `list` 출력 대조 + `test_adapters.py::test_skill_adapter_list`.
- **산출물 검사 (Step 9)**: TS-001·002·003·020~023·030~033·040·041·050~052·060~062·070~072를 grep 기반 결정론 검사로 수행.
- **공개 인터페이스만 검증** — 내부 함수 직접 호출 없이 CLI exit code + stdout JSON으로 판정한다 ([MUST] `opal/core/references/harness/red-first.md` §4).

### C-5. RED-first 트랙 판정 (필수 기재)

`opal/core/references/harness/red-first.md` §1.5 적용 기준으로 F별 판정:

| F-ID | 변경 성격 | 트랙 | 근거 |
|------|----------|------|------|
| **F-002** | 신규 Node CLI 서브명령 + 판정 로직 + 출력 계약 | **RED-first 강제** | §1.5 「API 계약」 — `{ok, verdict, hits[]}`는 SKILL.md가 소비하는 계약이다. 또한 §1.5 「비즈니스 로직」 — verdict 산출·오탐 억제 4규칙은 판정 로직이다 |
| F-001, F-003, F-004, F-005, F-006, F-007, F-008 | 스킬 문서·설계 문서 재작성 | 구현 후 시나리오 검증 허용 | §1.5 「설정·문서」 |

**self-confirming 위험 판정 (명시)**: F-002는 **위험 높음**이다. 근거 — ① verdict 산출 규칙과 그 검증 단정이 같은 판단에서 나오면 「구현한 대로가 정답」이 되어 오탐 억제 규칙(H-3)이 실질 검증되지 않는다 ② 오탐/미탐은 **픽스처 설계 자체가 검증의 본질**이므로, 구현자가 픽스처를 만들면 자기가 잡을 수 있는 패턴만 픽스처에 넣는 편향이 구조적으로 발생한다 ③ 「무해 픽스처에서 검출 0건」은 픽스처를 무해하게 만들수록 쉽게 통과하는 reward hacking 표면이다. 따라서 Step 1을 `opal-test-agent`로 분리하고 Step 2는 픽스처를 **수정하지 않는다**.

**공통 불변 3조건 충족**: ① 테스트 코드 산출물 = `test-scan-risk.js` ② 작성자(Step 1 `opal-test-agent`) ≠ 구현자(Step 2 `opal-task-agent`) ③ TEST 단계 검증 = Step 9.

**§1.6 목표계열 선작성 트랙**: 착수하지 않는다 — 이 태스크의 목표는 교체형이 아니라 기존 절차에 판정 축을 **추가**하는 것이고, 핵심 목표(위험 스킬 차단)가 파괴 관점(리스크 가설)으로 그대로 환원된다. §1.6 (f) 착수 판단 기준의 「목표가 단일 결함 수정이고 검증 관점이 파괴 관점과 사실상 일치한다 → 순차 권장」에 해당한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Node.js 18+ CommonJS, 외부 의존 0 (`fs`/`path`/`os`) | 해당 없음 — 프레임워크 본체 |
| 도구 테스트 | `node:test` + `node:assert/strict` + `node:child_process` CLI 블랙박스 | 해당 없음 |
| 스킬 문서 | Markdown + YAML frontmatter | `opal-skill-creator` (문서 표준 참조) |
| 절차 | Bash — `git clone --depth 1`·`git log -1`·`git ls-remote`·`mktemp -d`·`npx skills find` | 해당 없음 |

> plan-guide.md §0단계의 기술 컨텍스트 스킬 표(React/Next.js/Python/FE)는 이 태스크의 스택과 무관하여 전건 미적용이다. `~/.opal/community-skills/vercel-labs/`는 실제로 존재하지 않는다(E1 — `ls ~/.opal/community-skills/` 결과 `anthropics`·`getsentry`·`google-labs-code`·`obra`·`openai`·`modern-python`).

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 외부 라이브러리 API 조회 불요 — Node 내장 모듈과 프로젝트 내부 코드만 사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 개선 대상 본문 — 현행 §1~§6 절차·절 번호 구조·§변경이력 (v1.4.1, 217줄) |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | `main()` switch(653-724)·종료 코드 규약(720-723)·`validate()` 미지 필드 무시(435-462)·`listCommand`(340-369)·`matchCommand`(251-317)·ReDoS 헬퍼(145-166)·`loadAllSkills`/`flattenGroups`(58-143) — 실측 726줄 |
| D-3 | 소스 | test-validate.js / test-migrate.js | `opal/tools/skill-registry/tests/test-validate.js`, `tests/test-migrate.js` | 신규 테스트가 승계할 패턴 — CLI 블랙박스·`mkdtempSync` 합성 픽스처·인라인 @header·TC↔시나리오 매핑 주석 |
| D-4 | 소스 | skill_adapter.py / test_adapters.py | `dashboard/backend/adapters/skill_adapter.py:49-60`, `dashboard/backend/tests/test_adapters.py:96-101` | `list` 무인자 호출 소비 계약 — H-1 무수정 경계의 근거 |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §@header 규칙·§변경이력 작성 의무·§배포 경계(커뮤니티 스킬 이원 경계 + 런타임 쓰기 예외)·§플랫폼 분기 격리·§도구 우선 원칙 |
| D-6 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 2-Layer 배포 모델(221-224)·tools/ 인벤토리(81)·커뮤니티 스킬 정책(189-197) — F-008 갱신 대상 |
| D-7 | 설계 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | §Core Stance(tool gates it)·§2 Simplicity First·§3 Surgical Changes — 루브릭 폐기·무수정 경계 근거 |
| D-8 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | §1 RED→GREEN·§1.5 하이브리드 자동분기·§1.6 선작성 opt-in·§2 작성자≠구현자·§3 테스트 불변성·§4 공개 인터페이스 — C-5 판정 근거 |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷·§2.2 코드 근거·§2.4 [MUST] 토큰·§9 근거 등급(E5 단독 인용 금지) |
| D-10 | 가이드 | skill-commands.md | `opal/core/references/harness/skill-commands.md:24,36` (배포본 `~/.opal/references/harness/skill-commands.md`) | `SKILL.md §6`·`§2` 축자 앵커 — H-2 절 번호 보존 요구의 근거 |
| D-11 | 소스 | opal-skill-creator SKILL.md | `opal/skills/opal-skill-creator/SKILL.md:38-77` | F-007 위임 페이로드가 충족해야 하는 입력 지점 — Capture Intent 3항목·Interview·스킬 유형 판단 |
| D-12 | 소스 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | 카탈로그 실측 형상 — `$schema` v2.1·`groups` 7 vendor·항목 7필드 (F-005 additive 근거) |
| D-13 | 지식(E5) | community-skill-user-registry.md | `.opal/brain/pages/concept/community-skill-user-registry.md` | registry 이원 구조 결정 배경. **stale 서술 2건 확인 — 단독 근거로 사용하지 않음** (H-8, `citation-rules.md` §9 (e)) |
| D-14 | 지식(E5) | skill-quoting-ssot-must-edit-ssot-first.md | `.opal/brain/pages/concept/skill-quoting-ssot-must-edit-ssot-first.md` | SSOT 선행 개정 + `grep -F` 축자 일치 검증 — §3.8.2 (b) 검증 절차 근거 |
| D-15 | 외부 | skills.sh | [skills.sh](https://skills.sh/) | 6단 흐름 1단의 탐색 소스 — `npx skills find` 출력 필드 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | `list` 출력 계약 파손 → OPAL Console 스킬 화면 즉시 파손 (H-1) | F-002 | P0 | Step 2 무수정 경계를 `[MUST]`로 고정 + Step 9에서 `list` 출력 대조 및 `test_adapters.py` 실행 (TS-015) |
| 2 | 절 번호 이동으로 `skill-commands.md` 축자 앵커 무성 파손 (H-2) | F-001, F-008 | P0 | 절 번호 보존 설계(§3.1.2 (a)) + 신규 규격을 `####` 하위로만 삽입 + Step 9 grep 6건 검증 (TS-071). 이동 불가피 시 동반 개정 Step 내포 |
| 3 | 위험 패턴 오탐으로 무해 스킬 전량 RISKY 탈락 → 절차 기능 정지 (H-3) | F-002 | P0 | 오탐 억제 4규칙(§3.2.2 (d)) + `context` 태그로 verdict 승격 분리 + 오탐 픽스처 4종 테스트 (TS-013) |
| 4 | 산문 지시형 위험 스킬 미탐 → 보안 축 형식화 (H-4) | F-002 | P1 | 한계를 SKILL.md에 명문화(「1층은 필요조건이며 사람 검토를 대체하지 않는다」) + 2층 판정에 사람의 SKILL.md 실물 대조를 유지 |
| 5 | brain 페이지 stale 서술이 후속 워커에 잘못된 전제 주입 — 카탈로그 `commit_sha` 갱신 가능/`loadAllSkills` flat 배열 (H-8) | F-005 | P2 | PLAN이 코드·SKILL.md 기준을 명시(§2.5.2)하고 `citation-rules.md` §9 (e)에 따라 D-13을 단독 근거에서 배제. Step 7 완료 기준에 `:102` 금지 문장 잔존 확인 포함 (TS-072). **brain 페이지 정정은 이 태스크 범위 밖 — PM 백로그 후보** |
| 6 | `match` 출력에 `matched_by` 부재 → Exact/Partial 판정이 산문 판단으로 흐름 (H-6) | F-006 | P1 | 판정을 문자열 동일성 비교로만 기술(§3.6.2 (a)) + `matched_by` additive 추가는 Surgical Changes에 따라 범위 밖으로 보류. **후속 백로그 후보** |
| 7 | 추천 사다리 동률에서 주관 판단 유입 → 100점 루브릭 실패모드 회귀 (H-9) | F-003 | P1 | 사다리 6단 + 6단(동률)에서 자동 선택 금지·사용자 선택 요청으로 종료 + 점수 표기 0건 검사 (TS-021, TS-023) |
| 8 | 정규식 ReDoS로 악성 스킬이 스캐너를 정지 (H-7) | F-002 | P1 | nested quantifier 금지 + 라인 2000자·파일 1MB 상한 + 병리 입력 타임박스 테스트 (TS-016) |
| 9 | user-registry 형상 위반으로 설치 이력 조용히 유실 (H-5) | F-005 | P1 | `groups[vendor][]` 형상 `[MUST]` 명시(§3.5.2 (b)) + 합성 픽스처로 `validate`·`list` 검증 (TS-042, TS-043) |
| 10 | `~/.opal/community-skills/modern-python/`이 vendor 미중첩 flat 잔재로 남아 있어 등급·설치 판정이 흔들릴 수 있다 (E1 실측) | F-006 | P2 | 현행 §관리 진입 훅의 `migrate` 1회 멱등 실행을 무변경 유지 — 4절차 공통 선행이므로 자동 정규화된다 (`opal/skills/opal-skill-manager/SKILL.md:14-25`) |
| 11 | 3건 clone으로 네트워크·디스크 비용이 3배가 되고 후보 저장소가 대형이면 지연 | F-001 | P2 | `--depth 1` + 후보 상한 3 + 추천 확정 즉시 미채택 clone 삭제(§3.1.2 (f)) |

---

## 에스컬레이션 권고

**해당 없음.** 3조건 전건 미해당 — (a) 예상 변경 파일 **4개**(신규 1 + 수정 3)로 10개 미만 (b) 다단계 기술 의사결정 **미결 0건** — 위험 패턴 목록·오탐 억제 규칙·4단 매핑·추천 사다리를 이 PLAN이 전건 확정했고 EXECUTE에 남은 판단은 없다 (c) 변경 모듈은 스킬 문서 1 + Node 도구 1(+테스트) + 설계 문서 1로, 연쇄 영향을 받는 독립 모듈은 `dashboard` 어댑터 1개뿐이며 그마저 **무수정 회귀 확인** 대상이다.

> 참고: Step 수 10개는 `references/plan-guide.md` §4.2의 Short Task 권장치(5개 이하)를 초과한다. 다만 초과분 5개는 **동일 파일(`SKILL.md`)을 순차 편집하는 Step 3~8**이며 단일 디스패치 1회로 실행되므로 실제 디스패치 수는 5회다. 파일·모듈 규모가 Short Task 범위 안이므로 Full Task 전환을 권고하지 않는다.

---

## 발견한 문서·코드 불일치 (PM 보고용)

| # | 불일치 | 실측 (코드 = 실질적 문서) | 문서/전제 서술 | 처리 |
|---|--------|--------------------------|--------------|------|
| 1 | brain 페이지의 카탈로그 갱신 서술 | `opal/skills/opal-skill-manager/SKILL.md:102` — `[MUST] ~/.opal/references/community-skills-registry.json(프레임워크 카탈로그)은 설치 시 수정하지 않는다` | `.opal/brain/pages/concept/community-skill-user-registry.md` §기록 규칙 — "registry 등재 스킬 → 카탈로그 기존 항목에 `commit_sha` 갱신 가능" | 코드·SKILL.md 기준 채택. brain 정정은 범위 밖 — PM 백로그 후보 (H-8) |
| 2 | brain 페이지의 `loadAllSkills()` 예시 | `opal/tools/skill-registry/skill-registry.js:125-143` + `58-74` — `groups[vendor][]`를 `flattenGroups`로 평탄화한 뒤 `name` 기준 override 병합 | 동 brain 페이지 §로드 규칙 — flat 배열 spread 병합(`[...catalogSkills, ...userSkills]`)으로 묘사 | 코드 기준 채택. §3.5.2 (b)에 형상 제약 명시 (H-5, H-8) |
| 3 | `skill-registry.js` 규모 | **726줄** (`wc -l` 실측) | PM 디스패치 프롬프트 「현재 1071줄 규모」 | 실측 채택. 설계 영향 없음 |
| 4 | `match` 출력의 매칭 경로 노출 | `opal/tools/skill-registry/skill-registry.js:277-317` — `matched_by` 필드 없음 | R-6이 Exact/Partial 등급 구분을 요구 | 문자열 동일성 비교로 우회(§3.6.2 (a)·(c)). `matched_by` additive 추가는 후속 백로그 후보 (H-6) |
| 5 | user-registry 실재 여부 | `~/.opal/community-skills/user-registry.json` **미존재**. 반면 vendor 디렉토리 6개 실재(`anthropics`·`getsentry`·`google-labs-code`·`obra`·`openai`·`modern-python`) | TASK.md:19 "현재 미존재, 설치 이력 0건" — 미존재는 일치하나 **설치 실물은 6건 있다** | 백필 0건 유지(§3.5.2 (c)). flat 잔재 `modern-python`은 `migrate` 훅이 흡수 (리스크 #10) |
| 6 | plan-guide 기술 컨텍스트 경로 | `~/.opal/community-skills/vercel-labs/`·`trailofbits/` **미존재** (`modern-python`은 flat) | `~/.opal/skills/op-dev-plan/SKILL.md` §Step 2 탐색 경로 표 | 이 태스크 스택과 무관하여 미적용. §8.1 각주에 기재 |

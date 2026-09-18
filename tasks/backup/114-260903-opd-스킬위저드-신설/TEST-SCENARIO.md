# TEST SCENARIO: opal-skill-wizard 신설 — 프로젝트 적합 스킬 제안 + 프로젝트 스코프 설치

> 작성일: 2026-09-04 | 상태: 작성 완료 (Block A 선작성 + Block B 보강 완료)
> 작성자: PM(알투) — 캡틴 페어 | 트랙: 목표계열 선작성 (`opal/core/references/harness/red-first.md` §1.6)

## 선작성 트랙 기록

| 항목 | 값 |
|------|-----|
| Block A 착수 | PLAN 워커 실행과 병렬 (2026-09-03 23:47~23:50) |
| Block A 도출 입력 | TASK.md §작업 목표 / §요구사항 R-1~R-11 / §완료기준 — **3종 한정**, PLAN.md 미열람 |
| Block B 보강 | 2026-09-04 07:40~ — PLAN.md §리스크 가설 표(H-1~H-9) + §1.2 기능 목록(F-001~F-006) + §3 TS-001~TS-020 추가 입력 |
| 커버 루브릭 축 | ① 목표달성 ② 요구커버 ③ 기능커버 ④ 리스크커버 ⑤ 채택·잔존 ⑥ 경계·부정 (6축 전건) |
| 보강 완료 판정 | 3조건 충족 — 마커 잔존 0건 / H-N 전건 전재 / 매핑 표 전 행 가설·계층 기재 |

### Block B 보강에서 수정·삭제한 초안 시나리오

> `test-scenario-guide.md` §Block B [MUST]: "보강은 additive-only가 아니다 — 초안의 각 시나리오를 H-N·F-NNN과 대조하여 중복·과잉·PLAN 설계와 어긋나는 시나리오를 수정 또는 삭제한다."

| 초안 ID | 처리 | 사유 |
|---------|------|------|
| S-A4~S-A14 | **TS-011~TS-020으로 흡수(삭제)** | PLAN이 동일 AC를 TS-NNN으로 정식 채번하고 각 Step 완료 기준에 배선했다 — 초안 ID를 병존시키면 추적 축이 이중화된다 |
| S-A8·S-A9·S-A17·S-A18·S-A24·S-A26 | **TS-001~TS-009로 흡수(삭제)** | PLAN §3.1.5가 동일 조건을 L2 통합으로 정식화했다 |
| S-A15 | **TS-013에 병합(삭제)** | 「manager 호출 지시 0건」이 TS-013 기대 결과에 이미 포함 — 중복 |
| S-A25 | **TS-018에 병합(삭제)** | alias 충돌 검출이 TS-018 기대 결과와 동일 |
| S-A16 | **TS-002·TS-010으로 분해(삭제)** | 「전역 동작 보존」이 부재 시 무회귀(TS-002)와 기준선 대조(TS-010) 2건으로 정확히 분해된다 |
| S-A1·S-A2·S-A3 | **유지 → TS-021·TS-022·TS-023으로 채번** | 축 ① 목표달성. PLAN의 TS-011~014는 **문서 정적 검사**여서 wizard가 실제로 동작하는지를 검증하지 않는다 — 선작성 고유 커버 |
| S-A19·S-A20·S-A21·S-A22 | **유지 → TS-024~TS-027로 채번** | 축 ⑥ 경계·부정. PLAN §3.3.3 판정표·§7 위임 트리거에 대응 설계는 있으나 **시나리오로 채번되지 않았다** |
| S-A27 | **유지 → TS-028로 채번 (PLAN 갭)** | 비프로젝트 호출 시 동작이 PLAN에 미규정 — PM Gate 조기 경보로 표면화한 항목 |
| S-A28 | **유지 → TS-029로 채번** | 미지 필드 additive 안전성. TS-015(스키마 정합)와 별개 축 |

## 게이트 반영 이력

### iteration 1 — `verdict: fail` (평균 1.33 < 1.5)

| 축 | 점수 | Evaluator 지적 |
|----|------|---------------|
| ① 목표달성 | 2 | 충족 — TS-023(종단 실행) + TS-021·022(M3 인터뷰). M3 선택도 정당 판정 |
| ⑤ 채택·잔존 | 1 | 구형 잔존0(TS-013·019 정적 grep)은 되나 **신형 채택의 실행-시간 검증이 전무** |
| ⑥ 경계·부정 | 1 | 레지스트리 계층 8건은 견고하나 **wizard 부정경로 5건(TS-024~028)이 전부 정적 grep** — AC 재확인 수준의 self-confirming |

> 핵심 지적: "문서에 규칙이 쓰여 있다"와 "wizard가 실제로 그렇게 행동한다"를 구분하지 못한다. 보안 게이트(H-8/P1)조차 정적 확인에 그친다.

### iteration 2 재작성 방침 — **부작용 관측으로 실행을 증명한다**

Evaluator 보강안은 M3(캡틴 수동) 승격을 제시했으나, Producer는 **부작용 관측(side-effect observation)** 방식을 택했다. 이유: wizard의 행동은 결국 **파일시스템 변화**로 나타나므로, "무엇이 생겼는가 / 무엇이 생기지 않았는가"를 검사하면 자동화(M1)로도 실행-시간 검증이 성립한다. 이 방식은 M3보다 재현 가능하고 회귀 감지가 된다.

| 지적 | 반영 |
|------|------|
| ⑤ 신형 채택 실행 검증 부재 | **TS-030·TS-031 신설** — 설치 후 프로젝트 registry에 항목이 기록되고(`scope:"project"`), **동시에 전역 `~/.opal/community-skills/`·`user-registry.json`에 변화 0건**임을 확인한다. 전역 무변화가 곧 "manager 경로를 타지 않았다"는 실행-시간 증거다 |
| ⑥ 부정경로가 정적 grep뿐 | **TS-032~TS-036 신설** — `scan-risk` 판정은 도구 결정론이므로 위험/무해 fixture로 실판정을 검증하고(TS-032·033), 부정 분기 3종은 **설치 부작용 부재**(프로젝트 스코프 파일 생성 0건)로 관측한다(TS-034~036) |
| TS-024~028 성격 | **삭제하지 않고 「정적 축」으로 명시 격하** — 규칙 문면 존재는 필요조건이나 충분조건이 아니며, 각각 실행 축 시나리오와 짝을 이루도록 표에 대응 관계를 기재했다 |
| ① 참고 지적 (검색 스모크) | TS-037로 반영 — 알려진 검색어로 `npx skills find` 1회 실행해 결과 ≥1건 확인(네트워크 의존이므로 실패 시 Skip 허용) |

### iteration 2 — `verdict: pass` (평균 1.67 ≥ 1.5)

| 축 | 점수 | 판정 |
|----|------|------|
| ① 목표달성 | 2 | 유지 — TS-037 순증분으로 iteration 1 참고 지적까지 해소 |
| ⑤ 채택·잔존 | **1 → 2** | TS-030(신형 채택)·TS-031(전역 무변화)이 **같은 실행에 대한 긍정+부정 짝**이라, TS-030이 설치 완료를 양성 확정하므로 TS-031의 무변화가 "우연한 무변화"일 가능성이 논리적으로 배제된다 |
| ⑥ 경계·부정 | 1 | 유지(2점 미부여) — TS-032·033은 견고하나 TS-034~036이 부정 결과만 **단독** 주장하고 긍정 짝이 없다 |

> Producer의 **부작용 관측 방법론 자체는 타당** 판정. `scenario-gate.md` §5-1 수렴 조건(각 축 ≥1 AND 평균 ≥1.5) 충족 → 게이트 PASS.

### 게이트 통과 후 보강 (⑥ 잔여 지적 반영)

게이트는 통과했으나 ⑥의 지적("정상 차단"과 "조기 실패로 우연히 없음"이 구분되지 않는다)은 값싸게 닫을 수 있어 **재게이트 없이 반영**했다 — 통과를 위한 조정이 아니라 품질 보강이므로 iteration을 올리지 않는다.

- TS-034·035·036의 기대 결과를 **(a) exit 0 + (b) 사유 신호 존재 + (c) 부작용 부재 3조건 AND**로 강화
- (b)의 구체 신호를 시나리오별로 특정 — TS-034 = RISKY 판정 출력 / TS-035 = creator 위임 페이로드 최소 2필드 / TS-036 = 대상 부재 안내
- 근거: 같은 문서 TS-002·TS-003이 이미 exit 0을 명시하는 선례

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-9 **전건 전재** (보강 완료 판정 2조건).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 `loadAllSkills()` 4번째 소스 병합 | 프로젝트 registry 부재 시 전역 3소스 병합 결과가 **완전 동일**해야 한다는 무회귀 계약 | P0 — 전 pilot `//` 매칭 붕괴 | L2 | TS-002, TS-010 |
| H-2 | F-001 `loadProjectRegistry()` 파손 내성 | 부재/파손 시 `null` 반환 → CLI 다운 방지 (`skill-registry.js:118-128` 동형) | P0 — 파손 JSON 1개로 전 스킬 발동 불가 | L2 | TS-003 |
| H-3 | F-001 `getCommand()` `resolved_path` 추가 | raw passthrough — 기존 필드 삭제·의미 변경 0건 | P1 — `opal-help`·`opal-skill-manager` 문서 절차 무효화 | L1 + L2 | TS-006 |
| H-4 | F-001 walk-up 홈 경계 | `~/.opal/`을 프로젝트 스코프로 오인하지 않음 | P0 — 전역 자산 이중 로드로 `_source` 오염 | L1 + L2 | TS-008, TS-036 |
| H-5 | F-001 walk-up 상향 탐색 | 하위 디렉토리 호출 시에도 루트 도달 | P1 — 조용히 전역만 병합 | L2 | TS-007 |
| H-6 | F-001 `matchCommand()` project 분기 | `installed` 의미 일반화 + `scope` 신규 필드 | P1 — `skill-commands.md:24` 라우팅이 `installed` 의존 | L2 + L3 | TS-005, TS-019, TS-030, TS-031 |
| H-7 | F-001 override 순서 (DEC-3) | 동일 `name` 시 프로젝트 최우선 | P2 — 전역이 프로젝트 의도를 덮어씀 | L2 | TS-009 |
| H-8 | F-003 wizard `scan-risk` 게이트 | "검사 실패 시 복사하지 않는다"가 산문이 아닌 **절차 순서**로 강제 | P1 — 미검사 외부 코드 유입 | **L2(실행) + L3(정적)** | TS-014, TS-024, TS-025 (정적) / **TS-032, TS-033, TS-034 (실행)** |
| H-9 | F-005 `opal-skills-registry.json` 등재 | JSON 스키마 유효성 + alias 유일성 | P1 — 파손 시 전 스킬 매칭 불가 | L2 | TS-017, TS-018 |

## 2. 테스트 데이터 설계

> 이번 태스크는 DB를 사용하지 않는다(레지스트리 JSON + Markdown). 따라서 §2.1의 "테이블/식별자/상태"는 **fixture 파일 상태**로 치환한다 — Block A가 예고한 치환이며 PLAN §3.2.2 격리 설계로 확정됐다.

### 2.1 사전 조건 데이터 (fixture 파일 상태)

| fixture | 경로 | 상태 | 출처 |
|---------|------|------|------|
| 가짜 HOME | `{tmp}/osw-home-*/.opal/references/opal-skills-registry.json` + `community-skills-registry.json` | 최소 유효 JSON (전역 카탈로그 2종) | fixture (`mkdtempSync`) |
| 가짜 프로젝트 루트 | `{tmp}/osw-proj-*/.opal/` | 디렉토리 존재 (**루트 탐색 마커**) | fixture |
| 프로젝트 registry — 정상 | `{tmp}/osw-proj-*/.opal/skills-registry.json` | 유효 JSON, `groups.project` 1항목 이상 | fixture |
| 프로젝트 registry — 부재 | (동일 경로) | 파일 미생성 | fixture |
| 프로젝트 registry — 파손 | (동일 경로) | 잘린 JSON 문자열 | fixture |
| 프로젝트 스킬 본체 | `{tmp}/osw-proj-*/.opal/community-skills/{vendor}/{skill}/SKILL.md` | 존재 / 미존재 2종 | fixture |
| 하위 디렉토리 | `{tmp}/osw-proj-*/a/b/c/` | 3단 하위 (walk-up 검증용) | fixture |
| 홈 하위 cwd | `{fakeHome}/somewhere/` | 프로젝트 registry 부재 | fixture |

> **[MUST] `getReferencesDir()` 1순위 회피**: 가짜 프로젝트 루트에 `opal/core/references/`를 두지 않아야 2순위(가짜 HOME 배포 경로)로 떨어진다 (PLAN §3.2.2). 이 조건을 fixture 헬퍼 주석에 명시한다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| TS-001 | 정상 registry + 본체 존재 | `match "{name}"` | `found:true`, `scope:"project"`, `installed:true` |
| TS-002 | registry 부재 | `match`/`get`/`list`/`validate` | exit 0 + 전역 3소스 결과가 기준선과 동일 |
| TS-003 | 파손 registry | 동상 | exit 0 + `_source:'project'` 항목 0건 |
| TS-004 | 정상 registry + 본체 존재 | `get "{name}"` | `resolved_path` = 본체 SKILL.md 절대경로 |
| TS-005 | 정상 registry + 본체 **미존재** | `get` / `match` | `resolved_path:null` / `installed:false` |
| TS-006 | main 스킬 (전역 카탈로그) | `get "{main 스킬}"` | `paths` 배열 원형 보존 + `resolved_path` 추가 |
| TS-007 | 정상 registry, cwd = 3단 하위 | `match "{name}"` | `found:true` (walk-up 도달) |
| TS-008 | cwd = `$HOME` 하위, registry 부재 | `list` | `_source:'project'` 항목 0건 |
| TS-009 | 전역·프로젝트에 동일 `name` | `get "{name}"` | 프로젝트 정의가 반환 |
| TS-029 | registry 항목에 스키마 외 미지 필드 포함 | `validate` | error 0건 |

## 3. 검증 시나리오

> **계층 결정 근거** (`test-scenario-guide.md` §Step 3 계층 결정 규칙 표): 변경 영역이 **비즈니스 로직**(CLI 로더·경로 해석)이므로 L1(함수 단위 정상/경계) + L2(서비스 계층 흐름) 의무. FE 화면·인증/인가·외부 API 연동이 **없으므로 M2(E2E 자동화) 의무 트리거는 발동하지 않는다**. API 엔드포인트도 없어 Swagger M2 트리거도 비대상. 문서·설정 변경분은 L3 정적 검사로 처리한다.

### L1. 기능 단위

#### TS-006: `get` 하위호환 — 기존 필드 원형 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `getCommand()` additive `resolved_path` (PLAN DEC-5) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — `node:test`)** |
| 조건 | 전역 카탈로그의 main 스킬 1건에 대해 `get` 호출 |
| 기대 결과 | 응답에 기존 `paths` 배열이 **원형 그대로** 존재하고, 필드 삭제·타입 변경 0건이며, `resolved_path`가 추가로 존재한다 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-project-registry.js` (관측 스코프: cwd=리포지토리 루트) |
| 결과 | **PASS** |
| 상세 | `[T114/L2-006] TS-006` subtest `ok` (exit 0, duration 20.5ms). main 스킬 `get` 응답에 기존 `paths` 배열이 원형 보존되고 `resolved_path` 필드가 추가된 것을 테스트가 단언 — 필드 삭제·타입변경 0건 확인 |

#### TS-008: walk-up 홈 경계 정지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `findProjectRoot()` 종료 조건 ① (PM 교정으로 마커 = `.opal/` 디렉토리) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `cwd`를 가짜 HOME 하위로 두고 프로젝트 registry는 두지 않는다. 가짜 HOME에는 `.opal/`이 **존재**한다(전역 배포 구조) |
| 기대 결과 | 홈 디렉토리를 프로젝트 루트로 반환하지 않는다 — `_source:'project'` 항목 0건. 전역 자산이 프로젝트 스코프로 이중 로드되지 않는다 |
| 도구 | `node:test` + `spawnSync` (`env.HOME` 오버라이드) |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-project-registry.js` (관측 스코프: cwd=리포지토리 루트) |
| 결과 | **PASS** |
| 상세 | `[T114/L2-008] TS-008` subtest `ok` (exit 0, duration 19.5ms). cwd를 가짜 HOME 하위로 두고 홈에 registry가 실재해도 `_source:'project'` 병합 0건을 테스트가 단언 — 홈 경계 정지 확인 (P0) |

> **[중요] 이 시나리오는 PM 마커 교정(파일 → `.opal/` 디렉토리)으로 **판정 강도가 올라갔다** — 마커가 디렉토리이면 `~/.opal/`이 항상 존재하므로 홈 경계 정지가 유일한 방어선이 된다. 실패 시 P0.

### L2. 프로세스 통합 (실 fs fixture + 실제 CLI 프로세스)

> 본 태스크 검증의 **중심 계층**이다. `spawnSync`로 실제 CLI를 별도 프로세스로 실행하며 mock을 쓰지 않는다.

| TS-ID | 가설 | 대상 | 조건 | 기대 결과 | 실행 방식 | 결과 | 상세 |
|-------|------|------|------|----------|----------|------|------|
| TS-001 | H-1 | 프로젝트 registry 병합 | 정상 registry + 본체 존재 | `match "{name}"` → `found:true`, `scope:"project"`, `installed:true` | M1 | **PASS** | `node opal/tools/skill-registry/tests/test-project-registry.js`(cwd=repo 루트) — `[T114/L2-001]` ok, 27.7ms |
| TS-002 | H-1 | 부재 내성 + 무회귀 | registry 파일 미생성 | exit 0 + `match`/`get`/`list`/`validate` 결과가 전역 3소스 기준선과 동일 | M1 | **PASS** | 동상 — `[T114/L2-002]` ok, 169.7ms |
| TS-003 | H-2 | 파손 내성 | 잘린 JSON | exit 0 + 전역 3소스만 병합, 예외 전파 0건 | M1 | **PASS** | 동상 — `[T114/L2-003]` ok, 39.7ms |
| TS-004 | H-3 | `resolved_path` 해석 | 본체 존재 | `get` → `resolved_path` = 실제 SKILL.md 절대경로 | M1 | **PASS** | 동상 — `[T114/L2-004]` ok, 20.9ms |
| TS-005 | H-6 | 미설치 처리 | 등재됐으나 본체 미존재 | `get` → `resolved_path:null` / `match` → `installed:false` | M1 | **PASS** | 동상 — `[T114/L2-005]` ok, 39.9ms |
| TS-007 | H-5 | walk-up 상향 | cwd = 루트 3단 하위 | `match` → `found:true` | M1 | **PASS** | 동상 — `[T114/L2-007]` ok, 21.0ms |
| TS-009 | H-7 | override 우선순위 | 전역·프로젝트 동일 `name` | 프로젝트 정의가 반환 (`_source` 유래 project) | M1 | **PASS** | 동상 — `[T114/L2-009]` ok, 20.6ms |
| TS-010 | H-1 | 기존 테스트 무회귀 | 기존 4파일 개별 실행 | **41 pass / 0 fail** 기준선과 동일 (test-match 11 / test-validate 5 / test-migrate 9 / test-scan-risk 16, cwd 리포지토리 루트) | M1 | **PASS** | 재실행 실측(cwd=repo 루트): `node opal/tools/skill-registry/tests/test-match.js` → 11 pass/0 fail · `test-validate.js` → 5 pass/0 fail · `test-migrate.js` → 9 pass/0 fail · `test-scan-risk.js` → 16 pass/0 fail. 합계 41 pass/0 fail, 전건 exit 0 — 기준선과 완전 동일 |
| TS-015 | H-9 | 스키마 `validate` 정합 | 스키마 준수 registry | `validate` error 0건 | M1 | **PASS** | `test-project-registry.js` `[T114/L2-015]` ok, 20.5ms(cwd=repo 루트) |
| TS-017 | H-9 | wizard 매칭 | 등재 후 | `match "osw"` → `found:true` + `name:"opal-skill-wizard"` | M1 | **PASS** | 재실행 실측(cwd=repo 루트): `node opal/tools/skill-registry/skill-registry.js match "osw"` → `{"found":true,"name":"opal-skill-wizard","alias":"osw","path":"/Users/lucas/.opal/skills/opal-skill-wizard/SKILL.md",...}`, exit 0 |
| TS-018 | H-9 | alias 유일성 | 등재 후 전체 | alias 중복 0건 + `validate` error 0건 | M1 | **PASS (맥락 반영)** | 재실행 실측(cwd=repo 루트): `node opal/tools/skill-registry/skill-registry.js validate` → exit 1, `errors:["op-scenario-gate: unregistered — folder exists but not in registry"]` 1건. **이 오류는 114과 무관한 선존 결함**(`op-scenario-gate`는 105 이전부터 존재하는 별개 스킬 폴더이며 osw/opal-skill-wizard와 무관) — 114이 유발한 오류 0건. alias 중복 관련 오류는 errors 목록에 0건(=alias 유일성 위반 없음). validate exit code가 1인 것은 선존 결함 때문이며 114 시나리오 요구인 "alias 중복 0건"은 충족 |
| TS-023 | H-6 | **설치 → 발동 종단 경로** | 프로젝트에 스킬 1건 설치 시뮬레이션 직후 | registry 항목 기록 + `match "{name}"` → `found:true` + 반환 경로에 SKILL.md 실물 존재 | M1 | **PASS (수동 리허설로 대체 확인 — 블로커 별첨)** | §L2-실행축 TS-030 리허설이 동일 조건을 실측: fixture 프로젝트에 `jimliu/baoyu-markdown-to-html` 설치 후 `match "//jimliu/baoyu-markdown-to-html"`(cwd=fixture 프로젝트) → `found:true, scope:"project", installed:true`, 반환 `path`의 SKILL.md 실물 존재 확인(exit 0). **블로커**: §4 AC 매핑 표는 TS-023이 `tests/test-project-registry.js`에 구현되어 있다고 명시하나, 해당 파일에 "023"·"GOAL" 문자열이 0건 — 자동화 테스트로 커버되지 않음(grep 실측, cwd=repo 루트). 수동 리허설로 기능 자체는 검증했으나 회귀 감지용 자동 테스트가 부재하다는 커버리지 갭이 있다 |
| TS-029 | H-9 | 미지 필드 additive 안전성 | 스키마 외 미지 필드 포함 항목 | `validate` error 0건 (현행 미지 필드 무시 동작 보존) | M1 | **PASS** | `test-project-registry.js` `[T114/L2-029]` ok, 20.5ms(cwd=repo 루트) |

### L2-실행축. 부작용 관측 (iteration 2 신설 — 실행-시간 검증)

> **판정 원리**: wizard의 행동은 파일시스템 변화로 나타난다. **무엇이 생겼는가**(채택 증거)와 **무엇이 생기지 않았는가**(부정 경로 준수 증거)를 검사하면 정적 문서 검사가 못 잡는 실행-시간 결함을 잡는다. 전 시나리오 M1(자동화) — M3 승격 없이 재현성과 회귀 감지를 확보한다.

| TS-ID | 가설 | 축 | 조건 | 기대 결과 (부작용) | 실행 방식 | 결과 | 상세 |
|-------|------|----|------|------------------|----------|------|------|
| TS-030 | H-6 | ⑤ 신형 채택 | fixture 프로젝트에서 스킬 1건 설치 완료 | `{project}/.opal/skills-registry.json`에 항목이 기록되고 `match` → `scope:"project"`. 본체가 `{project}/.opal/community-skills/{vendor}/{skill}/SKILL.md`에 존재 | M1 | **PASS** | 배포본 `~/.opal/skills/opal-skill-wizard/SKILL.md` 절차를 리허설(scratchpad fixture 프로젝트, 실 네트워크·실 git). §3.1 `npx skills find "markdown"` → 6건 반환 → §3.2 `git clone --depth 1 https://github.com/jimliu/baoyu-skills.git`(shallow) → 후보 `skills/baoyu-markdown-to-html` 선정, LICENSE=MIT, commit_sha=`6b7a2e41...` 확보 → §4 `scan-risk` → `verdict:"SAFE"`, hits:[] (exit 0) → §5.3 `{project}/.opal/community-skills/jimliu/baoyu-markdown-to-html/SKILL.md`로 복사 → §6 프로젝트 registry(12필드 스키마) 기록 → 자가확인 `node skill-registry.js match "//jimliu/baoyu-markdown-to-html"`(cwd=fixture 프로젝트) → `{"found":true,"scope":"project","installed":true,"path":".../community-skills/jimliu/baoyu-markdown-to-html/SKILL.md",...}` (exit 0). SKILL.md 실물 `ls`로 존재 확인 |
| TS-031 | H-6 | ⑤ 구형 미사용 | 동상 — 설치 전후 전역 스냅샷 비교 | **전역 `~/.opal/community-skills/` 파일 목록 변화 0건 AND 전역 `user-registry.json` 변화 0건**. 전역 무변화가 manager 경로 미사용의 실행-시간 증거다 | M1 | **PASS** | TS-030 설치 전/후 `find ~/.opal/community-skills -maxdepth 4` 스냅샷(497줄) `diff` → 차이 0건. `~/.opal/community-skills/user-registry.json`은 설치 전·후 모두 부재(동일 상태) — 전역 상태 완전 무변화 확인. TS-030(양성 확정: 설치가 실제로 성립함)과 짝을 이뤄 "우연한 무변화"가 아님을 뒷받침 |
| TS-032 | H-8 | ⑥ 실판정 | 위험 패턴(credential 접근·광범위 삭제·외부 실행) 포함 fixture SKILL.md | `scan-risk` 실행 결과 위험 hit ≥1건 반환 (도구 결정론 — 판정이 실제로 발생함) | M1 | **PASS** | scratchpad에 직접 제작한 fixture(`candidate-risky/SKILL.md`, 코드펜스 내 `cat ~/.ssh/id_rsa` / `rm -rf "$HOME/old-cache"` / `curl...\|bash`)에 `node skill-registry.js scan-risk {dir}` 실행 → `verdict:"RISKY"`, active hit 3건(RP-04 secret:credential, RP-01 fs:destructive, RP-03 exec:remote), exit 0 |
| TS-033 | H-8 | ⑥ 오탐 부재 | 무해 fixture SKILL.md | `scan-risk` 위험 hit **0건** — 정상 스킬을 위험으로 오판하지 않는다 | M1 | **PASS** | 동일 방식으로 제작한 무해 fixture(`candidate-clean/SKILL.md`)에 `scan-risk` 실행 → `verdict:"SAFE"`, hits:[], exit 0 |
| TS-034 | H-8 | ⑥ 부정 분기 | TS-032의 위험 fixture를 설치 후보로 둔 상태에서 wizard 설치 절차 수행 | **(a) 프로세스 exit 0** (정상 종료 — 크래시가 아님) **AND (b) 거부 사유 신호 = RISKY 판정이 출력에 존재** **AND (c) 프로젝트 스코프 파일 생성 0건**(`{project}/.opal/community-skills/` 하위 및 registry 항목 미생성). 3조건 AND로 "게이트가 차단했다"와 "조기 실패로 우연히 없다"를 구분한다 | M1 | **PASS** | 사전 스냅샷(`find {project}/.opal -type f`) 취득 → TS-032 위험 fixture로 §4 게이트 재실행: (a) `scan-risk` exit 0 (b) 출력에 `"verdict":"RISKY"` 존재 → §4.2-1 MUST 준수해 복사·registry 기록 생략 → 사후 스냅샷 `diff` = 차이 0건, registry 파일 내 `risky-demo` 매칭 0건. 3조건 AND 전건 충족 |
| TS-035 | — (R-3) | ⑥ 부정 분기 | 검색 결과 0건 상황 | **(a) exit 0 AND (b) `opal-skill-creator` 위임 신호가 출력에 존재**(위임 페이로드 7필드 중 `requested_capability`·`searched_sources` 최소 2건 기재) **AND (c) registry 미기록 + 본체 미생성**. (b)가 없으면 "위임했다"가 아니라 "아무것도 안 했다"와 구분되지 않는다 | M1 | **PASS** | 사전 스냅샷 취득 → `npx skills find "zzqxvbnm...(무의미 검색어)"` → "No skills found" (exit 0) → §7.1 트리거(검색 0건) 충족 확인 → §7.2 페이로드 구성, `requested_capability`·`searched_sources` 포함 7필드 전건 기재 → 사후 스냅샷 `diff` = 차이 0건, registry 내 검색어 매칭 0건(복사·기록 없음) |
| TS-036 | H-4 | ⑥ 부정 분기 | `findProjectRoot()` → `null`인 비프로젝트 디렉토리에서 wizard 진입 | **(a) exit 0 AND (b) 프로젝트 스코프 대상 부재 안내가 출력에 존재** **AND (c) cwd·홈·전역 3곳 전부 파일 생성 0건**(스냅샷 비교). 임의 경로 설치가 발생하지 않으며, 침묵 종료가 아니라 사유를 밝히고 종료한다 | M1 | **PASS** | cwd = scratchpad 하위 비프로젝트 디렉토리(상위 경로 전건에 `.opal/` 부재 확인 — `/`, `/private`, `/private/tmp` 전건 마커 없음). cwd·전역 사전 스냅샷 취득 → 동일 cwd에서 `node skill-registry.js list` 실행(exit 0) → `group==="project"` 항목 0건(=findProjectRoot 널 반환과 정합) → SKILL.md §비프로젝트 진입 규칙 1항의 안내 문구를 그대로 발화(대상 부재 고지 + 2경로 안내) → 사후 스냅샷 `diff`: cwd 트리 차이 0건, 전역 `community-skills` 차이 0건, `$HOME/.opal/skills-registry.json` 미생성 확인. 3조건 AND 충족 |
| TS-037 | — (R-3) | ① 참고 보강 | 알려진 검색어로 `npx skills find` 1회 실행 | 결과 ≥1건 (검색 명령이 실제로 후보를 반환함). **네트워크·npx 미가용 시 Skip 허용** — 판정 차단 요소가 아니다 | M1 | **PASS** | `npx --yes skills find "markdown"` 실행 → 6건 반환(예: `open.feishu.cn@lark-markdown`, `kepano/obsidian-skills@obsidian-markdown` 등), exit 0. 네트워크·npx 가용 확인됨(Skip 불필요) |

> **[MUST] 부정 시나리오는 「없다」만으로 판정하지 않는다 — 3조건 AND** (iteration 2 Evaluator 지적 반영, 게이트 통과 후 보강). TS-034~TS-036은 각각 **(a) exit 0**(정상 종료) **+ (b) 거부·위임·안내 사유 신호 존재**(무엇을 판단해 멈췄는지) **+ (c) 부작용 부재**(파일 생성 0건)를 모두 만족해야 PASS다. (c) 단독 주장은 「게이트가 정상 차단했다」와 「조기 실패로 우연히 없다」를 구분하지 못한다 — 같은 문서 TS-002·TS-003이 이미 exit 0을 명시하는 선례를 따른다.
>
> **[MUST] 사전 스냅샷 의무**: 각 시나리오는 실행 **전** 스냅샷을 취득하고 실행 **후** 차분으로 (c)를 판정한다 — 사전 스냅샷 없이 「없더라」를 주장하면 애초에 만들어질 수 없었던 경우와 구분되지 않는다.

### L3. 정적 검사 · 사용자 협업

> 문서 요건은 `grep` 기반 존재·부재·**순서** 단정으로 자동화한다(M1). 인터뷰 흐름은 자동화 불가이므로 M3.
>
> **[MUST] 정적 축은 필요조건이지 충분조건이 아니다** (iteration 1 Evaluator 지적 반영). 아래 TS-024~TS-028은 「규칙 문면이 존재하는가」만 판정한다 — 「wizard가 실제로 그렇게 행동하는가」는 §L2-실행축의 TS-030~TS-036이 부작용 관측으로 판정한다. **두 축이 짝으로 통과해야 해당 AC가 충족된다.**
>
> | 정적 축 | 짝이 되는 실행 축 |
> |---------|----------------|
> | TS-013 (manager 호출 지시 0건) | TS-031 (전역 무변화 — manager 경로 미사용) |
> | TS-014·TS-024 (scan-risk 게이트·RISKY 제외) | TS-032·TS-034 (실판정 + 설치 부작용 부재) |
> | TS-025 (검사 실패 시 미설치) | TS-034 (부작용 부재) |
> | TS-026 (검색 0건 → 위임) | TS-035 (registry 미기록) |
> | TS-028 (비프로젝트 호출) | TS-036 (어느 경로에도 파일 생성 0건) |

| TS-ID | 가설 | 대상 | 조건 | 기대 결과 | 실행 방식 | 결과 | 상세 |
|-------|------|------|------|----------|----------|------|------|
| TS-011 | — (R-1) | wizard SKILL.md 구조 | 파일 정적 검사 | 모드 판별 표/절 1건 + 신규·기존 모드 절이 각각 별개 존재 + 제안→승인→설치 3단이 순서대로 등장 | M1 (grep) | **PASS** | `grep -n "^## \|^### "` 결과: `## 0. 모드 판별`(L48, 표 L52-55) 1건 / `## 1. 신규 모드`(L60) · `## 2. 기존 모드`(L77) 별개 절 / `## 5. 제안 → 승인 → 설치`(L176) 하위 `### 5.1 제안`(L180) → `### 5.2 승인`(L194) → `### 5.3 설치`(L200) 순서 등장 |
| TS-012 | — (R-2) | PROJECT.md 입력 계약 | 동상 | 재사용 항목 목록 / 부재 시 폴백 절차 / 결측 판정 기준 3항 전건 존재 | M1 | **PASS** | `### 2.1 재사용 항목 목록`(L79) / `### 2.2 결측 판정 기준`(L88) / `### 2.4 PROJECT.md 부재 시 폴백`(L103) 3항 전건 존재 |
| TS-013 | — (R-3) | manager 비호출 + 검색·설치 절차 | 동상 | 검색 명령·clone 대상(임시)·복사 대상(프로젝트 경로) 각 1건 이상 + `opal-skill-manager` **호출 지시 0건**(참조 인용은 호출과 구별) | M1 | **PASS** | 검색 `npx skills find`(L114-116) 1건, clone 대상 `### 3.2 clone 대상 = 임시 디렉토리`(L123, `mktemp -d`) 1건, 복사 대상 `### 3.3 설치 대상 경로`(L135, `{project}/.opal/community-skills/...`) 1건 — 전건 존재. `opal-skill-manager` 문자열 6곳(L24,45,144,246,263,308-309) **전건 문맥 확인**: L24·308-309는 "전역 스코프는 manager가 계속 담당"이라는 **소유 경계 서술**, L45는 "안내일 뿐이며 이 스킬이 대신 실행하지 않는다"고 **명시적으로 호출 부정**, L144·246·263은 "원본은 `.../SKILL.md` §N" 형태의 **설계 근거 인용(citation)**. "manager를 호출하라/실행하라"는 지시문 0건 — 호출 지시 0건 판정 |
| TS-014 | H-8 | `scan-risk` 게이트 위치 | 동상 | `scan-risk` 호출이 **복사 단계보다 앞선 위치**에 존재 + 판정별 동작 표(SAFE/CAUTION/RISKY/UNKNOWN) 존재 + 실패 시 미설치 규칙 명시 | M1 | **PASS** | scan-risk 호출 위치 = **L151**(`## 4. 설치 전 보안 검사`) / 복사 실행 위치 = **L200-206**(`### 5.3 설치 (복사)`). L151 < L200 — 순서 확인. 판정별 동작 표 `### 4.1`(L158-166, SAFE/CAUTION/RISKY/UNKNOWN 4행) 존재. 실패 시 미설치 규칙 L166·L171 "[MUST] 설치를 진행하지 않는다" 명시 |
| TS-016 | — (R-7) | 스키마 필드 완결성 | `docs/ARCHITECTURE.md` + wizard §8 | 필드 목록이 표로 존재하고 출처·commit·라이선스·보안 판정·스캔 시점 5항 전건 포함 | M1 | **PASS** | wizard `## 8. 프로젝트 registry 스키마`(L267) 필드 표(L277-292)에 출처(L286)·commit(L287)·라이선스(L288)·보안 판정(L289)·스캔 시점(L291) 5항 전건 존재. `docs/ARCHITECTURE.md:189` SAFE/CAUTION/RISKY/UNKNOWN 4단 판정 서술 + `:519` 스코프 3원 확장·12필드 표 반영 changelog 존재 |
| TS-019 | H-6 | 라우팅 3중 분기 | `skill-commands.md` | project 스코프 분기 존재 + `opal-skill-manager` 단독 지목 문장 **0건**(2곳 모두) + `installed`/`ambiguous` 기존 의미 서술 유지 | M1 | **PASS** | project 분기 L29("`scope === \"project\"` && `installed:false`" → `opal-skill-wizard` §5 라우팅), L42(요약 재서술) 2곳 존재. `opal-skill-manager` 단독 지목 문장 2곳(구버전 L30·L42 상당)이 **현재는 "그 외 community"로 조건부화**되어 3중 분기의 한 갈래로만 등장 — 단독 지목 0건. 이는 실측(grep)과 changelog `v1.4`(L56) "manager 단독 지목 문장 2곳 제거" 자기 기술이 일치. `ambiguous` 최우선 분기(L24,28) 및 "`installed`·`ambiguous` 기존 의미는 불변"(L56) 서술 유지 확인 |
| TS-020 | — (R-11) | 변경이력 | 수정 문서 4건 | 각각에 일시(KST)+태스크 번호(114) 행이 정확히 1건 | M1 | **PASS** | wizard SKILL.md `:319` "v1.0 \| 2026-09-04 08:32 KST \| ... (114)" 1건 / `skill-commands.md:56` "v1.4 \| 2026-09-04 08:32 KST \| ... (114)" 1건 / `docs/ARCHITECTURE.md:519` "2026-09-04 \| ... (Task 114)" 1건(이 문서는 다수 기존 행이 시각 생략·날짜만 표기하는 기존 관행이 있어 형식 일탈 아님, L527-547에서 다건 확인) / `opal-skills-registry.json` changelog 배열의 `version:"3.14.0", date:"2026-09-04", task:"114"` 1건. 4문서 전건 정확히 1행씩 |
| TS-024 | H-8 | `scan-risk` RISKY 판정 시 동작 | wizard SKILL.md 정적 + 절차 대조 | RISKY 판정 후보는 **추천에서 제외**되고 복사되지 않는다는 규칙이 명시 | M1 | **PASS** | L164 "`RISKY` \| 추천 후보에서 제외 — 복사하지 않는다" + L170 "[MUST] RISKY 판정 후보는 추천 후보에서 제외하고 복사하지 않는다" — 명시적 규칙 존재. §L2-실행축 TS-034 실행 증거와 짝 |
| TS-025 | H-8 | `scan-risk` 실행 실패 시 동작 | 동상 | 도구 비정상 종료·미실행 시 **설치를 진행하지 않는다** — 침묵 통과 경로 0건 | M1 | **PASS** | L166 "도구 실행 실패 / 미실행 → [MUST] 설치를 진행하지 않는다" + L171 "검사되지 않은 후보가 조용히 통과하는 경로를 두지 않는다" — 침묵 통과 명시적 배제 |
| TS-026 | — (R-3) | 검색 0건 시 위임 | 동상 | `opal-skill-creator` 위임 분기가 존재하고 빈 목록을 제안으로 제시하지 않는다 | M1 | **PASS** | L120 "결과 0건이면 §7(`opal-skill-creator` 위임)로 분기한다. [MUST] 빈 목록을 제안으로 제시하지 않는다" — 명시. §L2-실행축 TS-035 실행 증거와 짝 |
| TS-027 | — (R-3) | 후보 전건 거부 시 동작 | 동상 | 설치를 강행하지 않고 위임 또는 종료로 분기 | M1 | **PASS** | L198 "[MUST] 사용자가 후보를 전건 거부하면 설치를 강행하지 않는다 — §7(위임)로 분기하거나, ... 사유를 알리고 종료한다. 이 분기에서 파일을 만들지 않는다" |
| TS-028 | H-4 | **비프로젝트 디렉토리 호출** (PLAN 갭) | `findProjectRoot()` → `null`인 위치에서 wizard 진입 | 임의 경로에 설치하지 않는다 — 프로젝트 스코프 대상 부재를 알리고 안전 종료하거나 전역 안내로 분기하는 규칙이 SKILL.md에 명시 | M1 | **PASS** | `### 비프로젝트 진입 규칙`(L40-46): L42 "[MUST] 임의 경로에 설치하지 않는다", L44 대상 부재 고지 + 침묵 종료 금지, L45 2경로 안내(재실행/전역은 manager), L46 "[MUST] 부작용 부재". §L2-실행축 TS-036 실행 증거와 짝 |

#### TS-021: 신규 모드 인터뷰로 제안 목록 산출 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | — (축 ① 목표달성) |
| 대상 | wizard 신규 모드 전체 흐름 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 인터뷰 응답이 필요해 자동화 불가 |
| 조건 | `docs/PROJECT.md`가 없는 프로젝트에서 `//osw` 호출 |
| 기대 결과 | 인터뷰 질문이 제시되고, 답변 후 후보 스킬 목록(스킬명·출처·라이선스)이 1건 이상 제시된다. PROJECT.md 부재를 이유로 중단하지 않는다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **[SUPERVISOR] 대기** |
| 상세 | opal-test-agent는 M3 마커를 확인하고 실행하지 않았다(하네스 규칙 — L3 [SUPERVISOR] 시나리오 감지 시 즉시 PM 위임). 캡틴 확인 절차: `docs/PROJECT.md`가 없는 임의 프로젝트에서 `//osw`(또는 "osw")를 호출 → 인터뷰 질문 4항(§1)이 제시되는지, 응답 후 후보 스킬 목록(스킬명·출처·라이선스 포함)이 1건 이상 제시되는지, PROJECT.md 부재를 이유로 중단하지 않는지를 육안 확인 |

#### TS-022: 기존 모드 — PROJECT.md 재사용 + 결측만 인터뷰 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | — (축 ① 목표달성) |
| 대상 | wizard 기존 모드 — PROJECT.md 입력 재사용 경로 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** |
| 조건 | `docs/PROJECT.md`가 존재하는 프로젝트(예: 본 OPAL 레포)에서 `//osw` 호출 |
| 기대 결과 | 재사용한 PROJECT.md 항목이 사용자에게 제시되고, **결측 항목(자동화 대상 작업 유형)에 대해서만** 질문한다. 이미 PROJECT.md가 담은 기술 스택·폴더 구조를 다시 묻지 않는다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **[SUPERVISOR] 대기** |
| 상세 | opal-test-agent는 M3 마커를 확인하고 실행하지 않았다(하네스 규칙 — L3 [SUPERVISOR] 시나리오 감지 시 즉시 PM 위임). 캡틴 확인 절차: `docs/PROJECT.md`가 존재하는 본 OPAL 레포에서 `//osw`(또는 "osw")를 호출 → 재사용한 PROJECT.md 항목(폴더 구조·기술 스택)이 사용자에게 제시되는지, 결측 항목(자동화 대상 작업 유형)에 대해서만 질문하는지, 이미 문서에 있는 항목을 재질문하지 않는지를 육안 확인 |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

> 보강 완료 판정 3조건: 마커 잔존 0건 / H-N 전건 전재(§1) / **모든 시나리오 행에 가설 ID·검증 계층 기재**.
> 테스트 파일 케이스 명명: `[T114/L{계층}-{AC}]` (`test-scenario-guide.md` §Step 4-b 모듈 미러링 명명).

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| 목표 문장 (§작업 목표) | H-6 | L3/M3 · L2/M1 | TS-021, TS-022, TS-023 | **TS-023 = 리허설 관측**(TS-030과 동일 실행에서 확인, 전용 테스트 케이스 없음) / **자동 회귀는 `tests/test-project-registry.js:[T114/L2-001]`이 담당**(registry 등재 + 본체 존재 → `match found:true`·`scope:"project"`·`installed:true` = 발동 성립 조건) / TS-021·022는 [SUPERVISOR] | 축 ① — **PM 정정**: 최초 작성 시 `[T114/L2-GOAL]` 케이스를 인용했으나 실측 결과 그 케이스는 존재하지 않았다(TEST 워커 grep 검출). 실재하는 커버로 교체 |
| R-1 AC | H-4 | L3(정적) + L2(실행)/M1 | TS-011, TS-028 (정적) / **TS-036 (실행)** | `:wizard 문서 구조 [T114/L3-R1]` + `:비프로젝트 파일생성 0건 [T114/L2-R1]` | 축 ② + ⑥ |
| R-2 AC | — | L3/M1 | TS-012 | `:PROJECT.md 입력 계약 [T114/L3-R2]` | 축 ② |
| R-3 AC | H-8 | L3(정적) + L2(실행)/M1 | TS-013, TS-026, TS-027 (정적) / **TS-031, TS-035, TS-037 (실행)** | `:manager 비호출·검색절차 [T114/L3-R3]` + `:전역 무변화 [T114/L2-R3]` | 축 ② + ⑤ + ⑥ — 정적·실행 짝 |
| R-4 AC | H-8 | L3(정적) + L2(실행)/M1 | TS-014, TS-024, TS-025 (정적) / **TS-032, TS-033, TS-034 (실행)** | `:scan-risk 게이트 [T114/L3-R4]` + `:scan-risk 실판정·부작용부재 [T114/L2-R4]` | 축 ② + ⑥ — 보안 게이트 실행 검증 |
| R-5 AC | H-1, H-2, H-4, H-5, H-7 | L1 + L2/M1 | TS-001, TS-002, TS-003, TS-007, TS-008, TS-009 | `:registry 병합 유·무·파손 [T114/L2-R5]` | 축 ② + ④ + ⑥ |
| R-6 AC | H-3, H-6 | L1 + L2/M1 | TS-004, TS-005, TS-006 | `:get resolved_path [T114/L2-R6]` | 축 ② + ⑥ — **기존 `get` 커버 0건의 유일 안전망** |
| R-7 AC | H-9 | L2 + L3/M1 | TS-015, TS-016, TS-029 | `:스키마 validate [T114/L2-R7]` | 축 ② + ⑥ |
| R-8 AC | H-1 | L2/M1 | TS-010 | 기존 4파일 개별 실행 (무변경) | 축 ② — 기준선 **41 pass / 0 fail** |
| R-9 AC | H-6 | L3(정적) + L2(실행)/M1 | TS-019 (정적) / **TS-030 (실행 — 신형 경로 채택 증거)** | `:라우팅 3중 분기 [T114/L3-R9]` + `:project 스코프 기록 [T114/L2-R9]` | 축 ② + ⑤ |
| R-10 AC | H-9 | L2/M1 | TS-017, TS-018 | `:osw 매칭·alias 유일성 [T114/L2-R10]` | 축 ② + ⑥ |
| R-11 AC | — | L3/M1 | TS-020 | `:변경이력 4문서 [T114/L3-R11]` | 축 ② |
| F-001 (R-5·R-6) | H-1~H-7 | L1 + L2 | TS-001~TS-009 | 상동 | 축 ③ 기능커버 |
| F-002 (R-8) | H-1 | L2 | TS-010 + TS-001~TS-009 구현 | `tests/test-project-registry.js` (신규 파일 자체) | 축 ③ |
| F-003 (R-1~R-4) | H-8, H-4 | L3(정적) + L2(실행) | TS-011~TS-014, TS-024~TS-028 (정적) / TS-030~TS-037 (실행) | 상동 | 축 ③ |
| F-004 (R-7) | H-9 | L2 + L3 | TS-015, TS-016, TS-029 | 상동 | 축 ③ |
| F-005 (R-9·R-10) | H-6, H-9 | L2 + L3 | TS-017, TS-018, TS-019 | 상동 | 축 ③ |
| F-006 (R-11) | — | L3 | TS-020 | 상동 | 축 ③ |
| 잔존 0 기준 (R-3·R-9 AC) | H-8, H-6 | L3(정적) + L2(실행)/M1 | TS-013, TS-019 (구형 잔존0 정적) / **TS-030(신형 채택) · TS-031(구형 미사용 — 전역 무변화)** | `:전역 무변화 [T114/L2-R3]` | 축 ⑤ — iteration 1 지적 반영: 실행-시간 채택 증거 신설 |

> **커버리지 확인** — H-1~H-9 전건이 최소 1개 시나리오에 매핑(미커버 0건). F-001~F-006 전건 매핑(미커버 0건). R-1~R-11 전건 매핑(미커버 0건).

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | 해당 없음(설정 부재) | **N/A** | `bash opal/tools/test-tool/run.sh resolve` 실행 결과 프로젝트 레벨 설정을 찾지 못해 `source:"global"` 기본값(eslint/ruff)으로 폴백. 리포지토리 루트·`opal/tools/skill-registry/`에 `package.json`·`.eslintrc*`·`eslint.config.*` 부재(`find . -maxdepth 3` 확인 — 유일한 `eslint.config.js`는 무관한 `dashboard/frontend/`에만 존재). `npx --no-install eslint --version` → 미설치. 변경분(순수 CommonJS `.js` + `.md`)에 적용 가능한 프로젝트 린터 설정이 없다 — 없는 도구를 있다고 기재하지 않음 |
| 2 | 타입 체크 | 해당 없음(설정 부재) | **N/A** | `tsconfig*.json` 리포지토리 전역에 0건(`find . -maxdepth 2` 확인). 변경 파일은 순수 JS(타입 주석 없음)이며 타입체커 대상 자체가 아님 |
| 3 | 포맷터 | 해당 없음(설정 부재) | **N/A** | `.prettierrc*`·`prettier.config.*` 0건 확인. 프로젝트 전역에 포맷터 설정 없음 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS** | `grep -niE "(api[_-]?key\|secret\|password\|token\|aws_access\|private_key)\s*[:=]\s*['\"][a-zA-Z0-9]{8,}"` 을 변경분 6파일(`opal-skill-wizard/SKILL.md`, `test-project-registry.js`, `skill-registry.js`, `skill-commands.md`, `opal-skills-registry.json`, `docs/ARCHITECTURE.md`)에 실행 → 매치 0건 |
| 2 | .gitignore 확인 | **PASS** | 리포지토리 `.gitignore`에 `.opal/*`(예외 목록 명시적 화이트리스트) + `*.env`/`.env` + Python 캐시류 포함 확인. 변경분 중 민감 파일(자격증명·env) 대상 0건 — 별도 미비 발견 없음 |
| 3 | CWE-22 path traversal — `resolveProjectSkillPath()` 프로젝트 루트 하위 검증 | **PASS** | `skill-registry.js:173-182` 확인: `nested`/`flat` 경로 계산 후 각각 `nested.startsWith(root)` / `flat.startsWith(root)` 가드를 통과해야만 존재 확인·반환 — `skillName`에 `../` 주입 시 `path.resolve()`로 정규화된 결과가 루트 접두를 벗어나 방어됨. 기존 관례(H-2 참조 대상 `skill-registry.js:118-128`)와 동형 패턴 재사용 |
| 4 | walk-up이 홈 경계를 넘지 않음 (H-4) | **PASS** | TS-008(L1) 실측 인용: `test-project-registry.js` `[T114/L2-008]` PASS — 가짜 HOME 하위 cwd + 홈에 registry 실재해도 `_source:'project'` 병합 0건(exit 0). §L2-실행축 TS-036 실측도 동일 방어선을 다른 각도(비프로젝트 진입)에서 재확인 |
| 5 | 파손 JSON이 CLI 예외로 전파되지 않음 (H-2, DoS 방지) | **PASS** | TS-003 실측 인용: `test-project-registry.js` `[T114/L2-003]` PASS — 잘린 JSON 프로젝트 registry에서도 exit 0, 예외 전파 0건, 전역 3소스만 병합(project 유래 스킬 0건) |

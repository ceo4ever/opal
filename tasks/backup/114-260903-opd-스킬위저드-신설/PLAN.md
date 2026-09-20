# PLAN: opal-skill-wizard 신설 — 프로젝트 적합 스킬 제안 + 프로젝트 스코프 설치

> 작성일: 2026-09-04 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 6개)
> 산출: PLAN.md (TEST-SCENARIO.md는 PM이 별도 작성 — self-confirming 방지)

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 제안 대상은 커뮤니티 스킬(skills.sh) 한정, 미발견 시 `opal-skill-creator` 위임 | 유효 | 위임 페이로드 7필드가 creator 입력과 1:1 대응 (`opal/skills/opal-skill-manager/SKILL.md:92-102`) |
| [결정] 설치 대상은 프로젝트 스코프 신설(전역은 manager 유지) | 유효 | - |
| [결정] wizard는 `opal-skill-manager`를 호출하지 않는다 | 유효 | - |
| [결정] 기존 프로젝트 분석은 `docs/PROJECT.md` 재사용 + 결측만 인터뷰 | 유효 | 재사용 가능 항목·결측 항목 실측 확인 (→ ANALYSIS §7 Q9) |
| [결정] 설치 전 사전 검사는 `skill-registry.js scan-risk` 직접 호출 | 유효 | 서브명령 실존 (`opal/tools/skill-registry/skill-registry.js:912`) |
| [결정] 프로젝트 설치 이력 registry 신설 | 유효 | - |
| [결정] 발동 경로는 OPAL 레지스트리 + `//` 커맨드, 플랫폼 네이티브 디렉토리 미사용 | 유효 | `opal/core/references/harness/skill-commands.md:11-24` |
| [결정] 착수 트랙은 `//opd --agentic` | 유효 | - |
| [사실] 대가는 플랫폼 네이티브 description 자동 트리거 불가 | 유효 | `scripts/install-mac.sh:1723-1751` (네이티브 skills/ 레거시 지정) |

> `사실오류` 강등 0건. 9개 항목 전건 재도출 없이 판정만 수행했다 (op-dev-plan SKILL.md §확정 입력 소비 규약).

---

## 0. PLAN 결정 확정 (ANALYSIS §8 「PLAN 결정 필요」 6건)

> ANALYSIS.md §8 「PLAN 결정 필요」 표의 6건을 전건 확정한다. 미확정 이월 0건.
> 공통 판단 축: [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." / [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."

### DEC-1. 프로젝트 루트 판별 방식 → **cwd 기점 walk-up 탐색 (홈 경계 정지)**

| 구분 | 안 | 판정 |
|------|-----|------|
| 선택 | ① cwd 기점 **walk-up** — `process.cwd()`부터 부모 방향으로 `.opal/skills-registry.json` 존재 여부를 검사, 최초 발견 디렉토리를 프로젝트 루트로 확정 | **채택** |
| 탈락 | ② 명시적 인자 주입(`--project-root=`) | 탈락 |
| 탈락 | ③ 환경변수(`OPAL_PROJECT_ROOT`) | 탈락 |

- **선택 근거**: 배선 비용 0 — 호출부(`match`/`get`/`list`/`validate` 4개 CLI 진입점, `harness/skill-commands.md` `//` 라우팅 절차, `dashboard/backend/adapters/skill_adapter.py:47`)를 **한 곳도 고치지 않는다**. [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." — ②는 5개 이상 호출부를 인접 개선하게 만든다.
- **H-5(하위 디렉토리 호출 시 실패) 처리**: walk-up 도입이 곧 H-5의 해소책이다. ANALYSIS가 지적한 실패 모드는 "`process.cwd()` 단일 지점만 검사"에서 나오며(`opal/tools/skill-registry/skill-registry.js:83-84`), 상향 탐색으로 `dashboard/backend/`에서 호출해도 리포지토리 루트의 `.opal/skills-registry.json`에 도달한다. **walk-up 도입 여부: 도입한다.**
- **탐색 종료 조건 3종 (모두 [MUST])**:
  1. `.opal/skills-registry.json`을 발견하면 즉시 그 디렉토리를 반환한다.
  2. `os.homedir()`에 도달하면 **홈 디렉토리 자체는 검사하지 않고 중단**하고 `null`을 반환한다 — 전역 `~/.opal/`을 프로젝트 스코프로 오인하는 것을 구조적으로 차단한다 (전역은 `loadUserRegistry()`가 이미 담당, `:118-128`).
  3. 파일시스템 루트(`path.dirname(dir) === dir`)에 도달하면 중단하고 `null`을 반환한다. 추가로 상한 깊이 **32단**을 두어 심볼릭 루프에서 무한 순회를 막는다.
- ③ 탈락 근거: ANALYSIS Q1이 지적한 "값 부재/오염 시 조용히 전역만 병합되는 실패 모드" — [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." 환경변수는 전파 보장이 규약(산문)에 의존한다.

### DEC-2. 프로젝트 registry 파일 경로·파일명 → **`.opal/skills-registry.json` 단일 파일 + 본체 `.opal/community-skills/{vendor}/{skill}/`**

| 구분 | 안 | 판정 |
|------|-----|------|
| 선택 | ① registry = `{project}/.opal/skills-registry.json`, 스킬 본체 = `{project}/.opal/community-skills/{vendor}/{skill}/SKILL.md` | **채택** |
| 탈락 | ② `{project}/.opal/community-skills/user-registry.json` 전역 미러링 | 탈락 |

- **선택 근거 (a) 계층 정합**: 프로젝트 `.opal/` 최상위는 이미 `code-scan.json`·`worktree.json`·`MEMORY.json`처럼 **역할별 단일 JSON**을 두는 계층이다 (→ ANALYSIS §7 Q2 `ls .opal/` 실측). `skills-registry.json`은 이 관례에 그대로 편입된다.
- **선택 근거 (b) 스코프 혼동 차단**: ②는 전역 파일명(`user-registry.json`)과 **완전히 동일**하여 사람이 grep·경로 축약 표기에서 스코프를 혼동한다(ANALYSIS Q2가 명시한 단점). ①은 파일명 자체가 다르므로 혼동 표면이 없다.
- **선택 근거 (c) 본체 디렉토리는 전역과 동형**: `.opal/community-skills/{vendor}/{skill}/SKILL.md`는 전역 설치 위치(`~/.opal/community-skills/{vendor}/{skill}/SKILL.md`, → D-11 `docs/ARCHITECTURE.md` §커뮤니티 스킬)와 **루트만 다른 동형 구조**다. 따라서 경로 해석 로직이 `resolveCommunitySkillPath()`(`:100-109`)의 vendor 중첩 규칙을 그대로 이식할 수 있고, 신규 알고리즘 설계가 없다.
- **install 안전성**: `scripts/install-mac.sh`는 프로젝트 상대 `.opal/`에 어떤 쓰기도 하지 않는다(전건 grep 0건 — → ANALYSIS §8 확정값). 두 후보 모두 install 재실행에 안전하나, 이는 ①의 배제 근거가 되지 못하므로 (a)(b)(c)로 확정한다.
- **[MUST] 이 결정은 전역 경로를 변경하지 않는다** — [MUST] `opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙: "커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다. 플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다." wizard는 프로젝트 스코프를 **추가**할 뿐 전역 규칙 문장을 개정하지 않는다.

### DEC-3. 전역-프로젝트 동일 `name` 충돌 우선순위 → **현행 override 방향 연장 (프로젝트 최우선)**

- **선택**: `loadAllSkills()`의 병합 순서를 `main → community → user → **project**`로 두어, 현행 규칙("동일 `name`은 나중에 병합되는 소스가 우선", `opal/tools/skill-registry/skill-registry.js:137-144`)의 자연 귀결로 프로젝트가 최우선이 된다.
- **탈락안**: 별도 명시적 우선순위 테이블/가중치 필드 도입 — [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." 신규 규칙 축은 현행 override 루프와 이중 규칙이 되어 유지 비용만 늘린다.
- **정당화**: 프로젝트 스코프는 사용자가 **그 프로젝트에 한정해 의도적으로 설치한 것**이므로, 전역보다 좁고 명시적인 의도를 우선하는 것이 override 방향과 의미상 일치한다.
- **서브명령별 영향 (4건 전건 명시)**:

| 서브명령 | 영향 | 추가 구현 필요 여부 |
|---------|------|------------------|
| `match` | `matchByAlias`/`matchByTriggers`가 병합 배열을 그대로 소비하므로 override가 자동 반영된다. 단 `matchCommand()`는 `isCommunitySkill()` 단일 분기이므로 `_source==='project'` 응답 분기를 **추가해야 한다**(F-001) — 그렇지 않으면 project 스킬이 main 분기로 떨어져 `resolveFirstPath(skill.paths)`(`paths` 부재 → null 폴백)를 타게 된다 | **필요** |
| `get` | `skills.find()`가 병합 배열의 첫 매치를 반환하므로 override는 자동 반영. 단 경로 필드는 DEC-5에서 별도 처리 | 필요 (DEC-5) |
| `list` | override로 전역 동명 항목이 배열에서 사라진다 → 섀도잉 가시성 이슈. DEC-4에서 처리 | 불필요 (DEC-4로 이관) |
| `validate` | override된 병합 배열만 검사하므로 가려진 전역 원본은 검증 대상에서 빠진다. **이는 기존 user-registry override에서 이미 성립하던 한계의 상속이며 신규 결함이 아니다**(→ ANALYSIS §7 Q3) | 불필요 |

### DEC-4. `list` 응답의 섀도잉된 전역 항목 표시 → **숨김 유지 (현행 동작 연장), 신규 필드 미도입**

- **선택**: 현행처럼 override된 전역 항목은 `list` 결과에서 노출하지 않는다.
- **탈락안**: `shadowed_by`/`shadows` 신규 필드 노출 — TASK.md §완료기준 8항 어디에도 섀도잉 가시성 요구가 없다. [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
- **회귀 안전성 확인**: `list` 최상위 반환 타입은 배열로 유지된다 → 유일한 코드 레벨 소비자 `dashboard/backend/adapters/skill_adapter.py`가 최상위 타입만 분기하므로(`:53-75`) 회귀 표면 0 (→ ANALYSIS §4-5).
- **부수 확인**: `listCommand()`의 `--group=community` 필터는 `_source === 'community'` 단일 조건이므로(`:349-351`) 신규 `_source: 'project'` 항목은 이 필터에서 자연 제외된다 — 필터 코드 무변경 (ANALYSIS H-7). `--group=project` 신규 옵션은 요구되지 않았으므로 **도입하지 않는다**.
- **이월**: 섀도잉 가시성은 후속 개선 제안으로 분리한다 (§9 R-2).

### DEC-5. `get` 서브커맨드 경로 계산 계약 변경 범위 → **additive 신규 필드 `resolved_path` (기존 필드 전건 불변)**

- **선택**: `getCommand()`(`:327-340`)의 기존 반환(`{...rest, group}` — raw passthrough)을 **한 필드도 제거·변경하지 않고**, `resolved_path` 1개 필드만 추가한다.

| 스킬 `_source` | `resolved_path` 산출 | 기존 필드 |
|---------------|---------------------|----------|
| `main` | `resolveFirstPath(skill.paths)` (`:229-253`) | `paths` 배열 그대로 유지 |
| `community` | `resolveCommunitySkillPath(skill.name)` (`:100-109`) | 기존 raw 필드 유지 |
| `project` | `resolveProjectSkillPath(skill.name)` (신규, DEC-2 경로) | 등재 raw 필드 유지 |

- **하위호환 유지 방식**: 기존 소비자는 자신이 읽던 필드를 그대로 읽는다 — 필드 삭제·의미 변경 0건이므로 "raw passthrough 계약"은 **깨지지 않고 상위집합으로 확장**된다. ANALYSIS H-2가 "계약 변경 불가피"로 본 것은 *기존 경로 필드를 계산값으로 덮어쓰는* 안을 전제한 것이며, additive 필드 추가로 그 전제를 회피한다.
- **미설치/미해석 시**: `resolved_path`는 `null`을 반환한다 (`match`의 `path` 필드가 미설치 community에서 `null`을 반환하는 현행 규약과 동형, `:302`). R-6 AC "미설치 시 기존과 동일하게 처리된다"를 충족한다.
- **[MUST] H-2·H-3 반영 — 신규 테스트가 `get`을 반드시 커버한다**: `get` 전용 테스트는 기존 4파일에 0건이다(→ ANALYSIS §1.4 grep 결과). 따라서 F-002 신규 테스트는 `get`에 대해 (a) project 스킬 `resolved_path` 해석, (b) 미설치 시 `null`, (c) **기존 필드 보존 회귀**(main 스킬 `paths` 배열이 그대로 반환되는지) 3케이스를 의무 포함한다 — §4.2 Step 3·Step 4 완료 기준에 명시.

### DEC-6. `analysis-core.md` §5 축에 "도구" 라벨 추가 → **이번 범위 밖으로 이월 (문서 미개정)**

- **선택**: `opal/core/references/harness/analysis-core.md` §5를 이번 태스크에서 **수정하지 않는다**.
- **근거**: [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." — analysis-core.md는 TASK.md §범위의 「포함」 7항 어디에도 없고, 「제외」에 해당하는 인접 프레임워크 문서다. 축 라벨 개정은 **모든 pilot의 ANALYSIS/PLAN 산출물 포맷에 파급**되므로 별도 태스크의 영향 분석을 요구한다.
- **이번 태스크의 대응(우회)**: 본 PLAN의 §2·§3 파일 맵/변경 계획에서는 `skill-registry.js`·테스트 파일에 **임시 라벨 `도구`**를 사용하고, 각 표에 H-1 각주를 단다. agent 배정은 `도구` → `opal-task-agent`(범용)로 매핑한다 — op-dev-plan SKILL.md §agent 필드 배정 규칙의 `공통`/`환경` 행과 동일한 범용 귀속이다.
- **이월 등록**: §9 R-1에 후속 개선 제안으로 기재한다.

### DEC-7 (추가 확정). wizard 약어 → **`osw`**

- **선택**: `osw` (`opal-skill-wizard`).
- **근거**: 기존 명명 패턴 `opal-skill-manager → osm`, `opal-skill-creator → osc`("스킬" 그룹 내 역할 이니셜 3자 조합)의 직계 연장이다. 등재 alias 29종 전건 grep 결과 충돌 0건 (→ ANALYSIS §7 Q7).
- **탈락**: `oskw`(4자 — 기존 3자 관례 이탈), `wizard`(전체어 — `osm`/`osc`와 비대칭). 둘 다 충돌은 0건이나 패턴 정합성에서 열위.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

프로젝트에 적합한 커뮤니티 스킬을 인터뷰·분석으로 도출해 제안하고, 승인분을 **프로젝트 스코프**(`{project}/.opal/community-skills/`)에 설치하는 신규 스킬 `opal-skill-wizard`(약어 `osw`)를 신설한다. 설치분이 `//` 커맨드로 발동하도록 `skill-registry.js`의 `loadAllSkills()`에 프로젝트 registry를 4번째 소스로 additive 병합하고, 프로젝트 스킬 경로 해석과 `get`의 `resolved_path` 필드를 추가한다. 전역 설치 경로·규칙은 `opal-skill-manager`가 계속 담당하며 이번 변경 대상이 아니다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 프로젝트 registry 병합 + 프로젝트 스킬 경로 해석 (`skill-registry.js`) | R-5, R-6 | P0 | 없음 |
| F-002 | 회귀 방지 + 신규 테스트 (유·무·파손 3케이스 + `get` 커버) | R-8 | P0 | F-001 |
| F-003 | `opal-skill-wizard` SKILL.md 신설 (2모드·제안→승인→설치·scan-risk·creator 위임) | R-1, R-2, R-3, R-4 | P0 | F-004 |
| F-004 | 프로젝트 registry 스키마 정의 + 아키텍처 문서 반영 | R-7 | P0 | 없음 |
| F-005 | `//` 라우팅 개정 + 레지스트리 등재·약어 배정 | R-9, R-10 | P1 | F-001, F-003 |
| F-006 | 변경이력 행 추가 (수정 문서 전건) | R-11 | P1 | F-003, F-004, F-005 |

> 요구사항 커버리지: R-1~R-11 전건이 F-001~F-006에 매핑되며 미할당 0건.

### 1.3 기능 의존 그래프 (ASCII)

```
F-004 (스키마 정의)
   |
   v
F-003 (wizard SKILL.md) ----+
                            |
F-001 (registry 로더 확장)  |
   |         \              |
   v          \             v
F-002 (테스트) +-------> F-005 (라우팅·등재)
                              |
                              v
                          F-006 (변경이력)
```

- F-001과 F-004는 선행 의존이 없어 **병렬 착수 가능**.
- F-002는 F-001의 구현 계약이 확정돼야 검증 대상이 생기므로 순차. 단 **RED-first 트랙**(§1.4)에서는 실패 테스트 작성이 F-001 구현에 선행한다.

### 1.4 RED-first 트랙 판정

> 근거: `opal/core/references/harness/red-first.md` §1.5 (하이브리드 자동분기).

| F-ID | 변경 영역 | §1.5 분류 | 트랙 |
|------|----------|----------|------|
| F-001 | `skill-registry.js` 로더·경로 해석·`match`/`get` 응답 계약 | **API 계약** (CLI 서브커맨드 응답 계약) | **RED-first 강제** |
| F-002 | 테스트 코드 자체 | (트랙의 산출물) | RED 단계 산출물 |
| F-003 | SKILL.md 신설 | 설정·문서 | 구현 후 시나리오 검증 허용 |
| F-004 | 스키마 정의 + `docs/ARCHITECTURE.md` | 설정·문서 | 구현 후 시나리오 검증 허용 |
| F-005 | 참조 문서 + 레지스트리 JSON | 설정·문서 | 구현 후 시나리오 검증 허용 |
| F-006 | 변경이력 표 | 설정·문서 | 구현 후 시나리오 검증 허용 |

- **종합 판정: 하이브리드 — 동작검증 대상인 F-001/F-002는 RED-first 강제, 문서·설정 F-003~F-006은 구현 후 검증.**
- [MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지." → §4.2 Step 3(RED)이 Step 4(GREEN)에 선행하도록 배치했다.
- **state-tool 연동**: RED-first 트랙이 켜지므로 `verify --red-check` **ON**으로 검증한다 (red-first.md §1.5 state-tool 연동).
- **공통 불변 3항 유지**: ① 테스트 코드 산출물(F-002) ② 작성자≠구현자 — RED 테스트는 `opal-test-agent(mode: red)`, 구현은 `opal-task-agent` ③ TEST 단계 검증.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. 검증 계층 — L1 단위(함수/순수 로직) / L2 통합(실 fs fixture + 실제 CLI 프로세스) / L3 E2E(`//` 커맨드 발동 경로).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `loadAllSkills()` 4번째 소스 병합 | 전역 3소스(main/community/user) 병합 결과가 프로젝트 registry 부재 시에도 **완전 동일**해야 한다는 무회귀 계약 | P0 — 깨지면 전 pilot의 `//` 커맨드 매칭이 전면 붕괴 | L2 (실 CLI, 프로젝트 registry 無 fixture) | S 후보: "프로젝트 registry 없음 → 기존 41 pass 기준선 전건 유지" |
| H-2 | F-001 `loadProjectRegistry()` 파손 내성 | `loadUserRegistry()`가 확립한 "부재/파손 시 `null` 반환 → CLI 다운 방지" 계약(`skill-registry.js:118-128`) | P0 — 파손 JSON 하나로 CLI 전체가 throw하면 모든 스킬 발동 불가 | L2 (깨진 JSON fixture로 실제 프로세스 exit code 검증) | S 후보: "잘린 JSON `.opal/skills-registry.json` → exit 0 + 전역만 병합" |
| H-3 | F-001 `getCommand()` `resolved_path` 추가 | 기존 raw passthrough 계약 — 기존 필드(`paths`, community raw 필드)의 **삭제·의미 변경 0건** | P1 — `opal-help`/`opal-skill-manager` 절차가 참조하는 필드가 사라지면 문서 절차가 무효화 | L1 + L2 (기존 필드 보존 회귀 단정) | S 후보: "main 스킬 `get` → `paths` 배열 원형 유지 + `resolved_path` 추가" (ANALYSIS H-2·H-3: `get` 커버리지 0건) |
| H-4 | F-001 walk-up 프로젝트 루트 탐색 | 홈 경계 정지 규약 — `~/.opal/`을 프로젝트 스코프로 오인하지 않음 | P0 — 오인 시 전역 자산이 프로젝트 스코프로 이중 로드되어 `_source` 마커가 오염 | L2 (cwd를 `$HOME` 하위로 둔 fixture) | S 후보: "cwd=$HOME 하위, 프로젝트 registry 無 → project 소스 0건" |
| H-5 | F-001 walk-up 상향 탐색 | 하위 디렉토리 호출 시에도 루트를 찾는다는 신규 계약 (ANALYSIS H-5 해소책) | P1 — 실패 시 `dashboard/backend/`에서의 호출이 조용히 전역만 병합 | L2 (fixture 루트의 3단 하위에서 `spawnSync cwd` 지정) | S 후보: "하위 디렉토리 cwd → project 스킬 `match found:true`" |
| H-6 | F-001 `matchCommand()` `_source==='project'` 분기 | `match` 응답의 `installed` 필드 의미 — community 한정에서 "실물 SKILL.md 부재 전반"으로 일반화 | P1 — `harness/skill-commands.md` 라우팅이 `installed`에 의존(`:24`) | L2 + L3 (`//` 라우팅 문서 정합 확인) | S 후보: "project 스킬 미설치 → `installed:false` + wizard 라우팅" |
| H-7 | F-001 override 순서 (DEC-3) | 동일 `name` 시 프로젝트 최우선 — `match`/`get`이 프로젝트 항목을 반환 | P2 — 잘못되면 전역 동명 스킬이 프로젝트 의도를 덮어씀 | L2 (동일 `name`을 전역·프로젝트 양쪽에 둔 fixture) | S 후보: "동명 충돌 → `_source` 유래가 project인 정의가 반환" |
| H-8 | F-003 wizard SKILL.md `scan-risk` 게이트 | [MUST] "설치 전 검사 실패 시 복사하지 않는다" 규칙이 산문이 아닌 **절차 순서**로 강제되는지 | P1 — 누락 시 미검사 외부 코드가 프로젝트에 유입 | L3 (문서 절차 정적 검사: 복사 단계 직전 `scan-risk` 호출 존재) | S 후보: "SKILL.md 절 순서 — scan-risk가 복사 단계보다 앞" |
| H-9 | F-005 `opal-skills-registry.json` 등재 | JSON 스키마 유효성 + alias 유일성 | P1 — 파손 시 `getReferencesDir()` 하위 카탈로그 로드 실패 → 전 스킬 매칭 불가 | L2 (`validate` error 0건 + `match "osw"` found:true) | S 후보: "`match \"osw\"` → `opal-skill-wizard` 반환, alias 중복 0" |

---

## 2. 기능별 분석

> 영역 축: `analysis-core.md` §5 "프레임워크 문서·스킬 태스크" 축(스킬/가이드/오케스트레이터/에이전트/문서/환경/배치)을 사용한다. CLI 코드 파일에 대응하는 라벨이 없어 **임시 라벨 `도구`**를 사용한다 — 축 개정은 DEC-6에 따라 이번 범위 밖으로 이월(ANALYSIS H-1).

### F-001: 프로젝트 registry 병합 + 프로젝트 스킬 경로 해석

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구(임시 라벨, H-1) | `opal/tools/skill-registry/skill-registry.js` | `loadAllSkills()` 4소스 병합, 프로젝트 루트 walk-up, 경로 해석, `match`/`get` 응답 분기 | 수정 |

#### 2.1.2 현재 구현

- `loadAllSkills()`(`:129-147`)는 `getReferencesDir()`로 얻은 카탈로그 디렉토리에서 `opal-skills-registry.json`·`community-skills-registry.json` 2개를 로드하고, `loadUserRegistry()`(`:118-128`) 결과를 3번째로 병합한다. 병합은 `flattenGroups(reg, source)`로 `_source` 마커를 부착한 뒤 `findIndex(s => s.name === us.name)` → `skills[idx] = us` else `push` 루프다(`:137-144`).
- `getReferencesDir()`(`:80-92`)는 "cwd 소스 레이아웃 → `~/.opal/references/` 배포 → `__dirname` 소스" 3단 폴백이며 **상향 탐색은 하지 않는다**(`:83-84`) — ANALYSIS H-5의 원천.
- 경로 해석은 유형별로 분화되어 있다: main은 `resolveFirstPath(paths)`(`:229-253`, `~`·`{project}` 치환 + `path.resolve` 정규화 + homedir/cwd 하위 검증으로 CWE-22 방어), community는 `resolveCommunitySkillPath(name)`(`:100-109`, vendor 중첩 → flat 폴백 → `null`).
- `matchCommand()`(`:255-323`)는 `isCommunitySkill(skill)`(`:112-114`, `_source==='community'` 단일 조건) 2분기 구조다 — community 분기는 `installed`/`source_repo`/`license`/`install_command`/`install_method`를 추가 반환하고, main 분기는 `path: resolveFirstPath(skill.paths)`를 반환한다.
- `getCommand()`(`:327-340`)는 `{_group, _source, ...rest}` 구조분해 후 `{...rest, group: _group}`을 반환할 뿐 **경로 계산이 전무**하다.
- `listCommand()`(`:342-)`는 `--group=community`를 `_source === 'community'`로 필터한다(`:349-351`).

#### 2.1.3 영향 범위

- `main()`(`:849-931`)이 라우팅하는 7개 서브커맨드(`match`/`get`/`list`/`validate`/`migrate`/`parse-source-repo`/`scan-risk`)가 전부 `loadAllSkills()`를 공유 소비 → 1곳 확장이 7곳에 파급 (→ ANALYSIS §1.3).
- 외부 소비자 3종: `dashboard/backend/adapters/skill_adapter.py:47`(`list` 무인자, 최상위 타입만 분기 `:53-75`), `opal/skills/opal-skill-manager/SKILL.md`(`match`/`list`), `opal/skills/opal-help/SKILL.md`(`list`/`get`/`match`). `get`의 코드 레벨 소비자는 0건.
- 기존 테스트 4파일 41 pass가 전부 이 함수 경로를 지나므로 회귀 감지 표면이 넓다 — 단 `get`만 커버 0건(ANALYSIS H-3).

### F-002: 회귀 방지 + 신규 테스트

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구(임시 라벨, H-1) | `opal/tools/skill-registry/tests/test-project-registry.js` | 프로젝트 registry 유·무·파손 3케이스 + walk-up + `get` 계약 회귀 | 신규 |
| 도구(임시 라벨, H-1) | `opal/tools/skill-registry/tests/test-match.js` / `test-validate.js` / `test-migrate.js` / `test-scan-risk.js` | 회귀 기준선(41 pass / 0 fail) 유지 확인 — **파일 무변경** | 무변경(실행만) |

#### 2.2.2 현재 구현

- 프레임워크: Node.js 내장 `node:test`. 러너 설정 없이 `node <파일>` 직접 실행.
- 격리 패턴 2종 併用 — (a) `os.tmpdir()` + `mkdtempSync` 합성 fixture에 `spawnSync`의 `env.HOME` 오버라이드로 `os.homedir()` 리다이렉트(`test-validate.js:93-95`, `test-match.js:126-135`), (b) `spawnSync`의 `cwd` 옵션으로 프로세스 작업 디렉토리를 fixture 루트로 지정(`test-match.js:135`).
- 실측 기준선: `test-match.js` 11 / `test-validate.js` 5 / `test-migrate.js` 9 / `test-scan-risk.js` 16 = **합계 41 pass / 0 fail** (cwd 리포지토리 루트, 4파일 개별 실행 — → ANALYSIS §1.4).

#### 2.2.3 영향 범위

- 신규 테스트는 기존 4파일을 수정하지 않는다 → 기준선 산술이 그대로 유지되고, 신규분은 별도 파일의 pass 수로 가산된다.
- (a)+(b) 병용이 **전역/프로젝트 두 스코프를 동시에 통제**하는 유일한 방법이다 — HOME으로 전역 registry를, cwd로 프로젝트 registry를 각각 격리한다.

### F-003: `opal-skill-wizard` SKILL.md 신설

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-wizard/SKILL.md` | 2모드 판별 + 제안→승인→설치 흐름 + scan-risk 게이트 + creator 위임 | 신규 |
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | 위임 페이로드 7필드·설치 4단 절차의 **참조 원본** | 무변경(참조만) |
| 스킬 | `opal/skills/opal-project-init/SKILL.md` | 2모드 골격·PROJECT.md 표준 섹션의 **참조 원본** | 무변경(참조만) |

#### 2.3.2 현재 구현

- `opal-skill-manager/SKILL.md`는 §1 검색 → §2 설치(clone-copy 4단) → §3 목록 → §4 삭제 → §5 업데이트 확인 → §6 미설치 자동설치 구성이며, §설치 경로 규칙(`:256-`)이 전역 이원 registry 경계를 규정한다.
- [MUST] `opal/skills/opal-skill-manager/SKILL.md` §2: "**clone은 임시, 복사가 설치** — `git clone --depth 1`의 대상은 **임시 디렉토리**이며 clone 자체는 설치가 아니다. **설치는 `~/.opal/community-skills/{vendor}/{basename}/`로의 복사 시점에 성립**하므로, 승인 게이트는 6단(복사 직전) 1회를 유지한다." → wizard도 동일 원리를 프로젝트 경로에 적용한다.
- 위임 트리거 3조건(`:85-88`)과 페이로드 7필드(`:92-102`)는 wizard의 검색·판정 절차와 동형이므로 **재사용 가능**(→ ANALYSIS §7 Q8).
- `opal-project-init/SKILL.md`의 2모드 판별(`:54`)·초기화 신규(`:263`)·초기화 기존(`:354`)·최신화 조건부 인터뷰(`:806`)가 2모드 골격의 선례다.

#### 2.3.3 영향 범위

- wizard는 신규 파일이므로 기존 스킬의 동작을 변경하지 않는다. `opal-skill-manager`를 **호출하지 않으므로**(TASK.md [결정]) manager 절차 변경도 유발하지 않는다.
- `docs/PROJECT.md`를 읽기 전용으로 소비 — 재사용 가능 항목은 §프로젝트 구조 폴더 구조맵 + §프로젝트 구성 4열 표(기술 스택 컬럼), 결측 항목은 "원하는 스킬의 기능 범주"(→ ANALYSIS §7 Q9).

### F-004: 프로젝트 registry 스키마 정의 + 아키텍처 문서 반영

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-wizard/SKILL.md` | 스키마 필드 표 게재(운용 SSOT) | 신규(F-003과 동일 파일) |
| 문서 | `docs/ARCHITECTURE.md` | §커뮤니티 스킬 표의 "레지스트리 (이원)" 행을 스코프 3원 구조로 확장 | 수정 |

#### 2.4.2 현재 구현

- `docs/ARCHITECTURE.md` §커뮤니티 스킬(`:187-198`)에 전용 "레지스트리 구조" 절은 없고 표 1행("레지스트리 (이원)", `:196`)으로만 존재한다 — 프레임워크 카탈로그 + 사용자 등록분 2원.
- 동 행은 사용자 등록분이 "기존 7필드에 판정 3필드(`trust`·`capabilities`·`scanned_at`)를 additive로 함께 기록"하며 "`validate`가 미지 필드를 무시하는 성질을 이용한다"고 명시한다 → 프로젝트 registry도 동일 성질 위에 설계한다(R-7 AC "validate error 0건" 충족 경로).

#### 2.4.3 영향 범위

- `validate` 서브커맨드가 프로젝트 registry 항목도 검사 대상에 포함하게 되므로(DEC-3 표), 스키마가 필수 필드를 만족하지 못하면 `validate`가 error를 낸다 → 스키마 정의가 곧 `validate` 통과 조건이다.

### F-005: `//` 라우팅 개정 + 레지스트리 등재·약어 배정

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/skill-commands.md` | 미설치 매칭 라우팅 3중 분기화 | 수정 |
| 문서 | `opal/core/references/opal-skills-registry.json` | `groups.opal` 배열에 wizard 항목 등재 + `changelog` 추가 | 수정 |

#### 2.5.2 현재 구현

- `skill-commands.md:24`가 `installed:false` 단일 조건으로 `opal-skill-manager/SKILL.md §6`을 **단독 지목**하며, 동 문서 하단(§쌍슬래시 커맨드 말미)에도 동일 취지 문장이 1건 더 있다 — R-9 AC("단독 지목 문장 0건")는 이 **2건 모두**를 대상으로 한다.
- `opal-skills-registry.json`은 `$schema`/`version`/`updated_at`/`groups`/`changelog` 5키 구조이며 `groups.opal`은 13개 항목이다. 각 항목은 `name`/`alias`/`description`/`triggers`(정규식 배열)/`paths`(`{project}` → `~` 2단)/`domain` 필드를 갖는다.
- 마지막 changelog는 `version: "3.13.0"`(2026-09-02).

#### 2.5.3 영향 범위

- `paths`에 `{project}/.opal/skills/...` → `~/.opal/skills/...` 2단 패턴을 그대로 적용한다 — `resolveFirstPath()`가 `{project}`를 `process.cwd()`로 치환하고 homedir/cwd 하위 검증을 하므로(`:229-253`) 기존 13항목과 동일하게 해석된다.
- `//` 라우팅 문서는 전 pilot의 커맨드 해석 경로가 공유 소비하므로, `installed`/`ambiguous` 필드 의미가 유지되어야 한다(→ ANALYSIS §3.2).

### F-006: 변경이력 행 추가

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/skill-commands.md` | 변경이력 표 v1.4 행 | 수정 |
| 문서 | `opal/core/references/opal-skills-registry.json` | `changelog` 배열 항목 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | 변경이력 표 행 | 수정 |
| 스킬 | `opal/skills/opal-skill-wizard/SKILL.md` | 변경이력 표 v1.0 행(신설) | 신규 |

#### 2.6.2 현재 구현

- `skill-commands.md` 변경이력 최신 행은 v1.3(2026-07-17). `opal-skills-registry.json` changelog 최신은 3.13.0. `docs/ARCHITECTURE.md`는 문서 말미 변경이력 표를 보유한다.

#### 2.6.3 영향 범위

- 문서 메타데이터만 변경 — 런타임 동작 영향 없음. 단 `opal-skills-registry.json`은 JSON이므로 **파손 시 전 스킬 매칭 불가**(H-9) → `validate` 통과가 완료 조건.

---

## 3. 기능별 설계

### F-001: 프로젝트 registry 병합 + 프로젝트 스킬 경로 해석

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음 (F-001 범위 내 신규 파일 없음)

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `findProjectRoot()` 신규 (walk-up, 홈 경계 정지) | DEC-1 / `skill-registry.js:80-92` |
| 2 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `loadProjectRegistry()` 신규 (방어적 로드, 파손 시 `null`) | `skill-registry.js:118-128` (loadUserRegistry 동형) |
| 3 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `resolveProjectSkillPath()` 신규 (vendor 중첩 → flat 폴백 → `null`) | `skill-registry.js:100-109` (resolveCommunitySkillPath 동형) |
| 4 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `loadAllSkills()`에 4번째 병합 단계 추가 (`_source:'project'`) | `skill-registry.js:129-147` / DEC-3 |
| 5 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `matchCommand()`에 `_source==='project'` 분기 추가 | `skill-registry.js:255-323` / H-6 |
| 6 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `getCommand()`에 `resolved_path` additive 필드 추가 | `skill-registry.js:327-340` / DEC-5 |

> 영역 라벨 `도구`는 DEC-6에 따른 임시 라벨(ANALYSIS H-1). agent 배정은 `opal-task-agent`.

#### 3.1.2 API·데이터 모델 설계

##### (a) `findProjectRoot(startDir = process.cwd())` — 신규

- 반환: 프로젝트 루트 절대경로(string) 또는 `null`.
- 알고리즘: `dir = path.resolve(startDir)`에서 시작해 반복 — `fs.existsSync(path.join(dir, '.opal'))`(디렉토리 존재)이면 `dir` 반환. 아니면 `parent = path.dirname(dir)`.
- **[MUST] 탐색 마커는 `.opal/` 디렉토리이며 `.opal/skills-registry.json` 파일이 아니다** (PM 교정, PM Gate). 파일을 마커로 삼으면 (i) 최초 설치 전에는 루트를 찾지 못하는 순환이 생기고 — registry는 wizard 최초 설치 시 생성되며 부재가 정상 상태다(§3.1.4) —, (ii) wizard 진입 훅이 쓰는 마커(`{project}/.opal/`, §3.3.2 §진입 훅)와 로더가 쓰는 마커가 갈려 **설치 루트와 해석 루트가 불일치**할 수 있다. `.opal/` 디렉토리는 OPAL 프로젝트의 정의 자체와도 정합한다 — [MUST] `~/.opal/AGENT.md` §부트스트랩 Phase B: "cwd에 `.opal/AGENT.md`가 없으면 Phase B 전체를 스킵한다"가 프로젝트 판별 기준으로 `.opal/`을 이미 사용한다.
- 마커를 디렉토리로 바꾸어도 종료 조건은 그대로 유효하다 — `~/.opal/`이 항상 존재하므로 **홈 경계 정지(①)가 더 결정적**이 되며, 이는 이미 [MUST]로 규정되어 있다(H-4/TS-008). registry 파일 부재 시에는 루트를 찾되 `loadProjectRegistry()`가 `null`을 반환하므로 TS-002(부재 시 전역 3소스 동일)는 그대로 성립한다.
- **[MUST] 종료 3조건** (DEC-1): ① `dir === os.homedir()`이면 검사하지 않고 `null` 반환 (전역 `~/.opal/` 오인 차단, H-4) ② `parent === dir`(FS 루트)이면 `null` ③ 반복 32회 초과 시 `null`.
- 예외 내성: `fs.existsSync`는 throw하지 않으나, 권한 오류 대비 전체를 `try/catch`로 감싸고 catch 시 `null` 반환 — [MUST] "CLI 전체 다운 방지"(`skill-registry.js:126` 주석 규약 상속).

##### (b) `loadProjectRegistry(projectRoot)` — 신규

- `projectRoot`가 falsy면 즉시 `null`.
- `path.join(projectRoot, '.opal', 'skills-registry.json')`을 `existsSync` → `JSON.parse(readFileSync)`. `catch` 시 `null` (H-2). `loadUserRegistry()`(`:118-128`)와 **동일 구조**를 따른다 — 신규 예외 정책을 만들지 않는다.

##### (c) `resolveProjectSkillPath(skillName, projectRoot)` — 신규

- vendor 중첩 우선: `{projectRoot}/.opal/community-skills/{skillName}/SKILL.md`
- flat 폴백: `{projectRoot}/.opal/community-skills/{basename}/SKILL.md` (`skillName`에 `/`가 있으면 마지막 세그먼트)
- 둘 다 없으면 `null`. → `resolveCommunitySkillPath()`(`:100-109`)의 규칙을 루트만 바꿔 이식 (DEC-2).

##### (d) `loadAllSkills()` 확장 — 4번째 병합 단계

- 기존 `if (userReg) {...}` 블록(`:138-145`) **직후**에 추가한다 (→ ANALYSIS §8 확정값).
- `const projectRoot = findProjectRoot(); const projectReg = loadProjectRegistry(projectRoot);`
- `if (projectReg) { const ps = flattenGroups(projectReg, 'project'); for (const p of ps) { const idx = skills.findIndex(s => s.name === p.name); if (idx >= 0) skills[idx] = p; else skills.push(p); } }`
- **[MUST] additive 한정**: 기존 3소스 로드·병합 코드는 한 줄도 수정하지 않는다 — TASK.md §제약: "`skill-registry.js` 변경은 기존 전역 3소스 병합 동작을 보존하는 additive 방식으로 한정한다."
- `projectRoot`는 `_source:'project'` 항목이 이후 경로 해석에 쓰도록 각 항목에 `_project_root` 내부 필드로 부착한다(`_`-prefix 내부 필드 관례는 `_group`/`_source`와 동일, `:70-72`).

##### (e) `matchCommand()` project 분기 — 응답 계약

| 필드 | 값 | 비고 |
|------|-----|------|
| `found` | `true` | |
| `name`/`group`/`alias`/`description`/`domain`/`cleanInput` | 기존과 동일 | |
| `path` | `resolveProjectSkillPath(...)` 또는 미설치 시 `null` | community 분기(`:302`)와 동형 |
| `installed` | `path !== null` | H-6 — 의미를 "실물 SKILL.md 존재 여부"로 일반화 |
| `scope` | `"project"` | **신규 필드** — 라우팅이 스코프를 구분하는 근거 (F-005) |
| `source_repo` / `license` | 프로젝트 registry 등재값 또는 `null`/`"Unknown"` | community 분기와 동일 규약 |

- **[MUST] main·community 분기의 기존 반환 필드는 변경하지 않는다** — `scope` 필드는 project 분기에만 추가한다(하위호환). `installed`/`ambiguous` 필드의 기존 의미는 유지된다(→ ANALYSIS §3.2).

##### (f) `getCommand()` — additive `resolved_path` (DEC-5)

- 기존 `const { _group, _source, ...rest } = skill; return { ...rest, group: _group };`에 `resolved_path`를 더한다.
- `_source`별 산출은 DEC-5 표를 따른다. `_project_root`·`_group`·`_source` 등 `_`-prefix 내부 필드는 계속 응답에서 제외한다(현행 구조분해 규약 유지).

#### 3.1.3 환경 변경

해당 없음 — 신규 패키지·환경변수 도입 0건 (DEC-1이 환경변수안을 탈락시켰다).

#### 3.1.4 배치/마이그레이션

해당 없음 — 기존 데이터 이관 불필요. 프로젝트 registry는 wizard 최초 설치 시 생성된다(부재가 정상 상태).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-5 AC① | L2 통합 | 프로젝트 registry에 등재된 스킬에 대해 `match "{name}"`이 `found:true` |
| TS-002 | R-5 AC② | L2 통합 | 프로젝트 registry **부재** 시 CLI exit 0 + 전역 3소스 결과가 기준선과 동일 |
| TS-003 | R-5 AC② | L2 통합 | 프로젝트 registry **파손**(잘린 JSON) 시 CLI exit 0 + 전역 3소스만 병합 |
| TS-004 | R-6 AC① | L2 통합 | 프로젝트 설치 스킬의 `get` 응답 `resolved_path`가 실제 SKILL.md 절대경로 |
| TS-005 | R-6 AC② | L2 통합 | 미설치 project 스킬 `get` → `resolved_path: null`, `match` → `installed:false` |
| TS-006 | H-3 | L2 통합 | main 스킬 `get` 응답에 기존 `paths` 배열이 원형 보존 + `resolved_path` 추가 |
| TS-007 | H-5 | L2 통합 | fixture 루트 3단 하위 디렉토리를 `cwd`로 실행해도 project 스킬 매칭 성공 |
| TS-008 | H-4 | L2 통합 | `cwd`가 `$HOME` 하위이고 프로젝트 registry 부재 → `_source:'project'` 항목 0건 |
| TS-009 | H-7 / DEC-3 | L2 통합 | 전역·프로젝트 동일 `name` → 프로젝트 정의가 반환(override) |

### F-002: 회귀 방지 + 신규 테스트

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/skill-registry/tests/test-project-registry.js` | 도구 | TS-001~TS-009 전건 구현 (`node:test`) | R-8 AC / (→ ANALYSIS §1.4 격리 패턴) |

**수정**: 없음 — 기존 4개 테스트 파일은 **무변경**으로 재실행만 한다 (회귀 기준선 산술 보존).

#### 3.2.2 설계

- **격리**: `mkdtempSync(path.join(os.tmpdir(), 'osw-'))`로 (a) 가짜 HOME과 (b) 가짜 프로젝트 루트를 각각 만든다. `spawnSync(process.execPath, [CLI, ...args], { env: {...process.env, HOME: fakeHome}, cwd: fakeProject, encoding: 'utf8' })` — `test-match.js:126-135` 패턴 재사용.
- **가짜 HOME 구성**: `{fakeHome}/.opal/references/opal-skills-registry.json` + `community-skills-registry.json` 최소 fixture. `getReferencesDir()`의 2순위(배포 경로)에 걸리게 한다 — 단 **1순위가 cwd 소스 레이아웃**(`:83-84`)이므로 가짜 프로젝트 루트에 `opal/core/references/`를 두지 않아야 2순위로 떨어진다. [MUST] 이 조건을 테스트 fixture 주석에 명시한다.
- **가짜 프로젝트 구성**: `{fakeProject}/.opal/skills-registry.json` + `{fakeProject}/.opal/community-skills/{vendor}/{skill}/SKILL.md`.
- 3케이스 = 유(정상 JSON) / 무(파일 미생성) / 파손(잘린 JSON 문자열) — R-8 AC 직결.
- **[MUST] `get` 커버 의무** (DEC-5 / ANALYSIS H-2·H-3): TS-004·TS-005·TS-006이 `get`을 직접 호출한다. 기존 4파일에 `get` 커버가 0건이므로 이 3건이 유일한 안전망이다.

#### 3.2.3 환경 변경 / 3.2.4 배치

해당 없음.

#### 3.2.5 테스트 시나리오

F-001의 TS-001~TS-009가 곧 이 파일의 구현 대상이다. 추가로:

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-8 AC(기존 전건 통과) | L2 회귀 | 기존 4파일 개별 실행 결과가 **41 pass / 0 fail**(cwd 리포지토리 루트) 기준선과 동일 |

### F-003: `opal-skill-wizard` SKILL.md 신설

#### 3.3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-skill-wizard/SKILL.md` | 스킬 | 2모드 제안·승인·설치 스킬 본문 | R-1~R-4, R-7 |

#### 3.3.2 SKILL.md 설계 — 목차와 각 절이 담을 내용

> **[MUST] 본문은 EXECUTE에서 작성한다. 본 절은 목차와 각 절의 확정 내용만 규정한다.**
> [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → wizard 본문에 플랫폼 분기를 두지 않는다.

| 절 | 제목 | 담을 내용(확정) |
|----|------|---------------|
| frontmatter | `name`/`description`/`version` | `name: opal-skill-wizard`, description에 "반드시 사용해야 하는 상황" + 필수 입력/보장 출력, `version: 1.0` — 기존 스킬 frontmatter 관례 준수 |
| §진입 훅 | 실행 컨텍스트·선행 확인 | Node.js·`git` 가용성 확인, `skill-registry.js` 경로 확인, 프로젝트 루트 확정 — `findProjectRoot`와 **동일 마커 `{project}/.opal/` 디렉토리**를 사용한다(§3.1.2(a) [MUST], PM 교정으로 양측 마커 통일) |
| §0 | **모드 판별** | **판별 기준 표** — `docs/PROJECT.md` 존재 여부 단일 축. 존재 → **기존 모드**, 부재 → **신규 모드**. 판별 결과를 사용자에게 1줄 통지 후 진행 (R-1 AC "모드 판별 기준이 표 또는 절로 존재") |
| §1 | **신규 모드 — 인터뷰** | PROJECT.md가 없으므로 프로젝트 파악을 인터뷰로 수행. **[MUST] `opal-project-init`을 대체하지 않는다** — 스킬 제안에 필요한 최소 항목(기술 영역 / 반복 작업 유형 / 자동화 희망 범주 / 제약)만 묻고, 전면 온보딩이 필요하면 `opal-project-init`을 안내만 한다 |
| §2 | **기존 모드 — PROJECT.md 재사용 + 결측 인터뷰** | **재사용 항목 목록**(§프로젝트 구조 폴더 구조맵, §프로젝트 구성 4열 표의 기술 스택 컬럼 — → ANALYSIS §7 Q9) / **결측 판정 기준**(해당 절 부재 또는 값이 비어 있음) / **결측 항목**(원하는 스킬의 기능 범주 = 자동화 대상 작업 유형 — PROJECT.md에 구조화 필드 없음) / **PROJECT.md 부재 시 폴백** = §1 신규 모드로 전환 (R-2 AC 3항 전건) |
| §3 | **후보 도출 + skills.sh 직접 검색** | `npx skills find "{query}"` 검색 명령 명시 / clone 대상 = **임시 디렉토리** / 복사 대상 = `{project}/.opal/community-skills/{vendor}/{skill}/`. **[MUST] `opal-skill-manager`를 호출하라는 지시를 본문 전체에 0건으로 유지**(R-3 AC) — manager 문서를 *참조 근거로 인용*하는 것과 *호출 지시*는 구분한다 |
| §4 | **설치 전 보안 검사 (`scan-risk` 게이트)** | **호출 지점 = 복사 직전**(clone 이후, 복사 이전). 명령: `node {skill-registry.js} scan-risk {clone된 SKILL.md 경로}`. **판정별 동작 표**(아래 3.3.3) + [MUST] "검사 실패(도구 비정상 종료·미실행) 시 설치를 진행하지 않는다" 규칙 (R-4 AC 3항 전건) |
| §5 | **제안 → 승인 → 설치** | 3단이 이 순서로 기재된다(R-1 AC). 승인 게이트는 **복사 직전 1회**로 고정 — [MUST] `opal/skills/opal-skill-manager/SKILL.md` §2: "clone은 임시, 복사가 설치 ... 승인 게이트는 6단(복사 직전) 1회를 유지한다."와 동일 원리를 프로젝트 경로에 적용 |
| §6 | **프로젝트 registry 기록** | **기록 시점 = 복사 성공 직후**(설치 성립 시점). 대상 파일 `{project}/.opal/skills-registry.json`(DEC-2). 파일 부재 시 스켈레톤 생성 후 append. 기록 후 `match "{name}"`으로 발동 가능 여부를 즉시 자가 확인 |
| §7 | **적합 스킬 미발견 시 `opal-skill-creator` 위임** | **트리거 3조건 재사용** — 검색 0건 / 판정 후 잔존 후보 0건 / 사용자 전건 거부 (`opal/skills/opal-skill-manager/SKILL.md:85-88`). **페이로드 7필드 그대로 재사용**(`:92-102`, → ANALYSIS §7 Q8): `requested_capability`·`requested_triggers`·`requested_output_format`·`searched_sources`·`candidates_evaluated`·`security_findings`·`skill_type_hint`. [MUST] 위임 대상은 `opal-skill-creator`이며 신규 생성기 컴포넌트를 만들지 않는다 |
| §8 | **프로젝트 registry 스키마** | F-004 스키마 표(3.4.2)를 게재 |
| §9 | **설치 경로 규칙 (스코프 경계)** | wizard = 프로젝트 스코프 전용. [MUST] 전역(`~/.opal/community-skills/`)에 쓰지 않는다. [MUST] 플랫폼 네이티브 `skills/` 디렉토리에 복사하지 않는다 — `opal-skill-manager` §설치 경로 규칙과 동일 금지를 프로젝트 스코프에도 적용 |
| §변경이력 | 표 | v1.0 행 (F-006) |

#### 3.3.3 `scan-risk` 판정별 동작 (§4 표의 확정 내용)

| `scan-risk` 판정 | wizard 동작 |
|-----------------|------------|
| `SAFE` | 승인 게이트 없이 제안 목록에 포함, 사용자 승인 후 복사 진행 |
| `CAUTION` | 제안 목록에 포함하되 **확인 게이트 필수** — hit 요약을 제시하고 명시 승인 시에만 복사 |
| `RISKY` | **추천 후보에서 제외** — 복사하지 않는다 |
| `UNKNOWN`(라이선스 미확인 포함) | **확인 게이트 필수** — 라이선스·출처 불명 사실을 고지하고 명시 승인 시에만 복사 |
| 도구 실행 실패 / 미실행 | **[MUST] 설치를 진행하지 않는다** (R-4 AC) |

> 4단 판정 축과 명칭은 `docs/ARCHITECTURE.md` §커뮤니티 스킬("SAFE / CAUTION / RISKY / UNKNOWN 4단")을 그대로 따른다 — 신규 판정 체계를 만들지 않는다.
> [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." → 게이트는 `scan-risk` **도구 호출 결과**로 판정하며, 산문 판단으로 대체하지 않는다.

#### 3.3.4 환경 변경 / 3.3.5 배치

- 환경: 런타임 의존 = Node.js + `git`(clone) + `npx`(skills find). 신규 패키지 설치 없음.
- 배치: 해당 없음.

#### 3.3.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-1 AC | L3 정적 | SKILL.md에 모드 판별 표/절 1건 + 신규·기존 모드 절이 각각 별개로 존재 + 제안→승인→설치 3단이 순서대로 등장 |
| TS-012 | R-2 AC | L3 정적 | 재사용 PROJECT.md 항목 목록 / 부재 시 폴백 절차 / 결측 판정 기준 3항 전건 존재 |
| TS-013 | R-3 AC | L3 정적 | 검색 명령·clone 대상(임시)·복사 대상(프로젝트 경로) 각 1건 이상 + `opal-skill-manager` **호출 지시** 0건 |
| TS-014 | R-4 AC / H-8 | L3 정적 | `scan-risk` 호출이 복사 단계보다 **앞선 위치**에 존재 + 판정별 동작 표 존재 + 실패 시 미설치 규칙 명시 |

### F-004: 프로젝트 registry 스키마 정의 + 아키텍처 문서 반영

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/ARCHITECTURE.md` | 문서 | §커뮤니티 스킬 표 "레지스트리 (이원)" 행을 **스코프 3원**(프레임워크 카탈로그 / 사용자 등록분 / 프로젝트 스코프)으로 확장 + 프로젝트 설치 위치 행 추가 | `docs/ARCHITECTURE.md:196` / DEC-2 |

#### 3.4.2 데이터 모델 — 프로젝트 registry 스키마

**파일**: `{project}/.opal/skills-registry.json` (DEC-2)

**최상위 구조** — 기존 registry들과 동일하게 `groups` 맵을 갖는다. `flattenGroups()`(`:64-78`)가 `groups`를 순회하므로 이 형태를 벗어나면 병합되지 않는다.

```
{ "$schema": ..., "version": "1.0.0", "updated_at": "...", "groups": { "project": [ <항목>, ... ] } }
```

**항목 필드**

| 필드 | 필수 | 타입 | 내용 |
|------|------|------|------|
| `name` | ✅ | string | `{vendor}/{skill}` 정식명 — 병합 override 키 |
| `alias` | | string | 약어 (미지정 가능) |
| `description` | ✅ | string | 1줄 설명 |
| `triggers` | ✅ | string[] | 정규식 배열 — `matchByTriggers` 소비 |
| `domain` | | string | 도메인 라벨 |
| `source_repo` | ✅ | string | clone 출처 URL (R-7 "출처") |
| `commit_sha` | ✅ | string | clone 시점 commit (R-7 "commit") |
| `license` | ✅ | string | 라이선스 (미확인 시 `"Unknown"`) (R-7 "라이선스") |
| `trust` | ✅ | string | `SAFE`/`CAUTION`/`RISKY`/`UNKNOWN` (R-7 "보안 판정") |
| `capabilities` | | string[] | `scan-risk` active hit 요약 |
| `scanned_at` | ✅ | string | 스캔 시점 ISO8601 (R-7 "스캔 시점") |
| `installed_at` | ✅ | string | 복사 성립 시점 ISO8601 |

- **[MUST] `paths` 필드를 두지 않는다** — 프로젝트 스킬 경로는 `resolveProjectSkillPath()`가 `name`에서 동적 계산한다(DEC-2/3.1.2(c)). 이는 community 스킬의 "P-1: paths 폐기, name에서 계산" 규약(`skill-registry.js:95` 주석)과 동일 방향이다.
- **`validate` 통과 근거**: 판정·출처 필드는 카탈로그 스키마에 없는 필드이나, `docs/ARCHITECTURE.md` §커뮤니티 스킬이 명시한 "`validate`가 미지 필드를 무시하는 성질"을 이용한 additive 기록 방식을 그대로 따른다 → R-7 AC(`validate` error 0건) 충족.

#### 3.4.3 환경 변경 / 3.4.4 배치

해당 없음. 기존 프로젝트에 registry가 없는 것은 정상 상태이며 마이그레이션 대상이 아니다.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-7 AC | L2 통합 | 스키마를 따르는 프로젝트 registry에 대해 `validate` 실행 시 error 0건 |
| TS-016 | R-7 AC | L3 정적 | 필드 목록이 표로 존재하고 출처·commit·라이선스·보안 판정·스캔 시점 5항을 모두 포함 |

### F-005: `//` 라우팅 개정 + 레지스트리 등재·약어 배정

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/skill-commands.md` | 가이드 | 미설치 라우팅을 **3중 분기**로 개정 + `opal-skill-manager` 단독 지목 문장 제거(2곳) | `skill-commands.md:24` + §쌍슬래시 말미 / (→ ANALYSIS §7 Q10) |
| 2 | `opal/core/references/opal-skills-registry.json` | 문서 | `groups.opal`에 wizard 항목 추가 (alias `osw`) | DEC-7 / R-10 |

#### 3.5.2 설계

##### (a) `skill-commands.md` 라우팅 3중 분기 (확정 문안 구조)

| 조건 | 라우팅 |
|------|--------|
| `ambiguous: true` | (기존 유지) 후보 목록 표시 + 정식명 재호출 유도 — **소스 무관 공통 분기, 최우선 평가** |
| `scope === "project"` && `installed: false` | `opal-skill-wizard/SKILL.md` §설치 절차로 라우팅 (**신규 분기**) |
| `installed: false` (그 외 = community 전역) | (기존 유지) `opal-skill-manager/SKILL.md §6` 자동 설치·실행 |

- **[MUST] R-9 AC "`opal-skill-manager`만을 유일 경로로 지목하는 문장 0건"**: 기존 2개 문장(`:24`, §쌍슬래시 말미)을 **모두** 위 표 형태로 교체한다. manager는 "community 전역 분기의 경로"로 격하되어 단독 지목이 사라진다.
- `installed`·`ambiguous` 필드의 **기존 의미는 유지**된다 — project 스코프는 `scope` 신규 필드로 구분하므로 기존 소비자 회귀 0 (3.1.2(e)).

##### (b) `opal-skills-registry.json` 등재 항목

| 필드 | 값 |
|------|-----|
| `name` | `opal-skill-wizard` |
| `alias` | `osw` (DEC-7) |
| `description` | 프로젝트 적합 커뮤니티 스킬 제안 + 프로젝트 스코프 설치 (2모드: 신규 인터뷰 / 기존 PROJECT.md 재사용) |
| `triggers` | `["^opal-skill-wizard$", "^osw$"]` — 기존 13항목의 `^{정식명}$`/`^{alias}$` 2요소 패턴 준수 |
| `paths` | `["{project}/.opal/skills/opal-skill-wizard/SKILL.md", "~/.opal/skills/opal-skill-wizard/SKILL.md"]` — 기존 항목과 동일 2단 |
| `domain` | `skill` (`opal-skill-manager`/`opal-skill-creator`와 동일 도메인 라벨을 사용 — EXECUTE 시 실측 확인 후 정합) |
| 배치 | `groups.opal` 배열 **말미**에 append |

#### 3.5.3 환경 변경 / 3.5.4 배치

해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-017 | R-10 AC / H-9 | L2 통합 | `match "osw"` → `found:true` + `name: "opal-skill-wizard"` |
| TS-018 | R-10 AC | L2 통합 | 등재 후 전체 alias 중복 0건 (`validate` error 0건 포함) |
| TS-019 | R-9 AC | L3 정적 | `skill-commands.md`에 project 스코프 분기 존재 + manager 단독 지목 문장 0건 |

### F-006: 변경이력 행 추가

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/skill-commands.md` | 가이드 | 변경이력 v1.4 행 (114) | [MUST] `.opal/AGENT.md` §금지사항 |
| 2 | `opal/core/references/opal-skills-registry.json` | 문서 | `changelog` 배열 항목 추가 (`version` minor bump, `task: "114"`) + `updated_at` 갱신 | 동상 |
| 3 | `docs/ARCHITECTURE.md` | 문서 | 변경이력 표 행 (114) | 동상 |
| 4 | `opal/skills/opal-skill-wizard/SKILL.md` | 스킬 | 변경이력 표 v1.0 행 (114) | 동상 |

#### 3.6.2 설계

- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- 일시는 [MUST] `docs/CONVENTIONS.md` §네이밍 규칙: "`{YYMMDD}`는 `node ~/.opal/tools/date/date.js yymmdd`로 취득한다 (KST 기준, 추측 금지)." → 변경이력 일시도 동일 도구로 KST 실측 취득한다(추측 금지).
- `opal/tools/skill-registry/skill-registry.js`와 테스트 파일은 변경이력 표를 보유하지 않는 코드 파일이므로 대상 외 — 대신 함수 주석에 태스크 번호(114)를 남긴다(기존 관례: `:100` "태스크 064 F-001, H-1").

#### 3.6.3 환경 변경 / 3.6.4 배치

해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-11 AC | L3 정적 | 수정한 문서 4건 각각에 일시(KST)+태스크 번호(114)를 포함한 행이 정확히 1건 추가 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| P1 | F-004(스키마 확정) | Step 1 | 순차 | F-003의 선행 입력 |
| P2 | F-001 / F-002 (RED) | Step 2, Step 3 | 순차 | **RED-first** — Step 3(실패 테스트)이 Step 4(구현)에 선행 |
| P3 | F-001 (GREEN) | Step 4 | 순차 | RED 증거 확보 후 진입 |
| P4 | F-002 (회귀 검증) | Step 5 | 순차 | 기준선 41 pass 대조 |
| P5 | F-003 / F-004(문서) | Step 6, Step 7 | **병렬 가능** | 서로 다른 파일 |
| P6 | F-005 | Step 8, Step 9 | 병렬 가능 | 서로 다른 파일 |
| P7 | F-006 | Step 10 | 순차 | 전 문서 확정 후 일괄 |

### 4.2 실행 체크리스트

> 총 **10개 Step** | Phase **7개** | 실행 모드: **복잡** (§6 판정)
> 영역 라벨 `도구`는 DEC-6에 따른 임시 라벨(ANALYSIS H-1) — agent 배정은 범용 `opal-task-agent`.

#### Step 1: 프로젝트 registry 스키마 확정 + ARCHITECTURE.md 반영
- [x] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §커뮤니티 스킬 표의 "레지스트리 (이원)" 행을 스코프 3원(프레임워크 카탈로그 / 사용자 등록분 / **프로젝트 스코프 `{project}/.opal/skills-registry.json`**)으로 확장하고, 프로젝트 설치 위치 행(`{project}/.opal/community-skills/{vendor}/{skill}/SKILL.md`)을 추가한다. 스키마 12필드는 §3.4.2 표를 그대로 옮긴다.
- **완료 기준**: 표에 프로젝트 스코프 행이 존재하고, 출처·commit·라이선스·보안 판정·스캔 시점 5항이 필드 목록에 포함된다 (TS-016).
- **테스트**: TS-016
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: RED 테스트 fixture 골격 작성
- [x] 완료 **소속 기능**: F-002
- **영역**: 도구
- **agent**: `opal-test-agent` (mode: red)
- **파일**: `opal/tools/skill-registry/tests/test-project-registry.js` (신규)
- **작업 내용**: §3.2.2 격리 패턴(가짜 HOME + 가짜 프로젝트 cwd 이중 격리, `spawnSync`)으로 fixture 헬퍼를 작성한다. `getReferencesDir()` 1순위(cwd 소스 레이아웃) 회피 조건을 주석으로 명시한다.
- **완료 기준**: fixture 헬퍼가 가짜 HOME/프로젝트를 생성·정리하고, 최소 1개 스모크 테스트가 실행된다.
- **테스트**: (자체)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: RED — TS-001~TS-009 실패 테스트 작성·실행
- [x] 완료 **소속 기능**: F-002
- **영역**: 도구
- **agent**: `opal-test-agent` (mode: red)
- **파일**: `opal/tools/skill-registry/tests/test-project-registry.js`
- **작업 내용**: TS-001~TS-009를 구현한다. **[MUST] `get` 커버 3건(TS-004·TS-005·TS-006)을 반드시 포함**한다 — 기존 4파일의 `get` 커버가 0건이므로 유일한 안전망이다 (DEC-5 / ANALYSIS H-2·H-3).
- **완료 기준**: [MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입." → 실행 결과 exit code≠0과 실패 목록을 증거로 기록한다.
- **테스트**: TS-001~TS-009 (전건 RED)
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: GREEN — `skill-registry.js` 확장 구현
- [x] 완료 **소속 기능**: F-001
- **영역**: 도구
- **agent**: `opal-task-agent`
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: §3.1.2 (a)~(f) 6건을 구현한다 — `findProjectRoot()`(walk-up, 홈 경계 정지), `loadProjectRegistry()`(파손 시 `null`), `resolveProjectSkillPath()`, `loadAllSkills()` 4번째 병합, `matchCommand()` project 분기(+`scope` 필드), `getCommand()` `resolved_path` additive 필드.
- **완료 기준**: TS-001~TS-009 전건 GREEN. **[MUST] 기존 3소스 병합 코드 무수정**(additive 한정, TASK.md §제약) — `git diff`에서 기존 `loadAllSkills()` 3소스 라인이 변경되지 않음이 확인된다.
- **테스트**: TS-001~TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3 (RED 증거 확보 후)

#### Step 5: 회귀 기준선 대조
- [x] 완료 **소속 기능**: F-002
- **영역**: 도구
- **agent**: `opal-test-agent`
- **파일**: `opal/tools/skill-registry/tests/` (기존 4파일 무변경, 실행만)
- **작업 내용**: cwd = 리포지토리 루트(`/Volumes/Data/AiStudio/workspace/opal`)에서 `node opal/tools/skill-registry/tests/{test-match,test-validate,test-migrate,test-scan-risk}.js`를 개별 실행한다.
- **완료 기준**: **회귀 기준선 41 pass / 0 fail**(test-match 11 / test-validate 5 / test-migrate 9 / test-scan-risk 16, cwd 리포지토리 루트, 4파일 개별 실행 — ANALYSIS §1.4 실측)과 **동일**하다. fail 1건이라도 발생하면 R-8 미완료로 판정한다. 신규 파일 pass 수는 이 기준선에 가산 기록한다.
- **테스트**: TS-010
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: `opal-skill-wizard/SKILL.md` 작성
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-skill-wizard/SKILL.md` (신규)
- **작업 내용**: §3.3.2 목차 표의 frontmatter + §진입 훅 + §0~§9 + §변경이력을 작성한다. §4 판정별 동작은 §3.3.3 표를 그대로 게재하고, §7 위임 페이로드는 `opal/skills/opal-skill-manager/SKILL.md:92-102`의 7필드를 재사용한다. §8에 §3.4.2 스키마 표를 게재한다.
- **완료 기준**: TS-011~TS-014 전건 통과 — 특히 **`scan-risk` 호출이 복사 단계보다 앞선 위치**(H-8)이고, **`opal-skill-manager` 호출 지시 0건**(R-3 AC)이다.
- **테스트**: TS-011, TS-012, TS-013, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 7: 프로젝트 registry `validate` 정합 확인
- [x] 완료
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: `opal-test-agent`
- **파일**: `opal/tools/skill-registry/tests/test-project-registry.js` (TS-015 추가)
- **작업 내용**: §3.4.2 스키마를 따르는 fixture registry에 대해 `validate` 서브커맨드를 실행하는 테스트를 추가한다.
- **완료 기준**: `validate` error 0건 (TS-015). R-7 AC 충족.
- **테스트**: TS-015
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 6

#### Step 8: `skill-commands.md` 라우팅 3중 분기 개정
- [x] 완료
- **소속 기능**: F-005
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/skill-commands.md`
- **작업 내용**: §3.5.2(a) 표대로 3중 분기(ambiguous → project → community)로 교체한다. `:24`와 §쌍슬래시 커맨드 말미 **2곳 모두**를 대상으로 한다.
- **완료 기준**: project 스코프 분기가 존재하고, `opal-skill-manager`를 유일 경로로 지목하는 문장이 **0건**이다 (TS-019). `installed`/`ambiguous` 기존 의미 서술은 유지된다.
- **테스트**: TS-019
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 6

#### Step 9: `opal-skills-registry.json` wizard 등재
- [x] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: §3.5.2(b) 표대로 `groups.opal` 말미에 항목을 append하고 `updated_at`을 갱신한다. `domain` 값은 `opal-skill-manager`/`opal-skill-creator`의 실측 `domain`과 정합시킨다.
- **완료 기준**: `node opal/tools/skill-registry/skill-registry.js match "osw"` → `found:true` + `name:"opal-skill-wizard"` (TS-017), `validate` error 0건 + alias 중복 0건 (TS-018).
- **테스트**: TS-017, TS-018
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 10: 변경이력 행 일괄 추가 (docs/ 갱신 포함)
- [x] 완료 **소속 기능**: F-006
- **영역**: 문서
- **agent**: **PM 직접** (docs/ 갱신 Step — op-dev-plan SKILL.md §docs/ 갱신 Step 자동 생성 규칙)
- **파일**: `docs/ARCHITECTURE.md`, `opal/core/references/harness/skill-commands.md`, `opal/core/references/opal-skills-registry.json`, `opal/skills/opal-skill-wizard/SKILL.md`
- **작업 내용**: 4개 문서에 114 태스크 행을 추가한다. 일시는 [MUST] `docs/CONVENTIONS.md` §네이밍 규칙("`node ~/.opal/tools/date/date.js yymmdd`로 취득한다 (KST 기준, 추측 금지)")에 따라 도구로 실측 취득한다. `opal-skills-registry.json`은 `changelog` 배열에 `version` minor bump + `task: "114"`으로 추가한다.
- **완료 기준**: 4개 문서 각각에 일시(KST)+태스크 번호(114) 행이 정확히 1건씩 추가되고, JSON은 `validate` error 0건을 유지한다 (TS-020).
- **테스트**: TS-020
- **실행 방법**: direct
- **의존**: Step 1, Step 6, Step 8, Step 9

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 서로 다른 파일(`docs/ARCHITECTURE.md` vs 신규 테스트), 의존 없음 |
| Step 3 → Step 4 | [MUST] `red-first.md` §1 RED→GREEN 순서 — RED 증거 없이 GREEN 진입 금지 |
| Step 4 → Step 5 | 회귀 기준선 대조는 구현 반영 후에만 의미가 있다 |
| Step 1 → Step 6 | wizard §8이 F-004 스키마를 게재하므로 스키마 확정이 선행 |
| Step 6 ∥ Step 8 ∥ Step 9 | 3개 모두 서로 다른 파일. 단 Step 8·9는 Step 6(wizard 실존)에 의존 — 라우팅·등재가 가리키는 대상이 존재해야 한다 |
| Step 4 → Step 8 | 라우팅 분기가 `scope` 신규 필드에 의존 (§3.1.2(e)) |
| Step 10 최후 | 변경이력은 대상 문서가 모두 확정된 뒤 일괄 기재 — 중간 재작성 시 행 중복 위험 |
| 동일 파일 동시 편집 없음 | Step 4·Step 7만 `skill-registry.js`/테스트 파일을 만지며 Step 7은 Step 4 이후로 직렬화 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 프로젝트 registry 병합 동작 | TS-001 | `match "{name}"` → `found:true` |
| F-001 | 부재·파손 내성 (CLI 다운 방지) | TS-002, TS-003 | exit 0 + 전역 3소스 결과 유지 |
| F-001 | `get` `resolved_path` 해석 | TS-004, TS-005 | 설치 시 절대경로 / 미설치 시 `null` |
| F-001 | `get` 하위호환 (기존 필드 보존) | TS-006 | main 스킬 `paths` 배열 원형 유지 |
| F-001 | walk-up / 홈 경계 | TS-007, TS-008 | 하위 디렉토리 성공 / `$HOME` 하위 오인 0건 |
| F-001 | override 우선순위 | TS-009 | 동명 충돌 시 project 정의 반환 |
| F-002 | 기존 테스트 무회귀 | TS-010 | **41 pass / 0 fail** 기준선 동일 |
| F-003 | SKILL.md 구조 요건 | TS-011, TS-012 | 모드 판별·2모드 절·3단 흐름·PROJECT.md 계약 존재 |
| F-003 | manager 비호출 + 검색·설치 절차 | TS-013 | 호출 지시 0건 + 검색/clone/복사 각 1건 이상 |
| F-003 | `scan-risk` 게이트 위치·판정표 | TS-014 | 복사 단계보다 앞 + 판정별 동작 표 + 실패 시 미설치 |
| F-004 | 스키마 `validate` 정합 | TS-015 | error 0건 |
| F-004 | 스키마 필드 완결성 | TS-016 | 출처·commit·라이선스·판정·스캔시점 5항 포함 |
| F-005 | wizard 매칭 | TS-017, TS-018 | `match "osw"` 성공 + alias 중복 0 |
| F-005 | 라우팅 개정 | TS-019 | project 분기 존재 + manager 단독 지목 0건 |
| F-006 | 변경이력 | TS-020 | 4개 문서 각 1행 |

> 전 F-001~F-006이 최소 1개 QA 항목으로 커버됨 (미커버 0건).

### 5.2 회귀 테스트

- [ ] 기존 4개 테스트 파일 개별 실행 결과가 **41 pass / 0 fail** (cwd 리포지토리 루트) — R-8 완료 판정 기준선
- [ ] 프로젝트 registry 부재 환경에서 `list`/`match`/`get`/`validate` 출력이 변경 전과 동일
- [ ] `list` 최상위 반환 타입이 배열로 유지 (`dashboard/backend/adapters/skill_adapter.py:53-75` 소비 계약)
- [ ] `--group=community` 필터 결과에 `_source:'project'` 항목이 섞이지 않음 (ANALYSIS H-7)
- [ ] `opal-skill-manager` / `opal-help` SKILL.md 절차가 참조하는 `match`/`get`/`list` 필드가 전건 잔존

### 5.3 코드/문서 품질

- [ ] [MUST] `.opal/AGENT.md` §업무 수행 지침: "`~/.opal/` 배포 파일을 직접 수정하지 않는다." — 변경 파일이 전부 `opal/`·`docs/` 프로젝트 소스인가
- [ ] [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지" — 신규 코드·문서에 Claude/Cursor/Gemini/codex 분기 0건
- [ ] [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names." — `analysis-core.md` 미수정(DEC-6), 기존 3소스 병합 코드 미수정
- [ ] [MUST] `docs/CONVENTIONS.md` §네이밍 규칙: "전문 에이전트 네이밍: `opal-{domain}-agent`" — 신규 컴포넌트 명명이 기존 체계(`opal-skill-{역할}`)와 정합
- [ ] 신규 함수에 태스크 번호 주석(114) 기재 (기존 관례: `skill-registry.js:100` "태스크 064 F-001, H-1")
- [ ] 변경이력 4건 누락 0

### 5.4 보안

- [ ] `resolveProjectSkillPath()`가 `path.resolve` 정규화 후 **프로젝트 루트 하위인지 검증**한다 — CWE-22 path traversal 방어. `resolveFirstPath()`의 homedir/cwd 하위 검증(`skill-registry.js:236-241`)과 동일 방어를 프로젝트 루트에 적용
- [ ] 프로젝트 registry의 `name` 값에 `../` 등 경로 이탈 시퀀스가 있어도 루트 밖 파일을 반환하지 않음
- [ ] `findProjectRoot()` walk-up이 홈 디렉토리를 넘어 상향하지 않음 (H-4) — 타 사용자 홈·시스템 디렉토리 접근 차단
- [ ] wizard 설치 흐름에서 `scan-risk` 게이트 우회 경로 0건 (H-8) — 실패·미실행 시 설치 중단
- [ ] clone 대상이 임시 디렉토리이며 clone 자체가 설치가 아님이 문서에 명시 (승인 게이트 = 복사 직전 1회)
- [ ] 프로젝트 registry 파손 JSON이 CLI 예외로 전파되지 않음 (DoS 방지, H-2)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 10개 | 복잡 (>5) |
| 변경 파일 수 | 6개 (신규 2 / 수정 4) | 복잡 |
| 모듈 범위 | 다중 — 도구(CLI 코드) + 스킬 + 참조 가이드 + 레지스트리 JSON + 아키텍처 문서 | 복잡 |
| 작업 유형 | 신규 컴포넌트 신설 + 공유 로더 계약 확장 | 복잡 |
| 외부 의존성 | 없음 (Node.js 내장만, 신규 패키지 0) | 단순 |
| **실행 모드** | **복잡** | 5기준 중 4개 복잡 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
[P1]  Step 1  (opal-task-agent, docs)      ┐
[P2]  Step 2 → Step 3 (opal-test-agent RED) ┘  ← 병렬 착수
[P3]           Step 4 (opal-task-agent, GREEN)
[P4]           Step 5 (opal-test-agent, 회귀)
[P5]  Step 6  (opal-task-agent, wizard SKILL.md)
[P6]  Step 7 (opal-test-agent) ∥ Step 8 (opal-task-agent) ∥ Step 9 (opal-task-agent)
[P7]  Step 10 (PM 직접, 변경이력·docs)
```

- 배치 실행 순서: `{Step1, Step2}` → `{Step3}` → `{Step4}` → `{Step5, Step6}` → `{Step7, Step8, Step9}` → `{Step10}`
- **[MUST] 생성자≠검증자 분리**: RED 테스트(Step 2·3·5·7)는 `opal-test-agent`, 구현(Step 4·6·8·9)은 `opal-task-agent` — `red-first.md` §1.5 공통 불변 ②.

### C-2. 스킬 요구사항

| 필요 역량 | 매칭 스킬 | 갭 |
|----------|----------|-----|
| 프레임워크 코드 구현 | `op-dev-execute` (opal-task-agent 경유) | 없음 |
| RED 테스트 작성 | `op-dev-test` / `opal-test-agent(mode: red)` | 없음 |
| 스킬 문서 신설 | `opal-skill-creator` — **이번엔 사용하지 않는다**. wizard는 OPAL 전용 스킬 신설이며 기존 스킬 포맷 모사로 충분 | 없음 |

### C-3. 도구 요구사항

| 도구 | 용도 |
|------|------|
| `node` (내장 `node:test`) | 테스트 실행 — 별도 러너·패키지 없음 |
| `node opal/tools/skill-registry/skill-registry.js` | `match`/`get`/`list`/`validate` 검증 |
| `node ~/.opal/tools/date/date.js yymmdd` | 변경이력 일시 KST 실측 (추측 금지) |
| `~/.opal/tools/state-tool/run.sh verify --red-check` | RED-first 트랙 집행 (red-first.md §1.5) |

- MCP 사용 없음. 외부 네트워크 의존 없음(EXECUTE 시점 기준 — wizard **런타임**은 `npx skills find`·`git clone`을 쓰지만 이는 구현 대상 문서 내용이지 EXECUTE 자체의 의존이 아니다).

### C-4. 테스트 전략

- **L1(단위)**: `findProjectRoot()`/`resolveProjectSkillPath()`의 경계 조건 — 홈 경계·FS 루트·32단 상한.
- **L2(통합, 주 계층)**: `spawnSync` 실 CLI 프로세스 + 실 fs fixture. 프로젝트 registry 유/무/파손 3케이스 × `match`/`get`/`validate`. **본 태스크 검증의 중심**이며 기존 4파일의 격리 패턴을 그대로 재사용한다.
- **L3(정적/E2E)**: 문서 요건 검사(TS-011~TS-014, TS-016, TS-019, TS-020) — `grep` 기반 존재·부재·순서 단정.
- **RED-first 집행**: F-001/F-002는 Step 3에서 exit code≠0 증거 확보 후 Step 4 진입. `verify --red-check` ON.
- **회귀 판정**: R-8 완료는 **기존 4파일 41 pass / 0 fail 유지 + 신규 파일 전건 pass** 두 조건의 AND.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구(CLI) | Node.js CommonJS (단일 파일, 순수 함수) | 해당 없음 (프레임워크 내부 코드) |
| 테스트 | Node.js 내장 `node:test` + `spawnSync` 실 프로세스 | `op-dev-test` |
| 문서 | Markdown (SKILL.md·references) | `op-dev-execute` |
| 설정 | JSON 레지스트리 | 해당 없음 |
| 배포 | Bash (`scripts/install-mac.sh`) — **이번 무변경** | 해당 없음 |

> 프로젝트 루트에 `package.json`·`pyproject.toml`·`go.mod`·`Cargo.toml` 부재 — 패키지 매니저 비의존 (TASK.md §기술 스택).
> op-dev-plan SKILL.md §Step 2의 활용 스킬 표(React/Next.js/Python/shadcn/FE 설계)는 **해당 스택 0건**이므로 Read 대상 없음.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 API 조회 불필요 — 신규 외부 의존 0건 (→ ANALYSIS §6.4) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 전역 설치 경로 규칙·clone-copy 승인 게이트·위임 페이로드 7필드 (DEC-2, F-003 §5·§7) |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 로더·경로 해석·`match`/`get`/`list` 현행 구현 (DEC-1·3·5, F-001 전체) |
| D-3 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | `//` 라우팅·`installed` 필드 의미 (F-005) |
| D-4 | 설계 | opal-project-init SKILL.md | `opal/skills/opal-project-init/SKILL.md` | 2모드 판별·인터뷰 골격 (F-003 §0~§2) |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 네이티브 skills/ 레거시 지정, 프로젝트 `.opal/` 무접촉 (DEC-2 install 안전성) |
| D-6 | 설계 | 프로젝트 PM 프로필 | `.opal/AGENT.md` | 배포 경계·플랫폼 분기 금지·변경이력 의무 (§5.3, F-006) |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | Core Stance(도구 집행)·§2 Simplicity·§3 Surgical (DEC-1·2·4·6) |
| D-8 | 외부 | skills.sh | [skills.sh](https://skills.sh/) | 커뮤니티 스킬 검색 소스 (F-003 §3) |
| D-10 | 설계 | opal-skill-creator SKILL.md | `opal/skills/opal-skill-creator/SKILL.md` | 위임 진입 모드·Capture Intent 입력 대응 (F-003 §7) |
| D-11 | 설계 | docs/ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 커뮤니티 스킬 4단 판정·이원 registry·`validate` 미지 필드 무시 성질 (DEC-2, F-004) |
| D-12 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | §1 RED→GREEN·§1.5 하이브리드 자동분기 (§1.4 트랙 판정) |
| D-13 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2.2 원문 전사 금지·§4 PLAN 인용 요건 |
| D-14 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍 규칙(KST 일시 도구 취득)·State 도구 규율 (§5.3, Step 10) |
| D-15 | 설계 | analysis-core.md | `opal/core/references/harness/analysis-core.md` | §5 영역 축 — "도구" 라벨 부재(DEC-6 이월 근거) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1.
> [MUST] `opal/core/references/harness/citation-rules.md` §2.2: "ANALYSIS·PLAN 등 산출물에 소스코드 원문 블록을 기재하지 않는다. 대체: `경로:줄번호` 인용 + 필요 시 1~3줄 약식 발췌까지만 허용한다." → 본 PLAN은 §3.1.2에서 의사코드 수준 서술만 사용하고 원문 블록을 전사하지 않았다.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | `loadAllSkills()` 확장이 7개 서브커맨드 전체에 파급 (→ ANALYSIS §1.3) | F-001 | 높음 | additive 한정 + Step 5 기준선(41 pass) 대조를 완료 조건으로 강제 |
| 2 | `get` 계약 변경으로 문서 절차(`opal-help`·`opal-skill-manager`) 무효화 (H-3) | F-001 | 중간 | DEC-5 additive 필드 방식 — 기존 필드 삭제·의미 변경 0. TS-006이 보존을 단정 |
| 3 | walk-up이 홈·시스템 디렉토리로 상향 (H-4) | F-001 | 높음(보안) | 홈 경계 정지 + FS 루트 + 32단 상한 3중 종료 조건. TS-008 |
| 4 | 프로젝트 registry 파손 JSON이 CLI 전체를 다운 (H-2) | F-001 | 높음 | `loadUserRegistry()` 동형 try/catch → `null`. TS-003 |
| 5 | `scan-risk` 게이트가 산문 권고에 그쳐 우회 (H-8) | F-003 | 중간 | 절 순서로 강제(복사 직전) + 실패 시 미설치 [MUST] 규칙 + TS-014 정적 검사 |
| 6 | `opal-skills-registry.json` JSON 파손 시 전 스킬 매칭 불가 (H-9) | F-005 | 높음 | Step 9 완료 조건에 `validate` error 0건 + `match "osw"` 성공 포함 |
| 7 | 프로젝트 registry `name`의 경로 이탈 시퀀스 (CWE-22) | F-001 | 중간 | `path.resolve` 정규화 + 프로젝트 루트 하위 검증 (§5.4) |
| 8 | `dashboard` adapter 회귀 (`list` 타입 계약) | F-001 | 낮음 | DEC-4로 신규 필드 미도입 + 배열 타입 유지. §5.2 회귀 항목 |

### 후속 개선 제안 (이번 범위 밖 — 이월)

| # | 제안 | 이월 근거 |
|---|------|----------|
| R-1 | `opal/core/references/harness/analysis-core.md` §5 축에 "도구(CLI 코드)" 라벨 추가 | DEC-6 — [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." 축 개정은 전 pilot 산출물 포맷에 파급되므로 별도 태스크의 영향 분석 필요 |
| R-2 | `list` 응답의 섀도잉 가시성(`shadowed_by` 등) | DEC-4 — TASK.md §완료기준에 요구 없음. [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First |
| R-3 | `listCommand()` `--group=project` 필터 옵션 | ANALYSIS H-7 — R-5/R-6 범위 밖의 잠재 확장 |


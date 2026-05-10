# QA: PLAN — OPAL 보안 강화 (태스크 144)

> 검토일: 2026-05-10 | 판정: Pass (with minor warnings)

---

## 1. 요약

PLAN.md는 GC-SECURITY 보고서의 High 4건(GC-001~004) + Medium 핵심(GC-006/007/010) + Info GC-014(SECURITY.md 신설)를 16개 Step / 8 Phase로 분해한 실행 계획이다. TASK.md R-1~R-9가 Step 1~16에 빠짐없이 매핑되었으며, 캡틴 SSOT(§0)는 변경 없이 승계되었다. 미확정 사항 P-D-1~P-D-8은 모두 디폴트 또는 명시적 이유와 함께 결정되었고, PLAN 작성 중 신설된 P-D-9~P-D-11도 근거와 함께 기재되었다. 주요 경고 사항: §3 헤더가 Step 16개 / Phase 8개임에도 "총 13개 Step / Phase 6개"로 잘못 기재됨 (오타 수준). R-5 ReDoS 거짓양성 분석에서 `react-components` 패턴(`.*` 실제 2회)을 1회로 잘못 계산하여 "통과"로 결론내린 점이 EXECUTE 전 반드시 재검토해야 할 Warning이다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | Step별 파일 경로 / agent / 작업 내용 / 완료 기준 / 테스트 / AC 매핑 모두 명시. EXECUTE 진입 즉시 가능 |
| GP-2 | 의존성 순서 | Pass | 레지스트리/스키마(Phase 1-2) → 도구(Phase 3-4) → install 본체(Phase 5-6) → SECURITY.md(Phase 7) → 회귀 검증(Phase 8) 순서 정확 |
| GP-3 | TASK 반영 | Pass | R-1→Step 15, R-2→Step 12-14, R-3→Step 5-6, R-4→Step 9-11, R-5→Step 7, R-6→Step 1-4, R-7→Step 2, R-8→Step 8-11, R-9→Step 16. 9개 요구사항 전부 매핑 |
| GP-4 | 파일 목록 완전성 | Pass | 신규 1 + 수정 14 = 총 15 파일. TASK.md §제약 조건의 변경이력 의무 대상 파일과 일치 |
| GP-5 | 설계 구체성 | Pass | 각 파일별 의사코드(bash/PowerShell), 설계 결정 근거, 인용 번호 포함. EXECUTE에서 추가 설계 없이 직접 구현 가능 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 Step 1-16이 R-1~R-9 모두 커버. §4 QA 체크리스트도 R-1~R-9 + 4.2 일관성 + 4.3 문서 품질 + 4.4 컨벤션 4개 섹션 |
| SEC-1 | GC-001 매핑 (install 무결성) | Pass | Step 12/13/14 (install.sh / install.ps1 / update.sh) — 비대화형 거부 + OPAL_ALLOW_UNVERIFIED=1 + main banner 설계 완비 |
| SEC-2 | GC-002 매핑 (third-party fetch) | Pass | Step 5 (registry v2.1 + commit_sha) + Step 6 (SKILL.md prompt 강화) — Unknown 두 번째 확인 텍스트(P-D-3) 명시 |
| SEC-3 | GC-003 매핑 (MCP spawn) | Pass | Step 9/10/11 (mcp.sh + install-mac.sh + windows.ps1) — command 화이트리스트 bash/PowerShell 의사코드 모두 포함. fork banner P-D-2 결정 명시 |
| SEC-4 | GC-004 매핑 (ReDoS) | Warning | Step 7 설계 자체는 완비. 단 §2 거짓양성 분석(L457)이 `react-components` 패턴의 `.*` 카운트를 1로 잘못 기재 — 실제 2회이므로 MAX_DOTSTAR_COUNT=2 조건에서 reject됨. 임계값 재검토 필요 (상세: §3 지적 사항 W-1) |
| SEC-5 | GC-006 매핑 (MCP 핀) | Pass | Step 1-4. semver `^x.y` 형식 + npm registry 버전 근거(D-26) 명시 |
| SEC-6 | GC-007 매핑 (/tmp 경로) | Pass | Step 2. playwright `~/.opal/cache/playwright-mcp` + install이 0700 mkdir 보장 + `~` expand 처리 설계 포함 |
| SEC-7 | GC-010 매핑 (OPAL_HOME 가드) | Pass | Step 8/10/11. bash `pwd -P` 정규화 + PowerShell `GetFullPath` 비교 + OPAL_HOME_OVERRIDE=1 옵트인 |
| SEC-8 | GC-014 매핑 (SECURITY.md) | Pass | Step 15. 6 섹션 골격 + GC-DP-001~005 매핑 + docs 면제 선례 인용 |
| SEC-9 | Low/Medium 후속 분리 | Pass | GC-005/008/009/011/012 후속 분리 + TASK.md §확정된 설계 방향 §8 인용. GC-013은 Step 7에 보너스 포함 |
| SSOT-1 | §0 캡틴 SSOT 정합 | Pass | §0 표의 0.1~0.8이 TASK.md §1~§10을 변경 없이 승계. [MUST] 제약 재확인 |
| SSOT-2 | P-D-1~P-D-8 결정 완료 | Pass | 8개 모두 결정. P-D-1만 "main 분기 banner-only" 세부 결정 추가 (TASK 디폴트와 정합). P-D-9~P-D-11 신설 결정도 근거 포함 |
| VER-1 | MCP 핀 버전 semver 정합성 | Warning | D-26(npm registry 기준) 인용하여 shadcn@^4.7 / @playwright/mcp@^0.0.75 / @upstash/context7-mcp@^2.2 / server-sequential-thinking@^2025.12 명시. 단, `^2025.12` 캘린더 버전의 npm semver 호환성 미검증 — §5 R-3 리스크로 기재되어 있으나 EXECUTE 전 `npm view @modelcontextprotocol/server-sequential-thinking` 실제 검증 권장 |
| CHG-1 | 변경이력 의무 파일 처리 | Pass | install.sh/install.ps1/install-mac.sh/install/windows.ps1/update.sh/uninstall.sh/mcp.sh/skill-registry.js/opal-skill-manager SKILL.md — 9개 파일 모두 Step에 행 추가 명시 |
| CHG-2 | 변경이력 면제 처리 | Pass | SECURITY.md (docs 면제) + 4개 mcps/*.json (JSON config 면제) — D-9 141 선례 인용. playwright.json은 TASK §제약 조건에서 명시적으로 면제 |
| CHG-3 | community-skills-registry.json 갈음 | Pass (decision_required) | `schema_notes` 필드에 (144) 태스크 번호 명시로 갈음 — P-D-9로 PM 게이트 에스컬레이션 적절. TASK.md §제약 조건과의 긴장관계가 §5 R-7 리스크에 명시됨 |
| OS-1 | mac/Windows 동등 처리 | Pass | Step 10(install-mac.sh) + Step 11(install/windows.ps1) 동등 화이트리스트 + fork banner + OPAL_HOME 가드. §4.2 일관성 테스트에도 항목화 |
| REG-1 | 회귀 검증 충실성 | Pass | Step 16이 install / claude mcp list / //pdf 매칭 / opal-cli doctor / OPAL_HOME 거부 5개 시나리오 + 구체 명령 포함. R-9 AC (1)~(5) 모두 커버 |
| AGENT-1 | agent 라우팅 | Pass | 모든 Step `opal-task-agent` — PROJECT.md L79 "Framework 영역 → opal-task-agent(범용)" 정합 |
| META-1 | §3 Step/Phase 카운트 오타 | Warning | L491 "총 13개 Step / Phase 6개" 기재 — 실제 Step 16개 / Phase 8개. Phase 표(L493-502)와 §4 실행 구성(L957-965)도 불일치. 가독성 혼란 유발 가능 (상세: §3 지적 사항 W-2) |
| CONV-1 | 용어 일관성 | Pass | §5 R-T1에서 OPAL_HOME(bash) vs OpalHome(PowerShell) 불일치를 명시하고 `$env:OPAL_HOME` 통일 방안 기술. 환경 변수 토큰은 양 OS 동일 |

---

## 3. 지적 사항

### W-1 [Warning] ReDoS 거짓양성 분석 오류 — react-components 패턴 `.*` 카운트 불일치

**위치**: PLAN.md §2 핵심 설계 M-10 "거짓양성 영향 분석" (L457)

**현상**: `google-labs-code/react-components`의 trigger 패턴 `(?i)(stitch.*react|react\s*component.*stitch)`에 대해 PLAN이 "`.*` 1회 + `\s*` 1회 → 미위험 (DOTSTAR_COUNT=1)"로 분석하고 "통과"라고 결론내렸다.

**실제 분석**: `(?i)` prefix를 제거한 패턴 `(stitch.*react|react\s*component.*stitch)` 내에서 `\.[*+]` 패턴을 적용하면 `.*`가 2회 검출된다 (`stitch.*react`의 `.*`와 `react\s*component.*stitch`의 `.*`). Python 검증 결과 `['.*', '.*']` count=2.

**영향**: `isUnsafeRegex` 함수가 `dotStarCount >= MAX_DOTSTAR_COUNT(2)` 조건에서 이 패턴을 reject하게 된다. 결과적으로 `//react-components` 계열 커뮤니티 trigger가 작동하지 않아 기능 회귀가 발생한다.

**권장 조치 (캡틴 결정 필요)**: 다음 중 하나를 선택해야 한다.

1. `MAX_DOTSTAR_COUNT`를 3으로 상향 (완화) — `.*`가 3회 미만이면 통과
2. `>=` 대신 `>` 비교로 변경 — `.*`가 정확히 2회는 통과, 3회 이상 reject
3. `isUnsafeRegex`의 카운트 대상을 `/\.\*/g` (`.{*}` 리터럴만)로 한정 — `\s*`는 제외하고 `.*`만 카운트 (현재 의사코드는 `/\.[*+]/g`)
4. 임계값을 유지하되 해당 패턴에 대해 community-skills-registry.json에서 수동 검증 후 경고 marking

**심각도**: Warning (기능 회귀 가능성 — EXECUTE 전 결정 필요)

---

### W-2 [Warning] §3 헤더 Step/Phase 카운트 오타

**위치**: PLAN.md §3 첫 줄 L491 `> 총 13개 Step | Phase 6개`

**현상**: 실제 Step은 16개(Step 1~16), Phase는 8개(Phase 1~8)이다. L493-502 Phase 표에도 Phase 7(Step 16: SECURITY.md) / Phase 8(Step 17: 회귀 검증)이 포함되어 있으며, §4 종합 실행 구성(L957-965)은 "8 Phase"로 올바르게 기재되어 있다. L498의 Phase 4 비고에 "mcp.sh + (없음 — Step 11/12로 통합)" 기재와 실제 Step 9/10으로의 번호 변경이 있어 Step 구성이 중간에 변경되면서 헤더 수치를 갱신하지 않은 것으로 보인다.

**영향**: EXECUTE 워커가 총 Step 수를 혼동할 가능성. Phase 표 자체는 8행이고 §4 실행 구성이 정확하므로 직접적인 실행 오류 위험은 낮음.

**권장 조치**: L491을 `> 총 16개 Step | Phase 8개`로 수정. EXECUTE 진입 전 또는 캡틴 검토 시 간단히 수정 가능.

**심각도**: Warning (가독성 혼란, 실행 오류 위험 낮음)

---

### I-1 [Info] MCP sequential-thinking 캘린더 버전 핀 npm 호환성

**위치**: PLAN.md §2 M-11~M-14 / §5 R-3 리스크

**현상**: `@modelcontextprotocol/server-sequential-thinking@^2025.12`는 캘린더 버전이다. npm semver 규칙에서 `^2025.12`는 `>=2025.12.0 <2026.0.0`으로 파싱된다. 패키지가 실제로 이 범위로 배포되어 있는지는 런타임 확인이 필요하다. §5 R-3 리스크에 "EXECUTE 시 확인" 명시 — 리스크 처리는 적절.

**영향**: EXECUTE 중 `npm install` 실패 가능성. §5에서 인지하고 있으므로 추가 조치 불필요.

**심각도**: Info

---

### I-2 [Info] P-D-9 — community-skills-registry.json 변경이력 면제 PM 게이트

**위치**: PLAN.md §7 P-D-9 / §5 R-7

TASK.md §제약 조건이 명시적으로 `community-skills-registry.json`을 변경이력 의무 대상에 포함시켰으나, JSON 파일 특성상 `## 변경이력` 표를 둘 수 없으므로 `schema_notes` 필드로 갈음하는 결정이다. PLAN이 PM 게이트 에스컬레이션(`decision_required`)으로 처리한 방식은 적절하다. QA 관점에서: `schema_notes`에 `(144)` 태스크 번호가 포함되어야 CONVENTIONS.md §변경이력 작성 의무의 "태스크 번호 괄호 포함" 요건을 충족할 수 있다. PLAN Step 5에 "v2.1: commit_sha 옵션 필드 신설 (144)" 형식으로 명시됨 — 충분.

**심각도**: Info (PM 결정 대기 중, QA 추가 조치 불필요)

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-9 | PLAN Step 1-16 1:1 매핑 완전성 | Pass |
| TASK.md §확정된 설계 방향 §1~§10 | PLAN §0 캡틴 SSOT 표 정합 (변경 없음) | Pass |
| TASK.md §미확정 사항 P-D-1~P-D-8 | PLAN §7 결정 결과 전수 | Pass |
| TASK.md §제약 조건 "변경이력 의무" | PLAN 파일별 Step 변경이력 행 명시 / 면제 처리 | Pass (W-note: community-skills-registry.json P-D-9) |
| TASK.md §제약 조건 "mac/Windows 동등 처리" | PLAN Step 10/11 OS 동등 처리 + §4.2 일관성 항목 | Pass |
| GC-SECURITY §3 High 4건 (GC-001~004) | PLAN SEC-1~SEC-4 매핑 | Pass (W: SEC-4 거짓양성 오류) |
| GC-SECURITY §3 Medium 핵심 (GC-006/007/010) | PLAN SEC-5~SEC-7 매핑 | Pass |
| GC-SECURITY §5 SECURITY.md 골격 | PLAN §2 N-1 + Step 15 내용 정합 | Pass |
| GC-SECURITY Low (GC-009/011/012) + Medium GC-005/008 | 후속 분리 명시 (§확정된 설계 방향 §8) | Pass |
| 142 DONE.md (community-skills-registry v2) | PLAN v2.1 minor bump + skill-registry.js v2/v2.1 양쪽 인식 | Pass |
| 141 DONE.md (docs/JSON config 면제 선례) | PLAN D-9 인용 — SECURITY.md + playwright.json 면제 | Pass |
| PROJECT.md Framework 영역 | PLAN 모든 Step `opal-task-agent` 폴백 | Pass |

---

## 5. 판정

**Pass (pass_with_minor)**

PLAN.md는 TASK.md R-1~R-9를 Step 1-16에 빠짐없이 매핑했고, GC-SECURITY 14건과의 scope 처리(High 4 + Medium 핵심 포함 / Low 3 + Medium 2 후속 분리)가 캡틴 결정과 정합하며, 설계 구체성(의사코드 + 완료 기준 + 테스트 시나리오)이 충분하다. 두 개의 Warning이 있으나 어느 쪽도 EXECUTE 진입 자체를 차단하지는 않는다. 단, W-1(ReDoS 거짓양성 분석 오류)은 EXECUTE 시작 전 임계값 결정이 필요하다.

---

## 6. PM 보고 — 캡틴 결정 필요 사항

### 필수 결정 (EXECUTE 진입 전)

**[W-1] ReDoS 임계값 재결정**

`MAX_DOTSTAR_COUNT=2` 유지 시 `google-labs-code/react-components` trigger가 reject된다. EXECUTE 전에 다음 중 선택해야 한다:
- 옵션 A: `MAX_DOTSTAR_COUNT=3` 으로 상향 (완화)
- 옵션 B: 비교 연산자를 `>= 2` → `> 2` 변경 (완화 — `.*` 정확히 2회는 허용)
- 옵션 C: `/\.[*+]/g` → `/\.\*/g`로 카운트 패턴 축소 (`\s*` 제외, `.*`만 카운트)
- 옵션 D: 임계값 유지 + community-skills-registry.json의 해당 패턴에 명시적 `unsafe_trigger_override` 플래그 추가

QA 권장: 옵션 B — `dotStarCount > MAX_DOTSTAR_COUNT`(strict greater-than)로 변경. 현재 의사코드가 `>= 2`이므로 `> 2`로 바꾸면 2회 패턴(`.*A.*B` 형태)은 통과하고 3회 이상만 reject된다.

### PM 게이트 에스컬레이션 (P-D-9)

`community-skills-registry.json` 변경이력 면제 적정성 — `schema_notes` 필드로 갈음하는 결정을 캡틴이 승인해야 한다. QA 관점: `schema_notes`에 `(144)` 태스크 번호 포함이 CONVENTIONS.md §변경이력 요건을 만족하는 합리적 대안으로 판단. 캡틴 승인 시 추가 조치 불필요.

### 경미한 수정 권장 (EXECUTE 전 선택)

**[W-2]** PLAN.md §3 L491을 `> 총 16개 Step | Phase 8개`로 수정. 실행 오류 위험은 낮으나 문서 일관성을 위해 권장.

---

*verdict: pass_with_minor | blockers: W-1 (임계값 결정 — EXECUTE 전 필수) | artifact_path: /Volumes/Data/AiStudio/workspace/opal/tasks/144-260510-opp-security-hardening/QA-PLAN.md*

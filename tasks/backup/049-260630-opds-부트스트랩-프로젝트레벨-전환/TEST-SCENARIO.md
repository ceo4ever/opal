# TEST-SCENARIO: 부트스트랩 진입 모델 사용자레벨 상시 → 프로젝트레벨 opt-in (2-tier)

> 태스크: 049-260630-opds-부트스트랩-프로젝트레벨-전환 | 작성일: 2026-06-30
> 입력: PLAN.md 리스크 가설 표(H-1~H-9) + §3.x.5 테스트 시나리오 + §5 QA 매트릭스 + §7 C-4 테스트 전략
> 검증 계층: L1(산출물 grep/구조·`bash -n`·`node -c`) → L2(install 멱등·마커 교체 셸 테스트 + apply.js 임시 프로젝트 실행) → L3(실세션 동작 — 캡틴 직접)
> SSOT: `opal/core/references/harness/red-first.md`

---

## RED-first 판단

> red-first.md §1.5 하이브리드 자동분기 적용. 판단 주체 = PM(작성 시점). 모호하면 RED-first 기본(안전측).

| 변경 영역 | 트랙 | 근거 (red-first.md §1.5) |
|----------|------|------------------------|
| F-003 install 마커 교체 동작 (TS-009) | **RED-first** | 부수효과 있는 동작 로직(파일 치환·사용자 내용 보존·멱등). self-confirming 위험 → RED 셸 테스트 선작성 |
| F-004 apply.js 4파일 생성·멱등 병합 (TS-013, TS-015) | **RED-first** | 동작 로직(파일 생성·마커 병합). self-confirming 위험 → RED node/셸 테스트 선작성 |
| F-001·F-002 AGENT.md 2-phase·절 반전 (TS-001~006) | 구현-후-검증 | 설정·문서(부트스트랩 절차 서술). "설정·문서" 트랙 → 정적 grep 단언 |
| F-005 docs 정합 (TS-016) | 구현-후-검증 | 문서 |
| F-006 setting.json 회귀 (TS-017) | 구현-후-검증 | 정적 grep(불변 단언). L3(TS-018)는 실세션 회귀 |

**혼합 트랙**: F-003·F-004 동작계약 = RED-first 적격(작성자≠구현자 — opal-test-agent mode:red가 RED 선작성 → opal-be-agent/opal-task-agent가 GREEN). 나머지 = 정적·실세션 검증.

**공통 불변(red-first.md §1.5)**: ① 테스트 코드 산출물(`tests/` 셸·node) ② 작성자≠구현자 ③ TEST 단계 검증 유지. RED 테스트는 GREEN 루핑 중 수정 금지(§3).

**graceful skip(§5)**: 부트스트랩은 LLM 거동이라 L3(실세션)는 결정론적 자동화 불가 → 캡틴 수동 확인(pending). 정적 단언(L1) + install/apply.js 동작계약(L2)이 결정론적 핵심 게이트.

---

## 1. 시나리오 목록

### RED-first 트랙 — install/apply.js 동작계약 (작성자≠구현자, mode:red 선작성)

> red-first.md §1·§2 — opal-test-agent(mode:red)가 RED(실패) 테스트를 선작성, 구현 워커가 GREEN. RED 테스트는 GREEN 루핑 중 수정 금지(§3). 공개 인터페이스(함수 호출 결과·파일 내용·exit code)로 검증(§4).

| TS-ID | 항목 | 대상 | 검증 방법 | PASS 조건 | RED 증거 | 결과 |
|-------|------|------|----------|----------|---------|------|
| TS-009 | install 마커 교체 — 구 마커 치환 + 사용자 내용 보존 + 멱등 (H-4) | `install_opal_section` (`scripts/install-mac.sh`) | 임시 HOME에 `사용자내용\n# === OPAL START ===\n구마커\n# === OPAL END ===\n사용자꼬리` 선배치 → bootstrapper로 함수 1회 호출 → 파일 검사. 이어 2회 호출(멱등) | START~END 구간이 신 콘텐츠로 치환 + 마커 밖 "사용자내용"·"사용자꼬리" 보존 + 2회차 결과가 1회차와 동일(diff 0). exit 0 | **GREEN (회귀 가드)**: `tests/ts-009-install-marker-replace.sh` 실행 결과 PASS=9 FAIL=0. 기존 install_opal_section이 이미 마커 교체·보존·멱등을 올바르게 구현함. | ✅ PASS (PASS=9 FAIL=0) |
| TS-013 | apply.js 4파일 생성 — Codex AGENTS.md 포함 (H-6) | `apply.js` (`opal/skills/opal-project-init/scripts/`) | 빈 임시 프로젝트에서 `node apply.js --project-root {tmp}` → 산출 파일 검사 | `CLAUDE.md`·`GEMINI.md`·`.cursorrules`·`AGENTS.md` 4개 생성 + 각 파일에 `# === OPAL START ===` 포함. exit 0 | **RED 확인**: `tests/ts-013-apply-four-files.sh` 실행 결과 PASS=7 FAIL=1. apply.js가 3파일(CLAUDE.md/GEMINI.md/.cursorrules)만 생성, AGENTS.md 파일 없음. PLATFORM_FILES 배열에 AGENTS.md 항목 미존재. | ✅ PASS (PASS=9 FAIL=0) — 구현 완료로 GREEN |
| TS-015 | apply.js AGENTS.md 멱등 병합 — 사용자 내용 보존 (H-7) | `apply.js` | 임시 프로젝트에 `사용자내용\n# === OPAL START ===\n구\n# === OPAL END ===` AGENTS.md 선배치 → apply.js 2회 실행 → 검사 | 마커 구간만 교체 + "사용자내용" 보존 + 2회차 멱등(diff 0) + `.bak` 백업 생성. exit 0 | **RED 확인**: `tests/ts-015-apply-agents-idempotent.sh` 실행 결과 PASS=6 FAIL=2. 구 내용 그대로 남음(교체 안 됨) + .bak 미생성. apply.js가 AGENTS.md를 처리하지 않아 mergeOther 미호출. | ✅ PASS (PASS=8 FAIL=0) — 구현 완료로 GREEN |

### L1 — 산출물 검사 (정적·결정론적)

| TS-ID | 항목 | 대상 파일 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|---------|----------|----------|------|
| TS-001 | AGENT.md Eager 2-phase 구분 (S-1, H-1) | `opal/core/AGENT.md` | `### Eager 단계` 내 grep: `Phase A`(비서) + `Phase B`(PM) + Phase B 게이트 `.opal/AGENT.md` + `존재` + Phase A에 `identity`·`PRINCIPLES` 잔존 | Phase A/B 구분 명시 + Phase B 진입 조건 "`.opal/AGENT.md` 존재" + Phase A에 identity/PRINCIPLES 포함 | ✅ PASS — L7 "Phase A — 비서 tier", L26 "Phase B — PM tier", L28 게이트 명문화, L22 identity, L24 PRINCIPLES 모두 확인 |
| TS-002 | PM tier 게이팅 명문화 (S-2, H-2) | `opal/core/AGENT.md` | Eager 절 grep: `.opal/AGENT.md` `부재`(또는 `없으면`) 시 `harness`·`opal-pm` 미Read 절차 | `.opal/AGENT.md` 부재 시 harness·opal-pm Read 안 함이 Phase B 게이트로 명시 | ✅ PASS — L28 "cwd에 `.opal/AGENT.md`가 없으면 Phase B 전체를 스킵한다(harness·opal-pm·PM 컨텍스트 미로드)" 명문화 확인 |
| TS-003 | `//` 불변식 명문화 (S-3, H-3) | `opal/core/AGENT.md` | Phase A 구간 grep: `//` + (`opi` 또는 `커맨드`) + 발동 가능 취지 + Lazy `//` 트리거 전제조건 `-`(없음) 유지 확인(`:39` 행 불변) | Phase A에 "비서 tier `//`(opi 포함) 발동 가능" + `//` Lazy 트리거 전제조건 부재 보존 | ✅ PASS — L15 "비서 tier에서도 `//` 입력만으로 skill-commands.md가 Lazy 로드되어 `//opi` 발동 가능" + L52 Lazy 트리거 `//` 전제조건 `-` 확인 |
| TS-004 | step 0 스킵게이트 불변 (H-8 가드) | `opal/core/AGENT.md` | step 0 grep: `setting.json` + `bootstrap` + `off` + fail-safe(`파싱`/`부재`/`정상 진행`) + models 머지. step 0이 Phase A 최상단 | step 0이 setting.json 게이트+fail-safe+models 머지 보존, 문구·위치 불변 | ✅ PASS — L17~19 step 0 스킵게이트+effective setting+bootstrap판정+fail-safe+models 로드 전부 Phase A 최상단에 보존 |
| TS-006 | 부트스트래퍼 관리 절 2-tier 반전 (H-1·R-7) | `opal/core/AGENT.md` | "프로젝트 부트스트래퍼 자동 관리" 절 grep: Claude/Cursor/Codex/Gemini 각 소절에 2-tier(전역=비서/프로젝트=PM·이식성) + "잉여" 단정 제거(`항상 잉여` 부재) | 4 플랫폼 2-tier 서술 + "프로젝트 마커는 항상 잉여" 단정 제거 | ✅ PASS — L399 "2-tier 모델에서 전역 마커는 비서 tier를 상시 활성화"로 논리 반전 + L403~435 4플랫폼 소절 2-tier 서술. "항상 잉여" 단정 없음 |
| TS-007 | bootstrapper 4종 비서 진입 정합 + 변경이력 (S, R-5) | `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md` | 코드블록 추출 grep: `setting.json` 스킵게이트 보존 + `~/.opal/AGENT.md` 진입 + 변경이력 `049` 행 | 3종 스킵게이트+AGENT.md 진입 보존 + 각 변경이력 049 행 | ✅ PASS — 3종 모두 L17 스킵게이트, L23 `~/.opal/AGENT.md` 진입, 각 049 변경이력(claude v1.0.4 / gemini v1.2.1 / codex v1.0.4) 확인 |
| TS-008 | cursor.mdc frontmatter 무손상 (H-5) | `opal/bootstrapper/cursor-bootstrap.mdc` | frontmatter grep: `---` + `alwaysApply: true` 무손상 + 본문 `setting.json` 게이트 보존 | `---`/`alwaysApply: true` 보존 + 본문 게이트 보존 | ✅ PASS — frontmatter `---`/`alwaysApply: true` 보존, 본문 setting.json 스킵게이트 보존, 변경이력 표 미신설 확인 |
| TS-010 | install 호출부 무결 (R-4) | `scripts/install-mac.sh`, `scripts/install/windows.ps1` | `bash -n scripts/install-mac.sh`(exit 0) + `install_opal_section` 호출부 grep(claude/gemini/codex 3건 + cursor cp 1건) + windows.ps1 `Register-Bootstrapper` 4 플랫폼 매칭 | bash -n 통과 + 마커 삽입 4 플랫폼 경로 존재 (install 로직 불변) | ✅ PASS — `bash -n` exit 0. L1206 claude / L1210 cursor cp / L1218 gemini / L1224 codex 호출부 4건 확인. windows.ps1 Register-Bootstrapper + Codex ~/.codex/AGENTS.md 확인 |
| TS-011 | Codex AGENTS.md 템플릿 신규 (R-6, H-6) | `opal/skills/opal-project-init/templates/common/platform/AGENTS.md` | 파일 존재 + grep: `# === OPAL START ===` + `# === OPAL END ===` + `~/.opal/AGENT.md` + `identity.md` | 템플릿 존재 + 마커 + AGENT.md/identity.md 진입 지시 | ✅ PASS — 파일 존재. L1 `# === OPAL START ===`, L8 `# === OPAL END ===`, L6 `~/.opal/AGENT.md`, L7 `identity.md` 모두 확인 |
| TS-012 | apply.js PLATFORM_FILES 배열 + 구문 (R-6, H-6) | `opal/skills/opal-project-init/scripts/apply.js` | `node -c apply.js`(또는 `node --check`) exit 0 + `PLATFORM_FILES` grep: `AGENTS.md` 항목 존재 + 병합 분기에서 `dest === "CLAUDE.md"`만 mergeClaudeMd(AGENTS.md는 mergeOther) | node 구문 무결 + AGENTS.md 배열 항목 + mergeOther 경로 | ✅ PASS — `node --check` exit 0. L25 `{ src: "platform/AGENTS.md", dest: "AGENTS.md" }` 항목. L178~180 `dest === "CLAUDE.md"` → mergeClaudeMd, 나머지 → mergeOther 분기 확인 |
| TS-014 | opi SKILL.md AGENTS.md 반영 (R-6) | `opal/skills/opal-project-init/SKILL.md` | grep: Phase 4-1 표에 `AGENTS.md` 행 + 기존파일처리에 AGENTS.md + 완료보고 플랫폼 파일에 AGENTS.md + 변경이력 `049` 행 | SKILL.md 4곳(표·처리·보고·변경이력) AGENTS.md 반영 | ✅ PASS — L564 Phase 4-1 표, L569 기존파일처리, L618 완료보고, L1005 변경이력 049(v4.5) 4곳 모두 확인 |
| TS-016 | docs 2-tier 정합 (R-9) | `docs/ARCHITECTURE.md`, `docs/PROJECT.md` | ARCHITECTURE grep: `2-tier`(또는 `비서`+`PM` tier) + `.opal/AGENT.md` 승격 + PROJECT.md 변경이력 `049` 행 | ARCHITECTURE 2-tier 부트스트랩 기술 + PROJECT 049 변경이력 | ✅ PASS — ARCHITECTURE.md L54 "부트스트랩 진입 모델 (2-tier)" + L56 비서/PM tier 표 + L61 `.opal/AGENT.md` 승격. PROJECT.md L142 "049" 변경이력 확인 |
| TS-017 | setting.json 회귀 0 — 게이트 문구 불변 (R-8, H-8) | `opal/core/AGENT.md` + bootstrapper 4종 | 5곳 스킵게이트 교차 grep: 조건(`off`)·동작(전부 스킵)·fail-safe·models 우선순위 서술 불변. setting.json 스키마 변경 0 | 5곳 게이트 의미 보존 + setting.json 스키마·게이트 값·models 우선순위 미변경 | ✅ PASS — AGENT.md+claude+gemini+codex+cursor.mdc 5곳 모두 `bootstrap:off` 조건, 전체 스킵, fail-safe 서술 보존. setting.json 스키마 변경 없음 확인 |
| TS-019 | 변경이력 일괄 (R 전체) | AGENT.md·claude/gemini/codex-bootstrap.md·opi SKILL.md·ARCHITECTURE.md·PROJECT.md | 각 파일 변경이력에 `049` 행 grep (KST 일시·semver — cursor.mdc 제외: 표 부재) | 6개 파일 049 변경이력 행 존재 | ✅ PASS — 7개 파일 모두 049 행 각 1건 이상 확인 (AGENT.md v4.0 / claude v1.0.4 / gemini v1.2.1 / codex v1.0.4 / SKILL.md v4.5 / ARCHITECTURE.md / PROJECT.md) |
| TS-020 | 플랫폼 분기 격리 (H-9) | `opal/core/AGENT.md` + bootstrapper 4종 | AGENT.md Eager 2-phase 로직에 플랫폼 조건문(`if Claude`/`if Cursor` 등) 부재 + bootstrapper에 tier 분기 로직 부재(진입점만) | tier 게이트 로직은 AGENT.md(플랫폼 독립)에만, bootstrapper/install은 어댑터(진입점·마커) | ✅ PASS — AGENT.md에 `if Claude`/`if Cursor` 등 플랫폼 조건문 없음. bootstrapper 4종 모두 tier 분기 로직 없이 진입점(setting.json 게이트 + AGENT.md 1줄 로드)만 보유 |

### L2 — install/apply.js 재배포·실행 후 확인 (사용자 승인 후 수행)

| TS-ID | 항목 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-009b | install 재배포 멱등 (실배포) | 캡틴 환경에서 install 재실행 ×2 → `~/.claude/CLAUDE.md` 등 마커 영역 신 콘텐츠 치환 + 사용자 내용 보존 | 재실행 후 마커 신 버전 + 마커 밖 사용자 내용 보존 + 2회 멱등 | ⏸ pending (캡틴 직접) |
| TS-013b | opi 실행 4파일 (실배포) | 캡틴이 비-opi 임시 프로젝트에 install 후 `//opi` 실행 → CLAUDE/GEMINI/.cursorrules/AGENTS 4파일 생성 확인 | 4파일 생성 + 각 마커 포함 | ⏸ pending (캡틴 직접) |

### L3 — 실세션 동작 (수동, 부트스트랩 LLM 거동 — 캡틴 직접)

> TASK §완료기준 5 시나리오 직결. 결정론적 자동화 불가(graceful skip §5) → 캡틴 수동 확인.

| TS-ID | 항목 (TASK 완료기준) | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-005a | ① 비서 tier 전역 로드 | 비-opi 폴더(`.opal/AGENT.md` 부재) 새 세션 | 알투 비서 활성(identity·PRINCIPLES·보고형식 적용) + 부트스트랩 보고에 `⬜ harness ⬜ PM ⬜ PM모드` | ⏸ pending |
| TS-005b | ② 비-opi 폴더 PM tier 미로드 | 같은 비-opi 세션에서 harness/opal-pm 로드 여부 관찰 | harness·opal-pm·프로젝트 컨텍스트 미Read (Phase B 스킵) | ⏸ pending |
| TS-005c | ③ 비-opi 폴더 `//opi` 발동 | 같은 비-opi 세션에서 `//opi` 입력 | skill-commands.md Lazy 로드 → opi 발동(프로젝트 초기화 진입) | ⏸ pending |
| TS-005d | ④ opi 후 PM tier 승격 | TS-005c로 opi 완료(=`.opal/AGENT.md` 생성) 후 같은/다음 세션 진입 | harness·opal-pm·프로젝트 AGENT.md 로드 + PM 모드 활성 + 보고 `✅ harness ✅ PM ✅ PM모드` | ⏸ pending |
| TS-018a | ⑤ 전역 bootstrap:off | `~/.opal/setting.json={"bootstrap":"off"}` → 새 세션(임의 폴더) | 전 세션 부트스트랩 step 1~7 스킵 + 보고 없음 (회귀 불변) | ⏸ pending |
| TS-018b | ⑤ 프로젝트 setting.local.off | opi 프로젝트에 `.opal/setting.local.json={"bootstrap":"off"}` → 그 프로젝트 새 세션 | 해당 프로젝트만 스킵, 타 프로젝트·전역은 정상 (회귀 불변) | ⏸ pending |

---

## 2. 코드 품질

> L1 정적 검사 기반 — install `bash -n`, apply.js `node -c`, 마크다운 grep. 마크다운/JS/설정 변경.

| 항목 | 기준 | 결과 |
|------|------|------|
| 변경이력 기록 | AGENT.md + claude/gemini/codex-bootstrap.md + opi SKILL.md + ARCHITECTURE.md + PROJECT.md에 049 행(KST 일시·semver·태스크) | ✅ PASS (TS-019) |
| install 구문 무결 | `bash -n scripts/install-mac.sh` exit 0 (로직 불변 — 검증만) | ✅ PASS (TS-010) |
| apply.js 구문 무결 | `node --check apply.js` exit 0 | ✅ PASS (TS-012) |
| cursor frontmatter 무손상 | `---`/`alwaysApply: true` 구조 보존 (H-5) | ✅ PASS (TS-008) |
| cursor.mdc 변경이력 표 미신설 | 043 선례 정합 — 표 없는 파일에 표 추가하지 않음 | ✅ PASS — cursor.mdc에 변경이력 표 없음 확인 |
| 과서술 금지 | bootstrapper 마커 정합 1줄 — tier 로직은 AGENT.md에만(헌법 §3 Surgical) | ✅ PASS (TS-020) |

---

## 3. 보안

| 항목 | 기준 | 결과 |
|------|------|------|
| 시크릿 없음 | 마커·템플릿·bootstrapper·apply.js 변경분에 토큰/시크릿 없음 | ✅ PASS — grep 결과 해당 파일들에 api_key/secret/token/password/Bearer 없음 (gemini-hardening.md 주석 1건은 변경 파일 아님) |
| 권한 최소 — 신 표면 0 | 기존 `Read(~/.opal/**)` 재사용, 신규 권한 등록 0 | ✅ PASS — AGENTS.md 템플릿은 기존 Read 패턴 재사용. 신규 MCP/권한 등록 없음 |
| 민감정보 비저장 | AGENTS.md 템플릿·마커는 부트스트랩 진입 지시만 (인증/네트워크/시크릿 없음) | ✅ PASS (TS-011) — AGENTS.md 템플릿은 OPAL START/END 마커와 AGENT.md/identity.md 로드 지시만 포함 |

---

## 4. 회귀 테스트

| 항목 | 기준 | 결과 |
|------|------|------|
| setting.json 게이트 불변 | 스키마·`bootstrap:off`·models 2-레이어 우선순위 미변경 (전역/프로젝트 off 정상) | ✅ PASS (TS-017) — 5곳 게이트 문구 보존. L3 실세션(TS-018a/b)은 pending |
| opi 기존 3종 비파괴 | CLAUDE/GEMINI/.cursorrules 생성 동작 유지 (AGENTS.md 추가가 회귀 유발 안 함) | ✅ PASS (TS-013) — apply.js 4파일 생성 PASS=9. 기존 3종 동작 유지 확인 |
| install 마커 밖 사용자 내용 보존 | 마커 교체 시 START/END 밖 사용자 내용 보존 | ✅ PASS (TS-009) — PASS=9. 사용자머리/사용자꼬리 보존 + 멱등 확인 |
| AGENT.md 기존 신호 정합 | 역할전환 표·완료보고 PM모드 칼럼 등 `.opal/AGENT.md` 신호 사용처 불변 | ✅ PASS (TS-001) — 역할전환 표 L122 보존, 부트스트랩 보고 L73 PM모드 칼럼 보존 |
| Antigravity 자동 삽입 동작 불변 | Step 2(절 반전)는 서술만 변경 — 자동 삽입 동작 불변 | ✅ PASS (TS-006) — Step 6 Antigravity 자동 삽입 로직 L37 불변. 서술만 2-tier 논리 반전 |

---

## 5. 시나리오 ↔ AC/리스크 매핑

| TS-ID | F-ID | AC/완료기준 | 리스크(H) | 트랙 |
|-------|------|-----------|----------|------|
| TS-001~004 | F-001 | R-1·R-2·R-3 / 완료기준 ②③ | H-1, H-2, H-3, H-8 | 정적 |
| TS-005a~d | F-001 | 완료기준 ①②③④ | H-1, H-2, H-3 | L3 실세션 |
| TS-006 | F-002 | R-7 | H-1 | 정적 |
| TS-007~010 | F-003 | R-4·R-5 / 완료기준 (마커 교체) | H-4, H-5, H-9 | 정적 + L2(TS-009 RED) |
| TS-011~015 | F-004 | R-6 / 완료기준 ④(진입 보강) | H-6, H-7 | 정적 + L2(TS-013·015 RED) |
| TS-016 | F-005 | R-9 | — | 정적 |
| TS-017, TS-018a/b | F-006 | R-8 / 완료기준 ⑤ | H-8 | 정적 + L3 |
| TS-019, TS-020 | 전 기능 | 변경이력 의무·플랫폼 분기 격리 | H-9 | 정적 |

---

## 6. 실행 노트

- **RED-first 산출물**: `tasks/049-260630-opds-부트스트랩-프로젝트레벨-전환/tests/` 하위에 TS-009(install 마커 교체 셸 테스트)·TS-013/TS-015(apply.js node 동작 테스트)를 opal-test-agent(mode:red)가 선작성. RED FAIL 증거 기록 후 구현 워커 GREEN.
- **정적 단언 자동화**: TS-001~020 중 L1은 grep/`bash -n`/`node --check`로 결정론적 PASS/FAIL 판정. opal-test-agent가 일괄 수행.
- **L2 동작계약**: TS-009·TS-013·TS-015는 임시 HOME/임시 프로젝트에서 함수·스크립트 실호출(실배포 아님 — 격리). TS-009b·TS-013b 실배포는 캡틴 승인 후.
- **L3 실세션(graceful skip)**: TS-005a~d·TS-018a/b는 부트스트랩 LLM 거동이라 캡틴 직접 확인(pending). install 재배포는 캡틴 책임(배포 경계).

---

## 7. 최종 판정

> 실행일: 2026-06-30 | 실행자: opal-test-agent

| 분류 | 수 |
|------|-----|
| ✅ PASS (L1+L2 자동화) | 17 |
| ⏸ pending (L3 실세션·실배포) | 8 |
| ❌ FAIL | 0 |

**종합 판정: TEST PASS (L3 pending=캡틴)**

- L1 정적 단언 14건 전체 PASS (TS-001~004, 006~008, 010~012, 014, 016, 017, 019, 020)
- L2 동작계약 3건 전체 PASS (TS-009 PASS=9 / TS-013 PASS=9 / TS-015 PASS=8)
- 코드 품질 6항목 PASS, 보안 3항목 PASS, 회귀 5항목 PASS
- L3 실세션 8건(TS-005a/b/c/d, TS-009b, TS-013b, TS-018a/b)은 LLM 거동·실배포 — 결정론적 자동화 불가, 캡틴 직접 확인 대기 (graceful skip)

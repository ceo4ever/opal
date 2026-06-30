# PLAN: 부트스트랩 진입 모델 사용자레벨 상시 → 프로젝트레벨 opt-in (2-tier)

> 작성일: 2026-06-30 | 입력: TASK.md (ANALYSIS.md 없음 — PLAN에서 직접 코드 분석 수행)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 부트스트랩을 **2-tier**로 분리한다. 비서(Lite) tier(스킵게이트+identity+PRINCIPLES+보고형식+도구·MCP 인지맵+`//` 레지스트리 해석)는 전역 마커로 모든 세션 상시 로딩하고, PM(Full) tier(harness+opal-pm+프로젝트 `.opal/AGENT.md`+PROJECT/MEMORY 브리핑)는 **`.opal/AGENT.md` 존재 시에만 승격 로딩**한다. 변경의 핵심은 `opal/core/AGENT.md` Eager 단계를 Phase A(비서·항상)/Phase B(PM·조건부)로 재구성하는 것이며, install 어댑터(마커 콘텐츠 교체)·opi(전 플랫폼 마커 + Codex `AGENTS.md` 보강)·docs 정합이 뒤따른다. setting.json 스키마·`bootstrap:off` 게이트·models 2-레이어 우선순위는 회귀 0으로 불변한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | AGENT.md Eager 2-phase 재구성 (비서/PM 승격 게이트 + `//` 불변식) | R-1, R-2, R-3 | P0 | 없음 |
| F-002 | AGENT.md "부트스트래퍼 자동 관리" 절 논리 반전 (전역=비서 / 프로젝트=PM) | R-7 | P0 | F-001 |
| F-003 | 전역 마커 경량화 — bootstrapper 4종 소스 정합 + install 콘텐츠 교체 검증 | R-4, R-5 | P0 | F-001 |
| F-004 | opi 전 플랫폼 프로젝트 마커 + Codex `AGENTS.md` 템플릿 보강 | R-6 | P0 | 없음 |
| F-005 | docs 정합 (ARCHITECTURE 2-tier 구조 + PROJECT/CONVENTIONS 변경이력) | R-9 | P1 | F-001~F-004 |
| F-006 | setting.json 불변 보장 (회귀 0 — 검증 전용 기능, 산출물 없음) | R-8 | P0 | 없음 |

> F-006은 신규 산출물이 없는 **불변(회귀) 기능**이다. EXECUTE에서 코드 변경 없이 회귀 테스트로만 커버한다(§5.2). F-001~F-004의 변경이 setting.json 게이트·models 우선순위를 건드리지 않음을 보증하는 가드 역할.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ──┐
       └─ F-003 ──┼─ F-005
F-004 ────────────┘
F-006 (불변 가드 — 전 기능에 횡단 적용, 산출물 없음)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 AGENT.md Phase A/B 재구성 | 비서 tier가 PRINCIPLES·identity·보고형식을 여전히 로드해야 함(전역 비서 유지). Phase A에서 누락 시 전역 알투 비서가 죽음 | P0 | L1(grep 단언) + L3(실세션) | S-1, S-5 |
| H-2 | F-001 PM 승격 게이트 | `.opal/AGENT.md` 부재 폴더에서 harness·opal-pm가 로드되면(게이트 누수) "프로젝트레벨 opt-in" 불변식 깨짐 | P0 | L1(grep 절차 단언) + L3(비-opi 세션) | S-2, S-6 |
| H-3 | F-001 `//` 불변식 | 비서 tier가 `//` 레지스트리 해석 능력을 잃으면 비-opi 폴더에서 `//opi` 발동 불가 → OPAL화 진입점 소실(치명) | P0 | L1(Lazy 트리거 전제조건 부재 단언) + L3(`//opi` 실발동) | S-3, S-7 |
| H-4 | F-003 bootstrapper 마커 콘텐츠 교체 | install `install_opal_section`이 `OPAL START/END` 마커 단위로 치환 → 구 무거운 마커 능동 제거. 마커 외 사용자 내용 보존 계약이 깨지면 사용자 CLAUDE.md 손상 | P0 | L1(마커 추출 무결) + L2(install 멱등·마커 교체 셸 테스트) | S-8, S-9, S-12 |
| H-5 | F-003 cursor `.mdc` frontmatter | cursor 마커 교체 시 `---`/`alwaysApply:true` frontmatter 손상 → user-level 룰 비활성 | P1 | L1(frontmatter 무손상 grep) | S-10 |
| H-6 | F-004 opi Codex `AGENTS.md` 신규 | apply.js `PLATFORM_FILES`에 Codex 항목 누락 시 opi가 `AGENTS.md` 미생성 → Codex 이식성 불변식 미충족 | P0 | L1(템플릿 파일 존재 + apply.js 배열) + L2(apply.js 실행 → 4파일 산출) | S-13, S-14, S-15 |
| H-7 | F-004 apply.js 기존 병합 로직 | `AGENTS.md` 추가 시 기존 CLAUDE.md 마커 병합(`mergeClaudeMd`)·기타 병합(`mergeOther`) 회귀 — `AGENTS.md`는 `mergeOther` 경로여야 함 | P1 | L2(기존 `AGENTS.md`에 사용자 내용 + 마커 병합 멱등) | S-16 |
| H-8 | F-006 setting.json 게이트 | F-001 Eager step 0(스킵게이트+머지) 재배치/문구 변경이 `bootstrap:off` 판정·models 2-레이어 우선순위를 건드리면 회귀 | P0 | L1(step 0 불변 grep) + L3(전역/프로젝트 off 스위치) | S-17, S-18 |
| H-9 | F-003 플랫폼 분기 누수 | 2-tier 로직(승격 게이트)을 bootstrapper 마커나 install 분기에 넣으면 PRINCIPLES "플랫폼 분기는 어댑터에만, 로직은 AGENT.md" 위반 | P1 | L1(bootstrapper에 tier 로직 부재 + AGENT.md에만 존재 단언) | S-11 |

**가설 도출 메모**: H-1~H-3은 F-001의 핵심 행동 계약(비서 유지 / PM 게이팅 / `//` 불변식)으로 TASK 완료기준 ①②③에 직결. H-4·H-7은 마커/템플릿 병합의 사용자 내용 보존 계약. H-8·H-9는 회귀 0(R-8)과 플랫폼 분기 격리 헌법 제약의 직접 방어.

---

## 2. 기능별 분석

### F-001: AGENT.md Eager 2-phase 재구성

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md` | 부트스트랩 SSOT. Eager 단계 / 역할전환 표 / 부트스트랩 완료 보고 | 수정 |
| 에이전트 | `opal/core/PRINCIPLES.md` | 헌법(비서 tier 포함 대상 — 경량 로드) | 읽기 전용(불변) |
| 참조 | `opal/core/references/opal-harness.md` | PM tier 로드 대상 (Phase B) | 읽기 전용(불변) |
| 참조 | `opal/core/references/opal-pm.md` | PM tier 로드 대상 (Phase B) | 읽기 전용(불변) |
| 참조 | `opal/core/references/harness/skill-commands.md` | `//` 커맨드 Lazy 트리거 정의 (전제조건 부재 근거) | 읽기 전용(불변) |

#### 2.1.2 현재 구현
`opal/core/AGENT.md` Eager 단계(`opal/core/AGENT.md:11-29`):
- **step 0** (`:13-16`): 스킵게이트(setting.json 전역+로컬 머지) + `bootstrap:off` 판정 + models 로드. **비서 tier 소속**.
- **step 1** (`:18`): identity.md Read. **비서 tier**.
- **step 2** (`:19`): identity 부재 시 온보딩. **비서 tier**.
- **step 2.5** (`:20`): PRINCIPLES.md(헌법) Read — **무조건**. 비서 tier(경량 헌법).
- **step 3** (`:21`): opal-harness.md Read — **무조건**. → PM tier로 게이팅 대상.
- **step 4** (`:22`): opal-pm.md Read — **무조건**. → PM tier로 게이팅 대상.
- **step 5** (`:23`): 프로젝트 `.opal/AGENT.md` 존재 시 Read. PM tier 신호.
- **step 6** (`:24`): Antigravity 한정 부트스트래퍼 자동 삽입.
- **step 6.5** (`:25-28`): cwd 판별로 next-action 결정 (`.opal/AGENT.md` 존재/미존재 분기 — 이미 동일 신호 사용).
- **step 7** (`:29`): 활성화.

역할전환 표(`opal/core/AGENT.md:108-111`)는 이미 `.opal/AGENT.md` 존재 여부로 비서/PM을 구분한다 — `[MUST] 'opal/core/AGENT.md' §행동규칙 상태정의 표`: "비서 | 프로젝트 밖(`.opal/AGENT.md` 미존재) | 일상 대화 / PM | 프로젝트 내(`.opal/AGENT.md` 존재) | 프로젝트 모든 상호작용 관리". 부트스트랩 완료 보고의 `PM모드` 칼럼(`:65`)도 `.opal/AGENT.md` 존재 시 ✅ PM / 미존재 시 ⬜ 비서로 동일 신호를 쓴다.

`//` 커맨드 Lazy 트리거(`opal/core/AGENT.md:39`): `| // 커맨드 입력 | harness/skill-commands.md | - |` — **전제 조건 칸이 `-`**(전제조건 없음). 즉 harness·PM 미로드 상태(비서 tier)에서도 `//` 입력만으로 skill-commands.md가 Lazy 로드되어 `//opi` 발동 가능.

#### 2.1.3 영향 범위
- **상위 의존(이 파일을 읽는 주체)**: install이 strip 후 `~/.opal/AGENT.md`로 배포 → 모든 플랫폼 세션이 부트스트랩 시 Read. bootstrapper 마커가 이 파일을 가리킴.
- **하위 의존(이 파일이 가리키는 것)**: PRINCIPLES.md / identity.md / opal-harness.md / opal-pm.md / 프로젝트 `.opal/AGENT.md` / MEMORY.md.
- **공유 상태**: 부트스트랩 완료 보고 형식(`:55-67`)의 체크라인 — Phase A/B 분리 시 `harness`·`PM` 칼럼이 비서 tier에서 `⬜`(해당 없음)으로 표기되어야 정합.
- **관련 테스트**: 043 태스크가 step 0 게이트를 grep 단언으로 검증한 선례(`tasks/043.../TEST-SCENARIO.md` TS-005).

---

### F-002: AGENT.md "부트스트래퍼 자동 관리" 절 논리 반전

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md` | "프로젝트 부트스트래퍼 자동 관리" 절(§383-427) + Eager step 6(§24) | 수정 |

#### 2.2.2 현재 구현
`opal/core/AGENT.md:383-417` "프로젝트 부트스트래퍼 자동 관리" 절의 현 논리: "Claude Code/Cursor/Codex는 install이 글로벌 부트스트래퍼를 자동 셋업하므로 **프로젝트 마커는 잉여**이며 자동 삽입 스킵. Antigravity(Gemini)만 자동 삽입." 각 플랫폼 소절이 "프로젝트 마커는 항상 잉여"(`:394`)를 명시. Eager step 6(`:24`)도 동일 취지("Claude Code/Cursor는 install 단계에서 글로벌 부트스트래퍼가 자동 셋업되므로 프로젝트 마커는 불필요").

#### 2.2.3 영향 범위
- 이 절의 서술은 **R-7 반전 대상**이다. 2-tier 모델에서 프로젝트 마커의 의미가 "잉여"에서 "(Claude는) PM 승격 신호 + (Gemini/Codex는) 이식성·폴백 트리거"로 바뀐다.
- **불변 보존**: 자동 삽입 동작 자체(Claude/Cursor/Codex 스킵, Gemini 수행)는 변경하지 않는다. 변경하는 것은 **이유 서술(논리)**이다. PM 승격 게이트는 `.opal/AGENT.md` 존재이지 `CLAUDE.md` 마커가 아니므로, 자동 삽입 정책은 그대로 둬도 2-tier와 정합한다.
- TASK 확정 방향 §2: "프로젝트 마커는 Claude에선 보조(중복·무해), Gemini/Antigravity·Codex 이식성·폴백 트리거로 유지".

---

### F-003: 전역 마커 경량화 — bootstrapper 4종 소스 + install 콘텐츠 교체

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 부트스트래퍼 | `opal/bootstrapper/claude-bootstrap.md` | 전역 `~/.claude/CLAUDE.md` 마커 콘텐츠 SSOT | 수정 |
| 부트스트래퍼 | `opal/bootstrapper/gemini-bootstrap.md` | 전역 `~/.gemini/GEMINI.md` 마커 콘텐츠 SSOT | 수정 |
| 부트스트래퍼 | `opal/bootstrapper/codex-bootstrap.md` | 전역 `~/.codex/AGENTS.md` 마커 콘텐츠 SSOT | 수정 |
| 부트스트래퍼 | `opal/bootstrapper/cursor-bootstrap.mdc` | 전역 `~/.cursor/rules/000-opal-agent.mdc` 콘텐츠 SSOT | 수정 |
| 배치 | `scripts/install-mac.sh` | `install_opal_section` 마커 교체 + 호출부 4건 | 읽기 전용(불변 — 검증만) |
| 배치 | `scripts/install/windows.ps1` | `Register-Bootstrapper` + `Install-OpalSection` | 읽기 전용(불변 — 검증만) |

#### 2.3.2 현재 구현
- **bootstrapper 4종**은 이미 동일한 스킵게이트(setting.json 전역+로컬 머지) 문구 + "`~/.opal/AGENT.md` Read → identity.md Read"만 지시한다(콘텐츠 동일, 플랫폼별 wrapper 차이만). **실제 2-tier 로직은 전부 `~/.opal/AGENT.md`가 보유**하므로, bootstrapper는 진입점(AGENT.md를 가리킴)일 뿐 tier 분기를 담지 않는다. → 마커 콘텐츠 자체는 거의 그대로 유지 가능하며, **변경은 (a) 비서 진입 의미 1줄 정합 + (b) 변경이력 049 행 추가**로 최소화한다. (헌법 §"플랫폼 분기는 어댑터에만, 로직은 AGENT.md" 준수 — H-9.)
- **install 마커 교체 메커니즘**: `install_opal_section`(`scripts/install-mac.sh:251-325`)은 target에 `# === OPAL START ===`가 있으면 START~END 구간을 새 content로 **치환**하고 마커 밖 사용자 내용은 보존한다(`:274-293`). 즉 **구버전 마커는 콘텐츠 교체만으로 능동 제거**된다(R-4 "구버전 능동 제거" 자동 충족). 호출부 4건(`:1206`, `:1210`(cursor는 cp), `:1218`, `:1224`).
- **windows.ps1**: `Register-Bootstrapper`(`scripts/install/windows.ps1:809-872`)가 `Install-OpalSection`으로 동일 마커 교체. cursor는 CRLF 정규화 cp.

#### 2.3.3 영향 범위
- **install 로직 변경 불필요**: 마커 교체 메커니즘이 이미 콘텐츠 단위 치환 + 사용자 내용 보존을 제공하므로, bootstrapper 콘텐츠 SSOT만 갱신하면 install 재실행 시 자동으로 신 마커로 치환된다. install/windows 스크립트는 **검증 대상**(L1 구문·grep, L2 멱등)이지 변경 대상이 아니다.
- **bootstrapper 콘텐츠가 이미 AGENT.md를 가리키므로**, F-001(AGENT.md 2-phase)이 적용되면 전역 마커가 가리키는 AGENT.md가 비서 tier부터 시작 → 전역 비서 유지 + PM 게이팅이 마커 변경 없이도 달성됨. bootstrapper 변경은 의미 정합·변경이력에 한정(최소 침습 — 헌법 §3 Surgical).

---

### F-004: opi 전 플랫폼 프로젝트 마커 + Codex `AGENTS.md` 보강

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-project-init/SKILL.md` | opi 프로세스 — Phase 4-1 플랫폼 파일 생성 표(§559-568) + 완료 보고 | 수정 |
| 스킬 | `opal/skills/opal-project-init/scripts/apply.js` | 플랫폼 파일 생성 스크립트 — `PLATFORM_FILES` 배열(§21-25) + 병합 로직 | 수정 |
| 스킬 | `opal/skills/opal-project-init/templates/common/platform/AGENTS.md` | Codex 프로젝트 마커 템플릿 | 신규 |

#### 2.4.2 현재 구현
- **템플릿 현황**: `templates/common/platform/`에 `CLAUDE.md`·`GEMINI.md`·`.cursorrules` 3종만 존재. **`AGENTS.md`(Codex) 누락**. 각 템플릿은 `# === OPAL START === ... # === OPAL END ===` 마커 + "`~/.opal/AGENT.md` Read → identity.md Read" 지시(전역 부트스트래퍼와 동일 콘텐츠). GEMINI.md는 추가로 `# === GEMINI HARDENING START/END ===` 블록 포함.
- **apply.js**: `PLATFORM_FILES`(`apply.js:21-25`)에 3개 항목(`platform/CLAUDE.md→CLAUDE.md`, `platform/GEMINI.md→GEMINI.md`, `platform/.cursorrules→.cursorrules`). **Codex 항목 없음**. 병합 분기: `dest === "CLAUDE.md"` → `mergeClaudeMd`(마커 구간 교체+사용자 내용 보존), 그 외 → `mergeOther`(마커 구간 교체 또는 append). `AGENTS.md`는 `mergeOther` 경로(파일 1개 마커 단위)로 처리되어야 함 — H-7.
- **SKILL.md Phase 4-1 표**(`opal/skills/opal-project-init/SKILL.md:559-563`): CLAUDE.md·GEMINI.md·.cursorrules 3행만. 기존 파일 처리(§565-568)도 3종만 언급.

#### 2.4.3 영향 범위
- **하위 의존**: apply.js가 `TEMPLATES_DIR`(`apply.js:18`)에서 템플릿을 읽음 → 신규 `AGENTS.md` 템플릿 추가 + 배열 행 추가가 묶음.
- **install 배포**: `templates/`는 `~/.opal/skills/opal-project-init/templates/`로 배포되며 install이 별도 변경 없이 신규 파일을 자동 포함(`install_dir` 재귀 복사). install 스크립트 변경 불필요.
- **회귀**: 기존 3종 생성 동작은 불변(배열 행 추가만). H-7(병합 멱등) 보존.

---

### F-005: docs 정합

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `docs/ARCHITECTURE.md` | 시스템 구조 — 부트스트랩 진입 다이어그램(§9-52) + 2-레이어 모델(§54-85) | 수정 |
| 문서 | `docs/PROJECT.md` | 프로젝트 정의 — 변경이력(§134-141) | 수정 |
| 문서 | `docs/CONVENTIONS.md` | 컨벤션 — 변경이력(해당 시) | 수정(해당 시) |

#### 2.5.2 현재 구현
- `docs/ARCHITECTURE.md:9-52` 부트스트랩 진입 다이어그램은 "부트스트래퍼 → AGENT.md Read → 에이전트 활성화"의 단일 흐름으로, **tier 구분이 없다**. §54-85 2-레이어 모델은 Global/Project Layer를 다루지만 부트스트랩 로딩의 비서/PM tier 분리는 미반영.
- `docs/PROJECT.md:134-141` 변경이력 표는 날짜·변경내용 2칼럼. `docs/CONVENTIONS.md`는 §배포 경계(§200)·플랫폼 분기 격리(§205)를 다루며 본 작업으로 규칙 신설은 없음 → 변경이력 행만 해당 시 추가.

#### 2.5.3 영향 범위
- ARCHITECTURE는 2-tier 부트스트랩 구조를 기술해야 함(R-9 AC). 새 패턴(2-tier) 도입이므로 ARCHITECTURE 갱신이 docs/ 갱신 규칙상 필수(plan-guide §4 "시스템 구조 변경 → ARCHITECTURE.md").
- PROJECT.md는 변경이력 행만 추가(R-9 AC: "PROJECT.md 변경이력 행 추가").

---

## 3. 기능별 설계

### F-001: AGENT.md Eager 2-phase 재구성

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 에이전트 | Eager 단계를 Phase A(비서·항상)/Phase B(PM·`.opal/AGENT.md` 존재 시 승격)로 재구성. 설계원칙 박스·완료보고 칼럼 정합. 변경이력 행 추가 | (→ D-1 §Eager) |

#### 3.1.2 설계

**Eager 단계 재구성 (핵심)**. 현 step 0~7을 2-phase로 재배치한다. **step 번호는 보존**하고 Phase 라벨을 부여하여 물리 분할 없이(헌법 §2 — AGENT.md 물리 파일 분할은 범위 외) 논리 게이팅만 추가한다.

```
### Eager 단계 (세션 시작 시 즉시 수행)

#### Phase A — 비서 tier (항상 로드, 모든 세션)
0. [스킵 게이트 + 프로젝트 설정 머지]  ← 현 step 0 그대로 (불변, H-8)
1. identity.md Read
2. identity 부재 시 onboarding
2.5. PRINCIPLES.md(헌법) Read   ← 경량 헌법, 비서 tier 포함
   (보고 형식·도구·MCP 인지맵·// 레지스트리 해석 능력은 본 AGENT.md 본문이 보유 →
    AGENT.md Read 자체로 활성화. 별도 Lazy 로드 트리거 전제조건 없음 — R-3 불변식 근거)

#### Phase B — PM tier (승격 게이트: 현재 cwd에 `.opal/AGENT.md` 존재 시에만)
> 게이트: cwd `.opal/AGENT.md` 부재 → Phase B 전체 스킵 (harness·opal-pm·PM 컨텍스트 미로드). R-2.
3. opal-harness.md Read         ← .opal/AGENT.md 존재 시에만
4. opal-pm.md Read              ← .opal/AGENT.md 존재 시에만
5. 프로젝트 .opal/AGENT.md Read  ← (게이트 신호 자신)
   + MEMORY.md 브리핑 (프로젝트 메모리 브리핑 절 연동)

#### 공통 (Phase A 직후, B 유무 무관)
6. Antigravity 한정 부트스트래퍼 자동 삽입  ← 현 step 6 (F-002에서 서술 반전)
6.5. cwd 판별 next-action  ← 현 step 6.5 그대로 (이미 .opal/AGENT.md 신호 사용)
7. 활성화 (비서 또는 PM)
```

- **PM 승격 게이트 = `.opal/AGENT.md` 존재** (→ D-1 §행동규칙 역할전환 표와 동일 신호). `[MUST] 'opal/core/AGENT.md' §행동규칙: "PM | 프로젝트 내 (.opal/AGENT.md 존재) | 프로젝트 모든 상호작용 관리"` — 이 신호를 Eager 무거운 로드(step 3·4·5) 앞으로 게이팅하는 것이 변경의 전부. 역할전환 표·완료보고 PM모드 칼럼이 이미 동일 신호를 쓰므로 정합(H-2).
- **`//` 불변식(R-3)**: `//` 커맨드 Lazy 트리거의 전제 조건은 `-`(없음) (→ D-1 §Lazy 트리거 테이블 `:39`). 즉 Phase B(harness/PM) 미로드 상태에서도 `//` 입력 → skill-commands.md Lazy 로드 → `//opi` 발동 가능. Phase A 박스에 "비서 tier는 `//`(opi 포함) 커맨드/스킬 레지스트리 해석 능력을 보유한다 — `//` Lazy 트리거는 harness/PM 로드를 전제하지 않는다" 취지 1줄을 명문화(H-3).
- **설계원칙 박스 정합**(`opal/core/AGENT.md:7`): 현 "Eager 단계에서 PRINCIPLES + identity + opal-harness + opal-pm + PM 컨텍스트를 즉시 로드"를 "Phase A(비서, 항상)=PRINCIPLES+identity / Phase B(PM, `.opal/AGENT.md` 존재 시 승격)=harness+pm+PM 컨텍스트"로 서술 정합.
- **부트스트랩 완료 보고 정합**(`opal/core/AGENT.md:55-67`): 비서 tier(`.opal/AGENT.md` 부재) 세션에서 `harness`·`PM` 체크가 `⬜`(해당 없음)로 표기되도록 보고 라인 규칙 1줄 보강. 현 보고 코드블록(`:60`)은 PM 세션 기준 ✅ 나열 — 비서 세션 시 `⬜ harness ⬜ PM ⬜ PM모드` 표기 규칙을 추가. (`PM모드` 칼럼 규칙 `:65`는 이미 미존재 시 ⬜.)

> [MUST] `opal/core/PRINCIPLES.md` Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic." — 2-phase 게이트 로직은 AGENT.md(플랫폼 독립)에만 둔다. 플랫폼 조건문 추가 금지 (H-9).
> [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction." — AGENT.md 물리 파일 분할·신규 게이트 값 도입은 범위 외. step 번호 보존 + Phase 라벨만 부여.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
install 재배포(캡틴 수행)가 변경된 `opal/core/AGENT.md`를 strip 후 `~/.opal/AGENT.md`로 반영. 코드 변경 측 배치 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | AGENT.md Eager 절에 Phase A/Phase B 구분 + Phase B 진입 조건 "`.opal/AGENT.md` 존재" 문구 grep 매칭 |
| TS-002 | R-2 AC | 산출물 검사 | `.opal/AGENT.md` 부재 시 harness·opal-pm 미Read 절차가 Phase B 게이트로 명문화됨(grep) |
| TS-003 | R-3 AC | 산출물 검사 | Phase A에 "비서 tier `//`(opi 포함) 발동 가능" + Lazy `//` 트리거 전제조건 부재 단언 |
| TS-004 | R-1 | 산출물 검사 | step 0(스킵게이트) 불변 — setting.json+bootstrap+off+fail-safe 문구 보존 (H-8 가드) |
| TS-005 | R-1·R-3 | 실세션(L3) | 비-opi 폴더 새 세션: 비서 활성 + harness/PM 미로드 + `//opi` 발동 가능 |

---

### F-002: AGENT.md "부트스트래퍼 자동 관리" 절 논리 반전

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 에이전트 | "프로젝트 부트스트래퍼 자동 관리" 절(§383-417) 서술을 "전역=비서 상시 / 프로젝트 마커=PM 승격 신호+이식성"으로 반전. Eager step 6(§24) 문구 정합 | (→ D-1 §부트스트래퍼 자동 관리) |

#### 3.2.2 설계
- 절 도입부(`:385`) "프로젝트 마커는 잉여" → "전역 마커는 비서 tier를 상시 활성화하고, 프로젝트 마커는 (Claude/Cursor/Codex) PM 승격을 강화하는 보조 신호이자 (Gemini/Codex) 이식성·폴백 트리거다"로 반전.
- Claude 소절(`:387-407`) "프로젝트 마커는 항상 잉여"(`:394`) → "PM 승격 게이트는 `.opal/AGENT.md` 존재이므로 프로젝트 `CLAUDE.md` 마커는 PM tier 진입에 불필요(중복·무해). 단 전역 마커가 임의 제거된 환경의 폴백 진입점으로 수동 삽입 가능"으로 정합.
- Cursor(`:409-411`)·Codex(`:413-417`) 소절도 동일 취지로 "이식성·폴백" 서술 추가. Antigravity(`:419-427`)는 기존 자동 삽입 유지 + 2-tier에서 "Gemini 전역 진입점이 다르므로 프로젝트 마커가 비서 tier 진입에 필요" 서술 정합.
- **불변**: 자동 삽입 동작(Claude/Cursor/Codex 스킵, Gemini 수행)은 변경하지 않는다 — 서술(이유)만 2-tier로 반전. (헌법 §3 Surgical — 동작 불변, 논리 서술만.)
- Eager step 6(`:24`) "프로젝트 마커는 불필요" 문구를 절과 동기.

> [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임)." — 이 절은 플랫폼별 자동 삽입 정책 서술이므로 기존 구조(어댑터 책임 위임)를 유지하며 논리만 반전.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음 (install 재배포 시 반영).

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-7 AC | 산출물 검사 | "부트스트래퍼 자동 관리" 절이 Claude/Cursor/Codex/Gemini 각각에 2-tier(전역=비서/프로젝트=PM·이식성) 서술 반영. "잉여" 단정 제거 grep |

---

### F-003: 전역 마커 경량화 — bootstrapper 4종 + install 검증

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/bootstrapper/claude-bootstrap.md` | 부트스트래퍼 | 마커 콘텐츠 비서 진입 의미 1줄 정합 + 변경이력 049 행 | (→ D-4) |
| 2 | `opal/bootstrapper/gemini-bootstrap.md` | 부트스트래퍼 | 동상 + 변경이력 049 행 | (→ D-4) |
| 3 | `opal/bootstrapper/codex-bootstrap.md` | 부트스트래퍼 | 동상 + 변경이력 049 행 | (→ D-4) |
| 4 | `opal/bootstrapper/cursor-bootstrap.mdc` | 부트스트래퍼 | 본문 의미 정합 (frontmatter 무손상). 변경이력 표 없음 — 본문 주석 행만 | (→ D-4) |

> install-mac.sh·windows.ps1은 **변경 대상 아님** — 마커 교체 메커니즘이 이미 콘텐츠 단위 치환+사용자 내용 보존을 제공(검증만).

#### 3.3.2 설계
- **변경 최소화 원칙**: bootstrapper 콘텐츠는 이미 "`~/.opal/AGENT.md` Read → identity.md Read"만 지시하고 tier 로직을 담지 않는다. 따라서 마커 본문은 거의 불변 유지하고, **"이 진입점은 비서 tier를 활성화하며, PM 승격은 AGENT.md가 `.opal/AGENT.md` 존재 시 자동 수행한다" 취지 1줄**만 정합 추가(선택적·과서술 금지 — 헌법 §3). 핵심은 **AGENT.md(F-001)가 2-phase로 바뀌면 전역 마커가 가리키는 진입점이 자동으로 비서부터 시작**한다는 점이다.
- **install 콘텐츠 교체 검증(R-4)**: `install_opal_section`(`scripts/install-mac.sh:274-293`)이 `OPAL START/END` 구간을 새 content로 치환 + 마커 밖 사용자 내용 보존. 이 동작이 "구 무거운 마커 → 신 경량 마커 능동 교체"를 충족함을 L1(추출 무결)·L2(멱등 셸 테스트)로 검증. `[MUST]` 마커 단위 치환이므로 콘텐츠 교체만으로 구버전 제거 완료.
- **cursor frontmatter 보존(H-5)**: `cursor-bootstrap.mdc`의 `---`/`alwaysApply: true` frontmatter 무손상 — 본문 의미 행만 정합. install은 cursor를 `cp`로 통째 복사(`:1210`)하므로 frontmatter 그대로 배포.
- **변경이력**: claude/gemini/codex bootstrap.md는 변경이력 표 보유 → 049 행 추가(KST `2026-06-30 16:xx` + semver bump). cursor.mdc는 변경이력 표 없음(043 선례 동일) → 표 추가하지 않음(헌법 §3 — 불필요 구조 도입 금지).

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." — bootstrapper 3종에 049 행 추가.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
install 재배포(캡틴)가 신 마커를 4 플랫폼 전역 파일로 치환. L2 멱등 셸 테스트로 사전 검증.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-5 AC | 산출물 검사 | bootstrapper 4종 마커 콘텐츠가 비서 진입과 일치(setting.json 게이트 보존 + AGENT.md 진입). claude/gemini/codex에 049 변경이력 행 |
| TS-008 | R-5 | 산출물 검사 | cursor-bootstrap.mdc frontmatter `---`/`alwaysApply: true` 무손상 (H-5) |
| TS-009 | R-4 AC | 동작계약(L2) | 임시 HOME에 사용자 내용+구 마커 선배치 → `install_opal_section` 호출 → START/END 구간 신 콘텐츠 치환 + 마커 밖 사용자 내용 보존 + 멱등(2회) |
| TS-010 | R-4 | 산출물 검사 | install-mac.sh `bash -n` 통과 + `install_opal_section` 호출부 4건(claude/gemini/codex + cursor cp) grep. windows.ps1 `Register-Bootstrapper` 4 플랫폼 매칭 |

---

### F-004: opi 전 플랫폼 마커 + Codex `AGENTS.md` 보강

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-project-init/templates/common/platform/AGENTS.md` | 스킬 | Codex 프로젝트 마커 템플릿 (CLAUDE.md 템플릿과 동일 마커 콘텐츠) | (→ D-5) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `opal/skills/opal-project-init/scripts/apply.js` | 스킬 | `PLATFORM_FILES`에 `{src:"platform/AGENTS.md", dest:"AGENTS.md"}` 행 추가. `AGENTS.md`는 `mergeOther` 경로(기본 분기 — CLAUDE.md만 mergeClaudeMd) | `apply.js:21-25` |
| 3 | `opal/skills/opal-project-init/SKILL.md` | 스킬 | Phase 4-1 플랫폼 파일 표(§561-563)에 AGENTS.md 행 추가 + 기존 파일 처리 서술(§565-568) + 완료 보고 플랫폼 파일 목록(§616)에 AGENTS.md. 변경이력 049 행 | (→ D-5 §Phase 4) |

#### 3.4.2 설계
- **AGENTS.md 템플릿**: `CLAUDE.md` 템플릿(`templates/common/platform/CLAUDE.md`)과 **동일 마커 콘텐츠** 사용:
  ```
  # === OPAL START ===
  ## OPAL AI Agent — 필수 부트스트랩
  **[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. ...
  1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
  2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 ...)
  # === OPAL END ===
  ```
  Codex CLI는 글로벌→프로젝트 순으로 `AGENTS.md`를 자동 로드(전역 부트스트래퍼 절 인용 — `opal/core/AGENT.md:415` [Codex AGENTS.md 가이드]). 프로젝트 `AGENTS.md`는 이식성·폴백 트리거.
- **apply.js 배열 추가**: `PLATFORM_FILES`(`apply.js:21-25`)에 4번째 항목 추가. 병합 분기(`apply.js` main `dest === "CLAUDE.md" ? mergeClaudeMd : mergeOther`)는 그대로 — `AGENTS.md`는 자동으로 `mergeOther` 경로(마커 구간 교체 또는 append + `.bak` 백업)를 탄다. **분기 로직 수정 불필요**(H-7 — 기존 mergeOther가 마커 단위 멱등 병합 제공).
- **SKILL.md 표 갱신**: Phase 4-1 생성 표에 `templates/common/platform/AGENTS.md → {프로젝트}/AGENTS.md | OPAL 부트스트래퍼` 행 추가. 기존 파일 처리 bullet(§567)에 "`AGENTS.md`: 기존 파일 `.bak` 백업 후 마커 병합" 추가. 완료 보고 플랫폼 파일 목록(§616 "CLAUDE.md, GEMINI.md, .cursorrules")에 AGENTS.md 추가.
- **install 배포 자동 포함**: `templates/`는 `install_dir` 재귀 복사로 배포되므로 신규 `AGENTS.md` 템플릿이 install 변경 없이 `~/.opal/skills/opal-project-init/templates/`에 포함됨.

> [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction." — apply.js 병합 분기 일반화·신규 함수 도입 금지. 배열 1행 + 템플릿 1파일 + 기존 mergeOther 재사용.

#### 3.4.3 환경 변경
해당 없음 (Node.js 기존 의존 — apply.js 실행 환경 불변).

#### 3.4.4 배치/마이그레이션
install 재배포가 신규 템플릿을 `~/.opal/...`로 반영. opi 실행 시 apply.js가 4파일 생성.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-6 | 산출물 검사 | `templates/common/platform/AGENTS.md` 존재 + `# === OPAL START/END ===` 마커 + AGENT.md/identity.md 지시 grep |
| TS-012 | R-6 | 산출물 검사 | apply.js `PLATFORM_FILES`에 AGENTS.md 항목 추가 + `node -c` 구문 무결 + 병합 분기에서 AGENTS.md가 mergeOther 경로 |
| TS-013 | R-6 AC | 동작계약(L2) | 임시 프로젝트에서 `node apply.js --project-root {tmp}` → CLAUDE.md+GEMINI.md+.cursorrules+AGENTS.md 4파일 생성. 각 마커 포함 |
| TS-014 | R-6 AC | 산출물 검사 | opi SKILL.md Phase 4-1 표·기존파일처리·완료보고에 AGENTS.md 반영 + 변경이력 049 행 |
| TS-015 | R-6 | 동작계약(L2) | 기존 AGENTS.md(사용자 내용 + 구 마커) 선배치 → apply.js 2회 실행 → 마커 구간만 교체 + 사용자 내용 보존 + 멱등 (H-7) |

---

### F-005: docs 정합

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/ARCHITECTURE.md` | 문서 | 부트스트랩 진입에 2-tier(비서 항상 / PM `.opal/AGENT.md` 승격) 구조 추가 + 변경이력 행 | (→ D-6) |
| 2 | `docs/PROJECT.md` | 문서 | 변경이력 행 추가 (2-tier 부트스트랩 반영) | (→ D-6) |
| 3 | `docs/CONVENTIONS.md` | 문서 | (해당 시) 변경이력 행 — 신규 규칙 없으면 스킵 | (→ D-6) |

#### 3.5.2 설계
- ARCHITECTURE: §시스템 구성 다이어그램 또는 별도 소절에 "부트스트랩 2-tier: Phase A 비서(전역 마커·항상) / Phase B PM(`.opal/AGENT.md` 존재 시 승격 — harness·pm·PM 컨텍스트)" 기술. 진입 다이어그램(`docs/ARCHITECTURE.md:9-52`)에 tier 분기 1줄 또는 소절 추가.
- PROJECT.md 변경이력(`docs/PROJECT.md:136-141`)에 `2026-06-30 | 부트스트랩 2-tier 전환 — 비서(전역 상시)/PM(opi 프로젝트 opt-in) 분리 (049)` 행 추가.
- CONVENTIONS: 본 작업은 신규 규칙 도입 없음(배포 경계·플랫폼 분기 격리 기존 규칙 준수) → 변경이력 행은 CONVENTIONS 본문이 바뀌는 경우에만 추가. PM이 EXECUTE 시점에 본문 변경 유무로 판단(기본 스킵).

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 변경이력 일시 KST·semver·태스크 번호 포맷 준수.

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-9 AC | 산출물 검사 | ARCHITECTURE.md에 2-tier 부트스트랩 구조 기술 + PROJECT.md 변경이력 049 행 grep |

---

### F-006: setting.json 불변 보장 (회귀 0)

#### 3.6.1 파일 변경 계획
**신규/수정 없음** — 검증 전용 기능. F-001~F-004의 변경이 setting.json 스키마·`bootstrap:off` 게이트·models 2-레이어 우선순위를 건드리지 않음을 회귀 테스트로 보증.

#### 3.6.2 설계
- step 0(스킵게이트+머지)은 F-001에서 **문구·위치 불변**으로 보존(Phase A 최상단). `bootstrap:off` → step 1~7 전체 스킵, models effective setting 머지(전역 base + 로컬 셀 덮어쓰기) 동작은 변경되지 않는다.
- 검증: AGENT.md step 0 문구가 043 태스크 게이트와 동일하게 보존(`setting.json`+`bootstrap`+`off`+fail-safe). bootstrapper 4종 스킵게이트 문구 보존.

> [MUST] `opal/core/PRINCIPLES.md` §2: setting.json 스키마 변경·신규 게이트 값 도입은 범위 외. 회귀 0.

#### 3.6.3 환경 변경
해당 없음.

#### 3.6.4 배치/마이그레이션
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-017 | R-8 AC | 산출물 검사(회귀) | AGENT.md step 0 + bootstrapper 4종 스킵게이트 문구가 setting.json+bootstrap+off+fail-safe 보존. models 우선순위 서술 불변 |
| TS-018 | R-8 AC | 실세션(L3) | 전역 `setting.json bootstrap:off`=전 세션 스킵 / 프로젝트 `setting.local.json bootstrap:off`=해당 프로젝트만 스킵 동작 (회귀) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 단독 | AGENT.md Eager 2-phase — 핵심, 선행 |
| 1 | F-004 | 4 | opal-task-agent | F-001과 병렬 가능 | opi 영역(독립 파일 — templates/apply.js/SKILL.md) |
| 2 | F-002 | 2 | opal-task-agent | F-001 후 순차 | 동일 파일(AGENT.md) — 충돌 방지 순차 |
| 2 | F-003 | 3 | opal-task-agent | F-001 후 | bootstrapper 4종 (AGENT.md 2-phase 전제) |
| 3 | F-005 | 5 | PM 직접 | F-001~F-004 후 | docs 정합 |
| 횡단 | F-006 | (검증) | opal-test-agent | TEST 단계 | 산출물 없음 — 회귀 검증만 |

### 4.2 실행 체크리스트
> 총 5개 Step | Phase 3개 | 실행 모드: 복잡 (변경 파일 9개 ≥ 4 + 다중 모듈)

#### Step 1: AGENT.md Eager 단계 2-phase 재구성 (F-001)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: Eager 단계를 Phase A(비서·항상: step 0 스킵게이트 불변 + identity + PRINCIPLES + 보고형식·도구맵·`//` 레지스트리 해석 능력)/Phase B(PM·`.opal/AGENT.md` 존재 시 승격: harness + opal-pm + 프로젝트 AGENT.md + MEMORY 브리핑)로 재구성. step 번호 보존 + Phase 라벨 부여(물리 분할 없음). Phase A에 "비서 tier `//`(opi 포함) 발동 가능 — `//` Lazy 트리거는 harness/PM 로드를 전제하지 않음" 1줄 명문화. 설계원칙 박스(§7)·부트스트랩 완료 보고(§55-67) 비서 세션 `⬜` 표기 규칙 정합. 변경이력 049 행 추가
- **완료 기준**: Phase A/B 구분 + Phase B 게이트("`.opal/AGENT.md` 존재") + `//` 불변식 명문화 + step 0 불변 보존 + 변경이력 049 행. TS-001~004 grep PASS
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: AGENT.md "부트스트래퍼 자동 관리" 절 논리 반전 (F-002)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: "프로젝트 부트스트래퍼 자동 관리" 절(§383-417) 서술을 "전역 마커=비서 tier 상시 / 프로젝트 마커=PM 승격 보조(Claude/Cursor/Codex)·이식성·폴백 트리거(Gemini/Codex)"로 반전. "프로젝트 마커는 잉여" 단정 제거. 자동 삽입 동작(Claude/Cursor/Codex 스킵·Gemini 수행)은 불변. Eager step 6(§24) 문구 동기
- **완료 기준**: 4 플랫폼 각각 2-tier 서술 반영 + "잉여" 단정 제거 + 동작 불변. TS-006 grep PASS
- **테스트**: TS-006
- **실행 방법**: sub-agent
- **의존**: Step 1 (동일 파일 AGENT.md — 순차)

#### Step 3: bootstrapper 4종 소스 정합 + install 검증 (F-003)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 부트스트래퍼
- **agent**: opal-task-agent
- **파일**: `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`
- **작업 내용**: 4종 마커 콘텐츠에 "비서 tier 진입점 — PM 승격은 AGENT.md가 `.opal/AGENT.md` 존재 시 자동 수행" 취지 1줄 정합(과서술 금지). 스킵게이트 문구 불변. cursor.mdc frontmatter(`---`/`alwaysApply:true`) 무손상. claude/gemini/codex에 변경이력 049 행 추가(KST+semver). install-mac.sh/windows.ps1은 변경하지 않고 검증만(마커 교체 메커니즘 재사용)
- **완료 기준**: 4종 마커 비서 진입 정합 + setting.json 게이트 보존 + cursor frontmatter 무손상 + 3종 049 변경이력. TS-007~010 PASS
- **테스트**: TS-007, TS-008, TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1 (AGENT.md 2-phase 전제 — 마커가 가리키는 진입점)

#### Step 4: opi 전 플랫폼 마커 + Codex AGENTS.md 보강 (F-004)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-project-init/templates/common/platform/AGENTS.md`(신규), `opal/skills/opal-project-init/scripts/apply.js`, `opal/skills/opal-project-init/SKILL.md`
- **작업 내용**: (a) Codex `AGENTS.md` 템플릿 신규 생성(CLAUDE.md 템플릿과 동일 마커 콘텐츠). (b) apply.js `PLATFORM_FILES`에 `{src:"platform/AGENTS.md", dest:"AGENTS.md"}` 행 추가(병합 분기는 기존 mergeOther 재사용 — 수정 없음). (c) SKILL.md Phase 4-1 표·기존파일처리·완료보고에 AGENTS.md 반영 + 변경이력 049 행
- **완료 기준**: AGENTS.md 템플릿(마커 포함) + apply.js 배열 4항목(node 구문 무결) + SKILL.md 반영. TS-011~015 PASS
- **테스트**: TS-011, TS-012, TS-013, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: 없음 (F-001과 병렬 — 독립 파일)

#### Step 5: docs 정합 (F-005)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`, (해당 시 `docs/CONVENTIONS.md`)
- **작업 내용**: ARCHITECTURE에 2-tier 부트스트랩 구조(Phase A 비서 항상 / Phase B PM `.opal/AGENT.md` 승격) 기술 + 변경이력 행. PROJECT.md 변경이력 049 행. CONVENTIONS는 본문 변경 시에만 변경이력 행(기본 스킵)
- **완료 기준**: ARCHITECTURE 2-tier 기술 + PROJECT 049 변경이력. TS-016 PASS
- **테스트**: TS-016
- **실행 방법**: direct (PM 직접)
- **의존**: Step 1~4 (코드 변경 확정 후 문서 정합)

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 동일 파일(`opal/core/AGENT.md`) 순차 수정 — 충돌 방지 |
| Step 1 → Step 3 | bootstrapper 마커가 AGENT.md를 가리킴 — 2-phase 전제 후 정합 (논리 의존) |
| Step 1 ∥ Step 4 | 독립 파일군(AGENT.md vs opi templates/apply.js/SKILL.md) — 병렬 가능 |
| Step 2 ∥ Step 3 | 서로 독립 파일(AGENT.md 절 vs bootstrapper) — 단, 둘 다 Step 1 후 |
| Step 1~4 → Step 5 | docs는 코드 변경 확정 후 정합 (산출물 의존) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | Eager Phase A/B 구분 + PM 게이트 + `//` 불변식 | TS-001, TS-002, TS-003, TS-005 | Phase A/B 명시 + Phase B 게이트 "`.opal/AGENT.md` 존재" + `//` 발동 명문화 + 실세션 비-opi 폴더 비서 활성·PM 미로드·`//opi` 발동 |
| F-002 | 부트스트래퍼 관리 절 2-tier 반전 | TS-006 | 4 플랫폼 2-tier 서술 + "잉여" 단정 제거 |
| F-003 | 전역 마커 비서 정합 + install 교체 동작 | TS-007, TS-008, TS-009, TS-010 | 4종 마커 비서 진입 + cursor frontmatter 무손상 + install 마커 치환·사용자 내용 보존·멱등 |
| F-004 | opi 4파일 생성 + Codex AGENTS.md | TS-011, TS-012, TS-013, TS-014, TS-015 | AGENTS.md 템플릿 + apply.js 배열 + 4파일 생성 + 멱등 병합 + SKILL.md 반영 |
| F-005 | docs 2-tier 정합 | TS-016 | ARCHITECTURE 2-tier 기술 + PROJECT 변경이력 |
| F-006 | setting.json 회귀 0 | TS-017, TS-018 | step 0·게이트 문구 불변 + off 스위치(전역/프로젝트) 정상 |

### 5.2 회귀 테스트
- [ ] setting.json 스키마·`bootstrap:off` 게이트·models 2-레이어 우선순위 불변 (TS-017, TS-018)
- [ ] opi 기존 3종(CLAUDE/GEMINI/.cursorrules) 생성 동작 비파괴 (TS-013)
- [ ] install 마커 교체 시 마커 밖 사용자 내용 보존 (TS-009)
- [ ] AGENT.md 역할전환 표·완료보고 PM모드 칼럼 등 기존 `.opal/AGENT.md` 신호 사용처 정합 (TS-001)
- [ ] Antigravity 자동 삽입 동작 불변 (Step 2 동작 불변 확인)

### 5.3 코드/문서 품질
- [ ] 변경이력 기록 — AGENT.md, claude/gemini/codex-bootstrap.md, opi SKILL.md, ARCHITECTURE.md, PROJECT.md에 049 행(KST 일시·semver·태스크 번호) (`docs/CONVENTIONS.md §변경이력 작성 의무`)
- [ ] apply.js `node -c` 구문 무결 / install-mac.sh `bash -n` 무결 / windows.ps1 구조 무결
- [ ] cursor.mdc 변경이력 표 부재 — 표 신설하지 않음 (043 선례 정합)
- [ ] 플랫폼 분기는 어댑터(install)에만 — AGENT.md 로직에 플랫폼 조건문 부재 (TS-011/H-9)

### 5.4 보안
- [ ] 마커 콘텐츠·템플릿·bootstrapper에 토큰/시크릿 없음
- [ ] 신규 권한 표면 0 — 기존 `Read(~/.opal/**)` 재사용, 신규 권한 등록 없음
- [ ] AGENTS.md 템플릿은 부트스트랩 진입 지시만 (민감정보 비저장)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 9개 (AGENT.md, bootstrapper 4종, AGENTS.md 템플릿, apply.js, opi SKILL.md, ARCHITECTURE/PROJECT) | **복잡** |
| 모듈 범위 | 다중 (코어 에이전트 / 부트스트래퍼 / 스킬 / 문서) | **복잡** |
| 작업 유형 | 부트스트랩 진입 모델 구조 개선 | **복잡** |
| 외부 의존성 | 없음 (기존 install·apply.js 메커니즘 재사용) | 단순 |
| **실행 모드** | **복잡** | |

> **설계 피드백 — Full Task(opd) 에스컬레이션 검토**: 변경 파일 9개로 규모 점검 임계(10개)에 근접하나 미달이고, 각 변경은 서술 정합·배열 1행·템플릿 1파일 수준의 저위험 surgical 변경이다. 다단계 의사결정은 캡틴 답변 3건으로 이미 확정됨(추가 의사결정 없음). 따라서 Short Task(opds) 유지가 적합하며 Full Task 에스컬레이션은 불요로 판단한다. 단 복잡 모드이므로 §7 실행 아키텍처를 포함한다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬):
  Agent-A: opal-task-agent → Step 1 (AGENT.md 2-phase)
  Agent-B: opal-task-agent → Step 4 (opi templates/apply.js/SKILL.md — AGENT.md와 독립 파일)

Batch 2 (Step 1 완료 후, 동일 AGENT.md 충돌 방지 직렬 + bootstrapper):
  Agent-A: opal-task-agent → Step 2 (AGENT.md 절 반전 — 동일 파일이므로 Agent-A 연속)
  Agent-C: opal-task-agent → Step 3 (bootstrapper 4종 — 독립 파일, Step 2와 병렬 가능)

Batch 3 (전 코드 변경 후):
  PM 직접 → Step 5 (docs 정합)

TEST 단계 (PM이 opal-test-agent 디스패치):
  opal-test-agent → F-006 회귀 + L1/L2 동작계약 (TEST-SCENARIO.md 기반)
```
> **파일 충돌 방지**: AGENT.md를 만지는 Step 1·2는 동일 에이전트(Agent-A)에 직렬 배치. bootstrapper(Step 3)·opi(Step 4)는 독립 파일군이므로 별도 에이전트 병렬.

### C-2. 스킬 요구사항
- 모든 EXECUTE Step은 `op-dev-execute` 스킬로 수행(단계 스킬 재사용). 신규 스킬 갭 없음(Markdown/JS/Bash 편집은 범용 워커 역량 내).
- 갭 판별: 동일 패턴 3+ Step 반복 없음 → 스킬 신설 불요. 인라인 지침으로 충분.

### C-3. 도구 요구사항
- CLI: `node`(apply.js 구문 체크·동작계약), `bash`(install-mac.sh `bash -n`·셸 동작계약), `python3`(JSON 유효성 — 회귀). 모두 기존 환경 보유.
- MCP: 불요.
- 패키지: 신규 설치 없음.

### C-4. 테스트 전략 (opal-test-agent)
- **RED-first 트랙(혼합)**: F-003 install 마커 교체 동작계약(TS-009)·F-004 apply.js 4파일 생성·멱등 병합(TS-013, TS-015)은 동작 로직 → **RED-first 적격**(작성자≠구현자, RED 셸/node 테스트 선작성 → FAIL 증거 → GREEN). F-001~F-002·F-005·F-006 문서 grep 단언은 정적 검증 트랙. 상세는 TEST-SCENARIO.md §RED-first 판단.
- **기능 테스트**: L1(산출물 grep/구문 — AGENT.md·bootstrapper·SKILL.md·apply.js·docs) → L2(install 멱등 셸 테스트 + apply.js 임시 프로젝트 실행) → L3(실세션 동작 — 캡틴 직접: 비-opi 비서/PM 미로드/`//opi` 발동/opi 후 승격/off 스위치).
- **회귀**: setting.json off 스위치(전역/프로젝트) + opi 기존 3종 생성.
- **코드 품질**: 변경이력 049 행 / `bash -n` / `node -c`.
- **보안**: 시크릿 스캔 / 신규 권한 표면 0.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 에이전트/부트스트래퍼/docs | Markdown | (해당 없음 — 범용 편집) |
| install | Bash (`install-mac.sh`), PowerShell (`windows.ps1`) | (검증만) |
| opi | Node.js (apply.js), Markdown (SKILL.md/templates) | (해당 없음) |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 본 작업은 OPAL 내부 부트스트랩 구조 개선 — 외부 라이브러리 API 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL AGENT.md (부트스트랩 SSOT) | `opal/core/AGENT.md` | Eager 2-phase 재구성·부트스트래퍼 관리 절 반전 대상 |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh:251-325`, `:1206-1225` | 마커 교체 메커니즘·호출부 4건 (검증) |
| D-3 | 소스 | windows.ps1 | `scripts/install/windows.ps1:809-872` | Register-Bootstrapper·Install-OpalSection (검증) |
| D-4 | 소스 | bootstrapper 4종 | `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md`, `cursor-bootstrap.mdc` | 전역 마커 콘텐츠 SSOT |
| D-5 | 소스 | opi 스킬 | `opal/skills/opal-project-init/SKILL.md:547-568`, `scripts/apply.js:21-25`, `templates/common/platform/` | 프로젝트 마커 생성·Codex AGENTS.md 보강 대상 |
| D-6 | 설계 | PROJECT/ARCHITECTURE/CONVENTIONS | `docs/PROJECT.md:134-141`, `docs/ARCHITECTURE.md:9-85`, `docs/CONVENTIONS.md:194-208` | docs 정합 + 변경이력·배포경계·플랫폼분기 [MUST] 인용 |
| D-7 | 설계 | 헌법 | `opal/core/PRINCIPLES.md:12-27` | 플랫폼 분기 격리(Core Stance)·Simplicity First [MUST] 근거 |
| D-8 | 소스 | 043 태스크 (선례) | `tasks/043-260624-opds-부트스트랩-게이트-설정파일-전환/TEST-SCENARIO.md` | install 동작계약·grep 단언·RED-first 혼합 패턴 참조 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | Phase A에서 비서 필수 항목(PRINCIPLES/identity/보고형식) 누락 → 전역 비서 사망 | F-001 (H-1) | P0 | TS-001 grep + TS-005 실세션. Phase A 항목 체크리스트 명문화 |
| R-2 | PM 게이트 누수 — 비-opi 폴더에서 harness/pm 로드 → opt-in 불변식 깨짐 | F-001 (H-2) | P0 | TS-002 절차 단언 + TS-005 비-opi 세션 미로드 확인 |
| R-3 | `//` 불변식 깨짐 — 비서 tier에서 `//opi` 발동 불가 | F-001 (H-3) | P0 | TS-003 Lazy 전제조건 부재 단언 + TS-005 `//opi` 실발동 |
| R-4 | install 마커 교체가 사용자 내용 손상 | F-003 (H-4) | P0 | TS-009 동작계약(마커 밖 보존+멱등). install 로직 불변(검증만) |
| R-5 | cursor frontmatter 손상 | F-003 (H-5) | P1 | TS-008 frontmatter 무손상 grep |
| R-6 | opi가 AGENTS.md 미생성 (배열 누락) | F-004 (H-6) | P0 | TS-012 배열 단언 + TS-013 4파일 생성 동작계약 |
| R-7 | apply.js 병합 회귀 (AGENTS.md 분기 오류) | F-004 (H-7) | P1 | TS-015 멱등 병합. mergeOther 재사용(신규 분기 도입 금지) |
| R-8 | setting.json 게이트 회귀 | F-006 (H-8) | P0 | TS-017 step 0 불변 grep + TS-018 off 스위치 실세션 |
| R-9 | 플랫폼 분기 누수 — tier 로직이 bootstrapper/install에 침투 | F-003 (H-9) | P1 | 로직은 AGENT.md에만(헌법 §Core Stance). bootstrapper는 진입점만 |
| R-T1 | 용어 일관성 — "비서/Lite tier" vs "PM/Full tier" 토큰 통일 필요 | 전 기능 | P2 | 산출물 전반에서 "비서(Lite) tier"·"PM(Full) tier" 표기 통일. AGENT.md·docs·bootstrapper 동일 토큰 사용 (citation-rules §7) |

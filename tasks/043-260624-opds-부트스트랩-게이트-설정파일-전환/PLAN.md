# PLAN: 부트스트랩 스킵 게이트 — 환경변수 → 배포 설정파일(setting.json) 전환

> 작성일: 2026-06-24 | 입력: TASK.md (ANALYSIS.md 없음 — F-NNN별 직접 코드 분석)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

040이 도입한 부트스트랩 스킵 게이트의 메커니즘을 **Bash 환경변수 체크(`echo $OPAL_BOOTSTRAP`)에서 배포 설정파일(`~/.opal/setting.json`) Read 기반으로 전환**한다. 게이트가 부트스트랩이 이미 무프롬프트로 통과하는 Read 경로(`~/.opal/AGENT.md`·`identity.md` Read)에 얹혀 매 세션 권한 프롬프트 없이 자동 수행되도록 하고, `setting.json`을 향후 런타임 설정 확장의 거점으로 삼는다. 게이트 명령 소스 6곳(S-1~S-6)을 setting.json Read 기반으로 교체하고, install이 `setting.json`을 create-if-absent로 신규 배포하며, 폐기되는 환경변수 메커니즘(직전 L2 추가분 `Bash(echo $OPAL_BOOTSTRAP)` 권한 포함)을 정리한다.

### 1.2 핵심 검증 — Read 경로 무프롬프트 가정 (TASK 규명사항 #1)

> **[검증 완료]** "fresh 세션에서 `Read(~/.opal/**)`가 무프롬프트인가"라는 핵심 가정을 코드 근거로 실증한다.

| 근거 | 확인 결과 |
|------|----------|
| install이 Claude 권한에 Read 경로를 등록 | `install_claude_permissions`가 `perm_entries`에 `Read({opal_home}/**)`, `Read(~/.opal/**)`를 등록한다 (`scripts/install-mac.sh:395`). 절대/틸다 두 형태 모두 등록되어 Claude Code가 어느 형태로 매칭해도 무프롬프트 통과. |
| 부트스트랩이 이미 동일 경로를 Read | Eager step 1·2는 `~/.opal/identity.md`/`AGENT.md`를 Read한다 (`opal/core/AGENT.md:15-16`). 040 도입 세션에서도 이 Read는 프롬프트 없이 통과했다(캡틴 문제 제기는 오직 Bash `echo`). |
| 040 게이트의 프롬프트 원인 | `echo $OPAL_BOOTSTRAP`는 셸 변수 확장(simple_expansion)을 포함해 Claude Code가 read-only로 보증하지 못하고, 허용 규칙으로도 자동 승인되지 않는다 (TASK §배경분석 §1). |

**귀결**: 게이트를 `Read(~/.opal/setting.json)`로 전환하면 **새 권한 표면 0**. `Read(~/.opal/**)` 글롭이 이미 `setting.json`을 포괄하므로 추가 권한 등록 불요. macOS 외 플랫폼(Windows/Linux/Cursor/Gemini/Codex)은 권한 등록 패리티가 애초에 쟁점에서 사라진다 — Read 경로 재사용이기 때문(TASK §배경분석 §4). 단, Bash echo 권한이 등록되지 않은 플랫폼이 만약 있었다면(현 macOS만 존재) 이번 전환이 그 갭까지 해소한다.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `setting.json` 배포 소스 신규 + install create-if-absent 배포 | R-1, R-2 | P0 | 없음 |
| F-002 | 게이트 로직 전환 — 코어 AGENT.md step 0 + 부트스트래퍼 4종 (S-1~S-5) | R-3, R-4 | P0 | 없음 (논리적으로 F-001 산출물 가정) |
| F-003 | 환경변수 접근·권한 정리 (S-6) — `Bash(echo $OPAL_BOOTSTRAP)` 권한 제거 + 미커밋 reconcile | R-5 | P0 | 없음 |
| F-004 | 변경이력 행 추가 (수정 문서·스크립트 전체) | R-6 | P1 | F-001, F-002, F-003 |

> **F-002 통합 근거**: S-1(코어 AGENT.md)·S-2~S-5(부트스트래퍼 4종)는 모두 동일 setting.json 게이트 의미를 동일 위치 규칙으로 받는 "게이트 문구 교체" 단일 논리 작업이다(plan-guide §1 그룹핑 기준 — 논리적으로 함께 테스트 가능한 묶음). 단 5개 파일 각각의 변경은 §3.2·§5.1에서 개별 추적한다.
> **F-004 분리 근거**: 변경이력은 F-001~F-003 모든 수정 파일에 걸치는 횡단 요구라 별도 F로 추적하되, 실행은 각 수정 Step 내에서 함께 처리한다(§4.2 참조).

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 (setting.json 소스 + install 배포)
F-002 (게이트 문구 6→5곳 교체)        [F-001과 독립 파일 — 병렬]
F-003 (환경변수 권한 정리)             [독립 — 병렬]
        └──────┬──────┘
               F-004 (변경이력 — 각 수정 Step에 흡수)
```

> 3개 핵심 F는 서로 다른 파일군을 수정(F-001=install+신규소스 / F-002=AGENT.md+bootstrapper / F-003=install perm 블록)하므로 병렬 가능. 단 F-001과 F-003은 동일 파일 `scripts/install-mac.sh`를 수정하므로 **같은 에이전트·순차 처리**한다(§4.3 파일 충돌 방지).

### 1.5 핵심 제약 (PLAN 영향 [MUST] 인용)

- [MUST] `docs/CONVENTIONS.md` §구현 규칙(배포 경계): "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." → 모든 수정 대상은 소스에 한정. `setting.json` 실배포·실세션 검증은 캡틴 install 재실행 시점 (→ D-2 §구현 규칙).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙(플랫폼 분기 격리): "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다." → 게이트 로직(setting.json Read)은 플랫폼 독립 행위로 기술하고, 배포 분기는 install 어댑터에만 (→ D-2 §구현 규칙).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙(Guards): "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다." → 본 PLAN 단계는 설계 문서(PLAN.md/TEST-SCENARIO.md)만 작성, 소스 미수정 (→ D-2 §구현 규칙).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙(변경이력 작성 의무): "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" → F-004 (→ D-2 §구현 규칙).
- fail-safe 불변(TASK §확정방향 §3, 040 계승): 값이 `off`면 스킵 / 파일 부재·필드 부재·파싱 실패 = 정상 진행. 게이트 불확실 시 항상 정상 부트스트랩으로 안전 수렴.
- create-if-absent(TASK §확정방향 §4): install이 `setting.json`을 **없을 때만** 생성 — 사용자 토글이 재설치에도 보존.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 install create-if-absent 함수 | "존재 시 불변(멱등)" 계약 위반 — 기존 `setting.json`을 덮어써 사용자 토글(off) 소실 | P0 (사용자 토글 유실 → 의도와 반대로 부트스트랩 동작) | L1(단위: 함수 호출 전후 기존 파일 내용 불변 검사) + L2(install dry-run/2회 실행 후 내용 동일) | S-1, S-2 |
| H-2 | F-001 install create-if-absent 함수 | "부재 시 생성" 계약 — 부재 시 유효 JSON(`{"bootstrap":"on"}`) 생성 실패 | P1 (게이트 거점 미배포 — 단, fail-safe로 정상 부트스트랩되므로 치명 아님) | L1(단위: 부재 상태에서 1회 실행 후 유효 JSON + bootstrap 키 존재) | S-3 |
| H-3 | F-002 게이트 조건 표현 (5곳) | LLM이 "`off`이면 스킵"을 과확대 해석 → 파일 부재/필드 부재/`on` 세션도 스킵 | P0 (정상 세션 부트스트랩 누락) | L1(문구 명확성 리뷰: fail-safe 분기 명시 여부) + L3(설정/부재 세션 실동작) | S-4, S-5 |
| H-4 | F-002 게이트 동기 (6→5곳 의미 일치) | 코어 AGENT.md step 0과 부트스트래퍼 4종의 조건(`bootstrap==off`)·동작(전부 스킵)·fail-safe 표현 불일치 | P1 (문서 간 모순 — 마커와 AGENT.md 정의 괴리) | L1(5곳 문구 의미 일치 교차 검사) | S-6 |
| H-5 | F-002 cursor `.mdc` | cursor-bootstrap.mdc는 frontmatter(`---`)+산문 구조이며 코드블록이 아닌 **파일 전체 복사** 배포(`scripts/install-mac.sh:1115`). 삽입 위치·포맷이 다른 3종과 상이 | P0 (Cursor 마커 누락 또는 frontmatter 파손) | L1(파일 구조 검사: `---` frontmatter 무손상) | S-7 |
| H-6 | F-002 claude/codex/gemini 코드블록 | 게이트 문구에 코드 펜스(` ``` `) 삽입 시 `extract_bootstrap_content`(`scripts/install-mac.sh`) 추출 조기 종료 | P0 (부트스트랩 마커 추출 깨짐) | L1(산출물 검사: 코드 펜스 미사용, 인라인 백틱만) + L2(install 재배포 후 배포 파일 내용 확인) | S-8 |
| H-7 | F-003 권한 정리 | `perm_entries`에서 `Bash(echo $OPAL_BOOTSTRAP)` 제거 후 install python json 블록 구문 파손 (`bash -n` 실패) | P1 (install 실행 불능) | L1(`bash -n scripts/install-mac.sh` 통과) + L1(perm_entries에 echo 잔존 0) | S-9 |
| H-8 | F-001 setting.json 게이트 우선순위 (프로젝트 오버라이드) | TASK 미확정 항목 — `{프로젝트}/.opal/setting.json` 채택 시 글로벌과의 우선순위 규칙 부재로 모호 | P2 (확장 시 혼선 — 현 범위는 글로벌 단일) | L1(범위 외 명시: §3.1.2 결정 D-1로 글로벌만 채택, 오버라이드는 후속) | S-10 |

**가설 도출 메모**: H-1(멱등성)·H-2(생성)는 install create-if-absent 함수의 동작 계약 — RED-first 트랙 적격(§RED-first 판단). H-3·H-4는 "LLM이 읽는 산문 게이트"의 본질적 모호성 리스크로 문구 정밀도가 완료기준을 좌우(정적 검증 트랙). H-5·H-6은 040에서 검증된 추출/복사 메커니즘 의존성을 계승.

---

## 2. 기능별 분석

### F-001: `setting.json` 배포 소스 신규 + install create-if-absent 배포

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/core/setting.default.json` (신규) | 배포용 기본 설정 소스 — `{"bootstrap":"on"}` | 신규 |
| 배치 | `scripts/install-mac.sh` | create-if-absent 배포 함수 신규 + `install_opal` 호출부 추가 | 수정 |
| 배치 | `scripts/install/windows.ps1` | (PLAN 판단) create-if-absent 배포 — Install-OpalCore 내 신규 블록 | 수정(범위 결정 §3.1.2) |
| 배치 | `scripts/install/linux.sh` | install-mac.sh를 `exec` 위임하는 순수 wrapper — **자동 상속, 수정 불요** | 검증 |

#### 2.1.2 현재 구현

**install_opal 배포 흐름** (`scripts/install-mac.sh:933-1182`):
- `clean_dirs=("skills" "agents" "references" "templates" "tools" "dashboard-server")`를 rm -rf로 클린 후 재배포한다 (`scripts/install-mac.sh:954-960`).
- **사용자 데이터 보존 항목**: `identity.md`, `AGENT.md`, `projects/`, `community-skills/`는 clean_dirs에 없어 보존되거나 strip_deploy_md로 갱신 배포된다 (`scripts/install-mac.sh:961`). 단 `AGENT.md`는 `strip_deploy_md`로 매번 덮어쓴다(`:964`) — 사용자 편집 비대상.
- 코어 배포 패턴: `strip_deploy_md "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"` (`:964`), PRINCIPLES.md 동일 (`:968`). 이들은 **무조건 덮어쓰기**라 setting.json(사용자 토글 보존)에는 부적합.

**멱등 json 처리 기존 패턴** (`install_claude_permissions`, `scripts/install-mac.sh:382-420`):
- `/usr/bin/python3 -c "..."`로 settings.json을 읽어(`json.loads(content) if content else {}`) 키가 없을 때만 append하는 멱등 패턴. setting.json 생성에 동형 적용 가능 — 단 setting.json은 "파일 자체 부재 시 생성, 존재 시 전혀 건드리지 않음"이 계약(키 병합 아님).

**Windows 미러** (`scripts/install/windows.ps1` Install-OpalCore):
- AGENT.md 보존 주석: "보존: identity.md, AGENT.md(덮어쓰지만 후속 사용자 메모는 별도 위치), projects/, .venv/". `Copy-Item -Force`로 AGENT.md 덮어쓰기. setting.json은 `if (-not (Test-Path ...))` 가드로 create-if-absent 신규 블록 필요.
- `Remove-ChangelogSection` (= mac `strip_deploy_md` 대응)이 존재.

**Linux** (`scripts/install/linux.sh:1-39`): `exec bash "${INSTALLER}" "$@"`로 install-mac.sh에 전량 위임하는 wrapper. install-mac.sh에 추가한 setting.json 배포는 Linux에 자동 상속(별도 코드 변경 불요).

#### 2.1.3 영향 범위

- **상위 의존(소비자)**: 게이트 5곳(F-002)이 `~/.opal/setting.json`을 Read한다. 단 fail-safe로 파일 부재도 정상 동작 → setting.json 배포는 "게이트 거점 제공"이지 부트스트랩 필수 선행은 아님(H-2 영향 완화).
- **하위 의존**: install 메뉴 [1]/[3] 재실행 시 발효. 별도 마이그레이션 불요(멱등).
- **공유 상태**: `~/.opal/setting.json`은 사용자 토글 상태를 담는 사용자 데이터. clean_dirs·strip_deploy_md 어느 경로도 거치면 안 됨(H-1 — 멱등성).
- **관련 테스트**: install create-if-absent는 동작 로직 → RED-first 적격(§RED-first 판단). bash 함수 단위 검증.

---

### F-002: 게이트 로직 전환 — 코어 AGENT.md step 0 + 부트스트래퍼 4종 (S-1~S-5)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | OPAL AGENT 정의 소스 (배포본 `~/.opal/AGENT.md` 원천) — Eager step 0 게이트 (S-1) | 수정 |
| 환경 | `opal/bootstrapper/claude-bootstrap.md` | Claude `~/.claude/CLAUDE.md` 마커 SSOT (코드블록 추출) — S-2 | 수정 |
| 환경 | `opal/bootstrapper/gemini-bootstrap.md` | Gemini `~/.gemini/GEMINI.md` 마커 SSOT (코드블록 추출) — S-3 | 수정 |
| 환경 | `opal/bootstrapper/codex-bootstrap.md` | Codex `~/.codex/AGENTS.md` 마커 SSOT (코드블록 추출) — S-4 | 수정 |
| 환경 | `opal/bootstrapper/cursor-bootstrap.mdc` | Cursor `~/.cursor/rules/000-opal-agent.mdc` 마커 SSOT (**파일 전체 복사**) — S-5 | 수정 |

#### 2.2.2 현재 구현 (게이트 소스 6곳 전수 — 라인 재확인 완료)

| # | 파일 | 현재 게이트 위치·내용 | 배포 메커니즘 |
|---|------|---------------------|-------------|
| S-1 | `opal/core/AGENT.md:13` | Eager step 0: "먼저 Bash 도구로 `echo $OPAL_BOOTSTRAP`를 1회 실행한다. 출력이 정확히 `off`이면 — 이하 step 1~7 전체 … 생략 … Bash를 쓸 수 없으면 게이트를 무시하고 step 1부터 정상 진행" | `strip_deploy_md`로 `~/.opal/AGENT.md` 배포 (변경이력 위 본문만) (`scripts/install-mac.sh:964`) |
| S-2 | `opal/bootstrapper/claude-bootstrap.md:17` | 코드블록 내 `> **[스킵 게이트]** … echo $OPAL_BOOTSTRAP …` | `extract_bootstrap_content` → `install_opal_section` 멱등 삽입 (`scripts/install-mac.sh:1111`) |
| S-3 | `opal/bootstrapper/gemini-bootstrap.md:17` | 코드블록 내 동일 게이트 | install_opal_section (`scripts/install-mac.sh:1123`) |
| S-4 | `opal/bootstrapper/codex-bootstrap.md:17` | 코드블록 내 동일 게이트 | install_opal_section (`scripts/install-mac.sh:1129`) |
| S-5 | `opal/bootstrapper/cursor-bootstrap.mdc:8` | frontmatter `---` 직후 산문 `**[스킵 게이트]** … echo $OPAL_BOOTSTRAP …` | **파일 전체 복사** `cp ... 000-opal-agent.mdc` (`scripts/install-mac.sh:1115`) |
| S-6 | `scripts/install-mac.sh:395` (+ 변경이력 `:35`) | `perm_entries`에 `'Bash(echo $OPAL_BOOTSTRAP)'` (직전 L2 미커밋 추가분) | F-003에서 처리 |

> **S-5 라인 확정**: TASK에서 "라인 미확인"으로 표기된 cursor-bootstrap.mdc 게이트는 **`:8`** (frontmatter 종료 `---`(`:4`) 직후 본문 첫 문단)에 위치함을 grep으로 확인 (`opal/bootstrapper/cursor-bootstrap.mdc:8`).

3종(claude/codex/gemini)은 동일 구조 — 산문 헤더 + ` ```markdown `…` ``` ` 코드블록 내부에 `> **[스킵 게이트]**` 인용 문단 + `**[MUST]**` 본문. cursor는 frontmatter + 산문 본문(코드블록 없음).

#### 2.2.3 영향 범위

- **상위 의존(소비자)**: 모든 OPAL 세션의 부트스트랩 진입. 마커(S-2~S-5)는 "`~/.opal/AGENT.md`를 Read하라" 지시 → AGENT.md step 0(S-1)이 setting.json을 Read하여 게이트 판정. 두 계층의 조건·동작·fail-safe 표현은 일치해야 함(H-4).
- **번호 체계 영향**: step 0은 040에서 이미 추가됨 — 내용만 교체(Bash echo → setting.json Read). 기존 1~7 번호 불변.
- **추출 경계 민감도**: claude/codex/gemini 코드블록 내부에 코드 펜스 추가 시 추출 조기 종료(H-6). 게이트 문구에 코드 펜스 금지, 인라인 백틱(`` `~/.opal/setting.json` ``)만 사용.
- **strip 경계**: AGENT.md 게이트(step 0)는 `## 변경이력` 위 본문에 위치(현 `:13`) → `strip_deploy_md`(awk `/^## 변경이력$/{keep=0}`, `scripts/install-mac.sh:222-225`)가 잘라내지 않음. 위치 불변 유지.

---

### F-003: 환경변수 접근·권한 정리 (S-6)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | `install_claude_permissions` perm_entries에서 `Bash(echo $OPAL_BOOTSTRAP)` 제거 + 관련 주석 정리 + 헤더 변경이력 reconcile | 수정 |

#### 2.3.2 현재 구현

- `perm_entries = [f'Read({opal_home}/**)', 'Read(~/.opal/**)', 'Bash(echo $OPAL_BOOTSTRAP)']` (`scripts/install-mac.sh:395`) — 직전 L2(미커밋)로 추가된 echo 권한.
- 직전 주석 `# 부트스트랩 스킵 게이트가 매 세션 실행하는 OPAL_BOOTSTRAP 점검 명령도 무프롬프트 허용` (`scripts/install-mac.sh:394`).
- 헤더 변경이력 `v3.5 … perm_entries에 'Bash(echo $OPAL_BOOTSTRAP)' 추가 …` (`scripts/install-mac.sh:35`) — 미커밋.
- `git status`: `M scripts/install-mac.sh` — 이 미커밋 변경분이 이번 전환의 reconcile 대상.

#### 2.3.3 영향 범위

- **상위 의존**: `install_claude_permissions`는 `install_opal`에서 1회 호출(`scripts/install-mac.sh:1133`). echo 권한 제거 후에도 `Read(~/.opal/**)` 글롭이 setting.json Read를 포괄하므로 게이트 동작에 영향 없음.
- **무프롬프트 보장 불변**: Read 권한 2개는 유지 → setting.json Read 무프롬프트 보장(§1.2).
- **구문 무결성**: python json 블록 리스트 1개 항목 제거 — `bash -n` 통과 필수(H-7).
- **미커밋 reconcile**: v3.5 변경이력 행은 "추가"였으나 이번에 "원복/대체"된다. 변경이력은 누적 보존(소급 삭제 금지, citation-rules §5 레거시 호환 정신) — v3.5는 남기되 v3.6 행으로 "echo 권한 제거 + setting.json 전환"을 기록(F-004).

---

## 3. 기능별 설계

### F-001: `setting.json` 배포 소스 신규 + install create-if-absent 배포

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/core/setting.default.json` | 환경 | 배포용 기본 설정 — `{"bootstrap":"on"}` (기본 on, fail-safe 기본값) | TASK §확정방향 §2; 기존 opal/core/ 코어 자산 배치 패턴(AGENT.md/PRINCIPLES.md) (`scripts/install-mac.sh:964,968`) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `scripts/install-mac.sh` | 배치 | create-if-absent 배포 함수 `install_opal_setting` 신규 + `install_opal` 내 호출부 추가 + 헤더 변경이력 행 | `install_claude_permissions` 멱등 python json 패턴(`:382-420`); 코어 배포 호출 위치(`:964-969`) |
| 3 | `scripts/install/windows.ps1` | 배치 | Install-OpalCore 내 create-if-absent 블록(`if (-not (Test-Path setting.json))`) 추가 + 헤더 변경이력 | Install-OpalCore AGENT.md 보존 패턴 미러 |

#### 3.1.2 API·데이터 모델·화면 설계

**setting.json 스키마** (`opal/core/setting.default.json`):

```json
{
  "bootstrap": "on"
}
```

- [MUST] 스키마 시작점 `{"bootstrap": "on"|"off"}`, 기본 `on` (→ TASK §확정방향 §2). `off`만 스킵 트리거, 그 외 모든 값(`on`/임의 문자열/키 부재)은 정상 진행(fail-safe).
- 향후 키 확장 거점 — 추가 런타임 설정은 이 객체에 키를 누적(범위 외, 후속).

**소스 위치 결정 D-1** (TASK 규명사항 #2 — setting.json 소스 위치):
- 채택: `opal/core/setting.default.json`. 근거 — `opal/core/`는 install이 `~/.opal/` 루트로 직접 배포하는 코어 자산 디렉토리(AGENT.md→`~/.opal/AGENT.md`, PRINCIPLES.md→`~/.opal/PRINCIPLES.md`; `scripts/install-mac.sh:964,968`). `setting.json`도 `~/.opal/` 루트에 놓이므로 동일 디렉토리가 자연스럽다.
- 파일명에 `.default` 접미 — "배포 소스(불변 기본값)"와 "배포본(사용자 토글 가능)"을 명시 구분. 배포본은 `~/.opal/setting.json`, 소스는 `setting.default.json`. 배포본 직접편집 금지 원칙([MUST] §1.5)과 정합 — 소스는 항상 기본값만 보유.

**create-if-absent 배포 함수** (`scripts/install-mac.sh` 신규 `install_opal_setting`):

```
install_opal_setting() {
    local src="$FRAMEWORK_ROOT/opal/core/setting.default.json"
    local dst="$USER_HOME/.opal/setting.json"
    if [[ -f "$dst" ]]; then
        # 멱등: 존재 시 절대 덮어쓰지 않음 (사용자 토글 보존) — H-1
        info "setting.json 이미 존재 — 보존 (사용자 설정 유지)"
        return 0
    fi
    cp "$src" "$dst"
    success "OPAL setting.json (기본값) → $dst"
}
```

- [MUST] 멱등성 — 존재 시 불변(H-1). `[[ -f "$dst" ]]` 가드로 early return. `strip_deploy_md`/clean_dirs 경로를 **거치지 않음**(사용자 데이터 보존 항목과 동급).
- 호출 위치: `install_opal` 내 코어 배포 직후(`scripts/install-mac.sh:969` PRINCIPLES.md 배포 다음 줄)에 `install_opal_setting` 호출 추가. clean_dirs 클린(`:954-960`) 이후여야 함(클린이 setting.json을 건드리지 않지만 순서 안전).

**Windows 미러** (`scripts/install/windows.ps1` Install-OpalCore 내 신규 블록):

```powershell
# ── OPAL 기본 설정: opal/core/setting.default.json → ~/.opal/setting.json (create-if-absent) ──
$settingSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'setting.default.json')
$settingDst = Join-Path $OpalHome 'setting.json'
if ((Test-Path $settingSrc) -and -not (Test-Path $settingDst)) {
    Copy-Item -Path $settingSrc -Destination $settingDst
    Write-OpalOk "OPAL setting.json (기본값) → $settingDst"
} elseif (Test-Path $settingDst) {
    Write-OpalInfo 'setting.json 이미 존재 — 보존 (사용자 설정 유지)'
}
```

**Windows/Linux install 정합 결정 D-2** (TASK 규명사항 #5):
- **Linux**: `linux.sh`가 install-mac.sh를 `exec` 위임하는 순수 wrapper(`scripts/install/linux.sh:39`)이므로 setting.json 배포가 **자동 상속**. 코드 변경 불요 — 검증만(TS-013).
- **Windows**: `windows.ps1`은 독립 PowerShell 미러이므로 create-if-absent 블록을 명시 추가한다(범위 포함). 근거 — Read 기반 게이트는 권한 등록 패리티가 불요하나, setting.json '배포'는 각 플랫폼 install이 해줘야 사용자가 토글 가능. 단 파일 부재 시 fail-safe로 정상 동작하므로 배포 누락이 치명적이지 않음 → 우선순위는 P0(F-001 포함)이되, Windows 미반영도 fail-safe 안전망이 있다는 점을 명시.

**프로젝트 오버라이드 결정 D-3** (TASK 규명사항 #6 — `{프로젝트}/.opal/setting.json`):
- **범위 외(현 태스크 제외)**. 근거 — TASK §명확화결과에서 "미확정"으로 표기된 항목이며, 우선순위 규칙(글로벌 vs 프로젝트)을 도입하면 게이트 로직(현 단일 Read)이 복잡해진다. 현 전환의 목표는 "무프롬프트 + 단일 거점"이므로 글로벌 `~/.opal/setting.json` 단일 채택. 프로젝트 오버라이드는 후속 태스크에서 우선순위 규칙(프로젝트 > 글로벌 등)과 함께 설계(H-8). 게이트 문구에도 "`~/.opal/setting.json`" 단일 경로만 명시.

#### 3.1.3 환경 변경

신규 배포 파일 `~/.opal/setting.json` (install 재배포 시 create-if-absent). 추가 패키지 없음.

#### 3.1.4 배치/마이그레이션

install 재배포 시 `install_opal_setting`(mac/linux)·Install-OpalCore 블록(windows)이 setting.json을 없을 때만 생성. 별도 마이그레이션 스크립트 불요(멱등). 040의 환경변수 사용자는 setting.json 미존재 → 신규 생성(기본 on)되며, 환경변수가 폐기되므로 캡틴이 off 토글하려면 setting.json 편집.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | `opal/core/setting.default.json` 존재 + 유효 JSON + `bootstrap` 키 보유 (값 `"on"`) |
| TS-002 | R-2 AC (멱등) | 기능 테스트 (RED-first) | 기존 `~/.opal/setting.json`(예: `{"bootstrap":"off"}`)이 있는 상태에서 `install_opal_setting` 호출 시 내용 **불변** (H-1) |
| TS-003 | R-2 AC (생성) | 기능 테스트 (RED-first) | `~/.opal/setting.json` 부재 상태에서 `install_opal_setting` 호출 시 유효 JSON 생성 + `bootstrap` 키 존재 (H-2) |
| TS-004 | R-2 AC (구문) | 산출물 검사 | `bash -n scripts/install-mac.sh` 통과 + `install_opal`에 `install_opal_setting` 호출부 존재 |
| TS-013 | R-2 AC (Linux 상속) | 산출물 검사 | `scripts/install/linux.sh`가 install-mac.sh exec 위임 구조 유지(setting.json 배포 자동 상속) — 별도 코드 부재 확인 |
| TS-014 | R-2 AC (Windows) | 산출물 검사 | `scripts/install/windows.ps1` Install-OpalCore에 create-if-absent setting.json 블록 존재 (`Test-Path` 가드) |

---

### F-002: 게이트 로직 전환 — 코어 AGENT.md step 0 + 부트스트래퍼 4종 (S-1~S-5)

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 4 | `opal/core/AGENT.md` | 문서 | step 0(:13) 내용 교체: Bash echo → setting.json Read 게이트. `[WORKER 규칙]` 구분 유지. 변경이력 행 | `opal/core/AGENT.md:13` |
| 5 | `opal/bootstrapper/claude-bootstrap.md` | 환경 | 코드블록 내 게이트(:17) 교체 (코드 펜스 금지). 변경이력 행 | `opal/bootstrapper/claude-bootstrap.md:17` |
| 6 | `opal/bootstrapper/gemini-bootstrap.md` | 환경 | #5와 동일 위치·문구. 변경이력 행 | `opal/bootstrapper/gemini-bootstrap.md:17` |
| 7 | `opal/bootstrapper/codex-bootstrap.md` | 환경 | #5와 동일 위치·문구. 변경이력 행 | `opal/bootstrapper/codex-bootstrap.md:17` |
| 8 | `opal/bootstrapper/cursor-bootstrap.mdc` | 환경 | frontmatter `---`(:4) 직후 산문 게이트(:8) 교체. frontmatter 무손상. (변경이력 표 부재 — §3.2.2 결정) | `opal/bootstrapper/cursor-bootstrap.mdc:8` |

#### 3.2.2 API·데이터 모델·화면 설계

해당 없음(마크다운 산문 변경). **교체 문구 초안**을 워커가 그대로 사용하도록 확정한다. 5곳 모두 의미 동일(H-4 동기): 조건=`bootstrap` 필드가 `off`, 동작=전체 스킵, fail-safe=파일/필드 부재·파싱 실패 시 정상 진행.

##### 게이트 문구 초안 — 코어 AGENT.md step 0 (S-1)

기존 step 0(`opal/core/AGENT.md:13`)을 아래로 교체:

```
0. **[스킵 게이트]** 먼저 Read 도구로 `~/.opal/setting.json`을 읽는다. JSON의 `bootstrap` 필드 값이 정확히 `off`이면 — 이하 step 1~7 전체(정체성·헌법·하네스·PM·PM 컨텍스트 포함 부트스트랩 전부)를 생략하고 OPAL 없이 순수 동작한다(부트스트랩 완료 보고도 생략). 파일이 없거나·`bootstrap` 필드가 없거나·`off`가 아니거나(예: `on`)·JSON 파싱에 실패하면 게이트를 무시하고 step 1부터 정상 진행한다(fail-safe). 이 게이트는 세션/캡틴 전역 토글이며, 위 `[WORKER 규칙]`(디스패치 프롬프트 첫 줄 `[WORKER]`)과는 별개의 독립 스킵 경로다.
```

> 설계 결정 근거:
> - "Read 도구로 `~/.opal/setting.json`" — Bash echo 폐기, 무프롬프트 Read 경로 재사용(§1.2). 새 권한 표면 0 (→ §1.2).
> - "정확히 `off`" 단일 매칭 + "파일/필드 부재·파싱 실패 시 정상 진행" fail-safe 명시 — H-3 방어, 040 fail-safe 계승(TASK §확정방향 §3).
> - "step 0" 위치·`[WORKER 규칙]` 구분 불변 — 040 구조 계승(H-4 회귀 차단).
> - `## 변경이력` 위 본문 위치(현 :13) → strip_deploy_md 배포 보장 (`scripts/install-mac.sh:222-225`).

##### 게이트 문구 초안 — claude/codex/gemini 코드블록용 (S-2~S-4, 3종 동일)

기존 코드블록 내 게이트(:17)를 아래로 교체(코드 펜스 미사용, 인라인 백틱만 — H-6):

```
> **[스킵 게이트]** 먼저 Read 도구로 `~/.opal/setting.json`을 읽는다. JSON의 `bootstrap` 필드 값이 정확히 `off`이면 — 이하 OPAL 부트스트랩 절차 전체(정체성 포함)를 생략하고, OPAL 없이 순수 동작한다. 파일이 없거나·`bootstrap` 필드가 없거나·`off`가 아니거나·JSON 파싱에 실패하면 — 게이트를 무시하고 아래 절차를 정상 수행한다(fail-safe).
```

> 설계 결정 근거: AGENT.md step 0과 동일 의미(H-4 동기). 코드블록 추출 경계 보존을 위해 코드 펜스 금지, 인라인 백틱만(H-6) (→ `scripts/install-mac.sh` extract_bootstrap_content 경계).

##### 게이트 문구 초안 — cursor `.mdc`용 (S-5, 산문 직접)

frontmatter `---`(:4) 종료 직후 `# OPAL AI Agent` 본문 게이트(:8)를 아래로 교체:

```
**[스킵 게이트]** 먼저 Read 도구로 `~/.opal/setting.json`을 읽는다. JSON의 `bootstrap` 필드 값이 정확히 `off`이면 이하 OPAL 활성화 절차(정체성 포함)를 전부 생략하고 순수 동작한다. 파일이 없거나·`bootstrap` 필드가 없거나·`off`가 아니거나·JSON 파싱에 실패하면 게이트를 무시하고 아래 절차를 정상 수행한다(fail-safe).
```

> cursor는 frontmatter(`---`) 바깥 본문에만 삽입 — 구조 무손상(H-5). 의미는 4곳과 동일(H-4).

**cursor 변경이력 결정 D-4**: `cursor-bootstrap.mdc`는 변경이력 표가 없는 frontmatter+산문 구조다(`opal/bootstrapper/cursor-bootstrap.mdc` 전체 10줄). 040도 cursor에는 변경이력 행을 추가하지 않았다. F-004는 변경이력 표가 있는 파일(AGENT.md·claude/codex/gemini-bootstrap.md·install-mac.sh 헤더)에만 적용하고, cursor는 표 부재로 생략(소스 구조 보존).

#### 3.2.3 환경 변경

해당 없음. (install 재배포 시 발효 — 본 단계는 소스 수정만.)

#### 3.2.4 배치/마이그레이션

install 재배포 시: AGENT.md는 strip_deploy_md로(`:964`), bootstrapper 3종은 install_opal_section 멱등 마커 교체로(`:1111,1123,1129`), cursor는 파일 전체 복사로(`:1115`) 갱신. 멱등 — 중복 누적 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-3 AC | 산출물 검사 | `opal/core/AGENT.md` step 0이 `~/.opal/setting.json` Read 게이트로 교체됨 + `echo $OPAL_BOOTSTRAP` 문자열 0건 + fail-safe 분기(파일/필드 부재·파싱실패) 명시 + `[WORKER]` 구분 유지 |
| TS-006 | R-4 AC (claude) | 산출물 검사 | `claude-bootstrap.md` 코드블록 내 setting.json 게이트 존재 + `echo $OPAL_BOOTSTRAP` 0건 + 코드 펜스 추가 없음(추출 무결) |
| TS-007 | R-4 AC (gemini) | 산출물 검사 | `gemini-bootstrap.md` 코드블록 내 setting.json 게이트 + echo 0건 |
| TS-008 | R-4 AC (codex) | 산출물 검사 | `codex-bootstrap.md` 코드블록 내 setting.json 게이트 + echo 0건 |
| TS-009 | R-4 AC (cursor) | 산출물 검사 | `cursor-bootstrap.mdc` 본문 setting.json 게이트 + echo 0건 + `---` frontmatter 구조 무손상 |
| TS-010 | R-3+R-4 (동기) | 산출물 검사 | 5곳 게이트의 조건(`off`)·동작(전부 스킵)·fail-safe 표현 의미 일치 (H-4) |
| TS-011 | 완료기준 ②③ (실세션) | 통합 테스트 | install 재배포 후 setting.json `off` 세션이 **프롬프트 없이** 부트스트랩 스킵 / `on`·필드제거·파일부재 세션 정상 부트스트랩 (수동 — 환경·캡틴 install 의존) |

---

### F-003: 환경변수 접근·권한 정리 (S-6)

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 9 | `scripts/install-mac.sh` | 배치 | `perm_entries`에서 `'Bash(echo $OPAL_BOOTSTRAP)'` 제거(:395) + 직전 주석(:394) 정리 + 헤더 변경이력 reconcile(:35) | `scripts/install-mac.sh:394-395, :35` |

#### 3.3.2 API·데이터 모델·화면 설계

해당 없음. **변경 명세**:
- `perm_entries = [f'Read({opal_home}/**)', 'Read(~/.opal/**)']`로 복원(echo 항목 제거) — Read 2개 유지(무프롬프트 보장 §1.2).
- 주석 `:394` (`# 부트스트랩 스킵 게이트가 매 세션 실행하는 OPAL_BOOTSTRAP 점검 명령도 무프롬프트 허용`) 제거 — Read 경로 재사용으로 echo 점검 자체가 사라짐.
- 헤더 변경이력(:35) v3.5 행은 누적 보존(소급 삭제 금지). F-004에서 v3.6 행 추가로 "echo 권한 제거 + setting.json 게이트 전환" 기록.

> 설계 결정 근거: Read 경로(`Read(~/.opal/**)`)가 setting.json을 이미 포괄 → echo 권한 잉여(§1.2). 미커밋 v3.5 변경분을 이번 전환으로 reconcile(TASK §배경분석 §5). [MUST] 단일 메커니즘 통일(TASK §확정방향 §5).

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

install 재실행 시 기존 `~/.claude/settings.json`에 이미 등록된 `Bash(echo $OPAL_BOOTSTRAP)` 권한은 install이 자동 제거하지 않는다(멱등 append-only 패턴, `scripts/install-mac.sh:408-411`). 잔존해도 무해(미사용 권한). 캡틴 수동 정리 선택 — 본 태스크는 소스 잔존 0 보장에 한정(완료기준 ⑤).

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 AC | 산출물 검사 | `scripts/install-mac.sh` `perm_entries`에 `echo $OPAL_BOOTSTRAP` 0건 + `bash -n` 통과 (H-7) |
| TS-015 | 완료기준 ⑤ (소스 잔존 0) | 회귀 테스트 | 전체 소스(`opal/`, `scripts/`)에서 `echo $OPAL_BOOTSTRAP` Bash 게이트 grep 0건 (변경이력 행의 과거 기록 제외) |

---

### F-004: 변경이력 행 추가

#### 3.4.1 파일 변경 계획

**수정** (각 F의 수정 Step에 흡수 — §4.2)

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 10 | `opal/core/AGENT.md` 변경이력 표 | 문서 | v3.7 행: setting.json 게이트 전환 (043) | `opal/core/AGENT.md:452` 다음 행 |
| 11 | `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md` 변경이력 표 | 환경 | 각 신규 버전 행: echo→setting.json 게이트 (043) | 각 파일 변경이력 표 말미 |
| 12 | `scripts/install-mac.sh` 헤더 변경이력 | 배치 | v3.6 행: install_opal_setting 신규 + perm echo 제거 (043) | `scripts/install-mac.sh:35` 다음 |
| 13 | `scripts/install/windows.ps1` 헤더 변경이력 | 배치 | 신규 행: Install-OpalCore setting.json create-if-absent (043) | windows.ps1 헤더 변경이력 말미 |

#### 3.4.2 API·데이터 모델·화면 설계

해당 없음. 변경이력 포맷: `| vX.Y | YYYY-MM-DD HH:mm | <내용> (043) |` (KST). [MUST] `docs/CONVENTIONS.md` §변경이력: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (→ D-2 §구현 규칙).

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R-6 AC | 산출물 검사 | 수정한 각 파일(AGENT.md·claude/gemini/codex-bootstrap.md·install-mac.sh 헤더·windows.ps1 헤더)에 043 변경이력 행 존재 (cursor.mdc 제외 — 표 부재 D-4) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-be-agent | 순차 (install + 신규 소스) | setting.json 소스 + install create-if-absent (mac/windows) + Linux 검증 |
| 1 | F-002 | 2 | opal-task-agent | 병렬 가능 (F-001과 독립 파일) | 게이트 문구 5곳 교체 |
| 2 | F-003 | 3 | opal-be-agent | 순차 (F-001 후 — 동일 install-mac.sh) | perm echo 제거 + reconcile |
| 2 | F-004 | (각 Step 흡수) | (각 Step agent) | — | 변경이력은 수정 Step 내 처리 |

### 4.2 실행 체크리스트

> 총 3개 Step | Phase 2개 | 실행 모드: 복잡 (변경 파일 6개 + RED-first 트랙 + 다중 플랫폼 어댑터)

#### Step 1: setting.json 배포 소스 신규 + install create-if-absent 배포
- [ ] 완료
- **소속 기능**: F-001 (+ F-004 변경이력 #12,#13)
- **영역**: 배치
- **agent**: opal-be-agent
- **파일**: `opal/core/setting.default.json` (신규), `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/install/linux.sh` (검증)
- **작업 내용**: ①`opal/core/setting.default.json` 생성 `{"bootstrap":"on"}`. ②install-mac.sh에 `install_opal_setting` 함수 신규(§3.1.2 — `[[ -f "$dst" ]]` 멱등 가드 + create-if-absent) + `install_opal` 코어 배포 직후(`:969` 다음)에 호출부 추가 + 헤더 v3.6 변경이력. ③windows.ps1 Install-OpalCore에 create-if-absent 블록(§3.1.2 PowerShell) + 헤더 변경이력. ④linux.sh는 exec 위임 구조 확인만(수정 없음).
- **완료 기준**: TS-001~TS-004, TS-013, TS-014 통과 — 소스 유효 JSON + 멱등(존재 시 불변) + 부재 시 생성 + `bash -n` 통과 + Linux 상속/Windows 블록 확인
- **테스트**: TS-001, TS-002(RED-first), TS-003(RED-first), TS-004, TS-013, TS-014, TS-016
- **실행 방법**: sub-agent
- **의존**: 없음 (단 Step 3과 동일 install-mac.sh → Step 3을 Step 1 후 순차)

#### Step 2: 게이트 문구 5곳 setting.json Read 기반 교체 (S-1~S-5)
- [x] 완료
- **소속 기능**: F-002 (+ F-004 변경이력 #10,#11)
- **영역**: 문서/환경 (혼합 — AGENT.md=문서, bootstrapper 4종=환경)
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`, `opal/bootstrapper/claude-bootstrap.md`, `opal/bootstrapper/gemini-bootstrap.md`, `opal/bootstrapper/codex-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`
- **작업 내용**: §3.2.2 교체 문구 초안 적용 — AGENT.md step 0(:13) = "코어 AGENT.md" 문구, claude/codex/gemini 코드블록(:17) = "코드블록용" 문구(코드 펜스 금지·인라인 백틱만), cursor(:8) = "cursor용" 산문 문구(frontmatter 무손상). 5곳 모두 `echo $OPAL_BOOTSTRAP` 제거. 변경이력 표 있는 4파일(AGENT.md·claude/gemini/codex)에 043 행 추가, cursor 생략(표 부재 D-4).
- **완료 기준**: TS-005~TS-010 통과 — 5곳 게이트 setting.json Read로 교체 + echo 0건 + fail-safe 분기 명시 + 5곳 의미 동기 + cursor frontmatter/코드블록 추출 무결
- **테스트**: TS-005, TS-006, TS-007, TS-008, TS-009, TS-010, TS-016
- **실행 방법**: sub-agent
- **의존**: 없음 (F-001과 병렬 가능 — 다른 파일군)

#### Step 3: 환경변수 접근·권한 정리 (S-6 reconcile)
- [x] 완료
- **소속 기능**: F-003 (+ F-004 변경이력 #12 — Step 1과 동일 install-mac.sh 헤더)
- **영역**: 배치
- **agent**: opal-be-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §3.3.2 — `perm_entries`에서 `'Bash(echo $OPAL_BOOTSTRAP)'` 제거(:395) + 직전 주석(:394) 정리. v3.5 변경이력 행은 보존, v3.6 행에 "echo 권한 제거" 통합 기록(Step 1과 동일 헤더 — 한 행에 install_opal_setting + perm 제거 합산 가능).
- **완료 기준**: TS-012, TS-015 통과 — perm_entries echo 0건 + `bash -n` 통과 + 전체 소스 echo 게이트 grep 0건(변경이력 과거 기록 제외)
- **테스트**: TS-012, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 1 (동일 `scripts/install-mac.sh` 파일 충돌 방지 — Step 1 완료 후 동일 에이전트가 이어서 처리 권장)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일군 (install+신규소스 vs AGENT.md+bootstrapper), 독립 기능 |
| Step 1 → Step 3 | **동일 파일** `scripts/install-mac.sh` 수정 → 파일 충돌 방지(plan-guide §6 C-1 1순위). 동일 에이전트(opal-be-agent) 순차 처리. Step 1(함수 추가)이 Step 3(perm 제거)보다 선행해도 무방하나 한 에이전트가 두 변경을 묶어 헤더 변경이력 1행으로 reconcile하는 것이 깔끔 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | setting.json 소스 유효성 | TS-001 | 유효 JSON + bootstrap 키 (값 on) |
| F-001 | create-if-absent 멱등 (존재 시 불변) | TS-002 | 기존 off 토글 보존 (H-1) |
| F-001 | create-if-absent 생성 (부재 시) | TS-003 | 유효 JSON 신규 생성 (H-2) |
| F-001 | install 구문 무결 + 호출부 | TS-004 | bash -n 통과 + install_opal_setting 호출 존재 |
| F-001 | Linux 자동 상속 | TS-013 | linux.sh exec 위임 구조 유지 |
| F-001 | Windows create-if-absent 블록 | TS-014 | Install-OpalCore에 Test-Path 가드 블록 존재 |
| F-002 | 코어 AGENT.md step 0 전환 | TS-005 | setting.json Read + echo 0 + fail-safe + WORKER 구분 |
| F-002 | claude 마커 전환 + 추출 무결 | TS-006 | 코드블록 게이트 + echo 0 + 코드 펜스 무추가 |
| F-002 | gemini 마커 전환 | TS-007 | 코드블록 게이트 + echo 0 |
| F-002 | codex 마커 전환 | TS-008 | 코드블록 게이트 + echo 0 |
| F-002 | cursor 마커 전환 + frontmatter 무손상 | TS-009 | 본문 게이트 + echo 0 + `---` 구조 유지 |
| F-002 | 5곳 게이트 의미 동기 | TS-010 | 조건/동작/fail-safe 일치 (H-4) |
| F-002 | 실세션 off/on/부재 동작 (통합) | TS-011 | off 무프롬프트 스킵 / on·부재 정상 (수동) |
| F-003 | perm echo 제거 + 구문 무결 | TS-012 | perm_entries echo 0 + bash -n (H-7) |
| F-003 | 소스 echo 게이트 잔존 0 | TS-015 | 전체 소스 grep 0건 (완료기준 ⑤) |
| F-004 | 변경이력 행 추가 | TS-016 | 수정 각 파일에 043 행 (cursor 제외) |

### 5.2 회귀 테스트
- [ ] setting.json `on`/필드제거/파일부재 세션에서 기존 7단계 부트스트랩 정상 동작 (TS-011, fail-safe)
- [ ] 기존 `[WORKER]` 스킵 메커니즘 불변 (디스패치 첫 줄 `[WORKER]`)
- [ ] install 멱등 — 2회 재실행 시 setting.json 내용 불변 + 마커 중복 누적 없음 (TS-002)
- [ ] Read 권한 2개(`Read(~/.opal/**)`, `Read({opal_home}/**)`) 유지 — 무프롬프트 보장 불변

### 5.3 코드/문서 품질
- [ ] 5곳 게이트 문구 의미 일치 (H-4)
- [ ] 변경이력 기록 (버전, KST 일시, 043) — AGENT.md + 3 bootstrapper + install-mac.sh + windows.ps1 (TS-016)
- [ ] 코드 펜스/특수문자로 인한 코드블록 추출 경계 파손 없음 (H-6)
- [ ] cursor frontmatter(`---`) 구조 무손상 (H-5)
- [ ] [MUST] 배포본 `~/.opal/` 직접편집 0 — 소스(`opal/`,`scripts/`)만 수정 (§1.5)

### 5.4 보안
- [ ] setting.json·게이트 문구에 하드코딩된 토큰/시크릿 없음 (해당 없음 — 설정/산문)
- [ ] 추가 권한 요구 없음 — 기존 Read 권한 재사용, 신 권한 표면 0 (§1.2)
- [ ] setting.json은 부트스트랩 토글만 보유 (민감정보 비저장)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 3개 | 단순 |
| 변경 파일 수 | 6개 (setting.default.json 신규 + install-mac.sh + windows.ps1 + AGENT.md + bootstrapper 3종; cursor 1; linux 검증) | 복잡 |
| 모듈 범위 | 다중 (install 어댑터 + 부트스트래퍼 마커 + 코어 AGENT.md) | 복잡 |
| 작업 유형 | 메커니즘 전환 + 신규 배포 함수 (동작 로직) | 복잡 |
| 외부 의존성 | 없음 (프레임워크 내부) | 단순 |
| **실행 모드** | **복잡** | 변경 파일 4개 초과 + 다중 모듈(install/bootstrapper/core) + create-if-absent 동작 로직(RED-first) → 복잡 모드. §7 실행 아키텍처 포함 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬):
  A1 = opal-be-agent  → Step 1 (setting.json 소스 + install create-if-absent: install-mac.sh + windows.ps1)
  A2 = opal-task-agent → Step 2 (게이트 문구 5곳 교체)

Batch 2 (A1 완료 후 — 동일 install-mac.sh):
  A1 = opal-be-agent  → Step 3 (perm echo 제거 + reconcile)
```

**그룹핑 근거**:
1. **파일 충돌 방지**: Step 1·Step 3 모두 `scripts/install-mac.sh` 수정 → 동일 에이전트(A1=opal-be-agent)에 배치, Batch 분리(순차).
2. **모듈 응집도**: Step 2는 문서/마커 계층(install 무관) → 독립 에이전트(A2)로 병렬.
3. **병렬 극대화**: Batch 1에서 A1(install/배치)·A2(마커/문서) 동시 실행.

### C-2. 스킬 요구사항

- 기존 스킬로 충분 — 신규 스킬 불요. install 함수 작성은 기존 `install_claude_permissions` 멱등 패턴 인라인 참조(`scripts/install-mac.sh:382-420`). 게이트 문구 교체는 040 PLAN 문구 패턴 계승. (갭 판별: 동일 패턴 3개 Step 미만 → 인라인 지침으로 충분.)

### C-3. 도구 요구사항

- CLI: `bash -n`(구문 검사), `grep`(잔존 검사), `python3 -c`(install 내 json — 단 setting.json 생성은 cp로 충분). MCP·패키지 설치 불요.

### C-4. 테스트 전략 (opal-test-agent / RED-first 연동)

- **RED-first 트랙 (BE 모드)**: TS-002(멱등)·TS-003(생성)는 install create-if-absent 동작 로직 → RED-first 적격(§RED-first 판단). opal-test-agent(mode: red)가 `install_opal_setting` 멱등/생성 검증 셸 테스트를 RED 작성(작성자≠구현자, red-first.md §2).
- **정적 검증 트랙**: TS-001,004~010,012~016은 산출물 grep/구조 검사(L1) — 결정론적. EXECUTE 후 검증.
- **통합(수동)**: TS-011은 캡틴 install 재배포 + 실세션(off/on/부재) — 환경 의존.
- **회귀**: §5.2 — install 2회 멱등, [WORKER] 불변, fail-safe.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 설정파일 | JSON (`setting.json`) | - |
| 설치 어댑터 | Bash (`install-mac.sh`), PowerShell (`windows.ps1`), Bash wrapper (`linux.sh`) | - |
| 부트스트래퍼 마커 | Markdown (코드블록/frontmatter) | - |
| 게이트 판정 | Read 도구 + JSON 필드 파싱 (LLM 산문 지시) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| - | 해당 없음 (프레임워크 내부 설정/셸/마크다운 — 외부 라이브러리 미사용) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 태스크 정의 | `tasks/043-260624-opds-부트스트랩-게이트-설정파일-전환/TASK.md` | 확정 설계방향·요구사항·규명사항 SSOT |
| D-2 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 배포 경계·플랫폼 분기·Guards·변경이력 [MUST] 규칙 |
| D-3 | 소스 | OPAL AGENT.md (코어) | `opal/core/AGENT.md` | Eager step 0 게이트 SSOT (S-1, :13), strip 경계 (:452 변경이력) |
| D-4 | 소스 | 부트스트래퍼 4종 | `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md`, `cursor-bootstrap.mdc` | 게이트 마커 SSOT (S-2~S-5, 각 :17 / cursor :8) |
| D-5 | 소스 | macOS install | `scripts/install-mac.sh` | perm 멱등 패턴(:382-420), 코어 배포(:964-969), 마커 추출/삽입(:1111-1133), strip(:222-225), perm echo(:35,:394-395) |
| D-6 | 소스 | Windows install 미러 | `scripts/install/windows.ps1` | Install-OpalCore 보존 패턴 (setting.json create-if-absent 미러) |
| D-7 | 소스 | Linux install wrapper | `scripts/install/linux.sh` | exec 위임 구조 — setting.json 배포 자동 상속 (:39) |
| D-8 | 기획 | 040 원 설계 | `tasks/040-260624-opds-부트스트랩-스킵/PLAN.md` | 전환 대상 게이트 원 설계 (Bash echo 메커니즘·fail-safe 계승) |
| D-9 | 설계 | RED-first 트랙 SSOT | `opal/core/references/harness/red-first.md` | install 동작 로직 RED-first 적용 판단 |
| D-10 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 산출물 근거 인용 [MUST] |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | create-if-absent가 기존 setting.json 덮어써 사용자 토글 유실 (H-1) | F-001 | P0 | `[[ -f "$dst" ]]` early-return 멱등 가드; TS-002 RED-first |
| R-2 | 부재 시 유효 JSON 생성 실패 (H-2) | F-001 | P1 | cp로 검증된 소스 그대로 복사; TS-003 RED-first. fail-safe로 미생성도 정상 부트스트랩 |
| R-3 | LLM이 `off` 조건 과확대 → 부재/필드없음/on 세션도 스킵 (H-3) | F-002 | P0 | "정확히 off" + fail-safe 분기(파일/필드 부재·파싱실패 명시); TS-010 동기 검사 |
| R-4 | 5곳 게이트 의미 불일치 (H-4) | F-002 | P1 | 5곳 동일 조건·동작·fail-safe 표현; TS-010 교차 검사 |
| R-5 | cursor `.mdc` frontmatter 파손 (H-5) | F-002 | P0 | `---` 바깥 본문에만 교체; TS-009 구조 검사 |
| R-6 | 코드 펜스로 코드블록 추출 조기 종료 (H-6) | F-002 | P0 | 코드 펜스 금지, 인라인 백틱만; TS-006 추출 무결 |
| R-7 | perm 제거 후 install python json 구문 파손 (H-7) | F-003 | P1 | `bash -n` 통과 검증; TS-012 |
| R-8 | 프로젝트 오버라이드 우선순위 부재로 혼선 (H-8) | F-001 | P2 | 범위 외 명시(결정 D-3) — 글로벌 단일, 게이트 문구 단일 경로. 후속 태스크 |
| R-9 | Windows 미러 미반영 시 Windows 토글 불가 | F-001 | P2 | windows.ps1 create-if-absent 블록 포함(결정 D-2). 미반영도 fail-safe 정상동작(파일 부재=정상 진행) |

---

## RED-first 트랙 판단

> TASK §RED-first 판단 지시 응답. SSOT: `opal/core/references/harness/red-first.md`.

- **F-001 install create-if-absent 함수 = RED-first 적격**: 멱등 생성(존재 시 불변 / 부재 시 생성)이라는 **동작 계약**을 가진 로직이다. red-first.md §1.5 "비즈니스 로직 / 버그 수정(회귀 방지)" 범주에 준하는 동작 로직 — self-confirming 위험이 있으므로 RED-first 강제 트랙을 적용한다.
  - RED 작성: opal-test-agent(mode: red)가 TS-002(멱등)·TS-003(생성) 셸 테스트를 실패(exit≠0) 상태로 선작성(작성자≠구현자, red-first.md §2).
  - GREEN: opal-be-agent가 `install_opal_setting` 구현으로 통과.
  - state-tool 연동: `verify --red-check` ON (red-first.md §1.5).
- **F-002 게이트 문구 교체(S-1~S-5) = 정적 검증 트랙**: 마크다운 산문/설정 문구 교체 — red-first.md §1.5 "설정·문서" 범주. 실행 가능한 단위 테스트 대상 함수 없음. L1 산출물 grep/구조 검사(TS-005~010)로 검증. RED-first 비적용.
- **F-003 perm 정리 = 정적 검증 트랙**: 리스트 1항목 제거 — 구문 검사(`bash -n`)·grep(TS-012,015). RED-first 비적용.
- **공통 불변(red-first.md §1.5)**: 어느 트랙이든 ①테스트 시나리오 산출물(TEST-SCENARIO.md) ②작성자≠구현자 ③TEST 단계 검증 유지.
- **인프라 부재 graceful skip(red-first.md §5)**: 프레임워크는 셸 테스트 하네스가 경량(직접 bash 실행)이므로 RED 셸 테스트 작성 가능 — 우회 금지. 통합 TS-011은 환경 의존으로 수동(state-tool RED 게이트는 해당 산출물 부재 시 skip).

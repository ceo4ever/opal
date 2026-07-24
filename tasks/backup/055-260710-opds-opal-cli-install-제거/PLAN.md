# PLAN: opal-cli install 서브커맨드 완전 제거

> 작성일: 2026-07-10 | 입력: TASK.md (ANALYSIS.md 없음 — 직접 코드 분석 수행)
> 모드: Multi-Feature (F-001·F-002·F-003)
> 실행 에이전트: opal-task-agent (Framework 요소 opal/tools) · 문서 영역은 PM 직접

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-cli install` 서브커맨드를 디스패처에서 **완전 제거**하고(리다이렉트 스텁 없음), `lib/install.sh`를 삭제한다. `install`을 전제하던 연쇄 안내 문구(doctor/update/console)와 unknown 메시지를 이식 가능한 경로(신규=원라이너 / 갱신=`opal-cli update`)로 리다이렉트하고, 문서(README·ARCHITECTURE)를 정합화한다. `opal-cli install` 입력은 dispatch의 `*)` unknown 분기로 흡수되어 표준 usage를 출력한다(설치 시도 없음).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | install 디스패치·헬프·헤더·unknown·lib 완전 제거 | R-1, R-2, R-4 | P0 | 없음 |
| F-002 | 연쇄 안내 리다이렉트 (doctor/update/console) | R-3 | P0 | 없음 |
| F-003 | 문서 정합 (README·ARCHITECTURE) | R-5 | P1 | F-001, F-002 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┐
       ├─→ F-003 (문서 반영)
F-002 ─┘
(F-001·F-002는 상호 독립 — 서로 다른 파일/영역, 병렬 가능)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `run.sh` dispatch case 라인 114에서 `install\|` 제거 | dispatch 문자열 편집 실수로 `update\|doctor\|...` 파이프 손상 → 정상 서브커맨드가 unknown으로 falls-through (회귀) | P0 | L1(소스 직접 실행) | S-3, S-4 |
| H-2 | `lib/install.sh` 파일 삭제 | run.sh가 `install`을 여전히 dispatch하면 `source` 실패로 "lib/install.sh 없음" 오류 (파일-디스패치 정합 계약) | P0 | L1(`opal-cli install` 실행 관찰) | S-2 |
| H-3 | `update.sh:147` 리다이렉트 문구 | 문구를 `opal-cli update`로 교체하면 **순환 안내**(이미 update 안에서 미설치 감지 — update 재실행 무의미). 반드시 원라이너(신규 설치)여야 함 | P1 | L1(문자열 검증) | S-6 |
| H-4 | `run.sh:106` --version fallback 문구 | VERSION 부재 = 미설치/불완전 상태. 갱신(update)이 아니라 신규(원라이너)를 가리켜야 정합 | P2 | L1(OPAL_HOME override 실행) | S-5 |
| H-5 | `console.sh`·`doctor.sh` 리다이렉트 | ~/.opal은 존재하나 컴포넌트(uvicorn/dashboard/doctor) 누락 상황 → 신규 설치가 아니라 `opal-cli update`(재배포)가 정답. 원라이너로 잘못 안내 시 사용자 혼란 | P2 | L1(문자열 검증 + OPAL_HOME override) | S-7 |
| H-6 | 전 파일 `grep "opal-cli install"` = 0 (변경이력 제외) | 잔존 문자열이 있으면 안내 UX 함정 잔류 (R-3 AC 미달) | P1 | L1(grep 전수) | S-8 |
| H-7 | README/ARCHITECTURE 편집 | 현행 서브커맨드 목록에 install 잔존 시 문서-코드 불일치 (사용자 오도) | P2 | L1(grep) | S-9, S-10 |

> **가설 도출 근거**: H-1·H-2는 dispatch 문자열/파일 정합의 파괴적 회귀(P0). H-3는 순환 안내라는 논리 결함(대체 명령 선택 정당성의 핵심). H-5는 "미설치 vs 컴포넌트 누락"의 컨텍스트 구분 실패. 모든 계층이 L1(소스 직접 실행/grep)으로 검증 가능 — 재배포 불필요.

---

## 2. 기능별 분석

### F-001: install 디스패치·헬프·헤더·unknown·lib 완전 제거

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트/도구 | `opal/tools/opal-cli/run.sh` | 진입점 디스패처 (case/help/header/version-fallback) | 수정 |
| 에이전트/도구 | `opal/tools/opal-cli/lib/install.sh` | install 서브커맨드 로직 | 삭제 |

#### 2.1.2 현재 구현 (직접 분석)

- **dispatch 메커니즘** (`run.sh:95~124`): `case "$subcommand"`에서 `install|update|doctor|uninstall|mcp|console)` 한 분기가 **동적 로딩** 방식으로 처리 — `source "$LIB_DIR/${subcommand}.sh"` 후 `"cmd_${subcommand}" "$@"` 호출 (`run.sh:114~123`). 즉 install.sh는 **정적 source가 아니라 이 case 분기에서만 동적으로 로드**된다. → case에서 `install`을 빼면 install.sh는 어디에서도 로드되지 않으므로 파일 삭제가 안전 (grep 확인: `cmd_install`은 install.sh에만 존재, `lib/install.sh` 정적 참조 0건 — `update.sh`의 `install.sh` 언급은 모두 `scripts/install.sh`(원라이너) 정합 주석이라 무관).
- **unknown 처리** (`run.sh:131~136` `*)` 분기): 알 수 없는 서브커맨드 입력 시 `error "알 수 없는 서브커맨드: $subcommand"` + `usage()` + `exit 1`. → `install` 제거 후 `opal-cli install` 입력은 이 분기로 흡수됨 (설치 시도 없음, R-1 AC 충족).
- **help** (`run.sh:53~91` `usage()` heredoc): 라인 63 서브커맨드 목록에 install 행, 라인 75 예시에 `opal-cli install`.
- **header 주석**: 라인 10 `# Subcommands: install | update | ...` (현행 목록), 라인 12~17 변경이력.
- **--version fallback** (`run.sh:99~108`): `~/.opal/VERSION` 부재 시 `echo "opal-cli (unknown — run install or update first)"` (라인 106).

#### 2.1.3 영향 범위

- **상위 의존**: `~/.opal/bin/opal-cli` symlink → `~/.opal/tools/opal-cli/run.sh` (배포본). 소스 수정 후 재배포(CLOSE 후 캡틴 지시)가 최종 반영. **검증은 소스 `run.sh` 직접 실행으로 수행** (§TEST 전략).
- **하위 의존**: install.sh는 case 분기에서만 로드 → 삭제해도 다른 코드 무영향.
- **회귀 위험**: dispatch case 문자열 편집 시 나머지 파이프(`update|doctor|uninstall|mcp|console`) 보존 필수 (H-1).

### F-002: 연쇄 안내 리다이렉트 (doctor/update/console)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트/도구 | `opal/tools/opal-cli/lib/doctor.sh` | doctor 위임 (도구 누락 시 안내) | 수정 |
| 에이전트/도구 | `opal/tools/opal-cli/lib/update.sh` | update (미설치 감지 시 안내) | 수정 |
| 에이전트/도구 | `opal/tools/opal-cli/lib/console.sh` | console (컴포넌트 누락·전제 안내) | 수정 |

#### 2.2.2 현재 구현 (직접 분석)

install을 전제한 안내 문구 5곳 (컨텍스트 구분이 핵심):

| 위치 | 컨텍스트 | 현재 상태 조건 |
|------|---------|--------------|
| `update.sh:146~148` | ~/.opal **부재**(미설치) — `cmd_update`가 `[[ ! -d "$opal_home" ]]`에서 error 후 안내 | `~/.opal` 자체가 없음 |
| `doctor.sh:49~53` | ~/.opal **존재**하나 `tools/doctor/run.sh` 누락 (배포 불완전) | 배포본 손상/구버전 |
| `console.sh:45~49` | ~/.opal 존재하나 `.venv/bin/uvicorn` 누락 | 배포 불완전 |
| `console.sh:51~55` | ~/.opal 존재하나 `dashboard-server/dashboard/backend` 누락 | 배포 불완전 |
| `console.sh:123` | console help의 전제 안내 (일반 안내) | - |

#### 2.2.3 영향 범위

- 순수 사용자 안내 문자열 교체 — 제어 흐름/반환값 무변경. 회귀 위험 최소.
- **논리 정당성 계약**(H-3): `update.sh:147`은 "update 실행 중 미설치 감지" 상황 → 여기서 `opal-cli update`를 권하면 순환. `cmd_update`는 `~/.opal` 부재 시 진행 불가(`update.sh:145~148`)이므로 반드시 **신규 설치 원라이너**를 안내해야 한다.

### F-003: 문서 정합 (README·ARCHITECTURE)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/tools/opal-cli/README.md` | opal-cli 도구 문서 (도구 로컬) | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | 시스템 아키텍처 (배포 채널·CLI 서술) | 수정 |

#### 2.3.2 현재 구현 (직접 분석)

- **README.md** install 언급 (PM 분석 대비 **추가 발견 2곳 포함**):
  - 라인 4: 인트로 "설치, 업데이트, 진단, 제거, MCP 관리를 서브커맨드로 제공한다" — "설치" 포함
  - 라인 26: 서브커맨드 표 `| install | OPAL 설치 또는 재설치 |` 행
  - 라인 45~47: 사용 예시 `# 설치 (레포 클론 후)` + `opal-cli install`
  - **라인 149**: 파일 구조 트리 `│   ├── install.sh      install 서브커맨드` (PM 분석 미포함 — 추가)
  - 라인 163: 변경이력 "5개 서브커맨드 (install/update/doctor/uninstall/mcp)" (**역사 기록 — 보존**, 신규 행 추가)
- **ARCHITECTURE.md** install 언급:
  - 라인 309: 배포 채널 표 `opal-cli` 행 — `` `install`/`update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 `` → **현행 서브커맨드 목록**이므로 `install` 제거 대상
  - 그 외 라인 60·72·199·209 등 `install`/`install-mac.sh` 언급은 **원라이너·install-mac.sh 배포 프로세스** 서술로 `opal-cli install`과 무관 → 변경 제외

#### 2.3.3 영향 범위

- 문서 정합만 — 코드 무영향. 변경이력 행 추가 의무 (CONVENTIONS §변경이력 작성 의무).

---

## 3. 기능별 설계

### F-001: install 디스패치·헬프·헤더·unknown·lib 완전 제거

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/run.sh` | 도구 | dispatch case `install\|` 제거(라인 114) / usage() install 행·예시 제거(63·75) / 헤더 라인 10 서브커맨드 목록 install 제거 / --version fallback 문구(106) install 제거 / 변경이력 신규 행 추가 | `run.sh:114`, `run.sh:63`, `run.sh:75`, `run.sh:10`, `run.sh:106` |

**삭제**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `opal/tools/opal-cli/lib/install.sh` | 도구 | 파일 전체 삭제 | `lib/install.sh` (D-2), case 외 정적 참조 0건 |

#### 3.1.2 API·데이터 모델·변경 상세 설계

- **dispatch case (R-1, H-1)**: `run.sh:114`
  ```
  install|update|doctor|uninstall|mcp|console)   →   update|doctor|uninstall|mcp|console)
  ```
  동적 로딩 로직(`source "$LIB_DIR/${subcommand}.sh"` + `"cmd_${subcommand}"`)은 그대로 유지 — install만 목록에서 제거. 나머지 파이프는 그대로. (`run.sh:114~123`)
- **unknown 흡수 (R-1 AC)**: 별도 코드 불필요. `opal-cli install` → `*)` 분기(`run.sh:131~136`) → `error "알 수 없는 서브커맨드: install"` + `usage()` + `exit 1`. **설치 시도 없음** 보장.
- **usage() (R-1)**: `run.sh:63` `  install               OPAL 설치 (one-liner 외 수동 진입점)` 행 삭제. `run.sh:75` `  opal-cli install` 예시 삭제.
- **헤더 주석 (R-1)**: `run.sh:10` → `# Subcommands: update | doctor | uninstall | mcp | console`. **라인 12~17 변경이력은 역사 기록으로 보존**(v1.0이 install을 포함했던 것은 사실) — 대신 신규 변경이력 행 추가:
  ```
  #   v1.2 2026-07-10 install 서브커맨드 완전 제거 — dispatch/help/header/unknown 정리 + lib/install.sh 삭제 (055)
  ```
  [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "변경하면 변경이력 표/헤더 라인에 행을 추가한다. 일시 KST, 버전 semver, 변경내용은 태스크 번호를 괄호로 포함".
- **--version fallback (R-4, H-4)**: `run.sh:106`
  ```
  echo "opal-cli (unknown — run install or update first)"
  →
  echo "opal-cli (미설치 — 원라이너로 설치하세요: curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash)"
  ```
  근거: VERSION 부재 = 미설치/불완전 → 신규 설치 원라이너가 정답 (D-A 리다이렉트 표준, §3.2.2).

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음. (파일 삭제는 EXECUTE에서 `git rm` 또는 `rm`)

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (help) | 산출물 검사 | `bash run.sh --help` 출력에 `install` 미노출 |
| TS-002 | R-1 AC (install 실행) | 기능 테스트 | `bash run.sh install` → "알 수 없는 서브커맨드: install" + usage + exit 1 (설치 시도 없음) |
| TS-003 | R-2 AC | 산출물 검사 | `lib/install.sh` 파일 부재 + run.sh에 install.sh/cmd_install 참조 0건 |
| TS-004 | R-4 AC | 산출물 검사 | `run.sh:106` fallback 문구에 `install` 없음 |

### F-002: 연쇄 안내 리다이렉트 (doctor/update/console)

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 3 | `opal/tools/opal-cli/lib/update.sh` | 도구 | 라인 147 "먼저 opal-cli install 실행" → 신규 설치 원라이너 안내 | `update.sh:147`, D-A |
| 4 | `opal/tools/opal-cli/lib/doctor.sh` | 도구 | 라인 51~52 재설치 안내 "opal-cli install" → `opal-cli update` | `doctor.sh:52`, D-A |
| 5 | `opal/tools/opal-cli/lib/console.sh` | 도구 | 라인 47·53 "opal-cli install 먼저 실행" → `opal-cli update`, 라인 123 전제 안내 → `opal-cli update` | `console.sh:47`, `console.sh:53`, `console.sh:123`, D-A |

#### 3.2.2 리다이렉트 표준안 (D-A) — 컨텍스트별 대체 명령

> **[결정]** 대체 명령은 **상태 컨텍스트**로 분기한다 (H-3·H-5). 원라이너는 mac/linux·Windows 2종을 모두 제시하되, 배포본 손상 케이스는 `opal-cli update` 단일로 통일한다.

| 컨텍스트 | 조건 | 대체 명령 | 근거 |
|---------|------|----------|------|
| **미설치** (~/.opal 부재) | `update.sh:145~148` | 신규 설치 원라이너 | `opal-cli update`는 ~/.opal 존재 전제(`update.sh:145`) → 순환 회피(H-3) |
| **배포본 손상/컴포넌트 누락** (~/.opal 존재) | `doctor.sh:49`, `console.sh:45·51`, `console.sh:123` | `opal-cli update` | update가 tarball 재fetch로 재배포 + 사용자 데이터 보존 (`update.sh` 로직) — 신규 설치 불필요(H-5) |

**표준 문자열 (EXECUTE 반영용)**:

- 원라이너 (미설치용, `update.sh:147` 대체):
  ```bash
  info "신규 설치: curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash"
  info "  (Windows PowerShell) iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)"
  ```
  (원라이너 실경로 확인: `scripts/install.sh:10`, `scripts/install.ps1:11`)
- `opal-cli update` (배포본 손상용):
  - `doctor.sh:51~52`:
    ```
    info "OPAL을 재설치하면 doctor 도구가 포함됩니다:"
    info "  opal-cli install"
    →
    info "OPAL을 최신 배포본으로 갱신하면 doctor 도구가 포함됩니다:"
    info "  opal-cli update"
    ```
  - `console.sh:47`·`console.sh:53`: `error "opal-cli install 을 먼저 실행하세요."` → `error "opal-cli update 로 최신 배포본을 재배포하세요."`
  - `console.sh:123`: `전제: opal-cli install 실행 후 사용 가능합니다.` → `전제: opal-cli update 로 대시보드 배포본(dashboard-server·venv) 반영 후 사용 가능합니다.`

> [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "행위는 플랫폼 독립적으로 기술". 원라이너 안내는 mac/linux·Windows 2줄 병기로 플랫폼 독립성을 유지하되 조건 분기 코드는 추가하지 않는다(단순 안내 문자열).

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-3 AC (grep 0건) | 산출물 검사 | `grep -rn "opal-cli install" opal/tools/opal-cli/` = 0건 (변경이력 행 제외) |
| TS-006 | R-3 AC (유효 명령) | 산출물 검사 | update.sh는 원라이너, doctor/console은 `opal-cli update` 안내 존재 |
| TS-007 | R-3 (동작) | 기능 테스트 | `OPAL_HOME=/tmp/nx bash run.sh update` → 원라이너 안내 출력 (순환 없음) |

### F-003: 문서 정합 (README·ARCHITECTURE)

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 6 | `opal/tools/opal-cli/README.md` | 문서 | 인트로(4)·서브커맨드 표(26)·예시(45~47)·파일 트리(149) install 제거 + 변경이력 신규 행 | `README.md:4·26·47·149·163` |
| 7 | `docs/ARCHITECTURE.md` | 문서 | 라인 309 opal-cli 서브커맨드 목록에서 `install` 제거 + 변경이력 신규 행 | `ARCHITECTURE.md:309` |

#### 3.3.2 변경 상세 설계

- **README.md**:
  - 라인 4: `설치, 업데이트, 진단, 제거, MCP 관리를...` → `업데이트, 진단, 제거, MCP 관리를...`
  - 라인 26: `| install | OPAL 설치 또는 재설치 |` 행 삭제
  - 라인 45~47: `# 설치 (레포 클론 후)` 주석 + `opal-cli install` 예시 삭제 (신규 설치는 원라이너이므로 예시에서 제외; 필요 시 원라이너 주석으로 대체 가능하나 TASK 범위는 "install 제거"이므로 삭제만 수행)
  - 라인 149: `│   ├── install.sh      install 서브커맨드` 트리 행 삭제
  - 라인 163 변경이력 표: **역사 행 보존** + 신규 행 추가:
    ```
    | v1.1 | 2026-07-10 10:00 | install 서브커맨드 제거 — dispatch/help/문서 정리 + lib/install.sh 삭제 (055) |
    ```
  - [MUST] `docs/CONVENTIONS.md` §변경이력: 일시 `YYYY-MM-DD HH:mm` KST, 버전 semver, 태스크번호 `(055)` 포함.
- **ARCHITECTURE.md**:
  - 라인 309: `` `install`/`update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 `` → `` `update`/`doctor`/`uninstall`/`mcp`/`console` 단일 진입점 `` (라인 60·72·199·209 등 install-mac.sh/원라이너 서술은 **변경 제외** — `opal-cli install`과 무관)
  - 변경이력 표(라인 381~) 신규 행 추가:
    ```
    | 2026-07-10 | 배포 채널 표의 opal-cli 서브커맨드 목록에서 install 제거 — opal-cli install 서브커맨드 완전 제거에 정합 (Task 055) |
    ```

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-5 AC (README) | 산출물 검사 | `opal-cli/README.md`에 `install` 미노출 (변경이력 행 제외) |
| TS-009 | R-5 AC (ARCHITECTURE) | 산출물 검사 | ARCHITECTURE 라인 309 서브커맨드 목록에 `install` 없음 |
| TS-010 | R-5 AC (변경이력) | 산출물 검사 | README·ARCHITECTURE에 055 변경이력 행 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2 | opal-task-agent | 순차 | 동일 파일(run.sh) 후 install.sh 삭제 |
| 1 | F-002 | 3 | opal-task-agent | 병렬(F-001과) | 서로 다른 lib 파일 |
| 2 | F-003 | 4, 5 | opal-task-agent / PM 직접 | 순차 | 코드 확정 후 문서 반영 |

> **파일 충돌 방지**: 전 Step이 동일 tool 디렉토리를 편집하나 파일이 서로 겹치지 않음(run.sh / install.sh / doctor·update·console.sh / README / ARCHITECTURE). 단일 agent(opal-task-agent) 순차 처리를 권장하여 충돌 원천 차단.

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 2개 | 실행 모드: 복잡 (변경 파일 7개 ≥ 4 — §6 판별)

#### Step 1: run.sh install 디스패치·헬프·헤더·unknown 제거
- [x] 완료
- **소속 기능**: F-001
- **영역**: 에이전트/도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/run.sh`
- **작업 내용**: (1) dispatch case 라인 114 `install|update|doctor|uninstall|mcp|console)` → `update|doctor|uninstall|mcp|console)` (동적 로딩 로직 유지). (2) usage() 라인 63 install 행 삭제, 라인 75 `opal-cli install` 예시 삭제. (3) 헤더 라인 10 서브커맨드 목록 install 제거. (4) --version fallback 라인 106 문구 → 원라이너 안내(§3.1.2). (5) 헤더 변경이력에 v1.2 (055) 행 추가.
- **완료 기준**: `bash opal/tools/opal-cli/run.sh --help`에 install 미노출 / `bash ... install` → unknown+usage+exit1 / dispatch 나머지 파이프 보존
- **테스트**: TS-001, TS-002, TS-004
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: lib/install.sh 삭제
- [x] 완료
- **소속 기능**: F-001
- **영역**: 에이전트/도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/install.sh`
- **작업 내용**: 파일 삭제(`git rm`). Step 1로 dispatch에서 install 제거 완료된 상태 전제 — install.sh는 case 분기에서만 동적 로드되므로 삭제 안전.
- **완료 기준**: `lib/install.sh` 부재 + `grep -rn "cmd_install\|lib/install.sh" opal/tools/opal-cli/` 0건(update.sh의 `scripts/install.sh` 정합 주석 제외)
- **테스트**: TS-003
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: lib 연쇄 안내 리다이렉트 (doctor/update/console)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 에이전트/도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/doctor.sh`, `opal/tools/opal-cli/lib/update.sh`, `opal/tools/opal-cli/lib/console.sh`
- **작업 내용**: §3.2.2 표준안대로 — update.sh:147 → 원라이너(미설치) / doctor.sh:51~52 → `opal-cli update` / console.sh:47·53·123 → `opal-cli update`. 각 파일 변경이력 있으면 헤더 변경이력 행 추가.
- **완료 기준**: `grep -rn "opal-cli install" opal/tools/opal-cli/` 0건(변경이력 제외) / 각 안내가 유효 명령을 가리킴 / 컨텍스트별 대체 명령 정합(미설치=원라이너, 손상=update)
- **테스트**: TS-005, TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 가능)

#### Step 4: opal-cli README 정합
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent (도구 로컬 문서 — opal/tools 번들)
- **파일**: `opal/tools/opal-cli/README.md`
- **작업 내용**: §3.3.2 — 인트로(4)/서브커맨드 표(26)/예시(45~47)/파일 트리(149) install 제거 + 변경이력 v1.1 (055) 행 추가.
- **완료 기준**: README에 install 미노출(변경이력 제외) + 055 변경이력 행 존재
- **테스트**: TS-008, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3 (코드 확정 후 문서 반영)

#### Step 5: docs/ARCHITECTURE.md 정합 (docs/ 갱신)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: PM 직접 (docs/ 갱신 Step)
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 라인 309 opal-cli 서브커맨드 목록에서 `install` 제거(라인 60·72·199·209 등 install-mac.sh/원라이너 서술은 변경 제외). 변경이력 표에 055 행 추가.
- **완료 기준**: 라인 309 목록에 install 없음 + 055 변경이력 행 존재
- **테스트**: TS-009, TS-010
- **실행 방법**: direct (PM)
- **의존**: Step 1, Step 2, Step 3

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | Step 1이 dispatch에서 install 제거 → install.sh가 로드되지 않는 상태 보장 후 삭제 (안전 순서) |
| Step 1 ∥ Step 3 | 서로 다른 파일(run.sh vs doctor/update/console.sh), 독립 변경 |
| Step 4·5 → after 1·2·3 | 문서는 코드 최종 상태 반영 |
| Step 4 ∥ Step 5 | 독립 문서 파일 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | help에 install 미노출 | TS-001 | `bash run.sh --help \| grep -c install` = 0 |
| F-001 | install 입력 unknown 처리 | TS-002 | 종료코드 1 + "알 수 없는 서브커맨드" + 설치 시도 없음 |
| F-001 | install.sh 삭제·참조 0 | TS-003 | 파일 부재 + cmd_install/lib 참조 0건 |
| F-001 | version fallback 정합 | TS-004 | 문구에 install 없음 |
| F-002 | install 안내 전수 제거 | TS-005 | grep 0건(변경이력 제외) |
| F-002 | 대체 명령 컨텍스트 정합 | TS-006, TS-007 | 미설치=원라이너, 손상=update / update 순환 없음 |
| F-003 | README install 제거 | TS-008 | README grep 0건(변경이력 제외) |
| F-003 | ARCHITECTURE 목록 정합 | TS-009 | 라인 309 install 없음 |
| F-003 | 변경이력 행 존재 | TS-010 | README·ARCHITECTURE 055 행 |

### 5.2 회귀 테스트
- [ ] `bash run.sh --help` 정상 출력 (update/doctor/uninstall/mcp/console 모두 노출)
- [ ] `bash run.sh doctor --help` / `mcp` / `console --help` / `update --help` 정상 (dispatch 파이프 무손상)
- [ ] `bash run.sh --version` 정상 (VERSION 존재 시 버전 출력)
- [ ] `bash run.sh` (인자 없음) → "서브커맨드를 입력하세요" + usage

### 5.3 코드/문서 품질
- [ ] 변경 파일 전부 변경이력 행 추가 (run.sh 헤더, README 표, ARCHITECTURE 표) — CONVENTIONS §변경이력 작성 의무
- [ ] `~/.opal/` 직접 편집 없음, `opal/` 소스만 수정 — CONVENTIONS §배포 경계
- [ ] shellcheck 무경고 (bash 파일 편집 시)
- [ ] 원라이너 안내 문자열이 실경로(`scripts/install.sh`, `scripts/install.ps1`)와 일치

### 5.4 보안
- [ ] 안내 문구 URL이 정규 레포(`raw.githubusercontent.com/ceo4ever/opal`)만 가리킴 (오타/타 도메인 없음)
- [ ] 하드코딩 토큰/시크릿 없음 (안내 문자열만 추가)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 7개 (run.sh, install.sh 삭제, doctor/update/console.sh, README, ARCHITECTURE) | 복잡 |
| 모듈 범위 | opal-cli 도구 + docs (단일 도구 + 문서) | 단순~경계 |
| 작업 유형 | 제거/문구 리다이렉트 | 단순 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **복잡** (변경 파일 7개 ≥ 4 — "하나라도 복잡 기준" 규칙) | |

> 실제 토폴로지는 단일 agent(opal-task-agent) 순차 처리로 자명 — §7은 최소 구성으로 기재.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **단일 에이전트**: opal-task-agent 1개가 Step 1~4 순차 처리 (파일 충돌 원천 차단). Step 5(ARCHITECTURE)는 PM 직접.
- **Batch 1**: Step 1 → Step 2 (순차, run.sh→install.sh 삭제) + Step 3 (병렬 가능하나 동일 agent 순차 권장)
- **Batch 2**: Step 4 (README), Step 5 (ARCHITECTURE, PM)
- DAG: `(1→2), 3 ⟶ 4, 5`

### C-2. 스킬 요구사항
- 신규 스킬 불요. EXECUTE는 op-dev-execute 표준 프로세스 + 텍스트 편집(Edit/Write/git rm)으로 충분. 동일 패턴 3개 미만 → 인라인 지침(§3.1.2·§3.2.2)으로 커버.

### C-3. 도구 요구사항
- 표준 Edit / Bash(git rm) / grep. 외부 CLI·MCP·패키지 불요.

### C-4. 테스트 전략 (opal-test-agent, mode=BE/CLI)
- **검증 대상은 소스 배포본이 아닌 소스 파일 직접 실행**(비파괴). `~/.opal` 재배포는 CLOSE 후 캡틴 지시 영역.
- **핵심 원리**: `run.sh`는 `SCRIPT_DIR/lib` (BASH_SOURCE 기준 상대)에서 lib를 로드(`run.sh:27~34`). 소스 경로 `opal/tools/opal-cli/run.sh`를 직접 실행하면 LIB_DIR = 소스 `opal/tools/opal-cli/lib` → **소스 변경이 그대로 검증**된다. 재배포 불필요.
- 상태 의존 분기는 `OPAL_HOME` 환경변수 override로 재현 (`run.sh`/lib 모두 `${OPAL_HOME:-$HOME/.opal}` 사용).
- 상세: TEST-SCENARIO.md.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| CLI 디스패처 | Bash (run.sh + lib/*.sh) | - (프레임워크 내장 컨벤션) |
| 문서 | Markdown (README, ARCHITECTURE) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 내장 Bash 도구 태스크 — 외부 라이브러리 문서 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-cli run.sh | `opal/tools/opal-cli/run.sh` | dispatch 메커니즘·help·헤더·version fallback (R-1/R-4) |
| D-2 | 소스 | lib/install.sh | `opal/tools/opal-cli/lib/install.sh` | 삭제 대상·cmd_install 유일 정의 확인 (R-2) |
| D-3 | 소스 | lib/{doctor,update,console}.sh | `opal/tools/opal-cli/lib/` | 안내 리다이렉트 컨텍스트 분석 (R-3) |
| D-4 | 소스 | 원라이너 스크립트 | `scripts/install.sh:10`, `scripts/install.ps1:11` | 안내 문구 실경로 반영 (R-3/R-4) |
| D-5 | 설계 | opal-cli README | `opal/tools/opal-cli/README.md` | install 언급 5곳 (R-5) |
| D-6 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md:309` | 배포 채널 CLI 서브커맨드 목록 정합 (R-5) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` §변경이력·§배포 경계·§플랫폼 분기 | 변경이력·배포 경계·안내 플랫폼 독립성 제약 |

> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`...)에서 수행한다." — 전 Step 대상은 `opal/` 소스.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | dispatch case 편집 실수로 정상 서브커맨드 falls-through | F-001 | P0 | Step 1 완료 기준에 "나머지 파이프 보존" 명시 + 회귀 테스트(§5.2)로 update/doctor/mcp/console/help 전수 검증 |
| H-2 | install.sh 삭제 후에도 dispatch가 install 로드 시도 → source 실패 | F-001 | P0 | Step 1(dispatch 제거) → Step 2(파일 삭제) 순서 강제 (§4.3) |
| H-3 | update.sh 리다이렉트를 update로 잘못 안내 → 순환 | F-002 | P1 | D-A 표준: 미설치=원라이너 강제, 근거 `update.sh:145` 존재 전제 |
| H-4 | version fallback을 update로 안내 (미설치인데) | F-001 | P2 | D-A: VERSION 부재=미설치 → 원라이너 |
| H-5 | 배포본 손상 케이스를 원라이너로 안내 (재설치 불필요) | F-002 | P2 | D-A: ~/.opal 존재 시 update 권고 |
| H-6 | install 문자열 잔존 (grep 누락) | F-002 | P1 | TS-005 전수 grep = 0건 (변경이력 제외) |
| H-7 | README 파일 트리(149)·인트로(4) 등 PM 미식별 지점 누락 | F-003 | P2 | §2.3.2에서 5곳 전수 식별(라인 4·26·47·149·163) — Step 4 완료 기준 grep |

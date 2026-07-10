# PLAN: opal-cli console scan — console.config.json 자동 생성·머지 업데이트

> 작성일: 2026-07-10 | 입력: TASK.md (ANALYSIS.md 없음 — Short Task, PLAN 워커 직접 코드 분석)
> 모드: Multi-Feature
> 적용 스킬: op-dev-plan v2.6 / plan-guide v2.0

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`opal-cli console scan [기준경로...]` 서브명령을 신설하여 OPAL Console 대시보드가 읽는 런타임 설정 `~/.opal/console.config.json`을 없으면 생성, 있으면 머지 갱신한다. 현재 이 파일을 생성·갱신하는 코드 경로가 전무하여(`dashboard/backend/config.py:33-52`는 읽기 전용, install·`console.sh` 어디에도 쓰기 없음), 프로젝트가 기본값 경로(`~/workspace`) 밖에 있는 신규 머신에서 대시보드가 떠도 프로젝트 목록이 비는 실사고를 근본 해결한다. install 연동으로 신규 머신에서 자동 1회 실행되며, dashboard 백엔드는 읽기 전용을 유지한다(021 결정 C-2).

### 1.2 기능 목록

TASK.md 요구사항 F-1~F-7을 그대로 F-001~F-007로 1:1 매핑한다 (임의 변경 없음).

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | scan 서브명령 신설 (마커 탐색 + 출력 계약) | TASK F-1, F-6(C-6 출력) | P0 | 없음 |
| F-002 | 머지 규칙 구현 (보존+추가+중복제거, --prune) | TASK F-2 | P0 | F-001 |
| F-003 | install 연동 (install_dashboard 말미 scan 1회) | TASK F-3 | P0 | F-001, F-002 |
| F-004 | start 가드 (config 부재 안내) | TASK F-4 | P1 | F-001 |
| F-005 | config.py 독스트링 정정 | TASK F-5 | P1 | 없음 |
| F-006 | windows.ps1 동기화 (install 연동 등가) | TASK F-6 | P1 | F-003 |
| F-007 | 테스트 (생성/머지/prune/출력계약/연동) | TASK F-7 | P0 | F-001~F-006 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-005 (독스트링, 독립)

F-001 ─┬─ F-002 ─┬─ F-003 ─── F-006
       │         │
       └─ F-004  │
                 │
F-001~F-006 ─────┴─→ F-007 (테스트, RED-first 선작성)
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 머지 로직 | 기존 수기 root/미지정 키 보존 계약 (C-3) — 덮어쓰기 시 사용자 편집분 유실 | P0 | L1(단위: 머지 결과 비교) | S-2, S-3 |
| H-2 | F-001 마커 탐색 | scan_root 도출 규칙 — `$OPAL_HOME/AGENT.md`를 프로젝트로 오탐 시 `/Users` 등 과도 root 추가 | P1 | L1(단위: OPAL 홈 제외 확인) | S-5 |
| H-3 | F-001 출력 | JSON 출력 계약(C-6) — `ok/created/added_roots/projects_found` 스키마 불일치 시 하네스·후속 소비 오류 | P1 | L1(단위: JSON 스키마 검사) | S-1, S-4 |
| H-4 | F-001 탐색 범위 | 전체 디스크 스캔 금지(C-2) — maxdepth·exclude 누락 시 성능/과탐 | P1 | L1(정적: find 옵션 검사) | S-6 |
| H-5 | F-002 --prune | --prune 없이 기존 root 제거 금지(C-3) — 프래그 오해석 시 데이터 손실 | P0 | L1(단위: prune on/off 대조) | S-3 |
| H-6 | F-001 write 대상 | 손상된 기존 config를 파싱 실패 시 무조건 덮어쓰면 사용자 데이터 유실 | P1 | L1(단위: 손상 파일 비파괴) | S-7 |
| H-7 | F-003 install 연동 | scan 실패가 install 전체를 중단시키면 배포 회귀 | P0 | L1(정적: 실패 격리 `\|\| true`) | S-8 |

---

## 2. 기능별 분석

### F-001: scan 서브명령 신설 (마커 탐색 + 출력 계약)

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/console.sh` | console 서브커맨드 (`cmd_console`) — scan action 신설 대상 | 수정 |
| 공통 | `opal/tools/opal-cli/run.sh` | 진입점 디스패처 — `usage()` help의 console 액션 목록에 scan 추가 | 수정 |
| 공통(참조) | `dashboard/backend/scanner.py` | 마커 탐색 규칙 SSOT — scan은 동일 규칙(`.opal/AGENT.md`)으로 프로젝트 발견 | 미변경(근거) |
| 공통(참조) | `dashboard/backend/config.py` | scan_roots/scan_depth/exclude 스키마·기본값 SSOT | 미변경(F-005는 독스트링만) |

#### 2.1.2 현재 구현 (직접 분석)
- `cmd_console()`는 `local action="${1:-}"`로 첫 인자를 받아 `case`로 start/stop/status/open/--help/`*`(unknown)을 분기한다 (`opal/tools/opal-cli/lib/console.sh:27-134`). scan은 이 case에 새 브랜치로 추가한다.
- 출력은 `info/success/warn/error` 헬퍼(run.sh:47-50)로 사람용 로그를 내되, TASK C-6은 **JSON 출력 계약**을 요구한다. scan은 사람용 로그를 stderr로, JSON 결과 1줄을 stdout로 분리 출력한다 (하네스 소비 계약 — `opal/core/references/opal-harness.md` §9).
- run.sh는 `console`을 이미 라우팅한다 (run.sh:113 `update|doctor|uninstall|mcp|console`). scan은 `cmd_console`의 내부 action이므로 **run.sh 디스패치 로직 변경 불필요** — usage() 도움말 1줄만 갱신한다 (run.sh:68).
- 마커 탐색 규칙: 스캐너는 `os.path.join(current_dir, ".opal", "AGENT.md")` 존재 시 OPAL 프로젝트로 등록하고 하위 탐색을 prune한다 (`dashboard/backend/scanner.py:96-108`). exclude 목록·숨김 디렉토리(.opal 제외) 진입 금지 (`scanner.py:128-131`). scan은 bash `find`로 동일 규칙을 재현한다.
- scan_root 도출: TASK C-1은 "마커 프로젝트의 **부모 디렉토리들**을 scan_roots로 도출"로 확정. 스캐너는 scan_root 하위 depth>0에서 프로젝트를 찾으므로(`scanner.py:94-108`), 프로젝트의 부모를 root로 등록하면 대시보드가 depth 1에서 재발견한다.

#### 2.1.3 영향 범위
- 소비자: `dashboard/backend/config.py load_config()`(읽기)만 scan_roots를 소비. scan은 config **파일**만 갱신하고 백엔드 코드는 무변경 → 021 C-2(읽기 전용) 보존.
- 호출자: F-003(install-mac.sh), F-006(windows.ps1)가 scan을 자동 호출.
- **[검출된 엣지 케이스]** 기본 base=`$HOME`으로 find 실행 시 `$HOME/.opal/AGENT.md`(= OPAL 배포 홈의 글로벌 AGENT.md, `opal/core/AGENT.md` 배포본)가 매칭된다(실측 확인). 이 마커의 "프로젝트"는 `$HOME`이고 부모는 `/Users`가 되어 과도한 root가 추가된다 → **discovery에서 `$OPAL_HOME` 자체를 반드시 제외**해야 한다 (H-2).

### F-002: 머지 규칙 구현

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/console.sh` | scan action 내 머지 로직 | 수정(F-001과 동일 함수) |

#### 2.2.2 현재 구현 (직접 분석)
- 실측 `~/.opal/console.config.json` 구조: `{scan_roots:[3개 /Volumes 경로], scan_depth:2, exclude:[5종]}` — 캡틴 머신은 태스크 021 진행 중 수동 작성한 런타임 파일(배포물 아님). 수기 편집분 보존이 필수(C-3).
- `config.py` 기본값 SSOT: `DEFAULT_SCAN_DEPTH=2`, `DEFAULT_EXCLUDE=["node_modules",".git",".venv","__pycache__",".DS_Store"]` (`dashboard/backend/config.py:21-23`). 신규 생성 시 이 값을 그대로 기록해야 백엔드 폴백값과 일치.
- bash 3.2(macOS)에는 신뢰할 JSON 파서가 없다. `jq`는 전 머신 보장 불가(이 맥엔 있으나 미보장). `python3`은 OPAL 전 구간 필수 의존(venv·config.py·doctor python 점검)이므로 **JSON 읽기/머지/쓰기를 `python3` 인라인 스크립트에 위임**한다. `find`(마커 탐색)만 bash가 담당 (도구 우선 원칙 — `docs/CONVENTIONS.md` §구현 규칙).

#### 2.2.3 영향 범위
- 미지정 키(scan_depth/exclude/사용자 추가 키) 보존: 기존 dict를 로드하여 `scan_roots`만 갱신 후 재직렬화하면 unknown 키 자동 보존 (H-1 대응).

### F-003: install 연동 (mac)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | `install_dashboard()` 말미 scan 1회 자동 실행 | 수정 |

#### 2.3.2 현재 구현 (직접 분석)
- `install_dashboard()`는 `scripts/install-mac.sh:1369-1411`. FE 빌드→BE 복사→완료 안내 순. 그 다음 `console_autostart()`(1419-)가 데몬을 재기동한다. 호출 순서: `install_dashboard`(1261) → `console_autostart`(1262), 메뉴 [5]도 동일(1859-1860).
- `console_autostart`는 배포된 `$opal_cli="$opal_home/bin/opal-cli"`를 `[[ -x ]]` 가드 후 위임하는 패턴을 이미 사용(1424, 1447-1448, 1461-1463). scan 호출도 동일 패턴으로 미러링.
- opal-cli는 dashboard보다 먼저 배포됨(`install_opal_bin` 1258 < `install_dashboard` 1261) → install 시점에 `~/.opal/bin/opal-cli` 사용 가능.

#### 2.3.3 영향 범위
- scan은 `install_dashboard()` 말미(완료 안내 직전, `console_autostart` 이전)에서 실행 → 데몬 기동 전에 config가 준비됨. 실패해도 install 중단 없음(H-7: `|| true` + `-x` 가드).

### F-004: start 가드

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/console.sh` | `start` action 초입에 config 부재 안내 | 수정 |

#### 2.4.2 현재 구현
- `start` action은 `console.sh:39-71`. 기동 전 health 체크·uvicorn·pkg 가드가 있다. config 부재 시 안내 문구를 `info/warn`으로 출력하되 **기동은 계속**(C-5).

#### 2.4.3 영향 범위 — 기동 흐름 무변경, 안내 출력만 추가.

### F-005: config.py 독스트링 정정

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/config.py` | `load_config()` 독스트링 | 수정(독스트링만) |

#### 2.5.2 현재 구현
- `config.py:33-38` 독스트링: "첫 기동 시 기본값 파일을 생성하지 않음 — PLAN §3.1.3: '런타임 생성/읽기' (설정 파일 생성은 install 단계에서 수행)". 배경 분석상 install에 생성 로직이 없어 문서·코드 불일치. 로직(`config.py:39-52`)은 **무변경**(021 C-2 읽기 전용 유지).

#### 2.5.3 영향 범위 — 독스트링만, 런타임 동작 무영향.

### F-006: windows.ps1 동기화

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install/windows.ps1` | `Install-Dashboard` 말미 scan 등가 로직 | 수정 |

#### 2.6.2 현재 구현
- `Install-Dashboard`는 `scripts/install/windows.ps1:986-`, 호출은 1736. bash `opal-cli`가 Windows에서 네이티브로 실행되지 않으므로, PowerShell 네이티브 등가 함수(`ConvertFrom-Json`/`ConvertTo-Json`)로 마커 탐색+머지+쓰기를 구현한다. 021에서 mac↔win을 "의미상 동등"으로 유지해온 정책 연장(`windows.ps1:990`).

#### 2.6.3 영향 범위 — 실기 검증 제외, 코드 리뷰 수준(TASK F-6 AC).

### F-007: 테스트

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/tests/test_console_scan.sh` | scan 생성/머지/prune/출력계약/연동 회귀 테스트 | 신규 |

#### 2.7.2 현재 구현 (테스트 배치 위치 확정)
- opal-cli에는 **전용 tests/ 디렉토리가 없다**(`opal/tools/opal-cli/`는 README.md·lib/·run.sh만). 다른 도구(state-tool 등)는 pytest를 쓰나 이는 Python 도구용.
- bash CLI·install 스크립트 테스트의 기존 선례는 **`scripts/tests/test_*.sh`** — `scripts/tests/test_version_stamp.sh`가 install-mac.sh·`opal-cli/lib/update.sh`를 이미 검증(pass/fail/skip 카운터·exit code·RED-first 주석 하네스, bash 3.2 호환). scan은 bash 서브명령 + install 연동이므로 **동일 위치·동일 하네스**가 정확한 배치다.
- **[확정] F-7 테스트 배치 = `scripts/tests/test_console_scan.sh`** (근거: `scripts/tests/test_version_stamp.sh` 선례, opal-cli tests/ 부재).

#### 2.7.3 영향 범위 — mktemp 격리 실행(HOME/OPAL_HOME override), 실 config 비파괴.

---

## 3. 기능별 설계

### F-001: scan 서브명령 신설

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/console.sh` | 공통 | `cmd_console` case에 `scan)` 브랜치 신설 (인자·플래그 파싱 → find 탐색 → python3 머지 → JSON 출력) + help에 scan 추가 | `console.sh:38` |
| 2 | `opal/tools/opal-cli/run.sh` | 공통 | `usage()` console 액션 목록에 `scan` 추가 | `run.sh:68` |

#### 3.1.2 API·데이터 모델·화면 설계

**서브명령 시그니처** (C-1):
```
opal-cli console scan [기준경로...] [--prune] [--depth N]
```
- `기준경로...`: 탐색 시작 경로(복수). 미지정 시 기본 `$HOME` 1개 (C-2 — `/Volumes/*` 등 외부 볼륨은 명시 인자로만). 실측상 이 맥의 실제 프로젝트는 `/Volumes/Data/...`에 있어 `$HOME` 기본으로는 발견되지 않음 → 안내 문구로 "프로젝트가 안 보이면 기준경로를 명시하라"를 출력.
- `--prune`: 지정 시에만 scan 미발견 기존 root 제거 (C-3). 미지정이 기본.
- `--depth N`: 마커 탐색 최대 깊이(프로젝트 디렉토리 기준). 기본값 `3` — `기준경로/그룹/하위그룹/프로젝트`까지 커버. [설계 결정·근거: 값 미확정 사안, C-2 "제한 깊이 탐색만" 준수 위해 유한값 채택. find는 `.opal/AGENT.md`가 프로젝트 아래 2단계(`.opal`+`AGENT.md`)이므로 실제 `-maxdepth $((N+2))` 적용].

**탐색 로직 (bash `find`)** — 스캐너 규칙 재현 (`scanner.py:96-131`):
```
for base in "${bases[@]}"; do
  [[ -d "$base" ]] || continue                     # 미존재 경로 스킵 (scanner.py:65)
  find "$base" -maxdepth $((depth+2)) \
       -type d \( -name node_modules -o -name .git -o -name .venv \
                  -o -name __pycache__ -o -name .DS_Store \) -prune -o \
       -type f -path '*/.opal/AGENT.md' -print 2>/dev/null
done
```
- 각 hit(`.../<project>/.opal/AGENT.md`)에서 `project_dir = ${hit%/.opal/AGENT.md}`, `scan_root = $(dirname "$project_dir")` 도출 (C-1 부모 디렉토리).
- **[MUST]** OPAL 홈 제외: `project_dir == $HOME` (즉 마커가 `$OPAL_HOME/AGENT.md`)이거나 `.opal` 디렉토리가 `$OPAL_HOME`와 동일하면 discovery에서 제외 (H-2 — 실측 오탐 방지).
- `projects_found` = 제외 후 유효 마커 수, `discovered_roots` = 유효 scan_root의 중복 제거 목록.
- exclude 기본값은 `config.py:23` DEFAULT_EXCLUDE와 동일 5종 사용 (C-2 전체 디스크 스캔 금지 — `-prune`).

**출력 계약 (C-6)** — stdout에 JSON 1줄, 사람용 로그는 stderr:
```json
{"ok":true, "created":true|false, "added_roots":["..."], "projects_found":N}
```
- 오류(기존 config 파싱 실패 등): `{"ok":false, "error":"<메시지>"}` + 비정상 종료코드 (`opal/core/references/opal-harness.md` §9).
- [MUST] `opal/core/references/opal-harness.md` §9: "OPAL 도구는 ... 출력은 JSON이며, `\"ok\": false`이면 `\"error\"` 필드를 확인하여 에스컬레이션한다."

**write 대상**: `${OPAL_HOME:-$HOME/.opal}/console.config.json`.
- **[배포 경계 판정 — 위반 아님]** `docs/CONVENTIONS.md` §배포 경계 "[MUST] `~/.opal/` 배포 파일을 직접 편집하지 않는다"는 **소스→install로 배포되는 프레임워크 산출물**(skills/agents/tools 등)을 대상으로 한다. `console.config.json`은 install 배포 대상이 아닌 **런타임 설정 파일**이다(태스크 021 DONE.md "런타임 설정 (배포물 아님)"; `update.sh`에 config 참조 0건 — 실측 확인). scan이 이 파일을 생성·갱신하는 것이 본 태스크의 목적이며, 배포 경계 위반이 아니다. OPAL_HOME 오버라이드를 지원하여 테스트 격리를 가능케 한다.

#### 3.1.3 환경 변경 — 해당 없음 (`python3`·`find`는 기존 필수 의존).
#### 3.1.4 배치/마이그레이션 — 해당 없음.
#### 3.1.5 테스트 시나리오 (AC ↔ TS)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC(생성·created:true) | 기능 | config 부재 상태 scan 시 파일 생성 + `{"ok":true,"created":true,...}` |
| TS-002 | F-1 AC(마커 부모=root) | 기능 | 마커 프로젝트의 부모 디렉토리가 scan_roots에 포함 |
| TS-003 | H-2(OPAL 홈 제외) | 기능 | base=$HOME 탐색 시 `$OPAL_HOME/AGENT.md`가 root로 추가되지 않음 |
| TS-004 | H-3(출력 계약) | 산출물 검사 | stdout JSON이 `ok/created/added_roots/projects_found` 키 스키마 준수 |
| TS-005 | H-4(디스크 스캔 금지) | 산출물 검사 | scan action에 `-maxdepth`·exclude `-prune` 존재 (정적) |

### F-002: 머지 규칙 구현

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/console.sh` | 공통 | scan 브랜치 내 python3 머지 스크립트 | (→ D-2 §21-23) |

#### 3.2.2 API·데이터 모델·화면 설계

**머지 알고리즘** (`python3` 인라인, stdin=discovered_roots JSON, argv=플래그):
```
existed  = CONFIG_PATH.exists()
data     = json.load(CONFIG_PATH) if existed else {}     # 파싱 실패 → ok:false, no write (H-6)
existing = list(data.get("scan_roots", []))
disc     = discovered_roots (중복 제거, bash에서 전달)
if prune:
    merged = [r for r in disc]                            # C-3: 미발견 기존 root 제거
else:
    merged = existing + [r for r in disc if r not in existing]  # 보존+추가+중복제거
data["scan_roots"] = dedup(merged)                        # 순서 보존 dedup
if not existed:                                           # 신규 생성 시에만 기본값 기록
    data.setdefault("scan_depth", 2)                      # config.py:22
    data.setdefault("exclude", ["node_modules",".git",".venv","__pycache__",".DS_Store"])  # config.py:23
# scan_depth·exclude·미지정 키: 기존 파일이면 절대 미변경 (dict 로드→scan_roots만 갱신→재dump = unknown 키 자동 보존, H-1)
write json.dumps(data, indent=2, ensure_ascii=False)
added = [r for r in data["scan_roots"] if r not in existing]
print({"ok":true,"created":not existed,"added_roots":added,"projects_found":N})
```
- [MUST] `docs/PROJECT.md`/TASK C-3: "config 없으면 생성, 있으면 머지(기존 roots 보존 + 신규 추가 + 중복 제거). scan이 못 찾은 기존 root도 지우지 않음 — 제거는 `--prune` 명시 플래그로만."
- 손상 파일 비파괴(H-6): 기존 파일 JSON 파싱 실패 시 write 금지·`ok:false` 반환 (config.py의 silent 폴백과 달리 scan은 write이므로 안전측).

#### 3.2.3 환경 변경 — 해당 없음.
#### 3.2.4 배치/마이그레이션 — 해당 없음.
#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | F-2 AC(수기 root 보존) | 기능 | 수기 root 포함 config에 scan 후 해당 root 그대로 유지 |
| TS-007 | F-2 AC(중복 없이 추가) | 기능 | 신규 root가 중복 없이 추가, 기존과 dedup |
| TS-008 | F-2 AC(--prune) | 기능 | `--prune` 시에만 미발견 기존 root 제거; 미지정 시 유지 |
| TS-009 | H-1(미지정 키 보존) | 기능 | 사용자 추가 키·scan_depth·exclude가 머지 후 보존 |
| TS-010 | H-6(손상 비파괴) | 기능 | 손상된 기존 config에 scan 시 `ok:false` + 원본 미변경 |

### F-003: install 연동 (mac)

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배치 | `install_dashboard()` 말미(완료 안내 직전)에 scan 1회 자동 실행 | `install-mac.sh:1408-1411` |

#### 3.3.2 설계
- `install_dashboard()` 말미(1408 `echo ""` 직전)에 삽입:
```
# ── console.config.json 자동 생성/갱신 (신규 머신 문제 근본 해결) ──
local opal_cli="$USER_HOME/.opal/bin/opal-cli"
if [[ -x "$opal_cli" ]]; then
    "$opal_cli" console scan "$USER_HOME" >/dev/null 2>&1 || \
        warn "console scan 실패 — 프로젝트 자동 탐색을 건너뜁니다 (수동: opal-cli console scan <경로>)"
fi
```
- [MUST] TASK F-3 AC: "scan 실패 시에도 install은 정상 종료한다." → `|| warn` (비치명), set -e 하의 파이프에서도 `|| true` 성격 유지.
- 기본 base `$USER_HOME`(C-2). `console_autostart`(1262) 이전에 실행되어 데몬 기동 전 config 준비.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-3 AC(연동 존재) | 산출물 검사 | `install_dashboard`에 `console scan` 호출 + 실패 격리(`\|\|`) 존재 (정적) |

### F-004: start 가드

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/console.sh` | 공통 | `start` action 초입에 config 부재 안내 | `console.sh:39-45` |

#### 3.4.2 설계
- `start)` 브랜치 초입(health 체크 전/후)에:
```
local config_path="${OPAL_HOME:-$HOME/.opal}/console.config.json"
if [[ ! -f "$config_path" ]]; then
    warn "console.config.json이 없습니다 — 대시보드에 프로젝트가 안 보일 수 있습니다."
    info "먼저 스캔을 실행하세요: opal-cli console scan <프로젝트-기준경로>"
fi
```
- [MUST] TASK C-5/F-4 AC: "config 부재면 scan 안내 메시지 출력(기동은 계속)." → 안내 후 return/exit 없이 기동 지속.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | F-4 AC | 산출물 검사 | `start` action에 config 부재 안내 문구 + scan 안내 존재 (정적) |

### F-005: config.py 독스트링 정정

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/config.py` | BE | `load_config()` 독스트링을 실제 생성 경로로 정정 | `config.py:34-38` |

#### 3.5.2 설계
- 독스트링(34-38)을 아래로 교체 (로직 39-52 무변경):
```
"""~/.opal/console.config.json 로드. 없으면 기본값 반환.

설정 파일 생성/갱신은 `opal-cli console scan [기준경로...]`가 수행하며,
install(install_dashboard)이 신규 머신에서 1회 자동 실행한다.
백엔드는 이 파일을 읽기 전용으로 소비한다(쓰기 없음, 태스크 021 C-2).
"""
```
- [MUST] 021 결정 C-2: dashboard 백엔드 읽기 전용 유지 — 로직 변경 금지.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | F-5 AC | 산출물 검사 | 독스트링이 `console scan`+install 연동을 서술, "install 단계에서 수행" 오기재 제거 (정적) |

### F-006: windows.ps1 동기화

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install/windows.ps1` | 배치 | `Install-Dashboard` 말미에 PS 네이티브 scan 등가 로직 | `windows.ps1:986,1736` |

#### 3.6.2 설계
- `Install-Dashboard` 말미(BE 복사 후)에 인라인 또는 헬퍼 함수 `Invoke-ConsoleScan`:
  - `$base = $HOME`; `Get-ChildItem -Recurse -Depth (N+2) -Filter AGENT.md -Path (Join-Path $base '*\.opal')` 대신 `.opal\AGENT.md` 경로 매칭으로 마커 수집 (exclude·OPAL 홈 제외 동일 규칙).
  - `project_dir = Split-Path (Split-Path $marker -Parent) -Parent`, `scan_root = Split-Path $project_dir -Parent`.
  - 기존 `console.config.json`을 `ConvertFrom-Json`→scan_roots 머지(보존+추가+dedup, `--prune` 미적용 기본)→`ConvertTo-Json`으로 기록.
  - 실패는 `try/catch` + `Write-OpalWarn`으로 격리(install 중단 없음).
- [MUST] TASK F-6 AC: "windows.ps1에 등가 로직이 존재한다 (실기 검증은 제외, 코드 리뷰 수준)."

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | F-6 AC | 산출물 검사 | `Install-Dashboard`(또는 헬퍼)에 마커 탐색+config 머지+실패 격리 등가 로직 존재 (정적 리뷰) |

### F-007: 테스트

#### 3.7.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `scripts/tests/test_console_scan.sh` | 배치 | scan 생성/머지/prune/출력계약/연동 테스트 (bash 하네스) | `scripts/tests/test_version_stamp.sh` 선례 |

#### 3.7.2 설계
- `test_version_stamp.sh` 하네스 재사용: `pass/fail/skip` 카운터, exit code(0/1), bash 3.2 호환(연관배열·mapfile 미사용), `mktemp -d` 격리.
- 격리 기법: `OPAL_HOME=$SCRATCH/.opal` + scratch 프로젝트 트리(`$SCRATCH/ws/proj-a/.opal/AGENT.md` 등) 생성 후 `console.sh`를 `source` 또는 `opal-cli console scan "$SCRATCH/ws"` 직접 호출. 실 `~/.opal/console.config.json` 비파괴.
- (가) 기능 계약 검증(RED 시점 FAIL): TS-001~010, (나) 정적/메커니즘 검증(구현 후·static): TS-004/005/011~014.
- RED-first: 이 파일은 **RED 산출물**(구현 전 작성), `opal-test-agent`(mode: red)가 작성. 상세는 TEST-SCENARIO.md.

#### 3.7.5 테스트 시나리오 — TS-001~TS-014 전체 커버 (위 각 F 참조).

---

## 3.5 참조 문서 테이블 → §8.3 참조.

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0 (RED) | F-007 | 7 | opal-test-agent (mode:red) | 단독 | 구현 전 실패 테스트 선작성 |
| 1 | F-001, F-002, F-004 | 1, 2 | opal-task-agent | 순차(동일 파일 console.sh) | scan 핵심 + start 가드 |
| 1 | F-005 | 4 | opal-be-agent | 병렬(독립 파일) | config.py 독스트링 |
| 2 | F-003 | 3 | opal-task-agent | 순차 | scan 완성 후 install 연동 |
| 2 | F-006 | 5 | opal-task-agent | 병렬(F-003과 등가·독립 파일) | windows.ps1 |
| 3 | 문서 | 6 | PM 직접 | 순차 | docs 갱신 |
| 4 (GREEN 확인) | F-007 | 7 | opal-test-agent | 단독 | 전체 GREEN 확인 (TEST 단계) |

### 4.2 실행 체크리스트

> 총 7개 Step | Phase 5개(RED 포함) | 실행 모드: 복잡

#### Step 1: console.sh — scan 서브명령 + 머지 로직 구현
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/console.sh`, `opal/tools/opal-cli/run.sh`
- **작업 내용**: `cmd_console` case에 `scan)` 브랜치 신설 — 인자/`--prune`/`--depth` 파싱, bash `find`로 `.opal/AGENT.md` 마커 탐색(maxdepth+exclude prune, `$OPAL_HOME` 제외), 프로젝트 부모→scan_root 도출, `python3` 인라인으로 기존 config 로드→머지(보존+추가+dedup, prune 분기, 미지정 키 보존, 손상 비파괴)→쓰기, stdout에 C-6 JSON 1줄·stderr에 사람 로그 출력. console.sh help·run.sh usage에 scan 추가. 변경이력 라인 추가.
- **완료 기준**: config 부재 시 생성+`created:true`, 마커 부모가 scan_roots에 포함, `$OPAL_HOME` 미포함, JSON 스키마 준수 (TS-001~010)
- **테스트**: TS-001~TS-010
- **실행 방법**: sub-agent
- **의존**: Step 7(RED 테스트 선작성) 이후

#### Step 2: console.sh — start 가드 추가
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/console.sh`
- **작업 내용**: `start)` 브랜치 초입에 config 부재 시 scan 안내(`warn`+`info`) 출력, 기동은 계속.
- **완료 기준**: config 부재 start 출력에 scan 안내 포함 (TS-012)
- **테스트**: TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1 (동일 파일)

#### Step 3: install-mac.sh — install_dashboard 말미 scan 연동
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `install_dashboard()` 완료 안내 직전(1408 이전)에 `$USER_HOME/.opal/bin/opal-cli console scan "$USER_HOME"` 호출(`-x` 가드 + `|| warn` 실패 격리). 변경이력 라인 추가.
- **완료 기준**: 연동 코드 + 실패 격리 존재, install 비중단 (TS-011)
- **테스트**: TS-011
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 4: config.py — 독스트링 정정
- [ ] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/config.py`
- **작업 내용**: `load_config()` 독스트링(34-38)을 `console scan`+install 연동+읽기 전용 서술로 교체. 로직(39-52) 무변경.
- **완료 기준**: 독스트링 정정, "install 단계에서 수행" 오기재 제거, 로직 diff 0 (TS-013)
- **테스트**: TS-013
- **실행 방법**: sub-agent
- **의존**: 없음 (병렬 가능)

#### Step 5: windows.ps1 — scan 등가 로직
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install/windows.ps1`
- **작업 내용**: `Install-Dashboard` 말미에 PS 네이티브 마커 탐색+config 머지(보존+추가+dedup)+실패 격리 로직 추가(`Invoke-ConsoleScan` 헬퍼 권장). 변경이력 라인 추가.
- **완료 기준**: 등가 로직 존재 (코드 리뷰 수준, TS-014)
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 3 (mac 로직 확정 후 이식)

#### Step 6: docs 갱신
- [ ] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`
- **작업 내용**: ARCHITECTURE §OPAL Console "프로젝트 식별" 행에 `console scan`이 config를 생성·갱신함을 명기 + 기동 행(`opal-cli console {start|stop|status|open}`)에 `scan` 추가. PROJECT.md `opal-cli console` 컴포넌트 설명·변경이력에 scan 반영. 양 문서 변경이력 행 추가.
- **완료 기준**: 두 문서에 scan 반영 + 변경이력 갱신
- **테스트**: 문서 검토(PM Gate)
- **실행 방법**: direct
- **의존**: Step 1

#### Step 7: RED 테스트 작성 (선행) + GREEN 확인
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 배치
- **agent**: opal-test-agent (mode: red)
- **파일**: `scripts/tests/test_console_scan.sh`
- **작업 내용**: `test_version_stamp.sh` 하네스 기반으로 TS-001~014 검증 테스트 작성. **Step 1 이전(RED)**: 기능 계약 TC는 구현 부재로 FAIL 확인·기록. **TEST 단계(GREEN)**: 전체 PASS + 기존 `scripts/tests/` 회귀 0.
- **완료 기준**: RED 시점 기능 TC FAIL 증거 → 구현 후 전체 PASS, exit 0
- **테스트**: 자기 자신 (self)
- **실행 방법**: sub-agent
- **의존**: 없음(RED 선작성) → GREEN은 Step 1~5 이후

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 7(RED) → Step 1 | RED-first: 실패 테스트 선작성 후 구현 (red-first.md §1) |
| Step 1 → Step 2 | 동일 파일(console.sh) 순차 수정 |
| Step 1 ∥ Step 4 | 독립 파일(console.sh ↔ config.py), 독립 기능 |
| Step 1,2 → Step 3 | scan 서브명령 완성 후 install이 호출 |
| Step 3 → Step 5 | mac 연동 로직 확정 후 windows 이식(등가) |
| Step 1 → Step 6 | 구현 확정 후 문서 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | config 부재→생성, 마커 부모→root, OPAL 홈 제외, JSON 계약 | TS-001~005 | 전 항목 기대결과 일치 |
| F-002 | 수기 root 보존·중복제거·prune·미지정 키·손상 비파괴 | TS-006~010 | 전 항목 기대결과 일치 |
| F-003 | install 연동 + 실패 격리 | TS-011 | 정적 검사 PASS |
| F-004 | start 가드 안내 | TS-012 | 정적 검사 PASS |
| F-005 | 독스트링 정정 | TS-013 | 정적 검사 PASS |
| F-006 | windows 등가 로직 | TS-014 | 정적 리뷰 PASS |
| F-007 | 테스트 전체 GREEN + 회귀 0 | TS-001~014 | exit 0 |

### 5.2 회귀 테스트
- [ ] `bash scripts/tests/test_version_stamp.sh` 통과 (install-mac.sh 회귀 0)
- [ ] `opal-cli console start/stop/status/open` 기존 동작 무변경
- [ ] dashboard 백엔드 `load_config()` 로직 diff 0 (읽기 전용 보존)

### 5.3 코드/문서 품질
- [ ] bash 3.2 호환 (연관배열·mapfile 미사용)
- [ ] console.sh·run.sh·install-mac.sh·windows.ps1 변경이력 라인 추가
- [ ] ARCHITECTURE.md·PROJECT.md 변경이력 표 행 추가

### 5.4 보안
- [ ] scan이 전체 디스크를 순회하지 않음 (maxdepth+exclude) — C-2
- [ ] 하드코딩 시크릿·토큰 없음
- [ ] 실 `~/.opal/console.config.json`을 테스트가 파괴하지 않음 (격리)
- [ ] 손상된 config를 무조건 덮어쓰지 않음 (H-6)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 6개 (console.sh, run.sh, install-mac.sh, config.py, windows.ps1, +신규 test) | 복잡 |
| 모듈 범위 | 다중 (CLI/install/backend/test) | 복잡 |
| 작업 유형 | 신규 개발(서브명령) | 복잡 |
| 외부 의존성 | 없음 (python3·find 기존 의존) | 단순 |
| **실행 모드** | **복잡** | |

> 에스컬레이션 판단: Step 7개로 Short Task 5-Step 권장을 초과하나, 단일 CLI 서브명령 + 배포 연결이라는 **응집된 단일 피처**이며 ANALYSIS가 요구할 신규 코드베이스 탐색 부담이 낮다. 복잡 모드(§7)로 opds 내 실행하며 Full Task 전환은 불필요.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 0 (RED):   opal-test-agent(red) → test_console_scan.sh [FAIL 증거]
Batch 1:         opal-task-agent(console.sh: Step1→Step2)  ∥  opal-be-agent(config.py: Step4)
Batch 2:         opal-task-agent(install-mac.sh: Step3) → opal-task-agent(windows.ps1: Step5)
Batch 3:         PM(docs: Step6)
Batch 4 (GREEN): opal-test-agent → 전체 PASS 확인
```
- 파일 충돌 방지: console.sh는 Step1·2 동일 에이전트 순차. install-mac.sh↔windows.ps1은 별 파일이나 등가 로직이라 확정→이식 순서로 순차.

### C-2. 스킬 요구사항
- 기존 단계 스킬(op-dev-execute)로 충분. 신규 스킬 갭 없음(1개 피처).

### C-3. 도구 요구사항
- `python3`(JSON 머지, 기존 필수), `find`(마커 탐색, POSIX), `curl`(기존 health). 신규 패키지 없음.

### C-4. 테스트 전략
- RED-first 적용(§TEST-SCENARIO). RED 작성자=opal-test-agent(mode:red), 구현자≠작성자.
- 기능 테스트: `bash scripts/tests/test_console_scan.sh` (mktemp 격리, OPAL_HOME override).
- 회귀: `bash scripts/tests/test_version_stamp.sh`.
- 품질: bash 3.2 호환 확인, shellcheck 권장.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| CLI | Bash (macOS zsh/bash 3.2 호환) | - |
| JSON 처리 | python3 인라인 | - |
| 백엔드 | Python 3 / FastAPI (독스트링만) | - |
| Windows 배포 | PowerShell | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 신규 라이브러리 API 조회 불요 — bash/python3 표준 기능만 사용 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | console.sh | `opal/tools/opal-cli/lib/console.sh` | cmd_console 구조·start/help·JSON 출력 패턴 |
| D-2 | 소스 | config.py | `dashboard/backend/config.py` | scan_roots/scan_depth/exclude 스키마·기본값(21-23)·load_config 로직 |
| D-3 | 소스 | scanner.py | `dashboard/backend/scanner.py` | `.opal/AGENT.md` 마커 탐색 규칙(96-131) — scan이 재현할 SSOT |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | install_dashboard(1369-1411)·console_autostart 위임 패턴·호출 순서(1261-1262) |
| D-5 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | Install-Dashboard(986)·호출(1736)·mac 등가 정책 |
| D-6 | 소스 | run.sh | `opal/tools/opal-cli/run.sh` | console 라우팅(113)·usage(68)·색상/헬퍼 |
| D-7 | 소스 | test_version_stamp.sh | `scripts/tests/test_version_stamp.sh` | bash 테스트 하네스 선례·RED-first 패턴·테스트 배치 위치 |
| D-8 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | OPAL Console 프로젝트 식별(.opal/AGENT.md 스캔) §267·읽기 전용 원칙 |
| D-9 | 설계 | 하네스 도구 계약 | `opal/core/references/opal-harness.md` §9 | JSON 출력·ok/error 계약 |
| D-10 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·도구 우선·변경이력·플랫폼 분기 격리 |
| D-11 | 설계 | 021 opal-console | `tasks/backup/021-260615-opd-opal-console/` | C-2 읽기 전용 결정·config "런타임 설정(배포물 아님)" |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `$HOME/.opal/AGENT.md` 오탐으로 과도 root 추가 | F-001 | P1 | discovery에서 `$OPAL_HOME` 제외 (H-2, TS-003) |
| R-2 | 머지가 수기 편집분/미지정 키를 유실 | F-002 | P0 | dict 로드→scan_roots만 갱신→재dump; prune 옵트인 (H-1/H-5, TS-006~009) |
| R-3 | 손상 config를 덮어써 데이터 유실 | F-002 | P1 | 파싱 실패 시 ok:false·write 금지 (H-6, TS-010) |
| R-4 | scan 실패가 install 중단 유발 | F-003 | P0 | `-x` 가드 + `\|\| warn` 실패 격리 (H-7, TS-011) |
| R-5 | $HOME 기본 탐색이 외부 볼륨(/Volumes) 프로젝트 미발견 | F-001 | P2 | 안내 문구로 기준경로 명시 유도 (C-2 설계 의도) |
| R-6 | 전체 디스크 스캔 위험 | F-001 | P1 | maxdepth + exclude prune (H-4, TS-005) |
| R-7 | dashboard 백엔드 쓰기 오염 | F-005 | P0 | 독스트링만 변경, 로직 diff 0 (021 C-2) |

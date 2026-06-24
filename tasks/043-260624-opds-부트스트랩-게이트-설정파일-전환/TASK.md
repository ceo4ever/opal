# TASK: 부트스트랩 스킵 게이트 — 환경변수 → 배포 설정파일(setting.json) 전환

> 작성일: 2026-06-24 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

040이 도입한 부트스트랩 스킵 게이트의 메커니즘을 **Bash 환경변수 체크(`echo $OPAL_BOOTSTRAP`)에서 배포된 설정파일(`~/.opal/setting.json`) Read 기반으로 전환**하여, 매 세션 게이트 체크가 권한 프롬프트 없이 자동 수행되도록 한다. 동시에 설정파일을 향후 런타임 설정 확장의 거점으로 삼는다.

## 배경

040에서 `OPAL_BOOTSTRAP=off` 환경변수로 부트스트랩 전체를 스킵하는 게이트를 도입했다(부트스트래퍼 4종 + `opal/core/AGENT.md` Eager step 0). 그러나 게이트가 매 세션 `echo $OPAL_BOOTSTRAP`를 Bash로 실행하는데, 이 명령이 **매번 권한 프롬프트를 띄운다**. 일반 사용자가 OPAL을 설치해 매 세션 claude를 호출할 때마다 선택을 강요받으므로, "필요할 때만 토글하고 평소엔 무간섭"이라는 기능 의도를 위반한다.

## 배경 분석 (대화에서 도출)

### 1. 프롬프트 원인 (권위 확인 완료 — claude-code-guide)

- `echo $OPAL_BOOTSTRAP`는 셸 변수 확장(simple_expansion)을 포함한다. Claude Code는 이를 read-only로 취급하지 않아 정적으로 안전성을 보증할 수 없고, **허용 규칙(`Bash(echo $OPAL_BOOTSTRAP)`)으로도 자동 승인되지 않는다**(실측: 활성 설정에 규칙이 로드돼 있는데도 fresh 세션에서 프롬프트 재발).
- v2.1.139+에서 simple_expansion 자동승인은 `sandbox.enabled + autoAllowBashIfSandboxed`를 켜야만 적용 → 캡틴 환경(v2.1.187, 샌드박스 미사용) 미해당.
- `printenv OPAL_BOOTSTRAP`(확장 없는 read-only)로 바꾸면 허용 가능하나, 여전히 **권한 등록 표면**이 남고 플랫폼별 install 정합이 필요하다.

### 2. 설정파일 접근의 우위 (채택 방향)

- 부트스트랩은 **이미 맨 처음** `Read(~/.opal/AGENT.md)`·`identity.md`를 읽는다. 이 Read 경로는 이번 세션에서도 프롬프트 없이 통과됐다(캡틴이 문제 삼은 것은 오직 Bash `echo`).
- 게이트를 `Read(~/.opal/setting.json)`로 전환하면 **이미 작동하는 Read 경로에 얹는 것** → Bash·변수확장·플랫폼별 권한 등록이 모두 불필요. 새 권한 표면 0.
- 확장성: `setting.json`은 향후 기본 모드·토글 등 런타임 설정을 누적할 거점이 된다(캡틴 의도).

### 3. 게이트 명령 소스 위치 (전수 — 배포본 `~/.opal` 제외)

| # | 파일 | 위치 |
|---|------|------|
| S-1 | `opal/core/AGENT.md` | `:13` Eager step 0 게이트 문구 |
| S-2 | `opal/bootstrapper/claude-bootstrap.md` | `:17` 스킵 게이트 문구 |
| S-3 | `opal/bootstrapper/gemini-bootstrap.md` | `:17` 스킵 게이트 문구 |
| S-4 | `opal/bootstrapper/codex-bootstrap.md` | `:17` 스킵 게이트 문구 |
| S-5 | `opal/bootstrapper/cursor-bootstrap.mdc` | 스킵 게이트 문구 (라인 PLAN 확인) |
| S-6 | `scripts/install-mac.sh` | `:395` `install_claude_permissions` perm_entries에 추가된 `Bash(echo $OPAL_BOOTSTRAP)` (직전 L2 작업분, 미커밋) |

### 4. 패리티 갭 (config-file 접근이 무력화)

- `install_claude_permissions`는 **macOS install에만** 존재. Windows(`scripts/install/windows.ps1`)·Linux(`scripts/install/linux.sh`)는 Claude 권한 등록 함수 자체가 없다.
- 환경변수/printenv 접근이었다면 이 갭을 메워야 했으나, **설정파일 Read 접근은 부트스트랩이 이미 쓰는 Read 경로를 재사용**하므로 갭 자체가 쟁점에서 사라진다.

### 5. 미커밋 상태 (이 태스크에서 reconcile)

- `git status`: `M scripts/install-mac.sh` — 직전 L2로 추가한 `Bash(echo $OPAL_BOOTSTRAP)` 권한 + v3.5 변경이력. 이번 전환으로 환경변수 접근 자체가 폐기되므로, 이 변경분은 본 태스크 EXECUTE에서 원복/대체된다.

## 확정된 설계 방향 (대화에서 합의)

1. **게이트 메커니즘 전환**: `echo $OPAL_BOOTSTRAP`(Bash) → `~/.opal/setting.json`의 필드 Read.
2. **스키마 시작점**: `{"bootstrap": "on" | "off"}` (이후 키 확장 가능).
3. **게이트 로직**: 값이 `off`면 전체 부트스트랩 스킵 / 파일 없음·필드 없음·파싱 실패 = 정상 진행(fail-safe 유지, 040 동작 계승).
4. **install 배포 = create-if-absent**: 기존 파일이 있으면 덮어쓰지 않는다(사용자 토글이 재설치에도 보존).
5. **환경변수 메커니즘 폐기**: 단일 메커니즘(설정파일)으로 통일. 직전 L2로 추가된 `Bash(echo $OPAL_BOOTSTRAP)` 권한도 정리.
6. **변경이력**: 수정한 모든 부트스트래퍼/코어 문서·install 스크립트에 변경이력 행 추가.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 부트스트랩 스킵 게이트를 환경변수 Bash 체크에서 배포 설정파일(`~/.opal/setting.json`) Read로 전환, 무프롬프트 보장 | - | 배경분석 §1·§2 |
| 범위 | 포함: 게이트 메커니즘 전환(S-1~S-6), `setting.json` 신규 배포(create-if-absent), 환경변수 접근·권한 정리, 변경이력. 제외: 신규 설정 키 추가(스키마는 bootstrap 1개로 시작), CI/배포 자동화 | 프로젝트 단위 오버라이드(`{프로젝트}/.opal/setting.json`) 채택 여부 | 배경분석 §3 |
| 제약 | 배포 경계(`~/.opal` 직접 편집 금지, 소스만 수정 후 install 재배포). 플랫폼 독립(분기는 어댑터에만). fail-safe 불변. 부트스트래퍼 마커는 install이 생성하는 SSOT | - | PRINCIPLES, AGENT.md 금지사항 |
| 완료기준 | ①install 후 `~/.opal/setting.json` 존재 ②`bootstrap:"off"`로 두면 fresh 세션이 **프롬프트 없이** 부트스트랩 스킵 ③`"on"`/필드제거/파일부재면 정상 부트스트랩 ④재설치 시 기존 setting.json 미덮어씀 ⑤소스에 `echo $OPAL_BOOTSTRAP` Bash 게이트 잔존 0 | Read(~/.opal/**) fresh 무프롬프트 실증 | 배경분석 §2 |

## 요구사항

- [ ] R-1 (설정파일 신규): `~/.opal/setting.json` 배포용 소스를 프레임워크에 추가한다. 스키마 `{"bootstrap": "on"|"off"}`(기본 `on`). — 어디에: `opal/` 하위 적절 위치(PLAN 확정) / 왜: 확정방향 §2 / AC: 소스 파일이 존재하고 유효 JSON이며 `bootstrap` 키를 가진다.
- [ ] R-2 (install 배포 create-if-absent): install이 `~/.opal/setting.json`을 **없을 때만** 생성한다(기존 보존). — 어디에: `scripts/install-mac.sh`(+PLAN이 Windows/Linux 정합 판단) / 왜: 확정방향 §4 / AC: setting.json 부재 시 생성됨, 존재 시 내용 불변(멱등 재실행 dry-run으로 검증 가능).
- [ ] R-3 (게이트 로직 전환): 부트스트랩 Eager step 0을 `setting.json` Read 기반으로 재작성한다. `bootstrap=="off"`면 전체 스킵, 그 외/부재/실패면 정상 진행(fail-safe). — 어디에: S-1 `opal/core/AGENT.md:13` / 왜: 확정방향 §1·§3 / AC: step 0 문구가 setting.json Read를 지시하고, off 스킵 + fail-safe 정상진행 분기를 명시한다. `echo $OPAL_BOOTSTRAP` 문자열 없음.
- [ ] R-4 (부트스트래퍼 4종 정합): S-2~S-5 부트스트래퍼 마커의 스킵 게이트 문구를 setting.json Read 기반으로 교체한다. — 어디에: `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md`, `cursor-bootstrap.mdc` / 왜: 확정방향 §1 / AC: 4파일 모두 `echo $OPAL_BOOTSTRAP` 제거, setting.json 게이트 문구로 일관 교체.
- [ ] R-5 (환경변수 접근·권한 정리): S-6 `install_claude_permissions`의 `Bash(echo $OPAL_BOOTSTRAP)` 항목 제거(직전 L2분 원복). 환경변수 잔재 정리. — 어디에: `scripts/install-mac.sh:395` / 왜: 확정방향 §5 / AC: perm_entries에 `echo $OPAL_BOOTSTRAP` 없음, install 구문 정상(`bash -n`).
- [ ] R-6 (변경이력): R-2~R-5에서 수정한 각 문서·스크립트의 변경이력 표에 행을 추가한다(일시 KST + 태스크 043). — AC: 수정한 각 파일에 043 행이 존재한다.

## 제약 조건

- **배포 경계**: `~/.opal/` 배포본 직접 편집 금지. 소스(`opal/`, `scripts/`)만 수정 후 install로 재배포. setting.json 실배포·실세션 검증은 캡틴이 install 재실행 시점.
- **플랫폼 독립**: 플랫폼 분기는 어댑터 계층(install·bootstrapper)에서만. 코어 AGENT.md 로직 불변 원칙.
- **fail-safe 불변**: 040의 "게이트 불확실 시 정상 진행" 안전 동작을 계승한다.
- **부트스트래퍼 마커 SSOT**: 마커는 install이 생성한다(040 핵심발견: emit 함수 아닌 bootstrapper 파일이 SSOT).
- **커밋**: 사용자 명시 요청 시에만.

## 기술 스택

- Bash (install-mac.sh), PowerShell (windows.ps1), Python3 (install 내 JSON 처리), Markdown/MDC (부트스트래퍼·코어 문서), JSON (setting.json)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | 코어 부트스트랩 정의 | `opal/core/AGENT.md` | 게이트 step 0 SSOT (S-1) |
| D-2 | 소스 | 부트스트래퍼 마커 | `opal/bootstrapper/*.md`, `*.mdc` | 게이트 문구 교체 대상 (S-2~S-5) |
| D-3 | 소스 | macOS install | `scripts/install-mac.sh` | 권한 등록·setting.json 배포 (S-6, R-2/R-5) |
| D-4 | 태스크 | 040 부트스트랩 스킵 | `tasks/040-260624-opds-부트스트랩-스킵/` | 전환 대상 원 설계 |

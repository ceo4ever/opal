# TEST-SCENARIO: 부트스트랩 스킵 게이트 — 환경변수 → 배포 설정파일(setting.json) 전환

> 태스크: 043-260624-opds-부트스트랩-게이트-설정파일-전환 | 작성일: 2026-06-24
> RED-first: **혼합** — F-001 install create-if-absent 함수=RED-first 적격(동작 로직, TS-002/TS-003) / F-002 게이트 문구 교체·F-003 perm 정리=정적 검증 트랙. SSOT: `opal/core/references/harness/red-first.md`
> 검증 계층: L1(산출물 grep/구조·bash -n) → L2(install 재배포·멱등 셸 테스트) → L3(수동 실세션 off/on/부재 동작)
> 입력: PLAN.md 리스크 가설 표(H-1~H-8) + §3.x.5 테스트 시나리오 + §5 QA 매트릭스 + §RED-first 트랙 판단

---

## 1. 시나리오 목록

### RED-first 트랙 — install create-if-absent 동작 검증 (BE 모드, 작성자≠구현자)

> red-first.md §1·§2 — opal-test-agent(mode: red)가 RED(실패) 셸 테스트를 선작성, opal-be-agent가 GREEN 구현. RED 테스트는 GREEN 루핑 중 수정 금지(§3). 공개 인터페이스(함수 호출 결과·파일 내용·exit code)로 검증(§4).

| TS-ID | 항목 | 대상 | 검증 방법 | PASS 조건 | RED 증거 | 결과 |
|-------|------|------|----------|----------|---------|------|
| TS-002 | create-if-absent 멱등 — 존재 시 불변 (H-1) | `install_opal_setting` (`scripts/install-mac.sh`) | 임시 HOME에 `~/.opal/setting.json={"bootstrap":"off"}` 선배치 → 함수 1회 호출 → 파일 내용 diff | 호출 후 setting.json 내용이 호출 전과 **완전 동일**(off 토글 보존). exit 0 | 구현 전 함수 부재 → 호출 실패(exit≠0) 또는 파일 덮어씌워짐 = RED | ✅ PASS |
| TS-003 | create-if-absent 생성 — 부재 시 생성 (H-2) | `install_opal_setting` (`scripts/install-mac.sh`) | 임시 HOME에 `~/.opal/setting.json` 부재 상태 → 함수 1회 호출 → 파일 검사 | setting.json 생성됨 + `python3 -c "import json,sys;d=json.load(open(sys.argv[1]));assert 'bootstrap' in d"` 통과(exit 0) | 구현 전 함수 부재 → 파일 미생성 = RED | ✅ PASS |

### L1 — 산출물 검사 (정적·결정론적)

| TS-ID | 항목 | 대상 파일 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|---------|----------|----------|------|
| TS-001 | setting.json 배포 소스 유효성 | `opal/core/setting.default.json` | `python3 -c "import json;d=json.load(open(...));assert d.get('bootstrap')=='on'"` | 유효 JSON + `bootstrap` 키 값 `"on"` (exit 0) | ✅ PASS |
| TS-004 | install 구문 무결 + 호출부 | `scripts/install-mac.sh` | `bash -n scripts/install-mac.sh` + `grep -c 'install_opal_setting' scripts/install-mac.sh` | bash -n 통과(exit 0) + 함수 정의 1 + `install_opal` 내 호출 1 (총 ≥2 매칭) | ✅ PASS |
| TS-013 | Linux 자동 상속 (코드 변경 부재) | `scripts/install/linux.sh` | `grep -c 'exec bash' scripts/install/linux.sh` + setting.json 관련 코드 부재 확인 | exec 위임 구조 유지(install-mac.sh 위임) + linux.sh에 setting.json 별도 코드 0건 | ✅ PASS |
| TS-014 | Windows create-if-absent 블록 | `scripts/install/windows.ps1` | Install-OpalCore 내 `setting.json` + `Test-Path` 가드 블록 grep | create-if-absent 블록 존재(`-not (Test-Path $settingDst)` 가드 + Copy-Item) | ✅ PASS |
| TS-005 | 코어 AGENT.md step 0 게이트 전환 (S-1) | `opal/core/AGENT.md` | `### Eager 단계` 내 step 0 grep: `setting.json` + `bootstrap` + `off` + fail-safe(`파싱`/`부재`/`정상 진행`) + `[WORKER` 구분 + `echo $OPAL_BOOTSTRAP` 부재 | step 0이 setting.json Read 게이트 + fail-safe 분기 명시 + WORKER 구분 + echo 0건. step 0이 step 1 앞 | ✅ PASS |
| TS-006 | claude 마커 전환 + 추출 무결 (S-2, H-6) | `opal/bootstrapper/claude-bootstrap.md` | `sed -n '/```markdown/,/```/p'` 추출 결과 grep: `setting.json` 게이트 존재 + `echo $OPAL_BOOTSTRAP` 0건 + 코드 펜스 추가 없음(추출 조기종료 없음) | 코드블록 내 setting.json 게이트 + echo 0 + 코드블록 정상 추출 | ✅ PASS |
| TS-007 | gemini 마커 전환 (S-3) | `opal/bootstrapper/gemini-bootstrap.md` | 코드블록 추출 grep: `setting.json` 게이트 + echo 0건 | 코드블록 내 setting.json 게이트 + echo 0 | ✅ PASS |
| TS-008 | codex 마커 전환 (S-4) | `opal/bootstrapper/codex-bootstrap.md` | 코드블록 추출 grep: `setting.json` 게이트 + echo 0건 | 코드블록 내 setting.json 게이트 + echo 0 | ✅ PASS |
| TS-009 | cursor 마커 전환 + frontmatter 무손상 (S-5, H-5) | `opal/bootstrapper/cursor-bootstrap.mdc` | frontmatter `---` 구조 확인 + 본문 grep: `setting.json` 게이트 + echo 0건 | `---`/`alwaysApply: true` 무손상 + 본문 setting.json 게이트 + echo 0 | ✅ PASS |
| TS-010 | 5곳 게이트 의미 동기 (H-4) | AGENT.md + bootstrapper 4종 | 조건(`off`)·동작(전부 스킵)·fail-safe(파일/필드 부재·파싱실패=정상 진행) 표현 5곳 교차 확인 | 5곳 조건·동작·fail-safe 의미 일치 | ✅ PASS |
| TS-012 | perm echo 제거 + 구문 무결 (S-6, H-7) | `scripts/install-mac.sh` | `perm_entries` 라인 grep: `echo $OPAL_BOOTSTRAP` 0건 + `bash -n` 통과 | perm_entries에 echo 0 + Read 2개 유지 + bash -n 통과 | ✅ PASS |
| TS-015 | 소스 echo 게이트 잔존 0 (완료기준 ⑤) | `opal/`, `scripts/` 전체 | `grep -rn 'echo $OPAL_BOOTSTRAP' opal/ scripts/` (변경이력 과거 기록 행 제외) | 게이트 명령으로서의 `echo $OPAL_BOOTSTRAP` 0건 (변경이력 설명 텍스트만 허용) | ✅ PASS |
| TS-016 | 변경이력 행 추가 (R-6) | AGENT.md·claude/gemini/codex-bootstrap.md·install-mac.sh 헤더·windows.ps1 헤더 | 각 파일 변경이력에 `043` 행 grep | 각 파일에 043 행 존재 (cursor.mdc 제외 — 표 부재 D-4) | ✅ PASS |

### L2 — install 재배포 후 확인 (사용자 승인 후 수행)

| TS-ID | 항목 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-002b | install 2회 재실행 멱등 (실배포) | 캡틴 `~/.opal/setting.json`을 `{"bootstrap":"off"}`로 둔 뒤 install 재실행 ×2 | 재실행 후에도 setting.json off 토글 보존(덮어쓰기 0) | ⏸ pending (캡틴 직접 수행 대기) |

### L3 — 실세션 동작 (수동, L2 이후 — 환경 의존)

| TS-ID | 항목 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-011a | `off` 세션 무프롬프트 스킵 | install 재배포 + `~/.opal/setting.json={"bootstrap":"off"}` → 새 세션 | 첫 응답 전 setting.json Read 1회(무프롬프트) + 부트스트랩 step 1~7 스킵 + 부트스트랩 보고 없음 | ⏸ pending (캡틴 직접 확인) |
| TS-011b | `on`/필드제거/파일부재 세션 정상 (fail-safe 회귀) | setting.json `on` / `bootstrap` 키 제거 / 파일 삭제 각 케이스로 새 세션 | 3 케이스 모두 기존 7단계 부트스트랩 정상 + `[부트스트랩] ✅` 보고 | ⏸ pending (캡틴 직접 확인) |

---

## 2. 코드 품질

> L1 정적 검사 기반 — install은 `bash -n`, setting.json은 JSON 유효성. 마크다운/설정 변경.

| 항목 | 기준 | 결과 |
|------|------|------|
| 변경이력 기록 | AGENT.md + claude/gemini/codex-bootstrap.md + install-mac.sh 헤더 + windows.ps1 헤더에 043 행(KST 일시·semver) | ✅ PASS (TS-016) |
| 코드 펜스 미사용 | claude/codex/gemini 코드블록 내 게이트 문구에 코드 펜스(` ``` `) 없음, 인라인 백틱만 (H-6 방어) | ✅ PASS (TS-006~008) |
| 5곳 문구 의미 일치 | 조건(`정확히 off`) + 동작(전부 스킵) + fail-safe(파일/필드 부재·파싱실패=정상 진행) 동일 | ✅ PASS (TS-010) |
| 멱등 가드 명시 | `install_opal_setting`에 `[[ -f "$dst" ]]` early-return / windows `-not (Test-Path)` 가드 | ✅ PASS (TS-002, TS-014) |
| cursor frontmatter 무손상 | `---`/`alwaysApply: true` 구조 보존 (H-5) | ✅ PASS (TS-009) |

---

## 3. 보안

| 항목 | 기준 | 결과 |
|------|------|------|
| 시크릿 없음 | setting.json·게이트 문구·install 블록에 토큰/시크릿 없음 | ✅ PASS |
| 권한 최소 — 신 표면 0 | 기존 `Read(~/.opal/**)`·`Read({opal_home}/**)` 재사용, 신규 권한 등록 0. Bash echo 권한 제거 | ✅ PASS (TS-012, PLAN §1.2) |
| 민감정보 비저장 | setting.json은 `bootstrap` 토글만 보유 (인증/네트워크/시크릿 없음) | ✅ PASS (TS-001) |

---

## 4. 회귀 테스트

| 항목 | 기준 | 결과 |
|------|------|------|
| fail-safe 불변 | setting.json `on`/필드제거/파일부재 세션에서 기존 7단계 부트스트랩 정상 (040 계승) | ⏸ pending (TS-011b — 캡틴 직접 확인) |
| 기존 `[WORKER]` 스킵 불변 | 디스패치 프롬프트 첫 줄 `[WORKER]` 동작 — 게이트 전환으로 영향 없음 | ✅ PASS (TS-005 — WORKER 구분 유지 확인) |
| install 멱등 (setting + 마커) | 재실행 시 setting.json 내용 불변(TS-002b) + 마커 중복 누적 없음(install_opal_section 멱등) | ✅ PASS (L1: TS-002 함수 계약) / ⏸ pending (L2: 실배포 멱등 — 캡틴) |
| Read 권한 유지 | `Read(~/.opal/**)`, `Read({opal_home}/**)` 2개 유지 — 무프롬프트 보장 불변 | ✅ PASS (TS-012) |

---

## 5. 설계 피드백 및 미해결 빈틈

| 항목 | 상태 |
|------|------|
| 핵심 가정 (Read 무프롬프트) | ✅ 실증 — PLAN §1.2: install이 `Read(~/.opal/**)` 등록(`scripts/install-mac.sh:395`) + 부트스트랩이 이미 동일 경로 Read |
| 소스 위치 (규명 #2) | ✅ 결정 — `opal/core/setting.default.json` (PLAN §3.1.2 D-1) |
| Windows/Linux 정합 (규명 #5) | ✅ 결정 — Linux 자동 상속(exec 위임), Windows create-if-absent 블록 추가 (PLAN §3.1.2 D-2). 미반영도 fail-safe 안전망 |
| 프로젝트 오버라이드 (규명 #6) | ⏸ 범위 외 — 글로벌 `~/.opal/setting.json` 단일 채택. 우선순위 규칙은 후속 태스크 (PLAN §3.1.2 D-3, H-8) |
| TS-011a/b 실세션 | L3 — install 재배포·실세션은 캡틴 직접 수행. TEST 단계에서 L1+RED-first GREEN 통과 후 보고 포함 |
| H-1 멱등성 (사용자 토글 유실) | RED-first TS-002로 집행 — 존재 시 불변 계약을 테스트가 게이트 |

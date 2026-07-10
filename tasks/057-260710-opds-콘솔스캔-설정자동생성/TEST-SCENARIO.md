# TEST-SCENARIO: opal-cli console scan — console.config.json 자동 생성·머지

> 작성일: 2026-07-10 | 입력: PLAN.md §리스크 가설 표 + §3.N.5 테스트 시나리오
> 검증 대상: F-001~F-007 / TS-001~TS-014
> 트랙 규칙 SSOT: `opal/core/references/harness/red-first.md`

---

## 0. 동작검증 원칙 (배포 산출물 기준)

[MUST] `deploy-artifact-verification-lesson`(태스크 021 교훈): 동작검증은 **배포 산출물 + 실제 실행** 기준으로 수행한다. 따라서:
- scan 서브명령은 소스(`opal/tools/opal-cli/lib/console.sh`) 편집만으로 검증하지 않고, **실제 실행 가능한 형태**(deploy된 `~/.opal/bin/opal-cli` 또는 소스 `run.sh`/`console.sh`를 직접 실행)로 검증한다.
- 실 `~/.opal/console.config.json`을 파괴하지 않도록 `OPAL_HOME`을 mktemp 디렉토리로 오버라이드하여 격리 실행한다.
- install 연동(F-003)은 정적 검사(코드 존재+실패 격리)로 검증하고, scan 자체 동작은 기능 테스트로 검증한다.

---

## 1. RED-first 트랙 판정

### 판정 결과: **RED-first 적용**

### 근거 (red-first.md §1.5 자동분기)

| 요소 | 트랙 분류 | 근거 |
|------|----------|------|
| F-001 마커 탐색→scan_root 도출 | **RED-first 강제** | 비즈니스 로직 — 도출 규칙·OPAL 홈 제외가 self-confirming 위험(약한 테스트로 통과 유도 가능) |
| F-002 머지 로직 (보존/추가/dedup/prune/손상 비파괴) | **RED-first 강제** | 비즈니스 로직 + 데이터 보존 계약(C-3) — 유실 리스크 P0 |
| F-001 출력 계약(C-6) | **RED-first 강제** | API 계약(도구 JSON 출력) — 스키마 불일치 시 후속 소비 오류 |
| F-003 install 연동 | 구현-후 정적 검증 | 배선(wiring) — 정적 grep(코드 존재+실패 격리)으로 충분 |
| F-004 start 가드 | 구현-후 정적 검증 | 안내 출력 — 행위 불변 |
| F-005 config.py 독스트링 | 구현-후 정적 검증 | 문서(독스트링) — 로직 불변 |
| F-006 windows.ps1 | 구현-후 정적 검증 | 설정 스크립트 — 실기 검증 제외(코드 리뷰) |

**종합**: 지배적 리스크(F-002 머지 데이터 보존·F-001 도출 규칙)가 self-confirming 위험 높은 비즈니스 로직 + API 계약이므로 **RED-first 트랙 적용**. red-first.md §1.5 "모호하면 RED-first 기본(안전측)"에도 부합. 구조/문서성 요구(F-003~F-006)는 동일 테스트 파일 내 정적 TC로 흡수한다.

### 트랙 운용 규칙 (red-first.md)
- [MUST] §1 RED→GREEN: `scripts/tests/test_console_scan.sh`의 기능 계약 TC(TS-001~010)를 **구현(Step 1) 이전에 작성·실행하여 FAIL(exit≠0) 증거 기록** 후 GREEN 진입.
- [MUST] §2 작성자≠구현자: RED 테스트는 `opal-test-agent`(mode: red)가 작성, EXECUTE 구현은 `opal-task-agent`/`opal-be-agent`가 담당(분리).
- [MUST] §3 테스트 불변성: GREEN/fix 루핑 중 RED 테스트 파일 수정 금지(약화·삭제 금지).
- §4 공개 인터페이스 검증: 내부 함수가 아닌 **관찰 행위**(stdout JSON, exit code, 생성된 config 파일 내용)로 검증.
- §6 STATE: RED는 EXECUTE 내부 서브스텝으로 흡수(별도 STATE 행 없음, opds 10행 보존).

> PLAN 워커(본 문서 작성자)는 TEST-SCENARIO만 작성하며 RED 테스트 **코드**는 작성하지 않는다(§2 작성자≠구현자 — RED 코드는 opal-test-agent 담당).

---

## 2. 테스트 환경 및 격리

| 항목 | 값 |
|------|-----|
| 실행 하네스 | `scripts/tests/test_version_stamp.sh` 패턴 (pass/fail/skip 카운터, exit 0/1, bash 3.2 호환) |
| 테스트 파일 | `scripts/tests/test_console_scan.sh` (신규) |
| 실행 명령 | `bash scripts/tests/test_console_scan.sh` |
| 격리 | `SCRATCH=$(mktemp -d)`; `OPAL_HOME=$SCRATCH/.opal`; scratch 프로젝트 트리 생성 |
| 대상 실행체 | `opal/tools/opal-cli/run.sh console scan ...` (또는 배포 `~/.opal/bin/opal-cli`) — OPAL_HOME override로 실 config 비파괴 |
| 회귀 | `bash scripts/tests/test_version_stamp.sh` (install-mac.sh 회귀 0) |

### Scratch 픽스처 (예시 트리)
```
$SCRATCH/ws/proj-a/.opal/AGENT.md      # 유효 프로젝트 (scan_root=$SCRATCH/ws)
$SCRATCH/ws/group/proj-b/.opal/AGENT.md # 중첩 프로젝트 (scan_root=$SCRATCH/ws/group)
$SCRATCH/ws/node_modules/x/.opal/AGENT.md # exclude — 발견 금지
$SCRATCH/.opal/AGENT.md                 # OPAL 홈 마커 — 제외 대상 (H-2)
```

---

## 3. 시나리오 상세 (S-N ↔ TS-N ↔ 리스크 가설)

| S-ID | 시나리오 | 관련 TS | 가설 | 유형 | 트랙 | 기대 결과 | 결과 |
|------|---------|---------|------|------|------|----------|------|
| S-1 | config 부재 상태 scan → 생성 | TS-001, TS-004 | H-3 | 기능 | RED | 파일 생성 + stdout `{"ok":true,"created":true,"added_roots":[...],"projects_found":N}` | PASS — TC-S1 확인, `ok:true,created:true` 및 실제 소스 실행에서도 동일 스키마 관찰 |
| S-2 | 마커 프로젝트의 부모가 scan_roots에 포함 | TS-002 | H-1 | 기능 | RED | `$SCRATCH/ws`, `$SCRATCH/ws/group`가 scan_roots에 포함 | PASS — TC-S2 확인 |
| S-3 | 수기 root 보존 + --prune 대조 | TS-006, TS-008 | H-1, H-5 | 기능 | RED | 미지정: 수기 root 유지+신규 추가 / `--prune`: 미발견 수기 root만 제거 | PASS — TC-S3a, TC-S3b 확인 |
| S-4 | JSON 출력 계약 스키마 준수 | TS-004, TS-007 | H-3 | 산출물 검사 | RED | stdout 1줄 JSON에 4키 존재, added_roots 중복 없음 | PASS — TC-S4 확인 |
| S-5 | OPAL 홈 마커 제외 | TS-003 | H-2 | 기능 | RED | base=$SCRATCH scan 시 `$SCRATCH`(OPAL 홈)가 scan_root로 추가되지 않음 | PASS — TC-S5 확인 |
| S-6 | 전체 디스크 스캔 금지 (정적) | TS-005 | H-4 | 산출물 검사 | 정적 | scan action에 `-maxdepth`·exclude `-prune` 존재 | PASS — TC-S6 확인 |
| S-7 | 손상 config 비파괴 | TS-010 | H-6 | 기능 | RED | 손상 JSON 존재 시 `{"ok":false,"error":...}` + 원본 바이트 불변 | PASS — TC-S7 확인 |
| S-8 | install 연동 존재 + 실패 격리 (정적) | TS-011 | H-7 | 산출물 검사 | 정적 | `install_dashboard`에 `console scan` + `\|\|`(실패 격리) grep 매칭 | PASS — TC-S8 확인 |
| S-9 | 미지정 키 보존 | TS-009 | H-1 | 기능 | RED | 사용자 추가 키·scan_depth·exclude가 머지 후 보존 | PASS — TC-S9 확인 |
| S-10 | 중복 root dedup | TS-007 | H-1 | 기능 | RED | 이미 존재하는 root 재발견 시 중복 미추가, added_roots 비어있음 | PASS — TC-S10 확인 |
| S-11 | start 가드 안내 (정적) | TS-012 | - | 산출물 검사 | 정적 | `start)` 브랜치에 config 부재 안내+scan 안내 문구 존재 | PASS — TC-S11 확인 |
| S-12 | config.py 독스트링 정정 (정적) | TS-013 | - | 산출물 검사 | 정적 | 독스트링에 `console scan`+install 서술, "install 단계에서 수행" 제거, load_config 로직 diff 0 | PASS — TC-S12, TC-S12b 확인 (docstring 정정 + 로직 불변) |
| S-13 | windows.ps1 등가 로직 (정적) | TS-014 | - | 산출물 검사 | 정적 | `Install-Dashboard`/헬퍼에 마커 탐색+config 머지+실패 격리 존재 | PASS — TC-S13 확인 |
| S-14 | 회귀 — 기존 console 액션·install 무변경 | - | - | 회귀 | 정적/기능 | `test_version_stamp.sh` PASS, start/stop/status/open 무변경 | PASS — TC-S14 확인 + `test_version_stamp.sh` 11/11 PASS 별도 실행 확인 |

---

## 4. RED 단계 기대 (구현 전 실행)

| TC 그룹 | RED 시점 기대 |
|---------|--------------|
| (가) 기능 계약 TS-001~010 (S-1~S-10, RED 트랙) | **FAIL** — scan action 미구현 (증거: exit≠0 로그) |
| (나) 정적/구조 TS-011~014 (S-8·11~13) | 구현 전 **FAIL**(대상 코드 미삽입) → 구현 후 PASS |
| 회귀 test_version_stamp.sh | RED 시점에도 **PASS**(무관 변경) |

---

## 5. GREEN 완료 기준 (TEST 단계)

- [ ] `bash scripts/tests/test_console_scan.sh` → 전체 PASS, exit 0
- [ ] TS-001~TS-014 전부 PASS
- [ ] `bash scripts/tests/test_version_stamp.sh` → PASS (회귀 0)
- [ ] 실 `~/.opal/console.config.json` 미변경(격리 확인)
- [ ] RED 테스트 파일이 GREEN 루핑 중 수정되지 않음 (red-first.md §3)
- [ ] (배포검증) `~/.opal/bin/opal-cli console scan <scratch>` 실제 실행으로 config 생성·머지 관찰 (deploy-artifact-verification-lesson)

---

## 6. 커버리지 매트릭스 (요구사항 ↔ 시나리오)

| 요구사항 | AC 요지 | S-ID | TS-ID |
|---------|---------|------|-------|
| TASK F-1 | 생성+`created:true`, 마커 부모→root | S-1, S-2, S-5 | TS-001~005 |
| TASK F-2 | 수기 보존·중복 없이 추가·prune 옵트인 | S-3, S-4, S-9, S-10 | TS-006~010 |
| TASK F-3 | install 후 config 존재, 실패 시 install 정상 종료 | S-8 | TS-011 |
| TASK F-4 | config 부재 start 안내 | S-11 | TS-012 |
| TASK F-5 | 독스트링 실제 경로 서술 | S-12 | TS-013 |
| TASK F-6 | windows 등가 로직 | S-13 | TS-014 |
| TASK F-7 | 신규 테스트 GREEN + 회귀 0 | S-14 + 전체 | TS-001~014 |

---

## 7. TEST 실행 결과

> 실행 일시: 2026-07-10 18:03 (KST) | 실행자: opal-test-agent (mode: short, test_mode: be·CLI)

### 실행 명령 및 집계

| 명령 | 결과 | 상세 |
|------|------|------|
| `bash scripts/tests/test_console_scan.sh` | **PASS** (exit 0) | PASS: 16 \| FAIL: 0 \| SKIP: 0 — TS-001~014 전항목 커버(TC-S1~S14, S12b 포함 16개 TC) |
| `bash scripts/tests/test_version_stamp.sh` | **PASS** (exit 0) | PASS: 11 \| FAIL: 0 \| SKIP: 0 — 회귀 0 확인 |
| 실 `~/.opal/console.config.json` 무변경 확인 | **PASS** | 실행 전/후 mtime 동일(1781504049), md5 동일(10eab0df70c966939fc0d0bd3b28c2af) — OPAL_HOME 격리 실효성 이중 확인 |
| RED 테스트 파일 불변 확인 | **PASS** | `git status --porcelain scripts/tests/test_console_scan.sh` 실행 전/후 모두 `??` (untracked, 신규 상태 그대로) — 워커가 수정하지 않음 |
| `bash -n opal/tools/opal-cli/lib/console.sh` | **PASS** | 문법 오류 없음 |
| `bash -n scripts/install-mac.sh` | **PASS** | 문법 오류 없음 |
| `python3 -c "import ast; ast.parse(...)" dashboard/backend/config.py` | **PASS** | 파싱 오류 없음 |
| (배포검증) `~/.opal/bin/opal-cli console scan <scratch>` | **DEFERRED** | 배포본(`~/.opal/tools/opal-cli/lib/console.sh`)은 install 재배포 전 구버전 — `scan` 서브명령 미존재 확인(`알 수 없는 액션: scan`, exit 1). diff 결과 배포본에 057 변경분(scan 서브명령, v1.3 로그) 미반영 확인. **install 재배포 후속 태스크에서 검증** (배포 경계: 소스 수정 후 install로 배포). 대체 근거: 소스 `opal/tools/opal-cli/run.sh console scan`을 동일 시나리오(마커 프로젝트 1개, OPAL_HOME 격리)로 직접 실행 → `{"ok": true, "created": true, "added_roots": [".../ws"], "projects_found": 1}` (exit 0) + 생성된 config 파일 내용이 계약대로 확인됨 |

### 시나리오 커버리지

S-1~S-14 (TS-001~TS-014) 전체 PASS — §3 표 결과 컬럼 참조.

### 최종 판정

**verdict: PASS**

- §5 GREEN 완료 기준 6개 항목 중 5개 완전 충족, 1개(배포검증)는 DEFERRED로 대체 근거(소스 실행 성공) 확보 — FAIL 아님.
- 핵심 기능(머지 로직, dedup, prune, 손상 비파괴, JSON 계약)과 정적 검증(install 연동, start 가드, docstring, windows.ps1) 전항목 PASS.
- 회귀 0 (test_version_stamp.sh 11/11 PASS).
- 실 설정 파일 비파괴 이중 확인 완료.

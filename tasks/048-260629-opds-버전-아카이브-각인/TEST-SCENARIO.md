# TEST-SCENARIO: 버전을 릴리스 아카이브에 각인 (export-subst)

> 작성일: 2026-06-29 | 입력: PLAN.md (리스크 가설 표 §H-1~H-8), TASK.md (R1~R8)
> 검증 대상: VERSION, .gitattributes, install.sh, update.sh, install-mac.sh, install.ps1, test_version_stamp.sh

## 0. RED-first 트랙 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| **트랙** | **RED-first 강제** | 본 작업은 설치기 동작 변경 — `red-first.md §1.5` "버그 수정(회귀 방지)" + self-confirming 위험 영역(API 실패 시 버전 오염 회귀 방지). 버전 결정은 설치 결과를 좌우하는 핵심 동작 계약. |
| state-tool | `verify --red-check` **ON** | red-first §1.5 — RED-first 트랙은 red-check ON |
| 작성자≠구현자 | 적용 | RED 테스트(`test_version_stamp.sh`)는 opal-test-agent(mode: red)가 작성, EXECUTE 구현 워커와 분리 (red-first §2) |
| 테스트 불변성 | 적용 | GREEN/fix 루핑 중 RED 테스트 수정 금지 (red-first §3) |
| 공개 인터페이스 | 적용 | 검증은 관측 행위로 — `OPAL_VERSION` env 값, `~/.opal/VERSION` 파일 내용, `git archive` 산출 tarball 내용, exit code (red-first §4) |

> **graceful skip 비대상**: 테스트 인프라(bash/git) 존재. 신규 `scripts/tests/test_version_stamp.sh`가 RED 산출물.
> **RED 증거 요건**: Step 1~5 구현 전, `test_version_stamp.sh` 실행 시 각 케이스가 실패(exit≠0)함을 기록한 뒤 GREEN 진입.

---

## 1. 리스크 → 시나리오 매핑 (PLAN 리스크 가설 표 입력)

| 가설 ID | 시나리오 | 검증 계층 |
|---------|---------|----------|
| H-1 (export-ignore 누락) | S-1, S-2 | L2 (실 git archive) |
| H-2 (치환 실패/오치환) | S-1, S-3 | L2 |
| H-3 (placeholder 오인) | S-4, S-7 | L1 (셸 단위) |
| H-4 (API 403 main 오염) | S-5 | L1 (curl stub + 태그 archive) |
| H-5 (git clone describe 폴백) | S-6 | L1 |
| H-6 (런타임 placeholder 표출) | S-8 | L1 (사용처 회귀) |
| H-7 (ps1 순서) | S-9 | L1 (정적/로직) |
| H-8 (시크릿) | S-10 | L1 (스캔) |

---

## 2. 검증 시나리오

### S-1: 태그 archive → 실태그 각인 (L2, 핵심)
- **대응 TS**: TS-003 | **가설**: H-1, H-2
- **유형**: 회귀 테스트 (실 git archive)
- **전제**: scratch git repo에 `VERSION`(`$Format:%(describe:tags)$`) + `.gitattributes`(`VERSION export-subst`) 커밋, `v9.9.9` 태그 부여
- **실행**: `git archive --format=tar v9.9.9 | tar -xO VERSION`
- **기대 결과**: 출력 = `v9.9.9` (정확한 태그, placeholder 아님)
- **실측 사전 확인**: PLAN 작성 중 동일 시나리오로 `v9.9.9` 산출 확인됨

### S-2: VERSION이 export에서 누락되지 않음 (L2)
- **대응 TS**: TS-002 | **가설**: H-1
- **유형**: 산출물 검사
- **실행**: 본 저장소에서 `git check-attr export-subst VERSION` / `git check-attr export-ignore VERSION`
- **기대 결과**: `export-subst: set`, `export-ignore: unspecified` (VERSION이 archive에 포함됨)
- **추가**: `git archive HEAD | tar -t | grep -x VERSION` → VERSION 엔트리 존재

### S-3: HEAD-after-tag archive → git describe 형식 (L2)
- **대응 TS**: TS-004 | **가설**: H-2
- **유형**: 회귀 테스트
- **전제**: 태그 후 커밋 1개 추가
- **실행**: `git archive --format=tar HEAD | tar -xO VERSION`
- **기대 결과**: `v9.9.9-1-g<sha>` 형식 (describe). 실측: `v9.9.9-1-ga3c81a7` 확인됨

### S-4: 작업트리/git clone → placeholder 미치환 (L1+L2)
- **대응 TS**: TS-005, TS-011 | **가설**: H-3
- **유형**: 회귀 테스트
- **실행**: 커밋된 작업트리에서 `cat VERSION` (archive 아님)
- **기대 결과**: `$Format:%(describe:tags)$` (미치환 placeholder) — 설치기 폴백 분기 트리거. 실측 확인됨

### S-5: API 완전 실패(403/차단) 시뮬레이션에서 정확 버전 (L1, 핵심)
- **대응 TS**: TS-022 | **가설**: H-4
- **유형**: 기능 테스트 (curl stub)
- **전제**: `PATH` 앞에 항상 비정상 종료하는 `curl` stub 배치 (또는 `OPAL_VERSION=v9.9.9` 명시로 API 스킵). 태그 archive에서 추출한 mock `OPAL_EXTRACT_DIR/VERSION`=`v9.9.9`
- **실행 대상**:
  - install.sh `adopt_stamped_version` (또는 통합): 추출 디렉토리 VERSION 채택
  - update.sh: `--to v9.9.9` + curl stub → 각인값 채택
- **기대 결과**: `OPAL_VERSION`/`version` = `v9.9.9` (`main` 아님). `~/.opal/VERSION`에 `v9.9.9` 기록
- **반증 조건(이게 실패하면 H-4 미해결)**: 결과가 `main`이면 FAIL

### S-6: git clone(개발자) 경로 → git describe 폴백 유지 (L1)
- **대응 TS**: TS-031 | **가설**: H-5
- **유형**: 회귀 테스트
- **전제**: mock `FRAMEWORK_ROOT`에 placeholder VERSION + `.git` 디렉토리 존재, `OPAL_VERSION` 미설정
- **실행**: install-mac.sh `record_installed_version`(분리 후) 또는 VERSION 기록 블록
- **기대 결과**: `~/.opal/VERSION` = `git describe --tags --always` 값 (placeholder 채택 안 함)

### S-7: placeholder VERSION을 실값으로 오인하지 않음 (L1)
- **대응 TS**: TS-011, TS-021 | **가설**: H-3
- **유형**: 기능 테스트
- **실행**: 4개 설치기 판별 로직에 placeholder(`$Format:%(describe:tags)$`) 입력
- **기대 결과**: 전부 폴백 유지 (`OPAL_VERSION`/`version`/`installed_version` 불변, placeholder 미기록)
- **bash 판별**: `case "$v" in *'$Format:'*) ... ;; esac` / PS `-notlike '*$Format:*'`

### S-8: 루트 VERSION 런타임 직접 사용처 회귀 (L1)
- **대응 TS**: (Step 1 완료 기준) | **가설**: H-6
- **유형**: 회귀 테스트
- **실행**: `grep -rn "VERSION" opal/tools/opal-cli/ scripts/ | grep -v "\.opal/VERSION\|FRAMEWORK_ROOT/VERSION\|extract"` 로 루트 VERSION 직접 읽는 코드 탐색
- **기대 결과**: 루트 `VERSION`을 런타임(`opal-cli --version` 등)이 직접 읽어 표출하는 사용처 없음. 있으면 placeholder 폴백 처리 필요(블로커 보고)

### S-9: install.ps1 추출 후 VERSION 읽기 순서 (L1)
- **대응 TS**: TS-040, TS-041 | **가설**: H-7
- **유형**: 산출물 검사 (정적 + pwsh 가용 시 동적)
- **실행**: install.ps1에서 (a) `$extractDir/VERSION` 읽기가 `tar` 추출(`:259`) 이후·`windows.ps1` 호출(`:286`) 이전에 위치, (b) `-notlike '*$Format:*'` 판별 분기 존재 확인
- **기대 결과**: 추출 후 각인값으로 `$script:OpalVersion` override → `-OpalVersion` 전달. placeholder면 불변

### S-10: 보안 — 시크릿 스캔 + .gitignore (L1)
- **대응 TS**: TS-051 | **가설**: H-8
- **유형**: 보안 테스트
- **실행**: 변경 파일 `git diff`에 토큰/키 패턴 grep (`ghp_`, `AKIA`, `-----BEGIN`, `password=`, base64 키 등). VERSION 내용이 placeholder 외 민감정보 없음 확인. `.gitignore`에 VERSION 누락(=트래킹 의도) 확인
- **기대 결과**: 시크릿 0건, VERSION은 의도적 커밋 대상

---

## 3. 테스트 실행 계층 요약

| 계층 | 범위 | 도구 | 시나리오 |
|------|------|------|---------|
| L1 (단위) | 설치기 셸 함수 판별·기록 로직 | bash + mock 디렉토리 | S-5, S-6, S-7, S-8, S-9, S-10 |
| L2 (통합) | 실 `git archive` 각인 메커니즘 | git (scratch repo) | S-1, S-2, S-3, S-4 |
| L3 (E2E) | 전체 설치 흐름 | (선택, 후속) | — (본 태스크 범위 외; 각인 첫 실효는 v0.6.5 원격 태그) |

> L3 E2E(실제 GitHub release 설치)는 export-subst 첫 실효가 v0.6.5 원격 태그라 본 태스크에서 미실행. 로컬 `git archive` 실측(L2)이 각인 메커니즘을 완전 검증.

---

## 4. RED → GREEN 절차

1. **RED**: opal-test-agent(mode: red)가 `scripts/tests/test_version_stamp.sh` 작성 (S-1~S-10 케이스). Step 1~5 구현 전 실행 → 실패(exit≠0) 증거 기록.
   - 단, S-1~S-4(git archive)는 Step 1(VERSION+.gitattributes) 완료 후 GREEN — RED 시점엔 VERSION 부재로 실패.
   - S-5~S-9(설치기)는 Step 2~5 구현 전 폴백 미전환 상태로 실패.
2. **GREEN**: Step 1~5 구현 후 `bash scripts/tests/test_version_stamp.sh` → 전체 exit 0.
3. **테스트 불변**: GREEN 루핑 중 test_version_stamp.sh 수정 금지 (red-first §3).

---

## 5. 통과 기준 (Definition of Done)

- [ ] S-1~S-4: 로컬 git archive 3경로 각인 정확 (태그→실태그/HEAD-after-tag→describe/작업트리→placeholder)
- [ ] S-2: `check-attr export-subst`=set, export-ignore=unspecified
- [ ] S-5: API 실패 시뮬레이션에서 4종 설치기 모두 `main` 아닌 정확 태그
- [ ] S-6: git clone 경로 git describe 폴백 유지
- [ ] S-7: placeholder 미오인 (전 설치기 폴백)
- [ ] S-8: 루트 VERSION 런타임 직접 사용처 없음 (또는 폴백 처리)
- [ ] S-9: install.ps1 추출 후 읽기 + placeholder 판별
- [ ] S-10: 시크릿 0건
- [ ] bash 3.2 호환 (mac 기본 bash) — 연관 배열·mapfile 미사용
- [ ] `test_version_stamp.sh` exit 0 (TS-050)

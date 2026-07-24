# TEST SCENARIO: 워크스페이스 Git 일괄 동기화

> 작성일: 2026-07-02 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> 트랙: **RED-first** (git 판정 로직 = 비즈니스 로직, self-confirming 위험 높음 — `red-first.md §1.5`)

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | git_sync_tool.py — dirty 무손실 | dirty 저장소가 pull/조작되어 작업트리·HEAD 변경 | P0 | L2 | S-16 |
| H-2 | git_sync_tool.py — diverged 무손실 | ff-only가 diverged를 병합/pull하여 HEAD 이동·머지커밋 생성 | P0 | L2 | S-17, S-18 |
| H-3 | 판정 순서 (no-upstream→detached→dirty→fetch→diverged) | 순서 오류 시 no-upstream에서 `@{u}` 참조가 diverged로 흘러 예외/오분류 | P1 | L2 | S-2~S-6 |
| H-4 | diverged 컬럼 매핑 (left=behind/right=ahead) | 좌/우 반전 → behind-only(ff 가능)를 diverged로 오판 | P1 | L2 | S-1, S-3 |
| H-5 | ff-only pull 정책 | non-ff 시 예외 미처리로 크래시 또는 부분 조작 잔재 | P1 | L2 | S-18 |
| H-6 | JSON 계약 | ok/repositories/summary/error 필드 누락·타입 불일치 → 스킬 파싱 실패 | P1 | L1 | S-7 |
| H-7 | 대상 결정 3분기 | workspace 유무·단일 루트 분기 오판 → 대상 오순회/누락 | P1 | L2 | S-9, S-10, S-11 |
| H-8 | 승인 게이트 | 문제 저장소에 승인 없이 자율 조치 (헌법 위반) | P0 | L1 | S-13 |
| H-9 | git 버전 | git 2.22 미만서 rev-list --left-right --count 미지원 | P2 | L1 | S-19 |
| H-10 | install 등록 | chmod 블록 누락·오위치 → run.sh 실행 권한 없음 | P1 | L2 | S-14, S-15 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터 (git fixture)

> DB가 아닌 git 저장소 fixture. 임시 디렉토리에 로컬 bare remote 1개 + 상태별 clone 다수를 구성한다. seed는 셸 스크립트(fixture builder)로 생성.

| fixture 저장소 | 상태 | 구성 방법 | 출처 |
|---------------|------|----------|------|
| `repo_behind` | clean, behind-only (원격이 N커밋 앞섬) | clone 후 remote에 추가 커밋 push, 로컬은 fetch 전 | fixture builder |
| `repo_current` | clean, already-current (원격==로컬) | clone 직후 그대로 | fixture builder |
| `repo_dirty` | dirty (작업트리 미커밋 변경) | clone 후 파일 수정, 커밋 안 함 | fixture builder |
| `repo_diverged` | diverged (ahead>0 AND behind>0) | 로컬 커밋 1 + remote 커밋 1 (양쪽 갈림) | fixture builder |
| `repo_detached` | detached HEAD | clone 후 `git checkout <sha>` | fixture builder |
| `repo_noupstream` | upstream tracking 없음 | clone 후 upstream 없는 새 로컬 브랜치 체크아웃 | fixture builder |
| `repo_fetchfail` | fetch 실패 (원격 URL 무효) | clone 후 origin URL을 존재하지 않는 경로로 변경 | fixture builder |
| `workspace/` (컨테이너) | 위 저장소들의 부모 디렉토리 | 위 clone들을 직속 자식으로 배치 | fixture builder |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (실행) | Then (검증) |
|---------|------------------|------------|------------|
| S-1 | repo_behind (behind N) | `sync workspace/` | status=updated, pulled_commits=N, HEAD 전진 |
| S-2 | repo_dirty | `sync workspace/` | status=skipped, reason=dirty |
| S-3 | repo_diverged | `sync workspace/` | status=skipped, reason=diverged |
| S-4 | repo_detached | `sync workspace/` | status=skipped, reason=detached |
| S-5 | repo_noupstream | `sync workspace/` | status=skipped, reason=no-upstream, upstream=null |
| S-6 | repo_fetchfail | `sync workspace/` | status=failed, reason=fetch-failed |
| S-7 | workspace 전체 | `sync workspace/` | 유효 JSON + ok/command/workspace/repositories/summary/error 필드 |
| S-8 | repo_current | `sync workspace/` | status=already-current, pull 미실행 |
| S-16 | repo_dirty | `sync` 실행 전후 HEAD·porcelain 스냅샷 | 실행 전후 완전 불변 |
| S-17 | repo_diverged | `sync` 실행 전후 HEAD 스냅샷 | HEAD 불변, 머지커밋 미생성 |
| S-18 | repo_diverged | `sync` 실행 | pull 미실행(ff-only가 diverged 병합 안 함) |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-7: JSON 출력 계약 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | git_sync_tool.py JSON 출력 스키마 (PLAN §3.1.2(e)) |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | workspace fixture에 대해 sync 실행, stdout 파싱 |
| 기대 결과 | 유효 JSON. `ok`(bool)·`command`("sync")·`workspace`(str)·`repositories`(list)·`summary`(total/updated/skipped/failed)·`error` 필드 존재. 각 repo 객체에 name/branch/upstream/status/reason/ahead/behind/prev_head/new_head/pulled_commits |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-13: 승인 게이트 무자율 (정적 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | git_sync_tool.py + opal-workspace-sync/SKILL.md — 자율 조치 코드 부재 |
| 계층 | L1 |
| 실행 방식 | M1 (grep 정적 검사) |
| 조건 | `git_sync_tool.py`에 대해 `git stash|git rebase|--force|git push|git commit|git reset --hard` grep. SKILL.md에서 조치가 "제안(AskUserQuestion)"에만 존재하고 자동 실행 로직 부재 확인 |
| 기대 결과 | git_sync_tool.py 조작 명령 grep 0건. SKILL.md 조치 문구가 승인 게이트 이후에만 위치 |
| 도구 | grep |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-12: 5섹션 보고서 규격 (정적 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (보고서 정합) |
| 대상 | opal-workspace-sync/SKILL.md — 5섹션 보고서 규격 명시 |
| 계층 | L1 |
| 실행 방식 | M1 (문서 검사) |
| 조건 | SKILL.md STEP 3에서 요약헤더/✅최신화/⏭️Skip/❌실패/📋조치제안 5섹션 + summary 집계 + reason별 제안 카탈로그 존재 확인 |
| 기대 결과 | 5섹션 모두 규격에 명시, 사유 5종별 제안조치 매핑 존재 |
| 도구 | grep/문서 검사 |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-19: git 버전 요구사항 명시 (정적 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | git_sync_tool.py @header + SKILL.md — git 2.22+ 명시 |
| 계층 | L1 |
| 실행 방식 | M1 (문서 검사) |
| 조건 | git_sync_tool.py @header description 또는 SKILL.md에 "git 2.22+" 문구 grep |
| 기대 결과 | git 2.22+ 요구사항 명시 존재 |
| 도구 | grep |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### L2. 프로세스 통합 (자동, 실 git 저장소 fixture)

#### S-1: clean + behind-only → ff-pull 성공

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 (컬럼 매핑 정합) |
| 대상 | behind-only 저장소의 ff-only pull |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_behind (원격이 N커밋 앞, 로컬 clean) |
| 기대 결과 | status=updated, pulled_commits=N, HEAD가 원격 tip으로 전진, behind=N/ahead=0 정확 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-2: dirty → skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | dirty 저장소 skip 판정 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_dirty (작업트리 미커밋 변경) |
| 기대 결과 | status=skipped, reason=dirty |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-3: diverged → skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-4 |
| 대상 | diverged 저장소 skip 판정 (ahead>0 AND behind>0) |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_diverged |
| 기대 결과 | status=skipped, reason=diverged, ahead>0 AND behind>0 정확 계산 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-4: detached HEAD → skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | detached HEAD 저장소 skip |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_detached |
| 기대 결과 | status=skipped, reason=detached |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-5: no-upstream → skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | upstream 없는 저장소 skip (판정 순서상 최우선) |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_noupstream |
| 기대 결과 | status=skipped, reason=no-upstream, upstream=null (예외 없이) |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-6: fetch-failed → failed

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | fetch 실패 저장소 분류 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_fetchfail (원격 URL 무효) |
| 기대 결과 | status=failed, reason=fetch-failed, 도구 크래시 없이 계속 순회 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-8: already-current → pull 미실행

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 이미 최신 저장소 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_current (원격==로컬) |
| 기대 결과 | status=already-current, pulled_commits=0, HEAD 불변 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-9: 대상 결정 — (프로젝트)/workspace 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 도구 순회 대상 = workspace 직속 자식 git |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | workspace/ 아래 여러 clone (직속 자식) |
| 기대 결과 | 직속 자식 중 .git 보유 저장소 전부가 repositories에 포함, 1단계만 순회(중첩 미포함) |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-10: 대상 결정 — 단일 git 루트

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 경로 자체가 git 루트일 때 그 1개 처리 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | path/.git 존재하는 단일 저장소 경로 전달 |
| 기대 결과 | repositories 길이 1, 해당 저장소 처리 결과 반환 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-11: 대상 결정 — 질의 분기 (스킬)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | opal-workspace-sync SKILL.md — workspace 없고 단일 루트 아니면 AskUserQuestion 질의 |
| 계층 | L2 |
| 실행 방식 | M1 (문서 검사 — 스킬 프로세스 STEP 1 명시) |
| 조건 | SKILL.md STEP 1 3분기 로직 확인 |
| 기대 결과 | 3번째 분기(질의)가 AskUserQuestion으로 정의됨 |
| 도구 | 문서 검사 |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-14: install 후 도구 배포 + 실행 권한

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | install-mac.sh git-sync-tool chmod 블록 |
| 계층 | L2 |
| 실행 방식 | M1 (install 실행 후 파일 검사) |
| 조건 | install-mac.sh 실행 (또는 chmod 블록 dry 확인) |
| 기대 결과 | `~/.opal/tools/git-sync-tool/run.sh` 존재 + `-x` (실행 가능) |
| 도구 | bash test -x |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-15: install 후 스킬 배포

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | 스킬 자동 순회 배포 |
| 계층 | L2 |
| 실행 방식 | M1 (install 실행 후 파일 검사) |
| 조건 | install-mac.sh 실행 |
| 기대 결과 | `~/.opal/skills/opal-workspace-sync/SKILL.md` 존재 (변경이력 strip 확인) |
| 도구 | bash test -f |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-16: dirty 무손실 (P0 안전)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | dirty 저장소 실행 전후 불변 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture, before/after 스냅샷) |
| 조건 | repo_dirty. 실행 전 `git rev-parse HEAD` + `git status --porcelain` 스냅샷 |
| 기대 결과 | 실행 후 HEAD·porcelain 완전 동일 (작업트리·커밋 미조작) |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-17: diverged 무손실 (P0 안전)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | diverged 저장소 실행 전후 HEAD 불변·머지커밋 미생성 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture, before/after 스냅샷) |
| 조건 | repo_diverged. 실행 전 HEAD + 커밋 그래프 스냅샷 |
| 기대 결과 | 실행 후 HEAD 불변, 머지커밋 미생성, 커밋 수 불변 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-18: ff-only가 diverged를 병합하지 않음 (P0 안전)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-5 |
| 대상 | ff-only 정책이 diverged에서 pull을 실행하지 않음 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + git fixture) |
| 조건 | repo_diverged. sync 실행 |
| 기대 결과 | status=skipped(reason=diverged)로 pull 자체 미실행. non-ff pull 시도 없음, 예외/크래시 없음 |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

> 해당 없음 — 본 태스크는 CLI 도구·문서 스킬로 FE 화면·사용자 플로우가 없다. 모든 검증이 M1(pytest/grep/문서·install 검사)로 자동화 가능. 실제 원격(GitHub) 대상 스모크는 CLOSE 후 캡틴이 pointail 워크스페이스로 선택적 확인(참고용, 게이트 아님).

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| AC#1 (clean+ff pull) | H-4 | L2 | S-1 | _{EXECUTE 워커가 채움}_ | behind-only → updated |
| AC#1 (5종 skip) | H-3 | L2 | S-2,S-3,S-4,S-5,S-6 | _{채움}_ | dirty/diverged/detached/no-upstream/fetch-failed |
| AC#1 (JSON 계약) | H-6 | L1 | S-7 | _{채움}_ | 필드 유효성 |
| AC#1 (already-current) | H-6 | L2 | S-8 | _{채움}_ | pull 미실행 |
| AC#2 (대상결정 3분기) | H-7 | L2 | S-9,S-10,S-11 | _{채움}_ | workspace/단일루트/질의 |
| AC#2 (5섹션 보고서) | H-7 | L1 | S-12 | _{채움}_ | 문서 규격 |
| AC#2 (승인 게이트 무자율) | H-8 | L1 | S-13 | _{채움}_ | grep 자율조치 0건 |
| AC#3 (dirty 무손실) | H-1 | L2 | S-16 | _{채움}_ | HEAD·작업트리 불변 |
| AC#3 (diverged 무손실+ff-only) | H-2,H-5 | L2 | S-17,S-18 | _{채움}_ | 머지커밋 미생성·pull 미실행 |
| AC#4 (도구/스킬 배포) | H-10 | L2 | S-14,S-15 | _{채움}_ | install 후 -x·존재 |
| (부가) git 2.22+ 명시 | H-9 | L1 | S-19 | _{채움}_ | 문서 명시 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff | ✅ Pass | `ruff check` All checks passed |
| 2 | 컴파일/타입 | py_compile | ✅ Pass | 구문 오류 없음 |
| 3 | 포맷터 | ruff | ✅ Pass | 위반 없음 |
| 4 | @header 검증 | grep | ✅ Pass | git_sync_tool.py @header 6필드 + git 2.22+·보정사유·자율조치금지 명시 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | ✅ Pass | 토큰/경로 하드코딩 0건 ($HOME 기반) |
| 2 | .gitignore 확인 | ✅ Pass | fixture는 pytest tmp_path 사용 — 커밋 대상 아님 |
| 3 | 자율 조치 코드 부재 (grep stash/rebase/--force/push/commit) | ✅ Pass | git_sync_tool.py 실행 코드 0건 (히트는 @header 설명문뿐) (H-8) |
| 4 | subprocess shell injection 부재 | ✅ Pass | 인자 리스트 방식, `shell=True` 0건, cwd 격리 |

## 7. 판정

**All Pass — 기능 13/13 PASS(PM 재현), 정적 S-11/12/13/19 SKILL.md 검증, 품질(ruff)·보안(시크릿/자율조치/injection) 전항 Pass, install-mac.sh 회귀 정합.**

### 결과 요약 (시나리오별)

| 시나리오 | 결과 | 근거 |
|---------|------|------|
| S-1~S-8, S-16~S-18 (git 기능·무손실) | ✅ Pass | pytest 13/13 (test_git_sync_tool.py) |
| S-9, S-10 (대상 결정 순회) | ✅ Pass | pytest (직속자식/단일루트 케이스) |
| S-11 (질의 분기) | ✅ Pass | SKILL.md STEP 1 line 45 AskUserQuestion 분기 |
| S-12 (5섹션 보고서) | ✅ Pass | SKILL.md STEP 3 ①~⑤ (line 109-129) |
| S-13 (승인 게이트 무자율) | ✅ Pass | SKILL.md STEP 4 [MUST] line 137 + 도구 grep 0건 |
| S-14, S-15 (install 배포) | ✅ Pass | install 재실행 → `~/.opal/tools/git-sync-tool/run.sh` -x, `~/.opal/skills/opal-workspace-sync/SKILL.md` 존재 |
| S-19 (git 2.22+ 명시) | ✅ Pass | git_sync_tool.py @header + SKILL.md line 64 |
| **S-20 (registry discoverability)** | ✅ Pass | opal-skills-registry.json 등록 → 런타임 `skill-registry match "opws"` found:true (배포 갭 수정 후 추가 검증) |

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 git fixture 사용 — grep 확인 대상)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (git fixture 8종)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-10 전부 매핑)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 해당 없음 명시 (FE·사용자 플로우 부재)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 없음 → M2 의무 트리거 비해당

## 변경이력

| 버전 | 작성일 | 변경내용 |
|------|--------|---------|
| v1.0 | 2026-07-02 | 초기 작성 — RED-first 트랙, git fixture 8종, S-1~S-19 시나리오, H-1~H-10 매핑, 무손실(S-16~18) P0 안전 시나리오 (052) |

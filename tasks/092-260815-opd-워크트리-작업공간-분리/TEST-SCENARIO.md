# TEST SCENARIO: 태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)

> 작성일: 2026-08-15 | 상태: **실행 완료**
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표(H-1~H-16) 기반
> 작성자≠구현자: PLAN 워커(opal-plan-agent)와 분리된 PM이 작성 (self-confirming 방지)

## 0. 트랙 판정 및 실행 방식 면제 근거

### 0.1 RED-first 트랙 판정 (`harness/red-first.md` §1.5)

변경 영역이 혼합이므로 영역별로 분기한다. **판단 주체는 PM**이며, 모호한 경우 안전측(RED-first)을 택했다.

| 변경 영역 | 해당 Step | 트랙 | 근거 |
|-----------|----------|------|------|
| `worktree_tool.py` (도구 CLI 신설) | Step 2~5 | **RED-first 강제** | red-first §1.5 "비즈니스 로직" + "API 계약"(도구 JSON 응답 계약) |
| `state_tool.py` (`--worktree` 추가) | Step 7~8 | **RED-first 강제** | red-first §1.5 "API 계약" — 기존 소비자가 있는 CLI 인터페이스 변경 |
| 참조 문서·스킬·설정 (하네스·dispatch·SKILL.md·docs·code-scan.json·install) | Step 9~17 | **구현 후 시나리오 검증** | red-first §1.5 "설정·문서" |
| 실환경 검증 (revup·mams) | Step 19~20 | 검증 전용 | 구현 산출물의 실환경 확인 — 트랙 분기 대상 아님 |
| `UV_CACHE_DIR` 이전 | Step 21 | 검증 전용 (비가역) | 캡틴 로컬 환경 변경 — 코드 산출물 아님 |

**RED 작성 주체**: `opal-test-agent` (mode: red) — EXECUTE 진입 전. `harness/red-first.md` §2 "작성자≠구현자".
**테스트 불변성**: GREEN/fix 루핑 중 RED 테스트 파일 수정 금지 (§3). 위반 시 블로커.
**state-tool 연동**: RED-first 트랙이므로 EXECUTE 진입 전 `state-tool verify --red-check` 게이트를 호출한다.

### 0.2 M2(E2E 자동화) 의무 트리거 — **면제**

`test-scenario-guide.md` §Step 3-b의 M2 의무 트리거 3종을 본 태스크 변경 영역과 대조한다.

| 트리거 영역 | 본 태스크 포함 여부 | 판정 |
|------------|------------------|------|
| FE 화면/컴포넌트 | **미포함** — 변경 파일에 `dashboard/frontend/` 없음 | 면제 |
| 인증/인가 | **미포함** — 토큰·세션·권한 코드 없음 | 면제 |
| 외부 API 연동 | **미포함** — 네트워크 호출 없음(로컬 git subprocess만) | 면제 |
| (참고) API 엔드포인트 | **미포함** — HTTP 엔드포인트 아닌 CLI 도구 | BE API M2 트리거 미발동 |

→ **M2 시나리오 없음이 정당하다.** 변경 영역은 CLI 도구(비즈니스 로직) + 문서·설정 단독이며, `test-scenario-guide.md` "DB 스키마·비즈니스 로직 단독 변경은 M2 면제" 조항에 해당한다.

### 0.3 테스트 스택 (`test-tool resolve` 결과)

| tier × scope | 도구 | 근거 |
|--------------|------|------|
| unit × be | **pytest** | `test-tool resolve` 응답 `tiers.unit.be.unit[0].name` |
| unit × be (lint) | ruff | 동 응답 `tiers.unit.be.lint[0].name` |
| integration × be | pytest (실 자원, mock 금지) | 동 응답 `tiers.integration.be.api_db[0]` — 본 태스크는 DB 대신 **실 git 저장소**를 실 자원으로 사용 |

> 본 태스크의 "실 자원"은 DB가 아니라 **임시 git 저장소**다. mock/patch를 쓰지 않고 실제 `git init`/`git worktree add`를 수행하는 fixture로 L2를 구성한다(헌법 §4 "Don't fake it").

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표에서 이관. 시나리오 컬럼을 확정한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-005 `state_tool.py cmd_init` | `--worktree` 미지정 시 `state.json`에 `worktree` 키가 생성되면 안 됨 | P0 | L1 + L2 | S-1, S-2 |
| H-2 | F-003·F-004·F-006 참조 문서 3종 | "pilot 10종 SKILL.md diff 0"(TASK C-9) | P0 | L1 | S-3 |
| H-3 | F-002 `create` 유형 A(multi-repo) | `repos[]` N개 각각 worktree 생성 + 레이아웃이 메인과 동일 | P0 | L2 + L3 | S-4, S-18 |
| H-4 | F-002 `create` 유형 B(monorepo) | `--no-checkout`→`sparse-checkout init --cone`→`set`→`checkout` 순서 | P0 | L2 + L3 | S-5, S-19 |
| H-5 | F-008 `remove` 3중 가드 | dirty/unpushed/미머지 각각 **고유 에러 코드**로 거부 | P0 | L2 | S-6, S-7, S-8, S-9, S-10 |
| H-6 | F-007 `ensure_gitignore_entry()` | 2회 실행 시 중복 0행 + 이미 있으면 **바이트 무변경** | P0 | L2 | S-11 |
| H-7 | F-002 `create` 롤백 (DEC-2) | M번째 실패 시 자기 생성물 전량 회수 (재실행 차단 방지) | P1 | L2 | S-12 |
| H-8 | F-002 base-ref 동결 (DEC-3) | `remove` 판정이 `create` 시점 base와 동일 (결정론) | P1 | L2 | S-13 |
| H-9 | F-001 `validate_worktree_config()` | 필수 키 누락·`layout` 무효값·`repos[]` 경로 이탈 3종이 각각 다른 에러 코드 | P1 | L1 | S-14 |
| H-10 | F-002 배포 (`install-mac.sh`) | `run.sh` 실행 권한은 개별 chmod 블록이 있어야 부여됨 | P1 | L2 | S-15 |
| H-11 | F-005 STATE.md 렌더 | `--worktree` 지정 시에도 STATE.md 렌더 결과 현행 동일 | P1 | L2 | S-2 |
| H-12 | F-009(b) 볼륨 진단 | 캐시·프로젝트 볼륨 불일치 시 **경고만, 차단 금지** | P2 | L1 | S-16 |
| H-13 | F-003 하네스 § 번호 삽입 | 신규 절을 `§3`으로 넣으면 전역 `§N` 인용이 dangling | P1 | L1 | S-17 |
| H-14 | F-009(a) `UV_CACHE_DIR` 이전 | 비가역 로컬 환경 변경 — 실패 시 mams 개발 환경 정지 | P0 | L3 | S-20 |
| H-15 | F-002 lazy setup (TASK C-7) | `create`는 `setup[]`을 **실행하지 않고 열거만** | P2 | L2 | S-21 |
| H-16 | F-002 동시 슬롯 경고 (DEC-6) | 슬롯 2개 이상 시 경고 출현 + **차단하지 않음** | P2 | L2 | S-22 |
| **H-17** | F-004·F-006 **파이프라인 접합** | `--wt` → task-process 스텝 4.5 훅 → `worktree-tool create` → `state-tool init --worktree` 관통 계약. **훅이 create를 호출하지 않게 접합돼도 S-1~S-23이 전건 PASS**하는 공백 | **P0** | L2 | **S-24** |
| **H-18** | F-002 `status` + F-008 CLOSE 안내 | `status`가 `remove`와 동일 판정을 보고하되 **거부하지 않는** 계약. CLOSE "머지 대기" 안내가 `status` 출력을 근거로 하는 계약 | P1 | L2 | S-25 |
| **H-19** | F-002 config 부재·무효 | `.opal/worktree.json` 부재 시 `CONFIG_NOT_FOUND` + **부수효과 0**, 깨진 JSON은 `CONFIG_INVALID_JSON`. 실사용자가 가장 먼저 만나는 경로 | P1 | L2 | S-26 |
| **H-20** | F-002 중복 생성 거부 | 살아 있는 슬롯에 동일 태스크 번호 재실행 시 거부 + 기존 worktree·브랜치·메타 **무손상**. H-7(롤백 후 재실행 허용)의 **반대 방향** | P1 | L2 | S-27 |
| **H-21** | F-002 메타 부재 경로 | 슬롯 없이 `remove`/`status` 호출 시 예외로 죽지 않고 `META_NOT_FOUND` 보고. CLOSE 경로에서는 **no-op 비차단** | P2 | L2 | S-28 |
| **H-22** | F-002 `remove` 정리 범위 + `create` 재생성 (DEC-7) | `remove` 후 슬롯 루트 잔존 금지 + 같은 번호 재생성 성공(브랜치 재사용) + `list`·`create` 슬롯 판정 일치. 위반 시 **재작업 영구 차단** | **P0** | L2 | S-29 |
| **목표** | 태스크 전체 (TASK §작업 목표) | "여러 태스크를 격리된 작업공간에서 동시 수행" — 2슬롯이 서로 간섭 없이 독립 편집 가능 | P0 | L2 + L3 | **S-23**, **S-18**, **S-24** |

> **iteration 2 추가분 (H-17~H-20)**: 목표-커버 게이트 iteration 1에서 `opal-evaluator-agent`가 gaps G-1·G-4·G-5·G-6으로 지적한 누락 가설이다. 게이트 루프가 "있어야 할 시나리오가 빠졌는지"를 잡아낸 결과이며(`scenario-gate.md` §1 070 사건 대응), PLAN §리스크 가설 표에는 없던 항목을 Producer가 추가했다.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크는 DB를 사용하지 않는다. "테이블" 열은 **실 자원 유형**으로 해석한다(git 저장소·설정 파일·환경). 모든 칸을 채운다.

| 테이블(실 자원) | 식별자 | 상태 | 출처 |
|--------------|--------|------|------|
| bare git remote | `origin_be.git` | 초기 커밋 1개 + `main` 브랜치 + `origin/HEAD`→main 설정 | fixture (`conftest.py` `git init --bare`) |
| bare git remote | `origin_fe.git` | 초기 커밋 1개 + `main` 브랜치 | fixture |
| clone (유형 A 코드 레포) | `{proj_a}/workspace/backend` | `origin_be.git` clone, `main` 체크아웃, clean | fixture |
| clone (유형 A 코드 레포) | `{proj_a}/workspace/frontend` | `origin_fe.git` clone, `main` 체크아웃, clean | fixture |
| 프로젝트 루트 (유형 A) | `{proj_a}` | `.opal/worktree.json`(multi-repo) + `.gitignore` 존재, `workspace/` 아래 clone 2개 | fixture |
| bare git remote | `origin_mono.git` | `workspace/backend/`·`workspace/frontend/`·`tasks/`·`.opal/` 4디렉토리 + 각 파일 1개 커밋 | fixture |
| clone (유형 B 모노레포) | `{proj_b}` | `origin_mono.git` clone, `main` 체크아웃, `.opal/worktree.json`(monorepo) 배치 | fixture |
| 가드 상태 저장소 | `{guard_dirty}` | worktree 생성 후 추적 파일 1개 수정(미커밋) | fixture |
| 가드 상태 저장소 | `{guard_unpushed}` | worktree 생성 후 커밋 1개 생성, push 안 함 | fixture |
| 가드 상태 저장소 | `{guard_unmerged}` | worktree 브랜치에 커밋 1개, base(`main`)에 미머지 | fixture |
| 가드 상태 저장소 | `{guard_clean}` | 브랜치 커밋을 base에 머지 + push 완료 + clean | fixture |
| 설정 파일 | `worktree.json` (부적합 3종) | ①`layout` 키 누락 ②`layout: "unknown"` ③`repos[0].path: "../escape"` | fixture (인라인 dict → json.dump) |
| 설정 파일 | `.gitignore` (기존 항목 보유) | `.opal-worktrees/` 행이 이미 존재 | fixture |
| 기존 state.json | 090·091 태스크 산출물 | 현행 스키마 (worktree 키 없음) | 저장소 실파일 (읽기 전용 대조용) |
| 실환경 프로젝트 | `/Volumes/Data/StoreLinkStudio/revup` | git clean, `main`, 코드 레포 2개 보유 | 캡틴 작업 환경 (검증 후 `remove`로 원복) |
| 실환경 프로젝트 | `/Volumes/Data/StoreLinkStudio/mams` | git clean 아님(2파일 수정) — 검증 전 상태 기록 필수 | 캡틴 작업 환경 (검증 후 `remove`로 원복) |
| 환경 변수 | `UV_CACHE_DIR` | 미설정 (기본 `~/.cache/uv`, 12GB, 시스템 볼륨) | 캡틴 로컬 셸 |
| **도구 경로 (iteration 2)** | `state-tool` 실행 경로 | S-24가 `state-tool`을 subprocess로 호출하므로 conftest가 경로를 노출 | fixture (`~/.opal/tools/state-tool/run.sh` 또는 저장소 소스 경로) |
| **프로젝트 (iteration 2)** | `{proj_no_config}` | 유형 A 구조이나 `.opal/worktree.json` **부재**. `.gitignore` sha256 사전 기록 | fixture (S-24 ⓒ · S-26 ①) |
| **프로젝트 (iteration 2)** | `{proj_broken_config}` | `.opal/worktree.json`이 JSON 문법 오류 | fixture (S-26 ②) |
| **설정 파일 (iteration 2)** | `worktree.json` 부적합 추가 3종 | ④`repos: []` ⑤`repos[1]`이 `.git` 없는 디렉토리 ⑥`repos[0]`이 프로젝트 밖 심볼릭 링크 | fixture (S-14 확장) |

> **[MUST] git fixture 공통 주입**: 모든 fixture의 git 호출에 `-c user.email=test@opal.local -c user.name=OPAL Test -c commit.gpgsign=false -c init.defaultBranch=main`을 주입한다. 캡틴 전역 git 설정에 의존하면 CI·타 머신에서 깨진다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 빈 태스크 폴더 | `state-tool init` **`--worktree` 미지정** | `state.json` 파싱 → `"worktree" not in state` |
| S-2 | 동일 입력 태스크 폴더 2개 | 한쪽 `--worktree` 유, 한쪽 무로 `init` | 두 `STATE.md` 바이트 비교 → 동일. `--worktree` 쪽 `state.json`에만 키 존재 |
| S-3 | 변경 전 git 트리 | Step 9~17 문서 변경 커밋 전 상태 | `git diff --stat opal/skills/opal-pilot-*/SKILL.md` → `opal-pilot-dev` 1건만 |
| S-4 | 유형 A fixture (`{proj_a}`) | `create --task 092` | 코드 레포 2곳 `git worktree list` 각 +1행, `{proj_a}/.opal-worktrees/task_092/workspace/{backend,frontend}` 존재, 브랜치 `feat/OP-TASK-092` |
| S-5 | 유형 B fixture (`{proj_b}`) | `create --task 092` | `.opal-worktrees/task_092/` 에 `workspace/` 존재 + `tasks/`·`.opal/` **부재** |
| S-6 | `{guard_dirty}` worktree | `remove --task 092` | `{"ok": false}` + dirty 전용 에러 코드. worktree 디렉토리 **잔존** |
| S-7 | `{guard_unpushed}` worktree | `remove --task 092` | `{"ok": false}` + unpushed 전용 에러 코드 (dirty 코드와 상이) |
| S-8 | `{guard_unmerged}` worktree | `remove --task 092` | `{"ok": false}` + unmerged 전용 에러 코드 (앞 2종과 상이) |
| S-9 | `{guard_clean}` worktree | `remove --task 092` | `{"ok": true}` + worktree 디렉토리 제거 + **브랜치는 잔존** |
| S-10 | `{guard_dirty}` worktree | `remove --task 092 --force` | `{"ok": true}` + stdout에 `forced`·`bypassed_guards` 기록 |
| S-11 | `.gitignore` 미보유 fixture | `create` 2회 연속 실행 | `.opal-worktrees/` 행 수 == 1. 이어서 3회째 실행 후 `sha256` 불변 |
| S-12 | 유형 A fixture, `repos[1].path`를 존재하지 않는 경로로 조작 | `create --task 092` | `{"ok": false}` + `repos[0]` worktree·브랜치 **부재**(롤백 완료) + 재실행이 `WORKTREE_EXISTS`로 막히지 않음 |
| S-13 | S-4 성공 상태 | `origin/HEAD`를 다른 브랜치로 변경 → `remove --task 092` | 미머지 판정이 `create` 시점 base(`main`) 기준으로 불변 |
| S-14 | 부적합 config **6종** + 템플릿 2종 | ①②③④는 `list --project-root`, ⑤⑥은 `create --task 092`(pre-flight 경로) 호출 | ①②③이 **서로 다른** 코드, ④ `CONFIG_INVALID_TYPE`, ⑤ `NOT_A_GIT_REPO`(worktree 0개·브랜치 0개), ⑥ 심볼릭 링크 **통과**. 템플릿 2종 통과 |
| S-15 | install 미실행 상태 | `./scripts/install-mac.sh` 실행 | `test -x ~/.opal/tools/worktree-tool/run.sh` 성공 + `run.sh list` JSON 반환 |
| S-16 | 캐시 경로를 프로젝트와 다른 볼륨으로 조작한 fixture | `create --task 092` | `{"ok": true}` + `warnings[]`에 볼륨 불일치 항목 존재 (**차단 없음**) |
| S-17 | 하네스 §2.5 삽입 후 트리 | `grep -rn "opal-harness.md §" opal/ docs/` | 매칭된 모든 §번호가 실제 존재 절을 지시 (dangling 0) |
| S-18 | 실환경 revup (clean 확인 후) | `create --task 092` → 검증 → `remove` | 코드 레포 2곳 worktree 생성 확인 후 원복. `git status` 검증 전과 동일 |
| S-19 | 실환경 mams (사전 상태 기록) | `create --task 092` → 검증 → `remove` | sparse 체크아웃 확인 + `copy[]` 파일 복사됨 + `.venv`·`node_modules` **부재** 후 원복 |
| S-20 | `UV_CACHE_DIR` 미설정 상태 | 캐시 이전 6단계 실행 | `uv cache dir` 신경로 + mams `uv sync` 완주 + `df` 실디스크 증가 측정 + 복구 절차 유효 |
| S-21 | `setup[]`에 sentinel 생성 명령을 넣은 fixture | `create --task 092` | sentinel 파일 **부재** + 응답 `pending_setup[]`에 명령 열거됨 |
| S-22 | 슬롯 0개 상태 | `create --task 092` → 이어서 `create --task 093` | 1회차 동시 슬롯 경고 **부재**, 2회차 경고 **출현**, 양쪽 모두 `ok:true` |
| S-23 | 유형 A fixture, 슬롯 2개 생성 | 슬롯 A 파일 수정·커밋 → 슬롯 B 상태 확인 | 슬롯 B의 작업 트리·브랜치가 **영향 없음**. 두 슬롯이 서로 다른 브랜치를 독립 체크아웃 중 |
| S-24 | 유형 A fixture + 빈 태스크 폴더 + `state-tool` 실행 경로 | `create --task 092` → 응답 `worktree_root` 추출 → `state-tool init --worktree <값>` → `show --format json`. 이어서 config 부재 fixture로 실패 경로 재현 | `data.worktree` == `worktree_root` (문자열 동일). 실패 경로에서는 `worktree` 키 부재 + `state init` 자체는 exit 0. **문서 3종에 축 문안 존재**(grep) |
| S-25 | dirty·unpushed·미머지·clean 4상태 worktree | 각 상태에 `status --task 092` 호출 + `opal-pilot-dev/SKILL.md` grep | 4상태 모두 `ok:true` + 가드 판정이 동일 상태의 `remove` 판정과 일치. SKILL.md STEP 6 안내가 `status`를 근거로 기술됨 |
| S-26 | ①`worktree.json` 부재 프로젝트 ②깨진 JSON 보유 프로젝트 (각각 `.gitignore` sha256 사전 기록) | 각각 `create --task 092` | ① `CONFIG_NOT_FOUND` ② `CONFIG_INVALID_JSON`. 양쪽 모두 `.gitignore` sha256 **불변** + `.opal-worktrees/` 미생성 + 브랜치 미생성 |
| S-27 | S-4 성공 상태(슬롯 092 생존) + 메타 파일 sha256 사전 기록 | 동일 번호로 `create --task 092` 재실행 | `WORKTREE_EXISTS`/`BRANCH_EXISTS` 거부. 기존 worktree 디렉토리·브랜치 존재 + `.meta/task_092.json` sha256 **불변** |
| S-29 | 유형 A·B fixture 각각 `create` 완료 상태 + 빈 껍데기 인위 조성 fixture | `remove` → 슬롯 루트 확인 → 같은 번호 `create` 재실행 → `list`·`create` 판정 대조 | 슬롯 루트(`task_092/`) **부재**. 재생성 `ok:true`(기존 브랜치 재사용). `list`가 슬롯 없다 할 때 `create`가 `WORKTREE_EXISTS`를 내지 않음 |
| S-28 | 슬롯이 **없는** 상태(또는 `remove` 완료 직후) | `remove --task 092` 및 `status --task 092` 재호출 | 양쪽 모두 `META_NOT_FOUND` 계열로 **명확히 보고**하고 예외로 죽지 않음. CLOSE 안내 경로에서는 no-op 비차단(태스크 종료를 막지 않음) |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: `--worktree` 미지정 시 `state.json`에 키가 생성되지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `state_tool.py cmd_init` 조건부 대입 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 빈 임시 태스크 폴더 2개. ①`--worktree` **미지정** ②`--worktree <절대경로>` **지정** — 같은 케이스에서 양방향을 함께 본다 |
| 기대 결과 | ①미지정: `state.json`에 `"worktree"` 키가 **존재하지 않음**(`null` 값 키도 불가). ②**지정: `state["worktree"]`가 전달한 절대경로와 문자열 동일**(`null`·빈 문자열·상대경로 불가) + `state-tool show --format json`의 `data.worktree`가 **같은 값**을 반환. 양쪽 exit 0 <br>*(iteration 2 — G-3 반영: 종전에는 "키 존재"만 보아 값이 `null`이어도 통과했다)* |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py -k TestWorktreeFlag -v` |
| 결과 | Pass |
| 상세 | `test_s1_worktree_specified_key_matches_value_and_show_json` PASSED, `test_s1_worktree_unspecified_key_absent_in_state_json` PASSED (전량 `state-tool` 스위트 308 passed, 32 subtests passed 중 포함, PM 기준값 일치). ①미지정 시 `"worktree" not in state`, `null` 키도 부재 확인 ②지정 시 `state["worktree"]`가 입력 절대경로와 문자열 동일 + `show --format json`의 `data.worktree` 동일 값 반환. 양쪽 exit 0 |

#### S-3: pilot SKILL.md diff가 `opal-pilot-dev` 1건뿐이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | TASK C-9 "pilot 10종 미변경" 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash + git)** |
| 조건 | Step 9~17 문서 변경 완료 후, 커밋 전 작업 트리 |
| 기대 결과 | `git diff --stat opal/skills/opal-pilot-*/SKILL.md` 출력 파일 수 == 1이고 그 파일이 `opal-pilot-dev/SKILL.md`. 나머지 9종 diff 0 |
| 도구 | git (Bash 단발) |
| 실행 명령 | `git diff --stat opal/skills/opal-pilot-*/SKILL.md` |
| 결과 | Pass |
| 상세 | 출력: `opal/skills/opal-pilot-dev/SKILL.md \| 8 +++++++-` 1건뿐(7 insertions, 1 deletion). `opal-pilot-*` glob에 매칭되는 나머지 9종 SKILL.md는 diff 0. (참고: `opal-project-init/SKILL.md`도 별도로 수정되어 있으나 이는 `opal-pilot-*` 패턴에 해당하지 않아 TASK C-9 "pilot 10종 미변경" 계약의 검증 대상 밖) |

#### S-14: `validate_worktree_config()`가 부적합 3종을 각각 다른 코드로 거부한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-001 검증 함수 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | **부적합 6종** — ①`layout` 키 누락 ②`layout: "unknown"` ③`repos[0].path: "../escape"` ④`repos: []`(빈 배열) ⑤`repos[1]`이 `.git` 없는 일반 디렉토리 ⑥`repos[0]`이 프로젝트 밖을 가리키는 심볼릭 링크 + 유형 A/B 템플릿 2종 |
| 기대 결과 | ①②③이 `{"ok": false}`이고 `error` 값이 **서로 모두 다름**. ④는 `CONFIG_INVALID_TYPE`. ⑤는 pre-flight `NOT_A_GIT_REPO`로 거부되며 **worktree 0개·브랜치 0개**(S-12 롤백 경로와 별개 계약 — 애초에 생성 시도 자체가 없어야 함). ⑥은 PLAN §3.1.3 `_is_inside()`의 "**심볼릭 링크 미해석**" 결정대로 **통과**(구현자가 `resolve()`로 바꾸면 이 케이스가 깨져 결정을 고정한다). 템플릿 2종은 `{"ok": true}` <br>*(iteration 2 — G-7 반영: ④⑤⑥ 추가)* |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s14` |
| 결과 | Pass |
| 상세 | 9 tests PASSED (`pytest -k s14` → `9 passed, 32 deselected`): `test_s14_1_missing_layout_key_gives_config_missing_key`, `test_s14_2_invalid_layout_value_gives_config_invalid_layout`, `test_s14_3_repos_path_escape_gives_config_path_escape`, `test_s14_4_empty_repos_array_gives_config_invalid_type`, `test_s14_error_codes_are_all_distinct`, `test_s14_5_non_git_repo_dir_rejected_pre_flight_with_zero_side_effect`, `test_s14_6_symlink_repo_path_is_not_resolved_and_passes`, `test_s14_multi_repo_template_passes_validation`, `test_s14_monorepo_template_passes_validation`(9개 함수 전량 PASS). 코드 확인(`validate_worktree_config()` L167-213): ①②③이 각각 `CONFIG_MISSING_KEY`/`CONFIG_INVALID_LAYOUT`/`CONFIG_PATH_ESCAPE`로 상이, ④`CONFIG_INVALID_TYPE`, ⑤ pre-flight `NOT_A_GIT_REPO`로 거부(worktree/브랜치 0개), ⑥ `_is_inside()`가 문자열 기준 판정(`Path.resolve()` 미사용)이라 심볼릭 링크 미해석 통과가 코드로 고정됨. 템플릿 2종 통과 |

#### S-16: 캐시 볼륨 불일치는 경고만 하고 차단하지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | F-009(b) `diagnose_cache_volume()` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `UV_CACHE_DIR`를 프로젝트와 다른 `st_dev`를 갖는 경로로 지정한 fixture |
| 기대 결과 | `{"ok": true}` 유지 + `warnings[]` 길이 >= 1 + 해당 경고에 캐시 볼륨 관련 문구 포함. 예외 전파 없음 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s16` |
| 결과 | Pass |
| 상세 | `test_s16_cache_volume_mismatch_warns_but_never_blocks` PASSED (`1 passed, 40 deselected`). `{"ok": true}` 유지 + `warnings[]` >= 1 + 볼륨 관련 문구 포함, 예외 미전파 확인 |

#### S-17: 하네스 § 번호 삽입 후 전역 인용에 dangling이 없다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | F-003 `opal-harness.md` §2.5 삽입 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep + 대조)** |
| 조건 | Step 9 완료 후 작업 트리 |
| 기대 결과 | `grep -rn "opal-harness.md §" opal/ docs/`가 찾은 모든 §번호가 `opal-harness.md`에 실존하는 절을 지시. 기존 `§3 State`·`§4`·`§9 OPAL Tools` 번호 불변 |
| 도구 | grep (Bash 단발) |
| 실행 명령 | `grep -rn "opal-harness.md §" opal/ docs/` 후 `opal-harness.md`의 `^## <N>` 헤딩 집합과 대조(파이썬 1회성 스크립트로 dangling 여부 산출) — `python3 -m pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -k s17 -q`로도 동일 검증 |
| 결과 | Pass |
| 상세 | opal-test-agent 재검증: `grep -rn "opal-harness.md §" opal/ docs/`로 §1~§9 인용 다수 확인 → `grep -n "^## " opal/core/references/opal-harness.md` 헤딩 목록: `1. Guards`, `2. 모듈 구조`, `2.5 워크스페이스 축`, `3. State`, `4. TASK 공통 프로세스`, `5. Observability`, `6. Model Mapping`, `7. 병렬 처리 원칙`, `8. EXECUTE @header 규칙`, `9. OPAL Tools`, `10. Coding Principles` — 인용된 모든 §번호가 실존, dangling 0건. `pytest -k s17` → `1 passed, 40 deselected`. EXECUTE 자가점검과 일치 |

### L2. 프로세스 통합 (자동, 실 자원 read→CUD→re-read)

> 본 태스크의 실 자원은 **실 git 저장소**다. mock/patch 없이 `git init`·`git worktree add`를 실제 수행한다.

#### S-2: `--worktree` 유무와 무관하게 STATE.md 렌더가 동일하다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-11 |
| 대상 | F-005 — `_build_new_state_md` 무접촉 계약 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 동일 인자(`--skill`/`--mode`/`--rows-from`/`--task-title`)로 태스크 폴더 2개에 `init`. 한쪽만 `--worktree` 추가 |
| 기대 결과 | 두 `STATE.md`가 **타임스탬프 행을 제외하고 바이트 동일**. `state.json`은 `worktree` 키 유무만 차이 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py -k TestWorktreeFlag -v` |
| 결과 | Pass |
| 상세 | `test_s2_state_json_differs_only_in_worktree_key` PASSED, `test_s2_state_md_identical_regardless_of_worktree_flag` PASSED. 동일 인자(`--skill`/`--mode`/`--rows-from`/`--task-title`)로 초기화한 두 `STATE.md`가 타임스탬프 행 제외 바이트 동일, `state.json`은 `worktree` 키 유무만 차이 확인 |

#### S-4: 유형 A — 코드 레포 N개에 각각 worktree가 생성된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-002 `create` multi-repo 분기 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | bare remote 2 + clone 2를 `workspace/{backend,frontend}`에 둔 `{proj_a}`, `.opal/worktree.json`(multi-repo) |
| 기대 결과 | 각 코드 레포에서 `git worktree list` 항목 +1. 경로가 `{proj_a}/.opal-worktrees/task_092/workspace/{backend,frontend}`. 브랜치명이 `feat/OP-TASK-092`. `.opal-worktrees/.meta/task_092.json`에 `entries[].base_ref` 기록 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s4` |
| 결과 | Pass |
| 상세 | `test_s4_multi_repo_create_creates_worktree_per_repo` PASSED (`1 passed`). 실 git 자원으로 각 코드 레포 `git worktree list` +1행, `.opal-worktrees/task_092/workspace/{backend,frontend}` 존재, 브랜치 `feat/OP-TASK-092`, `.meta/task_092.json`에 `entries[].base_ref` 기록 확인 |

#### S-5: 유형 B — sparse worktree에 `workspace/`만 체크아웃된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-002 `create` monorepo 분기 (`--no-checkout`→`init --cone`→`set`→`checkout` 순서) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `workspace/`·`tasks/`·`.opal/` 4디렉토리를 가진 모노레포 clone `{proj_b}` |
| 기대 결과 | `.opal-worktrees/task_092/workspace/` 존재. `tasks/`·`.opal/` **부재**. 브랜치 `feat/OP-TASK-092` |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s5` |
| 결과 | Pass |
| 상세 | `test_s5_monorepo_create_checks_out_workspace_only` PASSED (`1 passed`). `--no-checkout`→`sparse-checkout init --cone`→`set`→`checkout` 순서로 `.opal-worktrees/task_092/workspace/`만 존재, `tasks/`·`.opal/` 부재, 브랜치 `feat/OP-TASK-092` 확인 |

#### S-6: `remove`가 dirty 작업본을 거부한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-008 가드 ① |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `create` 성공 후 worktree 안 추적 파일 1개를 수정(미커밋) |
| 기대 결과 | `{"ok": false}` + dirty 전용 에러 코드. worktree 디렉토리와 브랜치 모두 **잔존** |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s6` |
| 결과 | Pass |
| 상세 | `test_s6_remove_rejects_dirty_worktree` PASSED (`1 passed`). `{"ok": false}` + dirty 전용 에러 코드, worktree 디렉토리·브랜치 잔존 확인 |

#### S-7: `remove`가 unpushed 커밋을 거부한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-008 가드 ② |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `create` 후 worktree에서 커밋 1개 생성, push 안 함, 작업본은 clean |
| 기대 결과 | `{"ok": false}` + unpushed 전용 에러 코드 (**S-6 코드와 상이**) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s7` |
| 결과 | Pass |
| 상세 | `test_s7_remove_rejects_unpushed_commit` PASSED (`1 passed`). `{"ok": false}` + unpushed 전용 에러 코드(S-6 코드와 상이) 확인 |

#### S-8: `remove`가 미머지 브랜치를 거부한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-008 가드 ③ |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `create` 후 커밋 1개 생성 + push 완료, 그러나 base(`main`)에 미머지. 작업본 clean |
| 기대 결과 | `{"ok": false}` + unmerged 전용 에러 코드 (**S-6·S-7 코드와 상이**) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s8` |
| 결과 | Pass |
| 상세 | `test_s8_remove_rejects_unmerged_branch` PASSED (`1 passed`). `{"ok": false}` + unmerged 전용 에러 코드(S-6·S-7과 상이) 확인 |

#### S-9: 3조건 모두 해소되면 `remove`가 성공하고 브랜치는 남긴다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-008 정상 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | clean + push 완료 + base에 머지 완료 |
| 기대 결과 | `{"ok": true}` + worktree 디렉토리 제거 + `git branch --list feat/OP-TASK-092`가 **여전히 존재**(브랜치 자동 삭제 금지) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s9` |
| 결과 | Pass |
| 상세 | `test_s9_remove_succeeds_when_all_guards_clear_and_keeps_branch` PASSED (`1 passed`). `{"ok": true}` + worktree 디렉토리 제거 + `git branch --list feat/OP-TASK-092` 여전히 존재(브랜치 자동 삭제 없음) 확인 |

#### S-10: `--force`가 가드를 우회하되 우회 사실을 기록한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-008 `--force` 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | dirty 상태 worktree + `--force` |
| 기대 결과 | `{"ok": true}` + stdout JSON에 `forced: true`와 우회된 가드 목록(`bypassed_guards`) 포함 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s10` |
| 결과 | Pass |
| 상세 | `test_s10_remove_force_bypasses_guard_and_records_it` PASSED (`1 passed`). `{"ok": true}` + stdout JSON에 `forced: true`·`bypassed_guards` 기록 확인 |

#### S-11: `.gitignore` 추가가 멱등이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-007 `ensure_gitignore_entry()` |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `.opal-worktrees/` 항목이 없는 `.gitignore`. `create`를 3회 실행(2회차·3회차는 다른 태스크 번호) |
| 기대 결과 | `.opal-worktrees/` 행 수 == 1. 2회차 실행 직전/직후 `.gitignore` **sha256 동일**(항목 존재 시 write 자체를 하지 않음) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s11` |
| 결과 | Pass |
| 상세 | `test_s11_gitignore_entry_idempotent_and_byte_unchanged` PASSED (`1 passed`). `.opal-worktrees/` 행 수 == 1(3회 실행 후도 동일), 2회차 이후 `.gitignore` sha256 불변 확인. 코드(`ensure_gitignore_entry` L254-274)도 이미 존재 시 write를 skip하도록 구현됨 |

#### S-12: 중간 실패 시 자기 생성물을 전량 회수한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-002 `_rollback()` (DEC-2 도구 계층 all-or-nothing) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | 유형 A fixture에서 `repos[1].path`를 존재하지 않는 경로로 조작(pre-flight를 통과하도록 조작 시점은 첫 `worktree add` 이후) |
| 기대 결과 | `{"ok": false}` + `repos[0]`의 worktree 디렉토리·브랜치 **모두 부재** + 조작을 되돌린 뒤 `create` 재실행이 `WORKTREE_EXISTS`/`BRANCH_EXISTS` 없이 성공 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s12` |
| 결과 | Pass |
| 상세 | `test_s12_partial_failure_rolls_back_all_created_entries` PASSED (`1 passed`). `{"ok": false}` + `repos[0]` worktree·브랜치 모두 부재(롤백 완료), 재실행이 `WORKTREE_EXISTS` 없이 성공 확인 |

#### S-13: base-ref 동결로 `remove` 판정이 결정론적이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-002 `resolve_base_ref()` + 메타 동결 (DEC-3) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `create` 성공 후 `origin/HEAD`를 다른 브랜치(`develop`)로 변경. worktree 브랜치는 `main`에 미머지 |
| 기대 결과 | `remove` 판정이 여전히 `main` 기준 미머지로 거부. `origin/HEAD` 변경이 판정을 뒤집지 않음. 메타 파일이 `.opal-worktrees/.meta/`(worktree **밖**)에 있어 dirty 가드 오탐 없음 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s13` |
| 결과 | Pass |
| 상세 | `test_s13_remove_uses_frozen_base_ref_not_live_origin_head` PASSED (`1 passed`). `origin/HEAD`를 `develop`으로 변경해도 `remove` 판정이 여전히 `create` 시점 base(`main`) 기준 미머지로 거부(동결 확인) |

#### S-15: install 재배포 후 `run.sh`에 실행 권한이 있다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-002 배포 (`install-mac.sh` chmod 블록) |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash)** |
| 조건 | Step 14 완료 후 `./scripts/install-mac.sh` 실행 |
| 기대 결과 | `test -x ~/.opal/tools/worktree-tool/run.sh` 성공 + `~/.opal/tools/worktree-tool/run.sh list --project-root $(pwd)`가 단일 라인 JSON 반환 + `~/.opal/templates/worktree-*.json` 2개 배포됨 |
| 도구 | Bash 단발 |
| 실행 명령 | `./scripts/install-mac.sh && test -x ~/.opal/tools/worktree-tool/run.sh && ~/.opal/tools/worktree-tool/run.sh list --project-root $(pwd) && test -f ~/.opal/templates/worktree-multi-repo.json && test -f ~/.opal/templates/worktree-monorepo.json` — Step 14 GREEN(chmod 블록 추가 완료). **[MUST] 실제 재배포는 Step 18(PM 직접) 담당** — 본 워커는 명령 문안만 기입하고 실행하지 않는다(가드레일: `~/.opal/` 배포본 수정 금지, install 실행 금지) |
| 결과 | Pass |
| 상세 | [MUST] 준수 — `install-mac.sh` 재실행하지 않고 배포 결과만 확인. `test -x ~/.opal/tools/worktree-tool/run.sh` → OK(실행 가능). `~/.opal/tools/worktree-tool/run.sh list --project-root /Volumes/Data/AiStudio/workspace/opal` → 단일 라인 JSON 반환(`{"ok": false, "error": "CONFIG_NOT_FOUND", ...}` — opal 저장소 자체에 `.opal/worktree.json`이 없어 발생하는 정상 응답이며, "단일 라인 JSON 반환" 요건은 충족). `ls ~/.opal/templates/worktree-*.json` → `worktree-monorepo.json`, `worktree-multi-repo.json` 2개 배포 확인 |

#### S-21: `setup[]`을 실행하지 않고 열거만 한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | F-002 lazy setup (TASK C-7) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `worktree.json`의 `setup[]`에 sentinel 파일을 생성하는 명령을 넣은 fixture |
| 기대 결과 | `create` 후 sentinel 파일 **부재**. 응답 `pending_setup[]`에 해당 명령이 문자열로 열거됨 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s21` |
| 결과 | Pass |
| 상세 | `test_s21_setup_commands_are_not_executed_but_enumerated` PASSED (`1 passed`). `create` 후 sentinel 파일 부재, 응답 `pending_setup[]`에 명령 문자열 열거 확인(lazy setup) |

#### S-22: 동시 슬롯 2개째부터 경고가 나오되 차단하지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-16 |
| 대상 | F-002 `diagnose_concurrent_slots()` (DEC-6) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | 슬롯 0개 상태에서 `create --task 092` 후 이어서 `create --task 093` |
| 기대 결과 | 1회차 `warnings[]`에 동시 슬롯 항목 **부재**, 2회차 **출현**. 양쪽 모두 `{"ok": true}`이며 2회차 worktree도 정상 생성됨(차단 없음) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s22` |
| 결과 | Pass |
| 상세 | `test_s22_concurrent_slot_warning_appears_from_second_slot_only` PASSED (`1 passed`). 1회차 `warnings[]` 동시 슬롯 항목 부재, 2회차 출현, 양쪽 `{"ok": true}`(차단 없음) 확인 |

#### S-23: 두 슬롯이 서로 간섭 없이 독립 작업된다 (목표달성 시나리오)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-목표 (TASK §작업 목표 직접 검증) |
| 대상 | 태스크 전체 — "여러 태스크를 격리된 작업공간에서 동시 수행" |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | 유형 A fixture에서 `create --task 092`와 `create --task 093`으로 슬롯 2개 생성 |
| 기대 결과 | ①슬롯 092에서 파일 수정·커밋해도 슬롯 093의 `git status --porcelain`이 **비어 있음** ②두 슬롯이 서로 다른 브랜치(`feat/OP-TASK-092` / `feat/OP-TASK-093`)를 각각 체크아웃 중 ③메인 작업본(`workspace/backend`)의 브랜치·상태가 **양쪽 모두에 영향받지 않음** |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s23` |
| 결과 | Pass |
| 상세 | `test_s23_two_slots_are_isolated_from_each_other` PASSED (`1 passed`). ①슬롯 092 수정·커밋해도 슬롯 093 `git status --porcelain` 비어 있음 ②두 슬롯이 각각 `feat/OP-TASK-092`/`feat/OP-TASK-093` 체크아웃 ③메인 작업본 무영향 확인 — 목표달성 시나리오(2슬롯 격리 실효성) 검증 완료 |

#### S-24: 파이프라인 관통 — 플래그에서 state 기록까지 실제로 이어진다 (목표달성 시나리오)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-17**, H-목표 |
| 대상 | F-004 스텝 4.5 훅 + F-005 `--worktree` 전달 + DEC-2 파이프라인 계층 정책 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | 유형 A fixture. `task-process.md` 스텝 4.5가 규정한 호출 순서를 그대로 재현하는 통합 테스트 — ①`worktree-tool create --task 092` ②응답 `worktree_root` 수신 ③`state-tool init --worktree <그 값>` |
| 기대 결과 | **4항 전부 성립** — ⓐ`create`가 `{"ok": true}`이고 응답 `worktree_root`가 `{proj}/.opal-worktrees/task_092` ⓑ`state-tool show --format json`의 `data.worktree`가 ⓐ의 값과 **문자열 동일** ⓒ`create`를 실패시킨 조건(config 부재)에서는 `--worktree`가 전달되지 않아 `state.json`에 `worktree` 키가 **부재**하고, 그럼에도 `state init` 자체는 **성공**한다(DEC-2 파이프라인 비차단 계속) <br>ⓓ**문서 3종이 그 순서를 실제로 지시한다**(grep) — `harness/task-process.md`에 스텝 **4.5**와 `worktree-tool create` 호출 + `--worktree` 전달 문안 존재 / `pm/dispatch-process.md`에 `## 작업 경로` 블록과 "절대경로" 문구 존재 / `opal-harness.md`에 **§2.5** 절과 3항목(직교 축·미사용 시 현행 유지·config 부재 시 동작) 존재 |
| ⓓ가 필요한 이유 | iteration 2 권고 R-1 — ⓐⓑⓒ만으로는 **테스트가 올바른 순서를 스스로 하드코딩**할 뿐, 문서가 그 순서를 지시하는지는 묻지 않는다. 훅 문안이 비어 있어도 통과하는 여지가 남는다. S-25가 이미 쓰는 grep 기법과 동일하며 비용은 grep 3회 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -k s24 -q` — Step 3/6/7/9/10/11 전부 완료(Step 10: `harness/task-process.md` 스텝 4.5 삽입 GREEN) → 실행 결과 `1 passed`(전량 `36 passed` — `pytest opal/tools/worktree-tool/tests/ -q`) |
| 결과 | Pass |
| 상세 | opal-test-agent 재실행: `test_s24_pipeline_flag_flows_from_create_into_state` PASSED (`1 passed` — 전체 스위트 재실행 시점 기준 `41 passed`, 이전 Step 기록의 `36 passed`에서 S-25~S-29 등 후속 추가분 반영). ⓐ`create` `{"ok": true}` + `worktree_root` = `{proj}/.opal-worktrees/task_092` ⓑ`state-tool show --format json`의 `data.worktree`가 ⓐ 값과 문자열 동일 ⓒ config 부재 조건에서 `--worktree` 미전달 시 `state.json`에 `worktree` 키 부재 + `state init` exit 0 성공. ⓓ grep 재확인 — `harness/task-process.md`에 "4.5" 스텝과 `worktree-tool create`/`--worktree` 호출 문안 존재, `pm/dispatch-process.md`에 `## 작업 경로` 블록과 "절대경로" 문구 존재, `opal-harness.md`에 §2.5 절 존재(앞서 S-17에서 헤딩 확인). 파이프라인 관통(플래그→훅→도구→state) 계약 실증 완료 |

> **이 시나리오가 필요한 이유** (iteration 1 gap G-1): 목표 문장의 주어는 `worktree-tool`이 아니라 "**OPAL 태스크 파이프라인**이 축을 신설하여"다. 그런데 iteration 1의 F-004·F-006 검증은 `git diff --stat`(S-3)뿐이어서, **훅이 `create`를 아예 호출하지 않게 접합돼도 S-1~S-23이 전건 PASS**했다. 070과 동일한 형태의 공백이다.

#### S-25: `status`가 remove와 같은 판정을 보고하되 거부하지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-18** |
| 대상 | F-002 `status` 서브명령 + F-008 CLOSE "머지 대기" 안내 근거 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | dirty / unpushed / 미머지 / clean 4상태 worktree 각각에 `status --task 092` 호출 |
| 기대 결과 | 4상태 모두 `{"ok": true}`(**거부하지 않음**)이고, 보고된 가드 판정이 같은 상태에서의 `remove` 판정과 **일치**(dirty→dirty, clean→정리 가능). `opal-pilot-dev/SKILL.md` STEP 6의 안내 문안이 `status` 출력을 근거로 삼도록 기술되어 있음(grep 확인) |
| 도구 | pytest + grep |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -k s25 -q` (4상태 파라미터화 + CLOSE 안내 grep, 2개 테스트 함수) — Step 12(`opal-pilot-dev/SKILL.md` STEP 6 worktree 정리 안내) GREEN 반영 |
| 결과 | Pass |
| 상세 | 5 tests PASSED: `test_s25_status_reports_same_judgment_as_remove_without_rejecting[dirty/unpushed/unmerged/clean]`(4개 파라미터) + `test_s25_close_guidance_references_status_output`. 4상태 모두 `status`가 `{"ok": true}`로 거부 없이 판정 보고, 같은 상태의 `remove` 판정과 일치 확인. `opal-pilot-dev/SKILL.md` STEP 6 안내 문안이 `status` 출력 근거 기술 확인(grep) |

> iteration 1 gap G-4: `status`는 23개 시나리오에서 **0회 호출**되었고, F-8의 절반인 CLOSE 안내가 무검증이었다.

#### S-26: `worktree.json` 부재·무효 시 부수효과 없이 거부한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-19** |
| 대상 | F-002 `load_config()` + F-003 §2.5 (3) "`worktree.json` 부재 시 동작" |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | ①`.opal/worktree.json`이 아예 없는 프로젝트 ②JSON 문법이 깨진 파일 — 각각 `create --task 092` |
| 기대 결과 | ①`{"ok": false}` + `CONFIG_NOT_FOUND` ②`{"ok": false}` + `CONFIG_INVALID_JSON`. **두 경우 모두 부수효과 0** — `.gitignore` 무변경(sha256 동일) + `.opal-worktrees/` 디렉토리 미생성 + 브랜치 미생성 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s26` |
| 결과 | Pass |
| 상세 | `test_s26_missing_config_rejected_without_side_effects`, `test_s26_broken_json_config_rejected_without_side_effects` 2건 PASSED. ①`CONFIG_NOT_FOUND` ②`CONFIG_INVALID_JSON` + 양쪽 모두 `.gitignore` sha256 불변·`.opal-worktrees/` 미생성·브랜치 미생성(부수효과 0) 확인 |

> iteration 1 gap G-5: F-3 AC가 §2.5의 필수 기재 3항목 중 하나로 못박은 동작인데 시나리오가 0건이었다. 실사용자가 가장 먼저 만나는 경로다.

#### S-27: 살아 있는 슬롯에 같은 번호로 재생성하면 거부하고 기존을 보존한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-20** |
| 대상 | F-002 pre-flight 중복 검사 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | `create --task 092` 성공 후, 슬롯을 제거하지 않은 채 `create --task 092` **재실행** |
| 기대 결과 | `{"ok": false}` + `WORKTREE_EXISTS` 또는 `BRANCH_EXISTS`. **기존 worktree 디렉토리·브랜치·`.opal-worktrees/.meta/task_092.json`이 모두 무손상**(재실행이 기존 슬롯을 훼손하지 않음) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s27` |
| 결과 | Pass |
| 상세 | `test_s27_duplicate_create_rejected_and_existing_slot_untouched` PASSED (`1 passed`). 재실행이 `WORKTREE_EXISTS`/`BRANCH_EXISTS`로 거부되고 기존 worktree·브랜치·`.meta/task_092.json` sha256 무손상 확인 |

> iteration 1 gap G-6: S-12는 "롤백 후 재실행이 **막히지 않음**"만 보았고, "살아 있는 슬롯은 **막혀야 함**"이라는 반대 방향이 비어 있었다.

#### S-28: 슬롯이 없는데 `remove`·`status`를 불러도 죽지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-21** |
| 대상 | F-002 `remove`/`status` 메타 부재 경로 + F-008 CLOSE 안내 no-op |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | ①슬롯을 만든 적 없는 프로젝트 ②`remove` 성공 직후 같은 명령 재실행 — 각각 `remove --task 092`·`status --task 092` |
| 기대 결과 | 두 경우 모두 `META_NOT_FOUND` 계열로 **명확히 보고**하고 스택 트레이스·예외로 종료하지 않음. CLOSE 안내 경로에서 호출될 때는 **no-op 비차단**(태스크 종료를 막지 않음 — `op-brain-ingest`·회고 하드스텝과 동일 패턴) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s28` |
| 결과 | Pass |
| 상세 | 3 tests PASSED: `test_s28_remove_and_status_without_meta_report_meta_not_found[remove]`, `[status]`, `test_s28_remove_twice_is_reported_cleanly_after_success`. 슬롯 없는 상태·`remove` 2회 재호출 모두 `META_NOT_FOUND` 계열로 명확히 보고, 예외로 죽지 않음 확인 |

> iteration 2 권고 R-2: `remove` 2회 실행은 실사용에서 흔한 경로인데 미검증이었다.

#### S-29: `remove` 후 같은 번호로 재생성할 수 있다 (실환경 결함 대응)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-22** |
| 대상 | F-002 `cmd_remove` 정리 범위 + `cmd_create` pre-flight 판정 기준 (DEC-7) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 git)** |
| 조건 | 5 케이스 — ⓐ유형 B 슬롯 루트 회수 ⓑ유형 A 슬롯 루트 회수 ⓒ`remove` 후 동일 번호 재생성 ⓓ`list`·`create` 판정 일치 ⓔ빈 껍데기만 남은 상태에서의 재생성 내성 |
| 기대 결과 | ⓐⓑ `remove` 성공 후 `{project}/.opal-worktrees/task_092/` **부재**(단 `.opal-worktrees/`·`.meta/`는 다른 슬롯용이라 보존) ⓒ재생성 `{"ok": true}` — 기존 브랜치를 **재사용**하며 `WORKTREE_EXISTS`/`BRANCH_EXISTS`로 막히지 않음 ⓓ`list`가 해당 슬롯을 반환하지 않는 상태에서 `create`가 `WORKTREE_EXISTS`를 반환하지 않음 ⓔ빈 껍데기가 재생성을 **영구 차단하지 않음** |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests/ -q -k s29` |
| 결과 | Pass |
| 상세 | 5 tests PASSED: `test_s29_1a_remove_clears_slot_root_for_single_repo`, `test_s29_1b_remove_clears_slot_root_for_multi_repo`, `test_s29_2_recreate_after_remove_succeeds`, `test_s29_3_list_and_create_agree_on_slot_existence`, `test_s29_4_empty_shell_slot_root_does_not_permanently_block_recreate`. ⓐⓑ `remove` 후 슬롯 루트 부재(`.opal-worktrees/`·`.meta/`는 보존) ⓒ재생성 `{"ok": true}`(브랜치 재사용, `WORKTREE_EXISTS` 없음) ⓓ`list`·`create` 판정 일치 ⓔ빈 껍데기가 재생성 영구 차단하지 않음 — 전건 확인 |

> **이 시나리오의 출처**: pytest 36건이 전부 GREEN인 상태에서 **revup 실환경 검증이 잡아낸 차단성 결함**이다(AGENTIC-LOG #25). S-9는 레포별 경로만, S-27은 살아 있는 슬롯만 봐서 "제거된 슬롯의 재생성" 경로가 비어 있었다. **단위 테스트 전건 통과가 실환경 정상을 보장하지 않는다는 증거**로 남긴다.

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-18: revup(유형 A) 실환경 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 실환경 multi-repo — TASK 완료기준 ① |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 캡틴 작업 환경을 건드리므로 자동화하지 않는다. M1 자동 검증은 S-4가 이미 커버 |
| 조건 | `/Volumes/Data/StoreLinkStudio/revup` git clean 확인 → 유형 A 템플릿 배치(`repos`를 실경로로 조정) → `create --task 092` → **이어서 `create --task 093`으로 슬롯 2개 확보** |
| 기대 결과 | ⓐ코드 레포 2곳에서 `git worktree list`에 신규 항목이 **슬롯당 1개씩(총 2개씩)**. 브랜치 `feat/OP-TASK-092`·`feat/OP-TASK-093`. `.gitignore` 멱등(2회 실행 1행) <br>ⓑ**2슬롯 동시성(목표 실증)** — 슬롯 092에서 파일 1개를 수정·커밋해도 슬롯 093과 **메인 `workspace/` 작업본**의 `git status --porcelain`이 **비어 있고 브랜치도 불변** <br>ⓒ**양쪽 슬롯을 `remove`로 원복**하여 `git status`·`git worktree list`가 검증 전과 동일 <br>*(iteration 2 — G-2 반영: 목표 주장이 실환경에서 미확인 상태였다)* |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** — 캡틴 CLOSE 진입 승인으로 수용 (2026-08-15) |
| 상세 | PM이 실환경 수행. 코드 레포 2곳 worktree 생성(`feat/OP-TASK-092`), 레이아웃 메인 동형, `.gitignore` 1행 멱등, `base_ref=origin/main` 동결. **2슬롯 격리 실증** — 슬롯 092 커밋 후 슬롯 093·메인 `workspace/backend` 공히 `git status` 0건·브랜치 불변(3자 각각 다른 브랜치 체크아웃). 3중 가드 `GUARD_UNPUSHED` 거부 → 해소 후 성공, 브랜치 잔존. **기준선 완전 원복**(루트 변경 0건, worktree 1개, `.opal-worktrees` 없음) |

#### S-19: mams(유형 B) 실환경 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 실환경 monorepo — TASK 완료기준 ② |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 캡틴 작업 환경 + mams는 현재 2파일 수정 상태라 사전 상태 기록이 필수 |
| 조건 | `/Volumes/Data/StoreLinkStudio/mams` **사전 `git status` 기록** → 유형 B 템플릿 배치 → `create --task 092` |
| 기대 결과 | `.opal-worktrees/task_092/`에 `workspace/`만 존재(`tasks/`·`.opal/` 부재). `copy[]` 대상 파일 복사됨. `.venv`·`node_modules` **부재**(lazy setup). `pending_setup[]` 열거. **검증 후 `remove`로 원복하여 사전 기록과 동일** |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** — 캡틴 CLOSE 진입 승인으로 수용 (2026-08-15) |
| 상세 | PM이 실환경 수행. sparse가 `workspace/`만 체크아웃하고 `tasks/`·`.opal/`·`100.기획`·`200.개발`·`900.문서` **전부 부재** 확인. `copy[]` 3파일 복사됨. lazy setup으로 `.venv`·`node_modules`·`.next` 미생성, `pending_setup` 열거. **슬롯 13MB**(메인 1.9GB 대비). 사전 2건 기준선 원복. **알려진 제약**: `cmux.json`이 `.opal/cmux/...`를 가리키는 심볼릭 링크라 슬롯에서 끊김 — 필요 시 `worktree.json` `copy[]`로 해결 가능 |

#### S-20: `UV_CACHE_DIR` 이전 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | F-009(a) — TASK 완료기준 ⑥ |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — **비가역 로컬 환경 변경**. 12GB 캐시 이동 + 셸 프로파일 영속화라 자동 실행 금지 |
| 조건 | 캡틴 명시 승인 → PLAN §3.9.3의 실행 6단계 → 검증 4항목 |
| 기대 결과 | `uv cache dir`이 `/Volumes/Data` 하위 신경로. mams `uv sync` 완주. 신규 `.venv` 실디스크 증가를 `df` 전후 측정치로 보고. `create` 재실행 시 볼륨 경고가 `warnings[]`에서 **사라짐**(H-12 반증). 복구 4단계 유효성 확인 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** — 캡틴 CLOSE 진입 승인으로 수용 (2026-08-15) |
| 상세 | PM이 PLAN §3.9.3 6단계 + 검증 4항 수행. 구 캐시 10.9GiB/639,911파일 clean, `~/.zshrc` 멱등 export(2회차 추가 생략 확인), interactive 셸에서 `uv cache dir → /Volumes/Data/.uv-cache`, `st_dev` 동일(16777230), mams `uv sync` exit 0, **볼륨 경고 소멸**(H-12 반증). **실디스크: 이전 전 263MB → 이전 후 8.7MB(약 30배 절감)**. 첫 슬롯은 캐시 재구축 포함 242.5MB, 2번째부터 8.7MB. **캡틴 환경에 `~/.zshrc` 1줄만 영구 잔존**(복구법 PLAN §3.9.3 표에 기재) |

#### PM 표준 요청 양식 (L3 시나리오 3건 공통)

```
캡틴, [시나리오 S-18 / S-19 / S-20]은 사용자 협업 검증이 필요합니다.
요청 내용: {시나리오 조건 요약}
기대 결과: {기대 결과 요약}
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

### 4.1 요구사항(F-1~F-9) AC 커버리지

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC (템플릿 2종 통과 + 3종 고유 코드 거부) | H-9 | L1 | S-14 | `opal/tools/worktree-tool/tests/test_worktree_tool.py`:`[T092/L1-F1]` | PLAN TS-002~005 |
| F-2 AC (4서브명령 JSON 계약 + 유형별 생성) | H-3, H-4, **H-18**, **H-19**, **H-20**, **H-21** | L2 | S-4, S-5, **S-25**, **S-26**, **S-27**, **S-28** | 동:`[T092/L2-F2a]`~`[T092/L2-F2f]` | PLAN TS-010·TS-011 + iteration 2 추가 4건. **`status` 서브명령이 S-25로 처음 검증됨** |
| F-3 AC (§2.5 3항목 + pilot diff 0) | H-2, H-13, **H-19** | L1 + L2 | S-3, S-17, **S-26** | 동:`[T092/L1-F3]`, `[T092/L2-F3b]` | §2.5 (3) "config 부재 시 동작"이 S-26으로 실증됨 |
| F-4 AC (4.5 훅 존재 + 기존 스텝 무변경) | H-2, **H-17** | L1 + L2 | S-3, **S-24** | 동:`[T092/L1-F4]`, `[T092/L2-F4b]` | `git diff` 대조 + **관통 실행 검증** |
| F-5 AC (지정 시 키 존재·**값 정합** / 미지정 시 키 부재 / STATE.md diff 0) | H-1, H-11, **H-17** | L1 + L2 | S-1, S-2, **S-24** | `opal/tools/state-tool/tests/test_state_tool.py`:`[T092/L1-F5a]`, `[T092/L2-F5b]` / `test_worktree_tool.py`:`[T092/L2-F4b]` | 기존 스위트에 **추가만**. 값 정합은 G-3 반영 |
| F-6 AC (절대경로 문구 + 2필드 계약 + 기존 블록 무변경) | H-2, **H-17** | L1 + L2 | S-3, **S-24** | `test_worktree_tool.py`:`[T092/L1-F6]` | grep + 관통 검증 |
| F-7 AC (2회 실행 시 1행 + 바이트 무변경) | H-6 | L2 | S-11 | 동:`[T092/L2-F7]` | PLAN TS-060~063 |
| F-8 AC (3조건 각 고유 코드 + 해소 시 성공 + force 기록 + **CLOSE 안내** + **재생성**) | H-5, **H-18**, **H-22** | L2 | S-6~S-10, **S-25**, **S-29** | 동:`[T092/L2-F8a]`~`[T092/L2-F8f]` | PLAN TS-070~075 + CLOSE 안내 검증(G-4) |
| F-9(a) AC (`uv sync` 정상 + 실디스크 측정 보고) | H-14 | L3 | S-20 | (수동 — 테스트 파일 없음) | 캡틴 승인 게이트 |
| F-9(b) AC (볼륨 불일치 경고 + 차단 없음) | H-12 | L1 | S-16 | `test_worktree_tool.py`:`[T092/L1-F9b]` | PLAN TS-080~082 |

### 4.2 TASK 완료기준(①~⑦) 커버리지

| 완료기준 | 가설 ID | 검증 계층 | 시나리오 | 비고 |
|---------|---------|---------|---------|------|
| ① revup worktree 2개 + `feat/OP-TASK-092` | H-3, H-17 | L2 + L3 | S-4(자동), **S-24**(관통), **S-18**(실환경 2슬롯) | 실환경 필수 |
| ② mams sparse + `tasks/`·`.opal/` 미체크아웃 | H-4 | L2 + L3 | S-5(자동), **S-19**(실환경) | 실환경 필수 |
| ③ `--wt` 미사용 시 스키마·렌더 diff 0 | H-1, H-11 | L1 + L2 | S-1, S-2 | 하위호환 핵심 |
| ④ `remove` 3중 가드 각 조건 거부 | H-5, **H-22** | L2 | S-6, S-7, S-8, **S-29** | 코드 상이 검증 + 제거 후 재생성 가능 |
| ⑤ `.gitignore` 멱등(중복 0행) | H-6 | L2 | S-11 | 바이트 무변경 포함 |
| ⑥ `UV_CACHE_DIR` 이전 후 `uv sync` + 측정 보고 | H-14 | L3 | **S-20** | 캡틴 승인 게이트 |
| ⑦ worktree-tool 회귀 테스트 전량 pass | **H-1~H-22** | L1 + L2 | **S-1~S-17, S-21~S-29** (L3 3건 S-18·S-19·S-20 제외) | `pytest` 스위트 전량 |

### 4.3 목표달성 시나리오 (`scenario-gate.md` §2 ①축)

| 목표 문장 (TASK §작업 목표) | 검증 계층 | 시나리오 | 검증 관점 |
|---------------------------|---------|---------|----------|
| "**OPAL 태스크 파이프라인에** 축을 신설하여" (목표 문장의 주어) | L2 | **S-24** | 플래그→훅→도구→state 접합이 **실제로 이어지는가** (부품이 아니라 관통) |
| "태스크별 코드 작업공간을 git worktree로 격리한다" | L2 + L3 | **S-23**(자동), **S-18**(실환경) | 2슬롯이 서로 간섭 없이 독립 편집되는가 (격리의 실효성) |
| "플래그가 없으면 현행 동작을 100% 그대로 유지한다" | L1 + L2 | S-1, S-2, S-3 | 잔존 검증 — `--wt` 미사용 경로가 바뀌지 않았는가 |
| "모드 축과 직교하는 축" | L1 | S-3, S-17 | pilot·하네스에 모드 축 오염이 없는가 |
| (채택 관점) 기능이 실제로 **쓸모 있게** 동작하는가 | L2 | **S-25**, **S-26**, S-2 | `status`가 CLOSE 안내의 근거가 되는가 / 설정 부재 시 사용자가 이유를 아는가 / state 값이 실제 경로와 맞는가 |

> **교체형 목표 아님**: 본 태스크는 신규 축 추가이지 구형 대체가 아니므로 "구형 잔존 0" 기준은 적용 대상이 아니다. 다만 "현행 동작 유지"가 잔존 검증 성격을 가지므로 S-1·S-2·S-3으로 커버한다.

---

## 5. 코드 품질

> fix 루프 1/3 반영 후 재측정 (2026-08-15 18:00). 대상은 **092 신규·변경 파일**로 한정한다.

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff check | **Pass** | `worktree_tool.py` → `All checks passed!`. `state_tool.py` 재측정 시에도 매칭 0건 |
| 2 | 타입 체크 | mypy | **Pass** | fix 전 2건(`:146`·`:380` Missing return statement) → `err_response()`에 `-> NoReturn` 어노테이션 1곳 추가로 동시 해소. `Success: no issues found` |
| 3 | 포맷터 | ruff format | **Pass** | `worktree_tool.py` `1 file already formatted`. **`state_tool.py`는 092 범위 밖 기존 포맷이라 의도적으로 미접촉** — 2,600행 전체 포맷은 092 변경 3곳(+8/-1)을 묻어버려 Surgical Changes 위반 |
| 4 | 포맷 후 로직 불변 검증 | PM 직접 | **Pass** | `ERROR_CODES` 18종 불변, 서브명령 4종(create/list/remove/status) 불변, 회귀 349 passed 유지 |
| 5 | pyright | - | **Skip** | 미설치. 신규 설치는 범위 밖(TASK §제약 Simplicity First) |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -inE "(api[_-]?key\|secret\|password\|token\|AKIA[0-9A-Z]{16}\|-----BEGIN)"` on `worktree_tool.py`·`state_tool.py` → 매칭 없음(제외어 필터링 후 0건, 걸린 몇 건은 `_is_safe_artifact_token` 등 무관 식별자). 하드코딩 시크릿 없음 |
| 2 | `.gitignore` 확인 | Pass | 코드 확인: `ensure_gitignore_entry()`(worktree_tool.py L254-274)가 `create` 실행 시 프로젝트 루트 `.gitignore`에 `.opal-worktrees/` 항목을 멱등 추가(부재 시만 write) — S-11 pytest로 실증(`.opal-worktrees/` 1행 유지, 재실행 시 sha256 불변). opal 저장소 자체는 `.opal/worktree.json`이 없어 도구가 아직 호출된 적 없으므로 루트 `.gitignore`에 항목이 없는 것이 정상(도구 미사용 상태) |
| 3 | 커맨드 인젝션 — 모든 git 호출이 리스트 인자이고 `shell=True` 부재 | Pass | `grep -n "shell=True" worktree_tool.py` → 매칭 0건. `_run_git()`(L74-80)이 `subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)` 형태로 리스트 인자만 사용, `shell=True` 전무. 파일 내 모든 git 호출(`_branch_exists`/`_worktree_entries`/`_git_or_raise` 등 11개소)이 `_run_git()` 경유로 동일 계약 유지 확인 |
| 4 | 경로 이탈 — `repos[]`·`copy[]`가 프로젝트 루트 밖을 가리키지 못함 | Pass | `_is_inside()`(L157-164)가 절대경로 즉시 거부 + `os.path.normpath` 후 `project_root` 하위 여부로 판정(심볼릭 링크 미해석, PLAN §3.1.3 결정 고정). `validate_worktree_config()`가 `repos[]`(L189-191)·`copy[]`(L196-198) 각각에 동일 `_is_inside()` 게이트 적용. S-14③(`repos[0].path: "../escape"` → `CONFIG_PATH_ESCAPE` 거부) 실측 통과로 실증 |

## 7. 판정

**Partial Fail -- 시나리오 26/26(S-1~S-17, S-21~S-29) 전건 Pass + 보안 4/4 Pass로 핵심 기능·보안은 문제없으나, §5 코드 품질에서 신규 파일 `worktree_tool.py`에 mypy "Missing return statement" 2건(L146 `load_config`, L380 `_load_meta` — `err_response()`가 실제로는 `sys.exit()`으로 종료하지만 `NoReturn` 애노테이션 부재로 mypy가 오인, 런타임 결함 아님)과 `ruff format --check` 스타일 불일치가 확인되어 "All Pass" 기준을 충족하지 못한다. `state_tool.py`의 나머지 lint/format 지적 사항은 092 diff(1244·2459-2467행) 밖의 pre-existing 코드로 본 태스크 범위 밖임을 diff 대조로 확인했다. L3 3건(S-18·S-19·S-20)은 캡틴 확인 대기이며 본 판정에서 제외한다.**

### PM Gate 체크 (7대 강제 룰)

> **자기 인증 기준 시점: iteration 2 반영 후(시나리오 28건 / 가설 21건).** iteration 1 시점 수치(23행·H-1~H-16)를 그대로 두어 실제와 어긋났던 것을 정정했다(iteration 2 권고 R-3).

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (§0.3에 "mock 금지" 명시, 실 git 저장소 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (**21행**, 빈 칸 0 — iteration 2 fixture 4종 포함. S-29는 기존 fixture 재사용)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (**29행** — S-24~S-29 포함)
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-18·S-19·S-20)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (**H-1~H-22** + H-목표 전건 연결)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — **면제**. §0.2에서 트리거 3종(FE 화면·인증/인가·외부 API) 전부 미해당임을 근거와 함께 판정 (iteration 2 Evaluator가 "면제 정당" 확인)
- [x] **목표 커버** — TASK 요구사항 F-1~F-9 전건 + 완료기준 ①~⑦ 전건이 §4.1·§4.2에 매핑되고, 목표달성 시나리오 **S-23**(격리 실효성)·**S-24**(파이프라인 관통)·**S-18**(실환경 2슬롯)이 존재

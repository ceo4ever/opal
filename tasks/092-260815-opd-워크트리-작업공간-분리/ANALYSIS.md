# ANALYSIS: 태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)

> 작성일: 2026-08-15
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·플랫폼 분기 금지사항 |
| D-2 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards·모듈 구조(§2)·State(§3)·OPAL Tools(§9) |
| D-3 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | TASK 채번·오케스트레이터 공통 영역 스텝 순서 |
| D-4 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 워커 컨텍스트 주입 5단계 + 템플릿 |
| D-5 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷·트랙별 매트릭스 |
| D-6 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `cmd_init`(1138-1309)·argparse(2445-2461)·`cmd_validate`(1686-1743)·`validate_pipeline_spec`(941-) — 검증 방식 실측 |
| D-7 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | 루트 `additionalProperties:false`(줄7) — 신규 필드 추가 지점 |
| D-8 | 소스 | git_sync_tool.py | `opal/tools/git-sync-tool/git_sync_tool.py` | 최신 신설 도구 골격 — ERROR_CODES·ok/err 응답·subprocess 패턴 |
| D-9 | 소스 | git-sync-tool run.sh | `opal/tools/git-sync-tool/run.sh` | run.sh 래퍼 표준 형태 |
| D-10 | 소스 | opal-pilot-dev/SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | Harness 모드 파싱(10-19)·STEP 1(22-30)·STEP 6 CLOSE(236-264) |
| D-11 | 소스 | pipeline.json (opd) | `opal/skills/opal-pilot-dev/references/pipeline.json` | task_steps[] 구조·gate 필드 실례 |
| D-12 | 소스 | install-mac.sh | `scripts/install-mac.sh:1112-1189` | 도구 배포 — `install_dir` 일괄복사 + 개별 `chmod +x` 블록 |
| D-13 | 소스 | opal-project-init/SKILL.md | `opal/skills/opal-project-init/SKILL.md:66-80` | `.gitignore` 멱등 추가 기존 패턴(setting.local.json) — F-7 재사용 지점 |
| D-14 | 소스 | code-scan.json (본 프로젝트) | `.opal/code-scan.json` | exclude 배열 실측 — `.opal-worktrees` 부재 확인 |
| D-15 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` §158-161 | 브랜치 전략 기존 규칙 — C-4 브랜치 네이밍과 표기 차이 발견 |
| D-16 | 설계 | AGENT.md (opal-task-agent) | 본 워커 시스템 프롬프트 | "cwd 매 Bash 호출 리셋 — 절대경로만 사용" 기존 워커 규범, F-6 근거 강화 |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/worktree-tool/` (전체) | **신설 대상** — F-1(스키마)·F-2(CLI) | 신규 생성 | - |
| `opal/tools/git-sync-tool/git_sync_tool.py` | 참조 골격 — ERROR_CODES/ok_response/err_response/`_run_git` 패턴 | 참조만(수정 없음) | `git_sync_tool.py:23-42, 49-56` |
| `opal/tools/git-sync-tool/run.sh` | 참조 골격 — venv python 위임 래퍼 | 참조만 | `run.sh:1-10` |
| `opal/tools/state-tool/state_tool.py` | F-5 대상 — `cmd_init`에 `--worktree` 옵션 추가 | 수정 필요 | `state_tool.py:1138-1245, 2445-2461` |
| `opal/tools/state-tool/schema/state.schema.json` | F-5 대상 — 루트 `properties`에 `worktree` optional 필드 추가 | 수정 필요 | `state.schema.json:6-8`(`additionalProperties:false`) |
| `opal/core/references/opal-harness.md` | F-3 대상 — 신규 절(`--worktree`/`--wt` 축) 추가 | 수정 필요 | `opal-harness.md:71-131`(§2 모듈 구조 인접) |
| `opal/core/references/harness/task-process.md` | F-4 대상 — 오케스트레이터 공통 영역에 worktree 생성 스텝 삽입 | 수정 필요 | `task-process.md:33-53`(스텝 3-6 사이) |
| `opal/core/references/pm/dispatch-process.md` | F-6 대상 — 워커 컨텍스트 주입 템플릿에 경로 계약 추가 | 수정 필요 | `dispatch-process.md:81-105`(템플릿 블록) |
| `opal/skills/opal-pilot-dev/SKILL.md` | F-8 대상 — STEP 6 CLOSE에 안내 스텝 추가 | 수정 필요 | `SKILL.md:236-264`(STEP 6, 5스텝 구조) |
| `opal/skills/opal-project-init/SKILL.md` | F-7 대상 — `.gitignore` 멱등 추가 로직 재사용/확장 | 수정 필요(확장) | `SKILL.md:66-80`(공통: setting.local.json 보장 절) |
| `.opal/code-scan.json` (본 프로젝트 + revup/mams) | 추가 조사 항목 — `.opal-worktrees` exclude 필요성 | **F-item 미지정, PLAN 판단 필요** | `.opal/code-scan.json:9-10`(`exclude` 배열) |
| `scripts/install-mac.sh` | worktree-tool 배포 등록 — 개별 chmod 블록 추가 | 수정 필요 | `install-mac.sh:1112-1189` |
| `docs/CONVENTIONS.md` | 브랜치 네이밍 기존 규칙과 C-4 표기 차이 | **불일치 발견 — 결정 필요** | `CONVENTIONS.md:158-161` |
| `opal/templates/` | F-1 템플릿(유형 A/B) 저장 위치 | 신규 파일 추가 | `opal/templates/`(현재 `test-tools.yaml` 1개만 존재) |

### 1.2 아키텍처 패턴

**도구 신설 2계보 비교** (D-6, D-8):

| 항목 | `state-tool`(성숙형) | `git-sync-tool`(경량 신설형) | `worktree-tool`(신설 예정)이 따를 모델 |
|------|---------------------|----------------------------|--------------------------------------|
| 파일 구성 | `state_tool.py`(2604줄) + `run.sh` + `schema/*.json`(2개) + `tests/`(2파일) + `README.md` | `git_sync_tool.py`(237줄) + `run.sh` + `tests/`(conftest+1파일) | git-sync-tool 규모(경량) + state-tool의 `schema/` 디렉토리(설정파일 검증 대상 있음) |
| 응답 계약 | `ok(command, **kwargs)` / `err(command, code, ...)` — `state_tool.py:151-158` | `ok_response(**kwargs)` / `err_response(code, path=None, exit_code=1)` — `git_sync_tool.py:29-42` | 동일 패턴(`{"ok": bool, "error": code\|None, ...}`, 단일 라인 JSON, `ensure_ascii=False`) |
| 에러 카탈로그 | `ERROR_CODES = {...}` dict, 23종+ (D-2 §3 인용) | `ERROR_CODES = {...}` dict, 2종 — 명시적으로 "`state_tool.py:66-100` 패턴" 참조 주석 포함(`git_sync_tool.py:21`) | dict 기반 카탈로그 — F-2 AC의 "실패 시 error 필드에 에러 코드" 요건과 정합 |
| subprocess 호출 | 해당 없음(git 미호출) | `_run_git(args, repo_path)` — `["git", *args]` 리스트 방식, `shell=True` 금지(injection 방지 주석 명시, `git_sync_tool.py:46`) | worktree-tool도 동일 원칙 필수 — `git worktree add`/`sparse-checkout`/`branch` 전부 리스트 인자 |
| 스키마 검증 방식 | **`jsonschema` 라이브러리 미사용** — `cmd_validate`(1686-1743)·`validate_pipeline_spec`(941-)는 hand-rolled 필드별 체크. `state.schema.json`은 문서 참조용 SSOT이지 런타임 강제 대상이 아님 — `state_tool.py` 전체에서 `state.schema.json`을 로드하는 코드가 없고 유일한 언급이 주석 1줄(`state_tool.py:464`)이다 ※PM 정정 | 스키마 파일 없음(단순 CLI라 불필요) | **worktree.json 검증도 hand-rolled 함수로 작성** — 단 사유는 "의존성 부재"가 아니라 **프로젝트 관행 일치**다 ※PM 정정 |
| run.sh 래퍼 | `$HOME/.opal/.venv/bin/python` 존재 확인 → `exec` 위임(`run.sh:4-12`) | 동일(`run.sh:4-10`, 1줄 차이 없음 — 완전 동형) | 그대로 복제 |
| CLI 골격 | `argparse` + `subparsers(dest="subcommand", required=True)`, 서브파서마다 `set_defaults(func=...)`(`state_tool.py:2598-`) | 동일 패턴(`git_sync_tool.py:225-233`), 서브커맨드 1개(`sync`)뿐 | worktree-tool은 4서브커맨드(create/list/remove/status) — state-tool 규모에 더 가까움 |

**배포 등록 패턴** (D-12): `install-mac.sh:1113-1114`의 `install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"`가 `opal/tools/` 전체를 **일괄 복사**하므로 신규 `worktree-tool/` 디렉토리는 **자동으로 배포된다** — 디렉토리 추가만으로 별도 등록 코드가 필요 없다. 단, `run.sh` 실행 권한(`chmod +x`)은 도구별 개별 블록이 필요하다 — `state-tool`(1124-1129)·`git-sync-tool`(1169-1174)·`backlog-tool`(1176-1181) 등 총 8개 블록이 순차 나열되어 있고, 각 블록은 `if [[ -f "$X_run" ]]; then chmod +x ...; fi` 3줄 형태로 완전히 동형이다. **worktree-tool도 이 패턴을 그대로 복제하는 신규 블록 1개**(어느 기존 블록 뒤든 순서 무관, 최신 블록인 `backlog-tool`/`opal-action-monitor` 뒤에 추가하는 것이 관례 — `install-mac.sh:1176-1189`)가 필요하다.

**`.gitignore` 멱등 추가 기존 패턴** (D-13, F-7 재사용 지점): `opal-project-init/SKILL.md:66-80` "공통: 프로젝트 로컬 설정(setting.local.json) 보장" 절이 정확히 F-7이 요구하는 패턴을 이미 구현하고 있다 —
1. 대상 파일(`setting.local.json`) 존재 확인
2. 없으면 생성
3. **생성한 경우에만** `.gitignore`에 한 줄 추가(이미 있으면 스킵) — "생성한 경우" 조건이 미묘하다. worktree-tool의 경우는 "매 `create` 실행 시" 멱등 검사(파일 신설 여부와 무관하게 항상 grep 검사 후 없으면 추가)가 필요하므로, opi 패턴을 **그대로 복제하지 않고 조건을 "실행할 때마다 무조건 존재 검사"로 일반화**해야 한다(F-7 AC: "2회 실행해도 정확히 1개 행"). opi 쪽 F-7 요구사항은 이 절 안에 `.opal-worktrees/` 라인을 병렬로 추가하는 형태로 확장하면 된다.

### 1.3 의존성 맵

```
사용자 invocation ("//opd --wt 작업")
  └─ PM(오케스트레이터)
       ├─ opal-harness.md Read (Phase B 부트스트랩에서 이미 Eager 로드 — D-2)
       │    └─ [F-3] 신규 §: --worktree/--wt 축 정의 (여기서 "인지"가 발생)
       ├─ STEP 1 TASK → task-process.md Read (D-3, §4 stub: "TASK 단계 진입 시" 전 pilot 공통)
       │    └─ [F-4] 오케스트레이터 공통 영역 스텝 3-6 사이에 worktree 생성 훅 삽입
       │         └─ worktree-tool create 호출 (신규, F-1/F-2)
       │              ├─ .opal/worktree.json 읽기 (F-1 스키마, 프로젝트별 선언)
       │              ├─ git worktree add [+ sparse-checkout] (git CLI subprocess)
       │              └─ .gitignore 멱등 추가 (F-7 계층 1)
       ├─ state-tool init --worktree <path> (F-5) → state.json에 조건부 필드 기록
       ├─ 워커 디스패치 (STEP 2/3/4 등) → dispatch-process.md (D-4)
       │    └─ [F-6] "문서 루트/코드 루트" 2필드 조건부 삽입 (--wt 사용 시만)
       └─ STEP 6 CLOSE (opal-pilot-dev/SKILL.md, D-10)
            └─ [F-8] 5번째 안내 스텝(no-op 비차단) — worktree-tool remove 3중 가드는 캡틴이 별도 시점에 수동 호출
```

**핵심 의존 순서**: F-1(스키마) → F-2(도구) → F-4(훅이 도구를 호출) → F-5(도구 실행 결과를 state에 기록) 순으로 하위 의존성이 있다. F-3(하네스 SSOT 정의)·F-6(디스패치 계약)·F-7(gitignore)·F-8(CLOSE 안내)·F-9(캐시)는 F-1/F-2와 병렬 진행 가능하다.

### 1.4 테스트 현황

- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py` + `conftest.py` — pytest 기반, 임시 git 저장소를 fixture로 생성해 `discover_targets`/`process_repo`를 검증하는 패턴(worktree-tool 테스트가 동일하게 임시 git 저장소 + `git worktree add` 실측으로 검증 가능 — mock 금지 원칙과 정합, `opal/core/references/harness/coding-principles.md` §4 참조 대상).
- `opal/tools/state-tool/tests/test_state_tool.py`(5600줄+) — `cmd_init` 관련 테스트가 이미 방대하므로, F-5의 `--worktree` 추가는 **기존 회귀 스위트 전체가 그대로 pass해야 하는 하위호환 검증 대상**이다(TASK 완료기준 ⑦ "회귀 테스트 전량 pass"와 직결).
- worktree-tool 자체는 신설이므로 테스트 0건 — F-2 AC의 회귀 테스트는 신규 작성이 전제.

## 2. 외부 조사 결과

### 2.1 git worktree + sparse-checkout cone mode 명령 시퀀스

문서/컨텍스트7 조사 불필요 — git 표준 기능이며 프로젝트에 설치된 git 2.50.1(TASK.md 실측)이 사양을 충족한다(cone mode는 git 2.25+). 경험 기반 표준 시퀀스(citation-rules §5 "추론/경험 기반 결정" — 인용 생략 허용):

**유형 A (multi-repo, 코드 레포마다 개별 worktree)**:
```bash
# 코드 레포 자신의 .git 컨텍스트에서 실행 (예: storelink6, revup-front 각각)
git -C /path/to/storelink6 worktree add -b feat/OP-TASK-092 \
  {project_root}/.opal-worktrees/task_092/workspace/backend <base-ref>
git -C /path/to/revup-front worktree add -b feat/OP-TASK-092 \
  {project_root}/.opal-worktrees/task_092/workspace/frontend <base-ref>
```

**유형 B (monorepo, 루트 레포 1개 + sparse-checkout)**:
```bash
git worktree add --no-checkout -b feat/OP-TASK-092 \
  {project_root}/.opal-worktrees/task_092 <base-ref>
git -C {project_root}/.opal-worktrees/task_092 sparse-checkout init --cone
git -C {project_root}/.opal-worktrees/task_092 sparse-checkout set workspace
git -C {project_root}/.opal-worktrees/task_092 checkout feat/OP-TASK-092
```
`--no-checkout` 선행 후 sparse-checkout 패턴을 설정하고 마지막에 checkout하는 순서가 불필요한 전체 체크아웃(및 이후 스파스 축소로 인한 파일 삭제)을 피한다.

**remove 3중 가드 판정에 필요한 git 조회**: dirty=`git status --porcelain`(git-sync-tool과 동일 패턴, D-8:123), unpushed=`git rev-list @{u}..HEAD --count` 또는 upstream 부재 시 별도 처리, 미머지=`git branch --merged <base>`에 브랜치명 포함 여부. 이 3가지는 이미 git-sync-tool의 `process_repo`(D-8:83-183)가 유사 판정 로직(behind/ahead/upstream 조회)을 구현해두었으므로 코드 재사용보다는 **판정 순서 패턴**(detached→no-upstream→dirty→...)을 그대로 차용할 수 있다.

### 2.2 버전 호환성

- git 2.50.1(로컬 실측, TASK.md) — sparse-checkout cone mode(2.25+) 요구사항 충족.
- Python 3(state-tool·git-sync-tool과 동일 스택) — `~/.opal/.venv` 공유, 신규 의존성 불필요(표준 라이브러리 `argparse`/`json`/`pathlib`/`subprocess`만으로 구현 가능, state_tool.py:19-27 "표준 라이브러리만 import" 원칙과 정합).

## 3. 영향 범위

### 3.1 직접 영향

- 신규: `opal/tools/worktree-tool/{worktree_tool.py, run.sh, schema/worktree.schema.json, tests/}`
- 신규: `opal/templates/worktree-type-a.json`, `opal/templates/worktree-type-b.json`(또는 동등 명명)
- 수정: `opal/tools/state-tool/state_tool.py`(`cmd_init` 확장, argparse 1행), `schema/state.schema.json`(properties 1개 추가)
- 수정: `opal/core/references/opal-harness.md`(신규 절), `opal/core/references/harness/task-process.md`(스텝 삽입), `opal/core/references/pm/dispatch-process.md`(템플릿 블록 추가)
- 수정: `opal/skills/opal-pilot-dev/SKILL.md`(STEP 6에 6번째 스텝)
- 수정: `opal/skills/opal-project-init/SKILL.md`(gitignore 보장 절 확장)
- 수정: `scripts/install-mac.sh`(chmod 블록 1개)
- 수정(캡틴 로컬 환경, 코드 아님): `UV_CACHE_DIR` 셸 프로파일

### 3.2 간접 영향

- **pilot 9종**(opds/opdw/opp/opwt/oppd/opsdd/oppl/opdd/opgc) — F-3·F-4 설계상 이들 SKILL.md는 무변경이어야 하며(§1.3 의존성 맵에서 확인한 바와 같이 opal-harness.md·task-process.md는 모든 pilot이 무조건 Read하는 공통 문서이므로 구조적으로 전파 가능. §5에서 상세 근거 제시), 실제 diff 0 여부는 PLAN/EXECUTE 단계에서 검증 대상.
- **`revup`·`mams` 프로젝트의 `.gitignore`**(TASK.md D-5 인용) — F-7 수동 계층(3계층 중 1개)이 직접 파일 변경 대상이나, 본 태스크의 실측 검증 환경일 뿐 OPAL 저장소 산출물은 아니다.
- **`.opal/code-scan.json`**(본 프로젝트 및 향후 revup/mams) — `.opal-worktrees` 미체크 시 code-scan이 worktree 내부(코드 사본)를 중복 스캔할 가능성(§5 리스크 R-4).
- **existing state.json 파일들**(과거 태스크 산출물) — F-5가 optional 필드이므로 기존 파일 무변화(재작성 없음), 하위호환 영향 없음.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `state-tool init`에 `--worktree` 신규 옵션(하위호환, optional)
- [x] 설정/환경변수 변경 — `UV_CACHE_DIR`(캡틴 로컬), `.opal/worktree.json`(신규 옵트인 설정 파일)
- [x] 빌드/배포 파이프라인 변경 — `install-mac.sh`에 worktree-tool chmod 블록 추가

## 4. 핵심 발견 사항

1. **F-3의 핵심 우려("SSOT 1곳 정의만으로 pilot이 `--wt`를 인지할 수 있는가")는 구조적으로 해소된다.** `opal-harness.md`는 Phase B(PM tier) 부트스트랩에서 프로젝트 진입 시 **무조건 Eager 로드**되고(`docs/ARCHITECTURE.md` §부트스트랩 진입 모델), 각 pilot SKILL.md의 `## Harness` 절도 "부트스트랩에서 로드되지 않은 경우: Read한다"는 폴백을 명시한다(D-10:12). 또한 `task-process.md`는 `opal-harness.md` §4 stub에 "TASK 단계 진입 시" 로드로 등록되어 있고, 모든 pilot의 STEP 1(TASK)이 "opal-harness.md 'TASK 공통 프로세스' 참조"로 이를 호출한다(D-10:22-23 확인, task-process.md 자체도 "적용 주체: PM(오케스트레이터)"로 pilot 중립적). 즉 `opal-harness.md`(축 정의, F-3)와 `task-process.md`(생성 훅, F-4) 두 문서 모두 **10종 pilot이 공통으로 무조건 Read하는 경로**이므로, pilot SKILL.md를 건드리지 않고도 `--wt` 인지·집행이 전파된다. C-9의 "pilot 10종 미변경" 전제가 실제로 성립한다.
2. **`state.json`의 `additionalProperties:false`는 런타임에 강제되지 않는다.** `cmd_validate`(D-6:1686-1743)와 `validate_pipeline_spec`(D-6:941-)은 dict 기반 hand-rolled 필드 체크만 수행하며, `state_tool.py` 어디에서도 `state.schema.json`을 로드해 검증하지 않는다(전체 파일에서 해당 문자열의 유일한 등장이 주석 1줄 — `state_tool.py:464`). 즉 F-5의 `worktree` 필드 추가는 **실행 리스크가 없다**(스키마 문서만 갱신하면 되고, 별도 검증 로직 수정 불필요) — TASK 지시문이 우려한 "스키마 위반 시 전체 회귀" 시나리오는 이 프로젝트 구조상 발생하지 않는다. 다만 문서 SSOT로서의 정합성을 위해 `state.schema.json` properties 갱신은 여전히 수행해야 한다.

   > **[PM 정정 — 2026-08-15]** 초안은 위 결론의 근거로 "`jsonschema` 라이브러리가 프로젝트 전체(`requirements.txt`)에 부재"를 들었으나 이는 **사실이 아니다**. `~/.opal/.venv`에 `jsonschema 4.26.0`이 실제로 설치되어 있으며(`~/.opal/.venv/bin/python -c "import jsonschema"` 실측), state-tool에는 `requirements.txt` 자체가 없다. 결론(런타임 미강제 → F-5 리스크 없음)은 "코드가 스키마를 로드하지 않는다"는 실측만으로 그대로 성립하므로 유지한다. 다만 **F-1 설계 시 "jsonschema를 쓸 수 없어서 hand-rolled로 간다"는 전제를 세우면 안 된다** — 라이브러리는 사용 가능하며, hand-rolled를 택하는 근거는 어디까지나 기존 도구(state-tool)와의 관행 일치다. PLAN에서 이 선택을 근거와 함께 명시적으로 결정할 것.
3. **`worktree-tool`은 신규 의존성 없이 기존 관행만으로 F-1의 "스키마 검증 함수" 요건을 충족한다.** state-tool의 `validate_pipeline_spec`이 이미 "hand-rolled 검증 함수 + `.schema.json` 문서" 조합의 선례이므로, `worktree.json`도 동일 패턴(`validate_worktree_config()` 함수 + `worktree.schema.json` 참조 문서)으로 구현하면 프로젝트 전체의 검증 방식과 완전히 일치한다.
4. **`install-mac.sh`의 도구 배포는 2단 구조다** — 디렉토리 자체는 `install_dir` 일괄 복사로 자동 배포되지만, `run.sh` 실행 권한만은 도구별 개별 `chmod` 블록이 필요하다(D-12). 이 블록을 빠뜨리면 `worktree-tool/run.sh`가 배포는 되어도 실행 권한이 없어 `Permission denied`로 실패한다 — 놓치기 쉬운 배포 체크포인트.
5. **F-7의 `.gitignore` 멱등 추가는 opi에 이미 실증된 패턴이 있으나, 조건 트리거가 다르다.** opi는 "파일을 새로 생성한 경우에만" gitignore 라인을 추가하는 1회성 조건(D-13:79)인 반면, F-7은 "worktree-tool create를 실행할 때마다" 무조건 존재 검사 후 추가하는 반복 호출형 멱등이 필요하다 — 코드를 그대로 복사하면 안 되고 조건을 일반화해야 한다.
6. **브랜치 네이밍 표기 불일치 발견.** `docs/CONVENTIONS.md:158-161`(D-15)의 기존 "브랜치 전략"은 예외 분기 형식을 `feat/{NNN}-{스킬약어}-{설명}`(예: `feat/092-opd-워크트리`)로 정의하는 반면, TASK.md C-4는 worktree 기본 브랜치 템플릿을 `feat/OP-TASK-{NNN}`(예: `feat/OP-TASK-092`)로 확정했다. 두 규칙이 서로 다른 프로젝트(OPAL 저장소 자체 vs worktree 대상 프로젝트인 revup/mams)에 적용되는 것이라면 문제가 없으나, 문서상 명시적 구분이 없어 **용어 불일치**로 분류한다(citation-rules.md §7, decision_required 후보 — PLAN 단계에서 "이 두 브랜치 네이밍 규칙이 서로 다른 적용 대상임을 명시할 것인지" 확정 필요).
7. **F-4 롤백 정책이 TASK.md 확정 방향에 명시되지 않은 진짜 공백이다.** task-process.md의 기존 오케스트레이터 공통 영역(D-3:33-53)은 "폴더 생성 → 모드 기록 → state init" 순서로 실패 처리 절차가 없다(각 스텝이 실패할 가능성을 상정하지 않은 선형 절차). `worktree-tool create`가 이 스텝들 사이에 삽입되면 "태스크 폴더는 이미 생성됐는데 worktree 생성이 실패"하는 부분 실패 상태가 최초로 발생한다 — PLAN 단계에서 명시적 정책(예: 실패 시 `--wt` 없이 진행할지 물어보고 재시도 여부를 사용자에게 확인)이 필요하다.

## 5. 제약/리스크

| # | 리스크 | 심각도 | 근거 |
|---|--------|--------|------|
| R-1 | 브랜치 네이밍 규칙 불일치 — CONVENTIONS.md 기존 `feat/{NNN}-{스킬약어}-{설명}` ↔ TASK.md C-4 `feat/OP-TASK-{NNN}` | 중 | `docs/CONVENTIONS.md §158-161` ↔ TASK.md §C-4 |
| R-2 | F-4 부분 실패 시 롤백/재시도 정책 미정의 — 태스크 폴더 생성 후 worktree 생성 실패 시 상태 불명 | 중 | `opal/core/references/harness/task-process.md:33-53`(기존 절차에 실패 분기 없음) |
| R-3 | `worktree-tool remove` 3중 가드 중 "미머지" 판정은 `base-ref`(비교 대상 브랜치)를 알아야 하는데, `.opal/worktree.json`의 `branchTemplate`만으로는 base가 자동 결정되지 않음(어느 브랜치 대비 미머지인지 — main? 현재 HEAD?) | 중 | TASK.md F-8 AC(가드 3종) — base 판정 근거 문서 없음, PLAN에서 확정 필요 |
| R-4 | `code-scan.json`의 `exclude` 배열에 `.opal-worktrees` 미등록 시, worktree 내부(코드 사본)가 `workspace/`와 중복 스캔되어 `@header` 커버리지 지표가 왜곡될 가능성 | 낮 | `.opal/code-scan.json:9-10`(exclude 배열 실측 — 유사 항목 `tasks`/`specs` 이미 등록) |
| R-5 | F-6 "절대경로 주입"은 기존 dispatch 템플릿(ANALYSIS/PLAN/EXECUTE 디스패치 프롬프트)이 관행적으로 상대경로 형태(`{tasks/{NNN}-{name}/}`)를 써온 것과 표기가 다르다 — worktree 태스크에서만 절대경로 규칙을 신설하면 동일 필드가 태스크 유형에 따라 다른 표기 규칙을 갖게 되어 워커 혼란 가능 | 낮 | `opal/core/references/pm/dispatch-process.md:81-105`(기존 템플릿), 대비 워커 시스템 프롬프트 "cwd 매 Bash 리셋 — 절대경로만 사용" 기존 규범(D-16) — 규범 자체는 이미 존재하므로 신규 도입 리스크는 낮음 |
| R-6 | F-9 캐시 볼륨 진단은 `os.stat().st_dev` 비교가 플랫폼 독립적(POSIX 표준)이나 Windows에서는 `st_dev` 의미가 달라 진단이 부정확할 수 있음 — 단, TASK 제약이 "차단하지 않는다"(경고만)이므로 오탐이 있어도 치명적이지 않음 | 낮 | TASK.md F-9 AC "차단하지 않는다" |
| R-7 | worktree-tool의 git 호출은 `git-sync-tool` 패턴(리스트 인자, `shell=True` 금지)을 반드시 따라야 하나, `sparse-checkout`/`worktree add -b`처럼 인자 개수가 가변적인 명령이 많아 인젝션 방지 원칙을 지키면서도 옵션 조합을 다양화해야 하는 구현 복잡도가 git-sync-tool 대비 높음 | 낮 | `opal/tools/git-sync-tool/git_sync_tool.py:46-56`(`_run_git` 고정 패턴) |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3 | `~/.opal/.venv` 공유(state-tool·git-sync-tool과 동일) |
| CLI | Bash (`run.sh` 래퍼) | - |
| VCS | git | 2.50.1(로컬 실측, TASK.md) — sparse-checkout cone mode 요구 2.25+ 충족 |
| 문서 | Markdown | 하네스·참조 문서 SSOT |
| 테스트 | pytest | `opal/tools/{state-tool,git-sync-tool}/tests/` 기존 관행 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음 — 프레임워크 내부 도구/문서 작업, 외부 프레임워크 스킬 불필요) | - |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음 — 표준 git/Python 기능만 사용, 외부 라이브러리 문서 조회 불필요) | - |

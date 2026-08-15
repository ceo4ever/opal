# ADD_DONE-1: `worktree.json` 온보딩 경로 신설 (`worktree-tool init`)

> 추가작업 번호: **ADD-1** | 시작: 2026-08-15 19:05 | 완료: 2026-08-15 19:45 (KST)
> 원본 완료 기록 `DONE.md`는 보존하며 수정하지 않는다.

## 1. 사유

092 본편 완료 후 캡틴이 **"`worktree.json`은 언제 만들어지나"**를 물었고, 다른 세션의 알투도 같은 지점을 짚었다. 실측 결과 **구현에도 규범에도 생성 경로가 없었다**.

| 경로 | 실측 |
|------|------|
| `worktree-tool` | `load_config()`로 읽기만. 서브명령 4종(`create`/`list`/`status`/`remove`)에 생성 기능 없음 |
| `opi` | `.gitignore` 한 줄만 멱등 보장 |
| 하네스 §2.5 (3) | 부재 시 "템플릿 경로를 **안내**한다"까지 |
| 파이프라인 스텝 4.5 | `create` 실패 시 `--wt` 없이 계속 |

즉 **도구는 완성됐지만 첫 사용자가 진입할 문이 없었다.** PM이 revup·mams 실환경 검증에서 두 번 다 `cat >`로 손수 만들었으면서 갭으로 인지하지 못했다.

### 왜 빠졌나 (원인 사슬)

1. **TASK 요구사항에 없었다** — F-1은 "스키마 정의 + 템플릿 **제공**"까지. 범위 포함 9항목·제외 목록 어디에도 "생성"이 없어 **논의 대상 자체가 아니었다**.
2. **설계 대화가 "무엇이 필요한가"에서 멈췄다** — C-3는 "프로젝트가 선언해야 한다"까지 도출했으나 **그 파일이 어떻게 존재하게 되는지**는 묻지 않았다.
3. **어떤 게이트도 못 잡는다** — ANALYSIS는 지정된 접합면만, 목표-커버 게이트는 "TASK 요구사항 **전체가** 매핑되는가"를 본다. **요구사항 자체에 없으면 커버리지 100%로 통과한다.** 070이 "목표를 검증하는 시나리오 부재"였다면 이건 한 단계 위인 **"요구사항 자체의 부재"**다.

## 2. 변경 내용

### `worktree-tool init` 신설 (4서브명령 → 5)

**자동 생성이 아니라 탐지 기반 초안 생성**이다. `code-scan init`의 비대화형 초안 생성 패턴을 따랐다.

| 탐지 단계 | 규칙 | revup | mams |
|---|------|-------|------|
| 1 | 어디에도 git 레포가 없으면 `NOT_A_GIT_REPO` | 통과 | 통과 |
| 2 | 루트 이하 3 depth 독립 `.git` 탐색 | **2개** | **0개** |
| 3 | ≥1 → `multi-repo`, repos = 발견 경로(정렬) | ✅ | — |
| 4 | 0 → `monorepo`, repos = 추적 최상위 중 manifest 보유 | — | ✅ `["workspace"]` |
| 5 | 후보 0개 → `LAYOUT_UNDETERMINED` 거부(추측 금지) | — | — |

`setup[]`은 lock 파일로 결정론 매핑(`uv.lock`→`uv sync`, `pnpm-lock.yaml`→`pnpm install`, `bun.lock`→`bun install`. gradle·maven은 생성 안 함). **repos 이하 depth 2까지** 탐색하며 `node_modules`·`.venv`·`.git`·`dist`·`build`·`.next`는 제외한다.

**추측하지 않는 것** — `copy[]`는 빈 배열(후보는 `_copy_candidates` 주석 키로만), `portOffset`은 0. 잘못 복사하면 슬롯에 엉뚱한 자격증명이 들어간다.

**멱등·안전** — 기존 파일 있으면 `CONFIG_EXISTS` 거부(sha256 불변), `--force`로만 덮어씀, `--dry-run`은 쓰지 않고 `draft` 키 반환.

### 문서 반영

- `opal-harness.md` §2.5 (3) — "템플릿 경로 안내" → **`worktree-tool init` 실행 안내**로 교체
- `opal/core/references/tools.md` — `init` 커맨드 + 변경이력(4→5서브명령)

## 3. 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/tools/worktree-tool/worktree_tool.py` | `init` 서브명령 + 탐지 5단계 + 깊이 확장. `_find_independent_git_dirs`·`_tracked_top_level_dirs`·`_has_manifest_beneath`·`_find_monorepo_candidates`·`_detect_setup`·`_detect_copy_candidates`·`_build_init_draft`·`cmd_init`·`_iter_setup_search_dirs`·`_BUILD_ARTIFACT_DIR_NAMES` |
| `opal/tools/worktree-tool/tests/test_worktree_tool.py` | S-30 10건 + S-31 5건 추가 (기존 41건 무수정) |
| `opal/tools/worktree-tool/tests/conftest.py` | import 1건 추가, 기존 fixture 시그니처 불변 |
| `opal/core/references/opal-harness.md` | §2.5 (3) 갱신 + 변경이력 v7.1 |
| `opal/core/references/tools.md` | `init` 커맨드 + 변경이력 v2.14 |
| `PLAN.md` | DEC-8 · DEC-8 보충(3건) · **PM 정정 — 보충 #2** · DEC-8 보충 2 · H-23 · H-24 |
| `TEST-SCENARIO.md` | S-30 · S-31 · H-23 · H-24 + §7 자기 인증 수치 갱신 |

신규 `ERROR_CODES` 2종: `CONFIG_EXISTS` · `LAYOUT_UNDETERMINED` (`NOT_A_GIT_REPO`는 기존 재사용)

## 4. 검증 결과

opd 추가작업 검증 기준(전체 테스트 스위트 + PM Gate 문서검증)을 적용했다.

| 항목 | 결과 |
|------|------|
| 전체 회귀 | **364 passed** (worktree-tool **56** + state-tool 308) |
| 신규 시나리오 | S-30 10/10 · S-31 5/5 |
| 기존 회귀 | 41건 무손상 (테스트 파일 무수정) |
| 코드 품질 | mypy 0 · `ruff check` All passed · `ruff format` 통과 |
| 배포 | install 재실행, `run.sh init --help` 정상 |

### 실환경 실측 (2유형)

| | layout | repos | setup | `_copy_candidates` |
|---|---|---|---|---|
| **revup** | `multi-repo` | `workspace/backend`·`workspace/frontend` | `bun install` 1건 | 3건 |
| **mams** | `monorepo` | `workspace` | **4건**(`uv sync` + `pnpm install` ×3) | **12건** |

양쪽 `--dry-run`에서 **파일 미생성** 확인. `copy: []`·`portOffset: 0` 추측 금지 유지.

## 5. 이 추가작업에서 잡힌 것

### (1) 실환경이 또 결함을 잡았다 — 두 번째

`init` 구현 후 pytest **51 passed** 상태에서 mams 실측 결과가 `setup: []`이었다. `_detect_setup()`이 repos 경로 **바로 아래(depth 1)만** 봤기 때문이다. multi-repo는 repos가 코드 레포 자신이라 우연히 맞았고(revup `workspace/frontend/bun.lock`), monorepo는 repos가 상위 디렉토리 하나라 한 단계 더 깊어 전부 놓쳤다.

**pytest가 놓친 이유**: `test_s30_3`이 lock을 repos 바로 아래 두는 fixture로만 검증해 depth 가정이 드러나지 않았다.

본편 S-29(왕복 경로 없음)에 이어 **두 번 모두 원인이 "fixture가 실환경 구조를 재현하지 않음"**이었다.

### (2) PM 단독 오판이 코드까지 가지 않았다

DEC-8 보충 #2에서 PM이 "multi-repo도 루트가 git 레포여야 한다"고 확정했으나 **틀렸다**. **테스트 실물을 읽지 않고 RED 워커의 요약 보고만으로 판단**한 오류다 — 워커 보고의 "root도 `git init` 추가"는 `test_s30_1` 얘기였고, `test_s30_6`은 루트에 `.git`이 없는 기존 `project_a` fixture를 재사용하고 있었다.

GREEN 워커가 구현 단계에서 이를 잡아 보고했고, PM이 임시 워크스페이스로 실증해(루트 git 없는 멀티레포에서 `init`→`create`→worktree 생성 전부 정상) 정정했다. **작성자·확정자·구현자 3자 분리**가 의도한 것 이상으로 작동했다.

### (3) 워커 3명이 모두 임의 판단 대신 에스컬레이션했다

RED 워커가 DEC-8 미규정 3건(`--dry-run` 응답 키·루트 git 필수 여부·플래그명)을 블로커로 올렸다. 특히 두 번째는 fixture 전제가 걸린 문제라 틀렸으면 4개 케이스가 잘못된 계약을 고정했을 것이다.

## 6. 알려진 특성 (결함 아님)

mams `init` 결과의 `setup[]`에 `workspace/frontend_test`·`workspace/frontend_wireframe`이 포함된다. 두 디렉토리는 mams의 보조 디렉토리라 실무상 설치가 불필요하다.

**결함이 아니라 설계 경계**다 — 도구는 "lock 파일이 있으면 setup 후보"라는 결정론 규칙만 알고, **어느 디렉토리가 실제로 쓰이는지는 프로젝트만 안다**. 도구가 "보조 디렉토리 같으니 빼자"고 판단하면 그게 더 위험한 추측이며 DEC-8 §추측하지 않는 것의 정신에 어긋난다. `init`은 **초안 생성**이고 `_help`에 검토·수정을 명시하므로 사용자가 2줄 지우면 된다.

이름 패턴(`*_test`·`*_wireframe`) 제외를 검토했으나 프로젝트마다 의미가 달라 오탐이 더 크다고 판단해 채택하지 않았다(Simplicity First).

## 7. 후속 과제

| # | 내용 |
|---|------|
| 1 | `opi`가 프로젝트 초기화·최신화 시 `init`을 함께 제안할지 — 현재는 `--wt` 첫 사용 시점에만 안내한다 |
| 2 | 본편 후속 3건은 그대로 유효 (pilot 9종 `--wt` 실사용 미검증 / `state_tool.py` 기존 포맷 / mams `cmux.json` 심볼릭 링크) |
| 3 | **"요구사항 자체의 누락은 어떤 게이트로도 검출되지 않는다"** — 이번 사건의 구조적 원인. CLOSE 회고에서 개선 후보로 기록한다 |

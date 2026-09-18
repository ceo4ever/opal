# REGRESSION-EVIDENCE — OP-TASK-119 비워크트리 바이트 동일 회귀 증거와 배포 검증

> W-8 (실행 그룹 P2) 산출물. 완료 기준 연결: AC-14, C-1, C-2 / 담당 시나리오 S-19, S-24.
> 측정 일시: 2026-09-12 KST. 측정자: EXECUTE 워커(opal-task-agent).
> **이 문서는 측정·판정만 기록한다. W-8은 소스 코드를 한 줄도 수정하지 않았고 실 `~/.opal/`에 배포하지 않았다.**

---

## 0. 측정 대상과 좌표

| 항목 | 값 |
|---|---|
| 허브 | `/Volumes/Data/AIStudio/workspace/ai-framework` |
| 변경 전 기준(base) | `20c38a4` — 119 브랜치 분기 직전 `main` |
| 변경 후 기준(after) | `a5bfb77` — 현재 `main`(119 머지 완료) |
| base 소스 clone | `/private/tmp/op119w8/src_base` (측정 후 삭제) |
| after 소스 clone | `/private/tmp/op119w8/src_after` (측정 후 삭제) |
| 고정 데이터 루트 | `/private/tmp/op119w8/fix` — **비워크트리** 일반 프로젝트 fixture 1개 (측정 후 삭제) |
| 진입 계약 | `state-tool verify --plan-contract-check` → `pass` (W-1~W-10 10건 인식) |
| 진입 계약 | `state-tool verify --code-scan-citation-check` → `pass` |

### 0.1 실험 설계 — 왜 "데이터 고정 · 코드만 스왑"인가

PLAN §Release and recovery 원문과 brain `byte-identical-proof-requires-data-root-fixed`가 지시하는 설계를 그대로 적용했다.

이 태스크는 도구가 **읽는 데이터**(`harness/worktree.md`·`harness/task-process.md`·`.opal/worktree.json`)를 함께 바꿨다.
따라서 "base clone에서 실행 ↔ 허브에서 실행" 대조는 코드 차이와 데이터 차이가 동시에 개입해 C-1이 묻는
"**코드 변경이 비워크트리 실행의 출력을 바꿨는가**"를 판정하지 못한다.

그래서 아래 설계로 측정했다.

- **데이터 루트 고정** — `/private/tmp/op119w8/fix`에 비워크트리 프로젝트 fixture를 1회 만들고 두 실행 사이 전혀 건드리지 않는다.
  fixture 내용은 전부 **base 스냅샷**에서만 복사했다: 실태스크 1건(`tasks/109-260906-opds-태스크루트-해석-수렴`),
  `.opal/worktree.json`(= `20c38a4` 시점 내용, `taskCapsuleCone` **없음** — 전환 전 기존 프로젝트를 재현),
  `.opal/AGENT.md`·`.opal/code-scan.json`·`.opal/MEMORY.json`·`.opal/setting.local.json`, code-scan 대상 소스(`opal/tools/memory-tool/`).
  fixture는 자체 git 레포(`9f23832`)로 초기화해 실행 중 변형 여부를 `git status`로 판정 가능하게 뒀다.
- **도구 코드만 스왑** — **단일 고정 배포 경로** `/private/tmp/op119w8/home_swap/.opal`에
  ① base 소스로 `install-mac.sh` → 캡처 → ② 같은 경로에 after 소스로 `install-mac.sh` → 재캡처.
  배포 루트 절대경로가 양쪽 동일하므로 **정규화 0회, `cmp`로 바이트 동일을 직접 판정**한다.

`HOME`을 `home_before`/`home_after`로 나눈 1차 시도도 병행했는데, 출력 중 `manifest_path`가 `HOME` 절대경로를
그대로 싣기 때문에 6개 중 `event-loader` 1건만 2바이트 차이가 났다(`home_before` ↔ `home_after` 문자열).
이는 격리 HOME 인공물이지 동작 차이가 아니며(동 응답의 `manifest_sha256`은 양쪽 동일),
**정규화를 피하라**는 지시에 따라 위의 고정 경로 스왑을 주 증거로 채택했다. 아래 판정은 전부 고정 경로 스왑 결과다.

### 0.2 [MUST] C-1 대조 범위에서 제외한 표면과, 실제로는 제외가 불필요했다는 실측

PM 확정 해석에 따라 **신규 CLI 표면**(`--help`·argparse `usage:`·인자 없는 호출·오용 호출)은 대조 대상에서 제외했다.
argparse는 서브명령·플래그가 늘면 `usage:` 줄이 필연적으로 달라지므로, C-1의 "바이트 동일"은
**기존 동작 경로의 출력**을 뜻한다는 것이 그 근거다.

다만 이번 변경에 한해서는 **그 제외가 결과적으로 불필요했다**. 실측 결과:

| 제외 예정 표면 | base ↔ after |
|---|---|
| `worktree-tool --help` | stdout·stderr·exit(0/0) 전부 **바이트 동일** |
| `worktree-tool` (인자 없음) | stdout·stderr·exit(2/2) 전부 **바이트 동일** |
| `worktree-tool create --help` | stdout·stderr·exit(0/0) 전부 **바이트 동일** |

근거: `git diff 20c38a4 main -- opal/tools/worktree-tool/worktree_tool.py`의 `add_argument`/`add_parser` 변경이 **0건**이다.
119는 서브명령도 플래그도 추가하지 않았고, `task_path_source`는 기존 응답에 붙는 **additive 출력 필드**다.
제외 규칙은 계약으로 유지하되, 이번 판정은 그 예외를 쓰지 않고 성립한다.

### 0.3 변경 표면의 구조적 경계 — 왜 비워크트리 실행이 영향을 받지 않는가

`worktree_tool.py`의 6개 서브명령 본문을 base/after에서 함수 단위로 추출해 `cmp`했다.

| 함수 | base ↔ after |
|---|---|
| `cmd_list` | UNCHANGED |
| `cmd_create` | UNCHANGED |
| `cmd_remove` | UNCHANGED |
| `cmd_init` | UNCHANGED |
| `cmd_status` | **CHANGED** |
| `cmd_finalize` | **CHANGED** |

신규 `_resolve_canonical_task_path`(구 `_assert_task_path_unambiguous`)의 호출부는 배포본 기준
`worktree_tool.py:1074`(`cmd_status`)와 `:1420`(`cmd_finalize`) **2곳뿐**이다.
두 명령은 모두 `.opal-worktrees/.meta/task_{NNN}.json` registry 항목을 전제로 하는 워크트리 경로 명령이므로,
`--wt`를 쓰지 않는 실행(C-1의 정의)에는 구조적으로 도달하지 않는다.
아래 §1은 그 구조적 경계를 **실행 출력으로** 확인한 것이다(문구 존재 확인이 아니다).

---

## 1. 비워크트리 바이트 동일 (S-19 / AC-14 / C-1) — 판정: **PASS**

### 1.1 캡처 명령 전문

```bash
R=/private/tmp/op119w8
export HOME="$R/home_swap"            # 양쪽 실행이 동일한 배포 절대경로를 쓴다
F="$R/fix"                            # 고정 데이터 루트 (비워크트리)
TASK="$F/tasks/109-260906-opds-태스크루트-해석-수렴"

"$HOME/.opal/tools/state-tool/run.sh"    show "$TASK"
"$HOME/.opal/tools/state-tool/run.sh"    validate "$TASK"
"$HOME/.opal/tools/worktree-tool/run.sh" list --project-root "$F"
"$HOME/.opal/tools/memory-tool/run.sh"   show --file "$F/.opal/MEMORY.json" --boot-brief
node "$HOME/.opal/tools/code-scan/code-scan.js" scan --project-root "$F"
"$HOME/.opal/tools/event-loader/run.sh"  load --event session.project --project-root "$F"
```

각 명령의 **stdout / stderr / exit code를 개별 파일로** 캡처했다. 스왑 순서:
`install(base) → 캡처 6건 → install(after, 같은 HOME) → 캡처 6건 → cmp 18쌍`.
두 install 모두 종료코드 0.

### 1.2 대조 결과 — 18쌍 전부 차이 0줄

| # | 명령 | stdout | stderr | exit | stdout sha256(앞 16) base / after |
|---|---|---|---|---|---|
| 1 | `state-tool show` | 동일 | 동일 | 0 / 0 | `5e3aa588f6e00725` / `5e3aa588f6e00725` |
| 2 | `state-tool validate` | 동일 | 동일 | 0 / 0 | `08c62a593a726078` / `08c62a593a726078` |
| 3 | `worktree-tool list` | 동일 | 동일 | 0 / 0 | `c30e25fd06245200` / `c30e25fd06245200` |
| 4 | `memory-tool show --boot-brief` | 동일 | 동일 | 0 / 0 | `235860a87a3a3717` / `235860a87a3a3717` |
| 5 | `code-scan scan` | 동일 | 동일 | 0 / 0 | `1593d203b29639d2` / `1593d203b29639d2` |
| 6 | `event-loader load --event session.project` | 동일 | 동일 | 0 / 0 | `5b7ec4ec85ed9077` / `5b7ec4ec85ed9077` |

`cmp` 판정: **18/18 IDENTICAL, 정규화 0회, 차이 0줄.** C-1 위반 0건.

stderr는 6건 모두 0바이트다. 출력 실물(after 쪽, base와 바이트 동일):

```
$ worktree-tool list --project-root /private/tmp/op119w8/fix
{"ok": true, "error": null, "command": "list", "project_root": "/private/tmp/op119w8/fix", "layout": "monorepo", "entries": []}

$ state-tool validate .../tasks/109-...
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}
```

### 1.3 대조가 공허하지 않다는 실증 (non-vacuity)

같은 fixture에 base/after를 각각 별도 `HOME`으로도 설치해, 스왑이 실제로 코드를 바꿨는지 해시로 확인했다.

| 배포 파일 | base sha256(앞 12) | after sha256(앞 12) | |
|---|---|---|---|
| `tools/worktree-tool/worktree_tool.py` | `b20943b927a7` | `2bb746daa1e4` | DIFF |
| `references/harness/worktree.md` | `a18d07c60a66` | `b37c205630be` | DIFF |
| `references/harness/task-process.md` | `b4ecf1338bd4` | `f283e8bb253e` | DIFF |
| `references/pm/dispatch-process.md` | `b89a70ed151d` | `118c6221a0fe` | DIFF |
| `skills/opal-pilot-dev/SKILL.md` | `b9b07dfbcd6c` | `f83724856e15` | DIFF |
| `skills/opal-pilot-dev-short/SKILL.md` | `114c6db7b967` | `649058ace844` | DIFF |

6/6 실제로 달라진 상태에서 출력이 18/18 동일했다 — 대조는 공허하지 않다.

### 1.4 데이터 루트 불변 실증

캡처 12회 후 fixture 레포의 `git status --porcelain` 출력 줄 수 **0**.
즉 어떤 도구도 고정 데이터 루트를 변형하지 않았고, 두 캡처가 같은 입력을 본 것이 확인된다.

### 1.5 이 증거가 커버하지 않는 범위 (과대주장 방지)

- fixture는 **비워크트리**이므로 `worktree-tool list`의 `entries`는 빈 배열이다. 워크트리가 등록된 상태의
  `list`·`status`·`finalize` 출력은 이 문서가 판정하지 않는다 — §0.3대로 `cmd_status`·`cmd_finalize`는
  의도된 변경 대상이고, 그 실증은 **W-9(FIXTURE-EVIDENCE.md)** 소관이다.
- C-1의 문언이 "`--wt`를 쓰지 않는 실행"이므로 위 범위 한정은 계약 축소가 아니다.

---

## 2. install 경유 source→installed 동치와 배포 누락 (S-19 / C-2) — 판정: **PASS**

### 2.1 실행 방식과 그 사유 — 실 `~/.opal/` 미배포

`install_opal()`이 `opal_home`을 `"$USER_HOME/.opal"`로 하드코딩하고 비표준 경로를 `OPAL_HOME` 가드로 거부하므로,
`OPAL_HOME`으로는 대상을 바꿀 수 없다. 따라서 **`HOME` 환경변수로만 격리**했다(직전 태스크 118 W-14 실측 방법).

```bash
HOME=/private/tmp/op119w8/home_swap OPAL_AUTO_INSTALL=1 \
  bash /private/tmp/op119w8/src_after/scripts/install-mac.sh </dev/null
```

실 `~/.opal/`은 이 태스크에서 **한 번도 install 대상이 아니었다**. 그 실증:

| 실 배포본 파일 | 실 `~/.opal/` sha256(앞 12) | 판정 |
|---|---|---|
| `tools/worktree-tool/worktree_tool.py` | `b20943b927a7` | base와 동일 = **119 미배포** |
| `references/harness/worktree.md` | `a18d07c60a66` | base와 동일 = **119 미배포** |
| `references/pm/dispatch-process.md` | `b89a70ed151d` | base와 동일 = **119 미배포** |

`references/pm/dispatch-process.md`의 실 배포본 해시는 이 워커의 `worker.dispatch` receipt가 검증한 값과도 일치한다.
실 배포는 소유자가 P4 직전 1회 수행한다(C-2·PLAN §Release and recovery).

### 2.2 배포 누락 — 0건

after 소스(`a5bfb77`)와 배포본 `home_swap/.opal`(및 `home_after/.opal`)을 파일 단위로 대조했다.

| 소스 트리 | 배포 대상 | 소스 파일 수 | 배포 누락 |
|---|---|---|---|
| `opal/skills/` | `.opal/skills/` | 121 | **0** |
| `opal/agents/` | `.opal/agents/` | 21 | **0** |
| `opal/core/references/` | `.opal/references/` | 50 | **0** |
| `opal/tools/` | `.opal/tools/` | 408 | **0** |
| `skills/` | `.opal/skills/` | 21 | **0** |
| **합계** | | **621** | **0** |

### 2.3 이번 변경 파일의 source→installed 바이트 동치

119가 바꾼 배포 대상 6파일을 소스와 배포본으로 직접 `cmp`했다.

| 배포 경로 | source(`a5bfb77`) ↔ installed |
|---|---|
| `tools/worktree-tool/worktree_tool.py` | **BYTE-EQ** |
| `references/harness/worktree.md` | **BYTE-EQ** |
| `references/harness/task-process.md` | **BYTE-EQ** |
| `references/pm/dispatch-process.md` | **BYTE-EQ** |
| `skills/opal-pilot-dev/SKILL.md` | **BYTE-EQ** |
| `skills/opal-pilot-dev-short/SKILL.md` | **BYTE-EQ** |

배포본에 119 변경 내용이 실제로 실렸다: `references/harness/worktree.md`의 `taskCapsuleCone` 2회,
`tools/worktree-tool/worktree_tool.py`의 `task_path_source` 3회.

**`.opal/worktree.json`은 install 배포 대상이 아니다.** 이 파일은 프로젝트 데이터(허브 `.opal/`)이며
`~/.opal/` 어디에도 배포되지 않는다(`find $HOME/.opal -name worktree.json` → 0건).
W-4의 변경은 허브 레포 커밋으로만 적용되고 install과 무관하므로, "배포 누락" 판정 모수에서 제외된다.

### 2.4 install 부작용 — Console 데몬 기동, 조치 완료

PM 경고대로 `OPAL_AUTO_INSTALL` 경로가 `install_dashboard()`를 태워 Console 데몬을 `127.0.0.1:7823`에 띄웠다
(install 3회 각각 PID 54822 / 59760 / 스왑 2회). 매 install 직후 `opal-cli console stop`으로 종료했고,
최종 상태에서 `lsof -nP -iTCP:7823 -sTCP:LISTEN` 결과 **리스너 0건(포트 해제 확인)**, 해당 PID 전부 소멸.

---

## 3. 배포 선결 조건 검사 (S-24 / H-4) — 판정: **조건 충족**

### 3.1 실측

```bash
H=/Volumes/Data/AIStudio/workspace/ai-framework
git -C $H rev-parse main                              # a5bfb77622183cde8eaac64c1d86b15db058ba36
git -C $H rev-parse feat/OP-TASK-119                  # 25b8a8c3c9caa749afd766885753fac84cd391d9
git -C $H merge-base main feat/OP-TASK-119            # 25b8a8c... == 119 tip  → 119는 main에 완전 머지됨
git -C $H log --oneline main..feat/OP-TASK-119 | wc -l # 0  → main에 미반영 119 커밋 없음
```

119 브랜치 분기점은 `20c38a4`이고, 현재 `main`은 그 위에 119 머지 커밋을 포함한 `a5bfb77`이다.
**119는 이미 `main`에 머지됐으므로 배포 선결 조건은 충족 상태다.**

### 3.2 그러나 — 배포는 반드시 `main` 체크아웃에서 해야 한다 (H-4 실 위험 정량)

`main`에는 119 tip 이후 커밋 3건이 더 있다.

```
a5bfb77 merge(119): 워크트리 태스크 캡슐 소유권 브랜치 귀속
81363d1 feat(120): GC 검사 역량 공통 스킬 분리 — op-gc-* 3종 신설과 pilot thin wrapper 전환
f1f96ee chore(119): 태스크 산출물과 제안서 아카이브 헤더 귀속
```

`install_opal()`은 `skills`·`agents`·`references`·`templates`·`tools`·`dashboard-server`를 `rm -rf` 후 복사한다.
따라서 **119 워크트리(`.opal-worktrees/task_119`, `25b8a8c`)에서 install을 실행하면 태스크 120의 배포분이 조용히 롤백된다.**
롤백 대상 실측 — 배포 경로 파일 **17건**:

```
M  opal/agents/opal-convention-checker/AGENT.md        M  opal/agents/opal-security-checker/AGENT.md
M  opal/core/references/agents.md                      A  opal/core/references/harness/gc-finding-schema.md
M  opal/core/references/opal-skills-registry.json      A  opal/skills/op-gc-convention/SKILL.md
A  opal/skills/op-gc-report/SKILL.md                   A  opal/skills/op-gc-report/references/report-template.md
A  opal/skills/op-gc-security/SKILL.md                 M  opal/skills/opal-pilot-gc/SKILL.md
M  scripts/tests/task113_bootstrap_audit.py            R  opal/skills/opal-pilot-gc/references/* → op-gc-*/references/* (5건)
```

### 3.3 [MUST] 실 배포 전 확인 절차 (소유자가 P4 직전 1회 실행)

```bash
H=/Volumes/Data/AIStudio/workspace/ai-framework

# ① 119가 main에 전부 반영됐는가 — 0이어야 한다
test "$(git -C $H log --oneline main..feat/OP-TASK-119 | wc -l)" -eq 0 || { echo "STOP: 119 미머지 — merge 선행"; exit 1; }

# ② 배포 소스가 main 체크아웃인가 — 워크트리/브랜치 체크아웃에서 install 금지
test "$(git -C $H rev-parse HEAD)" = "$(git -C $H rev-parse main)" || { echo "STOP: HEAD != main"; exit 1; }

# ③ 배포 경로에 미커밋 변경이 없는가
git -C $H status --porcelain -- opal/skills opal/agents opal/core/references opal/tools skills   # 출력 0줄

# ④ 위 3건 통과 후에만
bash $H/scripts/install-mac.sh
```

불일치 시 배포를 중단하고 rebase/merge를 선행한다. 이 절차는 W-8의 게이트이며 PLAN H-4 설계 대응의 집행이다.

---

## 4. 실패 복구 기준 — 어긋난 캡처 ↔ 소관 W 매핑

이번 측정에서 어긋난 항목은 **0건**이므로 아래는 재발 시 적용할 판정표다.

| 어긋난 캡처 | 1차 의심 소관 | 되돌릴 대상 |
|---|---|---|
| `worktree-tool list` / `state-tool show`·`validate` | **W-1** | `opal/tools/worktree-tool/worktree_tool.py` |
| `event-loader load --event session.project` | **W-2 / W-3** | `opal/core/references/harness/worktree.md`, `harness/task-process.md` |
| 비워크트리 프로젝트에서 cone·sparse 동작 변화 | **W-4** | `.opal/worktree.json` (`taskCapsuleCone` 키 제거 → 기본 `[]` 전개는 no-op) |
| 파일럿 스킬 경유 디스패치 출력 변화 | **W-5 / W-6** | `opal/skills/opal-pilot-dev/SKILL.md`, `opal-pilot-dev-short/SKILL.md` |
| `worker.dispatch` 프롬프트·receipt 계약 변화 | **W-7** | `opal/core/references/pm/dispatch-process.md` |
| `code-scan scan` / `memory-tool show --boot-brief` | 119 변경 대상 아님 | 119 외 원인(타 태스크·데이터) 먼저 의심 |

P2 시점은 실 배포 전이므로 복구는 `git restore`(소스) + 격리 HOME 삭제 + `/private/tmp` fixture 폐기로 끝난다.

---

## 5. fixture 잔여물과 허브 무결성 (C-8)

### 5.1 사용한 임시 자원 — 전부 `/private/tmp/op119w8` 하위

`src_base`, `src_after`, `fix`(고정 데이터 루트), `home_before`, `home_after`, `home_swap`, 캡처 디렉터리·로그.
총 5.7G. Git 조작은 전부 `git -C <dir>` 형식으로만 수행했고 `cd` 후 git 호출은 사용하지 않았다.
운영 `.opal-worktrees/` 하위에는 fixture worktree를 만들지 않았다.

W-9 소유 자원(`/private/tmp/op119w9*`, `FIXTURE-EVIDENCE.md`)은 열람·수정하지 않았다.

### 5.2 삭제 실증 — 잔여물 0건

```
$ rm -rf /private/tmp/op119w8
$ ls -d /private/tmp/op119w8*
zsh: no matches found: /private/tmp/op119w8*     → 잔여물 0건
$ lsof -nP -iTCP:7823 -sTCP:LISTEN
(출력 없음)                                       → 포트 해제
```

### 5.3 허브 무결성 (삭제 후)

```
$ git -C <허브> rev-parse main
a5bfb77622183cde8eaac64c1d86b15db058ba36          → 측정 전과 동일

$ git -C <허브> worktree list
<허브>                           a5bfb77 [main]
<허브>/.opal-worktrees/task_119  25b8a8c [feat/OP-TASK-119]   → 측정 전과 동일, 신규 worktree 0건
```

작업 트리의 `docs/proposals/opal-pm-direct-execution.md`·`opal-task-run-log.md` 수정은 **동시 실행 중인 다른 주체의 변경**이며
W-8은 이 두 파일을 포함해 허브의 어떤 소스 파일도 수정하지 않았다. W-8의 유일한 변경 파일은 이 문서다.

---

## 6. 최종 판정

| 시나리오 | 완료 기준 | 결과 |
|---|---|---|
| S-19 | AC-14, C-1 — 비워크트리 실행 바이트 동일 | **PASS** — 6명령 × (stdout·stderr·exit) = 18쌍 전부 차이 0줄, 정규화 0회 |
| S-19 | C-2 — 소스만 수정, install로 배포 | **PASS** — 배포 누락 621/0, 변경 6파일 source↔installed 바이트 동일, 실 `~/.opal/` 미배포 확인 |
| S-24 | H-4, C-2 — 배포 선결 조건 | **PASS(조건 충족)** — 119 완전 머지(`main..119` = 0건). 단 배포는 `main` 체크아웃에서만 (§3.3 절차) |
| C-8 | 임시 fixture 격리·회수 | **PASS** — `/private/tmp/op119w8` 전량 삭제, 잔여물 0건, 허브 무결 |

블로커 없음. 소스 코드 수정 0건.

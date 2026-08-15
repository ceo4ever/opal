# PLAN: 태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)

> 작성일: 2026-08-15 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 9개)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 태스크 파이프라인에 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교하는 `--worktree`/`--wt` 축**을 신설하여, 태스크별 코드 작업본을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리한다. 규칙은 산문이 아니라 신규 `worktree-tool`이 집행하고(→ D-3 Core Stance), pilot 10종 SKILL.md는 건드리지 않는다(F-8의 opd CLOSE 안내 1스텝만 예외). 플래그를 쓰지 않으면 `state.json` 스키마·STATE.md 렌더·디스패치 프롬프트가 전부 현행과 바이트 동일해야 한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `.opal/worktree.json` 스키마 + 검증 함수 + 유형 A/B 템플릿 | TASK F-1 | P0 | 없음 |
| F-002 | `worktree-tool` 신설 — create/list/remove/status | TASK F-2 | P0 | F-001 |
| F-003 | `--worktree`/`--wt` 축 하네스 SSOT 정의 | TASK F-3 | P0 | 없음 (계약은 본 PLAN이 확정) |
| F-004 | TASK 후처리 worktree 생성 훅 | TASK F-4 | P0 | F-002, F-005 |
| F-005 | `state-tool init --worktree <path>` 영속화 | TASK F-5 | P0 | 없음 |
| F-006 | 워커 디스패치 경로 계약 (문서 루트/코드 루트 2필드) | TASK F-6 | P1 | 없음 |
| F-007 | `.gitignore` 멱등 추가 — 도구 계층 + opi 계층 | TASK F-7 | P0 | F-002(도구 계층) |
| F-008 | CLOSE 정리 안내 게이트 + `remove` 3중 가드 | TASK F-8 | P0 | F-002 |
| F-009 | `UV_CACHE_DIR` 이전 + 볼륨 불일치 진단 | TASK F-9 | P1 | F-002(진단 부분만) |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ──> F-002 ──┬──> F-004 ──(F-005 결과 소비)
                  ├──> F-007(도구 계층)
                  ├──> F-008(remove 가드)
                  └──> F-009(b: 볼륨 진단)

F-003 ────────────────────(독립·병렬)
F-005 ────────────────────(독립·병렬) ──> F-004
F-006 ────────────────────(독립·병렬)
F-007(opi 계층) ──────────(독립·병렬)
F-009(a: UV_CACHE_DIR) ───(독립·병렬, 캡틴 로컬 환경)
```

근거: ANALYSIS §1.3 "F-1(스키마) → F-2(도구) → F-4(훅이 도구를 호출) → F-5(도구 실행 결과를 state에 기록) 순으로 하위 의존성이 있다. F-3·F-6·F-7·F-8·F-9는 F-1/F-2와 병렬 진행 가능하다" (→ D-2 §1.3).

---

## 1.4 확정 결정 사항 (DEC-1 ~ DEC-5)

ANALYSIS가 "PLAN에서 확정 필요"로 이관한 5건을 여기서 종결한다. 하위 설계·체크리스트는 전부 이 결론을 전제로 작성되었다.

### DEC-1 — 브랜치 네이밍 두 규칙의 관계 (R-1 종결)

**결론**: 두 규칙은 **적용 대상이 다른 별개 규칙이며 통일하지 않는다.** 대신 `docs/CONVENTIONS.md` §브랜치 전략에 적용 범위를 명시하는 2줄을 추가한다.

| 규칙 | 적용 대상 | SSOT |
|------|----------|------|
| `feat/{NNN}-{스킬약어}-{설명}` | **OPAL 저장소 자체**의 예외적 브랜치 분리 | `docs/CONVENTIONS.md` §브랜치 전략 |
| `feat/OP-TASK-{NNN}` (기본값) | **worktree 대상 프로젝트의 코드 레포**(revup·mams 등)에서 `worktree-tool`이 생성하는 브랜치 | `.opal/worktree.json`의 `branchTemplate` |

근거:
- [MUST] `docs/CONVENTIONS.md` §브랜치 전략: "`main`: 안정 브랜치이자 **기본 작업 브랜치** — 태스크 커밋은 브랜치 분리 없이 main에 직접 수행한다." → OPAL 저장소는 브랜치 분리 자체가 예외 경로이므로, worktree 브랜치 규칙과 충돌할 지점이 구조적으로 없다.
- TASK.md §C-4는 캡틴 확정 사항이므로 기본값 `feat/OP-TASK-{NNN}`은 변경 대상이 아니다. 프로젝트별 조정은 `branchTemplate` 오버라이드로 흡수한다.
- 문제의 실체는 "규칙 충돌"이 아니라 "적용 범위 미표기"였다(citation-rules.md §7.2 "다름의 발견"). 표기를 채우면 해소된다.

**CONVENTIONS.md 갱신 필요 여부 = 필요(§4.2 Step 16, 영역 `문서`, agent `PM 직접`).** 추가 문안:
> - 위 규칙은 **OPAL 저장소 자체**에만 적용된다. `--worktree`/`--wt`로 생성하는 대상 프로젝트의 코드 브랜치는 `{프로젝트}/.opal/worktree.json`의 `branchTemplate`(기본 `feat/OP-TASK-{NNN}`)을 따르며, 본 절의 적용 대상이 아니다.

### DEC-2 — `worktree-tool create` 부분 실패 시 정책 (R-2 종결)

**결론**: 책임을 **도구 계층**과 **파이프라인 계층**으로 분리한다.

| 계층 | 정책 |
|------|------|
| 도구(`worktree-tool create`) | **all-or-nothing.** ① pre-flight 선검사(대상 경로 미존재·브랜치 미존재·repos 경로 실재·git 레포 여부)를 전부 통과해야 첫 `git worktree add`를 시작한다. ② 그럼에도 N번째 레포에서 실패하면 **자기가 만든 worktree·브랜치만** `git worktree remove --force` + `git branch -D`로 되돌리고 `{"ok": false}`를 반환한다. 태스크 폴더·TASK.md·`.gitignore`는 건드리지 않는다. |
| 파이프라인(`task-process.md` 훅) | **비차단 계속(선택지 b).** 태스크 폴더·TASK.md는 이미 사용자 승인 산출물이므로 **롤백하지 않는다.** `--wt` 없이 스텝 5(`state init`)로 진행하고, 실패 사유를 사용자에게 보고한다. |
| `state.json` 기록 시점 | **성공 후에만.** `create`가 `ok: false`면 `state init`에 `--worktree`를 전달하지 않으므로 `worktree` 키가 아예 생성되지 않고 결과적으로 현행 스키마와 동일해진다 — 부분 실패 상태가 state에 남지 않는다. |
| 모드별 동작 | interactive/semi-agentic: 실패 사유 보고 후 계속(사용자가 원하면 수동 재시도). **agentic: 동일하게 자동 계속하되 AGENTIC-LOG.md에 실패 사유를 기록.** 사용자 확인을 요구하지 않으므로 agentic에서 정지하지 않는다. |

근거:
- 선택지 (a)(생성물 롤백 후 중단)를 기각한 이유: 태스크 폴더·TASK.md는 사용자 승인을 거친 산출물이며 자동 삭제는 비가역이다. [MUST] `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다" 계열의 user sovereignty 원칙과, git-sync-tool이 문제 저장소에 "자율 조치(stash/rebase/force/commit/push) 일절 없음 — skip 후 보고만"을 택한 선례(`opal/core/references/tools.md` §git-sync-tool)를 그대로 따른다.
- 선택지 (c)(사용자 재시도 확인)를 기각한 이유: agentic 모드에서 정지가 발생해 지시문의 "agentic 모드에서도 동작해야" 요건을 위반한다.
- 도구 계층 all-or-nothing이 필요한 이유: 유형 A는 레포 N개에 순차 `worktree add`를 하므로, 중간 실패 시 "반쪽 worktree"가 남으면 재실행이 `WORKTREE_EXISTS`/`BRANCH_EXISTS`로 영구 차단된다.

### DEC-3 — `remove` 미머지 판정의 비교 base (R-3 종결)

**결론**: **`create` 시점에 base-ref를 1회 해석해 메타 파일에 동결 기록하고, `remove`는 그 값만 읽는다.** 재해석하지 않는다.

1. **해석 우선순위(`create` 시점, `resolve_base_ref()` 1곳에 봉인)**
   1. `.opal/worktree.json`의 `baseBranch`(선택 키) — 프로젝트가 명시 선언한 경우
   2. `git -C <repo> symbolic-ref refs/remotes/origin/HEAD` → `origin/main` (본 저장소 실측: `refs/remotes/origin/main`)
   3. 위 둘 다 실패하면 해당 레포의 현재 체크아웃 브랜치명
2. **동결 위치**: `{project}/.opal-worktrees/.meta/task_{NNN}.json`
   - **worktree 내부에 두지 않는다** — 유형 B의 worktree 루트에 파일을 두면 sparse-checkout된 작업본에 미추적 파일이 생겨 `git status --porcelain`이 비지 않고 **dirty 가드가 오탐**한다.
   - `.opal-worktrees/`는 F-007이 `.gitignore`에 넣으므로 루트 레포에도 잡히지 않는다.
3. **`remove` 동작**: 메타의 `entries[].base_ref`를 그대로 사용해 `git branch --merged <base_ref>` 포함 여부를 판정한다. 메타 부재 시 `META_NOT_FOUND`로 거부하고 `--force`로만 우회한다.

근거: `remove`는 CLOSE 이후 임의 시점에 캡틴이 단독 호출하므로 태스크 폴더·`state.json` 없이 **worktree 경로만으로 자기완결**이어야 한다. 또한 `origin/HEAD`를 remove 시점에 재조회하면 그 사이 기본 브랜치가 바뀌었을 때 판정이 달라져 비결정론이 된다 — [MUST] `~/.opal/PRINCIPLES.md` Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."

### DEC-4 — `worktree.json` 검증 방식 (F-1 종결)

**결론**: **hand-rolled 검증 함수 `validate_worktree_config()`를 채택한다.** `jsonschema` 라이브러리를 쓰지 않는다.

근거 3가지(ANALYSIS [PM 정정] 반영 — "쓸 수 없다"는 전제는 사용하지 않는다):
1. **미선언 전이 의존성 회피(실측).** `jsonschema 4.26.0`은 `~/.opal/.venv`에 실재하지만 `opal/tools/requirements.txt`에 **선언되어 있지 않다**. `pip show jsonschema` 결과 `Required-by: mcp` — 즉 `mcp>=1.1.0`의 전이 의존성으로만 존재한다. mcp가 의존성을 정리하거나 venv 구성이 달라지면 `worktree-tool`이 `ImportError`로 즉사한다. 직접 쓰려면 `requirements.txt`에 선언을 추가해야 하는데, 이는 [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."에 비추어 이번 요구사항에 비해 과한 런타임 계약 확장이다.
2. **관행 일치.** `state_tool.py`의 `cmd_validate`(`state_tool.py:1686-1743`)·`validate_pipeline_spec`(`state_tool.py:941-`), `git_sync_tool.py` 전체가 표준 라이브러리만 사용한다(`git_sync_tool.py:14-18`). `worktree-tool`만 외부 라이브러리를 끌어들이면 도구 계보가 갈라진다.
3. **에러 코드 입도 요건.** TASK F-1 AC는 "필수 키 누락 / `layout` 무효값 / `repos[]` 경로 이탈 3종을 **각각 고유 에러 코드로**" 거부할 것을 요구한다. `jsonschema`는 단일 `ValidationError`를 던지므로 어차피 코드 매핑 레이어를 손으로 써야 한다 — 라이브러리를 써도 hand-rolled 분량이 줄지 않는다.

`schema/worktree.schema.json`은 state-tool의 `state.schema.json`과 동일하게 **문서 SSOT(사람·AI 참조용)**로 두고 런타임 로드는 하지 않는다(선례: ANALYSIS §4-2 "state_tool.py 어디에서도 state.schema.json을 로드해 검증하지 않는다").

### DEC-5 — `.opal/code-scan.json` exclude에 `.opal-worktrees` 추가 (R-4 종결)

**결론**: **범위에 포함하되 축소한다.**

| # | 조치 | 대상 | 포함 여부 |
|---|------|------|----------|
| (a) | `exclude` 배열에 `".opal-worktrees"` 1개 추가 | **OPAL 저장소 자체** `/Volumes/Data/AiStudio/workspace/opal/.opal/code-scan.json` | **포함**(§4.2 Step 17) |
| (b) | `create` 실행 시 대상 프로젝트 `.opal/code-scan.json`에 항목이 없으면 **비차단 경고** 출력 | worktree 대상 프로젝트(revup·mams 등) | **포함**(§4.2 Step 4, `warnings[]`) |
| (c) | 도구가 남의 `code-scan.json`을 **자동 편집** | 대상 프로젝트 | **제외** |
| (d) | opi 최신화 계층 / code-scan `init` 기본 exclude 변경 / 템플릿 신설 | 신규 프로젝트 | **제외** |

근거:
- (a)는 문자열 1개 추가로 비용이 0이며 R-4(worktree 내부 코드 사본이 중복 스캔되어 `@header` 커버리지 지표 왜곡)를 즉시 제거한다. `exclude` 배열에는 이미 `tasks`·`specs` 같은 동류 항목이 등재되어 있다(`.opal/code-scan.json:9-10` 실측).
- (c)를 제외한 이유: `.gitignore` 미비는 **루트 레포가 worktree 전체를 변경분으로 인식하는 기능 파손급** 결함이라 도구의 자동 수정이 정당하지만(F-7), code-scan exclude 미비는 **지표 왜곡(ANALYSIS R-4 심각도 "낮")**에 그친다. 반면 `code-scan.json`은 사람이 손으로 들여쓴 포맷이라 `json.dump` 재작성이 대규모 diff를 만든다. 이익보다 부작용이 크다.
- (d)를 제외한 이유: [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First — 이번 요구사항(F-7은 `.gitignore` 2계층만 규정)에 없는 확장이다. (b)의 경고가 `--wt`를 실제로 쓰는 프로젝트를 이미 커버한다.

---

### DEC-6 — TASK §제약 "DB 동시성 경고"의 처리 (R-13 종결, PM 판정 2026-08-15)

**결론**: **저비용 형태로 이번 범위에 흡수한다**(§4.2 Step 4에 `diagnose_concurrent_slots()` 추가, H-16 신설).

PLAN 초안은 이 제약이 F-001~F-009 어느 AC에도 편입되지 않았음을 정직하게 지적하고 후속 과제로 넘겼다. PM 판정은 다음과 같다.

- **제외할 수 없는 이유**: TASK.md §제약 조건에 캡틴 확정 사항으로 명시된 항목이다. AC 미편입은 TASK 작성 시점의 누락이지 캡틴이 철회한 것이 아니므로, 조용히 빠지면 "제약이 사라진" 사고가 된다.
- **원안대로 구현할 수 없는 이유**: "스키마 마이그레이션 동반 태스크"인지를 도구가 판정하려면 태스크 성격을 입력받아야 하는데 그 계약이 설계 어디에도 없다. 이를 만들려면 `worktree.json` 스키마 확장 + 파이프라인 입력 추가가 필요해 [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."에 저촉된다.
- **채택안**: 도구가 **실제로 관측 가능한 사실**(동시 활성 슬롯 수)로 경고를 대체한다. 슬롯이 2개 이상이면 공유 자원(개발 DB·포트·compose 프로젝트명) 충돌 주의를 `warnings[]`에 넣는다. 메타 디렉토리 열거만 하므로 `list` 로직 재사용으로 비용이 3줄 수준이고, F-009(b) 볼륨 진단과 **동일한 비차단 경고 계열**이라 새 개념을 도입하지 않는다.
- **경계**: 여전히 **차단하지 않는다**(TASK F-9 AC의 "차단하지 않는다" 원칙 준용). 태스크의 DB 영향 여부 판정은 범위 밖으로 남으며, 필요해지면 `worktree.json`에 선언 키를 추가하는 후속 과제로 다룬다.


### DEC-7 — `remove` 후 재생성 경로 (실환경 결함 대응, PM 판정 2026-08-15)

**배경**: revup 실환경에서 `remove` 성공 후 빈 슬롯 껍데기가 남아 같은 번호 재생성이 `WORKTREE_EXISTS`로 영구 차단되는 결함을 발견했다(AGENTIC-LOG #25). RED 워커가 후속 공백까지 짚었다 — 슬롯 루트만 고치면 이번엔 `BRANCH_EXISTS`에 막힌다. `remove`가 브랜치를 의도적으로 보존하기 때문이다(S-9, user sovereignty).

**PM이 확인한 git 실동작** (임시 저장소 실측):

| # | 검사 | 결과 |
|---|------|------|
| ① | `worktree remove` 후 브랜치 | 잔존 (`feat/X`) |
| ② | `git worktree add <path> <기존브랜치>` | **성공** — 해당 브랜치를 그대로 체크아웃 |
| ③ | 이미 체크아웃 중인 브랜치를 다시 `add` | git이 자체 거부 (`already used by worktree at ...`) |
| ④ | 체크아웃 여부 판별 | `worktree list --porcelain`의 `branch refs/heads/...` 행으로 가능 |

**결론 — 판정 기준을 "존재"에서 "점유"로 바꾼다.**

| 항목 | 변경 전 (결함) | 변경 후 |
|------|--------------|--------|
| 슬롯 존재 판정 | `wt_root` **디렉토리 존재** | **실제 worktree 등록 여부**(`git worktree list`) |
| 브랜치 판정 | 브랜치 **존재**(`_branch_exists`) | 브랜치가 **다른 worktree에 체크아웃 중**인가 |
| 브랜치 존재 + 미점유 | `BRANCH_EXISTS` 거부 | **재사용** — `worktree add <path> <branch>`(`-b` 없이) |
| `remove` 정리 범위 | 레포별 worktree 경로만 | **슬롯 루트(`task_{NNN}/`)까지** 빈 디렉토리 회수. `.opal-worktrees/` 자체와 `.meta/`는 다른 슬롯이 쓸 수 있으므로 남긴다 |

근거:
- `remove`가 브랜치를 보존하는 이유는 **작업이 살아 있기 때문**이다(S-9). 그렇다면 재생성은 그 작업을 다시 펼치는 것이므로 **같은 브랜치를 이어받는 것이 의미상 정확**하다. 새 브랜치명으로 우회하면 `_render_branch()`의 결정론이 깨지고, 명시적 거부는 사용자가 매번 브랜치를 손으로 지우게 만든다.
- 살아 있는 슬롯의 중복 생성 거부(S-27/H-20)는 **여전히 성립한다** — 그 경우 브랜치가 점유 중이므로 ③에 의해 git이 거부하고, 도구는 그 신호를 `BRANCH_EXISTS`로 옮기면 된다. 즉 두 경우가 판정 기준 하나로 자연히 갈린다.
- 재사용 경로는 `worktree add <path> <branch>` **단일 명령**으로 충분하다 — 브랜치를 만들지 않으므로 Step 3 승인 이탈(고아 브랜치 방지용 `--detach` → `checkout -b` 분리)의 대상이 아니다.

**영향**: 신규 가설 **H-22**, 시나리오 **S-29**(5 케이스). S-27(살아 있는 슬롯 거부)은 계약 불변 — 회귀로 지킨다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-005 `state_tool.py cmd_init` | `--worktree` 미지정 시 `state.json`에 `worktree` 키가 생성되면 안 되는 계약. 무조건 대입(`state["worktree"] = args.worktree`)하면 `null` 값 키가 생겨 스키마 `additionalProperties:false`·기존 소비자 파싱을 깬다 | **P0** | L1(단위: 키 부재 assert) + L2(기존 state.json 바이트 대조) | S-1 후보 |
| H-2 | F-003·F-004·F-006 (하네스·참조 문서 3종) | "pilot 10종 SKILL.md diff 0" 계약(TASK C-9). `--wt` 인지를 SSOT에 두지 못하고 pilot에 산문을 복제하면 위반 | **P0** | L1(`git diff --stat opal/skills/opal-pilot-*/SKILL.md` = opd 1파일 외 0) | S-2 후보 |
| H-3 | F-002 `create` 유형 A(multi-repo) | `repos[]` N개 각각에 `git worktree add -b <branch> <target> <baseRef>`가 성공하고, 대상 레이아웃이 메인과 동일(`.opal-worktrees/task_{NNN}/{path}`)해야 하는 계약 | **P0** | L2(임시 bare remote + clone 2개 fixture) + L3(revup 실환경) | S-3 후보 |
| H-4 | F-002 `create` 유형 B(monorepo) | `--no-checkout` → `sparse-checkout init --cone` → `set <repos...>` → `checkout` 순서 계약. 순서가 틀리면 전체 체크아웃 후 축소가 일어나 `tasks/`·`.opal/`이 잠깐 체크아웃됨 | **P0** | L2(sparse fixture: `tasks/`·`.opal/` 미체크아웃 assert) + L3(mams 실환경) | S-4 후보 |
| H-5 | F-008 `remove` 3중 가드 | dirty / unpushed / 미머지 각 조건이 **조건별 고유 에러 코드**로 거부되어야 하는 계약. 판정 순서(dirty→unpushed→unmerged)가 뒤섞이면 단독 조건 테스트가 다른 코드를 반환 | **P0** | L2(각 조건을 단독 성립시키는 fixture 3종 + 전조건 해소 성공 1종 + `--force` 우회 1종) | S-5 후보 |
| H-6 | F-007 `ensure_gitignore_entry()` | "2회 실행 시 중복 0행 · 이미 있으면 **바이트 단위 무변경**" 계약. 항목이 있어도 write를 하면 mtime·개행이 바뀌어 AC 위반 | **P0** | L2(2회 실행 후 행 수 == 1 + `sha256` 동일 assert) | S-6 후보 |
| H-7 | F-002 `create` 롤백 (DEC-2) | N개 중 M번째 실패 시 이미 만든 worktree·브랜치가 남으면 재실행이 `WORKTREE_EXISTS`/`BRANCH_EXISTS`로 영구 차단되는 계약 | **P1** | L2(2번째 repo 경로를 고의로 깨뜨린 fixture → 1번째 worktree·브랜치 부재 assert) | S-7 후보 |
| H-8 | F-002 base-ref 동결 (DEC-3) | `remove`의 미머지 판정이 `create` 시점 base와 동일해야 하는 결정론 계약. remove가 `origin/HEAD`를 재조회하면 그 사이 기본 브랜치 변경 시 판정이 뒤집힘 | **P1** | L2(create 후 `origin/HEAD`를 다른 브랜치로 바꾸고 remove 판정 불변 assert) | S-8 후보 |
| H-9 | F-001 `validate_worktree_config()` | 필수 키 누락·`layout` 무효값·`repos[]` 경로 이탈(`..`/절대경로) 3종이 **각각 다른 에러 코드**여야 하는 계약(F-1 AC) | **P1** | L1(3종 부적합 입력 × 고유 코드 + 유형 A/B 템플릿 2종 통과) | S-9 후보 |
| H-10 | F-002 배포 (`install-mac.sh`) | `install_dir`이 디렉토리를 복사해도 `run.sh` 실행 권한은 개별 chmod 블록이 있어야 부여되는 계약. 누락 시 배포는 되지만 `Permission denied` (ANALYSIS §4-4) | **P1** | L2(install 재실행 후 `test -x ~/.opal/tools/worktree-tool/run.sh`) | S-10 후보 |
| H-11 | F-005 STATE.md 렌더 | `--worktree` 지정 시에도 STATE.md 렌더 결과가 현행과 동일해야 하는 계약(`_build_new_state_md`가 worktree를 참조하지 않음) | **P1** | L2(동일 입력 init을 `--worktree` 유/무로 2회 → STATE.md diff 0) | S-11 후보 |
| H-12 | F-009(b) 볼륨 진단 | 캐시·프로젝트 볼륨 불일치 시 **경고만 하고 차단하지 않는다**는 계약(F-9 AC). `st_dev` 비교가 예외를 던지면 create 전체가 실패 | **P2** | L1(경로 조작 fixture: `ok:true` + `warnings[]` 비어있지 않음) | S-12 후보 |
| H-13 | F-003 하네스 § 번호 삽입 | 신규 절을 `§3`으로 넣으면 이후 `§4`~`§10` 번호가 전부 밀려 프로젝트 전역 인용(`opal-harness.md §9 OPAL Tools` 등)이 dangling이 되는 계약 | **P1** | L1(`grep -rn "opal-harness.md §" opal/ docs/` 결과가 전부 유효 절을 가리키는지 대조) | S-13 후보 |
| H-14 | F-009(a) `UV_CACHE_DIR` 이전 | 비가역 로컬 환경 변경. 이전 후 `uv sync`가 실패하면 mams 개발 환경이 멈춤. 복구 경로가 없으면 치명 | **P0** | L3(실환경: 이전 → `uv cache dir` 확인 → `uv sync` 완주 → `df` 측정 → 복구 절차 리허설) | S-14 후보 |
| H-15 | F-002 lazy setup (TASK C-7) | `create`는 `setup[]`을 **실행하지 않고 열거만** 해야 하는 계약. 실행해버리면 편집만 하는 슬롯에 수 분의 설치 시간이 붙음 | **P2** | L2(`setup`에 sentinel 파일 생성 명령을 넣고 create 후 sentinel 부재 assert + `pending_setup[]` 열거 확인) | S-15 후보 |
| **H-22** | F-002 `remove` 정리 범위 + `create` 재생성 (DEC-7) | `remove` 후 슬롯 루트 잔존 금지 + 같은 번호 재생성 성공(브랜치 재사용) + `list`·`create`의 슬롯 판정 일치. 위반 시 **재작업 영구 차단** | **P0** | L2(S-29 5케이스: 유형 A/B 슬롯 루트 · 재생성 · 판정 일치 · 빈 껍데기 내성) | S-29 |
| H-16 | F-002 동시 슬롯 경고 (DEC-6, PM 추가) | TASK §제약 "DB 동시성 — 도구가 경고한다(차단하지 않는다)" 계약. 경고가 아예 없으면 제약 미충족이고, 반대로 차단하면 "차단하지 않는다"를 위반 | **P2** | L2(슬롯 1개째 경고 부재 → 2개째 경고 출현 + 양쪽 모두 `ok:true` assert) | S-16 후보 |

---

## 2. 기능별 분석

### F-001: `.opal/worktree.json` 스키마 + 검증 함수 + 템플릿

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/tools/worktree-tool/schema/worktree.schema.json` | 스키마 문서 SSOT (런타임 미로드 — DEC-4) | 신규 |
| BE | `opal/tools/worktree-tool/worktree_tool.py` | `load_config()` + `validate_worktree_config()` | 신규 |
| 환경 | `opal/templates/worktree-multi-repo.json` | 유형 A 템플릿 | 신규 |
| 환경 | `opal/templates/worktree-monorepo.json` | 유형 B 템플릿 | 신규 |

#### 2.1.2 현재 구현

부재(신설). 선례는 `opal/tools/state-tool/schema/state.schema.json` — `additionalProperties:false`를 선언하지만 런타임에 로드되지 않고 문서 SSOT로만 기능한다(ANALYSIS §4-2, `state_tool.py:464` 주석 1줄이 유일한 언급). 검증은 `validate_pipeline_spec`(`state_tool.py:941-`)처럼 hand-rolled 필드 체크가 담당한다.

#### 2.1.3 영향 범위

- 피호출자: 없음(표준 라이브러리 `json`/`pathlib`만).
- 호출자: F-002의 `create`/`list`/`remove`/`status` 4서브명령 전부가 진입 시 `load_config()`를 거친다.
- `opal/templates/`는 현재 `test-tools.yaml` 1개뿐이며(ANALYSIS §1.1), `install-mac.sh:1107`의 `install_dir "$opal_dir/templates" "$opal_home/templates"`가 디렉토리를 통째로 배포하므로 파일 추가만으로 자동 배포된다.

---

### F-002: `worktree-tool` 신설 — create/list/remove/status

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/worktree-tool/worktree_tool.py` | 도구 본체 (4서브명령) | 신규 |
| 환경 | `opal/tools/worktree-tool/run.sh` | venv python 위임 래퍼 | 신규 |
| BE | `opal/tools/worktree-tool/tests/conftest.py` | 임시 git 저장소 fixture (유형 A/B) | 신규 |
| BE | `opal/tools/worktree-tool/tests/test_worktree_tool.py` | pytest 스위트 | 신규 |
| 환경 | `scripts/install-mac.sh` | `run.sh` chmod 블록 1개 | 수정 |

#### 2.2.2 현재 구현

부재(신설). 골격 참조 대상은 `git-sync-tool`(경량 신설형, 237줄):
- `ERROR_CODES` dict + `ok_response(**kwargs)` / `err_response(code, path=None, exit_code=1)` — `git_sync_tool.py:23-42`
- `_run_git(args, repo_path)` — `["git", *args]` **리스트 인자, `shell=True` 금지**(injection 방지 주석 명시) — `git_sync_tool.py:46-56`
- `argparse` + `subparsers(dest="subcommand", required=True)` + `set_defaults(func=...)` — `git_sync_tool.py:225-233`
- `run.sh`는 `$HOME/.opal/.venv/bin/python` 존재 확인 후 `exec` 위임하는 10줄 — `opal/tools/git-sync-tool/run.sh:1-10`

테스트 선례는 `opal/tools/git-sync-tool/tests/conftest.py` — `tmp_path`에 bare remote + 상태별 clone 8종을 subprocess로 구성하고, **공개 인터페이스(CLI 호출)로만 검증하며 내부 함수 import를 금지**한다(`conftest.py` `run_sync_cli` docstring). mock/patch 금지.

#### 2.2.3 영향 범위

- 상위 의존(호출자): F-004(task-process 훅), F-008(opd CLOSE 안내), 캡틴 수동 호출.
- 하위 의존(피호출자): git CLI 2.50.1(실측), F-001의 config 로더.
- 공유 상태: 대상 프로젝트의 `.gitignore`(F-007이 수정), `.opal-worktrees/`(신규 디렉토리), 각 코드 레포의 `.git/worktrees/` 메타.
- **git-sync-tool 대비 구현 복잡도 상승 지점**(ANALYSIS R-7): `worktree add -b`·`sparse-checkout set <가변 개수 경로>`처럼 인자 개수가 가변이라 `_run_git`을 그대로 쓰되 인자 리스트를 **호출부에서 조립**해야 한다. 문자열 결합(f-string)으로 명령을 만들지 않는다.

---

### F-003: `--worktree`/`--wt` 축 하네스 SSOT 정의

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/opal-harness.md` | §2.5 신규 절 + §9 도구 표 행 추가 | 수정 |

#### 2.3.2 현재 구현

- §2 모듈 구조가 모드 축 3종을 정의하고 로딩 규칙 3항을 둔다 — `opal-harness.md:71-131` 구간. "다중 모드 플래그 동시 사용 → `mode_flag_conflict` 에러"가 여기 있다.
- §9 OPAL Tools "현재 등록된 도구" 표에 도구 11행이 등재되어 있다 — `opal-harness.md:248-260`.
- ANALYSIS §4-1이 확인한 전파 경로: `opal-harness.md`는 Phase B(PM tier) 부트스트랩에서 **무조건 Eager 로드**되고, 각 pilot의 `## Harness` 절이 "부트스트랩에서 로드되지 않은 경우: Read한다" 폴백을 명시한다(`opal/skills/opal-pilot-dev/SKILL.md:11`). → pilot 10종 무변경으로 `--wt` 인지가 전파된다.

#### 2.3.3 영향 범위

- pilot 10종 전부가 이 문서를 읽으므로 **본 절 1곳이 전 pilot에 전파**된다(간접 영향, 파일 변경 0).
- **번호 체계 리스크(H-13)**: 프로젝트 전역이 `opal-harness.md §N` 형태로 절 번호를 인용한다(예: `docs/CONVENTIONS.md` §구현 규칙이 "§1 Guards"·"§3 State"·"§9 OPAL Tools"를 인용). 신규 절을 정수 번호로 삽입하면 대량 dangling이 발생한다.

---

### F-004: TASK 후처리 worktree 생성 훅

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/task-process.md` | §오케스트레이터 공통 영역에 스텝 4.5 삽입 + 스텝 5 코드블록에 옵션 1줄 | 수정 |

#### 2.4.2 현재 구현

`task-process.md:33-53` "오케스트레이터 공통 영역 (스킬 완료 후 후처리)"은 스텝 3(스킬약어 반영) → 4(모드 플래그 기록) → 5(`state init` **[필수]**) → 6(사용자 보고)의 **선형 절차이며 실패 분기가 전혀 없다**(ANALYSIS §4-7). 스텝 5의 코드블록은 다음 형태다:

```
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <약어> \
  --mode <interactive|semi-agentic|agentic> \
  [--task-title <태스크 제목>] \
  [--next-action <첫 액션 텍스트>]
```

#### 2.4.3 영향 범위

- 상위 의존: pilot 10종 전부의 STEP 1(TASK)이 "opal-harness.md 'TASK 공통 프로세스' 참조"로 이 문서를 호출한다(`opal/skills/opal-pilot-dev/SKILL.md:22-23`).
- 하위 의존: F-002 `create`, F-005 `state init --worktree`.
- **하위호환 급소**: `--wt` 미사용 경로에서 스텝 3·4·5·6의 순서·문구가 한 글자도 바뀌면 안 된다(TASK F-4 AC).

---

### F-005: `state-tool init --worktree <path>`

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/state_tool.py` | argparse 1행 + `cmd_init` 조건부 대입 1블록 | 수정 |
| 환경 | `opal/tools/state-tool/schema/state.schema.json` | `properties`에 `worktree` optional 추가 | 수정 |
| BE | `opal/tools/state-tool/tests/test_state_tool.py` | 신규 케이스 추가(기존 케이스 무변경) | 수정 |

#### 2.5.2 현재 구현

- `cmd_init`의 state dict 구성 — `state_tool.py:1237-1247`. 9키 고정(`task_id`/`skill`/`mode`/`schema_version`/`created_at`/`updated_at`/`current_status`/`rows`/`next_action`)이며 그 직후 `save_state_json(task_path, state)` — `state_tool.py:1255`.
- argparse `init` 서브파서 — `state_tool.py:2445-2461`.
- `state.schema.json:6-8`: `"required": [... 8키 ...]`, `"additionalProperties": false`.
- `_build_new_state_md(task_title, now_str, mode, first_stage, rows, table_str, next_action)` — `state_tool.py:1315-`. **인자 목록에 state dict가 없어 `worktree`를 참조할 수 없다** → 렌더 무변경이 구조적으로 보장된다(H-11).
- `cmd_show --format json`은 `ok(command, format="json", ..., data=state)`로 **state dict 전체를 그대로 반환**한다 — `state_tool.py:1358`. 따라서 "워커·PM이 어느 작업본인지 도구가 답한다"는 F-5의 목적은 `worktree` 키만 넣으면 **추가 코드 없이 충족**된다.

#### 2.5.3 영향 범위

- 기존 `state.json` 파일들(과거 태스크 산출물): optional 필드이므로 재작성 없음, 무영향(ANALYSIS §3.2).
- 회귀 대상: `opal/tools/state-tool/tests/test_state_tool.py`(5600줄+) + `test_todo_mirror_hook.py` **전량 pass가 완료 조건**(TASK 완료기준 ⑦).
- ANALYSIS §4-2가 확인한 대로 `state.schema.json`은 런타임 강제 대상이 아니므로 실행 리스크는 없다. 다만 문서 SSOT 정합을 위해 **반드시 갱신한다** — `additionalProperties:false`를 그대로 두고 필드를 추가하지 않으면 스키마 문서가 실제 산출물을 거짓으로 기술하게 된다.

---

### F-006: 워커 디스패치 경로 계약

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/pm/dispatch-process.md` | 워커 컨텍스트 주입 템플릿에 조건부 블록 추가 | 수정 |

#### 2.6.2 현재 구현

`dispatch-process.md:81-107` "워커 컨텍스트 주입 템플릿"이 `## 참조 문서` / `## 핵심 제약` / `## 종속 문서` / `## 문서/코드 불일치 규칙` 4블록을 정의한다. 경로 관련 필드는 없고, 실제 디스패치 프롬프트의 경로 표기는 pilot SKILL.md가 관례적으로 상대경로로 써 왔다(`opal/skills/opal-pilot-dev/SKILL.md:39` `**태스크 폴더**: {tasks/{NNN}-{name}/}`).

#### 2.6.3 영향 범위

- ANALYSIS R-5: 절대경로 규칙을 worktree 태스크에서만 신설하면 동일 필드가 태스크 유형에 따라 다른 표기 규칙을 갖는다. **단 "cwd는 매 Bash 호출마다 리셋 — 절대경로만 사용"은 이미 워커 시스템 프롬프트의 기존 규범**(ANALYSIS D-16)이므로 신규 도입 리스크는 낮다.
- 완화책: 신규 블록을 **기존 `**태스크 폴더**` 필드를 대체하지 않는 별도 블록**으로 두고, `--wt` 미사용 시 블록 자체를 주입하지 않는다 → 현행 프롬프트와 diff 0.

---

### F-007: `.gitignore` 멱등 추가 (도구 + opi 2계층)

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/worktree-tool/worktree_tool.py` | `ensure_gitignore_entry()` | 신규(함수) |
| 스킬 | `opal/skills/opal-project-init/SKILL.md` | §공통 절에 `.opal-worktrees/` 보장 항목 추가 | 수정 |

#### 2.7.2 현재 구현

`opal/skills/opal-project-init/SKILL.md:66-80` "공통: 프로젝트 로컬 설정(setting.local.json) 보장" 절이 유사 패턴을 이미 구현한다:
1. 대상 파일 존재 확인 → 2. 없으면 생성 → 3. **생성한 경우에만** `.gitignore`에 한 줄 추가(이미 있으면 스킵) → 4. 이미 존재하면 스킵.

**조건 트리거가 다르다**(ANALYSIS §4-5): opi는 "파일을 새로 생성한 경우에만"인 1회성 조건이고, F-007 도구 계층은 "`create`를 실행할 때마다" 무조건 존재 검사하는 반복 호출형 멱등이 필요하다. **코드를 그대로 복사하면 안 되고 조건을 일반화해야 한다.**

#### 2.7.3 영향 범위

- 대상 프로젝트 루트 `.gitignore` 1곳만 수정한다. 유형 A의 코드 레포는 worktree 경로가 자기 레포 밖이고, 유형 B는 sparse라 worktree 내부에서 보이지 않는다(TASK C-5).
- revup·mams의 수동 계층(3계층 중 1개)은 본 태스크의 **검증 환경 조작**이지 OPAL 저장소 산출물이 아니다(ANALYSIS §3.2).

---

### F-008: CLOSE 정리 안내 게이트 + `remove` 3중 가드

#### 2.8.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/worktree-tool/worktree_tool.py` | `cmd_remove` 3중 가드 | 신규(함수) |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 6에 안내 스텝 1개 삽입 | 수정 |

#### 2.8.2 현재 구현

`opal/skills/opal-pilot-dev/SKILL.md:236-264` STEP 6 CLOSE는 5스텝 구조다 — 1(DONE.md 생성+mark) → 2(관련 문서 업데이트) → 3(op-brain-ingest 디스패치) → 4(회고 하드스텝) → 5(완료 보고). 스텝 3·4가 **"부재 시 자연 스킵(no-op), CLOSE를 중단시키지 않는다"** 패턴을 이미 확립해 두었으므로, worktree 안내도 동일 패턴으로 삽입한다.

가드 판정에 필요한 git 조회는 `git-sync-tool`의 `process_repo`가 유사 로직을 이미 구현해 두었다 — dirty는 `git status --porcelain`(`git_sync_tool.py:123`), ahead/behind는 `git rev-list --left-right --count @{u}...HEAD`(`git_sync_tool.py:137-139`). **판정 순서를 먼저 확정하고 첫 위반에서 즉시 반환**하는 패턴(`git_sync_tool.py:99-127`의 detached→no-upstream→dirty)을 차용한다.

#### 2.8.3 영향 범위

- opd 1종만 수정한다. 나머지 pilot 9종의 CLOSE에는 안내가 없다 — TASK 범위 제외(C-9)이며 §9 리스크에 기재한다.
- `remove`는 **브랜치를 삭제하지 않는다**(worktree 디렉토리만 회수) — 커밋 보존 = user sovereignty.

---

### F-009: `UV_CACHE_DIR` 이전 + 볼륨 불일치 진단

#### 2.9.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `~/.zshrc` (캡틴 로컬) | `UV_CACHE_DIR` 영속 export | 수정(로컬 환경, OPAL 산출물 아님) |
| BE | `opal/tools/worktree-tool/worktree_tool.py` | `diagnose_cache_volume()` | 신규(함수) |

#### 2.9.2 현재 구현

- 실측(TASK.md §파일시스템 실측): uv 캐시 `~/.cache/uv` = `dev=16777235`(시스템 볼륨) / 프로젝트 `/Volumes/Data` = `dev=16777230`. 12GB, `/Volumes/Data` 여유 217GB.
- pnpm store는 `/Volumes/Data/.pnpm-store/v10`로 **이미 동일 볼륨**이라 APFS CoW로 재설치 비용이 0에 수렴한다 → uv만 남은 병목.
- 진단 로직은 미구현.

#### 2.9.3 영향 범위

- (a)는 **비가역 로컬 환경 변경**이며 OPAL 저장소 코드가 아니다. `mams`의 Python 개발 환경 전체가 영향권이다.
- (b)는 `create` 응답의 `warnings[]`에만 영향 — [MUST] TASK.md F-9 AC: "캐시·프로젝트 볼륨이 다를 때 `create`가 경고 메시지를 출력하되 **차단하지 않는다**."
- ANALYSIS R-6: `os.stat().st_dev`는 POSIX 표준이나 Windows에서 의미가 달라 오탐 가능. 경고 전용이므로 치명적이지 않다.

---

## 3. 기능별 설계

### F-001: `.opal/worktree.json` 스키마 + 검증 함수 + 템플릿

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/worktree-tool/schema/worktree.schema.json` | 환경 | 스키마 문서 SSOT (런타임 미로드) | (→ DEC-4), 선례 `opal/tools/state-tool/schema/state.schema.json` |
| 2 | `opal/templates/worktree-multi-repo.json` | 환경 | 유형 A 템플릿 | (→ D-1 §C-3) |
| 3 | `opal/templates/worktree-monorepo.json` | 환경 | 유형 B 템플릿 | (→ D-1 §C-3) |

**수정**: 없음(F-001 범위 한정. 검증 함수는 F-002의 `worktree_tool.py`에 들어간다).

#### 3.1.2 데이터 모델 설계

**`.opal/worktree.json` 7키 스키마**

| 키 | 타입 | 필수 | 기본값 | 설명 |
|----|------|------|--------|------|
| `layout` | string enum | **필수** | - | `"multi-repo"` \| `"monorepo"` (→ D-1 §C-2) |
| `repos` | string[] (len >= 1) | **필수** | - | **격리 대상 코드 경로**(프로젝트 루트 상대). `layout`이 해석 방식을 결정한다 |
| `branchTemplate` | string | 선택 | `"feat/OP-TASK-{NNN}"` | 치환 토큰 `{NNN}`·`{slug}`·`{skill}` (→ D-1 §C-4, DEC-1) |
| `baseBranch` | string | 선택 | 자동 판정 | base-ref 명시 선언 (→ DEC-3 우선순위 1) |
| `copy` | string[] | 선택 | `[]` | gitignore된 로컬 설정의 프로젝트 루트 상대 경로 |
| `setup` | object[] `{cwd: string, run: string}` | 선택 | `[]` | 의존성 설치 명령. **create는 실행하지 않는다**(→ D-1 §C-7 lazy) |
| `portOffset` | integer >= 0 | 선택 | `0` | 슬롯 포트 오프셋 **힌트**. 도구는 값을 출력만 하고 적용하지 않는다 |

> **설계 핵심 — `repos[]` 단일 키가 두 유형을 흡수한다.** `repos[]`의 의미를 "격리 대상 코드 경로"로 통일하고, `layout`이 처리 방식만 분기한다:
> - `multi-repo`: 각 path가 **독립 git 레포** → path마다 `git worktree add`
> - `monorepo`: 각 path는 **루트 레포의 서브디렉토리** → 루트 레포 1개 worktree + `sparse-checkout set <paths...>`
>
> 별도의 `target` 키를 두지 않는다 — [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." 대상 경로는 항상 `{project}/.opal-worktrees/task_{NNN}/{path}`로 **메인 레이아웃을 그대로 미러링**한다 (→ D-1 §C-1 "worktree 내부 레이아웃은 메인 프로젝트와 동일하게 맞춘다").
>
> `baseBranch`는 TASK C-3이 나열한 6키에 없는 추가 키다. F-8 AC의 "미머지 판정"을 결정론적으로 성립시키려면 필수이며(→ DEC-3), 선택 키라 기존 6키만 쓰는 선언도 그대로 유효하다.

**유형 A 템플릿** (`worktree-multi-repo.json`, revup 기준):
```json
{
  "layout": "multi-repo",
  "repos": ["workspace/storelink6", "workspace/revup-front"],
  "branchTemplate": "feat/OP-TASK-{NNN}",
  "copy": [],
  "setup": [],
  "portOffset": 0
}
```

**유형 B 템플릿** (`worktree-monorepo.json`, mams 기준):
```json
{
  "layout": "monorepo",
  "repos": ["workspace"],
  "branchTemplate": "feat/OP-TASK-{NNN}",
  "copy": ["workspace/backend/settings.local.yaml", "workspace/docker/.env.compose.local"],
  "setup": [
    {"cwd": "workspace/backend", "run": "uv sync"},
    {"cwd": "workspace/frontend", "run": "pnpm install"}
  ],
  "portOffset": 100
}
```
근거: `copy[]` 값은 TASK.md D-6·D-7이 실측한 mams의 gitignore된 로컬 설정 파일이다(`workspace/backend/settings.local.yaml` 공유 RDS 설정, `.env.compose.local` `COMPOSE_PROJECT_NAME`).

#### 3.1.3 함수 시그니처

```python
def load_config(project_root: pathlib.Path) -> dict:
    """{project_root}/.opal/worktree.json 로드. 부재→CONFIG_NOT_FOUND, 파싱실패→CONFIG_INVALID_JSON."""

def validate_worktree_config(cfg: dict, project_root: pathlib.Path) -> dict:
    """검증 통과 시 기본값이 채워진 정규화 dict 반환. 위반 시 err_response로 즉시 종료.

    검증 순서(첫 위반에서 즉시 반환 — 결정론):
      1. cfg가 dict가 아님                        -> CONFIG_INVALID_TYPE
      2. 'layout' 부재 / 'repos' 부재              -> CONFIG_MISSING_KEY   (key=<키명>)
      3. layout not in {multi-repo, monorepo}      -> CONFIG_INVALID_LAYOUT (value=<입력값>)
      4. repos가 list[str]이 아니거나 빈 배열       -> CONFIG_INVALID_TYPE   (key="repos")
      5. repos/copy 각 항목이 절대경로이거나
         정규화 후 project_root를 벗어남('..')      -> CONFIG_PATH_ESCAPE   (value=<위반 항목>)
      6. branchTemplate/baseBranch가 str 아님      -> CONFIG_INVALID_TYPE
      7. setup 각 항목이 {cwd,run} dict 아님        -> CONFIG_INVALID_TYPE
      8. portOffset이 int>=0 아님                  -> CONFIG_INVALID_TYPE
    """

def _is_inside(project_root: pathlib.Path, rel: str) -> bool:
    """os.path.normpath 후 project_root 하위인지 판정. 심볼릭 링크는 해석하지 않는다(경로 문자열 기준)."""
```

> [MUST] F-1 AC(TASK.md): "필수 키 누락·`layout` 무효값·`repos[]` 경로 이탈(`..`) 3종을 각각 **고유 에러 코드**로 거부한다" → 위 2·3·5번이 각각 `CONFIG_MISSING_KEY`/`CONFIG_INVALID_LAYOUT`/`CONFIG_PATH_ESCAPE`에 1:1 대응한다.

#### 3.1.4 환경 변경

없음. 표준 라이브러리 `json`/`pathlib`/`os.path`만 사용한다 (→ DEC-4 근거 1·2).

#### 3.1.5 배치/마이그레이션

해당 없음. `.opal/worktree.json`은 **옵트인 신규 파일**이며 부재해도 기존 프로젝트가 영향받지 않는다.

#### 3.1.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC(템플릿 통과) | 기능 테스트 | 유형 A/B 템플릿 2종이 `validate_worktree_config()`를 통과하고 기본값이 채워진 dict를 반환한다 |
| TS-002 | F-1 AC(필수 키) | 기능 테스트 | `layout` 제거 / `repos` 제거 각각 `{"ok":false,"error":"CONFIG_MISSING_KEY"}` + `key` 필드에 누락 키명 |
| TS-003 | F-1 AC(layout 무효) | 기능 테스트 | `layout:"hybrid"` → `CONFIG_INVALID_LAYOUT` |
| TS-004 | F-1 AC(경로 이탈) | 보안 테스트 | `repos:["../../etc"]`, `repos:["/etc"]`, `copy:["../secret"]` 3종 각각 `CONFIG_PATH_ESCAPE` |
| TS-005 | F-1 AC | 기능 테스트 | `.opal/worktree.json` 부재 시 `CONFIG_NOT_FOUND`, 깨진 JSON 시 `CONFIG_INVALID_JSON` |

---

### F-002: `worktree-tool` 신설

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/worktree-tool/worktree_tool.py` | BE | 도구 본체 | (→ D-8 골격) |
| 2 | `opal/tools/worktree-tool/run.sh` | 환경 | venv python 위임 래퍼 | `opal/tools/git-sync-tool/run.sh:1-10` **완전 복제**(도구명만 치환) |
| 3 | `opal/tools/worktree-tool/tests/conftest.py` | BE | 유형 A/B fixture | `opal/tools/git-sync-tool/tests/conftest.py` 패턴 |
| 4 | `opal/tools/worktree-tool/tests/test_worktree_tool.py` | BE | pytest 스위트 | 동상 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `scripts/install-mac.sh` | 환경 | `worktree-tool/run.sh` chmod 블록 1개 추가 (`code-scan` 블록 직후, `scripts/install-mac.sh:1197-1202` 뒤) | ANALYSIS §4-4 |

#### 3.2.2 CLI·응답 계약 설계

**서브명령 4종**

```bash
~/.opal/tools/worktree-tool/run.sh create --project-root <abs> --task <NNN> [--slug <s>] [--skill <s>]
~/.opal/tools/worktree-tool/run.sh list   --project-root <abs>
~/.opal/tools/worktree-tool/run.sh status --project-root <abs> --task <NNN>
~/.opal/tools/worktree-tool/run.sh remove --project-root <abs> --task <NNN> [--force]
```

**응답 계약** — `git_sync_tool.py:29-42` 완전 동형:
```python
def ok_response(**kwargs):   # {"ok": True,  "error": None, **kwargs}  단일 라인 JSON, ensure_ascii=False
def err_response(code, exit_code=1, **kwargs):  # {"ok": False, "error": code, "message": ..., **kwargs}
```
> [MUST] TASK.md F-2 AC: "4서브명령이 모두 JSON `{"ok": true|false}`를 반환하고 … 실패 시 `"error"` 필드에 에러 코드가 담긴다."

**`ERROR_CODES` 카탈로그** (dict 기반 — `git_sync_tool.py:23-26` 패턴):

| 코드 | 서브명령 | 의미 |
|------|---------|------|
| `CONFIG_NOT_FOUND` | 전체 | `.opal/worktree.json` 부재 |
| `CONFIG_INVALID_JSON` | 전체 | JSON 파싱 실패 |
| `CONFIG_MISSING_KEY` | 전체 | `layout`/`repos` 누락 |
| `CONFIG_INVALID_LAYOUT` | 전체 | `layout` 무효값 |
| `CONFIG_INVALID_TYPE` | 전체 | 키 타입 불일치 |
| `CONFIG_PATH_ESCAPE` | 전체 | `repos`/`copy` 경로 루트 이탈 |
| `PROJECT_ROOT_NOT_FOUND` | 전체 | `--project-root` 경로 부재 |
| `WORKTREE_EXISTS` | create | 대상 경로가 이미 존재 |
| `BRANCH_EXISTS` | create | 브랜치가 이미 존재 |
| `REPO_NOT_FOUND` | create | `repos[]` 경로 부재 |
| `NOT_A_GIT_REPO` | create | multi-repo인데 `.git` 없음 / monorepo인데 루트에 `.git` 없음 |
| `GIT_COMMAND_FAILED` | create/remove | git 호출 실패 (`detail`에 stderr 원문) |
| `META_NOT_FOUND` | remove/status | `.opal-worktrees/.meta/task_{NNN}.json` 부재 |
| `WORKTREE_NOT_FOUND` | remove/status | 메타는 있으나 실제 경로 부재 |
| `GUARD_DIRTY` | remove | 작업본 미커밋 변경 존재 |
| `GUARD_UNPUSHED` | remove | 원격에 없는 커밋 존재 |
| `GUARD_UNMERGED` | remove | base-ref에 미머지 |

**git 호출 헬퍼** — `git_sync_tool.py:46-56` 복제:
```python
def _run_git(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    """["git", *args] 리스트 인자. [MUST] shell=True 금지, f-string 명령 조립 금지 (injection 방지)."""
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
```
> [MUST] `opal/tools/git-sync-tool/git_sync_tool.py:46`: "git 호출 헬퍼 — 모두 인자 리스트 방식(shell=True 금지, injection 방지)". 가변 인자 명령(`sparse-checkout set <paths...>`)은 호출부에서 **리스트를 조립해 전달**한다: `_run_git(["sparse-checkout", "set", *repos], cwd=wt_root)` (→ ANALYSIS R-7 대응).

#### 3.2.3 `create` 알고리즘 (DEC-2·DEC-3 집행)

```python
def cmd_create(args):
    project_root = _resolve_project_root(args.project_root)          # 부재→PROJECT_ROOT_NOT_FOUND
    cfg = validate_worktree_config(load_config(project_root), project_root)
    branch = _render_branch(cfg["branchTemplate"], args.task, args.slug, args.skill)
    wt_root = project_root / ".opal-worktrees" / f"task_{args.task}"

    # ── (1) pre-flight — 여기서 실패하면 아무것도 만들지 않는다 (DEC-2) ──
    if wt_root.exists():                     err_response("WORKTREE_EXISTS", path=str(wt_root))
    for rel in cfg["repos"]:
        src = project_root / rel
        if not src.is_dir():                 err_response("REPO_NOT_FOUND", path=rel)
    git_roots = _git_roots(cfg, project_root)         # multi-repo→각 repo / monorepo→[project_root]
    for gr in git_roots:
        if not (gr / ".git").exists():       err_response("NOT_A_GIT_REPO", path=str(gr))
        if _branch_exists(gr, branch):       err_response("BRANCH_EXISTS", branch=branch, repo=str(gr))

    # ── (2) 부수 효과(비파괴) ──
    gitignore_state = ensure_gitignore_entry(project_root, ".opal-worktrees/")   # F-007
    warnings  = diagnose_cache_volume(project_root)                             # F-009(b)
    warnings += diagnose_code_scan_exclude(project_root)                        # DEC-5(b)

    # ── (3) base-ref 해석 + 동결 (DEC-3) ──
    base_refs = {str(gr): resolve_base_ref(gr, cfg.get("baseBranch")) for gr in git_roots}

    # ── (4) worktree 생성 — 실패 시 자기 생성물만 롤백 (DEC-2) ──
    created = []                       # [(git_root, wt_path, branch)]
    try:
        if cfg["layout"] == "multi-repo":
            for rel in cfg["repos"]:
                gr, dest = project_root / rel, wt_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                _git_or_raise(gr, ["worktree", "add", "-b", branch, str(dest), base_refs[str(gr)]])
                created.append((gr, dest, branch))
        else:  # monorepo — 순서 [MUST]: --no-checkout → init --cone → set → checkout
            gr = project_root
            _git_or_raise(gr, ["worktree", "add", "--no-checkout", "-b", branch,
                               str(wt_root), base_refs[str(gr)]])
            created.append((gr, wt_root, branch))
            _git_or_raise(wt_root, ["sparse-checkout", "init", "--cone"])
            _git_or_raise(wt_root, ["sparse-checkout", "set", *cfg["repos"]])
            _git_or_raise(wt_root, ["checkout", branch])
    except GitFailure as e:
        _rollback(created)             # git worktree remove --force + git branch -D
        err_response("GIT_COMMAND_FAILED", detail=e.stderr, rolled_back=len(created))

    # ── (5) copy[] — 원본 부재는 비차단 경고 ──
    copied, warnings = _copy_local_files(project_root, wt_root, cfg["copy"], warnings)

    # ── (6) setup[]은 실행하지 않는다 (C-7 lazy) — 열거만 ──
    pending_setup = cfg["setup"]

    _write_meta(project_root, args.task, cfg, branch, created, base_refs)   # DEC-3 동결
    ok_response(command="create", task=args.task, layout=cfg["layout"],
                worktree_root=str(wt_root), branch=branch,
                entries=[{"repo": str(g), "path": str(p), "branch": branch,
                          "base_ref": base_refs[str(g)]} for g, p, _ in created],
                gitignore=gitignore_state, copied=copied,
                pending_setup=pending_setup, port_offset=cfg["portOffset"],
                warnings=warnings)
```

**monorepo 명령 순서 근거** (→ ANALYSIS §2.1): `--no-checkout` 선행 후 sparse 패턴을 설정하고 마지막에 checkout하는 순서가 불필요한 전체 체크아웃(및 이후 스파스 축소로 인한 파일 삭제)을 피한다. 이 순서를 지켜야 `tasks/`·`.opal/`이 **한 순간도 체크아웃되지 않는다**(TASK 완료기준 ②, H-4).

**`resolve_base_ref()` — DEC-3 3단 우선순위, 1곳에 봉인**:
```python
def resolve_base_ref(git_root: pathlib.Path, declared: str | None) -> str:
    if declared:
        return declared                                    # 1. worktree.json baseBranch
    r = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], git_root)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip().removeprefix("refs/remotes/")   # "origin/main"  (본 저장소 실측값)
    r = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], git_root)
    return r.stdout.strip()                                # 3. 현재 브랜치명
```

**메타 파일** `{project_root}/.opal-worktrees/.meta/task_{NNN}.json` — **worktree 밖**(H-4·dirty 오탐 방지, → DEC-3):
```json
{
  "task": "092", "layout": "monorepo", "branch": "feat/OP-TASK-092",
  "created_at": "2026-08-15 14:30",
  "worktree_root": "/abs/.opal-worktrees/task_092",
  "entries": [{"repo": "/abs/project", "path": "/abs/.opal-worktrees/task_092",
               "branch": "feat/OP-TASK-092", "base_ref": "origin/main"}],
  "pending_setup": [{"cwd": "workspace/backend", "run": "uv sync"}]
}
```

#### 3.2.4 `list` / `status` 설계

- `list`: `.opal-worktrees/.meta/*.json`을 열거하고 각 항목의 실경로 존재 여부를 대조하여 `{task, branch, worktree_root, exists}` 목록을 반환한다. 비파괴.
- `status`: 메타 + 각 entry의 현재 상태를 조회한다 — `{branch, dirty(bool), unpushed(int), merged(bool), pending_setup[]}`. **`remove`와 동일한 판정 함수를 재사용**하되 거부하지 않고 보고만 한다(F-008 CLOSE 안내가 소비).

#### 3.2.5 환경 변경

- 신규 도구 디렉토리 `opal/tools/worktree-tool/` → `install_dir "$opal_dir/tools"`(`scripts/install-mac.sh:1113-1114`)가 **자동 배포**한다. 별도 등록 코드 불필요(ANALYSIS §4-4).
- **`run.sh` 실행 권한만 개별 chmod 블록 필요** — 누락 시 배포는 되어도 `Permission denied`. `scripts/install-mac.sh:1197-1202`의 code-scan 블록 직후에 동형 3줄 블록을 추가한다:
```bash
        # ── worktree-tool 실행 권한 (092) ──
        local worktree_run="$opal_home/tools/worktree-tool/run.sh"
        if [[ -f "$worktree_run" ]]; then
            chmod +x "$worktree_run"
            success "worktree-tool run.sh 실행 권한 설정"
        fi
```
- Python 신규 의존성 **없음** — `argparse`/`json`/`pathlib`/`subprocess`/`os`/`shutil` 표준 라이브러리만 (→ DEC-4).

#### 3.2.6 배치/마이그레이션

해당 없음.

#### 3.2.7 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | F-2 AC(유형 A) | 통합 테스트 | 독립 bare remote 2개 + clone 2개 fixture에서 `create` → worktree 2개 생성, 각 경로가 `{wt_root}/{repos[i]}`와 일치, 브랜치명이 `feat/OP-TASK-092` |
| TS-011 | F-2 AC(유형 B) | 통합 테스트 | monorepo fixture(`workspace/`·`tasks/`·`.opal/` 보유)에서 `create` → `workspace/`만 체크아웃, `tasks/`·`.opal/` **부재** |
| TS-012 | F-2 AC(JSON 계약) | 기능 테스트 | 4서브명령 stdout이 전부 단일 라인 JSON이며 `ok` 키를 갖는다 |
| TS-013 | DEC-2 (H-7) | 통합 테스트 | 2번째 repo를 비-git 디렉토리로 만든 fixture → pre-flight `NOT_A_GIT_REPO`로 거부되고 worktree 0개, 브랜치 0개 |
| TS-014 | DEC-2 (H-7) | 통합 테스트 | pre-flight 통과 후 2번째 `worktree add`를 실패시키는 fixture → `GIT_COMMAND_FAILED` + 1번째 worktree·브랜치 부재(롤백 확인) |
| TS-015 | DEC-3 (H-8) | 통합 테스트 | `create` 후 `origin/HEAD`를 다른 브랜치로 변경 → `status`/`remove`의 미머지 판정이 create 시점 base 기준으로 불변 |
| TS-016 | C-7 lazy (H-15) | 기능 테스트 | `setup`에 sentinel 파일 생성 명령 선언 → `create` 후 sentinel **부재**, 응답 `pending_setup[]`에 해당 항목 열거 |
| TS-017 | F-2 배포 (H-10) | 회귀 테스트 | `./scripts/install-mac.sh` 후 `test -x ~/.opal/tools/worktree-tool/run.sh` 성공 |

---

### F-003: `--worktree`/`--wt` 축 하네스 SSOT 정의

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 가이드 | **§2.5 "워크스페이스 축(`--worktree`/`--wt`)"** 신설(§2 모듈 구조 직후, `opal-harness.md:131` 인근) + §9 도구 표에 worktree-tool 행 추가(`opal-harness.md:260` 뒤) + 변경이력 1행 | (→ D-1 §F-3), ANALYSIS §1.1 |

#### 3.3.2 설계 — 절 번호 결정

> **[MUST] 신규 절은 `§2.5` 소수점 번호로 삽입한다. `§3`으로 삽입하면 안 된다.**
> 근거: `docs/CONVENTIONS.md` §구현 규칙이 `opal-harness.md` "§1 Guards"·"§3 State"·"§9 OPAL Tools"를 인용하고, `opal/core/references/harness/*.md` 다수가 "출처: opal-harness.md §N"을 헤더에 명시한다(예: `harness/task-process.md:3` "출처: opal/core/references/opal-harness.md §4", `harness/citation-rules.md:3` "출처: opal-harness.md §2"). 정수 번호를 삽입하면 이 인용들이 전부 dangling이 된다(H-13).

#### 3.3.3 §2.5 본문 3항목 (F-3 AC)

```markdown
## 2.5 워크스페이스 축 (`--worktree` / `--wt`)

### (1) 모드 축과 직교하는 별개 축

`--worktree`(약칭 `--wt`)는 §2의 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**한다.
- 모드 축은 "PM이 얼마나 자율적으로 진행하는가"를, 워크스페이스 축은 "코드를 어느 작업본에서 만지는가"를 결정한다.
- 조합 가능: `//opd --agentic --wt`, `//opds --wt` 모두 유효하다.
- `mode_flag_conflict` 판정 대상이 **아니다** — 모드 플래그 개수 검사에 `--wt`를 세지 않는다.
- 서브 하네스 로딩 규칙(§2 로딩 규칙)에 영향을 주지 않는다.

### (2) `--wt` 미사용 시 = 현행 동작 100% 유지

플래그가 없으면 다음이 전부 현행과 동일하다. 어떤 조건부 분기도 실행되지 않는다.
- `state.json` 스키마 — `worktree` 키가 **아예 생성되지 않는다**(`state-tool init`에 `--worktree`를 전달하지 않는다).
- STATE.md 렌더 결과 · 산출물 경로 · 워커 디스패치 프롬프트(`pm/dispatch-process.md` §작업 경로 블록 미주입).
- 코드 작업본은 프로젝트 기본 작업본(`workspace/` 등)이다.

### (3) `.opal/worktree.json` 부재 시 동작

`--wt`를 받았는데 `{프로젝트}/.opal/worktree.json`이 없으면:
- `worktree-tool create`가 `{"ok": false, "error": "CONFIG_NOT_FOUND"}`를 반환한다.
- PM은 **태스크를 중단하지 않는다.** `--wt` 없이 위 (2) 경로로 계속 진행하고, 사용자에게 사유와 템플릿 경로(`~/.opal/templates/worktree-multi-repo.json` · `worktree-monorepo.json`)를 안내한다.
- 경로 계약: 코드 작업본은 `{프로젝트}/.opal-worktrees/task_{NNN}/`이며 태스크 문서(`tasks/`)·`.opal/MEMORY.json`·`.opal/brain/`은 **분기하지 않고 허브에 고정**한다.
- 생성·회수 절차의 SSOT는 `harness/task-process.md` §오케스트레이터 공통 영역 스텝 4.5(생성)와 `worktree-tool remove`(회수)이며, 본 절은 축의 정의만 소유한다.
```

§9 도구 표 추가 행:
```markdown
| worktree-tool | 태스크별 코드 작업본 git worktree 격리 결정론 집행 — 4서브명령 `create`/`list`/`status`/`remove`. `.opal/worktree.json` 선언 기반으로 multi-repo(레포별 worktree)·monorepo(sparse-checkout) 2유형 흡수, `.gitignore` 멱등 보장, `remove` 3중 가드(dirty/unpushed/미머지). 자동 커밋·자동 머지·자동 제거 없음. git 2.25+ | `--worktree`/`--wt` 태스크의 TASK 후처리 / CLOSE 정리 안내 / 캡틴 수동 회수 시 |
```

#### 3.3.4 환경 변경 / 배치

해당 없음. [MUST] `.opal/AGENT.md` §업무 수행 지침: "문서 변경이력 — 스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)." → `opal-harness.md` 변경이력에 `(092)` 행 추가 필수.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | F-3 AC(3항목) | 산출물 검사 | `opal-harness.md`에 §2.5가 존재하고 ①직교 축 선언 ②`--wt` 미사용 시 현행 유지 ③`worktree.json` 부재 시 동작 3항목이 모두 기재됨 |
| TS-021 | F-3 AC(pilot diff 0) (H-2) | 회귀 테스트 | `git diff --stat opal/skills/opal-pilot-*/SKILL.md` 결과가 `opal-pilot-dev/SKILL.md` 1건(F-008)뿐이고 나머지 9종은 0 |
| TS-022 | H-13 | 회귀 테스트 | `grep -rn "opal-harness.md §" opal/ docs/` 전 결과가 실존 절을 가리킨다(§1~§10 + §2.5) |
| TS-023 | F-3 AC | 산출물 검사 | §9 도구 표에 worktree-tool 행이 존재하고 4서브명령이 명시됨 |

---

### F-004: TASK 후처리 worktree 생성 훅

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/task-process.md` | 가이드 | §오케스트레이터 공통 영역에 **스텝 4.5** 삽입 + 스텝 5 코드블록에 `[--worktree <path>]` 1행 + 변경이력 1행 | `task-process.md:33-53`, (→ DEC-2) |

#### 3.4.2 설계 — 삽입 지점과 번호

> **[MUST] 신규 스텝은 `4.5`로 삽입한다.** 기존 스텝 3·4·5·6의 번호·문구를 바꾸지 않는다.
> 근거: [MUST] TASK.md F-4 AC: "`--wt` 미사용 경로의 기존 스텝 순서·문구가 변경되지 않는다."
> 삽입 위치 근거: 태스크 번호는 스텝 3에서 확정되고 `state init`은 스텝 5에서 `--worktree` 값을 필요로 하므로, **4와 5 사이가 유일하게 가능한 지점**이다 (→ D-1 §C-1 "태스크 번호가 확정된 직후가 `task_{NNN}` 경로를 만들 수 있는 유일한 시점").

삽입 문안:
```markdown
4.5. **`--worktree`/`--wt` 플래그가 있을 때만 수행한다** (플래그가 없으면 이 스텝 전체를 건너뛰고 4 → 5로 직행한다 — 현행 동작 100% 유지).

   ```bash
   ~/.opal/tools/worktree-tool/run.sh create \
     --project-root <프로젝트 절대경로> \
     --task <NNN> \
     [--slug <태스크명>] \
     [--skill <약어>]
   ```

   - `ok: true` → 응답의 `worktree_root` 값을 아래 5번 `state init`의 `--worktree <path>`에 전달한다. `warnings[]`가 있으면 그대로 사용자에게 전달한다(**차단하지 않는다**).
   - `ok: false` → **태스크 폴더·TASK.md를 롤백하지 않는다.** `--wt` 없이 5번으로 진행하고(=`--worktree`를 전달하지 않으므로 `state.json`이 현행 스키마와 동일해진다), 실패 사유(`error` 코드)를 사용자에게 보고한다. agentic 모드에서는 사용자 확인을 요구하지 않고 자동 계속하되 AGENTIC-LOG.md에 실패 사유를 기록한다.
   - 도구는 부분 실패 시 자기가 만든 worktree·브랜치만 스스로 되돌린다(all-or-nothing) — 파이프라인이 정리할 잔여물은 없다.
   - 축 정의 SSOT: `opal/core/references/opal-harness.md` §2.5.
```

스텝 5 코드블록 갱신(옵션 1행 추가 — 기존 행 무변경):
```
  [--next-action <첫 액션 텍스트>] \
  [--worktree <worktree_root 절대경로>]      ← 4.5가 ok:true를 반환한 경우에만 전달
```

#### 3.4.3 환경 변경 / 배치

해당 없음. 변경이력 행 추가 의무 적용.

#### 3.4.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | F-4 AC | 산출물 검사 | `task-process.md`에 스텝 4.5가 존재하고 `worktree-tool create` 호출·성공/실패 분기·롤백 금지가 명시됨 |
| TS-031 | F-4 AC | 회귀 테스트 | 스텝 3·4·5·6의 번호와 본문 문구가 변경 전과 동일(`git diff`에서 해당 라인 미변경, 스텝 5 코드블록의 신규 옵션 1행만 추가) |
| TS-032 | DEC-2 | 산출물 검사 | 실패 시 "태스크 폴더·TASK.md 롤백 금지" + "agentic 자동 계속 + AGENTIC-LOG 기록"이 명문화됨 |

---

### F-005: `state-tool init --worktree <path>`

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | BE | argparse `init`에 `--worktree` 1행(`state_tool.py:2461` 인근) + `cmd_init`에 조건부 대입 블록(`state_tool.py:1247` 직후) | `state_tool.py:1237-1255, 2445-2461` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 환경 | `properties`에 `worktree` optional 추가(`required`에는 미추가) | `state.schema.json:6-8`(`additionalProperties:false`) |
| 3 | `opal/tools/state-tool/tests/test_state_tool.py` | BE | 신규 케이스 3건 추가 — 기존 케이스 무변경 | ANALYSIS §1.4 |

#### 3.5.2 함수 시그니처·구현 명세

argparse (`state_tool.py:2461` 뒤, `--import-existing` 인접):
```python
p_init.add_argument("--worktree", metavar="<path>",
                    help="worktree 코드 작업본 절대경로 (092). 미지정 시 state.json에 키를 생성하지 않는다.")
```

`cmd_init` — `state = {...}` dict 생성(`state_tool.py:1237-1247`) **직후**, `save_state_json` 호출 전:
```python
    # 092 F-5: worktree 경로 조건부 영속화.
    # [MUST] 미지정 시 키 자체를 생성하지 않는다 — 기존 state.json과 스키마·바이트 동일(TASK F-5 AC).
    if getattr(args, "worktree", None):
        state["worktree"] = args.worktree
```

> [MUST] TASK.md F-5 AC: "`--worktree` 지정 시 `state.json`에 해당 필드가 기록되고, **미지정 시 필드가 아예 생성되지 않아** 기존 `state.json`과 스키마·바이트가 동일하다."
> → `state["worktree"] = args.worktree`를 **무조건 실행하면 안 된다**(`None` 값 키가 생성되어 AC 위반, H-1).
> → `getattr(args, "worktree", None)`을 쓰는 이유: `cmd_init`은 `init` 서브파서 외 경로(테스트의 인자 스텁 등)에서도 호출될 수 있어 속성 부재에 방어한다(기존 코드가 `getattr(args, "rows_acts", None)`·`getattr(args, "format", "md")`로 쓰는 관행과 일치 — `state_tool.py:1145, 1350`).

`state.schema.json` `properties`에 추가(`next_action` 인접, `state.schema.json:124` 부근):
```json
    "worktree": {
      "type": "string",
      "description": "worktree 코드 작업본 절대경로. --worktree 지정 시에만 존재하는 optional 필드 — 미지정 태스크의 state.json에는 키 자체가 없다 (092)"
    }
```

**변경하지 않는 것**(하위호환 [MUST]):
- `_build_new_state_md(...)` — 인자에 state dict가 없어 `worktree`를 참조할 수 없다. **시그니처를 바꾸지 않는다** → STATE.md 렌더 diff 0이 구조적으로 보장된다(H-11).
- `render_pipeline_table` · `build_todo_mirror` · `save_state_json` — 무변경.
- `required` 배열 — `worktree`를 넣지 않는다.
- `cmd_show` — 무변경. `--format json`이 `data=state`로 dict 전체를 반환하므로(`state_tool.py:1358`) `worktree` 키가 **자동 노출**된다. F-5의 "도구가 답할 수 있어야 함" 목적은 추가 코드 없이 충족된다.

#### 3.5.3 환경 변경 / 배치

해당 없음.

#### 3.5.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | F-5 AC(기록) | 기능 테스트 | `init --worktree /abs/wt` → `state.json`에 `"worktree": "/abs/wt"` 존재, `show --format json`의 `data.worktree`가 동일 값 |
| TS-041 | F-5 AC(미지정) (H-1) | 회귀 테스트 | `--worktree` 없이 `init` → `json.loads(state.json)`에 `"worktree" not in state` |
| TS-042 | F-5 AC(바이트 동일) (H-1) | 회귀 테스트 | 동일 인자로 변경 전/후 `init` 실행 → `state.json` 바이트 동일(timestamp 정규화 후) |
| TS-043 | H-11 | 회귀 테스트 | `--worktree` 유/무 2회 init → `STATE.md` diff 0 |
| TS-044 | 완료기준 ⑦ | 회귀 테스트 | `pytest opal/tools/state-tool/tests/` **전량 pass**(기존 케이스 0 fail) |
| TS-045 | F-5 AC | 산출물 검사 | `state.schema.json` `properties`에 `worktree` 존재, `required`에 **미존재** |

---

### F-006: 워커 디스패치 경로 계약

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/pm/dispatch-process.md` | 가이드 | 워커 컨텍스트 주입 템플릿에 조건부 `## 작업 경로` 블록 추가(`dispatch-process.md:103` 코드블록 내) + 하단 주석 1줄 + 변경이력 1행 | `dispatch-process.md:81-107` |

#### 3.6.2 설계 — 템플릿 추가 블록

기존 템플릿 코드블록(`dispatch-process.md:85-103`)의 `## 문서/코드 불일치 규칙` **앞**에 삽입:
```markdown
## 작업 경로 (worktree 태스크에서만 주입 — `--wt` 미사용 시 이 블록 전체를 주입하지 않는다)
- **문서 루트**: {절대경로}/tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/   ← 산출물(.md)·state 기록 위치
- **코드 루트**: {절대경로}/.opal-worktrees/task_{NNN}/                   ← 코드 변경 위치
- [MUST] 두 루트는 **절대경로**로 주입한다. 상대경로 금지 — 워커의 cwd는 매 Bash 호출마다 리셋된다.
- [MUST] 코드 변경은 **코드 루트 안에서만** 수행한다. 허브 프로젝트의 `workspace/`를 수정하지 않는다.
```

코드블록 뒤 주석:
> `--worktree`/`--wt` 미사용 태스크에서는 위 `## 작업 경로` 블록을 주입하지 않는다 — 디스패치 프롬프트가 현행과 동일하게 유지된다(축 정의: `opal/core/references/opal-harness.md` §2.5). 기존 `**태스크 폴더**` 등 pilot SKILL.md의 경로 필드는 **대체하지 않고 그대로 둔다**(ANALYSIS R-5 완화 — 표기 규칙 이원화를 신규 블록에 격리).

#### 3.6.3 환경 변경 / 배치

해당 없음. 변경이력 행 추가 의무 적용.

#### 3.6.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | F-6 AC | 산출물 검사 | `dispatch-process.md`에 "상대경로 금지·절대경로 주입" 문구 + 문서 루트/코드 루트 2필드 계약이 존재 |
| TS-051 | F-6 AC / R-5 | 산출물 검사 | 블록이 조건부(`--wt` 시에만 주입)로 명시되고, 기존 템플릿 4블록의 문구가 무변경 |

---

### F-007: `.gitignore` 멱등 추가 (도구 + opi 2계층)

#### 3.7.1 파일 변경 계획

**신규 생성**: 없음(F-002의 `worktree_tool.py` 내 함수).

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/worktree-tool/worktree_tool.py` | BE | `ensure_gitignore_entry()` 추가, `cmd_create`에서 호출 | (→ D-1 §C-5 계층 1) |
| 2 | `opal/skills/opal-project-init/SKILL.md` | 스킬 | §"공통: 프로젝트 로컬 설정 보장" 절에 `.opal-worktrees/` 보장 항목 추가 + 변경이력 1행 | `opal-project-init/SKILL.md:66-80` |

#### 3.7.2 함수 시그니처

```python
GITIGNORE_ENTRY = ".opal-worktrees/"

def ensure_gitignore_entry(project_root: pathlib.Path, entry: str = GITIGNORE_ENTRY) -> str:
    """루트 .gitignore에 entry를 멱등 보장. 반환: "created" | "added" | "present".

    [MUST] 이미 있으면 파일에 write를 하지 않는다 — 바이트 단위 무변경 (TASK F-7 AC).
    판정: 각 라인을 strip()하여 {entry, entry.rstrip('/')} 집합과 비교(주석 라인 제외).
    추가: 기존 내용이 개행으로 끝나지 않으면 개행을 먼저 보장한 뒤 entry + "\n"을 append.
    """
```

> **opi 패턴을 그대로 복제하지 않는다**(ANALYSIS §4-5). opi는 "대상 파일을 새로 생성한 경우에만" gitignore 라인을 추가하는 1회성 조건(`opal-project-init/SKILL.md:79`)인 반면, 도구 계층은 **`create`를 실행할 때마다 무조건 존재 검사**하는 반복 호출형 멱등이어야 한다 — [MUST] TASK.md F-7 AC: "동일 프로젝트에서 `create`를 2회 실행해도 `.gitignore`에 `.opal-worktrees/` 행이 정확히 1개다."

opi 측 추가 문안(§공통 절 말미, 형제 항목으로):
```markdown
5. `.gitignore`에 `.opal-worktrees/` 한 줄을 **멱등 보장**한다 — 없으면 추가, 이미 있으면 파일을 변경하지 않는다.
   - 초기화·최신화 두 모드 모두에서 수행한다(아직 `--wt`를 쓰지 않는 기존 프로젝트도 선반영).
   - 이유: 미비 시 `--wt` 사용 순간 루트 레포가 worktree 사본 전체를 변경분으로 인식한다.
   - 축 정의: `opal/core/references/opal-harness.md` §2.5.
```

#### 3.7.3 환경 변경 / 배치

- 검증 환경 수동 계층(TASK C-5 계층 3): revup·mams `.gitignore` 2곳에 항목 추가 — **본 태스크의 검증 환경 조작이며 OPAL 저장소 산출물이 아니다**(§4.2 Step 19·20에 포함).

#### 3.7.4 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | F-7 AC(멱등) (H-6) | 기능 테스트 | `create` 2회 실행 → `.gitignore`의 `.opal-worktrees/` 행 수 == 1 |
| TS-061 | F-7 AC(무변경) (H-6) | 기능 테스트 | 항목이 이미 있는 `.gitignore` → `create` 후 `sha256` 동일, mtime 변화 없음 |
| TS-062 | F-7 AC | 기능 테스트 | `.gitignore` 부재 프로젝트 → 생성 후 1행, 응답 `gitignore == "created"` |
| TS-063 | F-7 AC | 기능 테스트 | 마지막 줄에 개행이 없는 `.gitignore` → 추가 후 기존 마지막 줄이 손상되지 않음 |
| TS-064 | F-7 AC(opi) | 산출물 검사 | `opal-project-init/SKILL.md` §공통 절에 `.opal-worktrees/` 멱등 보장 항목 존재 |

---

### F-008: CLOSE 정리 안내 게이트 + `remove` 3중 가드

#### 3.8.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/worktree-tool/worktree_tool.py` | BE | `cmd_remove` + 3중 가드 판정 함수 | (→ D-1 §C-6) |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | STEP 6에 안내 스텝 5 삽입(기존 5 "완료 보고" → 6) + 변경이력 1행 | `opal-pilot-dev/SKILL.md:236-264` |

#### 3.8.2 `remove` 3중 가드 설계

```python
GUARD_ORDER = ("dirty", "unpushed", "unmerged")   # [MUST] 판정 순서 고정 — 첫 위반에서 즉시 반환

def check_guards(wt_path: pathlib.Path, git_root: pathlib.Path,
                 branch: str, base_ref: str) -> tuple[str | None, dict]:
    """(위반 코드 | None, 상세) 반환. 판정 순서는 작업본 → 로컬 → 원격 순으로 고정한다."""
    # ① dirty — git-sync-tool과 동일 패턴 (git_sync_tool.py:123)
    if _run_git(["status", "--porcelain"], wt_path).stdout:
        return "GUARD_DIRTY", {...}

    # ② unpushed — upstream이 있으면 @{u}..HEAD, 없으면 base_ref..HEAD (원격에 아예 없으므로)
    up = _run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], wt_path)
    ref = up.stdout.strip() if up.returncode == 0 else base_ref
    n = int(_run_git(["rev-list", f"{ref}..HEAD", "--count"], wt_path).stdout.strip() or 0)
    if n > 0:
        return "GUARD_UNPUSHED", {"unpushed": n, "compared_to": ref}

    # ③ unmerged — base_ref는 메타에서 읽은 동결 값 (DEC-3). 재해석하지 않는다.
    merged = _run_git(["branch", "--merged", base_ref, "--format=%(refname:short)"], git_root).stdout.split()
    if branch not in merged:
        return "GUARD_UNMERGED", {"base_ref": base_ref}

    return None, {}
```

`cmd_remove` 흐름:
1. 메타 로드 → 부재 시 `META_NOT_FOUND`(`--force`로만 우회)
2. entry마다 `check_guards()` → 위반 시 **첫 위반 코드로 즉시 `{"ok": false}`**. `--force`면 위반을 `bypassed_guards[]`에 수집하고 계속.
3. `git worktree remove <path>`(`--force` 시 `--force` 부가)
4. **브랜치는 삭제하지 않는다** — 커밋 보존(user sovereignty). 회수 대상은 작업 디렉토리뿐이다.
5. 메타 파일 삭제 후 `ok_response(command="remove", removed=[...], forced=args.force, bypassed_guards=[...])`

> [MUST] TASK.md F-8 AC: "dirty·unpushed·미머지 3조건 각각에서 `remove`가 `{"ok": false}`와 조건별 고유 에러 코드를 반환하고, 3조건 모두 해소된 상태에서만 제거에 성공한다. `--force` 지정 시에만 우회되며 **우회 사실이 stdout에 기록**된다."
> → `forced`·`bypassed_guards` 필드가 stdout JSON에 실린다.

#### 3.8.3 opd CLOSE 안내 스텝

`opal-pilot-dev/SKILL.md` STEP 6에 삽입(기존 스텝 4 "회고 하드스텝" 뒤, 기존 5 "완료 보고"를 6으로):
```markdown
5. **worktree 정리 안내** (`--worktree`/`--wt` 태스크에서만 — 미사용 시 자연 스킵):
   - `~/.opal/tools/worktree-tool/run.sh status --project-root <프로젝트 루트> --task <NNN>`으로 현재 상태를 조회해 보고한다.
   - **[MUST] 자동 제거하지 않는다.** CLOSE 시점에 미머지 커밋이 남아 있는 것이 정상이다 — 커밋·머지는 캡틴의 권한이며 PM이 대행하지 않는다.
   - 안내 문구: "worktree `{worktree_root}`는 **머지 대기** 상태입니다. 머지·PR 처리 후 `~/.opal/tools/worktree-tool/run.sh remove --project-root <루트> --task <NNN>`으로 회수하세요."
   - `status` 호출 실패·메타 부재·worktree 부재는 전부 **no-op** — op-brain-ingest(스텝 3)·회고(스텝 4)와 동일하게 **CLOSE를 중단시키지 않는다**.
6. 완료 보고
```

> **범위 한정 근거**: [MUST] TASK.md §범위(제외): "pilot 10종 SKILL.md 개별 수정 금지. 단 `opal-pilot-dev/SKILL.md`의 F-8 CLOSE 안내 스텝 1개는 예외로 허용된다." → 나머지 pilot 9종의 CLOSE에는 안내를 넣지 않는다(§9 R-3에 후속 과제로 기재).

#### 3.8.4 환경 변경 / 배치

해당 없음. 변경이력 행 추가 의무 적용.

#### 3.8.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-070 | F-8 AC(dirty) (H-5) | 통합 테스트 | worktree에 미커밋 변경만 만든 상태 → `remove`가 `{"ok":false,"error":"GUARD_DIRTY"}` |
| TS-071 | F-8 AC(unpushed) (H-5) | 통합 테스트 | clean + 로컬 커밋 1개(push 없음) → `GUARD_UNPUSHED` + `unpushed:1` |
| TS-072 | F-8 AC(미머지) (H-5) | 통합 테스트 | clean + push 완료 + base 미머지 → `GUARD_UNMERGED` + `base_ref` 표기 |
| TS-073 | F-8 AC(성공) | 통합 테스트 | 3조건 모두 해소(merge 완료) → `{"ok":true}` + worktree 디렉토리 부재 + **브랜치는 잔존** |
| TS-074 | F-8 AC(`--force`) | 통합 테스트 | dirty 상태 + `--force` → `{"ok":true, "forced":true, "bypassed_guards":["GUARD_DIRTY"]}`가 stdout에 기록 |
| TS-075 | DEC-3 | 통합 테스트 | 메타 파일 삭제 후 `remove` → `META_NOT_FOUND`, `--force`로만 진행 |
| TS-076 | F-8 AC(CLOSE) | 산출물 검사 | `opal-pilot-dev/SKILL.md` STEP 6에 worktree 안내 스텝이 존재하고 "자동 제거하지 않는다"·no-op 비차단이 명시됨 |

---

### F-009: `UV_CACHE_DIR` 이전 + 볼륨 불일치 진단

#### 3.9.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/worktree-tool/worktree_tool.py` | BE | `diagnose_cache_volume()` — 비차단 경고 | (→ D-1 §C-8) |
| 2 | `~/.zshrc` (캡틴 로컬) | 환경 | `export UV_CACHE_DIR=/Volumes/Data/.uv-cache` 멱등 추가 | TASK.md §파일시스템 실측 |

#### 3.9.2 (b) 볼륨 진단 함수

```python
def diagnose_cache_volume(project_root: pathlib.Path) -> list[str]:
    """캐시·프로젝트 볼륨(st_dev) 불일치를 경고 문자열 리스트로 반환. [MUST] 절대 차단하지 않는다.

    검사 대상: UV_CACHE_DIR 환경변수 → 없으면 ~/.cache/uv
    비교: os.stat(cache).st_dev != os.stat(project_root).st_dev
    예외(경로 부재·권한 오류·st_dev 미지원)는 모두 삼켜 빈 리스트를 반환한다 — 진단 실패가
    create를 실패시키면 안 된다 (ANALYSIS R-6: Windows에서 st_dev 의미 상이).
    """
```
경고 문안 예: `"uv 캐시(/Users/x/.cache/uv, dev=16777235)가 프로젝트(/Volumes/Data/..., dev=16777230)와 다른 볼륨입니다 — 슬롯당 .venv가 실복사됩니다. UV_CACHE_DIR을 프로젝트와 같은 볼륨으로 옮기면 제거됩니다."`

> [MUST] TASK.md F-9 AC: "캐시·프로젝트 볼륨이 다를 때 `create`가 경고 메시지를 출력하되 **차단하지 않는다**."

```python
def diagnose_code_scan_exclude(project_root: pathlib.Path) -> list[str]:
    """DEC-5(b). {project_root}/.opal/code-scan.json이 있고 exclude에 '.opal-worktrees'가 없으면
    경고 1건. [MUST] 파일을 수정하지 않는다(DEC-5 (c) 제외 결정). 파일 부재·파싱 실패는 빈 리스트."""
```

#### 3.9.3 (a) `UV_CACHE_DIR` 이전 — 비가역 환경 변경 절차

> **[MUST] 이 절차는 캡틴 로컬 환경에 대한 비가역 변경이다.** PM·워커가 임의로 실행하지 않는다. [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." → 캡틴의 명시 승인 후에만 수행하며, 각 단계 결과를 보고한다.

**실행 절차**
| # | 명령 | 목적 |
|---|------|------|
| 1 | `df -k / && df -k /Volumes/Data && du -sh ~/.cache/uv` | 이전 전 기준선 측정(보고 필수) |
| 2 | `uv cache dir` | 현재 캐시 경로 확인 |
| 3 | `mkdir -p /Volumes/Data/.uv-cache` | 대상 디렉토리 생성 |
| 4 | `uv cache clean` | **구 캐시 삭제**(12GB) — 아래 "이전 방식 선택" 근거 참조 |
| 5 | `~/.zshrc`에 멱등 추가 — `grep -q 'UV_CACHE_DIR' ~/.zshrc \|\| echo 'export UV_CACHE_DIR=/Volumes/Data/.uv-cache  # OPAL 092' >> ~/.zshrc` | 영속화 |
| 6 | 새 셸에서 `uv cache dir` | 새 경로 반영 확인 |

**이전 방식 선택 근거**: 12GB를 볼륨 간 `mv`로 옮기면 실제 복사가 발생해 수 분~수십 분이 걸리고 중단 시 반쪽 상태가 남는다. **uv 캐시는 재생성 가능한 파생물**이므로 `uv cache clean` 후 새 경로에서 재구축하는 편이 단순하고 실패 위험이 낮다(첫 `uv sync`만 느려지며 이후는 동일). 데이터 손실이 아니다.

**검증** (TASK F-9 AC (a))
| # | 명령 | 기대 |
|---|------|------|
| 1 | `cd /Volumes/Data/StoreLinkStudio/mams/workspace/backend && uv sync` | 정상 완료(exit 0) |
| 2 | `df -k /Volumes/Data` (신규 `.venv` 생성 전/후) | **실디스크 증가 측정치를 보고**한다 |
| 3 | `stat -f "%d" /Volumes/Data/.uv-cache /Volumes/Data/StoreLinkStudio/mams` | `st_dev` 동일 |
| 4 | `worktree-tool create` 재실행 | 볼륨 경고가 `warnings[]`에서 **사라짐** |

**복구 절차** (완전 무손실)
| # | 명령 | 효과 |
|---|------|------|
| 1 | `~/.zshrc`에서 `# OPAL 092` 마커가 붙은 export 라인 삭제 | 환경변수 원복 |
| 2 | `uv cache clean` (새 셸 진입 전, 새 경로 정리) | 신규 캐시 제거 |
| 3 | `rm -rf /Volumes/Data/.uv-cache` | 디렉토리 회수 |
| 4 | 새 셸에서 `uv sync` | `~/.cache/uv`에 캐시 자동 재구축 → 원상 복귀 |

#### 3.9.4 환경 변경

- `UV_CACHE_DIR=/Volumes/Data/.uv-cache` (캡틴 로컬 셸 프로파일).
- **OPAL 저장소에는 어떤 환경 설정도 추가하지 않는다** — [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지". 경로 `/Volumes/Data`는 캡틴 로컬 사실이지 도구 로직에 들어가지 않는다(도구는 `st_dev` 비교만 한다).

#### 3.9.5 배치/마이그레이션

해당 없음(캐시 재구축은 uv가 자동 수행).

#### 3.9.6 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-080 | F-9 AC(b) (H-12) | 기능 테스트 | `UV_CACHE_DIR`을 다른 볼륨으로 조작 → `create`가 `{"ok":true}` + `warnings[]` 비어있지 않음 (**차단 없음**) |
| TS-081 | F-9 AC(b) | 기능 테스트 | 캐시 경로 부재·권한 오류 → 예외 없이 `warnings` 빈 리스트, `create` 정상 완료 |
| TS-082 | DEC-5(b) | 기능 테스트 | `.opal/code-scan.json`에 `.opal-worktrees` 부재 → 경고 1건, **파일 무변경**(sha256 동일) |
| TS-083 | F-9 AC(a) (H-14) | 통합 테스트 | 이전 후 mams `uv sync` exit 0 + `df` 전후 측정치 보고 |
| TS-084 | F-9 AC(a) (H-14) | 통합 테스트 | 복구 절차 4단계 수행 후 `uv cache dir`이 `~/.cache/uv` 반환 + `uv sync` 정상 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **P1** | F-001 | 1 | opal-be-agent | 단독 | 스키마·템플릿 — 도구의 전제 |
| **P2** | F-002·F-007(도구)·F-008(가드)·F-009(b) | 2, 3, 4, 5 | opal-be-agent | **순차(동일 파일)** | 전부 `worktree_tool.py` 단일 파일 → **같은 디스패치에 묶어 순차 편집**(`pm/dispatch-process.md` Step 6-5) |
| **P3** | F-001·F-002·F-007·F-008 | 6 | opal-be-agent | 단독 | pytest 스위트 — P2 완료 후 |
| **P2′** | F-005 | 7, 8 | opal-be-agent | **P1~P3와 병렬** | `state_tool.py`는 worktree-tool과 파일 무교집합 |
| **P2″** | F-003·F-006·DEC-5(a) | 9, 11, 17 | opal-task-agent | **P1~P3와 병렬** | 참조 문서·설정 — 도구 코드와 무관 |
| **P4** | F-004 | 10 | opal-task-agent | 순차 | F-002·F-005 완료 후(훅이 두 도구를 모두 호출) |
| **P5** | F-007(opi)·F-008(CLOSE) | 12, 13 | opal-task-agent | 병렬 | 스킬 문서 2종, 파일 무교집합 |
| **P6** | 배포·문서 | 14, 15, 16, 18 | opal-task-agent / **PM 직접**(16) | 순차 | install → tools.md → docs/ → 재배포·diff 0 검증 |
| **P7** | 실환경 검증 | 19, 20 | opal-task-agent | 병렬 | revup(A) · mams(B) — 서로 다른 프로젝트 |
| **P8** | F-009(a) | 21 | **PM 직접(캡틴 실행)** | 최종 | 비가역 로컬 환경 변경 — 명시 승인 필수 |

### 4.2 실행 체크리스트

> 총 21개 Step | Phase 8개 | 실행 모드: **복잡**

#### Step 1: `.opal/worktree.json` 스키마 문서 + 유형 A/B 템플릿 작성
- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/schema/worktree.schema.json`, `opal/templates/worktree-multi-repo.json`, `opal/templates/worktree-monorepo.json`
- **작업 내용**: §3.1.2의 7키 스키마(`layout`/`repos`/`branchTemplate`/`baseBranch`/`copy`/`setup`/`portOffset`)를 JSON Schema draft-07로 기술한다(런타임 미로드 문서 SSOT — DEC-4). `state.schema.json` 스타일(`description` 한국어, `required` 명시)을 따른다. 템플릿 2종은 §3.1.2 본문 값 그대로 작성한다.
- **완료 기준**: 3파일 존재 + `python -c "import json;[json.load(open(p)) for p in [...]]"` 성공 + 스키마 `required`가 `["layout","repos"]`
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `worktree-tool` 골격 — run.sh · ERROR_CODES · 응답 계약 · config 로더/검증
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/run.sh`, `opal/tools/worktree-tool/worktree_tool.py`
- **작업 내용**: `run.sh`는 `opal/tools/git-sync-tool/run.sh:1-10`을 도구명만 바꿔 복제한다. `worktree_tool.py`에 @header 블록, §3.2.2의 `ERROR_CODES` 17종, `ok_response`/`err_response`, `_run_git`(리스트 인자·`shell=True` 금지), `argparse` 4서브파서 골격, §3.1.3의 `load_config`/`validate_worktree_config`/`_is_inside`를 작성한다.
- **완료 기준**: `python worktree_tool.py list --project-root <임시>` 호출 시 단일 라인 JSON 반환 + 유형 A/B 템플릿이 검증 통과 + 3종 부적합이 각각 고유 코드 반환
- **테스트**: TS-002, TS-003, TS-004, TS-005, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1


> **[PM 승인 이탈 — 2026-08-15]** EXECUTE 워커가 §3.2.3의 `worktree add -b <branch>` **단일 명령**을
> `worktree add --detach` → `checkout -b <branch>` **2단계 분리**로 변경했다. 근거(워커가 재현으로 확인):
> git은 브랜치 ref를 먼저 기록한 뒤 `.git/worktrees/` 등록에서 실패할 수 있어, 그 경우 **고아 브랜치**가 남고
> `_rollback()`이 이를 항상 지우지는 못한다(권한 제약 시). 이는 PLAN 자신의 H-7(롤백 원자성)을 깨뜨린다.
> 분리하면 `add` 실패 시 애초에 브랜치가 만들어지지 않는다. monorepo는 detached→브랜치 전환이 같은 커밋이라
> sparse 파일이 물질화되지 않으므로 `checkout -b` 후 `git reset --hard HEAD` 1줄을 추가했다.
> **판정**: PLAN 설계 의도(H-7)를 더 잘 만족하는 개선이므로 승인한다(`opal-harness-agentic.md` §3 폴백 승인 의무 —
> "더 나은 방식이라면 PM 승인 후 허용한다"). 구현 실코드: `worktree_tool.py:456-480`.
#### Step 3: `create` 서브명령 — pre-flight · base-ref 동결 · layout 분기 · 롤백 · 메타 기록
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/worktree_tool.py`
- **작업 내용**: §3.2.3 알고리즘을 구현한다 — (1) pre-flight 4종 선검사 → (2) `resolve_base_ref()` 3단(DEC-3) → (3) multi-repo/monorepo 분기(**monorepo는 `--no-checkout` → `sparse-checkout init --cone` → `set` → `checkout` 순서 [MUST]**) → (4) 실패 시 `_rollback()`으로 자기 생성물만 회수(DEC-2) → (5) `copy[]` 복사(원본 부재는 비차단 경고) → (6) **`setup[]`은 실행하지 않고 `pending_setup`으로 열거만**(C-7) → (7) `.opal-worktrees/.meta/task_{NNN}.json` 동결 기록.
- **완료 기준**: 유형 A/B 임시 fixture에서 `create`가 `ok:true` + `entries[].base_ref` 기록 + 메타 파일 생성 + 유형 B에서 `tasks/`·`.opal/` 미체크아웃
- **테스트**: TS-010, TS-011, TS-013, TS-014, TS-015, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: `create` 부수 효과 — `.gitignore` 멱등 · 볼륨 진단 · code-scan 경고
- [x] 완료
- **소속 기능**: F-007, F-009, DEC-5(b)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/worktree_tool.py`
- **작업 내용**: §3.7.2 `ensure_gitignore_entry()`(**이미 있으면 write 자체를 하지 않는다** — 바이트 무변경), §3.9.2 `diagnose_cache_volume()`·`diagnose_code_scan_exclude()`(둘 다 **비차단**, 예외는 삼켜 빈 리스트)를 추가하고 `cmd_create`에 배선한다. 진단은 파일을 **수정하지 않는다**(DEC-5 (c)).
- **작업 내용(PM 추가 — DEC-6)**: `diagnose_concurrent_slots()`를 함께 추가한다. `.opal-worktrees/.meta/`의 기존 엔트리를 세어 **이번 슬롯 포함 2개 이상이면** `warnings[]`에 "동시 슬롯 N개 — 공유 자원(개발 DB·포트·compose 프로젝트명) 충돌 주의" 경고를 넣는다. **비차단**(`ok:true` 유지)이며 파일을 수정하지 않는다. 메타 디렉토리 열거만 하므로 `list` 로직을 재사용한다.
- **완료 기준**: `create` 2회 실행 후 `.gitignore` 행 수 1 + 기존 항목 존재 시 sha256 불변 + 볼륨 불일치 시 `ok:true` + `warnings[]` 비어있지 않음 + **슬롯 2개째 `create` 시 동시 슬롯 경고 출현·`ok:true` 유지**
- **테스트**: TS-060, TS-061, TS-062, TS-063, TS-080, TS-081, TS-082, TS-085
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: `list` / `status` / `remove` — 3중 가드 구현
- [x] 완료
- **소속 기능**: F-002, F-008
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/worktree_tool.py`
- **작업 내용**: §3.2.4의 `list`/`status`, §3.8.2의 `check_guards()`(판정 순서 dirty→unpushed→unmerged 고정, 첫 위반 즉시 반환)와 `cmd_remove`를 구현한다. base-ref는 **메타에서만 읽고 재해석하지 않는다**(DEC-3). `remove`는 worktree 디렉토리만 회수하고 **브랜치를 삭제하지 않는다**. `--force` 시 `forced`·`bypassed_guards`를 stdout JSON에 기록한다.
- **완료 기준**: 3조건 각각이 고유 코드로 거부되고, 전조건 해소 시에만 성공하며, `--force` 우회가 stdout에 기록됨
- **테스트**: TS-070 ~ TS-075
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: `worktree-tool` pytest 스위트 작성
- [x] 완료
- **소속 기능**: F-001, F-002, F-007, F-008, F-009(b)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/worktree-tool/tests/conftest.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- **작업 내용**: `git-sync-tool/tests/conftest.py` 패턴으로 fixture를 구성한다 — 유형 A(bare remote 2 + clone 2 + 프로젝트 루트), 유형 B(`workspace/`·`tasks/`·`.opal/` 보유 monorepo clone), 가드용 상태 3종(dirty/unpushed/unmerged). **[MUST] mock/patch 금지 — 실 git 저장소만 사용하고, 내부 함수 import 없이 CLI 서브프로세스 호출로만 검증한다**(`git-sync-tool/tests/conftest.py` `run_sync_cli` docstring). 모든 git 호출에 `-c user.email/-c user.name/-c commit.gpgsign=false/-c init.defaultBranch=main` 주입.
- **완료 기준**: `pytest opal/tools/worktree-tool/tests/ -q` 전량 pass, TS-001~TS-016·TS-060~TS-063·TS-070~TS-075·TS-080~TS-082 커버
- **완료 기준(PM 추가 — 목표-커버 게이트 iteration 1 gaps)**: 아래 4개 시나리오의 테스트 케이스가 본 스위트에 포함된다.
  - **S-24 파이프라인 관통** (`[T092/L2-F4b]`) — `worktree-tool create` → 응답 `worktree_root` → `state-tool init --worktree` 순으로 **실제 호출**하여 `state show --format json`의 `data.worktree`가 일치함을 확인. `create` 실패 시 `--worktree` 미전달 + `state init` 성공(비차단) 경로도 함께 검증. **state-tool을 subprocess로 호출**하므로 conftest에 state-tool 경로 fixture를 추가한다.
  - **S-25 `status` + CLOSE 안내** (`[T092/L2-F2c]`) — 4상태에서 `status`가 `ok:true`로 remove와 동일 판정을 보고. `opal-pilot-dev/SKILL.md` 안내 문안 grep 포함.
  - **S-26 config 부재·무효** (`[T092/L2-F3b]`) — `CONFIG_NOT_FOUND`/`CONFIG_INVALID_JSON` + **부수효과 0**(`.gitignore` sha256 불변·`.opal-worktrees/` 미생성).
  - **S-27 중복 생성 거부** (`[T092/L2-F2e]`) — 살아 있는 슬롯 재생성 거부 + 기존 자산 무손상.
- **테스트**: 상기 TS 전체
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: `state-tool init --worktree` 추가 + 스키마 문서 갱신
- [x] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: §3.5.2대로 argparse 1행(`state_tool.py:2461` 인근)과 `cmd_init` 조건부 대입 블록(`state_tool.py:1247` 직후)을 추가하고, `state.schema.json` `properties`에 `worktree` optional을 추가한다(`required` 미변경). **[MUST] `_build_new_state_md` 시그니처·`render_pipeline_table`·`build_todo_mirror`·`cmd_show`를 변경하지 않는다** — STATE.md 렌더 diff 0 보장. **[MUST] `state["worktree"] = args.worktree`를 무조건 실행하지 않는다** — 미지정 시 키 자체가 없어야 한다.
- **완료 기준**: `--worktree` 지정 시 키 존재 + `show --format json`의 `data.worktree` 노출 / 미지정 시 `"worktree" not in state` / STATE.md diff 0
- **테스트**: TS-040, TS-041, TS-042, TS-043, TS-045
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1~6과 병렬)

#### Step 8: state-tool 회귀 스위트 전량 실행 + 신규 케이스 추가
- [x] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-040~TS-043·TS-045 케이스를 기존 스위트에 **추가만** 한다(기존 케이스 수정 금지). 그 후 `pytest opal/tools/state-tool/tests/ -q` 전량 실행.
- **완료 기준**: **기존 케이스 0 fail** + 신규 케이스 전부 pass (TASK 완료기준 ⑦)
- **테스트**: TS-044
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: `opal-harness.md` §2.5 신설 + §9 도구 표 등록
- [x] 완료
- **소속 기능**: F-003
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §3.3.3 문안으로 **§2.5**(정수 번호 금지 — H-13)를 §2 모듈 구조 직후에 신설하고, §9 "현재 등록된 도구" 표(`opal-harness.md:260` 뒤)에 worktree-tool 행을 추가한다. 변경이력 표에 `(092)` 행 추가.
- **완료 기준**: §2.5의 3항목 전부 기재 + §3~§10 번호 불변 + `grep -rn "opal-harness.md §" opal/ docs/` 결과가 전부 유효 절 지시 + 변경이력 행 존재
- **테스트**: TS-020, TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: 없음 (병렬)

#### Step 10: `task-process.md` 스텝 4.5 worktree 생성 훅 삽입
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/task-process.md`
- **작업 내용**: §3.4.2 문안으로 스텝 4와 5 사이에 **4.5**를 삽입하고, 스텝 5 코드블록에 `[--worktree <worktree_root 절대경로>]` 1행을 추가한다. **[MUST] 기존 스텝 3·4·5·6의 번호·본문 문구를 변경하지 않는다**(TASK F-4 AC). 실패 정책(DEC-2 — 롤백 금지·agentic 자동 계속)을 명문화한다. 변경이력 `(092)` 행 추가.
- **완료 기준**: 4.5 존재 + `git diff`에서 기존 스텝 라인 미변경(옵션 1행 추가 제외) + DEC-2 정책 명문화
- **테스트**: TS-030, TS-031, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 3, Step 7 (훅이 두 도구 계약을 모두 참조)

#### Step 11: `dispatch-process.md` 문서 루트/코드 루트 경로 계약 추가
- [x] 완료
- **소속 기능**: F-006
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**: §3.6.2 문안으로 워커 컨텍스트 주입 템플릿(`dispatch-process.md:85-103`)에 조건부 `## 작업 경로` 블록을 추가하고, 코드블록 뒤에 "`--wt` 미사용 시 미주입 + 기존 경로 필드 대체 금지" 주석을 단다. 변경이력 `(092)` 행 추가.
- **완료 기준**: "상대경로 금지·절대경로 주입" 문구 + 2필드 계약 존재 + 기존 4블록 문구 무변경
- **테스트**: TS-050, TS-051
- **실행 방법**: sub-agent
- **의존**: 없음 (병렬)

#### Step 12: `opal-pilot-dev/SKILL.md` STEP 6 worktree 정리 안내 스텝 삽입
- [x] 완료
- **소속 기능**: F-008
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: §3.8.3 문안으로 STEP 6에 안내 스텝 5를 삽입하고 기존 5(완료 보고)를 6으로 조정한다. **[MUST] 이 파일 외 pilot 9종은 건드리지 않는다**(TASK §범위 제외). 변경이력 `(092)` 행 추가.
- **완료 기준**: 안내 스텝 존재 + "자동 제거하지 않는다" + no-op 비차단 명시 + 나머지 pilot 9종 diff 0
- **테스트**: TS-076, TS-021
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 13: `opal-project-init/SKILL.md` `.gitignore` opi 계층 추가
- [x] 완료
- **소속 기능**: F-007
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-project-init/SKILL.md`
- **작업 내용**: §3.7.2의 opi 문안을 §"공통: 프로젝트 로컬 설정(setting.local.json) 보장" 절(`opal-project-init/SKILL.md:66-80`)에 형제 항목 5로 추가한다. **opi의 기존 1회성 조건(생성한 경우에만)을 복제하지 않고 "두 모드 모두에서 멱등 보장"으로 기술한다**(ANALYSIS §4-5). 변경이력 `(092)` 행 추가.
- **완료 기준**: 항목 존재 + 초기화·최신화 두 모드 적용 명시 + 기존 setting.local.json 항목 문구 무변경
- **테스트**: TS-064
- **실행 방법**: sub-agent
- **의존**: 없음 (병렬)

#### Step 14: `install-mac.sh` worktree-tool chmod 블록 추가
- [x] 완료
- **소속 기능**: F-002
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §3.2.5 3줄 블록을 code-scan 블록 직후(`scripts/install-mac.sh:1202` 뒤)에 추가한다. **[MUST] 디렉토리 자체는 `install_dir "$opal_dir/tools"`가 자동 배포하므로 별도 등록 코드를 추가하지 않는다** — chmod 블록만 필요하다(ANALYSIS §4-4). 파일 상단 변경이력 주석에 `v4.x 2026-08-15: worktree-tool run.sh 실행 권한 chmod 블록 추가 (092)` 1행 추가.
- **완료 기준**: 블록 존재 + 기존 12개 chmod 블록과 동형 3줄 구조 + 헤더 변경이력 행
- **테스트**: TS-017
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 15: `tools.md`에 worktree-tool 섹션 추가
> **[PM 정정 — 2026-08-15]** §3.2.2가 `ERROR_CODES` **17종**으로 기술했으나 구현 실물은 **18종**이다(`worktree_tool.py` 실측). `tools.md`는 코드를 SSOT로 삼아 18종으로 기재했다(`harness/doc-code-mismatch.md` — 문서·코드 불일치 시 코드가 SSOT).
- [x] 완료
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md`
- **작업 내용**: `tools.md:900-937` git-sync-tool 섹션과 동일 포맷(용도/실행 경로/소스 경로/의존성/호출자 → 트리거 조건 → 커맨드 → 출력 형식)으로 worktree-tool 섹션을 추가한다. 4서브명령 시그니처·`ERROR_CODES` 17종·응답 필드·exit code를 §3.2.2에서 옮긴다. 변경이력 `(092)` 행 추가.
- **완료 기준**: 섹션 존재 + 4서브명령 전부 기재 + 에러 코드 카탈로그 기재 + 변경이력 행
- **테스트**: 산출물 검사 (QA-1)
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 16: docs/ 갱신 — ARCHITECTURE · CONVENTIONS(DEC-1 포함) · PROJECT
- [x] 완료
- **소속 기능**: F-002, DEC-1
- **영역**: 문서
- **agent**: **PM 직접**
- **파일**: `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/PROJECT.md`
- **작업 내용**:
  1. `docs/ARCHITECTURE.md:81` 도구 인벤토리 **18종 → 19종** + "환경·배포" 범주에 `worktree-tool/` 설명 추가, `docs/ARCHITECTURE.md:395` 인근 트리에 1행 추가.
  2. `docs/CONVENTIONS.md` §도구 우선 원칙의 "전체 목록: `opal/tools/` (18종)" → **19종** + 목록에 `worktree-tool` 추가.
  3. **`docs/CONVENTIONS.md` §브랜치 전략에 DEC-1 문안 추가** — "위 규칙은 OPAL 저장소 자체에만 적용된다. worktree 대상 프로젝트의 코드 브랜치는 `.opal/worktree.json`의 `branchTemplate`(기본 `feat/OP-TASK-{NNN}`)을 따른다."
  4. `docs/PROJECT.md` §폴더 구조맵 `opal/tools/` 행 "18종 → 19종" + 변경이력 행.
  5. 3문서 모두 변경이력 표에 `(092)` 행 추가.
- **완료 기준**: 19종 정합(3문서 일치) + DEC-1 문안 존재 + 변경이력 3행
- **테스트**: 산출물 검사 (QA-2)
- **실행 방법**: direct
- **의존**: Step 14

#### Step 17: OPAL 저장소 `.opal/code-scan.json` exclude에 `.opal-worktrees` 추가
- [x] 완료
- **소속 기능**: DEC-5(a)
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `.opal/code-scan.json`
- **작업 내용**: `exclude` 배열(`.opal/code-scan.json:9-10`)의 `"specs"` 뒤에 `".opal-worktrees"` 1개를 추가한다. **[MUST] 배열 원소 1개 추가 외 어떤 키·포맷도 변경하지 않는다**(들여쓰기 보존).
- **완료 기준**: `exclude`에 항목 존재 + `code-scan scan framework`가 정상 동작(exit 0) + diff가 1행
- **테스트**: 산출물 검사 (QA-3)
- **실행 방법**: sub-agent
- **의존**: 없음 (병렬)

#### Step 18: install 재배포 + pilot 10종 diff 0 검증
- [x] 완료
- **소속 기능**: F-002, F-003
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: (검증 전용 — 파일 변경 없음)
- **작업 내용**: `./scripts/install-mac.sh` 실행 후 ① `test -x ~/.opal/tools/worktree-tool/run.sh` ② `~/.opal/tools/worktree-tool/run.sh list --project-root $(pwd)` JSON 반환 ③ `~/.opal/templates/worktree-*.json` 배포 확인 ④ `git diff --stat opal/skills/opal-pilot-*/SKILL.md`가 `opal-pilot-dev` 1건뿐인지 확인 ⑤ `grep -rn "opal-harness.md §" opal/ docs/` dangling 0.
- **완료 기준**: ①~⑤ 전부 통과
- **테스트**: TS-017, TS-021, TS-022
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 8, Step 9, Step 10, Step 11, Step 12, Step 13, Step 14, Step 15, Step 16

#### Step 19: revup(유형 A) 실환경 검증
- [x] 완료
- **소속 기능**: F-002, F-007
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `/Volumes/Data/StoreLinkStudio/revup/.opal/worktree.json`(신규), `/Volumes/Data/StoreLinkStudio/revup/.gitignore`(수동 계층)
- **작업 내용**: 유형 A 템플릿을 revup에 배치하고(`repos`는 실제 `workspace/` 하위 clone 2개 실경로로 조정) `create --task 092`를 실행한다. **[MUST] 검증 후 `remove`로 원복한다** — 캡틴 작업 환경에 잔여물을 남기지 않는다. `.gitignore` 수동 계층 1행 추가(TASK C-5 계층 3).
- **완료 기준**: [MUST] TASK 완료기준 ①: "revup에서 `--wt` 실행 시 코드 레포 2개 worktree + `feat/OP-TASK-092` 규칙 브랜치 생성 확인". `git worktree list`가 각 코드 레포에서 신규 항목 1개씩 표시 + `.gitignore` 멱등(2회 실행 1행)
- **테스트**: TS-010, TS-060
- **실행 방법**: sub-agent
- **의존**: Step 18

#### Step 20: mams(유형 B) 실환경 검증
- [x] 완료
- **소속 기능**: F-002, F-007
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `/Volumes/Data/StoreLinkStudio/mams/.opal/worktree.json`(신규), `/Volumes/Data/StoreLinkStudio/mams/.gitignore`(수동 계층)
- **작업 내용**: 유형 B 템플릿을 mams에 배치하고 `create --task 092`를 실행한다. **[MUST] 검증 후 `remove`로 원복한다.** 스키마 마이그레이션 동반 태스크 경고(TASK §제약 DB 동시성)는 이번 범위에서 도구 구현 대상이 아니므로 검증 항목에서 제외한다.
- **완료 기준**: [MUST] TASK 완료기준 ②: "mams에서 sparse worktree 생성 + `tasks/`·`.opal/` 미체크아웃 확인". `ls .opal-worktrees/task_092/`에 `workspace/`만 존재 + `copy[]` 2파일 복사됨 + `setup[]` 미실행(`.venv`·`node_modules` 부재) + `pending_setup[]` 열거
- **테스트**: TS-011, TS-016, TS-060
- **실행 방법**: sub-agent
- **의존**: Step 18

#### Step 21: `UV_CACHE_DIR` 이전 + 실디스크 측정 보고 (캡틴 실행)
- [x] 완료
- **소속 기능**: F-009(a)
- **영역**: 환경
- **agent**: **PM 직접** (캡틴 명시 승인 후 실행)
- **파일**: `~/.zshrc` (캡틴 로컬 환경 — OPAL 저장소 산출물 아님)
- **작업 내용**: §3.9.3의 실행 절차 6단계 → 검증 4항목 → (필요 시) 복구 4단계. **[MUST] 비가역 환경 변경이므로 캡틴의 명시 승인 없이 착수하지 않는다.** 절차·검증·복구를 먼저 제시하고 승인을 받은 뒤 단계별로 결과를 보고한다. `uv cache clean` 선택 근거(캐시는 재생성 가능한 파생물 / 12GB 볼륨 간 mv 회피)를 함께 설명한다.
- **완료 기준**: [MUST] TASK 완료기준 ⑥: "`UV_CACHE_DIR` 이전 후 `uv sync` 정상 완료 + 신규 `.venv` 실디스크 증가 측정치 보고". 추가로 `create` 재실행 시 볼륨 경고가 `warnings[]`에서 사라짐(H-12 반증), 복구 절차 유효성 확인
- **테스트**: TS-083, TS-084
- **실행 방법**: direct
- **의존**: Step 20

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → 2 → 3 → 4 → 5 → 6 | **전부 `worktree_tool.py` 단일 파일을 순차 편집**한다. [MUST] `opal/core/references/pm/dispatch-process.md` Step 6-5: "동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다(동시 편집 시 후행 저장이 선행 편집을 덮어쓰는 충돌 방지)." → Step 2~6은 **단일 디스패치**로 배치한다. |
| Step 7 → 8 | 동일 파일 계열(`state_tool.py` → 그 테스트) 순차 |
| Step 1~6 ∥ Step 7~8 | 파일 무교집합(`worktree-tool/` vs `state-tool/`), 기능 의존 없음 |
| Step 1~8 ∥ Step 9, 11, 13, 17 | 참조 문서·스킬·설정 — 도구 코드와 파일 무교집합 |
| Step 3, 7 → Step 10 | 스텝 4.5 훅이 `worktree-tool create` 응답 계약과 `state init --worktree` 인자를 **둘 다** 참조 |
| Step 5 → Step 12, 15 | CLOSE 안내와 tools.md 문서가 `status`/`remove` 최종 계약을 인용 |
| Step 2 → Step 14 | chmod 블록이 `run.sh` 실존을 전제 |
| Step 14 → Step 16 | docs/ 도구 19종 정합이 배포 등록 완료를 전제 |
| Step 9, 11 ∥ Step 13 | 3파일 모두 무교집합(references 2 + skills 1) |
| Step 18 → Step 19 ∥ Step 20 | 실환경 2건은 서로 다른 프로젝트라 병렬. 단 배포(Step 18) 완료가 선행 필수 |
| Step 20 → Step 21 | `UV_CACHE_DIR` 이전 효과(볼륨 경고 소거)를 mams 검증 결과와 대조해야 함 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 유형 A/B 템플릿 2종 검증 통과 | TS-001 | 정규화 dict 반환, 기본값 채워짐 |
| F-001 | 3종 부적합 고유 에러 코드 | TS-002, TS-003, TS-004 | `CONFIG_MISSING_KEY`/`CONFIG_INVALID_LAYOUT`/`CONFIG_PATH_ESCAPE` 각각 반환 |
| F-002 | 4서브명령 JSON `ok` 계약 | TS-012 | 4개 모두 단일 라인 JSON + `ok` 키 |
| F-002 | 유형 A 다중 worktree 생성 | TS-010, Step 19 | `repos[]` 개수만큼 worktree + 규칙 브랜치 |
| F-002 | 유형 B sparse-checkout | TS-011, Step 20 | `workspace/`만 체크아웃, `tasks/`·`.opal/` 부재 |
| F-002 | 부분 실패 원자적 롤백 | TS-013, TS-014 | 실패 후 worktree 0개·브랜치 0개 |
| F-002 | base-ref 동결 결정론 | TS-015 | `origin/HEAD` 변경 후에도 판정 불변 |
| F-002 | lazy setup (미실행) | TS-016 | sentinel 부재 + `pending_setup[]` 열거 |
| F-003 | 하네스 §2.5 3항목 | TS-020, TS-023 | 직교 축·현행 유지·config 부재 동작 + §9 도구 행 |
| F-003 | pilot 10종 diff 0 | TS-021 | opd 1건 외 diff 0 |
| F-003 | 절 번호 인용 무파괴 | TS-022 | dangling 인용 0건 |
| F-004 | 스텝 4.5 훅 존재 + 기존 스텝 불변 | TS-030, TS-031 | 4.5 존재 + 3·4·5·6 문구 무변경 |
| F-004 | 실패 정책 명문화 | TS-032 | 롤백 금지 + agentic 자동 계속 기재 |
| F-005 | `--worktree` 기록 + show 노출 | TS-040 | `data.worktree` 동일 값 |
| F-005 | 미지정 시 키 부재 | TS-041, TS-042 | `"worktree" not in state` + 바이트 동일 |
| F-005 | STATE.md 렌더 불변 | TS-043 | diff 0 |
| F-005 | 기존 회귀 스위트 전량 pass | TS-044 | 0 fail |
| F-006 | 문서/코드 루트 2필드 절대경로 계약 | TS-050, TS-051 | 문구 존재 + 조건부 주입 명시 |
| F-007 | `.gitignore` 멱등 (2회 실행 1행) | TS-060, TS-062, TS-063 | 행 수 1 + 개행 손상 없음 |
| F-007 | 기존 항목 존재 시 바이트 무변경 | TS-061 | sha256 동일 |
| F-007 | opi 계층 문안 | TS-064 | 두 모드 모두 적용 명시 |
| F-008 | `remove` 3중 가드 각 조건 거부 | TS-070, TS-071, TS-072 | 조건별 고유 코드 |
| F-008 | 전조건 해소 시에만 성공 | TS-073 | `ok:true` + 브랜치 잔존 |
| F-008 | `--force` 우회 stdout 기록 | TS-074 | `forced`·`bypassed_guards` 노출 |
| F-008 | CLOSE 안내 no-op 비차단 | TS-076 | 자동 제거 금지 + no-op 명시 |
| F-009 | 볼륨 불일치 경고 비차단 | TS-080, TS-081 | `ok:true` + `warnings[]` |
| F-009 | code-scan 경고 시 파일 무변경 | TS-082 | sha256 동일 |
| F-009 | UV 이전 후 `uv sync` + 측정 보고 | TS-083 | exit 0 + `df` 측정치 |
| F-009 | 복구 절차 유효 | TS-084 | 원상 복귀 확인 |

### 5.2 회귀 테스트

- [ ] `pytest opal/tools/state-tool/tests/` **전량 pass** — 기존 케이스 0 fail (TASK 완료기준 ⑦)
- [ ] `pytest opal/tools/git-sync-tool/tests/` 전량 pass (인접 도구 비파괴)
- [ ] `--wt` 미사용 태스크의 `state.json` 스키마·바이트가 현행과 동일 (TASK 완료기준 ③)
- [ ] `--wt` 미사용 태스크의 STATE.md 렌더 diff 0
- [ ] pilot 10종 SKILL.md diff — `opal-pilot-dev` 1건 외 0 (TASK C-9)
- [ ] `opal-harness.md §N` 형태 인용 전수 유효 (§3~§10 번호 불변)
- [ ] `task-process.md` 기존 스텝 3·4·5·6 문구 무변경
- [ ] `dispatch-process.md` 기존 템플릿 4블록 문구 무변경
- [ ] `./scripts/install-mac.sh` 재실행 후 기존 도구 12종 `run.sh` 실행 권한 유지
- [ ] `code-scan scan framework` exit 0 (Step 17 이후)

### 5.3 코드/문서 품질

- [ ] `worktree_tool.py`·`conftest.py`·`test_worktree_tool.py`에 @header 블록 작성 — [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" (기록 위치는 `code-scan target <file>` 판정을 따른다)
- [ ] 파일 네이밍 — [MUST] `docs/CONVENTIONS.md` §네이밍 규칙: "**kebab-case** 사용 (Python 파일은 **snake_case**)" → 디렉토리 `worktree-tool/`, 파일 `worktree_tool.py`
- [ ] 변경이력 행 추가 — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" → 대상 7종(`opal-harness.md`, `task-process.md`, `dispatch-process.md`, `opal-pilot-dev/SKILL.md`, `opal-project-init/SKILL.md`, `tools.md`, docs/ 3문서)
- [ ] 배포 경계 — [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 모든 변경은 `opal/`·`skills/`·`scripts/`에서만
- [ ] 플랫폼 분기 격리 — [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → `worktree_tool.py`에 macOS/APFS 조건문 없음(표준 git + POSIX `st_dev`만)
- [ ] 도구 계보 일치 — 표준 라이브러리만 import (`jsonschema` 등 외부 라이브러리 0건, DEC-4)
- [ ] `_run_git` 리스트 인자 — f-string/`shell=True` 명령 조립 0건
- [ ] docs/ 도구 인벤토리 19종이 3문서(`ARCHITECTURE.md`·`CONVENTIONS.md`·`PROJECT.md`)에서 일치

### 5.4 보안

- [ ] **경로 이탈 차단** — `repos[]`·`copy[]`에 `..`·절대경로가 오면 `CONFIG_PATH_ESCAPE`로 거부 (TS-004). worktree 생성 경로가 프로젝트 루트를 벗어나지 않는다
- [ ] **명령 주입 차단** — 모든 git 호출이 리스트 인자이며 `shell=True`가 없다. `branchTemplate`·`slug` 등 사용자 입력이 셸 문자열로 결합되지 않는다
- [ ] **브랜치명 인젝션** — `_render_branch()` 결과가 `-`로 시작하면(옵션으로 해석될 위험) 거부하거나 `--`로 구분한다
- [ ] `.gitignore`에 `.opal-worktrees/`가 보장되어 worktree 사본(로컬 설정·비밀 포함 가능)이 실수로 커밋되지 않는다 (F-007)
- [ ] `copy[]`가 복사하는 로컬 설정 파일(예: `settings.local.yaml`) 내용을 **stdout/로그에 출력하지 않는다** — 경로만 `copied[]`에 기록
- [ ] 코드에 하드코딩된 토큰/시크릿 0건 (`/Volumes/Data` 등 로컬 경로도 도구 로직에 하드코딩하지 않는다)
- [ ] `remove`가 `--force` 없이는 미커밋·미푸시 작업을 파괴하지 않는다 (F-008 3중 가드)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 21개 | **복잡** (6개 이상) |
| 변경 파일 수 | 신규 7 + 수정 12 = 19개 | **복잡** (4개 이상) |
| 모듈 범위 | 도구 2종 + 참조 문서 3종 + 스킬 2종 + 배포 스크립트 + docs 3종 + 설정 1종 | **복잡** (다중 모듈/레이어) |
| 작업 유형 | 신규 도구 개발 + 하네스 축 신설 | **복잡** |
| 외부 의존성 | 신규 도구(worktree-tool) 필요, git 2.25+ (로컬 2.50.1 충족), 신규 Python 패키지 없음 | **복잡** (새 도구 필요) |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬 4 디스패치)
  ├─ A1 [opal-be-agent]   Step 1~6   worktree-tool 전체 (단일 파일 순차 편집)
  ├─ A2 [opal-be-agent]   Step 7~8   state-tool --worktree + 회귀
  ├─ A3 [opal-task-agent] Step 9, 11 opal-harness.md §2.5 · dispatch-process.md
  └─ A4 [opal-task-agent] Step 13, 17 opi SKILL.md · code-scan.json

Batch 2 (A1·A2 완료 후, 병렬 2)
  ├─ A5 [opal-task-agent] Step 10, 14 task-process.md 훅 · install-mac.sh chmod
  └─ A6 [opal-task-agent] Step 12, 15 opd CLOSE 안내 · tools.md 섹션

Batch 3 (순차)
  └─ PM 직접             Step 16    docs/ 3문서 갱신(DEC-1 포함)

Batch 4 (순차)
  └─ A7 [opal-task-agent] Step 18   install 재배포 + diff 0 검증

Batch 5 (병렬 2)
  ├─ A8 [opal-task-agent] Step 19   revup(유형 A) 실환경
  └─ A9 [opal-task-agent] Step 20   mams(유형 B) 실환경

Batch 6 (순차, 캡틴 승인 게이트)
  └─ PM 직접             Step 21    UV_CACHE_DIR 이전
```

**그룹핑 근거**:
1. **파일 충돌 방지** — Step 2~6이 전부 `worktree_tool.py`를 수정하므로 A1 단일 에이전트에 묶었다 ([MUST] `pm/dispatch-process.md` Step 6-5).
2. **산출량 상한** — A1의 산출 파일은 `worktree_tool.py`·`run.sh`·`schema/*.json`·`templates/*.json` 2·`tests/*.py` 2 = 7개로 임계값 3을 초과한다. 다만 **Step 2~6이 동일 파일을 순차 편집하는 관계**이므로 분할 금지 규칙이 우선한다. Step 1(템플릿 3파일)을 A1 선두에 두되, 실행 시 규모가 과하면 Step 1만 별도 디스패치로 분리 가능하다(비중첩).
3. **모듈 응집도** — 참조 문서(A3)·스킬 문서(A4·A6)·배포(A5)를 도메인별로 묶었다.
4. **병렬 극대화** — Batch 1에서 도구 2종 + 문서 4종을 동시 진행한다.

### C-2. 스킬 요구사항

| 작업 | 매칭 스킬 | 갭 |
|------|----------|-----|
| Step 1~8 (Python 도구 구현) | `op-dev-execute` + `harness/coding-principles.md` | 없음 |
| Step 9~13, 15 (참조 문서·스킬 수정) | `op-dev-execute` | 없음 |
| Step 14, 18 (배포) | `op-dev-execute` | 없음 |
| Step 16 (docs/ 갱신) | PM 직접 | 없음 |
| Step 19~21 (실환경 검증·환경 변경) | `op-dev-test-scenario` → `opal-test-agent` | 없음 |

**신규 스킬 불필요** — 동일 패턴이 3개 Step 이상 반복되는 구간이 없다(도구 구현은 1개 도구, 문서 수정은 파일마다 내용이 상이).

### C-3. 도구 요구사항

| 항목 | 상태 |
|------|------|
| git 2.25+ (sparse-checkout cone mode) | **충족** — 로컬 2.50.1 실측 |
| Python 3 (`~/.opal/.venv`) | **충족** — 신규 패키지 0개 (DEC-4) |
| pytest | **충족** — 기존 도구 테스트 관행 |
| `state-tool` | 수정 대상(F-005) |
| `code-scan` | Step 17에서 exclude 갱신 후 정상 동작 확인 |
| `memory-tool` / `brain-tool` | 무영향 |
| **신규 `worktree-tool`** | **본 태스크 산출물** |
| MCP | **불필요** — 표준 git/Python 기능만 사용 (ANALYSIS §6.3) |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 명령 | 기대 |
|------|------|----------|------|
| **L1 정적** | 스키마·문서 산출물 검사 | `python -c "import json; json.load(...)"`, `grep` 기반 문구 검사 | TS-001~005, TS-020~023, TS-030~032, TS-050~051, TS-064, TS-076 |
| **L2 단위/통합** | worktree-tool | `pytest opal/tools/worktree-tool/tests/ -q` | TS-010~017, TS-060~063, TS-070~075, TS-080~082 |
| **L2 회귀** | state-tool | `pytest opal/tools/state-tool/tests/ -q` | TS-040~045 + **기존 전량 pass** |
| **L2 회귀** | 인접 도구 | `pytest opal/tools/git-sync-tool/tests/ -q` | 0 fail |
| **L3 배포** | install | `./scripts/install-mac.sh` + 권한·배포 확인 | TS-017 |
| **L3 실환경** | revup(A) · mams(B) | `worktree-tool create/status/remove` 왕복 | TASK 완료기준 ①②⑤ |
| **L3 환경** | UV_CACHE_DIR | 이전 → `uv sync` → `df` → 복구 리허설 | TASK 완료기준 ⑥ |

> **[MUST] mock 금지** — `opal/core/references/harness/coding-principles.md` §4 및 git-sync-tool 선례(`tests/conftest.py`: "RED-first 트랙(052) — 실 git 저장소만 사용, mock/patch 금지")를 따른다. worktree 동작은 실제 `git worktree add`가 아니면 검증 의미가 없다.
> **[MUST] 프레임워크 단위 테스트만으로 완료 판정하지 않는다** — TASK.md §제약 조건 §검증 환경: "revup(유형 A)·mams(유형 B) 실환경에서 실측한다." L3 실환경(Step 19·20)이 완료 조건이다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 구현 | Python 3 (표준 라이브러리 전용) | `op-dev-execute` (opal-be-agent) |
| CLI 래퍼 | Bash (`run.sh`) | `op-dev-execute` |
| VCS | git 2.50.1 — worktree, sparse-checkout cone mode | - |
| 테스트 | pytest (실 git 저장소 fixture, mock 금지) | `opal-test-agent` |
| 문서 SSOT | Markdown (하네스·참조 문서) | `op-dev-execute` (opal-task-agent) |
| 배포 | Bash (`install-mac.sh`) | `op-dev-execute` |
| 검증 대상 외부 스택 | Gradle/Kotlin(revup BE) · Vite/bun(revup FE) · uv/Python(mams BE) · pnpm/Next.js(mams FE) · docker-compose(mams) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 표준 git/Python 기능만 사용하므로 외부 라이브러리 문서 조회가 불필요하다 (ANALYSIS §6.3). git worktree·sparse-checkout 시퀀스는 ANALYSIS §2.1의 경험 기반 표준 시퀀스를 채택한다(citation-rules.md §5 "추론/경험 기반 결정" — 인용 생략 허용). |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md (본 태스크) | `tasks/092-260815-opd-워크트리-작업공간-분리/TASK.md` | 확정 방향 C-1~C-9 · 요구사항 F-1~F-9 AC · 제약 조건 · 완료기준 |
| D-2 | 설계 | ANALYSIS.md (본 태스크) | `tasks/092-260815-opd-워크트리-작업공간-분리/ANALYSIS.md` | 접합면 6곳 실측 · 의존 순서(§1.3) · 리스크 R-1~R-7 · [PM 정정] 블록 |
| D-3 | 설계 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | Core Stance(Enforce, don't just advise) · §2 Simplicity First — DEC-4·DEC-5 근거 |
| D-4 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 배포 경계 · 플랫폼 분기 금지 · 변경이력 의무 |
| D-5 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards · §2 모듈 구조(F-003 삽입 지점) · §9 도구 표 |
| D-6 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | §오케스트레이터 공통 영역 스텝 3~6(F-004 삽입 지점) |
| D-7 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 워커 컨텍스트 주입 템플릿(F-006) · Step 6-5 산출량 상한·동일 파일 묶음 규칙 |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷 · §7 용어 일관성/decision_required(DEC-1) |
| D-9 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §브랜치 전략(DEC-1) · §네이밍 · §@header · §변경이력 · §도구 우선 원칙(19종 갱신) |
| D-10 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성 전문 에이전트 매핑(Framework→opal-task-agent) · 도구 인벤토리 |
| D-11 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 도구 인벤토리 18종(→19종) · 디렉토리 트리 |
| D-12 | 소스 | git_sync_tool.py | `opal/tools/git-sync-tool/git_sync_tool.py:23-56, 99-183, 225-233` | ERROR_CODES · ok/err 응답 · `_run_git` 리스트 인자 · 판정 순서 패턴 |
| D-13 | 소스 | git-sync-tool run.sh | `opal/tools/git-sync-tool/run.sh:1-10` | `run.sh` 래퍼 표준(완전 복제 대상) |
| D-14 | 소스 | git-sync-tool conftest.py | `opal/tools/git-sync-tool/tests/conftest.py` | 실 git fixture 패턴 · mock 금지 · CLI 전용 검증 |
| D-15 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py:1138-1310, 1345-1375, 2445-2461` | `cmd_init` state dict 구성 · `cmd_show` data=state · argparse init 서브파서 |
| D-16 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json:6-8, 124` | `additionalProperties:false` · properties 추가 지점 |
| D-17 | 소스 | install-mac.sh | `scripts/install-mac.sh:1107, 1113-1114, 1117-1202` | 템플릿·도구 `install_dir` 자동 배포 + 개별 chmod 블록 12개 |
| D-18 | 소스 | opal-pilot-dev/SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md:10-19, 22-30, 236-264` | Harness 모드 파싱 · STEP 1 TASK 참조 · STEP 6 CLOSE 5스텝 구조 |
| D-19 | 소스 | opal-project-init/SKILL.md | `opal/skills/opal-project-init/SKILL.md:66-80` | `.gitignore` 멱등 추가 기존 패턴(조건 트리거 상이) |
| D-20 | 소스 | tools.md | `opal/core/references/tools.md:898-937` | 도구 문서 섹션 포맷(용도/경로/의존성/커맨드/출력) |
| D-21 | 소스 | code-scan.json | `.opal/code-scan.json:9-10` | `exclude` 배열 실측 — DEC-5(a) 대상 |
| D-22 | 소스 | requirements.txt | `opal/tools/requirements.txt` | `jsonschema` **미선언** 실측 — DEC-4 근거 1 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | **브랜치 네이밍 표기 불일치** (ANALYSIS R-1) | F-002 | 중 | **DEC-1로 종결.** 적용 대상이 다른 별개 규칙으로 확정하고 `docs/CONVENTIONS.md` §브랜치 전략에 적용 범위 2줄 추가(Step 16). `feat/OP-TASK-{NNN}` 기본값은 불변 |
| R-2 | **부분 실패 정책 미정의** (ANALYSIS R-2) | F-002, F-004 | 중 | **DEC-2로 종결.** 도구=all-or-nothing 자기 롤백 / 파이프라인=비차단 계속 / state 기록=성공 후에만. agentic에서도 정지하지 않음. 명문화 위치 = `task-process.md` 4.5(Step 10) |
| R-3 | **미머지 판정 base 미확정** (ANALYSIS R-3) | F-008 | 중 | **DEC-3으로 종결.** create가 3단 우선순위로 1회 해석 → `.opal-worktrees/.meta/task_{NNN}.json`에 동결 → remove는 재해석 없이 읽기만. 메타 부재 시 `META_NOT_FOUND` 거부 |
| R-4 | **code-scan 중복 스캔** (ANALYSIS R-4) | DEC-5 | 낮 | **DEC-5로 종결.** OPAL 저장소는 exclude 1행 추가(Step 17), 대상 프로젝트는 create의 **비차단 경고**만. 도구의 자동 JSON 편집은 부작용 대비 이득이 작아 제외 |
| R-5 | **경로 표기 규칙 이원화** (ANALYSIS R-5) | F-006 | 낮 | 신규 `## 작업 경로` 블록을 **별도 블록으로 격리**하고 기존 `**태스크 폴더**` 필드를 대체하지 않는다. `--wt` 미사용 시 미주입 → 현행 프롬프트 diff 0. "cwd 매 Bash 리셋 — 절대경로" 규범은 이미 워커 시스템 프롬프트에 존재 |
| R-6 | **`st_dev` 플랫폼 의존** (ANALYSIS R-6) | F-009 | 낮 | 경고 전용(차단 없음)이며 예외를 전부 삼켜 빈 리스트를 반환한다(TS-081). 로직이 APFS·macOS에 의존하지 않는다 — [MUST] TASK.md §제약: "표준 git 명령만 사용한다. APFS 클론·macOS 전용 동작은 성능상 이점일 뿐이며 로직이 여기에 의존해서는 안 된다" |
| R-7 | **가변 인자 git 명령의 구현 복잡도** (ANALYSIS R-7) | F-002 | 낮 | `_run_git(args: list, cwd)` 고정 시그니처를 유지하고 **인자 리스트를 호출부에서 조립**한다(`_run_git(["sparse-checkout","set",*repos], cwd)`). f-string·`shell=True` 0건을 §5.4 보안 체크로 강제 |
| R-8 | **§ 번호 삽입에 의한 대량 dangling 인용** (신규, H-13) | F-003 | 중 | 정수 번호 대신 **§2.5 소수점 번호** 채택. Step 18에서 `grep -rn "opal-harness.md §"` 전수 검사로 확인 |
| R-9 | **메타 파일이 worktree 내부에 놓이면 dirty 가드 오탐** (신규, H-4·H-5) | F-002, F-008 | 중 | 메타를 worktree **밖**(`.opal-worktrees/.meta/`)에 배치(DEC-3). `.opal-worktrees/`가 gitignore되므로 루트 레포에도 미검출 |
| R-10 | **pilot 9종 CLOSE에 worktree 안내 부재** (신규) | F-008 | 낮 | TASK §범위 제외(C-9)로 의도된 결과다. opd 외 pilot으로 `--wt`를 쓰면 CLOSE에서 안내가 나오지 않으나, `worktree-tool status/remove`는 캡틴이 언제든 수동 호출 가능하므로 기능 손실은 없다. **후속 태스크 후보로 §CLOSE 보고에 기재** |
| R-11 | **`UV_CACHE_DIR` 이전이 캡틴 개발 환경을 멈출 위험** (신규, H-14) | F-009 | **높** | 캡틴 명시 승인 게이트(Step 21) + `uv cache clean` 방식 선택(볼륨 간 12GB mv 회피) + **복구 절차 4단계 사전 제시**(§3.9.3). 캐시는 재생성 가능한 파생물이라 데이터 손실이 아니다 |
| R-12 | **실환경 검증 잔여물이 캡틴 작업 환경에 남을 위험** (신규) | F-002 | 중 | Step 19·20의 완료 기준에 **`remove`로 원복** 의무를 포함. `.opal/worktree.json`과 `.gitignore` 1행은 의도된 잔존물(TASK C-5 계층 3) |
| R-13 | **DB 동시성 경고(TASK §제약)가 이번 범위에 미구현** (신규) | - | 낮 | TASK.md §제약 "mams는 원격 공유 RDS를 사용하므로 스키마 마이그레이션 동반 태스크의 동시 실행을 도구가 경고한다"는 F-1~F-9 어느 요구사항에도 AC로 편입되지 않았다. **본 PLAN 범위에서 제외**하고 후속 과제로 기재한다 — [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement." 필요 시 `worktree.json`에 선언 키를 추가하는 후속 태스크로 다룬다 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-15 15:20 | 초기 작성 — 기능 9종(F-001~F-009) 설계, DEC-1~DEC-5 확정, 리스크 가설 15건(H-1~H-15), 실행 체크리스트 21 Step / 8 Phase, 복잡 모드 판정 (092) |

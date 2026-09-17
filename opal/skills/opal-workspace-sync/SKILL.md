---
name: opal-workspace-sync
description: |
  **워크스페이스 Git 일괄 동기화** — 워크스페이스 직속 자식 git 저장소 + 프로젝트 root 저장소를 순회하여 안전 최신화(clean+ff-only pull)하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 skip+보고+승인 후 조치.
  반드시 이 스킬을 사용해야 하는 상황: "워크스페이스 동기화", "저장소 일괄 pull", "opal-workspace-sync".
alias: opws
triggers:
  - "^opal-workspace-sync$"
  - "^opws$"
  - "(?i)(워크스페이스\\s*동기화|저장소\\s*일괄|일괄\\s*pull)"
version: "1.1"
domain: workspace
---

# opal-workspace-sync (워크스페이스 Git 일괄 동기화)

단일 pilot 구조의 operator 타입 스킬이다. 여러 독립 git 저장소가 모여 있는 워크스페이스를 순회하여, 안전하게 pull 가능한 저장소만 자동 최신화하고 문제 저장소는 건드리지 않는다.

**핵심 원칙 — 문제 저장소는 PM이 자율 조치하지 않는다.** dirty/diverged/detached/no-upstream/fetch-failed 저장소는 항상 **skip → 보고 → 제안 → 승인 후에만 조치**한다. 승인 없이 stash/rebase/merge/force/commit/push 등을 자동 실행하는 것은 절대 금지다 (헌법 user sovereignty 원칙).

## Harness

이 스킬은 단일 pilot 구조다. 하네스 부트스트랩에서 로드되지 않은 경우:
- `~/.opal/references/opal-harness.md` Read.

git-sync-tool은 `~/.opal/tools/git-sync-tool/run.sh`로 호출한다. 출력이 `"ok": false`이면 `"error"` 필드를 확인하여 사용자에게 에스컬레이션한다 (opal-harness §9).

---

## STEP 0 — Harness 확인

`~/.opal/references/opal-harness.md`가 이번 세션에서 아직 로드되지 않았다면 Read한다.

---

## STEP 1 — 대상 결정 (3분기) [스킬 책임]

대상 결정 로직은 **스킬의 책임**이다. git-sync-tool은 이미 확정된 경로를 인자로 받아 순회만 수행한다.

```
(현재 프로젝트 또는 사용자가 지정한 경로)/workspace 존재?
  ├─ 예 → 그 workspace 경로를 순회 대상으로 확정
  │        + <경로>/.git 존재 시 <경로>를 root 저장소로 함께 확정 (STEP 2에서 --root로 전달)
  └─ 아니오 → 받은 경로 자체가 단일 git 루트(<경로>/.git 존재)?
               ├─ 예 → 그 경로를 대상으로 확정 (git-sync-tool이 1개 저장소로 처리)
               └─ 아니오 → AskUserQuestion으로 워크스페이스 경로를 질의하여 확정
```

- 판단에 필요한 경로 존재 확인은 Bash(`ls`/`test -d`) 또는 Read 도구로 수행한다.
- 사용자가 이미 명시적으로 경로를 지정했다면 그 경로에 대해 위 분기를 그대로 적용한다(우선 `<경로>/workspace`, 다음 `<경로>` 자체가 단일 루트인지 확인).
- **[MUST] root 저장소 누락 금지.** `<경로>/workspace`를 순회 대상으로 확정한 경우, 순회는 workspace 직속 자식 1단계만 돌기 때문에 프로젝트 root repo가 대상에서 빠진다. `<경로>/.git`이 존재하면 반드시 `--root <경로>`로 함께 전달한다 (미전달 시 root repo는 조용히 최신화되지 않는다).
- 두 번째 분기(경로 자체가 단일 git 루트)에서는 그 경로가 곧 root이므로 `--root`를 전달하지 않는다.

### 선언 조회 (조건부)

순회 대상 경로의 **부모 디렉토리**에 `.opal/workspace.json`이 있으면 도구가 선언×디스크를 대조한다. 스킬이 따로 읽을 필요는 없고, 선언 유무에 따라 응답에 판정 필드가 붙는지만 달라진다.

- **선언 파일 없음** → 위 3분기가 그대로 끝이다. 응답에 `declaration`·`repo` 필드가 없고 판정도 수행되지 않는다. 현행 동작 100% 유지.
- **선언 파일 있음** → 응답에 `workspace_config` 경로와 저장소별 `declaration`·`repo`가 추가된다. STEP 3 보고서에 선언 관련 섹션을 포함한다.

선언 파일이 아직 없는 프로젝트에서 사용자가 선언을 만들고 싶어 하면 `init`으로 초안을 만든다. **초안은 탐지 결과일 뿐이므로 사용자 확인 없이 확정하지 않는다** — `--dry-run`으로 먼저 보여주고 승인 후 기록한다.

```bash
~/.opal/tools/git-sync-tool/run.sh init <순회 대상 경로> [--dry-run] [--force]
```

---

## STEP 2 — git-sync-tool 호출 [도구 위임]

STEP 1에서 확정된 경로로 도구를 호출한다:

```bash
~/.opal/tools/git-sync-tool/run.sh sync <확정 경로> [--root <프로젝트 root 경로>]
```

**`--root` 규칙:**
- STEP 1에서 root 저장소를 함께 확정한 경우에만 전달한다. 전달된 root는 순회 결과 **선두**에 추가된다.
- `.git`이 없는 경로를 `--root`로 주면 조용히 제외된다(에러 아님) — `.git` 없는 경로에서 git을 실행하면 상위 저장소로 올라가 엉뚱한 저장소를 조작하기 때문이다.
- root가 순회에서 이미 발견된 저장소와 동일하면 중복 계상하지 않는다.
- `--root` 미전달 시 동작은 이 옵션 도입 이전과 100% 동일하다.

**순회 규칙 (도구 책임, 참고용):**
- 순회 깊이: **직속 자식 1단계만** (재귀하지 않는다).
- pull 정책: **`git pull --ff-only`** (clean + fast-forward 가능한 저장소만 자동 pull).
- git **2.22 이상** 필요 (`git rev-list --left-right --count` 사용).

**JSON 응답 계약** (`~/.opal/tools/git-sync-tool/git_sync_tool.py` 구현 기준):

```json
{
  "ok": true,
  "command": "sync",
  "workspace": "/absolute/path/to/workspace",
  "root": "/absolute/path/to/project",
  "repositories": [
    {
      "name": "backend",
      "branch": "main",
      "upstream": "origin/main",
      "status": "updated",
      "reason": null,
      "ahead": 0,
      "behind": 3,
      "prev_head": "a1b2c3d",
      "new_head": "e4f5g6h",
      "pulled_commits": 3
    }
  ],
  "summary": { "total": 7, "updated": 4, "skipped": 2, "failed": 1 },
  "error": null
}
```

| 필드 | 설명 |
|------|------|
| `root` | `--root`로 전달되어 대상에 추가된 root 저장소 절대경로. 미전달 또는 `.git` 없어 제외된 경우 `null`. 해당 저장소는 `repositories[]` **선두**에 온다 |
| `status` | enum: `updated` \| `skipped` \| `failed` \| `already-current` |
| `reason` | enum: `dirty` \| `diverged` \| `detached` \| `no-upstream` \| `fetch-failed` (정상 상태면 `null`) |
| `upstream` | `no-upstream`이면 `null` |
| `ahead` / `behind` | 계산 불가 시 `null` |
| `prev_head` / `new_head` | `updated`에서만 유효, 그 외 `null` |
| `summary` | `total`/`updated`/`skipped`/`failed` 집계. `already-current`는 `total`에는 포함되지만 세 카운트 어디에도 포함되지 않는다 |

**선언 파일이 있을 때 추가되는 필드** (없으면 아래 필드 자체가 나타나지 않는다):

| 필드 | 설명 |
|------|------|
| `workspace_config` (최상위) | 대조에 사용한 선언 파일 절대경로 |
| `repo` | 실제 origin에서 환원한 `org/repo` 좌표. 환원 불가면 `null`. **원격 URL 원문은 응답에 없다** |
| `declaration` | enum: `match` \| `mismatch` \| `unknown` \| `not-cloned` \| `undeclared` \| `undeclared-active`. `--root`로 추가된 저장소는 멤버십 선언 대상이 아니므로 `null` |

| 선언 | 디스크 | `declaration` | `reason` | 동작 |
|------|--------|---------------|----------|------|
| `active` | 있음·좌표 일치 | `match` | 순회 판정 그대로 | 정상 sync |
| `active` | 있음·좌표 불일치 | `mismatch` | `mismatch` | **pull 보류** — 엉뚱한 저장소 방지 |
| `active`/`deferred` | 있음·환원 불가 | `unknown` | `unknown` | **pull 보류** — 확정 못 하면 일치로 간주하지 않는다 |
| `active` | 없음 | `not-cloned` | `not-cloned` | 보고 + clone 제안 (승인 필요) |
| `deferred` | 없음 | — | — | 의도된 상태. 보고하지 않는다 |
| `deferred` | 있음 | `undeclared-active` | 순회 판정 그대로 | sync + 선언 어긋남 보고 |
| 미선언 | 있음 | `undeclared` | `undeclared` | 선언 드리프트 보고, pull 보류 |

`mismatch`·`unknown`·`undeclared`는 fetch 이전에 확정되므로 `branch`·`upstream`·`ahead`·`behind`가 `null`이다.

`ok: false`이면 (예: 경로 부재 `PATH_NOT_FOUND`, 경로가 디렉토리가 아님 `NOT_A_DIRECTORY`, 선언 파일 스키마 위반 `WORKSPACE_CONFIG_INVALID`, 선언 파일 JSON 파싱 실패 `WORKSPACE_CONFIG_MALFORMED`) `error` 필드를 사용자에게 그대로 에스컬레이션하고 STEP 3~4를 진행하지 않는다. 선언 파일 오류는 한 저장소도 건드리지 않은 상태에서 반환된다.

---

## STEP 3 — 5섹션 보고서 렌더 [스킬 책임]

STEP 2의 JSON을 아래 5섹션 형식으로 렌더한다.

### ① 요약 헤더
워크스페이스 경로 + `summary` 집계를 한 줄로 표시한다. `already-current`는 별도로 "이미 최신 N개"로 표기한다 (updated/skipped/failed 카운트에는 포함되지 않으므로 `repositories[]`에서 `status == "already-current"` 개수를 직접 센다).

`root`가 `null`이 아니면 그 저장소가 root repo임을 헤더 다음 줄에 명시한다 — 사용자가 root 포함 여부를 헤더에서 바로 읽을 수 있어야 한다.

```
[opal-workspace-sync] <workspace 경로>
총 <total>개 저장소 — ✅ 최신화 <updated> · ⏭️ skip <skipped> · ❌ 실패 <failed> · 이미 최신 <already-current 수>
root 저장소: <root 경로> 포함              ← root != null일 때만
```

### ② ✅ 최신화 (status=updated)
각 저장소: `name`, `branch`, `prev_head → new_head`, `+N commits` (`pulled_commits`).

### ③ ⏭️ Skip (status=skipped)
`reason`(dirty/diverged/detached/no-upstream)별로 그룹핑하여 저장소명 나열 + 그룹별 제안조치 1줄 요약(§사유별 제안조치 카탈로그 참조).

### ④ ❌ 실패 (status=failed)
각 저장소: `name`, `reason`(fetch-failed) + 가능한 원인 설명(네트워크/인증/원격/non-ff 충돌 등).

### ④-2 📑 선언 대조 (선언 파일이 있을 때만)

응답에 `declaration` 필드가 있을 때만 렌더한다. `match`는 정상이므로 나열하지 않는다.

| `declaration` | 표시 | 함께 보여줄 것 |
|---------------|------|----------------|
| `not-cloned` | 선언됐지만 클론되지 않음 | 선언 좌표(`repo`) — 조치는 ⑤의 clone |
| `undeclared` | 디스크에 있지만 선언에 없음 | 실제 좌표(`repo`) — 선언 드리프트다. 선언 추가 또는 디렉토리 정리는 사람 결정 |
| `mismatch` | 디렉토리는 맞는데 다른 레포 | 선언 좌표와 실제 좌표, **그리고 원격 URL 원문** |
| `unknown` | 원격 좌표를 확정할 수 없음 | **원격 URL 원문** (없으면 "origin 없음") |
| `undeclared-active` | `deferred` 선언인데 디스크에 존재 | 선언을 `active`로 고칠지 묻는다 — **도구는 선언을 자동 변경하지 않는다** |

**[MUST] 원격 URL 원문은 `mismatch`·`unknown`에서만, 화면에만 노출한다.** 도구 응답에는 URL이 없으므로 스킬이 렌더 시점에 `git -C <경로> config --get remote.origin.url`로 직접 읽는다. 이 값을 DONE.md·보고 파일 등 영속 산출물에 기록하지 않는다 — 사용자마다 다른 접속 방식이 기록에 굳는다.

### ⑤ 📋 조치 제안 (승인 대기)
③·④·④-2에서 등장한 문제 저장소마다 `사유 → 제안조치` 매핑을 나열한다. 이 섹션은 **제안일 뿐 실행이 아니다** — STEP 4 승인 전에는 어떤 명령도 실행하지 않는다.

문제 저장소가 하나도 없으면(③·④·④-2가 모두 빈 경우) ⑤ 섹션은 생략하고 STEP 4도 건너뛴다.

---

## STEP 4 — 승인 게이트 [MUST, 헌법 user sovereignty]

⑤ 섹션에 제안이 있으면 AskUserQuestion으로 저장소별 후속조치를 제시한다.

**[MUST] 승인 전 자동 실행 절대 금지.** 승인된 조치만 Bash로 실행한다. 사용자가 특정 저장소를 승인하지 않으면 해당 저장소는 그대로 skip 상태로 남긴다.

### 사유별 제안조치 카탈로그 (제안만 — 자동 실행 금지)

| reason | 제안조치 (승인 후에만 실행) |
|--------|----------------------|
| `dirty` | `git stash` 후 pull / 변경 커밋 후 pull / 수동 검토 (기본 권장: 수동 검토) |
| `diverged` | `git rebase` / `git merge` / 수동 검토 (기본 권장: 수동 검토) |
| `detached` | 브랜치 체크아웃 후 재시도 (수동) |
| `no-upstream` | `git branch --set-upstream-to` 후 재시도 (수동) |
| `fetch-failed` | 네트워크/인증/원격 URL 점검 (수동) |
| `not-cloned` | `clone` 서브명령으로 클론 (승인 후에만) |
| `undeclared` | 선언에 추가 / 디렉토리 정리 / 그대로 두기 (사람 결정 — 도구는 선언을 고치지 않는다) |
| `mismatch` | 디렉토리명 또는 선언 수정 (수동). **자동 조치 없음** — 엉뚱한 저장소를 건드릴 위험이 가장 큰 상태다 |
| `unknown` | origin 설정 점검 (수동) |
| `undeclared-active` | 선언을 `active`로 수정 (사람 결정) |

**clone 실행 규칙:**

```bash
~/.opal/tools/git-sync-tool/run.sh clone <순회 대상 경로> --dir <디렉토리명> --url <clone URL>
```

- **접속 방식(SSH 별칭·HTTPS)은 레포마다 묻지 않고 세션에서 1회만 질의한다.** 첫 clone 승인 시 방식을 확정하고 같은 세션의 나머지 clone에 그대로 적용한다.
- clone URL은 선언의 `host`·`org`·`repo`로 조립하되, 사용자가 지정한 접속 방식을 우선한다.
- 대상 디렉토리가 이미 존재하면 도구가 `DIR_EXISTS`로 거부한다 — 덮어쓰지 않는다.
- clone 후 sync를 다시 돌려 `match` 판정을 확인한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-02 | 초기 작성 — 대상결정 3분기, git-sync-tool 호출, 5섹션 보고서, 승인 게이트, 사유별 제안조치 카탈로그 (052) |
| v1.1 | 2026-09-02 14:04 | root 저장소 포함 — STEP 1에 root 확정 분기 + [MUST] 누락 금지, STEP 2 `--root` 규칙, JSON `root` 필드, ① 요약 헤더 root 표기. `<경로>/workspace` 순회 시 프로젝트 root repo가 대상에서 빠지던 누락 교정 (L2 직접 수정) |
| v1.2 | 2026-09-02 17:22 | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |

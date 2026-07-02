---
name: opal-workspace-sync
description: |
  **워크스페이스 Git 일괄 동기화** — 워크스페이스 직속 자식 git 저장소를 순회하여 안전 최신화(clean+ff-only pull)하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 skip+보고+승인 후 조치.
  반드시 이 스킬을 사용해야 하는 상황: "워크스페이스 동기화", "저장소 일괄 pull", "opal-workspace-sync".
alias: opws
triggers:
  - "^opal-workspace-sync$"
  - "^opws$"
  - "(?i)(워크스페이스\\s*동기화|저장소\\s*일괄|일괄\\s*pull)"
version: "1.0"
domain: workspace
---

# opal-workspace-sync (워크스페이스 Git 일괄 동기화)

단일 pilot 구조의 operator 타입 스킬이다. 여러 독립 git 저장소가 모여 있는 워크스페이스를 순회하여, 안전하게 pull 가능한 저장소만 자동 최신화하고 문제 저장소는 건드리지 않는다.

**핵심 원칙 — 문제 저장소는 알투가 자율 조치하지 않는다.** dirty/diverged/detached/no-upstream/fetch-failed 저장소는 항상 **skip → 보고 → 제안 → 승인 후에만 조치**한다. 승인 없이 stash/rebase/merge/force/commit/push 등을 자동 실행하는 것은 절대 금지다 (헌법 user sovereignty 원칙).

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
  ├─ 예 → 그 workspace 경로를 대상으로 확정
  └─ 아니오 → 받은 경로 자체가 단일 git 루트(<경로>/.git 존재)?
               ├─ 예 → 그 경로를 대상으로 확정 (git-sync-tool이 1개 저장소로 처리)
               └─ 아니오 → AskUserQuestion으로 워크스페이스 경로를 질의하여 확정
```

- 판단에 필요한 경로 존재 확인은 Bash(`ls`/`test -d`) 또는 Read 도구로 수행한다.
- 사용자가 이미 명시적으로 경로를 지정했다면 그 경로에 대해 위 분기를 그대로 적용한다(우선 `<경로>/workspace`, 다음 `<경로>` 자체가 단일 루트인지 확인).

---

## STEP 2 — git-sync-tool 호출 [도구 위임]

STEP 1에서 확정된 경로로 도구를 호출한다:

```bash
~/.opal/tools/git-sync-tool/run.sh sync <확정 경로>
```

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
| `status` | enum: `updated` \| `skipped` \| `failed` \| `already-current` |
| `reason` | enum: `dirty` \| `diverged` \| `detached` \| `no-upstream` \| `fetch-failed` (정상 상태면 `null`) |
| `upstream` | `no-upstream`이면 `null` |
| `ahead` / `behind` | 계산 불가 시 `null` |
| `prev_head` / `new_head` | `updated`에서만 유효, 그 외 `null` |
| `summary` | `total`/`updated`/`skipped`/`failed` 집계. `already-current`는 `total`에는 포함되지만 세 카운트 어디에도 포함되지 않는다 |

`ok: false`이면 (예: 경로 부재 `PATH_NOT_FOUND`, 경로가 디렉토리가 아님 `NOT_A_DIRECTORY`) `error` 필드를 사용자에게 그대로 에스컬레이션하고 STEP 3~4를 진행하지 않는다.

---

## STEP 3 — 5섹션 보고서 렌더 [스킬 책임]

STEP 2의 JSON을 아래 5섹션 형식으로 렌더한다.

### ① 요약 헤더
워크스페이스 경로 + `summary` 집계를 한 줄로 표시한다. `already-current`는 별도로 "이미 최신 N개"로 표기한다 (updated/skipped/failed 카운트에는 포함되지 않으므로 `repositories[]`에서 `status == "already-current"` 개수를 직접 센다).

```
[opal-workspace-sync] <workspace 경로>
총 <total>개 저장소 — ✅ 최신화 <updated> · ⏭️ skip <skipped> · ❌ 실패 <failed> · 이미 최신 <already-current 수>
```

### ② ✅ 최신화 (status=updated)
각 저장소: `name`, `branch`, `prev_head → new_head`, `+N commits` (`pulled_commits`).

### ③ ⏭️ Skip (status=skipped)
`reason`(dirty/diverged/detached/no-upstream)별로 그룹핑하여 저장소명 나열 + 그룹별 제안조치 1줄 요약(§사유별 제안조치 카탈로그 참조).

### ④ ❌ 실패 (status=failed)
각 저장소: `name`, `reason`(fetch-failed) + 가능한 원인 설명(네트워크/인증/원격/non-ff 충돌 등).

### ⑤ 📋 조치 제안 (승인 대기)
③·④에서 등장한 문제 저장소마다 `사유 → 제안조치` 매핑을 나열한다. 이 섹션은 **제안일 뿐 실행이 아니다** — STEP 4 승인 전에는 어떤 명령도 실행하지 않는다.

문제 저장소가 하나도 없으면(③·④가 모두 빈 경우) ⑤ 섹션은 생략하고 STEP 4도 건너뛴다.

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

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-02 | 초기 작성 — 대상결정 3분기, git-sync-tool 호출, 5섹션 보고서, 승인 게이트, 사유별 제안조치 카탈로그 (052) |

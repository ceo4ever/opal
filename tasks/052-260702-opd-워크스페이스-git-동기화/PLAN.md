# PLAN: 워크스페이스 Git 일괄 동기화 — git-sync-tool + opal-workspace-sync 스킬 신설

> 작성일: 2026-07-02 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 4개)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약
하나의 워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전하게 일괄 최신화한다. 결정론적 git 작업(순회·fetch·ff-pull·5종 skip 판정)은 `git-sync-tool`(도구)이 집행하고, 순회 대상 결정·5섹션 보고서·문제 저장소 후속조치 승인 게이트는 `opal-workspace-sync`(스킬)가 오케스트레이션한다. OPAL "enforce, don't advise" 원칙에 정합한다 (→ TASK §확정 설계 방향).

### 1.2 기능 목록
| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | git-sync-tool 신설 (결정론 도구: 순회·fetch·ff-pull·5종 skip·JSON) | R1 (TASK §요구사항 #1), AC #1·#3 | P0 | 없음 |
| F-002 | opal-workspace-sync 스킬 신설 (대상결정 3분기·5섹션 보고서·승인 게이트) | R2 (TASK §요구사항 #2), AC #2 | P0 | F-001 |
| F-003 | install 등록 (git-sync-tool chmod +x 블록) | R3 (TASK §요구사항 #3), AC #4 | P0 | F-001 |
| F-004 | 안전성 검증 (dirty/diverged 무손실 원상보존 증명) | R4 (TASK §요구사항 #4), AC #3 | P0 | F-001, F-002, F-003 |

> **커버리지 확인**: TASK §요구사항 4건(git-sync-tool 신설 / opal-workspace-sync 스킬 신설 / install 등록 / 안전성 검증)이 F-001~F-004로 전량 매핑됨. AC 4건(TASK §AC)도 F-001(AC#1), F-002(AC#2), F-004(AC#3 무손실), F-003(AC#4 배포)로 전량 커버.

### 1.3 기능 의존 그래프
```
F-001 (git-sync-tool) ─┬─ F-002 (opal-workspace-sync 스킬)
                       ├─ F-003 (install 등록)
                       └───────────────────────────┬─ F-004 (안전성 검증)
F-002 ─────────────────────────────────────────────┤
F-003 ─────────────────────────────────────────────┘
```

### 1.4 설계 잠금 승계 ([MUST] 인용)

> TASK.md에서 확정·잠금된 설계로 PLAN이 변경 불가한 항목. (→ TASK §확정 설계 방향, §명확화 결과)

- **[MUST]** `docs/CONVENTIONS.md` §네이밍 규칙: 스킬 폴더 `{그룹}-{역할}` → 스킬명 `opal-workspace-sync`, 도구 폴더 `git-sync-tool` (kebab-case), Python 파일 `git_sync_tool.py` (snake_case) 확정 (→ D-2, ANALYSIS §5).
- **[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." → 모든 파일 경로는 프로젝트 소스 기준, install 재배포로 검증 (→ D-2).
- **[MUST]** `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다" → git-sync-tool은 로컬 git CLI 의존이나 셸 표준 준수로 이식성 확보, 하드코딩 분기 금지 (→ TASK §제약).
- **[MUST]** `docs/CONVENTIONS.md` §@header 규칙: 코드 파일 생성·수정 시 파일 상단에 @header 블록(해당 확장자에 한해). → `git_sync_tool.py`는 @header 블록 필수, `run.sh`는 `# @header: shell script — 적용 대상 아님` 주석 (→ D-2, ANALYSIS §5, `state_tool.py:1-14`, `state-tool/run.sh:3`).
- **[MUST]** `opal/core/references/opal-harness.md` §9: "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다. 출력은 JSON이며, `"ok": false`이면 `"error"` 필드를 확인한다." → git-sync-tool JSON 계약 준수 (→ D-4).
- **[MUST]** TASK §확정 설계 방향 핵심 원칙: "문제 저장소 = skip → 보고 → 제안 → 승인 후에만 조치. 알투 자율 실행 절대 금지 (헌법 user sovereignty)" → 도구·스킬 모두 dirty/diverged 저장소에 stash·rebase·force·commit·push 자동 수행 금지 (→ TASK §제약 #4).
- **[MUST]** TASK §확정 설계 방향: 순회 깊이 "직속 자식 1단계만 (재귀 안 함)", pull 정책 "`git pull --ff-only`", skip 사유 5종(dirty/diverged/detached/no-upstream/fetch-failed), 보고서 5섹션 — 변경 금지 (하네스 Guards).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 git_sync_tool.py — dirty 무손실 | dirty 저장소가 pull/조작되어 작업트리·HEAD가 변경됨 | P0 | L2 (실 git 저장소 통합) 의무 | S-무손실-dirty: 실행 전후 `git status --porcelain`·`git rev-parse HEAD` 불변 |
| H-2 | F-001 git_sync_tool.py — diverged 무손실 | ff-only가 diverged 저장소를 강제 병합/pull하여 HEAD 이동 또는 머지커밋 생성 | P0 | L2 (실 git, ahead+behind 인위 구성) 의무 | S-무손실-diverged: diverged 저장소 skip 확인 + HEAD 불변 |
| H-3 | F-001 판정 순서 (no-upstream→detached→dirty→diverged) | 판정 순서 오류 시 no-upstream 저장소에서 `@{u}` 참조가 diverged 판정으로 흘러 예외/오분류 | P1 | L1 (단위: 각 skip 조건 격리) + L2 | S-skip-5종: 5종 각각 정확한 reason 반환 |
| H-4 | F-001 diverged 컬럼 매핑 (rev-list --left-right --count) | 좌/우(behind/ahead) 컬럼을 반대로 매핑 → ff 가능(behind-only)을 diverged로 오판 또는 그 반대 | P1 | L1 (단위) + L2 (behind-only는 pull, diverged는 skip) | S-ff-behind-only: behind만 있는 저장소는 ff-pull 성공 |
| H-5 | F-001 ff-only pull 정책 | `pull --ff-only`가 실패(non-ff) 시 예외 미처리로 도구 크래시 또는 부분 조작 잔재 | P1 | L2 (non-ff 유발 후 실패 분류) | S-nonff-fail: non-ff 상황에서 failed/skipped 반환, 저장소 불변 |
| H-6 | F-001 JSON 계약 | `ok`/`repositories`/`summary`/`error` 필드 누락·타입 불일치 → 스킬 파싱 실패 | P1 | L1 (JSON 스키마 검증) | S-json-schema: 모든 실행 결과가 유효 JSON + 필수 필드 |
| H-7 | F-002 대상 결정 3분기 | `(프로젝트)/workspace` 유무·단일 루트 분기 오판 → 잘못된 대상 순회 또는 순회 누락 | P1 | L2 (3분기 각 시나리오) | S-target-3분기: workspace 존재/부재/단일루트 각각 올바른 대상 |
| H-8 | F-002 승인 게이트 | 문제 저장소에 승인 없이 자율 조치 실행 (헌법 위반) | P0 | L1 (스킬 프로세스 정적 검토) + 수동 | S-approval-gate: dirty/diverged 저장소에 조치 문구가 "제안"에만 존재, 자동 실행 코드 없음 |
| H-9 | F-001 git 버전 | git 2.22 미만서 `rev-list --left-right --count` 미지원 → 판정 실패 | P2 | 문서 명시 + fetch-failed류 방어 | S-git-version: 도구 문서에 git 2.22+ 명시 |
| H-10 | F-003 install 등록 | chmod +x 블록 누락·위치 오류 → run.sh 실행 권한 없음 → 배포 후 도구 미동작 | P1 | L2 (install 후 `-x` 확인) | S-install: install 후 `~/.opal/tools/git-sync-tool/run.sh` 존재 + 실행 가능 |

---

## 2. 기능별 분석

### F-001: git-sync-tool 신설

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/git-sync-tool/run.sh` | Bash 래퍼 (venv 검사 → Python 위임) | 신규 |
| 도구 | `opal/tools/git-sync-tool/git_sync_tool.py` | 순회·fetch·5종 skip 판정·ff-pull·JSON 조립 | 신규 |
| 도구 | `opal/tools/state-tool/run.sh` | 래퍼 패턴 참조 원본 | 참조 |
| 도구 | `opal/tools/state-tool/state_tool.py` | @header·ERROR_CODES·JSON 계약 참조 원본 | 참조 |

#### 2.1.2 현재 구현 (ANALYSIS 참조)
- **run.sh 패턴** (`state-tool/run.sh:1-12`): `#!/bin/bash` → `VENV_PYTHON="$HOME/.opal/.venv/bin/python"` → `SCRIPT_DIR=...` → venv 미존재 시 `{"ok":false,"error":...}` + exit 1 → `exec "$VENV_PYTHON" "$SCRIPT_DIR/{tool}.py" "$@"` (→ ANALYSIS §1(a)).
- **Python 구현** (표준 라이브러리만): json/argparse/pathlib/sys/subprocess. @header 블록 필수 (`state_tool.py:1-14`) (→ ANALYSIS §1(b), §5).
- **JSON 계약** (`state_tool.py:66-100`, `opal-harness.md §9`): `{"ok": bool, "command": str, ..., "error": str(ok=false 시)}`, ERROR_CODES 카탈로그 dict 참조, exit 0/1 (→ ANALYSIS §1(c)).
- **중복 없음**: `opal/tools/` 내 git 조작 도구 부재 확인 (grep 0건) → 완전 신규 (→ ANALYSIS §6).

#### 2.1.3 영향 범위
- **피호출자(도구가 호출)**: 로컬 git CLI (`git fetch/status/rev-parse/symbolic-ref/rev-list/pull`). git 2.22+ 필요 (→ ANALYSIS §4).
- **호출자(도구를 호출)**: F-002 opal-workspace-sync 스킬 (`~/.opal/tools/git-sync-tool/run.sh sync <경로>`).
- **공유 상태**: 없음 (순수 순회, 부작용은 clean+ff 저장소 pull에 한정).
- **관련 테스트**: 기존 도구는 단위테스트 미존재, TEST-SCENARIO.md 기반 검증 (→ ANALYSIS §1(d)).

---

### F-002: opal-workspace-sync 스킬 신설

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-workspace-sync/SKILL.md` | frontmatter + 대상결정 3분기 + git-sync-tool 호출 + 5섹션 보고서 + 승인 게이트 | 신규 |
| 스킬 | `opal/skills/opal-workspace-sync/references/report-format.md` | 5섹션 보고서 렌더 규격 + 사유별 제안조치 (선택) | 신규 |
| 스킬 | `opal/skills/opal-brain/SKILL.md` | operator 타입 템플릿 (파이프라인 없음, 도구 직접 호출) 참조 원본 | 참조 |
| 스킬 | `~/.opal/community-skills/skill-creator/SKILL.md` | 스킬 생성 프로세스 (메모리 피드백) | 참조 |

#### 2.2.2 현재 구현 (ANALYSIS 참조)
- **opal-brain 템플릿** (`opal-brain/SKILL.md:1-43`): frontmatter(name/description/alias/triggers/version/domain/pipeline) + Harness 섹션 + 모드 라우팅 테이블 + 도구를 `~/.opal/tools/{tool}/run.sh`로 직접 호출 + JSON `ok:false` 에스컬레이션. 단계 파이프라인 없는 **operator 타입** (→ ANALYSIS §2(b), D-6).
- **배치 경로 확정**: `opal/skills/opal-workspace-sync/` — opal 접두사=OPAL 전용(`CONVENTIONS.md:30-36`), install 자동 순회(`install-mac.sh:1057-1068`) (→ ANALYSIS §2(c)).
- **스킬 생성 방식**: skill-creator 사용 — "Capture Intent → Interview → Draft → Test → Evaluate → Iterate → Optimize Description → Package" (→ `feedback_skill_creation.md`).

#### 2.2.3 영향 범위
- **피호출자**: F-001 git-sync-tool, AskUserQuestion (승인 게이트).
- **호출자**: 사용자/PM (트리거 문구 또는 alias).
- **공유 상태**: 없음.
- **관련 테스트**: 대상결정 3분기 시나리오, 보고서 5섹션 렌더, 승인 게이트 무자율.

---

### F-003: install 등록

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배포 | `scripts/install-mac.sh` | git-sync-tool run.sh chmod +x 블록 추가 | 수정 |

#### 2.3.2 현재 구현 (ANALYSIS 참조)
- **도구 배포**: `install_dir "$opal_dir/tools" "$opal_home/tools"` 일괄 복사 → 자동 순회이므로 git-sync-tool 디렉토리는 나열 불필요 (`install-mac.sh:1108-1110`) (→ ANALYSIS §3(b)).
- **개별 chmod 패턴**: state-tool/brain-tool/tool-scan/memory-tool 각각 `local x_run="$opal_home/tools/{tool}/run.sh"; if [[ -f "$x_run" ]]; then chmod +x "$x_run"; success "..."; fi` (`install-mac.sh:1120-1163`) (→ ANALYSIS §3(c)).
- **스킬 배포**: `install-mac.sh:1057-1068` for 루프 자동 순회 → opal-workspace-sync 명시 나열 불필요 (→ ANALYSIS §3(a)).

#### 2.3.3 영향 범위
- **직접**: install-mac.sh chmod 블록 1개 추가.
- **간접**: install 실행 시 `~/.opal/tools/git-sync-tool/` 및 `~/.opal/skills/opal-workspace-sync/` 배포.
- **회귀 위험**: 기존 chmod 블록 미변경 — 신규 블록만 append.

---

### F-004: 안전성 검증

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 검증 | (테스트 저장소 — 임시 fixture) | dirty/diverged/detached/no-upstream/behind-only 상황 구성 | 검증 전용 |

#### 2.4.2 현재 구현
- 기존 도구는 명시적 단위테스트 없음 → TEST-SCENARIO.md 기반 동적 검증 (→ ANALYSIS §1(d)). opal-pilot-dev STEP 3.5에서 PM이 TEST-SCENARIO.md 별도 작성.

#### 2.4.3 영향 범위
- **검증 대상**: F-001 skip 판정 정확성, dirty/diverged 무손실 원상보존, ff-only가 diverged를 pull하지 않음.
- **fixture**: 임시 디렉토리에 로컬 bare remote + clone 여러 개 구성하여 5종 skip + behind-only(ff 가능) 상황 인위 생성.

---

## 3. 기능별 설계

### F-001: git-sync-tool 신설

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/git-sync-tool/run.sh` | 도구 | Bash 래퍼: venv 검사 → `exec python git_sync_tool.py "$@"` | `state-tool/run.sh:1-12` |
| 2 | `opal/tools/git-sync-tool/git_sync_tool.py` | 도구 | argparse `sync <경로>` → 순회 → 각 저장소 처리 → JSON 출력 | `state_tool.py:1-14,66-100` |

**수정**: 없음 (도구 신규 생성)

#### 3.1.2 API·데이터 모델·설계

##### (a) run.sh 래퍼 설계
`state-tool/run.sh` 패턴을 그대로 따른다 (`state-tool/run.sh:1-12`):
```bash
#!/bin/bash
# git-sync-tool 래퍼 — OPAL .venv python 호출
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi
exec "$VENV_PYTHON" "$SCRIPT_DIR/git_sync_tool.py" "$@"
```
[MUST] `run.sh`는 `.sh`이므로 @header 블록 미적용, 주석으로 대체 (→ D-2, ANALYSIS §5).

##### (b) 서브명령 설계
단일 서브명령 `sync <경로>` 채택 (Simplicity First — TASK §확정 순회 깊이 "직속 자식 1단계만"과 정합). 대상 결정 3분기 로직은 **스킬 책임**이며, 도구는 **이미 결정된 경로를 인자로 받아 순회**만 집행 (→ TASK §확정, "경로 인자 받아 순회"=도구 / "workspace 없으면 질의"=스킬).

```
git_sync_tool.py sync <workspace_path>
```
- argparse: subcommand `sync`, positional `path`.
- `git_sync_tool.py:1-14` @header 블록 (module=`git_sync_tool`, layer=`util`, domain=`opal-workspace`, description, exports, depends) 필수 (→ D-2).

##### (c) 대상 순회 로직 (도구 책임 경계)
- 입력 `path`가 **그 자체로 단일 git 루트**(`path/.git` 존재)이면 → 그 1개를 대상 리스트로 (유형 A 통합) (→ TASK §대상 결정).
- 아니면 → `path`의 **직속 자식 디렉토리 1단계**만 순회하여 각 자식 중 `child/.git` 존재하는 것을 대상 리스트로 (재귀 금지) (→ TASK §순회 깊이).
- pathlib `Path(path).iterdir()` 사용, 정렬(이름순) 후 처리.
- 대상 0개면 `summary.total=0`으로 정상 JSON 반환.

##### (d) 저장소별 처리 함수 — 판정 순서 [MUST] 확정
`process_repo(repo_path) -> dict` 함수. 판정 순서는 ANALYSIS §4 확정에 따라 **no-upstream 먼저 → detached → dirty → fetch → diverged/ff** (→ ANALYSIS §4 "no-upstream 먼저 검사 후 diverged 판정"):

```
1. branch 조회: git rev-parse --abbrev-ref HEAD
   → "HEAD"이면 detached 후보 (아래 3에서 확정)
2. no-upstream 판정: git rev-parse --abbrev-ref --symbolic-full-name @{u}
   → exit != 0 → status=skipped, reason=no-upstream, upstream=null  [종료]
3. detached 판정: git symbolic-ref -q HEAD
   → exit != 0 → status=skipped, reason=detached  [종료]
   (주의: detached는 @{u}가 없을 수도 있어 2에서 먼저 걸릴 수 있음. 2→3 순서로 no-upstream 우선)
4. dirty 판정: git status --porcelain
   → 출력 길이 > 0 → status=skipped, reason=dirty  [종료]
5. fetch: git fetch --all --prune
   → exit != 0 → status=failed, reason=fetch-failed  [종료]
6. ahead/behind 계산: git rev-list --left-right --count @{u}...HEAD
   → 출력 "L R" (L=@{u} 고유=behind, R=HEAD 고유=ahead)  [MUST 컬럼 매핑 확정]
   → behind = L, ahead = R
   → ahead>0 AND behind>0 → status=skipped, reason=diverged  [종료]
   → behind==0 (ahead>=0) → status=already-current (pull 불요)  [종료]
   → behind>0 AND ahead==0 → ff 가능:
7. ff-pull: git pull --ff-only
   → exit 0 → status=updated, pulled_commits 기록
   → exit != 0 → status=failed, reason=fetch-failed (non-ff/충돌)
```

> **[MUST] diverged 컬럼 매핑**: `git rev-list --left-right --count @{u}...HEAD` 출력은 `<left> <right>`이며 left=`@{u}`에만 있는 커밋 수(=behind), right=`HEAD`에만 있는 커밋 수(=ahead) (→ ANALYSIS §4 "좌=behind, 우=ahead"). H-4 리스크 — L2로 검증.

> **[MUST]** git 2.22+ 필요 (`rev-list --left-right --count`). 도구 @header description 및 SKILL.md에 명시 (→ ANALYSIS §4, §설계피드백/리스크 H-9).

> **[MUST]** 자율 조치 금지: 6·7단계 어디에서도 dirty/diverged 저장소에 stash/rebase/force/commit/push 실행 금지. skipped/failed 반환만 (→ TASK §제약 #4, H-1·H-2·H-8).

##### (e) JSON 출력 스키마 [MUST] 최종 확정
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
필드 계약:
- `ok`: bool — 도구 실행 자체 성공 여부(개별 저장소 실패와 무관, 순회 완료 시 true). 치명적 오류(경로 부재 등)만 false.
- `command`: `"sync"` 고정.
- `workspace`: 순회 대상 절대 경로.
- `repositories[]`: 각 저장소 결과 객체.
  - `name`: 저장소 디렉토리명.
  - `branch`: 현재 브랜치 (detached면 `"HEAD"` 또는 short sha).
  - `upstream`: `origin/main` 등, no-upstream이면 `null`.
  - `status`: enum `updated | skipped | failed | already-current`.
  - `reason`: enum `dirty | diverged | detached | no-upstream | fetch-failed`, 정상(updated/already-current)이면 `null`.
  - `ahead`, `behind`: int (계산 못 하면 `null`).
  - `prev_head`, `new_head`: short sha (updated에서 유효, 그 외 동일 또는 `null`).
  - `pulled_commits`: int (updated에서 behind 수, 그 외 0).
- `summary`: `{total, updated, skipped, failed}` int 집계. (`already-current`는 total에 포함하되 updated/skipped/failed 어디에도 미포함 — 스킬 보고서 ✅섹션에서 "이미 최신"으로 별도 렌더).
- `error`: 치명적 오류 ERROR_CODE 문자열(ok=false 시), 정상이면 `null`.

> ERROR_CODES 카탈로그: `PATH_NOT_FOUND`, `NOT_A_DIRECTORY`, `GIT_NOT_FOUND` 등을 dict로 정의 (`state_tool.py:66-100` 패턴). exit 0(ok=true) / 1(ok=false) (→ ANALYSIS §1(c)).

##### (f) git 명령 정확 목록 (subprocess.run, `cwd=repo_path`)
| 목적 | 명령 |
|------|------|
| 현재 브랜치 | `git rev-parse --abbrev-ref HEAD` |
| no-upstream | `git rev-parse --abbrev-ref --symbolic-full-name @{u}` |
| detached | `git symbolic-ref -q HEAD` |
| dirty | `git status --porcelain` |
| fetch | `git fetch --all --prune` |
| ahead/behind | `git rev-list --left-right --count @{u}...HEAD` |
| HEAD sha | `git rev-parse --short HEAD` |
| ff-pull | `git pull --ff-only` |

#### 3.1.3 환경 변경
해당 없음 (표준 라이브러리 + 로컬 git CLI만).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | AC#1 clean+ff pull | 기능 테스트 | behind-only 저장소 → status=updated, pulled_commits>0, HEAD 전진 |
| TS-002 | AC#1 dirty skip | 기능 테스트 | dirty 저장소 → status=skipped, reason=dirty |
| TS-003 | AC#1 diverged skip | 기능 테스트 | ahead>0+behind>0 → status=skipped, reason=diverged |
| TS-004 | AC#1 detached skip | 기능 테스트 | detached HEAD → status=skipped, reason=detached |
| TS-005 | AC#1 no-upstream skip | 기능 테스트 | upstream 없음 → status=skipped, reason=no-upstream, upstream=null |
| TS-006 | AC#1 fetch-failed | 기능 테스트 | fetch 실패(원격 접근 불가) → status=failed, reason=fetch-failed |
| TS-007 | AC#1 JSON 계약 | 산출물 검사 | 모든 실행 결과가 유효 JSON + 필수 필드 존재 |
| TS-008 | AC#1 already-current | 기능 테스트 | behind==0 저장소 → status=already-current, pull 미실행 |

---

### F-002: opal-workspace-sync 스킬 신설

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-workspace-sync/SKILL.md` | 스킬 | frontmatter + 대상결정 3분기 + git-sync-tool 호출 + 5섹션 보고서 + 승인 게이트 | `opal-brain/SKILL.md:1-43` |
| 2 | `opal/skills/opal-workspace-sync/references/report-format.md` | 스킬 | 5섹션 보고서 렌더 규격 + 사유별 제안조치 카탈로그 | TASK §보고서 |

> `references/`는 5섹션 보고서 규격이 SKILL.md 본문에서 분리할 만큼 길 때만 생성. skill-creator의 Package 단계 판단에 위임 (설계 여지 — 최소 SKILL.md 단일 파일도 허용).

#### 3.2.2 API·설계

##### (a) SKILL.md frontmatter (opal-brain 템플릿)
```yaml
---
name: opal-workspace-sync
description: |
  **워크스페이스 Git 일괄 동기화** — 워크스페이스 직속 자식 git 저장소를 순회하여 안전 최신화(clean+ff-only pull)하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 skip+보고+승인 후 조치.
  반드시 이 스킬을 사용해야 하는 상황: "워크스페이스 동기화", "저장소 일괄 pull", "opal-workspace-sync", alias.
alias: (skill-creator Optimize 단계에서 확정 — 예: opws)
triggers:
  - "^opal-workspace-sync$"
  - "(?i)(워크스페이스\\s*동기화|저장소\\s*일괄|일괄\\s*pull)"
version: "1.0"
domain: workspace
---
```
> operator 타입 — pipeline 필드는 단일 동작이므로 생략 (opal-brain은 다중 모드라 pipeline 명시, 본 스킬은 단일 동작이므로 파이프라인 없음) (→ ANALYSIS §2(b), D-6).

##### (b) 프로세스 설계
```
STEP 0. Harness: ~/.opal/references/opal-harness.md 미로드 시 Read.

STEP 1. 대상 결정 (3분기) — [스킬 책임]
  (프로젝트)/workspace 존재?
    ├─ 예 → workspace 경로를 대상으로
    └─ 아니오 → 받은 경로가 단일 git 루트(path/.git)?
                 ├─ 예 → 그 경로 (도구가 1개로 처리)
                 └─ 아니오 → AskUserQuestion으로 워크스페이스 경로 질의 → 확정

STEP 2. git-sync-tool 호출 — [도구 위임]
  ~/.opal/tools/git-sync-tool/run.sh sync <확정 경로>
  → JSON 수신. ok:false 이면 error 필드 에스컬레이션 (→ D-4, opal-harness §9).

STEP 3. 5섹션 보고서 렌더 — [스킬 책임]
  ① 요약 헤더: workspace 경로 + summary 집계 (✅updated / ⏭️skipped / ❌failed / (이미 최신))
  ② ✅ 최신화: status=updated 목록 (name, branch, prev→new head, +N commits)
  ③ ⏭️ Skip: status=skipped 목록 (name, reason별 그룹 + 제안조치)
  ④ ❌ 실패: status=failed 목록 (name, reason=fetch-failed 등 + 원인)
  ⑤ 📋 조치 제안 (승인 대기): 문제 저장소별 사유→제안조치 매핑

STEP 4. 승인 게이트 — [스킬 책임, 헌법 user sovereignty]
  ⑤에 제안이 있으면 AskUserQuestion으로 저장소별 후속조치 제시.
  [MUST] 승인 전 자동 실행 절대 금지. 승인된 조치만 실행.
```

##### (c) 사유별 제안조치 카탈로그 (⑤섹션, 제안만 — 자동 실행 금지)
| reason | 제안조치 (승인 후에만) |
|--------|----------------------|
| dirty | `git stash` 후 pull / 변경 커밋 후 pull / 수동 검토 (기본: 수동 검토 권장) |
| diverged | `git rebase` / `git merge` / 수동 검토 (기본: 수동 검토 권장) |
| detached | 브랜치 체크아웃 후 재시도 (수동) |
| no-upstream | upstream 설정(`git branch --set-upstream-to`) 후 재시도 (수동) |
| fetch-failed | 네트워크/인증/원격 URL 점검 (수동) |

> [MUST] 위 제안은 AskUserQuestion 선택지로만 제시. 스킬이 자율 실행하지 않는다 (→ TASK §제약 #4, H-8). 승인 시 실행 명령은 사용자 확정 후 Bash로 실행.

##### (d) FE 화면
해당 없음 (CLI/보고서 스킬).

#### 3.2.3 환경 변경 / 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | AC#2 대상결정 (프로젝트)/workspace 존재 | 통합 테스트 | workspace 경로가 도구에 전달됨 |
| TS-010 | AC#2 대상결정 단일 루트 | 통합 테스트 | path/.git 존재 시 그 1개를 대상 |
| TS-011 | AC#2 대상결정 질의 | 통합 테스트 | workspace 없고 단일 루트 아님 → AskUserQuestion 질의 |
| TS-012 | AC#2 5섹션 보고서 | 산출물 검사 | 요약/✅/⏭️/❌/📋 5섹션 + 집계 + 사유별 제안 포함 |
| TS-013 | AC#2 승인 게이트 무자율 | 산출물 검사 | 문제 저장소 조치가 "제안"에만 존재, 자동 실행 로직 부재 |

---

### F-003: install 등록

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배포 | memory-tool chmod 블록(~line 1163) 직후 git-sync-tool chmod +x 블록 추가 | `install-mac.sh:1157-1163` |

#### 3.3.2 설계
memory-tool 블록 직후, 동일 패턴으로 추가 (`install-mac.sh:1157-1163` 패턴):
```bash
        # ── git-sync-tool 실행 권한 (052) ──
        local git_sync_run="$opal_home/tools/git-sync-tool/run.sh"
        if [[ -f "$git_sync_run" ]]; then
            chmod +x "$git_sync_run"
            success "git-sync-tool run.sh 실행 권한 설정"
        fi
```
- 도구 디렉토리 복사·스킬 배포는 자동 순회로 처리되므로 별도 나열 불필요 (→ ANALYSIS §3(a),(b),(c)).
- [MUST] 삽입 위치는 `if [[ -d "$opal_dir/tools" ]]` 블록 **내부**, memory-tool 블록 뒤·cmux 의존성 안내(`install-mac.sh:1165`) 앞 (→ ANALYSIS §3, `install-mac.sh:1108-1163`).

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | AC#4 도구 배포 | 통합 테스트 | install 후 `~/.opal/tools/git-sync-tool/run.sh` 존재 + `-x` 실행 가능 |
| TS-015 | AC#4 스킬 배포 | 통합 테스트 | install 후 `~/.opal/skills/opal-workspace-sync/SKILL.md` 존재 (변경이력 strip 확인) |

---

### F-004: 안전성 검증

#### 3.4.1 파일 변경 계획
신규/수정 소스 없음 — TEST-SCENARIO.md(PM 작성) 기반 동적 검증. fixture는 임시 디렉토리에 로컬 bare remote + clone으로 구성.

#### 3.4.2 설계 — 무손실 검증 프로토콜
각 무손실 대상 저장소에 대해:
1. 실행 전 스냅샷: `git rev-parse HEAD`, `git status --porcelain` 저장.
2. git-sync-tool `sync` 실행.
3. 실행 후 재측정: HEAD·porcelain 동일 여부 assert.
4. dirty/diverged/detached는 실행 전후 **완전 불변**이어야 통과 (H-1, H-2).

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | AC#3 dirty 무손실 | 보안/회귀 테스트 | dirty 저장소 HEAD·작업트리 실행 전후 불변 (H-1) |
| TS-017 | AC#3 diverged 무손실 | 보안/회귀 테스트 | diverged 저장소 HEAD 불변, 머지커밋 미생성 (H-2) |
| TS-018 | AC#3 ff-only non-diverged | 보안 테스트 | diverged 저장소에 pull 미실행 (ff-only가 diverged를 병합하지 않음) (H-2, H-5) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2 | opal-be-agent | 순차 | run.sh → git_sync_tool.py (동일 도구 디렉토리) |
| 2 | F-002 | 3 | opal-task-agent | F-001 후 | skill-creator 활용, 도구 호출 계약 의존 |
| 2 | F-003 | 4 | opal-be-agent | F-001 후 | F-002와 병렬 가능 (독립 파일) |
| 3 | F-004 | 5 | opal-test-agent | Phase 1·2 후 | 도구+스킬+install 완료 후 검증 |
| 3 | 문서 | 6 | PM 직접 | Phase 1·2 후 | harness §9 도구 카탈로그 갱신 |

### 4.2 실행 체크리스트
> 총 6개 Step | Phase 3개 | 실행 모드: 복잡

#### Step 1: git-sync-tool run.sh 래퍼 작성
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/git-sync-tool/run.sh`
- **작업 내용**: state-tool 패턴 복제 — venv 검사 → `exec python git_sync_tool.py "$@"`. `# @header: shell script — 적용 대상 아님` 주석 (§3.1.2(a)).
- **완료 기준**: run.sh가 venv 미존재 시 `{"ok":false,"error":...}` + exit 1, 존재 시 python 위임. `chmod +x` 로컬 확인.
- **테스트**: TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: git_sync_tool.py 본체 구현
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/git-sync-tool/git_sync_tool.py`
- **작업 내용**: @header 블록 → argparse `sync <path>` → 대상 순회(단일루트 vs 직속자식 1단계, §3.1.2(c)) → `process_repo()` 판정 순서 no-upstream→detached→dirty→fetch→diverged/ff (§3.1.2(d)) → JSON 스키마 조립(§3.1.2(e)) → ERROR_CODES. git 2.22+ 명시. [MUST] 자율 조치 코드 부재.
- **완료 기준**: TS-001~008 로컬 fixture로 PASS. 유효 JSON 출력. dirty/diverged skip + 무손실.
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005, TS-006, TS-007, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: opal-workspace-sync 스킬 작성 (skill-creator 활용)
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-workspace-sync/SKILL.md` (+ 필요 시 `references/report-format.md`)
- **작업 내용**: [MUST] `~/.opal/community-skills/skill-creator/SKILL.md`를 Read하여 그 프로세스(Capture Intent→Interview→Draft→Test→Evaluate→Iterate→Optimize Description→Package)를 따른다 (→ `feedback_skill_creation.md`). opal-brain frontmatter 템플릿(§3.2.2(a)) + 대상결정 3분기(STEP 1) + git-sync-tool 호출(STEP 2) + 5섹션 보고서(STEP 3) + AskUserQuestion 승인 게이트(STEP 4) + 사유별 제안 카탈로그(§3.2.2(c)). [MUST] 자율 조치 금지 문구 포함.
- **완료 기준**: SKILL.md frontmatter 유효, 3분기 로직·5섹션·승인게이트 명시, 조치는 "제안"에만 존재. TS-012·TS-013 검토 PASS.
- **테스트**: TS-009, TS-010, TS-011, TS-012, TS-013
- **실행 방법**: sub-agent
- **의존**: Step 2 (도구 호출 계약 의존)

#### Step 4: install-mac.sh git-sync-tool chmod 블록 추가
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 배포
- **agent**: opal-be-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: memory-tool chmod 블록(`install-mac.sh:1157-1163`) 직후에 git-sync-tool chmod +x 블록 추가 (§3.3.2). `if [[ -d "$opal_dir/tools" ]]` 블록 내부, cmux 안내 앞.
- **완료 기준**: install 실행 후 `~/.opal/tools/git-sync-tool/run.sh`가 `-x`. 스킬은 자동 순회 배포 확인. 기존 chmod 블록 미변경.
- **테스트**: TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 2 (도구 존재 필요)

#### Step 5: 안전성 검증 (무손실 + 5종 skip)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치 (검증)
- **agent**: opal-test-agent
- **파일**: (임시 fixture — 로컬 bare remote + clone)
- **작업 내용**: TEST-SCENARIO.md(PM 작성) 기반. 5종 skip + behind-only(ff) + already-current fixture 구성 → sync 실행 → 무손실 프로토콜(§3.4.2)로 dirty/diverged HEAD·작업트리 전후 불변 assert. ff-only가 diverged를 병합하지 않음 증명.
- **완료 기준**: TS-001~008, TS-016~018 전량 PASS. dirty/diverged 무손실 증명.
- **테스트**: TS-016, TS-017, TS-018 (+ F-001 재검증 TS-001~008)
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 3, Step 4

#### Step 6: docs/ 갱신 (도구/스킬 카탈로그)
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/core/references/opal-harness.md §9 "현재 등록된 도구"` 테이블, 필요 시 `docs/ARCHITECTURE.md`
- **작업 내용**: 신규 도구 git-sync-tool을 harness §9 도구 카탈로그에 1행 추가(용도·트리거). ARCHITECTURE.md에 컴포넌트 추가 필요 여부 PM 판단.
- **완료 기준**: 도구 카탈로그에 git-sync-tool 반영. 문서-코드 정합.
- **테스트**: 문서 리뷰
- **실행 방법**: direct (PM)
- **의존**: Step 2, Step 3

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 동일 도구 디렉토리, run.sh가 git_sync_tool.py를 exec (계약 선행) |
| Step 2 → Step 3 | 스킬이 도구 JSON 계약(§3.1.2(e))에 의존 |
| Step 2 → Step 4 | install chmod는 도구 존재 필요 |
| Step 3 ∥ Step 4 | 독립 파일(SKILL.md vs install-mac.sh), 상호 무의존 → 병렬 가능 |
| Step 2·3·4 → Step 5 | 검증은 도구+스킬+배포 완료 후 |
| Step 2·3 → Step 6 | 문서는 구현 확정 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | clean+ff pull 동작 | TS-001 | behind-only 저장소 updated + HEAD 전진 |
| F-001 | 5종 skip 판정 정확성 | TS-002~006 | 각 사유별 정확한 status/reason 반환 |
| F-001 | JSON 계약 준수 | TS-007 | ok/command/workspace/repositories/summary/error 필드 유효 |
| F-001 | already-current 미pull | TS-008 | behind==0 → already-current |
| F-002 | 대상결정 3분기 | TS-009~011 | workspace/단일루트/질의 각 분기 정확 |
| F-002 | 5섹션 보고서 | TS-012 | 요약/✅/⏭️/❌/📋 + 집계 + 사유별 제안 |
| F-002 | 승인 게이트 무자율 | TS-013 | 조치 "제안"에만 존재, 자동 실행 부재 |
| F-003 | 도구/스킬 배포 | TS-014, TS-015 | install 후 run.sh `-x` + SKILL.md 존재 |
| F-004 | dirty 무손실 | TS-016 | dirty HEAD·작업트리 전후 불변 |
| F-004 | diverged 무손실 + ff-only | TS-017, TS-018 | diverged HEAD 불변, 머지커밋 미생성, pull 미실행 |

### 5.2 회귀 테스트
- [ ] 기존 도구(state-tool/brain-tool/tool-scan/memory-tool) chmod 블록 미변경 확인
- [ ] install-mac.sh 스킬/도구 자동 순회 로직 미파손 확인
- [ ] 기존 스킬/도구 배포 정상 (install 재실행)

### 5.3 코드/문서 품질
- [ ] `git_sync_tool.py` @header 블록 (module/layer/domain/description/exports/depends) 작성 (→ D-2, ANALYSIS §5)
- [ ] `run.sh` `# @header: shell script — 적용 대상 아님` 주석
- [ ] 폴더 kebab-case(`git-sync-tool`), Python snake_case(`git_sync_tool.py`), 스킬 `opal-workspace-sync`
- [ ] 변경이력 기록 (semver, KST 일시) — install이 배포본에서 자동 strip
- [ ] git 2.22+ 요구사항 도구 문서·@header 명시
- [ ] 플랫폼 조건문 미포함 (셸 표준 준수)

### 5.4 보안
- [ ] [MUST] dirty/diverged 저장소 자율 조치(stash/rebase/force/commit/push) 코드 부재 (→ TASK §제약 #4)
- [ ] `~/.opal/` 직접 편집 없음 — 프로젝트 소스만 수정 후 install (→ D-2)
- [ ] 하드코딩된 토큰/시크릿/경로 없음 (`$HOME` 기반)
- [ ] subprocess 호출에 shell injection 여지 없음 (인자 리스트 방식, `cwd` 격리)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 |
| 변경 파일 수 | 4개 (run.sh, git_sync_tool.py, SKILL.md, install-mac.sh) | 복잡 |
| 모듈 범위 | 다중 (도구 + 스킬 + 배포) | 복잡 |
| 작업 유형 | 신규 개발 (도구+스킬 신설) | 복잡 |
| 외부 의존성 | 새 도구·새 스킬·git CLI 2.22+ | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1: [opal-be-agent] Step 1 → Step 2  (git-sync-tool: run.sh + py, 동일 디렉토리 순차)
Batch 2: [opal-task-agent] Step 3 (스킬)  ∥  [opal-be-agent] Step 4 (install)
Batch 3: [opal-test-agent] Step 5 (검증)  +  [PM] Step 6 (문서)
```
- **파일 충돌 방지**: Step 1·2는 동일 도구 디렉토리 → opal-be-agent 단일 배치.
- **모듈 응집도**: 도구(BE)·install(BE)는 opal-be-agent, 스킬(MD)은 opal-task-agent.
- **병렬 극대화**: Step 3(스킬) ∥ Step 4(install) 독립.

### C-2. 스킬 요구사항
- **기존 스킬 매칭**: opal-brain(operator 템플릿, `opal-brain/SKILL.md:1-43`), skill-creator(생성 프로세스).
- **갭 판별**: opal-workspace-sync 자체가 신규 스킬 산출물 — skill-creator로 생성. 인라인 지침 불충분(신규 트리거·프로세스 필요) → 정식 스킬.

### C-3. 도구 요구사항
- **신규 도구**: git-sync-tool (run.sh + git_sync_tool.py).
- **CLI**: git 2.22+ (로컬).
- **패키지**: 없음 (Python 표준 라이브러리만).

### C-4. 테스트 전략
- **기능 테스트** (opal-test-agent, mode=BE): 임시 fixture(로컬 bare remote + clone 다수)로 5종 skip + behind-only(ff) + already-current + dirty/diverged 무손실. 실행: `~/.opal/tools/git-sync-tool/run.sh sync <fixture>` → JSON assert.
- **회귀 테스트**: install-mac.sh 재실행, 기존 도구/스킬 배포 정상 확인.
- **코드 품질**: @header 검증, kebab/snake-case 네이밍, git 2.22+ 명시.
- **보안**: 자율 조치 코드 부재 grep(`stash|rebase|--force|push|commit`) over git_sync_tool.py = 0건, subprocess 인자 리스트 방식.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 래퍼 | Bash (run.sh) | state-tool 패턴 |
| 도구 본체 | Python (표준 라이브러리: json/argparse/pathlib/sys/subprocess) | tool-scan/state-tool 패턴 |
| git 조작 | git CLI 2.22+ (fetch/status/rev-parse/symbolic-ref/rev-list/pull) | ANALYSIS §4 |
| 스킬 | Markdown + YAML frontmatter | opal-brain 템플릿, skill-creator |
| 배포 | Bash (install-mac.sh) | install 자동 순회 + chmod 패턴 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 로컬 git CLI·표준 라이브러리만 사용, 외부 API·라이브러리 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 도구/스킬 배포 모델·컴포넌트 구조 정합 |
| D-2 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·배포 경계·플랫폼 분기 격리 |
| D-3 | 소스 | state-tool | `opal/tools/state-tool/run.sh:1-12`, `state_tool.py:1-14,66-100` | run.sh 래퍼·@header·JSON 계약 패턴 |
| D-4 | 설계 | 도구 규약 | `opal/core/references/opal-harness.md` §9 | OPAL Tools 호출·JSON 출력 규약 |
| D-5 | 소스 | install 스크립트 | `scripts/install-mac.sh:1108-1163` | 도구 chmod +x 블록 삽입점·스킬 자동 순회 |
| D-6 | 소스 | opal-brain 스킬 | `opal/skills/opal-brain/SKILL.md:1-43` | operator 타입 스킬 frontmatter·모드 라우팅 템플릿 |
| D-7 | 소스 | 피드백 메모리 | `.opal/memory/feedback_skill_creation.md` | 스킬 생성 시 skill-creator 활용 |
| D-8 | 기획 | TASK.md | `tasks/052-.../TASK.md` | 확정·잠금 설계(스킬명·구조·순회·pull·skip 5종·보고서 5섹션) |
| D-9 | 설계 | ANALYSIS.md | `tasks/052-.../ANALYSIS.md` | 도구 구조·git 판정 명령·install 등록점·컨벤션 확정 사실 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | dirty/diverged 무손실 파손 | F-001 | P0 | ff-only 정책 + skip 후 조작 코드 부재 + L2 무손실 assert (H-1,H-2, TS-016~018) |
| R-2 | 5종 skip 판정 오류 | F-001 | P1 | 판정 순서 확정(no-upstream→detached→dirty→fetch→diverged) + L1·L2 (H-3, TS-002~006) |
| R-3 | diverged 컬럼 매핑 반전 | F-001 | P1 | [MUST] left=behind/right=ahead 확정 + behind-only ff 테스트 (H-4, TS-001) |
| R-4 | ff-only가 diverged pull | F-001 | P0 | ff-only + diverged skip 선행 + TS-018 (H-5) |
| R-5 | 승인 없는 자율 조치 | F-002 | P0 | 조치는 AskUserQuestion "제안"에만, 자동 실행 부재 grep 검증 (H-8, TS-013) |
| R-6 | git 2.22 미만 비호환 | F-001 | P2 | @header·SKILL.md에 git 2.22+ 명시 (H-9) |
| R-7 | install chmod 누락/오위치 | F-003 | P1 | memory-tool 블록 직후 동일 패턴 + install 후 `-x` 확인 (H-10, TS-014) |
| R-8 | 대상결정 3분기 오판 | F-002 | P1 | 스킬 STEP 1 명시 분기 + 도구는 경로만 순회 (책임 분리) (H-7, TS-009~011) |

---

## 설계 피드백

- **설계 빈틈**: 없음. TASK.md에서 스킬명·구조·순회 깊이·pull 정책·skip 5종·보고서 5섹션이 전부 잠겨 있고, ANALYSIS.md가 도구 구조·git 판정 명령·install 등록점·컨벤션을 모두 확정하여 PLAN이 재설계 없이 청사진화 가능.
- **PLAN이 확정한 미확정 잔여 2건** (ANALYSIS가 PLAN에 위임한 항목):
  1. **diverged 컬럼 매핑** — ANALYSIS §4 지시 → §3.1.2(d) [MUST]로 left=behind/right=ahead 확정 (H-4).
  2. **JSON 스키마 필드** — 태스크 지시 스키마를 §3.1.2(e)에서 필드별 타입·enum·null 규칙으로 최종 확정 (`already-current`를 status enum에 포함, summary는 total/updated/skipped/failed만 집계).
- **skill-creator 반영**: Step 3 [MUST]로 EXECUTE 시 skill-creator SKILL.md를 Read하여 프로세스를 따르도록 명시 (→ D-7).

## 변경이력

| 버전 | 작성일 | 변경내용 |
|------|--------|---------|
| v1.0 | 2026-07-02 | 초기 작성 — 4기능(F-001~004)·6스텝·복잡모드, JSON 스키마·판정순서·diverged 컬럼매핑·5섹션 보고서·승인게이트 [MUST] 확정, 리스크 가설 H-1~H-10 (052) |

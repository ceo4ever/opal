# RED-EVIDENCE: code-scan 결과 인용 게이트 (S-9 · S-10)

> 작성: 2026-09-04 23:31 (KST, `node ~/.opal/tools/date/date.js datetime`) | 작성자: opal-test-agent (TEST 단계, mode: be)
> 트랙: RED-first 적용 — `opal/core/references/harness/red-first.md` §1 「RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입」
> 적용 근거: `TEST-SCENARIO.md` 머리말 — `state_tool.py` 게이트 판정 로직은 판정 결과가 곧 통과 근거가 되는 self-confirming 위험 영역(`red-first.md` §1.5 「모호하면 RED-first 기본」). 대상 시나리오 **S-9 · S-10**.
> 검증 규율: mock/patch/MagicMock **0건**. 실 CLI 블랙박스 실행(`run.sh` / `python3 <state_tool.py>` subprocess) + 실 파일 상태(`md5`·JSON 재판독)로만 판정.

---

## 0. 관측 순서와 시점 한계 (정직한 기록)

이 태스크는 **구현(EXECUTE Step 4)이 이미 완료·배포된 시점에 TEST가 수행**되었다. 따라서 본 RED 증거는 「구현 전에 시간순으로 먼저 관측한 것」이 아니라, **개정 전 코드를 `git show HEAD:`로 복원해 동일 픽스처에 재현한 A/B 대조**다.

- 베이스라인 커밋: `69f5ce1` (`git rev-parse HEAD`) — 106의 변경이 아직 커밋되지 않았으므로 `HEAD:opal/tools/state-tool/state_tool.py`가 곧 **개정 전 원본**이다.
- 복원 방법: `cp -R opal/tools/state-tool <SP>/state-tool-HEAD` 후 `git show HEAD:opal/tools/state-tool/state_tool.py > <SP>/state-tool-HEAD/state_tool.py` — 형제 자산(`schema/`·`run.sh`)을 함께 두어 실행 경로를 보존했다.
- 복원본 게이트 부재 확인: `grep -c 'code_scan_citation' <SP>/state-tool-HEAD/state_tool.py` → **0**.
- 작성자≠구현자 유지: 구현은 `opal-be-agent`(Step 4), 본 RED/GREEN 관측은 `opal-test-agent`.

`red-first.md` §1의 「RED 먼저」 시간 순서를 이 태스크가 문자 그대로 지켰다고 주장하지 않는다. 확보한 것은 **동일 입력에서 개정 전이 실패하고 개정 후가 통과한다는 인과 증거**다. PM 판단이 필요하면 이 절을 근거로 삼으라.

---

## 1. 픽스처 (양 버전 공통 · 동일 입력)

프로젝트 밖 세션 스크래치패드에 생성했다. `SP` = `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/1d38c7a1-01d1-4758-91a1-021efe5acbf1/scratchpad`.

| 항목 | 값 |
|------|-----|
| 프로젝트 루트 인식 | `<트리>/.opal/MEMORY.json` (`find_project_root`가 조상 탐색으로 요구) |
| code-scan 설정 | `<트리>/.opal/code-scan.json` = `{"headerSource":"inline","scopes":{"src":"src/"},"extensions":[".py",".js",".ts"],"exclude":["node_modules","__pycache__"]}` |
| 태스크 폴더 | `<트리>/tasks/999-260904-opd-fixture` |
| 파이프라인 초기화 | `state-tool init <T> --skill opd --mode agentic --rows-from opal/skills/opal-pilot-dev/references/pipeline.json` (16행) |
| EXECUTE 진입 준비 | EXECUTE 이전 11행을 `done`으로 직접 세팅(픽스처 준비 — 검증 대상 아님). EXECUTE 첫 행 = `execute.implement`(row_id 12) |
| **RED-neg / S-9 픽스처** | `PLAN.md` §4.2에 `- **파일**: `src/app.py`` + 본문 인용 토큰 **0건** (「함수 하나를 고친다. 관련 사실은 파일을 열어 눈으로 읽어 확인했다.」) |
| **S-10 픽스처** | 동일 구조 + §4.2 본문에 `domain: core` · `layer: service` · `depends: ["util"]` · `exports: ["run"]` 인용 |

---

## 2. S-9 (인용 미충족 → exit 1 차단) — RED

### RED-1 — 라우터 부재

```
$ python3 <SP>/state-tool-HEAD/state_tool.py verify <T> --code-scan-citation-check
usage: state-tool [-h] <command> ...
state-tool: error: unrecognized arguments: --code-scan-citation-check
exit=2
```

**관측**: 개정 전에는 `--code-scan-citation-check` 플래그 자체가 존재하지 않는다. 인용 여부를 도구가 판정할 수단이 **0개**이며, `pm-review-gate.md` 항목 14가 PM 자기판정(「인용 부재 시 Fail → 재디스패치 1회」)에 의존하던 상태와 정합한다.

### RED-2 — EXECUTE 첫 행 훅 부재 (핵심 RED)

```
$ md5 -q <T>/state.json
dd332df86e9ddc59dae0bdc72c3c0392

$ python3 <SP>/state-tool-HEAD/state_tool.py mark <T> --task-step execute.implement --done \
      --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "RED 관측"
{"ok": true, "command": "mark", "row_id": 12, "stage": "EXECUTE", "item": "작업",
 "status": "done", "timestamp": "2026-09-04 23:21:53", "owner": "PM", "auto_approved": [],
 "todo_mirror": {...}, "worker_duration_minutes": 1}
exit=0

$ md5 -q <T>/state.json
065e5a4d3abc703565a8af01debc9599        ← 변경됨
```

**관측**: code-scan 인용이 **0건인 PLAN.md**로 EXECUTE 첫 행 진입을 시도했는데 개정 전 도구는 **거부하지 않는다**(`ok: true`, exit 0). `execute.implement` 행이 `status: done` / `owner: PM`으로 전이하고 `state.json` md5가 변한다 — 인용 없는 디스패치가 그대로 통과한다.

⇒ **RED 성립**: R-4 AC(b)가 요구하는 차단이 개정 전에는 존재하지 않는다.

### GREEN — 개정 후 (배포본)

```
$ ~/.opal/tools/state-tool/run.sh verify <T> --code-scan-citation-check
{"ok": false, "command": "verify", "error": "code_scan_citation_unmet",
 "message": "PLAN.md에 code-scan 결과 인용 없음 — EXECUTE 진입 차단 (pm-review-gate.md 항목 14): ['citation_absent']",
 "code_scan_citation_check": "unmet", "missing": ["citation_absent"],
 "target_files": ["src/app.py"], "matched_tokens": []}
exit=1

$ md5 -q <T>/state.json  →  b5bb12f3f337031e9e9f9aee9ec567fc   (호출 전)

$ ~/.opal/tools/state-tool/run.sh mark <T> --task-step execute.implement --done \
      --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "S-9 관측"
{"ok": false, "command": "mark", "error": "code_scan_citation_unmet",
 "message": "... ['citation_absent']", "missing": ["citation_absent"]}
exit=1

$ ~/.opal/tools/state-tool/run.sh advance <T> --task-step execute.implement
{"ok": false, "command": "advance", "error": "code_scan_citation_unmet", "missing": ["citation_absent"]}
exit=1

$ md5 -q <T>/state.json  →  b5bb12f3f337031e9e9f9aee9ec567fc   (호출 후 — 동일, 6123 바이트)
```

**GREEN 성립**: ① 라우터가 `ok:false` · `code_scan_citation_unmet` · **exit 1** ② `mark`·`advance` 두 집행 지점 모두 동일 에러코드로 거부 ③ `state.json` **바이트 무변경**(md5 동일) — 거부가 `save_state_json()` 이전 검증 구간에서 일어나 파일이 오염되지 않는다.

| 축 | RED (HEAD `69f5ce1`) | GREEN (배포본) |
|----|---------------------|----------------|
| `verify --code-scan-citation-check` | 플래그 부재 · exit **2**(argparse) | `unmet` · exit **1** |
| EXECUTE 첫 행 `mark` | `ok:true` · exit **0** | `ok:false` · exit **1** |
| EXECUTE 첫 행 `advance` | (미관측 — `mark`로 대표) | `ok:false` · exit **1** |
| `state.json` md5 | `dd332df…` → `065e5a4…` **변경** | `b5bb12f…` → `b5bb12f…` **무변경** |

---

## 3. S-10 (인용 충족 → exit 0 통과) — RED

### RED

개정 전 베이스라인에는 통과 판정을 **낼 수단 자체가 없다** — RED-1과 동일하게 `--code-scan-citation-check`가 `unrecognized arguments`(exit 2)로 거부된다. 즉 「인용이 있으면 통과한다」는 계약을 개정 전 도구로는 관측할 수 없다(판정 라우터 0개). 이것이 S-10의 RED다: 통과·차단 어느 쪽도 도구가 말하지 못하는 상태.

### GREEN — 개정 후 (배포본)

```
$ ~/.opal/tools/state-tool/run.sh verify <T-pos> --code-scan-citation-check
{"ok": true, "command": "verify", "code_scan_citation_check": "pass", "reason": null,
 "target_files": ["src/app.py"],
 "matched_tokens": ["domain", "layer", "depends", "exports", "code-scan"]}
exit=0

# 행 상태 전이 관측
before: execute.implement status= pending
$ ~/.opal/tools/state-tool/run.sh mark <T-pos> --task-step execute.implement --done \
      --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "S-10 관측"
{'ok': True, 'command': 'mark', 'row_id': 12, 'stage': 'EXECUTE', 'status': 'done', 'owner': 'PM'}
exit=0
after:  execute.implement status= done owner= PM ts= 2026-09-04 23:22:15
```

**GREEN 성립**: ① `code_scan_citation_check: "pass"` · `reason: null` · **exit 0** · `matched_tokens` **5건**(≥1 충족) ② EXECUTE 첫 행 `mark` 정상 진행 — `pending → done` 전이 및 timestamp 기록을 `state.json` 재판독으로 확인.

---

## 4. 미탐/오탐 경계 — 게이트가 공허하게 통과하지 않음의 증거 (H-10)

RED→GREEN만으로는 「게이트가 항상 거부한다」 또는 「항상 통과한다」는 축퇴 구현도 통과할 수 있다. 그 축퇴를 배제하는 대조군을 함께 관측했다.

| # | 입력 | 관측 | 의미 |
|---|------|------|------|
| 1 | `.py` 대상 + 인용 0건 | `unmet` · exit 1 | 정탐 |
| 2 | `.py` 대상 + 인용 보유 | `pass` · exit 0 · `matched_tokens` 5 | 오탐 아님 |
| 3 | `.md`만 대상 + `--auto-pass` | `skipped` · `doc_only_task` · exit 0 · 거부 0건 | 순서 계약(게이트 ⑤ → ⑥) 성립 (S-24) |
| 4 | `.py` 대상 + 인용 0건 + `--auto-pass` | `unmet`(`auto-pass cannot bypass code-scan citation gate`) · exit 1 | 게이트 ⑥ 생존 — 3번의 통과가 「게이트 사망」이 아님 |
| 5 | `code-scan.json` 부재 | `skipped` · `code_scan_unavailable` · exit 0 | 미보급 프로젝트 오탐 0건 |
| 6 | PLAN.md 부재 | `skipped` · `plan_md_absent` · exit 0 | 하위호환 skip |
| 7 | 이 레포 태스크 106 폴더 | `pass` · exit 0 · `matched_tokens` 9 · `target_files` 20 | 실환경 오탐 0건 (S-11) |

토큰 경계 방어도 소스로 확인했다 — `_CODE_SCAN_CITATION_RES`가 `(?<![\w-])…(?![\w-])`를 두어 `depends_on`(Step 의존 필드)이 `depends`로 오인되지 않는다(`state_tool.py:2536-2545`). 이 경계가 없으면 모든 PLAN이 무조건 통과해 게이트가 무력화된다.

---

## 5. 회귀 무영향 — 개정 전후 동형 확인 (H-6)

RED-first 대상이 아닌 축이지만 「게이트 신설이 기존 경로를 깨지 않았다」는 A/B 증거를 같은 베이스라인으로 확보했다.

EXECUTE 단계를 보유한 파이프라인 **8종**(opd·opds·opdw·opp·oppd·oppl·opsdd·opwt) × 개정 전/후 2버전 × 픽스처 2변이(설정 부재=skip / 설정+인용=pass) = **32 실행**, 각각 EXECUTE 첫 행 `advance`:

- 전건 **exit 0 · `ok: true` · `error: None`** — 예기치 않은 거부 **0건**
- stdout 키 집합이 32 실행 전건 동일: `auto_approved, command, item, ok, row_id, stage, status, timestamp, todo_mirror`
- 파이프라인별 EXECUTE 첫 키: opd·opds·opdw·opp `execute.implement` / oppd `execute.actions` / oppl `execute.l0_select` / opsdd `execute.act_run` / opwt `execute.batches`
- `opdd`·`opgc`는 EXECUTE 행 **0개**(15행 / 7행)로 대상 아님

---

## 6. 사용한 명령 원문 (재현용)

```bash
SP=/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/<session>/scratchpad
REPO=/Volumes/Data/AIStudio/workspace/ai-framework

# (1) 개정 전 베이스라인 복원
cp -R "$REPO/opal/tools/state-tool" "$SP/state-tool-HEAD"
git -C "$REPO" show HEAD:opal/tools/state-tool/state_tool.py > "$SP/state-tool-HEAD/state_tool.py"
grep -c 'code_scan_citation' "$SP/state-tool-HEAD/state_tool.py"     # → 0 (게이트 부재)

# (2) 픽스처 (mkfix.sh <name> <inline|manifest|NONE> <none|py-nocite|py-cite|md-only>)
#     루트에 .opal/MEMORY.json + .opal/code-scan.json 생성 → state-tool init → EXECUTE 앞 구간 done → PLAN.md 작성

# (3) RED (개정 전)
python3 "$SP/state-tool-HEAD/state_tool.py" verify "$T" --code-scan-citation-check
python3 "$SP/state-tool-HEAD/state_tool.py" mark "$T" --task-step execute.implement --done \
        --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "RED 관측"

# (4) GREEN (배포본 — H-11 회피)
"$HOME/.opal/tools/state-tool/run.sh" verify "$T" --code-scan-citation-check
"$HOME/.opal/tools/state-tool/run.sh" mark "$T" --task-step execute.implement --done \
        --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "S-9 관측"
"$HOME/.opal/tools/state-tool/run.sh" advance "$T" --task-step execute.implement
md5 -q "$T/state.json"      # 호출 전후 대조
```

임시 자원은 관측 종료 후 `rm -rf`로 회수했다(`find` 실측 잔여 0건). 재현 시 픽스처를 다시 생성해야 한다.

---

## 7. 요약

| 시나리오 | RED (개정 전, HEAD `69f5ce1`) | GREEN (개정 후, 배포본) | 판정 |
|---------|------------------------------|------------------------|------|
| S-9 | `verify` 플래그 부재 exit 2 · 인용 0건 `mark` **ok:true exit 0** · `state.json` 변경 | `unmet` exit 1 · `mark`/`advance` 거부 exit 1 · `state.json` 무변경 | **Pass** |
| S-10 | 판정 라우터 부재(플래그 미인식) — 통과 판정 수단 0개 | `pass` exit 0 · `matched_tokens` 5 · `mark` 정상 전이 | **Pass** |

`state.json`·`STATE.md`·`schema/*.json`에 신규 영속 필드는 **0건**이며, 거부 경로에서 파일 바이트가 변하지 않음을 md5로 실증했다.

변경이력: v1.0 | 2026-09-04 23:31 | S-9·S-10 RED-first 증거 초기 작성 — 개정 전 베이스라인(`git show HEAD:`) 복원 A/B 대조 + 미탐/오탐 경계 7케이스 + 8 파이프라인 회귀 동형 (106)

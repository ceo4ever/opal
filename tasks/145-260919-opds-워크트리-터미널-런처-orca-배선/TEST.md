---
template: sdlc-v2
---
# TEST: 워크트리 전용 터미널 런처 orca 경로 배선 — 독립 검증

> 검증자: opal-test-agent (BE mode, 독립 평가자) | 검증일시: 2026-09-19 15:56 KST
> 역할: PM이 구현·실행·마킹한 판정을 그대로 옮기지 않고, 직접 재실행·재대조한 증거로 재검증한다.

## 0. 잠금·마킹 현황 재확인

```
~/.opal/tools/test-tool/run.sh scenario-status --task-path <task-folder>
→ {"ok": true, "locked": true, "total": 15, "red_confirmed": 9, "red_required": 9,
   "passed": 15, "failed": 0, "blocked": 0, "awaiting_human": 0}
```

PM 신고(locked=true, 15/15 pass, red 9/9)와 일치함을 도구로 직접 확인.

## 1. 결정론 시나리오 직접 재실행

스위트별 독립 실행(conftest 충돌 회피):

| 명령 | 결과 | 기준선 대비 |
|---|---|---|
| `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests -q` | **110 passed, 1 skipped** | 기준선(110 passed/1 skipped)과 **바이트 동일** |
| `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests -q` | **146 passed** (111.28s) | 기준선(146 passed)과 **동일**, 회귀 0건 |

두 수치 모두 `test-scenario.json` S-12 증거("110 passed/1 skipped", "146 passed in 120.11s")와 재현 결과(passed 수 동일, 소요시간만 환경차)가 일치한다.

## 2. 시나리오별 판정 (S-1~S-15)

| ID | 판정 | 재검증 근거 |
|---|---|---|
| S-1 | **PASS** | `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py` 직접 확인 — `parse_response()`가 `result.terminal`만 읽음(D-D 준수), `_reported_cwd()`가 `worktreeId` 첫 `::` 분리로 구현됨. 재실행 스위트에 `test_adapter_orca.py` 포함되어 통과 |
| S-2 | **PASS** | `grep -rn "PROMPT_SOURCE_SESSIONSTART_CLAIM\|sessionstart_claim_observation" worktree_launcher/` → **0건** 직접 확인. orca.py docstring에 `prompt_receipt_source`는 항상 `launch_argv`로 명시 |
| S-3 | **PASS (단, RED 증거 신뢰도 하향 — §4 참조)** | `test_adapter_conformance.py`가 실재하고 재실행 스위트에 포함되어 통과. RED 증거 자체의 재현 가능성에는 의문점 있음(§4-3) |
| S-4 | **PASS** | `test_launcher_core.py` 238~450행 직접 Read — 복귀 5경로(`launch_receipt_missing`·`reported_cwd_mismatch`·`prompt_receipt_missing`·`adapter_report_invalid`·`ownership_set_rejected`) 전건에서 handle 존재 시 `close` 정확히 1회, handle 부재 시 미시도, close 예외/비-0/`AttributeError` 전부 복귀를 막지 않음을 각 테스트 함수 단위로 확인. 재실행 스위트 포함 통과 |
| S-5 | **PASS** | `cli.py` 존재, `run.sh` 내 `not_implemented` 리터럴 0건(재확인: `grep not_implemented run.sh` 미검출), 재실행 스위트 통과 |
| S-6 | **PASS** | `setting.default.json`에 `launcher` 블록 존재, `_help`에 `models` 비대칭 근거 문장 확인. 재실행 스위트 통과 |
| S-7 | **PASS** | `worktree_tool.py`의 `cmd_remove` 소스에서 스윕 호출이 3중 가드 통과 직후·`git worktree remove` 직전 위치. 재실행 스위트(`test_worktree_tool.py` 146 passed) 포함 |
| S-8 | **PASS** | 재실행 스위트 포함 통과. `worktree.md`/`task-process.md` diff에서 `completed_unmerged` 파생 필드 확인(§3) |
| S-9 | **PASS** | `git diff`로 `task-process.md`·`worktree.md` 변경분을 직접 대조 — 4.5 `ok:true`에 포인터 1줄만 추가, 명령 블록은 5.5가 단독 소유, `worktree.md` 신설 절의 `main merge·push` 행이 `guards.md` §커밋 규칙 포인터만 가짐. 원문 복제 0건, "워크트리에서 merge 수행" 문구 0건 재확인(§3) |
| S-10 | **PASS (문서 대조)** | live 재실행 안 함(지시 준수). `evidence/S-11-live.md` (1)절의 `adapter_handle`·`reported_cwd` 실측값이 S-10 기대 결과(둘 다 채워짐)를 충족 |
| S-11 | **PASS (문서 대조, 조건부 확인)** | live 재실행 안 함. `evidence/S-11-live.md`에 (1)정상 경로 registry 객체 2종, (2)실패 주입 `hub_owned`+터미널 0개, (3)사람 입력 0회 첫 턴 자기시작(상태줄·hook 발화 로그) 전건 기록 확인 — **skip이 아니라 실제 실행됐다**(§4-1) |
| S-12 | **PASS** | §1 직접 재실행으로 재확인(worktree-launcher/worktree-tool 2스위트). state-tool 스위트는 재실행 지시에 없어 기록된 증거(535 passed/3 skipped)만 대조, 재실행하지 않음 |
| S-13 | **PASS** | `orca.py` close() 소스 직접 확인 — `--terminal`/`--worktree --all` 2스코프가 서로의 플래그를 만들지 않음, 인자 배타성 위반 시 `close_scope_invalid`. 재실행 스위트 통과 |
| S-14 | **PASS** | `test_adapter_conformance.py` 396~496행 직접 Read — C-1(모듈 동결+git status 대조)·C-2(ClassDef/ABC AST 검사)·C-4(금지 문자열 grep)·C-5(registry 직접 쓰기 AST 검사 + `ownership-set` positive 대조) 전건 실제 AST/grep 코드로 구현됨을 확인 |
| S-15 | **PASS** | `test_worktree_tool.py`에 `test_s15_checkpoint_on_main_branch_still_requires_user_approval`(`protected_branch_commit`)·`test_s15_checkpoint_on_hub_root_still_requires_user_approval`(`hub_commit`) 존재 확인. 문서 grep으로 "워크트리에서 merge 수행" 문구 0건 재확인 |

## 3. AC 역방향 대조 (AC → 시나리오, 코드/문서 직접 확인)

| AC | 커버 S | 직접 확인 |
|---|---|---|
| AC-1 | S-5 | `SUPPORTED_ADAPTERS` 폐쇄 목록, `--adapter` 누락/목록 밖 거부 — cli.py 존재 확인 |
| AC-2 | S-1·S-2·S-10 | parse_response 실물 파싱 확인(위 S-1) + S-10 live 증거 문서 대조 |
| AC-3 | S-5·S-11 | S-11 evidence (1)절 `worktree_session_owned` 전이 + registry 객체 2종 |
| AC-4 | S-4 | 위 S-4 재검증 — 5경로 close 계약 코드 확인 |
| AC-5 | S-9·S-11 | S-9 문서 diff 확인 + S-11 evidence (2)절 첫 턴 자기시작 |
| AC-6 | S-7 | `cmd_remove` 스윕 위치 확인 + evidence (4)절 `task_994` 회수 0개 |
| AC-7 | S-5·S-6 | `launcher.agents.claude/codex` 존재, `default` 교체 시 명령 변경 — `test_settings.py` 재실행 통과로 간접 확인(직접 값 대조는 생략) |
| AC-8 | S-2·S-3·S-10·S-13 | 적합성 스위트(S-14 코드) + S-13 close 인자 검사 |
| AC-9 | S-8 | 재실행 스위트 통과 |
| AC-10 | S-12 | §1 재실행 결과로 회귀 0건 확인 |

AC-1~AC-10 전건이 실제 시나리오·코드로 대응됨을 확인. 커버리지 매핑 표(TEST-SCENARIO.md)와 실제 코드/문서 상태 사이에 불일치 없음.

## 4. 엄격 검토 대상 3건 판정

### 4-1. S-11이 skip이 아니라 실제로 실행됐는가 — **충족**

`evidence/S-11-live.md`에 다음이 모두 기록돼 있어 skip이 아니라 실측임을 확인했다(문서 대조, live 재실행하지 않음 — 지시 준수):

- (1) 실제 명령(`worktree-launcher/run.sh launch --adapter orca …`)과 실제 JSON 응답(`adapter_handle`·`launch_receipt`·`prompt_receipt` 구체값)
- registry 직접 조회 결과(`execution_ownership.state = worktree_session_owned`, receipt 2종이 **객체**로 기록)
- (2) `orca terminal read` 실제 stdout(상태줄에 `task_996 │ feat/OP-TASK-996 │ 🎯 996` 표시, `Brewed for 1m 10s`, hook 3/3 발화)
- (3) 실패 주입 JSON 응답(`hub_owned`, `terminal_close.attempted=false`)과 (4) 회수 JSON 응답(`terminals_closed.exit_code=0`)

AGENTIC-LOG의 사전 조건("S-11이 skip이면 TEST PM Gate를 Fail로 판정한다")이 요구한 "명령·스코프·출력 기록"이 실제로 존재한다. **판정: 조건 충족.**

### 4-2. AC-4의 live 한계 분리가 타당한가 — **타당**

`evidence/S-11-live.md`의 자기신고("실패 주입 경로는 터미널이 생성된 적이 없어 …")를 코드로 대조했다.

- `test_launcher_core.py`의 `test_revert_closes_reported_terminal_exactly_once_on_every_handle_path`(238행)와 `test_revert_closes_terminal_when_ownership_set_rejects_the_owned_transition`(408행)이 **handle이 실재하는** 5개 복귀 경로(`launch_receipt_missing`·`reported_cwd_mismatch`·`prompt_receipt_missing`·`ownership_set_rejected` + `adapter_report_invalid`의 부재 케이스)를 fake adapter로 전건 커버한다.
- `_ClosingAdapter.close()`가 실제로 handle 인자를 받아 기록하는 방식이라 "이미 만든 터미널을 닫는다"는 동작 자체를 코드 레벨에서 검증하고 있다 — live에서 그 경로를 못 밟은 것을 단위 테스트가 정확히 메운다는 주장이 코드와 일치한다.
- **판정: 분리 타당. S-4가 AC-4의 "이미 만든 터미널 정리" 요구를 실제로 소유한다.**

### 4-3. RED 원장 기록 시점 이탈 — **절차 이탈은 사실, 증거 내용은 대부분 실측이나 S-3 1건은 신뢰도가 낮다**

- `red_at` 9건이 전부 `2026-09-19T15:38:43`로 **동일 초**다. 이는 각 워커의 실제 RED 관측 시각이 아니라 `scenario-red` 도구를 **일괄 호출한 기록 시각**이라는 뜻이며, AGENTIC-LOG의 자기신고("원장 기록 시점이 GREEN 이후다")와 일치한다. **절차 이탈은 사실이다.**
- 그러나 `red_evidence` 문자열은 각기 다른 수치를 담고 있고, 다음은 AGENTIC-LOG의 워커 보고와 **대조 가능하며 일치**한다:
  - S-1 "13 failed, 3 passed" ↔ AGENTIC-LOG "워커 보고(RED 13 failed/3 passed → GREEN 16, 회귀 55)와 일치"
  - S-4 "5 failed, 6 passed" ↔ AGENTIC-LOG "워커 보고(기준선 5 → RED 5 failed/6 passed → GREEN 11, 스위트 55)와 일치" (+5번째 경로 보완 "1 failed" ↔ "RED 1 failed/11 passed → GREEN 12"와 일치)
  - S-6 "3 failed, 18 errors, 0 passed" ↔ AGENTIC-LOG "워커 보고(RED 3 failed/18 errors → GREEN 21 passed)와 일치"
  - S-5·S-7·S-8·S-13은 AGENTIC-LOG에 개별 수치 재인용은 없으나, 같은 워커·같은 시점(W-6/W-3/W-4)의 RED 실행이라는 서술과 모순되지 않는다.
  - 이 문자열들은 **사후 합리화(값을 지어냄)가 아니라 각 워커가 실행 중 실제로 관측·보고한 원문을 옮긴 것**으로 판단한다. 도구 호출 시점만 늦었을 뿐 관측 자체는 실측이다.
- **예외 — S-3**: 증거 문자열이 "W-7 RED: test_adapter_conformance.py 신규 — 구현 전 orca 모듈에 read/close 부재로 AttributeError **(W-4 GREEN 전 상태 기준)**"이다. PLAN.md의 Work item 선행 관계상 W-7(P3)은 W-4·W-5(P2)의 GREEN 완료 **이후에** 디스패치됐다(AGENTIC-LOG "EXECUTE P3 착수"가 P2 완료 다음에 나온다). 즉 `test_adapter_conformance.py` 자체가 존재한 시점에는 이미 orca에 `read`/`close`가 구현되어 있었을 가능성이 높고, "구현 전 AttributeError"는 실제로 그 순간에 재현한 관측이라기보다 **"W-4 GREEN 이전이었다면 이랬을 것"이라는 사후 추론(counterfactual)** 으로 읽힌다. AGENTIC-LOG 어디에도 W-7의 실제 RED 실행 로그(실패 건수·오류 메시지 원문)가 없다.
  - 이 자체가 시나리오 결과를 뒤집지는 않는다 — 현재 코드에 실제로 `read`/`close`가 존재하고 GREEN 테스트가 29 passed로 통과하며, "만약 없었다면 AttributeError"라는 명제 자체는 논리적으로 참이다. 하지만 **RED 증거의 품질이 다른 8건과 다르다** — 재현 가능한 실행 로그가 아니라 추론 진술이다.
  - **판정**: S-3의 `result: pass`는 유지 가능(GREEN 코드·스위트 통과가 실재하므로)하나, `red_confirmed: true`의 근거는 다른 8건보다 약하다는 사실을 이 보고서에 남긴다. 전체 게이트 판정(9/9 red_confirmed)을 뒤집을 만큼의 결함은 아니라고 판단하되, **PM Gate 재발 방지 조치("scenario-red를 EXECUTE 첫 워커 디스패치 전에 끝낸다")가 실제로 다음 태스크부터 집행되는지 후속 확인이 필요하다.**

## 5. 코드 품질 회귀 가드

- 재실행한 2스위트(256건) 전건 통과, 신규 경고·오류 없음.
- 하드코딩 시크릿·`.gitignore` 이상 없음(변경 파일이 테스트/문서/설정 스키마뿐이며 시크릿 성격의 값 없음 — `evidence/S-11-live.md`의 `owner_session_id`·`task_path` 등은 시크릿이 아님).
- 목업 대체 여부: S-10·S-11은 실제 orca CLI 응답 그대로이며 mock 없음. 그 외 unit 스위트는 명세상 `required_fidelity: mock`으로 지정된 fake adapter만 사용 — 지시된 실연동 항목(S-10/S-11)을 목업으로 대체한 사실 없음.

## 6. 최종 판정

**All Pass** — 15/15 시나리오가 증거와 실제 코드/문서 상태에 부합하며, 직접 재실행한 2개 결정론 스위트(256건)가 전건 통과했다. AC-1~AC-10 전건이 시나리오로 역추적된다.

단, 다음은 **결함이 아니라 기록 대상 관찰**로 남긴다:
1. RED 원장 기록이 GREEN 이후 일괄 처리된 절차 이탈(자기신고와 일치) — 증거 내용 자체는 대부분 실측.
2. S-3의 RED 근거는 재현 로그가 아닌 사후 추론 진술로, 다른 8건과 증거 품질이 다르다.
3. `evidence/S-11-live.md`가 스스로 신고한 "발견 3건"(owner_session_id 미기록으로 워크트리 세션이 체크포인트 자격을 못 얻음, `--all` 스윕의 `closed` 상시 공백, TUI 종료 시 비-0 오탐)은 이번 AC 범위 밖이며 후속 태스크 후보로 남는다.

## 검증 명령 요약

```bash
~/.opal/tools/test-tool/run.sh scenario-status --task-path <task-folder>
~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests -q   # 110 passed, 1 skipped
~/.opal/.venv/bin/python -m pytest opal/tools/worktree-tool/tests -q      # 146 passed
grep -rn "PROMPT_SOURCE_SESSIONSTART_CLAIM|sessionstart_claim_observation" opal/tools/worktree-launcher/worktree_launcher/  # 0건
git diff opal/core/references/harness/task-process.md opal/core/references/harness/worktree.md
```

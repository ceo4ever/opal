# PROBE-GAPS.md — W-4 4경로 갭 실측과 범위 확정

- **Work item**: W-4 (실행 그룹 P4)
- **checklist_source**: `PLAN.md` W-4 행 + `Decisions and contracts` **D-M**
- **scenario_source**: `TEST-SCENARIO.md` **S-5**
- **완료 기준**: AC-5 · C-2
- **선행 게이트**: W-3(AC-4) PASS — `block_continue` 실측 확인. P4 개방.
- **이 Work item은 코드를 바꾸지 않는다.** 산출물은 이 파일 1건뿐이다.
- **총평**: 4경로 전건 실측 완료. **4경로 모두 `후속 경계`** — 수정 지점이 PLAN `변경 대상` 4파일 밖이고, 4경로 중 4경로가 새 계약 결정을 요구한다(D-M (i)·(ii) 동시 불충족).

---

## H-5 — 착수 직후 세션 식별자 3종

| 식별자 | 값 | export 여부 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | **export 됨** (`export -p`에 1건) |
| `OPAL_SESSION_ID` | (env·`export -p` 모두 **0건**) | **export 안 됨** — W-2가 소유한 export 결함의 현재 상태 유지 |
| 봉투 `session_id` (기준 경로) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 위 2종과 동일 |

- `resolve_session_id`(`ownership_core.py:349`) 우선순위는 ① `OPAL_SESSION_ID` ② `CLAUDE_CODE_SESSION_ID` ③ 봉투다. `OPAL_SESSION_ID` 미export이므로 이번 프로브의 실제 해석 경로는 **②**이고, ②·③ 값이 같아 판정에 영향이 없었다(W-3과 동일).
- 이 우선순위 때문에 **경로 1(세션 재시작)은 봉투 `session_id`만 바꿔서는 성립하지 않는다.** 실제 재시작은 env `CLAUDE_CODE_SESSION_ID`도 새 값이 되므로, 봉투와 env를 **함께** 새 값으로 두어 구성했다(아래 경로 1 구성 참조).
- 허브 registry(`…/.opal-worktrees/.meta/task_999.json`)의 `owner_session_id`는 여전히 **`null`(미기재)**이다. 타 세션 owner가 아니므로 blocked 조건이 아니다 — W-2·W-3과 같은 판정을 유지한다.

**H-5 판정: 충족.** 3종 전건 기록됐고, `OPAL_SESSION_ID` 미export가 이번 4경로 판정 어디에도 영향을 주지 않았음을 식별자 해석 경로로 확인했다.

---

## 0. 인계받은 기준선 (재측정하지 않고 인용)

| 항목 | 값 | 출처 |
|---|---|---|
| stop-guard receipt `block_count` | **3** | W-5 |
| 같은 receipt `fingerprint` · `decided_at` | 둘 다 **`null`** | W-3 · W-5 |
| run-log 최신 `sequence` | 13 | W-5 |
| `state.json` `execute.implement` `step` | `4/11` (행 status `in_progress` 불변) | W-5 |
| `run/.runtime/owner.json` | `claim_source=state_transition`, `owner_session_id=4e1a2aa2-…b237`, `generation=1` | W-2 |

착수 직후 실독으로 기준선 3을 확인했다(재측정이 아니라 출발점 확인):

```
{"block_count": 3, "decided_at": null, "decision_kind": "block_continue", "fingerprint": null, "session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237"}
```

---

## 1. 실행 표면 — C-4 준수 근거

- **공개 hook 진입점 1종만 사용**: `~/.claude/settings.json`의 `_opal_managed: true` Stop 항목 원문과 동일한
  `"$HOME/.opal/.venv/bin/python" "$HOME/.opal/tools/ownership-tool/ownership_tool/stop_hook.py"`.
- **evaluator 덤프**는 `stop_evaluator.evaluate(payload, project_root=payload["cwd"])` 1형태뿐이다. 이는 `stop_hook.py:51`의 호출 형태와 **인자까지 동일**하다 — `show_json`·`prior_receipt`·`env`·lease를 **주입하지 않는다**.
- 배포본과 워크트리 소스 동일성 확인: `diff -q ~/.opal/…/stop_evaluator.py <worktree>/…/stop_evaluator.py` → **동일**.
- **C-6 준수**: 봉투 `transcript_path`는 실존 경로를 채우기만 했고 **열거나 읽지 않았으며** 판정 입력으로 쓰지 않았다. 임시 트리 경로들은 `transcript_path`를 `/dev/null`로 두었다.
- **C-1 준수**: `~/.opal/` 아래에 어떤 쓰기도 하지 않았다(읽기·실행만).
- **C-5 준수**: 태스크 999 자산과 이 세션 스크래치패드 외에는 건드리지 않았다. 타 태스크·슬롯의 lease·registry·run-log를 읽지도 쓰지도 않았다.

증거 파일 접두: `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework--opal-worktrees-task-999/4e1a2aa2-1800-43e6-af3c-60b86a27b237/scratchpad/w4/`

| 경로 | 봉투 원문 | hook stdout | evaluator 덤프 |
|---|---|---|---|
| 1 | `p1-envelope.json` | `p1.hook.stdout` | `p1.dump.json` |
| 1b | `p1b-envelope.json` | `p1b.hook.stdout` | `p1b.dump.json` |
| 2 | `p2-envelope.json` | `p2.hook.stdout` | `p2.dump.json` |
| 3a·3b·3c | `p3a/3b/3c-envelope.json` | `p3{a,b,c}.hook.stdout` | `p3{a,b,c}.dump.json` |
| 4a·4b·4c | `p4-envelope.json` (공용) | `p4{a,b,c}.hook.stdout` | `p4{a,b,c}.dump.json` |

---

## 2. 경로별 봉투 구성

| 경로 | 구성 방법 | `cwd` | 봉투 `session_id` | env `CLAUDE_CODE_SESSION_ID` | `stop_hook_active` | env `…BLOCK_CAP` |
|---|---|---|---|---|---|---|
| **1. 세션 재시작 직후** | 새 UUID를 봉투와 env **양쪽**에 넣어 주입. 실물 lease는 이전 세션 소유 그대로(변경 없음) | 실제 워크트리 루트 | `9f3c0b21-…0001` | `9f3c0b21-…0001` | `false` | 미설정 |
| **1b. 재시작 + SessionStart 재claim** | 임시 트리에 `claim_source=session_start`·`owner_session_id=새 UUID` lease와 정상 `state.json`을 두고 주입 (실물 `owner.json` 무변경) | `…/w4/p1b` | `9f3c0b21-…0001` | `9f3c0b21-…0001` | `false` | 미설정 |
| **2. 상태 전이 없는 재개** | 현재 세션 ID + 실물 lease 유지 + `stop_hook_active: true`. 이번 턴에 새 `state.changed`를 만들지 않은 상태에서 주입 | 실제 워크트리 루트 | `4e1a2aa2-…b237` | `4e1a2aa2-…b237` | **`true`** | 미설정 |
| **3a. state view 부재(파일 없음)** | 임시 트리 `…/w4/p3a`에 현재 세션 소유 lease만 두고 `state.json`을 **만들지 않음** | `…/w4/p3a` | `4e1a2aa2-…b237` | (상속) | `false` | 미설정 |
| **3b. state view 해석 불가(깨진 JSON)** | 동일 구조 + `state.json`에 `{ this is not valid json` | `…/w4/p3b` | `4e1a2aa2-…b237` | (상속) | `false` | 미설정 |
| **3c. 대조군(정상 state)** | 동일 구조 + 정상 `state.json`(`in_progress`) | `…/w4/p3c` | `4e1a2aa2-…b237` | (상속) | `false` | 미설정 |
| **4a. cap 미설정** | 경로 2와 같은 봉투, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` **미설정** | 실제 워크트리 루트 | `4e1a2aa2-…b237` | (상속) | `true` | **미설정** |
| **4b. cap 설정(작은 값)** | 같은 봉투, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=1` | 실제 워크트리 루트 | `4e1a2aa2-…b237` | (상속) | `true` | **`1`** |
| **4c. cap 설정(큰 값·대조군)** | 같은 봉투, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=99` | 실제 워크트리 루트 | `4e1a2aa2-…b237` | (상속) | `true` | **`99`** |

> **경로 3이 실물을 건드리지 않았음** — 실물 `state.json`은 읽지도 쓰지도 않았고, 3a/3b/3c는 전부 스크래치패드 안의 별도 트리다. 3계열 실행 전후 실물 receipt `block_count`가 **3에서 불변**인 것이 이를 뒷받침한다(§4 원장).

---

## 3. 4경로 × 6지표 실측표

`decision_kind`는 evaluator 반환값, `hook stdout`은 공개 진입점 실제 출력이다.

| 경로 | `claim_source` | `evidence.forced_count` | `decision_kind` | `diagnostics` | `evidence.fingerprint` 유무 / receipt `fingerprint` | `stop_hook_block_cap(env)` 반환 | hook stdout |
|---|---|---|---|---|---|---|---|
| **1** 세션 재시작 직후 | `state_transition` (후보 evidence) | **0** | `allow_inactive` | `["foreign_owner", "no_owned_task"]` — `passive_ownership` 없음 · `allow_block_cap_reached` 없음 · `allow_no_progress_same_fingerprint` 없음 | **키 없음** / 새 세션 receipt `null` (기존 receipt는 `null` 유지) | `None` | **0바이트(무출력 통과)** |
| **1b** 재시작 + SessionStart 재claim | **`session_start`** | **0** | `allow_inactive` | **`["passive_ownership", "no_owned_task"]`** | **키 없음** / `null` | `None` | **0바이트(무출력 통과)** |
| **2** 상태 전이 없는 재개 | `state_transition` | **1** | **`block_continue`** | `[]` — **`allow_no_progress_same_fingerprint` 미발화** | **키 없음** / `null` (불변) | `None` | 332바이트 `{"decision":"block",…}` |
| **3a** state view 부재(파일 없음) | (후보 자체가 소멸 — `candidate_count: 0`) | **0** | `allow_inactive` | `["no_owned_task"]` | **키 없음** / `null` | `None` | **0바이트(무출력 통과)** |
| **3b** state view 해석 불가(깨진 JSON) | (노출 안 됨 — `invalid_state` 분기가 lease 판정 이전에 종료) | **0** | `allow_inactive` | `["invalid_state", "no_owned_task"]` | **키 없음** / `null` | `None` | **0바이트(무출력 통과)** |
| **3c** 대조군(정상 state) | `state_transition` | **1** | **`block_continue`** | `[]` | 키 없음 / `null` | `None` | 298바이트 `{"decision":"block",…}` |
| **4a** cap 미설정 | `state_transition` | **1** | **`block_continue`** | `[]` — **`allow_block_cap_reached` 미발화** | 키 없음 / `null` | **`None`** (상한 검사 자체를 건너뜀) | 332바이트 차단 |
| **4b** cap=1 | `state_transition` | **1** | **`allow_block_cap_reached`** | `[]` (진단 없음 — `evidence.block_cap: 1`, `evidence.prior_block_count: 7`) | 키 없음 / `null` | **`1`** | **0바이트(차단 해제)** |
| **4c** cap=99 (대조군) | `state_transition` | **1** | **`block_continue`** | `[]` | 키 없음 / `null` | **`99`** | 332바이트 차단 |

### 3-1. `evidence.fingerprint`가 어디서도 생기지 않는 이유 (실측 + 코드 대조)

`evidence`에 `fingerprint` 키가 붙는 조건은 `current_fingerprint is not None`이고(`stop_evaluator.py:196-198`), `current_fingerprint`는 `show_json is not None`일 때만 계산된다. 그런데 공개 진입점은

```
stop_evaluator.evaluate(payload, project_root=project_root)   # stop_hook.py:51
```

로 호출해 **`show_json`·`now`·`env`를 한 번도 넘기지 않는다.** 따라서 실 운영 경로에서:

- `evidence.fingerprint`는 **구조적으로 절대 생기지 않는다** — 9회 실측 전건 "키 없음".
- receipt의 `fingerprint`는 **영구히 `null`** — 기준선 `null`에서 바뀌지 않았고, 바뀔 수 있는 경로가 없다.
- receipt의 `decided_at`도 `now=None`이 그대로 저장되어 **영구히 `null`**이다.
- `allow_no_progress_same_fingerprint`는 `current_fingerprint is not None`을 선행 조건으로 갖는다(`stop_evaluator.py:218`) → **도달 불가능한 분기**다. 경로 2가 이를 실증한다.
- `_state_view_transition`/`_state_view_next_action`(`stop_evaluator.py:86-102`)과 `fingerprint.compute`의 전체 정규화 로직도 같은 이유로 **공개 hook 경로에서 사용되지 않는다.**

### 3-2. `stop_hook_block_cap(env)` 반환값 전수 (순수 함수 직접 호출)

`claude_adapter.stop_hook_block_cap`은 env만 읽는 순수 함수라 evaluator 주입이 아니다(C-4 무관).

| env 상태 | 반환 |
|---|---|
| 키 부재(미설정) | `None` |
| 빈 문자열 | `None` |
| `"0"` | `0` |
| `"1"` | `1` |
| `"99"` | `99` |
| `"abc"` | `None` |
| `" 2 "` (공백 포함) | `2` |
| `env=None` | `None` |

**현재 환경의 실제 값은 `None`이다.** `~/.claude/settings.json`에 `env` 블록이 아예 없고(`env: null`), settings와 워크트리 `.claude/` 어디에도 `STOP_HOOK_BLOCK_CAP` 문자열이 **0건**이다. 즉 **운영 기본 상태는 "상한 검사 생략"**이며, `allow_block_cap_reached`는 누군가 이 변수를 명시적으로 설정하기 전까지 절대 발화하지 않는다. 경로 4a가 이를 실증하고, 4b가 "설정하면 즉시 동작한다(로직 자체는 정상)"를 실증한다.

> 주의: `"0"` → `0`이므로 cap=0은 `prior_block_count >= 0`이 항상 참이 되어 **Stop 가드를 상시 무력화**한다. `None`(검사 생략)과 `0`(항상 상한 도달)이 의미가 정반대인데 둘 다 "설정 안 한 것처럼 보이는 값"에서 나올 수 있다 — 후속 경계 항목으로 남긴다.

---

## 4. `block_count` 원장 — 기준선 3 → 최종 9

매 호출 전후를 실독했다. **경로 1·1b·3계열은 실물 receipt를 전혀 움직이지 않았다**(다른 session_id 또는 다른 project_root로 receipt가 분리되기 때문).

| # | 실행 | 대상 receipt | 전 | 후 | `decision_kind` |
|---|---|---|---|---|---|
| 0 | (기준선) | 실물 `4e1a2aa2…json` | — | **3** | `block_continue` |
| 1 | 경로 1 hook | 실물 | 3 | **3** (불변) | — |
| 2 | 경로 1 dump | 실물 | 3 | **3** (불변) | — |
| — | 경로 1 부수효과 | **신규** `9f3c0b21-…0001.json` | 부재 | `0` | `allow_inactive` |
| 3 | 경로 3a·3b·3c hook+dump | 실물 | 3 | **3** (불변) | — |
| — | 경로 3 부수효과 | 임시 트리 내부 receipt(스크래치패드) | 부재 | 3a·3b `0` / 3c `2` | — |
| — | 경로 1b 부수효과 | 임시 트리 내부 receipt(스크래치패드) | 부재 | `0` | `allow_inactive` |
| 4 | **경로 2 hook** | 실물 | **3** | **4** | `block_continue` |
| 5 | 경로 2 dump | 실물 | 4 | **5** | `block_continue` |
| 6 | **경로 4a hook** | 실물 | **5** | 6 | `block_continue` |
| 7 | 경로 4a dump | 실물 | 6 | **7** | `block_continue` |
| 8 | **경로 4b hook** (cap=1) | 실물 | **7** | **7** (불변) | **`allow_block_cap_reached`** |
| 9 | 경로 4b dump (cap=1) | 실물 | 7 | **7** (불변) | `allow_block_cap_reached` |
| 10 | **경로 4c hook** (cap=99) | 실물 | **7** | 8 | `block_continue` |
| 11 | 경로 4c dump (cap=99) | 실물 | 8 | **9** | `block_continue` |

**최종 실물 receipt**:

```
{"block_count": 9, "decided_at": null, "decision_kind": "block_continue", "fingerprint": null, "session_id": "4e1a2aa2-1800-43e6-af3c-60b86a27b237"}
```

- `fingerprint`·`decided_at`은 **`null`에서 끝까지 바뀌지 않았다** (기준선 그대로).
- 증가분 6건(3→9)은 전부 `block_continue` 판정 6회(경로 2·4a·4c 각 hook 1 + dump 1)에서 발생했다. `allow_*` 판정은 `block_count`를 올리지 않는다(`stop_evaluator.py:281` — `block_count=None`이면 prior 유지).
- **새로 생긴 실물 파일 1건**: `<worktree>/.opal/run/.runtime/stop-guard/9f3c0b21-0000-4aaa-bbbb-000000000001.json`. 경로 1의 합성 세션 ID로 만들어진 receipt다. 태스크 999 경계 안이고 그 세션 ID는 재현되지 않으므로 무해하나, **후속 Work item이 receipt 디렉터리를 열거할 때 실세션이 아님을 알아야 한다.**

---

## 5. D-M 2항 판정 — 경로별 확정

판정 기준(PLAN D-M, 실행 전 고정):
- **(i)** 수정 범위가 PLAN `변경 대상`에 **이미 있는 파일** 안에 닫히는가
- **(ii)** 새 계약 결정을 요구하는가

PLAN 현재 `변경 대상` 전체 = `session_start_hook.py` · `test_session_start.py` · `.opal/brain/pages/entity/ownership-tool.md` · `opal/tools/ownership-tool/README.md` **4개뿐**.

| 경로 | 확정된 갭 | 수정이 필요한 파일 | (i) 변경 대상 안? | (ii) 새 계약 결정? | **D-M 판정** |
|---|---|---|---|---|---|
| **1** 세션 재시작 직후 | 재시작 세션이 **Stop을 그냥 통과**한다. 태스크는 `in_progress`인데 lease가 이전 세션 소유라 `foreign_session_owned` → `forced_count: 0` → `allow_inactive`. 세션 상속이 성립하지 않는다 | `lease.py`(claim 이전/승격) 또는 `resolver.py`(분류) | **아니오** — 둘 다 목록 밖 | **예** — "만료 전 타 세션 lease를 언제 이전하는가"는 새 소유권 계약 | **후속 경계** |
| **1b** 재시작 + SessionStart 재claim | SessionStart가 재claim해도 `claim_source=session_start` → D-21이 강제 후보에서 제외 → `passive_ownership` + `allow_inactive`. **재claim 성공이 곧 Stop 가드 복구가 아니다** | `stop_evaluator.py:24-27`(D-21 제외 규칙) 또는 `lease.py`(claim_source 승격) | **아니오** | **예** — D-21 자체의 재협상. `session_start` claim을 언제 `state_transition`으로 승격하는가는 신규 결정 | **후속 경계** |
| **2** 상태 전이 없는 재개 | 진행이 없어도 **무제한 재차단**된다. `allow_no_progress_same_fingerprint`가 `show_json` 부재로 **도달 불가 분기**이기 때문 (`block_count` 3→5 실측) | `stop_hook.py`(state view 획득) + `stop_evaluator.py` | **아니오** | **예** — "Stop hook이 매번 state를 읽는가 / 어떤 표면으로 / 실패 시 fail-open인가"는 신규 계약 | **후속 경계** |
| **3** state view 부재 | `state.json`을 못 읽으면 후보가 **조용히 사라지거나**(3a, `candidate_count: 0`) **비강제 `invalid_state`**(3b)가 되어 Stop이 통과한다. 대조군 3c는 같은 트리에서 `block_continue`이므로 원인이 state view 하나로 격리된다 | `resolver.py:240-254` · `stop_evaluator.py` | **아니오** | **예** — "읽을 수 없는 state를 fail-open으로 둘 것인가 `defer_to_pm`으로 올릴 것인가"는 신규 안전 계약 | **후속 경계** |
| **4** block cap 미설정 | 운영 기본값이 `None`(검사 생략)이라 `allow_block_cap_reached`가 **영원히 발화하지 않는다**. 로직은 정상(4b에서 cap=1로 즉시 발화). 결손은 **설정 부재**이며, `"0"`과 미설정의 의미가 정반대로 갈리는 위험도 확인됨 | `~/.opal` 배포 settings(= C-1 금지) 또는 `claude_adapter.py`에 기본 상한 도입 | **아니오** — 목록 밖이고, 한쪽은 C-1이 금지 | **예** — `claude_adapter.py:31` 주석이 "자체 기본 상한을 두지 않는다(H-7)"로 **이미 명시적으로 결정**해 둔 사항이라, 상한 도입은 H-7 번복이라는 신규 결정 | **후속 경계** |

**확정: 4경로(및 보조 1b) 전건 `후속 경계`. 이번 태스크에서 구현할 항목은 0건이다.**

- D-M은 (i)·(ii)를 **모두** 만족할 때만 `이번 구현`을 허용한다. 5건 모두 (i)·(ii) **양쪽에서 불충족**이므로 단일 기준으로도, 양 기준으로도 결론이 같다.
- 재협상하지 않았고 `변경 대상` 확대를 제안하지 않았다 — **C-2 준수**(`claim`·`state view`·`block cap`·`transcript` 정책 어느 것도 변경하지 않았다).
- 경로 4는 "구현 결함"이 아니라 **설정 결손**이라는 점에서 나머지와 성격이 다르다. 후속 경계로 닫되, 구현 없이 배포 설정 1줄로 해소 가능한 유일한 항목임을 후속 태스크가 알아야 한다(단, `~/.opal` 쓰기는 C-1이 금지하므로 이 태스크에서는 불가).

### 5-1. 갭 간 인과 구조 (후속 태스크 설계용)

경로 2·3·4는 **독립 결함 3건이 아니라 한 뿌리의 3면**이다. `stop_hook.py:51`이 `show_json`을 넘기지 않는다는 사실 하나가:

- `fingerprint` 계산을 통째로 죽이고(→ 경로 2의 무제한 재차단),
- state 해석을 resolver의 파일 읽기에만 의존하게 만들며(→ 경로 3의 조용한 통과),
- 남은 유일한 탈출구를 `block_cap` env 하나로 몰아넣는다(→ 경로 4가 미설정이면 탈출구가 0개).

**현재 운영 상태에서 `block_continue` 루프를 끊는 장치는 사실상 존재하지 않는다.** 경로 2가 실측으로 보인 3→5 증가는 상한 없이 계속된다. 후속 태스크는 이 3건을 한 계약 결정(“Stop 가드가 진행 여부를 무엇으로 판정하는가”)으로 묶어 다루는 편이 낫다.

---

## 6. S-5 / AC-5 충족 대조

| S-5 기대 항목 | 실측 | 판정 |
|---|---|---|
| 4경로를 실제 봉투로 실측 | 4경로 + 대조군 3건(1b·3c·4c) = 9회 실행, 전건 hook stdout·evaluator 덤프 보존 | **충족** |
| 각 경로 `claim_source` 기록 | §3 표 1열 | **충족** |
| 각 경로 `forced_count` 기록 | §3 표 2열 | **충족** |
| 각 경로 `decision_kind` 기록 | §3 표 3열 | **충족** |
| 각 경로 `diagnostics` 기록 (`passive_ownership`·`allow_block_cap_reached`·`allow_no_progress_same_fingerprint` 포함) | §3 표 4열 — `passive_ownership` 1b에서 **발화 실측**, `allow_block_cap_reached` 4b에서 **발화 실측**, `allow_no_progress_same_fingerprint`는 **도달 불가**임을 코드·실측 양쪽으로 확정(§3-1) | **충족** |
| 각 경로 `fingerprint` 유무 | §3 표 5열 + §3-1 — 전건 부재, receipt `null` 불변, 구조적 원인 확정 | **충족** |
| 각 경로 `stop_hook_block_cap` 반환 | §3 표 6열 + §3-2 전수표 | **충족** |
| 경로마다 `이번 구현`/`후속 경계` 확정 (D-M 2항 근거 동반) | §5 — 5건 전건 `후속 경계`, (i)·(ii) 각각 근거 명시 | **충족** |

**AC-5 판정: 충족.** 4경로가 실측됐고 `claim`·`state view`·`block cap` 구현 범위가 증거와 함께 **"이번 태스크 구현 없음 / 전건 후속 경계"로 확정**됐다. D-M이 정의한 AC-5의 완료 기준은 "구현"이 아니라 "범위 확정"이므로, 구현 0건은 미달이 아니라 확정 결과다.

**측정 불가 경로: 없다.** 9회 전건 실행됐고 지어낸 값은 없다.

---

## 7. 기준선 이동 인계 (후속 Work item용)

| 항목 | W-4 이전 | **W-4 이후 (새 기준선)** | 비고 |
|---|---|---|---|
| stop-guard receipt `block_count` | 3 | **9** | 경로 2·4a·4c의 `block_continue` 6회. 경로 1·1b·3은 0 기여 |
| receipt `decision_kind` | `block_continue` | **`block_continue`** | 마지막 실행(4c)이 차단이라 종류는 동일 |
| receipt `fingerprint` | `null` | **`null`** (불변) | 공개 hook 경로에서 변할 수 없음이 §3-1로 확정 |
| receipt `decided_at` | `null` | **`null`** (불변) | `now=None` 고정 |
| `run/.runtime/owner.json` 판정 필드 | `claim_source=state_transition`, `owner_session_id=4e1a2aa2-…b237`, `generation=1`, `status=active` | **전건 불변** | 이 프로브는 읽기만 했다 |
| `run/.runtime/owner.json` heartbeat | `heartbeat_at=18:38:01` / `lease_expires_at=22:38:01` | `heartbeat_at=18:43:25` / `lease_expires_at=22:43:25` | **이 프로브의 쓰기가 아니다** — 세션 heartbeat hook이 배경에서 갱신한 값이다. 판정 필드는 건드리지 않았고, 이 프로브는 `owner.json`에 어떤 쓰기도 하지 않았다 |
| 실물 `state.json` | `execute.implement` `step 4/11`, `in_progress` | **불변** | **읽지 않았고 쓰지 않았다** |
| run-log 최신 `sequence` | 13 | **13 (불변)** | run-log에 기록하지 않음 |
| 허브 registry `owner_session_id` | `null` | **`null` (불변)** | 읽기만 함 |
| stop-guard 디렉터리 파일 수 | 1 (+`.lock`) | **2** — `9f3c0b21-0000-4aaa-bbbb-000000000001.json` 추가 | 경로 1의 합성 세션 receipt. 실세션 아님 |

**W-7(S-6 · transcript)이 전제할 것**

1. `block_count`는 **9에서 출발한다** (3이 아니다).
2. `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`은 **현재 미설정**이며, 이 프로브는 설정을 남기지 않았다(모든 cap 설정은 `env VAR=… <cmd>` 형태의 단일 프로세스 한정이었다). 후속 실행에서 cap은 다시 `None`이다.
3. 마지막 실물 판정은 `block_continue`이므로, 다음 Stop 봉투도 상태가 그대로면 차단된다.
4. stop-guard 디렉터리에 **실세션이 아닌 receipt 1건**이 섞여 있다.
5. §3-1이 확정한 "공개 hook은 `show_json`·`now`·`env`를 넘기지 않는다"는 W-7의 transcript 검토에도 직접 적용된다 — 현재 집행 경로(`stop_evaluator.evaluate`)에 **봉투 5필드 외의 어떤 입력도 들어가지 않는다**. transcript를 입력으로 추가하지 않았음을 보이는 근거로 쓸 수 있다.

---

## 8. 부수효과·준수 확인

- **소스·테스트 파일 무수정.** `git status --porcelain` 결과가 착수 시점과 **동일**: `M session_start_hook.py` · `M test_session_start.py`(둘 다 W-6 산출물, 이 프로브는 **읽기만** 함) + `?? tasks/999-…/`.
- **커밋하지 않았다.** 파이프라인 행을 전진시키지 않았다(`advance` 미실행).
- **실물 `state.json`·`owner.json`·허브 registry 무변경.**
- **`~/.opal/` 무쓰기, 재배포 없음.**
- **`test-tool`을 호출하지 않았다** — 이번 디스패치의 실행 capability에 주입되지 않았고(기본 도구 · `~/.opal/.venv/bin/python` · `state-tool show`만 주입), 하네스 Guard가 산출물을 `PROBE-GAPS.md` 1건으로 한정했다. `test-scenario.json`의 S-5 결과 기록은 PM이 소유한다.
- **`TEST-SCENARIO.md`(`template: sdlc-v2`) 무수정** — 불변 명세로 취급했다.

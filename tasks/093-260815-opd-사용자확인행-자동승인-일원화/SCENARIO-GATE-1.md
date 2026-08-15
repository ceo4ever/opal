# SCENARIO GATE 1 — scenario-rubric 판정 보고서

> 실행 일시: 2026-08-15T21:00:00+09:00
> phase: `scenario-rubric` | iteration: 1
> scenario_source: `tasks/093-260815-opd-사용자확인행-자동승인-일원화/TEST-SCENARIO.md`
> 판정 주체: opal-evaluator-agent (판단축 ①⑤⑥ 전용)
> 기준 SSOT: `~/.opal/references/harness/scenario-gate.md` §2(6축·판정 주체 분리) / §5-1(종료조건)
> CONTRACT.md 부재 — `scenario-rubric`은 CONTRACT 루브릭절 병합 대상이 아니므로 판정에 영향 없음 (AGENT.md Phase 2 단서)

## 0. 판정 범위

- 본 보고서는 §2 **①목표 달성 / ⑤채택·잔존 / ⑥경계·부정** 3축만 채점한다.
- ②요구 커버 / ③기능 커버 / ④리스크 커버는 test-tool `scenario-coverage-check` 결정론 판정(exit 0) 소관이며 재채점하지 않는다.
- 척도 0~2. 수렴 임계: 각 축 ≥1점(0점 축 없음) AND 평균 ≥1.5점.

## 1. 판단축별 판정

| 축 | 점수 | 판정 |
|----|------|------|
| ① 목표 달성 | **2** | 목표를 사용자·운영 계층에서 직접 관통 검증 |
| ⑤ 채택/잔존 | **2** | 교체형 F-1의 구형 잔존 0 · 신형 채택 양측 모두 검증 |
| ⑥ 경계/부정 | **2** | 경계·부정 경로가 파일 실측 강도로 다수 존재 |

**평균 2.00 / verdict: pass**

---

### ① 목표 달성 — 2점

**목표 문장**(TASK.md §작업 목표·§명확화 결과): "사용자 확인 행의 상태 전이를 `pending → done/auto` 또는 `pending → done/user` 단일 축으로 일원화하고, 자동 승인을 **PM 호출이 아닌 도구 훅으로 집행**한다."

**2점 근거 — 무엇이 있어서**

1. **S-1(L2)이 플래그→훅→도구→state 파일 전 구간을 실제로 관통한다.** 실 `opal/skills/opal-pilot-dev/references/pipeline.json`으로 `init --mode agentic`(플래그) → PM 실제 순서대로 `advance`/`mark` 연쇄(도구, worktree `run.sh` subprocess 실호출) → state.json **재로드**(파일 실측)로 `*.user_confirm` 4행이 `done/owner=auto/timestamp≠None`임을 확인한다. 반환값만 보는 검증이 아니다(§3 L2 서두 "메모리상 반환값만 보는 검증은 금지한다").
2. **070 동형 공백(훅 미접합인데 전건 PASS)이 구조적으로 차단된다.** S-1 조건에 "**어느 호출에도 `--auto-pass`를 전달하지 않는다**"가 명시되어 있고, 이것이 선언이 아니라 실제 강도로 작동한다 — `--auto-pass` 없이 사용자 확인 행이 `pending`이면 `check_stage_transition_guard`(PLAN §1.3 각주 / `state_tool.py:634-679`)가 다음 단계 진입을 차단하므로, 훅이 배선되지 않으면 S-1은 반드시 `stage_transition_violation`으로 실패한다. S-1 "검증 강도" 행이 이를 [MUST]로 못 박았다. **즉 S-1은 "관통을 주장하는 선언"이 아니라, 실패 조건이 실재하는 시나리오다.**
3. **PM 호출 배제라는 목표의 핵심 반전이 별도로도 검증된다** — S-5(L1)가 "ANALYSIS 행을 `pending`으로 둔 채 PLAN 첫 행 advance, `--auto-pass` 미전달 → `done/auto/timestamp≠None`"으로 F-2 AC를 직접 대응하고, note 접두를 `auto-approved on … entry`로 구분해 훅 승인분과 PM 명시 호출분의 혼동을 배제한다.
4. **운영 계층 확인이 L3로 별도 존재한다** — S-23(SUPERVISOR)이 전역 배포 후 실파이프라인에서 ①`pending/PM` 초기화 ②다음 단계 진입 시 `done/auto` ③CLOSE는 여전히 캡틴 승인을 캡틴 수동 확인으로 요구한다. 자동화 불가 사유(install 단일 타겟)도 명시되어 면제가 아니라 계층 배치임이 확인된다.

**2점이 아니었다면 무엇이 없어서인가(잔여 리스크, 비차단)**

- S-1의 명령 연쇄가 "PM이 실제 파이프라인에서 하는 것과 동일한 순서"로만 서술되어 **정확한 호출 시퀀스가 EXECUTE 워커 재량으로 남아 있다.** 워커가 시퀀스를 짧게 잡으면 관통 폭이 줄 수 있다(단, 훅 미배선 시 실패 성질 자체는 유지되므로 070형 공백은 남지 않는다).
- S-1 기대결과 ④ "각 승인의 `timestamp`가 해당 단계 진입 시각과 일치(초기화 시각이 아님)"는 **비교 방법·허용오차가 미규정**이다. "초기화 시각과 다름" 정도의 약한 assert로 구현될 여지가 있다.
- 관통 시나리오가 **agentic 단일 모드**다. semi-agentic의 "EXECUTE 이후 자동 승인"(S-13)은 L1에만 있어, semi-agentic 실파이프라인 관통은 S-23(수동)에 의존한다.

---

### ⑤ 채택/잔존 — 2점

F-1은 TASK.md가 명시적으로 "(교체형)"으로 라벨한 요구사항이며, AC가 (a)구형 잔존 0 / (b)신형 채택으로 이미 분리되어 있다. 이 두 면이 **서로 다른 시나리오로 각각 존재**한다.

**2점 근거 — 무엇이 있어서**

| 면 | 시나리오 | 검증 내용 |
|----|---------|----------|
| 구형 잔존 0 (정적) | **S-2** | `state_tool.py`에서 `agentic auto-na at init` 문자열 grep **0건**. 부수적으로 빌더 3곳의 `mode` 시그니처 존치까지 확인(Surgical Change 경계) |
| 구형 잔존 0 (동적) | **S-1 ③** | 신규 생성 state.json 재로드 시 `na` 상태 행 **0건** — 정적 grep이 아닌 산출 데이터 실측으로 이중 확인 |
| 신형 채택 (초기화) | **S-3** | 3모드 init 결과 `rows[]` 전 필드 diff 0 + `*.user_confirm` 5행이 `status=pending / status_label=⬜ / owner=PM / timestamp=None / note=None`. TEST-SCENARIO 자체가 "F-1 AC(b)의 유일한 직접 검증"으로 표시 |
| 신형 채택 (경로 전수) | **S-4** | `--rows-spec` / `--rows-from *.md` / `--rows-from *.json` 3 빌더 경로 전건 `pending/⬜/PM`. "어느 한 경로만 고쳐도 나머지에서 실패"라는 판별력 조건 명시 |
| 신형 채택 (훅 발동) | **S-5, S-1** | 신형 계약의 나머지 절반 — `pending` 초기화가 실제로 자동 승인으로 귀결됨을 훅 경로로 검증 |
| 하위호환(구형 데이터 존치) | **S-17, S-18** | 092 실파일 복사본 `validate`/`advance`/`mark` 3종 exit 0, CLOSE `done/auto` 보유 파일 violations 0 |

즉 **"구형 제거만 검증하고 신형 채택은 비어 있음"이라는 070형 결함은 존재하지 않는다.** 초기화 신형(pending/PM)과 승인 신형(훅 자동 승인)이 각각 독립 시나리오를 갖고, S-1이 둘을 한 흐름으로 결합한다.

**2점이 아니었다면 무엇이 없어서인가(잔여 리스크, 비차단)**

- **F-3의 구조적 채택 검증이 없다.** TASK.md F-3 AC는 "판정 로직이 **단일 함수에 모이고**, 기존 지점이 그 함수를 호출한다"를 요구하고 PLAN이 이를 TS-023(`MODE_BOUNDARY_STAGES` 참조 지점이 판정 함수 내부 1곳뿐임을 grep)으로 설계했으나, TEST-SCENARIO §3에 대응 시나리오가 없다. S-12~S-14는 **행동 불변**만 검증하므로, 판정 로직을 3곳에 복붙한 채로도 전건 PASS한다(F-1에 대해 S-2가 수행한 "구형 잔존 grep"의 F-3판 부재). 다만 본 축의 SSOT 정의상 교체형 목표는 F-1이며 F-1은 완전 검증되므로 감점 사유로는 삼지 않는다.
- PLAN TS-005가 설계한 "pending 초기화 + 훅 승인 한 시나리오 연속 검증"은 S-1이 사실상 흡수했으나, S-1은 L2 subprocess라 **초기 상태(`timestamp=None`) 시점 assert가 명시되지 않았다** — S-3에 위임되어 있다.

---

### ⑥ 경계/부정 — 2점

**2점 근거 — 무엇이 있어서**

| 부정 경로 | 시나리오 | 기대 결과의 강도 |
|----------|---------|----------------|
| CLOSE 우회(훅에 의한 게이트 무력화, H-1/P0) | **S-6**(L2) | exit 1 **+ state.json 파일 재로드 시 해당 행이 여전히 `pending`** + 이후 `--owner user` mark로 정상 통과까지 확인 — 반환값이 아닌 파일 실측 |
| CLOSE auto-pass 직접 시도 | **S-7** | agentic·semi-agentic 양 모드에서 `agentic_close_gate_requires_user` — **에러 코드 문자열까지 대조**(exit code 비교 금지) |
| 워커 권한 우회(H-2/P0) | **S-8**(L2) | `stage_transition_violation` + 앞 단계 행 `pending` 유지를 파일 재로드로 확인 |
| 워커 경로 부작용 0 | **S-9**(L2) | state.json **바이트 완전 동일**(`updated_at` 포함) — 가장 강한 형태의 무변경 assert |
| 후속 가드 실패 시 미저장(H-8) | **S-10**(L2) | `gate_artifact_missing` 후 **저장된 파일**의 앞 단계 행이 `pending` — 메모리 mutate가 파일로 새지 않음을 실측 |
| 실패 응답 오염 | **S-11** | 실패 JSON에 `auto_approved` 부재/빈 배열 + `save_state_json` 미호출 |
| semi-agentic 경계 거부 | **S-12** | `user_confirmation_required` + 응답에 `row_id`·`stage`·`reason=="semi_agentic_pre_execute"`·`required_action` **필드 단위 대조**(F-4 AC 대응) |
| interactive 거부 | **S-14(a)** (§2.2 데이터 흐름 행) | 훅 경로 진입 시 `user_confirmation_required` 거부 / (b) PM 직접 `mark --auto-pass`는 exit 0 후 `validate`가 `auto_pass_in_interactive_mode` 1건 — DEC-A 경로 분리까지 검증 |
| 경계 이동 전수(H-3/H-4) | **S-14** | PLAN §3.3.2 표 A(B-1~B-9)+표 B(V-1~V-9) **18셀 파라미터화**. B-7 `close_gate_violation` vs B-8·B-9 `agentic_close_gate_requires_user` 코드 차이 대조, V-8·V-9 `violations_count == 0`(H-4 핵심 셀) |
| 멱등 재호출 | **S-16** | 2회차 `ok:true` + note 문자열 불변 + **대조군 3종**(`owner=user` done / `--force` / `--action-step`)이 no-op에 삼켜지지 않음까지 — 과잉 no-op(오통과) 방향의 부정 검증 |
| 문서 회귀(H-9) | **S-21** | CLOSE 첫 행 거부 지시 약 25지점 grep 스냅샷 전후 **완전 동일** |

부정 경로가 정상 경로의 부속이 아니라 **P0 리스크(H-1·H-2)에 1:2로 대응**하며, L2 시나리오 6건 중 4건(S-6·S-8·S-9·S-10)이 부정 경로 파일 실측이다. §3 L2 서두의 "메모리상 반환값만 보는 검증은 금지한다"가 이 강도를 규약으로 고정한다.

**2점이 아니었다면 무엇이 없어서인가(잔여 리스크, 비차단)**

- **S-14의 §2.2 서술과 §3 본문이 불일치한다.** §2.2 데이터 흐름 표의 S-14는 "interactive 파이프라인 (a)훅 경로 진입 / (b)PM 직접 mark --auto-pass"이나, §3 본문 S-14는 "모드×단계 18셀 경계 불변 회귀표"만 서술하고 **interactive 훅 경로 거부(PLAN TS-031)를 언급하지 않는다.** §4 매핑 표는 F-4 AC를 "S-12, S-14(b)"에 연결하는데, TASK.md F-4 AC의 문자 그대로의 요구는 "**interactive 모드에서 F-2 훅이 발동하면** 자동 마킹하지 않고 전용 에러 + `row_id`"이므로 이는 S-14**(a)**에 해당한다. 구현자가 §3 본문만 읽으면 interactive 훅 거부 케이스가 누락될 수 있다.
- **PLAN TS-016(`auto_approved` 성공 응답 필드) 대응 시나리오가 긍정 방향에 없다.** S-11이 실패 경로의 부재만 확인하므로, 성공 시 이 필드가 승인된 `row_id`를 담는지는 미검증이다.
- S-12는 semi-agentic만 `reason` 필드를 대조하고, `close_requires_user` 사유의 페이로드(PLAN §3.4.2 계약 표)를 확인하는 시나리오는 없다(S-6·S-7은 CLOSE를 기존 에러 코드로만 확인).

---

## 2. 결과 계약

```json
{"scores": {"goal": 2, "adoption": 2, "boundary": 2}, "average": 2.0, "gaps": [], "verdict": "pass"}
```

- 세 축 모두 ≥1점(0점 축 없음), 평균 2.00 ≥ 1.5 → **수렴(PASS)** (`scenario-gate.md` §5-1).
- `gaps[]`는 SSOT 정의상 **<1점 축**에 대해 반환하므로 비어 있다. 위 §1의 "잔여 리스크"는 차단 사유가 아닌 **권고**이며, 아래 §3에 반영 권고로 분리 기재한다.

## 3. 반영 권고 (비차단 — PM 재량)

| # | 대상 | 권고 |
|---|------|------|
| A-1 | S-14 | §3 본문에 §2.2가 이미 규정한 **(a) interactive 훅 경로 → `user_confirmation_required` 거부**를 명시 추가(PLAN TS-031). 현재 §3 본문은 18셀 회귀표만 서술해 F-4 AC의 interactive 훅 케이스가 누락될 여지가 있다 |
| A-2 | F-3 | PLAN TS-023(`MODE_BOUNDARY_STAGES` 참조 지점 단일화 grep) 대응 시나리오 신설 검토 — 현재 시나리오 집합은 F-3의 **행동 불변**만 검증하며 **구조적 단일화**는 미검증이다 |
| A-3 | S-1 | 기대결과 ④ timestamp 비교의 판별 기준(초기화 시각 대비 차이 / 진입 명령 전후 시각 범위)을 명문화 |
| A-4 | F-2 관측 | PLAN TS-016(성공 응답 `auto_approved` 배열이 승인 row_id를 담음) 대응 시나리오 추가 검토 |

## 4. 판정 주체 경계 확인

- 본 보고서는 `scenario-gate.md` §2 ①⑤⑥만 채점했다. ②③④(요구·기능·리스크 매핑 커버리지)는 test-tool `scenario-coverage-check` 결정론 판정 소관으로, 본 에이전트가 대신 판정하지 않았다.
- 게이트 PASS 성립 요건(§6 tool-gated): `scenario-coverage-check` exit 0 **AND** 본 보고서 verdict pass. 전자는 호출 스킬이 이미 확보했다고 입력에 명시되었다.
- 본 에이전트는 판정만 수행했으며 TEST-SCENARIO.md를 포함한 어떤 산출물도 수정하지 않았다(생성자≠평가자).

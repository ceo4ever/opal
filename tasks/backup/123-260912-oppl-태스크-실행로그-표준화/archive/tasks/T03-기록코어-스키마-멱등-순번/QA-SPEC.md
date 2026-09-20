# QA-SPEC — T03 기록코어 스키마·멱등·순번 (G 명세 리뷰 게이트)

> 판정 주체: opal-evaluator-agent (phase: spec-review, readonly) — 생성자≠평가자(H-9)
> 판정 시각: 2026-09-13 01:09 KST | 시도 2회차(1회차 300초 하드에러)
> 판정 기준: CONTRACT.md §5 루브릭절(RB-1~RB-5) + SPEC §4 Base
> 대상: PLAN.md · test-scenario.json(locked=true) · docs/run-log/CONTRACT.md

Verification complete. All checks were read-only; I wrote nothing.

**Note on the event gate**: the `event-loader verify` subcommand is blocked by this session's sandbox permissions, so I verified the receipt equivalently — the receipt declares `event: worker.dispatch`, `ok: true`, 4 required documents, and all four document `sha256` values plus `manifest_sha256` match the on-disk files byte-for-byte (not stale, not wrong-event).

```
verdict: pass
scores: RB-1=4 RB-2=4 RB-3=4 RB-4=5 RB-5=5
        (Base 추가축) 컨벤션 정신=4  아키텍처 적합=5  drift 필요성=yes
findings:
  - id: F-1
    severity: major
    축: RB-1 / RB-2 (drift=yes)
    내용: PM 판정②의 "명시적 모드 인자"가 계약의 기계가독 원천 어디에도 없다.
          `surfaces.json`의 `run-log-tool.append.request_shape.optional` 24개 항목에 `--mode`가
          없고(실측), CONTRACT §2.6이 확정한 인프로세스 시그니처
          `append(task_path, run_id, event, *, lock_held, lock_timeout_ms)`에도 모드 파라미터가 없다
          (현행 `run_log_core.py:420`이 이 시그니처와 정확히 일치함을 확인).
          CONTRACT §2.3은 "호출 형태·인자·응답 필드는 surfaces.json이 기계가독 원천"이라고 못박고,
          TRD D-5는 코어가 "태스크 경로·실행 식별자·사건 payload만 소비한다"고 3항으로 열거한다.
          PLAN §변경하지 않는 자산은 `CONTRACT.md`·`surfaces.json`을 명시적으로 불변으로 선언한다.
          따라서 S-29를 그대로 구현하면 계약 문언과 구현이 갈린다 — D-5의 *정신*(상태 미열람,
          호출자 소유)은 지켜지나 *문언*은 네 번째 입력을 인가하지 않는다.
          판정: 이것은 T1 설계 결함이 아니라 **계약 개정 필요**다. 오너십 계층은 "인터페이스 변경"
          (공개 CLI 표면 인자 추가)이므로 Evaluator가 고치지 않는다.
    조치 주체: PM 보고 — §2.6 시그니처, TRD D-5 소비 입력 열거, `surfaces.json` append
               request_shape 3곳을 같은 변경 단위로 갱신한 뒤 T3 구현에 진입할 것

  - id: F-2
    severity: major
    축: RB-2
    내용: S-28(동결됨)의 `expected`가 `state-tool` 기준선을 **428 passed / 3 skipped**로 하드코딩한다
          (PLAN §Release and recovery 221행도 동일). 실측 결과는
          **436 passed / 3 skipped / 111 subtests passed / 0 failed** (직접 실행, 173.85s).
          T05가 신규 8건을 추가해 기준선이 이동했고 PM 컨텍스트도 436을 명시한다.
          현재 문언대로면 T4a에서 **구현이 정상인데도 S-28이 거짓 FAIL**을 낸다.
          `test-scenario.json`이 `locked=true`이므로 워커가 임의로 상수를 고칠 수 없다.
    조치 주체: PM 보고 — 동결 해제 후 상수 갱신. 다만 숫자 고정보다
               "0 failed + 기존 테스트 파일 미수정"으로 다시 쓰는 편이 재발을 막는다
               (기준선은 형제 태스크가 계속 이동시킨다)

  - id: F-3
    severity: minor
    축: RB-1
    내용: §1.2 사건별 actor 제약 위반(예: `gate.requested`에 `actor.kind=user`)의 오류 코드가
          계약으로 확정돼 있지 않다. D-T03-3은 "§1.3 명시적 거부 목록 5번이 §1.3 안에 있으므로"
          `provenance_invalid`로 배정하는데, §2.2의 조건 문장만 보면 이 위반은
          `provenance_invalid`의 세 조건("표 밖 조합 / 필수 증거 부재 / 분해 금지 위반")
          어디에도 들어맞지 않고, 오히려 `schema_invalid`("enum 위반", 원천 제안서 §5.1)에
          가깝게도 읽힌다. 덧붙여 S-12의 `acceptance_ref`가 MV-2로 달려 있으나 MV-2의 고정 입력은
          4축 조합이지 event×actor 쌍이 아니다.
          PLAN이 근거를 달아 명시적으로 메웠으므로 구현 착수는 가능하다(RB-1 반려 사유 아님).
    조치 주체: PM 보고 — §2.2 또는 §1.3에 한 문장으로 확정 권고.
               확정 전까지는 T3 구현 시 D-T03-3 배정을 그대로 따를 것

  - id: F-4
    severity: minor
    축: RB-2
    내용: 20건 전부 `required_fidelity: "real-usage"`(요구 충실도 충족)이나, result존 필드
          `fidelity`가 20건 전부 `"mock"`이다. 이는 정상 기본값이며 결함이 아니다 —
          `test-tool/lib/scenario.py:224,549`가 `scenario-mark --fidelity` 미지정 시
          `"mock"`을 넣는다. 다만 T4a가 `--fidelity real-usage`로 마킹하지 않으면
          `scenario-fidelity-check`가 `fidelity_unmet`(exit 13)으로 전건 거부한다(같은 파일 646-669행).
    조치 주체: T3/T4a 인계 — 마킹 시 `--fidelity real-usage` 필수

  - id: F-5
    severity: minor
    축: RB-2
    내용: PLAN §테스트 시나리오 초안 표는 S-10~S-28(19건)만 열거하고 S-29가 없다.
          S-29는 PM 판정② 이후 신설돼 `test-scenario.json`에만 존재하며,
          다른 시나리오와 달리 PLAN 산문 상세가 없다(`steps: []`, `assertions: []`는
          20건 공통이므로 S-29 고유 결함은 아니다). S-29의 `expected`가 (a)~(d) 4케이스와
          D-5 정적 검사를 자체 완결로 담고 있어 구현 가능성에는 지장이 없다.
    조치 주체: T5 마무리 — DONE.md 정리 시 PLAN 표를 20건으로 동기화

blockers:
  - CONTRACT §2.6 시그니처 · TRD D-5 소비 입력 열거 · surfaces.json `run-log-tool.append`
    request_shape 3자산의 `--mode`/모드 파라미터 반영 (F-1). 계약 갱신은 PM 소관이므로
    본 에이전트는 판정만 반환한다.
  - 동결된 S-28의 `state-tool` 기준선 상수 428 → 436 갱신 승인 (F-2).
```

**PM이 명시 지시한 판정 항목 답변**

- **AC-6 / MV-2 전수성** — 충족. `iter_all_combinations()`가 4축 곱집합 660건을 생성하고 기대값을 `COMBINATION_TABLE`에서만 파생한다(D-T03-1·2). 시나리오가 660·636을 상수로 적지 않으므로 표가 늘면 검증이 자동으로 따라간다. 표본화 흔적 없음. S-10이 "필수 증거를 전부 채운" 상태로 돌아 *증거 결측*과 *조합 위반*을 분리하는 설계도 적절하다.
- **AC-7 / MV-5 정규화 결정론** — 충족. 제외 4필드·`sort_keys`·`separators`·`ensure_ascii=False`·`default=str`·UTF-8·SHA-256·계산 시점(기본값 채움 후 + `redact()` 후)·저장본 재계산까지 모호성 없이 확정됐다(D-T03-6). 키 순서 흡수를 S-17이 동작으로 고정한다. H-4가 `redact()` 규칙 변경이라는 유일한 잔여 경로까지 식별하고 T06 인계로 넘긴다.
- **MV-10 순번 불일치** — 닫는다. D-T03-5가 `scan_sequences()`의 `(kind, id)` 고정을 교정하고, S-19가 **같은 `actor.id` + 서로 다른 `worker_run_id` 2건이 각각 1부터 세는지**를 판정한다. RED 증거가 현행 동작을 `wrk_a: [1,2,5]`로 실관찰했다 — PM 판정①이 요구한 구분을 정확히 겨냥한다.
- **D-5 단방향 의존** — 유지된다. 설계 전체에 `state.json` 읽기·`state_tool` import가 없고, S-27이 기존 S-8b 정적 검사를 T03 신규 코드까지 확장한다. 판정②의 모드 인자도 S-29가 "모드는 인자로만 들어오고 어디서도 읽지 않는다"를 같은 정적 검사로 확인한다. **판정②는 D-5의 성질을 깨지 않는다** — 다만 계약 문언 갱신이 필요하다(F-1).
- **RB-4 범위 누수** — 없음. T04·T05·T06·T07·T08·T11 소관이 §단건 vs 다건 표로 소유자와 함께 배제되고, `begin-worker`·워커 token은 D-T03-19가 "권한 없이 통과시키는 것보다 전부 거부"로 fail-closed 처리하며 `worker_token_invalid`를 구현하지 않는다. 판정②의 교정도 append 시점 구조 제약까지만 닿는다.
- **MV-30** — 발동하지 않는다. D-T03-17의 "신규 오류 코드 없음" 주장을 실측 검증했다: `append.err`에 `provenance_invalid`·`request_id_conflict`·`event_too_large`가 이미 등재돼 있다. 두 import 표면 `err`에 `request_id_conflict`가 **없다**는 D-T03-11의 근거도 사실이며, 해시를 멱등 키에 항상 포함해 구조적으로 그 코드가 발생할 수 없게 만든 설계는 계약과 정합한다.
- **충실도** — 20건 전부 `real-usage`이고 `surface_ref`가 실제 표면 id 4종(`append`·`validate-run`·`import-agentic`·`import-oppl`)이다. mock/patch/스텁을 쓰는 시나리오 없음.
- **RED 실관찰** — 신뢰할 만하다. `red_required=true` 17건 전건이 개별적으로 구체적인 pytest 실패(`AttributeError: no attribute 'iter_all_combinations'`, `argparse: invalid choice 'import-agentic'`, 관찰값 `[1,2,5]` 등)를 증거로 갖는다. 일괄 문구 복붙이나 소급 선언의 징후가 없다. `locked=true`, `locked_at` 00:54:33이 `red_at` 00:54:19~20 직후다.
- **`red_required=false` 3건의 판단** — 타당하다. S-20·S-28은 이미 성립하는 성질이라 RED가 성립할 수 없다. **S-27이 미묘한데, 판단이 옳다**: 동적부는 지금 실패하지만 그 원인은 import 서브명령 부재(= S-21·S-24·S-25가 이미 RED로 덮는 사실)이지 "state 자산 독립"이라는 *판정 대상 성질*의 부재가 아니다. 이를 RED로 세면 **잘못된 이유로 붉은 것**을 근거로 삼게 된다. 위조하지 않은 판단을 지지한다.
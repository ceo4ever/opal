---
template: sdlc-v2
---
# PLAN: T03 — 기록 코어 스키마·멱등·순번 (표준 사건의 문지기)

> 입력: [TASK.md](../../TASK.md), [CONTRACT.md](../../../../docs/run-log/CONTRACT.md), [TRD.md](../../../../docs/run-log/TRD.md), [surfaces.json](../../../../docs/run-log/surfaces.json), [T02 PLAN](../T02-워킹-스켈레톤-CLI-관통/PLAN.md)
> 작성: 2026-09-13 00:17 KST

## Approach

T02가 남긴 관통 경로(`init` → `append` → `validate-run`)는 살아 있지만 `append`는 **아직 문지기가 아니다.**
아래 §실측이 보이듯 지금은 PM 대필 조합도, 같은 `request_id`의 3회 재호출도 전부 통과해 새 사건을 만든다.

T03은 `append` 한 지점에 **단건 사건 판정 전부**를 모은다 — 폐쇄형 어휘(§1.1·§1.2), 4축 허용 조합과
출처 증거(§1.3), 요청 식별자 멱등(§5.1), 직렬화 상한(§1.1), 주체별 순번 범위(§1.1). 그 위에
`import-agentic`·`import-oppl` 두 표면을 얹어 원본을 **같은 문을 통과하는 표준 사건**으로 바꾼다.
가져오기가 별도의 느슨한 경로를 갖지 않는 것이 이 설계의 핵심이다 — 두 importer는 정규화만 하고
검증·순번·멱등은 전부 `append()`를 그대로 탄다.

범위 경계는 **단건 vs 다건**으로 긋는다. 한 사건 payload만 보고 판정되는 것은 T03이 집행하고,
여러 사건의 관계(terminal 유일성 MV-4, 게이트 쌍 MV-22, 완료 알림 분해 금지 MV-7, span 합산 MV-15)는
`validate-worker` 소유로 남긴다. 예외는 멱등 판정 하나이며, 이는 AC-7이 T03에 명시 배정한 것이다.

색인·조각 경계(T04), 상태 보관함(T05), `redact()` 본문(T06), 변환기(T07), 게이트 집행(T11),
`begin-worker`·워커 token(범위 밖)은 건드리지 않는다. `state_tool.py`는 한 줄도 열지 않는다.

---

## 실측 (추정 아님)

### M-1. 멱등 미구현 재현 — AC-7이 닫아야 할 지점

```
bash opal/tools/run-log-tool/run.sh init --task /tmp/t03probe/task --run-id run_probe --format json
→ {"ok":true,"data":{"run_id":"run_probe","segment":".../run-log-run_probe-0001.jsonl","created":true}}

같은 --request-id req_same 로 --summary "same payload" 를 2회, 이어서 "DIFFERENT payload" 1회:
#1 → sequence 1, idempotent_hit false
#2 → sequence 2, idempotent_hit false   ← 동일 payload인데 새 사건
#3 → sequence 3, idempotent_hit false   ← 다른 payload인데 request_id_conflict 없음
조각 줄 수: 3
```

동일 payload 재호출이 **기존 사건을 반환하지 않고**, 다른 payload 재사용이 **거부되지 않는다.**
MV-5 두 갈래가 모두 미구현이다.

### M-2. 조합 검증 미구현 재현 — AC-6이 닫아야 할 지점

```
append --actor-kind worker --actor-id w1 --provenance-type direct --recorded-by-kind PM
→ {"ok":true,"data":{... "sequence":4, "actor_sequence":1 ...}}
```

§1.3 **명시적 거부 조합 1번(PM 대필)** 이 통과한다. 현재 `validate_event()`는 §1.1 최상위 키와
§1.2 `event` enum만 본다(`run_log_core.py:363-378`). `provenance`·`actor`의 내용은 전혀 보지 않는다.

### M-3. 조합 공간의 크기 — MV-2 "표 밖 조합 전수"의 실제 규모

| 축 | 값 수 | 값 |
|---|---|---|
| `actor.kind` | 5 | `worker` `PM` `user` `auto` `tool` |
| `provenance.type` | 3 | `direct` `adapter` `import` |
| `provenance.recorded_by.kind` | 4 | `worker` `PM` `adapter` `tool` |
| `provenance.source.kind` | 11 | §1.1.2 enum 10종 + `null` |

전체 **660** 조합, §1.3 표가 허용하는 것 **24**(A1 7 + A2 1 + A3 2 + A4 2 + A5 2 + A6 1 + A7 1 + A8 8),
**거부 대상 636**. 이 수는 표에서 기계적으로 파생되므로 시나리오가 상수를 손으로 적지 않는다.

CLI 실호출 비용 실측: 20회 연속 `append` 1.14초 = **호출당 57 ms**. 거부 경로는 검증에서 끝나
디스크를 읽지 않으므로(아래 §검증 순서) 636건 전수는 **약 36초**로 예상한다.

### M-4. legacy 원본(`AGENTIC-LOG.md`) — 한 형식이 아니다

18개 파일에서 4가지 구조를 확인했다.

| 변종 | 구조 | 파일 | 시각 |
|---|---|---|---|
| V1 | `## 대행 일지` + 6열 표 `# / 시점 / 단계 / 카테고리 / 내용 / 결과` | 11건 (104·105·108·112·113·114·115·118·119·120·123) | `2026-09-12 14:49` (KST, 시간대 없음) |
| V2 | `## PM 자율 판단 로그` + 4열 표 `# / 시점 / 판단 / 근거` | 1건 (101) | **시각 아님** — `"TEST-SCENARIO 게이트 후"` 같은 서술 |
| V3 | `## [DECISION] …` `## [GATE] …` 자유 서술 절 | 3건 (106·107·109) | 절 제목·본문에 산발, 없는 절 다수 |
| V4 | 표 없는 불릿 목록 | 2건 (116·117) | 없음 |

V1 앞에는 `## 요약` + 2열 표(`항목 / 건수`)가 거의 항상 붙는다 — **사건 표가 아니다.**

헤더 행 기준 파싱 실측: V1 6열 데이터 행 **671건**, 카테고리는 7종으로 닫힌다
(`DECISION` 218 / `GATE` 183 / `ERROR` 134 / `FIX` 91 / `IMPROVE` 26 / `ESCALATION` 10 / `IMPROVEMENT` 9).
시점이 `YYYY-MM-DD HH:mm`을 만족하지 않는 행은 **9건**뿐이며 그 값은 `2026-09-03`(날짜만) 4건과
`2026-09-12 20:0x`(자리표시자) 5건이다.

> 위치 기반 정규식(열 수를 보지 않는 `^\|\s*\d+\s*\|…`)으로 세면 691건이 잡히고 카테고리가
> 20종으로 흩어진다 — V2의 `근거` 열이 카테고리 자리로 밀려 들어오기 때문이다. **헤더 행으로
> 표를 식별하지 않으면 정규화가 조용히 오염된다.** 이것이 아래 D-T03-8의 근거다.

### M-5. oppl 원본(`.oppl-run/`) — 이원 구조 실측

`tasks/123-*/tasks/T01|T02|T03-*/.oppl-run/` 3곳에서 확인했다.

| 자산 | 형식 | 실측 |
|---|---|---|
| `<phase>.events.jsonl` | 비동기 축 stream JSONL | T02 `t3.events.jsonl` 2.75 MB. `type` 분포(t1) = `system` 153 / `assistant` 65 / `user` 41 / `rate_limit_event` 7 / `tool_progress` 2 / **`result` 1** |
| `<phase>.result.json` | 동기 축 단일 결과 파일 | **stream의 `result` 레코드와 키 집합이 완전히 동일**(`type`·`subtype`·`is_error`·`duration_ms`·`num_turns`·`session_id`·`uuid`·`usage`…) |
| `<phase>.exitcode` | 완료 마커 | 2바이트(`0\n`) |
| `journal.md` | 운행 일지 4열 표 `시각 / 단계 / 이벤트 / 근거` | 38행 전부 `시각`이 RFC 3339 `…Z`. `이벤트` 값은 **4종으로 닫힘** — `end` 15 / `start` 13 / `gate-verdict` 7 / `retry` 3 |
| `<phase>.prompt.txt` | 워커 프롬프트 원문 | 최대 55 KB. **수집 대상 아님**(AC-14) |
| `<phase>.probe.stdout/.stderr`, `*.err.log` | 표준 출력·오류 | **수집 대상 아님**(AC-14) |
| `session.json` | `{constructor_session_id, created, provider}` | 124바이트 |

stream 레코드는 `uuid`(레코드 고유)와 `session_id`를 갖는다 — `uuid`가 `source.upstream_event_id`의
자연스러운 원천이다. `assistant`/`user` 레코드에만 `timestamp`(`2026-09-12T11:08:37.200Z`)가 있고
`system`·`tool_progress`·`rate_limit_event`에는 없다.

**동기 축과 비동기 축이 같은 `result` 스키마로 수렴한다**는 것이 이번 실측의 가장 큰 발견이며,
D-T03-10의 정규화 규칙이 두 축에 대해 분기 없이 성립하는 근거다(TRD D-6).

### M-6. 기존 테스트 8건이 고정하는 것

`opal/tools/run-log-tool/tests/test_run_log_tool.py` — S-3~S-8, 8개 테스트 메서드.

| 시나리오 | 고정하는 사실 | T03 설계가 깨지 않는 이유 |
|---|---|---|
| S-3 init 멱등 | 2회차 `created:false`, 조각 바이트 불변, 조각 1개 | `init` 미변경 |
| S-4 append 1건 | `evt_` 접두, 응답 5필드, `idempotent_hit:false`, 줄 +1 | 사용 조합이 `PM/direct/PM/null` = **A4 허용** ✓. `--request-id req_s4_1` 단일 호출이라 멱등 경로 미진입 |
| S-5 validate-run | `verdict:pass`, `event_count:2`, gaps·violations 빈 배열 | `req_s5_0`·`req_s5_1` **서로 다른 request_id** ✓ 멱등 hit 없음 |
| S-6 상대경로 | 3표면 전부 `task_path_not_absolute` | 경로 검증이 여전히 최우선 단계 |
| S-7a/b 스키마 | `schema_invalid` + 조각 바이트 불변 | 검증이 조각 쓰기보다 앞선다는 성질을 T03이 **강화**만 함 |
| S-8a/b state 독립 | 생애주기 3연속 exit 0 + tmpdir에 `state.json` 0건, **소스에 `state_tool`·`state.json` 문자열 0건** | T03 신규 코드도 두 문자열을 쓰지 않는다 → W-1~W-4 공통 제약 |

**S-8b가 정적 문자열 검사라는 점이 설계 제약이다** — 주석·docstring·오류 메시지 어디에도 두 문자열을
넣을 수 없다. 상태 계층을 가리켜야 할 때는 "상태 도구"·"상태 원천"으로 쓴다(T02가 이미 쓰는 표현).

---

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| **D-T03-1. §1.3 허용 조합을 8행 선언 테이블 `COMBINATION_TABLE`로 표현하고, 판정 함수는 그 테이블에서만 파생한다** | 각 행은 `{id, actor_kinds, provenance_type, recorded_by_kinds, source_kinds, required_evidence}`. `combination_of(actor_kind, prov_type, recorded_by_kind, source_kind)` 는 매칭된 행 id 또는 `None`을 돌려주고, `None`이면 `provenance_invalid`. 어느 판정도 if 분기로 조합을 따로 적지 않는다 | AC-6의 판정 조건이 "표 밖 조합 **전수** 거부"다. 판정이 분기문에 흩어지면 전수 열거가 불가능해지고 표와 코드가 각자 진화한다. 테이블이면 시나리오가 4축 곱집합 660을 돌며 **같은 테이블로 기대값을 계산**할 수 있다(M-3) |
| **D-T03-2. 조합 공간 열거는 `iter_all_combinations()` 공개 함수가 소유한다** | 4축 enum 상수(`ACTOR_KINDS` 5 / `PROVENANCE_TYPES` 3 / `RECORDED_BY_KINDS` 4 / `SOURCE_KINDS` 10 + `None`)의 곱집합 660건을 생성한다. 시나리오는 이 함수를 import해 전수를 돌고 660·636 같은 상수를 하드코딩하지 않는다 | 상수를 시나리오에 적으면 계약이 늘 때 테스트가 조용히 낡는다. enum이 코드의 SSOT이고 열거가 그 파생이면 계약 확장이 곧 검증 확장이다 |
| **D-T03-3. `schema_invalid`와 `provenance_invalid`의 경계는 "무엇을 위반했는가"로 확정한다** | §1.1 최상위 필드의 존재·타입·형식·enum, §1.2의 사건별 조건부 필수 필드(`gate_id`·`summary`·`reason`·`duration_*`·`data.kind`·`data.from/to/row_key`) 위반 → **`schema_invalid`**. §1.3 4축 조합표 밖 조합, §1.3 명시적 거부 5종, `provenance` 필수 증거 결측·형식 위반 → **`provenance_invalid`** | §2.2 조건 문장 그대로다 — `schema_invalid`는 "폐쇄형 스키마 위반(미정의 키·타입·enum)", `provenance_invalid`는 "§1.3 허용 조합 표 밖의 조합, 필수 증거 부재, 분해 금지 불변식 위반". §1.3 **명시적 거부 목록 5번(사건별 actor 제약)이 §1.3 안에 있으므로** `gate.requested`에 `actor.kind=user`를 넣는 것도 `provenance_invalid`다. MV-1은 `schema_invalid`, MV-2·MV-3·MV-6은 `provenance_invalid`로 각각 대응한다 |
| **D-T03-4. `actor.kind=worker`이면 `worker_run_id`가 필수이고, 그 외에는 `null`이어야 한다** | §1.1 "worker 계열 사건은 필수"의 판정 기준을 **event 이름이 아니라 주체**로 확정한다. 위반은 `schema_invalid`(최상위 필드 조건부 필수) | A1·A2·A3 세 조합이 전부 worker actor이고, `actor_sequence` 범위(§1.1)와 `scope.worker_run_id`(§1.7.2)가 모두 이 식별자를 키로 쓴다. 주체 기준이 아니면 `activity`(actor=worker)가 범위 없는 순번을 받게 되어 MV-10이 성립하지 않는다. `worker.capability.*`는 actor가 `tool`이므로 최상위는 `null`이고 대상 워커는 `data.scope`가 갖는다(§1.7.2) |
| **D-T03-5. `actor_sequence` 범위를 §1.1 정의로 교정한다** | 범위 키 = `actor.kind == "worker"`면 `worker_run_id`, 그 외에는 `(actor.kind, actor.id)`. `scan_sequences()`의 현행 `(kind, id)` 고정(`run_log_core.py:340,351`)을 이 규칙으로 바꾼다 | §1.1 `actor_sequence` 정의 원문이며 MV-10의 판정 대상이다. T02 PLAN은 이 교정을 `begin-worker`(T04)와 묶어 미뤘으나, **범위 키 계산은 token 발급과 무관하다** — `worker_run_id`는 이미 `--worker-run-id`로 전달되는 평범한 필드다. T04를 기다릴 이유가 없고, 기다리면 T03이 만든 worker 사건들이 잘못된 범위의 순번을 확정해 버린다 |
| **D-T03-6. 멱등 판정 키는 `(run_id, request_id)`, 동일성 판정은 발급 필드 4종을 제외한 정규 직렬화의 SHA-256이다** | `canonical_digest(event)` = `event`에서 **`event_id`·`sequence`·`actor_sequence`·`timestamp`** 를 뺀 dict를 `json.dumps(…, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)` 한 UTF-8 바이트의 SHA-256 hex. 계산 시점은 **기본값 채움 이후·`redact()` 통과 이후**. 저장된 사건의 digest는 조각에서 같은 함수로 **재계산**한다 | 발급 필드는 매 호출 달라지므로 비교에서 빠져야 하고(AC-7 지시), 나머지는 전부 호출자가 정한 값이라 비교 대상이다. `sort_keys`가 **키 순서 차이를 흡수**하므로 `--data '{"a":1,"b":2}'`와 `'{"b":2,"a":1}'`이 같은 사건으로 판정된다. 폐쇄형 스키마가 새 최상위 키를 금지하므로(§1.1) digest를 사건에 **저장할 수 없다** — 재계산이 유일한 경로이고, 동시에 색인 없이도 성립한다(T04 경계 밖) |
| **D-T03-7. 멱등 조회는 순번 스캔과 같은 1회 스캔에서 수행한다** | `scan_sequences()`를 `scan_run(task_path, run_id, event)` 로 확장해 `(next_sequence, next_actor_sequence, malformed, idempotent_match)` 를 한 번의 조각 순회로 돌려준다. `idempotent_match`는 같은 `request_id`를 가진 저장 사건의 `(event_id, sequence, actor_sequence, segment, digest)` | 조각 glob이 이미 `run_id`로 좁혀져 있으므로 `(run_id, request_id)` 범위가 자동으로 성립한다(`_segment_glob_pattern`). 스캔을 두 번 돌면 append 비용이 2배가 되고 두 결과가 서로 다른 시점을 보게 된다 — 같은 락 구간이라도 한 번에 읽는 편이 단순하다. 비용은 T04 색인이 해소한다(D-3) |
| **D-T03-8. 직렬화 상한 16 KiB는 `redact()` 통과 후 최종 줄의 UTF-8 바이트로 잰다(개행 제외)** | `len(json.dumps(redacted_event, ensure_ascii=False, default=str).encode("utf-8")) > 16384` → `event_too_large`, 조각 미변경 | §1.1은 "직렬화 상한: UTF-8 16 KiB"이고 **디스크에 직렬화되는 것은 마스킹 후 payload**다. 마스킹 전에 재면 마스킹으로 줄어들 payload를 부당하게 거부하고, 마스킹으로 늘어나는 경우(치환 문자열이 원문보다 길 때)를 놓쳐 상한이 사실상 무력해진다. 순번을 채운 **최종 형태**를 재므로 디스크 크기와 판정이 정확히 일치하며, 거부해도 순번은 디스크에 확정되지 않아 다음 append가 같은 번호를 재계산한다(빈 번호 없음) |
| **D-T03-9. active 모드의 사건별 source 제약은 기록 코어가 집행하지 않는다** | §1.3 명시적 거부 목록 마지막 항(`worker.started`는 `process_start\|agent_handshake`, `activity`는 `agent_message\|stream_event\|tool_result`, terminal은 `process_exit\|agent_error`)은 T03 범위에서 **의도적으로 비집행**이며, 소유자는 완료 게이트 판정 주체(`state-tool.mark.completion-gate` / `run-log-tool.validate-worker` = T08·T11)다 | 이 제약은 조건문 자체에 `active 모드의`가 붙어 있다. 기록 코어는 모드를 알 수 없고 알아서도 안 된다(D-5·§3.1 "계약 활성 여부를 판정하지 않는다"). 코어가 이를 무조건 집행하면 **shadow 태스크의 정상 사건을 거부**한다 — §1.2가 `worker.started`의 source 제약을 "active는"으로 한정한 것과 정면 충돌한다. 코어는 A1이 허용하는 7종 전부를 통과시키고, 모드를 아는 계층이 그 부분집합으로 좁힌다. **이 문단은 후속 태스크가 같은 질문을 다시 올리지 않도록 하는 종결 조항이다** |
| **D-T03-10. 가져오기는 워커 생애주기 사건을 만들지 않는다 — 가져온 항목은 전부 `activity`다** | `import-agentic`·`import-oppl`이 만드는 사건은 예외 없이 `event="activity"`, `actor.kind="PM"`, `provenance.type="import"`, `recorded_by={"kind":"tool","id":"run-log-tool"}` = **조합 A8**이다. `worker.started`·terminal·`gate.*`·`run.*`·`state.changed`를 만들지 않는다 | 세 가지 이유가 같은 결론을 가리킨다. ① worker 계열 사건은 `worker_run_id`가 필수인데(D-T03-4) 원본에 그 식별자가 없고, **없는 값을 만들어내는 것은 TRD 데이터 흐름 (d) §금지된 복구가 명시적으로 금지**한다. ② terminal을 만들면 같은 `worker_run_id`에 실제 실행의 terminal과 가져온 terminal이 공존해 MV-4 유일성을 가져오기가 깨뜨린다. ③ 가져온 사건은 A3·A8 둘 다 완료 게이트 **불기여**이므로 생애주기로 만들 이득이 0이다. A3(worker+import)는 계약에 남지만 이 importer는 사용하지 않는다 — 상위 사건 식별자에 워커 실행 식별자가 실려 오는 미래 원본을 위한 자리다 |
| **D-T03-11. 가져오기 멱등 키는 `request_id`로 환원하고, 정규화 해시를 키에 항상 포함한다** | 키 = `upstream_event_id`가 있으면 `(source.id, upstream_event_id, sha256)`, 없으면 `(source.id, locator, sha256)`. `request_id = "imp_" + sha256(키 문자열)`. 따라서 가져오기 멱등은 D-T03-6의 `(run_id, request_id)` 판정을 그대로 타고, `skipped_idempotent` = `idempotent_hit:true`로 돌아온 건수다 | §3.4는 `upstream_event_id`를 "멱등 키의 **1순위 구성요소**"로 부른다 — 유일 구성요소가 아니다. 해시를 항상 포함하면 **`request_id_conflict`가 구조적으로 발생할 수 없다.** 이것이 필수인 이유: `surfaces.json`의 두 import 표면 `err` 집합에 `request_id_conflict`가 **없다**(실측). 키에서 해시를 빼면 원본이 수정된 재가져오기가 계약에 없는 오류 코드를 내고, 그걸 고치려면 §2.2·§2.2.1·`surfaces.json` 세 자산을 같은 단위로 열어야 한다(MV-30). 메커니즘 하나로 MV-5와 MV-19를 함께 만족시키는 편이 옳다 |
| **D-T03-12. legacy 가져오기는 헤더 행으로 표를 식별하고, 절대 시각이 없는 항목은 가져오지 않는다** | `\| # \| 시점 \| 단계 \| 카테고리 \| 내용 \| 결과 \|` 헤더와 정확히 일치하는 표의 6열 데이터 행만 사건 후보다. `시점`이 `YYYY-MM-DD HH:mm`을 만족하지 않으면 후보에서 제외한다. `요약` 2열 표·V2 4열 표·V3 자유 서술·V4 불릿은 **인식하지 않는다** | M-4 실측이 근거다. 위치 기반 파싱은 V2의 `근거` 열을 카테고리로 잘못 읽어 카테고리가 7종에서 20종으로 오염된다(691행 vs 671행). 시각 없는 항목을 가져오려면 시각을 지어내야 하는데 TRD (d)가 이를 금지한다 — `2026-09-03`(날짜만)·`20:0x`(자리표시자) 9건이 실제로 존재한다. **`scanned`는 "원본에서 인식한 사건 후보 수"로 정의**하며 항상 `scanned == imported + skipped_idempotent`를 만족한다(미인식 구조는 어느 칸에도 세지 않는다) — `surfaces.json`의 `ok` 응답 필드를 늘리지 않기 위한 정의다 |
| **D-T03-13. legacy 시각은 KST(+09:00)로 해석해 UTC로 옮기며, 이 변환은 가져오기 전용이다** | `_legacy_kst_to_utc_ms("2026-09-12 14:49")` → `"2026-09-12T05:49:00.000Z"`. 고정 오프셋 `+09:00`을 쓰고 외부 날짜 도구를 호출하지 않는다 | TRD §시간 모델: "기존 상태 파일의 시간대 없는 시각은 `Asia/Seoul`로 해석한 뒤 UTC로 바꾼다. 이 규칙은 **가져오기 전용**". 기록 코어가 외부 프로세스에 의존하면 "명시 인자만 소비"(D-5) 성질이 흐려진다(T02 D-G와 같은 이유). **날짜 경계 표본으로 두 시간계 정합을 판정하는 MV-26은 T06 소유**이며 T03은 변환 함수만 제공한다 |
| **D-T03-14. oppl 가져오기는 원본 형식별 규칙 3종을 갖되 출력은 한 형식으로 수렴한다** | ① `journal.md` 4열 표 → 행마다 1건, `data.kind` = `start`/`end`→`progress`, `gate-verdict`→`validation`, `retry`→`retry`. ② `<phase>.result.json` **및** `<phase>.events.jsonl`의 `type=="result"` 레코드 → 1건, `data.kind="progress"`, `data` = `{phase, subtype, is_error, duration_ms, num_turns, session_id, exitcode?}`. ③ `<phase>.exitcode` 단독(짝 결과 파일 부재 시) → 1건, `data={phase, exitcode}` | TRD 데이터 흐름 (e) "원본이 단일 형식이 아님" 분기의 지시 그대로다 — "하나의 파서가 아니라 원본 형식별 변환 규칙 집합을 갖되 출력은 하나의 표준 사건 형식으로 수렴한다"(D-6). ②가 한 규칙으로 두 축을 덮는 것은 M-5에서 **동기 축 `result.json`과 비동기 축 `result` 레코드의 키 집합이 동일**함을 실측했기 때문이다. 축별 분기가 필요 없다는 것이 MV-29가 요구하는 성질과 같은 방향이다 |
| **D-T03-15. oppl 가져오기는 `result` 이외의 stream 레코드와 원문 캡처 파일을 수집하지 않는다** | `assistant`·`user`·`system`·`tool_progress`·`rate_limit_event` 레코드, `*.prompt.txt`, `*.probe.stdout/stderr`, `*.err.log`는 읽지 않는다. `sources` 배열에는 실제로 소비한 파일만 `{path(태스크 상대), sha256, scanned}`로 싣는다 | ① AC-14·§8.1: "표준 출력·오류 출력·프롬프트 원문은 기본 수집하지 않는다". `user` 레코드는 tool_result **전문**을 담고 `assistant`는 모델 출력 전문을 담는다 — 가져오면 opt-in 없이 저장하는 것과 같다. ② 규모: 단일 `t3.events.jsonl`이 2.75 MB이고 레코드 3천 건 규모다. 감사 증거여야 할 표준 기록이 대화 로그 사본이 된다. ③ 16 KiB 상한에 걸리는 레코드가 다수다. **실행 중 중간 메시지를 사건으로 만드는 일은 변환기(T07) 소유**이며 가져오기는 변환기가 아니다 |
| **D-T03-16. 검증·멱등·순번·상한·쓰기 순서를 고정한다** | 아래 §검증 순서 표. 특히 **스키마·조합 검증이 조각 스캔보다 앞선다** | 거부될 사건 때문에 디스크를 읽지 않게 해 636건 전수 시나리오를 36초 규모로 유지한다(M-3). 또한 "부분 쓰기 없음"(S-7 고정 사실)을 순서로 보장한다 — 쓰기는 마지막 한 단계이고 그 앞의 모든 거부는 조각을 건드리지 않는다 |
| **D-T03-17. `RUN_LOG_ERROR_CODES`에 3종을 추가하고 그 외 자산은 손대지 않는다** | 추가: `provenance_invalid`·`request_id_conflict`·`event_too_large`. `CONTRACT.md`·`surfaces.json`·`TRD.md`·상태 도구의 어떤 테이블도 변경하지 않는다 | 세 코드는 §2.2에 이미 있고 §2.2.1이 `run-log-tool.append`를 발생 표면으로 지정하며 `surfaces.json`의 `append.err`에 이미 등재돼 있다(실측). **새 오류 코드를 만들지 않았으므로 MV-30 3자산 동시 개정이 발생하지 않는다.** `redaction_failed`(T06)·`worker_token_invalid`(범위 밖)는 추가하지 않는다 |
| **D-T03-18. `--run-id` 미지정 가져오기는 조각에서 run을 발견하되 모호하면 거부한다** | `run/`의 조각 파일명에서 `run_id` 집합을 뽑아 **정확히 1개면** 그것을 쓰고, **0개면** `run_log_missing`, **2개 이상이면** `schema_invalid`(detail: `--run-id` 필요) | `surfaces.json`이 두 import 표면의 `--run-id`를 optional로 둔다. 0개는 `run_log_missing`의 정의("기록 조각·실행 디렉터리 부재") 그대로다. 2개 이상(=`restart-run` 이후, T10)에서 임의로 고르면 사건이 엉뚱한 run에 붙는다. 인자 조합 부족을 `schema_invalid`로 돌리는 것은 T02가 이미 세운 선례다 — 손상된 `--data`를 CLI 단계에서 `schema_invalid`로 거부한다(`run_log_tool.py:57`) |
| **D-T03-19. A2(워커 직접 기록)는 구현되지만 현재 CLI로는 성립하지 않는다** | `COMBINATION_TABLE`의 A2는 `worker_log_token_id` 필수 증거를 갖고 판정에 참여한다. 그러나 CLI `append`는 `worker_log_token_id`를 `None`으로 고정하므로(`run_log_tool.py:76`) 워커 direct 호출은 **항상 `provenance_invalid`(§1.3 명시적 거부 2번)로 거부**된다. `worker_token_invalid`는 구현하지 않는다 | token 발급(`begin-worker`)과 런타임 권한 테이블이 범위 밖이다. 식별자를 인자로 받아 검증 없이 신뢰하면 R-20(위조 방지)이 무너진다 — **권한 없이 통과시키는 것보다 전부 거부하는 편이 fail-closed다.** 이 거부 사실을 시나리오로 고정해 두면 T04가 `begin-worker`를 붙일 때 RED가 명확해진다 |
| **D-T03-20. `@header`는 현재 사실로 제자리 교체하고 태스크 번호 이력을 남기지 않는다** | `run_log_core.py`·`run_log_tool.py`의 `description`에서 `"(T02 워킹 스켈레톤)"`, `"§1.3 조합 전수·16 KiB 상한·멱등 판정은 T03 소관"` 같은 **미래·이력 서술을 제거**하고 현재 동작으로 다시 쓴다. `exports` 배열에 신규 공개 함수를 반영한다 | `docs/CONVENTIONS.md:224` "코드 `@header`에는 현재 사실만 기재한다 — 이력은 git 로그와 `DONE.md`가 갖는다". T02가 GC-C001로 두 차례 지적받은 항목이다(`tasks/T02-*/GC-CONVENTION-*-recheck.md`). 다른 태스크 소관을 가리키는 서술은 남기되 **"T0N 소관" 형태의 번호가 아니라 현재 미구현 사실**로 적는다 |

### 검증 순서 (D-T03-16 확정)

| # | 단계 | 실패 시 코드 | 디스크 접근 |
|---|---|---|---|
| 1 | `require_absolute(task_path)` | `task_path_not_absolute` | 없음 |
| 2 | `_validate_run_id(run_id)` | `run_id_invalid` | 없음 |
| 3 | 배타 락 획득 | `task_lock_timeout` | 락 파일만 |
| 4 | 기본값 채움(`schema_version`/`event_id`/`timestamp`/널 허용 필드) | — | 없음 |
| 5 | §1.1·§1.2 단건 스키마·조건부 필수 검증 | `schema_invalid` | 없음 |
| 6 | §1.3 4축 조합 + 명시적 거부 + 필수 증거·형식 검증 | `provenance_invalid` | 없음 |
| 7 | `run/` 심볼릭 링크 검사 + 1회 조각 스캔(순번·멱등·손상) | `run_log_write_failed` | 조각 전량 |
| 8 | 멱등 판정 — digest 동일 → 기존 사건 반환 / 상이 → 거부 | `request_id_conflict` | 없음(7의 결과 사용) |
| 9 | 순번 부여 → `redact()` → 직렬화 → 16 KiB 검사 | `event_too_large` | 없음 |
| 10 | `O_APPEND` 쓰기 + `fsync` | `run_log_missing` / `run_log_write_failed` | 조각 1개 |

### 단건 vs 다건 — T03이 집행하지 않는 것과 그 소유자

| 항목 | 판정 성격 | 소유 |
|---|---|---|
| terminal 유일성(MV-4), 게이트 쌍(MV-22) | 다건 관계 | `validate-worker` / `state-tool.gate-*` — T08·T09 |
| 완료 알림 분해 금지 불변식(MV-7) | 다건 관계 | `validate-worker` — T08 |
| `data.duration_spans[]` 합·중복(MV-15) | 단건이지만 **대응 표면이 `validate-worker`** | T08·T09 |
| active 모드 사건별 source 제약 | 모드 종속 | 게이트 판정 주체 — T08·T11 (D-T03-9) |
| 가져온 사건의 게이트 불기여 **집행** | 게이트 조합 판정 | T11 |
| 색인·조각 경계·락 정책 | 런타임 | T04 |
| `redact()` 본문·원본 상한 | 마스킹 | T06 |

---

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 사건 어휘·조합 검증 | opal-be-agent | `opal/tools/run-log-tool/run_log_core.py` | (a) 4축 enum 상수 신설 — `ACTOR_KINDS`·`PROVENANCE_TYPES`·`RECORDED_BY_KINDS`·`SOURCE_KINDS`(§1.1.1·§1.1.2). (b) `COMBINATION_TABLE` 8행(A1~A8) + `combination_of(...)` + `iter_all_combinations()`(D-T03-1·2). (c) `EVENT_ACTOR_CONSTRAINTS` 12행(§1.2 주체 열) — `run.*`/`state.changed`/`worker.capability.*`=`tool`, `worker.*`=`worker`, `activity`={`worker`,`PM`}, `gate.requested`=`PM`, `gate.resolved`={`PM`,`user`,`auto`}. (d) `validate_event()` 확장 — 최상위 필드 타입·형식(`evt_`/`wrk_` 접두, RFC 3339 ms `Z` timestamp, `schema_version=="1.0"`, `refs` 상대경로 배열), §1.2 조건부 필수(`gate_id`·`summary`·`reason`·`reason_code`·`duration_ms`+`duration_source` XOR `duration_unknown_reason`·`data.kind` 4종·`state.changed`의 `data.from/to/row_key`·`worker.capability.issued`의 `data` 4키), D-T03-4 `worker_run_id` 조건부 필수 → 전부 `schema_invalid`. (e) `validate_provenance()` 신설 — 조합 판정 + 명시적 거부 5종 + 필수 증거 존재·형식(`sha256` 64자 소문자 hex, `observed_at` RFC 3339 ms, `locator` 비어있지 않은 문자열) → `provenance_invalid`. (f) `RUN_LOG_ERROR_CODES`에 `provenance_invalid` 추가. **D-T03-9 비집행 사유를 코드 주석으로 남긴다.** `state_tool`·`state.json` 문자열 0건 유지 | 없음 | P1 | AC-6, C-4 |
| W-2. 멱등·상한·순번 범위 | opal-be-agent | `opal/tools/run-log-tool/run_log_core.py` | (a) `canonical_digest(event)` 신설(D-T03-6). (b) `scan_sequences()`를 `scan_run(task_path, run_id, event)`로 확장 — 1회 순회로 `(next_sequence, next_actor_sequence, malformed, idempotent_match)` 반환, `actor_sequence` 범위 키를 D-T03-5로 교정. 기존 이름은 유지하지 않는다(내부 함수, 외부 호출자 없음 — `exports`만 갱신). (c) `append()`에 §검증 순서 8~9단계 삽입 — 멱등 hit면 저장 사건의 `event_id`·`sequence`·`actor_sequence`·`segment` + `idempotent_hit:true`를 **조각 미변경으로** 반환, digest 상이면 `request_id_conflict`. (d) 16 KiB 검사(D-T03-8) → `event_too_large`. (e) `RUN_LOG_ERROR_CODES`에 `request_id_conflict`·`event_too_large` 추가 | W-1 | P2 | AC-7, C-4 |
| W-3. 가져오기 정규화 2종 | opal-be-agent | `opal/tools/run-log-tool/run_log_core.py` | (a) `_legacy_kst_to_utc_ms()`(D-T03-13). (b) `_resolve_import_run_id()`(D-T03-18). (c) `_import_key_to_request_id()`(D-T03-11). (d) `import_agentic(task_path, run_id=None, *, dry_run=False, lock_held=False, lock_timeout_ms=…)` — `<task-path>/AGENTIC-LOG.md`를 헤더 행 기준 파싱(D-T03-12), 행마다 A8 `activity` payload 조립(`stage`=단계 열, `summary`=내용 열, `data`={`kind`, `category`, `result`}, `source`={`kind":"legacy_line"`, `id`=태스크 상대 경로, `sha256`=정규화 행의 SHA-256, `locator`=`AGENTIC-LOG.md#L{n}`}), `append(..., lock_held=True)` 호출. 카테고리 매핑 `DECISION`→`decision`, `GATE`→`validation`, 그 외(미지정 포함)→`progress`. (e) `import_oppl(...)` — `<task-path>/.oppl-run/` 3규칙(D-T03-14), 수집 제외 목록 준수(D-T03-15), `source.kind="oppl_event"`, stream `result` 레코드는 `upstream_event_id`=레코드 `uuid`. (f) 두 명령 모두 `{scanned, imported, skipped_idempotent}`(+oppl은 `sources`) 반환, `dry_run`이면 `append`를 호출하지 않고 키만 계산해 같은 3수치를 낸다. 파일 부재 시 `run_log_missing` | W-2 | P3 | AC-15, C-4 |
| W-4. CLI 표면 2종 배선 | opal-be-agent | `opal/tools/run-log-tool/run_log_tool.py` | `build_parser()`에 `import-agentic`·`import-oppl` 서브파서 추가 — `--task` 필수, `--run-id`·`--dry-run`(`store_true`)·`--format json` 선택(`surfaces.json` request_shape 그대로). `cmd_import_agentic`/`cmd_import_oppl`은 `run_log_core`의 동명 함수를 호출해 §2.1 봉투를 그대로 `_emit`한다. CLI는 파싱·정규화를 직접 하지 않는다. `exports`·`@header` 갱신(D-T03-20) | W-3 | P4 | AC-15 |
| W-5. 계약 테스트 신설 | opal-be-agent | `opal/tools/run-log-tool/tests/test_run_log_tool_contract.py` | 신규 파일. `@header`(layer=test, `scenarios`에 S-10~S-28). 아래 §테스트 시나리오 초안 전건 구현. `run.sh` subprocess 실호출 + 디스크 조각 검사만 — mock/patch/MagicMock/스텁/가짜 파일시스템 금지. 전수 시나리오는 `run_log_core.iter_all_combinations()`·`COMBINATION_TABLE`을 import해 기대값을 파생시키고 상수를 하드코딩하지 않는다. **기존 `test_run_log_tool.py`는 한 줄도 고치지 않는다** | W-4 | P5 | AC-6, AC-7, AC-15, AC-19 |
| W-6. 도구 문서 갱신 | opal-be-agent | `opal/tools/run-log-tool/README.md` | 서브명령 3종 → 5종으로 갱신, `import-agentic`·`import-oppl` 사용례와 응답 필드, `RUN_LOG_ERROR_CODES` 카탈로그에 추가 3종 반영, 가져오기 멱등 키 규칙(D-T03-11)과 비수집 대상(D-T03-15) 한 절. 이력 서술 없이 현재 사실만 | W-4 | P5 | AC-15 |

**변경하지 않는 자산(명시)**: `docs/run-log/CONTRACT.md`, `docs/run-log/surfaces.json`, `docs/run-log/TRD.md`,
`opal/tools/state-tool/state_tool.py`, `opal/tools/run-log-tool/tests/test_run_log_tool.py`,
`opal/tools/run-log-tool/run.sh`, `.gitignore`. 신규 오류 코드가 없고(D-T03-17) 표면 request/response
shape도 그대로이므로 MV-30 3자산 동시 개정이 발생하지 않는다.

---

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 상태 도구가 지금 내는 `run.started`가 강화된 검증을 통과하지 못한다 | T02가 배선한 shadow 초기화 관통(AC-2)과 `state-tool` 회귀 428건 | shadow init이 `provenance_invalid`/`schema_invalid`로 실패하면 T02 성과가 회귀한다 | 실측으로 확인했다 — `state_tool.py:1511-1540`의 payload는 `tool`/`direct`/`tool`/`source=null` = **조합 A7**이고 `worker_run_id`·`gate_id`는 `null`, `summary` 있음, `run.started`는 `reason` 불필요. 전 검증 통과다. W-5에 회귀 시나리오 S-28을 두어 428건 + 기존 8건을 판정한다 |
| H-2. 상태 도구의 보관함 재전송이 이제 멱등 hit로 돌아온다 | TRD (a) 5단계·(d) 복구 경로의 응답 해석 | 재전송이 `idempotent_hit:true`를 받았을 때 호출자가 실패로 읽으면 복구가 멈춘다 | 이는 **의도된 동작**이며 T02 D-E가 이미 전제한다("같은 `event_id`의 멱등 append가 중복을 만들지 않으므로 복구가 안전하게 보관함만 비운다"). 응답은 `ok:true`이고 `event_id`도 저장본과 같은 값이라 호출자 분기가 필요 없다. 보관함 복구를 완성하는 **T05에 이 사실을 인계 사항으로 명시**한다 |
| H-3. `state.changed`의 `data.from/to/row_key` 필수 집행이 T05 진행 중 작업과 충돌한다 | T05가 만들 상태 전이 사건 | T05가 해당 키 없이 append하면 `schema_invalid`로 막힌다 | §1.2가 이미 요구하는 조건이므로 계약 위반이 아니라 계약 집행이다. 두 태스크가 같은 배치에서 돌고 있으므로 **이 조항을 T05 인계 목록에 올린다**. 파일 충돌은 없다 — T03은 `run_log_core.py`만, T05는 상태 도구만 만진다 |
| H-4. `redact()` 본문이 채워지면(T06) 기존 조각의 digest와 새 사건의 digest가 어긋난다 | D-T03-6 멱등 판정, MV-5 | T06 배포 전에 기록된 사건에 대한 재호출이 `request_id_conflict`로 잘못 거부될 수 있다 | digest를 **마스킹 후**에 계산하므로 저장본과 신규 계산이 같은 함수를 탄다. 남는 경우는 "마스킹 규칙이 바뀌기 전에 저장된 사건 + 규칙 변경 후 같은 요청 재호출"뿐이며, 이는 `redact()`의 **멱등 계약**(`run_log_core.py:103-107`)이 재적용 안정성을 보장하는 범위다. T06 인계 사항으로 명시하고, 규칙 변경은 새 run에서 시작하는 것을 권고로 남긴다 |
| H-5. 전수 시나리오(636+45건)의 subprocess 비용이 테스트 스위트를 느리게 만든다 | 개발 반복 속도, CI 수용성 | 스위트가 1분을 넘기면 실행 빈도가 떨어진다 | 실측 57 ms/호출이고 **거부 경로는 조각을 읽지 않으므로**(D-T03-16) 조각이 커지지 않아 O(n²)가 생기지 않는다. 예상 36초 + 45건 3초. 임시 태스크 폴더 1개를 전 조합이 공유해 `init` 호출을 1회로 줄인다. 상한을 넘기면 분할이 아니라 **전수 유지 + 별도 클래스 분리**로 대응한다 — MV-2의 판정 조건이 전수이므로 표본화는 선택지가 아니다 |

---

## Release and recovery

- **적용 순서**: P1 → P2 → P3 → P4 → P5. `run_log_core.py` 단일 파일을 W-1~W-3이 순차 점유하므로
  세 그룹을 겹치지 않는다. W-5·W-6은 서로 다른 파일이라 P5에서 병렬이다.
- **검증 범위**: (a) 결정론 — 신규 S-10~S-27 전건, (b) 회귀 — 기존 `run-log-tool` 8건 + `state-tool`
  428건(C-2), (c) 실제 연동 — `run.sh` subprocess 실호출과 디스크 조각 파일 검사만. 실제 legacy
  `AGENTIC-LOG.md`(671행)와 실제 `.oppl-run/` 3벌을 fixture 복제 없이 **읽기 전용 원본으로** 사용한다.
- **배포 경계**: 이 태스크는 `opal/tools/` 프로젝트 소스만 바꾼다. `~/.opal/` 배포본을 직접 고치지
  않으며(C-1), install 재배포는 태스크 종료 시점에 수행한다 — `state-tool`이 형제 경로 우선 해석으로
  `run_log_core`를 적재하므로(T02 D-C) 배포 전에도 소스 트리에서 전 검증이 성립한다.
- **실패 시**: 기록 코어 변경은 파일 3개(+테스트·README)에 국한되고 디스크 포맷을 바꾸지 않는다 —
  기존 조각은 그대로 읽히고 새 검증은 **신규 append만** 막는다. 되돌림은 커밋 revert 한 번이며
  이미 기록된 사건은 손상되지 않는다. 가져오기가 잘못된 사건을 만든 경우 조각은 append 전용이므로
  삭제하지 않고, 잘못된 항목은 `validate-run`이 보고하는 대상으로 남긴다(합성·수정 금지, TRD (d)).

---

## 테스트 시나리오 초안 (RED-first)

공통 조건 — 전 시나리오 `required_fidelity: real-usage`.
`run.sh` subprocess 실행 + 디스크 조각 파일 검사로만 판정한다. mock/patch/MagicMock/스텁/가짜
파일시스템을 쓰지 않으며, 태스크 폴더는 `tempfile.TemporaryDirectory()` 아래 **절대 경로**다.

| id | title | surface_ref | red_required | AC/MV |
|---|---|---|---|---|
| S-10 | §1.3 표 밖 4축 조합 전수 거부 | `run-log-tool.append` | true | AC-6 / MV-2 |
| S-11 | 명시적 거부 조합 4종 | `run-log-tool.append` | true | AC-6 / MV-3 |
| S-12 | 사건 종류별 actor 제약 전수 | `run-log-tool.append` | true | AC-6 / MV-2 |
| S-13 | adapter·import 필수 증거 결측·형식 위반 | `run-log-tool.append` | true | MV-6 |
| S-14 | §1.2 조건부 필수 필드 위반 | `run-log-tool.append` | true | AC-6 / MV-1 |
| S-15 | 동일 request_id + 동일 payload → 기존 사건 반환 | `run-log-tool.append` | true | AC-7 / MV-5 |
| S-16 | 동일 request_id + 다른 payload → 거부 | `run-log-tool.append` | true | AC-7 / MV-5 |
| S-17 | 정규화가 키 순서·발급 필드에 불변 | `run-log-tool.append` | true | AC-7 / MV-5 |
| S-18 | 16 KiB 직렬화 상한 | `run-log-tool.append` | true | §1.1 / AC-6 |
| S-19 | `actor_sequence` 범위 — worker는 `worker_run_id` | `run-log-tool.validate-run` | true | MV-10 |
| S-20 | `sequence` run 전역 단조·무중복·무누락 | `run-log-tool.validate-run` | false | MV-10 |
| S-21 | legacy 가져오기 멱등 | `run-log-tool.import-agentic` | true | AC-15 / MV-19 |
| S-22 | legacy 구조 변종 식별과 정규화 | `run-log-tool.import-agentic` | true | AC-15 |
| S-23 | oppl 이원 구조 정규화와 비수집 경계 | `run-log-tool.import-oppl` | true | AC-15 / AC-14 |
| S-24 | oppl 가져오기 멱등 | `run-log-tool.import-oppl` | true | AC-15 / MV-19 |
| S-25 | `--dry-run` 무쓰기 | `run-log-tool.import-oppl` | true | AC-15 |
| S-26 | `--run-id` 해석과 모호성 거부 | `run-log-tool.import-agentic` | true | AC-15 / §3.2 |
| S-27 | 기록 도구 state 자산 독립 유지 | `run-log-tool.append` | false | AC-19 / MV-24 |
| S-28 | 기존 회귀 무손상 | `run-log-tool.append` | false | C-2 / AC-20 |
| S-29 | 명시적 `--mode` 인자로만 active 전용 source 제약 집행 | `run-log-tool.append` | true | PM 판정② / §1.3 말미 · §3.1(D-5) |

### S-10 — §1.3 표 밖 4축 조합 전수 거부

- **given**: 절대 경로 임시 태스크 폴더 1개, `init` 1회. 시나리오는 `run_log_core`의
  `iter_all_combinations()`(660건)와 `combination_of()`를 import한다.
- **when**: 660 조합 각각에 대해 `combination_of(...)`가 `None`인 것만 골라(= 636건 예상, **수치는
  코드에서 파생하며 시나리오에 상수로 적지 않는다**) `append`를 실호출한다. 각 호출은
  `--event activity --actor-kind <a> --actor-id x --provenance-type <t> --recorded-by-kind <r>`
  에 `source.kind`가 `None`이 아니면 `--source-kind <s> --source-id sid --source-sha256 <64hex>
  --source-observed-at <RFC3339ms> --source-locator loc`를 덧붙이고, `--request-id`는 조합마다 고유하게
  만든다. **필수 증거를 전부 채워 넣는 것이 핵심** — 증거 결측 때문이 아니라 조합 때문에 거부됨을 분리한다.
- **then**: 전건 exit ≠ 0, `ok:false`, `error.code == "provenance_invalid"`. 전 호출이 끝난 뒤
  조각 파일의 바이트가 `init` 직후와 **동일**(부분 쓰기 0건). 이어서 허용 24 조합 중 `activity`가
  성립하는 것들(§1.2 actor 제약과 교차)만 골라 append하면 전건 `ok:true`.
- **전수를 어떻게 도는가**: `ACTOR_KINDS`(5) × `PROVENANCE_TYPES`(3) × `RECORDED_BY_KINDS`(4) ×
  (`SOURCE_KINDS`(10) + `[None]`) 곱집합을 `itertools.product`로 생성한다. 기대값(허용/거부)은
  `COMBINATION_TABLE`에서만 파생하므로, 표가 바뀌면 시나리오가 자동으로 따라간다.

### S-11 — 명시적 거부 조합 4종

- **given**: 위와 같은 태스크 폴더.
- **when**: (a) `actor.kind=worker` + `recorded_by.kind=PM`(PM 대필), (b) `actor.kind=worker` +
  `type=direct` + `worker_log_token_id` 부재(현재 CLI의 유일한 worker direct 경로 — D-T03-19),
  (c) `type=adapter` + `recorded_by.kind=tool`, (d) `type=import` + `recorded_by.kind=adapter`.
- **then**: 4건 전부 `provenance_invalid`, 조각 불변. (a)는 M-2에서 **현재 통과함을 실측**했으므로
  확정적 RED다.

### S-12 — 사건 종류별 actor 제약 전수

- **given**: 태스크 폴더 1개. `EVENT_ACTOR_CONSTRAINTS`를 import한다.
- **when**: 사건 12종 × `actor.kind` 5종 = **60쌍**을 전수로 돈다. 각 쌍은 그 actor로 성립 가능한
  최소 유효 조합(예: `tool`→A7, `PM`→A4, `worker`→A1 증거 완비)과 사건별 필수 필드(`gate_id`·
  `summary`·`reason`·`duration_*`·`data`)를 채워 **actor 제약 외의 실패 요인을 제거**한다.
- **then**: `EVENT_ACTOR_CONSTRAINTS[event]`에 없는 45쌍은 `provenance_invalid`, 있는 15쌍은
  `ok:true`. 기대값은 상수가 아니라 매핑에서 파생한다.

### S-13 — adapter·import 필수 증거 결측·형식 위반

- **given**: 태스크 폴더 1개.
- **when**: (a) A1 adapter 사건에서 `source.id`·`source.sha256`·`source.observed_at`을 **각각 하나씩**
  뺀 3건, (b) A8 import 사건에서 `source.id`·`source.sha256`·`source.locator`를 각각 뺀 3건,
  (c) `sha256`이 64자 hex가 아닌 값(`"x"`, 대문자 hex, 63자) 3건, (d) `observed_at`이 RFC 3339 ms가
  아닌 값(`"2026-09-12"`, `"2026-09-12T05:49:00Z"`) 2건.
- **then**: 11건 전부 `provenance_invalid`, 조각 불변. 증거를 전부 채운 대조군 2건은 `ok:true`.

### S-14 — §1.2 조건부 필수 필드 위반

- **given**: 태스크 폴더 1개.
- **when**: (a) `gate.requested`에 `gate_id` 없음, (b) `activity`에 `gate_id` 있음(그 외 사건은 null),
  (c) `activity`에 `summary` 없음, (d) `activity`의 `data.kind`가 4종 밖, (e) `worker.failed`에
  `reason` 없음, (f) terminal에 `duration_ms`와 `duration_unknown_reason`이 **둘 다** 있음,
  (g) terminal에 **둘 다 없음**, (h) `state.changed`에 `data.row_key` 없음, (i) `actor.kind=worker`인데
  `worker_run_id` 없음, (j) `refs`에 절대 경로 원소, (k) `timestamp`가 RFC 3339 ms가 아님.
- **then**: 11건 전부 `schema_invalid`(**`provenance_invalid`가 아님** — D-T03-3 경계), 조각 불변.

### S-15 — 동일 request_id + 동일 payload → 기존 사건 반환

- **given**: `init` 후 `--request-id req_idem`으로 A4 `activity` 1건 append(1회차 응답 보관).
- **when**: **완전히 같은 인자**로 append를 1회 더 호출한다.
- **then**: exit 0, `ok:true`, `data.idempotent_hit == true`, `data.event_id`·`data.sequence`·
  `data.actor_sequence`가 1회차와 **동일**, 조각 줄 수가 1회차 직후와 **동일**(증가 0),
  조각 바이트도 동일. 이어서 `validate-run`의 `event_count`가 1이고 `verdict=="pass"`.
- **RED 근거**: M-1 실측에서 2회차가 `sequence:2`·`idempotent_hit:false`로 새 줄을 만든다.

### S-16 — 동일 request_id + 다른 payload → 거부

- **given**: S-15와 같은 1회차 사건.
- **when**: `--request-id`만 같고 `--summary`를 바꿔 append.
- **then**: exit ≠ 0, `error.code == "request_id_conflict"`, 조각 바이트 불변. `--data` 한 키만
  바꾼 경우, `--stage`만 추가한 경우도 같은 판정(3갈래).
- **RED 근거**: M-1 실측에서 3회차가 `ok:true`로 통과한다.

### S-17 — 정규화가 키 순서·발급 필드에 불변

- **given**: `init` 후 `--data '{"kind":"progress","a":1,"b":2}'`로 append 1건.
- **when**: 같은 `--request-id`로 `--data '{"b":2,"kind":"progress","a":1}'`(**JSON 키 순서만 다름**)
  를 append. 이어서 1회차와 수 초 간격을 두어 `timestamp`가 달라지는 조건에서 같은 호출을 반복.
- **then**: 두 경우 모두 `idempotent_hit:true` + 같은 `event_id`. 즉 `sort_keys` 정규화가 키 순서를
  흡수하고, 발급 필드(`timestamp`·`event_id`·`sequence`·`actor_sequence`)가 digest에서 제외됨을
  **동작으로** 고정한다.

### S-18 — 16 KiB 직렬화 상한

- **given**: `init` 후 조각 바이트 기록.
- **when**: (a) `--summary`를 반복 문자로 채워 최종 직렬화가 16,384바이트를 **넘도록** 만든 append,
  (b) 16,384바이트 **이하**가 되도록 한 단계 줄인 append, (c) 멀티바이트 한글로 (a)와 같은 실험
  (문자 수가 아니라 **UTF-8 바이트** 기준임을 고정).
- **then**: (a)·(c)는 `event_too_large` + 조각 바이트 불변, (b)는 `ok:true` + 줄 +1. (a) 거부 직후
  (b)를 호출하면 `sequence`가 **건너뛰지 않는다**(거부가 순번을 소모하지 않음).

### S-19 — `actor_sequence` 범위 — worker는 `worker_run_id`

- **given**: `init` 후, 같은 `--actor-id w1`이지만 `--worker-run-id`가 서로 다른 두 워커 실행
  `wrk_a`·`wrk_b`를 준비한다. 사건은 A1 adapter `activity`로 증거를 완비한다.
- **when**: `wrk_a` 2건 → `wrk_b` 2건 → `wrk_a` 1건 순서로 5건 append. 이어서 비워커 주체
  (`PM`/`pm`, A4) 2건 append.
- **then**: 응답의 `actor_sequence`가 `wrk_a`: 1,2,3 / `wrk_b`: 1,2 / `PM`: 1,2.
  즉 **같은 `actor.id`라도 `worker_run_id`가 다르면 범위가 갈린다.** `sequence`는 1..7로 전역 단조.
  조각 파일을 직접 읽어 같은 값을 재확인한다.
- **RED 근거**: 현행 `scan_sequences`는 `(kind, id)`로만 계산하므로 `wrk_b`의 첫 사건이 3을 받는다.

### S-20 — `sequence` run 전역 단조·무중복·무누락

- **given**: `init` 후.
- **when**: 서로 다른 주체(A4 PM, A6 auto, A7 tool)와 서로 다른 `request_id`로 12건을 순차 append.
- **then**: 응답 `sequence`가 1..12, `validate-run`의 `verdict=="pass"`·`event_count==12`·
  `sequence_gaps==[]`·`violations==[]`. 조각을 직접 파싱해 `sequence` 집합이 `{1..12}`와 일치.

### S-21 — legacy 가져오기 멱등

- **given**: 임시 태스크 폴더에 `init` 후, **실제 저장소의 `AGENTIC-LOG.md` 1건을 읽기 전용으로
  복사**해 `<task>/AGENTIC-LOG.md`로 둔다(원본 수정 금지).
- **when**: `import-agentic --task <abs> --run-id <run> --format json`을 2회 실행.
- **then**: 1회차 `scanned == imported`·`skipped_idempotent == 0`·`imported > 0`.
  2회차 `imported == 0`·`skipped_idempotent == 1회차 imported`·`scanned` 동일. 조각 줄 수가
  2회차 후에도 1회차 직후와 같다. `validate-run` `verdict=="pass"`.

### S-22 — legacy 구조 변종 식별과 정규화

- **given**: 한 파일 안에 (i) `## 요약` 2열 표, (ii) V1 6열 `## 대행 일지` 표(정상 4행 + 시점이
  `2026-09-03`인 행 1 + `2026-09-12 20:0x`인 행 1), (iii) V2 4열 `## PM 자율 판단 로그` 표,
  (iv) V3 `## [DECISION]` 자유 서술 절, (v) V4 불릿 목록을 모두 넣은 `AGENTIC-LOG.md`.
  구조는 M-4 실측에서 그대로 가져온다.
- **when**: `import-agentic` 1회.
- **then**: `scanned == imported == 4`(V1의 시각 정상 행만). 조각을 파싱해 생성된 4건이 전부
  `event=="activity"`·`actor.kind=="PM"`·`provenance.type=="import"`·
  `provenance.recorded_by.kind=="tool"`·`provenance.source.kind=="legacy_line"`이고,
  `data.kind`가 `{progress, decision, validation, retry}` 안에 있으며, `timestamp`가 KST 대비
  **9시간 뒤로 물러난 UTC**(`2026-09-12 14:49` → `2026-09-12T05:49:00.000Z`)임을 확인한다.
  `locator`가 `AGENTIC-LOG.md#L<n>` 형식이고 4건이 서로 다르다. `worker.*`·`gate.*`·`run.*`·
  `state.changed` 사건이 **0건**(D-T03-10).

### S-23 — oppl 이원 구조 정규화와 비수집 경계

- **given**: 임시 태스크 폴더 `<task>/.oppl-run/`에 M-5 구조를 재현한다 — `journal.md`(4열, 시각
  RFC 3339, 이벤트 `start`/`end`/`gate-verdict`/`retry` 각 1행), `t1.events.jsonl`(`system`·
  `assistant`·`user`·`tool_progress`·`rate_limit_event` 각 1줄 + `result` 1줄), `t1.exitcode`,
  `t4a.result.json`(동기 축), `t1.prompt.txt`(비밀스러운 문자열 포함), `t1.err.log`.
- **when**: `import-oppl --task <abs> --run-id <run> --format json` 1회.
- **then**:
  - `imported == 6` — journal 4행 + stream `result` 1건 + 동기 `result.json` 1건.
    `system`/`assistant`/`user`/`tool_progress`/`rate_limit_event`는 **사건이 되지 않는다.**
  - `sources` 배열에 `journal.md`·`t1.events.jsonl`·`t4a.result.json`이 있고
    `t1.prompt.txt`·`t1.err.log`는 **없다.** 각 항목이 `path`(태스크 상대)·`sha256`·`scanned`를 갖는다.
  - 조각 파일 전문에 `t1.prompt.txt`의 문자열이 **0건**으로 나타난다(실제 파일 검사).
  - 생성 6건 전부 A8(`PM`/`import`/`tool`/`oppl_event`)이고 `event=="activity"`.
  - stream `result`에서 온 사건의 `provenance.source.upstream_event_id`가 그 레코드의 `uuid`와 같고,
    journal 행에서 온 사건은 `upstream_event_id`가 `null`이며 `locator`가 `…journal.md#L<n>`이다.
  - `data`에 `duration_ms`·`is_error`·`subtype`·`exitcode`가 실리고, 모델 출력 본문(`result` 문자열)은
    실리지 않는다.

### S-24 — oppl 가져오기 멱등

- **given**: S-23 직후 상태.
- **when**: 같은 명령을 1회 더 실행.
- **then**: `imported == 0`, `skipped_idempotent == 6`, `scanned == 6`, 조각 줄 수 불변.
  이어서 `journal.md`에 1행을 **추가**한 뒤 3회차를 실행하면 `imported == 1`·
  `skipped_idempotent == 6`(기존 항목은 계속 건너뜀). MV-19의 판정 형태 그대로다.

### S-25 — `--dry-run` 무쓰기

- **given**: S-23의 원본 구조를 가진 새 태스크 폴더, `init` 직후 조각 바이트 기록.
- **when**: `import-oppl --dry-run`, 이어서 `import-agentic --dry-run`.
- **then**: 두 응답 모두 `ok:true`이고 `scanned`·`imported`가 실제 실행과 같은 수치,
  조각 파일 바이트가 **불변**. `validate-run`의 `event_count`가 0.

### S-26 — `--run-id` 해석과 모호성 거부

- **given**: (a) `run/` 조각이 하나도 없는 태스크 폴더, (b) `run_x` 조각만 있는 폴더,
  (c) `run_x`·`run_y` 두 벌의 조각이 있는 폴더. 각각에 legacy 원본을 둔다.
- **when**: 세 폴더에서 `--run-id` **없이** `import-agentic` 실행.
- **then**: (a) `run_log_missing`, (b) `ok:true`이며 사건이 `run_x` 조각에 붙는다,
  (c) `schema_invalid`(detail에 `--run-id` 필요 문구). 이어서 (c)에 `--run-id run_y`를 명시하면
  `ok:true`이고 `run_y` 조각에만 줄이 는다. 추가로 상대 경로 `--task`는 두 import 표면 모두
  `task_path_not_absolute`(§3.2 / MV-27).

### S-27 — 기록 도구 state 자산 독립 유지

- **given**: 빈 절대 경로 태스크 폴더.
- **when**: `init` → `append` → `import-agentic` → `import-oppl` → `validate-run` 5연속.
- **then**: 전건 exit 0(원본 부재 케이스는 `run_log_missing`을 허용하되 그 외 오류 없음),
  tmpdir 전역에 `state.json` 0건. 정적 판정 — `run_log_core.py`·`run_log_tool.py` 두 소스에
  `state_tool`·`state.json` 문자열 **0건**(기존 S-8b와 같은 검사를 T03 신규 코드 범위까지 확장).

### S-28 — 기존 회귀 무손상

- **given**: 변경 후 소스 트리.
- **when**: `python3 -m unittest discover opal/tools/run-log-tool/tests`,
  `python3 -m unittest discover opal/tools/state-tool/tests`.
- **then**: 기존 8건 전건 통과(파일 미수정), `state-tool` **428 passed / 3 skipped / 0 failed**
  (T02 DONE 기준선과 동일). 실패 0건이 아니면 T03은 완료가 아니다.

### S-29 — 명시적 `--mode` 인자로만 active 전용 source 제약 집행

- **given**: 절대 경로 임시 태스크 폴더, `init` 1회. A1 조합(worker/adapter/adapter) 증거 완비 + `worker_run_id` 채움.
- **when**: 같은 사건을 (a) `--mode` 미지정, (b) `--mode active`, (c) `--mode active` + 허용 `source.kind`,
  (d) `--mode shadow` 네 가지로 `append` 실호출한다. (b)는 `activity`에 `process_start`처럼
  §1.3 말미가 active에서 허용하지 않는 `source.kind`를 준다.
- **then**: (a)·(d)는 `ok:true`(기본값·shadow는 active 전용 제약 미적용), (b)는 `provenance_invalid`,
  (c)는 `ok:true`. 아울러 `run_log_core.py`·`run_log_tool.py` 소스에 `state_tool`·`state.json`
  문자열이 0건임을 정적으로 확인한다 — **모드는 인자로만 들어오고 코어가 어디서도 조회하지 않는다**(D-5).
- **배경**: 본 PLAN 작성 시점 이후 PM이 판정 ②를 확정했다. `D-T03-9`의 원 설계는 "기록 코어가
  active 전용 source 제약을 아예 집행하지 않는다"였으나, 확정 판정은 **코어가 모드를 판정하지는 않되
  호출자가 넘긴 명시적 모드 인자를 받아 집행**하고 미지정 시 미적용하는 형태다. 기본값이 미적용이므로
  `D-T03-9`가 우려한 "shadow 정상 사건 오거부"는 발생하지 않는다. 완료 게이트 최종 조합 판정은 T08 소관이다.

---
template: sdlc-v2
---
# DONE: T03 기록코어 — 스키마·멱등·순번

> 태스크: `T03-기록코어-스키마-멱등-순번` | 상위: `123-260912-oppl-태스크-실행로그-표준화`
> 완료: 2026-09-13 05:06 KST | 파이프라인: T1 → T2(RED) → G → T3 → T4a → T4b → T5

---

## 1. 무엇을 만들었나

기록 코어를 **표준 사건의 완전한 문지기**로 만들었다. T02가 남긴 워킹 스켈레톤(`init`/`append`/`validate_run`, 551행)이 사건을 **받아 적기만** 했다면, 이제는 **받을 자격이 있는 사건인지 판정**한 뒤 적는다.

| 능력 | 구현 |
|---|---|
| §1.3 허용 조합 전수 검증 | `COMBINATION_TABLE` 8행(A1~A8) 선언 테이블 + `combination_of()` + `iter_all_combinations()`. 4축 곱집합 660건 중 표 밖 **636건 전수 거부** |
| 사건별 actor 제약 | `EVENT_ACTOR_CONSTRAINTS` 12행. 사건 12종 × actor 5종 = 60쌍 전수 판정 |
| 출처(provenance) 증거 검증 | `validate_provenance()` — adapter/import 조건부 필수(`source.id`·`sha256`·`observed_at`·`locator`)와 형식(64자 hex, RFC 3339 ms) |
| 폐쇄형 스키마 | 최상위 키 + **중첩 4집합**(`actor`·`provenance`·`recorded_by`·`source`) 폐쇄 |
| 요청 식별자 멱등 | `canonical_digest()` — 발급 4필드 제외 + `sort_keys` 정규 직렬화 SHA-256. `idempotent_hit` / `request_id_conflict` |
| 16 KiB 상한 | 마스킹 후 최종 줄 UTF-8 바이트 기준 → `event_too_large` |
| 순번 범위 교정 | `scan_run()` — `actor.kind=worker`는 `worker_run_id` 범위, 그 외 `(actor.kind, actor.id)` 범위 |
| 가져오기 2종 | `import_agentic`(legacy `AGENTIC-LOG.md`) · `import_oppl`(`.oppl-run/` 이원 구조) — 단방향·멱등 |
| CLI 표면 | `init`/`append`/`validate-run`/`import-agentic`/`import-oppl` 5서브명령 + `append --mode` |

`run_log_core.py` 551 → **1,497행**. 신규 오류 코드 **0건** — 계약이 이미 정의한 코드만 썼다.

---

## 2. acceptance 판정

| AC | 판정 | 근거 |
|---|---|---|
| **AC-6** 정의되지 않은 조합 거부 | **통과** | S-10(표 밖 4축 전수 636건 `provenance_invalid`) · S-11(명시적 거부 4종) · S-12(event×actor 60쌍) · S-13(증거 결측·형식) · S-14(조건부 필수 10건 `schema_invalid`). 기대값을 상수로 적지 않고 `COMBINATION_TABLE`·`EVENT_ACTOR_CONSTRAINTS`에서 파생시켜, 표가 바뀌면 검증이 자동으로 따라간다 |
| **AC-7** 요청 식별자 멱등 | **통과** | S-15(동일 payload → `idempotent_hit:true` + **같은 `event_id`** + 조각 줄 수 불변) · S-16(다른 payload → `request_id_conflict`) · S-17(키 순서·발급 필드 불변) |
| **AC-15(1A분)** 가져오기 능력 | **통과** | S-21~S-26. 2회 실행 시 `imported:0` + `skipped_idempotent`가 1회차와 동일 + 사건 수 불변. 완료 게이트 **집행**은 T11 소관이며 이번엔 조합(A8)과 멱등까지만 만들었다 |
| **AC-19** 상태 자산 없이 통과 | **통과** | S-27. `state.json`·상태 fixture 0건으로 전건 통과. 소스의 `state_tool`·`state.json` 문자열 `grep -c` = **0 / 0** |
| **MV-1~6·MV-10·MV-30** | **통과** | 아래 §3 |

### MV 판정

| MV | 결과 | 근거 |
|---|---|---|
| MV-1 폐쇄형 스키마 | PASS | S-14 — 미정의 키·타입·enum 위반 `schema_invalid` |
| MV-2 enum 조합 전수 거부 | PASS | S-10·S-12 — 표 밖 **전수**(표본 아님) |
| MV-3 PM 대필 거부 | PASS | S-11 — RED 시점엔 `ok:true`로 통과하던 것이 닫혔다 |
| MV-5 요청 식별자 멱등 | PASS | S-15·S-16·S-17 |
| MV-6 출처 검증 | PASS | S-13 — 증거 각각 결측 시 전건 거부, 완비 대조군은 통과 |
| MV-10 순번 단조성 | PASS | S-19·S-20 — 같은 `actor.id`·다른 `worker_run_id` 2건이 **각각 1부터** |
| MV-30 오류코드↔표면 양방향 | PASS | §2.2 23종 / §2.2.1 23종 / `kind=cli` 17표면. 신규 코드 0건이라 3자산 개정 불발동 |

MV-4·MV-7~9·MV-11~29·MV-31은 이 태스크의 판정 대상이 아니다(완료 게이트·색인·마스킹·변환기 소관).

---

## 3. 검증 결과 (실측)

| 항목 | 결과 |
|---|---|
| `run-log-tool` 테스트 | **36 passed** (T02 8 + T03 시나리오 23 + 방어 회귀 5) |
| `state-tool` 회귀 | **436 passed, 3 skipped, 111 subtests passed, 0 failed** |
| MV-30 | **PASS** (23 / 23 / 17) |
| 시나리오 | **20/20 pass**, `locked=true`, `red_confirmed_required` 17/17 |
| 충실도 | `all_met: true` **20/20 real-usage** |
| 보안 | **blocking 0** — `PASS_WITH_ADVISORIES` |
| 컨벤션 | pass (Medium 3건 전건 수정) |

### 기준선 이동 — `428 → 436`

T02 시점 `state-tool` 기준선은 428이었다. 형제 태스크 **T05가 신규 8건을 추가**해 436으로 이동했다(T03 작업분 델타 0 — `git diff --stat opal/tools/state-tool/tests/test_state_tool.py` → `1 file changed, 8 insertions(+), 2 deletions(-)`, 전량 T05). 동결된 S-28의 `expected`에 남은 `428 passed`는 T02 시점 **서술**이며, 구속 문언은 마지막 문장("실패 0건이 아니면 T03은 완료가 아니다")이다. 잠긴 시나리오 상수를 갱신할 도구 경로가 없어 **판정으로 처리**했다(PM 확정).

---

## 4. 확정 판정 반영 (PM 판정 ①②)

**판정 ① `actor_sequence` 범위** — 계약(§1.1)이 옳고 구현이 틀렸다. `actor.kind=worker`면 `worker_run_id` 범위로 센다. 같은 워커 에이전트가 한 run에서 여러 번 디스패치될 때 `(kind, id)` 범위로는 서로 다른 실행이 한 순번에 섞여 궤적 복원이 성립하지 않기 때문이다.

- 반영: `scan_run()`의 범위 키 + `validate_provenance()`의 `worker_run_id` 필수 집행.
- **집행 위치가 설계 판단이었다**: 처음엔 스키마 단계(`validate_event`)에 뒀으나, 그러면 조합 자체가 표 밖인 사건(S-11의 PM 대필 등)이 이 필드 검사에 먼저 가로채여 `provenance_invalid`가 아니라 `schema_invalid`로 **잘못 분류**됐다(회귀 2건 실측). 조합 매치 확인 **직후**로 옮겨, 조합이 표 밖이면 그 사유로 먼저 거부되고 **조합이 유효한데 worker가 `worker_run_id`를 안 채운 경우만** 이 지점에서 거부된다.
- 적용 범위는 `event=worker.*`가 아니라 **`actor.kind=worker`인 모든 사건**이다 — `actor_sequence` 범위가 `worker_run_id`이므로 `activity`라도 없으면 셀 범위가 미정의다.

**판정 ② 명시적 모드 인자** — 코어는 모드를 **판정하지 않고 인자로 받는다**. `append(..., mode=None)` / CLI `--mode <shadow|active>`. 미지정이면 active 전용 source 제약을 적용하지 않는다(모르는 것을 추측해 차단하지 않는다).

- PLAN의 `D-T03-9`는 "코어가 아예 집행하지 않음"이었으나 판정 ②로 **대체**됐다. 기본값이 미적용이라 `D-T03-9`가 우려한 "shadow 정상 사건 오거부"는 발생하지 않는다.
- D-5는 보존된다 — 코어는 모드를 **어디서도 조회하지 않는다**(소스 `state_tool`·`state.json` 0건). 값의 출처는 호출자 책임이다.
- 집행 범위는 **append 시점의 구조 제약까지**다. 완료 게이트 최종 조합 판정은 **T08 소관**이다.
- 계약 3자산(§2.6 시그니처 · TRD D-5 소비 입력 · `surfaces.json` request_shape)의 `--mode` 반영은 **PM이 수행**했다. 이 태스크는 계약 자산을 수정하지 않았다.

---

## 5. 재작업 5회 — 무엇을 고쳤고, 왜 기대값을 낮추지 않았나

**[MUST] 다섯 번 모두 단언을 완화하지 않았다.** 고친 것은 **입력 구성**이거나 **구현**이며, 기대값은 한 번도 내리지 않았다.

| 회차 | 고친 것 | 기대값을 낮추지 않은 근거 |
|---|---|---|
| a2 | ① S-14 구현 결함(판정① 적용 범위 확대) ② S-10 **입력 구성** | S-10은 `provenance_invalid` 기대인데 `schema_invalid`가 났다. 원인은 테스트가 `activity` 필수 필드(`summary`·`data.kind`)를 안 채워 **조합에 도달하기 전에** 스키마 단계에서 걸린 것. 시나리오 문언이 스스로 "증거 결측 때문이 아니라 조합 때문에 거부됨을 분리한다"고 적었으므로, 입력을 채워 **비로소 조합을 판정하게** 만든 것이다. 기대값은 그대로 |
| a3 | S-13 **픽스처 격리** | `base_adapter`가 `actor.kind=worker`인데 `worker_run_id`를 비워 둬, 판정 대상(출처 증거)이 아닌 필드 때문에 결과가 갈렸다. S-14(i)와 입력이 사실상 동일해 **같은 입력에 다른 판정**을 요구하는 자기모순이었다. 판정 대상만 격리했을 뿐 단언은 불변 |
| a4 | 보안 blocking 6건(GC-201~206) + 컨벤션 3건 | 방어 **추가**. 완화 아님 |
| a5 | GC-208·209·211 | 〃 |
| a6 | GC-212·213 | 〃 |
| a7 | 방어 회귀 테스트 5건 **추가** | 추가 전용. 기존 31건 무수정 |

---

## 6. 보안 — 3회 검사에서 무엇이 드러났나

핵심 진단: **우회·약화가 아니라 미이식**이었다. T02가 조각 경로에 세운 방어(`O_NOFOLLOW`·경계 확인·권한)가 이번에 **신설한 가져오기 읽기 경로 2종**에는 들어가지 않았다. 가져오기는 **신뢰할 수 없는 외부 원본**을 읽는 경로이므로 조각 경로보다 방어가 약하면 안 된다.

| ID | 내용 | 처리 |
|---|---|---|
| GC-201·202 | 심볼릭 링크 추종 → 태스크 밖 파일을 **내부 출처로 위장** 적재 | 닫힘 — `_reject_symlink_or_escape()`·`_safe_read_bytes()` 신설, 신뢰 기준은 호출자 `task_path`(오염 가능한 `resolve()` 결과 아님) |
| GC-203~206 | 비신뢰 원본 예외 4종(`ValueError`/`AttributeError`/`RecursionError`/`UnicodeDecodeError`)이 봉투를 우회해 CLI를 죽임 | 닫힘 — 전부 §2.1 봉투로 환원 |
| GC-208 | `provenance` 중첩 미폐쇄 → **token 원문 평문 적재 가능**(실측 재현) | 닫힘 — 중첩 4집합 폐쇄. *마스킹은 자기가 모르는 필드를 가릴 수 없으므로* T06 `redact()`로 미룰 수 없는 **폐쇄형 스키마 구멍**이었다 |
| GC-209 | 거대 행 1개가 배치를 영구 차단 | 닫힘 — 해당 행만 건너뛰고 계속 |
| GC-211 | 디렉터리 0755 생성 | 닫힘(최말단). 중간 경로 잔여는 informational |
| GC-212 | **하드 링크**가 신설 방어를 우회(경로 검사로는 못 잡음) | 닫힘 — `os.fstat(fd)` 게이트(`S_ISREG` + `st_nlink == 1`) |
| GC-213 | FIFO가 가져오기를 무한 정지 | 닫힘 — `O_NONBLOCK`. `fstat`만으로는 부족했다(`open()` 자체가 writer 대기로 블로킹돼 검사에 도달하지 못함) |
| GC-214 | 위 방어에 **회귀 테스트 0건** — 게이트를 지워도 31건이 통과 | 닫힘 — `TestImportReadPathDefenses` 5건 추가. **변이 검증**으로 고정력 실증: 게이트 무력화 시 그 게이트에 묶인 2건만 실패, 원복 후 36 passed |

최종 판정 **blocking 0 / `PASS_WITH_ADVISORIES`**. 부작용 2축도 실측으로 없음을 확인했다 — `st_nlink == 1` 오탐 0건(APFS clonefile 포함 전건 `nlink=1`), `O_NONBLOCK` short read 0건(1 B~64 MiB 8종 SHA 일치, 19 MB 파일 끝줄 후보 도달 확인).

---

## 7. 인계 (handover)

| 항목 | 소유 | 내용 |
|---|---|---|
| **GC-207 원본 크기 상한 부재** | **T06** | **T03이 판정해 T06으로 넘긴 blocking 항목이다.** 실측: 64 MiB 원본 → RSS 158 MB. **GC-201(경계 확인)을 닫은 뒤의 잔여 위험**은 `/dev/zero` 링크 증폭 경로가 사라져 "정상적으로 거대한 legacy 원본"이라는 자원 문제만 남는다 — T06의 원본 상한 정책과 같은 판단 단위다. PM이 T06 수용 기준에 편입한다 |
| GC-210 sha256 이중 읽기 TOCTOU | T06 | 마스킹 구현이 읽기 경로를 다시 만질 때 함께 본다 |
| GC-206 `errors="replace"` 기준 | T06 / 계약 | 치환 디코딩 탓에 `source.sha256`이 **원본 바이트가 아니라 치환 후 텍스트**의 해시가 된다 — `import_oppl`의 `sources[].sha256`(원본 바이트)과 의미가 어긋난다. 체커 권고는 "되돌리지 말고 기준을 계약에 명문화" |
| GC-209 `scanned` 차감 | T11 / 계약 | 인식 후 버린 행이 stdout 봉투에서 사라진다(유일 신호인 stderr는 `--format json` 파이프에서 유실). `surfaces.json` `ok` 필드를 늘리지 않으려는 제약 때문이며, 체커 권고는 **`skipped_invalid` 필드 계약 개정 접수** |
| GC-211 잔여 / GC-215 / GC-216 | 후속 | 중간 경로 0755 · `os.fdopen()` raise 시 fd 누수 · `@header`·docstring이 방어를 `O_NOFOLLOW`까지만 기술 |
| 런타임 색인·조각 경계·락 정책 | **T04** | 순번은 현재 **색인 없이 조각 전량 스캔**으로 발급한다. `run_log_core.py`를 만질 때 §6의 방어 게이트를 제거하지 말 것 — `TestImportReadPathDefenses`가 고정한다 |
| 완료 게이트 최종 조합 판정 | **T08** | 판정 ②의 집행 범위는 **append 시점 구조 제약까지**다. 등급별 게이트 조건·분해 금지 불변식은 T08 |
| 가져온 사건의 게이트 불기여 **집행** | **T11** | 이번엔 조합(A8)과 멱등까지만. `import` 사건이 완료 게이트에 기여하지 않게 **막는 것**은 T11 |
| `scenario-conformance` 미검증 15표면 | PM / backlog | `surfaces.json` 분모가 Phase 1 전체라 exit 14가 난다. 미검증분은 전부 타 태스크 소유(init=T02 / begin-worker·validate-worker·reconcile·show·export=T04 / `state-tool.*` 6종=T05 / adapter 2종=T07). T03 소유 4표면은 전건 green |

---

## 8. 변경 파일

| 파일 | 변경 |
|---|---|
| `opal/tools/run-log-tool/run_log_core.py` | 551 → **1,497행**. 조합·actor 제약·출처·중첩 폐쇄 검증, `canonical_digest`/`scan_run`, 16 KiB 상한, `mode` 인자, 가져오기 2종, 읽기 경로 방어 |
| `opal/tools/run-log-tool/run_log_tool.py` | 164 → **190행**. 5서브명령 + `--mode` |
| `opal/tools/run-log-tool/tests/test_run_log_tool.py` | 309 → **1,626행**. 기존 8건 무수정 + 시나리오 23 + 방어 회귀 5 |
| `opal/tools/run-log-tool/README.md` | 5서브명령·오류 코드·가져오기 멱등 키·방어 절로 갱신 |
| `<task_folder>/PLAN.md` | 시나리오 표 19 → **20건 동기화**(S-29 행 + 상세 절) |
| `<task_folder>/QA-SPEC.md`·`DONE.md`·GC 보고서 6종 | 신규 |

**변경하지 않은 자산**: `docs/run-log/CONTRACT.md`·`surfaces.json`·`TRD.md`(PM 소유) · `opal/tools/state-tool/**`(T05 소유) · `test-scenario.json`(locked, 도구로만 갱신).

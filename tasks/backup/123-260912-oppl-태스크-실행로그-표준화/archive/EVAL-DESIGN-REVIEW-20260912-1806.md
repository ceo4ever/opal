# EVAL: 설계 루프 D6 명세 리뷰 — 태스크 실행 로그 표준화

- 실행 일시: 2026-09-12T18:06:00+09:00
- phase: `design-review`
- target_artifacts: `PRD.md`, `TRD.md`, `CONTRACT.md`, `BACKLOG.md`
- 보조 입력: `TASK.md`(C-1~C-9 / AC-1~AC-20), `surfaces.json`(표면 19개), `backlog.json`
- 기준 원천: `CONTRACT.md` §5 루브릭절 (RB-1~RB-5, 통과선 포함) — **로드 성공**
- Base 루브릭 보충 적용: 루브릭절이 다루지 않는 4개 축(표면 완전성 / auth 필드 완전성 / origin 선언 / 워킹 스켈레톤)에만 적용. 계약 완전성·일관성·설계 정합은 RB-1~RB-3이 소유하므로 Base 동명 축을 중복 적용하지 않았다.
- 워킹 스켈레톤 판정 기준: Base의 웹 구성(BE 기동+API 문서 UI / FE dev 서버 / 브라우저 관통 / 로그인 관통)이 아니라 **PM이 확정한 CLI 관통 등가 정의**로 판정했다. 근거: `surfaces.json` note(`origins`는 웹 클라이언트가 없으므로 선언하지 않는다), `CONTRACT.md` §3.1 말미, 제안서 §10 Phase 1A 첫 문단(`docs/proposals/opal-task-run-log.md:657-663`).
- verdict-only. 어떤 소스·산출물도 수정하지 않았다.

---

## 종합 verdict: **pass**

| 축 | 점수 | 통과선 | 판정 |
|---|---|---|---|
| RB-1 계약 완전성 | 4 | ≥4 | PASS |
| RB-2 계약 일관성 | 4 | ≥4 | PASS |
| RB-3 설계 정합 | 5 | ≥4 (3 이하 반려) | PASS |
| RB-4 범위 준수 | 4 | ≥4 (3 이하 반려) | PASS |
| RB-5 근거 인용 충실도 | 5 | ≥4 | PASS |

- 전 축 4점 이상 → 통과.
- 2점 이하 축 없음 → 즉시 반려 조건 미해당.
- RB-3·RB-4 모두 4점 이상 → 반려 조건 미해당.
- drift 필요성: **no** (CONTRACT 개정을 요구하는 판정 없음).

---

## 1. 루브릭절 축별 판정

### RB-1 계약 완전성 — 4

| item | result | reason | suggestion |
|---|---|---|---|
| `CONTRACT.md`::RB-1 | 4 | 사건 12종·공통 필드 34개·허용 조합 8행·오류 코드 22종·서브명령 17개(11+4+2)·MV 28항이 전건 타입·필수 여부·조건부 조건과 함께 정의돼 있고, 조건부 필수는 조건이 명시돼 있다(`CONTRACT.md` §1.1~§1.6, §2.2~§2.5, §4). 앵커 5에 근접하나 아래 3건이 "구현자가 임의로 메워야 하는" 빈칸으로 남아 앵커 3~5 사이의 4에 해당한다. | 아래 3건을 §1.2 또는 §2.3에 채우면 5 |
| `CONTRACT.md`::RB-1::capability scope | FAIL | `worker_token_invalid`가 "scope 불일치"를 거부 조건으로 선언하고(`CONTRACT.md`:281) `worker.capability.issued`가 `data.scope`를 필수로 요구하지만(같은 파일:86), **scope의 값 집합이 어디에도 정의돼 있지 않다**. `surfaces.json`의 `run-log-tool.begin-worker`도 `--scope <scope>`로만 둔다(`surfaces.json`:26). | §1.2에 `data.scope` enum(예: 1회 디스패치 범위를 표현하는 고정 값 집합)을 추가한다 |
| `CONTRACT.md`::RB-1::token 만료 | FAIL | `--expires-in <seconds>`가 optional인데(`surfaces.json`:26) **기본값·상한이 계약 어디에도 없다**. §2.7이 락 상한에 대해 "기본값이 항상 존재"를 명시한 것과 대비된다. | §2.3 `begin-worker` 행에 기본 TTL과 상한을 §2.7과 같은 형식으로 명시한다 |
| `CONTRACT.md`::RB-1::M-1 인터페이스 형태 | FAIL | §3.5가 `quietHours.timeZone` 추가와 `quiet_hours_token` 서명 포함을 Phase 1A로 확정했으나, 실제 대상 함수는 `load_quiet_hours() -> tuple[int, int] | None`(`dashboard/backend/config.py`:160)과 `quiet_hours_token(quiet_hours: tuple[int, int] | None)`(같은 파일:196)이다. **두 시그니처의 개정 후 형태가 계약에 없다.** 결정은 있으나 인터페이스가 비어 있어 구현자가 반환 형태를 임의로 정하게 된다. | §3.5에 개정 후 반환 형태와 서명 입력 구성을 한 줄로 확정한다 |
| `CONTRACT.md`::RB-1::gate 사건 payload | 확인 필요(감점 없음) | `gate.requested`/`gate.resolved`의 `data` 필드가 정의돼 있지 않다(§1.2). 단 MV-22의 판정(대기 시간 재구성)은 `gate_id`+`timestamp`만으로 성립하므로 구현 착수를 막지 않는다. | 게이트 종류·소유자를 집계에서 구분할 필요가 있으면 §1.2에 `data` 필드를 추가한다 |

### RB-2 계약 일관성 — 4

| item | result | reason | suggestion |
|---|---|---|---|
| `CONTRACT.md`::RB-2::내부 | PASS | 계약 문서 내부에서 같은 값이 두 번 다르게 나오는 지점을 찾지 못했다. outbox 상한(사건당 4 KiB·`TOTAL_LIMIT=128`·전체 512 KiB)이 §1.4에서 단일 정의되고 §2.2 `run_log_outbox_full`·MV-21·`TASK.md` AC-10·`TRD.md` D-2가 같은 값을 가리킨다. 사건 12종·표면 17+2개도 §1.2/§2.3~§2.5/`surfaces.json` 사이에서 개수와 id가 정확히 일치한다. | — |
| `PRD.md`::RB-2::AC 귀속 표 vs 주석 | FAIL | §성공 판정 표(`PRD.md`:201-207)와 바로 아래 주석(:209-216)이 어긋난다. 주석은 AC-6을 "Phase 1A에서 갖추고 1B에서 집행", AC-15를 "1A에서 갖추고 1B에서 집행", AC-18을 "1B에서 성립, 1C에서 완성"으로 분할하는데, **표의 Phase 1A 행에 AC-6·AC-15가 없고 Phase 1B 행에 AC-18이 없다.** AC-9·AC-10은 양쪽 행에 모두 있어 같은 문서 안에서 분할 표기 방식이 일관되지 않다. | 표를 주석과 맞춰 1A 행에 AC-6·AC-15, 1B 행에 AC-18을 추가하거나, 분할 AC는 표에서 빼고 주석만 SSOT로 선언한다 |
| `backlog.json`::T10::AC-17 | FAIL | T10의 수용 기준 2번이 `"AC-17(재실행분): 재접속·재개는 실행 식별자를 유지하고 명시적 재실행만 새 식별자를 발급한다"`인데, **`TASK.md` AC-17은 "pilot SKILL·하네스·`docs/CONVENTIONS.md`의 AGENTIC 무조건 생성 지시가 0건"**(`TASK.md`:88-89)으로 전혀 다른 기준이다. 서술 내용은 AC가 아니라 `PRD.md` R-16(:117)에 해당한다. AC-17 자체는 T15가 원문대로 커버하므로 누락은 아니고, T10의 라벨이 틀렸다. | T10의 해당 항목을 `R-16` 또는 무번호 기준으로 고친다 |
| `TRD.md`::RB-2::M-1 미결 표기 | FAIL | `TRD.md`:227이 "Phase 1에서 서명을 바꿔야 하는지 … 확정되지 않았다 — §미결 기술 쟁점 M-1로 올린다"로 남아 있으나, `CONTRACT.md` §3.5가 "Phase 1A에서 함께 포함한다"로 이미 확정했다. 미결 표(`TRD.md`:384)가 결정 주체를 CONTRACT로 지정했으므로 설계 충돌은 아니지만, TRD만 읽는 구현자는 미확정으로 읽는다. | `TRD.md` M-1 행에 "CONTRACT §3.5에서 확정됨"을 부기한다 |
| `CONTRACT.md`::RB-2::token 식별자 명칭 | FAIL(경미) | 같은 대상에 대해 `worker_log_token_id`(§1.1.2), `data.token_sha256`(§1.2 issued), `data.token_id`(§1.2 revoked) 세 이름이 쓰이는데 **셋의 관계가 어디에도 정의돼 있지 않다**. `data.token_id`가 `worker_log_token_id`와 같은 값인지 구현자가 추론해야 한다. | §1.1.2 또는 §1.2에 세 식별자의 관계를 1줄로 고정한다 |

### RB-3 설계 정합 (TRD 결정과의 일치) — 5

| item | result | reason | suggestion |
|---|---|---|---|
| `CONTRACT.md`::RB-3 | 5 | D-1~D-9 전건이 최소 1개 계약 조항 또는 MV 항목으로 집행된다: D-1→§3.2 경로 계약+§1.1, D-2→§1.4 보관함, D-3→§3.1(파생 색인)+MV-11, D-4→§2.7+MV-13, D-5→§2.6 인프로세스 시그니처(`lock_held`, "코어는 `state.json`을 읽지 않는다")+MV-24, D-6→§3.1 플랫폼 분기 금지, D-7→§1.4 계약 무결성+MV-20, D-8→§1.6+§3.3+MV-23, D-9→§2.2 `redaction_failed`+MV-17. TRD 결정과 충돌하는 계약 조항(예: 기록 코어가 상태 파일을 읽는 시그니처)은 없다. | — |
| `CONTRACT.md`::RB-3::결정 우회 경로 | PASS | 우회 가능한 합법 호출 경로를 찾지 못했다. §3.1이 변환기의 `run-log-core` 직접 링크를, §2.6이 `lock_held` 거짓 선언을 계약 위반으로 각각 명시하고, MV-24가 단방향 의존을 실측 판정으로 건다. | — |
| `CONTRACT.md`::RB-3::D-6 동일성 판정 | 확인 필요(감점 없음) | D-6은 §3.1 계약 조항으로 집행되므로 앵커 5 요건을 충족하지만, `PRD.md` R-12의 관찰 지점("서로 다른 플랫폼 원본이 만들어 낸 표준 사건의 동일성")에 직접 대응하는 MV 항목이 §4에 없다. 판정 자체는 T07의 그림자 표본으로 가능하다. | Phase 1A 구현 태스크에서 두 채널 fixture의 표준 사건 동일성 판정을 시나리오로 추가하는 것을 권고 |

### RB-4 범위 준수 (Phase 경계·비목표) — 4

| item | result | reason | suggestion |
|---|---|---|---|
| 비목표 침범 | PASS | 4종 비목표 전건 미침범을 확인했다. 2단 커밋·correction 체인은 `CONTRACT.md`:86이 "이 계약에 없다"로 명시 배제하고 `TRD.md` D-2가 대안 (a)로 기각한다. Console 분석 화면은 §3.1이 "기록 segment 직접 읽기 금지(Phase 2 범위)"로 차단한다. `backlog.json` 15개 태스크 어디에도 Phase 2·3 항목이 없다. | — |
| Phase 2 종결 조항 | PASS | §3.4가 "**이 문단은 후속 단계가 같은 질문을 다시 올리지 않도록 하는 종결 조항이다. Phase 1 범위에서 교차 집계 주체를 정하지 않는 것이 결정이다**"로 앵커 5가 요구하는 형태를 그대로 갖췄다. | — |
| 계약/데이터 분리 | PASS | 계약(등급 enum §1.5·게이트 조건 §1.5·receipt 구조 §1.5·`profiles.json` 스키마 §1.6)과 배정값(`profiles.json` 실물)의 소유가 §1.6 본문·§3.3·`TRD.md` D-8에서 일관되게 분리돼 있고, `TRD.md`:298이 "등급 배정값 자체는 Phase 0 산출이므로 이 문서에서 확정하지 않는다"로 못 박는다. §1.6 말미가 배정값 변경을 "재스파이크이며 계약 재확정 절차를 발동하지 않는다"로 명시해 `TASK.md` C-9를 집행한다. | — |
| `CONTRACT.md`::RB-4::예시 배정값 | FAIL(경미) | §1.4와 §1.6의 JSON 예시가 실존 채널 `pm-agent-tool`에 `"completion_profile": "observed_trajectory"`를 박아 둔다(`CONTRACT.md`:132, :207). 스키마 예시이며 본문이 소유 주체를 명확히 하므로 침범은 아니지만, **Phase 0 실측 전에 이 축의 등급이 이미 정해진 것처럼 읽힐 여지**가 있다. RK-1(관측 불가 판정 가능성)과 정면으로 충돌하는 외관이다. | 예시의 `channel_id`를 가상값으로 바꾸거나 "예시값이며 배정이 아니다" 1줄을 단다 |
| `BACKLOG.md`::RB-4::Phase 0 승인 게이트 | FAIL | 제안서(`docs/proposals/opal-task-run-log.md:653-655`)와 `PRD.md`(:144-147, 게이트 요약 :188), `TRD.md`(:310)는 Phase 0→1A 사람 승인 게이트를 "백로그 의존 관계로 대체되지 않으며 자율 진행 모드에서도 유지"로 명시한다. 즉 **게이트 기재는 존재한다.** 그러나 실행을 구동하는 `BACKLOG.md`/`backlog.json`에는 게이트 표시가 전혀 없고 T02가 `depends:["T01"]`·`status:"pending"`으로만 묶여 있다. 자율 진행 모드에서 T01이 done이 된 직후 T02가 곧바로 선택 가능하며, 이는 제안서가 "의존으로 대체 불가"라고 한 바로 그 상황이다. | T02의 `status`를 `blocked`로 두고 해소 조건을 사용자 승인으로 명시하거나, `BACKLOG.md`에 T01↔T02 사이 게이트 행을 추가하고 `STATE.md` 블로커에 등재한다 |

### RB-5 근거 인용 충실도 — 5

| item | result | reason | suggestion |
|---|---|---|---|
| PM 판정 5건 표기 | PASS | M-1~M-5 전건이 제목에 "(PM 판정 M-n)"으로 명시되고 판단 근거를 함께 적는다: §2.7(M-4, fail-closed≠무한 대기, R-6 충돌 논증), §3.2(M-2, `worktree.md:29`·`:41`·`memory_tool.py:169`로 "두 규칙은 만나지 않는다" 논증), §3.3(M-3, 2단 소유·승격 절차), §3.4(M-5, brain 개념 문서 인용 + 종결 조항), §3.5(M-1, `config.py` @header·204행으로 캐시 키 논증). 제안서에 없는 조항임이 전건 드러나 있다. | — |
| 인용 정확성 표본 검증 | PASS | 인용 6건을 원문에서 직접 확인해 전건 일치를 확인했다 — `docs/proposals/opal-task-run-log.md:653-655`(Phase 1A 승인 게이트 문단 시작 행 일치), `opal/core/references/harness/worktree.md:29`(task_root/allocator_root 소유 문장 일치)·`:41`(추론 금지 [MUST] 일치)·`:57`(canonical path 6종 필드 일치), `opal/tools/memory-tool/memory_tool.py:169`(`WORKTREE_WRITE_REJECTED` 정의 일치), `dashboard/backend/config.py:160`(`load_quiet_hours` 정의)·`:196`·`:204`(서명이 시작·끝 분만 담음 — 일치), `opal/tools/state-tool/state_tool.py:1402-1405`(1.0/1.1 판정 규칙 일치), `.gitignore:38`(`.oppl-run/`만 등재 — 일치). **줄번호 오기 0건.** | — |
| 인용 입도 | PASS | 대부분의 비자명 조항이 `문서 §절` 또는 `경로:줄번호`를 단다. 앵커 5의 "제안서 전체를 다시 읽지 않아도 되는" 수준을 충족한다. | — |

---

## 2. Base 루브릭 보충 판정 (루브릭절 미포함 축)

| 축 | 결과 | 근거 |
|---|---|---|
| 표면 완전성 | 5 | `surfaces.json` 표면 19개(CLI 17 + adapter 2)가 `CONTRACT.md` §2.3(11) + §2.4(4) + §2.5(2) + §4 변환기 조항(2)과 개수·id 모두 일치한다. 백로그 `covers` 합집합과 표면 집합을 대조한 결과 **미커버 표면 0건, 미정의 표면 참조 0건**이다. |
| auth 필드 완전성 | yes | 19개 표면 전건이 `auth` 필드를 선언한다(전부 `none`). 이 프로젝트는 CLI·프레임워크 내부 계약이므로 인증 표면 자체가 존재하지 않으며, 그 사실이 `surfaces.json` note와 `CONTRACT.md` §3.1 말미에 기재돼 있다. |
| origin 선언 | N/A | 웹 클라이언트 부재. `surfaces.json` note("origins는 웹 클라이언트가 없으므로 선언하지 않는다")와 `CONTRACT.md` §3.1 "**`origins` 미선언**" 조항이 부재 사실을 명시적으로 선언한다 — 누락이 아니라 선언된 N/A다. |
| 워킹 스켈레톤 (CLI 관통 등가) | yes | 아래 4항 전건 충족. |

**워킹 스켈레톤 4항 판정**

1. **슬라이스 존재**: `T02 워킹 스켈레톤 — CLI 관통 1건`(P0)이 존재하고 `depends:["T01"]`로 **의존 루트(T01) 바로 다음**에 배치돼 있다. T01은 코드 산출이 없는 읽기·실험 전용 슬라이스이므로(`TRD.md`:307) T02가 사실상 첫 구현 슬라이스다.
2. **관통 범위가 끝에서 끝인가**: yes. T02의 `covers`가 `state-tool.init.run-log-mode` → `run-log-tool.init` → `run-log-tool.append` → `run-log-tool.validate-run` 4표면이며, 제안서 §10 Phase 1A 첫 문단이 정의한 관통(`state-tool init --run-log-mode shadow`가 `state.json` 1.2와 첫 segment 생성 → `append` 1건 → `validate-run` 통과, `docs/proposals/opal-task-run-log.md:657-663`)과 표면 단위로 정확히 일치한다. 수용 기준 1번이 AC-2를 그대로 인용한다.
3. **후속 태스크가 이 경로 위에서 검증하는가**: yes. Phase 1A의 병렬 4태스크(T03·T04·T05·T06)가 모두 `depends:["T02"]`이며, 통합 T07이 그 4건에 의존한다. 스켈레톤을 우회해 진입 가능한 구현 태스크가 없다.
4. **모의 검증 회피 경로**: 닫혀 있다. T02 수용 기준 3번이 `"스켈레톤 부재를 이유로 한 모의 검증이 이후 태스크에서 성립하지 않는다"`를 기준으로 명시하고, `TRD.md`:314과 `PRD.md`:151-154가 같은 금지를 반복한다.

---

## 3. 지시된 확인 지점별 결과

| # | 확인 지점 | 결과 |
|---|---|---|
| 1 | 계약/데이터 분리 성립 | **성립.** RB-4 판정 참조. 배정값이 계약 본문 조항으로 새어 들어온 사례는 없다. 다만 §1.4·§1.6 JSON 예시의 실존 채널명+구체 등급 조합은 정리를 권고(경미). |
| 2 | PM 판정 M-1~M-5 반영 | **전건 반영.** §2.7/§3.2/§3.3/§3.4/§3.5 각각이 "(PM 판정 M-n)" 표기와 판단 근거를 갖는다. 다만 `TRD.md` M-1 서술이 확정 전 상태로 남아 있다(RB-2 지적). |
| 3 | Phase 게이트의 구조적 강제 | **부분 충족.** 게이트 기재는 `PRD.md` 단계별 인도 범위·게이트 요약, `TRD.md` Phase 0 항에 존재하며 제안서 줄번호까지 인용한다. 그러나 백로그 산출물에는 게이트 표시가 없어 자율 진행 모드에서 T01 done 직후 T02 진입을 막는 구조가 없다. → unresolved U-1. |
| 4 | AC-1~AC-20 전건 백로그 반영 | **20/20 반영.** 매핑: AC-1→T01, AC-2→T02, AC-3→T05, AC-4·5·11→T08, AC-6→T03+T08, AC-7·19→T03, AC-8→T04, AC-9→T04+T08, AC-10→T05+T10, AC-12→T09, AC-13·14→T06, AC-15→T11, AC-16→T07+T11, AC-17→T15, AC-18→T15, AC-20→T06+T12+T15. **분할 귀속 8건 중 7건이 양쪽 태스크에 반영**됐다. 예외는 AC-15로, `PRD.md`:214가 "1A에서 갖추고 1B에서 집행"으로 분할했으나 백로그에는 T11(Phase 1B) 한쪽만 있다. → unresolved U-3. 별건으로 T10의 AC-17 라벨 오기 1건(RB-2 지적). |
| 5 | 비목표 침범 | **없음.** RB-4 판정 참조. §3.5가 `quiet_hours_token` 서명 변경을 Phase 1A로 당기는 건은 Phase 2 침범이 아니다 — 계약이 "설정 키 추가와 서명 포함은 한 단위"이며 "겹침 계산의 실제 소비가 Phase 2인 것과 무관하다"고 근거를 밝히고, `config.py:204`로 캐시 오염 논증을 편다. 판단 근거가 명시된 의도적 결정으로 수용한다. |
| 6 | 문서 간 모순 | **4건 발견** — PRD 표 vs 주석(U-2), T10 AC-17 오기(U-4), TRD M-1 stale(U-5), 그리고 가장 실질적인 건: **가져오기(import) 구현이 PRD·TRD의 단계별 인도 범위 어느 Phase 목록에도 없다**(U-3). `PRD.md`:155-157(1A 나머지 인도물)과 :166-169(1B 인도물), `TRD.md`:316(1A 코드)과 :323(1B 코드) 어디에도 가져오기가 없는데, `backlog.json` T11이 P1(Phase 1B)에서 `run-log-tool.import-agentic`·`import-oppl`을 구현하고 AC-15를 진다. |

---

## 4. 미해결 이슈 (unresolved)

| ID | 이슈 | 심각도 | 되돌림 대상 |
|---|---|---|---|
| U-1 | Phase 0→1A 사람 승인 게이트가 백로그 산출물에 미기재 — 자율 진행 모드에서 T01 done 직후 T02 진입을 막는 구조가 없다. 제안서 `:653-655`는 "백로그 의존 관계로 대체되지 않는다"고 명시한다 | **중** | **D5 (백로그)** — T02를 `blocked`로 두고 해소 조건을 사용자 승인으로 명시, `BACKLOG.md`·`STATE.md`에 게이트 등재 |
| U-2 | `PRD.md` 성공 판정 표(:201-207)와 분할 주석(:209-216) 불일치 — 1A 행에 AC-6·AC-15 누락, 1B 행에 AC-18 누락 | 중 | **D2 (PRD)** |
| U-3 | 가져오기 구현이 PRD·TRD의 어느 Phase 인도 목록에도 없는데 백로그 T11이 Phase 1B로 구현한다. 연동해서 AC-15의 "1A분"이 백로그에 없다 | 중 | **D2·D3 (PRD 단계별 인도 범위 + TRD 단계별 기술 도입 순서)** — 가져오기를 어느 Phase 인도물로 확정할지 정한 뒤 백로그 반영 |
| U-4 | `backlog.json` T10 수용 기준의 `AC-17(재실행분)` 라벨이 `TASK.md` AC-17 원문과 무관(실제로는 `PRD.md` R-16) | 중 | **D5 (백로그)** — 라벨만 교정 |
| U-5 | `TRD.md`:227이 M-1을 미확정으로 서술하나 `CONTRACT.md` §3.5가 확정함 | 하 | **D3 (TRD)** — 미결 표에 확정 사실 부기 |
| U-6 | `CONTRACT.md` §1.2 `data.scope` 값 집합 미정의, `--expires-in` 기본값·상한 미정의 | 중 | **D4 (CONTRACT)** — §1.2/§2.3 보강 |
| U-7 | `CONTRACT.md` §3.5의 M-1 결정에 대응하는 `load_quiet_hours`·`quiet_hours_token` 개정 후 시그니처 형태 미정의 | 하 | **D4 (CONTRACT)** 또는 Phase 1A 구현 태스크 |
| U-8 | `worker_log_token_id` / `data.token_sha256` / `data.token_id` 세 식별자의 관계 미정의 | 하 | **D4 (CONTRACT)** |
| U-9 | §1.4·§1.6 JSON 예시가 실존 채널 `pm-agent-tool`에 구체 등급을 박아 둬 Phase 0 실측 전 배정으로 읽힐 여지 | 하 | **D4 (CONTRACT)** — 예시값 표기 정리 |
| U-10 | `PRD.md` R-12의 관찰 지점(두 채널 원본의 표준 사건 동일성)에 대응하는 MV 항목 부재 | 하 | **D4 (CONTRACT)** 또는 T07 시나리오로 흡수 |

> U-1~U-10 모두 **통과선 미달 사유가 아니다.** 어느 축도 4점 미만으로 끌어내리지 않으므로 verdict는 pass이며, 위 항목은 구현 진입 전 정정 권고다. 특히 U-1은 구현 태스크 진입 순서에 직접 영향을 주므로 T02 디스패치 전에 해소할 것을 권고한다.

---

## 5. drift 필요성

- **판정: no.** 본 리뷰가 CONTRACT의 인터페이스 변경이나 계약 범위 개정을 요구하는 지점은 없다. U-6~U-9는 **미정의 항목의 보강**(빈칸 채우기)이지 확정된 계약 조항의 변경이 아니므로, `CONTRACT.md` §5가 정의한 계약 개정 절차나 거버넌스 에스컬레이션을 발동하지 않는다.
- `profiles.json` 배정값은 §1.6 말미와 §3.3이 이미 "재스파이크이며 계약 재확정 절차를 발동하지 않는다"로 분리해 두었으므로, Phase 0 실측 결과가 어떻게 나오더라도 drift를 유발하지 않는다.
- 따라서 "## CONTRACT 거버넌스" 오너십 계층에 따른 에스컬레이션 대상 없음. 본 에이전트는 판정만 반환하며, 위 권고의 반영 여부와 방법은 PM(오케스트레이터)의 책임이다.

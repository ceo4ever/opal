---
template: sdlc-v2
---
# QA-SPEC: T02 — 구현 전 명세 리뷰 (G 게이트)

> 판정 주체: opal-evaluator-agent (생성자와 분리된 별도 에이전트 — H-9 검증 2원화)
> 판정 시점: 구현(T3) **이전**. 이 문서의 산출 시점이 test-scenario.json result 기록 시점보다 앞선다(순서 evidence).
> 판정 기준 원천: docs/run-log/CONTRACT.md §5 루브릭절 + §4 기계검증절
> 디스패치 채널: opal-agent claude/opus, readonly allowlist(Read,Grep,Glob), 원문 .oppl-run/g.result.json

## verdict: pass

## 루프 액션 에이전트의 후속 처리 판정

| finding | 등급 | 처리 |
|---|---|---|
| F-1 응답 봉투 2종 분기 (CONTRACT §2.1 서술과 기존 도구 실측 불일치) | 차단 제기 → **T02 진행 가능으로 판정** | CONTRACT §2.1은 run-log-tool의 봉투를 중첩형으로 **명시적으로 확정**하고 있으므로 신규 도구의 구현은 모호하지 않다. 미확정이던 것은 state-tool 신규 run-log 경로의 봉투 형태뿐이며, 이는 기존 err() 평면 봉투를 그대로 쓰는 것으로 T3에 지시했다(동결 테스트 보전과도 정합). **CONTRACT.md 본문 정정(§2.1의 선례 서술)은 루프 액션 에이전트의 권한 밖이므로 PM에 보고한다.** |
| F-2 D-9 마스킹 진입점 미예약 | 권고 → **수용** | T3에 직렬화 직전 pass-through 초크포인트 1개 예약을 지시했다. T06이 그 한 곳만 채운다. |
| F-3 run-log-tool.append 잔여 계약 미소유 (T03 covers 누락) | 권고 → **PM 보고** | backlog.json은 PM 단독 오너십(3-SSOT 경계)이므로 루프 액션 에이전트가 갱신하지 않는다. |
| F-4 _error_template 키 충돌 동작 미정의 | 권고 → **수용** | T3에 충돌 시 거동 명시를 지시했다. |
| F-5 S-6 RED 증거 원인 귀속 부정확 | 권고 → **기록 유지** | test-scenario.json은 locked 상태이며 red_evidence는 spec존 동결 대상이다. 인용한 단언 문구 자체는 정확하므로 정정 없이 둔다. |
| F-6 profile_not_found 템플릿 소재 | 권고 → **수용** | T3에 state-tool 쪽 소유로 지시했다. |

---

## Evaluator 원문 판정

# ⚖️ G 게이트 — 구현 전 명세 리뷰 (spec-review)

**`verdict: pass`** — CONTRACT §5 통과선(전 축 ≥4, 2점 이하 0건, RB-3·RB-4 ≥4) 충족.

실행 일시 2026-09-12 20:42 KST · `worker.dispatch` verify `ok:true`, verified_document_count=4.

---

## RB-1~RB-5 채점

| 축 | 점수 | 근거 |
|---|---|---|
| **RB-1 계약 완전성** | **4** | 사건 필수 필드를 §1.1 전건 채워 발급값·완성 소유를 행별로 명시(PLAN:52-67), `RUN_LOG_ERROR_CODES` 6종 발생 조건 확정(73-84), W-1~W-8이 함수 시그니처 수준까지 내려감. 감점: state-tool의 run-log 오류 **응답 봉투 형태 미확정**(F-1), `_error_template` 키 충돌 시 동작 미정의 |
| **RB-2 계약 일관성** | **4** | PLAN↔test-scenario↔테스트 코드의 값이 전건 일치(`cooperative`·`0001`·`sequence==1`·425/3/111). 감점: W-1이 "`state_tool.py:264-288` 패턴 복제"라 적고 실제로는 그 패턴과 다른 중첩 봉투를 지정(F-1), test-scenario S-1 `expected`에서 `completion_profile` 값만 누락(PLAN·테스트는 `cooperative` 단언) |
| **RB-3 설계 정합** | **4** | D-1(D-H)·D-2(D-E)·D-3(D-I)·D-4(D-J)·D-5(D-D)·D-6·D-7·D-8 전건이 계약 조항 또는 시나리오로 집행됨. 특히 D-5는 S-8이 **정적(소스 문자열 0건) + 동적(state.json 없는 폴더 3연속 exit 0)** 양면으로 판정 — 우회 경로 없음. 감점: **D-9(공통 마스킹 단일 경로)만 T02가 만드는 writer에 진입점조차 예약하지 않음**(F-2) |
| **RB-4 범위 준수** | **4** | 최소 구현마다 완성 소유 태스크를 인라인 명시(D-E·D-F·D-H·D-I·D-J). T03~T07 선점 0건, 비목표 유입 0건. 감점: `run-log-tool.append` 잔여 계약의 소유 태스크 부재를 H-4와 같은 축인데도 미escalate(F-3) |
| **RB-5 근거 인용 충실도** | **5** | 전 비자명 조항이 `경로:행` 또는 `문서 §절`을 달았고 PM 판정 위임분은 그렇게 표기. 인용 8건을 직접 대조했고 **전건 정확**(아래 검증 로그) |

`drift: **yes**` — F-1. 오너십 계층상 **인터페이스 변경 → 통합 게이트**. 반영은 PM 책임이며 본 에이전트는 판정만 반환한다.

---

## 지시 항목별 판정

**2. D-1·D-5·D-7·§3.2 준수 — 준수.** 우회 경로 없음. `run_log_core`의 단방향(D-5)은 설계(D-D)와 테스트(S-8) 양쪽에서 집행되며, S-8 (c)가 `state.json`이 아예 없는 빈 절대경로 폴더를 고정 입력으로 삼아 "코어가 state를 읽는 구현"을 구조적으로 통과 불가능하게 만든다. §3.2는 S-6이 3서브명령 × cwd 변경으로 판정.

**3. 범위 경계 — 선점 없음, 목으로 때우지 않음.** T03~T07 소유 영역 침범 0건. 반대 방향도 확인: 실제 `fcntl` 배타 락, 실제 2단 원자 커밋, 실제 순번 발급, 실제 subprocess CLI 호출이며 **두 테스트 파일 전체에 mock/patch/MagicMock 0건**을 실행으로 확인했다.

**4. 테스트가 계약을 판정하는가 — 그렇다.** 9 시나리오가 커버 표면 4종을 전건 덮고(S-1·S-2→`state-tool.init.run-log-mode`, S-3·S-6→`.init`, S-4·S-7→`.append`, S-5·S-8→`.validate-run`) AC-2의 세 구간(init→append→validate-run)을 끝까지 관통한다. `real-usage` 충실도는 실행으로 확인 — 전건 `subprocess.run(["bash", run.sh, …])` + 디스크 바이트 검사.

**5. RED가 self-confirming이 아닌가 — 아니다.** 재관찰했다.
- `run-log-tool` 8 failed — 전건 `bash: …/run-log-tool/run.sh: No such file or directory` (exit 127) 또는 `S-8 소스 파일 부재: run_log_core.py`. 구현 부재가 원인.
- S-1 — `state-tool: error: unrecognized arguments: --run-log-mode shadow` (exit 2). 인자 미구현이 원인.
- S-2는 **현재 GREEN** — `red_required:false` 회귀 가드로서 구현 전에 무장된 상태가 옳다.
- 결함 1건(advisory): S-6의 `red_evidence`가 실패 원인을 "require_absolute 미구현"으로 적었으나 실제 근인은 `run.sh` 부재다. 인용한 단언 문구 자체는 정확하다.

**6. C-2/C-3 우회의 성격 — 계약 회피가 아니라 정당한 경계 분리.**
- 동결 단언 4건을 직접 열어 확인: `test_error_codes_count`(`len==51`), `test_all_28_codes_registered`, README 헤더 51종, S-40 `error_codes_key_set_untouched`. **전건이 `ERROR_CODES` 키 집합·종수만 보며 `err()` 본문·외부 테이블은 보지 않는다.** D-A는 이 경계를 우회하는 게 아니라 경계 밖에 새 자산을 두는 것이다.
- 관례 근거도 실재한다 — `state_tool.py:218-223` `WARNING_CODES` 분리 주석이 *같은 이유*("ERROR_CODES 키 집합은 회귀 테스트가 HEAD와 대조해 고정")를 이미 명문화하고 있다. D-A는 그 3번째 적용이며 기존 테스트 수정 0건.
- D-B 확인: `cmd_validate`(2068-2082)는 필수 필드를 함수 내 하드코딩하며 `state.schema.json`을 **참조하지 않는다**. 관통은 스키마 파일 갱신 없이 성립하고, 반대로 갱신하면 `set(enum)=={"1.0","1.1"}`이 즉시 FAIL한다. 드리프트는 존재하되 런타임 판정에 **무해**하다.
- S-2는 실제로 회귀를 막는다 — HEAD 사본과 개정본을 같은 리프 디렉터리명·동일 조건으로 실행해 `state.json` 바이트를 비교하며, 현재 통과한다.

**7. PM 판단 필요 2건 — 둘 다 타당한 에스컬레이션, 회피 아님.**
- **H-1(state.schema.json 1.2 → T05)**: T05가 "상태 1.2 — 보관함·중단 가능 초기화"로 정확한 소유자다. 게다가 T02가 갱신하면 동결 단언 갱신을 워킹 스켈레톤에 끼워 넣게 된다. S-40 주석이 "등재 태스크가 기대값을 함께 옮긴다"를 선례로 명문화하고 있어 관례에도 부합.
- **H-4(active 3종 분기 미배정)**: `backlog.json`에서 `state-tool.init.run-log-mode`를 `covers`로 선언한 태스크는 **T02가 유일**함을 확인했다. 동시에 **C-6**("Phase 0 실측 증거 없이 어떤 채널도 active로 승격하지 않는다")과 T01 미완 때문에 T02는 active를 끝까지 구현할 수 없다. 회피가 아니라 구조적 선행 의존이다.

---

## findings

**F-1 · 차단(blocking) — 응답 봉투 2종 분기, drift 원천.** `CONTRACT.md §2.1`은 `{"ok":false,"error":{"code","message","detail"}}` 중첩 봉투를 정하면서 "기존 도구 관례를 복제한다"고 근거를 단다. 그러나 실측상 `state_tool.py:279`와 `backlog_tool.py:84`는 **평면** `{"ok":false,"command":…,"error":"<code>","message":…}`를 낸다 — §2.1이 인용한 선례를 잘못 서술하고 있다. 결과로 §2.2.1이 "전 CLI 표면 17종 공통"이라 선언한 `task_path_not_absolute`·`task_lock_timeout`이 `run-log-tool`에서는 중첩, `state-tool`에서는 평면으로 나온다. PLAN W-3은 `--run-log-mode active` → `profile_not_found` 거부만 적고 **어느 형태로 낼지 정하지 않았으며 시나리오도 없다**. → PM 조치: (a) §2.1을 두 봉투 병존으로 정정하거나 (b) state-tool 신규 경로만 중첩을 쓰도록 계약에 명기, 그리고 T02에 해당 거부 경로 시나리오 1건 추가.

**F-2 · 권고(advisory) — D-9 마스킹 진입점 미예약.** T02는 `run_log_core.append`로 디스크 쓰기 경로를 **처음** 만드는데 공통 redactor 통과 지점을 이름조차 남기지 않는다(C-8 / TRD D-9). D-9의 되돌림 비용은 "높음"이며 TRD는 "경로가 쪼개지면 보안 판정이 문구 검사로 퇴화한다"고 경고한다. → 권고: W-1의 직렬화 직전에 pass-through 초크포인트 함수 1개를 두어 T06이 한 곳만 채우게 한다.

**F-3 · 권고(advisory) — `run-log-tool.append` 잔여 계약이 미소유.** PLAN은 §1.3 조합표 전수·16 KiB 상한·provenance 증거·멱등 충돌을 "T03이 완성한다"고 적으나, `backlog.json`상 T03의 `covers`는 `show`/`import-agentic`/`import-oppl`뿐이고 **`run-log-tool.append`를 `covers`로 가진 태스크는 T02가 유일**하다. CONTRACT §4는 `covers`를 커버리지 게이트의 유일 키로 못 박으므로 MV-1·2·3·5·6이 게이트상 미소유로 남는다. H-4와 동일한 구조의 누락인데 escalate되지 않았다. → PM 조치: T03의 `covers`에 `run-log-tool.append` 가산.

**F-4 · 권고(advisory) — `_error_template` 키 충돌 동작 미정의.** D-A는 `ERROR_CODES` → `RUN_LOG_ERROR_CODES` 순 조회만 정하고 양쪽에 같은 키가 생겼을 때의 거동(선순위 침묵 채택 vs 거부)을 정하지 않는다. 테이블이 2개가 된 이상 한 줄로 명시할 값이다.

**F-5 · 권고(advisory) — S-6 RED 증거의 원인 귀속 부정확.** 위 5번 참조. 기록만 정정하면 된다.

**F-6 · 권고(advisory) — `profile_not_found` 템플릿의 소재.** `run_log_core.RUN_LOG_ERROR_CODES`에 등재되지만 그 의미(`profiles.json` 항목 부재)는 §3.1이 `state-tool` 소유로 규정한 영역이다. 메시지 템플릿뿐이라 D-5를 행위로 깨지는 않으나, 발신 도구 쪽에 두는 편이 경계와 일치한다.

---

## 검증 로그 (인용 대조 결과)

| PLAN 인용 | 대조 결과 |
|---|---|
| `state_tool.py:135-217` `ERROR_CODES` / `:218-223` `WARNING_CODES` 주석 | 정확 — 분리 사유가 D-A와 동일 |
| `:264-288` `ok`/`err` | 존재. 단 봉투 형태는 평면(F-1) |
| `:293-306` `_date_js_path` | 정확 — "형제 우선, 없으면 배포본" 관례와 그 근거 주석 실재 |
| `:1402-1405` schema_version 판정 / `:1411-1421` state dict / `:1423-1425` `--worktree` 조건부 | 전건 정확 |
| `:2068-2082` `cmd_validate` | 정확 — `state.schema.json` 미참조 확인 |
| `:3969-3991` `p_init` | 정확 — `--run-log-mode` 부재 확인 |
| `tests/test_state_tool.py:2582-2591`, `:2622-2638`, `:5461-5466`, `:9125-9159` | 전건 정확 |
| `backlog_tool.py:6` @header / `:167-197` fcntl 락 | 정확 |
| `surfaces.json` 4표면 request/response shape | PLAN·테스트 인자 집합과 일치 |

> `QA-SPEC.md`는 **생성하지 않았다** — 디스패치 프롬프트의 `금지: 파일 수정·생성 금지 (readonly)`를 AGENT.md Phase 5의 보고서 산출보다 우선 적용했다. 파일 산출이 필요하면 PM이 지시해 주기 바란다.

```json
{"artifact_path": null, "summary": "명세 리뷰 완료: verdict=pass, Likert 미달 0건, drift=yes(F-1), 차단 1건·권고 5건", "status": "completed", "verdict": "pass", "scores": {"RB-1": 4, "RB-2": 4, "RB-3": 4, "RB-4": 4, "RB-5": 5}, "drift": "yes", "blockers": [], "changed_files": []}
```

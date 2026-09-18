<!-- @header {"module":"QA-SPEC","layer":"gate-record","domain":"oppl","description":"T01 G 게이트(구현 전 명세 리뷰) 판정 기록 — opal-evaluator-agent(spec-review) verdict와 근거. 검증 2원화 순서 evidence의 timestamp 원천(verification.md §4).","task":"127-T01"} -->

# QA-SPEC — T01 실행 스켈레톤 (G 게이트: 구현 전 명세 리뷰)

| 항목 | 값 |
|---|---|
| 게이트 | G (구현 전 명세 리뷰) |
| 심판 | `opal-evaluator-agent` (phase: `spec-review`, readonly·verdict-only) |
| 생성자 | `opal-task-agent` (T1) — **심판과 분리**(H-9) |
| 판정 대상 | `PLAN.md`, `test-scenario.json`(locked, red_confirmed 8/8), RED 테스트 4파일 |
| 호출 채널 | opal-agent(claude, model=opus, allowlist=`Read,Grep,Glob`) |

---

## 시도 1 — 2026-09-12 22:41 · verdict: **fail**

증거: `.oppl-run/g.a2.events.jsonl` (시도 1은 `.oppl-run/g.result.json` exit 2 = 300초 timeout, 재호출분이 a2)

### 루브릭 채점 (CONTRACT §E, 통과선 전 축 ≥4)

| 축 | 점수 | 판정 |
|---|---:|---|
| E.1 계약 완전성 | 3 | **FAIL** — `start_frontend` 시그니처가 사전 확보 포트를 받을 수 없다 |
| E.2 계약 일관성 | 4 | PASS |
| E.3 설계 정합 | 3 | **FAIL** — 회귀 게이트 명령 2건이 실제 툴체인과 어긋나 회귀를 검출할 수 없다 |
| E.4 drift 필요성 | 4 | PASS (drift = yes) |
| E.5 컨벤션 정신 | 4 | PASS |
| E.6 아키텍처 적합 | 5 | PASS |

### 통과한 쟁점

acceptance 커버리지(6기준 → S-1~S-8 빠짐없이), 충실도 문턱(S-7의 CDP `Network.responseReceived` 관측은 `real-http` 위장이 아님), 범위 경계(T03 소유 lease record·allocator lock을 stub조차 두지 않음), 변경 0 계약(`e2e_contract.py`·`scenario.py`·`worktree-tool`·`console.sh` 무접촉, `SutStartupError` reason 집합이 `FINAL_STATUSES`와 교집합 0), 사용자 자원 불가침(`pkill -f` 0건, 7823 읽기 전용), RED 진정성(자작 통과 없음, S-4의 3 failed/2 passed는 불변 단언이므로 정상), OS 분기 단일화(`process.py` 단독).

### 치명 결함

- **[F-1] S-7의 CORS origin 주입이 실제 frontend 포트와 일치하지 않는다.**
  PLAN H-4는 "frontend 포트를 backend보다 먼저 확보"로 대응했으나, 확정 시그니처 `start_frontend(*, source_root, artifact_dir, backend_url, env_extra)`에 **포트 인자가 없다**. `start_frontend`가 내부에서 `find_free_port`를 자체 호출하면 테스트가 미리 확보한 포트는 버려지고, 브라우저는 실제 vite 포트에서 뜨므로 `Origin`이 허용 목록에 없어 CORS 차단된다. 최악의 경우 `Network.responseReceived`는 200을 보고하는데 앱 fetch는 실패한 상태로 **거짓 통과**한다.
  → 수정 방향: `start_backend`·`start_frontend`가 확보된 포트를 인자로 받도록 시그니처를 고치고, 테스트가 그 포트를 전달하도록 한다.
- **[F-2] §BLOCKED D-3(test-tool baseline 82 passed / 2 failed) 무효.**
  `run.sh:4`가 venv를 도구 인터프리터로 선언하며 `jsonschema`는 venv에만 있다. 디스패처 실측으로도 `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q` = **84 passed**. 회귀 기준선은 84 passed다.
- **[F-3] 회귀 게이트 명령 2건의 cwd·인터프리터 오류** — 저장소 루트 기준 전체 실행으로 정정 필요.

### drift (binary: yes)

- **MV-26의 문구 범위가 어떤 구현으로도 충족 불가하다.** `main.py:86`의 `allow_headers=["*"]`는 TD-7이 변경 대상에서 제외했는데 MV-26은 "CORS 설정에 `"*"` 없음"을 요구한다.
- 오너십 계층: **#2 내부 조정**(기계검증절 문구 범위 명확화, 외부 노출·인터페이스 변경 없음) → PM 자율 반영 대상.
- 권고 문구: MV-26의 `"*"`·정규식 금지 대상을 `allow_origins`·`allow_origin_regex`로 명시 한정.
- Evaluator·루프 액션 에이전트 모두 CONTRACT.md를 수정하지 않았다.

### 권고 (A-1~A-5)

- **A-1** S-7의 `skipTest`가 문턱 미달을 침묵시킨다 — skip을 hard fail로 승격하거나 `executor_unavailable`을 결과에 기록할 것.
- **A-2** S-2의 typecheck·build 절반이 자동 검증에 묶여 있지 않다 — `--outDir` 빌드를 S-2 판정 절차에 묶을 것.
- **A-3** RED 기간에는 import-level 실패가 수집을 중단시켜 기준선 측정이 불가 — `--ignore`가 필요함을 절차에 명시.
- **A-4** S-8의 회수 검증이 그룹 리더 1건에 그친다 — `terminate_process_group`이 잔존 구성원을 실제 집계하도록 구현 계약에 명시.
- **A-5** S-7의 `Runtime.evaluate` DOM 확인이 PLAN에만 있고 구현물·시나리오 본문에 없다 — 문구를 맞추거나 단언 추가.

---

## 시도 2 — 2026-09-12 23:07 · verdict: **pass**

증거: `.oppl-run/g.a3.events.jsonl`. 재작업 내역: PLAN.md 갱신(T1 warm resume) + RED 테스트 정렬(T2 재작업).

### 루브릭 채점 (전 축 ≥4 → pass)

| 축 | 1회차 | 2회차 |
|---|---:|---:|
| E.1 계약 완전성 | 3 | **4** |
| E.2 계약 일관성 | (통과) | **5** |
| E.3 설계 정합 | 3 | **4** |
| E.4 drift 필요성 | yes | **yes (5)** |
| E.5 컨벤션 정신 | (통과) | **5** |
| E.6 아키텍처 적합 | (통과) | **5** |

### 치명 결함 해소 판정

- **F-1 해소** — 거짓 통과 경로가 구조적으로 닫혔다. D-11(`port` 필수 키워드 인자, 내부 `find_free_port` 호출 금지) + D-12(순서 ①~⑤) + [MUST] "③ origin 포트 == ⑤ vite 바인딩 포트 == ① 같은 정수". 테스트가 `fe_port`를 실제로 `start_frontend`에 전달한다. 테스트 로컬 헬퍼 `_start_backend(port=, cors_origin=)`은 `env_extra={"OPAL_CONSOLE_CORS_ORIGINS": ...}`로 변환해 PLAN 시그니처 그대로 호출 — 인터페이스 어긋남 없음.
- **F-2 해소(재측정은 T4a로 이월)** — D-3 "취소(무효) — 인터프리터 선택 오류", baseline 84 확정. 근거 `opal/tools/test-tool/run.sh:4` `VENV_PYTHON="$HOME/.opal/.venv/bin/python"` 직접 확인. Evaluator는 readonly라 84를 독립 재측정하지 못했다.
- **F-3 실질 해소** — 인터프리터 venv 고정·H-6 판정 기준 교체 완료. 잔존분은 F-4.

### 새로 식별된 결함 (비차단)

- **[F-4] 회귀 게이트 블록에 cwd 누수 잔존.** 결과가 **거짓 실패**(조사·수정 유발)이지 F-1 같은 거짓 통과가 아니며 한 줄로 끝난다 → 블록에 `cd "$(git rev-parse --show-toplevel)"` 추가로 해소.

### A-1~A-5 반영

전건 반영. A-1은 **기본 경로가 `self.fail(...)`**이고 `OPAL_E2E_ALLOW_NO_BROWSER=1`일 때만 skip으로 강등되며 양쪽 모두 `executor_unavailable`을 남긴다 — skip이 기본으로 남아 있지 않다.

### 1회차 통과 쟁점 재확인 (재작업으로 깨지지 않음)

T03 경계(`ports.py`에 lock·lease record stub조차 없음), 변경 0 계약, 사용자 자원 불가침(7823 `urlopen` 1회 읽기 전용), OS 분기 단일화(테스트에 `sys.platform`·`os.name`·`platform.system()` 0건), RED 진정성(`test-scenario.json` locked·8/8 red_confirmed 변경 없음), 충실도 문턱(D-17이 침묵 경로를 차단해 오히려 강화).

### drift 판정

**#2 내부 조정 — 타당.** `surfaces.json` 무변경, 시그니처·스키마 무변경, T02~T09 계약 소비 방식 무변경. 실체적 근거: `CONTRACT.md` §C.8 "보안 경계의 실체"가 `allow_headers`를 꼽지 않고, §C.9 전개 규칙이 origin 축만 다룬다. **반영 주체는 PM이다.**

### 잔여 권고 (비차단, T3 반영 권장)

- **A-6** `int(frontend.url.rsplit(":",1)[-1])`는 `SutHandle.url`이 `port`에서 조립되므로 사실상 항진 단언 — 동일성의 실제 보증은 D-13 strict-port다. 더 강하게 하려면 vite stdout의 `Local: http://127.0.0.1:<port>` 실측치를 파싱할 것.
- **A-7** `MAX_PORT_ATTEMPTS` 소진 시 `SutStartupError(reason="port_bind_exhausted")`를 올리는 주체(호출자 vs `runtime`)를 §모듈 분해 표에 한 줄로 확정할 것.
- **A-8** `test_e2e_skeleton.py`의 "(start_backend 내부에서 wait_healthy)" 주석이 사실과 다르다 — 주석만 정정.

---

## 검증 2원화 순서 evidence

- G(구현 전) 완료: 2026-09-12 23:14 — 이 파일의 시도 2 verdict `pass`
- T4a(구현 후) 결과 기록: `test-scenario.json` result존 `marked_at` (이 시각 **이후**)

<!-- @header {"module":"DONE","layer":"task-record","domain":"oppl","description":"T01 실행 스켈레톤 완료 기록 — 파이프라인 경과·변경 파일·검증 결과·시나리오 판정·PM 판정 대상 잔여 항목.","task":"127-T01"} -->

# DONE — T01 실행 스켈레톤

> 주소 주입·CORS 포함, 임대 포트로 Console BE/FE를 소스 트리에서 기동하고 FE→BE 실 호출 1건을 관통.

| 항목 | 값 |
|---|---|
| task_id | `T01` |
| area | `공통` |
| 요구 충실도 | `real-usage` — **충족**(`scenario-fidelity-check all_met=true, 8/8`) |
| 시나리오 | 8/8 pass (fail 0 · blocked 0 · awaiting_human 0) |
| 회귀 | 0건 |
| blocker | 없음 |

---

## 파이프라인 경과

| 단계 | 축 | 결과 |
|---|---|---|
| T1 명세·설계 | 생성자(`opal-task-agent`, cold prime) | PLAN.md 산출. §BLOCKED 5건(판정 필요 드리프트) |
| T2 RED 시나리오 | `opal-test-agent`(mode: red) | 테스트 4파일. RED 8/8 실관찰 → `scenario-red` 8건 → `scenario-lock` |
| **G 명세 리뷰 ①** | `opal-evaluator-agent`(spec-review) | **fail** — E.1=3, E.3=3. F-1·F-2·F-3 |
| T1 재작업 | 생성자(warm resume) | F-1(포트 확보 책임 호출자 이관)·F-2·F-3 + A-1~A-5 + drift 오너십 분류 |
| T2 재작업 | `opal-test-agent` | 호출 순서 계약 ①~⑤ 정렬, 포트 동일성 단언 추가 |
| **G 명세 리뷰 ②** | `opal-evaluator-agent` | **pass** — 전 축 ≥4 (E.1 3→4, E.3 3→4, 나머지 5) |
| T3 구현 | 생성자(warm resume) | 구현 9파일. 1회 시도로 전건 GREEN |
| T4a 테스트 | `opal-test-agent`(독립 검증) | S-1~S-8 전건 pass, 회귀 0, 누출 0 |
| T4b 규칙검사 | conv + sec checker | **blocker 0** / major 2 / minor 7 → major 2건 수정 완료 |

**검증 2원화 순서 evidence**: `QA-SPEC.md`(G 완료 2026-09-12 23:14) < `test-scenario.json` result `marked_at`(23:3x). 생성자≠평가자(H-9)를 전 구간 유지했다.

---

## 변경 파일

**수정 (2)**
- `dashboard/frontend/src/lib/api.ts` — `API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""`. `7823` 리터럴 제거, base에 `/api` 접두사 없음(MV-24)
- `dashboard/backend/main.py` — `_DEFAULT_DEV_ORIGINS` + `_parse_extra_origins(os.getenv("OPAL_CONSOLE_CORS_ORIGINS"))`. `CORS_ORIGINS` 심볼 유지(`tests/test_main.py:80-93` 소비자 보존)

**신설 (10)**
- `dashboard/frontend/src/vite-env.d.ts` · `dashboard/frontend/.env.development` (MV-25)
- `opal/tools/test-tool/lib/e2e/{__init__,ports,process,runtime}.py` (478줄)
- `opal/tools/test-tool/tests/test_e2e_skeleton.py` (S-5~S-8)
- `dashboard/backend/tests/test_cors_env.py` (S-4)
- `dashboard/frontend/src/lib/{api-base-url,api-env-files}.test.ts` (S-1·S-2·S-3)

---

## 시나리오 판정

| id | 수용기준 | required | 실제 충실도 | 결과 |
|---|---|---|---|---|
| S-1 | 1 | mock | mock | pass |
| S-2 | 1 | mock | mock | pass |
| S-3 | 2 | mock | mock | pass |
| S-4 | 3 | mock | mock | pass |
| S-5 | 4 | real-http | real-http | pass |
| S-6 | 3 | real-http | real-http | pass |
| **S-7** | **5** | **real-usage** | **real-usage** | **pass** |
| S-8 | 6 | real-http | real-http | pass |

### S-7 real-usage 증적 (독립 재관측)

Playwright(패키지·MCP)는 사용 불가였다 — MCP 프로파일을 타 세션이 점유 중이고 그 Chrome은 사용자 소유라 C-2로 종료할 수 없다. 대신 **이미 디스크에 있는 `chrome-headless-shell`을 CDP로 직접 구동**했다(패키지 설치 0건, 격리 프로파일).

```
fe_port(CORS 주입)=50015  ==  vite 실제 바인딩=50015
backend=http://127.0.0.1:50016  frontend=http://127.0.0.1:50015
CDP Network.responseReceived = {"url":"http://127.0.0.1:50016/api/dashboard","status":200}
cdp_returncode=0 · stop_all leaked=[]
```

`OPAL_E2E_ALLOW_NO_BROWSER` 미설정 = hard fail 경로 유지, `-rs` 확인 **skip 0건**. 호출 순서 계약 ①~⑤가 "주입 origin 포트 == vite 바인딩 포트"를 강제해, CDP는 200인데 앱 fetch는 CORS 차단되는 **거짓 통과**를 구조적으로 차단한다(G 1회차 F-1의 수정 결과).

---

## 검증 결과

| 명령 | 결과 |
|---|---|
| `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests -q -rs` | **88 passed, skip 0** (baseline 84 + 신규 4) |
| `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests -q` | 345 passed / **36 failed**(사전 존재, T01 무관 — 증가 0). `test_cors_env.py` 5/5 GREEN |
| `npx vitest run` | 161 passed (12 files) |
| `npm run typecheck` | exit 0 |
| `npm run build -- --outDir "$TMPDIR/..." --emptyOutDir` | exit 0, 저장소 `dist/` 미생성 |
| `git status --porcelain` 전후 | **IDENTICAL** (MV-28) |
| 사용자 `127.0.0.1:7823` Console | 200 → 200 불변 (읽기 전용 접촉만) |

기계검증절: MV-24·MV-25·MV-26·MV-27·MV-28 충족. `pkill`/`killall`/`pgrep` **0건**, OS 조건문은 `lib/e2e/process.py:47` **1건뿐**(MV-20), `console.pid` 참조 0건(MV-22), 바인딩은 `127.0.0.1` 명시.

**범위 경계**: `ports.py`는 `find_free_port` + `MAX_PORT_ATTEMPTS`만 갖는다. allocator lock·lease record·stale 회수·worktree 동시성(§A.7, C-LEASE-1/2, MV-36)은 **T03 소유이며 stub조차 두지 않았다**.
**변경 0 계약**: `e2e_contract.py`·`scenario.py`·`worktree-tool/**`·`opal-cli/lib/console.sh` diff 0.

---

## 실행 중 발견·해소한 누출 1건

T3 중간 시도(구현자가 `terminate_process_group`의 좀비 reap·`PermissionError` 버그를 고치기 **전**)가 남긴 고아 프로세스 그룹 1건(`pgid 51501` = `npm run dev` → vite `:62535`, PPID=1)을 최종 확인에서 발견했다.

- **현행 코드는 누출하지 않는다** — S-7+S-8 재실행 전/후 vite·npm 프로세스 집합이 동일하고 `chrome-headless-shell` 잔존 0건임을 확인했다(완료 기준 6 유지).
- 고아는 프로젝트 **자체 모듈** `lib.e2e.process.terminate_process_group`으로 회수했다: members `[51501, 51591]` → `[]`, `TerminationResult(released=True, method='sigterm', leaked=[])`. 이름 패턴 종료 미사용, 사용자 7823 Console 불변.
- 부수 효과로 **npm→vite 손자 회수(RK-3)가 실증**되었다.

---

## PM 판정 대상 (차단 아님)

1. **[drift #2 내부 조정] MV-26 문구가 어떤 구현으로도 충족 불가하다.**
   `main.py:86`의 `allow_headers=["*"]`는 TD-7이 변경 대상에서 제외했는데 MV-26은 "CORS 설정에 `"*"` 없음"을 요구한다. Evaluator가 **오너십 계층 #2(외부 노출·인터페이스 변경 0) → PM 자율 반영 대상**으로 분류했다.
   권고 문구: MV-26의 `"*"`·정규식 금지 대상을 **`allow_origins`·`allow_origin_regex`로 명시 한정**. 구현·테스트는 이 해석(origin 축 한정)으로 진행했다. **CONTRACT.md는 수정하지 않았다.**

2. **`scenario-conformance`가 exit 14 `surface_unverified` 38건을 반환한다 — T01 defect 아님.**
   분모가 프로젝트 전체 `surfaces.json`(40건)이고 미검증 38건은 T02~T09 소유다(`e2e-*`·`console-*`·`driver-*`·`api-executor-*`·`human-executor-*` 및 나머지 `sut-*` 15건). T01이 참조한 2표면은 전부 문턱 이상 green이다:
   - `sut-health` ← S-5·S-6 (`real-http`)
   - `sut-dashboard` ← S-7 (`real-usage`)
   게이트에 태스크 스코핑 인자가 없어(`--task-path`/`--surfaces`만) 재작업으로 해소 불가하다. 이 프로젝트에서는 **T09 완료 시점에만 green**이 되므로, 태스크별로는 backlog `covers` 기준 판정이 필요하다.

3. **backlog `covers` 갱신 필요.** T01 `covers`는 `["sut-health"]`이나 완료 기준 5가 "FE 화면에서 발생한 호출"을 요구하고 FE 루트가 실제 호출하는 것은 `GET /api/dashboard`다(`DashboardPage.tsx:1170-1177`). S-7이 `sut-dashboard`를 관통했으므로 **T01의 실제 커버 표면은 2건**이다. `surfaces.json`은 읽기 전용으로만 소비했고 수정하지 않았다.

4. **환경 전제 정정** — `opal/tools/test-tool` baseline은 **84 passed**다. "82 passed / 2 failed"는 `jsonschema`가 없는 system `python3`로 측정한 값이며, 도구 SSOT 인터프리터는 `~/.opal/.venv/bin/python`이다(`opal/tools/test-tool/run.sh:4`). backend 기동·전 pytest가 이 인터프리터를 쓴다.

5. **워크트리 환경 조치(기록용)** — 워크트리에 `dashboard/frontend/node_modules`가 없어 main 체크아웃 설치본으로 **심볼릭 링크**했다. 패키지 설치 0건이고 `node_modules`는 `.gitignore` 대상이라 MV-28에 영향이 없다.

## 잔여 권고 (비차단)

T4b minor 7건(`depends` 필드 보강, `Optional[str]`↔`str | None` 표기 혼용, `method="noop"` 죽은 대입, origin 정규식의 userinfo 통과 등)과 G 게이트 A-6·A-8(항진 단언 강화, 주석 1줄 정정)은 미조치 상태로 남겼다. 전부 advisory이며 계약·판정에 영향이 없다.

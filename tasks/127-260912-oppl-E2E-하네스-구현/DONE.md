# DONE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

## 결과

`docs/proposals/opal-e2e-harness.md`가 정의한 9개 구현 태스크 중 남아 있던 7개를 구현했다. 착수 시점의 문제는 **판정 계약과 최소 실행 환경은 있으나 그것을 집행할 실행 주체가 없다**는 것이었다 — `e2e_adapter.py:217-225`가 `assertion_results: []`로 `build_verdict`를 호출해 구조적으로 `pass`를 낼 수 없었고, `test_tool.py`에는 `e2e` 서브파서 자체가 없었다.

**새로 생긴 것**

- `test-tool e2e` 4서브명령 — `run`·`resume`·`status`·`clean`. 기존 4서브명령(`resolve`·`check`·`unit`·`integration`)은 인자·exit 계약 무변경.
- `lib/e2e/` 실행 계층 — target 3종 해석(`source-main`/`source-worktree`/`installed`), allocator lock·lease record·stale 회수를 갖춘 포트 임대, SUT 기동·health gate, §A.2.1 상태 전이.
- `drivers/` — `agent-browser`(orca-managed·standalone)·`cmux`의 §B.2 8연산, 버전 게이트 매니페스트, 후보 레지스트리.
- `executors/` — `api`(실 SUT HTTP)·`human`(handoff·resume·timeout).
- `evidence.py` + `redaction.py` 증적 단일 관문 — 저장 전 `Authorization`·`Cookie`·`Set-Cookie`·query secret 마스킹, 실패 시 원문 미보존·`infra_error`.

**함께 닫은 안전 결함**

`opal-cli console stop`이 PID 레코드의 `started_at`을 부팅 시각과 비교하지 않아, 리부팅 후 PID가 재할당되면 무관한 사용자 프로세스를 종료할 수 있었다. `scripts/install-mac.sh`가 이 경로를 무인 호출하므로 **리부팅 후 첫 설치가 임의 사용자 프로세스를 죽일 수 있는 상태**였다. 부팅 이전 레코드를 stale로 판정해 종료하지 않고 레코드만 정리하도록 고쳤다(파싱 실패는 fail-open, 신규 reason 토큰 0).

**정리한 것**

- Playwright가 기본 설치에서 빠지고 opt-in으로 전환됐다. clean install에서 Chromium 다운로드 0회. 기존 사용자 캐시는 삭제하지 않는다(566MB 실 캐시로 확인, 359파일 → 359파일 불변).
- `real-usage` 정의가 `lib/scenario.py:119` `FIDELITY_ORDER` 한 곳으로 수렴했다. 파이프라인 문서는 참조만 한다.

**유지한 경계**

- `lib/e2e_contract.py`·`lib/scenario.py` **변경 0**(C-1) — 태스크 125가 확정한 profile·final status 5종·exit code 계약을 소비만 했다.
- 사용자 소유 자원 미접촉(C-2) — `EXCLUDED_PORTS=(7823,)`, `owned.json` 대장 자원만 회수, `user_owned=true`는 `skipped[]`, `pkill`·`pgrep`·`killall` 0건.
- 산출물은 OS 임시 경로 또는 `OPAL_E2E_ARTIFACT_DIR`에만(C-5). OS 분기는 `lib/e2e/process.py` 한 곳(C-7).

## 변경 파일

- `opal/tools/test-tool/test_tool.py` · `lib/resolver.py` · `lib/e2e_adapter.py` · `README.md`
- `opal/tools/test-tool/lib/e2e/` — `orchestrator.py` · `target.py` · `ports.py` · `evidence.py` · `redaction.py` · `scenario_adapter.py`
- `opal/tools/test-tool/lib/e2e/drivers/` — `__init__.py` · `agent_browser.py` · `cmux.py` · `manifest.json`
- `opal/tools/test-tool/lib/e2e/executors/` — `__init__.py` · `api.py` · `human.py`
- `opal/tools/test-tool/tests/` — 신규 19건(동결 RED 10 + 구현 검증 9)
- `opal/tools/opal-cli/lib/console.sh` · `README.md`
- `scripts/install-mac.sh` · `scripts/install/windows.ps1` · `scripts/tests/test_console_ownership.sh`
- `opal/tools/requirements.txt` · `opal/tools/doctor/{lib/checks.sh,run.sh,README.md}` · `dashboard/backend/tests/test_doctor_adapter.py`
- `opal/templates/test-tools.yaml` · `opal/core/references/{test-tools-schema.yaml,agents.md,mcps.md}` · `opal/tools/tool-scan/tests/test_tool_scan.py`
- `opal/skills/opal-pilot-project-loop/references/verification.md` · `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` · `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/agents/opal-test-agent/AGENT.md` · `personas/test-engineer.md`
- `docs/ARCHITECTURE.md` · `docs/CONVENTIONS.md` · `docs/PROJECT.md`
- `docs/proposals/e2e-journey-fragment-library.md` (태스크 범위 밖 산출물 — 미적용 제안)

## 검증

- `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q` → **424 passed / 0 failed**(330 subtests)
- `bash scripts/tests/test_console_ownership.sh` → **23 PASS / 0 FAIL — ALL PASS**
- `grep -Ec '\b(pkill|pgrep|killall)\b' console.sh install-mac.sh` → **0 / 0**
- `git diff --stat lib/e2e_contract.py lib/scenario.py` → **빈 출력**(C-1)
- vitest **131 passed** — 161 미달이나 main 상속(`710800d`가 `WorkbenchApp.test.tsx` 30케이스 삭제, 131+30=161). 이 태스크는 9케이스를 추가했다.
- RED-first: 동결 11건 전건 GREEN(`locked: true`, `red_confirmed_required 11/11`)
- `scenario-conformance`: 미검증 표면 **40 → 19**

**AC 판정: 충족 15 / blocked 1 / 미충족 0.** AC별 근거와 실행 출력은 `VERIFY-AC.md`가 소유한다.

- AC-4는 실 Orca 브라우저로 관통했다 — `fidelity: real-usage`, 실제 DOM 값으로 판정(`title 'OPAL Console'`, `eval '"대시보드"'`), 소유 page 1건만 정리되고 사용자 `default` 세션·Chrome 프로필 5종 불변.
- AC-9는 전 구간 관통했다 — `awaiting_human`·exit 20 → 동일 run-id·resume token 재개 → `submission.completed: true`인데도 `fail`(사람 제출 단독으로는 `pass` 불가, R-13).
- AC-12는 blocked다 — `console_autostart()`의 7823 하드코딩과 `install_dashboard()`의 소스 트리 `dist/` 쓰기 때문에 격리 install이 성립하지 않는다. Console 소유권 모델 재작업은 `TASK.md` §Affected의 **제외 항목**이다.

## 회고적 학습 후보

.opal/brain/pages/concept/e2e-integration-gap-pattern.md
.opal/brain/pages/concept/e2e-frozen-spec-seeding-constraint.md
.opal/brain/pages/decision/e2e-candidate-order-and-fidelity-ownership.md

## 참고

**이월 5건** — 전부 이 태스크 범위 밖이거나 계약상 수정 불가로 판정했다. 상세 근거는 `STATE.md` 블로커 표와 `VERIFY-AC.md`가 소유한다.

| # | 항목 | 사유 |
|---|------|------|
| B-1 | `tool-scan` 4건 실패 | main 상속 — 태스크 131 W-16이 `opal/core/AGENT.md` 인지맵 구조를 제거했다. 고치려면 playwright fallback 산문을 되살려야 해 AC-14와 정면 충돌한다 |
| B-2 | `opal-cli mcp add playwright`가 설치본에서 실패 | `mcp.sh:59,113`이 install이 만들지 않는 `~/.opal/opal/core/mcps`를 참조한다. 선행 결함 |
| B-4 | AC-12 격리 install 불성립 | 위 참조. 범위 제외 항목 |
| B-5 | `scenario-conformance` `all_surfaces_green` 미달 | S-10·S-40~S-44·S-7이 `profile:"api"` + `required_fidelity:"real-usage"`인데 api profile 충실도 상한은 `real-http`다. 동결 spec도 `e2e_contract.py`(C-1)도 수정 불가 — PM의 초기 시드 오류이며 도구 결함이 아니다 |
| B-6 | `cleanup.json` 거짓 보고 | `complete`/`leaked:[]`를 보고하고도 프로세스가 남는다. 대장이 거짓이면 수동 회수가 소유권 없이 PID만 보고 판단하게 된다 |

**후속 제안**: `docs/proposals/e2e-journey-fragment-library.md` — `//e2e` operator와 여정·조각 라이브러리. 이 태스크에서 실측된 두 제약(동결 후 시나리오 추가 불가 · 발동층 부재)이 근거다.

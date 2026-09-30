# ADD_DONE-1: opd2 Builder 전문 에이전트 라우팅 + 컨벤션 문서 주입 보정

## 추가작업 번호

ADD-1

## 일시

- 시작: 2026-10-01 07:22 (KST)
- 완료: 2026-10-01 07:33 (KST)

## 사유

원본 DONE.md 작성 후 사용자와의 대화 중 두 가지 설계 빈틈이 드러났다.

1. opd2의 worker.dispatch 절차가 Builder/Verifier/Reviewer 모두를 무조건 `opal-task-agent`로만 디스패치했다 — opd처럼 `docs/PROJECT.md` "프로젝트 구성"과 파일 경로를 매칭해 FE/BE/DB 전문 에이전트를 선택하는 라우팅이 없었다.
2. 어떤 역할에도 프로젝트 컨벤션 문서(`docs/CONVENTIONS.md` 등) 주입이 보장되지 않았고, `pipeline.json`에 컨벤션 자동 진단을 강제하는 gate도 전혀 없었다(opd의 `test.pm_gate`에 있는 것과 달리).

사용자가 검토 후 "추가 작업으로 해줘"로 명시 승인했다.

## 변경 내용

1. `agents/coordinator.md` — 디스패치 직전 `dispatch-process.md` §Step 1~3(프로젝트 문서 선별)을 수행하도록 명시. Builder 디스패치는 추가로 §Step 4에 따라 `plan.files`를 `docs/PROJECT.md` "프로젝트 구성"과 매칭해 `opal-fe-agent`/`opal-be-agent`/`opal-db-agent`를 우선 선택하고, 매핑이 없거나 `docs/PROJECT.md`가 없으면 `opal-task-agent`로 폴백하도록 추가. Verifier/Reviewer는 계약(`lifecycle.py collect-evidence`·리뷰 판정)이 FW 전문 에이전트와 매핑되지 않아 계속 `opal-task-agent`를 쓰도록 명시.
2. `agents/builder.md` — 입력 목록에 "PM(Coordinator)이 선별한 프로젝트 문서(컨벤션·아키텍처 등)" 추가.
3. `SKILL.md` — worker.dispatch 게이트 절에 "Coordinator가 매 디스패치 전 §Step 1~4를 수행한 뒤 디스패치한다" 추가. 기존에 남아 있던 모순 문장("등록된 FW 워커는 항상 opal-task-agent다... FE/BE/DB 도메인 매핑이 없는 범용 변경 파일럿")을 위 1번과 일치하도록 정정(Builder는 라우팅 대상, Verifier/Reviewer만 항상 opal-task-agent).
4. `references/pipeline.json` — `verify.review` 행(id 9)에 `gate` 추가: `artifacts: ["run/opd2-ledger.json"]`, `checklist: ["컨벤션 자동 진단 PASS (GC-CONVENTION-*.md Critical/High 0건 — 컨벤션 적용 대상 ≥1건 시 발동)"]`. opd의 `test.pm_gate`와 동형의 안전망을 VERIFY 완료 직전에 추가.

## 변경 파일

- `opal/skills/opal-pilot-dev2/agents/coordinator.md`
- `opal/skills/opal-pilot-dev2/agents/builder.md`
- `opal/skills/opal-pilot-dev2/SKILL.md`
- `opal/skills/opal-pilot-dev2/references/pipeline.json`

## 검증 결과

- `python3 opal/tools/state-tool/state_tool.py spec-validate opal/skills/opal-pilot-dev2/references/pipeline.json` → `ok:true, violations_count:0`.
- `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests -v` → 31 tests, OK(회귀 없음 — 이번 변경은 전부 스킬 문서·설정이라 코드 동작 무영향).
- `~/.opal/.venv/bin/python -m pytest -q opal/tools/state-tool/tests/test_pilot_shared_contract.py opal/tools/state-tool/tests/test_opd2_gate_mark_guard.py` → 23 passed, 169 subtests passed.
- PM Gate 문서검증(opd 추가작업 오버라이드 — 전체 테스트 스위트 + 문서검증): 4개 파일 diff 전수 확인, Builder/Verifier/Reviewer 라우팅 서술이 `coordinator.md`·`SKILL.md`·`builder.md` 간에 모순 없이 일치함을 확인. `git status --porcelain`으로 변경 범위가 이 4개 파일에 정확히 한정됨을 확인.

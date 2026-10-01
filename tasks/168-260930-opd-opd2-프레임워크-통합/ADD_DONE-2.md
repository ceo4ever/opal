# ADD_DONE-2: opd2 PLAN 사전심사(결정론+병렬 추론) + agents model frontmatter

## 추가작업 번호

ADD-2

## 일시

- 시작: 2026-10-01 08:46 (KST)
- 완료: 2026-10-01 09:15 (KST)

## 사유

사용자와의 설계 대화에서 "opd2는 opd보다 빠르고 품질은 유지"라는 목표가 확정됐다. opd의 설계 게이트(독립 evaluator 반복 루프)를 그대로 가져오면 속도 이점이 사라지므로, (1) 결정론 검사로 값싼 실패를 먼저 거르고, (2) 통과 시에만 추론이 필요한 검사를 **병렬**로 실행하며, (3) 재시도 시 실패한 축만 표적 재검증하는 구조를 설계해 사용자 승인을 받았다. 추가로 Builder/Verifier/Reviewer의 model을 역할별로 제어 가능하게 해달라는 요청을 받았다(effort는 `Agent` 도구 스키마에 파라미터 자체가 없어 이번 범위에서 제외 — 별도 FW 에이전트 승격이 필요함을 사용자에게 설명하고 model만 진행 승인받음).

## 변경 내용

1. **Layer 1(결정론 게이트, LLM 없음)**: `plan.json`에 신규 필수 필드 `ac_coverage`(배열의 배열 — `checks[i]`가 커버하는 `intent.acceptance` 인덱스 목록) 추가. `lifecycle.py`의 `Store.plan_coverage()`가 전체 `acceptance` 인덱스가 커버됐는지 즉시(밀리초 단위) 검사하고, 미달이면 Reviewer를 부르기도 전에 거부한다.
2. **Layer 2(추론 게이트, 병렬)**: PLAN→BUILD 전이에 독립 Reviewer의 **Call A**(요구 충분성·위험 신고 적절성·미결 질문 실질 해소)와 **Call B**(범위 적절성·실행가능성/RED 적용)가 모두 현재 fingerprint에서 `verdict: pass`로 기록돼 있어야 한다는 요건을 추가. `lifecycle.py review <task> --call {A,B} --verdict {pass,fail} --reason ... --actor <plan.reviewer>`로 기록하며, 신원(`actor==plan.reviewer, actor!=plan.builder`)이 다르면 거부. `--force`/`--auto-pass`류 우회 없음(기존 게이트와 동일하게 저장 전 판정).
3. **표적 재검증**: `agents/coordinator.md`에 "Call A/B를 한 메시지에서 병렬 디스패치, 실패한 Call만 재디스패치(통과한 Call은 재사용)" 절차 명시. 재시도 상한은 opd2 기존 `retries<=3`을 공유(신규 카운터 없음).
4. **model frontmatter**: `agents/builder.md`·`agents/verifier.md`는 `model: standard`(opal-be/fe/test-agent와 동급), `agents/reviewer.md`는 `model: advanced`(opal-evaluator-agent와 동급 — 판단·심사 역할이라 이번에 PLAN 사전심사까지 맡으며 더 중요해짐). `SKILL.md`에 "Coordinator가 이 frontmatter 값을 `opal-model-mapping.md`로 변환해 디스패치에 전달한다"는 지시 추가(플랫폼 분기 없음, 원문 비복제).
5. **rewind 정합**: `plan_reviews`도 기존 `evidence`/`reviews`/`approvals`와 함께 rewind 시 초기화되도록 반영.

## 변경 파일

- `opal/skills/opal-pilot-dev2/schemas/plan.schema.json`
- `opal/skills/opal-pilot-dev2/templates/plan.json`
- `opal/skills/opal-pilot-dev2/scripts/lifecycle.py`
- `opal/skills/opal-pilot-dev2/agents/reviewer.md`
- `opal/skills/opal-pilot-dev2/agents/coordinator.md`
- `opal/skills/opal-pilot-dev2/agents/builder.md`
- `opal/skills/opal-pilot-dev2/agents/verifier.md`
- `opal/skills/opal-pilot-dev2/SKILL.md`
- `opal/skills/opal-pilot-dev2/tests/test_lifecycle.py`

## 검증 결과

- `python3 opal/tools/state-tool/state_tool.py spec-validate opal/skills/opal-pilot-dev2/references/pipeline.json` → `ok:true, violations_count:0`(이번 변경과 무관함 재확인).
- `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests -v` → **36 tests, OK**(기존 31 + 신규 5건: ac_coverage 누락 거부, call A/B 개별 누락 거부, 잘못된 actor 거부, rewind 시 plan_reviews 초기화). 기존 기계 게이트(해시 체인·범위·evidence·역할분리·RED-first·retries≤3) assertion 전건 유지.
- `~/.opal/.venv/bin/python -m pytest -q opal/tools/state-tool/tests/test_pilot_shared_contract.py opal/tools/state-tool/tests/test_opd2_gate_mark_guard.py` → 23 passed, 169 subtests passed(공유 인프라·ADD-1 가드 회귀 없음).
- 배치1 워커가 임시 디렉터리에서 7단계 수동 스모크 테스트로 Layer 1/2 게이트·신원 검사·rewind 무효화를 실측 확인(uncovered acceptance 거부 → 커버리지 수정 → call A 없이 거부 → call A 기록 → call B 없이 거부 → 잘못된 actor 거부 → call B 기록 후 전이 성공 → rewind로 plan_reviews 초기화 확인).
- PM Gate 문서검증: `agents/*.md`·`SKILL.md`의 서술이 `lifecycle.py` 실제 CLI 계약과 정확히 일치함을 diff로 확인. 플랫폼 분기 미포함, 원문 복제 없음(참조만) 확인.

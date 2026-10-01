# 자체 상태관리 파일럿을 SSOT로 편입할 때 동형 가드 패턴을 재사용한다

- 유형: architecture
- 상태: candidate
- 기록일: 2026-10-01

## 내용

태스크 168(opd2 프레임워크 통합)에서, 자체 journal(`.sdlc/`)로 상태를 관리하던 파일럿(opd2)을 `state-tool`의 `state.json` 단일 SSOT로 옮기면서 "PM이 게이트를 건너뛰고 행을 완료할 수 없다"(--force로도 우회 불가)는 요건이 나왔다. `lifecycle.py` 내부에서만 게이트를 검사하면 PM이 그 스크립트를 거치지 않고 `state-tool mark --force`를 직접 호출해 뚫을 수 있다는 결함을 독립 설계 평가자(design-rubric)가 iteration 2에서 지적했다.

해법은 새 메커니즘을 설계하지 않고, `state_tool.py`에 이미 있던 `apply_scenario_gate_mark_guard()`(opd/opds의 `test_scenario.scenario_gate`/`plan.scenario_gate` 키 전용, 형제 CLI를 호출해 실패 시 `--force`로도 못 뚫는 패턴)와 정확히 같은 시그니처·호출 위치로 `apply_opd2_gate_mark_guard()`를 추가하는 것이었다. 이 패턴은 (1) `skill=="X"`이고 (2) 대상 `row.key`가 그 파일럿 전용 키 집합에 속할 때만 동작해, 다른 파일럿의 행 구성·전이 동작을 전혀 건드리지 않는다.

이 확장이 TASK.md의 문자 그대로 범위("state-tool 변경은 식별자·신규 기본값 등록으로 한정")를 넘어서는 결정이었으므로, PM이 임의로 결정하지 않고 세션 중 사용자에게 직접 확인해 승인받았다(AskUserQuestion, 2026-09-30 23:20).

## 일반화

- FW 공통 도구(`state-tool` 등)에 파일럿 전용 우회 방지 가드가 필요하면, 이미 있는 동형 가드(`apply_scenario_gate_mark_guard` 등)를 찾아 같은 스코프 한정 조건(`skill==` + 전용 키 집합)으로 복제하는 것이 새 메커니즘 설계보다 안전하다 — 다른 파일럿 무영향을 구조적으로 보장하기 때문이다.
- 이런 확장이 TASK Constraint의 문자 그대로 범위를 넘어서면, PM이 "다른 파일럿에 영향 없음"을 근거로 제시하되 최종 승인은 사용자에게 명시적으로 받는다(design-decision 흐름 또는 직접 확인).

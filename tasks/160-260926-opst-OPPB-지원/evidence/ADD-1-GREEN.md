# ADD-1 GREEN 증빙: function-todo-crud

## 시나리오 규격

- `skill_tester.py validate function-todo-crud` — 통과.
- `skill_tester.py validate --all` — 6개 시나리오 모두 통과.

## 회귀 검증

- `pytest -q opal/skills/opal-skill-tester/tests` — `10 passed`.
- TODO 기반 저장소 기존 테스트 — `2 passed`.
- Python `py_compile` — 기반 app, hidden acceptance, 시나리오 단위 테스트 통과.
- `git diff --check` — 통과.

## 코드·컨벤션 검증

- `code-scan validate --changed <TODO 15개 대상>` — `ok=true`, `newly_uncovered=0`, `pre_existing=1`.
- 독립 컨벤션 재검사 — `PASS_WITH_ADVISORIES`, 신규 blocking 0건.
- 기존 `README.md` 헤더 결손 1건은 `pre_existing` informational로 분리했다.

## 비실행 범위

- 실제 `skill_tester.py run function-todo-crud` 유료 세션은 실행하지 않았다.

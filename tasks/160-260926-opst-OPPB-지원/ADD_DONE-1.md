# ADD_DONE: function-todo-crud 재사용 시나리오

## 추가작업 번호

ADD-1

## 일시

- 시작: 2026-09-26 22:07 KST
- 완료: 2026-09-26 22:24 KST

## 사유

특정 Pilot에 종속되지 않고 여러 Pilot의 기능 구현 품질을 비교할 수 있는 TODO CRUD 시나리오가 필요했다.

## 변경 내용

- `function-todo-crud` 시나리오와 Pilot 중립 요구서를 추가했다.
- Python 표준 라이브러리 TODO 웹 skeleton과 OPAL 프로젝트 자산을 추가했다.
- CRUD, 영속성, 다른 항목 보존, 검증·HTTP 예외, HTML 화면을 검증하는 hidden acceptance 6건을 추가했다.
- 시나리오 규격·기반 GREEN·hidden RED를 고정하는 회귀 테스트를 추가했다.
- README에 실행 예시를 추가했다.

## 변경 파일

- `opal/skills/opal-skill-tester/README.md`
- `opal/skills/opal-skill-tester/scenarios/_bases/todo-web/`
- `opal/skills/opal-skill-tester/scenarios/function-todo-crud/`
- `opal/skills/opal-skill-tester/tests/test_skill_tester_todo_crud.py`
- `tasks/160-260926-opst-OPPB-지원/evidence/ADD-1-RED.md`
- `tasks/160-260926-opst-OPPB-지원/evidence/ADD-1-GREEN.md`
- `tasks/160-260926-opst-OPPB-지원/GC-CONVENTION-20260926-2214-todo.md`
- `tasks/160-260926-opst-OPPB-지원/gc-findings-convention-20260926-2214-todo.json`
- `tasks/160-260926-opst-OPPB-지원/GC-CONVENTION-20260926-2222-todo-recheck.md`
- `tasks/160-260926-opst-OPPB-지원/gc-findings-convention-20260926-2222-todo-recheck.json`
- `tasks/160-260926-opst-OPPB-지원/ADD_PM-GATE-1.md`

## 검증 결과

- `validate function-todo-crud`, `validate --all` 통과.
- skill tester 회귀 `10 passed`, TODO 기반 회귀 `2 passed`.
- hidden acceptance는 미구현 skeleton에서 기대한 RED `5 failed, 1 passed`.
- Python compile, `git diff --check` 통과.
- code-scan `newly_uncovered=0`; 독립 컨벤션 재검사 `PASS_WITH_ADVISORIES`.
- 실제 유료 시나리오 실행은 하지 않았다.

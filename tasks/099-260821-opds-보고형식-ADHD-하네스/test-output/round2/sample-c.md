지정된 3개 명령을 존재하지 않는 경로로 실행해 실패 응답을 실측했다.
▶ 다음 액션: 3개 명령 모두 정상 경로/파일로 재실행해 회귀 여부 확인 (소요: 5분)

## 🎯 결론·근거

> **1️⃣ 3개 명령 모두 설계된 오류 코드로 실패 [상]**
- `state-tool show tasks/000-does-not-exist`는 exit 1, `task_path_not_found`를 반환했다.
- `test-tool scenario-coverage-check --coverage-input /tmp/nonexistent.json`은 exit 17, `coverage_input_invalid`를 반환했다.
- `memory-tool show --file /tmp/nonexistent.json`은 exit 1, `memory_json_not_found`를 반환했다.
**세 명령 모두 버그가 아니라 부재 입력에 대한 의도된 거부 응답이다.**

| 명령 | exit | error 코드 | 원인 | 해결 |
|---|---|---|---|---|
| `state-tool show tasks/000-does-not-exist` | 1 | `task_path_not_found` | task-path 디렉토리가 실제로 없음 | 존재하는 태스크 경로로 재지정 |
| `test-tool scenario-coverage-check` | 17 | `coverage_input_invalid` | `--coverage-input` 파일이 없음 | 정규화 페이로드 파일을 실제 경로로 생성 후 지정 |
| `memory-tool show --file /tmp/nonexistent.json` | 1 | `memory_json_not_found` | 지정 경로에 `.json`/`.md` 둘 다 없음 | 해당 경로에 `init` 먼저 실행 |

**원인**: 세 명령 모두 실제로 존재하지 않는 경로/파일을 인자로 넘겨 발생했다(하네스 검증용 의도적 입력).
**해결**: `state-tool`은 `state-tool list`로 유효 태스크 경로 확인 후 재호출, `test-tool`은 coverage 입력 JSON을 먼저 생성, `memory-tool`은 대상 경로에 `init` 서브커맨드를 선행 실행한다.

## 📌 잔여·보류·유의

- exit 코드 17(`coverage_input_invalid`)은 `test-tool/README.md`에 별도 표로 명시돼 있지 않아 조회 시 소스(`lib/scenario.py`)까지 확인해야 했다 — README 보강 후보다.
- 세 도구 모두 오류 응답이 JSON 구조(`ok`/`error`/`message`)로 일관돼 있어 실패 처리 자동화에는 문제가 없다.

완료: 3/3

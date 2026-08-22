state-tool·test-tool·memory-tool 3개 명령을 존재하지 않는 경로로 실행해 실패 응답을 실측했다.
▶ 다음 액션: 정상 입력으로 재실행해 회귀 여부를 확인한다 (소요: 5분)

---
## 🎯 결론·근거
> **1️⃣ state-tool show — task_path_not_found (exit 1) [상]**
- 명령: `show tasks/000-does-not-exist` 실행 시 `{"ok": false, "error": "task_path_not_found", ...}` 응답과 종료코드 1을 반환했다.
- **원인** 지정한 태스크 디렉토리가 실제로 존재하지 않는다.
- **해결** `tasks/` 하위 실재 경로를 지정하거나, 신규 태스크면 태스크 폴더를 먼저 생성한 뒤 재실행한다.
> **2️⃣ test-tool scenario-coverage-check — coverage_input_invalid (exit 17) [상]**
- 명령: `--coverage-input /tmp/nonexistent.json` 실행 시 `{"ok": false, "error": "coverage_input_invalid", ...}` 응답과 종료코드 17을 반환했다.
- **원인** `--coverage-input`이 가리키는 JSON 파일이 없다. `--help` 확인 결과 이 옵션은 `test-scenario.json`이 아닌 별도의 정규화 페이로드(`goal/requirements/features/hypotheses/scenarios`)를 요구한다.
- **해결** 해당 스키마의 커버리지 입력 JSON을 실제 경로에 생성한 뒤 재실행한다.
> **3️⃣ memory-tool show — memory_json_not_found (exit 1) [중]**
- 명령: `--file /tmp/nonexistent.json` 실행 시 `{"ok": false, "error": "memory_json_not_found", ...}` 응답과 종료코드 1을 반환했다.
- **원인** `--file`이 가리키는 `MEMORY.json`이 아직 생성되지 않았다.
- **해결** 응답 메시지가 안내하는 대로 `init` 명령으로 `MEMORY.json`을 먼저 생성하거나, 기존 `MEMORY.json` 경로를 지정한다.
**3개 명령 모두 입력 경로 부재를 사전 검증해 구조화된 JSON 에러로 종료했고, 스택 트레이스나 미확인 예외는 관측되지 않았다.**

---
## 📌 잔여·보류·유의
- state-tool·memory-tool은 종료코드 1을 공유하지만 `error` 필드 값으로 구분 가능하다 — 종료코드만으로 원인을 판별하지 않도록 유의(유의).

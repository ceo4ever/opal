state-tool·test-tool·memory-tool에 존재하지 않는 경로를 입력해 실패 사례를 실측하고 원인·해결을 정리해 달라는 요청으로 이해했습니다.
▶ 다음 액션: 재현 결과 확인 (소요: 5분)

---

## 🎯 결론·근거

> **1️⃣ state-tool show — task_path_not_found, exit 1 [상]**
- 존재하지 않는 `tasks/000-does-not-exist`를 넣자 `{"ok": false, "error": "task_path_not_found"}`가 exit 1로 반환됐다.
- **원인**: 지정한 `<task-path>` 디렉토리가 실제로 없다.
- **해결**: `ls tasks/`로 존재하는 태스크 경로를 먼저 확인한 뒤 정확한 상대경로를 넣는다.
**방어적으로 설계된 거부이며 도구 결함은 아니다.**

> **2️⃣ test-tool scenario-coverage-check — coverage_input_invalid, exit 17 [상]**
- 존재하지 않는 `/tmp/nonexistent.json`을 `--coverage-input`에 넣자 `{"ok": false, "error": "coverage_input_invalid"}`가 exit 17로 반환됐다.
- **원인**: `--coverage-input` 파일이 실제로 없다 — `test_scenario.py`(T073)에도 exit 17이 이 조건의 기대값으로 고정돼 있다.
- **해결**: 커버리지 입력 JSON을 실제 경로에 먼저 생성한 뒤 `--coverage-input`에 지정한다.
**exit 17은 소스 테스트상 의도된 코드이며 README.md에는 아직 문서화돼 있지 않다.**

> **3️⃣ memory-tool show — memory_json_not_found, exit 1 [상]**
- 존재하지 않는 `/tmp/nonexistent.json`을 `--file`에 넣자 `{"ok": false, "error": "memory_json_not_found"}`가 exit 1로 반환됐다.
- **원인**: 해당 경로에 MEMORY.json이 아직 생성되지 않았다.
- **해결**: 에러 메시지가 안내하는 대로 `memory-tool init`을 먼저 실행해 MEMORY.json을 만든 뒤 `show`를 호출한다.
**세 명령 모두 크래시가 아니라 구조화된 에러 응답(JSON + 비0 exit code)으로 정상 종료됐다.**

---

## 📌 잔여·보류·유의

- `test-tool/README.md`에는 `scenario-coverage-check` 서브명령 자체가 기술돼 있지 않다 — exit 17 매핑은 소스와 테스트 코드에서만 확인 가능했다(유의).

---

## ▶️ 승인 요청

- [x] `test-tool/README.md`에 `scenario-coverage-check` 서브명령·exit 16/17 설명을 보강하는 것으로 권고 확정

이의 없으면 이대로 진행하겠습니다.
질문: README 보강을 별도 후속 태스크로 지금 등록할까요?

<!--
@header {
  "module": "self-pm-tool-readme",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "self-pm-tool 사용 안내 — init/update/show 3서브명령, 8필드 스키마, SSOT 무접촉 불변식.",
  "exports": ["사용법", "8필드 스키마", "제약"]
}
-->

# self-pm-tool — opal-self-pm 경량 실행 기록 CLI

`opal-self-pm` 모델이 PM 직접 수행 실행을 자기완결적으로 기록하기 위한 최소 CLI다.
`improve-tool`(`opal/tools/improve-tool/`)의 구조를 그대로 답습한다 — argparse 서브파서,
JSON stdout, `run.sh` 얇은 래퍼.

## 서브명령

### init

```bash
bash run.sh init --task-root <path> --objective <text> [--run-id <id>] [--run-dir <path>]
```

`{task_root}/.opal/self-pm/{run_id}.json`을 신설한다(`--run-id` 미지정 시 도구가 생성).
8필드 스켈레톤을 모두 채우고 `status`는 `discovering`으로 초기화한다.
stdout: `{"ok":true,"run_id":"...","path":"..."}`.

### update

```bash
bash run.sh update --task-root <path> --run-id <id> \
  [--status <value>] \
  [--set-field <FIELD> <JSON배열>]... \
  [--append-field <FIELD> <값>]... \
  [--run-dir <path>]
```

기존 run 파일의 `status` 전이 및/또는 6개 리스트 필드(`decisions`·`open_questions`·
`approved_scope`·`changed_files`·`validation`·`knowledge_impact`)를 갱신한다.
`objective`는 `init`이 소유하며 `update`로는 바꿀 수 없다.

- `--status`, `--set-field`, `--append-field` 중 **최소 하나**는 있어야 한다. 셋 다
  없으면 의미 없는 호출로 거부한다.
- `--status`는 폐쇄 집합(`discovering`/`awaiting_approval`/`executing`/
  `awaiting_confirmation`/`done`) 값만 허용한다.
- `--set-field FIELD VALUE`는 해당 리스트 필드를 **전체 교체**한다. `VALUE`는 반드시
  유효한 JSON 배열이어야 한다(스칼라·객체 등은 거부).
- `--append-field FIELD VALUE`는 해당 리스트 필드 뒤에 항목 **하나를 추가**한다.
  `VALUE`는 JSON으로 파싱을 시도하고, 실패하면 원문 문자열 그대로 항목이 된다.
- `--set-field`/`--append-field`는 각각 반복 지정할 수 있다. 같은 호출에서 같은
  필드에 `--set-field`와 `--append-field`를 함께 주면 교체 후 추가 순서로 적용된다.
- `FIELD`가 6개 리스트 필드 밖(예: `objective`, `status`)이거나, run 파일 부재,
  run 파일 8필드 결손, 잘못된 값 타입인 경우 모두 `{"ok":false,"error":"..."}` +
  exit != 0으로 거부한다(traceback 없음).

예시:

```bash
bash run.sh update --task-root "$TASK_ROOT" --run-id "$RUN_ID" \
  --status executing \
  --append-field open_questions "롤백 기준은 무엇인가"

bash run.sh update --task-root "$TASK_ROOT" --run-id "$RUN_ID" \
  --set-field decisions '["D-1: ...", "D-2: ..."]'
```

### show

```bash
bash run.sh show --task-root <path> --run-id <id> [--run-dir <path>]
```

run 파일을 읽어 stdout으로 반환한다(read-only). 8필드 중 하나라도 결손되어 있으면
`{"ok":false,"error":"..."}` + exit != 0으로 거부한다.

## 8필드 스키마

```json
{
  "objective": "...",
  "status": "discovering|awaiting_approval|executing|awaiting_confirmation|done",
  "decisions": [],
  "open_questions": [],
  "approved_scope": [],
  "changed_files": [],
  "validation": [],
  "knowledge_impact": []
}
```

## `--run-dir` (공용, 선택)

run 파일이 위치한 디렉토리를 직접 지정하는 저수준 override다(기본값
`{task_root}/.opal/self-pm`). 해석된 경로가 `{task_root}` 밖이면 경로 이탈로 거부한다
(`{"ok":false,...}` + exit != 0).

## 제약 — SSOT 무접촉

이 도구는 `state.json`·`test-scenario.json`·`backlog.json` 어느 것도 읽거나 쓰지 않는다.
자신의 run 파일(`{task_root}/.opal/self-pm/{run_id}.json`) 하나만 다룬다 — 3-SSOT
소유권 경계를 흐리지 않기 위함이다.

의도적으로 조회·집계·목록 기능을 만들지 않는다 — `init`/`update`/`show` 3서브명령이 전부다.

## 근거

`tasks/122-260912-opds-PM-직접수행-모델/PLAN.md` D-8 (경량 기록 도구 설계 근거, 대안
폐기 사유), TASK AC-10.

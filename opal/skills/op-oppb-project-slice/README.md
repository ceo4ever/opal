# op-oppb-project-slice

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project-build`(oppb)가 P2 PROJECT DESIGN & SLICE 단계에서 디스패치합니다.

승인된 INTENT를 capability 단위 미니 태스크 DAG·계약·완료조건 역인덱스로 변환하는 OPPB 프로젝트 슬라이스 단계 스킬입니다.

## 역할

이 스킬은 **초안 작성자**입니다. Project Planner/Slicer 워커가 승인된 INTENT를 읽고, capability 단위로 미니 태스크를 나누어 Controller Tool이 소비할 구조화 spec을 씁니다. 승인은 PM Agent가, 기계 검증과 실제 `workgraph.json`·`acceptance.json` 생성은 `opal/tools/oppb-runtime-tool/controller.py`가 소유합니다. 이 스킬은 `workgraph load --spec`이 받는 spec 파일만 쓰며, `scope_hash` 계산이나 `.opal/oppb-environment.json` 기입 같은 Controller·probe 전용 영역은 건드리지 않습니다.

슬라이스의 기본 단위는 동일한 비즈니스 개념·변경 이유·정책을 공유하며 사용자가 끝까지 사용할 수 있는 하나의 응집된 capability입니다. FE/BE/DB처럼 단독으로 사용자 가치를 내지 못하는 수평 레이어 조각을 별도 미니 태스크로 만드는 것은 금지되며, 그런 조각은 같은 capability 안의 `executors` work item으로 둡니다. 별도 미니 태스크로 병렬 실행하려면 `tracked_writes`·`ephemeral_writes`·`contracts`·`runtime_resources` 네 lease 축에 교집합이 없어야 하며, 증명할 수 없으면 병렬로 선언하지 않고 순차 의존이나 단일 capability로 합칩니다.

## 입력

- `task_folder`: OPPB 프로젝트 태스크 캡슐(`<task_root>/tasks/{NNN}-oppb-{name}/`)
- `intent`: `<task_folder>/INTENT.md` — 승인된 목표·제외 범위·완료조건·예산
- `project_docs`: PM이 `docs/PROJECT.md` 레지스트리에서 선별해 주입한 문서 목록(이 목록 밖은 탐색하지 않음)
- `run_root`: 이미 발급된 경우 경로만 전달받음(이 스킬은 run root에 쓰지 않음)

## 출력

- `<task_folder>/.oppb-workgraph-spec.json` — `budget`, `mini_tasks[]`(id·capability·depends_on·lease·run_command·verify_command·executors), `acceptance[]`(완료조건 ↔ 기여 태스크 역인덱스 원천)
- `<task_folder>/.oppb-probe-commands.json` — 미추적 쓰기 힌트를 관측할 명령 목록(`probe seal`이 소비)
- `<task_folder>/PROJECT-DESIGN.md` 초안 — 슬라이스 근거, 병렬 판정표, 계약 경계, 통합 전략·위험, PM 판정 요청 항목

## 호출 시점

OPPB Product Flow가 P2 PROJECT DESIGN & SLICE를 Project Planner/Slicer 워커에게 디스패치할 때 실행됩니다. OPPB의 미니 태스크는 OPAL 태스크가 아니며, 태스크 번호·폴더·worktree·branch를 갖지 않고 `workgraph.json`의 record로만 존재합니다. 이 스킬은 미니 태스크별 `TASK.md`·`PLAN.md`·`DONE.md` 같은 문서 파이프라인을 설계하지 않습니다.

## 관련 문서

- `opal/tools/oppb-runtime-tool/controller.py` — spec을 소비하고 `workgraph.json`·`acceptance.json`을 생성하는 유일한 writer

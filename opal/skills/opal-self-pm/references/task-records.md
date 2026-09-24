<!--
@header {
  "module": "opal-self-pm-task-records",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "oppm 정식 태스크 경로, PM 수행 문서, self-pm 현재 기록과 표준 run-log의 초기화·재개·검증 계약.",
  "exports": ["태스크 경로", "수행 문서", "실행 기록", "종료 확인"]
}
-->

# PM 수행 기록

## 태스크 경로

- 신규 작업은 프로젝트 설정의 태스크 폴더(기본 `tasks/`) 아래 `{NNN}-{YYMMDD}-oppm-{태스크명}/`을 만든다. 번호·날짜·이름은 `harness/task-process.md`의 **태스크 번호 채번 규칙과 저장 경로 규칙만** 재사용한다. Pilot의 `state init`·단계 행 생성은 적용하지 않는다.
- 채번은 `memory-tool task-number --file <허브 절대경로>/.opal/MEMORY.json --bump`, 날짜는 `node ~/.opal/tools/date/date.js yymmdd` 결과를 사용한다. 태스크 경로를 확정한 뒤 폴더와 TASK.md를 생성한다.
- 기존 oppm 작업의 재개는 같은 폴더·실행 ID를 사용한다. 재채번·재초기화하지 않고 TASK.md와 `self-pm-tool show`로 현재 맥락을 복원한다.
- 다른 Pilot 태스크 안에서 호출되면 별도 정식 oppm 태스크를 만들고 TASK.md에 원 태스크 경로를 연결한다. 원 태스크의 TASK·PLAN·DONE을 덮어쓰거나 상태를 변경하지 않는다.
- 프로젝트 루트·임시 폴더에 남은 이전 실행을 재개할 때도 정식 태스크 폴더를 발급한다. 원 기록은 보존하고 TASK.md에 원 경로·실행 ID와 인계 내용을 남긴 뒤 새 실행을 초기화한다.
- `task_root`는 이 문서 및 self-pm-tool 호출에서 **확정된 태스크 폴더의 절대경로**다. 프로젝트 루트·채번용 허브 경로와 혼용하지 않는다. 기존 워크트리에서는 발급된 루트 계약(`harness/worktree.md`)을 따른다.

## 수행 문서

문서는 PM이 작업하면서 작성·갱신하며, 사용자가 필요할 때 확인하는 수행 기록이다. 문서 이름을 단계나 문서별 승인 게이트로 취급하지 않는다. 기존 실행 계약 승인·최종 확인 경계는 유지한다.

| 문서 | 시점 | 최소 기록 |
|---|---|---|
| TASK.md — 필수 | 진입 시 작성, 결정·범위 변경 시 갱신 | 요청·목표·완료 기준, 범위·대상, 참조 문서와 제약, 계약·승인 근거, 결정·남은 질문, 실행 ID 및 기록 경로 |
| DONE.md — 필수 | 수행 중 결과 누적, 최종 확인 요청 전 정리 | 실제 변경·산출물 링크, 검증 방법·결과·증거, 지식 동기화 결과, 미해결·후속, 사용자 확인 상태 |
| PLAN.md 및 기타 문서 — 선택 | 의존 순서·설계 판단·조사·검증 등의 별도 기록이 필요할 때 | 필요한 내용만 기록하고 TASK/DONE에서 연결 |

완료를 기다리며 빈 DONE.md를 만들 필요는 없다. 사용자 확인 전에는 DONE.md에 `최종 확인 대기`를 표시하고, 확인 후 결과를 갱신한다. TASK.md가 실행 ID와 원천 경로를 연결하므로 재개 때 대화 기억으로 추측하지 않는다.

## 실행 기록

`self-pm-tool`은 현재 목표·결정·검증·상태를, `run-log-tool`은 시간순 사건을 소유한다. 두 기록은 같은 태스크 폴더와 실행 ID를 사용한다. run-log JSONL은 도구만 쓰며 PM이 직접 작성·수정하지 않는다.

### 신규 초기화

`run_<UUIDv4>`를 한 번 발급해 두 도구에 명시 전달한다. self-pm-tool의 기본 자동 ID를 run-log에서 사용할 수 있다고 가정하지 않는다.

```bash
python3 -c 'import uuid; print("run_" + str(uuid.uuid4()))'
~/.opal/tools/self-pm-tool/run.sh init --task-root <task_root> --run-id <run_id> --objective "<목표 요약>"
~/.opal/tools/run-log-tool/run.sh init --task <task_root> --run-id <run_id> --format json
```

각 응답의 성공을 확인하고 TASK.md에 ID·경로를 기록한다. 일부 실패 시 이미 성공한 기록을 지우거나 새 ID로 우회하지 않고 오류를 해결한다.

### 발생 시점 기록

진입·작업 진행·문서 동기화는 `progress`, 확정 결정·실제 승인·최종 확인은 `decision`, 검증 결과는 `validation`, 실패 후 재시도는 `retry`로 남긴다. 내부 사고 과정이나 원본 프롬프트·비밀값은 기록하지 않는다.

```bash
~/.opal/tools/run-log-tool/run.sh append --task <task_root> --run-id <run_id> \
  --request-id <사건별_고유_ID> --event activity \
  --actor-kind PM --actor-id self-pm --provenance-type direct --recorded-by-kind PM \
  --summary "<실제로 수행한 일과 결과>" --data '{"kind":"progress"}' \
  --refs <관련_문서_또는_증거_경로> --format json
```

동일 사건 전송 재시도는 같은 request ID와 payload를 사용한다. 새 사건에는 새 ID를 쓴다. 사건·출처·payload 규범은 `docs/run-log/CONTRACT.md` §1.2·§1.3, 실제 CLI는 `opal/tools/run-log-tool/README.md`가 소유한다. 대상 프로젝트에 프레임워크 원문이 없으면 설치본 `~/.opal/tools/run-log-tool/README.md`를 사용한다.

PM 보고는 같은 계약의 `pm.report`, 사용자 확인 요청·응답은 실제 발생한 `gate.requested`·`gate.resolved`로 기록한다. 기존 gate를 기록하는 것이며 새 승인 단계를 추가하지 않는다. PM이 Pilot 전용 `run.started`·`run.completed`나 worker 사건을 가장하지 않는다. PM 사건의 스키마 검증 통과를 독립 평가·작업 성공의 증거로 대체하지 않는다.

## 종료 확인

1. TASK.md와 DONE.md에 수행 범위·결과·미해결 사항이 맞게 기록되어 있는지 확인한다. PLAN.md 부재는 실패가 아니다.
2. `testing-evidence.md`의 테스트 증거·E2E 적용 검토 기록이 있고 실제 결과와 연결되는지 확인한다. 지식 동기화는 `knowledge-sync.md`에 따라 실제 반영 후 기록한다.
3. `run-log-tool validate-run --task <task_root> --run-id <run_id> --format json`을 실행한다. 오류가 있으면 해결하기 전 종료하지 않는다.
4. DONE.md를 근거로 사용자 최종 확인을 요청한다. 수정 요청이면 같은 태스크에서 기록을 이어간다.
5. 확인 발화 후 DONE.md의 확인 상태와 최종 결정 사건을 기록하고 로그를 재검증한 다음 `self-pm-tool update --status done`을 수행한다.

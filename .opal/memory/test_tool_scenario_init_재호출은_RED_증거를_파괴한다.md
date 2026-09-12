# test-tool scenario-init 재호출은 RED 증거를 파괴한다

`scenario-init`은 `test-scenario.json` spec을 통째로 덮어쓰며 `red_confirmed`를 **항상 false로 강제**한다(056/ADD-1 — RED 미관찰 상태를 시드로 우회 선언하는 경로 봉쇄).

## 안전한 정정 절차

`red_required` 분류를 고쳐야 할 때(예: 성격상 실패할 수 없는 시나리오를 RED 대상에서 빼는 경우):

1. 기존 `red_evidence`를 먼저 보존한다.
2. TEST-SCENARIO.md의 `시점`을 고치고 scenarios JSON을 재생성한다.
3. `scenario-init` 재호출.
4. `scenario-red --id S-N --evidence "..."`로 재기록한다. **플래그는 `--id`다** — `--scenario`가 아니다.
5. `scenario-status`로 `red_confirmed`를 확인한 뒤에 백업을 정리한다.

## 태스크 124에서 실제로 일어난 일

4단계에서 `--scenario`로 잘못 호출해 19건이 전부 argparse 오류(exit 2, 빈 stdout)로 실패했다. 그런데 결과의 `ok`를 확인하기 전에 백업 파일을 지워 증거 텍스트를 잃었다. 복구는 RED 작성자 에이전트를 재개해 재관측·재기록으로 했다 — PM이 증거 텍스트를 지어내면 증거 성격 자체가 무너지기 때문이다.

**도구 호출 결과의 `ok`를 확인하기 전에 백업을 삭제하지 않는다.**

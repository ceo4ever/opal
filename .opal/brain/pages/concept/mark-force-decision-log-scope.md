---
type: concept
title: 강제 처리의 실제 거동 — 사유는 필수지만 의사결정 로그에는 자동 기재되지 않는다
tags:
- state-tool
- pipeline
- decision-log
- doc-correction
- task-090
- task-094
sources:
- task:090
- task:094
related:
- state-tool
- na-status-contract-agentic-init-only
- state-md-journal-redefinition
created: '2026-08-13'
updated: '2026-08-16'
status: active
---
## 개요

행 상태를 강제로 바꾸는 "강제 처리" 사용에는 사유 기재가 항상 필수이지만, 그 사유가 STATE.md의 "의사결정 로그" 표에 자동으로 남는 것은 아니다. 자동 기재는 일반적인 강제 처리가 아니라 **정확히 세 가지**(task:090 당시 파악은 두 가지였으나 task:094가 코드 실측으로 세 번째를 확정)의 특수한 경우에만 일어난다.

## 결정 배경 (WHY)

- (근거: task:090 DONE.md §5) 프로젝트개발 pilot의 na 지시문 결함을 고치는 과정에서, "강제 처리로 우회하면 STATE.md에 의사결정 로그가 자동으로 남는다"는 정정문이 한 차례 작성됐다. 이 정정문의 출처는 운영 하네스 문서 한 줄(문서: `opal/core/references/harness/opal-harness-agentic.md:109`)이었고, 실제 동작과 대조하지 않은 채 그대로 이어받은 것이었다.
- 실측 결과 사유 기재 자체는 사실이었지만(강제 처리 시 사유가 없으면 거부된다), "자동으로 로그에 남는다"는 부분만 사실이 아니었다. 실측 기준으로 다시 정정한 뒤에야 정확해졌다(근거: task:090 DONE.md §5 2차 정정 문단).
- (근거: task:094 TASK.md R-2 AC 정정 이력, EXECUTE Step 0 RED에서 검출) 094는 STATE.md 저널 재배선의 회귀 방지 대상으로 "의사결정 로그 자동 기재 트리거"를 코드에서 전수 재확인했다. 최초 문안은 트리거를 `mark --force --note`(일반 강제 처리)로 잘못 명시했으나, 실측 결과 `cmd_mark`가 `decision`을 세팅하는 경로는 아래 3종뿐이고 일반 `--force`(비워커·비게이트)는 `decision=None`으로 호출됨을 grep으로 확인했다(`state_tool.py:1615-1634` 대응 구간). AC를 실재 트리거로 교정했다.

## 결정 내용

- 일반적인 강제 처리(사유를 남기고 강제로 상태를 바꾸는 경우)는 그 사유를 행 자체의 메모 필드에만 남긴다(`opal/tools/state-tool/state_tool.py` 사유 필수 검사). STATE.md에서 사람이 보는 "의사결정 로그" 표에는 나타나지 않는다.
- 의사결정 로그 표에 자동으로 한 줄이 남는 경우는 **세 가지**다 — ① 완전자율 모드에서 사용자 확인을 자동으로 통과시킬 때(`mark --auto-pass --note`) ② 워커가 자신이 맡은 단계를 벗어난 행을 강제로 처리할 때(`mark --as-worker --force --note`) ③ PM Gate 산출물 미충족을 강제 우회할 때(`gate_artifact_force`, task:091 도입). 셋 다 "누가, 왜 정상 경로를 벗어났는가"를 남겨야 하는 예외적 상황이기 때문에 자동 기재 대상이 된다. (task:090 시점 파악은 ①·②뿐이었다 — ③은 task:091이 이미 도입했으나 090이 놓쳤고, task:094가 전수 재확인하며 셋으로 확정했다.)
- add-row·status 변경·gate-pass처럼 상태 자체가 아니라 파이프라인 구조·표시를 바꾸는 명령들은 위 세 트리거와 무관하게 **항상** 의사결정 로그에 한 줄을 남긴다(별도 성격 — "강제 우회" 트리거가 아니라 "구조 변경 이력").
- 그래서 "강제 처리 사유가 로그 표에 보이지 않는다"는 것은 결함이 아니라 원래 설계다. 사유를 사람이 보는 곳에 남기고 싶다면 그 사유가 실제로 남는 곳(행 메모, 또는 위 3트리거 중 하나로 발생한 로그 행)을 직접 확인해야 한다.
- **교훈**: 운영 문서 한 줄을 근거로 코드 동작을 단정하지 않는다. 두 태스크(090, 094) 모두 "실측 전 문서 근거 정정문"이 실제로는 불완전했고, 코드 grep 전수 확인 후에야 트리거 개수가 확정됐다.

## 관련 페이지

- [[state-tool]]
- [[na-status-contract-agentic-init-only]]
- [[state-md-journal-redefinition]]

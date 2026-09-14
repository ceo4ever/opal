---
type: entity
title: self-pm-tool
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- tool
- cli
- pm
- task-122
sources:
- task:122
related:
- opal-self-pm
- improve-tool
- state-tool
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

`self-pm-tool`은 [[opal-self-pm]] 대화형 루프 전용의 경량 실행 기록 CLI다. PM이 직접 수행한 작업의 목표·결정·질문·승인 범위·변경 파일·검증·지식 영향을 8개 필드로 강제해 기록하며, 파이프라인 3-SSOT(`state.json`·`test-scenario.json`·`backlog.json`)는 읽지도 쓰지도 않는다(근거: task:122 PLAN.md D-8, `opal/tools/self-pm-tool/README.md:11-16`).

## 책임 (WHAT)

- `init` — `{task_root}/.opal/self-pm/{run_id}.json`을 신설하고 8필드 스켈레톤을 채운 뒤 `status`를 `discovering`으로 초기화한다(`opal/tools/self-pm-tool/README.md:19-27`).
- `update` — `--status`(폐쇄 집합 `discovering`/`awaiting_approval`/`executing`/`awaiting_confirmation`/`done`), `--set-field`(리스트 필드 전체 교체), `--append-field`(리스트 필드에 항목 1개 추가) 중 최소 하나를 받아 6개 리스트 필드(`decisions`·`open_questions`·`approved_scope`·`changed_files`·`validation`·`knowledge_impact`)를 갱신한다. `objective`는 `init` 전용이라 `update`로 바꿀 수 없다(`opal/tools/self-pm-tool/README.md:29-56`).
- `show` — run 파일을 읽기 전용으로 반환한다. 8필드 중 하나라도 결손이면 거부한다(`opal/tools/self-pm-tool/README.md:68-75`).
- 8필드 누락·미지 `status` 값·경로 이탈(`--run-dir`이 `{task_root}` 밖을 가리키는 경우)은 모두 JSON `{"ok":false,...}` + 비정상 exit로 거부하고 traceback을 내지 않는다(`opal/tools/self-pm-tool/README.md:53-56, 92-96`).

## 설계 배경 (WHY)

- (근거: task:122 PLAN.md D-8) 두 가지 대안을 검토 후 폐기했다 — (i) 손으로 쓰는 JSON은 8필드 보장이 산문 규율에 그쳐 "enforce, don't advise" 원칙을 위반하고, (ii) `state-tool`을 확장해 이 기록을 얹는 방식은 3-SSOT 소유권 경계를 흐려 태스크가 지키려는 속성(파이프라인 상태와 대화형 PM 루프 기록의 분리) 자체를 깬다.
- (근거: task:122 PLAN.md D-8) 신설 CLI는 조회·집계 기능을 만들지 않는 최소 구현이다 — 규모 선례로 `improve-tool`(442행 + `run.sh` 12행)을 참조해 그 구조(argparse 서브파서·JSON stdout·`run.sh` 얇은 래퍼)를 그대로 답습했다(`opal/tools/self-pm-tool/README.md:14-16`).
- (근거: task:122 AGENTIC-LOG.md 엔트리 #23·#26) 1차 산출물은 `update`가 `--status`만 받아 PLAN이 요구한 "필드별 set/append"가 미구현이었다. 재지시로 `--set-field`/`--append-field` 반복 인자와 6필드 폐쇄, 원자적 검증(파일에 손대기 전 전부 검증)을 반영했다.

## 관계 (HOW)

- [[opal-self-pm]] — 이 도구의 유일한 소비자. 루프의 매 단계 전이(질문 제시·계약 확정·실행 승인·파일 변경·검증·지식 동기화·최종 확인 후 종료)가 `update` 호출 한 번씩으로 남는다.
- [[improve-tool]] — 구조를 그대로 답습한 선례. 두 도구 모두 최소 CLI로 "필요 이상으로 조회·집계 기능을 만들지 않는다"는 절제 원칙을 공유한다.
- [[state-tool]] — 대비 관계다. `state-tool`은 파이프라인 3-SSOT의 하나(`state.json`)를 소유하지만, `self-pm-tool`은 그 3-SSOT 중 어느 것도 접촉하지 않는 별도 저장 공간(`{task_root}/.opal/self-pm/`)을 쓴다.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `init`/`update`/`show` 서브명령 | `opal/tools/self-pm-tool/self_pm_tool.py` | CLI 진입점 3종 |
| `run.sh` | `opal/tools/self-pm-tool/run.sh` | venv 래퍼 |
| 8필드 스키마 예시 | `opal/tools/self-pm-tool/README.md:79-90` | `objective`/`status`/`decisions`/`open_questions`/`approved_scope`/`changed_files`/`validation`/`knowledge_impact` |
| 테스트 | `opal/tools/self-pm-tool/tests/test_self_pm_tool.py` | pytest 6 passed(task:122 DONE.md §검증) |
| install 배포 등록 | `scripts/install-mac.sh`(`self-pm-tool/run.sh` chmod 블록) | 배포본 실행 권한 부여 |

---
name: opal-self-pm
description: |
  **대화형 PM 직접 수행 루프**. Pilot이 아니라 종료 조건을 가진 질문 반복형 작업 루프다 — 질문 1개→조회·정리를 반복해 범위를 확정하고, PM이 직접 조회·작성·수정·검증을 수행하며, 완료 전 지식 영향을 전수 판정한 뒤 사용자 최종 확인을 받고서야 종료한다.
  필수 입력: 사용자의 자연어 요청(목표)과 실행 맥락(진행 중이면 해당 태스크 폴더, 아니면 프로젝트 루트에서 정식 태스크를 생성).
  보장 출력: 사용자와 합의한 계약 범위 안의 산출물 변경, 정식 태스크 폴더의 `TASK.md`·`DONE.md` 수행 기록, `self-pm-tool` 현재 기록(8필드 JSON)과 표준 run-log, 8영역(기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan) 지식 동기화 판정(`update` 또는 `no-op + 근거`).
  반드시 이 스킬을 사용해야 하는 상황: `//oppm`, "opal-self-pm", 또는 사용자가 "대화하면서 직접 해줘"·"하나씩 질문하며 PM이 처리해줘"처럼 질문 반복형 PM 직접 수행을 요청할 때.
alias: oppm
triggers:
  - "^oppm$"
  - "^opal-self-pm$"
domain: pm
pipeline: "없음 — 대화형 루프(operator 스킬). opal-brain과 동일 유형: 단계 파이프라인·`state-tool`·워커 디스패치 없음"
---

<!--
@header {
  "module": "opal-self-pm-skill",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "정식 태스크 폴더에서 PM이 직접 수행하며 TASK·DONE 수행 기록, 표준 run-log, 관련 문서 조회와 실제 지식 동기화를 남기는 대화형 루프를 규정한다.",
  "exports": ["설계 원천과 경계", "루프 개요", "진입", "질문 단계", "작업 계약 확정", "PM 작업·검증", "범위 변경 시 복귀", "지식·산출물 동기화", "사용자 최종 확인", "종료", "self-pm-tool 호출 지점 요약", "권한 경계"]
}
-->

# opal-self-pm (대화형 PM 직접 수행 루프)

## 0. 설계 원천과 경계

이 스킬은 OPAL을 사용하는 실제 개발 프로젝트에서 실행한다. 프로젝트 문서·코드·테스트 경로는 **대상 프로젝트의 PROJECT 문서와 실제 구성**에서 찾는다. OPAL 규칙·스킬·도구는 설치된 프레임워크 자산에서 읽으며, 대상 프로젝트에 `opal/` 소스 트리가 있다고 가정하지 않는다.


- 이 스킬이 `opal-self-pm` 대화형 루프 절차의 원문을 소유한다. 질문 루프·계약 승인·지식 동기화·최종 확인의 판정 기준은 이 문서와 `references/`가 정한다.
- 독립 검증 경계(생성자≠평가자 예외)와 GC 3종 호출 지점의 공유 계약은 `opal/core/references/harness/actor.md` §독립 검증 경계와 GC 호출 지점이 소유한다. 이 문서는 호출 시점만 규정하고 원문을 복제하지 않는다.
- 권한 경계(외부 skill·package 설치, 프로젝트 밖 쓰기, 비가역 변경, 허브·기본 브랜치 commit, merge·push·배포, 사용자 Gate)는 작업 방식 승인과 별개로 항상 유지된다. 등록된 전용 worktree 체크포인트의 모드별 예외를 포함한 원문은 `harness/guards.md`가 소유한다.
- `opal-self-pm`은 Pilot이 아니다. `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT를 읽지도 쓰지도 않는다. 현재 실행 기록은 `self-pm-tool`, 사건 이력은 `run-log-tool`, 사람이 검토할 수행 기록은 PM이 작성하는 태스크 문서가 소유한다. 기록 계약은 `references/task-records.md`를 따른다.

## 1. 루프 개요

```text
[진입] 정식 태스크 폴더 + TASK.md + self-pm/run-log 초기화
   │
   ▼
질문(1개) → 조회·검토·정리 → 질문(1개) → 조회·검토·정리 → ...
   │
   ▼ (결정 충분)
작업 계약 확정 (6항목)  ──[MUST] 승인 없이 쓰기 금지
   │
   ▼
사용자 실행 승인
   │
   ▼
PM 작업·검증  ──(범위 변경·새 결정 발생 시)──▶ 질문 단계로 복귀
   │
   ▼
지식·산출물 동기화 (8영역 전수 판정)
   │
   ▼
사용자 최종 확인  ──[MUST] 확인 전 완료 선언 금지
   │
   ▼
종료
```

질문 수를 미리 정하거나 고정 단계로 가장하지 않는다. 새로운 결정이나 범위 변경이 생기면 실행 중에도 질문 단계로 돌아간다(§6).

## 2. 진입

1. `pm/dispatch-process.md` Steps 1~3으로 현재 실행 범위·관련 brain·코드맵을 확인하고, `docs/PROJECT.md` 레지스트리에서 기획·설계·코드 컨벤션·운영 문서를 선별해 읽는다. 이때 관련 지식·문서와 선별 근거를 TASK.md의 **영향 후보 집합**으로 남겨 이후 동기화 입력으로 승계한다. 현재 세션에서 이미 읽었고 변경되지 않은 내용은 재사용하며, 변경·누락·범위 확대 시 해당 원천만 다시 읽는다. 기억만으로 확인을 생략하지 않는다.
2. `references/task-records.md`의 신규·재개 규칙으로 정식 태스크 폴더의 절대경로를 확정한다. 프로젝트 루트나 임시 폴더를 실행 기록 위치로 사용하지 않는다.
3. 같은 참조 문서에 따라 `TASK.md`와 두 도구의 실행 기록을 준비한다. 반환·확정한 태스크 경로와 `run_id`를 이후 모든 호출에 사용한다.

`TASK.md`·`DONE.md`는 PM이 수행하면서 남기는 필수 기록이다. `PLAN.md`·조사·검증 문서는 과정에서 필요할 때 작성한다. 문서 생성 자체를 단계 파이프라인이나 별도 승인 게이트로 만들지 않는다.

## 3. 질문 단계 — 한 개씩

질문 1개의 5요소 구성, 시점별 조회 우선순위는 `references/question-loop.md`를 따른다(이 문서에 복제하지 않는다).

- 질문을 제시할 때마다 기록한다:
  ```bash
  ~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
    --append-field open_questions "<질문 5요소 요약>"
  ```
- 사용자 답변 뒤 조회·정리를 마치면 확정된 결정을 기록한다:
  ```bash
  ~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
    --append-field decisions "<확정된 결정 요약>"
  ```
- 이미 답한 질문을 반복하지 않는다. 상태 값은 계속 `discovering`이다(변경 불필요 — 이미 그 값이므로 별도 `--status` 호출 생략 가능).

## 4. 작업 계약 확정 — [MUST] 쓰기 전 승인

**[MUST]** 파일·설정·데이터를 쓰기 전에 다음 6항목 계약을 한 번에 제시하고 사용자 승인을 받는다. 승인 전에는 계약 대상의 구현·설정·데이터 변경을 시작하지 않는다. 진입 시 태스크 채번·폴더·TASK.md 및 실행 기록을 준비하는 일은 스킬 수행 기록에 포함된다. 기존 사용자 발화로 승인된 범위는 TASK.md에 근거를 남기고 중복 승인받지 않는다.

1. 목표와 완료 조건
2. 포함 범위와 제외 범위
3. 변경 대상
4. 확정된 결정과 남은 가정
5. 검증 방법
6. 예상되는 docs·기획·설계·brain·memory 영향

6항목 계약과 승인 근거는 `TASK.md`에도 갱신한다. 계약을 확정하면 기록한다(6항목 전체를 배열로 전체 교체 — `approved_scope`는 계약 그 자체이므로 append가 아니라 set):
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
  --set-field approved_scope '["1. 목표/완료조건: ...", "2. 포함/제외 범위: ...", "3. 변경 대상: ...", "4. 결정/가정: ...", "5. 검증 방법: ...", "6. 예상 영향: ..."]' \
  --status awaiting_approval
```

사용자 승인 후에만 실행 단계로 넘어간다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> --status executing
```

승인 이후 계약 안의 가역적 작업은 연속 수행한다. **계약 밖 변경, 별도 권한 경계, 사용자 선택이 필요한 새 결정이 발생하면 작업을 멈추고 §3 질문 단계로 복귀한다**(§6).

## 5. PM 작업·검증

PM이 확정 계약에 따라 직접 조회·작성·수정한다. 중요한 진행·결정·검증·재시도는 `references/task-records.md`에 따라 발생 시점에 run-log로 남기고, 검토에 필요한 과정은 TASK.md 또는 선택 문서에 기록한다. 서브에이전트에게 구현을 넘기면 그 실행 단위는 PM 직접 수행으로 기록하지 않는다(§0, `actor.md` §독립 검증 경계).

작업 중 새 결정·변경 파일·소비자·범위가 초기 영향 후보에 없을 때만 후보를 증분 추가한다. 이미 확인한 PROJECT·brain·관련 문서를 전체 재탐색하지 않는다.

- 파일을 바꿀 때마다 기록한다:
  ```bash
  ~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
    --append-field changed_files "<변경 파일 경로>"
  ```
- `header-rules.md` §갱신 시점 (4단) (a) — 파일 변경과 같은 자리에서 @header를 기록한다(신규 `.md`/`.py` 파일 포함).
- 검증(정적·동적)을 수행할 때마다 기록한다:
  ```bash
  ~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
    --append-field validation "<검증 방법과 결과>"
  ```

### 수정 전 컨벤션과 테스트 근거

**[MUST]** 코드·설정 수정 전에 대상 프로젝트의 PROJECT 문서가 연결한 공통·영역별 컨벤션, 하위 지침, 린터·포매터·테스트 설정과 인접 코드의 기존 방식을 확인한다. 읽은 경로·적용 규칙을 TASK.md에 남긴다. 현재 세션에서 확인한 규칙이 유효하면 재사용하되 변경 영역이 넓어지면 다시 선별한다. 문서가 없으면 실제 설정과 기존 코드에서 확인한 관례를 기록하며, 부재를 규칙 확인 생략으로 처리하지 않는다.

**[MUST]** 검증은 `references/testing-evidence.md`에 따라 계획·실행하고 실제 결과와 재현 가능한 증거를 보존한다. `opal-e2e` 스킬을 이용한 테스트의 적용 여부를 매 작업 검토해 실행 또는 미실행 근거를 남긴다. 테스트 증거와 E2E 검토 기록이 빠진 상태로 최종 확인을 요청하지 않는다.

### GC 3종 호출 지점

독립 검증(보안·컨벤션·리포트)이 필요하면 `op-gc-security`·`op-gc-convention`·`op-gc-report`를 **호출만** 한다(스킬 본체·파라미터·finding 스키마는 변경하지 않는다). 입력 필드는 각 스킬이 소유하며 이 문서는 복제하지 않는다 — `op-gc-security`는 `opal/skills/op-gc-security/SKILL.md` §1, `op-gc-convention`은 `opal/skills/op-gc-convention/SKILL.md` §입력, `op-gc-report`는 `opal/skills/op-gc-report/SKILL.md` §입력과 책임을 그대로 따른다. `project_root`·`target_files`(=현재까지 `changed_files`)·`output_dir`·`timestamp`를 채워 호출한다.

**[MUST]** 생성자≠평가자 원칙에 따라 PM이 직접 채점하지 않는다 — 독립 검증은 서브에이전트로 위임한다(제안서 §3.2 독립 검증 예외). PM은 검증 입력·범위·채택 기준과 후속 수정만 소유한다.

호출 결과는 `validation` 필드에 요약해 기록한다(위 예시와 동일한 `--append-field validation` 호출).

### 완료 게이트 — code-scan validate

완료 직전(§7 진입 전) `git diff --name-only HEAD`(+untracked)로 변경 파일을 재구성해 `code-scan validate --changed <목록>`을 실행한다. 판정·차단 조건은 `opal/core/references/harness/header-rules.md` §갱신 시점 (4단) (d)를 참조한다(원문 복제 없음). 차단되면 §7 지식 동기화에 앞서 그 자리에서 @header를 기록해 재검증한다.

## 6. 범위 변경 시 복귀

작업 중 계약 밖 변경, 별도 권한 경계, 새로운 사용자 결정이 필요한 지점이 발견되면 즉시 작업을 멈추고 §3 질문 단계로 복귀한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
  --status discovering --append-field open_questions "<범위 변경으로 새로 결정할 질문>"
```
재확정된 범위는 §4를 다시 거쳐 새 계약으로 승인받는다(이전 `approved_scope`는 새 계약으로 전체 교체된다).

## 7. 지식·산출물 동기화

완료 직전에는 §2에서 승계한 영향 후보 집합에 실행 중 증분과 최종 `changed_files`·결정을 대조한다. PROJECT·brain·관련 문서를 처음부터 다시 검색하지 않는다. 새 범위·새 용어·새 소비자·경로 불일치가 발견된 부분만 제한적으로 추가 조회하고, 후보를 실제 동기화한 뒤 8영역을 누락 방지 관점으로 모두 판정한다. 판정 기준·owner 문서·"무근거 생략 금지" [MUST]는 `references/knowledge-sync.md`를 따른다(이 문서에 복제하지 않는다).

`update` 판정은 실제 갱신·추가와 검증을 마친 뒤 기록한다. 수행 예정 표시만으로 닫지 않는다. 작업 결과·검증·지식 동기화 근거는 `DONE.md`에 작성하고, 표준 로그를 `validate-run`으로 검증한다(`references/task-records.md`).

8영역의 현재 판정을 한 번에 기록한다. 초기 판정과 보정 판정이 충돌하지 않도록 append하지 않고 항상 전체 교체한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
  --set-field knowledge_impact '["기획: ...", "설계: ...", "프로젝트 문서: ...", "CONVENTIONS: ...", "SECURITY: ...", "brain: ...", "memory: ...", "code-scan: ..."]'
```

8영역 전부가 `update` 또는 `no-op + 근거`로 닫힌 뒤에만 `awaiting_confirmation`으로 전이한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> --status awaiting_confirmation
```

## 8. 사용자 최종 확인 — [MUST] 완료 선언 금지

**[MUST]** 사용자에게 6항목 계약 이행 결과와 8영역 판정을 제시하고 최종 확인을 요청한다. **사용자가 확인을 발화하기 전에는 완료를 선언하지 않는다** — "완료했습니다"·"끝났습니다" 류의 종결 발화를 이 시점 이전에 하지 않는다.

- 사용자가 확인하면 종료로 진행한다.
- 수정 의견이 있으면 그 응답을 기존 확인 gate의 보정 요청으로 기록하고 §3 질문·조회·정리 루프로 돌아간다(§6과 동일 경로). 보정·재검증 뒤에는 새 확인 gate를 요청하며, 수정 의견 자체를 최종 확인으로 해석하지 않는다.

## 9. 종료

사용자 최종 확인 발화 이후에만 DONE.md에 확인 결과를 반영하고, 최종 결정 사건 기록·run-log 검증을 마친 뒤 종료 상태를 기록한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> --status done
```

## 10. self-pm-tool 호출 지점 요약

| 단계 전이 | 명령 | 대상 필드 |
|---|---|---|
| 진입 | `init --objective` | (스켈레톤 8필드, `status: discovering`) |
| 질문 제시 | `update --append-field open_questions` | `open_questions` |
| 답변 후 정리 | `update --append-field decisions` | `decisions` |
| 계약 확정 | `update --set-field approved_scope '[...]' --status awaiting_approval` | `approved_scope`, `status` |
| 실행 승인 | `update --status executing` | `status` |
| 파일 변경 | `update --append-field changed_files` | `changed_files` |
| 검증 수행(GC 3종 포함) | `update --append-field validation` | `validation` |
| 범위 변경 복귀 | `update --status discovering --append-field open_questions` | `status`, `open_questions` |
| 지식 동기화 판정 | `update --set-field knowledge_impact '[8건...]'` | `knowledge_impact` 전체 교체 |
| 동기화 완료 | `update --status awaiting_confirmation` | `status` |
| 최종 확인 후 | `update --status done` | `status` |

`--set-field`/`--append-field` 대상은 6개 리스트 필드(`decisions`·`open_questions`·`approved_scope`·`changed_files`·`validation`·`knowledge_impact`)로 폐쇄이며, `objective`는 `init` 전용, `status`는 폐쇄 집합(`discovering`·`awaiting_approval`·`executing`·`awaiting_confirmation`·`done`) 값만 허용된다 — 그 외 값·미지 필드는 도구가 `{"ok":false,...}`로 거부한다.

## 11. 권한 경계

직접 수행 선택은 작업 방식의 승인이지 다음의 포괄 승인이 아니다 — 외부 skill·package 설치와 계정·MCP 연결, 프로젝트 밖 또는 외부 시스템 쓰기, 파괴적 변경과 비가역 데이터 마이그레이션, 허브·기본 브랜치 commit, merge·push·배포, Pilot과 harness가 정한 사용자 Gate. 등록된 전용 worktree 체크포인트의 모드별 예외를 포함한 원문은 제안서 §3.3·`harness/guards.md`가 소유한다.

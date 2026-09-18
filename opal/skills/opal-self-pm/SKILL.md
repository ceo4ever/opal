---
name: opal-self-pm
description: |
  **대화형 PM 직접 수행 루프**. Pilot이 아니라 종료 조건을 가진 질문 반복형 작업 루프다 — 질문 1개→조회·정리를 반복해 범위를 확정하고, PM이 직접 조회·작성·수정·검증을 수행하며, 완료 전 지식 영향을 전수 판정한 뒤 사용자 최종 확인을 받고서야 종료한다.
  필수 입력: 사용자의 자연어 요청(목표)과 실행 맥락(진행 중이면 해당 `tasks/NNN/` 폴더, 아니면 프로젝트 루트).
  보장 출력: 사용자와 합의한 계약 범위 안의 산출물 변경, `self-pm-tool` 경량 실행 기록(8필드 JSON), 8영역(기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan) 지식 동기화 판정(`update` 또는 `no-op + 근거`).
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
  "description": "질문 1개→조회·정리 반복으로 범위를 확정하고 PM이 직접 조회·작성·수정·검증을 수행한 뒤 8영역 지식 동기화 판정과 사용자 최종 확인을 거쳐 종료하는 대화형 PM 직접 수행 루프를 규정한다.",
  "exports": ["설계 원천과 경계", "루프 개요", "진입", "질문 단계", "작업 계약 확정", "PM 작업·검증", "범위 변경 시 복귀", "지식·산출물 동기화", "사용자 최종 확인", "종료", "self-pm-tool 호출 지점 요약", "권한 경계"]
}
-->

# opal-self-pm (대화형 PM 직접 수행 루프)

## 0. 설계 원천과 경계

- 이 스킬이 `opal-self-pm` 대화형 루프 절차의 원문을 소유한다. 질문 루프·계약 승인·지식 동기화·최종 확인의 판정 기준은 이 문서와 `references/`가 정한다.
- 독립 검증 경계(생성자≠평가자 예외)와 GC 3종 호출 지점의 공유 계약은 `opal/core/references/harness/actor.md` §독립 검증 경계와 GC 호출 지점이 소유한다. 이 문서는 호출 시점만 규정하고 원문을 복제하지 않는다.
- 권한 경계(외부 skill·package 설치, 프로젝트 밖 쓰기, 비가역 변경, 허브·기본 브랜치 commit, merge·push·배포, 사용자 Gate)는 작업 방식 승인과 별개로 항상 유지된다. 등록된 전용 worktree 체크포인트의 모드별 예외를 포함한 원문은 `harness/guards.md`가 소유한다.
- `opal-self-pm`은 Pilot이 아니다. `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT를 읽지도 쓰지도 않는다. 경량 실행 기록은 별도 `self-pm-tool`이 전담한다(§3).

## 1. 루프 개요

```text
[진입] self-pm-tool init
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

1. `task_root`를 정한다 — 대화가 특정 `tasks/NNN/` 폴더 맥락(예: 진행 중인 태스크 안에서 발동)이면 그 폴더, 아니면 프로젝트 루트.
2. run 기록을 생성한다.
   ```bash
   ~/.opal/tools/self-pm-tool/run.sh init --task-root <task_root> --objective "<사용자 요청 원문>"
   ```
   반환된 `run_id`를 이후 모든 `update`/`show` 호출에 사용한다. 생성 직후 `status`는 도구가 `discovering`으로 채운다(별도 `update` 불필요).

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

**[MUST]** 파일·설정·데이터를 쓰기 전에 다음 6항목 계약을 한 번에 제시하고 사용자 승인을 받는다. 승인 없이는 어떤 쓰기도 시작하지 않는다.

1. 목표와 완료 조건
2. 포함 범위와 제외 범위
3. 변경 대상
4. 확정된 결정과 남은 가정
5. 검증 방법
6. 예상되는 docs·기획·설계·brain·memory 영향

계약을 확정하면 기록한다(6항목 전체를 배열로 전체 교체 — `approved_scope`는 계약 그 자체이므로 append가 아니라 set):
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

PM이 확정 계약에 따라 직접 조회·작성·수정한다. 서브에이전트에게 구현을 넘기면 그 실행 단위는 PM 직접 수행으로 기록하지 않는다(§0, `actor.md` §독립 검증 경계).

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

### GC 3종 호출 지점

독립 검증(보안·컨벤션·리포트)이 필요하면 `op-gc-security`·`op-gc-convention`·`op-gc-report`를 **호출만** 한다(스킬 본체·파라미터·finding 스키마는 변경하지 않는다). 입력 필드는 각 스킬이 소유하며 이 문서는 복제하지 않는다 — `op-gc-security`는 `opal/skills/op-gc-security/SKILL.md` §1, `op-gc-convention`은 `opal/skills/op-gc-convention/SKILL.md` §입력, `op-gc-report`는 `opal/skills/op-gc-report/SKILL.md` §입력과 책임을 그대로 따른다. `project_root`·`target_files`(=현재까지 `changed_files`)·`output_dir`·`timestamp`를 채워 호출한다.

**[MUST]** 생성자≠평가자 원칙에 따라 PM이 직접 채점하지 않는다 — 독립 검증은 서브에이전트로 위임한다(제안서 §3.2 독립 검증 예외). PM은 검증 입력·범위·채택 기준과 후속 수정만 소유한다.

호출 결과는 `validation` 필드에 요약해 기록한다(위 예시와 동일한 `--append-field validation` 호출).

### 완료 게이트 — code-scan validate

완료 직전(§6 진입 전) `git diff --name-only HEAD`(+untracked)로 변경 파일을 재구성해 `code-scan validate --changed <목록>`을 실행한다. 판정·차단 조건은 `opal/core/references/harness/header-rules.md` §갱신 시점 (4단) (d)를 참조한다(원문 복제 없음). 차단되면 §6 지식 동기화에 앞서 그 자리에서 @header를 기록해 재검증한다.

## 6. 범위 변경 시 복귀

작업 중 계약 밖 변경, 별도 권한 경계, 새로운 사용자 결정이 필요한 지점이 발견되면 즉시 작업을 멈추고 §3 질문 단계로 복귀한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
  --status discovering --append-field open_questions "<범위 변경으로 새로 결정할 질문>"
```
재확정된 범위는 §4를 다시 거쳐 새 계약으로 승인받는다(이전 `approved_scope`는 새 계약으로 전체 교체된다).

## 7. 지식·산출물 동기화

완료 직전 8영역을 모두 판정한다. 판정 기준·owner 문서·"무근거 생략 금지" [MUST]는 `references/knowledge-sync.md`를 따른다(이 문서에 복제하지 않는다).

각 영역 판정을 기록한다(영역마다 1회 append, 또는 한 번에 8건을 순서대로 append):
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> \
  --append-field knowledge_impact "<영역>: update|no-op - <근거>"
```

8영역 전부가 `update` 또는 `no-op + 근거`로 닫힌 뒤에만 `awaiting_confirmation`으로 전이한다:
```bash
~/.opal/tools/self-pm-tool/run.sh update --task-root <task_root> --run-id <run_id> --status awaiting_confirmation
```

## 8. 사용자 최종 확인 — [MUST] 완료 선언 금지

**[MUST]** 사용자에게 6항목 계약 이행 결과와 8영역 판정을 제시하고 최종 확인을 요청한다. **사용자가 확인을 발화하기 전에는 완료를 선언하지 않는다** — "완료했습니다"·"끝났습니다" 류의 종결 발화를 이 시점 이전에 하지 않는다.

- 사용자가 확인하면 종료로 진행한다.
- 수정 의견이 있으면 §3 질문·조회·정리 루프로 돌아간다(§6과 동일 경로).

## 9. 종료

사용자 최종 확인 발화 이후에만 기록하고 종료한다:
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
| 지식 동기화 판정 | `update --append-field knowledge_impact` (8회 또는 순차) | `knowledge_impact` |
| 동기화 완료 | `update --status awaiting_confirmation` | `status` |
| 최종 확인 후 | `update --status done` | `status` |

`--set-field`/`--append-field` 대상은 6개 리스트 필드(`decisions`·`open_questions`·`approved_scope`·`changed_files`·`validation`·`knowledge_impact`)로 폐쇄이며, `objective`는 `init` 전용, `status`는 폐쇄 집합(`discovering`·`awaiting_approval`·`executing`·`awaiting_confirmation`·`done`) 값만 허용된다 — 그 외 값·미지 필드는 도구가 `{"ok":false,...}`로 거부한다.

## 11. 권한 경계

직접 수행 선택은 작업 방식의 승인이지 다음의 포괄 승인이 아니다 — 외부 skill·package 설치와 계정·MCP 연결, 프로젝트 밖 또는 외부 시스템 쓰기, 파괴적 변경과 비가역 데이터 마이그레이션, 허브·기본 브랜치 commit, merge·push·배포, Pilot과 harness가 정한 사용자 Gate. 등록된 전용 worktree 체크포인트의 모드별 예외를 포함한 원문은 제안서 §3.3·`harness/guards.md`가 소유한다.

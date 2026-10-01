---
template: self-pm-task
actor: PM
---

# TASK: OPPB run root 태스크 귀속

## 요청과 목표

OPPB 실행 운영 기록이 허브의 `.opal-runs/<run_id>/`에 누적되는 현행 구조를 재검토하고,
해당 OPPB 태스크 폴더 아래에서 태스크 수행 중에만 사용하는 구조로 변경한다.

## 완료 기준

- OPPB run root의 생성·조회·재개 경로가 해당 OPPB 태스크에 귀속된다.
- 실행 중 Supervisor 장애 복구 계약은 유지된다.
- 공유 캐시와 태스크별 실행 기록의 수명·소유권이 분리된다.
- 종료 시 정리와 최종 증거 보존 계약이 문서·도구·테스트에서 일치한다.
- 관련 회귀 테스트와 정적 검증이 통과한다.

## 현재 범위

- 포함 후보: OPPB Product Flow 스킬, `oppb-runtime-tool`, run root 소비 단계 스킬,
  관련 harness·설계 문서·테스트.
- 유지 후보: 여러 태스크가 공유하는 `.opal-cache/oppb/`의 허브 배치.
- 제외 후보: 기존 `.opal-runs` 데이터의 즉시 삭제·마이그레이션, Git commit·merge·push.

## 선조회 근거와 제약

- `docs/proposals/opal-oppb-project-build-pilot.md §4.5`: 현행 run root를
  `<allocator_root>/.opal-runs/<run_id>/`로 두고 worktree 회수 뒤에도 보존한다.
- `tasks/backup/132-260914-opd-oppb-프로젝트빌드-파일럿-신설/TASK.md AC-11`:
  필수 복구 요구는 Supervisor 비정상 종료 후 재부착·수확과 자동 tick 재개다.
- `.opal/brain` 검색에서 `.opal-runs` 관련 과거 지식 페이지는 발견되지 않았다.
- 검색 재현: `brain-tool search 'run root task lifecycle cache allocator' --type concept` 결과 0건.
- code-scan은 `oppb-runtime-tool`이 run root의 writer·consumer임을 확인했다.
- 사용자 소유의 기존 미추적 `.claude/skills/`는 수정하거나 되돌리지 않는다.

## 확정된 결정

- `//oppm`으로 PM 직접 수행한다.
- OPPB 실행 기록은 허브보다 해당 OPPB 태스크에 귀속시키는 방향을 권고안으로 삼는다.
- run root의 정확한 경로는 `<oppb_task_path>/.oppb-run/<run_id>/`로 확정한다.
- 공유 캐시 `.opal-cache/oppb/`는 실행 기록과 별도 수명으로 본다.
- 성공 완료 후 로그·결과·검증 증거·최종 상태는 태스크에 보존하고 PID·lock·임시
  sandbox·임시 index처럼 무효화된 런타임 파일만 정리한다. 실패·중단 상태는 전체를
  유지한다.
- 동작 계약은 OPPB에만 적용한다. 공용 `op-scenario-gate`는 `pilot: oppb` 확장만,
  공용 `worktree.md`는 `.opal-runs` 허브 예외 문구만 정합화한다. `opal-agent`는 경로
  비의존 `run_dir` 계약을 유지하며 표준 run-log·OPPL `.oppl-run`·OPD·OPDS·OPSDD는
  변경하지 않는다.
- 기존 허브 `.opal-runs` 7개 실행 기록은 이동·삭제하지 않고, 신규 OPPB 실행부터
  `<oppb_task_path>/.oppb-run/<run_id>/`를 사용한다.
- 신규 `init`은 태스크 내부 경로만 생성하되, 기존 `.opal-runs/<run_id>` 형식은
  `status`·`resume`·조회 대상으로 legacy 수용한다. 현재 프로젝트의 기존 폴더는 사용자가
  이미 삭제했으며 실측 결과도 부재다.

## 남은 질문

- 없음. 작업 계약은 사용자 승인되어 실행 중이다.

## 작업 계약 — 승인됨

### 1. 목표와 완료 조건

- 신규 OPPB run root를 `<oppb_task_path>/.oppb-run/<run_id>/`에 생성한다.
- 실행 중 장애 복구와 실패·중단 재개는 유지한다.
- 성공 종료 시 로그·결과·검증 증거·최종 상태는 해당 태스크에 남기고, PID·lock·임시
  sandbox·임시 index처럼 수명이 끝난 런타임 파일만 제거한다.
- 기존 허브 run root는 legacy 조회·재개가 가능하고 신규 허브 run root는 생성되지 않는다.

### 2. 포함 범위와 제외 범위

- 포함: OPPB Product Flow, `oppb-runtime-tool`, OPPB 단계 스킬, 공용
  `op-scenario-gate`의 `pilot: oppb` 분기, worktree의 `.opal-runs` 예외 문구, 관련 문서·스키마·테스트.
- 제외: OPD·OPDS·OPSDD·OPPL·OPPM 동작, 표준 run-log 계약, `opal-agent`의 경로 비의존
  `run_dir` 계약, `.opal-cache/oppb` 위치, 기존 `.opal-runs` 데이터 이동·삭제, commit·merge·push·배포.

### 3. 변경 대상

- 구현·테스트: `opal/tools/oppb-runtime-tool/oppb_runtime_tool.py`, `README.md`, schema 설명,
  `tests/test_oppb_init.py` 및 경로·종료 정리 관련 OPPB 회귀 테스트.
- 스킬: `opal/skills/opal-pilot-project-build/SKILL.md`,
  `opal/skills/op-oppb-knowledge-finalize/{SKILL.md,README.md}`,
  `opal/skills/op-scenario-gate/SKILL.md`의 OPPB 확장.
- 계약 문서: `opal/core/references/harness/worktree.md`,
  `docs/proposals/opal-oppb-project-build-pilot.md` 및 직접 연결된 현재 사실 설명.

### 4. 확정 결정과 남은 가정

- `init`에 OPPB 태스크 절대경로 입력을 추가하고 새 run root는 그 경로에서만 발급한다.
- 운영 root와 보존 기록은 Git 미추적 상태를 유지한다. P5 finalize는 worktree 회수 전에
  정리된 보존 묶음을 canonical 태스크 폴더에 남기며, `DONE.md` manifest가 이를 가리킨다.
- legacy `.opal-runs`는 manifest 기반으로만 허용하고 cwd·경로 문자열 추론은 도입하지 않는다.
- 구현 중 새로운 외부 계약이나 데이터 손실 선택이 발견되면 질문 단계로 복귀한다.

### 5. 검증 방법

- 공개 CLI RED/GREEN 테스트로 신규 task path 생성, 허브 미생성, ignore 판정, 잘못된 경로 거부,
  legacy status/resume 수용, 성공 종료 보존/임시 정리를 검증한다.
- `oppb-runtime-tool` 전체 단위·통합 테스트와 관련 `op-scenario-gate` 계약 검사를 실행한다.
- `rg`로 활성 문서의 낡은 신규 생성 경로가 남지 않았는지 확인하고 변경 파일
  `code-scan validate`를 수행한다.
- `opal-e2e` 적용 여부를 검토하고, 독립 보안·컨벤션 검증이 필요한 변경은 별도 평가자로 확인한다.

### 6. 예상 지식·문서 영향

- OPPB 스킬·도구 README·schema·worktree owner 문서·설계 제안서의 경로와 수명 계약은 갱신 대상이다.
- PROJECT 레지스트리·CONVENTIONS·SECURITY·brain·memory·code-scan은 완료 전 실제 변경과
  재사용 가치에 따라 각각 `update` 또는 `no-op + 근거`로 판정한다.

## 실행 기록

- run_id: `run_80630d63-6ee6-4c4f-bbe5-3d2ac6b955e3`
- self-pm: `.opal/self-pm/run_80630d63-6ee6-4c4f-bbe5-3d2ac6b955e3.json`
- run-log: `run/run-log-run_80630d63-6ee6-4c4f-bbe5-3d2ac6b955e3-0001.jsonl`
- 상태: `executing`

## 작업 계약과 승인

6항목 작업 계약은 사용자가 승인했다. 신규 OPPB 실행에만 태스크 귀속 경로를 적용하고,
legacy 허브 실행은 읽기·재개 호환으로 유지하며 기존 데이터는 이동·삭제하지 않는다.

## 구현·검증 진행

- RED: [`evidence/RED.md`](evidence/RED.md) — 신규 CLI 계약 구현 전 `9 failed, 12 passed`.
- 1차 GREEN: `test_oppb_init.py` `22 passed`; 표준 실행 로그 sequence 10 validation 사건에 기록.
- OPPB 전체 회귀 1차에서 allocator와 project가 다른 fixture의 cache exclude 등록 위치 오류를
  발견했고, cache exclude를 allocator repository에 별도 등록하도록 수정했다.
- 영향 테스트: cache+probe `26 passed`, controller+checkpoint+recovery+product-flow `36 passed`.
- 최종 GREEN: [`evidence/GREEN.md`](evidence/GREEN.md) — 신규 경계 `30 passed`, 전체 OPPB
  runtime `154 passed, 13 subtests passed`, OPPL/opal-agent 비영향 `18 passed`; 표준 실행 로그
  sequence 12 validation 사건에 같은 증거 경로를 기록했다.
- `code-scan validate --changed -`: `OK`, coverage `63.6% (14/22)`; 새 미포함 파일 0건.
- brain 선조회 0건 뒤 `.opal/brain/pages/concept/oppb-run-records-follow-task-lifecycle.md`를
  `brain-tool add-page`로 등록했다. 프로젝트 전체 brain validate/lint의 기존 구조 결손은 별도
  baseline으로 관측했으며 새 페이지·index·log 생성은 확인했다.
- 독립 보안·컨벤션 1차 보고서는 `evidence/GC-SECURITY-20260926T091900Z.md`와
  `evidence/GC-CONVENTION-20260926T091900Z.md`다. 차단 findings를 수정하고 재검증 중이다.
- 독립 최종 판정: 보안 `GC-SECURITY-20260926T094658Z-final.md` **PASS**, 컨벤션
  `GC-CONVENTION-20260926T091900Z-final-recheck.md` **PASS_WITH_ADVISORIES**(blocking 0).

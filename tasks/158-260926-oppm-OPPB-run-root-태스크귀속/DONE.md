<!--
@header {
  "module": "oppm-158-done",
  "layer": "document",
  "domain": "oppb-runtime",
  "description": "OPPB run root 태스크 귀속 변경, 검증, 지식 동기화와 사용자 최종 확인 상태를 기록한다.",
  "exports": []
}
-->

# DONE: OPPB run root 태스크 귀속

## 결과

- 신규 OPPB run은 `<oppb_task_path>/.oppb-run/<run_id>/`에 생성한다.
- 공유 cache만 `<allocator_root>/.opal-cache/oppb/`에 유지한다.
- 성공 run은 P5 worktree 회수 전에 `finalize-run`으로 허브 canonical 태스크에 게시한다.
  로그·결과·evidence·최종 상태는 남기고 lock·Supervisor identity·임시 index·검증 sandbox는 제거한다.
- 실패·중단 run은 닫거나 정리하지 않아 그대로 재개할 수 있다.
- 기존 `<allocator_root>/.opal-runs/<run_id>/`는 신규 생성하지 않으며 status·resume legacy 호환만 유지한다.
- OPPL `.oppl-run`, 표준 run-log, `opal-agent --run-dir`, 다른 Pilot 동작은 변경하지 않았다.

## 보안·무결성

- source 완료 판정과 copy는 Supervisor·workgraph lock을 함께 획득한 snapshot에서 수행한다.
- source lock과 destination 조상은 directory fd·`O_NOFOLLOW`로 고정하며 symlink·특수파일을 거부한다.
- 보존 hash는 domain/type/path length/path/content length/content framing을 사용하고, 멱등 재호출과
  archived status가 현재 tree를 다시 검증한다.
- 명시 `--allocator-root`는 run manifest와 대조한다.

## 검증

- RED: [`evidence/RED.md`](evidence/RED.md) — `9 failed, 12 passed`.
- GREEN: [`evidence/GREEN.md`](evidence/GREEN.md) — 신규 경계 `30 passed`, OPPB runtime 전체
  `154 passed, 13 subtests passed`, OPPL/opal-agent 호환 `18 passed`.
- 정적: Python compile, JSON schema parse, schema sha256, `git diff --check` 통과.
- code-scan: `newly_uncovered=0`, pre-existing uncovered 11건만 존재, exit 0.
- 독립 보안: [`GC-SECURITY-20260926T094658Z-final.md`](evidence/GC-SECURITY-20260926T094658Z-final.md)
  — PASS, blocking/advisory 0.
- 독립 컨벤션: [`GC-CONVENTION-20260926T091900Z-final-recheck.md`](evidence/GC-CONVENTION-20260926T091900Z-final-recheck.md)
  — PASS_WITH_ADVISORIES, blocking 0.
- `opal-e2e`는 브라우저·HTTP·UI 표면이 없는 파일 시스템 CLI 변경이라 미적용했다. 승인 계약에서
  배포가 제외되어 설치본 재배포 검증은 수행하지 않았다.

## 지식 동기화

| 영역 | 판정 | 근거 |
|---|---|---|
| 기획 | update | OPPB P0/P5 및 제안서의 경로·보존·legacy 정책 갱신 |
| 설계 | update | runtime README·schema 설명·worktree owner 계약 갱신 |
| 프로젝트 문서 | no-op | PROJECT 레지스트리에 기존 owner가 모두 등록됨 |
| CONVENTIONS | no-op | 기존 규칙 준수, 신규 예외 없음 |
| SECURITY | update | `docs/SECURITY.md §8` 보존 경계 추가 |
| brain | update | `oppb-run-records-follow-task-lifecycle` concept 등록 |
| memory | no-op | 미해결 후속 없음; task number 158 발급만 반영 |
| code-scan | update | 신규 brain page header 추가 및 완료 게이트 통과 |

## 남은 사항

- 사용자가 로컬 배포를 완료했다고 알렸고, 이어서 이 태스크 변경분의 commit을 명시적으로 요청했다. merge·push는 수행하지 않는다.
- 사용자 최종 확인 상태: **대기**.

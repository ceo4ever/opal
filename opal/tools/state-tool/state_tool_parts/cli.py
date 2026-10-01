# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.cli",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool CLI — argparse 파서 구성과 main 진입",
  "exports": [
    "build_parser",
    "main"
  ]
}
"""

import argparse
import pathlib

from .codes import (
    STAGE_ENUM,
    STATUS_COMPLETED_UNMERGED,
    VALID_MODES,
)
from .base import (
    resolve_task_path,
    state_writer_lock,
)
from .run_log import (
    _PM_ACTIVITY_KIND_ENUM,
    _PM_REPORT_TYPE_ENUM,
    _PM_TRANSITION_ACTION_ENUM,
    cmd_gate_request,
    cmd_gate_resolve,
    cmd_log_event,
)
from .gates import (
    cmd_design_decision,
    cmd_design_gate_record,
    cmd_design_gate_reset,
    cmd_design_gate_start,
    cmd_event_verify,
    cmd_verify,
)
from .commands_core import (
    _worker_duration_minutes,
    cmd_add_row,
    cmd_advance,
    cmd_block,
    cmd_init,
    cmd_mark,
    cmd_resolve_mode,
    cmd_resolve_start,
    cmd_show,
    cmd_spec_validate,
    cmd_status,
    cmd_validate,
)
from .commands_run import (
    cmd_boot_summary,
    cmd_finalize_attribution,
    cmd_gate_pass,
    cmd_run_start,
    cmd_test_clock,
    cmd_test_metrics,
)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정 (PLAN §2.19 E-2 매트릭스 그대로)
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="state-tool",
        description="OPAL 파이프라인 현황판 JSON SSOT 관리 CLI (PLAN §2.19 E-2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (11종):
  init          state.json + STATE.md 생성
  show          현황판 출력 (md/json/full)
  advance       ⬜→🔄 전환
  mark          ⬜/🔄→✅ 전환 (--done 필수)
  block         any→❌ 전환 + current_status=blocked
  validate      정합성 검증 → violations[]
  add-row       추가작업 행 삽입
  status        current_status 명시 전환
  finalize-attribution  merge 확인 후 허브 MEMORY history 귀속 (--allocator-root 필수)
  spec-validate pipeline.json 스펙 검증 (070 R-6)
  event-verify  단계 진입용 event-loader receipt 검증 (상태 비접촉)
  gate-pass     [DEPRECATED] Gate 4행 일괄 ✅ 처리 (레거시 state.json 전용)

행 주소(070): --task-step <key> / --task-step-id <n> / --row <n>[deprecated] 중 하나만 지정.
호출 형식: ~/.opal/tools/state-tool/run.sh <command> <task-path> [options]
종료 코드: 0=ok  1=violation/scope_error  2=internal_error
"""
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="state.json + STATE.md 생성 (§2.11 G-8)")
    p_init.add_argument("task_path", metavar="<task-path>")
    p_init.add_argument("--skill", required=True,
                        choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd","oppb","opd2"])
    p_init.add_argument("--mode", required=True,
                        choices=["interactive","semi-agentic","agentic"])
    p_init.add_argument("--task-title")
    p_init.add_argument("--next-action")
    rows_group = p_init.add_mutually_exclusive_group()  # C-1
    rows_group.add_argument("--rows-spec", metavar="<inline-json>")
    rows_group.add_argument("--rows-from", metavar="<path>",
                        help="SKILL.md(레거시, deprecated 경고) 또는 pipeline.json(070 신규, 확장자로 분기)")
    p_init.add_argument("--rows-acts", metavar="<inline-json>",
                        help="opsdd ACT 동적 주입 (시그니처만, 미구현 — R-13)")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--note")
    # 094 D-2: 저널화로 파싱 대상(파이프라인 표)이 소멸 — cmd_init이 즉시 거부.
    # 인자 정의는 하위 호환을 위해 유지하되 help는 감춘다(§3.2.2 (2)).
    p_init.add_argument("--import-existing", action="store_true", dest="import_existing",
                        help=argparse.SUPPRESS)
    p_init.add_argument("--worktree", metavar="<path>",
                        help="worktree 코드 작업본 절대경로 (092). 미지정 시 state.json에 키를 생성하지 않는다.")
    # CONTRACT §2.5 state-tool.init.run-log-mode — 기본값 shadow(135 ADD-2).
    # 모든 신규 태스크가 기록 계약을 갖게 해 pilot별 적용 여부에 따른 집계 구멍을
    # 없앤다. `off`는 기존 1.1 경로를 그대로 타는 명시적 비활성화다.
    p_init.add_argument("--run-log-mode", dest="run_log_mode",
                        choices=["shadow", "active", "off"], default="shadow",
                        help="실행 로그 계약 활성화 모드 (기본 shadow. off는 1.1 경로 유지, "
                             "active는 --profiles의 --channel-id 항목이 있을 때만 수용)")
    p_init.add_argument("--channel-id", dest="channel_id",
                        help="--run-log-mode active 전용 (T02 범위 밖 — profiles.json 미배포)")
    p_init.add_argument("--profiles", dest="profiles",
                        help="--run-log-mode active 전용 (T02 범위 밖)")
    # 156 DEC-4: pm은 legacy 값이라 choices에 남겨 두고 cmd_init이 actor_pm_retired로 거부한다.
    p_init.add_argument("--actor", choices=["coordinator", "worker", "pm"],
                        help="실행 주체(opd/opds 전용). 미지정 시 state.json에 키를 생성하지 않는다.")
    p_init.add_argument("--workspace", choices=["worktree", "hub"],
                        help="resolve-start가 판정한 작업본. worktree는 --worktree 필수, "
                             "oppb는 hub 불가. 미지정 시 기존 동작.")
    p_init.set_defaults(func=cmd_init)

    # ── show ──
    p_show = sub.add_parser("show", help="현황판 출력 (§2.14 G-11)")
    p_show.add_argument("task_path", metavar="<task-path>")
    p_show.add_argument("--format", dest="format", choices=["md","json","full"], default="md")
    p_show.set_defaults(func=cmd_show)

    p_mode = sub.add_parser(
        "resolve-mode",
        help="effective mode 판정 (explicit > state > new-task default)",
    )
    p_mode.add_argument("task_path", metavar="<task-path>")
    p_mode.add_argument("--mode", choices=sorted(VALID_MODES))
    p_mode.add_argument("--new-task", action="store_true", dest="new_task")
    p_mode.add_argument("--skill", help="신규 태스크 기본 mode를 Pilot별 표로 판정 (미지정 시 semi-agentic)")
    p_mode.set_defaults(func=cmd_resolve_mode)

    # ── resolve-start (156) ──
    p_start = sub.add_parser(
        "resolve-start",
        help="Pilot 시작·재개의 mode·workspace·actor 판정 (신규는 init 인자 반환)",
    )
    p_start.add_argument("task_path", metavar="<task-path>")
    p_start.add_argument("--skill", required=True,
                         choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd","oppb","opd2"])
    p_start.add_argument("--new-task", action="store_true", dest="new_task")
    p_start.add_argument("--interactive", action="store_true")
    p_start.add_argument("--semi-agentic", action="store_true", dest="semi_agentic")
    p_start.add_argument("--agentic", action="store_true")
    p_start.add_argument("--wt", "--worktree", action="store_true", dest="wt")
    p_start.add_argument("--no-wt", action="store_true", dest="no_wt")
    p_start.add_argument("--pm", action="store_true")
    p_start.add_argument("--no-pm", action="store_true", dest="no_pm")
    p_start.set_defaults(func=cmd_resolve_start)

    # ── advance ──
    p_adv = sub.add_parser("advance", help="⬜→🔄 전환 (T-7)")
    p_adv.add_argument("task_path", metavar="<task-path>")
    p_adv.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_adv.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_adv.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_adv.add_argument("--note")
    p_adv.add_argument("--force", action="store_true",
                       help="게이트 산출물·명확화·code-scan 인용 가드 우회(--note 필수). "
                            "157 PM 경로 설계 게이트 가드는 우회하지 못한다")
    p_adv.add_argument("--next-action",
                       help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                            "미지정 시 프론티어에서 자동 파생")
    p_adv.set_defaults(func=cmd_advance)

    # ── mark ──
    p_mark = sub.add_parser("mark", help="⬜/🔄→✅ 전환 (T-7, §2.4, §2.15)")
    p_mark.add_argument("task_path", metavar="<task-path>")
    p_mark.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_mark.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_mark.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_mark.add_argument("--done", action="store_true", required=True)
    p_mark.add_argument("--note")
    p_mark.add_argument("--as-worker", action="store_true", dest="as_worker")
    p_mark.add_argument("--worker-stage",
                        choices=STAGE_ENUM,
                        dest="worker_stage")
    # 070 R-5: --action-step은 --step의 신규 별칭 — dest 공유로 _parse_step/row["step"] 로직 무변경
    p_mark.add_argument("--step", dest="step", metavar="N/M")
    p_mark.add_argument("--action-step", dest="step", metavar="N/M",
                        help="EXECUTE 액션 진행률 (구 --step 별칭, 070 R-5)")
    # 103 R-21: 소요 '값'과 소요 '미상 선언'은 동시에 성립할 수 없으므로 배타 그룹으로
    #   묶는다. 둘 다 주면 argparse가 exit 2로 거부한다 — `--owner`/`--auto-pass`와
    #   동일 계열의 CLI 인자 형식 오류이므로 ERROR_CODES를 신설하지 않는다(45종 불변).
    duration_group = p_mark.add_mutually_exclusive_group()
    duration_group.add_argument("--worker-duration-minutes", dest="worker_duration_minutes",
                        type=_worker_duration_minutes, metavar="<minutes>",
                        help="103 R-15: 이 행에서 워커가 실제 실행한 시간(분, 0 이상 정수). "
                             "원천은 하네스 duration_ms — 분으로 환산해 전달한다. "
                             "지정 시에만 rows[].worker_duration_minutes에 기록되며, "
                             "미지정 시 필드를 만들지 않는다(기존 태스크 무영향)")
    duration_group.add_argument("--worker-duration-unknown", action="store_true",
                        dest="worker_duration_unknown",
                        help="103 R-21: 이 행의 워커 소요를 알 수 없음을 명시한다"
                             "(중단된 워커·PM 직접 수행·소급 불가 과거 데이터). "
                             "worker_duration_missing 경고를 억제하며, 행에 필드를 "
                             "만들지 않는다 — 기록 결과는 인자 미지정과 완전히 동일하다")
    owner_group = p_mark.add_mutually_exclusive_group()  # C-2
    owner_group.add_argument("--owner", choices=["PM","worker","user","auto"])
    owner_group.add_argument("--auto-pass", action="store_true", dest="auto_pass")
    p_mark.add_argument("--force", action="store_true")
    p_mark.add_argument("--next-action",
                        help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                             "미지정 시 프론티어에서 자동 파생")
    p_mark.set_defaults(func=cmd_mark)

    # ── block ──
    p_blk = sub.add_parser("block", help="any→❌ 전환 + current_status=blocked (§2.17 트리거 #7)")
    p_blk.add_argument("task_path", metavar="<task-path>")
    p_blk.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_blk.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_blk.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_blk.add_argument("--reason", required=True)
    p_blk.set_defaults(func=cmd_block)

    # ── validate ──
    p_val = sub.add_parser("validate", help="정합성 검증 → violations[] (§2.6, F-10)")
    p_val.add_argument("task_path", metavar="<task-path>")
    p_val.set_defaults(func=cmd_validate)

    # ── add-row ──
    p_add = sub.add_parser("add-row", help="추가작업 행 삽입 (§2.12 G-9)")
    p_add.add_argument("task_path", metavar="<task-path>")
    p_add.add_argument("--after-task-step", dest="after_task_step", metavar="<key>",
                       help="070: 앵커 행 key 주소")
    p_add.add_argument("--after-task-step-id", dest="after_task_step_id", type=int, metavar="<n>",
                       help="070: 앵커 행 숫자 주소(신규, row_id와 동일 의미)")
    p_add.add_argument("--after", type=int, metavar="<n>",
                       help="[deprecated] --after-task-step / --after-task-step-id 사용 권장")
    p_add.add_argument("--stage", required=True, choices=STAGE_ENUM)
    p_add.add_argument("--item", required=True)
    p_add.add_argument("--key", metavar="<key>",
                       help="070 R-9: 신규 행 key 명시 지정 (미지정 시 자동 생성)")
    p_add.add_argument("--note")
    p_add.add_argument("--test-change-kind", choices=["fix", "requirement_change"])
    p_add.set_defaults(func=cmd_add_row)

    # ── status ──
    p_sts = sub.add_parser("status", help="current_status 명시 전환 (§2.11 G-7)")
    p_sts.add_argument("task_path", metavar="<task-path>")
    p_sts.add_argument("--set", dest="set", required=True,
                       choices=["in_progress","done","blocked",
                                "additional_work","additional_work_done",
                                STATUS_COMPLETED_UNMERGED])
    p_sts.add_argument("--note")
    p_sts.set_defaults(func=cmd_status)

    p_clock = sub.add_parser("test-clock", help="Record TEST execution or human wait interval")
    p_clock.add_argument("action", choices=["start", "stop"])
    p_clock.add_argument("task_path", metavar="<task-path>")
    p_clock.add_argument("--kind", required=True, choices=["auto", "human"])
    p_clock.add_argument("--id", required=True)
    p_clock.set_defaults(func=cmd_test_clock)

    p_metrics = sub.add_parser("test-metrics", help="Read only TEST timing and iteration counts")
    p_metrics.add_argument("task_path", metavar="<task-path>")
    p_metrics.set_defaults(func=cmd_test_metrics)

    # ── run-start (131 D8) ──
    p_run = sub.add_parser(
        "run-start",
        help="새 run_id 발급 + state.json 기록 (131 D8) — 재호출 시 교체, 이력 누적 없음")
    p_run.add_argument("task_path", metavar="<task-path>")
    p_run.set_defaults(func=cmd_run_start)

    # ── finalize-attribution (118 D-4b / AC-4) ──
    p_fin = sub.add_parser(
        "finalize-attribution",
        help="merge 확인 후 허브 .opal/MEMORY.json history 귀속 (118 AC-4)")
    p_fin.add_argument("task_path", metavar="<task-path>")
    # required=True로 두지 않는다 — 미지정도 이 도구의 err() 관례(exit 1 + 단일 라인
    # JSON)로 거부해야 하기 때문이다(argparse의 exit 2/usage 출력 회피).
    p_fin.add_argument("--allocator-root", dest="allocator_root", metavar="<abs>",
                       help="worktree registry가 발급한 허브 절대 경로 (추론하지 않음)")
    p_fin.set_defaults(func=cmd_finalize_attribution)

    # ── boot-summary ──
    p_boot = sub.add_parser(
        "boot-summary",
        help="프로젝트 하위 미완료 태스크 1건의 읽기 전용 부트 요약",
    )
    p_boot.add_argument("project_root", metavar="<project-root>")
    p_boot.set_defaults(func=cmd_boot_summary)

    # Friendly alias used by bootstrap integrations; both routes share the
    # exact same implementation and output contract.
    p_boot_alias = sub.add_parser("boot-brief", help=argparse.SUPPRESS)
    p_boot_alias.add_argument("project_root", metavar="<project-root>")
    p_boot_alias.set_defaults(func=cmd_boot_summary)

    # ── gate-pass ──
    p_gp = sub.add_parser("gate-pass",
                          help="[DEPRECATED] Gate 4행 일괄 ✅ 처리 — 레거시 state.json 전용 (§2.13 G-10, 014 Phase 4)")
    p_gp.add_argument("task_path", metavar="<task-path>")
    p_gp.add_argument("--start", type=int, required=True)
    p_gp.add_argument("--note")
    p_gp.set_defaults(func=cmd_gate_pass)

    # ── spec-validate (070 R-6) ──
    p_spec = sub.add_parser("spec-validate", help="pipeline.json 스펙 검증 (070 R-6, DEC-2)")
    p_spec.add_argument("spec_path", metavar="<pipeline.json>")
    p_spec.set_defaults(func=cmd_spec_validate)

    # ── event-verify ──
    p_evt = sub.add_parser(
        "event-verify",
        help="단계 진입 전 event-loader receipt 최신성 검증 (상태 파일 비접촉)",
    )
    p_evt.add_argument("--event", required=True,
                       help="검증할 정확한 이벤트 id (예: pilot.start, stage.execute)")
    p_evt.add_argument("--receipt", required=True,
                       help="event-loader load 응답 또는 receipt object JSON 파일")
    p_evt.add_argument("--manifest", help="events.json 경로")
    p_evt.add_argument("--source-root", dest="source_root",
                       help="framework source checkout root")
    p_evt.add_argument("--deployed-root", dest="deployed_root",
                       help="installed OPAL root")
    p_evt.add_argument("--project-root", dest="project_root",
                       help="current project root")
    p_evt.set_defaults(func=cmd_event_verify)

    # ── verify ──
    p_vfy = sub.add_parser(
        "verify",
        help="TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사 (PLAN 013, 헌법 §4)"
    )
    p_vfy.add_argument("task_path", metavar="<task-path>")
    p_vfy.add_argument("--scenario", metavar="<path>",
                       help="TEST-SCENARIO.md 경로 명시 (기본: <task-path>/TEST-SCENARIO.md)")
    # 016 RED-first 게이트
    p_vfy.add_argument("--red-check", action="store_true", dest="red_check",
                       help="RED 증거(실패 출력) 게이트 — 누락 시 red_evidence_missing")
    p_vfy.add_argument("--changed-files", nargs="*", default=[], dest="changed_files",
                       help="fix 루핑 변경 파일 목록 (테스트 불변성 입력)")
    p_vfy.add_argument("--test-globs", nargs="*", default=None, dest="test_globs",
                       help="테스트 파일 식별 glob 패턴 (프로젝트 탐지값 주입 — 하드코딩 금지)")
    p_vfy.add_argument("--fix-mode", action="store_true", dest="fix_mode",
                       help="fix 루핑 컨텍스트 — 테스트 파일 수정 시 test_modified_in_fix")
    # 005 명확화 게이트
    p_vfy.add_argument("--clarification-check", action="store_true", dest="clarification_check",
                       help="TASK 4요소 잠금 게이트 — 미충족 시 clarification_gate_unmet (PRINCIPLES §1 집행)")
    p_vfy.add_argument("--task-md", metavar="<path>", dest="task_md",
                       help="TASK.md 경로 명시 (기본: <task-path>/TASK.md)")
    # 098 근거 등급 확정/미확정 판정 게이트
    p_vfy.add_argument("--evidence-check", action="store_true", dest="evidence_check",
                       help="근거 등급 확정/미확정 판정 라우터 — 항목별 판정+사유를 "
                            "반환하되 차단하지 않음(exit 0 유지, PLAN §3.3.2)")
    # 106 code-scan 결과 인용 게이트
    p_vfy.add_argument("--code-scan-citation-check", action="store_true",
                       dest="code_scan_citation_check",
                       help="PLAN.md code-scan 결과 인용 게이트 — 미충족 시 "
                            "code_scan_citation_unmet(exit 1). 자산·산출물·적용 범위 "
                            "3조건 미해당 시 skipped(exit 0, PLAN §3.4.2)")
    p_vfy.add_argument("--plan-contract-check", action="store_true",
                       dest="plan_contract_check",
                       help="sdlc-v2 PLAN.md Work items 계약 검사 — 필수 열/W-ID/선행/그룹/"
                            "AC-C 연결/동일 그룹 파일 충돌 미충족 시 plan_contract_unmet(exit 1). "
                            "legacy PLAN은 skipped(exit 0)")
    # 135 W-4 (AC-5~AC-8) — run-log 완전성 진단 (읽기 전용, 비차단)
    p_vfy.add_argument("--run-log-completeness-check", action="store_true",
                       dest="run_log_completeness_check",
                       help="state.json run_log 계약과 JSONL 사건을 대조해 누락·관측"
                            "지점을 진단한다(비차단, exit 0 유지). run_log 블록이 없으면"
                            "skipped 취급")
    # 170 AC-1 — design-gate 결정론 사전검사 (evaluator 호출 전, 회차·상태 비소비)
    p_vfy.add_argument("--design-gate-check", action="store_true",
                       dest="design_gate_check",
                       help="design-gate ①~⑦ 결정론 검사 + decision_clarity 유보 어휘 "
                            "후보 린트를 회차·상태 소비 없이 실행한다(비차단, exit 0 유지). "
                            "state.json 부재·PM 경로 아님은 skipped 취급")
    p_vfy.set_defaults(func=cmd_verify)

    # ── log-event (135 W-3, CONTRACT §2.4 state-tool.log-event) ──
    p_log = sub.add_parser(
        "log-event",
        help="PM direct activity 기록 (CONTRACT §2.4 state-tool.log-event)")
    p_log.add_argument("task_path", metavar="<task-path>")
    p_log.add_argument("--event", required=True, choices=["activity", "pm.report"],
                       help="activity 또는 pm.report(TASK-147 D-2, §2.4). "
                            "stop.decision은 이 표면이 수용하지 않는다(D-6 — Stop hook "
                            "receipt drain 경로가 조립한다)")
    p_log.add_argument("--kind", choices=sorted(_PM_ACTIVITY_KIND_ENUM),
                       help="--event activity에서 --data 미지정 시 필수. "
                            "data.kind 값(§1.3 4종 enum)")
    # ── TASK-147 W-5 — `--event pm.report`의 data 폐쇄 3축 ──
    # [MUST] choices를 걸지 않는다. argparse가 거르면 앞단 거부가 usage 오류(exit 2)가
    # 되어 기록 코어의 `schema_invalid`와 판정이 갈린다(§1.3 중복 방어 일치 계약).
    # 값 검증은 `_build_pm_report_data()`가 한다.
    p_log.add_argument("--report-type", dest="report_type",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.report_type(§1.3 2종 enum: "
                            f"{', '.join(_PM_REPORT_TYPE_ENUM)})")
    p_log.add_argument("--transition-action", dest="transition_action",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.transition_action(§1.3 4종 enum: "
                            f"{', '.join(_PM_TRANSITION_ACTION_ENUM)})")
    p_log.add_argument("--user-input-required", dest="user_input_required",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.user_input_required(true|false)")
    p_log.add_argument("--summary", required=True)
    p_log.add_argument("--reason")
    p_log.add_argument("--stage")
    p_log.add_argument("--task-step", dest="task_step")
    p_log.add_argument("--work-item", dest="work_item")
    p_log.add_argument("--refs", nargs="*", default=None)
    p_log.add_argument("--data",
                       help="사건 data 객체 원문 JSON(§1.3 폐쇄 목록 검증 대상). "
                            "미지정 시 activity는 --kind로, pm.report는 "
                            "--report-type/--transition-action/--user-input-required로 구성")
    p_log.add_argument("--format", dest="format", choices=["json"])
    p_log.set_defaults(func=cmd_log_event)

    # ── gate-request (135 W-3, CONTRACT §2.4 state-tool.gate-request) ──
    p_greq = sub.add_parser(
        "gate-request",
        help="gate.requested 기록 (CONTRACT §2.4 state-tool.gate-request)")
    p_greq.add_argument("task_path", metavar="<task-path>")
    p_greq.add_argument("--gate-id", dest="gate_id", required=True)
    p_greq.add_argument("--summary", required=True)
    p_greq.add_argument("--stage")
    p_greq.add_argument("--task-step", dest="task_step")
    p_greq.add_argument("--format", dest="format", choices=["json"])
    p_greq.set_defaults(func=cmd_gate_request)

    # ── gate-resolve (135 W-3, CONTRACT §2.4 state-tool.gate-resolve) ──
    p_gres = sub.add_parser(
        "gate-resolve",
        help="gate.resolved 기록 (CONTRACT §2.4 state-tool.gate-resolve)")
    p_gres.add_argument("task_path", metavar="<task-path>")
    p_gres.add_argument("--gate-id", dest="gate_id", required=True)
    p_gres.add_argument("--verdict", required=True, choices=["approved", "rejected", "auto"])
    p_gres.add_argument("--owner", required=True, choices=["PM", "user", "auto"])
    p_gres.add_argument("--note")
    p_gres.add_argument("--format", dest="format", choices=["json"])
    p_gres.set_defaults(func=cmd_gate_resolve)

    # ── design-gate (157 DEC-7/DEC-9/DEC-10) ──
    p_dg = sub.add_parser("design-gate", help="PM 경로 독립 설계 게이트 (start|record|reset)")
    dg_sub = p_dg.add_subparsers(dest="design_gate_command", metavar="<start|record|reset>")
    dg_sub.required = True
    p_dgs = dg_sub.add_parser("start", help="결정론 검사 후 설계 게이트 시도 시작 (gate.requested)")
    p_dgs.add_argument("task_path", metavar="<task-path>")
    p_dgs.add_argument("--iteration", type=int, required=True, metavar="N")
    p_dgs.set_defaults(func=cmd_design_gate_start)
    p_dgr = dg_sub.add_parser("record", help="evaluator design-rubric 판정 기록 (gate.resolved)")
    p_dgr.add_argument("task_path", metavar="<task-path>")
    p_dgr.add_argument("--iteration", type=int, required=True, metavar="N")
    p_dgr.add_argument("--verdict", required=True, choices=["pass", "rewrite", "input_error"])
    p_dgr.add_argument("--evaluator-result", dest="evaluator_result", required=True, metavar="<json>")
    p_dgr.add_argument("--rewrite-target", dest="rewrite_target", choices=["plan", "scenario", "both"])
    p_dgr.add_argument("--advisory-responses", dest="advisory_responses", metavar="<json>",
                       help="advisory 응답 파일 [{id, response: apply|retain, reason}] (167)")
    p_dgr.set_defaults(func=cmd_design_gate_record)
    p_dgx = dg_sub.add_parser("reset", help="반복 상한(retry_limit) 해제 — 사용자 결정 전용")
    p_dgx.add_argument("task_path", metavar="<task-path>")
    p_dgx.add_argument("--owner", choices=["PM", "worker", "user", "auto"])
    p_dgx.add_argument("--note")
    p_dgx.set_defaults(func=cmd_design_gate_reset)

    # ── design-decision (157 DEC-12) ──
    p_dd = sub.add_parser("design-decision", help="PM 경로 PLAN 단계 설계 결정 분류 기록")
    p_dd.add_argument("task_path", metavar="<task-path>")
    p_dd.add_argument("--scope", required=True, choices=["external", "detail"])
    p_dd.add_argument("--summary", required=True)
    p_dd.add_argument("--basis", required=True)
    p_dd.set_defaults(func=cmd_design_decision)

    return parser

# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()
    state_writers = {
        "advance", "mark", "block", "add-row",
        "status", "test-clock", "run-start", "gate-pass", "log-event",
        "gate-request", "gate-resolve", "design-gate", "design-decision",
    }
    resolve_mode_write = (
        args.command == "resolve-mode" and args.mode is not None
        and (pathlib.Path(args.task_path) / "state.json").exists()
    )
    if args.command in state_writers or resolve_mode_write:
        task_path = resolve_task_path(args.task_path, args.command)
        with state_writer_lock(task_path):
            args.func(args)
    else:
        args.func(args)

/**
 * @header {
 *   "module": "tasks-page-stats-test",
 *   "layer": "test",
 *   "domain": "tasks",
 *   "description": "[T103] 태스크 상세 Sheet 2탭 + A-1~A-4 렌더 AC 컴포넌트 테스트. apiClient를 vi.mock으로 대체해 101 고정 응답(FX-DETAIL-101, BE 실응답 스냅샷)과 결측 응답(FX-DETAIL-NOSTATS)을 주입하고, QueryClientProvider + createMemoryRouter로 TasksPage를 렌더한다. 스냅샷 테스트·픽셀 비교·전체 트리 검증은 작성하지 않는다(PLAN P-6 범위 한정). [R-18] 소요 3계열 렌더 — 진행 중 태스크의 4구획 항등(총 483 = PM 23 + 워커 146 + 캡틴 130 + 진행중 184, 집계기준 16-c)과 워커 미기록 태스크의 축퇴(PM == 기존 작업 105 · 워커 0폭 · 작업 구획 폭 전후 동일, 16-a)를 단정한다. [R-20] TS-130~TS-133은 A-1·A-2 구획 호버 툴팁 — 구획 문면(단계·계열·BE 라벨·비율·단계 총), 워커 미측정 태스크의 막대 전체 받침 툴팁, 0폭 워커 구획의 키보드 도달, 진행 중 태스크의 「진행중」 4번째 구획을 단정한다. 기대 문면의 시간 문자열은 전부 BE 라벨이며 테스트도 분→시간 변환을 하지 않는다. [R-21] TS-140·TS-141은 A-1 야간 보정 배지 — applied=true면 BE 구간 라벨 배지와 툴팁 문면이 서고, applied=false·필드 부재 2경로 모두 배지가 뜨지 않음을 단정한다.",
 *   "exports": [],
 *   "depends": ["tasks-page", "api-client", "ui-store"],
 *   "task": "103",
 *   "scenarios": ["TS-030", "TS-031", "TS-032", "TS-033", "TS-034", "TS-035", "TS-036", "TS-037", "TS-038", "TS-039", "TS-106", "TS-107", "TS-108", "TS-109", "TS-130", "TS-131", "TS-132", "TS-133", "TS-140", "TS-141"],
 *   "changelog": [
 *     "2026-08-26 T103 R-21: 야간 보정 배지 케이스 2건(TS-140·TS-141) + 픽스처 FX-DETAIL-101-QUIET·FX-DETAIL-101-NOQUIET 신설. 기존 케이스·픽스처 무변경",
 *     "2026-08-26 T103 R-20: 구획 호버 툴팁 케이스 4건(TS-130~TS-133) + 픽스처 FX-DETAIL-103-LABELS·FX-DETAIL-101-LABELS(단계 3계열 라벨 동반 응답) 신설. 트리거는 마우스가 아니라 키보드 포커스로 열어 a11y 계약을 함께 단정하고, 열린 툴팁이 항상 1개임을 확인해 구획·막대 툴팁 중첩을 막는다. 기존 케이스·픽스처 무변경",
 *     "2026-08-25 T103 R-18: 3계열 렌더 케이스 4건(TS-106~TS-109) + 픽스처 FX-DETAIL-103(워커 기록 진행 중)·FX-DETAIL-101-SERIES(워커 미기록 축퇴) 신설. 기존 케이스·픽스처 무변경"
 *   ]
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TasksPage } from "./TasksPage";
import { useUiStore } from "@/store/ui-store";
import { apiClient } from "@/lib/api";
// 정적 검사용 원문 — vite `?raw` 로 읽는다(node:fs 미사용, 신규 의존 0건)
import tasksPageSource from "./TasksPage.tsx?raw";
import statsTestSource from "./TasksPage.stats.test.tsx?raw";

const PROJECT = "/Volumes/Data/AIStudio/workspace/ai-framework";
const TASK_ID = "101-260824-opd-핸드오프-스키마-계약정합";

/* ------------------------------------------------------------------ */
/* 픽스처 — FX-DETAIL-101 (BE 실응답 스냅샷, note만 길이 축약)                */
/* ------------------------------------------------------------------ */

const FX_DETAIL_101 = {
  owner_term: "캡틴",
    "task_id": "101-260824-opd-핸드오프-스키마-계약정합",
    "title": "101-260824-opd-핸드오프-스키마-계약정합",
    "skill": "opd",
    "mode": "semi-agentic",
    "current_status": "done",
    "current_stage": "CLOSE",
    "progress": 100,
    "pipeline": [
      {
        "stage": "TASK",
        "done_count": 2,
        "total": 2,
        "status": "done",
        "rows": [
          {
            "row": 1,
            "stage": "TASK",
            "status": "done",
            "updated_at": "2026-08-24 16:32",
            "row_id": 1,
            "key": "task.task_md",
            "item": "작업",
            "timestamp": "2026-08-24 16:32",
            "time_label": "16:32",
            "owner": "PM",
            "owner_label": "PM",
            "note": null,
            "gate": null,
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 2,
            "stage": "TASK",
            "status": "done",
            "updated_at": "2026-08-24 16:56",
            "row_id": 2,
            "key": "task.user_confirm",
            "item": "사용자 확인",
            "timestamp": "2026-08-24 16:56",
            "time_label": "16:56",
            "owner": "user",
            "owner_label": "캡틴",
            "note": "캡틴 확인: ANALYSIS 진입 승인 + ",
            "gate": null,
            "duration_minutes": 24,
            "duration_label": "24분",
            "series": "wait",
            "is_max_gap": false
          }
        ],
        "work_minutes": 0,
        "wait_minutes": 24,
        "total_minutes": 24,
        "total_label": "24분",
        "is_peak": false
      },
      {
        "stage": "ANALYSIS",
        "done_count": 3,
        "total": 3,
        "status": "done",
        "rows": [
          {
            "row": 3,
            "stage": "ANALYSIS",
            "status": "done",
            "updated_at": "2026-08-24 17:13",
            "row_id": 3,
            "key": "analysis.analysis_md",
            "item": "작업",
            "timestamp": "2026-08-24 17:13",
            "time_label": "17:13",
            "owner": "PM",
            "owner_label": "PM",
            "note": null,
            "gate": null,
            "duration_minutes": 17,
            "duration_label": "17분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 4,
            "stage": "ANALYSIS",
            "status": "done",
            "updated_at": "2026-08-24 17:13",
            "row_id": 4,
            "key": "analysis.pm_gate",
            "item": "PM Gate",
            "timestamp": "2026-08-24 17:13",
            "time_label": "17:13",
            "owner": "PM",
            "owner_label": "PM",
            "note": "PM Gate 통과: 체크리스트 4항목 전건",
            "gate": {
              "artifacts": [
                "ANALYSIS.md"
              ],
              "checklist": [
                "ANALYSIS.md §0 참조 문서 — code-scan·brain 선조회 결과 1건 이상",
                "ANALYSIS.md §확정 입력 판정 — TASK.md [결정]·[사실] 전건 판정(누락 0)",
                "ANALYSIS.md §다음 단계 입력 — 항목|확정값|근거 3열 표 존재",
                "소스코드 원문 블록 0건 (코드펜스는 실행 명령·시그니처 한정)"
              ]
            },
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 5,
            "stage": "ANALYSIS",
            "status": "done",
            "updated_at": "2026-08-24 17:18",
            "row_id": 5,
            "key": "analysis.user_confirm",
            "item": "사용자 확인",
            "timestamp": "2026-08-24 17:18",
            "time_label": "17:18",
            "owner": "user",
            "owner_label": "캡틴",
            "note": "캡틴 확인: PLAN 진입 승인 + anal",
            "gate": null,
            "duration_minutes": 5,
            "duration_label": "5분",
            "series": "wait",
            "is_max_gap": false
          }
        ],
        "work_minutes": 17,
        "wait_minutes": 5,
        "total_minutes": 22,
        "total_label": "22분",
        "is_peak": false
      },
      {
        "stage": "PLAN",
        "done_count": 3,
        "total": 3,
        "status": "done",
        "rows": [
          {
            "row": 6,
            "stage": "PLAN",
            "status": "done",
            "updated_at": "2026-08-24 17:29",
            "row_id": 6,
            "key": "plan.plan_md",
            "item": "작업",
            "timestamp": "2026-08-24 17:29",
            "time_label": "17:29",
            "owner": "PM",
            "owner_label": "PM",
            "note": "범위 확장 결정: analysis-core.",
            "gate": null,
            "duration_minutes": 11,
            "duration_label": "11분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 7,
            "stage": "PLAN",
            "status": "done",
            "updated_at": "2026-08-24 17:29",
            "row_id": 7,
            "key": "plan.pm_gate",
            "item": "PM Gate",
            "timestamp": "2026-08-24 17:29",
            "time_label": "17:29",
            "owner": "PM",
            "owner_label": "PM",
            "note": "PM Gate 통과: R-1~R-5 전건 커",
            "gate": {
              "artifacts": [
                "TASK.md",
                "PLAN.md"
              ],
              "checklist": [
                "TASK.md 요구사항",
                "PLAN.md §4.2",
                "PLAN.md §5",
                "PLAN.md §리스크 가설 표"
              ]
            },
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 8,
            "stage": "PLAN",
            "status": "done",
            "updated_at": "2026-08-24 17:31",
            "row_id": 8,
            "key": "plan.user_confirm",
            "item": "사용자 확인",
            "timestamp": "2026-08-24 17:31",
            "time_label": "17:31",
            "owner": "user",
            "owner_label": "캡틴",
            "note": "캡틴 확인: TEST-SCENARIO 진입 ",
            "gate": null,
            "duration_minutes": 2,
            "duration_label": "2분",
            "series": "wait",
            "is_max_gap": false
          }
        ],
        "work_minutes": 11,
        "wait_minutes": 2,
        "total_minutes": 13,
        "total_label": "13분",
        "is_peak": false
      },
      {
        "stage": "TEST-SCENARIO",
        "done_count": 3,
        "total": 3,
        "status": "done",
        "rows": [
          {
            "row": 9,
            "stage": "TEST-SCENARIO",
            "status": "done",
            "updated_at": "2026-08-24 17:35",
            "row_id": 9,
            "key": "test_scenario.test_scenario_md",
            "item": "작업",
            "timestamp": "2026-08-24 17:35",
            "time_label": "17:35",
            "owner": "PM",
            "owner_label": "PM",
            "note": "Block A 선작성 → Block B 보강",
            "gate": null,
            "duration_minutes": 4,
            "duration_label": "4분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 10,
            "stage": "TEST-SCENARIO",
            "status": "done",
            "updated_at": "2026-08-24 17:41",
            "row_id": 10,
            "key": "test_scenario.scenario_gate",
            "item": "목표-커버 게이트",
            "timestamp": "2026-08-24 17:41",
            "time_label": "17:41",
            "owner": "PM",
            "owner_label": "PM",
            "note": "게이트 통과 — tool-gated 두 증거",
            "gate": {
              "artifacts": [
                "TEST-SCENARIO.md"
              ],
              "checklist": [
                "mock 부재(grep)",
                "사전 조건 데이터 채워짐",
                "Given/When/Then 3필드",
                "가설↔시나리오 매핑 완전",
                "L1/L2/L3 계층 명시",
                "L3 [SUPERVISOR] 마커 + PM 요청 양식",
                "실행 방식(M1/M2/M3) 명시"
              ]
            },
            "duration_minutes": 6,
            "duration_label": "6분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 11,
            "stage": "TEST-SCENARIO",
            "status": "done",
            "updated_at": "2026-08-24 22:26",
            "row_id": 11,
            "key": "test_scenario.user_confirm",
            "item": "사용자 확인",
            "timestamp": "2026-08-24 22:26",
            "time_label": "22:26",
            "owner": "user",
            "owner_label": "캡틴",
            "note": "캡틴 확인: 평가자 비차단 권고 4건 반영 ",
            "gate": null,
            "duration_minutes": 285,
            "duration_label": "4시간 45분",
            "series": "wait",
            "is_max_gap": true
          }
        ],
        "work_minutes": 10,
        "wait_minutes": 285,
        "total_minutes": 295,
        "total_label": "4시간 55분",
        "is_peak": true
      },
      {
        "stage": "EXECUTE",
        "done_count": 1,
        "total": 1,
        "status": "done",
        "rows": [
          {
            "row": 12,
            "stage": "EXECUTE",
            "status": "done",
            "updated_at": "2026-08-24 22:44",
            "row_id": 12,
            "key": "execute.implement",
            "item": "작업",
            "timestamp": "2026-08-24 22:44",
            "time_label": "22:44",
            "owner": "PM",
            "owner_label": "PM",
            "note": "Phase 3(Step 7·8) 완료. 검증",
            "gate": null,
            "duration_minutes": 18,
            "duration_label": "18분",
            "series": "work",
            "is_max_gap": false
          }
        ],
        "work_minutes": 18,
        "wait_minutes": 0,
        "total_minutes": 18,
        "total_label": "18분",
        "is_peak": false
      },
      {
        "stage": "TEST",
        "done_count": 6,
        "total": 6,
        "status": "done",
        "rows": [
          {
            "row": 13,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:27",
            "row_id": 13,
            "key": "test.run_tests",
            "item": "작업",
            "timestamp": "2026-08-24 23:27",
            "time_label": "23:27",
            "owner": "PM",
            "owner_label": "PM",
            "note": "L1 17건+L2 2건 실행: 16 PASS",
            "gate": null,
            "duration_minutes": 43,
            "duration_label": "43분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 14,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:27",
            "row_id": 14,
            "key": "test.add_3",
            "item": "ADD-3: S-15·S-14 판정 기준 정정(MEMORY.json·타 태스크 폴더 제외, 5문서→6문서)",
            "timestamp": "2026-08-24 23:27",
            "time_label": "23:27",
            "owner": "PM",
            "owner_label": "PM",
            "note": "PM 직접 수행 — 판정 기준 3건 정정. ",
            "gate": null,
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 15,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:31",
            "row_id": 15,
            "key": "test.add_2",
            "item": "ADD-2: 컨벤션 Medium — 템플릿 코드펜스 내 폐지 안내 문장 제거",
            "timestamp": "2026-08-24 23:31",
            "time_label": "23:31",
            "owner": "PM",
            "owner_label": "PM",
            "note": "컨벤션 Medium 해소 — 템플릿 코드펜스",
            "gate": null,
            "duration_minutes": 4,
            "duration_label": "4분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 16,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:31",
            "row_id": 16,
            "key": "test.add_1",
            "item": "ADD-1: S-17(b) 해소 — 레거시 소급 미적용 명시 추가",
            "timestamp": "2026-08-24 23:31",
            "time_label": "23:31",
            "owner": "PM",
            "owner_label": "PM",
            "note": "S-17(b) 해소 — op-dev-anal",
            "gate": null,
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 17,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:31",
            "row_id": 17,
            "key": "test.pm_gate",
            "item": "PM Gate",
            "timestamp": "2026-08-24 23:31",
            "time_label": "23:31",
            "owner": "PM",
            "owner_label": "PM",
            "note": "PM Gate 통과: 시나리오 19건 중 1",
            "gate": {
              "artifacts": [
                "TEST-SCENARIO.md"
              ],
              "checklist": [
                "시나리오 결과/코드품질/보안/회귀",
                "컨벤션 자동 진단 PASS (GC-CONVENTION-*.md Critical/High 0건 — 컨벤션 적용 대상 ≥1건 시 발동)"
              ]
            },
            "duration_minutes": 0,
            "duration_label": "0분",
            "series": "work",
            "is_max_gap": false
          },
          {
            "row": 18,
            "stage": "TEST",
            "status": "done",
            "updated_at": "2026-08-24 23:35",
            "row_id": 18,
            "key": "test.user_confirm",
            "item": "사용자 확인",
            "timestamp": "2026-08-24 23:35",
            "time_label": "23:35",
            "owner": "user",
            "owner_label": "캡틴",
            "note": "캡틴 확인: CLOSE 진입 승인",
            "gate": null,
            "duration_minutes": 4,
            "duration_label": "4분",
            "series": "wait",
            "is_max_gap": false
          }
        ],
        "work_minutes": 47,
        "wait_minutes": 4,
        "total_minutes": 51,
        "total_label": "51분",
        "is_peak": false
      },
      {
        "stage": "CLOSE",
        "done_count": 1,
        "total": 1,
        "status": "done",
        "rows": [
          {
            "row": 19,
            "stage": "CLOSE",
            "status": "done",
            "updated_at": "2026-08-24 23:37",
            "row_id": 19,
            "key": "close.done_md",
            "item": "DONE.md 생성",
            "timestamp": "2026-08-24 23:37",
            "time_label": "23:37",
            "owner": "PM",
            "owner_label": "PM",
            "note": null,
            "gate": null,
            "duration_minutes": 2,
            "duration_label": "2분",
            "series": "work",
            "is_max_gap": false
          }
        ],
        "work_minutes": 2,
        "wait_minutes": 0,
        "total_minutes": 2,
        "total_label": "2분",
        "is_peak": false
      }
    ],
    "artifacts": [
      "TASK.md",
      "ANALYSIS.md",
      "PLAN.md",
      "TEST-SCENARIO.md",
      "DONE.md",
      "SCENARIO-GATE-1.md",
      "GC-CONVENTION-260824.md",
      "STATE.md",
      "AGENTIC-LOG.md"
    ],
    "updated_at": "2026-08-24 23:37",
    "stats": {
      "available": true,
      "total_minutes": 425,
      "total_label": "7시간 5분",
      "work_minutes": 105,
      "work_label": "1시간 45분",
      "wait_minutes": 320,
      "wait_label": "5시간 20분",
      "wait_ratio": 75,
      "peak_stage": "TEST-SCENARIO",
      "peak_stage_label": "4시간 55분",
      "gate_count": 4,
      "gate_recorded": true,
      "blocker_count": 0,
      "is_running": false,
      "current_row_id": null,
      "current_stage": null,
      "current_item": null,
      "current_key": null,
      "current_series": "",
      "current_elapsed_minutes": null,
      "current_elapsed_label": "—"
    },
    "artifact_items": [
      {
        "name": "TASK.md",
        "type": "pipeline",
        "type_label": "파이프라인"
      },
      {
        "name": "ANALYSIS.md",
        "type": "pipeline",
        "type_label": "파이프라인"
      },
      {
        "name": "PLAN.md",
        "type": "pipeline",
        "type_label": "파이프라인"
      },
      {
        "name": "TEST-SCENARIO.md",
        "type": "pipeline",
        "type_label": "파이프라인"
      },
      {
        "name": "DONE.md",
        "type": "pipeline",
        "type_label": "파이프라인"
      },
      {
        "name": "SCENARIO-GATE-1.md",
        "type": "verification",
        "type_label": "검증"
      },
      {
        "name": "GC-CONVENTION-260824.md",
        "type": "verification",
        "type_label": "검증"
      },
      {
        "name": "STATE.md",
        "type": "log",
        "type_label": "로그"
      },
      {
        "name": "AGENTIC-LOG.md",
        "type": "log",
        "type_label": "로그"
      }
    ]
  };

/** FX-DETAIL-NOSTATS — `state.json` 부재 태스크(FX-089)의 실응답 형태 */
const FX_DETAIL_NOSTATS = {
  ...FX_DETAIL_101,
  pipeline: [],
  artifacts: [],
  artifact_items: [],
  stats: { ...FX_DETAIL_101.stats, available: false, gate_recorded: false, gate_count: 0 },
};

/** FX-DETAIL-NOGATE — `092` 이전 태스크: 집계는 되지만 gate 기록이 없다 */
const FX_DETAIL_NOGATE = {
  ...FX_DETAIL_101,
  stats: { ...FX_DETAIL_101.stats, gate_recorded: false, gate_count: 0 },
};

/**
 * FX-DETAIL-103 — 워커 소요가 기록된 진행 중 태스크(103)의 3계열 응답.
 * 수치 원천은 `tasks/103.../state.json`을 `stats.py`로 집계한 실값이다:
 * 정적 299 = PM 23 + 워커 146 + 캡틴 130, 실시간 총 483 = 299 + 현재 행 경과 184 (16-c).
 * A-1·A-2 판정 전용이라 `rows`는 비운다 — 행 파생 판정은 FX-DETAIL-101이 담당한다.
 */
const FX_DETAIL_103 = {
  ...FX_DETAIL_101,
  task_id: "103-260825-opd-태스크-진행통계",
  current_status: "in_progress",
  current_stage: "EXECUTE",
  pipeline: [
    { stage: "TASK", done_count: 2, total: 2, status: "done", rows: [],
      work_minutes: 0, wait_minutes: 115, total_minutes: 115, total_label: "1시간 55분", is_peak: true,
      pm_minutes: 0, worker_minutes: 0, captain_minutes: 115, worker_measured: false },
    { stage: "ANALYSIS", done_count: 3, total: 3, status: "done", rows: [],
      work_minutes: 19, wait_minutes: 7, total_minutes: 26, total_label: "26분", is_peak: false,
      pm_minutes: 3, worker_minutes: 16, captain_minutes: 7, worker_measured: true },
    { stage: "PLAN", done_count: 3, total: 3, status: "done", rows: [],
      work_minutes: 26, wait_minutes: 2, total_minutes: 28, total_label: "28분", is_peak: false,
      pm_minutes: 5, worker_minutes: 21, captain_minutes: 2, worker_measured: true },
    { stage: "TEST-SCENARIO", done_count: 3, total: 3, status: "done", rows: [],
      work_minutes: 26, wait_minutes: 6, total_minutes: 32, total_label: "32분", is_peak: false,
      pm_minutes: 6, worker_minutes: 20, captain_minutes: 6, worker_measured: true },
    { stage: "EXECUTE", done_count: 2, total: 3, status: "in_progress", rows: [],
      work_minutes: 87, wait_minutes: 0, total_minutes: 87, total_label: "1시간 27분", is_peak: false,
      pm_minutes: 7, worker_minutes: 80, captain_minutes: 0, worker_measured: true },
    { stage: "TEST", done_count: 1, total: 2, status: "pending", rows: [],
      work_minutes: 11, wait_minutes: 0, total_minutes: 11, total_label: "11분", is_peak: false,
      pm_minutes: 2, worker_minutes: 9, captain_minutes: 0, worker_measured: true },
    { stage: "CLOSE", done_count: 0, total: 2, status: "pending", rows: [],
      work_minutes: 0, wait_minutes: 0, total_minutes: 0, total_label: "0분", is_peak: false,
      pm_minutes: 0, worker_minutes: 0, captain_minutes: 0, worker_measured: false },
  ],
  stats: {
    ...FX_DETAIL_101.stats,
    total_minutes: 483,          // 실시간 값 — 정적 299보다 184 크다 (16-c)
    total_label: "8시간 3분",
    work_minutes: 169, work_label: "2시간 49분",
    wait_minutes: 130, wait_label: "2시간 10분",
    wait_ratio: 43,              // 정적 총 기준 130/299
    pm_minutes: 23, pm_label: "23분",
    worker_minutes: 146, worker_label: "2시간 26분",
    captain_minutes: 130, captain_label: "2시간 10분",
    worker_measured: true,
    worker_clamped_count: 0,
    peak_stage: "TASK", peak_stage_label: "1시간 55분",
    is_running: true,
    current_row_id: 12,
    current_stage: "EXECUTE",
    current_item: "구현",
    current_key: "execute.implement",
    current_series: "work",
    current_elapsed_minutes: 184,
    current_elapsed_label: "3시간 4분",
  },
};

/**
 * FX-DETAIL-101-SERIES — 같은 101 태스크의 3계열 응답.
 * 워커 미기록이라 축퇴 규칙 16-a로 작업 전액이 PM에, 대기 전액이 캡틴에 귀속된다
 * (`stats.py` 실측: pm 105 == work 105 · captain 320 == wait 320 · worker_measured false).
 */
const FX_DETAIL_101_SERIES = {
  ...FX_DETAIL_101,
  pipeline: FX_DETAIL_101.pipeline.map((g) => ({
    ...g,
    pm_minutes: g.work_minutes,
    worker_minutes: 0,
    captain_minutes: g.wait_minutes,
    worker_measured: false,
  })),
  stats: {
    ...FX_DETAIL_101.stats,
    pm_minutes: 105, pm_label: "1시간 45분",
    worker_minutes: 0, worker_label: "0분",
    captain_minutes: 320, captain_label: "5시간 20분",
    worker_measured: false,
    worker_clamped_count: 0,
  },
};

const FX_CARDS = [
  {
    task_id: TASK_ID,
    title: "핸드오프 스키마 계약정합",
    skill: "opd",
    mode: "semi-agentic",
    column: "done",
    current_stage: "CLOSE",
    progress: 100,
    updated_at: "08-24 23:37",
    artifact_count: 9,
  },
];

/* ------------------------------------------------------------------ */
/* apiClient mock                                                       */
/* ------------------------------------------------------------------ */

let detailFixture: unknown = FX_DETAIL_101;

vi.mock("@/lib/api", () => ({
  apiClient: vi.fn((path: string) => {
    if (path.startsWith("/api/tasks/detail")) return Promise.resolve(detailFixture);
    if (path.startsWith("/api/tasks/artifact")) return Promise.resolve({ content: "# 문서" });
    if (path.startsWith("/api/tasks")) return Promise.resolve(FX_CARDS);
    return Promise.reject(new Error(`[test] unmocked apiClient path: ${path}`));
  }),
}));

/* ------------------------------------------------------------------ */
/* 렌더 헬퍼                                                             */
/* ------------------------------------------------------------------ */

function renderTasksPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter([{ path: "/tasks", element: <TasksPage /> }], {
    initialEntries: ["/tasks"],
  });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

/** 칸반 카드를 눌러 상세 Sheet를 연다 */
async function openDrawer() {
  renderTasksPage();
  const card = await screen.findByLabelText(`태스크 ${TASK_ID} 상세 보기`);
  fireEvent.click(card);
  return screen.findByRole("tab", { name: /태스크 대시보드/ });
}

function detailCallCount() {
  return vi
    .mocked(apiClient)
    .mock.calls.filter(([p]) => typeof p === "string" && p.startsWith("/api/tasks/detail")).length;
}

beforeEach(() => {
  vi.clearAllMocks();
  detailFixture = FX_DETAIL_101;
  useUiStore.setState({ contextProject: PROJECT });
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* R-5 — 2탭 분리 · 기본 활성 · 배지 9 · 스크롤 격리                       */
/* ------------------------------------------------------------------ */

describe("상세 Sheet 2탭 재구성 (R-5)", () => {
  it("두 탭 렌더와 기본 활성 [T103/L1-R5]", async () => {
    await openDrawer();

    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(2);
    expect(screen.getByRole("tab", { name: /태스크 대시보드/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: /산출물/ })).toHaveAttribute("aria-selected", "false");
    // 산출물 배지 = `.md` 전수 (화이트리스트 폐기 선행 결과)
    expect(screen.getByTestId("artifact-count-badge")).toHaveTextContent("9");
  });

  it("탭별 자체 스크롤 [T103/L1-R5b]", async () => {
    await openDrawer();

    // 통계 탭 본문이 자체 세로 스크롤 컨테이너를 보유한다
    expect(screen.getByTestId("tab-panel-stats").className).toContain("overflow-y-auto");

    const before = detailCallCount();
    fireEvent.mouseDown(screen.getByRole("tab", { name: /산출물/ }));
    // 헤더(ID·상태·기간)는 탭 전환과 무관하게 계속 렌더된다 — SheetHeader 고정
    expect(screen.getByRole("heading", { name: new RegExp(TASK_ID) })).toBeInTheDocument();
    expect(screen.getByTestId("sheet-status")).toBeInTheDocument();
    // [T103/R-19] 기간 라벨은 양끝 모두 BE `time_label` 직독이다(원시 timestamp 혼용 제거).
    // 이 픽스처의 time_label은 R-19 이전 형식(`HH:MM`)이라 그대로 관찰된다 — 실 BE는
    // `YY-MM-DD HH:mm:ss`를 내려보낸다.
    expect(screen.getByTestId("sheet-period")).toHaveTextContent("16:32 → 23:37");
    // 산출물 탭 본문도 자체 컨테이너다
    expect(screen.getByTestId("tab-panel-artifacts").className).toContain("overflow-hidden");
    // 탭 전환으로 상세 API가 재호출되지 않는다
    expect(detailCallCount()).toBe(before);
  });

  it("탭 바 가로 스크롤 격리 [T103/L1-R5c]", async () => {
    await openDrawer();
    fireEvent.mouseDown(screen.getByRole("tab", { name: /산출물/ }));

    const scroller = screen.getByTestId("artifact-tablist-scroll");
    expect(scroller.className).toContain("overflow-x-auto");
    // 문서 탭 9개가 그 컨테이너 안에 있다
    const docTabs = within(scroller).getAllByRole("tab");
    expect(docTabs).toHaveLength(9);
    expect(docTabs[0]).toHaveTextContent("TASK.md");
    // 유형 라벨이 pipeline → verification → log 순으로 구분자 표시된다
    expect(
      within(scroller)
        .getAllByTestId("artifact-type-label")
        .map((el) => el.textContent),
    ).toEqual(["파이프라인", "검증", "로그"]);
  });
});

/* ------------------------------------------------------------------ */
/* R-6 — A-1 요약 4타일                                                  */
/* ------------------------------------------------------------------ */

describe("A-1 요약 4타일 (R-6)", () => {
  it("A-1 4타일 문자열 [T103/L1-R6]", async () => {
    await openDrawer();
    const a1 = screen.getByTestId("block-a1");

    expect(within(a1).getByText("7시간 5분")).toBeInTheDocument();
    expect(within(a1).getByText("1시간 45분")).toBeInTheDocument();
    expect(within(a1).getByText("5시간 20분 (75%)")).toBeInTheDocument();
    expect(within(a1).getByText("TEST-SCENARIO")).toBeInTheDocument();

    // 목업 A-1 구성은 폐기됐다 (H-11 경계)
    expect(within(a1).queryByText("완료 단계")).toBeNull();
    expect(within(a1).queryByText("게이트 · 블로커")).toBeNull();
    // 완료 태스크에는 「진행 중」 배지가 붙지 않는다
    expect(within(a1).queryByText("진행 중")).toBeNull();
  });
});

/* ------------------------------------------------------------------ */
/* R-7 — A-2 단계별 2색 스택 막대                                         */
/* ------------------------------------------------------------------ */

describe("A-2 단계별 스택 막대 (R-7)", () => {
  it("A-2 스택 막대 [T103/L1-R7]", async () => {
    await openDrawer();
    const bars = within(screen.getByTestId("block-a2")).getAllByTestId("a2-bar");
    expect(bars).toHaveLength(7);

    const peaks = bars.filter((b) => b.getAttribute("data-peak") === "true");
    expect(peaks).toHaveLength(1);
    expect(peaks[0].getAttribute("data-stage")).toBe("TEST-SCENARIO");
    expect(peaks[0]).toHaveTextContent("4시간 55분");

    // 단일색 채움이 아니라 작업·대기 2구획으로 분할된다
    expect(peaks[0].getAttribute("data-work-minutes")).toBe("10");
    expect(peaks[0].getAttribute("data-wait-minutes")).toBe("285");
    const work = within(peaks[0]).getByTestId("a2-seg-work");
    const wait = within(peaks[0]).getByTestId("a2-seg-wait");
    expect(work.style.background).toContain("var(--brand-primary)");
    expect(wait.style.background).toContain("var(--brand-tertiary)");
    expect(parseFloat(wait.style.width)).toBeGreaterThan(parseFloat(work.style.width));
  });
});

/* ------------------------------------------------------------------ */
/* R-8 — A-3 타임라인                                                    */
/* ------------------------------------------------------------------ */

describe("A-3 타임라인 (R-8)", () => {
  it("A-3 타임라인 [T103/L1-R8]", async () => {
    await openDrawer();
    const a3 = screen.getByTestId("block-a3");

    const items = within(a3).getAllByTestId("a3-item");
    expect(items).toHaveLength(19);

    // 담당 구분이 색 단독이 아니라 라벨을 동반한다
    expect(items[0]).toHaveTextContent("PM");
    expect(items[1]).toHaveTextContent("캡틴");
    expect(within(a3).getAllByText("캡틴").length).toBeGreaterThan(0);

    // 최대 공백 구간이 별도 표시된다
    const gaps = within(a3).getAllByTestId("a3-gap");
    const maxGap = gaps.filter((g) => g.getAttribute("data-max-gap") === "true");
    expect(maxGap).toHaveLength(1);
    expect(maxGap[0].textContent).toContain("공백 4시간 45분 · 캡틴 확인 대기 · 최대 공백");
  });
});

/* ------------------------------------------------------------------ */
/* R-9 — A-4 상세 표                                                     */
/* ------------------------------------------------------------------ */

describe("A-4 단계별 상세 표 (R-9)", () => {
  it("A-4 상세 표 [T103/L1-R9]", async () => {
    await openDrawer();
    const a4 = screen.getByTestId("block-a4");

    const rows = within(a4).getAllByTestId("a4-row");
    expect(rows).toHaveLength(19);
    expect(within(a4).getAllByTestId("a4-gate")).toHaveLength(4);

    // 소요가 작업·대기 2열로 분리된다 (목업 단일 열 폐기)
    const heads = within(a4).getAllByRole("columnheader").map((h) => h.textContent);
    expect(heads).toEqual(["#", "단계", "항목", "상태", "담당", "시각", "작업", "대기"]);

    // row 2(캡틴 확인 24분)는 대기 열에만 값이 있다
    const r2 = within(rows[1]).getAllByRole("cell").map((c) => c.textContent);
    expect(r2[0]).toBe("2");
    expect(r2[6]).toBe("—");
    expect(r2[7]).toBe("24분");
    // row 3(PM 작업 17분)은 작업 열에만 값이 있다
    const r3 = within(rows[2]).getAllByRole("cell").map((c) => c.textContent);
    expect(r3[6]).toBe("17분");
    expect(r3[7]).toBe("—");

    // 표는 자체 가로 스크롤 컨테이너 안에서만 스크롤된다
    expect(screen.getByTestId("a4-scroll").className).toContain("overflow-x-auto");
  });
});

/* ------------------------------------------------------------------ */
/* R-12 — 결측 축소 표시                                                  */
/* ------------------------------------------------------------------ */

describe("결측 내성 (R-12)", () => {
  it("결측 축소 표시 [T103/L1-R12b]", async () => {
    detailFixture = FX_DETAIL_NOSTATS;
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    await openDrawer();

    expect(screen.getByTestId("stats-empty")).toHaveTextContent("데이터 없음");
    expect(screen.queryByTestId("block-a1")).toBeNull();
    expect(screen.queryByTestId("block-a4")).toBeNull();
    expect(screen.getByTestId("artifact-count-badge")).toHaveTextContent("0");
    expect(errorSpy).not.toHaveBeenCalled();

    errorSpy.mockRestore();
  });

  it("게이트 미기록 표기 [T103/L1-R12b2]", async () => {
    detailFixture = FX_DETAIL_NOGATE;
    await openDrawer();

    const a4 = screen.getByTestId("block-a4");
    // 「0건」이 아니라 「미기록」으로 구분 표기된다 (R-12 AC)
    expect(a4).toHaveTextContent("게이트 미기록");
    expect(a4).not.toHaveTextContent("게이트 0건");
  });
});

/* ------------------------------------------------------------------ */
/* R-18 — 소요 3계열 렌더 (집계기준 16 · 16-a · 16-c)                     */
/* ------------------------------------------------------------------ */

describe("A-1 3계열 + 진행중 4구획 (R-18)", () => {
  it("진행 중 태스크는 총 = PM + 워커 + 캡틴 + 진행중 [T103/L1-TS-106]", async () => {
    detailFixture = FX_DETAIL_103;
    await openDrawer();

    const a1 = screen.getByTestId("block-a1");
    const minutes = (id: string) =>
      Number(within(a1).getByTestId(id).getAttribute("data-minutes"));

    expect(minutes("a1-tile-pm")).toBe(23);
    expect(minutes("a1-tile-worker")).toBe(146);
    expect(minutes("a1-tile-captain")).toBe(130);
    expect(minutes("a1-seg-running")).toBe(184);

    // 3구획만 그리면 184가 사라져 합이 총과 어긋난다 — 4구획이라야 항등이 선다
    const strip = within(a1).getByTestId("a1-strip");
    expect(Number(strip.getAttribute("data-parts-minutes"))).toBe(483);
    expect(Number(strip.getAttribute("data-total-minutes"))).toBe(483);
    expect(23 + 146 + 130 + 184).toBe(483);
    expect(parseFloat(within(a1).getByTestId("a1-seg-running").style.width)).toBeCloseTo(
      (184 / 483) * 100,
      6,
    );

    // 타일 표시 문자열은 전부 BE label 직독이다
    expect(within(a1).getByText("8시간 3분")).toBeInTheDocument();
    expect(within(a1).getByText("23분")).toBeInTheDocument();
    expect(within(a1).getByText("2시간 26분")).toBeInTheDocument();
    expect(within(a1).getByText("2시간 10분 (43%)")).toBeInTheDocument();
    expect(a1).toHaveTextContent("진행중 3시간 4분 포함");
    expect(within(a1).queryByTestId("a1-worker-unmeasured")).toBeNull();
  });

  it("워커 미측정 태스크는 진행중 구획 없이 3구획으로 축퇴 [T103/L1-TS-107]", async () => {
    detailFixture = FX_DETAIL_101_SERIES;
    await openDrawer();

    const a1 = screen.getByTestId("block-a1");
    // PM 타일이 기존 「작업」 값(105분 = 1시간 45분)과 동일 — 축퇴 16-a
    expect(within(a1).getByTestId("a1-tile-pm")).toHaveTextContent("1시간 45분");
    expect(within(a1).getByTestId("a1-tile-pm").getAttribute("data-minutes")).toBe("105");
    // 「워커 0분」이 아니라 「미측정」으로 구분 표기된다
    expect(within(a1).getByTestId("a1-tile-worker")).toHaveTextContent("미측정");
    expect(within(a1).getByTestId("a1-tile-worker").getAttribute("data-measured")).toBe("false");
    expect(within(a1).getByTestId("a1-worker-unmeasured")).toBeInTheDocument();
    // 워커 0폭 · 완료 태스크라 진행중 구획 자체가 없다
    expect(parseFloat(within(a1).getByTestId("a1-seg-worker").style.width)).toBe(0);
    expect(within(a1).queryByTestId("a1-seg-running")).toBeNull();
    expect(Number(within(a1).getByTestId("a1-strip").getAttribute("data-parts-minutes"))).toBe(425);
  });
});

describe("A-2 3색 스택 (R-18)", () => {
  it("PM·워커·캡틴이 서로 다른 토큰으로 분할된다 [T103/L1-TS-108]", async () => {
    detailFixture = FX_DETAIL_103;
    await openDrawer();

    const bars = within(screen.getByTestId("block-a2")).getAllByTestId("a2-bar");
    const execute = bars.find((b) => b.getAttribute("data-stage") === "EXECUTE")!;
    expect(execute.getAttribute("data-pm-minutes")).toBe("7");
    expect(execute.getAttribute("data-worker-minutes")).toBe("80");
    expect(execute.getAttribute("data-captain-minutes")).toBe("0");

    const pm = within(execute).getByTestId("a2-seg-pm");
    const worker = within(execute).getByTestId("a2-seg-worker");
    const captain = within(execute).getByTestId("a2-seg-wait");
    expect(pm.style.background).toContain("var(--brand-primary)");
    expect(worker.style.background).toContain("var(--brand-secondary)");
    expect(captain.style.background).toContain("var(--brand-tertiary)");
    expect(new Set([pm.style.background, worker.style.background, captain.style.background]).size)
      .toBe(3);
    // 워커 몫이 실제 폭을 갖는다 (80 / 87)
    expect(parseFloat(worker.style.width)).toBeCloseTo((80 / 87) * 100, 6);
  });

  it("워커 미기록 태스크는 작업 구획 폭이 3계열 전후로 동일하다 [T103/L1-TS-109]", async () => {
    // (1) 3계열 이전 응답의 작업 구획 폭을 먼저 채집한다
    await openDrawer();
    const before = within(screen.getByTestId("block-a2"))
      .getAllByTestId("a2-seg-work")
      .map((el) => el.style.width);
    cleanup();

    // (2) 같은 태스크의 3계열 응답 — 워커 미기록이라 전액 PM 귀속 (16-a)
    detailFixture = FX_DETAIL_101_SERIES;
    await openDrawer();
    const a2 = screen.getByTestId("block-a2");
    const after = within(a2).getAllByTestId("a2-seg-work").map((el) => el.style.width);

    expect(after).toEqual(before);   // 작업 구획 폭 불변 — 시각 회귀 0건
    for (const seg of within(a2).getAllByTestId("a2-seg-worker")) {
      expect(parseFloat(seg.style.width)).toBe(0);
    }
    for (const seg of within(a2).getAllByTestId("a2-seg-pm")) {
      expect(seg.style.background).toContain("var(--brand-primary)");
    }
    expect(within(a2).getByTestId("a2-worker-unmeasured")).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* R-13 — hex 색상 리터럴 0건 (정적 검사)                                 */
/* ------------------------------------------------------------------ */

describe("토큰 경유 (R-13)", () => {
  it("hex 리터럴 0건 [T103/L1-R13]", () => {
    // 리터럴로 적으면 이 파일 자신이 매칭되므로 런타임 조립한다
    const hexPattern = new RegExp("#" + "[0-9a-fA-F]{3,8}\\b", "g");
    for (const source of [tasksPageSource, statsTestSource]) {
      expect(source.match(hexPattern) ?? []).toEqual([]);
    }
  });
});

/* ------------------------------------------------------------------ */
/* 회귀 — 칸반 읽기 전용 (P-4 회귀 경계 3)                                */
/* ------------------------------------------------------------------ */

describe("칸반 읽기 전용 회귀 (H-7)", () => {
  it("읽기 전용 계약 불변 [T103/L1-REG3]", async () => {
    renderTasksPage();
    await screen.findByLabelText(`태스크 ${TASK_ID} 상세 보기`);

    // 🔒 badge 상시 표시
    expect(screen.getByText("읽기 전용")).toBeInTheDocument();
    // 5컬럼 배치 불변
    for (const label of ["대기", "진행중", "블로킹", "완료", "아카이브"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    // grab 커서·dnd 속성 0건
    const source = tasksPageSource;
    expect(source).not.toContain("cursor-grab");
    // dnd-kit sensors 미도입 — import·useSensor 0건 (@header 문구는 규약 서술이므로 제외)
    expect(source).not.toContain("@dnd-kit");
    expect(source).not.toContain("useSensor");
  });
});

/* ------------------------------------------------------------------ */
/* R-20 — 구획 호버 툴팁 (TS-130~TS-133)                                 */
/* 기대 문면의 시간 문자열은 전부 BE 라벨이다 — 테스트도 조립하지 않는다(P-7).  */
/* ------------------------------------------------------------------ */

/** 103 단계별 3계열 라벨 — BE `format_duration` 실출력(stage: [pm, worker, captain]) */
const LABELS_103: Record<string, [string, string, string]> = {
  TASK: ["0분", "0분", "1시간 55분"],
  ANALYSIS: ["3분", "16분", "7분"],
  PLAN: ["5분", "21분", "2분"],
  "TEST-SCENARIO": ["6분", "20분", "6분"],
  EXECUTE: ["7분", "1시간 20분", "0분"],
  TEST: ["2분", "9분", "0분"],
  CLOSE: ["0분", "0분", "0분"],
};

/** 101 단계별 3계열 라벨 — 워커 전건 미기록이라 워커는 항상 `0분`이다 (16-a) */
const LABELS_101: Record<string, [string, string, string]> = {
  TASK: ["0분", "0분", "24분"],
  ANALYSIS: ["17분", "0분", "5분"],
  PLAN: ["11분", "0분", "2분"],
  "TEST-SCENARIO": ["10분", "0분", "4시간 45분"],
  EXECUTE: ["18분", "0분", "0분"],
  TEST: ["47분", "0분", "4분"],
  CLOSE: ["2분", "0분", "0분"],
};

const withStageLabels = (
  fixture: typeof FX_DETAIL_103 | typeof FX_DETAIL_101_SERIES,
  table: Record<string, [string, string, string]>,
) => ({
  ...fixture,
  pipeline: fixture.pipeline.map((g) => {
    const [pm, worker, captain] = table[g.stage];
    return { ...g, pm_label: pm, worker_label: worker, captain_label: captain };
  }),
});

/** FX-DETAIL-103-LABELS — 워커 기록 진행 중 태스크 + 단계 3계열 라벨 (R-20 응답) */
const FX_DETAIL_103_LABELS = withStageLabels(FX_DETAIL_103, LABELS_103);

/** FX-DETAIL-101-LABELS — 워커 미측정 태스크 + 단계 3계열 라벨 (R-20 응답) */
const FX_DETAIL_101_LABELS = withStageLabels(FX_DETAIL_101_SERIES, LABELS_101);

/** 트리거에 키보드 포커스를 주고 열린 툴팁 1개를 받는다 — 마우스 없이도 떠야 한다 */
async function focusTip(trigger: HTMLElement) {
  fireEvent.focus(trigger);
  const tips = await screen.findAllByRole("tooltip");
  // 구획 툴팁이 상위 막대 툴팁과 겹쳐 열리지 않는다 (SEG_STOP)
  expect(tips).toHaveLength(1);
  return tips[0];
}

const a2Bar = (stage: string) =>
  within(screen.getByTestId("block-a2"))
    .getAllByTestId("a2-bar")
    .find((b) => b.getAttribute("data-stage") === stage)!;

describe("구획 호버 툴팁 (R-20)", () => {
  it("A-2 구획은 단계·계열·라벨·비율·단계 총을 보여준다 [T103/L1-TS-130]", async () => {
    detailFixture = FX_DETAIL_103_LABELS;
    await openDrawer();

    const bar = a2Bar("EXECUTE");
    // EXECUTE 단계 총 87분 = PM 7 + 워커 80 + 캡틴 0
    const tip = await focusTip(within(bar).getByTestId("a2-seg-pm"));
    expect(tip.textContent).toContain("EXECUTE");
    expect(tip.textContent).toContain("PM · 7분 · 8%");
    expect(tip.textContent).toContain("단계 총 1시간 27분");
  });

  it("A-2 워커 구획은 BE 워커 라벨을 보여준다 [T103/L1-TS-131]", async () => {
    detailFixture = FX_DETAIL_103_LABELS;
    await openDrawer();

    const tip = await focusTip(within(a2Bar("EXECUTE")).getByTestId("a2-seg-worker"));
    expect(tip.textContent).toContain("워커 · 1시간 20분 · 92%");
    expect(tip.textContent).not.toContain("미측정");
  });

  it("워커 미측정 태스크는 막대 전체 툴팁이 3계열과 귀속을 말한다 [T103/L1-TS-132]", async () => {
    detailFixture = FX_DETAIL_101_LABELS;
    await openDrawer();

    const bar = a2Bar("TEST-SCENARIO");
    // 워커 구획은 0폭이라 마우스로는 잡히지 않는다 — 막대 전체가 받침이다
    expect(parseFloat(within(bar).getByTestId("a2-seg-worker").style.width)).toBe(0);

    const tip = await focusTip(within(bar).getByTestId("a2-track"));
    expect(tip.textContent).toContain("TEST-SCENARIO · 총 4시간 55분");
    expect(tip.textContent).toContain("PM 10분 · 워커 미측정 · 캡틴 4시간 45분");
    expect(tip.textContent).toContain("워커 미측정 — 그 몫은 PM에 귀속됩니다");

    // 0폭 구획도 키보드로는 도달한다
    cleanup();
    await openDrawer();
    const workerTip = await focusTip(
      within(a2Bar("TEST-SCENARIO")).getByTestId("a2-seg-worker"),
    );
    expect(workerTip.textContent).toContain("워커 · 미측정");
    expect(workerTip.textContent).toContain("워커 미측정 — 그 몫은 PM에 귀속됩니다");
  });

  it("진행 중 태스크의 진행중 구획도 툴팁 대상이다 [T103/L1-TS-133]", async () => {
    detailFixture = FX_DETAIL_103_LABELS;
    await openDrawer();

    const strip = within(screen.getByTestId("block-a1")).getByTestId("a1-strip");
    // 총 483 = PM 23 + 워커 146 + 캡틴 130 + 진행중 184 (16-c)
    const tip = await focusTip(within(strip).getByTestId("a1-seg-running"));
    expect(tip.textContent).toContain("진행중 · 3시간 4분 · 38%");
    expect(tip.textContent).toContain("총 8시간 3분");

    cleanup();
    await openDrawer();
    const barTip = await focusTip(
      within(screen.getByTestId("block-a1")).getByTestId("a1-strip"),
    );
    expect(barTip.textContent).toContain("PM 23분 · 워커 2시간 26분 · 캡틴 2시간 10분");
    expect(barTip.textContent).toContain("진행중 3시간 4분");
  });
});

/* ------------------------------------------------------------------ */
/* R-21 — 야간 보정 배지 (applied 2경로)                                  */
/* ------------------------------------------------------------------ */

/** FX-DETAIL-101-QUIET — 야간 보정이 적용된 응답 (구간 라벨은 BE 완성값) */
const FX_DETAIL_101_QUIET = {
  ...FX_DETAIL_101,
  stats: {
    ...FX_DETAIL_101.stats,
    quiet_hours_applied: true,
    quiet_hours_label: "00:00~09:00",
  },
};

/** FX-DETAIL-101-NOQUIET — 보정이 꺼진 응답: 수치가 벽시계 그대로다 */
const FX_DETAIL_101_NOQUIET = {
  ...FX_DETAIL_101,
  stats: {
    ...FX_DETAIL_101.stats,
    quiet_hours_applied: false,
    quiet_hours_label: "",
  },
};

describe("야간 보정 배지 (R-21)", () => {
  it("applied=true면 A-1에 BE 구간 라벨 배지가 선다 [T103/L1-TS-140]", async () => {
    detailFixture = FX_DETAIL_101_QUIET;
    await openDrawer();

    const a1 = screen.getByTestId("block-a1");
    const badge = within(a1).getByTestId("quiet-hours-badge");
    // 라벨은 BE가 완성해 내린 문자열 그대로다 (P-7 — FE 무계산)
    expect(badge.textContent).toContain("야간 제외 00:00~09:00");

    const tip = await focusTip(badge);
    expect(tip.textContent).toContain("매일 이 구간을 소요에서 제외합니다");
  });

  it("applied=false·필드 부재면 배지가 뜨지 않는다 [T103/L1-TS-141]", async () => {
    detailFixture = FX_DETAIL_101_NOQUIET;
    await openDrawer();
    expect(
      within(screen.getByTestId("block-a1")).queryByTestId("quiet-hours-badge"),
    ).toBeNull();

    // 필드 자체가 없는 기존 응답도 같은 경로로 축퇴한다
    cleanup();
    detailFixture = FX_DETAIL_101;
    await openDrawer();
    expect(
      within(screen.getByTestId("block-a1")).queryByTestId("quiet-hours-badge"),
    ).toBeNull();
  });
});

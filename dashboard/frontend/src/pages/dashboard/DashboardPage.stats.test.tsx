/**
 * @header {
 *   "module": "dashboard-page-stats-test",
 *   "layer": "test",
 *   "domain": "dashboard",
 *   "description": "[T103] 대시보드 B-1~B-4 + 워크플로우 필터 렌더 AC 컴포넌트 테스트. apiClient를 vi.mock으로 대체해 동결 코호트 응답(FX-DASH, BE 실응답 스냅샷)과 빈 응답(FX-DASH-EMPTY)을 주입하고 QueryClientProvider로 DashboardPage를 렌더한다. 스냅샷 테스트·픽셀 비교·전체 트리 검증은 작성하지 않는다(PLAN P-6 범위 한정). [R-18] 소요 3계열 렌더 — B-1 구성 스트립·B-2 3색 스택의 계열 항등(PM + 워커 == 작업 · 캡틴 == 대기)과 워커 미측정 코호트의 축퇴(워커 0폭 · 작업 구획 폭 불변, 16-a)를 단정한다. [R-21] TS-142·TS-143은 B-1 야간 보정 배지 — 응답 최상위 applied=true면 BE 구간 라벨 배지와 툴팁 문면이 서고, applied=false·필드 부재 2경로 모두 배지가 뜨지 않음을 단정한다.",
 *   "exports": [],
 *   "depends": ["dashboard-page", "api-client", "ui-store"],
 *   "task": "103",
 *   "scenarios": ["TS-040", "TS-041", "TS-042", "TS-043", "TS-044", "TS-045", "TS-046", "TS-047", "TS-110", "TS-111", "TS-134", "TS-135", "TS-136", "TS-142", "TS-143"],
 *   "changelog": [
 *     "2026-08-26 T103 R-21: 야간 보정 배지 케이스 2건(TS-142·TS-143) + 픽스처 FX-DASH-QUIET·FX-DASH-NOQUIET 신설. 기존 케이스·픽스처 무변경",
 *     "2026-08-26 T103 R-20: 구획 호버 툴팁 케이스 3건(TS-134~TS-136) + 픽스처 FX-DASH-WORKER-LABELS·FX-DASH-UNMEASURED-LABELS(3계열 라벨·누적 총 동반 응답) 신설. 트리거는 키보드 포커스로 열고 열린 툴팁이 항상 1개임을 확인한다. 기존 케이스·픽스처 무변경",
 *     "2026-08-25 T103 R-18: 3계열 렌더 케이스 2건(TS-110·TS-111) + 픽스처 FX-DASH-WORKER 신설. 기존 케이스·픽스처 무변경"
 *   ]
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DashboardPage } from "./DashboardPage";
import { useUiStore } from "@/store/ui-store";
import { apiClient } from "@/lib/api";
// 정적 검사용 원문 — vite `?raw` 로 읽는다(node:fs 미사용, 신규 의존 0건)
import dashboardPageSource from "./DashboardPage.tsx?raw";
import statsTestSource from "./DashboardPage.stats.test.tsx?raw";

const PROJECT = "/Volumes/Data/AIStudio/workspace/ai-framework";

/* ------------------------------------------------------------------ */
/* 픽스처 — FX-DASH (동결 코호트 21건, BE 실응답 스냅샷)                   */
/* ------------------------------------------------------------------ */

const FX_DASH = {
  owner_term: "캡틴",
    "total_projects": 1,
    "running_tasks": 2,
    "blockers": 0,
    "additional_work": 0,
    "status_distribution": {
      "pending": 0,
      "in_progress": 2,
      "blocked": 0,
      "done": 21
    },
    "activity_trend": [
      {
        "date": "2026-08-19",
        "count": 1
      },
      {
        "date": "2026-08-20",
        "count": 1
      },
      {
        "date": "2026-08-21",
        "count": 2
      },
      {
        "date": "2026-08-22",
        "count": 1
      },
      {
        "date": "2026-08-23",
        "count": 0
      },
      {
        "date": "2026-08-24",
        "count": 3
      },
      {
        "date": "2026-08-25",
        "count": 1
      }
    ],
    "alerts": [],
    "recent_activities": [
      {
        "date": "2026-08-25",
        "task_id": "103-260825-opd-태스크-진행통계",
        "title": "OPAL Console 태스크 진행 통계",
        "project": "ai-framework",
        "stage": ""
      },
      {
        "date": "2026-08-24",
        "task_id": "101-260824-opd-핸드오프-스키마-계약정합",
        "title": "ANALYSIS→PLAN 핸드오프 스키마 계약 정합 + 확정 입력 판정값 템플릿 승격",
        "project": "ai-framework",
        "stage": ""
      },
      {
        "date": "2026-08-24",
        "task_id": "102-260824-opd-태스크분석-경계재정의",
        "title": "op-task 재정의 — 요구사항 도출기 전환 + 판정축 배선 + 자산 정합",
        "project": "ai-framework",
        "stage": ""
      }
    ],
    "completed_tasks": 21,
    "total_tasks": 23,
    "artifact_total": 194,
    "artifact_by_type": {
      "pipeline": 93,
      "verification": 51,
      "log": 43,
      "other": 7
    },
    "workflow_stats": [
      {
        "skill": "opd",
        "n": 7,
        "sample_insufficient": false,
        "median_minutes": 799,
        "median_label": "13시간 19분",
        "mean_minutes": 1057,
        "mean_label": "17시간 37분",
        "work_minutes": 5841,
        "wait_minutes": 1557,
        "wait_ratio": 21,
        "gate_count": 20,
        "blocker_count": 0,
        "stages": [
          {
            "stage": "TASK",
            "n": 7,
            "median_minutes": 24,
            "median_label": "24분",
            "work_minutes": 171,
            "wait_minutes": 156,
            "is_peak": false
          },
          {
            "stage": "ANALYSIS",
            "n": 7,
            "median_minutes": 48,
            "median_label": "48분",
            "work_minutes": 192,
            "wait_minutes": 221,
            "is_peak": false
          },
          {
            "stage": "PLAN",
            "n": 7,
            "median_minutes": 19,
            "median_label": "19분",
            "work_minutes": 810,
            "wait_minutes": 2,
            "is_peak": false
          },
          {
            "stage": "TEST-SCENARIO",
            "n": 7,
            "median_minutes": 33,
            "median_label": "33분",
            "work_minutes": 880,
            "wait_minutes": 773,
            "is_peak": false
          },
          {
            "stage": "EXECUTE",
            "n": 7,
            "median_minutes": 104,
            "median_label": "1시간 44분",
            "work_minutes": 2975,
            "wait_minutes": 0,
            "is_peak": true
          },
          {
            "stage": "TEST",
            "n": 7,
            "median_minutes": 84,
            "median_label": "1시간 24분",
            "work_minutes": 267,
            "wait_minutes": 405,
            "is_peak": false
          },
          {
            "stage": "CLOSE",
            "n": 7,
            "median_minutes": 2,
            "median_label": "2분",
            "work_minutes": 546,
            "wait_minutes": 0,
            "is_peak": false
          }
        ],
        "tasks": [
          {
            "task_id": "080-260801-opd-헤더소스-단일화",
            "title": "헤더 소스 단일화 — headerSource 기준 통일 + 스코프 include/exclude",
            "total_minutes": 1451,
            "total_label": "24시간 11분",
            "is_peak": false
          },
          {
            "task_id": "100-260822-opd-분석코어-공유SSOT",
            "title": "ANALYSIS 분석 코어 공유 SSOT 신설 — 지식 선조회·확정 승계·중복 제거",
            "total_minutes": 2519,
            "total_label": "41시간 59분",
            "is_peak": true
          },
          {
            "task_id": "094-260815-opd-STATE-저널화",
            "title": "STATE.md 파생 섹션 제거 — 저널로 재정의",
            "total_minutes": 1624,
            "total_label": "27시간 4분",
            "is_peak": false
          },
          {
            "task_id": "092-260815-opd-워크트리-작업공간-분리",
            "title": "태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)",
            "total_minutes": 342,
            "total_label": "5시간 42분",
            "is_peak": false
          },
          {
            "task_id": "091-260813-opd-파이프라인-스펙-중복정리",
            "title": "파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격",
            "total_minutes": 799,
            "total_label": "13시간 19분",
            "is_peak": false
          },
          {
            "task_id": "093-260815-opd-사용자확인행-자동승인-일원화",
            "title": "파이프라인 사용자 확인 행 — 자동 승인 경로 일원화",
            "total_minutes": 238,
            "total_label": "3시간 58분",
            "is_peak": false
          },
          {
            "task_id": "101-260824-opd-핸드오프-스키마-계약정합",
            "title": "ANALYSIS→PLAN 핸드오프 스키마 계약 정합 + 확정 입력 판정값 템플릿 승격",
            "total_minutes": 425,
            "total_label": "7시간 5분",
            "is_peak": false
          }
        ]
      },
      {
        "skill": "opds",
        "n": 10,
        "sample_insufficient": false,
        "median_minutes": 276,
        "median_label": "4시간 36분",
        "mean_minutes": 486,
        "mean_label": "8시간 6분",
        "work_minutes": 4679,
        "wait_minutes": 179,
        "wait_ratio": 4,
        "gate_count": 10,
        "blocker_count": 0,
        "stages": [
          {
            "stage": "TASK",
            "n": 10,
            "median_minutes": 2,
            "median_label": "2분",
            "work_minutes": 365,
            "wait_minutes": 1,
            "is_peak": false
          },
          {
            "stage": "PLAN",
            "n": 10,
            "median_minutes": 49,
            "median_label": "49분",
            "work_minutes": 1618,
            "wait_minutes": 6,
            "is_peak": false
          },
          {
            "stage": "EXECUTE",
            "n": 10,
            "median_minutes": 59,
            "median_label": "59분",
            "work_minutes": 1087,
            "wait_minutes": 0,
            "is_peak": true
          },
          {
            "stage": "TEST",
            "n": 10,
            "median_minutes": 43,
            "median_label": "43분",
            "work_minutes": 1511,
            "wait_minutes": 172,
            "is_peak": false
          },
          {
            "stage": "CLOSE",
            "n": 10,
            "median_minutes": 2,
            "median_label": "2분",
            "work_minutes": 98,
            "wait_minutes": 0,
            "is_peak": false
          }
        ],
        "tasks": [
          {
            "task_id": "095-260819-opds-시나리오-목표계열-선작성",
            "title": "TEST-SCENARIO 목표계열 선작성 — PLAN 병렬 도출 트랙 신설",
            "total_minutes": 256,
            "total_label": "4시간 16분",
            "is_peak": false
          },
          {
            "task_id": "096-260820-opds-메모리툴-참조무결성-고착해소",
            "title": "memory-tool 참조 무결성 검사 + 본문 부재 행 고착 해소",
            "total_minutes": 359,
            "total_label": "5시간 59분",
            "is_peak": false
          },
          {
            "task_id": "082-260803-opds-코드맵-매니페스트-샤딩",
            "title": "code-scan 매니페스트 샤딩 — 파일 크기 상한 기반 분산 구조",
            "total_minutes": 295,
            "total_label": "4시간 55분",
            "is_peak": false
          },
          {
            "task_id": "098-260821-opds-근거등급-확정판정-트랙강등",
            "title": "근거 등급층 신설 + 확정/미확정 판정 + 트랙 자동 강등",
            "total_minutes": 423,
            "total_label": "7시간 3분",
            "is_peak": false
          },
          {
            "task_id": "081-260802-opds-워커중단-복구프로토콜",
            "title": "워커 중단 복구 프로토콜 + 디스패치 산출량 상한 + 증분 저장 규율 SSOT화",
            "total_minutes": 166,
            "total_label": "2시간 46분",
            "is_peak": false
          },
          {
            "task_id": "085-260807-opds-릴리즈-체크섬-검증경로-정합",
            "title": "릴리즈 체크섬 검증 경로 정합 — 다운로드 대상과 검증 대상 일치",
            "total_minutes": 254,
            "total_label": "4시간 14분",
            "is_peak": false
          },
          {
            "task_id": "083-260803-opds-샤드정책-확장",
            "title": "샤드 분할 파이프라인 — 2축 판정 + 분할 집행 + 유도",
            "total_minutes": 1800,
            "total_label": "30시간",
            "is_peak": true
          },
          {
            "task_id": "090-260813-opds-파이프라인-스펙-마이그레이션",
            "title": "미전환 6 pilot 파이프라인 스펙 마이그레이션 — 10/10 완전 전환",
            "total_minutes": 215,
            "total_label": "3시간 35분",
            "is_peak": false
          },
          {
            "task_id": "099-260821-opds-보고형식-ADHD-하네스",
            "title": "보고 형식 개정 — ADHD 보고 하네스 v1.0",
            "total_minutes": 1004,
            "total_label": "16시간 44분",
            "is_peak": false
          },
          {
            "task_id": "097-260821-opds-커밋금지-워커주입-슬롯화",
            "title": "워커 커밋 금지 주입 슬롯화 — 프레임워크 보증 경로 신설",
            "total_minutes": 86,
            "total_label": "1시간 26분",
            "is_peak": false
          }
        ]
      },
      {
        "skill": "opp",
        "n": 4,
        "sample_insufficient": true,
        "median_minutes": 75,
        "median_label": "1시간 15분",
        "mean_minutes": 158,
        "mean_label": "2시간 38분",
        "work_minutes": 288,
        "wait_minutes": 343,
        "wait_ratio": 54,
        "gate_count": 0,
        "blocker_count": 0,
        "stages": [
          {
            "stage": "TASK",
            "n": 4,
            "median_minutes": 1,
            "median_label": "1분",
            "work_minutes": 4,
            "wait_minutes": 0,
            "is_peak": false
          },
          {
            "stage": "PLAN",
            "n": 4,
            "median_minutes": 16,
            "median_label": "16분",
            "work_minutes": 72,
            "wait_minutes": 0,
            "is_peak": false
          },
          {
            "stage": "EXECUTE",
            "n": 4,
            "median_minutes": 58,
            "median_label": "58분",
            "work_minutes": 207,
            "wait_minutes": 343,
            "is_peak": true
          },
          {
            "stage": "CLOSE",
            "n": 4,
            "median_minutes": 1,
            "median_label": "1분",
            "work_minutes": 5,
            "wait_minutes": 0,
            "is_peak": false
          }
        ],
        "tasks": [
          {
            "task_id": "087-260810-opp-파이썬-버전게이트-설치유도",
            "title": "설치 스크립트 Python 최소버전 게이트 + 3.14 설치 유도 (플랫폼 대칭화)",
            "total_minutes": 47,
            "total_label": "47분",
            "is_peak": false
          },
          {
            "task_id": "086-260810-opp-아키텍처-다이어그램-재작성",
            "title": "OPAL 아키텍처 다이어그램 재작성 — 지식 자산·환류 루프 강조 + 사실 정합 복구",
            "total_minutes": 450,
            "total_label": "7시간 30분",
            "is_peak": true
          },
          {
            "task_id": "088-260811-opp-클로즈-메모리히스토리-자동연결",
            "title": "CLOSE 완료 시 메모리 히스토리 자동 연결",
            "total_minutes": 103,
            "total_label": "1시간 43분",
            "is_peak": false
          },
          {
            "task_id": "084-260806-opp-현황분석-워크플로우",
            "title": "PM 대화형 AS-IS 분석 워크플로우",
            "total_minutes": 31,
            "total_label": "31분",
            "is_peak": false
          }
        ]
      }
    ]
  };

/**
 * FX-DASH-WORKER — opd 코호트에 워커 소요가 실린 3계열 응답.
 * 오늘의 실코호트에는 워커 기록 태스크가 없다(유일 보유 태스크 103은 진행 중이라
 * 집계기준 3에 따라 완료 모수에서 빠진다) — 따라서 이 픽스처는 BE 계약 형태를 따라
 * 실측 `work_minutes`를 PM·워커로 쪼갠 값이며, 계열 합은 원 응답과 항등이다
 * (PM 971 + 워커 4870 == 작업 5841 · 캡틴 1557 == 대기 1557).
 */
const FX_DASH_WORKER = {
  ...FX_DASH,
  workflow_stats: FX_DASH.workflow_stats.map((w) =>
    w.skill !== "opd"
      ? w
      : {
          ...w,
          pm_minutes: 971,
          worker_minutes: 4870,
          captain_minutes: 1557,
          worker_measured: true,
          stages: w.stages.map((st) => {
            const worker: Record<string, number> = {
              TASK: 120, ANALYSIS: 150, PLAN: 700, "TEST-SCENARIO": 700,
              EXECUTE: 2600, TEST: 200, CLOSE: 400,
            };
            const w2 = worker[st.stage] ?? 0;
            return {
              ...st,
              pm_minutes: st.work_minutes - w2,
              worker_minutes: w2,
              captain_minutes: st.wait_minutes,
              worker_measured: true,
            };
          }),
        },
  ),
};

/** FX-DASH-EMPTY — 완료 태스크가 없어 워크플로우 집계가 비는 경우 */
const FX_DASH_EMPTY = {
  ...FX_DASH,
  completed_tasks: 0,
  workflow_stats: [],
};

/* ------------------------------------------------------------------ */
/* apiClient mock                                                       */
/* ------------------------------------------------------------------ */

let dashFixture: unknown = FX_DASH;

vi.mock("@/lib/api", () => ({
  apiClient: vi.fn((path: string) => {
    if (path.startsWith("/api/dashboard")) return Promise.resolve(dashFixture);
    return Promise.reject(new Error(`[test] unmocked apiClient path: ${path}`));
  }),
}));

/* ------------------------------------------------------------------ */
/* 렌더 헬퍼                                                             */
/* ------------------------------------------------------------------ */

async function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <DashboardPage />
    </QueryClientProvider>,
  );
  // 로딩 스켈레톤도 "대시보드" h1을 렌더하므로 데이터 의존 요소를 기다린다
  await screen.findByText("OPAL 프로젝트");
}

function dashCallCount() {
  return vi
    .mocked(apiClient)
    .mock.calls.filter(([p]) => typeof p === "string" && p.startsWith("/api/dashboard")).length;
}

/** B-4 대조표에서 워크플로우를 선택한다 */
function selectWorkflow(skill: string) {
  const option = screen
    .getAllByTestId("b4-option")
    .find((el) => el.getAttribute("value") === skill || el.textContent?.startsWith(skill));
  expect(option).toBeDefined();
  fireEvent.click(option!);
}

beforeEach(() => {
  vi.clearAllMocks();
  dashFixture = FX_DASH;
  useUiStore.setState({ contextProject: PROJECT });
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* R-11 — B-4 필터 · 표본 부족 · n= 표기                                  */
/* ------------------------------------------------------------------ */

describe("워크플로우 필터 (R-11)", () => {
  it("B-4 필터 연동 [T103/L1-R11]", async () => {
    await renderDashboard();

    // B-4 는 분포 차트가 아니라 필터 진입점이다 — 3개 선택 컨트롤
    expect(screen.getAllByTestId("b4-option")).toHaveLength(3);

    // 기본 선택 = 첫 워크플로우(opd)
    const b1 = screen.getByTestId("block-b1");
    expect(b1).toHaveTextContent("13시간 19분");

    const before = dashCallCount();

    selectWorkflow("opds");
    expect(screen.getByTestId("block-b1")).toHaveTextContent("4시간 36분");
    expect(within(screen.getByTestId("block-b2")).getAllByTestId("b2-bar")).toHaveLength(5);

    selectWorkflow("opp");
    expect(screen.getByTestId("block-b1")).toHaveTextContent("1시간 15분");
    expect(within(screen.getByTestId("block-b2")).getAllByTestId("b2-bar")).toHaveLength(4);
    expect(within(screen.getByTestId("block-b3")).getAllByTestId("b3-column")).toHaveLength(4);

    // 필터는 응답 객체에서 키를 고르는 동작이다 — API 재호출 0건
    expect(dashCallCount()).toBe(before);
  });

  it("표본 부족 배지 [T103/L1-R11b]", async () => {
    await renderDashboard();

    // opd(n=7)·opds(n=10) 선택 시 B-1 배지 0건
    expect(within(screen.getByTestId("block-b1")).queryByText("표본 부족")).toBeNull();
    selectWorkflow("opds");
    expect(within(screen.getByTestId("block-b1")).queryByText("표본 부족")).toBeNull();

    // opp(n=4) 선택 시 배지 표시 — 판정은 sample_insufficient 직독
    selectWorkflow("opp");
    expect(within(screen.getByTestId("block-b1")).getByText("표본 부족")).toBeInTheDocument();
  });

  it("B-2 모수 표기 [T103/L1-R11c]", async () => {
    await renderDashboard();

    const bars = within(screen.getByTestId("block-b2")).getAllByTestId("b2-bar");
    expect(bars).toHaveLength(7);
    for (const bar of bars) {
      expect(bar.textContent).toContain("n=");
    }
    expect(bars[0].textContent).toContain("TASK n=7");
    // 모수는 선택 워크플로우를 따라 바뀐다 (단일 모수 가정 금지)
    selectWorkflow("opds");
    expect(
      within(screen.getByTestId("block-b2")).getAllByTestId("b2-bar")[0].textContent,
    ).toContain("TASK n=10");
    selectWorkflow("opp");
    expect(
      within(screen.getByTestId("block-b2")).getAllByTestId("b2-bar")[0].textContent,
    ).toContain("TASK n=4");
  });

  it("목업 폐기 잔존 0 [T103/L1-R11d]", async () => {
    await renderDashboard();

    // 혼합 중앙값 표기 폐기
    expect(screen.queryByText("5시간 42분")).toBeNull();
    // 「스킬 · 모드 분포」 폐기 — B-4는 필터 컨트롤이다
    expect(screen.queryByText(/스킬 · 모드 분포/)).toBeNull();
    for (const option of screen.getAllByTestId("b4-option")) {
      expect(option.tagName.toLowerCase()).toBe("button");
    }
    // B-3 모수는 완료 태스크만 — 진행 중 102·103 막대 0건
    const ids = screen
      .getAllByTestId("b3-column")
      .map((el) => el.getAttribute("data-task-id") ?? "");
    expect(ids.filter((id) => id.startsWith("102") || id.startsWith("103"))).toEqual([]);
    expect(ids).toHaveLength(7);
  });
});

/* ------------------------------------------------------------------ */
/* R-10 — B-1 요약 5타일                                                 */
/* ------------------------------------------------------------------ */

describe("B-1 요약 5타일 (R-10 화면 대응)", () => {
  it("완료·전체 병기와 산출물 규모 [T103/L1-R10d]", async () => {
    await renderDashboard();
    const b1 = screen.getByTestId("block-b1");

    expect(within(b1).getByText("21 / 23")).toBeInTheDocument();
    expect(within(b1).getByText("13시간 19분")).toBeInTheDocument();
    // 평균은 보조 지표
    expect(b1).toHaveTextContent("평균 17시간 37분");
    expect(within(b1).getByText("21%")).toBeInTheDocument();
    expect(b1).toHaveTextContent("194");
  });
});

/* ------------------------------------------------------------------ */
/* R-12 — 결측 축소 표시                                                  */
/* ------------------------------------------------------------------ */

describe("결측 내성 (R-12)", () => {
  it("결측 축소 표시 [T103/L1-R12c]", async () => {
    dashFixture = FX_DASH_EMPTY;
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    await renderDashboard();

    expect(screen.getByTestId("workflow-stats-empty")).toHaveTextContent("데이터 없음");
    expect(screen.queryByTestId("block-b1")).toBeNull();
    expect(screen.queryByTestId("block-b4")).toBeNull();
    // 기존 5블록은 정상 렌더된다
    expect(screen.getByText("주의 알림")).toBeInTheDocument();
    expect(errorSpy).not.toHaveBeenCalled();

    errorSpy.mockRestore();
  });
});

/* ------------------------------------------------------------------ */
/* R-18 — 소요 3계열 렌더 (집계기준 16 · 16-a)                            */
/* ------------------------------------------------------------------ */

describe("B-1·B-2 3계열 렌더 (R-18)", () => {
  it("워커 기록 코호트는 PM·워커·캡틴 3색으로 분할된다 [T103/L1-TS-110]", async () => {
    dashFixture = FX_DASH_WORKER;
    await renderDashboard();

    // B-1 구성 스트립 — 3계열 합이 원 2계열과 항등이다
    const strip = within(screen.getByTestId("block-b1")).getByTestId("b1-strip");
    expect(Number(strip.getAttribute("data-pm-minutes"))).toBe(971);
    expect(Number(strip.getAttribute("data-worker-minutes"))).toBe(4870);
    expect(Number(strip.getAttribute("data-captain-minutes"))).toBe(1557);
    expect(971 + 4870).toBe(5841);
    expect(strip.getAttribute("data-worker-measured")).toBe("true");
    expect(within(screen.getByTestId("block-b1")).queryByTestId("b1-worker-unmeasured")).toBeNull();

    // B-2 — EXECUTE 막대가 3구획으로 갈린다 (작업 2975 = PM 375 + 워커 2600)
    const bar = within(screen.getByTestId("block-b2"))
      .getAllByTestId("b2-bar")
      .find((b) => b.getAttribute("data-stage") === "EXECUTE")!;
    expect(bar.getAttribute("data-pm-minutes")).toBe("375");
    expect(bar.getAttribute("data-worker-minutes")).toBe("2600");

    const pm = within(bar).getByTestId("b2-seg-pm");
    const worker = within(bar).getByTestId("b2-seg-worker");
    const captain = within(bar).getByTestId("b2-seg-wait");
    expect(pm.style.background).toContain("var(--brand-primary)");
    expect(worker.style.background).toContain("var(--brand-secondary)");
    expect(captain.style.background).toContain("var(--brand-tertiary)");
    expect(new Set([pm.style.background, worker.style.background, captain.style.background]).size)
      .toBe(3);
    expect(parseFloat(worker.style.width)).toBeCloseTo((2600 / 2975) * 100, 6);
  });

  it("워커 미측정 코호트는 워커 0폭으로 축퇴한다 [T103/L1-TS-111]", async () => {
    await renderDashboard();   // FX-DASH — 3계열 필드가 없는 응답

    const b2 = screen.getByTestId("block-b2");
    const bar = within(b2)
      .getAllByTestId("b2-bar")
      .find((b) => b.getAttribute("data-stage") === "EXECUTE")!;
    // 작업 전액이 PM에 귀속된다 (16-a) — 작업 구획 폭은 종전대로 100%
    expect(bar.getAttribute("data-pm-minutes")).toBe("2975");
    expect(bar.getAttribute("data-worker-minutes")).toBe("0");
    expect(parseFloat(within(bar).getByTestId("b2-seg-work").style.width)).toBe(100);
    expect(parseFloat(within(bar).getByTestId("b2-seg-worker").style.width)).toBe(0);
    expect(parseFloat(within(bar).getByTestId("b2-seg-pm").style.width)).toBe(100);

    expect(within(b2).getByTestId("b2-worker-unmeasured")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("block-b1")).getByTestId("b1-worker-unmeasured"),
    ).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* R-13 — hex 색상 리터럴 0건 (정적 검사)                                 */
/* ------------------------------------------------------------------ */

describe("토큰 경유 (R-13)", () => {
  it("hex 리터럴 0건 [T103/L1-R13b]", () => {
    // 리터럴로 적으면 이 파일 자신이 매칭되므로 런타임 조립한다
    const hexPattern = new RegExp("#" + "[0-9a-fA-F]{3,8}\\b", "g");
    for (const source of [dashboardPageSource, statsTestSource]) {
      expect(source.match(hexPattern) ?? []).toEqual([]);
    }
  });
});

/* ------------------------------------------------------------------ */
/* 회귀 — 기존 5블록 (P-4 회귀 경계 3)                                    */
/* ------------------------------------------------------------------ */

describe("기존 블록 회귀 (H-7)", () => {
  it("기존 5블록 렌더 불변 [T103/L1-REG3b]", async () => {
    await renderDashboard();

    for (const label of [
      "OPAL 프로젝트",
      "진행중 태스크",
      "블로커",
      "추가 작업",
      "태스크 활동 추이",
      "단계 분포",
      "주의 알림",
      "최근 활동",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    // 기존 4메트릭 값이 B 블록 추가로 변하지 않는다
    expect(screen.getByText("전체 태스크 23개")).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* R-20 — 구획 호버 툴팁 (TS-134~TS-136)                                 */
/* 기대 문면의 시간 문자열은 전부 BE 라벨이다 — 테스트도 조립하지 않는다(P-7).  */
/* ------------------------------------------------------------------ */

/** opd 단계별 라벨 — [누적 총, PM, 워커, 캡틴]. 워커 기록 코호트(FX-DASH-WORKER) 기준 */
const B2_LABELS_MEASURED: Record<string, [string, string, string, string]> = {
  TASK: ["5시간 27분", "51분", "2시간", "2시간 36분"],
  ANALYSIS: ["6시간 53분", "42분", "2시간 30분", "3시간 41분"],
  PLAN: ["13시간 32분", "1시간 50분", "11시간 40분", "2분"],
  "TEST-SCENARIO": ["27시간 33분", "3시간", "11시간 40분", "12시간 53분"],
  EXECUTE: ["49시간 35분", "6시간 15분", "43시간 20분", "0분"],
  TEST: ["11시간 12분", "1시간 7분", "3시간 20분", "6시간 45분"],
  CLOSE: ["9시간 6분", "2시간 26분", "6시간 40분", "0분"],
};

/** FX-DASH-WORKER-LABELS — 워커 기록 코호트 + 3계열 라벨·누적 총 (R-20 응답) */
const FX_DASH_WORKER_LABELS = {
  ...FX_DASH_WORKER,
  workflow_stats: FX_DASH_WORKER.workflow_stats.map((w) =>
    w.skill !== "opd"
      ? w
      : {
          ...w,
          pm_label: "16시간 11분",
          worker_label: "81시간 10분",
          captain_label: "25시간 57분",
          stages: w.stages.map((st) => {
            const [total, pm, worker, captain] = B2_LABELS_MEASURED[st.stage];
            return {
              ...st,
              total_minutes: st.work_minutes + st.wait_minutes,
              total_label: total,
              pm_label: pm,
              worker_label: worker,
              captain_label: captain,
            };
          }),
          // B-3 — 태스크 막대는 태스크 층 3계열을 그대로 승계한다 (080: 1451 = 200 + 1000 + 251)
          tasks: w.tasks.map((t) =>
            t.task_id !== "080-260801-opd-헤더소스-단일화"
              ? t
              : {
                  ...t,
                  pm_minutes: 200,
                  pm_label: "3시간 20분",
                  worker_minutes: 1000,
                  worker_label: "16시간 40분",
                  captain_minutes: 251,
                  captain_label: "4시간 11분",
                  worker_measured: true,
                },
          ),
        },
  ),
};

/** FX-DASH-UNMEASURED-LABELS — 워커 미측정 코호트의 축퇴 응답 + 라벨 (16-a) */
const FX_DASH_UNMEASURED_LABELS = {
  ...FX_DASH,
  workflow_stats: FX_DASH.workflow_stats.map((w) =>
    w.skill !== "opd"
      ? w
      : {
          ...w,
          worker_measured: false,
          stages: w.stages.map((st) =>
            st.stage !== "EXECUTE"
              ? st
              : {
                  ...st,
                  total_minutes: 2975,
                  total_label: "49시간 35분",
                  pm_minutes: 2975,
                  pm_label: "49시간 35분",
                  worker_minutes: 0,
                  worker_label: "0분",
                  captain_minutes: 0,
                  captain_label: "0분",
                  worker_measured: false,
                },
          ),
          tasks: w.tasks.map((t) =>
            t.task_id !== "080-260801-opd-헤더소스-단일화"
              ? t
              : {
                  ...t,
                  pm_minutes: 1200,
                  pm_label: "20시간",
                  worker_minutes: 0,
                  worker_label: "0분",
                  captain_minutes: 251,
                  captain_label: "4시간 11분",
                  worker_measured: false,
                },
          ),
        },
  ),
};

/** 트리거에 키보드 포커스를 주고 열린 툴팁 1개를 받는다 — 마우스 없이도 떠야 한다 */
async function focusTip(trigger: HTMLElement) {
  fireEvent.focus(trigger);
  const tips = await screen.findAllByRole("tooltip");
  // 구획 툴팁이 상위 막대 툴팁과 겹쳐 열리지 않는다 (SEG_STOP)
  expect(tips).toHaveLength(1);
  return tips[0];
}

const b2Bar = (stage: string) =>
  within(screen.getByTestId("block-b2"))
    .getAllByTestId("b2-bar")
    .find((b) => b.getAttribute("data-stage") === stage)!;

describe("구획 호버 툴팁 (R-20)", () => {
  it("B-2 구획은 단계·모수·계열·라벨·비율·단계 총을 보여준다 [T103/L1-TS-134]", async () => {
    dashFixture = FX_DASH_WORKER_LABELS;
    await renderDashboard();

    // EXECUTE 누적 2975 = PM 375 + 워커 2600 + 캡틴 0
    const tip = await focusTip(within(b2Bar("EXECUTE")).getByTestId("b2-seg-pm"));
    expect(tip.textContent).toContain("EXECUTE n=7");
    expect(tip.textContent).toContain("PM · 6시간 15분 · 13%");
    expect(tip.textContent).toContain("단계 총 49시간 35분");
  });

  it("B-2 막대 전체는 미측정 코호트의 3계열과 귀속을 말한다 [T103/L1-TS-135]", async () => {
    dashFixture = FX_DASH_UNMEASURED_LABELS;
    await renderDashboard();

    const bar = b2Bar("EXECUTE");
    expect(parseFloat(within(bar).getByTestId("b2-seg-worker").style.width)).toBe(0);

    const tip = await focusTip(within(bar).getByTestId("b2-track"));
    expect(tip.textContent).toContain("EXECUTE n=7");
    expect(tip.textContent).toContain("누적 49시간 35분 · 중앙값 1시간 44분");
    expect(tip.textContent).toContain("PM 49시간 35분 · 워커 미측정 · 캡틴 0분");
    expect(tip.textContent).toContain("워커 미측정 — 그 몫은 PM에 귀속됩니다");
  });

  it("B-3 태스크 막대는 식별·총·3계열을 보여준다 [T103/L1-TS-136]", async () => {
    dashFixture = FX_DASH_WORKER_LABELS;
    await renderDashboard();

    const column = within(screen.getByTestId("block-b3"))
      .getAllByTestId("b3-column")
      .find((c) => c.getAttribute("data-task-id") === "080-260801-opd-헤더소스-단일화")!;

    const tip = await focusTip(column);
    expect(tip.textContent).toContain("080-260801-opd-헤더소스-단일화");
    expect(tip.textContent).toContain("총 24시간 11분");
    expect(tip.textContent).toContain("PM 3시간 20분 · 워커 16시간 40분 · 캡틴 4시간 11분");
    expect(tip.textContent).not.toContain("미측정");

    // 미측정 태스크는 워커 자리에 「미측정」과 귀속 안내가 선다
    cleanup();
    dashFixture = FX_DASH_UNMEASURED_LABELS;
    await renderDashboard();
    const unmeasured = within(screen.getByTestId("block-b3"))
      .getAllByTestId("b3-column")
      .find((c) => c.getAttribute("data-task-id") === "080-260801-opd-헤더소스-단일화")!;
    const tip2 = await focusTip(unmeasured);
    expect(tip2.textContent).toContain("PM 20시간 · 워커 미측정 · 캡틴 4시간 11분");
    expect(tip2.textContent).toContain("워커 미측정 — 그 몫은 PM에 귀속됩니다");
  });
});

/* ------------------------------------------------------------------ */
/* R-21 — 야간 보정 배지 (applied 2경로)                                  */
/* ------------------------------------------------------------------ */

/** FX-DASH-QUIET — 야간 보정이 적용된 응답 (구간 라벨은 BE 완성값, 최상위 원천) */
const FX_DASH_QUIET = {
  ...FX_DASH,
  quiet_hours_applied: true,
  quiet_hours_label: "00:00~09:00",
};

/** FX-DASH-NOQUIET — 보정이 꺼진 응답: 수치가 벽시계 그대로다 */
const FX_DASH_NOQUIET = {
  ...FX_DASH,
  quiet_hours_applied: false,
  quiet_hours_label: "",
};

describe("야간 보정 배지 (R-21)", () => {
  it("applied=true면 B-1에 BE 구간 라벨 배지가 선다 [T103/L1-TS-142]", async () => {
    dashFixture = FX_DASH_QUIET;
    await renderDashboard();

    const b1 = screen.getByTestId("block-b1");
    const badge = within(b1).getByTestId("quiet-hours-badge");
    // 라벨은 BE가 완성해 내린 문자열 그대로다 (P-7 — FE 무계산)
    expect(badge.textContent).toContain("야간 제외 00:00~09:00");

    const tip = await focusTip(badge);
    expect(tip.textContent).toContain("매일 이 구간을 소요에서 제외합니다");
  });

  it("applied=false·필드 부재면 배지가 뜨지 않는다 [T103/L1-TS-143]", async () => {
    dashFixture = FX_DASH_NOQUIET;
    await renderDashboard();
    expect(
      within(screen.getByTestId("block-b1")).queryByTestId("quiet-hours-badge"),
    ).toBeNull();

    // 필드 자체가 없는 기존 응답도 같은 경로로 축퇴한다
    cleanup();
    dashFixture = FX_DASH;
    await renderDashboard();
    expect(
      within(screen.getByTestId("block-b1")).queryByTestId("quiet-hours-badge"),
    ).toBeNull();
  });
});

/* ------------------------------------------------------------------ */
/* 사용자 호칭 — owner_term (T103)                                       */
/* ------------------------------------------------------------------ */

describe("사용자 호칭", () => {
  it("owner_term이 화면 라벨에 반영된다 [T103/L1-TS-150]", async () => {
    dashFixture = { ...FX_DASH_WORKER_LABELS, owner_term: "대장" };
    await renderDashboard();

    const b1 = screen.getByTestId("block-b1");
    // BE가 내린 호칭이 타일 라벨에 그대로 들어간다 — FE는 조립만 한다
    expect(b1).toHaveTextContent("대장 확인 대기 비중");
    expect(b1).not.toHaveTextContent("캡틴 확인 대기 비중");
  });

  it("owner_term 부재 시 「사용자」로 폴백한다 [T103/L1-TS-151]", async () => {
    const { owner_term: _drop, ...noTerm } = FX_DASH_WORKER_LABELS as Record<string, unknown>;
    dashFixture = noTerm;
    await renderDashboard();

    // 구버전 캐시 응답 대비 — BE 폴백과 같은 값으로 FE에서도 한 번 더 감싼다
    expect(screen.getByTestId("block-b1")).toHaveTextContent("사용자 확인 대기 비중");
  });
});

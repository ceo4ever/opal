/**
 * @header {
 *   "module": "tasks-page",
 *   "layer": "page",
 *   "domain": "tasks",
 *   "description": "태스크 칸반 화면 — 상태 5컬럼(대기/진행중/블로킹/완료/아카이브) + 카드(ID·제목·진행률·badge·단계 뱃지 진행중 강조) + 카드 클릭→Sheet(right 사이드 패널). [T103] 상세 Sheet 본문을 2탭으로 재구성 — 「태스크 대시보드」(기본 활성: 파이프라인 스테퍼 + A-1 요약 4타일(총·PM·워커·캡틴)+구획 스트립+최장 단계 메타 + A-2 단계별 PM·워커·캡틴 3색 스택 막대 + A-3 타임라인 + A-4 단계별 상세 표) · 「산출물」(`.md` 전수 탭, 유형 그룹 정렬, TabsList 자체 가로 스크롤). 태스크 식별 헤더(ID·skill·mode·상태·기간)는 탭 위 SheetHeader에 고정. 완료·아카이브 컬럼 최근순 정렬. [MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용 — 통계 블록도 조회 전용이며 쓰기·편집·정렬 토글을 갖지 않는다. [MUST] FE 무계산 — 시간 표시 문자열은 BE `*_label` 직독이며 포맷 함수를 두지 않는다(PLAN P-7). [T103/R-18] 소요 3계열(집계기준 16) — PM=var(--brand-primary)·워커=var(--brand-secondary)·캡틴=var(--brand-tertiary), 진행 중 태스크의 A-1은 「진행중」(var(--status-running), current_elapsed_minutes)을 4번째 구획으로 세워 실시간 총과의 항등을 복원한다(16-c). 3계열 필드가 없는 응답은 seriesOf가 축퇴 16-a로 사상해 워커 0폭·PM=기존 작업 폭이 되어 시각 회귀가 없다. [MUST] 색상은 index.css :root 토큰(var(--brand-*)·var(--status-*)) 경유 — hex 리터럴 금지. contextProject(ui-store) 전역 구독 — 스위처 연동. [T103/R-20] 구획 호버 툴팁 — 막대의 각 구획(PM·워커·캡틴, A-1은 진행중 포함)과 막대 전체가 Radix Tooltip 트리거(TooltipTrigger asChild)이며 tabIndex로 키보드 포커스에서도 뜬다. 구획은 SEG_STOP으로 포인터·포커스 전파를 끊어 상위 막대 툴팁이 겹쳐 열리지 않게 한다. 워커 미측정 태스크는 워커 구획이 0폭이라 호버가 잡히지 않으므로 막대 전체 툴팁이 3계열 요약과 「워커 미측정 — 그 몫은 PM에 귀속됩니다」를 대신 말한다(16-a). [MUST] 툴팁의 시간 문자열도 BE `*_label` 직독이며 분→시간 변환을 FE가 하지 않는다(P-7) — 비율(%)만 막대 폭 계산에 쓰는 값을 그대로 반올림한다. [T103/R-21] 야간 보정 배지 — BE `quiet_hours_applied`가 참일 때만 A-1 헤딩에 「야간 제외 {quiet_hours_label}」 배지를 세우고 Radix Tooltip으로 「매일 이 구간을 소요에서 제외합니다」를 덧붙인다. 거짓이면 렌더하지 않는다(보정 꺼짐 = 벽시계 그대로). [MUST] 구간 문자열은 BE 완성값 직독이며 FE가 시:분을 조립하지 않는다(P-7).",
 *   "exports": ["TasksPage"],
 *   "depends": ["api-client", "card", "badge", "progress", "sheet", "tabs", "table", "scroll-area", "tooltip", "skeleton", "separator", "markdown-view", "ui-store"],
 *   "task": "103",
 *   "changelog": [
 *     "2026-08-26 T104: 화면 호칭 하드코딩 제거 — 「캡틴」 리터럴 13곳을 BE `owner_term` 직독으로 교체(부재 시 「사용자」 폴백). TaskDetail 로컬 타입에 owner_term 동기, StatsSummaryCards·StageStackBars·RowTimeline에 ownerTerm prop 명시 전달. 계열 식별자 필드명(captain_minutes·captain_label)과 색·폭·레이아웃은 무변경",
    "2026-08-26 T103 R-21: A-1 헤딩에 야간 보정 배지 추가 — QuietHoursBadge 신설, BlockHeading에 extra 슬롯 추가, TaskStats 로컬 타입에 quiet_hours_applied·quiet_hours_label 동기. 타일·구획·색·레이아웃 무변경",
 *     "2026-08-25 T103 Step9: 상세 Sheet 2탭 재구성 + 로컬 타입 동기(PipelineGate·PipelineRow 확장·PipelineStageGroup 확장·TaskStats·ArtifactItem)",
 *     "2026-08-25 T103 Step10: A-1~A-4 블록 렌더(StatsSummaryCards·StageStackBars·RowTimeline·RowDetailTable) — BE 값 직독",
 *     "2026-08-26 T103 R-20: A-1 구획 스트립·A-2 스택 막대에 구획 호버 툴팁 추가 — ChartTip·SeriesTip·UnmeasuredNote·pctOf·SEG_STOP·SEG_FOCUS 신설, PipelineStageGroup 로컬 타입에 pm_label·worker_label·captain_label 동기. 막대 폭·색·구획 수 무변경. TS-130~TS-133",
 *     "2026-08-25 T103 R-19: 시각 표기 `YY-MM-DD HH:mm:ss` 수용 — A-3 시각 거터(74→138px)·A-4 「시각」 열(w-16→w-32) 폭만 확장하고, 기간 라벨은 원시 timestamp 혼용을 걷어내 양끝 모두 BE time_label 직독으로 통일. 포맷 계산은 여전히 FE에 없다(P-7)",
 *     "2026-08-25 T103 R-18: A-1·A-2 3계열 렌더 — A-1 4타일+4구획 스트립(진행중 포함)+최장 단계 메타 줄, A-2 3색 스택(작업 구획 내부 PM·워커 2분할), seriesOf·LegendDot 신설. A-3·A-4 무변경"
 *   ]
 * }
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { useUiStore } from "@/store/ui-store";
import {
  Lock,
  Inbox,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  Clock,
  FileText,
  ChevronRight,
  AlertCircle,
  Archive,
  BarChart3,
  Moon,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { MarkdownView } from "@/components/markdown-view";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

type KanbanColumn = "pending" | "in_progress" | "blocked" | "done" | "archive";

interface TaskCard {
  task_id: string;
  title: string;
  skill: string;
  mode: string;
  column: KanbanColumn;
  current_stage: string;
  progress: number;
  updated_at: string;
  artifact_count: number;
}

/** BE `PipelineGate` — 원천 스키마가 artifacts·checklist로 닫혀 있다(불리언 아님) */
interface PipelineGate {
  artifacts: string[];
  checklist: string[];
}

interface PipelineRow {
  row: number; // deprecated 별칭 — row_id 값이 채워진다
  stage: string;
  status: string;
  updated_at: string; // deprecated 별칭 — timestamp 값이 채워진다
  // 원천 필드
  row_id: number;
  key: string;
  item: string;
  timestamp: string;
  time_label: string;
  owner: string;
  owner_label: string;
  note: string | null;
  gate: PipelineGate | null;
  // 파생 필드 (BE 계산)
  duration_minutes: number;
  duration_label: string;
  series: string; // work | wait | ""(비 done)
  is_max_gap: boolean;
}

interface PipelineStageGroup {
  stage: string;
  done_count: number;
  total: number;
  status: string; // done | in_progress | pending | blocked
  rows: PipelineRow[];
  work_minutes: number;
  wait_minutes: number;
  total_minutes: number;
  total_label: string;
  is_peak: boolean;
  // 3계열 분해 (집계기준 16) — 3계열 이전 응답에는 없어 optional. 부재 시 축퇴 16-a로 읽는다
  pm_minutes?: number;
  worker_minutes?: number;
  captain_minutes?: number;
  worker_measured?: boolean;
  // 3계열 표시 문자열 (R-20) — 구획 호버가 읽는다. 라벨 부재 응답은 `—`로 축퇴
  pm_label?: string;
  worker_label?: string;
  captain_label?: string;
}

/** BE `TaskStats` — 정적 파생 + 실시간 파생 병합. 표시 문자열은 전부 BE 소유(P-7) */
interface TaskStats {
  available: boolean;
  total_minutes: number;
  total_label: string;
  work_minutes: number;
  work_label: string;
  wait_minutes: number;
  wait_label: string;
  wait_ratio: number;
  // 3계열 분해 (집계기준 16) — pm + worker + captain == 정적 총. 부재 시 축퇴 16-a로 읽는다
  pm_minutes?: number;
  pm_label?: string;
  worker_minutes?: number;
  worker_label?: string;
  captain_minutes?: number;
  captain_label?: string;
  worker_measured?: boolean; // 「워커 0분」과 「미측정」(필드 부재) 구분 신호
  worker_clamped_count?: number;
  peak_stage: string;
  peak_stage_label: string;
  gate_count: number;
  gate_recorded: boolean;
  blocker_count: number;
  is_running: boolean;
  current_row_id: number | null;
  current_stage: string | null;
  current_item: string | null;
  current_key: string | null;
  current_series: string;
  current_elapsed_minutes: number | null;
  current_elapsed_label: string;
  // 야간 보정 표면화 (집계기준 17) — 구간 문자열은 BE 완성값이며 FE가 조립하지 않는다 (P-7)
  quiet_hours_applied?: boolean;
  quiet_hours_label?: string;
}

interface ArtifactItem {
  name: string;
  type: string; // pipeline | verification | log | other
  type_label: string; // 파이프라인 | 검증 | 로그 | 기타
}

interface TaskDetail {
  task_id: string;
  title: string;
  skill: string;
  mode: string;
  current_status: string;
  current_stage: string;
  progress: number;
  pipeline: PipelineStageGroup[];
  artifacts: string[];
  updated_at: string;
  stats: TaskStats | null;
  artifact_items: ArtifactItem[];
  // 사용자 호칭 — BE가 identity.md에서 읽어 내린다. 화면 문구의 유일한 원천(하드코딩 금지)
  owner_term?: string;
}

/* ------------------------------------------------------------------ */
/* 컬럼 설정                                                            */
/* ------------------------------------------------------------------ */

const COLUMNS: {
  key: KanbanColumn;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  statusClass: string;
}[] = [
  {
    key: "pending",
    label: "대기",
    icon: Inbox,
    statusClass: "text-status-todo",
  },
  {
    key: "in_progress",
    label: "진행중",
    icon: PlayCircle,
    statusClass: "text-status-running",
  },
  {
    key: "blocked",
    label: "블로킹",
    icon: AlertTriangle,
    statusClass: "text-status-blocked",
  },
  {
    key: "done",
    label: "완료",
    icon: CheckCircle2,
    statusClass: "text-status-done",
  },
  {
    key: "archive",
    label: "아카이브",
    icon: Archive,
    statusClass: "text-muted-foreground",
  },
];

function columnBorderClass(col: KanbanColumn) {
  return {
    pending: "border-l-status-todo",
    in_progress: "border-l-status-running",
    blocked: "border-l-status-blocked",
    done: "border-l-status-done",
    archive: "border-l-border",
  }[col];
}

function stageStatusClass(status: string) {
  if (status === "done") return "bg-status-done";
  if (status === "in_progress") return "bg-status-running";
  if (status === "blocked") return "bg-status-blocked";
  return "bg-status-todo";
}

/** 행 status → 한국어 표시. 표시 매핑일 뿐 계산이 아니다 */
const ROW_STATUS_TEXT: Record<string, string> = {
  done: "완료",
  in_progress: "진행중",
  blocked: "블로킹",
  pending: "대기",
  failed: "실패",
  na: "해당없음",
};

function rowStatusText(status: string) {
  return ROW_STATUS_TEXT[status] ?? status;
}

/**
 * [MUST] index.css :root "hex 하드코딩 금지 — oklch() 함수 값만 사용한다".
 * 담당 색은 CSS 변수 문자열로만 전달한다.
 */
function ownerColor(owner: string) {
  if (owner === "user") return "var(--brand-tertiary)";
  if (owner === "auto") return "var(--brand-secondary)";
  return "var(--brand-primary)";
}

/** stage 그룹 rows를 원천 정렬 키(row_id) 기준 단일 리스트로 평탄화한다 */
function flattenRows(pipeline: PipelineStageGroup[]): PipelineRow[] {
  return pipeline
    .flatMap((g) => g.rows)
    .slice()
    .sort((a, b) => a.row_id - b.row_id);
}

/** 막대 폭 기하 — 표시 문자열이 아니라 *_minutes에서 파생한다 (PLAN P-7 근거 3) */
function widthPct(part: number, whole: number) {
  return whole > 0 ? (part / whole) * 100 : 0;
}

/** 3계열 사상의 입력 — 2계열(하위 호환)과 3계열(집계기준 16)이 함께 실린다 */
interface SeriesSource {
  work_minutes: number;
  wait_minutes: number;
  pm_minutes?: number;
  worker_minutes?: number;
  captain_minutes?: number;
  worker_measured?: boolean;
}

/**
 * 소요를 PM·워커·캡틴 3계열로 읽는다 (집계기준 16).
 * 3계열 필드가 없는 응답은 축퇴 규칙 16-a — 워커 미기록이므로 「작업」 전액이 PM,
 * 「대기」 전액이 캡틴이다. 계산이 아니라 2계열↔3계열 계약 사상이며 표시 문자열을 만들지 않는다.
 */
function seriesOf(src: SeriesSource) {
  return {
    pm: src.pm_minutes ?? src.work_minutes,
    worker: src.worker_minutes ?? 0,
    captain: src.captain_minutes ?? src.wait_minutes,
    measured: src.worker_measured ?? false,
  };
}

/** 범례 항목 — 색 단독이 아니라 라벨을 동반한다 */
function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono">
      <i
        className="inline-block h-2.5 w-2.5 rounded-sm"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* 구획 호버 툴팁 (R-20) — 조회 전용                                      */
/* 시간 문자열은 BE `*_label` 직독이며 FE는 분→시간 변환을 하지 않는다(P-7). */
/* ------------------------------------------------------------------ */

/** 구획 비율(%) — 막대 폭 계산에 쓰는 값 그대로다. 시간 문자열이 아니므로 라벨 대상이 아니다 */
function pctOf(part: number, whole: number) {
  return Math.round(widthPct(part, whole));
}

/**
 * 중첩 트리거 차단 — 구획 위에서는 상위 막대 툴팁이 함께 열리면 안 된다.
 * Radix Trigger는 전달받은 핸들러를 자기 핸들러보다 먼저 실행하므로,
 * 여기서 전파를 끊으면 구획 툴팁만 남고 막대 툴팁은 열리지 않는다.
 */
const SEG_STOP = {
  onPointerMove: (e: React.PointerEvent) => e.stopPropagation(),
  onFocus: (e: React.FocusEvent) => e.stopPropagation(),
} as const;

/** 키보드로도 뜨게 하는 포커스 가능 구획의 공통 클래스 */
const SEG_FOCUS =
  "outline-none focus-visible:outline focus-visible:outline-2 " +
  "focus-visible:-outline-offset-2 focus-visible:outline-ring";

/** 막대·구획을 그대로 트리거로 삼는다 (asChild — 별도 래퍼 DOM을 만들지 않는다) */
function ChartTip({
  tip,
  children,
}: {
  tip: React.ReactNode;
  children: React.ReactElement;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent className="font-mono text-[11px] leading-5">
        {tip}
      </TooltipContent>
    </Tooltip>
  );
}

/** 구획 1개의 호버 문면 — 대상 · 계열명 · 그 계열 라벨 · 비율 · 총 라벨 */
function SeriesTip({
  scope,
  series,
  label,
  pct,
  foot,
}: {
  scope: string;
  series: string;
  label: string;
  pct: number;
  foot: string;
}) {
  return (
    <>
      <p className="font-semibold">{scope}</p>
      <p>
        {series} · {label} · {pct}%
      </p>
      <p className="opacity-70">{foot}</p>
    </>
  );
}

/** 워커 미측정 안내 — 0폭 구획은 호버가 잡히지 않으므로 막대 툴팁이 대신 말한다 (16-a) */
function UnmeasuredNote() {
  return <p className="opacity-70">워커 미측정 — 그 몫은 PM에 귀속됩니다</p>;
}

/* ------------------------------------------------------------------ */
/* 통계 블록 공통 헤딩                                                    */
/* ------------------------------------------------------------------ */

function BlockHeading({
  code,
  title,
  aside,
  extra,
}: {
  code: string;
  title: string;
  aside?: string;
  extra?: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span
        className="font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded"
        style={{
          background:
            "color-mix(in oklab, var(--brand-primary) 15%, transparent)",
          color: "var(--brand-primary)",
        }}
      >
        {code}
      </span>
      <span className="text-[13px] font-semibold">{title}</span>
      {extra}
      {aside && (
        <span className="font-mono text-[11px] text-muted-foreground ml-auto">
          {aside}
        </span>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 야간 보정 배지 — BE `quiet_hours_*` 직독 (집계기준 17)                  */
/* 구간 문자열은 BE가 완성해 내린다 — FE는 조립하지 않는다 (P-7)           */
/* ------------------------------------------------------------------ */

function QuietHoursBadge({
  applied,
  label,
}: {
  applied?: boolean;
  label?: string;
}) {
  // 보정이 꺼져 있으면 수치가 벽시계 그대로라 배지를 띄우지 않는다
  if (!applied) return null;
  return (
    <TooltipProvider delayDuration={120}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="secondary"
            className="text-[9px] px-1.5 py-0 h-4 gap-1 font-normal"
            data-testid="quiet-hours-badge"
            tabIndex={0}
          >
            <Moon className="h-2.5 w-2.5" />
            야간 제외 {label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="text-[11px]">
          매일 이 구간을 소요에서 제외합니다
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/* ------------------------------------------------------------------ */
/* A-1 StatsSummaryCards — 총·PM·워커·캡틴 4타일 + 구획 스트립 + 최장 단계  */
/* (전부 BE label 직독 — 시간 문자열을 FE에서 만들지 않는다)                */
/* ------------------------------------------------------------------ */

function StatsSummaryCards({
  stats,
  ownerTerm,
}: {
  stats: TaskStats;
  ownerTerm: string;
}) {
  const s = seriesOf(stats);
  // [MUST] 집계기준 16-c — 진행 중 태스크의 총은 실시간 값(created_at→now)이라 3계열 합보다
  // 크고, 그 차이가 현재 행 경과 시간이다. 「진행중」을 4번째 구획으로 세워 항등을 복원한다.
  // 완료 태스크는 current_elapsed_minutes가 없어 0으로 축퇴 → 3구획이 된다.
  const running = stats.is_running ? (stats.current_elapsed_minutes ?? 0) : 0;
  const parts = s.pm + s.worker + s.captain + running;
  // 호버 지표 — 전부 BE 라벨 직독. 3계열 라벨이 없는 응답은 2계열 라벨로 축퇴한다 (16-a)
  const pmLabel = stats.pm_label ?? stats.work_label;
  const workerLabel = s.measured ? (stats.worker_label ?? "—") : "미측정";
  const captainLabel = stats.captain_label ?? stats.wait_label;

  return (
    <section className="px-6 py-5 border-b" data-testid="block-a1">
      <BlockHeading
        code="A-1"
        title="진행 요약"
        extra={
          <QuietHoursBadge
            applied={stats.quiet_hours_applied}
            label={stats.quiet_hours_label}
          />
        }
        aside={
          stats.is_running
            ? `총 = PM + 워커 + ${ownerTerm} + 진행중`
            : `총 = PM + 워커 + ${ownerTerm}`
        }
      />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div
          className="rounded-lg border p-3"
          data-testid="a1-tile-total"
          data-minutes={stats.total_minutes}
        >
          <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
            총 리드타임
            {stats.is_running && (
              <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">
                진행 중
              </Badge>
            )}
          </div>
          <p className="text-2xl font-semibold tabular-nums leading-tight mt-0.5">
            {stats.total_label}
          </p>
          <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
            {stats.is_running
              ? `진행중 ${stats.current_elapsed_label} 포함`
              : `PM + 워커 + ${ownerTerm}`}
          </p>
        </div>

        <div
          className="rounded-lg border p-3"
          data-testid="a1-tile-pm"
          data-minutes={s.pm}
        >
          <p className="text-[11px] text-muted-foreground">PM</p>
          <p
            className="text-2xl font-semibold tabular-nums leading-tight mt-0.5"
            style={{ color: "var(--brand-primary)" }}
          >
            {stats.pm_label ?? stats.work_label}
          </p>
          <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
            디스패치 준비 · 게이트 검토
          </p>
        </div>

        {/* 워커 — 「0분」과 「미측정」을 구분한다 (worker_measured, 집계기준 16-a) */}
        <div
          className="rounded-lg border p-3"
          data-testid="a1-tile-worker"
          data-minutes={s.worker}
          data-measured={s.measured ? "true" : "false"}
          title={
            s.measured
              ? "서브에이전트 실제 실행 시간"
              : "워커 소요 미측정 — 그 몫 전액이 PM에 귀속된다 (집계기준 16-a)"
          }
        >
          <p className="text-[11px] text-muted-foreground">워커</p>
          <p
            className={cn(
              "text-2xl font-semibold tabular-nums leading-tight mt-0.5",
              !s.measured && "text-muted-foreground",
            )}
            style={s.measured ? { color: "var(--brand-secondary)" } : undefined}
          >
            {s.measured ? (stats.worker_label ?? "—") : "미측정"}
          </p>
          <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
            {s.measured ? "서브에이전트 실행" : "미기록 — PM에 귀속"}
          </p>
        </div>

        <div
          className="rounded-lg border p-3"
          data-testid="a1-tile-captain"
          data-minutes={s.captain}
          style={{
            borderColor:
              "color-mix(in oklab, var(--brand-tertiary) 40%, transparent)",
          }}
        >
          <p className="text-[11px] text-muted-foreground">{ownerTerm}</p>
          <p
            className="text-2xl font-semibold tabular-nums leading-tight mt-0.5"
            style={{ color: "var(--brand-tertiary)" }}
          >
            {`${stats.captain_label ?? stats.wait_label} (${stats.wait_ratio}%)`}
          </p>
          <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
            {ownerTerm} 확인 대기
          </p>
        </div>
      </div>

      {/* 총 구획 — 진행 중이면 PM·워커·캡틴·진행중 4구획, 완료면 진행중 0으로 3구획 축퇴 */}
      <TooltipProvider delayDuration={120}>
        <ChartTip
          tip={
            <>
              <p className="font-semibold">총 {stats.total_label}</p>
              <p>
                PM {pmLabel} · 워커 {workerLabel} · {ownerTerm}{" "}
                {captainLabel}
              </p>
              {stats.is_running && <p>진행중 {stats.current_elapsed_label}</p>}
              {!s.measured && <UnmeasuredNote />}
            </>
          }
        >
          <div
            data-testid="a1-strip"
            data-total-minutes={stats.total_minutes}
            data-parts-minutes={parts}
            tabIndex={0}
            className={cn(
              "flex h-3 rounded overflow-hidden bg-muted mt-3",
              SEG_FOCUS,
            )}
          >
            <ChartTip
              tip={
                <SeriesTip
                  scope="총 소요"
                  series="PM"
                  label={pmLabel}
                  pct={pctOf(s.pm, parts)}
                  foot={`총 ${stats.total_label}`}
                />
              }
            >
              <span
                data-testid="a1-seg-pm"
                data-minutes={s.pm}
                tabIndex={0}
                className={SEG_FOCUS}
                {...SEG_STOP}
                style={{
                  width: `${widthPct(s.pm, parts)}%`,
                  background: "var(--brand-primary)",
                }}
              />
            </ChartTip>
            <ChartTip
              tip={
                <>
                  <SeriesTip
                    scope="총 소요"
                    series="워커"
                    label={workerLabel}
                    pct={pctOf(s.worker, parts)}
                    foot={`총 ${stats.total_label}`}
                  />
                  {!s.measured && <UnmeasuredNote />}
                </>
              }
            >
              <span
                data-testid="a1-seg-worker"
                data-minutes={s.worker}
                tabIndex={0}
                className={SEG_FOCUS}
                {...SEG_STOP}
                style={{
                  width: `${widthPct(s.worker, parts)}%`,
                  background: "var(--brand-secondary)",
                }}
              />
            </ChartTip>
            <ChartTip
              tip={
                <SeriesTip
                  scope="총 소요"
                  series={ownerTerm}
                  label={captainLabel}
                  pct={pctOf(s.captain, parts)}
                  foot={`총 ${stats.total_label}`}
                />
              }
            >
              <span
                data-testid="a1-seg-captain"
                data-minutes={s.captain}
                tabIndex={0}
                className={SEG_FOCUS}
                {...SEG_STOP}
                style={{
                  width: `${widthPct(s.captain, parts)}%`,
                  background: "var(--brand-tertiary)",
                }}
              />
            </ChartTip>
            {stats.is_running && (
              <ChartTip
                tip={
                  <SeriesTip
                    scope="총 소요"
                    series="진행중"
                    label={stats.current_elapsed_label}
                    pct={pctOf(running, parts)}
                    foot={`총 ${stats.total_label}`}
                  />
                }
              >
                <span
                  data-testid="a1-seg-running"
                  data-minutes={running}
                  tabIndex={0}
                  className={SEG_FOCUS}
                  {...SEG_STOP}
                  style={{
                    width: `${widthPct(running, parts)}%`,
                    background: "var(--status-running)",
                  }}
                />
              </ChartTip>
            )}
          </div>
        </ChartTip>
      </TooltipProvider>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[11px] text-muted-foreground">
        <LegendDot color="var(--brand-primary)" label="PM" />
        <LegendDot color="var(--brand-secondary)" label="워커" />
        <LegendDot color="var(--brand-tertiary)" label={ownerTerm} />
        {stats.is_running && (
          <LegendDot color="var(--status-running)" label="진행중" />
        )}
        {!s.measured && (
          <span data-testid="a1-worker-unmeasured" className="font-mono">
            워커 미측정 — 그 몫은 PM에 귀속됩니다
          </span>
        )}
      </div>

      {/* 최장 단계 — 타일 4개를 총·PM·워커·캡틴에 내주고 메타 줄로 내린다 */}
      <div
        data-testid="a1-peak"
        className="flex flex-wrap items-baseline gap-x-2 mt-2 text-[11px] text-muted-foreground"
      >
        <span className="font-mono">최장 단계</span>
        <span className="font-mono font-semibold text-foreground break-words">
          {stats.peak_stage || "—"}
        </span>
        <span className="font-mono tabular-nums">{stats.peak_stage_label}</span>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* A-2 StageStackBars — 단계별 PM·워커·캡틴 3색 스택 (집계기준 16)        */
/* ------------------------------------------------------------------ */

function StageStackBars({
  pipeline,
  ownerTerm,
}: {
  pipeline: PipelineStageGroup[];
  ownerTerm: string;
}) {
  const maxMinutes = pipeline.reduce(
    (m, g) => (g.total_minutes > m ? g.total_minutes : m),
    0,
  );
  const peak = pipeline.find((g) => g.is_peak);
  const workerMeasured = pipeline.some((g) => g.worker_measured);

  return (
    <section className="px-6 py-5 border-b" data-testid="block-a2">
      <BlockHeading
        code="A-2"
        title="단계별 소요 시간"
        aside="행 timestamp 차분 합산"
      />
      <TooltipProvider delayDuration={120}>
        <div className="space-y-1.5">
          {pipeline.map((g) => {
            const s = seriesOf(g);
            const split = s.pm + s.worker + s.captain;
            const work = s.pm + s.worker; // 하위 호환 계열 — work == pm + worker
            // 호버 지표 — BE 라벨 직독. 라벨이 없는 옛 응답은 `—`로 축퇴한다 (P-7)
            const pmLabel = g.pm_label ?? "—";
            const workerLabel = s.measured ? (g.worker_label ?? "—") : "미측정";
            const captainLabel = g.captain_label ?? "—";
            return (
              <div
                key={g.stage}
                data-testid="a2-bar"
                data-stage={g.stage}
                data-peak={g.is_peak ? "true" : "false"}
                data-work-minutes={g.work_minutes}
                data-wait-minutes={g.wait_minutes}
                data-pm-minutes={s.pm}
                data-worker-minutes={s.worker}
                data-captain-minutes={s.captain}
                data-worker-measured={s.measured ? "true" : "false"}
                className="grid items-center gap-3"
                style={{ gridTemplateColumns: "124px 1fr 92px" }}
              >
                <span
                  className={cn(
                    "font-mono text-[11px] text-right whitespace-nowrap",
                    g.is_peak ? "font-semibold" : "text-muted-foreground",
                  )}
                >
                  {g.stage}
                </span>
                {/* 막대 전체 툴팁 — 워커 0폭(미측정)이라 구획 호버가 잡히지 않는 경우의 받침 */}
                <ChartTip
                  tip={
                    <>
                      <p className="font-semibold">
                        {g.stage} · 총 {g.total_label}
                      </p>
                      <p>
                        PM {pmLabel} · 워커 {workerLabel} · {ownerTerm}{" "}
                        {captainLabel}
                      </p>
                      {!s.measured && <UnmeasuredNote />}
                    </>
                  }
                >
                  <span
                    data-testid="a2-track"
                    tabIndex={0}
                    className={cn(
                      "block h-3.5 rounded bg-muted overflow-hidden",
                      SEG_FOCUS,
                    )}
                  >
                    <span
                      className="flex h-full rounded"
                      style={{
                        width: `${widthPct(g.total_minutes, maxMinutes)}%`,
                      }}
                    >
                      {/* 작업 구획(= PM + 워커)은 폭·기본색을 유지하고 내부만 2분할한다 —
                        워커 미기록이면 워커 폭 0으로 PM 단색이 되어 시각 회귀가 없다 (16-a) */}
                      <span
                        data-testid="a2-seg-work"
                        className="flex h-full"
                        style={{
                          width: `${widthPct(work, split)}%`,
                          background: "var(--brand-primary)",
                        }}
                      >
                        <ChartTip
                          tip={
                            <SeriesTip
                              scope={g.stage}
                              series="PM"
                              label={pmLabel}
                              pct={pctOf(s.pm, split)}
                              foot={`단계 총 ${g.total_label}`}
                            />
                          }
                        >
                          <span
                            data-testid="a2-seg-pm"
                            tabIndex={0}
                            className={SEG_FOCUS}
                            {...SEG_STOP}
                            style={{
                              width: `${widthPct(s.pm, work)}%`,
                              background: "var(--brand-primary)",
                            }}
                          />
                        </ChartTip>
                        <ChartTip
                          tip={
                            <>
                              <SeriesTip
                                scope={g.stage}
                                series="워커"
                                label={workerLabel}
                                pct={pctOf(s.worker, split)}
                                foot={`단계 총 ${g.total_label}`}
                              />
                              {!s.measured && <UnmeasuredNote />}
                            </>
                          }
                        >
                          <span
                            data-testid="a2-seg-worker"
                            tabIndex={0}
                            className={SEG_FOCUS}
                            {...SEG_STOP}
                            style={{
                              width: `${widthPct(s.worker, work)}%`,
                              background: "var(--brand-secondary)",
                            }}
                          />
                        </ChartTip>
                      </span>
                      <ChartTip
                        tip={
                          <SeriesTip
                            scope={g.stage}
                            series={ownerTerm}
                            label={captainLabel}
                            pct={pctOf(s.captain, split)}
                            foot={`단계 총 ${g.total_label}`}
                          />
                        }
                      >
                        <span
                          data-testid="a2-seg-wait"
                          tabIndex={0}
                          className={SEG_FOCUS}
                          {...SEG_STOP}
                          style={{
                            width: `${widthPct(s.captain, split)}%`,
                            background: "var(--brand-tertiary)",
                          }}
                        />
                      </ChartTip>
                    </span>
                  </span>
                </ChartTip>
                <span
                  className={cn(
                    "font-mono text-[11px] tabular-nums",
                    g.is_peak ? "font-semibold" : "text-muted-foreground",
                  )}
                >
                  {g.total_label}
                </span>
              </div>
            );
          })}
        </div>
      </TooltipProvider>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-[11px] text-muted-foreground">
        <LegendDot color="var(--brand-primary)" label="PM" />
        <LegendDot color="var(--brand-secondary)" label="워커" />
        <LegendDot color="var(--brand-tertiary)" label={ownerTerm} />
        {!workerMeasured && (
          <span data-testid="a2-worker-unmeasured" className="font-mono">
            워커 미측정 — 그 몫은 PM에 귀속됩니다
          </span>
        )}
        {peak && (
          <span>
            최장 단계는 {peak.stage} ({peak.total_label})입니다.
          </span>
        )}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* A-3 RowTimeline — 시각 오름차순 + 공백 구간 + 담당 라벨 동반           */
/* ------------------------------------------------------------------ */

function RowTimeline({
  rows,
  ownerTerm,
}: {
  rows: PipelineRow[];
  ownerTerm: string;
}) {
  return (
    <section className="px-6 py-5 border-b" data-testid="block-a3">
      <BlockHeading
        code="A-3"
        title="타임라인"
        aside={`${rows.length}개 행 · 공백 구간 표시`}
      />
      {/* 시각 거터 폭은 BE 라벨 `YY-MM-DD HH:mm:ss`(17자) 기준 — 축과 24px 간격 유지 */}
      <ol className="flex flex-col border-l-2 ml-[138px]">
        {rows.map((r) => (
          <React.Fragment key={r.row_id}>
            {r.series === "wait" && (
              <li
                data-testid="a3-gap"
                data-max-gap={r.is_max_gap ? "true" : "false"}
                className="ml-[18px] my-0.5 self-start inline-flex items-center gap-2 rounded-md px-2.5 py-1 font-mono text-[11px] tabular-nums"
                style={{
                  background:
                    "color-mix(in oklab, var(--brand-tertiary) 15%, transparent)",
                  color: "var(--brand-tertiary)",
                }}
              >
                <i
                  className="inline-block h-2 w-2 rounded-[2px]"
                  style={{ background: "var(--brand-tertiary)" }}
                />
                {`공백 ${r.duration_label} · ${ownerTerm} 확인 대기${r.is_max_gap ? " · 최대 공백" : ""}`}
              </li>
            )}
            <li data-testid="a3-item" className="relative py-1.5 pl-[18px]">
              <span
                className="absolute -left-[6px] top-3 h-2.5 w-2.5 rounded-full ring-2 ring-background"
                style={{ background: ownerColor(r.owner) }}
              />
              <span className="absolute -left-[138px] top-1.5 w-[114px] text-right font-mono text-[11px] text-muted-foreground tabular-nums">
                {r.time_label}
              </span>
              <div className="flex items-start justify-between gap-3">
                <span className="text-[13px]">
                  <span className="font-mono text-[11px] text-muted-foreground mr-2">
                    {r.stage}
                  </span>
                  {r.item}
                </span>
                <span className="font-mono text-[10px] text-muted-foreground shrink-0">
                  {r.owner_label}
                </span>
              </div>
            </li>
          </React.Fragment>
        ))}
      </ol>

      {/* 담당 구분은 색 단독이 아니라 라벨을 동반한다 (R-8 AC) */}
      <div className="flex flex-wrap gap-4 mt-4 text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5 font-mono">
          <i
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: "var(--brand-primary)" }}
          />
          PM
        </span>
        <span className="inline-flex items-center gap-1.5 font-mono">
          <i
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: "var(--brand-tertiary)" }}
          />
          {ownerTerm}
        </span>
        <span className="inline-flex items-center gap-1.5 font-mono">
          <i
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: "var(--brand-secondary)" }}
          />
          자동
        </span>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* A-4 RowDetailTable — 단계별 상세 표 (소요 작업·대기 2열 분리)          */
/* ------------------------------------------------------------------ */

function RowDetailTable({
  rows,
  stats,
}: {
  rows: PipelineRow[];
  stats: TaskStats;
}) {
  return (
    <section className="px-6 py-5" data-testid="block-a4">
      <BlockHeading
        code="A-4"
        title="단계별 상세"
        aside={
          stats.gate_recorded
            ? `게이트 ${stats.gate_count}건 · 블로커 ${stats.blocker_count}건`
            : "게이트 미기록"
        }
      />
      {/* [MUST] 가로 스크롤 격리 — 표는 자체 컨테이너 안에서만 가로 스크롤한다 */}
      <div
        data-testid="a4-scroll"
        className="overflow-x-auto rounded-lg border"
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs text-right w-10">#</TableHead>
              <TableHead className="text-xs">단계</TableHead>
              <TableHead className="text-xs">항목</TableHead>
              <TableHead className="text-xs w-20">상태</TableHead>
              <TableHead className="text-xs w-16">담당</TableHead>
              <TableHead className="text-xs text-right w-32">시각</TableHead>
              <TableHead className="text-xs text-right w-20">작업</TableHead>
              <TableHead className="text-xs text-right w-20">대기</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.row_id} data-testid="a4-row">
                <TableCell className="text-right text-xs font-mono tabular-nums">
                  {r.row_id}
                </TableCell>
                <TableCell className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                  {r.stage}
                </TableCell>
                <TableCell className="text-xs">
                  <span className="mr-1.5">{r.item}</span>
                  {r.gate && (
                    <Badge
                      data-testid="a4-gate"
                      variant="outline"
                      className="text-[9px] px-1 py-0 h-4 font-mono align-middle"
                    >
                      GATE
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-xs whitespace-nowrap">
                  <span
                    className={cn(
                      "inline-block h-1.5 w-1.5 rounded-full mr-1.5",
                      stageStatusClass(r.status),
                    )}
                  />
                  {rowStatusText(r.status)}
                </TableCell>
                <TableCell className="text-xs font-mono whitespace-nowrap">
                  {r.owner_label}
                </TableCell>
                <TableCell className="text-right text-xs font-mono tabular-nums whitespace-nowrap">
                  {r.time_label}
                </TableCell>
                <TableCell className="text-right text-xs font-mono tabular-nums">
                  {r.series === "work" ? r.duration_label : "—"}
                </TableCell>
                <TableCell
                  className="text-right text-xs font-mono tabular-nums"
                  style={
                    r.series === "wait"
                      ? { color: "var(--brand-tertiary)" }
                      : undefined
                  }
                >
                  {r.series === "wait" ? r.duration_label : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* KanbanCard                                                            */
/* ------------------------------------------------------------------ */

function KanbanCard({
  card,
  onClick,
}: {
  card: TaskCard;
  onClick: () => void;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer border-l-2 hover:bg-accent transition-colors select-none",
        "hover:-translate-y-px",
        columnBorderClass(card.column),
      )}
      // [MUST] 읽기 전용: drag 없음 — onClick만 처리
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      aria-label={`태스크 ${card.task_id} 상세 보기`}
    >
      <CardHeader className="p-3 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] font-mono text-muted-foreground leading-none mb-1">
              {card.task_id}
            </p>
            <p className="text-sm font-medium leading-tight line-clamp-2">
              {card.title}
            </p>
          </div>
          {card.column === "blocked" && (
            <AlertCircle className="h-4 w-4 shrink-0 text-status-blocked mt-0.5" />
          )}
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0 space-y-2">
        {/* 진행률 */}
        <div className="space-y-1">
          <Progress value={card.progress} className="h-1.5" />
          <p className="text-[10px] text-muted-foreground text-right tabular-nums">
            {card.progress}%
          </p>
        </div>

        {/* badge 행 */}
        <div className="flex flex-wrap items-center gap-1">
          {card.skill && (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
              {card.skill}
            </Badge>
          )}
          {card.mode && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5">
              {card.mode}
            </Badge>
          )}
          {card.current_stage && (
            <Badge
              variant="outline"
              className={cn(
                "text-[10px] px-1.5 py-0 h-5 ml-auto font-mono",
                card.column === "in_progress"
                  ? "border-status-running text-status-running"
                  : "text-muted-foreground",
              )}
            >
              {card.current_stage}
            </Badge>
          )}
        </div>

        {/* 메타 */}
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{card.updated_at || "—"}</span>
          {card.artifact_count > 0 && (
            <>
              <FileText className="h-3 w-3 ml-1" />
              <span>{card.artifact_count}</span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* KanbanColumn                                                          */
/* ------------------------------------------------------------------ */

function KanbanColumnView({
  col,
  cards,
  onCardClick,
}: {
  col: (typeof COLUMNS)[number];
  cards: TaskCard[];
  onCardClick: (card: TaskCard) => void;
}) {
  const Icon = col.icon;

  return (
    <div className="flex flex-col min-w-[220px] flex-1">
      {/* 컬럼 헤더 */}
      <div className="flex items-center gap-2 px-1 pb-3 shrink-0">
        <Icon className={cn("h-4 w-4", col.statusClass)} />
        <span className="text-sm font-medium">{col.label}</span>
        <Badge variant="secondary" className="ml-auto text-xs tabular-nums">
          {cards.length}
        </Badge>
      </div>

      {/* 카드 리스트 */}
      <ScrollArea className="flex-1">
        <div className="space-y-2 pr-1 pb-4">
          {cards.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground border border-dashed border-border rounded-lg">
              <Inbox className="h-6 w-6 opacity-40" />
              <p className="text-xs">
                {col.key === "archive" ? "아카이브 없음" : "태스크 없음"}
              </p>
            </div>
          ) : (
            cards.map((card) => (
              <KanbanCard
                key={card.task_id}
                card={card}
                onClick={() => onCardClick(card)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PipelineStepper — 가로 스테퍼                                        */
/* ------------------------------------------------------------------ */

function PipelineStepper({ pipeline }: { pipeline: PipelineStageGroup[] }) {
  if (pipeline.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">파이프라인 데이터 없음</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {pipeline.map((g, idx) => (
        <React.Fragment key={g.stage}>
          <div className="flex flex-col items-center gap-1">
            <div
              className={cn(
                "h-2.5 w-2.5 rounded-full shrink-0",
                stageStatusClass(g.status),
              )}
            />
            <span className="text-[10px] font-mono text-center leading-tight max-w-[56px] break-words">
              {g.stage}
            </span>
            <span className="text-[9px] text-muted-foreground tabular-nums">
              {g.done_count}/{g.total}
            </span>
          </div>
          {idx < pipeline.length - 1 && (
            <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0 mb-4" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ArtifactViewer — 산출물 탭 마크다운                                  */
/* ------------------------------------------------------------------ */

function ArtifactContent({
  taskId,
  project,
  artifactName,
}: {
  taskId: string;
  project: string;
  artifactName: string;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data, isLoading } = useQuery<{ content: string }>({
    queryKey: ["artifact", project, taskId, artifactName],
    queryFn: () =>
      apiClient<{ content: string }>(
        `/api/tasks/artifact?project=${encodeURIComponent(project)}&task_id=${encodeURIComponent(taskId)}&name=${encodeURIComponent(artifactName)}`,
      ),
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        {[...Array(10)].map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.content) {
    return (
      <p className="text-sm text-muted-foreground p-4">
        산출물을 불러올 수 없습니다
      </p>
    );
  }

  return (
    <div className="p-4">
      <MarkdownView content={data.content} />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TaskDrawer                                                            */
/* ------------------------------------------------------------------ */

function TaskDrawer({
  open,
  onClose,
  card,
  project,
}: {
  open: boolean;
  onClose: () => void;
  card: TaskCard | null;
  project: string;
}) {
  // query param 방식 — path segment에 절대경로 사용 시 FastAPI 매칭 실패 근본 수정
  const { data: detail, isLoading } = useQuery<TaskDetail>({
    queryKey: ["task-detail", project, card?.task_id],
    queryFn: () =>
      apiClient<TaskDetail>(
        `/api/tasks/detail?project=${encodeURIComponent(project)}&task_id=${encodeURIComponent(card!.task_id)}`,
      ),
    enabled: open && !!card,
    retry: 1,
  });

  // 표시 값 선택만 수행한다 — 시간 포맷은 BE 소유(P-7)
  const rows = detail ? flattenRows(detail.pipeline) : [];
  // 사용자 호칭은 BE `owner_term` 직독 — 구버전 캐시 응답(필드 부재)만 「사용자」로 받는다
  const ownerTerm = detail?.owner_term || "사용자";
  const periodLabel =
    rows.length > 0
      ? `${rows[0].time_label} → ${rows[rows.length - 1].time_label}`
      : "";
  const artifactItems: ArtifactItem[] = detail
    ? detail.artifact_items.length > 0
      ? detail.artifact_items
      : detail.artifacts.map((name) => ({
          name,
          type: "other",
          type_label: "기타",
        }))
    : [];
  const statsAvailable = !!detail?.stats?.available;

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-[min(72vw,1200px)] sm:max-w-[min(72vw,1200px)] p-0 flex flex-col h-full overflow-hidden"
      >
        {/* 고정 헤더 — 태스크 식별(ID·배지·기간). 탭 위에 고정 유지 (R-5 AC) */}
        <SheetHeader className="border-b px-6 py-4 shrink-0">
          <SheetTitle className="text-sm font-semibold leading-tight">
            {card?.task_id} — {card?.title}
          </SheetTitle>
          {/* Badge(div)를 담으므로 asChild로 <p> 중첩을 피한다 — 콘솔 경고 0건 (R-12 AC) */}
          <SheetDescription asChild>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-muted-foreground">
              {card?.skill && (
                <Badge variant="outline" className="text-[10px]">
                  {card.skill}
                </Badge>
              )}
              {card?.mode && (
                <Badge variant="secondary" className="text-[10px]">
                  {card.mode}
                </Badge>
              )}
              {detail?.current_status && (
                <Badge
                  variant="outline"
                  className="text-[10px]"
                  data-testid="sheet-status"
                >
                  {rowStatusText(detail.current_status)}
                </Badge>
              )}
              {periodLabel && (
                <Badge
                  variant="outline"
                  className="text-[10px] font-mono"
                  data-testid="sheet-period"
                >
                  {periodLabel}
                </Badge>
              )}
            </div>
          </SheetDescription>
        </SheetHeader>

        {/* 본문 — flex-1 + min-h-0 로 스크롤 컨테이너 구성 */}
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : detail ? (
            <Tabs
              defaultValue="stats"
              className="flex flex-1 flex-col min-h-0 overflow-hidden"
            >
              <div className="shrink-0 border-b px-6 pt-3 pb-2">
                <TabsList className="w-fit">
                  <TabsTrigger value="stats" className="text-xs gap-1.5">
                    <BarChart3 className="h-3.5 w-3.5" />
                    태스크 대시보드
                  </TabsTrigger>
                  <TabsTrigger value="artifacts" className="text-xs gap-1.5">
                    <FileText className="h-3.5 w-3.5" />
                    산출물
                    <Badge
                      variant="secondary"
                      className="text-[10px] px-1.5 py-0 h-4 tabular-nums"
                      data-testid="artifact-count-badge"
                    >
                      {detail.artifacts.length}
                    </Badge>
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* ===== 탭 1: 태스크 대시보드 — 자체 영역에서만 세로 스크롤 ===== */}
              <TabsContent
                value="stats"
                data-testid="tab-panel-stats"
                className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden mt-0"
              >
                {/* 파이프라인 스테퍼 */}
                <div className="px-6 py-4 border-b">
                  <p className="text-xs font-medium text-muted-foreground mb-3">
                    파이프라인 단계
                  </p>
                  <PipelineStepper pipeline={detail.pipeline} />
                </div>

                {statsAvailable && detail.stats ? (
                  <>
                    <StatsSummaryCards
                      stats={detail.stats}
                      ownerTerm={ownerTerm}
                    />
                    <StageStackBars
                      pipeline={detail.pipeline}
                      ownerTerm={ownerTerm}
                    />
                    <RowTimeline rows={rows} ownerTerm={ownerTerm} />
                    <RowDetailTable rows={rows} stats={detail.stats} />
                  </>
                ) : (
                  /* R-12 축소 표시 — FE는 자체 방어 로직을 갖지 않는다 */
                  <div className="px-6 py-5" data-testid="stats-empty">
                    <p className="text-sm text-muted-foreground">데이터 없음</p>
                  </div>
                )}
              </TabsContent>

              {/* ===== 탭 2: 산출물 — .md 전수, 유형 그룹 정렬 ===== */}
              <TabsContent
                value="artifacts"
                data-testid="tab-panel-artifacts"
                className="flex flex-1 flex-col min-h-0 overflow-hidden mt-0"
              >
                {artifactItems.length > 0 ? (
                  <Tabs
                    defaultValue={artifactItems[0].name}
                    className="flex flex-1 flex-col min-h-0 overflow-hidden px-6 pt-4"
                  >
                    {/* [MUST] 가로 스크롤 격리 — 탭 바 내부에서만 가로 스크롤 */}
                    <div
                      data-testid="artifact-tablist-scroll"
                      className="shrink-0 overflow-x-auto pb-1"
                    >
                      <TabsList className="h-auto w-max flex-nowrap gap-1">
                        {artifactItems.map((it, i) => (
                          <React.Fragment key={it.name}>
                            {(i === 0 ||
                              artifactItems[i - 1].type !== it.type) && (
                              <span
                                data-testid="artifact-type-label"
                                className="px-1.5 text-[10px] text-muted-foreground whitespace-nowrap select-none"
                              >
                                {it.type_label}
                              </span>
                            )}
                            <TabsTrigger
                              value={it.name}
                              className="text-xs font-mono whitespace-nowrap"
                            >
                              {it.name}
                            </TabsTrigger>
                          </React.Fragment>
                        ))}
                      </TabsList>
                    </div>
                    {artifactItems.map((it) => (
                      <TabsContent
                        key={it.name}
                        value={it.name}
                        className="flex-1 min-h-0 overflow-y-auto mt-3 border rounded-md"
                      >
                        <ArtifactContent
                          taskId={detail.task_id}
                          project={project}
                          artifactName={it.name}
                        />
                      </TabsContent>
                    ))}
                  </Tabs>
                ) : (
                  <div className="px-6 py-4">
                    <p className="text-sm text-muted-foreground">산출물 없음</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          ) : (
            <div className="p-6">
              <p className="text-sm text-muted-foreground">
                상세 정보를 불러올 수 없습니다
              </p>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/* ------------------------------------------------------------------ */
/* ProjectSelectGrid — 프로젝트 미선택 시 선택 그리드                    */
/* ------------------------------------------------------------------ */

interface ProjectInfo {
  name: string;
  path: string;
  is_opal: boolean;
}

function ProjectSelectGrid({ onSelect }: { onSelect: (path: string) => void }) {
  const { data: projects } = useQuery<ProjectInfo[]>({
    queryKey: ["projects"],
    queryFn: () => apiClient<ProjectInfo[]>("/api/projects"),
    retry: 1,
  });

  const opalProjects = (projects ?? []).filter((p) => p.is_opal);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6">
      <div className="text-center">
        <Inbox className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-40" />
        <p className="text-sm font-medium">프로젝트를 선택하세요</p>
        <p className="text-xs text-muted-foreground mt-1">
          칸반 보드는 단일 프로젝트 컨텍스트로 동작합니다
        </p>
      </div>
      {opalProjects.length > 0 && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 w-full max-w-lg">
          {opalProjects.map((p) => (
            <button
              key={p.path}
              className="flex flex-col items-start gap-1 rounded-lg border border-border p-3 text-left hover:bg-accent transition-colors"
              onClick={() => onSelect(p.path)}
            >
              <span className="text-sm font-medium truncate w-full">
                {p.name}
              </span>
              <Badge
                variant="default"
                className="text-[10px] bg-status-done/20 text-status-done border-status-done/30"
              >
                OPAL
              </Badge>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TasksPage — 루트 컴포넌트                                             */
/* ------------------------------------------------------------------ */

export function TasksPage() {
  // contextProject(ui-store)를 단일 소스로 구독 — 스위처 연동. searchParams는 딥링크용 보조.
  const [searchParams, setSearchParams] = useSearchParams();
  const { contextProject, setContextProject } = useUiStore();
  // 선택 우선순위: contextProject > searchParams?project (딥링크 진입 시 초기 동기)
  const projectParam = contextProject ?? searchParams.get("project");
  const [selectedCard, setSelectedCard] = useState<TaskCard | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const {
    data: tasks,
    isLoading,
    isError,
  } = useQuery<TaskCard[]>({
    queryKey: ["tasks", projectParam],
    queryFn: () =>
      apiClient<TaskCard[]>(
        projectParam
          ? `/api/tasks?project=${encodeURIComponent(projectParam)}`
          : "/api/tasks",
      ),
    enabled: !!projectParam,
    retry: 1,
  });

  const handleCardClick = (card: TaskCard) => {
    setSelectedCard(card);
    setDrawerOpen(true);
  };

  const handleProjectSelect = (path: string) => {
    // contextProject 전역 동기 → 프로젝트 화면 등도 따라가게
    setContextProject(path);
    setSearchParams({ project: path });
  };

  // 컬럼별 카드 그룹핑 (BE가 정렬해서 반환하므로 FE는 그룹핑만 수행)
  const grouped = COLUMNS.reduce(
    (acc, col) => {
      acc[col.key] = (tasks ?? []).filter((t) => t.column === col.key);
      return acc;
    },
    {} as Record<KanbanColumn, TaskCard[]>,
  );

  if (!projectParam) {
    return <ProjectSelectGrid onSelect={handleProjectSelect} />;
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center gap-3 border-b px-6 py-3 shrink-0">
        <h1 className="text-sm font-semibold">태스크 칸반</h1>
        <span className="text-xs text-muted-foreground font-medium truncate max-w-[240px]">
          {projectParam.split("/").filter(Boolean).pop()}
        </span>
        {/* [MUST] 읽기 전용 badge — 상시 표시 (S-8, C-2/C-6, WIREFRAME §4.4) */}
        <Badge
          variant="secondary"
          className="ml-auto flex items-center gap-1 shrink-0 text-xs text-muted-foreground"
        >
          <Lock className="h-3 w-3" />
          읽기 전용
        </Badge>
      </div>

      {/* 에러 */}
      {isError && (
        <div className="px-6 pt-4">
          <div className="flex items-center gap-2 rounded-md border border-status-blocked/30 bg-status-blocked/5 px-4 py-3">
            <AlertTriangle className="h-4 w-4 text-status-blocked shrink-0" />
            <p className="text-sm">
              API 연결 실패. opal-cli console start를 실행하세요.
            </p>
          </div>
        </div>
      )}

      {/* 칸반 보드 */}
      {isLoading ? (
        <div className="flex gap-4 p-6 overflow-x-auto">
          {COLUMNS.map((col) => (
            <div
              key={col.key}
              className="flex flex-col min-w-[220px] flex-1 space-y-2"
            >
              <Skeleton className="h-6 w-24" />
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-28 w-full" />
              ))}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-1 gap-4 p-6 overflow-x-auto overflow-y-hidden">
          {COLUMNS.map((col) => (
            <React.Fragment key={col.key}>
              <KanbanColumnView
                col={col}
                cards={grouped[col.key]}
                onCardClick={handleCardClick}
              />
              {col.key !== "archive" && (
                <Separator orientation="vertical" className="h-full" />
              )}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* 상세 Sheet (right 사이드 패널) */}
      <TaskDrawer
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCard(null);
        }}
        card={selectedCard}
        project={projectParam}
      />
    </div>
  );
}

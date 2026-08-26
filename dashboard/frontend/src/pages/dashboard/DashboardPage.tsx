/**
 * @header {
 *   "module": "dashboard-page",
 *   "layer": "page",
 *   "domain": "dashboard",
 *   "description": "대시보드 화면 — 4메트릭 section-cards + Recharts 활동추이(7d/30d/90d) + 단계분포 파이 + 주의알림 + 최근활동 테이블. [T103] 기존 5블록 아래에 횡단 통계 4블록 추가 — B-4 워크플로우 대조표(필터 진입점, 로컬 useState·API 재호출 0건) · B-1 요약 5타일 · B-2 단계별 PM·워커·캡틴 3색 스택(단계별 n= 표기) · B-3 태스크별 리드타임 스파크 컬럼(완료 태스크만). n<5는 「표본 부족」 배지. brain 위젯 제외(C-11). contextProject 스위처 연동으로 전체/개별 프로젝트 집계 전환. [T103/R-18] 소요 3계열(집계기준 16) — B-1에 3계열 구성 스트립, B-2 막대를 PM=var(--brand-primary)·워커=var(--brand-secondary)·캡틴=var(--brand-tertiary) 3색 스택으로 확장. 3계열 필드가 없는 응답은 seriesOf가 축퇴 16-a로 사상해 워커 0폭·PM=기존 작업 폭이 되어 시각 회귀가 없다. [MUST] 신규 색상은 CSS 변수 문자열 전달(var(--brand-*)) — hex 리터럴 금지. [MUST] FE 무계산 — 시간 표시 문자열은 BE *_label 직독(PLAN P-7). [T103/R-20] 구획 호버 툴팁 — 막대의 각 구획(PM·워커·캡틴, A-1은 진행중 포함)과 막대 전체가 Radix Tooltip 트리거(TooltipTrigger asChild)이며 tabIndex로 키보드 포커스에서도 뜬다. 구획은 SEG_STOP으로 포인터·포커스 전파를 끊어 상위 막대 툴팁이 겹쳐 열리지 않게 한다. 워커 미측정 태스크는 워커 구획이 0폭이라 호버가 잡히지 않으므로 막대 전체 툴팁이 3계열 요약과 「워커 미측정 — 그 몫은 PM에 귀속됩니다」를 대신 말한다(16-a). [MUST] 툴팁의 시간 문자열도 BE `*_label` 직독이며 분→시간 변환을 FE가 하지 않는다(P-7) — 비율(%)만 막대 폭 계산에 쓰는 값을 그대로 반올림한다. [T103/R-21] 야간 보정 배지 — BE 응답 최상위 `quiet_hours_applied`가 참일 때만 B-1 헤딩에 「야간 제외 {quiet_hours_label}」 배지를 세우고 Radix Tooltip으로 「매일 이 구간을 소요에서 제외합니다」를 덧붙인다. 거짓이면 렌더하지 않는다(보정 꺼짐 = 벽시계 그대로). [MUST] 구간 문자열은 BE 완성값 직독이며 FE가 시:분을 조립하지 않는다(P-7).",
 *   "exports": ["DashboardPage"],
 *   "depends": ["api-client", "card", "badge", "table", "skeleton", "toggle-group", "tooltip", "ui-store"],
 *   "task": "103",
 *   "changelog": [
 *     "2026-08-26 T103 R-21: B-1 헤딩에 야간 보정 배지 추가 — QuietHoursBadge 신설, BlockHeading에 extra 슬롯 추가, DashboardSummary 로컬 타입에 quiet_hours_applied·quiet_hours_label 동기. 타일·막대·색·레이아웃 무변경",
 *     "2026-08-25 T103 Step11: B-1~B-4 + 워크플로우 필터 추가 + 로컬 타입 동기(WorkflowStat·StageStat·TaskLeadtime). 기존 5블록·PIE_COLORS 무변경",
 *     "2026-08-26 T103 R-20: B-2 스택 막대 구획·B-3 태스크별 리드타임 막대에 호버 툴팁 추가 — ChartTip·SeriesTip·UnmeasuredNote·pctOf·SEG_STOP·SEG_FOCUS 신설, StageStat(누적 total_*·3계열 라벨)·TaskLeadtime(3계열 승계) 로컬 타입 동기. B-3의 native title 속성은 Radix 툴팁으로 대체(중복 표시 제거). 막대 폭·색 무변경. TS-134~TS-136",
 *     "2026-08-25 T103 R-18: B-1 3계열 구성 스트립 + B-2 3색 스택(작업 구획 내부 PM·워커 2분할) + seriesOf·LegendDot 신설. B-3·B-4·기존 5블록 무변경"
 *   ]
 * }
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useUiStore } from "@/store/ui-store";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  FolderKanban,
  Play,
  AlertTriangle,
  PlusCircle,
  Clock,
  AlertCircle,
  Moon,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface StatusDistribution {
  pending: number;
  in_progress: number;
  blocked: number;
  done: number;
}

interface ActivityPoint {
  date: string;
  count: number;
}

interface AlertItem {
  task_id: string;
  title: string;
  project: string;
  status: string;
  message: string;
}

interface RecentActivity {
  date: string;
  task_id: string;
  title: string;
  project: string;
  stage: string;
}

/** BE `StageStat` — 워크플로우 내 단계별 집계. 단계마다 모수(n)가 다르다 */
interface StageStat {
  stage: string;
  n: number;
  median_minutes: number;
  median_label: string;
  work_minutes: number;
  wait_minutes: number;
  is_peak: boolean;
  // 3계열 분해 (집계기준 16) — 3계열 이전 응답에는 없어 optional. 부재 시 축퇴 16-a
  pm_minutes?: number;
  worker_minutes?: number;
  captain_minutes?: number;
  worker_measured?: boolean;
  // 누적 총(= work + wait)과 3계열 표시 문자열 (R-20) — 구획 호버가 읽는다
  total_minutes?: number;
  total_label?: string;
  pm_label?: string;
  worker_label?: string;
  captain_label?: string;
}

/** BE `TaskLeadtime` — 완료 태스크만 (집계기준 3) */
interface TaskLeadtime {
  task_id: string;
  title: string;
  total_minutes: number;
  total_label: string;
  is_peak: boolean;
  // 3계열 승계 (R-20) — 태스크 막대 호버 지표. 라벨 부재 응답은 `—`로 축퇴
  pm_minutes?: number;
  worker_minutes?: number;
  captain_minutes?: number;
  pm_label?: string;
  worker_label?: string;
  captain_label?: string;
  worker_measured?: boolean;
}

/** BE `WorkflowStat` — skill 단위 횡단 집계 (집계기준 15: 원천 용어 skill) */
interface WorkflowStat {
  skill: string;
  n: number;
  sample_insufficient: boolean;
  median_minutes: number;
  median_label: string;
  mean_minutes: number;
  mean_label: string;
  work_minutes: number;
  wait_minutes: number;
  wait_ratio: number;
  // 3계열 분해 (집계기준 16) — 부재 시 축퇴 16-a로 읽는다
  pm_minutes?: number;
  worker_minutes?: number;
  captain_minutes?: number;
  worker_measured?: boolean;
  gate_count: number;
  blocker_count: number;
  stages: StageStat[];
  tasks: TaskLeadtime[];
}

interface DashboardSummary {
  total_projects: number;
  running_tasks: number;
  blockers: number;
  additional_work: number;
  status_distribution: StatusDistribution;
  activity_trend: ActivityPoint[];
  alerts: AlertItem[];
  recent_activities: RecentActivity[];
  completed_tasks: number;
  total_tasks: number;
  artifact_total: number;
  artifact_by_type: Record<string, number>;
  workflow_stats: WorkflowStat[];
  // 야간 보정 표면화 (집계기준 17) — 대시보드 배지 1개의 원천. 구간 문자열은 BE 완성값(P-7)
  owner_term?: string;
  quiet_hours_applied?: boolean;
  quiet_hours_label?: string;
}

/* ------------------------------------------------------------------ */
/* 상수 / 유틸                                                          */
/* ------------------------------------------------------------------ */

type Period = "7d" | "30d" | "90d";

const PERIOD_DAYS: Record<Period, number> = { "7d": 7, "30d": 30, "90d": 90 };

/** 상태 분포 파이 색상 */
const PIE_STATUS_KEYS = [
  { key: "done", label: "완료" },
  { key: "in_progress", label: "진행중" },
  { key: "blocked", label: "블로킹" },
  { key: "pending", label: "대기" },
];

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "대기",
    in_progress: "진행중",
    blocked: "블로킹",
    done: "완료",
  };
  return map[status] ?? status;
}

/* ------------------------------------------------------------------ */
/* SectionCards — 4개 메트릭                                           */
/* ------------------------------------------------------------------ */

interface MetricCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  highlight?: "warn" | "blocked";
}

function MetricCard({ title, value, icon: Icon, description, highlight }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon
          className={cn(
            "h-4 w-4",
            highlight === "blocked" && "text-status-blocked",
            highlight === "warn" && "text-status-stale",
            !highlight && "text-muted-foreground",
          )}
        />
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "text-2xl font-bold tabular-nums",
            highlight === "blocked" && "text-status-blocked",
            highlight === "warn" && "text-status-stale",
          )}
        >
          {value}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* ActivityChart — Recharts AreaChart (7d/30d/90d toggle)             */
/* ------------------------------------------------------------------ */

function ActivityChart({ data, period, onPeriodChange }: {
  data: ActivityPoint[];
  period: Period;
  onPeriodChange: (p: Period) => void;
}) {
  const days = PERIOD_DAYS[period];
  // 최근 N일만
  const sliced = data.slice(-days);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm font-medium">태스크 활동 추이</CardTitle>
          <CardDescription className="text-xs">최근 {days}일 활동</CardDescription>
        </div>
        <ToggleGroup
          type="single"
          value={period}
          onValueChange={(v) => v && onPeriodChange(v as Period)}
          className="h-7"
        >
          {(["7d", "30d", "90d"] as Period[]).map((p) => (
            <ToggleGroupItem key={p} value={p} className="h-7 px-2 text-xs">
              {p}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={sliced} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="actGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--brand-primary)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="var(--brand-primary)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <RechartsTooltip
              contentStyle={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="var(--brand-primary)"
              strokeWidth={1.5}
              fill="url(#actGrad)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* StatusPieChart — 단계 분포 파이                                      */
/* ------------------------------------------------------------------ */

const PIE_COLORS = [
  "oklch(0.56 0.13 152)",  // done — status-done
  "oklch(0.60 0.19 245)",  // in_progress — status-running
  "oklch(0.60 0.20 20)",   // blocked — status-blocked
  "oklch(0.65 0.04 215)",  // pending — status-todo
];

function StatusPieChart({ dist }: { dist: StatusDistribution }) {
  const total = dist.pending + dist.in_progress + dist.blocked + dist.done;
  const pieData = PIE_STATUS_KEYS.map((s, i) => ({
    name: s.label,
    value: dist[s.key as keyof StatusDistribution],
    color: PIE_COLORS[i],
  })).filter((d) => d.value > 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">단계 분포</CardTitle>
        <CardDescription className="text-xs">전체 태스크 {total}개</CardDescription>
      </CardHeader>
      <CardContent className="flex items-center justify-center">
        {total === 0 ? (
          <p className="text-sm text-muted-foreground py-8">데이터 없음</p>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={65}
                paddingAngle={2}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
              <Legend
                iconSize={8}
                iconType="circle"
                formatter={(value) => (
                  <span style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{value}</span>
                )}
              />
              <RechartsTooltip
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* AlertList — 주의 알림                                                */
/* ------------------------------------------------------------------ */

function AlertList({ alerts }: { alerts: AlertItem[] }) {
  if (alerts.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            주의 알림
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground py-2">알림 없음 — 모든 태스크가 정상입니다.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-status-stale" />
          주의 알림
          <Badge variant="secondary" className="ml-auto text-xs">
            {alerts.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ul className="divide-y divide-border">
          {alerts.map((alert) => (
            <li key={`${alert.project}-${alert.task_id}`} className="flex items-start gap-3 px-6 py-3">
              <span
                className={cn(
                  "mt-1 h-2 w-2 shrink-0 rounded-full",
                  alert.status === "blocked" ? "bg-status-blocked" : "bg-status-stale",
                )}
              />
              <div className="min-w-0">
                <p className="text-sm font-medium leading-tight truncate">
                  [{alert.project}] {alert.task_id} — {alert.title}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">{alert.message}</p>
              </div>
              <Badge
                variant={alert.status === "blocked" ? "destructive" : "secondary"}
                className="ml-auto shrink-0 text-xs"
              >
                {statusLabel(alert.status)}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* RecentTable — 최근 활동 data-table                                  */
/* ------------------------------------------------------------------ */

function RecentTable({ activities }: { activities: RecentActivity[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          최근 활동
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {/* [T103] 표는 자체 컨테이너에서만 가로 스크롤한다 — 없으면 넓은 표가
            페이지 전체를 밀어내 뷰포트 오른쪽이 잘린다(TASK.md §제약 「가로 스크롤 격리」). */}
        <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs w-32 whitespace-nowrap">일자</TableHead>
              <TableHead className="text-xs w-32">프로젝트</TableHead>
              <TableHead className="text-xs w-72">태스크 ID</TableHead>
              <TableHead className="text-xs">제목</TableHead>
              <TableHead className="text-xs w-28">단계</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {activities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-sm text-muted-foreground py-8">
                  최근 활동 없음
                </TableCell>
              </TableRow>
            ) : (
              activities.slice(0, 20).map((act, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs text-muted-foreground font-mono whitespace-nowrap">
                    {act.date}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground truncate max-w-[8rem]">
                    {act.project}
                  </TableCell>
                  <TableCell className="text-xs font-mono text-brand-primary">
                    {act.task_id}
                  </TableCell>
                  <TableCell className="text-xs truncate max-w-[16rem]">
                    {act.title}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs font-mono">
                      {act.stage}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* 통계 블록 공통 — 헤딩 · 막대 폭 기하                                   */
/* ------------------------------------------------------------------ */

/** 막대 폭·높이 기하 — 표시 문자열이 아니라 *_minutes에서 파생한다 (PLAN P-7 근거 3) */
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
 * 「대기」 전액이 캡틴이다. 계산이 아니라 2계열↔3계열 계약 사상이다.
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
      <i className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}

function sizePct(part: number, whole: number) {
  return whole > 0 ? (part / whole) * 100 : 0;
}

/* ------------------------------------------------------------------ */
/* 구획 호버 툴팁 (R-20) — 조회 전용                                      */
/* 시간 문자열은 BE `*_label` 직독이며 FE는 분→시간 변환을 하지 않는다(P-7). */
/* ------------------------------------------------------------------ */

/** 구획 비율(%) — 막대 폭 계산에 쓰는 값 그대로다. 시간 문자열이 아니므로 라벨 대상이 아니다 */
function pctOf(part: number, whole: number) {
  return Math.round(sizePct(part, whole));
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
function ChartTip({ tip, children }: { tip: React.ReactNode; children: React.ReactElement }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent className="font-mono text-[11px] leading-5">{tip}</TooltipContent>
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
          background: "color-mix(in oklab, var(--brand-primary) 15%, transparent)",
          color: "var(--brand-primary)",
        }}
      >
        {code}
      </span>
      <span className="text-[13px] font-semibold">{title}</span>
      {extra}
      {aside && (
        <span className="font-mono text-[11px] text-muted-foreground ml-auto">{aside}</span>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 야간 보정 배지 — BE `quiet_hours_*` 직독 (집계기준 17)                  */
/* 구간 문자열은 BE가 완성해 내린다 — FE는 조립하지 않는다 (P-7)           */
/* ------------------------------------------------------------------ */

function QuietHoursBadge({ applied, label }: { applied?: boolean; label?: string }) {
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
/* B-4 WorkflowFilter — 워크플로우 대조표 겸 필터 진입점                  */
/* ------------------------------------------------------------------ */

function WorkflowFilter({
  workflows,
  selected,
  onSelect,
}: {
  workflows: WorkflowStat[];
  selected: string;
  onSelect: (skill: string) => void;
}) {
  return (
    <Card data-testid="block-b4">
      <CardContent className="p-5">
        <BlockHeading code="B-4" title="워크플로우 대조" aside="선택 시 B-1~B-3이 좁혀집니다" />
        <ToggleGroup
          type="single"
          value={selected}
          onValueChange={(v) => v && onSelect(v)}
          className="flex flex-wrap justify-start gap-2"
        >
          {workflows.map((w) => (
            <ToggleGroupItem
              key={w.skill}
              value={w.skill}
              data-testid="b4-option"
              className="h-auto flex-col items-start gap-1 rounded-lg border px-3 py-2 data-[state=on]:border-primary"
            >
              <span className="flex items-center gap-1.5">
                <span className="font-mono text-xs font-semibold">{w.skill}</span>
                <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
                  n={w.n}
                </span>
                {w.sample_insufficient && (
                  <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">
                    표본 부족
                  </Badge>
                )}
              </span>
              <span className="font-mono text-[11px] tabular-nums">{w.median_label}</span>
              <span className="font-mono text-[10px] tabular-nums" style={{ color: "var(--brand-tertiary)" }}>
                대기 {w.wait_ratio}%
              </span>
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* B-1 WorkflowSummaryCards — 요약 5타일 + 소요 3계열 구성 스트립          */
/* ------------------------------------------------------------------ */

function WorkflowSummaryCards({
  stat,
  ownerTerm,
  completedTasks,
  totalTasks,
  artifactTotal,
  artifactByType,
  quietApplied,
  quietLabel,
}: {
  stat: WorkflowStat;
  ownerTerm: string;
  completedTasks: number;
  totalTasks: number;
  artifactTotal: number;
  artifactByType: Record<string, number>;
  quietApplied?: boolean;
  quietLabel?: string;
}) {
  const typeSummary = Object.entries(artifactByType)
    .map(([k, v]) => `${k} ${v}`)
    .join(" · ");
  // 워크플로우 코호트 누적 소요의 3계열 구성 (집계기준 16). WorkflowStat에는 계열별
  // 표시 라벨이 없으므로 수치 문자열을 만들지 않고 비율만 스트립으로 드러낸다.
  const s = seriesOf(stat);
  const parts = s.pm + s.worker + s.captain;

  return (
    <section data-testid="block-b1">
      <BlockHeading
        code="B-1"
        title="태스크 통계 요약"
        extra={<QuietHoursBadge applied={quietApplied} label={quietLabel} />}
        aside={`선택 워크플로우 ${stat.skill}`}
      />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5 [&>*]:min-w-0">
        <Card>
          <CardContent className="p-4">
            <p className="text-[11px] text-muted-foreground">완료 태스크</p>
            <p className="text-2xl font-semibold tabular-nums leading-tight mt-0.5">
              {`${completedTasks} / ${totalTasks}`}
            </p>
            <p className="font-mono text-[10px] text-muted-foreground mt-0.5">완료 / 전체</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
              리드타임 중앙값
              {stat.sample_insufficient && (
                <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">
                  표본 부족
                </Badge>
              )}
            </div>
            <p className="text-2xl font-semibold tabular-nums leading-tight mt-0.5">
              {stat.median_label}
            </p>
            <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
              평균 {stat.mean_label}
            </p>
          </CardContent>
        </Card>

        <Card style={{ borderColor: "color-mix(in oklab, var(--brand-tertiary) 40%, transparent)" }}>
          <CardContent className="p-4">
            <p className="text-[11px] text-muted-foreground">{ownerTerm} 확인 대기 비중</p>
            <p
              className="text-2xl font-semibold tabular-nums leading-tight mt-0.5"
              style={{ color: "var(--brand-tertiary)" }}
            >
              {`${stat.wait_ratio}%`}
            </p>
            <p className="font-mono text-[10px] text-muted-foreground mt-0.5">모수 n={stat.n}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-[11px] text-muted-foreground">게이트 통과</p>
            <p className="text-2xl font-semibold tabular-nums leading-tight mt-0.5">
              {stat.gate_count}
            </p>
            <p className="font-mono text-[10px] text-muted-foreground mt-0.5">
              블로커 {stat.blocker_count}건
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-[11px] text-muted-foreground">산출물</p>
            <p className="text-2xl font-semibold tabular-nums leading-tight mt-0.5">
              {artifactTotal}
              <span className="text-sm font-medium text-muted-foreground ml-1">md</span>
            </p>
            <p className="font-mono text-[10px] text-muted-foreground mt-0.5 truncate">
              {typeSummary}
            </p>
          </CardContent>
        </Card>
      </div>

      <div
        data-testid="b1-strip"
        data-pm-minutes={s.pm}
        data-worker-minutes={s.worker}
        data-captain-minutes={s.captain}
        data-worker-measured={s.measured ? "true" : "false"}
        className="flex h-3 rounded overflow-hidden bg-muted mt-3"
      >
        <span
          data-testid="b1-seg-pm"
          style={{ width: `${sizePct(s.pm, parts)}%`, background: "var(--brand-primary)" }}
        />
        <span
          data-testid="b1-seg-worker"
          style={{ width: `${sizePct(s.worker, parts)}%`, background: "var(--brand-secondary)" }}
        />
        <span
          data-testid="b1-seg-captain"
          style={{ width: `${sizePct(s.captain, parts)}%`, background: "var(--brand-tertiary)" }}
        />
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[11px] text-muted-foreground">
        <LegendDot color="var(--brand-primary)" label="PM" />
        <LegendDot color="var(--brand-secondary)" label="워커" />
        <LegendDot color="var(--brand-tertiary)" label={ownerTerm} />
        {!s.measured && (
          <span data-testid="b1-worker-unmeasured" className="font-mono">
            워커 미측정 — 그 몫은 PM에 귀속됩니다
          </span>
        )}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* B-2 WorkflowStageBars — 단계별 PM·워커·캡틴 3색 스택 + 단계별 n= 표기   */
/* ------------------------------------------------------------------ */

function WorkflowStageBars({ stat, ownerTerm }: { stat: WorkflowStat; ownerTerm: string }) {
  const maxMinutes = stat.stages.reduce(
    (m, st) => (st.work_minutes + st.wait_minutes > m ? st.work_minutes + st.wait_minutes : m),
    0,
  );
  const peak = stat.stages.find((st) => st.is_peak);
  const workerMeasured = stat.stages.some((st) => st.worker_measured);

  return (
    <Card data-testid="block-b2">
      <CardContent className="p-5">
        <BlockHeading
          code="B-2"
          title="단계별 소요 — 어디가 병목인가"
          aside="막대 = 누적 작업·대기 · 값 = 중앙값"
        />
        <TooltipProvider delayDuration={120}>
        <div className="space-y-1.5">
          {stat.stages.map((st) => {
            const s = seriesOf(st);
            const split = s.pm + s.worker + s.captain;
            const work = s.pm + s.worker;   // 하위 호환 계열 — work == pm + worker
            // 호버 지표 — BE 라벨 직독. 라벨이 없는 옛 응답은 `—`로 축퇴한다 (P-7)
            const scope = `${st.stage} n=${st.n}`;
            const totalLabel = st.total_label ?? "—";
            const pmLabel = st.pm_label ?? "—";
            const workerLabel = s.measured ? st.worker_label ?? "—" : "미측정";
            const captainLabel = st.captain_label ?? "—";
            return (
              <div
                key={st.stage}
                data-testid="b2-bar"
                data-stage={st.stage}
                data-peak={st.is_peak ? "true" : "false"}
                data-pm-minutes={s.pm}
                data-worker-minutes={s.worker}
                data-captain-minutes={s.captain}
                data-worker-measured={s.measured ? "true" : "false"}
                className="grid items-center gap-3"
                style={{ gridTemplateColumns: "152px 1fr 100px" }}
              >
                <span
                  className={cn(
                    "font-mono text-[11px] text-right whitespace-nowrap",
                    st.is_peak ? "font-semibold" : "text-muted-foreground",
                  )}
                >
                  {`${st.stage} n=${st.n}`}
                </span>
                {/* 막대 전체 툴팁 — 워커 0폭(미측정)이라 구획 호버가 잡히지 않는 경우의 받침 */}
                <ChartTip
                  tip={
                    <>
                      <p className="font-semibold">{scope}</p>
                      <p>누적 {totalLabel} · 중앙값 {st.median_label}</p>
                      <p>
                        PM {pmLabel} · 워커 {workerLabel} · {ownerTerm} {captainLabel}
                      </p>
                      {!s.measured && <UnmeasuredNote />}
                    </>
                  }
                >
                  <span
                    data-testid="b2-track"
                    tabIndex={0}
                    className={cn("block h-3.5 rounded bg-muted overflow-hidden", SEG_FOCUS)}
                  >
                    <span
                      className="flex h-full rounded"
                      style={{ width: `${sizePct(split, maxMinutes)}%` }}
                    >
                      {/* 작업 구획(= PM + 워커)은 폭·기본색을 유지하고 내부만 2분할한다 —
                          워커 미기록이면 워커 폭 0으로 PM 단색이 되어 시각 회귀가 없다 (16-a) */}
                      <span
                        data-testid="b2-seg-work"
                        className="flex h-full"
                        style={{
                          width: `${sizePct(work, split)}%`,
                          background: "var(--brand-primary)",
                        }}
                      >
                        <ChartTip
                          tip={
                            <SeriesTip
                              scope={scope}
                              series="PM"
                              label={pmLabel}
                              pct={pctOf(s.pm, split)}
                              foot={`단계 총 ${totalLabel}`}
                            />
                          }
                        >
                          <span
                            data-testid="b2-seg-pm"
                            tabIndex={0}
                            className={SEG_FOCUS}
                            {...SEG_STOP}
                            style={{
                              width: `${sizePct(s.pm, work)}%`,
                              background: "var(--brand-primary)",
                            }}
                          />
                        </ChartTip>
                        <ChartTip
                          tip={
                            <>
                              <SeriesTip
                                scope={scope}
                                series="워커"
                                label={workerLabel}
                                pct={pctOf(s.worker, split)}
                                foot={`단계 총 ${totalLabel}`}
                              />
                              {!s.measured && <UnmeasuredNote />}
                            </>
                          }
                        >
                          <span
                            data-testid="b2-seg-worker"
                            tabIndex={0}
                            className={SEG_FOCUS}
                            {...SEG_STOP}
                            style={{
                              width: `${sizePct(s.worker, work)}%`,
                              background: "var(--brand-secondary)",
                            }}
                          />
                        </ChartTip>
                      </span>
                      <ChartTip
                        tip={
                          <SeriesTip
                            scope={scope}
                            series={ownerTerm}
                            label={captainLabel}
                            pct={pctOf(s.captain, split)}
                            foot={`단계 총 ${totalLabel}`}
                          />
                        }
                      >
                        <span
                          data-testid="b2-seg-wait"
                          tabIndex={0}
                          className={SEG_FOCUS}
                          {...SEG_STOP}
                          style={{
                            width: `${sizePct(s.captain, split)}%`,
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
                    st.is_peak ? "font-semibold" : "text-muted-foreground",
                  )}
                >
                  {st.median_label}
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
            <span data-testid="b2-worker-unmeasured" className="font-mono">
              워커 미측정 — 그 몫은 PM에 귀속됩니다
            </span>
          )}
          {peak && <span>{stat.skill} 워크플로우의 최장 단계는 {peak.stage}입니다.</span>}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* B-3 TaskLeadtimeChart — 태스크별 리드타임 스파크 컬럼 (완료 태스크만)  */
/* ------------------------------------------------------------------ */

function TaskLeadtimeChart({ stat, ownerTerm }: { stat: WorkflowStat; ownerTerm: string }) {
  const tasks = stat.tasks.slice().sort((a, b) => a.task_id.localeCompare(b.task_id));
  const maxMinutes = tasks.reduce((m, t) => (t.total_minutes > m ? t.total_minutes : m), 0);
  const shortest = tasks.reduce<TaskLeadtime | null>(
    (acc, t) => (acc === null || t.total_minutes < acc.total_minutes ? t : acc),
    null,
  );
  const longest = tasks.find((t) => t.is_peak) ?? null;

  return (
    <Card data-testid="block-b3">
      <CardContent className="p-5">
        <BlockHeading code="B-3" title="태스크별 리드타임" aside="막대 = 총 소요 · 완료 태스크만" />
        <TooltipProvider delayDuration={120}>
        <div className="flex items-end gap-1.5 h-32 overflow-x-auto">
          {tasks.map((t) => {
            // 호버 지표 — BE 라벨 직독. 라벨이 없는 옛 응답은 `—`로 축퇴한다 (P-7)
            const measured = t.worker_measured ?? false;
            return (
            <ChartTip
              key={t.task_id}
              tip={
                <>
                  <p className="font-semibold">{t.task_id}</p>
                  <p>총 {t.total_label}</p>
                  <p>
                    PM {t.pm_label ?? "—"} · 워커{" "}
                    {measured ? t.worker_label ?? "—" : "미측정"} · {ownerTerm}{" "}
                    {t.captain_label ?? "—"}
                  </p>
                  {!measured && <UnmeasuredNote />}
                </>
              }
            >
              <div
                data-testid="b3-column"
                data-task-id={t.task_id}
                tabIndex={0}
                className={cn(
                  "flex flex-col items-center justify-end gap-1 h-full min-w-[24px] flex-1",
                  SEG_FOCUS,
                )}
              >
                <span
                  className="block w-full rounded-t"
                  style={{
                    height: `${sizePct(t.total_minutes, maxMinutes)}%`,
                    background: t.is_peak ? "var(--brand-secondary)" : "var(--brand-primary)",
                    opacity: t.is_peak ? 1 : 0.45,
                  }}
                />
                <span className="font-mono text-[9.5px] text-muted-foreground">
                  {t.task_id.slice(0, 3)}
                </span>
              </div>
            </ChartTip>
            );
          })}
        </div>
        </TooltipProvider>

        <div className="flex justify-between font-mono text-[10.5px] text-muted-foreground border-t pt-2 mt-2">
          <span>{shortest ? `최단 ${shortest.total_label} · ${shortest.task_id.slice(0, 3)}` : "—"}</span>
          <span>{longest ? `최장 ${longest.total_label} · ${longest.task_id.slice(0, 3)}` : "—"}</span>
        </div>

        <div className="flex flex-wrap gap-4 mt-3 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1.5 font-mono">
            <i
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ background: "var(--brand-secondary)" }}
            />
            최장
          </span>
          <span className="inline-flex items-center gap-1.5 font-mono">
            <i
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ background: "var(--brand-primary)", opacity: 0.45 }}
            />
            그 외
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* DashboardPage — 루트 컴포넌트                                         */
/* ------------------------------------------------------------------ */

export function DashboardPage() {
  const [period, setPeriod] = useState<Period>("30d");
  // B-4 워크플로우 필터 — 로컬 상태. ui-store 미사용, API 재호출 없음 (ANALYSIS §8 확정값)
  const [skill, setSkill] = useState<string>("");
  const { contextProject } = useUiStore();

  const apiUrl = contextProject
    ? `/api/dashboard?project=${encodeURIComponent(contextProject)}`
    : "/api/dashboard";

  const { data, isLoading, isError } = useQuery<DashboardSummary>({
    queryKey: ["dashboard", contextProject ?? "ALL"],
    queryFn: () => apiClient<DashboardSummary>(apiUrl),
    retry: 1,
  });

  // 페이지 제목/서브텍스트 — 프로젝트 basename 사용
  const projectLabel = contextProject
    ? contextProject.split("/").filter(Boolean).at(-1) ?? contextProject
    : null;

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <h1 className="text-xl font-semibold">대시보드</h1>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-52" />
          <Skeleton className="h-52" />
        </div>
        <Skeleton className="h-40" />
        <Skeleton className="h-60" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <h1 className="text-xl font-semibold">대시보드</h1>
        <Card className="border-status-blocked/30">
          <CardContent className="flex items-center gap-3 py-6">
            <AlertTriangle className="h-5 w-5 text-status-blocked shrink-0" />
            <div>
              <p className="text-sm font-medium">API 연결 실패</p>
              <p className="text-xs text-muted-foreground">
                opal-cli console start 명령으로 데몬을 기동하세요.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 필터는 응답 객체에서 키를 고르는 동작이다 — 재호출 0건
  // [T103] 사용자 호칭 — BE가 ~/.opal/identity.md owner_name을 읽어 내리고,
  // 부재·파싱 실패 시 "사용자"로 폴백한다. FE에서 한 번 더 감싸 구버전 캐시 응답에도 대비한다.
  const ownerTerm = data.owner_term || "사용자";
  const workflows = data.workflow_stats ?? [];
  const selectedStat = workflows.find((w) => w.skill === skill) ?? workflows[0] ?? null;

  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">대시보드</h1>
        <span className="text-xs text-muted-foreground">
          {projectLabel ? projectLabel : "전체 프로젝트"}
        </span>
      </div>

      {/* section-cards 4메트릭 */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          title="OPAL 프로젝트"
          value={data.total_projects}
          icon={FolderKanban}
          description={projectLabel ? projectLabel : undefined}
        />
        <MetricCard
          title="진행중 태스크"
          value={data.running_tasks}
          icon={Play}
          description="현재 진행 중"
        />
        <MetricCard
          title="블로커"
          value={data.blockers}
          icon={AlertTriangle}
          highlight={data.blockers > 0 ? "blocked" : undefined}
          description={data.blockers > 0 ? "즉시 확인 필요" : undefined}
        />
        <MetricCard
          title="추가 작업"
          value={data.additional_work}
          icon={PlusCircle}
          highlight={data.additional_work > 0 ? "warn" : undefined}
        />
      </div>

      {/* 차트 영역 */}
      <div className="grid gap-4 md:grid-cols-[1fr_280px]">
        <ActivityChart
          data={data.activity_trend}
          period={period}
          onPeriodChange={setPeriod}
        />
        <StatusPieChart dist={data.status_distribution} />
      </div>

      {/* 주의 알림 */}
      <AlertList alerts={data.alerts} />

      {/* 최근 활동 */}
      <RecentTable activities={data.recent_activities} />

      {/* ===== 횡단 통계 B-1~B-4 — 기존 5블록 아래 ===== */}
      {workflows.length > 0 && selectedStat ? (
        <>
          <WorkflowFilter
            workflows={workflows}
            selected={selectedStat.skill}
            onSelect={setSkill}
          />
          <WorkflowSummaryCards
            stat={selectedStat}
            completedTasks={data.completed_tasks}
            totalTasks={data.total_tasks}
            artifactTotal={data.artifact_total}
            artifactByType={data.artifact_by_type}
            ownerTerm={ownerTerm}
            quietApplied={data.quiet_hours_applied}
            quietLabel={data.quiet_hours_label}
          />
          <WorkflowStageBars stat={selectedStat} ownerTerm={ownerTerm} />
          <TaskLeadtimeChart stat={selectedStat} ownerTerm={ownerTerm} />
        </>
      ) : (
        /* R-12 축소 표시 */
        <Card data-testid="workflow-stats-empty">
          <CardContent className="py-6">
            <p className="text-sm text-muted-foreground">데이터 없음</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

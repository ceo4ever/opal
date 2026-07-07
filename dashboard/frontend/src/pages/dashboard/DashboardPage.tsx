/**
 * @header {
 *   "module": "dashboard-page",
 *   "layer": "page",
 *   "domain": "dashboard",
 *   "description": "대시보드 화면 — 4메트릭 section-cards + Recharts 활동추이(7d/30d/90d) + 단계분포 파이 + 주의알림 + 최근활동 테이블. brain 위젯 제외(C-11). contextProject 스위처 연동으로 전체/개별 프로젝트 집계 전환.",
 *   "exports": ["DashboardPage"],
 *   "depends": ["api-client", "card", "badge", "table", "skeleton", "toggle-group", "ui-store"]
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

interface DashboardSummary {
  total_projects: number;
  running_tasks: number;
  blockers: number;
  additional_work: number;
  status_distribution: StatusDistribution;
  activity_trend: ActivityPoint[];
  alerts: AlertItem[];
  recent_activities: RecentActivity[];
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
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* DashboardPage — 루트 컴포넌트                                         */
/* ------------------------------------------------------------------ */

export function DashboardPage() {
  const [period, setPeriod] = useState<Period>("30d");
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
    </div>
  );
}

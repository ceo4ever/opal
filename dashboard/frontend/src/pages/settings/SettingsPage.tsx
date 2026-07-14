/**
 * @header {
 *   "module": "settings-page",
 *   "layer": "page",
 *   "domain": "settings",
 *   "description": "OPAL Console 설정 화면(T061 신설, T061 추가작업에서 범위 축소) — 프라임 풀 토글 단일 섹션: contextProject 대상 선프라임 ON/OFF Switch(GET /api/config로 상태 로드, POST /api/config/prewarm으로 변경 후 invalidateQueries 재조회) + 현재 prewarm_projects 목록 읽기 전용 표시 + console.config.json·프로젝트 로컬 설정(setting.local.json)은 파일 직접 편집으로 관리한다는 안내 문구. console.config 전반 관리·프로젝트 로컬 설정 편집 섹션 및 그 쓰기 API(POST /api/config/console, GET/POST /api/config/project-local)는 캡틴 지시로 제거되었다(후속 태스크에서 기능 단위 회수 예정).",
 *   "exports": ["SettingsPage"],
 *   "depends": ["api-client", "ui-store", "card", "switch", "label", "separator", "alert", "badge", "skeleton"],
 *   "task": "061",
 *   "changelog": [
 *     "2026-07-14 T061 Step9: 설정 화면 신설 — 3섹션 폼(프라임 토글·console.config·프로젝트 로컬 설정) + 5 API 연동 (F-005)",
 *     "2026-07-14 T061 추가작업(캡틴 범위 축소): console.config 전반 관리·프로젝트 로컬 설정 섹션 및 해당 쓰기 API 호출 제거 — 프라임 풀 토글 단일 섹션 + prewarm_projects 읽기 전용 목록 + 파일 직접 편집 안내 문구로 축소"
 *   ]
 * }
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Settings2, Zap, XCircle } from "lucide-react";
import { useUiStore } from "@/store/ui-store";
import { apiClient } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface ConsoleConfig {
  scan_roots: string[];
  scan_depth: number;
  exclude: string[];
  prewarm_projects: string[];
}

interface ConfigWriteResponse {
  ok: boolean;
  config: Record<string, unknown>;
}

/* ------------------------------------------------------------------ */
/* 유틸                                                                  */
/* ------------------------------------------------------------------ */

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "알 수 없는 오류가 발생했습니다.";
}

function SaveFailureAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
      <XCircle className="h-4 w-4" />
      <AlertTitle className="text-sm">저장 실패</AlertTitle>
      <AlertDescription className="text-xs">{message}</AlertDescription>
    </Alert>
  );
}

/* ------------------------------------------------------------------ */
/* Section: 프라임 풀 토글                                               */
/* ------------------------------------------------------------------ */

function PrimePoolSection({
  contextProject,
  config,
  isLoading,
}: {
  contextProject: string | null;
  config: ConsoleConfig | undefined;
  isLoading: boolean;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const toggleMutation = useMutation<
    ConfigWriteResponse,
    Error,
    { project: string; enabled: boolean }
  >({
    mutationFn: (body) =>
      apiClient<ConfigWriteResponse>("/api/config/prewarm", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["config"] });
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const enabled = !!(contextProject && config?.prewarm_projects.includes(contextProject));

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Zap className="h-4 w-4 text-muted-foreground" />
          프라임 풀 토글
        </CardTitle>
        <CardDescription>
          선택한 프로젝트의 브레인 세션을 미리 준비(prewarm)해 첫 질의 응답 지연을 줄입니다.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {!contextProject ? (
          <p className="text-sm text-muted-foreground">
            좌측 상단 프로젝트 스위처에서 프로젝트를 선택하세요.
          </p>
        ) : isLoading ? (
          <Skeleton className="h-9 w-48" />
        ) : (
          <div className="flex items-center gap-3">
            <Switch
              checked={enabled}
              disabled={toggleMutation.isPending}
              onCheckedChange={(checked) => {
                setError(null);
                toggleMutation.mutate({ project: contextProject, enabled: checked });
              }}
              aria-label="프라임 풀 토글"
            />
            <Label className="text-sm font-normal">
              {enabled ? "선프라임 활성화됨" : "선프라임 비활성화됨"}
            </Label>
          </div>
        )}
        {error && <SaveFailureAlert message={error} />}

        <Separator />

        <div className="flex flex-col gap-1.5">
          <Label className="text-xs text-muted-foreground">현재 선프라임 등록 프로젝트</Label>
          {isLoading ? (
            <Skeleton className="h-6 w-64" />
          ) : config && config.prewarm_projects.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {config.prewarm_projects.map((p) => (
                <Badge key={p} variant="outline" className="text-xs font-mono">
                  {p}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">등록된 프로젝트가 없습니다.</p>
          )}
        </div>

        <p className="text-xs text-muted-foreground">
          console.config.json·프로젝트 로컬 설정(setting.local.json)은 파일을 직접 편집해 관리합니다.
        </p>
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* SettingsPage — 루트 컴포넌트                                          */
/* ------------------------------------------------------------------ */

export function SettingsPage() {
  const contextProject = useUiStore((s) => s.contextProject);

  const {
    data: config,
    isLoading: configLoading,
    isError: configError,
  } = useQuery<ConsoleConfig>({
    queryKey: ["config"],
    queryFn: () => apiClient<ConsoleConfig>("/api/config"),
    retry: 1,
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-6 overflow-auto">
      <div className="flex items-center gap-3">
        <Settings2 className="h-5 w-5 text-muted-foreground" />
        <h1 className="text-sm font-semibold">설정</h1>
      </div>

      {configError && (
        <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
          <XCircle className="h-4 w-4" />
          <AlertTitle className="text-sm">API 연결 실패</AlertTitle>
          <AlertDescription className="text-xs">
            opal-cli console start 명령으로 데몬을 기동하세요.
          </AlertDescription>
        </Alert>
      )}

      <PrimePoolSection
        contextProject={contextProject}
        config={config}
        isLoading={configLoading}
      />
    </div>
  );
}

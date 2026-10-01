/**
 * @header {
 *   "module": "brain-legacy-gate",
 *   "layer": "page",
 *   "domain": "brain",
 *   "description": "구형 Brain 게이트(D-19) — GET /api/brain/legacy({enabled, running_turns})로 상태를 읽어, 꺼짐이면 children(대화 UI)을 마운트하지 않아 prime·status·query 호출이 0회인 첫 진입 화면(새 Brain 출시 전까지 사용 불가·업그레이드로 기본 꺼짐 안내·구형 경로 위험 3종·위험 확인 체크박스와 '구형 Brain 켜기' 버튼(체크 전 비활성)·'새 경로 출시를 기다린다' 선택지)을 보인다. 켜기는 POST /api/brain/legacy {enabled:true, risk_acknowledged:true}, 끄기는 {enabled:false, risk_acknowledged:false}. 켜진 뒤에는 legacy 배지와 '구형 Brain 끄기' 버튼 아래 children을 보이고, 끈 직후 응답 running_turns가 1 이상이면 '진행 중인 N개 질의는 끝까지 진행됩니다'를 표시한다.",
 *   "exports": ["BrainLegacyGate", "BRAIN_LEGACY_QUERY_KEY"],
 *   "depends": ["api-client", "button", "alert", "badge", "skeleton"],
 *   "task": "172"
 * }
 */

import { useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, MessageCircleQuestion, ShieldAlert } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

/* eslint-disable-next-line react-refresh/only-export-components */
export const BRAIN_LEGACY_QUERY_KEY = ["brain", "legacy"] as const;

interface BrainLegacyState {
  enabled: boolean;
  running_turns: number;
}

function postLegacy(enabled: boolean): Promise<BrainLegacyState> {
  return apiClient<BrainLegacyState>("/api/brain/legacy", {
    method: "POST",
    body: JSON.stringify({ enabled, risk_acknowledged: enabled }),
  });
}

export function BrainLegacyGate({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [acknowledged, setAcknowledged] = useState(false);
  const [offNotice, setOffNotice] = useState<number>(0);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery<BrainLegacyState>({
    queryKey: BRAIN_LEGACY_QUERY_KEY,
    queryFn: () => apiClient<BrainLegacyState>("/api/brain/legacy"),
    retry: 1,
  });

  const toggle = useMutation<BrainLegacyState, Error, boolean>({
    mutationFn: postLegacy,
    onSuccess: (res, enabled) => {
      setActionError(null);
      setOffNotice(enabled ? 0 : res.running_turns);
      if (!enabled) setAcknowledged(false);
      queryClient.setQueryData(BRAIN_LEGACY_QUERY_KEY, res);
    },
    onError: (err) => setActionError(err.message),
  });

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle className="text-sm">API 연결 실패</AlertTitle>
          <AlertDescription className="text-xs">
            opal-cli console start 명령으로 데몬을 기동하세요.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!data.enabled) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6 overflow-auto">
        <div className="flex items-center gap-3">
          <MessageCircleQuestion className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-sm font-semibold">프로젝트 브레인</h1>
        </div>

        {offNotice >= 1 && (
          <Alert className="border-status-stale/30 bg-status-stale/5">
            <AlertCircle className="h-4 w-4 text-status-stale" />
            <AlertDescription className="text-xs">
              진행 중인 {offNotice}개 질의는 끝까지 진행됩니다.
            </AlertDescription>
          </Alert>
        )}

        <Alert className="border-status-stale/30 bg-status-stale/5">
          <ShieldAlert className="h-4 w-4 text-status-stale" />
          <AlertTitle className="text-sm">새 Brain 출시 전까지 이 화면은 잠겨 있습니다</AlertTitle>
          <AlertDescription className="flex flex-col gap-2 text-xs mt-1">
            <p>Brain은 기본적으로 사용할 수 없는 상태입니다.</p>
            <p>이번 업그레이드로 구형 Brain이 기본 꺼짐으로 바뀌었습니다.</p>
            <p>구형 경로를 켜면 다음 위험을 감수해야 합니다.</p>
            <ul className="list-disc pl-5">
              <li>파일 읽기 범위가 제한되지 않습니다.</li>
              <li>임의 Bash 명령이 실행될 수 있습니다.</li>
              <li>네트워크를 통해 내용이 외부로 유출될 수 있습니다.</li>
            </ul>
          </AlertDescription>
        </Alert>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            className="mt-0.5"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
          />
          <span>위 위험을 모두 이해했으며 감수합니다.</span>
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="sm"
            variant="destructive"
            disabled={!acknowledged || toggle.isPending}
            onClick={() => toggle.mutate(true)}
          >
            구형 Brain 켜기
          </Button>
          <span className="text-xs text-muted-foreground">
            새 경로 출시를 기다린다 — 아무 동작도 하지 않고 그대로 두면 됩니다.
          </span>
        </div>

        {actionError && (
          <Alert variant="destructive" className="border-status-blocked/50 bg-status-blocked/5">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">{actionError}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 border-b shrink-0">
        <Badge variant="outline" className="text-[10px] border-status-stale/50 text-status-stale">
          legacy
        </Badge>
        <Button
          size="sm"
          variant="outline"
          className="ml-auto"
          disabled={toggle.isPending}
          onClick={() => toggle.mutate(false)}
        >
          구형 Brain 끄기
        </Button>
        {actionError && <span className="text-xs text-status-blocked">{actionError}</span>}
      </div>
      {children}
    </div>
  );
}

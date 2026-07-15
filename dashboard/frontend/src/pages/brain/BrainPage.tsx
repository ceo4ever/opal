/**
 * @header {
 *   "module": "brain-page",
 *   "layer": "page",
 *   "domain": "brain",
 *   "description": "프로젝트 브레인 화면 — 인증 분기(GET /api/brain/auth) + 프로젝트 필수 게이팅(미선택 시 폼 비활성·안내) + 단일 휘발성 세션(FE가 mount마다 crypto.randomUUID()로 session_id 발급 — 이력 비영속, 재오픈/새로고침마다 새 세션) + 자동 prime(POST /api/brain/prime {project, session_id}) + 상태 폴링(GET /api/brain/status?project=<절대경로>&session_id=<id>, 2초 간격, TanStack Query key에 project+session_id 포함) + 연동 상태 배지(priming/ready/error/idle) + 질문 게이팅(state≠ready면 disabled) + 멀티턴(동일 session_id로 연속 질의 — BE --resume 웜 재개) + 질의(POST /api/brain/query {question,project,session_id}) + 낙관적 턴(제출 즉시 pending→done/error 갱신, 캡처 session_id 귀속 가드 — 세션 전환 중 잡 완료 시 폐기) + 답변/인용 렌더 + '새 대화' 클릭 시 turns 초기화+새 session_id 발급+즉시 재prime. localStorage 미사용(비영속, R-2) — 단일 대화창(사이드바 없음). [T063 R-8] 이탈 가드 — turns.length>0일 때: ①콘솔 메뉴 전환은 react-router useBlocker(pathname 변경만 감지)로 가로채 AlertDialog 확인 ②브라우저 새로고침·탭 닫기는 beforeunload에서 preventDefault ③프로젝트 스위처 전환은 ui-store brainDirty 플래그로 노출해 AppShell이 가로챔(본 파일은 turns.length 변화·언마운트 시 brainDirty를 동기화만 함) ④'새 대화' 버튼은 handleNewSessionClick이 turns.length>0이면 pendingNewSession AlertDialog로 확인 후 handleNewSession 실행(라우트 이탈이 아니므로 useBlocker와 무관, 독립 상태로 처리) — turns=0이면 확인 없이 즉시 실행(기존 동작 불변).",
 *   "exports": ["BrainPage", "addPendingTurn", "resolvePendingTurn", "makeSessionId", "projectDisplayName", "jobResponseToResolution", "jobPollingInterval", "BrainJobResponse", "BrainState", "BrainTurn", "BRAIN_LEAVE_GUARD_TITLE", "BRAIN_LEAVE_GUARD_DESCRIPTION"],
 *   "depends": ["api-client", "textarea", "button", "alert", "alert-dialog", "badge", "skeleton", "markdown-view", "ui-store"],
 *   "task": "063",
 *   "changelog": [
 *     "2026-07-15 T063 R-8: useBlocker(콘솔 메뉴 전환) + beforeunload(새로고침·탭 닫기) + ui-store brainDirty 동기화(프로젝트 스위처 가드용) 추가 — turns.length>0에서만 활성",
 *     "2026-07-15 T063 R-8 후속(4번째 경로): '새 대화' 버튼에 pendingNewSession AlertDialog 확인 추가 — handleNewSessionClick이 turns>0이면 확인 후 handleNewSession, turns=0이면 즉시 실행(현행 유지). useBlocker와 독립",
 *     "2026-07-15 T063 CLOSE: @header exports 정합 — BrainState·BrainTurn·BRAIN_LEAVE_GUARD_TITLE·BRAIN_LEAVE_GUARD_DESCRIPTION 누락 4건 반영(코드 변경 없음)"
 *   ]
 * }
 */

import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, useBlocker } from "react-router-dom";
import {
  MessageCircleQuestion,
  Plus,
  Send,
  AlertCircle,
  Clock,
  BookOpen,
  RefreshCw,
  CheckCircle2,
  Loader2,
  FolderOpen,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useUiStore } from "@/store/ui-store";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownView } from "@/components/markdown-view";

/** 3경로 공통 이탈 확인 문구 (R-8) — AppShell 프로젝트 스위처 가드와 동일 문구 유지 */
export const BRAIN_LEAVE_GUARD_TITLE = "화면을 나가면 이 대화 세션이 사라집니다";
export const BRAIN_LEAVE_GUARD_DESCRIPTION = "나가시겠어요?";

/* ------------------------------------------------------------------ */
/* 타입                                                                  */
/* ------------------------------------------------------------------ */

interface BrainAuthResponse {
  authenticated: boolean;
  cli_available: boolean;
  message: string;
}

export type BrainState = "idle" | "priming" | "ready" | "error";

interface BrainStatusResponse {
  state: BrainState;
  session_active: boolean;
  message: string;
}

interface CitationItem {
  page: string;
  title: string;
  type: string;
  score?: number;
}

// === 잡 폴링 헬퍼 (태스크 037) ===
export interface BrainJobResponse {
  job_id: string;
  status: "pending" | "done" | "error";
  answer: string;
  citations: CitationItem[];
  error_msg: string;
}

export function jobResponseToResolution(
  job: BrainJobResponse,
):
  | { status: "done"; answer: string; citations: CitationItem[] }
  | { status: "error"; errorMsg: string }
  | null {
  if (job.status === "done")
    return { status: "done", answer: job.answer, citations: job.citations };
  if (job.status === "error")
    return { status: "error", errorMsg: job.error_msg || "요청 처리 중 오류가 발생했습니다" };
  return null;
}

export function jobPollingInterval(status: string | undefined): number | false {
  return status === "done" || status === "error" ? false : 2000;
}

/* 단일 세션 turns[] 상태 (태스크 063 — 휘발성, localStorage 없음) */
export interface BrainTurn {
  q: string;
  a: string;
  citations: CitationItem[];
  ts: number; // Date.now()
  status: "pending" | "done" | "error"; // 낙관적 업데이트 상태
  errorMsg?: string; // status="error" 시 에러 메시지
}

/* ------------------------------------------------------------------ */
/* 세션·턴 헬퍼 (태스크 063 — 단일 turns[] 기반)                          */
/* ------------------------------------------------------------------ */

/** mount·"새 대화"마다 새 세션 ID 발급 (R-3, R-5) */
export function makeSessionId(): string {
  return crypto.randomUUID();
}

/**
 * 낙관적 pending 턴을 turns 배열에 추가한다 (제출 즉시 호출).
 * status="pending", a="", citations=[] 로 초기화된다.
 */
export function addPendingTurn(turns: BrainTurn[], question: string): BrainTurn[] {
  const pendingTurn: BrainTurn = {
    q: question,
    a: "",
    citations: [],
    ts: Date.now(),
    status: "pending",
  };
  return [...turns, pendingTurn];
}

/**
 * turns 배열의 마지막 pending 턴을 답변/에러로 갱신한다 (onSuccess/onError 시 호출).
 * 세션 전환 오귀속 가드는 호출측(capturedSessionIdRef)이 담당한다.
 */
export function resolvePendingTurn(
  turns: BrainTurn[],
  resolution:
    | { status: "done"; answer: string; citations: CitationItem[] }
    | { status: "error"; errorMsg: string },
): BrainTurn[] {
  const lastPendingIdx = [...turns].map((t, i) => ({ t, i }))
    .filter(({ t }) => t.status === "pending")
    .pop()?.i ?? -1;

  if (lastPendingIdx === -1) return turns; // pending 턴 없음 → 변경 없음

  return turns.map((turn, i) => {
    if (i !== lastPendingIdx) return turn;
    if (resolution.status === "done") {
      return {
        ...turn,
        a: resolution.answer,
        citations: resolution.citations,
        status: "done" as const,
      };
    }
    return {
      ...turn,
      status: "error" as const,
      errorMsg: resolution.errorMsg,
    };
  });
}

/** 프로젝트 절대 경로에서 표시용 짧은 이름을 추출한다 */
export function projectDisplayName(project: string | null): string | null {
  if (!project) return null;
  return project.split("/").filter(Boolean).pop() ?? project;
}

/* ------------------------------------------------------------------ */
/* CitationList                                                          */
/* ------------------------------------------------------------------ */

function CitationList({ citations }: { citations: CitationItem[] }) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {citations.map((c, i) => (
        <Badge
          key={i}
          variant="outline"
          className="text-xs gap-1 cursor-default max-w-xs truncate"
          title={`${c.page} (${c.type})`}
        >
          <BookOpen className="h-2.5 w-2.5 shrink-0" />
          <span className="truncate">{c.title || c.page}</span>
          <span className="text-muted-foreground shrink-0">[{c.type}]</span>
          {c.score != null && (
            <span className="text-muted-foreground shrink-0">
              {c.score.toFixed(2)}
            </span>
          )}
        </Badge>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TurnTrigger — 아코디온 헤더 (질문 + 시각 + 상태 아이콘)              */
/* ------------------------------------------------------------------ */

function TurnTrigger({ turn, index }: { turn: BrainTurn; index: number }) {
  const ts = new Date(turn.ts);
  const timeStr = ts.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="flex flex-1 items-center gap-2 min-w-0 pr-2">
      {/* Q번호 */}
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
        Q{index + 1}
      </span>
      {/* 질문 텍스트 — 트리거가 깨지지 않도록 truncate */}
      <span className="flex-1 text-sm font-medium text-left truncate">
        {turn.q}
      </span>
      {/* 우측: 시각 + 상태 아이콘 */}
      <span className="shrink-0 flex items-center gap-1.5 text-[10px] text-muted-foreground">
        <Clock className="h-2.5 w-2.5" />
        {timeStr}
        {turn.status === "pending" && (
          <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
        )}
        {turn.status === "error" && (
          <AlertCircle className="h-3 w-3 text-destructive" />
        )}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* TurnContent — 아코디온 본문 (답변 영역)                               */
/* ------------------------------------------------------------------ */

function TurnContent({ turn }: { turn: BrainTurn }) {
  return (
    <div className="pt-1 pb-2">
      {turn.status === "pending" && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin shrink-0" />
            <span>답변 대기中…</span>
          </div>
          <Skeleton className="h-3.5 w-3/4" />
          <Skeleton className="h-3.5 w-1/2" />
          <Skeleton className="h-3.5 w-5/6" />
        </div>
      )}
      {turn.status === "error" && (
        <div className="flex items-start gap-2 text-[11px] text-destructive">
          <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{turn.errorMsg ?? "질의 실패 — 다시 시도하세요."}</span>
        </div>
      )}
      {turn.status === "done" && (
        <>
          <MarkdownView content={turn.a} className="text-sm" />
          <CitationList citations={turn.citations} />
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* BrainPage                                                             */
/* ------------------------------------------------------------------ */

export function BrainPage() {
  const [searchParams] = useSearchParams();
  const contextProject = useUiStore((s) => s.contextProject);
  const setBrainDirty = useUiStore((s) => s.setBrainDirty);
  const project = contextProject ?? searchParams.get("project") ?? null;
  const queryClient = useQueryClient();

  // 선택된 프로젝트의 표시용 짧은 이름
  const projName = projectDisplayName(project);

  /* ---------- 세션 상태 (휘발성 — mount마다 새 세션 발급, R-3) ---------- */
  const [sessionId, setSessionId] = useState<string>(() => makeSessionId());

  /* ---------- 대화 턴 상태 (인메모리 전용 — localStorage 없음, R-2) ---------- */
  const [turns, setTurns] = useState<BrainTurn[]>([]);

  /* ---------- 이탈 가드 (R-8) — turns.length>0일 때만 활성, 3경로 동일 문구 ---------- */
  const hasUnsavedTurns = turns.length > 0;

  // ① 콘솔 메뉴 전환(라우트 pathname 변경)만 가로챈다 — 같은 경로 내 쿼리 변경(스위처의 searchParams 갱신 등)은 차단하지 않는다
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      hasUnsavedTurns && currentLocation.pathname !== nextLocation.pathname,
  );

  // ② 브라우저 새로고침·탭 닫기 — turns=0이면 preventDefault를 스킵(리스너는 상시 등록, no-op)
  useEffect(() => {
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      if (!hasUnsavedTurns) return;
      e.preventDefault();
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedTurns]);

  // ③ 프로젝트 스위처 전환 — ui-store에 dirty 상태를 노출해 AppShell이 가로채도록 한다. 언마운트 시 false로 복원.
  useEffect(() => {
    setBrainDirty(hasUnsavedTurns);
  }, [hasUnsavedTurns, setBrainDirty]);

  useEffect(() => {
    return () => setBrainDirty(false);
  }, [setBrainDirty]);

  // ④ "새 대화" 버튼 — 화면 내 액션(라우트 이탈 아님, useBlocker와 무관). 확인 대기 상태만 별도 관리.
  const [pendingNewSession, setPendingNewSession] = useState(false);

  /* ---------- 잡 폴링 상태 ---------- */
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  /* ---------- API: query (잡 제출 — 비동기) ---------- */
  // 캡처된 sessionId를 ref로 추적 — mutation 시작 시점의 sessionId를 캡처한다.
  // 잡 폴링 done/error 시 이 값을 사용해 현재 세션과 다르면(= 그사이 "새 대화"로 전환됨) 폐기한다.
  const capturedSessionIdRef = useRef<string | null>(null);

  const submitMutation = useMutation<
    { job_id: string },
    Error,
    { question: string; session_id: string }
  >({
    mutationFn: ({ question: q, session_id }) =>
      apiClient<{ job_id: string }>("/api/brain/query", {
        method: "POST",
        body: JSON.stringify({ question: q, project, session_id }),
        timeoutMs: 30000,
      }),
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
    },
    onError: (error) => {
      // 세션 전환 가드: 제출 이후 "새 대화"로 전환됐다면 이 에러는 폐기한다.
      if (capturedSessionIdRef.current !== sessionId) return;
      const errMsg = error?.message ?? "알 수 없는 오류가 발생했습니다.";
      setTurns((prev) => resolvePendingTurn(prev, { status: "error", errorMsg: errMsg }));
    },
  });

  /* ---------- 질문 입력 ---------- */
  const [question, setQuestion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  /* ---------- API: auth ---------- */
  const {
    data: authData,
    isLoading: authLoading,
    isError: authError,
  } = useQuery<BrainAuthResponse>({
    queryKey: ["brain-auth"],
    queryFn: () => apiClient<BrainAuthResponse>("/api/brain/auth"),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  /* ---------- API: prime ---------- */
  const primeMutation = useMutation<
    { priming: boolean },
    Error,
    { session_id: string }
  >({
    mutationFn: ({ session_id }) =>
      apiClient<{ priming: boolean }>("/api/brain/prime", {
        method: "POST",
        body: JSON.stringify({ project, session_id }),
      }),
    // 결과 무시, 에러도 조용히
  });

  /* ---------- API: status 폴링 (project + session_id 포함) ---------- */
  const {
    data: statusData,
    refetch: refetchStatus,
  } = useQuery<BrainStatusResponse>({
    // project + session_id를 query key에 포함 → 세션 전환 시 자동 재폴링
    queryKey: ["brain-status", project, sessionId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (project) params.set("project", project);
      params.set("session_id", sessionId);
      return apiClient<BrainStatusResponse>(`/api/brain/status?${params.toString()}`);
    },
    // 인증 완료 + 프로젝트 선택 시에만 폴링 (session_id는 mount 시 상시 발급됨)
    enabled: !!authData?.authenticated && project !== null,
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      // ready 또는 error 상태면 폴링 중단
      if (state === "ready" || state === "error") return false;
      return 2_000;
    },
    staleTime: 1_000,
    retry: 1,
  });

  const brainState: BrainState = statusData?.state ?? "idle";
  const isReady = brainState === "ready";

  /* 인증 완료 + 프로젝트 선택 시 → 현재 세션 prime (mount마다 1회, R-3) */
  const primedSessionRef = useRef<string | null>(null); // 이미 prime된 session_id 추적
  useEffect(() => {
    if (!authData?.authenticated || project === null) return;
    // 이미 prime한 세션은 skip
    if (primedSessionRef.current === sessionId) return;
    primedSessionRef.current = sessionId;
    primeMutation.mutate({ session_id: sessionId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authData?.authenticated, project, sessionId]);

  /* idle 상태 감지 시 현재 세션 재프라임 트리거 */
  useEffect(() => {
    if (brainState === "idle" && authData?.authenticated && project !== null) {
      primeMutation.mutate({ session_id: sessionId });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brainState]);

  /* ---------- 재시도 핸들러 ---------- */
  function handleRetryPrime() {
    primedSessionRef.current = null;
    primeMutation.mutate({ session_id: sessionId });
    void refetchStatus();
  }

  /* ---------- API: 잡 폴링 ---------- */
  const { data: jobData } = useQuery<BrainJobResponse>({
    queryKey: ["brain-job", project, sessionId, activeJobId],
    enabled: activeJobId !== null,
    queryFn: () => {
      const params = new URLSearchParams();
      if (project) params.set("project", project);
      params.set("session_id", sessionId);
      return apiClient<BrainJobResponse>(`/api/brain/job/${activeJobId}?${params.toString()}`, {
        timeoutMs: 30000,
      });
    },
    refetchInterval: (q) => jobPollingInterval(q.state.data?.status),
    staleTime: 0,
    retry: 1,
  });

  /* 잡 폴링 결과 처리 — done/error 시 턴 갱신 */
  useEffect(() => {
    if (!jobData) return;
    const resolution = jobResponseToResolution(jobData);
    if (resolution === null) return;

    // 세션 전환 가드: 이 잡이 캡처된 세션과 다른 세션에 도착했다면 폐기 (H-6)
    if (capturedSessionIdRef.current !== sessionId) return;

    setTurns((prev) => resolvePendingTurn(prev, resolution));
    setActiveJobId(null);
    if (resolution.status === "done") {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- 비동기 잡 폴링 결과(외부 시스템) 반영 시 입력창 초기화, 렌더 중 계산 불가
      setQuestion("");
    }
    // jobData 변화만 감지하면 됨 — 다른 deps 포함 시 중복 처리
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobData]);

  /* 새 pending 턴 후 하단 스크롤 (turns 변경 감지) */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    // turns 변경 시마다 실행 — pending 추가 / done 전환 모두 포함
  }, [turns.length, turns]);

  /* ---------- 핸들러 ---------- */
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || submitMutation.isPending || activeJobId !== null || !isReady || project === null) return;

    // 1. 캡처: 제출 시점의 sessionId 고정 (세션 전환 시 오귀속 방지)
    capturedSessionIdRef.current = sessionId;

    // 2. 낙관적 턴 즉시 추가
    setTurns((prev) => addPendingTurn(prev, q));

    // 3. API 잡 제출 (onSuccess에서 setActiveJobId → 폴링 시작)
    submitMutation.mutate({ question: q, session_id: sessionId });
  }

  function handleNewSession() {
    if (project === null) return;

    // 1. 대화 내역 초기화 (비영속 — R-2)
    setTurns([]);

    // 2. 새 세션 발급 (R-5)
    const next = makeSessionId();
    setSessionId(next);

    // 3. 잡/입력 리셋
    submitMutation.reset();
    setActiveJobId(null);
    setQuestion("");

    // 4. 새 세션 즉시 prime (웜 배정은 BE 프라임 풀이 담당)
    primedSessionRef.current = next;
    primeMutation.mutate({ session_id: next });

    // 5. 상태 폴링 즉시 재조회 → priming 배지 즉시 반영
    void queryClient.invalidateQueries({
      queryKey: ["brain-status", project, next],
    });
  }

  /* "새 대화" 버튼 클릭 진입점 (R-8 ④) — turns>0이면 확인 후 handleNewSession, turns=0이면 즉시 실행.
     라우트 이탈이 아닌 화면 내 액션이므로 useBlocker와 무관하게 독립 처리한다. */
  function handleNewSessionClick() {
    if (turns.length > 0) {
      setPendingNewSession(true);
      return;
    }
    handleNewSession();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }

  /* ---------- 렌더 ---------- */

  // 로딩
  if (authLoading) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <div className="flex items-center gap-3">
          <MessageCircleQuestion className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-sm font-semibold">프로젝트 브레인</h1>
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // auth API 에러
  if (authError) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <div className="flex items-center gap-3">
          <MessageCircleQuestion className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-sm font-semibold">프로젝트 브레인</h1>
        </div>
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

  // 미인증
  if (!authData?.authenticated) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-6">
        <div className="flex items-center gap-3">
          <MessageCircleQuestion className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-sm font-semibold">프로젝트 브레인</h1>
        </div>
        <Alert className="border-status-stale/30 bg-status-stale/5">
          <AlertCircle className="h-4 w-4 text-status-stale" />
          <AlertTitle className="text-sm">브레인 질의를 사용할 수 없습니다</AlertTitle>
          <AlertDescription className="text-xs mt-1">
            {authData?.message ||
              "Claude Code CLI가 설치되어 있지 않거나 로그인되지 않았습니다."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  /* 인증 완료 상태 — 단일 대화창 (사이드바 없음, F-001) */
  return (
    <>
    <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center gap-2 px-4 py-3 border-b shrink-0">
        <MessageCircleQuestion className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="text-sm font-semibold">프로젝트 브레인</span>

        {/* 연동 상태 배지 (프로젝트 선택 + 현재 세션 기준) */}
        <div className="ml-auto flex items-center gap-2 shrink-0">
          {project === null ? (
            /* 프로젝트 미선택 배지 */
            <Badge
              variant="outline"
              className="text-[10px] text-muted-foreground"
            >
              <FolderOpen className="h-2.5 w-2.5 mr-1" />
              프로젝트 선택 필요
            </Badge>
          ) : (
            <>
              {brainState === "priming" && (
                <Badge
                  variant="outline"
                  className="text-[10px] gap-1 border-amber-400/50 text-amber-600 bg-amber-50 dark:bg-amber-950/20 dark:text-amber-400"
                >
                  <Loader2 className="h-2.5 w-2.5 animate-spin" />
                  {projName} · 연동 중…
                </Badge>
              )}
              {brainState === "ready" && (
                <Badge
                  variant="outline"
                  className="text-[10px] gap-1 border-green-400/50 text-green-700 bg-green-50 dark:bg-green-950/20 dark:text-green-400"
                >
                  <CheckCircle2 className="h-2.5 w-2.5" />
                  {projName} · 연동됨
                </Badge>
              )}
              {brainState === "error" && (
                <div className="flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className="text-[10px] gap-1 border-destructive/50 text-destructive bg-destructive/5"
                  >
                    <AlertCircle className="h-2.5 w-2.5" />
                    {projName} · 연동 실패{statusData?.message ? `: ${statusData.message}` : ""}
                  </Badge>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5"
                    title="재시도"
                    onClick={handleRetryPrime}
                  >
                    <RefreshCw className="h-3 w-3" />
                  </Button>
                </div>
              )}
              {brainState === "idle" && (
                <Badge
                  variant="outline"
                  className="text-[10px] text-muted-foreground"
                >
                  {projName} · 연동 시작 중…
                </Badge>
              )}
            </>
          )}
        </div>
      </div>

      {/* 대화 내용 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">

        {/* 프로젝트 미선택 안내 (인증 완료지만 프로젝트 미선택) */}
        {project === null && (
          <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
            <FolderOpen className="h-10 w-10 opacity-20" />
            <p className="text-sm font-medium">프로젝트를 선택하세요</p>
            <p className="text-xs text-center max-w-xs">
              좌측 상단 프로젝트 스위처에서 프로젝트를 선택하면
              <br />
              해당 프로젝트의 브레인 질의를 시작할 수 있습니다.
            </p>
          </div>
        )}

        {/* 빈 상태 (프로젝트 선택됨, 대화 내역 없음) */}
        {project !== null && turns.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
            <MessageCircleQuestion className="h-10 w-10 opacity-20" />
            <p className="text-sm">질문을 입력하세요</p>
            <p className="text-xs text-center max-w-xs">
              프로젝트 브레인에 저장된 지식을 기반으로 답변합니다.
              <br />
              첫 질의는 워밍업으로 최대 20초 소요될 수 있습니다.
            </p>
            <p className="text-[11px] text-center max-w-xs text-muted-foreground/70">
              이 대화는 저장되지 않아요 — 새로고침하거나 다시 열면 처음부터 시작합니다.
            </p>
          </div>
        )}

        {/* turns 렌더 (pending/done/error 모두 포함) — 아코디온 */}
        {turns.length > 0 && (
          <div className="max-w-3xl">
            <Accordion
              type="multiple"
              defaultValue={[`turn-${turns.length - 1}`]}
              className="border border-border/60 rounded-lg divide-y divide-border/60 overflow-hidden"
            >
              {turns.map((turn, i) => (
                <AccordionItem
                  key={i}
                  value={`turn-${i}`}
                  className="border-0"
                >
                  <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-accent/40 transition-colors [&[data-state=open]]:bg-accent/20">
                    <TurnTrigger turn={turn} index={i} />
                  </AccordionTrigger>
                  <AccordionContent className="px-4 border-t border-border/40 bg-muted/20">
                    <TurnContent turn={turn} />
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* 입력 폼 */}
      <div className="shrink-0 border-t px-4 py-3">
        {/* 프로젝트 미선택 안내 배너 */}
        {project === null && (
          <Alert className="mb-2 border-muted/50 bg-muted/20 py-2">
            <FolderOpen className="h-3.5 w-3.5" />
            <AlertDescription className="text-xs">
              프로젝트를 선택하세요 — 질의는 프로젝트 선택 후 가능합니다.
            </AlertDescription>
          </Alert>
        )}
        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              project === null
                ? "프로젝트를 선택하세요"
                : isReady
                  ? "질문을 입력하세요... (⌘Enter로 제출)"
                  : "연동 완료 후 질문 가능합니다"
            }
            rows={3}
            disabled={submitMutation.isPending || activeJobId !== null || !isReady || project === null}
            className="resize-none text-sm"
          />
          <div className="flex items-center justify-between">
            <p className="text-[11px] text-muted-foreground">
              {project === null
                ? "프로젝트 선택 필요"
                : !isReady
                  ? brainState === "priming"
                    ? "브레인 연동 중…"
                    : brainState === "error"
                      ? "연동 실패 — 재시도 후 질문하세요"
                      : "연동 준비 중…"
                  : turns.length > 0
                    ? `이어서 질문 중 (${turns.length}턴)`
                    : "새 대화"}
            </p>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                className="h-7 text-xs"
                onClick={handleNewSessionClick}
                disabled={submitMutation.isPending || activeJobId !== null || project === null}
              >
                <Plus className="h-3 w-3 mr-1" />
                새 대화
              </Button>
              <Button
                type="submit"
                size="sm"
                className="h-7 text-xs"
                disabled={!question.trim() || submitMutation.isPending || activeJobId !== null || !isReady || project === null}
              >
                <Send className="h-3 w-3 mr-1" />
                {submitMutation.isPending || activeJobId !== null ? "처리 중..." : "질문"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>

    {/* 이탈 확인 다이얼로그 (R-8 ①) — 콘솔 메뉴 전환(pathname 변경) 시도 시 노출 */}
    <AlertDialog
      open={blocker.state === "blocked"}
      onOpenChange={(open) => {
        if (!open) blocker.reset?.();
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{BRAIN_LEAVE_GUARD_TITLE}</AlertDialogTitle>
          <AlertDialogDescription>{BRAIN_LEAVE_GUARD_DESCRIPTION}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => blocker.reset?.()}>취소</AlertDialogCancel>
          <AlertDialogAction onClick={() => blocker.proceed?.()}>나가기</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    {/* 새 대화 확인 다이얼로그 (R-8 ④) — 라우트 이탈이 아닌 화면 내 액션, useBlocker와 무관하게 독립 처리 */}
    <AlertDialog
      open={pendingNewSession}
      onOpenChange={(open) => {
        if (!open) setPendingNewSession(false);
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>새 대화를 시작하면 현재 대화가 사라집니다</AlertDialogTitle>
          <AlertDialogDescription>계속할까요?</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => setPendingNewSession(false)}>취소</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              setPendingNewSession(false);
              handleNewSession();
            }}
          >
            확인
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
}

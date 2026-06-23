/**
 * @header {
 *   "module": "brain-page",
 *   "layer": "page",
 *   "domain": "brain",
 *   "description": "프로젝트 브레인 화면 — 인증 분기(GET /api/brain/auth) + 프로젝트 필수 게이팅(미선택 시 폼 비활성·안내) + 대화별 session_id(FE가 crypto.randomUUID()로 발급) + 자동 prime(POST /api/brain/prime {project, session_id}) + 상태 폴링(GET /api/brain/status?project=<절대경로>&session_id=<id>, 2초 간격, TanStack Query key에 project+session_id 포함) + 연동 상태 배지(활성 대화 세션 기준·프로젝트명 귀속·priming/ready/error/idle) + 질문 게이팅(state≠ready면 disabled) + 새 대화 시 즉시 이력추가+자기세션 프라임 + 질의(POST /api/brain/query {question,project,session_id}) + 낙관적 턴(제출 즉시 pending→done/error 갱신, 캡처 convId 귀속) + 답변/인용 렌더 + localStorage 이력(project 키잉 — 현재 선택 프로젝트 대화만 표시). 이력 키: opal-console:brain:conversations.",
 *   "exports": ["BrainPage", "addPendingTurn", "resolvePendingTurn", "appendTurnToConversation", "loadConversations", "saveConversations", "filterConversationsByProject", "makeNewConversation", "projectDisplayName", "jobResponseToResolution", "jobPollingInterval", "BrainJobResponse"],
 *   "depends": ["api-client", "card", "textarea", "button", "alert", "badge", "skeleton", "markdown-view", "ui-store"]
 * }
 */

import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownView } from "@/components/markdown-view";
import { cn } from "@/lib/utils";

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

/* localStorage 구조 */
export interface BrainTurn {
  q: string;
  a: string;
  citations: CitationItem[];
  ts: number; // Date.now()
  status: "pending" | "done" | "error"; // 낙관적 업데이트 상태
  errorMsg?: string; // status="error" 시 에러 메시지
}

export interface BrainConversation {
  id: string;          // thread ID (uuid)
  session_id: string;  // FE가 발급한 UUID (대화별 고유, BE 세션 키)
  project: string | null;
  turns: BrainTurn[];
  created_at: number;
}

/* ------------------------------------------------------------------ */
/* localStorage 헬퍼                                                     */
/* ------------------------------------------------------------------ */

const STORAGE_KEY = "opal-console:brain:conversations";

export function loadConversations(): BrainConversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed as BrainConversation[];
  } catch {
    return [];
  }
}

export function saveConversations(conversations: BrainConversation[]): void {
  try {
    // 최대 50개 대화만 유지 (localStorage 쿼터 보호)
    const capped = conversations.slice(-50);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(capped));
  } catch {
    // localStorage 쿼터 초과 시 조용히 무시
  }
}

/**
 * 낙관적 pending 턴을 특정 대화에 추가한다 (제출 즉시 호출).
 * 대화가 없으면 새로 생성한다.
 * status="pending", a="", citations=[] 로 초기화된다.
 */
export function addPendingTurn(
  conversations: BrainConversation[],
  conversationId: string,
  sessionId: string,
  question: string,
  project: string | null,
): BrainConversation[] {
  const pendingTurn: BrainTurn = {
    q: question,
    a: "",
    citations: [],
    ts: Date.now(),
    status: "pending",
  };

  const existing = conversations.find((c) => c.id === conversationId);
  if (existing) {
    return conversations.map((c) =>
      c.id === conversationId
        ? { ...c, session_id: sessionId, turns: [...c.turns, pendingTurn] }
        : c,
    );
  }

  // 새 conversation 생성
  const newConv: BrainConversation = {
    id: conversationId,
    session_id: sessionId,
    project,
    turns: [pendingTurn],
    created_at: Date.now(),
  };
  return [...conversations, newConv];
}

/**
 * 특정 대화의 마지막 pending 턴을 답변/에러로 갱신한다 (onSuccess/onError 시 호출).
 * capturedConvId 기준으로 귀속하므로 activeConvId가 바뀌어 있어도 올바른 대화에 반영된다.
 */
export function resolvePendingTurn(
  conversations: BrainConversation[],
  capturedConvId: string,
  resolution:
    | { status: "done"; answer: string; citations: CitationItem[] }
    | { status: "error"; errorMsg: string },
): BrainConversation[] {
  return conversations.map((c) => {
    if (c.id !== capturedConvId) return c;

    // 마지막 pending 턴의 인덱스를 찾는다
    const lastPendingIdx = [...c.turns].map((t, i) => ({ t, i }))
      .filter(({ t }) => t.status === "pending")
      .pop()?.i ?? -1;

    if (lastPendingIdx === -1) return c; // pending 턴 없음 → 변경 없음

    const updatedTurns = c.turns.map((turn, i) => {
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

    return { ...c, turns: updatedTurns };
  });
}

/**
 * 완성된 턴(done 상태)을 대화에 추가한다 (하위 호환 유지).
 * 낙관적 업데이트를 사용하지 않는 외부 호출 또는 테스트에서 직접 사용 가능.
 */
export function appendTurnToConversation(
  conversations: BrainConversation[],
  conversationId: string,
  sessionId: string,
  turn: Omit<BrainTurn, "ts" | "status" | "errorMsg">,
  project: string | null,
): BrainConversation[] {
  const existing = conversations.find((c) => c.id === conversationId);
  const newTurn: BrainTurn = { ...turn, ts: Date.now(), status: "done" };

  if (existing) {
    return conversations.map((c) =>
      c.id === conversationId
        ? { ...c, session_id: sessionId, turns: [...c.turns, newTurn] }
        : c,
    );
  }

  // 새 conversation 생성
  const newConv: BrainConversation = {
    id: conversationId,
    session_id: sessionId,
    project,
    turns: [newTurn],
    created_at: Date.now(),
  };
  return [...conversations, newConv];
}

/**
 * 전체 대화 목록에서 특정 프로젝트 대화만 필터링한다.
 * project가 null이면 project 필드가 null인 대화를 반환한다.
 */
export function filterConversationsByProject(
  conversations: BrainConversation[],
  project: string | null,
): BrainConversation[] {
  return conversations.filter((c) => c.project === project);
}

/** 새 대화용 고유 ID 생성 (conv id와 session_id 모두 UUID 사용) */
export function makeNewConversation(project: string | null): BrainConversation {
  const id = crypto.randomUUID();
  const session_id = crypto.randomUUID();
  return {
    id,
    session_id,
    project,
    turns: [],
    created_at: Date.now(),
  };
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
/* ConversationView — 단일 대화 thread                                  */
/* ------------------------------------------------------------------ */

function ConversationView({
  conversation,
  isActive,
  onSelect,
}: {
  conversation: BrainConversation;
  isActive: boolean;
  onSelect: () => void;
}) {
  const date = new Date(conversation.created_at);
  const dateStr = date.toLocaleDateString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  const preview = conversation.turns[0]?.q ?? "(빈 대화)";
  const hasPending = conversation.turns.some((t) => t.status === "pending");

  return (
    <button
      className={cn(
        "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
        isActive
          ? "bg-accent text-accent-foreground"
          : "hover:bg-accent/50 text-muted-foreground hover:text-foreground",
      )}
      onClick={onSelect}
    >
      <div className="flex items-center gap-1 min-w-0">
        <p className="truncate font-medium text-xs flex-1">{preview}</p>
        {hasPending && (
          <Loader2 className="h-2.5 w-2.5 animate-spin shrink-0 text-amber-500" />
        )}
      </div>
      <p className="text-[10px] mt-0.5 opacity-60">{dateStr}</p>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* BrainPage                                                             */
/* ------------------------------------------------------------------ */

export function BrainPage() {
  const [searchParams] = useSearchParams();
  const contextProject = useUiStore((s) => s.contextProject);
  const project = contextProject ?? searchParams.get("project") ?? null;
  const queryClient = useQueryClient();

  // 선택된 프로젝트의 표시용 짧은 이름
  const projName = projectDisplayName(project);

  /* ---------- 이력 상태 (전체 — localStorage) ---------- */
  const [allConversations, setAllConversations] = useState<BrainConversation[]>(() =>
    loadConversations(),
  );

  // 현재 프로젝트에 속하는 대화만 파생
  const conversations = filterConversationsByProject(allConversations, project);

  const [activeConvId, setActiveConvId] = useState<string | null>(() => {
    const convs = filterConversationsByProject(loadConversations(), project);
    return convs.length > 0 ? convs[convs.length - 1].id : null;
  });

  // 활성 대화 객체 (전체 대화 목록에서 조회 — 프로젝트 필터 무관하게)
  const activeConv = allConversations.find((c) => c.id === activeConvId) ?? null;

  // 활성 대화의 session_id (없으면 null)
  const activeSessionId = activeConv?.session_id ?? null;

  /* ---------- 잡 폴링 상태 ---------- */
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  /* ---------- API: query (잡 제출 — 비동기) ---------- */
  // 캡처된 convId를 ref로 추적 — mutation 시작 시점의 activeConvId를 캡처한다.
  // 잡 폴링 done/error 시 이 값을 사용해 올바른 대화에 답변을 귀속시킨다.
  const capturedConvIdRef = useRef<string | null>(null);

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
      const convId = capturedConvIdRef.current;
      if (!convId) return;

      setAllConversations((prev) => {
        const errMsg = error?.message ?? "알 수 없는 오류가 발생했습니다.";
        const updated = resolvePendingTurn(prev, convId, {
          status: "error",
          errorMsg: errMsg,
        });
        saveConversations(updated);
        return updated;
      });
    },
  });

  // 프로젝트 전환 시 activeConvId를 새 프로젝트의 최신 대화로 재설정
  const prevProjectRef = useRef(project);
  useEffect(() => {
    if (prevProjectRef.current !== project) {
      prevProjectRef.current = project;
      const convs = filterConversationsByProject(allConversations, project);
      setActiveConvId(convs.length > 0 ? convs[convs.length - 1].id : null);
      submitMutation.reset();
      setActiveJobId(null);
    }
    // submitMutation을 deps에 포함하면 무한루프 — 의도적 제외
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project]);

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

  /* ---------- API: status 폴링 (project + session_id 포함 — 대화별 격리) ---------- */
  const {
    data: statusData,
    refetch: refetchStatus,
  } = useQuery<BrainStatusResponse>({
    // project + session_id를 query key에 포함 → 대화 전환 시 자동 재폴링
    queryKey: ["brain-status", project, activeSessionId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (project) params.set("project", project);
      if (activeSessionId) params.set("session_id", activeSessionId);
      return apiClient<BrainStatusResponse>(`/api/brain/status?${params.toString()}`);
    },
    // 인증 완료 + 프로젝트 선택 + 활성 session_id 있을 때만 폴링
    enabled: !!authData?.authenticated && project !== null && activeSessionId !== null,
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

  /* 인증 완료 + 프로젝트 선택 + 활성 대화 있을 때 → status 확인 후 prime */
  const primedSessionRef = useRef<string | null>(null); // 이미 prime된 session_id 추적
  useEffect(() => {
    if (!authData?.authenticated || project === null || activeSessionId === null) return;
    // 이미 prime한 세션은 skip
    if (primedSessionRef.current === activeSessionId) return;
    primedSessionRef.current = activeSessionId;
    primeMutation.mutate({ session_id: activeSessionId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authData?.authenticated, project, activeSessionId]);

  /* idle 상태 감지 시 활성 세션 재프라임 트리거 */
  useEffect(() => {
    if (brainState === "idle" && authData?.authenticated && project !== null && activeSessionId !== null) {
      primeMutation.mutate({ session_id: activeSessionId });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brainState]);

  /* ---------- 재시도 핸들러 ---------- */
  function handleRetryPrime() {
    if (activeSessionId === null) return;
    primedSessionRef.current = null;
    primeMutation.mutate({ session_id: activeSessionId });
    void refetchStatus();
  }

  /* ---------- API: 잡 폴링 ---------- */
  const { data: jobData } = useQuery<BrainJobResponse>({
    queryKey: ["brain-job", project, activeSessionId, activeJobId],
    enabled: activeJobId !== null,
    queryFn: () => {
      const params = new URLSearchParams();
      if (project) params.set("project", project);
      if (activeSessionId) params.set("session_id", activeSessionId);
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

    const convId = capturedConvIdRef.current;
    if (!convId) return;

    setAllConversations((prev) => {
      const updated = resolvePendingTurn(prev, convId, resolution);
      saveConversations(updated);
      return updated;
    });
    setActiveJobId(null);
    if (resolution.status === "done") {
      setQuestion("");
    }
    // jobData 변화만 감지하면 됨 — 다른 deps 포함 시 중복 처리
  }, [jobData]);

  /* 새 pending 턴 후 하단 스크롤 (allConversations 변경 감지) */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    // allConversations 변경 시마다 실행 — pending 추가 / done 전환 모두 포함
  }, [allConversations.length, allConversations]);

  /* ---------- 핸들러 ---------- */
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || submitMutation.isPending || activeJobId !== null || !isReady || project === null || activeSessionId === null || activeConvId === null) return;

    // 1. 캡처: 제출 시점의 convId + session_id 고정 (오라우팅 방지)
    capturedConvIdRef.current = activeConvId;

    // 2. 낙관적 턴 즉시 추가 + localStorage 저장
    setAllConversations((prev) => {
      const updated = addPendingTurn(prev, activeConvId, activeSessionId, q, project);
      saveConversations(updated);
      return updated;
    });

    // 3. API 잡 제출 (onSuccess에서 setActiveJobId → 폴링 시작)
    submitMutation.mutate({ question: q, session_id: activeSessionId });
  }

  function handleNewConversation() {
    if (project === null) return;

    // 새 대화 생성 (id + session_id 모두 FE에서 UUID 발급)
    const newConv = makeNewConversation(project);

    // 이력에 즉시 추가 (질의 전에도 이력 목록에 표시)
    const updated = [...allConversations, newConv];
    setAllConversations(updated);
    saveConversations(updated);

    // 활성 대화를 새 대화로 전환
    setActiveConvId(newConv.id);
    setQuestion("");
    submitMutation.reset();
    setActiveJobId(null);

    // 새 대화의 session_id로 prime 호출
    primedSessionRef.current = newConv.session_id;
    primeMutation.mutate({ session_id: newConv.session_id });
    // status 폴링을 즉시 refetch → priming 배지 즉시 반영
    void queryClient.invalidateQueries({
      queryKey: ["brain-status", project, newConv.session_id],
    });
  }

  function handleSelectConversation(conv: BrainConversation) {
    setActiveConvId(conv.id);
    setQuestion("");
    submitMutation.reset();
    setActiveJobId(null);

    // 선택한 대화의 세션 상태를 확인하고, ready가 아니면 재워밍
    // (useEffect의 status 폴링 + primedSessionRef 로직이 담당)
    // primedSessionRef를 리셋하여 재prime 허용
    if (project !== null) {
      primedSessionRef.current = null;
      // status 폴링 즉시 실행 → 상태 확인
      void queryClient.invalidateQueries({
        queryKey: ["brain-status", project, conv.session_id],
      });
    }
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

  /* 인증 완료 상태 */
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* 좌측: 대화 이력 목록 */}
      <aside className="w-56 shrink-0 border-r flex flex-col gap-2 p-3 overflow-y-auto">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            대화 이력
          </p>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            title="새 대화"
            onClick={handleNewConversation}
            disabled={project === null}
          >
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* 프로젝트 미선택 시 안내 */}
        {project === null && (
          <p className="text-[11px] text-muted-foreground px-1 flex items-start gap-1">
            <FolderOpen className="h-3 w-3 shrink-0 mt-0.5" />
            프로젝트를 선택하면 이력이 표시됩니다.
          </p>
        )}

        {/* 프로젝트 선택 시 대화 이력 없음 안내 */}
        {project !== null && conversations.length === 0 && (
          <p className="text-[11px] text-muted-foreground px-1">
            새 대화 버튼으로 시작하세요.
          </p>
        )}

        {project !== null && (
          /* 최신 순으로 표시 */
          [...conversations].reverse().map((conv) => (
            <ConversationView
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConvId}
              onSelect={() => handleSelectConversation(conv)}
            />
          ))
        )}
      </aside>

      {/* 우측: 대화 본문 */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* 대화 헤더 */}
        <div className="flex items-center gap-2 px-4 py-3 border-b shrink-0">
          <MessageCircleQuestion className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="text-sm font-semibold">
            {activeConvId === null
              ? "대화를 선택하세요"
              : activeConv && activeConv.turns.length === 0
                ? "새 대화"
                : `대화 ${activeConv ? conversations.indexOf(activeConv) + 1 : ""}`}
          </span>

          {/* 연동 상태 배지 (프로젝트 선택 + 활성 세션 기준) */}
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

          {/* 빈 상태 (프로젝트 선택됨, 대화 미선택 또는 빈 대화) */}
          {project !== null && (activeConvId === null || (activeConv && activeConv.turns.length === 0)) && (
            <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
              <MessageCircleQuestion className="h-10 w-10 opacity-20" />
              <p className="text-sm">질문을 입력하세요</p>
              <p className="text-xs text-center max-w-xs">
                프로젝트 브레인에 저장된 지식을 기반으로 답변합니다.
                <br />
                첫 질의는 워밍업으로 최대 20초 소요될 수 있습니다.
              </p>
            </div>
          )}

          {/* turns 렌더 (pending/done/error 모두 포함) — 아코디온 */}
          {activeConv && activeConv.turns.length > 0 && (
            <div className="max-w-3xl">
              <Accordion
                type="multiple"
                defaultValue={[`turn-${activeConv.turns.length - 1}`]}
                className="border border-border/60 rounded-lg divide-y divide-border/60 overflow-hidden"
              >
                {activeConv.turns.map((turn, i) => (
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
              disabled={submitMutation.isPending || activeJobId !== null || !isReady || project === null || activeConvId === null}
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
                    : activeConv && activeConv.turns.length > 0
                      ? `이어서 질문 중 (${activeConv.turns.length}턴)`
                      : "새 대화"}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={handleNewConversation}
                  disabled={submitMutation.isPending || activeJobId !== null || project === null}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  새 대화
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  className="h-7 text-xs"
                  disabled={!question.trim() || submitMutation.isPending || activeJobId !== null || !isReady || project === null || activeConvId === null}
                >
                  <Send className="h-3 w-3 mr-1" />
                  {submitMutation.isPending || activeJobId !== null ? "처리 중..." : "질문"}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

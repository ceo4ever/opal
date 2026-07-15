/**
 * @header {
 *   "module": "brain-navigation-guard-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "R-8 이탈 가드 RTL 단위 테스트 — turns.length>0일 때 4경로(①콘솔 메뉴 전환 useBlocker ②beforeunload ③brainDirty→AppShell 프로젝트 스위처 ④'새 대화' 버튼 pendingNewSession)를 검증한다. apiClient를 mock하여 auth→prime→status(ready)→query→job(done) 흐름을 즉시 완료시켜 turns.length===1 상태를 재현한 뒤, createMemoryRouter의 imperative navigate 또는 UI 클릭으로 각 경로 이탈을 시도한다.",
 *   "exports": [],
 *   "depends": ["brain-page", "app-shell", "ui-store", "api-client"],
 *   "task": "063",
 *   "scenarios": ["T063-S-R8-1", "T063-S-R8-2", "T063-S-R8-3", "T063-S-R8-4"]
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, within, cleanup, act } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrainPage } from "./BrainPage";
import { AppShell } from "@/components/app-shell/AppShell";
import { useUiStore } from "@/store/ui-store";
import { apiClient } from "@/lib/api";

/* ------------------------------------------------------------------ */
/* apiClient mock — brain 4-endpoint + projects/health(AppShell용)      */
/* ------------------------------------------------------------------ */

const PROJECT_A = "/path/to/project-a";
const PROJECT_B = "/path/to/project-b";
const ANSWER_TEXT = "[T063/L1-R8] 테스트 답변";

vi.mock("@/lib/api", () => ({
  apiClient: vi.fn((path: string) => {
    if (path.startsWith("/api/brain/auth")) {
      return Promise.resolve({ authenticated: true, cli_available: true, message: "" });
    }
    if (path.startsWith("/api/brain/prime")) {
      return Promise.resolve({ priming: true });
    }
    if (path.startsWith("/api/brain/status")) {
      // 폴링 대기 없이 즉시 ready — turns 누적 흐름만 검증 대상
      return Promise.resolve({ state: "ready", session_active: true, message: "" });
    }
    if (path.startsWith("/api/brain/query")) {
      return Promise.resolve({ job_id: "job-1" });
    }
    if (path.startsWith("/api/brain/job/")) {
      return Promise.resolve({ job_id: "job-1", status: "done", answer: ANSWER_TEXT, citations: [] });
    }
    if (path.startsWith("/api/projects")) {
      return Promise.resolve([
        { name: "project-a", path: PROJECT_A, is_opal: true },
        { name: "project-b", path: PROJECT_B, is_opal: true },
      ]);
    }
    if (path.startsWith("/health")) {
      return Promise.resolve({ status: "ok", version: "0.1" });
    }
    return Promise.reject(new Error(`[test] unmocked apiClient path: ${path}`));
  }),
}));

/* ------------------------------------------------------------------ */
/* 렌더 헬퍼                                                             */
/* ------------------------------------------------------------------ */

function renderBrainPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/brain", element: <BrainPage /> },
      { path: "/other", element: <div>다른 화면</div> },
    ],
    { initialEntries: ["/brain"] },
  );
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router, unmount: view.unmount };
}

function renderAppShell() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter(
    [{ path: "/", element: <AppShell />, children: [{ index: true, element: <div>홈</div> }] }],
    { initialEntries: ["/"] },
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router };
}

/** 인증+연동 완료(ready) 대기 — 질문 입력 활성화 시점까지 */
async function waitUntilReady() {
  await screen.findByPlaceholderText("질문을 입력하세요... (⌘Enter로 제출)");
}

/** 질문 1건 제출 → 답변 완료(turns.length===1)까지 대기 */
async function askOneQuestionAndWaitDone() {
  const textarea = await screen.findByPlaceholderText("질문을 입력하세요... (⌘Enter로 제출)");
  fireEvent.change(textarea, { target: { value: "테스트 질문" } });
  const submitBtn = screen.getByRole("button", { name: "질문" });
  fireEvent.click(submitBtn);
  await screen.findByText(ANSWER_TEXT);
}

/** mock된 apiClient 호출 중 /api/brain/prime 요청 바디의 session_id 목록을 순서대로 추출한다 */
function primeSessionIds(): string[] {
  return vi
    .mocked(apiClient)
    .mock.calls.filter(([path]) => typeof path === "string" && path.startsWith("/api/brain/prime"))
    .map(([, options]) => {
      const body = (options as RequestInit | undefined)?.body;
      const parsed = body ? (JSON.parse(body as string) as { session_id?: string }) : {};
      return parsed.session_id ?? "";
    });
}

beforeEach(() => {
  vi.clearAllMocks();
  // ui-store는 모듈 싱글턴 — 테스트 간 오염 방지 (contextProject/brainDirty 리셋, 액션 함수는 유지)
  useUiStore.setState({ contextProject: PROJECT_A, brainDirty: false });
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* ① 콘솔 메뉴 전환 — useBlocker (pathname 변경)                         */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R8] 이탈 가드 ① 콘솔 메뉴 전환 (useBlocker)", () => {
  it("turns=0일 때는 확인 없이 즉시 이동한다 (blocker 비활성)", async () => {
    const { router } = renderBrainPage();
    await waitUntilReady();

    await act(async () => {
      await router.navigate("/other");
    });

    await waitFor(() => expect(screen.getByText("다른 화면")).toBeInTheDocument());
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("turns>0일 때 이동 시도 시 확인 다이얼로그가 노출되고 페이지에 잔류한다", async () => {
    const { router } = renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    act(() => {
      void router.navigate("/other");
    });

    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText("화면을 나가면 이 대화 세션이 사라집니다")).toBeInTheDocument();
    // 아직 이동하지 않음 — 대화 화면에 잔류
    expect(screen.queryByText("다른 화면")).not.toBeInTheDocument();
    expect(screen.getByText(ANSWER_TEXT)).toBeInTheDocument();
  });

  it("'취소' 클릭 시 페이지에 잔류하고 대화(turns)가 유지된다", async () => {
    const { router } = renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    act(() => {
      void router.navigate("/other");
    });
    const dialog = await screen.findByRole("alertdialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "취소" }));

    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(screen.queryByText("다른 화면")).not.toBeInTheDocument();
    expect(screen.getByText(ANSWER_TEXT)).toBeInTheDocument(); // 세션(turns) 유지
  });

  it("'나가기' 클릭 시 이동이 완료된다", async () => {
    const { router } = renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    act(() => {
      void router.navigate("/other");
    });
    const dialog = await screen.findByRole("alertdialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "나가기" }));

    await waitFor(() => expect(screen.getByText("다른 화면")).toBeInTheDocument());
  });
});

/* ------------------------------------------------------------------ */
/* ② 브라우저 새로고침·탭 닫기 — beforeunload                            */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R8] 이탈 가드 ② 브라우저 새로고침·탭 닫기 (beforeunload)", () => {
  it("turns>0이면 beforeunload에서 preventDefault가 호출된다", async () => {
    renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    const event = new Event("beforeunload", { cancelable: true });
    const preventDefaultSpy = vi.spyOn(event, "preventDefault");
    window.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it("turns=0이면 beforeunload에서 preventDefault가 호출되지 않는다 (리스너 no-op)", async () => {
    renderBrainPage();
    await waitUntilReady();

    const event = new Event("beforeunload", { cancelable: true });
    const preventDefaultSpy = vi.spyOn(event, "preventDefault");
    window.dispatchEvent(event);

    expect(preventDefaultSpy).not.toHaveBeenCalled();
  });
});

/* ------------------------------------------------------------------ */
/* ③ 프로젝트 스위처 전환 — ui-store brainDirty → AppShell 가드          */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R8] 이탈 가드 ③ 프로젝트 스위처 전환 (brainDirty)", () => {
  it("turns>0(brainDirty)이면 BrainPage가 ui-store.brainDirty를 true로 동기화하고, 언마운트 시 false로 복원한다", async () => {
    const { unmount } = renderBrainPage();
    await waitUntilReady();
    expect(useUiStore.getState().brainDirty).toBe(false);

    await askOneQuestionAndWaitDone();
    await waitFor(() => expect(useUiStore.getState().brainDirty).toBe(true));

    unmount();
    expect(useUiStore.getState().brainDirty).toBe(false);
  });

  it("brainDirty=true일 때 프로젝트 전환 시도 시 확인 다이얼로그가 노출되고, '취소' 시 프로젝트가 유지된다", async () => {
    useUiStore.setState({ contextProject: PROJECT_A, brainDirty: true });
    renderAppShell();

    const trigger = await screen.findByRole("button", { name: /project-a/ });
    fireEvent.pointerDown(trigger, { button: 0, ctrlKey: false });

    const projectBItem = await screen.findByText("project-b");
    fireEvent.click(projectBItem);

    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText("화면을 나가면 이 대화 세션이 사라집니다")).toBeInTheDocument();
    expect(useUiStore.getState().contextProject).toBe(PROJECT_A); // 아직 전환되지 않음

    fireEvent.click(within(dialog).getByRole("button", { name: "취소" }));
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(useUiStore.getState().contextProject).toBe(PROJECT_A); // 취소 — 유지
  });

  it("brainDirty=true일 때 프로젝트 전환 확인 다이얼로그에서 '나가기' 클릭 시 프로젝트가 전환된다", async () => {
    useUiStore.setState({ contextProject: PROJECT_A, brainDirty: true });
    renderAppShell();

    const trigger = await screen.findByRole("button", { name: /project-a/ });
    fireEvent.pointerDown(trigger, { button: 0, ctrlKey: false });

    const projectBItem = await screen.findByText("project-b");
    fireEvent.click(projectBItem);

    const dialog = await screen.findByRole("alertdialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "나가기" }));

    await waitFor(() => expect(useUiStore.getState().contextProject).toBe(PROJECT_B));
  });

  it("brainDirty=false(브레인 화면 아님)이면 프로젝트 전환이 확인 없이 즉시 적용된다", async () => {
    useUiStore.setState({ contextProject: PROJECT_A, brainDirty: false });
    renderAppShell();

    const trigger = await screen.findByRole("button", { name: /project-a/ });
    fireEvent.pointerDown(trigger, { button: 0, ctrlKey: false });

    const projectBItem = await screen.findByText("project-b");
    fireEvent.click(projectBItem);

    await waitFor(() => expect(useUiStore.getState().contextProject).toBe(PROJECT_B));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* ④ "새 대화" 버튼 — pendingNewSession (라우트 이탈과 무관한 화면 내 액션)  */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R8] 이탈 가드 ④ '새 대화' 버튼 (pendingNewSession)", () => {
  it("turns>0에서 '새 대화' 클릭 시 확인 다이얼로그가 노출되고, '취소' 시 대화(turns)가 유지된다", async () => {
    renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    fireEvent.click(screen.getByRole("button", { name: "새 대화" }));

    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText("새 대화를 시작하면 현재 대화가 사라집니다")).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole("button", { name: "취소" }));
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(screen.getByText(ANSWER_TEXT)).toBeInTheDocument(); // 유지 — handleNewSession 미실행
  });

  it("확인 다이얼로그에서 '확인' 클릭 시 handleNewSession이 실행되어 turns가 초기화되고 새 session_id로 재prime된다", async () => {
    renderBrainPage();
    await waitUntilReady();
    await askOneQuestionAndWaitDone();

    fireEvent.click(screen.getByRole("button", { name: "새 대화" }));
    const dialog = await screen.findByRole("alertdialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "확인" }));

    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText(ANSWER_TEXT)).not.toBeInTheDocument()); // turns 초기화
    await screen.findByText("질문을 입력하세요"); // 빈 상태로 복귀

    const sessionIds = primeSessionIds();
    expect(sessionIds.length).toBeGreaterThanOrEqual(2); // mount prime + 새 대화 prime
    expect(new Set(sessionIds).size).toBeGreaterThanOrEqual(2); // 서로 다른 session_id — 새 세션 발급 확인
  });

  it("turns=0에서 '새 대화' 클릭 시 확인 없이 즉시 재실행된다 (현행 유지)", async () => {
    renderBrainPage();
    await waitUntilReady();

    // mount 시퀀스의 비동기 prime 호출이 모두 안정화될 때까지 대기(baseline 오염 방지)
    await waitFor(() => expect(primeSessionIds().length).toBeGreaterThanOrEqual(1));
    const idsBefore = primeSessionIds();
    const lastIdBefore = idsBefore[idsBefore.length - 1];

    fireEvent.click(screen.getByRole("button", { name: "새 대화" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument(); // 확인 없이 즉시 실행
    await waitFor(() => {
      const idsAfter = primeSessionIds();
      expect(idsAfter.length).toBeGreaterThan(idsBefore.length); // handleNewSession의 재prime 호출 확인
      expect(idsAfter[idsAfter.length - 1]).not.toBe(lastIdBefore); // 새 session_id로 재prime — 새 세션 발급 확인
    });
  });
});

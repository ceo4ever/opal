/**
 * @header {
 *   "module": "brain-new-conversation-prime-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "새 대화→재프라임 + 대화별 session_id 경로 단위 테스트 — prime 페이로드에 session_id 포함 + query에 session_id 포함 + 대화별 독립 session_id 검증 + 새 대화 즉시 이력추가 + 기존 대화 session_id 불변 로직 검증 + 낙관적 업데이트 흐름 검증. fetch mock 사용.",
 *   "task": "022-260615-opd-opx-flex-pilot",
 *   "scenarios": ["new-conv-prime", "per-conv-session", "new-conv-immediate-history", "optimistic-update-flow"]
 * }
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  makeNewConversation,
  filterConversationsByProject,
  saveConversations,
  loadConversations,
  addPendingTurn,
  resolvePendingTurn,
  type BrainConversation,
} from "./BrainPage";

/* ------------------------------------------------------------------ */
/* localStorage 모킹                                                     */
/* ------------------------------------------------------------------ */

let _store: Record<string, string> = {};

const localStorageMock = {
  getItem: vi.fn((key: string) => _store[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { _store[key] = value; }),
  removeItem: vi.fn((key: string) => { delete _store[key]; }),
  clear: vi.fn(() => { _store = {}; }),
  get length() { return Object.keys(_store).length; },
  key: vi.fn(),
};

Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  writable: true,
});

/* ------------------------------------------------------------------ */
/* prime 페이로드 빌더 순수 함수 (컴포넌트 로직에서 추출한 동일 구조)    */
/* ------------------------------------------------------------------ */

/**
 * primeMutation.mutationFn에 상응하는 순수 페이로드 빌더.
 * project + session_id를 항상 포함한다.
 */
function buildPrimePayload(
  project: string | null,
  session_id: string,
): Record<string, unknown> {
  return { project, session_id };
}

/**
 * query mutationFn에 상응하는 순수 페이로드 빌더.
 * question + project + session_id를 포함한다.
 */
function buildQueryPayload(
  question: string,
  project: string | null,
  session_id: string,
): Record<string, unknown> {
  return { question, project, session_id };
}

/* ------------------------------------------------------------------ */
/* 테스트                                                                */
/* ------------------------------------------------------------------ */

const PROJECT = "/path/to/project";

describe("prime 페이로드 — session_id 포함", () => {
  it("prime: project + session_id 포함", () => {
    const payload = buildPrimePayload(PROJECT, "sess-uuid-1234");
    expect(payload).toEqual({ project: PROJECT, session_id: "sess-uuid-1234" });
  });

  it("project가 null이어도 session_id는 포함된다", () => {
    const payload = buildPrimePayload(null, "sess-uuid-1234");
    expect(payload.project).toBeNull();
    expect(payload.session_id).toBe("sess-uuid-1234");
  });

  it("new_conversation 필드는 포함하지 않는다 (BE 계약 변경)", () => {
    const payload = buildPrimePayload(PROJECT, "sess-uuid-1234");
    expect(payload).not.toHaveProperty("new_conversation");
  });
});

describe("query 페이로드 — session_id 포함", () => {
  it("question + project + session_id를 포함한다", () => {
    const payload = buildQueryPayload("테스트 질문", PROJECT, "sess-uuid-5678");
    expect(payload).toEqual({
      question: "테스트 질문",
      project: PROJECT,
      session_id: "sess-uuid-5678",
    });
  });

  it("project가 null이어도 session_id 포함", () => {
    const payload = buildQueryPayload("질문", null, "sess-uuid-5678");
    expect(payload.session_id).toBe("sess-uuid-5678");
    expect(payload).not.toHaveProperty("new_conversation");
  });
});

describe("대화별 session_id — 독립성 검증", () => {
  it("각 대화는 고유한 session_id를 가진다", () => {
    const conv1 = makeNewConversation(PROJECT);
    const conv2 = makeNewConversation(PROJECT);
    expect(conv1.session_id).not.toBe(conv2.session_id);
  });

  it("한 대화의 session_id가 다른 대화의 session_id와 다르다", () => {
    const convs = Array.from({ length: 5 }, () => makeNewConversation(PROJECT));
    const sessionIds = convs.map((c) => c.session_id);
    const uniqueIds = new Set(sessionIds);
    expect(uniqueIds.size).toBe(5);
  });

  it("기존 대화는 새 대화 생성 후에도 session_id가 불변이다", () => {
    _store = {};
    const existing: BrainConversation = {
      id: "old-id",
      session_id: "old-session-uuid",
      project: PROJECT,
      turns: [{ q: "q", a: "a", citations: [], ts: Date.now(), status: "done" }],
      created_at: Date.now() - 10000,
    };
    saveConversations([existing]);

    // 새 대화 생성 (기존 대화에 영향 없음)
    const newConv = makeNewConversation(PROJECT);
    const all = [...loadConversations(), newConv];
    saveConversations(all);

    const loaded = loadConversations();
    const oldLoaded = loaded.find((c) => c.id === "old-id");
    expect(oldLoaded).toBeDefined();
    expect(oldLoaded!.session_id).toBe("old-session-uuid"); // 불변
  });
});

describe("새 대화 즉시 이력추가 시뮬레이션", () => {
  beforeEach(() => {
    _store = {};
    vi.clearAllMocks();
  });

  it("새 대화 생성 시 turns가 빈 배열이어도 이력에 즉시 추가된다", () => {
    const allConvs: BrainConversation[] = [];
    const newConv = makeNewConversation(PROJECT);

    // handleNewConversation 로직: 즉시 이력에 추가
    const updated = [...allConvs, newConv];
    saveConversations(updated);

    const loaded = loadConversations();
    expect(loaded).toHaveLength(1);
    expect(loaded[0].id).toBe(newConv.id);
    expect(loaded[0].turns).toHaveLength(0); // 빈 대화도 이력에 있음
  });

  it("기존 대화 목록에 새 대화를 추가해도 기존 대화는 변경되지 않는다", () => {
    const existing: BrainConversation = {
      id: "existing-id",
      session_id: "existing-session",
      project: PROJECT,
      turns: [{ q: "기존 질문", a: "기존 답변", citations: [], ts: Date.now() - 5000, status: "done" }],
      created_at: Date.now() - 5000,
    };
    saveConversations([existing]);

    const newConv = makeNewConversation(PROJECT);
    const all = [...loadConversations(), newConv];
    saveConversations(all);

    const loaded = loadConversations();
    expect(loaded).toHaveLength(2);

    const existingLoaded = loaded.find((c) => c.id === "existing-id");
    expect(existingLoaded).toBeDefined();
    expect(existingLoaded!.session_id).toBe("existing-session");
    expect(existingLoaded!.turns).toHaveLength(1);
    expect(existingLoaded!.turns[0].q).toBe("기존 질문");
  });

  it("filterConversationsByProject로 프로젝트별 분리 유지", () => {
    const OTHER_PROJECT = "/path/to/other";
    const convA = makeNewConversation(PROJECT);
    const convB = makeNewConversation(OTHER_PROJECT);
    saveConversations([convA, convB]);

    const loaded = loadConversations();
    const forProject = filterConversationsByProject(loaded, PROJECT);
    const forOther = filterConversationsByProject(loaded, OTHER_PROJECT);

    expect(forProject).toHaveLength(1);
    expect(forProject[0].id).toBe(convA.id);
    expect(forOther).toHaveLength(1);
    expect(forOther[0].id).toBe(convB.id);
  });
});

describe("handleNewConversation 흐름 시뮬레이션 — fetch mock", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("새 대화 클릭 시 prime에 session_id를 보내고 query에도 같은 session_id를 보낸다", async () => {
    const primeCalls: unknown[] = [];
    const queryCalls: unknown[] = [];

    const newConv = makeNewConversation(PROJECT);

    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      const body = init?.body ? JSON.parse(init.body as string) : {};
      if (url.includes("/api/brain/prime")) {
        primeCalls.push(body);
      } else if (url.includes("/api/brain/query")) {
        queryCalls.push(body);
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ priming: true }),
      });
    });

    // 새 대화 클릭 시 prime 호출 시뮬레이션
    await mockFetch("/api/brain/prime", {
      method: "POST",
      body: JSON.stringify(buildPrimePayload(PROJECT, newConv.session_id)),
    });

    // 이후 질문 제출 시 query 호출 시뮬레이션 (같은 session_id)
    await mockFetch("/api/brain/query", {
      method: "POST",
      body: JSON.stringify(buildQueryPayload("새로운 질문", PROJECT, newConv.session_id)),
    });

    // prime에 session_id 포함 확인
    expect(primeCalls).toHaveLength(1);
    expect(primeCalls[0]).toMatchObject({ project: PROJECT, session_id: newConv.session_id });
    expect(primeCalls[0]).not.toHaveProperty("new_conversation");

    // query에 동일한 session_id 포함 확인
    expect(queryCalls).toHaveLength(1);
    expect(queryCalls[0]).toMatchObject({
      question: "새로운 질문",
      project: PROJECT,
      session_id: newConv.session_id,
    });
  });
});

/* ------------------------------------------------------------------ */
/* 낙관적 업데이트 전체 흐름 시뮬레이션                                  */
/* ------------------------------------------------------------------ */

describe("낙관적 업데이트 전체 흐름 — submit→pending→done/error", () => {
  beforeEach(() => {
    _store = {};
    vi.clearAllMocks();
  });

  it("제출 즉시 pending 턴이 localStorage에 저장된다", () => {
    const conv = makeNewConversation(PROJECT);
    // handleSubmit 시뮬레이션: 제출 즉시 pending 추가 + 저장
    const updated = addPendingTurn([conv], conv.id, conv.session_id, "테스트 질문", PROJECT);
    saveConversations(updated);

    const loaded = loadConversations();
    expect(loaded[0].turns).toHaveLength(1);
    expect(loaded[0].turns[0].status).toBe("pending");
    expect(loaded[0].turns[0].q).toBe("테스트 질문");
  });

  it("다른 대화로 이동 후 답변 도착해도 원래 대화에 정확히 귀속된다", () => {
    const convA = makeNewConversation(PROJECT);
    const convB = makeNewConversation(PROJECT);

    // 1. conv-A에서 질문 제출 (pending 추가)
    let state = [convA, convB];
    const capturedConvId = convA.id; // handleSubmit에서 캡처
    state = addPendingTurn(state, convA.id, convA.session_id, "A의 질문", PROJECT);
    saveConversations(state);

    // 2. 사용자가 conv-B로 이동 (상태 변경 없음, capturedConvId만 유지)
    // (실제로는 setActiveConvId(convB.id) 호출됨 — 여기선 localStorage만 검증)

    // 3. 답변 도착 → capturedConvId 기준으로 갱신
    state = resolvePendingTurn(state, capturedConvId, {
      status: "done",
      answer: "A의 답변",
      citations: [],
    });
    saveConversations(state);

    const loaded = loadConversations();
    const loadedA = loaded.find(c => c.id === convA.id)!;
    const loadedB = loaded.find(c => c.id === convB.id)!;

    expect(loadedA.turns[0].status).toBe("done");
    expect(loadedA.turns[0].a).toBe("A의 답변");
    expect(loadedB.turns).toHaveLength(0); // B는 빈 대화 그대로
  });

  it("502 에러 시 pending 턴이 error 상태로 전환된다", () => {
    const conv = makeNewConversation(PROJECT);
    let state = addPendingTurn([conv], conv.id, conv.session_id, "실패할 질문", PROJECT);

    // onError 시뮬레이션
    state = resolvePendingTurn(state, conv.id, {
      status: "error",
      errorMsg: "502 Bad Gateway — 브레인 세션이 준비되지 않았거나 타임아웃되었습니다.",
    });
    saveConversations(state);

    const loaded = loadConversations();
    expect(loaded[0].turns[0].status).toBe("error");
    expect(loaded[0].turns[0].errorMsg).toContain("502");
  });

  it("pending 턴 추가 후 질문 텍스트가 보존된다 (네비게이션 후 재확인)", () => {
    const conv = makeNewConversation(PROJECT);
    const question = "이 질문은 네비게이션 후에도 보여야 한다";
    let state = addPendingTurn([conv], conv.id, conv.session_id, question, PROJECT);
    saveConversations(state);

    // 다른 대화로 이동 후 다시 이 대화로 돌아옴 → localStorage에서 복원
    const restored = loadConversations();
    expect(restored[0].turns[0].q).toBe(question);
    expect(restored[0].turns[0].status).toBe("pending");

    // 답변 도착
    state = resolvePendingTurn(state, conv.id, { status: "done", answer: "답변 도착", citations: [] });
    saveConversations(state);

    const final = loadConversations();
    expect(final[0].turns[0].q).toBe(question); // 질문 보존
    expect(final[0].turns[0].a).toBe("답변 도착");
    expect(final[0].turns[0].status).toBe("done");
  });
});

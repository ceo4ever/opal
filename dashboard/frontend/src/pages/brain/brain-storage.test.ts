/**
 * @header {
 *   "module": "brain-storage-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "BrainPage localStorage 이력 헬퍼 단위 테스트 — appendTurn·load/save·새 대화·복원 검증 + filterConversationsByProject(프로젝트별 분리) 검증 + makeNewConversation(FE UUID 발급) 검증 + addPendingTurn·resolvePendingTurn 낙관적 업데이트 검증. 네트워크 미사용.",
 *   "task": "022-260615-opd-opx-flex-pilot",
 *   "scenarios": ["H-15", "H-project-filter", "H-session-id", "H-optimistic-pending", "H-resolve-pending", "H-cross-conv-routing"]
 * }
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  loadConversations,
  saveConversations,
  appendTurnToConversation,
  filterConversationsByProject,
  makeNewConversation,
  projectDisplayName,
  addPendingTurn,
  resolvePendingTurn,
  type BrainConversation,
  type BrainTurn,
} from "./BrainPage";

/* ------------------------------------------------------------------ */
/* localStorage 모킹                                                     */
/* ------------------------------------------------------------------ */

const STORAGE_KEY = "opal-console:brain:conversations";

let _store: Record<string, string> = {};

const localStorageMock = {
  getItem: vi.fn((key: string) => _store[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { _store[key] = value; }),
  removeItem: vi.fn((key: string) => { delete _store[key]; }),
  clear: vi.fn(() => { _store = {}; }),
  get length() { return Object.keys(_store).length; },
  key: vi.fn(),
};

// happy-dom 환경에서 localStorage를 모킹
Object.defineProperty(globalThis, "localStorage", {
  value: localStorageMock,
  writable: true,
});

/* ------------------------------------------------------------------ */
/* 유틸                                                                  */
/* ------------------------------------------------------------------ */

function makeConv(id: string, sessionId: string = "sess-1", project: string | null = null): BrainConversation {
  return {
    id,
    session_id: sessionId,
    project,
    turns: [],
    created_at: Date.now(),
  };
}

function makeTurn(q: string, a: string): Omit<BrainTurn, "ts" | "status" | "errorMsg"> {
  return { q, a, citations: [] };
}

/* ------------------------------------------------------------------ */
/* 테스트                                                                */
/* ------------------------------------------------------------------ */

describe("brain localStorage 이력", () => {
  beforeEach(() => {
    _store = {};
    vi.clearAllMocks();
  });

  afterEach(() => {
    _store = {};
  });

  /* --- loadConversations --- */

  it("빈 저장소에서 빈 배열 반환", () => {
    expect(loadConversations()).toEqual([]);
  });

  it("저장된 대화를 복원한다", () => {
    const convs: BrainConversation[] = [makeConv("c1")];
    _store[STORAGE_KEY] = JSON.stringify(convs);
    const loaded = loadConversations();
    expect(loaded).toHaveLength(1);
    expect(loaded[0].id).toBe("c1");
  });

  it("JSON 파싱 실패 시 빈 배열 반환", () => {
    _store[STORAGE_KEY] = "not-json{{{";
    expect(loadConversations()).toEqual([]);
  });

  it("배열이 아닌 값 저장 시 빈 배열 반환", () => {
    _store[STORAGE_KEY] = JSON.stringify({ invalid: true });
    expect(loadConversations()).toEqual([]);
  });

  /* --- saveConversations --- */

  it("대화를 저장한다", () => {
    const convs: BrainConversation[] = [makeConv("c1")];
    saveConversations(convs);
    const raw = _store[STORAGE_KEY];
    expect(raw).toBeDefined();
    const parsed = JSON.parse(raw) as BrainConversation[];
    expect(parsed).toHaveLength(1);
    expect(parsed[0].id).toBe("c1");
  });

  it("50개 초과 시 최신 50개만 유지 (쿼터 보호)", () => {
    const convs: BrainConversation[] = Array.from({ length: 60 }, (_, i) =>
      makeConv(`c${i}`),
    );
    saveConversations(convs);
    const loaded = loadConversations();
    expect(loaded).toHaveLength(50);
    // 가장 최신(마지막 50개)만 유지
    expect(loaded[0].id).toBe("c10");
    expect(loaded[49].id).toBe("c59");
  });

  /* --- appendTurnToConversation --- */

  it("새 conversation에 첫 turn을 추가한다", () => {
    const convId = "new-conv";
    const result = appendTurnToConversation(
      [],
      convId,
      "sess-1",
      makeTurn("첫 질문", "첫 답변"),
      null,
    );
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(convId);
    expect(result[0].session_id).toBe("sess-1");
    expect(result[0].turns).toHaveLength(1);
    expect(result[0].turns[0].q).toBe("첫 질문");
    expect(result[0].turns[0].a).toBe("첫 답변");
    expect(result[0].turns[0].ts).toBeGreaterThan(0);
    expect(result[0].turns[0].status).toBe("done"); // appendTurnToConversation은 done 상태
  });

  it("기존 conversation에 turn을 append한다 (재질문)", () => {
    const conv = makeConv("c1", "sess-1");
    const withFirst = appendTurnToConversation(
      [conv],
      "c1",
      "sess-1",
      makeTurn("q1", "a1"),
      null,
    );
    // 재질문
    const withSecond = appendTurnToConversation(
      withFirst,
      "c1",
      "sess-1",
      makeTurn("q2", "a2"),
      null,
    );
    expect(withSecond[0].turns).toHaveLength(2);
    expect(withSecond[0].turns[1].q).toBe("q2");
  });

  it("재질문 시 session_id를 갱신한다 (BE resume)", () => {
    const conv = makeConv("c1", "old-sess");
    const result = appendTurnToConversation(
      [conv],
      "c1",
      "new-sess",
      makeTurn("q1", "a1"),
      null,
    );
    expect(result[0].session_id).toBe("new-sess");
  });

  it("다른 conversation은 변경하지 않는다", () => {
    const conv1 = makeConv("c1");
    const conv2 = makeConv("c2");
    const result = appendTurnToConversation(
      [conv1, conv2],
      "c1",
      "sess-1",
      makeTurn("q", "a"),
      null,
    );
    expect(result[1].turns).toHaveLength(0); // c2 불변
    expect(result[0].turns).toHaveLength(1); // c1만 변경
  });

  /* --- 저장 → 복원 왕복 --- */

  it("저장 후 복원 시 이력이 완전히 유지된다", () => {
    const convId = "c-roundtrip";
    const initial = appendTurnToConversation(
      [],
      convId,
      "sess-rt",
      { q: "복원 테스트 질문", a: "복원 테스트 답변", citations: [{ page: "p1", title: "T1", type: "concept" }] },
      "/path/to/project",
    );
    saveConversations(initial);

    const loaded = loadConversations();
    expect(loaded).toHaveLength(1);
    expect(loaded[0].id).toBe(convId);
    expect(loaded[0].turns[0].q).toBe("복원 테스트 질문");
    expect(loaded[0].turns[0].citations[0].title).toBe("T1");
  });

  /* --- 새 대화 (별도 conversation) --- */

  it("새 대화 ID를 사용하면 별도 conversation이 생성된다", () => {
    const existingConv = appendTurnToConversation(
      [],
      "old-conv",
      "sess-old",
      makeTurn("구 질문", "구 답변"),
      null,
    );

    // 새 대화: 기존 목록에 새 convId로 추가
    const withNew = appendTurnToConversation(
      existingConv,
      "new-conv",
      "sess-new",
      makeTurn("새 질문", "새 답변"),
      null,
    );

    expect(withNew).toHaveLength(2);
    expect(withNew[0].id).toBe("old-conv");
    expect(withNew[1].id).toBe("new-conv");
    expect(withNew[1].session_id).toBe("sess-new");
  });
});

/* ------------------------------------------------------------------ */
/* makeNewConversation — FE UUID 발급                                    */
/* ------------------------------------------------------------------ */

describe("makeNewConversation — 대화별 session_id 발급", () => {
  it("id와 session_id가 UUID 형식으로 생성된다", () => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    const conv = makeNewConversation("/path/to/project");
    expect(conv.id).toMatch(uuidRegex);
    expect(conv.session_id).toMatch(uuidRegex);
  });

  it("id와 session_id가 서로 다른 값이다", () => {
    const conv = makeNewConversation("/path/to/project");
    expect(conv.id).not.toBe(conv.session_id);
  });

  it("project 필드가 올바르게 설정된다", () => {
    const proj = "/path/to/my-project";
    const conv = makeNewConversation(proj);
    expect(conv.project).toBe(proj);
  });

  it("project가 null이어도 생성된다", () => {
    const conv = makeNewConversation(null);
    expect(conv.project).toBeNull();
    expect(conv.turns).toHaveLength(0);
  });

  it("turns가 빈 배열로 시작한다 (빈 대화)", () => {
    const conv = makeNewConversation("/p");
    expect(conv.turns).toEqual([]);
  });

  it("created_at이 현재 시간대에 있다", () => {
    const before = Date.now();
    const conv = makeNewConversation("/p");
    const after = Date.now();
    expect(conv.created_at).toBeGreaterThanOrEqual(before);
    expect(conv.created_at).toBeLessThanOrEqual(after);
  });

  it("두 번 호출하면 서로 다른 id와 session_id가 생성된다", () => {
    const conv1 = makeNewConversation("/p");
    const conv2 = makeNewConversation("/p");
    expect(conv1.id).not.toBe(conv2.id);
    expect(conv1.session_id).not.toBe(conv2.session_id);
  });
});

/* ------------------------------------------------------------------ */
/* 프로젝트별 이력 분리                                                  */
/* ------------------------------------------------------------------ */

describe("filterConversationsByProject — 프로젝트별 이력 분리", () => {
  const PA = "/path/to/pointail";
  const PB = "/path/to/ai-framework";

  const convA1 = makeConv("a1", "s1", PA);
  const convA2 = makeConv("a2", "s2", PA);
  const convB1 = makeConv("b1", "s3", PB);
  const convNull = makeConv("n1", "s4", null);

  it("특정 프로젝트 대화만 반환한다", () => {
    const all = [convA1, convA2, convB1, convNull];
    const result = filterConversationsByProject(all, PA);
    expect(result).toHaveLength(2);
    expect(result.every((c) => c.project === PA)).toBe(true);
  });

  it("다른 프로젝트 대화를 포함하지 않는다", () => {
    const all = [convA1, convA2, convB1];
    const result = filterConversationsByProject(all, PB);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("b1");
  });

  it("project=null이면 project 필드가 null인 대화만 반환한다", () => {
    const all = [convA1, convB1, convNull];
    const result = filterConversationsByProject(all, null);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("n1");
  });

  it("빈 목록에서 빈 배열 반환", () => {
    expect(filterConversationsByProject([], PA)).toEqual([]);
  });

  it("해당 프로젝트 대화가 없으면 빈 배열 반환", () => {
    const all = [convA1, convA2];
    expect(filterConversationsByProject(all, PB)).toEqual([]);
  });

  it("프로젝트 전환 시 이전 프로젝트 대화가 섞이지 않는다", () => {
    const all = [convA1, convA2, convB1];
    const resultA = filterConversationsByProject(all, PA);
    const resultB = filterConversationsByProject(all, PB);
    // A와 B 대화가 완전히 분리됨
    expect(resultA.map((c) => c.id)).not.toContain("b1");
    expect(resultB.map((c) => c.id)).not.toContain("a1");
    expect(resultB.map((c) => c.id)).not.toContain("a2");
  });
});

/* ------------------------------------------------------------------ */
/* projectDisplayName                                                    */
/* ------------------------------------------------------------------ */

describe("projectDisplayName — 표시용 짧은 이름 추출", () => {
  it("절대 경로의 마지막 세그먼트를 반환한다", () => {
    expect(projectDisplayName("/path/to/pointail")).toBe("pointail");
    expect(projectDisplayName("/Volumes/Data/AIStudio/workspace/ai-framework")).toBe("ai-framework");
  });

  it("null이면 null 반환", () => {
    expect(projectDisplayName(null)).toBeNull();
  });

  it("단일 경로면 그대로 반환", () => {
    expect(projectDisplayName("/myproject")).toBe("myproject");
  });
});

/* ------------------------------------------------------------------ */
/* addPendingTurn — 낙관적 턴 추가                                       */
/* ------------------------------------------------------------------ */

describe("addPendingTurn — 낙관적 pending 턴 추가", () => {
  beforeEach(() => {
    _store = {};
    vi.clearAllMocks();
  });

  it("빈 목록에 새 대화+pending 턴을 생성한다", () => {
    const result = addPendingTurn([], "conv-1", "sess-1", "첫 질문", "/proj");
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("conv-1");
    expect(result[0].turns).toHaveLength(1);
    expect(result[0].turns[0].q).toBe("첫 질문");
    expect(result[0].turns[0].a).toBe(""); // pending이므로 답변 없음
    expect(result[0].turns[0].citations).toEqual([]);
    expect(result[0].turns[0].status).toBe("pending");
    expect(result[0].turns[0].ts).toBeGreaterThan(0);
  });

  it("기존 대화에 pending 턴을 append한다", () => {
    const conv = makeConv("c1", "sess-1", "/proj");
    const result = addPendingTurn([conv], "c1", "sess-1", "추가 질문", "/proj");
    expect(result[0].turns).toHaveLength(1);
    expect(result[0].turns[0].status).toBe("pending");
    expect(result[0].turns[0].q).toBe("추가 질문");
  });

  it("다른 대화는 변경하지 않는다", () => {
    const conv1 = makeConv("c1", "sess-1", "/proj");
    const conv2 = makeConv("c2", "sess-2", "/proj");
    const result = addPendingTurn([conv1, conv2], "c1", "sess-1", "질문", "/proj");
    expect(result[1].turns).toHaveLength(0); // c2 불변
    expect(result[0].turns).toHaveLength(1); // c1만 변경
  });

  it("project=null이어도 정상 생성된다", () => {
    const result = addPendingTurn([], "conv-null", "sess-null", "질문", null);
    expect(result[0].project).toBeNull();
    expect(result[0].turns[0].status).toBe("pending");
  });

  it("pending 턴 추가 후 저장-복원하면 status가 유지된다", () => {
    const result = addPendingTurn([], "c-save", "sess-save", "저장 테스트", "/proj");
    saveConversations(result);
    const loaded = loadConversations();
    expect(loaded[0].turns[0].status).toBe("pending");
    expect(loaded[0].turns[0].q).toBe("저장 테스트");
  });
});

/* ------------------------------------------------------------------ */
/* resolvePendingTurn — pending 턴 갱신                                  */
/* ------------------------------------------------------------------ */

describe("resolvePendingTurn — pending 턴을 done/error로 갱신", () => {
  function makeConvWithPending(id: string, question: string): BrainConversation {
    return {
      id,
      session_id: "sess-1",
      project: "/proj",
      turns: [{
        q: question,
        a: "",
        citations: [],
        ts: Date.now(),
        status: "pending",
      }],
      created_at: Date.now(),
    };
  }

  it("마지막 pending 턴을 done으로 갱신한다", () => {
    const conv = makeConvWithPending("c1", "테스트 질문");
    const result = resolvePendingTurn([conv], "c1", {
      status: "done",
      answer: "테스트 답변",
      citations: [{ page: "p1", title: "T1", type: "concept" }],
    });

    expect(result[0].turns[0].status).toBe("done");
    expect(result[0].turns[0].a).toBe("테스트 답변");
    expect(result[0].turns[0].citations).toHaveLength(1);
    expect(result[0].turns[0].citations[0].title).toBe("T1");
    expect(result[0].turns[0].q).toBe("테스트 질문"); // 질문은 보존
  });

  it("마지막 pending 턴을 error로 갱신한다", () => {
    const conv = makeConvWithPending("c1", "실패 질문");
    const result = resolvePendingTurn([conv], "c1", {
      status: "error",
      errorMsg: "502 Bad Gateway",
    });

    expect(result[0].turns[0].status).toBe("error");
    expect(result[0].turns[0].errorMsg).toBe("502 Bad Gateway");
    expect(result[0].turns[0].q).toBe("실패 질문"); // 질문은 보존
  });

  it("capturedConvId가 다른 대화는 변경하지 않는다", () => {
    const conv1 = makeConvWithPending("c1", "질문1");
    const conv2 = makeConvWithPending("c2", "질문2");
    const result = resolvePendingTurn([conv1, conv2], "c1", {
      status: "done",
      answer: "답변1",
      citations: [],
    });

    expect(result[0].turns[0].status).toBe("done"); // c1 갱신
    expect(result[1].turns[0].status).toBe("pending"); // c2 불변
  });

  it("pending 턴이 없는 대화는 변경하지 않는다", () => {
    const conv: BrainConversation = {
      id: "c-no-pending",
      session_id: "sess",
      project: "/proj",
      turns: [{
        q: "q",
        a: "a",
        citations: [],
        ts: Date.now(),
        status: "done",
      }],
      created_at: Date.now(),
    };
    const result = resolvePendingTurn([conv], "c-no-pending", {
      status: "done",
      answer: "new answer",
      citations: [],
    });
    // 기존 done 턴은 변경되지 않음
    expect(result[0].turns[0].a).toBe("a");
    expect(result[0].turns[0].status).toBe("done");
  });

  it("여러 턴 중 마지막 pending 턴만 갱신한다", () => {
    const conv: BrainConversation = {
      id: "c-multi",
      session_id: "sess",
      project: "/proj",
      turns: [
        { q: "q1", a: "a1", citations: [], ts: Date.now() - 2000, status: "done" },
        { q: "q2", a: "a2", citations: [], ts: Date.now() - 1000, status: "done" },
        { q: "q3", a: "",   citations: [], ts: Date.now(),         status: "pending" },
      ],
      created_at: Date.now(),
    };
    const result = resolvePendingTurn([conv], "c-multi", {
      status: "done",
      answer: "답변3",
      citations: [],
    });
    expect(result[0].turns[0].status).toBe("done"); // 기존 done 유지
    expect(result[0].turns[1].status).toBe("done"); // 기존 done 유지
    expect(result[0].turns[2].status).toBe("done"); // pending → done
    expect(result[0].turns[2].a).toBe("답변3");
  });

  it("존재하지 않는 capturedConvId로 호출 시 원본 반환", () => {
    const conv = makeConvWithPending("c1", "질문");
    const result = resolvePendingTurn([conv], "non-existent", {
      status: "done",
      answer: "답변",
      citations: [],
    });
    // 변경 없이 원본 반환
    expect(result[0].turns[0].status).toBe("pending");
  });
});

/* ------------------------------------------------------------------ */
/* 캡처 convId 귀속 — 대화 전환 중 답변 오라우팅 방지                     */
/* ------------------------------------------------------------------ */

describe("답변 캡처 convId 귀속 — 대화 전환 오라우팅 방지", () => {
  it("pending 추가(conv-A) → 다른 대화(conv-B) 전환 → conv-A에만 답변 귀속", () => {
    // 시나리오: conv-A에서 질문 → 대기 중 conv-B로 이동 → 답변 conv-A에 귀속
    const convA: BrainConversation = {
      id: "conv-A",
      session_id: "sess-A",
      project: "/proj",
      turns: [],
      created_at: Date.now(),
    };
    const convB: BrainConversation = {
      id: "conv-B",
      session_id: "sess-B",
      project: "/proj",
      turns: [{ q: "B의 기존 질문", a: "B의 기존 답변", citations: [], ts: Date.now() - 1000, status: "done" }],
      created_at: Date.now() - 5000,
    };

    // 1. conv-A에 pending 턴 추가 (질문 제출)
    const afterPending = addPendingTurn([convA, convB], "conv-A", "sess-A", "A의 질문", "/proj");
    expect(afterPending.find(c => c.id === "conv-A")!.turns[0].status).toBe("pending");
    expect(afterPending.find(c => c.id === "conv-B")!.turns).toHaveLength(1); // B 불변

    // 2. 사용자가 conv-B로 이동 (activeConvId 변경 시뮬레이션 — capturedConvId는 "conv-A" 유지)
    const capturedConvId = "conv-A"; // handleSubmit에서 캡처된 값

    // 3. 답변 도착 → capturedConvId(conv-A) 기준으로 갱신
    const afterResolve = resolvePendingTurn(afterPending, capturedConvId, {
      status: "done",
      answer: "A의 답변",
      citations: [],
    });

    const resolvedA = afterResolve.find(c => c.id === "conv-A")!;
    const resolvedB = afterResolve.find(c => c.id === "conv-B")!;

    // conv-A의 pending 턴이 done으로 갱신됨
    expect(resolvedA.turns[0].status).toBe("done");
    expect(resolvedA.turns[0].a).toBe("A의 답변");

    // conv-B는 전혀 변경되지 않음
    expect(resolvedB.turns).toHaveLength(1);
    expect(resolvedB.turns[0].q).toBe("B의 기존 질문");
  });

  it("각 대화에 독립적으로 pending 추가 후 순서대로 resolve", () => {
    const convA: BrainConversation = { id: "conv-A", session_id: "sess-A", project: "/proj", turns: [], created_at: Date.now() };
    const convB: BrainConversation = { id: "conv-B", session_id: "sess-B", project: "/proj", turns: [], created_at: Date.now() };

    // 두 대화에 각각 pending 추가
    let state = addPendingTurn([convA, convB], "conv-A", "sess-A", "A 질문", "/proj");
    state = addPendingTurn(state, "conv-B", "sess-B", "B 질문", "/proj");

    expect(state.find(c => c.id === "conv-A")!.turns[0].status).toBe("pending");
    expect(state.find(c => c.id === "conv-B")!.turns[0].status).toBe("pending");

    // conv-A 답변 먼저 도착
    state = resolvePendingTurn(state, "conv-A", { status: "done", answer: "A 답변", citations: [] });
    expect(state.find(c => c.id === "conv-A")!.turns[0].status).toBe("done");
    expect(state.find(c => c.id === "conv-B")!.turns[0].status).toBe("pending"); // B는 여전히 pending

    // conv-B 답변 도착
    state = resolvePendingTurn(state, "conv-B", { status: "done", answer: "B 답변", citations: [] });
    expect(state.find(c => c.id === "conv-B")!.turns[0].status).toBe("done");
    expect(state.find(c => c.id === "conv-B")!.turns[0].a).toBe("B 답변");
  });

  it("에러 응답도 capturedConvId에만 귀속된다", () => {
    const convA: BrainConversation = {
      id: "conv-A",
      session_id: "sess-A",
      project: "/proj",
      turns: [],
      created_at: Date.now(),
    };
    const convB: BrainConversation = {
      id: "conv-B",
      session_id: "sess-B",
      project: "/proj",
      turns: [{ q: "B 질문", a: "B 답변", citations: [], ts: Date.now(), status: "done" }],
      created_at: Date.now(),
    };

    let state = addPendingTurn([convA, convB], "conv-A", "sess-A", "A 질문", "/proj");
    state = resolvePendingTurn(state, "conv-A", { status: "error", errorMsg: "502 Bad Gateway" });

    const resolvedA = state.find(c => c.id === "conv-A")!;
    const resolvedB = state.find(c => c.id === "conv-B")!;

    expect(resolvedA.turns[0].status).toBe("error");
    expect(resolvedA.turns[0].errorMsg).toBe("502 Bad Gateway");
    expect(resolvedB.turns[0].status).toBe("done"); // B 불변
  });
});

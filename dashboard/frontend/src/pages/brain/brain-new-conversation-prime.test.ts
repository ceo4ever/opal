/**
 * @header {
 *   "module": "brain-new-conversation-prime-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "새 대화(handleNewSession)→재프라임 경로 단위 테스트 — prime 페이로드에 session_id 포함 + query에 동일 session_id 포함 + makeSessionId() 신규 헬퍼(mount·새 대화마다 새 세션 발급) 검증 + addPendingTurn(turns, question) 2-인자 신규 시그니처 누적 검증. fetch mock 사용. [T063] 멀티대화 배열(BrainConversation) 전제의 대화별 독립성·localStorage 이력·프로젝트 필터 테스트는 단일 세션 리팩터로 개념이 소멸해 제거하고, makeNewConversation 참조를 makeSessionId로 치환.",
 *   "exports": [],
 *   "task": "022-260615-opd-opx-flex-pilot / 063-260715-opd-콘솔-브레인-세션-단순화",
 *   "scenarios": ["new-conv-prime", "T063-S-6", "T063-S-8"],
 *   "changelog": ["2026-07-15 T063 CLOSE: @header exports 필드 추가(누락, 코드 변경 없음)"]
 * }
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  makeSessionId,
  addPendingTurn,
  type BrainTurn,
} from "./BrainPage";

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

describe("새 대화(handleNewSession) 흐름 시뮬레이션 — fetch mock", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("새 대화 클릭 시 prime에 새 session_id를 보내고 query에도 같은 session_id를 보낸다", async () => {
    const primeCalls: unknown[] = [];
    const queryCalls: unknown[] = [];

    // handleNewSession() 시뮬레이션: 새 세션 발급 (makeSessionId, R-5)
    const sessionId = makeSessionId();

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

    // 새 대화 클릭 시 즉시 prime 호출 시뮬레이션
    await mockFetch("/api/brain/prime", {
      method: "POST",
      body: JSON.stringify(buildPrimePayload(PROJECT, sessionId)),
    });

    // 이후 질문 제출 시 query 호출 시뮬레이션 (같은 session_id)
    await mockFetch("/api/brain/query", {
      method: "POST",
      body: JSON.stringify(buildQueryPayload("새로운 질문", PROJECT, sessionId)),
    });

    // prime에 session_id 포함 확인
    expect(primeCalls).toHaveLength(1);
    expect(primeCalls[0]).toMatchObject({ project: PROJECT, session_id: sessionId });
    expect(primeCalls[0]).not.toHaveProperty("new_conversation");

    // query에 동일한 session_id 포함 확인
    expect(queryCalls).toHaveLength(1);
    expect(queryCalls[0]).toMatchObject({
      question: "새로운 질문",
      project: PROJECT,
      session_id: sessionId,
    });
  });
});

/* ------------------------------------------------------------------ */
/* [T063/L1-R4] addPendingTurn — turns 배열 신규 시그니처 (RED)          */
/* 태스크 063 PLAN.md §3.1.2: addPendingTurn(turns: BrainTurn[], question: string) */
/* — conversationId·sessionId·project 인자 제거(단일 세션 turns[] 상태 전제, F-001/F-002). */
/* 현재 시그니처는 addPendingTurn(conversations, conversationId, sessionId, question, project) */
/* 5개 인자이므로, 신규 2개-인자 호출 시 2번째 인자(질문 텍스트)가 conversationId 자리에 */
/* 들어가고 question 자리는 undefined가 되어, 반환된 원소는 BrainTurn이 아니라 */
/* BrainConversation 래퍼 객체({id, session_id, project, turns, created_at})가 된다. */
/* → turns[0].q / turns[0].status 등 BrainTurn 평평한(flat) 필드 접근이 모두 undefined가 */
/*   되어 GREEN(turns 기반 리팩터) 전까지 아래 테스트는 FAIL해야 한다(RED). */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R4] addPendingTurn — turns 배열 신규 시그니처 (RED)", () => {
  it("동일 세션에서 addPendingTurn(turns, question)을 2회 호출하면 동일 turns 배열에 2건이 순서대로 누적되어야 한다", () => {
    let turns: BrainTurn[] = [];

    turns = addPendingTurn(turns, "첫 질문");
    turns = addPendingTurn(turns, "두 번째 질문");

    expect(turns).toHaveLength(2); // 신규 시그니처 기준 기대값 — 세션 유지, 동일 배열에 2턴 누적
    expect(turns[0].q).toBe("첫 질문");
    expect(turns[0].status).toBe("pending");
    expect(turns[1].q).toBe("두 번째 질문");
    expect(turns[1].status).toBe("pending");
  });
});

/* ------------------------------------------------------------------ */
/* [T063/L1-R3] makeSessionId — mount마다 새 세션 발급 신규 헬퍼 (RED)    */
/* 태스크 063 PLAN.md §3.2.2: const [sessionId] = useState(() => crypto.randomUUID()) */
/* + 선택적 순수 헬퍼 makeSessionId(): string { return crypto.randomUUID(); } */
/* 현재는 makeNewConversation(project)이 conv id + session_id 2개를 한 번에 발급하며, */
/* 세션 단독 발급용 makeSessionId 헬퍼는 BrainPage.tsx에 아직 export되지 않았다. */
/* 정적 import 시 모듈 전체 로드가 다른 케이스에 영향을 주지 않도록 동적 import로 */
/* 네임스페이스만 확인한다 — GREEN(makeSessionId export) 전까지 아래 테스트는 FAIL한다(RED). */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R3] makeSessionId — 신규 헬퍼 (RED)", () => {
  it("makeSessionId()가 export되어 있고, 호출마다 새 UUID를 반환해야 한다 (재mount 시뮬레이션)", async () => {
    const mod = (await import("./BrainPage")) as unknown as {
      makeSessionId?: () => string;
    };

    // 신규 헬퍼 미존재 → 현재 mod.makeSessionId는 undefined이므로 아래 단언에서 FAIL한다(RED)
    expect(typeof mod.makeSessionId).toBe("function");

    const first = mod.makeSessionId!();
    const second = mod.makeSessionId!();
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    expect(first).toMatch(uuidRegex);
    expect(second).toMatch(uuidRegex);
    expect(first).not.toBe(second); // 재mount마다 새 세션 — R-3 핵심
  });
});

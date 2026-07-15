/**
 * @header {
 *   "module": "brain-storage-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "BrainPage 단일 세션 turns[] 헬퍼 단위 테스트 — addPendingTurn·resolvePendingTurn(turns 기반 2-인자 시그니처) 낙관적 업데이트 검증 + projectDisplayName 검증 + localStorage 비영속 검증(R-2 — 질의·응답 흐름 후 opal-console:brain:* 키 미기록, 복원 경로 부재로 재mount 시 turns=[]). [T063] 멀티대화관리·localStorage 이력 헬퍼(loadConversations/saveConversations/filterConversationsByProject/makeNewConversation/appendTurnToConversation, 타입 BrainConversation)가 리팩터로 제거되어 해당 테스트 전건 함께 제거. 네트워크 미사용.",
 *   "exports": [],
 *   "task": "022-260615-opd-opx-flex-pilot / 063-260715-opd-콘솔-브레인-세션-단순화",
 *   "scenarios": ["H-optimistic-pending", "H-resolve-pending", "T063-S-10", "T063-S-11"],
 *   "changelog": ["2026-07-15 T063 CLOSE: @header exports 필드 추가(누락, 코드 변경 없음)"]
 * }
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  projectDisplayName,
  addPendingTurn,
  resolvePendingTurn,
  type BrainTurn,
} from "./BrainPage";

/* ------------------------------------------------------------------ */
/* addPendingTurn — 낙관적 pending 턴 추가 (turns 기반 2-인자 시그니처)   */
/* ------------------------------------------------------------------ */

describe("addPendingTurn — 낙관적 pending 턴 추가 (turns 기반)", () => {
  it("빈 배열에 새 pending 턴을 생성한다", () => {
    const result = addPendingTurn([], "첫 질문");
    expect(result).toHaveLength(1);
    expect(result[0].q).toBe("첫 질문");
    expect(result[0].a).toBe(""); // pending이므로 답변 없음
    expect(result[0].citations).toEqual([]);
    expect(result[0].status).toBe("pending");
    expect(result[0].ts).toBeGreaterThan(0);
  });

  it("기존 turns 뒤에 pending 턴을 append한다 (기존 턴은 불변)", () => {
    const existing: BrainTurn[] = [
      { q: "이전 질문", a: "이전 답변", citations: [], ts: Date.now() - 1000, status: "done" },
    ];
    const result = addPendingTurn(existing, "새 질문");
    expect(result).toHaveLength(2);
    expect(result[0].status).toBe("done"); // 기존 턴 불변
    expect(result[0].q).toBe("이전 질문");
    expect(result[1].q).toBe("새 질문");
    expect(result[1].status).toBe("pending");
  });
});

/* ------------------------------------------------------------------ */
/* resolvePendingTurn — pending 턴 갱신 (turns 기반 2-인자 시그니처)      */
/* ------------------------------------------------------------------ */

describe("resolvePendingTurn — pending 턴을 done/error로 갱신 (turns 기반)", () => {
  it("마지막 pending 턴을 done으로 갱신한다", () => {
    const turns: BrainTurn[] = [
      { q: "테스트 질문", a: "", citations: [], ts: Date.now(), status: "pending" },
    ];
    const result = resolvePendingTurn(turns, {
      status: "done",
      answer: "테스트 답변",
      citations: [{ page: "p1", title: "T1", type: "concept" }],
    });

    expect(result[0].status).toBe("done");
    expect(result[0].a).toBe("테스트 답변");
    expect(result[0].citations).toHaveLength(1);
    expect(result[0].citations[0].title).toBe("T1");
    expect(result[0].q).toBe("테스트 질문"); // 질문은 보존
  });

  it("마지막 pending 턴을 error로 갱신한다", () => {
    const turns: BrainTurn[] = [
      { q: "실패 질문", a: "", citations: [], ts: Date.now(), status: "pending" },
    ];
    const result = resolvePendingTurn(turns, {
      status: "error",
      errorMsg: "502 Bad Gateway",
    });

    expect(result[0].status).toBe("error");
    expect(result[0].errorMsg).toBe("502 Bad Gateway");
    expect(result[0].q).toBe("실패 질문"); // 질문은 보존
  });

  it("pending 턴이 없으면 turns를 변경하지 않는다", () => {
    const turns: BrainTurn[] = [
      { q: "q", a: "a", citations: [], ts: Date.now(), status: "done" },
    ];
    const result = resolvePendingTurn(turns, {
      status: "done",
      answer: "new answer",
      citations: [],
    });
    // 기존 done 턴은 변경되지 않음
    expect(result[0].a).toBe("a");
    expect(result[0].status).toBe("done");
  });

  it("여러 턴 중 마지막 pending 턴만 갱신한다", () => {
    const turns: BrainTurn[] = [
      { q: "q1", a: "a1", citations: [], ts: Date.now() - 2000, status: "done" },
      { q: "q2", a: "a2", citations: [], ts: Date.now() - 1000, status: "done" },
      { q: "q3", a: "", citations: [], ts: Date.now(), status: "pending" },
    ];
    const result = resolvePendingTurn(turns, {
      status: "done",
      answer: "답변3",
      citations: [],
    });
    expect(result[0].status).toBe("done"); // 기존 done 유지
    expect(result[1].status).toBe("done"); // 기존 done 유지
    expect(result[2].status).toBe("done"); // pending → done
    expect(result[2].a).toBe("답변3");
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
/* [T063/L1-R5] resolvePendingTurn — turns 배열 신규 시그니처 (RED)      */
/* 태스크 063 PLAN.md §3.1.2/§3.2.1: resolvePendingTurn(turns: BrainTurn[], resolution) */
/* — capturedConvId 인자 제거(세션 오귀속 가드는 F-002의 capturedSessionId로 이동). */
/* 현재 시그니처는 resolvePendingTurn(conversations, capturedConvId, resolution) */
/* 3개 인자이므로, 신규 2개-인자 호출 시 resolution 객체가 capturedConvId 자리에 */
/* 들어가 `c.id !== capturedConvId`가 항상 참이 되어 turns가 전혀 갱신되지 않는다. */
/* → GREEN 구현(turns 기반 단일 상태 리팩터) 전까지 아래 테스트는 FAIL해야 한다(RED). */
/* ------------------------------------------------------------------ */

describe("[T063/L1-R5] resolvePendingTurn — turns 배열 신규 시그니처 (RED)", () => {
  it("capturedConvId 인자 없이 resolvePendingTurn(turns, resolution) 호출 시 마지막 pending 턴이 done으로 갱신되어야 한다", () => {
    let turns: BrainTurn[] = [
      { q: "질문1", a: "", citations: [], ts: Date.now(), status: "pending" },
    ];

    turns = resolvePendingTurn(turns, { status: "done", answer: "답변1", citations: [] });

    expect(turns).toHaveLength(1);
    expect(turns[0].status).toBe("done"); // 신규 시그니처 기준 기대값 — 현재 구현은 갱신 못 하고 "pending" 잔존
    expect(turns[0].a).toBe("답변1");
    expect(turns[0].q).toBe("질문1"); // 질문은 보존되어야 한다
  });

  it("capturedConvId 인자 없이 resolvePendingTurn(turns, resolution) 호출 시 error로도 갱신되어야 한다", () => {
    let turns: BrainTurn[] = [
      { q: "질문2", a: "", citations: [], ts: Date.now(), status: "pending" },
    ];

    turns = resolvePendingTurn(turns, { status: "error", errorMsg: "502 Bad Gateway" });

    expect(turns[0].status).toBe("error");
    expect(turns[0].errorMsg).toBe("502 Bad Gateway");
  });
});

/* ------------------------------------------------------------------ */
/* [T063/L1-R2] localStorage 비영속 — opal-console:brain:* 키 미기록      */
/* 태스크 063 PLAN.md §3.1.1/§3.1.2 (R-2): FE는 인메모리 turns[] 단일 상태만 */
/* 사용하고 localStorage 이력 영속을 제거했다(GREEN). 검증 방식은 제거된      */
/* saveConversations/loadConversations 호출이 아니라, 실 헬퍼(turns 기반    */
/* addPendingTurn/resolvePendingTurn)가 handleSubmit과 동일한 순서로        */
/* 호출되어도 localStorage에 어떤 브레인 키도 기록하지 않음을 확인하고,      */
/* 복원 경로(loadConversations류) 자체가 모듈에서 완전히 제거되어           */
/* "재mount 시 turns=[]"가 항상 성립함을 확인한다.                          */
/* ------------------------------------------------------------------ */

// localStorage 모킹 (getItem/setItem/removeItem/clear 호출 여부를 spy로 관찰)
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

describe("[T063/L1-R2] localStorage 비영속 — opal-console:brain:* 키 미기록", () => {
  beforeEach(() => {
    _store = {};
    vi.clearAllMocks();
  });

  afterEach(() => {
    _store = {};
  });

  it("질의·응답 흐름(제출→pending 추가→done 갱신) 후 localStorage에 opal-console:brain:* 키가 기록되지 않는다", () => {
    // 실 프로덕션 handleSubmit과 동일한 흐름: pending 턴 추가 → 잡 done 수신 시 resolve.
    // 두 헬퍼 모두 순수 함수로 turns 배열만 조작하며 localStorage를 전혀 건드리지 않는다.
    let turns: BrainTurn[] = [];
    turns = addPendingTurn(turns, "질문");
    turns = resolvePendingTurn(turns, { status: "done", answer: "답변", citations: [] });

    expect(turns[0].status).toBe("done"); // 흐름 자체는 정상 동작(선행 조건)

    expect(localStorageMock.setItem).not.toHaveBeenCalled();
    const brainKeys = Object.keys(_store).filter((k) => k.startsWith("opal-console:brain:"));
    expect(brainKeys).toHaveLength(0);
  });

  it("재mount 시 turns를 복원하는 저장소 읽기 메커니즘이 모듈에 존재하지 않는다 (항상 빈 배열로 시작)", async () => {
    // 신규 설계(BrainPage.tsx: `useState<BrainTurn[]>([])`)는 mount 시 어떤 스토리지도 읽지 않는다.
    // 과거 loadConversations/saveConversations류의 복원·저장 함수가 모듈에서 완전히 제거됐다 —
    // 읽어올 대상 자체가 없으므로 재mount는 항상 turns=[]로 시작한다(R-2 핵심).
    const mod = (await import("./BrainPage")) as Record<string, unknown>;
    expect(mod.loadConversations).toBeUndefined();
    expect(mod.saveConversations).toBeUndefined();
  });
});

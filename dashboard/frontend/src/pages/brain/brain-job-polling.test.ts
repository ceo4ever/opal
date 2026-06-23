/**
 * @header {
 *   "module": "brain-job-polling-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "잡 폴링 순수 헬퍼 단위 테스트 — S-7(폴링 done 수신 → resolvePendingTurn done 전이), S-10(폴링 error 수신 → resolvePendingTurn error graceful). jobResponseToResolution·jobPollingInterval 헬퍼 import 실패로 RED(GREEN 워커가 BrainPage.tsx에 구현·export 예정).",
 *   "task": "037-260622-opd-브레인질의-타임아웃-견고화",
 *   "scenarios": ["S-7", "S-10"]
 * }
 */

import { describe, it, expect } from "vitest";

// [RED 이유]
// jobResponseToResolution 과 jobPollingInterval 은 아직 BrainPage.tsx에 구현·export 되지 않았다.
// 아래 import가 실패하거나(모듈 미존재) named export 미노출로 undefined가 되어 테스트가 FAIL된다.
// GREEN 워커가 BrainPage.tsx(또는 동일 폴더 모듈)에 두 함수를 export하면 PASS로 전환된다.
import {
  jobResponseToResolution,
  jobPollingInterval,
  resolvePendingTurn,
  addPendingTurn,
  type BrainConversation,
} from "./BrainPage";

/* ------------------------------------------------------------------ */
/* BrainJobResponse 타입 (FE 관점 — BE BrainJobResponse와 동형)         */
/* GREEN 구현 시 BrainPage.tsx에서 export 되어야 한다.                    */
/* ------------------------------------------------------------------ */

interface BrainJobResponse {
  job_id: string;
  status: "pending" | "done" | "error";
  answer: string;
  citations: { page: string; title: string; type: string; score?: number }[];
  error_msg: string;
}

/* ------------------------------------------------------------------ */
/* 유틸                                                                  */
/* ------------------------------------------------------------------ */

function makeConvWithPending(id: string, question: string): BrainConversation {
  return {
    id,
    session_id: "sess-1",
    project: "/proj",
    turns: [
      {
        q: question,
        a: "",
        citations: [],
        ts: Date.now(),
        status: "pending",
      },
    ],
    created_at: Date.now(),
  };
}

/* ------------------------------------------------------------------ */
/* S-7: 잡 폴링 done 수신 → 해당 턴 done 전이 (answer/citations 렌더)    */
/* ------------------------------------------------------------------ */

describe("S-7: jobResponseToResolution — done 전이", () => {
  /**
   * [RED 이유] jobResponseToResolution 은 BrainPage.tsx에 미존재.
   * GREEN 구현 시 BrainPage.tsx에 다음 시그니처로 export 되어야 한다:
   *
   *   export function jobResponseToResolution(job: BrainJobResponse):
   *     | { status: "done"; answer: string; citations: CitationItem[] }
   *     | { status: "error"; errorMsg: string }
   *     | null  // status="pending" 시 null — 아직 완료 아님
   */

  it("status=done 잡 응답을 resolvePendingTurn에 맞는 done 객체로 변환한다", () => {
    const job: BrainJobResponse = {
      job_id: "job-abc",
      status: "done",
      answer: "테스트 답변 내용",
      citations: [{ page: "p1", title: "타이틀1", type: "concept" }],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);

    expect(resolution).not.toBeNull();
    expect(resolution!.status).toBe("done");
    // done 분기에는 answer / citations 가 있어야 한다
    if (resolution && resolution.status === "done") {
      expect(resolution.answer).toBe("테스트 답변 내용");
      expect(resolution.citations).toHaveLength(1);
      expect(resolution.citations[0].title).toBe("타이틀1");
    }
  });

  it("done 변환 결과를 resolvePendingTurn에 적용하면 턴이 done으로 갱신된다", () => {
    const conv = makeConvWithPending("conv-1", "질문1");
    const job: BrainJobResponse = {
      job_id: "job-abc",
      status: "done",
      answer: "최종 답변",
      citations: [{ page: "p2", title: "T2", type: "concept", score: 0.9 }],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    const updated = resolvePendingTurn([conv], "conv-1", resolution!);

    expect(updated[0].turns[0].status).toBe("done");
    expect(updated[0].turns[0].a).toBe("최종 답변");
    expect(updated[0].turns[0].citations[0].title).toBe("T2");
    expect(updated[0].turns[0].q).toBe("질문1"); // 질문 보존
  });

  it("status=pending 잡 응답은 null을 반환한다 (아직 완료 아님)", () => {
    const job: BrainJobResponse = {
      job_id: "job-abc",
      status: "pending",
      answer: "",
      citations: [],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);

    // pending 상태에서는 resolvePendingTurn을 호출하지 않아야 함 → null 반환
    expect(resolution).toBeNull();
  });

  it("done 전이 후 폴링이 중단된다 (jobPollingInterval이 false 반환)", () => {
    // done 수신 후 refetchInterval을 false로 설정해 폴링 중단
    expect(jobPollingInterval("done")).toBe(false);
  });

  it("pending 상태에서는 2000ms 간격으로 폴링을 계속한다", () => {
    expect(jobPollingInterval("pending")).toBe(2000);
  });

  it("빈 citations 배열도 올바르게 변환된다", () => {
    const job: BrainJobResponse = {
      job_id: "job-xyz",
      status: "done",
      answer: "답변",
      citations: [],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);

    expect(resolution).not.toBeNull();
    expect(resolution!.status).toBe("done");
    if (resolution && resolution.status === "done") {
      expect(resolution.citations).toEqual([]);
    }
  });

  it("대화 전환 중에도 capturedConvId 기준으로 done 귀속이 정확하다", () => {
    // conv-A에서 질문 → 대기 중 conv-B로 이동 → conv-A에만 done 귀속
    let state = addPendingTurn([], "conv-A", "sess-A", "A 질문", "/proj");
    state = addPendingTurn(state, "conv-B", "sess-B", "B 질문", "/proj");

    const job: BrainJobResponse = {
      job_id: "job-A",
      status: "done",
      answer: "A 답변",
      citations: [],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    // capturedConvId = "conv-A" 로 귀속
    state = resolvePendingTurn(state, "conv-A", resolution!);

    const convA = state.find((c) => c.id === "conv-A")!;
    const convB = state.find((c) => c.id === "conv-B")!;

    expect(convA.turns[0].status).toBe("done");
    expect(convA.turns[0].a).toBe("A 답변");
    expect(convB.turns[0].status).toBe("pending"); // conv-B 불변
  });
});

/* ------------------------------------------------------------------ */
/* S-10: 잡 폴링 error 수신 → error 턴 graceful 표시                     */
/* ------------------------------------------------------------------ */

describe("S-10: jobResponseToResolution — error(잡 소멸) graceful", () => {
  /**
   * [RED 이유] jobResponseToResolution 은 BrainPage.tsx에 미존재.
   * GREEN 구현 시:
   *   status="error" → { status: "error", errorMsg: job.error_msg }
   *   error_msg가 비어 있으면 "잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)" 류 기본 메시지.
   */

  it("status=error 잡 응답을 error 객체로 변환한다", () => {
    const job: BrainJobResponse = {
      job_id: "job-dead",
      status: "error",
      answer: "",
      citations: [],
      error_msg: "잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)",
    };

    const resolution = jobResponseToResolution(job);

    expect(resolution).not.toBeNull();
    expect(resolution!.status).toBe("error");
    if (resolution && resolution.status === "error") {
      expect(resolution.errorMsg).toContain("잡을 찾을 수 없습니다");
    }
  });

  it("error 변환 결과를 resolvePendingTurn에 적용하면 턴이 error로 graceful 갱신된다 (빈 답 아님)", () => {
    const conv = makeConvWithPending("conv-err", "에러 질문");
    const job: BrainJobResponse = {
      job_id: "job-dead",
      status: "error",
      answer: "",
      citations: [],
      error_msg: "잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    const updated = resolvePendingTurn([conv], "conv-err", resolution!);

    const turn = updated[0].turns[0];
    // 빈 답(pending 잔존)이 아니라 error 상태로 graceful 전이되어야 한다
    expect(turn.status).toBe("error");
    // errorMsg는 빈 문자열이 아니어야 한다 — graceful 메시지 포함
    expect(turn.errorMsg).toBeTruthy();
    expect(turn.q).toBe("에러 질문"); // 질문 보존
  });

  it("error 수신 후 폴링이 중단된다 (jobPollingInterval이 false 반환)", () => {
    expect(jobPollingInterval("error")).toBe(false);
  });

  it("error_msg가 빈 문자열이어도 기본 메시지로 채워져 graceful 표시된다", () => {
    // BE가 error_msg 없이 error 상태를 반환하는 예외적 경우
    const job: BrainJobResponse = {
      job_id: "job-empty-msg",
      status: "error",
      answer: "",
      citations: [],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);

    expect(resolution).not.toBeNull();
    expect(resolution!.status).toBe("error");
    if (resolution && resolution.status === "error") {
      // 빈 문자열이 그대로 errorMsg로 전달되지 않아야 한다 (graceful fallback)
      // 구현 시: error_msg || "요청 처리 중 오류가 발생했습니다" 류 기본값
      expect(resolution.errorMsg).toBeTruthy();
    }
  });

  it("error 턴 적용 후 다른 대화는 변경되지 않는다", () => {
    let state = addPendingTurn([], "conv-err", "sess-err", "에러 질문", "/proj");
    state = addPendingTurn(state, "conv-ok", "sess-ok", "정상 질문", "/proj");

    const job: BrainJobResponse = {
      job_id: "job-dead",
      status: "error",
      answer: "",
      citations: [],
      error_msg: "세션 소멸",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    state = resolvePendingTurn(state, "conv-err", resolution!);

    const convErr = state.find((c) => c.id === "conv-err")!;
    const convOk = state.find((c) => c.id === "conv-ok")!;

    expect(convErr.turns[0].status).toBe("error");
    expect(convOk.turns[0].status).toBe("pending"); // 다른 대화 불변
  });
});

/* ------------------------------------------------------------------ */
/* jobPollingInterval — refetchInterval 판정 로직                       */
/* ------------------------------------------------------------------ */

describe("jobPollingInterval — refetchInterval 판정", () => {
  /**
   * [RED 이유] jobPollingInterval 은 BrainPage.tsx에 미존재.
   * GREEN 구현 시 BrainPage.tsx에 다음 시그니처로 export 되어야 한다:
   *
   *   export function jobPollingInterval(status: string | undefined): number | false
   *     - "done" | "error" → false  (폴링 중단)
   *     - "pending" | 그 외 → 2000  (2초 간격 폴링 계속)
   *     - undefined → 2000         (초기값 — 아직 응답 없음)
   */

  it("status=done이면 false를 반환한다 (폴링 중단)", () => {
    expect(jobPollingInterval("done")).toBe(false);
  });

  it("status=error이면 false를 반환한다 (폴링 중단)", () => {
    expect(jobPollingInterval("error")).toBe(false);
  });

  it("status=pending이면 2000을 반환한다 (2초 간격 계속)", () => {
    expect(jobPollingInterval("pending")).toBe(2000);
  });

  it("status=undefined(초기값)이면 2000을 반환한다", () => {
    expect(jobPollingInterval(undefined)).toBe(2000);
  });
});

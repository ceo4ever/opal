/**
 * @header {
 *   "module": "brain-job-polling-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "잡 폴링 순수 헬퍼 단위 테스트 — S-7(폴링 done 수신 → resolvePendingTurn done 전이), S-10(폴링 error 수신 → resolvePendingTurn error graceful). jobResponseToResolution·jobPollingInterval은 시그니처 불변(H-8 회귀 가드). [T063] resolvePendingTurn/addPendingTurn 호출부를 turns[] 기반 2-인자 신규 시그니처로 갱신 — 대화 배열(BrainConversation) 전제의 교차대화 귀속 케이스는 단일 세션 리팩터로 개념이 소멸해 제거(세션 오귀속 가드는 컴포넌트의 capturedSessionIdRef로 이동).",
 *   "exports": [],
 *   "task": "037-260622-opd-브레인질의-타임아웃-견고화 / 063-260715-opd-콘솔-브레인-세션-단순화",
 *   "scenarios": ["S-7", "S-10"],
 *   "changelog": ["2026-07-15 T063 CLOSE: @header exports 필드 추가(누락, 코드 변경 없음)"]
 * }
 */

import { describe, it, expect } from "vitest";

import {
  jobResponseToResolution,
  jobPollingInterval,
  resolvePendingTurn,
  type BrainTurn,
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

function makeTurnsWithPending(question: string): BrainTurn[] {
  return [
    {
      q: question,
      a: "",
      citations: [],
      ts: Date.now(),
      status: "pending",
    },
  ];
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
    const turns = makeTurnsWithPending("질문1");
    const job: BrainJobResponse = {
      job_id: "job-abc",
      status: "done",
      answer: "최종 답변",
      citations: [{ page: "p2", title: "T2", type: "concept", score: 0.9 }],
      error_msg: "",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    const updated = resolvePendingTurn(turns, resolution!);

    expect(updated[0].status).toBe("done");
    expect(updated[0].a).toBe("최종 답변");
    expect(updated[0].citations[0].title).toBe("T2");
    expect(updated[0].q).toBe("질문1"); // 질문 보존
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
    const turns = makeTurnsWithPending("에러 질문");
    const job: BrainJobResponse = {
      job_id: "job-dead",
      status: "error",
      answer: "",
      citations: [],
      error_msg: "잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)",
    };

    const resolution = jobResponseToResolution(job);
    expect(resolution).not.toBeNull();

    const updated = resolvePendingTurn(turns, resolution!);

    const turn = updated[0];
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

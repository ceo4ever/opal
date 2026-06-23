/**
 * @header {
 *   "module": "brain-status-test",
 *   "layer": "test",
 *   "domain": "brain",
 *   "description": "BrainPage 상태 게이팅 로직 단위 테스트 — state→isReady 도출, 폼 활성화 조건, 상태별 placeholder 문자열 검증 + 프로젝트 필수 게이팅(프로젝트 미선택 시 제출·폼 비활성) + session_id 기반 status query key 검증. 네트워크 미사용.",
 *   "task": "022-260615-opd-opx-flex-pilot",
 *   "scenarios": ["H-status-gate", "H-project-gate", "H-session-id-querykey"]
 * }
 */

import { describe, it, expect } from "vitest";

/* ------------------------------------------------------------------ */
/* 테스트 대상 순수 로직 (컴포넌트 외부 추출)                              */
/* ------------------------------------------------------------------ */

type BrainState = "idle" | "priming" | "ready" | "error";

function isReady(state: BrainState): boolean {
  return state === "ready";
}

/**
 * 프로젝트 필수 게이팅 + session_id 필수 게이팅을 포함한 제출 가능 여부.
 * project가 null이거나 session_id가 null이면 항상 false.
 */
function canSubmit(
  state: BrainState,
  questionTrimmed: string,
  isPending: boolean,
  project: string | null,
  session_id: string | null,
): boolean {
  if (project === null) return false;
  if (session_id === null) return false;
  return !!questionTrimmed && !isPending && isReady(state);
}

/**
 * 프로젝트 선택 여부를 포함한 placeholder 문자열.
 */
function getPlaceholder(state: BrainState, project: string | null): string {
  if (project === null) return "프로젝트를 선택하세요";
  return isReady(state)
    ? "질문을 입력하세요... (⌘Enter로 제출)"
    : "연동 완료 후 질문 가능합니다";
}

/**
 * 프로젝트 선택 여부를 포함한 상태 힌트.
 */
function getStatusHint(state: BrainState, turnCount: number, project: string | null): string {
  if (project === null) return "프로젝트 선택 필요";
  if (!isReady(state)) {
    if (state === "priming") return "브레인 연동 중…";
    if (state === "error") return "연동 실패 — 재시도 후 질문하세요";
    return "연동 준비 중…";
  }
  return turnCount > 0 ? `이어서 질문 중 (${turnCount}턴)` : "새 대화";
}

/**
 * status 폴링 queryKey 빌더 (대화별 격리).
 * project + session_id 포함.
 */
function buildStatusQueryKey(
  project: string | null,
  session_id: string | null,
): readonly unknown[] {
  return ["brain-status", project, session_id] as const;
}

/**
 * status API URL 빌더.
 */
function buildStatusUrl(project: string | null, session_id: string | null): string {
  const params = new URLSearchParams();
  if (project) params.set("project", project);
  if (session_id) params.set("session_id", session_id);
  return `/api/brain/status?${params.toString()}`;
}

/* ------------------------------------------------------------------ */
/* 테스트                                                                */
/* ------------------------------------------------------------------ */

describe("brain 상태 게이팅 — isReady", () => {
  it("ready 상태만 true 반환", () => {
    expect(isReady("ready")).toBe(true);
    expect(isReady("idle")).toBe(false);
    expect(isReady("priming")).toBe(false);
    expect(isReady("error")).toBe(false);
  });
});

describe("brain 상태 게이팅 — canSubmit (프로젝트 + session_id 포함)", () => {
  const proj = "/path/to/project";
  const sess = "session-uuid-1234";

  it("ready + 질문 있음 + isPending=false + 프로젝트 + session_id → 제출 가능", () => {
    expect(canSubmit("ready", "질문", false, proj, sess)).toBe(true);
  });

  it("priming 상태에서는 제출 불가", () => {
    expect(canSubmit("priming", "질문", false, proj, sess)).toBe(false);
  });

  it("idle 상태에서는 제출 불가", () => {
    expect(canSubmit("idle", "질문", false, proj, sess)).toBe(false);
  });

  it("error 상태에서는 제출 불가", () => {
    expect(canSubmit("error", "질문", false, proj, sess)).toBe(false);
  });

  it("ready 상태라도 질문이 빈 문자열이면 제출 불가", () => {
    expect(canSubmit("ready", "", false, proj, sess)).toBe(false);
  });

  it("ready 상태라도 isPending=true이면 제출 불가", () => {
    expect(canSubmit("ready", "질문", true, proj, sess)).toBe(false);
  });

  /* 프로젝트 필수 게이팅 */
  it("프로젝트 미선택(null)이면 ready 상태라도 제출 불가", () => {
    expect(canSubmit("ready", "질문", false, null, sess)).toBe(false);
  });

  it("프로젝트 미선택(null)이면 모든 상태에서 제출 불가", () => {
    const states: BrainState[] = ["idle", "priming", "ready", "error"];
    for (const state of states) {
      expect(canSubmit(state, "질문", false, null, sess)).toBe(false);
    }
  });

  /* session_id 필수 게이팅 */
  it("session_id가 null이면 ready 상태라도 제출 불가", () => {
    expect(canSubmit("ready", "질문", false, proj, null)).toBe(false);
  });

  it("session_id가 null이면 모든 상태에서 제출 불가", () => {
    const states: BrainState[] = ["idle", "priming", "ready", "error"];
    for (const state of states) {
      expect(canSubmit(state, "질문", false, proj, null)).toBe(false);
    }
  });
});

describe("brain 상태 게이팅 — placeholder (프로젝트 포함)", () => {
  const proj = "/path/to/project";

  it("ready + 프로젝트 선택 → 질문 입력 안내", () => {
    expect(getPlaceholder("ready", proj)).toContain("질문을 입력하세요");
  });

  it("priming + 프로젝트 선택 → 연동 완료 후 안내", () => {
    expect(getPlaceholder("priming", proj)).toBe("연동 완료 후 질문 가능합니다");
  });

  it("idle + 프로젝트 선택 → 연동 완료 후 안내", () => {
    expect(getPlaceholder("idle", proj)).toBe("연동 완료 후 질문 가능합니다");
  });

  it("error + 프로젝트 선택 → 연동 완료 후 안내", () => {
    expect(getPlaceholder("error", proj)).toBe("연동 완료 후 질문 가능합니다");
  });

  /* 프로젝트 필수 게이팅 */
  it("프로젝트 미선택(null) → 프로젝트 선택 안내", () => {
    expect(getPlaceholder("ready", null)).toBe("프로젝트를 선택하세요");
    expect(getPlaceholder("idle", null)).toBe("프로젝트를 선택하세요");
  });
});

describe("brain 상태 게이팅 — statusHint (프로젝트 포함)", () => {
  const proj = "/path/to/project";

  it("priming → 연동 중 메시지", () => {
    expect(getStatusHint("priming", 0, proj)).toBe("브레인 연동 중…");
  });

  it("error → 연동 실패 메시지", () => {
    expect(getStatusHint("error", 0, proj)).toBe("연동 실패 — 재시도 후 질문하세요");
  });

  it("idle → 준비 중 메시지", () => {
    expect(getStatusHint("idle", 0, proj)).toBe("연동 준비 중…");
  });

  it("ready + turn 없음 → 새 대화", () => {
    expect(getStatusHint("ready", 0, proj)).toBe("새 대화");
  });

  it("ready + turn 있음 → 이어서 질문 중 (N턴)", () => {
    expect(getStatusHint("ready", 3, proj)).toBe("이어서 질문 중 (3턴)");
  });

  /* 프로젝트 필수 게이팅 */
  it("프로젝트 미선택(null) → 프로젝트 선택 필요 메시지", () => {
    expect(getStatusHint("ready", 0, null)).toBe("프로젝트 선택 필요");
    expect(getStatusHint("priming", 0, null)).toBe("프로젝트 선택 필요");
    expect(getStatusHint("idle", 5, null)).toBe("프로젝트 선택 필요");
  });
});

describe("brain status queryKey — session_id 기반 대화별 격리", () => {
  const proj = "/path/to/project";
  const sess1 = "session-uuid-1111";
  const sess2 = "session-uuid-2222";

  it("queryKey에 project와 session_id가 포함된다", () => {
    const key = buildStatusQueryKey(proj, sess1);
    expect(key).toEqual(["brain-status", proj, sess1]);
  });

  it("session_id가 다르면 queryKey가 다르다 (대화별 격리)", () => {
    const key1 = buildStatusQueryKey(proj, sess1);
    const key2 = buildStatusQueryKey(proj, sess2);
    expect(key1).not.toEqual(key2);
  });

  it("session_id가 null이면 queryKey에 null이 포함된다", () => {
    const key = buildStatusQueryKey(proj, null);
    expect(key).toEqual(["brain-status", proj, null]);
  });

  it("project가 null이면 queryKey에 null이 포함된다", () => {
    const key = buildStatusQueryKey(null, sess1);
    expect(key).toEqual(["brain-status", null, sess1]);
  });
});

describe("brain status URL — session_id 파라미터 포함", () => {
  const proj = "/path/to/my project";
  const sess = "session-uuid-abcd";

  it("project와 session_id가 URL 파라미터로 포함된다", () => {
    const url = buildStatusUrl(proj, sess);
    // URLSearchParams는 공백을 + 로 인코딩하므로 파라미터 키/값 존재 여부만 확인
    expect(url).toContain("project=");
    expect(url).toContain("session_id=");
    expect(url).toContain(sess);
    // 슬래시가 %2F로 인코딩됨을 확인
    expect(url).toContain("%2F");
  });

  it("project가 null이면 project 파라미터가 없다", () => {
    const url = buildStatusUrl(null, sess);
    expect(url).not.toContain("project=");
    expect(url).toContain(`session_id=${sess}`);
  });

  it("session_id가 null이면 session_id 파라미터가 없다", () => {
    const url = buildStatusUrl("/path/to/proj", null);
    expect(url).not.toContain("session_id=");
    expect(url).toContain("project=");
  });
});

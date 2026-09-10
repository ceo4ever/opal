/**
 * @header {
 *   "module": "workbench-app-test",
 *   "layer": "test",
 *   "domain": "workbench",
 *   "description": "Task 생성부터 mention·재검증·Result 승인까지 DOM 상호작용 검증",
 *   "exports": []
 * }
 */

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { WorkbenchApp } from "./WorkbenchApp";

describe("Desktop Workbench mock flow", () => {
  beforeEach(() => localStorage.clear());
  afterEach(cleanup);

  it("creates a task, delegates a mention, reruns verification, and approves the result", async () => {
    render(<WorkbenchApp />);

    fireEvent.click(screen.getByRole("button", { name: /New Task/i }));
    fireEvent.click(within(screen.getByTestId("task-board")).getByRole("button", { name: /New Task/i }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("제목 *"), { target: { value: "세션 복원 점검" } });
    fireEvent.change(within(dialog).getByLabelText("설명 *"), { target: { value: "목업 상태 복원을 검토한다" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Task 만들기" }));
    expect((await screen.findAllByText("세션 복원 점검")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Workbench로 돌아가기" }));
    fireEvent.change(screen.getByLabelText("Agent 요청"), { target: { value: "@OPAL PM 로그인 오류를 구현해줘" } });
    fireEvent.click(screen.getByRole("button", { name: "요청 전송" }));
    expect(await screen.findByText(/Developer에게 위임했습니다/)).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Verification" }));
    fireEvent.click(await screen.findByRole("button", { name: /실패 검증 재실행/ }));
    expect(await screen.findByText(/3 checks PASS/)).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByRole("tab", { name: "Result" }));
    fireEvent.click(await screen.findByRole("switch", { name: /변경·검증/ }));
    fireEvent.click(screen.getByRole("button", { name: "결과 승인" }));
    expect(await screen.findByText("Result 승인 완료")).toBeInTheDocument();
  });
});

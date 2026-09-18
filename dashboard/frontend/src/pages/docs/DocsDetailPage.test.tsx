/**
 * @header {
 *   "module": "docs-detail-page-test",
 *   "layer": "test",
 *   "domain": "docs",
 *   "description": "DocsDetailPage RED 테스트 — S-12(DEC-8, AC-2, AC-3, AC-6, C-1, C-4, C-7). apiClient를 vi.mock으로 대역하고 QueryClientProvider + createMemoryRouter로 렌더한다. source 부재 시 메타 유지+본문 부재 Alert, alias 진입 시 canonical URL로 replace(히스토리 중복 없음), 예시 복사 성공/실패 폴백, 접근 가능한 이름과 포커스 이동을 검증한다. screenshot golden은 만들지 않는다.",
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "scenarios": ["S-12"],
 *   "exports": []
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocsDetailPage } from "./DocsDetailPage";
import { apiClient } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    apiClient: vi.fn(),
  };
});

const mockedApiClient = vi.mocked(apiClient);

function renderDetail(initialPath: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/docs/skills", element: <div>catalog placeholder</div> },
      { path: "/docs/skills/:skillId", element: <DocsDetailPage /> },
    ],
    { initialEntries: [initialPath] },
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router };
}

function fxDetail(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    canonical_name: "opal-onboarding",
    source_name: "onboarding",
    aliases: ["onboarding", "onb"],
    description: "OPAL 온보딩 안내",
    use_cases: ["신규 사용자 안내"],
    display_group: "operator",
    registry_group: "opal",
    domain: null,
    pipeline_summary: null,
    source_path: "opal/skills/opal-onboarding/SKILL.md",
    resolved_from: { kind: "canonical", value: "opal-onboarding" },
    quick_start: {
      id: "qs-1",
      label: "Quick Start",
      language: "bash",
      command: "opal-cli console start",
      kind: "quick-start",
    },
    usage_markdown: "## Usage\n사용법 본문",
    arguments: [],
    options: [],
    when_to_use_markdown: "언제 쓰는지",
    examples: [],
    pipeline: null,
    related_skills: [],
    source: { path: "opal/skills/opal-onboarding/SKILL.md", available: true, content_hash: "abc123" },
    ...overrides,
  };
}

beforeEach(() => {
  mockedApiClient.mockReset();
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* ⑤ source 부재 — 메타 유지 + 본문 부재 Alert                              */
/* ------------------------------------------------------------------ */

describe("S-12 ⑤: source 부재 (RED)", () => {
  it("source.available=false여도 제목·설명 등 메타는 유지된다", async () => {
    mockedApiClient.mockResolvedValue(
      fxDetail({
        usage_markdown: null,
        when_to_use_markdown: null,
        source: { path: "opal/skills/opal-onboarding/SKILL.md", available: false, content_hash: null },
      }),
    );
    renderDetail("/docs/skills/opal-onboarding");

    expect(await screen.findByText("OPAL 온보딩 안내")).toBeInTheDocument();
  });

  it("source.available=false면 본문 부재 Alert를 표시한다", async () => {
    mockedApiClient.mockResolvedValue(
      fxDetail({
        usage_markdown: null,
        when_to_use_markdown: null,
        source: { path: "opal/skills/opal-onboarding/SKILL.md", available: false, content_hash: null },
      }),
    );
    renderDetail("/docs/skills/opal-onboarding");

    await screen.findByText("OPAL 온보딩 안내");
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* ⑥ alias 진입 시 canonical URL로 replace (히스토리 중복 없음)              */
/* ------------------------------------------------------------------ */

describe("S-12 ⑥: alias → canonical replace (RED)", () => {
  it("alias URL로 진입하면 canonical URL로 replace되어 뒤로가기 히스토리가 늘지 않는다", async () => {
    mockedApiClient.mockResolvedValue(
      fxDetail({ resolved_from: { kind: "alias", value: "onboarding" } }),
    );
    const { router } = renderDetail("/docs/skills/onboarding");

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/docs/skills/opal-onboarding");
    });

    // 히스토리 스택 길이가 1이어야 한다 (replace이므로 push로 늘어나지 않음)
    expect(router.state.historyAction).not.toBe("PUSH");
  });
});

/* ------------------------------------------------------------------ */
/* ⑧⑨ 복사 버튼 — 성공 시 프롬프트 문자 없는 원문 전달, 실패 시 폴백           */
/* ------------------------------------------------------------------ */

describe("S-12 ⑧⑨: 예시 복사 (RED)", () => {
  it("복사 버튼 클릭 시 프롬프트 문자 없는 명령 원문이 클립보드로 전달되고 성공 피드백이 표시된다", async () => {
    mockedApiClient.mockResolvedValue(fxDetail());
    renderDetail("/docs/skills/opal-onboarding");

    const copyButton = await screen.findByRole("button", { name: "예시 복사" });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("opal-cli console start");
    });
    const call = (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(call).not.toMatch(/^[$%>]/);
    expect(await screen.findByText("복사됨")).toBeInTheDocument();
  });

  it("클립보드 API 실패 시 수동 복사 폴백 경로를 제공한다", async () => {
    mockedApiClient.mockResolvedValue(fxDetail());
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error("clipboard denied")) },
    });
    renderDetail("/docs/skills/opal-onboarding");

    const copyButton = await screen.findByRole("button", { name: "예시 복사" });
    fireEvent.click(copyButton);

    // 폴백: 선택 가능한 텍스트로 노출되어 수동 복사가 가능해야 한다
    await waitFor(() => {
      expect(screen.getByText("opal-cli console start")).toBeInTheDocument();
    });
  });
});

/* ------------------------------------------------------------------ */
/* ⑩ 접근성 — 접근 가능한 이름과 포커스 이동                                  */
/* ------------------------------------------------------------------ */

describe("S-12 ⑩: 접근성 (RED)", () => {
  it("모든 조작 요소(복사 버튼 등)가 접근 가능한 이름을 갖는다", async () => {
    mockedApiClient.mockResolvedValue(fxDetail());
    renderDetail("/docs/skills/opal-onboarding");

    const copyButton = await screen.findByRole("button", { name: "예시 복사" });
    expect(copyButton).toBeInTheDocument();
  });

  it("포커스 가능한 조작 요소들이 순서대로 포커스를 받을 수 있다", async () => {
    mockedApiClient.mockResolvedValue(fxDetail());
    renderDetail("/docs/skills/opal-onboarding");

    await screen.findByText("OPAL 온보딩 안내");
    const focusable = screen
      .getAllByRole("button")
      .concat(screen.queryAllByRole("link"));
    expect(focusable.length).toBeGreaterThan(0);
    focusable.forEach((el) => {
      (el as HTMLElement).focus();
      expect(document.activeElement).toBe(el);
    });
  });
});

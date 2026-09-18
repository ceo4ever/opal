/**
 * @header {
 *   "module": "docs-catalog-page-test",
 *   "layer": "test",
 *   "domain": "docs",
 *   "description": "DocsCatalogPage RED 테스트 — S-12(DEC-8, AC-2, AC-3, AC-6, C-1, C-4, C-7). apiClient를 vi.mock으로 대역하고 QueryClientProvider + createMemoryRouter로 렌더한다. 로딩/빈 상태(전체 0건 vs 검색 0건 구분)/오류 code별 분기, 검색·필터의 URL 쿼리(q/group/domain) 동기화와 새로고침 복원, 접근 가능한 이름을 검증한다. screenshot golden은 만들지 않는다.",
 *   "task": "140-260917-opdw-스킬-문서-화면",
 *   "scenarios": ["S-12"],
 *   "exports": []
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocsCatalogPage } from "./DocsCatalogPage";
import { apiClient, ApiError } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    apiClient: vi.fn(),
  };
});

const mockedApiClient = vi.mocked(apiClient);

function renderCatalog(initialPath = "/docs/skills") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [{ path: "/docs/skills", element: <DocsCatalogPage /> }],
    { initialEntries: [initialPath] },
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router };
}

function fxItem(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    canonical_name: "oppb",
    source_name: "opal-pilot-project-build",
    aliases: ["oppb"],
    description: "프로젝트 빌드 파이프라인",
    use_cases: ["신규 프로젝트 착수"],
    display_group: "pilot",
    registry_group: "opal-pilot",
    domain: "project",
    pipeline_summary: "P0~P5",
    source_path: "opal/skills/opal-pilot-project-build/SKILL.md",
    ...overrides,
  };
}

beforeEach(() => {
  mockedApiClient.mockReset();
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* ① 로딩 상태                                                           */
/* ------------------------------------------------------------------ */

describe("S-12 ①: 로딩 상태 (RED)", () => {
  it("응답이 도착하기 전에는 aria-busy 로딩 표시를 렌더한다", async () => {
    mockedApiClient.mockImplementation(() => new Promise(() => {}));
    renderCatalog();

    const busyRegions = document.querySelectorAll('[aria-busy="true"]');
    expect(busyRegions.length).toBeGreaterThan(0);
  });
});

/* ------------------------------------------------------------------ */
/* ②③ 전체 0건 vs 검색 결과 0건 — 서로 구분되어 표시                          */
/* ------------------------------------------------------------------ */

describe("S-12 ②③: 빈 상태 구분 (RED)", () => {
  it("전체 소스 집합이 0개면 '아직 문서화된 스킬이 없습니다'를 표시한다", async () => {
    mockedApiClient.mockResolvedValue({
      items: [],
      meta: { total: 0, filtered: 0, query: "" },
      facets: { groups: [], domains: [] },
    });
    renderCatalog();

    expect(await screen.findByText("아직 문서화된 스킬이 없습니다")).toBeInTheDocument();
  });

  it("검색 결과만 0개면 '조건에 맞는 스킬이 없습니다'를 표시하고 전체-0건 문구와 다르다", async () => {
    mockedApiClient.mockResolvedValue({
      items: [],
      meta: { total: 55, filtered: 0, query: "존재하지않는검색어" },
      facets: { groups: [], domains: [] },
    });
    renderCatalog("/docs/skills?q=존재하지않는검색어");

    expect(await screen.findByText("조건에 맞는 스킬이 없습니다")).toBeInTheDocument();
    expect(screen.queryByText("아직 문서화된 스킬이 없습니다")).not.toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* ④ 오류 code별 복구 UI 분기                                              */
/* ------------------------------------------------------------------ */

describe("S-12 ④: 오류 code별 분기 (RED)", () => {
  it("registry_unavailable이면 재시도 가능한 Alert를 표시한다", async () => {
    mockedApiClient.mockRejectedValue(
      new ApiError("스킬 목록을 불러오지 못했습니다", {
        status: 500,
        code: "registry_unavailable",
        details: { retryable: true },
      }),
    );
    renderCatalog();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("스킬 목록을 불러오지 못했습니다");
    expect(screen.getByRole("button", { name: "다시 시도" })).toBeInTheDocument();
  });

  it("parse_error면 일반 오류 메시지를 표시하고 절대경로/스택을 노출하지 않는다", async () => {
    mockedApiClient.mockRejectedValue(
      new ApiError("스킬 목록을 불러오지 못했습니다", {
        status: 500,
        code: "parse_error",
        details: { retryable: true },
      }),
    );
    renderCatalog();

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).not.toMatch(/\/Users\/|\/Volumes\/|at .*:\d+:\d+/);
  });
});

/* ------------------------------------------------------------------ */
/* ⑦ 검색·필터 URL 동기화 + 새로고침 복원                                    */
/* ------------------------------------------------------------------ */

describe("S-12 ⑦: 검색·필터 URL 동기화 (RED)", () => {
  it("검색어 입력 시 URL 쿼리 q에 반영된다", async () => {
    mockedApiClient.mockResolvedValue({
      items: [fxItem()],
      meta: { total: 55, filtered: 55, query: "" },
      facets: {
        groups: [{ value: "pilot", label: "파일럿", count: 1 }],
        domains: [{ value: "project", label: "프로젝트", count: 1 }],
      },
    });
    const { router } = renderCatalog();
    await screen.findByText("oppb");

    const searchInput = screen.getByRole("textbox", { name: /스킬 검색/ });
    fireEvent.change(searchInput, { target: { value: "oppb" } });

    await waitFor(() => {
      expect(router.state.location.search).toContain("q=oppb");
    });
  });

  it("q/group/domain 쿼리가 있는 URL로 진입하면 검색·필터 상태가 복원된다", async () => {
    mockedApiClient.mockResolvedValue({
      items: [fxItem()],
      meta: { total: 55, filtered: 1, query: "oppb" },
      facets: {
        groups: [{ value: "pilot", label: "파일럿", count: 1 }],
        domains: [{ value: "project", label: "프로젝트", count: 1 }],
      },
    });
    renderCatalog("/docs/skills?q=oppb&group=pilot&domain=project");
    await screen.findByText("oppb");

    const searchInput = screen.getByRole("textbox", { name: /스킬 검색/ }) as HTMLInputElement;
    expect(searchInput.value).toBe("oppb");
  });
});

/* ------------------------------------------------------------------ */
/* 접근성 — 조작 요소의 접근 가능한 이름                                     */
/* ------------------------------------------------------------------ */

describe("S-12 ⑩: 접근성 (RED)", () => {
  it("검색 입력과 카드 링크가 접근 가능한 이름을 갖는다", async () => {
    mockedApiClient.mockResolvedValue({
      items: [fxItem()],
      meta: { total: 55, filtered: 55, query: "" },
      facets: {
        groups: [{ value: "pilot", label: "파일럿", count: 1 }],
        domains: [{ value: "project", label: "프로젝트", count: 1 }],
      },
    });
    renderCatalog();

    expect(screen.getByRole("textbox", { name: /스킬 검색/ })).toBeInTheDocument();
    const cardLink = await screen.findByRole("link", { name: /oppb/ });
    expect(cardLink).toBeInTheDocument();
  });
});

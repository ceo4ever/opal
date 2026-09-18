/**
 * @header {
 *   "module": "skill-docs-page-test",
 *   "layer": "test",
 *   "domain": "docs",
 *   "description": "SkillDocsPage RED 테스트 — PLAN W-2(DEC-6, S-8·S-9·S-10). 대상 컴포넌트 SkillDocsPage는 아직 존재하지 않아 import 실패로 전부 RED다. apiClient를 vi.mock으로 대역하고 QueryClientProvider + createMemoryRouter로 두 라우트(docs/skills, docs/skills/:skillId)에 동일 컴포넌트를 지정해 렌더한다. 새 계약(SkillCatalogItem.listed, SkillDetailResponse.body{markdown,origin,source_path})을 반영한 mock 응답을 사용한다. 검사 대상: ①3그룹 헤더 + listed=true만 렌더 ②canonical+alias 병기 ③클릭 시 URL 변경·사이드바 유지·aria-current ④body.markdown Markdown 렌더(제목·목록·표·코드블록) ⑤origin=skill_md 폴백 안내/ origin=null 부재 상태 ⑥searchbox·Select 부재 ⑦로딩/목록 빈 상태/목록 조회 실패/상세 404 구분 ⑧nav 랜드마크+접근 가능한 이름+키보드 포커스 이동. screenshot golden은 만들지 않는다.",
 *   "task": "143-260918-opds-스킬-문서-사이드바",
 *   "scenarios": ["S-8", "S-9", "S-10"],
 *   "exports": []
 * }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SkillDocsPage } from "./SkillDocsPage";
import { apiClient, ApiError } from "@/lib/api";
import type { SkillCatalogItem, SkillDetailResponse } from "./types";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    apiClient: vi.fn(),
  };
});

const mockedApiClient = vi.mocked(apiClient);

function renderDocs(initialPath = "/docs/skills") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/docs/skills", element: <SkillDocsPage /> },
      { path: "/docs/skills/:skillId", element: <SkillDocsPage /> },
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

function fxItem(overrides: Partial<SkillCatalogItem> = {}): SkillCatalogItem {
  return {
    canonical_name: "oppb",
    source_name: "opal-pilot-project-build",
    aliases: ["oppb", "opal-pilot-project-build"],
    description: "프로젝트 빌드 파이프라인",
    display_group: "pilot",
    registry_group: "opal-pilot",
    domain: "project",
    pipeline_summary: "P0~P5",
    source_path: "opal/skills/opal-pilot-project-build/SKILL.md",
    listed: true,
    ...overrides,
  };
}

function fxCatalog(items: SkillCatalogItem[]) {
  return {
    items,
    facets: { groups: [], domains: [] },
    meta: { total: items.length, filtered: items.length, query: "" },
  };
}

function fxDetail(overrides: Partial<SkillDetailResponse> = {}): SkillDetailResponse {
  return {
    canonical_name: "oppb",
    source_name: "opal-pilot-project-build",
    aliases: ["oppb"],
    description: "프로젝트 빌드 파이프라인",
    display_group: "pilot",
    registry_group: "opal-pilot",
    domain: "project",
    pipeline_summary: "P0~P5",
    source_path: "opal/skills/opal-pilot-project-build/SKILL.md",
    source: { available: true, path: "opal/skills/opal-pilot-project-build/SKILL.md" },
    body: {
      markdown:
        "# 제목\n\n- 목록1\n- 목록2\n\n| 열1 | 열2 |\n|---|---|\n| a | b |\n\n```bash\necho hi\n```",
      origin: "readme",
      source_path: "opal/skills/opal-pilot-project-build/README.md",
    },
    pipeline: null,
    related_skills: [],
    listed: true,
    resolved_from: { kind: "canonical", value: "oppb" },
    ...overrides,
  };
}

const CATALOG_ITEMS: SkillCatalogItem[] = [
  fxItem({
    canonical_name: "oppb",
    aliases: ["oppb", "opal-pilot-project-build"],
    display_group: "pilot",
    listed: true,
  }),
  fxItem({
    canonical_name: "opal-operator-review",
    source_name: "opal-operator-review",
    aliases: ["opal-operator-review"],
    display_group: "operator",
    listed: true,
  }),
  fxItem({
    canonical_name: "opal-standalone-tool",
    source_name: "opal-standalone-tool",
    aliases: ["opal-standalone-tool"],
    display_group: "standalone",
    listed: true,
  }),
  fxItem({
    canonical_name: "op-internal-step",
    source_name: "op-internal-step",
    aliases: ["op-internal-step"],
    display_group: "internal-stage",
    listed: false,
  }),
];

beforeEach(() => {
  mockedApiClient.mockReset();
});

afterEach(() => {
  cleanup();
});

/* ------------------------------------------------------------------ */
/* S-8 ①②: 3그룹 헤더 + listed 필터링 + canonical/alias 병기               */
/* ------------------------------------------------------------------ */

describe("S-8 ①②: 사이드바 그룹·노출 집합 (RED)", () => {
  it("파일럿·오퍼레이터·독립 3그룹 헤더가 렌더되고 listed=true 항목만 보인다", async () => {
    mockedApiClient.mockResolvedValue(fxCatalog(CATALOG_ITEMS));
    renderDocs();

    expect(await screen.findByText("oppb")).toBeInTheDocument();
    expect(screen.getByText(/파일럿/)).toBeInTheDocument();
    expect(screen.getByText(/오퍼레이터/)).toBeInTheDocument();
    expect(screen.getByText(/독립/)).toBeInTheDocument();

    expect(screen.getByText("opal-operator-review")).toBeInTheDocument();
    expect(screen.getByText("opal-standalone-tool")).toBeInTheDocument();
    expect(screen.queryByText("op-internal-step")).not.toBeInTheDocument();
  });

  it("각 항목에 canonical 이름과 alias가 함께 표시된다", async () => {
    mockedApiClient.mockResolvedValue(fxCatalog(CATALOG_ITEMS));
    renderDocs();

    await screen.findByText("oppb");
    expect(screen.getByText(/opal-pilot-project-build/)).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* S-8 ③: 클릭 시 URL 변경, 사이드바 유지, aria-current                    */
/* ------------------------------------------------------------------ */

describe("S-8 ③: 항목 클릭 내비게이션 (RED)", () => {
  it("사이드바 항목 클릭 시 URL이 /docs/skills/{id}로 바뀌고 사이드바가 유지되며 선택 항목이 시각적으로 구분된다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.resolve(fxDetail());
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    const { router } = renderDocs();

    const item = await screen.findByText("oppb");
    fireEvent.click(item);

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/docs/skills/oppb");
    });

    // 사이드바가 유지된다
    expect(screen.getByText("opal-operator-review")).toBeInTheDocument();

    const selectedLink = screen.getByRole("link", { name: /oppb/ });
    expect(selectedLink).toHaveAttribute("aria-current");
  });

  it("항목 전환 후에도 사이드바 목록이 재요청되지 않는다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.resolve(fxDetail());
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    renderDocs();

    await screen.findByText("oppb");
    const listCallCountBeforeClick = mockedApiClient.mock.calls.filter((c) =>
      String(c[0]).startsWith("/api/docs/skills") && !String(c[0]).includes("/oppb"),
    ).length;

    fireEvent.click(screen.getByText("oppb"));
    await waitFor(() => screen.getByText(/제목/));

    const listCallCountAfterClick = mockedApiClient.mock.calls.filter((c) =>
      String(c[0]).startsWith("/api/docs/skills") && !String(c[0]).includes("/oppb"),
    ).length;

    expect(listCallCountAfterClick).toBe(listCallCountBeforeClick);
  });
});

/* ------------------------------------------------------------------ */
/* S-9 ④: body.markdown이 Markdown 요소로 렌더                            */
/* ------------------------------------------------------------------ */

describe("S-9 ④: 본문 Markdown 렌더 (RED)", () => {
  it("제목·목록·표·코드 블록이 실제 요소로 나타난다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.resolve(fxDetail());
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    renderDocs("/docs/skills/oppb");

    expect(await screen.findByRole("heading", { name: "제목" })).toBeInTheDocument();
    expect(screen.getByText("목록1")).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("echo hi")).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* S-9 ⑤: origin=skill_md 폴백 안내 / origin=null 부재 상태                */
/* ------------------------------------------------------------------ */

describe("S-9 ⑤: 폴백·부재 상태 (RED)", () => {
  it("origin이 skill_md면 폴백 안내가 보인다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.resolve(
          fxDetail({
            body: {
              markdown: "SKILL.md 본문",
              origin: "skill_md",
              source_path: "opal/skills/oppb/SKILL.md",
            },
          }),
        );
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    renderDocs("/docs/skills/oppb");

    await screen.findByText("SKILL.md 본문");
    expect(screen.getByText(/README/)).toBeInTheDocument();
  });

  it("origin이 null이면 부재 상태가 보인다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.resolve(
          fxDetail({ body: { markdown: null, origin: null, source_path: null } }),
        );
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    renderDocs("/docs/skills/oppb");

    expect(await screen.findByText(/문서가 없습니다|본문이 없습니다|부재/)).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* S-8 ⑥: 검색·필터 부재                                                  */
/* ------------------------------------------------------------------ */

describe("S-8 ⑥: 검색 입력·Select 부재 (RED)", () => {
  it("role=searchbox 입력과 그룹·도메인 Select가 화면에 없다", async () => {
    mockedApiClient.mockResolvedValue(fxCatalog(CATALOG_ITEMS));
    renderDocs();

    await screen.findByText("oppb");
    expect(screen.queryByRole("searchbox")).toBeNull();
    expect(screen.queryByLabelText("그룹 필터")).toBeNull();
    expect(screen.queryByLabelText("도메인 필터")).toBeNull();
  });
});

/* ------------------------------------------------------------------ */
/* S-10 ⑦: 로딩 / 목록 빈 상태 / 목록 조회 실패 / 상세 404                    */
/* ------------------------------------------------------------------ */

describe("S-10 ⑦: 상태 구분 (RED)", () => {
  it("목록 응답 도착 전에는 로딩 표시를 렌더한다", async () => {
    mockedApiClient.mockImplementation(() => new Promise(() => {}));
    renderDocs();

    const busyRegions = document.querySelectorAll('[aria-busy="true"]');
    expect(busyRegions.length).toBeGreaterThan(0);
  });

  it("목록이 0건이면 빈 상태 문구를 표시한다", async () => {
    mockedApiClient.mockResolvedValue(fxCatalog([]));
    renderDocs();

    expect(
      await screen.findByText(/문서화된 스킬이 없습니다|목록이 비어 있습니다/),
    ).toBeInTheDocument();
  });

  it("목록 조회 실패 시 오류 상태를 표시한다", async () => {
    mockedApiClient.mockRejectedValue(
      new ApiError("스킬 목록을 불러오지 못했습니다", {
        status: 500,
        code: "registry_unavailable",
        details: { retryable: true },
      }),
    );
    renderDocs();

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("상세 404면 목록 오류와 구분되는 상세 전용 오류 상태를 표시한다", async () => {
    mockedApiClient.mockImplementation((path: unknown) => {
      const p = String(path);
      if (p.startsWith("/api/docs/skills/")) {
        return Promise.reject(
          new ApiError("해당 스킬 문서를 찾을 수 없습니다", {
            status: 404,
            code: "skill_not_found",
            details: {},
          }),
        );
      }
      return Promise.resolve(fxCatalog(CATALOG_ITEMS));
    });
    renderDocs("/docs/skills/no-such-skill");

    expect(await screen.findByText(/찾을 수 없습니다/)).toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/* S-8 ⑧: nav 랜드마크·접근 가능한 이름·키보드 포커스 이동                    */
/* ------------------------------------------------------------------ */

describe("S-8 ⑧: 접근성 (RED)", () => {
  it("사이드바가 nav 랜드마크와 접근 가능한 이름을 갖고 키보드로 항목 간 포커스 이동이 가능하다", async () => {
    mockedApiClient.mockResolvedValue(fxCatalog(CATALOG_ITEMS));
    renderDocs();

    await screen.findByText("oppb");
    const nav = screen.getByRole("navigation");
    expect(nav).toHaveAccessibleName();

    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(3);
    links[0].focus();
    expect(document.activeElement).toBe(links[0]);
  });
});

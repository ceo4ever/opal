/**
 * @header {
 *   "module": "app",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "OPAL Console 루트 — 조회 전용 Console router와 query client provider를 구성한다.",
 *   "exports": ["App"],
 *   "depends": ["query-client", "router"]
 * }
 */

import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/api";
import { router } from "@/router";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;

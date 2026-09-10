/**
 * @header {
 *   "module": "app",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "OPAL Console 루트 — query flag에 따라 기존 Console 또는 Desktop Workbench 목업 제공",
 *   "exports": ["App"],
 *   "depends": ["query-client", "router", "workbench-app"]
 * }
 */

import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/api";
import { router } from "@/router";
import { WorkbenchApp } from "@/workbench/WorkbenchApp";

function App() {
  if (new URLSearchParams(window.location.search).get("workbench") === "1") {
    return <WorkbenchApp />;
  }
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;

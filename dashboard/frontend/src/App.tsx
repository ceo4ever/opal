/**
 * @header {
 *   "module": "app",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "OPAL Console 루트 앱 컴포넌트 — QueryClientProvider + RouterProvider 제공",
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

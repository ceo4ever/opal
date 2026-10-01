/**
 * @header {
 *   "module": "app",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "OPAL Console 루트 — query client provider를 구성하고, 인증 상태(useAuthStatus)가 authed일 때만 Console router를 마운트한다(pending은 빈 화면, locked는 LockScreen).",
 *   "exports": ["App"],
 *   "depends": ["query-client", "router", "auth", "lock-screen"]
 * }
 */

import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/api";
import { router } from "@/router";
import { useAuthStatus } from "@/lib/auth";
import { LockScreen } from "@/components/auth/LockScreen";

function App() {
  const authStatus = useAuthStatus();
  return (
    <QueryClientProvider client={queryClient}>
      {authStatus === "authed" ? (
        <RouterProvider router={router} />
      ) : authStatus === "locked" ? (
        <LockScreen />
      ) : null}
    </QueryClientProvider>
  );
}

export default App;

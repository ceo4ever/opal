/**
 * @header {
 *   "module": "lock-screen",
 *   "layer": "component",
 *   "domain": "core",
 *   "description": "인증 잠금 화면(D-14) — 세션이 없다는 사실과 터미널에서 `opal-cli console open`을 다시 실행하라는 정적 안내, 상태 재확인 버튼 1개만 보인다. API를 호출하지 않으며 프로젝트·설정·계정 정보를 렌더링하지 않는다. 재확인은 페이지를 다시 불러 인증 부트스트랩을 재수행한다.",
 *   "exports": ["LockScreen"],
 *   "depends": ["button"],
 *   "task": "172"
 * }
 */

import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LockScreen() {
  return (
    <div className="flex min-h-screen flex-1 flex-col items-center justify-center gap-4 p-6 text-center">
      <Lock className="h-8 w-8 text-muted-foreground" />
      <h1 className="text-base font-semibold">콘솔 세션이 없습니다</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        터미널에서 <code className="font-mono">opal-cli console open</code>을 실행해 다시 여세요.
      </p>
      <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
        상태 재확인
      </Button>
    </div>
  );
}

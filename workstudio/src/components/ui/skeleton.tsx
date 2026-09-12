/**
 * @header {
 *   "module": "ui-skeleton",
 *   "layer": "component",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio skeleton UI primitive. shadcn/ui 기반 스타일과 접근성 계약을 앱 내부에서 제공한다.",
 *   "exports": ["Skeleton"]
 * }
 */
import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }

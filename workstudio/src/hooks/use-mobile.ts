/**
 * @header {
 *   "module": "use-mobile",
 *   "layer": "hook",
 *   "domain": "workstudio",
 *   "description": "WorkStudio UI primitive에서 사용하는 모바일 breakpoint 감지 hook.",
 *   "exports": ["useIsMobile"]
 * }
 */
import * as React from "react"

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(() =>
    typeof window === "undefined" ? false : window.innerWidth < MOBILE_BREAKPOINT
  )

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return isMobile
}

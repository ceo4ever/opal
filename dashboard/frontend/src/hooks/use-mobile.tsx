/**
 * @header {
 *   "module": "use-mobile",
 *   "layer": "hook",
 *   "domain": "dashboard",
 *   "description": "Dashboard responsive breakpoint hook. matchMedia change 이벤트로 모바일 여부를 제공한다.",
 *   "exports": ["useIsMobile"]
 * }
 */
import * as React from "react"

const MOBILE_BREAKPOINT = 768

function getIsMobile() {
  return window.innerWidth < MOBILE_BREAKPOINT
}

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(() => getIsMobile())

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(getIsMobile())
    }
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return isMobile
}

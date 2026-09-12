/**
 * @header {
 *   "module": "workstudio-renderer-entry",
 *   "layer": "app",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio React renderer entrypoint. Dashboard router/query client 없이 독립 WorkStudio shell을 마운트한다.",
 *   "exports": []
 * }
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { WorkStudioApp } from './workstudio/WorkStudioApp.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WorkStudioApp />
  </StrictMode>,
)

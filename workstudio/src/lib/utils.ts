/**
 * @header {
 *   "module": "utils",
 *   "layer": "util",
 *   "domain": "ui",
 *   "description": "Tailwind CSS className 병합 유틸리티 (clsx + tailwind-merge)",
 *   "exports": ["cn"]
 * }
 */
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

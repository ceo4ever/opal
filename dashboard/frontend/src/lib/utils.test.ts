/**
 * @header {
 *   "module": "utils-test",
 *   "layer": "test",
 *   "domain": "ui-util",
 *   "description": "cn() 유틸리티 샘플 테스트 — 클래스 병합 및 tailwind-merge dedupe 검증",
 *   "task": "033",
 *   "scenarios": ["S-8"]
 * }
 */
import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  it('dedupes conflicting tailwind classes', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })
})

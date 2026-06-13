import { describe, it, expect } from 'vitest'
import { formatEstimatedTime } from '../format'

describe('formatEstimatedTime', () => {
  it('60초 미만은 초 단위로 표기한다', () => {
    expect(formatEstimatedTime(0)).toBe('약 0초')
    expect(formatEstimatedTime(48)).toBe('약 48초')
    expect(formatEstimatedTime(59)).toBe('약 59초')
  })

  it('정확히 분 단위면 초를 생략한다', () => {
    expect(formatEstimatedTime(60)).toBe('약 1분')
    expect(formatEstimatedTime(120)).toBe('약 2분')
  })

  it('분과 초를 함께 표기한다', () => {
    expect(formatEstimatedTime(70)).toBe('약 1분 10초')
    expect(formatEstimatedTime(135)).toBe('약 2분 15초')
  })
})

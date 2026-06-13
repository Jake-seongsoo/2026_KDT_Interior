import { describe, it, expect } from 'vitest'
import { formatDate, formatEstimatedTime } from '../format'

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

describe('formatDate', () => {
  it('ISO 문자열을 YYYY.MM.DD로 변환한다', () => {
    // 정오 UTC라 로컬 타임존 영향 없이 날짜가 보존됨
    expect(formatDate('2026-06-13T12:00:00+00:00')).toBe('2026.06.13')
    expect(formatDate('2026-01-05T12:00:00Z')).toBe('2026.01.05')
  })

  it('파싱 불가 입력은 빈 문자열', () => {
    expect(formatDate('not-a-date')).toBe('')
    expect(formatDate('')).toBe('')
  })
})

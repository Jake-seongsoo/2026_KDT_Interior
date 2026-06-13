import { describe, it, expect } from 'vitest'
import { PRESET_MOOD_CHIPS, addChip, isPresetChip, toggleChip } from '../mood-chips'

describe('isPresetChip', () => {
  it('프리셋 목록에 있으면 true', () => {
    expect(isPresetChip('모던')).toBe(true)
    expect(isPresetChip('다크무드')).toBe(true)
  })
  it('커스텀 칩이면 false', () => {
    expect(isPresetChip('우드포인트')).toBe(false)
    expect(isPresetChip('')).toBe(false)
  })
})

describe('toggleChip', () => {
  it('없는 칩은 추가한다', () => {
    expect(toggleChip(['모던'], '코지')).toEqual(['모던', '코지'])
  })
  it('있는 칩은 제거한다', () => {
    expect(toggleChip(['모던', '코지'], '모던')).toEqual(['코지'])
  })
  it('원본 배열을 변형하지 않는다', () => {
    const original = ['모던']
    toggleChip(original, '코지')
    expect(original).toEqual(['모던'])
  })
})

describe('addChip', () => {
  it('새 칩을 추가한다', () => {
    expect(addChip(['모던'], '우드포인트')).toEqual(['모던', '우드포인트'])
  })
  it('앞뒤 공백을 제거하고 추가한다', () => {
    expect(addChip([], '  코지  ')).toEqual(['코지'])
  })
  it('빈 입력은 무시한다', () => {
    expect(addChip(['모던'], '   ')).toEqual(['모던'])
  })
  it('중복 칩은 무시한다', () => {
    expect(addChip(['모던'], '모던')).toEqual(['모던'])
  })
})

describe('PRESET_MOOD_CHIPS', () => {
  it('12개 프리셋을 제공한다', () => {
    expect(PRESET_MOOD_CHIPS).toHaveLength(12)
  })
})

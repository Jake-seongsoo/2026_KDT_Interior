import { describe, it, expect } from 'vitest'
import { squarifiedTreemap, type TreemapRect } from '../treemap'

const W = 600
const H = 400
const SAMPLE = [
  { id: 'living', value: 28.5 },
  { id: 'bed1', value: 14.5 },
  { id: 'kitchen', value: 12.0 },
  { id: 'bed2', value: 9.5 },
]
const TOTAL_VALUE = SAMPLE.reduce((s, i) => s + i.value, 0) // 64.5

function area(r: TreemapRect) {
  return r.w * r.h
}

function intersectArea(a: TreemapRect, b: TreemapRect): number {
  const xOverlap = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x))
  const yOverlap = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y))
  return xOverlap * yOverlap
}

describe('squarifiedTreemap', () => {
  it('방 4개를 입력하면 사각형 4개를 반환한다', () => {
    const rects = squarifiedTreemap(SAMPLE, W, H)
    expect(rects).toHaveLength(4)
  })

  it('반환된 id가 입력 id와 1:1 대응한다', () => {
    const rects = squarifiedTreemap(SAMPLE, W, H)
    const ids = new Set(rects.map(r => r.id))
    expect(ids).toEqual(new Set(SAMPLE.map(i => i.id)))
  })

  it('사각형 면적 합이 캔버스 면적에 근사한다 (±1%)', () => {
    const rects = squarifiedTreemap(SAMPLE, W, H)
    const totalArea = rects.reduce((s, r) => s + area(r), 0)
    expect(totalArea).toBeCloseTo(W * H, -2) // ±100px² 허용
  })

  it('value 비율과 사각형 면적 비율이 일치한다 (±2%)', () => {
    const rects = squarifiedTreemap(SAMPLE, W, H)
    const totalArea = rects.reduce((s, r) => s + area(r), 0)
    for (const item of SAMPLE) {
      const rect = rects.find(r => r.id === item.id)!
      const expectedPct = item.value / TOTAL_VALUE
      const actualPct = area(rect) / totalArea
      expect(Math.abs(actualPct - expectedPct)).toBeLessThan(0.02)
    }
  })

  it('사각형들이 서로 겹치지 않는다', () => {
    const rects = squarifiedTreemap(SAMPLE, W, H)
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        // 부동소수점 오차 1px² 허용
        expect(intersectArea(rects[i], rects[j])).toBeLessThan(1)
      }
    }
  })

  it('빈 배열은 빈 배열을 반환한다', () => {
    expect(squarifiedTreemap([], W, H)).toEqual([])
  })

  it('단일 아이템은 컨테이너 전체를 차지한다', () => {
    const rects = squarifiedTreemap([{ id: 'a', value: 10 }], W, H)
    expect(rects).toHaveLength(1)
    expect(rects[0]).toMatchObject({ x: 0, y: 0, w: W, h: H })
  })

  it('모두 같은 면적이면 균등 분할된다', () => {
    const equal = [
      { id: 'a', value: 10 },
      { id: 'b', value: 10 },
      { id: 'c', value: 10 },
      { id: 'd', value: 10 },
    ]
    const rects = squarifiedTreemap(equal, W, H)
    const areas = rects.map(area)
    const avg = areas.reduce((s, a) => s + a, 0) / areas.length
    for (const a of areas) {
      expect(Math.abs(a - avg) / avg).toBeLessThan(0.02)
    }
  })

  it('value가 모두 0이면 균등 그리드 fallback을 반환한다', () => {
    const rects = squarifiedTreemap(
      [{ id: 'a', value: 0 }, { id: 'b', value: 0 }],
      W, H
    )
    expect(rects).toHaveLength(2)
  })

  it('2개 방도 정상 처리된다', () => {
    const rects = squarifiedTreemap([
      { id: 'living', value: 28.5 },
      { id: 'bed1', value: 14.5 },
    ], W, H)
    expect(rects).toHaveLength(2)
    expect(intersectArea(rects[0], rects[1])).toBeLessThan(1)
  })
})

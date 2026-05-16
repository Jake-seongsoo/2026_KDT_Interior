export interface TreemapInput {
  id: string
  value: number
}

export interface TreemapRect {
  id: string
  x: number
  y: number
  w: number
  h: number
}

// row 내 각 아이템의 종횡비 최악값 계산
// l: 스트립의 긴 쪽 (= max(area.w, area.h))
function worstAspect(values: number[], sum: number, l: number): number {
  if (!values.length || sum <= 0 || l <= 0) return Infinity
  let max = 0
  for (const v of values) {
    if (v <= 0) continue
    const r = Math.max((l * l * v) / (sum * sum), (sum * sum) / (l * l * v))
    if (r > max) max = r
  }
  return max
}

function placeRow(
  row: TreemapInput[],
  rowSum: number,
  area: { x: number; y: number; w: number; h: number },
  result: TreemapRect[]
) {
  const isHoriz = area.w >= area.h
  const l = isHoriz ? area.w : area.h
  const depth = rowSum / l // 스트립의 짧은 쪽 크기
  let pos = isHoriz ? area.x : area.y

  for (const item of row) {
    const len = (item.value / rowSum) * l
    if (isHoriz) {
      result.push({ id: item.id, x: pos, y: area.y, w: len, h: depth })
    } else {
      result.push({ id: item.id, x: area.x, y: pos, w: depth, h: len })
    }
    pos += len
  }
}

function squarifyArea(
  items: TreemapInput[],
  area: { x: number; y: number; w: number; h: number },
  result: TreemapRect[]
) {
  if (!items.length || area.w < 0.5 || area.h < 0.5) return

  const isHoriz = area.w >= area.h
  const l = isHoriz ? area.w : area.h

  let row: TreemapInput[] = []
  let rowSum = 0
  let prevWorst = Infinity

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    const nextRow = [...row, item]
    const nextSum = rowSum + item.value
    const w = worstAspect(nextRow.map(x => x.value), nextSum, l)

    if (row.length > 0 && w > prevWorst) {
      // 종횡비가 나빠지면 현재 row 확정 후 재귀
      placeRow(row, rowSum, area, result)
      const depth = rowSum / l
      const nextArea = isHoriz
        ? { x: area.x, y: area.y + depth, w: area.w, h: area.h - depth }
        : { x: area.x + depth, y: area.y, w: area.w - depth, h: area.h }
      squarifyArea(items.slice(i), nextArea, result)
      return
    }

    row = nextRow
    rowSum = nextSum
    prevWorst = w
  }

  if (row.length) placeRow(row, rowSum, area, result)
}

function uniformGrid(items: TreemapInput[], width: number, height: number): TreemapRect[] {
  const n = items.length
  const cols = Math.ceil(Math.sqrt(n))
  const rows = Math.ceil(n / cols)
  const cw = width / cols
  const ch = height / rows
  return items.map((item, i) => ({
    id: item.id,
    x: (i % cols) * cw,
    y: Math.floor(i / cols) * ch,
    w: cw,
    h: ch,
  }))
}

// 면적 비례 squarified treemap 반환
// items.value가 모두 0이면 균등 그리드 fallback
export function squarifiedTreemap(
  items: TreemapInput[],
  width: number,
  height: number
): TreemapRect[] {
  if (!items.length) return []

  const totalValue = items.reduce((s, i) => s + i.value, 0)
  if (totalValue <= 0) return uniformGrid(items, width, height)

  const scale = (width * height) / totalValue
  const scaled = [...items]
    .sort((a, b) => b.value - a.value)
    .map(i => ({ id: i.id, value: i.value * scale }))

  const result: TreemapRect[] = []
  squarifyArea(scaled, { x: 0, y: 0, w: width, h: height }, result)
  return result
}

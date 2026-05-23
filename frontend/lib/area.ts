const SQM_PER_PYEONG = 3.305785

export function formatArea(sqm: number): string {
  const pyeong = sqm / SQM_PER_PYEONG
  return `${sqm.toFixed(1)}㎡ (약 ${pyeong.toFixed(1)}평)`
}

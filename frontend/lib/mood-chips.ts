/** 무드 키워드 칩 — 톤 직접 입력(라이트)과 정밀화 모달(다크)이 공유하는 프리셋·순수 로직 */

export const PRESET_MOOD_CHIPS = [
  '모던', '미니멀', '내추럴', '코지', '럭셔리',
  '빈티지', '북유럽', '일본풍', '인더스트리얼', '보헤미안',
  '클래식', '다크무드',
]

/** 프리셋 칩인지 여부 (false면 사용자가 직접 추가한 커스텀 칩) */
export const isPresetChip = (chip: string): boolean => PRESET_MOOD_CHIPS.includes(chip)

/** 칩 선택 토글 — 있으면 제거, 없으면 추가한 새 배열 반환 */
export const toggleChip = (chips: string[], chip: string): string[] =>
  chips.includes(chip) ? chips.filter(c => c !== chip) : [...chips, chip]

/** 커스텀 칩 추가 — 공백·중복은 무시하고 원본을 그대로 반환 */
export const addChip = (chips: string[], input: string): string[] => {
  const trimmed = input.trim()
  if (!trimmed || chips.includes(trimmed)) return chips
  return [...chips, trimmed]
}

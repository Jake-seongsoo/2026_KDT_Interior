'use client'

import { KeyboardEvent, useState } from 'react'
import { cn } from '@/lib/utils'
import { PRESET_MOOD_CHIPS, addChip, isPresetChip, toggleChip } from '@/lib/mood-chips'

type Theme = 'light' | 'dark'

// 라이트(톤 직접 입력)·다크(정밀화 모달) 테마별 클래스 — 기존 두 컴포넌트의 스타일 보존
const THEME: Record<Theme, {
  presetOn: string
  presetOff: string
  custom: string
  customX: string
  input: string
  addBtn: string
}> = {
  light: {
    presetOn: 'border-stone-900 bg-stone-900 text-white',
    presetOff: 'border-stone-200 bg-stone-50 text-stone-600 hover:border-stone-400 hover:bg-stone-100',
    custom: 'border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100',
    customX: 'text-amber-500',
    input: 'border-stone-200 bg-white text-stone-800 placeholder-stone-400 focus:border-stone-400',
    addBtn: 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50',
  },
  dark: {
    presetOn: 'border-amber-500 bg-amber-900/40 text-amber-300',
    presetOff: 'border-stone-700 bg-stone-800 text-stone-300 hover:border-stone-500',
    custom: 'border-amber-700/50 bg-amber-900/30 text-amber-400 hover:bg-amber-900/50',
    customX: 'text-amber-600',
    input: 'border-stone-700 bg-stone-800 text-stone-200 placeholder-stone-500 focus:border-amber-600',
    addBtn: 'border-stone-700 bg-stone-800 text-stone-300 hover:bg-stone-700',
  },
}

interface MoodChipSelectorProps {
  value: string[]
  onChange: (chips: string[]) => void
  theme?: Theme
}

/** 무드 키워드 칩 선택 — 프리셋 토글 + 커스텀 칩 추가/제거. 자유 텍스트 입력은 호출부가 담당. */
export function MoodChipSelector({ value, onChange, theme = 'light' }: MoodChipSelectorProps) {
  const [chipInput, setChipInput] = useState('')
  const t = THEME[theme]

  const handleAdd = () => {
    onChange(addChip(value, chipInput))
    setChipInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className='space-y-2'>
      <div className='flex flex-wrap gap-2'>
        {PRESET_MOOD_CHIPS.map(chip => (
          <button
            key={chip}
            type='button'
            onClick={() => onChange(toggleChip(value, chip))}
            className={cn(
              'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
              value.includes(chip) ? t.presetOn : t.presetOff,
            )}
          >
            {chip}
          </button>
        ))}
        {value.filter(c => !isPresetChip(c)).map(chip => (
          <button
            key={chip}
            type='button'
            onClick={() => onChange(toggleChip(value, chip))}
            className={cn(
              'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium',
              t.custom,
            )}
          >
            {chip}
            <span className={t.customX}>✕</span>
          </button>
        ))}
      </div>

      <div className='flex gap-2'>
        <input
          value={chipInput}
          onChange={e => setChipInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='직접 입력 후 엔터'
          maxLength={20}
          className={cn(
            'max-w-48 flex-1 rounded-lg border px-3 py-1.5 text-xs focus:outline-none',
            t.input,
          )}
        />
        <button
          type='button'
          onClick={handleAdd}
          disabled={!chipInput.trim()}
          className={cn(
            'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40',
            t.addBtn,
          )}
        >
          + 추가
        </button>
      </div>
    </div>
  )
}

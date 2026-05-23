'use client'

import { useState, KeyboardEvent } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const PRESET_CHIPS = [
  '모던', '미니멀', '내추럴', '코지', '럭셔리',
  '빈티지', '북유럽', '일본풍', '인더스트리얼', '보헤미안',
  '클래식', '다크무드',
]

export interface CustomToneInputValue {
  userText: string
  moodChips: string[]
}

interface CustomToneInputProps {
  value: CustomToneInputValue
  onChange: (val: CustomToneInputValue) => void
}

export function CustomToneInput({ value, onChange }: CustomToneInputProps) {
  const [chipInput, setChipInput] = useState('')

  const togglePreset = (chip: string) => {
    const next = value.moodChips.includes(chip)
      ? value.moodChips.filter(c => c !== chip)
      : [...value.moodChips, chip]
    onChange({ ...value, moodChips: next })
  }

  const addCustomChip = () => {
    const trimmed = chipInput.trim()
    if (!trimmed || value.moodChips.includes(trimmed)) {
      setChipInput('')
      return
    }
    onChange({ ...value, moodChips: [...value.moodChips, trimmed] })
    setChipInput('')
  }

  const handleChipKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addCustomChip()
    }
  }

  const removeChip = (chip: string) => {
    onChange({ ...value, moodChips: value.moodChips.filter(c => c !== chip) })
  }

  const isCustomChip = (chip: string) => !PRESET_CHIPS.includes(chip)

  return (
    <div className='space-y-4'>
      <div className='space-y-1.5'>
        <label className='text-sm font-medium text-stone-700'>
          원하는 분위기를 자유롭게 적어주세요
        </label>
        <Textarea
          value={value.userText}
          onChange={e => onChange({ ...value, userText: e.target.value })}
          placeholder='예: 따뜻한 베이지에 우드 포인트, 카페 같은 분위기가 좋아요'
          rows={3}
          maxLength={500}
          className='text-stone-800'
        />
        <p className='text-right text-xs text-stone-400'>{value.userText.length}/500</p>
      </div>

      <div className='space-y-2'>
        <label className='text-sm font-medium text-stone-700'>무드 키워드 선택</label>
        <div className='flex flex-wrap gap-2'>
          {PRESET_CHIPS.map(chip => (
            <button
              key={chip}
              type='button'
              onClick={() => togglePreset(chip)}
              className={cn(
                'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                value.moodChips.includes(chip)
                  ? 'border-stone-900 bg-stone-900 text-white'
                  : 'border-stone-200 bg-stone-50 text-stone-600 hover:border-stone-400 hover:bg-stone-100',
              )}
            >
              {chip}
            </button>
          ))}
          {value.moodChips.filter(isCustomChip).map(chip => (
            <button
              key={chip}
              type='button'
              onClick={() => removeChip(chip)}
              className='inline-flex items-center gap-1 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100'
            >
              {chip}
              <span className='text-amber-500'>✕</span>
            </button>
          ))}
        </div>

        <div className='flex gap-2'>
          <Input
            value={chipInput}
            onChange={e => setChipInput(e.target.value)}
            onKeyDown={handleChipKeyDown}
            placeholder='직접 입력 후 엔터'
            maxLength={20}
            className='max-w-48 text-sm'
          />
          <button
            type='button'
            onClick={addCustomChip}
            disabled={!chipInput.trim()}
            className='rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-medium text-stone-600 hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-40'
          >
            + 추가
          </button>
        </div>
      </div>
    </div>
  )
}

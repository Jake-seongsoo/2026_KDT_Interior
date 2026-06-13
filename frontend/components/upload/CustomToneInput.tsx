'use client'

import { Textarea } from '@/components/ui/textarea'
import { MoodChipSelector } from '@/components/common/MoodChipSelector'

export interface CustomToneInputValue {
  userText: string
  moodChips: string[]
}

interface CustomToneInputProps {
  value: CustomToneInputValue
  onChange: (val: CustomToneInputValue) => void
}

export function CustomToneInput({ value, onChange }: CustomToneInputProps) {
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
        <MoodChipSelector
          value={value.moodChips}
          onChange={chips => onChange({ ...value, moodChips: chips })}
          theme='light'
        />
      </div>
    </div>
  )
}

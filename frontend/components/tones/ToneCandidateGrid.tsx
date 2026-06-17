'use client'

import { CheckCircle2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ToneCandidateOut } from '@/types/api'

interface ToneCandidateGridProps {
  tones: ToneCandidateOut[]
  selectedToneId: string | null
  onSelect: (tone: ToneCandidateOut) => void
}

export function ToneCandidateGrid({ tones, selectedToneId, onSelect }: ToneCandidateGridProps) {
  return (
    <div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3'>
      {tones.map((tone) => {
        const isSelected = tone.id === selectedToneId
        return (
          <button
            key={tone.id}
            data-testid='tone-card'
            onClick={() => onSelect(tone)}
            className={cn(
              'group relative flex flex-col overflow-hidden rounded-xl border bg-white text-left shadow-sm transition-all',
              'hover:-translate-y-1 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300',
              isSelected
                ? 'border-amber-500 ring-2 ring-amber-200 shadow-md -translate-y-1'
                : 'border-stone-200 hover:border-amber-300',
            )}
          >
            {/* 가로 팔레트 바 */}
            <div className='flex h-14 overflow-hidden'>
              {tone.color_palette.slice(0, 5).map((c, i) => (
                <div
                  key={i}
                  title={`${c.name} ${c.role ?? ''}`}
                  className='flex-1 transition-all group-hover:flex-[1.2]'
                  style={{ backgroundColor: c.hex }}
                />
              ))}
            </div>

            {/* 카드 본문 */}
            <div className='flex flex-1 flex-col p-4'>
              <div className='flex items-start justify-between gap-2'>
                <Badge variant={isSelected ? 'success' : 'muted'}>{tone.category}</Badge>
                {isSelected && (
                  <CheckCircle2 className='h-4 w-4 shrink-0 text-amber-600' />
                )}
              </div>

              <h3
                className='mt-3 text-lg font-semibold leading-tight text-stone-900'
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {tone.name}
              </h3>
              <p className='mt-2 text-sm leading-6 text-stone-500'>
                {tone.description}
              </p>

              <div className='mt-4 rounded-lg bg-stone-50 px-3 py-2.5'>
                <p className='text-xs font-medium text-stone-400 mb-1'>AI 추천 이유</p>
                <p className='text-xs leading-5 text-stone-600'>{tone.reason}</p>
              </div>

              {/* 색상 이름 태그 */}
              <div className='mt-3 flex flex-wrap gap-1'>
                {tone.color_palette.slice(0, 3).map((c, i) => (
                  <span
                    key={i}
                    className='flex items-center gap-1 rounded-full border border-stone-100 bg-stone-50 px-2 py-0.5 text-[10px] text-stone-500'
                  >
                    <span
                      className='h-2 w-2 rounded-full'
                      style={{ backgroundColor: c.hex }}
                    />
                    {c.name}
                  </span>
                ))}
              </div>
            </div>

            {isSelected && (
              <div className='border-t border-amber-200 bg-amber-50 py-2 text-center text-xs font-semibold text-amber-700'>
                선택됨
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}

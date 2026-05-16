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
              'min-h-64 rounded-lg border bg-white p-4 text-left shadow-sm transition-all',
              'hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300',
              isSelected ? 'border-teal-500 ring-2 ring-teal-100' : 'border-slate-200',
            )}
          >
            <div className='flex items-start justify-between gap-3'>
              <div className='flex gap-1.5'>
                {tone.color_palette.slice(0, 5).map((c, i) => (
                  <div
                    key={i}
                    title={`${c.name} ${c.role ?? ''}`}
                    className='h-8 w-8 rounded-full border-2 border-white shadow-sm ring-1 ring-slate-200'
                    style={{ backgroundColor: c.hex }}
                  />
                ))}
              </div>
              {isSelected && <CheckCircle2 className='h-5 w-5 shrink-0 text-teal-600' />}
            </div>

            <div className='mt-5 space-y-2'>
              <Badge variant={isSelected ? 'success' : 'muted'}>{tone.category}</Badge>
              <h3 className='text-lg font-bold leading-tight text-slate-950'>{tone.name}</h3>
              <p className='line-clamp-3 text-sm leading-6 text-slate-600'>{tone.description}</p>
            </div>

            <div className='mt-4 rounded-lg bg-slate-50 px-3 py-2'>
              <p className='line-clamp-3 text-xs leading-5 text-slate-600'>{tone.reason}</p>
            </div>

            {isSelected && (
              <div className='mt-4 text-center text-xs font-bold text-teal-700'>
                선택됨
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}

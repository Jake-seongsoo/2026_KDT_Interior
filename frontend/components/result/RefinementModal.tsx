'use client'

import { useState } from 'react'
import { Settings2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { MoodChipSelector } from '@/components/common/MoodChipSelector'
import type { Appliance, RefinementParams } from '@/types/api'

const FAMILY_OPTIONS = [
  { value: 'single', label: '혼자 살아요' },
  { value: 'couple', label: '둘이서 (커플·부부)' },
  { value: 'family_with_kid', label: '아이와 함께' },
  { value: 'family_with_pet', label: '반려동물과 함께' },
] as const

// 신혼 필수 가전 10종 + 기본 배치 방 (도면에 해당 방이 없으면 드롭다운에서 변경 가능)
const APPLIANCE_LIST: Array<{ name: string; defaultRoom: string }> = [
  { name: '냉장고',     defaultRoom: '주방' },
  { name: '김치냉장고', defaultRoom: '주방' },
  { name: '인덕션',     defaultRoom: '주방' },
  { name: '전자레인지', defaultRoom: '주방' },
  { name: '식기세척기', defaultRoom: '주방' },
  { name: '세탁기',     defaultRoom: '다용도실' },
  { name: '건조기',     defaultRoom: '다용도실' },
  { name: '스타일러',   defaultRoom: '다용도실' },
  { name: '공기청정기', defaultRoom: '거실' },
  { name: '로봇청소기', defaultRoom: '거실' },
]

interface RefinementModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (params: RefinementParams) => void
  rooms?: string[]  // 도면에서 인식된 방 유형 목록 (드롭다운 옵션용)
}

export function RefinementModal({ open, onOpenChange, onConfirm, rooms = [] }: RefinementModalProps) {
  const [budget, setBudget] = useState<number | null>(null)
  const [familyType, setFamilyType] = useState<string | null>(null)
  const [moodChips, setMoodChips] = useState<string[]>([])
  const [userText, setUserText] = useState('')
  const [keepAppliances, setKeepAppliances] = useState(false)
  // key: 가전명, value: 배치 방 유형 — key가 존재하면 선택된 상태
  const [applianceSelections, setApplianceSelections] = useState<Record<string, string>>({})

  const toggleAppliance = (name: string, defaultRoom: string) => {
    setApplianceSelections(prev => {
      if (name in prev) {
        const next = { ...prev }
        delete next[name]
        return next
      }
      // 도면에 defaultRoom이 없으면 첫 번째 방으로 폴백
      const room = rooms.includes(defaultRoom) ? defaultRoom : (rooms[0] ?? defaultRoom)
      return { ...prev, [name]: room }
    })
  }

  const setApplianceRoom = (name: string, room: string) => {
    setApplianceSelections(prev => ({ ...prev, [name]: room }))
  }

  const handleConfirm = () => {
    const selectedAppliances: Appliance[] = Object.entries(applianceSelections).map(
      ([name, room]) => ({ name, room }),
    )
    onConfirm({
      budget_10k_won: budget,
      family_type: familyType,
      style_keywords: moodChips.length > 0 ? moodChips : null,
      keep_appliances: keepAppliances || null,
      appliances: selectedAppliances.length > 0 ? selectedAppliances : null,
      user_text: userText.trim() || null,
    })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-w-md max-h-[88vh] overflow-y-auto bg-stone-900 border-stone-700 text-stone-100'>
        <DialogHeader>
          <DialogTitle className='flex items-center gap-2 text-stone-100'>
            <Settings2 className='h-5 w-5 text-amber-500' />
            내 조건으로 정밀화
          </DialogTitle>
          <DialogDescription className='text-stone-400'>
            조건을 입력하면 선택한 톤에 맞게 더 세밀한 시안을 생성합니다.
          </DialogDescription>
        </DialogHeader>

        <div className='space-y-6 py-2'>
          {/* 예산 */}
          <div className='space-y-2'>
            <Label className='text-stone-300 text-sm font-medium'>
              예산 (인테리어 총 비용)
            </Label>
            <div className='space-y-3'>
              <input
                type='range'
                min={500}
                max={10000}
                step={500}
                value={budget ?? 3000}
                onChange={e => setBudget(Number(e.target.value))}
                className='w-full accent-amber-500'
              />
              <div className='flex justify-between text-xs text-stone-400'>
                <span>500만원</span>
                <span className='text-amber-400 font-semibold'>
                  {budget ? `${budget.toLocaleString()}만원` : '미입력'}
                </span>
                <span>1억원</span>
              </div>
              {budget && (
                <button
                  type='button'
                  onClick={() => setBudget(null)}
                  className='text-xs text-stone-500 hover:text-stone-300 underline'
                >
                  예산 입력 취소
                </button>
              )}
            </div>
          </div>

          {/* 가족 형태 */}
          <div className='space-y-2'>
            <Label className='text-stone-300 text-sm font-medium'>가족 형태</Label>
            <div className='grid grid-cols-2 gap-2'>
              {FAMILY_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  type='button'
                  onClick={() => setFamilyType(prev => prev === opt.value ? null : opt.value)}
                  className={[
                    'rounded-lg border px-3 py-2 text-sm text-left transition-colors',
                    familyType === opt.value
                      ? 'border-amber-500 bg-amber-900/40 text-amber-300'
                      : 'border-stone-700 bg-stone-800 text-stone-300 hover:border-stone-500',
                  ].join(' ')}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 직접 입력 + 무드 칩 */}
          <div className='space-y-3'>
            <Label className='text-stone-300 text-sm font-medium'>
              원하는 분위기 <span className='text-stone-500 font-normal'>(선택)</span>
            </Label>

            {/* 자유 텍스트 */}
            <div className='space-y-1'>
              <textarea
                value={userText}
                onChange={e => setUserText(e.target.value)}
                placeholder='예: 거실에 그린톤 포인트 벽을 원해요, 수납이 많았으면 좋겠어요'
                rows={3}
                maxLength={300}
                className='w-full rounded-lg border border-stone-700 bg-stone-800 px-3 py-2 text-sm text-stone-200 placeholder-stone-500 focus:border-amber-600 focus:outline-none resize-none'
              />
              <p className='text-right text-xs text-stone-500'>{userText.length}/300</p>
            </div>

            {/* 무드 칩 — 프리셋 토글 + 커스텀 추가 */}
            <MoodChipSelector value={moodChips} onChange={setMoodChips} theme='dark' />
          </div>

          {/* 기존 가전 유지 */}
          <div className='flex items-center justify-between rounded-lg border border-stone-700 bg-stone-800 px-4 py-3'>
            <div>
              <p className='text-sm font-medium text-stone-200'>기존 가전제품 유지</p>
              <p className='text-xs text-stone-500 mt-0.5'>냉장고·세탁기 등 기존 제품과 어울리는 시안</p>
            </div>
            <button
              type='button'
              role='switch'
              aria-checked={keepAppliances}
              onClick={() => setKeepAppliances(prev => !prev)}
              className={[
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                keepAppliances ? 'bg-amber-600' : 'bg-stone-600',
              ].join(' ')}
            >
              <span
                className={[
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  keepAppliances ? 'translate-x-6' : 'translate-x-1',
                ].join(' ')}
              />
            </button>
          </div>

          {/* 신혼 가전 배치 */}
          <div className='space-y-3'>
            <div>
              <Label className='text-stone-300 text-sm font-medium'>
                신혼 가전 배치 <span className='text-stone-500 font-normal'>(선택)</span>
              </Label>
              <p className='text-xs text-stone-500 mt-0.5'>
                보유하거나 구입 예정인 가전을 체크하면 해당 공간에 맞게 렌더링합니다.
              </p>
            </div>
            <div className='space-y-2'>
              {APPLIANCE_LIST.map(({ name, defaultRoom }) => {
                const checked = name in applianceSelections
                const selectedRoom = applianceSelections[name] ?? defaultRoom
                // 드롭다운 옵션: 도면 방 목록 + defaultRoom 항상 포함
                const roomOptions = Array.from(new Set([...rooms, defaultRoom]))
                return (
                  <div key={name} className='flex items-center gap-3'>
                    <button
                      type='button'
                      role='checkbox'
                      aria-checked={checked}
                      onClick={() => toggleAppliance(name, defaultRoom)}
                      className={[
                        'flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors',
                        checked
                          ? 'border-amber-500 bg-amber-600 text-white'
                          : 'border-stone-600 bg-stone-800',
                      ].join(' ')}
                    >
                      {checked && <span className='text-[10px] font-bold'>✓</span>}
                    </button>
                    <span
                      className={[
                        'flex-1 text-sm',
                        checked ? 'text-stone-200' : 'text-stone-500',
                      ].join(' ')}
                    >
                      {name}
                    </span>
                    {checked && (
                      <select
                        value={selectedRoom}
                        onChange={e => setApplianceRoom(name, e.target.value)}
                        className='rounded border border-stone-600 bg-stone-800 px-2 py-1 text-xs text-stone-300 focus:border-amber-600 focus:outline-none'
                      >
                        {roomOptions.map(r => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    )}
                  </div>
                )
              })}
            </div>
            <p className='text-xs text-stone-600'>
              AI 렌더링 예시이며 실제 가전 위치·치수는 시공 환경에 따라 달라질 수 있습니다.
            </p>
          </div>
        </div>

        <DialogFooter className='gap-2'>
          <Button
            variant='outline'
            size='sm'
            onClick={() => onOpenChange(false)}
            className='border-stone-700 bg-stone-800 text-stone-300 hover:bg-stone-700 hover:text-stone-100'
          >
            취소
          </Button>
          <Button
            size='sm'
            onClick={handleConfirm}
            className='bg-amber-700 text-white hover:bg-amber-600'
          >
            이 조건으로 재렌더링
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

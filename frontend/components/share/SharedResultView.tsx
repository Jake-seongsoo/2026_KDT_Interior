'use client'

import { useRef, useState } from 'react'
import Link from 'next/link'
import { Sparkles } from 'lucide-react'
import { LayoutCanvas } from '@/components/result/LayoutCanvas'
import { RoomTabs } from '@/components/result/RoomTabs'
import { Button } from '@/components/ui/button'
import type { RenderResponse } from '@/types/api'

interface SharedResultViewProps {
  data: RenderResponse
}

/** 공유 링크로 열린 읽기 전용 결과 뷰 — 톤 + 방별 렌더만(상품·편집 기능 제외). */
export function SharedResultView({ data }: SharedResultViewProps) {
  const tone = data.selected_tone
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(
    data.room_results[0]?.room_id ?? null,
  )
  const roomTabsRef = useRef<HTMLElement | null>(null)

  function handleRoomClick(roomId: string) {
    setSelectedRoomId(roomId)
    roomTabsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-ivory'>
      {/* 톤 히어로 — 다크 섹션 (읽기 전용, 편집 버튼 없음) */}
      <section className='bg-stone-950'>
        <div className='mx-auto max-w-6xl px-4 py-10 sm:px-6'>
          <p className='mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-amber-600'>
            Shared Tone
          </p>
          <div className='flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between'>
            <div className='flex-1'>
              <h1
                className='text-3xl font-bold tracking-tight text-stone-100 sm:text-4xl'
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {tone.name}
              </h1>
              <p className='mt-3 max-w-2xl text-sm leading-7 text-stone-400'>{tone.description}</p>
            </div>
            <span className='inline-flex h-6 shrink-0 items-center rounded-full border border-amber-700/40 bg-amber-700/20 px-2.5 text-xs font-medium text-amber-400'>
              {tone.category}
            </span>
          </div>

          {/* 팔레트 바 */}
          <div className='mt-8 overflow-hidden rounded-xl' style={{ height: 48 }}>
            <div className='flex h-full'>
              {tone.color_palette.map((c, i) => (
                <div key={i} title={c.name} className='group relative flex-1' style={{ backgroundColor: c.hex }}>
                  <span className='absolute bottom-0 left-0 right-0 bg-black/50 py-0.5 text-center text-[9px] text-white opacity-0 transition-opacity group-hover:opacity-100'>
                    {c.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 메인 콘텐츠 */}
      <div className='mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6'>
        <LayoutCanvas
          rooms={data.room_results.map(r => ({
            room_id: r.room_id,
            room_type: r.room_type,
            area_sqm: null,  // 공유 응답엔 면적 정보 없음 — 균등 분할 배치도
          }))}
          activeRoomId={selectedRoomId}
          onRoomClick={handleRoomClick}
        />

        <section ref={roomTabsRef} className='scroll-mt-4'>
          <div className='mb-5'>
            <h2 className='text-xl font-bold text-stone-900' style={{ fontFamily: 'var(--font-serif)' }}>
              방별 제안
            </h2>
            <p className='mt-1 text-sm text-stone-500'>공간별 렌더 이미지와 추천 근거를 확인하세요.</p>
          </div>
          {/* 공유는 상품 제외 (showProducts=false) */}
          <RoomTabs
            rooms={data.room_results}
            activeRoomId={selectedRoomId}
            onChange={setSelectedRoomId}
            showProducts={false}
          />
        </section>

        {/* 전환 유도 CTA */}
        <div className='rounded-2xl border border-stone-200 bg-white p-6 text-center shadow-sm'>
          <div className='mb-2 flex items-center justify-center gap-2 text-amber-600'>
            <Sparkles className='h-4 w-4' />
            <span className='text-sm font-semibold text-stone-800'>나도 내 도면으로 만들어보기</span>
          </div>
          <p className='mb-4 text-xs text-stone-500'>
            도면 한 장으로 AI가 공간에 맞는 톤과 방별 연출안을 제안합니다.
          </p>
          <Button asChild>
            <Link href='/'>새 도면 분석하기</Link>
          </Button>
        </div>

        {/* 푸터 면책 */}
        <div className='border-t border-stone-200 pt-5 text-xs leading-5 text-stone-400'>
          <p>{data.disclaimer}</p>
        </div>
      </div>
    </div>
  )
}

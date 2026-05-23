import Image from 'next/image'
import { ImageOff, Sparkles } from 'lucide-react'
import type { RoomResultOut } from '@/types/api'
import { ProductGrid } from './ProductGrid'

interface RoomRenderCardProps {
  room: RoomResultOut
}

export function RoomRenderCard({ room }: RoomRenderCardProps) {
  return (
    <div className='space-y-6'>
      {/* 렌더 이미지 */}
      <div className='relative aspect-[16/9] overflow-hidden rounded-2xl border border-stone-200 bg-stone-100'>
        {room.render_url ? (
          <>
            <Image
              src={room.render_url}
              alt={`${room.room_type} 인테리어 제안`}
              fill
              className='object-cover transition-transform duration-700 hover:scale-[1.02]'
              sizes='(max-width: 768px) 100vw, 900px'
            />
            <div className='absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-black/40 to-transparent' />
            <div className='absolute bottom-3 right-3 rounded-md bg-black/60 px-2.5 py-1 text-[10px] font-medium text-white backdrop-blur-sm'>
              AI 생성 이미지
            </div>
          </>
        ) : (
          <div className='flex h-full flex-col items-center justify-center gap-2 text-stone-400'>
            <ImageOff className='h-8 w-8' />
            <p className='text-sm'>이미지 생성 실패</p>
          </div>
        )}
      </div>

      {/* AI 추천 근거 */}
      <div className='rounded-xl border border-stone-200 bg-white p-5'>
        <div className='flex items-center gap-2 mb-3'>
          <Sparkles className='h-4 w-4 text-amber-600' />
          <h3 className='text-sm font-semibold text-stone-900'>AI 추천 근거</h3>
        </div>
        <p className='text-sm leading-7 text-stone-600'>{room.rationale}</p>
      </div>

      {/* 추천 상품 */}
      <div className='space-y-3'>
        <div className='flex items-center justify-between'>
          <h3 className='text-sm font-semibold text-stone-900'>추천 상품</h3>
          <span className='text-xs text-stone-400'>{room.products.length}개</span>
        </div>
        <ProductGrid products={room.products} />
      </div>
    </div>
  )
}

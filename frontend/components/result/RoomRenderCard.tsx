import Image from 'next/image'
import { ImageOff, Sparkles } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { RoomResultOut } from '@/types/api'
import { ProductGrid } from './ProductGrid'

interface RoomRenderCardProps {
  room: RoomResultOut
}

export function RoomRenderCard({ room }: RoomRenderCardProps) {
  return (
    <div className='space-y-5'>
      <div className='relative aspect-[4/3] overflow-hidden rounded-lg border border-slate-200 bg-slate-100'>
        {room.render_url ? (
          <>
            <Image
              src={room.render_url}
              alt={`${room.room_type} 인테리어 제안`}
              fill
              className='object-cover'
              sizes='(max-width: 768px) 100vw, 900px'
            />
            <div className='absolute bottom-3 right-3 rounded-md bg-slate-950/75 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur'>
              AI 생성 이미지
            </div>
          </>
        ) : (
          <div className='flex h-full flex-col items-center justify-center gap-2 text-slate-400'>
            <ImageOff className='h-8 w-8' />
            <p className='text-sm'>이미지 생성 실패</p>
          </div>
        )}
      </div>

      <Card>
        <CardContent className='space-y-3'>
          <div className='flex items-center gap-2'>
            <Sparkles className='h-4 w-4 text-teal-600' />
            <h3 className='text-sm font-bold text-slate-950'>AI 추천 근거</h3>
          </div>
          <p className='text-sm leading-7 text-slate-600'>{room.rationale}</p>
        </CardContent>
      </Card>

      <div className='space-y-3'>
        <div className='flex items-center justify-between'>
          <h3 className='text-sm font-bold text-slate-950'>추천 상품</h3>
          <Badge variant='muted'>{room.products.length}개</Badge>
        </div>
        <ProductGrid products={room.products} />
      </div>
    </div>
  )
}

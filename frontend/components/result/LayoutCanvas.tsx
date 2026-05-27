'use client'

import { useMemo } from 'react'
import { Map as MapIcon, Sofa, Bed, UtensilsCrossed, Bath, LayoutGrid } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { squarifiedTreemap } from '@/lib/treemap'

const CANVAS_W = 600
const CANVAS_H = 400

const ROOM_PALETTES = [
  { bg: '#FEF9EE', border: '#FDE68A', text: '#92400E' },
  { bg: '#F0FDF4', border: '#86EFAC', text: '#15803D' },
  { bg: '#F5F3FF', border: '#C4B5FD', text: '#5B21B6' },
  { bg: '#FFF1F2', border: '#FECDD3', text: '#9F1239' },
]

function roomIcon(roomType: string) {
  const t = roomType
  if (t.includes('거실')) return Sofa
  if (t.includes('주방') || t.includes('식당') || t.includes('부엌')) return UtensilsCrossed
  if (t.includes('욕실') || t.includes('화장실') || t.includes('바스')) return Bath
  if (t.includes('침실') || t.includes('방') || t.includes('안방')) return Bed
  return LayoutGrid
}

interface RoomItem {
  room_id: string
  room_type: string
  area_sqm?: number | null
}

interface LayoutCanvasProps {
  rooms: RoomItem[]
  activeRoomId?: string | null
  onRoomClick?: (roomId: string) => void
}

export function LayoutCanvas({ rooms, activeRoomId, onRoomClick }: LayoutCanvasProps) {
  const hasArea = rooms.every(r => r.area_sqm != null && r.area_sqm > 0)
  const totalArea = hasArea ? rooms.reduce((s, r) => s + (r.area_sqm ?? 0), 0) : 0

  const rects = useMemo(() => {
    const items = rooms.map(r => ({
      id: r.room_id,
      value: hasArea ? (r.area_sqm ?? 1) : 1,
    }))
    return squarifiedTreemap(items, CANVAS_W, CANVAS_H)
  }, [rooms, hasArea])

  const rectById = new Map(rects.map(r => [r.id, r]))

  return (
    <Card className='overflow-hidden'>
      <CardHeader className='flex flex-row items-center gap-2 pb-2'>
        <MapIcon className='h-4 w-4 shrink-0 text-amber-600' />
        <div>
          <h2 className='text-sm font-semibold text-stone-900'>2D 공간 배치도</h2>
          <p className='text-xs text-stone-400'>
            {hasArea && totalArea > 0
              ? `총 면적 ${totalArea.toFixed(1)}㎡ · 사각형 크기는 실제 면적 비율`
              : '공간 구성 시각화'}
          </p>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className='relative w-full overflow-hidden rounded-xl border border-stone-200 bg-stone-50'
          style={{ aspectRatio: `${CANVAS_W}/${CANVAS_H}` }}
        >
          {rooms.map((room, i) => {
            const rect = rectById.get(room.room_id)
            if (!rect) return null

            const palette = ROOM_PALETTES[i % ROOM_PALETTES.length]
            const isActive = room.room_id === activeRoomId
            const Icon = roomIcon(room.room_type)
            const pct =
              hasArea && totalArea > 0 && room.area_sqm
                ? Math.round((room.area_sqm / totalArea) * 100)
                : null

            const minDim = Math.min(rect.w, rect.h)
            const iconSize = Math.max(12, Math.min(minDim * 0.14, 28))
            const nameSize = Math.max(10, Math.min(minDim * 0.1, 16))
            const subSize = Math.max(9, Math.min(minDim * 0.07, 12))

            // 셀 높이에 따라 표시 요소 조절 (캔버스 단위 기준)
            const showName = rect.h >= 45 && rect.w >= 50
            const showArea = rect.h >= 65 && rect.w >= 55

            return (
              <button
                key={room.room_id}
                onClick={() => onRoomClick?.(room.room_id)}
                title={`${room.room_type}${room.area_sqm ? ` ${room.area_sqm.toFixed(1)}㎡` : ''}`}
                className='absolute flex flex-col items-center justify-center gap-0.5 overflow-hidden p-1 transition-all hover:brightness-90'
                style={{
                  left: `${(rect.x / CANVAS_W) * 100}%`,
                  top: `${(rect.y / CANVAS_H) * 100}%`,
                  width: `${(rect.w / CANVAS_W) * 100}%`,
                  height: `${(rect.h / CANVAS_H) * 100}%`,
                  backgroundColor: palette.bg,
                  border: `2px solid ${isActive ? '#B45309' : palette.border}`,
                  outline: isActive ? '2px solid #B45309' : 'none',
                  outlineOffset: '-3px',
                  cursor: onRoomClick ? 'pointer' : 'default',
                }}
              >
                <Icon
                  style={{ width: iconSize, height: iconSize, color: palette.text, flexShrink: 0 }}
                />
                {showName && (
                  <span
                    className='overflow-hidden text-ellipsis whitespace-nowrap font-semibold leading-tight'
                    style={{ fontSize: nameSize, color: palette.text, maxWidth: '90%' }}
                  >
                    {room.room_type}
                  </span>
                )}
                {showArea && room.area_sqm && (
                  <span
                    className='overflow-hidden text-ellipsis whitespace-nowrap text-stone-500 leading-tight'
                    style={{ fontSize: subSize, maxWidth: '90%' }}
                  >
                    {room.area_sqm.toFixed(1)}㎡{pct !== null ? ` (${pct}%)` : ''}
                  </span>
                )}
              </button>
            )
          })}
        </div>
        {onRoomClick && (
          <p className='mt-2 text-center text-xs text-stone-400'>
            방을 클릭하면 아래 제안으로 이동합니다
          </p>
        )}
      </CardContent>
    </Card>
  )
}

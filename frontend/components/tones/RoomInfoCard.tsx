'use client'

import { useState } from 'react'
import { Check, Pencil, X } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { RoomCorrection, RoomOut } from '@/types/api'

interface RoomInfoCardProps {
  rooms: RoomOut[]
  /** 방 이름 수정 저장 핸들러 (F003). 전달 시 편집 기능이 활성화된다. */
  onSave?: (corrections: RoomCorrection[]) => Promise<void>
}

export function RoomInfoCard({ rooms, onSave }: RoomInfoCardProps) {
  const [editing, setEditing] = useState(false)
  const [names, setNames] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startEdit = () => {
    setNames(Object.fromEntries(rooms.map((r) => [r.id, r.room_type])))
    setError(null)
    setEditing(true)
  }

  const cancelEdit = () => {
    setEditing(false)
    setError(null)
  }

  const handleSave = async () => {
    if (!onSave) return
    const corrections: RoomCorrection[] = rooms
      .map((r) => ({ id: r.id, room_type: (names[r.id] ?? '').trim() }))
      .filter((c) => c.room_type && c.room_type !== rooms.find((r) => r.id === c.id)?.room_type)

    if (corrections.length === 0) {
      setEditing(false)
      return
    }

    setSaving(true)
    setError(null)
    try {
      await onSave(corrections)
      setEditing(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader className='flex flex-row items-center justify-between'>
        <h2 className='text-sm font-semibold text-stone-900'>인식한 공간 구성</h2>
        {editing ? (
          <div className='flex items-center gap-1'>
            <button
              type='button'
              onClick={cancelEdit}
              disabled={saving}
              aria-label='수정 취소'
              className='inline-flex h-7 w-7 items-center justify-center rounded-md text-stone-400 hover:bg-stone-100 hover:text-stone-700 disabled:opacity-50'
            >
              <X className='h-4 w-4' />
            </button>
            <button
              type='button'
              onClick={handleSave}
              disabled={saving}
              data-testid='rooms-save'
              className='inline-flex h-7 items-center gap-1 rounded-md bg-amber-700 px-2.5 text-xs font-semibold text-white hover:bg-amber-600 disabled:opacity-50'
            >
              <Check className='h-3.5 w-3.5' />
              {saving ? '저장 중' : '저장'}
            </button>
          </div>
        ) : (
          <div className='flex items-center gap-2'>
            <Badge variant='muted'>{rooms.length}개 공간</Badge>
            {onSave && (
              <button
                type='button'
                onClick={startEdit}
                data-testid='rooms-edit'
                aria-label='방 이름 수정'
                className='inline-flex h-7 w-7 items-center justify-center rounded-md text-stone-400 hover:bg-stone-100 hover:text-stone-700'
              >
                <Pencil className='h-3.5 w-3.5' />
              </button>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className='space-y-2.5'>
        {editing && (
          <p className='rounded-lg bg-stone-50 px-3 py-2 text-xs leading-relaxed text-stone-500'>
            AI가 잘못 인식한 방 이름을 직접 고칠 수 있어요. 수정하면 다음 시안 생성에 반영됩니다.
          </p>
        )}
        {rooms.map((room, i) => (
          <div
            key={room.id}
            className='rounded-xl border border-stone-100 bg-stone-50 p-3'
          >
            <div className='flex items-center justify-between gap-3 mb-2'>
              <div className='flex min-w-0 flex-1 items-center gap-2.5'>
                <span className='flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-stone-200 text-[11px] font-bold text-stone-600'>
                  {i + 1}
                </span>
                {editing ? (
                  <input
                    type='text'
                    value={names[room.id] ?? ''}
                    onChange={(e) => setNames((prev) => ({ ...prev, [room.id]: e.target.value }))}
                    maxLength={20}
                    aria-label={`${i + 1}번 방 이름`}
                    className='h-8 min-w-0 flex-1 rounded-md border border-stone-300 bg-white px-2 text-sm text-stone-900 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100'
                  />
                ) : (
                  <div className='min-w-0'>
                    <p className='truncate text-sm font-semibold text-stone-900'>{room.room_type}</p>
                    {room.area_sqm && (
                      <p className='text-xs text-stone-400'>{room.area_sqm.toFixed(1)}㎡</p>
                    )}
                  </div>
                )}
              </div>
              {!editing && (
                <span className='text-xs font-medium text-stone-400 shrink-0'>
                  {Math.round(room.confidence * 100)}%
                </span>
              )}
            </div>
            {!editing && (
              <div className='h-1 overflow-hidden rounded-full bg-stone-200'>
                <div
                  className='h-full rounded-full bg-amber-500 transition-all'
                  style={{ width: `${Math.round(room.confidence * 100)}%` }}
                />
              </div>
            )}
          </div>
        ))}
        {error && (
          <p className='rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600'>
            {error}
          </p>
        )}
        {!editing && rooms.some((r) => r.confidence < 0.65) && (
          <p className='rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-700'>
            일부 방의 인식 신뢰도가 낮습니다. {onSave ? '연필 아이콘을 눌러 직접 고치거나, ' : ''}방 경계와 이름이 선명한 도면을 사용하면 정확도가 올라갑니다.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

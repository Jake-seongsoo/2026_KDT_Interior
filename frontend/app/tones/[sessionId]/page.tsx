'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, getAnalyzeResult } from '@/lib/api'
import { RoomInfoCard } from '@/components/tones/RoomInfoCard'
import { ToneCandidateGrid } from '@/components/tones/ToneCandidateGrid'
import { Button } from '@/components/ui/button'
import type { AnalyzeResponse, ToneCandidateOut } from '@/types/api'

export default function TonesPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const router = useRouter()

  const [data, setData] = useState<AnalyzeResponse | null>(null)
  const [selectedTone, setSelectedTone] = useState<ToneCandidateOut | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    const load = async () => {
      const raw = sessionStorage.getItem(`analyze:${sessionId}`)
      if (raw) {
        setData(JSON.parse(raw))
        return
      }

      try {
        const result = await getAnalyzeResult(sessionId)
        if (ignore) return
        sessionStorage.setItem(`analyze:${result.session_id}`, JSON.stringify(result))
        setData(result)
      } catch (e) {
        if (ignore) return
        if (e instanceof AuthRequiredError) {
          router.replace(`/auth/login?next=/tones/${sessionId}`)
          return
        }
        setError(e instanceof Error ? e.message : '분석 결과를 불러오지 못했습니다.')
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [sessionId, router])

  const handleProceed = () => {
    if (!selectedTone || !data) return
    sessionStorage.setItem(`tone:${sessionId}`, JSON.stringify(selectedTone))
    router.push(`/render/${sessionId}`)
  }

  if (error) {
    return (
      <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 bg-[#F5EFE5]'>
        <div className='w-full max-w-md space-y-4 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm'>
          <p className='rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700'>{error}</p>
          <Button asChild className='w-full'>
            <Link href='/'>새 도면 분석하기</Link>
          </Button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center bg-[#F5EFE5]'>
        <p className='text-sm text-stone-400'>불러오는 중...</p>
      </div>
    )
  }

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-[#F5EFE5]'>
      <div className='mx-auto max-w-6xl px-4 py-10 sm:px-6'>

        {/* 페이지 헤더 */}
        <div className='mb-10'>
          <p className='mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700'>
            분석 완료
          </p>
          <h1
            className='text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            인테리어 톤을 선택하세요
          </h1>
          <p className='mt-3 max-w-2xl text-sm leading-6 text-stone-500'>
            AI가 도면을 분석해 공간에 맞는 톤 후보를 준비했습니다. 하나를 선택하면 방별 연출안을 생성합니다.
          </p>
          {data.has_reference && (
            <span className='mt-3 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800'>
              <span className='h-1.5 w-1.5 rounded-full bg-amber-500' />
              내 레퍼런스 이미지 기반 톤
            </span>
          )}
        </div>

        {data.warnings.length > 0 && (
          <div className='mb-6 space-y-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3'>
            {data.warnings.map((w, i) => (
              <p key={i} className='text-sm text-amber-700'>{w}</p>
            ))}
          </div>
        )}

        <div className='grid gap-8 lg:grid-cols-[300px_1fr]'>
          {/* 사이드바: 방 정보 */}
          <aside className='lg:sticky lg:top-20 lg:self-start'>
            <RoomInfoCard rooms={data.rooms} />
          </aside>

          {/* 메인: 톤 선택 */}
          <section className='space-y-4'>
            <div className='flex items-center justify-between'>
              <h2 className='text-base font-semibold text-stone-900'>추천 톤</h2>
              <span className='text-sm text-stone-400'>{data.tone_candidates.length}가지</span>
            </div>
            <ToneCandidateGrid
              tones={data.tone_candidates}
              selectedToneId={selectedTone?.id ?? null}
              onSelect={setSelectedTone}
            />
          </section>
        </div>

        {/* 하단 CTA */}
        <div className='sticky bottom-4 mt-8'>
          <div className='rounded-2xl border border-stone-200 bg-white/95 p-3 shadow-lg backdrop-blur-sm'>
            <Button
              onClick={handleProceed}
              disabled={!selectedTone}
              className='w-full'
              size='lg'
            >
              {selectedTone
                ? `"${selectedTone.name}"으로 제안 만들기`
                : '톤을 선택해 주세요'}
              <ArrowRight className='h-4 w-4' />
            </Button>
          </div>
        </div>

      </div>
    </div>
  )
}

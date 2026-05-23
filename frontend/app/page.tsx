'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FloorPlanUploader } from '@/components/upload/FloorPlanUploader'
import { CustomToneInput, type CustomToneInputValue } from '@/components/upload/CustomToneInput'
import { modeStorage, customInputStorage } from '@/lib/session-storage'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'
import type { ToneMode } from '@/lib/session-storage'

export default function HomePage() {
  const router = useRouter()
  const [mode, setMode] = useState<ToneMode>('auto')
  const [customInput, setCustomInput] = useState<CustomToneInputValue>({
    userText: '',
    moodChips: [],
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const ensureLoggedIn = async () => {
    const supabase = createClient()
    const { data } = await supabase.auth.getSession()

    if (!data.session) {
      alert('도면 업로드와 AI 분석을 진행하려면 먼저 로그인이 필요합니다.')
      router.push('/auth/login?next=/')
      return false
    }

    return true
  }

  const handleUpload = async (file: File, floorAreaPyeong: number) => {
    if (!(await ensureLoggedIn())) {
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = e.target?.result as string
      sessionStorage.setItem('upload:file:base64', base64)
      sessionStorage.setItem('upload:file:name', file.name)
      sessionStorage.setItem('upload:file:type', file.type)
      sessionStorage.setItem('upload:floorArea', String(floorAreaPyeong))

      modeStorage.set(mode)
      if (mode === 'custom') {
        customInputStorage.set({
          userText: customInput.userText.trim(),
          moodChips: customInput.moodChips,
        })
      } else {
        customInputStorage.clear()
      }

      router.push('/analyze')
    }
    reader.readAsDataURL(file)
  }

  const autoSteps = [
    { step: '01', label: '도면 업로드', desc: '분양 도면이나 네이버 부동산 캡처' },
    { step: '02', label: '방 구성 분석', desc: 'Claude Vision으로 공간 인식' },
    { step: '03', label: '인테리어 톤 선택', desc: '2026 트렌드 기반 6가지 팔레트' },
    { step: '04', label: '방별 제안 확인', desc: 'Imagen 렌더링 + 이케아 추천 상품' },
  ]

  const customSteps = [
    { step: '01', label: '도면 업로드', desc: '분양 도면이나 네이버 부동산 캡처' },
    { step: '02', label: '원하는 분위기 입력', desc: '자유 텍스트 + 무드 키워드 선택' },
    { step: '03', label: '톤 변형 3가지 확인', desc: '안전 · 중립 · 대담 해석 중 선택' },
    { step: '04', label: '방별 제안 확인', desc: 'Imagen 렌더링 + 이케아 추천 상품' },
  ]

  const steps = mode === 'auto' ? autoSteps : customSteps

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-[#F5EFE5]'>
      <div className='mx-auto grid max-w-6xl gap-12 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_420px] lg:py-20 lg:gap-16 lg:items-start'>

        {/* 좌측: 헤드라인 + 설명 */}
        <section className='lg:pt-4'>
          <p className='mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700'>
            2026 인테리어 톤 추천
          </p>

          <h1
            className='text-4xl font-bold leading-[1.2] tracking-tight text-stone-900 sm:text-5xl lg:text-6xl'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            도면 한 장으로
            <br />
            <span className='text-stone-400'>공간의 방향을</span>
            <br />
            읽습니다.
          </h1>

          <p className='mt-6 max-w-lg text-base leading-8 text-stone-500'>
            AI가 평면도를 분석해 공간 구성을 파악하고, 어울리는 톤과 방별 연출안, 추천 가구까지 한 흐름으로 제안합니다.
          </p>

          {/* 스텝 표시 */}
          <div className='mt-10 space-y-4'>
            {steps.map(({ step, label, desc }) => (
              <div key={step} className='flex items-start gap-4'>
                <span
                  className='mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-stone-900 text-[11px] font-bold text-amber-100'
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {step}
                </span>
                <div>
                  <p className='text-sm font-semibold text-stone-800'>{label}</p>
                  <p className='text-xs text-stone-400 mt-0.5'>{desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className='mt-10 h-px w-24 bg-stone-300' />

          <p className='mt-6 text-xs leading-6 text-stone-400 max-w-sm'>
            아파트 분양 도면·네이버 부동산 캡처에 최적화. 방 경계와 이름이 선명한 이미지를 사용하세요.
          </p>
        </section>

        {/* 우측: 업로드 카드 */}
        <div className='rounded-2xl border border-stone-200 bg-white p-6 shadow-sm sm:p-7'>
          {/* 모드 선택 토글 */}
          <div className='mb-5 flex rounded-lg border border-stone-200 bg-stone-50 p-1'>
            {(['auto', 'custom'] as const).map(m => (
              <button
                key={m}
                type='button'
                onClick={() => setMode(m)}
                className={cn(
                  'flex-1 rounded-md py-2 text-sm font-medium transition-all',
                  mode === m
                    ? 'bg-white text-stone-900 shadow-sm'
                    : 'text-stone-500 hover:text-stone-700',
                )}
              >
                {m === 'auto' ? 'AI 자동 추천' : '직접 입력'}
              </button>
            ))}
          </div>

          <div className='mb-5'>
            <h2
              className='text-xl font-semibold text-stone-900'
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              도면 업로드
            </h2>
            <p className='mt-1.5 text-sm text-stone-400'>
              {mode === 'auto'
                ? '공급면적과 도면 이미지를 입력해 주세요.'
                : '도면 + 원하는 분위기를 함께 입력해 주세요.'}
            </p>
          </div>

          <FloorPlanUploader
            onSubmit={handleUpload}
            onBeforeFileSelect={ensureLoggedIn}
            onFileChange={setSelectedFile}
            formId={mode === 'custom' ? 'upload-form' : undefined}
            hideSubmit={mode === 'custom'}
          />

          {mode === 'custom' && (
            <div className='mt-5 border-t border-stone-100 pt-5 space-y-5'>
              <CustomToneInput value={customInput} onChange={setCustomInput} />
              <button
                form='upload-form'
                type='submit'
                disabled={!selectedFile || !customInput.userText.trim()}
                className={cn(
                  'w-full rounded-lg py-3 text-sm font-semibold transition-colors',
                  (!selectedFile || !customInput.userText.trim())
                    ? 'cursor-not-allowed bg-stone-200 text-stone-400'
                    : 'bg-stone-900 text-white hover:bg-stone-700',
                )}
              >
                분석 시작
              </button>
              {!customInput.userText.trim() && selectedFile && (
                <p className='text-center text-xs text-stone-400'>원하는 분위기를 입력해야 분석을 시작할 수 있습니다.</p>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

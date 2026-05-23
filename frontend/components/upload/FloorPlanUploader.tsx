'use client'

import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { FileImage, UploadCloud } from 'lucide-react'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const schema = z.object({
  floorArea: z
    .number({ invalid_type_error: '숫자를 입력해 주세요.' })
    .min(5, '5평 이상이어야 합니다.')
    .max(200, '200평 이하이어야 합니다.'),
})

type FormValues = z.infer<typeof schema>

interface FloorPlanUploaderProps {
  onSubmit: (file: File, floorAreaPyeong: number) => void | Promise<void>
  onBeforeFileSelect?: () => boolean | Promise<boolean>
  isLoading?: boolean
}

export function FloorPlanUploader({ onSubmit, onBeforeFileSelect, isLoading }: FloorPlanUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { floorArea: 30 },
  })

  const canSelectFile = async () => {
    if (!onBeforeFileSelect) return true
    return await onBeforeFileSelect()
  }

  const handleFile = async (file: File) => {
    if (!(await canSelectFile())) return

    if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
      alert('JPG 또는 PNG 파일만 지원합니다.')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('파일 크기는 5MB 이하이어야 합니다.')
      return
    }
    setSelectedFile(file)
    setPreview(URL.createObjectURL(file))
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) await handleFile(file)
  }

  const handleUploadAreaClick = async () => {
    if (!(await canSelectFile())) return
    fileInputRef.current?.click()
  }

  const onFormSubmit = (values: FormValues) => {
    if (!selectedFile) {
      alert('도면 파일을 선택해 주세요.')
      return
    }
    onSubmit(selectedFile, values.floorArea)
  }

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className='space-y-5'>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={handleUploadAreaClick}
        className={cn(
          'group cursor-pointer rounded-xl border border-dashed p-4 transition-all sm:p-5',
          dragOver
            ? 'border-amber-400 bg-amber-50'
            : preview
              ? 'border-amber-300 bg-white'
              : 'border-stone-300 bg-stone-50 hover:border-amber-300 hover:bg-white',
        )}
      >
        <input
          ref={fileInputRef}
          type='file'
          accept='image/jpeg,image/png'
          className='hidden'
          onClick={(e) => {
            e.stopPropagation()
          }}
          onChange={async (e) => {
            const f = e.target.files?.[0]
            if (f) await handleFile(f)
          }}
        />

        {preview ? (
          <div className='space-y-3'>
            <div className='overflow-hidden rounded-xl border border-stone-200 bg-stone-100'>
              <img
                src={preview}
                alt='도면 미리보기'
                className='mx-auto max-h-64 w-full object-contain'
              />
            </div>
            <div className='flex items-center gap-2 text-sm text-stone-700'>
              <FileImage className='h-4 w-4 text-amber-700' />
              <span className='truncate font-medium'>{selectedFile?.name}</span>
            </div>
            <p className='text-xs text-stone-400'>클릭하면 다른 파일로 교체할 수 있습니다.</p>
          </div>
        ) : (
          <div className='flex flex-col items-center justify-center py-8 text-center'>
            <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white text-amber-700 shadow-sm ring-1 ring-stone-200'>
              <UploadCloud className='h-6 w-6' />
            </div>
            <p className='text-sm font-semibold text-stone-900'>
              도면 이미지를 드래그하거나 클릭해서 선택
            </p>
            <p className='mt-2 text-xs text-stone-500'>JPG / PNG, 최대 5MB</p>
            <p className='mt-1 text-xs text-stone-400'>
              방 경계와 이름이 잘 보이는 분양 도면을 권장합니다.
            </p>
          </div>
        )}
      </div>

      <div className='space-y-2'>
        <label className='text-sm font-semibold text-stone-800'>
          공급면적 <span className='font-normal text-stone-400'>(평형, 예: 32)</span>
        </label>
        <input
          type='number'
          step='0.5'
          {...register('floorArea', { valueAsNumber: true })}
          className='h-11 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm text-stone-900 shadow-sm outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100'
          placeholder='예: 32'
        />
        {errors.floorArea && (
          <p className='text-xs text-red-600'>{errors.floorArea.message}</p>
        )}
        <p className='text-xs leading-5 text-stone-400'>
          82.55㎡처럼 제곱미터가 아닌, 흔히 말하는 25평·32평 기준으로 입력해 주세요.
        </p>
      </div>

      <p className='rounded-xl bg-stone-50 px-3 py-2 text-xs leading-relaxed text-stone-500'>
        업로드한 도면 이미지는 AI 분석 목적으로만 사용되며 30일 후 자동 삭제됩니다.
      </p>

      <Button
        type='submit'
        disabled={!selectedFile || isLoading}
        className='w-full'
        size='lg'
      >
        {isLoading ? '분석 중...' : '분석 시작'}
      </Button>
    </form>
  )
}

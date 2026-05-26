'use client'

import { useRef, useState } from 'react'
import { FileImage, UploadCloud, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ReferenceImageUploaderProps {
  onFileChange: (file: File | null) => void
}

export function ReferenceImageUploader({ onFileChange }: ReferenceImageUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
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
    onFileChange(file)
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedFile(null)
    setPreview(null)
    onFileChange(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className='space-y-2'>
      <div
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => !preview && fileInputRef.current?.click()}
        className={cn(
          'relative rounded-xl border border-dashed p-3 transition-all',
          preview ? 'cursor-default' : 'cursor-pointer',
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
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
          }}
        />

        {preview ? (
          <div className='space-y-2'>
            <div className='relative overflow-hidden rounded-lg border border-stone-200 bg-stone-100'>
              <img
                src={preview}
                alt='레퍼런스 미리보기'
                className='mx-auto max-h-40 w-full object-contain'
              />
              <button
                type='button'
                onClick={handleClear}
                className='absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-stone-900/70 text-white hover:bg-stone-900'
              >
                <X className='h-3.5 w-3.5' />
              </button>
            </div>
            <div className='flex items-center gap-2 text-xs text-stone-600'>
              <FileImage className='h-3.5 w-3.5 text-amber-700' />
              <span className='truncate font-medium'>{selectedFile?.name}</span>
            </div>
          </div>
        ) : (
          <div className='flex flex-col items-center justify-center py-5 text-center'>
            <UploadCloud className='mb-2 h-7 w-7 text-stone-400' />
            <p className='text-xs font-semibold text-stone-700'>레퍼런스 사진 선택</p>
            <p className='mt-1 text-xs text-stone-400'>JPG / PNG, 최대 5MB</p>
          </div>
        )}
      </div>

      <p className='rounded-lg bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800'>
        본인이 직접 촬영했거나 사용 권한이 있는 이미지만 업로드해 주세요.
        타인 저작물 업로드 시 저작권 침해 책임은 업로더에게 있으며,
        이미지는 AI 톤 분석 목적으로만 사용되고 30일 후 자동 삭제됩니다.
      </p>
    </div>
  )
}

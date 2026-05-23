import Image from 'next/image'
import { ExternalLink, Sparkles } from 'lucide-react'
import type { ProductOut } from '@/types/api'
import { resolvePurchaseUrl } from '@/lib/naver-url'

interface ProductGridProps {
  products: ProductOut[]
}

function formatPrice(price: number): string {
  return `${price.toLocaleString('ko-KR')}원`
}

function ProductCard({ product }: { product: ProductOut }) {
  return (
    <a
      href={resolvePurchaseUrl(product)}
      target='_blank'
      rel='noopener'
      referrerPolicy='strict-origin-when-cross-origin'
      className='group flex gap-3 rounded-xl border border-stone-200 bg-white p-3 shadow-sm transition-all hover:border-amber-300 hover:shadow-md'
    >
      {product.image_url && (
        <div className='relative h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-stone-100'>
          <Image
            src={product.image_url}
            alt={product.name}
            fill
            className='object-cover transition-transform duration-500 group-hover:scale-105'
            sizes='80px'
          />
        </div>
      )}
      <div className='min-w-0 flex-1 space-y-1.5'>
        <div className='flex items-start justify-between gap-2'>
          <p className='line-clamp-2 text-sm font-semibold leading-5 text-stone-900'>
            {product.name}
          </p>
          <ExternalLink className='mt-0.5 h-3.5 w-3.5 shrink-0 text-stone-300 group-hover:text-amber-600 transition-colors' />
        </div>
        <div className='flex flex-wrap items-center gap-1'>
          {product.category && (
            <span className='inline-flex h-5 items-center rounded-full border border-stone-200 bg-stone-50 px-2 text-[10px] text-stone-500'>
              {product.category}
            </span>
          )}
          {product.match_score != null && product.match_score >= 0.6 && (
            <span className='inline-flex h-5 items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 text-[10px] text-amber-700'>
              <Sparkles className='h-2.5 w-2.5' />
              스타일 일치
            </span>
          )}
        </div>
        <p className='text-sm font-bold text-stone-900'>
          {formatPrice(product.price_min)}
          {product.price_max > product.price_min && (
            <span className='font-normal text-stone-400'>
              {' '}~ {formatPrice(product.price_max)}
            </span>
          )}
        </p>
      </div>
    </a>
  )
}

export function ProductGrid({ products }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <p className='rounded-xl border border-stone-100 bg-stone-50 py-6 text-center text-sm text-stone-400'>
        추천 상품을 찾지 못했습니다.
      </p>
    )
  }

  const hasSlots = products.some((p) => p.slot)

  if (!hasSlots) {
    return (
      <div className='space-y-3'>
        <p className='text-xs leading-5 text-stone-400'>
          가격·재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.
        </p>
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-2'>
          {products.map((product, i) => (
            <ProductCard key={i} product={product} />
          ))}
        </div>
      </div>
    )
  }

  const slotOrder: string[] = []
  const grouped: Record<string, ProductOut[]> = {}
  for (const product of products) {
    const slot = product.slot ?? '기타'
    if (!grouped[slot]) {
      grouped[slot] = []
      slotOrder.push(slot)
    }
    grouped[slot].push(product)
  }

  return (
    <div className='space-y-5'>
      <p className='text-xs leading-5 text-stone-400'>
        가격·재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.
      </p>
      {slotOrder.map((slot) => (
        <div key={slot} className='space-y-2'>
          <h4 className='text-[11px] font-semibold uppercase tracking-widest text-stone-400'>
            {slot}
          </h4>
          <div className='grid grid-cols-1 gap-3 sm:grid-cols-2'>
            {grouped[slot].map((product, i) => (
              <ProductCard key={i} product={product} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

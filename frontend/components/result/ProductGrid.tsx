import Image from 'next/image'
import { ExternalLink, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
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
      className='group flex gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-all hover:border-teal-300 hover:shadow-md'
    >
      {product.image_url && (
        <div className='relative h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-100'>
          <Image
            src={product.image_url}
            alt={product.name}
            fill
            className='object-cover'
            sizes='80px'
          />
        </div>
      )}
      <div className='min-w-0 flex-1 space-y-2'>
        <div className='flex items-start justify-between gap-2'>
          <p className='line-clamp-2 text-sm font-semibold leading-5 text-slate-900'>
            {product.name}
          </p>
          <ExternalLink className='mt-0.5 h-4 w-4 shrink-0 text-slate-300 group-hover:text-teal-600' />
        </div>
        <div className='flex flex-wrap items-center gap-1.5'>
          {product.category && <Badge>{product.category}</Badge>}
          {product.match_score != null && product.match_score >= 0.6 && (
            <Badge className='flex items-center gap-1 bg-teal-50 text-teal-700 hover:bg-teal-100'>
              <Sparkles className='h-3 w-3' />
              이미지 스타일 일치
            </Badge>
          )}
        </div>
        <p className='text-sm font-bold text-slate-950'>
          {formatPrice(product.price_min)}
          {product.price_max > product.price_min && (
            <span className='font-normal text-slate-400'>
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
      <p className='rounded-lg border border-slate-100 bg-slate-50 py-5 text-center text-sm text-slate-400'>
        추천 상품을 찾지 못했습니다.
      </p>
    )
  }

  // slot 필드가 있으면 슬롯별 그룹핑, 없으면 기존 평면 표시
  const hasSlots = products.some((p) => p.slot)

  if (!hasSlots) {
    return (
      <div className='space-y-3'>
        <p className='text-xs leading-5 text-slate-400'>
          가격과 재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.
        </p>
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-2'>
          {products.map((product, i) => (
            <ProductCard key={i} product={product} />
          ))}
        </div>
      </div>
    )
  }

  // 슬롯별 그룹핑 (삽입 순서 유지)
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
    <div className='space-y-4'>
      <p className='text-xs leading-5 text-slate-400'>
        가격과 재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.
      </p>
      {slotOrder.map((slot) => (
        <div key={slot} className='space-y-2'>
          <h4 className='text-xs font-semibold uppercase tracking-wide text-slate-500'>
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

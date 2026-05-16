import { describe, it, expect } from 'vitest'
import { resolvePurchaseUrl } from '../naver-url'
import type { ProductOut } from '@/types/api'

function makeProduct(overrides: Partial<ProductOut>): ProductOut {
  return {
    name: '테스트 상품',
    price_min: 10000,
    price_max: 10000,
    ...overrides,
  }
}

describe('resolvePurchaseUrl', () => {
  it('purchase_url 이 null 이면 # 을 반환한다', () => {
    const product = makeProduct({ purchase_url: null })
    expect(resolvePurchaseUrl(product)).toBe('#')
  })

  it('cr.shopping.naver.com URL + naver_product_id → 카탈로그 직링크', () => {
    const product = makeProduct({
      purchase_url: 'https://cr.shopping.naver.com/adcr.nhn?x=abc',
      naver_product_id: '12345',
    })
    expect(resolvePurchaseUrl(product)).toBe(
      'https://search.shopping.naver.com/catalog/12345'
    )
  })

  it('gate.nhn URL + naver_product_id → 카탈로그 직링크', () => {
    const product = makeProduct({
      purchase_url: 'https://search.shopping.naver.com/gate.nhn?id=99',
      naver_product_id: '99',
    })
    expect(resolvePurchaseUrl(product)).toBe(
      'https://search.shopping.naver.com/catalog/99'
    )
  })

  it('adcr.naver.com URL + naver_product_id → 카탈로그 직링크', () => {
    const product = makeProduct({
      purchase_url: 'https://adcr.naver.com/adcr/home?x=y',
      naver_product_id: '777',
    })
    expect(resolvePurchaseUrl(product)).toBe(
      'https://search.shopping.naver.com/catalog/777'
    )
  })

  it('어필리에이트 URL 이지만 naver_product_id 없으면 원본 반환', () => {
    const url = 'https://cr.shopping.naver.com/adcr.nhn?x=abc'
    const product = makeProduct({ purchase_url: url, naver_product_id: null })
    expect(resolvePurchaseUrl(product)).toBe(url)
  })

  it('smartstore.naver.com 직링크(어필리에이트 아님) → 원본 유지', () => {
    const url = 'https://smartstore.naver.com/shop/products/123'
    const product = makeProduct({ purchase_url: url, naver_product_id: '123' })
    expect(resolvePurchaseUrl(product)).toBe(url)
  })

  it('일반 외부몰 URL → 원본 유지', () => {
    const url = 'https://www.coupang.com/vp/products/abc'
    const product = makeProduct({ purchase_url: url, naver_product_id: '456' })
    expect(resolvePurchaseUrl(product)).toBe(url)
  })
})

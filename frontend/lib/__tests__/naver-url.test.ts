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

const SEARCH_URL = `https://search.shopping.naver.com/search/all?query=${encodeURIComponent('테스트 상품')}`

describe('resolvePurchaseUrl', () => {
  it('purchase_url 이 없으면 상품명 검색 URL로 폴백한다', () => {
    expect(resolvePurchaseUrl(makeProduct({ purchase_url: null }))).toBe(SEARCH_URL)
    expect(resolvePurchaseUrl(makeProduct({ purchase_url: undefined }))).toBe(SEARCH_URL)
  })

  // 네이버 카탈로그/어필리에이트 URL은 외부 접근 시 CAPTCHA 발생 → 검색 URL로 우회
  it.each([
    'https://cr.shopping.naver.com/adcr.nhn?x=abc',
    'https://search.shopping.naver.com/gate.nhn?id=99',
    'https://adcr.naver.com/adcr/home?x=y',
  ])('네이버 어필리에이트 URL(%s)은 검색 URL로 대체한다', (url) => {
    expect(resolvePurchaseUrl(makeProduct({ purchase_url: url }))).toBe(SEARCH_URL)
  })

  it('smartstore.naver.com 직링크는 어필리에이트 패턴이 아니므로 원본 유지', () => {
    const url = 'https://smartstore.naver.com/shop/products/123'
    expect(resolvePurchaseUrl(makeProduct({ purchase_url: url }))).toBe(url)
  })

  it('이케아 등 외부 직링크는 원본을 그대로 반환한다', () => {
    const url = 'https://www.ikea.com/kr/ko/p/some-product-123/'
    expect(resolvePurchaseUrl(makeProduct({ purchase_url: url }))).toBe(url)
  })
})

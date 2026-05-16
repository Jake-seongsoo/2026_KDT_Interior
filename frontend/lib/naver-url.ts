import type { ProductOut } from '@/types/api'

// 네이버 카탈로그/어필리에이트 URL은 외부 도메인에서 접근 시 CAPTCHA가 발생함
// 검색 결과 페이지(search/all?query=...)는 외부 공유용으로 CAPTCHA 없이 작동
function naverSearchUrl(name: string): string {
  return `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(name)}`
}

const NAVER_URL_PATTERNS = [
  'shopping.naver.com',
  'cr.shopping.naver.com',
  'gate.nhn',
  'adcr.naver.com',
]

export function resolvePurchaseUrl(product: ProductOut): string {
  const url = product.purchase_url
  if (!url) return naverSearchUrl(product.name)

  const isNaverUrl = NAVER_URL_PATTERNS.some((p) => url.includes(p))
  if (isNaverUrl) return naverSearchUrl(product.name)

  return url
}

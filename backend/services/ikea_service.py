"""이케아 한국 비공식 검색 API 서비스.

sik.search.blue.cdtapps.com 은 이케아 내부 검색 인프라로,
공식 지원이 아니므로 응답 구조가 변경될 수 있다.
응답 파싱 실패 시 빈 리스트를 반환해 상위 레이어에 영향을 주지 않는다.
"""
import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = 'https://sik.search.blue.cdtapps.com/kr/ko/search-result-page'
_PRODUCT_PAGE_BASE = 'https://www.ikea.com/kr/ko/p/'

# 동시 이케아 요청 수 제한
_IKEA_SEMAPHORE = asyncio.Semaphore(3)


class IkeaService:
  async def search_products(self, keyword: str, display: int = 5) -> list[dict]:
    """이케아 한국 카탈로그에서 키워드로 상품을 검색한다."""
    async with _IKEA_SEMAPHORE:
      try:
        async with httpx.AsyncClient(timeout=10.0) as client:
          resp = await client.get(
            _BASE_URL,
            params={'q': keyword, 'types': 'PRODUCT', 'size': display},
            headers={'Accept': 'application/json'},
          )
          resp.raise_for_status()
          return self._parse(resp.json(), display)
      except httpx.HTTPError as e:
        logger.warning('이케아 API 오류 (keyword=%s): %s', keyword, e)
        return []
      except Exception as e:
        logger.warning('이케아 응답 파싱 실패 (keyword=%s): %s', keyword, e)
        return []

  @staticmethod
  def _parse(data: dict, limit: int) -> list[dict]:
    """이케아 API 응답에서 상품 목록을 추출해 정규화된 dict 리스트로 반환한다."""
    try:
      items = (
        data
        .get('searchResultPage', {})
        .get('products', {})
        .get('main', {})
        .get('items', [])
      )
    except AttributeError:
      return []

    result = []
    for item in items[:limit]:
      product = item.get('product') if isinstance(item, dict) else None
      if not product:
        continue
      normalized = IkeaService._normalize(product)
      if normalized:
        result.append(normalized)
    return result

  @staticmethod
  def _normalize(product: dict) -> dict | None:
    """이케아 상품 dict를 ProductOut 호환 형태로 변환한다."""
    name = product.get('name', '')
    type_name = product.get('typeName', '')
    full_name = f'{name} {type_name}'.strip() if type_name else name
    if not full_name:
      return None

    price_raw = product.get('price', {})
    price_str = price_raw.get('numeral', '0') if isinstance(price_raw, dict) else '0'
    try:
      price = int(str(price_str).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
      price = 0

    pip_url = product.get('pipUrl') or ''
    if pip_url and not pip_url.startswith('http'):
      pip_url = f'https://www.ikea.com{pip_url}'

    return {
      'naver_product_id': str(product.get('id') or ''),
      'name': full_name,
      'category': type_name or None,
      'price_min': price,
      'price_max': price,
      'image_url': product.get('contextualImageUrl') or product.get('mainImageUrl'),
      'purchase_url': pip_url or None,
      'source': 'ikea',
    }

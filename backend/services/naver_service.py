import asyncio
import logging
import re
from urllib.parse import quote

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)

_BASE_URL = 'https://openapi.naver.com/v1/search/shop.json'
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_NAVER_URL_PATTERNS = ('shopping.naver.com', 'gate.nhn', 'adcr.naver.com')

# 동시 네이버 요청 수 제한 — 429 방지
_NAVER_SEMAPHORE = asyncio.Semaphore(3)


def _strip_html(text: str) -> str:
  return _HTML_TAG_RE.sub('', text).strip()


class NaverService:
  def __init__(self) -> None:
    s = get_settings()
    self._headers = {
      'X-Naver-Client-Id': s.NAVER_CLIENT_ID,
      'X-Naver-Client-Secret': s.NAVER_CLIENT_SECRET,
    }

  async def search_products(self, keyword: str, display: int = 5) -> list[dict]:
    """네이버쇼핑에서 키워드로 상품을 검색한다. 동시 요청은 최대 3개로 제한한다."""
    async with _NAVER_SEMAPHORE:
      try:
        async with httpx.AsyncClient(timeout=10.0) as client:
          resp = await client.get(
            _BASE_URL,
            headers=self._headers,
            params={'query': keyword, 'display': display, 'sort': 'sim'},
          )
          resp.raise_for_status()
          items = resp.json().get('items', [])
          return [self._normalize(item) for item in items]
      except httpx.HTTPError as e:
        logger.warning('Naver 쇼핑 API 오류 (keyword=%s): %s', keyword, e)
        return []

  @staticmethod
  def _build_purchase_url(item: dict) -> str | None:
    """네이버 쇼핑 검색 결과 URL을 반환한다.

    카탈로그/어필리에이트 URL(catalog, cr.shopping.naver.com 등)은
    외부 도메인에서 접근 시 CAPTCHA가 발생하므로 상품명 검색 URL로 대체한다.
    직접 쇼핑몰 URL(비네이버)인 경우에는 그대로 반환한다.
    """
    link = item.get('link') or ''
    title = _strip_html(item.get('title', ''))

    if not link or any(p in link for p in _NAVER_URL_PATTERNS):
      return f'https://search.shopping.naver.com/search/all?query={quote(title)}'
    return link

  @staticmethod
  def _normalize(item: dict) -> dict:
    return {
      'naver_product_id': str(item.get('productId') or ''),
      'name': _strip_html(item.get('title', '')),
      'category': item.get('category4') or item.get('category3') or item.get('category2'),
      'price_min': int(item.get('lprice') or 0),
      'price_max': int(item.get('hprice') or item.get('lprice') or 0),
      'image_url': item.get('image'),
      'purchase_url': NaverService._build_purchase_url(item),
    }

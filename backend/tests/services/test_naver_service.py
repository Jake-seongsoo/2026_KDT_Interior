"""NaverService 단위 테스트."""
from urllib.parse import quote

import pytest

from services.naver_service import NaverService


_NAVER_LINK = 'https://cr.shopping.naver.com/adcr.nhn?x=abc'
_GATE_LINK = 'https://search.shopping.naver.com/gate.nhn?id=12345'
_MERCHANT_LINK = 'https://www.coupang.com/vp/products/123456'
_TITLE = '원목 소파'
_ENCODED_TITLE = quote(_TITLE)
_EXPECTED_SEARCH = f'https://search.shopping.naver.com/search/all?query={_ENCODED_TITLE}'


class TestBuildPurchaseUrl:
  def test_naver_affiliate_link_returns_search_url(self):
    item = {'productId': '12345', 'productType': 2, 'title': _TITLE, 'link': _NAVER_LINK}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_gate_nhn_link_returns_search_url(self):
    item = {'productId': '99', 'productType': 3, 'title': _TITLE, 'link': _GATE_LINK}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_adcr_naver_link_returns_search_url(self):
    adcr_link = 'https://adcr.naver.com/adcr?x=abc'
    item = {'productId': '777', 'productType': 8, 'title': _TITLE, 'link': adcr_link}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_direct_merchant_link_returned_as_is(self):
    item = {'productId': '12345', 'productType': 1, 'title': _TITLE, 'link': _MERCHANT_LINK}
    result = NaverService._build_purchase_url(item)
    assert result == _MERCHANT_LINK

  def test_missing_link_returns_search_url(self):
    item = {'productId': '123', 'productType': 1, 'title': _TITLE, 'link': None}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_empty_link_returns_search_url(self):
    item = {'productId': '123', 'productType': 3, 'title': _TITLE, 'link': ''}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_title_with_html_tags_is_stripped(self):
    item = {'productId': '555', 'productType': 2, 'title': '<b>원목 소파</b>', 'link': _NAVER_LINK}
    result = NaverService._build_purchase_url(item)
    assert result == _EXPECTED_SEARCH

  def test_normalize_uses_search_url_for_naver_link(self):
    item = {
      'productId': '9999',
      'productType': 2,
      'title': f'<b>{_TITLE}</b>',
      'category4': '소파',
      'lprice': '100000',
      'hprice': '200000',
      'image': 'https://img.example.com/a.jpg',
      'link': _NAVER_LINK,
    }
    result = NaverService._normalize(item)
    assert result['purchase_url'] == _EXPECTED_SEARCH
    assert result['naver_product_id'] == '9999'
    assert result['name'] == _TITLE

  def test_normalize_uses_merchant_url_for_direct_link(self):
    item = {
      'productId': '8888',
      'productType': 1,
      'title': _TITLE,
      'category4': '소파',
      'lprice': '50000',
      'hprice': '50000',
      'image': 'https://img.example.com/b.jpg',
      'link': _MERCHANT_LINK,
    }
    result = NaverService._normalize(item)
    assert result['purchase_url'] == _MERCHANT_LINK


def _make_item(product_type: int, title: str = '상품') -> dict:
  return {'productId': '1', 'productType': product_type, 'title': title, 'link': ''}


class TestSortByCatalog:
  def test_catalog_items_come_first(self):
    items = [
      _make_item(2, '단독상품A'),
      _make_item(1, '카탈로그상품B'),
      _make_item(2, '단독상품C'),
      _make_item(1, '카탈로그상품D'),
    ]
    result = NaverService._sort_by_catalog(items)
    assert result[0]['title'] == '카탈로그상품B'
    assert result[1]['title'] == '카탈로그상품D'

  def test_all_catalog_items_unchanged_order(self):
    items = [_make_item(1, f'상품{i}') for i in range(3)]
    result = NaverService._sort_by_catalog(items)
    assert [r['title'] for r in result] == ['상품0', '상품1', '상품2']

  def test_all_non_catalog_items_unchanged_order(self):
    items = [_make_item(2, f'상품{i}') for i in range(3)]
    result = NaverService._sort_by_catalog(items)
    assert [r['title'] for r in result] == ['상품0', '상품1', '상품2']

  def test_empty_list_returns_empty(self):
    assert NaverService._sort_by_catalog([]) == []

  def test_missing_product_type_treated_as_non_catalog(self):
    items = [
      {'productId': '1', 'title': 'productType없음', 'link': ''},
      _make_item(1, '카탈로그상품'),
    ]
    result = NaverService._sort_by_catalog(items)
    assert result[0]['title'] == '카탈로그상품'

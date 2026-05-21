"""IkeaService 단위 테스트."""
import pytest

from services.ikea_service import IkeaService


def _make_api_response(items: list[dict]) -> dict:
  return {'searchResultPage': {'products': {'main': {'items': items}}}}


def _make_product(
  id_: str = 'P001',
  name: str = 'KALLAX',
  type_name: str = '선반 유닛',
  price: str = '119900',
  image: str = 'https://www.ikea.com/img/a.jpg',
  pip_url: str = 'https://www.ikea.com/kr/ko/p/kallax-/',
) -> dict:
  return {
    'product': {
      'id': id_,
      'name': name,
      'typeName': type_name,
      'price': {'numeral': price},
      'contextualImageUrl': image,
      'pipUrl': pip_url,
    }
  }


class TestIkeaServiceParse:
  def test_returns_normalized_products(self):
    data = _make_api_response([_make_product()])
    result = IkeaService._parse(data, limit=5)

    assert len(result) == 1
    assert result[0]['name'] == 'KALLAX 선반 유닛'
    assert result[0]['price_min'] == 119900
    assert result[0]['source'] == 'ikea'

  def test_respects_limit(self):
    items = [_make_product(id_=str(i)) for i in range(5)]
    result = IkeaService._parse(_make_api_response(items), limit=3)
    assert len(result) == 3

  def test_empty_items_returns_empty(self):
    assert IkeaService._parse(_make_api_response([]), limit=5) == []

  def test_malformed_response_returns_empty(self):
    assert IkeaService._parse({}, limit=5) == []
    assert IkeaService._parse({'searchResultPage': None}, limit=5) == []

  def test_item_without_product_key_skipped(self):
    data = _make_api_response([{'product': None}, _make_product(id_='valid')])
    result = IkeaService._parse(data, limit=5)
    assert len(result) == 1
    assert result[0]['naver_product_id'] == 'valid'


class TestIkeaServiceNormalize:
  def test_full_name_combines_name_and_type(self):
    p = {'id': '1', 'name': 'EKTORP', 'typeName': '2인용 소파', 'price': {'numeral': '599000'}}
    result = IkeaService._normalize(p)
    assert result['name'] == 'EKTORP 2인용 소파'

  def test_type_name_empty_uses_name_only(self):
    p = {'id': '1', 'name': 'KALLAX', 'typeName': '', 'price': {'numeral': '0'}}
    result = IkeaService._normalize(p)
    assert result['name'] == 'KALLAX'

  def test_price_with_comma_parsed_correctly(self):
    p = {'id': '1', 'name': 'X', 'typeName': '', 'price': {'numeral': '1,199,000'}}
    result = IkeaService._normalize(p)
    assert result['price_min'] == 1199000

  def test_invalid_price_defaults_to_zero(self):
    p = {'id': '1', 'name': 'X', 'typeName': '', 'price': {'numeral': 'N/A'}}
    result = IkeaService._normalize(p)
    assert result['price_min'] == 0

  def test_relative_pip_url_becomes_absolute(self):
    p = {'id': '1', 'name': 'X', 'typeName': '', 'price': {}, 'pipUrl': '/kr/ko/p/x/'}
    result = IkeaService._normalize(p)
    assert result['purchase_url'].startswith('https://www.ikea.com')

  def test_absolute_pip_url_unchanged(self):
    url = 'https://www.ikea.com/kr/ko/p/x/'
    p = {'id': '1', 'name': 'X', 'typeName': '', 'price': {}, 'pipUrl': url}
    result = IkeaService._normalize(p)
    assert result['purchase_url'] == url

  def test_no_name_returns_none(self):
    p = {'id': '1', 'name': '', 'typeName': '', 'price': {}}
    result = IkeaService._normalize(p)
    assert result is None

  def test_source_is_ikea(self):
    p = {'id': '1', 'name': 'X', 'typeName': 'Y', 'price': {'numeral': '10000'}}
    result = IkeaService._normalize(p)
    assert result['source'] == 'ikea'

  def test_price_min_equals_price_max(self):
    p = {'id': '1', 'name': 'X', 'typeName': '', 'price': {'numeral': '50000'}}
    result = IkeaService._normalize(p)
    assert result['price_min'] == result['price_max'] == 50000

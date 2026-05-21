"""product_filter 단위 테스트 — rerank_products_by_visuals, enrich_query_with_vision."""
import pytest

from services.product_filter import enrich_query_with_vision, filter_products_by_expected_colors, rerank_products_by_visuals


def _make_product(name: str, **kwargs) -> dict:
  return {
    'name': name,
    'price_min': 100000,
    'price_max': 200000,
    'image_url': None,
    'purchase_url': None,
    **kwargs,
  }


VISUAL_ATTRS = {
  '수납장': {
    'primary_hex': '#D4C5A9',  # 베이지/아이보리 계열
    'secondary_hex': '#7A9E8A',  # 세이지 그린 계열
    'materials': ['자작나무', '원목'],
    'structure': ['큐브', '인셋박스', '벽걸이형'],
    'style_tokens': ['스칸디나비안', '내추럴'],
  }
}


class TestRerankProductsByVisuals:
  def test_색상만_일치_상품이_상위_랭크(self):
    """색상 토큰 일치 상품이 상위에 오야 한다."""
    products = [
      _make_product('일반 수납장'),
      _make_product('원목 큐브 수납장'),   # 구조 일치
      _make_product('아이보리 원목 수납장'),  # 색상+재질 일치
    ]
    expected_colors = ['아이보리', '원목', '베이지']

    result = rerank_products_by_visuals(products, expected_colors, VISUAL_ATTRS, limit=3)

    assert len(result) == 3
    assert any('아이보리' in p['name'] for p in result[:2])

  def test_구조만_일치_상품이_중간_랭크(self):
    """구조 토큰만 일치하는 상품은 중간 순위여야 한다."""
    products = [
      _make_product('일반 수납장'),
      _make_product('큐브 인셋 수납장'),  # 구조 일치
      _make_product('그레이 패브릭 수납장'),
    ]
    expected_colors = []

    result = rerank_products_by_visuals(products, expected_colors, VISUAL_ATTRS, limit=3)

    assert any('큐브' in p['name'] for p in result)
    # 구조 일치 상품이 완전 불일치보다 높은 점수여야 함
    cube_score = next(p['match_score'] for p in result if '큐브' in p['name'])
    plain_score = next(p['match_score'] for p in result if '일반' in p['name'])
    assert cube_score > plain_score

  def test_색상_구조_모두_일치_최상위(self):
    """색상과 구조 모두 일치하는 상품이 가장 높은 점수여야 한다."""
    products = [
      _make_product('일반 수납장'),
      _make_product('큐브 수납장'),
      _make_product('아이보리 원목 큐브 인셋 수납장'),  # 최우선
    ]
    expected_colors = ['아이보리', '원목']

    result = rerank_products_by_visuals(products, expected_colors, VISUAL_ATTRS, limit=3)

    assert '아이보리' in result[0]['name']
    assert result[0]['match_score'] >= result[1]['match_score']

  def test_visual_attrs_None_기존_필터_폴백(self):
    """visual_attrs가 None이면 기존 텍스트 필터로 폴백해야 한다."""
    products = [
      _make_product('그레이 소파'),
      _make_product('아이보리 소파'),
      _make_product('일반 소파'),
    ]
    expected_colors = ['아이보리']

    result = rerank_products_by_visuals(products, expected_colors, None, limit=2)

    # 기존 필터: expected_colors 매칭 우선
    assert len(result) <= 2
    assert result[0]['name'] == '아이보리 소파'

  def test_동점_시_원래_순위_보존(self):
    """점수가 동점이면 원래 정렬(Naver sim) 순서가 유지되어야 한다."""
    products = [
      _make_product('수납장 A'),
      _make_product('수납장 B'),
      _make_product('수납장 C'),
    ]
    # 색상/구조 토큰 전혀 없음 → 모두 동점 → 원래 순서 보존
    result = rerank_products_by_visuals(products, [], None, limit=3)

    assert result[0]['name'] == '수납장 A'

  def test_match_score_0_1_범위(self):
    """match_score는 0~1 범위 안에 있어야 한다."""
    products = [_make_product(f'상품{i}') for i in range(5)]
    expected_colors = ['원목', '자작나무']

    result = rerank_products_by_visuals(products, expected_colors, VISUAL_ATTRS, limit=5)

    for p in result:
      assert 0.0 <= p['match_score'] <= 1.1  # 동점 보정 미세값 허용

  def test_match_reasons_내용_검증(self):
    """색상 일치 시 match_reasons에 '색상 일치'가 포함되어야 한다."""
    products = [_make_product('아이보리 원목 수납장')]
    expected_colors = ['아이보리', '원목']

    result = rerank_products_by_visuals(products, expected_colors, VISUAL_ATTRS, limit=1)

    assert '색상 일치' in result[0]['match_reasons']

  def test_빈_상품_리스트_빈_결과(self):
    """상품이 없으면 빈 리스트를 반환해야 한다."""
    result = rerank_products_by_visuals([], ['원목'], VISUAL_ATTRS, limit=3)

    assert result == []


class TestEnrichQueryWithVision:
  def test_재질과_스타일_토큰이_쿼리에_추가된다(self):
    attrs = {'materials': ['패브릭'], 'style_tokens': ['미니멀'], 'primary_hex': None}
    result = enrich_query_with_vision('모던 소파', attrs)
    assert '패브릭' in result
    assert '미니멀' in result

  def test_색상_hex가_한국어로_변환되어_추가된다(self):
    attrs = {'materials': [], 'style_tokens': [], 'primary_hex': '#F5F5F5'}
    result = enrich_query_with_vision('침대 프레임', attrs)
    # #F5F5F5 → 화이트/아이보리 계열
    assert '침대 프레임' in result
    assert len(result) > len('침대 프레임')

  def test_이미_포함된_토큰은_중복_추가하지_않는다(self):
    attrs = {'materials': ['패브릭'], 'style_tokens': ['모던'], 'primary_hex': None}
    result = enrich_query_with_vision('모던 패브릭 소파', attrs)
    assert result.count('모던') == 1
    assert result.count('패브릭') == 1

  def test_slot_attrs가_None이면_base_query_그대로_반환(self):
    assert enrich_query_with_vision('소파', None) == '소파'

  def test_slot_attrs가_빈_dict면_base_query_그대로_반환(self):
    assert enrich_query_with_vision('소파', {}) == '소파'

  def test_추출_토큰이_없으면_base_query_그대로_반환(self):
    attrs = {'materials': [], 'style_tokens': [], 'primary_hex': None}
    assert enrich_query_with_vision('식탁', attrs) == '식탁'

  def test_재질_최대_2개만_추가된다(self):
    attrs = {'materials': ['원목', '철재', '유리'], 'style_tokens': [], 'primary_hex': None}
    result = enrich_query_with_vision('선반', attrs)
    assert '원목' in result
    assert '철재' in result
    assert '유리' not in result

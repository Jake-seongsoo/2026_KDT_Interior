"""가구별 검색 결과 후처리 — 기대 색상/재질 토큰 기반 필터링 및 Vision 속성 재랭킹."""

import re


def filter_products_by_expected_colors(
  products: list[dict],
  expected_colors: list[str],
  limit: int = 3,
) -> list[dict]:
  """상품 목록에서 기대 색상/재질 토큰이 상품명에 포함된 항목을 우선으로 limit개 반환한다.

  매칭 항목이 limit에 미달하면 나머지를 원래 정렬(sim) 순서로 채운다.
  """
  if not products:
    return []

  # 토큰 소문자 정규화
  tokens = [t.lower() for t in expected_colors]

  matched: list[dict] = []
  unmatched: list[dict] = []

  for product in products:
    name_lower = product.get('name', '').lower()
    if any(token in name_lower for token in tokens):
      matched.append(product)
    else:
      unmatched.append(product)

  combined = matched + unmatched
  return combined[:limit]


def _hex_to_korean_color(hex_color: str | None) -> list[str]:
  """hex 색상값을 가까운 한국어 색상명 토큰 리스트로 변환한다."""
  if not hex_color:
    return []
  hex_color = hex_color.lstrip('#').lower()
  try:
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
  except (ValueError, IndexError):
    return []

  tokens: list[str] = []
  # 기본 색상 분류 (근사값)
  if r > 200 and g > 200 and b > 200:
    tokens.extend(['화이트', '아이보리', '크림'])
  elif r < 60 and g < 60 and b < 60:
    tokens.extend(['블랙', '차콜'])
  elif r > 150 and g > 150 and b > 150:
    tokens.extend(['그레이', '실버', '라이트그레이'])
  elif r > 180 and g < 120 and b < 120:
    tokens.extend(['레드', '버건디', '와인'])
  elif r < 120 and g > 150 and b < 120:
    tokens.extend(['그린', '올리브', '세이지', '포레스트그린'])
  elif r < 120 and g < 120 and b > 150:
    tokens.extend(['블루', '네이비', '스카이블루'])
  elif r > 160 and g > 120 and b < 80:
    tokens.extend(['브라운', '원목', '월넛', '오크'])
  elif r > 200 and g > 150 and b < 100:
    tokens.extend(['옐로우', '머스타드', '골드'])
  else:
    tokens.extend(['베이지', '뉴트럴'])
  return tokens


def _token_match_ratio(tokens: list[str], name: str) -> float:
  """토큰 리스트 중 상품명(name)에 포함된 비율을 반환한다."""
  if not tokens:
    return 0.0
  name_lower = name.lower()
  # HTML 태그 제거 (네이버 상품명에 <b> 태그 포함 가능)
  name_lower = re.sub(r'<[^>]+>', '', name_lower)
  matched = sum(1 for t in tokens if t.lower() in name_lower)
  return matched / len(tokens)


def rerank_products_by_visuals(
  products: list[dict],
  expected_colors: list[str],
  visual_attrs: dict | None,
  limit: int = 3,
) -> list[dict]:
  """Vision 추출 시각 속성을 활용해 상품을 재랭킹한다.

  visual_attrs가 None이면 기존 텍스트 필터로 폴백한다.
  각 상품에 match_score(float)와 match_reasons(list[str])를 첨부한다.
  """
  if not products:
    return []

  if visual_attrs is None:
    # Vision 실패 시 기존 텍스트 필터 폴백
    return filter_products_by_expected_colors(products, expected_colors, limit)

  # Vision 속성에서 색상 토큰 보강
  color_tokens = list(expected_colors)
  for slot_attrs in visual_attrs.values():
    if not isinstance(slot_attrs, dict):
      continue
    color_tokens.extend(_hex_to_korean_color(slot_attrs.get('primary_hex')))
    color_tokens.extend(_hex_to_korean_color(slot_attrs.get('secondary_hex')))

  # 구조/재질 토큰 수집
  structure_tokens: list[str] = []
  style_tokens: list[str] = []
  for slot_attrs in visual_attrs.values():
    if not isinstance(slot_attrs, dict):
      continue
    structure_tokens.extend(slot_attrs.get('structure', []) or [])
    structure_tokens.extend(slot_attrs.get('materials', []) or [])
    style_tokens.extend(slot_attrs.get('style_tokens', []) or [])

  scored: list[dict] = []
  for rank, product in enumerate(products):
    name = product.get('name', '')

    color_score = _token_match_ratio(color_tokens, name)
    structure_score = _token_match_ratio(structure_tokens, name)
    style_score = _token_match_ratio(style_tokens, name)

    # 가중 합산: 배색 0.5, 구조 0.3, 스타일 0.2, 원래 순위 보정
    final_score = (
      0.5 * color_score
      + 0.3 * structure_score
      + 0.2 * style_score
      + 0.001 / (rank + 1)
    )

    reasons: list[str] = []
    if color_score > 0:
      reasons.append('색상 일치')
    if structure_score > 0:
      reasons.append('구조/재질 일치')
    if style_score > 0:
      reasons.append('스타일 일치')

    p = dict(product)
    p['match_score'] = round(final_score, 4)
    p['match_reasons'] = reasons
    scored.append(p)

  scored.sort(key=lambda x: x['match_score'], reverse=True)
  return scored[:limit]

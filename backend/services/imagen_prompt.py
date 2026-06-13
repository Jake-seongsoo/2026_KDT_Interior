"""Imagen 렌더링 프롬프트 빌더.

방 정보·선택 톤·정밀화 파라미터·레퍼런스 시그니처를 영문 Imagen 프롬프트로 조립한다.
순수 함수 모듈 — Claude API 호출이 없으며, ClaudeService에서 위임받아 사용한다.
"""
from core.room_matcher import lookup_room_key

# 방 유형별 이미지 프롬프트에서 제외해야 할 가구/소품 키워드
# (욕실에 소파가 나오는 등의 이상 렌더링 방지)
_ROOM_EXCLUDED_KEYWORDS: dict[str, set[str]] = {
  '욕실': {'소파', '침대', '식탁', '러그', '커튼', '책상', '소파베드', '쇼파'},
  '주방': {'소파', '침대', '러그'},
  '발코니': {'소파', '침대', '식탁'},
  '침실': {'식탁', '가스레인지', '조리대', '싱크대', '레인지후드', '주방', '부엌'},
  '안방': {'식탁', '가스레인지', '조리대', '싱크대', '레인지후드', '주방', '부엌'},
  '작은방': {'식탁', '가스레인지', '조리대', '싱크대', '레인지후드', '주방', '부엌'},
}

# 발코니 인접 상태별 Imagen 프롬프트 단서 (비확장/확장형)
# False(비확장): 슬라이딩 도어 묘사 제거 — 도어가 이미지에 강하게 등장해 실내 인테리어 품질 저하
_BALCONY_BOUNDARY_HINTS: dict[str | None, str] = {
  False: (
    'balcony NOT part of room, clean interior wall boundary separating room from balcony'
  ),
  True: (
    'expanded balcony integrated into room with floor-level transition, '
    'continuous flooring throughout'
  ),
}

# 방 유형의 영문 자연어 이름 (Imagen 프롬프트용 — 한국어 토큰이 영어 모델 해석을 흐림)
# 복합 방 이름(부부욕실, 가족욕실)을 직접 등록해 startswith/endswith 매칭보다 우선한다
_ROOM_EN_NAMES: dict[str, str] = {
  '거실': 'living room',
  '주방': 'kitchen',
  '주방/식당': 'kitchen and dining',
  '안방': 'master bedroom',
  '침실': 'bedroom',
  '욕실': 'bathroom',
  '부부욕실': 'master bathroom',
  '가족욕실': 'family bathroom',
  '발코니': 'balcony',
  '발코나': 'balcony',
  '현관': 'entrance',
  '다용도실': 'utility room',
  '작은방': 'small bedroom',
  '알파룸': 'flexible room',
  '드레스룸': 'walk-in closet',
}

# 방 유형별 Imagen negative 단서 (해당 공간에 절대 등장하면 안 되는 사물)
# 복합 이름(부부욕실·가족욕실)은 endswith 매칭으로 처리되므로 기본 키만 등록
_ROOM_NEGATIVE_HINTS: dict[str, str] = {
  '욕실': 'no sofa, no couch, no bed, no dining table, no rug, no curtain',
  '주방': 'no sofa, no bed',
  '발코니': 'no sofa, no bed, no dining table',
  '발코나': 'no sofa, no bed, no dining table',
  # 발코니 인접 거실/침실에 적용: has_adjoining_balcony=true 시 추가 단서로 보강
  '거실': 'no exterior balcony tiles inside room, no outdoor space as living area',
  '안방': 'no exterior balcony tiles inside room, no kitchen cabinets, no stove, no cooking appliances, no sink',
  '침실': 'no exterior balcony tiles inside room, no kitchen cabinets, no stove, no cooking appliances, no sink, no dining table',
  '작은방': 'no exterior balcony tiles inside room, no kitchen cabinets, no stove, no cooking appliances',
}

# 방 유형별 이미지 프롬프트에 강제 포함할 공간 힌트 (영문)
_ROOM_SPACE_HINTS: dict[str, str] = {
  '욕실': 'bathroom with bathtub or shower, vanity mirror, towel rack',
  '주방': 'kitchen with cabinets and countertop',
  '발코니': 'balcony with plants and outdoor furniture',
  '발코나': 'balcony with plants and outdoor furniture',
  '침실': 'bedroom with bed, wardrobe, bedside table, soft ambient lighting',
  '안방': 'master bedroom with double bed, built-in wardrobe, bedside tables, soft ambient lighting',
  '작은방': 'small bedroom with single bed, study desk and wardrobe',
}

# 재질 한국어 → Imagen 영문 변환 (레퍼런스 시그니처 텍스트 힌트 전용)
_MATERIAL_EN_MAP: dict[str, str] = {
  '원목': 'natural wood',
  '패브릭': 'fabric',
  '황동': 'brass',
  '메탈': 'metal',
  '가죽': 'leather',
  '유리': 'glass',
  '대리석': 'marble',
  '콘크리트': 'concrete',
  '벽돌': 'brick',
  '세라믹': 'ceramic',
  '라탄': 'rattan',
  '린넨': 'linen',
  '벨벳': 'velvet',
  '스틸': 'steel',
  '자작나무': 'birch wood',
  '천연석': 'natural stone',
  '타일': 'tile',
}

# 스타일 토큰 한국어 → Imagen 영문 변환 (레퍼런스 시그니처 텍스트 힌트 전용)
_STYLE_TOKEN_EN_MAP: dict[str, str] = {
  '미니멀': 'minimal',
  '내추럴': 'natural',
  '코지': 'cozy',
  '모던': 'modern',
  '빈티지': 'vintage',
  '인더스트리얼': 'industrial',
  '클래식': 'classic',
  '스칸디나비안': 'Scandinavian',
  '보헤미안': 'bohemian',
  '웜': 'warm',
  '쿨': 'cool',
  '아늑한': 'cozy',
  '고급스러운': 'luxury',
  '북유럽': 'Nordic',
  '와비사비': 'wabi-sabi',
  '보태니컬': 'botanical',
  '아르데코': 'art deco',
}

# 한국어 가전명 → Imagen 영문 키워드 매핑
# 이케아 검색 슬롯과 무관 — 렌더링 프롬프트 전용
_APPLIANCE_EN_MAP: dict[str, str] = {
  '냉장고': 'built-in refrigerator',
  '김치냉장고': 'kimchi refrigerator',
  '세탁기': 'washing machine',
  '건조기': 'dryer',
  '스타일러': 'clothing care machine',
  '전자레인지': 'microwave oven',
  '식기세척기': 'built-in dishwasher',
  '인덕션': 'induction cooktop',
  '공기청정기': 'air purifier',
  '로봇청소기': 'robot vacuum docking station',
}


def build_size_hint(area_sqm: float | None) -> str:
  """면적(㎡)을 Imagen이 이해할 수 있는 공간감 형용사 + 수치로 변환한다.

  면적 미제공 시 빈 문자열 반환 (Imagen 기본 공간감에 맡김).
  """
  if not area_sqm:
    return ''
  if area_sqm < 8:
    adj = 'very compact'
  elif area_sqm < 12:
    adj = 'compact'
  elif area_sqm < 20:
    adj = 'standard-sized'
  elif area_sqm < 30:
    adj = 'large'
  else:
    adj = 'spacious'
  return f'{adj} {area_sqm:.1f}sqm '


def build_reference_style_hint(reference_signature: dict | None) -> str:
  """레퍼런스 시그니처에서 추출한 톤·재질·조명을 Imagen 영문 텍스트 힌트로 변환한다.

  Claude Vision이 분석한 분위기를 새 공간에 재해석하는 용도이며,
  이미지 시각적 복사(StyleReferenceImage)와 다르다.
  """
  if not reference_signature:
    return ''
  sig = reference_signature
  primary = sig.get('primary_hex', '')
  secondary = sig.get('secondary_hex', '')
  lighting = sig.get('lighting', '')

  en_materials = [_MATERIAL_EN_MAP.get(m, m) for m in (sig.get('materials') or [])]
  en_tokens = [_STYLE_TOKEN_EN_MAP.get(t, t) for t in (sig.get('style_tokens') or [])]

  parts = []
  if en_tokens:
    parts.append(f"{' '.join(en_tokens)} aesthetic")
  if primary:
    color_desc = f'color palette inspired by {primary}'
    if secondary:
      color_desc += f' and {secondary}'
    parts.append(color_desc)
  if en_materials:
    parts.append(f"{', '.join(en_materials)} materials and textures")
  if lighting:
    parts.append(f'{lighting} lighting')

  if not parts:
    return ''
  return ', inspired by reference style: ' + ', '.join(parts)


def build_appliance_hint(room_type: str, refinement: dict | None) -> str:
  """refinement.appliances 중 해당 방에 배치된 가전을 Imagen 영문 키워드로 변환한다.

  appliances 리스트가 없거나 해당 방에 매핑된 가전이 없으면 빈 문자열 반환.
  """
  if not refinement:
    return ''
  appliances: list[dict] = refinement.get('appliances') or []
  matched = [
    _APPLIANCE_EN_MAP.get(a['name'], a['name'])
    for a in appliances
    if a.get('room') == room_type and a.get('name') in _APPLIANCE_EN_MAP
  ]
  if not matched:
    return ''
  return ', with ' + ', '.join(matched) + ' integrated naturally into the space'


def build_refinement_hint(refinement: dict | None) -> str:
  """정밀화 파라미터를 Imagen 프롬프트 힌트 문자열로 변환한다."""
  if not refinement:
    return ''
  parts = []
  family = refinement.get('family_type')
  if family == 'family_with_kid':
    parts.append('child-safe layout, rounded edges, soft materials')
  elif family == 'family_with_pet':
    parts.append('pet-friendly materials, durable flooring, easy to clean surfaces')
  elif family == 'couple':
    parts.append('romantic and cozy atmosphere for two')
  keywords = refinement.get('style_keywords') or []
  if keywords:
    parts.append(f"emphasizing {', '.join(keywords)} style")
  # appliances 리스트가 있으면 keep_appliances 추상 문구는 생략 (중복 방지)
  has_appliances = bool(refinement.get('appliances'))
  if refinement.get('keep_appliances') and not has_appliances:
    parts.append('retain existing appliances, integrated look')
  budget = refinement.get('budget_10k_won')
  if budget and budget <= 2000:
    parts.append('budget-friendly furniture, cost-effective choices')
  elif budget and budget >= 8000:
    parts.append('premium materials, high-end furniture')
  user_text = refinement.get('user_text')
  if user_text and user_text.strip():
    parts.append(user_text.strip())
  return ', ' + ', '.join(parts) if parts else ''


def build_imagen_prompt(
  room: dict,
  tone: dict,
  refinement: dict | None = None,
  reference_signature: dict | None = None,
) -> str:
  """방 정보와 선택 톤을 기반으로 Imagen 프롬프트를 생성한다.

  reference_signature가 주어지면 Claude Vision이 추출한 톤·재질·조명 정보를
  영문 텍스트 힌트로 변환해 프롬프트에 추가한다 (이미지 복사가 아닌 분위기 재해석).
  """
  room_type = room.get('room_type', '거실')

  # 한국어 방 이름을 영어로 변환 (Imagen은 영어 모델 — 한국어 토큰이 공간 인식을 흐림)
  # 정확 매칭 우선, 없으면 endswith/startswith 순 매칭
  room_en = _ROOM_EN_NAMES.get(room_type)
  if room_en is None:
    matched_key = lookup_room_key(room_type, _ROOM_EN_NAMES)
    if matched_key:
      base_name = _ROOM_EN_NAMES[matched_key]
      if room_type.startswith(matched_key):
        suffix = room_type[len(matched_key):]
        room_en = f'{base_name} {suffix}'.strip() if suffix else base_name
      else:
        room_en = base_name
  if room_en is None:
    room_en = room_type

  # 방 유형과 맞지 않는 가구 키워드 제거 (욕실에 소파 등 방지)
  excluded = set()
  excl_key = lookup_room_key(room_type, _ROOM_EXCLUDED_KEYWORDS)
  if excl_key:
    excluded = _ROOM_EXCLUDED_KEYWORDS[excl_key]

  filtered_keywords = [
    kw for kw in tone.get('keywords', [])
    if kw not in excluded
  ]
  keywords = ', '.join(filtered_keywords)
  colors = ', '.join(
    c['name'] for c in tone.get('color_palette', [])
  )

  # 방 유형별 공간 힌트 (욕실 등 특수 공간에 적합한 요소 강제 포함)
  space_hint = ''
  hint_key = lookup_room_key(room_type, _ROOM_SPACE_HINTS)
  if hint_key:
    space_hint = f'{_ROOM_SPACE_HINTS[hint_key]}, '

  # 방 유형별 negative 단서 (해당 공간에 절대 그려선 안 되는 사물 명시)
  negative_hint = ''
  neg_key = lookup_room_key(room_type, _ROOM_NEGATIVE_HINTS)
  if neg_key:
    negative_hint = f', {_ROOM_NEGATIVE_HINTS[neg_key]}'

  # 발코니 인접·확장 여부에 따른 경계 단서 생성
  balcony_hint = ''
  if room.get('has_adjoining_balcony'):
    expanded = room.get('balcony_expanded')  # True/False/None
    hint_text = _BALCONY_BOUNDARY_HINTS.get(expanded, '')
    if hint_text:
      balcony_hint = f', {hint_text}'

  # 방 면적 → 공간감 힌트 (Imagen이 방 크기를 왜곡하지 않도록)
  size_hint = build_size_hint(room.get('area_sqm'))

  base = (
    f'Korean apartment {size_hint}{room_en} interior design, '
    f'{space_hint}'
    f'{tone.get("name", "")} style, '
    f'{keywords}, '
    f'color palette: {colors}, '
    'photorealistic, high quality, natural lighting, 4K resolution, '
    'single room view, one room only, no split screen, no collage, no diptych, '
    f'clean modern space, no people{negative_hint}{balcony_hint}'
  )

  appliance_hint = build_appliance_hint(room_type, refinement)
  reference_hint = build_reference_style_hint(reference_signature)
  return base + build_refinement_hint(refinement) + appliance_hint + reference_hint

import asyncio
import base64
import json
import logging
import re
from datetime import datetime, timezone

from anthropic import AsyncAnthropic

from core.cache import furniture_query_cache, trend_cache
from core.config import get_settings

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*([\s\S]+?)\s*```', re.IGNORECASE)

# 방 유형별 이미지 프롬프트에서 제외해야 할 가구/소품 키워드
# (욕실에 소파가 나오는 등의 이상 렌더링 방지)
_ROOM_EXCLUDED_KEYWORDS: dict[str, set[str]] = {
  '욕실': {'소파', '침대', '식탁', '러그', '커튼', '책상', '소파베드', '쇼파'},
  '주방': {'소파', '침대', '러그'},
  '발코니': {'소파', '침대', '식탁'},
}

# 발코니 인접 상태별 Imagen 프롬프트 단서 (비확장/확장형)
_BALCONY_BOUNDARY_HINTS: dict[str | None, str] = {
  False: (
    'room interior bounded by floor-to-ceiling sliding glass door to balcony, '
    'balcony NOT part of room, no furniture beyond sliding door, '
    'interior wall ends at glass door'
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
  '안방': 'no exterior balcony tiles inside room',
  '침실': 'no exterior balcony tiles inside room',
  '작은방': 'no exterior balcony tiles inside room',
}

# 방 유형별 이미지 프롬프트에 강제 포함할 공간 힌트 (영문)
_ROOM_SPACE_HINTS: dict[str, str] = {
  '욕실': 'bathroom with bathtub or shower, vanity mirror, towel rack',
  '주방': 'kitchen with cabinets and countertop',
  '발코니': 'balcony with plants and outdoor furniture',
  '발코나': 'balcony with plants and outdoor furniture',
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

# 가구별 이케아 검색어 생성 시스템 프롬프트
_FURNITURE_QUERY_SYSTEM_PROMPT = '''당신은 이케아 한국 상품 검색 전문가입니다.
제공된 인테리어 톤(색상 팔레트, 스타일 키워드)과 방 정보를 기반으로
이케아 검색 API에서 사용할 가구별 한국어 검색어를 생성해주세요.

규칙:
1. 검색어는 3~6단어로 구성된 한국어
2. 색상명은 hex에서 한국어로 변환 (예: #2E4D3A → "딥그린", #F5E6C8 → "아이보리", #C8B89A → "베이지")
   색상 토큰을 반드시 검색어에 포함하여 이미지 톤과 유사한 색상의 상품이 검색되도록 할 것
3. 각 슬롯에 어울리는 재질·스타일 키워드 1개 포함
4. 욕실·주방·발코니 등 기능적 공간은 반드시 방 이름을 검색어 맨 앞에 포함할 것
   (예: 욕실 → "욕실 수납장", "욕실 거울", 주방 → "주방 수납장")
   거실·침실은 방 이름 생략 가능
5. expected_colors는 상품명에서 매칭할 한국어 색상·재질 토큰 2~5개
6. 이케아에서 판매하지 않는 품목(수전, 타일, 변기 등)은 이케아에서 판매하는 유사 품목으로 대체할 것
   (예: 수전 → 욕실 수건걸이, 타일 → 욕실 매트)

예시 (아이보리 소프트 미니멀 톤 + 욕실 / 슬롯: 욕실수납장, 욕실매트, 욕실거울, 수건걸이):
```json
{
  "rooms": [
    {
      "room_id": "room-uuid-example",
      "queries": [
        {"slot": "욕실수납장", "query": "욕실 아이보리 세면대 하부장", "expected_colors": ["아이보리", "화이트", "크림"]},
        {"slot": "욕실매트", "query": "욕실 베이지 소프트 목욕매트", "expected_colors": ["베이지", "아이보리"]},
        {"slot": "욕실거울", "query": "욕실 거울 화이트 미니멀", "expected_colors": ["화이트", "실버"]},
        {"slot": "수건걸이", "query": "욕실 수건걸이 크롬 미니멀", "expected_colors": ["실버", "크롬", "메탈"]}
      ]
    }
  ]
}
```

예시 (딥그린 모던 톤 + 거실 / 슬롯: 소파, 사이드테이블, 조명, 러그):
```json
{
  "rooms": [
    {
      "room_id": "room-uuid-example",
      "queries": [
        {"slot": "소파", "query": "딥그린 벨벳 모던 4인용 소파", "expected_colors": ["딥그린", "그린", "벨벳"]},
        {"slot": "사이드테이블", "query": "월넛 원목 원형 사이드테이블", "expected_colors": ["월넛", "원목", "브라운"]},
        {"slot": "조명", "query": "블랙 매트 펜던트 조명", "expected_colors": ["블랙", "매트", "메탈"]},
        {"slot": "러그", "query": "그레이 단색 북유럽 러그", "expected_colors": ["그레이", "그린", "단색"]}
      ]
    }
  ]
}
```

반드시 위와 동일한 JSON 코드 블록 형식으로만 응답하세요. 코드 블록 외 텍스트 금지.'''

# 방별 렌더링 이미지에서 가구 시각 속성을 추출하는 시스템 프롬프트
_RENDER_VISION_SYSTEM_PROMPT = '''당신은 인테리어 이미지 분석 전문가입니다.
제공된 방 시안에서 주어진 가구 슬롯에 해당하는 가구를 식별하고,
각 가구의 시각 속성을 JSON 코드 블록 한 개로만 반환하세요. 코드 블록 외 텍스트 금지.

응답 형식:
```json
{
  "슬롯명": {
    "primary_hex": "#A0B899",
    "secondary_hex": "#D4C5A9",
    "materials": ["원목", "자작나무"],
    "structure": ["큐브", "인셋박스", "벽걸이형"],
    "style_tokens": ["스칸디나비안", "내추럴"]
  }
}
```

규칙:
- 이미지에서 해당 슬롯이 보이지 않으면 null로 설정
- primary_hex: 가구의 가장 넓은 면의 주색상 hex
- secondary_hex: 인셋·내부 마감 등 보조색상 hex (없으면 null)
- materials: 마감재 한국어 2~4개 (원목, 벨벳, 패브릭, 메탈, 유리 등)
- structure: 형태·구조 키워드 한국어 3~5개 (큐브, 인셋, 라운드, 벽걸이형, 슬라이딩도어 등)
- style_tokens: 스타일 키워드 한국어 2~3개 (스칸디나비안, 미니멀, 내추럴 등)'''

# Claude에게 방 추출을 요청하는 시스템 프롬프트
_VISION_SYSTEM_PROMPT = '''당신은 아파트 도면 분석 전문가입니다.
도면 이미지에서 방 정보를 추출해 반드시 아래 JSON 형식으로만 응답하세요.
JSON 코드 블록 외에 어떤 텍스트도 포함하지 마세요.

응답 형식:
```json
{
  "rooms": [
    {
      "room_type": "거실",
      "area_sqm": 18.5,
      "confidence": 0.92,
      "priority": 1,
      "position": {"x": 0.05, "y": 0.10, "w": 0.35, "h": 0.40},
      "has_adjoining_balcony": true,
      "balcony_expanded": false
    }
  ],
  "warnings": []
}
```

규칙:
- room_type: 도면에 표기된 한국어 방 이름을 그대로 사용 (예: 거실, 주방, 안방, 침실2, 침실3, 욕실, 발코니 등). 번호가 붙은 방(침실2, 침실3)도 도면 표기 그대로 반환
- priority: 거실=1, 주방=2, 안방=3, 침실·침실2·침실3 등 번호 순=4·5·6, 기타 순
- confidence: 0~1 사이 신뢰도 점수
- position: 도면 이미지 내 상대 좌표 (0~1 정규화). 모를 경우 null
- has_adjoining_balcony: 이 방이 발코니/베란다와 인접해 있으면 true, 아니면 false. 한국 아파트 도면에서 발코니는 보통 빗금(해칭) 패턴이나 옅은 색상으로 표시되며 깊이 1.0~1.5m
- balcony_expanded: 발코니와 방 사이 경계선이 점선이거나 없으면 true(확장형), 실선이면 false(비확장형), 판별 불가시 null
- 문·창문은 추출하지 않음
- 방이 인식되지 않으면 warnings 배열에 이유 포함'''


def _parse_json_block(text: str) -> dict:
  """텍스트에서 JSON 블록을 추출하고 파싱한다."""
  match = _JSON_BLOCK_RE.search(text)
  if match:
    return json.loads(match.group(1))
  # 코드 블록 없이 JSON만 있는 경우 직접 파싱 시도
  return json.loads(text.strip())


def _now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


class ClaudeService:
  def __init__(self) -> None:
    settings = get_settings()
    self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    self._model = settings.CLAUDE_MODEL

  async def analyze_floorplan(
    self,
    image_bytes: bytes,
    mime: str,
    floor_area_pyeong: float,
  ) -> dict:
    """도면 이미지를 분석해 방 정보 JSON을 반환한다."""
    b64 = base64.b64encode(image_bytes).decode()

    resp = await self._client.messages.create(
      model=self._model,
      max_tokens=2048,
      system=_VISION_SYSTEM_PROMPT,
      messages=[{
        'role': 'user',
        'content': [
          {
            'type': 'image',
            'source': {'type': 'base64', 'media_type': mime, 'data': b64},
          },
          {
            'type': 'text',
            'text': (
              f'공급면적 {floor_area_pyeong}평 아파트 도면입니다. '
              '방 이름, 개수, 우선순위를 추출해 JSON으로 반환해주세요.'
            ),
          },
        ],
      }],
    )

    result = _parse_json_block(resp.content[0].text)
    logger.info('Vision 분석 완료: 방 %d개', len(result.get('rooms', [])))
    return result

  async def generate_tone_candidates(
    self,
    rooms: list[dict],
    floor_area_pyeong: float,
    year: int = 2026,
  ) -> tuple[list[dict], dict]:
    """도면 특성과 트렌드를 기반으로 인테리어 톤 후보 6개를 생성한다."""
    cache_key = f'tone-trend:{year}'
    cached_trend = trend_cache.get(cache_key)

    # 캐시 히트 시 Web Search 생략
    if cached_trend:
      tools = []
      trend_context = f'2026년 인테리어 트렌드 요약:\n{json.dumps(cached_trend, ensure_ascii=False)}'
      logger.info('트렌드 캐시 히트: %s', cache_key)
    else:
      tools = [{'name': 'web_search', 'type': 'web_search_20250305'}]
      trend_context = f'{year}년 한국 인테리어 트렌드를 웹에서 검색해 반영해주세요.'
      logger.info('트렌드 캐시 미스: Web Search 호출')

    room_summary = ', '.join(r.get('room_type', '') for r in rooms)
    prompt = f'''아파트 인테리어 톤 후보 6개를 생성해주세요.

도면 정보:
- 공급면적: {floor_area_pyeong}평
- 방 구성: {room_summary}

{trend_context}

반드시 아래 JSON 형식으로만 응답하세요 (JSON 코드 블록 외 텍스트 금지):

```json
{{
  "tones": [
    {{
      "tone_index": 1,
      "name": "호텔라이크",
      "category": "luxury",
      "description": "차분한 뉴트럴 팔레트와 간접조명 중심의 고급스러운 공간",
      "reason": "거실과 안방이 분리된 구조라 고급스러운 휴식 무드가 잘 맞음",
      "color_palette": [
        {{"name": "웜 화이트", "hex": "#F7F3EA", "role": "벽·천장"}},
        {{"name": "딥 그레이", "hex": "#4A4A4A", "role": "가구"}}
      ],
      "keywords": ["호텔라이크", "뉴트럴", "간접조명", "소파", "러그"]
    }}
  ],
  "trend_summary": []
}}
```

규칙:
- 6개 톤은 각각 트렌드 검색 결과와 도면 특성을 반영한 고유한 category를 자유롭게 결정
  (참고 카테고리 예시: luxury, natural, minimal, color, trendy, practical, japandi, wabi-sabi, coastal, vintage, industrial, biophilic, maximalist, artdeco, cottagecore, dark-moody 등)
- 6개 카테고리는 서로 중복 없이 다양한 컨셉을 커버할 것
- 각 톤의 color_palette는 2~4개 컬러
- keywords는 Imagen 프롬프트와 Naver 상품 검색에 사용할 단어 3~5개
- reason은 이 도면 구조에 해당 톤이 맞는 이유 1~2문장'''

    resp = await self._client.messages.create(
      model=self._model,
      max_tokens=4000,
      messages=[{'role': 'user', 'content': prompt}],
      tools=tools if tools else [],
    )

    # Tool Use 응답에서 텍스트 블록 추출
    text = ''
    for block in resp.content:
      if hasattr(block, 'text'):
        text += block.text

    parsed = _parse_json_block(text)
    tones = parsed.get('tones', [])
    trend_raw = parsed.get('trend_summary', [])

    # 캐시 미스 시 트렌드 데이터 저장
    if not cached_trend and trend_raw:
      trend_cache[cache_key] = trend_raw

    snapshot = {
      'searched_at': _now_iso(),
      'cache_hit': cached_trend is not None,
      'trends': trend_raw if not cached_trend else cached_trend,
    }

    logger.info('톤 후보 %d개 생성 완료 (cache_hit=%s)', len(tones), snapshot['cache_hit'])
    return tones, snapshot

  async def generate_custom_tone_variants(
    self,
    rooms: list[dict],
    floor_area_pyeong: float,
    user_text: str,
    mood_chips: list[str],
    year: int = 2026,
  ) -> tuple[list[dict], dict]:
    """사용자 입력(자유 텍스트 + 무드 칩)을 기반으로 톤 변형 3개를 생성한다.

    tone_index: 1=안전(입력 충실), 2=중립(균형), 3=대담(확장·대비)
    트렌드 캐시는 자동 추천 모드와 동일한 키로 공유한다.
    """
    cache_key = f'tone-trend:{year}'
    cached_trend = trend_cache.get(cache_key)

    if cached_trend:
      tools = []
      trend_context = f'2026년 인테리어 트렌드 요약:\n{json.dumps(cached_trend, ensure_ascii=False)}'
      logger.info('트렌드 캐시 히트: %s', cache_key)
    else:
      tools = [{'name': 'web_search', 'type': 'web_search_20250305'}]
      trend_context = f'{year}년 한국 인테리어 트렌드를 웹에서 검색해 반영해주세요.'
      logger.info('트렌드 캐시 미스: Web Search 호출')

    room_summary = ', '.join(r.get('room_type', '') for r in rooms)
    chips_text = ', '.join(mood_chips) if mood_chips else '(없음)'

    prompt = f'''사용자가 원하는 인테리어 스타일을 기반으로 톤 변형 3개를 생성해주세요.

도면 정보:
- 공급면적: {floor_area_pyeong}평
- 방 구성: {room_summary}

사용자 입력:
- 원하는 분위기: {user_text}
- 선택한 무드 키워드: {chips_text}

{trend_context}

반드시 아래 JSON 형식으로만 응답하세요 (JSON 코드 블록 외 텍스트 금지):

```json
{{
  "tones": [
    {{
      "tone_index": 1,
      "name": "톤 이름",
      "category": "카테고리",
      "description": "공간 분위기 설명",
      "reason": "사용자 입력을 어떻게 반영했는지 1~2문장",
      "color_palette": [
        {{"name": "컬러 이름", "hex": "#F7F3EA", "role": "벽·천장"}},
        {{"name": "컬러 이름", "hex": "#4A4A4A", "role": "가구"}}
      ],
      "keywords": ["키워드1", "키워드2", "키워드3"]
    }}
  ],
  "trend_summary": []
}}
```

규칙:
- tone_index 1: 안전 — 사용자 입력을 가장 충실히 반영, 무난하고 안정적인 해석
- tone_index 2: 중립 — 사용자 의도와 2026 트렌드를 균형 있게 혼합
- tone_index 3: 대담 — 사용자 입력을 확장·재해석하여 콘트라스트와 개성을 강조
- 3개 톤은 서로 뚜렷이 차별화되어야 함
- reason 필드에 사용자 입력을 구체적으로 언급하며 어떻게 반영했는지 명시
- 각 color_palette는 2~4개 컬러
- keywords는 Imagen 프롬프트에 쓸 단어 3~5개'''

    resp = await self._client.messages.create(
      model=self._model,
      max_tokens=3000,
      messages=[{'role': 'user', 'content': prompt}],
      tools=tools if tools else [],
    )

    text = ''
    for block in resp.content:
      if hasattr(block, 'text'):
        text += block.text

    parsed = _parse_json_block(text)
    tones = parsed.get('tones', [])
    trend_raw = parsed.get('trend_summary', [])

    if not cached_trend and trend_raw:
      trend_cache[cache_key] = trend_raw

    snapshot = {
      'searched_at': _now_iso(),
      'cache_hit': cached_trend is not None,
      'trends': trend_raw if not cached_trend else cached_trend,
    }

    logger.info('커스텀 톤 변형 %d개 생성 완료 (cache_hit=%s)', len(tones), snapshot['cache_hit'])
    return tones, snapshot

  @staticmethod
  def _lookup_room_key(room_type: str, key_map: dict) -> str | None:
    """방 이름으로 딕셔너리 키를 찾는다.

    우선순위: 정확 매칭 → endswith 매칭(부부욕실→욕실) → startswith 매칭(침실2→침실)
    """
    if room_type in key_map:
      return room_type
    for key in key_map:
      if room_type.endswith(key):
        return key
    for key in key_map:
      if room_type.startswith(key):
        return key
    return None

  def build_imagen_prompt(
    self,
    room: dict,
    tone: dict,
    refinement: dict | None = None,
  ) -> str:
    """방 정보와 선택 톤을 기반으로 Imagen 프롬프트를 생성한다."""
    room_type = room.get('room_type', '거실')

    # 한국어 방 이름을 영어로 변환 (Imagen은 영어 모델 — 한국어 토큰이 공간 인식을 흐림)
    # 정확 매칭 우선, 없으면 endswith/startswith 순 매칭
    room_en = _ROOM_EN_NAMES.get(room_type)
    if room_en is None:
      matched_key = self._lookup_room_key(room_type, _ROOM_EN_NAMES)
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
    excl_key = self._lookup_room_key(room_type, _ROOM_EXCLUDED_KEYWORDS)
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
    hint_key = self._lookup_room_key(room_type, _ROOM_SPACE_HINTS)
    if hint_key:
      space_hint = f'{_ROOM_SPACE_HINTS[hint_key]}, '

    # 방 유형별 negative 단서 (해당 공간에 절대 그려선 안 되는 사물 명시)
    negative_hint = ''
    neg_key = self._lookup_room_key(room_type, _ROOM_NEGATIVE_HINTS)
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
    size_hint = self._build_size_hint(room.get('area_sqm'))

    base = (
      f'Korean apartment {size_hint}{room_en} interior design, '
      f'{space_hint}'
      f'{tone.get("name", "")} style, '
      f'{keywords}, '
      f'color palette: {colors}, '
      'photorealistic, high quality, natural lighting, 4K resolution, '
      f'clean modern space, no people{negative_hint}{balcony_hint}'
    )

    appliance_hint = self._build_appliance_hint(room_type, refinement)
    return base + self._build_refinement_hint(refinement) + appliance_hint

  @staticmethod
  def _build_size_hint(area_sqm: float | None) -> str:
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

  @staticmethod
  def _build_appliance_hint(room_type: str, refinement: dict | None) -> str:
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

  @staticmethod
  def _build_refinement_hint(refinement: dict | None) -> str:
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

  def build_rationale(self, room: dict, tone: dict) -> str:
    """방별 추천 근거 텍스트를 생성한다."""
    return (
      f'{room.get("room_type", "이 공간")}에 {tone.get("name", "")} 톤을 적용했습니다. '
      f'{tone.get("description", "")} '
      f'{tone.get("reason", "")}'
    )

  async def generate_furniture_queries(
    self,
    tone: dict,
    rooms: list[dict],
    slots_map: dict[str, list[str]],
  ) -> dict[str, list[dict]]:
    """톤과 방 목록을 기반으로 가구 슬롯별 네이버 검색어를 생성한다.

    여러 방을 1회 Claude 호출로 묶어 처리한다. TTLCache(24h)를 사용해 동일
    톤+방 유형 조합은 재계산하지 않는다.

    반환값: {room_id: [{slot, query, expected_colors}, ...]}
    """
    tone_id = str(tone.get('id', ''))
    colors_text = ', '.join(
      f"{c['name']}({c['hex']})" for c in tone.get('color_palette', [])
    )
    keywords_text = ', '.join(tone.get('keywords', []))

    # 캐시 히트 확인 — 캐시에 없는 방만 Claude에 요청
    result: dict[str, list[dict]] = {}
    uncached_rooms: list[dict] = []
    for room in rooms:
      cache_key = f'fq:{tone_id}:{room.get("room_type", "")}'
      cached = furniture_query_cache.get(cache_key)
      if cached is not None:
        result[room['id']] = cached
        logger.info('가구 쿼리 캐시 히트: %s', cache_key)
      else:
        uncached_rooms.append(room)

    if not uncached_rooms:
      return result

    # 캐시 미스된 방들을 1회 Claude 호출로 묶음 처리
    rooms_spec = '\n'.join(
      f'- room_id: {r["id"]}, room_type: {r["room_type"]}, '
      f'슬롯: {", ".join(slots_map.get(r["room_type"], ["가구", "조명"]))}'
      for r in uncached_rooms
    )

    prompt = f'''인테리어 톤 정보:
- 이름: {tone.get("name", "")}
- 설명: {tone.get("description", "")}
- 색상 팔레트: {colors_text}
- 스타일 키워드: {keywords_text}

추천 대상 방 목록:
{rooms_spec}

위 각 방의 슬롯별 네이버 쇼핑 검색어를 JSON으로 생성해주세요.
room_id는 위 목록의 값을 그대로 사용하세요.'''

    resp = await self._client.messages.create(
      model=self._model,
      max_tokens=2000,
      system=_FURNITURE_QUERY_SYSTEM_PROMPT,
      messages=[{'role': 'user', 'content': prompt}],
    )

    text = next((block.text for block in resp.content if hasattr(block, 'text') and block.text), '')
    if not text.strip():
      raise ValueError('Claude 가구 쿼리 응답이 비어있습니다')
    parsed = _parse_json_block(text)
    for room_data in parsed.get('rooms', []):
      room_id = room_data.get('room_id', '')
      queries = room_data.get('queries', [])
      result[room_id] = queries

      # 결과를 캐시에 저장 (해당 방 유형 키로)
      matching_room = next((r for r in uncached_rooms if r['id'] == room_id), None)
      if matching_room:
        cache_key = f'fq:{tone_id}:{matching_room["room_type"]}'
        furniture_query_cache[cache_key] = queries

    logger.info('가구 쿼리 생성 완료: %d개 방', len(parsed.get('rooms', [])))
    return result

  async def analyze_render_visuals(
    self,
    image_bytes: bytes,
    mime: str,
    slots: list[str],
    timeout_s: float = 15.0,
  ) -> dict[str, dict] | None:
    """Imagen이 생성한 방 이미지에서 가구 슬롯별 시각 속성을 추출한다.

    실패·타임아웃 시 None을 반환하고 예외를 전파하지 않는다.
    """
    b64 = base64.b64encode(image_bytes).decode()
    slots_text = ', '.join(slots)

    async def _call() -> dict:
      resp = await self._client.messages.create(
        model=self._model,
        max_tokens=1024,
        system=_RENDER_VISION_SYSTEM_PROMPT,
        messages=[{
          'role': 'user',
          'content': [
            {
              'type': 'image',
              'source': {'type': 'base64', 'media_type': mime, 'data': b64},
            },
            {
              'type': 'text',
              'text': (
                f'이 방 시안에서 다음 가구 슬롯의 시각 속성을 추출해주세요: {slots_text}'
              ),
            },
          ],
        }],
      )
      text = next((block.text for block in resp.content if hasattr(block, 'text')), '')
      return _parse_json_block(text)

    try:
      result = await asyncio.wait_for(_call(), timeout=timeout_s)
      logger.info('Vision 재분석 완료: 슬롯 %d개', len(result))
      return result
    except Exception as e:
      logger.warning('Vision 재분석 실패, 텍스트 필터로 폴백: %s', e, exc_info=True)
      return None

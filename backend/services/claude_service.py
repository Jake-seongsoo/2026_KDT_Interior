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

# 방 유형의 영문 자연어 이름 (Imagen 프롬프트용 — 한국어 토큰이 영어 모델 해석을 흐림)
_ROOM_EN_NAMES: dict[str, str] = {
  '거실': 'living room',
  '주방': 'kitchen',
  '안방': 'master bedroom',
  '침실': 'bedroom',
  '욕실': 'bathroom',
  '발코니': 'balcony',
  '현관': 'entrance',
  '다용도실': 'utility room',
  '작은방': 'small bedroom',
}

# 방 유형별 Imagen negative 단서 (해당 공간에 절대 등장하면 안 되는 사물)
_ROOM_NEGATIVE_HINTS: dict[str, str] = {
  '욕실': 'no sofa, no couch, no bed, no dining table, no rug, no curtain',
  '주방': 'no sofa, no bed',
  '발코니': 'no sofa, no bed, no dining table',
}

# 방 유형별 이미지 프롬프트에 강제 포함할 공간 힌트 (영문)
_ROOM_SPACE_HINTS: dict[str, str] = {
  '욕실': 'bathroom with bathtub or shower, vanity mirror, towel rack',
  '주방': 'kitchen with cabinets and countertop',
  '발코니': 'balcony with plants and outdoor furniture',
}

# 가구별 네이버 검색어 생성 시스템 프롬프트
_FURNITURE_QUERY_SYSTEM_PROMPT = '''당신은 한국 인테리어 상품 검색 전문가입니다.
제공된 인테리어 톤(색상 팔레트, 스타일 키워드)과 방 정보를 기반으로
네이버 쇼핑에서 검색할 가구별 한국어 검색어를 생성해주세요.

규칙:
1. 검색어는 3~6단어로 구성된 한국어
2. 색상명은 hex에서 한국어로 변환 (예: #2E4D3A → "딥그린" 또는 "포레스트그린", #F5E6C8 → "아이보리" 또는 "크림")
3. 각 슬롯에 어울리는 재질·스타일 키워드 1개 포함
4. 방 이름("거실", "침실" 등)은 검색어에 포함하지 않음 (검색 결과 오염 방지)
5. expected_colors는 상품명에서 매칭할 한국어 색상·재질 토큰 2~5개

예시 (딥그린 모던 톤 + 거실 / 슬롯: 소파, 사이드테이블, 조명, 러그):
```json
{
  "rooms": [
    {
      "room_id": "room-uuid-example",
      "queries": [
        {"slot": "소파", "query": "딥그린 벨벳 모던 4인용 소파", "expected_colors": ["딥그린", "그린", "벨벳"]},
        {"slot": "사이드테이블", "query": "월넛 원목 원형 사이드테이블", "expected_colors": ["월넛", "원목", "브라운"]},
        {"slot": "조명", "query": "블랙 매트 펜던트 6구 조명", "expected_colors": ["블랙", "매트", "메탈"]},
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
      "position": {"x": 0.05, "y": 0.10, "w": 0.35, "h": 0.40}
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

  def build_imagen_prompt(self, room: dict, tone: dict) -> str:
    """방 정보와 선택 톤을 기반으로 Imagen 프롬프트를 생성한다."""
    room_type = room.get('room_type', '거실')

    # 한국어 방 이름을 영어로 변환 (Imagen은 영어 모델 — 한국어 토큰이 공간 인식을 흐림)
    room_en = _ROOM_EN_NAMES.get(room_type)
    if room_en is None:
      for key, name in _ROOM_EN_NAMES.items():
        if room_type.startswith(key):
          suffix = room_type[len(key):]
          room_en = f'{name} {suffix}'.strip() if suffix else name
          break
    if room_en is None:
      room_en = room_type

    # 방 유형과 맞지 않는 가구 키워드 제거 (욕실에 소파 등 방지)
    excluded = set()
    for key, kw_set in _ROOM_EXCLUDED_KEYWORDS.items():
      if room_type == key or room_type.startswith(key):
        excluded = kw_set
        break

    filtered_keywords = [
      kw for kw in tone.get('keywords', [])
      if kw not in excluded
    ]
    keywords = ', '.join(filtered_keywords)
    colors = ', '.join(
      f"{c['name']}({c['hex']})" for c in tone.get('color_palette', [])
    )

    # 방 유형별 공간 힌트 (욕실 등 특수 공간에 적합한 요소 강제 포함)
    space_hint = ''
    for key, hint in _ROOM_SPACE_HINTS.items():
      if room_type == key or room_type.startswith(key):
        space_hint = f'{hint}, '
        break

    # 방 유형별 negative 단서 (해당 공간에 절대 그려선 안 되는 사물 명시)
    negative_hint = ''
    for key, neg in _ROOM_NEGATIVE_HINTS.items():
      if room_type == key or room_type.startswith(key):
        negative_hint = f', {neg}'
        break

    return (
      f'Korean apartment {room_en} interior design, '
      f'{space_hint}'
      f'{tone.get("name", "")} style, '
      f'{keywords}, '
      f'color palette: {colors}, '
      'photorealistic, high quality, natural lighting, 4K resolution, '
      f'clean modern space, no people{negative_hint}'
    )

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

    text = next((block.text for block in resp.content if hasattr(block, 'text')), '')
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
    timeout_s: float = 8.0,
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
      logger.warning('Vision 재분석 실패, 텍스트 필터로 폴백: %s', e)
      return None

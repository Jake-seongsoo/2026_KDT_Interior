import asyncio
import base64
import json
import logging
import re
from datetime import datetime, timezone

from anthropic import AsyncAnthropic

from core.cache import furniture_query_cache, trend_cache
from core.config import get_settings
from services import imagen_prompt

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*([\s\S]+?)\s*```', re.IGNORECASE)

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

# 사용자가 업로드한 인테리어 레퍼런스 이미지에서 톤 시그니처를 추출하는 시스템 프롬프트
_REFERENCE_VISION_SYSTEM_PROMPT = '''당신은 인테리어 분위기 분석 전문가입니다.
사용자가 업로드한 인테리어 사진(카페·SNS 캡쳐 등)에서 톤·재질·분위기를 추출해
반드시 아래 JSON 형식 코드 블록 한 개로만 응답하세요. 코드 블록 외 텍스트 금지.

응답 형식:
```json
{
  "primary_hex": "#E8DFD3",
  "secondary_hex": "#A89682",
  "accent_hex": "#2E2A26",
  "materials": ["원목", "패브릭", "황동"],
  "style_tokens": ["웜", "japandi", "코지"],
  "lighting": "warm low-key indirect",
  "mood": "차분하고 따뜻한 휴식 무드"
}
```

규칙:
- primary_hex: 사진에서 가장 넓은 면적을 차지하는 주색상 hex
- secondary_hex: 두 번째로 두드러진 색상 hex
- accent_hex: 포인트가 되는 강조 색상 hex (없으면 secondary와 동일하게)
- materials: 식별되는 마감재 한국어 2~4개 (원목, 패브릭, 메탈, 가죽, 유리, 황동, 대리석, 콘크리트 등)
- style_tokens: 한국 인테리어 시장에서 흔히 쓰는 스타일 키워드 2~4개
  (japandi, 미니멀, 내추럴, 코지, 모던, 빈티지, 인더스트리얼, 클래식, 스칸디나비안, 보헤미안 등)
- lighting: 조명 분위기 영문 1줄 (warm/cool, high/low key, indirect/direct 조합)
- mood: 공간 분위기를 한국어로 짧게 요약 (10~20자)'''

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
- 욕실·화장실(부부욕실, 가족욕실 포함)은 반드시 rooms 배열에 포함. 생활공간 여부와 관계없이 도면에 표기된 모든 방을 추출하며 자체 필터링 금지
- priority: 거실=1, 주방=2, 안방=3, 침실·침실2·침실3 등 번호 순=4·5·6, 욕실=7, 기타 순
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

  async def analyze_reference_image(
    self,
    image_bytes: bytes,
    mime: str,
    timeout_s: float = 15.0,
  ) -> dict | None:
    """사용자 업로드 인테리어 레퍼런스 이미지에서 톤 시그니처를 추출한다.

    실패·타임아웃·파싱 오류 시 None을 반환하고 예외를 전파하지 않는다
    (호출자는 None일 때 시그니처 없이 톤 생성을 계속 진행).
    """
    b64 = base64.b64encode(image_bytes).decode()

    async def _call() -> dict:
      resp = await self._client.messages.create(
        model=self._model,
        max_tokens=1024,
        system=_REFERENCE_VISION_SYSTEM_PROMPT,
        messages=[{
          'role': 'user',
          'content': [
            {
              'type': 'image',
              'source': {'type': 'base64', 'media_type': mime, 'data': b64},
            },
            {
              'type': 'text',
              'text': '이 인테리어 사진의 톤·재질·분위기를 JSON 시그니처로 추출해주세요.',
            },
          ],
        }],
      )
      text = next((block.text for block in resp.content if hasattr(block, 'text')), '')
      return _parse_json_block(text)

    try:
      result = await asyncio.wait_for(_call(), timeout=timeout_s)
      logger.info('레퍼런스 톤 시그니처 추출 완료: %s', result.get('mood', ''))
      return result
    except Exception as e:
      logger.warning('레퍼런스 톤 시그니처 추출 실패: %s', e)
      return None

  @staticmethod
  def _format_reference_block(reference_signature: dict | None) -> str:
    """레퍼런스 시그니처 dict를 톤 생성 프롬프트에 끼울 텍스트 블록으로 변환한다."""
    if not reference_signature:
      return ''
    sig = reference_signature
    materials = ', '.join(sig.get('materials') or [])
    tokens = ', '.join(sig.get('style_tokens') or [])
    return (
      '\n레퍼런스 이미지 분석 결과 (사용자가 원하는 분위기):\n'
      f'- 주색상: {sig.get("primary_hex", "")} / '
      f'보조: {sig.get("secondary_hex", "")} / 포인트: {sig.get("accent_hex", "")}\n'
      f'- 재질: {materials}\n'
      f'- 스타일 키워드: {tokens}\n'
      f'- 조명: {sig.get("lighting", "")}\n'
      f'- 무드: {sig.get("mood", "")}\n'
      '\n레퍼런스 모드 규칙:\n'
      '- 6개 톤 모두 이 시그니처를 시드로 사용해 변주(라이트/다크/웜/쿨/소프트/볼드)\n'
      '- 각 톤의 color_palette 첫 번째 색은 primary_hex 와 인접한 색조(±20)를 유지\n'
      '- keywords에는 위 style_tokens 중 최소 1개를 반드시 포함\n'
    )

  async def generate_tone_candidates(
    self,
    rooms: list[dict],
    floor_area_pyeong: float,
    year: int = 2026,
    reference_signature: dict | None = None,
  ) -> tuple[list[dict], dict]:
    """도면 특성과 트렌드를 기반으로 인테리어 톤 후보 6개를 생성한다.

    reference_signature가 주어지면 6개 톤을 모두 해당 시그니처를 시드로 변주한다.
    """
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
    reference_block = self._format_reference_block(reference_signature)
    prompt = f'''아파트 인테리어 톤 후보 6개를 생성해주세요.

도면 정보:
- 공급면적: {floor_area_pyeong}평
- 방 구성: {room_summary}

{trend_context}
{reference_block}
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
    reference_signature: dict | None = None,
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
    reference_block = self._format_reference_block(reference_signature)

    # 텍스트 없이 레퍼런스 이미지만 있을 때 프롬프트 분기
    if user_text.strip():
      user_input_block = f'''사용자 입력:
- 원하는 분위기: {user_text}
- 선택한 무드 키워드: {chips_text}'''
    else:
      user_input_block = f'''사용자 입력:
- 원하는 분위기: (레퍼런스 이미지에서 추출한 시각 속성으로 대체)
- 선택한 무드 키워드: {chips_text}'''

    prompt = f'''사용자가 원하는 인테리어 스타일을 기반으로 톤 변형 3개를 생성해주세요.

도면 정보:
- 공급면적: {floor_area_pyeong}평
- 방 구성: {room_summary}

{user_input_block}

{trend_context}
{reference_block}
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

  def build_imagen_prompt(
    self,
    room: dict,
    tone: dict,
    refinement: dict | None = None,
    reference_signature: dict | None = None,
  ) -> str:
    """방 정보와 선택 톤을 기반으로 Imagen 프롬프트를 생성한다. (services.imagen_prompt 위임)"""
    return imagen_prompt.build_imagen_prompt(room, tone, refinement, reference_signature)

  @staticmethod
  def _build_size_hint(area_sqm: float | None) -> str:
    return imagen_prompt.build_size_hint(area_sqm)

  @staticmethod
  def _build_reference_style_hint(reference_signature: dict | None) -> str:
    return imagen_prompt.build_reference_style_hint(reference_signature)

  @staticmethod
  def _build_appliance_hint(room_type: str, refinement: dict | None) -> str:
    return imagen_prompt.build_appliance_hint(room_type, refinement)

  @staticmethod
  def _build_refinement_hint(refinement: dict | None) -> str:
    return imagen_prompt.build_refinement_hint(refinement)

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

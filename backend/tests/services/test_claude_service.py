"""ClaudeService 카테고리 다양화 단위 테스트."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.cache import trend_cache
from services.claude_service import ClaudeService, _parse_json_block


# ── _parse_json_block 단위 테스트 ──────────────────────────────────────────

class TestParseJsonBlock:
  def test_code_block_with_json_tag(self):
    text = '```json\n{"key": "value"}\n```'
    assert _parse_json_block(text) == {'key': 'value'}

  def test_code_block_without_tag(self):
    text = '```\n{"key": 1}\n```'
    assert _parse_json_block(text) == {'key': 1}

  def test_raw_json_without_block(self):
    text = '{"tones": []}'
    assert _parse_json_block(text) == {'tones': []}

  def test_invalid_json_raises(self):
    with pytest.raises(Exception):
      _parse_json_block('not json at all')


# ── generate_tone_candidates 프롬프트 검증 ────────────────────────────────

FIXED_CATEGORIES = {'luxury', 'natural', 'minimal', 'color', 'trendy', 'practical'}

DYNAMIC_TONES = [
  {
    'tone_index': 1,
    'name': '자연 속 고요',
    'category': 'japandi',
    'description': '일본식 미니멀과 북유럽 웜톤의 조화',
    'reason': '거실이 넓어 여백의 미가 잘 살음',
    'color_palette': [{'name': '웜 베이지', 'hex': '#E8DCC8', 'role': '벽'}],
    'keywords': ['자파니즈', '원목', '미니멀', '소파', '러그'],
  },
  {
    'tone_index': 2,
    'name': '해안의 바람',
    'category': 'coastal',
    'description': '밝고 청량한 해변 분위기',
    'reason': '발코니와 연결되어 개방감을 극대화',
    'color_palette': [{'name': '오션 블루', 'hex': '#7EC8E3', 'role': '포인트'}],
    'keywords': ['코스탈', '블루', '화이트', '라탄', '조명'],
  },
  {
    'tone_index': 3,
    'name': '어반 인더스트리얼',
    'category': 'industrial',
    'description': '콘크리트 텍스처와 메탈 조합',
    'reason': '주방이 오픈형이라 터프한 소재가 잘 맞음',
    'color_palette': [{'name': '콘크리트 그레이', 'hex': '#9E9E9E', 'role': '벽'}],
    'keywords': ['인더스트리얼', '메탈', '그레이', '선반', '펜던트'],
  },
  {
    'tone_index': 4,
    'name': '보태니컬 그린',
    'category': 'biophilic',
    'description': '식물과 자연 소재로 생동감 있는 공간',
    'reason': '채광이 좋아 식물 배치에 최적',
    'color_palette': [{'name': '포레스트 그린', 'hex': '#3A5F3A', 'role': '포인트'}],
    'keywords': ['바이오필릭', '그린', '식물', '원목', '린넨'],
  },
  {
    'tone_index': 5,
    'name': '모던 다크',
    'category': 'dark-moody',
    'description': '딥 컬러와 매트 소재의 강렬한 무드',
    'reason': '안방 독립 구조로 드라마틱한 침실 연출 가능',
    'color_palette': [{'name': '차콜', 'hex': '#2C2C2C', 'role': '벽'}],
    'keywords': ['다크무디', '블랙', '매트', '벨벳', '간접조명'],
  },
  {
    'tone_index': 6,
    'name': '레트로 빈티지',
    'category': 'vintage',
    'description': '따뜻한 어스톤과 빈티지 가구의 향수',
    'reason': '복층 구조가 빈티지 레이어링과 잘 어울림',
    'color_palette': [{'name': '테라코타', 'hex': '#C1694F', 'role': '포인트'}],
    'keywords': ['빈티지', '테라코타', '어스톤', '우드', '황동'],
  },
]


def _make_mock_response(tones: list[dict]) -> MagicMock:
  """Anthropic 응답 mock 객체를 생성한다."""
  payload = json.dumps({'tones': tones, 'trend_summary': ['2026 트렌드: 자연소재']}, ensure_ascii=False)
  text_block = SimpleNamespace(text=f'```json\n{payload}\n```')
  resp = MagicMock()
  resp.content = [text_block]
  return resp


@pytest.fixture(autouse=True)
def clear_trend_cache():
  """각 테스트 전에 트렌드 캐시를 비워 캐시 간섭을 방지한다."""
  trend_cache.clear()
  yield
  trend_cache.clear()


@pytest.fixture
def service():
  with patch('services.claude_service.get_settings') as mock_settings, \
       patch('services.claude_service.AsyncAnthropic'):
    mock_settings.return_value = MagicMock(
      ANTHROPIC_API_KEY='test-key',
      CLAUDE_MODEL='claude-sonnet-4-6',
    )
    yield ClaudeService()


@pytest.mark.asyncio
async def test_categories_are_not_restricted_to_fixed_list(service):
  """반환된 카테고리가 고정 6개에 국한되지 않는다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(DYNAMIC_TONES)
  )

  rooms = [{'room_type': '거실'}, {'room_type': '안방'}]
  tones, _ = await service.generate_tone_candidates(rooms, floor_area_pyeong=25.0)

  returned_categories = {t['category'] for t in tones}
  # 고정 카테고리 집합과 완전히 같으면 안 됨 (새 카테고리 허용)
  assert returned_categories != FIXED_CATEGORIES
  # 실제로 반환된 카테고리가 동적 목록과 일치
  expected = {t['category'] for t in DYNAMIC_TONES}
  assert returned_categories == expected


@pytest.mark.asyncio
async def test_categories_are_unique(service):
  """6개 톤의 카테고리는 서로 중복되지 않는다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(DYNAMIC_TONES)
  )

  rooms = [{'room_type': '거실'}]
  tones, _ = await service.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  categories = [t['category'] for t in tones]
  assert len(categories) == len(set(categories)), f'중복 카테고리 발생: {categories}'


@pytest.mark.asyncio
async def test_prompt_contains_extended_category_hints(service):
  """프롬프트에 확장된 카테고리 예시(japandi, coastal 등)가 포함된다."""
  captured_prompt = {}

  async def capture(*args, **kwargs):
    captured_prompt['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return _make_mock_response(DYNAMIC_TONES)

  service._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  await service.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  prompt_text = captured_prompt['content']
  for keyword in ('japandi', 'coastal', 'biophilic', 'vintage'):
    assert keyword in prompt_text, f'프롬프트에 "{keyword}" 카테고리 예시가 없음'


@pytest.mark.asyncio
async def test_prompt_does_not_hard_restrict_categories(service):
  """프롬프트가 고정 6개 카테고리만 허용하는 문구를 포함하지 않는다."""
  captured_prompt = {}

  async def capture(*args, **kwargs):
    captured_prompt['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return _make_mock_response(DYNAMIC_TONES)

  service._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  await service.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  prompt_text = captured_prompt['content']
  # 과거 고정 카테고리 목록 문구가 없어야 함
  old_restriction = '(luxury, natural, minimal, color, trendy, practical)'
  assert old_restriction not in prompt_text, '고정 카테고리 제한 문구가 여전히 프롬프트에 남아 있음'


@pytest.mark.asyncio
async def test_snapshot_cache_hit_flag(service):
  """캐시 미스 시 snapshot의 cache_hit이 False이다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(DYNAMIC_TONES)
  )

  rooms = [{'room_type': '거실'}]
  _, snapshot = await service.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  assert snapshot['cache_hit'] is False


# ── build_imagen_prompt 키워드 필터링 테스트 ────────────────────────────────

BATHROOM_TONE = {
  'name': '호텔라이크',
  'description': '고급스러운 공간',
  'color_palette': [{'name': '웜 화이트', 'hex': '#F7F3EA', 'role': '벽'}],
  'keywords': ['호텔라이크', '뉴트럴', '간접조명', '소파', '러그'],
}


class TestBuildImagenPrompt:
  def test_bathroom_excludes_sofa_keyword(self, service):
    """욕실 프롬프트에 소파·러그 키워드가 포함되지 않는다."""
    room = {'room_type': '욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert '소파' not in prompt
    assert '러그' not in prompt

  def test_bathroom_includes_space_hint(self, service):
    """욕실 프롬프트에 욕실 전용 공간 힌트가 포함된다."""
    room = {'room_type': '욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'bathroom' in prompt
    assert 'vanity' in prompt

  def test_living_room_keeps_sofa_keyword(self, service):
    """거실 프롬프트에는 소파 키워드가 유지된다."""
    room = {'room_type': '거실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert '소파' in prompt

  def test_bathroom_keeps_non_excluded_keywords(self, service):
    """욕실이라도 제외 대상이 아닌 키워드는 유지된다."""
    room = {'room_type': '욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert '호텔라이크' in prompt
    assert '간접조명' in prompt

  def test_bathroom_uses_english_room_name(self, service):
    """욕실 프롬프트는 영어 'bathroom'으로 렌더되어야 한다 (한국어 토큰 노이즈 제거)."""
    room = {'room_type': '욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'bathroom' in prompt
    assert '욕실' not in prompt

  def test_bathroom_includes_negative_hint(self, service):
    """욕실 프롬프트에는 negative 가구 단서가 포함된다."""
    room = {'room_type': '욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'no sofa' in prompt
    assert 'no bed' in prompt

  def test_living_room_uses_english_name(self, service):
    """거실은 'living room'으로 변환된다."""
    room = {'room_type': '거실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'living room' in prompt

  def test_numbered_bedroom_translated(self, service):
    """침실2 같은 번호 포함 방은 'bedroom 2'로 변환된다."""
    room = {'room_type': '침실2'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'bedroom' in prompt
    assert '침실' not in prompt

  def test_couple_bathroom_uses_master_bathroom(self, service):
    """부부욕실 프롬프트는 'master bathroom'으로 변환되고 욕실 힌트가 적용된다."""
    room = {'room_type': '부부욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'bathroom' in prompt
    assert '부부욕실' not in prompt
    assert '소파' not in prompt
    assert 'no sofa' in prompt
    assert 'vanity' in prompt

  def test_family_bathroom_uses_bathroom_hints(self, service):
    """가족욕실 프롬프트에 욕실 전용 힌트와 negative 단서가 적용된다."""
    room = {'room_type': '가족욕실'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'bathroom' in prompt
    assert '가족욕실' not in prompt
    assert 'no sofa' in prompt
    assert 'vanity' in prompt

  def test_alpha_room_uses_english_name(self, service):
    """알파룸 프롬프트에 영어 이름이 사용된다."""
    room = {'room_type': '알파룸'}
    prompt = service.build_imagen_prompt(room, BATHROOM_TONE)
    assert 'flexible room' in prompt
    assert '알파룸' not in prompt


# ── generate_furniture_queries 빈 텍스트 처리 테스트 ────────────────────────

class TestGenerateFurnitureQueriesEmptyResponse:
  @pytest.mark.asyncio
  async def test_empty_response_raises_value_error(self, service):
    """Claude가 빈 텍스트를 반환하면 ValueError가 발생한다."""
    from core.cache import furniture_query_cache
    furniture_query_cache.clear()

    empty_resp = MagicMock()
    empty_resp.content = [SimpleNamespace(text='')]
    service._client.messages.create = AsyncMock(return_value=empty_resp)

    tone = {
      'id': 'tone-1',
      'name': '테스트',
      'description': '',
      'color_palette': [],
      'keywords': [],
    }
    rooms = [{'id': 'room-1', 'room_type': '거실'}]
    slots_map = {'거실': ['소파', '조명']}

    with pytest.raises(ValueError, match='비어있습니다'):
      await service.generate_furniture_queries(tone=tone, rooms=rooms, slots_map=slots_map)

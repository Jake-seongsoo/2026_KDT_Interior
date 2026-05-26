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

  def test_bedroom_includes_bed_space_hint(self, service):
    """침실2 프롬프트에 침대·옷장 공간 힌트가 포함된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '미니멀',
      'color_palette': [{'name': '화이트', 'hex': '#FFFFFF', 'role': '벽'}],
      'keywords': ['미니멀', '소파'],
    }
    prompt = service.build_imagen_prompt(room, tone)
    assert 'bed' in prompt
    assert 'wardrobe' in prompt

  def test_bedroom_excludes_kitchen_keywords(self, service):
    """침실 프롬프트에 주방 관련 키워드가 필터링된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '모던',
      'color_palette': [{'name': '그레이', 'hex': '#888888', 'role': '벽'}],
      'keywords': ['모던', '식탁', '가스레인지', '싱크대'],
    }
    prompt = service.build_imagen_prompt(room, tone)
    assert '식탁' not in prompt
    assert '가스레인지' not in prompt
    assert '싱크대' not in prompt

  def test_bedroom_includes_no_kitchen_negative_hint(self, service):
    """침실 프롬프트에 no kitchen 관련 negative 단서가 포함된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '미니멀',
      'color_palette': [],
      'keywords': ['미니멀'],
    }
    prompt = service.build_imagen_prompt(room, tone)
    assert 'no kitchen cabinets' in prompt
    assert 'no stove' in prompt

  def test_master_bedroom_includes_bed_space_hint(self, service):
    """안방 프롬프트에 더블 침대·빌트인 옷장 힌트가 포함된다."""
    room = {'room_type': '안방'}
    tone = {
      'name': '럭셔리',
      'color_palette': [],
      'keywords': ['럭셔리'],
    }
    prompt = service.build_imagen_prompt(room, tone)
    assert 'double bed' in prompt
    assert 'wardrobe' in prompt


# ── generate_custom_tone_variants 테스트 ─────────────────────────────────────

CUSTOM_TONES = [
  {
    'tone_index': 1,
    'name': '안전 베이지',
    'category': 'natural',
    'description': '사용자 입력에 충실한 따뜻한 베이지 톤',
    'reason': '사용자가 원하는 따뜻한 베이지를 벽과 가구에 그대로 반영',
    'color_palette': [{'name': '웜 베이지', 'hex': '#E8D5B7', 'role': '벽·천장'}],
    'keywords': ['베이지', '내추럴', '따뜻함', '우드', '러그'],
  },
  {
    'tone_index': 2,
    'name': '균형 웜톤',
    'category': 'minimal',
    'description': '베이지와 2026 트렌드 뉴트럴을 균형 있게 혼합',
    'reason': '사용자 입력의 웜톤에 트렌디한 뉴트럴 포인트를 추가',
    'color_palette': [{'name': '아이보리', 'hex': '#F5F0E8', 'role': '벽'}],
    'keywords': ['뉴트럴', '미니멀', '웜', '린넨', '조명'],
  },
  {
    'tone_index': 3,
    'name': '대담 콘트라스트',
    'category': 'japandi',
    'description': '베이지 기반에 딥 컬러 포인트로 개성 강조',
    'reason': '사용자의 베이지 선호를 확장해 차콜 포인트로 드라마틱한 대비 연출',
    'color_palette': [{'name': '차콜', 'hex': '#3C3C3C', 'role': '가구 포인트'}],
    'keywords': ['자파니즈', '콘트라스트', '딥컬러', '원목', '간접조명'],
  },
]


@pytest.mark.asyncio
async def test_custom_variants_returns_three_tones(service):
  """generate_custom_tone_variants는 3개 톤을 반환한다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(CUSTOM_TONES)
  )

  rooms = [{'room_type': '거실'}, {'room_type': '안방'}]
  tones, _ = await service.generate_custom_tone_variants(
    rooms, 25.0, '따뜻한 베이지 톤', ['내추럴', '코지']
  )

  assert len(tones) == 3


@pytest.mark.asyncio
async def test_custom_variants_tone_indices(service):
  """반환된 톤의 tone_index가 1·2·3이다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(CUSTOM_TONES)
  )

  rooms = [{'room_type': '거실'}]
  tones, _ = await service.generate_custom_tone_variants(
    rooms, 20.0, '베이지', []
  )

  indices = [t['tone_index'] for t in tones]
  assert indices == [1, 2, 3]


@pytest.mark.asyncio
async def test_custom_variants_prompt_includes_user_text(service):
  """프롬프트에 사용자가 입력한 자유 텍스트가 포함된다."""
  captured: dict = {}

  async def capture(*args, **kwargs):
    captured['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return _make_mock_response(CUSTOM_TONES)

  service._client.messages.create = capture

  user_text = '따뜻한 베이지에 우드 포인트, 카페 같은 느낌'
  rooms = [{'room_type': '거실'}]
  await service.generate_custom_tone_variants(rooms, 20.0, user_text, [])

  assert user_text in captured['content']


@pytest.mark.asyncio
async def test_custom_variants_prompt_includes_mood_chips(service):
  """프롬프트에 선택된 무드 칩 키워드가 포함된다."""
  captured: dict = {}

  async def capture(*args, **kwargs):
    captured['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return _make_mock_response(CUSTOM_TONES)

  service._client.messages.create = capture

  chips = ['내추럴', '코지', '북유럽']
  rooms = [{'room_type': '거실'}]
  await service.generate_custom_tone_variants(rooms, 20.0, '베이지', chips)

  for chip in chips:
    assert chip in captured['content'], f'무드 칩 "{chip}"이 프롬프트에 없음'


@pytest.mark.asyncio
async def test_custom_variants_empty_text_with_reference(service):
  """user_text가 빈 문자열이어도 reference_signature가 있으면 정상 동작한다."""
  service._client.messages.create = AsyncMock(
    return_value=_make_mock_response(CUSTOM_TONES)
  )

  rooms = [{'room_type': '거실'}]
  ref_sig = {'primary_colors': ['#F0EDE5'], 'mood': 'minimal'}
  tones, _ = await service.generate_custom_tone_variants(
    rooms, 24.0, '', [], reference_signature=ref_sig
  )

  assert len(tones) == 3


@pytest.mark.asyncio
async def test_custom_variants_shares_trend_cache(service):
  """자동 추천 모드와 동일한 캐시 키를 사용해 트렌드 캐시를 공유한다."""
  # 트렌드 캐시에 데이터 미리 삽입
  trend_cache['tone-trend:2026'] = ['2026 트렌드: 자연소재']

  calls: list = []

  async def capture(*args, **kwargs):
    calls.append(kwargs)
    return _make_mock_response(CUSTOM_TONES)

  service._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  _, snapshot = await service.generate_custom_tone_variants(rooms, 20.0, '베이지', [])

  # 캐시 히트 → Web Search 미호출
  assert snapshot['cache_hit'] is True
  # tools가 빈 리스트로 호출됐는지 확인
  assert calls[0].get('tools', []) == []


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

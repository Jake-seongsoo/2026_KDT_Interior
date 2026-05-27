"""ClaudeService 카테고리 다양화 단위 테스트."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.cache import trend_cache
from services.claude_service import _parse_json_block


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


@pytest.mark.asyncio
async def test_categories_are_not_restricted_to_fixed_list(claude_service_async, six_tones, make_claude_response, clear_caches):
  """반환된 카테고리가 고정 6개에 국한되지 않는다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(six_tones)
  )

  rooms = [{'room_type': '거실'}, {'room_type': '안방'}]
  tones, _ = await claude_service_async.generate_tone_candidates(rooms, floor_area_pyeong=25.0)

  returned_categories = {t['category'] for t in tones}
  assert returned_categories != FIXED_CATEGORIES
  expected = {t['category'] for t in six_tones}
  assert returned_categories == expected


@pytest.mark.asyncio
async def test_categories_are_unique(claude_service_async, six_tones, make_claude_response, clear_caches):
  """6개 톤의 카테고리는 서로 중복되지 않는다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(six_tones)
  )

  rooms = [{'room_type': '거실'}]
  tones, _ = await claude_service_async.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  categories = [t['category'] for t in tones]
  assert len(categories) == len(set(categories)), f'중복 카테고리 발생: {categories}'


@pytest.mark.asyncio
async def test_prompt_contains_extended_category_hints(claude_service_async, six_tones, make_claude_response, clear_caches):
  """프롬프트에 확장된 카테고리 예시(japandi, coastal 등)가 포함된다."""
  captured_prompt = {}

  async def capture(*args, **kwargs):
    captured_prompt['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return make_claude_response(six_tones)

  claude_service_async._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  await claude_service_async.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  prompt_text = captured_prompt['content']
  for keyword in ('japandi', 'coastal', 'biophilic', 'vintage'):
    assert keyword in prompt_text, f'프롬프트에 "{keyword}" 카테고리 예시가 없음'


@pytest.mark.asyncio
async def test_prompt_does_not_hard_restrict_categories(claude_service_async, six_tones, make_claude_response, clear_caches):
  """프롬프트가 고정 6개 카테고리만 허용하는 문구를 포함하지 않는다."""
  captured_prompt = {}

  async def capture(*args, **kwargs):
    captured_prompt['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return make_claude_response(six_tones)

  claude_service_async._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  await claude_service_async.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  prompt_text = captured_prompt['content']
  old_restriction = '(luxury, natural, minimal, color, trendy, practical)'
  assert old_restriction not in prompt_text, '고정 카테고리 제한 문구가 여전히 프롬프트에 남아 있음'


@pytest.mark.asyncio
async def test_snapshot_cache_hit_flag(claude_service_async, six_tones, make_claude_response, clear_caches):
  """캐시 미스 시 snapshot의 cache_hit이 False이다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(six_tones)
  )

  rooms = [{'room_type': '거실'}]
  _, snapshot = await claude_service_async.generate_tone_candidates(rooms, floor_area_pyeong=20.0)

  assert snapshot['cache_hit'] is False


# ── build_imagen_prompt 키워드 필터링 테스트 ────────────────────────────────

class TestBuildImagenPrompt:
  def test_bathroom_excludes_sofa_keyword(self, claude_service_sync, minimal_tone):
    """욕실 프롬프트에 소파·러그 키워드가 포함되지 않는다."""
    room = {'room_type': '욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert '소파' not in prompt
    assert '러그' not in prompt

  def test_bathroom_includes_space_hint(self, claude_service_sync, minimal_tone):
    """욕실 프롬프트에 욕실 전용 공간 힌트가 포함된다."""
    room = {'room_type': '욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'bathroom' in prompt
    assert 'vanity' in prompt

  def test_living_room_keeps_sofa_keyword(self, claude_service_sync, minimal_tone):
    """거실 프롬프트에는 소파 키워드가 유지된다."""
    room = {'room_type': '거실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert '소파' in prompt

  def test_bathroom_keeps_non_excluded_keywords(self, claude_service_sync, minimal_tone):
    """욕실이라도 제외 대상이 아닌 키워드는 유지된다."""
    room = {'room_type': '욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert '우드' in prompt
    assert '린넨' in prompt

  def test_bathroom_uses_english_room_name(self, claude_service_sync, minimal_tone):
    """욕실 프롬프트는 영어 'bathroom'으로 렌더되어야 한다 (한국어 토큰 노이즈 제거)."""
    room = {'room_type': '욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'bathroom' in prompt
    assert '욕실' not in prompt

  def test_bathroom_includes_negative_hint(self, claude_service_sync, minimal_tone):
    """욕실 프롬프트에는 negative 가구 단서가 포함된다."""
    room = {'room_type': '욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'no sofa' in prompt
    assert 'no bed' in prompt

  def test_living_room_uses_english_name(self, claude_service_sync, minimal_tone):
    """거실은 'living room'으로 변환된다."""
    room = {'room_type': '거실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'living room' in prompt

  def test_numbered_bedroom_translated(self, claude_service_sync, minimal_tone):
    """침실2 같은 번호 포함 방은 'bedroom 2'로 변환된다."""
    room = {'room_type': '침실2'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'bedroom' in prompt
    assert '침실' not in prompt

  def test_couple_bathroom_uses_master_bathroom(self, claude_service_sync, minimal_tone):
    """부부욕실 프롬프트는 'master bathroom'으로 변환되고 욕실 힌트가 적용된다."""
    room = {'room_type': '부부욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'bathroom' in prompt
    assert '부부욕실' not in prompt
    assert '소파' not in prompt
    assert 'no sofa' in prompt
    assert 'vanity' in prompt

  def test_family_bathroom_uses_bathroom_hints(self, claude_service_sync, minimal_tone):
    """가족욕실 프롬프트에 욕실 전용 힌트와 negative 단서가 적용된다."""
    room = {'room_type': '가족욕실'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'bathroom' in prompt
    assert '가족욕실' not in prompt
    assert 'no sofa' in prompt
    assert 'vanity' in prompt

  def test_alpha_room_uses_english_name(self, claude_service_sync, minimal_tone):
    """알파룸 프롬프트에 영어 이름이 사용된다."""
    room = {'room_type': '알파룸'}
    prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
    assert 'flexible room' in prompt
    assert '알파룸' not in prompt

  def test_bedroom_includes_bed_space_hint(self, claude_service_sync):
    """침실2 프롬프트에 침대·옷장 공간 힌트가 포함된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '미니멀',
      'color_palette': [{'name': '화이트', 'hex': '#FFFFFF', 'role': '벽'}],
      'keywords': ['미니멀', '소파'],
    }
    prompt = claude_service_sync.build_imagen_prompt(room, tone)
    assert 'bed' in prompt
    assert 'wardrobe' in prompt

  def test_bedroom_excludes_kitchen_keywords(self, claude_service_sync):
    """침실 프롬프트에 주방 관련 키워드가 필터링된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '모던',
      'color_palette': [{'name': '그레이', 'hex': '#888888', 'role': '벽'}],
      'keywords': ['모던', '식탁', '가스레인지', '싱크대'],
    }
    prompt = claude_service_sync.build_imagen_prompt(room, tone)
    assert '식탁' not in prompt
    assert '가스레인지' not in prompt
    assert '싱크대' not in prompt

  def test_bedroom_includes_no_kitchen_negative_hint(self, claude_service_sync):
    """침실 프롬프트에 no kitchen 관련 negative 단서가 포함된다."""
    room = {'room_type': '침실2'}
    tone = {
      'name': '미니멀',
      'color_palette': [],
      'keywords': ['미니멀'],
    }
    prompt = claude_service_sync.build_imagen_prompt(room, tone)
    assert 'no kitchen cabinets' in prompt
    assert 'no stove' in prompt

  def test_master_bedroom_includes_bed_space_hint(self, claude_service_sync):
    """안방 프롬프트에 더블 침대·빌트인 옷장 힌트가 포함된다."""
    room = {'room_type': '안방'}
    tone = {
      'name': '럭셔리',
      'color_palette': [],
      'keywords': ['럭셔리'],
    }
    prompt = claude_service_sync.build_imagen_prompt(room, tone)
    assert 'double bed' in prompt
    assert 'wardrobe' in prompt


# ── generate_custom_tone_variants 테스트 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_custom_variants_returns_three_tones(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """generate_custom_tone_variants는 3개 톤을 반환한다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(three_custom_tones)
  )

  rooms = [{'room_type': '거실'}, {'room_type': '안방'}]
  tones, _ = await claude_service_async.generate_custom_tone_variants(
    rooms, 25.0, '따뜻한 베이지 톤', ['내추럴', '코지']
  )

  assert len(tones) == 3


@pytest.mark.asyncio
async def test_custom_variants_tone_indices(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """반환된 톤의 tone_index가 1·2·3이다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(three_custom_tones)
  )

  rooms = [{'room_type': '거실'}]
  tones, _ = await claude_service_async.generate_custom_tone_variants(
    rooms, 20.0, '베이지', []
  )

  indices = [t['tone_index'] for t in tones]
  assert indices == [1, 2, 3]


@pytest.mark.asyncio
async def test_custom_variants_prompt_includes_user_text(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """프롬프트에 사용자가 입력한 자유 텍스트가 포함된다."""
  captured: dict = {}

  async def capture(*args, **kwargs):
    captured['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return make_claude_response(three_custom_tones)

  claude_service_async._client.messages.create = capture

  user_text = '따뜻한 베이지에 우드 포인트, 카페 같은 느낌'
  rooms = [{'room_type': '거실'}]
  await claude_service_async.generate_custom_tone_variants(rooms, 20.0, user_text, [])

  assert user_text in captured['content']


@pytest.mark.asyncio
async def test_custom_variants_prompt_includes_mood_chips(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """프롬프트에 선택된 무드 칩 키워드가 포함된다."""
  captured: dict = {}

  async def capture(*args, **kwargs):
    captured['content'] = kwargs.get('messages', [{}])[0].get('content', '')
    return make_claude_response(three_custom_tones)

  claude_service_async._client.messages.create = capture

  chips = ['내추럴', '코지', '북유럽']
  rooms = [{'room_type': '거실'}]
  await claude_service_async.generate_custom_tone_variants(rooms, 20.0, '베이지', chips)

  for chip in chips:
    assert chip in captured['content'], f'무드 칩 "{chip}"이 프롬프트에 없음'


@pytest.mark.asyncio
async def test_custom_variants_empty_text_with_reference(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """user_text가 빈 문자열이어도 reference_signature가 있으면 정상 동작한다."""
  claude_service_async._client.messages.create = AsyncMock(
    return_value=make_claude_response(three_custom_tones)
  )

  rooms = [{'room_type': '거실'}]
  ref_sig = {'primary_colors': ['#F0EDE5'], 'mood': 'minimal'}
  tones, _ = await claude_service_async.generate_custom_tone_variants(
    rooms, 24.0, '', [], reference_signature=ref_sig
  )

  assert len(tones) == 3


@pytest.mark.asyncio
async def test_custom_variants_shares_trend_cache(claude_service_async, three_custom_tones, make_claude_response, clear_caches):
  """자동 추천 모드와 동일한 캐시 키를 사용해 트렌드 캐시를 공유한다."""
  trend_cache['tone-trend:2026'] = ['2026 트렌드: 자연소재']

  calls: list = []

  async def capture(*args, **kwargs):
    calls.append(kwargs)
    return make_claude_response(three_custom_tones)

  claude_service_async._client.messages.create = capture

  rooms = [{'room_type': '거실'}]
  _, snapshot = await claude_service_async.generate_custom_tone_variants(rooms, 20.0, '베이지', [])

  assert snapshot['cache_hit'] is True
  assert calls[0].get('tools', []) == []


# ── generate_furniture_queries 빈 텍스트 처리 테스트 ────────────────────────

class TestGenerateFurnitureQueriesEmptyResponse:
  @pytest.mark.asyncio
  async def test_empty_response_raises_value_error(self, claude_service_async):
    """Claude가 빈 텍스트를 반환하면 ValueError가 발생한다."""
    from core.cache import furniture_query_cache
    furniture_query_cache.clear()

    empty_resp = MagicMock()
    empty_resp.content = [SimpleNamespace(text='')]
    claude_service_async._client.messages.create = AsyncMock(return_value=empty_resp)

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
      await claude_service_async.generate_furniture_queries(tone=tone, rooms=rooms, slots_map=slots_map)

"""가구별 검색어 생성 관련 단위 테스트."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.room_furniture_map import (
  DEFAULT_FURNITURE_SLOTS,
  ROOM_FURNITURE_SLOTS,
  get_furniture_slots,
)
from services.supabase_service import _NON_RENDER_TYPES


# ---------------------------------------------------------------------------
# get_furniture_slots 테스트
# ---------------------------------------------------------------------------

class TestGetFurnitureSlots:
  def test_known_room_types(self):
    assert get_furniture_slots('거실') == ROOM_FURNITURE_SLOTS['거실']
    assert get_furniture_slots('안방') == ROOM_FURNITURE_SLOTS['안방']
    assert get_furniture_slots('주방') == ROOM_FURNITURE_SLOTS['주방']

  def test_numbered_bedroom_prefix_match(self):
    # 침실2, 침실3 등 번호 포함 이름은 '침실' 슬롯과 동일해야 함
    assert get_furniture_slots('침실2') == ROOM_FURNITURE_SLOTS['침실']
    assert get_furniture_slots('침실3') == ROOM_FURNITURE_SLOTS['침실']

  def test_unknown_room_type_returns_default(self):
    result = get_furniture_slots('창고')
    assert result == DEFAULT_FURNITURE_SLOTS

  def test_empty_string_returns_default(self):
    result = get_furniture_slots('')
    assert result == DEFAULT_FURNITURE_SLOTS

  def test_all_defined_rooms_have_at_least_two_slots(self):
    for room_type, slots in ROOM_FURNITURE_SLOTS.items():
      assert len(slots) >= 2, f'{room_type}의 슬롯이 2개 미만'


# ---------------------------------------------------------------------------
# 렌더 대상 공간 블랙리스트 테스트
# ---------------------------------------------------------------------------

class TestNonRenderTypes:
  def test_living_spaces_are_render_targets(self):
    render_spaces = ['거실', '주방', '안방', '침실2', '침실3', '욕실']
    for room in render_spaces:
      assert room not in _NON_RENDER_TYPES, f'{room}이 렌더 대상에서 잘못 제외됨'

  def test_utility_spaces_are_excluded(self):
    excluded = ['현관', '현관창고', '다용도실', '드레스룸', '팬트리', '실외기실', '발코니']
    for room in excluded:
      assert room in _NON_RENDER_TYPES, f'{room}이 제외 목록에 없음'


# ---------------------------------------------------------------------------
# ClaudeService.generate_furniture_queries 테스트
# ---------------------------------------------------------------------------

SAMPLE_TONE = {
  'id': 'tone-uuid-123',
  'name': '딥그린 모던',
  'description': '다크그린 계열의 모던한 공간',
  'keywords': ['모던', '딥그린', '벨벳'],
  'color_palette': [
    {'name': '딥그린', 'hex': '#2E4D3A', 'role': '주조색'},
    {'name': '웜화이트', 'hex': '#F7F3EA', 'role': '벽'},
  ],
}

SAMPLE_ROOMS = [
  {'id': 'room-a', 'room_type': '거실'},
  {'id': 'room-b', 'room_type': '안방'},
]

SAMPLE_SLOTS_MAP = {
  '거실': ['소파', '사이드테이블', '조명', '러그'],
  '안방': ['침대', '협탁', '조명', '커튼'],
}

MOCK_CLAUDE_RESPONSE = {
  'rooms': [
    {
      'room_id': 'room-a',
      'queries': [
        {'slot': '소파', 'query': '딥그린 벨벳 모던 4인용 소파', 'expected_colors': ['딥그린', '그린', '벨벳']},
        {'slot': '사이드테이블', 'query': '월넛 원목 원형 사이드테이블', 'expected_colors': ['월넛', '원목']},
        {'slot': '조명', 'query': '블랙 매트 펜던트 6구', 'expected_colors': ['블랙', '매트']},
        {'slot': '러그', 'query': '그레이 단색 북유럽 러그', 'expected_colors': ['그레이', '단색']},
      ],
    },
    {
      'room_id': 'room-b',
      'queries': [
        {'slot': '침대', 'query': '딥그린 패브릭 퀸 침대', 'expected_colors': ['딥그린', '그린']},
        {'slot': '협탁', 'query': '월넛 원목 1단 협탁', 'expected_colors': ['월넛', '원목']},
      ],
    },
  ]
}


@pytest.fixture
def claude_service():
  """ClaudeService 인스턴스를 설정 mock과 함께 반환한다."""
  with patch('services.claude_service.get_settings') as mock_settings:
    mock_settings.return_value = MagicMock(
      ANTHROPIC_API_KEY='test-key',
      CLAUDE_MODEL='claude-sonnet-4-6',
    )
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      from services.claude_service import ClaudeService
      service = ClaudeService()
      service._client = AsyncMock()
      yield service


@pytest.fixture(autouse=True)
def clear_furniture_cache():
  """각 테스트 전 캐시를 초기화한다."""
  from core.cache import furniture_query_cache
  furniture_query_cache.clear()
  yield
  furniture_query_cache.clear()


class TestGenerateFurnitureQueriesParsing:
  async def test_returns_queries_for_all_rooms(self, claude_service):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=f'```json\n{json.dumps(MOCK_CLAUDE_RESPONSE)}\n```')]
    claude_service._client.messages.create = AsyncMock(return_value=mock_resp)

    result = await claude_service.generate_furniture_queries(
      tone=SAMPLE_TONE,
      rooms=SAMPLE_ROOMS,
      slots_map=SAMPLE_SLOTS_MAP,
    )

    assert 'room-a' in result
    assert 'room-b' in result
    assert len(result['room-a']) == 4
    assert result['room-a'][0]['slot'] == '소파'
    assert '딥그린' in result['room-a'][0]['query']

  async def test_each_query_has_required_fields(self, claude_service):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=f'```json\n{json.dumps(MOCK_CLAUDE_RESPONSE)}\n```')]
    claude_service._client.messages.create = AsyncMock(return_value=mock_resp)

    result = await claude_service.generate_furniture_queries(
      tone=SAMPLE_TONE,
      rooms=SAMPLE_ROOMS,
      slots_map=SAMPLE_SLOTS_MAP,
    )

    for queries in result.values():
      for q in queries:
        assert 'slot' in q
        assert 'query' in q
        assert 'expected_colors' in q
        assert isinstance(q['expected_colors'], list)

  async def test_cache_hit_skips_claude_call(self, claude_service):
    from core.cache import furniture_query_cache

    cached_queries = [{'slot': '소파', 'query': '캐시된 소파', 'expected_colors': ['그린']}]
    furniture_query_cache['fq:tone-uuid-123:거실'] = cached_queries
    furniture_query_cache['fq:tone-uuid-123:안방'] = cached_queries

    result = await claude_service.generate_furniture_queries(
      tone=SAMPLE_TONE,
      rooms=SAMPLE_ROOMS,
      slots_map=SAMPLE_SLOTS_MAP,
    )

    # Claude API 호출 없어야 함
    claude_service._client.messages.create.assert_not_called()
    assert result['room-a'] == cached_queries
    assert result['room-b'] == cached_queries

  async def test_partial_cache_hit_calls_claude_once(self, claude_service):
    from core.cache import furniture_query_cache

    # 거실만 캐시, 안방은 미스
    furniture_query_cache['fq:tone-uuid-123:거실'] = [
      {'slot': '소파', 'query': '캐시된 소파', 'expected_colors': ['그린']}
    ]

    mock_resp = MagicMock()
    partial_response = {
      'rooms': [{'room_id': 'room-b', 'queries': MOCK_CLAUDE_RESPONSE['rooms'][1]['queries']}]
    }
    mock_resp.content = [MagicMock(text=f'```json\n{json.dumps(partial_response)}\n```')]
    claude_service._client.messages.create = AsyncMock(return_value=mock_resp)

    result = await claude_service.generate_furniture_queries(
      tone=SAMPLE_TONE,
      rooms=SAMPLE_ROOMS,
      slots_map=SAMPLE_SLOTS_MAP,
    )

    # Claude는 1회만 호출됨 (안방만)
    claude_service._client.messages.create.assert_called_once()
    assert 'room-a' in result  # 캐시에서
    assert 'room-b' in result  # Claude에서


# ---------------------------------------------------------------------------
# filter_products_by_expected_colors 테스트
# ---------------------------------------------------------------------------

class TestFilterProductsByExpectedColors:
  def _make_products(self, names: list[str]) -> list[dict]:
    return [
      {'name': name, 'slot': '소파', 'price_min': 100000, 'image_url': None, 'purchase_url': None}
      for name in names
    ]

  def test_matching_products_come_first(self):
    from services.product_filter import filter_products_by_expected_colors

    products = self._make_products([
      '베이지 패브릭 소파',
      '딥그린 벨벳 소파 4인용',
      '자주색 보조의자',
      '그린 모던 소파',
    ])
    result = filter_products_by_expected_colors(products, ['딥그린', '그린', '벨벳'], limit=2)

    assert len(result) == 2
    # 딥그린이 포함된 항목이 우선
    assert any('그린' in p['name'] or '벨벳' in p['name'] for p in result)

  def test_fallback_when_no_color_match(self):
    from services.product_filter import filter_products_by_expected_colors

    products = self._make_products(['베이지 소파', '흰색 소파'])
    result = filter_products_by_expected_colors(products, ['딥그린', '그린'], limit=2)

    # 매칭 없어도 상위 limit개를 반환
    assert len(result) == 2

  def test_empty_products_returns_empty(self):
    from services.product_filter import filter_products_by_expected_colors

    result = filter_products_by_expected_colors([], ['그린'], limit=2)
    assert result == []

  def test_limit_respected(self):
    from services.product_filter import filter_products_by_expected_colors

    products = self._make_products([f'그린 소파 {i}' for i in range(10)])
    result = filter_products_by_expected_colors(products, ['그린'], limit=3)
    assert len(result) == 3

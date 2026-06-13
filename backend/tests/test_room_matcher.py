"""core/room_matcher.py 유닛 테스트."""
from core.room_matcher import lookup_room_key

KEY_MAP = {
  '거실': 'L',
  '침실': 'B',
  '욕실': 'BA',
  '주방': 'K',
}


class TestLookupRoomKey:
  def test_exact_match(self):
    assert lookup_room_key('거실', KEY_MAP) == '거실'
    assert lookup_room_key('욕실', KEY_MAP) == '욕실'

  def test_endswith_match(self):
    # 부부욕실 → 욕실, 가족욕실 → 욕실
    assert lookup_room_key('부부욕실', KEY_MAP) == '욕실'
    assert lookup_room_key('가족욕실', KEY_MAP) == '욕실'

  def test_startswith_match(self):
    # 침실2 → 침실 (endswith 불일치 후 startswith로 매칭)
    assert lookup_room_key('침실2', KEY_MAP) == '침실'
    assert lookup_room_key('침실3', KEY_MAP) == '침실'

  def test_endswith_priority_over_startswith(self):
    # endswith가 startswith보다 먼저 평가된다
    key_map = {'방': 1, '안방': 2}
    assert lookup_room_key('드레스방', key_map) == '방'

  def test_no_match_returns_none(self):
    assert lookup_room_key('창고', KEY_MAP) is None
    assert lookup_room_key('', KEY_MAP) is None

  def test_empty_key_map(self):
    assert lookup_room_key('거실', {}) is None

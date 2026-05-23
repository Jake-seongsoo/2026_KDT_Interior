"""analyze 라우터 단위 테스트."""
import uuid
import pytest

from routers.analyze import _to_analyze_response

SESS = str(uuid.uuid4())
R1 = str(uuid.uuid4())
R2 = str(uuid.uuid4())
T1 = str(uuid.uuid4())


# ── _to_analyze_response 변환 테스트 ─────────────────────────────────────────

class TestToAnalyzeResponse:
  def _rooms(self):
    return [
      {'id': R1, 'room_type': '거실', 'confidence': 0.9, 'priority': 1, 'area_sqm': 25.0},
      {'id': R2, 'room_type': '침실', 'confidence': 0.8, 'priority': 2, 'area_sqm': None},
    ]

  def _tones(self):
    return [
      {
        'id': T1,
        'tone_index': 1,
        'name': '자연 속 고요',
        'category': 'natural',
        'description': '설명',
        'reason': '이유',
        'color_palette': [{'name': 'Primary', 'hex': '#A0785A', 'role': 'main'}],
        'keywords': ['자연', '편안함'],
      }
    ]

  def test_rooms_are_mapped_correctly(self):
    res = _to_analyze_response(SESS, self._rooms(), self._tones())
    assert len(res.rooms) == 2
    assert str(res.rooms[0].id) == R1
    assert res.rooms[0].room_type == '거실'
    assert res.rooms[0].area_sqm == 25.0
    assert res.rooms[1].area_sqm is None

  def test_tones_are_mapped_correctly(self):
    res = _to_analyze_response(SESS, self._rooms(), self._tones())
    assert len(res.tone_candidates) == 1
    tone = res.tone_candidates[0]
    assert str(tone.id) == T1
    assert tone.name == '자연 속 고요'
    assert tone.keywords == ['자연', '편안함']

  def test_warnings_default_to_empty_list(self):
    res = _to_analyze_response(SESS, self._rooms(), self._tones())
    assert res.warnings == []

  def test_warnings_are_passed_through(self):
    res = _to_analyze_response(SESS, self._rooms(), self._tones(), warnings=['경고1'])
    assert res.warnings == ['경고1']

  def test_missing_optional_room_fields_use_defaults(self):
    rooms = [{'id': str(uuid.uuid4()), 'room_type': '욕실'}]
    res = _to_analyze_response(SESS, rooms, [])
    assert res.rooms[0].confidence == 0.5
    assert res.rooms[0].priority == 0

  def test_tone_index_auto_assigned_when_missing(self):
    tones = [
      {'id': str(uuid.uuid4()), 'name': '톤A'},
      {'id': str(uuid.uuid4()), 'name': '톤B'},
    ]
    res = _to_analyze_response(SESS, [], tones)
    assert res.tone_candidates[0].tone_index == 1
    assert res.tone_candidates[1].tone_index == 2

  def test_session_id_is_set(self):
    sess = str(uuid.uuid4())
    res = _to_analyze_response(sess, [], [])
    assert str(res.session_id) == sess

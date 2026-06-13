"""SupabaseService 기록 조회 메서드 유닛 테스트 (F011 단계 1).

실제 Supabase 연결 없이, 쿼리 빌더 체인을 self-returning MagicMock으로 대체해
각 메서드가 올바른 테이블·필터·정렬을 호출하고 .data를 반환하는지 검증한다.
(pytest-asyncio asyncio_mode=auto — async def 테스트가 자동 실행됨)
"""
from unittest.mock import MagicMock, patch

from services.supabase_service import SupabaseService


def _make_service(return_data):
  """_db가 mock인 SupabaseService를 만든다. 모든 쿼리 체인은 같은 mock을 반환하고
  마지막 execute().data가 return_data가 된다."""
  query = MagicMock()
  for method in ('select', 'eq', 'in_', 'order', 'limit'):
    getattr(query, method).return_value = query
  query.execute.return_value.data = return_data

  db = MagicMock()
  db.table.return_value = query

  with patch('services.supabase_service._get_client', return_value=db):
    svc = SupabaseService()
  return svc, db, query


class TestGetSessionsByUser:
  async def test_returns_data_and_queries_correct_table(self):
    rows = [{'id': 's1', 'user_id': 'u1'}, {'id': 's2', 'user_id': 'u1'}]
    svc, db, query = _make_service(rows)

    result = await svc.get_sessions_by_user('u1')

    assert result == rows
    db.table.assert_called_with('analysis_sessions')
    query.eq.assert_called_with('user_id', 'u1')
    query.order.assert_called_with('created_at', desc=True)
    query.limit.assert_called_with(20)

  async def test_custom_limit(self):
    svc, db, query = _make_service([])
    await svc.get_sessions_by_user('u1', limit=5)
    query.limit.assert_called_with(5)


class TestGetRoomsBySessions:
  async def test_empty_input_returns_empty_without_query(self):
    svc, db, query = _make_service([{'should': 'not appear'}])
    result = await svc.get_rooms_by_sessions([])
    assert result == []
    db.table.assert_not_called()

  async def test_queries_in_filter(self):
    rows = [{'session_id': 's1', 'room_type': '거실', 'priority': 1}]
    svc, db, query = _make_service(rows)

    result = await svc.get_rooms_by_sessions(['s1', 's2'])

    assert result == rows
    db.table.assert_called_with('rooms')
    query.in_.assert_called_with('session_id', ['s1', 's2'])


class TestGetResultsBySessions:
  async def test_empty_input_returns_empty(self):
    svc, db, query = _make_service([{'x': 1}])
    assert await svc.get_results_by_sessions([]) == []
    db.table.assert_not_called()

  async def test_queries_results_recent_first(self):
    rows = [{'id': 'r1', 'session_id': 's1', 'selected_tone_id': 't1', 'created_at': 'x'}]
    svc, db, query = _make_service(rows)

    result = await svc.get_results_by_sessions(['s1'])

    assert result == rows
    db.table.assert_called_with('recommendation_results')
    query.in_.assert_called_with('session_id', ['s1'])
    query.order.assert_called_with('created_at', desc=True)


class TestGetTonesByIds:
  async def test_empty_input_returns_empty(self):
    svc, db, query = _make_service([{'x': 1}])
    assert await svc.get_tones_by_ids([]) == []
    db.table.assert_not_called()

  async def test_queries_id_name(self):
    rows = [{'id': 't1', 'name': '호텔라이크'}]
    svc, db, query = _make_service(rows)

    result = await svc.get_tones_by_ids(['t1', 't2'])

    assert result == rows
    db.table.assert_called_with('tone_candidates')
    query.in_.assert_called_with('id', ['t1', 't2'])

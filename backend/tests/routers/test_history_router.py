"""history 라우터 테스트 (F011 단계 2)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from core.auth import AuthUser, verify_jwt
from main import app
from routers.history import _room_summary

TEST_USER = AuthUser(user_id='user-1', email='t@e.com')


# ── _room_summary 순수 함수 ────────────────────────────────────────────────

class TestRoomSummary:
  def test_joins_room_types_in_order(self):
    rooms = [{'room_type': '거실'}, {'room_type': '주방'}, {'room_type': '안방'}]
    assert _room_summary(rooms) == '거실·주방·안방'

  def test_deduplicates_preserving_order(self):
    rooms = [{'room_type': '침실'}, {'room_type': '침실'}, {'room_type': '거실'}]
    assert _room_summary(rooms) == '침실·거실'

  def test_empty_returns_placeholder(self):
    assert _room_summary([]) == '방 정보 없음'
    assert _room_summary([{'room_type': ''}, {}]) == '방 정보 없음'


# ── GET /history 엔드포인트 ─────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
  """verify_jwt를 우회하고 Supabase·Storage를 mock한 TestClient."""
  fake_db = MagicMock()
  fake_storage = MagicMock()
  monkeypatch.setattr('routers.history.SupabaseService', lambda: fake_db)
  monkeypatch.setattr('routers.history.StorageService', lambda: fake_storage)
  app.dependency_overrides[verify_jwt] = lambda: TEST_USER

  c = TestClient(app)
  c.fake_db = fake_db
  c.fake_storage = fake_storage
  yield c

  app.dependency_overrides.clear()


SID = '11111111-1111-1111-1111-111111111111'
RID = '22222222-2222-2222-2222-222222222222'
TID = '33333333-3333-3333-3333-333333333333'


class TestGetHistory:
  def test_empty_sessions_returns_empty_list(self, client):
    client.fake_db.get_sessions_by_user = AsyncMock(return_value=[])

    resp = client.get('/history')

    assert resp.status_code == 200
    assert resp.json() == {'sessions': []}

  def test_full_nesting_with_thumbnail(self, client):
    client.fake_db.get_sessions_by_user = AsyncMock(return_value=[{
      'id': SID, 'created_at': '2026-06-13T00:00:00+00:00',
      'floor_area_pyeong': 32.0, 'status': 'completed', 'gcs_path': 'floor-plans/u/s/o.jpg',
    }])
    client.fake_db.get_rooms_by_sessions = AsyncMock(return_value=[
      {'session_id': SID, 'room_type': '거실', 'priority': 1},
      {'session_id': SID, 'room_type': '주방', 'priority': 2},
    ])
    client.fake_db.get_results_by_sessions = AsyncMock(return_value=[
      {'id': RID, 'session_id': SID, 'selected_tone_id': TID, 'created_at': '2026-06-13T01:00:00+00:00'},
    ])
    client.fake_db.get_tones_by_ids = AsyncMock(return_value=[{'id': TID, 'name': '호텔라이크'}])
    client.fake_storage.signed_url_for_floorplan = MagicMock(return_value='https://signed/url')

    resp = client.get('/history')

    assert resp.status_code == 200
    data = resp.json()
    assert len(data['sessions']) == 1
    s = data['sessions'][0]
    assert s['session_id'] == SID
    assert s['room_summary'] == '거실·주방'
    assert s['thumbnail_url'] == 'https://signed/url'
    assert len(s['results']) == 1
    assert s['results'][0]['tone_name'] == '호텔라이크'
    assert s['results'][0]['result_id'] == RID

  def test_no_gcs_path_yields_null_thumbnail(self, client):
    client.fake_db.get_sessions_by_user = AsyncMock(return_value=[{
      'id': SID, 'created_at': '2026-06-13T00:00:00+00:00',
      'floor_area_pyeong': 24.0, 'status': 'analyzing', 'gcs_path': None,
    }])
    client.fake_db.get_rooms_by_sessions = AsyncMock(return_value=[])
    client.fake_db.get_results_by_sessions = AsyncMock(return_value=[])
    client.fake_db.get_tones_by_ids = AsyncMock(return_value=[])

    resp = client.get('/history')

    assert resp.status_code == 200
    s = resp.json()['sessions'][0]
    assert s['thumbnail_url'] is None
    assert s['room_summary'] == '방 정보 없음'
    assert s['results'] == []
    # gcs_path 없으면 Signed URL 발급을 시도하지 않는다
    client.fake_storage.signed_url_for_floorplan.assert_not_called()

  def test_thumbnail_failure_degrades_to_null(self, client):
    client.fake_db.get_sessions_by_user = AsyncMock(return_value=[{
      'id': SID, 'created_at': '2026-06-13T00:00:00+00:00',
      'floor_area_pyeong': 24.0, 'status': 'completed', 'gcs_path': 'floor-plans/u/s/o.jpg',
    }])
    client.fake_db.get_rooms_by_sessions = AsyncMock(return_value=[])
    client.fake_db.get_results_by_sessions = AsyncMock(return_value=[])
    client.fake_db.get_tones_by_ids = AsyncMock(return_value=[])
    client.fake_storage.signed_url_for_floorplan = MagicMock(side_effect=RuntimeError('GCS down'))

    resp = client.get('/history')

    assert resp.status_code == 200
    assert resp.json()['sessions'][0]['thumbnail_url'] is None

  def test_requires_auth(self, monkeypatch):
    # dependency_override 없이 호출하면 401
    monkeypatch.setattr('routers.history.SupabaseService', lambda: MagicMock())
    monkeypatch.setattr('routers.history.StorageService', lambda: MagicMock())
    resp = TestClient(app).get('/history')
    assert resp.status_code == 401

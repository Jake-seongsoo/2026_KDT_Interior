"""share 라우터 테스트 (F008 단계 2)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from core.auth import AuthUser, verify_jwt
from main import app
from models.schemas import RenderResponse, ToneCandidateOut

TEST_USER = AuthUser(user_id='user-1', email='t@e.com')

RESULT_ID = '11111111-1111-1111-1111-111111111111'
SHARE_ID = '22222222-2222-2222-2222-222222222222'
TONE_ID = '33333333-3333-3333-3333-333333333333'


def _fake_render_response() -> RenderResponse:
  return RenderResponse(
    result_id=RESULT_ID,
    selected_tone=ToneCandidateOut(
      id=TONE_ID, tone_index=1, name='호텔라이크', category='luxury',
      description='설명', reason='이유', color_palette=[], keywords=[],
    ),
    svg_layout='<svg/>',
    room_results=[],
    processing_ms=1000,
  )


@pytest.fixture
def db():
  """routers.share.SupabaseService·StorageService·_assemble_render_response를 mock한다."""
  fake_db = MagicMock()
  fake_storage = MagicMock()
  return fake_db, fake_storage


@pytest.fixture
def authed_client(monkeypatch, db):
  fake_db, fake_storage = db
  monkeypatch.setattr('routers.share.SupabaseService', lambda: fake_db)
  monkeypatch.setattr('routers.share.StorageService', lambda: fake_storage)
  app.dependency_overrides[verify_jwt] = lambda: TEST_USER
  c = TestClient(app)
  c.fake_db = fake_db
  yield c
  app.dependency_overrides.clear()


# ── POST /share (로그인 + 소유권) ──────────────────────────────────────────

class TestCreateShare:
  def test_owner_creates_share(self, authed_client):
    authed_client.fake_db.get_result = AsyncMock(return_value={'id': RESULT_ID, 'session_id': 's1', 'user_id': 'user-1'})
    authed_client.fake_db.get_session = AsyncMock(return_value={'id': 's1', 'user_id': 'user-1'})
    authed_client.fake_db.create_share_link = AsyncMock(return_value={'id': SHARE_ID, 'result_id': RESULT_ID})

    resp = authed_client.post('/share', json={'result_id': RESULT_ID})

    assert resp.status_code == 200
    assert resp.json()['share_id'] == SHARE_ID

  def test_non_owner_forbidden(self, authed_client):
    authed_client.fake_db.get_result = AsyncMock(return_value={'id': RESULT_ID, 'session_id': 's1', 'user_id': 'other'})
    authed_client.fake_db.get_session = AsyncMock(return_value={'id': 's1', 'user_id': 'other'})
    authed_client.fake_db.create_share_link = AsyncMock()

    resp = authed_client.post('/share', json={'result_id': RESULT_ID})

    assert resp.status_code == 403
    authed_client.fake_db.create_share_link.assert_not_called()

  def test_missing_result_404(self, authed_client):
    authed_client.fake_db.get_result = AsyncMock(side_effect=ValueError('결과를 찾을 수 없습니다'))

    resp = authed_client.post('/share', json={'result_id': RESULT_ID})

    assert resp.status_code == 404

  def test_requires_auth(self, monkeypatch, db):
    fake_db, fake_storage = db
    monkeypatch.setattr('routers.share.SupabaseService', lambda: fake_db)
    monkeypatch.setattr('routers.share.StorageService', lambda: fake_storage)
    resp = TestClient(app).post('/share', json={'result_id': RESULT_ID})
    assert resp.status_code == 401


# ── GET /share/{id} (비로그인) ─────────────────────────────────────────────

class TestGetSharedResult:
  def test_public_access_excludes_products_and_increments_view(self, monkeypatch, db):
    fake_db, fake_storage = db
    fake_db.get_share_link = AsyncMock(return_value={'id': SHARE_ID, 'result_id': RESULT_ID, 'view_count': 7})
    fake_db.get_result = AsyncMock(return_value={'id': RESULT_ID, 'session_id': 's1'})
    fake_db.increment_share_view = AsyncMock()
    monkeypatch.setattr('routers.share.SupabaseService', lambda: fake_db)
    monkeypatch.setattr('routers.share.StorageService', lambda: fake_storage)
    assemble = AsyncMock(return_value=_fake_render_response())
    monkeypatch.setattr('routers.share._assemble_render_response', assemble)

    # 비로그인 — dependency_overrides 없이 호출
    resp = TestClient(app).get(f'/share/{SHARE_ID}')

    assert resp.status_code == 200
    assert resp.json()['selected_tone']['name'] == '호텔라이크'
    # 조회수 증가 (7 → 현재값 전달)
    fake_db.increment_share_view.assert_awaited_once_with(SHARE_ID, 7)
    # 상품 제외로 조립 호출
    assert assemble.await_args.kwargs.get('include_products') is False

  def test_unknown_share_404(self, monkeypatch, db):
    fake_db, fake_storage = db
    fake_db.get_share_link = AsyncMock(side_effect=ValueError('공유 링크를 찾을 수 없습니다'))
    monkeypatch.setattr('routers.share.SupabaseService', lambda: fake_db)
    monkeypatch.setattr('routers.share.StorageService', lambda: fake_storage)

    resp = TestClient(app).get(f'/share/{SHARE_ID}')

    assert resp.status_code == 404

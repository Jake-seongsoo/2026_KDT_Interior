"""render 라우터 단위 테스트."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from routers.render import (
  _build_product_query,
  _room_slug,
  _to_tone_out,
  _upload_render_image,
  _verify_session_and_tone,
)


# ── _room_slug 테스트 ──────────────────────────────────────────────────────

class TestRoomSlug:
  def test_known_room_types(self):
    assert _room_slug('거실') == 'livingroom'
    assert _room_slug('안방') == 'master_bedroom'
    assert _room_slug('욕실') == 'bathroom'
    assert _room_slug('발코니') == 'balcony'

  def test_numbered_room(self):
    assert _room_slug('침실2') == 'bedroom2'
    assert _room_slug('침실3') == 'bedroom3'

  def test_unknown_room_returns_room(self):
    assert _room_slug('창고') == 'room'
    assert _room_slug('') == 'room'


# ── _build_product_query 테스트 ────────────────────────────────────────────

class TestBuildProductQuery:
  def test_query_includes_furniture_and_style(self):
    room = {'room_type': '거실'}
    tone = {'keywords': ['모던'], 'name': '딥그린 모던'}
    query = _build_product_query(room, tone)
    assert '소파' in query
    assert '모던' in query

  def test_fallback_to_tone_name_when_no_keywords(self):
    room = {'room_type': '주방'}
    tone = {'keywords': [], 'name': '재팬디'}
    query = _build_product_query(room, tone)
    assert '재팬디' in query
    assert '식탁' in query

  def test_numbered_room_matches_prefix(self):
    room = {'room_type': '침실2'}
    tone = {'keywords': ['내추럴'], 'name': ''}
    query = _build_product_query(room, tone)
    assert '침대' in query

  def test_unknown_room_uses_default_furniture(self):
    room = {'room_type': '창고'}
    tone = {'keywords': ['미니멀'], 'name': ''}
    query = _build_product_query(room, tone)
    assert '가구' in query


# ── _to_tone_out 테스트 ────────────────────────────────────────────────────

TONE_UUID = str(uuid.uuid4())
TONE_UUID2 = str(uuid.uuid4())


class TestToToneOut:
  def test_all_fields_mapped(self):
    tone = {
      'id': TONE_UUID,
      'tone_index': 3,
      'name': '모카무스 럭셔리',
      'category': 'luxury',
      'description': '설명',
      'reason': '이유',
      'color_palette': [{'name': 'Mocha', 'hex': '#A0785A', 'role': 'main'}],
      'keywords': ['고급', '차분'],
    }
    out = _to_tone_out(tone)
    assert str(out.id) == TONE_UUID
    assert out.tone_index == 3
    assert out.name == '모카무스 럭셔리'
    assert out.keywords == ['고급', '차분']

  def test_missing_optional_fields_use_defaults(self):
    tone = {'id': TONE_UUID2, 'name': '톤명'}
    out = _to_tone_out(tone)
    assert out.tone_index == 1
    assert out.category == ''
    assert out.color_palette == []
    assert out.keywords == []


# ── _upload_render_image 테스트 ────────────────────────────────────────────

class TestUploadRenderImage:
  def _storage(self):
    storage = MagicMock()
    storage.upload_render.return_value = 'renders/result-1/livingroom.png'
    storage.public_url_for_render.return_value = 'https://storage.googleapis.com/bucket/renders/result-1/livingroom.png'
    return storage

  @pytest.mark.asyncio
  async def test_success_returns_url_and_path(self):
    room = {'room_type': '거실'}
    img_bytes = b'fake-image'
    storage = self._storage()

    with patch('routers.render.asyncio.to_thread', new=AsyncMock(return_value='renders/result-1/livingroom.png')):
      render_url, gcs_path, rationale = await _upload_render_image(
        img_bytes, room, 0, '거실 연출 설명', 'result-1', storage
      )

    assert render_url is not None
    assert gcs_path == 'renders/result-1/livingroom.png'
    assert rationale == '거실 연출 설명'

  @pytest.mark.asyncio
  async def test_exception_returns_none_url_and_error_rationale(self):
    room = {'room_type': '침실'}
    error = Exception('Imagen 타임아웃')
    storage = self._storage()

    render_url, gcs_path, rationale = await _upload_render_image(
      error, room, 0, '원래 설명', 'result-1', storage
    )

    assert render_url is None
    assert gcs_path == ''
    assert '침실' in rationale
    assert '실패' in rationale

  @pytest.mark.asyncio
  async def test_second_room_of_same_type_gets_index_suffix(self):
    room = {'room_type': '침실'}
    img_bytes = b'fake'
    storage = self._storage()

    with patch('routers.render.asyncio.to_thread', new=AsyncMock(return_value='renders/r1/bedroom_1.png')):
      _, gcs_path, _ = await _upload_render_image(
        img_bytes, room, 1, '설명', 'r1', storage
      )

    assert gcs_path == 'renders/r1/bedroom_1.png'


# ── _verify_session_and_tone 테스트 ───────────────────────────────────────

SESSION_ID = str(uuid.uuid4())
TONE_ID = str(uuid.uuid4())
USER_ID = 'user-abc'


def _make_body(session_id=SESSION_ID, tone_id=TONE_ID):
  body = MagicMock()
  body.session_id = session_id
  body.selected_tone_id = tone_id
  return body


def _make_user(user_id=USER_ID):
  user = MagicMock()
  user.user_id = user_id
  return user


def _make_db(session=None, rooms=None, tone=None, session_error=False, tone_error=False):
  db = AsyncMock()
  if session_error:
    db.get_session.side_effect = ValueError('세션 없음')
  else:
    db.get_session.return_value = session or {'id': SESSION_ID, 'user_id': USER_ID}
  db.get_render_target_rooms.return_value = rooms if rooms is not None else [
    {'id': 'room-1', 'room_type': '거실'}
  ]
  if tone_error:
    db.get_tone.side_effect = ValueError('톤 없음')
  else:
    db.get_tone.return_value = tone or {'id': TONE_ID, 'session_id': SESSION_ID}
  return db


class TestVerifySessionAndTone:
  @pytest.mark.asyncio
  async def test_success_returns_session_rooms_tone(self):
    db = _make_db()
    session, rooms, tone = await _verify_session_and_tone(db, _make_body(), _make_user())
    assert session['id'] == SESSION_ID
    assert len(rooms) == 1
    assert tone['id'] == TONE_ID

  @pytest.mark.asyncio
  async def test_session_not_found_raises_404(self):
    db = _make_db(session_error=True)
    with pytest.raises(HTTPException) as exc:
      await _verify_session_and_tone(db, _make_body(), _make_user())
    assert exc.value.status_code == 404

  @pytest.mark.asyncio
  async def test_wrong_user_raises_403(self):
    db = _make_db(session={'id': SESSION_ID, 'user_id': 'other-user'})
    with pytest.raises(HTTPException) as exc:
      await _verify_session_and_tone(db, _make_body(), _make_user())
    assert exc.value.status_code == 403

  @pytest.mark.asyncio
  async def test_no_rooms_raises_422(self):
    db = _make_db(rooms=[])
    with pytest.raises(HTTPException) as exc:
      await _verify_session_and_tone(db, _make_body(), _make_user())
    assert exc.value.status_code == 422

  @pytest.mark.asyncio
  async def test_tone_not_found_raises_404(self):
    db = _make_db(tone_error=True)
    with pytest.raises(HTTPException) as exc:
      await _verify_session_and_tone(db, _make_body(), _make_user())
    assert exc.value.status_code == 404

  @pytest.mark.asyncio
  async def test_tone_wrong_session_raises_400(self):
    db = _make_db(tone={'id': TONE_ID, 'session_id': 'other-session'})
    with pytest.raises(HTTPException) as exc:
      await _verify_session_and_tone(db, _make_body(), _make_user())
    assert exc.value.status_code == 400

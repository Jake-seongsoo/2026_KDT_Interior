"""SupabaseService 공유 링크 메서드 유닛 테스트 (F008 단계 1)."""
from unittest.mock import MagicMock, patch

import pytest

from services.supabase_service import SupabaseService


def _make_service():
  """_db가 self-returning mock인 SupabaseService를 만든다.
  각 테이블 호출의 execute().data는 테스트에서 개별 설정한다."""
  query = MagicMock()
  for method in ('select', 'eq', 'insert', 'update'):
    getattr(query, method).return_value = query

  db = MagicMock()
  db.table.return_value = query

  with patch('services.supabase_service._get_client', return_value=db):
    svc = SupabaseService()
  return svc, db, query


class TestCreateShareLink:
  async def test_returns_existing_when_present(self):
    svc, db, query = _make_service()
    existing = {'id': 'share-1', 'result_id': 'res-1', 'view_count': 3}
    query.execute.return_value.data = [existing]

    result = await svc.create_share_link('res-1')

    assert result == existing
    db.table.assert_called_with('share_links')
    query.eq.assert_called_with('result_id', 'res-1')
    query.insert.assert_not_called()  # 기존이 있으면 새로 만들지 않는다

  async def test_inserts_when_absent(self):
    svc, db, query = _make_service()
    # select는 빈 결과, insert는 새 행 반환 — 호출 순서대로 다른 data 반환
    query.execute.return_value.data = []

    inserted = {'id': 'new-share', 'result_id': 'res-2'}
    insert_query = MagicMock()
    insert_query.execute.return_value.data = [inserted]
    query.insert.return_value = insert_query

    result = await svc.create_share_link('res-2')

    assert result == inserted
    query.insert.assert_called_once()


class TestGetShareLink:
  async def test_returns_row(self):
    svc, db, query = _make_service()
    row = {'id': 'share-1', 'result_id': 'res-1', 'view_count': 0}
    query.execute.return_value.data = [row]

    result = await svc.get_share_link('share-1')

    assert result == row
    query.eq.assert_called_with('id', 'share-1')

  async def test_raises_when_missing(self):
    svc, db, query = _make_service()
    query.execute.return_value.data = []

    with pytest.raises(ValueError, match='공유 링크를 찾을 수 없습니다'):
      await svc.get_share_link('nope')


class TestIncrementShareView:
  async def test_updates_incremented_count(self):
    svc, db, query = _make_service()
    query.execute.return_value.data = []

    await svc.increment_share_view('share-1', current_count=4)

    query.update.assert_called_with({'view_count': 5})
    query.eq.assert_called_with('id', 'share-1')

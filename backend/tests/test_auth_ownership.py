"""core/auth.py ensure_owner 유닛 테스트."""
import pytest
from fastapi import HTTPException, status

from core.auth import AuthUser, ensure_owner

USER = AuthUser(user_id='user-1', email='a@b.com')


class TestEnsureOwner:
  def test_single_owned_record_passes(self):
    # 예외가 발생하지 않으면 통과
    ensure_owner(USER, {'user_id': 'user-1'})

  def test_multiple_owned_records_pass(self):
    ensure_owner(USER, {'user_id': 'user-1'}, {'user_id': 'user-1'})

  def test_foreign_record_raises_403(self):
    with pytest.raises(HTTPException) as exc:
      ensure_owner(USER, {'user_id': 'other'})
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

  def test_one_foreign_among_many_raises_403(self):
    # 결과 조회처럼 여러 레코드 중 하나라도 남의 것이면 차단
    with pytest.raises(HTTPException) as exc:
      ensure_owner(USER, {'user_id': 'user-1'}, {'user_id': 'other'})
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

  def test_missing_user_id_raises_403(self):
    with pytest.raises(HTTPException):
      ensure_owner(USER, {})

  def test_custom_detail_message(self):
    with pytest.raises(HTTPException) as exc:
      ensure_owner(USER, {'user_id': 'other'}, detail='이 결과에 접근할 권한이 없습니다.')
    assert exc.value.detail == '이 결과에 접근할 권한이 없습니다.'

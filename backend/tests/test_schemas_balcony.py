"""RoomOut 발코니 필드 직렬화·기본값 유닛 테스트"""
import pytest
from uuid import uuid4

from models.schemas import RoomOut


def _base_data(**kwargs) -> dict:
  return {
    'id': uuid4(),
    'room_type': '거실',
    'confidence': 0.9,
    'priority': 1,
    **kwargs,
  }


def test_default_values() -> None:
  """새 필드 기본값: has_adjoining_balcony=False, balcony_expanded=None."""
  room = RoomOut(**_base_data())
  assert room.has_adjoining_balcony is False
  assert room.balcony_expanded is None


def test_explicit_values() -> None:
  """명시 값이 올바르게 저장된다."""
  room = RoomOut(**_base_data(has_adjoining_balcony=True, balcony_expanded=False))
  assert room.has_adjoining_balcony is True
  assert room.balcony_expanded is False


def test_expanded_true() -> None:
  """확장형(true) 값 처리."""
  room = RoomOut(**_base_data(has_adjoining_balcony=True, balcony_expanded=True))
  assert room.balcony_expanded is True


def test_serialization_includes_fields() -> None:
  """JSON 직렬화 결과에 두 필드가 포함된다."""
  room = RoomOut(**_base_data(has_adjoining_balcony=True, balcony_expanded=False))
  data = room.model_dump()
  assert 'has_adjoining_balcony' in data
  assert 'balcony_expanded' in data
  assert data['has_adjoining_balcony'] is True
  assert data['balcony_expanded'] is False

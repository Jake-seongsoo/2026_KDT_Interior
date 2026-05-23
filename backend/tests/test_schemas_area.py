from uuid import uuid4

from models.schemas import RoomResultOut


def test_room_result_out_with_area_sqm():
  room = RoomResultOut(
    room_id=uuid4(),
    room_type='안방',
    area_sqm=16.5,
    rationale='테스트 근거',
  )
  assert room.area_sqm == 16.5


def test_room_result_out_area_sqm_defaults_to_none():
  room = RoomResultOut(
    room_id=uuid4(),
    room_type='침실2',
    rationale='테스트 근거',
  )
  assert room.area_sqm is None


def test_room_result_out_area_sqm_serializes():
  room = RoomResultOut(
    room_id=uuid4(),
    room_type='거실',
    area_sqm=24.0,
    rationale='근거',
  )
  data = room.model_dump()
  assert data['area_sqm'] == 24.0
  assert data['room_type'] == '거실'

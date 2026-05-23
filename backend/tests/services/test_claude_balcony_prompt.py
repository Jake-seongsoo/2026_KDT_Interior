"""build_imagen_prompt 발코니 경계 단서 유닛 테스트"""
import pytest

from services.claude_service import ClaudeService

_TONE = {
  'name': '호텔라이크',
  'description': '차분한 뉴트럴 팔레트',
  'reason': '거실과 안방이 분리된 구조',
  'keywords': ['호텔라이크', '뉴트럴', '소파'],
  'color_palette': [
    {'name': '웜 화이트', 'hex': '#F7F3EA', 'role': '벽·천장'},
    {'name': '딥 그레이', 'hex': '#4A4A4A', 'role': '가구'},
  ],
}


@pytest.fixture
def svc() -> ClaudeService:
  return ClaudeService.__new__(ClaudeService)


def test_no_adjoining_balcony(svc: ClaudeService) -> None:
  """발코니 비인접 방 — 경계 단서 없음."""
  room = {'room_type': '거실', 'has_adjoining_balcony': False}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'balcony' not in prompt.lower() or 'no exterior balcony tiles' in prompt


def test_adjoining_balcony_not_expanded(svc: ClaudeService) -> None:
  """발코니 인접 + 비확장 — sliding door 단서 포함."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': False}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'balcony NOT part of room' in prompt
  assert 'sliding glass door' in prompt


def test_adjoining_balcony_expanded(svc: ClaudeService) -> None:
  """발코니 인접 + 확장형 — 연속 바닥재 단서 포함."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': True}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'expanded balcony integrated' in prompt
  assert 'continuous flooring' in prompt


def test_adjoining_balcony_unknown_expansion(svc: ClaudeService) -> None:
  """발코니 인접 + 확장 여부 불명(None) — 경계 단서 없음(안전 처리)."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': None}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'balcony NOT part of room' not in prompt
  assert 'expanded balcony integrated' not in prompt


def test_negative_hint_living_room(svc: ClaudeService) -> None:
  """거실 negative hint에 발코니 타일 금지 단서 포함."""
  room = {'room_type': '거실', 'has_adjoining_balcony': False}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'no exterior balcony tiles inside room' in prompt


def test_negative_hint_bedroom_variant(svc: ClaudeService) -> None:
  """침실2처럼 startswith 매칭되는 방도 negative hint 적용."""
  room = {'room_type': '침실2', 'has_adjoining_balcony': False}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'no exterior balcony tiles inside room' in prompt


def test_negative_hint_master_bedroom(svc: ClaudeService) -> None:
  """안방에도 발코니 타일 금지 단서 적용."""
  room = {'room_type': '안방', 'has_adjoining_balcony': False}
  prompt = svc.build_imagen_prompt(room, _TONE)
  assert 'no exterior balcony tiles inside room' in prompt

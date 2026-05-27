"""build_imagen_prompt 발코니 경계 단서 유닛 테스트"""
import pytest


def test_no_adjoining_balcony(claude_service_sync, minimal_tone) -> None:
  """발코니 비인접 방 — 경계 단서 없음."""
  room = {'room_type': '거실', 'has_adjoining_balcony': False}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'balcony' not in prompt.lower() or 'no exterior balcony tiles' in prompt


def test_adjoining_balcony_not_expanded(claude_service_sync, minimal_tone) -> None:
  """발코니 인접 + 비확장 — 경계 단서 포함, 슬라이딩 도어 묘사 제외."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': False}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'balcony NOT part of room' in prompt
  assert 'sliding glass door' not in prompt


def test_adjoining_balcony_expanded(claude_service_sync, minimal_tone) -> None:
  """발코니 인접 + 확장형 — 연속 바닥재 단서 포함."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': True}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'expanded balcony integrated' in prompt
  assert 'continuous flooring' in prompt


def test_adjoining_balcony_unknown_expansion(claude_service_sync, minimal_tone) -> None:
  """발코니 인접 + 확장 여부 불명(None) — 경계 단서 없음(안전 처리)."""
  room = {'room_type': '거실', 'has_adjoining_balcony': True, 'balcony_expanded': None}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'balcony NOT part of room' not in prompt
  assert 'expanded balcony integrated' not in prompt


def test_negative_hint_living_room(claude_service_sync, minimal_tone) -> None:
  """거실 negative hint에 발코니 타일 금지 단서 포함."""
  room = {'room_type': '거실', 'has_adjoining_balcony': False}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'no exterior balcony tiles inside room' in prompt


def test_negative_hint_bedroom_variant(claude_service_sync, minimal_tone) -> None:
  """침실2처럼 startswith 매칭되는 방도 negative hint 적용."""
  room = {'room_type': '침실2', 'has_adjoining_balcony': False}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'no exterior balcony tiles inside room' in prompt


def test_negative_hint_master_bedroom(claude_service_sync, minimal_tone) -> None:
  """안방에도 발코니 타일 금지 단서 적용."""
  room = {'room_type': '안방', 'has_adjoining_balcony': False}
  prompt = claude_service_sync.build_imagen_prompt(room, minimal_tone)
  assert 'no exterior balcony tiles inside room' in prompt

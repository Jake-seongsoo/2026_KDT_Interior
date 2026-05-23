"""_build_size_hint 유닛 테스트 — 방 면적이 Imagen 프롬프트에 반영되는지 검증"""
import pytest
from unittest.mock import patch
from services.claude_service import ClaudeService


TONE = {
  'name': '내추럴 모던',
  'keywords': ['우드'],
  'color_palette': [{'name': 'ivory', 'hex': '#F5EFE5'}],
}


@pytest.fixture
def svc():
  with patch('services.claude_service.get_settings'):
    return ClaudeService()


class TestBuildSizeHint:
  def test_none_반환_빈문자열(self, svc):
    assert svc._build_size_hint(None) == ''

  def test_zero_반환_빈문자열(self, svc):
    assert svc._build_size_hint(0) == ''

  def test_very_compact_7sqm(self, svc):
    hint = svc._build_size_hint(7.0)
    assert 'very compact' in hint
    assert '7.0sqm' in hint

  def test_compact_10sqm(self, svc):
    hint = svc._build_size_hint(10.0)
    assert 'compact' in hint
    assert 'very compact' not in hint

  def test_standard_15sqm(self, svc):
    hint = svc._build_size_hint(15.0)
    assert 'standard-sized' in hint

  def test_large_25sqm(self, svc):
    hint = svc._build_size_hint(25.0)
    assert 'large' in hint

  def test_spacious_30sqm(self, svc):
    hint = svc._build_size_hint(30.0)
    assert 'spacious' in hint

  def test_hint_끝에_공백(self, svc):
    # 프롬프트에 이어 붙일 때 공백 포함 확인
    hint = svc._build_size_hint(13.5)
    assert hint.endswith(' ')


class TestBuildImagenPromptAreaSqm:
  def test_area_sqm_없으면_hint_없음(self, svc):
    room = {'room_type': '침실'}
    prompt = svc.build_imagen_prompt(room, TONE)
    assert 'sqm' not in prompt

  def test_area_sqm_프롬프트에_포함(self, svc):
    room = {'room_type': '침실', 'area_sqm': 13.5}
    prompt = svc.build_imagen_prompt(room, TONE)
    assert '13.5sqm' in prompt
    assert 'standard-sized' in prompt

  def test_거실_30sqm_spacious(self, svc):
    room = {'room_type': '거실', 'area_sqm': 30.0}
    prompt = svc.build_imagen_prompt(room, TONE)
    assert 'spacious' in prompt
    assert '30.0sqm' in prompt

  def test_침실2_compact(self, svc):
    room = {'room_type': '침실2', 'area_sqm': 9.5}
    prompt = svc.build_imagen_prompt(room, TONE)
    assert 'compact' in prompt
    assert '9.5sqm' in prompt

  def test_정밀화_있어도_size_hint_유지(self, svc):
    room = {'room_type': '침실', 'area_sqm': 13.5}
    refinement = {'family_type': 'family_with_kid', 'style_keywords': ['미니멀']}
    prompt = svc.build_imagen_prompt(room, TONE, refinement=refinement)
    assert '13.5sqm' in prompt
    assert 'standard-sized' in prompt
    assert 'child-safe' in prompt
    assert '미니멀' in prompt

  def test_정밀화_appliances_있어도_size_hint_유지(self, svc):
    room = {'room_type': '주방', 'area_sqm': 12.0}
    refinement = {'appliances': [{'name': '냉장고', 'room': '주방'}]}
    prompt = svc.build_imagen_prompt(room, TONE, refinement=refinement)
    assert '12.0sqm' in prompt
    assert 'standard-sized' in prompt
    assert 'refrigerator' in prompt

  def test_size_hint가_room_en_바로_앞에_위치(self, svc):
    room = {'room_type': '거실', 'area_sqm': 30.0}
    prompt = svc.build_imagen_prompt(room, TONE)
    assert 'spacious 30.0sqm living room' in prompt

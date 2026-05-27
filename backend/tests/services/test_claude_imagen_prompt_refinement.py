"""build_imagen_prompt 정밀화 파라미터 반영 테스트"""
import pytest

from services.claude_service import ClaudeService


class TestBuildImagenPromptRefinement:
  def test_refinement_없으면_기본_프롬프트(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone)
    assert 'living room' in prompt.lower() or 'Korean apartment' in prompt
    assert 'child-safe' not in prompt
    assert 'pet-friendly' not in prompt

  def test_family_with_kid_힌트_포함(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'family_type': 'family_with_kid'})
    assert 'child-safe' in prompt

  def test_family_with_pet_힌트_포함(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'family_type': 'family_with_pet'})
    assert 'pet-friendly' in prompt

  def test_couple_힌트_포함(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'family_type': 'couple'})
    assert 'romantic' in prompt or 'cozy' in prompt

  def test_style_keywords_반영(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'style_keywords': ['미니멀', '빈티지']})
    assert '미니멀' in prompt and '빈티지' in prompt

  def test_keep_appliances_True_반영(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'keep_appliances': True})
    assert 'retain existing appliances' in prompt

  def test_keep_appliances_False_미반영(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'keep_appliances': False})
    assert 'retain existing appliances' not in prompt

  def test_예산_낮을때_budget_friendly(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'budget_10k_won': 1000})
    assert 'budget-friendly' in prompt

  def test_예산_높을때_premium(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'budget_10k_won': 9000})
    assert 'premium' in prompt

  def test_중간_예산_힌트_없음(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'budget_10k_won': 4000})
    assert 'budget-friendly' not in prompt
    assert 'premium' not in prompt

  def test_refinement_None_전달(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement=None)
    assert 'child-safe' not in prompt

  def test_user_text_반영(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'user_text': '그린톤 포인트 벽'})
    assert '그린톤 포인트 벽' in prompt

  def test_user_text_공백_무시(self, claude_service_sync, room_living, minimal_tone):
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, refinement={'user_text': '   '})
    assert 'child-safe' not in prompt
    assert 'pet-friendly' not in prompt


class TestBuildRefinementHint:
  def test_빈_dict_힌트_없음(self):
    hint = ClaudeService._build_refinement_hint({})
    assert hint == ''

  def test_None_힌트_없음(self):
    hint = ClaudeService._build_refinement_hint(None)
    assert hint == ''

  def test_힌트_있으면_쉼표로_시작(self):
    hint = ClaudeService._build_refinement_hint({'family_type': 'couple'})
    assert hint.startswith(', ')

  def test_user_text_힌트_포함(self):
    hint = ClaudeService._build_refinement_hint({'user_text': '오픈 선반 원해요'})
    assert '오픈 선반 원해요' in hint

  def test_user_text_빈문자열_무시(self):
    hint = ClaudeService._build_refinement_hint({'user_text': ''})
    assert hint == ''

  def test_user_text_공백만_무시(self):
    hint = ClaudeService._build_refinement_hint({'user_text': '  \n  '})
    assert hint == ''

"""ClaudeService 레퍼런스 시그니처 프롬프트 블록 및 Imagen 프롬프트 단위 테스트."""
import pytest

from services.claude_service import ClaudeService


class TestFormatReferenceBlock:
  def test_None_입력_빈_문자열_반환(self):
    """reference_signature=None 이면 빈 문자열을 반환해야 한다."""
    result = ClaudeService._format_reference_block(None)
    assert result == ''

  def test_빈_dict_입력_빈_문자열_반환(self):
    """빈 dict는 Python에서 falsy이므로 빈 문자열을 반환해야 한다."""
    result = ClaudeService._format_reference_block({})
    assert result == ''

  def test_시그니처_블록에_색상_포함(self, reference_signature):
    """primary_hex 가 블록에 포함되어야 한다."""
    result = ClaudeService._format_reference_block(reference_signature)
    assert '#A0785A' in result

  def test_시그니처_블록에_재질_포함(self, reference_signature):
    """materials 가 블록에 포함되어야 한다."""
    result = ClaudeService._format_reference_block(reference_signature)
    assert '원목' in result

  def test_시그니처_블록에_스타일_토큰_포함(self, reference_signature):
    """style_tokens 가 블록에 포함되어야 한다."""
    result = ClaudeService._format_reference_block(reference_signature)
    assert '보태니컬' in result

  def test_시그니처_블록에_무드_포함(self, reference_signature):
    """mood 가 블록에 포함되어야 한다."""
    result = ClaudeService._format_reference_block(reference_signature)
    assert '따뜻하고 차분한' in result


class TestBuildImagenPromptWithReference:
  def test_reference_signature_있으면_스타일_힌트_포함(self, claude_service_sync, room_living, minimal_tone, reference_signature):
    """reference_signature가 주어지면 'inspired by reference style' 힌트가 포함되어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, reference_signature=reference_signature)
    assert 'inspired by reference style' in prompt

  def test_reference_signature_hex_색상_포함(self, claude_service_sync, room_living, minimal_tone, reference_signature):
    """reference_signature의 primary_hex가 프롬프트에 포함되어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, reference_signature=reference_signature)
    assert '#A0785A' in prompt

  def test_reference_signature_재질_영문_변환_포함(self, claude_service_sync, room_living, minimal_tone, reference_signature):
    """materials 한국어가 영문으로 변환되어 포함되어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, reference_signature=reference_signature)
    assert 'natural wood' in prompt
    assert 'linen' in prompt

  def test_reference_signature_None_힌트_미포함(self, claude_service_sync, room_living, minimal_tone):
    """reference_signature=None 이면 reference 힌트가 없어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, reference_signature=None)
    assert 'inspired by reference style' not in prompt

  def test_기본값_reference_힌트_미포함(self, claude_service_sync, room_living, minimal_tone):
    """reference_signature 파라미터 생략 시 reference 힌트가 없어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone)
    assert 'inspired by reference style' not in prompt

  def test_reference_signature_있어도_기본_프롬프트_요소_포함(self, claude_service_sync, room_living, minimal_tone, reference_signature):
    """reference_signature가 있어도 방 타입·톤 이름 등 기본 요소가 포함되어야 한다."""
    prompt = claude_service_sync.build_imagen_prompt(room_living, minimal_tone, reference_signature=reference_signature)
    assert 'living room' in prompt

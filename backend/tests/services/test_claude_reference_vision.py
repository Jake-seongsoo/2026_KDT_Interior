"""ClaudeService.analyze_reference_image 단위 테스트."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.claude_service import ClaudeService

SAMPLE_SIGNATURE = {
  'primary_hex': '#A0785A',
  'secondary_hex': '#D4C4B0',
  'accent_hex': '#3D6B5A',
  'materials': ['원목', '린넨'],
  'style_tokens': ['보태니컬', '스칸디나비안'],
  'lighting': '자연광',
  'mood': '따뜻하고 차분한',
}


def _make_text_block(text: str) -> SimpleNamespace:
  block = SimpleNamespace()
  block.text = text
  return block


def _make_response(payload: dict) -> MagicMock:
  resp = MagicMock()
  resp.content = [_make_text_block(f'```json\n{json.dumps(payload, ensure_ascii=False)}\n```')]
  return resp


def _make_svc() -> ClaudeService:
  with patch('services.claude_service.get_settings') as mock_settings:
    mock_settings.return_value = MagicMock(
      ANTHROPIC_API_KEY='test-key',
      CLAUDE_MODEL='claude-sonnet-4-6',
    )
    return ClaudeService()


@pytest.mark.asyncio
class TestAnalyzeReferenceImage:
  async def test_정상_응답_파싱(self):
    """시그니처 JSON이 올바르게 파싱되어야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(return_value=_make_response(SAMPLE_SIGNATURE))
      mock_anthropic.return_value = mock_client

      svc = _make_svc()
      result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is not None
    assert result['primary_hex'] == '#A0785A'
    assert '원목' in result['materials']
    assert result['mood'] == '따뜻하고 차분한'

  async def test_타임아웃_None_반환(self):
    """타임아웃 발생 시 None을 반환하고 예외를 전파하지 않아야 한다."""
    async def _slow(*args, **kwargs):
      await asyncio.sleep(10)

    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(side_effect=_slow)
      mock_anthropic.return_value = mock_client

      svc = _make_svc()
      result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg', timeout_s=0.1)

    assert result is None

  async def test_API_예외_None_반환(self):
    """API 호출 예외 시 None을 반환해야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(side_effect=Exception('API 오류'))
      mock_anthropic.return_value = mock_client

      svc = _make_svc()
      result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is None

  async def test_잘못된_JSON_None_반환(self):
    """JSON 파싱 실패 시 None을 반환해야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      resp = MagicMock()
      resp.content = [_make_text_block('JSON 아닌 텍스트')]
      mock_client.messages.create = AsyncMock(return_value=resp)
      mock_anthropic.return_value = mock_client

      svc = _make_svc()
      result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is None

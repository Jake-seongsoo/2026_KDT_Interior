"""ClaudeService.analyze_reference_image 단위 테스트."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
class TestAnalyzeReferenceImage:
  async def test_정상_응답_파싱(self, make_claude_service, make_claude_response, reference_signature):
    """시그니처 JSON이 올바르게 파싱되어야 한다."""
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=make_claude_response(reference_signature))
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is not None
    assert result['primary_hex'] == '#A0785A'
    assert '원목' in result['materials']
    assert result['mood'] == '따뜻하고 차분한'

  async def test_타임아웃_None_반환(self, make_claude_service):
    """타임아웃 발생 시 None을 반환하고 예외를 전파하지 않아야 한다."""
    async def _slow(*args, **kwargs):
      await asyncio.sleep(10)

    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=_slow)
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg', timeout_s=0.1)

    assert result is None

  async def test_API_예외_None_반환(self, make_claude_service):
    """API 호출 예외 시 None을 반환해야 한다."""
    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=Exception('API 오류'))
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is None

  async def test_잘못된_JSON_None_반환(self, make_claude_service):
    """JSON 파싱 실패 시 None을 반환해야 한다."""
    resp = MagicMock()
    resp.content = [SimpleNamespace(text='JSON 아닌 텍스트')]
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=resp)
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_reference_image(b'fake-image', 'image/jpeg')

    assert result is None

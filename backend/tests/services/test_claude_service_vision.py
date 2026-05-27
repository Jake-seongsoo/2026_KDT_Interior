"""ClaudeService.analyze_render_visuals 단위 테스트."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


SAMPLE_VISUAL_ATTRS = {
  '소파': {
    'primary_hex': '#5B7F6A',
    'secondary_hex': None,
    'materials': ['벨벳', '패브릭'],
    'structure': ['4인용', '라운드암'],
    'style_tokens': ['모던', '스칸디나비안'],
  },
  '조명': {
    'primary_hex': '#B5A080',
    'secondary_hex': '#2C2C2C',
    'materials': ['황동', '메탈'],
    'structure': ['펜던트', '구형'],
    'style_tokens': ['미드센추리', '빈티지'],
  },
}


@pytest.mark.asyncio
class TestAnalyzeRenderVisuals:
  async def test_정상_응답_파싱(self, make_claude_service, make_claude_response):
    """슬롯별 시각 속성 JSON이 올바르게 파싱되어야 한다."""
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=make_claude_response(SAMPLE_VISUAL_ATTRS))
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_render_visuals(
      image_bytes=b'fake-image',
      mime='image/jpeg',
      slots=['소파', '조명'],
    )

    assert result is not None
    assert '소파' in result
    assert result['소파']['primary_hex'] == '#5B7F6A'
    assert '벨벳' in result['소파']['materials']

  async def test_빈_응답_None_반환(self, make_claude_service):
    """빈 텍스트 응답 시 None을 반환하고 예외를 던지지 않아야 한다."""
    resp = MagicMock()
    resp.content = [SimpleNamespace(text='')]
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=resp)
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_render_visuals(
      image_bytes=b'fake-image',
      mime='image/jpeg',
      slots=['소파'],
    )

    assert result is None

  async def test_타임아웃_None_반환(self, make_claude_service):
    """타임아웃 발생 시 None을 반환하고 예외를 전파하지 않아야 한다."""
    async def _slow(*args, **kwargs):
      await asyncio.sleep(10)

    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=_slow)
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_render_visuals(
      image_bytes=b'fake-image',
      mime='image/jpeg',
      slots=['소파'],
      timeout_s=0.1,
    )

    assert result is None

  async def test_API_예외_None_반환(self, make_claude_service):
    """API 호출 예외 발생 시 None을 반환해야 한다."""
    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=Exception('API 오류'))
    svc = make_claude_service(mock_client=client)

    result = await svc.analyze_render_visuals(
      image_bytes=b'fake-image',
      mime='image/jpeg',
      slots=['소파'],
    )

    assert result is None

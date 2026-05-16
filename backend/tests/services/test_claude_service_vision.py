"""ClaudeService.analyze_render_visuals 단위 테스트."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.claude_service import ClaudeService


# Vision 분석 응답 예시 픽스처
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


def _make_text_block(text: str) -> SimpleNamespace:
  """Claude 응답 텍스트 블록 모의 객체를 생성한다."""
  block = SimpleNamespace()
  block.text = text
  return block


def _make_response(attrs: dict) -> MagicMock:
  """Claude Messages API 응답 모의 객체를 생성한다."""
  resp = MagicMock()
  resp.content = [_make_text_block(f'```json\n{json.dumps(attrs, ensure_ascii=False)}\n```')]
  return resp


@pytest.mark.asyncio
class TestAnalyzeRenderVisuals:
  async def test_정상_응답_파싱(self):
    """슬롯별 시각 속성 JSON이 올바르게 파싱되어야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(return_value=_make_response(SAMPLE_VISUAL_ATTRS))
      mock_anthropic.return_value = mock_client

      with patch('services.claude_service.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
          ANTHROPIC_API_KEY='test-key',
          CLAUDE_MODEL='claude-sonnet-4-6',
        )
        svc = ClaudeService()
        result = await svc.analyze_render_visuals(
          image_bytes=b'fake-image',
          mime='image/jpeg',
          slots=['소파', '조명'],
        )

    assert result is not None
    assert '소파' in result
    assert result['소파']['primary_hex'] == '#5B7F6A'
    assert '벨벳' in result['소파']['materials']

  async def test_빈_응답_None_반환(self):
    """빈 텍스트 응답 시 None을 반환하고 예외를 던지지 않아야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      resp = MagicMock()
      resp.content = [_make_text_block('')]  # 빈 응답
      mock_client.messages.create = AsyncMock(return_value=resp)
      mock_anthropic.return_value = mock_client

      with patch('services.claude_service.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
          ANTHROPIC_API_KEY='test-key',
          CLAUDE_MODEL='claude-sonnet-4-6',
        )
        svc = ClaudeService()
        result = await svc.analyze_render_visuals(
          image_bytes=b'fake-image',
          mime='image/jpeg',
          slots=['소파'],
        )

    assert result is None

  async def test_타임아웃_None_반환(self):
    """타임아웃 발생 시 None을 반환하고 예외를 전파하지 않아야 한다."""
    async def _slow(*args, **kwargs):
      await asyncio.sleep(10)  # 타임아웃보다 오래 대기

    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(side_effect=_slow)
      mock_anthropic.return_value = mock_client

      with patch('services.claude_service.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
          ANTHROPIC_API_KEY='test-key',
          CLAUDE_MODEL='claude-sonnet-4-6',
        )
        svc = ClaudeService()
        result = await svc.analyze_render_visuals(
          image_bytes=b'fake-image',
          mime='image/jpeg',
          slots=['소파'],
          timeout_s=0.1,  # 0.1초로 타임아웃 유발
        )

    assert result is None

  async def test_API_예외_None_반환(self):
    """API 호출 예외 발생 시 None을 반환해야 한다."""
    with patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
      mock_client = MagicMock()
      mock_client.messages.create = AsyncMock(side_effect=Exception('API 오류'))
      mock_anthropic.return_value = mock_client

      with patch('services.claude_service.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
          ANTHROPIC_API_KEY='test-key',
          CLAUDE_MODEL='claude-sonnet-4-6',
        )
        svc = ClaudeService()
        result = await svc.analyze_render_visuals(
          image_bytes=b'fake-image',
          mime='image/jpeg',
          slots=['소파'],
        )

    assert result is None

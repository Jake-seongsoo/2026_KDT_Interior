"""ImagenService.render_rooms_parallel 단위 테스트.

레퍼런스 분위기는 Claude Vision 시그니처를 텍스트 프롬프트로 반영하므로
모든 spec은 표준 generate 모델(render_room)만 사용한다.
"""
from unittest.mock import MagicMock, patch

import pytest

from services.imagen_service import ImagenService


def _make_svc() -> ImagenService:
  with patch('services.imagen_service.get_settings') as mock_settings, \
       patch('services.imagen_service.get_google_credentials'), \
       patch('services.imagen_service.genai.Client'):
    mock_settings.return_value = MagicMock(
      IMAGEN_MODEL='imagen-4.0-generate-001',
      IMAGEN_CAPABILITY_MODEL='imagen-3.0-capability-001',
      GCP_PROJECT_ID='test-project',
      GCP_REGION='asia-northeast3',
    )
    return ImagenService()


@pytest.mark.asyncio
class TestRenderRoomsParallel:
  async def test_단일_방_render_room_호출(self):
    """spec 1개 → render_room 1회 호출, 결과 반환."""
    svc = _make_svc()
    called = []

    async def _fake_render(prompt):
      called.append(prompt)
      return b'gen-bytes'

    svc.render_room = _fake_render  # type: ignore[method-assign]

    specs = [{'room_type': '거실', 'prompt': 'living room'}]
    results = await svc.render_rooms_parallel(specs)

    assert len(results) == 1
    assert results[0] == b'gen-bytes'
    assert called == ['living room']

  async def test_복수_방_병렬_처리(self):
    """spec 2개 → render_room 2회 호출, 각 결과 반환."""
    svc = _make_svc()
    called: list[str] = []

    async def _fake_render(prompt):
      called.append(prompt)
      return b'gen-bytes'

    svc.render_room = _fake_render  # type: ignore[method-assign]

    specs = [
      {'room_type': '거실', 'prompt': 'living room'},
      {'room_type': '침실', 'prompt': 'bedroom'},
    ]
    results = await svc.render_rooms_parallel(specs)

    assert len(results) == 2
    assert all(r == b'gen-bytes' for r in results)
    assert len(called) == 2

  async def test_실패한_방_Exception_반환(self):
    """한 방 렌더링 실패 시 해당 항목만 Exception이고 나머지는 정상이어야 한다."""
    svc = _make_svc()

    async def _fail(prompt):
      raise RuntimeError('Imagen 오류')

    svc.render_room = _fail  # type: ignore[method-assign]

    specs = [{'room_type': '거실', 'prompt': 'living room'}]
    results = await svc.render_rooms_parallel(specs)

    assert len(results) == 1
    assert isinstance(results[0], RuntimeError)

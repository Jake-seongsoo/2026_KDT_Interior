"""ImagenService.render_rooms_parallel 단위 테스트.

레퍼런스 분위기는 Claude Vision 시그니처를 텍스트 프롬프트로 반영하므로
모든 spec은 표준 generate 모델(render_room)만 사용한다.
"""
import pytest


@pytest.mark.asyncio
class TestRenderRoomsParallel:
  async def test_단일_방_render_room_호출(self, imagen_service):
    """spec 1개 → render_room 1회 호출, 결과 반환."""
    called = []

    async def _fake_render(prompt):
      called.append(prompt)
      return b'gen-bytes'

    imagen_service.render_room = _fake_render

    specs = [{'room_type': '거실', 'prompt': 'living room'}]
    results = await imagen_service.render_rooms_parallel(specs)

    assert len(results) == 1
    assert results[0] == b'gen-bytes'
    assert called == ['living room']

  async def test_복수_방_병렬_처리(self, imagen_service):
    """spec 2개 → render_room 2회 호출, 각 결과 반환."""
    called: list[str] = []

    async def _fake_render(prompt):
      called.append(prompt)
      return b'gen-bytes'

    imagen_service.render_room = _fake_render

    specs = [
      {'room_type': '거실', 'prompt': 'living room'},
      {'room_type': '침실', 'prompt': 'bedroom'},
    ]
    results = await imagen_service.render_rooms_parallel(specs)

    assert len(results) == 2
    assert all(r == b'gen-bytes' for r in results)
    assert len(called) == 2

  async def test_실패한_방_Exception_반환(self, imagen_service):
    """한 방 렌더링 실패 시 해당 항목만 Exception이고 나머지는 정상이어야 한다."""
    async def _fail(prompt):
      raise RuntimeError('Imagen 오류')

    imagen_service.render_room = _fail

    specs = [{'room_type': '거실', 'prompt': 'living room'}]
    results = await imagen_service.render_rooms_parallel(specs)

    assert len(results) == 1
    assert isinstance(results[0], RuntimeError)

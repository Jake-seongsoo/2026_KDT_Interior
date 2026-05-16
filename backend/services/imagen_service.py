# RISK-01: asyncio.gather(..., return_exceptions=True) 로 부분 실패 허용
import asyncio
import io
import logging

from google import genai
from google.genai import types
from PIL import Image as PILImage

from core.config import get_google_credentials, get_settings

logger = logging.getLogger(__name__)


def _to_jpeg_bytes(pil_img: PILImage.Image) -> bytes:
  """PIL 이미지를 JPEG bytes로 변환한다. (Phase 2에서 워터마크 추가 예정)"""
  buf = io.BytesIO()
  pil_img.save(buf, format='JPEG', quality=90)
  return buf.getvalue()


class ImagenService:
  def __init__(self) -> None:
    settings = get_settings()
    self._model = settings.IMAGEN_MODEL
    self._client = genai.Client(
      vertexai=True,
      project=settings.GCP_PROJECT_ID,
      location=settings.GCP_REGION,
      credentials=get_google_credentials(),
    )

  async def render_room(self, prompt: str) -> bytes:
    """방 1개 인테리어 렌더링 이미지를 생성한다."""
    # google-genai 이미지 생성 API는 동기 호출이라 이벤트 루프 밖에서 실행한다.
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
      None,
      lambda: self._client.models.generate_images(
        model=self._model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
          number_of_images=1,
          aspect_ratio='4:3',
          output_mime_type='image/jpeg',
          output_compression_quality=90,
        ),
      ),
    )
    generated_images = response.generated_images or []
    if not generated_images:
      raise RuntimeError('Imagen returned no generated images')

    image_bytes = generated_images[0].image.image_bytes
    if image_bytes:
      return image_bytes

    pil_img: PILImage.Image | None = getattr(generated_images[0].image, '_pil_image', None)
    if pil_img is None:
      raise RuntimeError('Imagen response did not contain image bytes')
    return _to_jpeg_bytes(pil_img)

  async def render_rooms_parallel(
    self,
    specs: list[dict],
  ) -> list[bytes | Exception]:
    """최대 4개 방을 병렬로 렌더링한다.

    RISK-01: return_exceptions=True 로 1개 실패해도 나머지 결과를 반환한다.
    반환 리스트에서 Exception 인스턴스는 해당 방 렌더링 실패를 의미한다.
    """
    tasks = [self.render_room(spec['prompt']) for spec in specs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
      if isinstance(result, Exception):
        room_type = specs[i].get('room_type', f'방{i + 1}')
        logger.warning('렌더링 실패 (room=%s): %s', room_type, result)
      else:
        logger.info('렌더링 완료: %s', specs[i].get('room_type', f'방{i + 1}'))

    return results
